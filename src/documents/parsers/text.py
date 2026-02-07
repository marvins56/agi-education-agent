"""Plain text and markdown file parser."""

import pathlib


class TextParser:
    """Extract text from plain text and markdown files."""

    def parse(self, file_path: str) -> str:
        """Read the full contents of a text file."""
        return pathlib.Path(file_path).read_text(encoding="utf-8")

    def parse_with_metadata(self, file_path: str) -> dict:
        """Read text and gather basic metadata."""
        path = pathlib.Path(file_path)
        text = path.read_text(encoding="utf-8")
        stat = path.stat()
        return {
            "text": text,
            "pages": 1,
            "metadata": {
                "filename": path.name,
                "extension": path.suffix,
                "size_bytes": stat.st_size,
            },
        }
