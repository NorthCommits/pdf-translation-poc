import os
from typing import Dict
import deepl
from core.config import settings

class PDFProcessor:
    def __init__(self):
        """Initialize DeepL translator"""
        self.translator = deepl.Translator(settings.DEEPL_API_KEY)
        print("✓ PDFProcessor initialized with DeepL Document Translation API")

    def validate_pdf(self, pdf_path: str) -> bool:
        """Validate that file is a valid PDF by checking header"""
        try:
            with open(pdf_path, 'rb') as f:
                header = f.read(4)
                # Check for PDF magic number: %PDF
                return header == b'%PDF'
        except Exception as e:
            print(f"PDF validation error: {e}")
            return False

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

            # Poll until done
            while True:
                status = translator.translate_document_get_status(handle)
                print(f"  Status: {status.status}...")

                # Check if done (status.done is a boolean property)
                if status.done:
                    print("  ✓ Translation completed!")
                    break

                # Check for errors
                if hasattr(status, 'error_message') and status.error_message:
                    raise Exception(f"Translation failed: {status.error_message}")

                time.sleep(2)

            print("\nStep 3: Downloading translated document...")

            # Download translated document
            with open(output_pdf_path, 'wb') as output_file:
                translator.translate_document_download(handle, output_file)

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
