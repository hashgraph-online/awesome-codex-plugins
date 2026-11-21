"""Where an envelope adapter's JSON envelope sits in its stdout.

:func:`envelope_signature` compiles an adapter's ``ENVELOPE_SIGNATURE``,
:func:`read_stdout` is the one rule for reading stdout against it, and
:func:`structural_stdout` and :func:`diagnostic_streams` are what a parser's
structural check and a failure verdict read through it
(docs/development/providers.md#reading-a-capture). It parses stdout rather than
classifying it, and it needs ``utils.json_extractor``'s ANSI pattern, so it
sits beside ``failure_classifier`` rather than in it. ``base`` re-exports every
name here for reading (docs/development/providers.md#the-provider-base-modules).
"""

import json
import re
from dataclasses import dataclass
from typing import Any, Collection, Dict, List, Pattern, Tuple

# The one ANSI/OSC pattern (`utils.json_extractor` sits below the provider
# layer, so the import closes no cycle).
from ..json_extractor import _ANSI_ESCAPE


def envelope_signature(*openers: Any) -> Tuple["Pattern[str]", ...]:
    """Compile one adapter's envelope signature: how its JSON envelope opens.

    Each opener is the envelope's first key, or a ``(key, value)`` pair where
    the key alone is too common to tell an envelope from an answer object
    (``("type", "result")``). Taken from the adapter's captured envelopes;
    JSON whitespace between the tokens is tolerated (gemini and goose print
    theirs indented). :func:`read_stdout` matches each pattern at the opening
    brace of a JSON value where the CLI writes its envelope, and searches for
    it as plain text everywhere else.
    """
    patterns = []
    for opener in openers:
        if isinstance(opener, tuple):
            key, value = opener
            patterns.append(re.compile(
                r"\{[ \t\n\r]*" + re.escape(json.dumps(key)) + r"[ \t\n\r]*:[ \t\n\r]*"
                + re.escape(json.dumps(value))
            ))
        else:
            patterns.append(re.compile(
                r"\{[ \t\n\r]*" + re.escape(json.dumps(opener)) + r"[ \t\n\r]*:"
            ))
    return tuple(patterns)


#: :func:`read_stdout`'s four readings of an envelope adapter's stdout: the
#: envelope where the CLI writes it; its opening there with no complete value
#: after it (a kill or the capture bound cut it); its opening anywhere else, so
#: no text can be told to be the CLI's; no opening at all.
STDOUT_ENVELOPE = "envelope"
STDOUT_CUT = "cut"
STDOUT_AMBIGUOUS = "ambiguous"
STDOUT_PLAIN = "plain"

_JSON_SPACE = re.compile(r"[ \t\n\r]*")
_LINE_SPACE = re.compile(r"[ \t]*")


def _opens_on(signature: Collection["Pattern[str]"], text: str, at: int) -> bool:
    return any(pattern.match(text, at) for pattern in signature)


@dataclass(frozen=True)
class StdoutShape:
    """:func:`read_stdout`'s answer.

    For :data:`STDOUT_ENVELOPE` only: ``records`` are the complete JSON values
    stdout opens with, one per line, as ``(start, end, value)`` into ``text``
    (stdout less its ANSI colour), and ``envelope`` indexes the one the
    adapter reads.
    """

    kind: str
    text: str = ""
    records: Tuple[Tuple[int, int, Any], ...] = ()
    envelope: int = -1

    @property
    def value(self) -> Any:
        """The envelope's decoded object."""
        return self.records[self.envelope][2]

    def failure(self, cli: str, stdout: str) -> Dict[str, Any]:
        """The parse failure for a cut or an ambiguous stdout: no answer.

        ``incomplete`` marks an envelope that did not finish, so the ask lane
        keeps any text as partial evidence.
        """
        if self.kind == STDOUT_CUT:
            return {
                "success": False,
                "error": (
                    f"{cli}'s JSON envelope is incomplete: stdout ends inside it, "
                    f"so it holds no finished answer"
                ),
                "raw": stdout, "data": None, "incomplete": True,
            }
        return {
            "success": False,
            "error": (
                f"{cli}'s stdout holds its JSON envelope's opening away from where "
                f"the CLI writes the envelope, so no answer in it can be trusted"
            ),
            "raw": stdout, "data": None,
        }


