#!/usr/bin/env python3
"""``--detach``: the orchestrator self-daemonizes, and the run stays findable.

Several host harnesses cap a single shell command at 2–10 minutes, and the
fan-out review/ask modes routinely run longer than any of those caps. Claude Code
has a native background Bash, so it keeps using it; every other host needs the
orchestrator to put *itself* in the background and hand back a way to watch and
stop the run. That is this module.

**Exactly one backgrounding mechanism per host — never both.** ``--detach`` inside
a host's own background primitive double-backgrounds: the launcher returns in
milliseconds, the host reports "finished", and the real work continues in a
detached grandchild whose log path and abort command were printed into a shell
nobody reads. A shim picks one mechanism; Claude Code's is its own.

The three halves, and where each lives:

* **The invoker** (:func:`launch`) runs entirely in the foreground: pre-flight,
  the concurrency ceiling, the lock pre-check, log rotation, the spawn, and a
  bounded handshake that waits until the worker has published its own identity.
  Every failure here exits non-zero *on the caller's terminal* with no child
  spawned and no log file written, so a failed launch is indistinguishable from a
  failed foreground run.
* **The worker** (:class:`RunHandle`) owns the phase dir for the run's lifetime:
  the lock, ``run`` in ``{phase}/.status.json``, the heartbeat, the signal
  handlers, and — because after the POSIX double-spawn *nothing* is its parent and
  no caller can ever observe its wait status — its own terminal record. Every run
  ends in exactly one of ``done`` / ``failed`` / ``aborted`` with
  ``run.exit_code`` recorded.
* **The reader** (:func:`classify_run`, and ``utils/run_status.py`` on top of it)
  answers "is this run alive?" from files alone, closes out runs whose heartbeat
  expired *and* whose process is provably gone, and never blocks or signals a
  process just to look.

The one gap the design accepts: a death that runs no handler (SIGKILL, OOM,
reboot). It is closed by heartbeat expiry rather than by guessing — ``status``
reports ``running (stale)`` while the liveness probe is inconclusive and
``failed(heartbeat_timeout)`` with ``run.exit_code: null`` once it is not, so "no
exit code was ever observed" is a defined value and never a fabricated ``0``.
"""

from __future__ import annotations

import asyncio
import atexit
import contextlib
import functools
import io
import json
import os
import shutil
import signal as _signal
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional, Sequence, Tuple, Union

from . import (
    output_handler,
    process_control,
    run_registry,
    status_file,
    stream_bootstrap,
)
from . import run_record as _run_record
# The run record's writers and stamp reader live in run_record (L1), which the
# layers below read: re-exported here for reading only. The active handle is
# run_record._ACTIVE; patch it there (docs/development/dispatcher.md#import-layers).
from .run_record import (  # noqa: F401 - re-exported for reading only
    _elapsed_since,
    _parse_stamp,
    record_resolution,
    report_progress,
)
from .advisory import note_swallowed
from .atomic_io import atomic_write_text
from .cli_common import (
    EXIT_ERROR,
    EXIT_NEEDS_HUMAN,
    EXIT_NOTHING_TO_DO,
    EXIT_OK,
    STATE_PARTIAL,
    dispatcher_command,
    modes_table,
    record_artifact,
    record_next,
    record_progress_lines,
    replay_flags,
    skill_dir,
    current_replay_flags,
    retry_command,
    flag_value,
    invocation,
)
from .status_file import (
    RUN_STATE_ABORTED,
    RUN_STATE_DONE,
    RUN_STATE_FAILED,
    RUN_STATE_RUNNING,
    RUN_STATE_STARTING,
    TERMINAL_RUN_STATES,
)
from .output_handler import consolidation_is_current

# ---------------------------------------------------------------------------
# Tunables
# ---------------------------------------------------------------------------

#: The child refreshes ``run.heartbeat_at`` at most this often.
HEARTBEAT_INTERVAL_S = 10.0

#: A heartbeat older than this is expired — six missed beats, not one, so a
#: loaded machine or a slow filesystem cannot make a healthy run look dead.
HEARTBEAT_STALE_AFTER_S = 60.0

#: How long the invoker waits for the worker to publish ``run.state: running``.
HANDSHAKE_TIMEOUT_S = 10.0

#: Rotated logs kept per phase dir.
ROTATED_LOG_KEEP = 5

#: The current run's log. Existing behavior this inherits, not a new artifact:
#: today's ``host_background`` path already redirects here, the instruction corpus
#: already names it, and a poller that may come back after a re-detach reads
#: ``run.log_path`` instead of hardcoding it.
LOG_NAME = "orchestrator-run.log"

LOCK_NAME = ".lock"

#: Set in the child's environment by :func:`launch`. Its presence is what makes a
#: worker willing to take over the terminal (reopen stdio onto the log) and to
#: hard-exit when it discovers its record was closed out from under it — an
#: in-process test or a hand-run ``--internal-worker`` does neither.
WORKER_ENV = "MULTI_LLM_DETACHED_WORKER"

#: One-shot transport for restoring a worker's output before pre-flight, when
#: a Windows uv/.cmd trampoline did not preserve the launcher's log handles.
WORKER_LOG_ENV = "MULTI_LLM_WORKER_LOG"

#: The launcher's replay flags (``cli_common.replay_flags`` over the
#: pre-``build_worker_argv`` argv), shipped to the worker as a JSON list (D2).
#: Computed in :func:`launch` rather than by the worker because the worker's own
#: argv carries the appended ``--yes``/``--exec-subagents`` indistinguishable
#: from typed ones; :func:`begin_worker_run` decodes it, pops it so no provider
#: subprocess inherits it, and :class:`RunHandle` writes it into the run record
#: once. Not a new ``--internal-*`` flag: that would land in the worker's own
#: recorded argv and need a drop-set entry whose only job is undoing the
#: transport. Absent or malformed decodes to ``[]``.
REPLAY_FLAGS_ENV = "MULTI_LLM_REPLAY_FLAGS"

#: The launcher's ``--plan-file`` value exactly as the dispatcher received it
#: (``cli_common.invocation()``'s argv), shipped to the worker for the same
#: reason as :data:`REPLAY_FLAGS_ENV`: the worker's own argv can only carry the
#: absolute path :func:`build_worker_argv` rewrote it to, and the next-phase
#: command a finished run prints names the plan the way the user typed it
#: (plans/next-phase-command.md §2.1, "Where each emitter gets its inputs").
#: :func:`begin_worker_run` pops it (no provider subprocess inherits it) and
#: :class:`RunHandle` writes it once into the run record as ``plan_arg``, beside
#: ``plan_file``. Absent — a launch with no ``--plan-file``, or a worker started
#: by hand — records no ``plan_arg``, and readers fall back to ``plan_file``.
PLAN_ARG_ENV = "MULTI_LLM_PLAN_ARG"

#: The number of the descriptor on which a ``--detach`` launcher hands its
#: worker the phase lock (POSIX). The worker inherits the launcher's open file
#: description, and a ``flock`` belongs to that, so the lock is held across the
#: boundary with no unlocked interval (docs/development/runtime.md, "One writer
#: per phase dir"). Popped by the worker on its first line
#: (:func:`prepare_worker_output`), so no provider child sees it.
LOCK_FD_ENV = "MULTI_LLM_PHASE_LOCK_FD"

#: Env overrides, all read at call time so a test can set them per-case.
HEARTBEAT_INTERVAL_ENV = "MULTI_LLM_HEARTBEAT_INTERVAL_S"
HANDSHAKE_TIMEOUT_ENV = "MULTI_LLM_HANDSHAKE_TIMEOUT_S"

#: An explicit ``uv`` location, tried before the documented probe chain. A
#: detached process inherits no guarantee about the host's ``PATH`` edits, and a
#: host that installs ``uv`` somewhere unusual should not have to patch code.
UV_ENV = "MULTI_LLM_UV"

#: The modes ``--detach`` covers: the fan-out modes plus the executor-backed write
#: modes (``implement``, the three apply phases, ``generate-tasks``, ``full``),
#: which became long-running when the write executor landed — a phase that
#: schedules N batches through real agent CLIs outlives a host's shell cap exactly
#: as a fan-out does. A mode outside this set still gets a loud exit 3 rather than
#: a flag that silently does nothing.
#:
#: Read from the mode table, never re-listed: ``supports_detach`` is a column on
#: the row, so adding the flag to a mode stays a one-line change there.
DETACH_MODES: Tuple[str, ...] = modes_table().DETACH_MODES

#: Flags the launcher consumes itself and must not pass to the worker.
_LAUNCHER_ONLY_FLAGS: Tuple[str, ...] = ("--detach", "--if-not-running")
_LAUNCHER_ONLY_VALUE_FLAGS: Tuple[str, ...] = ("--max-detached",)

#: Flags whose value is a path the worker must see absolute: it starts in the
#: recorded launch cwd, but a run that outlives its launching shell must not
#: depend on that cwd still meaning the same thing.
_PATH_FLAGS: Tuple[str, ...] = (
    "--plan-file", "--question-file", "--out-dir", "--tasks-file",
    # A commit front door's launch stage (plans/review-commits.md §2.1): the
    # worker applies it after its lock, from wherever it runs.
    "--commit-stage",
)

#: Nested-session variables that must not leak into a detached run.
_STRIPPED_ENV: Tuple[str, ...] = (
    "CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT", "CLAUDE_CODE_SSE_PORT",
    "ANTHROPIC_MODEL", "ANTHROPIC_SMALL_FAST_MODEL",
)


def heartbeat_interval() -> float:
    raw = os.environ.get(HEARTBEAT_INTERVAL_ENV)
    if raw:
        try:
            return max(float(raw), 0.05)
        except ValueError:
            pass
    return HEARTBEAT_INTERVAL_S


def handshake_timeout() -> float:
    raw = os.environ.get(HANDSHAKE_TIMEOUT_ENV)
    if raw:
        try:
            return max(float(raw), 0.1)
        except ValueError:
            pass
    return HANDSHAKE_TIMEOUT_S


class DetachError(Exception):
    """A launch-time failure with a fixed exit code (3 = needs a human)."""

    def __init__(self, message: str, exit_code: int = EXIT_NEEDS_HUMAN):
        super().__init__(message)
        self.exit_code = exit_code


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

def log_path(phase_dir: str) -> str:
    return os.path.join(str(phase_dir), LOG_NAME)


def prepare_worker_output() -> None:
    """Restore launched-worker output before the dispatcher prints anything.

    Called only for ``--internal-worker``. Consume the transport so provider
    children cannot reopen this log; run ownership and jobs still begin at the
    detach boundary, after pre-flight.
    """
    log = os.environ.pop(WORKER_LOG_ENV, None)
    if log and os.environ.get(WORKER_ENV) == "1":
        process_control.redirect_output_to_log(log)
    _receive_handed_lock()


#: The descriptor a launcher handed this worker (:data:`LOCK_FD_ENV`), from the
#: worker's first line until its entry adopts it (:func:`_adopt_handed_lock`).
_HANDED_LOCK_FD: Optional[int] = None


def _receive_handed_lock() -> None:
    """Take :data:`LOCK_FD_ENV` out of the environment and make the descriptor
    it names close-on-exec at once, before anything this worker starts could
    inherit it."""
    global _HANDED_LOCK_FD
    raw = os.environ.pop(LOCK_FD_ENV, None)
    if raw is None:
        return
    try:
        fd = int(raw)
        os.set_inheritable(fd, False)
    except (ValueError, OSError):
        return
    _HANDED_LOCK_FD = fd


def _take_handed_lock_fd() -> Optional[int]:
    global _HANDED_LOCK_FD
    if _HANDED_LOCK_FD is None:
        _receive_handed_lock()
    fd, _HANDED_LOCK_FD = _HANDED_LOCK_FD, None
    return fd


def lock_path(phase_dir: str) -> str:
    return os.path.join(str(phase_dir), LOCK_NAME)


def rotated_log_path(phase_dir: str, run_id: str) -> str:
    return os.path.join(str(phase_dir), f"orchestrator-run.{run_id}.log")


def cli_record_path(phase_dir: str, run_id: str) -> str:
    """The file a detached worker records every process it starts in, by
    pid, start time and group (:func:`process_control.record_cli_identities`):
    what a close-out signals once the worker itself is gone. Removed when the
    run ends, or once a kill has confirmed every process stopped; kept while
    a teardown is under way or unconfirmed (:func:`cleanup_incomplete`). Only
    ever opened as the run's own (:func:`process_control.read_cli_record`)."""
    return os.path.join(str(phase_dir), process_control.cli_record_name(run_id))


def _discard_cli_record(phase_dir: str, run_id: Any) -> None:
    try:
        os.unlink(cli_record_path(phase_dir, str(run_id)))
    except OSError:
        pass


def rotate_log(phase_dir: str, previous_run_id: Optional[str]) -> Optional[str]:
    """Move an existing log aside so ``orchestrator-run.log`` names *this* run.

    Rotation is scoped to the detach path: the ``host_background`` path keeps
    today's truncate-on-``>`` behavior and never rotates.
    """
    current = log_path(phase_dir)
    if not os.path.exists(current):
        return None
    label = previous_run_id or time.strftime("%Y%m%d-%H%M%S")
    target = rotated_log_path(phase_dir, label)
    try:
        if os.path.exists(target):
            os.unlink(target)
        os.replace(current, target)
    except OSError:
        return None
    _prune_rotated_logs(phase_dir)
    return target


def _prune_rotated_logs(phase_dir: str, keep: int = ROTATED_LOG_KEEP) -> None:
    try:
        rotated = [
            os.path.join(phase_dir, name)
            for name in os.listdir(phase_dir)
            if name.startswith("orchestrator-run.") and name.endswith(".log")
            and name != LOG_NAME
        ]
    except OSError:
        return
    rotated.sort(key=lambda p: os.path.getmtime(p) if os.path.exists(p) else 0)
    for path in rotated[:-keep] if len(rotated) > keep else []:
        try:
            os.unlink(path)
        except OSError:
            pass


# ---------------------------------------------------------------------------
# The re-exec command (D4e): uv, rebuilt — never remembered, never bare python
# ---------------------------------------------------------------------------

def resolve_uv() -> str:
    """The absolute ``uv`` path, by the same probe the shim preflight uses.

    ``MULTI_LLM_UV`` first (an explicit override, also what the hermetic tests
    point at a stub), then ``PATH``, then :data:`utils.unattended.UV_CANDIDATES`.
    An unresolvable ``uv`` is a foreground pre-flight failure, never a child that
    dies into a log.

    It **delegates** rather than probing: this function used to carry its own
    two-entry list — ``~/.local/bin/uv`` and ``~/.cargo/bin/uv``, no ``.exe``, no
    Homebrew, no ``/usr/local``, no ``/opt/local`` — and named that shortened list
    back to the user in its own error text. So the detached path, which
    ``detach: required`` puts *every* fan-out mode through, could refuse on a
    machine where the foreground preflight had just succeeded, and the two
    ``.exe`` entries that are the whole Windows story were missing from it. The
    error text is rendered from the same tuple for the same reason.
    """
    # Imported here to keep run_sweep, which loads this module, light.
    from .unattended import UV_CANDIDATES, find_uv

    found = find_uv()
    if found is not None:
        return found
    looked = ", ".join(("$" + UV_ENV, "PATH") + UV_CANDIDATES)
    raise DetachError(
        "ERROR: --detach needs `uv` on PATH and it could not be found.\n"
        f"       Looked at: {looked}\n"
        "       Install it (https://docs.astral.sh/uv/) or run the phase in the "
        "foreground."
    )


def build_worker_argv(
    mode: str, argv: Sequence[str], *, run_id: str
) -> List[str]:
    """The worker's flags: post-parse, normalized, with implications explicit.

    Rebuilt rather than echoed, so the child is identical whether the invoker was
    reached through a rendered shim, a ``"$MULTI_LLM_SKILL_DIR"`` spelling or a
    direct call:

    * ``--detach`` is **replaced** by the reserved ``--internal-worker`` (plus the
      run id the invoker minted), so the child cannot detach recursively and the
      handshake has something to match on.
    * ``--yes`` and ``--exec-subagents`` are written out rather than left implied
      (D4c) — a detached run has no one to ask and no one to continue it past a
      dispatch marker, so both implications are part of the recorded argv.
    * path flags are made absolute.
    * launcher-only flags (the ceiling, ``--if-not-running``) are dropped.
    """
    out: List[str] = []
    index = 0
    tokens = list(argv)
    while index < len(tokens):
        token = tokens[index]
        head = token.split("=", 1)[0]
        if head in _LAUNCHER_ONLY_FLAGS:
            index += 1
            continue
        if head in _LAUNCHER_ONLY_VALUE_FLAGS:
            index += 2 if "=" not in token else 1
            continue
        if head in _PATH_FLAGS:
            if "=" in token:
                value = token.split("=", 1)[1]
                out.append(f"{head}={os.path.abspath(value)}")
                index += 1
            elif index + 1 < len(tokens):
                out += [head, os.path.abspath(tokens[index + 1])]
                index += 2
            else:  # a dangling flag; argparse will report it
                out.append(token)
                index += 1
            continue
        out.append(token)
        index += 1

    if not any(
        t.split("=", 1)[0] in ("--yes", "-y", "--non-interactive") for t in out
    ):
        out.append("--yes")
    if not any(t.split("=", 1)[0] == "--exec-subagents" for t in out):
        # The worker is the only actor left: without this it would exit 0 at
        # [VALIDATION_PENDING]/[SALVAGE_NEEDED] with the phase unfinished, and a
        # poller would read run.state: done.
        out.append("--exec-subagents")
    out += ["--internal-worker", "--internal-run-id", run_id]
    return out


def build_child_command(
    mode: str,
    argv: Sequence[str],
    *,
    run_id: str,
    uv: Optional[str] = None,
    base: Optional[Path] = None,
) -> List[str]:
    """``[<abs uv>, run, --project, <SKILL_DIR>, --, python, <SKILL_DIR>/multi_llm.py, <mode>, …]``

    Reproducing the invoker's own wrapping is the point: re-launching as
    ``[sys.executable, __file__, *args]`` would look right and be subtly wrong —
    inside ``uv run``, ``sys.executable`` is the interpreter uv resolved, but the
    child would inherit it *without* uv, so no lockfile resolution, no re-sync of
    a stale environment, and no ``--project`` for a worker that may run for an hour
    from a different cwd.

    The uv flags come from :func:`utils.unattended.uv_run_args`, the same owner
    the foreground launcher and every printed follow-up read. They were absent
    here, which meant a careful launch — preflighted, ``--no-dev``-ed — handed
    off to a worker that synced the whole dev group anyway, or failed offline,
    with the failure moving out of the launcher where the model sees it and into
    a log where it does not.
    """
    base = Path(base) if base is not None else skill_dir()
    uv_bin = uv or resolve_uv()
    env_dir = os.environ.get("MULTI_LLM_SKILL_DIR")
    if env_dir and os.path.abspath(env_dir) != os.path.abspath(str(base)):
        print(
            f"WARNING: MULTI_LLM_SKILL_DIR ({env_dir}) disagrees with the running "
            f"skill dir ({base}); using the running one.",
            file=sys.stderr,
        )
    # Imported here to keep run_sweep, which loads this module, light.
    from .unattended import uv_run_args

    return [
        uv_bin, "run", *uv_run_args(), "--project", str(base), "--", "python",
        str(base / "multi_llm.py"), mode,
        *build_worker_argv(mode, argv, run_id=run_id),
    ]


def child_env(
    *,
    base: Optional[Path] = None,
    replay_flags: Optional[Sequence[str]] = None,
    plan_arg: Optional[str] = None,
) -> Dict[str, str]:
    """The invoker's environment, pinned for a process that outlives its shell."""
    base = Path(base) if base is not None else skill_dir()
    env = dict(os.environ)
    for name in _STRIPPED_ENV:
        env.pop(name, None)
    env["MULTI_LLM_SKILL_DIR"] = str(base)
    env[WORKER_ENV] = "1"
    # Only `launch` names a handed lock, for the one worker it hands it to.
    env.pop(LOCK_FD_ENV, None)
    env[REPLAY_FLAGS_ENV] = json.dumps([str(t) for t in (replay_flags or [])])
    # This launch's own value or none: never one inherited from whatever
    # environment the invoker itself was started in.
    if plan_arg:
        env[PLAN_ARG_ENV] = str(plan_arg)
    else:
        env.pop(PLAN_ARG_ENV, None)
    # Propagate the *binary*, not only the flags: the worker outlives the shell
    # that launched it and may not share its PATH, so re-probing could resolve a
    # different uv — or none — than the preflight approved. ``UV_ENV`` is common
    # to this module and ``unattended`` (both are "MULTI_LLM_UV"), which is what
    # makes this a one-line propagation rather than a new variable. An override
    # already in the environment is left alone: it is what put us here.
    if not env.get(UV_ENV):
        try:
            env[UV_ENV] = resolve_uv()
        except DetachError:
            # Nothing to propagate. The child's own probe will fail with the
            # full message rather than this one being swallowed here.
            pass
    config = env.get("MULTI_LLM_PROVIDERS_CONFIG")
    if config and not os.path.isabs(config):
        env["MULTI_LLM_PROVIDERS_CONFIG"] = os.path.abspath(config)
    return env


