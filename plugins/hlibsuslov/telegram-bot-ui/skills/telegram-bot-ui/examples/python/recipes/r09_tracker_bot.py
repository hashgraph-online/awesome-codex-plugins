"""R09 - Monitoring bot upgraded to 10.3/10.4 (case study: btc-tracker).

One live confirmation card per transaction (a widget updated silently) instead of four
separate messages; a shared BTC price ticker; a compact table for address verification;
a short list (not a table) for wallet analysis; disabled numbers that are already taken;
a name step with buttons + reply field; one icon family for buttons and titles; and a
classic text fallback where widgets are unavailable.

Run:  py -3 examples/python/recipes/r09_tracker_bot.py
"""
from __future__ import annotations

import json

import _common as c
from tgkit.errors import TelegramError
from tgkit.icons import IconSystem
from tgkit.transport import FakeTransport, TelegramErrorResponse
from tgkit.widgets import check_widget, encode_state

CHAT = 111111111
TXID = "4a5e1e4baab89f3a32518a88c31bc87f618f76673e2cc77ab2127b7afdeda33b"
ICONS = IconSystem({   # ONE family; ids from btc-tracker's tgmacicons entries
    "wallets": {"id": "5258389041006518073", "fallback": "💼", "set": "tgmacicons"},
    "search": {"id": "5429571366384842791", "fallback": "🔍", "set": "tgmacicons"},
    "settings": {"id": "5258096772776991776", "fallback": "⚙️", "set": "tgmacicons"},
    "notifications": {"id": "5260535596941582167", "fallback": "🔔", "set": "tgmacicons"},
})


class TxCard:
    """One widget message per transaction; confirmations edit its chat_data silently."""

    def __init__(self, t: FakeTransport, *, sound_on_final: bool, widgets_ok: bool = True):
        self.t, self.sound_on_final, self.widgets_ok = t, sound_on_final, widgets_ok
        self.message_id: int | None = None
        self.mode = "widget"
        self.revision = 0
        self.state: dict = {}

    def _markup(self) -> dict:
        return {"inline_keyboard": [[
            {"text": "Explorer", "url": f"https://mempool.space/tx/{TXID}"},
            {"text": "Copy TXID", "copy_text": {"text": TXID}}]]}

    def _caption(self) -> str:
        s = self.state
        word = "Incoming" if s["d"] == "in" else "Outgoing"
        status = "confirmed" if s["conf"] >= s["target"] else f"{s['conf']}/{s['target']} confirmations"
        return f"{word} {s['amt']} BTC · {s['w']} · {status}"   # chat list, notifications, old apps

    def _text(self) -> str:   # the classic fallback screen, same facts
        s = self.state
        return (f"<b>{'📥 Incoming' if s['d'] == 'in' else '📤 Outgoing'} transaction</b> · {s['w']}\n"
                f"Amount: <b>{s['amt']} BTC</b> (≈ ${s['usd']})\n"
                f"Confirmations: <b>{s['conf']}/{s['target']}</b>")

    def open(self, **state) -> None:
        self.state = {**state, "url": f"https://mempool.space/tx/{TXID}", "tx": TXID}
        html = c.widget_html("tx-confirmations.html")
        if self.widgets_ok:
            payload = encode_state({**self.state, "r": 0})
            assert check_widget(html, caption=self._caption(), chat_data=payload).ok
            try:
                msg = self.t.call("sendWidget", {"chat_id": CHAT, "html": html, "chat_data": payload,
                                                 "caption": self._caption(), "reply_markup": self._markup()})
                self.message_id = msg["message_id"]
                return
            except TelegramError as err:
                if err.category not in ("unsupported", "validation"):
                    raise
        self.mode = "text"                       # same chat, same facts, same buttons
        msg = self.t.call("sendMessage", {"chat_id": CHAT, "text": self._text(), "parse_mode": "HTML",
                                          "reply_markup": self._markup()})
        self.message_id = msg["message_id"]

    def confirm(self, conf: int) -> None:
        if conf <= self.state["conf"]:
            return                               # replayed poll result: nothing to do
        self.state["conf"] = conf
        self.revision += 1
        if self.mode == "widget":
            self.t.call("editMessageWidgetData", {"chat_id": CHAT, "message_id": self.message_id,
                                                  "chat_data": encode_state({**self.state, "r": self.revision})})
            self.t.call("editMessageCaption", {"chat_id": CHAT, "message_id": self.message_id,
                                               "caption": self._caption(), "reply_markup": self._markup()})
        else:
            self.t.call("editMessageText", {"chat_id": CHAT, "message_id": self.message_id, "text": self._text(),
                                            "parse_mode": "HTML", "reply_markup": self._markup()})
        if conf >= self.state["target"] and self.sound_on_final:
            # Widget edits are silent: a final confirmation the user asked to HEAR needs a message.
            self.t.call("sendMessage", {"chat_id": CHAT, "text": f"✅ Confirmed: {self.state['amt']} BTC · {self.state['w']}",
                                        "reply_parameters": {"message_id": self.message_id}})


