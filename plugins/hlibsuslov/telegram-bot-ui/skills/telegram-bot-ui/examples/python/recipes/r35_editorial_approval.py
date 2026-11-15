"""R35 - Editorial approval: draft -> preview in the editor's private chat ->
Approve / Edit / Reject -> exactly one channel post.

* The preview is the exact plan of the channel post, sent to the editor.
* Control buttons carry draft id AND version: a tap on an old preview can't
  publish an outdated text.
* Only allow-listed editors act; every callback is answered.
* Approve is idempotent (ledger key per draft version): a double tap posts once.
* Edit asks for the new text with force_reply and re-previews as v2.

Run:  py -3 examples/python/recipes/r35_editorial_approval.py
"""
from __future__ import annotations

from typing import Any

import _common as c
from tgkit.publish import Post, Publisher, plan
from tgkit.transport import FakeTransport

CHANNEL, CHANNEL_USERNAME = -1001500000001, "demo_city_news"
EDITORS = {111111111}


class ApprovalDesk:
    def __init__(self, transport: Any, publisher: Publisher, editors: set[int], channel_id: int):
        self.t, self.pub, self.editors, self.channel = transport, publisher, editors, channel_id
        self.drafts: dict[str, dict[str, Any]] = {}
        self.awaiting_text: dict[int, str] = {}       # editor id -> draft id

    def submit(self, draft_id: str, post: Post, editor_chat: int) -> None:
        self.drafts[draft_id] = {"post": post, "version": 1, "state": "draft", "chat": editor_chat}
        self._preview(draft_id)

    def _preview(self, draft_id: str) -> None:
        d = self.drafts[draft_id]
        for method, params in plan(d["post"], d["chat"]):          # exactly what the channel will get
            self.t.call(method, params)
        v = d["version"]
        self.t.call("sendMessage", {
            "chat_id": d["chat"], "text": f"Draft {draft_id} · v{v} → City News. The preview is above.",
            "reply_markup": {"inline_keyboard": [
                [{"text": "Approve and publish", "callback_data": f"pub:approve:{draft_id}:{v}", "style": "success"}],
                [{"text": "Edit text", "callback_data": f"pub:edit:{draft_id}:{v}"},
                 {"text": "Reject", "callback_data": f"pub:reject:{draft_id}:{v}", "style": "danger"}]]}})

    def on_callback(self, cq: dict[str, Any]) -> str:
        answer = {"callback_query_id": cq["id"]}
        try:
            _, action, draft_id, version = cq["data"].split(":")
        except ValueError:
            self.t.call("answerCallbackQuery", answer)
            return "ignored"
        d = self.drafts.get(draft_id)
        if cq["from"]["id"] not in self.editors or d is None:
            self.t.call("answerCallbackQuery", {**answer, "text": "Only editors can do this.", "show_alert": True})
            return "refused"
        if int(version) != d["version"] and d["state"] == "draft":
            self.t.call("answerCallbackQuery", {**answer, "text": f"Outdated preview: v{d['version']} is current.",
                                                "show_alert": True})
            return "stale"
        chat, mid = cq["message"]["chat"]["id"], cq["message"]["message_id"]
        if action == "approve":
            result = self.pub.publish(d["post"], self.channel, f"draft:{draft_id}:v{version}")
            if result.status == "already_sent":
                self.t.call("answerCallbackQuery", {**answer, "text": "Already published."})
                return "already_published"
            if result.status != "sent":
                self.t.call("answerCallbackQuery", {**answer, "text": "Publishing status unknown - check the channel.",
                                                    "show_alert": True})
                return result.status
            d["state"] = "published"
            self.t.call("answerCallbackQuery", {**answer, "text": "Published."})
            link = f"https://t.me/{CHANNEL_USERNAME}/{result.message_ids[0]}"
            self.t.call("editMessageText", {"chat_id": chat, "message_id": mid,
                                            "text": f"Draft {draft_id} · v{version} published by {cq['from']['first_name']}.",
                                            "reply_markup": {"inline_keyboard": [[{"text": "Open the post", "url": link}]]}})
            return "published"
        if action == "edit":
            self.awaiting_text[cq["from"]["id"]] = draft_id
            self.t.call("answerCallbackQuery", answer)
            self.t.call("sendMessage", {"chat_id": chat, "text": f"Send the corrected text for draft {draft_id}.",
                                        "reply_markup": {"force_reply": True, "input_field_placeholder": "New text"}})
            return "awaiting_text"
        if action == "reject":
            d["state"] = "rejected"
            self.t.call("answerCallbackQuery", {**answer, "text": "Rejected."})
            self.t.call("editMessageText", {"chat_id": chat, "message_id": mid,
                                            "text": f"Draft {draft_id} rejected by {cq['from']['first_name']}."})
            return "rejected"
        self.t.call("answerCallbackQuery", answer)
        return "ignored"

    def on_message(self, msg: dict[str, Any]) -> str:
        editor = msg["from"]["id"]
        draft_id = self.awaiting_text.get(editor)
        if not draft_id or not msg.get("reply_to_message") or editor not in self.editors:
            return "ignored"
        del self.awaiting_text[editor]
        d = self.drafts[draft_id]
        d["post"] = d["post"].with_changes(blocks=[d["post"].blocks[0], {"type": "paragraph", "text": msg["text"]}])
        d["version"] += 1
        self._preview(draft_id)
        return "re_previewed"


def run(transport: FakeTransport | None = None):
    t = transport or FakeTransport()
    pub = Publisher(t, sleep=lambda s: None)
    desk = ApprovalDesk(t, pub, EDITORS, CHANNEL)
    draft = Post(kind="text", blocks=[{"type": "heading", "text": "Tram line 4 reopens"},
                                      {"type": "paragraph", "text": "Night trams run on Saturday until 01:00."}],
                 buttons=[[{"text": "Timetable", "url": "https://example.com/tram4"}]])
    desk.submit("d42", draft, 111111111)
    desk.submit("d43", Post(kind="text", blocks=[{"type": "paragraph", "text": "Unconfirmed rumour about fares."}]),
                111111111)
    routes = []
    for u in c.fixture("r35_editor_updates.json"):
        routes.append(desk.on_callback(u["callback_query"]) if "callback_query" in u else desk.on_message(u["message"]))
    return t, routes, desk


def main() -> None:
    t, routes, desk = run()
    c.dump(t, "Editorial approval")
    c.check(routes == ["refused", "awaiting_text", "re_previewed", "stale", "published", "already_published", "rejected"],
            f"routes {routes}")
    channel_posts = [p for m, p in t.calls if p.get("chat_id") == CHANNEL]
    c.check(len(channel_posts) == 1 and "not Saturday" in channel_posts[0]["text"],
            "one channel post, with the corrected v2 text")
    c.check(len(t.params_of("answerCallbackQuery")) == 6, "every callback answered")
    prompt = next(p for p in t.params_of("sendMessage") if "force_reply" in p.get("reply_markup", {}))
    c.check(prompt["reply_markup"]["force_reply"] is True, "Edit asks for the text with force_reply")
    c.check(desk.drafts["d43"]["state"] == "rejected" and desk.drafts["d42"]["state"] == "published",
            "states: d42 published, d43 rejected")
    done = t.params_of("editMessageText")[0]
    c.check(done["reply_markup"]["inline_keyboard"][0][0]["url"].startswith("https://t.me/demo_city_news/"),
            "the control message turns into a link to the live post")


if __name__ == "__main__":
    main()
