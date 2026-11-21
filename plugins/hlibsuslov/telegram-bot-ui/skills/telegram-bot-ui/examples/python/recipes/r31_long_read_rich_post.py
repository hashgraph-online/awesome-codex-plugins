"""R31 - Long read as one Rich Message: headings, compact table, expandable
quote, attached document, embedded buttons.

A text longer than 4096 characters would need splitting as a regular message;
as a Rich Message it is ONE post (up to 32768 characters, 500 blocks). The
same plan is sent to the editor's private chat as a preview first.

Run:  py -3 examples/python/recipes/r31_long_read_rich_post.py
"""
from __future__ import annotations

import _common as c
from tgkit.publish import LIMITS, Post, Publisher, plan, resolve_kind, rich_size, to_entities, validate
from tgkit.transport import FakeTransport

CHANNEL = -1001500000001
EDITOR = 111111111
PDF_FILE_ID = "BQACAgIAAxkBAAIBdemoReportPdf"

INTRO = ("Every quarter we compare how fast the five city districts fix potholes after a report. "
         "This issue covers July to September 2026. ")
METHOD = ("We counted every report submitted through the city app and the hotline, then matched it with the "
          "closing record in the maintenance system. Reports closed as duplicates were removed. ")


def long_read() -> Post:
    return Post(blocks=[
        {"type": "heading", "text": "Potholes Q3 2026: Riverside is fastest, Old Town still slowest"},
        {"type": "paragraph", "text": INTRO * 14},
        {"type": "heading", "text": "Days from report to repair"},
        {"type": "table", "header": ["District", "Reports", "Median days", "Change"],
         "rows": [["Riverside", "412", "3.1", "−1.2"], ["Hillside", "388", "4.0", "−0.4"],
                  ["Harbour", "295", "5.6", "+0.3"], ["Northgate", "510", "6.2", "−0.9"],
                  ["Old Town", "640", "9.8", "+1.1"]],
         "numeric": [1, 2, 3], "compact": True, "caption": "Median, 1 Jul – 30 Sep 2026"},
        {"type": "heading", "text": "How we counted"},
        {"type": "paragraph", "text": METHOD * 14},
        {"type": "quote", "expandable": True, "credit": "Maintenance department, 2 Oct 2026",
         "text": "Old Town streets are narrow and the repair crew needs a traffic permit for each job. "
                 "From November permits will be issued for a whole week at once, which should cut two to "
                 "three days from the median."},
        {"type": "document", "ref": PDF_FILE_ID, "caption": "Full data set (PDF, 14 pages)"},
        {"type": "divider"},
        {"type": "footer", "text": ["Data: city open data portal. ", {"italic": "Next issue in January."}]},
    ], buttons=[[{"text": "Report a pothole", "url": "https://example.com/report", "style": "primary"},
                 {"text": "Copy data link", "copy_text": "https://example.com/data/q3-2026"}]])


def run(transport: FakeTransport | None = None):
    t = transport or FakeTransport()
    post = long_read()
    pub = Publisher(t, sleep=lambda s: None)
    preview = pub.publish(post, EDITOR, "longread:q3:preview")        # the editor sees the exact post
    live = pub.publish(post, CHANNEL, "longread:q3")
    # The same content authored as Rich Markdown and as Rich HTML (one source each),
    # previewed side by side so an editor can compare the three authoring formats.
    for source in ("markdown", "html"):
        pub.publish(post.with_changes(rich_source=source), EDITOR, f"longread:q3:preview:{source}")
    return t, post, preview, live


def main() -> None:
    t, post, preview, live = run()
    c.dump(t, "Long read as a Rich Message")
    c.check(resolve_kind(post) == "rich", "tables + several headings -> rich")
    sends = t.params_of("sendRichMessage")
    c.check(len(sends) == 4 and sends[0]["rich_message"] == sends[1]["rich_message"],
            "preview and channel post are byte-identical rich payloads")
    md, html = sends[2]["rich_message"], sends[3]["rich_message"]
    c.check(set(md) == {"markdown", "media"} and set(html) == {"html", "media"} and md["media"] == html["media"],
            "exactly one source field per InputRichMessage; the PDF goes through media + tg://document?id=")
    c.check(md["markdown"].startswith("# Potholes Q3 2026") and "<table bordered compact>" in md["markdown"] and
            "<blockquote expandable>" in md["markdown"] and "![](tg://document?id=doc1" in md["markdown"],
            "Rich Markdown: Markdown headings/paragraphs, HTML tags for compact table and expandable quote")
    c.check(html["html"].startswith("<h1>Potholes Q3 2026") and '<tg-document src="tg://document?id=doc1">' in html["html"]
            and "<tg-button-row>" in html["html"], "Rich HTML: one tag set for everything, buttons included")
    blocks = sends[1]["rich_message"]["blocks"]
    types = [b["type"] for b in blocks]
    c.check(types[0] == "heading" and blocks[0]["size"] == 1, "first block is the title (largest heading)")
    c.check({"table", "expandable_blockquote", "document", "buttons", "footer", "divider"} <= set(types),
            "table, expandable quote, document, divider, footer and a button row are real blocks")
    table = next(b for b in blocks if b["type"] == "table")
    c.check(table.get("is_compact") is True and table["cells"][1][2]["align"] == "right",
            "compact table, numbers right-aligned")
    chars, n, media = rich_size(blocks)
    plain_len = len(to_entities([b for b in post.blocks if b["type"] in ("heading", "paragraph")])[0])
    c.check(plain_len > LIMITS["text"] and chars <= LIMITS["rich_chars"] and n <= LIMITS["rich_blocks"],
            f"{plain_len} chars of prose (> 4096): one rich post instead of a split ({chars} chars, {n} blocks)")
    c.check("link_preview_options" not in sends[1] and "reply_markup" not in sends[1],
            "sendRichMessage has no link_preview_options; buttons are embedded blocks")
    c.check(live.status == "sent" and preview.status == "sent", "both sent once")
    bad = post.with_changes(buttons=[[{"text": "Open app", "web_app": {"url": "https://example.com/app"}}]])
    c.check(any(i.code == "button_context" for i in validate(bad, context="channel")),
            "a web_app button is refused for a channel (private chats only)")
    c.check(plan(post, CHANNEL)[0][0] == "sendRichMessage", "plan is one request")


if __name__ == "__main__":
    main()
