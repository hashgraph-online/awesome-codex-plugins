"""Which D3k rung one attempt lands on, read from its capture.

:func:`_classify_pre_parse` (rungs 1 and 2: the runner never started, or
timed out, with a kill that may not be confirmed),
:func:`_parse_and_validate` and :func:`_parse_with_schema_policy`
(rungs 3 to 6, through the adapter's ``parse_output``, and the schema
leg), :func:`_reply_text` (the runner's own words, for a re-ask) and
:func:`_classify_failed_run` (a rate limit, a login, a model or the
context length, read from the streams of a run that produced nothing
usable), which quotes what decided it through :func:`_quote_verdict`,
redacted first. Nothing here spawns.

``utils.subagent_executor`` re-exports every name defined here for reading
only: patch one here, never through the executor
(docs/development/delegation.md#where-the-executors-helpers-live).
"""

from __future__ import annotations

import json
import sys
from typing import Any, List, Optional, Tuple

from . import structured_output
from .json_extractor import describe_syntax_error
from .providers.base import (
    context_length_message,
    exit_zero_failure_category,
    launch_refusal,
    match_streams,
    sandbox_hint,
)
from .retry_ladder import (
    STATUS_AUTH_FAILED,
    STATUS_BUDGET_EXHAUSTED,
    STATUS_CONTEXT_LENGTH_EXCEEDED,
    STATUS_INVALID_MODEL,
    STATUS_OK,
    STATUS_RATE_LIMITED,
    STATUS_REJECTED,
    STATUS_RUNNER_ERROR,
    STATUS_SALVAGE_UNRECOVERABLE,
    STATUS_SANDBOX_UNAVAILABLE,
    STATUS_SCHEMA_INVALID,
    STATUS_SPAWN_FAILED,
    STATUS_TIMEOUT,
)
from . import task_outcome as _task_outcome
from . import task_result as _task_result
from . import runner_selection as _runner_selection
from . import dispatch_spawn as _dispatch_spawn
from . import process_capture
from . import process_control
from .redact import _REDACTIONS, _replace_group, redact_text


def _classify_pre_parse(capture: _dispatch_spawn._Capture) -> Tuple[str, str]:
    """Ladder rungs 1–2, decidable without parsing anything (D3k).

    ``STATUS_OK`` here means only "the child ran to completion"; rungs 3–6 need
    the parse result, because telling a rate limit from "no text at all" from
    "text with no result object" is exactly what the streams say.
    """
    if capture.launch_error is not None:
        return STATUS_SPAWN_FAILED, (
            f"could not start the runner: {capture.launch_error}. Either the CLI "
            f"is missing/not executable, or the host sandbox denied the spawn."
        )
    if capture.timed_out:
        # The pid is set once the executor's own timeout kill was made; Lane
        # A's shared `Capture` makes none.
        pid = getattr(capture, "kill_pid", None)
        verdict = getattr(capture, "kill_verdict", None)
        reason = process_control.unconfirmed_kill(verdict) if pid is not None else None
        # A stop the adapter's stdout watch asked for (a CLI that loops instead
        # of exiting) is the fan-out's verdict too: `runner_error`, never "ran
        # out of time", and the ladder sends it no identical retry
        # (docs/development/providers.md#a-cli-that-loops).
        stop = getattr(capture, "stream_stop", None)
        if stop:
            line = process_capture.stopped_early_text(
                stop, getattr(capture, "duration", 0.0) or 0.0, "its per-task timeout",
            )
            if reason is not None:
                line += (f"; it could not be confirmed stopped (kill verdict {verdict}, "
                         f"pid {pid}): {reason}, so it may still be running")
            return STATUS_RUNNER_ERROR, line
        if reason is not None:
            return STATUS_TIMEOUT, (
                f"the runner exceeded its per-task timeout and could not be "
                f"confirmed stopped (kill verdict {verdict}, pid {pid}): {reason}, "
                "so it may still be running; no partial result file exists "
                "(executor writes are atomic)"
            )
        return STATUS_TIMEOUT, (
            "the runner exceeded its per-task timeout and was killed; no partial "
            "result file exists (executor writes are atomic)"
        )
    return STATUS_OK, ""


