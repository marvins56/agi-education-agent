"""Synchronous HTTP client wrapper for the EduAGI API."""

from __future__ import annotations

import httpx

from src.cli.config import clear_credentials, get_api_url, load_credentials, save_credentials


class CLIError(Exception):
    """Friendly CLI error with a message suitable for display."""


class CLIClient:
    """Sync httpx wrapper that injects Bearer tokens and handles 401 refresh."""

    def __init__(self) -> None:
        self.base_url = get_api_url()

    def _headers(self) -> dict[str, str]:
        creds = load_credentials()
        if creds and creds.get("access_token"):
            return {"Authorization": f"Bearer {creds['access_token']}"}
        return {}

    def _try_refresh(self) -> bool:
        """Attempt to refresh the access token. Returns True on success."""
        creds = load_credentials()
        if not creds or not creds.get("refresh_token"):
            return False
        try:
            resp = httpx.post(
                f"{self.base_url}/auth/refresh",
                json={"refresh_token": creds["refresh_token"]},
                timeout=10.0,
            )
            if resp.status_code == 200:
                data = resp.json()
                save_credentials(
                    access_token=data["access_token"],
                    refresh_token=data["refresh_token"],
                    email=creds.get("email", ""),
                )
                return True
        except httpx.HTTPError:
            pass
        return False

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict | None = None,
        params: dict | None = None,
        authenticated: bool = True,
    ) -> httpx.Response:
        url = f"{self.base_url}{path}"
        headers = self._headers() if authenticated else {}

        try:
            resp = httpx.request(method, url, json=json, params=params, headers=headers, timeout=60.0)
        except httpx.ConnectError:
            raise CLIError(
                "Cannot connect to the EduAGI server. "
                f"Is it running at {self.base_url}?"
            )
        except httpx.HTTPError as exc:
            raise CLIError(f"Network error: {exc}")

        # Auto-refresh on 401
        if resp.status_code == 401 and authenticated and self._try_refresh():
            headers = self._headers()
            try:
                resp = httpx.request(method, url, json=json, params=params, headers=headers, timeout=60.0)
            except httpx.HTTPError as exc:
                raise CLIError(f"Network error after token refresh: {exc}")

        if resp.status_code == 401:
            clear_credentials()
            raise CLIError("Session expired. Please log in again with: eduagi login")

        if resp.status_code == 403:
            raise CLIError("Permission denied. You do not have access to this resource.")

        if resp.status_code == 429:
            raise CLIError("Rate limited. Please wait a moment and try again.")

        if resp.status_code >= 500:
            raise CLIError(f"Server error ({resp.status_code}). Please try again later.")

        if resp.status_code >= 400:
            detail = ""
            try:
                detail = resp.json().get("detail", "")
            except Exception:
                pass
            raise CLIError(detail or f"Request failed with status {resp.status_code}")

        return resp

    def get(self, path: str, *, params: dict | None = None, authenticated: bool = True) -> httpx.Response:
        return self._request("GET", path, params=params, authenticated=authenticated)

    def post(self, path: str, *, json: dict | None = None, authenticated: bool = True) -> httpx.Response:
        return self._request("POST", path, json=json, authenticated=authenticated)

    def delete(self, path: str, *, authenticated: bool = True) -> httpx.Response:
        return self._request("DELETE", path, authenticated=authenticated)
