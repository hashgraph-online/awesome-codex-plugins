"""Controlled AI generation: draft streaming with Stop (Bot API 10.3).

`Generation` is a pure state machine. Every event returns a list of *effects*
(API calls to make, or "cancel the upstream model"); `execute()` applies them.
Keeping decisions pure makes races testable: two events processed in either
order must end in exactly one logical finalization.

States
    STARTED -> GENERATING -> COMPLETED            (model finished)
                          -> STOP_REQUESTED -> STOPPED   (user pressed Stop)
                          -> FAILED             (model / API error)
                          -> TIMED_OUT          (deadline passed)
Terminal states never change again. Late chunks, a second Stop, a Stop after
completion, a completion after Stop, a timer firing after the end - all no-ops.

"One logical finalization" is an application invariant. It is NOT a network
exactly-once guarantee: a final send that times out has an unknown outcome
(see errors.OutcomeUnknown and `execute(on_unknown=...)`).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Iterable

from .errors import OutcomeUnknown, TelegramError, call_with_policy


class State(str, Enum):
    STARTED = "started"
    GENERATING = "generating"
    STOP_REQUESTED = "stop_requested"
    STOPPED = "stopped"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMED_OUT = "timed_out"


TERMINAL = {State.STOPPED, State.COMPLETED, State.FAILED, State.TIMED_OUT}
STOP_POLICIES = ("discard", "keep_marked", "offer_continue")

# Real, user-meaningful stages. Model reasoning text never goes into a
# thinking block: only these labels (localize them through the project's i18n).
DEFAULT_STAGE_LABELS = {
    "start": "Starting…",
    "search": "Searching the sources…",
    "read": "Reading the documents…",
    "write": "Writing the answer…",
}
SENTENCE_END = re.compile(r"[.!?…。！？]\s*$")
RICH_TEXT_LIMIT = 32768        # Rich Message Limits (official)
PLAIN_DRAFT_LIMIT = 4096       # sendMessageDraft.text, after entity parsing


@dataclass
class GenerationConfig:
    rich: bool = True
    can_stop: bool = True
    stop_policy: str = "keep_marked"
    min_interval: float = 1.0      # seconds between drafts (design heuristic)
    min_new_chars: int = 40        # or a finished sentence (still waits for min_interval)
    deadline: float = 120.0        # seconds for the whole operation
    stage_labels: dict[str, str] = field(default_factory=lambda: dict(DEFAULT_STAGE_LABELS))
    texts: dict[str, str] = field(default_factory=lambda: {
        "stopped_note": "Stopped by you — the answer is incomplete.",
        "stopped_discarded": "Stopped. Nothing was saved.",
        "stopped_offer": "Stopped. Continue from here or start over?",
        "failed": "Couldn't finish the answer. Nothing was charged.",
        "timed_out": "This is taking too long, so I stopped.",
        "continue": "Continue",
        "retry": "Try again",
    })

    def __post_init__(self) -> None:
        if self.stop_policy not in STOP_POLICIES:
            raise ValueError(f"stop_policy must be one of {STOP_POLICIES}")


Effect = dict[str, Any]


class Generation:
    def __init__(self, *, op_id: str, chat_id: int, draft_id: int,
                 message_thread_id: int | None = None,
                 config: GenerationConfig | None = None, now: float = 0.0):
        if not draft_id:
            raise ValueError("draft_id must be non-zero")
        self.op_id = op_id
        self.chat_id = chat_id
        self.draft_id = draft_id
        self.thread_id = message_thread_id
        self.cfg = config or GenerationConfig()
        self.state = State.STARTED
        self.started_at = now
        self.buffer = ""
        self.flushed_len = 0
        self.last_flush_at: float | None = None
        self.not_before = 0.0
        self.stage = "start"
        self.stage_dirty = True
        self.dropped_chunks = 0
        self.finalizations = 0
        self.outcome: State | None = None
        self.transitions: list[tuple[float, str, str]] = []

    # ---- identity -----------------------------------------------------
    @property
    def key(self) -> tuple[int, int, int]:
        return (self.chat_id, self.thread_id or 0, self.draft_id)

    @property
    def terminal(self) -> bool:
        return self.state in TERMINAL

    def matches_stop(self, upd: dict[str, Any]) -> bool:
        """MessageGenerationStopped -> this operation? chat + thread + draft."""
        return (upd.get("chat", {}).get("id") == self.chat_id
                and (upd.get("message_thread_id") or 0) == (self.thread_id or 0)
                and upd.get("draft_id") == self.draft_id)

    # ---- events -------------------------------------------------------
    def start(self, now: float) -> list[Effect]:
        self._move(State.GENERATING, now)
        return self._draft(now)

    def on_stage(self, stage: str, now: float) -> list[Effect]:
        if self.terminal:
            return []
        self.stage = stage if stage in self.cfg.stage_labels else "write"
        self.stage_dirty = True
        return self._maybe_flush(now)

    def on_chunk(self, text: str, now: float) -> list[Effect]:
        if self.terminal or self.state == State.STOP_REQUESTED:
            self.dropped_chunks += 1        # late chunk after Stop / end
            return []
        self.buffer += text
        return self._maybe_flush(now) + self._check_deadline(now)

    def on_tick(self, now: float) -> list[Effect]:
        if self.terminal:
            return []                       # a stale timer must not revive the stream
        return self._check_deadline(now) or self._maybe_flush(now)

    def on_rate_limited(self, retry_after: float, now: float) -> None:
        # A rejected draft is simply dropped: the next flush carries newer text.
        self.not_before = max(self.not_before, now + retry_after)

    def on_stop(self, now: float) -> list[Effect]:
        if self.terminal or self.state == State.STOP_REQUESTED:
            return []                       # repeated Stop / Stop after the end
        self._move(State.STOP_REQUESTED, now)
        partial = self.buffer               # snapshot: later chunks never join it
        effects: list[Effect] = [{"cancel_upstream": True}]
        effects += self._finalize(State.STOPPED, now, partial)
        return effects

    def on_done(self, now: float) -> list[Effect]:
        if self.terminal or self.state == State.STOP_REQUESTED:
            return []                       # completion lost the race to Stop
        return self._finalize(State.COMPLETED, now, self.buffer)

    def on_error(self, now: float) -> list[Effect]:
        if self.terminal:
            return []
        return [{"cancel_upstream": True}] + self._finalize(State.FAILED, now, self.buffer)

    # ---- internals ----------------------------------------------------
    def _move(self, new: State, now: float) -> None:
        self.transitions.append((now, self.state.value, new.value))
        self.state = new

    def _check_deadline(self, now: float) -> list[Effect]:
        if self.terminal or now - self.started_at < self.cfg.deadline:
            return []
        return [{"cancel_upstream": True}] + self._finalize(State.TIMED_OUT, now, self.buffer)

    def _maybe_flush(self, now: float) -> list[Effect]:
        new = len(self.buffer) - self.flushed_len
        wants = self.stage_dirty or new >= self.cfg.min_new_chars or (
            new > 0 and SENTENCE_END.search(self.buffer) is not None)
        if not wants:
            return []
        earliest = self.not_before
        if self.last_flush_at is not None:
            earliest = max(earliest, self.last_flush_at + self.cfg.min_interval)
        if now < earliest:
            return []                       # coalesced; on_tick will flush later
        return self._draft(now)

    def _thread(self) -> dict[str, Any]:
        return {"message_thread_id": self.thread_id} if self.thread_id else {}

    def _draft(self, now: float) -> list[Effect]:
        self.last_flush_at = now
        self.flushed_len = len(self.buffer)
        self.stage_dirty = False
        common = {"chat_id": self.chat_id, **self._thread(), "draft_id": self.draft_id,
                  # Sent on every call: the spec does not say the flags persist
                  # between draft updates, and repeating them is harmless.
                  "can_stop": self.cfg.can_stop,
                  "keep_on_stop": self.cfg.stop_policy == "keep_marked"}
        if self.cfg.rich:
            label = self.cfg.stage_labels.get(self.stage, "Working…")
            blocks = [{"type": "thinking", "text": label}] + text_blocks(self.buffer)
            return [{"call": "sendRichMessageDraft",
                     "params": {**common, "rich_message": {"blocks": blocks}}}]
        preview = self.buffer[-PLAIN_DRAFT_LIMIT:]
        return [{"call": "sendMessageDraft", "params": {**common, "text": preview}}]

    def _buttons(self, *kinds: str) -> dict[str, Any]:
        row = [{"text": self.cfg.texts[k], "callback_data": f"gen:{k}:{self.op_id}"}
               for k in kinds]
        return {"inline_keyboard": [row]}

    def _final(self, blocks: list[dict[str, Any]], markup: dict | None) -> Effect:
        params: dict[str, Any] = {"chat_id": self.chat_id, **self._thread()}
        if self.cfg.rich:
            params["rich_message"] = {"blocks": blocks}   # no thinking block here
            method = "sendRichMessage"
        else:
            params["text"] = blocks_to_plain(blocks)
            method = "sendMessage"
        if markup:
            params["reply_markup"] = markup
        return {"call": method, "params": params, "final": True}

    def _finalize(self, outcome: State, now: float, text: str) -> list[Effect]:
        self.finalizations += 1
        self.outcome = outcome
        self._move(outcome, now)
        t = self.cfg.texts
        if outcome == State.COMPLETED:
            return [self._final(text_blocks(text) or [para("(empty answer)")], None)]
        if outcome == State.STOPPED:
            policy = self.cfg.stop_policy
            if policy == "keep_marked" and text.strip():
                blocks = text_blocks(text) + [{"type": "footer", "text": t["stopped_note"]}]
                return [self._final(blocks, self._buttons("continue", "retry"))]
            if policy == "offer_continue" and text.strip():
                return [self._final([para(t["stopped_offer"])], self._buttons("continue", "retry"))]
            return [self._final([para(t["stopped_discarded"])], self._buttons("retry"))]
        key = "failed" if outcome == State.FAILED else "timed_out"
        return [self._final([para(t[key])], self._buttons("retry"))]


def para(text: str) -> dict[str, Any]:
    # RichText as a plain String: model output can never become markup.
    return {"type": "paragraph", "text": text}


def text_blocks(text: str) -> list[dict[str, Any]]:
    parts = [p.strip() for p in re.split(r"\n\s*\n", text[:RICH_TEXT_LIMIT]) if p.strip()]
    return [para(p) for p in parts]


def blocks_to_plain(blocks: list[dict[str, Any]]) -> str:
    return "\n\n".join(str(b.get("text", "")) for b in blocks)


class OperationRegistry:
    """Active generations, keyed so parallel topics never cross."""

    def __init__(self) -> None:
        self._ops: dict[tuple[int, int, int], Generation] = {}

    def add(self, gen: Generation) -> None:
        chat, thread, _ = gen.key
        for other in self._ops.values():
            if other.key[:2] == (chat, thread) and not other.terminal:
                raise RuntimeError("a generation is already running in this chat/topic")
        self._ops[gen.key] = gen

    def find_for_stop(self, upd: dict[str, Any]) -> Generation | None:
        key = (upd.get("chat", {}).get("id"), upd.get("message_thread_id") or 0,
               upd.get("draft_id"))
        return self._ops.get(key)  # unknown / expired draft -> None, ignore safely


def execute(effects: Iterable[Effect], transport: Any, gen: Generation, *,
            now: float, cancel_upstream: Callable[[], None] = lambda: None,
            on_unknown: str = "raise", log: Callable[[dict], None] | None = None,
            sleep: Callable[[float], None] = lambda s: None) -> list[Any]:
    """Apply effects. Draft failures never end the operation; final failures
    get exactly one format fallback (rich -> plain, same chat and thread)."""
    results = []
    for eff in effects:
        if eff.get("cancel_upstream"):
            cancel_upstream()
            continue
        method, params = eff["call"], eff["params"]
        if not eff.get("final"):
            try:
                results.append(transport.call(method, params))
            except TelegramError as err:
                if err.category == "rate_limited":
                    gen.on_rate_limited(float(err.retry_after or 1), now)
                _log(log, gen, "draft_error", err.category)
            except OutcomeUnknown:
                _log(log, gen, "draft_error", "outcome_unknown")  # preview only
            continue
        results.append(_send_final(transport, method, params, gen, on_unknown, log, sleep))
    return results


def _send_final(transport, method, params, gen, on_unknown, log, sleep):
    try:
        return call_with_policy(transport, method, params, sleep=sleep, log=log)
    except OutcomeUnknown:
        _log(log, gen, "final_unknown", on_unknown)
        if on_unknown == "retry_once":   # acceptable for an AI answer: a rare
            return call_with_policy(transport, method, params, sleep=sleep, log=log)  # duplicate beats a loss
        raise                             # orders, payments: reconcile instead
    except TelegramError as err:
        if err.category == "validation" and method == "sendRichMessage":
            _log(log, gen, "fallback", "rich_to_plain")
            plain = {k: v for k, v in params.items() if k != "rich_message"}
            plain["text"] = blocks_to_plain(params["rich_message"]["blocks"])[:4096]
            return call_with_policy(transport, "sendMessage", plain, sleep=sleep, log=log)
        raise


def _log(log, gen: Generation, event: str, detail: str) -> None:
    if log:
        log({"event": event, "op": gen.op_id, "state": gen.state.value, "detail": detail})
