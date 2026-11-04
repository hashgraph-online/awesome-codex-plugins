"""Pi coding agent CLI provider implementation."""
import json
import re
import shutil
from typing import Any, Dict, List, Optional, Tuple

from ..json_extractor import extract_json_from_text
from .base import (
    CATEGORY_SERVER_ERROR,
    STATUS_AUTH_FAILED,
    STATUS_CONTEXT_LENGTH_EXCEEDED,
    STATUS_RATE_LIMITED,
    STATUS_TIMEOUT,
    USAGE_FULL,
    InternalRetryEnvelope,
    LLMProvider,
    ReasoningLadder,
    StructuredSchema,
    classify_streams,
    split_reasoning_effort,
    warn_gate_once,
)
from .pi_family_stream import (  # noqa: F401 - _MAX_DIAGNOSIS_CHARS re-exported
    _MAX_DIAGNOSIS_CHARS,
    StreamDialect,
    _answer_text,
    _assistant_ends,
    _cap,
    _events,
    _first_line,
    _one_line,
    _result_text,
    _retry_give_up,
    _stream_version,
    _tool_ends,
    _unclosed_container,
    assistant_text_of_stream,
    has_stream_envelope,
    shape_fault,
    sum_usage,
    unrecognized_stop_reason,
    warn_stream_version,
)

# Terminal codes, imported by name from the runner as omp.py does: a parse that
# sets one tells `invoke_with_file_output` whether a findings file beside a
# failed parse may still be recovered.
try:  # pragma: no cover - import shim mirrors the rest of utils/
    from ..llm_client import ERROR_SUBPROCESS_FAILED, ERROR_TIMEOUT
except ImportError:  # pragma: no cover - direct-script import shim
    ERROR_SUBPROCESS_FAILED = "SUBPROCESS_FAILED"
    ERROR_TIMEOUT = "TIMEOUT"

# Thinking levels accepted by `pi --thinking` (per pi.dev docs). pi also
# parses the same levels as a native ":level" suffix on --model; the adapter
# strips the suffix itself so only --thinking carries it.
#
# Seven levels, and they are the seven rungs with `off` in `none`'s place: pi
# spells the bottom rung `off` and takes no `none` at all, so `off` is declared
# as a spelling and the ladder renders canonical `none` as `off` here.
EFFORT_LADDER = ReasoningLadder(
    provider="pi",
    rungs=("minimal", "low", "medium", "high", "xhigh", "max"),
    spellings=(("off", "none"),),
)
REASONING_EFFORTS = EFFORT_LADDER.accepted

#: The bare HTTP-status prefix pi puts ahead of the vendor's JSON error object
#: (``401: {"message": …}``). At 0.80.6 that line was stderr; under ``--mode
#: json`` (0.87.1) the same string is the terminal assistant message's
#: ``errorMessage``. It is the **only** place the status survives — pi's
#: ``AssistantMessage`` has no ``errorStatus`` field, and the JSON payload carries
#: `type` and `code` but never the number — so the prefix is stripped to reach
#: the JSON and then put back in the message.
_STATUS_PREFIX = re.compile(r"^(\d{3})\s*:\s*")

#: The ``session.version`` the json-mode parser was written against (pi 0.87.1,
#: the same value as omp's). A different value is WARNed once, never refused.
PI_STREAM_VERSION = 3

#: pi's closed ``stopReason`` set, as far as this parser handles it. pi's
#: ``docs/message-types.md`` lists ``pending`` (streaming only, never on a
#: ``message_end``) and ``deferred`` too; both fail closed, naming the enum.
#: ``length`` is pi's and not omp's: a max-output cut.
_KNOWN_STOP_REASONS = ("stop", "length", "toolUse", "error", "aborted")

#: pi's words for the shared pi-family reader. pi ends a compaction with
#: ``compaction_end`` and its successful ``result.usage`` is a paid
#: summarization call no assistant ``message_end`` carries, so the usage leg is
#: **on** (measured: ``tests/fixtures/pi/context-overflow-compacted``).
PI_DIALECT = StreamDialect(
    product="pi",
    verified_version="1.1.0",
    stream_version=PI_STREAM_VERSION,
    stop_reasons=_KNOWN_STOP_REASONS,
    compaction_event="compaction_end",
    compaction_usage=True,
)

#: The sentence pi 0.87.1 ends a failed truncated-response recovery with
#: (``agent-session.js``). It rides a ``compaction_end`` whose ``reason`` is
#: ``overflow`` — the same reason a real context overflow carries — so the text,
#: not the reason, is what separates a cut answer from an overflow (§7.3 step 5).
_TRUNCATED_RECOVERY = "truncated response recovery failed"

#: The sentence pi ends a failed context-overflow compact-and-retry with ("Context
#: overflow recovery failed after one compact-and-retry attempt"). UNMEASURED:
#: §7.3 step 5 names the shape (compaction succeeds — ``result`` present,
#: ``aborted: false`` — and the retried turn fails again); no live capture has
#: produced it yet. The sentence need not embed the vendor's 400 text, so it is
#: a positive overflow signal of its own on the terminal ``errorMessage``.
_OVERFLOW_RECOVERY = "context overflow recovery failed"