def _reply_text(provider: Any, stdout: str) -> Optional[str]:
    """The runner's own reply text, or ``None`` when there is none to quote.

    The adapter's :meth:`salvage_text` when it has an opinion (the assistant's
    own words, never tool output or event framing); else the ``result`` string
    of a one-object result envelope; else the stream itself, which for a CLI
    that prints its answer as plain text is the reply. Never raises.
    """
    try:
        text = provider.salvage_text(stdout or "")
    except Exception:  # noqa: BLE001 - a diagnosis must never fail a dispatch
        text = None
    if isinstance(text, str):
        return text if text.strip() else None
    body = (stdout or "").strip()
    if body.startswith("{"):
        try:
            envelope = json.loads(body)
        except json.JSONDecodeError:
            envelope = None
        if isinstance(envelope, dict) and isinstance(envelope.get("result"), str):
            return envelope["result"] if envelope["result"].strip() else None
    return body or None


def _parse_and_validate(
    provider: Any,
    capture: _dispatch_spawn._Capture,
    *,
    kind: str,
    prefer_arrays: bool,
    failure: Optional[str] = None,
) -> Tuple[str, str, Any]:
    """Ladder rungs 4–6, plus the two ways a salvage answers with no answer.

    Returns ``(status, error, data)``. Every caller persists ``data`` only on
    ``STATUS_OK``, which is what makes this the place to recognise a salvage that
    recovered nothing: :func:`_salvage_gave_up` runs between extraction and
    validation, so both the ``salvage_failed`` sentinel and a reply that is not
    answer-shaped at all — the provider error a subagent faithfully pulled out of
    a truncated stream — leave here as failures, and no invented review is ever
    written over the model's result file. Its status is not a rung — the
    dispatch itself worked (see ``STATUS_SALVAGE_UNRECOVERABLE``) — and it is in
    none of the ladder's policy sets, so ``record()`` files it under "never
    retried": the same raw output through the same prompt has the same answer.
    """
    try:
        data, fragment = _task_result._extract_result_and_syntax(
            provider, capture.stdout, capture.stderr, prefer_arrays=prefer_arrays,
            kind=kind, capped="stdout" in getattr(capture, "capped_streams", ()),
        )
    except _task_outcome.ResultRejected as exc:
        return exc.status, exc.message, None
    gave_up = _task_result._salvage_gave_up(kind, data, failure)
    if gave_up is not None:
        return STATUS_SALVAGE_UNRECOVERABLE, gave_up, data
    _task_result._report_normalized(
        kind, _task_result.normalize_result(kind, data), _task_result.supply_result_version(kind, data))
    errors = _task_result.validate_result(kind, data)
    if errors:
        syntax = redact_text(describe_syntax_error(fragment)) if fragment else None
        capture.reply_syntax_error = syntax
        if syntax:
            # The errors are the fragment's, not the reply's: say so first
            # (2026-10-05, a task-generation reply with the right keys was
            # reported "missing schema_version" over one unescaped quote).
            return (
                STATUS_SCHEMA_INVALID,
                f"the reply is not valid JSON ({syntax}); only a fragment of "
                f"it could be read, and that fragment does not match the "
                f"{kind} result shape: " + "; ".join(errors[:5]),
                data,
            )
        return (
            STATUS_SCHEMA_INVALID,
            f"the extracted result does not match the {kind} result shape: "
            + "; ".join(errors[:5]),
            data,
        )
    return STATUS_OK, "", data


