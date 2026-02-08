"""GitHub repository file loader."""
import logging
import httpx

logger = logging.getLogger(__name__)

_RAW_URL = "https://raw.githubusercontent.com"
_API_URL = "https://api.github.com"

# File extensions we'll try to load from repos
_LOADABLE_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".md", ".txt", ".rst",
    ".java", ".cpp", ".c", ".h", ".go", ".rs", ".rb", ".php",
    ".html", ".css", ".json", ".yaml", ".yml", ".toml", ".xml",
    ".sh", ".bash", ".r", ".jl", ".ipynb", ".sql",
}

class GitHubLoader:
    """Fetch files from public GitHub repositories."""

    async def load(self, repo: str, file_path: str | None = None, branch: str = "main") -> dict | list[dict]:
        """Load file(s) from a GitHub repository.

        Args:
            repo: Repository in 'owner/repo' format
            file_path: Specific file path (if None, loads README)
            branch: Branch name (default 'main')
        """
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                if file_path:
                    return await self._load_single_file(client, repo, file_path, branch)
                else:
                    return await self._load_readme(client, repo, branch)
        except ValueError:
            raise
        except Exception as exc:
            logger.error("GitHub load failed for %s: %s", repo, exc)
            raise ValueError(f"Failed to load from GitHub repo '{repo}': {exc}") from exc

    async def _load_single_file(self, client: httpx.AsyncClient, repo: str, file_path: str, branch: str) -> dict:
        """Load a single file from the repository."""
        url = f"{_RAW_URL}/{repo}/{branch}/{file_path}"
        resp = await client.get(url)

        if resp.status_code == 404:
            # Try 'master' branch as fallback
            if branch == "main":
                url = f"{_RAW_URL}/{repo}/master/{file_path}"
                resp = await client.get(url)

        if resp.status_code == 404:
            raise ValueError(f"File not found: {repo}/{file_path}")
        resp.raise_for_status()

        return {
            "text": resp.text,
            "title": f"{repo}/{file_path}",
            "metadata": {
                "source_type": "github",
                "repo": repo,
                "file_path": file_path,
                "branch": branch,
                "url": f"https://github.com/{repo}/blob/{branch}/{file_path}",
            },
            "source_type": "github",
        }

    async def _load_readme(self, client: httpx.AsyncClient, repo: str, branch: str) -> dict:
        """Load the README file from a repository."""
        for readme_name in ["README.md", "readme.md", "README.rst", "README.txt", "README"]:
            try:
                result = await self._load_single_file(client, repo, readme_name, branch)
                return result
            except (ValueError, httpx.HTTPStatusError):
                continue

        raise ValueError(f"No README found in {repo}")