#: The tool allow-list every ``generate`` dispatch pins with ``--tools`` (plan:
#: review-run-scope-salvage-and-failure-visibility D3.1, decision 11.6).
#:
#: * **What it replaces.** With no ``--tools``, pi 0.87.1 activates ``read,
#:   bash, edit, write`` (``core/sdk.js:140-145``) — unless the user's settings,
#:   a trusted project's ``.pi/settings.json`` or an installed extension change
#:   that, so the reviewer's toolset used to be whatever the host happened to
#:   configure. This list is that default minus ``edit`` (``write`` covers the
#:   one legitimate write, the output file) plus omp's search tools: ``grep``,
#:   and ``find``, pi's name for omp's ``glob``. ``ls`` is left out because
#:   ``read`` and ``find`` cover it. ``bash`` stays because the code-review
#:   prompt runs ``git diff``, so this is **not** a read-only mode
#:   (``read_only_modes.pi`` stays ``null``).
#: * **The accepted form is ONE comma-separated value.** ``cli/args.js:110-115``
#:   splits the value on ``,``, trims each name and drops empty ones; ``pi
#:   --help`` says "Comma-separated allowlist of tool names to enable". A second
#:   ``--tools``/``-t`` *replaces* the first value rather than adding to it, and a
#:   space-separated value is one name. Hence one flag and one
#:   ``",".join(PI_TOOLS)``, never a flag per tool.
#: * **Unknown names are dropped silently** (``cli/args.js:110-115``,
#:   ``core/agent-session.js:2496``, probed offline). A misspelled name removes
#:   that tool with no error, and a wrong separator removes every tool: ``read
#:   bash write`` is one unknown name, and pi would review with no ``read`` at
#:   all. That is why the names live here once, pinned by tests to pi's
#:   built-in vocabulary (``read, bash, edit, write, grep, find, ls``), and why
#:   ``cli-surface.yaml`` pins the help's "Comma-separated" wording.
#: * **It pins names, not implementations.** ``_refreshToolRegistry``
#:   (``core/agent-session.js:2491-2567``) puts built-ins and extension tools
#:   through the same name check, then lays each surviving extension tool over
#:   the built-in of the same name. A user or trusted-project extension that
#:   registers ``bash``, ``read`` or ``write`` therefore replaces the built-in
#:   under this list too, and extension ``tool_call``/``tool_result`` handlers
#:   (``:245-267``) see every call whatever the list says. Isolating extensions
#:   is deliberately deferred (decision 11.8).
#: * **``grep`` and ``find`` may download a binary.** They call
#:   ``ensureTool("rg")`` / ``ensureTool("fd")``, which fetch the tool the first
#:   time it is missing. Accepted (decision 11.6), on the condition that a failed
#:   download does not fail the run — MEASURED 2026-09-28 in the pinned image
#:   (``--network none``, no ``rg``/``fd`` on PATH, one scripted ``grep`` call):
#:   the tool returned ``isError: true`` with "ripgrep (rg) is not available and
#:   could not be downloaded", the model's next turn ended ``stopReason: stop``
#:   and pi exited 0. A tool error the model can work around, so both names stay.
PI_TOOLS = ("read", "grep", "find", "bash", "write")

#: The flag that carries :data:`PI_TOOLS`, gated per flag like claude-code's
#: optional flags: a pi whose help does not document it gets today's argv.
PI_TOOLS_FLAG = "--tools"

#: pi's built-in MCP client, switched off for the run. pi 1.1.0 changed what
#: :data:`PI_TOOLS_FLAG` bounds: "``--tools`` now keeps MCP tools unless an
#: entry starts with ``mcp__``" (its CHANGELOG and ``pi --help``), and pi
#: connects every server in ``~/.pi/agent/mcp.json`` (and a trusted project's
#: ``.pi/mcp.json``) at start-up. So under the allow-list above a reviewer still
#: got every MCP tool the user configured for their own sessions — tools this
#: list never names, launched as processes the run never asked for.
#: ``--no-mcp`` ("no servers connect and no MCP tools", 1.1.0's help) restores
#: what the list claims, the way codex runs with ``-c features.plugins=false``
#: and copilot with ``--disable-builtin-mcps``. Gated on the installed help like
#: ``--tools``: a pi that does not document it has no built-in MCP client to
#: turn off, so it gets today's argv with no warning.
PI_NO_MCP_FLAG = "--no-mcp"


def parse_answer_text(text: str) -> Dict[str, Any]:
    """The answer-channel reader: a bare model answer in, a result dict out.

    Direct ``json.loads`` when the text starts with ``[`` or ``{``, else the
    shared extractor over code blocks and JSON embedded in prose, arrays
    preferred.

    Module-level because it has **two** callers: :class:`PiProvider` (on the
    terminal assistant message's text under ``--mode json``, and on a bare
    text-mode stdout on the back-compat leg) and
    :class:`~utils.providers.omp.OmpProvider`, which reaches the same text by the
    same road. Everything else about the two adapters' products — argv, env,
    tool policy, transports — diverges, which is why omp does not subclass pi;
    the stream reader they now share lives in ``pi_family_stream``.
    """
    text = (text or "").strip()

    if not text:
        return {"success": False, "error": "Empty output", "raw": text, "data": None}

    if text.startswith(('[', '{')):
        try:
            return {"success": True, "data": json.loads(text)}
        except json.JSONDecodeError:
            pass

    return extract_json_from_text(text, prefer_arrays=True)


# --------------------------------------------------------------------------- #
# The json-mode stream, read through the shared pi-family reader under
# `PI_DIALECT`. What follows is only what pi has and omp does not: the status
# lives in the `errorMessage` prefix, `length` is a stop reason, and an overflow
# can end in a failed `compaction_end`.
# --------------------------------------------------------------------------- #

def _vendor_json_line(text: str) -> Optional[str]:
    """``"NNN: message (code)"`` from a ``NNN: {vendor json}`` line, or ``None``."""
    match = _STATUS_PREFIX.match(text)
    if not match:
        return None
    try:
        payload = json.loads(text[match.end():])
    except ValueError:
        return None
    if not isinstance(payload, dict):
        return None
    message = payload.get("message")
    if not (isinstance(message, str) and message.strip()):
        return None
    line = f"{match.group(1)}: {_one_line(message)}"
    code = payload.get("code")
    if isinstance(code, str) and code.strip():
        line = f"{line} ({code.strip()})"
    return line


def _error_status(message: Dict[str, Any]) -> Optional[int]:
    """The HTTP status in a terminal message's ``errorMessage`` prefix, if any."""
    match = _STATUS_PREFIX.match(_one_line(str(message.get("errorMessage") or "")))
    return int(match.group(1)) if match else None


def _error_sentence(message: Dict[str, Any]) -> str:
    """An ``error``/``aborted`` message's ``errorMessage`` through the vendor-JSON tier.

    The same reduction :meth:`PiProvider._diagnose` applies to a 0.80.6 stderr
    line, because it is the same string: ``401: {…}`` becomes *401: Incorrect API
    key provided: … (invalid_api_key)*, and a non-JSON sentence (``Connection
    error.``, ``Stream ended without finish_reason``) is reported verbatim.
    """
    detail = _one_line(str(message.get("errorMessage") or ""))
    return _cap(_vendor_json_line(detail) or detail)


