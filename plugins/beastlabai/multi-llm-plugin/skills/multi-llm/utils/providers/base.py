"""Base protocol for LLM CLI providers."""

import inspect
import os
import re
import shutil
import subprocess
import sys
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import (
    Any,
    Callable,
    Collection,
    Dict,
    FrozenSet,
    Iterable,
    List,
    Mapping,
    Optional,
    Pattern,
    Sequence,
    Set,
    Tuple,
)

# The status vocabulary is the retry ladder's, never a second copy of it (§7.2).
# The dependency runs one way only: this module may import the ladder, and the
# ladder must stay free of provider imports — it reads an adapter's retry
# envelope *structurally*, through a Protocol, for exactly that reason.
try:  # pragma: no cover - import shim mirrors the rest of utils/
    from ..retry_ladder import (
        STATUS_AUTH_FAILED,
        STATUS_CONTEXT_LENGTH_EXCEEDED,
        STATUS_RATE_LIMITED,
        STATUS_RUNNER_ERROR,
        STATUS_SPAWN_FAILED,
        STATUS_TIMEOUT,
    )
except ImportError:  # pragma: no cover - direct-script import shim
    from utils.retry_ladder import (
        STATUS_AUTH_FAILED,
        STATUS_CONTEXT_LENGTH_EXCEEDED,
        STATUS_RATE_LIMITED,
        STATUS_RUNNER_ERROR,
        STATUS_SPAWN_FAILED,
        STATUS_TIMEOUT,
    )

#: The three invocation profiles (D3e). ``generate`` is today's callee path (no
#: tools, no workspace); ``agent-readonly`` is an agentic invocation with writes
#: denied by the runner's own sandbox/permission mechanism and is what every
#: read/analyze subagent runs under; ``agent-write`` is the implement/apply path.
PROFILE_GENERATE = "generate"
PROFILE_AGENT_READONLY = "agent-readonly"
PROFILE_AGENT_WRITE = "agent-write"

# ---------------------------------------------------------------------------
# The sandbox fallback (D6, 2026-09-17) — the one dispatch-time override
# ---------------------------------------------------------------------------

#: ``providers.<name>.sandbox_fallback`` — the closed policy set. ``auto`` is
#: the shipped default: a runner whose own OS sandbox cannot start still runs
#: its **read-only** dispatches, without that sandbox, rather than being left
#: out of the fan-out — the footing every adapter with no OS sandbox of its own
#: (cursor-agent, pi, claude-code, muse under ``--disable-sandbox``) has always
#: had in the same phases. ``off`` restores the refusal: the runner is left out
#: until the repair ``multi_llm.py doctor`` prints is installed. Neither value
#: touches a write profile. It is a standing property of the machine, which is
#: why it is a config key and never a CLI flag or an ``unattended`` row: the
#: decision does not vary per run. The plugin makes no claim about what is
#: outside the process (measured 2026-09-17: the Claude Code Bash tool's
#: ``mnt``/``net``/``user``/``pid`` namespaces are identical to the outer
#: terminal's), which is why the default is spelled ``auto`` and not a word
#: that would assert a boundary nobody checked.
SANDBOX_FALLBACK_OFF = "off"
SANDBOX_FALLBACK_AUTO = "auto"
#: The third value (landlock rung, 2026-09-22): *yes to any real boundary, no to
#: the bypass, ever*. A ``contained`` rung (:attr:`SandboxRung.contained`) is
#: reached under ``auto`` **or** ``contained``; an uncontained one under
#: ``auto`` alone; ``off`` reaches no rung at all, which is the refusal it
#: always meant. When every contained rung is gone (``use_legacy_landlock``
#: removed upstream) ``contained`` degrades to that refusal, never to the
#: bypass the operator opted out of.
SANDBOX_FALLBACK_CONTAINED = "contained"
SANDBOX_FALLBACK_POLICIES: Tuple[str, ...] = (
    SANDBOX_FALLBACK_OFF,
    SANDBOX_FALLBACK_AUTO,
    SANDBOX_FALLBACK_CONTAINED,
)

#: The only profiles the fallback may ever widen. ``generate`` is the review/ask
#: fan-out (review-plan, review-tasks, review-code, ask — every one consumes a
#: document); ``agent-readonly`` is every executor READ kind (validation,
#: revalidation, consolidation, salvage, task generation, the human-decision
#: judge). ``agent-write`` is absent by construction and stays absent: a runner
#: with no honoured write sandbox is refused for ``agent-write`` today, and the
#: fallback exists to keep read-only work flowing, not to hand a model
#: pre-approved edit access with the boundary removed. An adapter's
#: :meth:`LLMProvider.apply_sandbox_fallback` raises on anything outside this
#: tuple rather than rendering it.
SANDBOX_FALLBACK_PROFILES: Tuple[str, ...] = (PROFILE_GENERATE, PROFILE_AGENT_READONLY)

#: What every artifact of a bypassed slot says, verbatim — the fan-out's
#: stdout line, the executor's preflight line, ``models_served`` in
#: ``.status.json``, the report label. One string so the reader can grep one
#: marker across the run, the way ``[SANDBOX_UNAVAILABLE]`` reads today.
SANDBOX_BYPASSED_MARKER = "[SANDBOX_BYPASSED]"

#: The marker for a slot that ran on a **contained** fallback rung — a real OS
#: boundary that is not the adapter's default one. Never ``[SANDBOX_BYPASSED]``:
#: such a slot is sandboxed, and saying otherwise is the mislabel the rung id
#: exists to prevent.
SANDBOX_FALLBACK_MARKER = "[SANDBOX_FALLBACK]"

#: The marker for the once-only line saying a contained rung the previous run
#: took is no longer usable (:func:`sandbox_rung_retired_notice`). Its own
#: marker, never ``[SANDBOX_BYPASSED]``: that one stays exactly one line per
#: bypassed slot, so counting it across a run counts slots — the slot that
#: fell to the uncontained rung already prints its own ``[SANDBOX_BYPASSED]``.
SANDBOX_RUNG_RETIRED_MARKER = "[SANDBOX_RUNG_RETIRED]"

#: The well-known rung ids. What travels from the probe to the argv is one of
#: these strings (or ``None``), never a bool: a two-state flag cannot name
#: "contained fallback", "no boundary" and "no fallback" apart. The id is also
#: what the executor's sandbox cache records as the state of a runner that took
#: a rung. :data:`SANDBOX_RUNG_UNSANDBOXED` is the one uncontained rung and the
#: only one any ``bypassed`` word may ever be derived from.
SANDBOX_RUNG_LANDLOCK = "landlock"
SANDBOX_RUNG_UNSANDBOXED = "unsandboxed"
#: The plugin's own Landlock jail (plan codex-sandbox-unavailable-findings-and-
#: fixes §6 F1, 2026-09-30): a wrapper applies a Landlock ruleset to itself and
#: ``exec``s the CLI under ``--sandbox danger-full-access``. It sits between
#: the legacy ``landlock`` rung and ``unsandboxed``, and is reached only when
#: the adapter's own sandbox probe said ``unavailable``. Its grade is
#: :data:`SANDBOX_CONTAINMENT_INCIDENTAL`, never ``contained``: it stops stray
#: and incidental writes, not a model set on escaping (``systemd-run --user``
#: wrote through it, measured 2026-09-29).
SANDBOX_RUNG_PLUGIN_LANDLOCK = "plugin-landlock"

#: The containment grades a rung may carry besides ``contained``
#: (:attr:`SandboxRung.containment`). ``incidental`` is the plugin-landlock
#: rung's: the kernel refuses every content write outside an allow-list, but
#: writes through pathname Unix sockets, metadata changes (``chmod``,
#: ``utimes``) and writes to ``$CODEX_HOME`` are not stopped. ``sandbox_fallback:
#: contained`` never reaches it (its promise is a real OS boundary), and no
#: artifact of such a slot may call it "contained" or "sandboxed".
SANDBOX_CONTAINMENT_INCIDENTAL = "incidental"

#: The marker for a slot on an ``incidental``-grade rung. It **replaces**
#: ``[SANDBOX_BYPASSED]`` for such a slot (that marker still counts uncontained
#: slots only), and is never ``[SANDBOX_FALLBACK]`` (whose label means a real OS
#: boundary). Keyed to the grade, not the rung id, so a later rung of the same
#: grade reuses it.
SANDBOX_INCIDENTAL_MARKER = "[SANDBOX_INCIDENTAL]"

#: The after-the-fact checks of a slot on the incidental rung (F1 "What it
#: fixes", Limits): a flipped executable bit on a tracked file (fan-out lanes
#: only), a change to ``$CODEX_HOME``'s security-relevant files (both lanes),
#: and a turn the jail denied at Codex's own level.
MODE_CHECK_MARKER = "[MODE_CHECK]"
CODEX_HOME_CHECK_MARKER = "[CODEX_HOME_CHECK]"
JAIL_DENIED_MARKER = "[JAIL_DENIED]"

#: The one environment switch that skips the plugin-landlock rung alone for a
#: process (F1 "Where it sits" item 4/6). Its only accepted value is the rung
#: id; any other value is rejected at start-up, never ignored.
SKIP_RUNG_ENV = "MULTI_LLM_CODEX_SKIP_RUNG"

#: The write profiles a fallback may reach (plan step 3, user decision
#: 2026-09-30, option (b)). Separate from :data:`SANDBOX_FALLBACK_PROFILES`,
#: which never grows: ``agent-write`` reaches exactly the rungs an adapter
#: declares in its write ladder — for codex the plugin-landlock rung alone —
#: and only through :func:`write_rung_allowed`.
SANDBOX_WRITE_FALLBACK_PROFILES: Tuple[str, ...] = (PROFILE_AGENT_WRITE,)

#: Plan step 6 (F5, user decision 2026-09-30: "Adopt F5"): the env var the
#: Codex host's MCP server sets on the dispatcher it starts, per tool call, to
#: the chat's own sandbox posture (the turn metadata's ``sandbox_mode``). Read
#: per call and never carried over (``os.environ`` of that one dispatcher
#: process). When — and only when — it says ``danger-full-access`` and the
#: plugin-landlock rung could not take a write dispatch, the write may take the
#: uncontained rung: the user already granted the chat agent unconfined write
#: access to the machine. Below F1 on the ladder, never instead of it; never
#: under ``contained`` or ``off``.
HOST_SANDBOX_POSTURE_ENV = "MULTI_LLM_HOST_SANDBOX_POSTURE"
HOST_POSTURE_FULL_ACCESS = "danger-full-access"


@dataclass(frozen=True)
class WritePostureConsent:
    """The chat's full-access posture, handed to the render for a write
    dispatch on the uncontained rung (F5). Its only valid ``posture`` is
    ``danger-full-access``; the render raises on anything else.

    ``write_scope`` is the scope of the dispatch the consent is handed to (the
    kind map's, never the task JSON's). F5 serves the step-3 scopes alone
    (:data:`WRITE_SCOPES_BY_CONSENT`), so the render and the executor's
    backstop both refuse a consent whose scope is missing or ``repo-wide`` —
    the refusal holds there even if a gate upstream let such a dispatch
    through."""

    posture: str
    source: str = HOST_SANDBOX_POSTURE_ENV
    write_scope: Optional[str] = None


def host_write_posture_consent(
    environ: Optional[Mapping[str, str]] = None,
    *,
    write_scope: Optional[str] = None,
) -> Optional["WritePostureConsent"]:
    """The F5 consent the environment carries for this process, or ``None``.

    Only the exact value ``danger-full-access`` consents; any other posture,
    an empty value or none leaves the step-3 rule as it is. ``write_scope``
    is recorded on the consent for a caller that hands it to a render."""
    env = os.environ if environ is None else environ
    value = (env.get(HOST_SANDBOX_POSTURE_ENV) or "").strip()
    if value == HOST_POSTURE_FULL_ACCESS:
        return WritePostureConsent(posture=value, write_scope=write_scope)
    return None


def write_consent_allows(
    rung: Optional["SandboxRung"],
    policy: Optional[str],
    consent: Optional["WritePostureConsent"],
) -> bool:
    """Whether F5's consent lets a write profile take ``rung``: the uncontained
    rung alone, under ``auto`` alone, with a ``danger-full-access`` consent.
    Called only after the plugin-landlock rung could not take the dispatch."""
    if rung is None or consent is None or consent.posture != HOST_POSTURE_FULL_ACCESS:
        return False
    if rung.name != SANDBOX_RUNG_UNSANDBOXED or rung.contained or getattr(rung, "wrapper", None):
        return False
    return policy == SANDBOX_FALLBACK_AUTO


#: The write scopes a jailed write dispatch may carry (F1 "Write profiles on the
#: rung"). ``plan-file`` is ``apply-suggestions`` (one file rule on the plan),
#: ``tasks`` is ``apply-task-suggestions`` (a dir rule on the default tasks
#: directory, else a file rule on the tasks file), ``repo-wide`` is
#: ``apply-code-fixes``/``implement`` (one dir rule on the repository root —
#: ``.git``, ``.codex``, ``.multi-llm`` and the run's output folder included,
#: instruction-level hands-off; step 3b, revised 2026-10-05).
WRITE_SCOPE_PLAN_FILE = "plan-file"
WRITE_SCOPE_TASKS = "tasks"
WRITE_SCOPE_REPO_WIDE = "repo-wide"
WRITE_SCOPES: Tuple[str, ...] = (
    WRITE_SCOPE_PLAN_FILE, WRITE_SCOPE_TASKS, WRITE_SCOPE_REPO_WIDE,
)
#: The scopes the rung serves: ``plan-file`` and ``tasks`` since step 3
#: (2026-09-30), ``repo-wide`` since step 3b (2026-10-02, a user decision;
#: since 2026-10-05 as one dir rule on the repository root, another user
#: decision — the per-entry enumeration refused the racing re-run's
#: root-level ``index.html`` before any dispatch).
WRITE_SCOPES_ON_RUNG: Tuple[str, ...] = WRITE_SCOPES
#: The scopes F5's consent (plan step 6) may take to the uncontained rung when
#: the jail could not take the dispatch: the step-3 scopes alone. ``repo-wide``
#: never reaches the uncontained rung by consent (2026-10-02, step 3b: the
#: safer reading of "the ``unsandboxed`` rung never reachable" for repo-wide
#: edits; widening F5 to them is a separate user decision).
WRITE_SCOPES_BY_CONSENT: Tuple[str, ...] = (WRITE_SCOPE_PLAN_FILE, WRITE_SCOPE_TASKS)

#: What a contained rung's probe canary prints (on stderr, exit non-zero) when
#: the write it attempted was **not** denied — the fail-open shape: the flag
#: was accepted and no boundary came up. The walk reads it as a *rejected* rung
#: (move on), distinct from a sandbox that could not start.
SANDBOX_CANARY_NOT_DENIED = "multi-llm sandbox canary: the write was not denied"

#: What a contained rung's probe canary prints when it **ran to completion and
#: its write was denied** — the only answer the walk takes a contained rung on.
#: Exit 0 alone is not containment: a CLI that prints usage and exits 0 without
#: ever running the canary would otherwise read as a boundary nobody measured.
#: A canary script must never carry this sentence contiguously in its own text
#: (a CLI that echoes its argv back would then forge it); see
#: :func:`canary_marker_shell_words`.
SANDBOX_CANARY_DENIED = "multi-llm sandbox canary: the write was denied"


def canary_marker_shell_words(marker: str) -> str:
    """``marker`` as a double-quoted shell word that ``echo`` prints verbatim
    but whose **source text** never contains ``marker`` contiguously.

    The sentence is split at its first ``": "`` into two adjacent quoted
    strings (``"a: ""b"``), which a POSIX shell concatenates. So a CLI that
    prints usage echoing the probe's argv cannot put the marker on its output
    — only a shell that actually ran the script can.
    """
    head, sep, tail = marker.partition(": ")
    if not sep:
        raise ValueError(f"marker has no ': ' to split at: {marker!r}")
    return f'"{head}{sep}""{tail}"'


@dataclass(frozen=True)
class SandboxRung:
    """One rung of an adapter's sandbox-fallback ladder (landlock rung, 2026-09-22).

    Declared by the adapter through :meth:`LLMProvider.sandbox_fallback_rungs`,
    walked in order by ``subagent_executor.sandbox_verdict`` only after the
    profile's own probe answered ``unavailable``, and rendered by
    :meth:`LLMProvider.apply_sandbox_fallback` from its ``name``.

    * ``name`` — the rung id that travels (:data:`SANDBOX_RUNG_LANDLOCK`, …).
    * ``probe_argv`` — the model-free command that decides whether this rung is
      usable here, **pinned verbatim**: never rebuilt from the profile's probe
      or from the dispatch argv. ``None`` means the rung needs no probe (the
      uncontained rung: there is no boundary to ask about). A contained rung's
      probe must exit 0 **only when a write it attempts is denied**, and then
      print :data:`SANDBOX_CANARY_DENIED` — exit 0 alone proves that a process
      started, not that a boundary exists, and the walk refuses a markerless
      exit 0.
    * ``argv_rewrite`` — the argv atoms this rung renders, as data (for the
      guards and for ``doctor``); the rendering itself is the adapter's
      :meth:`~LLMProvider.apply_sandbox_fallback`.
    * ``contained`` — whether the rung is a real OS boundary. Decides which
      ``sandbox_fallback`` values may reach it (``auto``/``contained`` vs.
      ``auto`` alone) and whether any artifact may call the slot bypassed.
    * ``deprecated_at`` — ``(measured_at_version, upstream_deprecation_sentence)``
      for a rung that rides a feature upstream has announced it will remove, or
      ``None``. **Render-only**: nothing compares a running CLI's version
      against it.
    * ``removed_at`` — ``(version, evidence)``: the first CLI version on which
      the rung was **measured** unavailable (a measurement on this
      configuration, not an upstream changelog entry), or ``None``. Unlike
      ``deprecated_at`` it **is compared**: a run whose detected CLI version is
      at or above it does not probe the rung at all — the walk records it
      ``skipped`` and the run prints the retirement line once
      (:func:`rung_removed_for_version`). ``multi_llm.py doctor`` alone still
      runs the real probe whatever the version says, so a build that restores
      the rung shows there as a mismatch; re-measuring moves or drops the
      field. (Split from the old two-tuple ``retires_when``, 2026-09-24.)
    * ``removed_signature`` — the sentence the rung's probe prints when this
      CLI build no longer supports the rung (codex 0.156.1's panic), matched
      whitespace-insensitively **by text, never by exit code**. The walk
      records such a probe ``retired`` — its own outcome, distinct from a
      generic ``unavailable`` — and only that outcome (or the version skip)
      earns the retirement line.
    * ``probe_workdir`` — the cwd-relative directory a contained rung's canary
      writes into, or ``None``. The walk creates it and proves it writable
      **outside** the sandbox before the probe runs, so a denial the canary
      sees inside can only be the boundary's — never a ``mkdir`` the sandbox
      refused, a non-directory in the way, or plain filesystem permissions.
      A setup that fails is recorded ``unknown`` (the rung is not taken).
    * ``wrapper`` — the id of a launcher the rung's dispatch and probe are
      prefixed with (``"landlock_exec"``), or ``None`` for a rung rendered
      entirely inside the CLI's argv. A wrapping rung's ``argv_rewrite`` holds
      only the atoms inside the CLI argv; the prefix is added by
      ``utils.landlock_dispatch.wrap_argv`` after ``_resolve_executable``, and
      never by the adapter. An id rather than a path, so the declaration stays
      host-independent for the guards and ``doctor``.
    * ``containment`` — a grade other than ``contained``, or ``None``.
      ``incidental`` (:data:`SANDBOX_CONTAINMENT_INCIDENTAL`) is reached under
      ``auto`` only, gets its own marker and wording, and keeps
      ``contained=False``.
    * ``measured_through`` — ``(version, evidence)``: the newest CLI version the
      rung's allow-list was measured against. Render-only (``doctor``, the
      ``[JAIL_DENIED]`` line), like ``deprecated_at``: a newer CLI is named as
      the likely cause of a jail denial, never refused.
    """

    name: str
    probe_argv: Optional[Tuple[str, ...]]
    argv_rewrite: Tuple[str, ...]
    contained: bool
    deprecated_at: Optional[Tuple[str, str]] = None
    removed_at: Optional[Tuple[str, str]] = None
    probe_workdir: Optional[str] = None
    removed_signature: Optional[str] = None
    wrapper: Optional[str] = None
    containment: Optional[str] = None
    measured_through: Optional[Tuple[str, str]] = None


def rung_is_incidental(rung: Optional["SandboxRung"]) -> bool:
    """Whether ``rung`` carries the ``incidental`` grade (the plugin's jail)."""
    return bool(
        rung is not None
        and getattr(rung, "containment", None) == SANDBOX_CONTAINMENT_INCIDENTAL
    )


@dataclass(frozen=True)
class JailRequest:
    """What a lane knows about a jailed dispatch before it spawns (F1 "How a
    dispatch receives its grant").

    Built once per task by the lane that owns the dispatch, from trusted inputs
    only, with no filesystem side effect. A read-only request carries
    ``repo_root`` and ``kind`` alone; a write request adds ``write_scope`` (from
    the kind map, never the task JSON) and ``target`` (the phase's own write
    target, ``realpath``-resolved). Only a dispatch on the plugin-landlock rung
    reads it; every other dispatch ignores it and renders today's argv.

    ``target_dir`` is set only for the ``tasks`` scope, and only when the tasks
    file sits in the plan's **default** tasks directory
    (``plans/<stem>/tasks/``, after ``realpath``): the grant is then a dir rule
    on that directory. Anywhere else (a ``TASKS_FILE`` override into ``plans/``
    or the output folder) it is ``None`` and the grant is a file rule on
    ``target``, because a dir rule there would grant sibling plans or
    ``state.json`` (``landlock_dispatch.default_tasks_dir`` decides).

    A ``repo-wide`` request (plan step 3b, 2026-10-02; revised 2026-10-05)
    carries no target. Its grant is one dir rule on ``repo_root``
    (``landlock_dispatch.repo_wide_entry``), so the whole repository is
    writable inside the jail; ``output_dir`` is this run's output folder,
    which the developer message tells the model to leave alone beside
    ``.git``, ``.codex`` and ``.multi-llm`` (instruction-level: nothing is
    backed up around a batch, a user decision). No per-task path rides the
    request, so none reaches a cache key.
    """

    repo_root: str
    kind: str
    write_scope: Optional[str] = None
    target: Optional[str] = None
    target_dir: Optional[str] = None
    output_dir: Optional[str] = None


@dataclass(frozen=True)
class JailContext:
    """A :class:`JailRequest` completed at the spawn site, once per attempt:
    the attempt's scratch ``tmpdir`` (made by ``slot_tmpdir()``) and the
    ``codex_home`` the child will really see (read from its composed env).

    Deliberately not named ``DispatchContext`` — ``llm_client.DispatchContext``
    is what an adapter's ``hermetic_dispatch`` yields and must stay free of
    per-task paths. Never stored on an adapter, in a module global or in a
    cache: an argument to the render and the wrap, dropped with the attempt.
    ``codex_home`` is ``None`` until the env is composed (the argv render runs
    before it, and needs only ``tmpdir``).
    """

    request: JailRequest
    tmpdir: str
    codex_home: Optional[str] = None

    @property
    def repo_root(self) -> str:
        return self.request.repo_root

    @property
    def kind(self) -> str:
        return self.request.kind

    @property
    def write_scope(self) -> Optional[str]:
        return self.request.write_scope

    @property
    def target(self) -> Optional[str]:
        return self.request.target

    @property
    def target_dir(self) -> Optional[str]:
        return self.request.target_dir

    @property
    def output_dir(self) -> Optional[str]:
        return self.request.output_dir


def rung_removed_for_version(rung: "SandboxRung", version: Optional[str]) -> bool:
    """Whether ``version`` is at or above ``rung.removed_at``'s version.

    ``False`` for a rung with no ``removed_at`` and for an unknown or empty
    ``version`` — an unread version never skips a probe: the probe runs and its
    outcome is authoritative. Compared through :func:`version_tuple`, the one
    ordering rule of the harness.
    """
    if not rung.removed_at or not version or version == "unknown":
        return False
    token = _version_token(str(version))
    if not token:
        return False
    return version_tuple(token) >= version_tuple(rung.removed_at[0])


def rung_probe_said_removed(rung: "SandboxRung", text: str) -> bool:
    """Whether a rung probe's output carries the rung's ``removed_signature``
    (whitespace-insensitive, since a panic message may wrap)."""
    signature = getattr(rung, "removed_signature", None)
    if not signature:
        return False
    return " ".join(signature.split()) in " ".join((text or "").split())


def sandbox_rung_id(value: Any) -> Optional[str]:
    """Normalise a ``sandbox_fallback`` carrier value to a rung id, or ``None``.

    The carrier was a ``bool`` until the landlock rung; it is now the rung id.
    ``True`` is still accepted as the old spelling of *the* fallback, which was
    always the uncontained rung — so a caller (or a test fake) that still hands
    ``True`` renders exactly what it rendered before, and never a contained
    rung it did not name. Falsy is "no rung".
    """
    if value is True:
        return SANDBOX_RUNG_UNSANDBOXED
    if not value:
        return None
    return str(value)


def sandbox_fallback_notice_text(
    provider_name: str, rung: "SandboxRung", policy: Optional[str]
) -> str:
    """The one ``[SANDBOX_FALLBACK]`` line for a slot on a **contained** rung.

    One builder for the fan-out lanes and the executor's preflight line, so the
    reader greps one sentence across a run the way ``[SANDBOX_BYPASSED]`` reads.
    It names the rung, what it renders, and the key value that permitted it; for
    a rung riding a feature upstream has announced it will remove
    (``deprecated_at``) it names that too, and says in advance what a reader of
    the raw capture will find: the deprecation sentence arrives as an
    ``item.completed`` whose item is ``"type":"error"`` on **every** run of this
    rung, healthy ones included — the marker that the run took the rung, never
    the failure.
    """
    text = (
        f"{SANDBOX_FALLBACK_MARKER} {provider_name}: bubblewrap cannot start; "
        f"running on the contained {rung.name!r} fallback rung "
        f"({' '.join(rung.argv_rewrite)}) under "
        f"providers.{provider_name}.sandbox_fallback={policy or SANDBOX_FALLBACK_AUTO} "
        f"(read-only phase; writes denied by the kernel)"
    )
    if rung.deprecated_at:
        version, sentence = rung.deprecated_at
        text += (
            f"; deprecated upstream (measured at {provider_name} {version}: "
            f"{sentence!r}) — every raw capture of this slot carries that "
            f"sentence as a \"type\":\"error\" item, healthy runs included; it "
            f"marks the rung, it is not the failure"
        )
    return text


def sandbox_rung_retired_notice(
    provider_name: str,
    spec: str,
    rung: "SandboxRung",
    *,
    measured: bool = False,
    version: Optional[str] = None,
    refused: bool = False,
) -> str:
    """The one line naming a contained rung this run could no longer take.

    Two causes, one marker. **Measured** (``measured=True``, 2026-09-24):
    the detected CLI ``version`` is at or above the rung's ``removed_at``, or
    the rung's probe printed its ``removed_signature`` — the rung was *measured*
    unavailable from that build on this configuration (not an upstream
    removal: no changelog says so yet), and the line says so whatever the
    previous run recorded. **By transition** (open question 2 of the
    landlock-rung plan): the previous run of this phase recorded ``spec`` on
    ``rung`` and this run took the uncontained rung instead. Either way it is
    said once per run, with ``deprecated_at``'s version and sentence, and
    nothing else about the run changes. ``spec`` may name several slots,
    comma-joined.

    ``refused=True`` is the ``sandbox_fallback=contained`` refusal path: the
    run did **not** fall to the uncontained rung — it refused the slot — so
    the tail says that instead of offering ``contained`` as the fix.
    """
    said = ""
    if rung.deprecated_at:
        dep_version, sentence = rung.deprecated_at
        said = f" (deprecated at {provider_name} {dep_version}; upstream said {sentence!r})"
    if measured:
        if rung.removed_at:
            removed = f"has been unavailable since {provider_name} {rung.removed_at[0]} (measured)"
            if rung.removed_at[1]:
                removed += f" ({rung.removed_at[1]})"
        else:
            removed = f"is measured unavailable on this {provider_name} build"
        this = f"; this is {provider_name} {version}" if version else ""
        head = (
            f"{SANDBOX_RUNG_RETIRED_MARKER} {spec}: the contained {rung.name!r} "
            f"fallback rung {removed}{this}{said}"
        )
    else:
        head = (
            f"{SANDBOX_RUNG_RETIRED_MARKER} {spec}: the contained {rung.name!r} fallback "
            f"rung the previous run used is no longer usable here{said}"
        )
    if refused:
        return (
            f"{head}; the uncontained rung is never taken under providers."
            f"{provider_name}.sandbox_fallback={SANDBOX_FALLBACK_CONTAINED}, so "
            f"this run refused {spec}"
        )
    return (
        f"{head}; this run fell to the uncontained rung. Set providers."
        f"{provider_name}.sandbox_fallback={SANDBOX_FALLBACK_CONTAINED} to refuse "
        f"instead"
    )


