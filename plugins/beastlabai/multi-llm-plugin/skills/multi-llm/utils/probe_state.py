"""What this process has learned about its runners, kept once per process.

The preflight's caches (version, auth, model, nested exec), the sandbox
decisions and the one sandbox probe cache both lanes share, with their
locks, the jail summary lines, and the ``reset_*`` functions the tests
call. Every cache is registered with ``process_state``.
:func:`sandbox_rung` and :func:`sandbox_bypassed` read a recorded decision;
the sandbox walk (``sandbox_walk``) and the preflight write them. It
imports none of the executor's other modules.

``utils.subagent_executor`` re-exports every name defined here for reading
only: patch one here, never through the executor
(docs/development/delegation.md#where-the-executors-helpers-live).
"""

from __future__ import annotations

import sys
import threading
from typing import Any, Dict, List, NamedTuple, Optional, Set, Tuple

from . import host_capabilities as caps
from .process_state import process_cache
from . import landlock_dispatch
from .providers.base import (
    SANDBOX_WRITE_FALLBACK_PROFILES,
    WritePostureConsent,
    host_write_posture_consent,
    SANDBOX_RUNG_UNSANDBOXED,
)


#: Process-local version cache: detected once per *distinct* runner, never per
#: dispatch (D3m).
_VERSION_CACHE: Dict[str, str] = process_cache("utils.probe_state._VERSION_CACHE")

#: The same, for the D3c auth probe: ``ok`` | ``unknown`` | ``not-required`` |
#: ``config``, keyed ``<provider>|<needs-credentials 0/1>|<profile>|<model
#: prefix>|<hermetic/plain>`` — NOT by bare provider name (D3 step 2): one
#: process holding both ``opencode/big-pickle`` and ``openrouter/deepseek/…``
#: would otherwise serve one's verdict to the other. The profile joined the key
#: with T8.13 (the probe runs under that profile's dispatch env), and the model
#: prefix and hermeticity with T8.4 (whether a config declares the provider
#: depends on both). A failed probe is never cached — it raises, and the run
#: ends.
_AUTH_CACHE: Dict[str, str] = process_cache("utils.probe_state._AUTH_CACHE")

#: The same, for the D3c nested-exec verdict, keyed by ``<host id>|<runner spec>``
#: rather than by provider: the question is about the *pair*, and a host that
#: denies one runner's egress may hand another its own bundled CLI. A denial is
#: never cached either — it raises.
_NESTED_CACHE: Dict[str, str] = process_cache("utils.probe_state._NESTED_CACHE")

#: The same, for the D3 step 3 catalog leg: ``ok`` | ``unknown`` per
#: ``<provider>|<hermetic on/off>|<config-content digest>|<normalized model>``
#: — not provider+model, because the effective configuration changes the
#: answer, and a hermetic and a non-hermetic slot in one process must not share
#: a verdict. A refusal is never cached — it raises.
_MODEL_CACHE: Dict[str, str] = process_cache("utils.probe_state._MODEL_CACHE")

#: The executor's per-runner sandbox **decision** for the D6 self-test: ``ok``
#: | ``unknown`` | ``not-required`` | a **rung id** per ``<host id>|<runner
#: spec>|<profile>``. Not a probe cache — the measurement lives in the one
#: probe cache both lanes share (:data:`_SANDBOX_PROBE_CACHE`, 2026-09-24);
#: this records only what the preflight *decided* from it, so
#: :func:`sandbox_rung` can hand the rung id to every dispatch of that runner
#: under that profile — the id, never a bool, because the dispatch must render
#: *that* rung and a bool cannot say which. A refusal is never recorded — it
#: raises. A rung id (``landlock``, ``unsandboxed``) is the one
#: ``unavailable`` that did not raise. Recorded so the notice prints once per
#: runner rather than once per batch.
_SANDBOX_DECISIONS: Dict[str, str] = process_cache("utils.probe_state._SANDBOX_DECISIONS")

