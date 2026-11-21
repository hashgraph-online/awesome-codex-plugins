"""Call the decision API through the official Python SDK (typesafe-sdk).

Fill in: the INPUT record and the question set below, and the thresholds, which must stay in step
with constants.template.ts in this folder. The SDK reads the key from TYPESAFE_API_KEY, and
TYPESAFE_BASE_URL when it is set. A live call only after the user consents: nothing is sent until
LIVE_CALL_APPROVED is turned on, and the key is read from the environment at call time and never
printed.

Snapshot 2026-11-08, re-check before the first live call: references/providers.md and
references/official/jev-platform.md.
SDK notes: `typesafe-sdk` 0.7.5 (2026-10-14), Python 3.10 or newer. The client is `TypeSafeClient`
(synchronous) with `system_one(...)`; answers are readable as `response.answers[...]` and through the
convenience maps `response.nouls`, `response.choices`, and `response.scores`, with the raw body left
on `response.raw_http_response`. The retry policy defaults to two retries on 408, 429, and 5xx with a
bounded backoff, so this file adds none of its own.
"""

from __future__ import annotations

import math
import os

from typesafe_sdk import Choice, Noul, Score, TypeSafeClient

# Consent gate. Leave this false until the person has agreed to a live call and knows its cost.
LIVE_CALL_APPROVED = False

# Snapshot 2026-11-08, re-check before the first live call: this is the versioned id, because an alias
# moves when a release ships. The id appears once, here.
MODEL = "jev-1.14.0"

# The thresholds are pre-tuning assumptions, so evaluate them on your own labeled cases before trusting
# them. The TypeScript template next to this file holds the same three thresholds.
THRESHOLDS = {
    "boolean_act_at_or_above": 0.6,
    "choice_probability_at_or_above": 0.7,
    "score_confidence_at_or_above": 0.7,
}

