"""DOCX document parser using python-docx."""

from docx import Document


class DocxParser:
    """Extract text and metadata from DOCX files."""

    def parse(self, file_path: str) -> str:
        """Extract all text from a DOCX file."""
        doc = Document(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n\n".join(paragraphs)

    def parse_with_metadata(self, file_path: str) -> dict:
        """Extract text and metadata from a DOCX file."""
        doc = Document(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]

        core = doc.core_properties
        return {
            "text": "\n\n".join(paragraphs),
            "pages": len(doc.sections),
            "metadata": {
                "title": core.title or "",
                "author": core.author or "",
                "subject": core.subject or "",
            },
        }
