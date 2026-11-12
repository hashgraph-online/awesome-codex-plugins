"""Starting one runner and reading back what it left: the spawn, the
jail, the timeout kill, and the grant a write dispatch gets.

:func:`_spawn` runs one attempt and returns its :class:`_Capture`: the
schema leg (:func:`_spawn_with_schema`), the child's environment
(:func:`dispatch_child_env`, which the auth probe reads too) and cached
version (:func:`_preflight_version`), the process tree, the plugin's
Landlock jail and what it reported (:func:`_read_jailed_outcome`, its
``[JAIL_DENIED]`` line from ``landlock_dispatch.jail_denied_text``), the
argv an audit record shows (:func:`render_audit_argv`, :func:`audit_argv`),
and the timeout kill (:func:`_kill_timed_out`,
``process_control.unconfirmed_kill``, :func:`_drain_after_kill`). The grant a write
dispatch's jail gets is derived from its kind (:func:`_dispatch_grant`,
``runner_selection.WRITE_SCOPE_BY_KIND``), never from the task JSON.

``utils.subagent_executor`` re-exports every name defined here for reading
only: patch one here, never through the executor
(docs/development/delegation.md#where-the-executors-helpers-live).
"""

from __future__ import annotations

import contextlib
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, FrozenSet, List, Optional, Sequence, Tuple

from . import host_capabilities as caps
from . import process_capture
from . import process_control
from . import structured_output
from .llm_client import (
    _resolve_executable,
    expand_env_home,
    provider_dispatch_context,
)
from . import landlock_dispatch
from .providers.base import (
    CODEX_HOME_CHECK_MARKER,
    HOST_POSTURE_FULL_ACCESS,
    INCIDENTAL_LANE_EXECUTOR,
    JailContext,
    JailRequest,
    WRITE_SCOPE_REPO_WIDE,
    WRITE_SCOPES_BY_CONSENT,
    WRITE_SCOPES_ON_RUNG,
    WritePostureConsent,
    PROFILE_AGENT_WRITE,
    SandboxRung,
    build_child_env,
)
from .subagent_tasks import WRITE_KINDS
from . import task_outcome as _task_outcome
from . import task_result as _task_result
from . import runner_selection as _runner_selection
from . import probe_state as _probe_state
from . import sandbox_walk as _sandbox_walk


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Grace between the SIGTERM and the SIGKILL of a timed-out dispatch's process
#: group (D3k rung 2). Short on purpose: the child has already spent its entire
#: ``subagent_timeout_s``, so this is teardown, not one more chance to finish.
TIMEOUT_KILL_GRACE_S = 0.5

#: Ceiling on the post-kill drain, and the grace a runner's pipes get to reach
#: end of file once it has exited: the shared ``process_capture.DRAIN_S``. A
#: grandchild the kill did not reach still holds the inherited stdout pipe, so
#: the drain must be bounded — an unbounded one is the hang that turns a
#: timed-out task into a wedged batch.
TIMEOUT_DRAIN_S = process_capture.DRAIN_S


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

def _preflight_version(provider: Any) -> Optional[str]:
    """The version :func:`_detect_version` already read for this provider, or None.

    Strictly the cache (:data:`_VERSION_CACHE`), never a spawn: it is read on
    the dispatch path, once per dispatch, and handed to the adapter's dispatch
    context so a version-gated config key (opencode's
    ``continue_loop_on_deny``, plan T4.2) costs nothing beyond the preflight's
    one ``version_cmd`` per process. A recorded ``"unknown"`` is passed through
    as itself, so the adapter can tell "the read failed" from "no read here".
    """
    try:
        name = provider.name
    except Exception:  # noqa: BLE001 - a lookup may never end a dispatch
        return None
    return _probe_state._VERSION_CACHE.get(name) if isinstance(name, str) else None


def dispatch_child_env(
    provider: Any,
    model: str,
    profile: str,
    *,
    anchor: Optional[str] = None,
    cwd: Optional[str] = None,
) -> Optional[Dict[str, str]]:
    """The child environment one spawn of ``provider`` gets (plan §8 T8.13).

    ``resolve_env`` + ``build_child_env`` and nothing else: the two calls
    :func:`_spawn_in_context` makes, factored out so the auth probe and
    opencode's ``debug config`` reader (T8.3) see what a dispatch sees — the
    adapter's delta, the ``env_allowlist`` filter and the running host's
    ``env_guards``. ``None`` means "inherit this process's environment
    unchanged", exactly as :func:`build_child_env` returns it.

    Not pure for every adapter: cursor-agent's ``resolve_env`` creates its
    run-scoped profile directory (or arms its side-effect guard), both bounded
    and idempotent per process. Callers outside a dispatch therefore build it
    at most once per cache key and never hand one call's result to another
    spawn.
    """
    provider_env = expand_env_home(
        provider.resolve_env(model, profile, anchor=anchor, cwd=cwd)
    )
    host_guards, passthrough = _host_env_guards()
    return build_child_env(
        provider,
        provider_env=provider_env,
        host_guards=host_guards,
        host_passthrough=passthrough,
        anchor=anchor,
    )


def _host_env_guards() -> Tuple[List[str], List[str]]:
    """``(strip, passthrough)`` from the running host's ``env_guards`` (D3c/D5b).

    Under ``subagents: executor`` the runner is a *grandchild* — the host's shell
    tool spawned this dispatcher, this dispatcher spawns the runner — so the child
    inherits the host's injected variables on top of the runner's own: the
    nested-session marker that makes a same-binary runner refuse to start, and the
    session/skill ids that make it join or overwrite the parent's session instead
    of running its own turn. The adapter's ``get_remove_env()`` only knows about
    the *runner*, so the strip list is the union of the two, composed here at the
    single spawn site.

    Deliberately non-fatal, like :func:`_host_ceiling`: a partial install that
    cannot answer falls back to the adapter's own list rather than failing a
    dispatch.
    """
    try:
        declared = caps.env_guards(caps.resolve_host_id(sys.argv[1:]))
    except Exception:  # pragma: no cover - unknown host / missing data
        return [], []
    return (
        [*declared["guards"], *declared["session_scoped"]],
        list(declared["passthrough"]),
    )