def _parse_with_schema_policy(
    provider: Any,
    capture: _dispatch_spawn._Capture,
    *,
    kind: str,
    prefer_arrays: bool,
    schema: Optional[Any] = None,
    schema_phase: str = "",
    model: str = "",
    declined_marker: Optional[str] = None,
    failure: Optional[str] = None,
) -> Tuple[str, str, Any, Optional[str]]:
    """:func:`_parse_and_validate` plus §4.2.1, when a schema was really carried.

    Returns ``(status, error, data, marker)``. ``marker`` is set **only** when a
    document was produced, so a report row never claims a path for a dispatch
    that produced nothing.

    ``schema=None`` — every kind with no schema phase, and every adapter that
    declined the flag — returns exactly what :func:`_parse_and_validate` returns,
    so this lane is byte-identical to its pre-M7 self and nothing new can fail a
    dispatch. ``declined_marker`` is what ``schema_for_dispatch`` already decided
    for the declining half of that case (``recovered``/``unvalidated``, never
    ``native``) and is ``None`` for a kind that resolved no phase at all — which
    is why such a kind's report row grows no key.

    With a schema, ``structured_output.classify_attempt`` (the one policy object
    both lanes share) reads the captured streams and its verdict is translated
    into D3k rungs:

    * a **configuration error** — the CLI refused the schema *before making any
      request* — is rung 7 (``rejected``): never retried, nothing billed. It
      must not be allowed to land on rungs 4/5, which **are** retried: re-running
      a refusal that made zero requests spends the transport budget on an
      identical failure and reports it as if it were transient.
    * the CLI's **own exhausted structured-output budget**
      (``error_max_structured_output_retries``) is rung 6 (``schema_invalid``):
      never retried here, because the CLI already spent the budget §4.2.1
      pinned, and rung 6 is this lane's existing "deterministic disagreement"
      rung.
    * ``structured_output`` **present and conformant** is the answer. It is taken
      as the result rather than re-derived from prose, and still passes through
      the kind's own :func:`validate_result` — the CLI validates client-side, so
      a disagreement here should be unreachable and is treated as case 2's
      failure rather than trusted.
    * anything else falls through to **this lane's own** extraction, which *is*
      §4.2.1 case 2 performed against the same schema file:
      :func:`validate_result` resolves to the file ``PHASE_SCHEMA_FILE`` names
      for exactly the kinds :data:`SCHEMA_PHASE_BY_KIND` lists. It is preferred
      over ``classify_attempt``'s own recovery because it runs the mandatory
      ``parse_output``-before-extraction ordering (D3) and the kind's own
      ``prefer_arrays``, neither of which a lane-agnostic policy function can
      know — and because failing a document *this* extractor would have accepted
      would be a regression dressed as a policy. Fail-closed is preserved
      either way: a document that does not validate is rung 5/6 exactly as
      before, so exit 0 is never on its own a success for a schema-carrying
      dispatch.
    """
    # A stdout the capture cut at its bound is refused at rung 5 unread: its
    # head is never a native document either (`process_capture`).
    if schema is None or "stdout" in getattr(capture, "capped_streams", ()):
        status, error, data = _parse_and_validate(
            provider, capture, kind=kind, prefer_arrays=prefer_arrays,
            failure=failure,
        )
        return (
            status, error, data,
            declined_marker if status == STATUS_OK else None,
        )

    # The native document is completed before it is validated, as this lane's
    # own parse is: a reply that left out a required-but-nullable key is
    # native, not "present but did not validate" (fix round 8).
    native_notes: List[str] = []
    verdict = structured_output.classify_attempt(
        schema,
        stdout=capture.stdout,
        stderr=capture.stderr,
        exit_code=capture.exit_code,
        phase=schema_phase,
        model=model,
        native_document=structured_output.native_document_for(
            provider, capture.stdout
        ),
        normalize=lambda document: native_notes.extend(
            _task_result.normalize_result(kind, document)
        ),
    )
    if verdict.warning:
        print(f"[WARN] {verdict.warning}", file=sys.stderr)
    if verdict.failure_reason == structured_output.FAILURE_CONFIG_ERROR:
        return STATUS_REJECTED, verdict.warning or (
            f"structured output: the CLI refused {schema.name}"
        ), None, None
    if (
        verdict.failure_reason == structured_output.FAILURE_SCHEMA_VIOLATION
        and not verdict.retryable
    ):
        return STATUS_SCHEMA_INVALID, verdict.warning or (
            f"structured output: no document conforming to {schema.name}"
        ), None, None
    if verdict.marker == structured_output.MARKER_NATIVE and verdict.data is not None:
        _task_result._report_normalized(kind, native_notes + _task_result.normalize_result(kind, verdict.data))
        errors = _task_result.validate_result(kind, verdict.data)
        if errors:
            return (
                STATUS_SCHEMA_INVALID,
                f"the CLI's own structured_output does not match the {kind} "
                f"result shape: " + "; ".join(errors[:5]),
                verdict.data,
                None,
            )
        return STATUS_OK, "", verdict.data, structured_output.MARKER_NATIVE

    status, error, data = _parse_and_validate(
        provider, capture, kind=kind, prefer_arrays=prefer_arrays,
        failure=failure,
    )
    if status == STATUS_OK:
        if not verdict.warning:
            # §4.2.1 wants one WARN whenever a document was recovered rather than
            # handed over natively. `classify_attempt` prints its own when *its*
            # recovery succeeded; this covers the case where only this lane's
            # extractor got there, so a recovered result always says so.
            print(
                f"[WARN] structured output: no `structured_output` key "
                f"({schema_phase} {model}); the document was recovered from the "
                f"reply and validated against {schema.name}. Marked "
                f"'{structured_output.MARKER_RECOVERED}'.",
                file=sys.stderr,
            )
        return status, error, data, structured_output.MARKER_RECOVERED
    return status, error, data, None


