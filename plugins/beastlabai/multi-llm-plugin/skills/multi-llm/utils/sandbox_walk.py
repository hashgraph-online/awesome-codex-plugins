"""The sandbox gate: probe the runner's own sandbox, walk the fallback
ladder, and say what was decided (D3k, the plugin-landlock rung).

:func:`sandbox_verdict` and :func:`cached_sandbox_verdict` (one probe per
runner version, shared with the fan-out), the ladder walk
(:func:`_walk_fallback_rungs`, :func:`_walk_wrapped_rung`), the policy
(:func:`sandbox_fallback_rung`), the preflight's sandbox leg
(:func:`_detect_sandbox`, :func:`repo_wide_write_refusal`) and the lines it
prints (:func:`sandbox_walk_note`, :func:`write_rung_notice`, the F6 jail
sentences). Its state lives in ``probe_state``.

``utils.subagent_executor`` re-exports every name defined here for reading
only: patch one here, never through the executor
(docs/development/delegation.md#where-the-executors-helpers-live).
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import os
import subprocess
import sys
import tempfile
import threading
import time
from typing import Any, Dict, Iterator, List, Mapping, Optional, Sequence, Tuple

from . import process_control
from . import write_safety as _write_safety
from .git_utils import get_project_root_from_dir
from .llm_client import _resolve_executable
from .provider_registry import get_provider
from .providers.codex import PLUGIN_LANDLOCK_CANARY_POSITIVE_EXIT
from . import landlock_dispatch
from .providers.base import (
    HOST_POSTURE_FULL_ACCESS,
    HOST_SANDBOX_POSTURE_ENV,
    INCIDENTAL_LANE_EXECUTOR,
    JailRequest,
    SANDBOX_WRITE_FALLBACK_PROFILES,
    SKIP_RUNG_ENV,
    WALK_OUTCOME_SKIPPED_BY_SWITCH,
    WRITE_SCOPE_REPO_WIDE,
    WRITE_SCOPES_BY_CONSENT,
    WRITE_SCOPES_ON_RUNG,
    host_write_posture_consent,
    rung_is_incidental,
    sandbox_incidental_notice_text,
    skip_rung_requested,
    version_newer,
    write_consent_allows,
    write_rung_allowed,
    PROFILE_AGENT_READONLY,
    PROFILE_AGENT_WRITE,
    SANDBOX_BYPASSED_MARKER,
    SANDBOX_CANARY_DENIED,
    SANDBOX_CANARY_NOT_DENIED,
    SANDBOX_FALLBACK_AUTO,
    SANDBOX_FALLBACK_CONTAINED,
    SANDBOX_FALLBACK_OFF,
    SANDBOX_FALLBACK_PROFILES,
    SANDBOX_RUNG_UNSANDBOXED,
    SandboxRung,
    sandbox_bypassed_notice_text,
    sandbox_fallback_notice_text,
    sandbox_rung_allowed,
    sandbox_rung_retired_notice,
    sandbox_walk_clause,
    rung_probe_said_removed,
    rung_removed_for_version,
    sandbox_probe_inconclusive,
)
from . import failure_capture as _failure_capture
from . import task_outcome as _task_outcome
from . import runner_selection as _runner_selection
from . import probe_state as _probe_state


#: Wall-clock budget for the D6 sandbox self-test (`sandbox_probe_command`).
#: The command is model-free — codex's runs in ~30 ms — so ten seconds is
#: generous; a probe that outlives it is recorded ``unknown`` and dispatches,
#: exactly like the nested-exec probe's inconclusive branch.
SANDBOX_PROBE_TIMEOUT_S = 10.0

#: How long a timed-out sandbox probe's tree kill, and then the read of what is
#: left in its pipes, may each take on Windows (:func:`_run_sandbox_probe`).
#: The kill is a Job Object's, a single call; the bound is for the ``taskkill``
#: fallback of a probe that got no job.
SANDBOX_PROBE_KILL_S = 1.0

#: The advisory readers' probe budget (`status`, `init`, the next-step block:
#: `repo_wide_write_refusal`), for the standard probe and the rung walk
#: together. `status` has a sub-second contract and dispatches nothing, so a
#: probe that hangs or is slow must cost it this much at most and draw no
#: warning (a warning that may be wrong is worse than none) — and a
#: measurement this budget cut short is never cached, so a dispatch later in
#: the same process probes afresh under `SANDBOX_PROBE_TIMEOUT_S`, which
#: does not move (adversarial review, 2026-10-02).
ADVISORY_PROBE_BUDGET_S = 1.0


def _run_sandbox_probe(
    argv: Sequence[str],
    *,
    cwd: Optional[str],
    timeout: float,
    env: Optional[Mapping[str, str]] = None,
) -> Optional["subprocess.CompletedProcess"]:
    """Run one ``sandbox_probe_command`` argv (D6 step 3).

    A sibling of :func:`_run_probe` rather than a flag on it — a write
    profile's probe writes a byte, so it has to run with ``cwd`` at the repo
    root the dispatch would use, and it has its own, shorter budget. ``None``
    means the command could not be run at all (the binary vanished between
    ``is_available`` and here, the interpreter refused the spawn) and every
    caller reads it as ``unknown``: a preflight probe reports, it never blocks
    on its own failure.
    A timeout is ``None`` too, for the same reason.

    ``env`` (plan codex-sandbox-unavailable §6 F1, 2026-09-30) is the wrapped
    rung probe's own environment — the probe's ``TMPDIR`` and the canary's
    seeded file and targets — from ``landlock_dispatch.rung_probe``; ``None``
    inherits this process's, as every other probe does.
    """
    launcher, _ = _resolve_executable(argv[0])
    kwargs: Dict[str, Any] = {}
    if env is not None:
        kwargs["env"] = dict(env)
    if process_control.IS_WINDOWS:
        return _run_sandbox_probe_tree([*launcher, *argv[1:]], cwd=cwd,
                                       timeout=timeout, **kwargs)
    try:
        return subprocess.run(
            [*launcher, *argv[1:]],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            stdin=subprocess.DEVNULL,
            cwd=cwd,
            **kwargs,
        )
    except (OSError, subprocess.SubprocessError):
        return None


def _run_sandbox_probe_tree(
    command: Sequence[str], *, cwd: Optional[str], timeout: float, **kwargs: Any,
) -> Optional["subprocess.CompletedProcess"]:
    """:func:`_run_sandbox_probe` on Windows, where ``subprocess.run`` does not
    keep its timeout.

    There ``run`` kills the direct child alone on a timeout and then reads both
    pipes to their end with no timeout at all, so a grandchild still holding
    them (``sh -c`` → ``sleep``, a CLI's own helper) held the probe for as long
    as it lived: 5.3 s against a 0.2 s budget on the Windows CI (Windows port,
    round seven). A timed-out probe's whole tree is killed instead and its
    pipes are read for at most :data:`SANDBOX_PROBE_KILL_S` more, then let go
    unclosed — a close would wait on the read that holds them. ``None`` on a
    timeout, as before.

    The probe runs in a Job Object (``process_control.popen_tree``), so the
    kill is one ``TerminateJobObject`` call that reaches exactly its tree
    (round-8 review): ``taskkill /T``, now only the fallback for a probe that
    got no job, walks parent pids and can reach an unrelated orphan, and
    within :data:`SANDBOX_PROBE_KILL_S` on a loaded runner it can time out
    having killed nothing past the direct child.
    """
    try:
        proc, job = process_control.popen_tree(
            list(command),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=cwd,
            **kwargs,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        process_control.end_tree(proc.pid, job, timeout=SANDBOX_PROBE_KILL_S)
        try:
            proc.kill()
        except OSError:  # pragma: no cover - already gone
            pass
        try:
            proc.communicate(timeout=SANDBOX_PROBE_KILL_S)
        except (subprocess.SubprocessError, OSError, ValueError):
            pass
        return None
    except BaseException as exc:
        # What `run` does on any other way out: no child left, and an OSError
        # is "could not be run", like the spawn's.
        if job is None or not job.terminate():
            proc.kill()
        if isinstance(exc, (OSError, subprocess.SubprocessError)):
            return None
        raise
    finally:
        if job is not None:
            job.close()
    return subprocess.CompletedProcess(proc.args, proc.returncode, stdout, stderr)


#: How one rung of the fallback walk ended (landlock rung, 2026-09-22).
#: ``taken`` — the rung was selected; ``rejected`` — its probe exited but its
#: containment canary's write was NOT denied (the flag was a no-op: fail-open);
#: ``unavailable`` — a real sandbox failure; ``absent`` — the CLI did not
#: understand the probe (this build does not know the rung), or exited 0
#: without the canary's affirmative ``SANDBOX_CANARY_DENIED`` marker (the
#: canary never ran to completion, so no boundary was measured); ``unprobed`` — the
#: walk's shared deadline ran out before or while this rung was measured;
#: ``unknown`` — the probe produced no exit status for another reason (spawn
#: failure), or the rung's canary directory (``SandboxRung.probe_workdir``)
#: could not be created and proven writable outside the sandbox, so the probe
#: was never run. The first four let the walk continue (``taken`` ends it with a
#: rung); the last two **stop** it with none: "nothing learned" never licenses
#: a widening.
RUNG_TAKEN = "taken"
RUNG_REJECTED = "rejected"
RUNG_UNAVAILABLE = "unavailable"
RUNG_ABSENT = "absent"
RUNG_UNPROBED = "unprobed"
RUNG_UNKNOWN = "unknown"
#: 2026-09-24 (plan §3): ``skipped`` — not probed because the detected CLI
#: version is at or above the rung's ``removed_at`` (the probe would only
#: re-measure a known exit-101 panic); ``retired`` — probed, and its output
#: carried the rung's ``removed_signature`` (codex 0.156.1's "requires
#: bubblewrap" panic), classified by text and never by exit code. Both let the
#: walk continue, like ``unavailable``; they are the two outcomes that earn the
#: retirement line. A timeout, a canary-setup failure or any other error is
#: never either of them.
RUNG_SKIPPED = "skipped"
RUNG_RETIRED = "retired"
#: 2026-09-30 (plan codex-sandbox-unavailable §6 F1 item 6): the process was
#: told to skip this rung (``MULTI_LLM_CODEX_SKIP_RUNG=plugin-landlock``). Not
#: probed, the walk moves on — and never a retirement, so it earns no
#: retirement line. Base's word, so the walk clause renders it.
RUNG_SKIPPED_BY_SWITCH = WALK_OUTCOME_SKIPPED_BY_SWITCH


def _sandbox_probe_inconclusive(text: str) -> bool:
    return sandbox_probe_inconclusive(text)


def _fallback_rungs(provider: Any, profile: str) -> Tuple[SandboxRung, ...]:
    """The adapter's declared ladder for ``profile``, or ``()``.

    ``getattr`` because a test's stand-in adapter may not declare the hook, and
    any failure reads as "no ladder" — a diagnostic may not break a preflight,
    and no ladder is the narrow reading.
    """
    hook = getattr(provider, "sandbox_fallback_rungs", None)
    if not callable(hook):
        return ()
    try:
        return tuple(hook(profile) or ())
    except Exception:  # noqa: BLE001 - a diagnostic may not break a preflight
        return ()


def _prepare_probe_workdir(cwd: Optional[str], workdir: str) -> Optional[List[str]]:
    """Create ``workdir`` under ``cwd`` and prove a file can be written there —
    outside any sandbox — before a contained rung's canary runs in it.

    Returns the directories this call created (deepest first, for
    :func:`_remove_created_dirs`), or ``None`` when the directory cannot be
    made (a non-directory in the way) or is not writable by this user: a
    canary whose write is refused by plain permissions must not read as a
    boundary. Anything this call created is removed again on failure.
    """
    base = os.path.abspath(cwd or os.getcwd())
    target = os.path.join(base, workdir)
    created: List[str] = []
    missing: List[str] = []
    probe = target
    while probe != base and not os.path.lexists(probe):
        missing.append(probe)
        probe = os.path.dirname(probe)
    try:
        for path in reversed(missing):
            os.mkdir(path)
            created.insert(0, path)
        if not os.path.isdir(target):
            raise NotADirectoryError(target)
        fd, scratch = tempfile.mkstemp(prefix="sandbox-setup-", dir=target)
        os.close(fd)
        os.unlink(scratch)
    except OSError:
        _remove_created_dirs(created)
        return None
    return created


def _remove_created_dirs(created: Optional[Sequence[str]]) -> None:
    """``rmdir`` what :func:`_prepare_probe_workdir` created, deepest first.

    Only ever those directories, only if empty, and quietly: a canary that ran
    unsandboxed may already have removed them itself.
    """
    for path in created or ():
        try:
            os.rmdir(path)
        except OSError:
            pass


#: The interprocess mutex a rung probe holds while its canary directory
#: exists, one file per repository under the system temp dir (never unlinked,
#: like every lock file of ``process_control``).
PROBE_WORKDIR_LOCK_PREFIX = "multi-llm-probe-"


def _probe_workdir_lock_path(cwd: Optional[str]) -> str:
    base = os.path.realpath(cwd or os.getcwd())
    digest = hashlib.sha256(base.encode("utf-8", "surrogateescape")).hexdigest()[:16]
    return os.path.join(tempfile.gettempdir(), f"{PROBE_WORKDIR_LOCK_PREFIX}{digest}.lock")


@contextlib.contextmanager
def _probe_workdir(
    cwd: Optional[str], workdir: Optional[str], deadline: float,
) -> Iterator[Optional[List[str]]]:
    """Prepare a rung probe's canary directory, serialized across processes,
    and remove what was created once the probe has run.

    Yields what :func:`_prepare_probe_workdir` created (``[]`` for a rung with
    no ``probe_workdir``), ``None`` when it could not be prepared — or when the
    mutex could not be taken before ``deadline`` (the caller reads the clock
    and records ``unprobed``). Each probe only ever removes the directories
    it created, so two probes of one repository at once — twelve concurrent
    ``status`` polls, measured 2026-10-02 — used to leave an empty
    ``.multi-llm/`` and ``.multi-llm/tmp/`` behind: the first one's ``rmdir``
    failed on the second one's seed, and the second one had created nothing.
    Under the mutex the second waits its turn and creates and removes its own.
    A mutex file that cannot be opened proceeds unserialized, as before.
    """
    if not workdir:
        yield []
        return
    mutex = process_control.FileMutex(_probe_workdir_lock_path(cwd))
    acquired = mutex.acquire(timeout_s=max(0.0, deadline - time.monotonic()))
    try:
        if not acquired and time.monotonic() >= deadline:
            yield None
            return
        created = _prepare_probe_workdir(cwd, workdir)
        try:
            yield created
        finally:
            _remove_created_dirs(created)
    finally:
        mutex.release()


def _rung_probe_tail(rung: SandboxRung, completed: Any) -> str:
    """The redacted line a rung's probe is remembered by: the line carrying
    its ``removed_signature`` when present, else the last non-empty line of
    stderr (stdout when stderr is empty)."""
    text = f"{completed.stderr or ''}\n{completed.stdout or ''}"
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    signature = getattr(rung, "removed_signature", None)
    if signature:
        needle = " ".join(signature.split())
        hit = next((line for line in lines if needle in " ".join(line.split())), None)
        if hit is None and rung_probe_said_removed(rung, text):
            hit = needle
        if hit:
            return _failure_capture._redact_probe_tail(hit, 500)
    source = [line.strip() for line in (completed.stderr or completed.stdout or "").splitlines()
              if line.strip()]
    return _failure_capture._redact_probe_tail(source[-1] if source else "", 500)


def _scrub_probe_paths(text: str, *paths: Optional[str]) -> str:
    """``text`` with the rung probe's own per-attempt paths replaced by
    placeholders, so no cached tail holds a slot ``TMPDIR`` or a seeded file
    (plan F1 "Task-specific paths stay out of shared state and caches")."""
    for path in paths:
        if path:
            text = text.replace(path, landlock_dispatch.PLACEHOLDER_TMPDIR)
    return text


def _walk_wrapped_rung(
    rung: SandboxRung,
    *,
    cwd: Optional[str],
    deadline: float,
    request: Optional[JailRequest],
    tails: Optional[List[Tuple[str, str]]],
) -> Tuple[str, bool]:
    """One wrapping rung's turn in the walk: ``(outcome, stop the walk)``.

    Plan codex-sandbox-unavailable §6 F1 "Where it sits" item 3 (2026-09-30).
    The rung has three kinds of result, and the walk keeps its old rule for
    each: a probe that measured nothing never counts as a failed rung.

    * **Skipped** (``MULTI_LLM_CODEX_SKIP_RUNG=plugin-landlock``): not probed,
      the walk moves on, never a retirement. A value the switch does not
      accept stops the walk (never ignored, never a widening).
    * **Stops the walk with no rung**: the deadline was already spent
      (``unprobed``), the negative target, seeded file or probe ``TMPDIR``
      could not be prepared outside the jail (``unknown``), or the probe
      produced no exit status (``unknown``/``unprobed``).
    * **Measured**, from the wrapper's exit and the canary: exit 126 (no
      Landlock, an ABI below 3) or 125 (a required allow entry missing) —
      and a required entry refused before the spawn (``JailRefused``, e.g.
      ``$CODEX_HOME`` missing) — are ``absent``; a write or truncation that
      landed (``SANDBOX_CANARY_NOT_DENIED``, or the parent's byte comparison
      of the seeded file) is ``rejected``; a failed positive control (exit 5)
      is ``unavailable``; exit 0 with ``SANDBOX_CANARY_DENIED`` and the seed
      intact is ``taken``; exit 0 without the marker is ``absent``; any other
      exit reads through the existing branches.

    The probe gets only what is left of the walk's one shared deadline, never
    a timeout of its own.
    """
    try:
        skipped = skip_rung_requested()
    except ValueError as exc:
        if tails is not None:
            tails.append((rung.name, _failure_capture._redact_probe_tail(str(exc), 500)))
        return RUNG_UNKNOWN, True
    if skipped == rung.name:
        return RUNG_SKIPPED_BY_SWITCH, False
    if deadline - time.monotonic() <= 0:
        return RUNG_UNPROBED, True
    with _probe_workdir(cwd, rung.probe_workdir, deadline) as created:
        if created is None:
            ran_out = time.monotonic() >= deadline
            return (RUNG_UNPROBED if ran_out else RUNG_UNKNOWN), True
        if request is None:
            request = JailRequest(
                repo_root=os.path.realpath(cwd or os.getcwd()), kind=PROFILE_AGENT_READONLY,
            )
        launcher, _ = _resolve_executable(str(rung.probe_argv[0]))
        resolved = [*launcher, *(str(a) for a in rung.probe_argv[1:])]
        completed = None
        seed_intact = True
        scrub: Tuple[Optional[str], ...] = ()
        try:
            with landlock_dispatch.rung_probe(rung, request, resolved, cwd=cwd) as probe:
                scrub = (probe.env.get("TMPDIR"), probe.seeded)
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return RUNG_UNPROBED, True
                completed = _run_sandbox_probe(
                    probe.argv, cwd=cwd, timeout=remaining, env=probe.env,
                )
                seed_intact = probe.seed_intact()
        except landlock_dispatch.ProbeSetupFailed as exc:
            if tails is not None:
                tails.append((rung.name, _failure_capture._redact_probe_tail(str(exc), 500)))
            return RUNG_UNKNOWN, True
        except landlock_dispatch.JailRefused as exc:
            # A required entry the probe (and so every dispatch it gates) cannot
            # be granted: the rung is not usable here, measured before any spawn.
            if tails is not None:
                tails.append((rung.name, _failure_capture._redact_probe_tail(exc.message, 500)))
            return RUNG_ABSENT, False
    if completed is None:
        ran_out = time.monotonic() >= deadline
        return (RUNG_UNPROBED if ran_out else RUNG_UNKNOWN), True
    said = f"{completed.stdout}\n{completed.stderr}"
    note = landlock_dispatch.wrapper_note(completed.stderr)
    if tails is not None:
        if not seed_intact and SANDBOX_CANARY_NOT_DENIED not in said:
            # The parent's byte comparison caught what the canary did not: the
            # canary's last line is its DENIED marker, which would read as the
            # opposite of the verdict (acceptance review, 2026-09-30).
            tail = "the truncation control changed the seeded file (truncate(2) was not denied)"
        else:
            tail = _failure_capture._redact_probe_tail(note, 500) if note else _rung_probe_tail(rung, completed)
        tails.append((rung.name, _scrub_probe_paths(tail, *scrub)))
    if SANDBOX_CANARY_NOT_DENIED in said or not seed_intact:
        # Checked first: a write or truncation that landed rejects the rung
        # whatever the exit status says — the canary's own word, or the
        # parent's byte comparison of the seeded file.
        return RUNG_REJECTED, False
    if completed.returncode in (
        landlock_dispatch.EXIT_UNAVAILABLE, landlock_dispatch.EXIT_REQUIRED_ENTRY,
    ):
        return RUNG_ABSENT, False
    positive_exit = _plugin_landlock_positive_exit()
    if completed.returncode == positive_exit:
        return RUNG_UNAVAILABLE, False
    if completed.returncode == 0 and SANDBOX_CANARY_DENIED in said:
        return RUNG_TAKEN, False
    if completed.returncode == 0:
        return RUNG_ABSENT, False
    if rung_probe_said_removed(rung, said):
        return RUNG_RETIRED, False
    if _sandbox_probe_inconclusive(said):
        return RUNG_ABSENT, False
    return RUNG_UNAVAILABLE, False


def _plugin_landlock_positive_exit() -> int:
    """The rung canary's positive-control exit (5), read from the adapter
    module so the two cannot drift."""
    return int(PLUGIN_LANDLOCK_CANARY_POSITIVE_EXIT)


def _walk_fallback_rungs(
    rungs: Sequence[SandboxRung],
    *,
    cwd: Optional[str],
    deadline: float,
    version: Optional[str] = None,
    tails: Optional[List[Tuple[str, str]]] = None,
    jail_request: Optional[JailRequest] = None,
) -> Tuple[Optional[str], Tuple[Tuple[str, str], ...]]:
    """Walk ``rungs`` in order under one shared ``deadline`` (T3's walk table).

    Returns ``(selected rung id or None, walk record)``. Each rung probe gets
    only what is left of the deadline; a rung with nothing left is not started
    and is recorded ``unprobed``, which — like a probe with no exit status —
    stops the walk with no rung, so the uncontained rung is never rendered on
    exhausted time.

    ``version`` (2026-09-24): a rung whose ``removed_at`` the version reaches
    is not probed at all — recorded ``skipped`` — and the walk moves on. An
    unread version never skips. ``tails``, when given, receives ``(rung id,
    probe tail)`` for every rung whose probe ran.

    A wrapping rung (the plugin's Landlock jail, 2026-09-30) is probed by
    :func:`_walk_wrapped_rung` under ``jail_request`` — the grant the dispatch
    it gates would carry, so a write profile's positive control writes that
    dispatch's own target. ``None`` builds the read-only request for ``cwd``.
    """
    walk: List[Tuple[str, str]] = []
    for rung in rungs:
        if rung.probe_argv and rung_removed_for_version(rung, version):
            walk.append((rung.name, RUNG_SKIPPED))
            continue
        if not rung.probe_argv:
            # Nothing to measure (the uncontained rung): reaching it is taking it.
            walk.append((rung.name, RUNG_TAKEN))
            return rung.name, tuple(walk)
        if getattr(rung, "wrapper", None):
            # The plugin's own Landlock jail (plan codex-sandbox-unavailable
            # §6 F1 item 3, 2026-09-30): its probe is wrapped, seeded and
            # read with its own outcome table, under the same deadline.
            outcome, stop = _walk_wrapped_rung(
                rung, cwd=cwd, deadline=deadline, request=jail_request,
                tails=tails,
            )
            walk.append((rung.name, outcome))
            if outcome == RUNG_TAKEN:
                return rung.name, tuple(walk)
            if stop:
                return None, tuple(walk)
            continue
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            walk.append((rung.name, RUNG_UNPROBED))
            return None, tuple(walk)
        workdir = getattr(rung, "probe_workdir", None)
        with _probe_workdir(cwd, workdir, deadline) as created:
            if created is None:
                # The canary's directory could not be made writable *outside*
                # the sandbox, so a denied write inside it would prove nothing
                # about the boundary: nothing was measured, never a widening —
                # or the deadline went while waiting for the workdir's turn.
                ran_out = time.monotonic() >= deadline
                walk.append((rung.name, RUNG_UNPROBED if ran_out else RUNG_UNKNOWN))
                return None, tuple(walk)
            completed = _run_sandbox_probe(
                list(rung.probe_argv), cwd=cwd,
                timeout=max(deadline - time.monotonic(), 0.0),
            )
        if completed is None:
            ran_out = time.monotonic() >= deadline
            walk.append((rung.name, RUNG_UNPROBED if ran_out else RUNG_UNKNOWN))
            return None, tuple(walk)
        said = f"{completed.stdout}\n{completed.stderr}"
        if tails is not None:
            tails.append((rung.name, _rung_probe_tail(rung, completed)))
        if SANDBOX_CANARY_NOT_DENIED in said:
            # Checked first: a write that landed rejects the rung whatever the
            # exit status says.
            walk.append((rung.name, RUNG_REJECTED))
        elif completed.returncode == 0 and SANDBOX_CANARY_DENIED in said:
            # Exit 0 *and* the canary's own affirmative marker: the canary ran
            # to completion and its write was denied.
            walk.append((rung.name, RUNG_TAKEN))
            return rung.name, tuple(walk)
        elif completed.returncode == 0:
            # Exit 0 without the marker is not containment: the canary never
            # ran to completion (a CLI that printed usage and exited 0, a flag
            # accepted as a no-op). Nothing about a boundary was measured, so
            # the rung is not usable here — read like a probe the CLI did not
            # understand.
            walk.append((rung.name, RUNG_ABSENT))
        elif rung_probe_said_removed(rung, said):
            # Classified by its text, before the generic branches: this build
            # no longer supports the rung (codex 0.156.1's panic, exit 101 —
            # the same exit as constraint 2's unrelated panic).
            walk.append((rung.name, RUNG_RETIRED))
        elif _sandbox_probe_inconclusive(said):
            walk.append((rung.name, RUNG_ABSENT))
        else:
            walk.append((rung.name, RUNG_UNAVAILABLE))
    return None, tuple(walk)


def sandbox_verdict(
    provider: Any,
    profile: str,
    *,
    cwd: Optional[str] = None,
    timeout: Optional[float] = None,
    version: Optional[str] = None,
    walk_key: Optional[Tuple[str, ...]] = None,
    jail_request: Optional[JailRequest] = None,
    walk: bool = True,
) -> _probe_state.SandboxProbeResult:
    """One adapter's sandbox self-test (D6 step 3), plus its fallback walk.

    ``state`` is ``not-required`` when the adapter answers no command for this
    profile, ``ok`` on exit 0, ``unavailable`` on any other exit, and
    ``unknown`` when the command could not be run or did not finish. ``tail``
    is the redacted end of what the command printed — the ``bwrap:`` line, on
    the machine this was written for. Shared by the executor's preflight and
    ``multi_llm.py doctor`` so both read the same command the same way.

    On ``unavailable`` — and only then — the adapter's fallback ladder
    (``sandbox_fallback_rungs``) is walked in order (landlock rung,
    2026-09-22): a rung whose probe exits 0 **and** prints the canary's
    affirmative ``SANDBOX_CANARY_DENIED`` marker (its canary write was
    *denied*) is selected — exit 0 alone is not containment; a rejected
    canary, a real sandbox failure, a probe the CLI did not understand or an
    exit 0 without the marker moves on; a probe with no exit status
    stops the walk with no rung. ``timeout`` is the budget for the **whole**
    call, not per probe: the deadline is taken once on entry and every rung
    probe gets only what is left of it, so a two-probe ladder never costs more
    than one ``SANDBOX_PROBE_TIMEOUT_S``.

    ``version`` (2026-09-24) is the CLI version the walk is judged against: a
    rung whose ``removed_at`` it reaches is recorded ``skipped`` without a
    probe. ``None`` — what ``doctor`` passes — probes every rung, so a build
    that restores a rung is measured rather than assumed. ``walk_key``, when
    given, is the :data:`_SANDBOX_PROBE_CACHE` key the walk is shared under:
    a walk already recorded there is reused rather than re-probed, and a fresh
    one is stored there.

    ``jail_request`` (plan codex-sandbox-unavailable §6 F1, 2026-09-30) is the
    grant a wrapping rung's probe is prepared under; ``None`` is the read-only
    request for ``cwd`` (``kind`` = ``profile``). A write profile's request
    carries its scope and target, which the rung canary's positive control
    writes. ``walk=False`` runs the profile's own probe and walks no rung — a
    caller that already knows no rung can take this dispatch (the ``off``
    policy, a write scope the rung does not serve) spawns no rung probe.
    """
    try:
        argv = provider.sandbox_probe_command(profile)
    except Exception:  # noqa: BLE001 - a diagnostic may not break a preflight
        argv = None
    if not argv:
        return _probe_state.SandboxProbeResult("not-required", "")
    if timeout is None:
        # Resolved at call time so a test can shorten the module constant.
        timeout = SANDBOX_PROBE_TIMEOUT_S
    deadline = time.monotonic() + max(timeout, 0.0)
    completed = _run_sandbox_probe(list(argv), cwd=cwd, timeout=timeout)
    if completed is None:
        return _probe_state.SandboxProbeResult("unknown", "")
    tail = _failure_capture._redact_probe_tail(completed.stderr or completed.stdout, 500)
    if completed.returncode == 0:
        return _probe_state.SandboxProbeResult("ok", tail)
    if _sandbox_probe_inconclusive(f"{completed.stdout}\n{completed.stderr}"):
        # The CLI did not understand the probe (a build older than its
        # `sandbox` subcommand): nothing about the sandbox was learned.
        return _probe_state.SandboxProbeResult("unknown", tail)
    rungs = _fallback_rungs(provider, profile) if walk else ()
    if not rungs:
        return _probe_state.SandboxProbeResult("unavailable", tail)
    if jail_request is None:
        jail_request = JailRequest(
            repo_root=os.path.realpath(cwd or os.getcwd()), kind=profile,
        )
    shared = None
    if walk_key is not None:
        with _probe_state._SANDBOX_PROBE_LOCK:
            shared = _probe_state._SANDBOX_PROBE_CACHE.get(walk_key)
    if shared is not None:
        return _probe_state.SandboxProbeResult(
            "unavailable", tail, shared.rung, shared.walk, shared.rung_tails,
            version or "",
        )
    tails: List[Tuple[str, str]] = []
    rung, walked = _walk_fallback_rungs(
        rungs, cwd=cwd, deadline=deadline, version=version, tails=tails,
        jail_request=jail_request,
    )
    result = _probe_state.SandboxProbeResult(
        "unavailable", tail, rung, walked, tuple(tails), version or "",
    )
    stopped = any(outcome in (RUNG_UNPROBED, RUNG_UNKNOWN) for _, outcome in walked)
    if walk_key is not None and not stopped:
        # A walk that stopped on "nothing learned" is not shared: another
        # profile's probe, with its own budget, may yet get an answer.
        with _probe_state._SANDBOX_PROBE_LOCK:
            _probe_state._SANDBOX_PROBE_CACHE[walk_key] = result
    return result


def _probe_cwd(anchor: Optional[str]) -> Optional[str]:
    """Where the sandbox probe writes its byte: the repo root a dispatch pins.

    The anchor is the plan path (or directory) the run discovers its config
    from; its git root is the ``cwd`` every write dispatch is pinned to, so the
    probe asks the same question in the same place. Without a resolvable root
    the process cwd stands in — ``None`` here means "inherit".
    """
    start: Optional[str] = None
    if anchor:
        start = anchor if os.path.isdir(anchor) else (os.path.dirname(anchor) or ".")
    try:
        root = get_project_root_from_dir(start) if start else get_project_root_from_dir()
    except Exception:  # noqa: BLE001 - a cwd choice may never end a preflight
        root = None
    return root or None


def _sandbox_fallback_policy(
    provider: Any, profile: str, *, anchor: Optional[str]
) -> Optional[str]:
    """The adapter's resolved ``sandbox_fallback`` policy for ``profile``, or
    ``None`` when it declares none (or the read fails).

    ``getattr`` because a test's stand-in adapter may not declare the hook; a
    config read that raises is ``None`` — the narrow reading, and the one that
    matches every other gate's posture on a config it cannot read. ``anchor``
    is the plan path, so the key is read from the same
    ``.multi-llm/providers.yaml`` the dispatch's env and timeout come from.
    """
    hook = getattr(provider, "sandbox_fallback_policy", None)
    if not callable(hook):
        return None
    try:
        policy = hook(profile, anchor=anchor)
    except Exception:  # noqa: BLE001 - a config read may never end a preflight
        return None
    return policy if isinstance(policy, str) else None


def sandbox_fallback_rung(
    provider: Any, profile: str, rung_id: Optional[str], policy: Optional[str]
) -> Optional[SandboxRung]:
    """The declared rung ``rung_id`` if ``policy`` may take it for ``profile``.

    The policy half of both gates (this module's :func:`_detect_sandbox` and
    ``review_orchestrator_base.sandbox_refusal``), in one place: the profile is
    one of ``SANDBOX_FALLBACK_PROFILES`` (repeated here although the adapter
    answers ``None``/``()`` outside it — two places have to agree before a
    write profile could slip through), the walk selected a rung the adapter
    actually declares for that profile, and :func:`sandbox_rung_allowed` says
    the key permits it — ``auto`` any rung, ``contained`` a contained one only,
    ``off`` none. The probe verdict ``unavailable`` is the caller's gate.

    A write profile (plan step 3, user decision 2026-09-30) is answered
    separately: it reaches a rung its adapter declares in the write ladder, and
    only through :func:`write_rung_allowed` — a wrapping ``incidental``-grade
    rung (the plugin's Landlock jail) under ``auto``. Never the uncontained or
    the legacy ``landlock`` rung, under any policy word. Two places still have
    to agree (the adapter's write ladder and this gate) before a write
    dispatch widens.
    """
    if not rung_id:
        return None
    if profile in SANDBOX_WRITE_FALLBACK_PROFILES:
        for rung in _fallback_rungs(provider, profile):
            if rung.name == rung_id:
                return rung if write_rung_allowed(rung, policy) else None
        return None
    if profile not in SANDBOX_FALLBACK_PROFILES:
        return None
    for rung in _fallback_rungs(provider, profile):
        if rung.name == rung_id:
            return rung if sandbox_rung_allowed(rung, policy) else None
    return None


def sandbox_walk_note(
    verdict: "_probe_state.SandboxProbeResult",
    policy: Optional[str],
    *,
    provider_name: Optional[str] = None,
    rungs: Sequence[SandboxRung] = (),
) -> str:
    """One sentence on why an ``unavailable`` verdict took no rung, or ``""``.

    Said only where it changes what the reader should do: the walk stopped on
    a probe that produced no answer (fail-closed — a hung or unstartable rung
    probe refuses where the old single probe would have bypassed), or
    ``contained`` refused the uncontained rung the walk reached. ``off`` and an
    adapter with no ladder say nothing new: that refusal is the old one.

    Under ``contained``, given ``provider_name`` (and the declared ``rungs``
    for ``removed_at``), the sentence carries the same rung clause the
    ``[SANDBOX_BYPASSED]`` line does (:func:`sandbox_walk_clause`) — so a rung
    ``skipped`` by version or ``retired`` by its probe's panic is named with
    its version and probe tail, not hidden behind "no contained rung".
    """
    if policy in (None, SANDBOX_FALLBACK_OFF):
        return ""
    stopped = next(
        (
            (name, outcome) for name, outcome in verdict.walk
            if outcome in (RUNG_UNPROBED, RUNG_UNKNOWN)
        ),
        None,
    )
    if stopped is not None:
        return (
            f"fallback rung {stopped[0]!r} was {stopped[1]} (its probe gave no "
            f"answer), so no fallback rung was taken"
        )
    if policy == SANDBOX_FALLBACK_CONTAINED and verdict.walk:
        clause = ""
        if provider_name:
            try:
                clause = sandbox_walk_clause(
                    provider_name, verdict.walk, verdict.rung_tails,
                    verdict.version or None, rungs,
                )
            except Exception:  # noqa: BLE001 - a note may never end a preflight
                clause = ""
        return (
            f"sandbox_fallback={SANDBOX_FALLBACK_CONTAINED}: no contained "
            f"fallback rung is usable here"
            + (f" ({clause})" if clause else "")
            + ", and the uncontained one is never taken under that value"
        )
    return ""


def _sandbox_probe_lock(key: Tuple[str, ...]) -> threading.Lock:
    """The probe lock for one :data:`_SANDBOX_PROBE_CACHE` key, created once."""
    with _probe_state._SANDBOX_PROBE_LOCK:
        lock = _probe_state._SANDBOX_PROBE_KEY_LOCKS.get(key)
        if lock is None:
            lock = _probe_state._SANDBOX_PROBE_KEY_LOCKS[key] = threading.Lock()
        return lock


def _ladder_has_removed_at(provider: Any, profile: str) -> bool:
    """Whether ``provider``'s ladder for ``profile`` declares a rung that a
    version can retire — the only case the probe needs the CLI version."""
    return any(getattr(rung, "removed_at", None) for rung in _fallback_rungs(provider, profile))


def _sandbox_cli_version(
    provider_name: str, provider: Any, *, timeout: Optional[float] = None,
) -> str:
    """The CLI version the sandbox probe is keyed and judged on, or ``""``.

    The version preflight's own read (:data:`_VERSION_CACHE`) when it ran;
    otherwise one ``version_cmd`` spawn per provider per process, through the
    sandbox probe's runner (so the suite's guard on real CLIs covers it) and
    cached in :data:`_PROBE_VERSION_CACHE`. ``""`` when nothing could be read —
    and an unread version never skips a rung. ``timeout`` is an advisory
    reader's budget in place of :data:`SANDBOX_PROBE_TIMEOUT_S`; an empty
    read under it is not cached, so a dispatch reads the version itself.
    """
    if provider_name in _probe_state._VERSION_CACHE:
        # The preflight's read is settled either way: a recorded "unknown"
        # already spawned `version_cmd` once, and a second spawn would only
        # re-measure the same failure. It reads as an unread version here.
        known = _probe_state._VERSION_CACHE[provider_name]
        return "" if known == "unknown" else (known or "")
    with _probe_state._SANDBOX_PROBE_LOCK:
        if provider_name in _probe_state._PROBE_VERSION_CACHE:
            return _probe_state._PROBE_VERSION_CACHE[provider_name]
        lock = _probe_state._PROBE_VERSION_LOCKS.get(provider_name)
        if lock is None:
            lock = _probe_state._PROBE_VERSION_LOCKS[provider_name] = threading.Lock()
    with lock:
        # Double-checked: a sibling spec of this provider, probed concurrently
        # in another thread, may have read the version while this one waited.
        with _probe_state._SANDBOX_PROBE_LOCK:
            if provider_name in _probe_state._PROBE_VERSION_CACHE:
                return _probe_state._PROBE_VERSION_CACHE[provider_name]
        version = ""
        argv = list(getattr(provider, "version_cmd", ()) or ())
        if argv:
            completed = _run_sandbox_probe(
                argv, cwd=None,
                timeout=SANDBOX_PROBE_TIMEOUT_S if timeout is None else timeout,
            )
            if completed is not None:
                try:
                    version = provider.parse_version(completed.stdout, completed.stderr) or ""
                except Exception:  # noqa: BLE001 - a diagnostic may not break a preflight
                    version = ""
        if version or timeout is None:
            with _probe_state._SANDBOX_PROBE_LOCK:
                _probe_state._PROBE_VERSION_CACHE[provider_name] = version
        return version


def cached_sandbox_verdict(
    provider_name: str,
    provider: Any,
    profile: str,
    *,
    cwd: Optional[str],
    policy: Optional[str],
    jail_request: Optional[JailRequest] = None,
    timeout: Optional[float] = None,
) -> _probe_state.SandboxProbeResult:
    """Run — or recall — ``provider``'s sandbox self-test for ``profile``: the
    one per-process probe cache both lanes share (plan §3.6, 2026-09-24).

    ``timeout`` is an advisory reader's budget (:data:`ADVISORY_PROBE_BUDGET_S`,
    2026-10-02) for the version read, the standard probe and the walk
    together; a verdict it cut short (:func:`probe_budget_cut`) is returned
    but **not** cached, so the dispatch's own probe, under its own timeout,
    never inherits a reader's `unprobed`. A cached verdict is recalled
    whatever the budget: it was settled.

    Keyed by host, provider, profile, ``cwd``, the CLI version and the
    ``sandbox_fallback`` policy, and holding the whole
    :class:`SandboxProbeResult` — walk, rung probe tails and version included
    — so a cache hit prints the same line as the cold probe that filled it.
    The fallback walk is shared across profiles under its own key, so the
    fan-out (``generate``) and the executor (``agent-readonly``) in one process
    spawn one rung probe per codex version, not two. The version is read only
    for an adapter whose ladder declares a ``removed_at`` rung; at or above it
    the rung is not probed at all. A probe that raises reads ``unknown`` and is
    cached like any answer.

    Blocking — the fan-out hands it to a thread. The cache lock is held for
    the dict read and write only; the probe runs under a per-key lock, so two
    slots of one provider share a probe and a slow provider never holds up
    another (F5, 2026-09-17).

    Plan codex-sandbox-unavailable §6 F1 (2026-09-30):

    * ``off`` walks no rung: the policy takes none, so no rung probe spawns.
    * ``MULTI_LLM_CODEX_SKIP_RUNG``, when set, joins both keys, so a walk taken
      without the switch is never replayed with it (or the reverse).
    * For a write profile, ``jail_request`` is the dispatch's grant. Both the
      ``verdict`` and the ``walk`` key add its scope and — for ``plan-file``
      and ``tasks``, whose positive control writes it — its target; never a
      per-task declared path, a slot ``TMPDIR`` or an allow list. A write
      scope the rung does not serve (an unmapped kind: none) walks no rung.
      Read-only keys are unchanged.
    """
    host = _probe_state._current_host_id()
    version = (
        _sandbox_cli_version(provider_name, provider, timeout=timeout)
        if _ladder_has_removed_at(provider, profile) else ""
    )
    write = profile in SANDBOX_WRITE_FALLBACK_PROFILES
    scope = getattr(jail_request, "write_scope", None) if write else None
    target = (
        getattr(jail_request, "target", None)
        if write and scope in WRITE_SCOPES_ON_RUNG else None
    )
    try:
        switch = skip_rung_requested() or ""
    except ValueError:
        switch = "invalid"
    extra: Tuple[str, ...] = ()
    if write:
        extra += (f"scope={scope or ''}", f"target={target or ''}")
    if switch:
        extra += (f"skip={switch}",)
    key = ("verdict", host, provider_name, profile, cwd or "", version, policy or "") + extra
    with _probe_state._SANDBOX_PROBE_LOCK:
        cached = _probe_state._SANDBOX_PROBE_CACHE.get(key)
    if cached is not None:
        return cached
    with _sandbox_probe_lock(key):
        # Double-checked: a sibling slot on this key may have finished the
        # probe while this thread waited for the lock.
        with _probe_state._SANDBOX_PROBE_LOCK:
            cached = _probe_state._SANDBOX_PROBE_CACHE.get(key)
        if cached is not None:
            return cached
        walk = policy != SANDBOX_FALLBACK_OFF and not (
            write and scope not in WRITE_SCOPES_ON_RUNG
        )
        rungs = _fallback_rungs(provider, profile) if walk else ()
        walk_key = (
            ("walk", host, provider_name, cwd or "", version,
             ",".join(rung.name for rung in rungs)) + extra
            if rungs else None
        )
        kwargs: Dict[str, Any] = {}
        if write and jail_request is not None:
            kwargs["jail_request"] = jail_request
        if not walk:
            kwargs["walk"] = False
        if timeout is not None:
            kwargs["timeout"] = timeout
        try:
            if walk_key is not None or version:
                verdict = sandbox_verdict(
                    provider, profile, cwd=cwd, version=version or None,
                    walk_key=walk_key, **kwargs,
                )
            else:
                verdict = sandbox_verdict(provider, profile, cwd=cwd, **kwargs)
        except Exception:  # noqa: BLE001 - a diagnostic may never end a run
            verdict = _probe_state.SandboxProbeResult("unknown", "")
        if timeout is None or not probe_budget_cut(verdict):
            with _probe_state._SANDBOX_PROBE_LOCK:
                _probe_state._SANDBOX_PROBE_CACHE[key] = verdict
        return verdict


def probe_budget_cut(verdict: _probe_state.SandboxProbeResult) -> bool:
    """Whether ``verdict`` measured nothing for want of time: the standard
    probe did not finish (``unknown``), or the walk ran out of deadline
    (``unprobed``). Not a rung's ``unknown`` — a canary directory or seed
    that could not be prepared is a fact about the machine, not the clock."""
    if verdict.state == "unknown":
        return True
    return any(outcome == RUNG_UNPROBED for _, outcome in (verdict.walk or ()))


def rung_retirements(verdict: _probe_state.SandboxProbeResult) -> List[str]:
    """The rung ids ``verdict``'s walk found retired — ``skipped`` by version
    or ``retired`` by the probe's own text. Never a timeout, a canary-setup
    failure or any other outcome: those are reported as themselves."""
    return [
        name for name, outcome in (verdict.walk or ())
        if outcome in (RUNG_SKIPPED, RUNG_RETIRED)
    ]


def recorded_rung_retirements(provider_name: str) -> List[Tuple[str, str]]:
    """``[(rung id, version), …]`` this process's probe cache recorded as
    retired for ``provider_name`` — what ``announce_retired_rungs`` prints the
    once-per-run retirement line from, whatever the previous run recorded."""
    found: List[Tuple[str, str]] = []
    with _probe_state._SANDBOX_PROBE_LOCK:
        items = list(_probe_state._SANDBOX_PROBE_CACHE.items())
    for key, verdict in items:
        if len(key) < 3 or key[0] != "verdict" or key[2] != provider_name:
            continue
        for name in rung_retirements(verdict):
            pair = (name, verdict.version or "")
            if pair not in found:
                found.append(pair)
    return found


def sandbox_bypass_line(
    provider_name: str, verdict: _probe_state.SandboxProbeResult,
    rungs: Sequence[SandboxRung] = (),
) -> str:
    """The ``[SANDBOX_BYPASSED]`` line for ``verdict``: the fixed stem plus the
    rung clause naming each rung tried with its outcome and probe tail
    (``rungs`` — the adapter's declared ladder — supplies ``removed_at``)."""
    return sandbox_bypassed_notice_text(
        provider_name,
        sandbox_walk_clause(
            provider_name, verdict.walk, verdict.rung_tails,
            verdict.version or None, rungs,
        ),
    )


#: Plan codex-sandbox-unavailable §7 "Step 4: the refusal's wording in each
#: state" (2026-09-30): every ``sandbox_unavailable`` refusal leads with an
#: option that works on this host today (F6), before it says why Codex cannot
#: run here. ``{key}`` is the refused key — ``driver.subagent_runner`` for
#: editing jobs.
F6_LEAD = (
    "To run this now, set `{key}` to a runner that is not Codex (for example "
    "`claude-code:<model>`) in `.multi-llm/providers.yaml`."
)

#: The three rung sentences of the step-4 refusal, picked from the walk.
JAIL_KEPT_OFF_SENTENCE = "The plugin's Landlock jail does not take this job: {case}."
JAIL_UNAVAILABLE_SENTENCE = (
    "The plugin's Landlock jail cannot run here either: this kernel or "
    "container lacks Landlock ({note}). Only a system-level change gives Codex "
    "a sandbox here: the AppArmor or sysctl repair `multi_llm.py doctor` "
    "prints, which needs sudo."
)
JAIL_SELF_TEST_SENTENCE = (
    "The plugin's Landlock jail is present but failed its self-test ({what}). "
    "Run `multi_llm.py doctor`: its `plugin-landlock` row shows the probe "
    "result."
)


def _f6_key(key: str) -> str:
    """The ``providers.yaml`` key the F6 lead names: the refused ``driver.*``
    key without its layer note, else ``driver.subagent_runner`` (a recorded or
    task-level spec is still replaced there)."""
    base = (key or "").split(" (", 1)[0].strip()
    return base if base.startswith("driver.") else "driver.subagent_runner"


def _f6_lead(key: str) -> str:
    return F6_LEAD.format(key=_f6_key(key))


def _sandbox_unavailable_rejection(
    *,
    key: str,
    spec: str,
    tail: str,
    rung_sentence: str = "",
    note: str = "",
    trailer: str = "",
) -> _task_outcome.RunnerRejected:
    """The one ``sandbox_unavailable`` refusal text (plan §7 step 4): the F6
    lead; why Codex cannot run here (today's reason, then one rung sentence);
    the probe tail and the ladder note; "Nothing was dispatched." No sudo
    "Fix:" sentence — the AppArmor text lives in the reason, the
    Landlock-unavailable sentence and ``doctor``'s repair block only."""
    message = (
        f"{_f6_lead(key)} Refusing to dispatch: {key} is {spec!r} (reason: "
        f"sandbox_unavailable) — {_runner_selection._REASON_EXPLANATION['sandbox_unavailable']}. "
        + (f"{rung_sentence} " if rung_sentence else "")
        + f"Probe tail: {tail!r}. "
        + (trailer if trailer else "")
        + (f"Fallback ladder: {note}. " if note else "")
        + "Nothing was dispatched."
    )
    return _task_outcome.RunnerRejected(
        message, key=key, spec=spec, reason_code="sandbox_unavailable", detail=tail,
    )


def _jail_rung(provider: Any) -> Optional[SandboxRung]:
    """The adapter's wrapping rung (the plugin's Landlock jail), from either
    ladder, or ``None`` when it declares none."""
    for profile in (*SANDBOX_FALLBACK_PROFILES, *SANDBOX_WRITE_FALLBACK_PROFILES):
        for rung in _fallback_rungs(provider, profile):
            if getattr(rung, "wrapper", None):
                return rung
    return None


def _installed_cli_version(provider_name: str, verdict: _probe_state.SandboxProbeResult) -> str:
    """The CLI version the preflight or the probe read, or ``""``."""
    for value in (
        verdict.version, _probe_state._VERSION_CACHE.get(provider_name),
        _probe_state._PROBE_VERSION_CACHE.get(provider_name),
    ):
        if value and value != "unknown":
            return str(value)
    return ""


def _jail_versions_clause(provider_name: str, rung: SandboxRung, verdict: _probe_state.SandboxProbeResult) -> str:
    """" Codex X is installed, newer than Y …" when it is, else ``""``."""
    measured = (getattr(rung, "measured_through", None) or ("",))[0]
    installed = _installed_cli_version(provider_name, verdict)
    if measured and version_newer(installed, measured):
        return (
            f" Codex {installed} is installed, newer than {measured}, the "
            f"version the jail was measured through; a changed start-up write "
            f"list is the likely cause."
        )
    return ""


def _jail_rung_sentence(
    provider_name: str,
    provider: Any,
    profile: str,
    policy: Optional[str],
    verdict: _probe_state.SandboxProbeResult,
    write_scope: Optional[str],
) -> str:
    """The step-4 rung sentence for one refusal, picked from the walk's record
    (plan §7 "Step 4: the refusal's wording in each state").

    Kept off the rung (whatever the rung's state): a write profile with the
    step-3 opt-in off, a write dispatch with no grant, a scope the rung does
    not serve, a ``sandbox_fallback`` value that does not reach the rung, or
    ``MULTI_LLM_CODEX_SKIP_RUNG``. Otherwise the rung's own outcome: Landlock
    unavailable (the wrapper's exit 126 and its note), or a failed self-test
    (the failing control or path, and both codex versions when the installed
    one is newer than the rung was measured through). ``""`` for an adapter
    with no jail.
    """
    jail = _jail_rung(provider)
    if jail is None:
        return ""
    kept_off = JAIL_KEPT_OFF_SENTENCE.format
    if profile in SANDBOX_WRITE_FALLBACK_PROFILES:
        if not any(
            r.name == jail.name for r in _fallback_rungs(provider, profile)
        ):
            return kept_off(case=(
                "write jobs are not enabled on it (the step-3 opt-in is off)"
            ))
        if not write_scope:
            return kept_off(case=(
                "the write dispatch carries no write grant (no write scope)"
            ))
        if write_scope not in WRITE_SCOPES_ON_RUNG:
            return kept_off(case=(
                f"the {write_scope!r} write scope is not one the jail serves "
                f"({', '.join(WRITE_SCOPES_ON_RUNG)}); such a job needs a "
                f"non-Codex runner (F6, as above)"
            ))
    if policy == SANDBOX_FALLBACK_OFF:
        return kept_off(case=(
            f"providers.{provider_name}.sandbox_fallback=off reaches no "
            f"fallback rung"
        ))
    if policy == SANDBOX_FALLBACK_CONTAINED:
        return kept_off(case=(
            f"providers.{provider_name}.sandbox_fallback=contained does not "
            f"reach it: that value promises a real OS boundary, and the jail "
            f"stops stray writes, not the model"
        ))
    outcome = dict(verdict.walk or ()).get(jail.name)
    tail = dict(verdict.rung_tails or ()).get(jail.name, "")
    if outcome == RUNG_SKIPPED_BY_SWITCH:
        return kept_off(case=f"skipped by {SKIP_RUNG_ENV}")
    if outcome is None:
        return ""
    if outcome == RUNG_ABSENT and tail.startswith(
        landlock_dispatch.NOTE_PREFIX + "unavailable"
    ):
        note = tail[len(landlock_dispatch.NOTE_PREFIX):].strip()
        return JAIL_UNAVAILABLE_SENTENCE.format(note=note)
    if outcome in (RUNG_UNKNOWN, RUNG_UNPROBED):
        what = f"its probe gave no answer ({outcome})"
    elif outcome == RUNG_REJECTED:
        what = "a write or truncation its canary made was not denied"
    elif outcome == RUNG_ABSENT:
        # A required allow entry (the wrapper's own code, or a grant refused
        # before the spawn) names itself; otherwise the canary never finished.
        what = "" if tail else "the canary never reported a denied write"
    else:
        what = "an allowed write failed, or Codex did not start under the allow-list"
    if tail:
        what = f"{what}: {tail}" if what else tail
    return (
        JAIL_SELF_TEST_SENTENCE.format(what=what)
        + _jail_versions_clause(provider_name, jail, verdict)
    )


def _write_consent_bypass_line(
    provider_name: str,
    verdict: _probe_state.SandboxProbeResult,
    rungs: Sequence[SandboxRung],
    policy: Optional[str],
    write_scope: Optional[str],
) -> str:
    """The ``[SANDBOX_BYPASSED]`` line for an F5 write dispatch (plan step 6).

    Built here rather than through ``sandbox_bypassed_notice_text``, whose
    stem says "read-only phase": this is a WRITE phase, uncontained because
    the chat itself runs with ``danger-full-access`` and the plugin's jail
    could not take it. It keeps the marker, so counting ``[SANDBOX_BYPASSED]``
    still counts every uncontained dispatch."""
    clause = sandbox_walk_clause(
        provider_name, verdict.walk, verdict.rung_tails,
        verdict.version or None, rungs,
    )
    said = " ".join((verdict.tail or "").split())
    if len(said) > 160:
        said = said[:157].rstrip() + " …"
    text = f"{SANDBOX_BYPASSED_MARKER} {provider_name}: its own sandbox cannot start here"
    if said:
        text += f" ({said})"
    if clause:
        text += f"; {clause}"
    text += (
        f"; running this write phase (scope {write_scope or 'none'}) under "
        f"--sandbox danger-full-access because the chat itself runs with the "
        f"{HOST_POSTURE_FULL_ACCESS} sandbox posture ({HOST_SANDBOX_POSTURE_ENV}; "
        f"F5, plan step 6) and the plugin's Landlock jail could not take this "
        f"job, under providers.{provider_name}.sandbox_fallback="
        f"{policy or SANDBOX_FALLBACK_AUTO}: no OS boundary between the model's "
        f"shell and this machine"
    )
    return text


def _render_target(request: Optional[JailRequest]) -> Optional[str]:
    """The write target a notice names: the tasks directory under a dir rule,
    else the file; the repository root for ``repo-wide``; ``$HOME`` as ``~``."""
    if request is None:
        return None
    if request.write_scope == WRITE_SCOPE_REPO_WIDE:
        return landlock_dispatch.render_home(request.repo_root)
    shown = request.target_dir or request.target
    return landlock_dispatch.render_home(shown) if shown else None


def write_rung_notice(spec: str, jail_request: Optional[JailRequest]) -> Optional[str]:
    """The executor-lane ``[SANDBOX_INCIDENTAL]`` line for a write dispatch of
    ``spec`` that will run on the plugin's Landlock jail, or ``None``.

    Plan codex-sandbox-unavailable §6 F1 item 4 (2026-09-30): "a write
    dispatch on the rung prints that line before its batch starts". The
    scheduler prints it once before each batch on the rung; it is built with
    the same builder as every other ``[SANDBOX_INCIDENTAL]`` line, from what
    :func:`_detect_sandbox` recorded for this runner and scope, and names the
    scope and target from ``jail_request``. ``None`` for a batch on Codex's
    own sandbox, on no rung, or with no request.
    """
    if jail_request is None or not jail_request.write_scope:
        return None
    scope = jail_request.write_scope
    rung_id = _probe_state.sandbox_rung(spec, PROFILE_AGENT_WRITE, write_scope=scope)
    if not rung_id:
        return None
    parts = _probe_state._SANDBOX_NOTICE_PARTS.get(
        _probe_state._sandbox_decision_key(spec, PROFILE_AGENT_WRITE, scope, None)
    )
    if parts is None:
        return None
    provider_name, recorded_rung, policy, tail, clause = parts
    if recorded_rung != rung_id:
        return None
    provider = get_provider(provider_name)
    rung = next(
        (r for r in _fallback_rungs(provider, PROFILE_AGENT_WRITE) if r.name == rung_id),
        None,
    )
    if rung is None or not rung_is_incidental(rung):
        return None
    return sandbox_incidental_notice_text(
        provider_name, rung, policy, tail, walk_clause=clause,
        lane=INCIDENTAL_LANE_EXECUTOR, write_scope=scope,
        target=_render_target(jail_request),
    )


def repo_wide_write_refusal(
    spec: str,
    *,
    anchor: Optional[str],
    output_dir: Optional[str] = None,
    key: str = "driver.subagent_runner",
    budget_s: Optional[float] = ADVISORY_PROBE_BUDGET_S,
) -> Optional[str]:
    """Why a ``repo-wide`` write dispatch of ``spec`` (``implement``,
    ``apply-code-fixes``) would be refused on this host right now, or ``None``
    when it would run (racing-run issue #1's early warning, 2026-10-02).

    The same decision the dispatch takes — :func:`_detect_sandbox` with the
    ``agent-write`` profile and a repo-wide :class:`JailRequest` — so the
    answer is never a guess from recorded evidence: it runs the adapter's
    model-free probes once per process (the standard sandbox, then the rung
    walk) through the shared probe cache, and a runner with no sandbox probe
    (every adapter but codex) answers ``None`` with nothing spawned. The
    refusal text is the dispatch's own, led by F6 and ending in "Nothing was
    dispatched." Advisory: any failure other than the refusal reads as
    ``None``, because a warning that may be wrong is worse than none.

    Silent: :func:`_detect_sandbox` prints the preflight's own lines (the
    ``unknown`` note says "Dispatching anyway", which is wrong for a reader
    that dispatches nothing), so both streams are swallowed here; the only
    output is the warning the caller renders from the returned text. The
    decision is cached under the repo-wide scope key, so a read-only phase or
    a step-3 write phase that ends with the next-step block costs one rung
    probe for this scope on top of its own.

    ``budget_s`` (:data:`ADVISORY_PROBE_BUDGET_S`, 2026-10-02) bounds the
    probes: a hung or slow probe draws no warning, costs the reader at most
    the budget, and leaves nothing in the caches for a dispatch to inherit.
    ``None`` probes under the dispatch's own timeout.
    """
    provider_name = str(spec).partition(":")[0]
    try:
        # Through the module, at each call: tests patch `write_safety.resolve_repo_root`.
        repo_root = _write_safety.resolve_repo_root(anchor)
        request = JailRequest(
            repo_root=repo_root, kind="implement", write_scope=WRITE_SCOPE_REPO_WIDE,
            output_dir=os.path.realpath(output_dir) if output_dir else None,
        )
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            _detect_sandbox(
                provider_name, key=key, spec=str(spec), profile=PROFILE_AGENT_WRITE,
                anchor=anchor, jail_request=request, probe_budget_s=budget_s,
            )
    except _task_outcome.RunnerRejected as exc:
        return exc.message
    except Exception:  # noqa: BLE001 - advisory, never a failed status or init
        return None
    return None


def _uncontained_rung(provider: Any) -> Optional[SandboxRung]:
    """The adapter's uncontained rung (read ladder), for F5's consent check."""
    for rung in _fallback_rungs(provider, PROFILE_AGENT_READONLY):
        if rung.name == SANDBOX_RUNG_UNSANDBOXED:
            return rung
    return None


def _detect_sandbox(
    provider_name: str,
    *,
    key: str,
    spec: str,
    profile: str,
    anchor: Optional[str] = None,
    jail_request: Optional[JailRequest] = None,
    probe_budget_s: Optional[float] = None,
) -> str:
    """Run the adapter's model-free sandbox self-test once per host/spec/profile
    and refuse a runner whose own sandbox cannot run (D6 step 3).

    ``probe_budget_s`` marks an advisory read (``repo_wide_write_refusal``,
    2026-10-02): the probes run under that budget instead of
    :data:`SANDBOX_PROBE_TIMEOUT_S`, and a measurement the budget cut short
    answers ``unknown`` with nothing printed and nothing recorded — neither
    in the probe cache nor in the decision table — so the reader stays fast
    and silent while the dispatch, later or elsewhere, measures for itself.
    A settled measurement is cached and recorded as any other.

    Returns ``ok`` | ``unknown`` | ``not-required`` | ``bypassed`` | a rung id
    (``landlock``, ``plugin-landlock``); a non-zero exit with no permitted
    rung raises, because bubblewrap failing to start is a property of the
    machine — every sibling on this runner would fail identically, and a retry
    never changes it (the system-level AppArmor or sysctl repair ``multi_llm.py
    doctor`` prints is one way out, and needs sudo; a non-Codex runner is the
    other — the refusal leads with it, plan §7 step 4). A timeout or a command
    that could not run records ``unknown`` and dispatches, exactly like the
    nested-exec probe's inconclusive branch.

    A **rung** (D6 override 2026-09-17, landlock rung 2026-09-22) is the *only*
    way an ``unavailable`` verdict does not raise here: the adapter's ladder
    walk selected one, the adapter declares it for this profile, and the
    ``sandbox_fallback`` key permits it — a contained rung under ``auto`` or
    ``contained``, the uncontained and the incidental rung under ``auto``
    alone, nothing under ``off``. The selected rung's **id** is what gets
    recorded, so :func:`sandbox_rung` hands the dispatch the rung it must
    render.

    Plan codex-sandbox-unavailable (2026-09-30):

    * **Write profiles (steps 3 and 3b).** ``agent-write`` computes its policy
      too, and reaches exactly one rung, the plugin's Landlock jail, through
      :func:`write_rung_allowed` — ``auto`` alone, and only for a
      ``jail_request`` whose scope the rung serves (``plan-file``, ``tasks``
      and, since 2026-10-02, ``repo-wide``). A write dispatch with no scope
      walks no rung and is refused naming the case and F6. A failed rung
      probe is refused, never walked on. The decision key adds the scope.
    * **The incidental grade.** A rung of the ``incidental`` grade prints one
      ``[SANDBOX_INCIDENTAL]`` line (executor lane: no mode check, a warn-only
      home check), never ``[SANDBOX_BYPASSED]`` or ``[SANDBOX_FALLBACK]``.
    * **F5 (step 6).** Only when the plugin's jail could NOT take a write
      dispatch and the chat's own posture, read per call from this process's
      environment, is ``danger-full-access`` under ``auto``, the write takes
      the uncontained rung: a ``[SANDBOX_BYPASSED]`` line naming F5, and a
      decision word of its own stored under a key that carries the posture.
      Never under ``contained`` or ``off``, never ahead of the jail, never on a
      walk that measured nothing.
    * **Refusals (step 4)** lead with F6 and add one rung sentence picked from
      the walk.

    The measurement comes from the probe cache the fan-out shares
    (:func:`cached_sandbox_verdict`, 2026-09-24); the uncontained rung's line
    names every rung tried first, and a rung retired from this CLI build
    (skipped by version, or its probe's own panic text) gets the retirement
    line once per process.
    """
    provider = get_provider(provider_name)
    write = profile in SANDBOX_WRITE_FALLBACK_PROFILES
    scope = getattr(jail_request, "write_scope", None) if write else None
    consent = host_write_posture_consent() if write else None
    cache_key = _probe_state._sandbox_decision_key(spec, profile, scope, consent)
    if cache_key in _probe_state._SANDBOX_DECISIONS:
        return _probe_state._sandbox_state_word(_probe_state._SANDBOX_DECISIONS[cache_key])
    if consent is not None:
        # A rung taken without the posture stands with it too (the jail is
        # always preferred to F5); only the F5 word is posture-bound.
        recorded = _probe_state._SANDBOX_DECISIONS.get(
            _probe_state._sandbox_decision_key(spec, profile, scope, None)
        )
        if recorded and recorded not in _probe_state._PLAIN_SANDBOX_STATES:
            return _probe_state._sandbox_state_word(recorded)
    try:
        skip_rung_requested()
    except ValueError as exc:
        # Rejected at start-up, never silently ignored (F1 item 6).
        raise _task_outcome.RunnerRejected(
            f"Refusing to dispatch: {exc}. Nothing was dispatched.",
            key=SKIP_RUNG_ENV, spec=spec, reason_code="invalid_skip_rung",
        ) from None

    policy: Optional[str] = (
        _sandbox_fallback_policy(provider, profile, anchor=anchor)
        if profile in SANDBOX_FALLBACK_PROFILES or write else None
    )
    verdict = cached_sandbox_verdict(
        provider_name, provider, profile, cwd=_probe_cwd(anchor), policy=policy,
        timeout=probe_budget_s,
        **({"jail_request": jail_request} if write and jail_request is not None else {}),
    )
    state, tail = verdict.state, verdict.tail
    if probe_budget_s is not None and probe_budget_cut(verdict):
        return "unknown"
    if state == "unavailable":
        rung = None
        if not write or scope in WRITE_SCOPES_ON_RUNG:
            rung = sandbox_fallback_rung(provider, profile, verdict.rung, policy)
        if rung is not None:
            declared = _fallback_rungs(provider, profile)
            # One line per runner per process, on stdout beside the other
            # preflight lines, in the same words the fan-out prints — the
            # reader greps one marker across the run. `unknown` never reaches
            # here: no rung widens anything on a probe that was not read.
            if rung_is_incidental(rung):
                clause = sandbox_walk_clause(
                    provider_name, verdict.walk, verdict.rung_tails,
                    verdict.version or None, declared,
                )
                if write:
                    # A write dispatch's line is the scheduler's to print, once
                    # before EACH batch on the rung (`write_rung_notice`, the
                    # same builder); printing it here too would show batch 0
                    # twice. What it is built from is kept, path-free.
                    _probe_state._SANDBOX_NOTICE_PARTS[
                        _probe_state._sandbox_decision_key(spec, profile, scope, None)
                    ] = (provider_name, rung.name, policy, tail, clause)
                else:
                    print(
                        "[exec-subagents] "
                        + sandbox_incidental_notice_text(
                            provider_name, rung, policy, tail, walk_clause=clause,
                            lane=INCIDENTAL_LANE_EXECUTOR,
                        )
                    )
            elif rung.contained:
                print(
                    "[exec-subagents] "
                    + sandbox_fallback_notice_text(provider_name, rung, policy)
                )
            else:
                print(
                    "[exec-subagents] "
                    + sandbox_bypass_line(provider_name, verdict, declared)
                )
                _announce_executor_retirements(provider_name, provider, spec, profile, verdict)
            # A decision without the posture is valid with it too: stored
            # under the posture-free key (`sandbox_rung` looks there second).
            _probe_state._SANDBOX_DECISIONS[
                _probe_state._sandbox_decision_key(spec, profile, scope, None)
            ] = rung.name
            return _probe_state._sandbox_state_word(rung.name)
        # F5 serves the step-3 scopes alone (`WRITE_SCOPES_BY_CONSENT`):
        # repo-wide edits (`apply-code-fixes`, `implement`) run on the jail
        # since step 3b and never reach the uncontained rung by consent,
        # whatever the chat's posture (the safer reading, 2026-10-02).
        if write and consent is not None and scope in WRITE_SCOPES_BY_CONSENT:
            stopped = any(
                outcome in (RUNG_UNPROBED, RUNG_UNKNOWN)
                for _, outcome in (verdict.walk or ())
            )
            floor = _uncontained_rung(provider)
            if not stopped and write_consent_allows(floor, policy, consent):
                print(
                    "[exec-subagents] "
                    + _write_consent_bypass_line(
                        provider_name, verdict, _fallback_rungs(provider, profile),
                        policy, scope,
                    )
                )
                _probe_state._SANDBOX_DECISIONS[cache_key] = _probe_state.SANDBOX_DECISION_WRITE_BY_CONSENT
                return _probe_state.SANDBOX_STATE_BYPASSED
    if state == "unavailable":
        declared = _fallback_rungs(provider, profile)
        if policy == SANDBOX_FALLBACK_CONTAINED:
            # The operator who opted into containment is the one who sees this
            # runner refused; a retired rung is named once per process here
            # too, worded as the refusal it is (plan §3.2).
            _announce_executor_retirements(
                provider_name, provider, spec, profile, verdict, refused=True,
            )
        note = sandbox_walk_note(
            verdict, policy, provider_name=provider_name, rungs=declared,
        )
        raise _sandbox_unavailable_rejection(
            key=key, spec=spec, tail=tail,
            rung_sentence=_jail_rung_sentence(
                provider_name, provider, profile, policy, verdict, scope,
            ),
            note=note,
        )
    if state == "unknown":
        print(
            f"multi-llm warning: the sandbox self-test for {spec} ({profile}) "
            f"could not be read within {SANDBOX_PROBE_TIMEOUT_S:.0f}s — recording "
            f"sandbox 'unknown'. Dispatching anyway; a broken sandbox will land on "
            f"the D3k ladder as sandbox_unavailable (rung 1).",
            file=sys.stderr,
        )
    _probe_state._SANDBOX_DECISIONS[cache_key] = state
    return state


def _announce_executor_retirements(
    provider_name: str, provider: Any, spec: str, profile: str,
    verdict: _probe_state.SandboxProbeResult,
    *,
    refused: bool = False,
) -> None:
    """Print the retirement line once per process per provider and version
    for a rung ``verdict``'s walk found retired (plan §3.2). The fan-out's
    twin is ``review_orchestrator_base.announce_retired_rungs``. ``refused``
    words it for the ``contained`` refusal path, where the run did not fall
    to the uncontained rung."""
    for name in rung_retirements(verdict):
        marker = f"{provider_name}|{name}|{verdict.version or ''}"
        if marker in _probe_state._RETIREMENTS_ANNOUNCED:
            continue
        declared = next(
            (r for r in _fallback_rungs(provider, profile) if r.name == name), None,
        )
        if declared is None:
            continue
        _probe_state._RETIREMENTS_ANNOUNCED.add(marker)
        print(
            "[exec-subagents] "
            + sandbox_rung_retired_notice(
                provider_name, spec, declared, measured=True,
                version=verdict.version or None, refused=refused,
            )
        )
