"""Provider registry and configuration loading.

Configuration is assembled from up to three layers, lowest → highest precedence,
each deep-merged over the one below:

1. Built-in base   — ``${skill_dir}/providers.yaml`` (always present).
2. Project-local   — ``<git-root>/.multi-llm/providers.yaml`` (auto-discovered).
3. Env override    — ``MULTI_LLM_PROVIDERS_CONFIG=/path.yaml`` (escape hatch;
   relative values resolve against CWD).

Both override layers deep-merge their **full** contents — including a
``providers:`` block — over base, identical to each other. ``command`` is
documentation-only and is NEVER executed (binaries are hardcoded in
``utils/providers/``), so no execution metadata is honored from config in any
layer. A merged provider name with no hardcoded adapter is ignored at runtime
(filtered out of :func:`get_available_models` *and* configured-spec validation); a
non-mapping provider value is restored from base when it shadows a known provider
(else dropped) at load time. ``--init`` writes layer 2 by uncommenting an inert template.

List values *replace* wholesale on merge; only nested dicts deep-merge. A blank
(``None``) override value is skipped (keeps base); an explicit empty list ``[]``
is a deliberate wipe-out. See the per-project override docs in docs/configuration.md.
"""
import copy
import math
import os
import re
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from .git_utils import (
    COLLAPSE_PATH_KEYS,
    DEFAULT_COLLAPSE_PATHS,
    compile_path_glob,
    get_project_root_from_dir,
)
from .providers.agy import AgyProvider
from .providers.aider import AiderProvider
from .providers.claude_code import ClaudeCodeProvider
from .providers.cline import ClineProvider
from .providers.codex import CodexProvider
from .providers.copilot import CopilotProvider
from .providers.cursor_agent import CursorAgentProvider
from .providers.fx import FxProvider
from .providers.gemini import GeminiProvider
from .providers.goose import GooseProvider
from .providers.grok import GrokProvider
from .providers.kilocode import KiloCodeProvider
from .providers.kimi import KimiProvider
from .providers.muse import MuseProvider
from .providers.omp import OmpProvider
from .providers.opencode import OpenCodeProvider
from .providers.pi import PiProvider
from .providers.qwen_code import QwenCodeProvider
from .providers.vibe import VibeProvider
from .providers.base import GIT_HELPER_AUTO, GIT_HELPER_POLICIES, LLMProvider

# Built-in providers
_PROVIDERS: Dict[str, LLMProvider] = {
    "agy": AgyProvider(),
    "aider": AiderProvider(),
    "claude-code": ClaudeCodeProvider(),
    "cline": ClineProvider(),
    "codex": CodexProvider(),
    "copilot": CopilotProvider(),
    "cursor-agent": CursorAgentProvider(),
    "fx": FxProvider(),
    "gemini": GeminiProvider(),
    "goose": GooseProvider(),
    "grok": GrokProvider(),
    "kilocode": KiloCodeProvider(),
    "kimi": KimiProvider(),
    "muse": MuseProvider(),
    "omp": OmpProvider(),
    "opencode": OpenCodeProvider(),
    "pi": PiProvider(),
    "qwen-code": QwenCodeProvider(),
    "vibe": VibeProvider(),
}

# Process-global config cache. Keyed on the resolved discovery anchor + env (see
# _cache_key) so a CWD-anchored result is not reused for a plan-derived root
# within the same process. Cache captures cwd/env at first load for a given key;
# a later os.chdir/setenv is not reflected for an already-cached key.
_config: Optional[dict] = None
_config_key: Optional[tuple] = None

# The run's discovery anchor (§9.3.b): the absolute plan-file path this process
# is working on, captured once during pre-flight. Consumed by _anchor_start_dir
# whenever an explicit `anchor=` is absent, so a call site the sweep missed falls
# back to THE RUN'S PLAN rather than to CWD — the difference between a residual
# timeout bug and a silently wrong provider. It is a backstop, never the primary
# mechanism: every accessor still takes and forwards `anchor=`.
_RUN_ANCHOR: Optional[str] = None

# Env var names.
ENV_CONFIG_VAR = "MULTI_LLM_PROVIDERS_CONFIG"
ENV_PERMISSIVE_VAR = "MULTI_LLM_PROVIDERS_CONFIG_PERMISSIVE"
# §2.2's one-run debugging hatch for the credential-helper policy. Highest
# precedence, above both config layers.
ENV_GIT_CREDENTIAL_HELPER_VAR = "MULTI_LLM_GIT_CREDENTIAL_HELPER"
#: The model the *host session* is currently running on, as the host's own
#: `provider/model` addressing, exported by a host shim or plugin that can read
#: it. THIS MODULE IS THE OWNER OF THE NAME — the opencode plugin reads it out of
#: the generated `cli-surface.json` rather than spelling it in JavaScript — and
#: the value is a *fact about the session*, never a config layer: it is consulted
#: below any operator opinion (see :func:`resolve_subagent_runner`) and only on a
#: host whose capability entry declares a `session_runner_provider` that can run
#: it. Unset, empty or whitespace-only means "the host did not say", which is the
#: pre-existing behaviour exactly.
HOST_SESSION_MODEL_ENV = "MULTI_LLM_HOST_SESSION_MODEL"

# Stable, greppable prefix for every non-fatal config warning emitted here. Tests
# capsys-assert on this exact prefix; do not vary it per call site. Fail-fast
# raises are errors, not warnings, and do NOT use this prefix.
CONFIG_WARNING_PREFIX = "multi-llm config warning:"

# Provider names already warned about as "no hardcoded adapter" (re-init drift),
# so the read-site filter warns once per name per process instead of every call.
_WARNED_UNKNOWN_PROVIDERS: set = set()


class ConfigError(RuntimeError):
    """An explicitly-provided override config is present but invalid.

    Subclasses ``RuntimeError`` so orchestrators that already wrap model
    resolution in ``except RuntimeError`` surface it as a clean, named
    fail-fast (printing the message and exiting non-zero) instead of an
    unplanned traceback from deep in the YAML parser.
    """
    pass


def _truthy_env(name: str) -> bool:
    """Return True if env var ``name`` is set to a truthy value."""
    val = os.environ.get(name)
    return val is not None and val.strip().lower() in ("1", "true", "yes", "on")


def _deep_merge(base: dict, override: dict) -> dict:
    """Deep-merge ``override`` onto ``base``, returning a new independent dict.

    - Nested dicts recurse; every other type (**including lists**) replaces.
    - An override value of ``None`` is **skipped** (keeps base) so a blank /
      uncommented-but-empty stub key (``models:`` → ``None``) does not blank the
      base. An explicit empty list ``[]`` *does* replace (a deliberate wipe-out).
    - Pure: uses ``copy.deepcopy`` for both the seed and each replaced value so
      the result shares no nested dict/list with either input.
    """
    result = copy.deepcopy(base)
    for k, v in override.items():
        if v is None:                                            # blank → keep base
            continue
        if isinstance(v, dict) and isinstance(result.get(k), dict):
            result[k] = _deep_merge(result[k], v)               # nested dicts merge
        else:
            result[k] = copy.deepcopy(v)                        # lists & scalars replace
    return result


def set_run_anchor(path: Union[str, Path]) -> None:
    """Pin this process's discovery anchor to the run's plan file (§9.3.b).

    Called once per process from each mode's pre-flight, right after
    ``--plan-file`` has been resolved to an absolute path and before any model
    or agent CLI runs. Two invariants keep it safe rather than order-dependent:

    1. **Set once, before the run's decision reads.** The config cache is keyed
       on the resolved anchor, so a value set after a load would leave earlier
       reads on the CWD key and later reads on the anchor key — exactly the
       half-anchored run this exists to forbid. A parser's ``--help`` epilog
       legitimately reads config before a plan path exists, so rather than
       refusing, changing the effective anchor **drops the cached slot**: no
       value read on the CWD key survives into the anchored half of the run.
    2. **Re-setting to a different path raises.** ``full`` runs several modes in
       one interpreter, but always against one plan; a second, different anchor
       means something multi-llm does not model is driving it, and failing
       loudly beats interleaving two configs. Re-setting to the *same* path is a
       no-op (``full``'s per-phase pre-flight does exactly that).

    **Normalization is this function's job, not the call sites'.** The six
    pre-flights hand over what they already had — one ``os.path.realpath``, one
    ``Path(...).resolve()``, one ``os.path.abspath``, and three more that pass
    whichever of those their own path resolution produced. Invariant 2 compares
    *strings*, so under a symlinked plan directory ``abspath`` and ``realpath``
    are two different anchors for one file, and a ``full`` run pinned the link
    spelling at phase 1 and re-pointed it to the real one at phase 5 — raising
    mid-run. Resolving here makes "the same path" mean the same file, which is
    what invariant 2 already means to say; two of the three original pinners
    realpath'd already, so this is the majority behaviour rather than a fourth
    spelling. **The one behaviour consequence:** :func:`_anchor_start_dir`
    starts git and config discovery from the anchor's directory, so a plan
    reached through a symlink now discovers from the real directory — the
    directory ``ask`` and ``code-review`` already anchored at.
    """
    global _RUN_ANCHOR, _config, _config_key
    resolved = os.path.realpath(str(path))
    if _RUN_ANCHOR == resolved:
        return
    if _RUN_ANCHOR is not None:
        raise RuntimeError(
            "multi-llm: the process-wide run anchor is already pinned to "
            f"{_RUN_ANCHOR!r} and cannot be re-pointed at {resolved!r}. One "
            "process runs one plan; two anchors would interleave two configs."
        )
    _RUN_ANCHOR = resolved
    # Invariant 1: nothing loaded on the pre-anchor key may be served afterwards.
    _config = None
    _config_key = None


def get_run_anchor() -> Optional[str]:
    """The pinned run anchor, or None when no pre-flight has set one."""
    return _RUN_ANCHOR


def _anchor_start_dir(anchor: Optional[Union[str, Path]]) -> str:
    """Directory to run git discovery from for an optional discovery anchor.

    ``anchor`` may be a plan-file path or a directory; when omitted, falls back
    to the process-wide run anchor (:func:`set_run_anchor`) and then to CWD. CWD
    is a *fallback*, not a guarantee — see _find_project_config.
    """
    if anchor is None:
        anchor = _RUN_ANCHOR
    if anchor is not None:
        anchor_str = str(anchor)
        if os.path.isdir(anchor_str):
            return anchor_str
        return os.path.dirname(anchor_str) or "."
    return os.getcwd()


