"""The pi-family ``--mode json`` stream reader, shared by ``pi`` and ``omp``.

pi and oh-my-pi write the same JSONL event family under ``--mode json``: a
``session`` header, ``agent_start``/``turn_start``, ``message_start`` /
``message_update`` / ``message_end`` per message, ``tool_execution_*`` per tool
call, ``turn_end``/``agent_end`` repeating what came before, and the retry and
compaction events. omp's adapter was the first to read it, and its reader is
fixture-graded (``tests/fixtures/omp/``). This module is that reader, lifted out
of ``utils/providers/omp.py`` so pi can read the same stream without importing
omp (``plans/opencode-validator-false-rate-limit-and-denied-turn.md`` §7.2,
option R3).

**Parameterised, never product-specific.** Everything that differs between the
two products — the name, the version the parser was measured at, the stream
``version`` it expects, the closed ``stopReason`` set, the compaction event —
is a :class:`StreamDialect` value the adapter passes in. So a sentence built
here for omp is byte-identical to the one omp built itself, and pi's says
"pi" and its own numbers.

**Dependency order**, pinned by ``tests/test_pi_family_stream.py``:
``base`` / ``json_extractor`` → this module → ``pi`` → ``omp``. This module
never imports ``utils.providers.pi`` or ``utils.providers.omp``; that is why
``_one_line``, ``_cap`` and ``_MAX_DIAGNOSIS_CHARS`` live here (the reader calls
them) and pi.py imports them back.
"""
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .base import warn_gate_once

#: ``describe_failure`` is a SUMMARY, not a second copy of the stream. The
#: caller keeps the full text — Lane A in ``details["stderr"]`` and in the log
#: file — so a long stderr is capped here rather than promoted into an error
#: string. pi's longest committed stderr is 218 bytes, so nothing measured is
#: actually cut; the cap exists so a future release cannot make it one.
_MAX_DIAGNOSIS_CHARS = 300


def _one_line(text: str) -> str:
    """Collapse a captured fragment to a single line, whitespace normalized."""
    return " ".join((text or "").split())


def _cap(text: str) -> str:
    """One short line (:data:`_MAX_DIAGNOSIS_CHARS`), with an explicit ellipsis."""
    if len(text) <= _MAX_DIAGNOSIS_CHARS:
        return text
    return text[:_MAX_DIAGNOSIS_CHARS - 1].rstrip() + "…"


#: What every assistant ``message_end`` must carry before anything reads it.
#: A release that renames one of these fails by name at the first parse, with a
#: hard error code, rather than handing ``parse_answer_text`` a message whose
#: shape is not the measured one.
_ASSISTANT_MESSAGE_REQUIRED_KEYS = ("role", "content", "stopReason")

#: The event ``type`` values the pi family writes under ``--mode json``, exact
#: names. Read by :func:`has_stream_envelope` only. ``notice`` is omp's (one
#: committed omp row carries it); pi 0.87.1's ``docs/json.md`` lists the rest.
PI_FAMILY_EVENT_TYPES: Tuple[str, ...] = (
    "session",
    "agent_start",
    "turn_start",
    "message_start",
    "message_update",
    "message_end",
    "turn_end",
    "agent_end",
    "agent_settled",
    "entry_appended",
    "notice",
)

#: Event ``type`` prefixes of the same family: ``tool_execution_start/update/end``,
#: ``auto_retry_start/end``, pi's ``compaction_start/end`` and omp's
#: ``auto_compaction_start/end``.
PI_FAMILY_EVENT_PREFIXES: Tuple[str, ...] = (
    "tool_execution_",
    "auto_retry_",
    "compaction_",
    "auto_compaction_",
)


