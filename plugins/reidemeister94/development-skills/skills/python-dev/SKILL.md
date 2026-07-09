---
name: python-dev
description: "Python development. Use for Python, FastAPI, Pydantic, asyncpg, pytest, pandas, SQLAlchemy."
user-invocable: true
allowed-tools: Glob, Read, Grep, Bash, Task, Skill, Edit, Write, AskUserQuestion
---

# Python Development

**Announce:** "I'm using the python-dev skill. Following the 4-phase workflow."

## MANDATORY: Read and Follow the Shared Workflow

**You MUST read [workflow.md](../../shared/workflow.md) NOW** and follow ALL 4 phases defined there. The sections below provide Python-specific inputs for each phase.

Read [patterns.md](patterns.md) during Phase 1.

**If you lost workflow.md from context:** Re-read `../../shared/workflow.md` NOW before continuing.

---

## Python-Specific Configuration

### Verification Commands (Phase 1 plan + Phase 3 verify)

WORKFLOW STATE Verification line: `pytest tests/ -x -q, ruff check, ruff format --check`

**Phase 3 Tier A commands:**
- `pytest tests/ -x -q` — default suite (unit + golden); excludes `e2e` and `integration` markers
- `pytest tests/ -x -q -m e2e` — e2e replay tests (no DB)
- `pytest tests/ -x -q -m integration` — integration tests (requires real DB)
- `pytest tests/ -x -q -m ''` — everything
- `ruff check .` — linting
- `ruff format --check .` — formatting
- `pre-commit run --files <touched>` — full hook chain (ruff + ruff-format + check-toml/yaml/merge-conflict + commitizen)

**Phase 3 Tier B additional MCP verifications:**
- PostgreSQL MCP → Query DB state before/after
- Legacy DB MCP → Query legacy databases for data verification

### Implementation Rules (Phase 3)

- **Model structure** — Domain-driven `app/model/<domain>/{models.py, requests.py, responses.py}`; cross-cutting types in `model/common/`. Separate `*Request` from `*Response`; never merge. When a response carries both DB-mapped fields AND computed/Python-only fields, split into a `*DbRow` base (SELECT columns only) + a `*Model` subclass that adds enrichment and `@computed_field` properties. Query builders and aggregation utilities receive the DB-row base. Composition over deep inheritance.
- **Settings** — `BaseSettings` hierarchy, `SecretStr` for sensitive values, `@lru_cache(maxsize=1)` on the `get_settings` accessor. Tests that mutate env call `get_settings.cache_clear()`.
- **Error handling** — One global `Exception` handler in `create_app` + a per-domain-error handler in `app/exception_handlers.py`. Domain errors raised straight from service/repository; never wrapped in `HTTPException`. Handler `detail` strings hardcoded — never `str(exc)`.
- **Async hygiene** — `except asyncio.CancelledError: raise` separately from `except Exception`. Bounded `asyncio.Queue` for background work. `asyncio.gather` for independent queries. Heavy SDK clients constructed once at lifespan; blocking calls wrapped in `asyncio.to_thread` at adapter seams.
- **Minimize complexity** — generators for large data, dict lookups over list scans, function length ~50-60 lines (soft guide; extract a helper past that).

### Staff Review Configuration (Phase 4)

- **Patterns file path:** Path to this skill's `patterns.md`

---

## Python-Specific Rules

- Type hints are mandatory — use Pydantic and strict typing per `patterns.md`.
- All imports at module top — never inside a function or method.
- Tests are required during implementation, not after — RED → GREEN → REFACTOR for every behavior.
- No positive claim without running `pytest tests/ -x -q`.
- Pydantic model fields with non-trivial types, defaults, or validators MUST have WHY comments explaining the rationale (data source format, business rule, cross-system constraint).
- One global FastAPI `Exception` handler in `create_app`; never per-endpoint `try / except → HTTPException`.
- `TestClient(app, raise_server_exceptions=False)` for any test that exercises the global handler.
- Domain metadata (schema names, plant codes, environment-specific strings) lives on an Enum property — never hardcoded in N places.

---

## Quality Checklist (Python-Specific)

Add these to the shared workflow's verification checklist:

- [ ] Python 3.14 (built-in `list[str]` / `dict[str, int]`, PEP 604 `str | None`; no `from __future__ import annotations`)
- [ ] No `from typing import List, Dict, Optional` — use built-ins
- [ ] Pydantic for all structured data; `BaseSettings` for configuration; `SecretStr` for sensitive values
- [ ] Request/Response Pydantic models separated; `*DbRow` base + `*Model` subclass where DB-mapped and computed fields coexist
- [ ] `json_schema_extra` used ONLY for OpenAPI examples — never for internal flags
- [ ] One global `Exception` handler + per-domain handlers in `app/exception_handlers.py`; routes/services raise domain errors, never `HTTPException`
- [ ] Sanitized 500 detail — never leak `str(exc)` to clients
- [ ] `except asyncio.CancelledError` re-raised; never swallowed in `except BaseException`
- [ ] Middleware order declared in one list and pinned by a test
- [ ] `@lru_cache(maxsize=1)` on `get_settings`; tests call `cache_clear()` after env mutations
- [ ] Heavy SDK clients constructed once at lifespan; blocking calls wrapped in `asyncio.to_thread` at adapter seams
- [ ] Repository returns typed Pydantic models, not raw `asyncpg.Record`
- [ ] Parameterized SQL (`$1`, `$2`) — no f-string interpolation of user input
- [ ] Independent DB queries run concurrently (`asyncio.gather`)
- [ ] No fetch-then-filter — JOIN or `IN (subquery)` in one round trip
- [ ] `asyncio_mode="auto"` in `pyproject.toml`; markers `golden`, `e2e`, `integration`
- [ ] `TestClient(app, raise_server_exceptions=False)` for tests that exercise the global handler
- [ ] `MagicMock(spec=Class)` + `AsyncMock` for async methods; autouse fixture clears `app.dependency_overrides`
- [ ] DataFrames copied before mutation; no `iterrows()`
- [ ] `ruff check .` passes; `ruff format --check .` passes
- [ ] Pre-commit (ruff + ruff-format + check-toml/yaml/merge-conflict + commitizen) passes on touched files
- [ ] `pytest tests/ -x -q` passes (or alternative verification documented)