def _find_project_config(anchor: Optional[Union[str, Path]] = None) -> Optional[Path]:
    """Locate ``<git-root>/.multi-llm/providers.yaml`` for the discovery anchor.

    Discovery is anchored on ``anchor`` (a plan-file path or repo directory)
    when supplied — matching the orchestrators' ``get_project_root(plan_path)``
    — and on CWD otherwise. The anchor → CWD precedence makes the plan-derived
    root authoritative when available while keeping CWD as a convenience
    fallback. Returns None outside a git repository or when the file is absent.
    """
    root = get_project_root_from_dir(_anchor_start_dir(anchor))
    if not root:
        return None
    candidate = Path(root) / ".multi-llm" / "providers.yaml"
    # exists() follows symlinks, so a broken symlink at the candidate path reads
    # as absent and would be skipped silently. Surface it (it exists *as a link*)
    # so the loader's is_symlink() branch can fail fast on the present-but-invalid
    # override.
    if candidate.exists() or candidate.is_symlink():
        return candidate
    return None


def _resolve_env_path() -> Optional[Path]:
    """Resolve ``MULTI_LLM_PROVIDERS_CONFIG`` to an absolute path (CWD-anchored).

    Relative values are allowed and resolved against CWD (the repo root in real
    runs), **not** the git root — keeping the env var usable from CI without
    computing a repo root. Returns None when the var is unset/empty.
    """
    value = os.environ.get(ENV_CONFIG_VAR)
    if not value:
        return None
    p = Path(value)
    if not p.is_absolute():
        p = Path(os.getcwd()) / p
    # A broken symlink must reach the loader's is_symlink() fail-fast branch, but
    # Path.resolve() collapses it to its non-existent target (no longer a link).
    # Detect the link on the unresolved path and keep it intact so the loader can
    # classify it as present-but-invalid rather than silently absent.
    if os.path.islink(p):
        return p
    return p.resolve()


def _override_paths(anchor: Optional[Union[str, Path]] = None) -> List[Tuple[str, Path]]:
    """Override config layers, lowest→highest precedence: ``[project, env]``.

    Each entry is ``(layer_name, path)``. The project-local path is included
    when it exists *or is a broken symlink*; the env path is included whenever
    the var is set (its existence is validated by the loader so a set-but-missing
    target can warn-and-skip rather than fail fast, while a broken symlink in
    either layer reaches the loader's fail-fast branch).
    """
    paths: List[Tuple[str, Path]] = []
    project = _find_project_config(anchor)
    if project is not None:
        paths.append(("project", project))
    env_path = _resolve_env_path()
    if env_path is not None:
        paths.append(("env", env_path))
    return paths


def _cache_key(anchor: Optional[Union[str, Path]], permissive: bool) -> tuple:
    """Cache key identifying the discovery context (anchor dir + relevant env).

    ``permissive`` is the *effective* (resolved) flag, not just the env var: a
    permissive load that warn-and-skips a broken override must not be served to a
    later strict call with the same anchor/env, which would bypass fail-fast.
    """
    return (
        os.path.abspath(_anchor_start_dir(anchor)),
        os.environ.get(ENV_CONFIG_VAR, ""),
        os.environ.get(ENV_PERMISSIVE_VAR, ""),
        permissive,
    )


def _load_base_config() -> dict:
    """Load and parse the built-in base ``providers.yaml`` (strict).

    Raises FileNotFoundError if the base is missing (matches prior behavior).
    """
    config_path = Path(__file__).parent.parent / "providers.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"providers.yaml not found at {config_path}")
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


def _load_override_layer(layer_name: str, path: Path, permissive: bool) -> Optional[dict]:
    """Load + validate one override layer; return a mapping to merge or None.

    Distinguishes **absent** (optional → skip) from **present-but-invalid** (the
    user asked for this override → fail fast in strict mode, raising
    :class:`ConfigError` that names the offending file). The opt-in permissive
    mode restores warn-and-skip. The base layer is loaded elsewhere and stays
    strict regardless.
    """
    is_env = layer_name == "env"

    if not path.exists():
        # A broken symlink exists *as a link* → present-invalid (fail fast).
        if path.is_symlink():
            msg = f"override config is a broken symlink: {path}"
            if permissive:
                print(f"{CONFIG_WARNING_PREFIX} {msg} — skipping", file=sys.stderr)
                return None
            raise ConfigError(f"multi-llm config error: {msg}")
        # Truly absent. The env layer warns on a set-but-missing target; the
        # project layer never reaches here (only returned when it exists).
        if is_env:
            print(
                f"{CONFIG_WARNING_PREFIX} {ENV_CONFIG_VAR} points at a missing file: "
                f"{path} — skipping",
                file=sys.stderr,
            )
        return None

    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        if permissive:
            print(
                f"{CONFIG_WARNING_PREFIX} ignoring malformed YAML in override config: "
                f"{path} ({e})",
                file=sys.stderr,
            )
            return None
        raise ConfigError(
            f"multi-llm config error: malformed YAML in override config: {path} ({e})"
        ) from e
    except OSError as e:
        # Covers IsADirectoryError / PermissionError / a file that vanished after
        # the existence check — present-invalid → fail fast (unless permissive).
        if permissive:
            print(
                f"{CONFIG_WARNING_PREFIX} ignoring unreadable override config: "
                f"{path} ({e})",
                file=sys.stderr,
            )
            return None
        raise ConfigError(
            f"multi-llm config error: could not read override config: {path} ({e})"
        ) from e

    if data is None:
        # Empty / all-comments file → no-op merge.
        return None

    if not isinstance(data, dict):
        if permissive:
            print(
                f"{CONFIG_WARNING_PREFIX} ignoring non-mapping root in override config: "
                f"{path} — skipping",
                file=sys.stderr,
            )
            return None
        raise ConfigError(
            f"multi-llm config error: override config must contain a top-level "
            f"mapping, got {type(data).__name__}: {path}"
        )

    # Trust model: BOTH override layers deep-merge their full contents (including a
    # `providers:` block) over base, identically. The residual surface is
    # availability-only metadata (timeouts/concurrency/model lists) — `command`/argv
    # is NEVER honored from config in any layer (provider binaries stay hardcoded in
    # their provider classes; `command` here is documentation-only), an unknown
    # provider name has no adapter and is ignored at runtime, and a non-mapping
    # provider value is dropped by the load-time guard in load_config. Any future
    # change that feeds config into command construction MUST revisit this.
    #
    # Revisited 2026-09-17, one key: `providers.codex.sandbox_fallback` changes
    # the *value* in codex's own `--sandbox` slot (never the binary, never a new
    # flag) to `danger-full-access`, and only after the D6 probe said the sandbox
    # cannot start, only for the two read-only profiles. Its default is `auto` —
    # the fallback is on unless a layer writes `off` — so what the project layer
    # can do with it is *restrict*: a cloned repository's `.multi-llm/providers.yaml`
    # can only turn the fallback off (its codex slot is then refused on a machine
    # whose bubblewrap cannot start, exactly the pre-D6 behaviour), never widen
    # anything beyond what a fresh install already does. That is why it sits
    # beside `driver.verify_command` — the key that really does run a shell
    # string from that layer — without changing the trust posture: on the hosts
    # this exists for, four of five reviewers run with the operator's shell
    # rights anyway (muse always `--disable-sandbox`, pi/cursor-agent/claude-code
    # never had one). `docs/configuration.md` §Safety names both keys.
    return data


def load_base_config() -> dict:
    """Public accessor for the built-in base ``providers.yaml`` (no overrides).

    Used by ``--init`` so the interactive flow reflects the plugin's canonical
    catalog (curated models, provider metadata, declaration order) independent of
    any project-local override or ``MULTI_LLM_PROVIDERS_CONFIG`` that may have
    altered the merged runtime view from :func:`load_config`.
    """
    return _load_base_config()


def load_config(anchor: Optional[Union[str, Path]] = None,
                permissive: Optional[bool] = None) -> dict:
    """Load layered providers configuration (base → project-local → env).

    Args:
        anchor: Optional plan-file path or target-repo directory. When supplied,
            project-local discovery resolves the git root from it (matching the
            orchestrators' plan-derived root); when omitted, falls back to CWD.
        permissive: When True, restores warn-and-skip on a present-but-invalid
            override instead of failing fast. Defaults to the
            ``MULTI_LLM_PROVIDERS_CONFIG_PERMISSIVE`` env var (strict otherwise).

    Returns:
        The merged config dict. Cached per resolved anchor/env within a process.
    """
    global _config, _config_key
    # Resolve the effective permissive flag *before* the cache lookup so it is
    # part of the key — otherwise a prior permissive load that degraded past a
    # broken override could be served to a later strict call, bypassing
    # fail-fast.
    if permissive is None:
        permissive = _truthy_env(ENV_PERMISSIVE_VAR)

    key = _cache_key(anchor, permissive)
    if _config is not None and _config_key == key:
        return _config

    base_config = _load_base_config()
    config = base_config
    driver_overridden = False
    git_env_overridden = False
    progress_overridden = False
    code_review_overridden = False
    for layer_name, path in _override_paths(anchor):
        data = _load_override_layer(layer_name, path, permissive)
        if data:
            if "driver" in data:
                driver_overridden = True
            if "progress" in data:
                progress_overridden = True
            if "code_review" in data:
                code_review_overridden = True
            layer_providers = data.get("providers")
            if "git_env" in data or (
                isinstance(layer_providers, dict)
                and any(
                    isinstance(entry, dict) and "git_env" in entry
                    for entry in layer_providers.values()
                )
            ):
                git_env_overridden = True
            config = _deep_merge(config, data)

    # D3: `driver:` validation is fail-fast, and only for an EXPLICIT override.
    # Base is ours (a broken base is a test failure, not a user's problem), and
    # validating it here would turn every unrelated invocation into a config
    # error. An override layer asked for these values, so a bad one raises
    # ConfigError naming the key, the value and the reason at load time rather
    # than surfacing as a mis-dispatched subagent mid-phase. Permissive mode
    # deliberately does NOT relax this: a silently ignored runner spec degrades
    # to "no runner configured", which is the failure this check exists for.
    if driver_overridden:
        validate_driver_block(config.get("driver"))

    # `progress:` follows `driver:`'s rule exactly, and for `driver:`'s reason: a
    # cadence that was silently dropped degrades to the shipped default, which is
    # indistinguishable from the user's setting having worked — the failure the
    # closed key set exists to catch — so permissive mode does not relax it
    # either. Validated HERE rather than lazily inside the accessors because
    # `interval_s` is first read at fan-out start (a ConfigError raised there
    # kills a run that has already launched eight models) and `poll_s` is first
    # read inside `status --wait`, i.e. in the agent's poll loop rather than at
    # the command the user typed.
    if progress_overridden:
        validate_progress_block(config.get("progress"))

    # `code_review:` follows the same rule, for the same reason: a collapse
    # glob list that was silently dropped degrades to the shipped rule, which
    # reads exactly like the repository's setting having worked — while the
    # review reads the `poetry.lock` diff the user meant to collapse
    # (decision 11.5 of the review-scope plan: a malformed key is a config
    # error at load time, never a silent fallback).
    if code_review_overridden:
        validate_code_review_block(config.get("code_review"))

    # §2.2: `git_env:` follows the identical rule — validated only when an
    # override layer asked for it, rejected rather than ignored, because
    # `credential_helper: keeep` silently meaning `auto` would restore the hang
    # the key exists to switch off and look like it had worked.
    if git_env_overridden:
        validate_git_env_block(config.get("git_env"), "git_env")
        merged_providers = config.get("providers")
        if isinstance(merged_providers, dict):
            for name, entry in merged_providers.items():
                if isinstance(entry, dict) and "git_env" in entry:
                    validate_git_env_block(
                        entry.get("git_env"), f"providers.{name}.git_env"
                    )

    # Load-time guard (post-merge): a clone-authored override can deep-merge a
    # malformed (non-mapping) provider value, e.g. `providers: {claude-code: "x"}`,
    # which REPLACES the base mapping during deep-merge and would later
    # AttributeError on `.get(...)`. Sanitize each such entry so the rest of the
    # config still loads and the residual stays availability-only: for a KNOWN base
    # provider, RESTORE its base mapping — the malformed scalar must not erase the
    # built-in catalog/metadata for the whole repo; for an unknown name (nothing to
    # inherit) drop it. ``base_config`` is the untouched base load (deep-merge seeds
    # from a deepcopy, so it is never mutated), giving the pristine entry to restore.
    base_providers = base_config.get("providers")
    base_providers = base_providers if isinstance(base_providers, dict) else {}
    providers = config.get("providers")
    if isinstance(providers, dict):
        for name in [k for k, v in providers.items() if not isinstance(v, dict)]:
            base_entry = base_providers.get(name)
            restore = isinstance(base_entry, dict)
            print(
                f"{CONFIG_WARNING_PREFIX} ignoring malformed provider '{name}' in "
                f"merged config (expected a mapping, got "
                f"{type(providers[name]).__name__}) — "
                f"{'restoring base definition' if restore else 'dropping it'}",
                file=sys.stderr,
            )
            if restore:
                providers[name] = copy.deepcopy(base_entry)
            else:
                del providers[name]

    _config = config
    _config_key = key
    return config


