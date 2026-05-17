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

WORKFLOW STATE Verification line: `pytest, ruff check, ruff format --check`

**Phase 3 Tier A commands:**
- `pytest` — run tests
- `ruff check` — linting
- `ruff format --check` — formatting
- Coverage target: 70-80%

**Phase 3 Tier B additional MCP verifications:**
- PostgreSQL MCP → Query DB state before/after
- Legacy DB MCP → Query legacy databases for data verification

### Implementation Rules (Phase 3)

- **Model structure** — Pydantic CRUD variants per entity (Base/Create/Update/Read), domain-driven `schemas.py`, AppBaseModel with ConfigDict, composition over deep inheritance
- **Minimize complexity** — generators for large data, dict lookups over list scans
- **Preserve compatibility** — Aliases for renamed fields, defaults for new fields, preserve public signatures, re-export moved symbols

### Staff Review Configuration (Phase 4)

- **Patterns file path:** Path to this skill's `patterns.md`

---

## Python-Specific Rules

- Type hints are mandatory — use Pydantic and strict typing per patterns.md
- Tests are required during implementation, not after — RED→GREEN→REFACTOR for every behavior
- No positive claim without running `pytest`
- Pydantic model fields with non-trivial types, defaults, or validators MUST have WHY comments explaining the rationale (e.g., data source format, business rule, cross-system constraint)

---

## Quality Checklist (Python-Specific)

Add these to the shared workflow's verification checklist:

- [ ] Type hints use built-in types (not `typing.List`, `typing.Dict`)
- [ ] Pydantic for all structured data
- [ ] No global state or hidden dependencies
- [ ] DataFrames copied before mutation
- [ ] Python 3.13+ features where appropriate
- [ ] `ruff check` passes
- [ ] `ruff format` applied
- [ ] `pytest` passes (or alternative verification documented)
- [ ] No `iterrows()` — vectorized ops, `to_dict("records")`, or `groupby` instead
- [ ] Independent DB queries run concurrently (`asyncio.gather` / `ThreadPoolExecutor`)
- [ ] No fetch-then-filter — use JOIN or IN (subquery) instead of 2 round trips
