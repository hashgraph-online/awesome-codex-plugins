#!/usr/bin/env python3
"""The inventory of every ``MULTI_LLM_*`` environment name the repository uses.

One table answers "who sets this, who reads it, is it public, does the Codex
tool server forward it". It is an **inventory, not an accessor layer**: readers
keep calling ``os.environ`` and keep their own constants (``detach.WORKER_ENV``,
``provider_registry.ENV_CONFIG_VAR``, ...). The names below exist so a test, a
doc generator and a person can read them in one place.

Rules, enforced by ``tests/test_codex_package.py`` and ``tests/test_env_vars.py``:

* a ``MULTI_LLM_*`` name read anywhere in the shipped tree, or spelled in any
  tracked file, needs a row here (``tests/test_env_vars.py`` lists the few
  spellings that are not variables);
* a row of a :data:`READ_KINDS` kind whose owner ships is still read there, and
  a :data:`NOT_READ_KINDS` row is read nowhere;
* ``forwarded_to_codex`` is exactly the ``MULTI_LLM_*`` part of the ``env_vars``
  list in the Codex ``.mcp.json`` (the order of that list is pinned by the test,
  not here);
* the "Environment variables" table in ``docs/configuration.md`` is generated
  from the rows of kind ``setting``. ``--check`` fails when it is stale.

Usage::

    python utils/env_vars.py            # rewrite the table between the markers
    python utils/env_vars.py --check    # exit 1 if docs/configuration.md is stale
    python utils/env_vars.py --stdout   # print the table, write nothing

Stdlib plus the L0 ``stream_bootstrap``; layer L0 (``tests/test_import_layers.py``).
"""

from __future__ import annotations

if __name__ == "__main__" and not __package__:
    # Run by path: put the skill root on sys.path, found from this file's real
    # location as Python finds sys.path[0], then call the package module's entry
    # point with sys.argv untouched, so the program name stays the one typed
    # (docs/development/dispatcher.md#import-safety).
    import os
    import sys

    _UTILS_DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path[:] = [os.path.dirname(_UTILS_DIR)] + [
        p for p in sys.path if os.path.realpath(p) != _UTILS_DIR]
    from utils.env_vars import main

    sys.exit(main())

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from .stream_bootstrap import bootstrap_streams

# --- kinds -----------------------------------------------------------------

#: A switch a person may set. Only these rows reach ``docs/configuration.md``.
SETTING = "setting"
#: Launcher-to-worker handshake: the parent sets it for one launch, the worker
#: consumes it. Never a user input; an inherited stale one is a bug.
HANDSHAKE = "handshake"
#: Set by a host shim or a tool server for the dispatcher it starts, per call.
HOST_INPUT = "host_input"
#: Set by the plugin for a child it spawns (a probe script, a runner profile).
PLUMBING = "plumbing"
#: A stdout/stderr token, not an environment variable at all.
MARKER = "marker"
#: Read only by the packaging scripts, never by the skill at run time.
BUILD = "build"
#: A test seam. ``MULTI_LLM_TEST_FAST_BACKOFF`` is read by shipped code.
TEST = "test"
#: Named in a comment or planned, but read nowhere yet.
RESERVED = "reserved"
#: Still read, only to say it no longer does anything.
RETIRED = "retired"

KINDS: Tuple[str, ...] = (
    SETTING, HANDSHAKE, HOST_INPUT, PLUMBING, MARKER, BUILD, TEST, RESERVED, RETIRED,
)

#: Kinds that are not environment reads. The package test asserts the
#: AST walk never finds a read of one, so a real read fails loudly instead of
#: being swept into the allowlist; change the row's kind in the same commit.
NOT_READ_KINDS: Tuple[str, ...] = (MARKER, RESERVED)

#: Kinds whose rows the owning module reads from its own environment. The
#: package test asserts that each such row whose owner ships is still read by
#: shipped code, so a removed read takes its row (or a kind change) with it.
#: ``plumbing`` is absent: the plugin sets those for a child's own script.
READ_KINDS: Tuple[str, ...] = (SETTING, HOST_INPUT, HANDSHAKE, BUILD, TEST, RETIRED)


@dataclass(frozen=True)
class EnvVar:
    name: str
    kind: str
    #: The module that defines or reads it, repo-relative to the skill directory
    #: (``packaging/...`` and ``Makefile`` for the build and test lanes).
    owner: str
    forwarded_to_codex: bool
    summary: str


# --- named constants -------------------------------------------------------

