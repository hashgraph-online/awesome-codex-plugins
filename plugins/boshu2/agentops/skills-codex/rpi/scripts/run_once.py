#!/usr/bin/env python3
"""Pure reference behavior for one RPI invocation.

The caller supplies one anti-ceremony guard and the three core phase functions.
This module invokes the guard once before Plan, dispatches each core phase at
most once, and never chooses a retry or next action.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
import re
from typing import Any


# The exact-identity property is BYTE-addressed: Validate snapshots the resolved
# intent bytes under `sha256(bytes)` and stores them as `<digest>.intent`
# (validate.py snapshot_intent), then re-derives that same digest from the same
# bytes when it binds runtime facts into the verdict. RPI is a dispatcher, not a
# second digest authority — it carries the digest Plan declares over the bytes it
# snapshotted, and cross-checks Validate's independently re-derived value against
# it.
#
# This module previously computed its own `sha256(canonical-JSON(mapping))` here
# and hard-compared that against Validate's `sha256(raw bytes)`. The two can
# never agree unless the source is byte-identical canonical JSON, so the composed
# contract was broken; both unit suites stayed green only because the RPI test
# mocked Validate with THIS module's digest function. A canonical-JSON digest is
# also the wrong identity in principle: two different source files that parse to
# the same mapping share it, which is precisely the collision exact identity
# exists to forbid.
DIGEST_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def valid_digest(value: Any) -> bool:
    """True for a lowercase hex SHA-256, the only shape an identity may take."""
    return isinstance(value, str) and bool(DIGEST_PATTERN.match(value))


def valid_string_list(value: Any) -> bool:
    """True for the guard contract's JSON-shaped string lists."""
    return isinstance(value, list) and all(
        isinstance(item, str) and bool(item.strip()) for item in value
    )


def guard_result(value: Any) -> dict[str, Any]:
    """Return one valid artifact-free anti-ceremony decision."""
    if not isinstance(value, Mapping):
        raise ValueError("anti-ceremony guard must return a mapping")
    result = dict(value)
    expected = {
        "decision",
        "reason",
        "frozen_outcome",
        "parked_process_work",
        "remaining_proof",
        "stop_condition",
    }
    if set(result) != expected:
        raise ValueError("anti-ceremony guard returned the wrong fields")
    if result["decision"] not in {"CONTINUE", "STOP"}:
        raise ValueError("anti-ceremony decision must be CONTINUE or STOP")
    reason = result["reason"]
    if (
        not isinstance(reason, str)
        or not reason.strip()
        or "\n" in reason
        or reason[-1] not in ".!?"
        or sum(reason.count(mark) for mark in ".!?") != 1
    ):
        raise ValueError("anti-ceremony reason must be exactly one sentence")
    if not isinstance(result["frozen_outcome"], str) or not result["frozen_outcome"].strip():
        raise ValueError("anti-ceremony frozen_outcome must be a nonempty string")
    if not valid_string_list(result["parked_process_work"]):
        raise ValueError("anti-ceremony parked_process_work must be a string list")
    if not valid_string_list(result["remaining_proof"]):
        raise ValueError("anti-ceremony remaining_proof must be a string list")
    if not isinstance(result["stop_condition"], str) or not result["stop_condition"].strip():
        raise ValueError("anti-ceremony stop_condition must be a nonempty string")
    return result


def report(
    status: str,
    *,
    intent_ref: str | None = None,
    acceptance_digest: str | None = None,
    subject_digest: str | None = None,
    verdict_ref: str | None = None,
    verdict_digest: str | None = None,
    checked: list[str] | None = None,
    not_checked: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": "rpi-report.v1",
        "status": status,
        "intent_ref": intent_ref,
        "acceptance_digest": acceptance_digest,
        "subject_manifest_digest": subject_digest,
        "verdict_ref": verdict_ref,
        "verdict_digest": verdict_digest,
        "checked": checked or [],
        "not_checked": not_checked or [],
    }


