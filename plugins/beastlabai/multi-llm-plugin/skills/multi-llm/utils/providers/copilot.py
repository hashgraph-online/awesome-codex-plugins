"""GitHub Copilot CLI provider implementation.

`@github/copilot` (proprietary, npm, binary ``copilot``). Everything below is
measured against **1.0.80** in the containerized probe of
`plans/harness-expansion.md` §6 — stub-only, ``--network none``, **no GitHub
account and no GitHub token** — and several measurements contradict the plan's
researched §3.1 contract. Where they do, the measurement is what shipped and the
contradiction is recorded on the member it affects.

**Auth is BYOK and nothing else.** ``COPILOT_PROVIDER_BASE_URL`` is the
activation switch — the vendor's own words are *"Set …BASE_URL to activate BYOK
mode. GitHub authentication is not required"* — so the whole credential surface
is the ``COPILOT_PROVIDER_*`` family. The Copilot-seat path (a fine-grained PAT
carrying "Copilot Requests") is deliberately **not** implemented: §0 bars a
benefit that depends on a subscription nobody holds from justifying adapter work,
and the two paths are mutually exclusive within one run. The only auth work here
is therefore subtractive — see :meth:`CopilotProvider.get_remove_env`.

**Output.** ``--output-format json`` emits JSONL, one object per line, **all on
stdout**. stderr is 0 bytes on every model-path failure and is used only for
argument-parse errors. ``--stream on`` adds two ephemeral records and still emits
the same terminal ``assistant.message``, so one parser serves both stream modes
and ``--stream off`` is a determinism choice rather than a parsing requirement.

**The unwrap trap, and it is the sharpest thing in this adapter.** §3.4's copilot
row says *"drop every ``"ephemeral":true`` record first, then take the assistant
content"*. Dropping ephemerals is **not sufficient on its own**: ``user.message``
is non-ephemeral and *also* carries ``data.content`` — our own prompt, 30 412
bytes of it in the captured fixture. A parser that filters on ``ephemeral`` alone
and takes the first surviving ``data.content`` returns **the prompt as the
answer**, which type-checks, looks plausible in a report and is wrong. The
``type == "assistant.message"`` filter is load-bearing, not decorative, and
:meth:`CopilotProvider.parse_output` keys off it rather than off ``ephemeral``.

**Exit-0 failures exist, and no marker can catch them.** A provider 200 with an
empty body yields process exit 0, ``result.exitCode: 0``, and an
``assistant.message`` whose ``data.content`` is ``""`` — with **no error record
anywhere**. There is no text to match, so
:attr:`CopilotProvider.exit_zero_failure_markers` is empty *by measurement* and
detection is **structural**, in ``parse_output``: an assistant message that
carries no content is a failure however cheerful the envelope is. That is
1.0.80's behaviour, and the check stays because 1.0.80 is still the floor: at
1.0.93 the CLI reports the same empty 200 itself, as a ``session.error``
(``errorType: query``, *"No response was returned…"*, no ``statusCode``) with
exit 1, which the ``session.error`` branch already handles.

**``session.error`` is the real error channel** and §3.1 does not mention it. It
arrives **on stdout with stderr empty** — §6.2's ``stdout-error`` trap in its
exact shape — carrying a structured ``errorType`` (``authentication`` / 401,
``rate_limit`` / 429, ``query`` / 400 and 404) and a ``statusCode``.

**Tool permissions: tier 1, and the help text is wrong.** ``--allow-all-tools``
is documented as *"required for non-interactive mode"*. Measured, it is **not**:
the §6.5 ladder was walked in ascending order with a seeded filesystem canary and
all four rungs produced byte-identical output with a **clean** canary, so rule 1's
ascending stop applies at rung 1. §3.1's bracketed
``[--allow-all-tools --add-dir "$WORKDIR"]`` line is therefore **struck**, not
shipped — this is precisely the case §6.5 exists to catch. ``--add-dir`` is not
emitted at any shipped tier, so §3.1's ``$WORKDIR`` resolution question is moot
for v1: copilot answered a realistic review-plan prompt without the enclosing
worktree. Never ``--yolo`` or ``--allow-all``; both expand to all tools **plus**
all paths **plus** all URLs.

**The permission tier is enforced in env as well as argv, and that is not
belt-and-braces.** ``COPILOT_ALLOW_ALL`` is the environment equivalent of
``--allow-all-tools``: a user with it exported silently promotes the run to tier
4 with no argv change at all. Stripping it is what makes §6.5's recorded tier
enforceable rather than aspirational, and it is a name §3.1's strip list missed.

**Prompt transport: argv and stdin.** Measured on the wire with a 30 414-byte
prompt: piped stdin with ``-p`` **omitted entirely** carried it (stub
``prompt_len=62966`` against 62989 on argv). Two near-misses are recorded so
nobody re-derives them: ``-p -`` does **not** mean stdin — it sends the literal
one-character prompt ``-`` — and a bare ``-`` exits 1. So a multi-KB prompt never
has to be measured against the Windows command-line cap.

**Reasoning effort: supported.** ``--effort`` accepts all seven of
``none, minimal, low, medium, high, xhigh, max`` at 1.0.80 (an invalid level
exits 1 and names the allowed set), confirming §3.1's researched set exactly.

**The image blocker, solved at build time rather than here.** The ``copilot`` npm
entry point is a *loader*: on first run it self-extracts the whole platform
package into ``$XDG_CACHE_HOME/copilot/pkg/linux-x64/<version>/`` — **209 MB**,
~2 s — and executes from there. Under the committed ``posture.yaml`` the tmpfs
mounts default to ``noexec`` and copilot dies with *"failed to map segment from
shared object"*. ``COPILOT_HOME`` does **not** relocate that cache (a direct
answer to §8.2's open question, and the answer is no); ``XDG_CACHE_HOME`` does.

**So this adapter deliberately does NOT set ``XDG_CACHE_HOME``**, and the reason
is worth stating because the probe listed it among the injected names. A
*per-slot* value would re-extract 209 MB on **every spawn**, and a hardcoded
absolute path would be wrong on a host. The cache is meant to be extracted once
and shared, so the correct owner is the environment: the E2E image pins it to a
pre-warmed ``/opt`` path at build time, and on a host the user's own
``XDG_CACHE_HOME`` (or its ``$HOME/.cache`` default) is already right.
``COPILOT_HOME`` — config and state only — is what this adapter isolates per
slot.
"""
import json
import os
import re
import shutil
import sys
import tempfile
import threading
from typing import Any, Dict, List, NamedTuple, Optional, Set, Tuple

