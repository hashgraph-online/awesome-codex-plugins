"""R01 - AI assistant: rich streaming with real stages, Stop, and one finalization.

Run:  py -3 examples/python/recipes/r01_ai_assistant.py      (offline, no token)
Shows five endings: completed, stopped (keep_marked / discard / offer_continue),
Stop racing completion, failure, timeout - plus late chunks and a repeated Stop.
"""
from __future__ import annotations

import _common as c
from tgkit.errors import TelegramError
from tgkit.generation import Generation, GenerationConfig, OperationRegistry, State, execute
from tgkit.router import Router, check_subscription
from tgkit.transport import FakeTransport, TelegramErrorResponse

CHAT = 111111111
DRAFT = 48127   # matches fixtures/stopped_message_generation.json


class FakeModel:
    """Stands in for the upstream LLM stream. cancel() must stop token spend."""

    def __init__(self) -> None:
        self.cancelled = False

    def cancel(self) -> None:
        self.cancelled = True


def run(policy: str = "keep_marked", ending: str = "stop", transport: FakeTransport | None = None):
    t = transport or FakeTransport()
    model = FakeModel()
    registry = OperationRegistry()
    gen = Generation(op_id="a1b2c3", chat_id=CHAT, draft_id=DRAFT,
                     config=GenerationConfig(stop_policy=policy, deadline=60.0))
    registry.add(gen)

    router = Router()

    @router.on("stopped_message_generation")
    def on_stop(upd):
        op = registry.find_for_stop(upd)
        if op is None:
            return "unknown_draft"            # expired or another process's draft
        execute(op.on_stop(clock[0]), t, op, now=clock[0], cancel_upstream=model.cancel)
        return "stopped"

    clock = [0.0]

    def at(ts, effects):
        clock[0] = ts
        execute(effects, t, gen, now=ts, cancel_upstream=model.cancel)

    at(0.0, gen.start(0.0))
    at(0.3, gen.on_stage("search", 0.3))           # coalesced: < min_interval
    at(1.2, gen.on_tick(1.2))                       # flushes the pending stage
    at(1.5, gen.on_chunk("Telegram added a Stop button to drafts. ", 1.5))
    at(1.9, gen.on_chunk("It is controlled by can_stop. ", 1.9))   # sentence end, but < 1 s
    at(2.6, gen.on_stage("write", 2.6))
    at(3.0, gen.on_chunk("\n\nkeep_on_stop keeps the partial draft visible for a short time", 3.0))

    if ending == "stop":
        router.dispatch(c.fixture("stopped_message_generation.json"))
        at(3.4, gen.on_chunk(" — this late chunk must be dropped.", 3.4))
        router.dispatch(c.fixture("stopped_message_generation.json"))   # repeated Stop
        at(4.0, gen.on_done(4.0))                                        # completion lost the race
    elif ending == "race_done_first":
        at(3.5, gen.on_done(3.5))
        router.dispatch(c.fixture("stopped_message_generation.json"))
    elif ending == "complete":
        at(3.5, gen.on_chunk(", then disappears.", 3.5))
        at(4.0, gen.on_done(4.0))
    elif ending == "error":
        at(3.5, gen.on_error(3.5))
    elif ending == "timeout":
        at(61.0, gen.on_tick(61.0))
    at(70.0, gen.on_tick(70.0))                     # stale timer after the end: no-op
    return t, gen, model, router


def main() -> None:
    router = Router()
    router.on("message")(lambda m: None)
    router.on("callback_query")(lambda q: None)
    router.on("stopped_message_generation")(lambda s: None)
    missing = check_subscription(["message", "callback_query"], router.allowed_updates())
    c.check(missing == ["stopped_message_generation"],
            "a fixed allowed_updates list silently drops the Stop update -> pass router.allowed_updates()")

    for policy in ("keep_marked", "discard", "offer_continue"):
        t, gen, model, _ = run(policy=policy, ending="stop")
        c.dump(t, f"Stop pressed, policy={policy}")
        finals = [p for m, p in t.calls if m in ("sendRichMessage", "sendMessage")]
        c.check(gen.outcome == State.STOPPED and len(finals) == 1, "exactly one finalization after Stop")
        c.check(model.cancelled, "upstream generation cancelled")
        c.check(gen.dropped_chunks == 1, "late chunk dropped, not appended")
        c.check(all("late chunk" not in str(p) for p in finals), "final message has no late text")
        drafts = t.params_of("sendRichMessageDraft")
        c.check(all(d["can_stop"] for d in drafts), "every draft offers Stop (can_stop)")
        c.check(all(d["keep_on_stop"] == (policy == "keep_marked") for d in drafts),
                "keep_on_stop only when the partial answer is kept")
        c.check(all(b["type"] != "thinking" for b in finals[0]["rich_message"]["blocks"]),
                "thinking block only in drafts")

    t, gen, *_ = run(ending="race_done_first")
    c.check(gen.outcome == State.COMPLETED and len(t.params_of("sendRichMessage")) == 1,
            "Stop after completion is a no-op (one final)")
    t, gen, *_ = run(ending="complete")
    drafts = t.params_of("sendRichMessageDraft")
    times = [d for d in drafts]
    c.check(len(drafts) <= 4, f"throttled: {len(drafts)} drafts for 6 events")
    for ending, state in (("error", State.FAILED), ("timeout", State.TIMED_OUT)):
        t, gen, model, _ = run(ending=ending)
        c.check(gen.outcome == state and gen.finalizations == 1 and model.cancelled,
                f"{ending}: distinct terminal state, one final, upstream cancelled")

    # 429 on a draft: the draft is dropped and the next one waits retry_after.
    t = FakeTransport().script("sendRichMessageDraft", {}, TelegramErrorResponse(429, "Too Many Requests: retry after 5", 5))
    gen = Generation(op_id="z9", chat_id=CHAT, draft_id=7)
    execute(gen.start(0.0), t, gen, now=0.0)
    execute(gen.on_chunk("A sentence that is long enough to flush now.", 1.1), t, gen, now=1.1)
    c.check(gen.not_before >= 6.1, "429 pushes the next draft past retry_after")
    c.check(gen.on_chunk(" More text.", 2.5) == [], "no draft inside the retry_after window")


if __name__ == "__main__":
    main()