def price_ticker(t: FakeTransport) -> str:
    html = c.widget_html("price-ticker.html")
    state = {"p": "97250.12", "ch": "+1.84", "at": 1762900800, "r": 0}
    assert check_widget(html, caption="BTC price", public_data=encode_state(state)).ok
    first = t.call("sendWidget", {"chat_id": CHAT, "html": html, "public_data": encode_state(state),
                                  "caption": "BTC price, live", "is_shared": True})    # no allow_queries needed
    wid = first["widget"]["id"]
    t.call("editSharedWidgetData", {"widget_id": wid, "public_data": encode_state({**state, "p": "97301.50", "ch": "+1.90", "at": 1762900810, "r": 1}),
                                    "cache_time": 10})          # price changes often: poll every 10 s
    t.call("sendSharedWidget", {"chat_id": 222222222, "widget_id": wid, "caption": "BTC price, live"})
    return wid


def verify_addresses_table(t: FakeTransport) -> None:
    rows = [("1", "bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq", "m/84'/0'/0'/0/0"),
            ("2", "bc1qcr8te4kr609gcawutmrza0j4xv80jy8z306fyu", "m/84'/0'/0'/0/1")]
    cell = lambda v, h=False, a="left": {"text": v, "align": a, "valign": "middle", **({"is_header": True} if h else {})}  # noqa: E731
    t.call("sendRichMessage", {"chat_id": CHAT, "rich_message": {"blocks": [
        {"type": "heading", "size": 3, "text": "Public key verification"},
        {"type": "paragraph", "text": "Compare at least the first two addresses with your wallet."},
        {"type": "table", "is_compact": True, "is_bordered": True,
         "cells": [[cell("No.", True, "right"), cell("Address", True), cell("Path", True)]] +
                  [[cell(n, a="right"), {"text": {"type": "code", "text": addr}, "align": "left", "valign": "middle"},
                    cell(path)] for n, addr, path in rows]},
        {"type": "expandable_blockquote", "text": "The bot only has a public key and cannot spend BTC. If the addresses differ, do not generate new ones."}]}})


def analysis_short_list(t: FakeTransport) -> None:
    # 4 facts read once -> short lines, not a table (format-selection criteria).
    t.call("sendMessage", {"chat_id": CHAT, "parse_mode": "HTML", "text":
        f"{ICONS.title('search', 'Analysis: Main')}\n\n"
        "Balance: <b>0.0412 BTC</b> (≈ $4,006)\nReceived: <b>0.1500 BTC</b> · Sent: <b>0.1088 BTC</b>\nTransactions: <b>14</b>"})


def position_picker(t: FakeTransport, taken: set[int]) -> None:
    row = [({"text": f"No. {n}", "disabled": {}} if n in taken else {"text": f"No. {n}", "callback_data": f"pos:{n}"})
           for n in range(1, 5)]
    t.call("sendMessage", {"chat_id": CHAT, "parse_mode": "HTML",
                           "text": "<b>Step 1 of 2 · Address number</b>\n\nTaken numbers are greyed out. Tap a number or type another.",
                           "reply_markup": {"inline_keyboard": [row, [{"text": "Cancel", "callback_data": "pos:cancel"}]],
                                            "force_reply": True}})


