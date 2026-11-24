"""R90-R99 - Mini App recipes, the bot and server side as offline scenarios with self-checks.

The app side lives in examples/mini-apps (kit, vanilla coffee app, portfolio, gallery, React); this file runs
what the bot and the server do around it, through FakeTransport, and checks the invariants each recipe is about.

Run:  py -3 examples/python/recipes/r90_99_mini_apps.py            # all ten
      py -3 examples/python/recipes/r90_99_mini_apps.py r92        # one
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import sys
import urllib.parse

import _common as c
from tgkit.transport import FakeTransport

MINI = os.path.join(c.ROOT, "mini-apps")
sys.path.insert(0, os.path.join(MINI, "bot"))
sys.path.insert(0, os.path.join(MINI, "server", "python"))
from bot_side import MiniAppBot, parse_start_param  # noqa: E402
import verify_init_data as vid  # noqa: E402

USER = 279058397
APP = "https://coffee.example.com/app"
with open(os.path.join(MINI, "server", "vectors.json"), encoding="utf-8") as fh:
    VECTORS = json.load(fh)
MENU = {"flat-white": {"M": 420, "L": 480}, "cappuccino": {"M": 390, "L": 450}}  # euro cents, server-side


def bot(t: FakeTransport, **kw) -> MiniAppBot:
    return MiniAppBot(t, bot_username="coffee_pickup_bot", app_url=APP, **kw)


def article(rid: str, title: str, text: str) -> dict:
    return {"type": "article", "id": rid, "title": title, "input_message_content": {"message_text": text}}


# ------------------------------------------------------------------ R90 decide + hybrid

def choose_surface(need: dict) -> str:
    """references/mini-apps/decide.md section 4."""
    if need.get("answers", 0) <= 3 and not (need.get("network") or need.get("uploads") or need.get("depth", 1) > 2):
        return "messages"
    if need.get("custom_layout") and not need.get("typed_text") and not need.get("network") and need.get("private"):
        return "widget"
    return "mini_app"


def r90(t: FakeTransport | None = None):
    t = t or FakeTransport()
    b = bot(t)
    decisions = {
        "rate the drink": choose_surface({"answers": 1}),
        "live order card": choose_surface({"answers": 4, "custom_layout": True, "private": True, "depth": 1}),
        "catalogue with search": choose_surface({"answers": 6, "network": True, "depth": 3}),
    }
    # Hybrid: the bot notifies, the Mini App acts on the exact screen.
    b.send_alert_with_link(USER, "Order 1042 is ready at the counter.", "Open order", "order-1042")
    b.set_menu_button(text="Order coffee")
    return t, decisions


# ------------------------------------------------------------------ R91 minimal Mini App

def r91(t: FakeTransport | None = None):
    t = t or FakeTransport()
    b = bot(t, app_short_name="pickup")
    b.set_menu_button(text="Menu")
    b.send_open_button(USER, "Order ahead and skip the queue.", "Open the menu")
    links = {"main": bot(FakeTransport()).link(), "drink": b.link("drink-flat-white"), "compact": b.link("tab-order", mode="compact")}
    return t, links


# ------------------------------------------------------------------ R92 initData + session

def r92(t: FakeTransport | None = None):
    """Server: verify initData, then answer the query once; a replay and a forged string are refused."""
    t = t or FakeTransport()
    b = bot(t)
    raw, now = VECTORS["init_data"], VECTORS["now"]
    outcomes = []
    for attempt in (raw, raw, raw.replace("order-8812", "order-9999")):
        try:
            data = vid.verify_hmac(attempt, VECTORS["bot_token"], now=now, max_age=3600)
        except vid.InitDataError as exc:
            outcomes.append(f"401 {exc}")
            continue
        ok = b.answer_query_once(data["query_id"], article("ord-8812", "Order 8812", "Order 8812 placed: 1 flat white"))
        outcomes.append("answered" if ok else "409 already answered")
    third_party = vid.verify_ed25519(raw, VECTORS["bot_id"], VECTORS["ed25519_public_key"], now=now)
    return t, outcomes, third_party["user"]["id"]


# ------------------------------------------------------------------ R93 shop

def price_cart(lines: list[dict]) -> int:
    """Prices from the server's menu; the client sends ids and quantities only."""
    total = 0
    for line in lines:
        qty = line.get("qty")
        if type(qty) is not int or not 1 <= qty <= 9 or line.get("size") not in MENU.get(line.get("id"), {}):
            raise ValueError("bad line")
        total += MENU[line["id"]][line["size"]] * qty
    return total