PROVIDERS_CONFIG = "MULTI_LLM_PROVIDERS_CONFIG"
PROVIDERS_CONFIG_PERMISSIVE = "MULTI_LLM_PROVIDERS_CONFIG_PERMISSIVE"
GIT_CREDENTIAL_HELPER = "MULTI_LLM_GIT_CREDENTIAL_HELPER"
HOST = "MULTI_LLM_HOST"
UV = "MULTI_LLM_UV"
UV_RUN_ARGS = "MULTI_LLM_UV_RUN_ARGS"
MAX_DETACHED = "MULTI_LLM_MAX_DETACHED"
HEARTBEAT_INTERVAL_S = "MULTI_LLM_HEARTBEAT_INTERVAL_S"
HANDSHAKE_TIMEOUT_S = "MULTI_LLM_HANDSHAKE_TIMEOUT_S"
VALIDATION_CONTEXT = "MULTI_LLM_VALIDATION_CONTEXT"
CODEX_UNSANDBOXED_WRITES = "MULTI_LLM_CODEX_UNSANDBOXED_WRITES"
CODEX_SKIP_RUNG = "MULTI_LLM_CODEX_SKIP_RUNG"
SKILL_DIR = "MULTI_LLM_SKILL_DIR"
ROUTE = "MULTI_LLM_ROUTE"
HOST_SESSION_MODEL = "MULTI_LLM_HOST_SESSION_MODEL"
HOST_SANDBOX_POSTURE = "MULTI_LLM_HOST_SANDBOX_POSTURE"
DETACHED_WORKER = "MULTI_LLM_DETACHED_WORKER"
WORKER_LOG = "MULTI_LLM_WORKER_LOG"
PHASE_LOCK_FD = "MULTI_LLM_PHASE_LOCK_FD"
REPLAY_FLAGS = "MULTI_LLM_REPLAY_FLAGS"
PLAN_ARG = "MULTI_LLM_PLAN_ARG"
FX_PATH = "MULTI_LLM_FX_PATH"
CANARY_SEEDED = "MULTI_LLM_CANARY_SEEDED"
CANARY_PYTHON = "MULTI_LLM_CANARY_PYTHON"
CANARY_WRITE_FILE = "MULTI_LLM_CANARY_WRITE_FILE"
CANARY_WRITE_DIR = "MULTI_LLM_CANARY_WRITE_DIR"
CANARY_WORKDIR = "MULTI_LLM_CANARY_WORKDIR"
RESULT = "MULTI_LLM_RESULT"
CORE_END = "MULTI_LLM_CORE_END"
NESTED_EXEC_OK = "MULTI_LLM_NESTED_EXEC_OK"
ALLOW_DIRTY = "MULTI_LLM_ALLOW_DIRTY"
TEST_FAST_BACKOFF = "MULTI_LLM_TEST_FAST_BACKOFF"
TEST_MODE = "MULTI_LLM_TEST_MODE"
LIVE_MODE = "MULTI_LLM_LIVE_MODE"
UPDATE_GOLDEN = "MULTI_LLM_UPDATE_GOLDEN"
REQUIRE_LANDLOCK = "MULTI_LLM_REQUIRE_LANDLOCK"
CONTRACT_AUDIT = "MULTI_LLM_CONTRACT_AUDIT"
E2E_ENV = "MULTI_LLM_E2E_ENV"
PROBE = "MULTI_LLM_PROBE"
PROBE_OVERRIDE = "MULTI_LLM_PROBE_OVERRIDE"
LEGACY_INSTRUCTIONS = "MULTI_LLM_LEGACY_INSTRUCTIONS"
DEBUG = "MULTI_LLM_DEBUG"
STRICT_ADVISORY = "MULTI_LLM_STRICT_ADVISORY"


def _v(name: str, kind: str, owner: str, forwarded: bool, summary: str) -> EnvVar:
    return EnvVar(name, kind, owner, forwarded, summary)