#: The walk outcomes :func:`sandbox_walk_clause` renders (the executor's
#: ``RUNG_*`` constants, spelled here so this module does not import it).
_WALK_OUTCOME_SKIPPED = "skipped"
_WALK_OUTCOME_RETIRED = "retired"
#: A rung the process was told to skip (``MULTI_LLM_CODEX_SKIP_RUNG``): not
#: probed, the walk moves on — and never a retirement, so no retirement line.
WALK_OUTCOME_SKIPPED_BY_SWITCH = "skipped-by-switch"


def _quoted_tail(tail: str) -> str:
    """A probe tail as the one quoted phrase a line can carry: the first line,
    capped, with an ellipsis when anything was cut."""
    text = " ".join((tail or "").split())
    if len(text) > 160:
        text = text[:157].rstrip() + " …"
    return f'"{text}"'


def sandbox_walk_clause(
    provider_name: str,
    walk: Sequence[Tuple[str, str]],
    rung_tails: Sequence[Tuple[str, str]] = (),
    version: Optional[str] = None,
    rungs: Sequence["SandboxRung"] = (),
) -> str:
    """The rung clause appended to the ``[SANDBOX_BYPASSED]`` line (2026-09-24).

    One phrase per rung the walk reached **before** the uncontained one, each
    with its outcome and — when it was probed — its probe tail, so the line
    says that a contained rung exists, was tried, and why it was not taken.
    A rung skipped by version (``removed_at``) says that instead and has no
    tail: nothing was probed; it names the ``removed_at`` version of its
    declaration in ``rungs`` (the running ``version`` when none is given).
    ``""`` when the walk reached no other rung.
    """
    tails = dict(rung_tails or ())
    removed = {
        rung.name: rung.removed_at[0] for rung in rungs or () if rung.removed_at
    }
    wrapping = {rung.name for rung in rungs or () if getattr(rung, "wrapper", None)}
    who = f"{provider_name} {version}" if version else "probe"
    parts: List[str] = []
    for name, outcome in walk or ():
        if outcome == "taken":
            continue
        tail = tails.get(name, "")
        if outcome == WALK_OUTCOME_SKIPPED_BY_SWITCH:
            parts.append(
                f"fallback rung {name!r} not tried: skipped by "
                f"{SKIP_RUNG_ENV}={name}"
            )
            continue
        if name in wrapping and outcome in ("absent", "rejected", "unavailable"):
            # The plugin's own jail (plan codex-sandbox-unavailable §7 step 4):
            # absent is the wrapper's own verdict (no Landlock, an ABI below
            # the floor, a required allow entry missing), never "this build
            # did not recognise the rung".
            said = {
                "absent": f"fallback rung {name!r} absent: the plugin's Landlock jail cannot run here",
                "rejected": f"fallback rung {name!r} rejected: a write its canary made was not denied",
                "unavailable": f"fallback rung {name!r} unavailable: the plugin's Landlock jail failed its self-test",
            }[outcome]
            if tail.strip():
                said += f" ({_quoted_tail(tail)})"
            parts.append(said)
            continue
        if outcome == _WALK_OUTCOME_SKIPPED:
            # "since", not "from": the version named is the first one measured
            # unusable, not the one installed. "unavailable from codex 0.156.1,
            # measured" printed under codex 0.159.3 read as a stale measurement
            # (2026-10-02); the installed build is named when it differs.
            # "unusable", not "removed": codex 0.160.0 still lists the feature
            # (`codex features list`: `use_legacy_landlock deprecated false`),
            # and what was measured is the rung probe's exit-101 panic, so a
            # reader of "removed" would drop a rung a later codex may serve
            # again (adversarial review, 2026-10-02). Only the landlock rung
            # declares `removed_at`, and its measured failure is that panic.
            since = removed.get(name) or version or "?"
            facts = ["panics", "measured"]
            if version and version != since:
                facts.append(f"installed: {version}")
            parts.append(
                f"fallback rung {name!r} not tried: unusable since "
                f"{provider_name} {since} ({'; '.join(facts)})"
            )
            continue
        if outcome == _WALK_OUTCOME_RETIRED:
            said = f"fallback rung {name!r} unavailable: requires bubblewrap in this {provider_name} build"
        elif outcome == "rejected":
            said = f"fallback rung {name!r} rejected: its canary write was not denied"
        elif outcome == "absent":
            said = f"fallback rung {name!r} absent: this build did not recognise the rung (probe ran, no boundary measured)"
        else:
            said = f"fallback rung {name!r} {outcome}"
        if tail.strip():
            said += f" ({who}: {_quoted_tail(tail)})"
        parts.append(said)
    return "; ".join(parts)


def sandbox_bypassed_notice_text(provider_name: str, walk_clause: str = "") -> str:
    """The ``[SANDBOX_BYPASSED]`` line both lanes print — the stem fixed on
    2026-09-17 (see ``review_orchestrator_base.sandbox_bypassed_notice``),
    with the rung clause (:func:`sandbox_walk_clause`) appended after it when
    the walk tried a rung first. One builder, so the fan-out and the executor
    cannot drift apart."""
    text = (
        f"{SANDBOX_BYPASSED_MARKER} {provider_name}: bubblewrap cannot start; "
        f"running --sandbox danger-full-access under "
        f"providers.{provider_name}.sandbox_fallback={SANDBOX_FALLBACK_AUTO} "
        f"(read-only phase; no OS boundary between the model's shell and this "
        f"machine)"
    )
    if walk_clause:
        text += f"; {walk_clause}"
    return text


def sandbox_rung_allowed(rung: "SandboxRung", policy: Optional[str]) -> bool:
    """Whether a resolved ``sandbox_fallback`` ``policy`` may take ``rung``.

    The Configuration table, in one place: ``auto`` reaches every rung,
    ``contained`` only a contained one, ``off`` (and ``None`` — an adapter with
    no fallback, or a write profile) none. The ``incidental`` grade (the
    plugin-landlock rung) keeps ``contained=False``, so ``contained`` never
    reaches it: that value promises a real OS boundary, and letting it accept
    the incidental grade would need a separate, explicit opt-in.

    Read-only profiles only. A write profile goes through
    :func:`write_rung_allowed`, never through this function.
    """
    if policy == SANDBOX_FALLBACK_AUTO:
        return True
    if policy == SANDBOX_FALLBACK_CONTAINED:
        return bool(rung.contained)
    return False


def write_rung_allowed(rung: Optional["SandboxRung"], policy: Optional[str]) -> bool:
    """Whether a **write** profile may take ``rung`` under ``policy`` (plan step 3,
    user decision 2026-09-30, option (b)).

    The structural rule that replaces the old blanket refusal: a write profile
    reaches a rung only if the rung **wraps** the CLI (``wrapper`` set) and
    carries the ``incidental`` grade — i.e. the plugin's own Landlock jail — and
    only under ``auto``. Never the uncontained rung, never the legacy
    ``landlock`` rung, never under ``contained`` (whose promise the incidental
    grade does not keep) or ``off``. ``None`` (no opt-in, no fallback) is no.
    """
    if rung is None or not getattr(rung, "wrapper", None):
        return False
    if not rung_is_incidental(rung):
        return False
    return policy == SANDBOX_FALLBACK_AUTO


def skip_rung_requested(environ: Optional[Mapping[str, str]] = None) -> Optional[str]:
    """The rung ``MULTI_LLM_CODEX_SKIP_RUNG`` skips for this process, or ``None``.

    The one accepted value is the plugin-landlock rung id; unset or empty is
    ``None``. Any other value raises ``ValueError`` naming the variable and the
    accepted value — rejected at start-up, never silently ignored (F1 "Where it
    sits" item 6).
    """
    env = os.environ if environ is None else environ
    value = (env.get(SKIP_RUNG_ENV) or "").strip()
    if not value:
        return None
    if value != SANDBOX_RUNG_PLUGIN_LANDLOCK:
        raise ValueError(
            f"{SKIP_RUNG_ENV}={value!r} is not recognised: the only rung it can "
            f"skip is {SANDBOX_RUNG_PLUGIN_LANDLOCK!r} (unset it to walk the "
            f"full ladder)"
        )
    return value


#: The residual clauses of the ``[SANDBOX_INCIDENTAL]`` line, per lane (F1
#: Limits and "What it fixes"). The fan-out lanes run the mode check and a
#: fail-closed home check; the executor lane runs a warn-only home check and no
#: mode check.
_INCIDENTAL_RESIDUALS_FANOUT = (
    "writes through Unix sockets and to file timestamps are neither stopped "
    "nor checked, writes to $CODEX_HOME are not stopped and only its config, "
    "instruction and plugin files are checked after this slot, and a changed "
    "file mode is not stopped but is checked after this slot"
)
_INCIDENTAL_RESIDUALS_EXECUTOR = (
    "writes through Unix sockets and to file timestamps are neither stopped "
    "nor checked, writes to $CODEX_HOME are not stopped and only its config, "
    "instruction and plugin files are reported after this dispatch, not "
    "failed, and a changed file mode is neither stopped nor checked"
)
INCIDENTAL_LANE_FANOUT = "fanout"
INCIDENTAL_LANE_EXECUTOR = "executor"


def sandbox_incidental_notice_text(
    provider_name: str,
    rung: "SandboxRung",
    policy: Optional[str],
    probe_tail: str = "",
    *,
    walk_clause: str = "",
    lane: str = INCIDENTAL_LANE_FANOUT,
    write_scope: Optional[str] = None,
    target: Optional[str] = None,
) -> str:
    """The one ``[SANDBOX_INCIDENTAL]`` line for a slot or dispatch on an
    ``incidental``-grade rung (plan §7, "Step 2 subtask: messaging and markers").

    One builder for both lanes — ``review_orchestrator_base.sandbox_refusal``
    and ``subagent_executor._detect_sandbox`` pick it by grade — so the reader
    greps one sentence across a run. Its clauses, in order: the marker and the
    runner; the standard probe's failure line and the walk clause (the legacy
    rung skipped by version); the rung id, the key in force and the phase; what
    the rung stops (stray writes, not the model); what it does not stop and
    what checks it afterwards, which differs per ``lane``. A write dispatch
    (``write_scope`` set) names its scope and target and says the network is
    not confined; it never says "read-only". The line never calls the rung
    "contained" or "sandboxed".
    """
    text = f"{SANDBOX_INCIDENTAL_MARKER} {provider_name}: its own sandbox cannot start here"
    said = " ".join((probe_tail or "").split())
    if len(said) > 160:
        said = said[:157].rstrip() + " …"
    if said:
        text += f" ({said})"
    if walk_clause:
        text += f"; {walk_clause}"
    if write_scope == WRITE_SCOPE_REPO_WIDE:
        phase = (
            f"write phase, scope repo-wide: the whole repository {target or ''} "
            f"is what it may write (one rule on the root — .git, .codex, "
            f".multi-llm and the run's output folder included; the model is "
            f"told to leave them alone and the sweep checks afterwards), and "
            f"network access is not confined"
        )
    elif write_scope:
        phase = (
            f"write phase, scope {write_scope}: {target or '(no target)'} is the "
            f"one repository path it may write, and network access is not "
            f"confined"
        )
    else:
        phase = "read-only phase"
    text += (
        f"; running on fallback rung {rung.name!r} under "
        f"providers.{provider_name}.sandbox_fallback="
        f"{policy or SANDBOX_FALLBACK_AUTO} ({phase}), which stops stray "
        f"writes, not the model: "
    )
    text += (
        _INCIDENTAL_RESIDUALS_EXECUTOR if lane == INCIDENTAL_LANE_EXECUTOR
        else _INCIDENTAL_RESIDUALS_FANOUT
    )
    return text

# ---------------------------------------------------------------------------
# Non-interactive git env (§2.2)
# ---------------------------------------------------------------------------

#: ``git_env.credential_helper`` — the closed policy set. ``auto`` is the shipped
#: scoping (:data:`HELPER_WIPE_PROFILES`); ``wipe`` and ``keep`` are the two
#: escape hatches, settable globally, per provider, or through
#: ``MULTI_LLM_GIT_CREDENTIAL_HELPER`` for one run.
GIT_HELPER_AUTO = "auto"
GIT_HELPER_WIPE = "wipe"
GIT_HELPER_KEEP = "keep"
GIT_HELPER_POLICIES: Tuple[str, ...] = (
    GIT_HELPER_AUTO,
    GIT_HELPER_WIPE,
    GIT_HELPER_KEEP,
)

#: The profiles that get ``credential.helper=""`` under the ``auto`` policy: the
#: ``generate`` callee path (which is the Lane A fan-out) and ``agent-readonly``.
#: ``agent-write`` is deliberately **absent** — see :func:`git_env`.
HELPER_WIPE_PROFILES = frozenset({PROFILE_GENERATE, PROFILE_AGENT_READONLY})

#: The measured, load-bearing half, applied to **every** provider and **both**
#: lanes. ``GIT_TERMINAL_PROMPT=0`` alone turns the 75.1 s tty-prompt hang into a
#: 0.253 s failure; ``GIT_ASKPASS=""`` is read by git as *no askpass* (never
#: exec'd) and uniquely short-circuits the whole ``GIT_ASKPASS → core.askPass →
#: SSH_ASKPASS`` chain, which ``GIT_TERMINAL_PROMPT`` does not. Neither suppresses
#: a credential helper that *answers*, so authentication that works today keeps
#: working everywhere.
#:
#: The last three were measured **inert on Linux** and are **untested on Windows
#: and macOS**: carry them as cheap hedges, never as a claim about those
#: platforms (verification is owned by ``plans/windows-macos-portability.md``).
#: ``credential.interactive`` / ``credential.guiPrompt`` are deliberately absent —
#: they are not git config keys at all (absent from ``git-config(1)`` and from the
#: binary's strings; they are Git Credential Manager settings), and so is
#: ``LC_ALL=C``: every git call in this repo uses ``--porcelain``/``rev-parse``/
#: ``diff``/``show`` and none passes ``env=``, so this block never reaches them.
GIT_ENV_GLOBAL: Dict[str, str] = {
    "GIT_TERMINAL_PROMPT": "0",
    "GIT_ASKPASS": "",
    "SSH_ASKPASS": "",
    "SSH_ASKPASS_REQUIRE": "never",
    "GCM_INTERACTIVE": "never",
}


def wipes_credential_helper(
    profile: str, credential_helper: str = GIT_HELPER_AUTO
) -> bool:
    """Whether this dispatch gets ``credential.helper=""`` (§2.2).

    ``auto`` is the scoping decision, not a guess: the wipe is the only measured
    cure for a *hanging* helper (90.1 s and an orphan → 0.27 s and no child), but
    it cannot tell a helper that hangs from one that works, so it equally
    suppresses ``store``, an OS keychain and ``gh auth git-credential``. It is
    therefore applied only where a private-remote credential has no business
    being needed at all.
    """
    if credential_helper == GIT_HELPER_KEEP:
        return False
    if credential_helper == GIT_HELPER_WIPE:
        return True
    return profile in HELPER_WIPE_PROFILES


def git_env(
    profile: str = PROFILE_GENERATE,
    *,
    credential_helper: str = GIT_HELPER_AUTO,
    base_env: Optional[Mapping[str, str]] = None,
) -> Dict[str, str]:
    """The non-interactive git env delta for one dispatch (§2.2).

    Every provider shells out to git under an agent profile, and a credential
    prompt behind ``capture_output=True`` blocks forever: measured at **75.1 s
    with two empty streams** for a tty prompt and **90.1 s plus an orphaned
    helper** for a GUI-style credential helper, both against a private https
    remote under a scratch ``HOME``. ``stdin=DEVNULL`` does not help — git prompts
    on ``/dev/tty``.

    Two layers, and the layering is the whole design:

    * :data:`GIT_ENV_GLOBAL` — unconditional, every provider, both lanes.
    * ``GIT_CONFIG_COUNT`` + ``credential.helper=""`` — **scoped** to
      :data:`HELPER_WIPE_PROFILES` (``generate``, i.e. the Lane A fan-out, and
      ``agent-readonly``).

    **The wipe must never be globalised onto ``agent-write``.** That profile
    really does run ``git commit``/``status``/``clone``/``fetch`` against the
    user's own remotes, and an empty helper list would fail those closed — the
    one profile that legitimately needs a private-remote credential. Its
    protection against a hanging helper is the process-group kill plus the
    per-task budget: a *bound*, not a fast failure. A later "unify the git env"
    refactor that moves these three keys out of the ``profile`` branch and into
    the unconditional block is a behaviour regression, not a cleanup.

    **Accepted trade-off, in the scoped lanes only.** A private-HTTPS
    ``clone``/``fetch`` that works today returns in ~0.27 s with ``fatal: could
    not read Username for 'https://…': terminal prompts disabled``; the helper is
    never invoked and leaves no orphan. That is a fast, legible failure rather
    than a hang or a silent wrong answer, and those lanes are Q&A and analysis
    over a workspace that is already checked out.
    ``git_env.credential_helper: keep`` restores today's behaviour for them.

    ``base_env`` (default ``os.environ``, which is what both spawn sites merge
    this delta over) is read only to find an existing ``GIT_CONFIG_COUNT``: a
    caller's own injected keys are preserved and ours is **appended last**,
    because for a multi-valued key an empty value *resets the list*, so it only
    suppresses helpers declared before it.
    """
    env = dict(GIT_ENV_GLOBAL)
    if not wipes_credential_helper(profile, credential_helper):
        return env
    source = os.environ if base_env is None else base_env
    try:
        index = int(str(source.get("GIT_CONFIG_COUNT", "") or "0"))
    except (TypeError, ValueError):
        index = 0
    index = max(index, 0)
    env["GIT_CONFIG_COUNT"] = str(index + 1)
    env[f"GIT_CONFIG_KEY_{index}"] = "credential.helper"
    env[f"GIT_CONFIG_VALUE_{index}"] = ""
    return env


# ─────────────────────────────────────────────────────────────────────────────
# M3 (donor §2.1) + M17 (donor §2.4) — the ONE shared child-env builder.
#
# These two ship as one change (atomic group **A6**): M17 without M3's sanitized
# gate fails every API-key-only `claude-code` slot closed, and M3 without its
# Lane B `env_guards.passthrough` half is a no-op that looks done. The reason
# they cannot be split is structural and lives right here — Lane A applied only
# the adapter's `get_remove_env`, while Lane B subtracted the host's
# `env_guards` and re-admitted `passthrough`, so the two lanes *constructed*
# the child env differently. A credential strip landing on that split strips on
# one lane and inherits on the other; a deny-by-default allowlist landing on it
# allows what the other denies, silently. :func:`build_child_env` is the single
# construction both lanes go through, which is what makes "Lane A ≡ Lane B"
# a property of the code rather than of two call sites kept in sync by hand.
#
# The composition order is load-bearing:
#   1. the inherited environment, **filtered** by M17's allowlist when it is on;
#   2. the adapter's own delta (`resolve_env`), applied last so it always wins —
#      this is what keeps opencode's run-scoped hermetic `XDG_CONFIG_HOME` and
#      every `MUSE_*`/`CURSOR_*` redirect intact under an allowlist that would
#      not have *inherited* them;
#   3. the removals: the adapter's `get_remove_env()` ∪ the host's guards, minus
#      the host's `passthrough`.
# ─────────────────────────────────────────────────────────────────────────────

#: `providers.<name>.strip_vendor_keys` — the closed policy set (§2.1 rule 3).
#: `auto` is the shipped default and means "consult the adapter's own gate";
#: `always` skips the gate and strips; `never` disables the credential half.
#: It is a **provider** key, not a `driver.*` key and not an env var: it changes
#: what one provider's spawn inherits.
STRIP_VENDOR_KEYS_AUTO = "auto"
STRIP_VENDOR_KEYS_ALWAYS = "always"
STRIP_VENDOR_KEYS_NEVER = "never"
STRIP_VENDOR_KEYS_POLICIES: Tuple[str, ...] = (
    STRIP_VENDOR_KEYS_AUTO,
    STRIP_VENDOR_KEYS_ALWAYS,
    STRIP_VENDOR_KEYS_NEVER,
)

#: The per-provider default for `strip_vendor_keys`, and the reason there is a
#: table rather than one constant. claude-code has a **zero-network verdict**
#: (`claude auth status`, §2.1 rule 1) so `auto` can mean something there.
#: codex has none — `codex login status` false-negatives for a `CODEX_API_KEY`-
#: only user and `codex doctor --json` is advisory (§5.3) — so `auto` behaves as
#: `never` for it and for every other adapter: an adapter with no verdict strips
#: nothing unless the user opts in per provider. Raising a row requires a
#: measured zero-network probe for that CLI, never a guess.
STRIP_VENDOR_KEYS_DEFAULTS: Dict[str, str] = {"claude-code": STRIP_VENDOR_KEYS_AUTO}
STRIP_VENDOR_KEYS_FALLBACK = STRIP_VENDOR_KEYS_NEVER

#: `providers.<name>.vendor_backend` — the *second*, independent gate (§2.1
#: rule 4). `CLAUDE_CODE_USE_BEDROCK`/`_VERTEX`/… are the configured auth path
#: for users who really run against Bedrock, Vertex or Foundry, so they are
#: gated on **declaration**, never on the credential probe: under `auto` such a
#: variable is stripped iff it arrived by ambient inheritance (multi-llm never
#: sets one itself, so an undeclared one can only have leaked in from the
#: invoking shell). The two gates are independent — a `vendor_backend: keep`
#: user still gets the credential row evaluated normally, and a
#: `strip_vendor_keys: never` user still gets an undeclared backend removed.
VENDOR_BACKEND_AUTO = "auto"
VENDOR_BACKEND_KEEP = "keep"
VENDOR_BACKEND_STRIP = "strip"
VENDOR_BACKEND_POLICIES: Tuple[str, ...] = (
    VENDOR_BACKEND_AUTO,
    VENDOR_BACKEND_KEEP,
    VENDOR_BACKEND_STRIP,
)

_ENV_POLICY_WARNED: set = set()


def _warn_policy_once(key: str, message: str) -> None:
    """One warning per distinct problem per process, on stderr.

    These values are read on every dispatch, far from any parser, so raising out
    of the middle of a fan-out over a typo would be worse than the typo — and
    printing the same line once per slot would bury the run's real output.
    """
    if key in _ENV_POLICY_WARNED:
        return
    _ENV_POLICY_WARNED.add(key)
    print(message, file=sys.stderr)


def reset_env_policy_warnings() -> None:
    """Forget the warn-once set (tests; never called on a run path)."""
    _ENV_POLICY_WARNED.clear()


def _merged_config(anchor: Optional[str] = None) -> Dict[str, Any]:
    """multi-llm's merged config, or ``{}`` when it cannot be read.

    A config problem may never turn into a refusal or a crash on a dispatch
    path, so every failure resolves to "no configuration", i.e. the documented
    defaults. Same posture as ``opencode._load_config``.
    """
    try:  # pragma: no cover - import shim mirrors the rest of utils/
        from ..provider_registry import load_config
    except ImportError:  # pragma: no cover - direct-script import shim
        from utils.provider_registry import load_config  # type: ignore[no-redef]
    try:
        config = load_config(anchor=anchor)
    except Exception:  # noqa: BLE001 - a config read may not break a dispatch
        return {}
    return config if isinstance(config, dict) else {}


def _provider_block(name: str, anchor: Optional[str] = None) -> Dict[str, Any]:
    providers = _merged_config(anchor).get("providers")
    if not isinstance(providers, dict):
        return {}
    block = providers.get(name)
    return block if isinstance(block, dict) else {}


def _resolve_policy(
    value: Any,
    policies: Tuple[str, ...],
    default: str,
    key_name: str,
) -> str:
    if value is None:
        return default
    candidate = str(value).strip().lower()
    if candidate in policies:
        return candidate
    _warn_policy_once(
        f"{key_name}:{candidate}",
        f"multi-llm config warning: ignoring {key_name}={value!r} (expected one "
        f"of {', '.join(policies)}); using {default}",
    )
    return default


def strip_vendor_keys_policy(
    provider_name: str, anchor: Optional[str] = None
) -> str:
    """Resolve ``providers.<name>.strip_vendor_keys`` (§2.1 rule 3).

    Read through the normal layering (base → auto-discovered
    ``<git-root>/.multi-llm/providers.yaml`` → ``MULTI_LLM_PROVIDERS_CONFIG``),
    so a repo can set it without editing the shipped file. The default comes
    from :data:`STRIP_VENDOR_KEYS_DEFAULTS`, which is per provider because only
    an adapter with a zero-network verdict can give ``auto`` a meaning.
    """
    default = STRIP_VENDOR_KEYS_DEFAULTS.get(provider_name, STRIP_VENDOR_KEYS_FALLBACK)
    return _resolve_policy(
        _provider_block(provider_name, anchor).get("strip_vendor_keys"),
        STRIP_VENDOR_KEYS_POLICIES,
        default,
        f"providers.{provider_name}.strip_vendor_keys",
    )


def vendor_backend_policy(provider_name: str, anchor: Optional[str] = None) -> str:
    """Resolve ``providers.<name>.vendor_backend`` (§2.1 rule 4)."""
    return _resolve_policy(
        _provider_block(provider_name, anchor).get("vendor_backend"),
        VENDOR_BACKEND_POLICIES,
        VENDOR_BACKEND_AUTO,
        f"providers.{provider_name}.vendor_backend",
    )


def declared_env_names(
    provider_name: str,
    domain: Collection[str],
    anchor: Optional[str] = None,
) -> Tuple[str, ...]:
    """The names this provider's own ``env:`` block declares, within ``domain``.

    ``domain`` is the adapter's pinned list — it doubles as the **validation
    domain** for the declaration, so the set a user may declare and the set the
    strip reasons about cannot drift apart (§2.1's pinned-constants test (b)).
    A declared name outside the domain warns once and is ignored rather than
    silently widening what "declared" means.
    """
    block = _provider_block(provider_name, anchor).get("env")
    if not isinstance(block, dict):
        return ()
    declared = []
    for name in block:
        key = str(name)
        if key in domain:
            declared.append(key)
    return tuple(declared)


# ── M17 (§2.4) — the deny-by-default allowlist, and the matrix that gates it ──

#: `env_allowlist: off | on`, read from the **top level** of the merged config
#: because it governs how every provider's child env is constructed, not one
#: provider's spawn. **It ships `off`** and stays `off` until the Linux column
#: of :func:`env_allowlist_matrix` is green over the registry *as it stands*
#: (M0.a) — an allowlist whose matrix was derived from the donor's thirteen-name
#: roster silently omits four adapters' credential, keyring, proxy and CA cells,
#: and each omission is a mid-run auth or TLS failure of exactly the kind the
#: allowlist exists to prevent. So an unrun cell degrades to today's inheritance
#: rather than to a silent failure.
ENV_ALLOWLIST_OFF = "off"
ENV_ALLOWLIST_ON = "on"
ENV_ALLOWLIST_POLICIES: Tuple[str, ...] = (ENV_ALLOWLIST_OFF, ENV_ALLOWLIST_ON)
ENV_ALLOWLIST_DEFAULT = ENV_ALLOWLIST_OFF

