# 0006. Own small Yahoo OAuth module

Date: 2026-10-01 · Status: accepted

## Context

Yahoo uses OAuth2 (authorization code with refresh tokens). Community libraries exist (`yahoo_oauth`, used by `yfpy` and others) but store tokens in JSON files by default and are maintained by volunteers. The flow itself is small.

## Decision

Write our own module (`adapters/platforms/yahoo/auth.py`, roughly 100 lines with `requests`): authorize URL, code exchange, refresh before expiry, tokens and client credentials in the macOS Keychain via `keyring`. Read scope only.

## Consequences

- Full control over where secrets live and how errors are reported (a failed refresh becomes a "Yahoo login needed" health event).
- No dependency on a lightly maintained library for the most security-sensitive part.
- We own the edge cases (redirect URI rules, token expiry); the M0 spike confirms which redirect Yahoo accepts.
