"""R44 - Streamed research answer with Stop that cancels the agent's own work.

The agent streams a long answer as a draft (sendRichMessageDraft, can_stop).
The operator presses Stop: the model stream is closed, queued tool calls are
cancelled, and one final message keeps the partial answer, marked as stopped.

Run:  py -3 examples/python/recipes/r44_streamed_research_stop.py
"""
from __future__ import annotations

import _common as c
from agent_bridge.demo import START, make_bridge

STOP = c.fixture("agent_stop_generation.json")


class ResearchJob:
    """Stands in for the agent's work: a model stream plus tool calls it would run next."""

    def __init__(self, clock):
        self.clock = clock
        self.tool_calls_cancelled = False
        self.stream_closed = False
        self.tokens_after_stop = 0

    def cancel(self) -> None:          # the agent's own cancellation path
        self.tool_calls_cancelled = True

    def chunks(self):
        try:
            yield ("stage", "search")
            for i in range(40):
                self.clock.sleep(0.5)
                if self.tool_calls_cancelled:
                    self.tokens_after_stop += 1
                yield f"Finding {i + 1}: Bot API 10.4 widgets are private-chat only in production. "
        finally:
            self.stream_closed = True        # generator.close() lands here: no more tokens are requested


def run(stop: bool = True):
    updates = [dict(STOP, _at=START + 6.0)] if stop else []
    b, t, clock = make_bridge(updates)
    job = ResearchJob(clock)
    res = b.stream_answer(job.chunks(), on_cancel=job.cancel)
    return t, res, job


def main() -> None:
    t, res, job = run()
    c.dump(t, "Streamed answer, stopped by the operator")
    drafts = t.params_of("sendRichMessageDraft")
    c.check(drafts and all(d["can_stop"] and d["draft_id"] == 40001 for d in drafts),
            "every draft has can_stop and the same draft_id (matches the Stop update)")
    c.check(len(drafts) <= 8, f"{len(drafts)} drafts for ~12 chunks: throttled, never per token")
    c.check(res["outcome"] == "stopped" and res["upstream_cancelled"], "Stop -> STOPPED, upstream cancelled")
    c.check(job.tool_calls_cancelled and job.stream_closed and job.tokens_after_stop == 0,
            "Stop cancels queued tool calls and closes the model stream - nothing runs after it")
    finals = t.params_of("sendRichMessage")
    c.check(len(finals) == 1 and res["finalizations"] == 1, "exactly one final message")
    t2, res2, _ = run(stop=False)
    c.check(res2["outcome"] == "completed" and len(t2.params_of("sendRichMessage")) == 1,
            "without Stop the same code completes with one final message")


if __name__ == "__main__":
    main()
