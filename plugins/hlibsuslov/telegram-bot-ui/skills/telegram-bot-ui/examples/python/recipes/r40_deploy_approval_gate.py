"""R40 - Deploy approval gate: the agent may not deploy until the operator taps Approve.

Three runs: approved -> deploy runs; rejected -> nothing runs; no answer -> expires,
nothing runs. Plus the attacks a gate must survive: a teammate's tap, a forged
nonce, a double tap.

Run:  py -3 examples/python/recipes/r40_deploy_approval_gate.py
"""
from __future__ import annotations

import _common as c
from agent_bridge.demo import OPERATOR, TEAM_GROUP, TEAMMATE, make_bridge, tap

PLAN = "Deploy shop-api v1.4.0 → production\n3 migrations · 41 files changed · CI green"
DETAILS = "0041_add_index (online), 0042_backfill_orders (~2 min), 0043_drop_legacy_col (irreversible)"


def deploy_with_gate(bridge, decide):
    """`decide(rec)` returns the updates that will arrive (taps). Returns (result, deployed)."""
    bridge.progress("deploy-1.4.0", title="Deploy v1.4.0", stages=["Checks", "Approval", "Migrate", "Release"],
                    stage="Approval")
    rec = bridge.request_approval(PLAN, details=DETAILS, ttl=900, destructive=True)
    bridge.source.queue.extend(decide(rec))
    result = bridge.wait(rec["rid"])
    while bridge.source.queue:                 # late taps still get an answer
        bridge.pump()
    deployed = result["decision"] == "approved"
    bridge.clock.sleep(5)
    if deployed:
        bridge.progress("deploy-1.4.0", stage="Release", state="done", note="v1.4.0 is live")
    else:
        bridge.progress("deploy-1.4.0", stage="Approval", state="failed",
                        note=f"Not deployed: {result['decision']}")
    return result, deployed


def run():
    b1, t1, _ = make_bridge()
    r1, d1 = deploy_with_gate(b1, lambda rec: [tap(rec, "d", uid=950001), tap(rec, "a", uid=950002),
                                               tap(rec, "a", uid=950003)])
    b2, t2, _ = make_bridge()
    r2, d2 = deploy_with_gate(b2, lambda rec: [tap(rec, "r", uid=950011)])
    b3, t3, _ = make_bridge()
    r3, d3 = deploy_with_gate(b3, lambda rec: [])
    b4, t4, _ = make_bridge(members={TEAMMATE}, groups={TEAM_GROUP})
    rec = b4.request_approval(PLAN, ttl=600, chat_id=TEAM_GROUP, destructive=True)
    forged = tap(rec, "a", uid=950021)
    forged["callback_query"]["data"] = forged["callback_query"]["data"].replace(rec["nonce"], "nZZZZZZZ")
    b4.source.queue.extend([tap(rec, "a", user=TEAMMATE, uid=950022), forged, tap(rec, "a", uid=950023)])
    r4 = b4.wait(rec["rid"])
    return t1, {"approved": (r1, d1), "rejected": (r2, d2), "expired": (r3, d3), "group": (r4, t4)}


def main() -> None:
    t, runs = run()
    c.dump(t, "Deploy approval gate (approved run)")
    (r1, d1), (r2, d2), (r3, d3) = runs["approved"], runs["rejected"], runs["expired"]
    c.check(d1 and not d2 and not d3, "deploy runs only after Approve; reject and timeout run nothing")
    c.check((r2["decision"], r3["decision"]) == ("rejected", "expired"), "distinct endings: rejected vs expired")
    gate = t.params_of("sendMessage")[1]
    rows = gate["reply_markup"]["inline_keyboard"]
    c.check(rows[-1] == [rows[-1][0]] and rows[-1][0]["style"] == "danger" and "style" not in rows[0][0],
            "irreversible deploy: Approve is red and alone in the last row, Reject is plain (color by meaning)")
    answers = [a["text"] for a in t.params_of("answerCallbackQuery")]
    c.check(answers == [DETAILS, "Approved", "Already recorded"],
            "Details informs, Approve decides once, the double tap is a no-op")
    closing = [e for e in t.params_of("editMessageText") if "disabled" in str(e.get("reply_markup"))]
    c.check(closing[0]["reply_markup"]["inline_keyboard"] == [[{"text": "Approved by Alice", "disabled": {}}]],
            "after the decision the card shows one disabled button with the result")
    r4, t4 = runs["group"]
    c.check(r4["by"] == OPERATOR and r4["decision"] == "approved",
            "in a group only the operator's id decides; teammate and forged taps are refused")
    refused = [a for a in t4.params_of("answerCallbackQuery") if a.get("show_alert")]
    c.check(refused and refused[0]["text"] == "You can't decide this request", "the teammate is told privately (alert)")


if __name__ == "__main__":
    main()
