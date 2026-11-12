"""What one run of a provider CLI means: a capture in, the result dict out.

``llm_client.invoke_with_provider`` prepares a dispatch, runs the CLI, hands
what it captured here as a :class:`Capture`, and writes the provider log from
what comes back. :func:`outcome_from_capture` is the one reading of a capture:
a non-zero exit, an exit 0 (parsed or not), a deadline kill and a launch
failure all leave through it, and the keys a child that ran carries on
``details`` are attached by one tail, so a new key cannot miss a path.

Nothing here spawns a process or touches the filesystem. The jail's read-back
needs the attempt's live context, so the caller passes it in as a callable;
the fixture grader passes none. Contract and the rules each key follows:
docs/development/providers.md#reading-a-capture.
"""

import json
import re
import sys
from dataclasses import dataclass
from typing import Any, Callable, Collection, Dict, FrozenSet, List, Optional, Tuple

from . import process_capture
from . import readonly_audit as _readonly_audit_mod
from . import structured_output
from .json_extractor import _ANSI_ESCAPE, looks_like_ndjson
from .providers.base import (
    CATEGORY_SANDBOX_UNAVAILABLE,
    SANDBOX_RUNG_LANDLOCK,
    SANDBOX_RUNG_PLUGIN_LANDLOCK,
    SANDBOX_RUNG_UNSANDBOXED,
    _matches_marker,
    availability_from_failure,
    exit_zero_failure_category,
    launch_refusal,
    sandbox_hint,
    sandbox_rung_id,
)
from .providers.result_envelope import is_clean_envelope
from .redact import redact_text
from .retry_ladder import (
    STATUS_RUNNER_ERROR, STATUS_SPAWN_FAILED, STATUS_TIMEOUT, STATUS_UNPARSEABLE,
)


# Error codes for consistent error reporting
ERROR_TIMEOUT = "TIMEOUT"
ERROR_PARSE_ERROR = "PARSE_ERROR"
ERROR_BINARY_NOT_FOUND = "BINARY_NOT_FOUND"
ERROR_SUBPROCESS_FAILED = "SUBPROCESS_FAILED"
ERROR_FILE_NOT_FOUND = "FILE_NOT_FOUND"
ERROR_PROMPT_TOO_LONG = "PROMPT_TOO_LONG"
ERROR_PROMPT_UNSAFE = "PROMPT_UNSAFE"


@dataclass(frozen=True)
class Capture:
    """What one run of a provider CLI left: its streams as decoded text, how it
    ended, how long it took and what the capture cut.

    One ending holds: ``launch_error`` (nothing ran), ``timed_out`` (the
    plugin stopped it, at the deadline or, with ``stream_stop``, when its
    stdout watch asked; ``exit_code`` is ``None``), or an ``exit_code``. The
    streams are kept as the spawn returned them, never coerced: a stand-in
    spawn may hand back ``None``. The executor's ``dispatch_spawn._Capture``
    carries the same stream fields, and its readers take this value too.
    """

    stdout: Any = ""
    stderr: Any = ""
    exit_code: Optional[int] = None
    timed_out: bool = False
    duration: float = 0.0
    #: Why the CLI could not be started (the launch error's message), or
    #: ``None`` when it ran.
    launch_error: Optional[str] = None
    #: The launch failed because the executable was not found
    #: (``FileNotFoundError``), not for another reason.
    launch_not_found: bool = False
    #: The streams the capture cut at ``stream_bound`` (``process_capture``).
    capped_streams: FrozenSet[str] = frozenset()
    #: The per-stream bound the capture ran under; a capped stdout's refusal
    #: names it.
    stream_bound: int = process_capture.MAX_STREAM_BYTES
    #: What a deadline kill's sweep did to the CLI and to each process group it
    #: had spawned, as the ``"; <verdicts>"`` suffix of the timeout's log line
    #: (D3.3), or ``""``.
    tree_sweep: str = ""
    #: Set only with ``timed_out``: the adapter's stdout watch, not the
    #: deadline, asked for the stop, and this is its reason
    #: (``process_capture.StreamStopped``); ``None`` for a deadline kill.
    stream_stop: Optional[str] = None
    #: The CLI exited while a process it started still held its output, and
    #: what the deadline's sweep then did (``llm_client._held_pipe_record``),
    #: or ``""``; with ``timed_out``, why the call was ended as a timeout.
    #: Lands on ``details["pipe_held"]``, and the attempt's read-only audit is
    #: not clean: that process's writes are not in the CLI's stream.
    pipe_held: str = ""


#: The jail's read-back for one child that ran (``llm_client._jail_after_child``
#: with its attempt bound): called as ``read(details, *, stdout, stderr,
#: returncode, failed, timed_out)``, it writes its keys onto ``details`` and
#: returns ``(error, note)``. A callable rather than a mapping because it
#: samples live state at a fixed point of the reading (before the read-only
#: audit on a non-zero exit, after it otherwise), and on an exit 0 whether a
#: jail failure is read at all depends on the parse.
JailReadBack = Callable[..., Tuple[Optional[str], str]]

#: The provider log's writer (``llm_client._log_outcome`` with its log file
#: bound): called as ``log(capture, result)``, once, at the point each path
#: writes its log (``outcome_from_capture``), so the log survives whatever
#: raises later in the reading.
LogWriter = Callable[["Capture", Dict[str, Any]], None]


#: ``details["sandbox"]`` for a slot that ran under the D6 fallback
#: on the **uncontained** rung: the runner's own OS sandbox could not start and
#: ``sandbox_fallback: auto`` (the default) let the read-only dispatch run
#: without any boundary. Absent means "ran as the adapter's default argv renders
#: it". A slot on a **contained** rung (landlock rung, 2026-09-22) carries that
#: rung's id here instead (``landlock``) — never this word, which would claim
#: the opposite of what happened.
SANDBOX_BYPASSED = "bypassed"

#: The per-slot record word for a contained fallback rung — ``models_served``'s
#: ``sandbox: fallback-landlock`` — so a run's provenance greps apart from
#: ``bypassed`` the way ``[SANDBOX_FALLBACK]`` greps apart from
#: ``[SANDBOX_BYPASSED]``. The renderers (``html_report_generator``,
#: ``run_status``) read the recorded word back, never a bool.
SANDBOX_FALLBACK_WORD_PREFIX = "fallback-"

#: The contained rung ids a record word may name. Closed on purpose: a value
#: nobody declared is dropped rather than recorded, exactly as an unknown word
#: always was, so a stray string can never read as a sandbox.
_CONTAINED_RUNG_IDS = frozenset({SANDBOX_RUNG_LANDLOCK})

#: The ``incidental``-grade rung ids a record word may name: the
#: plugin's own Landlock jail. A **separate** closed set beside
#: :data:`_CONTAINED_RUNG_IDS`, which stays ``{landlock}`` so nothing that reads
#: "contained" widens; without this set ``llm_client.sandbox_record_word`` would drop the
#: rung from every per-slot record, ``models_served`` and reaggregate while the
#: log line said it ran. Recorded as ``fallback-plugin-landlock``; the renderers
#: keep their own closed set of incidental words (they import no provider code).
_INCIDENTAL_RUNG_IDS = frozenset({SANDBOX_RUNG_PLUGIN_LANDLOCK})

