"""Diagnostics: guarded failures that degraded a run, recorded instead of swallowed (kicad_core).

A guard that falls back (section omitted, fallback model used) calls ``record``: one stderr line
always, plus one ``Diagnostic`` dict appended when the caller threaded a list sink. Analyzer
envelopes carry the collected list as ``diagnostics`` (``[]`` when nothing degraded).
"""
import sys
from dataclasses import asdict, dataclass, field


@dataclass
class Diagnostic:
    """One guarded failure that degraded the run."""
    source: str = field(metadata={
        "description": "Where the guard sits: '<module>.<function>'."})
    exception: str = field(metadata={
        "description": "Exception class name, e.g. 'KeyError'."})
    message: str = field(metadata={
        "description": "str(exception), truncated to 200 characters."})
    effect: str = field(metadata={
        "description": "What the run did instead, e.g. 'power_rails config not applied'."})


class OnceSink(list):
    """A sink for repeated runs: ``record()`` drops a record equal to one the sink already
    holds — no stderr line, no append."""


def record(sink, source: str, exc: BaseException, effect: str) -> None:
    """Print one stderr line for *exc*; append a Diagnostic dict when *sink* is a list."""
    message = str(exc)[:200]
    if isinstance(sink, list):
        entry = asdict(Diagnostic(source=source, exception=type(exc).__name__,
                                  message=message, effect=effect))
        if isinstance(sink, OnceSink) and entry in sink:
            return
        sink.append(entry)
    print(f"Warning: {source}: {type(exc).__name__}: {message} — {effect}", file=sys.stderr)


def merge(*sinks) -> list:
    """Concatenate diagnostic lists in argument order; None entries are skipped."""
    out: list = []
    for s in sinks:
        if s:
            out.extend(s)
    return out