def get_provider(name: str) -> Optional[LLMProvider]:
    """Get a provider by name."""
    return _PROVIDERS.get(name)


def parse_model_spec(spec: str, anchor: Optional[Union[str, Path]] = None) -> Tuple[str, str]:
    """Parse 'provider:model' format.

    Returns (provider_name, model_name).
    If no provider prefix, uses default_provider from config.
    """
    if ":" in spec:
        provider, model = spec.split(":", 1)
        return provider, model

    config = load_config(anchor=anchor)
    default = config.get("default_provider", "cursor-agent")
    return default, spec


def _provider_has_adapter(provider_name: str) -> bool:
    """Read-site drift filter: True iff ``provider_name`` has a hardcoded adapter.

    A config (e.g. one an OLDER plugin ``--init`` wrote, or a stale clone) can carry
    a ``providers:`` block or a ``defaults.*`` spec for a name the current base
    removed/renamed — one with no hardcoded adapter. Such a name merges but can never
    run (``get_provider`` returns None), so it MUST NOT be surfaced as a usable model
    source NOR validate as an explicitly-configured spec. Returns False (and warns
    once per name per process via ``_WARNED_UNKNOWN_PROVIDERS``) for such names, so
    BOTH read sites — :func:`get_available_models` and :func:`_collect_configured_specs`
    — filter them identically.
    """
    if get_provider(provider_name) is not None:
        return True
    if provider_name not in _WARNED_UNKNOWN_PROVIDERS:
        _WARNED_UNKNOWN_PROVIDERS.add(provider_name)
        print(
            f"{CONFIG_WARNING_PREFIX} provider '{provider_name}' in your "
            f"config is no longer supported — re-init to refresh",
            file=sys.stderr,
        )
    return False


def get_available_models(anchor: Optional[Union[str, Path]] = None) -> Dict[str, List[str]]:
    """Get all available models grouped by provider.

    Args:
        anchor: Optional discovery anchor (plan path / repo dir) threaded to
                load_config for plan-derived project-local discovery.
    """
    config = load_config(anchor=anchor)
    result = {}
    for provider_name, provider_config in config.get("providers", {}).items():
        # Skip a merged provider name with no hardcoded adapter (warn once) so it
        # contributes no models — see _provider_has_adapter for the rationale.
        if not _provider_has_adapter(provider_name):
            continue
        result[provider_name] = provider_config.get("models", [])
    return result


def get_all_model_specs(anchor: Optional[Union[str, Path]] = None) -> List[str]:
    """Get all models as provider:model specs for interactive selection.

    Args:
        anchor: Optional discovery anchor (plan path / repo dir) threaded to
                get_available_models. This list is what the "available models" /
                "unknown model" messages echo, and validation is already
                anchored (``is_model_valid(..., anchor=plan)``) — an anchored
                rejection paired with a CWD-discovered suggestion list is its own
                user-visible bug (§9.3.c).
    """
    models_by_provider = get_available_models(anchor=anchor)
    specs = []
    for provider, models in models_by_provider.items():
        for model in models:
            specs.append(f"{provider}:{model}")
    return specs


def get_provider_timeout(provider_name: str,
                         anchor: Optional[Union[str, Path]] = None) -> int:
    """Get timeout for a specific provider.

    Args:
        anchor: Optional discovery anchor (plan path / repo dir) threaded to
                load_config, so a project-local ``default_timeout`` still binds
                when the run starts outside that project (§9.3.c).
    """
    config = load_config(anchor=anchor)
    providers = config.get("providers", {})
    if provider_name in providers:
        return providers[provider_name].get("default_timeout", 1200)
    # Fallback to provider's built-in default
    provider = get_provider(provider_name)
    return provider.default_timeout if provider else 1200


# ---------------------------------------------------------------------------
# progress: — the two feedback cadences, read the same anchored way
# ---------------------------------------------------------------------------
# The typed reads sit beside `get_provider_timeout` because they answer the same
# question shape ("how long / how often, for THIS run"), but `progress:` is a
# TOP-LEVEL block, not a per-provider one: `get_provider_timeout` indexes
# `config["providers"][name]`, and copying that literally is the wrong shape. The
# block's closed key set, its fallbacks and its validator live with the other
# top-level blocks further down — search `PROGRESS_KEYS`.


def _progress_seconds(key: str, anchor: Optional[Union[str, Path]]) -> float:
    """The one read path both accessors share: merged ``progress.<key>``, seconds.

    The fallback covers exactly one case — a merged config carrying no
    ``progress:`` block at all (a test fixture, or a base predating the block),
    mirroring :data:`DRIVER_FALLBACKS`. A key that IS present is returned as
    written rather than re-checked: :func:`validate_progress_block` already ran
    at load time on every override layer that named one, so a value reaching here
    is either the shipped base's or one that passed the closed-set check.
    """
    progress = load_config(anchor=anchor).get("progress")
    if not isinstance(progress, dict) or key not in progress:
        return PROGRESS_FALLBACKS[key]
    return float(progress[key])


def get_progress_interval(anchor: Optional[Union[str, Path]] = None) -> float:
    """``progress.interval_s`` — the ``[PROGRESS]`` ticker cadence, in seconds.

    A stdout cadence, not a write cadence: it governs the ticker lines and
    nothing else. ``0.0`` is the documented disable form — the lines stop, the
    status file still records every event-driven transition, and ``--wait`` is
    unaffected (turning the ticker off cannot turn a poll into an instant
    return).

    Args:
        anchor: Discovery anchor (plan path / repo dir) threaded to
            :func:`load_config`, so a run started from a foreign CWD still
            resolves the *project's* cadence rather than the CWD's (§9.3.c — the
            bug :func:`get_provider_timeout`'s own docstring names). Never read
            as ``config["progress"]["interval_s"]`` at a call site: a layer that
            omitted the key would KeyError, and an unanchored read is the §9.3.c
            defect by construction.
    """
    return _progress_seconds("interval_s", anchor)


def get_progress_poll(anchor: Optional[Union[str, Path]] = None) -> float:
    """``progress.poll_s`` — the host poll cadence, in seconds.

    The resolved ``--wait`` default (an explicit ``--timeout`` wins over it), and
    a value the caller still clamps under the host's shell cap. Unlike the ticker
    it has no disable form: ``0`` is rejected at load, because a poll of zero
    means one that returns instantly, not one that is switched off.

    Args:
        anchor: as :func:`get_progress_interval`.
    """
    return _progress_seconds("poll_s", anchor)


def _collect_configured_specs(anchor: Optional[Union[str, Path]] = None) -> set:
    """Canonical set of provider:model specs the user explicitly configured.

    Walks the merged defaults.models + defaults.quick_models + every
    defaults.modes.<mode> entry (both the bare-list shape and the
    {"models": [...], "quick": [...]} dict shape), then canonicalizes each raw
    entry through parse_model_spec so a bare (prefix-less) id resolves against the
    same anchor-aware default_provider and compares equal to a resolved warned spec.

    Specs whose provider has **no hardcoded adapter** (a stale clone naming a
    removed/renamed provider) are filtered out via ``_provider_has_adapter`` — the
    same read-site drift filter ``get_available_models`` applies — so an orphan spec
    in ``defaults.*`` is NOT treated as "explicitly configured" and a model that
    cannot run is never validated.
    """
    config = load_config(anchor=anchor)
    defaults = config.get("defaults", {}) or {}
    raw: List[str] = []
    raw += defaults.get("models", []) or []
    raw += defaults.get("quick_models", []) or []
    for mode_val in (defaults.get("modes", {}) or {}).values():
        if isinstance(mode_val, dict):            # {models, quick} shape
            raw += mode_val.get("models", []) or []
            raw += mode_val.get("quick", []) or []
        elif isinstance(mode_val, list):          # bare-list shape
            raw += mode_val
        # any other shape (str/None/etc.) is ignored, not exploded
    canon = set()
    for spec in raw:
        if not isinstance(spec, str) or not spec.strip():
            continue
        provider, model = parse_model_spec(spec, anchor=anchor)
        if not _provider_has_adapter(provider):       # orphan provider → filter out
            continue
        canon.add(f"{provider}:{model}")
    return canon


