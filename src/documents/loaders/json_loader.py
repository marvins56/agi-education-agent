"""JSON file loader for structured data."""
import json
import logging
import pathlib

logger = logging.getLogger(__name__)

class JSONFileLoader:
    """Parse JSON files and extract text content."""

    def parse(self, file_path: str) -> str:
        """Extract text representation from a JSON file."""
        result = self.parse_with_metadata(file_path)
        return result["text"]

    def parse_with_metadata(self, file_path: str) -> dict:
        """Parse a JSON file and return text + metadata."""
        path = pathlib.Path(file_path)
        try:
            raw = path.read_text(encoding="utf-8")
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            logger.error("Invalid JSON in %s: %s", file_path, exc)
            return {"text": "", "pages": 1, "metadata": {"error": str(exc)}}
        except Exception as exc:
            logger.error("Failed to read JSON file %s: %s", file_path, exc)
            return {"text": "", "pages": 1, "metadata": {"error": str(exc)}}

        text = self._extract_text(data)

        item_count = 0
        if isinstance(data, list):
            item_count = len(data)
        elif isinstance(data, dict):
            item_count = len(data)

        return {
            "text": text,
            "pages": 1,
            "metadata": {
                "filename": path.name,
                "item_count": item_count,
                "data_type": type(data).__name__,
            },
        }

    def _extract_text(self, data, indent: int = 0) -> str:
        """Recursively extract text from JSON structure."""
        if isinstance(data, str):
            return data
        elif isinstance(data, (int, float, bool)):
            return str(data)
        elif isinstance(data, list):
            parts = []
            for i, item in enumerate(data):
                if isinstance(item, dict):
                    parts.append(self._dict_to_text(item, indent))
                else:
                    parts.append(self._extract_text(item, indent))
            return "\n\n".join(parts)
        elif isinstance(data, dict):
            return self._dict_to_text(data, indent)
        return ""

    def _dict_to_text(self, d: dict, indent: int = 0) -> str:
        """Convert a dict to readable text."""
        parts = []
        prefix = "  " * indent
        for key, value in d.items():
            if isinstance(value, (str, int, float, bool)):
                parts.append(f"{prefix}{key}: {value}")
            elif isinstance(value, list):
                if all(isinstance(v, (str, int, float, bool)) for v in value):
                    parts.append(f"{prefix}{key}: {', '.join(str(v) for v in value)}")
                else:
                    parts.append(f"{prefix}{key}:")
                    parts.append(self._extract_text(value, indent + 1))
            elif isinstance(value, dict):
                parts.append(f"{prefix}{key}:")
                parts.append(self._dict_to_text(value, indent + 1))
        return "\n".join(parts)
