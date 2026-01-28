from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
import os
import uuid
import shutil
from core.pdf_processor_simple import PDFProcessor
from core.config import settings
from models.schemas import (
    UploadResponse,
    TranslationRequest,
    TranslationResponse,
    ExtractTextResponse,
    TextSegment
)
from typing import Dict

router = APIRouter()

# Initialize PDF processor (singleton)
pdf_processor = PDFProcessor()

# Store uploaded files temporarily in memory
# In production, use Redis or a database
uploaded_files: Dict[str, Dict] = {}

@router.post("/upload-pdf", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    """
    Endpoint 1: Upload and validate PDF

    This endpoint:
    1. Validates file type
    2. Saves file to temp storage
    3. Validates PDF is not corrupted
    4. Returns session ID for subsequent operations
    """
    print(f"\n{'='*60}")
    print(f"Upload Request: {file.filename}")
    print(f"{'='*60}")

    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # Generate unique session ID
    session_id = str(uuid.uuid4())

    # Save uploaded file
    file_path = os.path.join(settings.TEMP_DIR, f"{session_id}_original.pdf")

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        print(f"✓ File saved to: {file_path}")

        # Validate PDF
        if not pdf_processor.validate_pdf(file_path):
            os.remove(file_path)
            raise HTTPException(status_code=400, detail="Invalid or corrupted PDF file")

        print(f"✓ PDF validation passed")

        # Store file info in memory
        uploaded_files[session_id] = {
            "original_path": file_path,
            "filename": file.filename
        }

        print(f"✓ Session created: {session_id}")
        print(f"{'='*60}\n")

        return UploadResponse(
            session_id=session_id,
            filename=file.filename,
            message="PDF uploaded and validated successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        # Cleanup on error
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/extract-text/{session_id}", response_model=ExtractTextResponse)
async def extract_text(session_id: str):
    """
    Endpoint 2: Extract text with positions for editing overlay

    This endpoint extracts all text from the PDF with bounding box coordinates,
    enabling the frontend to create clickable/editable overlays.
    """
    print(f"\n{'='*60}")
    print(f"Extract Text Request: Session {session_id}")
    print(f"{'='*60}")

    if session_id not in uploaded_files:
        raise HTTPException(status_code=404, detail="Session not found")

    pdf_path = uploaded_files[session_id]["original_path"]

    try:
        text_segments = pdf_processor.extract_text_with_positions(pdf_path)

        print(f"✓ Extraction complete")
        print(f"{'='*60}\n")

        return ExtractTextResponse(
            segments=[TextSegment(**seg) for seg in text_segments],
            total_segments=len(text_segments)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text extraction failed: {str(e)}")


@router.post("/update-pdf/{session_id}")
async def update_pdf(session_id: str, file: UploadFile = File(...)):
    """
    Endpoint 3: Update PDF with edited version from Nutrient

    After user edits the PDF in Nutrient, upload the modified version
    to replace the original before translation.
    """
    print(f"\n{'='*60}")
    print(f"Update PDF Request: Session {session_id}")
    print(f"{'='*60}")

    if session_id not in uploaded_files:
        raise HTTPException(status_code=404, detail="Session not found")

    # Save edited PDF (replace original)
    edited_path = os.path.join(settings.TEMP_DIR, f"{session_id}_edited.pdf")

    try:
        with open(edited_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        print(f"✓ Edited PDF saved: {edited_path}")

        # Update session to use edited PDF
        uploaded_files[session_id]["edited_path"] = edited_path

        print(f"✓ Session updated with edited PDF")
        print(f"{'='*60}\n")

        return {"message": "PDF updated successfully", "session_id": session_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update PDF: {str(e)}")


@router.post("/translate/{session_id}", response_model=TranslationResponse)
async def translate_pdf(session_id: str, request: TranslationRequest):
    """
    Endpoint 4: Translate PDF using DeepL Document Translation API

    This endpoint:
    1. Takes the original (or edited) PDF
    2. Sends it to DeepL Document Translation API
    3. DeepL translates and preserves formatting automatically
    4. Returns the translated PDF
    """
    print(f"\n{'='*60}")
    print(f"Translate Request: Session {session_id}")
    print(f"Languages: {request.source_lang} → {request.target_lang}")
    print(f"{'='*60}")

    if session_id not in uploaded_files:
        raise HTTPException(status_code=404, detail="Session not found")

    # Use edited PDF if available, otherwise use original
    input_pdf = uploaded_files[session_id].get("edited_path") or uploaded_files[session_id]["original_path"]

    if "edited_path" in uploaded_files[session_id]:
        print(f"✓ Using edited PDF for translation")
    else:
        print(f"ℹ Using original PDF for translation")
    output_pdf = os.path.join(
        settings.TEMP_DIR,
        f"{session_id}_translated.pdf"
    )

    try:
        # Use DeepL Document Translation API
        result = pdf_processor.translate_document_deepl(
            input_pdf_path=input_pdf,
            output_pdf_path=output_pdf,
            source_lang=request.source_lang,
            target_lang=request.target_lang
        )

        if result["success"]:
            # Store translated PDF path
            uploaded_files[session_id]["translated_path"] = output_pdf

            return TranslationResponse(
                success=True,
                message=result["message"],
                pdf_url=f"/api/v1/download/{session_id}/translated"
            )
        else:
            raise HTTPException(status_code=500, detail=result["error"])

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")


@router.get("/download/{session_id}/{pdf_type}")
async def download_pdf(session_id: str, pdf_type: str):
    """
    Endpoint 4: Download original or translated PDF

    Args:
        session_id: Session identifier
        pdf_type: Either "original" or "translated"
    """
    print(f"\n{'='*60}")
    print(f"Download Request: Session {session_id}, Type: {pdf_type}")
    print(f"{'='*60}")

    if session_id not in uploaded_files:
        raise HTTPException(status_code=404, detail="Session not found")

    if pdf_type == "original":
        file_path = uploaded_files[session_id].get("original_path")
    elif pdf_type == "translated":
        file_path = uploaded_files[session_id].get("translated_path")
        if not file_path:
            raise HTTPException(status_code=404, detail="Translated PDF not found. Please translate first.")
    else:
        raise HTTPException(status_code=400, detail="Invalid PDF type. Use 'original' or 'translated'")

    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="PDF file not found")

    filename = uploaded_files[session_id]["filename"]
    # Create a clean download filename
    name_without_ext = os.path.splitext(filename)[0]
    download_filename = f"{name_without_ext}_{pdf_type}.pdf"

    print(f"✓ Serving file: {download_filename}")
    print(f"{'='*60}\n")

    return FileResponse(
        file_path,
        media_type="application/pdf",
        filename=download_filename
    )


@router.delete("/cleanup/{session_id}")
async def cleanup_session(session_id: str):
    """
    Endpoint 5: Cleanup temporary files

    This endpoint removes all files associated with a session
    and frees up memory. Should be called when user is done.
    """
    print(f"\n{'='*60}")
    print(f"Cleanup Request: Session {session_id}")
    print(f"{'='*60}")

    if session_id not in uploaded_files:
        raise HTTPException(status_code=404, detail="Session not found")

    # Remove all files associated with session
    files_removed = 0
    for key in ["original_path", "translated_path"]:
        if key in uploaded_files[session_id]:
            file_path = uploaded_files[session_id][key]
            if os.path.exists(file_path):
                os.remove(file_path)
                files_removed += 1
                print(f"✓ Removed: {os.path.basename(file_path)}")

    # Remove from memory
    del uploaded_files[session_id]

    print(f"✓ Session cleaned up: {files_removed} file(s) removed")
    print(f"{'='*60}\n")

    return {"message": f"Session cleaned up successfully. {files_removed} file(s) removed."}


@router.get("/sessions")
async def list_sessions():
    """
    Endpoint 6: List active sessions (debugging/admin)

    Useful for development and debugging to see active sessions.
    """
    return {
        "active_sessions": len(uploaded_files),
        "sessions": [
            {
                "session_id": sid,
                "filename": data["filename"],
                "has_translation": "translated_path" in data
            }
            for sid, data in uploaded_files.items()
        ]
    }
