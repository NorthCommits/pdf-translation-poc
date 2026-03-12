import csv
import io
import json
import logging
import math
import os
from typing import Any, Dict, List

import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI
from openai import OpenAI
from pydantic import BaseModel


class PromptRequest(BaseModel):
    prompt: str


load_dotenv()


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def load_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set in the environment or .env file.")
    return OpenAI(api_key=api_key)


def load_semantic_mesh() -> pd.DataFrame:
    """
    Load the semantic mesh Excel file, convert it to CSV in memory to flatten
    all merged cells, then parse into a DataFrame. Forward-fill PM_ID and
    Primary_Message columns to propagate values across all rows in each group.
    """
    file_path = "Global Eda-Semantic Mesh Template (1) 1.xlsx"
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Semantic mesh file not found: {file_path}")

    # Step 1: read Excel as-is with openpyxl
    raw_df = pd.read_excel(file_path, sheet_name=0, engine="openpyxl", header=0)

    # Step 2: convert to CSV in memory — this flattens all Excel formatting
    csv_buffer = io.StringIO()
    raw_df.to_csv(csv_buffer, index=False, quoting=csv.QUOTE_ALL)
    csv_buffer.seek(0)

    # Step 3: read back from the in-memory CSV for a clean flat DataFrame
    df = pd.read_csv(csv_buffer, dtype=str)

    # Step 4: strip whitespace from all column names
    df.columns = df.columns.str.strip()

    # Step 5: strip whitespace from all cell values
    df = df.apply(lambda col: col.str.strip() if col.dtype == object else col)

    # Step 6: replace empty strings and literal 'nan' with actual NaN
    df = df.replace({"": None, "nan": None, "NaN": None})

    # Step 7: forward-fill PM_ID and Primary_Message so every row
    # carries the value from the first row of its group
    df["PM_ID"] = df["PM_ID"].ffill()
    df["Primary_Message (ES)"] = df["Primary_Message (ES)"].ffill()

    logger.info("Columns found in file: %s", df.columns.tolist())
    logger.info("Total rows loaded: %d", len(df))

    return df


def safe_cell_value(value: Any) -> Any:
    if value is None:
        return None
    try:
        if math.isnan(float(value)):
            return None
    except (TypeError, ValueError):
        pass
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    text = str(value).strip()
    return text if text else None


def element_metadata_from_type(element_type: Any) -> str:
    text = str(element_type or "").lower()
    if "claim" in text:
        return "CL"
    if "reusable text" in text or "supporting text" in text:
        return "RT"
    if "component" in text:
        return "COMP"
    if "reference" in text:
        return "REF"
    if "footnote" in text:
        return "FN"
    if "glossary" in text:
        return "GS"
    return ""


def element_mandatory_flag(row: pd.Series) -> str:
    relationship_columns = [
        "SC1-relationship", "SC2-relationship", "SC3-relationship",
        "SC4-relationship", "SC5-relationship",
        "ST1-relationship", "ST2-relationship", "ST3-relationship",
        "ST4-relationship", "ST5-relationship",
        "C1-relationship",  "C2-relationship",  "C3-relationship",
        "C4-relationship",  "C5-relationship",
    ]
    values = [str(safe_cell_value(row.get(col)) or "").lower() for col in relationship_columns]
    if any(v == "mandatory" for v in values):
        return "Mandatory"
    if any(v == "optional" for v in values):
        return "Optional"
    return "Null"


def select_primary_message_with_llm(
    prompt_text: str,
    all_pms: List[Dict[str, str]],
) -> str:
    """
    Pass the user prompt and every PM text to GPT-4o in a single call.
    GPT-4o reads all primary messages together and returns the PM_ID
    whose primary message most precisely matches the clinical intent
    of the prompt.
    """
    if not all_pms:
        return ""

    lines: List[str] = []
    for index, pm in enumerate(all_pms, start=1):
        lines.append(f'{index}) {pm["pm_id"]}: "{pm["primary_message"]}"')

    system_instruction = (
        "You are a pharmaceutical medical content routing expert specializing in HIV treatment. "
        "You will be given a marketing brief and a numbered list of primary messages. "
        "Select the single primary message that most precisely matches the core clinical intent "
        "of the brief.\n"
        "Rules:\n"
        "1. Prefer the most clinically specific match over broad or generic product messages.\n"
        "2. If the brief mentions a specific clinical problem such as adherence, resistance, "
        "tolerability, or efficacy, select the PM that directly addresses that exact problem.\n"
        "3. Do not select a general long-term treatment message when a more specific PM exists.\n"
        "4. Match on clinical intent, not just shared words.\n"
        "Return ONLY a JSON object with this exact shape: "
        '{"pm_id": "<ID>", "reason": "<one sentence explanation>"}'
    )

    user_content = (
        f"Brief:\n{prompt_text}\n\n"
        "Primary messages:\n" + "\n".join(lines)
    )

    logger.info("Sending %d primary messages to GPT-4o for selection.", len(all_pms))

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_content},
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )

        parsed = json.loads(response.choices[0].message.content)
        pm_id_value = parsed.get("pm_id", "").strip()

        if pm_id_value:
            logger.info(
                "LLM selected PM_ID=%s | reason=%s",
                pm_id_value,
                parsed.get("reason", ""),
            )
            return pm_id_value

    except Exception as exc:
        logger.exception("Error during LLM PM selection: %s", exc)

    fallback = all_pms[0]["pm_id"]
    logger.warning("LLM selection failed, falling back to: %s", fallback)
    return fallback