class Orders:
    """Server-side orders for the Mini App checkout (references/mini-apps/payments.md section 2).

    The payload carries a signed order reference bound to the order's owner; pre-checkout re-checks owner,
    expiry and amount; delivery is unique per telegram_payment_charge_id. In production this is the payments
    pipeline (references/payments-and-stars.md) with a database; here it is in memory for the offline run."""

    def __init__(self, secret: bytes, clock):
        self.secret, self.clock = secret, clock
        self.rows: dict[str, dict] = {}
        self.charges: set[str] = set()
        self.seq = 1041

    def _sign(self, order_id: str) -> str:
        return hmac.new(self.secret, order_id.encode(), hashlib.sha256).hexdigest()[:20]

    def checkout(self, user_id: int, lines: list[dict]) -> dict:
        cents = price_cart(lines)
        key = (user_id, json.dumps(sorted((l["id"], l["size"], l["qty"]) for l in lines)))
        for row in self.rows.values():  # the same cart again before it expires: the same order and link
            if row["key"] == key and row["status"] == "open" and row["valid_until"] > self.clock():
                return row
        self.seq += 1
        oid = str(self.seq)
        row = {"id": oid, "user": user_id, "lines": lines, "amount": cents, "currency": "EUR", "status": "open",
               "valid_until": self.clock() + 900, "key": key, "payload": f"ord:{oid}.{self._sign(oid)}"}
        self.rows[oid] = row
        return row

    def pre_checkout(self, query: dict) -> tuple[bool, str]:
        m = re.fullmatch(r"ord:(\d{1,12})\.([0-9a-f]{20})", query.get("invoice_payload", ""))
        row = self.rows.get(m.group(1)) if m else None
        if not row or not hmac.compare_digest(m.group(2), self._sign(row["id"])):
            return False, "This order is not valid any more. Open the cart and try again."
        if query["from"]["id"] != row["user"]:
            return False, "This payment link belongs to another account."
        if row["valid_until"] <= self.clock() or row["status"] != "open":
            return False, "This order has expired. Open the cart to see current prices."
        if query["currency"] != row["currency"] or query["total_amount"] != row["amount"]:
            return False, "The total changed. Open the cart to see the new total."
        return True, ""

    def paid(self, sp: dict) -> bool:
        """successful_payment: the only fact of payment. True when this charge delivered the order now."""
        oid = sp["invoice_payload"].split(":")[1].split(".")[0]
        row = self.rows.get(oid)
        if not row or sp["telegram_payment_charge_id"] in self.charges:
            return False
        self.charges.add(sp["telegram_payment_charge_id"])
        row["status"] = "paid"
        return True