@dataclass
class _Capture:
    """One dispatch's capture on this lane.

    The stream half (``stdout`` to ``launch_error``, and ``capped_streams``) is
    ``provider_outcome.Capture``'s, field for field, and this lane's readers
    (``_classify_pre_parse``, ``_extract_result_and_syntax``,
    ``_classify_failed_run``) take either. This one stays mutable: the spawn
    fills it in steps, the jail read-back adds its evidence once the child is
    gone, and ``_parse_and_validate`` records ``reply_syntax_error`` for the
    re-ask. ``tests/test_provider_outcome.py`` holds the two to the same fields.
    """

    stdout: str = ""
    stderr: str = ""
    exit_code: Optional[int] = None
    duration: float = 0.0
    timed_out: bool = False
    launch_error: Optional[str] = None
    argv: List[str] = field(default_factory=list)
    #: Plan codex-sandbox-unavailable §6 F1 (2026-09-30), set only for an
    #: attempt on a wrapping rung (the plugin's Landlock jail). Paths, classes
    #: and counts only — never output text beyond the ≤300-char excerpt the
    #: ``[JAIL_DENIED]`` line quotes.
    #: The rung id the attempt ran on.
    sandbox_rung: Optional[str] = None
    #: ``JailEvidence.to_dict()`` for a codex-internal EACCES (any class).
    jail_evidence: Optional[Dict[str, Any]] = None
    #: The one ``[JAIL_DENIED]`` line when the attempt failed on the jail
    #: (class ``jail`` or ``probable``, or a grant refused before the spawn):
    #: a non-retryable failure that never moves to another rung.
    jail_denied_line: Optional[str] = None
    #: The stream's denials (``landlock_dispatch.JailDenials``), read from the
    #: FULL stdout before any excerpt is bounded.
    jail_denials: Optional[Any] = None
    #: ``HomeChange.to_dict()`` when ``$CODEX_HOME``'s security-relevant set
    #: changed during the attempt (warn-only in this lane).
    home_change: Optional[Dict[str, Any]] = None
    #: Why the reply's JSON did not parse, as one redacted line, when the
    #: extractor served only a piece of a broken document and that piece failed
    #: validation; set by :func:`_parse_and_validate`, read by the re-ask.
    reply_syntax_error: Optional[str] = None
    #: The streams the capture cut at :data:`MAX_STREAM_BYTES`
    #: (``process_capture``). A capped stdout is refused at rung 5, unparsed.
    capped_streams: FrozenSet[str] = frozenset()
    #: The timeout kill's verdict (:func:`_kill_timed_out`), and the runner's
    #: pid it was about; ``None`` when no timeout kill was made.
    kill_verdict: Optional[str] = None
    kill_pid: Optional[int] = None
    #: Set only with ``timed_out``: the adapter's stdout watch asked for the
    #: stop, and this is its reason (``process_capture.StreamStopped``).
    stream_stop: Optional[str] = None
    #: The runner exited while a process it started still held its output
    #: pipe, and its process group was stopped as at a timeout before the
    #: dispatch returned (:func:`_stop_held_group`); ``pipe_held_verdict`` is
    #: that kill's verdict, ``unresolved`` when a pipe was still held after it.
    #: With both confirmed the dispatch goes on with the runner's answer and
    #: :func:`pipe_held_note` words it for the batch report; otherwise it is
    #: ended as a timeout, and ``held_pipe_note`` is what the timeout's
    #: failure adds to its words (docs/development/runtime.md, "A runner that
    #: exits while something it started holds its pipe").
    pipe_held: bool = False
    pipe_held_verdict: Optional[str] = None
    held_pipe_note: Optional[str] = None


@dataclass(frozen=True)
class _JailSpawn:
    """What a spawn on a wrapping rung carries from :func:`_spawn` down to
    :func:`_spawn_in_context`: the rung, the lane's request and this attempt's
    scratch directory. An argument, dropped with the attempt — never stored."""

    rung: SandboxRung
    request: JailRequest
    tmpdir: str


class SandboxBackstopViolation(_task_outcome.ExecutorError):
    """An ``agent-write`` argv carrying ``danger-full-access`` reached the spawn
    without the jail's wrapper prefix or an F5 consent, or with a grant whose
    write scope the rung does not serve, or an F5 consent whose scope F5 does
    not cover (``repo-wide``; plan steps 3 and 3b's backstop). Raised before
    ``Popen``: a write profile never renders the uncontained value unwrapped,
    whatever a gate above got wrong."""


def _wrapping_rung(provider: Any, profile: str, rung_id: Optional[str]) -> Optional[SandboxRung]:
    """The declared rung ``rung_id`` of ``profile``'s ladder when it wraps the
    CLI (the plugin's Landlock jail), else ``None``."""
    if not rung_id:
        return None
    for rung in _sandbox_walk._fallback_rungs(provider, profile):
        if rung.name == rung_id and getattr(rung, "wrapper", None):
            return rung
    return None


def render_audit_argv(
    provider: Any,
    model: str,
    profile: str,
    prompt: str,
    rung: Optional[str] = None,
    jail_request: Optional[JailRequest] = None,
    consent: Optional[WritePostureConsent] = None,
    *,
    launcher: Optional[Callable[[str], List[str]]] = None,
) -> List[str]:
    """The argv a dispatch on ``rung`` runs, for a record or a measure: never
    executed, and nothing is made (no scratch directory, no context, no
    allow-list resolution; F1 "Task-specific paths stay out of shared state").

    Built in the spawn's order (:func:`_spawn_in_context`): the adapter's
    command for ``profile``; ``rung`` rendered onto it; the executable resolved
    (``launcher``, given ``argv[0]``, when the caller measures what runs); and
    on the plugin's Landlock jail the wrapper prefix
    (``landlock_dispatch.preview_wrap_argv``). On the jail (a wrapping rung,
    :func:`_wrapping_rung`) the rung is rendered with ``jail_request``'s
    context and placeholder paths for the per-attempt scratch directory and
    ``$CODEX_HOME``; with no ``jail_request`` nothing of the rung is rendered
    (the spawn refuses that dispatch). Any other rung (F5's uncontained one,
    plan step 6) is rendered with ``consent`` as the dispatch renders it, so a
    record never shows a sandbox the child did not get.

    Raises what the adapter raises (a profile or a rung it will not render):
    each caller says what it records instead (:func:`audit_argv`).
    """
    argv = list(provider.build_agent_command(prompt, model, profile))
    wrap = _wrapping_rung(provider, profile, rung)
    if wrap is not None:
        if jail_request is None:
            wrap = None
        else:
            argv = list(provider.apply_sandbox_fallback(
                argv, profile, wrap.name,
                context=landlock_dispatch.preview_context(jail_request),
            ))
    elif rung:
        argv = list(provider.apply_sandbox_fallback(argv, profile, rung, consent=consent))
    if launcher is not None:
        argv = [*launcher(argv[0]), *argv[1:]]
    if wrap is not None:
        argv = landlock_dispatch.preview_wrap_argv(argv, wrap, jail_request)
    return argv