@dataclass(frozen=True)
class StreamDialect:
    """What one product's stream differs in. Every sentence reads its words here.

    * ``product`` — the name the sentences use (``"omp"``, ``"pi"``).
    * ``verified_version`` — the CLI version the parser was measured against.
    * ``stream_version`` — the ``session`` header's ``version`` it expects. A
      different value is WARNed once and quoted, never refused.
    * ``stop_reasons`` — the closed ``stopReason`` set. Anything else fails
      closed, naming the enum and this dialect.
    * ``compaction_event`` — the event a compaction ends with
      (``compaction_end`` for pi, ``auto_compaction_end`` for omp).
    * ``compaction_usage`` — whether :func:`sum_usage` adds that event's
      ``result.usage``. Off for omp until T7.15 decides it.
    * ``header_type`` / ``event_types`` / ``event_prefixes`` — what
      :func:`has_stream_envelope` recognises as this product's stream.
    """

    product: str
    verified_version: str
    stream_version: int
    stop_reasons: Tuple[str, ...]
    compaction_event: Optional[str] = None
    compaction_usage: bool = False
    header_type: str = "session"
    event_types: Tuple[str, ...] = PI_FAMILY_EVENT_TYPES
    event_prefixes: Tuple[str, ...] = PI_FAMILY_EVENT_PREFIXES

    def knows_event(self, kind: Any) -> bool:
        """True when ``kind`` is a string naming an event of this family."""
        if not isinstance(kind, str):
            return False
        return kind in self.event_types or kind.startswith(self.event_prefixes)


# --------------------------------------------------------------------------- #
# The stream reader. One implementation, read by each adapter's `parse_output`,
# `describe_failure`, `classify_failure` and `parse_usage` alike — so the
# report's `Reason:` line and the log's error string cannot drift apart.
# --------------------------------------------------------------------------- #

def _events(stdout: str) -> Tuple[List[Dict[str, Any]], List[str]]:
    """``(parsed JSONL events, the lines that were not JSON)``.

    A non-JSON line is kept rather than dropped: a banner a future release grows
    would land here, and naming it in the error is what turns "this stream made
    no sense" into something actionable.
    """
    events: List[Dict[str, Any]] = []
    junk: List[str] = []
    for line in (stdout or "").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            parsed = json.loads(line)
        except ValueError:
            junk.append(line)
            continue
        if isinstance(parsed, dict):
            events.append(parsed)
        else:
            junk.append(line)
    return events, junk


def has_stream_envelope(stdout: str, dialect: StreamDialect) -> bool:
    """True when ``stdout`` is this dialect's event stream, not a bare answer.

    ``_events`` counts every JSON *object* line as an event, so "any JSON
    events" is the wrong test for choosing the stream parser: a text-mode answer
    that is itself one JSON object (``{"answer":"OK"}``, a findings object on one
    line) would be read as a stream with no assistant message. The test here is
    the envelope instead (§7.3 step 1):

    * the first non-blank line parses as an object whose ``type`` is the
      dialect's header (``session``) — the normal case, which also keeps a
      stream that starts with the header but is cut or has junk lines on the
      stream parser, so it fails by name there; or
    * some line parses as an object whose ``type`` is a string naming an event
      of this family (a banner line ahead of the header, say).

    Anything else — a bare JSON object with no such ``type``, a JSON array,
    prose, a fenced block, an empty stdout — is not a stream.

    Unused by omp for now: omp's parser keeps its "any events" test, and adopting
    this is a later, separate change.
    """
    first = True
    for line in (stdout or "").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            parsed = json.loads(line)
        except ValueError:
            first = False
            continue
        if isinstance(parsed, dict):
            kind = parsed.get("type")
            if first and kind == dialect.header_type:
                return True
            if dialect.knows_event(kind):
                return True
        first = False
    return False


def _stream_version(events: List[Dict[str, Any]]) -> Optional[int]:
    """The ``session`` event's ``version``, or ``None`` when there was none."""
    for event in events:
        if event.get("type") == "session":
            version = event.get("version")
            return version if isinstance(version, int) else None
    return None