#: Guards :data:`_SANDBOX_PROBE_CACHE` for the dict read and write only; the
#: probe itself runs under a per-key lock (:func:`_sandbox_probe_lock`), so one
#: provider's slow probe never holds up another provider's slot (F5,
#: 2026-09-17). A ``threading.Lock``: the fan-out runs the blocking probe in a
#: worker thread, and one process may drive more than one event loop. It also
#: guards :data:`_SANDBOX_PROBE_KEY_LOCKS` and the probe's version read below.
_SANDBOX_PROBE_LOCK = threading.Lock()


def _sandbox_probe_running() -> bool:
    """Whether a sandbox probe or its version read is under way: the worker
    holds one of the per-key locks below and writes its answer to these caches
    when done. Read under :data:`_SANDBOX_PROBE_LOCK`, which every insert into
    the per-key tables holds; the suite's cache reset waits on it."""
    return any(
        lock.locked()
        for table in (_SANDBOX_PROBE_KEY_LOCKS, _PROBE_VERSION_LOCKS)
        for lock in table.values()
    )


#: The **one** per-process sandbox probe cache (plan §3.6, 2026-09-24),
#: replacing the fan-out's ``_FANOUT_SANDBOX_CACHE`` and this module's old
#: verdict-word cache, which cached separately and so could probe one codex
#: version twice. Values are the whole :class:`SandboxProbeResult` — walk,
#: per-rung probe tails and CLI version included — so a cache hit renders the
#: same ``[SANDBOX_BYPASSED]`` line as the cold probe that filled it. Two key
#: shapes, both tuples:
#:
#: * ``("verdict", host, provider, profile, cwd, version, policy)`` — one
#:   profile's probe plus its walk, as :func:`cached_sandbox_verdict` returns it;
#: * ``("walk", host, provider, cwd, version, rung ids)`` — the fallback walk
#:   alone. The rung probes do not depend on the profile (``generate`` and
#:   ``agent-readonly`` declare the same ladder), so the fan-out and the
#:   executor share **one** rung probe per codex version; the profiles' own
#:   probes differ (one writes a byte, the other does not) and stay per profile.
_SANDBOX_PROBE_CACHE: Dict[Tuple[str, ...], "SandboxProbeResult"] = process_cache(
    "utils.probe_state._SANDBOX_PROBE_CACHE",
    lock=_SANDBOX_PROBE_LOCK, busy=_sandbox_probe_running,
)
_SANDBOX_PROBE_KEY_LOCKS: Dict[Tuple[str, ...], threading.Lock] = process_cache(
    "utils.probe_state._SANDBOX_PROBE_KEY_LOCKS",
    lock=_SANDBOX_PROBE_LOCK, busy=_sandbox_probe_running,
)

#: The CLI version the sandbox probe keys on, per provider, when the version
#: preflight (:data:`_VERSION_CACHE`) has not already read it. Read only for an
#: adapter whose ladder declares a ``removed_at`` rung, so every other adapter
#: spawns nothing extra.
_PROBE_VERSION_CACHE: Dict[str, str] = process_cache(
    "utils.probe_state._PROBE_VERSION_CACHE",
    lock=_SANDBOX_PROBE_LOCK, busy=_sandbox_probe_running,
)
#: One lock per provider around that version spawn, so two specs of one
#: provider probed concurrently (``asyncio.to_thread``) spawn it once.
_PROBE_VERSION_LOCKS: Dict[str, threading.Lock] = process_cache(
    "utils.probe_state._PROBE_VERSION_LOCKS",
    lock=_SANDBOX_PROBE_LOCK, busy=_sandbox_probe_running,
)

#: ``<provider>|<version>`` pairs whose retirement line (a contained rung
#: measured unavailable from this build) this process already printed.
_RETIREMENTS_ANNOUNCED: Set[str] = process_cache(
    "utils.probe_state._RETIREMENTS_ANNOUNCED", set
)