from ..json_extractor import extract_json_from_text
from .base import (
    REASONING_LADDER,
    InternalRetryEnvelope,
    LLMProvider,
    ReasoningLadder,
    StructuredSchema,
    split_reasoning_effort,
)

#: Levels accepted by ``copilot --effort`` at 1.0.80, measured one at a time
#: (1.0.93's invalid-level error names the same seven, 2026-10-08).
#: All seven are accepted by the CLI; which of them a given backend honours is
#: server-side and model-dependent, which is why this is a parse-time whitelist
#: rather than a promise about behaviour — and why the declaration is the whole
#: ladder with no local spelling and no per-model cap: the CLI narrows nothing
#: locally, so there is nothing measured for this adapter to narrow either.
EFFORT_LADDER = ReasoningLadder(
    provider="copilot",
    rungs=REASONING_LADDER,
)
REASONING_EFFORTS = EFFORT_LADDER.accepted

#: §3.1's token-limit ladder, rung 3 — the conservative floor.
#:
#: The pair must be emitted **at all** because a catalog miss leaves copilot on
#: defaults small enough to truncate a real plan prompt. But the draft's fixed
#: ``190000``/``32000`` is only safe for large-context slugs: hand a
#: small-context model a declared 190k window and the CLI *believes* it, packs
#: the prompt to fit, and the run dies mid-flight on an upstream 400. The
#: asymmetry is what picks the default — a floor that is too small fails early
#: and legibly (or compacts); a ceiling that is too large fails late and mid-run.
FLOOR_MAX_PROMPT_TOKENS = 32000
FLOOR_MAX_OUTPUT_TOKENS = 8000

#: The output reserve held back from a slug's context window, and the output
#: ceiling this adapter will ever declare. It doubles as §7.4's required per-CLI
#: output bound on the credentialed lane.
#:
#: kimi's live smoke is why this is a real control rather than hygiene: a capped
#: upstream **rejects** an over-large output request rather than clamping it, so
#: an unpinned CLI does not answer at all on those providers.
OUTPUT_RESERVE_TOKENS = 8000

#: §3.1's ladder, rung 2 — a committed per-slug table beside the
#: ``providers.yaml`` model list, which that bullet names as an accepted catalog
#: source alongside OpenRouter's ``/models`` document.
#:
#: A committed table is chosen over a live ``/models`` lookup deliberately: rung
#: 2 must answer **offline** (the provider lane runs ``--network none``), it must
#: not add a network round trip to every spawn, and a value that changes under
#: the adapter would churn the pinned argv contract. Numbers are
#: ``(context_length, top_provider.max_completion_tokens)`` read from
#: OpenRouter's own catalog on 2026-08-18 for the slugs this block ships.
_MODEL_CATALOG: Dict[str, Tuple[int, int]] = {
    # OpenRouter /api/v1/models, 2026-10-22: context_length / max_completion_tokens.
    "openai/gpt-6-luna": (1050000, 128000),
    # Read from OpenRouter's catalog on 2026-08-19 when this became models[0].
    "openai/gpt-5.6-luna": (1050000, 128000),
    "openai/gpt-4.1-mini": (1047576, 32768),
    "openai/gpt-4o-mini": (128000, 16384),
}

#: The vendor's model-id / wire-model split
#: (``COPILOT_PROVIDER_MODEL_ID`` + ``COPILOT_PROVIDER_WIRE_MODEL``) is a second
#: route to rung 2 and is **not** taken. It asks us to name "a well-known base
#: model" for an arbitrary OpenRouter slug, which is a guess wearing a config
#: key; and the explicit pair below is documented to override *both* the catalog
#: and the defaults, so it reaches the same end deterministically. Recorded
#: rather than silently skipped, because the probe recommended it.
_MODEL_ID_SPLIT_DECLINED = True

#: Prefix under ``TMPDIR``, so a directory leaked by a SIGKILL is sweepable by
#: name — the rule ``cursor_agent``'s profile isolation, ``kimi``'s config root
#: and ``qwen-code``'s all follow.
_HOME_PREFIX = "multi-llm-copilot-"

_HOME_LOCK = threading.Lock()
#: Every config root **this process created**. Nothing outside this list is ever
#: removed: a user-pinned ``COPILOT_HOME`` is respected, never deleted.
_HOME_DIRS: List[str] = []
_HOME_ATEXIT_REGISTERED = False

#: The B1 selector set (§2.2 rule 2), emitted as one indivisible set.
#: ``COPILOT_PROVIDER_BASE_URL`` is the **activation switch** for BYOK, so a
#: partial set is not a degraded run — it is a run that falls through to the
#: GitHub seat path.
_BYOK_BASE_URL = "https://openrouter.ai/api/v1"