#: The matrix axes. Platforms and capabilities are literals because they are the
#: axes themselves; the **CLI axis is never a literal** — it is the live
#: registry, which is the whole of M0.a.
ENV_ALLOWLIST_PLATFORMS: Tuple[str, ...] = ("linux", "macos", "windows")
ENV_ALLOWLIST_CAPABILITIES: Tuple[str, ...] = (
    "credential",
    "keyring",
    "proxy",
    "ca_bundle",
)

#: A cell is **green** only when the CLI, launched under ``env -i`` plus the
#: allowlist, reaches that capability at parity with a full-env control — not
#: merely when it answers ``--version``. Anything else is ``unmeasured``.
ENV_ALLOWLIST_GREEN = "green"
ENV_ALLOWLIST_UNMEASURED = "unmeasured"

#: The measurements taken so far, keyed ``(provider, platform, capability)``.
#: **Empty on purpose.** Nothing in this pass ran a cell, so every cell reads
#: ``unmeasured`` and the shipped default stays ``off``. A cell is added here
#: only by a recorded parity run, never by inspection.
ENV_ALLOWLIST_MEASURED: Dict[Tuple[str, str, str], str] = {}

#: The two CA-bundle families, which is the correction M0.a makes to the donor's
#: "all these CLIs are Node". ``NODE_EXTRA_CA_CERTS`` covers the npm installs —
#: **ten of seventeen** once `copilot`, `kimi` and `qwen-code` are counted — and
#: is useless for the Go/Python/Rust/native seven (`vibe` is a PyPI install),
#: which need the OpenSSL/requests/curl names instead. A corporate-CA user is
#: broken by the donor's list as drafted, which is why the family is declared
#: per adapter and cross-checked against the registry.
CA_FAMILY_NODE = "node"
CA_FAMILY_NATIVE = "native"
CA_BUNDLE_ENV: Dict[str, Tuple[str, ...]] = {
    CA_FAMILY_NODE: ("NODE_EXTRA_CA_CERTS",),
    CA_FAMILY_NATIVE: (
        "SSL_CERT_FILE",
        "SSL_CERT_DIR",
        "REQUESTS_CA_BUNDLE",
        "CURL_CA_BUNDLE",
    ),
}


@dataclass(frozen=True)
class RunnerEnvProfile:
    """One adapter's contribution to the allowlist (§2.4's per-CLI axis).

    ``ca_family`` decides which CA-bundle variable is *load-bearing* for that
    adapter's ``ca_bundle`` cell; both families are admitted for every adapter
    regardless, because a variable a CLI ignores is inert and a wrong guess here
    would be a TLS failure rather than a tidy one.

    ``prefixes`` is the CLI's own prefix family (donor: "plus each harness's own
    prefix family") and ``names`` the exact home/config variables the
    measurement note enumerates.
    """

    ca_family: str
    prefixes: Tuple[str, ...] = ()
    names: Tuple[str, ...] = ()


#: One row per **registered** adapter. This is declared data rather than derived
#: because the values are measurements, but its completeness is not a matter of
#: opinion: `tests/test_env_allowlist.py` parametrizes over the live registry and
#: reds when a newly registered adapter has no row — which is the failure M0.a
#: names as security-relevant rather than tidy.
ENV_ALLOWLIST_PROFILES: Dict[str, RunnerEnvProfile] = {
    "agy": RunnerEnvProfile(
        CA_FAMILY_NATIVE, ("ANTIGRAVITY_",), ("ANTIGRAVITY_EXECUTABLE_DATA_DIR",)
    ),
    "aider": RunnerEnvProfile(CA_FAMILY_NATIVE, ("AIDER_",), ("BROWSER", "COLUMNS")),
    "claude-code": RunnerEnvProfile(CA_FAMILY_NODE, (), ("CLAUDE_CONFIG_DIR",)),
    "cline": RunnerEnvProfile(CA_FAMILY_NODE, ("CLINE_",), ("CLINE_DIR", "CLINE_DATA_DIR")),
    "codex": RunnerEnvProfile(CA_FAMILY_NATIVE, ("CODEX_",), ("CODEX_HOME",)),
    "copilot": RunnerEnvProfile(CA_FAMILY_NODE, ("COPILOT_",), ("COPILOT_HOME",)),
    "cursor-agent": RunnerEnvProfile(
        CA_FAMILY_NODE,
        ("CURSOR_",),
        ("AGENT_CLI_CREDENTIAL_STORE", "NODE_COMPILE_CACHE"),
    ),
    # Native TLS label only: fx 0.0.14 uses system trust, not SSL_CERT_FILE.
    "fx": RunnerEnvProfile(CA_FAMILY_NATIVE, ("FX_",), ()),
    "gemini": RunnerEnvProfile(
        CA_FAMILY_NODE, ("GEMINI_",), ("GEMINI_DIR", "GEMINI_CLI_HOME")
    ),
    # goose is XDG-only for config; its keyring cell is the `org.freedesktop.
    # secrets` pair in the shared base list, which is why that pair is not
    # optional there.
    "goose": RunnerEnvProfile(CA_FAMILY_NATIVE, ("GOOSE_",), ()),
    "grok": RunnerEnvProfile(CA_FAMILY_NATIVE, ("GROK_",), ("GROK_HOME",)),
    "kilocode": RunnerEnvProfile(CA_FAMILY_NODE, ("KILO_",), ("KILO_CONFIG_DIR",)),
    "kimi": RunnerEnvProfile(CA_FAMILY_NODE, ("KIMI_",), ("KIMI_CODE_HOME",)),
    # muse is XDG-only too, but its launcher reads a MUSE_* family and
    # self-updates at launch unless MUSE_NO_AUTO_UPDATE is set.
    "muse": RunnerEnvProfile(CA_FAMILY_NATIVE, ("MUSE_",), ()),
    # omp is a Bun single-file binary whose TLS is BoringSSL, so whether it
    # honours NODE_EXTRA_CA_CERTS or the OpenSSL names is unmeasured. The cell
    # is a **label**, not a filter — `env_allowlist_for` admits both families for
    # every adapter and this field only names the load-bearing variable for the
    # `ca_bundle` matrix cell — so pi's row is taken on the shared-lineage
    # argument and a wrong guess costs a wrong comment, never a dispatch.
    # It shares pi's PI_* family (including PI_CODING_AGENT_DIR, which redirects
    # the default profile only) and adds its own OMP_*.
    "omp": RunnerEnvProfile(CA_FAMILY_NODE, ("PI_", "OMP_"), ("PI_CODING_AGENT_DIR",)),
    "opencode": RunnerEnvProfile(
        CA_FAMILY_NODE,
        ("OPENCODE_",),
        ("OPENCODE_CONFIG", "OPENCODE_CONFIG_DIR", "OPENCODE_CONFIG_CONTENT"),
    ),
    "pi": RunnerEnvProfile(CA_FAMILY_NODE, ("PI_",), ("PI_CODING_AGENT_DIR",)),
    "qwen-code": RunnerEnvProfile(CA_FAMILY_NODE, ("QWEN_",), ("QWEN_HOME",)),
    "vibe": RunnerEnvProfile(CA_FAMILY_NATIVE, ("VIBE_",), ("VIBE_HOME",)),
}

#: Exact names every adapter gets. The corrections the donor's own measurement
#: forced are all here: ``SSH_AUTH_SOCK`` (every CLI shells out to git),
#: ``DBUS_SESSION_BUS_ADDRESS`` + ``XDG_RUNTIME_DIR`` (without them goose cannot
#: reach ``org.freedesktop.secrets``), lower-case proxies (matched
#: case-insensitively, see :func:`env_allowlist_admits`), ``XDG_CACHE_HOME``,
#: ``NODE_OPTIONS``, and the Windows set the last column will need.
ENV_ALLOWLIST_BASE_NAMES: Tuple[str, ...] = (
    "HOME", "PATH", "TERM", "TMPDIR", "USER", "LOGNAME", "SHELL", "PWD", "TZ",
    "SSH_AUTH_SOCK", "DBUS_SESSION_BUS_ADDRESS",
    "NODE_OPTIONS",
    "COLUMNS", "LINES", "NO_COLOR", "FORCE_COLOR",
    # `git_utils.intent_to_add_untracked` marks untracked files in a private
    # index copy it exports here (2026-10-02, replacing `git add -N` on the
    # user's index); a reviewer that runs `git diff` itself must read the same
    # copy, or the new files it is reviewing vanish from its diff.
    "GIT_INDEX_FILE",
    # Windows — unmeasured on this pass; `windows-macos-portability.md` owns
    # that column's runners, and an absent name there is a CLI that cannot
    # start at all rather than one that mis-authenticates.
    "SYSTEMROOT", "COMSPEC", "PATHEXT", "APPDATA", "LOCALAPPDATA",
    "USERPROFILE", "USERNAME", "HOMEDRIVE", "HOMEPATH", "TEMP", "TMP",
    "PROGRAMDATA", "PROGRAMFILES", "WINDIR", "NUMBER_OF_PROCESSORS",
    "PROCESSOR_ARCHITECTURE",
)

#: Prefix families every adapter gets. ``HTTP_``/``HTTPS_``/``ALL_PROXY``/
#: ``NO_PROXY``/``FTP_PROXY`` cover the proxy capability in both cases (the
#: comparison is case-insensitive), ``SSL_`` the OpenSSL CA names, ``XDG_`` the
#: whole XDG set including ``XDG_RUNTIME_DIR`` and ``XDG_CACHE_HOME``,
#: ``GIT_CONFIG_`` the numbered keys §2.2 injects, and ``MULTI_LLM_`` our own
#: namespace, which a nested invocation reads.
ENV_ALLOWLIST_BASE_PREFIXES: Tuple[str, ...] = (
    "HTTP_", "HTTPS_", "ALL_PROXY", "NO_PROXY", "FTP_PROXY",
    "SSL_", "XDG_", "LANG", "LC_", "NPM_CONFIG_", "GIT_CONFIG_", "MULTI_LLM_",
)


def env_allowlist_policy(anchor: Optional[str] = None) -> str:
    """Resolve the top-level ``env_allowlist`` key (default ``off``)."""
    value = _merged_config(anchor).get("env_allowlist")
    if isinstance(value, bool):
        # YAML 1.1 resolves a bare `on`/`off` to a boolean, and a user who wrote
        # the documented word should get the documented behaviour.
        return ENV_ALLOWLIST_ON if value else ENV_ALLOWLIST_OFF
    return _resolve_policy(
        value, ENV_ALLOWLIST_POLICIES, ENV_ALLOWLIST_DEFAULT, "env_allowlist"
    )


def env_allowlist_enabled(anchor: Optional[str] = None) -> bool:
    """Whether the deny-by-default filter runs for this process."""
    return env_allowlist_policy(anchor) == ENV_ALLOWLIST_ON


def env_allowlist_for(provider_name: str) -> Tuple[Tuple[str, ...], Tuple[str, ...]]:
    """``(exact names, prefixes)`` this adapter's children may inherit.

    An adapter with no declared profile falls back to the shared base plus both
    CA families — the fail-*open* direction, because a brand-new adapter that
    inherits one variable too many is a smaller failure than one that cannot
    reach its own credential store. The registry-parametrized completeness test
    is what stops that fallback from becoming the normal case.
    """
    profile = ENV_ALLOWLIST_PROFILES.get(provider_name)
    names: List[str] = list(ENV_ALLOWLIST_BASE_NAMES)
    for family in CA_BUNDLE_ENV.values():
        names.extend(family)
    prefixes: List[str] = list(ENV_ALLOWLIST_BASE_PREFIXES)
    if profile is not None:
        names.extend(profile.names)
        prefixes.extend(profile.prefixes)
    return tuple(dict.fromkeys(names)), tuple(dict.fromkeys(prefixes))


def env_allowlist_admits(provider_name: str, key: str) -> bool:
    """Whether ``key`` survives the allowlist for this adapter.

    Comparison is **case-insensitive**, which is what makes lower-case
    ``http_proxy``/``https_proxy`` (aider/libcurl) and Windows' case-insensitive
    names one rule rather than three lists.
    """
    names, prefixes = env_allowlist_for(provider_name)
    upper = key.upper()
    if upper in {n.upper() for n in names}:
        return True
    return any(upper.startswith(prefix.upper()) for prefix in prefixes)


def apply_env_allowlist(
    env: Mapping[str, str], provider_name: str
) -> Dict[str, str]:
    """The inherited environment, reduced to what this adapter may see."""
    return {key: value for key, value in env.items() if env_allowlist_admits(provider_name, key)}


def env_allowlist_matrix(
    provider_names: Optional[Collection[str]] = None,
) -> Dict[Tuple[str, str, str], str]:
    """The per-CLI × per-platform × per-capability matrix (§2.4 condition 2).

    The CLI axis defaults to the **live registry**, never to a name list: the
    specifications this came from were written against thirteen adapters and the
    registry holds more, so a matrix derived from a literal roster silently omits
    the newcomers' credential, keyring, proxy and CA cells. Its size is therefore
    ``len(registry) × len(platforms) × len(capabilities)``, computed, not typed.
    """
    if provider_names is None:
        try:  # pragma: no cover - import shim mirrors the rest of utils/
            from ..provider_registry import _PROVIDERS
        except ImportError:  # pragma: no cover - direct-script import shim
            from utils.provider_registry import _PROVIDERS  # type: ignore[no-redef]
        provider_names = sorted(_PROVIDERS)
    return {
        (name, platform, capability): ENV_ALLOWLIST_MEASURED.get(
            (name, platform, capability), ENV_ALLOWLIST_UNMEASURED
        )
        for name in sorted(provider_names)
        for platform in ENV_ALLOWLIST_PLATFORMS
        for capability in ENV_ALLOWLIST_CAPABILITIES
    }


def env_allowlist_column(
    platform: str, provider_names: Optional[Collection[str]] = None
) -> Dict[Tuple[str, str, str], str]:
    """One platform's column of :func:`env_allowlist_matrix`."""
    return {
        cell: status
        for cell, status in env_allowlist_matrix(provider_names).items()
        if cell[1] == platform
    }


def env_allowlist_column_is_green(
    platform: str, provider_names: Optional[Collection[str]] = None
) -> bool:
    """Whether every cell in a platform's column is measured green.

    This is the **ship gate**: until it answers ``True`` for a platform, the
    shipped default on that platform stays ``off``.
    """
    column = env_allowlist_column(platform, provider_names)
    return bool(column) and all(
        status == ENV_ALLOWLIST_GREEN for status in column.values()
    )


# ── the skill's own Python environment stays with the skill ──────────────────

#: Names that would carry the skill's own virtual environment into a runner.
#: Every host starts the dispatcher with ``uv run --project <skill dir>``, which
#: exports ``VIRTUAL_ENV`` naming the skill's environment, and a forwarded or
#: image-wide ``UV_PROJECT_ENVIRONMENT`` can name it too. A runner works in the
#: user's repository, where the first makes ``uv pip``, ``poetry`` and friends
#: install into the skill's environment and the second makes every ``uv run``
#: use it: fix round 8 measured that a jailed ``uv run`` failed with Permission
#: denied (exit 2) and an unjailed one installed the repository's dependencies
#: into the skill's environment, after round 7 (631bf9f, reverted) exported the
#: second from the codex MCP server. :func:`build_child_env` drops each one
#: that names the running interpreter's environment; a value naming any other
#: environment is the user's and stays. The same builder also takes the
#: environment's ``bin`` (``Scripts`` on Windows) off ``PATH``: uv puts it
#: first, and with neither name set and no ``.venv`` in the repository uv uses
#: the first ``python`` on ``PATH`` (fix round 9 measured ``uv pip install``
#: in an empty repository naming the skill's environment), and a runner's own
#: ``python``/``pytest`` resolved there too. No runner CLI lives in it.
SKILL_ENVIRONMENT_NAMES: Tuple[str, ...] = ("VIRTUAL_ENV", "UV_PROJECT_ENVIRONMENT")

#: Where a virtual environment keeps its executables: ``bin`` on POSIX,
#: ``Scripts`` on Windows.
SKILL_ENVIRONMENT_SCRIPT_DIRS: Tuple[str, ...] = ("bin", "Scripts")


def _same_path(left: str, right: str) -> bool:
    """Whether two directory spellings name one directory, as given or resolved."""
    for a, b in ((os.path.abspath(left), os.path.abspath(right)),
                 (os.path.realpath(left), os.path.realpath(right))):
        if os.path.normcase(a) == os.path.normcase(b):
            return True
    return False


def skill_environment_names(env: Mapping[str, str]) -> Tuple[str, ...]:
    """The names in ``env`` whose value is this interpreter's own virtual
    environment (``sys.prefix``), in :data:`SKILL_ENVIRONMENT_NAMES` order.

    Empty outside a virtual environment: then there is no environment of the
    skill's to keep a runner out of. A relative value is left alone, since uv
    resolves it against the child's own project.
    """
    own = sys.prefix
    if own == getattr(sys, "base_prefix", own):
        return ()
    return tuple(
        name for name in SKILL_ENVIRONMENT_NAMES
        if env.get(name) and os.path.isabs(env[name]) and _same_path(env[name], own)
    )


def _path_keys(env: Mapping[str, str]) -> Tuple[str, ...]:
    """The key(s) holding the search path: ``PATH``, or any spelling on Windows."""
    if os.name == "nt":
        return tuple(key for key in env if key.upper() == "PATH")
    return ("PATH",) if "PATH" in env else ()


def skill_environment_path(value: str) -> str:
    """``value`` (a ``PATH``) without the skill environment's script directory.

    Every entry that names ``sys.prefix``'s ``bin`` or ``Scripts``, as given or
    resolved, is dropped; every other entry stays, in order. Unchanged outside
    a virtual environment, where ``sys.prefix`` is the system's own
    installation and its ``bin`` is everyone's. Empty and relative entries are
    left alone: the child resolves them against its own working directory.
    """
    own = sys.prefix
    if own == getattr(sys, "base_prefix", own) or not value:
        return value
    scripts = [os.path.join(own, name) for name in SKILL_ENVIRONMENT_SCRIPT_DIRS]
    return os.pathsep.join(
        entry for entry in value.split(os.pathsep)
        if not (entry and os.path.isabs(entry)
                and any(_same_path(entry, directory) for directory in scripts))
    )


def _skill_environment_on_path(env: Mapping[str, str]) -> bool:
    """Whether ``env``'s ``PATH`` carries the skill environment's scripts."""
    return any(skill_environment_path(env[key]) != env[key] for key in _path_keys(env))


# ── the builder both lanes go through ────────────────────────────────────────


def _provider_removals(
    provider: Any,
    *,
    anchor: Optional[str] = None,
    base_env: Optional[Mapping[str, str]] = None,
) -> Tuple[str, ...]:
    """The adapter's removal list, asked with the dispatch's own context.

    :meth:`LLMProvider.get_remove_env` is a **policy** call for at least one
    adapter — claude-code resolves ``strip_vendor_keys`` / ``vendor_backend``
    through the normal config layering and decides against the environment the
    child will really inherit. Both of those are dispatch-scoped, so both have to
    reach it: an ``anchor``-less call resolves the policy against the *process
    anchor or the CWD* rather than the requested plan (the divergence A6 exists
    to close, one level down from the lanes), and a ``base_env``-less call
    reasons about ``os.environ`` while the builder composes something else.

    The call is signature-tolerant on purpose. An adapter whose removal list is
    static — most of them — declares ``get_remove_env(self)`` and takes no
    context, and this must keep working: the hook is duck-typed here
    (``provider: Any``), and refusing a zero-parameter override would turn a
    perfectly correct static list into a ``TypeError`` mid-dispatch. Each
    keyword is passed only to a hook that accepts it (or one taking ``**kwargs``).
    """
    hook = getattr(provider, "get_remove_env", None)
    if hook is None:
        return ()
    try:
        parameters = inspect.signature(hook).parameters
    except (TypeError, ValueError):  # pragma: no cover - builtins/C callables
        parameters = {}  # type: ignore[assignment]
    accepts_any = any(
        parameter.kind is inspect.Parameter.VAR_KEYWORD
        for parameter in parameters.values()
    )
    kwargs: Dict[str, Any] = {}
    if accepts_any or "anchor" in parameters:
        kwargs["anchor"] = anchor
    if accepts_any or "base_env" in parameters:
        kwargs["base_env"] = base_env
    return tuple(hook(**kwargs) or ())


def build_child_env(
    provider: Any,
    *,
    provider_env: Mapping[str, str],
    host_guards: Collection[str] = (),
    host_passthrough: Collection[str] = (),
    base_env: Optional[Mapping[str, str]] = None,
    anchor: Optional[str] = None,
) -> Optional[Dict[str, str]]:
    """The child environment for one spawn — the single construction (A6).

    Both spawn sites call exactly this: ``llm_client.call_llm`` for the Lane A
    fan-out (which passes no host guards, because a fan-out slot is a child of
    this process and not of the host's shell tool) and
    ``subagent_executor._spawn_in_context`` for the agent-profile lane (which
    passes the running host's ``env_guards``). A slot must never strip on one
    lane and inherit on the other, and after this function exists there is no
    ordering in which it can: the credential verdict, the removals and the
    allowlist are all computed here, once, from the adapter and the host entry.

    ``provider_env`` arrives already expanded (``expand_env_home``) from the
    spawn site — §2.5's rule that ``~`` is expanded before it reaches a child
    belongs to the two spawn sites, and ``tests/test_env_home_expansion.py``
    pins it there structurally.

    Returns ``None`` when nothing about the inherited environment changes, which
    is what lets ``subprocess`` inherit it directly — byte-identical to the
    behaviour before this function existed.
    """
    source = os.environ if base_env is None else base_env
    passthrough = set(host_passthrough)
    # The union, not the adapter's list alone (D3c): the adapter guards against
    # its own nesting marker, the host entry declares what *this* host injects
    # into every child. A name the host sanctions for the runner (`passthrough`)
    # is re-admitted last — but a host that sanctions a **vendor credential**
    # cancels the §2.1 strip on the agent-profile lane only, which is the
    # asymmetry A6 exists to close; see `hosts/capabilities.yaml`.
    #
    # The adapter is asked with **this dispatch's** anchor and the **composed**
    # source env, not with the process defaults: the strip is a policy read
    # (`strip_vendor_keys`, `vendor_backend`) over a set of names whose presence
    # is judged against what the child will really inherit, and both halves are
    # dispatch-scoped. See :func:`_provider_removals`.
    removals = [
        name
        for name in dict.fromkeys(
            [
                *_provider_removals(provider, anchor=anchor, base_env=source),
                *host_guards,
            ]
        )
        if name not in passthrough
    ]
    allowlist = env_allowlist_enabled(anchor)
    if (not provider_env and not removals and not allowlist
            and not skill_environment_names(source)
            and not _skill_environment_on_path(source)):
        return None
    if allowlist:
        env = apply_env_allowlist(source, getattr(provider, "name", ""))
    else:
        env = dict(source)
    env.update(provider_env)
    for key in removals:
        env.pop(key, None)
    # Last, so neither a delta nor a host passthrough can hand a runner the
    # skill's own environment (see SKILL_ENVIRONMENT_NAMES).
    for key in skill_environment_names(env):
        env.pop(key, None)
    for key in _path_keys(env):
        kept = skill_environment_path(env[key])
        if kept == env[key]:
            continue
        if kept:
            env[key] = kept
        else:
            # Nothing else was on it: the platform's default search path, not
            # an empty one (which a shell reads as "the current directory").
            env.pop(key)
    return env


# ─────────────────────────────────────────────────────────────────────────────
# §4.2.1 — the structured-output retry budget, pinned in the child env.
#
# It lives HERE rather than in ``utils/structured_output`` because an adapter's
# ``get_env`` is what emits it and an adapter may not import that module (it
# imports this one, and the reverse edge would be a cycle through
# ``utils.providers.__init__``). ``utils.structured_output`` re-exports both
# names, so there is one definition and no second copy of the number.
# ─────────────────────────────────────────────────────────────────────────────

#: The CLI's default is **5**, i.e. five *paid* model calls per invocation,
#: multiplied by the fan-out width and again by our own retry ladder. Set
#: explicitly so a vendor default change cannot silently re-inflate the bill.
#:
#: Measured 2026-08-16 (claude 2.1.233 at a localhost stub, zero paid tokens):
#: the variable caps **total** structured-output attempts, not repair calls on
#: top of the first one — ``=1`` produced exactly 1 request against a stub whose
#: tool input never validated, where the default produced 5.
MAX_STRUCTURED_OUTPUT_RETRIES = 1
STRUCTURED_OUTPUT_RETRY_ENV = "MAX_STRUCTURED_OUTPUT_RETRIES"

#: Declared usage-extraction fidelity (D3j), mirrored by ``runners[*].usage`` in
#: the D5b capability data. ``none`` is the honest default: an adapter with no
#: fixture-verified extractor is duration-only, never a promise of token counts.
USAGE_NONE = "none"
USAGE_PARTIAL = "partial"
USAGE_FULL = "full"

#: The two answers :meth:`LLMProvider.config_credential_source` may give (plan
#: opencode-validator-false-rate-limit-and-denied-turn §8.2). ``declared``: the
#: dispatch's own resolved config supplies the provider, so a ``False`` auth
#: probe is not a refusal and the auth state reads :data:`AUTH_STATE_CONFIG`.
#: ``unknown``: today's refusal stands. There is deliberately no third value.
CONFIG_AUTH_DECLARED = "declared"
CONFIG_AUTH_UNKNOWN = "unknown"

#: The preflight auth state for a provider admitted by its config declaration
#: rather than by a stored or environment credential.
AUTH_STATE_CONFIG = "config"


@dataclass(frozen=True)
class InternalRetryEnvelope:
    """What one vendor CLI does *inside* one awaited subprocess (§7.6(b)).

    §7.5's arithmetic needs one number per adapter, and before this declaration
    that number existed only in a plan's measurements. The retry ladder subtracts
    it in two places:

    * **rule 4** — an attempt is admitted only when what is left of the slot's
      deadline can hold one worst-case :attr:`max_wall_s`; otherwise the slot
      ends ``budget_exhausted`` with **no** child spawned, rather than a child
      being killed part-way through a retry chain the harness cannot see.
    * **rule 6(b)** — an adapter whose CLI already retries 429s internally
      (:attr:`retries_rate_limit`) gets **no** identical rate-limit re-dispatch:
      that would repeat a chain that already ran :attr:`max_requests` times
      against the same upstream, at the same price, for the same verdict.

    Every field is **measured, never inferred**. An adapter nobody measured
    declares ``None`` (:attr:`LLMProvider.internal_retries`), and §7.5 rule 6(c)
    reads that as *assume one request* — never *assume the worst*, which would
    fail slots that would have succeeded.

    The ladder reads :attr:`max_requests`, :attr:`max_wall_s` and
    :attr:`retries_rate_limit` **structurally** (``retry_ladder``'s
    ``InternalRetryEnvelopeLike`` Protocol), so this module is not importable
    from there and must not become so: the policy object stays pure and
    provider-free, and the structural read is the seam.
    """

    #: Requests the CLI may make to the upstream API inside one dispatch, at the
    #: configuration this harness actually runs (i.e. *including* whatever
    #: ``get_env`` pins). Never the CLI's out-of-the-box number when the adapter
    #: overrides it. ``None`` means no finite request bound is known; unlike
    #: an absent envelope, this can still declare measured internal retries.
    max_requests: Optional[int]

    #: The worst-case wall clock one dispatch may burn *inside* the child, in
    #: seconds. ``None`` means "no bound this adapter can state": rule 4 then
    #: performs no admission test, which is the honest posture — inventing a
    #: bound would refuse attempts that had budget for themselves.
    max_wall_s: Optional[float] = None

    #: Whether the CLI retries an HTTP 429 itself. ``False`` means the harness's
    #: own backoff is the only one a rate limit gets.
    retries_rate_limit: bool = False

    #: The env vars or config keys that change the numbers above — documentation
    #: for the human reading a budget, not a control surface. Empty means nothing
    #: reachable from here changes them.
    configurable_by: Tuple[str, ...] = ()