#: The cap on the text a forwarded verdict quotes (§4.5.3's exit-3 sink).
_VERDICT_QUOTE_CHARS = 2000
#: How much of that window sits before the matched text: enough to show what
#: led up to it, with the rest of the window after it.
_VERDICT_QUOTE_LEAD = 400


def _redact_tracking(text: str, offset: int) -> Tuple[str, int]:
    """``redact_text(text)`` plus where ``offset`` lands in the redacted text.

    The redacted text is always ``redact_text`` of the **unmodified** stream:
    nothing is inserted into it to carry the position, because any inserted
    character can split a credential so that no redaction pattern recognizes it
    (a marker inserted into the middle of a bearer-token credential left the
    part after the marker unredacted). The position is carried alongside instead, by
    replaying ``write_safety``'s own passes and shifting it by each
    replacement's length change; an offset inside a redacted span moves to the
    span's start. Should the replay ever disagree with ``redact_text``, the
    position falls back to the redacted length of the prefix — the returned
    text is still the canonical redaction, so only the window's placement can
    be off, never what it contains.
    """
    redacted = redact_text(text)
    offset = min(max(0, offset), len(text))
    try:
        out, pos = text or "", offset
        if out:
            for _name, pattern, group, predicate in _REDACTIONS:
                pieces: List[str] = []
                last = 0
                new_pos = pos
                for m in pattern.finditer(out):
                    if predicate is not None and not predicate(m.group(group)):
                        continue
                    repl = _replace_group(m, group, _name)
                    start, end = m.span()
                    pieces.append(out[last:start])
                    pieces.append(repl)
                    last = end
                    if end <= pos:
                        new_pos += len(repl) - (end - start)
                    elif start < pos:
                        new_pos -= pos - start
                pieces.append(out[last:])
                out, pos = "".join(pieces), new_pos
        if out == redacted:
            return redacted, min(max(0, pos), len(redacted))
    except Exception:  # noqa: BLE001 - the quote must never raise
        pass
    return redacted, min(len(redact_text(text[:offset])), len(redacted))


def _unlowered_offset(text: str, lowered_offset: int) -> int:
    """Map an index into ``text.lower()`` back to an index into ``text``.

    :func:`match_streams` reports offsets into the channel's lowered text, and
    ``str.lower()`` is not length-preserving for every character (U+0130
    lowers to two code points), so the raw offset can drift from the original
    stream. Lowering is applied per character here, which sums to the same
    length as lowering the whole string; an offset that lands inside one
    character's expansion maps to that character.
    """
    lowered_offset = max(0, lowered_offset)
    if len(text.lower()) == len(text):
        return min(lowered_offset, len(text))
    consumed = 0
    for index, char in enumerate(text):
        width = len(char.lower())
        if consumed + width > lowered_offset:
            return index
        consumed += width
    return len(text)


