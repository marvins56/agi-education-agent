"""ArXiv research paper loader."""
import logging
import arxiv

logger = logging.getLogger(__name__)

class ArxivLoader:
    """Fetch research papers from ArXiv."""

    async def load(self, query: str, max_results: int = 1) -> list[dict]:
        """Search ArXiv and return paper summaries.

        Args:
            query: Search query or ArXiv paper ID (e.g., '2301.07041')
            max_results: Maximum number of papers to return (1-10)

        Returns list of dicts, each with text/title/metadata.
        """
        max_results = min(max(1, max_results), 10)

        try:
            client = arxiv.Client()
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.Relevance,
            )

            results = []
            for paper in client.results(search):
                # Build comprehensive text from paper
                text_parts = [
                    f"# {paper.title}",
                    f"\n**Authors:** {', '.join(a.name for a in paper.authors)}",
                    f"\n**Published:** {paper.published.strftime('%Y-%m-%d') if paper.published else 'Unknown'}",
                    f"\n**Categories:** {', '.join(paper.categories)}",
                    f"\n## Abstract\n\n{paper.summary}",
                ]

                if paper.comment:
                    text_parts.append(f"\n**Comment:** {paper.comment}")

                results.append({
                    "text": "\n".join(text_parts),
                    "title": paper.title,
                    "metadata": {
                        "source_type": "arxiv",
                        "arxiv_id": paper.entry_id,
                        "authors": [a.name for a in paper.authors],
                        "published": paper.published.isoformat() if paper.published else "",
                        "categories": paper.categories,
                        "pdf_url": paper.pdf_url or "",
                        "doi": paper.doi or "",
                    },
                    "source_type": "arxiv",
                })

            if not results:
                raise ValueError(f"No ArXiv papers found for '{query}'")

            return results

        except ValueError:
            raise
        except Exception as exc:
            logger.error("Failed to search ArXiv for '%s': %s", query, exc)
            raise ValueError(f"ArXiv search failed for '{query}': {exc}") from exc