#: ``details["failure_reason"]`` for a jailed slot that failed on a
#: codex-internal EACCES the plugin's jail caused (F1 "Where it sits" item 6),
#: or whose required allow entry vanished before the spawn. Non-retryable and
#: never moved to another rung.
FAILURE_JAIL_DENIED = "jail-denied"

def _attach_sandbox_word(details: Dict[str, Any], sandbox_fallback: Any) -> None:
    """Record the D6 override on ``details["sandbox"]`` for a child that ran.

    ``bypassed`` for the uncontained rung, the rung id for a contained or
    incidental one (``plugin-landlock``, 2026-09-30), and
    nothing when the override did not fire. Called on every path where the
    child actually ran — exit 0, a non-zero exit, and a timeout kill — because
    the slot ran without the runner's sandbox whatever it then returned: a
    record that dropped the word on failure would hide exactly the slots an
    operator most needs to audit (the dogfood run 2026-09-25 lost a bypassed
    codex slot's provenance this way).
    """
    fallback_rung = sandbox_rung_id(sandbox_fallback)
    if fallback_rung:
        details["sandbox"] = (
            SANDBOX_BYPASSED if fallback_rung == SANDBOX_RUNG_UNSANDBOXED
            else fallback_rung
        )


#: The storage caps. A *successful* ``review-plan`` against a provider
#: emitting 3 MiB per stream wrote a 6,254,326 B ``log_gemini_*.txt``:
#: ``llm_client._save_log`` truncated the prompt and nothing else. Lane B already ``_tail``s its
#: failure captures at 64 KiB, so the log path is the one that was uncapped.
#:
#: Each stream keeps its **last** ``MAX_LOG_TAIL_LINES`` lines with every line
#: cut to ``MAX_LOG_LINE_BYTES``; the per-stream and whole-file byte budgets are
#: the backstops that make the ~100 KB total a property of the written file
#: rather than of the input. Measured against the captured 6 MB artifact,
#: 64 KiB/line + last-20 alone took it to ~17 KB.
MAX_LOG_LINE_BYTES = 64 * 1024
MAX_LOG_TAIL_LINES = 20
MAX_LOG_TOTAL_BYTES = 100 * 1024
#: Two streams plus a ≤5 KB prompt and the header stay inside the total.
MAX_LOG_STREAM_BYTES = 45 * 1024


def _redact(text: str) -> str:
    """The one redaction boundary (``redact.redact_text``), as ``llm_client``
    and the fan-out lanes read it from here. Callers redact before any tail or
    cut. The call is on a per-invocation path, not a per-line one.
    """
    return redact_text(text)


def _cut_bytes(text: str, limit: int, marker: str) -> str:
    """``text`` cut to ``limit`` UTF-8 bytes, head kept, ``marker`` appended.

    The marker is charged against ``limit`` rather than added on top, so a cap
    stated as a number of bytes really is one — a "~100 KB" file that comes out
    at 100 KB plus a footer is a cap nobody can assert on.
    """
    encoded = text.encode("utf-8", errors="replace")
    if len(encoded) <= limit:
        return text
    keep = max(0, limit - len(marker.encode("utf-8")))
    return encoded[:keep].decode("utf-8", errors="ignore") + marker


def _cut_bytes_middle(text: str, limit: int, marker: str) -> str:
    """``text`` cut to ``limit`` UTF-8 bytes, head **and tail** kept, ``marker`` between.

    A stream's end is where its answer is: codex's final ``agent_message`` and
    ``turn.completed`` come last, after a few multi-KB ``aggregated_output`` lines. A quarter of the
    budget keeps the opening, the rest keeps the ending. The marker is charged
    against ``limit``, as in :func:`_cut_bytes`.
    """
    encoded = text.encode("utf-8", errors="replace")
    if len(encoded) <= limit:
        return text
    room = max(0, limit - len(marker.encode("utf-8")))
    head = room // 4
    tail = room - head
    return (
        encoded[:head].decode("utf-8", errors="ignore")
        + marker
        + (encoded[len(encoded) - tail:].decode("utf-8", errors="ignore") if tail else "")
    )


def _bound_stream(text: str) -> str:
    """One captured stream, bounded — **after** it has been redacted.

    Order is normative and is the reason L3 and L4 are one atomic change: every
    cut below slices by construction, and a cut applied first leaves a remnant no
    pattern matches. The last-20-lines rule would decapitate a PEM block's
    ``-----BEGIN`` header and keep its body; the per-line cut would keep a value
    whose key name it had just removed. Neither is recoverable downstream.
    """
    if not text:
        return ""
    lines = text.splitlines()
    if len(lines) > MAX_LOG_TAIL_LINES:
        dropped = len(lines) - MAX_LOG_TAIL_LINES
        lines = [
            f"... [{dropped} earlier line(s) truncated; last {MAX_LOG_TAIL_LINES} kept]"
        ] + lines[-MAX_LOG_TAIL_LINES:]
    bounded = [
        _cut_bytes(line, MAX_LOG_LINE_BYTES, f" ... [line truncated at {MAX_LOG_LINE_BYTES} B]")
        for line in lines
    ]
    return _cut_bytes_middle(
        "\n".join(bounded),
        MAX_LOG_STREAM_BYTES,
        f"\n... [stream truncated at {MAX_LOG_STREAM_BYTES} B; middle elided]\n",
    )


def _attach_stdout_excerpt(details: Dict[str, Any], stdout: Optional[str]) -> None:
    """Put the run's stdout on ``details`` as ``stdout_excerpt``, redacted then bounded.

    **Why a helper and not a third copy.** ``invoke_with_provider`` loses a run
    three ways — a non-zero exit, a timeout kill, and a zero exit whose output
    would not parse — and all three are cases where the provider may already have
    said the thing the caller needs. The rule for carrying that text out is not
    one line but four decisions (``_redact`` *before* ``_bound_stream``, per;
    ``.strip()``; set the key only when something survives; never the
    raw stream), and this module argues elsewhere that a rule spelled three times
    is a rule that drifts twice — see ``_bound_stream``'s own note that the
    redact/bound order "is normative", and the forward-maintenance case against
    two hand-aligned blocks plus a comment. A cap tightened or a pattern added at
    one copy and not the others would leak from whichever site was forgotten, and
    the leak would be invisible until an artifact was read by a human. So it is
    written once, here, and :func:`outcome_from_capture`'s one tail calls it for
    all three.

    **Why the key is omitted rather than set empty.** Consumers test
    ``details.get("stdout_excerpt")`` for "did the provider say anything we can
    still use" — salvage gating at ``code_review_orchestrator.py``'s site A reads
    it ahead of ``details["stderr"]`` for exactly that. An always-present key
    holding ``""`` would make every one of those call sites carry a second
    emptiness check, and the first one written without it would treat "the
    provider printed nothing" as "the provider printed something". Absent means
    absent.

    Args:
        details: The result envelope's ``details`` dict, mutated in place.
        stdout: The raw captured stdout, or ``None`` when the path never had it
            (a ``TimeoutExpired`` that carried no partial output).
    """
    excerpt = _bound_stream(_redact(stdout or "")).strip()
    if excerpt:
        details["stdout_excerpt"] = excerpt