def r93(t: FakeTransport | None = None):
    """Coffee is a physical good: a payment provider in EUR (Stars are for digital goods), priced on the server."""
    t = t or FakeTransport()
    t.script("createInvoiceLink", "https://t.me/$order-1042-invoice")
    now = [1795400000]
    orders = Orders(b"test-secret-from-env", lambda: now[0])
    cart = [{"id": "flat-white", "size": "M", "qty": 2, "price": 1}]   # the client's price is ignored
    order = orders.checkout(USER, cart)
    again = orders.checkout(USER, cart)                                # double tap: same order, no new invoice
    link = t.call("createInvoiceLink", {"title": f"Order {order['id']}", "description": "2 × Flat white, pickup 10:30",
                                         "payload": order["payload"], "currency": "EUR",
                                         "provider_token": "PROVIDER_TOKEN_FROM_ENV",
                                         "prices": [{"label": "2 × Flat white", "amount": order["amount"]}]})
    # The app calls tma.pay(link) (WebApp.openInvoice) and then tma.watchOrder(); the bot gets these updates:
    base = {"currency": "EUR", "total_amount": order["amount"], "invoice_payload": order["payload"]}
    checks = {
        "owner": orders.pre_checkout({**base, "from": {"id": USER}}),
        "stranger": orders.pre_checkout({**base, "from": {"id": 999}}),
        "forged": orders.pre_checkout({**base, "invoice_payload": f"ord:{order['id']}.{'0' * 20}", "from": {"id": USER}}),
        "changed_total": orders.pre_checkout({**base, "total_amount": 1, "from": {"id": USER}}),
    }
    sp = {**base, "telegram_payment_charge_id": "TEST-CHARGE-1042", "provider_payment_charge_id": "prov_1042"}
    delivered = [orders.paid(sp), orders.paid(sp)]                    # a redelivered update delivers nothing
    if delivered[0]:
        t.call("sendMessage", {"chat_id": USER, "text": f"Paid €8.40. Order {order['id']}: 2 × Flat white, "
                                                         "pickup 10:30 at Central. Problems with the payment: /paysupport"})
    now[0] += 1000
    expired = orders.pre_checkout({**base, "from": {"id": USER}})
    return t, order, again, link, checks, delivered, expired


# ------------------------------------------------------------------ R94 form / booking

def booking_schema(d: dict) -> dict:
    people, slot, name = d.get("people"), d.get("slot"), d.get("name")
    if type(people) is not int or not 1 <= people <= 8 or not isinstance(slot, str) \
            or not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", slot) or not isinstance(name, str):
        raise ValueError("bad booking")
    return {"slot": slot, "people": people, "name": name.strip()[:40]}


def r94(t: FakeTransport | None = None):
    t = t or FakeTransport()
    b = bot(t)
    b.send_keyboard_button(USER, "Book a table: pick a time in the form.", "Choose a time", "/booking")
    good = {"chat": {"id": USER}, "web_app_data": {"button_text": "Choose a time",
                                                   "data": json.dumps({"slot": "2026-11-28T19:30", "people": 2, "name": "Olena"})}}
    bad = {"chat": {"id": USER}, "web_app_data": {"button_text": "Choose a time", "data": '{"slot":"tonight","people":99}'}}
    booked = b.on_web_app_data(good, booking_schema)
    t.call("sendMessage", {"chat_id": USER, "text": f"Table for {booked['people']} on 28 Nov at 19:30 is booked. "
                                                     "I will remind you an hour before.",
                           "reply_markup": {"remove_keyboard": True}})
    rejected = b.on_web_app_data(bad, booking_schema)
    return t, booked, rejected


# ------------------------------------------------------------------ R95 dashboard / portfolio

def r95(t: FakeTransport | None = None):
    t = t or FakeTransport()
    b = bot(t, app_short_name="points")
    b.send_alert_with_link(USER, "Gold level reached: 1,240 points.", "See points", "asset-points")
    routes = {"asset": re.compile(r"^asset-([a-z]{2,12})$"), "tab": re.compile(r"^tab-(home|bonus)$")}
    parsed = [parse_start_param(p, routes) for p in ("asset-points", "tab-bonus", "asset-../../x", "x" * 600)]
    return t, [(p[0], p[1].group(1)) if p else None for p in parsed]


# ------------------------------------------------------------------ R96 profile and settings

def r96(t: FakeTransport | None = None):
    t = t or FakeTransport()
    b = bot(t)
    before = b.notify(USER, "Order notifications are on.")
    b.on_write_access_allowed({"from": {"id": USER}, "chat": {"id": USER},
                               "write_access_allowed": {"web_app_name": "pickup", "from_request": True}})
    after = b.notify(USER, "Order notifications are on. Turn them off in the app's settings.")
    b.set_menu_button(chat_id=USER, text="Settings")
    return t, before, after


# ------------------------------------------------------------------ R97 game / leaderboard, fullscreen

