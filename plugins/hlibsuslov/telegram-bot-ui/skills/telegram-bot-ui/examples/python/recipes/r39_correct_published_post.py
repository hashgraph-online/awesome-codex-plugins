"""R39 - Correcting a published post: edit, delete-and-repost, or a note.

Decision (`decide_correction`):
* nothing changed            -> no request at all
* same layout (kind, parts)  -> edit in place: keeps views, reactions, comments
* layout must change, post is young (default < 15 min) -> delete + repost
* layout must change, post is older, or the post is paid -> reply with a
  visible correction note (deleteMessage only works for 48 h; a paid post must
  stay 24 h and can't be edited)

Run:  py -3 examples/python/recipes/r39_correct_published_post.py
"""
from __future__ import annotations

import _common as c
from tgkit.publish import Post, Publisher, decide_correction
from tgkit.transport import FakeTransport

CHANNEL = -1001500000001


def original() -> Post:
    return Post(kind="text", blocks=[{"type": "heading", "text": "Water outage on Monday"},
                                     {"type": "paragraph", "text": "Streets: Lime St. 1–20, Oak St. 3–9. From 09:00 to 15:00."}])


class Corrector:
    def __init__(self, publisher: Publisher):
        self.pub = publisher

    def correct(self, key: str, new_post: Post, note: str) -> str:
        rec = self.pub.ledger.get(key)
        decision = decide_correction(rec, new_post, self.pub.clock())
        if decision == "edit":
            self.pub.edit(key, new_post)
        elif decision == "repost":
            self.pub.delete(key)
            self.pub.publish(new_post, rec["chat_id"], key + "#r1")
        elif decision == "append_note":
            self.pub.t.call("sendMessage", {"chat_id": rec["chat_id"], "text": note,
                                            "reply_parameters": {"message_id": rec["message_ids"][0]}})
        return decision


def run(transport: FakeTransport | None = None):
    t = transport or FakeTransport()
    now = [1_763_200_000.0]
    pub = Publisher(t, sleep=lambda s: None, clock=lambda: now[0])
    fix = Corrector(pub)
    pub.publish(original(), CHANNEL, "outage:mon")
    decisions = []
    typo = original().with_changes(blocks=[original().blocks[0], {"type": "paragraph",
                                   "text": "Streets: Lime St. 1–20, Oak St. 3–9. From 09:00 to 13:00."}])
    decisions.append(fix.correct("outage:mon", typo, "Correction: until 13:00."))
    decisions.append(fix.correct("outage:mon", typo, "unused"))                      # already fixed
    now[0] += 5 * 60
    with_map = typo.with_changes(kind="photo", media=[{"type": "photo", "ref": "AgACAgIAAxkBAAIBdemoOutageMap"}])
    decisions.append(fix.correct("outage:mon", with_map, "unused"))                  # young: repost
    pub.publish(original().with_changes(blocks=[{"type": "paragraph", "text": "Bridge St. closed on Tuesday."}]),
                CHANNEL, "closure:tue")
    now[0] += 2 * 3600
    as_photo = original().with_changes(kind="photo", media=[{"type": "photo", "ref": "AgACAgIAAxkBAAIBdemoBridge"}],
                                       blocks=[{"type": "paragraph", "text": "Bridge St. closed on Wednesday."}])
    decisions.append(fix.correct("closure:tue", as_photo, "Correction: the closure is on Wednesday, not Tuesday."))
    return t, decisions, pub


def main() -> None:
    t, decisions, pub = run()
    c.dump(t, "Correcting published posts")
    c.check(decisions == ["edit", "unchanged", "repost", "append_note"], f"decisions {decisions}")
    c.check(t.methods() == ["sendMessage", "editMessageText", "deleteMessages", "sendPhoto", "sendMessage", "sendMessage"],
            "edit in place; unchanged sends nothing; repost = delete + new post; old post gets a reply note")
    c.check(t.params_of("editMessageText")[0]["message_id"] == 1001, "the typo is fixed in the same message")
    c.check(t.params_of("deleteMessages")[0] == {"chat_id": CHANNEL, "message_ids": [1001]}, "young post deleted by id")
    note = t.params_of("sendMessage")[-1]
    c.check(note["reply_parameters"] == {"message_id": 1003} and note["text"].startswith("Correction:"),
            "older post: a visible correction replying to the original")
    c.check(pub.ledger.get("outage:mon")["state"] == "deleted" and pub.ledger.get("outage:mon#r1")["state"] == "sent",
            "ledger tracks the deleted post and its replacement")
    paid = dict(pub.ledger.get("closure:tue"), paid_post=True)
    c.check(decide_correction(paid, original(), 0) == "append_note", "paid posts are never edited or deleted early")


if __name__ == "__main__":
    main()
