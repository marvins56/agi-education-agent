"""HTML file parser for local .html/.htm files.

Uses BeautifulSoup with lxml to extract main content from
local HTML files, stripping navigation, scripts, and other
non-content elements.
"""

import logging
import pathlib

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Tags to strip from the document before extracting text
_STRIP_TAGS = {"script", "style", "nav", "footer", "header", "aside", "noscript", "iframe"}


class HtmlFileParser:
    """Extract text and metadata from local HTML files.

    This parser is for local .html/.htm files on disk.
    For fetching and parsing web URLs, use the WebParser instead.
    """

    def parse(self, file_path: str) -> str:
        """Extract main content text from a local HTML file.

        Strips script, style, nav, footer, header, and aside tags,
        then extracts text from the main content area.
        """
        html_content = self._read_file(file_path)
        if not html_content:
            return ""

        try:
            soup = BeautifulSoup(html_content, "lxml")
        except Exception as exc:
            logger.warning("lxml parser failed for %s, falling back to html.parser: %s", file_path, exc)
            try:
                soup = BeautifulSoup(html_content, "html.parser")
            except Exception as exc2:
                logger.error("Failed to parse HTML file %s: %s", file_path, exc2)
                return ""

        # Remove unwanted elements
        for tag_name in _STRIP_TAGS:
            for tag in soup.find_all(tag_name):
                try:
                    tag.decompose()
                except Exception as exc:
                    logger.debug("Error removing tag '%s': %s", tag_name, exc)

        # Find main content area with fallback chain
        main = soup.find("main") or soup.find("article") or soup.find("body")
        if main is None:
            main = soup

        # Extract text with line separation
        text = main.get_text(separator="\n", strip=True)

        # Collapse excessive blank lines
        lines = [line for line in text.splitlines() if line.strip()]
        return "\n".join(lines)

    def parse_with_metadata(self, file_path: str) -> dict:
        """Extract text and metadata from a local HTML file."""
        html_content = self._read_file(file_path)
        if not html_content:
            return {"text": "", "pages": 0, "metadata": {}}

        try:
            soup = BeautifulSoup(html_content, "lxml")
        except Exception as exc:
            logger.warning("lxml parser failed for %s, falling back to html.parser: %s", file_path, exc)
            try:
                soup = BeautifulSoup(html_content, "html.parser")
            except Exception as exc2:
                logger.error("Failed to parse HTML file %s: %s", file_path, exc2)
                return {"text": "", "pages": 0, "metadata": {}}

        # Extract title before stripping tags
        title = ""
        try:
            title_tag = soup.find("title")
            if title_tag:
                title = title_tag.get_text(strip=True)
        except Exception as exc:
            logger.debug("Error extracting title: %s", exc)

        # Remove unwanted elements
        for tag_name in _STRIP_TAGS:
            for tag in soup.find_all(tag_name):
                try:
                    tag.decompose()
                except Exception as exc:
                    logger.debug("Error removing tag '%s': %s", tag_name, exc)

        # Find main content area
        main = soup.find("main") or soup.find("article") or soup.find("body")
        if main is None:
            main = soup

        # Extract text
        text = main.get_text(separator="\n", strip=True)
        lines = [line for line in text.splitlines() if line.strip()]
        clean_text = "\n".join(lines)

        word_count = len(clean_text.split()) if clean_text else 0

        return {
            "text": clean_text,
            "pages": 1,
            "metadata": {
                "title": title,
                "word_count": word_count,
            },
        }

    def _read_file(self, file_path: str) -> str:
        """Read an HTML file with encoding detection.

        Tries UTF-8 first, then falls back to Latin-1.
        Returns empty string on failure.
        """
        path = pathlib.Path(file_path)

        if not path.exists():
            logger.error("HTML file not found: %s", file_path)
            return ""

        if path.stat().st_size == 0:
            logger.warning("HTML file is empty: %s", file_path)
            return ""

        # Try UTF-8 first
        try:
            return path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            logger.debug("UTF-8 decoding failed for %s, trying latin-1", file_path)

        # Fallback to Latin-1 (never fails for byte values 0-255)
        try:
            return path.read_text(encoding="latin-1")
        except Exception as exc:
            logger.error("Failed to read HTML file %s: %s", file_path, exc)
            return ""
