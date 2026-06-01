from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class ZohoBooksError(RuntimeError):
    """Raised when Zoho Books authentication or API calls fail."""


@dataclass(frozen=True)
class ZohoBooksConfig:
    client_id: str
    client_secret: str
    refresh_token: str
    organization_id: str | None = None
    accounts_url: str = "https://accounts.zoho.com"
    api_domain: str = "https://www.zohoapis.com"

    @classmethod
    def from_env(cls) -> "ZohoBooksConfig":
        missing = [
            name
            for name in ("ZOHO_BOOKS_CLIENT_ID", "ZOHO_BOOKS_CLIENT_SECRET", "ZOHO_BOOKS_REFRESH_TOKEN")
            if not os.getenv(name)
        ]
        if missing:
            raise ZohoBooksError(f"Missing required Zoho Books environment variables: {', '.join(missing)}")

        return cls(
            client_id=os.environ["ZOHO_BOOKS_CLIENT_ID"],
            client_secret=os.environ["ZOHO_BOOKS_CLIENT_SECRET"],
            refresh_token=os.environ["ZOHO_BOOKS_REFRESH_TOKEN"],
            organization_id=os.getenv("ZOHO_BOOKS_ORGANIZATION_ID"),
            accounts_url=os.getenv("ZOHO_BOOKS_ACCOUNTS_URL", "https://accounts.zoho.com").rstrip("/"),
            api_domain=os.getenv("ZOHO_BOOKS_API_DOMAIN", "https://www.zohoapis.com").rstrip("/"),
        )


class ZohoBooksClient:
    def __init__(self, config: ZohoBooksConfig):
        self.config = config
        self._access_token: str | None = None

    def refresh_access_token(self) -> str:
        params = urlencode(
            {
                "refresh_token": self.config.refresh_token,
                "client_id": self.config.client_id,
                "client_secret": self.config.client_secret,
                "grant_type": "refresh_token",
            }
        )
        payload = self._request_json("POST", f"{self.config.accounts_url}/oauth/v2/token?{params}")
        token = payload.get("access_token")
        if not token:
            raise ZohoBooksError("Zoho token response did not include access_token")
        self._access_token = str(token)
        api_domain = payload.get("api_domain")
        if api_domain:
            object.__setattr__(self.config, "api_domain", str(api_domain).rstrip("/"))
        return self._access_token

    def list_organizations(self) -> dict[str, Any]:
        return self.get("/books/v3/organizations", require_organization=False)

    def list_invoices(self, **params: str) -> dict[str, Any]:
        return self.get("/books/v3/invoices", **params)

    def list_bills(self, **params: str) -> dict[str, Any]:
        return self.get("/books/v3/bills", **params)

    def list_expenses(self, **params: str) -> dict[str, Any]:
        return self.get("/books/v3/expenses", **params)

    def get(self, path: str, require_organization: bool = True, **params: str) -> dict[str, Any]:
        query = dict(params)
        if require_organization:
            if not self.config.organization_id:
                raise ZohoBooksError("ZOHO_BOOKS_ORGANIZATION_ID is required for this Zoho Books API call")
            query["organization_id"] = self.config.organization_id
        suffix = f"?{urlencode(query)}" if query else ""
        return self._request_json("GET", f"{self.config.api_domain}{path}{suffix}", auth=True)

    def _request_json(self, method: str, url: str, auth: bool = False) -> dict[str, Any]:
        headers = {"Accept": "application/json"}
        if auth:
            token = self._access_token or self.refresh_access_token()
            headers["Authorization"] = f"Zoho-oauthtoken {token}"
        request = Request(url, method=method, headers=headers)
        try:
            with urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise ZohoBooksError(f"Zoho Books API error {exc.code}: {body}") from exc


def build_client_from_env() -> ZohoBooksClient:
    return ZohoBooksClient(ZohoBooksConfig.from_env())