def is_model_valid(spec: str, anchor: Optional[Union[str, Path]] = None, *,
                   configured: Optional[set] = None) -> bool:
    """Check if a model spec is valid (exists in config).

    A spec is valid if either (a) the user explicitly configured it in
    ``defaults.*`` — so a model deliberately placed in the config is honoured even
    when it is absent from the provider catalog (suppressing the spurious "unknown
    model" warning) — or (b) it exists in the provider catalog.

    Args:
        spec: Model spec ('provider:model' or a bare, prefix-less model name).
        anchor: Optional discovery anchor (plan path / repo dir) threaded to
                parse_model_spec/get_available_models so a bare spec resolves its
                default_provider against the plan-derived project-local config
                rather than the CWD-anchored one.
        configured: Optional override of the canonical configured set (used by
                tests / explicit injection). When ``None``, the set is built
                internally from the merged ``defaults.*`` via
                ``_collect_configured_specs``.

    The spec is canonicalized through ``parse_model_spec`` *before* the membership
    test so a bare spec compares canonically against the canonical configured set.
    A spec whose provider has **no hardcoded adapter** (a removed/renamed key or a
    typo) is filtered out of the configured set by ``_collect_configured_specs``
    (warning once), so even an orphan spec written into ``defaults.*`` does NOT
    validate as "explicitly configured"; the catalog-membership path likewise skips
    it, so a model that cannot run is rejected rather than accepted on a stale config.
    """
    if configured is None:
        configured = _collect_configured_specs(anchor=anchor)
    provider_name, model = parse_model_spec(spec, anchor=anchor)
    if f"{provider_name}:{model}" in configured:   # canonical provider:model
        return True
    models_by_provider = get_available_models(anchor=anchor)
    if provider_name not in models_by_provider:
        return False
    return model in models_by_provider[provider_name]


def get_default_models(mode: Optional[str] = None,
                       anchor: Optional[Union[str, Path]] = None) -> List[str]:
    """Get default models from config.

    Args:
        mode: Optional mode name (e.g., 'review-plan', 'code-review')
              to get mode-specific defaults.
        anchor: Optional discovery anchor (plan path / repo dir) threaded to
                load_config for plan-derived project-local discovery.

    Returns:
        List of model specs, or empty list if no defaults configured.
    """
    config = load_config(anchor=anchor)
    defaults = config.get("defaults", {})

    # Check for mode-specific defaults first. Test for the mode KEY's presence
    # (not truthiness): an explicit empty list `defaults.modes.<mode>: []` is a
    # deliberate clear of that mode entry and must return [] rather than falling
    # through to defaults.models (which would re-select models the project tried
    # to disable). A missing key still falls back to the global defaults.
    modes = defaults.get("modes", {})
    if mode and mode in modes:
        mode_defaults = modes[mode]
        # Support dict format with 'models' key
        if isinstance(mode_defaults, dict):
            return mode_defaults.get("models", [])
        return mode_defaults

    # Fall back to global defaults
    return defaults.get("models", [])


def has_default_models(mode: Optional[str] = None,
                       anchor: Optional[Union[str, Path]] = None) -> bool:
    """Check if default models are configured."""
    return len(get_default_models(mode, anchor=anchor)) > 0


def get_quick_models(mode: Optional[str] = None,
                     anchor: Optional[Union[str, Path]] = None) -> List[str]:
    """Get quick models from config.

    Args:
        mode: Optional mode name (e.g., 'review-plan', 'code-review')
              to get mode-specific quick models.
        anchor: Optional discovery anchor (plan path / repo dir) threaded to
                load_config for plan-derived project-local discovery.

    Returns:
        List of model specs, or empty list if no quick_models configured.
    """
    config = load_config(anchor=anchor)
    defaults = config.get("defaults", {})

    # Check for mode-specific quick models first
    if mode:
        mode_defaults = defaults.get("modes", {}).get(mode)
        if isinstance(mode_defaults, dict) and "quick" in mode_defaults:
            return mode_defaults["quick"]

    # Fall back to global quick_models
    return defaults.get("quick_models", [])


def has_quick_models(mode: Optional[str] = None,
                     anchor: Optional[Union[str, Path]] = None) -> bool:
    """Check if quick models are configured."""
    return len(get_quick_models(mode, anchor=anchor)) > 0


# ---------------------------------------------------------------------------
# driver: — the `--exec-subagents` dispatch config (D3, D3o)
# ---------------------------------------------------------------------------

#: The base `driver:` block's keys, with the types each accepts. This is the
#: closed set: an unknown key under `driver:` is REJECTED rather than ignored, so
#: a typo (`subagent_runners:`) is not silently a no-op.
DRIVER_RUNNER_KEYS = ("subagent_runner", "subagent_runner_cheap")
DRIVER_POSITIVE_INT_KEYS = (
    "max_concurrent_subagents",
    # D3h: write phases get their OWN ceiling, defaulting to 1, because the
    # batchers' partitioning invariant (one shared artifact per apply phase, one
    # file per code-fix batch) is not the read path's fan-out. Raising it only
    # *permits* parallelism; the dispatch-time disjointness check still admits it.
    "max_concurrent_write_subagents",
    "subagent_retries",
    "verify_timeout_s",
)
DRIVER_OPTIONAL_INT_KEYS = ("subagent_timeout_s",)
#: F4: the repository's OWN post-write check, run once by the write scheduler
#: after a code-editing phase applied at least one batch. Optional because no
#: command is right for every repo — and because "unset" has to be distinguishable
#: from "not run", which is why the scheduler says so out loud rather than
#: skipping silently. `verify_timeout_s` is a positive int with a real default
#: (600 s) rather than an optional one: there is no provider default to inherit.
DRIVER_OPTIONAL_STR_KEYS = ("verify_command",)
#: D3l: `allow`/`deny` glob lists resolved against the pinned repo root, enforced
#: pre-dispatch (against the batch's declared file set) and post-run (against the
#: set the snapshot diff actually observed).
DRIVER_PATH_POLICY_KEYS = ("write_paths",)
DRIVER_KEYS = (
    DRIVER_RUNNER_KEYS
    + DRIVER_POSITIVE_INT_KEYS
    + DRIVER_OPTIONAL_INT_KEYS
    + DRIVER_OPTIONAL_STR_KEYS
    + DRIVER_PATH_POLICY_KEYS
)

#: The shipped write policy (D3l). `allow` is the repository; `deny` is what a
#: code-editing batch has no business touching. `.multi-llm/**` is denied to the
#: RUNNER precisely because the EXECUTOR owns those bytes — orchestrator state,
#: task files, snapshots, audit records and reports are written by the invoker
#: under D3f containment, never by a subagent.
DEFAULT_WRITE_PATHS: Dict[str, List[str]] = {
    "allow": ["**"],
    "deny": [
        ".git/**",
        ".multi-llm/**",
        "**/.env",
        "**/.env.*",
        "**/*.pem",
        "**/id_rsa*",
        "**/.ssh/**",
        "**/.aws/**",
        "**/.npmrc",
        "**/node_modules/**",
    ],
}

#: Values used when the merged config carries no `driver:` block at all (a test
#: fixture config, or a base file predating D3). The shipped base is fully
#: populated, so in a real run these are never reached.
DRIVER_FALLBACKS: Dict[str, object] = {
    "subagent_runner": "claude-code:sonnet",
    "subagent_runner_cheap": "claude-code:haiku",
    "max_concurrent_subagents": 4,
    "max_concurrent_write_subagents": 1,
    "subagent_timeout_s": None,
    "subagent_retries": 1,
    "verify_command": None,
    "verify_timeout_s": 600,
    "write_paths": DEFAULT_WRITE_PATHS,
}


def _driver_runner_error(key: str, value: object, reason: str) -> str:
    """One rejection surface for a bad `driver.*` runner spec (D3)."""
    return (
        f"multi-llm config error: driver.{key} is {value!r} — {reason}. "
        f"Set it to a provider:model spec whose provider has a built-in adapter "
        f"(e.g. claude-code:sonnet, codex:gpt-5.6-sol, opencode:<model>), or "
        f"remove the key to inherit the default."
    )


def validate_driver_block(driver: object) -> None:
    """Validate a merged ``driver:`` block, raising :class:`ConfigError`.

    Fail-fast and total: every field is checked, unknown keys are rejected, and
    each message names the key, the value and the reason. Called from
    :func:`load_config` whenever an **override** layer carried a ``driver:``
    block, so a bad value surfaces at load time rather than as a mis-dispatched
    subagent mid-phase.

    A runner spec is checked structurally here (parses as ``provider:model``, and
    that provider has a hardcoded adapter). Catalog membership
    (:func:`is_model_valid`) and the profile check (D3e) happen at resolution
    time, because both read the merged config this function is validating.
    """
    if driver is None:
        return
    if not isinstance(driver, dict):
        raise ConfigError(
            f"multi-llm config error: `driver:` must be a mapping, got "
            f"{type(driver).__name__}"
        )

    unknown = [key for key in driver if key not in DRIVER_KEYS]
    if unknown:
        raise ConfigError(
            f"multi-llm config error: unknown key(s) under `driver:`: "
            f"{', '.join(sorted(unknown))}. Known keys: "
            f"{', '.join(DRIVER_KEYS)}. A typo here would otherwise be a silent "
            f"no-op, so it is rejected instead of ignored."
        )

    for key in DRIVER_RUNNER_KEYS:
        if key not in driver:
            continue
        value = driver[key]
        if not isinstance(value, str) or not value.strip():
            raise ConfigError(_driver_runner_error(key, value, "expected a non-empty string"))
        provider_name, _, model = value.partition(":")
        if not provider_name.strip() or not model.strip():
            raise ConfigError(_driver_runner_error(
                key, value,
                "it must be an explicit provider:model spec (a bare model name "
                "cannot be resolved for a runner)",
            ))
        # Canonical spelling is part of the check, because dispatch-time
        # `parse_model_spec` does NOT strip: a spec like "codex :gpt-5" would
        # pass a stripped lookup here and then be rejected at preflight as
        # unknown_provider — exactly the mid-phase surprise load-time
        # validation exists to prevent.
        canonical = f"{provider_name.strip()}:{model.strip()}"
        if value != canonical:
            raise ConfigError(_driver_runner_error(
                key, value,
                f"it carries whitespace around the provider:model spec, which "
                f"dispatch does not strip (the same value is later rejected as "
                f"unknown_provider) — write it as {canonical!r}",
            ))
        # Deliberately NOT warn-and-filter: a filtered runner spec silently
        # degrades to "no runner configured" and resurfaces mid-phase, so the
        # driver validator raises where the fan-out path warns. The fan-out
        # behavior (_provider_has_adapter's warn-once) is untouched.
        if get_provider(provider_name) is None:
            raise ConfigError(_driver_runner_error(
                key, value,
                f"provider {provider_name!r} has no built-in adapter "
                f"(reason code: unknown_provider) — run --init to refresh a "
                f"stale config",
            ))

    for key in DRIVER_POSITIVE_INT_KEYS:
        if key not in driver:
            continue
        value = driver[key]
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ConfigError(
                f"multi-llm config error: driver.{key} is {value!r} — expected a "
                f"positive integer."
            )

    for key in DRIVER_OPTIONAL_INT_KEYS:
        if key not in driver:
            continue
        value = driver[key]
        if value is None:
            continue
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ConfigError(
                f"multi-llm config error: driver.{key} is {value!r} — expected a "
                f"positive integer or null (null = the runner provider's "
                f"default_timeout)."
            )

    for key in DRIVER_OPTIONAL_STR_KEYS:
        if key not in driver:
            continue
        value = driver[key]
        if value is None:
            continue
        if not isinstance(value, str) or not value.strip():
            raise ConfigError(
                f"multi-llm config error: driver.{key} is {value!r} — expected a "
                f"non-empty shell command string (e.g. \"pnpm typecheck && pnpm "
                f"lint\"), or null/omitted to declare no command. A blank string "
                f"would run the shell for nothing and report a pass."
            )

    for key in DRIVER_PATH_POLICY_KEYS:
        if key not in driver:
            continue
        _validate_path_policy(key, driver[key])