def _spec_binary(spec: str, anchor: Optional[str] = None) -> Optional[str]:
    """The CLI ``spec`` would launch, per the adapter that would launch it.

    ``None`` when nothing can say — an unparseable spec, a provider name with no
    built-in adapter, an adapter that refuses to render a command. An adapter that
    cannot say is not evidence of absence.
    """
    try:
        # Imported here to keep run_status, which loads this module, light.
        from .provider_registry import get_provider, parse_model_spec
    except Exception as exc:  # pragma: no cover - import guard
        note_swallowed("detach: provider binary import", exc)
        return None
    try:
        provider_name, model = parse_model_spec(spec, anchor=anchor)
        provider = get_provider(provider_name)
        if provider is None:
            return None
        return provider.build_command("preflight", model)[0] or None
    except Exception as exc:
        note_swallowed("detach: provider binary for a spec", exc)
        return None


def missing_provider_binaries(
    model_specs: Optional[Sequence[str]], *, anchor: Optional[str] = None
) -> Dict[str, str]:
    """``{model_spec: binary}`` for every requested model whose CLI is not on PATH.

    Part of the foreground pre-flight: a provider that is not installed is
    knowable *before* the fork, and discovering it by polling ``status`` and
    reading a log is exactly the experience ``--detach`` is supposed to avoid. The
    binary name comes from the adapter that would launch it, so this cannot drift
    from what the run actually runs.
    """
    missing: Dict[str, str] = {}
    if not model_specs:
        return missing
    for spec in model_specs:
        binary = _spec_binary(spec, anchor)
        if binary and shutil.which(binary) is None:
            missing[spec] = binary
    return missing


def configured_runner_specs(anchor: Optional[str] = None) -> List[str]:
    """The subagent runner specs this run could dispatch through, primary first.

    ``driver.subagent_runner`` then ``driver.subagent_runner_cheap`` (deduped):
    the executor resolves a task's runner from its ``capability_tier``, so both
    are binaries the run may need.
    """
    try:
        # Imported here to keep run_status, which loads this module, light.
        from .provider_registry import get_subagent_runner
    except Exception as exc:  # pragma: no cover - import guard
        note_swallowed("detach: subagent runner import", exc)
        return []
    specs: List[str] = []
    for tier in ("full", "cheap"):
        try:
            spec = get_subagent_runner(tier, anchor=anchor)
        except Exception as exc:
            note_swallowed("detach: configured subagent runner", exc)
            continue  # a config that cannot resolve is D3's refusal, not ours
        if spec and str(spec) not in specs:
            specs.append(str(spec))
    return specs


def missing_runner_binaries(anchor: Optional[str] = None) -> Dict[str, str]:
    """``{runner_spec: binary}`` for every configured runner CLI not on PATH.

    The second half of D4c step 3's ``shutil.which`` pre-flight: ``--detach``
    implies ``--exec-subagents``, so the run dispatches its own subagents and a
    configured-but-uninstalled ``driver.subagent_runner`` is exactly as knowable
    before the fork as an absent model provider — and exactly as invisible after
    it, where it surfaces only as a ``spawn_failed`` batch inside the log.
    """
    missing: Dict[str, str] = {}
    for spec in configured_runner_specs(anchor):
        binary = _spec_binary(spec, anchor)
        if binary and shutil.which(binary) is None:
            missing[spec] = binary
    return missing


def exec_subagents_in_effect(args: Any = None, argv: Sequence[str] = ()) -> bool:
    """Whether this run will drive its own subagents.

    Read from the parsed flag, with the recorded argv as a second source so a
    caller that hands over a bare namespace (a direct ``launch`` call, a test)
    still gets the pre-flight the flag asks for.
    """
    if bool(getattr(args, "exec_subagents", False)):
        return True
    return any(str(token).split("=", 1)[0] == "--exec-subagents" for token in argv)


def launch_key(mode: str, plan_path: str, phase_dir: str) -> str:
    """``(mode, plan_path, phase[, ask slug])`` — what "the same run" means."""
    return "|".join([mode, os.path.abspath(str(plan_path)), os.path.abspath(str(phase_dir))])


# ---------------------------------------------------------------------------
# Reading a run: liveness, staleness, close-out
# ---------------------------------------------------------------------------

#: ``status``-level verdicts. ``stale`` is deliberately not a stored state.
VERDICT_NO_RUN = "no_run"
VERDICT_STARTING = "starting"
VERDICT_RUNNING = "running"
VERDICT_STALE = "stale"
VERDICT_DONE = RUN_STATE_DONE
VERDICT_FAILED = RUN_STATE_FAILED
VERDICT_ABORTED = RUN_STATE_ABORTED

TERMINAL_VERDICTS = (VERDICT_DONE, VERDICT_FAILED, VERDICT_ABORTED)


def heartbeat_age(run: Dict[str, Any], now: Optional[float] = None) -> Optional[float]:
    """Seconds since the last heartbeat, or ``None`` when none was recorded."""
    return _run_record._elapsed_since(run.get("heartbeat_at"), now)


def effective_age(run: Dict[str, Any], now: Optional[float] = None) -> Optional[float]:
    """How old this run is, for the expiry decision: heartbeat, else ``started_at``.

    A record whose ``heartbeat_at`` is missing or unparseable still has to be able
    to reach a terminal state — otherwise a provably dead run is reported ``stale``
    forever and the phase dir never closes out, which is the condition D4b's
    close-out exists to prevent. ``started_at`` is written by the worker's very
    first record on the same clock, so it bounds the run's age whenever the beat
    cannot be read.
    """
    age = heartbeat_age(run, now)
    if age is not None:
        return age
    return _run_record._elapsed_since(run.get("started_at"), now)


def _open_recommendation(phase_dir: str, recommendation: Any) -> Any:
    """*recommendation* (the checkpoint's ``consolidation_recommended``), or
    ``None`` once ``consolidated.json`` was built from the phase's current
    ``grouped.json`` (``output_handler.consolidation_is_current``).

    The checkpoint loses the key when the consolidation pass finishes, but one
    written before that rule (or by a pass that failed to rewrite it) still
    holds it, and a recommendation for work already done is the noise live
    run 8 reported. Checked only when there is a recommendation to drop.
    """
    if not recommendation:
        return recommendation
    try:
        if consolidation_is_current(phase_dir):
            return None
    except Exception as exc:  # noqa: BLE001 - advisory: keep what the checkpoint says
        note_swallowed("detach: consolidation recommendation", exc)
    return recommendation


def classify_run(
    phase_dir: str,
    *,
    close_out: bool = True,
    now: Optional[float] = None,
) -> Dict[str, Any]:
    """The whole run view of one phase dir. Reads files; takes no lock.

    Works *while another run holds the dir* — that is the point of a poll loop —
    and writes at most one thing: the terminal close-out of a run whose heartbeat
    expired **and** whose process is provably gone. ``stale`` is reported only
    while the probe is inconclusive (the pid is alive and its start time matches
    but it has stopped beating — a hung worker, which ``--abort`` resolves), so a
    phase dir never sits at ``running`` forever after a reboot.
    """
    status = status_file.read_status(phase_dir)
    run = status.get("run") if isinstance(status.get("run"), dict) else {}
    # Coerced here, once, the same way `run` is on the line above: a truncated or
    # hand-edited checkpoint whose `progress` is a list or a string is *truthy*,
    # so `status.get("progress") or {}` let it straight through into the view and
    # every reader that spells the same idiom — `_checkpoint_in_flight`,
    # `_verdict_text`, `_model_table_lines`, `_terminal_fingerprints` — called
    # `.get` on it and raised `AttributeError`. A poll that ends in a traceback
    # and exit 1 is what rule 2 reads as "the run is unreadable", which is a much
    # larger claim than "this one key is malformed". Same rule the per-model rows
    # already follow: an entry that is not a mapping is not trusted.
    progress = status.get("progress")
    if not isinstance(progress, dict):
        progress = {}
    view: Dict[str, Any] = {
        "phase_dir": str(phase_dir),
        "phase": status.get("phase"),
        "question": status.get("question"),
        "state": status.get("state"),
        "updated_at": status.get("updated_at"),
        "output_files": status.get("output_files") or {},
        "progress": progress,
        # Optional, and absent on every phase that has nothing to recommend:
        # `{valid_groups, threshold, command}`, written by the review base's
        # `[CONSOLIDATION_RECOMMENDED]` site. A detached run's caller never saw
        # that stdout, so this view is the only route it reaches a host by.
        # Dropped once the consolidation it recommends has run on these groups
        # (live run 8: a checkpoint written before that pass kept saying "run
        # --consolidate" after it).
        "consolidation_recommended": _open_recommendation(
            phase_dir, status.get("consolidation_recommended")
        ),
        # Plan §2.4: optional, top-level, written only by
        # `validation.publish_validation_context` when a context document was
        # over the inline limit. Same route as `consolidation_recommended`: the
        # view is the only way a detached caller learns validation saw an
        # excerpt (and, for `mode: truncated`, only part of a document).
        "validation_context": status.get("validation_context"),
        # §6 T6.1: optional, present only when validation ran —
        # `{valid, invalid, needs_human_decision, validation_failed}`, written
        # by the review base's `record_validation_counts` wherever a report is
        # rebuilt. Same route as `consolidation_recommended`: without this
        # entry a detached run lost the counts between `.status.json` and the
        # poll's result line, and a host's summary left out the groups the
        # user still has to decide.
        "validation_counts": status.get("validation_counts"),
        # plans/ask-answer-recovery-and-false-success.md D7.2: present on every
        # ask run that reached its closing report and on no other phase —
        # `{answered, file, stdout, fallback, accepted, unrecorded, kept,
        # warn_all_fallback}`, written in the same `update_status` as `state`.
        # Same route as `validation_counts`: an ask is polled through `status`,
        # and without this entry a detached ask's all-fallback flag never
        # reached the host.
        "answer_origins": status.get("answer_origins"),
        # F4: optional, and present only on a finished code-review run —
        # `{count}`, written once by that phase's own `[HIGH_PRIORITY_ISSUES]`
        # site. Same reasoning as `consolidation_recommended` just above: a
        # detached run's caller never saw the bracketed marker's stdout.
        "high_priority_groups": status.get("high_priority_groups"),
        # D2 (live test 2026-10-26): optional, written only by a detached
        # composite's report (`record_step_results`) — `{run_id, phase, steps,
        # artifacts}`, its steps' notices, counts and validation context.
        # They ran in its process, so this is the only route their results
        # reach a poll of its run dir by.
        "step_results": status.get("step_results"),
        "run": dict(run),
        "run_state": run.get("state") if isinstance(run, dict) else None,
        # D4's refusal close-out: `{"state": "runner_rejected", "reason_code"}`
        # at the checkpoint's top level, which `_resume_command` ranks from.
        "reason_code": status.get("reason_code"),
        "reaggregate_command": resolved_reaggregate_command(status),
        "lock_held": not process_control.lock_is_free(lock_path(phase_dir)),
    }
    if not status:
        view["verdict"] = VERDICT_NO_RUN
        view["reason"] = "no .status.json in this phase dir"
        return view
    if not run:
        view["verdict"] = VERDICT_NO_RUN
        view["reason"] = "checkpoint present but no detached run recorded"
        return view

    run_state = run.get("state")
    view["run_state"] = run_state
    if run_state in TERMINAL_RUN_STATES:
        view["verdict"] = run_state
        return view

    age = heartbeat_age(run, now)
    view["heartbeat_age_s"] = age
    identity = process_control.probe(run.get("pid"), run.get("process_start_time"))
    view["identity"] = identity

    # The expiry clock falls back to `started_at` when the beat cannot be read,
    # and — when neither timestamp is usable — a provably dead run that is past
    # `starting` is expired on the spot: it published `running`, so it beat at
    # least once, and nothing that is gone will ever beat again.
    age_for_expiry = effective_age(run, now)
    expired = (
        age_for_expiry > HEARTBEAT_STALE_AFTER_S
        if age_for_expiry is not None
        else identity == process_control.DEAD and run_state != RUN_STATE_STARTING
    )

    if expired and identity == process_control.DEAD:
        if close_out:
            close_out_dead_run(phase_dir, reason="heartbeat_timeout",
                               expect_run_id=run.get("run_id"))
            refreshed = status_file.read_run(phase_dir)
            view["run"] = dict(refreshed)
            view["run_state"] = refreshed.get("state")
            view["verdict"] = refreshed.get("state") or VERDICT_FAILED
            view["lock_held"] = not process_control.lock_is_free(lock_path(phase_dir))
        else:
            view["verdict"] = VERDICT_FAILED
        view["reason"] = "heartbeat_timeout"
        return view

    if identity == process_control.DEAD and run_state == RUN_STATE_STARTING:
        # It never came up and its process is gone: nothing will ever beat.
        if close_out:
            close_out_dead_run(phase_dir, reason="worker_never_started",
                               expect_run_id=run.get("run_id"))
            # Read back rather than assert: the compare-and-set is refused when a
            # new run claimed the dir between the read above and the close-out,
            # and rendering that fresh, live run as failed would send a poller to
            # exit 3 on a run that is only just starting.
            refreshed = status_file.read_run(phase_dir)
            view["run"] = dict(refreshed)
            view["run_state"] = refreshed.get("state")
            view["verdict"] = refreshed.get("state") or VERDICT_FAILED
            view["lock_held"] = not process_control.lock_is_free(lock_path(phase_dir))
        else:
            view["verdict"] = VERDICT_FAILED
        view["reason"] = "worker_never_started"
        return view

    if age is not None:
        clock = f"heartbeat {age:.0f}s old"
    elif age_for_expiry is not None:
        clock = f"no readable heartbeat, started {age_for_expiry:.0f}s ago"
    else:  # pragma: no cover - a dead run with neither stamp expired above
        clock = "no readable heartbeat and no recorded start time"

    if expired:
        view["verdict"] = VERDICT_STALE
        view["reason"] = f"{clock}; process probe {identity}"
        return view

    if identity == process_control.DEAD:
        # The heartbeat is fresh but the process is provably gone (killed
        # between beats, or the pid was recycled and its creation time no longer
        # matches). Reporting `running` for a process we can prove is dead would
        # be a lie; closing it out on the spot would race a worker that is merely
        # slow to write. So: `stale` now, terminal once the heartbeat window
        # expires — which is the two bullets of D4b working exactly as written.
        view["verdict"] = VERDICT_STALE
        view["reason"] = (
            f"process is gone (pid/creation-time probe says dead) but {clock}; "
            "it closes out as failed(heartbeat_timeout) after "
            f"{HEARTBEAT_STALE_AFTER_S:.0f}s"
        )
        return view

    view["verdict"] = VERDICT_RUNNING if run_state == RUN_STATE_RUNNING else VERDICT_STARTING
    return view


def _driven_dir_names(mode: Optional[str]) -> Tuple[str, ...]:
    """The on-disk dir word of each phase a composite *mode* drives, in order.

    A composite (``modes.Mode.is_composite``) is the one kind of mode whose
    handle does not own the directories its progress lands in. It claims its run
    dir (``{plan}/full/``) for its lock, log and ``run`` record and then calls
    each phase's ``main()`` in process, where every tracker is built for
    ``{plan}/<phase>/`` and writes there through the foreign-dir branch of
    :func:`report_progress` (F3, 2026-09-20).

    Each phase word goes through ``output_handler.PHASE_DIRECTORIES``, read
    directly: ``get_phase_dir`` would create the directory it names, and a
    close-out must not leave dirs behind. The mode words themselves would miss
    two dirs, ``code-review/`` and ``apply-fixes/``. Empty for a mode that runs
    no other and for a word the table does not know.
    """
    row = modes_table().resolve(str(mode or ""))
    if row is None or not row.is_composite:
        return ()
    return tuple(
        output_handler.PHASE_DIRECTORIES.get(phase, phase)
        for phase in row.sequence_phases
    )


def _driven_phase_dirs(phase_dir: str, mode: Optional[str]) -> List[str]:
    """The checkpointed dirs beside *phase_dir* that composite *mode* drove.

    Only the composite's own ``sequence`` is looked at. A plan's output dir also
    holds the dirs of runs this one never drove (``ask/``, another composite's
    run dir), and an aborted composite has nothing to say about those. The
    caller's own dir is skipped (its compare-and-set path retires it), and so is
    one without a ``.status.json``, which cannot hold a map.
    """
    directory = os.path.abspath(str(phase_dir))
    parent = os.path.dirname(directory)
    found: List[str] = []
    for name in _driven_dir_names(mode):
        candidate = os.path.join(parent, name)
        if candidate == directory:
            continue
        if os.path.exists(status_file.status_path(candidate)):
            found.append(candidate)
    return found


def _retire_driven_phase_maps(
    phase_dir: str, mode: Optional[str], *, reason: Optional[str] = None
) -> int:
    """Retire the maps left live in the phase dirs a composite run drove.

    "Whoever records the ending retires the map" (F1, 2026-09-20) reads the
    ending's own dir, which is right for every mode but a composite. ``full``
    records its ending in ``{plan}/full/`` — a directory that holds no
    ``progress.models`` at all — while the phase that was actually fanning out
    when the run was aborted or died wrote its map into ``{plan}/<phase>/``.
    Those rows carry no ``run`` record of their own, so nothing else will ever
    retire them: the table went on reading ``codex:gpt-5.6-sol  running
    30m00s/30m``, the dir went on reporting ``running in foreground (…)``, and
    ``_checkpoint_in_flight`` stayed ``True`` on every later poll — on the
    longest-running mode the tool has.

    Only the dirs of the composite's ``sequence`` are swept
    (:func:`_driven_phase_dirs`). Until ``Mode.sequence`` existed, ``full``
    swept every sibling holding a ``.status.json``, so an aborted ``full`` also
    marked a foreground ``ask`` running beside it ``cancelled``.

    A driven dir carrying a **live ``run`` record of its own** is skipped. That
    is an independently detached phase run, not one this handle drove, and
    retiring it would mark a live run's slots ``cancelled`` — exactly what the
    compare-and-set in the callers prevents for their own dir.

    Called **after** the caller has released its own ``checkpoint_lock``, never
    inside it, and that is deliberate. :func:`progress_tracker.retire_live_entries`
    takes the *sibling's* lock, and holding two phase dirs' interprocess mutexes
    at once would introduce a lock order nothing else in this file has — two
    processes taking them in opposite orders would each wait out
    ``FileMutex``'s bounded timeout and then write unserialized, which is worse
    than not nesting. Nothing is given up by waiting: the caller's lock guards
    the caller's checkpoint and says nothing about a sibling's, so this
    retirement is no more atomic with the ``run`` write inside that section than
    outside it. The successor guard above is what covers the window instead.

    Returns how many dirs were rewritten. Never raises.
    """
    try:
        driven = _driven_phase_dirs(phase_dir, mode)
    except Exception:  # noqa: BLE001 - a close-out never raises
        return 0
    if not driven:
        return 0
    # Imported here to keep run_sweep, which loads this module, light.
    from . import progress_tracker

    swept = 0
    for sibling in driven:
        try:
            other = status_file.read_run(sibling)
            if other.get("run_id") and other.get("state") not in TERMINAL_RUN_STATES:
                continue
            if reason is None:
                changed = progress_tracker.retire_live_entries(sibling)
            else:
                changed = progress_tracker.retire_live_entries(sibling, reason=reason)
        except Exception:  # noqa: BLE001 - a close-out never raises
            continue
        if changed:
            swept += 1
    return swept


#: The kill verdicts that leave a run's processes not all confirmed stopped:
#: something outlived its SIGKILL (``survived``), or could not be identified as
#: the run's and was not signalled (``unresolved``, ``skipped``).
INCOMPLETE_KILL_VERDICTS = ("survived", "unresolved", "skipped")

#: ``run.cleanup.state`` while a run's processes are not all confirmed stopped.
CLEANUP_INCOMPLETE = "incomplete"

#: ``run.cleanup.state`` an abort writes before its kill, until the kill's
#: verdict replaces it: a teardown under way is not yet a confirmed one, and a
#: worker finishing inside it must leave the run's trackers alone
#: (:meth:`RunHandle.finish`). An aborter that dies first leaves it standing,
#: which reads as unconfirmed, as it is.
CLEANUP_PENDING = "pending"

#: ``run.cleanup.state`` once a later kill confirmed every process stopped.
CLEANUP_COMPLETE = "complete"


def cleanup_incomplete(record: Dict[str, Any]) -> bool:
    """Does *record* (a ``.status.json`` run record, or a registry entry)
    carry a cleanup not confirmed: :data:`CLEANUP_INCOMPLETE`, or
    :data:`CLEANUP_PENDING`?"""
    cleanup = record.get("cleanup") if isinstance(record, dict) else None
    return isinstance(cleanup, dict) and cleanup.get("state") in (
        CLEANUP_INCOMPLETE, CLEANUP_PENDING)


def _left_running(verdict: Optional[str]) -> bool:
    """A kill that returned *verdict* (``None``: it raised) may have left
    something of the run running."""
    return verdict is None or verdict in INCOMPLETE_KILL_VERDICTS


def _cleanup_entry(verdict: Optional[str], run: Dict[str, Any], *,
                   state: Optional[str] = None) -> Dict[str, Any]:
    """``run.cleanup`` after a kill that returned *verdict*."""
    return {
        "state": state or (CLEANUP_INCOMPLETE if _left_running(verdict) else CLEANUP_COMPLETE),
        "verdict": verdict,
        "pid": run.get("pid"),
        "pgid": run.get("pgid"),
        "checked_at": status_file.now_iso(),
    }


def _claimed_run(phase_dir: str, expect_run_id: Optional[str]) -> Optional[Dict[str, Any]]:
    """*phase_dir*'s run record, read under its checkpoint lock (the one
    ``claim_run`` takes), when it is run *expect_run_id*'s (any run's when
    ``None``); ``None`` otherwise. Its pid, start time, group and run id are
    what the caller's kill targets: never a record read again later, which a
    new run may have claimed since."""
    with status_file.checkpoint_lock(phase_dir):
        run = status_file.read_run(phase_dir)
    run_id = run.get("run_id")
    if not run_id:
        return None
    if expect_run_id is not None and str(run_id) != str(expect_run_id):
        return None
    return dict(run)


