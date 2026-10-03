# 0011. Python, strictly typed and written for a Java reader

Date: 2026-10-03 · Status: accepted

## Context

I'm a senior QA automation engineer, not a developer by trade. I know Java and Spring (from test automation) much better than Python, and I have little UI experience, and I asked whether to switch the project to Java. At that point, M0 code was small (about two days of work). But the product's core is analytics (projections, category win odds, calibration, backtests) and a simple local UI, and Python is much stronger there: `nba_api`, pandas/numpy/scipy, notebooks, Streamlit. In Java, the UI and analytics would take several times more code, and we would have to maintain our own client for stats.nba.com. A later hosted, multi-user product would be re-architected anyway (licensed data, accounts), and that is the right moment to reconsider the language.

## Decision

- Stay in Python.
- `pyright` runs in strict mode on `src/` and `tests/`; no `Any` past untyped boundaries.
- The code follows a plain, Java-like style: Protocols as interfaces, constructor injection with one wiring module, frozen dataclasses as value objects, enums, no metaprogramming.
- Python idioms, application-design concepts and UI concepts are explained in the conversation as they appear and logged once in `.claude/skills/nfa-engineering/references/python-for-java-devs.md`.
- Checkpoint: after M1, if the Python still feels foreign, reconsider before M2, while there's no analytics code yet. Recorded data is language-neutral (gzipped JSON, SQLite, parquet) and carries over.

## Consequences

- Strict typing costs some annotation effort, mainly at JSON and pandas boundaries.
- Fakes over mocks in tests, so pyright checks them against the Protocols.
- A hosted version may later move the backbone to Java/Spring; the ports-and-adapters layout keeps that a re-implementation of adapters and services, not a redesign.