def main_menu(t: FakeTransport) -> None:
    t.call("sendMessage", {"chat_id": CHAT, "parse_mode": "HTML",
                           "text": f"{ICONS.title('wallets', 'BTC Tracker')}\n\nTrack your Bitcoin addresses and public keys.",
                           "reply_markup": {"inline_keyboard": [
                               [ICONS.button("My wallets", "wallets", callback_data="menu_wallets", style="primary")],
                               [ICONS.button("Settings", "settings", callback_data="menu_settings"),
                                ICONS.button("Notifications", "notifications", callback_data="menu_notify")]]}})


def run(transport: FakeTransport | None = None):
    t = transport or FakeTransport()
    main_menu(t)
    card = TxCard(t, sound_on_final=True)
    card.open(d="in", w="Main", amt="0.0125", usd="1215.63", conf=0, target=3)
    for conf in (1, 1, 2, 3):                    # a replayed "1" from the poller is ignored
        card.confirm(conf)
    wid = price_ticker(t)
    verify_addresses_table(t)
    analysis_short_list(t)
    position_picker(t, taken={1, 2})
    return t, card, wid


def main() -> None:
    t, card, wid = run()
    c.dump(t, "Tracker bot on 10.3/10.4")
    c.check(t.methods().count("sendWidget") == 2 and t.methods().count("editMessageWidgetData") == 3,
            "one card per transaction, 3 silent state edits (replayed confirmation ignored)")
    finals = [p for p in t.params_of("sendMessage") if "Confirmed" in p.get("text", "")]
    c.check(len(finals) == 1 and finals[0]["reply_parameters"]["message_id"] == card.message_id,
            "the confirmation the user wants to hear is one real message, replying to the card")
    c.check(t.params_of("editSharedWidgetData")[0]["cache_time"] == 10, "ticker refresh period set for a fast-moving price")
    menu = t.params_of("sendMessage")[0]
    ids = {b.get("icon_custom_emoji_id") for row in menu["reply_markup"]["inline_keyboard"] for b in row}
    c.check('emoji-id="5258389041006518073"' in menu["text"] and "5258389041006518073" in ids,
            "title and button use the same custom emoji id (one visual language)")
    c.check(all(not b["text"][0] in "💼⚙️🔔" for row in menu["reply_markup"]["inline_keyboard"] for b in row),
            "no Unicode emoji inside labels that already carry a custom icon")
    picker = t.params_of("sendMessage")[-1]["reply_markup"]
    c.check(picker["force_reply"] and picker["inline_keyboard"][0][0] == {"text": "No. 1", "disabled": {}},
            "taken numbers disabled, typing still possible (force_reply)")
    table = next(b for b in t.params_of("sendRichMessage")[0]["rich_message"]["blocks"] if b["type"] == "table")
    c.check(table["is_compact"] and len(table["cells"][0]) == 3, "verification = compact table (compare across rows)")
    # Fallback where widgets are refused (old Bot API server, unsupported context).
    t2 = FakeTransport().script("sendWidget", TelegramErrorResponse(404, "Not Found"))
    card2 = TxCard(t2, sound_on_final=False)
    card2.open(d="out", w="Cold", amt="0.5000", usd="48625.06", conf=0, target=3)
    card2.confirm(1)
    c.check(card2.mode == "text" and t2.methods() == ["sendWidget", "sendMessage", "editMessageText"],
            "unsupported widget -> the same card as text, edited in place, same chat")
    off = IconSystem(ICONS.icons, enabled=False)
    c.check(off.button("Settings", "settings", callback_data="s")["text"] == "⚙️ Settings" and "emoji-id" not in off.title("settings", "Settings"),
            "not eligible for custom emoji -> every icon degrades together to Unicode")


if __name__ == "__main__":
    main()
