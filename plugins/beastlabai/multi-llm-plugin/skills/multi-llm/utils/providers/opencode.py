"""OpenCode CLI provider implementation with NDJSON event stream parsing."""
import atexit
import contextlib
import contextvars
import difflib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import threading
from typing import (
    Any,
    Callable,
    Dict,
    FrozenSet,
    Iterator,
    List,
    Mapping,
    NamedTuple,
    Optional,
    Tuple,
)

from ..json_extractor import extract_json_from_text, strip_jsonc
from .base import (
    PROFILE_AGENT_READONLY,
    PROFILE_AGENT_WRITE,
    PROFILE_GENERATE,
    CATEGORY_INVALID_MODEL,
    CATEGORY_SANDBOX_UNAVAILABLE,
    REASONING_LADDER,
    STATUS_AUTH_FAILED,
    STATUS_CONTEXT_LENGTH_EXCEEDED,
    STATUS_RATE_LIMITED,
    STATUS_RUNNER_ERROR,
    USAGE_FULL,
    LLMProvider,
    ModelVerdict,
    ReasoningLadder,
    StructuredSchema,
    split_reasoning_effort,
    version_tuple,
)

# OpenCode ships a built-in `plan` agent whose permission set denies every edit
# tool ("Plan mode. Disallows all edit tools." — verified against the agent
# table in the 1.18.x binary's embedded bundle, alongside `edit: {"*": "deny"}`).
# `--agent` is a documented `opencode run` flag, so the read-only profile is
# opencode's own permission mechanism rather than a convention this repo layers
# on top.
READONLY_AGENT = "plan"

# OpenCode's built-in edit-capable agent, the one `opencode run` uses when
# `--agent` is omitted ("build" — the primary agent in the same embedded agent
# table `plan` comes from). It is named EXPLICITLY on the `agent-write` profile
# rather than relying on the default, so a future change to opencode's default
# agent cannot silently move a write dispatch onto a different permission set.
WRITE_AGENT = "build"

# Reasoning effort values accepted by `opencode run --variant` — the values are
# provider-specific, so this is the practical union across providers
# (verified live against opencode 1.17.15): all seven canonical rungs, since
# every one of the 24 observed per-model `variants` sets is a subset of them.
#
# `model_caps` carries the one combination that is not merely unsupported but
# MEASURED TO HANG: `--variant` on `openrouter/deepseek/deepseek-v4-flash-0731`
# writes zero bytes to either stream, never reaches session creation, and burns
# the whole slot timeout, where the plain (suffix-free) model answers in ~3 s.
# It was a prose comment in `providers.yaml` before M12 and is a declaration
# here now, so a config that re-adds the suffix is graded against the adapter
# rather than against a paragraph nobody parses.
EFFORT_LADDER = ReasoningLadder(
    provider="opencode",
    rungs=REASONING_LADDER,
    model_caps=(("openrouter/deepseek/deepseek-v4-flash-0731", ()),),
)
REASONING_EFFORTS = EFFORT_LADDER.accepted

# ─────────────────────────────────────────────────────────────────────────────
# R3 — the structural model-spec refusal (opencode only).
#
# `opencode run --help` documents `-m, --model` as "model to use in the format
# of provider/model", and the resolver enforces it by *splitting* on the first
# `/`: a bare token becomes provider `<token>` with an empty model half, which
# fails as `ProviderModelNotFoundError: Model not found: <token>/.` before any
# HTTP call is attempted. Measured on opencode 1.18.18.
#
# That is the whole predicate, and the reason it is safe to refuse on: an empty
# model half is not a name any catalog, any release or any server can supply, so
# the dispatch is unresolvable *by construction*. It is deliberately NOT a
# catalog test — a well-formed slug that opencode's catalog does not list may
# still be live server-side or served by a provider declared in opencode's own
# config, which multi-llm cannot read, and refusing those would break working
# setups. Refuse only what the addressing scheme cannot express, never what the
# catalog merely does not list.
#
# If a later opencode release starts resolving bare tokens against a default
# provider, this check is withdrawn back to a warning rather than kept on for
# tidiness.
# ─────────────────────────────────────────────────────────────────────────────

#: The version the bare-token behaviour above was observed on.
STRUCTURAL_MODEL_VERSION = "1.18.18"

# ─────────────────────────────────────────────────────────────────────────────
# M4 / donor §2.3 — hermetic runs.
#
# The user's own opencode config can silently change the effective model, agent
# or permission set per machine and per repository. The containment is an empty,
# run-scoped `XDG_CONFIG_HOME` plus `--pure`; `XDG_DATA_HOME` is passed through
# untouched, which is what keeps `auth.json` (and therefore `auth list` and
# `models`) working — auth is never config-borne.
#
# `XDG_CACHE_HOME` is deliberately NOT redirected: it holds `opencode/models.json`,
# and a cold cache degrades *silently* (exit 0, empty stderr, a truncated model
# list). `XDG_STATE_HOME` and `XDG_RUNTIME_DIR` are likewise untouched.
#
# Measured on opencode 1.18.18, three deviations from the donor's text worth
# recording where the code is:
#   * `XDG_CONFIG_HOME` alone leaves the **workspace** `opencode.json` in force —
#     `--pure` does not close that layer either (measured: a workspace file
#     pinning `model` and an extra agent still shows up in `opencode debug
#     config` under both). `OPENCODE_DISABLE_PROJECT_CONFIG=1` is what yields the
#     empty-config shape, so it is set alongside the redirect; without it the
#     project-config isolation this section exists to provide does not exist.
#   * the directory does not stay empty: opencode seeds `opencode/.gitignore`
#     and an `opencode/opencode.jsonc` holding nothing but `$schema`. That is
#     fixed content with no per-slot state, so the one-shared-directory rule
#     stands; cleanup is `rmtree`, not `rmdir`. A future version that writes
#     slot-*varying* state there is what moves this to per-slot.
#   * `OPENCODE_CONFIG`, `OPENCODE_CONFIG_CONTENT` and `OPENCODE_CONFIG_DIR` are
#     stripped from the inherited environment while hermetic, because
#     `OPENCODE_CONFIG_CONTENT` is a *last-applied deep-merge layer* and an
#     inherited one would survive — and win over — the redirect.
#   * (measured 1.18.34, scratch HOME, egress closed) `~/.opencode/` is a config
#     directory too — `opencode.json[c]`, `agent/`, `command/`, plugins — read
#     from opencode's own home (`Global.Path.home` = `OPENCODE_TEST_HOME`, else
#     `os.homedir()`), which neither the redirect nor the project switch
#     reaches: a provider and an agent declared there showed up in a hermetic
#     `debug config`. `OPENCODE_TEST_HOME` set to the slot's config home closes
#     it and moves nothing else that a run needs: `HOME` is untouched, and
#     `auth.json`, the caches and the state directory derive from `HOME`/XDG,
#     not from that home (`opencode debug paths`, measured). Its side effects:
#     the global skill scan (`~/.claude/skills`, `~/.agents/skills`) and a `~/`
#     in a config's `instructions`/`skills.paths` resolve under the slot, so a
#     hermetic run sees no user-level skill either. It is opencode's test hook,
#     the only lever there is; the debug-config capture's `home_opencode_layer`
#     / `hermetic_home_opencode` pair re-measures it on every bump.
# ─────────────────────────────────────────────────────────────────────────────

#: `opencode run --pure` — "run without external plugins". Optional, not
#: load-bearing: without it the redirect still removes the global config layer,
#: so an unsupported or undecidable `--help` sniff omits the flag, WARNs the
#: reduced containment and keeps the run.
PURE_FLAG = "--pure"

#: `providers.opencode.hermetic`. `off` restores today's inheritance; `on` (the
#: default) and `auto` both apply the redirect to the profiles in
#: :data:`HERMETIC_PROFILES`. `auto` is accepted and behaves as `on` today — it
#: exists so the documented vocabulary is a value the loader accepts rather than
#: a validation error, and it is the value that stays *scoped* if `on` is later
#: widened to write slots.
HERMETIC_POLICIES = ("auto", "on", "off")
HERMETIC_DEFAULT = "on"

#: Fan-out (`generate`, which is what Lane A and `ask` dispatch under) and
#: `agent-readonly` only. `agent-write` keeps today's inherited config: the
#: built-in `build` agent is *expected* to survive `--pure`, and "expected" is
#: not the standard this repo applies to permission-carrying dispatch. Write
#: slots join once the ship gates are green on a write slot.
HERMETIC_PROFILES = frozenset({PROFILE_GENERATE, PROFILE_AGENT_READONLY})

#: `tempfile.mkdtemp` prefix, so a leaked directory is sweepable by name.
HERMETIC_DIR_PREFIX = "multi-llm-opencode-"

#: Config-carrying variables an inherited environment may hold. Stripped while
#: hermetic — except the one this adapter emits itself, when it emits it.
#:
#: ``OPENCODE_PERMISSION`` is opencode's own permission override, and it merges
#: **after** ``OPENCODE_CONFIG_CONTENT`` (read from the 1.18.32 binary: the
#: config layers are the files, then the content, then the account org config,
#: the managed file and this variable). It lands in the top-level
#: ``permission``, which the agent-layer rows the hermetic content carries
#: already beat (T4.6 rig ``envperm_plan``), but it is a config carrier the
#: redirect does not reach, so a hermetic slot strips it like the three above
#: (plans/opencode-validator-false-rate-limit-and-denied-turn.md §4.2 step 1).
#: A non-hermetic slot leaves it alone: there it is the user's own override.
CONFIG_ENV_NAMES = (
    "OPENCODE_CONFIG",
    "OPENCODE_CONFIG_CONTENT",
    "OPENCODE_CONFIG_DIR",
    "OPENCODE_PERMISSION",
)

#: Closes the workspace-`opencode.json` layer the redirect does not reach.
PROJECT_CONFIG_ENV = "OPENCODE_DISABLE_PROJECT_CONFIG"

#: opencode's own home (`Global.Path.home`), where it finds `~/.opencode/`. A
#: hermetic slot points it at its empty config home (see the M4 notes above).
HOME_DIR_ENV = "OPENCODE_TEST_HOME"

# ─────────────────────────────────────────────────────────────────────────────
# The denied turn (plans/opencode-validator-false-rate-limit-and-denied-turn.md
# §4.2, T4.1/T4.2).
#
# `opencode run` answers every permission `ask` with an auto-reject, and on
# 1.18.32 a rejected permission ENDS the agent loop: the process exits 0 with no
# final answer (run b38de8bb, a validator that probed a path outside cwd). A
# `deny` rule is a different error class that goes back to the model, and the
# loop continues. The built-in `plan` and `build` agents both carry `ask` for
# three rows — any path outside cwd (`external_directory`), a `.env` read, and
# the doom-loop trigger — so every one of them is a turn-ender under `run`.
#
# The rows below turn those three `ask`s into `deny`. They add denies only, so
# they grant no profile anything it lacked. `deny` is chosen over `--auto`,
# which would *approve* the `.env` reads.
#
# **Where they go: `agent.<name>.permission`, never top-level `permission`.**
# Measured on 1.18.32: a user's top-level `{"external_directory": "ask", "*":
# "allow"}` beat the same rows delivered top-level, because a merged key keeps
# its earlier position and opencode's ruleset is `findLast`. The agent layer is
# evaluated after every top-level layer (T4.6 rig, `q2_ustar_agentlayer_*`: the
# deny returns to the model and the turn finishes `stop`). A user's own
# `agent.<name>.permission.external_directory` in a config *file* is beaten too
# (rig `useragent_*`): only a layer merged after `OPENCODE_CONFIG_CONTENT` can
# shadow ours.
#
# **Known limitations of the hermetic delivery** (T4.6 rig, `SCHEMA.md`,
# "Layers after OPENCODE_CONFIG_CONTENT"). Three sources merge after the
# content, and neither `--pure` nor the `XDG_CONFIG_HOME` redirect gates them:
#   * `OPENCODE_PERMISSION` merges into the top-level `permission`, which our
#     agent layer beats (rig `envperm_plan`). It is stripped while hermetic
#     anyway (`CONFIG_ENV_NAMES`).
#   * The **managed** system config file. One that sets
#     `agent.<name>.permission.external_directory` itself shadows our deny (rig
#     `managed_agent_plan`: the read completed). The only env lever is an
#     opencode test hook, so it is not overridden: it is administrator policy.
#   * The **active-org account config**, fetched when `<data>/opencode.db` holds
#     a logged-in org account. The hermetic env passes `XDG_DATA_HOME` through,
#     so it loads in a hermetic slot, and an org config that sets the same agent
#     row shadows our deny (rig `org_agent_plan`). `OPENCODE_DB` pointed away
#     disables it but also stops session persistence; not done here, it is
#     organisation policy.
# A shadowing layer of either kind is a silent allow, which the structural
# denied-turn check (`classify_structural`) cannot catch.
#
# **The non-hermetic delivery (T4.7, §4.4).** `agent-write` (always) and
# `agent-readonly` under `hermetic: off` keep the user's own config, so they get
# no rebuild, no `--pure`, no `XDG_CONFIG_HOME` redirect and no stripping. Their
# rows are merged **over** the inherited `OPENCODE_CONFIG_CONTENT` instead
# (:func:`merge_permission_content`), under `agent.build` / `agent.plan`, and the
# user's own `external_directory` rules, read through `debug config`
# (:func:`read_user_declared_config`), are re-listed after our `"*": "deny"`
# (:func:`relisted_external_rules`) — a user allow before our deny is shadowed
# by it (rig `t47_shared_toplevel_*`), one re-listed after it survives (rig
# `t47_shared_*`). The `generate` profile under `hermetic: off` gets nothing:
# a user's `default_agent` can move it off `build` anyway, so it stays a
# recorded limitation rather than a guess at which agent to target.
# ─────────────────────────────────────────────────────────────────────────────

#: The three rows, in the order opencode evaluates them. Every rule map is
#: serialized in insertion order (see :func:`_dump_config`): the ruleset is
#: `findLast`, so `"*": "deny"` must stay first in `external_directory`, and the
#: `*.env.example` allow must follow the `*.env.*` deny it narrows.
PERMISSION_ROWS: Tuple[Tuple[str, Any], ...] = (
    ("external_directory", (("*", "deny"),)),
    ("read", (("*.env", "deny"), ("*.env.*", "deny"), ("*.env.example", "allow"))),
    ("doom_loop", "deny"),
)

#: The opencode agent each profile runs, and therefore the `agent.<name>` key its
#: permission rows go under. `generate` passes no `--agent`, so it runs
#: opencode's default agent, `build` (the same value as :data:`WRITE_AGENT`);
#: the profile stays read-intent because the rows only add denies.
PERMISSION_AGENT_BY_PROFILE: Dict[str, str] = {
    PROFILE_AGENT_READONLY: READONLY_AGENT,
    PROFILE_GENERATE: WRITE_AGENT,
    PROFILE_AGENT_WRITE: WRITE_AGENT,
}

#: The key the permission-rule maps sit under. Every map below a `permission`
#: key is an ordered rule list, never a set, so it is dumped as inserted.
_PERMISSION_KEY = "permission"


def _node_tmpdir(env: Mapping[str, str]) -> str:
    """The directory Node's ``os.tmpdir()`` returns for ``env`` (POSIX rule).

    ``TMPDIR``, then ``TMP``, then ``TEMP``, else the root ``tmp`` directory,
    with a trailing separator dropped — the order Node reads them in, which is
    not Python's ``tempfile`` order (and Node checks nothing for writability).
    """
    for name in ("TMPDIR", "TMP", "TEMP"):
        value = env.get(name)
        if value:
            stripped = value.rstrip("/\\")
            return stripped or value
    return os.path.join(os.sep, "tmp")


def _xdg_data_home(env: Mapping[str, str]) -> str:
    """``XDG_DATA_HOME``, else ``~/.local/share`` — what opencode's data dir
    (``<data>/opencode``) is rooted at. A hermetic slot passes it through."""
    value = env.get("XDG_DATA_HOME")
    if value:
        return value
    home = env.get("HOME") or os.path.expanduser("~")
    return os.path.join(home, ".local", "share")