def audit_argv(
    provider: Any,
    provider_name: str,
    model: str,
    profile: str,
    prompt: str,
    rung: Optional[str] = None,
    jail_request: Optional[JailRequest] = None,
    consent: Optional[WritePostureConsent] = None,
) -> List[str]:
    """:func:`render_audit_argv` for an audit record or a dry run, which must
    never fail the dispatch it describes: a rung the adapter will not render
    leaves the bare command, and a profile it will not render names the runner
    (``[provider_name, "<profile unsupported>"]``)."""
    try:
        return render_audit_argv(provider, model, profile, prompt, rung, jail_request, consent)
    except Exception:  # noqa: BLE001 - a record must never fail a dispatch
        pass
    try:
        return render_audit_argv(provider, model, profile, prompt)
    except Exception:  # noqa: BLE001 - a record must never fail a dispatch
        return [provider_name, "<profile unsupported>"]


def _carries_full_access(argv: Sequence[str]) -> bool:
    """Whether ``argv`` renders codex's ``danger-full-access`` value — as the
    ``--sandbox`` value or a ``sandbox_mode`` override, never as prose inside
    a prompt."""
    for item in argv:
        text = str(item)
        if text == HOST_POSTURE_FULL_ACCESS:
            return True
        if text.startswith("sandbox_mode=") and HOST_POSTURE_FULL_ACCESS in text:
            return True
    return False


def _spawn(
    *,
    provider: Any,
    model: str,
    prompt: str,
    profile: str,
    transport: str,
    timeout: float,
    cwd: Optional[str],
    schema: Optional[Any] = None,
    anchor: Optional[str] = None,
    sandbox_fallback: Optional[str] = None,
    read_dirs: Sequence[str] = (),
    jail_request: Optional[JailRequest] = None,
    write_consent: Optional[WritePostureConsent] = None,
) -> _Capture:
    """Run one dispatch, materializing ``schema`` for the CLIs that take a file.

    §4.2.1 puts codex's sidecar in the **caller** — adapters are module-level
    singletons in ``_PROVIDERS`` shared across a concurrent fan-out and cannot
    hold per-run state — and requires the directory to be removed in a
    ``finally`` covering timeout, kill-path teardown and exception alike. That is
    precisely this scope: the ``with`` below opens *before* :func:`_spawn_child`
    renders any argv (codex refuses a schema whose file is unreadable before
    returning argv at all, so nothing partial can reach the CLI) and closes only
    after the child has been spawned, communicated with, and — on a timeout —
    killed with its process group and drained.

    **One sidecar per attempt, not per dispatch.** This lane's retry loop lives
    inside :func:`dispatch_task`, which returns from four points and breaks from
    three more; a dispatch-scoped directory would have to be unwound by
    re-indenting that whole region into a ``try/finally``. Per attempt gets the
    same guarantee from one ``with`` in the one function that spawns, it matches
    Lane A's *observable* lifetime (its ladder re-enters
    ``invoke_with_provider``, which opens and closes a sidecar per call), and it
    re-materializes a file that vanished between two attempts instead of failing
    the retry on it. The cost is one ``mkdtemp`` plus one small write per
    attempt, and only on the adapter whose transport is a file (codex);
    claude's schema is inline and never touches the disk at all.

    ``schema=None`` — every kind with no schema phase, and every adapter that
    declined the flag — skips all of it and renders the argv it always did.

    **The jailed attempt's scratch directory** (plan codex-sandbox-unavailable
    §6 F1 "How a dispatch receives its grant", 2026-09-30). When
    ``sandbox_fallback`` names a wrapping rung, this ``with`` also owns the
    attempt's ``TMPDIR`` (``landlock_dispatch.slot_tmpdir``), beside the schema
    sidecar and for the same reason: made before any rule is applied, removed
    after the child exits — on a clean exit, a timeout's group kill,
    ``KeyboardInterrupt`` and the teardown alike — and fresh on every retry,
    so no attempt inherits another's scratch files. A dispatch on the rung with
    no ``jail_request`` is refused here with nothing made and nothing spawned
    (never rendered with the base entries alone), and a directory that cannot
    be made is a launch error, never a model error.
    """
    wrap = _wrapping_rung(provider, profile, sandbox_fallback)
    common: Dict[str, Any] = {
        "provider": provider, "model": model, "prompt": prompt, "profile": profile,
        "transport": transport, "timeout": timeout, "cwd": cwd, "schema": schema,
        "anchor": anchor, "sandbox_fallback": sandbox_fallback,
        "read_dirs": read_dirs, "write_consent": write_consent,
    }
    if wrap is None:
        return _spawn_with_schema(jail=None, **common)
    if jail_request is None:
        refused = _Capture(sandbox_rung=wrap.name)
        refused.launch_error = (
            f"the plugin's Landlock jail ({wrap.name}) needs this dispatch's "
            f"grant and none was handed to the spawn; nothing was made or "
            f"spawned"
        )
        return refused
    with contextlib.ExitStack() as stack:
        try:
            tmpdir = stack.enter_context(
                landlock_dispatch.slot_tmpdir(jail_request.repo_root)
            )
        except (landlock_dispatch.JailRefused, OSError) as exc:
            refused = _Capture(sandbox_rung=wrap.name)
            refused.launch_error = (
                f"the plugin's Landlock jail could not make this attempt's "
                f"scratch directory: {getattr(exc, 'message', None) or exc}"
            )
            return refused
        return _spawn_with_schema(
            jail=_JailSpawn(rung=wrap, request=jail_request, tmpdir=tmpdir),
            **common,
        )


def _spawn_with_schema(*, jail: Optional[_JailSpawn], **common: Any) -> _Capture:
    """:func:`_spawn`'s sidecar leg: the schema file for a file-transport CLI,
    removed in the same ``with`` that spawned the child."""
    provider = common["provider"]
    schema = common.pop("schema", None)
    if schema is not None and getattr(
        provider, "structured_output_transport", "inline"
    ) == "file":
        with structured_output.schema_sidecar(schema) as materialized:
            return _spawn_child(schema=materialized, jail=jail, **common)
    return _spawn_child(schema=schema, jail=jail, **common)


