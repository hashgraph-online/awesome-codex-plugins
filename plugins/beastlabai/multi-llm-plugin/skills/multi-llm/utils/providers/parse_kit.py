"""The result every adapter's ``parse_output`` returns, and the readers they share.

``parse_output(stdout, stderr)`` answers one dict
(docs/development/providers.md#reading-a-capture):

* a success, ``{"success": True, "data": <the answer>}``, plus what the shared
  extractor adds (``enclosing_syntax_error``, ``only_object``) or an adapter
  adds (``raw`` carrying the answer text);
* a failure, ``{"success": False, "error": <sentence>, "raw": <text>,
  "data": None}``, plus an adapter's own keys after those four
  (``incomplete``, ``error_code``, diagnostics).

A failure's ``raw`` decides a retry rung: the executor reads a failure with a
non-empty ``raw`` as an unparseable answer (rung 5) and one without as a
runner error (rung 4). Each adapter therefore passes the text it means,
usually its stdout; :func:`answer_from_text` defaults it only for the
empty-answer failure, where the stripped text is ``""``.

Error strings are graded by the fixture manifests (``error_contains``), so the
adapters keep their own sentences; nothing here words an error but the one
:func:`loads_or_extract` has always used.
"""

import json
from typing import Any, Optional, Tuple, TypedDict

from ..json_extractor import extract_json_from_text


class ParseResult(TypedDict, total=False):
    """The keys a parse result may carry (see the module docstring)."""

    success: bool
    data: Any
    error: str
    raw: str
    incomplete: bool
    error_code: str


def fail(error: Any, raw: Any, **extra: Any) -> ParseResult:
    """A failure: ``success``, ``error``, ``raw``, ``data``, then *extra* in order."""
    result: ParseResult = {"success": False, "error": error, "raw": raw, "data": None}
    result.update(extra)  # type: ignore[typeddict-item]
    return result


def ok(data: Any) -> ParseResult:
    """A success carrying *data* and nothing else."""
    return {"success": True, "data": data}


def direct_json(text: str) -> Optional[ParseResult]:
    """*text* as one whole JSON document when it opens like one, else ``None``.

    The fast path: a reply that is exactly the document is served whole, never
    a piece the extractor would rank first.
    """
    if text.startswith(("[", "{")):
        try:
            return ok(json.loads(text))
        except json.JSONDecodeError:
            pass
    return None


def answer_json(text: str) -> ParseResult:
    """:func:`direct_json`, else the shared extractor, arrays preferred.

    *text* is read as given; :func:`answer_from_text` strips it first.
    """
    direct = direct_json(text)
    if direct is not None:
        return direct
    return extract_json_from_text(text, prefer_arrays=True)


def answer_from_text(
    text: str,
    *,
    raw: Optional[str] = None,
    empty_error: Optional[str] = "Empty text response",
) -> ParseResult:
    """A model's answer text to a parse result: strip, refuse empty, then parse.

    An empty answer fails with *empty_error* and *raw* (the stripped text, so
    ``""``, when *raw* is ``None``). ``empty_error=None`` skips that check and
    hands even an empty text to the extractor, whose own failure then stands.
    """
    text = text.strip()
    if empty_error is not None and not text:
        return fail(empty_error, text if raw is None else raw)
    return answer_json(text)


def loads_or_extract(stdout: str) -> Tuple[Any, Optional[ParseResult]]:
    """``(envelope, None)`` when *stdout* is one JSON document, else ``(None, result)``.

    The *result* is the extractor's success over the raw stdout when it finds
    something, else ``JSON parse error: …`` with stdout as ``raw``. Check the
    second item: a document can itself be ``null``.
    """
    try:
        return json.loads(stdout), None
    except json.JSONDecodeError as e:
        fallback = extract_json_from_text(stdout, prefer_arrays=True)
        if fallback.get("success"):
            return None, fallback
        return None, fail(f"JSON parse error: {e}", stdout)
