import os
import uuid
from typing import Dict, List, Optional
from apryse_sdk import PDFNet, PDFDoc, TransPDF, TransPDFOptions
import deepl
import xml.etree.ElementTree as ET
from core.config import settings

class PDFProcessor:
    def __init__(self):
        """Initialize Apryse with license key"""
        PDFNet.Initialize(settings.APRYSE_LICENSE_KEY)
        self.translator = deepl.Translator(settings.DEEPL_API_KEY)
        print("✓ PDFProcessor initialized with Apryse and DeepL")

    def validate_pdf(self, pdf_path: str) -> bool:
        """Validate that file is a valid PDF"""
        try:
            doc = PDFDoc(pdf_path)
            doc.InitSecurityHandler()

            # Check if document has at least one page
            page_count = doc.GetPageCount()
            doc.Close()

            return page_count > 0
        except Exception as e:
            print(f"PDF validation error: {e}")
            return False

    def extract_text_with_positions(self, pdf_path: str) -> List[Dict]:
        """
        Extract text segments with their bounding box coordinates using Apryse TextExtractor
        Returns list of dicts: {text, page, x0, y0, x1, y1, segment_id}
        """
        try:
            doc = PDFDoc(pdf_path)
            doc.InitSecurityHandler()
            text_segments = []

            from apryse_sdk import TextExtractor

            for page_num in range(1, doc.GetPageCount() + 1):
                page = doc.GetPage(page_num)
                txt_extractor = TextExtractor()
                txt_extractor.Begin(page)

                segment_index = 0

                # Extract text line by line with positions
                line = txt_extractor.GetFirstLine()
                while line.IsValid():
                    # Get words in the line
                    word = line.GetFirstWord()
                    while word.IsValid():
                        try:
                            word_text = word.GetString()
                            # Get bounding box quads for the word
                            quads = word.GetQuads()

                            if quads and len(quads) > 0:
                                # Use first quad for position
                                quad = quads[0]
                                # Quad has 4 points: p1, p2, p3, p4
                                x0 = min(quad.p1.x, quad.p4.x)
                                y0 = min(quad.p1.y, quad.p2.y)
                                x1 = max(quad.p2.x, quad.p3.x)
                                y1 = max(quad.p3.y, quad.p4.y)

                                text_segments.append({
                                    "text": word_text,
                                    "page": page_num,
                                    "x0": float(x0),
                                    "y0": float(y0),
                                    "x1": float(x1),
                                    "y1": float(y1),
                                    "segment_id": f"seg_{page_num}_{segment_index}"
                                })
                                segment_index += 1
                        except Exception as e:
                            pass  # Skip words that can't be processed

                        word = word.GetNextWord()

                    line = line.GetNextLine()

            doc.Close()
            print(f"✓ Extracted {len(text_segments)} text segments from PDF")
            return text_segments

        except Exception as e:
            print(f"✗ Text extraction failed: {e}")
            import traceback
            traceback.print_exc()
            return []

    def extract_xliff(self, pdf_path: str, xliff_output_path: str) -> str:
        """
        Step 1: Extract text from PDF to XLIFF format
        Returns path to XLIFF file
        """
        doc = PDFDoc(pdf_path)
        options = TransPDFOptions()

        # Extract XLIFF - THIS IS KEY FOR LAYOUT PRESERVATION
        print(f"  Extracting XLIFF from PDF...")
        TransPDF.ExtractXLIFF(doc, xliff_output_path, options)

        doc.Close()
        print(f"✓ XLIFF extracted to: {xliff_output_path}")
        return xliff_output_path

    def translate_xliff(
        self,
        xliff_path: str,
        source_lang: str,
        target_lang: str,
        manual_edits: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Step 2: Translate XLIFF file using DeepL

        Args:
            xliff_path: Path to extracted XLIFF
            source_lang: Source language code (e.g., "EN", "DE")
            target_lang: Target language code (e.g., "ES", "FR")
            manual_edits: Dict mapping segment IDs to manually edited text

        Returns:
            Path to translated XLIFF file
        """
        print(f"  Translating from {source_lang} to {target_lang}...")

        # Parse XLIFF
        tree = ET.parse(xliff_path)
        root = tree.getroot()

        # Define namespace
        ns = {'xliff': 'urn:oasis:names:tc:xliff:document:2.0'}

        # Find all segments
        segments = root.findall('.//xliff:segment', ns)

        total_segments = len(segments)
        print(f"  Found {total_segments} segments to translate")

        translated_count = 0
        manual_edit_count = 0

        for i, segment in enumerate(segments):
            segment_id = segment.get('id')
            source_elem = segment.find('xliff:source', ns)

            if source_elem is not None and source_elem.text:
                original_text = source_elem.text.strip()

                # Skip empty text
                if not original_text:
                    continue

                # Check if this segment was manually edited
                if manual_edits and segment_id in manual_edits:
                    translated_text = manual_edits[segment_id]
                    manual_edit_count += 1
                    print(f"  [Manual Edit] Segment {segment_id}: using user edit")
                else:
                    # Translate using DeepL
                    try:
                        result = self.translator.translate_text(
                            original_text,
                            source_lang=source_lang,
                            target_lang=target_lang
                        )
                        translated_text = result.text
                        translated_count += 1
                    except Exception as e:
                        print(f"  [Warning] Translation error for segment {i}: {e}")
                        translated_text = original_text  # Fallback to original

                # Create or update target element
                target_elem = segment.find('xliff:target', ns)
                if target_elem is None:
                    target_elem = ET.SubElement(
                        segment,
                        '{urn:oasis:names:tc:xliff:document:2.0}target'
                    )

                target_elem.text = translated_text

                # Progress logging every 10 segments
                if (i + 1) % 10 == 0 or (i + 1) == total_segments:
                    print(f"  Progress: {i + 1}/{total_segments} segments processed")

        print(f"✓ Translation complete: {translated_count} auto-translated, {manual_edit_count} manual edits")

        # Save translated XLIFF
        translated_xliff_path = xliff_path.replace('.xlf', '_translated.xlf')
        tree.write(
            translated_xliff_path,
            encoding='utf-8',
            xml_declaration=True
        )

        print(f"✓ Translated XLIFF saved to: {translated_xliff_path}")
        return translated_xliff_path

    def apply_xliff_to_pdf(
        self,
        intermediate_pdf_path: str,
        translated_xliff_path: str,
        output_pdf_path: str
    ) -> str:
        """
        Step 3: Apply translated XLIFF back to PDF with layout preservation
        THIS IS THE KEY FEATURE - uses Apryse's XLIFF Reflow
        """
        print(f"  Applying XLIFF with reflow (layout preservation)...")

        doc = PDFDoc(intermediate_pdf_path)

        # Apply XLIFF with reflow - THIS PRESERVES LAYOUT!
        # This is the magic that maintains fonts, formatting, and positioning
        TransPDF.ApplyXLIFF(doc, translated_xliff_path)

        # Save final PDF with linearization for faster web viewing
        doc.Save(output_pdf_path, PDFDoc.e_linearized)
        doc.Close()

        print(f"✓ Translated PDF saved with preserved layout: {output_pdf_path}")
        return output_pdf_path

    def full_translation_workflow(
        self,
        input_pdf_path: str,
        output_pdf_path: str,
        source_lang: str,
        target_lang: str,
        manual_edits: Optional[Dict[str, str]] = None
    ) -> Dict:
        """
        Complete workflow: PDF → XLIFF → Translate → Reflow → PDF

        This is the main orchestration function that ties everything together.

        Returns:
            Dict with status and paths
        """
        try:
            print(f"\n{'='*60}")
            print(f"Starting PDF Translation Workflow")
            print(f"{'='*60}")
            print(f"Input: {input_pdf_path}")
            print(f"Output: {output_pdf_path}")
            print(f"Languages: {source_lang} → {target_lang}")
            if manual_edits:
                print(f"Manual edits: {len(manual_edits)} segment(s)")
            print(f"{'='*60}\n")

            # Generate unique temp filenames
            session_id = str(uuid.uuid4())[:8]  # Shorter ID for cleaner filenames
            xliff_path = os.path.join(settings.TEMP_DIR, f"{session_id}.xlf")
            intermediate_pdf = os.path.join(settings.TEMP_DIR, f"{session_id}_inter.pdf")

            # Step 1: Extract XLIFF
            print("STEP 1: Extracting XLIFF from PDF")
            print("-" * 60)
            self.extract_xliff(input_pdf_path, xliff_path)

            # Create intermediate PDF (copy of original for reflow)
            print("\n  Creating intermediate PDF for reflow...")
            doc = PDFDoc(input_pdf_path)
            doc.Save(intermediate_pdf, PDFDoc.e_linearized)
            doc.Close()

            # Step 2: Translate XLIFF
            print("\nSTEP 2: Translating XLIFF using DeepL")
            print("-" * 60)
            translated_xliff = self.translate_xliff(
                xliff_path,
                source_lang,
                target_lang,
                manual_edits
            )

            # Step 3: Apply XLIFF to PDF with Reflow
            print("\nSTEP 3: Applying XLIFF with Reflow (Layout Preservation)")
            print("-" * 60)
            self.apply_xliff_to_pdf(
                intermediate_pdf,
                translated_xliff,
                output_pdf_path
            )

            # Cleanup temp files
            print("\n  Cleaning up temporary files...")
            for temp_file in [xliff_path, intermediate_pdf, translated_xliff]:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    print(f"  Removed: {os.path.basename(temp_file)}")

            print(f"\n{'='*60}")
            print(f"✓ Translation workflow completed successfully!")
            print(f"{'='*60}\n")

            return {
                "success": True,
                "output_path": output_pdf_path,
                "message": "Translation completed successfully with layout preservation"
            }

        except Exception as e:
            print(f"\n{'='*60}")
            print(f"✗ Translation workflow failed!")
            print(f"{'='*60}")
            print(f"Error: {str(e)}")
            import traceback
            traceback.print_exc()

            return {
                "success": False,
                "error": str(e),
                "message": "Translation failed. Please check the logs for details."
            }

    def translate_document_deepl(
        self,
        input_pdf_path: str,
        output_pdf_path: str,
        source_lang: str,
        target_lang: str
    ) -> Dict:
        """
        Translate PDF document using DeepL Document Translation API
        This maintains formatting and layout automatically.

        Args:
            input_pdf_path: Path to input PDF
            output_pdf_path: Path to save translated PDF
            source_lang: Source language code (e.g., "EN", "DE")
            target_lang: Target language code (e.g., "ES", "FR")

        Returns:
            Dict with success status and output path
        """
        try:
            print(f"\n{'='*60}")
            print(f"DeepL Document Translation Workflow")
            print(f"{'='*60}")
            print(f"Input: {input_pdf_path}")
            print(f"Output: {output_pdf_path}")
            print(f"Languages: {source_lang} → {target_lang}")
            print(f"{'='*60}\n")

            print("Step 1: Uploading document to DeepL...")

            # Upload document for translation
            with open(input_pdf_path, 'rb') as pdf_file:
                translator = self.translator

                # Start document translation
                print("  Sending document to DeepL API...")
                handle = translator.translate_document_upload(
                    pdf_file,
                    source_lang=source_lang,
                    target_lang=target_lang
                )

                print(f"  Document uploaded. Document ID: {handle.document_id}")
                print(f"  Document key: {handle.document_key}")

            print("\nStep 2: Waiting for translation to complete...")

            # Wait for translation to complete and download
            import time

            # Poll until done (check status.ok() or status.done())
            while True:
                status = translator.translate_document_get_status(handle)
                print(f"  Status: {status.status}...")

                # Check if done (status has a done() method or check status directly)
                if status.done():
                    print("  ✓ Translation completed!")
                    break

                # Check for errors
                if hasattr(status, 'error_message') and status.error_message:
                    raise Exception(f"Translation failed: {status.error_message}")

                time.sleep(2)

            print("\nStep 3: Downloading translated document...")

            # Download translated document
            translator.translate_document_download(
                handle,
                output_path=output_pdf_path
            )

            print(f"✓ Translated PDF saved: {output_pdf_path}")

            print(f"\n{'='*60}")
            print(f"✓ DeepL Document Translation completed successfully!")
            print(f"{'='*60}\n")

            return {
                "success": True,
                "output_path": output_pdf_path,
                "message": "Translation completed successfully using DeepL Document API"
            }

        except Exception as e:
            print(f"\n{'='*60}")
            print(f"✗ DeepL Document Translation failed!")
            print(f"{'='*60}")
            print(f"Error: {str(e)}")
            import traceback
            traceback.print_exc()

            return {
                "success": False,
                "error": str(e),
                "message": f"Translation failed: {str(e)}"
            }

    def __del__(self):
        """Cleanup Apryse resources"""
        try:
            PDFNet.Terminate()
        except:
            pass