def _spawn_child(
    *,
    provider: Any,
    model: str,
    prompt: str,
    profile: str,
    transport: str,
    timeout: float,
    cwd: Optional[str],
    schema: Optional[Any] = None,
    anchor: Optional[str] = None,
    sandbox_fallback: Optional[str] = None,
    read_dirs: Sequence[str] = (),
    jail: Optional[_JailSpawn] = None,
    write_consent: Optional[WritePostureConsent] = None,
) -> _Capture:
    """Run one dispatch: build argv for the profile, spawn, capture everything.

    ``cwd`` is passed explicitly (never inherited) so the runner's sandbox root is
    the intended repository and a task cannot be steered into ``$HOME`` or a
    sibling checkout (D3e). Env composition is the adapter's
    ``get_env``/``get_remove_env`` pair — the same single site the fan-out path and
    the detached child use, so there is never a second hand-rolled env filter.

    ``anchor`` is the dispatch's plan anchor, threaded from the batch exactly as
    Lane A threads it into ``resolve_env``/``build_child_env`` — it is what makes
    config discovery resolve against the **plan's** git root rather than the
    process CWD's. Dropping it here is not cosmetic: an ``env_allowlist``,
    ``git_env`` or hermetic setting written into a plan-anchored
    ``.multi-llm/providers.yaml`` would govern Lane A slots and silently skip Lane
    B dispatches whenever the two roots differ, which is the one divergence
    M3/M17 (A6) exist to close.

    ``schema`` is §4.2.2's optional keyword, already materialized by
    :func:`_spawn` when this adapter's transport is a file. An adapter that
    declares no ``structured_output_support`` ignores it and renders the same
    argv either way; one that cannot carry it raises before any argv exists.

    M4/§2.3: the adapter's run-scoped dispatch context wraps argv *and* env,
    because an adapter that contains its own config layering renders a flag and
    an env redirect that only mean anything together (opencode's ``--pure`` and
    its ``XDG_CONFIG_HOME``). The ``with`` is the ``finally`` half of that
    lifecycle — it is left on a clean return, on a per-slot timeout, on
    ``KeyboardInterrupt`` and on the §8 process-group teardown alike.
    """
    with provider_dispatch_context(
        provider, model, profile, anchor=anchor,
        runner_version=_preflight_version(provider),
    ) as dispatch:
        if dispatch.refusal:
            # Nothing has been spawned and nothing has been claimed. The refusal
            # rides the same `launch_error` channel a failed `Popen` uses, so it
            # lands on the ladder's spawn rung rather than inventing a state.
            refused = _Capture()
            refused.launch_error = dispatch.refusal
            return refused
        return _spawn_in_context(
            provider=provider, model=model, prompt=prompt, profile=profile,
            transport=transport, timeout=timeout, cwd=cwd, schema=schema,
            anchor=anchor, sandbox_fallback=sandbox_fallback,
            read_dirs=read_dirs, jail=jail, write_consent=write_consent,
        )


def _jail_installed_version(provider_name: str) -> str:
    """The version a ``[JAIL_DENIED]`` line names as installed: the
    preflight's read, else the sandbox probe's, else ``unknown`` — read from
    the caches, never a spawn."""
    return (
        _probe_state._VERSION_CACHE.get(provider_name)
        or _probe_state._PROBE_VERSION_CACHE.get(provider_name)
        or "unknown"
    )


def _home_check_line(spec: str, rung: SandboxRung, change: Any, others: int) -> str:
    """The warn-only ``[CODEX_HOME_CHECK]`` line of the executor lane: the
    changed files and, for ``config.toml``, the changed key names — never a
    value — and how many other codex children of this run were live."""
    return (
        f"{CODEX_HOME_CHECK_MARKER} {spec} on rung {rung.name!r}: $CODEX_HOME "
        f"changed during this dispatch: {change.describe()}; {others} other "
        f"codex child(ren) of this run were live in the window, so any of them "
        f"may have made it. Review the file(s): the plugin does not revert "
        f"them. Warn-only in the executor lane: this dispatch's verdict is "
        f"unchanged."
    )