def _quote_verdict(
    provider: Any, stdout: str, stderr: str, exit_code: int, classified: str
) -> str:
    """The redacted text around what decided ``classified`` (T2.5).

    The verdict is ``provider.classify_failure``'s and nothing here changes it.
    ``stdout``/``stderr`` arrive already reduced by the adapter's own
    ``vendor_text`` — applied by :func:`_classify_failed_run`, the one
    permitted second application of that hook, see its docstring — and
    :func:`match_streams` re-scans the reduced text with the adapter's
    declared tables, for the quote only. When the re-scan lands on the same status
    with a pattern, the quote is the window around that match on the channel
    it matched; otherwise (an adapter's structural override decided a verdict
    no pattern produced, or the re-scan found another status) it is the head of
    the reduced ``stdout + "\n" + stderr``, never a pattern match that did not
    decide the verdict.

    Before this, the quote was ``stderr or stdout``: run b38de8bb recorded
    ``rate_limited`` off a ``rate limit`` in opencode's stdout and quoted a
    stderr line that said nothing of the kind.

    Redaction runs on the whole reduced channel **before** the window is cut,
    for the reason ``failure_capture._tail`` gives; the match position is carried beside it by
    :func:`_redact_tracking`, never by a character inserted into the stream.
    """
    match = None
    try:
        launch = getattr(provider, "launch_diagnostics", None)
        match = match_streams(
            stdout or "",
            stderr or "",
            exit_code or 0,
            auth_patterns=getattr(provider, "auth_error_patterns", None),
            rate_limit_patterns=getattr(provider, "rate_limit_patterns", None),
            exit_zero_markers=getattr(provider, "exit_zero_failure_markers", ()),
            launch_stderr=launch(stderr or "") if launch is not None else None,
        )
    except Exception:  # noqa: BLE001 - the quote must never raise
        match = None
    stdout, stderr = stdout or "", stderr or ""
    if (
        match is not None and match.status == classified
        and match.pattern is not None and match.offset is not None
    ):
        text = stdout if match.channel == "stdout" else stderr
        offset = _unlowered_offset(text, match.offset)
        redacted, at = _redact_tracking(text, offset)
        if len(redacted) <= _VERDICT_QUOTE_CHARS:
            return redacted
        start = max(0, at - _VERDICT_QUOTE_LEAD)
        start = min(start, len(redacted) - _VERDICT_QUOTE_CHARS)
        return redacted[start:start + _VERDICT_QUOTE_CHARS]
    head = stdout if not stderr else (f"{stdout}\n{stderr}" if stdout else stderr)
    return redact_text(head)[:_VERDICT_QUOTE_CHARS]