#: The key :func:`_attach_salvage_text` writes. Its *presence* is a verdict:
#: ``""`` means "the adapter read its stream and found no answer text", and an
#: absent key means "no reducer applies" (``salvage_source`` then falls back to
#: ``stdout_excerpt`` and stderr).
SALVAGE_TEXT_KEY = "salvage_text"


def _answer_window_start(text: str) -> Optional[int]:
    """Where the answer's JSON document opens, by a string-aware bracket walk.

    The depth-0 ``[`` or ``{`` that is **never closed** (the answer was cut
    mid-document) when there is one; otherwise the first depth-0 ``[``/``{``;
    ``None`` when the text has no bracket at all. Quotes toggle string state
    only inside a container, so an apostrophe or a quoted word in the prose
    ahead of the array cannot hide its bracket. Nesting is tracked with a stack
    of openers (the same string-aware walk as ``_unclosed_container`` in
    ``utils/providers/pi_family_stream.py``, over the whole text rather than
    from its first character).
    """
    first: Optional[int] = None
    open_at: Optional[int] = None
    stack: List[str] = []
    in_string = False
    escape_next = False
    pairs = {"]": "[", "}": "{"}
    for index, char in enumerate(text):
        if stack:
            if escape_next:
                escape_next = False
                continue
            if in_string:
                if char == "\\":
                    escape_next = True
                elif char == '"':
                    in_string = False
                continue
            if char == '"':
                in_string = True
            elif char in "[{":
                stack.append(char)
            elif char in pairs and stack[-1] == pairs[char]:
                stack.pop()
                if not stack:
                    open_at = None
        elif char in "[{":
            stack.append(char)
            open_at = index
            if first is None:
                first = index
    if stack and open_at is not None:
        return open_at
    return first


def _bound_salvage_text(text: str) -> str:
    """Salvage text capped at ``MAX_LOG_STREAM_BYTES``, **never cut before the answer**.

    ``_bound_stream``'s last-20-lines rule is the wrong bound here: it would cut
    the opening bracket off a pretty-printed array, which is the one part a
    repair pass cannot reconstruct. So text within the cap is kept whole — the
    usual case, since an adapter's reducer returns only the last message's text
    — and longer text is windowed forward from the answer's opening bracket
    (:func:`_answer_window_start`), then cut at the end with a marker charged
    against the cap. Text with no bracket keeps its head.
    """
    if len(text.encode("utf-8", errors="replace")) <= MAX_LOG_STREAM_BYTES:
        return text
    start = _answer_window_start(text)
    window = text[start:] if start is not None else text
    return _cut_bytes(
        window,
        MAX_LOG_STREAM_BYTES,
        f"\n... [salvage text truncated at {MAX_LOG_STREAM_BYTES} B]",
    )


#: Sentinel for "the caller has not read the hook yet": ``None`` is taken, it is
#: the hook's own "no opinion".
_HOOK_UNREAD: Any = object()


def _salvage_hook_text(provider: Any, stdout: Optional[str]) -> Optional[str]:
    """The adapter's :meth:`~utils.providers.base.LLMProvider.salvage_text` reading, once.

    The one place the hook's three-answer contract is read, so
    ``salvage_text`` and ``answer_text`` can never disagree about what the
    hook said, and a losing path that attaches both runs the hook once
    * the hook's string, as it returned it (``""`` included: "nothing there");
    * ``""`` when the hook raised: by overriding, the adapter declared its
      stdout a transport, so falling back to the raw stream would restore the
      bug the hook removes;
    * ``None`` for "no opinion": the base default, a provider with no callable
      hook, or a return that is not a string.
    """
    hook = getattr(provider, "salvage_text", None)
    if not callable(hook):
        return None
    try:
        text = hook(stdout or "")
    except Exception:  # noqa: BLE001 - a reducer may never break a run
        return ""
    return text if isinstance(text, str) else None


def _attach_salvage_text(
    details: Dict[str, Any],
    provider: Any,
    stdout: Optional[str],
    hook_text: Any = _HOOK_UNREAD,
) -> None:
    """Put the adapter's answer text on ``details['salvage_text']``, redacted then bounded.

    The salvage gate used to judge ``stdout_excerpt`` — the raw stream's last
    20 lines — and on a transport-stream adapter (pi, omp) those lines are
    event data whose ``content`` arrays pass ``has_salvageable_json``: a
    reviewer killed mid-tool-call was sent to salvage over its own
    ``thinking``/``toolCall`` parts. The adapter's
    :meth:`~utils.providers.base.LLMProvider.salvage_text` hook reads the
    **full** stdout, before any bounding, and says which words are the answer.

    Called beside :func:`_attach_stdout_excerpt` for the same three losing
    outcomes, and — like it — one helper so the redact-then-bound order cannot
    drift between them. What it records:

    * the hook returned a string → that string, redacted, then bounded by
      :func:`_bound_salvage_text`, **even when it is ``""``**: "present and
      empty" is the adapter's verdict that there is nothing to salvage;
    * the hook raised → ``""``: by overriding, the adapter declared its stdout
      a transport, so falling back to the raw stream would restore the bug;
    * the hook returned ``None`` (the base default, "no opinion") or anything
      that is not a string → the key stays **absent**, and the gate keeps its
      old input.

    ``hook_text`` is :func:`_salvage_hook_text`'s reading when the caller has
    already taken it (a losing path that also attaches ``answer_text`` passes
    the one reading to both); left out, this helper reads the hook itself.
    """
    if hook_text is _HOOK_UNREAD:
        hook_text = _salvage_hook_text(provider, stdout)
    if hook_text is None:
        return
    details[SALVAGE_TEXT_KEY] = _bound_salvage_text(_redact(hook_text)).strip()


#: The key :func:`_attach_answer_text` writes, and only when the caller passed
#: ``want_answer_text=True`` to :func:`invoke_with_provider` (the ask lane).
#: Its value is the model's **whole** answer text, reduced from the full stdout,
#: redacted and head-capped. It goes to that caller alone — never into
#: ``.status.json``, a result record or the log.
ANSWER_TEXT_KEY = "answer_text"

#: ``answer_text``'s cap. An answer is read from the top, so the **head** is
#: kept and a marker appended (:func:`_cut_bytes`), never the tail-bound of the
#: log nor ``_bound_salvage_text``'s bracket window (D2.2).
MAX_ANSWER_TEXT_BYTES = 1024 * 1024


