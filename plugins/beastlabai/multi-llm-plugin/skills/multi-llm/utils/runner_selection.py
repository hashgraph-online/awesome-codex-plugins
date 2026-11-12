"""Which runner a task dispatches to, and the words a refused runner gets.

:func:`profile_for_kind` (the profile is derived from the task kind, never
requested by a prompt), :func:`resolve_task_runner` and its source, the
runners the operator's roster allows (:func:`eligible_runners`), and the
refusal text a preflight leg raises (:data:`_REASON_EXPLANATION`,
:func:`_render_runner_rejection`).

``utils.subagent_executor`` re-exports every name defined here for reading
only: patch one here, never through the executor
(docs/development/delegation.md#where-the-executors-helpers-live).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from . import provider_registry as _provider_registry
from .provider_registry import (
    session_runner,
    get_provider,
    parse_model_spec,
    require_one_config_source,
    resolve_subagent_runner,
)
from .providers.base import (
    PROFILE_AGENT_READONLY,
    PROFILE_AGENT_WRITE,
    split_reasoning_effort,
    WRITE_SCOPE_PLAN_FILE,
    WRITE_SCOPE_REPO_WIDE,
    WRITE_SCOPE_TASKS,
)
from .subagent_tasks import (
    READ_KINDS,
    WRITE_KINDS,
)
from . import task_outcome as _task_outcome


#: Every read/analyze kind runs read-only; every write kind runs ``agent-write``.
#: Derived from the kind by the executor (D3e), never read from the task JSON —
#: which is the whole point: a materialized prompt embeds untrusted plan/diff text
#: and must not be able to request escalation.
PROFILE_BY_KIND = {
    **{kind: PROFILE_AGENT_READONLY for kind in READ_KINDS},
    **{kind: PROFILE_AGENT_WRITE for kind in WRITE_KINDS},
}

#: Every write kind maps to ``agent-write`` above, so the profile cannot tell a
#: plan edit from a code edit. The grant the plugin's Landlock jail gives a
#: write dispatch is therefore keyed by the KIND here, beside the profile map
#: and derived the same way — never read from the task JSON (plan
#: codex-sandbox-unavailable §6 F1 "How a dispatch receives its grant",
#: 2026-09-30). ``plan-file`` is one file rule on the plan, ``tasks`` the tasks
#: directory (or file); ``repo-wide`` (step 3b, 2026-10-02; one dir rule on
#: the repository root since 2026-10-05) the whole repository. A write kind
#: missing from this map is refused, never widened.
WRITE_SCOPE_BY_KIND = {
    "apply_suggestions": WRITE_SCOPE_PLAN_FILE,
    "apply_task_suggestions": WRITE_SCOPE_TASKS,
    "apply_code_fixes": WRITE_SCOPE_REPO_WIDE,
    "implement": WRITE_SCOPE_REPO_WIDE,
}


# ---------------------------------------------------------------------------
# Profiles, runners, ceilings
# ---------------------------------------------------------------------------

def profile_for_kind(kind: str) -> str:
    """The D3e invocation profile for a task kind.

    Derived here and nowhere else: the profile must never come from the task JSON,
    which embeds untrusted plan/diff/review text and could otherwise request
    escalation to ``agent-write``.
    """
    try:
        return PROFILE_BY_KIND[kind]
    except KeyError:
        raise _task_outcome.ExecutorError(
            f"Unknown task kind {kind!r}: the executor dispatches only "
            f"{', '.join(sorted(PROFILE_BY_KIND))}. Nothing was dispatched."
        ) from None


def eligible_runners(profile: str) -> List[str]:
    """Runner specs on this host that could serve ``profile``.

    The intersection of the adapters declaring the profile with the binaries
    actually present on PATH. Printed as advice by every rejection; an empty
    intersection gets its own sentence rather than an empty list.
    """
    names = []
    for name, provider in _provider_registry._PROVIDERS.items():
        if not provider.supports_profile(profile):
            continue
        try:
            if provider.is_available():
                names.append(name)
        except Exception:  # noqa: BLE001 - a probe must never break a refusal
            continue
    return sorted(names)


_REASON_EXPLANATION = {
    "unknown_provider": (
        "the provider name has no built-in adapter, so nothing can run it — "
        "this is a stale-config condition"
    ),
    "missing_capability": (
        "the adapter exists and runs fine, but does not declare the capability "
        "this phase needs — this is a capability condition, not a stale config"
    ),
    "missing_profile": (
        "the adapter exists and runs fine, but implements no invocation for this "
        "profile, and a fabricated one would hand an untrusted prompt write access"
    ),
    "binary_absent": (
        "the adapter is implemented but its CLI is not on PATH"
    ),
    "unresolvable_model": (
        "the model token cannot be expressed in this CLI's own addressing "
        "scheme, so no catalog, no release and no server could resolve it — a "
        "structural refusal, never a catalog lookup"
    ),
    "not_authenticated": (
        "the CLI is installed but not logged in — installed is not authenticated, "
        "and no retry can fix a missing credential"
    ),
    "nested_exec_denied": (
        "this host's capability data declares that a third-party agent CLI cannot "
        "be run from inside it at all — the executor refuses the run naming the "
        "field rather than dispatching into a sandbox that eats the failure"
    ),
    "nested_exec_spawn": (
        "the host's sandbox denied the spawn: the throwaway preflight dispatch "
        "could not start the runner as a child of this host's own shell"
    ),
    "runner_invalid_model": (
        "the runner rejected the model id itself during the preflight probe — "
        "a rejected id is a property of the spec, so every task in the batch "
        "would fail identically and the fix is a config edit, never a retry"
    ),
    "invalid_model_catalog": (
        "the CLI's own model listing, read in this dispatch's configuration, "
        "does not contain this model id — the id is a property of the spec, so "
        "every task in the batch would fail identically and the fix is a config "
        "edit, never a retry"
    ),
    "nested_exec_network": (
        "the runner started inside this host but could not reach its provider "
        "API — the host's egress rules, not the runner, are what failed"
    ),
    "nested_exec_credentials": (
        "the runner started inside this host but could not read its own "
        "credential store — a login notice from inside a sandbox is a host "
        "condition as often as a logged-out CLI, and neither is retryable"
    ),
    "sandbox_unavailable": (
        "the runner's own sandbox cannot start under this repo; on Ubuntu 24.04 "
        "this is the AppArmor user-namespace restriction, see "
        "`multi_llm.py doctor`"
    ),
}


def _availability_detail(spec: str) -> str:
    """The typed availability sentence for ``spec``'s adapter, or ``""`` (M10, §5.1).

    Reads the adapter's declared data only — no probe is run and no child is
    spawned — so it is safe on a refusal path that has already decided nothing
    will be dispatched. Any failure to resolve the adapter is silence, because a
    diagnostic may never be the reason a refusal cannot be printed.
    """
    try:
        provider_name, _, model = str(spec or "").partition(":")
        provider = get_provider(provider_name.strip())
        if provider is None:
            return ""
        return provider.describe_availability(
            credentials_required=_model_needs_credentials(provider, model.strip())
        ).detail
    except Exception:  # noqa: BLE001 - a diagnostic may never break a refusal
        return ""


def _model_needs_credentials(provider: Any, model: str) -> bool:
    """``provider.model_needs_credentials(model)``, defaulting to ``True``.

    The base adapter declares the hook; a narrow test double may not, and a
    missing declaration must read as "needs one" — the exemption is narrow or
    it is a hole (D3 step 2).
    """
    hook = getattr(provider, "model_needs_credentials", None)
    if not callable(hook):
        return True
    try:
        return bool(hook(model))
    except Exception:  # noqa: BLE001 - a declaration read may not break a preflight
        return True


def _render_runner_rejection(
    *, key: str, spec: str, reason_code: str, profile: str, detail: str = ""
) -> _task_outcome.RunnerRejected:
    """The single rejection formatter (D3). Exit 3."""
    if reason_code == "binary_absent" and not detail:
        # M10 (§5.1). The refusal itself stays a **bool** decision — the caller
        # gated on `is_available()` and this formatter does not second-guess it.
        # What gains the typed state is the *text*, here, in the one place every
        # rejection is rendered, so a `binary_absent` message finally names which
        # binary and why instead of leaving the reader with a reason code.
        detail = _availability_detail(spec)
    candidates = eligible_runners(profile)
    if candidates:
        advice = (
            f"Runners on this host that can serve {profile!r}: "
            f"{', '.join(candidates)}."
        )
    else:
        advice = (
            f"No runner on this host can serve {profile!r} — install one of the "
            f"supported CLIs (claude, codex, opencode) and authenticate it."
        )
    explanation = _REASON_EXPLANATION.get(reason_code, reason_code)
    message = (
        f"Refusing to dispatch: {key} is {spec!r} (reason: {reason_code}) — "
        f"{explanation}. {detail} {advice} "
        f"Fix: run --init to refresh a stale provider name, install the missing "
        f"CLI, or set {key} to one of the runners named above."
    ).replace("  ", " ")
    return _task_outcome.RunnerRejected(message, key=key, spec=spec, reason_code=reason_code)


def resolve_task_runner(
    task: Dict[str, Any],
    *,
    anchor: Optional[str] = None,
    recorded: Optional[Dict[str, str]] = None,
    snapshot: Any = None,
) -> str:
    """Resolve one task's runner spec, once, at batch start (D2e/D3o).

    Chain: a recorded runner from a previous attempt (so ``--resume`` and
    ``--retry-failed-subagents`` re-dispatch the runner the first attempt used,
    not one a since-edited config would pick) → the task's own ``model_hint`` when
    it is a concrete ``provider:model`` and not ``auto`` → ``capability_tier``
    (``cheap`` → ``driver.subagent_runner_cheap``) → ``driver.subagent_runner``.
    ``snapshot`` (``provider_registry.load_config_snapshot``) is the config load
    the ``driver`` keys are read from, so resolving many tasks costs one load.
    It stands for the anchor it was loaded with, so it is never passed beside
    ``anchor`` (``require_one_config_source`` raises).
    """
    return resolve_task_runner_source(
        task, anchor=anchor, recorded=recorded, snapshot=snapshot,
    )[0]


def resolve_task_runner_source(
    task: Dict[str, Any],
    *,
    anchor: Optional[str] = None,
    recorded: Optional[Dict[str, str]] = None,
    snapshot: Any = None,
) -> Tuple[str, str]:
    """:func:`resolve_task_runner`, plus the ``key`` naming what supplied the spec.

    The second element is what a preflight refusal prints as *the thing to
    edit* (D3 step 3's ``key=`` repair). Before it, every message said
    ``driver.subagent_runner`` whatever rung answered — and on the host and base
    rungs that names a key no file on the user's machine sets, then closes by
    telling them to edit it. So the source travels with the spec:

    * a runner recorded by a previous attempt → ``tasks[<id>].runner (recorded
      from a previous attempt)``;
    * the task's own ``model_hint`` → ``tasks[<id>].model_hint``;
    * the ladder → ``driver.subagent_runner`` (or ``_cheap``) with the layer
      :func:`resolve_subagent_runner` reported in parentheses — ``env``,
      ``project``, ``session``, ``host capabilities`` or ``base``/``default``.
    """
    spec, key, _layer = _resolve_task_source(
        task, anchor=anchor, recorded=recorded, snapshot=snapshot,
    )
    return spec, key


def _resolve_task_source(
    task: Dict[str, Any],
    *,
    anchor: Optional[str] = None,
    recorded: Optional[Dict[str, str]] = None,
    skip_session: bool = False,
    snapshot: Any = None,
) -> Tuple[str, str, str]:
    """:func:`resolve_task_runner_source`, plus the raw ladder *layer* word.

    The layer travels separately from the rendered ``key`` because one rung —
    ``session`` — is treated differently by :func:`run_tasks` when a preflight
    refuses it, and re-deriving that from the human-readable key would mean
    parsing a sentence written for a person. ``""`` is the layer for the two
    task-level overrides, which come off the task file rather than off the
    ladder and therefore have no rung of their own.

    ``skip_session`` is forwarded to the ladder so the fallback re-resolution
    cannot return the session spec that was just refused. ``anchor`` and
    ``snapshot`` are refused together before any rung, so a task the recorded
    runner or its hint answers refuses the pair as the ladder would.
    """
    require_one_config_source(anchor, snapshot)
    task_id = str(task.get("task_id", ""))
    if recorded and task_id in recorded:
        return (
            recorded[task_id],
            f"tasks[{task_id}].runner {_RECORDED_RUNNER_SUFFIX}",
            "",
        )
    hint = task.get("model_hint")
    if isinstance(hint, str) and hint.strip() and hint.strip() != "auto" and ":" in hint:
        return hint.strip(), f"tasks[{task_id}].model_hint", ""
    tier = str(task.get("capability_tier") or "full")
    spec, layer = resolve_subagent_runner(
        tier, anchor=anchor, skip_session=skip_session, snapshot=snapshot,
    )
    driver_key = "driver.subagent_runner_cheap" if tier == "cheap" else "driver.subagent_runner"
    return spec, f"{driver_key} ({layer})", layer


def _is_session_model(
    provider_name: str, model: str, *, anchor: Optional[str] = None
) -> bool:
    """Whether ``provider:model`` is the host session's own model, whoever named it.

    The configured catalog is the operator's fan-out list; the session's model
    is by definition one the host is already running, so "not configured" is
    never news about it — on whichever rung, or under whichever recorded key,
    it arrives. Answers ``False`` whenever the session rung cannot answer, so a
    host with no session model keeps the warning exactly as it was.
    """
    try:
        session = session_runner()
        if not session:
            return False
        session_provider, session_model = parse_model_spec(session, anchor=anchor)
    except Exception:  # noqa: BLE001 - an advisory exemption never ends a run
        return False
    return (session_provider, session_model) == (provider_name, model)


def _registry_module() -> Any:
    return _provider_registry


def _effort_stripped(provider: Any, model: str) -> str:
    """``model`` without a trailing ``:effort`` the adapter accepts."""
    hook = getattr(provider, "_accepted_efforts", None)
    try:
        efforts = hook() if callable(hook) else ()
    except Exception:  # noqa: BLE001 - an advisory read never ends a run
        efforts = ()
    base, _effort = split_reasoning_effort(str(model or ""), efforts or ())
    return base.strip()


def _in_operator_roster(
    provider_name: str, provider: Any, model: str, *, anchor: Optional[str] = None
) -> bool:
    """Whether ``provider:model``, effort suffix stripped from both sides, is in
    the operator's own roster or in ``<provider>.models`` (plan §6.1,
    2026-09-24).

    The roster is ``defaults.quick_models`` + ``defaults.models`` of the
    **effective** config — the same project-layer-resolved ``providers.yaml``
    ``is_model_valid(spec, anchor=anchor)`` reads the catalog from — so a
    project that narrowed its roster and left the model out keeps the warning.
    ``codex:gpt-6-astra`` matches the roster entry ``codex:gpt-6-astra:xhigh``;
    a typo'd id, suffixed or not, matches neither and stays warned.
    """
    wanted = _effort_stripped(provider, model)
    if not wanted:
        return False
    try:
        config = _registry_module().load_config(anchor=anchor)
    except Exception:  # noqa: BLE001 - an advisory read never ends a run
        return False
    defaults = config.get("defaults") or {}
    roster: List[str] = []
    for key in ("quick_models", "models"):
        value = defaults.get(key) or []
        if isinstance(value, list):
            roster += [entry for entry in value if isinstance(entry, str)]
    for entry in roster:
        try:
            entry_provider, entry_model = parse_model_spec(entry, anchor=anchor)
        except Exception:  # noqa: BLE001
            continue
        if entry_provider == provider_name and _effort_stripped(provider, entry_model) == wanted:
            return True
    block = (config.get("providers") or {}).get(provider_name) or {}
    catalog = block.get("models") if isinstance(block, dict) else None
    if isinstance(catalog, list):
        for entry in catalog:
            name = entry.get("name") if isinstance(entry, dict) else entry
            if isinstance(name, str) and _effort_stripped(provider, name) == wanted:
                return True
    return False


def _catalog_file_for_warning(anchor: Optional[str] = None) -> str:
    """The ``providers.yaml`` an operator edits to quiet the catalog warning:
    the project layer's resolved path, else the env layer's, else the base
    file — never ``hosts/capabilities.yaml``, whose pin follows the roster."""
    registry = _registry_module()
    try:
        layers = dict(registry._override_paths(anchor))
    except Exception:  # noqa: BLE001 - an advisory read never ends a run
        layers = {}
    for name in ("project", "env"):
        path = layers.get(name)
        if path is not None:
            try:
                return str(Path(path).resolve())
            except OSError:
                return str(path)
    return str((Path(registry.__file__).parent.parent / "providers.yaml").resolve())


#: The suffix :func:`_resolve_task_source` puts on a runner a previous attempt
#: of the same task recorded.
_RECORDED_RUNNER_SUFFIX = "(recorded from a previous attempt)"
