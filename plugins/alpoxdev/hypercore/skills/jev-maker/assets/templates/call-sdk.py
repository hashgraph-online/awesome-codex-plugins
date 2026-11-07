"""Call Jev through the official Python SDK (typesafe-sdk).

Fill in: the STATE record and the question set below, and the thresholds, which must stay in
step with constants.template.ts in this folder. The SDK reads the key from TYPESAFE_API_KEY.
A live call only after the user consents: nothing is sent until LIVE_CALL_APPROVED is turned on,
and the key is read from the environment at call time and never printed.
"""

# Confidence is read from raw_http_response because the SDK pages document no typed confidence field.
from __future__ import annotations

import math
import os

from typesafe_sdk import Choice, Noul, Score, TypeSafeClient

# Consent gate. Leave this false until the person has agreed to a live call and knows its cost.
LIVE_CALL_APPROVED = False

# Snapshot 2026-10-01, re-check before a live call: references/providers.md
MODEL = "jev-latest"

# The thresholds are assumed before tuning, so evaluate on your own data before trusting them.
# The TypeScript template next to this file holds the same two thresholds.
THRESHOLDS = {"noul_act_at_or_above": 0.6, "answer_confidence_at_or_above": 0.7}

STATE = {
    "ticket": {
        "channel": "email",
        "subject": "Payouts have been failing since Monday",
        "message": (
            "My payouts have been failing since Monday. I already re-entered my bank details "
            "twice. I have supplier invoices due this week."
        ),
    },
    "customer": {"plan": "growth"},
}

# The option set and the level list are defined once here, so the check on the response reads the
# same keys and the same level count the question was built from.
QUEUE_OPTIONS = {
    "billing": "Charges, payouts, invoices, refunds.",
    "technical": "Bugs, outages, integrations, API errors.",
    "account": "Login, plan changes, team membership.",
    "other": None,
}

URGENCY_LEVELS = [
    "Can wait: no money or access is blocked this week.",
    "Time-boxed: money or access is blocked within the next few days.",
    "Blocking: the customer cannot operate and is losing money today.",
]


def build_questions() -> dict:
    """Return the question set, spelled the way the HTTP API reference spells it."""
    return {
        "needs_human": Noul(
            instructions="Does this ticket need a human agent, rather than an automated reply?",
            criteria={
                "true": "The customer asks for something only a person can decide.",
                "false": "The help article or the account data in state answers the question.",
            },
        ),
        "queue": Choice(
            instructions="Which queue should own this ticket?",
            criteria=QUEUE_OPTIONS,
        ),
        "urgency": Score(
            instructions="How urgent is this ticket for the customer right now?",
            criteria=URGENCY_LEVELS,
        ),
    }


def key_is_missing(name: str) -> bool:
    """Report whether an environment variable holds no value, without reading it out."""
    value = os.environ.get(name)
    return value is None or not value.strip()


def validated_signal(value: object) -> float | None:
    """Return the value only when it is a real number inside 0..1, else None."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    # An int can be far larger than a float can hold, and math.isfinite on such an int raises
    # OverflowError instead of answering, so the range check runs first and isfinite only for floats.
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if value < 0 or value > 1:
        return None
    return float(value)


def decision_for(question: str, value: object, threshold: float) -> tuple[str, float | None]:
    """Return the outcome and the signal; a signal that fails validation goes to review."""
    signal = validated_signal(value)
    if signal is None:
        return "review", None
    return ("act" if signal >= threshold else "review"), signal


def choice_is_allowed(value: object, option_keys: tuple[str, ...]) -> bool:
    """Report whether an answered choice is one of the option keys its question was built from."""
    return isinstance(value, str) and value in option_keys


def score_is_allowed(value: object, level_count: int) -> bool:
    """Report whether an answered score is a finite number inside 0..(level_count - 1)."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    # Same order as validated_signal: the exact int comparison comes before math.isfinite, which
    # would raise OverflowError on a Python int larger than a float can represent.
    if isinstance(value, float) and not math.isfinite(value):
        return False
    return 0 <= value <= level_count - 1


def answer_decision_for(
    question: str, value: object, threshold: float, allowed: bool
) -> tuple[str, float | None]:
    """Return the outcome and the signal, after checking the answer against the set it came from."""
    if not allowed:
        return "review", None
    return decision_for(question, value, threshold)


def main() -> None:
    if key_is_missing("TYPESAFE_API_KEY"):
        raise SystemExit(
            "TYPESAFE_API_KEY is not set. Export it in the calling shell; never paste the key "
            "into a file, a prompt, or a log."
        )

    with TypeSafeClient(model=MODEL) as client:
        response = client.system_one(state=STATE, questions=build_questions())

    # A noul answer is the yes probability, and the SDK types that value.
    # No confidence is typed, so each choice and score confidence comes from the raw body.
    raw_answers = response.raw_http_response.json()["answers"]
    needs_human = response.nouls["needs_human"].noul
    queue = response.choices["queue"]
    urgency = response.scores["urgency"]

    decisions = [
        ("needs_human", needs_human, THRESHOLDS["noul_act_at_or_above"], True),
        (
            "queue",
            raw_answers.get("queue", {}).get("confidence"),
            THRESHOLDS["answer_confidence_at_or_above"],
            choice_is_allowed(queue.choice, tuple(QUEUE_OPTIONS)),
        ),
        (
            "urgency",
            raw_answers.get("urgency", {}).get("confidence"),
            THRESHOLDS["answer_confidence_at_or_above"],
            score_is_allowed(urgency.score, len(URGENCY_LEVELS)),
        ),
    ]
    for question, value, threshold, allowed in decisions:
        outcome, signal = answer_decision_for(question, value, threshold, allowed)
        if signal is None:
            reason = (
                "the value is missing or outside 0..1, so a person decides"
                if allowed
                else "the value is missing or outside the allowed set, so a person decides"
            )
        elif outcome == "act":
            reason = "at or above the threshold"
        else:
            reason = "below the threshold"
        shown = "null" if signal is None else signal
        print(f"{question}: {outcome} (signal {shown}, threshold {threshold}) - {reason}")
    # An answer outside the set its question was built from is printed as invalid, never as itself.
    queue_allowed = choice_is_allowed(queue.choice, tuple(QUEUE_OPTIONS))
    urgency_allowed = score_is_allowed(urgency.score, len(URGENCY_LEVELS))
    print(f"Chosen queue: {queue.choice if queue_allowed else 'invalid'}")
    print(f"Urgency score: {urgency.score if urgency_allowed else 'invalid'}")


if __name__ == "__main__":
    if LIVE_CALL_APPROVED:
        main()
    else:
        print("No call was made. Set LIVE_CALL_APPROVED to true only after the user consents.")