def version_clause(version: Optional[int], dialect: StreamDialect) -> str:
    """The parenthetical every shape error carries, naming what the parser knows."""
    seen = dialect.stream_version if version is None else version
    return (
        f"stream version {seen}; the parser was written against "
        f"{dialect.product} {dialect.verified_version}'s "
        f"version {dialect.stream_version} stream"
    )


def warn_stream_version(version: Optional[int], dialect: StreamDialect) -> None:
    """One WARN per process for a ``session.version`` that is not the measured one."""
    if version is None or version == dialect.stream_version:
        return
    warn_gate_once(
        (f"{dialect.product}-stream-version", version),
        f"WARNING: {dialect.product} stream version {version}; the parser was "
        f"written against {dialect.stream_version} "
        f"({dialect.product} {dialect.verified_version}).",
    )


def _assistant_ends(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Every assistant ``message_end`` message object, in stream order.

    The assistant ``message_start`` already carries the final message — content,
    ``stopReason``, ``errorMessage`` — so it is not a placeholder and therefore
    not a marker. Only ``message_end`` is collected, and ``turn_end`` /
    ``agent_end`` (which repeat the same message, and in ``agent_end``'s case the
    whole conversation including our own prompt) are ignored.
    """
    out = []
    for event in events:
        if event.get("type") != "message_end":
            continue
        message = event.get("message")
        if isinstance(message, dict) and message.get("role") == "assistant":
            out.append(message)
    return out


def _tool_ends(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Every ``tool_execution_end`` event, in stream order."""
    return [e for e in events if e.get("type") == "tool_execution_end"]


def _result_text(event: Dict[str, Any]) -> str:
    """A ``tool_execution_end``'s own result text — never assistant text.

    The denial marker is matched here and nowhere else: the model may quote the
    sentence in its answer, and a quoted denial is prose, not a denial.
    """
    result = event.get("result")
    if not isinstance(result, dict):
        return ""
    parts = []
    for item in result.get("content") or []:
        if isinstance(item, dict) and isinstance(item.get("text"), str):
            parts.append(item["text"])
    return "\n".join(parts)


def shape_fault(
    messages: List[Dict[str, Any]],
    version: Optional[int],
    *,
    dialect: StreamDialect,
) -> Optional[str]:
    """The first assistant ``message_end`` missing a required key, as a sentence.

    Checked **by name, before anything reads the stream**, because nothing else
    guards the JSONL surface: the help-text gate covers the argv, and a daily
    release can change the event shape under an unchanged help text with no
    marker at all.
    """
    for message in messages:
        for key in _ASSISTANT_MESSAGE_REQUIRED_KEYS:
            if key not in message:
                return (
                    f"assistant message_end without {key} "
                    f"({version_clause(version, dialect)})"
                )
        if not isinstance(message.get("content"), list):
            return (
                f"assistant message_end whose content is not a list "
                f"({version_clause(version, dialect)})"
            )
        if not isinstance(message.get("stopReason"), str):
            return (
                f"assistant message_end whose stopReason is not a string "
                f"({version_clause(version, dialect)})"
            )
    return None


def unrecognized_stop_reason(
    final: Dict[str, Any], version: Optional[int], dialect: StreamDialect
) -> str:
    """The fail-closed sentence for a ``stopReason`` outside the dialect's set.

    An unobserved enum may be a cut, a refusal or a rename, and the parser cannot
    tell which, so it names the enum, the set it knows and the stream version,
    plus the message's own ``errorMessage`` when it carries one.
    """
    reason = final.get("stopReason")
    sentence = (
        f"unrecognized stopReason {reason!r} on the last assistant message "
        f"({dialect.product} {dialect.verified_version} emits "
        f"{'/'.join(dialect.stop_reasons)}; "
        f"{version_clause(version, dialect)})"
    )
    detail = _one_line(str(final.get("errorMessage") or ""))
    return f"{sentence}; {detail}" if detail else sentence


def _answer_text(message: Dict[str, Any]) -> str:
    """The concatenated ``text`` content parts of a message — **and only those**.

    A ``thinking`` part is the model's reasoning, not its answer, and a
    ``toolCall`` part has no text; neither is ever concatenated in, so a fenced
    array inside a thinking block cannot become the findings.
    """
    parts = []
    for item in message.get("content") or []:
        if isinstance(item, dict) and item.get("type") == "text":
            text = item.get("text")
            if isinstance(text, str):
                parts.append(text)
    return "".join(parts)


def assistant_text_of_stream(stdout: str, dialect: StreamDialect) -> Optional[str]:
    """The **last** assistant message's answer text, for salvage — or ``None``.

    This is the pi-family ``LLMProvider.salvage_text``. A failed attempt's
    stdout is a transport stream, and every assistant ``message_end`` carries a
    ``"content": [...]`` array, so handing the raw stream to the salvage gate
    (``has_salvageable_json``) accepts event data as findings: a reviewer
    killed while a ``toolCall`` ran was "salvaged" from its own ``thinking`` and
    ``toolCall`` parts (plan: review-run-scope-salvage-and-failure-visibility
    §4). What comes back here is only the words the model wrote as its answer.

    Which message is "last":

    * **A message cut mid-stream** — an assistant ``message_start`` with no
      ``message_end`` after it. Its text is its ``text_delta``s, joined in
      order (``toolcall_delta``s and thinking deltas are never text). A
      reviewer killed while printing its array is the case salvage exists for.
    * Otherwise **the last assistant** ``message_end``: its ``text`` parts
      (:func:`_answer_text`), the same message the adapters' ``parse_output``
      reads as the answer (``final = messages[-1]``).

    A last message with no text gives ``""`` — "nothing to salvage", which is
    a verdict and not a gap: the incident this exists for was a ``thinking``
    part and a ``toolCall`` part, killed while the tool ran.

    **Earlier assistant messages are dropped, not capped.** They are narration
    between tool calls ("I'll now open X") and can quote an example array.
    Joining them in would let dozens of turns push the trailing array past the
    caller's size cap, and would let an example array pass the gate or hand
    the salvage subagent two arrays to choose between. A run that printed its
    answer and then called another tool loses that answer here, exactly as it
    does in ``parse_output``.

    ``None`` when ``stdout`` is not this dialect's stream at all
    (:func:`has_stream_envelope`): a bare text-mode answer is its own answer
    text, so the caller keeps its old input rather than being told "nothing".

    **An empty or whitespace-only stdout is ``""``, not ``None``.** Both
    adapters render ``--mode json`` on every ``generate`` (pi unconditionally,
    omp as a required flag), so a stdout that holds no bytes is a transport
    that carried nothing — a slot killed before the CLI printed its header, an
    early crash — and never a text-mode answer. ``None`` there would send the
    gate to stderr, whose diagnostics can be array-shaped
    (``{"error": ..., "attempts": []}``) and pass ``has_salvageable_json``: the
    outcome D4.3 removes for stream adapters. ``""`` keeps the verdict final.
    """
    if not (stdout or "").strip():
        return ""
    if not has_stream_envelope(stdout, dialect):
        return None
    events, _junk = _events(stdout)
    last_text = ""
    open_deltas: Optional[List[str]] = None
    for event in events:
        kind = event.get("type")
        message = event.get("message")
        is_assistant = isinstance(message, dict) and message.get("role") == "assistant"
        if kind == "message_start" and is_assistant:
            # A new assistant message supersedes everything before it, finished
            # or not: only the last message is ever the answer.
            open_deltas = []
        elif kind == "message_end" and is_assistant:
            last_text = _answer_text(message)
            open_deltas = None
        elif kind == "message_update" and open_deltas is not None:
            update = event.get("assistantMessageEvent")
            if isinstance(update, dict) and update.get("type") == "text_delta":
                delta = update.get("delta")
                if isinstance(delta, str):
                    open_deltas.append(delta)
    if open_deltas is not None:
        return "".join(open_deltas)
    return last_text


def _unclosed_container(text: str) -> Optional[str]:
    """The opening bracket of a JSON document the answer **never closes**.

    ``None`` when the answer does not begin a JSON document at all, and ``None``
    when the document it begins is balanced — a complete findings array followed
    by a closing sentence is exactly what the shared extractor exists to
    recover, and refusing it here would cost every honest run that says a word
    after its answer.

    **Why the question is the leading container rather than ``json.loads``**:
    both a cut answer and a complete array with a trailing sentence fail
    ``json.loads``, and only one of the two is a truncation. What separates them
    is whether the document the answer *opened* was ever closed, which is a
    bracket walk and not a parse.

    Nesting is counted in the leading container's own brackets only, so
    ``[{"file": "a.py", "line_range": [10, 15]}`` is unclosed (one ``[`` still
    open) while ``[{"line_range": [10, 15]}]`` is not.
    """
    text = (text or "").strip()
    if not text or text[0] not in "[{":
        return None
    opener = text[0]
    closer = "]" if opener == "[" else "}"
    depth = 0
    in_string = False
    escape_next = False
    for char in text:
        if escape_next:
            escape_next = False
        elif in_string and char == "\\":
            escape_next = True
        elif char == '"':
            in_string = not in_string
        elif not in_string:
            if char == opener:
                depth += 1
            elif char == closer:
                depth -= 1
                if depth == 0:
                    return None
    return opener


def _retry_give_up(events: List[Dict[str, Any]]) -> Optional[str]:
    """The last failed ``auto_retry_end``'s ``finalError``, or ``None``.

    omp's empty-stop retry gives up with an event rather than an exit code, and
    the sentence it carries is the only thing on either channel that says why a
    run that exited 0 produced no text.
    """
    for event in reversed(events):
        if event.get("type") != "auto_retry_end" or event.get("success"):
            continue
        detail = _one_line(str(event.get("finalError") or ""))
        if detail:
            return _cap(detail)
    return None


def _first_line(text: str) -> str:
    for line in (text or "").splitlines():
        if line.strip():
            return _cap(_one_line(line))
    return ""


def sum_usage(
    events: List[Dict[str, Any]], dialect: StreamDialect
) -> Optional[Dict[str, Any]]:
    """Sum ``usage`` over every assistant ``message_end`` — one per API call.

    A run with tool calls has one assistant message per call, so a multi-turn
    review reports the whole dispatch rather than its last turn. An absent
    block leaves the key **absent**, never 0: a zero would average into
    per-phase totals and read as a free run. ``tool_uses`` is the
    ``tool_execution_end`` count.

    When the dialect turns ``compaction_usage`` on, each
    ``<compaction_event>.result.usage`` is added with the same keys: a
    compaction is a paid summarization call that no assistant ``message_end``
    carries. It is off for omp (T7.15).

    ``None`` when there is nothing to report — no events, or no usage and no
    tool calls.
    """
    if not events:
        return None
    totals: Dict[str, Any] = {}
    seen = False

    def _add(key: str, value: Any) -> None:
        nonlocal seen
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return
        seen = True
        totals[key] = totals.get(key, 0) + value

    def _add_usage(usage: Any) -> None:
        if not isinstance(usage, dict):
            return
        _add("input_tokens", usage.get("input"))
        _add("output_tokens", usage.get("output"))
        _add("cached_input_tokens", usage.get("cacheRead"))
        _add("total_tokens", usage.get("totalTokens"))
        cost = usage.get("cost")
        if isinstance(cost, dict):
            _add("cost_usd", cost.get("total"))

    for message in _assistant_ends(events):
        _add_usage(message.get("usage"))

    if dialect.compaction_usage and dialect.compaction_event:
        for event in events:
            if event.get("type") != dialect.compaction_event:
                continue
            result = event.get("result")
            if isinstance(result, dict):
                _add_usage(result.get("usage"))

    tool_uses = len(_tool_ends(events))
    if tool_uses:
        totals["tool_uses"] = tool_uses
        seen = True
    return totals if seen else None