def _overflow_failure(events: List[Dict[str, Any]]) -> Optional[str]:
    """The last failed overflow ``compaction_end``'s sentence, or ``None``.

    A compaction that failed carries ``errorMessage`` (or ``aborted: true``) and
    no ``result``; a successful one carries ``result`` and neither. Only
    ``reason: "overflow"`` counts: a threshold compaction failing is not a
    failure of the run.
    """
    for event in reversed(events):
        if event.get("type") != PI_DIALECT.compaction_event:
            continue
        if event.get("reason") != "overflow":
            continue
        detail = _one_line(str(event.get("errorMessage") or ""))
        if detail:
            return _cap(detail)
        if event.get("aborted"):
            return "overflow compaction aborted"
        return None
    return None


def _is_overflow(final: Dict[str, Any], events: List[Dict[str, Any]]) -> bool:
    """True for a real context overflow — never for a truncated-response recovery.

    Either the terminal ``error``'s own ``errorMessage`` carries a shared
    :data:`~utils.providers.base.CONTEXT_OVERFLOW_MARKERS` row (measured: the
    vendor's ``400: … maximum context length …`` arrives verbatim), or the stream
    holds a failed overflow ``compaction_end`` whose sentence is **not** pi's
    truncated-recovery one (§7.3 step 5's pre-flight correction: both share
    ``reason: "overflow"``), or the terminal ``errorMessage`` is pi's own
    overflow-recovery-failed sentence (:data:`_OVERFLOW_RECOVERY`) — the shape
    where the compaction itself succeeded and the retried turn overflowed again.
    """
    if final.get("stopReason") == "error":
        text = _one_line(str(final.get("errorMessage") or ""))
        if classify_streams(text, "") == STATUS_CONTEXT_LENGTH_EXCEEDED:
            return True
        if _OVERFLOW_RECOVERY in text.lower():
            return True
    failure = _overflow_failure(events)
    return bool(failure) and _TRUNCATED_RECOVERY not in failure.lower()


def _named_for_the_ladder(status: str, token: str, sentence: str) -> str:
    """``sentence``, with ``token`` in front when the shared tables would miss it.

    Lane A classifies the composed error *string* through ``classify_streams``
    with no adapter in hand, so a structural verdict reaches its ladder only if
    the sentence carries a table word. omp's helper of the same name checks for
    the token as a substring; this one asks the table itself, so a sentence that
    already classifies (the measured ``400: … maximum context length …``) is
    returned untouched.
    """
    if classify_streams(sentence, "") == status:
        return sentence
    return f"{token}: {sentence}" if sentence else token


def _never_started(events: List[Dict[str, Any]]) -> bool:
    """A pre-flight corpse: the ``session`` header and no run.

    MEASURED at 0.87.1 (``tests/fixtures/pi/preflight-no-key``): pi writes the
    header before it resolves the credential, then throws — exit 1, a 143-byte
    one-line stdout, and ``No API key found for stub.`` on stderr. That is omp's
    ``_never_started`` shape exactly, and it is silent for ``STDOUT_ELSE_STDERR``.
    """
    if not events:
        return False
    if any(str(event.get("type")) == "agent_start" for event in events):
        return False
    return not _assistant_ends(events)


def _tool_use_diagnostics(events: List[Dict[str, Any]]) -> Tuple[str, str]:
    """``(tool name, first line of its result)`` for a ``toolUse``-final stream.

    The last errored ``tool_execution_end``, else the last one. The result line
    is diagnostics only and must never be composed into a classifier-facing
    error string (see :func:`terminal_verdict`).
    """
    tools = _tool_ends(events)
    errored = [e for e in tools if e.get("isError")]
    tool = errored[-1] if errored else (tools[-1] if tools else None)
    detail = _first_line(_result_text(tool)) if tool else ""
    return str((tool or {}).get("toolName") or "?"), detail


def terminal_verdict(stdout: str) -> Optional[str]:
    """What pi's json **stream** says went wrong, or ``None``.

    One reader for :meth:`PiProvider.parse_output` and
    :meth:`PiProvider.describe_failure`, so the report's ``Reason:`` line and the
    log's error string cannot say different things about the same bytes. stderr
    is never read here; precedence is the caller's.

    ``None`` for a stdout that is not a pi stream, and for a ``stop`` that
    carries text (a success).
    """
    if not has_stream_envelope(stdout, PI_DIALECT):
        return None
    events, _junk = _events(stdout)
    version = _stream_version(events)
    messages = _assistant_ends(events)

    fault = shape_fault(messages, version, dialect=PI_DIALECT)
    if fault is not None:
        return fault

    if not messages:
        last = events[-1] if events else {}
        kind = str(last.get("type") or "?")
        message = last.get("message")
        if isinstance(message, dict) and message.get("role"):
            kind = f"{kind}/{message['role']}"
        return (
            f"run ended before any assistant message (last event: {kind}, "
            f"{len(events)} events)"
        )

    final = messages[-1]
    reason = final.get("stopReason")
    if reason == "stop":
        if _answer_text(final).strip():
            return None
        return _retry_give_up(events)
    if reason == "length":
        answer = _answer_text(final)
        return (
            f"Truncated output (stopReason length: the model hit its output "
            f"limit after {len(answer)} characters)"
        )
    if reason == "error":
        sentence = _error_sentence(final) or "pi reported stopReason 'error'"
        if _is_overflow(final, events):
            failure = _overflow_failure(events)
            if failure and failure not in sentence:
                sentence = f"{sentence}; {failure}"
            return _named_for_the_ladder(
                STATUS_CONTEXT_LENGTH_EXCEEDED, "Context length exceeded", sentence
            )
        status = _error_status(final)
        if status is not None and 500 <= status < 600:
            return _named_for_the_ladder(CATEGORY_SERVER_ERROR, "Server error", sentence)
        return sentence
    if reason == "aborted":
        sentence = _error_sentence(final) or "pi reported stopReason 'aborted'"
        return _named_for_the_ladder(STATUS_TIMEOUT, "Deadline exceeded", sentence)
    if reason == "toolUse":
        # The tool's *name* only. Its result is content the run read (a file, a
        # command's output), never pi's verdict, and Lane A classifies this
        # sentence through the shared tables: a read that quoted "rate limit
        # exceeded" or "invalid api key" would turn this deadline into
        # rate_limited/auth_failed. The result text travels separately, as
        # parse_output's diagnostic `tool_result` field (_tool_use_diagnostics).
        name, _detail = _tool_use_diagnostics(events)
        return _named_for_the_ladder(
            STATUS_TIMEOUT,
            "Deadline exceeded",
            f"run ended inside a tool call: {name}",
        )
    return unrecognized_stop_reason(final, version, PI_DIALECT)


