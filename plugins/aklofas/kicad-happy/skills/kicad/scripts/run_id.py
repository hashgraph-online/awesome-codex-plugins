"""Run ID generation for analyzer provenance.

Format: ``YYYYMMDDTHHMMSSZ-<6 hex>``
Example: ``20260418T123456Z-a1b2c3``

- Timestamp portion: compact ISO-8601 UTC (sortable as a string).
- Random suffix: 6 hex chars from secrets.token_hex(3), giving ~2^24 =
  16M distinct IDs per second. Good enough for this workload (a single
  host runs one analyzer at a time; concurrent CI jobs across hosts
  still have timestamp + hash discrimination).

Deterministic overrides accepted via the ``now`` and ``rand_hex`` kwargs
so tests can pin the output without mocking the clock or the RNG.
"""
from __future__ import annotations

import re
import secrets
from datetime import datetime, timezone

_HEX_RE = re.compile(r"^[0-9a-f]{6}$")


def generate_run_id(
    now: datetime | None = None,
    rand_hex: str | None = None,
) -> str:
    """Return a freshly generated run ID.

    Parameters
    ----------
    now : datetime, optional
        Override the wall-clock timestamp. Defaults to ``datetime.now(UTC)``.
    rand_hex : str, optional
        Override the random suffix (must be exactly 6 lowercase hex chars).
        Defaults to ``secrets.token_hex(3)``.
    """
    if now is None:
        now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y%m%dT%H%M%SZ")
    if rand_hex is None:
        rand_hex = secrets.token_hex(3)
    elif not _HEX_RE.match(rand_hex):
        raise ValueError(
            f"rand_hex must be exactly 6 hex chars (got {rand_hex!r})"
        )
    return f"{timestamp}-{rand_hex}"
