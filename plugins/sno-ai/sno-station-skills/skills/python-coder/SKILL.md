---
name: python-coder
description: "Implement and refactor production Python, FastAPI, Pydantic, async, and migrations."
requires:
  programs: []
  harness:
    - {slot: 4.shell, need: required}
    - {slot: 4.file-read-write, need: required}
---

# Python Coder

Every development task has a finite budget including setup, tests, and reporting.
Before running tests, estimate duration from available timings and identify the changed
behavior or directly affected consumer. If timing is unknown, state an estimate; do not
build a timing system or run a preliminary suite. Full evaluation, unit, integration,
or repository suites require the owner's explicit request, never a skill, PRD, review,
or default command. Remove checks that neither prove the requested main function nor
expose its defects. Repeat only after a relevant change or failure.
Every new security check requires the owner's explicit approval for that specific check;
remove auxiliary security, assertion, hash, or bookkeeping blockers of useful work.


Write production Python that fits the current repository, stays small, and is easy to verify. Local repo instructions add project-specific detail; they do not weaken these rules.

## Runtime Source of Truth

Honor the Python version declared by the user or the repository (`pyproject.toml` `requires-python`, `.python-version`, `setup.cfg`, `tox.ini`, CI, package metadata). Never emit syntax, stdlib APIs, or typing features newer than the target. For 3.14+ targets, prefer 3.14 idioms where they improve clarity or correctness: lazy annotations (PEP 649), `InterpreterPoolExecutor` (PEP 734), t-strings (PEP 750), free-threading awareness (PEP 779).

## Boundaries

- **No backward compatibility by default.** No legacy paths, compatibility wrappers, migration shims, dual-format support, or fallback behavior unless explicitly requested. A published external contract is the only exception, and only when the user or repo instructions confirm it is published.
- **Read before writing.** Relevant exports, immediate callers, shared utilities, nearby tests, and the package's typecheck/test setup — before adding code.
- **Official docs for third-party behavior.** Before changing a dependency version, or using a third-party API, SDK, CLI, or service in a way neither the PRD nor existing code already shows, read its current official documentation; for a version change, read the release notes between the two versions. Name the page and version in the report. When a PRD governs the work and lacks or contradicts that fact, add it to the PRD's execution notes.
- **Surgical changes.** Touch only what the task requires. No adjacent refactoring, no speculative abstractions or configurability, no error handling for scenarios that cannot happen.
- **Deterministic code for deterministic decisions.** Routing, retries, status-code handling, schema validation, parsing, and transforms belong in code, never in a model call.
- **Conflicting local patterns:** pick one source of truth (by authority, recency, test coverage), state the choice, flag the other for cleanup. Never blend conventions into a third style.

## Design Rules

Intent: types make illegal states unrepresentable, data structures replace branches, and every line is a liability that must earn its place.

**Types**
- Zero `Any`. Use `object` + narrowing, generics, or `TypedDict`. `cast()` only at validated boundaries, with a comment saying why.
- `Literal[...]` over bare `str`; `TypedDict` over `dict[str, Any]` — split required/optional via a required base class + `total=False` subclass so guaranteed keys stay guaranteed.
- `Protocol` over ABC (structural typing, stub-friendly testing); class hierarchies max 1 level — favor composition.
- `@dataclass(frozen=True, slots=True)` for value objects with behavior; `TypedDict` for data crossing boundaries (JSON, APIs, configs).
- `T | None` over `Optional[T]`; `type X = ...` aliases (3.12+); `typing.Self` for fluent/builder methods; `@overload` when the return type depends on an argument; `ClassVar[T]` for class-level state.
- Abstract types (`Sequence`/`Mapping`/`Iterable` from `collections.abc`) in parameters, concrete types in returns. Explicit return types on public functions.
- `from __future__ import annotations`: omit on 3.14+ targets and remove it from files you edit there; on older targets follow the repo's existing annotation strategy — do not remove it opportunistically.
- `if TYPE_CHECKING:` for heavy or cycle-prone imports.

**Structure & errors**
- Functions under ~50 lines, max 3 indentation levels, early-return guard clauses, happy path at lowest indentation.
- Exception hierarchies for expected errors: a base class plus narrow subclasses, so callers choose their catch specificity. Wrap only the line that can raise; never bare `except:`; no mutable default arguments; no magic strings/numbers (constants or `Literal`).
- Resources (connections, files, locks) always via context managers or `finally`.
- `__all__` declares each module's public API. Pure logic in the core, side effects at the edges.
- Replace manual counting/grouping/nested combinatoric loops with `Counter`, `defaultdict`, `itertools`.
- Docstrings are contracts (preconditions, silenced errors, external failure modes), not narration; skip when nothing is non-obvious.

**Async & parallelism**
- `asyncio.TaskGroup` over `gather()` — structured cancellation, no orphaned tasks.
- CPU-bound work: `InterpreterPoolExecutor` over `ProcessPoolExecutor` (3.14+); keep threads for I/O.
- Shared mutable state is always locked (`threading.Lock` / `asyncio.Lock`) — free-threaded Python (PEP 779) turns previously-hidden races into real bugs.

**Boundaries & config**
- Keep fixed-format parsing and protocol literals in code; use existing translation resources only for text that requires localization.
- Reuse the repository's configuration and boundary-validation approach; do not introduce a configuration framework, translation system, or startup gate for an ordinary change. Internal calls trust types.
- SQL always via parameterized queries, HTML through the framework's escaping, log fields via `extra={}` — never hand-interpolated strings. T-strings (`string.templatelib`, 3.14+) do no escaping by themselves; use them only where the repo already has a vetted template processor for that exact sink.

**Logging**
- Never `print()` in production code. `logging.getLogger(__name__)`; `%s` formatting or `extra={}` — never f-strings in log calls; `logger.exception` for stack traces.

## Verification

Before reporting done, every claim must trace to a command actually run this session:

1. The repo's declared type checker passes with zero errors on changed files; no typing features newer than the declared runtime.
2. Run the repo's declared check/fix command and report zero remaining errors.
3. Search changed files for `Any` — confirm none; confirm annotation strategy matches the target runtime.
4. Re-read the diff once: delete anything removable without losing correctness or clarity, and confirm every changed line traces to the request.

If a check fails, report the failure with its output — never report done with errors outstanding.

For advanced patterns (generic protocols, async generators, thread-safe singletons, custom decorators, sentinel objects), read `references/advanced-patterns.md`.
<!-- reminders:start -->
<!-- reminders:end -->
