"""Credential storage and configuration for the EduAGI CLI."""

import json
import os
from pathlib import Path
from typing import Any

CONFIG_DIR = Path.home() / ".eduagi"
CREDENTIALS_FILE = CONFIG_DIR / "credentials.json"

DEFAULT_API_URL = "http://localhost:8000/api/v1"


def get_api_url() -> str:
    """Return the base API URL, respecting EDUAGI_API_URL env var."""
    return os.environ.get("EDUAGI_API_URL", DEFAULT_API_URL)


def _ensure_config_dir() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def save_credentials(access_token: str, refresh_token: str, email: str) -> None:
    """Save credentials to ~/.eduagi/credentials.json with 0600 permissions."""
    _ensure_config_dir()
    data = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "email": email,
    }
    CREDENTIALS_FILE.write_text(json.dumps(data, indent=2))
    os.chmod(CREDENTIALS_FILE, 0o600)


def load_credentials() -> dict[str, Any] | None:
    """Load credentials from disk. Returns None if not logged in."""
    if not CREDENTIALS_FILE.exists():
        return None
    try:
        data = json.loads(CREDENTIALS_FILE.read_text())
        if "access_token" in data:
            return data
    except (json.JSONDecodeError, KeyError):
        pass
    return None


def clear_credentials() -> None:
    """Remove stored credentials."""
    if CREDENTIALS_FILE.exists():
        CREDENTIALS_FILE.unlink()