def kill_recorded_tree(
    phase_dir: str, run: Dict[str, Any], *, start_time: Optional[str],
    escalate_after_s: Optional[float] = None,
    record: Optional[process_control.CliRecord] = None,
    obligations: Optional[process_control.KillObligations] = None,
) -> Optional[str]:
    """``kill_run_tree`` on *run*'s recorded pid and group (a run record or a
    registry entry), with the processes its worker recorded starting
    (:func:`cli_record_path`; *record* when the caller already read it) as its
    members; the verdict, or ``None`` when the kill itself failed.
    *obligations* gets what the verdict leaves unconfirmed (``kill_tree``)."""
    pid = run.get("pid")
    pgid = run.get("pgid")
    kwargs: Dict[str, Any] = {
        "start_time": start_time, "pgid": int(pgid) if pgid else None,
    }
    if escalate_after_s is not None:
        kwargs["escalate_after_s"] = escalate_after_s
    if obligations is not None:
        kwargs["obligations"] = obligations
    try:
        if record is None and phase_dir:
            record = _read_record(phase_dir, run)
        if record is not None:
            if record.members:
                kwargs["members"] = record.members
            if not record.complete:
                kwargs["members_complete"] = False
        return process_control.kill_run_tree(run.get("run_id"), int(pid) if pid else 0,
                                             **kwargs)
    except Exception:  # noqa: BLE001 - a teardown never raises
        return None


def _read_record(phase_dir: str, run: Dict[str, Any]) -> process_control.CliRecord:
    """Run *run*'s record of the processes its worker started; lines of
    another run found in it are ignored, and said on stderr."""
    record = process_control.read_cli_record(phase_dir, str(run.get("run_id")))
    _report_foreign(phase_dir, run, record)
    return record


def _report_foreign(phase_dir: str, run: Dict[str, Any],
                    record: Optional[process_control.CliRecord]) -> None:
    if record is not None and record.foreign:
        print(
            f"WARNING: {cli_record_path(phase_dir, str(run.get('run_id')))}: "
            f"{record.foreign} line(s) recorded for another run were ignored; "
            "nothing they name was signalled.",
            file=sys.stderr,
        )


#: Kill verdicts, worst first (:func:`_worst_verdict`).
_VERDICTS_WORST_FIRST = ("survived", "unresolved", "skipped", "killed", "gone")


def _worst_verdict(verdicts: Sequence[Optional[str]]) -> str:
    """The worst of *verdicts*: an unconfirmed one over ``killed`` over
    ``gone``; a word that is none of the kill's counts as ``unresolved``."""
    ranks = [_VERDICTS_WORST_FIRST.index(verdict) if verdict in _VERDICTS_WORST_FIRST
             else _VERDICTS_WORST_FIRST.index("unresolved") for verdict in verdicts]
    return _VERDICTS_WORST_FIRST[min(ranks)] if ranks else "gone"


def _owed_by(verdict: Optional[str],
             owed: process_control.KillObligations) -> Optional[List[Optional[str]]]:
    """What a kill that returned *verdict* still owes once a later kill has
    run, re-checked now (:meth:`process_control.KillObligations.outstanding`).
    Only what the kill named can be cleared, and only by that re-check: a
    verdict worse than everything it named (``None``, a kill that raised,
    included) is owed as it stands."""
    if verdict in ("killed", "gone"):
        return []
    named: List[str] = list(owed.identities.values())
    if owed.groups or owed.record_incomplete:
        named.append("unresolved")
    if (verdict is None or not named
            or _worst_verdict([verdict, *named]) != _worst_verdict(named)):
        return [verdict]
    return list(owed.outstanding())


def _kill_after_the_gate(
    phase_dir: str, run: Dict[str, Any], first: process_control.CliRecord,
    verdict: Optional[str], owed: process_control.KillObligations, *,
    start_time: Optional[str], escalate_after_s: Optional[float] = None,
) -> Optional[str]:
    """A teardown's kill, finished once its worker is stopped: the run's
    record read again. When it names a process the first read (*first*, taken
    under the closed launch gate) did not, or that read could not vouch for
    every launch, the kill is made again with every identity recorded now, so
    a launch whose intent got in before the gate and whose identity came after
    is stopped too. The verdict is then the worst of that kill's, and of what
    the first kill (*verdict*, which left *owed*) still owes once re-checked
    on its own (:func:`_owed_by`): a group the first kill found running
    something unidentified stays ``unresolved`` until it runs nothing, though
    the second kill no longer sees it (the process that showed it has exited);
    ``killed`` before ``gone`` stays ``killed``. A record that still has an
    intent with no identity, or whose gate never closed, leaves the verdict
    ``unresolved`` at best: the worker may have started a process nothing
    names."""
    again = process_control.read_cli_record(phase_dir, str(run.get("run_id")))
    if again.foreign != first.foreign:
        _report_foreign(phase_dir, run, again)
    if not again.closed:
        again = again._replace(complete=False)
    seen = {(member.pid, member.start_time) for member in first.members}
    late = [member for member in again.members
            if (member.pid, member.start_time) not in seen]
    if not late and first.complete:
        if not again.complete and not _left_running(verdict):
            return "unresolved"
        return verdict
    final = kill_recorded_tree(phase_dir, run, start_time=start_time, record=again,
                               escalate_after_s=escalate_after_s,
                               obligations=process_control.KillObligations())
    earlier = _owed_by(verdict, owed)
    if final is None or None in earlier:
        return None
    return _worst_verdict([final, *earlier, *(["killed"] if verdict == "killed" else [])])


def stop_recorded_run(
    phase_dir: Optional[str], run: Dict[str, Any], *, start_time: Optional[str],
    escalate_after_s: Optional[float] = None,
) -> Optional[str]:
    """Every teardown's kill of what run *run* left (a run record or a
    registry entry), whether or not its worker still runs: an abort, the
    retry of a cleanup not confirmed, a close-out, ``util runs --sweep``.

    The steps, in order: the run's launch gate closed
    (:func:`process_control.close_launch_gate`), so its worker, if it still
    runs, starts nothing more; the kill of the worker and of every identity
    the record names under that gate (:func:`kill_recorded_tree`); the record
    read again and every identity added since killed
    (:func:`_kill_after_the_gate`), the first kill's unconfirmed outcome kept
    until re-checked. The verdict, or ``None`` when a kill
    raised: only a reread after the gate closed can confirm every process
    stopped. Without a phase dir there is no record, and off the identity
    kill no gate (``None``): the kill alone, as it always was. Never raises."""
    try:
        gate = (process_control.close_launch_gate(phase_dir, str(run.get("run_id")))
                if phase_dir else None)
        _report_foreign(str(phase_dir or ""), run, gate)
        owed = process_control.KillObligations() if gate is not None else None
        verdict = kill_recorded_tree(str(phase_dir or ""), run, start_time=start_time,
                                     escalate_after_s=escalate_after_s, record=gate,
                                     obligations=owed)
        if gate is None or owed is None:
            return verdict
        return _kill_after_the_gate(str(phase_dir), run, gate, verdict, owed,
                                    start_time=start_time,
                                    escalate_after_s=escalate_after_s)
    except Exception:  # noqa: BLE001 - a teardown never raises
        return None


def _write_cleanup(phase_dir: str, run_id: str, cleanup: Dict[str, Any]) -> bool:
    """*cleanup* into run *run_id*'s record, if the phase dir is still its: a
    closed record takes only a restatement of its own state beside it."""
    with status_file.checkpoint_lock(phase_dir):
        current = status_file.read_run(phase_dir)
        if str(current.get("run_id")) != str(run_id):
            return False
        updates: Dict[str, Any] = {"cleanup": cleanup}
        if current.get("state") in TERMINAL_RUN_STATES:
            updates["state"] = current.get("state")
        return status_file.update_run(phase_dir, updates, expect_run_id=str(run_id),
                                      quiet=True)


def _settle_cleanup(phase_dir: Optional[str], run: Dict[str, Any],
                    cleanup: Optional[Dict[str, Any]], *,
                    project_root: Optional[str] = None) -> None:
    """What tracks a run's processes, after a kill whose outcome is
    *cleanup* (``None``: confirmed). Confirmed: its registry entry and its
    CLI record go. Not: both are kept, and the entry carries *cleanup* itself,
    so a later ``util runs --sweep`` or ``status --abort`` tries again from the
    run's own identities even once its phase dir belongs to another run."""
    run_id = str(run.get("run_id"))
    try:
        root = project_root or run_registry.resolve_project_root(
            str(run.get("plan_file") or phase_dir))
    except Exception:  # noqa: BLE001 - the record of what is left must not raise
        root = None
    if cleanup is not None and cleanup_incomplete({"cleanup": cleanup}):
        if root is not None:
            run_registry.mark_cleanup(root, run_id, cleanup, run, phase_dir=phase_dir)
        return
    if phase_dir:
        _discard_cli_record(phase_dir, run_id)
    if root is not None:
        try:
            run_registry.remove_entry(root, run_id)
        except Exception:  # noqa: BLE001
            pass


def retry_cleanup(phase_dir: str, *, expect_run_id: Optional[str] = None,
                  ) -> Optional[Dict[str, Any]]:
    """Try again to stop what a closed run left that was not confirmed stopped.

    For a terminal run (run *expect_run_id*, when given) whose ``run.cleanup``
    is not confirmed: the same kill its close-out ran, from that very record,
    and the record rewritten with what this one found. Returns the new
    ``run.cleanup``; ``None`` when there was nothing to retry. Never raises.
    """
    try:
        run = _claimed_run(phase_dir, expect_run_id)
        if (run is None or run.get("state") not in TERMINAL_RUN_STATES
                or not cleanup_incomplete(run)):
            return None
        # Its worker may still run (an earlier kill could not stop it): the
        # whole sequence again, gate first (`stop_recorded_run`).
        verdict = stop_recorded_run(phase_dir, run,
                                    start_time=run.get("process_start_time"),
                                    escalate_after_s=1.0)
        entry = _cleanup_entry(verdict, run)
        _write_cleanup(phase_dir, str(run["run_id"]), entry)
        _settle_cleanup(phase_dir, run, entry if cleanup_incomplete({"cleanup": entry})
                        else None)
        return entry
    except Exception:  # noqa: BLE001 - a teardown never raises
        return None


#: :func:`close_out_entry`'s *killed* when the caller made no kill of its own.
_NO_KILL_YET = object()


def close_out_entry(entry: Dict[str, Any], *, reason: str = "heartbeat_timeout",
                    project_root: Optional[str] = None, kill: bool = True,
                    killed: Any = _NO_KILL_YET) -> Optional[Dict[str, Any]]:
    """``util runs --sweep``'s close-out of one registry entry: its worker is
    gone, its cleanup is still not confirmed, or it is old enough to prune.

    When the phase dir still holds the entry's own run, open, that run is
    closed out (:func:`close_out_dead_run`, held to the entry's run id).
    Otherwise (closed already, or the dir is another run's now) what the run
    left is stopped from the entry's own identities and the CLI record named
    by its run id, never from the dir's current record: *killed* is the
    verdict of that kill when the caller already made it (the prune's), and
    with *kill* false none is made. A run still open takes *killed* as its
    close-out's kill too, rather than a second kill whose verdict would stand
    for what only the first one saw. Returns the outcome (``run.cleanup``'s
    shape); ``None`` when there was no kill. Never raises.
    """
    run_id = entry.get("run_id")
    phase_dir = entry.get("phase_dir")
    if not run_id:
        return None
    try:
        run = _claimed_run(str(phase_dir), str(run_id)) if phase_dir else None
        if run is not None and run.get("state") not in TERMINAL_RUN_STATES:
            return _close_out(str(phase_dir), reason=reason, expect_run_id=str(run_id),
                              project_root=project_root, run=run, killed=killed)[1]
        identity = {key: entry.get(key) for key in (
            "run_id", "pid", "process_start_time", "pgid", "plan_file", "mode")}
        if killed is not _NO_KILL_YET:
            verdict = killed
        elif kill:
            verdict = stop_recorded_run(str(phase_dir or ""), identity,
                                        start_time=identity.get("process_start_time"),
                                        escalate_after_s=1.0)
        else:
            return None
        outcome = _cleanup_entry(verdict, identity)
        unconfirmed = cleanup_incomplete({"cleanup": outcome})
        if run is not None and (unconfirmed or cleanup_incomplete(run)):
            _write_cleanup(str(phase_dir), str(run_id), outcome)
        _settle_cleanup(phase_dir, identity, outcome if unconfirmed else None,
                        project_root=project_root)
        return outcome
    except Exception:  # noqa: BLE001 - a teardown never raises
        return {"state": CLEANUP_INCOMPLETE, "verdict": None,
                "pid": entry.get("pid"), "pgid": entry.get("pgid"),
                "checked_at": status_file.now_iso()}


def close_out_dead_run(phase_dir: str, *, reason: str = "heartbeat_timeout",
                       expect_run_id: Optional[str] = None) -> bool:
    """Write the terminal record for a run whose process is gone.

    Compare-and-set on ``run_id``, so a worker that was merely paused (SIGSTOP, a
    suspended laptop) and resumes after being closed out fails the check and exits
    rather than writing over the terminal record. *expect_run_id* holds it to
    one run: the record is read under the phase's checkpoint lock, and when it
    is not that run's nothing is signalled and nothing written, since a new run
    may have claimed the dir since the caller looked. Also breaks the lock, and
    kills what the worker left running — the crash case where no handler ran: by
    the recorded process group, or on Linux with pidfds by the processes the
    worker recorded starting (:func:`cli_record_path`), each by its identity,
    their groups only read (docs/development/runtime.md, "A target known only by
    number"). When not everything could be confirmed stopped the record says so
    (``run.cleanup``, :data:`CLEANUP_INCOMPLETE`), and the registry entry, which
    carries the same, and the CLI record are kept for another try
    (:func:`retry_cleanup`, :func:`close_out_entry`); otherwise both are removed.

    A run already closed whose cleanup is still not confirmed is tried again
    here (``status``, an abort), and ``False`` is returned: no terminal record
    was written.
    """
    return _close_out(phase_dir, reason=reason, expect_run_id=expect_run_id)[0]


def _close_out(
    phase_dir: str, *, reason: str, expect_run_id: Optional[str],
    project_root: Optional[str] = None, run: Optional[Dict[str, Any]] = None,
    killed: Any = _NO_KILL_YET,
) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """:func:`close_out_dead_run`: whether it wrote the terminal record, and
    the outcome of its kill (``run.cleanup``'s shape; ``None`` for no kill).
    *run* is the record the caller already read with :func:`_claimed_run`;
    *killed* the verdict of the kill the caller already made of it (the
    prune's, :func:`close_out_entry`), which stands in for this one's."""
    if run is None:
        run = _claimed_run(phase_dir, expect_run_id)
    if run is None:
        return False, None
    run_id = str(run["run_id"])
    if run.get("state") in TERMINAL_RUN_STATES:
        return False, retry_cleanup(phase_dir, expect_run_id=run_id)
    pid = run.get("pid")
    pgid = run.get("pgid")
    outcome: Optional[Dict[str, Any]] = None
    if killed is not _NO_KILL_YET:
        outcome = _cleanup_entry(killed, run)
    elif pid or pgid or os.path.exists(cli_record_path(phase_dir, run_id)):
        # The leader is normally already dead here — that is what "close out"
        # means — so the recorded process group, and the processes the worker
        # recorded starting, are the only handles left on the provider CLIs it
        # spawned. On Windows the run's named job is that handle, while anything
        # still holds it open (`kill_run_tree`).
        verdict = stop_recorded_run(phase_dir, run,
                                    start_time=run.get("process_start_time"),
                                    escalate_after_s=1.0)
        outcome = _cleanup_entry(verdict, run)
    cleanup = outcome if outcome is not None and cleanup_incomplete(
        {"cleanup": outcome}) else None
    with status_file.checkpoint_lock(phase_dir):
        wrote = status_file.update_run(
            phase_dir,
            {
                "state": RUN_STATE_FAILED,
                "exit_code": None,      # no exit status was ever observed
                "error": reason,
                "closed_out_at": status_file.now_iso(),
                **({"cleanup": cleanup} if cleanup else {}),
            },
            expect_run_id=run_id,
            quiet=True,
        )
        if wrote:
            # The worker died without running its own close-out, so nothing swept
            # its per-model map either: without this the table goes on reading
            # `codex:gpt-5.6-sol  running  30m00s/30m` under `run.state: failed`,
            # forever. Same rule as `RunHandle.finish` — whoever records the ending
            # retires the map, and only on a compare-and-set that was accepted
            # (F1, 2026-09-20) — and, as there, both writes sit inside **one**
            # `checkpoint_lock` section. Releasing it between them would leave a
            # window for a successor to claim the dir and seed its own map, and
            # the retirement checks no run id of its own: it would close out the
            # live run's slots as `cancelled`.
            #
            # `reason` is forwarded rather than left at `CANCELLED_ERROR`: this
            # leg is reached for `heartbeat_timeout` and `worker_never_started`
            # as well as an abort, it is already the word recorded on the `run`
            # record two lines up, and a table reading `failed: cancelled` under
            # `run.error: heartbeat_timeout` tells the two halves of one
            # checkpoint two different stories about the same ending.
            # Imported here to keep run_sweep, which loads this module, light.
            from . import progress_tracker

            progress_tracker.retire_live_entries(phase_dir, reason=reason)
    if wrote:
        # A composite (`full`) records its ending here but fills no map here;
        # the maps it drove are one directory over. Outside the lock above on
        # purpose — see `_retire_driven_phase_maps`.
        _retire_driven_phase_maps(phase_dir, run.get("mode"), reason=reason)
        holder = process_control.read_lock_holder(lock_path(phase_dir))
        if holder is None or holder.get("run_id") == run_id:
            process_control.break_lock(lock_path(phase_dir))
    if wrote or cleanup is not None:
        # What is left unconfirmed is kept whether or not this wrote the
        # record: the registry entry carries it past a dir taken by another run.
        _settle_cleanup(phase_dir, run, cleanup, project_root=project_root)
    return wrote, outcome


def abort_run(phase_dir: str, *, force: bool = False) -> Dict[str, Any]:
    """The only way to stop a detached run. Identity probe → group kill → record.

    Returns ``{"result": …}`` where result is ``aborted`` (a live run was stopped),
    ``not_running`` (already terminal, or no record at all — so a cleanup step is
    safe to run unconditionally), ``survived`` (the pid outlived the SIGKILL
    window; a human gets pid, run_id and the log path), ``incomplete`` (not
    every process of the run could be confirmed stopped: the kill's
    ``verdict`` was ``unresolved`` or ``skipped``, now or in the close-out of
    a run already gone; the same human check) or ``needs_force`` (the
    identity probe was inconclusive). ``survived`` and ``incomplete`` leave
    ``run.cleanup`` :data:`CLEANUP_INCOMPLETE` and keep the registry entry, and
    an abort of a run already closed that way tries its cleanup again.

    Before its kill the abort marks the record :data:`CLEANUP_PENDING`, so a
    worker that finishes inside the kill (its SIGTERM handler) leaves its
    registry entry and CLI record to this abort, which retires them only once
    the kill confirms every process stopped. On Linux with pidfds it also
    closes the run's launch gate first, so the worker starts no provider CLI
    after the abort read what it started, and reads that record again once the
    worker is stopped (:func:`stop_recorded_run`, which the retry of a closed
    run's cleanup runs too). ``force`` overrides an
    inconclusive probe; where the kill goes by identity it still kills by the
    recorded start time.
    """
    run = _claimed_run(phase_dir, None)
    if not run:
        return {"result": "not_running", "run": status_file.read_run(phase_dir),
                "phase_dir": str(phase_dir)}
    run_id = str(run.get("run_id"))
    if run.get("state") in TERMINAL_RUN_STATES:
        if not cleanup_incomplete(run):
            return {"result": "not_running", "run": run, "phase_dir": str(phase_dir)}
        entry = retry_cleanup(phase_dir, expect_run_id=run_id) or run["cleanup"]
        if cleanup_incomplete({"cleanup": entry}):
            return {"result": "incomplete", "run": run, "phase_dir": str(phase_dir),
                    "verdict": entry.get("verdict"),
                    "detail": "the run is over, but what it left is still not "
                              "all confirmed stopped"}
        return {"result": "not_running", "run": run, "phase_dir": str(phase_dir),
                "detail": "what the run left is now confirmed stopped"}
    pid = run.get("pid")
    verdict = process_control.probe(pid, run.get("process_start_time"))
    if verdict == process_control.DEAD:
        _wrote, outcome = _close_out(
            phase_dir, reason="aborted_by_request (process already gone)",
            expect_run_id=run_id)
        if outcome is not None and cleanup_incomplete({"cleanup": outcome}):
            return {"result": "incomplete", "run": run, "phase_dir": str(phase_dir),
                    "verdict": outcome.get("verdict"),
                    "detail": "process was already gone; what it left could not "
                              "all be confirmed stopped"}
        return {"result": "not_running", "run": run, "phase_dir": str(phase_dir),
                "detail": "process was already gone; record closed out"}
    if verdict == process_control.UNKNOWN and not force:
        return {"result": "needs_force", "run": run, "phase_dir": str(phase_dir)}

    # The teardown is under way, and unconfirmed, from here until its verdict
    # replaces this: a worker finishing in its SIGTERM handler sees it.
    _write_cleanup(phase_dir, run_id,
                   _cleanup_entry(None, run, state=CLEANUP_PENDING))
    # `--force` overrides a probe that could not read the identity. Where the
    # kill goes by identity it still kills by the recorded start time, the
    # only thing that tells the worker from a process that took its pid (an
    # unreadable one makes the kill `skipped`, nothing sent); the kill by
    # number takes it as the unverified kill it always requested.
    start_time = run.get("process_start_time")
    if force and not process_control.signals_by_identity():
        start_time = None
    # No new provider launch from here on (the launch gate, `stop_recorded_run`):
    # what the record names now, and what a launch already past the gate adds
    # before the worker stops, is what the kill reaches. Windows: through the
    # run's named job when it opens and the live pid is in it, so the
    # escalation ends exactly the run's tree rather than `taskkill /T`'s
    # parent-pid walk (`process_control.kill_run_tree`).
    kill_verdict = stop_recorded_run(phase_dir, run, start_time=start_time)
    outcome = _cleanup_entry(kill_verdict, run)
    cleanup = outcome if cleanup_incomplete({"cleanup": outcome}) else None
    with status_file.checkpoint_lock(phase_dir):
        wrote = status_file.update_run(
            phase_dir,
            {
                "state": RUN_STATE_ABORTED,
                "exit_code": EXIT_NEEDS_HUMAN,
                "error": "aborted_by_request",
                "closed_out_at": status_file.now_iso(),
                "cleanup": outcome,
            },
            expect_run_id=run_id,
            quiet=True,
        )
        if wrote:
            # The worker's own handler retires the map when SIGTERM reaches it, but
            # this leg exists precisely for the workers that never got there: one
            # that outlived the 10 s window and took the SIGKILL, which catches
            # nothing and runs no `finally`. Whoever records the ending retires the
            # map (F1, 2026-09-20); the retirement is idempotent, so the overlap
            # with the handler's own costs a no-op read. Held under the *same*
            # `checkpoint_lock` as the record above, as in `RunHandle.finish`: the
            # retirement compares no run id, so a successor that claimed the dir in
            # a gap here would have its freshly seeded rows marked `cancelled`.
            # Imported here to keep run_sweep, which loads this module, light.
            from . import progress_tracker

            progress_tracker.retire_live_entries(phase_dir)
    if not wrote:
        # The worker closed its own record first (its handler, or an ending
        # that beat the signal), which takes no `aborted` over it: the kill's
        # outcome still replaces the pending mark beside the state it wrote.
        _write_cleanup(phase_dir, run_id, outcome)
    if wrote:
        # Same blind spot as `close_out_dead_run`: a composite run's maps live
        # in the phase dirs it drove, not in the dir it claimed. Outside the lock
        # above on purpose — see `_retire_driven_phase_maps`.
        _retire_driven_phase_maps(phase_dir, run.get("mode"))
    holder = process_control.read_lock_holder(lock_path(phase_dir))
    if holder is None or holder.get("run_id") == run_id:
        process_control.break_lock(lock_path(phase_dir))
    _settle_cleanup(phase_dir, run, cleanup)
    if kill_verdict == "survived":
        return {"result": "survived", "run": run, "phase_dir": str(phase_dir)}
    if cleanup is not None:
        return {"result": "incomplete", "run": run, "phase_dir": str(phase_dir),
                "verdict": kill_verdict}
    return {"result": "aborted", "run": run, "phase_dir": str(phase_dir),
            "recorded": wrote}


