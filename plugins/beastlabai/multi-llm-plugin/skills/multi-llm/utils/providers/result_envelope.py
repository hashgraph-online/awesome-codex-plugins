"""The one result-envelope parser (§9.5).

``cursor-agent --output-format json`` and ``claude -p --output-format json``
both wrap the model's answer in the same envelope::

    {"type": "result", "result": "<the answer, usually JSON as a string>", ...}

``cursor_agent.parse_output`` and ``claude_code.parse_output`` each carried a
34-line copy of the unwrapping logic, differing in **one comment**, with 0/9
behavioural differences measured over the envelope shapes in
``tests/test_result_envelope.py``. This module is that logic, once.

Not folded in here: ``llm_client.parse_subagent_response``, the legacy third
copy. It uses a weaker extractor and returns bare parsed JSON instead of a
``{"success": ..., "data": ...}`` result, and it is **live** behind the shipped
``--internal-validation`` flag (``review_orchestrator_base`` →
``validation.validate_groups`` → ``invoke_for_json`` → ``invoke_subagent`` +
``parse_subagent_response``). Unifying it would change what that flag returns,
so it stays until the flag is retired.

**The envelope also carries the CLI's own verdict, and this module reads it**
(C5). Three machine-readable fields were printed and ignored: ``is_error`` and
``terminal_reason``, which say *whether* the run failed, and
``api_error_status``, which says *why*. The first two belong to the parser and
are enforced by :func:`parse_result_envelope` below; the third belongs to the
classifier and is offered to the two adapters as
:func:`classify_api_error_status`, a rung they consult **ahead of** the text
ladder. Both value sets are measured off the committed captures under
``tests/fixtures/claude-code/`` and ``tests/fixtures/cursor-agent/`` rather than
guessed — see the two tables below.
"""
import json
from typing import Any, Dict, List, Optional

from ..json_extractor import extract_json_from_text
from .base import (
    CATEGORY_INVALID_MODEL,
    CATEGORY_SERVER_ERROR,
    STATUS_AUTH_FAILED,
    STATUS_RATE_LIMITED,
)

#: The ``terminal_reason`` values that mean "this run finished normally".
#:
#: Measured, not guessed. Across the eleven committed ``claude-code`` captures
#: the field takes exactly two values: ``"completed"`` on the three
#: ``is_error: false`` rows (``success``, ``ephemeral-only``,
#: ``multi-assistant``) and ``"api_error"`` on all eight ``is_error: true``
#: rows. cursor-agent never emits the field at all. "Present and not a success
#: value" is only implementable once the success values are named, and this is
#: the name — a *set* rather than a single string so a vendor adding
#: ``"finished"`` is one entry here rather than a rewrite of the rule.
SUCCESS_TERMINAL_REASONS = frozenset({"completed"})

#: The longest stretch of the envelope's own words, **in characters**, this
#: module will quote into an error string. A ``result`` field can hold a whole
#: document; the error string it lands in is read by a human on one line of a
#: report. Counted in characters rather than words because it is the rendered
#: line's width that has to fit, and a word count does not bound it.
_MAX_QUOTED_CHARS = 400


