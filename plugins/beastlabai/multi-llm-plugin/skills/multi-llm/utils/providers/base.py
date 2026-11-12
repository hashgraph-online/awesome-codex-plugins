"""Base protocol for LLM CLI providers.

This module is :class:`LLMProvider` and its fallback timeout. The rest of what
adapters import from here lives in seven modules beside it, one job each
(docs/development/providers.md#the-provider-base-modules):

* ``types``: profiles, usage and auth words, the retry envelope, the
  structured-output schema and refusals, setup hints, availability;
* ``reasoning``: the reasoning-effort ladder;
* ``failure_classifier``: the marker tables, ``classify_streams`` and
  ``match_streams``, and the two default pattern sets;
* ``stdout_shape``: where an envelope adapter's JSON envelope sits in stdout;
* ``child_env``: git's environment, the env policies and allowlist,
  ``build_child_env``;
* ``version_gate``: the version verdict and the help-token gate;
* ``sandbox_rungs``: the sandbox fallback's rungs, write posture and notices.

Every name that moved is still readable here (:data:`_MOVED`), **for reading
only**: ``base.X`` and ``from .base import X`` return the owner's current
object, but a patch or assignment here only shadows the name in this module and
reaches no code. Patch a moved name where it lives;
``tests/test_provider_base_moved_names.py`` fails any test that patches one here.
"""

import os
import re
import shutil
import sys
from abc import ABC, abstractmethod
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
    Tuple,
)

# The status vocabulary is the retry ladder's, never a second copy of it.
# Adapters and callers read ``STATUS_*`` through this module, so it stays
# imported here; the classifier that uses it is ``failure_classifier``.
from ..retry_ladder import (  # noqa: F401 - re-exported
    STATUS_AUTH_FAILED,
    STATUS_CONTEXT_LENGTH_EXCEEDED,
    STATUS_RATE_LIMITED,
    STATUS_RUNNER_ERROR,
    STATUS_SPAWN_FAILED,
    STATUS_TIMEOUT,
)

from . import (
    types,
    reasoning,
    failure_classifier,
    child_env,
    version_gate,
    sandbox_rungs,
)
from . import stdout_shape  # noqa: F401 - read only through the re-export table below


# ---------------------------------------------------------------------------
# The names that moved to the modules beside this one
# ---------------------------------------------------------------------------

