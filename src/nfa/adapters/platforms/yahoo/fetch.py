"""Yahoo Fantasy API: GET only (read-only, ADR 0002). Returns RawResponse; no parsing here."""

import time
from collections.abc import Callable
from typing import Protocol

import requests

from nfa.adapters import http
from nfa.adapters.http import HttpSession, Throttle
from nfa.domain.raw import FetchRequest, RawResponse

BASE_URL = "https://fantasysports.yahooapis.com/fantasy/v2/"


class TokenProvider(Protocol):
    def access_token(self) -> str: ...


def yahoo_request(dataset: str, key: str, path: str) -> FetchRequest:
    return FetchRequest(source="yahoo", dataset=dataset, key=key, params={"path": path})


class YahooFetcher:
    source = "yahoo"

    def __init__(
        self,
        auth: TokenProvider,
        throttle: Throttle,
        session: HttpSession | None = None,
        *,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._auth = auth
        self._throttle = throttle
        self._session: HttpSession = session if session is not None else requests.Session()
        self._sleep = sleep

    def fetch(self, request: FetchRequest) -> RawResponse:
        if request.source != self.source:
            raise ValueError(f"YahooFetcher cannot fetch source {request.source!r}")
        path = request.params["path"].lstrip("/")
        return http.get(
            request,
            BASE_URL + path,
            session=self._session,
            throttle=self._throttle,
            params={"format": "json"},
            headers={"Authorization": f"Bearer {self._auth.access_token()}"},
            sleep=self._sleep,
        )