#: Every row. Settings first (they become the docs table, in this order).
ENV_VARS: Tuple[EnvVar, ...] = (
    # --- settings ----------------------------------------------------------
    _v(PROVIDERS_CONFIG, SETTING, "utils/provider_registry.py", True,
       "Path to a `providers.yaml` deep-merged over the project and user "
       "config, above both. A malformed file fails fast (see the next row)."),
    _v(PROVIDERS_CONFIG_PERMISSIVE, SETTING, "utils/provider_registry.py", True,
       "`1` (also `true`, `yes`, `on`) turns a malformed explicit override "
       "file into a warning and skips it instead of failing fast."),
    _v(GIT_CREDENTIAL_HELPER, SETTING, "utils/provider_registry.py", True,
       "One-run override of the git credential-helper policy for runner "
       "children: `auto` (default), `wipe` or `keep`. Wins over both config "
       "layers; anything else warns and uses `auto`."),
    _v(HOST, SETTING, "utils/host_capabilities.py", True,
       "Host id used when `--host` is not passed (for a host that calls "
       "`multi_llm.py` without a rendered shim). Default `claude-code`; an "
       "unknown id exits 3."),
    _v(UV, SETTING, "utils/unattended.py", True,
       "Explicit path to `uv`, tried before `PATH` and the documented probe "
       "chain. Also used to re-run a detached worker."),
    _v(UV_RUN_ARGS, SETTING, "utils/unattended.py", True,
       "Replaces the flags passed to `uv run` (split on whitespace, no shell). "
       "Unset or empty keeps the default; `--no-sync` is correct only against "
       "an already-built `.venv`."),
    _v(MAX_DETACHED, SETTING, "utils/run_registry.py", True,
       "Ceiling on concurrent detached runs per project (default 4, minimum 1). "
       "The `--max-detached` flag beats it."),
    _v(HEARTBEAT_INTERVAL_S, SETTING, "utils/detach.py", True,
       "Seconds between a detached worker's heartbeats (default 10, minimum "
       "0.05). Mostly for tests and slow disks."),
    _v(HANDSHAKE_TIMEOUT_S, SETTING, "utils/detach.py", True,
       "Seconds `--detach` waits for the worker to confirm it started (default "
       "10, minimum 0.1) before reporting the launch as failed."),
    _v(VALIDATION_CONTEXT, SETTING, "utils/validation_sections.py", True,
       "How much plan and code each validation batch embeds: unset (whole plan "
       "plus the code its issues cite), `cited` (plan scoped per batch) or "
       "`full` (round-wide blocks in every batch). Anything else reads as "
       "`full`."),
    _v(CODEX_UNSANDBOXED_WRITES, SETTING, "modes.py", True,
       "Codex plugin only: `1` lifts the tool's own refusal of write-capable "
       "modes under a read-only or unreadable session posture. It never "
       "changes which sandbox the runners use. Set it in the environment that "
       "starts Codex."),
    _v(CODEX_SKIP_RUNG, SETTING, "utils/providers/sandbox_rungs.py", False,
       "`plugin-landlock` skips that sandbox rung alone for the process; any "
       "other value is rejected at start-up. Use it to tell a jail denial from "
       "a codex fault."),
    _v(DEBUG, SETTING, "utils/advisory.py", False,
       "`1` (also `true`, `yes`, `on`) writes each exception an advisory read "
       "swallowed (a status block, a hint line, a recorded route) to stderr, "
       "with the site's label and the traceback. Stdout and exit codes do not "
       "change. The Codex tool server does not forward it: run the command in "
       "a shell instead."),
    # --- set by a host shim or tool server, per call ----------------------
    _v(SKILL_DIR, HOST_INPUT, "packaging/codex/mcp_server.py", True,
       "The Codex tool server exports the skill directory to the dispatcher it "
       "starts, so a printed command can name it."),
    _v(ROUTE, HOST_INPUT, "modes.py", False,
       "Set by a package route's tool server on every child (`package`); picks "
       "the spelling of a printed next-phase command, never which phases run."),
    _v(HOST_SESSION_MODEL, HOST_INPUT, "utils/provider_registry.py", False,
       "The model the host session runs on, as `provider/model`, exported per "
       "call by a host shim or plugin. A fact about the session, consulted "
       "below any operator config."),
    _v(HOST_SANDBOX_POSTURE, HOST_INPUT, "utils/providers/sandbox_rungs.py", False,
       "The chat's own sandbox posture, set by the Codex tool server per call "
       "and never inherited. Only `danger-full-access` can let a write job run "
       "uncontained, and only after the plugin's jail could not take it."),
    # --- launcher-to-worker handshake -------------------------------------
    _v(DETACHED_WORKER, HANDSHAKE, "utils/detach.py", False,
       "Marks the process as the detached worker of a launch. A stale "
       "inherited value is a bug, so it is never forwarded."),
    _v(WORKER_LOG, HANDSHAKE, "utils/detach.py", False,
       "The launcher's own log path for one worker, consumed by the dispatcher "
       "before pre-flight."),
    _v(PHASE_LOCK_FD, HANDSHAKE, "utils/detach.py", False,
       "The inherited descriptor of the phase lock the launcher hands its "
       "worker (POSIX); the worker checks it names the phase's lock file "
       "before adopting it. A descriptor number means nothing elsewhere, so "
       "it is never forwarded."),
    _v(REPLAY_FLAGS, HANDSHAKE, "utils/detach.py", True,
       "The launcher's replayable flags (JSON) for one detached run, written to "
       "the run record once; absent or malformed reads as none."),
    _v(PLAN_ARG, HANDSHAKE, "utils/detach.py", False,
       "The typed plan argument of a launch, recorded by `detach.child_env` for "
       "the worker alone."),
    # --- plumbing the plugin sets for its own children --------------------
    _v(FX_PATH, PLUMBING, "utils/providers/fx.py", False,
       "The skill's resolved `PATH`, handed to the fx runner's private profile "
       "so `export PATH=$MULTI_LLM_FX_PATH` can find its tools."),
    _v(CANARY_SEEDED, PLUMBING, "utils/providers/codex.py", False,
       "Landlock rung probe: path of the seeded file the canary must not "
       "truncate."),
    _v(CANARY_PYTHON, PLUMBING, "utils/providers/codex.py", False,
       "Landlock rung probe: the interpreter the canary script runs."),
    _v(CANARY_WRITE_FILE, PLUMBING, "utils/providers/codex.py", False,
       "Landlock rung probe: a file the canary must be able to write."),
    _v(CANARY_WRITE_DIR, PLUMBING, "utils/providers/codex.py", False,
       "Landlock rung probe: a directory the canary must be able to write in."),
    _v(CANARY_WORKDIR, PLUMBING, "utils/providers/codex.py", False,
       "Landlock rung probe: the canary's negative-target directory when it "
       "is not the cwd-relative default."),
    # --- tokens that are not environment variables ------------------------
    _v(RESULT, MARKER, "utils/cli_common.py", False,
       "Prefix of the single machine-readable result line on stdout "
       "(`MULTI_LLM_RESULT: {json}`)."),
    _v(CORE_END, MARKER, "multi_llm.py", False,
       "Stdout marker that ends the instruction core a mode prints."),
    _v(NESTED_EXEC_OK, MARKER, "utils/runner_preflight.py", False,
       "The word the nested-exec probe asks a runner to print, searched for in "
       "its reply to decide whether it can start a nested exec."),
    # --- build, test, retired, reserved -----------------------------------
    _v(ALLOW_DIRTY, BUILD, "packaging/codex/build.py", False,
       "Build only: exactly `1` is the default of each `build.py`'s "
       "`--allow-dirty`; the Makefile exports it when `ALLOW_DIRTY` is set. "
       "`codex-package`, `claude-package` and the opencode clean build blank "
       "it on their recipe line. The skill never reads it."),
    _v(TEST_FAST_BACKOFF, TEST, "utils/review_orchestrator_base.py", False,
       "Test seam read by shipped code: `1` shortens every retry backoff to "
       "10 ms. Not a setting; moving it behind a seam is open work."),
    _v(TEST_MODE, TEST, "tests/conftest.py", False,
       "Tests: `1` marks a run that uses mock provider binaries from `PATH`."),
    _v(LIVE_MODE, TEST, "tests/conftest.py", False,
       "Tests: `1` lets `live` tests run (they spend real provider quota)."),
    _v(UPDATE_GOLDEN, TEST, "tests/test_subagent_prompts.py", False,
       "Tests: `1` rewrites the golden prompt fixtures."),
    _v(REQUIRE_LANDLOCK, TEST, "tests/test_landlock_exec.py", False,
       "Tests: `1` turns a skipped Landlock test into a failure."),
    _v(CONTRACT_AUDIT, TEST, "tests/contract_audit.py", False,
       "Tests: JSONL path the contract audit appends to."),
    _v(E2E_ENV, TEST, "Makefile", False,
       "Make: path of the credential file `make e2e-live-provider` sources "
       "(default `~/.config/multi-llm/e2e.env`)."),
    _v(PROBE, TEST, "tests/container/entrypoint.py", False,
       "Container probe: a marker planted only in the environment Codex is "
       "launched with; the observer reports by name whether it reached the "
       "dispatcher's login shell and its child."),
    _v(PROBE_OVERRIDE, TEST, "tests/container/entrypoint.py", False,
       "Container probe: the second launch-only marker, reported the same way."),
    _v(STRICT_ADVISORY, TEST, "utils/advisory.py", False,
       "Test seam read by shipped code: `1` re-raises what an advisory read "
       "would swallow, only inside a pytest process; anywhere else, a "
       "detached worker a test spawns included, it is ignored. "
       "`tests/conftest.py` sets it for the files that cover the converted "
       "modules."),
    _v(LEGACY_INSTRUCTIONS, RETIRED, "multi_llm.py", False,
       "No longer switches anything: the frozen core it once served is gone. "
       "A set value is answered on stderr and the current core is served."),
)

