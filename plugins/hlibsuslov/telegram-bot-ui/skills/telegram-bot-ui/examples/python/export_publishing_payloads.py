"""Write examples/payloads/r3N-*.json from the publishing recipes (30-39).

Same format as export_payloads.py: the exact JSON each recipe puts on the wire,
captured by FakeTransport after a JSON round trip. `--check` fails on drift
(tests/test_publishing.py runs it).

Run:  py -3 examples/python/export_publishing_payloads.py [--check]
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "recipes"))
OUT = os.path.join(os.path.dirname(HERE), "payloads")

import r30_news_autoposter  # noqa: E402
import r31_long_read_rich_post  # noqa: E402
import r32_media_album_post  # noqa: E402
import r33_poll_quiz_post  # noqa: E402
import r34_pinned_daily_digest  # noqa: E402
import r35_editorial_approval  # noqa: E402
import r36_cross_post_variants  # noqa: E402
import r37_broadcast_mailing  # noqa: E402
import r38_comments_and_direct_messages  # noqa: E402
import r39_correct_published_post  # noqa: E402

SCENARIOS = {
    "r30-news-autoposter": (lambda: r30_news_autoposter.run()[0], "production", "channel"),
    "r31-long-read-rich-post": (lambda: r31_long_read_rich_post.run()[0], "production", "private preview + channel"),
    "r32-media-album-post": (lambda: r32_media_album_post.run()[0], "production", "channel"),
    "r33-poll-quiz-post": (lambda: r33_poll_quiz_post.run()[0], "production", "channel"),
    "r34-pinned-daily-digest": (lambda: r34_pinned_daily_digest.run()[0], "production", "channel"),
    "r35-editorial-approval": (lambda: r35_editorial_approval.run()[0], "production", "editor private chat + channel"),
    "r36-cross-post-variants": (lambda: r36_cross_post_variants.run()[0], "production", "several channels"),
    "r37-broadcast-mailing": (lambda: r37_broadcast_mailing.run()[0], "production", "private chats (subscribers)"),
    "r38-comments-and-direct-messages": (lambda: r38_comments_and_direct_messages.run()[0], "production",
                                         "discussion group + channel direct messages chat"),
    "r39-correct-published-post": (lambda: r39_correct_published_post.run()[0], "production", "channel"),
}


def build(name: str) -> dict:
    fn, status, context = SCENARIOS[name]
    with contextlib.redirect_stdout(io.StringIO()):
        transport = fn()
    return {
        "scenario": name,
        "status": status,
        "context": context,
        "evidence": "offline contract: captured from the recipe code via FakeTransport; not sent to Telegram",
        "bot_api": "10.4 (verified 2026-11-15)",
        "steps": [{"method": m, "params": p} for m, p in transport.calls],
    }


def main() -> int:
    check = "--check" in sys.argv
    drift = []
    for name in SCENARIOS:
        text = json.dumps(build(name), ensure_ascii=False, indent=2) + "\n"
        path = os.path.join(OUT, f"{name}.json")
        if check:
            if not os.path.exists(path) or open(path, encoding="utf-8").read() != text:
                drift.append(name)
        else:
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(text)
    if drift:
        print("payloads out of date:", ", ".join(drift))
        return 1
    print(f"{'checked' if check else 'wrote'} {len(SCENARIOS)} publishing payload files in {os.path.relpath(OUT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