def r97(t: FakeTransport | None = None):
    t = t or FakeTransport()
    t.script("savePreparedInlineMessage", {"id": "prep-score-520", "expiration_date": 1795486400})
    b = bot(t, app_short_name="latte_art")
    link = b.link("challenge-520", mode="fullscreen")
    prepared = b.prepare_share(USER, {"type": "article", "id": "score-520", "title": "520 points in Latte Art",
                                      "input_message_content": {"message_text": "I scored 520 in Latte Art. Beat me?"},
                                      "reply_markup": {"inline_keyboard": [[{"text": "Play", "url": link}]]}},
                               chats=("users", "groups"))
    return t, link, prepared


# ------------------------------------------------------------------ R98 share a result

def r98(t: FakeTransport | None = None):
    t = t or FakeTransport()
    t.script("savePreparedInlineMessage", {"id": "prep-order-1042", "expiration_date": 1795486400})
    b = bot(t)
    prepared = b.prepare_share(USER, article("share-1042", "My usual", "My usual: flat white, oat milk. Try it at Central."),
                               chats=("users", "groups", "channels"))
    answered = b.answer_query_once("AAH-share-query", {"type": "article", "id": "fav-1", "title": "Favourite drink",
                                                       "input_message_content": {"message_text": "Flat white, oat milk"}})
    replay = b.answer_query_once("AAH-share-query", article("fav-2", "again", "again"))
    picker = b.prepare_chat_picker(USER, request_id=7, text="Share to a group")
    return t, prepared, answered, replay, picker


# ------------------------------------------------------------------ R99 editor

class Drafts:
    """Server store with revisions: a stale save is a conflict, never a silent overwrite."""

    def __init__(self):
        self.docs: dict[str, dict] = {}

    def save(self, doc_id: str, text: str, base_rev: int) -> dict:
        cur = self.docs.get(doc_id, {"rev": 0, "text": ""})
        if base_rev != cur["rev"]:
            return {"status": 409, "rev": cur["rev"], "text": cur["text"]}
        self.docs[doc_id] = {"rev": cur["rev"] + 1, "text": text}
        return {"status": 200, "rev": cur["rev"] + 1}


def r99(t: FakeTransport | None = None):
    t = t or FakeTransport()
    store = Drafts()
    phone = store.save("menu-board", "Autumn blend: spiced, low acidity", 0)
    desktop_stale = store.save("menu-board", "Autumn blend", 0)          # opened before the phone saved
    desktop_merged = store.save("menu-board", "Autumn blend: spiced, low acidity. €3.80", desktop_stale["rev"])
    text = store.docs["menu-board"]["text"]
    t.call("sendMessage", {"chat_id": USER, "text": f"Publish to the menu board?\n\n{text}", "reply_markup": {
        "inline_keyboard": [[{"text": "Publish", "callback_data": f"pub:menu-board:{desktop_merged['rev']}", "style": "success"},
                             {"text": "Keep editing", "web_app": {"url": APP + "/editor/menu-board"}}]]}})
    return t, phone, desktop_stale, desktop_merged


SCENARIOS = {"r90": r90, "r91": r91, "r92": r92, "r93": r93, "r94": r94, "r95": r95, "r96": r96, "r97": r97,
             "r98": r98, "r99": r99}


