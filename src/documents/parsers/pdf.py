"""Production-grade PDF parser with OCR fallback, table extraction, and image detection.

Uses PyMuPDF (fitz) as the primary extraction engine, with pdfplumber for table
extraction and pytesseract for OCR on scanned/image-heavy pages. Each dependency
degrades gracefully if unavailable.
"""

import io
import logging
import signal
import threading
from contextlib import contextmanager
from typing import Any, Generator

import fitz  # PyMuPDF — required

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional dependency availability flags
# ---------------------------------------------------------------------------
_HAS_PDFPLUMBER = False
try:
    import pdfplumber

    _HAS_PDFPLUMBER = True
except ImportError:
    logger.info("pdfplumber not available — table extraction disabled")

_HAS_TESSERACT = False
try:
    import pytesseract
    from PIL import Image

    _HAS_TESSERACT = True
except ImportError:
    logger.info("pytesseract/Pillow not available — OCR disabled")

# If pytesseract is importable, verify that the tesseract binary is reachable.
if _HAS_TESSERACT:
    try:
        pytesseract.get_tesseract_version()
    except Exception:
        logger.warning(
            "pytesseract is installed but the tesseract binary was not found on PATH. "
            "OCR will be skipped. Install tesseract-ocr to enable OCR support."
        )
        _HAS_TESSERACT = False

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
# Pages with fewer non-whitespace characters than this are treated as
# "mostly empty" and are candidates for OCR.
_MIN_TEXT_CHARS_FOR_PAGE = 30

# Maximum seconds to spend on OCR for a single page.
_OCR_TIMEOUT_SECONDS = 30

# DPI for rendering pages to images for OCR.
_OCR_RENDER_DPI = 300


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
class _OcrTimeout(Exception):
    """Raised when OCR exceeds the per-page timeout."""


@contextmanager
def _timeout(seconds: int) -> Generator[None, None, None]:
    """Context manager that raises ``_OcrTimeout`` after *seconds*.

    Uses ``signal.alarm`` on Unix.  On platforms that lack ``SIGALRM`` (e.g.
    Windows, or when running inside a thread that is not the main thread) we
    fall back to a threading-based approach which cannot actually interrupt
    native C code but will at least prevent the caller from blocking forever
    on pure-Python work.
    """
    # Fast path — try signal-based alarm (Unix main thread only).
    if hasattr(signal, "SIGALRM"):
        try:
            old_handler = signal.signal(signal.SIGALRM, _alarm_handler)
            signal.alarm(seconds)
            try:
                yield
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
            return
        except ValueError:
            # We're not in the main thread — fall through to threading approach.
            pass

    # Fallback — threading-based timeout.  Cannot interrupt blocking C calls
    # but covers the common case where OCR finishes quickly.
    result: dict[str, Any] = {"expired": False}
    timer = threading.Timer(seconds, lambda: result.update(expired=True))
    timer.start()
    try:
        yield
        if result["expired"]:
            raise _OcrTimeout()
    finally:
        timer.cancel()


def _alarm_handler(signum: int, frame: Any) -> None:  # noqa: ANN401
    raise _OcrTimeout()


def _is_mostly_empty(text: str) -> bool:
    """Return ``True`` if *text* has almost no meaningful content."""
    stripped = text.strip()
    # Count only non-whitespace characters.
    non_ws = sum(1 for ch in stripped if not ch.isspace())
    return non_ws < _MIN_TEXT_CHARS_FOR_PAGE


def _format_table_as_markdown(table: list[list[str | None]]) -> str:
    """Convert a list-of-lists table (from pdfplumber) to Markdown.

    Handles ``None`` cells and ragged rows gracefully.
    """
    if not table or not any(table):
        return ""

    # Normalise: replace None with empty string, ensure consistent column count.
    max_cols = max(len(row) for row in table)
    rows = []
    for row in table:
        normalised = [(cell or "").strip() for cell in row]
        # Pad short rows.
        normalised.extend([""] * (max_cols - len(normalised)))
        rows.append(normalised)

    lines: list[str] = []
    # Header row.
    header = rows[0]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("| " + " | ".join("---" for _ in header) + " |")
    # Body rows.
    for row in rows[1:]:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main parser