INPUT = {
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

# The option set and the level list are defined once here, so the check on the response reads the same
# keys and the same level count the question was built from.
QUEUE_OPTIONS = {
    "billing": "Charges, payouts, invoices, refunds.",
    "technical": "Bugs, outages, integrations, API errors.",
    "account": "Login, plan changes, team membership.",
    "other": "A last resort: real work, but no listed queue describes it.",
}

URGENCY_LEVELS = [
    "Can wait: no money or access is blocked this week.",
    "Time-boxed: money or access is blocked within the next few days.",
    "Blocking: the customer cannot operate and is losing money today.",
]


def build_questions() -> dict:
    """Return the question set, spelled the way the HTTP API reference spells it."""
    return {
        # The yes/no type is named noul in this dialect; the AI SDK calls the same type boolean.
        "needs_human": Noul(
            instructions="Does this ticket need a human agent, rather than an automated reply?",
            criteria={
                "true": "The customer asks for something only a person can decide.",
                "false": "The help article or the account data in state answers the question.",
            },
        ),
        # The companion boolean: a choice always returns one of its options, so a separate question
        # asks whether any option fits at all.
        "any_queue_fits": Noul(
            instructions=(
                "Does this ticket belong to one of the queues listed in the companion routing "
                "question (billing, technical, account, other)?"
            ),
            criteria={
                "true": "At least one listed queue describes the work this ticket needs.",
                "false": "No listed queue describes it, so a person has to decide where it goes.",
            },
        ),
        "queue": Choice(
            instructions="Which queue should own this ticket? Pick the closest queue.",
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


def decision_for(question: str, value: object, threshold: float, why: str | None = None) -> tuple[str, float | None, str]:
    """Return the outcome, the signal, and the reason; a signal that fails validation goes to review."""
    signal = validated_signal(value)
    if signal is None:
        return "review", None, why or "the value is missing or outside 0..1, so a person decides"
    if signal >= threshold:
        return "act", signal, "at or above the threshold"
    return "review", signal, "below the threshold"


def choice_is_allowed(value: object, option_keys: tuple[str, ...]) -> bool:
    """Report whether an answered choice is one of the option keys its question was built from."""
    return isinstance(value, str) and value in option_keys


def score_is_allowed(value: object, level_count: int) -> bool:
    """Report whether an answered score is a finite number inside 0..(level_count - 1)."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    # Same order as validated_signal: the exact int comparison comes before math.isfinite, which would
    # raise OverflowError on a Python int larger than a float can represent.
    if isinstance(value, float) and not math.isfinite(value):
        return False
    return 0 <= value <= level_count - 1


def answer_decision_for(
    question: str, value: object, threshold: float, allowed: bool
) -> tuple[str, float | None, str]:
    """Return the outcome, signal, and reason, after checking the answer against the set it came from."""
    if not allowed:
        return "review", None, "the value is missing or outside the allowed set, so a person decides"
    return decision_for(question, value, threshold)


def confidence_of(answer: object) -> object:
    """Read an answer's confidence defensively.

    The API returns a confidence on choice and score answers and none on a boolean answer. The SDK
    answer models are not listed field by field in the snapshot, so this reads the attribute when the
    model carries it and returns None otherwise, which becomes a review rather than a guess.
    """
    return getattr(answer, "confidence", None)


def main() -> None:
    if key_is_missing("TYPESAFE_API_KEY"):
        raise SystemExit(
            "TYPESAFE_API_KEY is not set. Export it in the calling shell; never paste the key into a "
            "file, a prompt, or a log."
        )

    with TypeSafeClient(model=MODEL) as client:
        response = client.system_one(state=INPUT, questions=build_questions())

    # Log the model id that answered: an alias resolves to a version, and this is where it is recorded.
    print(f"answer from {getattr(response, 'model', 'unreported')} (requested {MODEL})")

    needs_human = response.nouls["needs_human"]
    any_queue_fits = response.nouls["any_queue_fits"]
    queue = response.choices["queue"]
    urgency = response.scores["urgency"]

    # Read the probability of the chosen option rather than its confidence: for a fixed option set the
    # confidence is a transform of that same top probability.
    queue_probability = None
    probabilities = getattr(queue, "probabilities", None)
    if isinstance(probabilities, dict) and isinstance(queue.choice, str):
        queue_probability = probabilities.get(queue.choice)

    decisions = [
        ("needs_human", needs_human.noul, THRESHOLDS["boolean_act_at_or_above"], True, None),
        ("any_queue_fits", any_queue_fits.noul, THRESHOLDS["boolean_act_at_or_above"], True, None),
        (
            "queue",
            queue_probability,
            THRESHOLDS["choice_probability_at_or_above"],
            choice_is_allowed(queue.choice, tuple(QUEUE_OPTIONS)),
            None,
        ),
        (
            "urgency",
            confidence_of(urgency),
            THRESHOLDS["score_confidence_at_or_above"],
            score_is_allowed(urgency.score, len(URGENCY_LEVELS)),
            "this route reported no confidence, so a person decides",
        ),
    ]
    review: list[str] = []
    for question, value, threshold, allowed, why in decisions:
        outcome, signal, reason = answer_decision_for(question, value, threshold, allowed)
        if signal is None and why is not None:
            reason = why
        shown = "null" if signal is None else signal
        print(f"{question}: {outcome} (signal {shown}, threshold {threshold}) - {reason}")
        if outcome != "act":
            review.append(question)
    if review:
        print(f"Send {', '.join(review)} to the human review path.")
    # An answer outside the set its question was built from is printed as invalid, never as itself.
    print(f"Chosen queue: {queue.choice if choice_is_allowed(queue.choice, tuple(QUEUE_OPTIONS)) else 'invalid'}")
    print(f"Urgency score: {urgency.score if score_is_allowed(urgency.score, len(URGENCY_LEVELS)) else 'invalid'}")


if __name__ == "__main__":
    if LIVE_CALL_APPROVED:
        main()
    else:
        print(f"No call was made. The request would carry {len(build_questions())} questions to {MODEL}.")
        print("Set LIVE_CALL_APPROVED to true only after the user consents; the SDK reads TYPESAFE_API_KEY and never prints it.")