def _spawn_in_context(
    *,
    provider: Any,
    model: str,
    prompt: str,
    profile: str,
    transport: str,
    timeout: float,
    cwd: Optional[str],
    schema: Optional[Any] = None,
    anchor: Optional[str] = None,
    sandbox_fallback: Optional[str] = None,
    read_dirs: Sequence[str] = (),
    jail: Optional[_JailSpawn] = None,
    write_consent: Optional[WritePostureConsent] = None,
) -> _Capture:
    """:func:`_spawn_child`'s body, inside the adapter's dispatch context.

    ``sandbox_fallback`` is the D6 override (2026-09-17): the rung id
    :func:`dispatch_task` read off the preflight's cache for this runner and
    profile (:func:`sandbox_rung`), or ``None``; the adapter's
    ``apply_sandbox_fallback`` is what turns that rung into argv, and every
    adapter without one ignores it.

    **On the plugin's Landlock jail** (``jail`` set; plan codex-sandbox-
    unavailable §6 F1 "How a dispatch receives its grant", 2026-09-30), in this
    order: render the codex argv with ``JailContext(request, tmpdir)`` (the
    ``--sandbox`` slot and ``-c developer_instructions=…``); resolve the
    executable; compose the child env as today; complete the context with the
    ``$CODEX_HOME`` that env names (a missing or in-repo home refuses here —
    reported as a jail failure naming the path, nothing spawned); add the
    wrapper prefix through ``landlock_dispatch.wrap_argv``, the only site that
    does; snapshot the home, spawn in a new process group (the wrapper
    ``exec``s codex, so the PID and the group are codex's own and a timeout's
    group kill reaches it and everything it started), and snapshot again.
    While the context is alive the parent reads the outcome: a codex-internal
    EACCES (``is_jail_failure``), the stream's denials (``jail_denied_edits``,
    on the full stdout) and the home comparison. Only paths, classes and
    counts travel back, on the capture.

    **Backstop** (plan steps 3 and 3b): an ``agent-write`` argv carrying
    ``danger-full-access`` that is neither wrapped nor backed by an F5 consent
    — or whose jail grant names a write scope outside
    :data:`WRITE_SCOPES_ON_RUNG`, or whose consent names one outside
    :data:`WRITE_SCOPES_BY_CONSENT` — raises :class:`SandboxBackstopViolation`
    before ``Popen``.
    """
    capture = _Capture()
    render: Dict[str, Any] = {}
    if jail is not None:
        render["jail_context"] = JailContext(request=jail.request, tmpdir=jail.tmpdir)
        capture.sandbox_rung = jail.rung.name
    if write_consent is not None:
        render["write_consent"] = write_consent
    argv, stdin_text = provider.build_agent_command_for_transport(
        prompt, model, profile, transport, schema=schema,
        sandbox_fallback=sandbox_fallback, **render,
    )
    if read_dirs:
        # The adapter's own read-scope flag (claude-code `--add-dir`), for the
        # directories of path-named context snapshots outside cwd only.
        argv = provider.widen_read_scope(list(argv), read_dirs)
    # The batch-shim flag is consumed pre-dispatch by `_prompt_over_budget`, which
    # resolves argv[0] the same way: it applies cmd.exe's 8,191-unit cap and
    # refuses a metacharacter-bearing prompt (rung 7, nothing spawned) before this
    # runs, so by here the prompt is already known to be safe for this launcher.
    launcher, _is_batch_shim = _resolve_executable(argv[0])
    argv = [*launcher, *argv[1:]]
    capture.argv = list(argv)

    # `resolve_env`, not `get_env`: the dispatch's own profile is what scopes the
    # §2.2 git block. `agent-readonly` gets the global non-interactive keys AND
    # `credential.helper=""` (a hanging helper fails in ~0.27 s instead of burning
    # the slot and orphaning a child); `agent-write` gets the global keys ONLY and
    # keeps whatever helper the user configured, because it is the profile that
    # legitimately reaches private remotes. Passing a constant here would erase
    # that distinction.
    # `cwd` is passed for the same reason it is passed to `Popen` below: this
    # dispatch runs in an explicit directory, and an adapter whose delta carries
    # a workspace-scoped side effect (cursor's trust-marker guard) must scope it
    # to *that* directory rather than to the orchestrator's.
    # M3/M17 (A6): the union of the adapter's list and the host's guards, minus
    # the host's `passthrough`, is computed inside `build_child_env` — the one
    # builder Lane A goes through too. Before it existed the two lanes composed
    # the child env differently, which is what let `passthrough` cancel §2.1's
    # credential strip on this lane alone. The host entry still declares what
    # *this* host injects into every child; what it may no longer do is sanction
    # a vendor credential back into a runner the adapter just stripped it from.
    # Both calls live in `dispatch_child_env` (plan §8 T8.13), which the auth
    # preflight shares, so the probe and the dispatch cannot compose it apart.
    env = dispatch_child_env(provider, model, profile, anchor=anchor, cwd=cwd)

    spec = f"{getattr(provider, 'name', 'runner')}:{model}"
    context: Optional[JailContext] = None
    if jail is not None:
        composed = dict(os.environ) if env is None else dict(env)
        try:
            context = landlock_dispatch.complete_context(jail.request, jail.tmpdir, composed)
            argv, env = landlock_dispatch.wrap_argv(argv, jail.rung, context, composed)
        except landlock_dispatch.JailRefused as exc:
            # Between the probe and this dispatch a required entry vanished (or
            # the home is unusable): a jail failure naming the path, never a
            # model error, never retried on another rung, nothing spawned.
            capture.launch_error = exc.message
            capture.jail_evidence = {
                "where": "setup",
                "line": landlock_dispatch.redacted_excerpt(exc.message),
                "path": landlock_dispatch.redacted_excerpt(exc.path) or None,
                "class": landlock_dispatch.JAIL_CLASS_JAIL, "reason": exc.reason,
            }
            capture.jail_denied_line = landlock_dispatch.jail_denied_text(
                spec=spec, rung=jail.rung,
                evidence={"path": exc.path, "line": exc.message},
                allow_list="", installed=_jail_installed_version(spec.split(":", 1)[0]),
                profile=profile, write_scope=jail.request.write_scope,
                lane=INCIDENTAL_LANE_EXECUTOR,
            )
            return capture
        capture.argv = list(argv)
    if profile == PROFILE_AGENT_WRITE and _carries_full_access(argv):
        wrapped = landlock_dispatch.is_wrapped(argv)
        if not wrapped and write_consent is None:
            raise SandboxBackstopViolation(
                f"Refusing to spawn {spec}: an agent-write argv carries "
                f"{HOST_POSTURE_FULL_ACCESS} without the plugin's Landlock wrapper "
                f"prefix or the chat's F5 consent. A write profile never runs "
                f"uncontained unwrapped. Nothing was spawned."
            )
        # The grant's scope, not only its presence: the jail serves the
        # scopes in WRITE_SCOPES_ON_RUNG and F5 the narrower
        # WRITE_SCOPES_BY_CONSENT, so an unscoped write — or a repo-wide one
        # by consent — is refused here even if a gate upstream let it through.
        if wrapped:
            grant = "the plugin's Landlock jail"
            scope = getattr(getattr(jail, "request", None), "write_scope", None)
            served = WRITE_SCOPES_ON_RUNG
        else:
            grant = "the chat's F5 consent"
            scope = getattr(write_consent, "write_scope", None)
            served = WRITE_SCOPES_BY_CONSENT
        if scope not in served:
            raise SandboxBackstopViolation(
                f"Refusing to spawn {spec}: an agent-write argv carries "
                f"{HOST_POSTURE_FULL_ACCESS} under {grant} for write scope "
                f"{scope!r}, which it does not serve (served: "
                f"{', '.join(served)}; repo-wide edits run on the jail "
                f"alone). Nothing was spawned."
            )

    home_before = None
    run_cwds = [os.path.realpath(cwd or os.getcwd())]
    if context is not None:
        home_before = landlock_dispatch.home_snapshot(context.codex_home, run_cwds)

    start = time.time()
    # `Popen`, not `subprocess.run`: the timeout has to kill the child *with its
    # process group* (D3k rung 2), and `run` neither hands out the pid nor kills
    # anything but the direct child. An agentic runner is not a leaf — its tool
    # children (a shell, a nested provider CLI) inherit both the group and this
    # stdout pipe — so `run`'s leader-only kill leaves them running against a
    # task nobody is reading, and its own post-kill drain is unbounded on
    # Windows: a timed-out task wedges the whole batch instead of failing on
    # rung 2. On the jail the leader is the wrapper, which `exec`s codex: the
    # PID and the group recorded here are codex's own. Windows has no groups:
    # there the child starts in a Job Object of its own, and the job is what
    # the timeout kills (`process_control.popen_tree`).
    try:
        proc, job = process_control.popen_tree(
            argv,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE if stdin_text is not None else subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            cwd=cwd,
            **process_control.new_process_group_kwargs(),
        )
    except OSError as exc:
        capture.duration = time.time() - start
        capture.launch_error = str(exc)
        return capture

    if context is not None:
        with _probe_state._JAIL_SUMMARY_LOCK:
            live_before = _probe_state._JAILED_CHILDREN["live"]
            started_before = _probe_state._JAILED_CHILDREN["started"]
            _probe_state._JAILED_CHILDREN["live"] += 1
            _probe_state._JAILED_CHILDREN["started"] += 1
    streams: Optional[process_capture.PipeCapture] = None
    try:
        # Read the group now, while the child is alive: `os.getpgid` stops
        # answering the moment the leader is reaped, and the group — the thing
        # that still holds the tool children — outlives it. `None` on Windows,
        # where the job stands in for it.
        pgid = process_control.process_group_id(proc.pid)
        try:
            # Bounded, and the wait ends with the runner, not with the last
            # process holding its pipes (`process_capture`).
            # The adapter's stdout watch, if it declares one, ends the wait
            # early; the stop below is the timeout's own
            # (docs/development/providers.md#a-cli-that-loops).
            # A pipe still held once the runner exited is what the runner left
            # running: its group is stopped as at a timeout before this
            # dispatch returns, so the write lane's checks after it see every
            # write it made (docs/development/runtime.md#process-primitives).
            streams = process_capture.PipeCapture(
                proc, max_bytes=_task_result.MAX_STREAM_BYTES, grace_s=TIMEOUT_DRAIN_S,
                watch=process_capture.provider_watch(provider),
                on_held=lambda _held: _stop_held_group(proc, pgid, job),
            )
            stdout, stderr = streams.communicate(input=stdin_text, timeout=timeout)
            capture.duration = time.time() - start
            capture.stdout = _decode(stdout)
            capture.stderr = _decode(stderr)
            capture.exit_code = proc.returncode
            capture.capped_streams = streams.capped
            if streams.held_stopped:
                _record_held_pipe(capture, proc, pgid, streams)
        except subprocess.TimeoutExpired as exc:
            capture.kill_verdict = _kill_timed_out(proc, pgid, job)
            capture.kill_pid = proc.pid
            stdout, stderr = _drain_after_kill(streams, exc)
            capture.duration = time.time() - start
            capture.timed_out = True
            capture.stdout = stdout
            capture.stderr = stderr
            capture.capped_streams = streams.capped
            capture.stream_stop = streams.stream_stop
        except OSError as exc:
            _kill_timed_out(proc, pgid, job)
            _drain_after_kill(streams or proc, None)
            capture.duration = time.time() - start
            capture.launch_error = str(exc)
            return capture
        except BaseException:
            # The foreground SIGTERM handler's `SystemExit` (or a Ctrl-C) landing
            # in the wait: the child runs in a group of its own, so nothing else
            # reaches it. Stop and reap the group *before* unwinding — the
            # callers' cleanup removes the jail's TMPDIR and restores the trust
            # state, which a still-running codex could otherwise write the plan
            # into or rewrite behind it. Then re-raise, so the signal still ends
            # the run; a teardown failure never masks it.
            _kill_timed_out(proc, pgid, job)
            try:
                _drain_after_kill(streams or proc, None)
            except Exception:  # noqa: BLE001 - the interrupt is what propagates
                pass
            raise
    finally:
        if streams is not None:
            streams.close()
        if job is not None:
            job.close()
        if context is not None:
            with _probe_state._JAIL_SUMMARY_LOCK:
                _probe_state._JAILED_CHILDREN["live"] -= 1
                others = live_before + (
                    _probe_state._JAILED_CHILDREN["started"] - started_before - 1
                )
    if context is not None and jail is not None:
        _read_jailed_outcome(
            capture, jail=jail, context=context, spec=spec, cwd=cwd,
            home_before=home_before, run_cwds=run_cwds, others=others,
            profile=profile,
        )
    return capture