# ---------------------------------------------------------------------------
class PdfParser:
    """Extract text, tables, images, and metadata from PDF files.

    Features
    --------
    * **OCR fallback** — pages that yield little/no text are rendered to images
      and run through Tesseract (if available).
    * **Table extraction** — uses pdfplumber to pull tables and formats them as
      Markdown.
    * **Image detection** — reports dimensions and format for each embedded image.
    * **Graceful degradation** — missing optional dependencies (pytesseract,
      pdfplumber) are handled at import time; corrupt pages are skipped with a
      logged warning.
    * **Memory-efficient** — processes pages one-at-a-time; does not hold the
      entire rendered document in memory.
    """

    # ---- public interface --------------------------------------------------

    def parse(self, file_path: str, *, ocr: bool = True) -> str:
        """Return all extractable text from *file_path*.

        Parameters
        ----------
        file_path:
            Path to the PDF file.
        ocr:
            If ``True`` (default) and tesseract is available, scanned pages
            will be OCR'd.  Set to ``False`` to skip OCR entirely.
        """
        result = self._process_document(file_path, ocr=ocr)
        return result["text"]

    def parse_with_metadata(self, file_path: str, *, ocr: bool = True) -> dict:
        """Return text, metadata, tables, and image count from *file_path*.

        Returns
        -------
        dict with keys:
            text : str
            pages : int
            metadata : dict
            tables : list[str]   — each table as a Markdown string
            images : int         — total number of embedded images
        """
        return self._process_document(file_path, ocr=ocr)

    # ---- internal ----------------------------------------------------------

    def _process_document(self, file_path: str, *, ocr: bool) -> dict:
        """Core processing loop.  Iterates page-by-page for memory efficiency."""

        doc = self._open_document(file_path)
        try:
            total_pages = len(doc)
            pdf_metadata = doc.metadata or {}

            all_text_parts: list[str] = []
            all_tables: list[str] = []
            total_images = 0
            has_ocr_pages = False

            for page_num in range(total_pages):
                try:
                    page = doc[page_num]
                except Exception:
                    logger.warning(
                        "Failed to load page %d of '%s' — skipping",
                        page_num + 1,
                        file_path,
                    )
                    continue

                page_result = self._process_page(
                    page,
                    page_num=page_num,
                    file_path=file_path,
                    ocr=ocr,
                )

                all_text_parts.append(page_result["text"])
                all_tables.extend(page_result["tables"])
                total_images += page_result["image_count"]
                if page_result["was_ocr"]:
                    has_ocr_pages = True

            full_text = "\n".join(all_text_parts).strip()

            return {
                "text": full_text,
                "pages": total_pages,
                "metadata": {
                    "title": pdf_metadata.get("title", ""),
                    "author": pdf_metadata.get("author", ""),
                    "subject": pdf_metadata.get("subject", ""),
                    "creator": pdf_metadata.get("creator", ""),
                    "image_count": total_images,
                    "table_count": len(all_tables),
                    "has_ocr_pages": has_ocr_pages,
                    "total_chars": len(full_text),
                },
                "tables": all_tables,
                "images": total_images,
            }
        finally:
            doc.close()

    # -- document-level helpers ----------------------------------------------

    def _open_document(self, file_path: str) -> fitz.Document:
        """Open a PDF, raising a clear error for encrypted files."""
        try:
            doc = fitz.open(file_path)
        except Exception as exc:
            raise RuntimeError(
                f"Unable to open PDF '{file_path}': {exc}"
            ) from exc

        if doc.is_encrypted:
            doc.close()
            raise PermissionError(
                f"PDF '{file_path}' is encrypted/password-protected and cannot be parsed."
            )
        return doc

    # -- page-level processing -----------------------------------------------

    def _process_page(
        self,
        page: fitz.Page,
        *,
        page_num: int,
        file_path: str,
        ocr: bool,
    ) -> dict[str, Any]:
        """Process a single page.  Returns a dict with text, tables, images."""

        page_label = f"page {page_num + 1} of '{file_path}'"
        text_parts: list[str] = []
        tables: list[str] = []
        image_count = 0
        was_ocr = False

        # 1. Native text extraction via PyMuPDF.
        try:
            native_text = page.get_text() or ""
        except Exception:
            logger.warning("Text extraction failed on %s — skipping text", page_label)
            native_text = ""

        # 2. OCR fallback for scanned / image-heavy pages.
        if _is_mostly_empty(native_text) and ocr and _HAS_TESSERACT:
            ocr_text = self._ocr_page(page, page_label=page_label)
            if ocr_text:
                text_parts.append(ocr_text)
                was_ocr = True
            else:
                # OCR produced nothing useful either — keep whatever native
                # text we got (may still be empty).
                text_parts.append(native_text)
        else:
            text_parts.append(native_text)

        # 3. Image extraction / detection via PyMuPDF.
        try:
            image_list = page.get_images(full=True)
            image_count = len(image_list)
            if image_count > 0:
                image_descriptions = self._describe_images(page, image_list)
                text_parts.extend(image_descriptions)
        except Exception:
            logger.warning("Image extraction failed on %s", page_label)

        # 4. Table extraction via pdfplumber.
        if _HAS_PDFPLUMBER:
            page_tables = self._extract_tables(file_path, page_num, page_label)
            tables.extend(page_tables)

        return {
            "text": "\n".join(text_parts),
            "tables": tables,
            "image_count": image_count,
            "was_ocr": was_ocr,
        }

    # -- OCR -----------------------------------------------------------------

    def _ocr_page(self, page: fitz.Page, *, page_label: str) -> str:
        """Render *page* to an image and OCR it with tesseract.

        Returns the recognised text, or an empty string on failure/timeout.
        """
        try:
            with _timeout(_OCR_TIMEOUT_SECONDS):
                # Render at high DPI for better OCR quality.
                zoom = _OCR_RENDER_DPI / 72  # fitz default is 72 DPI
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)
                img_bytes = pix.tobytes("png")

                image = Image.open(io.BytesIO(img_bytes))
                text: str = pytesseract.image_to_string(image)
                logger.debug("OCR produced %d chars on %s", len(text), page_label)
                return text.strip()
        except _OcrTimeout:
            logger.warning(
                "OCR timed out after %ds on %s — skipping",
                _OCR_TIMEOUT_SECONDS,
                page_label,
            )
            return ""
        except Exception:
            logger.warning("OCR failed on %s — skipping", page_label, exc_info=True)
            return ""

    # -- image detection -----------------------------------------------------

    def _describe_images(
        self, page: fitz.Page, image_list: list
    ) -> list[str]:
        """Build a human-readable description for each embedded image."""
        descriptions: list[str] = []
        doc = page.parent  # The owning fitz.Document

        for img_info in image_list:
            try:
                xref = img_info[0]
                base_image = doc.extract_image(xref)
                if base_image:
                    width = base_image.get("width", "?")
                    height = base_image.get("height", "?")
                    img_ext = base_image.get("ext", "unknown")
                    descriptions.append(
                        f"[Image: {width}x{height} {img_ext}]"
                    )
                else:
                    descriptions.append("[Image: unknown format]")
            except Exception:
                descriptions.append("[Image: extraction failed]")
        return descriptions

    # -- table extraction ----------------------------------------------------

    def _extract_tables(
        self, file_path: str, page_num: int, page_label: str
    ) -> list[str]:
        """Use pdfplumber to extract tables from *page_num* and return as Markdown."""
        tables_md: list[str] = []
        try:
            with pdfplumber.open(file_path) as pdf:
                if page_num >= len(pdf.pages):
                    return tables_md
                plumber_page = pdf.pages[page_num]
                raw_tables = plumber_page.extract_tables() or []
                for idx, table in enumerate(raw_tables):
                    md = _format_table_as_markdown(table)
                    if md:
                        tables_md.append(md)
                        logger.debug(
                            "Extracted table %d from %s", idx + 1, page_label
                        )
        except Exception:
            logger.warning(
                "pdfplumber table extraction failed on %s", page_label, exc_info=True
            )
        return tables_md
