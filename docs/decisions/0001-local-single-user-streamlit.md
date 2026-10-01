# 0001. Local, single-user Streamlit app

Date: 2026-10-01 · Status: accepted

## Context

The tool is for one person managing a few Yahoo leagues. There is no deadline, no budget, and the main NBA stats source (stats.nba.com via `nba_api`) blocks many cloud IPs. A commercial version is possible later but not designed for now.

## Decision

Run everything locally on my Mac: a Streamlit app for on-demand use and a launchd-scheduled daily job, sharing the same services. No accounts, no hosting, no server process.

## Consequences

- $0 running cost; `nba_api` works from a home IP.
- The daily job only runs when the Mac is awake; launchd runs missed jobs on wake, and the digest marks itself late.
- Streamlit is quick to build with but limited for mobile and multi-user use. Keeping all logic in services means a web front end can replace it later without touching the core.
