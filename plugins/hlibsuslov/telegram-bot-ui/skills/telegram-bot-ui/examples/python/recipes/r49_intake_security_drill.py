"""R49 - Intake and security drill: long polling, restart, strangers, injection, unknown chats.

One polling loop meets everything hostile at once and must: drop strangers
silently, keep text as data, leave unknown groups, refuse a forged approval,
survive a restart without replaying or losing updates, and accept webhooks only
with the secret header.

Run:  py -3 examples/python/recipes/r49_intake_security_drill.py
"""
from __future__ import annotations

import json
import os
import tempfile

import _common as c
from agent_bridge.demo import make_bridge
from agent_bridge.intake import ALLOWED_UPDATES, PollingSource, webhook_events
from agent_bridge.security import Allowlist
from agent_bridge.store import JsonStore
from agent_bridge.transport import DryRunTransport

BATCH = [c.fixture("agent_commands.json")["updates"][0],           # /status from the operator
         c.fixture("agent_stranger_message.json"),                  # stranger with the operator's name
         c.fixture("agent_added_to_unknown_group.json"),
         {**c.fixture("agent_injection_reply.json"), "update_id": 910105}]


def poller(store, batches):
    t = DryRunTransport().script("getUpdates", *batches)
    b, _, _ = make_bridge(transport=t, store=store)
    b.source = b.intake.source = PollingSource(b.call, store, allowed_updates=list(ALLOWED_UPDATES))
    return b, t


def run():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "state.json")
        b1, t1 = poller(JsonStore(path), [BATCH])
        b1.pump(25)
        events = list(b1.inbox)
        # Crash and restart: Telegram re-sends the last batch (offset not yet confirmed
        # server-side) plus one new update.
        b2, t2 = poller(JsonStore(path), [BATCH + [c.fixture("agent_commands.json")["updates"][1]]])
        b2.pump(25)
        replayed = list(b2.inbox)
        offset_used = t2.params_of("getUpdates")[0]["offset"]
    secret = "drill-" + "s" * 24
    store = JsonStore()
    body = json.dumps(c.fixture("agent_commands.json")["updates"][0]).encode()
    hook = [webhook_events({}, body, secret, store, Allowlist({111111111})),
            webhook_events({"X-Telegram-Bot-Api-Secret-Token": secret}, body, secret, store, Allowlist({111111111})),
            webhook_events({"X-Telegram-Bot-Api-Secret-Token": secret}, body, secret, store, Allowlist({111111111}))]
    return t1, events, b1, replayed, offset_used, hook


def main() -> None:
    t, events, b, replayed, offset, hook = run()
    c.dump(t, "Intake drill (first poll)")
    p = t.params_of("getUpdates")[0]
    c.check(p["allowed_updates"] == ALLOWED_UPDATES and p["timeout"] == 25,
            "long polling with an explicit allowed_updates (it is sticky server-side)")
    c.check([e["type"] for e in events] == ["command", "reply"], "operator command + operator text reach the agent")
    c.check(events[1]["content_is_untrusted_data"] and "override" in events[1]["injection_signals"],
            "pasted instructions are data, labelled, and executed by nobody")
    c.check(b.intake.stats["rejected"] == 1, "the stranger (same display name, other id) is dropped silently")
    c.check(t.methods()[1:] == ["leaveChat", "sendMessage"], "unknown group: leave, then tell the operator")
    c.check(offset == 910106 and [e["update_id"] for e in replayed] == [910011],
            "after a restart: persisted offset, replayed updates skipped, the new one handled once")
    c.check([h[0] for h in hook] == [401, 200, 200] and hook[2][1] == [],
            "webhook: 401 without the secret header; a redelivery yields nothing")


if __name__ == "__main__":
    main()