def _clean_envelope_answer(value: Any, text: str) -> str:
    """Rule 2 of :func:`generic_answer_text`: a clean envelope's inner answer, else ``""``.

    Clean means one of the two measured shapes (D2.2):

    * ``{"type": "result", …}`` that
      :func:`~utils.providers.result_envelope.is_clean_envelope` passes
      (claude-code, cursor-agent): its ``result`` string;
    * ``{"response": "<string>"}`` with no ``error`` and a ``status`` that is
      absent or ``"SUCCESS"`` (gemini, agy). Without the ``status`` test an
      agy failure that carries no ``error`` would pass. An ``error`` that is
      present but empty (``null``, ``""``) says no error either: agy's success
      shape is uncaptured, and an answer lost to an empty field is the
      loss this plan fixes.

    Any other JSON value — a refusing envelope, grok's ``{"type":"error",…}``
    body, a record array, a bare number — is transport, never the answer.
    """
    if not isinstance(value, dict):
        return ""
    if value.get("type") == "result":
        if not is_clean_envelope(text):
            return ""
        inner = value.get("result")
        return inner if isinstance(inner, str) else ""
    response = value.get("response")
    if (
        isinstance(response, str)
        and not value.get("error")
        and value.get("status", "SUCCESS") == "SUCCESS"
    ):
        return response
    return ""


def generic_answer_text(
    stdout: Optional[str],
    *,
    framing: str = "auto",
    exit_zero_markers: Collection["re.Pattern[str]"] = (),
) -> str:
    """The answer text of a stdout whose adapter's hook has no opinion (D2.2).

    A conservative default, not a parser. It serves the adapters without a
    :meth:`~utils.providers.base.LLMProvider.salvage_text` hook
    (claude-code, cursor-agent, gemini, agy, kilocode) and any adapter added
    later without one. ``framing`` is the adapter's declared
    ``answer_framing``; the reducer never guesses it.

    Under ``"auto"`` the first rule that applies decides:

    1. an event stream (:func:`~utils.json_extractor.looks_like_ndjson`) → ``""``;
    2. a stdout that parses whole as one JSON value → the inner answer of a
       clean result envelope (:func:`_clean_envelope_answer`), ``""`` for any
       other JSON value: a provider's error body is never an answer;
    3. anything else is plain text: the whole stdout, ANSI escapes removed.

    Under ``"plain"`` (the stdout *is* the reply: kilocode) only rule 3 runs,
    so a direct JSON object, a JSON array or NDJSON the question asked for
    comes back whole.

    **Rule 3's exit-zero check.** Rule 3 cannot tell a prose answer from a
    prose error, and every exit-0 ``PARSE_ERROR`` may reach it (D3.1). So when
    one of the adapter's own ``exit_zero_markers`` matches the lowercased
    stdout (:func:`~utils.providers.failure_classifier._matches_marker`, as step 6 of
    ``classify_streams`` does), rule 3 gives ``""`` — on every path, success
    included, under both framings. Only the adapter's markers: the shared
    auth, rate-limit and context tables match words an answer *about* auth or
    rate limits uses. The haystack is the stdout both as captured and with its
    ANSI escapes removed, so a painted ``Error:`` still matches a marker.

    Whitespace-only text is ``""``. Text is otherwise returned as is, not
    stripped: the caller redacts and caps it.
    """
    raw = stdout or ""
    text = _ANSI_ESCAPE.sub("", raw)
    if not text.strip():
        return ""
    if framing != "plain":
        if looks_like_ndjson(text):
            return ""
        try:
            value = json.loads(text)
        except ValueError:
            pass
        else:
            answer = _clean_envelope_answer(value, text)
            return answer if answer.strip() else ""
    if exit_zero_markers and (
        _matches_marker(exit_zero_markers, raw.lower())
        or _matches_marker(exit_zero_markers, text.lower())
    ):
        return ""
    return text


def _attach_answer_text(
    details: Dict[str, Any],
    provider: Any,
    stdout: Optional[str],
    hook_text: Any = _HOOK_UNREAD,
) -> None:
    """Put the model's whole answer text on ``details['answer_text']`` (D2.2).

    Set on every :func:`invoke_with_provider` exit that ran the child — the
    success return, the exit-0 parse failure, the non-zero exit and the
    timeout — when the caller asked for it, from the **full** stdout:

    * the hook returned a string → used as is; ``""`` stays ``""``, a final
      "nothing to recover" (so does a hook that raised, and whitespace alone);
    * the hook had no opinion → :func:`generic_answer_text` under the
      adapter's ``answer_framing`` and ``exit_zero_failure_markers``.

    Then :func:`_redact` and the :data:`MAX_ANSWER_TEXT_BYTES` head-kept cap —
    nothing else. Hook text **never** goes through :func:`_bound_salvage_text`:
    its 45 KB window, forward from the first unclosed bracket, is built for a
    findings array and would cut the head off a long prose answer. The two
    keys read one hook result and each cuts its own copy, differently on
    purpose.

    ``hook_text`` is :func:`_salvage_hook_text`'s reading when the caller has
    already taken it for ``salvage_text``; left out, it is read here.
    """
    if hook_text is _HOOK_UNREAD:
        hook_text = _salvage_hook_text(provider, stdout)
    if hook_text is None:
        try:
            text = generic_answer_text(
                stdout,
                framing=getattr(provider, "answer_framing", "auto"),
                exit_zero_markers=tuple(
                    getattr(provider, "exit_zero_failure_markers", ()) or ()
                ),
            )
        except Exception:  # noqa: BLE001 - a reducer may never break a run
            text = ""
    else:
        text = hook_text
    if not text.strip():
        details[ANSWER_TEXT_KEY] = ""
        return
    details[ANSWER_TEXT_KEY] = _cut_bytes(
        _redact(text),
        MAX_ANSWER_TEXT_BYTES,
        f"\n... [answer text truncated at {MAX_ANSWER_TEXT_BYTES} B]",
    )


_READONLY_AUDIT_KEY = _readonly_audit_mod.DETAILS_KEY


def _readonly_audit(
    provider: Any, stdout: Optional[str], sandbox_fallback: Any = None,
    *, complete: bool = True, pipe_held: bool = False,
) -> Optional[Dict[str, Any]]:
    """The adapter's read-only verdict on this attempt's **full** stdout, compact.

    Only for an attempt dispatched on the uncontained rung (``sandbox_fallback``
    names ``unsandboxed``) or on the plugin's own jail (``plugin-landlock``,
    2026-09-30): the first is the one slot the porcelain check brackets, the
    second the one the mode check and the home check bracket, and both read
    this verdict to decide whether a change seen in the window is downgraded to
    a not-attributed warning. A default or contained-rung run adds no key — the same rule the D6
    ``sandbox`` provenance key follows.

 option B / 4.2: the audit must see the whole in-memory stream —
    the persisted log and ``stdout_excerpt`` are both cut at
    ``MAX_LOG_STREAM_BYTES``, and a cut stream has no ``turn.completed`` and
    would fail every long slot. So it runs here, at parse time, on every
    outcome that has a stream, before anything is bounded; only the compact
    verdict dict leaves (never the stream). ``None`` when the adapter has no
    opinion or the hook raised — a missing verdict, which
    ``readonly_audit.combine_audits`` treats as not clean.

    ``complete=False`` says the capture cut stdout at its bound
    (``process_capture``): the audit cannot see the whole stream, so the
    verdict is not clean whatever the kept head shows. *pipe_held* says a
    process the CLI started outlived it holding its output
    (``Capture.pipe_held``): what that process did is not in the stream, so
    the verdict is not clean either.
    """
    if sandbox_rung_id(sandbox_fallback) not in (
        SANDBOX_RUNG_UNSANDBOXED, *_INCIDENTAL_RUNG_IDS,
    ):
        return None
    hook = getattr(provider, "audit_readonly_stream", None)
    if hook is None:
        return None
    if not complete:
        return _readonly_audit_mod.AuditVerdict(
            False, "stdout passed the capture bound; the audit saw only its head",
        ).to_dict()
    if pipe_held:
        return _readonly_audit_mod.AuditVerdict(
            False, "a process the CLI started outlived it holding its output; "
            "the audit saw the CLI's stream, not what that process did",
        ).to_dict()
    try:
        verdict = hook(stdout or "")
    except Exception:  # noqa: BLE001 - an audit may never break a run
        return None
    if verdict is None:
        return None
    to_dict = getattr(verdict, "to_dict", None)
    if callable(to_dict):
        verdict = to_dict()
    return dict(verdict) if isinstance(verdict, dict) else None