def builtin_external_allows(
    agent: str, env: Optional[Mapping[str, str]] = None
) -> List[str]:
    """The built-in ``external_directory`` allows our ``"*": "deny"`` shadows.

    MEASURED on the pinned release (the T4.6 rig, cases ``builtin_tmp_{plan,build}`` and
    ``builtin_plansdir_{plan,build}`` against their ``_ctrl`` twins): the
    shared defaults and the agents' own overrides carry these allows *before*
    the agent layer, so by ``findLast`` our deny shadows them and a read the
    built-in agent allowed came back denied. Only ``<data>/opencode/tool-output/*``
    is appended after the agent layer and survives, so it is not re-listed.

    * ``<tmp>/opencode/*`` — both agents;
    * ``<data>/opencode/plans/*`` — ``plan`` only (absent from ``build``'s
      resolved rules).

    The globs cannot be read from ``opencode debug config`` (it does not print
    the per-agent built-in defaults), so they are hard-coded here from the deny
    error's resolved rule list and resolved the way opencode resolves them,
    from ``env`` (default this process's environment, which is the dispatch
    env for every name read here: ``TMPDIR``/``TMP``/``TEMP``, ``HOME`` and the
    ``XDG_`` family all pass the env allowlist and the hermetic delta unchanged).
    Every bump re-runs the rig, and ``test_opencode_permission_block.py`` reads
    these globs back out of the new capture's deny errors.

    **Known limitation, not re-listed:** the directory of each *discovered
    skill* (the rig's ``builtin_skilldir_*`` case, e.g. a skill under
    ``$HOME/.claude/skills/<name>/``) and each config-reference path are
    shadowed too, but which ones opencode discovers depends on the machine and
    cannot be enumerated here. A read under one now returns a deny to the
    model, which continues the turn rather than ending it.
    """
    source = os.environ if env is None else env
    allows = [os.path.join(_node_tmpdir(source), "opencode", "*")]
    if agent == READONLY_AGENT:
        allows.append(os.path.join(_xdg_data_home(source), "opencode", "plans", "*"))
    return allows


def permission_block(
    agent: Optional[str] = None, env: Optional[Mapping[str, str]] = None
) -> Dict[str, Any]:
    """A fresh copy of the §4.2 step 1 rows, as ordered dicts.

    With ``agent``, the built-in allows the deny shadows
    (:func:`builtin_external_allows`) are re-listed right after ``"*": "deny"``,
    so the block takes away only the ``ask`` rows and nothing the built-in agent
    already allowed. A caller that appends its own patterns (T4.7: the user's)
    appends them after these.

    Fresh on every call so a caller (T4.7's merge over an inherited value, say)
    can extend `external_directory` without mutating a shared constant.
    """
    block: Dict[str, Any] = {}
    for name, rule in PERMISSION_ROWS:
        block[name] = dict(rule) if isinstance(rule, tuple) else rule
    if agent is not None:
        for pattern in builtin_external_allows(agent, env):
            block["external_directory"][pattern] = "allow"
    return block


def _ordered_for_dump(value: Any, *, in_permission: bool = False) -> Any:
    """``value`` with every mapping key-sorted, except the permission rule maps.

    ``json.dumps(sort_keys=True)`` was right for the old provider-only content
    by accident, and it is wrong for a rule map: opencode evaluates rules
    `findLast`, so their order is their meaning, and a pattern that sorts before
    `"*"` (``"!x/*"``) would land ahead of the deny and be shadowed by it. So a
    mapping *below* a ``permission`` key keeps its insertion order, and every
    other mapping is sorted here, so the rest of the output stays deterministic.
    """
    if isinstance(value, dict):
        keys = list(value) if in_permission else sorted(value)
        return {
            key: _ordered_for_dump(
                value[key], in_permission=in_permission or key == _PERMISSION_KEY
            )
            for key in keys
        }
    if isinstance(value, list):
        return [_ordered_for_dump(item, in_permission=in_permission) for item in value]
    return value


def _dump_config(document: Dict[str, Any]) -> str:
    """The one serializer for an emitted ``OPENCODE_CONFIG_CONTENT``."""
    return json.dumps(_ordered_for_dump(document), sort_keys=False)


#: Versions this process has no read for: the executor's preflight records
#: ``"unknown"`` when `--version` failed, and a caller with no preflight read
#: at all passes ``None``.
_UNREAD_VERSIONS = frozenset({"", "unknown", "unread"})


def continue_loop_on_deny_allowed(
    version: Optional[str],
    version_range: Optional[Tuple[str, str]] = None,
) -> bool:
    """Whether ``experimental.continue_loop_on_deny`` may be emitted (T4.2).

    The key is experimental, so it is emitted only for a running opencode inside
    the measured :attr:`OpenCodeProvider.CONTINUE_LOOP_ON_DENY_RANGE` (inclusive
    both ends). It is the belt-and-braces half: the deny rows are the primary
    mechanism, and every branch that omits the key keeps them.

    * in range → ``True``;
    * below the floor → ``False``, silently (not the above-range case);
    * above the ceiling → ``False``, with one WARN per process naming the
      version and both bounds;
    * unread (``None``, ``""``, ``"unknown"``) → ``False``, fail-safe, with one
      WARN per process.

    ``version`` is the preflight's cached read, handed in by the caller; this
    never spawns ``opencode --version``. Shared by every profile that carries
    the key, so the write profile's delivery (T4.7) calls it too.
    """
    floor, ceiling = version_range or OpenCodeProvider.CONTINUE_LOOP_ON_DENY_RANGE
    token = (version or "").strip()
    if token.lower() in _UNREAD_VERSIONS:
        _warn_once(
            "continue-loop-unread",
            "multi-llm warning: the opencode version was not read on this path, "
            "so experimental.continue_loop_on_deny is omitted (fail-safe; the "
            "permission deny rows still apply).",
        )
        return False
    current = version_tuple(token)
    if current < version_tuple(floor):
        return False
    if current > version_tuple(ceiling):
        _warn_once(
            "continue-loop-above",
            f"multi-llm warning: opencode {token} is above the measured "
            f"continue_loop_on_deny range {floor}-{ceiling}; the key is omitted",
        )
        return False
    return True

#: Lane A's own ``opencode --version`` read, one per process. Lane A
#: (``llm_client``'s ``generate`` fan-out and ``--ask``) has no executor
#: preflight to hand a version in, so without this every such dispatch would
#: land on the unread branch above: the key never emitted on ``generate`` and
#: the "not read on this path" WARN printed on an ordinary run.
_LANE_A_VERSION: Dict[str, str] = {}
_LANE_A_VERSION_LOCK = threading.Lock()


def _lane_a_runner_version(provider: Any) -> str:
    """The running opencode version for a dispatch whose caller passed none.

    Read once per process (concurrent first callers share it) from the
    adapter's ``version_cmd`` and ``parse_version``, the same pair the
    executor's preflight uses. Any failure caches ``"unknown"``, which
    :func:`continue_loop_on_deny_allowed` treats as unread: the key is omitted
    and the WARN names a genuinely failed read.
    """
    with _LANE_A_VERSION_LOCK:
        cached = _LANE_A_VERSION.get("opencode")
        if cached is not None:
            return cached
        version = "unknown"
        argv = list(getattr(provider, "version_cmd", ()) or ())
        try:
            if argv:
                # Resolved like every other opencode spawn here: a bare
                # `opencode` is WinError 2 against npm's `opencode.cmd`.
                completed = subprocess.run(
                    [*_opencode_launcher(argv[0]), *argv[1:]],
                    stdin=subprocess.DEVNULL,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=5,
                )
                if completed.returncode == 0:
                    parsed = provider.parse_version(
                        completed.stdout or "", completed.stderr or ""
                    )
                    if parsed:
                        version = parsed
        except Exception:  # noqa: BLE001 - a failed read is "unknown", never a raise
            version = "unknown"
        _LANE_A_VERSION["opencode"] = version
        return version


_CONFIG_HOME_LOCK = threading.RLock()
_CONFIG_HOME: Optional[str] = None
#: How many dispatch contexts are currently inside the shared directory. One
#: directory per *process*, shared by every concurrent slot (no slot writes
#: per-slot state there), removed when the last slot leaves.
_CONFIG_HOME_USERS = 0
_ATEXIT_REGISTERED = False

#: The active dispatch's hermetic state, or ``None``. A ``ContextVar`` rather
#: than a plain global because it must be per-thread AND per-asyncio-task: Lane A
#: fans out concurrently, and a slot must never see another slot's env.
#:
#: Argv and env both read it, which is the point — ``--pure`` without the paired
#: `XDG_CONFIG_HOME` redirect is meaningless, so the two halves are rendered from
#: one piece of state and cannot drift apart. Outside a dispatch context the
#: adapter renders exactly the argv and env it rendered before M4.
_ACTIVE: contextvars.ContextVar[Optional[Dict[str, Any]]] = (
    contextvars.ContextVar("multi_llm_opencode_hermetic", default=None)
)

_WARNED: set = set()
_WARNED_LOCK = threading.Lock()


def _warn_once(key: str, message: str) -> None:
    # Check-and-add under a lock: the write scheduler dispatches disjoint
    # batches on threads, so concurrent first callers must not all print.
    with _WARNED_LOCK:
        if key in _WARNED:
            return
        _WARNED.add(key)
    print(message, file=sys.stderr)