@dataclass(frozen=True)
class StructuredSchema:
    """One schema on its way to a CLI — the object, and where it was written.

    §4.2.2 asks for **one optional parameter and two transports**, and the two
    transports need different things: claude takes the schema *inline*
    (``--json-schema <json>``) while codex takes a *path*
    (``--output-schema <FILE>``). Handing the adapter a bare ``dict`` would serve
    only the first; handing it a bare path would serve only the second and would
    make the argv fixtures unreadable. So the caller hands over both halves in
    one value and each adapter picks the half it can carry.

    :attr:`path` is filled in by the **caller**, never by the adapter: adapters
    are module-level singletons in ``_PROVIDERS`` shared across a concurrent
    fan-out and cannot hold per-run state (the constraint that sank §4.1's T9).
    ``utils.structured_output.schema_sidecar`` is the one writer, and it removes
    the directory in a ``finally``.

    :attr:`name` is the schema **file** name. It is carried so every refusal and
    every WARN can name the file a human has to go and fix, rather than printing
    a schema body.
    """

    document: Dict[str, Any]
    path: Optional[str] = None
    name: str = "<inline>"

    def with_path(self, path: str) -> "StructuredSchema":
        """The same schema, now materialized at ``path``."""
        return StructuredSchema(document=self.document, path=path, name=self.name)


class StructuredOutputUnavailable(Exception):
    """A schema was handed to an adapter that cannot transport it (§4.2.1).

    Raised **before spawn**, so no partial argv reaches the CLI — §4.2.1's sixth
    acceptance case ("missing sidecar / schema file (codex)"). It is a
    configuration error, never a retryable failure: nothing about re-running the
    same dispatch would produce the missing file.
    """

    exit_code = 3

    def __init__(self, message: str, provider: str = "", schema: str = "") -> None:
        super().__init__(message)
        self.message = message
        self.provider = provider
        self.schema = schema


class ReadOnlyInvocationRefused(Exception):
    """The user's own configuration defeats an adapter's read-only invocation.

    Raised by ``build_command_for_transport`` **before spawn**, like
    :class:`StructuredOutputUnavailable`, and handled beside it in
    ``llm_client.invoke_with_provider``: a configuration error, never retried,
    because re-running the same dispatch reads the same file again. aider is
    the one raiser (plans/ask-answer-recovery-and-false-success.md D4.2): a
    ``yes-always`` in an ``.aider.conf.yml``, or ``AIDER_YES_ALWAYS`` in a
    ``.env`` aider loads, answers every confirmation "y" before aider reads the
    decline supply on stdin, and ``--yes-always`` has no negative form, so
    nothing on argv can turn it back off. ``path`` names the file a human has
    to edit; editing the user's config is not the adapter's job.
    """

    exit_code = 3

    def __init__(self, message: str, provider: str = "", path: str = "") -> None:
        super().__init__(message)
        self.message = message
        self.provider = provider
        self.path = path


class ProfileUnsupported(Exception):
    """This adapter cannot honor the requested invocation profile (D3e).

    Raised by :meth:`LLMProvider.build_agent_command`'s default implementation,
    so an adapter with no genuinely read-only (or edit-capable) mode is refused
    at dispatch with the adapter and profile named rather than being handed a
    fabricated command. ``utils/subagent_executor`` re-exports this name and
    classifies it as D3k rung 7 (``rejected``, no child started).
    """

    exit_code = 3

    def __init__(self, message: str, provider: str = "", profile: str = "") -> None:
        super().__init__(message)
        self.message = message
        self.provider = provider
        self.profile = profile


# ---------------------------------------------------------------------------
# M13 (§5.3) — per-adapter install / login / status metadata
# ---------------------------------------------------------------------------
#
# §5.3's rule is "probe by running the CLI's own *status subcommand*, never by
# reading a credential file", and this metadata is what lets a message say how
# to fix what such a probe found. Two of §5.3's four rows already shipped under
# their executor-facing names — `auth_check` **is** the status argv (D3c) and
# `login_cmd` **is** the login command, both already read by
# `subagent_executor._detect_auth` and by `describe_availability` — so this adds
# only the two that were missing (`install_hint`, `auth_hint`) and exposes all
# four through one record. Declaring `status_args`/`login_args` as second
# storage would give one fact two owners and let a probe drift from the refusal
# that names its fix.
#
# **No auto-install.** `install_hint` is a sentence a human reads; nothing in
# this repo executes it, and nothing may. Running a vendor installer because a
# probe came back `BINARY_MISSING` is the trust boundary §5.3 refuses to cross —
# it is the same boundary M16 was declined on.


@dataclass(frozen=True)
class SetupHints:
    """§5.3's four rows for one adapter: how to install, log in, and check.

    A *derived* view, never a second declaration: :attr:`status_args` and
    :attr:`login_args` are built from the adapter's own ``auth_check`` and
    ``login_cmd``, so this record cannot disagree with the argv the preflight
    really runs or with the fix a refusal really prints.

    Every field is safe to render into ``--init`` output, a log or a failure
    artifact: all four are adapter *declarations*, and no probe stdout, stderr
    or environment value reaches any of them.
    """

    #: How a human installs this CLI, verbatim. **Never executed.**
    install_hint: str = ""
    #: ``login_cmd`` as argv. Empty when the adapter declares no login command.
    login_args: Tuple[str, ...] = ()
    #: ``auth_check`` — the CLI's own status subcommand. Empty means this CLI
    #: offers none, and the auth state is then ``UNKNOWN``, never assumed good.
    status_args: Tuple[str, ...] = ()
    #: One sentence naming what this CLI's credential actually *is*, for the
    #: cases where "run the login command" is not the whole story.
    auth_hint: str = ""


# ---------------------------------------------------------------------------
# M10 (§5.1) — a typed availability status *beside* the bool
# ---------------------------------------------------------------------------
#
# `is_available()` is a bare `shutil.which` in all seventeen adapters, which
# collapses "not installed" / "logged out" / "too old" into one message. The
# fix is **additive**: a status type on a new method, with `is_available()`
# left alone. The donor's widened-return-type proposal (a bool-or-string union
# on the existing name) is rejected in §5.1 and is not what ships — every one
# of those strings is truthy, so `if provider.is_available():` would have
# silently started admitting a logged-out CLI.


class Availability(str, Enum):
    """Why a runner is or is not usable. For humans and pickers, never for dispatch.

    A ``str`` mixin rather than :class:`enum.StrEnum` because this package
    declares ``requires-python = ">=3.10"`` and ``StrEnum`` is 3.11+. The
    members compare equal to their wire strings either way, and ``__str__`` is
    pinned below so an interpolated member renders ``needs-auth`` rather than
    ``Availability.NEEDS_AUTH`` on every supported version.

    **Only :attr:`BINARY_MISSING` refuses a launch.** ``NEEDS_AUTH``,
    ``VERSION_TOO_LOW`` and ``UNKNOWN`` all still dispatch, because an auth or
    version problem must surface at run time carrying the CLI's own message
    rather than vanishing into a preflight refusal (D3c: *installed is not
    authenticated*). That is the whole compatibility rule, and it is one
    assertable line — see :meth:`LLMProvider.describe_availability`.
    """

    #: The binary resolves **and** a probe positively said it is usable.
    READY = "ready"
    #: The binary does not resolve. The only state that refuses a launch.
    BINARY_MISSING = "binary-missing"
    #: A probe positively recognised a login notice — the only positive auth
    #: verdict, and the only one drawn from a pattern match.
    NEEDS_AUTH = "needs-auth"
    #: A *read* version is below ``min_version``. A label, not a second launch
    #: gate: the refusal that uses this word is issued by the preflight's own
    #: version check, and it does not flow back into ``is_available()``.
    VERSION_TOO_LOW = "version-too-low"
    #: Inconclusive: no probe declared, no probe run, a timeout, or an
    #: unrecognised non-zero exit. The **fail-open** state, and mandatory
    #: rather than decorative — absence of evidence is never a negative
    #: verdict, and never a positive one either.
    UNKNOWN = "unknown"

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value


#: The retry-ladder statuses that carry an availability verdict. §5.1's rule is
#: that the two tri-states **map, they do not merge**: exactly one run status
#: says something about whether the CLI is usable at all, and it is the one
#: drawn from a positive login-notice match. Everything else a run can fail
#: with (a timeout, a 429, a parse failure) says nothing, and mapping it would
#: manufacture a verdict the CLI never gave.
AVAILABILITY_BY_STATUS: Dict[str, Availability] = {
    STATUS_AUTH_FAILED: Availability.NEEDS_AUTH,
}

#: The states worth naming in a failure message. ``READY`` adds nothing to a run
#: that just failed, and ``UNKNOWN`` is the state almost every un-probed adapter
#: is in, so printing either would be noise on every single failure.
NAMED_UNAVAILABILITY = (
    Availability.BINARY_MISSING,
    Availability.NEEDS_AUTH,
    Availability.VERSION_TOO_LOW,
)


def availability_from_failure(
    provider: "LLMProvider", stdout: str, stderr: str, exit_code: int = 0
) -> Optional[Availability]:
    """The availability verdict a **failed run's own streams** carry, or ``None``.

    §5.1's status-consumer leg, shared by the two ``describe_failure`` call
    sites (``llm_client`` and ``subagent_executor``) so they cannot render the
    same failure differently. It spawns nothing and probes nothing: the streams
    are already in the caller's hand, and :meth:`LLMProvider.classify_failure`
    is the one implementation of "what is this failure".

    ``None`` means *say nothing*, which is the answer for almost every failure.
    Only a state in :data:`NAMED_UNAVAILABILITY` comes back — a run that failed
    is not the moment to announce ``ready``, and ``unknown`` is the state every
    un-probed adapter sits in, so either would append noise to every message.
    """
    try:
        status = provider.classify_failure(stdout, stderr, exit_code)
    except Exception:  # noqa: BLE001 - a diagnostic may never break a failure path
        return None
    state = AVAILABILITY_BY_STATUS.get(status or "")
    return state if state in NAMED_UNAVAILABILITY else None


def _version_token(text: str) -> str:
    """The first dotted-numeric token in ``text``, or ``""``.

    Two jobs, and the second one is the load-bearing one. It normalizes a
    version read that carries trailing build noise (``2026.08.11-e8db854``,
    ``codex-cli 0.146.0``) so the comparison sees the number; and it is the
    **only** thing from this parameter that reaches an
    :class:`AvailabilityReport`'s ``detail``. ``describe_availability`` is a
    public method, so a caller can hand it any string — echoing that string back
    into a sentence bound for ``--init`` output, a log and a failure artifact
    would be a redaction hole opened by a diagnostic. A dotted numeric token
    cannot be a credential.
    """
    match = re.search(r"\b(\d+(?:\.\d+)*)\b", text or "")
    return match.group(1) if match else ""


def _version_below(version: str, minimum: str) -> bool:
    """``version < minimum``, through the one shared comparison.

    **M14 (§5.4) merged the twin away.** This used to carry its own copy of
    ``subagent_executor._version_tuple``'s component-wise parse, with a comment
    saying M14 owned the merge; it now calls :func:`version_tuple`, which is the
    single rule both the availability label here and the executor's preflight
    refusal are computed from. One rule, one owner — a build can no longer be
    "too old" for the refusal and fine for the report, and
    ``tests/test_version_gate.py`` pins the two against each other.
    """
    return version_tuple(version) < version_tuple(minimum)


@dataclass(frozen=True)
class AvailabilityReport:
    """One runner's availability verdict, plus the sentence a human reads.

    :attr:`detail` is composed **only from data the adapter declares** — its
    name, its ``auth_check`` argv, its ``login_cmd``, its ``min_version``, and
    the already-parsed version token. No probe stdout or stderr reaches it, by
    construction, which is what keeps it safe to put in ``--init`` output, a log
    or a failure artifact without a second redaction pass (§4.5.1).
    """

    state: Availability
    detail: str = ""

    @property
    def launchable(self) -> bool:
        """The launch gate, in one place.

        Everything but :attr:`Availability.BINARY_MISSING` dispatches. This is
        the right-hand side of the compatibility identity
        ``is_available() == describe_availability().launchable``.
        """
        return self.state is not Availability.BINARY_MISSING


def split_reasoning_effort(model: str, efforts: Collection[str]) -> Tuple[str, Optional[str]]:
    """Split an optional trailing ``:effort`` suffix off a model string.

    Returns ``(base_model, effort)`` when the substring after the LAST colon
    is a member of ``efforts`` and the part before it is non-empty; otherwise
    ``(model, None)`` and the model string passes through verbatim. Splitting
    on the last colon keeps model ids that legitimately contain colons (e.g.
    openrouter ``:free`` variants) intact unless the suffix is whitelisted.
    """
    base, _, suffix = model.rpartition(":")
    if base and suffix in efforts:
        return base, suffix
    return model, None


# ---------------------------------------------------------------------------
# M12 (§6.1) — the canonical reasoning-effort ladder
# ---------------------------------------------------------------------------
#
# Before this region every adapter carried a private ``REASONING_EFFORTS`` set
# with no shared vocabulary behind it, so the tree had no answer to "is ``off``
# the same rung as ``none``", "is ``ultra`` a rung at all" or "is ``thinking``
# weaker than ``high``". Each set is now *expressed through* one ladder instead
# of being restated beside it: an adapter declares which canonical rungs its CLI
# takes, what that CLI calls them locally, and which off-ladder names it must let
# through — and its ``REASONING_EFFORTS`` is **derived** from that declaration.
#
# Nothing about :func:`split_reasoning_effort` moves. It still takes an arbitrary
# ``Collection[str]`` and every adapter still hands it ``REASONING_EFFORTS``; the
# value is computed now rather than typed out, which is the whole difference.
#
# Three rules the plan states normatively, each measured, and each pinned by
# ``tests/test_reasoning_effort_ladder.py`` over the **registry** rather than
# over a list of adapter names:
#
#   1. Seven rungs, one total order, and nothing else joins it.
#   2. ``thinking``/``instant`` are a SECOND AXIS, not rungs (21 models each in
#      kilocode and opencode). They are accepted and passed through verbatim,
#      never compared to a rung and never coerced onto one — which is why
#      acceptance is "is this name accepted *here*", not "is it on the ladder".
#   3. ``none`` and ``minimal`` are taken on the wire by CLIs whose own catalogs
#      advertise neither. An unadvertised rung may be *passed through* when a
#      user names it, never *chosen* by a default or by a rung-down.
#
# The two alias pairs run in both directions and are per-provider *spellings*,
# never ladder members: ``off`` ≡ ``none`` (goose, pi, vibe) and ``ultra`` ≡
# ``max`` — outbound for muse, which has no ``max`` and wants the word ``ultra``,
# and inbound-only for codex, which takes ``max`` verbatim, so codex's own
# client-side ``ultra → max`` normalization is an unused backstop rather than a
# dependency.
#
# Caps are per MODEL, never per provider: ``max → xhigh`` is something a
# particular model's ``supported_reasoning_levels``/``variants`` list says, not
# something a provider name implies. :attr:`ReasoningLadder.model_caps` is where
# a measured per-model narrowing lives, including the one combination measured to
# hang forever rather than fail.

#: The canonical rungs, weakest → strongest. One vocabulary for every adapter.
REASONING_LADDER: Tuple[str, ...] = (
    "none",
    "minimal",
    "low",
    "medium",
    "high",
    "xhigh",
    "max",
)

#: Membership, for "is this name a rung at all" — asked separately from "does
#: this CLI accept it", because rule 2 turns on exactly that distinction.
LADDER_RUNGS = frozenset(REASONING_LADDER)

#: Rung → position, so "weaker than" and "one rung down" are arithmetic on a
#: shared order rather than a comparison between two adapters' private lists.
LADDER_POSITION: Dict[str, int] = {
    rung: index for index, rung in enumerate(REASONING_LADDER)
}

#: Rungs that CLIs accept on the wire while advertising them in no catalog
#: entry (rule 3). They stay in the accepted sets — the CLIs really do take
#: them — but :meth:`ReasoningLadder.rung_down` steps over them, because a rung
#: nothing advertises may never be the one the harness picks on a user's behalf.
UNADVERTISED_RUNGS = frozenset({"none", "minimal"})

#: Off-ladder names that select a *mode* rather than an amount of effort
#: (rule 2). Declared here so an adapter listing one is visibly declaring a
#: second-axis variant rather than inventing an eighth rung.
SECOND_AXIS_VARIANTS = frozenset({"thinking", "instant"})


@dataclass(frozen=True)
class ReasoningLadder:
    """One CLI's accepted effort vocabulary, expressed against the ladder.

    Every field is a *measurement* of what the CLI takes, never a preference.
    The mapping fields are tuples of pairs rather than dicts so the whole
    declaration stays immutable and hashable.

    :attr:`rungs`
        The canonical rungs this CLI accepts, stated in ladder order and emitted
        verbatim.
    :attr:`spellings`
        ``local name → canonical rung`` for a rung this CLI calls something else.
        Accepted **and emitted**: muse wants ``ultra`` where the ladder says
        ``max``; goose, pi and vibe want ``off`` where the ladder says ``none``.
    :attr:`inbound_aliases`
        ``local name → canonical rung`` accepted at the harness boundary and
        rewritten *before* argv is built, so the emitted value is always a name
        this adapter states. codex's ``ultra`` is the only entry.
    :attr:`variants`
        Off-ladder second-axis names (:data:`SECOND_AXIS_VARIANTS`) passed
        through verbatim.
    :attr:`model_caps`
        ``model id → the names accepted for that model``. An empty tuple means
        *no* effort value is safe on that model. This is the per-model half of
        §6.1 and the only place a cap may live.
    :attr:`declined`
        Non-empty when the CLI has no per-run effort mechanism at all. The
        reason, not a flag: four adapters are in this state and each is there
        for a different measured reason.
    """

    provider: str = ""
    rungs: Tuple[str, ...] = ()
    spellings: Tuple[Tuple[str, str], ...] = ()
    inbound_aliases: Tuple[Tuple[str, str], ...] = ()
    variants: Tuple[str, ...] = ()
    model_caps: Tuple[Tuple[str, Tuple[str, ...]], ...] = ()
    declined: str = ""

    # -- the declaration, read back ---------------------------------------

    @property
    def local_names(self) -> Dict[str, str]:
        """``spellings`` as a mapping: local name → canonical rung."""
        return dict(self.spellings)

    @property
    def aliases(self) -> Dict[str, str]:
        """``inbound_aliases`` as a mapping: local name → canonical rung."""
        return dict(self.inbound_aliases)

    @property
    def accepted(self) -> "frozenset":
        """Every name this CLI accepts **and may be handed back**.

        This is what an adapter's ``REASONING_EFFORTS`` is, and therefore what
        :func:`split_reasoning_effort` is called with. Inbound-only aliases are
        deliberately absent: they are accepted on a *spec* and rewritten, never
        emitted.
        """
        return frozenset(self.rungs) | set(self.local_names) | set(self.variants)

    @property
    def accepted_inbound(self) -> "frozenset":
        """:attr:`accepted` plus the inbound-only aliases — what a spec may say."""
        return self.accepted | set(self.aliases)

    @property
    def caps(self) -> Dict[str, Tuple[str, ...]]:
        """``model_caps`` as a mapping: model id → accepted names."""
        return dict(self.model_caps)

    # -- the questions the dispatch path asks ------------------------------

    def normalize(self, name: str) -> Optional[str]:
        """Which canonical rung ``name`` denotes, or ``None``.

        Answers "what rung is this word", independent of whether this CLI
        accepts it — a second-axis variant and an unknown word both answer
        ``None``, which is rule 2 in one line.
        """
        if name in LADDER_RUNGS:
            return name
        return self.local_names.get(name) or self.aliases.get(name)

    def render(self, rung: str) -> Optional[str]:
        """The word this CLI wants for canonical ``rung``, or ``None``.

        The canonical spelling wins whenever the CLI takes it (goose accepts
        both ``none`` and ``off`` and gets ``none``); the local spelling is used
        only where the canonical one is not accepted at all (muse has no ``max``
        and gets ``ultra``; pi and vibe have no ``none`` and get ``off``).
        """
        if rung in self.rungs:
            return rung
        for local, canonical in self.spellings:
            if canonical == rung:
                return local
        return None

    def accepted_for(self, model: Optional[str] = None) -> "frozenset":
        """:attr:`accepted`, narrowed by any declared cap for ``model``.

        ``model`` may carry its own ``:effort`` suffix; it is split off with the
        adapter's own inbound set first, so a caller can pass the spec it has.
        """
        if not model:
            return self.accepted
        base, _ = split_reasoning_effort(model, self.accepted_inbound)
        caps = self.caps
        if base in caps:
            return frozenset(caps[base]) & self.accepted
        return self.accepted

    def accepts(self, name: str, model: Optional[str] = None) -> bool:
        """Whether ``name`` may be handed to this CLI (for ``model``, if given)."""
        return name in self.accepted_for(model)

    def refuses_for_model(self, model: str, name: str) -> bool:
        """``name`` is fine for this provider but declared unsafe on ``model``."""
        return name in self.accepted and name not in self.accepted_for(model)

    def resolve(self, raw: str, model: Optional[str] = None) -> Optional[str]:
        """The value to emit for a requested ``raw`` effort — ``None`` to refuse.

        §6.1's coercion rule, exactly: an alias is applied **only when the raw
        value is unsupported but the canonical one is**. A name this CLI already
        accepts is therefore returned untouched, and a name that maps to no rung
        this CLI has is refused rather than being rounded onto a neighbour — a
        silent downgrade is the worse of the two failures, because the effort a
        run actually used is invisible in almost every CLI's output.
        """
        name = (raw or "").strip()
        if not name:
            return None
        allowed = self.accepted_for(model)
        if name in allowed:
            return name
        rung = self.normalize(name)
        if rung is None:
            return None
        spelled = self.render(rung)
        if spelled is not None and spelled in allowed:
            return spelled
        return None

    def rung_down(self, rung: str) -> Optional[str]:
        """The next weaker rung this CLI accepts — never an unadvertised one.

        Rule 3 lives here: ``none``/``minimal`` are reachable only by a user
        naming them, so a rung-down that runs out of advertised rungs returns
        ``None`` instead of stepping onto one.
        """
        position = LADDER_POSITION.get(rung)
        if position is None:
            return None
        for candidate in reversed(REASONING_LADDER[:position]):
            if candidate in self.rungs and candidate not in UNADVERTISED_RUNGS:
                return candidate
        return None


#: The declaration a provider makes when its CLI has no per-run effort
#: mechanism at all. Adapters in that state name their own reason; this exists
#: so :class:`LLMProvider`-adjacent code has a falsy default that is visibly
#: *undeclared* rather than visibly "declines".
NO_REASONING_LADDER = ReasoningLadder()


#: Terms that make a *bare* token a real failure signal rather than a
#: coincidence. A one-word pattern ("429", "unauthorized") is required to occur
#: near one of these — outside its own span — because on its own it appears in
#: places that say nothing about the run: opencode prints per-step costs
#: (``"cost":0.0429``), every runner prints token counts (``14290``), and a
#: review answer quotes the plan and diff under review ("the unauthorized branch
#: returns early").
_ERROR_CONTEXT = re.compile(
    r"http|status|code|error|err\b|response|fail|denied|forbidden|reject|"
    r"invalid|expired|exceeded|missing|quota|retry|throttl|too\s*many|rate|"
    r"limit|credential|login|log\s*in|sign\s*in|api[\s_-]*key|401|403|429|529"
)

#: How far either side of a bare-token match :data:`_ERROR_CONTEXT` is looked for.
_CONTEXT_WINDOW = 48

#: Compiled-pattern cache: the classifier runs on every failed dispatch.
_STREAM_PATTERNS: Dict[str, "re.Pattern[str]"] = {}


def stream_pattern(pattern: str) -> "re.Pattern[str]":
    """Compile one classifier substring into a boundary-aware regex.

    A textual pattern keeps a left word boundary while staying a prefix match on
    the right — "rate limit" must still recognize "rate limits" and
    "rate-limited" — and any run of separators inside the pattern matches any run
    of separators in the stream, so one entry covers ``rate limit``,
    ``rate-limit`` and ``ratelimit`` alike. A numeric pattern (an HTTP status
    code) must additionally stand alone as a token, so ``429`` is not found
    inside ``0.0429`` or ``14290``.

    Patterns are matched against a lowercased haystack, so the compiled regex is
    lowercase and carries no ``IGNORECASE`` flag.
    """
    token = (pattern or "").strip().lower()
    cached = _STREAM_PATTERNS.get(token)
    if cached is not None:
        return cached
    if token.isdigit():
        regex = re.compile(rf"(?<![\w.]){token}(?![\w.])")
    else:
        body = re.sub(r"(?:\\?[ _\-])+", r"[\\s_\\-]*", re.escape(token))
        regex = re.compile(rf"(?<![a-z0-9]){body}")
    _STREAM_PATTERNS[token] = regex
    return regex


def _needs_context(token: str) -> bool:
    """Whether ``token`` is too bare to classify a run on its own.

    A multi-word phrase ("not logged in", "too many requests", "quota_exceeded")
    is specific enough to stand alone; a single token ("429", "unauthorized",
    "overloaded") is not, because it occurs inside numbers and inside the prose a
    runner prints about somebody else's code.
    """
    return re.search(r"[\s_\-]", token) is None


def matches_any(patterns: Collection[str], haystack: str) -> bool:
    """Whether any declared classifier pattern really occurs in ``haystack``.

    This is the whole difference between the executor classifying a run and
    guessing at one: the D3k ladder consults
    :meth:`LLMProvider.classify_failure` for a run with no usable result, and a
    bare ``pattern in haystack`` test moves such a run onto a rung with different
    retry rules than the one it belongs on — ``rate_limited`` is retried *without*
    consuming the retry budget, ``auth_failed`` fails the entire batch.
    """
    for pattern in patterns:
        token = (pattern or "").strip().lower()
        if not token:
            continue
        regex = stream_pattern(token)
        bare = _needs_context(token)
        for match in regex.finditer(haystack):
            if not bare:
                return True
            window = "\n".join((
                haystack[max(0, match.start() - _CONTEXT_WINDOW):match.start()],
                haystack[match.end():match.end() + _CONTEXT_WINDOW],
            ))
            if _ERROR_CONTEXT.search(window):
                return True
    return False


# ---------------------------------------------------------------------------
# The one failure classifier (§7.2, §7.1.a)
#
# Everything below is *new* data for categories the adapter pattern sets never
# covered. The two declared sets — ``auth_error_patterns`` and
# ``rate_limit_patterns`` — and the matcher above are **not** touched: they were
# audited on 2026-08-16 and measured clean (``stream_pattern`` gives a numeric
# token its own boundaries, and a bare token additionally needs an
# ``_ERROR_CONTEXT`` word within 48 characters), with
# ``tests/test_providers.py::TestClassifyFailure`` pinning it. This section adds
# categories beside them, and then makes every other classifier in the tree call
# this one instead of growing its own.
#
# The new tables are **regexes**, not substrings, because §7.2 asks for regexes
# ("maximum context length is N tokens") and because a regex states its own
# boundaries: ``\bthrottl(?:ed|ing)\b`` needs no context window to be safe,
# whereas the bare token ``throttled`` handed to ``matches_any`` would.
# ---------------------------------------------------------------------------

#: Categories the ladder has no status for. They exist so the ``Reason:`` line a
#: user acts on and the retry decision can be read off the *same* verdict —
#: §7.1.a's seven-branch ``elif`` chain is a lookup on these.
CATEGORY_CONNECTION_ERROR = "connection_error"
CATEGORY_SERVER_ERROR = "server_error"
CATEGORY_INVALID_MODEL = "invalid_model"
CATEGORY_PERMISSION_DENIED = "permission_denied"
#: The runner's *own* OS sandbox could not start (D6). Deliberately the same
#: string as ``retry_ladder.STATUS_SANDBOX_UNAVAILABLE`` — like
#: ``CATEGORY_INVALID_MODEL``, an alias for a word already in the vocabulary —
#: so it reaches the ladder under its own name, at rung 1: a property of the
#: machine, not of the turn, and every sibling on that runner fails identically.
CATEGORY_SANDBOX_UNAVAILABLE = "sandbox_unavailable"

