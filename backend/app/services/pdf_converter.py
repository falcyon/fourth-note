"""PDF to Markdown converter with OCR support."""
import io
import tempfile
from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from markitdown import MarkItDown

from app.services.progress import get_progress_tracker


class PdfConverter:
    """Converts PDF files to Markdown with OCR for images."""

    def __init__(self, ocr_lang: str = "eng"):
        self.ocr_lang = ocr_lang
        self.markitdown = MarkItDown()
        self.progress = get_progress_tracker()

    def _process_page_images(self, page, page_num: int, total_pages: int) -> tuple[int, int]:
        """Process images on a page with OCR, return (total_images, images_with_text)."""
        blocks = page.get_text("dict")["blocks"]
        total_images = 0
        images_with_text = 0

        for block in blocks:
            if block["type"] != 1:  # Not an image block
                continue

            total_images += 1
            image_bytes = block.get("image")
            if not image_bytes:
                continue

            try:
                image = Image.open(io.BytesIO(image_bytes))
                ocr_text = pytesseract.image_to_string(image, lang=self.ocr_lang)

                if ocr_text.strip():
                    images_with_text += 1
                    rect = fitz.Rect(block["bbox"])
                    page.insert_textbox(
                        rect,
                        ocr_text,
                        fontname="helv",
                        fontsize=10,
                        color=(0, 0, 0),
                    )
            except Exception:
                pass  # Skip images that fail OCR

        return total_images, images_with_text

    def convert_pdf(self, pdf_path: str, output_md_path: Optional[str] = None) -> str:
        """Convert a PDF file to Markdown with OCR for images."""
        filename = Path(pdf_path).name
        self.progress.emit("pdf", f"Opening PDF: {filename}")

        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        total_images = 0
        total_ocr_text = 0

        self.progress.emit("pdf", f"PDF has {total_pages} pages", {
            "filename": filename,
            "pages": total_pages
        })

        # Process each page
        self.progress.emit("ocr", f"Scanning {total_pages} pages for images...", {
            "pages": total_pages
        })

        for page_num, page in enumerate(doc):
            images, with_text = self._process_page_images(page, page_num, total_pages)
            total_images += images
            total_ocr_text += with_text

        if total_images > 0:
            self.progress.emit("ocr", f"OCR complete: {total_ocr_text}/{total_images} images had text", {
                "total_images": total_images,
                "images_with_text": total_ocr_text
            })

        # Save to temp file for markitdown (it requires a file path)
        self.progress.emit("convert", "Converting to Markdown...")

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        doc.save(str(tmp_path))
        doc.close()

        try:
            result = self.markitdown.convert(str(tmp_path))
            markdown_text = result.text_content if result else ""
            # Remove NUL bytes that PostgreSQL doesn't accept in text fields
            markdown_text = markdown_text.replace('\x00', '')
        finally:
            # Clean up temp file (ignore errors on Windows)
            try:
                tmp_path.unlink()
            except (PermissionError, OSError):
                pass

        char_count = len(markdown_text)
        self.progress.emit("convert", f"Markdown generated: {char_count:,} characters", {
            "filename": filename,
            "characters": char_count
        })

        # Optionally save to file
        if output_md_path:
            Path(output_md_path).parent.mkdir(parents=True, exist_ok=True)
            Path(output_md_path).write_text(markdown_text, encoding="utf-8")

        return markdown_text


# Singleton instance
_converter: Optional[PdfConverter] = None


def get_pdf_converter() -> PdfConverter:
    """Get singleton PDF converter instance."""
    global _converter
    if _converter is None:
        _converter = PdfConverter()
    return _converter