def _validate_path_policy(key: str, value: object) -> None:
    """Validate one ``allow``/``deny`` glob-list policy block (D3l).

    Fail-fast for the same reason a bad runner spec is: a policy that silently
    parsed as "no rules" would be indistinguishable from a policy that allows
    everything, and the difference is whether a headless write run is contained.
    """
    if value is None:
        return
    if not isinstance(value, dict):
        raise ConfigError(
            f"multi-llm config error: driver.{key} is {value!r} — expected a "
            f"mapping with `allow:` and/or `deny:` glob lists."
        )
    unknown = [name for name in value if name not in ("allow", "deny")]
    if unknown:
        raise ConfigError(
            f"multi-llm config error: unknown key(s) under driver.{key}: "
            f"{', '.join(sorted(str(u) for u in unknown))}. Known keys: allow, deny."
        )
    for name in ("allow", "deny"):
        if name not in value or value[name] is None:
            continue
        patterns = value[name]
        if not isinstance(patterns, list) or not all(
            isinstance(item, str) and item.strip() for item in patterns
        ):
            raise ConfigError(
                f"multi-llm config error: driver.{key}.{name} is {patterns!r} — "
                f"expected a list of non-empty glob strings (e.g. "
                f'["src/**", "docs/*.md"]).'
            )
        for pattern in patterns:
            _validate_path_glob(key, name, pattern)


def _validate_path_glob(key: str, name: str, pattern: str) -> None:
    """Reject a non-relative ``write_paths`` entry at load time (D3).

    The policy is matched against **repo-relative POSIX paths** resolved under
    the pinned repo root, so an absolute entry — the natural way to restate the
    shipped deny set by hand (``/home/me/repo/.git/**``) — matches nothing and
    silently leaves the user with no protection at all. A ``..`` segment cannot
    name anything under the pinned root for the same reason. Both are rejected
    here rather than at match time, where the failure is invisible.
    """
    normalized = pattern.strip().replace("\\", "/")
    drive_prefixed = (
        len(normalized) >= 2 and normalized[1] == ":" and normalized[0].isalpha()
    )
    if normalized.startswith("/"):
        reason = "an absolute path"
    elif drive_prefixed:
        reason = "a drive-prefixed absolute path"
    elif ".." in normalized.split("/"):
        reason = "a parent-traversal ('..') path"
    else:
        return
    raise ConfigError(
        f"multi-llm config error: driver.{key}.{name} entry {pattern!r} is "
        f"{reason} — entries are matched against repo-relative POSIX paths "
        f"under the pinned repo root, so it can never match and the rule would "
        f"silently be no rule at all. Write it relative to the repo root (e.g. "
        f'".git/**", "**/.env").'
    )


def get_driver_config(anchor: Optional[Union[str, Path]] = None) -> dict:
    """The merged ``driver:`` block, with every key present (D3).

    Reads go through this and the typed accessors below — never ad-hoc
    ``config["driver"]`` indexing — so a config layer that omitted a key still
    yields a complete block.
    """
    config = load_config(anchor=anchor)
    driver = config.get("driver")
    driver = dict(driver) if isinstance(driver, dict) else {}
    merged = dict(DRIVER_FALLBACKS)
    for key in DRIVER_KEYS:
        if key in driver and driver[key] is not None:
            merged[key] = driver[key]
        elif key in driver and key in DRIVER_OPTIONAL_INT_KEYS:
            merged[key] = None
    return merged


def get_driver_provenance(
    key: str, anchor: Optional[Union[str, Path]] = None
) -> str:
    """Which layer supplied ``driver.<key>``: ``env``/``project``/``base``/``default``.

    D3o: `--status` and `install-host --check` print the resolved runner together
    with the layer that supplied it, because "I set it and nothing changed" is
    otherwise a support question. Highest-precedence layer that names the key
    wins, matching the merge order exactly.
    """
    permissive = _truthy_env(ENV_PERMISSIVE_VAR)
    for layer_name, path in reversed(_override_paths(anchor)):
        data = _load_override_layer(layer_name, path, permissive)
        driver = (data or {}).get("driver")
        if isinstance(driver, dict) and driver.get(key) is not None:
            return layer_name
    base_driver = _load_base_config().get("driver")
    if isinstance(base_driver, dict) and key in base_driver:
        return "base"
    return "default"


#: The override layers that count as an operator *opinion* about a ``driver.*``
#: value (D3o). ``base`` and :data:`DRIVER_FALLBACKS` are ours, not the user's, so
#: they must never outrank the running host's own declared default: a fully
#: populated base would otherwise shadow every host entry and put `claude` back on
#: the hard-prerequisite list for a zero-config Codex or OpenCode install.
#:
#: :data:`SESSION_LAYER` is deliberately **not** here either, for the mirror
#: reason: the session's own model is something the operator selected rather than
#: something they configured, so it must lose to a real ``driver.*`` value and win
#: against a shipped floor.
EXPLICIT_DRIVER_LAYERS: Tuple[str, ...] = ("env", "project")


def _host_capabilities():
    """The capability reader, imported lazily and never fatally.

    Deferred rather than imported at module scope because ``host_capabilities``
    imports ``cli_common`` (which imports this module's siblings) and because most
    invocations never need the yaml parse at all.
    """
    try:
        from . import host_capabilities
    except ImportError:  # pragma: no cover - partial install / direct script run
        try:
            import host_capabilities  # type: ignore
        except ImportError:
            return None
    return host_capabilities


def _host_entry(host_id: Optional[str] = None) -> Optional[dict]:
    """The running host's capability entry, or ``None`` whenever it cannot answer.

    Never fatal and never a guess: an unreadable document, a partial install or
    an unknown id all degrade to ``None`` so the ladder falls through to the next
    rung rather than failing a dispatch on capability data.
    """
    caps = _host_capabilities()
    if caps is None:
        return None
    try:
        if not host_id:
            # The shim bakes `--host <id>` into the command line; there is no
            # in-process channel carrying it down to config resolution, so the
            # declaration is read back off argv exactly as the dispatcher reads it.
            host_id = caps.resolve_host_id(sys.argv[1:])
        return caps.entry(host_id)
    except Exception:  # pragma: no cover - unknown host / unreadable data
        return None


def host_default_runner(
    tier: str = "full", host_id: Optional[str] = None
) -> Optional[str]:
    """The running host's own ``default_subagent_runner``, when its CLI is there.

    The middle rung of D3o's ladder — explicit ``MULTI_LLM_PROVIDERS_CONFIG`` →
    explicit ``<git-root>/.multi-llm/providers.yaml`` → **this** → base
    ``claude-code:sonnet``. Without it the fully-populated base shadows every
    host's own default and a zero-config Codex or OpenCode install dispatches
    Claude Code, reintroducing the extra CLI, login and billing prerequisite the
    capability records exist to remove.

    It is *not* a fourth config layer: it is consulted only when no override layer
    expressed an opinion, so user config still always wins. Selection is gated on
    the runner's CLI being detected (D3c) — an undetected same-host CLI falls
    through to base rather than turning a zero-config run into a refusal — and the
    host id is *declared* (``--host`` on this invocation's argv, else
    ``$MULTI_LLM_HOST``, else the reference host), never sniffed. Returns ``None``
    whenever the data cannot answer, so a partial install degrades to base instead
    of failing a dispatch.
    """
    entry = _host_entry(host_id)
    if entry is None:
        return None

    spec = entry.get("default_subagent_runner")
    if not isinstance(spec, str) or ":" not in spec:
        return None
    provider_name, _, model = spec.strip().partition(":")
    provider_name, model = provider_name.strip(), model.strip()
    if not provider_name or not model:
        return None
    provider = get_provider(provider_name)
    if provider is None:
        return None
    # M10 (§5.1) — a **bool** consumer, deliberately left alone. Tier resolution
    # picks a runner spec; it renders no sentence to a human, so the typed
    # `describe_availability()` report has nothing to add here. A logged-out or
    # too-old CLI must still resolve — it is refused (or not) at preflight,
    # carrying the CLI's own message, never by silently disappearing from a
    # picker (D3c: installed is not authenticated).
    try:
        if not provider.is_available():
            return None
    except Exception:  # pragma: no cover - a detection probe never blocks
        return None

    if tier == "cheap":
        tiers = entry.get("subagent_tiers")
        if isinstance(tiers, dict):
            cheap = tiers.get("cheap")
            if isinstance(cheap, str) and cheap.strip():
                return f"{provider_name}:{cheap.strip()}"
    return f"{provider_name}:{model}"


#: The layer name reported for a value the running host's capability entry
#: supplied (D3o). Deliberately *not* spelled like a config file: the entry is a
#: shipped fact consulted only when no override layer expressed an opinion, and
#: pointing a reader at ``providers.yaml`` for a value no file in this repo
#: contains is the support question this reporting exists to end.
HOST_DEFAULT_LAYER = "host capabilities"

#: The layer name reported for the model the **host session** is itself running
#: on (D3o). It is not a config layer and deliberately does not read like one:
#: nobody wrote it into a file, and the repair for a wrong value is the session's
#: own model picker, not ``providers.yaml``. It sits *below* every explicit
#: operator opinion and *above* the host's shipped floor, because "use what I
#: selected" is a weaker claim than "use what I configured" and a much stronger
#: one than "use whatever ships".
SESSION_LAYER = "session"