def _attach_readonly_audit(
    details: Dict[str, Any], provider: Any, stdout: Optional[str],
    sandbox_fallback: Any = None, *, complete: bool = True,
) -> Optional[Dict[str, Any]]:
    """Put :func:`_readonly_audit`'s verdict on ``details['readonly_audit']``."""
    verdict = _readonly_audit(provider, stdout, sandbox_fallback, complete=complete)
    if verdict is not None:
        details[_READONLY_AUDIT_KEY] = verdict
    return verdict


def _attach_usage(
    details: Dict[str, Any], provider: Any, stdout: Optional[str], stderr: Optional[str]
) -> None:
    """Put what the run spent on ``details`` as ``usage``, when the adapter can say.

    The adapter's own :meth:`~utils.providers.base.LLMProvider.parse_usage`,
    under the same never-raise rule ``task_dispatch._safe_parse_usage``
    applies (D3j): metrics must not break a run, and an adapter that reports
    nothing leaves the key **absent** — a ``{}`` would read as "reported,
    free".

    Called on **every** outcome ``invoke_with_provider`` can reach — the
    non-zero exit, the timeout kill, and (Stage U) the exit-0 parse, clean or
    not. It began as a losing-paths-only helper, on the reasoning that a
    completed slot's usage was "a separate question"; it was not a separate
    question, it was the same one asked of the runs an operator is most
    likely to pay for. A successful slot's envelope was parsed for the answer
    and then discarded, so the fan-out could name what a *failed* $25 run
    spent and nothing at all about the run that succeeded beside it. The rule
    is now uniform: whatever the adapter can say about what a run spent
    travels on ``details``, whichever way the run ended.
    """
    try:
        usage = provider.parse_usage(stdout or "", stderr or "")
    except Exception:  # noqa: BLE001 - metrics must not break the run
        return
    if isinstance(usage, dict) and usage:
        details["usage"] = usage


#: ``details`` key for the adapter's own verdict on a failed child: the
#: ``classify_failure`` category of a non-zero exit, the
#: ``exit_zero_failure_category`` of an exit 0 that left no answer (absent for
#: an adapter that is not ``EXIT0_CLASSIFIABLE``), ``unparseable_result`` for a
#: capped stdout, :func:`rejected_answer_category` for a parsed answer the
#: file-output layer rejected, ``timeout`` for a deadline kill, or
#: ``runner_error`` for a stop the adapter's stdout watch asked for.
#: ``review_orchestrator_base.attempt_ladder_status`` hands it to the retry
#: ladder instead of re-classifying the error line; see
#: docs/development/delegation.md#read-and-analyze-executor.
FAILURE_CATEGORY_KEY = "failure_category"

#: ``details`` key for the reason an adapter's stdout watch stopped the child
#: (``Capture.stream_stop``, opencode's ``provider loop``); absent otherwise
#: (docs/development/providers.md#a-cli-that-loops).
STREAM_STOP_KEY = "stream_stop"

#: ``details`` key: the CLI exited while a process it started still held its
#: output, and what the sweep of that process did (``Capture.pipe_held``);
#: absent otherwise (docs/development/runtime.md#process-primitives).
PIPE_HELD_KEY = "pipe_held"


def rejected_answer_category(
    provider: Any, stdout: Optional[str], stderr: Optional[str]
) -> str:
    """The ``failure_category`` of an exit 0 whose stdout parsed, but not into
    an answer the file-output layer accepts (``invoke_with_file_output``).

    The executor's precedence for the same rejection, so the two lanes agree:
    the verdict of the one exit-0 gate (:func:`~.providers.base.
    exit_zero_failure_category`, read off the CLI's own text and stderr, never
    the answer) when it names a category, and otherwise the rejection's own
    ``unparseable_result``, one retry
    (docs/development/delegation.md#read-and-analyze-executor).
    """
    _, category = exit_zero_failure_category(provider, stdout, stderr)
    return category or STATUS_UNPARSEABLE


def _adapter_failure_category(
    provider: Any, stdout: Optional[str], stderr: Optional[str], returncode: int
) -> Tuple[bool, Optional[str]]:
    """``provider.classify_failure`` on a non-zero exit, as ``(classified, category)``.

    ``None`` from a working adapter is a verdict ("nothing recognized"), so it
    comes back as ``(True, None)``. Best-effort like ``describe_failure``: an
    adapter that raises, or answers anything but a category name or ``None``,
    gives ``(False, None)`` and the caller leaves :data:`FAILURE_CATEGORY_KEY`
    absent. Only the category leaves; the streams it was read from do not.
    """
    try:
        category = provider.classify_failure(stdout or "", stderr or "", returncode)
    except Exception:  # noqa: BLE001 - classification must not break a failure path
        return False, None
    if category is not None and not isinstance(category, str):
        return False, None
    if category == STATUS_SPAWN_FAILED:
        # A shell's `command not found` may be a hook's: the executor's rule
        # (`base.launch_refusal`), so both lanes stop or retry alike.
        category, _ = launch_refusal(provider, stdout, stderr, returncode)
    return True, category


def _served_model_attribution(
    provider: Any, model: str, stdout: str
) -> Optional[Tuple[str, bool, Optional[str]]]:
    """The ``(served_model, is_fallback, warning)`` for one attempt, or None.

    **Gated on a configured fallback list, which ships empty.** Attribution is
    mandatory *whenever a fallback is configured* — without it a report
    attributes a haiku answer to the sonnet the user asked for. With nothing
    configured there is no substitution to disclose, so nothing is parsed,
    nothing is recorded and nothing is printed: the result dict is byte-for-byte
    what it has always been.

    Only claude-code answers here (its envelope carries ``modelUsage``);
    stays closed, so every other adapter lacks both methods and returns None.

    **Read, never depended on.** Any failure to answer degrades to None — an
    attribution field never fails an otherwise-successful attempt.
    """
    resolve = getattr(provider, "resolve_served_model", None)
    configured = getattr(provider, "fallback_models", None)
    if resolve is None or configured is None:
        return None
    try:
        fallbacks = configured(model)
        if not fallbacks:
            return None
        return resolve(stdout, model, fallbacks)
    except Exception:  # noqa: BLE001 - attribution never fails a good attempt
        return None


