"""Web page parser using httpx and BeautifulSoup."""

import ipaddress
import logging
import socket
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

MAX_RESPONSE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_REDIRECTS = 3

# Private/internal network ranges that should be blocked
_BLOCKED_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]

_BLOCKED_HOSTNAMES = {"localhost", "0.0.0.0"}


def _validate_url(url: str) -> None:
    """Validate URL to prevent SSRF attacks.

    Rejects private/internal IPs, non-http(s) schemes, and localhost.
    """
    parsed = urlparse(url)

    # Only allow http and https schemes
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"URL scheme '{parsed.scheme}' is not allowed. Only http and https are permitted.")

    hostname = parsed.hostname
    if not hostname:
        raise ValueError("URL must have a valid hostname.")

    # Reject known dangerous hostnames
    if hostname.lower() in _BLOCKED_HOSTNAMES:
        raise ValueError(f"URL hostname '{hostname}' is not allowed.")

    # Resolve hostname to IP and check against blocked ranges
    try:
        addr_infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        raise ValueError(f"Cannot resolve hostname '{hostname}'.")

    for family, _, _, _, sockaddr in addr_infos:
        ip = ipaddress.ip_address(sockaddr[0])
        for network in _BLOCKED_NETWORKS:
            if ip in network:
                raise ValueError(f"URL resolves to a blocked network address.")


class WebParser:
    """Fetch and extract main content from web pages."""

    STRIP_TAGS = {"nav", "footer", "header", "aside", "script", "style", "noscript", "iframe"}

    async def parse_url(self, url: str) -> str:
        """Fetch a URL and extract the main text content."""
        _validate_url(url)

        async with httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            max_redirects=MAX_REDIRECTS,
        ) as client:
            # Stream response to enforce size limit
            async with client.stream("GET", url) as response:
                response.raise_for_status()

                # Check Content-Length header first if available
                content_length = response.headers.get("content-length")
                if content_length and int(content_length) > MAX_RESPONSE_SIZE:
                    raise ValueError(
                        f"Response size ({content_length} bytes) exceeds "
                        f"maximum allowed ({MAX_RESPONSE_SIZE} bytes)."
                    )

                # Stream and accumulate with size check
                chunks = []
                total_size = 0
                async for chunk in response.aiter_bytes():
                    total_size += len(chunk)
                    if total_size > MAX_RESPONSE_SIZE:
                        raise ValueError(
                            f"Response size exceeds maximum allowed "
                            f"({MAX_RESPONSE_SIZE} bytes)."
                        )
                    chunks.append(chunk)

                body = b"".join(chunks)

        html_text = body.decode("utf-8", errors="replace")
        soup = BeautifulSoup(html_text, "lxml")

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