# ---------------------------------------------------------------------------
# The durable, rebindable reaggregate command
# ---------------------------------------------------------------------------

def resolved_reaggregate_command(status: Dict[str, Any]) -> Optional[str]:
    """Rebuild the phase's follow-up command from the *running* skill dir.

    ``.status.json`` stores ``reaggregate_mode`` + ``plan_file`` (durable), never a
    resolved skill-dir-absolute command: the Claude plugin cache is keyed by
    commit hash, so the skill dir moves on every plugin update and a persisted
    absolute command silently points at a directory that no longer exists. Skill-dir
    movement is *rebindable*, so the reader resolves it — this function is that
    read-time resolution, and it is why ``status`` can hand back a command that
    works today for a checkpoint written a week ago.
    """
    mode = status.get("reaggregate_mode")
    plan = status.get("plan_file")
    if not mode or not plan:
        return None

    # The document's third element is the fallback; a live invocation of the
    # same mode wins (`cli_common.current_replay_flags`). `status`'s own argv
    # is a different mode and never wins here. Unshaped by design: this reader
    # did not witness the failure, so it names a legal resume command and
    # ranks nothing.
    return retry_command(
        str(mode), str(plan), "--reaggregate",
        flags=current_replay_flags(status.get("replay_flags"), mode=str(mode)),
    )


def decode_replay_flags(raw: Optional[str]) -> List[str]:
    """``REPLAY_FLAGS_ENV``'s value as a list; absent or malformed is ``[]``."""
    if not raw:
        return []
    try:
        decoded = json.loads(raw)
    except (TypeError, ValueError):
        return []
    if not isinstance(decoded, list):
        return []
    return [str(token) for token in decoded]


# ---------------------------------------------------------------------------
# The worker side
# ---------------------------------------------------------------------------

def active_run() -> Optional["RunHandle"]:
    """The run this process owns, if it is a detached worker."""
    return _run_record._ACTIVE


#: Applies a commit front door's ``--detach`` stage in the worker, right after
#: its lock (``RunHandle._apply_commit_stage``): ``commit_front_door.apply_stage``,
#: which publishes the brief through the commit-brief writer, above this
#: module's layer. So the worker's entry hands it in when the worker starts
#: (``commit_front_door.hand_worker_the_stage_applier``, called by the
#: dispatcher and by each orchestrator a front door runs), and this module
#: imports nothing above its layer (docs/development/dispatcher.md#import-layers).
#: A stage that arrives with no applier stops the worker as one that fails to
#: apply does.
_COMMIT_STAGE_APPLIER: Optional[Callable[[str], None]] = None


def register_commit_stage_applier(applier: Optional[Callable[[str], None]]) -> None:
    """Hand in the function that applies a commit front door's stage
    (:data:`_COMMIT_STAGE_APPLIER`)."""
    global _COMMIT_STAGE_APPLIER
    _COMMIT_STAGE_APPLIER = applier


# ---------------------------------------------------------------------------
# One writer per review phase dir, for the whole run (PhaseRun)
# ---------------------------------------------------------------------------

#: How often, and how far apart, a run's entry tries the phase dir's lock:
#: every ``status`` poll probes it by taking and dropping it
#: (``process_control.lock_is_free``), so one refusal may be a poll. The same
#: numbers as a composite's step lock (``improve_workflow.STEP_LOCK_*``).
ENTRY_LOCK_ATTEMPTS = 5
ENTRY_LOCK_RETRY_S = 0.025

#: How long a ``--detach --force`` launch waits, after asking the run that
#: holds the dir to stop, to take the same lock: twice the abort's own
#: escalation (SIGTERM, then SIGKILL after
#: ``process_control.DEFAULT_ESCALATE_AFTER_S``). Taking the lock is the proof
#: the old writer is gone; not taking it in time refuses the launch.
FORCE_STOP_WAIT_S = 2 * process_control.DEFAULT_ESCALATE_AFTER_S

#: How long a run's exit waits for the phase work still running on its
#: threads (:func:`run_phase_work`) before it releases the lock. Past it the
#: lock is held until the process exits, never released early.
PHASE_WORK_JOIN_S = 30.0

#: While an interrupted run waits for its phase work, how often it stops the
#: provider CLIs again: a thread that started its CLI after the first sweep
#: is stopped too, so the wait ends with the work rather than at its bound.
PHASE_WORK_RESWEEP_S = 1.0

#: The phase locks a run took at its entry (:meth:`PhaseRun.take`), by lock
#: key, until it releases them, a ``--detach`` launch hands one to its worker
#: (:func:`launch`), or the detached worker's :class:`RunHandle` takes one over.
_ENTRY_HOLDS: Dict[str, process_control.PhaseLock] = {}

#: The phase work handed to a thread and not ended yet (:func:`run_phase_work`):
#: a run's phase lock outlives every item (:meth:`PhaseRun.__exit__`).
_PHASE_WORK: set = set()
_PHASE_WORK_LOCK = threading.Lock()

#: The record a detached worker refused at the lock leaves for its launcher,
#: ``{phase}/.worker-refused-<run_id>``: the launch reports the refusal rather
#: than a run (:func:`_await_handshake`). Named for the worker's own run id
#: and read only by its launch, which removes it; nothing else reads it.
WORKER_REFUSAL_PREFIX = ".worker-refused-"


def _entry_key(phase_dir: str) -> str:
    return os.path.normcase(os.path.realpath(lock_path(str(phase_dir))))


class PhaseDirBusy(Exception):
    """Another live process holds the phase dir's lock."""

    def __init__(self, holder: Dict[str, Any]):
        super().__init__("phase dir busy")
        self.holder = holder


def _take_entry_lock(
    path: str, payload: Dict[str, Any], *, attempts: int = ENTRY_LOCK_ATTEMPTS,
) -> process_control.PhaseLock:
    """Take *path* for a run: retried past a ``status`` probe, and through a
    holder that is gone by the rule :meth:`RunHandle._acquire_lock` uses (a
    payload naming a dead process breaks only when the lock proves free).
    Raises :class:`PhaseDirBusy` while a live holder keeps it, and the
    ``OSError`` of a file that cannot be opened or locked at all."""
    holder: Dict[str, Any] = {}
    for attempt in range(attempts):
        if attempt:
            time.sleep(ENTRY_LOCK_RETRY_S)
        lock = process_control.PhaseLock(path)
        try:
            lock.acquire(payload)
            return lock
        except process_control.LockUnavailable as exc:
            holder = dict(exc.holder or {})
            if (process_control.holder_verdict(exc.holder) == process_control.DEAD
                    and process_control.break_lock(path)):
                continue
    raise PhaseDirBusy(holder)


def _take_within(
    path: str, payload: Dict[str, Any], timeout: float,
) -> Optional[process_control.PhaseLock]:
    """A blocking take of *path*, bounded by *timeout*: ``None`` when a live
    holder still has it then."""
    deadline = time.monotonic() + max(timeout, 0.0)
    while True:
        try:
            return _take_entry_lock(path, payload, attempts=1)
        except PhaseDirBusy:
            if time.monotonic() >= deadline:
                return None
            time.sleep(0.05)


def phase_dir_busy_message(
    phase_dir: str, holder: Dict[str, Any], *, plan_file: str, phase: Optional[str],
) -> str:
    """The refusal a run prints when another run holds its phase dir."""
    pid = holder.get("pid") or "unrecorded"
    verdict = process_control.holder_verdict(holder or None)
    run_id = holder.get("run_id")
    lines = [
        f"ERROR: another run of this phase is in progress (pid {pid}, {verdict}): "
        f"{_holder_words(holder)} owns this phase dir ({phase_dir}).",
        "       Two runs must not write one phase dir, so this run stopped before "
        "it read or changed anything there.",
        "       Watch it: " + status_command_for(plan_file, phase=phase, run_id=run_id),
    ]
    if run_id:
        lines.append("       Abort it: " + abort_command_for(plan_file, run_id=run_id))
    lines.append("       Then run this command again; it continues from what that "
                 "run leaves.")
    return "\n".join(lines)


def _holder_words(holder: Dict[str, Any]) -> str:
    run_id = holder.get("run_id")
    if run_id:
        return f"detached run {run_id}"
    return str(holder.get("holder") or "an unrecorded holder")


# -- the detached worker's side of the hand-off --------------------------

def worker_refusal_path(phase_dir: str, run_id: str) -> str:
    return os.path.join(str(phase_dir), f"{WORKER_REFUSAL_PREFIX}{run_id}")


def _record_worker_refusal(phase_dir: str, run_id: Optional[str], message: str) -> None:
    """A detached worker refused at its lock tells its launch why, so the
    launch reports the refusal instead of a run (Windows, where the lock is
    retaken across the boundary and another run can take it in between; and
    on POSIX a hand-off the worker could not adopt). Only a real detached
    worker writes it, and only under its own run id. ``atomic_io``'s write
    (docs/development/runtime.md#atomic-file-writes)."""
    if not run_id or os.environ.get(WORKER_ENV) != "1":
        return
    path = worker_refusal_path(phase_dir, str(run_id))
    try:
        atomic_write_text(path, json.dumps(
            {"run_id": str(run_id), "pid": os.getpid(), "message": message}),
            keep_mode=False)
    except OSError:
        pass


def record_worker_refusal(phase_dir: str, run_id: Optional[str], message: str) -> None:
    """A detached worker that stops at its startup, holding the lock but
    before it claims its run (a damaged checkpoint it could not recover,
    ``review_lane.recover_damaged_checkpoint``), tells its launch why
    (:func:`_record_worker_refusal`). Nothing outside a real worker."""
    _record_worker_refusal(phase_dir, run_id, message)


# -- a damaged checkpoint at a run's start ---------------------------------

def _phase_of(mode: Optional[str], phase: Optional[str]) -> Optional[str]:
    """*phase*, or the phase the mode table gives *mode*; ``None`` when
    neither names one (``status_file.records_withheld_answers`` then takes
    it for a phase that withholds answers)."""
    if phase:
        return str(phase)
    row = modes_table().resolve(str(mode)) if mode else None
    found = getattr(row, "phase", None) if row is not None else None
    return str(found) if found else None


def _damaged_checkpoint(
    phase_dir: str,
) -> Tuple[Optional[status_file.CheckpointDamage], Optional[str]]:
    """*phase_dir*'s checkpoint, judged before a run's first write to it:
    ``(damage, None)`` when it is damaged (``status_file.checkpoint_damage``),
    ``(None, None)`` when it is absent or readable, and ``(None, why)`` when
    it cannot be read and nothing proves its bytes damaged: such a file is
    left as it is."""
    try:
        return status_file.checkpoint_damage(phase_dir), None
    except status_file.CheckpointUnreadable as exc:
        cause = exc.__cause__ or exc
        return None, (
            f"{status_file.status_path(phase_dir)} could not be read ({cause}), on "
            f"each of {status_file.CHECKPOINT_READ_ATTEMPTS} reads: nothing shows "
            f"that its bytes are damaged, so it is left as it is.")


def _replace_damaged(
    phase_dir: str, damage: status_file.CheckpointDamage, *, phase: Optional[str],
) -> Optional[str]:
    """Replace *damage* for the run that owns *phase_dir*
    (``status_file.replace_damaged_checkpoint``), with a warning; ``None``
    when it was replaced, else why not. A phase whose checkpoint records
    withheld answers is never replaced here: only a fresh run of it recovers
    one (``review_lane.recover_damaged_checkpoint``)."""
    status = status_file.status_path(phase_dir)
    found = f"{status} is damaged ({damage.detail}, {damage.size} bytes)"
    if status_file.records_withheld_answers(phase):
        return (f"{found}, and it records which answers this phase withholds: only "
                f"a fresh run of the phase recovers it, before that run records "
                f"itself there.")
    try:
        archived = status_file.replace_damaged_checkpoint(phase_dir, damage, phase=phase)
    except (OSError, status_file.CheckpointUnreadable,
            status_file.CheckpointLockUnavailable) as exc:
        return f"{found}, and it could not be replaced ({exc or type(exc).__name__})."
    print(f"WARNING: {found}: its bytes are kept as {os.path.basename(archived)}, and "
          f"a fresh checkpoint replaced it, nothing read from it (this phase's "
          f"checkpoint holds run and progress records only).", file=sys.stderr)
    return None


@contextlib.contextmanager
def _repair_hold(phase_dir: str, phase: Optional[str]) -> Iterator[bool]:
    """*phase_dir*'s ``.lock`` for a foreground run's checkpoint repair:
    ``True`` while this process holds it (a hold it already had, or one taken
    here the way a run's entry takes it, :func:`_take_entry_lock`, and
    released on the way out), ``False`` when another process holds it or it
    cannot be taken at all; then nothing may be replaced."""
    if holds_phase_lock(phase_dir):
        yield True
        return
    payload = {
        "holder": f"{phase or 'phase'} (foreground checkpoint repair)",
        "mode": phase,
        "pid": os.getpid(),
        "process_start_time": process_control.process_start_time(os.getpid()),
        "acquired_at": status_file.now_iso(),
    }
    lock: Optional[process_control.PhaseLock]
    try:
        lock = _take_entry_lock(lock_path(phase_dir), payload)
    except (PhaseDirBusy, OSError):
        lock = None
    if lock is None:
        yield False
        return
    try:
        yield True
    finally:
        lock.release()


def settle_foreground_checkpoint(
    phase_dir: str, *, mode: Optional[str] = None, phase: Optional[str] = None,
) -> None:
    """A foreground run's start, before its first write to *phase_dir*'s
    checkpoint: a damaged one is replaced (:func:`_replace_damaged`), or a
    warning says why it is not and that the run goes on unrecorded there.

    Never stops: a foreground run's outputs do not depend on its checkpoint,
    whose writes skip a file they cannot read (``status_file.update_status``).
    Does nothing in a phase whose checkpoint records withheld answers (its
    own lane recovers it, ``review_lane.recover_damaged_checkpoint``), or
    over a folder or checkpoint that does not exist; and leaves a damaged
    one to the run that holds the phase lock, when that is another process.
    The replacement runs under that lock, held from a second look at the file
    to the rename (:func:`_repair_hold`): a worker that took the lock between
    a first look and the rename would find the damage, lose it to this run's
    replacement, and refuse without publishing its run. A detached worker
    settles its own in :meth:`RunHandle.start`
    (docs/development/review-results.md, "Recovering a damaged one")."""
    phase_dir = str(phase_dir)
    phase = _phase_of(mode, phase)
    if status_file.records_withheld_answers(phase):
        return
    if not os.path.lexists(status_file.status_path(phase_dir)):
        return
    damage, problem = _damaged_checkpoint(phase_dir)
    if damage is not None:
        with _repair_hold(phase_dir, phase) as held:
            if held:
                damage, problem = _damaged_checkpoint(phase_dir)
                if damage is not None:
                    problem = _replace_damaged(phase_dir, damage, phase=phase)
            else:
                problem = (f"{status_file.status_path(phase_dir)} is damaged "
                           f"({damage.detail}), and another process holds "
                           f"{lock_path(phase_dir)}: the run that owns it replaces it.")
    if problem is not None:
        print(f"WARNING: {problem} This run goes on, but until the file is replaced "
              f"nothing it records there is kept, and `status` shows no run of it. "
              f"{status_file.unreadable_checkpoint_advice(phase_dir, phase=phase)}",
              file=sys.stderr)


def _read_worker_refusal(phase_dir: str, run_id: str) -> Optional[Dict[str, Any]]:
    """The refusal record run *run_id*'s worker left, removed once read."""
    path = worker_refusal_path(phase_dir, run_id)
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        return None
    try:
        os.unlink(path)
    except OSError:
        pass
    return data if isinstance(data, dict) else {}


def _adopt_handed_lock(
    path: str, payload: Dict[str, Any],
) -> Optional[process_control.PhaseLock]:
    """The lock this worker's launch handed it (:data:`LOCK_FD_ENV`), held
    from here and relabelled with *payload*; ``None`` when none was handed
    over (Windows, a worker started by hand). Raises
    ``process_control.LockHandoffFailed`` when the descriptor is not *path*,
    and ``LockUnavailable`` when it does not hold the lock."""
    fd = _take_handed_lock_fd()
    if fd is None:
        return None
    return process_control.PhaseLock.adopt(path, fd, payload)


# -- a --detach launch's gate ---------------------------------------------

def _takes_over(args: Any) -> bool:
    """Whether this launch's ``--force`` takes a live run over. A commit front
    door's restart adds ``--force --rerun-all`` to restart the round; only a
    ``--force`` the user typed takes a live run over (plans/review-commits.md
    §2.1), and the stage records which it was."""
    force = bool(getattr(args, "force", False))
    if force and getattr(args, "commit_stage", None):
        # Imported here to keep run_status, which loads this module, light.
        from .commit_paths import stage_takes_over

        force = stage_takes_over(getattr(args, "commit_stage", None))
    return force


def _launcher_payload(mode: str) -> Dict[str, Any]:
    return {
        "holder": f"{mode} (--detach launcher)", "mode": mode,
        "pid": os.getpid(),
        "process_start_time": process_control.process_start_time(os.getpid()),
        "acquired_at": status_file.now_iso(),
    }