def _note_stream_cap(details: Dict[str, Any], capped: FrozenSet[str]) -> None:
    """Name the capped streams on ``details`` (absent when none was)."""
    if capped:
        details["stream_capped"] = sorted(capped)


def _turn_failed(stdout: Optional[str]) -> bool:
    """Whether the stream holds a top-level ``turn.failed`` event."""
    for raw in (stdout or "").splitlines():
        raw = raw.strip()
        if not raw.startswith("{") or "turn.failed" not in raw:
            continue
        try:
            event = json.loads(raw)
        except ValueError:
            continue
        if isinstance(event, dict) and event.get("type") == "turn.failed":
            return True
    return False


def _exit0_left_no_answer(hook_text: Optional[str], stdout: Optional[str]) -> bool:
    """Whether a jailed child that exited 0 left no finished answer — the only
    exit 0 a jail failure is read on.

    The parse verdict is not that question: codex's ``parse_output`` succeeds
    only when it finds JSON, so a finished prose ``ask`` answer, or a review
    whose JSON failed to parse for another reason, reads as failed. The answer
    is the adapter's own final answer text (``hook_text``, the
    :func:`_salvage_hook_text` reading — codex's last ``agent_message``), and a
    ``turn.failed`` event means the turn never finished, whatever narration
    came before it.
    """
    answered = isinstance(hook_text, str) and bool(hook_text.strip())
    return not answered or _turn_failed(stdout)


# ---------------------------------------------------------------------------
# The reading itself
# ---------------------------------------------------------------------------


def _launch_failure(capture: Capture, provider_name: str, model: str) -> Dict[str, Any]:
    """The result of a CLI that could not be started: nothing ran, so no key a
    child that ran carries."""
    # Process creation failed (executable removed after detection, an invalid
    # resolved shim, or any other CreateProcess/exec failure): a structured
    # error through the same result-dict path as other provider errors instead
    # of aborting the orchestrator.
    if capture.launch_not_found:
        error_code = ERROR_BINARY_NOT_FOUND
        error = f"{provider_name} CLI not found when launching: {capture.launch_error}"
    else:
        error_code = ERROR_SUBPROCESS_FAILED
        error = f"Failed to launch {provider_name} CLI: {capture.launch_error}"
    return {
        "success": False,
        "error": error,
        "error_code": error_code,
        "details": {
            "provider": provider_name,
            "model": model,
            "duration_seconds": capture.duration,
        },
    }


def _sandbox_hint_line(provider: Any, stderr: str) -> Optional[str]:
    """``base.sandbox_hint`` over the stderr the adapter's CLI wrote, redacted.

    A message only, never a verdict: a bubblewrap line that is none of the
    measured refusals does not stop the slot, but the reader still learns
    the runner's own sandbox may not have started
    (docs/development/providers.md#launch-diagnostics).
    """
    try:
        hint = sandbox_hint(provider.launch_diagnostics(stderr or ""))
    except Exception:  # noqa: BLE001 - diagnostics must not raise
        return None
    return _redact(hint) if hint else None


def _exit_line(provider: Any, provider_name: str, capture: Capture) -> str:
    """A non-zero exit's error line, before the jail and the category tag."""
    line = f"{provider_name} exited with code {capture.exit_code}"
    # Some CLIs report the actual cause on stdout and leave stderr empty
    # (opencode does this for auth/quota errors), which would otherwise leave
    # the caller with a bare exit code. A provider override must never mask the
    # real failure, so it is best-effort.
    try:
        reason = provider.describe_failure(capture.stdout, capture.stderr)
    except Exception:  # noqa: BLE001 - diagnostics must not raise
        reason = None
    if reason:
        # The reason is the vendor's own sentence quoted off a stream, and
        # it lands in `.status.json`'s `models_failed` and on the fan-out's
        # stdout — neither of which goes through `_save_log`'s redaction. The
        # one boundary applies here too.
        line = f"{line}: {_redact(reason)}"
    # M10 — the **status**-consumer half of this site. A failure whose
    # own streams carry a login notice is an availability verdict, not a parse,
    # so name it instead of leaving the caller with a generic tail. Only the
    # named negatives speak (see `availability_from_failure`), and nothing is
    # probed here.
    unavailable = availability_from_failure(
        provider, capture.stdout, capture.stderr, capture.exit_code
    )
    if unavailable is not None:
        line = f"{line} [{unavailable.value}]"
    return line


def _parse_exit_zero(provider: Any, provider_name: str, capture: Capture) -> Dict[str, Any]:
    """The adapter's ``parse_output`` of an exit 0, or the refusal of a capped
    stdout.

    A stdout cut at the capture bound is refused unparsed, and its head is
    never a finished answer: it is ``incomplete``, so ask keeps it as partial
    evidence only.
    """
    if "stdout" in capture.capped_streams:
        return {
            "success": False,
            "error": f"{provider_name}: " + process_capture.oversized_stream_message(
                "stdout", capture.stream_bound),
            "data": None,
            "incomplete": True,
        }
    return provider.parse_output(capture.stdout, capture.stderr)


def _schema_verdict(
    result: Dict[str, Any],
    details: Dict[str, Any],
    *,
    provider: Any,
    provider_name: str,
    model: str,
    capture: Capture,
    schema: Any,
    schema_phase: str,
    structured_marker: str,
) -> Dict[str, Any]:
    """The verdict on a dispatch that carried a phase schema; returns the
    result, replaced when an exit 0 fails it.

    Lane A only, and no production caller passes ``schema_phase`` (W1, deferred
    by the repository owner; see ``invoke_with_provider``'s docstring), so
    ``tests/test_structured_output.py`` is its standing check.
    """
    if capture.exit_code != 0:
        #  cases 2 and 4 both arrive here as a non-zero exit, and they
        # are NOT the same failure: the CLI exhausting its own structured-output
        # budget is a `schema_violation` our ladder must not re-run, while a
        # malformed schema is a configuration error that made **zero requests**
        # and cost nothing. Classifying here is what keeps the second from
        # being retried as if it were transient.
        verdict = structured_output.classify_attempt(
            schema,
            stdout=capture.stdout,
            stderr=capture.stderr,
            exit_code=capture.exit_code,
            phase=schema_phase,
            model=f"{provider_name}:{model}",
        )
        if (
            verdict.failure_reason
            and details.get("failure_reason") != FAILURE_JAIL_DENIED
        ):
            details["failure_reason"] = verdict.failure_reason
            details["retryable"] = verdict.retryable
        if verdict.warning:
            print(f"[WARN] {verdict.warning}", file=sys.stderr)
        return result

    # The rule, stated as a rule and not only as a case: **no** combination
    # of exit 0, `subtype: success` and `is_error: false` is by itself a success
    # for a schema-carrying phase. The only success is `structured_output`
    # present (→ `native`) or a recovered document that validates against the
    # SAME schema file (→ `recovered`, one WARN). Anything else is
    # `schema_violation`, handed to the retry ladder like any other parse
    # failure. Applied here, on the parsed envelope, so no adapter can silently
    # upgrade prose to validated output. A capped stdout is refused before this
    # and never recovered here.
    verdict = structured_output.classify_attempt(
        schema,
        stdout=capture.stdout,
        stderr=capture.stderr,
        exit_code=capture.exit_code,
        phase=schema_phase,
        model=f"{provider_name}:{model}",
        native_document=structured_output.native_document_for(
            provider, capture.stdout
        ),
    )
    if verdict.warning:
        print(f"[WARN] {verdict.warning}", file=sys.stderr)
    if verdict.failure_reason:
        return {
            "success": False,
            "error": (
                f"{provider_name} returned no schema-conformant document "
                f"for {schema_phase} ({verdict.failure_reason})"
            ),
            "error_code": ERROR_PARSE_ERROR,
            "data": None,
            "details": {
                **result.get("details", {}),
                "failure_reason": verdict.failure_reason,
                "retryable": verdict.retryable,
                "structured_output": None,
            },
        }
    details["structured_output"] = verdict.marker or structured_marker
    if verdict.data is not None:
        result["success"] = True
        result["data"] = verdict.data
    return result


