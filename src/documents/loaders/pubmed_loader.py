"""PubMed biomedical literature loader."""
import logging
import xmltodict
import httpx

logger = logging.getLogger(__name__)

_ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
_EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

class PubMedLoader:
    """Fetch articles from PubMed biomedical database."""

    async def load(self, query: str, max_results: int = 3) -> list[dict]:
        """Search PubMed and return article abstracts.

        Args:
            query: Search term (e.g., 'CRISPR gene editing')
            max_results: Maximum articles to return (1-10)
        """
        max_results = min(max(1, max_results), 10)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Step 1: Search for IDs
                search_resp = await client.get(_ESEARCH_URL, params={
                    "db": "pubmed",
                    "term": query,
                    "retmax": max_results,
                    "retmode": "json",
                })
                search_resp.raise_for_status()
                search_data = search_resp.json()
                id_list = search_data.get("esearchresult", {}).get("idlist", [])

                if not id_list:
                    raise ValueError(f"No PubMed articles found for '{query}'")

                # Step 2: Fetch article details
                fetch_resp = await client.get(_EFETCH_URL, params={
                    "db": "pubmed",
                    "id": ",".join(id_list),
                    "retmode": "xml",
                })
                fetch_resp.raise_for_status()

                parsed = xmltodict.parse(fetch_resp.text)
                articles_raw = parsed.get("PubmedArticleSet", {}).get("PubmedArticle", [])

                # Ensure it's always a list
                if isinstance(articles_raw, dict):
                    articles_raw = [articles_raw]

                results = []
                for article_data in articles_raw:
                    try:
                        article = article_data.get("MedlineCitation", {}).get("Article", {})
                        title = article.get("ArticleTitle", "Untitled")
                        if isinstance(title, dict):
                            title = title.get("#text", "Untitled")

                        abstract_data = article.get("Abstract", {}).get("AbstractText", "")
                        if isinstance(abstract_data, list):
                            abstract = " ".join(
                                item.get("#text", str(item)) if isinstance(item, dict) else str(item)
                                for item in abstract_data
                            )
                        elif isinstance(abstract_data, dict):
                            abstract = abstract_data.get("#text", str(abstract_data))
                        else:
                            abstract = str(abstract_data)

                        # Get authors
                        author_list = article.get("AuthorList", {}).get("Author", [])
                        if isinstance(author_list, dict):
                            author_list = [author_list]
                        authors = []
                        for a in author_list:
                            last = a.get("LastName", "")
                            first = a.get("ForeName", "")
                            if last:
                                authors.append(f"{last} {first}".strip())

                        pmid = article_data.get("MedlineCitation", {}).get("PMID", {})
                        if isinstance(pmid, dict):
                            pmid = pmid.get("#text", "")

                        text_parts = [f"# {title}"]
                        if authors:
                            text_parts.append(f"\n**Authors:** {', '.join(authors[:5])}")
                        text_parts.append(f"\n## Abstract\n\n{abstract}")

                        results.append({
                            "text": "\n".join(text_parts),
                            "title": title,
                            "metadata": {
                                "source_type": "pubmed",
                                "pmid": str(pmid),
                                "authors": authors[:5],
                                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                            },
                            "source_type": "pubmed",
                        })
                    except Exception as exc:
                        logger.debug("Failed to parse PubMed article: %s", exc)
                        continue

                if not results:
                    raise ValueError(f"Could not parse any PubMed results for '{query}'")

                return results

        except ValueError:
            raise
        except Exception as exc:
            logger.error("PubMed search failed for '%s': %s", query, exc)
            raise ValueError(f"PubMed search failed for '{query}': {exc}") from exc