def _live_holder_run(phase_dir: str, holder: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """The detached run the lock's label names, while the checkpoint records it
    unfinished: the run a re-attach follows and a ``--force`` stops. ``None``
    for any other holder (a foreground run, a launcher, a composite's step)."""
    run = status_file.read_run(phase_dir)
    run_id = run.get("run_id")
    if not run_id or holder.get("run_id") != run_id:
        return None
    if run.get("state") in TERMINAL_RUN_STATES:
        return None
    return run


def _print_reattach(
    phase_dir: str, run: Dict[str, Any], *, plan_file: str, phase: Optional[str],
    host: Optional[str],
) -> int:
    """``--if-not-running`` onto run *run*: its log and poll command."""
    existing_id = str(run.get("run_id"))
    print(f"A detached run is already in flight for {phase_dir}.")
    print(f"  run_id:  {existing_id}")
    print(f"  log:     {run.get('log_path')}")
    reattach_cmd = status_command_for(
        plan_file, phase=phase, run_id=existing_id, host=run.get("host") or host,
    )
    print(f"  status:  {reattach_cmd}")
    record_artifact(run.get("log_path") or log_path(phase_dir))
    record_next(reattach_cmd)
    return EXIT_OK


def _busy_launch_message(
    phase_dir: str, holder: Dict[str, Any], run: Optional[Dict[str, Any]], *,
    plan_file: str, force: bool = False,
) -> str:
    if run is not None:
        run_id = str(run.get("run_id"))
        age = heartbeat_age(run)
        return (
            f"ERROR: a detached run already owns {phase_dir}.\n"
            f"       run_id:        {run_id}\n"
            f"       pid:           {run.get('pid')} "
            f"({process_control.holder_verdict(holder or None)})\n"
            f"       last heartbeat: {'never' if age is None else f'{age:.0f}s ago'}\n"
            "       Pass --if-not-running to re-attach to it, abort it "
            f"({abort_command_for(plan_file, run_id=run_id)}), or pass "
            "--force to stop it and take the dir over."
        )
    lines = [
        f"ERROR: {lock_path(phase_dir)} is held by {_holder_words(holder)} "
        f"(pid {holder.get('pid') or 'unrecorded'}, "
        f"{process_control.holder_verdict(holder or None)}).",
        "       Two orchestrators must not interleave .status.json merges and "
        "result files in one phase dir, so nothing was launched.",
    ]
    if force:
        lines.append("       --force stops only a detached run of this phase, and "
                     "this holder is not one; a live writer's lock is never broken.")
    lines.append("       Let it finish (or stop it where it runs), then run this "
                 "command again.")
    return "\n".join(lines)


#: The :func:`abort_run` outcomes that mean every process of the stopped run
#: is gone: the only ones after which ``--detach --force`` takes the dir over.
#: An allowlist, so any other outcome (``needs_force``, ``survived``, a
#: teardown that could not confirm every process stopped, a value added
#: later) refuses: the old run's provider CLIs or their children may still
#: write in the dir, and the lock no longer says so once its worker is dead.
CONFIRMED_STOPS = frozenset({"aborted", "not_running"})


def _unconfirmed_stop_message(
    phase_dir: str, run: Dict[str, Any], stopped: Dict[str, Any], *,
    plan_file: str, phase: Optional[str],
) -> str:
    run_id = str(run.get("run_id"))
    outcome = stopped.get("result")
    verdict = stopped.get("verdict")
    return "\n".join([
        f"ERROR: --force asked run {run_id} (pid {run.get('pid')}) to stop, and its "
        f"teardown ended `{outcome}`"
        + (f" (verdict `{verdict}`)" if verdict else "")
        + ": not every process of that run is confirmed stopped, so its provider "
        f"CLIs or their children may still write in {phase_dir}.",
        "       Nothing was launched, and the run's records are kept for the cleanup.",
        f"       Finish the cleanup: {abort_command_for(plan_file, run_id=run_id)}",
        f"       or sweep this project's runs: {dispatcher_command('util', 'runs', '--sweep')}",
        f"       Check it: {status_command_for(plan_file, phase=phase, run_id=run_id)}",
        "       Then run this command again.",
    ])


#: The ``cleanup.state`` of a stopped run whose processes are all confirmed
#: stopped: with no ``cleanup`` at all, the only record a run's entry goes
#: past (:func:`unconfirmed_cleanup`). An allowlist, like
#: :data:`CONFIRMED_STOPS`.
CONFIRMED_CLEANUP_STATES = frozenset({CLEANUP_COMPLETE})


#: :func:`unconfirmed_cleanup`'s verdicts on one ``cleanup`` value.
CLEANUP_UNCONFIRMED = "unconfirmed"
CLEANUP_MALFORMED = "malformed"


def _cleanup_problem(cleanup: Any) -> Optional[str]:
    """``None`` when *cleanup* is confirmed: absent, or a ``state`` in
    :data:`CONFIRMED_CLEANUP_STATES`. :data:`CLEANUP_UNCONFIRMED` for any other
    string ``state``; :data:`CLEANUP_MALFORMED` for any other shape (not an
    object, or a ``state`` that is missing or not a string)."""
    if cleanup is None:
        return None
    if not isinstance(cleanup, dict) or not isinstance(cleanup.get("state"), str):
        return CLEANUP_MALFORMED
    return None if cleanup["state"] in CONFIRMED_CLEANUP_STATES else CLEANUP_UNCONFIRMED


def _matches_entry(entry: Dict[str, Any], here: str, run_id: Any) -> Tuple[bool, bool]:
    """Is registry *entry* that of run *run_id*, and of the phase dir keyed
    *here*? Read from the entry's ``run_id`` and ``phase_dir`` alone, before
    anything else in it: an entry of another dir and run, malformed or not,
    is not this entry's to read."""
    same_run = bool(run_id) and str(entry.get("run_id")) == str(run_id)
    where = entry.get("phase_dir")
    same_dir = False
    if isinstance(where, str) and where:
        try:
            same_dir = _entry_key(where) == here
        except (OSError, ValueError):
            same_dir = False
    return same_run, same_dir


def _cleanup_records(
    phase_dir: str, *, plan_file: Optional[str],
) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """``(blocking, stale)`` for :func:`unconfirmed_cleanup` and its caller:
    the cleanup record that refuses this entry, and a checkpoint cleanup not
    confirmed that no registry entry backs any more. Each is
    ``{"run_id", "cleanup", "record", "problem"}`` or ``None``."""
    status = status_file.status_path(phase_dir)
    run = status_file.read_run(phase_dir)
    run_id = run.get("run_id")
    try:
        root = run_registry.resolve_project_root(plan_file or str(phase_dir))
        entries: Optional[List[Dict[str, Any]]] = run_registry.list_entries(root)
    except Exception:  # noqa: BLE001 - unread, the checkpoint's record stands alone
        entries = None
    here = _entry_key(phase_dir)
    kept_for_run = False
    for entry in entries or ():
        same_run, same_dir = _matches_entry(entry, here, run_id)
        if not (same_run or same_dir):
            continue
        kept_for_run = kept_for_run or same_run
        problem = _cleanup_problem(entry.get("cleanup"))
        if problem is not None:
            return {"run_id": entry.get("run_id"), "cleanup": entry.get("cleanup"),
                    "record": entry.get("_path"), "problem": problem}, None
    problem = _cleanup_problem(run.get("cleanup"))
    if problem is None:
        return None, None
    found = {"run_id": run_id, "cleanup": run.get("cleanup"), "record": status,
             "problem": problem}
    # The registry decides: the kill paths keep a run's entry until its
    # teardown is confirmed and drop it then, but may leave the checkpoint's
    # value behind (docs/development/runtime.md).
    if entries is not None and not kept_for_run:
        return None, found
    return found, None


def unconfirmed_cleanup(
    phase_dir: str, *, plan_file: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """The teardown an earlier run of *phase_dir* left unconfirmed, or ``None``.

    Read against the schema code health U77 writes (its ``abort_run``,
    close-out and ``run_registry.mark_cleanup``):

    * ``.status.json`` ``run.cleanup``: ``{"state", "verdict", "pid", "pgid",
      "checked_at"}``. ``state`` is ``pending`` while an abort's kill is under
      way (and after an aborter that died in it), ``incomplete`` when a kill
      ``survived``, was ``unresolved`` or ``skipped``, and ``complete`` once
      every process of the run is confirmed stopped;
    * the run's registry entry, ``{project_root}/.multi-llm/runs/<run_id>.json``.
      The kill paths keep it, carrying the same ``cleanup`` beside its
      ``phase_dir`` when the kill could not confirm every process stopped,
      until a sweep or an abort confirms them stopped, and remove it then.

    The registry decides. Only entries of this dir or of the checkpoint's
    run are read. Such an entry's own ``cleanup``, then the checkpoint's
    while that run's entry is still kept, refuse unless absent or
    ``complete`` (:data:`CONFIRMED_CLEANUP_STATES`): any other string
    ``state`` is :data:`CLEANUP_UNCONFIRMED`, and any other shape
    :data:`CLEANUP_MALFORMED`. A checkpoint value no entry backs is stale and
    goes on. Returns ``{"run_id", "cleanup", "record", "problem"}`` for the
    record that refuses. Reads only."""
    return _cleanup_records(str(phase_dir), plan_file=plan_file)[0]


def holds_phase_lock(phase_dir: str) -> bool:
    """Whether this process holds *phase_dir*'s ``.lock`` (:class:`PhaseRun`,
    a composite's step lock, the worker's)."""
    return process_control.held_phase_lock(lock_path(str(phase_dir))) is not None


def registered_runs_of(
    phase_dir: str, *, plan_file: Optional[str], except_run_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """The run registry's entries of *phase_dir* (by each entry's
    ``phase_dir``), *except_run_id*'s left out.

    The registry keeps a detached run's entry from its start until its
    teardown is confirmed (``RunHandle.finish``, a sweep, an abort), and it
    is the one record of that run outside the phase's checkpoint: a reader
    that cannot read the checkpoint learns from it alone whether an earlier
    run of the dir may still have processes writing there. Reads only, and
    strictly (``run_registry.read_entries_strictly``), once: the ``OSError``
    of a registry that exists but cannot be listed propagates, and an entry
    whose phase cannot be told (unreadable, not a JSON object, no
    ``phase_dir`` that resolves) raises ``run_registry.UnreadableEntries``
    naming it. Unread, either may be this dir's run."""
    root = run_registry.resolve_project_root(plan_file or str(phase_dir))
    here = _entry_key(str(phase_dir))
    entries = run_registry.read_entries_strictly(root, except_run_id=except_run_id)
    found: List[Dict[str, Any]] = []
    unclear: List[str] = []
    for entry in entries:
        if except_run_id and str(entry.get("run_id")) == str(except_run_id):
            continue
        where = entry.get("phase_dir")
        try:
            key = _entry_key(where) if isinstance(where, str) and where else None
        except (OSError, ValueError):
            key = None
        if key is None:
            unclear.append(str(entry.get("_path")))
        elif key == here:
            found.append(entry)
    if unclear:
        raise run_registry.UnreadableEntries(unclear)
    return found


def _unconfirmed_cleanup_message(
    phase_dir: str, found: Dict[str, Any], *, plan_file: str, phase: Optional[str],
) -> str:
    run_id = found.get("run_id")
    cleanup = found.get("cleanup")
    details = cleanup if isinstance(cleanup, dict) else {"state": cleanup}
    facts = [f"cleanup `{details.get('state')}`"] + [
        f"{key} {details[key]}" for key in ("verdict", "pid", "pgid", "checked_at")
        if details.get(key) is not None
    ]
    who = f"run {run_id}" if run_id else "an earlier run"
    lines = [
        f"ERROR: the teardown of {who} in {phase_dir} is not confirmed "
        f"({', '.join(facts)}; recorded in {found.get('record')}): its provider CLIs "
        "or their children may still write in that dir.",
        "       This run stopped before it changed anything there, and that run's "
        "records are kept for the cleanup.",
    ]
    sweep = dispatcher_command("util", "runs", "--sweep")
    if run_id:
        lines += [
            f"       Finish the cleanup: {abort_command_for(plan_file, run_id=str(run_id))}",
            f"       or sweep this project's runs: {sweep}",
            f"       Check it: {status_command_for(plan_file, phase=phase, run_id=str(run_id))}",
        ]
    else:
        lines.append(f"       Finish the cleanup: {sweep}")
    lines.append("       Then run this command again.")
    return "\n".join(lines)


def _shown(value: Any, limit: int = 80) -> str:
    text = repr(value)
    return text if len(text) <= limit else text[:limit - 3] + "..."


def _malformed_cleanup_message(
    phase_dir: str, *, record: str, problem: str, plan_file: str, phase: Optional[str],
    run_id: Any = None,
) -> str:
    """The refusal for a cleanup record this entry cannot read: what is in it
    or why the read failed (*problem*), and the file(s) it read (*record*)."""
    who = f"run {run_id}" if run_id else "an earlier run"
    lines = [
        f"ERROR: malformed cleanup record of {who} in {phase_dir} ({problem}; in "
        f"{record}): whether that run's provider CLIs or their children still write "
        "in that dir is unknown.",
        "       This run stopped before it changed anything there, and the record is "
        "kept.",
        f"       Close that run out: {dispatcher_command('util', 'runs', '--sweep')}",
    ]
    if run_id:
        lines.append(
            f"       Check it: {status_command_for(plan_file, phase=phase, run_id=str(run_id))}")
    lines.append("       Then run this command again.")
    return "\n".join(lines)


def _records_read(phase_dir: str, plan_file: Optional[str]) -> str:
    """The checkpoint and the run registry the cleanup read looks in, named
    for a refusal; the registry left out when even its path is unknown."""
    names = [status_file.status_path(phase_dir)]
    try:
        names.append(run_registry.registry_dir(
            run_registry.resolve_project_root(plan_file or str(phase_dir))))
    except Exception:  # noqa: BLE001 - only the refusal's wording
        pass
    return " and ".join(str(name) for name in names)


def refuse_unconfirmed_cleanup(
    phase_dir: str, *, plan_file: str, phase: Optional[str],
    lock: Optional[process_control.PhaseLock] = None,
) -> None:
    """A run's entry, under its phase lock and before its first write: raise
    :class:`DetachError` (exit 3) while an earlier run's teardown is not
    confirmed or its record is malformed (:func:`unconfirmed_cleanup`), and
    when that read fails at all, releasing *lock* first when given. The lock
    frees once the stopped run's worker is gone, but what outlived it may
    still write in the dir. A stale checkpoint value warns and goes on.
    Writes nothing."""
    phase_dir = str(phase_dir)
    stale: Optional[Dict[str, Any]] = None
    try:
        found, stale = _cleanup_records(phase_dir, plan_file=plan_file)
        if found is None:
            message = None
        elif found["problem"] == CLEANUP_MALFORMED:
            message = _malformed_cleanup_message(
                phase_dir, record=str(found.get("record")),
                problem=f"cleanup {_shown(found.get('cleanup'))}, not an object with a "
                        "string `state`",
                plan_file=plan_file, phase=phase, run_id=found.get("run_id"))
        else:
            message = _unconfirmed_cleanup_message(phase_dir, found, plan_file=plan_file,
                                                   phase=phase)
    except Exception as exc:  # noqa: BLE001 - a record that breaks the read refuses
        message = _malformed_cleanup_message(
            phase_dir, record=_records_read(phase_dir, plan_file),
            problem=f"reading it failed: {type(exc).__name__}: {exc}",
            plan_file=plan_file, phase=phase)
    if message is None:
        if stale is not None:
            who = f"run {stale['run_id']}" if stale.get("run_id") else "an earlier run"
            print(
                f"WARNING: the cleanup state {_shown(stale.get('cleanup'))} of {who} "
                f"recorded in {stale.get('record')} is stale: the run registry no "
                "longer keeps that run, so its teardown was confirmed since; going on.",
                file=sys.stderr,
            )
        return
    if lock is not None:
        lock.release()
    raise DetachError(message)


def _stop_holder_and_take(
    phase_dir: str, holder: Dict[str, Any], run: Optional[Dict[str, Any]],
    payload: Dict[str, Any], *, plan_file: str, phase: Optional[str],
) -> process_control.PhaseLock:
    """``--detach --force`` against a live holder: ask it to stop through the
    abort path (:func:`abort_run`, what ``status --abort`` runs), then wait on
    the same lock, at most :data:`FORCE_STOP_WAIT_S`. Getting it is the proof
    the old worker is gone; a live holder's lock is never broken. Only a
    detached run of this dir can be stopped, never this process; anything
    else, an abort that does not confirm every process of the run stopped
    (:data:`CONFIRMED_STOPS`), and a holder that outlives the wait, refuse
    (exit 3)."""
    path = lock_path(phase_dir)
    own = os.getpid()
    if run is None or own in (holder.get("pid"), run.get("pid")):
        raise DetachError(_busy_launch_message(
            phase_dir, holder, None, plan_file=plan_file, force=True))
    run_id = str(run.get("run_id"))
    print(
        f"WARNING: --force: stopping run {run_id} (pid {run.get('pid')}), which owns "
        f"{phase_dir}; this launch takes the dir over once that run has let go "
        "of its lock.",
        file=sys.stderr,
    )
    stopped = abort_run(phase_dir)
    outcome = stopped.get("result")
    if outcome == "needs_force":
        raise DetachError(
            f"ERROR: --force could not stop run {run_id}: its identity probe is "
            f"inconclusive (pid {run.get('pid')}), so nothing was signalled and "
            "nothing was launched.\n"
            f"       Stop it yourself: {abort_command_for(plan_file, run_id=run_id)} "
            "--force\n"
            "       Then run this command again."
        )
    if outcome not in CONFIRMED_STOPS:
        raise DetachError(_unconfirmed_stop_message(
            phase_dir, run, stopped, plan_file=plan_file, phase=phase))
    lock = _take_within(path, payload, FORCE_STOP_WAIT_S)
    if lock is None:
        now = process_control.read_lock_holder(path) or holder
        raise DetachError(
            f"ERROR: --force asked run {run_id} to stop ({stopped.get('result')}), and "
            f"{path} is still held after {FORCE_STOP_WAIT_S:.0f}s by "
            f"{_holder_words(now)} (pid {now.get('pid') or 'unrecorded'}, "
            f"{process_control.holder_verdict(now or None)}).\n"
            "       A live writer's lock is never broken, so nothing was launched.\n"
            f"       Watch it: {status_command_for(plan_file, phase=phase, run_id=run_id)}\n"
            "       Then run this command again."
        )
    print(f"WARNING: --force: run {run_id} has stopped; this launch now holds {path}.",
          file=sys.stderr)
    return lock


def take_for_launch(
    phase_dir: str, *, mode: str, plan_file: str, phase: Optional[str], args: Any,
) -> Union[process_control.PhaseLock, int]:
    """A ``--detach`` launch's hold on its phase dir, taken before it writes
    anything there, and kept until its worker has it (:func:`launch`).

    Free: taken. Held by a live run: ``--if-not-running`` re-attaches to the
    detached run that holds it, deciding from the checkpoint alone (returns
    ``EXIT_OK``); ``--force`` stops that run and takes the lock once it is
    free (:func:`_stop_holder_and_take`); anything else refuses. Either way
    a lock taken is given up again while an earlier run's teardown is not
    confirmed (:func:`refuse_unconfirmed_cleanup`). Raises
    :class:`DetachError` on a refusal and ``OSError`` when the lock file
    cannot be opened or locked at all.
    """
    path = lock_path(phase_dir)
    payload = _launcher_payload(mode)
    try:
        lock = _take_entry_lock(path, payload)
    except PhaseDirBusy as busy:
        holder = busy.holder
    else:
        refuse_unconfirmed_cleanup(phase_dir, plan_file=plan_file, phase=phase, lock=lock)
        return lock
    run = _live_holder_run(phase_dir, holder)
    if getattr(args, "if_not_running", False):
        if run is not None:
            return _print_reattach(phase_dir, run, plan_file=plan_file, phase=phase,
                                   host=getattr(args, "host", None))
        raise DetachError(_busy_launch_message(phase_dir, holder, None,
                                               plan_file=plan_file))
    if _takes_over(args):
        lock = _stop_holder_and_take(phase_dir, holder, run, payload,
                                     plan_file=plan_file, phase=phase)
        refuse_unconfirmed_cleanup(phase_dir, plan_file=plan_file, phase=phase, lock=lock)
        return lock
    raise DetachError(_busy_launch_message(phase_dir, holder, run, plan_file=plan_file))


def _hand_off(hold: process_control.PhaseLock, env: Dict[str, str]) -> Optional[int]:
    """Ready *hold* for the worker about to be spawned: on POSIX the descriptor
    it inherits, named in *env*; on Windows, where a lock does not cross a
    spawn, the hold is released here and the worker takes it again (a run
    that takes it in between is reported by the worker's refusal record)."""
    if process_control.IS_WINDOWS:  # pragma: no cover - Windows
        _handed_over(hold, release=True)
        return None
    fd = hold.handoff_fd()
    env[LOCK_FD_ENV] = str(fd)
    return fd


def _handed_over(hold: process_control.PhaseLock, *, release: bool = False) -> None:
    """This launch's part in the lock ends: on POSIX its descriptor is closed
    without unlocking (:meth:`~process_control.PhaseLock.disown`), whatever
    the spawn and handshake said, so a worker that adopted the lock keeps it
    and the kernel drops it with the last copy otherwise."""
    for key, lock in list(_ENTRY_HOLDS.items()):
        if lock is hold:
            del _ENTRY_HOLDS[key]
    if release:
        hold.release()
    else:
        hold.disown()


# -- the phase work a run's lock outlives ----------------------------------

class _PhaseWork:
    """One call :func:`run_phase_work` handed to a thread: listed in
    :data:`_PHASE_WORK` from its hand-off until it has ended, or until its
    awaiter gave it up before any thread started it."""

    __slots__ = ("done", "started")

    def __init__(self) -> None:
        self.done = threading.Event()
        self.started = False


def _end_phase_work(item: _PhaseWork) -> None:
    with _PHASE_WORK_LOCK:
        _PHASE_WORK.discard(item)
    item.done.set()


async def run_phase_work(func: Any, /, *args: Any, **kwargs: Any) -> Any:
    """``asyncio.to_thread(func, ...)`` for anything a review phase runs on a
    thread: the fan-out's provider calls, with the result files and logs
    they write, rename and adopt, its probes, and a batch dispatch
    (``review_orchestrator_base.phase_thread``). A cancelled awaiter (a
    Ctrl-C) ends the coroutine, never the thread, so the run's exit waits for
    every listed call before it releases its phase lock
    (:meth:`PhaseRun.__exit__`). A call the awaiter gave up before a thread
    started it is never run. Listed until it ends, off the list before its
    awaiter wakes.

    Starting and giving up are one decision each, made under
    :data:`_PHASE_WORK_LOCK`: the thread marks the call started only while it
    is still listed, and the awaiter unlists it only while it is not started,
    each check and its change in one critical section. So either the thread
    finds the call given up and never runs it, or the awaiter finds it started
    and leaves it listed for the exit to wait on."""

    item = _PhaseWork()
    with _PHASE_WORK_LOCK:
        _PHASE_WORK.add(item)

    @functools.wraps(func)
    def work(*call_args: Any, **call_kwargs: Any) -> Any:
        with _PHASE_WORK_LOCK:
            if item not in _PHASE_WORK:
                return None
            item.started = True
        try:
            return func(*call_args, **call_kwargs)
        finally:
            _end_phase_work(item)

    try:
        return await asyncio.to_thread(work, *args, **kwargs)
    finally:
        with _PHASE_WORK_LOCK:
            given_up = not item.started
            if given_up:
                _PHASE_WORK.discard(item)
        if given_up:
            item.done.set()


def _pending_phase_work() -> List[_PhaseWork]:
    with _PHASE_WORK_LOCK:
        return list(_PHASE_WORK)


def stop_phase_work(tag: str) -> bool:
    """Stop the provider CLIs still live and wait, at most
    :data:`PHASE_WORK_JOIN_S`, for the phase work still running on threads
    (:func:`run_phase_work`); whether none is left. What a review fan-out
    whose deadline cancelled slots does before it sets their files aside, so
    no cancelled slot's thread writes after that (docs/development/
    review-results.md, "Withheld slot answers"). Every slot of the fan-out
    has ended by then, so every CLI still live is a cancelled slot's; the
    sweep is repeated every :data:`PHASE_WORK_RESWEEP_S` as on an interrupt."""
    pending = _pending_phase_work()
    if not pending:
        return True
    process_control.sweep_live_clis(tag)
    deadline = time.monotonic() + PHASE_WORK_JOIN_S
    while pending:
        left = deadline - time.monotonic()
        if left <= 0:
            break
        pending[0].done.wait(min(left, PHASE_WORK_RESWEEP_S))
        pending = _pending_phase_work()
        if pending:
            process_control.sweep_live_clis(tag)
    return not pending


def _is_interrupt(exc_type: Any) -> bool:
    if exc_type is None:
        return False
    if issubclass(exc_type, KeyboardInterrupt):
        return True

    return issubclass(exc_type, asyncio.CancelledError)


def _await_phase_work(locks: Sequence[process_control.PhaseLock], *,
                      interrupted: bool) -> None:
    """Before a run releases *locks*: wait for the phase work still listed
    (:func:`run_phase_work`), at most :data:`PHASE_WORK_JOIN_S`; past it, or
    when the wait itself is interrupted, the locks are held until this process
    exits. On an interrupt the live provider CLIs are stopped first, as the
    dispatcher's own sweep would a moment later, and again every
    :data:`PHASE_WORK_RESWEEP_S` while it waits, so the work can return."""
    pending = _pending_phase_work()
    if not pending or not locks:
        return
    try:
        if interrupted:
            process_control.sweep_live_clis("INTERRUPT_SWEEP")
        print("Waiting for this phase's provider calls and dispatch to stop before "
              "releasing its lock...", file=sys.stderr)
        deadline = time.monotonic() + PHASE_WORK_JOIN_S
        while pending:
            left = deadline - time.monotonic()
            if left <= 0:
                break
            pending[0].done.wait(min(left, PHASE_WORK_RESWEEP_S) if interrupted else left)
            pending = _pending_phase_work()
            if pending and interrupted:
                process_control.sweep_live_clis("INTERRUPT_SWEEP")
        pending = _pending_phase_work()
    except BaseException:
        for lock in locks:
            lock.hold_until_exit()
        raise
    if pending:
        for lock in locks:
            lock.hold_until_exit()
        print(f"WARNING: this phase's provider calls or dispatch are still running "
              f"after {PHASE_WORK_JOIN_S:.0f}s, so its lock is held until this process "
              "exits.", file=sys.stderr)


class PhaseRun:
    """A review run's hold on its phase dir's ``.lock``, from its entry to its exit.

    One writer per phase dir for the whole run: every invocation that can stamp
    a round, regroup, validate, reaggregate, auto-heal or complete a review
    phase takes it before it reads anything (:meth:`take`), and the context
    manager releases it when the orchestrator returns or exits, as its very
    last step. A second run is refused at its entry, before it writes anything
    (docs/development/runtime.md, "One writer per phase dir").

    * **Re-entrant within a process.** A lock this process already holds
      (a composite's step lock, a commit front door's, the worker's) is used
      as it is, and its taker releases it.
    * **A ``--detach`` launcher** decides at its entry, before any pre-flight
      write (:func:`take_for_launch`): it takes a free lock, re-attaches
      (``--if-not-running``), stops the detached run that holds it and waits
      for its lock (``--force``), or refuses. It keeps the lock to the
      boundary and hands it to its worker (:func:`launch`).
    * **The detached worker** adopts the lock its launcher handed it (POSIX)
      or takes it, so its pre-flight and guard run under it; its
      :class:`RunHandle` then takes the hold over and releases it after the
      terminal ``run`` record.
    * **Its exit waits for its phase work.** The fan-out's provider calls
      (with the result files and logs they write) and a batch dispatch run on
      threads (:func:`run_phase_work`) that a Ctrl-C does not stop; the lock
      is released only once every one has ended, or held until the process
      exits.
    * **Fail closed.** A live holder refuses a foreground run or a worker at
      exit 3; a lock file that cannot be opened or locked refuses every lane.
      A holder that is gone never blocks: the OS dropped its lock.
    """

    def __init__(self) -> None:
        self._stack = contextlib.ExitStack()
        #: Every lock this run writes under: its own, or one it found held.
        self._locks: List[process_control.PhaseLock] = []

    def __enter__(self) -> "PhaseRun":
        return self

    def __exit__(self, exc_type: Any, *exc_info: Any) -> None:
        try:
            _await_phase_work(self._locks, interrupted=_is_interrupt(exc_type))
        finally:
            self._stack.close()

    def take(
        self, phase_dir: str, *, mode: str, plan_file: str, args: Any,
        phase: Optional[str] = None,
    ) -> None:
        """Hold *phase_dir*'s lock for this run, or stop the run here: a
        refusal prints why and raises ``SystemExit(3)``, a launcher's
        re-attach ``SystemExit(0)``. Every lane, a lock already held
        included, then refuses while an earlier run's teardown is not
        confirmed (:func:`refuse_unconfirmed_cleanup`)."""
        phase_dir = str(phase_dir)
        path = lock_path(phase_dir)
        worker = bool(getattr(args, "internal_worker", False))
        run_id = getattr(args, "internal_run_id", None) if worker else None
        held = process_control.held_phase_lock(path)
        if held is not None:
            self._locks.append(held)
            try:
                # Its taker releases it.
                refuse_unconfirmed_cleanup(phase_dir, plan_file=plan_file, phase=phase)
            except DetachError as exc:
                print(str(exc), file=sys.stderr)
                raise SystemExit(exc.exit_code) from exc
            return
        launcher = bool(getattr(args, "detach", False)) and not worker
        identity = {
            "pid": os.getpid(),
            "process_start_time": process_control.process_start_time(os.getpid()),
            "acquired_at": status_file.now_iso(),
        }
        if worker:
            payload = {"run_id": run_id, "host": getattr(args, "host", None), **identity}
        else:
            payload = {"holder": f"{mode} (foreground)", "mode": mode, **identity}
        try:
            os.makedirs(phase_dir, exist_ok=True)
            if launcher:
                taken = take_for_launch(phase_dir, mode=mode, plan_file=plan_file,
                                        phase=phase, args=args)
                if isinstance(taken, int):
                    raise SystemExit(taken)
                lock = taken
            else:
                lock = ((_adopt_handed_lock(path, payload) if worker else None)
                        or _take_entry_lock(path, payload))
                refuse_unconfirmed_cleanup(phase_dir, plan_file=plan_file, phase=phase,
                                           lock=lock)
        except DetachError as exc:
            print(str(exc), file=sys.stderr)
            if worker:
                _record_worker_refusal(phase_dir, run_id, str(exc))
            raise SystemExit(exc.exit_code) from exc
        except (PhaseDirBusy, process_control.LockUnavailable) as busy:
            message = phase_dir_busy_message(
                phase_dir, dict(busy.holder or {}), plan_file=plan_file, phase=phase)
            print(message)
            if worker:
                _record_worker_refusal(phase_dir, run_id, message)
            raise SystemExit(EXIT_NEEDS_HUMAN) from busy
        except OSError as exc:
            message = (
                f"ERROR: could not lock {path} ({exc}).\n"
                "       A review run writes its phase dir only while it holds this "
                "lock, so it stopped before it read or changed anything there."
            )
            print(message)
            if worker:
                _record_worker_refusal(phase_dir, run_id, message)
            raise SystemExit(EXIT_NEEDS_HUMAN) from exc
        key = _entry_key(phase_dir)
        _ENTRY_HOLDS[key] = lock
        self._locks.append(lock)
        self._stack.callback(_drop_entry_hold, key, lock)


def _drop_entry_hold(key: str, lock: process_control.PhaseLock) -> None:
    """Release an entry hold, unless it went to the worker's :class:`RunHandle`
    (which releases it after the terminal record) or to a detached worker
    (:func:`_handed_over`)."""
    if _ENTRY_HOLDS.get(key) is lock:
        del _ENTRY_HOLDS[key]
        lock.release()


def _tool_route(host: Optional[str]) -> Optional[str]:
    """The tool route (``modes.TOOL_ROUTES``) this process runs on for *host*,
    or ``None``: ``routes.resolve_route`` over this process's
    environment, which the tool servers set and a launch's ``child_env``
    carries to the worker; its stderr note is the dispatcher's to print.
    Advisory: anything unreadable records nothing."""

    try:
        # Imported here to keep run_status, which loads this module, light.
        from . import host_capabilities, routes

        modes = routes._skill_module("modes")
        try:
            host_id = host_capabilities.resolve_host_id(explicit=host)
            route = routes.resolve_route(host_id, stderr=io.StringIO())
        except host_capabilities.UnknownHost:
            return None  # a host the capability data does not list has no tool route
    except Exception as exc:  # noqa: BLE001 - the record stands without it
        note_swallowed("detach: tool route", exc)
        return None
    return route if route in modes.TOOL_ROUTES else None


class RunHandle:
    """The worker's ownership of a phase dir: lock, record, heartbeat, close-out."""

    def __init__(
        self,
        phase_dir: str,
        *,
        run_id: str,
        mode: str,
        plan_file: str,
        host: Optional[str] = None,
        detached: bool = True,
        replay_flags: Optional[Sequence[str]] = None,
        plan_arg: Optional[str] = None,
        commit_stage: Optional[str] = None,
        phase: Optional[str] = None,
    ):
        self.phase_dir = str(phase_dir)
        # The phase the dir belongs to: whether its checkpoint records withheld
        # answers decides what `start` does over a damaged one.
        self.phase: Optional[str] = _phase_of(mode, phase)
        # A commit front door's `--detach` stage (`--commit-stage`), applied
        # once this worker owns the dir (see `start`).
        self.commit_stage: Optional[str] = str(commit_stage) if commit_stage else None
        self.run_id = run_id
        self.mode = mode
        self.plan_file = str(plan_file)
        # The launcher's typed plan (PLAN_ARG_ENV), never this process's argv.
        self.plan_arg: Optional[str] = str(plan_arg) if plan_arg else None
        self.host = host
        self.detached = detached
        # The launcher's list, never recomputed from this process's argv.
        self.replay_flags: Optional[List[str]] = (
            [str(t) for t in replay_flags] if replay_flags is not None else None
        )
        self.log_path = log_path(self.phase_dir)
        self.cwd = os.getcwd()
        self.project_root = run_registry.resolve_project_root(self.plan_file)
        self._lock = process_control.PhaseLock(lock_path(self.phase_dir))
        self._stop = threading.Event()
        self._beat: Optional[threading.Thread] = None
        self._closed = False
        self.interval = heartbeat_interval()
        self.hard_exit_on_lost = os.environ.get(WORKER_ENV) == "1"

    # -- startup --------------------------------------------------------
    def start(self) -> None:
        """Take the dir, publish identity, start beating. Raises on conflict."""
        self._acquire_lock()
        # Under the lock, before this run's first write: a mode with no
        # `PhaseRun` entry stops here too.
        try:
            refuse_unconfirmed_cleanup(self.phase_dir, plan_file=self.plan_file,
                                       phase=None, lock=self._lock)
        except DetachError as exc:
            _record_worker_refusal(self.phase_dir, self.run_id, str(exc))
            raise
        self._apply_commit_stage()
        # Still before this run's first write: `claim_run` over a checkpoint it
        # cannot read writes nothing, and the launch would wait out its
        # handshake while this worker ran the phase. A damaged one is replaced
        # (every phase but those whose checkpoint records withheld answers,
        # which their own fresh run recovers before this point); anything else
        # refuses at once, and the launch reports why
        # (docs/development/review-results.md, "Recovering a damaged one").
        damage, problem = _damaged_checkpoint(self.phase_dir)
        if damage is not None:
            problem = _replace_damaged(self.phase_dir, damage, phase=self.phase)
        if problem is not None:
            message = (
                f"ERROR: {problem} This run recorded nothing and dispatched nothing. "
                f"{status_file.unreadable_checkpoint_advice(self.phase_dir, phase=self.phase)}"
            )
            _record_worker_refusal(self.phase_dir, self.run_id, message)
            self._lock.release()
            raise DetachError(message)
        identity = process_control.identity()
        # Recorded, never re-derived: after the double spawn the group leader is
        # the exited intermediate, so once this worker dies nothing can ask the
        # OS which group its provider children are in — and that group is what
        # the close-out signals to stop providers burning quota on a crashed run.
        # Only a *detached* worker owns its group (`setsid` gave it a session of
        # its own); a foreground run's group belongs to the shell or harness that
        # started it, and recording that would license a group kill of the host.
        pgid = process_control.process_group_id() if self.detached else None
        record = {
            "run_id": self.run_id,
            "pid": identity["pid"],
            "process_start_time": identity["process_start_time"],
            "pgid": pgid,
            "detached": self.detached,
            "host": self.host,
            "mode": self.mode,
            "plan_file": self.plan_file,
            # Not process state: written once here, beside the absolute path,
            # never by update_run. Absent when the launcher shipped none.
            **({"plan_arg": self.plan_arg} if self.plan_arg else {}),
            "cwd": self.cwd,
            "log_path": self.log_path,
            "started_at": status_file.now_iso(),
            "heartbeat_at": status_file.now_iso(),
            "heartbeat_interval_s": self.interval,
            "state": RUN_STATE_STARTING,
            "exit_code": None,
            "error": None,
            "resolutions": [],
        }
        if self.replay_flags is not None:
            # Not process state: written once here, never by update_run.
            record["replay_flags"] = list(self.replay_flags)
        route = _tool_route(self.host)
        if route:
            # Fix round 24 (live run 10): the tool route that started this
            # run, so a reader with no route of its own (a shell's `status`,
            # `util next-command`) spells its commands as that route's user
            # types them (`next_phase.recorded_route`). Written once.
            record["route"] = route
        status_file.claim_run(self.phase_dir, record)
        run_registry.write_entry(
            self.project_root,
            {
                "run_id": self.run_id,
                "pid": identity["pid"],
                "process_start_time": identity["process_start_time"],
                "pgid": pgid,
                "plan_file": self.plan_file,
                "phase_dir": self.phase_dir,
                "mode": self.mode,
                "host": self.host,
                "launch_key": launch_key(self.mode, self.plan_file, self.phase_dir),
                "started_at": record["started_at"],
                "log_path": self.log_path,
            },
        )
        # Imported *before* the handler is installed, never by it: `finish()`
        # retires the per-model map on the `--abort` path (F1, 2026-09-20), and
        # a first import executed inside a signal handler takes the import lock
        # the interrupted main thread may already be holding. Warming it here
        # turns that into a `sys.modules` hit. Kept lazy at module level for the
        # reason the whole file is: `status` must stay a sub-second command and
        # nothing on its path needs the tracker.
        from . import progress_tracker  # noqa: F401  (warm-up, see above)
        # Same reason: `_restore_codex_trust` runs inside the signal handler and
        # on the heartbeat-lost exit (plan codex-sandbox-unavailable I12).
        from . import codex_trust  # noqa: F401  (warm-up, see above)

        process_control.install_worker_signal_handlers(self._on_signal)
        atexit.register(self._atexit)
        self._beat = threading.Thread(
            target=self._beat_loop, name=f"multi-llm-heartbeat-{self.run_id[:8]}",
            daemon=True,
        )
        self._beat.start()
        status_file.update_run(
            self.phase_dir, {"state": RUN_STATE_RUNNING}, expect_run_id=self.run_id
        )
        _run_record._ACTIVE = self
        print(f"[DETACHED_RUN] run_id={self.run_id} pid={identity['pid']} "
              f"phase_dir={self.phase_dir}")

    def _apply_commit_stage(self) -> None:
        """Publish a commit front door's staged brief header, snapshot and
        ``commit_range``, right after this worker won the dir's lock.

        Under ``--detach`` the launcher publishes nothing (plans/review-commits.md
        §2.1, "Ownership before any write"): it stages what it decided and names
        the stage on this worker's argv. Applied here, before the run record is
        claimed and before the phase goes on to read the brief, so a launch
        that is refused, re-attaches, or loses the lock changes nothing. A
        stage that cannot be applied stops the worker before it claims the
        run: reviewing a brief other than the one the launcher decided would
        be the silent failure.
        """
        if not self.commit_stage:
            return
        try:
            apply_stage = _COMMIT_STAGE_APPLIER
            if apply_stage is None:
                raise RuntimeError("no stage applier was handed to this worker "
                                   "(register_commit_stage_applier)")
            apply_stage(self.commit_stage)
        except Exception as exc:  # noqa: BLE001 - any failure stops the worker
            self._lock.release()
            raise DetachError(
                f"ERROR: could not apply the commit-review stage {self.commit_stage}: "
                f"{exc}",
                exit_code=EXIT_ERROR,
            ) from exc

    def _acquire_lock(self) -> None:
        payload = {
            "run_id": self.run_id,
            "pid": os.getpid(),
            "process_start_time": process_control.process_start_time(os.getpid()),
            "host": self.host,
            "acquired_at": status_file.now_iso(),
        }
        # The hold this worker took at its entry (`PhaseRun`), so its
        # pre-flight ran under the lock: taken over, never taken twice (the OS
        # refuses a second descriptor), and released in `finish`.
        entry = _ENTRY_HOLDS.pop(_entry_key(self.phase_dir), None)
        if entry is not None and entry.held:
            entry.relabel(payload)
            self._lock = entry
            return
        # The lock this worker's launch handed it (POSIX; `launch`), adopted
        # rather than taken: it was held across the boundary.
        try:
            handed = _adopt_handed_lock(lock_path(self.phase_dir), payload)
        except (process_control.LockUnavailable, OSError) as exc:
            message = (f"ERROR: the phase lock handed to this worker could not be "
                       f"adopted ({exc}), so it stopped before it changed anything "
                       f"in {self.phase_dir}.")
            _record_worker_refusal(self.phase_dir, self.run_id, message)
            raise DetachError(message) from exc
        if handed is not None:
            self._lock = handed
            return
        try:
            self._lock.acquire(payload)
            return
        except process_control.LockUnavailable as exc:
            holder = exc.holder or {}
            # An unreadable payload is `unknown`, not `dead`: the lock is held by
            # *somebody* (that is why we are here) and the payload is written
            # after the lock is taken, so "nothing to read" is a live holder we
            # cannot name — never a licence to break the lock.
            verdict = process_control.holder_verdict(exc.holder)
            if verdict == process_control.DEAD:
                # And even then the break has to prove it: break_lock refuses a
                # lock that is still held, so a payload naming a dead predecessor
                # cannot displace the live holder that overwrote it.
                if process_control.break_lock(lock_path(self.phase_dir)):
                    print(
                        f"WARNING: breaking a stale {LOCK_NAME} left by run "
                        f"{holder.get('run_id')} (pid {holder.get('pid')} is gone).",
                        file=sys.stderr,
                    )
                    self._lock = process_control.PhaseLock(lock_path(self.phase_dir))
                    try:
                        self._lock.acquire(payload)
                        return
                    except process_control.LockUnavailable:
                        pass
            run = status_file.read_run(self.phase_dir)
            age = heartbeat_age(run)
            message = (
                "ERROR: another run owns this phase dir "
                f"({self.phase_dir}).\n"
                f"       holder run_id: {holder.get('run_id') or 'unrecorded'}\n"
                f"       holder pid:    {holder.get('pid') or 'unrecorded'} "
                f"({verdict})\n"
                f"       last heartbeat: "
                f"{'never' if age is None else f'{age:.0f}s ago'}\n"
                "       Wait for it, abort it (status <plan> --abort"
                + (f" --run-id {holder.get('run_id')}" if holder.get("run_id") else "")
                + "), or launch with --detach --force to stop it and take the "
                "dir over."
            )
            _record_worker_refusal(self.phase_dir, self.run_id, message)
            raise DetachError(message) from exc

    # -- heartbeat ------------------------------------------------------
    def _beat_loop(self) -> None:
        while not self._stop.wait(self.interval):
            if self._closed:
                return
            ok = status_file.update_run(
                self.phase_dir,
                {"heartbeat_at": status_file.now_iso()},
                expect_run_id=self.run_id,
                quiet=True,
            )
            if ok:
                continue
            # Our record was closed out (or taken over) while we were away. Do
            # not resurrect it: exit and leave the terminal record standing.
            print(
                "ERROR: this run's record in .status.json is no longer ours to "
                f"write (run {self.run_id} was closed out, or the phase dir was "
                "taken over); exiting without overwriting it.",
                file=sys.stderr,
            )
            self._stop.set()
            self._closed = True
            if self.hard_exit_on_lost:
                # `os._exit` skips `multi_llm.main`'s `finally`, so the codex
                # trust entries this run's children added are removed here or
                # never (plan codex-sandbox-unavailable I12).
                _restore_codex_trust()
                try:
                    sys.stderr.flush()
                    sys.stdout.flush()
                except (AttributeError, ValueError):
                    pass
                os._exit(EXIT_NEEDS_HUMAN)
            return

    # -- progress -------------------------------------------------------
    def progress(self, **updates: Any) -> None:
        status_file.update_progress(self.phase_dir, updates)

    def resolution(self, site: str, decision: str) -> None:
        """Append one auto-resolution to ``run.resolutions``. Records, never prints.

        The announcement is the *unattended* layer's (``unattended.record_resolution``
        prints ``[AUTO_RESOLVED] <site>: <decision>`` before delegating here), and it
        is the only caller of this path. Printing again would put the marker in a
        detached run's log twice for every resolution, which reads as two decisions.
        """
        status_file.append_resolution(
            self.phase_dir, run_id=self.run_id, site=site, decision=decision
        )

    # -- shutdown -------------------------------------------------------
    def finish(
        self,
        exit_code: Optional[int],
        *,
        state: Optional[str] = None,
        error: Optional[str] = None,
        result_state: Optional[str] = None,
    ) -> None:
        """Record the terminal state, and retire whatever the run left live.

        Idempotent; the first call wins.

        *result_state* is the dispatcher's ``MULTI_LLM_RESULT.state`` word, and
        it is recorded as ``run.result_state`` only when the exit code cannot
        express it (:func:`carried_result_state`) — today exactly
        ``cli_common.STATE_PARTIAL``. Anything else is recorded as ``null``:
        ``run.state`` keeps its process meaning (``done`` for a partial run
        that exited 0), and a crash's ``error`` word would only repeat the
        exit code.

        **The per-model map is closed out here, not by a sweep** (F1,
        2026-09-20). On every other ending the fan-out's own ``finally`` (or the
        ticker's) retires the map before this is reached, and this finds nothing
        left to do. ``--abort`` is the ending that runs no such code: the signal
        handler calls this and then ``os._exit(3)``, which executes no
        ``finally``, cancels no task and gives the ticker no teardown — so
        without the retirement below the checkpoint kept ``run.state: aborted``
        beside rows still reading ``running``/``staggering``/``queued`` and a
        ``models_done`` frozen mid-count, and a poll rendered
        ``codex:gpt-5.6-sol  running  30m00s/30m`` under a run that was over.
        This function is the only code on that path, so this is the only place
        it can go.

        Both writes sit in **one** :func:`status_file.checkpoint_lock` section,
        reentrant with the ones ``update_run`` and ``update_progress`` take for
        themselves, so no poller can catch a terminal ``run`` record beside a
        table that still says ``running``. The map is retired *on disk*
        (``progress_tracker.retire_live_entries``) rather than through a live
        tracker: this runs inside a signal handler, where the interrupted frame
        may be halfway through mutating one, and a ``full`` run has one tracker
        per phase anyway.

        Only a **non-normal** close-out retires: a ``done`` run really did finish
        its slots, and rewriting its map from here could only overwrite honest
        endings with ``cancelled``.
        """
        if self._closed:
            return
        self._closed = True
        self._stop.set()
        # The worker's teardown has begun: from here until it exits it starts
        # no provider CLI (`process_control.refuse_launches`), while a launch
        # already past its intent still records its identity for the abort.
        process_control.refuse_launches(self.run_id)
        if state is None:
            state = state_for_exit(exit_code)
        if error is None and exit_code == EXIT_NEEDS_HUMAN and state == RUN_STATE_FAILED:
            error = "needs_human (exit 3)"
        with status_file.checkpoint_lock(self.phase_dir):
            recorded = status_file.update_run(
                self.phase_dir,
                {
                    "state": state,
                    "exit_code": exit_code,
                    "error": error,
                    "result_state": carried_result_state(result_state),
                    "heartbeat_at": status_file.now_iso(),
                    "finished_at": status_file.now_iso(),
                },
                expect_run_id=self.run_id,
                quiet=True,
            )
            # Gated on the compare-and-set, not just on the state: a refused
            # write means this dir was closed out under us or taken over by a
            # *successor* run, whose `claim_run` dropped our `progress` and
            # seeded its own map — retiring that would mark a live run's slots
            # `cancelled`. Whoever recorded the ending owns the retirement, which
            # is why `close_out_dead_run` and `abort_run` carry the same pair.
            if recorded and state != RUN_STATE_DONE:
                # Warmed at `start()` so this cannot be the import that runs
                # under a signal; a no-op lookup in `sys.modules` by now.
                from . import progress_tracker

                progress_tracker.retire_live_entries(self.phase_dir)
            # An abort's kill under way (`CLEANUP_PENDING`), or a teardown
            # that could not confirm every process stopped: the run's trackers
            # are whoever records that outcome's to retire, not this ending's.
            current = status_file.read_run(self.phase_dir)
            teardown_open = (
                str(current.get("run_id")) == str(self.run_id) and cleanup_incomplete(current)
            ) or run_registry.entry_cleanup_open(self.project_root, self.run_id)
        if recorded and state != RUN_STATE_DONE:
            # And the dirs this run drove but does not own. A composite
            # (`full`) is the only kind of mode where those differ from
            # `self.phase_dir`, and the one where the line above sweeps a
            # directory that holds no map at all.
            # Outside the lock above on purpose — see `_retire_driven_phase_maps`.
            _retire_driven_phase_maps(self.phase_dir, self.mode)
        if not teardown_open:
            # Its CLIs have ended, so nothing will read the record.
            run_registry.remove_entry(self.project_root, self.run_id)
            _discard_cli_record(self.phase_dir, self.run_id)
        self._lock.release()
        if _run_record._ACTIVE is self:
            _run_record._ACTIVE = None

    def _atexit(self) -> None:
        """Backstop: no run may be left parked at ``running``.

        Reached when the process exits without anyone calling :meth:`finish` —
        a direct ``sys.exit`` deep in a target, say. The exit status is not
        observable from here, so it is recorded as ``null`` rather than guessed.
        """
        if self._closed:
            return
        self.finish(
            None,
            state=RUN_STATE_FAILED,
            error="worker exited without recording an outcome",
        )

    def _on_signal(self, signum: int) -> None:
        # `os._exit` is deliberate — a run being aborted must not run another
        # phase's `atexit`, and the process group has already been signalled —
        # but it is also why everything this ending owes the checkpoint has to
        # happen *inside* `finish()`: no `finally` below this frame will run, no
        # task is cancelled, and neither the fan-out's sweep nor the ticker's
        # teardown is ever reached. `finish()` retires the per-model map for
        # exactly that reason (F1, 2026-09-20); nothing may be added here that
        # expects to run after it.
        name = _signal_name(signum)
        # No provider CLI starts from here on (as in `finish`), so the sweep
        # below and the abort's reread see every one there is.
        process_control.refuse_launches(self.run_id)
        # Every line from here on goes straight to the fd: the signal may
        # have landed inside a buffered write to the very stream this would
        # print through, and a second copy may land inside this handler's
        # own (Codex racing run 6: `RuntimeError: reentrant call` instead of
        # the `aborted` record). `install_worker_signal_handlers` already
        # ignores the copies.
        stream_bootstrap.streams_for_a_signal_handler()
        print(f"\nReceived {name}: aborting this detached run.", file=sys.stderr)
        # Fix round 21: a write run's `[ETA]` lines get their closing line
        # here, since `os._exit` below skips every ending that would print it
        # ("batch 3/5 … ~0m 20s remaining" was the log's last word). Only a
        # module already imported: nothing is imported under a signal.
        _print_aborted_eta_line(name)
        # First, while the snapshots still name them: the provider CLIs this
        # worker is waiting on, and every process group they spawned. The
        # abort's `kill_tree` signals this worker's group, which holds the CLIs
        # but never a child they put in a session of its own (pi's detached
        # bash shells, a `timeout` inside one) — those would outlive the run.
        _sweep_live_clis()
        # Then, with the children dead, the codex trust entries they added to
        # the user's config (plan codex-sandbox-unavailable I12): `main`'s
        # `finally` restores them on every other ending, and `os._exit` below
        # skips it. Before `finish()`, so the phase lock is still held and no
        # successor run can arm the same config first.
        _restore_codex_trust()
        # The lock goes last, with the process: `os._exit` ends every thread
        # that could still write the phase dir, and only then does the kernel
        # drop the lock (docs/development/runtime.md, "One writer per phase dir").
        self._lock.hold_until_exit()
        self.finish(
            EXIT_NEEDS_HUMAN,
            state=RUN_STATE_ABORTED,
            error=f"aborted_by_request ({name})",
        )
        os._exit(EXIT_NEEDS_HUMAN)


def _print_aborted_eta_line(signal_name: str) -> None:
    """Print the open write run's closing ``[ETA]`` line on an abort
    (``metrics.aborted_eta_line``), when the metrics module is loaded at all
    — a run that stamped an ``[ETA]`` baseline loaded it. Never raises."""
    try:
        metrics = sys.modules.get(f"{__package__}.metrics") if __package__ else None
        line = metrics.aborted_eta_line(signal_name) if metrics is not None else None
        if line:
            print(line, file=sys.stderr)
    except Exception:  # noqa: BLE001 - the abort's record must still be written
        pass


def _restore_codex_trust() -> None:
    """Remove the codex trust entries this run's children added (plan I12) on
    the two worker endings that ``os._exit`` past ``multi_llm.main``'s
    ``finally``: ``--abort`` (the signal handler) and a lost heartbeat. The
    module was imported at :meth:`RunHandle.start`, so this is a
    ``sys.modules`` hit, never an import under a signal. Never raises."""
    try:
        # Imported here to keep run_status, which loads this module, light.
        from . import codex_trust

        codex_trust.restore_all()
    except Exception as exc:  # noqa: BLE001 - the abort's record must still be written
        print(f"multi-llm warning: could not restore codex's config: {exc}",
              file=sys.stderr)


def _sweep_live_clis() -> None:
    """Stop every registered Lane A CLI and its snapshotted process groups.

    One ``[ABORT_SWEEP]`` line per CLI into the run log, naming each group's
    verdict, so a ``survived`` group is on record. Never raises: the abort's own
    record (``finish``) must still be written whatever this hits.
    """
    try:
        swept = process_control.live_cli_registry.sweep()
    except Exception as exc:  # noqa: BLE001 - see above
        print(f"[ABORT_SWEEP] failed: {exc}", file=sys.stderr)
        return
    for entry, result in swept:
        print(f"[ABORT_SWEEP] cli pid {entry.pid}: {result.describe()}", file=sys.stderr)


def _signal_name(signum: int) -> str:
    try:
        return _signal.Signals(signum).name
    except (ValueError, AttributeError):  # pragma: no cover
        return f"signal {signum}"


def state_for_exit(exit_code: Optional[int]) -> str:
    """Map a process exit status onto the run's terminal state.

    ``0`` and ``2`` are both clean stops (``2`` is "nothing to do / already
    complete"); ``3`` is D6's needs-a-human and ``1`` an unexpected error, and both
    are ``failed`` so a poller's exit-3 branch fires.
    """
    if exit_code in (EXIT_OK, EXIT_NOTHING_TO_DO):
        return RUN_STATE_DONE
    return RUN_STATE_FAILED


#: The result words a detached run carries across the process boundary as
#: ``run.result_state``: only those the exit code cannot express. ``partial``
#: exits 0, which ``state_for_exit`` and ``cli_common.emit`` both read as
#: ``done``; every other result word (``error``, ``needs-human``,
#: ``nothing-to-do``) is already the exit code's own word.
CARRIED_RESULT_STATES = (STATE_PARTIAL,)


def carried_result_state(word: Optional[str]) -> Optional[str]:
    """*word* if it is a result state the exit code cannot express, else ``None``.

    Bounded on purpose: ``run.result_state`` is never the context's word
    verbatim, so a crash (context state ``error``) records ``null`` and a
    poll reports the exit code's word once, not twice.
    """
    return word if word in CARRIED_RESULT_STATES else None


def finish_active_run(
    exit_code: Optional[int],
    *,
    error: Optional[str] = None,
    result_state: Optional[str] = None,
) -> None:
    """Close out this process's run, if it owns one. Called by the dispatcher.

    *result_state* is the dispatcher's result-context state; see
    :meth:`RunHandle.finish` for how it is bounded.
    """
    handle = _run_record._ACTIVE
    if handle is not None:
        handle.finish(exit_code, error=error, result_state=result_state)


def note_left_running(pid: Optional[int], pgid: Optional[int],
                      verdict: Optional[str]) -> bool:
    """A kill made inside this process's run (the executor's timeout kill of
    its runner) could not confirm *pid* stopped (*verdict*): ``run.cleanup``
    :data:`CLEANUP_INCOMPLETE` on the run's record, naming *pid* and *pgid*.
    ``finish`` then keeps the run's CLI record, which holds that process's
    identity, and its registry entry; ``status`` and ``status --sweep`` report
    it, and an abort (or ``util runs --sweep`` once the worker is gone) stops
    it by that identity (:func:`retry_cleanup`). Only for a run whose worker
    records its launches (:func:`process_control.record_cli_identities`):
    elsewhere no record holds an identity a later kill could use. A cleanup
    already open (an abort under way) is left to its kill. ``True`` once
    written. Never raises."""
    handle = _run_record._ACTIVE
    try:
        if (handle is None or handle._closed
                or process_control._CLI_RECORD[:1] != [(handle.phase_dir, handle.run_id)]):
            return False
        with status_file.checkpoint_lock(handle.phase_dir):
            current = status_file.read_run(handle.phase_dir)
            if str(current.get("run_id")) != str(handle.run_id) or cleanup_incomplete(current):
                return False
            return status_file.update_run(handle.phase_dir, {"cleanup": {
                "state": CLEANUP_INCOMPLETE, "verdict": verdict,
                "pid": int(pid) if pid else None, "pgid": int(pgid) if pgid else None,
                "checked_at": status_file.now_iso(),
            }}, expect_run_id=handle.run_id, quiet=True)
    except Exception:  # noqa: BLE001 - a teardown never raises
        return False


def record_output_files(phase_dir: str, **paths: Any) -> None:
    """Record this phase's artifacts in ``output_files`` — detached runs only.

    ``status`` on a ``done`` run prints them and repeats them in
    ``MULTI_LLM_RESULT.artifacts``, so a host never globs a phase dir to discover
    what a detached run produced and never has to read the log on the success
    path. Only paths that exist are recorded; a foreground run writes nothing.
    """
    handle = _run_record._ACTIVE
    if handle is None or os.path.abspath(handle.phase_dir) != os.path.abspath(str(phase_dir)):
        return
    existing = {
        key: str(value) for key, value in paths.items()
        if value and os.path.exists(str(value))
    }
    if existing:
        status_file.update_status(phase_dir, {"output_files": existing})


def record_step_results(
    phase_dir: str, phase: str, steps: Sequence[Dict[str, Any]],
    artifacts: Sequence[str],
) -> None:
    """Record a composite's step results in its run dir — detached runs only.

    A composite's steps run in its process, so what each hands a caller (its
    notice, its verdict counts, its ``validation_context``) is on the worker's
    own result line and in the step's phase dir, never in the run dir a poll
    pins; a detached ``improve-commits`` poll carried none of it (live test
    2026-10-26, D2). The composite keeps each step's as the step returned and
    records them, with its *phase* and the line's artifacts, under its own
    ``run_id``: a later run in the same step dirs cannot change them, and a run
    that never got this far (aborted, crashed) leaves an earlier run's record,
    which ``status`` reads as no record at all.
    """
    handle = _run_record._ACTIVE
    if handle is None or os.path.abspath(handle.phase_dir) != os.path.abspath(str(phase_dir)):
        return
    status_file.update_status(phase_dir, {"step_results": {
        "run_id": handle.run_id,
        "phase": phase,
        "steps": [dict(step) for step in steps],
        "artifacts": [str(path) for path in artifacts if path and os.path.exists(str(path))],
    }})


def recorded_step_results(view: Dict[str, Any]) -> Dict[str, Any]:
    """*view*'s ``step_results`` when its own run recorded them, else ``{}``."""
    record = view.get("step_results")
    run = view.get("run") if isinstance(view.get("run"), dict) else {}
    if isinstance(record, dict) and run.get("run_id") and record.get("run_id") == run["run_id"]:
        return record
    return {}


# ---------------------------------------------------------------------------
# The invoker side
# ---------------------------------------------------------------------------

#: Printed verbatim by every ``--detach`` launch. The poll loop lives here, once,
#: so the shims quote it instead of each host inventing a cadence — and so the two
#: rules that make it safe travel with it: the wait happens *between* calls in the
#: host's own turn loop (never ``sleep <n>; status`` in one shell call, which
#: reintroduces the very shell-cap kill ``--detach`` exists to remove), and
#: closing the session does not stop the run.
POLL_LOOP_TEXT = (
    "How to watch it:\n"
    "  1. run the status command above; it is a file read plus a liveness probe "
    "(sub-second).\n"
    "  2. on exit 2 the run is still going: return to your turn loop and poll "
    "again in ~15s (~30s after the first two minutes — the heartbeat is 10s, so "
    "faster polling learns nothing).\n"
    "  3. stop on exit 0 (read output_files) or exit 3 (read run.error).\n"
    "  4. after this mode's documented ceiling, stop polling and abort rather "
    "than looping forever.\n"
    "  Never collapse the wait into one shell call (`sleep 90; status`): that is "
    "the shell-cap kill --detach exists to remove.\n"
    "  Closing this session does NOT stop the run — only the abort command does."
)


#: The banner's headline, and the field names under it, in printed order.
#:
#: Constants rather than inline f-strings because the banner is **parsed**, not
#: only read: it is the only place a launch reports its ``run_id``. The
#: ``MULTI_LLM_RESULT`` payload has no ``run_id`` key at all, and the launch's
#: ``next`` carries ``--run-id`` only for ``ask`` runs — so any host driving a
#: detached launch has to read it off these lines. The OpenCode plugin does, and
#: it reads this list out of generated data rather than spelling the field names
#: in JavaScript. Renaming a field here is therefore a change with a consumer,
#: and this is where that consumer looks.
BANNER_HEADLINE = "=== DETACHED RUN STARTED ==="
BANNER_FIELDS: Tuple[str, ...] = (
    "run_id", "pid", "mode", "phase", "log", "status", "abort",
)


def _print_banner(
    *,
    run_id: str,
    pid: int,
    mode: str,
    phase_dir: str,
    log: str,
    status_cmd: str,
    abort_cmd: str,
) -> None:
    values = {
        "run_id": run_id,
        "pid": pid,
        "mode": mode,
        "phase": phase_dir,
        "log": log,
        "status": status_cmd,
        "abort": abort_cmd,
    }
    width = max(len(name) for name in BANNER_FIELDS) + 3
    print("")
    print(BANNER_HEADLINE)
    for name in BANNER_FIELDS:
        print(f"  {(name + ':').ljust(width)}{values[name]}")
    print("")
    print(POLL_LOOP_TEXT)


def status_command_for(
    plan_file: str,
    *,
    phase: Optional[str] = None,
    run_id: Optional[str] = None,
    host: Optional[str] = None,
) -> str:
    """The poll command for one run, carrying the run's own selectors.

    ``host`` is one of them. ``status`` reports the subagent runner for the host
    it resolves, and with no ``--host`` that is the *reader's* — so the command
    a run on another host hands back would, run verbatim, describe a different
    host's dispatch than the one it is polling (measured 2026-09-16 on an
    opencode run: the emitted ``next`` omitted the flag and the line read
    ``claude-code:sonnet``). Omitted when the run recorded no host, rather than
    defaulted, because a guessed ``--host`` is exactly what D5b forbids.
    """
    args: List[str] = [plan_file, "--view", "run"]
    if phase:
        args += ["--phase", phase]
    if run_id:
        args += ["--run-id", run_id]
    if host:
        args += ["--host", host]
    # `--wait` with no `--timeout`, which resolves to `progress.poll_s` and is
    # then clamped under the `--host` above. This command is what four
    # instruction cores tell an agent to poll *instead of composing one*, and
    # they describe it as waiting — it did not (F2, 2026-09-20). Without the
    # flag each poll is a 0.13 s file read, so the turn loop spins at the
    # host's own pace rather than the run's, the announced "I will check back
    # in ~90 s" is a gap nobody waits, and `just finished:` can never print
    # here at all: only a wait spans the two readings that line is a
    # difference between. The clamp is why no `--timeout` is baked in — a
    # number chosen here could not know the reader's shell cap.
    args.append("--wait")
    return dispatcher_command("status", *args)


def abort_command_for(plan_file: str, *, run_id: str) -> str:
    return dispatcher_command("status", plan_file, "--abort", "--run-id", run_id)


def launch(
    *,
    mode: str,
    argv: Sequence[str],
    phase_dir: str,
    plan_file: str,
    phase: Optional[str] = None,
    args: Any = None,
    ask_slug: Optional[str] = None,
    model_specs: Optional[Sequence[str]] = None,
) -> int:
    """Fork the worker and return, printing the log/status/abort commands.

    Everything knowable before the fork is reported before it: an unresolvable
    ``uv``, an unwritable phase dir, the concurrency ceiling and a live lock holder
    all exit non-zero here, with no child spawned and no log file created.

    The launch holds the phase dir's lock from its gate to its worker: the
    entry hold a review launcher took (:class:`PhaseRun`), or the one taken
    here (:func:`take_for_launch`, which also re-attaches or takes a live run
    over), handed to the worker at the spawn (docs/development/runtime.md,
    "One writer per phase dir").
    """
    plan_file = os.path.abspath(str(plan_file))
    phase_dir = os.path.abspath(str(phase_dir))
    hold = _ENTRY_HOLDS.get(_entry_key(phase_dir))
    taken: Optional[process_control.PhaseLock] = None
    if (hold is None or not hold.held) and os.path.isdir(phase_dir) and os.access(
            phase_dir, os.W_OK):
        try:
            gate = take_for_launch(phase_dir, mode=mode, plan_file=plan_file,
                                   phase=phase, args=args)
        except OSError as exc:
            raise DetachError(
                f"ERROR: could not lock {lock_path(phase_dir)} ({exc}), so nothing "
                "was launched: a run writes its phase dir only while it holds it."
            ) from exc
        if isinstance(gate, int):
            return gate
        hold = taken = gate
    try:
        return _launch(mode=mode, argv=argv, phase_dir=phase_dir, plan_file=plan_file,
                       phase=phase, args=args, ask_slug=ask_slug,
                       model_specs=model_specs, hold=hold)
    finally:
        # A no-op once the worker has it (`_handed_over`).
        if taken is not None:
            taken.release()


def _launch(
    *,
    mode: str,
    argv: Sequence[str],
    phase_dir: str,
    plan_file: str,
    phase: Optional[str],
    args: Any,
    ask_slug: Optional[str],
    model_specs: Optional[Sequence[str]],
    hold: Optional[process_control.PhaseLock],
) -> int:
    """:func:`launch`, under *hold*."""
    force = _takes_over(args)
    if_not_running = bool(getattr(args, "if_not_running", False))
    # The launcher's `--host`, carried into every poll command printed below —
    # it is the host the worker records, so the poll must select it too.
    host = getattr(args, "host", None)
    uv = resolve_uv()

    if not os.path.isdir(phase_dir) or not os.access(phase_dir, os.W_OK):
        raise DetachError(
            f"ERROR: phase dir is not writable: {phase_dir}", exit_code=EXIT_ERROR
        )

    # -- provider binaries: knowable now, invisible once detached -------
    missing = missing_provider_binaries(model_specs, anchor=plan_file)
    if missing:
        listing = "\n".join(
            f"       {spec} -> {binary} (not on PATH)"
            for spec, binary in missing.items()
        )
        if len(missing) == len(model_specs or ()):
            raise DetachError(
                "ERROR: none of the requested models has its CLI installed, so a "
                "detached run could only ever produce failures:\n" + listing
                + "\n       Install one, or pass --models with a provider you have."
            )
        print(
            "WARNING: some requested models have no CLI on PATH and will fail; "
            "the run continues with the rest (a partial aggregate is usable "
            "output):\n" + listing,
            file=sys.stderr,
        )

    # -- the subagent runner: same check, other half of D4c step 3 ------
    # A detached run drives its own subagents, so its runner CLI is as load-
    # bearing as a model provider's — and, unlike a provider, an absent one is
    # not a partial aggregate: every dispatch lands on rung 1 (spawn_failed) and
    # fails the whole batch inside a log nobody is watching.
    if exec_subagents_in_effect(args, argv):
        runners = configured_runner_specs(anchor=plan_file)
        missing_runners = missing_runner_binaries(anchor=plan_file)
        primary = runners[0] if runners else None
        if primary and primary in missing_runners:
            raise DetachError(
                "ERROR: this run dispatches its own subagents "
                "(--exec-subagents), and the configured runner's CLI is not "
                "installed, so every dispatch would fail as spawn_failed:\n"
                f"       driver.subagent_runner {primary} -> "
                f"{missing_runners[primary]} (not on PATH)\n"
                "       Install it, or point driver.subagent_runner at a runner "
                f"you have ({dispatcher_command('init')})."
            )
        if missing_runners:
            print(
                "WARNING: a configured subagent runner has no CLI on PATH; only "
                "the tasks that resolve to it will fail:\n"
                + "\n".join(
                    f"       {spec} -> {binary} (not on PATH)"
                    for spec, binary in missing_runners.items()
                ),
                file=sys.stderr,
            )

    # -- re-attach beats relaunch --------------------------------------
    # Read under the lock this launch holds: a run recorded as live here is
    # not holding it, so it is not writing this phase dir.
    existing = classify_run(phase_dir, close_out=True)
    if existing["verdict"] in (VERDICT_RUNNING, VERDICT_STARTING, VERDICT_STALE):
        existing_id = str(existing["run"].get("run_id"))
        if if_not_running:
            return _print_reattach(phase_dir, existing["run"], plan_file=plan_file,
                                   phase=phase, host=host)
        if force:
            print(
                f"WARNING: --force replaces the record of run {existing_id}: it "
                f"does not hold {lock_path(phase_dir)}, which this launch holds, so "
                "it is not writing this phase dir, and its next heartbeat fails the "
                "run_id compare-and-set.",
                file=sys.stderr,
            )
        else:
            age = existing.get("heartbeat_age_s")
            raise DetachError(
                f"ERROR: a detached run already owns {phase_dir}.\n"
                f"       run_id:        {existing_id}\n"
                f"       pid:           {existing['run'].get('pid')} "
                f"({existing.get('identity')})\n"
                f"       last heartbeat: "
                f"{'never' if age is None else f'{age:.0f}s ago'}\n"
                "       Pass --if-not-running to re-attach to it, abort it "
                f"({abort_command_for(plan_file, run_id=existing_id)}), or pass "
                "--force to take the dir over."
            )
    if hold is None or not hold.held:  # pragma: no cover - the gate above
        raise DetachError(f"ERROR: this launch does not hold {lock_path(phase_dir)}, "
                          "so nothing was launched.")

    # -- the ceiling ---------------------------------------------------
    project_root = run_registry.resolve_project_root(plan_file)
    ceiling = run_registry.max_detached(getattr(args, "max_detached", None))
    live = run_registry.live_entries(project_root)
    live = [e for e in live if os.path.abspath(str(e.get("phase_dir", ""))) != phase_dir]
    if len(live) >= ceiling:
        lines = [
            f"ERROR: {len(live)} detached runs are already in flight for this "
            f"project (ceiling {ceiling}).",
        ]
        for entry in live:
            run = status_file.read_run(str(entry.get("phase_dir") or ""))
            age = heartbeat_age(run)
            lines.append(
                f"       {str(entry.get('run_id'))[:8]}  {entry.get('mode')}  "
                f"{entry.get('phase_dir')}  last heartbeat "
                f"{'never' if age is None else f'{age:.0f}s ago'}"
            )
        lines.append(
            "       Abort one of them, wait, or raise the ceiling "
            f"(--max-detached N / {run_registry.MAX_DETACHED_ENV})."
        )
        raise DetachError("\n".join(lines))

    # -- fork ----------------------------------------------------------
    run_id = str(uuid.uuid4())
    previous = status_file.read_run(phase_dir).get("run_id")
    rotate_log(phase_dir, previous)
    argv = _snapshot_question_file(argv, phase_dir)
    command = build_child_command(mode, argv, run_id=run_id, uv=uv)
    # The launcher's list, from the argv *before* build_worker_argv appends a
    # thing: the only process that can still tell a typed --yes from an implied
    # one is this one (D2 step 2, the *Later* bullet).
    env = child_env(
        replay_flags=replay_flags(mode, argv),
        plan_arg=_invoker_plan_arg(argv),
    )
    log = log_path(phase_dir)
    env[WORKER_LOG_ENV] = log
    # The lock crosses the boundary held: the worker inherits this launch's
    # open file description and adopts it, and from the spawn on this process
    # only closes its own copy (`_handed_over`). Windows: released here, taken
    # again by the worker (`_hand_off`).
    handoff = _hand_off(hold, env)
    try:
        # On Windows the worker starts inside the run's named Job Object, and
        # `run_job` is this launcher's handle on it (`None` elsewhere, and
        # wherever the job could not be made): held until the handshake
        # resolves, so a failed one ends exactly the tree it started, then
        # closed. By then the worker holds the job itself (2026-10-25).
        worker_pid, run_job = process_control.spawn_detached_run(
            command, cwd=os.getcwd(), env=env, log_path=log, run_id=run_id,
            **({"keep_fds": (handoff,)} if handoff is not None else {}),
        )
    except (OSError, process_control.SpawnFailed) as exc:
        _handed_over(hold)
        raise DetachError(
            f"ERROR: could not start the detached worker: {exc}", exit_code=EXIT_ERROR
        ) from exc
    finally:
        if handoff is not None:
            os.close(handoff)

    teardown: Optional[str] = None
    try:
        observed = _await_handshake(phase_dir, run_id)
        if observed is None:
            # By the start time read the moment the spawn reported the pid
            # (`process_control.detached_worker_start_time`): where the kill
            # goes by identity a pid alone is not signalled, and where it does
            # not, the call is the unverified kill it always was.
            kill_kwargs: Dict[str, Any] = {"escalate_after_s": 1.0}
            worker_start = process_control.detached_worker_start_time(worker_pid)
            if worker_start is not None:
                kill_kwargs["start_time"] = worker_start
            if run_job is not None:
                kill_kwargs["job"] = run_job
            try:
                teardown = process_control.kill_tree(worker_pid, **kill_kwargs)
            except Exception:
                teardown = None
    finally:
        if run_job is not None:
            run_job.close()
        _handed_over(hold)
    if observed is None:
        tail = _log_tail(log, 20)
        if _left_running(teardown):
            ending = (
                f"       Not confirmed stopped (kill verdict {teardown or 'unknown'}): "
                "what could not be identified as the worker was not signalled.\n"
                f"       Check pid {worker_pid} and what it started by hand.\n")
        else:
            ending = "       Nothing is left half-detached: the worker was terminated.\n"
        raise DetachError(
            f"ERROR: the detached worker (pid {worker_pid}) never published "
            f"run {run_id} within {handshake_timeout():.0f}s.\n"
            + ending
            + (f"       Last log lines:\n{tail}" if tail else "")
        )

    observed_state = observed.get("state")
    if observed_state in (RUN_STATE_FAILED, RUN_STATE_ABORTED):
        # The handshake accepts any published record, terminal ones included, so
        # a worker that died inside the window is knowable *here* — on the
        # caller's terminal, with the log still at hand. Reporting it now is the
        # launch contract; the started banner plus exit 0 would defer a failure
        # that has already happened to the caller's first status poll. Exit 3 is
        # what `status` maps a terminal failed/aborted run onto
        # (`run_status.exit_code_for`), so the launch and that first poll agree
        # whatever status the worker itself handed the OS.
        tail = _log_tail(log, 20)
        raise DetachError(
            f"ERROR: the detached worker for run {run_id} ended as "
            f"{observed_state} before the launch returned (recorded exit_code "
            f"{observed.get('exit_code')}).\n"
            f"       {observed.get('error') or 'no reason recorded'}\n"
            f"       log: {log}\n"
            + (f"       Last log lines:\n{tail}" if tail else ""),
            exit_code=EXIT_NEEDS_HUMAN,
        )

    status_cmd = status_command_for(
        plan_file, phase=phase, run_id=run_id if ask_slug else None, host=host
    )
    _print_banner(
        run_id=run_id,
        pid=int(observed.get("pid") or worker_pid),
        mode=mode,
        phase_dir=phase_dir,
        log=log,
        status_cmd=status_cmd,
        abort_cmd=abort_command_for(plan_file, run_id=run_id),
    )
    record_artifact(log)
    record_artifact(status_file.status_path(phase_dir))
    record_next(status_cmd)
    # The roster, on the first result line a supervising host can read.
    #
    # `progress_lines` is otherwise `status`'s key, rendered from
    # `progress.models` — which nothing has written at this instant, because the
    # worker seeds that map a moment from now. The launcher does not need it:
    # it is the process that *resolved the selection*, and it has already
    # refused this very launch if none of those specs had a CLI, so the roster
    # is knowable here without a map. `roster_line_for_specs` renders it through
    # the same budget resolution `seed()` uses, so the two processes emit one
    # sentence rather than two spellings of it.
    #
    # Why here rather than one poll later. On the OpenCode package route the
    # launch's result is the first thing `execute` can relay, the next relay is
    # a whole `--wait` away (~83 s, the host cap less a margin), and the
    # *terminal* poll is deliberately never relayed — so a run that went
    # terminal inside that first wait announced its line-up nowhere at all, and
    # every other run announced it a poll late, against a requirement that says
    # a fan-out names its models when it starts. Nothing changes on the JS side:
    # that route's launch seam already reads `result.progress_lines`, and its
    # per-call "shown once" memory drops the identical line the first poll
    # brings behind it.
    #
    # A launch with no fan-out — a `--reaggregate` branch, `generate-tasks`, the
    # write phases — renders "" here, and `set_progress_lines` drops an empty
    # entry, so an invocation with nothing to say grows no key.
    record_progress_lines([_launch_roster(model_specs, plan_file, args)])
    return EXIT_OK


def _invoker_plan_arg(argv: Sequence[str]) -> Optional[str]:
    """The ``--plan-file`` value the dispatcher received, before anything resolved it.

    Read from the invoker's recorded invocation (``_normalize_positionals``
    copied the plan positional there verbatim), falling back to *argv* — the
    same list :func:`maybe_detach` hands in from that record — for a caller that
    reached :func:`launch` without one. ``launch`` makes its own ``plan_file``
    absolute before this matters, so this is the only place the typed spelling
    survives (:data:`PLAN_ARG_ENV`). A continuation launched with the absolute
    path its hand-off printed ships the spelling the dispatcher recovered for it
    (the record's ``plan_arg``, ``cli_common.invocation_plan_arg``).
    """

    record = invocation()
    if record and record.get("plan_arg"):
        return str(record["plan_arg"])
    source = record.get("argv") if record else None
    value = flag_value(list(source or argv), "--plan-file")
    return value or None


def _launch_roster(
    model_specs: Optional[Sequence[str]], plan_file: str, args: Any
) -> str:
    """This launch's roster line, or ``""`` — never an exception.

    Imported lazily like every other `progress_tracker` reach from this module,
    and wrapped, because the line is narration: a banner that has already been
    printed for a worker that is already running must not turn into a traceback
    over a config read. The anchor is the plan (§9.3.c) and the override is the
    run's own `--timeout`, which is exactly what the tracker will be constructed
    with on the other side of the fork.
    """
    try:
        # Imported here to keep run_sweep, which loads this module, light.
        from . import progress_tracker

        return progress_tracker.roster_line_for_specs(
            model_specs, anchor=plan_file, timeout=getattr(args, "timeout", None)
        )
    except Exception as exc:  # noqa: BLE001 - narration never fails a launch
        note_swallowed("detach: launch roster line", exc)
        return ""


def _snapshot_question_file(argv: Sequence[str], phase_dir: str) -> List[str]:
    """Copy a dispatcher-written ``--question-file`` into the phase dir.

    A question too long for argv is handed over as a temp file that the
    dispatcher owns for the length of *its* invocation — and the invoker returns
    (deleting it) while the worker is still starting. The handshake happens to
    order those two correctly today, but a detached run must not depend on the
    startup order of a process it cannot see, so the file becomes the run's own.
    Dot-prefixed, so it is invisible to anything that globs the dir.
    """
    out = list(argv)
    for index, token in enumerate(out):
        if token != "--question-file" or index + 1 >= len(out):
            continue
        source = out[index + 1]
        target = os.path.join(phase_dir, ".question.txt")
        try:
            with open(source, "r", encoding="utf-8") as src:
                text = src.read()
            with open(target, "w", encoding="utf-8") as dst:
                dst.write(text)
            out[index + 1] = target
        except (OSError, IOError, UnicodeDecodeError):
            pass  # leave the original path; the worker will report the failure
    return out


def _await_handshake(phase_dir: str, run_id: str) -> Optional[Dict[str, Any]]:
    """Block (bounded) until the worker publishes its own identity.

    The POSIX double-spawn produces three pids and only the final worker is
    authoritative, so the invoker never guesses ``run.pid``: it waits for the
    worker's own record. If that never appears, the launch failed and says so.

    D4b's handshake is exactly two facts — ``run.run_id`` matching the id this
    invoker minted **and** ``run.state`` at ``running`` (or already past it) —
    so a record that claimed the dir and stalled at ``starting`` is not a
    launched run however plausible its ``pid`` looks. Returning it would have
    the launch banner-print a worker that never came up; ``None`` sends the
    caller down the kill-and-report path instead.
    """
    deadline = time.time() + handshake_timeout()
    while True:
        run = status_file.read_run(phase_dir)
        if run.get("run_id") == run_id and run.get("state") in (
            RUN_STATE_RUNNING, *TERMINAL_RUN_STATES
        ):
            return run
        refusal = _read_worker_refusal(phase_dir, run_id)
        if refusal is not None:
            # The worker stopped at the lock and published nothing: this launch
            # reports that, never a run (`_record_worker_refusal`).
            raise DetachError(
                f"ERROR: the detached worker for run {run_id} stopped before it took "
                f"{phase_dir}, so no run was launched.\n"
                + str(refusal.get("message") or "(no reason recorded)")
            )
        if time.time() >= deadline:
            return None
        time.sleep(0.05)


def _log_tail(path: str, lines: int) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            tail = f.read().splitlines()[-lines:]
    except (OSError, IOError):
        return ""
    return "\n".join(f"         {line}" for line in tail)


# ---------------------------------------------------------------------------
# The one hook the orchestrators call
# ---------------------------------------------------------------------------

def mode_supports_detach(mode: Optional[str]) -> bool:
    return mode in DETACH_MODES


def handle_phase_detach(
    *,
    args: Any,
    mode: str,
    argv: Sequence[str],
    phase_dir: str,
    plan_file: str,
    phase: Optional[str] = None,
    ask_slug: Optional[str] = None,
    model_specs: Optional[Sequence[str]] = None,
) -> Optional[int]:
    """``None`` to keep running in this process; an exit code to return instead.

    Called by each fan-out orchestrator at the point where pre-flight has passed
    and the phase dir exists — arguments checked, inputs read, models resolved,
    output dir created — and *before* any model runs. Both directions of the
    detach story pass through here:

    * ``--internal-worker``: this process *is* the worker. Take the lock, publish
      identity, start the heartbeat, then carry on with the phase in-process.
    * ``--detach``: this process is the invoker. Fork, hand back the log and the
      status/abort commands, and return.
    """
    if getattr(args, "internal_worker", False):
        begin_worker_run(
            phase_dir=phase_dir, mode=mode, plan_file=plan_file, args=args,
            phase=phase,
        )
        return None
    if not getattr(args, "detach", False):
        return None
    if not mode_supports_detach(mode):
        raise DetachError(
            f"ERROR: --detach is not available for mode '{mode}' yet.\n"
            f"       It covers the long-running fan-out modes today: "
            f"{', '.join(DETACH_MODES)}.\n"
            "       Run this mode in the foreground (it emits task JSON and "
            "exits) or under your host's own background mechanism."
        )
    return launch(
        mode=mode,
        argv=argv,
        phase_dir=phase_dir,
        plan_file=plan_file,
        phase=phase,
        args=args,
        ask_slug=ask_slug,
        model_specs=model_specs,
    )


def begin_worker_run(
    *, phase_dir: str, mode: str, plan_file: str, args: Any,
    phase: Optional[str] = None,
) -> "RunHandle":
    """Start this process's ownership of a phase dir as the detached worker."""
    run_id = getattr(args, "internal_run_id", None) or str(uuid.uuid4())
    detached = os.environ.get(WORKER_ENV) == "1"
    # Popped, not read: the list must reach neither the provider subprocesses
    # this worker spawns nor any argv-echo of them (a short `ask` question
    # would otherwise ride along in every child's environment).
    replay = decode_replay_flags(os.environ.pop(REPLAY_FLAGS_ENV, None))
    # Same rule: the launcher's typed plan goes into the record, not into the
    # environment of every provider child this worker spawns.
    plan_arg = os.environ.pop(PLAN_ARG_ENV, None) or None
    if detached:
        # On both platforms the launcher already handed the log in as this
        # process's stdout/stderr, so this is normally a no-op on the
        # descriptors and a real call only for the stream bootstrap (line
        # buffering AND utf-8/replace). It stays here rather than moving earlier
        # because it is also the fallback for a worker that did *not* arrive
        # through `spawn_detached`.
        #
        # Consequence, and it is the intended one: the phase's own setup output —
        # everything the orchestrator printed on its way to this boundary — is
        # already in the log above the `[DETACHED_RUN]` banner. That ordering is
        # correct, not a leak: the banner marks where the *invoker* stopped
        # sharing the run, and the lines above it are the worker's own copy of
        # what the invoker printed on the caller's terminal.
        #
        # The run id goes with it: on Windows the worker holds the run's named
        # Job Object for life from here, which is what an abort opens.
        process_control.enter_detached_worker(log_path(phase_dir), run_id=run_id)
        # Every process this worker starts from here on (`popen_tree`), by
        # pid, start time and group: if it dies without its handler, they are
        # what its close-out signals (`close_out_dead_run`).
        process_control.record_cli_identities(phase_dir, run_id)
    handle = RunHandle(
        phase_dir,
        run_id=run_id,
        mode=mode,
        plan_file=plan_file,
        host=getattr(args, "host", None),
        detached=detached,
        replay_flags=replay,
        plan_arg=plan_arg,
        commit_stage=getattr(args, "commit_stage", None),
        phase=phase,
    )
    handle.start()
    return handle