def _classify_failed_run(
    provider: Any, capture: _dispatch_spawn._Capture, model: str = ""
) -> Optional[Tuple[str, str]]:
    """Ladder rung 3, plus the rung-1 verdicts (auth, invalid model, sandbox,
    and a refused invocation on a non-zero exit) and the rung-less
    ``context_length_exceeded``, consulted only for a run with no result.

    Classification lives in the adapter — it is the only layer that knows the
    provider's error shape — and is deliberately **not** consulted for a run that
    produced a schema-valid result: the patterns match on captured streams, and a
    successful answer routinely quotes plan text containing "rate limit" or
    "unauthorized".

    Of the five ``CATEGORY_*`` names the ladder has no rung for, exactly two are
    mapped here — ``invalid_model`` (D4) and ``sandbox_unavailable`` (D6) —
    because a rejected id is a property of the spec and a sandbox that cannot
    start is a property of the machine, so the batch-wide fatal gate is
    telling the truth about every sibling on it. ``connection_error`` and ``server_error`` fall through to the
    parse failure's own retryable status, which is the policy the classifier's
    table asks for; ``permission_denied`` can fail one task and not its
    neighbour, so a fatal mapping would be this function's complaint pointed
    the other way. They return ``None`` on purpose. ``spawn_failed`` (omp's
    unknown ``--tools`` name, a shell's ``command not found``) is forwarded on
    a non-zero exit: an install or argv refusal is identical for every sibling,
    and the classifier reads it only off exit 127, stderr and an adapter's own
    refusal shape, never off a model's or a tool's words on stdout
    (``base.STDERR_LAUNCH_FAILURE_MARKERS``). A shell's phrase on stderr may be
    a hook's or a wrapper's, so it is forwarded only for a run that made no
    progress (``base.launch_refusal``).

    **An exit 0 is classified through** ``base.exit_zero_failure_category``,
    the gate the fan-out reads too: only an adapter that declares
    ``EXIT0_CLASSIFIABLE`` gives a verdict, read from what the CLI wrote and
    never from the model's answer; for any other the parse failure's own
    status stands (one transport retry), and ``spawn_failed`` is nothing.

    One more verdict is forwarded, and it is not a pattern verdict: an
    adapter's ``classify_structural`` ``runner_error`` (opencode's turn ended
    by an auto-rejected permission, §4.2 step 4), with the adapter's own reason
    sentence. It is asked only when the pattern verdict is none of the above.
    Failing that, a non-zero exit whose stderr carries a bubblewrap line that
    is none of the measured refusals is ``runner_error`` too, one transport
    retry, with :func:`~utils.providers.base.sandbox_hint`'s sentence naming
    ``doctor``.

    The forwarded pattern verdicts quote the text that decided them
    (:func:`_quote_verdict`), not ``stderr or stdout``.
    """
    quote_err = capture.stderr or ""
    if capture.exit_code:
        try:
            classified = provider.classify_failure(
                capture.stdout, capture.stderr, capture.exit_code
            )
        except Exception:  # noqa: BLE001 - classification must not raise
            return None
        if classified == STATUS_SPAWN_FAILED:
            classified, quote_err = launch_refusal(
                provider, capture.stdout, capture.stderr, capture.exit_code
            )
    else:
        # An exit 0 that left no answer: stdout is usually the model's own
        # prose, so the verdict comes through the one gate the fan-out reads
        # too, and only from what the CLI wrote. An adapter that cannot tell
        # that apart from the answer (`EXIT0_CLASSIFIABLE`) gives none and the
        # parse failure's status stands; `spawn_failed` is read as nothing.
        _, classified = exit_zero_failure_category(
            provider, capture.stdout, capture.stderr
        )
    # §4.5.3's fourth sink: this reason is printed by the exit-3 block, which is
    # `orchestrator-run.log` under `--detach`, and is also stored in
    # `subagent_batch_report.json`. Redaction runs on the full stream **before**
    # the 2 KB tail — an auth failure is precisely the run whose stream quotes a
    # credential back, and tailing first would keep the value and drop the key
    # name that makes it matchable.
    if classified == STATUS_CONTEXT_LENGTH_EXCEEDED:
        # Terminal, and NOT a rung: it is in none of RETRYABLE/BACKOFF/FATAL, so
        # the ladder grants `dispatch_task` no further attempt and the slot
        # ends after exactly one attempt. §7.6(a) is explicit that this is the
        # shipping behaviour until open question 13 designs a prompt splitter —
        # re-sending an unchanged oversized prompt is the one retry guaranteed to
        # fail identically, and a rung-down would only spend the budget doing it.
        return STATUS_CONTEXT_LENGTH_EXCEEDED, context_length_message(model)
    if classified == STATUS_BUDGET_EXHAUSTED:
        # The provider already consumed its internal step budget. Repeating
        # the same prompt would silently grant a fresh budget to the same run.
        return STATUS_BUDGET_EXHAUSTED, "the provider exhausted its internal step budget"
    # T2.5: the quote is cut from the VENDOR-reduced capture, around the text
    # that decided the verdict, and from the stderr the verdict was read from
    # (a foreign shell's phrase blanked when `launch_refusal` read past it). This
    # is the one application of `vendor_text` outside `classify_failure` (its
    # docstring names both), and it is for the quote only: the verdict is
    # already decided and nothing below moves it. A reduction that raises
    # quotes the capture as it came.
    reduced_out, reduced_err = capture.stdout or "", quote_err
    if getattr(provider, "vendor_text", None) is not None:
        try:
            reduced_out, reduced_err = provider.vendor_text(
                reduced_out, reduced_err
            )
        except Exception:  # noqa: BLE001 - the quote must never raise
            reduced_out, reduced_err = capture.stdout or "", quote_err
    if classified not in (
        STATUS_AUTH_FAILED, STATUS_RATE_LIMITED, STATUS_INVALID_MODEL,
        STATUS_SANDBOX_UNAVAILABLE, STATUS_SPAWN_FAILED,
    ):
        # §4.2 step 4 (T4.3): a verdict the adapter reads off the stream's
        # SHAPE, with its own reason — opencode's turn ended by an auto-rejected
        # permission. It is consulted only here, after every forwarded pattern
        # verdict above had its chance, so a genuine vendor 429 or auth error
        # in the same stream still wins; and ahead of everything else, so the
        # attempt is recorded `runner_error` with the permission sentence rather
        # than `unparseable` with "No text events found in output". Its reason
        # is the adapter's own sentence, so the matched-pattern quote below
        # never applies to it.
        structural = getattr(provider, "classify_structural", None)
        found = None
        if structural is not None:
            try:
                found = structural(
                    capture.stdout, capture.stderr, capture.exit_code or 0
                )
            except Exception:  # noqa: BLE001 - classification must not raise
                found = None
        if (
            isinstance(found, tuple) and len(found) == 2
            and found[0] == STATUS_RUNNER_ERROR and found[1]
        ):
            return STATUS_RUNNER_ERROR, redact_text(str(found[1]))
        return _sandbox_hinted(provider, capture, classified, reduced_out, reduced_err)
    tail = _quote_verdict(
        provider, reduced_out, reduced_err, capture.exit_code or 0, classified
    )
    if classified == STATUS_SANDBOX_UNAVAILABLE:
        # D6 step 4. `STATUS_SANDBOX_UNAVAILABLE` *is* the classifier's
        # `CATEGORY_SANDBOX_UNAVAILABLE` string, on D4's pattern. The stream
        # tail carries the `bwrap:` line itself, which is the one thing the
        # reader needs to recognise the machine condition `doctor` repairs.
        return STATUS_SANDBOX_UNAVAILABLE, (
            f"the runner's own sandbox could not start — "
            f"{_runner_selection._REASON_EXPLANATION['sandbox_unavailable']} (a property of the "
            f"machine, never fixed by a retry). Stream tail: {tail!r}"
        )
    if classified == STATUS_INVALID_MODEL:
        # D4 step 2. `STATUS_INVALID_MODEL` *is* the classifier's
        # `CATEGORY_INVALID_MODEL` string, so this is the category under its own
        # name. The verdict ends in the redacted stream tail on purpose: that is
        # how the provider's "Did you mean" line reaches the log and the report,
        # and it is what replaces the adapter's composed text on the exit-3 line
        # (`status, error = reclassified` in `dispatch_task`) — never appended
        # to it, never deduplicated against it.
        provider_name = str(getattr(provider, "name", "") or "")
        spec = f"{provider_name}:{model}" if model else provider_name or "(unknown)"
        return STATUS_INVALID_MODEL, (
            f"the runner rejected the model id {spec!r} (the fix is a config "
            f"edit, never a retry). Stream tail: {tail!r}"
        )
    if classified == STATUS_AUTH_FAILED:
        return STATUS_AUTH_FAILED, (
            f"the runner is installed but not authenticated (it printed a "
            f"login/credential notice). No retry can fix this and every sibling "
            f"task would fail identically, so the whole batch fails. Stream tail: "
            f"{tail!r}"
        )
    if classified == STATUS_RATE_LIMITED:
        return STATUS_RATE_LIMITED, (
            f"the provider reported a rate limit / quota / overloaded condition. "
            f"Stream tail: {tail!r}"
        )
    if classified == STATUS_SPAWN_FAILED:
        return STATUS_SPAWN_FAILED, (
            f"the runner refused its own invocation (an argv or install "
            f"refusal, identical for every sibling task), so no retry can fix "
            f"it and the whole batch fails. Stream tail: {tail!r}"
        )
    return None


