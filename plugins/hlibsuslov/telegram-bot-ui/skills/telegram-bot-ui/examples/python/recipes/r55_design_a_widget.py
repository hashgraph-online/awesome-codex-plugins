"""R55 - Design a new widget from a user request, end to end:
decide the surface -> budget -> state model -> build for the user's language -> send -> test.

Request: "Let me set a price alert for TON right in the chat, with a slider, in Russian."

Run:  py -3 examples/python/recipes/r55_design_a_widget.py
"""
from __future__ import annotations

import json
import os
import sys

import _common as c
from tgkit.router import Router
from tgkit.transport import FakeTransport
from tgkit.widgets import encode_state
from widget_gallery import SPECS, GalleryBot

sys.path.insert(0, os.path.join(os.path.dirname(c.ROOT), "scripts"))
import build_widget  # noqa: E402

USER = 111111111


def choose_surface(need: dict) -> str:
    """references/widget-patterns.md section 1, first matching row wins."""
    if need.get("typed_text") or need.get("network") or need.get("tall"):
        return "mini_app"
    if need.get("place") != "private":
        return "keyboard_or_rich_message"     # production widgets: private chat with the bot only
    if need.get("mostly_text"):
        return "rich_message"
    if need.get("one_choice"):
        return "inline_keyboard"
    if need.get("changes_in_place") or need.get("custom_control"):
        return "widget"
    return "inline_keyboard"


def run(transport: FakeTransport | None = None):
    t = transport or FakeTransport()
    # 1) Decide: a slider and a card that changes in place, in the user's private chat.
    need = {"place": "private", "custom_control": True, "changes_in_place": True}
    surface = choose_surface(need)
    # 2) State model: what the widget draws, nothing more; prices in cents (no float drift).
    spec = SPECS["price-alert"]
    state_text = encode_state(spec.state("saved"))
    # 3) Build for the user's language (from.language_code = "ru"): one language per document.
    with open(os.path.join(build_widget.SRC_DIR, "price-alert.html"), encoding="utf-8") as fh:
        src = fh.read()
    ru = build_widget.build_text(src, caption=spec.demo["caption"], strict=True, langs=("ru",))
    en = build_widget.build_text(src, caption=spec.demo["caption"], strict=True, langs=("en",))
    # 4) Send the Russian build; the keyboard is the plain alternative.
    bot = GalleryBot(t)
    msg = bot.send("price-alert", USER, html=ru.html)
    # 5) Test the contract: an absolute set, a repeat (same alert again), and invalid data.
    router = Router()
    router.on("widget_query")(bot.handle)
    for i, data in enumerate(["set:above:5.90:once", "set:above:5.90:once", "set:up:5.90:once"]):
        upd = c.fixture("widget_query_sync.json")
        upd["widget_query"].update({"id": f"81234567890123550{i:02d}", "message_id": msg["message_id"],
                                    "data": data, "from": {**upd["widget_query"]["from"], "language_code": "ru"}})
        router.dispatch(upd)
    return t, surface, state_text, ru, en


def main() -> None:
    t, surface, state_text, ru, en = run()
    c.dump(t, "Design a widget: price alert")
    c.check(surface == "widget", "decision guide: a custom control that changes in place -> widget")
    c.check(len(state_text.encode()) <= 900, f"state {len(state_text.encode())} B leaves room for the answer envelope")
    c.check(ru.ok and en.ok, "strict build passes in both languages")
    c.check(ru.compressed_bytes <= 3800 and en.compressed_bytes <= 3800,
            f"working budget: ru {ru.compressed_bytes} B, en {en.compressed_bytes} B (limit 4096)")
    c.check(t.params_of("sendWidget")[0]["html"] == ru.html, "the user gets the build in their language")
    answers = [json.loads(p["data"]) for p in t.params_of("answerWidgetQuery")]
    c.check(answers[0]["ok"] and not answers[0].get("err"), "saving an alert succeeds")
    c.check(answers[1]["r"] == answers[0]["r"], "an absolute action repeated changes nothing (idempotent)")
    c.check(answers[2]["err"] == "bad_request", "untrusted data is checked like callback_data")
    c.check(len(t.params_of("editMessageWidgetData")) == 1, "one state edit for one real change")


if __name__ == "__main__":
    main()