class PiProvider(LLMProvider):
    """Provider for the Pi coding agent CLI (https://pi.dev).

    ``pi --no-session -p --mode json`` runs one-shot headless and writes a JSONL
    event stream to stdout — omp's event family (``session`` header,
    ``message_start``/``message_update``/``message_end``, ``tool_execution_*``,
    ``auto_retry_*``, ``compaction_*``, ``agent_end``, ``agent_settled``) — read
    by the shared reader in ``pi_family_stream`` under :data:`PI_DIALECT`. The
    answer is the text of the **last assistant ``message_end``**; usage is summed
    over every assistant ``message_end`` plus each successful
    ``compaction_end.result.usage`` (:meth:`parse_usage`).

    **The channel model, measured at 0.87.1** (``tests/fixtures/pi/``, 2026-09-25,
    in the container, ``--network none``, no credential):

    * **Every in-stream failure exits 0.** pi sets a non-zero exit only in text
      mode; under ``--mode json`` a 401, a 429, a 5xx, a 404, a cut stream and a
      400 context-length all end in an assistant ``message_end`` with
      ``stopReason: "error"`` and the vendor's own words in ``errorMessage``
      (``401: {…json…}``, the same string 0.80.6 printed to stderr), with stderr
      **empty**. Success is therefore structural (:meth:`parse_output`), never
      the exit code.
    * **A thrown pre-flight exits 1** with a one-line stdout (the ``session``
      header, written before the throw) and the diagnosis on stderr — ``No API
      key found for stub.`` measured. That is omp's ``_never_started`` shape.
    * **The 400 context-length is no longer silent.** At 0.80.6 it wrote nothing
      on either channel; at 0.87.1 it is an ``error`` whose ``errorMessage`` is
      the vendor's ``maximum context length`` sentence, classified
      ``context_length_exceeded``. With nothing compactable (a one-message
      conversation) pi does not compact; with history it compacts (a paid
      summarization call), retries once, and says "Context overflow recovery
      failed …" if that fails too.
    * **The stream echoes our prompt** (user ``message_start``/``message_end``,
      ``agent_end.messages``), carries pi's whole system prompt twice and every
      tool result, which is why :meth:`vendor_text` reduces it.

    **Back-compat.** A non-empty stdout with no pi stream envelope (a pi that
    ignored ``--mode``) is read as today's bare answer, with one WARN.

    Model names are pi model patterns passed VERBATIM to --model — pi
    resolves "provider/id" forms itself (e.g. "openrouter/z-ai/glm-5.2",
    "anthropic/claude-opus-4-8") — no partition/splitting. Auth is pi's own:
    provider API-key env vars (e.g. OPENROUTER_API_KEY, ANTHROPIC_API_KEY)
    inherited by the subprocess, or keys stored via pi's /login
    (~/.pi/agent/auth.json).

    Model strings support an optional ``model[:effort]`` suffix (e.g.
    ``openrouter/z-ai/glm-5.2:high``), translated to ``--thinking <effort>``.
    Valid efforts are listed in REASONING_EFFORTS; anything else passes
    through verbatim as the model name (keeping ``:free``-style ids — and
    bedrock ``...-v1:0`` version suffixes — intact). Stripping the suffix
    before --model also keeps pi's own native ":level" parsing out of the
    picture, so the whitelist here is the single source of truth.

    **Tools: a pinned allow-list, and NOT a read-only mode.** pi has no
    permission prompts and no sandbox: whatever tools are active run with the
    pi process's own permissions, which is how the headless file reads and the
    output-file write the review prompts rely on work unattended. Every
    ``generate`` dispatch pins those tools with ``--tools
    read,grep,find,bash,write`` (:data:`PI_TOOLS`, gated on the installed help
    documenting the flag), so which tool *names* are active no longer depends on
    the user's settings, a trusted project's ``.pi/settings.json`` or pi's own
    default (``read, bash, edit, write``). Since pi 1.1.0 that list no longer
    bounds MCP tools, so ``--no-mcp`` (:data:`PI_NO_MCP_FLAG`, gated the same
    way) keeps the servers in the user's ``~/.pi/agent/mcp.json`` from
    connecting. Three things it does not do:

    * **It is not read-only.** ``bash`` stays, because the code-review prompt
      runs ``git diff``; a model can still run any command, so
      ``read_only_modes.pi.mechanism`` stays ``null``.
    * **It pins names, not implementations.** A user or trusted-project
      extension that registers ``bash``, ``read`` or ``write`` replaces the
      built-in of that name under the allow-list too, and extension
      ``tool_call``/``tool_result`` handlers see every call whatever the list
      says (``core/agent-session.js:2491-2567``, ``:245-267``). Isolating
      extensions is a later plan (decision 11.8).
    * **It does not bound time.** pi has no ``--max-time`` and no setting caps
      the bash tool's ``timeout`` parameter ("no default timeout",
      ``core/tools/bash.js:28``).

    **The orphan risk a killed slot carries.** pi's bash tool spawns its shell
    ``detached: true`` (``core/tools/bash.js:52``): the shell gets a session and
    process group of its own, so a signal to pi, or to pi's group, never reaches
    it. pi reaps its tracked shells only on SIGTERM or SIGHUP (print and json
    mode call ``killTrackedDetachedChildren()``, ``modes/print-mode.js:31-45``,
    which SIGKILLs each shell's *group*, ``utils/shell.js:168-203``); a SIGKILL
    runs no handler. And a ``timeout``-wrapped command escapes even that
    cleanup: GNU ``timeout`` moves itself into a group of its own inside the
    shell's session. The incident this records was a review killed at its 1200 s
    slot while pi's last ``bash`` call was ``timeout 1700 python -m pytest …``,
    which could then run on for up to 1700 s, writing into the same ``plans/``
    tree. The fix is not here: ``llm_client``'s Lane A spawn snapshots a
    timed-out (or interrupted, or aborted) CLI's descendants before it signals
    anything, SIGTERMs the CLI first so pi's own handler runs, and then sweeps
    every snapshotted process group (``process_control.terminate_timed_out``).

    **Confirmed against pi 0.87.1 itself** (2026-09-28, the pinned image,
    ``--network none``, zero spend: the rig's stub scripted one chat ``bash``
    call, ``timeout 120 sleep 120 | cat``, and the process table was read from
    procfs after each stop, the image having no ``ps``). pi runs it as
    ``bash -c …`` leading its own session and group; ``cat`` shares the
    shell's group; ``timeout`` leads a group of its own in the shell's session,
    with ``sleep`` in it. After a SIGKILL of pi alone — what
    ``subprocess.run(timeout=…)`` used to send — all four survived, reparented
    to init. After a SIGTERM of pi alone, pi exited 143 having reaped the shell
    and ``cat``, and ``timeout`` and ``sleep`` survived. Through the Lane A spawn
    with the sweep, nothing survived and the log read ``pi timed out after 8s;
    cli terminated; process groups: 74 gone, 75 killed`` — the shell's group
    already reaped by pi's own SIGTERM handler, ``timeout``'s by the sweep.
    """

    version_cmd = ("pi", "--version")
    #: 1.1.0 is where the json-mode fixture set in ``tests/fixtures/pi/`` was
    #: last captured (the container pin, ``tests/container/cli-versions.lock``;
    #: first captured on 0.87.1), and it is the version :data:`PI_DIALECT` names
    #: in every shape error. It is not 0.80.6: no json-mode byte was captured there (that text-mode set is
    #: kept, ungraded, in ``tests/fixtures/pi/text-mode-0.80.6/``).
    #:
    #: **There is deliberately no ``min_version``.** A measured-at version is an
    #: upper bound on the true floor, never the floor
    #: (`harness-invocation-improvements.md` §5.4.1(a)). json mode with the
    #: ``session`` header dates from 0.45.0, and a pi that ignores ``--mode``
    #: (every release before 0.87.1 silently ignored an invalid one) is read by
    #: :meth:`parse_output`'s back-compat leg rather than refused.
    #: ``min_version`` is a hard exit-3 refusal in
    #: ``subagent_executor._detect_version``; ``verified_version`` is a one-line
    #: warning, and only the warning is earned.
    #:
    #: ``version_cmd`` stays, because it is the only thing that can ever make
    #: ``verified_version`` speak. Confirmed against the pinned binary 2026-09-25
    #: (``docker run --rm --network none --entrypoint /opt/mllm/real/pi
    #: mllm-e2e:local --version``): pi prints a bare ``0.87.1`` on stdout, which
    #: the base :meth:`parse_version` reads without an override (1.1.0 prints a
    #: bare ``1.1.0`` the same way).
    #:
    #: **Moved 0.87.1 -> 1.1.0 on 2026-10-08**: every captured row of
    #: ``tests/fixtures/pi/`` was re-captured on 1.1.0 by the same rig, now under
    #: the shipped ``--tools`` argv. Every row's class, exit code and request
    #: count held but ``truncated``'s: the 60-byte cut is one request ending
    #: ``Error reading response: malformed server-sent event JSON.`` (four
    #: ending "Stream ended without finish_reason" at 0.87.1), still classified
    #: as nothing. The stream gained ``durationMs``/``thinkingLevel`` on
    #: assistant messages and lost ``responseId`` on the assistant
    #: ``message_start``, none of which the parser reads; no parser change.
    verified_version = "1.1.0"

    #: USAGE_FULL: ``--mode json`` carries omp's usage shape on every assistant
    #: ``message_end`` (probe: ``tests/fixtures/pi/json-mode/``; recaptured in
    #: the fixture set), summed by :meth:`parse_usage`.
    usage_support = USAGE_FULL

    #: MEASURED TRUE: the 2026-09-25 ``review-code`` slot's own stream ended
    #: inside a ``bash`` tool call running ``timeout 1700 python -m pytest
    #: tests …`` (plan: review-run-scope-salvage-and-failure-visibility §3.1).
    #: pi has no permission prompt, and ``bash`` stays in :data:`PI_TOOLS` (the
    #: ``--tools`` allow-list, D3.1), so the shell is still there under the
    #: pinned argv; ``tests/test_provider_housekeeping.py``'s ``SHELL_EVIDENCE``
    #: row reads ``bash`` out of the rendered ``--tools`` value.
    runs_shell_in_generate = True

    #: pi's own retry chain (decision 12.7). MEASURED at 0.87.1 and again at
    #: 1.1.0 (``tests/fixtures/pi/manifest.yaml``: ``rate-limit``,
    #: ``server-error``, ``error-envelope``, ``zero-body``; ``truncated`` too at
    #: 0.87.1): **4 requests over ~14.4 s**, three ``auto_retry_start`` events
    #: at 2/4/8 s and one ``auto_retry_end{success: false}``. 401 and 404 are
    #: one request, and a context overflow goes to compaction instead of the
    #: retry chain. At 1.1.0 a stream cut inside its first ``data:`` frame is
    #: one request too: the SDK's ``malformed server-sent event JSON`` matches
    #: none of pi's retry words.
    #:
    #: * ``max_requests=4`` is 1 + ``retry.maxRetries`` (default 3) **per failing
    #:   model call** — the counter resets on every non-error assistant message
    #:   (``agent-session.js:606-615``), the per-call convention omp.py uses too.
    #:   Provider-level retries default to 0 and multiply the chain only when
    #:   ``retry.provider.maxRetries`` is set; each summarization call a
    #:   compaction makes has its own 4-request budget.
    #: * ``retries_rate_limit=True``: pi's retry test is a regex over
    #:   ``errorMessage`` (``429|rate.?limit|too many requests``, 5xx, connection
    #:   errors, ``ended without``) unless a quota/billing word matches first —
    #:   and the ``rate-limit`` row is 4 requests of 429.
    #: * ``max_wall_s=None``: no outer bound (sleeps cap at ``maxAgentDelayMs``
    #:   60 s, each request only at ``httpIdleTimeoutMs`` 300 s).
    #: * ``configurable_by``: ``retry.maxRetries`` and ``retry.provider.maxRetries``
    #:   in ``<PI_CODING_AGENT_DIR>/settings.json`` **and** a trusted project's
    #:   ``<cwd>/.pi/settings.json`` — so a reviewed repo's ``.pi/settings.json``
    #:   can change pi's retry count. That is not a new exposure: the same file
    #:   can change anything else pi reads. No CLI flag or env var controls them.
    internal_retries = InternalRetryEnvelope(
        max_requests=4,
        max_wall_s=None,
        retries_rate_limit=True,
        configurable_by=("retry.maxRetries", "retry.provider.maxRetries"),
    )

    #: pi's two pre-flight credential sentences. ``No API key found for`` is
    #: MEASURED (``preflight-no-key``: the model registry's refusal, stderr, exit
    #: 1); ``No API key for`` is the session's own throw
    #: (``agent-session.js:1647``, read, not captured). omp's precedent is the
    #: first of the two (``omp.py``'s ``auth_error_patterns``).
    auth_error_patterns = LLMProvider.auth_error_patterns + (
        "No API key found for",
        "No API key for",
    )

    @property
    def name(self) -> str:
        return "pi"

    @property
    def default_timeout(self) -> int:
        return 600

    def is_available(self) -> bool:
        return shutil.which("pi") is not None

    def build_command(
        self,
        prompt: str,
        model: str,
        *,
        timeout_s: Optional[int] = None,
        schema: Optional[StructuredSchema] = None,
    ) -> List[str]:
        # pi --no-session -p --mode json [--tools <PI_TOOLS>] [--no-mcp]
        #    [--thinking <effort>] --model <model> "<prompt>"
        # -p prints and exits; `--mode json` right after it (omp's order) makes
        # stdout the JSONL event stream parse_output reads. The prompt goes last
        # as a bare positional (adding `--` is a separate change: `@file`
        # expansion is a real pi feature).
        base_model, effort = split_reasoning_effort(model, REASONING_EFFORTS)
        cmd = ["pi", "--no-session", "-p", "--mode", "json"]
        # ONE `--tools`, ONE comma-joined value: pi splits the value on `,` and
        # a repeated flag replaces it (see PI_TOOLS). Optional-flag posture: a
        # pi whose own help does not document it (or whose help cannot be read)
        # gets today's argv byte for byte, plus one WARN naming what it lost.
        if self.supports_flag(PI_TOOLS_FLAG):
            cmd += [PI_TOOLS_FLAG, ",".join(PI_TOOLS)]
        else:
            warn_gate_once(
                ("pi", PI_TOOLS_FLAG),
                f"[WARN] pi: {PI_TOOLS_FLAG} is not documented by the installed "
                f"CLI's own help (verified at {self.verified_version}); the "
                f"tool allow-list ({','.join(PI_TOOLS)}) is not passed, so pi "
                f"runs with whatever toolset its own defaults, settings and "
                f"extensions enable. Everything else is unchanged.",
            )
        if self.supports_flag(PI_NO_MCP_FLAG):
            cmd.append(PI_NO_MCP_FLAG)
        if effort is not None:
            cmd += ["--thinking", effort]
        cmd += ["--model", base_model, prompt]
        return cmd

    #: The two tiers :meth:`_diagnose` can answer from, in precedence order.
    #: Named so a test can grade WHICH rung produced an answer rather than only
    #: the text. They apply to a stderr line and, under ``--mode json``, to the
    #: terminal message's ``errorMessage`` — the same string.
    TIER_VENDOR_JSON = "vendor-json"
    TIER_VERBATIM = "verbatim"
    #: A json-mode verdict read off the stream's *structure* rather than out of
    #: a vendor sentence: a ``length`` cut, a ``toolUse``-final deadline, a
    #: shape fault, a stream with no assistant message.
    TIER_STREAM = "stream"

    def _diagnose(self, stdout: str, stderr: str) -> Optional[Tuple[str, str]]:
        """``(tier, one-line message)`` for pi's **stderr**, or ``None``.

        ``stdout`` is accepted and deliberately unread: under ``--mode json`` the
        stream's own verdict is :func:`terminal_verdict`'s, and what reaches
        stderr is a pre-flight throw (``No API key found for stub.``).

        Within stderr: strip the bare ``NNN: `` status prefix, parse the
        remainder as the vendor's JSON error object, and report its ``message``
        with its ``code`` and the stripped status. If the remainder does not
        parse, the stderr text is reported verbatim. Both channels empty is
        ``None``: nothing is invented from an exit code.
        """
        # The first paragraph only: pi's pre-flight throw appends its login help
        # and two absolute doc paths under a blank line (`preflight-no-key`),
        # none of which is the diagnosis. Every 0.80.6 stderr is one paragraph.
        text = _one_line(re.split(r"\n\s*\n", (stderr or "").strip(), maxsplit=1)[0])
        if not text:
            return None
        line = _vendor_json_line(text)
        if line is not None:
            return (self.TIER_VENDOR_JSON, _cap(line))
        return (self.TIER_VERBATIM, _cap(text))

    def describe_failure(self, stdout: str, stderr: str) -> Optional[str]:
        """The stream's verdict, else stderr's — **precedence**, never composed.

        ``_DESCRIBE_FAILURE_CHANNELS["pi"]`` is ``STDOUT_ELSE_STDERR``, omp's:
        under ``--mode json`` every in-stream failure is on stdout with stderr
        empty, and a thrown pre-flight is a header-only stdout with the
        diagnosis on stderr. A header-only stream is silent here
        (:func:`_never_started`), so the missing key is described by its stderr
        sentence rather than by "run ended before any assistant message".

        A stdout that is not a pi stream (text mode) keeps 0.80.6's rule: stderr
        is the diagnosis, stdout is the answer.

        **Diagnostics first — but the words are load-bearing**: Lane A
        classifies the string this sentence is composed into, so the overflow,
        5xx and deadline sentences carry the shared tables' words
        (:func:`_named_for_the_ladder`).
        """
        diagnosis = self._diagnose_failure(stdout, stderr)
        return None if diagnosis is None else diagnosis[1]

    def _diagnose_failure(
        self, stdout: str, stderr: str
    ) -> Optional[Tuple[str, str]]:
        """``(tier, line)`` for :meth:`describe_failure`: the stream, else stderr.

        The tier says which rung answered, so ``tests/test_stderr_diagnosis.py``
        grades the precedence per capture: :data:`TIER_VENDOR_JSON` /
        :data:`TIER_VERBATIM` for a terminal ``error``/``aborted`` message (the
        same two tiers 0.80.6's stderr line took, now applied to
        ``errorMessage``), :data:`TIER_STREAM` for a structural verdict, and
        stderr's own tier for a silent or non-json stdout.
        """
        if has_stream_envelope(stdout, PI_DIALECT):
            events, _junk = _events(stdout)
            if not _never_started(events):
                verdict = terminal_verdict(stdout)
                if verdict:
                    messages = _assistant_ends(events)
                    final = messages[-1] if messages else {}
                    if (
                        shape_fault(messages, _stream_version(events), dialect=PI_DIALECT)
                        is None
                        and final.get("stopReason") in ("error", "aborted")
                        and _one_line(str(final.get("errorMessage") or ""))
                    ):
                        detail = _one_line(str(final.get("errorMessage") or ""))
                        tier = (
                            self.TIER_VENDOR_JSON
                            if _vendor_json_line(detail) is not None
                            else self.TIER_VERBATIM
                        )
                        return (tier, verdict)
                    return (self.TIER_STREAM, verdict)
        return self._diagnose(stdout, stderr)

    def parse_output(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """Read pi's ``--mode json`` stream. **Success is never the exit code.**

        In order (§7.3 of the plan, mirroring ``OmpProvider.parse_output``):

        1. **Empty stdout** is ``Empty output (stderr: …)``, as in text mode.
           **A non-empty stdout with no pi stream envelope** is a pi that ignored
           ``--mode``: it is read as a bare answer (the back-compat leg) and WARNed
           once. The test is the envelope (``has_stream_envelope``), never "any
           JSON line": a text-mode answer that is one JSON object must not be
           read as a stream with no assistant message, and a stream that starts
           with the ``session`` header but is cut or has junk lines stays here
           and fails by name — it is never handed to ``parse_answer_text``.
        2. **Shape.** A malformed assistant ``message_end`` fails by name, with a
           hard ``error_code``.
        3. **No assistant message** — including the header-only stdout of a thrown
           pre-flight — is omp's sentence plus ``; stderr: …``.
        4. **The last assistant ``message_end``**, on pi's closed set: ``stop``
           with text is the answer (``raw`` set to the answer on every outcome,
           and a JSON document the answer never closes is refused);  ``stop``
           with none is ``Empty output`` (plus pi's retry give-up sentence);
           ``length`` is ``Truncated output`` with no ``error_code`` (a findings
           file written before the cut may still be recovered); ``error`` is the
           ``errorMessage`` through the vendor-JSON tier, hard-coded, with the
           overflow and 5xx shapes named for the ladder; ``aborted`` and a
           ``toolUse``-final stream are ``Deadline exceeded``, ``ERROR_TIMEOUT``
           (the tool's name in the error, its result only in the diagnostic
           ``tool_result`` field — never where Lane A classifies it);
           anything else fails closed.
        5. **Overflow.** A real overflow — the vendor's context-length sentence on
           the terminal ``error``, or a failed overflow compaction that is not
           pi's truncated-recovery one — is named in the shared tables' words so
           it classifies ``context_length_exceeded``. A successful run that
           compacted after its answer is still a success.
        """
        raw = stdout or ""
        if not raw.strip() or not has_stream_envelope(raw, PI_DIALECT):
            if raw.strip():
                warn_gate_once(
                    ("pi-text-mode-stdout",),
                    f"WARNING: pi wrote no --mode json event stream; reading its "
                    f"stdout as a bare text-mode answer (the parser was written "
                    f"against pi {PI_DIALECT.verified_version}'s json mode).",
                )
            return self._parse_text_mode(raw, stderr)

        events, junk = _events(raw)
        version = _stream_version(events)
        warn_stream_version(version, PI_DIALECT)
        messages = _assistant_ends(events)

        def with_junk(sentence: Optional[str]) -> Optional[str]:
            if sentence and junk:
                return f"{sentence}; non-JSON output: {_first_line(junk[0])}"
            return sentence

        def failed(code: Optional[str]) -> Dict[str, Any]:
            out = {
                "success": False,
                "error": with_junk(terminal_verdict(raw)),
                "raw": raw,
                "data": None,
            }
            if code is not None:
                out["error_code"] = code
            return out

        if shape_fault(messages, version, dialect=PI_DIALECT) is not None:
            return failed(ERROR_SUBPROCESS_FAILED)

        if not messages:
            sentence = with_junk(terminal_verdict(raw))
            diagnosis = self._diagnose(raw, stderr)
            if diagnosis:
                sentence = f"{sentence}; stderr: {diagnosis[1]}"
            # No `error_code`: the model produced nothing, so the file channel is
            # welcome to look (and will find nothing).
            return {"success": False, "error": sentence, "raw": raw, "data": None}

        final = messages[-1]
        reason = final.get("stopReason")

        if reason == "stop":
            answer = _answer_text(final)
            if not answer.strip():
                gave_up = terminal_verdict(raw)
                return {
                    "success": False,
                    "error": f"Empty output ({gave_up})" if gave_up else "Empty output",
                    "raw": answer,
                    "data": None,
                }
            cut = _unclosed_container(answer)
            if cut is not None:
                closing = "]" if cut == "[" else "}"
                return {
                    "success": False,
                    "error": (
                        f"Truncated output (the answer opens a JSON document "
                        f"with '{cut}' and never closes it: no matching "
                        f"'{closing}' in {len(answer)} characters)"
                    ),
                    "raw": answer,
                    "data": None,
                }
            result = dict(parse_answer_text(answer))
            # `raw` carries the answer on every outcome: `ask`'s
            # `recover_answer_text` falls back to it, and without it would fall
            # back to the log's stdout — JSONL here, which it rejects.
            result.setdefault("raw", answer)
            return result

        if reason == "length":
            # No `error_code`: omp's unclosed-container disposition — a findings
            # file the model wrote before the cut may still be recovered.
            #
            # `incomplete` instead says what the code must not: the stream's own
            # terminal state is an output-limit cut, so the answer did not
            # finish, whether or not its text parses. The ask lane reads it
            # (as `details["incomplete"]`) and keeps the cut text as a partial
            # rather than counting it (plans/ask-answer-recovery-and-false-
            # success.md D3.1). The `stop` branch's unclosed-container refusal
            # above does not set it: there the model ended its turn, and the
            # refusal is a verdict on JSON, which an ask answer need not be.
            return {
                "success": False,
                "error": with_junk(terminal_verdict(raw)),
                "raw": _answer_text(final),
                "data": None,
                "incomplete": True,
            }

        if reason == "toolUse":
            out = failed(ERROR_TIMEOUT)
            # Diagnostics beside the error, never inside it: the error string is
            # what Lane A classifies (see `terminal_verdict`).
            name, detail = _tool_use_diagnostics(events)
            out["tool_name"] = name
            if detail:
                out["tool_result"] = detail
            return out

        if reason == "aborted":
            return failed(ERROR_TIMEOUT)

        return failed(ERROR_SUBPROCESS_FAILED)

    def vendor_text(self, stdout: str, stderr: str) -> Tuple[str, str]:
        """The terminal message's own ``errorMessage``, and **nothing earlier**.

        pi's json stream echoes our prompt three times (the user
        ``message_start``/``message_end`` and ``agent_end.messages``), carries
        pi's whole system prompt twice (the system message's ``sections``) and
        every tool result. Handed to the shared tables unreduced, a plan that
        discusses rate limits classifies a clean run ``rate_limited`` (measured:
        ``markers-in-tool-result``). So this is omp's reduction: the terminal
        assistant message's ``errorMessage`` when its ``stopReason`` is
        ``error``, ``aborted`` or unrecognized; ``""`` for ``stop``,
        ``toolUse`` and ``length`` (decided structurally, or not a failure); and
        ``""`` when there is no assistant message at all (a header-only
        pre-flight, whose diagnosis is stderr's).

        A stdout that is not a pi stream (prose, a bare JSON answer, empty) is
        returned unchanged, and so is anything when the reduction raises.
        stderr is never reduced.
        """
        try:
            if not has_stream_envelope(stdout, PI_DIALECT):
                return stdout, stderr
            events, _junk = _events(stdout)
            messages = _assistant_ends(events)
            if not messages:
                return "", stderr
            final = messages[-1]
            if final.get("stopReason") in ("stop", "toolUse", "length"):
                return "", stderr
            return _one_line(str(final.get("errorMessage") or "")), stderr
        except Exception:  # noqa: BLE001 - a failed reduction is identity
            return stdout, stderr

    def salvage_text(self, stdout: str) -> Optional[str]:
        """The last assistant message's answer text, never the event stream.

        pi's ``--mode json`` stdout is a transport: every assistant
        ``message_end`` carries a ``content`` array of ``thinking``/``toolCall``
        parts that the salvage gate would otherwise accept as findings. See
        :func:`~utils.providers.pi_family_stream.assistant_text_of_stream` for
        which message counts; ``None`` (a text-mode stdout that is its own
        answer) keeps the caller's old input. An empty or whitespace-only
        stdout is ``""``, a final verdict: ``generate`` always renders ``--mode
        json``, so no bytes means the transport carried nothing (a slot killed
        before pi printed, an early crash), and stderr's diagnostics must not
        reach the gate in its place.
        """
        return assistant_text_of_stream(stdout, PI_DIALECT)

    def classify_failure(
        self, stdout: str, stderr: str, exit_code: int = 0
    ) -> Optional[str]:
        """Structural first, then the declared tables over :meth:`vendor_text`.

        On the terminal assistant message: ``aborted``/``toolUse`` →
        ``timeout``; ``error`` that is a real context overflow
        (:func:`_is_overflow`) → ``context_length_exceeded`` — tested first, the
        order :func:`terminal_verdict` uses — then a ``401``/``403`` prefix →
        ``auth_failed``, ``429`` → ``rate_limited``, ``5xx`` → ``server_error``.
        Everything else — a 404 naming the model, ``Connection error.``, a
        pre-flight on stderr — reaches the shared tables through the reduced
        haystack.
        """
        try:
            envelope = has_stream_envelope(stdout, PI_DIALECT)
        except Exception:  # noqa: BLE001
            envelope = False
        if envelope:
            events, _junk = _events(stdout)
            messages = _assistant_ends(events)
            if messages:
                final = messages[-1]
                reason = final.get("stopReason")
                if reason in ("aborted", "toolUse"):
                    return STATUS_TIMEOUT
                if reason == "error":
                    # Overflow before the status ladder, as `terminal_verdict`
                    # (Lane A) and `classify_streams` (context before auth)
                    # order it: one message carrying both must not split lanes.
                    if _is_overflow(final, events):
                        return STATUS_CONTEXT_LENGTH_EXCEEDED
                    status = _error_status(final)
                    if status in (401, 403):
                        return STATUS_AUTH_FAILED
                    if status == 429:
                        return STATUS_RATE_LIMITED
                    if status is not None and 500 <= status < 600:
                        return CATEGORY_SERVER_ERROR
        return super().classify_failure(stdout, stderr, exit_code)

    def parse_usage(self, stdout: str, stderr: str) -> Optional[Dict[str, Any]]:
        """Sum ``usage`` over every assistant ``message_end``, plus compactions.

        The shared :func:`~utils.providers.pi_family_stream.sum_usage`: ``input``,
        ``output``, ``cacheRead``, ``totalTokens`` and ``cost.total`` over every
        assistant ``message_end`` (one per API call), ``tool_uses`` from the
        ``tool_execution_end`` count, and — pi's leg, on in :data:`PI_DIALECT` —
        each successful ``compaction_end.result.usage``, because a compaction is
        a paid summarization call no assistant message carries (measured:
        ``context-overflow-compacted``). An absent key stays absent, never 0.

        Three gaps, all pi's:

        * a summarization attempt that errored and was retried
          (``summarization_retry_*``) is not counted;
        * a failed or aborted compaction has ``result: undefined``, so its spend
          is invisible;
        * ``input`` excludes cached tokens (probe: 1704 = 1445 + 3 + 256).

        pi writes a **zeroed** usage block on an ``error`` message and on a
        provider that streams no usage (the container stub), so those keys are
        present and 0 — pi's number, not an invented one.

        Cost: ``cost_usd`` is pi's own catalog price, an **estimate**. A custom
        ``models.json`` provider with no ``cost`` block (the container's ``stub``)
        prices every call at 0, which ``describe_usage`` suppresses in the
        rendered clause while ``usage.json`` keeps the zero. Price a live run off
        the OpenRouter key's own usage, never off this self-report.
        """
        if not has_stream_envelope(stdout, PI_DIALECT):
            return None
        events, _junk = _events(stdout)
        return sum_usage(events, PI_DIALECT)

    def _parse_text_mode(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """The 0.80.6 text-mode reader: stdout is the answer, stderr is named."""
        result = self._parse_stdout(stdout)
        if result.get("success"):
            return result

        detail = self._diagnose(stdout, stderr)
        if not detail:
            return result
        result = dict(result)
        result["error"] = (
            f"{result.get('error') or 'parse failed'} (stderr: {detail[1]})"
        )
        return result

    def _parse_stdout(self, stdout: str) -> Dict[str, Any]:
        """The bare-answer reader, read on its own (:func:`parse_answer_text`)."""
        return parse_answer_text(stdout)
