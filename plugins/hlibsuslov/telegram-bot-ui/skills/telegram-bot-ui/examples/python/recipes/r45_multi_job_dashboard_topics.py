"""R45 - Several parallel jobs: one private-chat topic per job + a live dashboard widget.

Each job gets its own topic in the operator's private chat (createForumTopic in
a private chat, Bot API 9.4+; topic links 10.4), so cards, questions and replies
never mix. The main chat holds one HTML widget (10.4, production: private chats
only) that shows every job; its state changes only through editMessageWidgetData.

Run:  py -3 examples/python/recipes/r45_multi_job_dashboard_topics.py
"""
from __future__ import annotations

import json

import _common as c
from agent_bridge.demo import OPERATOR, make_bridge, text_message
from agent_bridge.transport import DryRunTransport
from tgkit.topics import private_topic_link
from tgkit.widgets import check_widget, encode_state

DASHBOARD_HTML = """<!-- Job dashboard (private chat). chat_data = {"r":N,"j":[[name,state,stage],...]} -->
<style>body{margin:0}.r{display:flex;justify-content:space-between;padding:6px 12px;gap:8px}
.n{font-weight:600}.s{color:var(--tg-theme-hint-color);font-variant-numeric:tabular-nums}
.failed .s{color:var(--tg-theme-destructive-text-color)}</style>
<div id="list"></div>
<script>
var W=window.TelegramWidget,S={r:-1,j:[]};
function load(){var s=null;try{s=JSON.parse(W?W.chatData:null)}catch(e){}if(s&&s.r>S.r)S=s}
function draw(){var l=document.getElementById("list");l.textContent="";S.j.forEach(function(x){
 var d=document.createElement("div");d.className="r "+x[1];var n=document.createElement("span");n.className="n";
 n.textContent=x[0];var s=document.createElement("span");s.className="s";s.textContent=x[2]+" · "+x[1];
 d.appendChild(n);d.appendChild(s);l.appendChild(d)})}
if(W){W.onEvent("chatDataChanged",function(){load();draw()})}
load();draw();if(W)W.ready();
</script>"""
JOBS = {"build-142": ["Install", "Compile", "Test"], "migrate-7": ["Backup", "Migrate", "Verify"]}


class Dashboard:
    """One widget, edited only when the state changed and at most every 2 s (design heuristic)."""

    def __init__(self, bridge, min_interval: float = 2.0):
        self.b, self.min_interval = bridge, min_interval
        self.rev, self.last, self.last_at, self.message_id = 0, None, None, None

    def state(self, cards):
        return [[k, v["state"], v["current"] or "-"] for k, v in sorted(cards.items())]

    def publish(self, cards, *, force=False):
        rows = self.state(cards)
        if rows == self.last:
            return "same"
        now = self.b.clock()
        if not force and self.last_at is not None and now - self.last_at < self.min_interval:
            return "throttled"
        self.rev += 1
        data = encode_state({"r": self.rev, "j": rows})
        caption = "Jobs: " + ", ".join(f"{n} {s}" for n, s, _ in rows)      # chat list, search, old apps
        if self.message_id is None:
            rep = check_widget(DASHBOARD_HTML, caption=caption, chat_data=data, context="private")
            if not rep.ok:
                raise ValueError(rep.errors)
            msg = self.b.call("sendWidget", {"chat_id": OPERATOR, "html": DASHBOARD_HTML, "chat_data": data,
                                             "caption": caption})
            self.message_id = msg["message_id"]
        else:
            self.b.call("editMessageWidgetData", {"chat_id": OPERATOR, "message_id": self.message_id,
                                                  "chat_data": data})
        self.last, self.last_at = rows, now
        return "published"


def run():
    t = DryRunTransport().script("createForumTopic",
                                 {"message_thread_id": 7, "name": "build-142", "icon_color": 7322096},
                                 {"message_thread_id": 9, "name": "migrate-7", "icon_color": 16766590})
    b, _, clock = make_bridge(transport=t)
    topics = {}
    for job in JOBS:
        topics[job] = b.call("createForumTopic", {"chat_id": OPERATOR, "name": job})["message_thread_id"]
    dash = Dashboard(b)
    for job, stages in JOBS.items():
        b.progress(job, title=job, stages=stages, stage=stages[0], thread_id=topics[job], announce_final=False)
    dash.publish(b.store.data["cards"])
    outcomes = []
    for step in range(3):
        clock.sleep(1.5)
        b.progress("build-142", stage=JOBS["build-142"][step])
        outcomes.append(dash.publish(b.store.data["cards"]))
    clock.sleep(4)
    b.progress("migrate-7", stage="Migrate", state="failed", note="lock timeout on orders", announce_final=False)
    outcomes.append(dash.publish(b.store.data["cards"], force=True))
    # The operator types in the migrate-7 topic: the event carries that thread -> that job only.
    b.source.queue.append(text_message("why did it fail?", uid=970001, thread=topics["migrate-7"]))
    event = next(iter(b.listen(max_events=1)))
    job_for_event = {v: k for k, v in topics.items()}[event["message_thread_id"]]
    return t, topics, outcomes, job_for_event


def main() -> None:
    t, topics, outcomes, job = run()
    c.dump(t, "Multi-job dashboard with private-chat topics")
    cards = t.params_of("sendMessage")
    c.check({m.get("message_thread_id") for m in cards} == {7, 9}, "each job's card lives in its own topic")
    c.check(t.params_of("sendWidget")[0].get("message_thread_id") is None and
            t.params_of("sendWidget")[0]["caption"].startswith("Jobs:"),
            "the dashboard sits in the main chat, with a caption fallback")
    c.check(outcomes == ["same", "published", "throttled", "published"],
            f"widget edits only on change and >= 2 s apart: {outcomes}")
    last = json.loads(t.params_of("editMessageWidgetData")[-1]["chat_data"])
    c.check(["migrate-7", "failed", "Migrate"] in last["j"] and last["r"] >= 2, "state with a revision number")
    c.check(job == "migrate-7", "a message in a topic routes to that topic's job only")
    c.check(not check_widget(DASHBOARD_HTML, caption="Jobs", context="group").ok,
            "the same widget in a group: test server only - use cards there")
    c.check(private_topic_link("agent_demo_bot", topics["build-142"]) == "https://t.me/agent_demo_bot/7",
            "topic deep link (opens the topic only for this operator)")


if __name__ == "__main__":
    main()