#: §7.2's retryable-code allowlist, shared across both harnesses. Auth is
#: deliberately absent (no retry fixes a logged-out CLI) and so is
#: :data:`STATUS_CONTEXT_LENGTH_EXCEEDED`: until §7.6(a) ships a prompt splitter,
#: re-dispatching an oversized prompt unchanged spends budget to reproduce the
#: same error. Open question 13 owns the splitter; this frozenset owns the fact
#: that nothing may retry it in the meantime.
RETRYABLE_FAILURE_CATEGORIES = frozenset({
    STATUS_RATE_LIMITED,
    STATUS_TIMEOUT,
    CATEGORY_CONNECTION_ERROR,
    CATEGORY_SERVER_ERROR,
})

#: A shell reports "could not execute what you asked for" as 127, on every
#: POSIX shell and through every wrapper script. It is the one launch verdict
#: that needs no text at all.
MISSING_BINARY_EXIT_CODE = 127


def _markers(*patterns: str) -> Tuple["Pattern[str]", ...]:
    """Compile one classifier table. Haystacks are lowercased before matching."""
    return tuple(re.compile(p) for p in patterns)


def _matches_marker(markers: Collection["Pattern[str]"], haystack: str) -> bool:
    return any(marker.search(haystack) for marker in markers)


#: Root-cause launch failures, ordered **before** the auth patterns (§7.2). A
#: sandbox that refused the exec, or a shim that could not find the binary,
#: prints text that reads like a permission or credential problem — and reading
#: it as ``auth_failed`` is expensive twice over, because rung 1 fails the whole
#: batch and because the actual fix (install the CLI, grant the exec) is never
#: mentioned. Each tuple is ``(category, markers)`` and the first match wins.
#:
#: The markers are deliberately specific phrases rather than the bare
#: ``'not found'`` Lane A used: that one called **every** provider's failure
#: "cursor-agent command not found", and it swallowed "model not found" too.
#: bubblewrap's own words when it cannot start (D6). Measured on a stock Ubuntu
#: 24.04 (``kernel.apparmor_restrict_unprivileged_userns=1``, no AppArmor
#: profile granting ``/usr/bin/bwrap`` the ``userns`` right):
#: ``bwrap: loopback: Failed RTM_NEWADDR: Operation not permitted`` under
#: ``--unshare-net``, ``bwrap: setting up uid map: Permission denied`` without.
#: codex and muse both sandbox through bubblewrap, so both die on these lines
#: before any model is reached. The table is consulted **first** of the launch
#: tuple, because the same lines also say "permission denied" / "operation not
#: permitted" and would otherwise land on ``permission_denied`` — a per-task
#: verdict, where this one is fatal to the batch and names a machine repair
#: (``multi_llm.py doctor``). The haystack is lowercased before matching and is
#: ``stdout\nstderr``, so the anchor is multiline and the words are lowercase.
SANDBOX_MARKERS = _markers(
    r"(?m)^bwrap: ",
    r"bubblewrap",
    r"failed rtm_newaddr",
    r"setting up uid map: permission denied",
)

#: A non-zero exit from a ``sandbox_probe_command`` that says nothing about the
#: sandbox: the CLI did not understand the probe. Measured on codex — a build
#: without the ``sandbox`` subcommand reads the argv as an interactive prompt
#: and dies on ``Error: stdin is not a terminal``; clap's own refusals are the
#: ``unrecognized subcommand`` / ``unexpected argument`` lines. The preflight
#: records these ``unknown`` and dispatches, exactly like a probe that timed
#: out: refusing a runner because it is *older* than the probe would turn a
#: diagnostic into a version gate the adapter never declared.
SANDBOX_PROBE_INCONCLUSIVE_MARKERS = _markers(
    r"unrecognized subcommand",
    r"unknown subcommand",
    r"unexpected argument",
    r"stdin is not a terminal",
)


def sandbox_probe_inconclusive(text: str) -> bool:
    """Whether a failed sandbox probe's output says the CLI did not run it."""
    return _matches_marker(SANDBOX_PROBE_INCONCLUSIVE_MARKERS, (text or "").lower())


LAUNCH_FAILURE_MARKERS: Tuple[Tuple[str, Tuple["Pattern[str]", ...]], ...] = (
    (CATEGORY_SANDBOX_UNAVAILABLE, SANDBOX_MARKERS),
    (STATUS_SPAWN_FAILED, _markers(
        r"command not found",
        r"executable file not found",
        r"\bbinary not found\b",
        r"not found in \$?path\b",
        r"is not recognized as an internal or external command",
        r"cannot execute binary file",
        r"\bexec format error\b",
        # omp 18.2.2, both measured, both exit 1 at **zero requests** because
        # the CLI validates its own argv and its config overlay before it
        # resolves a model: a rejected `--tools` name raises `CliUsageError`,
        # and a `--config` path that does not resolve is `error: Config overlay
        # not found: <abs path>` in 0.13 s. Neither is a failed *spawn* in the
        # literal sense — the binary ran — but the disposition is the one this
        # rung exists for: a property of the install, identical for every
        # sibling slot on that runner, and no retry can fix it. The alternative
        # was `None`, which offers a transport retry of a run that cannot
        # change its mind.
        # Lowercase, like every other row here: `_markers` compiles without
        # re.I and `classify_streams` lowercases the haystack first.
        r"\bcliusageerror\b",
        # omp 18.8.3's plain refusal (below, STDERR_LAUNCH_FAILURE_MARKERS) as
        # Lane A hands it over: that lane classifies its own
        # `"<cli> exited with code N: <describe_failure>"` sentence as stdout
        # (`llm_client`'s `error_message`), and omp's `describe_failure` puts
        # the stderr line first, so the refusal sits right after that prefix
        # at the very start of the haystack — where no CLI's own stdout, and
        # no model's answer, starts.
        r"\A[\w.-]+ exited with code -?\d+: error: unknown tools? in --tools\b",
        r"config overlay not found",
    )),
    (CATEGORY_PERMISSION_DENIED, _markers(
        r"permission denied",
        r"operation not permitted",
        r"\beacces\b",
        r"\beperm\b",
    )),
)

#: Launch-failure rows read on **stderr only**, each at the start of a line,
#: consulted beside :data:`LAUNCH_FAILURE_MARKERS`' row of the same category.
#: A phrase a model's answer can quote does not belong in the shared haystack:
#: rung 1 fails the whole batch, and a failed run's stdout is often that answer
#: (a reviewer reading this repo's own omp fixtures quotes this one). omp
#: 18.8.3 (measured 2026-10-08, tests/fixtures/omp/invalid-tool) refuses a bad
#: ``--tools`` name, exit 2, with ``Error: Unknown tool in --tools: bogus.``
#: (``Unknown tools in --tools: a, b.`` for two) opening its stderr, no Bun
#: trace and no ``CliUsageError`` word, so ``\bcliusageerror\b`` no longer
#: reaches it (review 24, pins #5).
STDERR_LAUNCH_FAILURE_MARKERS: Dict[str, Tuple["Pattern[str]", ...]] = {
    STATUS_SPAWN_FAILED: _markers(
        r"(?m)^error: unknown tools? in --tools\b",
    ),
}

#: Per-vendor context-overflow shapes (§7.2). These are the *only* thing that
#: may produce :data:`STATUS_CONTEXT_LENGTH_EXCEEDED`, because that status is
#: terminal: a false positive fails a slot that a retry would have completed.
#: Lane A's ``'context' in str(error)`` matched ``context_mode``, "in this
#: context" and any prose quoting a plan's Context section; every regex here
#: carries the numbers or the verb that make it a real overflow report.
CONTEXT_OVERFLOW_MARKERS = _markers(
    # OpenAI: "This model's maximum context length is 128000 tokens. However,
    # your messages resulted in 214537 tokens."
    r"maximum context length",
    r"\bcontext[_ ]length[_ ]exceeded\b",
    r"reduce the length of the messages",
    # Anthropic: "prompt is too long: 248113 tokens > 200000 maximum"
    r"prompt is too long",
    # Gemini: "The input token count (1093122) exceeds the maximum number of
    # tokens allowed (1048576)."
    r"input token count\s*\(?\d+\)?\s*exceeds",
    # The shapes several gateways normalise the three above onto. `effective`
    # is goose 1.53.0's own compaction report (tests/fixtures/goose/
    # context-overflow, measured 2026-10-08): "Failed to compact: the base
    # prompt … exceeds the model's effective context window …", which goose
    # writes as a text part with no error `kind`, so this row is what reaches
    # it. One optional word, so no new prose shape matches.
    r"exceeds the (?:model'?s )?(?:maximum |effective )?context (?:window|length)",
    r"context window (?:of \d+ tokens )?exceeded",
    r"\btoo many tokens\b",
    # Mistral Vibe, measured at 2.24.1: "The conversation context exceeds the
    # model's maximum limit. Use /rewind ...". The row above does not reach it --
    # vibe puts the noun first and calls the bound a "limit" rather than a
    # "window" or a "length" -- and without this the run classifies as
    # transport-shaped and burns the executor's whole bounded-retry path on a
    # condition no retry can fix. "conversation context" is what keeps it off
    # prose: an answer discussing a plan's Context section does not say it.
    r"conversation context exceeds",
    # aider, measured at 0.86.2 on the 2026-08-19 fixture capture: it SWALLOWS
    # litellm's ContextWindowExceededError and prints its own help instead, so
    # not one marker above appears anywhere in the run --
    #     "Model openai/stub-model has hit a token limit!"
    #     "Input tokens: ~103 of 0 -- possibly exhausted context window!"
    # The upstream 400's wording never reaches stdout at all. Without these two
    # the row classified as None, i.e. transport-shaped, and the executor spent
    # its whole bounded-retry budget on the one condition §7.2 calls terminal.
    # Both phrasings are specific enough to stay off prose: an answer discussing
    # token budgets does not say "has hit a token limit" or "exhausted context
    # window", and `_markers` anchors on the error context regardless.
    r"hit a token limit",
    r"exhausted context window",
)

#: Rate-limit shapes the adapters' declared English set does not carry, kept
#: here rather than added to it: a bare ``throttled`` handed to
#: :func:`matches_any` would need an ``_ERROR_CONTEXT`` word within 48
#: characters, and the measured phrasing ("Request was throttled") has none. A
#: regex states its own boundary and needs no window — which is why this is a
#: separate table and not an edit to the audited-clean adapter set.
SHARED_RATE_LIMIT_MARKERS = _markers(
    r"\bthrottl(?:ed|ing)\b",
    r"\bquota[ _-]?limit\b",
    r"\busage limit (?:reached|exceeded)\b",
    # gRPC / Connect-RPC status 8, ``RESOURCE_EXHAUSTED``: "some resource has
    # been exhausted, perhaps a per-user quota". cursor-agent speaks Connect-RPC
    # to its backend and relays the code by name. Measured 2026-09-17 on
    # ``cursor-agent:kimi-k3-high``: three ``Connection lost, reconnecting to
    # https://agentn.global.api5.cursor.sh (attempt N)...`` lines and then
    # ``RetriableError: [resource_exhausted] Error`` on stderr, exit 1, zero
    # bytes on stdout, 23.7 s — and no table above matched a word of it, so the
    # slot was recorded as a bare "exited with code 1" (its ``Connection lost``
    # is not a ``CONNECTION_ERROR_MARKERS`` shape either). The CLI names the
    # error retriable itself; this is the rung that retries.
    r"\bresource[_ ]exhausted\b",
)

#: A wall-clock cutoff, wherever it was imposed. Checked before the connection
#: table on purpose: "connection timed out" is a timeout, and
#: ``validation.py``'s persisted vocabulary has always classified it that way.
TIMEOUT_MARKERS = _markers(
    r"\btimed out\b",
    r"\btime[ _-]?out\b",
    r"deadline exceeded",
    r"\betimedout\b",
)

CONNECTION_ERROR_MARKERS = _markers(
    # **Separable on purpose — this row's widening plus its two fixture re-pins
    # are the whole change, and they land as their own commit**, not folded into
    # the adapter work that found them. Its file list is this row,
    # ``tests/fixtures/cline/manifest.yaml``'s ``zero-body`` row (with the
    # matching item 4 of ``tests/fixtures/cline/README.md``) and
    # ``tests/fixtures/omp/manifest.yaml``'s ``empty`` row — no adapter module,
    # and no other provider's verdict (``"connection was"`` greps to those two
    # fixture trees and this line only; the whole grader run confirms it). It is
    # ``plans/add-omp-provider.md``'s follow-up item 1, deferred there for
    # exactly this reason: re-pinning a committed verdict belongs to whoever
    # reviews that provider, so it is put where they can read it on its own
    # terms. If it is ever squashed into a larger commit, that commit's message
    # names the cline re-pin, because the moved verdict — not the regex — is the
    # part a reviewer has to agree with.
    #
    # ``(?:was )?`` is one word wide, and it is there because two adapters emit
    # the SAME Bun/undici sentence for a server that accepted the request and
    # then closed the socket after ZERO body bytes — "The socket connection was
    # closed unexpectedly …" — which the unwidened row missed for the single
    # reason that it says "connection **was** closed". cline's committed
    # `zero-body` row carries it on stderr with `(ECONNRESET)` appended (exit 1,
    # 3 requests over 7.85 s); omp's `empty` row carries it as a terminal
    # `stopReason: "error"` with **no** `errorStatus` (exit 1, 21 requests over
    # 31.9 s). A dropped socket is exactly what this row means, so the widening
    # is a better reading of the same bytes rather than a behaviour change in
    # either CLI. Taken 2026-09-18, with both fixture manifests re-pinned in the
    # same change: cline `runner_error` → `connection_error` (it had been
    # falling through to `exit_zero_markers`, the rung below this one) and omp
    # `None` → `connection_error`.
    #
    # Measured on those same bytes, what moves downstream is the `Reason:` line
    # — "the runner reported a failure" and "Unknown (see tail output below)"
    # both become "Connection/network error" — and, for omp alone, Lane A's
    # retry decision. Lane A classifies its own `"<cli> exited with code N:
    # <describe_failure>"` string rather than the streams: omp's
    # `describe_failure` quotes the sentence into it, so that slot goes from
    # `None` ("never retried") to one transport retry, while cline declares no
    # `describe_failure` at all, so its Lane A string stays the bare exit line
    # and its retry behaviour is byte-for-byte what it was. Lane B is unmoved
    # for both: its re-classification hook only upgrades a slot to auth, rate
    # limit, invalid model or sandbox, and `connection_error` is none of those.
    r"connection (?:was )?(?:refused|reset|closed|aborted|error|failed)",
    r"could not connect",
    r"unable to connect",
    r"failed to connect",
    r"network is unreachable",
    r"no route to host",
    r"temporary failure in name resolution",
    r"name or service not known",
    r"\bgetaddrinfo\b",
    r"\becconnrefused\b",
    r"\benotfound\b",
    r"\bdns\b.*\bfail",
)

SERVER_ERROR_MARKERS = _markers(
    r"\b5\d{2}\b\s*(?:internal|server|bad gateway|service|gateway)",
    r"internal server error",
    r"service unavailable",
    r"bad gateway",
    r"gateway time",
    r"\bupstream error\b",
    r"\bapi error\b",
    r"\bserver error\b",
)

#: "The model you named does not exist / is not available to this account."
#: Its own category because the fix is a config edit, never a retry.
INVALID_MODEL_MARKERS = _markers(
    r"model not found",
    r"\bmodel_not_found\b",
    r"invalid model",
    r"unknown model",
    r"\bmodel .{0,40}(?:does not exist|is not available)",
    r"unsupported model",
    # omp 18.2.2, measured pre-flight against its own local catalog:
    # `Model "stub/nonexistent" not found` — exit 1, zero bytes on stdout, zero
    # requests. The existing `model not found` row does not reach it because the
    # quoted selector sits between the two words, and `\bmodel .{0,40}…` wants a
    # different verb. Written with the quotes optional and the gap bounded, so
    # the row is the shape ("model <name> not found") rather than one vendor's
    # punctuation — a cost line or a token count cannot satisfy it.
    r"\bmodel [\"'`]?[\w./:-]{1,60}[\"'`]? not found",
)


def classify_streams(
    stdout: str,
    stderr: str,
    exit_code: int = 0,
    *,
    auth_patterns: Optional[Collection[str]] = None,
    rate_limit_patterns: Optional[Collection[str]] = None,
    exit_zero_markers: Collection["Pattern[str]"] = (),
) -> Optional[str]:
    """Classify one captured run. **The** implementation, for both lanes (§7.2).

    Returns a status from :mod:`utils.retry_ladder`'s vocabulary, one of the
    ``CATEGORY_*`` names above, or ``None`` for "nothing recognized" — which the
    caller must read as *transport-shaped*, never as "fine".

    The order is the whole design, and each step earns its place:

    1. ``exit_code == 127`` — the shell's own "I could not run that".
    2. :data:`LAUNCH_FAILURE_MARKERS` — root cause **before** auth (§7.2), since
       a refused exec prints text that reads like a credential problem.
    3. :data:`CONTEXT_OVERFLOW_MARKERS` — terminal and unambiguous, and it must
       not be laundered into a retryable category by a later table.
    4. auth, then rate limit — the existing order, pinned by
       ``TestClassifyFailure::test_auth_wins_over_a_rate_limit_in_the_same_stream``:
       misreading a logged-out CLI as a rate limit retries what cannot be fixed.
    5. timeout, connection, **invalid model, then server** — the rest of the
       allowlist. Invalid-model is consulted **before** server-error, and the
       pair is the one step of this ladder that did not earn its original
       order (C2). ``\\bapi error\\b`` sits in :data:`SERVER_ERROR_MARKERS`,
       so a 404 that correctly *names the model* used to land on
       ``server_error`` — a **retryable** category — and burn the retry budget
       on a terminal condition. A model-named 404 is strictly more specific
       than "api error", so the specific table is asked first. Measured on
       ``claude-code``, ``grok``, ``muse`` and ``vibe``; pinned by
       ``TestClassifyLadderOrder``.
    6. the adapter's own exit-0 marker, last: it says only "this run failed",
       so anything more specific must have had its chance first.

    ``auth_patterns``/``rate_limit_patterns`` default to :class:`LLMProvider`'s
    declared sets, which is what lets a caller with no adapter in hand — Lane A's
    ``_format_failure_details``, ``validation.py`` — get the same verdict as one
    with an adapter. Both are matched through :func:`matches_any`, never as raw
    substrings.
    """
    haystack = f"{stdout or ''}\n{stderr or ''}".lower()

    if exit_code == MISSING_BINARY_EXIT_CODE:
        return STATUS_SPAWN_FAILED

    if not haystack.strip():
        return None

    stderr_lower = (stderr or "").lower()
    for category, markers in LAUNCH_FAILURE_MARKERS:
        if _matches_marker(markers, haystack) or _matches_marker(
            STDERR_LAUNCH_FAILURE_MARKERS.get(category, ()), stderr_lower
        ):
            return category

    if _matches_marker(CONTEXT_OVERFLOW_MARKERS, haystack):
        return STATUS_CONTEXT_LENGTH_EXCEEDED

    auth = (
        LLMProvider.auth_error_patterns if auth_patterns is None else auth_patterns
    )
    if matches_any(auth, haystack):
        return STATUS_AUTH_FAILED

    rate = (
        LLMProvider.rate_limit_patterns
        if rate_limit_patterns is None
        else rate_limit_patterns
    )
    if matches_any(rate, haystack) or _matches_marker(
        SHARED_RATE_LIMIT_MARKERS, haystack
    ):
        return STATUS_RATE_LIMITED

    if _matches_marker(TIMEOUT_MARKERS, haystack):
        return STATUS_TIMEOUT
    if _matches_marker(CONNECTION_ERROR_MARKERS, haystack):
        return CATEGORY_CONNECTION_ERROR
    if _matches_marker(INVALID_MODEL_MARKERS, haystack):
        return CATEGORY_INVALID_MODEL
    if _matches_marker(SERVER_ERROR_MARKERS, haystack):
        return CATEGORY_SERVER_ERROR

    if _matches_marker(exit_zero_markers, haystack):
        # The exit code carried no verdict (goose, aider, cursor-agent and cline
        # all exit 0 on a provider failure), and the adapter's own marker is the
        # only thing that says this run failed at all.
        return STATUS_RUNNER_ERROR

    return None


@dataclass(frozen=True)
class StreamMatch:
    """Where :func:`match_streams` found the text that decided a verdict.

    ``channel`` is ``"stdout"`` or ``"stderr"`` and ``offset`` indexes that
    channel's own **lowered** text (never the joined haystack). All three are
    ``None`` for the two steps that decide without a pattern: exit 127 and the
    adapter's ``exit_zero_markers``.
    """

    status: str
    pattern: Optional[str] = None
    channel: Optional[str] = None
    offset: Optional[int] = None


def _first_pattern_match(
    patterns: Collection[str], haystack: str
) -> Optional[Tuple[str, int]]:
    """:func:`matches_any`'s walk, returning the pattern and offset it accepted.

    The same order, the same boundary regex and the same bare-token context
    rule; only the return value differs, so the two cannot disagree about
    *whether* a haystack matches.
    """
    for pattern in patterns:
        token = (pattern or "").strip().lower()
        if not token:
            continue
        regex = stream_pattern(token)
        bare = _needs_context(token)
        for match in regex.finditer(haystack):
            if not bare:
                return token, match.start()
            window = "\n".join((
                haystack[max(0, match.start() - _CONTEXT_WINDOW):match.start()],
                haystack[match.end():match.end() + _CONTEXT_WINDOW],
            ))
            if _ERROR_CONTEXT.search(window):
                return token, match.start()
    return None


def _first_marker_match(
    markers: Collection["Pattern[str]"], haystack: str
) -> Optional[Tuple[str, int]]:
    """:func:`_matches_marker`'s walk, returning the regex source and offset."""
    for marker in markers:
        found = marker.search(haystack)
        if found:
            return marker.pattern, found.start()
    return None


def match_streams(
    stdout: str,
    stderr: str,
    exit_code: int = 0,
    *,
    auth_patterns: Optional[Collection[str]] = None,
    rate_limit_patterns: Optional[Collection[str]] = None,
    exit_zero_markers: Collection["Pattern[str]"] = (),
) -> Optional[StreamMatch]:
    """:func:`classify_streams`'s verdict **plus where it matched**. Quote-only.

    Additive beside :func:`classify_streams`, which is untouched: the same
    parameters, the same steps in the same order, and ``match.status`` always
    equals what :func:`classify_streams` returns for the same arguments
    (``tests/test_providers.py::TestMatchStreams`` pins it over every
    ``classify_streams`` case in the suite). What it adds is the pattern that
    fired and its position, so ``subagent_executor._classify_failed_run`` can
    quote the text that actually decided a verdict instead of a stream tail
    that may not contain it (the b38de8bb run quoted a stderr line with no
    rate limit in it).

    **Nothing classifies through this.** Not ``validation.py``, not
    ``_format_failure_details``, not any adapter's ``classify_failure`` — the
    verdict is always :func:`classify_streams`' (through
    :meth:`LLMProvider.classify_failure`), and this is re-run afterwards for
    the quote alone. Like :func:`classify_streams` it is adapter-free: it never
    applies :meth:`LLMProvider.vendor_text`; the caller hands it text that is
    already reduced.

    ``offset`` is into the matched channel's own lowered text. The joined
    haystack is ``stdout + "\\n" + stderr``, so an offset below
    ``len(stdout)`` is on stdout and anything past the joiner is rebased onto
    stderr.
    """
    out_lower = (stdout or "").lower()
    haystack = f"{stdout or ''}\n{stderr or ''}".lower()

    if exit_code == MISSING_BINARY_EXIT_CODE:
        return StreamMatch(STATUS_SPAWN_FAILED)

    if not haystack.strip():
        return None

    def _found(status: str, hit: Tuple[str, int]) -> StreamMatch:
        pattern, offset = hit
        if offset < len(out_lower):
            return StreamMatch(status, pattern, "stdout", offset)
        return StreamMatch(
            status, pattern, "stderr", max(0, offset - len(out_lower) - 1)
        )

    err_lower = (stderr or "").lower()
    for category, markers in LAUNCH_FAILURE_MARKERS:
        hit = _first_marker_match(markers, haystack)
        if hit is not None:
            return _found(category, hit)
        hit = _first_marker_match(
            STDERR_LAUNCH_FAILURE_MARKERS.get(category, ()), err_lower
        )
        if hit is not None:
            return StreamMatch(category, hit[0], "stderr", hit[1])

    hit = _first_marker_match(CONTEXT_OVERFLOW_MARKERS, haystack)
    if hit is not None:
        return _found(STATUS_CONTEXT_LENGTH_EXCEEDED, hit)

    auth = (
        LLMProvider.auth_error_patterns if auth_patterns is None else auth_patterns
    )
    hit = _first_pattern_match(auth, haystack)
    if hit is not None:
        return _found(STATUS_AUTH_FAILED, hit)

    rate = (
        LLMProvider.rate_limit_patterns
        if rate_limit_patterns is None
        else rate_limit_patterns
    )
    hit = _first_pattern_match(rate, haystack) or _first_marker_match(
        SHARED_RATE_LIMIT_MARKERS, haystack
    )
    if hit is not None:
        return _found(STATUS_RATE_LIMITED, hit)

    for status, markers in (
        (STATUS_TIMEOUT, TIMEOUT_MARKERS),
        (CATEGORY_CONNECTION_ERROR, CONNECTION_ERROR_MARKERS),
        (CATEGORY_INVALID_MODEL, INVALID_MODEL_MARKERS),
        (CATEGORY_SERVER_ERROR, SERVER_ERROR_MARKERS),
    ):
        hit = _first_marker_match(markers, haystack)
        if hit is not None:
            return _found(status, hit)

    if _matches_marker(exit_zero_markers, haystack):
        return StreamMatch(STATUS_RUNNER_ERROR)

    return None


def context_length_message(model: str) -> str:
    """The §7.6(a) sentence a slot fails with, recorded verbatim in the report.

    Not a placeholder for the splitter: open question 13 owns that design, and
    until it is answered the shipping behaviour is to classify the condition,
    name it, and fail the slot with the two remedies a human can actually apply.
    """
    return (
        f"the prompt exceeded {model or 'this model'}'s context window; narrow "
        f"the plan/diff scope or configure a larger-context model"
    )


# ─────────────────────────────────────────────────────────────────────────────
# M14 (§5.4, §5.4.1) — ONE version gate.
#
# Before this section the same rule lived in several places at once, on purpose
# and with the reason written down each time: `_version_below` above carried a
# copy of `subagent_executor._version_tuple`'s comparison, and L7, M1 and M7
# each shipped their own per-flag help sniff *inside the task*, because §11.1
# needs those tasks severable from §11.2. Absorbing them is what this section
# is. It was never a precondition for any of them — each one-off worked on its
# own, and each is deleted only once its replacement is here and its own tests
# point at it.
#
# What "one gate" means concretely:
#
#   * **One parse-and-compare rule** — :func:`version_tuple`, used by
#     `_version_below` (the availability *label*) and by the executor's
#     preflight *refusal*. A build can no longer be too old for one and fine for
#     the other.
#   * **Floors and ceilings, both declared** — `min_version` and
#     `max_version_exclusive` (§5.4), read together by :func:`version_verdict`.
#     Every floor and ceiling carries a comment naming the **feature** that
#     requires it, never a bare number: a measured-at version is an upper bound
#     on the true floor, so a number with no feature behind it disables installs
#     that work (§5.4.1(a)).
#   * **One help read per CLI per process** — :func:`read_help_tokens`, memoised
#     on the resolved binary path *and* the help argv, so a four-model ×
#     ten-phase run performs at most one help spawn per CLI however many flags
#     that CLI gates.
#   * **One failure posture, in two documented shapes.** An *optional* flag that
#     cannot be confirmed is dropped with one WARN and the run proceeds
#     (:meth:`LLMProvider.supports_flag`); a *load-bearing* one is refused
#     before spawn, because there is no safe argv to fall back to
#     (:meth:`LLMProvider.missing_flags`). Both decline toward the status quo —
#     emitting a flag the binary may reject is the one outcome neither may
#     produce.
#
# Version reads take stdout and stderr **concatenated** (§5.4): some CLIs banner
# their version to stderr and opencode is stdout-only, so
# :meth:`LLMProvider.parse_version` reads both and `tests/test_version_gate.py`
# pins it with a CLI that prints its version on stderr alone.
#
# One thing this gate deliberately does **not** do: invent a sixth availability
# word. §5.1's report vocabulary is a closed five (`Availability`), so a build
# at or above a declared ceiling surfaces as the preflight's named refusal
# rather than as a mislabelled `version-too-low` report.
# ─────────────────────────────────────────────────────────────────────────────