def invoke_once(
    intent: Any,
    anti_ceremony_guard: Callable[[Any], Mapping[str, Any]],
    plan_phase: Callable[[Any], Mapping[str, Any] | None],
    implement_phase: Callable[[Mapping[str, Any]], Mapping[str, Any] | None],
    validate_phase: Callable[[Mapping[str, Any], Mapping[str, Any]], Mapping[str, Any]],
) -> dict[str, Any]:
    """Invoke the guard once, then dispatch each core phase at most once."""
    admission = guard_result(anti_ceremony_guard(intent))
    if admission["decision"] == "STOP":
        return report(
            "NOT_PLANNED",
            checked=[f"anti-ceremony guard: STOP — {admission['reason']}"],
            not_checked=["plan", "implement", "validate"],
        )
    resolved_intent = plan_phase(intent)
    if resolved_intent is None:
        return report("NOT_PLANNED", not_checked=["implement", "validate"])
    resolved_intent = dict(resolved_intent)
    intent_ref = resolved_intent.get("intent_ref")
    if not isinstance(intent_ref, str) or not intent_ref:
        intent_ref = "caller"
    acceptance_digest = resolved_intent.get("acceptance_digest")
    if not valid_digest(acceptance_digest):
        raise ValueError(
            "Plan must declare acceptance_digest as the SHA-256 of the exact resolved "
            "intent bytes it snapshotted (validate.py snapshot-intent emits it)"
        )

    subject = implement_phase(resolved_intent)
    if subject is None:
        return report(
            "NOT_BUILT",
            intent_ref=intent_ref,
            acceptance_digest=acceptance_digest,
            checked=["plan"],
            not_checked=["validate"],
        )
    subject = dict(subject)

    validation = dict(validate_phase(resolved_intent, subject))
    status = validation.get("verdict")
    if status not in {"PASS", "FAIL", "NOT_PROVEN"}:
        raise ValueError("Validate must return PASS, FAIL, or NOT_PROVEN")
    # Validate re-derives this from the snapshot bytes independently; equality
    # here is the composed exact-identity check, not a self-comparison.
    if validation.get("acceptance_digest") != acceptance_digest:
        raise ValueError("Validate verdict does not match the resolved intent digest")
    subject_digest = validation.get("subject_manifest_digest")
    if not valid_digest(subject_digest):
        raise ValueError("Validate must return the exact subject manifest digest")
    candidate_digest = subject.get("subject_manifest_digest")
    if candidate_digest is not None and subject_digest != candidate_digest:
        raise ValueError("Validate result does not match the implemented subject digest")
    author_context_id = validation.get("author_context_id")
    validator_context_id = validation.get("validator_context_id")
    freshness = validation.get("freshness_attestation")
    if (
        not isinstance(author_context_id, str)
        or not author_context_id
        or not isinstance(validator_context_id, str)
        or not validator_context_id
        or author_context_id == validator_context_id
        or not isinstance(freshness, Mapping)
        or freshness.get("source") not in {"runtime", "caller"}
        or not isinstance(freshness.get("attester_identity"), str)
        or not freshness.get("attester_identity")
    ):
        raise ValueError("Validate must return distinct context identities and explicit freshness")
    verdict_digest = validation.get("verdict_digest")
    verdict_ref = validation.get("verdict_ref")
    if (verdict_digest is None) != (verdict_ref is None):
        raise ValueError("Validate must return both verdict_ref and verdict_digest when persistence is requested")
    if verdict_ref is not None and (
        not isinstance(verdict_ref, str)
        or not verdict_ref
        or not valid_digest(verdict_digest)
    ):
        raise ValueError("Persisted verdict identity is invalid")
    return report(
        status,
        intent_ref=intent_ref,
        acceptance_digest=acceptance_digest,
        subject_digest=subject_digest,
        verdict_ref=verdict_ref,
        verdict_digest=verdict_digest,
        checked=list(validation.get("checked") or []),
        not_checked=list(validation.get("not_checked") or []),
    )