def _read_jailed_outcome(
    capture: _Capture,
    *,
    jail: _JailSpawn,
    context: JailContext,
    spec: str,
    cwd: Optional[str],
    home_before: Any,
    run_cwds: Sequence[str],
    others: int,
    profile: Optional[str] = None,
) -> None:
    """After a jailed child exits, while its context is alive: the jail
    failure, the stream's denials and the home check (plan F1 item 6,
    Limits). Only paths, classes and counts are kept on ``capture``.

    The exit code goes in too: the wrapper's own refusal at dispatch (exit
    125/126 with its ``landlock_exec:`` note — a required entry gone or a
    symlink since the probe, or Landlock failing after a good ABI query) is
    a jail failure, and the ``[JAIL_DENIED]`` line it sets rejects the
    attempt before any output is parsed — never retried, as on the fan-out
    lane."""
    evidence = landlock_dispatch.is_jail_failure(
        capture.stderr, capture.stdout, context, returncode=capture.exit_code,
    )
    if evidence is not None:
        capture.jail_evidence = evidence.to_dict()
        failed_turn = evidence.where == "event" or capture.exit_code not in (0, None)
        if (
            failed_turn
            and not capture.timed_out
            and evidence.klass in (
                landlock_dispatch.JAIL_CLASS_JAIL, landlock_dispatch.JAIL_CLASS_PROBABLE,
            )
        ):
            try:
                allow = landlock_dispatch.render_allow_list(
                    landlock_dispatch.allow_entries(context)
                )
            except landlock_dispatch.JailRefused:
                allow = ""
            capture.jail_denied_line = landlock_dispatch.jail_denied_text(
                spec=spec, rung=jail.rung, evidence=capture.jail_evidence,
                allow_list=allow, installed=_jail_installed_version(spec.split(":", 1)[0]),
                profile=profile, write_scope=jail.request.write_scope,
                lane=INCIDENTAL_LANE_EXECUTOR,
            )
    capture.jail_denials = landlock_dispatch.jail_denied_edits(
        capture.stdout, context, cwd=cwd,
    )
    home_after = landlock_dispatch.home_snapshot(context.codex_home, run_cwds)
    change = landlock_dispatch.compare_home(home_before, home_after)
    if change is not None:
        if change.any:
            capture.home_change = change.to_dict()
            _probe_state._record_jail_line(_home_check_line(spec, jail.rung, change, others))
        if change.foreign_trust:
            # Trust tables for directories other than this run's cwds (I12):
            # this run's batch or a concurrent codex session added them. Named
            # in the closing summary only, never a warning per dispatch, and
            # only those still in the config when it prints (fix round 17).
            _probe_state._record_jail_line(
                landlock_dispatch.TrustEntriesNote(
                    home=context.codex_home,
                    paths=tuple(change.foreign_trust),
                ),
                echo=False,
            )


def _kill_timed_out(
    proc: Any, pgid: Optional[int], job: Optional["process_control.TreeJob"] = None,
    *, what: str = "the timed-out runner",
) -> Optional[str]:
    """SIGTERM → SIGKILL the child *and its group*, through the one facade.
    Returns ``kill_tree``'s verdict; ``None`` when the kill raised (the child
    was then sent a kill through its job or its ``Popen``, unconfirmed).

    This pid is not a record read off disk: it is a child this process is
    still holding open, unreaped until :func:`_drain_after_kill` collects it,
    so no other process can take its pid. *proc* goes along as ``child``: it
    anchors its pid and group through the kill where the owned kill runs
    (Linux, wherever this process's children are known to become zombies; see
    ``kill_tree``), which counts its zombie as exited. Where the kill goes by
    identity and that is not known, the child is not signalled
    (``unresolved``). Elsewhere ``start_time=None`` requests the kill by
    number's unverified kill, and a ``survived`` that is only the child's own
    zombie is confirmed by its exit (``process_control.own_child_stopped``).

    Only ``killed`` and ``gone`` confirm the runner stopped. Any other outcome
    (``process_control.unconfirmed_kill``) gets a warning naming the pid, and a detached
    run's record keeps it for a later abort or sweep
    (``detach.note_left_running``). *job* is the child's Windows Job Object,
    the group's stand-in there (``None`` elsewhere). *what* names the runner
    in that warning.
    """
    try:
        verdict: Optional[str] = process_control.kill_tree(
            proc.pid,
            start_time=None,
            pgid=pgid,
            escalate_after_s=TIMEOUT_KILL_GRACE_S,
            poll_interval_s=0.05,
            job=job,
            child=proc,
        )
        if verdict == "survived" and process_control.own_child_stopped(proc, pgid):
            verdict = "killed"
    except Exception:  # noqa: BLE001 - teardown must never mask the timeout
        verdict = None
        if job is None or not job.terminate():
            try:
                proc.kill()
            except OSError:
                pass
    _note_runner_stop(proc, pgid, verdict, what)
    return verdict