#: Every top-level name of the seven modules split out of this one, by owner,
#: lowest first. They are read-only re-exports (see the module docstring):
#: reading one here returns the owner's current binding, and ``dir()`` lists
#: them. Nothing is copied into this module, so a patch of the owner shows
#: through here, and :class:`LLMProvider` reaches each one through its owner at
#: every call.
_MOVED: Dict[str, Tuple[str, ...]] = {
    "types": (
        "AUTH_STATE_CONFIG",
        "AVAILABILITY_BY_STATUS",
        "Availability",
        "AvailabilityReport",
        "CONFIG_AUTH_DECLARED",
        "CONFIG_AUTH_UNKNOWN",
        "InternalRetryEnvelope",
        "MAX_STRUCTURED_OUTPUT_RETRIES",
        "NAMED_UNAVAILABILITY",
        "PROFILE_AGENT_READONLY",
        "PROFILE_AGENT_WRITE",
        "PROFILE_GENERATE",
        "ProfileUnsupported",
        "ReadOnlyInvocationRefused",
        "STRUCTURED_OUTPUT_RETRY_ENV",
        "SetupHints",
        "StructuredOutputUnavailable",
        "StructuredSchema",
        "USAGE_FULL",
        "USAGE_NONE",
        "USAGE_PARTIAL",
        "availability_from_failure",
    ),
    "reasoning": (
        "LADDER_POSITION",
        "LADDER_RUNGS",
        "NO_REASONING_LADDER",
        "REASONING_LADDER",
        "ReasoningLadder",
        "SECOND_AXIS_VARIANTS",
        "UNADVERTISED_RUNGS",
        "split_reasoning_effort",
    ),
    "failure_classifier": (
        "AUTH_ERROR_PATTERNS",
        "CATEGORY_CONNECTION_ERROR",
        "CATEGORY_INVALID_MODEL",
        "CATEGORY_PERMISSION_DENIED",
        "CATEGORY_SANDBOX_UNAVAILABLE",
        "CATEGORY_SERVER_ERROR",
        "CLI_REFUSAL_MARKERS",
        "CONNECTION_ERROR_MARKERS",
        "CONTEXT_OVERFLOW_MARKERS",
        "INVALID_MODEL_MARKERS",
        "LAUNCH_DIAGNOSTICS_NONE",
        "LAUNCH_DIAGNOSTICS_STDERR",
        "LAUNCH_DIAGNOSTICS_VALUES",
        "LAUNCH_FAILURE_MARKERS",
        "MISSING_BINARY_EXIT_CODE",
        "RATE_LIMIT_PATTERNS",
        "RETRYABLE_FAILURE_CATEGORIES",
        "SANDBOX_HINT_MARKER",
        "SANDBOX_MARKERS",
        "SANDBOX_PROBE_INCONCLUSIVE_MARKERS",
        "SERVER_ERROR_MARKERS",
        "SHARED_RATE_LIMIT_MARKERS",
        "SHELL_REFUSAL_MARKERS",
        "STDERR_LAUNCH_FAILURE_MARKERS",
        "StreamMatch",
        "TIMEOUT_MARKERS",
        "_CONTEXT_WINDOW",
        "_ERROR_CONTEXT",
        "_SANDBOX_HINT_CHARS",
        "_STREAM_PATTERNS",
        "_first_marker_match",
        "_first_pattern_match",
        "_markers",
        "_matches_marker",
        "_needs_context",
        "classify_streams",
        "context_length_message",
        "exit_zero_failure_category",
        "launch_refusal",
        "match_streams",
        "matches_any",
        "sandbox_hint",
        "sandbox_probe_inconclusive",
        "stream_pattern",
    ),
    "stdout_shape": (
        "STDOUT_AMBIGUOUS",
        "STDOUT_CUT",
        "STDOUT_ENVELOPE",
        "STDOUT_PLAIN",
        "StdoutShape",
        "_JSON_SPACE",
        "_LINE_SPACE",
        "_opens_on",
        "diagnostic_streams",
        "envelope_signature",
        "read_stdout",
        "structural_stdout",
    ),
    "child_env": (
        "CA_BUNDLE_ENV",
        "CA_FAMILY_NATIVE",
        "CA_FAMILY_NODE",
        "ENV_ALLOWLIST_BASE_NAMES",
        "ENV_ALLOWLIST_BASE_PREFIXES",
        "ENV_ALLOWLIST_CAPABILITIES",
        "ENV_ALLOWLIST_DEFAULT",
        "ENV_ALLOWLIST_GREEN",
        "ENV_ALLOWLIST_MEASURED",
        "ENV_ALLOWLIST_OFF",
        "ENV_ALLOWLIST_ON",
        "ENV_ALLOWLIST_PLATFORMS",
        "ENV_ALLOWLIST_POLICIES",
        "ENV_ALLOWLIST_PROFILES",
        "ENV_ALLOWLIST_UNMEASURED",
        "GIT_ENV_GLOBAL",
        "GIT_HELPER_AUTO",
        "GIT_HELPER_KEEP",
        "GIT_HELPER_POLICIES",
        "GIT_HELPER_WIPE",
        "HELPER_WIPE_PROFILES",
        "RunnerEnvProfile",
        "SKILL_ENVIRONMENT_NAMES",
        "SKILL_ENVIRONMENT_SCRIPT_DIRS",
        "STRIP_VENDOR_KEYS_ALWAYS",
        "STRIP_VENDOR_KEYS_AUTO",
        "STRIP_VENDOR_KEYS_DEFAULTS",
        "STRIP_VENDOR_KEYS_FALLBACK",
        "STRIP_VENDOR_KEYS_NEVER",
        "STRIP_VENDOR_KEYS_POLICIES",
        "VENDOR_BACKEND_AUTO",
        "VENDOR_BACKEND_KEEP",
        "VENDOR_BACKEND_POLICIES",
        "VENDOR_BACKEND_STRIP",
        "_ENV_POLICY_WARNED",
        "_merged_config",
        "_path_keys",
        "_provider_block",
        "_provider_removals",
        "_resolve_policy",
        "_same_path",
        "_skill_environment_on_path",
        "_warn_policy_once",
        "apply_env_allowlist",
        "build_child_env",
        "declared_env_names",
        "env_allowlist_admits",
        "env_allowlist_column",
        "env_allowlist_column_is_green",
        "env_allowlist_enabled",
        "env_allowlist_for",
        "env_allowlist_matrix",
        "env_allowlist_policy",
        "git_env",
        "reset_env_policy_warnings",
        "skill_environment_names",
        "skill_environment_path",
        "strip_vendor_keys_policy",
        "vendor_backend_policy",
        "wipes_credential_helper",
    ),
    "version_gate": (
        "GATE_PROBE_TIMEOUT_S",
        "ModelVerdict",
        "VERSION_ABOVE_VERIFIED",
        "VERSION_OK",
        "VERSION_TOO_LOW",
        "VERSION_TOO_NEW",
        "VERSION_UNREAD",
        "VersionVerdict",
        "_CEILING_VERSION_RE",
        "_FLAG_TOKEN_RE",
        "_GATE_WARNED",
        "_HELP_TOKENS",
        "_HELP_TOKENS_LOCK",
        "_upgrade_suffix",
        "_version_below",
        "_version_token",
        "read_help_tokens",
        "reset_flag_gate_cache",
        "version_ceiling",
        "version_newer",
        "version_tuple",
        "version_verdict",
        "warn_gate_once",
    ),
    "sandbox_rungs": (
        "CODEX_HOME_CHECK_MARKER",
        "HOST_POSTURE_FULL_ACCESS",
        "HOST_SANDBOX_POSTURE_ENV",
        "INCIDENTAL_LANE_EXECUTOR",
        "INCIDENTAL_LANE_FANOUT",
        "JAIL_DENIED_MARKER",
        "JailContext",
        "JailRequest",
        "MODE_CHECK_MARKER",
        "SANDBOX_BYPASSED_MARKER",
        "SANDBOX_CANARY_DENIED",
        "SANDBOX_CANARY_NOT_DENIED",
        "SANDBOX_CONTAINMENT_INCIDENTAL",
        "SANDBOX_FALLBACK_AUTO",
        "SANDBOX_FALLBACK_CONTAINED",
        "SANDBOX_FALLBACK_MARKER",
        "SANDBOX_FALLBACK_OFF",
        "SANDBOX_FALLBACK_POLICIES",
        "SANDBOX_FALLBACK_PROFILES",
        "SANDBOX_INCIDENTAL_MARKER",
        "SANDBOX_RUNG_LANDLOCK",
        "SANDBOX_RUNG_PLUGIN_LANDLOCK",
        "SANDBOX_RUNG_RETIRED_MARKER",
        "SANDBOX_RUNG_UNSANDBOXED",
        "SANDBOX_WRITE_FALLBACK_PROFILES",
        "SKIP_RUNG_ENV",
        "SandboxRung",
        "WALK_OUTCOME_SKIPPED_BY_SWITCH",
        "WRITE_SCOPES",
        "WRITE_SCOPES_BY_CONSENT",
        "WRITE_SCOPES_ON_RUNG",
        "WRITE_SCOPE_PLAN_FILE",
        "WRITE_SCOPE_REPO_WIDE",
        "WRITE_SCOPE_TASKS",
        "WritePostureConsent",
        "_INCIDENTAL_RESIDUALS_EXECUTOR",
        "_INCIDENTAL_RESIDUALS_FANOUT",
        "_WALK_OUTCOME_RETIRED",
        "_WALK_OUTCOME_SKIPPED",
        "_quoted_tail",
        "canary_marker_shell_words",
        "host_write_posture_consent",
        "rung_is_incidental",
        "rung_probe_said_removed",
        "rung_removed_for_version",
        "sandbox_bypassed_notice_text",
        "sandbox_fallback_notice_text",
        "sandbox_incidental_notice_text",
        "sandbox_rung_allowed",
        "sandbox_rung_id",
        "sandbox_rung_retired_notice",
        "sandbox_walk_clause",
        "skip_rung_requested",
        "write_consent_allows",
        "write_rung_allowed",
    ),
}
_MOVED_TO: Dict[str, str] = {
    name: module for module, names in _MOVED.items() for name in names
}