def session_runner(host_id: Optional[str] = None) -> Optional[str]:
    """The session's own model as a runner spec, when the host can run it.

    Two facts have to line up, and either one missing means no session rung:

    * the host exported :data:`HOST_SESSION_MODEL_ENV` — the model the session is
      *currently* using, in the host's own ``provider/model`` addressing (the
      OpenCode plugin reads it back off the session's newest assistant message and
      sets it on the environment the launcher and every poll run with);
    * the running host's capability entry declares ``session_runner_provider``,
      i.e. names the CLI of its own that can be pointed at that same model. A host
      that declares ``null`` has no such CLI (or no way to read the value), and
      omitting the rung is the conservative answer.

    Why this rung exists at all: without it a ``--review-plan --quick`` run
    launched from a session whose selected model was
    ``opencode/nemotron-3-ultra-free`` validated all sixteen of its batches on
    ``opencode/big-pickle`` — the credential-free *floor* — because no layer above
    that floor had an opinion. Nothing was wrong with the floor; it simply is not
    what the operator picked in the picker two inches above the prompt.

    Like :func:`host_default_runner` this is gated on the runner's CLI being
    detected (D3c) and returns ``None`` whenever the data cannot answer, so a
    partial install degrades to the next rung instead of failing a dispatch. It
    spawns nothing: ``is_available()`` is a ``shutil.which``.
    """
    value = (os.environ.get(HOST_SESSION_MODEL_ENV) or "").strip()
    if not value:
        return None
    entry = _host_entry(host_id)
    if entry is None:
        return None
    provider_name = entry.get("session_runner_provider")
    if not isinstance(provider_name, str) or not provider_name.strip():
        return None
    provider_name = provider_name.strip()
    provider = get_provider(provider_name)
    if provider is None:
        return None
    # The same bool consumer host_default_runner keeps (M10 §5.1): an undetected
    # CLI falls through to the next rung rather than resolving to a spec whose
    # only possible outcome is a refusal.
    try:
        if not provider.is_available():
            return None
    except Exception:  # pragma: no cover - a detection probe never blocks
        return None
    return f"{provider_name}:{value}"


def resolve_subagent_runner(
    tier: str = "full",
    anchor: Optional[Union[str, Path]] = None,
    host_id: Optional[str] = None,
    skip_session: bool = False,
) -> Tuple[str, str]:
    """The resolved runner spec **and the layer that supplied it** (D2e/D3/D3o).

    The one implementation of D3o's ladder, so the value a dispatch uses and the
    value ``status`` / ``install-host --check`` report can never be resolved two
    different ways. Per key, highest precedence first: the value an **explicit**
    override layer supplied (``env`` then ``project``) → the model the host
    session is itself running on (:func:`session_runner`, layer
    :data:`SESSION_LAYER`) → the running host's ``default_subagent_runner`` from
    ``hosts/capabilities.yaml``, when its CLI is detected
    (:func:`host_default_runner`) → the merged (``base``/``default``) value.

    The session rung is **implicit** and deliberately absent from
    :data:`EXPLICIT_DRIVER_LAYERS`: it is what the operator selected, not what
    they configured, so it yields to any ``driver.*`` value a config layer really
    carries while still outranking a shipped floor nobody chose. It is also the
    one rung that is allowed to *fall through at preflight* rather than refuse —
    see ``subagent_executor.run_tasks``, which re-resolves with
    ``skip_session=True`` and prints what it fell back to. Every other rung keeps
    refusing, because an explicit opinion that cannot be served is a config error
    and silently substituting something else is how "I set it and nothing
    changed" starts.

    ``cheap`` reads ``driver.subagent_runner_cheap`` — and the host's own
    ``subagent_tiers.cheap`` when the host default is what answers — falling back
    to ``driver.subagent_runner`` last, as before. The session model has no tier
    split: it is a single thing the operator selected, so a ``cheap`` task takes
    it too unless ``driver.subagent_runner_cheap`` was explicitly set, which wins
    on the rung above. Tracking *where* a value came from is what keeps base's
    ``claude-code:sonnet`` from silently outranking a Codex or OpenCode host's own
    runner while still letting any user-set value win.

    Args:
        skip_session: skip the session rung entirely. The fallback path passes it
            after the session model failed preflight, so the re-resolution cannot
            return the spec that was just refused.

    Returns:
        ``(spec, layer)``, where ``layer`` is one of ``env``, ``project``,
        :data:`SESSION_LAYER`, :data:`HOST_DEFAULT_LAYER`, ``base`` or ``default``.
    """
    driver = get_driver_config(anchor=anchor)
    key = "subagent_runner_cheap" if tier == "cheap" else "subagent_runner"
    configured = driver.get(key)
    layer = get_driver_provenance(key, anchor=anchor)
    if (
        isinstance(configured, str)
        and configured.strip()
        and layer in EXPLICIT_DRIVER_LAYERS
    ):
        return configured.strip(), layer

    if not skip_session:
        session_spec = session_runner(host_id=host_id)
        if session_spec:
            return session_spec, SESSION_LAYER

    host_spec = host_default_runner(tier, host_id=host_id)
    if host_spec:
        return host_spec, HOST_DEFAULT_LAYER

    if tier == "cheap" and isinstance(configured, str) and configured.strip():
        return configured.strip(), layer
    fallback_layer = (
        layer if key == "subagent_runner"
        else get_driver_provenance("subagent_runner", anchor=anchor)
    )
    return (
        str(driver.get("subagent_runner") or DRIVER_FALLBACKS["subagent_runner"]),
        fallback_layer,
    )


def get_subagent_runner(
    tier: str = "full",
    anchor: Optional[Union[str, Path]] = None,
    host_id: Optional[str] = None,
    skip_session: bool = False,
) -> str:
    """The resolved runner spec for a capability tier (D2e/D3/D3o).

    The dispatch-side spelling of :func:`resolve_subagent_runner`, which owns the
    ladder and also names the layer that answered.
    """
    return resolve_subagent_runner(
        tier, anchor=anchor, host_id=host_id, skip_session=skip_session
    )[0]


def get_max_concurrent_subagents(anchor: Optional[Union[str, Path]] = None) -> int:
    """``driver.max_concurrent_subagents`` — the *global* executor gate."""
    return int(get_driver_config(anchor=anchor)["max_concurrent_subagents"])


def get_max_concurrent_write_subagents(
    anchor: Optional[Union[str, Path]] = None
) -> int:
    """``driver.max_concurrent_write_subagents`` — the write gate (default 1, D3h).

    A separate key from the read gate on purpose: the write phases preserve the
    batchers' partitioning invariant (apply phases edit one shared artifact,
    code-fix batches are partitioned by file), so the read path's fan-out would be
    two agents editing one file. Raising this only *permits* parallelism —
    ``can_parallelize`` and the dispatch-time pairwise-disjoint admission check
    still have to agree, and a shared-artifact phase is pinned to 1 regardless.
    """
    return max(1, int(get_driver_config(anchor=anchor)["max_concurrent_write_subagents"]))


def get_verify_command(anchor: Optional[Union[str, Path]] = None) -> Optional[str]:
    """``driver.verify_command`` — the repository's own post-write check (F4).

    ``None`` when the repo declares none, which is a different fact from "it
    passed": the write scheduler logs the difference rather than letting a phase
    that never checked anything read like one that did. The value is a **shell
    command string** (the documented shape is `pnpm typecheck && pnpm lint:fix`),
    run once with `cwd` at the pinned repo root after the last batch applied.
    """
    value = get_driver_config(anchor=anchor).get("verify_command")
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip()


def get_verify_timeout_s(anchor: Optional[Union[str, Path]] = None) -> int:
    """``driver.verify_timeout_s`` — the wall-clock ceiling for the command above."""
    return max(1, int(get_driver_config(anchor=anchor)["verify_timeout_s"]))


def get_write_paths(anchor: Optional[Union[str, Path]] = None) -> Dict[str, List[str]]:
    """``driver.write_paths`` — the declared write policy (D3l), always complete.

    Returns a dict with both ``allow`` and ``deny`` present, falling back to
    :data:`DEFAULT_WRITE_PATHS` per key, so a config that set only ``deny`` still
    yields an ``allow`` list rather than an accidental deny-all.
    """
    configured = get_driver_config(anchor=anchor).get("write_paths")
    configured = configured if isinstance(configured, dict) else {}
    resolved: Dict[str, List[str]] = {}
    for name in ("allow", "deny"):
        patterns = configured.get(name)
        if isinstance(patterns, list) and patterns:
            resolved[name] = [str(item) for item in patterns]
        else:
            resolved[name] = list(DEFAULT_WRITE_PATHS[name])
    return resolved


def get_subagent_retries(anchor: Optional[Union[str, Path]] = None) -> int:
    """``driver.subagent_retries`` — transport-shaped re-dispatches only."""
    return int(get_driver_config(anchor=anchor)["subagent_retries"])


# ---------------------------------------------------------------------------
# progress: — the fan-out's feedback cadences (the block `get_progress_interval`
# and `get_progress_poll`, defined beside `get_provider_timeout`, read)
# ---------------------------------------------------------------------------

#: The base `progress:` block's keys. CLOSED, like `driver:` and unlike the open
#: blocks: an unknown key is REJECTED rather than ignored, because a typo
#: (`interval:`) would otherwise be a silent no-op that keeps the shipped cadence
#: while the user believes they configured a ticker.
PROGRESS_KEYS = ("interval_s", "poll_s")

#: Values used when the merged config carries no `progress:` block at all (a test
#: fixture config, or a base predating the block), mirroring
#: :data:`DRIVER_FALLBACKS`. The shipped base declares both keys, so in a real
#: run these are never reached.
PROGRESS_FALLBACKS: Dict[str, float] = {
    "interval_s": 30.0,
    "poll_s": 90.0,
}


def _progress_floor_s() -> float:
    """The floor both keys share: ``run_status.WAIT_POLL_INTERVAL_S`` (5 s).

    Single-sourced rather than retyped, because the two numbers are the same one
    by construction: a cadence faster than the loop that re-reads the status file
    learns nothing new. Imported lazily because ``utils.run_status`` pulls in the
    detach/status/metrics subtree, and this module is imported by every entry
    point — a module-level import would make the registry drag the whole status
    stack behind it for a constant only the validator reads.
    """
    from .run_status import WAIT_POLL_INTERVAL_S

    return float(WAIT_POLL_INTERVAL_S)


def _progress_error(key: str, value: object, reason: str) -> str:
    """One rejection surface for a bad `progress.*` value: key, value, reason."""
    return f"multi-llm config error: progress.{key} is {value!r} — {reason}."