def _note_runner_stop(proc: Any, pgid: Optional[int], verdict: Optional[str],
                      what: str) -> None:
    """What every stop of a runner's tree records: whether it was confirmed,
    for the private home lent to the runner (which outlives a stop that is
    not), and for one that is not a ``WARNING`` naming the pid and group and,
    in a detached worker, ``run.cleanup`` ``incomplete``
    (``detach.note_left_running``). *what* names the runner in the warning."""
    reason = process_control.unconfirmed_kill(verdict)
    process_control.note_stop(proc, reason is None)
    if reason is None:
        return
    print(
        f"WARNING: {what} pid {proc.pid} (process group "
        f"{pgid if pgid is not None else '?'}) could not be confirmed stopped "
        f"(kill verdict {verdict}): {reason}, so it may still be running. "
        "Check it by hand; a detached run keeps it in its record for "
        "status --abort.",
        file=sys.stderr,
    )
    detach = sys.modules.get(f"{__package__}.detach") if __package__ else None
    if detach is not None:
        detach.note_left_running(proc.pid, pgid, verdict)


#: How a pipe holder's stop names the runner in its warning.
_HELD_WHAT = "what was left holding the output of the exited runner"


def _stop_held_group(
    proc: Any, pgid: Optional[int], job: Optional["process_control.TreeJob"] = None,
) -> Optional[str]:
    """Stop the group of a runner that exited on its own while something it
    started still held its output (``process_capture.PipeCapture``'s
    ``on_held``), exactly as its timeout does, before the dispatch returns to
    the write lane's checks; the kill's verdict.

    The runner is still unreaped here wherever its exit could be watched
    without reaping it (POSIX with ``waitid``): its zombie reserves its pid,
    and with it the number of the group it leads, so this is the timeout's
    own kill (:func:`_kill_timed_out`) on the same anchor. On Windows the
    runner's Job Object is the tree, and terminating it needs no pid.
    Anywhere else the runner has been reaped already: its group's number may
    name another group by now, so nothing is signalled, and the verdict is
    ``unresolved``.
    """
    if process_control.IS_WINDOWS:  # pragma: no cover - Windows
        verdict: Optional[str] = (
            "killed" if job is not None and job.terminate() else "unresolved")
    elif getattr(proc, "returncode", None) is not None:
        verdict = "unresolved"
    else:
        return _kill_timed_out(proc, pgid, job, what=_HELD_WHAT)
    _note_runner_stop(proc, pgid, verdict, _HELD_WHAT)
    return verdict


def _record_held_pipe(capture: _Capture, proc: Any, pgid: Optional[int],
                      streams: "process_capture.PipeCapture") -> None:
    """What the dispatch becomes once :func:`_stop_held_group` ran.

    The group stopped and the pipes let go: the dispatch goes on with the
    runner's own answer and exit code, and ``pipe_held`` words it for the
    batch report. Otherwise (a pipe still held after the stop, so a process
    outside the run's group holds it; or a stop that could not be confirmed)
    the dispatch ends as the timeout it was at the base, when that process
    held the pipe until the deadline: ``timed_out``, the kill's verdict, and
    the words that say what holds the output and how to look for it
    (``held_pipe_note``). The timeout's own handling follows, its retry and
    its partial application of a batch that moved bytes included."""
    verdict = streams.held_stop if isinstance(streams.held_stop, str) else None
    if streams.still_held and process_control.unconfirmed_kill(verdict) is None:
        # The group is gone, yet its output is still held: by a process
        # outside it, which may still run.
        verdict = "unresolved"
        _note_runner_stop(proc, pgid, verdict, _HELD_WHAT)
    capture.pipe_held = True
    capture.pipe_held_verdict = verdict
    if process_control.unconfirmed_kill(verdict) is None:
        return
    held = " and ".join(sorted(streams.still_held))
    group = pgid if pgid else proc.pid
    capture.held_pipe_note = (
        f"the runner exited (code {capture.exit_code}) while a process it started "
        f"held its output, so its process group was stopped as at a timeout"
        + (f", but its {held} was still held after that: a process outside the run's "
           f"process group holds it and may still be running"
           if held else f", which could not be confirmed (kill verdict {verdict})")
        + f"; the dispatch was ended as a timeout. Look for it with: pgrep -l -s "
        f"{group} (one still in the runner's session), or ps -eo "
        f"pid,ppid,pgid,sid,lstart,args (one in a session of its own has init or the "
        f"user's service manager as its parent and started during this run)"
    )
    capture.timed_out = True
    capture.exit_code = None
    capture.kill_verdict = verdict
    capture.kill_pid = proc.pid


def pipe_held_note(capture: Any) -> Optional[str]:
    """The batch report's words for a runner that exited while a process it
    started still held its output, whose group was then stopped and the
    output let go (``_Capture.pipe_held``, the dispatch not ended as a
    timeout), or ``None``."""
    if not getattr(capture, "pipe_held", False) or getattr(capture, "timed_out", False):
        return None
    return ("the runner exited while a process it started still held its output; "
            "its process group was stopped before the task's checks (kill verdict "
            f"{getattr(capture, 'pipe_held_verdict', None)})")