#: B3 and ambient names, all confirmed present at 1.0.80. Stripped so ambient
#: config cannot re-select a vendor route, silently widen the tool tier, or
#: outrank the key we inject (§2.2 rule 3: adapter wins, ambient loses, no
#: fallback).
_STRIPPED_VENDOR_VARS: Tuple[str, ...] = (
    # The seat path, in the documented precedence order. A token the user's
    # shell already exports for `gh` would otherwise re-enable the GitHub side
    # underneath BYOK -- a 401 today, and quiet quota spend the day a seat
    # exists.
    "COPILOT_GITHUB_TOKEN",
    "GH_TOKEN",
    "GITHUB_TOKEN",
    # SHIP-GATE HOLE, and a §3.1 miss: the env equivalent of --allow-all-tools.
    # Without this strip, §6.5's recorded tier is unenforceable.
    "COPILOT_ALLOW_ALL",
    # Documented to take PRECEDENCE OVER COPILOT_PROVIDER_API_KEY, so a stale
    # one overrides the key this adapter injects. Also a §3.1 miss.
    "COPILOT_PROVIDER_BEARER_TOKEN",
    # New since 1.0.80 (`copilot help environment` at 1.0.93, 2026-10-08): "shell
    # command that prints a fresh API key for each provider request. Takes
    # precedence over COPILOT_PROVIDER_API_KEY." An ambient one would both
    # outrank the key we inject and run a shell command on every request.
    "COPILOT_PROVIDER_API_KEY_COMMAND",
    # "Setting this automatically enables OTel." A user's exported endpoint
    # would turn on telemetry from our spawn, on their behalf, unasked.
    "OTEL_EXPORTER_OTLP_ENDPOINT",
    "COPILOT_OTEL_ENABLED",
    # Determinism: we pass --model, which wins over COPILOT_MODEL (measured).
    # Stripping it keeps the two from disagreeing in a bug report.
    "COPILOT_MODEL",
    "COPILOT_PROVIDER_MODEL_ID",
    "COPILOT_PROVIDER_WIRE_MODEL",
    # Reproducibility: repo-level instructions injected into a review answer.
    "COPILOT_CUSTOM_INSTRUCTIONS_DIRS",
    # Enterprise host selection for the GitHub side we do not use.
    "COPILOT_GH_HOST",
    "GH_HOST",
)

#: The opening of a ``user.message`` record, matched against a line ``json.loads``
#: REJECTED — i.e. a record the stream was cut inside of. Anchored at the line
#: start and requiring the key/value pair to be complete, so it names the echoed
#: record and nothing else; both spellings the committed captures carry
#: (``{"type":"user.message",`` and ``{"type": "user.message",``) match. Used by
#: :meth:`CopilotProvider.vendor_text` only, and only to REMOVE a line.
_CUT_USER_MESSAGE = re.compile(r'^\{\s*"type"\s*:\s*"user\.message"\s*[,}]')


class _CopilotRecords(NamedTuple):
    """What one pass over copilot's JSONL collected (:func:`_scan_copilot_records`)."""

    #: Whether any line parsed as a JSON object (``parse_output``'s test).
    saw_record: bool
    #: Whether any line was a copilot record: a string ``type`` beside a
    #: ``data`` object, or the ``result`` record. A bare answer object on a line
    #: of its own (the ``-s`` shape in ``success-silent.txt``) is neither.
    saw_envelope: bool
    #: Every ``assistant.message`` record's ``data.content``, in order.
    assistant_contents: List[str]
    #: The last ``session.error`` record's ``data``, if any.
    session_error: Optional[Dict[str, Any]]
    #: The last assistant message's text (see :func:`_scan_copilot_records`),
    #: or ``None`` when the stream holds no assistant message at all.
    last_message: Optional[str]


def _is_copilot_record(record: Dict[str, Any]) -> bool:
    """A record of copilot's own envelope, as opposed to a bare JSON answer."""
    kind = record.get("type")
    if not isinstance(kind, str):
        return False
    return isinstance(record.get("data"), dict) or kind == "result"


def _scan_copilot_records(text: str) -> _CopilotRecords:
    """Walk the JSONL once, keyed on record ``type`` (plan: review-run-scope-
    salvage-and-failure-visibility §4, D4.4 — shared by ``parse_output`` and
    ``salvage_text``).

    ``assistant_contents`` and ``session_error`` are ``parse_output``'s inputs,
    collected exactly as before. ``last_message`` is salvage's: the text of the
    most recent assistant message, which is the last ``assistant.message``'s
    ``data.content`` — unless a streamed message (``--stream on``:
    ``assistant.message_start`` / ``assistant.message_delta``, keyed by
    ``data.messageId``) came after it and never closed. A stream killed while
    the answer was printing is that case, and the answer is its
    ``deltaContent``s joined in order. The shipped argv is ``--stream off``, so
    this branch only matters to a stream mode nobody ships yet; it costs a dict.
    """
    assistant_contents: List[str] = []
    session_error: Optional[Dict[str, Any]] = None
    saw_record = False
    saw_envelope = False
    open_deltas: Dict[str, List[str]] = {}
    closed: Set[str] = set()
    latest: Optional[Tuple[str, str]] = None

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except ValueError:
            # A partial trailing line is what a truncated stream looks like;
            # it is not on its own a reason to fail a run that already
            # produced an answer.
            continue
        if not isinstance(record, dict):
            continue
        saw_record = True
        if _is_copilot_record(record):
            saw_envelope = True
        kind = record.get("type")
        data = record.get("data")
        if kind == "session.error" and isinstance(data, dict):
            session_error = data
        elif kind == "assistant.message" and isinstance(data, dict):
            content = data.get("content")
            if isinstance(content, str):
                assistant_contents.append(content)
                latest = ("done", content)
                message_id = data.get("messageId")
                if isinstance(message_id, str):
                    closed.add(message_id)
                    open_deltas.pop(message_id, None)
        elif kind in ("assistant.message_start", "assistant.message_delta") \
                and isinstance(data, dict):
            # Only a string id can be matched to its closing record (and only
            # a hashable one can key the dict — this walk also serves
            # `parse_output`, which must not start raising on a garbage id).
            message_id = data.get("messageId")
            if not isinstance(message_id, str) or message_id in closed:
                continue
            chunks = open_deltas.setdefault(message_id, [])
            delta = data.get("deltaContent")
            if kind == "assistant.message_delta" and isinstance(delta, str):
                chunks.append(delta)
            latest = ("open", message_id)

    last_message: Optional[str] = None
    if latest is not None:
        state, value = latest
        last_message = value if state == "done" else "".join(open_deltas.get(value, []))
    return _CopilotRecords(
        saw_record, saw_envelope, assistant_contents, session_error, last_message
    )