#: What :func:`_detect_sandbox` returns (and ``preflight_runner`` records as
#: ``info["sandbox"]``) for the uncontained rung — the word it has always been.
#: The decision record (:data:`_SANDBOX_DECISIONS`) stores the rung id; this word is derived from exactly
#: :data:`SANDBOX_RUNG_UNSANDBOXED` and nothing else.
SANDBOX_STATE_BYPASSED = "bypassed"

#: The recorded states that are **not** a rung id.
_PLAIN_SANDBOX_STATES = frozenset({"ok", "unknown", "not-required"})

#: The decision word for plan step 6 (F5, user decision 2026-09-30): a WRITE
#: dispatch on the uncontained rung, taken only because the chat itself runs
#: with the ``danger-full-access`` posture and the plugin-landlock rung could
#: not take the dispatch. Its own word, never the rung id, so nothing that
#: replays a decision can mistake it for a read phase's bypass; it is stored
#: only under a key that carries the posture (:func:`_sandbox_decision_key`),
#: so a later call without that posture never finds it. :func:`sandbox_rung`
#: hands the dispatch ``unsandboxed`` for it.
SANDBOX_DECISION_WRITE_BY_CONSENT = "unsandboxed-by-consent"

#: Per decision key, what the executor-lane ``[SANDBOX_INCIDENTAL]`` line of a
#: write dispatch on the plugin-landlock rung is built from — ``(provider,
#: rung id, policy, standard probe tail, walk clause)`` — so the scheduler can
#: print it before each batch (:func:`write_rung_notice`). No path: the write
#: target is rendered from the caller's request at print time.
_SANDBOX_NOTICE_PARTS: Dict[str, Tuple[str, str, Optional[str], str, str]] = process_cache(
    "utils.probe_state._SANDBOX_NOTICE_PARTS"
)

#: Lines the run's closing summary repeats (F1 item 6 and Limits): every
#: ``[JAIL_DENIED]`` and ``[CODEX_HOME_CHECK]`` line this process printed,
#: plus the trust-entry notes rendered only when the summary prints
#: (``landlock_dispatch.TrustEntriesNote``). Per process, like the probe
#: cache; :func:`jail_summary_lines` renders it and :func:`run_tasks` prints
#: the ones its own batch added (counted by :func:`jail_summary_count`).
_JAIL_SUMMARY_LOCK = threading.Lock()
_JAIL_SUMMARY_LINES: List[Any] = process_cache(
    "utils.probe_state._JAIL_SUMMARY_LINES", list, lock=_JAIL_SUMMARY_LOCK
)

#: How many jailed codex children of this process are live, and how many have
#: started, so a ``[CODEX_HOME_CHECK]`` line can say how many *other* children
#: could also have made the change it reports.
_JAILED_CHILDREN = {"live": 0, "started": 0}


def _sandbox_decision_key(
    spec: str,
    profile: str,
    write_scope: Optional[str] = None,
    consent: Optional[WritePostureConsent] = None,
) -> str:
    """``<host>|<spec>|<profile>``, plus ``|<scope>`` for a write profile that
    carries one, plus ``|<posture>`` when the chat's F5 consent is present.

    The scope keeps a ``plan-file`` decision from ever being replayed for a
    ``repo-wide`` dispatch of the same runner; the posture keeps an F5
    decision from ever being replayed for a call without the posture (it is
    read per call from ``os.environ``, plan step 6). Read-only keys are
    unchanged. Never a path.
    """
    key = f"{_current_host_id()}|{spec}|{profile}"
    if profile in SANDBOX_WRITE_FALLBACK_PROFILES:
        if write_scope:
            key += f"|{write_scope}"
        if consent is not None:
            key += f"|{consent.posture}"
    return key


