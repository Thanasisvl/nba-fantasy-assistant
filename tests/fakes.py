from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from keyring.backend import KeyringBackend

from nfa.adapters.http import Throttle


@dataclass
class FakeResponse:
    status_code: int
    content: bytes = b"{}"


class FakeSession:
    """Replays outcomes in order; an outcome may be a FakeResponse or an exception."""

    def __init__(self, outcomes: list[Any]) -> None:
        self.outcomes = list(outcomes)
        self.calls: list[dict[str, Any]] = []

    def get(
        self,
        url: str,
        *,
        params: Mapping[str, str] | None = None,
        headers: Mapping[str, str] | None = None,
        timeout: float | None = None,
    ) -> FakeResponse:
        self.calls.append(
            {"method": "GET", "url": url, "params": params, "headers": headers, "timeout": timeout}
        )
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


def no_wait_throttle() -> Throttle:
    return Throttle({}, sleep=lambda _s: None, monotonic=lambda: 0.0)


class MemoryKeyring(KeyringBackend):
    priority = 1  # pyright: ignore[reportAssignmentType]

    def __init__(self) -> None:
        super().__init__()
        self.store: dict[tuple[str, str], str] = {}

    def get_password(self, service: str, username: str) -> str | None:
        return self.store.get((service, username))

    def set_password(self, service: str, username: str, password: str) -> None:
        self.store[(service, username)] = password

    def delete_password(self, service: str, username: str) -> None:
        self.store.pop((service, username), None)
