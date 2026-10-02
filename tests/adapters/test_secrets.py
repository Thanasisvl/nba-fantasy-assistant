import pytest

from nfa.adapters.secrets import SERVICE, MissingSecretError, get_secret, set_secret


def test_set_then_get_uses_project_service(memory_keyring) -> None:
    set_secret("yahoo_client_id", "cid-value")
    assert get_secret("yahoo_client_id") == "cid-value"
    assert (SERVICE, "yahoo_client_id") in memory_keyring.store
    assert SERVICE == "nba-fantasy-assistant"


def test_missing_secret_names_account_not_value() -> None:
    with pytest.raises(MissingSecretError) as excinfo:
        get_secret("yahoo_tokens")
    assert "yahoo_tokens" in str(excinfo.value)
