"""Project Gutenberg public domain book loader."""
import logging
import re
import httpx

logger = logging.getLogger(__name__)

_SEARCH_URL = "https://gutendex.com/books"

class GutenbergLoader:
    """Fetch public domain books from Project Gutenberg."""

    async def load(self, query: str, max_results: int = 1) -> list[dict]:
        """Search and load books from Project Gutenberg.

        Args:
            query: Book title or author to search for
            max_results: Max books to return (1-5)
        """
        max_results = min(max(1, max_results), 5)

        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                # Search via Gutendex API
                search_resp = await client.get(_SEARCH_URL, params={"search": query})
                search_resp.raise_for_status()
                data = search_resp.json()

                books = data.get("results", [])[:max_results]
                if not books:
                    raise ValueError(f"No Gutenberg books found for '{query}'")

                results = []
                for book in books:
                    try:
                        title = book.get("title", "Unknown Title")
                        authors = [a.get("name", "") for a in book.get("authors", [])]
                        book_id = book.get("id", 0)

                        # Get the plain text URL
                        formats = book.get("formats", {})
                        text_url = (
                            formats.get("text/plain; charset=utf-8")
                            or formats.get("text/plain; charset=us-ascii")
                            or formats.get("text/plain")
                        )

                        if not text_url:
                            logger.warning("No plain text available for Gutenberg book %d", book_id)
                            continue

                        # Fetch the text (limit to first 100KB for very long books)
                        text_resp = await client.get(text_url)
                        text_resp.raise_for_status()
                        full_text = text_resp.text

                        # Strip Gutenberg header/footer boilerplate
                        text = self._strip_gutenberg_boilerplate(full_text)

                        # Truncate if very long (over 200KB of text)
                        truncated = False
                        if len(text) > 200_000:
                            text = text[:200_000]
                            truncated = True

                        results.append({
                            "text": text,
                            "title": title,
                            "metadata": {
                                "source_type": "gutenberg",
                                "gutenberg_id": book_id,
                                "authors": authors,
                                "subjects": book.get("subjects", [])[:5],
                                "languages": book.get("languages", []),
                                "download_count": book.get("download_count", 0),
                                "truncated": truncated,
                                "url": f"https://www.gutenberg.org/ebooks/{book_id}",
                            },
                            "source_type": "gutenberg",
                        })
                    except Exception as exc:
                        logger.debug("Failed to fetch Gutenberg book: %s", exc)
                        continue

                if not results:
                    raise ValueError(f"Could not fetch any books for '{query}'")

                return results

        except ValueError:
            raise
        except Exception as exc:
            logger.error("Gutenberg search failed for '%s': %s", query, exc)
            raise ValueError(f"Gutenberg search failed: {exc}") from exc

    def _strip_gutenberg_boilerplate(self, text: str) -> str:
        """Remove Project Gutenberg header and footer."""
        # Common start markers
        start_markers = [
            "*** START OF THIS PROJECT GUTENBERG",
            "*** START OF THE PROJECT GUTENBERG",
            "***START OF THE PROJECT GUTENBERG",
        ]
        # Common end markers
        end_markers = [
            "*** END OF THIS PROJECT GUTENBERG",
            "*** END OF THE PROJECT GUTENBERG",
            "***END OF THE PROJECT GUTENBERG",
            "End of the Project Gutenberg",
            "End of Project Gutenberg",
        ]

        for marker in start_markers:
            idx = text.find(marker)
            if idx != -1:
                # Find the end of the line containing the marker
                newline = text.find("\n", idx)
                if newline != -1:
                    text = text[newline + 1:]
                break

        for marker in end_markers:
            idx = text.find(marker)
            if idx != -1:
                text = text[:idx]
                break

        return text.strip()