_BY_NAME: Dict[str, EnvVar] = {row.name: row for row in ENV_VARS}


def by_name() -> Dict[str, EnvVar]:
    return dict(_BY_NAME)


def forwarded_names() -> Tuple[str, ...]:
    """The ``MULTI_LLM_*`` names the Codex tool server forwards, in table order."""
    return tuple(row.name for row in ENV_VARS if row.forwarded_to_codex)


def settings() -> Tuple[EnvVar, ...]:
    return tuple(row for row in ENV_VARS if row.kind == SETTING)


def counts_by_kind() -> Dict[str, int]:
    return {kind: sum(1 for row in ENV_VARS if row.kind == kind) for kind in KINDS}


def table_problems() -> List[str]:
    """Structural faults in the table itself (empty when sound)."""
    problems: List[str] = []
    seen = set()
    for row in ENV_VARS:
        if row.name in seen:
            problems.append(f"{row.name} has two rows")
        seen.add(row.name)
        if row.kind not in KINDS:
            problems.append(f"{row.name} has unknown kind {row.kind!r}")
        if not row.name.startswith("MULTI_LLM_"):
            problems.append(f"{row.name} is not a MULTI_LLM_* name")
        if not row.summary.strip() or "|" in row.summary or "\n" in row.summary:
            problems.append(f"{row.name} summary is empty or breaks a table cell")
        if row.forwarded_to_codex and row.kind in NOT_READ_KINDS + (BUILD, TEST):
            problems.append(f"{row.name} is {row.kind} and cannot be forwarded")
    return problems