def _load_config(anchor: Optional[str] = None) -> Dict[str, Any]:
    """multi-llm's merged config, or ``{}`` if it cannot be read.

    A config problem may never turn into a refusal or a crash on a dispatch
    path, so every failure here resolves to "no configuration", which means the
    documented defaults.
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


def _opencode_block(anchor: Optional[str] = None) -> Dict[str, Any]:
    providers = _load_config(anchor).get("providers")
    if not isinstance(providers, dict):
        return {}
    block = providers.get("opencode")
    return block if isinstance(block, dict) else {}


def hermetic_policy(anchor: Optional[str] = None) -> str:
    """Resolve ``providers.opencode.hermetic`` (default :data:`HERMETIC_DEFAULT`).

    An unrecognized value warns once naming the key and falls back to the
    default: this is read on every dispatch, far from any parser, and raising
    out of the middle of a fan-out over a typo would be worse than the typo.
    """
    value = _opencode_block(anchor).get("hermetic")
    if value is None:
        return HERMETIC_DEFAULT
    if isinstance(value, bool):
        # YAML 1.1 resolves a bare `on`/`off` to a boolean, and a user who wrote
        # the documented word should get the documented behaviour rather than a
        # warning about their own YAML loader.
        return "on" if value else "off"
    candidate = str(value).strip().lower()
    if candidate in HERMETIC_POLICIES:
        return candidate
    _warn_once(
        f"hermetic:{candidate}",
        f"multi-llm config warning: ignoring providers.opencode.hermetic="
        f"{value!r} (expected one of {', '.join(HERMETIC_POLICIES)}); using "
        f"{HERMETIC_DEFAULT}",
    )
    return HERMETIC_DEFAULT


def hermetic_enabled(profile: str, anchor: Optional[str] = None) -> bool:
    """Whether this profile runs hermetically under the resolved policy."""
    if hermetic_policy(anchor) == "off":
        return False
    return profile in HERMETIC_PROFILES


def _register_sweep() -> None:
    global _ATEXIT_REGISTERED
    if _ATEXIT_REGISTERED:
        return
    atexit.register(sweep_config_home)
    _ATEXIT_REGISTERED = True


def acquire_config_home() -> str:
    """The process-scoped 0700 config home, created on first use.

    One directory per orchestrator process, **shared** by every concurrent
    opencode slot: it exists only so opencode's config loader finds nothing of
    the user's, no slot keeps state in it, and a per-slot directory would
    multiply `mkdtemp` calls and cleanup races for zero isolation.
    """
    global _CONFIG_HOME, _CONFIG_HOME_USERS
    with _CONFIG_HOME_LOCK:
        if _CONFIG_HOME is None or not os.path.isdir(_CONFIG_HOME):
            _CONFIG_HOME = tempfile.mkdtemp(prefix=HERMETIC_DIR_PREFIX)
            os.chmod(_CONFIG_HOME, 0o700)
            _register_sweep()
        _CONFIG_HOME_USERS += 1
        return _CONFIG_HOME


def release_config_home() -> None:
    """Drop one user of the shared directory; remove it when the last leaves."""
    global _CONFIG_HOME_USERS
    with _CONFIG_HOME_LOCK:
        _CONFIG_HOME_USERS = max(0, _CONFIG_HOME_USERS - 1)
        if _CONFIG_HOME_USERS == 0:
            sweep_config_home()


def sweep_config_home() -> None:
    """Remove the directory this process created. Idempotent, never raises.

    **Never removes a directory this process did not create** — a user-supplied
    ``XDG_CONFIG_HOME`` is overridden for opencode slots and never deleted. It is
    `rmtree`, not `rmdir`, because opencode seeds a stub config file there
    (measured, 1.18.18); a leak costs one inode and is sweepable by prefix under
    ``TMPDIR``.
    """
    global _CONFIG_HOME, _CONFIG_HOME_USERS
    with _CONFIG_HOME_LOCK:
        path, _CONFIG_HOME, _CONFIG_HOME_USERS = _CONFIG_HOME, None, 0
    if not path:
        return
    shutil.rmtree(path, ignore_errors=True)


#: One bare ``provider/model`` slug, the whole line: no whitespace, at least
#: one ``/``, nothing that could be a log field or a decoration.
_MODEL_SLUG = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*/[^\s]+$")

#: A ``--print-logs`` line, which is what a listing must NOT open with.
_LOG_LINE = re.compile(r"^\s*(?:timestamp|level|service)=", re.IGNORECASE)


def _list_models(
    argv: List[str], env: Dict[str, str]
) -> Optional["subprocess.CompletedProcess"]:
    """Run the listing subcommand with the executor's own probe pins (D3 step 4).

    Mirrors ``subagent_executor._run_probe`` exactly — ``timeout=30``,
    ``stdin=DEVNULL``, captured text streams, ``None`` on any ``OSError`` /
    ``SubprocessError`` — because that ceiling is the one that matters: a
    ``subprocess.TimeoutExpired`` **is** a ``SubprocessError``, so a listing
    that hangs is killed at 30 s and read as *unknown*, which blocks nothing.
    It takes ``env`` because the listing must be read under the dispatch's own
    hermetic delta, which the executor's probe has no channel for.
    """
    launcher: List[str] = [argv[0]]
    try:  # pragma: no cover - import shim mirrors the rest of utils/
        from ..llm_client import _resolve_executable
    except ImportError:  # pragma: no cover - direct-script import shim
        try:
            from utils.llm_client import _resolve_executable  # type: ignore
        except ImportError:
            _resolve_executable = None  # type: ignore[assignment]
    if _resolve_executable is not None:
        try:
            launcher, _ = _resolve_executable(argv[0])
            launcher = list(launcher)
        except Exception:  # noqa: BLE001 - fall back to the bare name
            launcher = [argv[0]]
    try:
        return subprocess.run(
            [*launcher, *argv[1:]],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            stdin=subprocess.DEVNULL,
            env=env,
        )
    except (OSError, subprocess.SubprocessError):
        return None


def _parse_model_listing(text: str) -> Optional[FrozenSet[str]]:
    """The slugs of one ``opencode models`` stdout, or ``None`` if it is not one.

    ``None`` — "this is not a listing" — for an empty stream, a stream that
    opens with a log line, or one whose non-blank lines are mostly not
    ``provider/model`` shaped. A parsed listing is never empty by construction.
    """
    lines = [line.strip() for line in (text or "").splitlines()]
    lines = [line for line in lines if line]
    if not lines or _LOG_LINE.match(lines[0]):
        return None
    slugs = [line for line in lines if _MODEL_SLUG.match(line)]
    if not slugs or len(slugs) * 2 < len(lines):
        return None
    return frozenset(slugs)


def _read_help_tokens(binary: str) -> frozenset:
    """The long options ``opencode run --help`` documents (§5.4.1's flag gate).

    **The last local copy.** This was a near-twin of the claude-code adapter's
    own sniff; M14 has since landed the shared gate
    (``base.read_help_tokens`` / ``LLMProvider.supports_flag``) and deleted the
    copies in ``claude_code.py`` and ``cursor_agent.py``, together with codex's
    prose exemption (now ``flags_verified_at_floor``). This one was outside that
    task's file set and so still stands. Folding it in is a two-line change —
    ``help_argv = ("run", "--help")`` on the adapter plus ``supports_flag``
    instead of the body below — and the only reason it is still here is
    ownership, not design.

    Failure posture — decline the *flag*, keep the *run*: a timeout, a non-zero
    exit, an unreadable stream or *anything else this probe can hit* resolves to
    the empty set, i.e. the flag is treated as unsupported and simply omitted.
    The `except` is deliberately total: a diagnostic read of a binary's own help
    text may not be the thing that ends a dispatch, and the worst outcome of
    declining is the reduced containment the caller is warned about.
    """
    cached = _HELP_TOKENS.get(binary)
    if cached is not None:
        return cached
    env = dict(os.environ)
    env["TERM"] = "dumb"
    env["COLUMNS"] = "1000"
    env["NO_COLOR"] = "1"
    tokens: frozenset = frozenset()
    try:
        completed = subprocess.run(
            [binary, "run", "--help"],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=5,
            env=env,
        )
        if completed.returncode == 0:
            text = f"{completed.stdout or ''}\n{completed.stderr or ''}"
            tokens = frozenset(_FLAG_TOKEN_RE.findall(text))
    except Exception:  # noqa: BLE001 - see the failure posture above
        tokens = frozenset()
    _HELP_TOKENS[binary] = tokens
    return tokens


_FLAG_TOKEN_RE = re.compile(r"--[A-Za-z0-9][A-Za-z0-9-]*")
_HELP_TOKENS: Dict[str, frozenset] = {}


class _UnreconstructibleProvider(Exception):
    """A slot's provider exists only in the config the redirect replaces."""


def _defines_an_implementation(block: Dict[str, Any]) -> bool:
    """True when a `provider.<name>` block supplies the provider *itself*.

    Deliberately narrow, because this is the only predicate that can produce a
    refusal and an over-broad one would refuse a working setup. Two shapes
    qualify, and they are the two that cannot be reconstructed once the user's
    config is out of reach: an ``npm`` SDK package, or an ``options.baseURL``
    pointing the provider at a server multi-llm has never heard of — the shape
    §2.3 measured on a real machine (a custom base URL with its own ``models``
    map and a live ``apiKey``).

    Everything else is an *override* of a provider opencode already has, and an
    override still resolves after the redirect; it merely loses the override. In
    particular a user who adds a model to a built-in provider — ``provider:
    {opencode: {models: {...}}}`` — is not declaring a new provider, and
    refusing them would be exactly the over-refusal this design forbids.
    """
    if block.get("npm"):
        return True
    options = block.get("options")
    return isinstance(options, dict) and bool(options.get("baseURL"))


def _user_config_paths() -> List[str]:
    """The user's own opencode config files, read from the *inherited* env.

    This runs before the redirect is applied to a child, so ``XDG_CONFIG_HOME``
    here is still the user's. ``OPENCODE_CONFIG`` (an explicit file path) is
    honoured because opencode honours it.
    """
    paths: List[str] = []
    explicit = os.environ.get("OPENCODE_CONFIG")
    if explicit:
        paths.append(os.path.expanduser(explicit))
    home = os.environ.get("XDG_CONFIG_HOME") or os.path.join(
        os.path.expanduser("~"), ".config"
    )
    for name in ("opencode.jsonc", "opencode.json"):
        paths.append(os.path.join(home, "opencode", name))
    return paths


# ─────────────────────────────────────────────────────────────────────────────
# §8 (plans/opencode-validator-false-rate-limit-and-denied-turn.md) — the
# resolved config, read through `opencode debug config`.
#
# `auth list` is structurally blind to a provider declared only in config (a
# custom `stub` with an inline key prints `0 credentials`, measured 1.18.32), and
# a Python read of the config files would have to re-implement opencode's whole
# layering: global json *and* jsonc, the project walk-up, `OPENCODE_CONFIG`,
# `OPENCODE_CONFIG_CONTENT`, `{env:}` substitution. `debug config` resolves every
# one of those layers the way the dispatch will, including the container
# wrapper, because it is spawned through the same PATH binary with the same env.
#
# Up to 1.18.32 it **printed secrets in plaintext** (an inline `options.apiKey`,
# a substituted `{env:}` value); 1.18.34 masks every present `apiKey` as `"***"`
# — an empty string and an unset `{env:}` reference included (measured
# 2026-10-02, `debug_config.1.18.34.json`). The stdout is still reduced in
# memory, inside :func:`_read_declared_providers`, to booleans and rule lists,
# and the raw text never leaves that function — not in a return value, not in
# a log line, not in an exception message: the reducer does not rely on the
# mask. What the mask costs: the printed value says only that a key is
# *declared* (``key_declared``), never that it *resolves*, so whether a
# built-in override's key reaches the child is read from the config sources
# themselves (:func:`_config_key_resolves`, below).
# ─────────────────────────────────────────────────────────────────────────────

#: `opencode [--pure] debug config` — "show resolved configuration". A `debug`
#: subcommand, so its shape is not a contract: every failure reads as "unknown"
#: and keeps the caller's pre-existing verdict. **Measured on the pinned
#: release** (`debug_config.<verified_version>.json`, re-captured at every
#: bump): `debug config` and `--pure debug config` both exit 0 with the same
#: `provider` shape, so the pin does not need the unknown-fallback — it stays as
#: defence. `--pure` means only "no external plugins"; it does not stop the
#: global config loading (the isolation is the hermetic redirect's).
DEBUG_CONFIG_ARGV: Tuple[str, ...] = ("opencode", "debug", "config")

#: The executor's probe ceiling (`subagent_executor._run_probe`), unchanged.
DEBUG_CONFIG_TIMEOUT_S = 30.0

#: The three permission actions opencode accepts.
PERMISSION_ACTIONS = ("allow", "deny", "ask")

#: The `external_directory` layers the reduction returns, in merge order: the
#: top-level `permission`, then `agent.plan.permission`, then
#: `agent.build.permission`.
EXTERNAL_DIR_TOP = "top"
EXTERNAL_DIR_LAYERS: Tuple[str, ...] = (EXTERNAL_DIR_TOP, READONLY_AGENT, WRITE_AGENT)


class ProviderDecl(NamedTuple):
    """One ``provider.<id>`` block, reduced to what the auth verdict reads.

    ``custom`` is :func:`_defines_an_implementation` (an ``npm`` package or an
    ``options.baseURL``); ``key_declared`` is a non-empty string
    ``options.apiKey`` as ``debug config`` prints it. On the pin that is
    ``"***"`` for every declared key — a literal, ``""``, an unset ``{env:}``
    reference alike — so it means "declared", never "resolves": the auth leg
    asks :func:`_config_key_resolves` for that. Never the key itself.
    """

    custom: bool
    key_declared: bool


class ExternalDirLayer(NamedTuple):
    """One layer's ``external_directory`` rules, normalized (T8.2).

    ``rules`` are ``(pattern, action)`` pairs in the config's own insertion
    order, catch-alls included (removing them is T4.7's job). A string value is
    one catch-all pair. ``malformed`` marks a shape opencode's rules cannot
    have; the whole layer is then dropped (``rules=()``), because dropping one
    deny exception while keeping the allow it narrows would broaden the user's
    rules. Path globs, not secrets.
    """

    rules: Tuple[Tuple[str, str], ...] = ()
    malformed: bool = False


class DeclaredConfig(NamedTuple):
    """What :func:`_read_declared_providers` keeps of a ``debug config`` run.

    ``providers`` is ``None`` when the ``provider`` value is not a mapping
    ("unknown"); an absent ``provider`` key is ``{}`` (nothing declared), which
    reaches the same auth verdict. ``external_directory`` holds one
    :class:`ExternalDirLayer` per :data:`EXTERNAL_DIR_LAYERS` name.
    """

    providers: Optional[Dict[str, ProviderDecl]]
    external_directory: Dict[str, ExternalDirLayer]


def _opencode_launcher(binary: str) -> List[str]:
    """``binary`` resolved the way ``_list_models`` and the executor resolve it."""
    try:  # pragma: no cover - import shim mirrors the rest of utils/
        from ..llm_client import _resolve_executable
    except ImportError:  # pragma: no cover - direct-script import shim
        try:
            from utils.llm_client import _resolve_executable  # type: ignore
        except ImportError:
            return [binary]
    try:
        launcher, _ = _resolve_executable(binary)
        return list(launcher)
    except Exception:  # noqa: BLE001 - fall back to the bare name
        return [binary]


def _spawn_debug_config(
    argv: List[str],
    env: Optional[Mapping[str, str]],
    cwd: Optional[str],
    timeout: float,
) -> Optional["subprocess.CompletedProcess"]:
    """Run ``debug config`` with the executor's probe pins, or ``None``.

    ``stdin=DEVNULL``, captured text, a hard timeout, and ``None`` on any
    ``OSError``/``SubprocessError`` (a ``TimeoutExpired`` is one). ``env`` of
    ``None`` inherits this process's environment. The one seam tests patch.
    """
    try:
        return subprocess.run(
            [*_opencode_launcher(argv[0]), *argv[1:]],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            stdin=subprocess.DEVNULL,
            env=dict(env) if env is not None else None,
            cwd=cwd,
        )
    except (OSError, subprocess.SubprocessError):
        return None


def _provider_decl(block: Dict[str, Any]) -> ProviderDecl:
    options = block.get("options")
    key = options.get("apiKey") if isinstance(options, dict) else None
    return ProviderDecl(
        custom=_defines_an_implementation(block),
        key_declared=isinstance(key, str) and bool(key.strip()),
    )


def _action_or_none(value: Any) -> Optional[str]:
    return value if isinstance(value, str) and value in PERMISSION_ACTIONS else None


def _external_dir_layer(permission: Any) -> ExternalDirLayer:
    """Normalize one layer's ``permission`` value to its ``external_directory``.

    * absent (``None``, or no ``external_directory`` key): ``rules=()``;
    * the whole ``permission`` a valid action string (it applies to every
      tool): one catch-all pair ``("*", action)``;
    * ``external_directory`` a valid action string: the same catch-all pair;
    * ``external_directory`` a map of pattern → valid action: its pairs, in
      insertion order;
    * anything else: ``rules=()``, ``malformed=True``.

    Permission-level keys other than ``external_directory`` (a permission-level
    ``"*"`` included) are ignored.
    """
    if permission is None:
        return ExternalDirLayer()
    if isinstance(permission, str):
        action = _action_or_none(permission)
        if action is None:
            return ExternalDirLayer(malformed=True)
        return ExternalDirLayer(rules=(("*", action),))
    if not isinstance(permission, dict):
        return ExternalDirLayer(malformed=True)
    if "external_directory" not in permission:
        return ExternalDirLayer()
    value = permission["external_directory"]
    if isinstance(value, str):
        action = _action_or_none(value)
        if action is None:
            return ExternalDirLayer(malformed=True)
        return ExternalDirLayer(rules=(("*", action),))
    if isinstance(value, dict):
        rules: List[Tuple[str, str]] = []
        for pattern, rule in value.items():
            action = _action_or_none(rule)
            if not isinstance(pattern, str) or action is None:
                return ExternalDirLayer(malformed=True)
            rules.append((pattern, action))
        return ExternalDirLayer(rules=tuple(rules))
    return ExternalDirLayer(malformed=True)


def _reduce_debug_config(text: str) -> Optional[DeclaredConfig]:
    """``debug config`` stdout → :class:`DeclaredConfig`, or ``None``.

    ``None`` for anything that is not one JSON object. The parse error is
    caught **without** its message: a ``JSONDecodeError`` quotes the document
    it failed on, and this document carries plaintext keys. ``json.loads``
    keeps insertion order and nothing here sorts, so the rule order opencode
    printed (merge order, measured) survives.
    """
    try:
        document = json.loads(text or "")
    except (ValueError, RecursionError):
        return None
    if not isinstance(document, dict):
        return None
    raw_providers = document.get("provider", {})
    providers: Optional[Dict[str, ProviderDecl]] = None
    if isinstance(raw_providers, dict):
        providers = {
            str(provider_id): _provider_decl(block)
            for provider_id, block in raw_providers.items()
            if isinstance(block, dict)
        }
    agents = document.get("agent")
    agents = agents if isinstance(agents, dict) else {}
    layers: Dict[str, ExternalDirLayer] = {
        EXTERNAL_DIR_TOP: _external_dir_layer(document.get("permission")),
    }
    for name in (READONLY_AGENT, WRITE_AGENT):
        agent = agents.get(name)
        permission = agent.get("permission") if isinstance(agent, dict) else None
        layers[name] = _external_dir_layer(permission)
    return DeclaredConfig(providers=providers, external_directory=layers)


def _read_declared_providers(
    env: Optional[Mapping[str, str]],
    cwd: Optional[str],
    pure: bool,
    *,
    timeout: Optional[float] = None,
) -> Optional[DeclaredConfig]:
    """Run ``opencode [--pure] debug config`` and reduce it in memory (T8.2).

    ``env``/``cwd``/``pure`` are the dispatch's own (the caller builds them);
    ``env=None`` inherits this process's environment. ``timeout`` is what is
    left of a caller's deadline: it replaces the 30 s ceiling with
    ``min(30, timeout)``, and at ``<= 0`` nothing is spawned.

    ``None`` on **any** failure — spawn error, timeout, non-zero exit, non-JSON
    — which every caller reads as "unknown" and which therefore keeps that
    caller's pre-existing verdict: a debug-config problem can never turn a
    refusal into a pass. The raw stdout never leaves this function.
    """
    if timeout is None:
        budget = DEBUG_CONFIG_TIMEOUT_S
    else:
        if timeout <= 0:
            return None
        budget = min(DEBUG_CONFIG_TIMEOUT_S, float(timeout))
    argv = [DEBUG_CONFIG_ARGV[0], *([PURE_FLAG] if pure else []), *DEBUG_CONFIG_ARGV[1:]]
    try:
        completed = _spawn_debug_config(argv, env, cwd, budget)
    except (OSError, ValueError, TypeError, subprocess.SubprocessError):
        # `_spawn_debug_config` already maps OSError/SubprocessError to None;
        # this only covers a bad env/cwd value. Deliberately narrow: a test
        # tripwire raising AssertionError must surface, not read as a failure.
        return None
    if completed is None or completed.returncode != 0:
        return None
    return _reduce_debug_config(completed.stdout or "")


# ─────────────────────────────────────────────────────────────────────────────
# T8.3 — where a masked `apiKey` comes from, and whether the child resolves it.
#
# `debug config` prints every string under an `apiKey` key as `"***"` on the
# pin (the bundle's `debug config` handler masks any key matching
# /api.?key|secret|password|…/i), so it can say a built-in override declares a
# key but not whether that key reaches the dispatch: `{env:VAR}` with VAR
# unset, or dropped by `env_allowlist`/a host guard, prints exactly like a live
# literal. The reference is therefore read from the config sources the child
# loads, located through the **child's** env, and evaluated the way opencode's
# own `ConfigVariable.substitute` evaluates it: `{env:VAR}` → that variable or
# `""`; `{file:PATH}` → the trimmed file, PATH relative to the layer's own
# directory (`cwd` for `OPENCODE_CONFIG_CONTENT`), `~/` → `$HOME`.
#
# The layer order is MEASURED on 1.18.34 (2026-10-02: the real binary from a
# scratch HOME, every layer setting its own `provider.openrouter.options.timeout`,
# the printed winner removed until none was left), lowest precedence first:
#
#   1. the global directory, `$XDG_CONFIG_HOME/opencode/` (else
#      `~/.config/opencode/`): `config.json`, `opencode.json`, `opencode.jsonc`;
#   2. `$OPENCODE_CONFIG`;
#   3. project files, from the worktree root (the nearest `.git`, else `/`) down
#      to `cwd`, `opencode.json` then `opencode.jsonc` in each directory;
#   4. `opencode.json` then `opencode.jsonc` in every `.opencode` directory from
#      `cwd` UP to the worktree root (so the shallowest one wins), then
#      `~/.opencode/` (`$OPENCODE_TEST_HOME/.opencode/` when set, which is
#      how a hermetic slot closes it), then `$OPENCODE_CONFIG_DIR`;
#   5. `$OPENCODE_CONFIG_CONTENT`;
#   6. the managed directory (`/etc/opencode` on Linux).
#
# `OPENCODE_DISABLE_PROJECT_CONFIG` (`1`/`true`, case-folded) drops 3 and the
# `.opencode` walk of 4, and keeps `~/.opencode/` and `$OPENCODE_CONFIG_DIR`.
# Merging is deep, so a later layer that names the provider without `apiKey`
# hides nothing. Two remote layers (a `.well-known` org config, an account's
# console config) cannot be read from here: a key only they supply finds no
# reference and keeps the `not_authenticated` refusal. A `{file:}` is stat'ed,
# never read, and an `{env:}` value is only tested for emptiness: no key value
# is returned, logged or raised.
# ─────────────────────────────────────────────────────────────────────────────

#: opencode's own substitution syntax (`ConfigVariable.substitute`, 1.18.34).
_ENV_REFERENCE = re.compile(r"\{env:([^}]+)\}")
_FILE_REFERENCE = re.compile(r"\{file:([^}]+)\}")

#: opencode reads the managed directory from this variable before the platform
#: default (its own test seam, honoured because the binary honours it).
MANAGED_CONFIG_DIR_ENV = "OPENCODE_TEST_MANAGED_CONFIG_DIR"


class _LayerUnreadable(Exception):
    """A config layer exists but this read cannot parse it."""


def _flag_on(value: Optional[str]) -> bool:
    """opencode's boolean flag reader: ``"1"`` or ``"true"``, case-folded."""
    return (value or "").strip().lower() in ("1", "true")


def _managed_config_dir(env: Mapping[str, str]) -> str:
    override = env.get(MANAGED_CONFIG_DIR_ENV)
    if override:
        return override
    if sys.platform == "darwin":
        return "/Library/Application Support/opencode"
    if sys.platform == "win32":
        return os.path.join(env.get("ProgramData") or "C:\\ProgramData", "opencode")
    return "/etc/opencode"


def _walk_up(start: str, stop: Optional[str]) -> List[str]:
    """``start`` and each parent, deepest first, ending at ``stop`` (or ``/``)."""
    chain: List[str] = []
    here = start
    while True:
        chain.append(here)
        if here == stop:
            return chain
        parent = os.path.dirname(here)
        if parent == here:
            return chain
        here = parent


def _worktree_root(start: str) -> Optional[str]:
    """The nearest directory at or above ``start`` holding ``.git``, else None."""
    for here in _walk_up(start, None):
        if os.path.exists(os.path.join(here, ".git")):
            return here
    return None


def _config_layers(
    env: Mapping[str, str], cwd: str
) -> List[Tuple[Optional[str], Optional[str], str]]:
    """``(path, inline text, base dir)`` per local layer, lowest precedence first.

    Exactly one of ``path``/``inline text`` is set; ``base dir`` is where a
    relative ``{file:}`` in that layer resolves.
    """
    home = env.get("HOME") or os.path.expanduser("~")
    xdg_config = env.get("XDG_CONFIG_HOME") or os.path.join(home, ".config")
    global_dir = os.path.join(xdg_config, "opencode")
    layers: List[Tuple[Optional[str], Optional[str], str]] = []

    def add(path: str) -> None:
        layers.append((path, None, os.path.dirname(path)))

    for name in ("config.json", "opencode.json", "opencode.jsonc"):
        add(os.path.join(global_dir, name))
    explicit = env.get("OPENCODE_CONFIG")
    if explicit:
        add(os.path.join(cwd, explicit))
    project = not _flag_on(env.get(PROJECT_CONFIG_ENV))
    walk = _walk_up(cwd, _worktree_root(cwd))
    if project:
        for directory in reversed(walk):
            for name in ("opencode.json", "opencode.jsonc"):
                add(os.path.join(directory, name))
    config_dir = env.get("OPENCODE_CONFIG_DIR") or None
    directories = [global_dir]
    if project:
        directories += [
            os.path.join(d, ".opencode") for d in walk
            if os.path.isdir(os.path.join(d, ".opencode"))
        ]
    opencode_home = env.get(HOME_DIR_ENV) or home
    if os.path.isdir(os.path.join(opencode_home, ".opencode")):
        directories.append(os.path.join(opencode_home, ".opencode"))
    if config_dir:
        directories.append(config_dir)
    for directory in dict.fromkeys(directories):
        if directory.endswith(".opencode") or directory == config_dir:
            for name in ("opencode.json", "opencode.jsonc"):
                add(os.path.join(directory, name))
    content = env.get("OPENCODE_CONFIG_CONTENT")
    if content:
        layers.append((None, content, cwd))
    for name in ("opencode.json", "opencode.jsonc"):
        add(os.path.join(_managed_config_dir(env), name))
    return layers


def _read_layer(path: Optional[str], inline: Optional[str]) -> Optional[Dict[str, Any]]:
    """One layer's document; ``None`` when the file does not exist.

    Raises :class:`_LayerUnreadable` for a layer that exists but cannot be
    parsed here. The text is never quoted: a ``ValueError`` from ``json``
    carries the document it failed on, and this document may carry a key.
    """
    text = inline
    if path is not None:
        if not os.path.isfile(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as handle:
                text = handle.read()
        except (OSError, ValueError):
            raise _LayerUnreadable() from None
    if not (text or "").strip():
        return {}
    try:
        document = json.loads(strip_jsonc(text or ""))
    except (ValueError, RecursionError):
        raise _LayerUnreadable() from None
    if not isinstance(document, dict):
        raise _LayerUnreadable()
    return document


def _api_key_reference(
    prefix: str, env: Mapping[str, str], cwd: str
) -> Optional[Tuple[str, str]]:
    """``(raw apiKey, base dir)`` from the winning local layer, or ``None``.

    The winner is the highest-precedence layer that sets
    ``provider.<prefix>.options.apiKey``. ``None`` when no local layer sets
    it, when it is not a string, or when a layer above it cannot be read.
    """
    try:
        for path, inline, base in reversed(_config_layers(env, cwd)):
            document = _read_layer(path, inline)
            if not document:
                continue
            providers = document.get("provider")
            block = providers.get(prefix) if isinstance(providers, dict) else None
            options = block.get("options") if isinstance(block, dict) else None
            if isinstance(options, dict) and "apiKey" in options:
                key = options["apiKey"]
                return (key, base) if isinstance(key, str) else None
    except _LayerUnreadable:
        return None
    return None


def _api_key_resolves(raw: str, base: str, env: Mapping[str, str]) -> bool:
    """Whether ``raw`` is a non-empty key once opencode substitutes it in ``env``.

    A ``{file:}`` counts when it names a readable, non-empty regular file; it
    is never opened (a whitespace-only file, which opencode trims to empty,
    therefore counts — the one shape this over-admits).
    """
    home = env.get("HOME") or os.path.expanduser("~")
    text = _ENV_REFERENCE.sub(lambda match: env.get(match.group(1)) or "", raw)

    def file_reference(match: "re.Match[str]") -> str:
        target = match.group(1)
        if target.startswith("~/"):
            target = os.path.join(home, target[2:])
        target = os.path.normpath(os.path.join(base, target))
        try:
            info = os.stat(target)
        except (OSError, ValueError):
            return ""
        if not stat.S_ISREG(info.st_mode) or info.st_size == 0:
            return ""
        return "x" if os.access(target, os.R_OK) else ""

    return bool(_FILE_REFERENCE.sub(file_reference, text).strip())


def _config_key_resolves(
    prefix: str, env: Optional[Mapping[str, str]], cwd: Optional[str]
) -> bool:
    """T8.3: the config's ``apiKey`` for ``prefix`` resolves in the child's env.

    ``env`` is the child's whole environment (``None`` = this process's, which
    the child then inherits); ``cwd`` the dispatch's (``None`` = this
    process's). ``False`` whenever the reference cannot be found or read.
    """
    source: Mapping[str, str] = os.environ if env is None else env
    try:
        where = os.path.abspath(cwd or os.getcwd())
    except OSError:
        return False
    found = _api_key_reference(prefix, source, where)
    return found is not None and _api_key_resolves(found[0], found[1], source)


_USER_CONFIG_LOCK = threading.Lock()
_USER_CONFIG_MEMO: Dict[str, Optional[DeclaredConfig]] = {}


def _user_config_memo_key(cwd: Optional[str]) -> str:
    """The memo key: the variables that change what the user's resolved config
    is, plus ``cwd`` (the project layer). Hashed, because an inherited
    ``OPENCODE_CONFIG_CONTENT`` may hold a key. Literal reads, one per name, so
    the packaging's environment-read walk can resolve each."""
    import hashlib

    try:
        where = os.path.abspath(cwd or os.getcwd())
    except OSError:
        where = ""
    material = json.dumps([
        os.environ.get("HOME"),
        os.environ.get("XDG_CONFIG_HOME"),
        os.environ.get("OPENCODE_CONFIG"),
        os.environ.get("OPENCODE_CONFIG_DIR"),
        os.environ.get("OPENCODE_CONFIG_CONTENT"),
        os.environ.get("OPENCODE_DISABLE_PROJECT_CONFIG"),
        os.environ.get("OPENCODE_PERMISSION"),
        where,
    ])
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def read_user_declared_config(
    *, cwd: Optional[str] = None, timeout: Optional[float] = None
) -> Optional[DeclaredConfig]:
    """The **user's own** resolved config: ``debug config`` with no hermetic delta.

    What "the user's config" means to :func:`_user_defines_provider` (T8.5),
    to ``doctor``'s ``config-only`` leg (T8.6) and to the write profile's
    allow-pattern preservation (T4.7): this process's inherited environment,
    no ``--pure``, ``cwd`` for the project layer (``None`` = this process's).

    Memoised per process, keyed on the config-locating variables and ``cwd``:
    the spawn costs ~0.5 s and prints secrets, so it must not run per dispatch.
    Concurrent first callers share one read (the fill runs under a lock). A
    failed read is cached too. A read bounded by an explicit ``timeout`` (a
    caller's shrinking deadline) is served from the memo when there is one and
    is never itself cached, so a budget-starved miss cannot poison a later
    unbounded read. A mid-run edit of ``opencode.json`` stays unseen for the
    rest of the process; that is accepted.
    """
    key = _user_config_memo_key(cwd)
    with _USER_CONFIG_LOCK:
        if key in _USER_CONFIG_MEMO:
            return _USER_CONFIG_MEMO[key]
        result = _read_declared_providers(None, cwd, False, timeout=timeout)
        if timeout is None:
            _USER_CONFIG_MEMO[key] = result
        return result


# ─────────────────────────────────────────────────────────────────────────────
# T4.7 — the rows over the user's own config (plan §4.4 steps 2-3).
# ─────────────────────────────────────────────────────────────────────────────

#: `external_directory` patterns that match every path. Never re-listed after
#: our `"*": "deny"`: a catch-all allow there would re-open every external
#: read, and a catch-all deny/ask is our leading deny already.
CATCH_ALL_PATTERNS = frozenset({"*", "**", "/*", "/**"})

#: The layers each agent's rules are read from, in the order opencode evaluates
#: them: the top-level `permission`, then `agent.<agent>.permission`.
_LAYERS_BY_AGENT: Dict[str, Tuple[str, str]] = {
    READONLY_AGENT: (EXTERNAL_DIR_TOP, READONLY_AGENT),
    WRITE_AGENT: (EXTERNAL_DIR_TOP, WRITE_AGENT),
}


def relisted_external_rules(
    declared: Optional[DeclaredConfig], agent: str
) -> List[Tuple[str, str]]:
    """The user's ``external_directory`` rules to re-list after our deny (§4.4 step 3).

    ``declared`` is :func:`read_user_declared_config`'s result (the user's own
    resolved config, no hermetic delta). The effective ordered list is the
    top-level rules, then ``agent.<agent>.permission``'s (``agent.build`` is never
    read into the ``plan`` list, nor the reverse); a pattern in both keeps only
    its later occurrence, at that later position, because opencode's ruleset is
    ``findLast``. Then, walking that list in order:

    * a **catch-all** (:data:`CATCH_ALL_PATTERNS`) is never re-listed. A
      catch-all ``deny``/``ask`` shadows every entry before it, so those are
      dropped too (re-listing an earlier allow would broaden the user's rules).
      A catch-all ``allow`` is overridden by design — it is the row ours win on
      — and WARNs once, naming the row but no path;
    * every other entry is kept in order, ``ask`` turned into ``deny`` (a
      ``deny`` returns to the model; an ``ask`` ends the turn under ``run``), so
      a user deny exception still follows the allow it narrows.

    A malformed layer contributes nothing and WARNs once. ``declared`` of
    ``None`` (the read failed) returns ``[]`` with one WARN: the fail-safe is
    our deny alone. Path globs, never secrets, so none of this is sensitive —
    but the WARNs still quote no path.
    """
    if declared is None:
        _warn_once(
            "external-rules-unread",
            "multi-llm warning: opencode's resolved config could not be read "
            "(`opencode debug config` failed), so your own external_directory "
            "rules are not preserved on this run: every path outside the "
            "working directory is denied to the model (fail-safe).",
        )
        return []
    effective: Dict[str, str] = {}
    for layer_name in _LAYERS_BY_AGENT.get(agent, (EXTERNAL_DIR_TOP,)):
        layer = declared.external_directory.get(layer_name) or ExternalDirLayer()
        if layer.malformed:
            where = "top-level permission" if layer_name == EXTERNAL_DIR_TOP else (
                f"agent.{layer_name}.permission"
            )
            _warn_once(
                f"external-rules-malformed:{layer_name}",
                f"multi-llm warning: the external_directory rule in your opencode "
                f"config's {where} has a shape multi-llm cannot re-list, so that "
                f"layer's rules are not preserved (fail-safe: denied to the model).",
            )
            continue
        for pattern, action in layer.rules:
            effective.pop(pattern, None)
            effective[pattern] = action
    kept: Dict[str, str] = {}
    for pattern, action in effective.items():
        if pattern in CATCH_ALL_PATTERNS:
            if action == "allow":
                _warn_once(
                    "external-rules-catch-all",
                    "multi-llm warning: your opencode config allows every "
                    "external directory (a catch-all external_directory allow); "
                    "multi-llm's deny row overrides it on this dispatch, and only "
                    "your specific directory rules are kept.",
                )
            else:
                kept.clear()
            continue
        kept[pattern] = "deny" if action == "ask" else action
    return list(kept.items())


def _external_directory_map(
    agent: str,
    user_rules: List[Tuple[str, str]],
    env: Optional[Mapping[str, str]],
) -> Dict[str, str]:
    """``{"*": "deny"}``, the built-in allows it shadows, then the user's rules.

    Built-in first, then the user's (§4.2 step 1): a user pattern equal to a
    built-in one is moved to its own position with its own action.
    """
    rules = dict(permission_block(agent, env)["external_directory"])
    for pattern, action in user_rules:
        rules.pop(pattern, None)
        rules[pattern] = action
    return rules


#: A second permission key our ``external_directory`` list is repeated under,
#: last in the agent's ``permission`` map (T4.7, non-hermetic delivery only).
#:
#: Re-ordering the map we emit does not re-order the merged one: opencode
#: deep-merges ``OPENCODE_CONFIG_CONTENT`` over the user's config *files*, and a
#: key a file already holds keeps the file's position (§4.1). So with a file's
#: own ``agent.<name>.permission`` in force, the real ``external_directory`` key
#: can lose twice: its user patterns (``"/shared/*": "allow"``) stay ahead of
#: our appended ``"*": "deny"`` and are shadowed by it (rig
#: ``useragent_relist_ctrl_*``), and a file's permission-level ``"*": "allow"``
#: after the key stays after it and beats our deny (rig
#: ``useragent_ustar_ctrl_*``). opencode matches a rule's *permission* as a
#: wildcard too (``Permission.evaluate``: ``Wildcard.match(permission,
#: rule.permission)``, read from the 1.18.32 binary), so this key matches every
#: ``external_directory`` request, and because no config file has it, it is a
#: new key that lands after every file key, with its patterns in our order
#: (rigs ``useragent_relist_*`` and ``useragent_ustar_*``). The rows stay under
#: the real key as well, where the hermetic delivery and every earlier rig case
#: put them. A config file that itself uses this key is not handled.
TRAILING_EXTERNAL_KEY = "external_directory*"

#: The non-catch-all ``read`` patterns that match an ``.env.example`` file, for
#: :func:`_merge_rows_into`'s decision on our ``*.env.example`` allow.
_ENV_EXAMPLE_MATCHES = frozenset({"*.env.example", "*.env.*"})


def _merge_rows_into(
    permission: Dict[str, Any], agent: str, external: Dict[str, str]
) -> None:
    """Put our three rows at the END of one agent's ``permission`` map, in place.

    At the end, because a permission-level ``"*"`` key in the same layer (the
    q2_ustar shape one level down) would otherwise follow our rows and beat
    them. ``external_directory`` and ``doom_loop`` are replaced outright (ours
    win on those rows). ``read`` keeps the user's own rules: ours are appended
    after them, the ``.env`` denies and then our ``*.env.example`` allow — the
    same rows a user with no read rules gets, so an unrelated user rule (say
    ``{"/secret/*": "deny"}``) does not leave our ``*.env.*`` deny as the last
    match for ``.env.example``. The allow is left out only when the user's own
    rules already deny (or ask for) the example file — the last of their
    ``*.env.example``, ``*.env.*`` or catch-all rules is not an allow — since
    appending an allow after that would broaden it.

    The ``external_directory`` list is then repeated under
    :data:`TRAILING_EXTERNAL_KEY`, the last key, so that its precedence holds
    in the *merged* config too, where a config file's own keys keep their
    earlier positions.
    """
    rows = permission_block(agent)
    permission.pop("external_directory", None)
    permission.pop(TRAILING_EXTERNAL_KEY, None)
    existing_read = permission.pop("read", None)
    permission.pop("doom_loop", None)
    permission["external_directory"] = external
    if existing_read is None:
        permission["read"] = rows["read"]
    else:
        if isinstance(existing_read, dict):
            read = dict(existing_read)
        elif isinstance(existing_read, str):
            read = {"*": existing_read}
        else:
            read = {}
        # What the user's own rules decide for `.env.example` (findLast over
        # the patterns that match it), read before ours are appended.
        example_rule = None
        for pattern, action in read.items():
            if pattern in _ENV_EXAMPLE_MATCHES or pattern in CATCH_ALL_PATTERNS:
                example_rule = action
        keep_example_allow = example_rule is None or example_rule == "allow"
        for pattern, action in rows["read"].items():
            if action == "allow" and not keep_example_allow:
                continue
            read.pop(pattern, None)
            read[pattern] = action
        permission["read"] = read
    permission["doom_loop"] = rows["doom_loop"]
    permission[TRAILING_EXTERNAL_KEY] = dict(external)


def _parse_inherited_content(value: Optional[str]) -> Tuple[Optional[Dict[str, Any]], str]:
    """``(document, "")`` or ``(None, <failure kind>)``; ``({}, "")`` when unset.

    The failure kind is a fixed phrase. The value's bytes are never quoted —
    an inherited ``OPENCODE_CONFIG_CONTENT`` can carry an inline ``apiKey`` —
    and neither is a ``JSONDecodeError``'s message, which quotes the document.
    """
    if value is None or not value.strip():
        return {}, ""
    try:
        document = json.loads(value)
    except (ValueError, RecursionError):
        return None, "it is not valid JSON"
    if not isinstance(document, dict):
        return None, "it is not a JSON object"
    return document, ""


def merge_permission_content(
    inherited: Optional[str],
    agent: str,
    external: Dict[str, str],
    *,
    continue_loop: bool = False,
) -> Optional[str]:
    """Our rows deep-merged **over** the inherited ``OPENCODE_CONFIG_CONTENT`` (T4.7).

    The user's keys are kept; ours win only on the three rows under
    ``agent.<agent>.permission`` (plus ``experimental.continue_loop_on_deny``
    when ``continue_loop``). ``None`` means "emit nothing": the inherited value
    is not a JSON object (or its ``agent`` section is not a mapping) and is
    passed through untouched, with one WARN naming the variable and the failure
    kind only.
    """
    document, failure = _parse_inherited_content(inherited)
    agents = document.get("agent", {}) if document is not None else None
    if document is not None and not isinstance(agents, dict):
        document, failure = None, "its `agent` value is not an object"
    if document is None:
        _warn_once(
            "inherited-content-unparseable",
            f"multi-llm warning: the inherited OPENCODE_CONFIG_CONTENT is passed "
            f"through untouched because {failure}; the opencode permission deny "
            f"rows are not added to it, so a refused permission can still end a "
            f"turn early.",
        )
        return None
    document.setdefault("$schema", "https://opencode.ai/config.json")
    agents = document.setdefault("agent", {})
    section = agents.get(agent)
    if not isinstance(section, dict):
        section = {}
        agents[agent] = section
    permission = section.get(_PERMISSION_KEY)
    if isinstance(permission, str):
        permission = {"*": permission}
    elif not isinstance(permission, dict):
        permission = {}
    section[_PERMISSION_KEY] = permission
    _merge_rows_into(permission, agent, external)
    if continue_loop:
        experimental = document.get("experimental")
        if not isinstance(experimental, dict):
            experimental = {}
        experimental["continue_loop_on_deny"] = True
        document["experimental"] = experimental
    return _dump_config(document)


#: Project-layer config names opencode picks up while walking up from ``cwd``.
_PROJECT_CONFIG_NAMES = (
    "opencode.json",
    "opencode.jsonc",
    os.path.join(".opencode", "opencode.json"),
    os.path.join(".opencode", "opencode.jsonc"),
)


def _user_config_files_conclusive() -> bool:
    """True when :func:`_user_defines_provider_from_files` sees every layer.

    The file read is exact only for the plain case: no ``OPENCODE_CONFIG*``
    variable (an explicit file, dir or inline content opencode layers in), no
    global ``opencode.jsonc`` or ``config.json`` (``json.load`` cannot read the
    first and the file read does not look at the second), every global
    ``opencode.json`` that exists parses as JSON, no ``~/.opencode/`` config
    (a layer the user's own runs load and a hermetic slot does not), and no
    project config on the walk up from this process's ``cwd`` (unless opencode
    is told to skip that layer). Anything else is inconclusive and needs
    ``debug config``.
    """
    # Literal reads, one per name, so the packaging's env-read walk resolves each.
    if (
        os.environ.get("OPENCODE_CONFIG")
        or os.environ.get("OPENCODE_CONFIG_DIR")
        or os.environ.get("OPENCODE_CONFIG_CONTENT")
    ):
        return False
    home = os.environ.get("XDG_CONFIG_HOME") or os.path.join(
        os.path.expanduser("~"), ".config"
    )
    base = os.path.join(home, "opencode")
    for name in ("opencode.jsonc", "config.json"):
        if os.path.exists(os.path.join(base, name)):
            return False
    opencode_home = os.environ.get(HOME_DIR_ENV) or os.path.expanduser("~")
    for name in ("opencode.json", "opencode.jsonc"):
        if os.path.exists(os.path.join(opencode_home, ".opencode", name)):
            return False
    plain = os.path.join(base, "opencode.json")
    if os.path.exists(plain):
        try:
            with open(plain, "r", encoding="utf-8") as handle:
                json.load(handle)
        except (OSError, ValueError, RecursionError):
            return False
    if os.environ.get("OPENCODE_DISABLE_PROJECT_CONFIG"):
        return True
    try:
        where = os.path.abspath(os.getcwd())
    except OSError:
        return False
    while True:
        for name in _PROJECT_CONFIG_NAMES:
            if os.path.exists(os.path.join(where, name)):
                return False
        parent = os.path.dirname(where)
        if parent == where:
            return True
        where = parent


def _user_defines_provider(prefix: str) -> bool:
    """True when the user's own opencode config *defines* this provider.

    When the config files alone answer it (:func:`_user_config_files_conclusive`:
    only a plain global ``opencode.json``, no ``OPENCODE_CONFIG*``, no project
    config), the answer is the file read and **nothing is spawned** — this is
    reached by §8's structural leg, Lane A ``generate`` slots and the
    ``--dry-run-subagents`` renderer, none of which should pay for a spawn.

    Otherwise it is read through ``opencode debug config``
    (:func:`read_user_declared_config`, T8.5), which parses a commented
    ``opencode.jsonc`` and every other layer exactly as opencode does; the
    ``json.load`` this used to rely on raised on one, read it as "not
    defined", and let a hermetic slot dispatch into the silent
    model-resolution failure the refusal exists to prevent.

    When that read fails (no binary, a timeout, a shape it cannot reduce), the
    answer falls back to the previous file read, :func:`_user_defines_provider_from_files`
    — so a reader failure never changes today's verdict, and an unreadable or
    unparseable config still answers ``False`` (dispatch, don't refuse).
    """
    if _user_config_files_conclusive():
        return _user_defines_provider_from_files(prefix)
    declared = read_user_declared_config()
    if declared is not None and declared.providers is not None:
        decl = declared.providers.get(prefix)
        return bool(decl is not None and decl.custom)
    return _user_defines_provider_from_files(prefix)


def _user_defines_provider_from_files(prefix: str) -> bool:
    """The file-based fallback of :func:`_user_defines_provider`.

    Deliberately narrow. An unreadable or unparseable config answers ``False``
    (dispatch, don't refuse) — a config problem may never become a refusal, the
    same rule the structural model check follows. So does a block that only
    overrides a provider opencode already has: see
    :func:`_defines_an_implementation`.
    """
    for path in _user_config_paths():
        try:
            with open(path, "r", encoding="utf-8") as handle:
                document = json.load(handle)
        except (OSError, ValueError):
            continue
        if not isinstance(document, dict):
            continue
        providers = document.get("provider")
        if not isinstance(providers, dict):
            continue
        block = providers.get(prefix)
        if isinstance(block, dict) and _defines_an_implementation(block):
            return True
    return False


def reset_hermetic_state() -> None:
    """Forget the memoised help read, Lane A's version read, the user-config
    read and the warn-once set (tests only)."""
    _HELP_TOKENS.clear()
    with _WARNED_LOCK:
        _WARNED.clear()
    with _LANE_A_VERSION_LOCK:
        _LANE_A_VERSION.clear()
    with _USER_CONFIG_LOCK:
        _USER_CONFIG_MEMO.clear()


class _OpenCodeText(NamedTuple):
    """What :meth:`OpenCodeProvider._scan_text_parts` collected."""

    #: Every text part's text, in stream order (``parse_output``'s input).
    parts: List[str]
    #: The text parts of the last assistant message, in order (salvage's).
    last_message: List[str]
    #: Whether any line was one of ``OpenCodeProvider._EVENT_TYPES``.
    saw_event: bool


class OpenCodeProvider(LLMProvider):
    """Provider for OpenCode CLI tool.

    OpenCode outputs NDJSON (newline-delimited JSON) events when using
    --format json. The top-level event types are ``step_start``,
    ``step_finish``, ``tool_use``, ``text``, ``reasoning`` (only with
    ``--thinking``, which this adapter never passes) and ``error``; each
    carries a ``part`` object except ``error``, which carries ``error``.
    The actual LLM response is in the "text" events' part.text field.

    Model strings support an optional ``model[:effort]`` suffix (e.g.
    ``openai/gpt-5.5:high``), translated to ``--variant <effort>``. Valid
    efforts are listed in REASONING_EFFORTS; anything else passes through
    verbatim as the model name.
    """

    # `opencode run` reads the message from stdin when no message argument is
    # given, so this adapter has a real non-argv transport (D2d). The fan-out
    # default stays "argv"; materialized prompts use stdin.
    supported_prompt_transports = ("argv", "stdin")

    # Subagent-runner declarations (D3e/D3j/D3m).
    agent_profiles = (PROFILE_GENERATE, PROFILE_AGENT_READONLY, PROFILE_AGENT_WRITE)
    supports_file_edits = True
    supports_workspace_reads = True
    usage_support = USAGE_FULL
    # `opencode auth list` prints the credentials it has stored (and nothing
    # else): no model call, no session, so it is the cheap non-generating probe
    # the once-per-run auth preflight needs (D3c). It is blind to a provider
    # declared only in config (measured 1.18.32: `0 credentials`), so on its
    # `False` the preflight asks `config_credential_source`, which reads the
    # dispatch's own resolved config: a custom provider declared there passes
    # whether its key is in auth.json under the custom id, in an `{env:}`
    # reference, or absent (keyless); a built-in override passes only when its
    # config key resolves in the dispatch's env. A built-in with no key
    # anywhere, or one that does not resolve, is still refused (plan §8).
    auth_check = ("opencode", "auth", "list")
    login_cmd = "opencode auth login"
    #: D3 step 2 — the model tokens opencode serves with NO credential present,
    #: declared rather than sniffed and measured before being written down.
    #: `opencode/big-pickle`: probed 2026-09-11 on opencode 1.18.30 from a
    #: scratch HOME/XDG_CONFIG_HOME/XDG_DATA_HOME/XDG_STATE_HOME pair whose
    #: `opencode auth list` printed `└  0 credentials`, with OPENAI_API_KEY,
    #: GEMINI_API_KEY, ANTHROPIC_API_KEY and OPENROUTER_API_KEY unset:
    #: `opencode run --model opencode/big-pickle --print-logs --log-level ERROR
    #: "Reply with the single word OK."` exited 0 with stdout `OK` in a few
    #: seconds. `openrouter/*`, `openai/*` and `google/*` stay OUT: each needs a
    #: stored or environment credential and the auth leg must keep refusing
    #: them. Zen's catalog is server-side and `opencode/sonnet` vanished from
    #: it once already, so re-probe this on each opencode bump and drop the
    #: entry the day the probe stops answering (see hosts/capabilities.yaml).
    credential_free_models = frozenset({"opencode/big-pickle"})
    version_cmd = ("opencode", "--version")
    # SUPPORT POLICY (2026-10-02): the newest opencode release is the only one
    # supported, so the floor and the release the parser fixtures were captured
    # from are one version, always. Below it the executor refuses (exit 3,
    # naming `upgrade_hint`); above it — a release newer than this commit —
    # one line warns that stream parsing is best-effort until the next bump.
    # Every other pin of that version (`engines.opencode`, the container's
    # `opencode-ai` pin, lockfile and cli-versions.lock row, the mock's
    # `--version`) follows it, and `tests/test_opencode_version_pins.py` fails
    # the build on any one that does not. A bump is one command,
    # `make opencode-bump VERSION=<x.y.z>`: it moves every pin and re-captures
    # the fixtures offline on that release (`tests/fixtures/opencode/capture/`,
    # `auth_list.<v>.json`, `debug_config.<v>.json`), and the tests then grade
    # the parser on the new captures. `make opencode-latest-check` says when
    # npm has a newer release than this one.
    min_version = "1.19.5"
    verified_version = "1.19.5"
    #: What the below-floor refusal tells the user to run (never executed).
    upgrade_hint = "opencode upgrade {version}"
    #: T4.2 — the inclusive (floor, ceiling) opencode range in which
    #: `experimental.continue_loop_on_deny: true` is emitted
    #: (:func:`continue_loop_on_deny_allowed`): the support window itself. The
    #: rig (`tests/fixtures/opencode/capture/`, cases `s41_cont_read` and
    #: `t40_cont_*`) measures the key on every bump, and
    #: `test_opencode_permission_block.py` reads that capture, so the key is
    #: emitted exactly on the release it was measured on. It was measured on
    #: every release from 1.17.15 to 1.18.35 (accepted silently; a rejected
    #: permission no longer ends the turn) while the floor was lower; a newer,
    #: unmeasured build omits it with one WARN until the next bump.
    CONTINUE_LOOP_ON_DENY_RANGE = (min_version, verified_version)

    # §7.2 — per-adapter pattern overrides, EXTENDING the base sets (never
    # replacing them: the base entries are audited-clean and shared).
    #
    # `ProviderAuthError` is the `error.name` of a live opencode auth failure,
    # captured in `tests/fixtures/opencode/provider_auth_error.jsonl` — 304 bytes
    # on **stdout** with stderr empty. The `data.message` that accompanies it is
    # the upstream SDK's, so it varies per provider ("… API key is missing …"
    # happens to match the base list for Google and would not for another);
    # the event *name* is opencode's own and does not.
    auth_error_patterns = LLMProvider.auth_error_patterns + (
        "providerautherror",
    )
    # No rate-limit override: opencode's measured rate-limit behaviour is to
    # retry internally while writing to **neither** stream until the timeout
    # fires, so there is no captured text to declare. Declaring a guessed one
    # would be worse than declaring none — this is the honest "unmeasured".
    #
    # The haystack these patterns see is **vendor-only** (`vendor_text` below):
    # opencode's `--format json` stdout carries tool output, and a validator
    # that grepped a plan discussing rate limits was recorded `rate_limited`
    # (run b38de8bb, 2026-09-24). Only `error` events, unknown event types and
    # stderr reach the tables now.
    rate_limit_patterns = LLMProvider.rate_limit_patterns

    #: `opencode auth list` exits 0 whether or not anything is stored (§5.3), so
    #: the count line is the only verdict. Measured 2026-08-16 against a scratch
    #: HOME/XDG pair: a logged-out run prints exactly "└  0 credentials" and no
    #: Environment section at all, while an env-key-only run prints the same
    #: count *plus* "N environment variable(s)" and really can authenticate.
    _EMPTY_CREDENTIALS = re.compile(r"\b0 credentials\b")
    _ENVIRONMENT_KEYS = re.compile(r"\b\d+ environment variables?\b")

    @property
    def name(self) -> str:
        return "opencode"

    @property
    def default_timeout(self) -> int:
        return 600

    def is_available(self) -> bool:
        return shutil.which("opencode") is not None

    # ── R3 — structural model-spec refusal ────────────────────────────────

    def describe_unresolvable_model(
        self,
        model: str,
        *,
        profile: Optional[str] = None,
        anchor: Optional[str] = None,
    ) -> Optional[str]:
        """Why opencode's *addressing scheme* cannot express this model, or None.

        With ``profile`` (the executor's preflight passes it, plan §8 T8.3), a
        slot that runs hermetically is also asked the hermetic
        reconstructibility question here, **before** the auth leg: a provider
        defined only in the user's own opencode config is refused with the
        ``config_providers`` sentence instead of reaching ``auth list`` and
        being told to run ``opencode auth login``, which cannot fix it. That
        check builds the hermetic content from config reads only (no catalog
        call, no auth probe, no dispatch). Its only possible spawn is the
        per-process user-config read of :func:`read_user_declared_config`, and
        only when the config files alone cannot answer
        (:func:`_user_config_files_conclusive`).

        Structural and nothing else: after any ``:effort`` suffix is stripped, a
        model token with no ``/`` cannot be addressed at all, because opencode
        splits on the first ``/`` and a bare token yields an empty model half
        (``Model not found: <token>/.``, opencode 1.18.18) before a single
        catalog lookup or HTTP call happens.

        **This never consults a catalog.** A catalog that is empty, stale or
        unreadable can only ever downgrade the caller to "no warning"; it can
        never produce a refusal here, because this method does not read one. A
        well-formed but uncatalogued slug (``stub/stub-model``, any provider a
        user declared in opencode's own config) returns ``None`` and keeps
        today's warn-and-dispatch.

        The message states the required shape and echoes the offending token; it
        does not rewrite the spec, because the correct provider prefix for an
        unknown model cannot be inferred and guessing one would dispatch
        somewhere the caller never asked for.
        """
        base_model, _effort = split_reasoning_effort(model, REASONING_EFFORTS)
        token = base_model.strip()
        if "/" in token:
            if profile is None or not hermetic_enabled(profile, anchor):
                return None
            try:
                self._hermetic_config_content(
                    token, anchor=anchor, profile=profile, continue_gate=False
                )
            except _UnreconstructibleProvider as exc:
                return str(exc)
            except Exception:  # noqa: BLE001 - a diagnostic may never refuse
                return None
            return None
        return (
            f"opencode models resolve as 'provider/model' (`opencode run --help`: "
            f"\"model to use in the format of provider/model\"); {token!r} has no "
            f"provider prefix, so opencode splits it into provider {token!r} with "
            f"an empty model half and fails with 'ProviderModelNotFoundError: "
            f"Model not found: {token}/.' before any HTTP call (observed on "
            f"opencode {STRUCTURAL_MODEL_VERSION}) — pass e.g. 'opencode/{token}' "
            f"or the provider that serves it."
        )

    # ── D3 step 4 — the CLI's own catalog ─────────────────────────────────

    #: The listing subcommand: one bare ``provider/model`` per stdout line and
    #: nothing else (measured on 1.18.30 — no header, no decoration).
    models_cmd = ("opencode", "models")

    def describe_unlisted_model(
        self,
        model: str,
        *,
        anchor: Optional[str] = None,
        profile: str = PROFILE_AGENT_READONLY,
    ) -> ModelVerdict:
        """Is ``model`` in ``opencode models``' live listing? (D3 step 4)

        **Read in the dispatch's own configuration, or the verdict is wrong.**
        The listing is taken inside the same :meth:`hermetic_dispatch` context
        the dispatch it vets will enter — same ``XDG_CONFIG_HOME`` redirect, same
        ``OPENCODE_CONFIG_CONTENT`` rebuilt from multi-llm's own
        ``config_providers`` — so a provider defined only in the user's own
        ``opencode.json`` is absent here exactly as it would be at dispatch. When
        :func:`hermetic_enabled` is false for ``profile`` the probe runs plain,
        matching dispatch again. ``XDG_CACHE_HOME`` is never redirected (it holds
        ``opencode/models.json``), so this reads the same catalog cache a
        dispatch would rather than paying a cold fetch.

        *Normalization*: the ``:effort`` suffix is split off with the same
        :func:`split_reasoning_effort` call :meth:`build_command` makes before it
        emits ``--variant``, so the token compared is the token dispatched. Then
        whole lines, exact, case-sensitive.

        *Unknown means unknown.* A probe that could not run, a non-zero exit,
        zero parsed slugs, or output that is not a listing at all (a stream whose
        lines are mostly not ``provider/model`` shaped, or that opens with a
        ``timestamp=… level=…`` log line) is ``known=None`` — never ``False``.
        "Not in an empty list" is not a fact. ``known=False`` is reserved for a
        listing that parsed cleanly and does not contain the token, and it
        carries a diagnostic composed *here* from that listing — the ids sharing
        the token's ``provider/`` prefix, nearest first, capped at three, plus
        how many ids that prefix lists. ``opencode models`` prints no "Did you
        mean" line; quoting the CLI's own is D4's job on the dispatch path.
        """
        base_model, _effort = split_reasoning_effort(model or "", REASONING_EFFORTS)
        token = base_model.strip()
        if "/" not in token:
            # Structural — `describe_unresolvable_model` refuses it first.
            return ModelVerdict(known=None)
        try:
            with self.hermetic_dispatch(
                profile, token, anchor=anchor, continue_gate=False
            ) as refusal:
                if refusal:
                    # The slot itself is refused before spawn; a listing taken
                    # here would describe a configuration no dispatch will use.
                    return ModelVerdict(known=None)
                env = dict(os.environ)
                for name in self.get_remove_env() or ():
                    env.pop(name, None)
                env.update(self.get_env(token) or {})
                completed = _list_models(list(self.models_cmd), env)
        except Exception:  # noqa: BLE001 - a catalog read may never end a preflight
            return ModelVerdict(known=None)
        if completed is None or completed.returncode != 0:
            return ModelVerdict(known=None)
        listing = _parse_model_listing(completed.stdout or "")
        if listing is None:
            return ModelVerdict(known=None)
        if token in listing:
            return ModelVerdict(known=True)

        prefix = token.split("/", 1)[0]
        siblings = [slug for slug in listing if slug.startswith(prefix + "/")]
        nearest = tuple(
            difflib.get_close_matches(token, siblings, n=3, cutoff=0.0)
        )
        if siblings:
            hint = (
                f"; nearest: {', '.join(nearest)}" if nearest else ""
            )
            detail = (
                f"`opencode models` lists {len(siblings)} id(s) under "
                f"'{prefix}/' and {token!r} is not one of them{hint}."
            )
        else:
            detail = (
                f"`opencode models` lists no ids under '{prefix}/' "
                f"({len(listing)} ids listed in all) — this opencode has no "
                f"provider {prefix!r} configured, or none it can authenticate "
                f"to — so {token!r} cannot resolve."
            )
        return ModelVerdict(known=False, detail=detail, suggestions=nearest)

    # ── §8 — config-declared providers (T8.3, T8.6) ────────────────────────

    def config_credential_source(
        self,
        model: str,
        *,
        profile: str = PROFILE_AGENT_READONLY,
        anchor: Optional[str] = None,
        cwd: Optional[str] = None,
        env_builder: Optional[Callable[[], Optional[Mapping[str, str]]]] = None,
    ) -> str:
        """``declared`` when the dispatch's own config supplies this provider.

        Asked by the executor's auth leg only after ``auth list`` said ``False``
        for a model that needs a credential (lazy: the common path spawns
        nothing new). It enters the same :meth:`hermetic_dispatch` context the
        dispatch will, builds the child env **inside** it with ``env_builder``
        (the executor's shared ``resolve_env`` + ``build_child_env`` helper, so
        the ``env_allowlist`` and host guards apply exactly as at dispatch), and
        runs ``debug config`` with the dispatch's ``cwd`` and with ``--pure``
        exactly when the dispatch argv carries it. The verdict (§8.2):

        * the prefix is declared **custom** (``npm``/``baseURL``) → ``declared``,
          with or without a key: ``auth list`` is blind to it and a keyless
          local server is a legitimate shape;
        * a declared **built-in override** whose ``options.apiKey`` resolves to
          a non-empty value in the child's env → ``declared``. The pinned
          build prints every declared key as ``"***"``, so ``debug config``
          only says a key is declared; the reference itself (a literal,
          ``{env:VAR}``, ``{file:PATH}``) is read from the config sources the
          child loads and substituted in the child's env
          (:func:`_config_key_resolves`);
        * anything else — a keyless built-in override, an undeclared prefix, a
          refused hermetic slot, a reader failure, a builder that raises or
          yields ``None`` inside a hermetic slot → ``unknown``, which keeps
          today's ``not_authenticated`` refusal.

        ``env_builder`` of ``None`` composes ``resolve_env`` + ``build_child_env``
        here with no host guards (a caller outside the executor). Never raises.
        """
        try:
            from .base import CONFIG_AUTH_DECLARED, CONFIG_AUTH_UNKNOWN
        except ImportError:  # pragma: no cover - direct-script import shim
            CONFIG_AUTH_DECLARED, CONFIG_AUTH_UNKNOWN = "declared", "unknown"
        base_model, _effort = split_reasoning_effort(model or "", REASONING_EFFORTS)
        token = base_model.strip()
        prefix = token.split("/", 1)[0].strip() if "/" in token else ""
        if not prefix:
            return CONFIG_AUTH_UNKNOWN
        try:
            with self.hermetic_dispatch(
                profile, token, anchor=anchor, continue_gate=False
            ) as refusal:
                if refusal:
                    return CONFIG_AUTH_UNKNOWN
                if env_builder is not None:
                    env = env_builder()
                    slot = _ACTIVE.get()
                    if env is None and slot is not None and slot.get("config_home"):
                        # A hermetic slot always yields an `XDG_CONFIG_HOME`
                        # delta, so `None` here is a builder that lost it:
                        # `debug config` would run with neither the delta nor
                        # the allowlist. Only a non-hermetic, unfiltered
                        # dispatch legitimately inherits unchanged.
                        return CONFIG_AUTH_UNKNOWN
                else:
                    env = self._plain_child_env(token, profile, anchor=anchor, cwd=cwd)
                pure = PURE_FLAG in self._hermetic_argv()
                declared = _read_declared_providers(env, cwd, pure)
                if declared is None or declared.providers is None:
                    return CONFIG_AUTH_UNKNOWN
                decl = declared.providers.get(prefix)
                if decl is not None and decl.custom:
                    return CONFIG_AUTH_DECLARED
                if decl is not None and decl.key_declared and _config_key_resolves(
                    prefix, env, cwd
                ):
                    return CONFIG_AUTH_DECLARED
        except Exception:  # noqa: BLE001 - a diagnostic read may never end a preflight
            return CONFIG_AUTH_UNKNOWN
        return CONFIG_AUTH_UNKNOWN

    def _plain_child_env(
        self,
        model: str,
        profile: str,
        *,
        anchor: Optional[str] = None,
        cwd: Optional[str] = None,
    ) -> Optional[Dict[str, str]]:
        """``resolve_env`` + ``build_child_env`` with no host guards.

        The fallback for :meth:`config_credential_source` when no executor
        builder is handed in. ``None`` means "inherit this process's env".
        """
        from .base import build_child_env

        delta = {
            key: (os.path.expanduser(value) if isinstance(value, str) else value)
            for key, value in (
                self.resolve_env(model, profile, anchor=anchor, cwd=cwd) or {}
            ).items()
        }
        return build_child_env(self, provider_env=delta, anchor=anchor)

    def config_declared_providers(
        self, *, cwd: Optional[str] = None, timeout: Optional[float] = None
    ) -> Optional[Tuple[str, ...]]:
        """The ids the **user's own** resolved config declares, for ``doctor``.

        A provider counts when it is custom (``npm``/``baseURL``) or a built-in
        override declaring a key (whether that key resolves is the auth leg's
        question, asked per dispatch env; this row is never a clearance). Read with
        no hermetic delta (:func:`read_user_declared_config`) under ``timeout``
        (``doctor``'s remaining budget). ``None`` when the read failed or ran
        out of budget. Ids only, never a key.
        """
        declared = read_user_declared_config(cwd=cwd, timeout=timeout)
        if declared is None or declared.providers is None:
            return None
        return tuple(
            provider_id
            for provider_id, decl in declared.providers.items()
            if decl.custom or decl.key_declared
        )

    def hermetic_config_providers(self, anchor: Optional[str] = None) -> Tuple[str, ...]:
        """``providers.opencode.config_providers`` ids: what a hermetic slot rebuilds."""
        declared = _opencode_block(anchor).get("config_providers")
        if not isinstance(declared, dict):
            return ()
        return tuple(str(key) for key in declared)

    def dispatch_is_hermetic(self, profile: str, anchor: Optional[str] = None) -> bool:
        """Whether a dispatch under ``profile`` runs hermetically (duck-typed)."""
        return hermetic_enabled(profile, anchor)

    # ── M4 — hermetic dispatch ────────────────────────────────────────────

    @contextlib.contextmanager
    def hermetic_dispatch(
        self,
        profile: str,
        model: str = "",
        *,
        anchor: Optional[str] = None,
        runner_version: Optional[str] = None,
        continue_gate: bool = True,
    ) -> Iterator[Optional[str]]:
        """Scope one dispatch to the run's empty config home (donor §2.3).

        Yields ``None`` normally, or a refusal string when the slot's model names
        a provider that the redirect would make unreconstructible — a silent
        model-resolution failure is the one outcome the redirect may not produce.

        The context is what both argv and env read, so ``--pure`` and the
        ``XDG_CONFIG_HOME`` redirect are emitted together or not at all. Its
        ``finally`` drops this slot's claim on the shared directory, which is
        removed when the last slot leaves — on normal exit, on exception, on a
        per-slot timeout and on ``KeyboardInterrupt`` alike, with the ``atexit``
        sweep as the idempotent backstop.

        ``runner_version`` is the opencode version the caller's preflight
        already read (the executor's ``_VERSION_CACHE``), or ``None`` when the
        caller holds no read. It only gates T4.2's experimental key
        (:func:`continue_loop_on_deny_allowed`). A hermetic ``generate`` slot
        with no version (Lane A, which has no preflight) reads it once per
        process (:func:`_lane_a_runner_version`); no other path spawns
        ``opencode --version``. ``continue_gate=False`` is for a caller that
        spawns no model turn at all (the ``opencode models`` catalog probe, the
        auth leg's ``debug config`` read), which neither needs the key nor
        should warn about its absence.

        **Non-hermetic slots (T4.7).** ``agent-write``, and ``agent-readonly``
        under ``hermetic: off``, get a slot with **no** config home: no
        ``--pure``, no redirect, nothing stripped. It only records which agent
        the rows go under; :meth:`resolve_env` merges them over the inherited
        ``OPENCODE_CONFIG_CONTENT``. A ``continue_gate=False`` caller gets no
        such slot, so it never triggers the user-config read.
        """
        if not hermetic_enabled(profile, anchor):
            agent = self._merge_agent(profile)
            if agent is None or not continue_gate:
                # No rows to merge: a profile that runs no named agent, or a
                # caller that spawns no model turn (the catalog probe, the auth
                # leg's `debug config` read), which a permission row cannot
                # affect and which must not pay for the user-config read.
                yield None
                return
            # T4.7: a slot with NO config home. `--pure`, the XDG redirect and
            # the stripped carriers all key off `config_home`, so none of them
            # is rendered; the rows are merged over the inherited content later,
            # lazily, in `resolve_env` — never here, because this context is
            # also entered by argv-only renderers (`--dry-run-subagents`) that
            # must not spawn `opencode debug config`.
            token = _ACTIVE.set({
                "config_home": None,
                "config_content": None,
                "merge_agent": agent,
                "runner_version": runner_version,
                "continue_gate": continue_gate,
            })
            try:
                yield None
            finally:
                _ACTIVE.reset(token)
            return
        try:
            content = self._hermetic_config_content(
                model, anchor=anchor, profile=profile,
                runner_version=runner_version, continue_gate=continue_gate,
            )
        except _UnreconstructibleProvider as exc:
            # Raised BEFORE the directory is claimed, so a refusal leaks nothing.
            yield str(exc)
            return
        home = acquire_config_home()
        token = _ACTIVE.set({"config_home": home, "config_content": content})
        try:
            yield None
        finally:
            _ACTIVE.reset(token)
            release_config_home()

    @staticmethod
    def _merge_agent(profile: str) -> Optional[str]:
        """The agent a **non-hermetic** slot merges its rows under, or ``None``.

        ``agent-write`` always (it is never hermetic, §4.4) and ``agent-readonly``
        when ``hermetic: off`` put its dispatch here. ``generate`` does not: it
        passes no ``--agent``, and under ``hermetic: off`` a user's
        ``default_agent`` decides which agent it runs.
        """
        if profile == PROFILE_AGENT_WRITE:
            return WRITE_AGENT
        if profile == PROFILE_AGENT_READONLY:
            return READONLY_AGENT
        return None

    def resolve_env(
        self, model: str, profile: str = PROFILE_GENERATE, **options: Any
    ) -> Dict[str, str]:
        """The base composition, plus T4.7's merged content in a non-hermetic slot.

        The merge lives here and not in :meth:`get_env` because it needs the
        dispatch's ``cwd`` (the project layer of the user's config) and because
        :meth:`get_env` must stay a pure call: nothing but a real spawn's env
        composition may run ``opencode debug config``.
        """
        env = super().resolve_env(model, profile, **options)
        slot = _ACTIVE.get()
        if slot is None or slot.get("config_home") or not slot.get("merge_agent"):
            return env
        base = options.get("base_env")
        source: Mapping[str, str] = os.environ if base is None else base
        content = self._merged_config_content(slot, source, cwd=options.get("cwd"))
        if content is not None:
            env["OPENCODE_CONFIG_CONTENT"] = content
        return env

    def _merged_config_content(
        self,
        slot: Mapping[str, Any],
        source: Mapping[str, str],
        *,
        cwd: Optional[str] = None,
    ) -> Optional[str]:
        """T4.7's ``OPENCODE_CONFIG_CONTENT`` for one non-hermetic slot, or ``None``.

        The user's own rules come from :func:`read_user_declared_config`: one
        ``debug config`` spawn per process per (config-locating env, ``cwd``),
        concurrent first callers sharing it, a failed read cached as well.
        ``None`` passes an unparseable inherited value through untouched.
        """
        agent = str(slot["merge_agent"])
        inherited = source.get("OPENCODE_CONFIG_CONTENT")
        parsed = _parse_inherited_content(inherited)[0]
        if parsed is None or not isinstance(parsed.get("agent", {}), dict):
            # Decided before the reader runs: nothing will be emitted (not a
            # JSON object, or an `agent` value that is not an object), so there
            # is no reason to spawn it, nor to WARN about a failed read of it.
            # `merge_permission_content` WARNs the pass-through.
            return merge_permission_content(inherited, agent, {})
        declared = read_user_declared_config(cwd=cwd)
        external = _external_directory_map(
            agent, relisted_external_rules(declared, agent), source
        )
        continue_loop = bool(slot.get("continue_gate", True)) and (
            continue_loop_on_deny_allowed(
                slot.get("runner_version"), self.CONTINUE_LOOP_ON_DENY_RANGE
            )
        )
        return merge_permission_content(
            inherited, agent, external, continue_loop=continue_loop
        )

    def _hermetic_argv(self) -> List[str]:
        """``[--pure]`` inside an active hermetic dispatch, else ``[]``.

        A non-hermetic slot (T4.7: no ``config_home``) never gets ``--pure``.
        """
        slot = _ACTIVE.get()
        if slot is None or not slot.get("config_home"):
            return []
        binary = shutil.which("opencode")
        if binary and PURE_FLAG in _read_help_tokens(binary):
            return [PURE_FLAG]
        _warn_once(
            "pure-unsupported",
            f"multi-llm warning: `opencode run --help` does not list {PURE_FLAG} "
            f"— running without it. Containment is reduced (external plugins "
            f"still load); the config-home redirect still applies.",
        )
        return []

    def _hermetic_config_content(
        self,
        model: str,
        *,
        anchor: Optional[str] = None,
        profile: str = PROFILE_AGENT_READONLY,
        runner_version: Optional[str] = None,
        continue_gate: bool = True,
    ) -> Optional[str]:
        """The ``OPENCODE_CONFIG_CONTENT`` this hermetic slot needs, or None.

        Two halves, merged into one document:

        * **provider** — built from **multi-llm's own** resolved provider config
          (``providers.opencode.config_providers``) and from no other source,
          never copied out of the user's file, which is the config the redirect
          exists to neutralize. Credentials are never carried here; auth stays
          in ``auth.json`` under the retained ``XDG_DATA_HOME``. A built-in
          provider needs no block. A provider defined **only** in the user's own
          opencode config raises :class:`_UnreconstructibleProvider`, because
          after the redirect there is nothing left for it to resolve against.
        * **permission** (T4.1) — the §4.2 step 1 deny rows under
          ``agent.<name>.permission`` for every profile in
          :data:`PERMISSION_AGENT_BY_PROFILE`, whatever the provider, plus
          ``experimental.continue_loop_on_deny`` when the version gate allows it
          (T4.2).

        **The refusal fires first.** The provider half is resolved, and may
        raise, before any permission row is merged, so a refused slot produces
        no content at all and claims no config home (§9 item 4; §8's structural
        leg relies on this raise).
        """
        provider_block: Optional[Dict[str, Any]] = None
        base_model, _effort = split_reasoning_effort(model or "", REASONING_EFFORTS)
        prefix = base_model.split("/", 1)[0].strip() if "/" in base_model else ""
        if prefix:
            declared = _opencode_block(anchor).get("config_providers")
            if isinstance(declared, dict) and isinstance(declared.get(prefix), dict):
                provider_block = {prefix: declared[prefix]}
            elif _user_defines_provider(prefix):
                raise _UnreconstructibleProvider(
                    f"opencode provider {prefix!r} (from model {base_model!r}) is "
                    f"defined only in your own opencode config, which a hermetic run "
                    f"replaces — it would not resolve, so this slot is refused rather "
                    f"than dispatched into a silent model-resolution failure. Declare "
                    f"it under providers.opencode.config_providers (credentials "
                    f"excluded — they stay in auth.json), or set "
                    f"providers.opencode.hermetic: off to keep today's inheritance."
                )

        document: Dict[str, Any] = {}
        if provider_block is not None:
            document["provider"] = provider_block
        agent = PERMISSION_AGENT_BY_PROFILE.get(profile)
        if agent is not None:
            document["agent"] = {agent: {"permission": permission_block(agent)}}
            if runner_version is None and continue_gate and profile == PROFILE_GENERATE:
                # Lane A passes no version (it has no preflight); read it once
                # per process so `generate` gets the key rather than an unread
                # WARN. After the refusal above, so a refused slot spawns nothing.
                runner_version = _lane_a_runner_version(self)
            if continue_gate and continue_loop_on_deny_allowed(
                runner_version, self.CONTINUE_LOOP_ON_DENY_RANGE
            ):
                document["experimental"] = {"continue_loop_on_deny": True}
        if not document:
            return None
        document["$schema"] = "https://opencode.ai/config.json"
        return _dump_config(document)

    # ── env / argv ────────────────────────────────────────────────────────

    def get_env(self, model: str) -> Dict[str, str]:
        """Adapter env delta; hermetic keys only inside a dispatch context."""
        env = dict(super().get_env(model) or {})
        slot = _ACTIVE.get()
        if slot is None or not slot.get("config_home"):
            # Outside a dispatch, or a non-hermetic slot (T4.7): no redirect.
            return env
        # Exactly one XDG variable changes. XDG_DATA_HOME (auth.json),
        # XDG_CACHE_HOME (models.json), XDG_STATE_HOME and XDG_RUNTIME_DIR are
        # passed through untouched.
        env["XDG_CONFIG_HOME"] = str(slot["config_home"])
        env[PROJECT_CONFIG_ENV] = "1"
        # `~/.opencode/` hangs off opencode's own home, not HOME's XDG dirs.
        env[HOME_DIR_ENV] = str(slot["config_home"])
        content = slot.get("config_content")
        if content:
            env["OPENCODE_CONFIG_CONTENT"] = content
        return env

    def get_remove_env(self) -> List[str]:
        """Inherited config carriers, stripped only while hermetic."""
        names = list(super().get_remove_env() or ())
        slot = _ACTIVE.get()
        if slot is None or not slot.get("config_home"):
            # A non-hermetic slot (T4.7) strips nothing: the user's config is in
            # force, and its merged content replaces the inherited value.
            return names
        emitted = {"OPENCODE_CONFIG_CONTENT"} if slot.get("config_content") else set()
        names.extend(name for name in CONFIG_ENV_NAMES if name not in emitted)
        return names

    def build_command(
        self,
        prompt: str,
        model: str,
        *,
        timeout_s: Optional[int] = None,
        schema: Optional[StructuredSchema] = None,
    ) -> List[str]:
        # opencode run --format json --print-logs --log-level ERROR
        #     --model <model> [--variant <effort>] "<prompt>"
        #
        # --print-logs is the only way to learn why a run produced nothing.
        # A stream error (an exhausted key, say) makes opencode retry
        # internally while writing to neither stream, so the run burns the
        # full timeout and reports no cause. The logs go to stderr and are
        # pinned to ERROR, so stdout stays pure NDJSON and a healthy run
        # stays silent.
        base_model, effort = split_reasoning_effort(model, REASONING_EFFORTS)
        if effort is not None and EFFORT_LADDER.refuses_for_model(base_model, effort):
            # The per-model cap, asked at the ONE place `--variant` is emitted, so
            # both routes to a suffix are covered by one check: a user-typed
            # `--models opencode:<model>:high`, and the host session's own picker
            # variant, which the OpenCode plugin propagates as the same suffix.
            # A capped model is one measured to HANG on `--variant` rather than
            # merely ignore it (see EFFORT_LADDER), so dropping the word is the
            # conservative move: the slot answers at the model's default effort
            # instead of burning its whole timeout writing nothing. Said out loud
            # once per model+effort, because a silently different effort is the
            # defect this propagation exists to fix.
            _warn_once(
                f"variant-capped:{base_model}:{effort}",
                f"multi-llm warning: dropping `--variant {effort}` for "
                f"{base_model} — that model is declared not to accept a "
                f"reasoning effort (measured to hang on one); dispatching at "
                f"its default effort instead",
            )
            effort = None
        cmd = [
            "opencode", "run", "--format", "json",
            "--print-logs", "--log-level", "ERROR",
            # `--pure` is rendered only inside an active hermetic dispatch
            # context, i.e. only when the paired `XDG_CONFIG_HOME` redirect is
            # also being applied. Outside one this is the byte-identical argv
            # this adapter built before M4.
            *self._hermetic_argv(),
            "--model", base_model,
        ]
        if effort is not None:
            cmd += ["--variant", effort]
        cmd.append(prompt)
        return cmd

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
    ) -> Tuple[List[str], Optional[str]]:
        """Deliver the prompt on argv or on stdin (prompt omitted from argv)."""
        if transport != "stdin":
            return super().build_command_for_transport(
                prompt, model, transport, prompt_file, timeout_s=timeout_s,
                schema=schema,
                sandbox_fallback=sandbox_fallback,
            )
        cmd = self.build_command(prompt, model, timeout_s=timeout_s, schema=schema)
        return cmd[:-1], prompt

    def build_agent_command(
        self,
        prompt: str,
        model: str,
        profile: str = PROFILE_AGENT_READONLY,
        *,
        timeout_s: Optional[int] = None,
        schema: Optional[StructuredSchema] = None,
    ) -> List[str]:
        """Build ``opencode run`` under the profile's own agent (D3e).

        ``agent-readonly`` runs the built-in ``plan`` agent (every edit tool
        denied); ``agent-write`` runs the built-in ``build`` agent, named
        explicitly rather than inherited from opencode's default. Either way the
        permission set is opencode's own, and ``cwd`` is pinned by the executor.
        """
        if profile == PROFILE_AGENT_WRITE:
            cmd = self.build_command(prompt, model, timeout_s=timeout_s, schema=schema)
            return [*cmd[:2], "--agent", WRITE_AGENT, *cmd[2:]]
        if profile != PROFILE_AGENT_READONLY:
            return super().build_agent_command(
                prompt, model, profile, timeout_s=timeout_s, schema=schema
            )
        cmd = self.build_command(prompt, model, timeout_s=timeout_s, schema=schema)
        # `--agent` belongs to the `run` subcommand, so it goes after
        # `["opencode", "run"]` — never before it.
        return [*cmd[:2], "--agent", READONLY_AGENT, *cmd[2:]]

    def parse_usage(self, stdout: str, stderr: str) -> Optional[Dict[str, Any]]:
        """Sum per-step usage across the whole ``run --format json`` stream (D3j).

        OpenCode emits one assistant message per step — dozens for a long run —
        and the token counters live on each ``step_finish`` part
        (``tokens: {input, output, reasoning, cache: {read, write}}`` plus
        ``cost``, verified against the part schema in the 1.18.x bundle). Reading
        the final message alone under-reports a multi-step run, which is the
        specific bug this method exists to prevent, so every step is summed.
        ``tool_uses`` is the count of ``tool_use`` events — a real tool count, not
        an inference.
        """
        totals = {
            "input_tokens": 0,
            "output_tokens": 0,
            "cached_input_tokens": 0,
            "cost_usd": 0.0,
        }
        seen = {key: False for key in totals}
        tool_uses = 0
        saw_tool_event = False

        def _num(value: Any) -> Optional[float]:
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return value
            return None

        for event in self._iter_events(stdout):
            event_type = event.get("type")
            if event_type == "tool_use":
                saw_tool_event = True
                tool_uses += 1
                continue
            if event_type != "step_finish":
                continue
            part = event.get("part")
            if not isinstance(part, dict) or part.get("type") != "step-finish":
                continue
            cost = _num(part.get("cost"))
            if cost is not None:
                totals["cost_usd"] += cost
                seen["cost_usd"] = True
            tokens = part.get("tokens")
            if not isinstance(tokens, dict):
                continue
            step_input = _num(tokens.get("input"))
            if step_input is not None:
                totals["input_tokens"] += step_input
                seen["input_tokens"] = True
            step_output = _num(tokens.get("output"))
            step_reasoning = _num(tokens.get("reasoning")) or 0
            if step_output is not None:
                # opencode's own roll-up folds reasoning into output; mirror it.
                totals["output_tokens"] += step_output + step_reasoning
                seen["output_tokens"] = True
            cache = tokens.get("cache")
            if isinstance(cache, dict):
                cache_read = _num(cache.get("read"))
                if cache_read is not None:
                    totals["cached_input_tokens"] += cache_read
                    seen["cached_input_tokens"] = True

        out: Dict[str, Any] = {
            key: value for key, value in totals.items() if seen[key]
        }
        if "input_tokens" in out and "output_tokens" in out:
            out["total_tokens"] = out["input_tokens"] + out["output_tokens"]
        if saw_tool_event:
            out["tool_uses"] = tool_uses
        return out or None

    @staticmethod
    def _iter_events(stdout: str):
        """Yield the well-formed JSON objects in an NDJSON stream."""
        for line in stdout.strip().split('\n'):
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                # Skip malformed lines
                continue
            if isinstance(event, dict):
                yield event

    #: Every top-level ``run --format json`` event type (the emitter in the
    #: binary's bundle; ``error`` is the one that carries no ``part``). A line
    #: carrying one of them is what makes stdout an opencode event stream rather
    #: than a bare answer.
    _EVENT_TYPES = frozenset({
        "step_start", "step_finish", "tool_use", "text", "reasoning", "error",
    })

    @classmethod
    def _scan_text_parts(cls, stdout: str) -> "_OpenCodeText":
        """One walk over the stream for the answer text, shared by
        :meth:`parse_output` and :meth:`salvage_text` (plan:
        review-run-scope-salvage-and-failure-visibility §4, D4.4).

        A text part is a ``text`` event whose ``part.type`` is ``text`` —
        ``parse_output``'s rule, unchanged. Each step is one assistant message,
        named by ``part.messageID`` on every event of that step
        (``step_start``, ``tool_use``, ``text``, ``step_finish``), so the last
        message is the one the last such event names — even one that has
        printed no text yet. A text part that names no message counts as a
        message of its own.
        """
        parts: List[str] = []
        by_message: Dict[Any, List[str]] = {}
        last_key: Any = None
        saw_event = False
        for index, event in enumerate(cls._iter_events(stdout)):
            event_type = event.get("type")
            # `isinstance` first: an unhashable `type` would make the set
            # lookup raise, and this walk also serves `parse_output`.
            if isinstance(event_type, str) and event_type in cls._EVENT_TYPES:
                saw_event = True
            part = event.get("part")
            if not isinstance(part, dict):
                continue
            text = part.get("text")
            is_text = (
                event.get("type") == "text"
                and part.get("type") == "text"
                and isinstance(text, str)
            )
            message_id = part.get("messageID")
            if isinstance(message_id, str) and message_id:
                key: Any = message_id
            elif is_text:
                key = ("part", index)
            else:
                continue
            last_key = key
            if is_text:
                parts.append(text)
                by_message.setdefault(key, []).append(text)
        last_message = by_message.get(last_key, []) if last_key is not None else []
        return _OpenCodeText(parts, last_message, saw_event)

    @staticmethod
    def _direct_json(text: str) -> Optional[Dict[str, Any]]:
        """Parse ``text`` as one complete JSON document, or return None."""
        if text.startswith(('[', '{')):
            try:
                return {"success": True, "data": json.loads(text)}
            except json.JSONDecodeError:
                pass
        return None

    def classify_auth_probe(
        self, stdout: str, stderr: str, exit_code: int = 0
    ) -> Optional[bool]:
        """Read ``opencode auth list`` (§5.3/§7.2: exit 0 carries no verdict).

        The base implementation reports ``True`` on a clean exit with no login
        notice — and ``auth list`` *always* exits 0 and never prints one, so a
        logged-out opencode was being recorded READY and discovered one dispatch
        at a time. The count line is the verdict, and it is the only one:

        * ``0 credentials`` with no ``Environment`` section — nothing stored and
          nothing in the environment: ``False``, the one verdict that refuses a
          run, so it is drawn from the narrowest possible evidence.
        * ``0 credentials`` **plus** ``N environment variable(s)`` — opencode
          found a provider key in the environment and really can authenticate,
          so this must not refuse (it would fail closed on a working setup).
        * anything else falls through to the base rule.
        """
        haystack = f"{stdout or ''}\n{stderr or ''}".lower()
        if self._EMPTY_CREDENTIALS.search(haystack) and not self._ENVIRONMENT_KEYS.search(
            haystack
        ):
            return False
        return super().classify_auth_probe(stdout, stderr, exit_code)

    #: The ``run --format json`` event types that carry the model's words or
    #: the repo's, never the vendor's verdict: prose, reasoning, tool output
    #: (a ``grep`` of a plan that discusses rate limits), tool errors ("The user
    #: rejected permission…") and per-step token/cost numbers.
    _NON_VENDOR_EVENT_TYPES = frozenset({
        "text", "tool_use", "reasoning", "step_start", "step_finish",
    })

    #: A final line the kill cut mid-event cannot be parsed, so whether it is
    #: droppable is read off its text: one of the droppable openers inside the
    #: first ~64 characters. Written without assuming ``type`` is the first key
    #: (a capture may lead with ``timestamp``), because key order is not
    #: guaranteed.
    _CUT_LINE_OPENER = re.compile(r'"type"\s*:\s*"(?:tool_use|text|reasoning)"')
    _CUT_LINE_WINDOW = 64

    def vendor_text(self, stdout: str, stderr: str) -> Tuple[str, str]:
        """The events opencode itself wrote as a verdict, and nothing the model
        or the repo said.

        opencode does not echo our prompt, but it echoes the **repository**:
        ``--format json`` stdout carries every tool call's output. Run b38de8bb
        (2026-09-24) was a validator that grepped a plan discussing rate
        limiting, died on an auto-rejected permission with exit 0, and was
        recorded ``rate_limited`` off ``bypasses the record rate limiter`` in a
        ``tool_use`` event — then halved opencode's concurrency for the rest of
        the batch. omp drops its tool results for the same reason.

        So ``text``, ``tool_use``, ``reasoning``, ``step_start`` and
        ``step_finish`` events are dropped. ``error`` events are kept whole
        (``ProviderAuthError``, ``UnknownError``/``err_…``, a ``statusCode``
        429), and so are unknown event types and non-JSON lines — the
        conservative direction, since keeping text can only preserve a verdict
        the unreduced haystack already reached.

        * **An end-cut final line** (a stream killed mid-event) is dropped when
          a droppable ``"type"`` opener sits in its first ~64 characters, in any
          key position. A line cut at its *start* — the first line of a stored
          64 KB ``stdout_tail`` — carries no opener and is kept, by design: the
          live executor classifies the whole stream and never sees one.
        * **No line parses as an event** → the input, unchanged.
        * **Any exception** → the input, unchanged (the base contract).
        * **stderr is never reduced**: a real opencode quota failure is a
          ``--print-logs`` line there, and it reaches the tables untouched.

        The dropped events stay available for diagnostics — the executor's
        failure capture and ``describe_failure`` read the raw stream — and the
        structural denied-turn check (:meth:`classify_structural`) reads the
        raw stream too, never this reduction.

        kilocode is an opencode fork with the same event shape. It is fan-out
        only today, so no raw kilocode stdout reaches ``classify_failure``; give
        it this override when a kilocode agent profile appears.
        """
        try:
            text = stdout or ""
            lines = text.split("\n")
            last = max(
                (i for i, line in enumerate(lines) if line.strip()), default=-1
            )
            kept: List[str] = []
            events = 0
            for index, line in enumerate(lines):
                stripped = line.strip()
                if not stripped:
                    kept.append(line)
                    continue
                try:
                    event = json.loads(stripped)
                except ValueError:
                    if index == last:
                        opener = self._CUT_LINE_OPENER.search(stripped)
                        if opener is not None and opener.start() < self._CUT_LINE_WINDOW:
                            continue
                    kept.append(line)
                    continue
                if not isinstance(event, dict):
                    kept.append(line)
                    continue
                events += 1
                if event.get("type") in self._NON_VENDOR_EVENT_TYPES:
                    continue
                kept.append(line)
            if not events:
                return stdout, stderr
            return "\n".join(line for line in kept if line.strip()), stderr
        except Exception:  # noqa: BLE001 - a failed reduction is the identity
            return stdout, stderr

    #: The pattern verdicts that outrank a denied turn: the ones
    #: ``subagent_executor._classify_failed_run`` forwards. A stream that carries
    #: a rejected ``tool_use`` *and* a genuine vendor 429 / auth / model error is
    #: that error — reporting it as ``runner_error`` would hide it from
    #: backpressure and the ladder.
    _VERDICTS_THAT_OUTRANK_A_DENIED_TURN = frozenset({
        STATUS_AUTH_FAILED,
        STATUS_RATE_LIMITED,
        CATEGORY_INVALID_MODEL,
        CATEGORY_SANDBOX_UNAVAILABLE,
        STATUS_CONTEXT_LENGTH_EXCEEDED,
    })

    #: The ``PermissionRejectedError`` (and ``PermissionCorrectedError``) text
    #: of 1.18.32, the error a ``tool_use`` carries when ``run`` auto-rejected
    #: an ``ask``. A ``deny`` rule raises ``PermissionDeniedError`` instead,
    #: whose words differ and whose turn continues.
    _REJECTED_PERMISSION = "rejected permission to use this specific tool call"

    #: ``run``'s stderr line for an auto-rejected ``ask``, measured on 1.18.32:
    #: ``! permission requested: external_directory (<dir>/*); auto-rejecting``
    #: (behind ANSI colour codes, stripped first).
    _AUTO_REJECTING = re.compile(
        r"permission requested: (?P<permission>[^\s()]+) \((?P<pattern>[^\n]*?)\); "
        r"auto-rejecting"
    )
    _ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")

    def classify_structural(
        self, stdout: str, stderr: str, exit_code: int = 0
    ) -> Optional[Tuple[str, str]]:
        """A turn ``run`` ended on an auto-rejected permission → ``runner_error``.

        In 1.18.32 ``run`` answers every ``permission.asked`` with ``reject``,
        and a rejected permission **ends the agent loop** unless
        ``experimental.continue_loop_on_deny`` is set: the session goes idle
        and the process exits 0 with no answer. The b38de8bb validator did
        exactly that on a bash probe of a system path outside the repo.

        Read structurally off the **raw** stream (never :meth:`vendor_text`,
        which drops these very events), from the fields nested under ``part``
        — a top-level ``reason`` is absent on every turn, a healthy one
        included. All three must hold:

        * exit 0;
        * the last ``step_finish`` has a ``part.reason`` and it is not
          ``stop``;
        * a ``tool_use`` with ``part.state.status == "error"`` carries the
          rejected-permission text in ``part.state.error``, **or** stderr has
          the ``auto-rejecting`` line.

        The ``stop`` condition is required: with ``continue_loop_on_deny`` on,
        stderr still says ``auto-rejecting`` while the turn goes on to a final
        answer and a ``stop`` (measured; pinned as a negative).

        The ``(<permission> <pattern>)`` parenthetical comes from the stderr
        line, else from the same shape inside the rejected ``tool_use``'s
        ``part.state.error``; 1.18.32's ``PermissionRejectedError`` carries no
        fields (read from the binary), so without the stderr line the sentence
        omits the parenthetical rather than inventing one.
        """
        try:
            return self._denied_turn(stdout or "", stderr or "", exit_code)
        except Exception:  # noqa: BLE001 - classification must not raise
            return None

    def _denied_turn(
        self, stdout: str, stderr: str, exit_code: Optional[int]
    ) -> Optional[Tuple[str, str]]:
        if exit_code not in (0, None):
            return None
        last_reason: Optional[str] = None
        rejected_error: Optional[str] = None
        for event in self._iter_events(stdout):
            part = event.get("part")
            if not isinstance(part, dict):
                continue
            event_type = event.get("type")
            if event_type == "step_finish" and part.get("type") == "step-finish":
                reason = part.get("reason")
                last_reason = reason if isinstance(reason, str) else None
            elif event_type == "tool_use":
                state = part.get("state")
                if not isinstance(state, dict) or state.get("status") != "error":
                    continue
                error = state.get("error")
                if isinstance(error, str) and self._REJECTED_PERMISSION in error.lower():
                    rejected_error = error
        if not last_reason or last_reason == "stop":
            return None
        auto_rejects = list(self._AUTO_REJECTING.finditer(self._ANSI.sub("", stderr)))
        if rejected_error is None and not auto_rejects:
            return None
        found = auto_rejects[-1] if auto_rejects else (
            self._AUTO_REJECTING.search(rejected_error or "")
        )
        detail = ""
        if found is not None:
            detail = f" ({found.group('permission')} {found.group('pattern')})"
        return STATUS_RUNNER_ERROR, (
            f"opencode ended the turn after an auto-rejected permission{detail}; "
            f"no final answer"
        )

    def classify_failure(
        self, stdout: str, stderr: str, exit_code: int = 0
    ) -> Optional[str]:
        """The declared tables over :meth:`vendor_text`, then the denied turn.

        A genuine vendor verdict the executor forwards (auth, rate limit,
        invalid model, sandbox, context length) wins; only otherwise does the
        structural denied-turn check (:meth:`classify_structural`) answer
        ``runner_error``. The executor reads the reason sentence from
        :meth:`classify_structural` itself, since this method returns a
        category and nothing else.
        """
        verdict = super().classify_failure(stdout, stderr, exit_code)
        if verdict in self._VERDICTS_THAT_OUTRANK_A_DENIED_TURN:
            return verdict
        if self.classify_structural(stdout, stderr, exit_code) is not None:
            return STATUS_RUNNER_ERROR
        return verdict

    def describe_failure(self, stdout: str, stderr: str) -> Optional[str]:
        """Recover the reason for a non-zero exit from the event stream.

        OpenCode writes ``error`` events to *stdout* and leaves stderr empty,
        so without this the caller sees only "exited with code 1". Verified
        against a live auth failure, which produced a 304-byte error event on
        stdout and zero bytes on stderr.

        **stdout is the declared channel; stderr is enrichment (D5).** Since
        1.18.x the stdout event can be a wrapper with an ``err_…`` ref and no
        cause — ``UnknownError: Unexpected server error. Check server logs for
        details.`` — while the underlying exception goes to stderr under the
        ``--print-logs --log-level ERROR`` we pass, as a
        ``level=ERROR … error="<text>"`` line. When the stdout message has that
        wrapper shape, the first such stderr value is appended in parentheses,
        so the composed text extends the stdout-only one rather than replacing
        it (``tests/fixtures/opencode/invalid-model.*``). A stderr-only capture
        recovers nothing: the composition is gated on the wrapper being present.

        Diagnostics only, never classification: no marker table is consulted
        here and nothing in the composed string invites a caller to branch on
        it — ``classify_failure`` reads the same bytes for its own verdict.
        """
        messages: List[str] = []
        for event in self._iter_events(stdout):
            if event.get("type") != "error":
                continue
            error = event.get("error")
            if not isinstance(error, dict):
                continue
            name = error.get("name")
            data = error.get("data")
            detail = data.get("message") if isinstance(data, dict) else None
            parts = [p for p in (name, detail) if isinstance(p, str) and p]
            if parts:
                messages.append(": ".join(parts))
        if not messages:
            return None
        if any(self._SERVER_ERROR_WRAPPER in m for m in messages):
            cause = self._stderr_error_value(stderr)
            if cause:
                messages = [
                    f"{m} ({cause})" if self._SERVER_ERROR_WRAPPER in m else m
                    for m in messages
                ]
        return "; ".join(messages)

    #: The stdout wrapper whose cause lives on stderr (opencode ≥ 1.18.x).
    _SERVER_ERROR_WRAPPER = "UnknownError: Unexpected server error"

    #: One ``error="…"`` value on a log line. Anchored on a literal and free of
    #: nested quantifiers, so a 40 KB single-character line costs one linear
    #: scan and no backtracking (``test_every_override_survives_garbage_…``).
    _STDERR_ERROR_VALUE = re.compile(r'(?:^|\s)error="([^"\n]*)"')

    @classmethod
    def _stderr_error_value(cls, stderr: str) -> Optional[str]:
        """The first ``error="…"`` value on a ``level=ERROR`` stderr line."""
        for line in (stderr or "").splitlines():
            if "level=ERROR" not in line:
                continue
            match = cls._STDERR_ERROR_VALUE.search(line)
            if match and match.group(1).strip():
                return match.group(1).strip()
        return None

    def parse_output(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """:meth:`_parse_answer`, plus ``incomplete`` on a turn cut short.

        ``parse_output`` is only reached on exit 0, and one measured exit-0
        stream ends before its answer: the turn ``run`` ended on an
        auto-rejected permission (:meth:`classify_structural`, 1.18.32's
        ``denied_permission_turn_end``). Its last message is narration ("I'll
        read the exact plan rows …"), which the ask lane would otherwise count
        as the answer. The adapter already calls that ending a failure, so the
        parse result says the answer did not finish, ``"incomplete": True``
        (plans/ask-answer-recovery-and-false-success.md D3.1: any adapter that
        fails an exit-0 run on how its stream ended sets it). It is not an
        ``error_code``, so the findings-file channel is unchanged.

        The result also fails with the adapter's own sentence
        (``success: False``, ``error`` from :meth:`classify_structural`,
        ``data: None``), not whatever :meth:`_parse_answer` made of the
        narration ("No valid JSON found in text", or a success). D3.1 sends an
        incomplete run to the ask lane's step 3, which writes ``result["error"]``
        to ``error_<model>.log`` and the ``## Failed Models`` line, so that line
        names the denied permission rather than a JSON miss. ``raw`` is kept.
        """
        result = self._parse_answer(stdout, stderr)
        denied = self.classify_structural(stdout, stderr, 0)
        if denied is not None:
            result = dict(result)
            result["success"] = False
            result["error"] = denied[1]
            result["data"] = None
            result["incomplete"] = True
        return result

    def _parse_answer(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """Parse NDJSON event stream output from OpenCode.

        OpenCode emits one assistant message per step, so a run that uses
        tools produces many ``text`` events — real sessions reach 47. The
        final answer is the last one; earlier ones are narration that may
        itself contain a JSON code block, so extracting from the concatenation
        would return a draft rather than the answer.

        Candidates are therefore ordered by confidence rather than position:
        an exact parse of the whole stream or of the final message is
        unambiguous and is tried first, and only then the loose extraction
        that can match a fragment or an early draft.

        The text parts come from :meth:`_scan_text_parts`, the walk
        :meth:`salvage_text` shares.
        """
        text_parts: List[str] = self._scan_text_parts(stdout).parts

        if not text_parts:
            error = "No text events found in output"
            reason = self.describe_failure(stdout, stderr)
            if reason:
                error = f"OpenCode reported an error: {reason}"
            return {"success": False, "error": error, "raw": stdout, "data": None}

        last = text_parts[-1].strip()
        concatenated = "".join(text_parts).strip()
        # Newline-joined for the loose pass: separate steps are separate
        # messages, and gluing them directly runs the end of one into the
        # start of the next.
        joined = "\n".join(text_parts).strip()

        if not concatenated:
            return {"success": False, "error": "Empty text response", "raw": stdout, "data": None}

        # Exact parses first — they are unambiguous. The concatenation covers
        # a single document that arrived split across parts (a split can fall
        # mid-token, so only a separator-less join reassembles it); `last`
        # covers the ordinary case where the closing message is the answer.
        for candidate in (concatenated, last):
            if candidate:
                direct = self._direct_json(candidate)
                if direct is not None:
                    return direct

        # Then the loose pass, final message first so a late answer wins over
        # a draft quoted earlier in the run.
        result: Dict[str, Any] = {}
        for candidate in (last, joined):
            if not candidate:
                continue
            # Try to extract JSON from the text (may be in code blocks)
            result = extract_json_from_text(candidate, prefer_arrays=True)
            if result.get("success"):
                return result

        return result

    def salvage_text(self, stdout: str) -> Optional[str]:
        """The last assistant message's text, for the salvage gate (D4.1/D4.4).

        opencode's stdout is transport: every ``tool_use`` event carries the
        tool's input and output (a ``grep`` of the plan, a directory listing),
        and ``step_finish`` carries token counts. Judged whole by
        ``has_salvageable_json``, a tool part's arrays read as findings — the
        exit-0 ``denied_permission_turn_end`` capture, whose only text is
        narration, passed the gate that way.

        The answer is the text of the **last** assistant message: one message
        per step, so the last ``messageID`` the stream names, and that step's
        text parts joined in order (:meth:`_scan_text_parts`). On a finished run
        that is the closing step's text, the answer :meth:`parse_output` reads.
        On a run killed mid-step it is that unfinished step's text — ``""``
        when it had printed none yet — never an earlier step's narration
        (plan D4.2: earlier messages are dropped, not joined, because narration
        can quote an example array). opencode emits a text part only once it is
        complete (``part.time.end``), so a reply cut mid-print leaves no text of
        its own behind.

        * ``None`` when no line is an opencode event (not this adapter's
          stream);
        * ``""`` when the last message has no text part — a verdict, final;
        * otherwise that message's text.

        Never raises: a failed walk is ``""``, the reading the caller would give
        a raise anyway.
        """
        try:
            scan = self._scan_text_parts(stdout or "")
            if not scan.saw_event:
                return None
            return "".join(scan.last_message)
        except Exception:  # noqa: BLE001 - the hook must never raise
            return ""