def read_stdout(stdout: str, signature: Collection["Pattern[str]"]) -> StdoutShape:
    """**The** rule for where an adapter's JSON envelope sits in its stdout.

    For the adapters whose JSON mode prints one envelope holding the answer in
    named fields (claude-code, cursor-agent, gemini, grok, agy, goose), each
    with its ``ENVELOPE_SIGNATURE``: their parsers and :func:`diagnostic_streams`
    read this and nothing else. Provenance is position, never keys: a model
    writes inside the envelope's answer string, never the start of stdout, and
    every committed capture of the six is exactly one envelope.

    After ANSI colour and leading whitespace, stdout opens with a run of
    complete JSON values, one per line (JSON log lines), each decoded where it
    starts (``raw_decode``, so one linear pass); any other text after them, on
    the last one's line or below, is trailing text. Then:

    * :data:`STDOUT_ENVELOPE`: one of those values opens on the signature. The
      last such is the envelope; the rest is the CLI's.
    * :data:`STDOUT_CUT`: the run stops at a signature opening with no complete
      value there. The envelope was cut.
    * :data:`STDOUT_AMBIGUOUS`: neither, but a signature opening appears
      anywhere, matched as plain text so that no quote or bracket can hide
      it: a banner ahead of the envelope, or an answer quoting one. Refused.
    * :data:`STDOUT_PLAIN`: no opening at all, or no signature. The adapter's
      ordinary extraction, unchanged.

    See docs/development/providers.md#reading-a-capture.
    """
    if not signature:
        return StdoutShape(STDOUT_PLAIN)
    raw = stdout or ""
    text = _ANSI_ESCAPE.sub("", raw)
    decoder = json.JSONDecoder()
    records: List[Tuple[int, int, Any]] = []
    envelope = -1
    at = _JSON_SPACE.match(text).end()
    while at < len(text) and text[at] in "{[":
        opens = _opens_on(signature, text, at)
        try:
            value, end = decoder.raw_decode(text, at)
        except (ValueError, RecursionError):
            if opens:
                return StdoutShape(STDOUT_CUT, text)
            break
        if opens:
            envelope = len(records)
        records.append((at, end, value))
        line_end = _LINE_SPACE.match(text, end).end()
        if line_end < len(text) and text[line_end] not in "\r\n":
            break
        at = _JSON_SPACE.match(text, end).end()
    if envelope >= 0:
        return StdoutShape(STDOUT_ENVELOPE, text, tuple(records), envelope)
    if any(pattern.search(text) or pattern.search(raw) for pattern in signature):
        return StdoutShape(STDOUT_AMBIGUOUS, text)
    return StdoutShape(STDOUT_PLAIN, text)


def structural_stdout(stdout: str, provider: Any) -> str:
    """*stdout* for an adapter's structural failure check (a status field, an
    error part), or ``""`` when :func:`read_stdout` finds it cut or ambiguous:
    the same stdout decision :func:`diagnostic_streams` makes, so no check reads
    a capture the verdict was told to ignore. An envelope or plain capture is
    returned whole, as those checks read it before."""
    shape = read_stdout(stdout, provider.ENVELOPE_SIGNATURE)
    if shape.kind in (STDOUT_CUT, STDOUT_AMBIGUOUS):
        return ""
    return stdout


def diagnostic_streams(stdout: str, stderr: str, provider: Any) -> Tuple[str, str]:
    """**The** capture a failure verdict and its quote read, for an envelope adapter.

    The six envelope adapters' :meth:`LLMProvider.vendor_text`, so
    :meth:`LLMProvider.classify_failure` (on an exit 0, through
    :meth:`LLMProvider.classify_exit_zero`, and on any other) and the
    executor's failure quote read one text. By :func:`read_stdout`:

    * an envelope: each record that opens on the signature as
      :meth:`LLMProvider.envelope_diagnostics` keeps it (the model's answer
      out, the vendor's refusal fields in), the other JSON lines and the
      trailing text as the CLI wrote them;
    * cut or ambiguous: nothing of stdout, as no text in it can be told to be
      the CLI's; stderr is read as always, under the adapter's
      ``LAUNCH_DIAGNOSTICS``;
    * plain: the capture unchanged (a CLI's plain-text refusal).

    A record is re-serialised, compactly, only when something was taken out
    of it, so the result is a deletion from stdout. stderr is never reduced.
    """
    signature = provider.ENVELOPE_SIGNATURE
    shape = read_stdout(stdout, signature)
    if shape.kind == STDOUT_PLAIN:
        return stdout, stderr
    if shape.kind != STDOUT_ENVELOPE:
        return "", stderr
    pieces: List[str] = []
    last = 0
    for start, end, value in shape.records:
        kept = (
            provider.envelope_diagnostics(value)
            if _opens_on(signature, shape.text, start) else value
        )
        pieces.append(shape.text[last:start])
        pieces.append(
            shape.text[start:end] if kept == value
            else json.dumps(kept, ensure_ascii=False, separators=(",", ":"))
        )
        last = end
    pieces.append(shape.text[last:])
    return "".join(pieces), stderr
