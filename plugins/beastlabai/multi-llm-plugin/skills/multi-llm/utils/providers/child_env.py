"""The environment a provider CLI is spawned with, built one way for both lanes.

Git's non-interactive environment (:func:`git_env`), the credential-strip and
vendor-backend policies, the deny-by-default allowlist and its matrix, the
skill's own Python environment kept out of a runner, and
:func:`build_child_env`, which composes them in a fixed order. The merged
config is read through late imports of ``utils.provider_registry``, which
imports this package. ``base`` re-exports every name here for reading
(docs/development/providers.md#the-provider-base-modules).
"""

import inspect
import os
import sys
from dataclasses import dataclass
from typing import Any, Collection, Dict, List, Mapping, Optional, Tuple

from ..process_state import process_cache

from . import types


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
HELPER_WIPE_PROFILES = frozenset({types.PROFILE_GENERATE, types.PROFILE_AGENT_READONLY})

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
    profile: str = types.PROFILE_GENERATE,
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

_ENV_POLICY_WARNED: set = process_cache("utils.providers.child_env._ENV_POLICY_WARNED", set)


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
    defaults. ``claude_code``'s fallback-list read raises instead, on purpose.
    """
    # ``provider_registry`` imports the provider base, which imports this
    # module: a load-time cycle.
    from ..provider_registry import load_config
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

    The CLI axis defaults to the **live registry**, never to a name list: a
    matrix derived from a literal roster silently omits a newer adapter's
    credential, keyring, proxy and CA cells. Its size is therefore
    ``len(registry) × len(platforms) × len(capabilities)``, computed, not typed.
    """
    if provider_names is None:
        # A load-time cycle, as in :func:`_merged_config`.
        from ..provider_registry import _PROVIDERS
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
    ``dispatch_spawn._spawn_in_context`` for the agent-profile lane (which
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