def _is_finite_number(value: Union[int, float]) -> bool:
    """``math.isfinite``, with an un-representable ``int`` counted as NOT finite.

    PyYAML resolves a bare digit string of any length to a Python ``int``, and
    ``math.isfinite(10**400)`` raises ``OverflowError`` ("int too large to
    convert to float") rather than returning False. Absorbing that here keeps an
    oversized integer on the same :class:`ConfigError` as ``.inf`` / ``.nan``
    instead of escaping :func:`load_config` as an uncaught OverflowError.
    """
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def validate_progress_block(progress: object) -> None:
    """Validate a merged ``progress:`` block, raising :class:`ConfigError`.

    Fail-fast and total, modeled on :func:`validate_driver_block`: every key is
    checked, unknown keys are rejected, and each message names the key, the value
    and the reason. Called from :func:`load_config` whenever an **override** layer
    carried a ``progress:`` key — the base is ours (a broken base is a test
    failure, not a user's problem) and permissive mode does not relax it, because
    a silently ignored cadence degrades to the default, which is the failure this
    check exists for.
    """
    if progress is None:
        return
    if not isinstance(progress, dict):
        raise ConfigError(
            f"multi-llm config error: `progress:` must be a mapping of "
            f"{' / '.join(PROGRESS_KEYS)}, got {type(progress).__name__} "
            f"({progress!r})"
        )

    unknown = sorted(
        f"{key}: {value!r}"
        for key, value in progress.items()
        if key not in PROGRESS_KEYS
    )
    if unknown:
        raise ConfigError(
            f"multi-llm config error: unknown key(s) under `progress:`: "
            f"{'; '.join(unknown)}. Known keys: {', '.join(PROGRESS_KEYS)}. A typo "
            f"here would otherwise be a silent no-op — the shipped cadence kept "
            f"while the config reads as if it had been changed — so it is "
            f"rejected instead of ignored."
        )

    floor = _progress_floor_s()
    for key in PROGRESS_KEYS:
        if key not in progress:
            continue
        value = progress[key]
        # TYPE BEFORE FLOOR, and "numeric" means FINITE numeric. Both keys are
        # seconds, so — unlike DRIVER_POSITIVE_INT_KEYS — a float is legal and an
        # `isinstance(value, int)` guard is not enough on its own. Every value
        # this rejects is one YAML actually produces: `true` is an `int` in
        # Python and would read as a 1 s ticker; a quoted `"30"` would raise
        # TypeError from a comparison deep inside the ticker rather than here; a
        # nested mapping reaches the accessor as a non-number; and `.nan` /
        # `.inf` parse as real floats the floor alone does not handle —
        # `nan >= 5` is False, so a floor check would reject it with a message
        # about a floor rather than about a nonsense value, while `inf >= 5` is
        # True, so an `inf` would sail straight THROUGH and mean a ticker that
        # never fires and a `--wait` that never returns.
        #
        # `null` is deliberately NOT on that list. A blank key (`poll_s:` with
        # nothing after it) is :func:`_deep_merge`'s documented blank-keeps-base
        # form: the override value is SKIPPED, the shipped base's number
        # survives, and the merged block reaching here is the base's. That is the
        # rule every other key follows and the one the `--init` template's
        # commented-out `progress:` stanza relies on, so making this one block
        # the exception would surprise in the other direction. The `None` the
        # type check below still catches is the residual case with no base value
        # to keep — a merged block whose `progress:` came from a layer that
        # REPLACED rather than merged, i.e. a base carrying no `progress:` at all
        # (a fixture) — where `float(None)` would otherwise raise inside the
        # accessor, at fan-out start or in the agent's poll loop.
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not _is_finite_number(value)
        ):
            raise ConfigError(_progress_error(
                key, value,
                "expected a finite number of seconds (YAML's `true`, a quoted "
                "\"30\", a nested mapping, `.nan` and `.inf` all parse to "
                "something this cadence cannot be)",
            ))
        # `interval_s: 0` is the DOCUMENTED disable form, accepted explicitly:
        # it silences the ticker lines and changes nothing else. `poll_s: 0` has
        # no such meaning — a poll of zero returns instantly rather than being
        # switched off — so it is rejected by the floor like any other value
        # under it.
        if key == "interval_s" and value == 0:
            continue
        if value < floor:
            if key == "interval_s":
                reason = (
                    f"expected 0 (the documented disable form: it silences the "
                    f"[PROGRESS] ticker lines only) or at least {floor:g} seconds"
                )
            else:
                reason = (
                    f"expected at least {floor:g} seconds — `poll_s` has no "
                    f"disable form, because 0 means a poll that returns instantly "
                    f"rather than a poll that is switched off"
                )
            raise ConfigError(_progress_error(key, value, reason))


# ---------------------------------------------------------------------------
# code_review: — how `review-code` groups the paths in its scope
# ---------------------------------------------------------------------------

#: The closed key set under `code_review:`. CLOSED, like `progress:`: a typo
#: (`collapse:`) would otherwise be a silent no-op that keeps the shipped rule
#: while the config reads as if it had been changed. ``commit_reviews_dir``
#: is the folder the commit-review modes keep their briefs and report folders
#: in (plans/review-commits.md §2.4); it is registered here and not only
#: shipped in the base, because the block is validated MERGED, so a key the
#: base carries but this set lacks would make every project override of
#: ``collapse_paths`` fail at load.
CODE_REVIEW_KEYS = ("collapse_paths", "commit_reviews_dir")

#: Where commit briefs live when no layer sets ``code_review.commit_reviews_dir``
#: (a fixture base): relative to the repository root, beside the plans
#: (decision 8). The shipped ``providers.yaml`` carries the same value.
DEFAULT_COMMIT_REVIEWS_DIR = "plans/commit-reviews"


def _code_review_error(where: str, value: object, reason: str) -> str:
    """One rejection surface for a bad `code_review.*` value: key, value, reason."""
    return f"multi-llm config error: code_review.{where} is {value!r} — {reason}."


def validate_code_review_block(code_review: object) -> None:
    """Validate a merged ``code_review:`` block, raising :class:`ConfigError`.

    ``collapse_paths`` holds two glob lists, ``generated`` and ``fixtures``,
    that feed :func:`utils.git_utils.classify_review_paths` (the review-scope
    plan's D2.1 rules 1 and 2). Every message names the key. Checked here:

    * the block, and ``collapse_paths`` under it, are mappings with only the
      known keys;
    * each list is a list of non-empty strings — a bare string would otherwise
      be iterated character by character, a glob per letter;
    * no entry is absolute or holds a ``..`` segment: patterns match
      repo-relative paths, so such an entry can never match and the rule would
      silently be no rule at all (the same reasoning as ``driver.write_paths``);
    * every entry compiles, so a malformed character class is reported now
      rather than in the middle of a review.

    ``commit_reviews_dir`` is checked by :func:`_commit_reviews_dir_problem`:
    a non-empty string naming a folder inside the repository by text alone
    (``null`` keeps the default).

    Called from :func:`load_config` whenever an **override** layer carried a
    ``code_review:`` key; the base is ours, and permissive mode does not relax
    it (a dropped list degrades to the default, which is the failure this
    check exists for).
    """
    if code_review is None:
        return
    if not isinstance(code_review, dict):
        raise ConfigError(
            f"multi-llm config error: `code_review:` must be a mapping of "
            f"{' / '.join(CODE_REVIEW_KEYS)}, got {type(code_review).__name__} "
            f"({code_review!r})"
        )
    unknown = sorted(str(key) for key in code_review if key not in CODE_REVIEW_KEYS)
    if unknown:
        raise ConfigError(
            f"multi-llm config error: unknown key(s) under `code_review:`: "
            f"{', '.join(unknown)}. Known keys: {', '.join(CODE_REVIEW_KEYS)}."
        )
    commit_reviews_dir = code_review.get("commit_reviews_dir")
    if commit_reviews_dir is not None:
        problem = _commit_reviews_dir_problem(commit_reviews_dir)
        if problem is not None:
            raise ConfigError(_code_review_error(
                "commit_reviews_dir", commit_reviews_dir, problem,
            ))
    collapse = code_review.get("collapse_paths")
    if collapse is None:
        return
    if not isinstance(collapse, dict):
        raise ConfigError(_code_review_error(
            "collapse_paths", collapse,
            f"expected a mapping with `{'`/`'.join(COLLAPSE_PATH_KEYS)}` glob lists",
        ))
    unknown = sorted(str(key) for key in collapse if key not in COLLAPSE_PATH_KEYS)
    if unknown:
        raise ConfigError(
            f"multi-llm config error: unknown key(s) under "
            f"code_review.collapse_paths: {', '.join(unknown)}. Known keys: "
            f"{', '.join(COLLAPSE_PATH_KEYS)}."
        )
    for name in COLLAPSE_PATH_KEYS:
        if name not in collapse or collapse[name] is None:
            continue
        patterns = collapse[name]
        where = f"collapse_paths.{name}"
        if not isinstance(patterns, list) or not all(
            isinstance(item, str) and item.strip() for item in patterns
        ):
            raise ConfigError(_code_review_error(
                where, patterns,
                'expected a list of non-empty glob strings (e.g. ["**/*.lock", '
                '"dist/**"]); an empty list switches the rule off',
            ))
        for pattern in patterns:
            normalized = pattern.strip().replace("\\", "/")
            drive_prefixed = (
                len(normalized) >= 2 and normalized[1] == ":"
                and normalized[0].isalpha()
            )
            if normalized.startswith("/") or drive_prefixed:
                reason = "an absolute path"
            elif ".." in normalized.split("/"):
                reason = "a parent-traversal ('..') path"
            else:
                reason = None
            if reason is not None:
                raise ConfigError(_code_review_error(
                    where, pattern,
                    f"{reason}; entries match repo-relative paths, so it could "
                    f"never match. Write it relative to the repository root "
                    f'(e.g. "dist/**", "**/*.lock")',
                ))
            try:
                compile_path_glob(pattern)
            except re.error as exc:
                raise ConfigError(_code_review_error(
                    where, pattern, f"not a valid glob ({exc})",
                )) from exc


def get_collapse_paths(
    anchor: Optional[Union[str, Path]] = None,
) -> Dict[str, List[str]]:
    """``code_review.collapse_paths`` — both glob lists, always present.

    What :func:`utils.git_utils.classify_review_paths` is handed. Each list
    falls back to :data:`utils.git_utils.DEFAULT_COLLAPSE_PATHS` per key when
    the merged config has none (a fixture base, or a base predating the block),
    so a layer that set only ``generated`` keeps the default fixture rule. An
    explicit ``[]`` is kept as written: that is how a repository switches a
    rule off.
    """
    config = load_config(anchor=anchor)
    block = config.get("code_review")
    collapse = block.get("collapse_paths") if isinstance(block, dict) else None
    collapse = collapse if isinstance(collapse, dict) else {}
    resolved: Dict[str, List[str]] = {}
    for name in COLLAPSE_PATH_KEYS:
        patterns = collapse.get(name)
        if isinstance(patterns, list):
            resolved[name] = [str(item) for item in patterns]
        else:
            resolved[name] = list(DEFAULT_COLLAPSE_PATHS[name])
    return resolved