def main() -> None:
    which = sys.argv[1:] or list(SCENARIOS)
    if "r90" in which:
        t, d = r90()
        c.dump(t, "R90 decide and hybrid")
        c.check(d == {"rate the drink": "messages", "live order card": "widget", "catalogue with search": "mini_app"},
                "decision path: one tap -> messages, live card -> widget, search catalogue -> Mini App")
        c.check("startapp=order-1042" in t.params_of("sendMessage")[0]["reply_markup"]["inline_keyboard"][0][0]["url"],
                "the alert opens the exact screen through startapp")
    if "r91" in which:
        t, links = r91()
        c.dump(t, "R91 minimal Mini App")
        c.check(links["main"] == "https://t.me/coffee_pickup_bot?startapp", "Main Mini App link without a parameter")
        c.check(links["compact"].endswith("startapp=tab-order&mode=compact"), "compact mode link")
        c.check(t.params_of("sendMessage")[0]["reply_markup"]["inline_keyboard"][0][0]["web_app"]["url"] == APP,
                "inline web_app button for a query_id launch")
    if "r92" in which:
        t, outcomes, third = r92()
        c.dump(t, "R92 initData and the query answer")
        c.check(outcomes[0] == "answered", "verified initData -> answerWebAppQuery")
        c.check(outcomes[1] == "409 already answered", "a replayed query_id is refused")
        c.check(outcomes[2].startswith("401"), "a forged start_param fails the HMAC")
        c.check(len(t.params_of("answerWebAppQuery")) == 1, "exactly one answer per query")
        c.check(third == VECTORS["expect"]["user_id"], "third-party Ed25519 check without the token")
    if "r93" in which:
        t, order, again, link, checks, delivered, expired = r93()
        c.dump(t, "R93 shop checkout")
        c.check(order["amount"] == 840, "the server prices the cart; the client's price is ignored")
        c.check(again is order and len(t.params_of("createInvoiceLink")) == 1, "a repeated checkout reuses the open order")
        inv = t.params_of("createInvoiceLink")[0]
        c.check(inv["currency"] == "EUR" and inv["provider_token"], "a physical good goes through a provider, not Stars")
        c.check(re.fullmatch(r"ord:\d+\.[0-9a-f]{20}", inv["payload"]) is not None, "the payload is a signed order reference")
        c.check(checks["owner"][0] and not checks["stranger"][0] and not checks["forged"][0] and not checks["changed_total"][0],
                "pre-checkout refuses another payer, a forged payload and a changed total")
        c.check(delivered == [True, False] and len(t.params_of("sendMessage")) == 1, "one delivery and one receipt per charge")
        c.check(not expired[0], "an expired order is refused")
    if "r94" in which:
        t, booked, rejected = r94()
        c.dump(t, "R94 booking form")
        c.check(booked == {"slot": "2026-11-28T19:30", "people": 2, "name": "Olena"}, "web_app_data parsed by a schema")
        c.check(rejected is None and "did not come through" in t.params_of("sendMessage")[-1]["text"],
                "bad data gets a visible answer, not silence")
    if "r95" in which:
        t, parsed = r95()
        c.dump(t, "R95 dashboard deep link")
        c.check(parsed == [("asset", "points"), ("tab", "bonus"), None, None], "start_param allowlist")
    if "r96" in which:
        t, before, after = r96()
        c.dump(t, "R96 settings and write access")
        c.check(before is False and after is True, "the bot writes first only after write_access_allowed")
    if "r97" in which:
        t, link, prepared = r97()
        c.dump(t, "R97 fullscreen game share")
        c.check(link.endswith("startapp=challenge-520&mode=fullscreen"), "fullscreen link with the challenge")
        p = t.params_of("savePreparedInlineMessage")[0]
        c.check(p.get("allow_user_chats") and p.get("allow_group_chats") and prepared["id"], "prepared message for shareMessage")
    if "r98" in which:
        t, prepared, answered, replay, picker = r98()
        c.dump(t, "R98 share a result")
        c.check(answered and not replay, "answerWebAppQuery once")
        c.check(t.params_of("savePreparedKeyboardButton")[0]["button"]["request_chat"]["request_id"] == 7,
                "requestChat id prepared by the bot")
    if "r99" in which:
        t, phone, stale, merged = r99()
        c.dump(t, "R99 editor and publish")
        c.check(phone["status"] == 200 and stale["status"] == 409, "a stale save is a conflict, not an overwrite")
        c.check(merged == {"status": 200, "rev": 2}, "the merged save lands on the newest revision")
        c.check(t.params_of("sendMessage")[0]["reply_markup"]["inline_keyboard"][0][0]["callback_data"] == "pub:menu-board:2",
                "publishing is bound to the revision the user saw")


if __name__ == "__main__":
    main()
