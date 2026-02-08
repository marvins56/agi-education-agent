"""EPUB ebook parser using ebooklib and BeautifulSoup.

Extracts chapter text from EPUB files, organizing content
by chapter with metadata including chapter count and word count.
"""

import logging

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class EpubParser:
    """Extract text and metadata from EPUB files."""

    def parse(self, file_path: str) -> str:
        """Extract all text from an EPUB file.

        Returns text organized by chapter with chapter titles
        as markdown headings.
        """
        try:
            book = epub.read_epub(file_path, options={"ignore_ncx": True})
        except Exception as exc:
            logger.error("Failed to open EPUB file %s: %s", file_path, exc)
            return ""

        parts = []
        for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            try:
                chapter_text = self._extract_chapter(item)
                if chapter_text:
                    parts.append(chapter_text)
            except Exception as exc:
                logger.debug(
                    "Error processing EPUB item '%s': %s",
                    getattr(item, "file_name", "unknown"),
                    exc,
                )
                continue

        return "\n\n".join(parts)

    def parse_with_metadata(self, file_path: str) -> dict:
        """Extract text and metadata from an EPUB file."""
        try:
            book = epub.read_epub(file_path, options={"ignore_ncx": True})
        except Exception as exc:
            logger.error("Failed to open EPUB file %s: %s", file_path, exc)
            return {"text": "", "pages": 0, "metadata": {}}

        parts = []
        chapter_count = 0

        for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            try:
                chapter_text = self._extract_chapter(item)
                if chapter_text:
                    parts.append(chapter_text)
                    chapter_count += 1
            except Exception as exc:
                logger.debug(
                    "Error processing EPUB item '%s': %s",
                    getattr(item, "file_name", "unknown"),
                    exc,
                )
                continue

        text = "\n\n".join(parts)
        word_count = len(text.split()) if text else 0

        # Try to extract book metadata
        title = ""
        author = ""
        try:
            title_meta = book.get_metadata("DC", "title")
            if title_meta:
                title = title_meta[0][0]
        except Exception:
            pass

        try:
            creator_meta = book.get_metadata("DC", "creator")
            if creator_meta:
                author = creator_meta[0][0]
        except Exception:
            pass

        return {
            "text": text,
            "pages": chapter_count,
            "metadata": {
                "title": title,
                "author": author,
                "chapter_count": chapter_count,
                "word_count": word_count,
            },
        }

    def _extract_chapter(self, item) -> str:
        """Extract text from a single EPUB document item.

        Parses the XHTML content with BeautifulSoup and extracts
        readable text. The chapter title is derived from the first
        heading tag found, or from the item file name.
        """
        try:
            content = item.get_content()
        except Exception as exc:
            logger.debug("Could not get content from item: %s", exc)
            return ""

        if not content:
            return ""

        try:
            soup = BeautifulSoup(content, "html.parser")
        except Exception as exc:
            logger.debug("Could not parse item HTML: %s", exc)
            return ""

        # Try to find chapter title from heading tags
        chapter_title = ""
        for heading_tag in ["h1", "h2", "h3", "h4"]:
            heading = soup.find(heading_tag)
            if heading:
                chapter_title = heading.get_text(strip=True)
                break

        if not chapter_title:
            # Use filename as fallback title
            file_name = getattr(item, "file_name", "")
            if file_name:
                # Clean up filename: remove path and extension
                chapter_title = file_name.rsplit("/", 1)[-1].rsplit(".", 1)[0]
                chapter_title = chapter_title.replace("_", " ").replace("-", " ").title()

        # Extract all text
        text = soup.get_text(separator="\n", strip=True)

        if not text or not text.strip():
            return ""

        # Collapse excessive blank lines
        lines = [line for line in text.splitlines() if line.strip()]
        body_text = "\n".join(lines)

        if chapter_title:
            return f"## {chapter_title}\n\n{body_text}"
        return body_text
