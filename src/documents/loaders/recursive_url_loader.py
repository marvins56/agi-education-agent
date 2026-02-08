"""Recursive URL crawler for ingesting entire websites."""
import logging
import re
from urllib.parse import urljoin, urlparse
from collections import deque

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_STRIP_TAGS = {"nav", "footer", "header", "aside", "script", "style", "noscript", "iframe"}
_MAX_PAGE_SIZE = 5 * 1024 * 1024  # 5MB per page

class RecursiveURLLoader:
    """Crawl a website and extract text from all pages."""

    async def load(self, url: str, max_depth: int = 2, max_pages: int = 20) -> list[dict]:
        """Crawl a URL recursively and return page content.

        Args:
            url: Starting URL to crawl
            max_depth: Maximum depth of crawling (default 2)
            max_pages: Maximum number of pages to process (default 20, max 50)
        """
        max_depth = min(max(1, max_depth), 5)
        max_pages = min(max(1, max_pages), 50)

        base_domain = urlparse(url).netloc
        visited: set[str] = set()
        results: list[dict] = []
        queue: deque[tuple[str, int]] = deque([(url, 0)])

        try:
            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True, max_redirects=3) as client:
                while queue and len(results) < max_pages:
                    current_url, depth = queue.popleft()

                    # Normalize URL
                    normalized = current_url.split("#")[0].rstrip("/")
                    if normalized in visited:
                        continue
                    visited.add(normalized)

                    try:
                        page_result = await self._fetch_page(client, current_url)
                        if page_result:
                            results.append(page_result)

                            # Find and queue links if not at max depth
                            if depth < max_depth:
                                links = self._extract_links(page_result.get("_html", ""), current_url, base_domain)
                                for link in links:
                                    link_normalized = link.split("#")[0].rstrip("/")
                                    if link_normalized not in visited:
                                        queue.append((link, depth + 1))

                            # Remove internal HTML from result
                            page_result.pop("_html", None)
                    except Exception as exc:
                        logger.debug("Failed to fetch %s: %s", current_url, exc)
                        continue

            if not results:
                raise ValueError(f"Could not fetch any pages from '{url}'")

            return results

        except ValueError:
            raise
        except Exception as exc:
            logger.error("Recursive URL crawl failed for '%s': %s", url, exc)
            raise ValueError(f"Crawl failed for '{url}': {exc}") from exc

    async def _fetch_page(self, client: httpx.AsyncClient, url: str) -> dict | None:
        """Fetch and parse a single page."""
        try:
            resp = await client.get(url)
            resp.raise_for_status()

            content_type = resp.headers.get("content-type", "")
            if "text/html" not in content_type:
                return None

            if len(resp.content) > _MAX_PAGE_SIZE:
                return None

            html = resp.text
            soup = BeautifulSoup(html, "lxml")

            # Get title
            title = ""
            title_tag = soup.find("title")
            if title_tag:
                title = title_tag.get_text(strip=True)

            # Strip unwanted tags
            for tag in soup.find_all(_STRIP_TAGS):
                tag.decompose()

            # Extract main content
            main = soup.find("main") or soup.find("article") or soup.find("body")
            if main is None:
                main = soup

            text = main.get_text(separator="\n", strip=True)
            lines = [line for line in text.splitlines() if line.strip()]
            clean_text = "\n".join(lines)

            if not clean_text or len(clean_text) < 50:
                return None

            return {
                "text": clean_text,
                "title": title or url,
                "metadata": {
                    "source_type": "web_crawl",
                    "url": str(resp.url),
                    "word_count": len(clean_text.split()),
                },
                "source_type": "web_crawl",
                "_html": html,  # Temporary, for link extraction
            }
        except Exception:
            return None

    def _extract_links(self, html: str, base_url: str, base_domain: str) -> list[str]:
        """Extract same-domain links from HTML."""
        links = []
        try:
            soup = BeautifulSoup(html, "lxml")
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                full_url = urljoin(base_url, href)
                parsed = urlparse(full_url)

                # Only follow same-domain HTTP(S) links
                if parsed.scheme in ("http", "https") and parsed.netloc == base_domain:
                    # Skip common non-content URLs
                    skip_patterns = ["/login", "/signup", "/logout", "/api/", "/admin", ".pdf", ".zip", ".jpg", ".png"]
                    if not any(p in full_url.lower() for p in skip_patterns):
                        links.append(full_url)
        except Exception:
            pass
        return links[:50]  # Limit discovered links per page
