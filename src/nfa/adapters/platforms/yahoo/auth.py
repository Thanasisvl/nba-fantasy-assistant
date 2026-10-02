"""Yahoo OAuth2 (Confidential Client, read-only). ADR 0006.

Login: print authorize_url(), the user approves and pastes the redirected URL,
code_from_redirect() extracts the code, exchange_code() stores tokens in the Keychain.
"""

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import parse_qs, urlencode, urlsplit

import requests

from nfa import clock
from nfa.adapters import secrets
from nfa.adapters.http import AuthError

AUTHORIZE_URL = "https://api.login.yahoo.com/oauth2/request_auth"
TOKEN_URL = "https://api.login.yahoo.com/oauth2/get_token"
REDIRECT_URI = "https://localhost:8765/callback"
CLIENT_ID_ACCOUNT = "yahoo_client_id"
CLIENT_SECRET_ACCOUNT = "yahoo_client_secret"
TOKENS_ACCOUNT = "yahoo_tokens"
REFRESH_MARGIN = timedelta(minutes=5)
SCOPE = (
    "fspt-r"  # Fantasy Sports read-only; without it Yahoo may issue a token with no Fantasy access
)
LOGIN_HINT = "run `uv run python -m nfa.jobs.login`"


@dataclass(frozen=True)
class Tokens:
    access_token: str = field(repr=False)
    refresh_token: str = field(repr=False)
    expires_at: datetime

    def to_json(self) -> str:
        return json.dumps(
            {
                "access_token": self.access_token,
                "refresh_token": self.refresh_token,
                "expires_at": self.expires_at.isoformat(),
            }
        )

    @classmethod
    def from_json(cls, text: str) -> "Tokens":
        data = json.loads(text)
        return cls(
            data["access_token"], data["refresh_token"], datetime.fromisoformat(data["expires_at"])
        )


def authorize_url(client_id: str) -> str:
    query = urlencode(
        {
            "client_id": client_id,
            "redirect_uri": REDIRECT_URI,
            "response_type": "code",
            "scope": SCOPE,
        }
    )
    return f"{AUTHORIZE_URL}?{query}"


def code_from_redirect(pasted: str) -> str:
    """Extracts the authorization code. Error messages never repeat the pasted text."""
    text, previous = pasted, None
    while text != previous:
        previous, text = text, text.strip(" \t\r\n'\"<>")
    parts = urlsplit(text)
    expected = urlsplit(REDIRECT_URI)
    try:
        port = parts.port
    except ValueError:
        port = None
    if (parts.scheme, parts.hostname, port, parts.path) != (
        expected.scheme,
        expected.hostname,
        expected.port,
        expected.path,
    ):
        raise ValueError(
            f"Paste the full address Yahoo redirected to; it starts with {REDIRECT_URI}"
        )
    codes = parse_qs(parts.query).get("code")
    if not codes or not codes[0]:
        raise ValueError("The pasted address has no 'code' parameter; approve the login again.")
    return codes[0]


class YahooAuth:
    def __init__(
        self,
        *,
        get_secret: Callable[[str], str] = secrets.get_secret,
        set_secret: Callable[[str, str], None] = secrets.set_secret,
        post: Callable[..., Any] = requests.post,
        now: Callable[[], datetime] = clock.now,
    ) -> None:
        self._get_secret = get_secret
        self._set_secret = set_secret
        self._post = post
        self._now = now
        self.refreshed_at: datetime | None = None
        # Cached so one run reads the Keychain once (each read may show a macOS dialog).
        self._credentials: tuple[str, str] | None = None
        self._tokens: Tokens | None = None

    def client_id(self) -> str:
        return self._client_credentials()[0]

    def _client_credentials(self) -> tuple[str, str]:
        if self._credentials is None:
            self._credentials = (
                self._get_secret(CLIENT_ID_ACCOUNT),
                self._get_secret(CLIENT_SECRET_ACCOUNT),
            )
        return self._credentials

    def exchange_code(self, code: str) -> Tokens:
        return self._token_request({"grant_type": "authorization_code", "code": code})

    def access_token(self) -> str:
        if self._tokens is None:
            try:
                self._tokens = Tokens.from_json(self._get_secret(TOKENS_ACCOUNT))
            except secrets.MissingSecretError as exc:
                raise AuthError(f"No Yahoo tokens stored; {LOGIN_HINT}") from exc
        tokens = self._tokens
        if tokens.expires_at - self._now() <= REFRESH_MARGIN:
            tokens = self._token_request(
                {"grant_type": "refresh_token", "refresh_token": tokens.refresh_token},
                previous_refresh=tokens.refresh_token,
            )
            self.refreshed_at = self._now()
        return tokens.access_token

    def _token_request(self, data: dict[str, str], previous_refresh: str | None = None) -> Tokens:
        response = self._post(
            TOKEN_URL,
            auth=self._client_credentials(),
            data={**data, "redirect_uri": REDIRECT_URI},
            timeout=20.0,
        )
        if response.status_code != 200:
            raise AuthError(
                f"Yahoo token endpoint returned HTTP {response.status_code}; {LOGIN_HINT}"
            )
        body = response.json()
        tokens = Tokens(
            access_token=body["access_token"],
            refresh_token=body.get("refresh_token") or previous_refresh or "",
            expires_at=self._now() + timedelta(seconds=int(body["expires_in"])),
        )
        self._set_secret(TOKENS_ACCOUNT, tokens.to_json())
        self._tokens = tokens
        return tokens