def token_limits_for(model: str) -> Tuple[int, int]:
    """The pair for one model: the committed catalog, else the floor. Full stop.

    Returns ``(max_prompt_tokens, max_output_tokens)`` **for the model handed
    in**, never a process-wide constant and never a pair resolved for a
    different slug. Two inputs decide it and there is no third: the per-slug
    entry in :data:`_MODEL_CATALOG` if the slug is in it, and
    :data:`FLOOR_MAX_PROMPT_TOKENS` / :data:`FLOOR_MAX_OUTPUT_TOKENS` if it is
    not. **There is no config override, and this is not a gap left for later**
    (C9).

    §3.1's draft opened with a rung above these two — ``max_prompt_tokens:`` /
    ``max_output_tokens:`` keys in the copilot block of ``providers.yaml``. The
    affordance is **removed** rather than deferred, because a documented key
    that silently does nothing is worse than no key at all: §8 item 3 fixes a
    provider block at exactly ``default_timeout`` / ``max_concurrent`` /
    ``models``, and ``provider_registry`` **merges an undeclared key and then
    ignores it**, so such an entry would read as a supported setting and be a
    no-op — the footgun §5.1 refuses for a provider-level ``env:`` block. The
    removal costs nothing a user can reach: the key appears in no
    ``providers.yaml``, in no schema and in no instruction text, so there is
    nothing shipped to break, and an override key would be the only member of a
    provider block that is none of the three above.

    **The alternative, recorded as rejected rather than held open**, so the next
    reader finds a decision instead of a gap. Implementing it means a typed
    schema entry, a validation error for a bad value, a merge order defined
    against this catalog, per-provider-versus-per-model semantics, and a test
    asserting a configured pair reaches ``COPILOT_PROVIDER_MAX_PROMPT_TOKENS``
    and ``COPILOT_PROVIDER_MAX_OUTPUT_TOKENS`` in :meth:`CopilotProvider.get_env`'s
    output. That is a typed config feature, and copilot is the only adapter in
    the registry that declares a token budget at all — so it would ship with
    exactly one user, which is what the decision refuses.

    **One condition reopens it and nothing else: a second adapter in the
    registry declaring a token budget.** A user typing the key is *not* that
    condition — the answer to a typo is to make an unknown provider-block key a
    config error naming the three that exist, the way ``driver:`` and
    ``git_env:`` already reject one, and that is a compatibility change with its
    own decision to make, not a ride-along on this one. It is deliberately not
    built here.

    ``tests/test_providers.py::TestCopilotHasNoConfigurableTokenLimits`` pins the
    absence: the same pair comes back for a model with and without a
    ``providers.yaml`` block carrying those keys, so the key cannot be re-added
    half-way.
    """
    known = _MODEL_CATALOG.get(model)
    if known is None:
        return FLOOR_MAX_PROMPT_TOKENS, FLOOR_MAX_OUTPUT_TOKENS
    context_length, max_completion = known
    prompt_budget = max(FLOOR_MAX_PROMPT_TOKENS, context_length - OUTPUT_RESERVE_TOKENS)
    output_budget = min(max_completion, OUTPUT_RESERVE_TOKENS)
    return prompt_budget, output_budget


def _create_home_dir() -> str:
    """A fresh 0700 config root, owned and tracked by this process."""
    global _HOME_ATEXIT_REGISTERED

    path = tempfile.mkdtemp(prefix=_HOME_PREFIX)
    os.chmod(path, 0o700)  # mkdtemp already does this; asserted, not assumed
    _HOME_DIRS.append(path)
    if not _HOME_ATEXIT_REGISTERED:
        import atexit

        atexit.register(cleanup_home_dirs)
        _HOME_ATEXIT_REGISTERED = True
    return path


def isolated_home_dirs() -> Tuple[str, ...]:
    """Every config root this process created and has not yet removed."""
    with _HOME_LOCK:
        return tuple(_HOME_DIRS)


def cleanup_home_dirs() -> None:
    """Remove every config root this process created. Never raises.

    Containment must never be the thing that fails a run, so a directory that
    cannot be removed is left behind under a known prefix rather than
    propagating an exception out of interpreter shutdown.
    """
    with _HOME_LOCK:
        paths, _HOME_DIRS[:] = list(_HOME_DIRS), []
    for path in paths:
        shutil.rmtree(path, ignore_errors=True)


def reset_home_dirs() -> None:
    """Drop this process's tracking list without removing anything (tests)."""
    with _HOME_LOCK:
        _HOME_DIRS[:] = []