def sandbox_rung(
    spec: str, profile: str, write_scope: Optional[str] = None
) -> Optional[str]:
    """The fallback rung id the preflight recorded for this runner and profile,
    or ``None``.

    Read by :func:`dispatch_task` (and the dry-run preview) to hand
    ``sandbox_fallback=<rung id>`` to the argv build, which renders that rung.
    Strictly the cache, never a fresh probe or a config read: the decision was
    taken once, in :func:`_detect_sandbox`, with every gate in hand, and a
    dispatch may only replay it. A runner the preflight never saw (or saw
    under another profile) is ``None`` and renders the argv it always did.

    ``write_scope`` (plan step 3, 2026-09-30) selects a write profile's
    decision: one taken for ``plan-file`` is never replayed for ``repo-wide``.
    An F5 decision (plan step 6) is found only while the chat's
    ``danger-full-access`` posture is in this process's environment, and is
    handed out as ``unsandboxed``.
    """
    consent = (
        host_write_posture_consent()
        if profile in SANDBOX_WRITE_FALLBACK_PROFILES else None
    )
    keys = [_sandbox_decision_key(spec, profile, write_scope, consent)]
    if consent is not None:
        # A decision taken without the posture (the plugin-landlock rung, say)
        # is valid with it too; the reverse never holds, and the F5 word is
        # only ever stored under a key that carries the posture.
        keys.append(_sandbox_decision_key(spec, profile, write_scope, None))
    for key in keys:
        recorded = _SANDBOX_DECISIONS.get(key)
        if not recorded or recorded in _PLAIN_SANDBOX_STATES:
            continue
        if recorded == SANDBOX_DECISION_WRITE_BY_CONSENT:
            return SANDBOX_RUNG_UNSANDBOXED if consent is not None else None
        return recorded
    return None


def jail_summary_count() -> int:
    """How many entries the closing summary holds so far: the mark a caller
    takes before its batch and hands :func:`jail_summary_lines` after it."""
    with _JAIL_SUMMARY_LOCK:
        return len(_JAIL_SUMMARY_LINES)


def jail_summary_lines(start: int = 0) -> List[str]:
    """Every ``[JAIL_DENIED]`` / ``[CODEX_HOME_CHECK]`` line this process
    recorded from entry ``start`` on, in order, for a run's closing summary
    (plan F1 item 6, Limits). Trust-entry notes are rendered now and merged
    per home (``landlock_dispatch.render_summary_entries``): a table gone
    again by now is left out."""
    with _JAIL_SUMMARY_LOCK:
        entries = list(_JAIL_SUMMARY_LINES[start:])
    return landlock_dispatch.render_summary_entries(entries)


def _record_jail_line(line: Any, *, echo: bool = True) -> None:
    """Print ``line`` (the run log) and keep it for the closing summary."""
    with _JAIL_SUMMARY_LOCK:
        _JAIL_SUMMARY_LINES.append(line)
    if echo:
        print(f"[exec-subagents] {line}")


def sandbox_bypassed(spec: str, profile: str) -> bool:
    """Whether the preflight recorded the **uncontained** rung for this runner
    and profile — rung 2 exactly, never a contained rung."""
    return sandbox_rung(spec, profile) == SANDBOX_RUNG_UNSANDBOXED


def _sandbox_state_word(recorded: str) -> str:
    """The ``info["sandbox"]`` word for a cached state: ``bypassed`` for the
    uncontained rung (unchanged since D6) — an F5 write decision included,
    since that is the same rung — the recorded value otherwise."""
    if recorded in (SANDBOX_RUNG_UNSANDBOXED, SANDBOX_DECISION_WRITE_BY_CONSENT):
        return SANDBOX_STATE_BYPASSED
    return recorded


# The suite empties every cache above around each test (``process_state.reset_all``,
# tests/conftest.py); these resets serve a test that needs a cold cache mid-test.
def reset_version_cache() -> None:
    """Clear the per-process runner-version, auth, catalog, nested-exec and
    sandbox caches (tests)."""
    _VERSION_CACHE.clear()
    _AUTH_CACHE.clear()
    _NESTED_CACHE.clear()
    _MODEL_CACHE.clear()
    reset_sandbox_cache()


