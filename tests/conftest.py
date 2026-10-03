import socket
from collections.abc import Iterator

import keyring
import pytest

from tests.fakes import MemoryKeyring


@pytest.fixture(autouse=True)
def _no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def guard(*args: object, **kwargs: object) -> None:
        raise RuntimeError("Tests must not use the network; use a fake.")

    monkeypatch.setattr(socket.socket, "connect", guard)


@pytest.fixture(autouse=True)
def memory_keyring() -> Iterator[MemoryKeyring]:
    previous = keyring.get_keyring()
    backend = MemoryKeyring()
    keyring.set_keyring(backend)
    yield backend
    keyring.set_keyring(previous)