#: How long one version or help probe may take, matching §2.1's probe
#: containment. A gate that hangs is worse than a gate that declines.
GATE_PROBE_TIMEOUT_S = 5

#: The gate's verdict words. ``VERSION_TOO_LOW`` is spelled from the availability
#: vocabulary rather than re-typed, so the refusal, the report and cursor's
#: load-bearing refusal (`cursor_agent.CursorFlagsUnconfirmed`) all say the same
#: word.
VERSION_OK = "ok"
VERSION_UNREAD = "unread"
VERSION_TOO_LOW = Availability.VERSION_TOO_LOW.value
#: At or above a declared ``max_version_exclusive``. **Exclusive**: the declared
#: number is the first build that is refused, which is what lets a ceiling name
#: the release that broke the parser instead of the last one that worked.
VERSION_TOO_NEW = "version-too-new"
#: Above ``verified_version`` — a warning, never a refusal: blocking on new
#: releases would rot faster than the CLIs do.
VERSION_ABOVE_VERIFIED = "above-verified"


def _upgrade_suffix(provider: Any, minimum: str) -> str:
    """How a below-floor sentence ends: ``" (run: <upgrade_hint>)."`` or ``"."``."""
    upgrade = (getattr(provider, "upgrade_hint", "") or "").strip()
    return f" (run: {upgrade.replace('{version}', minimum)})." if upgrade else "."


def version_tuple(text: str) -> Tuple[int, ...]:
    """``text``'s leading integers, component-wise, for **ordering only**.

    The single comparison rule of the whole harness (M14). ``"2026.08.11-e8db854"``
    is ``(2026, 8, 11)`` and ``"codex-cli 0.146.0"`` is ``(0,)`` — the caller
    passes a *parsed* version (:meth:`LLMProvider.parse_version` or
    :func:`_version_token`), never raw probe output.

    A component that does not start with a digit contributes ``0`` rather than
    raising, so a build suffix can never turn a version comparison into a crash
    on a dispatch path, and an empty string is ``(0,)`` — below everything.
    """
    parts: List[int] = []
    for chunk in (text or "").split("."):
        match = re.match(r"^(\d+)", chunk)
        parts.append(int(match.group(1)) if match else 0)
    return tuple(parts) or (0,)


#: A ceiling value that is safe to compare, matched **whole**: dotted integers,
#: an optional ``v`` prefix, and an optional ``-``/``+`` build or prerelease
#: suffix (opencode versions look like ``2026.08.11-e8db854``). Group 1 is the
#: part :func:`version_tuple` may read; anything this does not match entirely is
#: dropped by :func:`version_ceiling` rather than compared.
_CEILING_VERSION_RE = re.compile(r"^[vV]?(\d+(?:\.\d+)*)(?:[-+][0-9A-Za-z.+-]*)?$")


def version_ceiling(provider: Any, anchor: Optional[str] = None) -> str:
    """This adapter's ``max_version_exclusive``, or ``""`` for "no ceiling".

    Config first (``providers.<name>.max_version_exclusive``), the class
    declaration second — the same layering ``default_timeout`` already has, and
    the reason the key is *reachable from config at all*: a vendor can ship a
    broken build between two of this repo's releases, and pinning a ceiling then
    must not require editing an adapter.

    A blank, non-scalar or **non-numeric** value is "no ceiling" plus one
    warning, never an error and never a refusal. That last case is the one worth
    spelling out: ``version_tuple`` maps a value with no leading digits to
    ``(0,)``, so an unusable ceiling compared naively would sit *below* every
    real build and refuse the entire roster. A typo in a YAML file may not
    disable a provider, so it is dropped here, where it is read, rather than
    reaching the comparison. (YAML 1.1's bare ``on``/``yes`` resolving to a bool
    is exactly how such a value arrives.)

    "Numeric" means the value matches :data:`_CEILING_VERSION_RE` **whole**, and
    what is returned is that match's numeric core: ``v2.0.0`` and
    ``2.0.0-rc1`` both resolve to ``2.0.0``, and ``2026.08.11-e8db854`` (an
    opencode build string) to ``2026.08.11``. Both halves of that are load
    bearing, because a *substring* search would re-open the same footgun one
    step further along: ``release-2.0`` contains a version, so it would pass the
    check, and ``version_tuple`` then reads the returned string as ``(0, 0)`` —
    below every real build, so the ceiling refuses the whole roster it was
    supposed to leave alone. Returning the core rather than the string also
    keeps :func:`version_verdict`'s printed sentence numeric, for the reason
    :func:`_version_token` documents: that sentence reaches logs and failure
    artifacts, and a dotted numeric token cannot be a credential.
    """
    name = getattr(provider, "name", "") or ""
    declared = getattr(provider, "max_version_exclusive", "") or ""
    source = "declaration"
    if name:
        configured = _provider_block(name, anchor).get("max_version_exclusive")
        if configured is not None:
            declared, source = configured, "config"
    if isinstance(declared, bool) or not isinstance(declared, (str, int, float)):
        candidate = ""
    else:
        candidate = str(declared).strip()
    if not candidate:
        return ""
    match = _CEILING_VERSION_RE.match(candidate)
    if match is None:
        _warn_policy_once(
            f"max_version_exclusive:{name}:{candidate}",
            f"multi-llm config warning: ignoring "
            f"providers.{name}.max_version_exclusive={declared!r} ({source}) — a "
            f"ceiling must be a version number (e.g. \"2.0.0\"); running with no "
            f"ceiling for {name}",
        )
        return ""
    return match.group(1)


@dataclass(frozen=True)
class VersionVerdict:
    """Where one *read* version sits against one adapter's declared bounds.

    :attr:`detail` is composed only from declared data and the parsed version
    token — the same redaction rule :class:`AvailabilityReport` holds itself to,
    because this sentence is printed, logged and stored in failure artifacts.
    """

    state: str
    version: str = "unknown"
    detail: str = ""

    @property
    def refuses(self) -> bool:
        """Whether a preflight must refuse this runner before spawning a child."""
        return self.state in (VERSION_TOO_LOW, VERSION_TOO_NEW)


@dataclass(frozen=True)
class ModelVerdict:
    """Whether one model token is in the CLI's *own* live catalog (D3 step 4).

    The typed answer :meth:`LLMProvider.describe_unlisted_model` returns, in the
    :class:`VersionVerdict` mould. ``known`` is a tri-state on purpose: ``True``
    means the listing parsed cleanly and contains the token, ``False`` means the
    listing parsed cleanly and does **not**, and ``None`` means the CLI could not
    answer — no listing subcommand, a probe that failed to run, a non-zero exit,
    an empty or malformed listing. Unknown means unknown: a ``None`` refuses
    nothing, and D4's dispatch-time classifier is the backstop for a real miss.

    :attr:`detail` is composed from the listing that was just read — never quoted
    from a run-time "Did you mean" line, which no listing subcommand prints —
    and :attr:`suggestions` carries the same nearest ids structurally, so a
    caller renders them without re-parsing prose.
    """

    known: Optional[bool] = None
    detail: str = ""
    suggestions: Tuple[str, ...] = ()


def version_verdict(
    provider: Any,
    version: Optional[str],
    *,
    name: Optional[str] = None,
    anchor: Optional[str] = None,
) -> VersionVerdict:
    """The floor/ceiling/verified verdict for one read version (§5.4).

    The **one** place the three bounds are compared, so the preflight refusal and
    any other consumer cannot disagree about the same build. Order matters and
    is the preflight's own: floor, then ceiling, then the advisory
    ``verified_version`` warning.

    ``"unknown"``, ``""`` and ``None`` are :data:`VERSION_UNREAD` — *absence of
    evidence is never a negative verdict*. A CLI that dropped ``--version`` still
    answers prompts, so an unread version warns and dispatches; it never blocks.

    Args:
        provider: the adapter, read for ``min_version``, ``verified_version``
            and ``max_version_exclusive``.
        version: what :meth:`LLMProvider.parse_version` recovered.
        name: the name to put in the sentence, defaulting to ``provider.name``.
            The executor passes the *registry* key it was asked for, so the
            message names the runner the user typed.
    """
    label = (name or getattr(provider, "name", "") or "").strip()
    read = (version or "").strip()
    if not read or read == "unknown":
        return VersionVerdict(VERSION_UNREAD, "unknown", "")

    minimum = (getattr(provider, "min_version", "") or "").strip()
    ceiling = version_ceiling(provider, anchor)
    verified = (getattr(provider, "verified_version", "") or "").strip()

    if minimum and version_tuple(read) < version_tuple(minimum):
        how = _upgrade_suffix(provider, minimum)
        return VersionVerdict(
            VERSION_TOO_LOW,
            read,
            f"{label} {read} is older than the minimum this release parses "
            f"({minimum}); its event stream shape is not the one the adapter was "
            f"written against. Upgrade {label} to >= {minimum}{how}",
        )
    if ceiling and version_tuple(read) >= version_tuple(ceiling):
        return VersionVerdict(
            VERSION_TOO_NEW,
            read,
            f"{label} {read} is at or above {ceiling}, the build this release "
            f"declines to parse (max_version_exclusive); install a {label} "
            f"below {ceiling}.",
        )
    if verified and version_tuple(read) > version_tuple(verified):
        return VersionVerdict(
            VERSION_ABOVE_VERIFIED,
            read,
            f"{label} {read} is newer than the release the shipped parser "
            f"fixtures were captured from ({verified}); stream parsing is "
            f"best-effort above that.",
        )
    return VersionVerdict(VERSION_OK, read, "")


#: A whole-word long-option token. ``--model`` must never be read as ``--mode``,
#: and ``--fallback-model`` must never be confirmed by a help text that only
#: documents ``--fallback-model-chain``: confirming the wrong flag is exactly the
#: failure this gate exists to prevent.
_FLAG_TOKEN_RE = re.compile(r"(?<![\w-])(--[A-Za-z0-9][A-Za-z0-9-]*)(?![\w-])")

#: One help read per (resolved binary, help argv) per process. The argv is part
#: of the key because a flag can live on a subcommand's help rather than the
#: top-level one, and those are two different reads of the same binary.
_HELP_TOKENS: Dict[Tuple[str, Tuple[str, ...]], FrozenSet[str]] = {}
_HELP_TOKENS_LOCK = threading.Lock()

#: One WARN per declined capability per process, not one per dispatch.
_GATE_WARNED: Set[Any] = set()


def reset_flag_gate_cache() -> None:
    """Forget the memoised help reads and the warn-once set (tests only).

    Never called on a run path: the whole point of the cache is that a fan-out
    spawns one help probe per CLI, not one per slot.
    """
    with _HELP_TOKENS_LOCK:
        _HELP_TOKENS.clear()
    _GATE_WARNED.clear()


def warn_gate_once(key: Any, message: str) -> None:
    """Print one gate WARN per distinct key per process, on stderr.

    The *sentence* stays with the adapter, because it names the capability that
    run is doing without; only the once-ness is shared.
    """
    if key in _GATE_WARNED:
        return
    _GATE_WARNED.add(key)
    print(message, file=sys.stderr)


def read_help_tokens(
    binary: str,
    *,
    help_argv: Tuple[str, ...] = ("--help",),
    env: Optional[Mapping[str, str]] = None,
) -> FrozenSet[str]:
    """Every long-option token this binary's own help documents (§5.4.1).

    Containment matches §2.1's probe: ``stdin=DEVNULL``, captured output, a
    :data:`GATE_PROBE_TIMEOUT_S` timeout, zero network, and an environment the
    caller composed with the same builder a dispatch uses
    (:meth:`LLMProvider.gate_probe_env`), so Lane A and Lane B can never
    disagree about which flags a run emits.

    ``TERM=dumb`` and a wide ``COLUMNS`` are the caller's job and are
    load-bearing: §3.6's own history is a *truncated* help rendering that hid
    what a flag required, and a token sniff must not inherit that failure mode.
    Both streams are read **concatenated** (§5.4) because some CLIs banner to
    stderr.

    Failure posture — decline the *flag*, keep the *run*. A timeout, a non-zero
    exit, an empty help, an unreadable stream or anything else this probe can
    hit all resolve to the empty set, i.e. "unsupported". The ``except`` is
    deliberately total: a diagnostic read of a binary's own help text may not be
    the thing that ends a dispatch.
    """
    key = (str(binary), tuple(help_argv))
    with _HELP_TOKENS_LOCK:
        cached = _HELP_TOKENS.get(key)
    if cached is not None:
        return cached

    tokens: FrozenSet[str] = frozenset()
    try:
        completed = subprocess.run(
            [str(binary), *help_argv],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=GATE_PROBE_TIMEOUT_S,
            env=dict(env) if env is not None else None,
        )
        if completed.returncode == 0:
            text = f"{completed.stdout or ''}\n{completed.stderr or ''}"
            if text.strip():
                tokens = frozenset(_FLAG_TOKEN_RE.findall(text))
    except Exception:  # noqa: BLE001 - see the failure posture above
        tokens = frozenset()

    with _HELP_TOKENS_LOCK:
        _HELP_TOKENS.setdefault(key, tokens)
        return _HELP_TOKENS[key]