def _is_error_flag(value: Any) -> bool:
    """Whether ``is_error`` says this run failed.

    Measured as a JSON boolean on every committed capture. The string form is
    accepted too because a flag spelled ``"true"`` by a future release must not
    read as "absent" — but nothing else is: a truthiness test would make
    ``"false"`` an error.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() == "true"
    return False


def _non_success_terminal_reason(value: Any) -> Optional[str]:
    """``terminal_reason`` when it is present and is **not** a success value.

    ``None`` covers all three of the table's serve-it cases at once: the field
    absent, the field ``null``, and the field naming a success.
    """
    if value is None:
        return None
    if isinstance(value, str) and value.strip().lower() in SUCCESS_TERMINAL_REASONS:
        return None
    return value if isinstance(value, str) else repr(value)


def _envelope_words(wrapper: Dict[str, Any]) -> str:
    """The vendor's own sentence for this failure, reduced to one line.

    ``result`` first, because that is where both CLIs put the diagnosis — every
    claude-code failure prefixes it ``API Error:``. ``error``/``message`` are
    the shapes an envelope with no ``result`` key uses instead.
    """
    for key in ("result", "error", "message"):
        value = wrapper.get(key)
        if isinstance(value, dict):
            value = value.get("message")
        if isinstance(value, str) and value.strip():
            text = " ".join(value.split())
            if len(text) > _MAX_QUOTED_CHARS:
                text = text[:_MAX_QUOTED_CHARS] + "..."
            return text
    return ""


def envelope_verdict(wrapper: Dict[str, Any]) -> List[str]:
    """The envelope's own reasons to refuse this run, in the fields' own words.

    Empty means "no field objected", which the caller must read as *serve the
    ``result`` exactly as before* — not as "this run succeeded". The two fields
    never disagree on any committed capture, so the ``or`` between them is
    belt-and-braces today; it is written as an accumulating list rather than a
    short-circuit so a future divergence is *reported* (both flags named in the
    error) instead of silently resolved by whichever field was consulted first.
    """
    flags = []
    if _is_error_flag(wrapper.get("is_error")):
        flags.append("is_error: true")
    reason = _non_success_terminal_reason(wrapper.get("terminal_reason"))
    if reason is not None:
        flags.append(f"terminal_reason: {reason}")
    return flags


def _refuse(wrapper: Dict[str, Any], raw: str) -> Optional[Dict[str, Any]]:
    """The refusal an objecting envelope becomes, or ``None`` to carry on."""
    flags = envelope_verdict(wrapper)
    if not flags:
        return None
    error = f"The runner reported a failed run ({', '.join(flags)})"
    words = _envelope_words(wrapper)
    if words:
        error = f"{error}: {words}"
    return {"success": False, "error": error, "raw": raw, "data": None}


def _whole_envelope(stdout: str) -> Optional[Dict[str, Any]]:
    """stdout parsed as the one envelope both CLIs print, or ``None``.

    The same read :func:`envelope_api_error_status` makes: one JSON object,
    the whole of stdout. Anything else — a run that never launched, a truncated
    stream, prose — is ``None``, and every caller treats ``None`` as "not an
    envelope", never as "fine".
    """
    text = (stdout or "").strip()
    if not text.startswith("{"):
        return None
    try:
        wrapper = json.loads(text)
    except ValueError:
        return None
    return wrapper if isinstance(wrapper, dict) else None


def describe_refused_envelope(stdout: str) -> Optional[str]:
    """One line for ``describe_failure``: the refusing envelope's own words.

    ``None`` unless stdout is a single envelope :func:`envelope_verdict`
    objects to; otherwise ``HTTP <status>: <sentence>`` when the envelope
    carries an ``api_error_status``, and the sentence alone when it does not.

    Why this exists (measured 2026-09-17, ``claude-code:claude-fable-5-1:high``):
    neither envelope adapter overrode ``describe_failure``, so a review slot
    that ran 491 s and died on a 429 usage cap was recorded — in
    ``error_<model>.log``, in ``.status.json``'s ``models_failed`` and on the
    fan-out's own ``Agent failed`` line — as the bare ``claude-code exited with
    code 1``, while the CLI had printed the status **and** the sentence
    ("You've reached your Fable limit. Switch to another model, or manage usage
    credits at claude.ai/settings/usage…") on the one stream it uses. The
    status is spelled out because the vendor sentence does not always carry it:
    the committed ``rate-limit`` capture says ``API Error: Request rejected
    (429)``, the usage cap says nothing numeric at all.

    Diagnostics, never classification: the number is the same integer
    :func:`classify_api_error_status` reads, and nothing here consults a marker
    table.
    """
    wrapper = _whole_envelope(stdout)
    if wrapper is None or not envelope_verdict(wrapper):
        return None
    words = _envelope_words(wrapper)
    status = wrapper.get("api_error_status")
    prefix = ""
    if status is not None and not isinstance(status, bool):
        try:
            prefix = f"HTTP {int(status)}"
        except (TypeError, ValueError):
            prefix = ""
    if prefix and words:
        return f"{prefix}: {words}"
    return prefix or words or None


def envelope_api_error_status(stdout: str) -> Any:
    """The envelope's ``api_error_status``, or ``None`` when it has none.

    Reads the whole of stdout as one JSON object, which is what
    ``--output-format json`` prints on both CLIs — one envelope, one line. A
    capture that is not that (a run that never launched, a truncated stream, a
    CLI printing prose) yields ``None``, which
    :func:`classify_api_error_status` turns into "defer to the text ladder".
    """
    wrapper = _whole_envelope(stdout)
    if wrapper is None:
        return None
    return wrapper.get("api_error_status")


def is_clean_envelope(stdout: str) -> bool:
    """Whether stdout is one envelope the CLI itself reports as a clean run.

    True only when all three verdict fields agree there was no error: the
    whole of stdout parses as one envelope, :func:`envelope_verdict` raises no
    objection (``is_error`` false, ``terminal_reason`` completed or absent), and
    ``api_error_status`` is absent or ``null``. Such an envelope's ``result`` is
    the model's own prose — a validator that read a plan discussing rate limits
    says so there — so a classifier must not read it as the vendor's verdict
    (plan ``opencode-validator-false-rate-limit-and-denied-turn`` T3.2). Anything
    else — no envelope, a refusing one, one carrying a status — is ``False``,
    which leaves the caller's existing routes exactly as they were.
    """
    wrapper = _whole_envelope(stdout)
    if wrapper is None or envelope_verdict(wrapper):
        return False
    return wrapper.get("api_error_status") is None


def category_for_api_error_status(status: Any) -> Optional[str]:
    """The classifier category an ``api_error_status`` names, or ``None``.

    ``None`` means **defer to the text ladder** — never "this run was fine".
    The map is measured off the committed claude-code rows, one row per line:

    ==================  ==========================  ==============================
    ``api_error_status``  Category                    The row that pins it
    ==================  ==========================  ==============================
    401, 403             ``auth_failed``             ``auth-error``
    429                  ``rate_limited``            ``rate-limit`` (already right)
    404                  ``invalid_model``           ``invalid-model``
    400                  defer                       ``context-overflow``
    5xx                  ``server_error``            ``stdout-error``
    ``null`` / absent    defer                       ``zero-byte-response``
    ==================  ==========================  ==============================

    **400 defers on purpose, and it is the one row that would be wrong as a
    constant.** claude-code's ``context-overflow`` capture is a 400 whose text
    must stay ``context_length_exceeded``; a 400 is not one condition, so the
    status alone cannot name it and the sentence has to.
    """
    if status is None or isinstance(status, bool):
        return None
    try:
        code = int(status)
    except (TypeError, ValueError):
        return None
    if code in (401, 403):
        return STATUS_AUTH_FAILED
    if code == 429:
        return STATUS_RATE_LIMITED
    if code == 404:
        return CATEGORY_INVALID_MODEL
    if code == 400:
        return None
    if 500 <= code <= 599:
        return CATEGORY_SERVER_ERROR
    return None


def classify_api_error_status(stdout: str) -> Optional[str]:
    """The status rung both envelope adapters consult before the text ladder.

    One implementation for the two adapters that emit this envelope, for the
    same §9.5 reason :func:`parse_result_envelope` is one implementation of the
    unwrap: a second copy of a measured table is a second thing to keep true.
    """
    return category_for_api_error_status(envelope_api_error_status(stdout))


def parse_result_envelope(stdout: str) -> Dict[str, Any]:
    """Unwrap a ``{"type": "result", "result": ...}`` envelope.

    The envelope's *bookkeeping* is discarded — adapters that need what it
    carries (``usage``, ``total_cost_usd``, ``modelUsage``) read it separately
    in ``parse_usage``, before this drops it. Its **verdict** is not: this
    function used to branch only on the presence of a ``result`` key, so an
    envelope the CLI had flagged as an error whose ``result`` still held a
    parseable document was served as the answer. Two committed captures prove
    it rather than a hypothesis — cursor-agent's ``exit-zero-failure`` row is
    the harvested live envelope with ``is_error`` flipped to ``true``, and
    claude-code's ``error-envelope`` row carries ``is_error: true`` and
    ``terminal_reason: "api_error"`` next to ``subtype: "success"``.

    The rule, measured off the committed captures (C5):

    ======================  =====================================  ============
    Field                   Value                                  Effect
    ======================  =====================================  ============
    ``is_error``            ``true``                               refuse
    ``is_error``            ``false``, or absent                   next field
    ``terminal_reason``     ``"completed"``, absent, ``null``      serve
    ``terminal_reason``     any other string                       refuse
    ======================  =====================================  ============

    A refusal is ``success: False`` with the envelope's own words as ``error``
    and the raw envelope as ``raw`` — the shape Lane B's rung split reads, and
    the reason the vendor's sentence reaches a human at all.

    The check runs on **any** parsed envelope, not only one carrying a
    ``result`` key: an error-flagged envelope without one used to come back
    ``{"success": True, "data": <the bookkeeping>}``, which is the same defect
    one branch further down.

    **Three adapters call this, and the third is inert by construction.**
    claude-code and cursor-agent are the two C5 measured. ``qwen-code``
    delegates too, but only *after* its own rule 1 has refused any record whose
    ``is_error`` is true, whose ``subtype`` is not ``"success"``, or which
    carries no ``result`` key — so no record reaching here from that adapter has
    a verdict left to read, checked over its whole committed corpus. qwen's own
    rule stays load-bearing rather than becoming redundant: it reads a
    ``subtype`` and a missing-key case this function does not.

    Args:
        stdout: The child's captured stdout.

    Returns:
        ``{"success": True, "data": ...}`` or ``{"success": False, "error":
        ..., "data": None}``, the shape every ``parse_output`` returns.
    """
    stdout = stdout.strip()

    if stdout.startswith("{"):
        try:
            wrapper = json.loads(stdout)
            if isinstance(wrapper, dict):
                refusal = _refuse(wrapper, stdout)
                if refusal is not None:
                    return refusal
            if isinstance(wrapper, dict) and "result" in wrapper:
                inner_result = wrapper["result"]
                if isinstance(inner_result, str):
                    inner_result = inner_result.strip()
                    if inner_result.startswith(("[", "{")):
                        try:
                            return {"success": True, "data": json.loads(inner_result)}
                        except json.JSONDecodeError:
                            pass
                    # Try to extract JSON from text
                    return extract_json_from_text(inner_result, prefer_arrays=True)
                return (
                    {"success": True, "data": inner_result}
                    if inner_result
                    else {"success": False, "error": "Empty result", "data": None}
                )
            return {"success": True, "data": wrapper}
        except json.JSONDecodeError:
            pass

    # Try direct JSON parsing for arrays
    if stdout.startswith("["):
        try:
            return {"success": True, "data": json.loads(stdout)}
        except json.JSONDecodeError:
            pass

    return extract_json_from_text(stdout, prefer_arrays=True)
