"""Whether a runner can serve a phase, asked before anything is
dispatched: :func:`preflight_runner` and its legs.

The version (:func:`_detect_version`, D3m), auth (:func:`_detect_auth`,
under the environment a dispatch gets), model (:func:`_detect_model`)
and nested-exec legs (:func:`_detect_nested_exec`; its probe
:func:`_probe_nested_exec` spawns one dispatch through ``dispatch_spawn``
and reads it with ``attempt_classifier``), and
:func:`probe_setup_metadata`. The sandbox leg is ``sandbox_walk``'s and
the caches are ``probe_state``'s.

``utils.subagent_executor`` re-exports every name defined here for reading
only: patch one here, never through the executor
(docs/development/delegation.md#where-the-executors-helpers-live).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .llm_client import _resolve_executable
from . import provider_registry as _provider_registry
from .provider_registry import (
    SESSION_LAYER,
    get_provider,
    is_model_valid,
    parse_model_spec,
)
from .providers.base import (
    JailRequest,
    LLMProvider,
    PROFILE_AGENT_READONLY,
    split_reasoning_effort,
    env_allowlist_enabled,
    matches_any,
    version_verdict,
    AUTH_STATE_CONFIG,
    CONFIG_AUTH_DECLARED,
    CONFIG_AUTH_UNKNOWN,
)
from .retry_ladder import (
    STATUS_AUTH_FAILED,
    STATUS_INVALID_MODEL,
    STATUS_SANDBOX_UNAVAILABLE,
)
from .subagent_tasks import preferred_prompt_transport
from . import failure_capture as _failure_capture
from . import task_outcome as _task_outcome
from . import runner_selection as _runner_selection
from . import probe_state as _probe_state
from . import sandbox_walk as _sandbox_walk
from . import dispatch_spawn as _dispatch_spawn
from . import attempt_classifier as _attempt_classifier


#: The four ``nested_exec`` refusal codes, mapped to the capability field each
#: one is a verdict about.
#:
#: These are *structured* refusals rather than crashes, and the mapping exists
#: because their consumers are not all Python. The OpenCode plugin surfaces each
#: one as a named tool error carrying the reason code **and the field it came
#: from**, so a model is told which capability said no rather than handed a bare
#: non-zero exit — and it reads that pairing from generated data rather than
#: re-deriving it in JavaScript.
NESTED_EXEC_FIELDS: Dict[str, str] = {
    "nested_exec_denied": "nested_exec",
    "nested_exec_spawn": "nested_exec.spawn",
    "nested_exec_network": "nested_exec.network",
    "nested_exec_credentials": "nested_exec.credentials",
}


#: Substrings that identify a *host-side egress* failure in a nested probe's
#: streams (D3c ``nested_exec.network``). Deliberately narrower than the adapters'
#: own classifier sets: these are matched only on a throwaway probe whose entire
#: expected output is one fixed token, and every entry names a transport
#: condition a model answer has no reason to contain. Matched through
#: ``matches_any`` (boundary-aware), never as bare substrings.
NETWORK_DENIAL_PATTERNS: Tuple[str, ...] = (
    "network is unreachable",
    "no route to host",
    "connection refused",
    "connection reset by peer",
    "connection timed out",
    "could not connect",
    "unable to connect",
    "failed to connect",
    "temporary failure in name resolution",
    "name or service not known",
    "getaddrinfo",
    "eai_again",
    "econnrefused",
    "enetunreach",
    "certificate verify failed",
    "self signed certificate",
    "tls handshake",
    "proxy connect",
    "blocked by proxy",
    "egress blocked",
)

#: The word the probe asks for and then looks for. Split out of the prompt so the
#: question and the answer cannot drift apart: the verdict below is decided by
#: searching for this exact string, and a prompt that asked for a different one
#: would record ``unknown`` on every healthy runner.
NESTED_PROBE_MARKER = "MULTI_LLM_NESTED_EXEC_OK"

#: The throwaway prompt the nested-exec probe dispatches (D3c). Trivial on
#: purpose: it is a real, billed turn, so it asks for one token and nothing that
#: needs the workspace, and it runs under ``agent-readonly`` regardless of the
#: profile the batch itself will use — a probe must never hold write access.
NESTED_PROBE_PROMPT = (
    f"Reply with exactly this token and nothing else: {NESTED_PROBE_MARKER}"
)

#: Wall-clock budget for that probe. Long enough for a cold agent CLI start plus
#: one trivial turn, short enough that a wedged sandbox — or merely a slow
#: runner — fails the preflight rather than consuming the batch's own budget.
#:
#: **Why 30 s and not the 120 s this used to be.** The deadline only ever decides
#: how long an *inconclusive* probe is allowed to stall the batch: everything it
#: can still learn after the first seconds is ``allowed``, and ``allowed`` and
#: ``unknown`` dispatch identically. The three verdicts that actually refuse — a
#: launch error (the child never started), a login notice, an egress failure —
#: are all decided before the runner's first token, so no denial needs a long
#: window to surface. What a long window buys is dead time, and the 2026-09-13
#: review-plan run measured it: on ``opencode:opencode/nemotron-3-ultra-free``
#: (a free-tier rung where a one-word ``opencode run`` reply takes ~62 s idle,
#: and longer behind a reviewer fan-out) the probe blew the 120 s deadline
#: anyway, so the run paid 120 s of wall clock between the fan-out and the first
#: validation dispatch to record the same ``unknown`` a 30 s deadline would have
#: recorded 90 s sooner. 30 s still clears a cold CLI start plus a trivial turn
#: on every runner fast enough for the verdict to mean anything.
NESTED_PROBE_TIMEOUT_S = 30.0


def preflight_runner(
    spec: str,
    *,
    profile: str = PROFILE_AGENT_READONLY,
    key: str = "driver.subagent_runner",
    anchor: Optional[str] = None,
    check_version: bool = True,
    layer: Optional[str] = None,
    check_auth: bool = True,
    check_nested: bool = True,
    probe_nested: bool = True,
    jail_request: Optional[JailRequest] = None,
) -> Dict[str, Any]:
    """Validate one runner spec; detect version, auth and nested-exec (D3c/D3m).

    Checks, earliest wins: the provider has an adapter, the model spec is valid
    for that provider, the adapter declares the requested profile, and (for a
    ``workspace-read`` phase) it declares ``supports_workspace_reads``. Then
    ``version_cmd`` runs once and its result is cached for the process: below
    ``min_version`` is a hard exit-3 refusal before any child is dispatched, above
    ``verified_version`` is a one-line warning (blocking on new releases would rot
    faster than the CLIs do), and unparseable output is recorded ``unknown`` with
    the same warning.

    The adapter's ``auth_check`` runs in the same preflight and is cached the same
    way (D3c): **installed is not authenticated** — every ``is_available()`` is a
    bare ``shutil.which``, so a logged-out CLI passes detection and would
    otherwise be discovered one spawned child at a time, once per task in the
    batch. A recognized login notice is exit 3 here, before anything is
    dispatched; anything the probe cannot read (no ``auth_check`` declared, the
    subcommand missing, the probe itself failing) is recorded ``unknown`` and
    never blocks, leaving the reactive ``auth_error_patterns`` path (rung 1) to
    catch it.

    Last comes the host's own ``nested_exec`` verdict (D3c), because presence,
    version and auth all describe the *runner* and none of them answers whether
    this host lets a third-party CLI run inside it with network and credentials
    intact. A declared ``denied`` leg is exit 3 naming the field — dispatching
    into a sandbox that eats the failure would spend the retry budget on every
    task in the batch — and a leg the data records as ``unknown`` or
    ``needs-config`` is *probed*, once per distinct host/runner/run, with one
    throwaway ``agent-readonly`` dispatch whose recognized denials (a refused
    spawn, an egress block, a credential notice from inside the sandbox) are the
    same exit 3 before anything is scheduled. An inconclusive probe is recorded
    ``unknown`` and never blocks, exactly like the version and auth probes.
    ``probe_nested=False`` keeps the declared verdict and suppresses only that
    throwaway dispatch — it is what ``--dry-run-subagents`` passes, because the
    probe is a real turn and "start no child" (D3l) means it.

    Between the catalog leg and the host's verdict sits the D6 sandbox
    self-test: an adapter that puts an OS sandbox between the model and the
    filesystem (codex, through bubblewrap) declares a model-free
    ``sandbox_probe_command`` for **every** profile it dispatches — the
    read-only one too, because a bwrap that cannot start denies a read dispatch
    the repository it was sent to read — and a non-zero exit is exit 3 here,
    ``sandbox_unavailable``, before the first dispatch of that profile. Cached
    per host/spec/profile; a timeout is ``unknown`` and dispatches.

    ``jail_request`` (plan codex-sandbox-unavailable step 3, 2026-09-30) is a
    write dispatch's grant — its kind, write scope and target — which the
    sandbox leg needs to decide whether the plugin's Landlock jail may take
    the dispatch: the scope joins the decision key, and the rung probe's
    positive control writes the target. Read profiles need none.

    Returns:
        ``{"provider", "model", "version", "auth", "nested_exec", "sandbox",
        "usage_support", "profile"}``.

    Raises:
        RunnerRejected: exit 3, through the one rejection formatter.
    """
    provider_name, model = parse_model_spec(spec, anchor=anchor)
    provider = get_provider(provider_name)
    if provider is None:
        raise _runner_selection._render_runner_rejection(
            key=key, spec=spec, reason_code="unknown_provider", profile=profile
        )
    if not provider.supports_profile(profile):
        raise _runner_selection._render_runner_rejection(
            key=key, spec=spec, reason_code="missing_profile", profile=profile,
            detail=(
                f"{provider_name} declares "
                f"{', '.join(provider.agent_profiles) or 'no profiles'}."
            ),
        )
    if not provider.is_available():
        raise _runner_selection._render_runner_rejection(
            key=key, spec=spec, reason_code="binary_absent", profile=profile,
        )
    # R3 — a *structural* refusal, which is a different predicate from the
    # catalog warning below and must be kept different. The adapter is asked
    # whether its own addressing scheme can express this model token at all;
    # only an adapter that can answer that question declares the hook (opencode
    # resolves `provider/model` and a bare token yields an empty model half), and
    # the answer never comes from a catalog. A catalog that is empty, stale or
    # unreadable can therefore only ever downgrade the *warning* below to
    # silence — it can never produce an exit.
    describe_unresolvable = getattr(provider, "describe_unresolvable_model", None)
    if callable(describe_unresolvable):
        # Plan §8 T8.3: `profile` and `anchor` let opencode answer the hermetic
        # reconstructibility question here, ahead of the auth leg, so a
        # user-config-only provider gets the `config_providers` sentence rather
        # than "run `opencode auth login`".
        try:
            unresolvable = describe_unresolvable(
                model, profile=profile, anchor=anchor
            )
        except Exception:  # noqa: BLE001 - a diagnostic may not break a preflight
            unresolvable = None
        if unresolvable:
            raise _runner_selection._render_runner_rejection(
                key=key, spec=spec, reason_code="unresolvable_model",
                profile=profile, detail=str(unresolvable),
            )
    # A catalog problem downgrades to "no warning", never to an exit (R3): the
    # catalog is advisory here, and a read that fails says nothing about whether
    # the runner can serve this model.
    try:
        catalogued = is_model_valid(spec, anchor=anchor)
    except Exception:  # noqa: BLE001 - an advisory read may not end a run
        catalogued = True
    # The session rung is exempt: the configured catalog is the operator's list
    # of fan-out models in providers.yaml, and the session's own model is by
    # definition one the host is already running — warning that it is "not
    # configured" told an opencode user their selected model was suspect on
    # every run. The live catalog leg (`_detect_model`) still judges it.
    # The exemption is keyed on the *model* as well as on the rung: the same
    # model reaches this function under other keys — the generate-tasks
    # orchestrator's own preflight, and `tasks[<id>].runner (recorded from a
    # previous attempt)` on a re-invocation — and each of those printed the
    # warning the session rung had just been excused from (measured
    # 2026-09-14, twice per `generate-tasks` retry).
    # Plan §6.1 (2026-09-24): the operator's own roster exempts too, under every
    # key — the host-capabilities pin included, whose comment says it "follows
    # the roster" — matched with the effort suffix stripped from both sides
    # (`codex:gpt-6-astra` is `codex:gpt-6-astra:xhigh`'s model). The roster is
    # the effective config's, never the base file's alone.
    if (
        not catalogued
        and layer != SESSION_LAYER
        and not _runner_selection._is_session_model(provider_name, model, anchor=anchor)
        and not _runner_selection._in_operator_roster(provider_name, provider, model, anchor=anchor)
    ):
        print(
            f"multi-llm warning: {key} names model {model!r}, which is not in "
            f"{provider_name}'s configured catalog — dispatching anyway. Add it "
            f"to `{provider_name}.models` (or to `defaults.quick_models` / "
            f"`defaults.models`) in {_runner_selection._catalog_file_for_warning(anchor)}.",
            file=sys.stderr,
        )

    info = {
        "provider": provider_name,
        "model": model,
        "profile": profile,
        "usage_support": provider.usage_support,
        "version": "unknown",
        "auth": "unknown",
        "nested_exec": "unknown",
        "sandbox": "unknown",
    }
    if check_version:
        info["version"] = _detect_version(provider_name, key=key, spec=spec, profile=profile)
    if check_auth:
        info["auth"] = _detect_auth(
            provider_name, model, key=key, spec=spec, profile=profile,
            anchor=anchor,
        )
    # D3 step 3 — the CLI's own catalog, after version and auth and before
    # nested-exec: a too-old CLI, or a logged-out one running a model that needs
    # a credential, is already a refusal and neither can produce a trustworthy
    # listing. A credential-free id exempted by the auth leg does reach here.
    # Gated on `check_auth` and `check_version` alike, because a caller that
    # asked for neither probe asked for no CLI spawn at all.
    if check_version or check_auth:
        info["model_catalog"] = _detect_model(
            provider_name, model, key=key, spec=spec, profile=profile, anchor=anchor
        )
        # D6 step 3 — the runner's own OS sandbox, exercised where the batch
        # would run it, with no model involved. Only an adapter that declares a
        # command for this profile is probed (codex, for every profile it
        # dispatches — read-only included, since that is the same bubblewrap);
        # everything else records `not-required`. Same gate as the catalog
        # leg: a caller that asked for no CLI spawn gets none.
        info["sandbox"] = _sandbox_walk._detect_sandbox(
            provider_name, key=key, spec=spec, profile=profile, anchor=anchor,
            **({"jail_request": jail_request} if jail_request is not None else {}),
        )
    if check_nested:
        info["nested_exec"] = _detect_nested_exec(
            provider_name, model,
            key=key, spec=spec,
            # The version probe already started this CLI as a child of the host's
            # own shell, so a parsed version is a *spawn* observation and the
            # throwaway dispatch has one less leg to answer for.
            spawn_observed=info["version"] != "unknown",
            probe=probe_nested,
        )
    return info


# The version comparison this module used to own (`_version_tuple`) is gone:
# M14 (§5.4) merged it with the twin in `providers/base.py` so the preflight's
# refusal and `describe_availability`'s label are computed from one rule. The
# floor, the ceiling and the above-verified warning now all come back from
# `version_verdict`, which is imported above.


def _run_probe(
    argv: Sequence[str], env: Optional[Mapping[str, str]] = None
) -> Optional["subprocess.CompletedProcess"]:
    """Run one cheap preflight argv (``version_cmd`` / ``auth_check``).

    Returns ``None`` when the probe could not be run at all, which every caller
    reads as "unknown": a preflight probe reports, it never blocks on its own
    failure.

    ``env`` (plan §8 T8.13) is the environment the probe runs under; ``None``
    inherits this process's, which is what every caller but the auth leg
    passes. The auth leg hands in :func:`dispatch_child_env`'s result, so the
    probe sees what a dispatch would.
    """
    launcher, _ = _resolve_executable(argv[0])
    kwargs: Dict[str, Any] = {}
    if env is not None:
        kwargs["env"] = dict(env)
    try:
        return subprocess.run(
            [*launcher, *argv[1:]],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            stdin=subprocess.DEVNULL,
            **kwargs,
        )
    except (OSError, subprocess.SubprocessError):
        return None


def _detect_version(
    provider_name: str, *, key: str, spec: str, profile: str
) -> str:
    """Run ``version_cmd`` once per provider and apply the shared gate (D3m).

    The probe is this module's; the **verdict is not**. Both bounds — the
    ``min_version`` floor and M14's ``max_version_exclusive`` ceiling — plus the
    advisory above-``verified_version`` warning come back from
    ``providers.base.version_verdict``, which is the same rule
    ``describe_availability`` labels a runner with (§5.4). Reading the streams
    **concatenated** is :meth:`parse_version`'s job, and it is why a CLI that
    banners its version to stderr is read at all.
    """
    if provider_name in _probe_state._VERSION_CACHE:
        return _probe_state._VERSION_CACHE[provider_name]

    provider = get_provider(provider_name)
    version = "unknown"
    argv = list(getattr(provider, "version_cmd", ()) or ())
    if argv:
        completed = _run_probe(argv)
        if completed is not None:
            parsed = provider.parse_version(completed.stdout, completed.stderr)
            if parsed:
                version = parsed

    if version == "unknown":
        if argv:
            print(
                f"multi-llm warning: could not determine the {provider_name} "
                f"version from `{' '.join(argv)}` — recording 'unknown'. A CLI "
                f"that dropped --version still answers prompts, so this is not a "
                f"blocker, but a stream-shape failure will not name a build.",
                file=sys.stderr,
            )
    else:
        verdict = version_verdict(provider, version, name=provider_name)
        if verdict.refuses:
            # A build outside the declared range is a refusal before any child,
            # not a degraded run: the adapter's parser was written against a
            # stream shape this build does not produce.
            raise _runner_selection._render_runner_rejection(
                key=key, spec=spec, reason_code="missing_capability",
                profile=profile, detail=verdict.detail,
            )
        if verdict.detail:
            # Above `verified_version` — a warning, never a block: blocking on
            # new releases would rot faster than the CLIs do.
            print(f"multi-llm warning: {verdict.detail}", file=sys.stderr)

    _probe_state._VERSION_CACHE[provider_name] = version
    return version


#: A CSI or OSC terminal escape — enough to tell a stream that carries only
#: colour resets from one that says something.
_PROBE_ESCAPE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)")


def _probe_verdict_stream(
    completed: Optional["subprocess.CompletedProcess"],
) -> str:
    """The stream a ``not_authenticated`` refusal should quote.

    stderr when it says anything, else stdout. "Says anything" is judged with
    terminal escapes removed, because a bare ``stderr or stdout`` quoted
    opencode 1.18.32's stderr — which is exactly ``"\\x1b[0m\\n"``, a colour
    reset and nothing else — while the ``└  0 credentials`` line the verdict was
    drawn from sat on stdout. The refusal then told its reader the probe had
    printed nothing, which is how a correct refusal was first mis-diagnosed as
    a parser break (measured in the container lane, 2026-09-25).
    """
    if completed is None:
        return ""
    stderr = completed.stderr or ""
    if _PROBE_ESCAPE.sub("", stderr).strip():
        return stderr
    return completed.stdout or stderr


#: A variable name shaped like a credential, for the one sentence that names
#: what ``env_allowlist`` (or a host guard) dropped from the probe's env. Names
#: only, never values.
_CREDENTIAL_NAME = re.compile(
    r"(?:API_KEY|_TOKEN|_SECRET|ACCESS_KEY|_KEY)$", re.IGNORECASE
)


def _auth_cache_key(
    provider: Any,
    provider_name: str,
    model: str,
    *,
    needs_auth: bool,
    profile: str,
    anchor: Optional[str],
) -> str:
    """``<provider>|<needs 0/1>|<profile>|<model prefix>|<hermetic/plain>``.

    The prefix is the model's ``provider/`` half after the ``:effort`` split
    (empty for a bare token); hermeticity is asked of the adapter's module the
    way :func:`_model_cache_key` asks it. Every leg degrades to a constant: a
    cache key may never be what ends a preflight.
    """
    normalized = model or ""
    try:
        normalized, _ = split_reasoning_effort(
            normalized, provider._accepted_efforts()  # noqa: SLF001 - the base's hook
        )
    except Exception:  # noqa: BLE001
        normalized = model or ""
    normalized = normalized.strip()
    prefix = normalized.split("/", 1)[0] if "/" in normalized else ""
    hermetic = "plain"
    try:
        module = sys.modules.get(type(provider).__module__)
        enabled = getattr(module, "hermetic_enabled", None)
        if callable(enabled) and enabled(profile, anchor):
            hermetic = "hermetic"
    except Exception:  # noqa: BLE001
        hermetic = "plain"
    return (
        f"{provider_name}|{1 if needs_auth else 0}|{profile}|{prefix}|"
        f"{hermetic}"
    )


def _dropped_credential_names(child_env: Optional[Mapping[str, str]]) -> List[str]:
    """Credential-shaped names this process carries that the probe env lacks."""
    if child_env is None:
        return []
    return sorted(
        name for name in os.environ
        if name not in child_env and _CREDENTIAL_NAME.search(name)
    )


def _detect_auth(
    provider_name: str,
    model: str = "",
    *,
    key: str,
    spec: str,
    profile: str,
    anchor: Optional[str] = None,
    cwd: Optional[str] = None,
) -> str:
    """Run ``auth_check`` once per cache key and refuse a logged-out CLI (D3c).

    Returns ``"ok"``, ``"unknown"``, ``"not-required"`` or ``"config"``; a
    recognized login/credential notice raises instead, because every sibling
    task in the batch would fail identically and no retry can fix a missing
    credential. ``unknown`` is the honest answer for a CLI that declares no
    probe (claude-code has no non-interactive status subcommand) or whose probe
    could not be read — never an assumption of success.

    ``model`` is what decides whether a ``False`` verdict is *allowed to refuse*
    (D3 step 2). On a CLI that fronts several vendors "needs a credential" is a
    property of the model, not of the binary, so the adapter is asked
    ``model_needs_credentials(model)``: when it declares the model credential-free
    the probe still runs and its verdict is still recorded (status keeps its
    evidence) but the refusal is skipped and the leg reads ``not-required``. A
    ``True``/``None`` verdict is untouched either way, and a credential-requiring
    spec on the same provider in the same process still refuses — the cache is
    keyed on the answer, not on the provider alone.

    **The probe runs under the dispatch's env (plan §8 T8.13).** On a cache
    miss, and only then, :func:`dispatch_child_env` builds what a dispatch of
    this model under ``profile`` would get — the adapter's delta, the
    ``env_allowlist`` filter, the host's ``env_guards`` — and ``auth_check``
    runs under it; ``cwd`` (default: the repo root the dispatch pins) is what
    ``resolve_env`` and the config hook see, not the probe's working directory
    (every probe adapter's status command reads a fixed store). A key the
    allowlist drops is therefore not counted as a login, and the refusal says
    so by name. An env that cannot be built never turns a refusal into a pass:
    the probe runs under the inherited environment, but only its ``False`` is
    kept (a ``True`` reads ``unknown``) and the config leg is not asked. The probe deliberately runs **outside**
    ``hermetic_dispatch``: the slot's delta redirects only ``XDG_CONFIG_HOME``
    and cannot hide ``auth.json`` (``XDG_DATA_HOME`` passes through), and
    entering it would turn a user-config-only provider into a skipped probe
    instead of the structural leg's ``unresolvable_model`` sentence.

    **The config leg (T8.4).** When the verdict is ``False`` for a model that
    needs a credential, the adapter's ``config_credential_source`` is asked
    whether the dispatch's own resolved config declares the provider (opencode:
    a custom provider, or a built-in override whose key resolves in the
    dispatch env). ``declared``
    records ``config`` and refuses nothing; ``unknown`` is today's refusal.
    Lazy: a ``True`` verdict never spawns it.
    """
    provider = get_provider(provider_name)
    needs_credentials = _runner_selection._model_needs_credentials(provider, model)
    cache_key = _auth_cache_key(
        provider, provider_name, model,
        # Keyword named `needs_auth`: the same-name credentials keyword form
        # trips the redaction-looseness tripwire in test_redaction.py.
        needs_auth=needs_credentials, profile=profile, anchor=anchor,
    )
    if cache_key in _probe_state._AUTH_CACHE:
        return _probe_state._AUTH_CACHE[cache_key]

    argv = list(getattr(provider, "auth_check", ()) or ())
    if not argv:
        _probe_state._AUTH_CACHE[cache_key] = "unknown"
        return "unknown"

    probe_cwd = cwd if cwd is not None else _sandbox_walk._probe_cwd(anchor)

    def build_env() -> Optional[Dict[str, str]]:
        # Built only on this cache miss, immediately before its spawn, and never
        # handed to a dispatch: cursor-agent's `resolve_env` has a bounded side
        # effect, and a hermetic delta belongs to one spawn. A failure raises:
        # `None` already means "inherit this process's env", so swallowing it
        # into `None` would run the probe (or the config hook's `debug config`)
        # with neither the delta nor the `env_allowlist`, counting a key the
        # dispatch will never see as a login. The config hook's own catch-all
        # turns the raise into `unknown`.
        return _dispatch_spawn.dispatch_child_env(
            provider, model, profile, anchor=anchor, cwd=probe_cwd
        )

    env_build_failed = False
    try:
        probe_env = build_env()
    except Exception:  # noqa: BLE001 - an env build may never end a preflight
        # Fail closed, never open: the probe still runs (inheriting this
        # process's env) so a logged-out CLI is still refused, but a `True`
        # it returns is demoted to "unknown" below and the config leg is not
        # asked — an env we could not build cannot vouch for a credential.
        probe_env = None
        env_build_failed = True
    completed = _run_probe(argv, env=probe_env)
    verdict: Optional[bool] = None
    if completed is not None:
        try:
            verdict = provider.classify_auth_probe(
                completed.stdout, completed.stderr, completed.returncode
            )
        except Exception:  # noqa: BLE001 - a probe must never break a preflight
            verdict = None
    if verdict is True and env_build_failed:
        # The inherited env may carry a key the dispatch env would drop
        # (`env_allowlist`, a host guard), so this login is not evidence.
        verdict = None
    if verdict is False and not needs_credentials:
        # Measured, not assumed: the adapter declared this model answers with no
        # credential present, so a logged-out probe is evidence about *other*
        # models on this CLI and refuses nothing here.
        _probe_state._AUTH_CACHE[cache_key] = "not-required"
        return "not-required"
    if verdict is False:
        source = CONFIG_AUTH_UNKNOWN
        hook = getattr(provider, "config_credential_source", None)
        if callable(hook) and not env_build_failed:
            try:
                source = hook(
                    model, profile=profile, anchor=anchor, cwd=probe_cwd,
                    env_builder=build_env,
                )
            except Exception:  # noqa: BLE001 - a diagnostic read may never end a preflight
                source = CONFIG_AUTH_UNKNOWN
        if source == CONFIG_AUTH_DECLARED:
            _probe_state._AUTH_CACHE[cache_key] = AUTH_STATE_CONFIG
            return AUTH_STATE_CONFIG
        login = getattr(provider, "login_cmd", "") or f"{argv[0]} login"
        # The probe's own envelope, redacted at this boundary: cursor-agent's
        # `status --format json` carries `userEmail`/`terminalProgram`/`shell`
        # (M13), and this message is printed straight to a terminal and a log —
        # it reaches neither of §4.5.3's redacting write sinks.
        tail = _failure_capture._redact_probe_tail(_probe_verdict_stream(completed), 500)
        dropped = _dropped_credential_names(probe_env)
        dropped_note = ""
        if dropped:
            # T8.13: this case used to pass preflight and fail at dispatch with
            # a vendor auth error, so the behaviour change is named. Names only.
            cause = (
                "`env_allowlist: on` does not admit "
                + ("it" if len(dropped) == 1 else "them")
                + " for this runner"
                if env_allowlist_enabled(anchor)
                else "a host env guard strips "
                + ("it" if len(dropped) == 1 else "them")
            )
            dropped_note = (
                f" This process's environment sets {', '.join(dropped)}, but the "
                f"runner's environment does not carry "
                f"{'it' if len(dropped) == 1 else 'them'} ({cause}), so the probe "
                f"ran without {'it' if len(dropped) == 1 else 'them'}, as a "
                f"dispatch would."
            )
        raise _task_outcome.RunnerRejected(
            f"Refusing to dispatch: {key} is {spec!r} (reason: not_authenticated) — "
            f"{_runner_selection._REASON_EXPLANATION['not_authenticated']}. "
            f"`{' '.join(argv)}` reported: {tail!r}.{dropped_note} "
            f"Fix: run `{login}`"
            + (
                " (a stored credential is not filtered by env_allowlist)"
                if dropped and env_allowlist_enabled(anchor)
                else ""
            )
            + ", then re-run this phase. Nothing was dispatched.",
            key=key,
            spec=spec,
            reason_code="not_authenticated",
        )

    state = "ok" if verdict else "unknown"
    _probe_state._AUTH_CACHE[cache_key] = state
    return state


def _model_cache_key(
    provider: Any, provider_name: str, model: str, *, profile: str,
    anchor: Optional[str],
) -> str:
    """``<provider>|<hermetic on/off>|<config-content digest>|<normalized model>``.

    The digest is over the adapter's own merged ``providers.<name>`` block —
    the source every rebuilt ``OPENCODE_CONFIG_CONTENT`` and the hermetic policy
    are read from — so an edit that would change the listing changes the key.
    Every leg degrades to a constant rather than raising: a cache key may never
    be what ends a preflight.
    """
    hermetic = "plain"
    try:
        module = sys.modules.get(type(provider).__module__)
        enabled = getattr(module, "hermetic_enabled", None)
        if callable(enabled) and enabled(profile, anchor):
            hermetic = "hermetic"
    except Exception:  # noqa: BLE001
        hermetic = "plain"
    digest = "-"
    try:
        # Through the module, at each call: tests patch `provider_registry.load_config`.
        block = (_provider_registry.load_config(anchor=anchor).get("providers") or {}).get(
            provider_name)
        digest = hashlib.sha256(
            json.dumps(block or {}, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()[:16]
    except Exception:  # noqa: BLE001
        digest = "-"
    normalized = model
    try:
        efforts = provider._accepted_efforts()  # noqa: SLF001 - the base's own hook
        normalized, _ = split_reasoning_effort(model, efforts)
    except Exception:  # noqa: BLE001
        normalized = model
    return f"{provider_name}|{hermetic}|{digest}|{normalized.strip()}"


def _detect_model(
    provider_name: str,
    model: str,
    *,
    key: str,
    spec: str,
    profile: str,
    anchor: Optional[str] = None,
) -> str:
    """Ask the CLI's own catalog whether ``model`` exists — once per slot (D3 step 3).

    The third and last leg about the *runner*, and the only one of the three
    model checks that spawns anything: ``describe_unresolvable_model`` is the
    structural, catalog-free refusal and the ``is_model_valid`` line is an
    advisory warning about *our* configured list; this is the CLI's answer.
    The adapter's :meth:`describe_unlisted_model` reads the listing inside the
    same dispatch context the dispatch will use (D3 step 4), under the same
    30 s ceiling every probe has — a listing that hangs is killed and read as
    unknown.

    Verdicts: ``known=True`` → ``"ok"``; ``known=False`` → the same
    ``RunnerRejected`` every other leg raises, reason ``invalid_model_catalog``
    (deliberately distinct from D4's dispatch-time ``runner_invalid_model``, so
    a preflight refusal and a dispatch-time one stay separable in a log), with
    the ``detail`` the adapter composed from the listing it just read;
    ``known=None`` → ``"unknown"``, printed like every other unknown and
    **never blocking** — the run proceeds exactly as it would with no probe at
    all, and D4 is the backstop that catches a real miss one attempt later in
    the provider's own words.

    **This runs at preflight and nowhere on the resolution ladder**: the ladder
    stays subprocess-free so ``status`` stays sub-second, and there is no rung
    fallback — the spec refused is the spec the ladder already finished
    resolving, whatever rung supplied it, and ``key`` names that rung.
    """
    provider = get_provider(provider_name)
    cache_key = _model_cache_key(
        provider, provider_name, model, profile=profile, anchor=anchor
    )
    if cache_key in _probe_state._MODEL_CACHE:
        return _probe_state._MODEL_CACHE[cache_key]

    # Every adapter takes `profile` (LLMProvider's signature does), so a
    # TypeError here is a bug in the adapter's own code, not a narrow signature:
    # it is reported as a catalog that could not be read, never retried.
    try:
        verdict = provider.describe_unlisted_model(
            model, anchor=anchor, profile=profile
        )
    except Exception:  # noqa: BLE001 - a catalog read may never end a preflight
        verdict = None

    known = getattr(verdict, "known", None)
    if known is False:
        raise _runner_selection._render_runner_rejection(
            key=key, spec=spec, reason_code="invalid_model_catalog",
            profile=profile, detail=str(getattr(verdict, "detail", "") or ""),
        )
    state = "ok" if known is True else "unknown"
    overrides_hook = (
        getattr(type(provider), "describe_unlisted_model", None)
        is not LLMProvider.describe_unlisted_model
    )
    if state == "unknown" and overrides_hook:
        # Only an adapter that has a listing to read gets the warning: the
        # base's typed default is "no catalog here", which is not a failed read.
        print(
            f"multi-llm warning: could not confirm {model!r} against "
            f"{provider_name}'s own model listing — recording 'unknown' and "
            f"dispatching anyway; a model the runner really rejects is caught "
            f"on the first attempt in the runner's own words.",
            file=sys.stderr,
        )
    _probe_state._MODEL_CACHE[cache_key] = state
    return state


def probe_setup_metadata(provider_name: str) -> Dict[str, str]:
    """Run an adapter's declared ``setup_probe`` and read it as metadata (M13, §5.2).

    The status path's counterpart to :func:`_detect_auth`, and deliberately not
    part of :func:`preflight_runner`: what this returns decides **nothing** — no
    refusal, no retry, no availability state — so a dispatch preflight would be
    paying a subprocess per phase for a sentence only a human reads. It is
    spawned from ``install-host --check`` row 5, which already runs the version
    and auth probes and is invoked by hand.

    It is not an auth probe and cannot become one. cursor-agent's ``about`` — the
    only declared readout today — returns the same two nulls for a logged-in CLI
    with the endpoint unreachable as for a logged-out one, which is why M13
    demoted it; the verdict comes from ``auth_check`` and only from there.

    Nothing here blocks or raises: an adapter that declares no readout, a probe
    that will not run, a reader that fails all report ``{}``, which renders as a
    status row with one less fact on it.

    Returns:
        ``label -> value`` exactly as the adapter's
        :meth:`~utils.providers.base.LLMProvider.read_setup_probe` reported it,
        minus any blank value. Every pair is rendered into a status row, so the
        adapter owes it the same care a refusal message is owed (§4.5.1).
    """
    provider = get_provider(provider_name)
    argv = list(getattr(provider, "setup_probe", ()) or ())
    if provider is None or not argv:
        return {}
    completed = _run_probe(argv)
    if completed is None:
        return {}
    try:
        facts = provider.read_setup_probe(
            completed.stdout, completed.stderr, completed.returncode
        )
    except Exception:  # noqa: BLE001 - a readout never breaks the status path
        return {}
    return {
        str(label): str(value).strip()
        for label, value in (facts or {}).items()
        if str(value).strip()
    }


def _detect_nested_exec(
    provider_name: str,
    model: str,
    *,
    key: str,
    spec: str,
    spawn_observed: bool = False,
    probe: bool = True,
) -> str:
    """Can a runner really run *inside this host*? Once per host/runner (D3c).

    Presence, version and auth are all facts about the runner; this is the one
    preflight leg about the **host**. Three verdicts:

    * a declared ``denied`` leg → exit 3 naming the field and its notes, before
      anything is scheduled. Every task in the batch would fail identically, and
      a sandbox that denies a spawn or an egress usually eats the failure into
      something the D3k ladder reads as generic runner noise and *retries*.
    * every leg ``allowed`` → ``"allowed"``, with no child spawned. The data has
      already answered; a probe would only spend a billed turn re-confirming it.
    * anything ``unknown`` or ``needs-config`` → one throwaway ``agent-readonly``
      dispatch, cached per ``host|spec`` for the process, whose recognized
      denials are the same exit 3 and whose inconclusive outcomes are
      ``"unknown"`` (a preflight probe reports; it never blocks on its own
      failure).
    """
    resolved = _probe_state._host_nested_exec()
    if resolved is None:
        return "unknown"
    host_id, legs, notes = resolved

    denied = [leg for leg in legs if legs[leg] == "denied"]
    if denied:
        raise _task_outcome.RunnerRejected(
            f"Refusing to dispatch: host {host_id!r} declares nested_exec "
            f"{', '.join(denied)} denied (reason: nested_exec_denied) — "
            f"{_runner_selection._REASON_EXPLANATION['nested_exec_denied']}. "
            + (f"{notes} " if notes else "")
            + "Fix: drop --exec-subagents and let this host's own subagent "
            "mechanism run the phase, or run it from a host whose nested_exec "
            "permits a nested CLI. Nothing was dispatched.",
            key=key,
            spec=spec,
            reason_code="nested_exec_denied",
        )

    cache_key = f"{host_id}|{spec}"
    cached = _probe_state._NESTED_CACHE.get(cache_key)
    if cached is not None:
        return cached

    unresolved = [leg for leg in legs if legs[leg] != "allowed"]
    if spawn_observed and unresolved == ["spawn"]:
        # The version probe already ran this CLI as a child of this host's shell,
        # which is the whole of the spawn leg. Nothing else is open, so there is
        # nothing left for a billed turn to answer.
        unresolved = []
    if not unresolved:
        _probe_state._NESTED_CACHE[cache_key] = "allowed"
        return "allowed"
    if not probe:
        # Deliberately uncached: the declared verdict has not been answered, and a
        # later real dispatch in this same process must still get its probe.
        return "unknown"

    state = _probe_nested_exec(
        provider_name, model,
        key=key, spec=spec, host_id=host_id, legs=unresolved, notes=notes,
    )
    _probe_state._NESTED_CACHE[cache_key] = state
    return state


def _probe_nested_exec(
    provider_name: str,
    model: str,
    *,
    key: str,
    spec: str,
    host_id: str,
    legs: Sequence[str],
    notes: str,
) -> str:
    """The throwaway dispatch behind an ``unknown``/``needs-config`` leg (D3c).

    One trivial ``agent-readonly`` turn, through the *same* :func:`_spawn` the
    batch uses — same argv builder, same composed environment, same host env
    guards — because a probe that composed its own child would answer a question
    about a process the batch never runs. Only a recognized denial refuses:

    * the child could not be started at all → the spawn leg, exit 3;
    * a login/credential notice → the credentials leg, exit 3 (from inside a
      sandbox this is as often the host's doing as a logged-out CLI, and neither
      is retryable);
    * an egress failure → the network leg, exit 3.

    ``allowed`` requires the reply to carry :data:`NESTED_PROBE_MARKER` — the word
    the prompt asked for. A clean exit whose output never mentions it is
    ``unknown`` under a warning of its own, distinct from the inconclusive one
    below so a log tells the two causes apart.

    Everything else — a timeout, a non-zero exit with nothing recognized, a
    silent zero-byte success, a clean exit that answered with something other
    than the token, an adapter that will not render the probe — is ``unknown``
    plus one warning line. The reactive ladder still covers those, and blocking a
    batch on an unreadable probe would be worse than the dispatch the probe
    exists to save.
    """
    provider = get_provider(provider_name)
    if provider is None:  # pragma: no cover - presence is checked before this
        return "unknown"
    opened = "/".join(legs)
    try:
        capture = _dispatch_spawn._spawn(
            provider=provider,
            model=model,
            prompt=NESTED_PROBE_PROMPT,
            # Always read-only, never the batch's own profile: a preflight has no
            # result to write, so it has no reason to hold write access.
            profile=PROFILE_AGENT_READONLY,
            transport=preferred_prompt_transport(provider_name),
            timeout=NESTED_PROBE_TIMEOUT_S,
            cwd=None,
        )
    except Exception as exc:  # noqa: BLE001 - a probe reports, it never blocks
        print(
            f"multi-llm warning: could not render the nested-exec probe for "
            f"{spec} on host {host_id} ({exc}) — recording nested_exec "
            f"'unknown' for {opened}.",
            file=sys.stderr,
        )
        return "unknown"

    trailer = (
        f"Host: {host_id} (nested_exec {opened} was not recorded as allowed). "
        + (f"{notes} " if notes else "")
    )

    if capture.launch_error is not None:
        raise _task_outcome.RunnerRejected(
            f"Refusing to dispatch: {key} is {spec!r} (reason: nested_exec_spawn) "
            f"— {_runner_selection._REASON_EXPLANATION['nested_exec_spawn']}: "
            f"{capture.launch_error}. {trailer}"
            f"Fix: grant this host's sandbox permission to start the runner, or "
            f"run the phase without --exec-subagents. Nothing was dispatched.",
            key=key,
            spec=spec,
            reason_code="nested_exec_spawn",
        )

    streams = f"{capture.stdout or ''}\n{capture.stderr or ''}".lower()

    if capture.timed_out:
        # A note, not a warning (2026-10-05, run 3): nothing here is the
        # user's to act on. A slow model's first turn routinely outlives the
        # probe (opencode/big-pickle, every run), the batch is dispatched anyway,
        # and a host that really blocks nested runs fails that batch with its
        # own timeout, which is where the user is told.
        print(
            f"[exec-subagents] note: the start-up check for {spec} (a one-word "
            f"test turn) did not answer within {NESTED_PROBE_TIMEOUT_S:.0f}s, so "
            f"it is unconfirmed that host {host_id} lets the runner start its "
            f"own model turn; dispatching anyway (nested_exec 'unknown' for "
            f"{opened}). Nothing to do unless a batch then times out.",
            file=sys.stderr,
        )
        return "unknown"

    classified = _attempt_classifier._classify_failed_run(provider, capture)
    if classified is not None and classified[0] == STATUS_AUTH_FAILED:
        login = getattr(provider, "login_cmd", "") or f"{provider_name} login"
        raise _task_outcome.RunnerRejected(
            f"Refusing to dispatch: {key} is {spec!r} (reason: "
            f"nested_exec_credentials) — "
            f"{_runner_selection._REASON_EXPLANATION['nested_exec_credentials']}. "
            f"Probe tail: "
            f"{_failure_capture._redact_probe_tail(capture.stderr or capture.stdout, 500)!r}. "
            f"{trailer}"
            f"Fix: run `{login}` from outside this host, or allow the runner to "
            f"read its credential store from inside it. Nothing was dispatched.",
            key=key,
            spec=spec,
            reason_code="nested_exec_credentials",
        )

    if classified is not None and classified[0] == STATUS_SANDBOX_UNAVAILABLE:
        # D6 step 4. The path that catches what step 3 has no command for —
        # any bubblewrap user whose adapter declares no `sandbox_probe_command`
        # — and, like the D4 branch below, opportunistic: it runs only where a
        # leg was unresolved and a probe therefore happened. A `bwrap:` line is
        # a fact about the machine, so every sibling fails identically and a
        # retry never changes it. The way out that works today is a non-Codex
        # runner (F6), which the refusal leads with; the AppArmor or sysctl
        # repair `doctor` prints is a system-level alternative that needs sudo
        # (plan codex-sandbox-unavailable §7 step 4, 2026-09-30). This
        # refusal walks no rung, so it carries no rung sentence.
        tail = _failure_capture._redact_probe_tail(capture.stderr or capture.stdout, 500)
        raise _sandbox_walk._sandbox_unavailable_rejection(
            key=key, spec=spec, tail=tail, trailer=trailer,
        )

    if classified is not None and classified[0] == STATUS_INVALID_MODEL:
        # D4 step 3. Opportunistic by construction: this branch only runs on a
        # host where a leg was still unresolved and a probe therefore happened.
        # The unconditional pre-dispatch gate is the preflight catalog leg (D3);
        # the guarantee when neither can answer is the fatal rung-1 status the
        # first real batch records. What this buys is zero dispatches where a
        # billed probe was going to run anyway.
        #
        # The window is `_classify_failed_run`'s 2000 bytes rather than the 500
        # the other legs quote: a login notice is the last thing a CLI prints,
        # but opencode's `ProviderModelNotFoundError` — the one line with the
        # "Did you mean" list — sits above a bun stack trace that alone
        # outruns 500 bytes, and a refusal that quotes only the frames has
        # thrown away the reason it exists to print.
        tail = _failure_capture._redact_probe_tail(capture.stderr or capture.stdout, 2000)
        raise _task_outcome.RunnerRejected(
            f"Refusing to dispatch: {key} is {spec!r} (reason: "
            f"runner_invalid_model) — "
            f"{_runner_selection._REASON_EXPLANATION['runner_invalid_model']}. "
            f"Probe tail: {tail!r}. "
            f"{trailer}"
            f"Fix: set `{key}` to a model this CLI lists "
            f"(`{provider_name} models`), or update the plugin's host default. "
            f"Nothing was dispatched.",
            key=key,
            spec=spec,
            reason_code="runner_invalid_model",
            detail=tail,
        )

    if matches_any(NETWORK_DENIAL_PATTERNS, streams):
        raise _task_outcome.RunnerRejected(
            f"Refusing to dispatch: {key} is {spec!r} (reason: "
            f"nested_exec_network) — "
            f"{_runner_selection._REASON_EXPLANATION['nested_exec_network']}. "
            f"Probe tail: "
            f"{_failure_capture._redact_probe_tail(capture.stderr or capture.stdout, 500)!r}. "
            f"{trailer}"
            f"Fix: allow this host's sandbox to reach the provider API (a domain "
            f"allow-list entry, a proxy setting), or run the phase without "
            f"--exec-subagents. Nothing was dispatched.",
            key=key,
            spec=spec,
            reason_code="nested_exec_network",
        )

    if capture.exit_code == 0 and streams.strip():
        # The probe asked for a word; this is where it is read back. Until
        # 2026-09-22 the verdict was "exit 0 and *something* on a stream", which
        # a usage banner, a progress spinner or a CLI that echoed its prompt and
        # quit all satisfy — so `allowed` meant "the binary ran", not "a model
        # answered through this host", and the container lane recorded it for a
        # runner whose every turn had been refused 422.
        #
        # PRESENCE, NOT EQUALITY, and deliberately so. These are the runner's raw
        # streams, not a parsed answer: every agent CLI this dispatches wraps the
        # reply in its own envelope (NDJSON events, usage counters, a `--print-
        # logs` tail), and `_probe_nested_exec` never calls `parse_output` — a
        # preflight has no result document, and adding a parse step here would
        # let an adapter's parser failure turn a working host into `unknown`. So
        # the prompt's "and nothing else" is a request for a cheap turn, not a
        # condition the verdict rests on; holding a model to literal exactness
        # would measure instruction-following rather than nested exec.
        #
        # The known hole, stated rather than papered over: a runner that echoes
        # our prompt into its own event stream carries the token whether or not a
        # model ever answered. That case read `allowed` under the old rule too,
        # so nothing regresses — this is strictly the tighter gate — and the
        # reactive D3k ladder still covers what it lets through.
        if NESTED_PROBE_MARKER.lower() in streams:
            return "allowed"
        print(
            f"multi-llm warning: the nested-exec probe for {spec} on host "
            f"{host_id} exited 0 with {len(streams.strip())} byte(s) of output, "
            f"but none of it carried the probe's token ({NESTED_PROBE_MARKER}) — "
            f"recording nested_exec 'unknown' for {opened}. The runner started "
            f"and returned, so this is not a denial; what is unproven is that a "
            f"model answered through it. Dispatching anyway; a real denial will "
            f"land on the D3k ladder.",
            file=sys.stderr,
        )
        return "unknown"

    print(
        f"multi-llm warning: the nested-exec probe for {spec} on host {host_id} "
        f"was inconclusive (exit {capture.exit_code}, "
        f"{len(streams.strip())} byte(s) of output) — recording nested_exec "
        f"'unknown' for {opened}. Dispatching anyway; a real denial will land on "
        f"the D3k ladder.",
        file=sys.stderr,
    )
    return "unknown"