def outcome_from_capture(
    provider: Any,
    capture: Capture,
    *,
    provider_name: str,
    model: str,
    timeout: Any = None,
    sandbox_fallback: Any = None,
    want_answer_text: bool = False,
    schema: Any = None,
    schema_phase: Optional[str] = None,
    structured_marker: str = structured_output.MARKER_UNVALIDATED,
    jail: Optional[JailReadBack] = None,
    defer_log: bool = False,
    log: Optional[LogWriter] = None,
) -> Dict[str, Any]:
    """The result ``invoke_with_provider`` returns for ``capture``.

    ``provider`` is the adapter, ``provider_name`` and ``model`` the two halves
    of the spec; ``timeout`` is the deadline a timeout's line names. The other
    arguments are ``invoke_with_provider``'s and mean what its docstring says:
    ``sandbox_fallback`` (the D6 rung, recorded as ``details["sandbox"]`` and
    deciding the read-only audit), ``want_answer_text`` (the ask lane's
    ``details["answer_text"]``), ``schema``/``schema_phase``/
    ``structured_marker``, ``jail`` (the plugin's jail
    read-back, :data:`JailReadBack`), ``defer_log`` (an exit 0 hands its
    capture back on ``details["_deferred_log"]`` instead of being logged) and
    ``log`` (the provider log's writer, :data:`LogWriter`).

    Every child that ran gets the same keys, from the same helpers, in the
    order each path has always had them; a key the reading has nothing for is
    **absent**, never empty. The full stream is read before anything bounds
    it (the read-only audit, the salvage and answer hooks, usage), and every
    stream text that leaves is redacted before it is cut. A jail denial
    decides the slot over any category. The reading writes nothing itself:
    ``log`` is called once its result has what the log records, before the
    rest of the reading (docs/development/providers.md#reading-a-capture).
    """
    if capture.launch_error is not None:
        result = _launch_failure(capture, provider_name, model)
        if log is not None:
            log(capture, result)
        return result

    stdout, stderr = capture.stdout, capture.stderr
    capped = capture.capped_streams
    timed_out = capture.timed_out
    exited_nonzero = not timed_out and capture.exit_code != 0
    exited_zero = not timed_out and not exited_nonzero

    # How the run ended: the result's first keys, the error line before the
    # jail has read the run back, and the failure category.
    if timed_out:
        stop = capture.stream_stop
        if stop:
            error_line = process_capture.stopped_early_text(
                stop, capture.duration, f"its {timeout}s timeout" if timeout else "its timeout",
            )
        else:
            error_line = f"{provider_name} timed out after {timeout}s"
        if capture.pipe_held:
            # The CLI exited, but what held its output could not be confirmed
            # stopped: the timeout it was at the base, saying why.
            error_line = f"{error_line}: {capture.pipe_held}"
        details: Dict[str, Any] = {
            "provider": provider_name,
            "model": model,
            "timeout": timeout,
            "duration_seconds": capture.duration,
        }
        if stop:
            details[STREAM_STOP_KEY] = stop
        result: Dict[str, Any] = {
            "success": False,
            "error": error_line,
            "error_code": ERROR_TIMEOUT,
            "details": details,
        }
        # A deadline kill is a timeout whatever the partial streams say, as on
        # the executor lane (`_classify_pre_parse`), so the adapter is not asked.
        # A stop the adapter's stdout watch asked for is `runner_error`: the
        # CLI looped, it did not run out of time. `details["stream_stop"]` is
        # what tells the ladder not to send it again. `ERROR_TIMEOUT` stays,
        # since the plugin cut the run short, so a salvaged `[]` from it is
        # refused as from a deadline kill
        # (docs/development/providers.md#a-cli-that-loops).
        classified, category = True, (STATUS_RUNNER_ERROR if stop else STATUS_TIMEOUT)
    elif exited_nonzero:
        error_line = _exit_line(provider, provider_name, capture)
        # The adapter's own verdict, read while the streams are held. The
        # fan-out's retry ladder takes it from `details`, and the error line
        # names it so `.status.json` says why the slot stopped or retried.
        classified, category = _adapter_failure_category(
            provider, stdout, stderr, capture.exit_code
        )
        details = {
            "exit_code": capture.exit_code,
            "stderr": stderr,
            "provider": provider_name,
            "model": model,
            "duration_seconds": capture.duration,
        }
        result = {
            "success": False,
            "error": error_line,
            "error_code": ERROR_SUBPROCESS_FAILED,
            "details": details,
        }
    else:
        result = _parse_exit_zero(provider, provider_name, capture)
        details = result["details"] = {
            "provider": provider_name,
            "model": model,
            "duration_seconds": capture.duration,
        }
        # The adapter's completion verdict moves onto `details` straight after
        # the parse:
        # `incomplete` says the stream's own terminal state shows the answer did
        # not finish (pi's `stopReason: "length"`), or that the capture cut
        # stdout at its bound, whether or not the text parsed. It is not an
        # `error_code`, so `invoke_with_file_output`'s hard-failure gate — and
        # with it the findings-file channel — is unchanged.
        if result.pop("incomplete", False):
            details["incomplete"] = True
        # EXTRACT BEFORE DISCARDING: `parse_output` has just unwrapped the
        # answer and thrown the envelope away, and the envelope is where the
        # token counts and the catalog cost live. An exit 0 asks right where
        # `details` is born (Stage U), a failed child at the end of the tail;
        # each keeps the place in `details` it has always had.
        _attach_usage(details, provider, stdout, stderr)
        if "stdout" in capped:
            # The executor's rung for a capped stdout, so the fan-out's ladder
            # retries it as the executor does (`process_capture`).
            classified, category = True, STATUS_UNPARSEABLE
        elif result.get("success", False):
            classified, category = False, None
        else:
            # An exit 0 with no answer: the adapter's own verdict, read while
            # the streams are held, and only from what the CLI wrote — an
            # adapter that cannot tell that from the answer gives none
            # (`EXIT0_CLASSIFIABLE`). The file channel may still answer for
            # the run, and then the fan-out never asks.
            classified, category = exit_zero_failure_category(
                provider, stdout, stderr
            )

    # F1: the jailed slot's read-back samples live state (the
    # home, other children still running), so it is taken where each path has
    # always taken it: a non-zero exit's here, before the audit, its keys held
    # back so they land after the `sandbox` word as on the other paths; the
    # others' after the exit-zero verdicts below.
    hook_text: Any = _HOOK_UNREAD
    jail_error: Optional[str] = None
    jail_note = ""
    jail_details: Dict[str, Any] = {}
    if jail is not None and exited_nonzero:
        jail_error, jail_note = jail(
            jail_details, stdout=stdout, stderr=stderr,
            returncode=capture.exit_code, failed=True, timed_out=False,
        )

    # The read-only verdict on the FULL stream, before anything
    # below bounds it — a failed attempt of a bypassed slot could still have
    # written, and 4.3 ANDs every attempt's verdict. A capped stdout's audit is
    # never clean (`process_capture`).
    audit = _readonly_audit(
        provider, stdout, sandbox_fallback, complete="stdout" not in capped,
        pipe_held=bool(capture.pipe_held),
    )
    if audit is not None:
        details[_READONLY_AUDIT_KEY] = audit
    if capture.pipe_held:
        details[PIPE_HELD_KEY] = capture.pipe_held
    _note_stream_cap(details, capped)
    if classified:
        details[FAILURE_CATEGORY_KEY] = category
    # D6 override: the child ran, whatever it returned, under the
    # rung it was given, so the provenance rides every outcome that ran one.
    _attach_sandbox_word(details, sandbox_fallback)
    details.update(jail_details)

    if exited_zero:
        # A fallback that fired rides out on the same details dict the
        # provider/model pair travels on, so every downstream record that names
        # the requested model can name the model that actually served the turn.
        # One WARN per slot — the adapter owns the text; there is no second one.
        attribution = _served_model_attribution(provider, model, stdout)
        if attribution is not None:
            served, is_fallback, warning = attribution
            details["served_model"] = served
            details["served_model_is_fallback"] = is_fallback
            if warning:
                print(f"[WARN] {warning}", file=sys.stderr)
        if schema_phase and "stdout" not in capped:
            result = _schema_verdict(
                result, details, provider=provider, provider_name=provider_name,
                model=model, capture=capture, schema=schema,
                schema_phase=schema_phase, structured_marker=structured_marker,
            )
            details = result["details"]
        if not result.get("success", False) and "error_code" not in result:
            result["error_code"] = ERROR_PARSE_ERROR

    # F1: the jailed slot's read-back, on every outcome that ran a
    # child — the home check and the in-stream denial count always; a jail
    # failure only on a failed attempt. A deadline kill stays a timeout, as on
    # the executor lane. An exit 0 is failed only when the run produced no
    # answer (a `turn.failed` on a codex-internal EACCES can still exit 0), by
    # `_exit0_left_no_answer`'s reading, not the parse verdict: codex's
    # `parse_output` succeeds only on JSON, so a finished prose answer would
    # otherwise be rewritten as jail-denied. Such a failure is a hard one
    # (`SUBPROCESS_FAILED`), so `invoke_with_file_output` returns it as it is.
    # A non-zero exit was read back before the audit, above.
    if jail is not None and not exited_nonzero:
        failed = True
        if exited_zero:
            failed = not result.get("success", False)
            if failed:
                hook_text = _salvage_hook_text(provider, stdout)
                failed = _exit0_left_no_answer(hook_text, stdout)
        jail_error, jail_note = jail(
            details, stdout=stdout, stderr=stderr,
            returncode=None if timed_out else capture.exit_code,
            failed=failed, timed_out=timed_out,
        )
    if timed_out:
        if jail_error:
            result["error"] = f"{error_line}: {jail_error}"
        elif jail_note:
            result["error"] = f"{error_line}{jail_note}"
    elif exited_nonzero:
        # A jailed child that died on a codex-internal EACCES the jail caused
        # is a jail failure, never a model error; an ordinary permission error
        # keeps the line plus the reason it is not a jail denial.
        if jail_error:
            result["error"] = (
                f"{provider_name} exited with code {capture.exit_code}: {jail_error}"
            )
        elif jail_note:
            result["error"] = f"{error_line}{jail_note}"
        # A bubblewrap line no measured refusal matched keeps its verdict, and
        # the line still points at `doctor` (`_sandbox_hint_line`), ahead of
        # the category tag, which ends the line.
        hint = None if jail_error or category == CATEGORY_SANDBOX_UNAVAILABLE else (
            _sandbox_hint_line(provider, stderr)
        )
        if hint:
            result["error"] = f"{result['error']} ({hint})"
        # A jail denial replaces the line and decides the slot on its own, so
        # it carries no category tag.
        if category and not jail_error:
            result["error"] = f"{result['error']} [{category}]"
    elif jail_error:
        result["success"] = False
        result["error"] = f"{provider_name}: {jail_error}"
        result["error_code"] = ERROR_SUBPROCESS_FAILED
    elif jail_note and result.get("error"):
        result["error"] = f"{result['error']}{jail_note}"

    # A hard failure's log, once its error line and audit are final and before
    # anything below reads its streams again, so a reading that raises later
    # still leaves the log. An exit 0's waits for its salvage, below.
    if not exited_zero and log is not None:
        log(capture, result)

    # What the model actually said, kept on every failure, redacted then
    # bounded — never the raw stream. A non-zero exit or a kill may
    # come after the answer was written (a truncated array, a crash on
    # teardown), and a JSON-erroring CLI puts its failure body on stdout with
    # stderr empty; an exit-0 parse failure's error describes our
    # disappointment, not the event. One hook reading serves `salvage_text`
    # and `answer_text`; the jail read-back above may already have taken it.
    if not exited_zero or not result.get("success", False):
        _attach_stdout_excerpt(details, stdout)
        if hook_text is _HOOK_UNREAD:
            hook_text = _salvage_hook_text(provider, stdout)
        _attach_salvage_text(details, provider, stdout, hook_text=hook_text)

    # §Fix1/F13: a deferring caller (`invoke_with_file_output`) gets an exit
    # 0's raw capture here instead of a log written now, on every exit-0
    # outcome, because only it knows which channel (file, stdout fallback, or
    # neither) answers for the run, and that is what `Result source:` names.
    # Any other exit 0 is logged here, before its answer text is read.
    if exited_zero and defer_log:
        details["_deferred_log"] = {
            "stdout": stdout,
            "stderr": stderr,
            "returncode": capture.exit_code,
            "duration_seconds": capture.duration,
        }
    elif exited_zero and log is not None:
        log(capture, result)

    # D2.2: the whole answer, on every outcome that ran the child, success
    # included — the path nemotron's 124-line answer was lost on.
    if want_answer_text:
        _attach_answer_text(details, provider, stdout, hook_text=hook_text)

    if not exited_zero:
        # A failed run still spent what its envelope records — a killed one
        # what it streamed before the kill; absent rather than `{}` when the
        # adapter can say nothing.
        _attach_usage(details, provider, stdout, stderr)
        if exited_nonzero and schema_phase:
            result = _schema_verdict(
                result, details, provider=provider, provider_name=provider_name,
                model=model, capture=capture, schema=schema,
                schema_phase=schema_phase, structured_marker=structured_marker,
            )
    return result
