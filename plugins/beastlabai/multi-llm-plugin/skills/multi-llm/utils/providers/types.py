"""The provider vocabulary: the words and records adapters and callers share.

The three invocation profiles, the structured-output retry budget, the usage
and config-auth words, :class:`InternalRetryEnvelope`, :class:`StructuredSchema`
and the refusals around it, :class:`SetupHints`, and the availability verdict
(:class:`Availability`, :class:`AvailabilityReport`). It imports no other module
of the package. ``base`` re-exports every name here for reading
(docs/development/providers.md#the-provider-base-modules).
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional, TYPE_CHECKING, Tuple

if TYPE_CHECKING:  # the annotation only: base imports this module
    from .base import LLMProvider

from ..retry_ladder import STATUS_AUTH_FAILED


#: The three invocation profiles (D3e). ``generate`` is today's callee path (no
#: tools, no workspace); ``agent-readonly`` is an agentic invocation with writes
#: denied by the runner's own sandbox/permission mechanism and is what every
#: read/analyze subagent runs under; ``agent-write`` is the implement/apply path.
PROFILE_GENERATE = "generate"
PROFILE_AGENT_READONLY = "agent-readonly"
PROFILE_AGENT_WRITE = "agent-write"


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
# `runner_preflight._detect_auth` and by `describe_availability` — so this adds
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
# `is_available()` is a bare `shutil.which` in every adapter, which
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
