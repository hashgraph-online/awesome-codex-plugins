"""R70 - Restyle an existing bot from Unicode emoji to ONE premium pack.

The handlers stay as they are (Unicode emoji in labels and titles). The project's emoji are
mapped to slots, one family is resolved (primary set + its sibling for gaps), and every
outgoing request goes through IconSystem.send(), which rewrites labels to
icon_custom_emoji_id and titles to <tg-emoji> with the SAME id - or leaves everything as
Unicode when the message is not eligible.

Run:  py -3 examples/python/recipes/r70_restyle_to_premium.py
"""
from __future__ import annotations

import _common as c
from icons.emoji_demo import VOCAB, resolve
from tgkit.icons import Eligibility, IconSystem, SendContext, slots_in, uses_custom_emoji
from tgkit.transport import FakeTransport

CHAT = 111111111


# ---- the existing bot, untouched -------------------------------------------
def main_menu() -> dict:
    return {"chat_id": CHAT, "parse_mode": "HTML",
            "text": "<b>🏠 Main menu</b>\nWallets: <b>3</b> · Alerts: <b>on</b>",
            "reply_markup": {"inline_keyboard": [
                [{"text": "💼 Wallets", "callback_data": "wallets"}, {"text": "🔍 Search", "callback_data": "search"}],
                [{"text": "🔔 Notifications", "callback_data": "notif"}, {"text": "⚙️ Settings", "callback_data": "settings"}],
                [{"text": "❓ Help", "callback_data": "help"}]]}}


def settings_screen() -> dict:
    return {"chat_id": CHAT, "parse_mode": "HTML",
            "text": "<b>⚙ Settings</b>\nLanguage: <b>English</b>\n<code>user id 42 ✅</code>",
            "reply_markup": {"inline_keyboard": [
                [{"text": "🌐 Language", "callback_data": "lang"}],
                [{"text": "⬅️ Back", "callback_data": "home"}]]}}


SCREENS = [main_menu, settings_screen]


def run(eligible: bool = True):
    needed = slots_in([s() for s in SCREENS], VOCAB)
    icon_map, report = resolve(["demo_line_icons", "demo_line_icons_extra"], needed, family="demo-line")
    icons = IconSystem(icon_map["icons"], vocabulary=VOCAB, eligibility=Eligibility(owner_premium=eligible))
    t = FakeTransport()
    for screen in SCREENS:
        icons.send(t, "sendMessage", screen(), SendContext("private"))
    return t, icons, report, needed


def main() -> None:
    t, icons, report, needed = run()
    c.dump(t, "Restyle to one premium pack")
    c.check(set(needed) >= {"home", "wallets", "settings", "back"} and report["coverage"] == 1.0,
            f"{len(needed)} slots found in the existing screens, all covered by one family")
    menu = t.params_of("sendMessage")[0]
    buttons = [b for row in menu["reply_markup"]["inline_keyboard"] for b in row]
    c.check(all(b.get("icon_custom_emoji_id") for b in buttons) and not any(b["text"][0] in "💼🔍🔔⚙❓" for b in buttons),
            "every label got its icon and lost its Unicode emoji (no double icon)")
    home_id = icons.icons["home"]["id"]
    c.check(f'emoji-id="{home_id}"' in menu["text"], "the title uses the same family via <tg-emoji>")
    settings = t.params_of("sendMessage")[1]
    c.check("<code>user id 42 ✅</code>" in settings["text"], "emoji inside <code> stay untouched (API: no nesting)")
    c.check(f'emoji-id="{icons.icons["settings"]["id"]}"' in settings["text"],
            "'⚙' without VS16 matched the same slot as '⚙️'")
    t2, *_ = run(eligible=False)
    c.check(not any(uses_custom_emoji(p) for _, p in t2.calls) and t2.params_of("sendMessage")[0]["reply_markup"]
            == main_menu()["reply_markup"], "not eligible -> the original Unicode screens, unchanged")


if __name__ == "__main__":
    main()
