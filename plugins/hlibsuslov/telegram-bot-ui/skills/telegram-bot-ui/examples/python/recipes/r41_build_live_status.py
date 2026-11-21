"""R41 - Long build/test run: one live status card, then a final report and the log.

A 12-minute CI run emits ~200 progress events. The operator sees ONE message
that changes in place (named stages, throttled), a short notice when it ends,
a Rich Message report with a compact table, and the full log as a document.

Run:  py -3 examples/python/recipes/r41_build_live_status.py
"""
from __future__ import annotations

import os
import tempfile

import _common as c
from agent_bridge.demo import make_bridge

STAGES = ["Install", "Compile", "Unit tests", "E2E tests", "Package"]
TIMELINE = [("Install", 40), ("Compile", 95), ("Unit tests", 180), ("E2E tests", 400)]   # seconds per stage


def run():
    b, t, clock = make_bridge()
    events = 0
    b.progress("ci-142", title="CI #142 · shop-api", stages=STAGES, stage="Install")
    for stage, seconds in TIMELINE:
        for i in range(0, seconds, 4):                     # the runner reports every 4 s...
            clock.sleep(4)
            events += 1
            note = f"{stage}: step {i // 4 + 1}" if stage != "E2E tests" else f"E2E: {min(60, i // 6)}/60 specs"
            b.progress("ci-142", stage=stage, note=note)   # ...the card absorbs it
    clock.sleep(3)
    b.progress("ci-142", stage="E2E tests", state="failed", note="3 of 60 E2E specs failed (checkout)")
    report = {"title": "CI #142 — failed at E2E tests",
              "summary": "Unit and integration are green. 3 checkout specs time out after the payment form change.",
              "table": {"header": ["Stage", "Result", "Time"],
                        "rows": [["Install", "passed", "40s"], ["Compile", "passed", "1m 35s"],
                                 ["Unit tests", "812 passed", "3m 00s"], ["E2E tests", "57/60", "6m 40s"]]},
              "items": [{"text": "checkout.spec.ts › pays with saved card", "done": False},
                        {"text": "checkout.spec.ts › applies coupon", "done": False}],
              "log_tail": "TimeoutError: waited 30000ms for #pay\n  at checkout.spec.ts:88"}
    rep = b.report(data=report)
    with tempfile.TemporaryDirectory() as d:
        log = os.path.join(d, "ci-142.log")
        with open(log, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(f"[{i:04d}] step ok" for i in range(2000)) + "\nTimeoutError: waited 30000ms\n")
        sent = b.send_file(log, caption="CI #142 full log (2001 lines)")
    return t, events, rep, sent


def main() -> None:
    t, events, rep, sent = run()
    c.dump(t, "Long build with a live status card")
    edits = t.params_of("editMessageText")
    c.check(events == 179 and len(edits) <= 720 // 15 + len(STAGES),
            f"{events} runner events -> {len(edits)} edits (stage changes >= 3 s apart, note-only >= 15 s)")
    c.check(len([m for m, _ in t.calls if m == "sendMessage"]) == 2,
            "one card + one end notice (edits don't notify); no message per event")
    c.check("❌ E2E tests" in edits[-1]["text"] and edits[-1]["text"].count("✅") == 3,
            "the final card names the failed stage; earlier stages are done")
    rich = t.params_of("sendRichMessage")[0]["rich_message"]["blocks"]
    c.check([b["type"] for b in rich] == ["heading", "paragraph", "table", "list", "details"],
            "report = heading, summary, table, checklist, collapsed log tail")
    c.check(rep["format"] == "rich" and sent["name"] == "ci-142.log", "report as a Rich Message, log as a document")
    c.check(t.params_of("sendDocument")[0]["document"] == "attach://document", "multipart upload, never pasted text")


if __name__ == "__main__":
    main()
