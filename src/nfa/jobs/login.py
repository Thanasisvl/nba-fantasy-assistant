"""Yahoo login: `uv run python -m nfa.jobs.login`. The pasted URL is read without echo."""

import getpass
from collections.abc import Callable
from typing import Any

from nfa.adapters.http import AuthError, FetchError, Throttle
from nfa.adapters.platforms.yahoo.auth import (
    REDIRECT_URI,
    YahooAuth,
    authorize_url,
    code_from_redirect,
)
from nfa.adapters.platforms.yahoo.fetch import YahooFetcher, yahoo_request
from nfa.adapters.secrets import SERVICE, MissingSecretError
from nfa.config import load_config


def _default_fetcher(auth: YahooAuth) -> YahooFetcher:
    return YahooFetcher(auth, Throttle(load_config().throttle_s))


def main(
    *,
    auth: YahooAuth | None = None,
    fetcher_factory: Callable[[YahooAuth], Any] | None = None,
    read_hidden: Callable[[str], str] = getpass.getpass,
    out: Callable[[str], None] = print,
) -> int:
    auth = auth or YahooAuth()
    try:
        client_id = auth.client_id()
    except MissingSecretError:
        out("Yahoo client credentials are not in the Keychain. Add them with:")
        out(f"  security add-generic-password -U -s {SERVICE} -a yahoo_client_id -w")
        out(f"  security add-generic-password -U -s {SERVICE} -a yahoo_client_secret -w")
        return 2

    out("1. Open this URL, sign in and approve read access:")
    out(f"   {authorize_url(client_id)}")
    out(f"2. The browser then shows an error page at {REDIRECT_URI}. Copy the full address.")
    pasted = read_hidden("3. Paste it here (hidden) and press Enter: ")
    try:
        auth.exchange_code(code_from_redirect(pasted))
    except (ValueError, AuthError, MissingSecretError) as exc:
        out(f"Login failed: {exc}")
        return 1

    fetcher = (fetcher_factory or _default_fetcher)(auth)
    try:
        raw = fetcher.fetch(yahoo_request("games", "nba", "games;game_keys=nba"))
    except FetchError as exc:
        out(f"Tokens saved, but the test call failed: {exc}")
        return 1
    out(f"Logged in. Tokens saved in the Keychain. Test call returned HTTP {raw.status}.")
    return 0 if raw.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