def build_element_from_row(row: pd.Series, index_in_cluster: int) -> Dict[str, Any]:
    return {
        "element_id":                       safe_cell_value(row.get("Element Id")),
        "element_ocr":                      safe_cell_value(row.get("Extracted Content")),
        "element_url":                      None,
        "Reference":                        safe_cell_value(row.get("Reference")),
        "Footnote":                         safe_cell_value(row.get("Footnotes")),
        "Glossary":                         safe_cell_value(row.get("Glossary")),
        "Supporting Claim 1":               safe_cell_value(row.get("Supporting Claim 1")),
        "Supporting Claim 1 relationship":  safe_cell_value(row.get("SC1-relationship")),
        "Supporting Claim 2":               safe_cell_value(row.get("Supporting Claim 2")),
        "Supporting Claim 2 relationship":  safe_cell_value(row.get("SC2-relationship")),
        "Supporting Claim 3":               safe_cell_value(row.get("Supporting Claim 3")),
        "Supporting Claim 3 relationship":  safe_cell_value(row.get("SC3-relationship")),
        "Supporting Claim 4":               safe_cell_value(row.get("Supporting Claim 4")),
        "Supporting Claim 4 relationship":  safe_cell_value(row.get("SC4-relationship")),
        "Supporting Claim 5":               safe_cell_value(row.get("Supporting Claim 5")),
        "Supporting Claim 5 relationship":  safe_cell_value(row.get("SC5-relationship")),
        "Supporting text1":                 safe_cell_value(row.get("Supporting Text1")),
        "Supporting text1 relationship":    safe_cell_value(row.get("ST1-relationship")),
        "Supporting text2":                 safe_cell_value(row.get("Supporting Text2")),
        "Supporting text2 relationship":    safe_cell_value(row.get("ST2-relationship")),
        "Supporting text3":                 safe_cell_value(row.get("Supporting Text3")),
        "Supporting text3 relationship":    safe_cell_value(row.get("ST3-relationship")),
        "Supporting text4":                 safe_cell_value(row.get("Supporting Text4")),
        "Supporting text4 relationship":    safe_cell_value(row.get("ST4-relationship")),
        "Supporting text5":                 safe_cell_value(row.get("Supporting Text5")),
        "Supporting text5 relationship":    safe_cell_value(row.get("ST5-relationship")),
        "Component 1":                      safe_cell_value(row.get("Component 1")),
        "Component 1 relationship":         safe_cell_value(row.get("C1-relationship")),
        "Component 2":                      safe_cell_value(row.get("Component 2")),
        "Component 2 relationship":         safe_cell_value(row.get("C2-relationship")),
        "Component 3":                      safe_cell_value(row.get("Component 3")),
        "Component 3 relationship":         safe_cell_value(row.get("C3-relationship")),
        "Component 4":                      safe_cell_value(row.get("Component 4")),
        "Component 4 relationship":         safe_cell_value(row.get("C4-relationship")),
        "Component 5":                      safe_cell_value(row.get("Component 5")),
        "Component 5 relationship":         safe_cell_value(row.get("C5-relationship")),
        "element_mandatory_optional":       element_mandatory_flag(row),
        "element_metadata":                 element_metadata_from_type(row.get("Element Type")),
        "cluster_element_index":            str(index_in_cluster),
    }


# ---------------------------------------------------------------------------
# Startup: load Excel via in-memory CSV and build the full PM list
# ---------------------------------------------------------------------------

openai_client = load_openai_client()
semantic_mesh_df = load_semantic_mesh()

# Build unique PM list preserving sheet order
all_primary_messages: List[Dict[str, str]] = []
seen_pm_ids: set = set()

for _, row in semantic_mesh_df.iterrows():
    pm_id = safe_cell_value(row.get("PM_ID"))
    primary_message = safe_cell_value(row.get("Primary_Message (ES)"))
    if pm_id and primary_message and pm_id not in seen_pm_ids:
        seen_pm_ids.add(pm_id)
        all_primary_messages.append(
            {
                "pm_id": pm_id,
                "primary_message": primary_message,
            }
        )

logger.info(
    "Loaded %d unique primary messages: %s",
    len(all_primary_messages),
    [pm["pm_id"] for pm in all_primary_messages],
)


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

app = FastAPI(title="EDA Semantic Mesh Cluster API")


@app.post("/clusters")
def generate_clusters(request: PromptRequest) -> Dict[str, Any]:
    """
    Select the best PM for the prompt using GPT-4o reading all primary
    messages, then return its full cluster JSON. Output structure is
    identical to previous versions.
    """
    selected_pm_id = select_primary_message_with_llm(
        prompt_text=request.prompt,
        all_pms=all_primary_messages,
    )

    # Resolve primary message text for the selected PM
    selected_primary_message = next(
        (pm["primary_message"] for pm in all_primary_messages if pm["pm_id"] == selected_pm_id),
        "",
    )

    # Pull all rows for the selected PM and build elements
    pm_rows_df = semantic_mesh_df[
        semantic_mesh_df["PM_ID"] == selected_pm_id
    ].reset_index(drop=True)

    elements: List[Dict[str, Any]] = [
        build_element_from_row(row, index + 1)
        for index, row in pm_rows_df.iterrows()
    ]

    return {
        "clusters": [
            {
                "PM_ID": selected_pm_id,
                "Primary_Message (ES)": selected_primary_message,
                "elements": elements,
            }
        ]
    }


@app.get("/health")
def health_check() -> Dict[str, str]:
    return {"status": "ok"}