def _sandbox_hinted(
    provider: Any, capture: _dispatch_spawn._Capture, classified: Optional[str],
    reduced_out: str, reduced_err: str,
) -> Optional[Tuple[str, str]]:
    """``runner_error`` naming ``doctor`` for a non-zero exit whose stderr
    carries a bubblewrap line, else ``None``. ``reduced_out``/``reduced_err``
    are :func:`_classify_failed_run`'s quote text.

    Reached only when no forwarded verdict decided the run, so the line is
    none of the measured refusals (those are ``sandbox_unavailable``,
    batch-fatal). The attempt keeps one transport retry, as the parse
    failure's status would give it, and its message points at the sandbox
    (docs/development/providers.md#launch-diagnostics).
    """
    if not capture.exit_code:
        return None
    try:
        hint = sandbox_hint(provider.launch_diagnostics(capture.stderr or ""))
    except Exception:  # noqa: BLE001 - a diagnosis must never fail a dispatch
        return None
    if hint is None:
        return None
    tail = _quote_verdict(
        provider, reduced_out, reduced_err, capture.exit_code, classified or ""
    )
    return STATUS_RUNNER_ERROR, (
        f"the runner exited with code {capture.exit_code}; {redact_text(hint)}. "
        f"Stream tail: {tail!r}"
    )