class LLMProvider(ABC):
    """Abstract base class for LLM CLI providers.

    All provider implementations must inherit from this class and implement
    the required abstract methods and properties. This ensures a consistent
    interface for invoking different LLM CLI tools.
    """

    # How build_command() delivers the prompt to the CLI. Every current
    # provider CLI takes the prompt as an argv element (none has a documented
    # stdin or prompt-file mode used anywhere in this codebase), so "argv" is
    # the default. On Windows, argv transport is subject to hard command-line
    # length caps (cmd.exe: 8,191 chars for .cmd/.bat shims; CreateProcess:
    # 32,767), so llm_client enforces a prompt-length check for "argv"
    # providers there. An adapter that grows a stdin ("stdin") or prompt-file
    # ("file") mode should override this to opt out of that check.
    prompt_transport: str = "argv"

    # Which transports this adapter can actually deliver a prompt over (D2d).
    # ``prompt_transport`` above is the one the fan-out path uses by default;
    # this tuple is what a *caller* may ask for, and it is what the materialized
    # -prompt budget is derived from: a materialized prompt is far larger than
    # the metadata JSON it replaces (validation alone permits ~30,000 characters
    # of context before the suggestion list), and argv cannot carry that on
    # Windows, where the whole rendered command line is capped at 8,191 UTF-16
    # code units for a .cmd/.bat shim and 32,767 natively. An adapter declaring
    # "stdin" or "file" makes the budget effectively unbounded; an argv-only
    # adapter keeps the cap, and the producer splits the batch rather than
    # truncating.
    supported_prompt_transports: Tuple[str, ...] = ("argv",)

    # Where ``build_command`` puts the prompt in the argv it returns (§9.4).
    #
    # ``-1`` — the last element — is the assumption every ``cmd[:-1]`` override
    # and :meth:`build_agent_command_for_transport` already relied on, silently.
    # Measured 2026-08-16: **two** adapters violated it. grok put the prompt at
    # index 4 (normalized since — the ``-p <prompt>`` pair now trails), and aider
    # has no standalone prompt element at all because it ships ``"/ask " +
    # prompt`` after ``--message``. That second case is why a bare assert could
    # not be written and this is a declaration instead: ``None`` means "not a
    # standalone argv element", and an adapter declaring it must never be handed
    # a non-argv transport or an agent profile, both of which drop ``argv[-1]``.
    #
    # ``tests/test_provider_housekeeping.py`` checks the declaration against the
    # argv each adapter really renders, in both directions.
    prompt_argv_index: Optional[int] = -1

    # Whether this adapter's ``generate`` invocation can write the per-model
    # result file the Lane A review prompts name in their ``{output_location}``
    # block (``llm_client.render_output_location``).
    #
    # ``True`` is the default and the honest one for a CLI agent that carries
    # write tools — it is what ``invoke_with_file_output``'s whole file-first
    # contract is built on. ``False`` is a *measured* refusal, never a
    # preference, and it exists because two adapters deliberately run their CLI
    # in a read-only chat mode: cursor under ``--mode ask`` (the write-refusal
    # that replaced ``-f``/``--yolo`` — see
    # :data:`~utils.providers.cursor_agent.CURSOR_REQUIRED_FLAGS`) and aider
    # under ``/ask``. Handed a "write this file" instruction those two spend the
    # whole turn explaining that they cannot, no file appears, and the slot dies
    # on ``JSON parsing failed from both file and stdout`` — a refusal sentence
    # is not a parse failure, so no retry rung can recover it either.
    #
    # The declaration is read at prompt-render time, so an adapter that cannot
    # write is *asked* for stdout rather than being asked for a file and left to
    # the fallback it can only reach by disobeying its own mode. Nothing about
    # the parse side moves: ``invoke_with_file_output`` still reads the file
    # first, so an adapter that writes one anyway is still served from it.
    supports_file_output: bool = True

    #: Whether the ask lane inlines the plan's body into this adapter's prompt
    #: (``prompts/ask.txt``'s ``{plan_block}``). ``True`` is the default and
    #: keeps every adapter's ask prompt byte-identical to the inline template.
    #: ``False`` promises that the adapter passes the plan **by another route**,
    #: so the inline copy would only duplicate it — aider attaches every
    #: absolute path its prompt names as a ``--read`` file, and an inlined body
    #: also feeds aider's mention scan, which auto-adds every repo path the plan
    #: names (plans/ask-answer-recovery-and-false-success.md D4.2). An adapter
    #: that declares ``False`` with no such route would get no plan at all, and
    #: ``tests/test_provider_housekeeping.py`` fails it by name.
    wants_inline_plan: bool = True

    #: How ``utils.llm_client.generic_answer_text`` reads this adapter's stdout
    #: when :meth:`salvage_text` has no opinion (D2.2). ``"auto"`` (the default)
    #: treats a whole-stdout event stream or a JSON value that is not a clean
    #: result envelope as transport, never as the answer. ``"plain"`` declares
    #: that the stdout **is** the model's reply, so a direct JSON or NDJSON
    #: answer comes back whole; only the ANSI strip and the adapter's own
    #: exit-zero markers apply. Read only by the answer-text reducer, never by
    #: the review lanes' salvage.
    answer_framing: str = "auto"

    #: Repo-relative directory prefixes (trailing ``/``) this adapter's CLI
    #: writes into the working tree as its own cache on every run — aider's repo
    #: map, ``.aider.tags.cache.v4/``. The porcelain write check ignores them
    #: **only when an adapter declaring them is in the same fan-out**
    #: (``review_orchestrator_base.fanout_ignore_prefixes``, D4.3), so a
    #: sibling's cache is never blamed on an uncontained slot, and without such
    #: a sibling a change there still counts. Each entry is the measured version,
    #: never a glob: a version bump must force a re-measurement.
    workspace_caches: Tuple[str, ...] = ()

    # ------------------------------------------------------------------
    # Subagent-runner capability declarations (D3/D3e/D3j/D3m)
    #
    # All five are **defaulting** members, following the ``prompt_transport``
    # pattern above: none of the thirteen shipped adapters has to change to keep
    # importing, instantiating and serving the ``generate`` path, and the model
    # fan-out — which never asks for a profile — is unaffected entirely. An
    # adapter opts in by overriding them, and ``tests/test_providers.py``
    # cross-checks every declaration against the members actually implemented so
    # the data cannot drift from the code.
    # ------------------------------------------------------------------

    #: Invocation profiles this adapter really implements. ``generate`` is
    #: implicit for every adapter (that is ``build_command``); anything else must
    #: be backed by a real ``build_agent_command`` branch.
    agent_profiles: Tuple[str, ...] = (PROFILE_GENERATE,)

    #: True only when this adapter has an edit-capable invocation (``agent-write``).
    supports_file_edits: bool = False

    #: True when the adapter's agentic invocation can explore a repository
    #: (``context_mode: workspace-read``, D2c).
    supports_workspace_reads: bool = False

    #: True when the ``agent-readonly`` invocation can read files OUTSIDE its
    #: working directory (the pinned repo root) with no extra flag — codex's
    #: ``--sandbox read-only`` reads anywhere. A validation batch may name a
    #: snapshot in a phase dir outside the repo (a plan kept elsewhere), so an
    #: adapter that is neither this nor :attr:`read_scope_flag` is treated as
    #: unable to read such a path (plans/validation-context-by-path-and-codex-0156-fallout.md §2.2).
    reads_outside_cwd: bool = False

    #: The flag that widens the ``agent-readonly`` read scope to one more
    #: directory (claude-code's ``--add-dir``), or ``None``. The executor asks
    #: for it only when a ``mode: path`` context source lies outside cwd, via
    #: :meth:`widen_read_scope`.
    read_scope_flag: Optional[str] = None

    # The two members below sit beside the agent-readonly read declarations
    # above but describe a DIFFERENT invocation: the ``generate`` profile, i.e.
    # ``build_command``, which is what every Lane A review/ask fan-out slot
    # runs. ``supports_workspace_reads``/``reads_outside_cwd``/
    # ``read_scope_flag`` say nothing about it, and neither does
    # ``providers.yaml``'s ``read_only_modes`` (the record of write-restricting
    # mechanisms). ``llm_client.render_diff_access`` renders the code-review
    # prompt's ``{diff_access}`` block from these two, so the orchestrator never
    # branches on a provider name (plan: review-run-scope-salvage-and-failure-
    # visibility D2.3).
    #
    # A value leaves its default only with a measured source — a log, a probe
    # or its argv — and the override's comment names that source.
    # ``tests/test_provider_housekeeping.py``'s ``SHELL_EVIDENCE`` table holds
    # each shell declaration to it.

    #: Whether the ``generate`` profile can run a shell command. Three states:
    #:
    #: * ``True``  — a shell runs, measured (the prompt grants ``git diff``);
    #: * ``False`` — no shell runs, measured (the prompt says so, and forbids
    #:   test-result claims it cannot back);
    #: * ``None``  — not measured. The default, and the safe one: its rendering
    #:   neither grants nor denies a shell. A ``False`` default would be a claim
    #:   too, and a wrong one — pi, omp and codex all run a shell on this path.
    #:
    #: This is the authoritative record of the fact. A ``read_only_modes``
    #: ``probed:`` note that speaks about a shell cites this attribute rather
    #: than restating it, so there is one value to change.
    runs_shell_in_generate: Optional[bool] = None

    #: Where the ``generate`` profile can read files. Three values:
    #:
    #: * ``"none"`` — no file tool at all (qwen-code's zero tool budget aborts
    #:   before the first call runs, so it cannot read even the plan);
    #: * ``"cwd"``  — reads under its working directory, the repo root. The
    #:   default, because every Lane A prompt already hands over the plan by
    #:   path and so already assumes it;
    #: * ``"any"``  — reads absolute paths anywhere.
    #:
    #: A shell flag cannot stand in for this: a lane can read with no shell
    #: (cursor ``--mode ask``) or have neither (qwen-code). A lane that cannot
    #: open the phase dir — ``"none"``, or ``"cwd"`` with the phase dir outside
    #: the repo — gets the diff inline, bounded, or is not dispatched.
    generate_read_scope: str = "cwd"

    #: Declared usage fidelity (D3j): ``none`` | ``partial`` | ``full``.
    usage_support: str = USAGE_NONE

    #: What the vendor CLI does *inside* one awaited subprocess before it returns
    #: (§7.6(b)). ``None`` means unmeasured: the ladder then assumes a single
    #: request and refuses to hand the adapter a retry-count env var (§7.3).
    #:
    #: The converse is a test, not a convention — an adapter whose ``get_env``
    #: sets a retry-shaped variable while this stays ``None`` is a budget bug,
    #: because §7.5 rule 4 would subtract one request's worth of wall clock from
    #: the deadline while the child quietly makes several.
    #:
    #: An adapter whose envelope depends on the *resolved* slot timeout (as
    #: claude-code's does — its wall is 4 × ``API_TIMEOUT_MS``, itself derived)
    #: overrides this with a property, so the declaration and the emitted env are
    #: one derivation rather than two copies of it.
    internal_retries: Optional[InternalRetryEnvelope] = None

    #: Whether this adapter really emits a schema flag when handed a ``schema=``
    #: (§4.2.2). ``False`` is the default and the honest one: the default
    #: builders below **ignore** ``schema`` entirely, so a caller that assumed
    #: otherwise would be reading prose as validated output.
    #:
    #: The caller reads this **before** dispatch: ``False`` ⇒ the phase runs its
    #: prompt-level JSON path and the result is marked ``recovered`` /
    #: ``unvalidated`` per §4.2.1, never ``native``. Only ``claude-code`` and
    #: ``codex`` set it ``True``, and an adapter that sets it ``True`` while
    #: emitting no flag is a bug ``tests/test_structured_output.py`` catches.
    structured_output_support: bool = False

    #: How this adapter carries a schema: ``"inline"`` (claude's
    #: ``--json-schema <json>``) or ``"file"`` (codex's
    #: ``--output-schema <FILE>``). §4.2's contract asymmetry, **declared** so
    #: the caller knows whether to materialize a sidecar without branching on an
    #: adapter name. Meaningless while ``structured_output_support`` is ``False``.
    structured_output_transport: str = "inline"

    #: argv that prints the CLI version, the oldest release whose streams this
    #: parser is known to handle, and the release the shipped parser fixtures
    #: were captured from (D3m). Empty means "not declared" — the executor
    #: records ``unknown`` and warns rather than blocking.
    #:
    #: **M14/§5.4: a declared floor carries a comment naming the FEATURE it
    #: protects, never a bare number.** A measured-at version is an upper bound
    #: on the true floor, so a floor raised to "the version this happened to be
    #: probed on" disables installs that work — which is why the flags verified
    #: on one recent build are gated per flag (:meth:`supports_flag`) instead of
    #: raising the number here.
    version_cmd: Tuple[str, ...] = ()
    min_version: str = ""
    verified_version: str = ""
    #: The command a human runs to reach ``min_version``, with ``{version}``
    #: standing for it, appended to the below-floor refusal
    #: (:func:`version_verdict`). Printed, never run; ``""`` names none.
    upgrade_hint: str = ""

    #: M14 (§5.4) — the first build this release **refuses**, exclusive, or ``""``
    #: for "no ceiling". The mirror of ``min_version`` and subject to the same
    #: rule: it carries a comment naming the feature (or the breakage) behind it.
    #: Overridable per install through ``providers.<name>.max_version_exclusive``
    #: (:func:`version_ceiling`), because a vendor can ship a broken build
    #: between two releases of this repo and pinning it must not require an
    #: adapter edit. A ceiling is a **refusal**, unlike ``verified_version``'s
    #: warning: the two are different claims, and merging them would either
    #: block every new release or refuse nothing.
    max_version_exclusive: str = ""

    #: M14 (§5.4.1) — the argv, after the binary, that prints the help
    #: documenting this adapter's gated flags. An adapter whose flags live on a
    #: subcommand declares that subcommand here (``("run", "--help")``); the
    #: default is the CLI's top-level help.
    help_argv: Tuple[str, ...] = ("--help",)

    #: M14/§5.4.1(a) — flags this adapter emits **unconditionally** because each
    #: was verified *functionally* at the declared ``min_version``, not merely
    #: found in help text. The shared gate answers :meth:`supports_flag` ``True``
    #: for these **without probing**: there is no release in the supported range
    #: that would need gating, and a runtime probe would only add a failure mode.
    #:
    #: This is the exemption §5.4.1 grants, written as data rather than as prose
    #: in one adapter's comment block, so the claim is assertable: every flag
    #: named here must really be documented by that CLI at its floor, and every
    #: flag *not* named here that an adapter adds to argv takes a gate.
    flags_verified_at_floor: Tuple[str, ...] = ()

    #: A cheap, **non-generating** argv that reports whether this CLI is logged in
    #: (D3c) — a ``login status`` / ``whoami``-class subcommand. The executor
    #: probes it once per distinct runner per run, in the same preflight that runs
    #: ``version_cmd``, so a logged-out runner is refused *before* a child is
    #: spawned instead of being discovered one dispatch at a time (installed is not
    #: authenticated: every ``is_available()`` is a bare ``shutil.which``).
    #: Empty means "this CLI offers no such subcommand": the probe is skipped and
    #: the auth state is recorded ``unknown`` rather than assumed good.
    auth_check: Tuple[str, ...] = ()

    #: The command that fixes a failed ``auth_check``, named verbatim in the
    #: exit-3 refusal. Mirrors ``runners[*].login_cmd`` in ``hosts/capabilities.yaml``,
    #: which is the same fact from the host's side.
    login_cmd: str = ""

    #: The OS-level sandbox this CLI puts between the model and the filesystem
    #: in the mode the adapter runs it (D6): ``"bubblewrap"`` for codex and
    #: muse, empty for every adapter that writes as an ordinary process under
    #: flags fixed at build time. Read by ``multi_llm.py doctor`` only — it is
    #: what selects the 2 ms ``bwrap --unshare-net`` self-test for a CLI whose
    #: own runner offers no model-free probe. Never a dispatch decision.
    sandbox_mechanism: str = ""

    #: The adapter flag that turns :attr:`sandbox_mechanism` **off** on every
    #: dispatch (muse's ``--disable-sandbox``, D6 step 2), so a broken sandbox
    #: is reported by ``doctor`` as bypassed rather than as a failure. Empty
    #: means the mechanism is live.
    sandbox_disabled_by: str = ""

    #: An open question about whether this CLI's workspace-trust gate blocks a
    #: headless write, recorded as data rather than guessed (D6 step 6). Empty
    #: for every adapter except one whose gate is unmeasured; ``doctor`` prints
    #: it verbatim as ``trust: <value>``.
    trust_status: str = ""

    def sandbox_probe_command(self, profile: str) -> Optional[List[str]]:
        """A model-free argv that exercises this CLI's own sandbox (D6 step 3).

        ``None`` — the default, and the answer for every adapter without an OS
        sandbox or with one turned off — means "nothing to probe". An adapter
        that returns an argv promises it exercises the *same* sandbox a
        ``profile`` dispatch would run under, with no model and no prompt, and
        exits 0 on success; anything non-zero is read as the sandbox refusing.
        A write-capable profile's probe writes one byte under
        ``.multi-llm/tmp`` of the current directory and deletes it; a read-only
        profile's writes nothing and asks only whether the sandbox starts,
        which is the question a dispatch under it needs answered — it reads the
        repository, and a sandbox that cannot come up denies it that too. The
        executor's preflight runs it once per host/spec/profile with a 10 s
        timeout before the first dispatch of that profile, the review fan-out
        runs it once per provider for ``generate`` before its first slot, and
        ``doctor`` runs the same command.
        """
        return None

    def sandbox_fallback_policy(
        self, profile: str, anchor: Optional[str] = None
    ) -> Optional[str]:
        """The resolved ``sandbox_fallback`` policy this adapter honours for
        ``profile``, or ``None`` (D6, 2026-09-17).

        ``None`` — the default, and the answer for every adapter without an OS
        sandbox of its own — means "no fallback exists here": a dispatch under
        this profile either runs sandboxed or is refused, and no config key can
        change that. An adapter that overrides this answers one of
        :data:`SANDBOX_FALLBACK_POLICIES`, read through the normal config
        layering, and **only for a profile in**
        :data:`SANDBOX_FALLBACK_PROFILES` — or, for an adapter that declares a
        write ladder (plan step 3, 2026-09-30), for ``agent-write`` while its
        opt-in is in force, and then only a policy :func:`write_rung_allowed`
        reads: a wrapping, ``incidental``-grade rung under ``auto``. Every other
        adapter answers ``None`` for ``agent-write`` whatever the config says.
        Every gate that consults this
        (``review_orchestrator_base.sandbox_refusal``,
        ``subagent_executor._detect_sandbox``) requires *all five* of: the
        probe verdict ``unavailable`` (never ``unknown`` — a probe that could
        not be read must not widen anything), a rung the walk selected, this
        answer permitting that rung (:func:`sandbox_rung_allowed`: ``auto``
        reaches every rung, ``contained`` a contained one only, ``off`` none),
        a read-only profile, and the adapter declaring the hook at all.
        """
        return None

    def sandbox_fallback_rungs(self, profile: str) -> Tuple["SandboxRung", ...]:
        """The ordered fallback ladder for ``profile`` (landlock rung, 2026-09-22).

        ``()`` — the default — means no fallback exists for this profile. An
        adapter that declares rungs does so for a profile in
        :data:`SANDBOX_FALLBACK_PROFILES`, and — only as a separate write ladder
        whose every rung :func:`write_rung_allowed` could admit — for
        ``agent-write`` (:data:`SANDBOX_WRITE_FALLBACK_PROFILES`); every other
        adapter's ``agent-write`` comes back ``()``. The write ladder never
        holds the uncontained or the legacy ``landlock`` rung, and a failed
        write rung never falls through. The executor's ``sandbox_verdict`` walks them in order after
        the profile's own probe said ``unavailable``, and the gates then decide
        by :func:`sandbox_rung_allowed` whether the selected rung may be taken.
        """
        return ()

    def apply_sandbox_fallback(
        self,
        argv: List[str],
        profile: str,
        rung: Optional[str] = None,
        context: Optional["JailContext"] = None,
        consent: Optional["WritePostureConsent"] = None,
    ) -> List[str]:
        """Rewrite a rendered ``argv`` onto fallback ``rung`` of this adapter's
        ladder, for a ``profile`` in :data:`SANDBOX_FALLBACK_PROFILES` (or the
        adapter's write ladder, :data:`SANDBOX_WRITE_FALLBACK_PROFILES`).

        ``context`` is the attempt's :class:`JailContext`, handed only for a
        wrapping rung (the plugin-landlock jail): its ``tmpdir`` and write
        scope reach the CLI argv (``developer_instructions``). A wrapping rung
        with no context must raise, never render the bare in-CLI atoms.
        ``consent`` is F5's :class:`WritePostureConsent`, the one way a write
        profile renders the uncontained rung (plan step 6).

        Called by the transport builders only when a gate has already selected
        ``rung`` (a :class:`SandboxRung` ``name``), so the default — ``argv``
        unchanged — is what every adapter without a fallback does with a rung
        it was never going to be handed. An adapter that declares rungs from
        :meth:`sandbox_fallback_rungs` must override this, must render **that**
        rung's rewrite (never a default one), and must raise on a profile
        outside the tuple or a rung it does not declare rather than render it:
        the write profiles are never widened, structurally, not by policy.
        """
        return argv

    #: Model tokens this CLI serves with **no credential of any kind present**
    #: (D3 step 2) — declared, never sniffed, and measured before it is written
    #: down. "Needs a credential" is a property of the *model* on a CLI that
    #: fronts several vendors (opencode's own ``opencode/*`` ids answer from a
    #: logged-out install; its ``openrouter/*`` ids do not), so the auth leg of
    #: the preflight asks :meth:`model_needs_credentials` per spec rather than
    #: treating one ``auth_check`` verdict as a fact about every model. Empty —
    #: the default for every adapter — means every model needs one, which is
    #: exactly today's behaviour: declaring nothing widens no gate. This is
    #: **not** ``hosts/capabilities.yaml``'s ``runners.*.needs_auth``, which is
    #: a host statement about a bundled runner and is read by nothing here.
    credential_free_models: FrozenSet[str] = frozenset()

    def model_needs_credentials(self, model: str) -> bool:
        """Whether dispatching ``model`` needs a stored or environment credential.

        ``model`` is normalized the way the dispatch normalizes it — the
        ``:effort`` suffix split off with :func:`split_reasoning_effort` against
        this adapter's accepted ladder — so one token spelling governs the auth
        leg and the catalog leg alike. ``True`` for every model an adapter has
        not explicitly declared credential-free.
        """
        base_model, _effort = split_reasoning_effort(
            str(model or ""), self._accepted_efforts()
        )
        return base_model.strip() not in self.credential_free_models

    def _accepted_efforts(self) -> Collection[str]:
        """This adapter's accepted ``:effort`` names — its module's ``EFFORT_LADDER``.

        Every registered adapter declares one at module scope and derives its
        ``REASONING_EFFORTS`` from it (``tests/test_reasoning_effort_ladder.py``
        grades that over the registry), so the base reads the same declaration
        instead of asking each adapter to repeat it. A test double without a
        ladder gets an empty set, which splits nothing.
        """
        module = sys.modules.get(type(self).__module__)
        ladder = getattr(module, "EFFORT_LADDER", None)
        try:
            return frozenset(ladder.accepted) if ladder is not None else frozenset()
        except Exception:  # noqa: BLE001 - a malformed ladder splits nothing
            return frozenset()

    #: M13 (§5.2) — an optional **metadata** readout: the cheap, non-generating
    #: argv that reports what a *status* surface prints beside the auth verdict
    #: (a plan tier, an entitlement), and nothing else. It is emphatically **not**
    #: a second auth probe: :meth:`classify_auth_probe` never sees it, no verdict
    #: is derived from it, and a run that cannot read it reports nothing rather
    #: than reporting a state. Empty — the default for every adapter — means this
    #: CLI has no such readout, and the status row simply has less to say.
    #:
    #: It is spawned only by the human-invoked status path
    #: (``install-host --check`` row 5, through
    #: :func:`utils.subagent_executor.probe_setup_metadata`), never by a dispatch
    #: preflight: the facts it carries change nothing about whether a child may
    #: start, so paying a subprocess for them once per phase would be cost
    #: without a decision.
    setup_probe: Tuple[str, ...] = ()

    #: M13 (§5.3) — how a human installs this CLI, verbatim. It is printed, and
    #: **never run**: no auto-install, because installing a vendor's binary
    #: because a probe said ``binary-missing`` crosses the same trust boundary
    #: M16 was declined on. Empty means "not declared", which is the honest
    #: state for a CLI whose install route this repo has not measured.
    install_hint: str = ""

    #: M13 (§5.3) — one sentence naming what this CLI's credential actually *is*
    #: (a profile directory, an OS keyring, an env var), for the adapters where
    #: ``login_cmd`` is not the whole story. Declared data only: it is rendered
    #: beside a probe verdict, so it may never carry a credential, a path from
    #: the environment, or probe output.
    auth_hint: str = ""

    #: Substrings that identify a login/credential notice on either stream, so a
    #: logged-out CLI lands on D3k rung 1 (``auth_failed``, no retry) instead of
    #: burning the retry budget as generic runner noise (D3c).
    auth_error_patterns: Tuple[str, ...] = (
        "not logged in",
        "please log in",
        "please login",
        "authentication required",
        "unauthorized",
        "invalid api key",
        "api key is missing",
        "no credentials",
        "credentials not found",
        "run `login`",
    )

    #: Substrings that identify a rate-limit / quota / overloaded response. A
    #: 429 is **not** a transport failure (D3i): it is retried with backoff and
    #: jitter and does not consume the retry budget, so it needs its own
    #: classification rather than being absorbed by "no parsed text". The bare
    #: status code is matched **with context** (see :func:`stream_pattern`) — a
    #: substring test would find it inside a cost or a token count and hand a
    #: never-retried failure an unlimited retry path.
    rate_limit_patterns: Tuple[str, ...] = (
        "429",
        "rate limit",
        "rate_limit",
        "ratelimit",
        "too many requests",
        "quota exceeded",
        "quota_exceeded",
        "insufficient_quota",
        "overloaded",
    )

    #: Regexes that make an **exit-0** run a failure (§7.2). Four shipped CLIs
    #: report a provider failure with exit code 0 — goose, aider, cline and
    #: cursor-agent (measured in all six auth states, §5.3) — so for them the
    #: exit code carries no verdict at all and only a stream marker does. These
    #: are consulted **last** in :func:`classify_streams`: they say "this run
    #: failed", never *why*, so every specific category gets its chance first.
    #:
    #: Empty for an adapter whose exit code is authoritative. Regexes rather than
    #: substrings because the markers are structured-JSON fragments
    #: (``"finishReason":"error"``) whose boundaries the substring matcher's
    #: separator rules were never designed for.
    exit_zero_failure_markers: Tuple["Pattern[str]", ...] = ()

    def supports_prompt_transport(self, transport: str) -> bool:
        """Whether this adapter can deliver a prompt over ``transport``."""
        return transport in self.supported_prompt_transports

    def vendor_text(self, stdout: str, stderr: str) -> Tuple[str, str]:
        """The part of this capture the vendor wrote. Base: the capture, unchanged.

        **Why this is a hook and not a parameter.** Four shipped adapters echo
        our own prompt back inside their JSON envelope (goose, copilot, vibe,
        muse), so ``f"{stdout}\\n{stderr}"`` is not "what the runner said" — it
        is the runner's answer *plus* ``prompts/plan_review.txt``. Every marker
        table in :func:`classify_streams` then matches against text we wrote:
        a completely successful goose run classified ``timeout`` because the
        prompt's example block contains the word, and copilot's and vibe's
        successful runs classified ``rate_limited`` because the plan under
        review discusses rate limits. On a *failed* run that verdict is live —
        ``subagent_executor._classify_failed_run`` forwards exactly
        ``auth_failed`` and ``rate_limited``, the two classes that change the
        whole batch's fate.

        **The class is wider than prompt echo: it is "echo our prompt or the
        repository".** A runner whose stdout carries *tool output* hands the
        classifier whatever the model read, and a validator reads the plan and
        the repo. opencode's ``--format json`` stream carried a validator's
        grep of a plan that discusses rate limiting, and the attempt was
        recorded ``rate_limited`` (run b38de8bb). The adapters that reduce for
        that reason are omp and pi (whose json streams echo the prompt *and*
        carry tool results), opencode (``tool_use``/``text`` events) and codex
        (``command_execution`` output and ``agent_message`` prose), and
        claude-code (a clean envelope's ``result`` is the model's own prose);
        each keeps only what the vendor itself wrote.

        A caller-supplied ``vendor_text=`` argument could not fix it: every
        existing call site would have to opt in, and the §6.2 fixture rig calls
        ``adapter.classify_failure(stdout, stderr, exit_code)`` with no extra
        argument. The reduction therefore happens *inside* this class, where the
        default is identity and every caller inherits it for free.

        The contract for an override, all three parts load-bearing:

        * **It may only remove.** An override returns the same capture with the
          echoed turn taken out of it. Returning text that was not in the
          capture is out of contract — this hook narrows a haystack, it never
          synthesizes one.
        * **A failed reduction returns its input unchanged, never ``""``.** An
          empty haystack classifies as ``None`` (see :func:`classify_streams`),
          so a hook that swallowed a genuine 401 on a parse error would launder
          a credential failure into a transport-shaped retry — a worse bug than
          the one this fixes. Every override is a ``try``/``except`` around a
          parse of an envelope the adapter does not control.
        * **stderr is not reduced** by any shipped override: the echo lives in
          the structured stdout envelope, and the diagnosis a real failure
          carries must reach the tables untouched. The one exception is
          qwen-code's, which drops a single named advisory line (its ripgrep
          fallback notice, whose ``EACCES`` is not a diagnosis) and nothing else.

        Applied in exactly two places. :meth:`classify_failure` applies it **to
        classify**. ``subagent_executor._classify_failed_run`` applies it a
        second time **to quote, never to classify**: once the verdict is in, it
        re-runs :func:`match_streams` over the reduced capture so the failure
        reason quotes the text that decided the verdict rather than a stream
        tail that may not contain it, and the re-scan's result never changes
        the verdict. Nothing else applies it. The module-level
        :func:`classify_streams` (and its quote-only twin
        :func:`match_streams`) deliberately does **not** grow it:
        ``validation.py`` and ``_format_failure_details`` call that function with
        no adapter in hand, and §7.2 depends on it staying the one rule both
        lanes share. :meth:`classify_auth_probe`'s haystack — the second place
        this module builds ``f"{stdout}\\n{stderr}".lower()``, over an
        ``auth_check`` run — is out of scope too: an auth probe never carries
        our prompt, so narrowing it fixes nothing and risks the one verdict
        allowed to refuse a run outright.
        """
        return stdout, stderr

    def classify_failure(
        self, stdout: str, stderr: str, exit_code: int = 0
    ) -> Optional[str]:
        """Classify a run: a ladder status, a ``CATEGORY_*`` name, or ``None``.

        The adapter supplies the *data* — its declared pattern sets and its own
        exit-0 markers — and :func:`classify_streams` is the one implementation
        of the rule. That split is the point of §7.2: before it, Lane A carried
        five substring copies of this decision and ``validation.py`` a sixth, and
        they disagreed with each other and with this method about the same
        streams.

        Both streams are read, because several providers report errors on stdout
        and leave stderr empty. An unrecognized error stays ``None`` —
        "transport-shaped" — and falls back to the executor's bounded retry path
        rather than looping forever.

        Auth is still checked before rate limiting: a logged-out CLI is D3k rung
        1 (no retry, whole batch fails), and misreading it as a rate limit would
        retry a condition no retry can fix. What now precedes **both** is the
        launch-failure tuple, because a refused exec prints text that reads like
        a credential problem (§7.2's root-cause-before-auth rule).

        Every declared pattern is still matched through :func:`stream_pattern`,
        never as a bare substring: the sets contain a status code (``429``) and
        short words (``unauthorized``) that occur inside numbers and longer
        tokens a runner routinely prints.

        One thing happens before the rule runs: :meth:`vendor_text` reduces the
        capture to the part the *vendor* wrote, so an adapter that echoes our
        prompt back into its envelope stops classifying our own words. The base
        implementation is identity, so an adapter that does not override it is
        byte-for-byte what it was.
        """
        stdout, stderr = self.vendor_text(stdout, stderr)
        return classify_streams(
            stdout,
            stderr,
            exit_code,
            auth_patterns=self.auth_error_patterns,
            rate_limit_patterns=self.rate_limit_patterns,
            exit_zero_markers=self.exit_zero_failure_markers,
        )

    def classify_structural(
        self, stdout: str, stderr: str, exit_code: int = 0
    ) -> Optional[Tuple[str, str]]:
        """A structural failure verdict **with its own reason**, or ``None``.

        :meth:`classify_failure` returns a category and nothing else, and
        ``subagent_executor._classify_failed_run`` forwards only the pattern
        verdicts that change a batch's fate (auth, rate limit, invalid model,
        sandbox, context length); a ``runner_error`` from it is dropped and the
        attempt keeps its parse failure's status and text. An adapter that can
        recognize a failure from the *shape* of its stream — opencode's turn
        ended by an auto-rejected permission (``OpenCodeProvider``) — returns
        ``(status, reason)`` here, and the executor records both. It is
        consulted only after :meth:`classify_failure`'s verdict was not one of
        the forwarded ones, so a genuine vendor error still wins.

        Base: ``None``, so every adapter that does not override it is exactly
        what it was.
        """
        return None

    def classify_auth_probe(
        self, stdout: str, stderr: str, exit_code: int = 0
    ) -> Optional[bool]:
        """Read an ``auth_check`` run as authenticated / not / unknown (D3c).

        ``False`` means a login/credential notice was recognized — that is the
        only verdict that refuses a run, so it is the only one drawn from a
        pattern match. A non-zero exit with nothing recognized is ``None``
        ("unknown"), because an older CLI without the subcommand, a broken pipe or
        an offline probe all exit non-zero without saying anything about
        credentials, and blocking a run on that would be worse than the dispatch
        it is meant to save. ``True`` is a clean exit with no notice.
        """
        haystack = f"{stdout or ''}\n{stderr or ''}".lower()
        if matches_any(self.auth_error_patterns, haystack):
            return False
        if exit_code != 0:
            return None
        return True

    def describe_setup(self) -> SetupHints:
        """This adapter's install / login / status metadata (M13, §5.3).

        Derived from what the adapter already declares — ``install_hint``,
        ``login_cmd``, ``auth_check``, ``auth_hint`` — so the four rows and the
        argv the preflight really runs cannot drift apart. Implemented once,
        here: no adapter overrides it, and a new adapter gets the rows by
        declaring them rather than by implementing a method.

        ``login_cmd`` is split on whitespace rather than with :mod:`shlex`
        because it is a *declaration*, not user input: every shipped value is a
        two- or three-word subcommand (``codex login``, ``opencode auth
        login``). A declared login command that needs quoting is a bug in the
        declaration, not a parsing problem to solve here.
        """
        return SetupHints(
            install_hint=(self.install_hint or "").strip(),
            login_args=tuple((self.login_cmd or "").split()),
            status_args=tuple(self.auth_check or ()),
            auth_hint=(self.auth_hint or "").strip(),
        )

    def read_setup_probe(
        self, stdout: str, stderr: str, exit_code: int = 0
    ) -> Dict[str, str]:
        """What a ``setup_probe`` run says, as printable ``label -> value`` (M13).

        The reader half of :attr:`setup_probe`, and it is held to the same rule
        the argv is: **nothing here is a verdict.** An adapter may report a plan
        tier or an entitlement the status row would otherwise have no way to
        show; it may not report whether the CLI is logged in, whether it is
        usable, or anything else a caller could branch on — that is
        :meth:`classify_auth_probe`'s job, from a different probe.

        Every value returned is rendered into a status row, so an override owes
        the same care ``AvailabilityReport.detail`` is owed: report the one or
        two facts the readout exists for, bounded and stripped of anything the
        envelope carries beside them, never the envelope itself.

        The default is ``{}`` — the honest answer for the adapters that declare
        no readout, which is all of them but one.
        """
        return {}

    def supports_profile(self, profile: str) -> bool:
        """Whether this adapter declares ``profile`` (D3e)."""
        return profile in self.agent_profiles

    def widen_read_scope(self, argv: List[str], dirs: Sequence[str]) -> List[str]:
        """``argv`` with :attr:`read_scope_flag` added once per directory.

        Inserted right after the executable, ahead of every other option, so a
        variadic option later in the argv can never swallow it and a trailing
        positional prompt is never displaced. An adapter with no flag returns
        ``argv`` unchanged — the caller refuses rather than dispatching a path
        the runner cannot open.
        """
        if not self.read_scope_flag or not dirs or not argv:
            return list(argv)
        extra: List[str] = []
        for directory in dirs:
            extra.extend([self.read_scope_flag, str(directory)])
        return [argv[0], *extra, *argv[1:]]

    def build_agent_command(
        self,
        prompt: str,
        model: str,
        profile: str = PROFILE_AGENT_READONLY,
        *,
        timeout_s: Optional[int] = None,
        schema: Optional[StructuredSchema] = None,
    ) -> List[str]:
        """Build the argv for an *agentic* invocation under ``profile`` (D3e).

        The executor never picks a raw command: it picks a profile, and the
        adapter renders the invocation whose own sandbox/permission mechanism
        enforces it. There is deliberately no fabricated fallback — an adapter
        with no genuinely read-only mode raises rather than being dispatched with
        write access to an untrusted prompt.

        The profile also scopes the child's git environment (§2.2), and that
        scoping is asymmetric on purpose: ``generate`` and ``agent-readonly`` run
        with ``credential.helper=""`` so a hanging helper fails in ~0.27 s instead
        of burning the slot and orphaning a child, while ``agent-write`` keeps
        whatever helper the user configured because it is the profile that
        legitimately reaches private remotes. **Re-globalising that wipe is
        forbidden** — see :func:`git_env`.

        Args:
            prompt: The prompt text.
            model: The model identifier.
            profile: ``agent-readonly`` or ``agent-write``.
            timeout_s: The caller's already-resolved outer timeout, in whole
                seconds (§9.6.a). Keyword-only, optional, and ignored by every
                adapter with no internal cutoff of its own — see
                :meth:`build_command` for why it exists and what ``None`` means.
            schema: §4.2.2's optional structured-output schema. Keyword-only,
                optional, and **ignored by this default implementation** — see
                :attr:`structured_output_support`.

        Returns:
            argv suitable for ``subprocess.run``.

        Raises:
            ProfileUnsupported: always, unless the adapter overrides this.
        """
        raise ProfileUnsupported(
            f"{self.name} does not implement the {profile!r} invocation profile "
            f"(declared: {', '.join(self.agent_profiles) or 'none'})",
            provider=self.name,
            profile=profile,
        )

    def build_agent_command_for_transport(
        self,
        prompt: str,
        model: str,
        profile: str = PROFILE_AGENT_READONLY,
        transport: str = "argv",
        prompt_file: Optional[str] = None,
        *,
        timeout_s: Optional[int] = None,
        schema: Optional[StructuredSchema] = None,
        sandbox_fallback: Optional[str] = None,
        jail_context: Optional["JailContext"] = None,
        write_consent: Optional["WritePostureConsent"] = None,
    ) -> Tuple[List[str], Optional[str]]:
        """``build_agent_command`` plus the text to write to the child's stdin.

        Mirrors :meth:`build_command_for_transport` for the agentic profiles. The
        default implementation assumes the prompt is the **last** argv element
        (which every profile command this repo ships builds that way), so a
        ``stdin`` transport simply drops it and returns it as the child's input.

        ``sandbox_fallback`` is the executor's D6 override (2026-09-17), now the
        **rung id** the preflight selected (landlock rung, 2026-09-22): set only
        when ``_detect_sandbox`` recorded a rung for this runner and profile,
        and it reaches the argv through :meth:`apply_sandbox_fallback` —
        which renders *that* rung — *before* the prompt is split off, so the
        rewrite sees the same positions ``build_agent_command`` rendered. A
        bare ``True`` is the pre-rung spelling and means the uncontained rung
        (:func:`sandbox_rung_id`). Ignored by every adapter that keeps the
        default hook.

        ``jail_context`` (plan codex-sandbox-unavailable §6 F1) is the attempt's
        :class:`JailContext`, set by the spawn site only for a dispatch on a
        wrapping rung (the plugin-landlock jail); it reaches
        :meth:`apply_sandbox_fallback` as ``context=`` and is passed only when
        set, so an adapter whose override predates the keyword is called
        exactly as before.
        """
        argv = self.build_agent_command(
            prompt, model, profile, timeout_s=timeout_s, schema=schema
        )
        rung = sandbox_rung_id(sandbox_fallback)
        if rung:
            extra: Dict[str, Any] = {}
            if jail_context is not None:
                extra["context"] = jail_context
            if write_consent is not None:
                extra["consent"] = write_consent
            argv = self.apply_sandbox_fallback(argv, profile, rung, **extra)
        if transport == "argv":
            return argv, None
        if transport == "stdin" and self.supports_prompt_transport("stdin"):
            if argv and argv[-1] == prompt:
                return argv[:-1], prompt
            return [arg for arg in argv if arg != prompt], prompt
        raise ValueError(
            f"{self.name} does not support the {transport!r} prompt transport "
            f"for profile {profile!r} (supported: "
            f"{', '.join(self.supported_prompt_transports)})"
        )

    def parse_usage(self, stdout: str, stderr: str) -> Optional[Dict[str, Any]]:
        """Extract normalized usage from a captured stream, or ``None`` (D3j).

        One closed, all-optional structure: ``input_tokens``, ``output_tokens``,
        ``total_tokens``, ``cached_input_tokens``, ``tool_uses``, ``cost_usd``.
        **Absent means "not reported", never 0** — a zero would average into
        per-phase totals and read as a free run — and nothing is ever derived
        from character counts or estimated.

        Returns ``None`` by default: an adapter is duration-only until a captured
        fixture proves its extractor.
        """
        return None

    def audit_readonly_stream(self, raw_stream: str) -> Optional[Any]:
        """Could this attempt have written to the tree? (plan §4.2, option B.)

        Called by ``llm_client.invoke_with_provider`` on the attempt's **full**
        stdout, before ``_attach_stdout_excerpt`` bounds it, on every outcome
        that has a stream; only the compact
        :class:`~utils.readonly_audit.AuditVerdict` rides out, as
        ``details['readonly_audit']``. ``None`` (the default) means *no opinion*:
        an adapter without a structured action stream, whose uncontained slots
        keep the porcelain check's fail-closed verdict unchanged. An override
        must fail closed on anything it cannot classify, and must never raise
        (the caller treats a raise as ``None``).
        """
        return None

    def salvage_text(self, stdout: str) -> Optional[str]:
        """The assistant's answer text in a failed attempt's stdout, for salvage.

        Called by ``llm_client`` on the attempt's **full** stdout at each of the
        three failure sites (non-zero exit, exit-0 parse failure, timeout),
        before any bounding, like :meth:`audit_readonly_stream`. The caller
        redacts and caps what comes back and stores it as
        ``details['salvage_text']``, which the salvage gate then reads *instead
        of* the raw stream excerpt. That matters for a transport-stream adapter:
        its events carry ``content`` arrays (``thinking``/``toolCall`` parts)
        that pass ``has_salvageable_json`` as if they were findings, so a
        reviewer killed mid-tool-call would otherwise be "salvaged" from pure
        event data (plan: review-run-scope-salvage-and-failure-visibility §4).

        The contract has three answers:

        - ``None`` (this default): *no opinion*. No reducer applies, the key
          stays absent, and the gate keeps reading ``stdout_excerpt`` then
          stderr, as before.
        - a non-empty string: *this is the answer text* — only the assistant's
          own words, never tool output, thinking or event framing.
        - ``""``: *nothing to salvage*. That verdict is final: the gate sees
          ``""`` and no other channel, because an adapter that reduces its
          stream has declared stdout a transport, and its stderr holds only
          diagnostics (which can themselves look like a JSON array).

        An override must never raise. If one does anyway, the caller records
        ``""`` rather than ``None``: by overriding, the adapter declared its
        stdout a transport stream, so falling back to that raw stream would
        bring back the bug this hook exists to remove.
        """
        return None

    def native_structured_output(self, stdout: str) -> Any:
        """The document the CLI's own schema enforcement produced, or ``None``.

        Only meaningful on a dispatch that carried a schema
        (:attr:`structured_output_support`): the caller —
        ``structured_output.classify_attempt`` — validates whatever this returns
        against the same schema file before calling it ``native``, so an
        override can never upgrade prose to validated output. The default has
        no opinion: claude's ``structured_output`` key is read off its result
        envelope by the caller itself. An adapter whose CLI delivers the
        constrained document somewhere else (codex: the final
        ``agent_message``'s whole text) says where. Must never raise.
        """
        return None

    def parse_version(self, stdout: str, stderr: str) -> Optional[str]:
        """Recover the CLI version from ``version_cmd`` output (D3m).

        The default finds the first dotted numeric token on either stream, which
        covers ``codex-cli 0.146.0``, ``1.18.12`` and ``2.1.224 (Claude Code)``
        alike. **Both streams are read** (§5.4): some CLIs banner their version
        to stderr and opencode is stdout-only, so a probe that read one stream
        would report ``unknown`` for whichever half of the roster it guessed
        wrong. Unparseable output is ``None`` (recorded ``unknown`` plus a
        warning, never a block: a CLI that dropped ``--version`` still answers
        prompts fine).
        """
        import re

        for text in (stdout or "", stderr or ""):
            match = re.search(r"\b(\d+\.\d+(?:\.\d+)*)\b", text)
            if match:
                return match.group(1)
        return None

    # ── M14 (§5.4.1) — the shared per-flag capability gate ────────────────
    #
    # Implemented once, here. The three one-off gates this replaced (L7's
    # `--fallback-model`, M7's `--json-schema` and M1's `--trust --mode ask`)
    # each had their own copy of the probe, the cache and the token regex; what
    # stays with each adapter is only what is genuinely its own — which flags it
    # gates, and what one WARN says about the capability a declined flag costs.

    def gate_binary_name(self) -> str:
        """The binary the gate probes, taken from what the adapter **declares**.

        ``version_cmd[0]`` first, then ``auth_check[0]`` — both are the CLI's own
        name by construction, so no adapter has to repeat that literal for the
        gate's benefit. An adapter that declares neither has no probeable binary
        here, which resolves to "undecidable" and therefore to declining an
        optional flag; it never resolves to a refusal.
        """
        for argv in (self.version_cmd, self.auth_check):
            if argv:
                return str(argv[0])
        return ""

    def gate_binary(self, *, runnable: bool = False) -> Optional[str]:
        """The resolved path the gate would read, or ``None``.

        ``runnable=True`` additionally requires a spawnable file, which is what
        the **load-bearing** form asks for: a path that cannot be spawned cannot
        reject a flag either, and turning "not installed" into "version-too-low"
        would only lose information — ``is_available()`` already reports that,
        precisely, and callers check it before building anything.
        ``shutil.which`` already tests for an executable, so in production the
        extra check is a no-op guarding against a resolver that points somewhere
        unrunnable.
        """
        name = self.gate_binary_name()
        if not name:
            return None
        binary = shutil.which(name)
        if binary is None:
            return None
        if runnable and not (os.path.isfile(binary) and os.access(binary, os.X_OK)):
            return None
        return binary

    def gate_probe_env(self) -> Dict[str, str]:
        """The environment one help probe runs in — §5.4.1's containment clause.

        Composed by :func:`build_child_env`, the same builder both spawn lanes
        go through, so the flags a run emits cannot depend on which lane asked.
        On top of it: the ``generate`` profile's git block (a probe must never
        reach a credential helper), and ``TERM=dumb`` / a wide ``COLUMNS`` /
        ``NO_COLOR`` so the help is rendered in full — §3.6's own history is a
        *truncated* help rendering that hid what a flag required.

        The adapter's ``get_remove_env`` is applied through the builder, which is
        what keeps a probe run from inside a Claude Code session from being
        refused by that CLI's nested-session guard.
        """
        delta = dict(git_env(PROFILE_GENERATE))
        delta.update({"TERM": "dumb", "COLUMNS": "1000", "NO_COLOR": "1"})
        return build_child_env(self, provider_env=delta) or dict(os.environ)

    def flag_tokens(self, *, runnable: bool = False) -> FrozenSet[str]:
        """Every long option this CLI's own help documents, or ``frozenset()``."""
        binary = self.gate_binary(runnable=runnable)
        if not binary:
            return frozenset()
        return read_help_tokens(
            binary, help_argv=tuple(self.help_argv), env=self.gate_probe_env()
        )

    def supports_flag(self, flag: str) -> bool:
        """§5.4.1's gate in its **optional-flag** form: undecidable ⇒ ``False``.

        On an older CLI an unrecognised flag is not a degraded run, it is
        ``unknown option`` and a dead slot, so this declines toward the status
        quo: the flag is omitted, the run proceeds, and the caller emits one WARN
        naming the capability the run is doing without.

        A flag the adapter declares in :attr:`flags_verified_at_floor` is
        supported **without a probe** — §5.4.1(a)'s exemption, granted only to a
        flag verified functionally at the declared ``min_version``.
        """
        if flag in tuple(self.flags_verified_at_floor):
            return True
        return flag in self.flag_tokens()

    def missing_flags(self, flags: Iterable[str]) -> Tuple[str, ...]:
        """§5.4.1's gate in its **load-bearing** form: which of ``flags`` is unconfirmed.

        For an argv that has no safe degraded form — cursor's ``--trust``/
        ``--mode`` pair, where dropping ``--trust`` fails the launch and the only
        other way past the trust gate is the ``-f``/``--yolo`` write bypass — the
        caller refuses the slot naming exactly what came back from here.

        **An unresolvable or unspawnable binary reports nothing missing.** That
        is the asymmetry with :meth:`supports_flag` and it is deliberate: an
        absent CLI is ``is_available()``'s refusal to make, with its own precise
        message, and a binary that cannot be spawned cannot reject a flag.
        """
        binary = self.gate_binary(runnable=True)
        if not binary:
            return ()
        tokens = read_help_tokens(
            binary, help_argv=tuple(self.help_argv), env=self.gate_probe_env()
        )
        exempt = tuple(self.flags_verified_at_floor)
        return tuple(
            flag for flag in flags if flag not in tokens and flag not in exempt
        )

    def build_command_for_transport(
        self,
        prompt: str,
        model: str,
        transport: str = "argv",
        prompt_file: Optional[str] = None,
        *,
        timeout_s: Optional[int] = None,
        schema: Optional[StructuredSchema] = None,
        sandbox_fallback: Optional[str] = None,
        cwd: Optional[str] = None,
        jail_context: Optional["JailContext"] = None,
    ) -> Tuple[List[str], Optional[str]]:
        """Build argv plus the text to write to the child's stdin.

        Args:
            prompt: The prompt text.
            model: The model identifier.
            transport: ``"argv"`` (prompt is an argv element), ``"stdin"``
                (``build_command`` omits it and the caller writes it to the
                child's stdin) or ``"file"`` (prompt already written to
                ``prompt_file``, whose path travels on argv).
            prompt_file: Path the prompt was written to, for ``"file"``.
            timeout_s: The caller's already-resolved outer timeout, forwarded to
                :meth:`build_command` (§9.6.a/b). This is the Lane A leg:
                ``invoke_with_provider`` computes ``effective_timeout`` before it
                builds anything, so the adapter never re-derives it.
            sandbox_fallback: The fan-out's D6 override (2026-09-17): the rung
                id ``sandbox_refusal`` selected for this slot (probe
                ``unavailable``, a rung the policy permits, profile
                ``generate``), rendered through :meth:`apply_sandbox_fallback`.
                ``True`` is the pre-rung spelling of the uncontained rung.
                Keyword-only, default ``None``, and ignored by every adapter
                that keeps the default hook, so every existing argv is
                rendered byte-for-byte.
            jail_context: The attempt's :class:`JailContext`, set by the
                invoker only for a slot on a wrapping rung (the plugin-landlock
                jail), and passed by the caller only when set, so the eight
                adapters that override this method without the keyword are
                called exactly as before.
            cwd: The directory the child will really be spawned in (``None``
                means "inherit this process's"), threaded from the spawn site on
                exactly the terms :meth:`resolve_env` already takes it — this and
                that hook are the only two that see the real workspace, and an
                adapter whose **argv** carries a workspace-scoped token needs it
                for the same reason an adapter's env delta does. omp is that
                adapter: launched from ``$HOME`` without ``--cwd`` it silently
                relocates to ``/tmp``, with nothing on either channel to say so,
                and a reviewer that moved there reads none of the repo's files
                while still exiting 0.

                **This composition ignores it**, exactly as
                :meth:`resolve_env`'s does, and does *not* forward it to
                :meth:`build_command` — so the abstract signature is unchanged
                and seventeen adapters render argv byte-for-byte. An adapter that
                wants it overrides this method and declares ``cwd`` on its own
                ``build_command``.

        Returns:
            ``(argv, stdin_text)``; ``stdin_text`` is the text to write to the
            child's stdin. That is the prompt under ``"stdin"``; on ``"argv"``
            it is ``None`` unless the adapter feeds the child interactive
            answers — aider, whose decline supply answers its "Add file to the
            chat?" prompts (plans/ask-answer-recovery-and-false-success.md
            D4.2). This base composition returns ``None`` on ``"argv"``.

        Raises:
            ValueError: when this adapter does not support ``transport``.
        """
        if transport == "argv":
            argv = self.build_command(
                prompt, model, timeout_s=timeout_s, schema=schema
            )
            rung = sandbox_rung_id(sandbox_fallback)
            if rung:
                argv = self.apply_sandbox_fallback(
                    argv, PROFILE_GENERATE, rung,
                    **({"context": jail_context} if jail_context is not None else {}),
                )
            return argv, None
        raise ValueError(
            f"{self.name} does not support the {transport!r} prompt transport "
            f"(supported: {', '.join(self.supported_prompt_transports)})"
        )

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier (e.g., 'cursor-agent', 'gemini').

        Returns:
            A unique string identifier for this provider.
        """
        pass

    @property
    @abstractmethod
    def default_timeout(self) -> int:
        """Default timeout in seconds for this provider.

        Returns:
            The default number of seconds to wait before timing out.
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the CLI tool is available in PATH.

        Returns:
            True if the CLI tool can be found and executed, False otherwise.
        """
        pass

    @abstractmethod
    def build_command(
        self,
        prompt: str,
        model: str,
        *,
        timeout_s: Optional[int] = None,
        schema: Optional[StructuredSchema] = None,
    ) -> List[str]:
        """Build the command line arguments for invocation.

        Args:
            prompt: The prompt text to send to the LLM.
            model: The model identifier to use for generation.
            timeout_s: The caller's already-resolved outer timeout in whole
                seconds, for the adapters whose CLI has an internal cutoff of
                its own to keep *under* it (§9.6.a). Twelve of the thirteen
                adapters have no such flag and ignore it.

                It is **keyword-only and optional on purpose**. Adapter
                instances are module-level singletons shared across a concurrent
                fan-out, so stashing a per-call timeout on ``self`` would be a
                data race rather than an API; and ``timeout_s=None`` must render
                argv byte-for-byte identical to what the adapter emitted before
                this parameter existed, which is what makes dropping the one
                call site in ``llm_client`` a complete rollback.
            schema: §4.2.2's optional structured-output schema, on the same terms
                and for the same reasons as ``timeout_s``: keyword-only,
                optional, ignored by the eleven adapters that declare no
                :attr:`structured_output_support`, and ``schema=None`` — the
                default and the only value those eleven ever see — renders argv
                **byte-for-byte identical** to today's. That is what keeps every
                existing ``expected_argv.yaml`` row green and what makes the
                per-adapter flag the off switch (§14.4).

        Returns:
            A list of command line arguments suitable for subprocess.run().
        """
        pass

    @abstractmethod
    def parse_output(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """Parse output and return structured result.

        Args:
            stdout: The standard output from the CLI invocation.
            stderr: The standard error from the CLI invocation.

        Returns:
            A dictionary with at least 'success' (bool) and 'data' keys.
            On success, 'data' contains the parsed response.
            On failure, 'data' may contain error information.
        """
        pass

    def describe_unlisted_model(
        self, model: str, *, anchor: Optional[str] = None
    ) -> ModelVerdict:
        """Is ``model`` in this CLI's own live catalog? (D3 step 4)

        The preflight's *catalog* leg — distinct from
        ``describe_unresolvable_model`` (structural, catalog-free) and from the
        advisory ``is_model_valid`` warning about *our* configured list. This is
        the one leg that may spawn the CLI, and only an adapter with a listing
        subcommand overrides it (opencode's ``opencode models``). Every adapter
        answers; this default answers **unknown** — ``ModelVerdict(known=None)``
        — which refuses nothing, warns nothing, and leaves D4's dispatch-time
        classifier to catch a real miss one attempt later in the provider's own
        words. Declared here, typed, the way :meth:`describe_failure` is, so the
        executor calls it directly rather than ``getattr``-ing a name that
        exists on one adapter.

        ``anchor`` is the run anchor a dispatch resolves config against, so an
        override reading the listing under its dispatch context (a hermetic
        config-home redirect, say) sees the same effective configuration the
        dispatch it vets will.
        """
        return ModelVerdict(known=None, detail="", suggestions=())

    def config_credential_source(
        self,
        model: str,
        *,
        profile: str = PROFILE_AGENT_READONLY,
        anchor: Optional[str] = None,
        cwd: Optional[str] = None,
        env_builder: Optional[Callable[[], Optional[Mapping[str, str]]]] = None,
    ) -> str:
        """Does the dispatch's own config supply this model's credential? (§8)

        Asked by the executor's auth leg only when ``auth_check`` said ``False``
        for a model that needs a credential. Two answers, never a third:
        :data:`CONFIG_AUTH_DECLARED` (the resolved config declares the
        provider, so the refusal is skipped and the auth state reads
        ``config``) or :data:`CONFIG_AUTH_UNKNOWN` (today's
        ``not_authenticated`` refusal stands). This default answers
        ``unknown``, so every adapter that does not override it is exactly
        what it was. Only opencode, whose ``auth list`` cannot see a
        config-declared provider, overrides it.
        """
        return CONFIG_AUTH_UNKNOWN

    def describe_failure(self, stdout: str, stderr: str) -> Optional[str]:
        """Extract a human-readable reason from a failed invocation.

        **Either channel, not one of them.** The hook was written for the
        stdout direction — ``parse_output`` is only called when the CLI exits 0,
        so a provider that reports its errors on *stdout* rather than stderr
        would otherwise have them discarded (opencode and muse are both that
        shape) — but the *inverse* shape is just as common and just as blind.
        ``pi`` writes **zero bytes to stdout on all ten** of its committed
        failure captures and ``gemini`` on **eight of its nine**, putting 100%
        of the diagnosis on stderr; before C4 both adapters took ``stderr`` in
        ``parse_output`` and never mentioned it again. So the rule is a
        *channel* rule rather than a stream name: **stderr is the diagnosis,
        stdout is the answer** — an override reads whichever channel its CLI
        really writes its reason on, and returns one short line of it.

        Reading stderr here is not duplication of what the caller already has.
        Neither caller prints raw stderr of its own: Lane A builds
        ``f"{provider} exited with code {n}"`` and appends only this hook's
        answer (``llm_client``), Lane B folds it into the rung-4 message
        (``subagent_executor``), and the full text stays in
        ``details["stderr"]`` and the log file. This hook is the **summary**,
        so a 15 KB retry log must be reduced to one line rather than copied.

        **Diagnostics, never classification.** Both callers wrap this in
        ``try``/``except`` and neither lets its answer change a category —
        that is :meth:`classify_failure`'s job, on declared pattern tables. An
        override may not move any run's classification, and returning ``None``
        must always stay safe.

        Args:
            stdout: The standard output from the failed CLI invocation.
            stderr: The standard error from the failed CLI invocation.

        Returns:
            A short description of the failure, or None when the provider has
            nothing to add beyond the exit code and stderr. None by default.
        """
        return None

    def get_env(self, model: str) -> Dict[str, str]:
        """Return **adapter-specific** environment variables for subprocess.

        Override this method if the provider requires environment variables
        for configuration (e.g., model selection).

        This is deliberately *not* where the non-interactive git block lives:
        that block is profile-scoped (§2.2) and this hook has no profile, and it
        must reach adapters that override this method too. It is composed in
        :meth:`resolve_env`, which is what both spawn sites call. **Never move
        ``git_env``'s ``GIT_CONFIG_COUNT`` / ``credential.helper=""`` keys in
        here** — they would then apply to ``agent-write``, whose git access to
        the user's own remotes the scoping exists to preserve.

        Args:
            model: The model identifier to use for generation.

        Returns:
            A dictionary of environment variables to set for the subprocess.
            Empty dict by default.
        """
        return {}

    def git_credential_helper_policy(self, anchor: Optional[str] = None) -> str:
        """This provider's resolved ``git_env.credential_helper`` (§2.2).

        ``MULTI_LLM_GIT_CREDENTIAL_HELPER`` → ``providers.<name>.git_env`` →
        top-level ``git_env`` → ``auto``. Read through the registry accessor
        rather than by indexing the config, exactly like the ``driver.*`` keys.
        """
        try:  # pragma: no cover - import shim mirrors the rest of utils/
            from ..provider_registry import get_git_credential_helper
        except ImportError:  # pragma: no cover - direct-script import shim
            from utils.provider_registry import get_git_credential_helper
        return get_git_credential_helper(self.name, anchor=anchor)

    def resolve_env(
        self,
        model: str,
        profile: str = PROFILE_GENERATE,
        *,
        credential_helper: Optional[str] = None,
        base_env: Optional[Mapping[str, str]] = None,
        anchor: Optional[str] = None,
        cwd: Optional[str] = None,
    ) -> Dict[str, str]:
        """The full env delta a spawn applies: the §2.2 git block, then the adapter's.

        The one composition point, called by both spawn sites
        (``llm_client.call_llm`` for the Lane A fan-out under ``generate``, and
        ``subagent_executor._spawn`` with the dispatch's own profile), so the git
        block cannot be present on one lane and missing on the other. The
        adapter's own :meth:`get_env` is merged **last** and therefore wins on any
        key it names.

        ``profile`` is what scopes the credential-helper wipe, and
        ``agent-write`` must keep resolving to *no* wipe — see :func:`git_env`.

        ``cwd`` is the directory the child will really be spawned in (``None``
        means "inherit this process's"), and the base composition ignores it: it
        is here because this is the only hook that sees every real spawn, so an
        adapter whose delta carries a **workspace-scoped side effect** — cursor's
        snapshot/restore guard, which has to know which ``.workspace-trusted``
        markers are its own — can be told the workspace instead of guessing
        ``os.getcwd()``. Both spawn sites pass it; a caller that only wants the
        env may omit it.
        """
        policy = (
            credential_helper
            if credential_helper is not None
            else self.git_credential_helper_policy(anchor=anchor)
        )
        env = git_env(profile, credential_helper=policy, base_env=base_env)
        env.update(self.get_env(model) or {})
        return env

    def get_remove_env(
        self,
        anchor: Optional[str] = None,
        base_env: Optional[Mapping[str, str]] = None,
    ) -> List[str]:
        """Return environment variable names to remove for subprocess.

        Override this method if the provider needs certain env vars stripped
        from the inherited environment (e.g., to avoid nested-session guards).

        Both parameters are the dispatch's own context, supplied by
        :func:`build_child_env`, and both are **optional in every direction**:
        an override whose list is static may keep the zero-parameter signature
        (:func:`_provider_removals` passes each keyword only to a hook that
        declares it), and a caller with no dispatch in hand may omit them, which
        is what a bare ``provider.get_remove_env()`` means.

        Args:
            anchor: The plan/run anchor this dispatch resolved against, so an
                override reading `providers.<name>.*` policy resolves it against
                the **requested project** rather than the process CWD.
            base_env: The environment the child will inherit, so an override
                deciding by presence judges the composed source rather than
                ``os.environ``. ``None`` means ``os.environ``.

        Returns:
            A list of environment variable names to remove. Empty by default.
        """
        return []

    # ── M10 (§5.1) — the typed status that sits beside is_available() ────────

    def describe_availability(
        self,
        *,
        auth: Optional[bool] = None,
        version: Optional[str] = None,
        credentials_required: bool = True,
    ) -> AvailabilityReport:
        """Why this runner is or is not usable, as a typed state (§5.1).

        **This does not replace :meth:`is_available`, and it does not widen it.**
        ``is_available()`` keeps its ``-> bool`` signature, its name and its
        meaning: it is the dispatch gate, it stays binary-only, and every
        existing ``if provider.is_available():`` behaves exactly as it did. This
        method is the *sibling* that can say **why**, for the surfaces that
        render a sentence to a human rather than branch on a yes/no.

        The two can never drift, because the first thing done here is to ask
        ``is_available()`` and return :attr:`Availability.BINARY_MISSING` when —
        and only when — it says no. That makes the compatibility identity

            ``self.is_available() == self.describe_availability().launchable``

        true *by construction* for every adapter in the registry, including ones
        that do not exist yet, and ``tests/test_availability.py`` asserts it
        parametrized over the live registry rather than over a name list.

        **It never spawns a child.** The probes this reads (``auth_check``,
        ``version_cmd``) are run once per distinct runner per run by the
        executor's preflight, which caches them; re-running them from inside a
        picker loop would turn a `shutil.which` into a fan-out of subprocesses.
        So evidence is *handed in*, and both parameters default to "nothing was
        probed".

        **Implemented once, here.** No adapter is required to override it; the
        seventeen subclasses gain nothing to implement. An override that changes
        the ``BINARY_MISSING`` leg breaks the identity above and the test says so.

        Args:
            auth: exactly what :meth:`classify_auth_probe` returned for this
                runner's ``auth_check`` — ``True`` clean, ``False`` a recognised
                login notice, ``None`` inconclusive — or ``None`` when no probe
                was run or the adapter declares none. The two ``None`` readings
                deliberately collapse: "the probe could not tell" and "there is
                no probe" are the same amount of evidence, which is none.
            version: exactly what :meth:`parse_version` recovered, or ``None`` /
                ``"unknown"`` when the version was not read. Only its leading
                dotted-numeric token is used, for the comparison *and* for the
                sentence (:func:`_version_token`), so trailing build noise is
                tolerated and nothing else from this string can reach a stored
                ``detail``.
            credentials_required: what :meth:`model_needs_credentials` answers
                for the model this report is about (D3 step 2). ``False``
                suppresses the ``NEEDS_AUTH`` leg — the preflight skips its
                refusal for a declared credential-free model, and a status that
                reported ``NEEDS_AUTH`` about a runner that dispatches fine
                would be the same drift facing the other way. It is declared
                adapter data like everything else read here; nothing is
                spawned. Defaults to ``True``, today's behaviour.

        Returns:
            An :class:`AvailabilityReport`. Its ``detail`` is built only from
            declared adapter data, never from probe output.

        The order of the legs below is the order the preflight applies its own
        refusals (version before auth), so a report and the refusal a run would
        actually hit cannot name different problems for the same runner.

        ``READY`` requires a **positive** verdict and is never inferred from
        silence: an adapter that declares no auth probe reports ``UNKNOWN``,
        never ``READY`` and never ``NEEDS_AUTH``. That is the fail-open posture
        held *by construction* rather than by convention.

        **cursor-agent was that row and is not any more.** It declared neither
        ``auth_check`` nor ``version_cmd`` when this method was written; M13
        shipped its real ``cursor-agent status --format json`` probe and M14 its
        ``cursor-agent --version``, so it now declares **both** and reports a
        verdict like every other row. Deleting either declaration to "fix" a
        cursor report would put it back to a permanent ``UNKNOWN`` — the probes
        are what upgrade that row, and a default never can.
        """
        name = self.name
        if not self.is_available():
            return AvailabilityReport(
                Availability.BINARY_MISSING,
                f"{name}: the CLI is not on PATH.",
            )

        # Only the numeric token survives into the comparison and the sentence —
        # see :func:`_version_token`. ``"unknown"`` carries no token, so the
        # executor's own "version not read" value falls out here for free.
        read = _version_token(version or "")
        minimum = (self.min_version or "").strip()
        if read and minimum and _version_below(read, minimum):
            return AvailabilityReport(
                Availability.VERSION_TOO_LOW,
                f"{name} {read} is older than the {minimum} this release parses; "
                f"upgrade {name} to >= {minimum}{_upgrade_suffix(self, minimum)}",
            )

        if auth is False and not credentials_required:
            # The probe's verdict is real and still recorded by the preflight;
            # what it may not do is refuse a model the adapter declares serves
            # with no credential present. Mirror that here so the report and
            # the refusal a run would hit cannot name different problems.
            return AvailabilityReport(
                Availability.READY,
                f"{name} is installed; its auth probe recognised a login notice, "
                f"but this model is declared to need no credential.",
            )
        if auth is False:
            login = (self.login_cmd or "").strip()
            fix = f" Fix: run `{login}`." if login else ""
            return AvailabilityReport(
                Availability.NEEDS_AUTH,
                f"{name} is installed but its auth probe recognised a login "
                f"notice.{fix}",
            )
        if auth is True:
            return AvailabilityReport(
                Availability.READY,
                f"{name} is installed and its auth probe came back clean.",
            )

        probe = " ".join(self.auth_check) if self.auth_check else ""
        why = (
            f"`{probe}` was inconclusive"
            if probe
            else f"{name} declares no auth probe"
        )
        return AvailabilityReport(
            Availability.UNKNOWN,
            f"{name} is installed; {why}, so whether it is logged in could not "
            f"be determined.",
        )
