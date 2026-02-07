"""PDF document parser using PyMuPDF."""

import fitz


class PdfParser:
    """Extract text and metadata from PDF files."""

    def parse(self, file_path: str) -> str:
        """Extract all text from a PDF file."""
        doc = fitz.open(file_path)
        try:
            text_parts = []
            for page in doc:
                text_parts.append(page.get_text())
            return "\n".join(text_parts).strip()
        finally:
            doc.close()

    def parse_with_metadata(self, file_path: str) -> dict:
        """Extract text and metadata from a PDF file."""
        doc = fitz.open(file_path)
        try:
            text_parts = []
            for page in doc:
                text_parts.append(page.get_text())

            pdf_metadata = doc.metadata or {}
            return {
                "text": "\n".join(text_parts).strip(),
                "pages": len(doc),
                "metadata": {
                    "title": pdf_metadata.get("title", ""),
                    "author": pdf_metadata.get("author", ""),
                    "subject": pdf_metadata.get("subject", ""),
                    "creator": pdf_metadata.get("creator", ""),
                },
            }
        finally:
            doc.close()
