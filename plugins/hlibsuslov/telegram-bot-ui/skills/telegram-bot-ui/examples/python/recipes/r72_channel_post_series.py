"""R72 - A channel post series with premium accents and a safe fallback.

Three posts (release notes, a how-to, an event) built from one neutral post model with
`decorate_post`: one accent before the headline, one per section, bullets only in the
first list, one before the CTA, capped by a density budget. Channel eligibility (API): the
owner-Premium route covers private/group/supergroup only, so a channel needs the Fragment
route; without it the SAME posts go out with Unicode accents. A rich-message variant uses
RichTextCustomEmoji nodes in headings.

Run:  py -3 examples/python/recipes/r72_channel_post_series.py
"""
from __future__ import annotations

import _common as c
from icons.emoji_demo import VOCAB, resolve
from tgkit.icons import (DENSITY, Eligibility, IconSystem, SendContext, decorate_post, density_warnings,
                         strip_html)
from tgkit.transport import FakeTransport

CHANNEL = "@example_channel"
SLOTS = ["headline", "section", "bullet", "cta", "check_item", "cross_item", "callout", "announcement"]

POSTS = [
    {"headline": "Version 2.4 is out", "lead": "Faster sync and a calmer menu.",
     "sections": [{"title": "New", "bullets": ["Offline drafts", "Two-step delete"]},
                  {"title": "Fixed", "status": "done", "body": "Duplicate alerts after a restart."}],
     "cta": {"text": "Read the changelog", "url": "https://example.com/changelog"}},
    {"headline": "How to export your data", "sections": [
        {"title": "Steps", "bullets": ["Open Settings", "Tap Export", "Pick CSV"]},
        {"title": "Don't", "status": "fail", "body": "Share the export link in public chats."}],
     "cta": {"text": "Open the bot", "url": "https://t.me/example_bot?start=export"}},
    {"headline": "Live Q&A on Friday", "lead": "Bring your questions about the 2.4 release.",
     "sections": [{"title": "When", "body": "Friday, 18:00 UTC"}],
     "cta": {"text": "Add to calendar", "url": "https://example.com/qa.ics"}},
]


def icon_system(fragment: bool) -> IconSystem:
    icon_map, _ = resolve(["demo_line_icons", "demo_line_icons_extra"], SLOTS, family="demo-line")
    return IconSystem(icon_map["icons"], vocabulary=VOCAB,
                      eligibility=Eligibility(fragment_usernames=fragment, owner_premium=True))


def rich_post(view: IconSystem, post: dict) -> dict:
    blocks = [{"type": "heading", "size": 1, "text": view.rich_label("headline", post["headline"])}]
    for sec in post["sections"]:
        blocks.append({"type": "heading", "size": 3, "text": view.rich_label("section", sec["title"])})
        if sec.get("body"):
            blocks.append({"type": "paragraph", "text": sec["body"]})
    return {"chat_id": CHANNEL, "rich_message": {"blocks": blocks}}


def run(fragment: bool):
    icons = icon_system(fragment)
    view = icons.for_context(SendContext.channel())       # one decision for the whole post
    t = FakeTransport()
    for post in POSTS:
        params = {"chat_id": CHANNEL, **decorate_post(post, view)}
        icons.send(t, "sendMessage", params, SendContext.channel(), decorate=False)
    icons.send(t, "sendRichMessage", rich_post(view, POSTS[0]), SendContext.channel(), decorate=False)
    return t, view


def main() -> None:
    t, view = run(fragment=True)
    c.dump(t, "Channel post series (Fragment route)")
    texts = [p["text"] for p in t.params_of("sendMessage")]
    c.check(view.active and all("<tg-emoji" in x for x in texts), "Fragment usernames -> premium accents in channel posts")
    c.check(all(x.count("<tg-emoji") <= DENSITY["post_text"] and not density_warnings({"text": x}, post=True) for x in texts),
            "density: at most one accent per line and within the post budget (heuristic)")
    c.check(all("tg-emoji" not in line for x in texts for line in x.split("\n") if "<a href" in line and "</a>" in
                line.split("<a href")[0]), "no custom emoji inside links (API nesting rule)")
    heading = t.params_of("sendRichMessage")[0]["rich_message"]["blocks"][0]["text"]
    c.check(heading[0]["type"] == "custom_emoji" and heading[0]["alternative_text"],
            "rich heading carries RichTextCustomEmoji with its alternative emoji")
    t2, view2 = run(fragment=False)
    texts2 = [p["text"] for p in t2.params_of("sendMessage")]
    c.check(not view2.active and not any("<tg-emoji" in x for x in texts2),
            "owner Premium only -> channel posts go out with Unicode accents (route 2 excludes channels)")
    c.check([strip_html(x) for x in texts] == texts2,
            "the fallback post is the same post: what screen readers and old clients get is the alternative emoji")


if __name__ == "__main__":
    main()