def __getattr__(name: str) -> Any:
    """A moved name, read from the module that defines it now."""
    owner = _MOVED_TO.get(name)
    if owner is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    try:
        return getattr(globals()[owner], name)
    except AttributeError:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from None


def __dir__() -> List[str]:
    """This module's own names and the moved ones it re-exports."""
    return sorted({*globals(), *_MOVED_TO})


#: The slot timeout, in seconds, for a provider the merged config has no
#: ``providers.<name>.default_timeout`` for. The per-provider number lives in
#: ``providers.yaml`` alone; the base layer ships a row for every registered
#: adapter (``tests/test_provider_roster.py``), so this is reached only by a
#: config read that failed or a test double. One value for every adapter, so
#: no class carries a second number that looks authoritative and is not
#: (docs/configuration.md#provider-blocks).
DEFAULT_TIMEOUT_S = 1200


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

    # Minimum seconds between two dispatches of this provider in one fan-out
    # (0 = never throttled), retries included (``utils/launch_limiter.py``);
    # dispatches of different providers never wait on each other. Declare a
    # value only for a CLI with a *measured* concurrent-start fault, and keep it
    # here rather than in ``providers.yaml``, which a cloned repository can
    # layer over.
    LAUNCH_STAGGER_S: float = 0.0

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

    # Where ``build_command`` puts the prompt in the argv it returns.
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
    # block (``prompt_channels.render_output_location``).
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
    #: names. An adapter
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
    # adapter opts in by overriding them, and the provider tests (``tests/test_provider_*.py``)
    # cross-checks every declaration against the members actually implemented so
    # the data cannot drift from the code.
    # ------------------------------------------------------------------

    #: Invocation profiles this adapter really implements. ``generate`` is
    #: implicit for every adapter (that is ``build_command``); anything else must
    #: be backed by a real ``build_agent_command`` branch.
    agent_profiles: Tuple[str, ...] = (types.PROFILE_GENERATE,)

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
    #: unable to read such a path.
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
    # ``tests/read_only_modes.yaml`` (the record of write-restricting
    # mechanisms). ``prompt_channels.render_diff_access`` renders the code-review
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
    usage_support: str = types.USAGE_NONE

    #: What the vendor CLI does *inside* one awaited subprocess before it returns.
    #: ``None`` means unmeasured: the ladder then assumes a single
    #: request and refuses to hand the adapter a retry-count env var.
    #:
    #: The converse is a test, not a convention — an adapter whose ``get_env``
    #: sets a retry-shaped variable while this stays ``None`` is a budget bug,
    #: because rule 4 would subtract one request's worth of wall clock from
    #: the deadline while the child quietly makes several.
    #:
    #: An adapter whose envelope depends on the *resolved* slot timeout (as
    #: claude-code's does — its wall is 4 × ``API_TIMEOUT_MS``, itself derived)
    #: overrides this with a property, so the declaration and the emitted env are
    #: one derivation rather than two copies of it.
    internal_retries: Optional[types.InternalRetryEnvelope] = None

    #: Whether this adapter really emits a schema flag when handed a ``schema=``.
    #: ``False`` is the default and the honest one: the default
    #: builders below **ignore** ``schema`` entirely, so a caller that assumed
    #: otherwise would be reading prose as validated output.
    #:
    #: The caller reads this **before** dispatch: ``False`` ⇒ the phase runs its
    #: prompt-level JSON path and the result is marked ``recovered`` /
    #: ``unvalidated``, never ``native``. Only ``claude-code`` and
    #: ``codex`` set it ``True``, and an adapter that sets it ``True`` while
    #: emitting no flag is a bug ``tests/test_structured_output.py`` catches.
    structured_output_support: bool = False

    #: How this adapter carries a schema: ``"inline"`` (claude's
    #: ``--json-schema <json>``) or ``"file"`` (codex's
    #: ``--output-schema <FILE>``). The contract asymmetry, **declared** so
    #: the caller knows whether to materialize a sidecar without branching on an
    #: adapter name. Meaningless while ``structured_output_support`` is ``False``.
    structured_output_transport: str = "inline"

    #: argv that prints the CLI version, the oldest release whose streams this
    #: parser is known to handle, and the release the shipped parser fixtures
    #: were captured from (D3m). Empty means "not declared" — the executor
    #: records ``unknown`` and warns rather than blocking.
    #:
    #: **: a declared floor carries a comment naming the FEATURE it
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

    #: M14 — the first build this release **refuses**, exclusive, or ``""``
    #: for "no ceiling". The mirror of ``min_version`` and subject to the same
    #: rule: it carries a comment naming the feature (or the breakage) behind it.
    #: Overridable per install through ``providers.<name>.max_version_exclusive``
    #: (:func:`version_ceiling`), because a vendor can ship a broken build
    #: between two releases of this repo and pinning it must not require an
    #: adapter edit. A ceiling is a **refusal**, unlike ``verified_version``'s
    #: warning: the two are different claims, and merging them would either
    #: block every new release or refuse nothing.
    max_version_exclusive: str = ""

    #: M14 — the argv, after the binary, that prints the help
    #: documenting this adapter's gated flags. An adapter whose flags live on a
    #: subcommand declares that subcommand here (``("run", "--help")``); the
    #: default is the CLI's top-level help.
    help_argv: Tuple[str, ...] = ("--help",)

    #: Flags this adapter emits **unconditionally** because each
    #: was verified *functionally* at the declared ``min_version``, not merely
    #: found in help text. The shared gate answers :meth:`supports_flag` ``True``
    #: for these **without probing**: there is no release in the supported range
    #: that would need gating, and a runtime probe would only add a failure mode.
    #:
    #: This is the gate's one exemption, written as data rather than as prose
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
        ``profile``, or ``None``.

        ``None`` — the default, and the answer for every adapter without an OS
        sandbox of its own — means "no fallback exists here": a dispatch under
        this profile either runs sandboxed or is refused, and no config key can
        change that. An adapter that overrides this answers one of
        :data:`SANDBOX_FALLBACK_POLICIES`, read through the normal config
        layering, and **only for a profile in**
        :data:`SANDBOX_FALLBACK_PROFILES` — or, for an adapter that declares a
        write ladder, for ``agent-write`` while its
        opt-in is in force, and then only a policy :func:`write_rung_allowed`
        reads: a wrapping, ``incidental``-grade rung under ``auto``. Every other
        adapter answers ``None`` for ``agent-write`` whatever the config says.
        Every gate that consults this
        (``review_orchestrator_base.sandbox_refusal``,
        ``sandbox_walk._detect_sandbox``) requires *all five* of: the
        probe verdict ``unavailable`` (never ``unknown`` — a probe that could
        not be read must not widen anything), a rung the walk selected, this
        answer permitting that rung (:func:`sandbox_rung_allowed`: ``auto``
        reaches every rung, ``contained`` a contained one only, ``off`` none),
        a read-only profile, and the adapter declaring the hook at all.
        """
        return None

    def sandbox_fallback_rungs(self, profile: str) -> Tuple["sandbox_rungs.SandboxRung", ...]:
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
        context: Optional["sandbox_rungs.JailContext"] = None,
        consent: Optional["sandbox_rungs.WritePostureConsent"] = None,
    ) -> List[str]:
        """Rewrite a rendered ``argv`` onto fallback ``rung`` of this adapter's
        ladder, for a ``profile`` in :data:`SANDBOX_FALLBACK_PROFILES` (or the
        adapter's write ladder, :data:`SANDBOX_WRITE_FALLBACK_PROFILES`).

        ``context`` is the attempt's :class:`JailContext`, handed only for a
        wrapping rung (the plugin-landlock jail): its ``tmpdir`` and write
        scope reach the CLI argv (``developer_instructions``). A wrapping rung
        with no context must raise, never render the bare in-CLI atoms.
        ``consent`` is F5's :class:`WritePostureConsent`, the one way a write
        profile renders the uncontained rung.

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
        base_model, _effort = reasoning.split_reasoning_effort(
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

    #: M13 — an optional **metadata** readout: the cheap, non-generating
    #: argv that reports what a *status* surface prints beside the auth verdict
    #: (a plan tier, an entitlement), and nothing else. It is emphatically **not**
    #: a second auth probe: :meth:`classify_auth_probe` never sees it, no verdict
    #: is derived from it, and a run that cannot read it reports nothing rather
    #: than reporting a state. Empty — the default for every adapter — means this
    #: CLI has no such readout, and the status row simply has less to say.
    #:
    #: It is spawned only by the human-invoked status path
    #: (``install-host --check`` row 5, through
    #: :func:`utils.runner_preflight.probe_setup_metadata`), never by a dispatch
    #: preflight: the facts it carries change nothing about whether a child may
    #: start, so paying a subprocess for them once per phase would be cost
    #: without a decision.
    setup_probe: Tuple[str, ...] = ()

    #: M13 — how a human installs this CLI, verbatim. It is printed, and
    #: **never run**: no auto-install, because installing a vendor's binary
    #: because a probe said ``binary-missing`` crosses the same trust boundary
    #: M16 was declined on. Empty means "not declared", which is the honest
    #: state for a CLI whose install route this repo has not measured.
    install_hint: str = ""

    #: M13 — one sentence naming what this CLI's credential actually *is*
    #: (a profile directory, an OS keyring, an env var), for the adapters where
    #: ``login_cmd`` is not the whole story. Declared data only: it is rendered
    #: beside a probe verdict, so it may never carry a credential, a path from
    #: the environment, or probe output.
    auth_hint: str = ""

    #: Substrings that identify a login/credential notice on either stream, so a
    #: logged-out CLI lands on D3k rung 1 (``auth_failed``, no retry) instead of
    #: burning the retry budget as generic runner noise (D3c).
    auth_error_patterns: Tuple[str, ...] = failure_classifier.AUTH_ERROR_PATTERNS

    #: Substrings that identify a rate-limit / quota / overloaded response. A
    #: 429 is **not** a transport failure (D3i): it is retried with backoff and
    #: jitter and does not consume the retry budget, so it needs its own
    #: classification rather than being absorbed by "no parsed text". The bare
    #: status code is matched **with context** (see :func:`stream_pattern`) — a
    #: substring test would find it inside a cost or a token count and hand a
    #: never-retried failure an unlimited retry path.
    rate_limit_patterns: Tuple[str, ...] = failure_classifier.RATE_LIMIT_PATTERNS

    #: Regexes that make an **exit-0** run a failure. Four shipped CLIs
    #: report a provider failure with exit code 0 — goose, aider, cline and
    #: cursor-agent (measured in all six auth states) — so for them the
    #: exit code carries no verdict at all and only a stream marker does. These
    #: are consulted **last** in :func:`classify_streams`: they say "this run
    #: failed", never *why*, so every specific category gets its chance first.
    #:
    #: Empty for an adapter whose exit code is authoritative. Regexes rather than
    #: substrings because the markers are structured-JSON fragments
    #: (``"finishReason":"error"``) whose boundaries the substring matcher's
    #: separator rules were never designed for.
    exit_zero_failure_markers: Tuple["Pattern[str]", ...] = ()

    #: Whether an **exit-0 failure** (exit 0, no usable answer) is classified
    #: at all. On such a run stdout is usually the model's own answer, prose
    #: quoting whatever the plan says about 429s and 401s, so a verdict may come
    #: only from text the CLI itself wrote. ``True`` is a reviewed claim about
    #: this adapter's envelope: :meth:`classify_exit_zero` never reads the
    #: model's answer, in a complete envelope or an interrupted one. ``False``
    #: (the default, and identity :meth:`vendor_text`'s only honest answer)
    #: leaves the run unclassified on both lanes: the fan-out stops on it, the
    #: executor keeps its parse failure's own retry. Read through
    #: :func:`exit_zero_failure_category` only; the per-adapter decisions and
    #: ``tests/test_exit_zero_prose_matrix.py`` are the review
    #: (docs/development/delegation.md#read-and-analyze-executor).
    EXIT0_CLASSIFIABLE: bool = False

    #: Where this CLI's launch diagnostics live, one of the
    #: ``LAUNCH_DIAGNOSTICS_*`` values: the text the batch-fatal
    #: ``sandbox_unavailable`` and ``spawn_failed`` rows may read
    #: (:meth:`launch_diagnostics`). Every shipped adapter declares it in its
    #: own class with the captures it rests on
    #: (``tests/test_launch_diagnostics.py``); the base value is for test doubles.
    #: See docs/development/providers.md#launch-diagnostics.
    LAUNCH_DIAGNOSTICS: str = failure_classifier.LAUNCH_DIAGNOSTICS_STDERR

    #: How this CLI's one JSON envelope opens (:func:`envelope_signature`),
    #: for an adapter whose JSON mode prints the answer inside one; empty for
    #: every other. Its :meth:`parse_output` and :meth:`vendor_text` read
    #: stdout through :func:`read_stdout` (:func:`diagnostic_streams`).
    ENVELOPE_SIGNATURE: Tuple["Pattern[str]", ...] = ()

    #: The fields of that envelope that hold the model's words, which
    #: :meth:`envelope_diagnostics` takes out.
    ENVELOPE_ANSWER_FIELDS: Tuple[str, ...] = ()

    def envelope_diagnostics(self, envelope: Dict[str, Any]) -> Dict[str, Any]:
        """One envelope record as a failure verdict may read it.

        Base: without :attr:`ENVELOPE_ANSWER_FIELDS`, whatever the envelope's
        flags say, so the vendor's own refusal fields stay. Removal only, into
        a new dict (:func:`diagnostic_streams` compares it with the record).
        """
        return {
            key: value for key, value in envelope.items()
            if key not in self.ENVELOPE_ANSWER_FIELDS
        }

    def launch_diagnostics(self, stderr: str) -> str:
        """The part of ``stderr`` the batch-fatal launch rows may read.

        ``stderr`` unchanged under ``stderr``, ``""`` under ``none``. An
        override may only remove, and blanks what it drops (spaces of the same
        length) so a match offset still indexes ``stderr`` (:func:`match_streams`).
        """
        if self.LAUNCH_DIAGNOSTICS == failure_classifier.LAUNCH_DIAGNOSTICS_NONE:
            return ""
        return stderr or ""

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
        ``attempt_classifier._classify_failed_run`` forwards exactly
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
        (``command_execution`` output and ``agent_message`` prose); each keeps
        only what the vendor itself wrote.

        **And it is narrower again on an exit 0 that left no answer**: stdout
        is then usually the model's own answer, prose instead of the JSON
        asked for. So aider (the span between its banner and its trailing
        accounting line), cline (content events, ``done`` and a finished
        ``run_result``) and kimi (``assistant`` and ``tool`` records) drop it
        here too. The six adapters whose JSON mode prints one envelope
        (claude-code, cursor-agent, gemini, grok, agy, goose) drop its answer
        fields on every exit code, through one reduction,
        :func:`diagnostic_streams`. What an exit 0 is classified on at all is
        :meth:`classify_exit_zero`'s, behind :attr:`EXIT0_CLASSIFIABLE`.

        A caller-supplied ``vendor_text=`` argument could not fix it: every
        existing call site would have to opt in, and the fixture rig calls
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
          parse of an envelope the adapter does not control. The one stdout
          dropped on purpose is :func:`diagnostic_streams`' cut or ambiguous
          envelope, where no text can be told to be the CLI's: a refusal that
          reached us only there is a bounded retry, never a verdict a model
          could write.
        * **stderr is not reduced** by any shipped override: the echo lives in
          the structured stdout envelope, and the diagnosis a real failure
          carries must reach the tables untouched. There are two exceptions.
          qwen-code's drops a single named advisory line (its ripgrep fallback
          notice, whose ``EACCES`` is not a diagnosis) and nothing else.
          kilocode's keeps only the lines it paints as its own ``Error:``,
          colour off, because the rest of its stderr is a banner and a tool
          trace naming what the model read; its stdout, the plain answer, goes
          entirely.

        Applied in exactly two places. :meth:`classify_failure` applies it **to
        classify**. ``attempt_classifier._classify_failed_run`` applies it a
        second time **to quote, never to classify**: once the verdict is in, it
        re-runs :func:`match_streams` over the reduced capture so the failure
        reason quotes the text that decided the verdict rather than a stream
        tail that may not contain it, and the re-scan's result never changes
        the verdict. Nothing else applies it. The module-level
        :func:`classify_streams` (and its quote-only twin
        :func:`match_streams`) deliberately does **not** grow it:
        Lane A's error-line fallback calls that function with no adapter in
        hand, and depends on it staying the one rule both lanes share.
        :meth:`classify_auth_probe`'s haystack — the second place
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
        of the rule. That split is the point: before it, Lane A carried
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
        a credential problem (the root-cause-before-auth rule).

        Every declared pattern is still matched through :func:`stream_pattern`,
        never as a bare substring: the sets contain a status code (``429``) and
        short words (``unauthorized``) that occur inside numbers and longer
        tokens a runner routinely prints.

        One thing happens before the rule runs: :meth:`vendor_text` reduces the
        capture to the part the *vendor* wrote, so an adapter that echoes our
        prompt back into its envelope stops classifying our own words. The base
        implementation is identity, so an adapter that does not override it is
        byte-for-byte what it was. The two batch-fatal launch rows then read
        only :meth:`launch_diagnostics` of the reduced stderr.
        """
        stdout, stderr = self.vendor_text(stdout, stderr)
        return failure_classifier.classify_streams(
            stdout,
            stderr,
            exit_code,
            auth_patterns=self.auth_error_patterns,
            rate_limit_patterns=self.rate_limit_patterns,
            exit_zero_markers=self.exit_zero_failure_markers,
            launch_stderr=self.launch_diagnostics(stderr),
        )

    def classify_exit_zero(self, stdout: str, stderr: str) -> Optional[str]:
        """The verdict on an exit-0 capture whose answer did not parse.

        Asked only when :attr:`EXIT0_CLASSIFIABLE` is ``True``, through
        :func:`exit_zero_failure_category`. :meth:`classify_failure` at exit 0,
        which is sound only where :meth:`vendor_text` drops the model's answer
        from every exit-0 shape the CLI prints. ``None`` means nothing the CLI
        wrote was recognised, one transport retry on both lanes. No adapter
        overrides it: what is read is :meth:`vendor_text`'s, so the failure
        quote (``attempt_classifier._classify_failed_run``) is cut from the
        same text on every exit code.
        """
        return self.classify_failure(stdout, stderr, 0)

    def classify_structural(
        self, stdout: str, stderr: str, exit_code: int = 0
    ) -> Optional[Tuple[str, str]]:
        """A structural failure verdict **with its own reason**, or ``None``.

        :meth:`classify_failure` returns a category and nothing else, and
        ``attempt_classifier._classify_failed_run`` forwards only the pattern
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
        if failure_classifier.matches_any(self.auth_error_patterns, haystack):
            return False
        if exit_code != 0:
            return None
        return True

    def describe_setup(self) -> types.SetupHints:
        """This adapter's install / login / status metadata (M13).

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
        return types.SetupHints(
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
        profile: str = types.PROFILE_AGENT_READONLY,
        *,
        timeout_s: Optional[int] = None,
        schema: Optional[types.StructuredSchema] = None,
    ) -> List[str]:
        """Build the argv for an *agentic* invocation under ``profile`` (D3e).

        The executor never picks a raw command: it picks a profile, and the
        adapter renders the invocation whose own sandbox/permission mechanism
        enforces it. There is deliberately no fabricated fallback — an adapter
        with no genuinely read-only mode raises rather than being dispatched with
        write access to an untrusted prompt.

        The profile also scopes the child's git environment, and that
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
                seconds. Keyword-only, optional, and ignored by every
                adapter with no internal cutoff of its own — see
                :meth:`build_command` for why it exists and what ``None`` means.
            schema: the optional structured-output schema. Keyword-only,
                optional, and **ignored by this default implementation** — see
                :attr:`structured_output_support`.

        Returns:
            argv suitable for ``subprocess.run``.

        Raises:
            ProfileUnsupported: always, unless the adapter overrides this.
        """
        raise types.ProfileUnsupported(
            f"{self.name} does not implement the {profile!r} invocation profile "
            f"(declared: {', '.join(self.agent_profiles) or 'none'})",
            provider=self.name,
            profile=profile,
        )

    def build_agent_command_for_transport(
        self,
        prompt: str,
        model: str,
        profile: str = types.PROFILE_AGENT_READONLY,
        transport: str = "argv",
        prompt_file: Optional[str] = None,
        *,
        timeout_s: Optional[int] = None,
        schema: Optional[types.StructuredSchema] = None,
        sandbox_fallback: Optional[str] = None,
        jail_context: Optional["sandbox_rungs.JailContext"] = None,
        write_consent: Optional["sandbox_rungs.WritePostureConsent"] = None,
    ) -> Tuple[List[str], Optional[str]]:
        """``build_agent_command`` plus the text to write to the child's stdin.

        Mirrors :meth:`build_command_for_transport` for the agentic profiles. The
        default implementation assumes the prompt is the **last** argv element
        (which every profile command this repo ships builds that way), so a
        ``stdin`` transport simply drops it and returns it as the child's input.

        ``sandbox_fallback`` is the executor's D6 override, now the
        **rung id** the preflight selected (landlock rung, 2026-09-22): set only
        when ``_detect_sandbox`` recorded a rung for this runner and profile,
        and it reaches the argv through :meth:`apply_sandbox_fallback` —
        which renders *that* rung — *before* the prompt is split off, so the
        rewrite sees the same positions ``build_agent_command`` rendered. A
        bare ``True`` is the pre-rung spelling and means the uncontained rung
        (:func:`sandbox_rung_id`). Ignored by every adapter that keeps the
        default hook.

        ``jail_context`` is the attempt's
        :class:`JailContext`, set by the spawn site only for a dispatch on a
        wrapping rung (the plugin-landlock jail); it reaches
        :meth:`apply_sandbox_fallback` as ``context=`` and is passed only when
        set, so an adapter whose override predates the keyword is called
        exactly as before.
        """
        argv = self.build_agent_command(
            prompt, model, profile, timeout_s=timeout_s, schema=schema
        )
        rung = sandbox_rungs.sandbox_rung_id(sandbox_fallback)
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
        """Could this attempt have written to the tree?

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
        event data.

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

    def stream_watch(self) -> Optional[Callable[[bytes], Optional[str]]]:
        """A fresh watch over one dispatch's stdout, or ``None`` (the default:
        the CLI runs until it exits or its deadline).

        Both spawn lanes ask once per attempt and hand the watch to
        ``process_capture.PipeCapture``, whose drain feeds it each stdout chunk
        as it is read (bytes, cut anywhere). The first non-empty string it
        returns is why the CLI should stop now: the lane stops it through its
        own timeout path, records the attempt as ``runner_error`` with that
        reason as its failure line, and does not send the same dispatch again
        (``RetryLadder`` rule 10). Declare one only for a CLI measured to
        loop without exiting, with a signal no finished or recovering run
        shows; an unrecognised stream must return ``None``, so a CLI release
        that changes its output falls back to the deadline. The watch runs on
        the drain thread: it must be cheap and bounded, and a raise drops it
        (docs/development/providers.md#a-cli-that-loops).
        """
        return None

    def parse_version(self, stdout: str, stderr: str) -> Optional[str]:
        """Recover the CLI version from ``version_cmd`` output (D3m).

        The default finds the first dotted numeric token on either stream, which
        covers ``codex-cli 0.146.0``, ``1.18.12`` and ``2.1.224 (Claude Code)``
        alike. **Both streams are read**: some CLIs banner their version
        to stderr and opencode is stdout-only, so a probe that read one stream
        would report ``unknown`` for whichever half of the roster it guessed
        wrong. Unparseable output is ``None`` (recorded ``unknown`` plus a
        warning, never a block: a CLI that dropped ``--version`` still answers
        prompts fine).
        """

        for text in (stdout or "", stderr or ""):
            match = re.search(r"\b(\d+\.\d+(?:\.\d+)*)\b", text)
            if match:
                return match.group(1)
        return None

    # ── M14 — the shared per-flag capability gate ────────────────
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
        """The environment one help probe runs in — the containment clause.

        Composed by :func:`build_child_env`, the same builder both spawn lanes
        go through, so the flags a run emits cannot depend on which lane asked.
        On top of it: the ``generate`` profile's git block (a probe must never
        reach a credential helper), and ``TERM=dumb`` / a wide ``COLUMNS`` /
        ``NO_COLOR`` so the help is rendered in full — the own history is a
        *truncated* help rendering that hid what a flag required.

        The adapter's ``get_remove_env`` is applied through the builder, which is
        what keeps a probe run from inside a Claude Code session from being
        refused by that CLI's nested-session guard.
        """
        delta = dict(child_env.git_env(types.PROFILE_GENERATE))
        delta.update({"TERM": "dumb", "COLUMNS": "1000", "NO_COLOR": "1"})
        return child_env.build_child_env(self, provider_env=delta) or dict(os.environ)

    def flag_tokens(self, *, runnable: bool = False) -> FrozenSet[str]:
        """Every long option this CLI's own help documents, or ``frozenset()``."""
        binary = self.gate_binary(runnable=runnable)
        if not binary:
            return frozenset()
        return version_gate.read_help_tokens(
            binary, help_argv=tuple(self.help_argv), env=self.gate_probe_env()
        )

    def supports_flag(self, flag: str) -> bool:
        """The gate in its **optional-flag** form: undecidable ⇒ ``False``.

        On an older CLI an unrecognised flag is not a degraded run, it is
        ``unknown option`` and a dead slot, so this declines toward the status
        quo: the flag is omitted, the run proceeds, and the caller emits one WARN
        naming the capability the run is doing without.

        A flag the adapter declares in :attr:`flags_verified_at_floor` is
        supported **without a probe**; the exemption is granted only to a
        flag verified functionally at the declared ``min_version``.
        """
        if flag in tuple(self.flags_verified_at_floor):
            return True
        return flag in self.flag_tokens()

    def missing_flags(self, flags: Iterable[str]) -> Tuple[str, ...]:
        """The gate in its **load-bearing** form: which of ``flags`` is unconfirmed.

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
        tokens = version_gate.read_help_tokens(
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
        schema: Optional[types.StructuredSchema] = None,
        sandbox_fallback: Optional[str] = None,
        cwd: Optional[str] = None,
        jail_context: Optional["sandbox_rungs.JailContext"] = None,
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
                :meth:`build_command`. This is the Lane A leg:
                ``invoke_with_provider`` computes ``effective_timeout`` before it
                builds anything, so the adapter never re-derives it.
            sandbox_fallback: The fan-out's D6 override: the rung
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
                and the adapters render argv byte-for-byte. An adapter that
                wants it overrides this method and declares ``cwd`` on its own
                ``build_command``.

        Returns:
            ``(argv, stdin_text)``; ``stdin_text`` is the text to write to the
            child's stdin. That is the prompt under ``"stdin"``; on ``"argv"``
            it is ``None`` unless the adapter feeds the child interactive
            answers — aider, whose decline supply answers its "Add file to the
            chat?" prompts. This base composition returns ``None`` on ``"argv"``.

        Raises:
            ValueError: when this adapter does not support ``transport``.
        """
        if transport == "argv":
            argv = self.build_command(
                prompt, model, timeout_s=timeout_s, schema=schema
            )
            rung = sandbox_rungs.sandbox_rung_id(sandbox_fallback)
            if rung:
                argv = self.apply_sandbox_fallback(
                    argv, types.PROFILE_GENERATE, rung,
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
    def default_timeout(self) -> int:
        """The fallback slot timeout, :data:`DEFAULT_TIMEOUT_S`, for every adapter.

        Not the timeout a run uses: that is ``providers.<name>.default_timeout``
        from the merged config (``provider_registry.get_provider_timeout``).
        This answers only when that row is missing.
        """
        return DEFAULT_TIMEOUT_S

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
        schema: Optional[types.StructuredSchema] = None,
    ) -> List[str]:
        """Build the command line arguments for invocation.

        Args:
            prompt: The prompt text to send to the LLM.
            model: The model identifier to use for generation.
            timeout_s: The caller's already-resolved outer timeout in whole
                seconds, for the adapters whose CLI has an internal cutoff of
                its own to keep *under* it. Most adapters have no
                such flag and ignore it.

                It is **keyword-only and optional on purpose**. Adapter
                instances are module-level singletons shared across a concurrent
                fan-out, so stashing a per-call timeout on ``self`` would be a
                data race rather than an API; and ``timeout_s=None`` must render
                argv byte-for-byte identical to what the adapter emitted before
                this parameter existed, which is what makes dropping the one
                call site in ``llm_client`` a complete rollback.
            schema: the optional structured-output schema, on the same terms
                and for the same reasons as ``timeout_s``: keyword-only,
                optional, ignored by every adapter that declares no
                :attr:`structured_output_support`, and ``schema=None`` — the
                default and the only value those adapters ever see — renders argv
                **byte-for-byte identical** to today's. That is what keeps every
                existing ``expected_argv.yaml`` row green and what makes the
                per-adapter flag the off switch.

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
        self, model: str, *, anchor: Optional[str] = None,
        profile: Optional[str] = None,
    ) -> version_gate.ModelVerdict:
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
        return version_gate.ModelVerdict(known=None, detail="", suggestions=())

    def config_credential_source(
        self,
        model: str,
        *,
        profile: str = types.PROFILE_AGENT_READONLY,
        anchor: Optional[str] = None,
        cwd: Optional[str] = None,
        env_builder: Optional[Callable[[], Optional[Mapping[str, str]]]] = None,
    ) -> str:
        """Does the dispatch's own config supply this model's credential?

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
        return types.CONFIG_AUTH_UNKNOWN

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
        that block is profile-scoped and this hook has no profile, and it
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
        """This provider's resolved ``git_env.credential_helper``.

        ``MULTI_LLM_GIT_CREDENTIAL_HELPER`` → ``providers.<name>.git_env`` →
        top-level ``git_env`` → ``auto``. Read through the registry accessor
        rather than by indexing the config, exactly like the ``driver.*`` keys.
        """
        # ``provider_registry`` imports this module: a load-time cycle.
        from ..provider_registry import get_git_credential_helper
        return get_git_credential_helper(self.name, anchor=anchor)

    def resolve_env(
        self,
        model: str,
        profile: str = types.PROFILE_GENERATE,
        *,
        credential_helper: Optional[str] = None,
        base_env: Optional[Mapping[str, str]] = None,
        anchor: Optional[str] = None,
        cwd: Optional[str] = None,
    ) -> Dict[str, str]:
        """The full env delta a spawn applies: the git block, then the adapter's.

        The one composition point, called by both spawn sites
        (``llm_client.call_llm`` for the Lane A fan-out under ``generate``, and
        ``dispatch_spawn._spawn`` with the dispatch's own profile), so the git
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
        env = child_env.git_env(profile, credential_helper=policy, base_env=base_env)
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

    # ── M10 — the typed status that sits beside is_available() ────────

    def describe_availability(
        self,
        *,
        auth: Optional[bool] = None,
        version: Optional[str] = None,
        credentials_required: bool = True,
    ) -> types.AvailabilityReport:
        """Why this runner is or is not usable, as a typed state.

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
            return types.AvailabilityReport(
                types.Availability.BINARY_MISSING,
                f"{name}: the CLI is not on PATH.",
            )

        # Only the numeric token survives into the comparison and the sentence —
        # see :func:`_version_token`. ``"unknown"`` carries no token, so the
        # executor's own "version not read" value falls out here for free.
        read = version_gate._version_token(version or "")
        minimum = (self.min_version or "").strip()
        if read and minimum and version_gate._version_below(read, minimum):
            return types.AvailabilityReport(
                types.Availability.VERSION_TOO_LOW,
                f"{name} {read} is older than the {minimum} this release parses; "
                f"upgrade {name} to >= {minimum}{version_gate._upgrade_suffix(self, minimum)}",
            )

        if auth is False and not credentials_required:
            # The probe's verdict is real and still recorded by the preflight;
            # what it may not do is refuse a model the adapter declares serves
            # with no credential present. Mirror that here so the report and
            # the refusal a run would hit cannot name different problems.
            return types.AvailabilityReport(
                types.Availability.READY,
                f"{name} is installed; its auth probe recognised a login notice, "
                f"but this model is declared to need no credential.",
            )
        if auth is False:
            login = (self.login_cmd or "").strip()
            fix = f" Fix: run `{login}`." if login else ""
            return types.AvailabilityReport(
                types.Availability.NEEDS_AUTH,
                f"{name} is installed but its auth probe recognised a login "
                f"notice.{fix}",
            )
        if auth is True:
            return types.AvailabilityReport(
                types.Availability.READY,
                f"{name} is installed and its auth probe came back clean.",
            )

        probe = " ".join(self.auth_check) if self.auth_check else ""
        why = (
            f"`{probe}` was inconclusive"
            if probe
            else f"{name} declares no auth probe"
        )
        return types.AvailabilityReport(
            types.Availability.UNKNOWN,
            f"{name} is installed; {why}, so whether it is logged in could not "
            f"be determined.",
        )
