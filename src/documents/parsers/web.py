"""Web page parser using httpx and BeautifulSoup."""

import httpx
from bs4 import BeautifulSoup


class WebParser:
    """Fetch and extract main content from web pages."""

    STRIP_TAGS = {"nav", "footer", "header", "aside", "script", "style", "noscript", "iframe"}

    async def parse_url(self, url: str) -> str:
        """Fetch a URL and extract the main text content."""
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")

        # Remove unwanted elements
        for tag in soup.find_all(self.STRIP_TAGS):
            tag.decompose()

        # Try to find main content area
        main = soup.find("main") or soup.find("article") or soup.find("body")
        if main is None:
            main = soup

        # Extract text with paragraph separation
        text = main.get_text(separator="\n", strip=True)

        # Collapse excessive blank lines
        lines = [line for line in text.splitlines() if line.strip()]
        return "\n".join(lines)
