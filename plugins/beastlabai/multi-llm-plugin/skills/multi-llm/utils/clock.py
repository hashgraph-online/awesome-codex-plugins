"""Wall-clock timestamps: one function for each format the skill writes.

A writer names the format its readers expect instead of spelling
``datetime.now()`` again. Three formats exist, and each is kept as it is
because records already on disk and the readers of them compare these
strings (merging the formats would be a change of its own):

* :func:`local_iso`: local time, no offset, microseconds
  (``2026-11-09T14:03:07.123456``; ``isoformat`` leaves the fraction out at
  a whole second). ``.status.json`` (``status_file.now_iso``) and the scope
  policy's run records, which compare stamps made within the same second.
* :func:`local_iso_seconds`: local time, no offset, whole seconds
  (``2026-11-09T14:03:07``). The scope policy's round and apply records and
  the write-safety records.
* :func:`utc_iso_z`: UTC, whole seconds, ``Z`` (``2026-11-09T13:03:07Z``).
  The commit range's ``resolved_at``/``created_at`` and the commit guard.

Readers of stamps a file may carry from another tool call :func:`parse_iso`,
which accepts a trailing ``Z`` on every Python the skill supports, or
:func:`parse_local` when it compares the result with another stamp.

Stdlib only; layer L0 (``tests/test_import_layers.py``).
"""

from __future__ import annotations

from datetime import datetime, timezone

__all__ = ["local_iso", "local_iso_seconds", "parse_iso", "parse_local", "utc_iso_z"]


def local_iso() -> str:
    """Now, local time without an offset, to the microsecond."""
    return datetime.now().isoformat()


def local_iso_seconds() -> str:
    """Now, local time without an offset, to the second."""
    return datetime.now().isoformat(timespec="seconds")


def utc_iso_z() -> str:
    """Now, in UTC, to the second, with a ``Z``."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso(text: str) -> datetime:
    """``datetime.fromisoformat`` that reads a trailing ``Z`` or ``z`` as UTC.

    Python 3.10's parser rejects the ``Z`` spelling that 3.11 and later accept, so
    a UTC stamp from another tool would read as unparseable there. The result is
    what the same text gives on 3.11+: aware for a ``Z`` or an offset, naive
    otherwise. A ``Z`` counts only as the last character, after a time (a date
    alone, a doubled suffix or a ``Z`` anywhere else is refused, on every Python).
    Raises ``ValueError`` for text that is not an ISO stamp, like
    ``fromisoformat``; the caller picks how an unreadable stamp reads.
    """
    if text[-1:] in ("Z", "z"):
        body = text[:-1]
        if "Z" in body or "z" in body:
            raise ValueError(f"Invalid isoformat string: {text!r}")
        parsed = datetime.fromisoformat(body + "+00:00")
        if parsed.tzinfo is None:
            raise ValueError(f"Invalid isoformat string: {text!r}")
        return parsed
    if "Z" in text or "z" in text:
        raise ValueError(f"Invalid isoformat string: {text!r}")
    return datetime.fromisoformat(text)


def parse_local(text: str) -> datetime:
    """:func:`parse_iso` as a naive local datetime, so stamps compare as instants.

    A stamp with a UTC offset is converted to local time. A stamp the platform
    cannot convert (year 9999 or 1 at the edge of the range) raises
    ``ValueError`` like any other unreadable stamp.
    """
    parsed = parse_iso(text)
    if parsed.tzinfo is not None:
        try:
            parsed = parsed.astimezone().replace(tzinfo=None)
        except (OverflowError, OSError) as exc:
            raise ValueError(f"Stamp outside the local time range: {text!r}") from exc
    return parsed