_COMMIT_REVIEWS_DIR_HINT = f'e.g. "{DEFAULT_COMMIT_REVIEWS_DIR}"'


def _commit_reviews_dir_segments(value: str) -> List[str]:
    """The folder's path segments, read with ``\\`` as ``/``.

    Empty and ``.`` segments are dropped, so ``./plans/x/`` and ``plans\\x``
    name the same folder as ``plans/x`` on every OS.
    """
    normalized = value.strip().replace("\\", "/")
    return [segment for segment in normalized.split("/") if segment not in ("", ".")]


def _commit_reviews_dir_problem(value: object) -> Optional[str]:
    """Why *value* cannot be ``code_review.commit_reviews_dir``, or ``None``.

    The text alone must keep the folder inside the repository: everything that
    consumes it (the scope drop, the protected set, the porcelain checks)
    works on repo-relative paths. Read with ``\\`` as ``/`` so a value written
    on Windows is judged the same everywhere. What a symlinked component
    resolves to is :func:`get_commit_reviews_dir`'s check, since it needs the
    disk.
    """
    if not isinstance(value, str):
        return (
            f"expected a string naming one folder relative to the repository "
            f"root ({_COMMIT_REVIEWS_DIR_HINT}), or null for the default"
        )
    normalized = value.strip().replace("\\", "/")
    if not normalized:
        return (
            f"an empty string; leave it unset or null for the default "
            f"{DEFAULT_COMMIT_REVIEWS_DIR}"
        )
    drive_prefixed = (
        len(normalized) >= 2 and normalized[1] == ":" and normalized[0].isalpha()
    )
    if normalized.startswith("/") or drive_prefixed:
        return (
            f"an absolute path; the folder is relative to the repository root "
            f"({_COMMIT_REVIEWS_DIR_HINT})"
        )
    if ".." in normalized.split("/"):
        return (
            f"a parent-traversal ('..') path; the folder must lie inside the "
            f"repository ({_COMMIT_REVIEWS_DIR_HINT})"
        )
    if not _commit_reviews_dir_segments(normalized):
        return (
            f"the repository root itself ('.'); name a folder inside the "
            f"repository ({_COMMIT_REVIEWS_DIR_HINT})"
        )
    return None


def _nearest_existing_dir(directory: str) -> str:
    """*directory*, absolute, or its nearest ancestor that exists.

    A brief's folder may not exist yet when the brief path is the anchor, and
    git cannot run in a directory that does not exist.
    """
    current = os.path.abspath(directory)
    while not os.path.isdir(current):
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return current


def get_commit_reviews_dir(anchor: Optional[Union[str, Path]] = None) -> Path:
    """``code_review.commit_reviews_dir`` as an absolute folder in the anchor's repository.

    The one reader of the key (plans/review-commits.md §2.4): the commit-review
    path layer (``utils/commit_review.py``), the front doors and the
    no-argument apply lookup all call it and none reads the YAML. The merged
    value, or :data:`DEFAULT_COMMIT_REVIEWS_DIR` when no layer has one, is
    joined to the git root of *anchor* (a brief path, or a directory such as
    the cwd's repository root): the root ``_find_project_config`` reads the
    project layer from. Never relative to the cwd or to the config file, so a
    ``MULTI_LLM_PROVIDERS_CONFIG`` file kept anywhere still names one folder,
    and a launch from a subdirectory finds the same briefs.

    Returns the joined path, not its ``realpath``. Raises :class:`ConfigError`
    naming the key, the value and the resolved path when
    ``realpath(<root>/<value>)`` is not under ``realpath(<root>)`` (a
    symlinked component pointing out, or back at the root itself), when the
    value fails the load-time text check (a base layer is not validated at
    load), and when *anchor* is not in a git repository at all.
    """
    start = _nearest_existing_dir(_anchor_start_dir(anchor))
    config = load_config(anchor=start)
    block = config.get("code_review")
    value = block.get("commit_reviews_dir") if isinstance(block, dict) else None
    if value is None:
        value = DEFAULT_COMMIT_REVIEWS_DIR
    problem = _commit_reviews_dir_problem(value)
    if problem is not None:
        raise ConfigError(_code_review_error("commit_reviews_dir", value, problem))
    root = get_project_root_from_dir(start)
    if not root:
        raise ConfigError(_code_review_error(
            "commit_reviews_dir", value,
            f"it is relative to the repository root, and {start} is not in a "
            f"git repository",
        ))
    folder = Path(root).joinpath(*_commit_reviews_dir_segments(value))
    real_root = os.path.realpath(root)
    resolved = os.path.realpath(str(folder))
    try:
        relative = os.path.relpath(resolved, real_root)
    except ValueError:  # another drive on Windows
        relative = None
    if relative == os.curdir:
        raise ConfigError(_code_review_error(
            "commit_reviews_dir", value,
            f"it resolves to {resolved}, the repository root itself (a "
            f"symlinked component points there); name a folder inside the "
            f"repository",
        ))
    if relative is None or relative == os.pardir or relative.startswith(os.pardir + os.sep):
        raise ConfigError(_code_review_error(
            "commit_reviews_dir", value,
            f"it resolves to {resolved}, outside the repository {real_root} (a "
            f"symlinked component points out of it); commit reviews must live "
            f"inside the repository",
        ))
    return folder


# ---------------------------------------------------------------------------
# git_env: — the non-interactive git environment's one knob (§2.2)
# ---------------------------------------------------------------------------

#: The closed key set under `git_env:`, global and per provider. Like `driver:`,
#: an unknown key is REJECTED rather than ignored.
GIT_ENV_KEYS = ("credential_helper",)


def validate_git_env_block(git_env: object, where: str = "git_env") -> None:
    """Validate one merged ``git_env:`` block, raising :class:`ConfigError`.

    Called from :func:`load_config` for the global block and for every
    ``providers.<name>.git_env`` an **override** layer carried. Base is ours, so
    a broken base is a test failure rather than a user's config error.

    Fail-fast rather than fall-back-to-``auto``, because this key's whole purpose
    is to switch a measured hang-avoidance off (or on): a typo that silently
    resolved to the default would restore the behaviour the user was trying to
    change while looking like it had worked.
    """
    if git_env is None:
        return
    if not isinstance(git_env, dict):
        raise ConfigError(
            f"multi-llm config error: `{where}:` must be a mapping, got "
            f"{type(git_env).__name__}"
        )
    unknown = [key for key in git_env if key not in GIT_ENV_KEYS]
    if unknown:
        raise ConfigError(
            f"multi-llm config error: unknown key(s) under `{where}:`: "
            f"{', '.join(sorted(unknown))}. Known keys: {', '.join(GIT_ENV_KEYS)}."
        )
    value = git_env.get("credential_helper")
    if value is None:
        return
    if not isinstance(value, str) or value.strip() not in GIT_HELPER_POLICIES:
        raise ConfigError(
            f"multi-llm config error: {where}.credential_helper is {value!r} — "
            f"expected one of {', '.join(GIT_HELPER_POLICIES)}. `auto` scopes the "
            f"credential-helper wipe to the read-only lanes (generate, the Lane A "
            f"fan-out, agent-readonly) and never applies it to agent-write; "
            f"`keep` disables it everywhere; `wipe` applies it everywhere."
        )


def get_git_credential_helper(
    provider_name: Optional[str] = None,
    anchor: Optional[Union[str, Path]] = None,
) -> str:
    """Resolve ``git_env.credential_helper`` for one provider (§2.2).

    Precedence: ``MULTI_LLM_GIT_CREDENTIAL_HELPER`` (a one-run debugging hatch) →
    ``providers.<name>.git_env.credential_helper`` → the top-level
    ``git_env.credential_helper`` → ``auto``.

    The env var is the one input that is **not** fail-fast: it is read on every
    dispatch, far from any parser, so an unrecognized value warns on stderr
    naming the variable and falls back to ``auto`` rather than raising out of the
    middle of a fan-out. Config values are validated at load time instead.
    """
    override = os.environ.get(ENV_GIT_CREDENTIAL_HELPER_VAR)
    if override is not None and override.strip():
        candidate = override.strip()
        if candidate in GIT_HELPER_POLICIES:
            return candidate
        print(
            f"{CONFIG_WARNING_PREFIX} ignoring "
            f"{ENV_GIT_CREDENTIAL_HELPER_VAR}={override!r} (expected one of "
            f"{', '.join(GIT_HELPER_POLICIES)}); using {GIT_HELPER_AUTO}",
            file=sys.stderr,
        )
        return GIT_HELPER_AUTO

    config = load_config(anchor=anchor)
    for block in (
        (config.get("providers") or {}).get(provider_name)
        if provider_name and isinstance(config.get("providers"), dict)
        else None,
        config,
    ):
        if not isinstance(block, dict):
            continue
        git_env = block.get("git_env")
        if not isinstance(git_env, dict):
            continue
        value = git_env.get("credential_helper")
        if isinstance(value, str) and value.strip() in GIT_HELPER_POLICIES:
            return value.strip()
    return GIT_HELPER_AUTO


def get_subagent_timeout(
    provider_name: str, anchor: Optional[Union[str, Path]] = None
) -> int:
    """Per-dispatch timeout: ``driver.subagent_timeout_s`` or the provider default."""
    configured = get_driver_config(anchor=anchor)["subagent_timeout_s"]
    if isinstance(configured, int) and not isinstance(configured, bool):
        return configured
    # Base ships `subagent_timeout_s: null`, so THIS is the default-on path:
    # dropping the anchor here would leak the whole Lane B half to CWD (§9.3.c).
    return get_provider_timeout(provider_name, anchor=anchor)


def get_provider_max_concurrent(
    provider_name: str, anchor: Optional[Union[str, Path]] = None
) -> Optional[int]:
    """Get the max concurrent limit for a provider, if configured.

    Returns None if no limit is set, meaning the provider uses only the global
    semaphore (unlimited concurrency within it).

    Args:
        anchor: Optional plan-file path or target-repo directory, threaded
            through to ``load_config`` exactly like the ``driver`` accessors so a
            project-local ``.multi-llm/providers.yaml`` still binds when the run
            starts outside that project. Omitted, discovery falls back to CWD.
    """
    config = load_config(anchor=anchor)
    providers = config.get("providers", {})
    if provider_name in providers:
        return providers[provider_name].get("max_concurrent")
    return None
