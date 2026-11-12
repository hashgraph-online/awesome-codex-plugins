"""The one version gate (M14, §5.4) and the help-token gate.

:func:`version_tuple` is the one parse-and-compare rule (:func:`version_newer`
applies it to an installed version read); :func:`version_verdict`
reads an adapter's floor and ceiling together; :func:`read_help_tokens` reads a
CLI's help once per process for the flags an adapter gates. ``base`` re-exports
every name here for reading (docs/development/providers.md#the-provider-base-modules).
"""

import re
import subprocess
import sys
import threading
from dataclasses import dataclass
from typing import Any, Dict, FrozenSet, List, Mapping, Optional, Set, Tuple

from ..process_state import process_cache

from . import types, child_env


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

    :func:`version_tuple` is the single rule both the availability label here
    and the executor's preflight refusal are computed from, so a build can
    never be "too old" for the refusal and fine for the report;
    ``tests/test_version_gate.py`` pins the two against each other.
    """
    return version_tuple(version) < version_tuple(minimum)


# ─────────────────────────────────────────────────────────────────────────────
# M14 (§5.4, §5.4.1) — ONE version gate.
#
# What "one gate" means concretely:
#
#   * **One parse-and-compare rule** — :func:`version_tuple`, used by
#     `_version_below` (the availability *label*), by the executor's
#     preflight *refusal* and, through :func:`version_newer`, by both lanes'
#     jail-denial wording. A build can no longer be too old for one and fine
#     for the other.
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
VERSION_TOO_LOW = types.Availability.VERSION_TOO_LOW.value
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


def version_newer(installed: str, measured: str) -> bool:
    """Whether the version read from ``installed`` (the first dotted-numeric
    token: ``codex-cli 0.167.0`` reads ``0.167.0``) is newer than ``measured``,
    through :func:`version_tuple`.

    ``False`` when ``installed`` names no dotted version, when ``measured`` is
    empty, or when the comparison fails: it only chooses wording (the "likely
    cause" clause of a jail denial), and wording never ends a refusal.
    """
    found = re.search(r"\d+(?:\.\d+)+", installed or "")
    if not found or not measured:
        return False
    try:
        return version_tuple(found.group(0)) > version_tuple(measured)
    except Exception:  # noqa: BLE001 - a wording choice never ends a refusal
        return False


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
        configured = child_env._provider_block(name, anchor).get("max_version_exclusive")
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
        child_env._warn_policy_once(
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
_HELP_TOKENS_LOCK = threading.Lock()
_HELP_TOKENS: Dict[Tuple[str, Tuple[str, ...]], FrozenSet[str]] = process_cache(
    "utils.providers.version_gate._HELP_TOKENS", lock=_HELP_TOKENS_LOCK
)

#: One WARN per declined capability per process, not one per dispatch.
_GATE_WARNED: Set[Any] = process_cache("utils.providers.version_gate._GATE_WARNED", set)


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
