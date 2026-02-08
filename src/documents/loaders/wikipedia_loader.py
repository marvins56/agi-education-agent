"""Wikipedia article loader."""
import logging
import wikipedia

logger = logging.getLogger(__name__)

class WikipediaLoader:
    """Fetch articles from Wikipedia."""

    async def load(self, query: str, lang: str = "en", sentences: int = 0) -> dict:
        """Load a Wikipedia article by search query.

        Args:
            query: Search term
            lang: Language code (default 'en')
            sentences: If >0, only return this many sentences (0 = full article)
        """
        wikipedia.set_lang(lang)
        try:
            # Search for the page
            results = wikipedia.search(query, results=3)
            if not results:
                raise ValueError(f"No Wikipedia articles found for '{query}'")

            # Try each result until one works (handles disambiguation)
            page = None
            for result_title in results:
                try:
                    if sentences > 0:
                        page = wikipedia.page(result_title, auto_suggest=False)
                    else:
                        page = wikipedia.page(result_title, auto_suggest=False)
                    break
                except wikipedia.DisambiguationError as e:
                    # Pick the first option from disambiguation
                    if e.options:
                        try:
                            page = wikipedia.page(e.options[0], auto_suggest=False)
                            break
                        except Exception:
                            continue
                except wikipedia.PageError:
                    continue

            if page is None:
                raise ValueError(f"Could not load any Wikipedia page for '{query}'")

            text = page.summary if sentences > 0 else page.content

            return {
                "text": text,
                "title": page.title,
                "metadata": {
                    "source_type": "wikipedia",
                    "url": page.url,
                    "page_id": page.pageid,
                    "language": lang,
                    "categories": page.categories[:10] if page.categories else [],
                    "references_count": len(page.references) if page.references else 0,
                },
                "source_type": "wikipedia",
            }
        except ValueError:
            raise
        except Exception as exc:
            logger.error("Failed to load Wikipedia article for '%s': %s", query, exc)
            raise ValueError(f"Could not load Wikipedia article for '{query}': {exc}") from exc
