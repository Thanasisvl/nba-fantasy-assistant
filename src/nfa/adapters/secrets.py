"""macOS Keychain access via keyring. Values are never printed or logged."""

import keyring

SERVICE = "nba-fantasy-assistant"


class MissingSecretError(Exception):
    pass


def get_secret(account: str) -> str:
    value = keyring.get_password(SERVICE, account)
    if value is None:
        raise MissingSecretError(f"No Keychain entry for service {SERVICE!r}, account {account!r}")
    return value


def set_secret(account: str, value: str) -> None:
    keyring.set_password(SERVICE, account, value)
