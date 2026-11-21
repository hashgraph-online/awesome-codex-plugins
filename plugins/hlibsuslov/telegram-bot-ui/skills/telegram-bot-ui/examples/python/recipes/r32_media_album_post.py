"""R32 - Media album post (and a paid-media variant).

* An album caption is the caption of the FIRST item; one caption = one album text.
* sendMediaGroup takes no reply_markup: buttons go to a short silent follow-up.
* A caption over 1024 characters keeps whole blocks that fit; the rest becomes a
  follow-up text that carries the buttons (they stay on the last part).
* Paid media (sendPaidMedia) can't be copied - cross-post by sending anew.

Run:  py -3 examples/python/recipes/r32_media_album_post.py
"""
from __future__ import annotations

import _common as c
from tgkit.publish import Post, Publisher, validate
from tgkit.transport import FakeTransport

CHANNEL = -1001500000001
PHOTOS = ["AgACAgIAAxkBAAIBdemoPhotoMarket1", "AgACAgIAAxkBAAIBdemoPhotoMarket2", "AgACAgIAAxkBAAIBdemoPhotoMarket3"]


def album(extra_text: str = "") -> Post:
    blocks = [{"type": "heading", "text": "Winter market opens on Saturday"},
              {"type": "paragraph", "text": "40 stalls, hot cider and a skating rink on Cathedral Square, 10:00–22:00."}]
    if extra_text:
        blocks.append({"type": "paragraph", "text": extra_text})
    return Post(media=[{"type": "photo", "ref": PHOTOS[0]}, {"type": "photo", "ref": PHOTOS[1]},
                       {"type": "photo", "ref": PHOTOS[2], "spoiler": True}],
                blocks=blocks, caption_above=True, followup_text="Plan your visit:",
                buttons=[[{"text": "Map and opening hours", "url": "https://example.com/market"}]])


def _group_reply(start: int):
    counter = [start]

    def reply(method, params):
        out = []
        for _ in params["media"]:
            counter[0] += 1
            out.append({"message_id": counter[0], "date": 0, "chat": {"id": params["chat_id"], "type": "channel"},
                        "media_group_id": "13800000000000001"})
        return out
    return reply


def run(transport: FakeTransport | None = None):
    t = transport or FakeTransport().script("sendMediaGroup", _group_reply(6000), _group_reply(6100))
    pub = Publisher(t, sleep=lambda s: None)
    short = pub.publish(album(), CHANNEL, "album:market")
    long_caption = "Stall list: " + ", ".join(f"stall {i} (crafts, food, gifts)" for i in range(1, 45)) + "."
    overflow = pub.publish(album(long_caption), CHANNEL, "album:market:full")
    paid = Post(kind="paid_media", stars=50, paid_payload="backstage-2026-11",
                media=[{"type": "photo", "ref": PHOTOS[0]}, {"type": "video", "ref": "BAACAgIAAxkBAAIBdemoVideo"}],
                blocks=[{"type": "paragraph", "text": "Backstage: how the rink was built (2 photos + video)"}],
                caption_above=False)
    paid_result = pub.publish(paid, CHANNEL, "paid:backstage")
    return t, pub, short, overflow, paid_result, long_caption


def main() -> None:
    t, pub, short, overflow, paid_result, long_caption = run()
    c.dump(t, "Album post + paid media")
    groups = t.params_of("sendMediaGroup")
    first = groups[0]["media"]
    c.check(first[0]["caption"].startswith("Winter market opens on Saturday") and
            all("caption" not in m for m in first[1:]), "one caption, on the first item")
    c.check(first[0].get("show_caption_above_media") is True and first[2].get("has_spoiler") is True,
            "caption above media; spoiler on the third photo only")
    c.check("reply_markup" not in groups[0], "no reply_markup on sendMediaGroup (the API has none)")
    follow = t.params_of("sendMessage")
    c.check(follow[0]["text"] == "Plan your visit:" and follow[0]["disable_notification"] is True and
            follow[0]["reply_markup"]["inline_keyboard"][0][0]["url"] == "https://example.com/market",
            "buttons ride on a silent follow-up message")
    c.check(short.status == "sent" and short.message_ids == [6001, 6002, 6003, short.message_ids[3]],
            "ledger keeps all album ids + the follow-up id")
    c.check(len(groups[1]["media"][0]["caption"]) <= 1024 and long_caption not in groups[1]["media"][0]["caption"],
            "a long caption keeps the blocks that fit in 1024 characters")
    c.check(follow[1]["text"].startswith("Stall list:") and "reply_markup" in follow[1] and
            follow[1]["link_preview_options"] == {"is_disabled": True},
            "overflow text carries the buttons; no extra link preview")
    paid = t.params_of("sendPaidMedia")[0]
    c.check(paid["star_count"] == 50 and paid["payload"] == "backstage-2026-11" and len(paid["media"]) == 2,
            "paid media: star_count, internal payload, photo + video")
    try:
        pub.copy_to("paid:backstage", -1001500000002, "paid:backstage@ru")
        c.check(False, "copying paid media must be refused")
    except ValueError:
        c.check(True, "copyMessage can't copy paid media: refused before the call")
    eleven = album().with_changes(media=[{"type": "photo", "ref": PHOTOS[0]}] * 11)
    c.check(any(i.code == "album_size" for i in validate(eleven)), "11 items refused (albums take 2-10)")
    mixed = album().with_changes(media=[{"type": "photo", "ref": PHOTOS[0]}, {"type": "document", "ref": "BQACdoc"}])
    c.check(any(i.code == "album_mix" for i in validate(mixed)), "documents can't mix with photos in one album")
    local = album().with_changes(media=[{"type": "photo", "ref": "C:\\photos\\a.jpg"}, {"type": "photo", "ref": PHOTOS[1]}])
    c.check(any(i.code == "media_ref" for i in validate(local)), "a local path is never sent as a media ref")


if __name__ == "__main__":
    main()