def _drain_after_kill(
    proc: Any, exc: Optional[subprocess.TimeoutExpired]
) -> Tuple[str, str]:
    """Collect the killed child's output and reap it, without ever hanging.

    *proc* is the child's :class:`process_capture.PipeCapture` (or the child
    itself when the capture never started). A second ``communicate()`` returns
    everything captured, including what was read before the first one timed
    out. If even *that* blocks, the child itself outlived the kill: fall back
    to the partial capture the ``TimeoutExpired`` carries and let the
    descriptors go, because a diagnostic tail is never worth wedging the batch
    for.
    """
    try:
        stdout, stderr = proc.communicate(timeout=TIMEOUT_DRAIN_S)
        return _decode(stdout), _decode(stderr)
    except (subprocess.TimeoutExpired, OSError, ValueError):
        if process_control.IS_WINDOWS:
            # communicate's reader threads can still hold the streams' locks.
            # close() waits for those reads, defeating TIMEOUT_DRAIN_S even
            # after the tree kill was attempted. Let the readers release the
            # pipes when the remaining writer exits, as the probe does. With
            # the child's Job Object terminated no writer is left; only a
            # child that got no job (`popen_tree`) can still have one.
            return (
                _decode(getattr(exc, "stdout", None)),
                _decode(getattr(exc, "stderr", None)),
            )
        for stream in (proc.stdin, proc.stdout, proc.stderr):
            try:
                if stream is not None:
                    stream.close()
            except (OSError, ValueError):  # pragma: no cover - best effort
                pass
        return (
            _decode(getattr(exc, "stdout", None)),
            _decode(getattr(exc, "stderr", None)),
        )


def _decode(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return value.decode("utf-8", errors="replace")


def _context_read_dirs(task: Dict[str, Any], cwd: Optional[str]) -> List[str]:
    """Directories of a task's ``mode: path`` context snapshots outside ``cwd``."""
    root = os.path.realpath(cwd or os.getcwd())
    dirs: List[str] = []
    for record in task.get("context_sources") or []:
        if not isinstance(record, dict) or record.get("mode") != "path":
            continue
        path = record.get("abs_path")
        if not path:
            continue
        directory = os.path.dirname(os.path.realpath(str(path)))
        if directory == root or directory.startswith(root.rstrip(os.sep) + os.sep):
            continue
        if directory not in dirs:
            dirs.append(directory)
    return dirs


def _missing_write_grant(
    request: Optional[JailRequest], *, kind: str, scope: str
) -> Optional[str]:
    """Why ``request`` is not a complete grant for a ``kind`` write dispatch on
    the plugin's jail, or ``None`` (plan F1 "A missing grant is refused, never
    narrowed or widened")."""
    if request is None:
        return "no grant was handed to the dispatch"
    if request.kind != kind:
        return f"its grant names kind {request.kind!r}, not the task's {kind!r}"
    if request.write_scope != scope:
        return (
            f"its grant's write scope is {request.write_scope!r}, not "
            f"{scope!r} (the scope of kind {kind!r})"
        )
    if scope == WRITE_SCOPE_REPO_WIDE:
        # The grant is one dir rule on the repository root (step 3b, revised
        # 2026-10-05): no single target, but the root and the run's output
        # folder, which the developer message names as hands-off.
        if not request.repo_root:
            return "its repo-wide grant names no repository root"
        if not request.output_dir:
            return "its repo-wide grant names no output folder for the developer message"
        return None
    if not request.target:
        return f"its {scope} grant names no target"
    return None


def _dispatch_grant(
    task: Dict[str, Any],
    *,
    kind: str,
    profile: str,
    runner: str,
    cwd: Optional[str],
    provider: Any,
    jail_request: Optional[JailRequest],
) -> Tuple[Optional[str], Optional[JailRequest], Optional[str]]:
    """``(refusal, request, rung id)`` for one dispatch (plan
    codex-sandbox-unavailable §6 F1 "How a dispatch receives its grant",
    2026-09-30).

    The rung is the preflight's decision, replayed: for a write kind, the one
    taken for the kind's own write scope (:data:`WRITE_SCOPE_BY_KIND`, never
    the task JSON). A read kind gets a request built from ``cwd`` when it has
    none, and is refused if handed one that carries a scope or a target. A
    write kind on the jail is refused unless its request is complete for the
    task. An unmapped write kind is refused outright. Every refusal is rung 7
    with nothing spawned.
    """
    task_id = str(task.get("task_id", ""))
    if kind in WRITE_KINDS:
        scope = _runner_selection.WRITE_SCOPE_BY_KIND.get(kind)
        if scope is None:
            return (
                f"Task {task_id}: write kind {kind!r} has no write scope "
                f"(WRITE_SCOPE_BY_KIND), so it is refused rather than given a "
                f"wider grant. Nothing was dispatched."
            ), jail_request, None
        fallback = _probe_state.sandbox_rung(runner, profile, write_scope=scope)
        wrap = _wrapping_rung(provider, profile, fallback)
        if wrap is not None:
            missing = _missing_write_grant(jail_request, kind=kind, scope=scope)
            if missing is not None:
                return (
                    f"Task {task_id}: the plugin's Landlock jail ({wrap.name}) "
                    f"needs this write dispatch's grant, and {missing}; a "
                    f"missing grant is refused, never narrowed or widened. "
                    f"Nothing was dispatched."
                ), jail_request, fallback
        return None, jail_request, fallback
    if jail_request is not None and (
        jail_request.write_scope or jail_request.target or jail_request.target_dir
    ):
        return (
            f"Task {task_id}: this read-only {kind} dispatch was handed a write "
            f"grant (scope {jail_request.write_scope!r}); a read kind never "
            f"carries one. Nothing was dispatched."
        ), jail_request, None
    if jail_request is None:
        jail_request = JailRequest(
            repo_root=os.path.realpath(cwd or os.getcwd()), kind=kind,
        )
    return None, jail_request, _probe_state.sandbox_rung(runner, profile)


def _jail_hook_context(
    capture: Any, request: Optional[JailRequest], fallback: Optional[str],
) -> Dict[str, Any]:
    """The keys ``after_result`` and ``changed_files`` gain (plan step 3):
    the rung the attempt ran on, the stream's denials for a write dispatch on
    the jail (``landlock_dispatch.JailDenials``; ``None`` otherwise), and the
    jail evidence (a dict, or ``None``). Paths, kinds and counts only."""
    denials = getattr(capture, "jail_denials", None)
    on_jail = getattr(capture, "sandbox_rung", None) is not None
    return {
        "sandbox_rung": fallback,
        "jail_denials": (
            denials if on_jail and request is not None and request.write_scope
            else None
        ),
        "jail_evidence": getattr(capture, "jail_evidence", None),
    }


def _report_jail_outcome(task_id: str, capture: Any) -> None:
    """Print what the parent read off a jailed attempt (plan F1 item 6): the
    ``[JAIL_DENIED]`` line (kept for the closing summary), and — on every
    dispatch on the rung — the count and first three paths of the command
    writes the jail stopped, which fail nothing."""
    line = getattr(capture, "jail_denied_line", None)
    if line:
        _probe_state._record_jail_line(line)
    said = landlock_dispatch.jail_denials_text(
        landlock_dispatch.as_jail_denials(getattr(capture, "jail_denials", None)),
        lane=INCIDENTAL_LANE_EXECUTOR,
    )
    if said:
        print(f"[exec-subagents] {task_id}: {said}")
