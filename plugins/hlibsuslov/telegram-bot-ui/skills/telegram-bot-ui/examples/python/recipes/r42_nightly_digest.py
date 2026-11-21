"""R42 - Nightly job digest: one quiet report in the morning, loud only on failure.

Run:  py -3 examples/python/recipes/r42_nightly_digest.py
"""
from __future__ import annotations

import _common as c
from agent_bridge.demo import make_bridge
from tgkit.transport import TelegramErrorResponse

JOBS = [("backup-db", "passed", "4m 12s", ""), ("reindex-search", "passed", "18m 40s", ""),
        ("sync-crm", "failed", "1m 03s", "HTTP 503 from CRM, 3 retries"), ("cleanup-tmp", "passed", "12s", "")]


def digest(jobs) -> dict:
    failed = [j for j in jobs if j[1] != "passed"]
    return {"title": f"Nightly jobs · 15 Nov · {len(jobs) - len(failed)}/{len(jobs)} passed",
            "summary": ("All jobs passed." if not failed else
                        "Needs attention: " + ", ".join(f"{j[0]} ({j[3]})" for j in failed)),
            "table": {"header": ["Job", "Result", "Time"], "rows": [[j[0], j[1], j[2]] for j in jobs]}}


def send_digest(bridge, jobs):
    data = digest(jobs)
    failed = any(j[1] != "passed" for j in jobs)
    res = bridge.report(data=data, silent=not failed)       # quiet when green
    if failed:
        bridge.notify("Nightly: sync-crm failed — details in the digest above.")   # one loud line
    return res


def run():
    b, t, _ = make_bridge()
    ok = send_digest(b, [j for j in JOBS if j[1] == "passed"])
    bad = send_digest(b, JOBS)
    old = make_bridge(transport=None)[1]
    old.script("sendRichMessage", TelegramErrorResponse(404, "Not Found: method not found"))
    b3, _, _ = make_bridge(transport=old)
    fallback = send_digest(b3, JOBS)
    return t, ok, bad, fallback, old


def main() -> None:
    t, ok, bad, fallback, old = run()
    c.dump(t, "Nightly digest")
    rich = t.params_of("sendRichMessage")
    c.check(rich[0].get("disable_notification") is True and "disable_notification" not in rich[1],
            "green night: silent digest; a failure: a normal notification")
    c.check(len(t.params_of("sendMessage")) == 1, "exactly one extra loud line on failure, none when green")
    table = rich[1]["rich_message"]["blocks"][2]
    c.check(table["type"] == "table" and len(table["cells"]) == 5, "a real table, not a monospace grid")
    c.check(fallback["format"] == "plain" and "sync-crm | failed" in old.params_of("sendMessage")[0]["text"],
            "server/SDK without rich messages: the same digest as plain text, logged as a fallback")


if __name__ == "__main__":
    main()
