"""The sandbox fallback (D6): its policies, the rungs an adapter declares, the
write posture, and the notices a slot on a fallback rung prints.

:class:`SandboxRung`, :class:`JailRequest` and :class:`JailContext`, which write
scopes a rung and the host's posture allow, and the ``[SANDBOX_*]`` marker
lines. The walk down the rungs belongs to its callers, the fan-out and the
executor; this module is what they walk. ``base`` re-exports every name here
for reading (docs/development/providers.md#the-provider-base-modules).
"""

import os
from dataclasses import dataclass
from typing import Any, List, Mapping, Optional, Sequence, Tuple

from . import types, version_gate


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
SANDBOX_FALLBACK_PROFILES: Tuple[str, ...] = (types.PROFILE_GENERATE, types.PROFILE_AGENT_READONLY)

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
SANDBOX_WRITE_FALLBACK_PROFILES: Tuple[str, ...] = (types.PROFILE_AGENT_WRITE,)

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
    walked in order by ``sandbox_walk.sandbox_verdict`` only after the
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
    token = version_gate._version_token(str(version))
    if not token:
        return False
    return version_gate.version_tuple(token) >= version_gate.version_tuple(rung.removed_at[0])


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
    and ``sandbox_walk._detect_sandbox`` pick it by grade — so the reader
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
