"""R30 - News autoposter: feed item -> channel post, exactly once.

A feed item becomes a structured post (title first, summary, source link, one
button), rendered as text + entities (hostile titles need no escaping), with an
explicit link preview. The first send times out: the publisher records
"unknown" and refuses to post again until the outcome is reconciled.

Run:  py -3 examples/python/recipes/r30_news_autoposter.py
"""
from __future__ import annotations

import hashlib

import _common as c
from tgkit.publish import Post, Publisher, plan, to_entities
from tgkit.transport import FakeTransport

CHANNEL = -1001500000001
FEED = [
    {"guid": "city-transport-4821", "title": "Tram line 4 <reopens> & runs until 01:00",
     "url": "https://example.com/news/4821?utm=feed&ref=\"tg\"",
     "summary": "Repairs on Bridge Street are finished two weeks early. Night trams start on Friday.",
     "source": "City Transport Office"},
    {"guid": "city-transport-4822", "title": "Трамвай №4 знову ходить — до 01:00",
     "url": "https://example.com/uk/news/4822",
     "summary": "Ремонт на мосту завершили на два тижні раніше.", "source": "Міський транспорт"},
]


def post_from_item(item: dict) -> Post:
    return Post(
        blocks=[{"type": "heading", "text": item["title"]},            # line 1 = notification + preview
                {"type": "paragraph", "text": item["summary"]},
                {"type": "paragraph", "text": ["Source: ", {"link": item["url"], "text": item["source"]}]}],
        buttons=[[{"text": "Read the full story", "url": item["url"]}]],
        link_preview={"url": item["url"], "large": True},
        kind="text",
    )


def item_key(item: dict) -> str:
    return "feed:" + hashlib.sha256(item["guid"].encode()).hexdigest()[:12]


def run(transport: FakeTransport | None = None):
    t = transport or FakeTransport().script("sendMessage", "TIMEOUT")
    pub = Publisher(t, sleep=lambda s: None, clock=lambda: 1_763_200_000.0)
    first, second = FEED
    out = [pub.publish(post_from_item(first), CHANNEL, item_key(first))]          # times out
    out.append(pub.publish(post_from_item(first), CHANNEL, item_key(first)))      # poller runs again
    # An operator (or a channel_post update) confirms the post exists as 5001.
    out.append(pub.reconcile(item_key(first), found_message_ids=[5001]))
    out.append(pub.publish(post_from_item(first), CHANNEL, item_key(first)))      # next poll
    out.append(pub.publish(post_from_item(second), CHANNEL, item_key(second)))
    return t, out, pub


def main() -> None:
    t, out, pub = run()
    c.dump(t, "News autoposter")
    c.check([r.status for r in out] == ["unknown", "unknown", "sent", "already_sent", "sent"],
            f"statuses {[r.status for r in out]}")
    c.check(len(t.params_of("sendMessage")) == 2, "two feed items -> two sendMessage calls, even after a timeout")
    p = t.params_of("sendMessage")[0]
    c.check(p["text"].startswith("Tram line 4 <reopens> & runs until 01:00\n"),
            "title is line 1 (notification / pinned preview), raw characters, no escaping needed")
    c.check(p["entities"][0] == {"type": "bold", "offset": 0, "length": 40}, "title is a bold entity (UTF-16 length)")
    c.check(p["link_preview_options"] == {"url": FEED[0]["url"], "prefer_large_media": True},
            "preview points at the article, large media")
    c.check(len(p["reply_markup"]["inline_keyboard"]) == 1, "one call to action")
    text, ents = to_entities(post_from_item(FEED[1]).blocks)
    c.check(all(e["offset"] + e["length"] <= len(text.encode("utf-16-le")) // 2 for e in ents),
            "Cyrillic item: entity offsets stay inside the UTF-16 text")
    preview = plan(post_from_item(FEED[0]), 111111111)
    c.check(preview[0][1]["chat_id"] == 111111111 and preview[0][1]["text"] == p["text"],
            "the same plan sent to a private chat is the exact preview")


if __name__ == "__main__":
    main()
