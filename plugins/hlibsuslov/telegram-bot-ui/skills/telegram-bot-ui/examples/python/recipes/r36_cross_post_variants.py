"""R36 - Cross-posting one story to several channels, per-language variants.

* One logical post, one idempotency key per target channel: a re-run after a
  partial failure fills only the gaps.
* Translated variants are sent as new posts (own text, own button labels).
* An identical post to a partner channel uses copyMessage (no "forwarded from"
  header, same formatting, new buttons allowed); forwardMessage keeps the
  attribution but fails for protected content.

Run:  py -3 examples/python/recipes/r36_cross_post_variants.py
"""
from __future__ import annotations

import _common as c
from tgkit.publish import Post, Publisher, cross_post
from tgkit.transport import FakeTransport, TelegramErrorResponse

EN, RU, UK, PARTNER = -1001500000001, -1001500000002, -1001500000003, -1001500000009


def story() -> Post:
    return Post(kind="text", lang="en",
                blocks=[{"type": "heading", "text": "New bike lanes on 12 streets"},
                        {"type": "paragraph", "text": "Work starts on 1 December and ends before spring."}],
                buttons=[[{"text": "See the map", "url": "https://example.com/bike?lang=en"}]])


TARGETS = [
    {"chat_id": EN},
    {"chat_id": RU, "lang": "ru", "changes": {
        "blocks": [{"type": "heading", "text": "Новые велодорожки на 12 улицах"},
                   {"type": "paragraph", "text": "Работы начнутся 1 декабря и закончатся до весны."}],
        "buttons": [[{"text": "Открыть карту", "url": "https://example.com/bike?lang=ru"}]]}},
    {"chat_id": UK, "lang": "uk", "changes": {
        "blocks": [{"type": "heading", "text": "Нові велодоріжки на 12 вулицях"},
                   {"type": "paragraph", "text": "Роботи почнуться 1 грудня й завершаться до весни."}],
        "buttons": [[{"text": "Відкрити мапу", "url": "https://example.com/bike?lang=uk"}]]}},
]


def run(transport: FakeTransport | None = None):
    t = transport or FakeTransport().script(
        "sendMessage", {"message_id": 7001, "date": 0, "chat": {"id": EN, "type": "channel"}},
        {"message_id": 7002, "date": 0, "chat": {"id": RU, "type": "channel"}},
        TelegramErrorResponse(403, "Forbidden: bot is not a member of the channel chat"),
        {"message_id": 7003, "date": 0, "chat": {"id": UK, "type": "channel"}})
    t.script("copyMessage", {"message_id": 880})
    pub = Publisher(t, sleep=lambda s: None)
    first = cross_post(pub, story(), TARGETS, "story:bike-lanes")
    # The admin adds the bot to the Ukrainian channel; the job runs again. A "failed"
    # record means nothing was posted, so publish() may try it again.
    second = cross_post(pub, story(), TARGETS, "story:bike-lanes")
    copied = pub.copy_to(f"story:bike-lanes@{EN}", PARTNER, "story:bike-lanes@partner",
                         reply_markup={"inline_keyboard": [[{"text": "Subscribe to City News",
                                                             "url": "https://t.me/demo_city_news"}]]})
    again = pub.copy_to(f"story:bike-lanes@{EN}", PARTNER, "story:bike-lanes@partner")
    return t, first, second, copied, again


def main() -> None:
    t, first, second, copied, again = run()
    c.dump(t, "Cross-posting with variants")
    c.check({k: r.status for k, r in first.items()} == {str(EN): "sent", str(RU): "sent", str(UK): "failed"},
            "first run: UK fails with 403, the others are posted")
    c.check({k: r.status for k, r in second.items()} == {str(EN): "already_sent", str(RU): "already_sent",
                                                          str(UK): "sent"}, "re-run fills only the gap")
    sends = t.params_of("sendMessage")
    c.check(len(sends) == 4 and sends[1]["text"].startswith("Новые") and
            sends[1]["reply_markup"]["inline_keyboard"][0][0]["text"] == "Открыть карту",
            "each language has its own text and button labels")
    cp = t.params_of("copyMessage")
    c.check(len(cp) == 1 and cp[0]["from_chat_id"] == EN and cp[0]["message_id"] == 7001 and
            "reply_markup" in cp[0], "partner channel: copyMessage with its own button")
    c.check(copied.status == "sent" and again.status == "already_sent", "a second copy is skipped")


if __name__ == "__main__":
    main()