class CopilotProvider(LLMProvider):
    """Provider for GitHub's Copilot CLI, driven BYOK against OpenRouter.

    ``copilot --output-format json --stream off --log-level none
    --no-custom-instructions --no-ask-user --no-auto-update
    --disable-builtin-mcps --model <model> [--effort <level>] -p <prompt>`` —
    flags first, the ``-p`` pair trailing.

    Declares a stdin transport and the ``:effort`` suffix, both measured; stays
    at ``usage_support = "none"``, also measured. See the module docstring.
    """

    #: §8.3: flags first, the ``-p <prompt>`` **pair** trailing. Confirmed legal
    #: at 1.0.80 — ``-p`` takes exactly one value and the flags are
    #: order-independent, so both prompt-first and prompt-last exit 0 and the
    #: grok-shape reorder changes no dispatched behaviour. Note the pair: the
    #: stdin transport drops ``-p`` **and** the prompt, not ``cmd[:-1]``.
    #:
    #: ``-1`` is *required* rather than preferred here, because
    #: ``test_last_element_assumption_holds_wherever_it_is_relied_on`` forces it
    #: on any adapter declaring a non-argv transport, which this one does.
    prompt_argv_index = -1

    #: Measured on the wire: the prompt travels as one argv element **or** on
    #: stdin with the ``-p`` pair omitted entirely. ``prompt_transport`` (the
    #: fan-out default) stays ``"argv"``, as it does for claude-code, codex,
    #: opencode and qwen-code, which declare the same pair.
    supported_prompt_transports = ("argv", "stdin")

    #: MEASURED, on the credentialed live lane, 2026-08-19 (run
    #: ``20260819T120345Z/live-copilot``, model ``openai/gpt-4.1-mini``): handed
    #: the shipped file block, the model called the ``create`` tool with exactly
    #: the right path and body, and the CLI refused it —
    #: ``tool.execution_complete`` came back ``success: false`` with
    #: ``{"message": "Permission denied and could not request permission from
    #: user", "code": "denied"}``, the turn ended "Refused due to permission
    #: denied error while writing the JSON file", and ``classify_failure``
    #: returned ``permission_denied``. No file.
    #:
    #: This is the §6.5 tier stated as data. The shipped argv deliberately
    #: carries no ``--allow-all-tools`` (and no ``--allow-tool``), which upstream
    #: documents as *required for non-interactive mode*; ``--no-ask-user`` is not
    #: a permission flag at all — it removes the ``ask_user`` tool — so under
    #: ``-p`` the write tool is advertised to the model, requested by it, and
    #: then has no channel on which approval could ever arrive. The declaration
    #: is therefore about OUR flag choice, not a copilot defect, and the fix is
    #: the prompt: asking for stdout is what stops the model spending its turn on
    #: an instruction the CLI will deny.
    #:
    #: WHY THE OLD "clean canary at all four §6.5 rungs" EVIDENCE DID NOT SETTLE
    #: THIS: that ladder ran against the offline stub, which never emits a tool
    #: call — ``"toolRequests":[]`` in 35 of 35 captures — so rung 4
    #: (``--allow-all-tools``, full permission) and rung 1 (none) produced
    #: byte-identical output. An experiment whose extremes agree is measuring the
    #: harness, not the tier.
    supports_file_output = False

    version_cmd = ("copilot", "--version")
    #: 1.0.80 is where the fixtures in ``tests/fixtures/copilot/`` were first
    #: captured and the floor this parser is known to handle; ``exit-zero-failure.jsonl``
    #: is still that release's bytes, because only 1.0.80 produces that shape.
    #: The JSONL schema is explicitly **unversioned** upstream (copilot-cli#3551),
    #: so this is a pin to re-confirm rather than a range to trust.
    #:
    #: A ``verify.pattern`` for this CLI must not anchor to end-of-output:
    #: ``copilot --version`` prints ``GitHub Copilot CLI 1.0.80.`` — trailing
    #: period included — **plus** a second "Run 'copilot update'…" line.
    min_version = "1.0.80"
    #: 2026-10-08: every other fixture re-captured on 1.0.93 offline, in the
    #: pinned image through the PATH wrapper (tests/fixtures/copilot/manifest.yaml).
    #: The parser needed no change. What moved: an empty provider 200 is now a
    #: `session.error` (`errorType: query`, "No response was returned…") with
    #: exit 1 (the `empty-response` row), two new ephemeral records
    #: (`model.call_finished`, `model.call_final_result`), no more
    #: `assistant.turn_retry`/`session.info` records on a retry, and shorter
    #: retry waits (5xx chain 17 s, 429 chain 57 s; still 6 requests each,
    #: `Retry-After` still honoured, a stall still unretried and untimed at
    #: 180 s), so `internal_retries` below holds as declared. One env change:
    #: COPILOT_PROVIDER_API_KEY_COMMAND (new since 1.0.80) is now stripped.
    verified_version = "1.0.93"

    #: Measured at 1.0.80, every field (§6.1.1). **All four of §3.1's
    #: placeholders were wrong and none of them shipped.**
    #:
    #: ``max_requests`` is **6** (1 + 5 retries), not 5 — confirmed twice over,
    #: from the stub's request log and independently from the CLI's own error
    #: text ("retried 5 times (total retry wait time: 85.66 seconds)").
    #:
    #: ``retries_rate_limit`` is **True**, not codex's ``False``: a 429-forever
    #: stub produced the same 6-request chain, so §7.5 rule 6(b) must suppress an
    #: identical harness-side rate-limit re-dispatch rather than repeating a
    #: chain that already ran at the same price for the same verdict.
    #:
    #: ``max_wall_s`` is ``None``, and that is the **honest** declaration rather
    #: than an unmeasured one — §3.1 pre-authorised it in those words. Two
    #: independent measurements refuse a bound: a stalled request is **never
    #: retried and has no client-side timeout at all** (one request, still open
    #: at 180 s), and a honoured ``Retry-After`` is a **server-chosen** sleep the
    #: CLI will not cap (a 60 s header produced ~61/71/68/66 s gaps and a chain
    #: past 300 s). The 5xx chain alone is 33 s and the rate-limit chain 86 s, so
    #: declaring either would describe one path out of three. ``base.py`` defines
    #: ``None`` as "no bound this adapter can state", and rule 4 then performs no
    #: admission test.
    #:
    #: ``configurable_by`` is empty because **no knob exists**: neither
    #: ``copilot help environment`` nor ``help config`` names a retry or
    #: request-timeout variable at 1.0.80.
    internal_retries = InternalRetryEnvelope(
        max_requests=6,
        max_wall_s=None,
        retries_rate_limit=True,
        configurable_by=(),
    )

    #: copilot's own authentication wording, added to the base set. The base
    #: patterns miss it entirely: the measured message is *"Authentication failed
    #: with provider at … (HTTP 401)"*, which contains none of "unauthorized",
    #: "not logged in" or "authentication required". Multi-word, so it stands
    #: alone without needing the bare-token context window.
    auth_error_patterns = LLMProvider.auth_error_patterns + (
        "authentication failed",
    )

    #: **Empty by measurement, not by omission** — and §6.1's column still reads
    #: YES for this CLI.
    #:
    #: copilot's one exit-0 failure shape is an empty provider 200 at 1.0.80
    #: (1.0.93 turns it into a ``session.error`` with exit 1): exit 0,
    #: ``result.exitCode: 0``, an ``assistant.message`` whose content is ``""``,
    #: and **no error record and no error text anywhere**. There is nothing for a
    #: regex to match, so the detection lives in :meth:`parse_output` as a
    #: structural check instead. Writing a marker against ``"content":""`` would
    #: pin this CLI's JSON key order into a classifier, and would false-positive
    #: on any legitimately empty field.
    #:
    #: The consequence is deliberate: such a run reaches the ladder as
    #: transport-shaped (``classify_failure`` returns ``None``) and takes the
    #: executor's bounded-retry path, which is the right treatment for an empty
    #: answer.
    exit_zero_failure_markers: Tuple[Any, ...] = ()

    @property
    def name(self) -> str:
        return "copilot"

    @property
    def default_timeout(self) -> int:
        # 1200 s, matching the providers.yaml block. It has to clear copilot's
        # own ~86 s internal rate-limit chain -- and, where a backend sends
        # `Retry-After`, an unbounded one -- before the harness's bound bites,
        # since the CLI exposes no knob to shorten either (see internal_retries).
        return 1200

    def is_available(self) -> bool:
        return shutil.which("copilot") is not None

    def build_command(
        self,
        prompt: str,
        model: str,
        *,
        timeout_s: Optional[int] = None,
        schema: Optional[StructuredSchema] = None,
    ) -> List[str]:
        """``copilot <flags> -p <prompt>`` — flags first, the prompt pair last.

        Args:
            prompt: The prompt text, rendered as the value of a trailing ``-p``.
            model: Passed to ``--model``, which is the whole model surface:
                measured, the flag **overrides** ``COPILOT_MODEL``, and an
                OpenRouter slug reaches the wire byte-exact (slash preserved), so
                no model env var is needed or set. An optional trailing
                ``:effort`` suffix is split off here and rendered as
                ``--effort``.
            timeout_s: Accepted and **ignored** — copilot exposes no wall-clock,
                turn or request-timeout flag at 1.0.80, so there is nothing to
                render. §1's guard is satisfied trivially: the argv is
                byte-identical with and without the keyword.
            schema: Accepted and ignored; copilot declares no structured-output
                support, so ``structured_output_support`` stays ``False`` and the
                caller never materializes a sidecar for it.
        """
        base_model, effort = split_reasoning_effort(model, REASONING_EFFORTS)
        cmd = [
            "copilot",
            "--output-format",
            "json",
            # Determinism, not a parsing requirement: the parser handles the
            # streamed shape too (the terminal assistant.message is emitted
            # either way), so this keeps one fixture shape rather than two.
            "--stream",
            "off",
            "--log-level",
            "none",
            # Reproducibility: without it, repo-level instructions are injected
            # into a review answer from files the fan-out never declared.
            "--no-custom-instructions",
            # A stalled interactive question burns the whole slot.
            "--no-ask-user",
            "--no-auto-update",
            # The GitHub MCP server is on by default in -p mode. We are a pure
            # ask; it is tokenless under the get_remove_env strip anyway, but
            # loading it is latency and surface for nothing.
            "--disable-builtin-mcps",
            "--model",
            base_model,
        ]
        if effort is not None:
            cmd += ["--effort", effort]
        # The §6.5 tier is expressed by what is ABSENT here: no --allow-all-tools,
        # no --allow-tool/--deny-tool, no --add-dir. Tier 1 was measured
        # sufficient with a clean canary; the help text's claim that
        # --allow-all-tools is "required for non-interactive mode" is false for a
        # prompt-in/answer-out run.
        cmd += ["-p", prompt]
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
        """Deliver the prompt on argv or on stdin.

        Under ``stdin`` the ``-p`` **pair** is dropped from argv entirely and the
        prompt is returned as the text to write to the child, so no part of it is
        measured against a command-line cap. Measured at 1.0.80: piped stdin with
        no ``-p`` at all carried a 30 414-byte prompt to the wire.

        Two shapes that look like stdin and are not, recorded because both fail
        quietly: ``-p -`` sends the literal one-character prompt ``-``, and a
        bare ``-`` exits 1.
        """
        if transport != "stdin":
            return super().build_command_for_transport(
                prompt, model, transport, prompt_file,
                timeout_s=timeout_s, schema=schema,
                sandbox_fallback=sandbox_fallback,
            )
        cmd = self.build_command(prompt, model, timeout_s=timeout_s, schema=schema)
        # Drop the trailing `-p <prompt>` PAIR, not just the prompt.
        return cmd[:-2], prompt

    def vendor_text(self, stdout: str, stderr: str) -> Tuple[str, str]:
        """The NDJSON stream minus the ``user.message`` record that echoes us.

        Measured on the committed captures: ``success.jsonl`` is 65 KB, of which
        **30 412 bytes are our own prompt**, carried in a non-ephemeral
        ``user.message`` record's ``data.content``. ``classify_failure`` read all
        of it, so a green copilot run classified ``rate_limited`` — the plan
        under review says "rate-limit patterns … declared per adapter" — and
        ``rate_limited`` is one of the two classes
        ``subagent_executor._classify_failed_run`` forwards to the retry ladder.
        Nothing pinned that until this defect was written up: copilot shipped
        with no manifest.

        The reduction is a line filter, so it removes and never rewrites: a
        record whose ``type`` is ``user.message`` is dropped, every other line is
        passed through byte-identically, including any non-JSON noise.
        ``session.error`` — the only channel copilot reports a failure on, and
        the one carrying the vendor's 401/429/404/context-length wording — is on
        the other side of the filter, as is every ``assistant.message``.

        **The cut-record case, which a whole-line parse cannot see.** A stream
        killed mid-flight ends in a partial line, and the echo is one record of
        61 751 bytes — by far the largest in the stream, so a random cut lands
        *inside* it more often than anywhere else. ``json.loads`` rejects that
        fragment, and passing it through would put the prompt bytes back in the
        haystack on exactly the failed-run path this hook exists for. So an
        unparseable line is dropped too, but **only** when it opens as this one
        record does — :data:`_CUT_USER_MESSAGE`, anchored at the line start and
        matching ``{"type": "user.message"`` in both the compact and the spaced
        spelling the committed captures use. Nothing else about a rejected line
        is inspected: a fragment of any other record, and any line that merely
        mentions the string later on, is still passed through, and a cut so
        early that the opener itself is incomplete carries no prompt bytes to
        expose. The rule is still removal-only, and a fragment is never parsed
        as evidence, so the degrade-to-input contract holds.
        ``truncated-mid-echo.jsonl`` is the committed capture of this shape;
        ``truncated.jsonl`` cuts at a record boundary and is unaffected.

        ``parse_output`` already applied the same type filter for the same
        reason (a ``user.message`` carries our prompt in the same
        ``data.content`` field an ``assistant.message`` uses); this is that rule
        reaching the classifier, which never had it.
        """
        try:
            if not stdout or "user.message" not in stdout:
                return stdout, stderr
            kept: List[str] = []
            dropped = False
            for line in stdout.split("\n"):
                stripped = line.strip()
                if stripped:
                    try:
                        record = json.loads(stripped)
                    except ValueError:
                        # A cut record. Drop it only if its opener names the
                        # echo; anything else a parse rejected is passed on.
                        if _CUT_USER_MESSAGE.match(stripped):
                            dropped = True
                            continue
                        record = None
                    if isinstance(record, dict) and record.get("type") == "user.message":
                        dropped = True
                        continue
                kept.append(line)
            if not dropped:
                return stdout, stderr
            return "\n".join(kept), stderr
        except (AttributeError, TypeError, ValueError):
            return stdout, stderr

    def parse_output(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """§3.4's two-step unwrap, keyed on record **type** rather than ephemerality.

        **Step 1** walks the JSONL and collects records by ``type``:

        * a ``session.error`` record is the run's verdict and is reported with
          the vendor's own message, so ``auth_error_patterns`` /
          ``rate_limit_patterns`` / the context-overflow markers all see the text
          they were measured against;
        * otherwise the answer is the **last** ``type == "assistant.message"``
          record's ``data.content``. Last-wins is what the ``multi-assistant``
          fixture pins, and the type filter is what stops ``user.message`` —
          non-ephemeral, and carrying our own prompt in the same ``data.content``
          field — from being served back as the model's answer.

        An assistant message with empty content is the **exit-0 failure** shape
        (see :attr:`exit_zero_failure_markers`) and is classified here, since no
        marker can reach it.

        **Step 2** runs :func:`extract_json_from_text` over that text with
        ``prefer_arrays=True``, which lifts the model's document out of the
        fenced block the captured answer really uses.

        Step 1's walk is :func:`_scan_copilot_records`, shared with
        :meth:`salvage_text`.
        """
        text = (stdout or "").strip()
        if not text:
            return {
                "success": False,
                "error": self._empty_stdout_reason(stderr),
                "raw": stdout,
                "data": None,
            }

        scan = _scan_copilot_records(text)
        assistant_contents = scan.assistant_contents
        session_error = scan.session_error
        saw_record = scan.saw_record

        if not saw_record:
            return {
                "success": False,
                "error": "copilot emitted no JSON records on stdout",
                "raw": stdout,
                "data": None,
            }

        if session_error is not None:
            message = session_error.get("message") or "copilot reported a session error"
            status = session_error.get("statusCode")
            kind = session_error.get("errorType")
            detail = f"{kind or 'error'}"
            if status is not None:
                detail = f"{detail} (HTTP {status})"
            return {
                "success": False,
                "error": f"{detail}: {message}",
                "raw": stdout,
                "data": None,
            }

        if not assistant_contents:
            return {
                "success": False,
                "error": (
                    "no assistant.message record in copilot output "
                    "(the run produced no answer)"
                ),
                "raw": stdout,
                "data": None,
            }

        answer = assistant_contents[-1]
        if not answer.strip():
            # THE exit-0 failure shape: exit 0, result.exitCode 0, no error
            # record, and an empty answer. Structural by necessity -- there is no
            # text here for a marker to match.
            return {
                "success": False,
                "error": (
                    "copilot returned an empty assistant message "
                    "(exit-0 failure: the provider answered 200 with no content)"
                ),
                "raw": stdout,
                "data": None,
            }

        return extract_json_from_text(answer, prefer_arrays=True)

    def salvage_text(self, stdout: str) -> Optional[str]:
        """The last assistant message's text, for the salvage gate (D4.1/D4.4).

        copilot's stdout is an envelope of typed records, and one of them is
        our own prompt: the non-ephemeral ``user.message`` echo, 30 412 bytes of
        plan text in ``success.jsonl``. Judged whole by
        ``has_salvageable_json``, that echo and the arrays in copilot's own
        bookkeeping records (``session.mcp_servers_loaded``,
        ``session.skills_loaded``, ``result``) passed the gate on 11 of the 12
        committed ``.jsonl`` captures, the 401 and the 429 among them, so a
        credential failure was sent to a JSON repair.

        The answer is the text :meth:`parse_output` reads: the **last**
        ``assistant.message``'s ``data.content`` (last-wins, as the
        ``multi-assistant`` row pins), or an unfinished streamed message's
        deltas when one came after it (:func:`_scan_copilot_records`). A
        ``session.error`` does not change the reading: the label is what the
        stream holds, not how the run ended.

        * ``None`` when no line is a copilot record — an empty stdout, or the
          ``-s`` bare-text shape, which is an answer and not a stream;
        * ``""`` when the stream holds no assistant message, or an empty one
          (the exit-0 failure) — a verdict, final;
        * otherwise that message's text.

        Never raises: a failed walk is ``""``, the reading the caller would give
        a raise anyway.
        """
        try:
            scan = _scan_copilot_records(stdout or "")
            if not scan.saw_envelope:
                return None
            return scan.last_message or ""
        except Exception:  # noqa: BLE001 - the hook must never raise
            return ""

    @staticmethod
    def _empty_stdout_reason(stderr: str) -> str:
        """Name the cause of a zero-byte stdout rather than restating the symptom.

        stderr is 0 bytes on every *model-path* failure — those arrive as
        ``session.error`` on stdout — so text here means an argument-parse error
        or a launch failure, which is exactly the case worth quoting.
        """
        raw = (stderr or "").strip()
        if raw:
            return f"copilot produced no output on stdout; stderr said: {raw[:300]}"
        return "Empty output from copilot (no JSON records on stdout)"

    def get_env(self, model: str) -> Dict[str, str]:
        """The complete B1 selector set, plus a per-slot config root.

        §2.2 rule 2 — **selection is total, never partial**. Every member is
        emitted together for every ``(model, profile)``, *including the base URL
        when the key is empty*, so a missing credential fails as a legible
        OpenRouter auth error rather than quietly resolving to the GitHub seat
        path. That fall-through is not hypothetical: ``COPILOT_PROVIDER_BASE_URL``
        is the documented activation switch for BYOK, so omitting it **is**
        selecting the other backend.

        ``COPILOT_OFFLINE=true`` is measured **not** to block the provider call
        (the vendor doc's "requires a local model provider" wording raised a real
        risk that it would). It disables GitHub auth, telemetry, web tools, the
        GitHub MCP server and auto-update, and leaves the provider endpoint
        reachable — so §7.4's belt-and-braces assertion can safely require it on
        the live lane.

        The token pair is resolved **for the model handed in** (see
        :func:`token_limits_for`), never as a process-wide constant and never for
        a different slug.

        Note what is **not** here: ``XDG_CACHE_HOME``. See the module docstring —
        a per-slot value would re-extract 209 MB on every spawn, and this adapter
        has no business hardcoding an absolute path that only the E2E image knows.
        Nothing here mutates ``os.environ``; this dict is the entire surface.
        """
        max_prompt, max_output = token_limits_for(
            split_reasoning_effort(model, REASONING_EFFORTS)[0]
        )
        env = {
            # The activation switch. Measured (§7 step 4): copilot appends
            # exactly `/chat/completions` to this VERBATIM and adds no version
            # segment of its own, so the `/v1` is load-bearing and the feared
            # `.../v1/v1/chat/completions` 404 cannot occur.
            "COPILOT_PROVIDER_BASE_URL": _BYOK_BASE_URL,
            "COPILOT_PROVIDER_TYPE": "openai",
            "COPILOT_PROVIDER_API_KEY": os.environ.get("OPENROUTER_API_KEY", ""),
            # Zero GitHub traffic, telemetry off -- and measured NOT to block the
            # BYOK provider call.
            "COPILOT_OFFLINE": "true",
            # The updater would otherwise move the binary underneath a pinned
            # parser whose schema upstream does not version.
            "COPILOT_AUTO_UPDATE": "false",
            "COPILOT_PROVIDER_MAX_PROMPT_TOKENS": str(max_prompt),
            "COPILOT_PROVIDER_MAX_OUTPUT_TOKENS": str(max_output),
        }
        home = self._home_dir_for_spawn()
        if home is not None:
            env["COPILOT_HOME"] = home
        return env

    def _home_dir_for_spawn(self) -> Optional[str]:
        """A fresh config root for this spawn, or ``None`` to leave it alone.

        Per **slot**, so two concurrent fan-out slots never share one writable
        config root — the corruption ``cursor-agent`` actually hit and the
        assertion §8.2's test 2 makes.

        ``None`` when the user pinned ``COPILOT_HOME`` themselves — their
        directory is respected and never removed — or when a temp directory
        cannot be created, because refusing a slot over a containment mechanism
        would be a worse trade than running without it.
        """
        if os.environ.get("COPILOT_HOME"):
            return None
        with _HOME_LOCK:
            try:
                return _create_home_dir()
            except OSError:  # noqa: BLE001 - containment must never fail a run
                return None

    def get_remove_env(self) -> List[str]:
        """Strip the seat path, the tier-widening switch and the key that outranks ours.

        §2.2 rule 3: adapter wins, ambient loses, no fallback. Three of these are
        §3.1 misses and each one is a different failure:

        * ``COPILOT_ALLOW_ALL`` silently promotes the run to tier 4 with no argv
          change, which would make §6.5's recorded tier unenforceable;
        * ``COPILOT_PROVIDER_BEARER_TOKEN`` is documented to outrank the API key
          this adapter injects;
        * ``OTEL_EXPORTER_OTLP_ENDPOINT`` turns telemetry on from a variable the
          user exported for something else entirely.

        Note the division of labour the strip does **not** cover: it removes
        stale values, while the *injection* in :meth:`get_env` selects the
        endpoint. Neither substitutes for the other.
        """
        return list(_STRIPPED_VENDOR_VARS)
