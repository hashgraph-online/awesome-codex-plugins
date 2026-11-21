"""R34 - Daily digest: one pinned post per day, edited in place.

The first run of a day publishes and pins the digest; later runs edit the same
message (editMessageText with rich_message) and send nothing when the content
did not change. A new day publishes a new digest, pins it and unpins the old.
Pinning in a channel needs can_edit_messages; channels never notify on pins.

Run:  py -3 examples/python/recipes/r34_pinned_daily_digest.py
"""
from __future__ import annotations

import _common as c
from tgkit.publish import Post, Publisher
from tgkit.transport import FakeTransport

CHANNEL = -1001500000001


def digest(day: str, items: list[tuple[str, str, str]]) -> Post:
    return Post(kind="rich", silent=True, blocks=[
        {"type": "heading", "text": f"Today in the city — {day}"},
        {"type": "table", "header": ["Time", "What", "Where"], "rows": [list(i) for i in items], "compact": True},
        {"type": "footer", "text": "Updated through the day. Tap a post in the channel for details."},
    ])


class DigestDesk:
    def __init__(self, publisher: Publisher, channel_id: int):
        self.pub, self.channel = publisher, channel_id
        self.current_key: str | None = None

    def update(self, day: str, items: list[tuple[str, str, str]]) -> str:
        key = f"digest:{day}"
        post = digest(day, items)
        if self.pub.ledger.get(key):
            return self.pub.edit(key, post).status          # "edited" or "unchanged"
        result = self.pub.publish(post, self.channel, key)
        if result.status != "sent":
            return result.status
        self.pub.pin(key)
        if self.current_key:
            self.pub.unpin(self.current_key)
        self.current_key = key
        return "published"


def run(transport: FakeTransport | None = None):
    t = transport or FakeTransport()
    desk = DigestDesk(Publisher(t, sleep=lambda s: None), CHANNEL)
    morning = [("09:00", "Farmers' market", "Cathedral Sq.")]
    noon = morning + [("13:00", "Road closed for repairs", "Bridge St.")]
    steps = [desk.update("15 Nov", morning),
             desk.update("15 Nov", morning),      # nothing new
             desk.update("15 Nov", noon),         # one more item
             desk.update("16 Nov", [("10:00", "Half marathon", "Riverside")])]
    return t, steps


def main() -> None:
    t, steps = run()
    c.dump(t, "Pinned daily digest")
    c.check(steps == ["published", "unchanged", "edited", "published"], f"steps {steps}")
    c.check(t.methods() == ["sendRichMessage", "pinChatMessage", "editMessageText",
                            "sendRichMessage", "pinChatMessage", "unpinChatMessage"],
            "unchanged run sends nothing; a new day pins the new and unpins the old")
    edit = t.params_of("editMessageText")[0]
    c.check(edit["message_id"] == 1001 and len(edit["rich_message"]["blocks"][1]["cells"]) == 3,
            "the same message (1001) is edited with the new table")
    c.check(t.params_of("unpinChatMessage")[0]["message_id"] == 1001, "yesterday's digest is unpinned by id")
    c.check("disable_notification" not in t.params_of("pinChatMessage")[0],
            "no disable_notification on pins: channels never notify about pins")


if __name__ == "__main__":
    main()