# --- the docs table --------------------------------------------------------

DOC_BEGIN = "<!-- BEGIN GENERATED: environment-variables (utils/env_vars.py) -->"
DOC_END = "<!-- END GENERATED: environment-variables -->"

_HEADER = (
    "<!-- Generated from the `setting` rows of utils/env_vars.py. Edit the row, "
    "then run `python utils/env_vars.py`. -->"
)


def render_table() -> str:
    lines = [
        _HEADER,
        "",
        "| Variable | What it does | Codex manifest |",
        "|---|---|---|",
    ]
    for row in settings():
        forwarded = "forwarded" if row.forwarded_to_codex else "not forwarded"
        lines.append(f"| `{row.name}` | {row.summary} | {forwarded} |")
    return "\n".join(lines)


def docs_path() -> Path:
    return Path(__file__).resolve().parents[3] / "docs" / "configuration.md"


def _block() -> str:
    return f"{DOC_BEGIN}\n{render_table()}\n{DOC_END}"


def doc_with_table(current: str) -> Optional[str]:
    """``current`` with the block between the markers rewritten, or ``None``
    when either marker is missing (the markers are hand-written, never created)."""
    start = current.find(DOC_BEGIN)
    end = current.find(DOC_END)
    if start < 0 or end < start:
        return None
    return current[:start] + _block() + current[end + len(DOC_END):]


def doc_problem(path: Optional[Path] = None) -> Optional[str]:
    """Why the docs table is stale or unrenderable, or ``None`` when it is current."""
    target = path or docs_path()
    try:
        current = target.read_text(encoding="utf-8")
    except OSError as exc:
        return f"{target} cannot be read: {exc}"
    fresh = doc_with_table(current)
    if fresh is None:
        return f"{target} lacks the markers {DOC_BEGIN!r} and {DOC_END!r}"
    if fresh != current:
        return (f"{target} has a stale environment-variables table; run "
                f"`python utils/env_vars.py` and commit the result")
    return None


def main(argv: Optional[Sequence[str]] = None) -> int:
    bootstrap_streams()
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--check", action="store_true",
                        help="exit 1 when docs/configuration.md is stale")
    parser.add_argument("--stdout", action="store_true",
                        help="print the table and write nothing")
    args = parser.parse_args(argv)
    if args.stdout:
        print(render_table())
        return 0
    problems = table_problems()
    if problems:
        print("env_vars table is unsound:\n  " + "\n  ".join(problems), file=sys.stderr)
        return 1
    if args.check:
        problem = doc_problem()
        if problem:
            print(problem, file=sys.stderr)
            return 1
        return 0
    target = docs_path()
    try:
        current = target.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"{target} cannot be read: {exc}", file=sys.stderr)
        return 1
    fresh = doc_with_table(current)
    if fresh is None:
        print(f"{target} lacks the markers {DOC_BEGIN!r} and {DOC_END!r}", file=sys.stderr)
        return 1
    if fresh != current:
        target.write_text(fresh, encoding="utf-8")
        print(f"wrote {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