def reset_sandbox_cache() -> None:
    """Clear the per-process sandbox probe cache and decisions (tests)."""
    _SANDBOX_DECISIONS.clear()
    _SANDBOX_NOTICE_PARTS.clear()
    with _JAIL_SUMMARY_LOCK:
        _JAIL_SUMMARY_LINES.clear()
    _SANDBOX_PROBE_CACHE.clear()
    _SANDBOX_PROBE_KEY_LOCKS.clear()
    _PROBE_VERSION_CACHE.clear()
    _PROBE_VERSION_LOCKS.clear()
    _RETIREMENTS_ANNOUNCED.clear()


def reset_auth_cache() -> None:
    """Clear the per-process runner-auth cache (tests)."""
    _AUTH_CACHE.clear()


def reset_model_cache() -> None:
    """Clear the per-process model-catalog cache (tests)."""
    _MODEL_CACHE.clear()


def reset_nested_exec_cache() -> None:
    """Clear the per-process nested-exec cache (tests)."""
    _NESTED_CACHE.clear()


class SandboxProbeResult(NamedTuple):
    """What :func:`sandbox_verdict` measured: ``(state, tail, rung, walk, rung_tails, version)``.

    A NamedTuple, not a widened plain tuple, so a stale two-value unpack
    (``state, tail = sandbox_verdict(...)``) *raises* instead of silently
    dropping the rung — the rung is what makes the dispatch render the right
    argv, and losing it quietly re-opens the skip-the-rewrite failure.

    * ``state`` — the profile's own probe: ``ok`` | ``unavailable`` |
      ``unknown`` | ``not-required``, exactly as before the ladder.
    * ``tail`` — the redacted end of what that probe printed.
    * ``rung`` — the id of the fallback rung the walk selected, or ``None``.
      Only ever set beside ``state == "unavailable"``; whether the rung may be
      *taken* is still the gates' decision (the ``sandbox_fallback`` key).
    * ``walk`` — ``((rung id, outcome), …)`` for every rung the walk reached,
      in order, outcomes from the ``RUNG_*`` constants. ``()`` when no walk
      ran. It is how a reader tells a rung that was measured and rejected from
      one the deadline never let anyone measure (``unprobed``).
    * ``rung_tails`` — ``((rung id, redacted probe tail), …)`` for every rung
      whose probe actually ran (2026-09-24), so the ``[SANDBOX_BYPASSED]`` line
      can say why a contained rung was not taken — and say it identically on a
      cache hit. A rung ``skipped`` by version has no tail.
    * ``version`` — the CLI version the walk was judged against (``""`` when
      unread): what the line and the retirement notice name.
    """

    state: str
    tail: str
    rung: Optional[str] = None
    walk: Tuple[Tuple[str, str], ...] = ()
    rung_tails: Tuple[Tuple[str, str], ...] = ()
    version: str = ""


def _current_host_id() -> str:
    """The host id the sandbox cache is keyed under (``unknown-host`` off-data)."""
    resolved = _host_nested_exec()
    return resolved[0] if resolved else "unknown-host"


def _host_nested_exec() -> Optional[Tuple[str, Dict[str, str], str]]:
    """``(host_id, {leg: state}, notes)`` for the running host, or ``None``.

    ``None`` means the capability data could not be read at all (an unknown
    host, missing data). That is the one
    case where the nested-exec leg is skipped outright rather than probed: a
    throwaway dispatch is a real billed turn, and "I do not know which host I am
    on" is not a reason to spend one — nor to refuse, since the legs it would
    have answered are exactly the ones the reactive D3k ladder still catches.
    """
    try:
        host_id = caps.resolve_host_id(sys.argv[1:])
        declared = caps.nested_exec(host_id)
    except Exception:  # pragma: no cover - unknown host / missing data
        return None
    notes = str(declared.pop("notes", "") or "").strip()
    legs = {
        leg: str(declared.get(leg) or "unknown")
        for leg in caps.NESTED_EXEC_LEGS
    }
    return host_id, legs, notes
