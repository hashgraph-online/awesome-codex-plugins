"""Error classes and the retry policy shared by every recipe.

The point of this module is to keep five failure classes apart, because each
one needs a different reaction:

* validation   - our payload is wrong (400). Fix it; never resend unchanged.
* unsupported  - the method/field does not exist on this server/SDK (404, or a
                 400 that names an unknown method/field). Use a fallback path.
* permission   - 403, or a 400 that says the bot lacks a right. Stop for this
                 chat; surface it.
* rate_limited - 429 with retry_after. Wait at least retry_after, bounded.
* outcome_unknown - the request may or may not have been executed (timeout,
                 connection reset after the body was sent). A non-idempotent
                 send must NOT be blindly repeated: it can duplicate.

Two more 400 sub-classes are not real failures and are reported separately:
`not_modified` (the edit is already in place) and `query_too_old` (a callback
or widget query answered after its deadline).
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable


class OutcomeUnknown(Exception):
    """The request may have been executed. Reconcile before repeating."""

    def __init__(self, method: str, reason: str = "timeout"):
        super().__init__(f"{method}: outcome unknown ({reason})")
        self.method = method
        self.reason = reason


@dataclass
class TelegramError(Exception):
    method: str
    error_code: int
    description: str
    retry_after: float | None = None

    def __str__(self) -> str:  # never includes the token or the payload
        return f"{self.method}: {self.error_code} {self.description}"

    @property
    def category(self) -> str:
        return classify(self.error_code, self.description)


# Narrow on purpose: "chat not found" / "message to edit not found" are
# validation errors about OUR payload, not missing capabilities. An unknown
# method comes back as HTTP 404 "Not Found".
_UNSUPPORTED_HINTS = ("method not found", "unknown method", "unsupported",
                      "not supported", "can't parse field")
_PERMISSION_HINTS = ("not enough rights", "need administrator rights",
                     "chat_write_forbidden", "have no rights",
                     "not allowed to send", "bot was blocked")


def classify(error_code: int, description: str) -> str:
    d = description.lower()
    if error_code == 429:
        return "rate_limited"
    if error_code == 403:
        return "permission"
    if error_code == 404:
        return "unsupported"
    if error_code >= 500:
        return "server"
    if error_code == 400:
        if "message is not modified" in d:
            return "not_modified"
        if "query is too old" in d or "query id is invalid" in d:
            return "query_too_old"
        if any(h in d for h in _PERMISSION_HINTS):
            return "permission"
        if any(h in d for h in _UNSUPPORTED_HINTS):
            return "unsupported"
        return "validation"
    return "validation"


def from_response(method: str, body: dict[str, Any]) -> TelegramError:
    params = body.get("parameters") or {}
    return TelegramError(
        method=method,
        error_code=int(body.get("error_code", 0)),
        description=str(body.get("description", "")),
        retry_after=params.get("retry_after"),
    )


# Methods whose repetition cannot create a second visible artefact. Edits and
# answers are safe to repeat (a repeated edit yields `not_modified`); every
# send* / copy* / forward* call is not.
_IDEMPOTENT_PREFIXES = ("edit", "answer", "get", "delete", "set")


def is_idempotent(method: str) -> bool:
    return method.startswith(_IDEMPOTENT_PREFIXES)


@dataclass
class RetryPolicy:
    max_attempts: int = 3
    base_backoff: float = 1.0   # seconds, used when retry_after is missing
    max_wait: float = 60.0      # never sleep longer than this in one step


def call_with_policy(
    transport: Any,
    method: str,
    params: dict[str, Any],
    *,
    policy: RetryPolicy | None = None,
    sleep: Callable[[float], None] = time.sleep,
    log: Callable[[dict[str, Any]], None] | None = None,
) -> Any:
    """Call `method` honouring the failure classes above.

    * 429: waits max(retry_after, backoff) - never a tight loop - then retries
      up to `max_attempts` in total.
    * 5xx / OutcomeUnknown: retried only for idempotent methods. For a send,
      OutcomeUnknown is re-raised so the caller reconciles (e.g. looks for the
      message it may already have sent) instead of duplicating it.
    * not_modified: treated as success for edits.
    * everything else: raised immediately.
    """
    policy = policy or RetryPolicy()
    attempt = 0
    while True:
        attempt += 1
        try:
            return transport.call(method, params)
        except TelegramError as err:
            cat = err.category
            _log(log, method, attempt, cat)
            if cat == "not_modified" and method.startswith("edit"):
                return True
            if cat == "rate_limited" and attempt < policy.max_attempts:
                wait = max(float(err.retry_after or 0), policy.base_backoff * attempt)
                if wait > policy.max_wait:
                    raise        # a long flood wait: let the caller reschedule, never retry early
                sleep(wait)
                continue
            if cat == "server" and is_idempotent(method) and attempt < policy.max_attempts:
                sleep(min(policy.base_backoff * 2 ** (attempt - 1), policy.max_wait))
                continue
            raise
        except OutcomeUnknown:
            _log(log, method, attempt, "outcome_unknown")
            if is_idempotent(method) and attempt < policy.max_attempts:
                sleep(min(policy.base_backoff * 2 ** (attempt - 1), policy.max_wait))
                continue
            raise


def _log(log, method: str, attempt: int, category: str) -> None:
    # Structured, token-free, payload-free: enough to see the decision.
    if log:
        log({"event": "api_error", "method": method, "attempt": attempt,
             "class": category})
