"""R20 - Shop: catalog -> product -> cart -> checkout with Telegram Stars or a
provider invoice, pre_checkout_query, successful_payment, receipt.

Invariants shown (offline, against fixtures):
* one invoice per cart revision - a second "Pay" does not send a second invoice;
* pre_checkout_query re-checks the order on the server (status, amount, stock)
  and is answered within 10 s, ok=False with a human reason when it can't go on;
* successful_payment is applied once per telegram_payment_charge_id, even if the
  update is delivered twice;
* a sold-out item is a DISABLED button, and a crafted "add" for it is refused;
* buttons of an older screen render are refused as stale.

Run:  py -3 examples/python/recipes/r20_shop.py [--write-payload]
"""
from __future__ import annotations

import sys

import _common as c
from tgkit import flows as f
from tgkit.rich import table
from tgkit.transport import FakeTransport

PAYLOAD = "r20-shop"
STATUS = "production"
CONTEXT = "private"
ALICE = f.user(111111111, "Alice", "en")
OLENA = f.user(333333333, "Олена", "uk")
# Live mode reads the provider token from the env var SHOP_PROVIDER_TOKEN (never
# committed). Offline payloads carry this placeholder instead.
PROVIDER_TOKEN = "PROVIDER_TOKEN_FROM_ENV"

COPY = {
    "en": {
        "catalog": "<b>Coffee beans</b>\nFresh roast, shipped in 2 days. Pick a coffee:",
        "product": "<b>{title}</b>\n{note}\n\nPrice: ⭐ {stars} · €{eur}\nIn your cart: {qty}",
        "cart": "<b>Your cart</b>\n{lines}\n\nTotal: ⭐ {stars} · €{eur}",
        "cart_empty": "<b>Your cart is empty</b>\nAdd a coffee from the catalog.",
        "pay": "<b>Checkout</b> · order {order}\nTotal: ⭐ {stars} · €{eur}\nChoose how to pay:",
        "invoice_sent": "Your invoice is below ↓",
        "sold_out": "Sold out. We'll restock on Monday.",
        "added": "Added to cart",
        "receipt_title": "Paid · order {order}",
        "receipt_note": "We'll message you when it ships.",
        "pc_changed": "Your cart changed after this invoice. Open the cart and pay again.",
        "pc_stock": "Sorry, {title} just sold out. Remove it from the cart and try again.",
        "invoice_title": "Order {order}",
        "invoice_desc": "{count} bag(s) of coffee, shipped in 2 days",
        "btn_cart": "Cart ({qty})",
        "btn_add": "Add to cart",
        "btn_back": "← Back",
        "btn_checkout": "Checkout",
        "btn_stars": "Pay ⭐ {stars}",
        "btn_card": "Pay by card · €{eur}",
        "btn_clear": "Empty the cart",
        "btn_catalog": "Catalog",
        "sys_stale": "This screen has changed. Use the latest message.",
        "sys_not_yours": "This menu belongs to someone else. Open your own with /start.",
        "sys_expired": "This menu has expired. Send /start to open a new one.",
    },
    "uk": {
        "catalog": "<b>Кава в зернах</b>\nСвіже обсмаження, відправка за 2 дні. Оберіть каву:",
        "product": "<b>{title}</b>\n{note}\n\nЦіна: ⭐ {stars} · €{eur}\nУ кошику: {qty}",
        "cart": "<b>Ваш кошик</b>\n{lines}\n\nРазом: ⭐ {stars} · €{eur}",
        "cart_empty": "<b>Кошик порожній</b>\nДодайте каву з каталогу.",
        "pay": "<b>Оформлення</b> · замовлення {order}\nРазом: ⭐ {stars} · €{eur}\nОберіть спосіб оплати:",
        "invoice_sent": "Рахунок нижче ↓",
        "sold_out": "Розпродано. Поповнимо в понеділок.",
        "added": "Додано в кошик",
        "receipt_title": "Оплачено · замовлення {order}",
        "receipt_note": "Напишемо, щойно відправимо.",
        "pc_changed": "Кошик змінився після цього рахунку. Відкрийте кошик і оплатіть знову.",
        "pc_stock": "На жаль, {title} щойно закінчилась. Приберіть її з кошика й спробуйте ще раз.",
        "invoice_title": "Замовлення {order}",
        "invoice_desc": "Кава: {count} уп., відправка за 2 дні",
        "btn_cart": "Кошик ({qty})",
        "btn_add": "Додати в кошик",
        "btn_back": "← Назад",
        "btn_checkout": "Оформити",
        "btn_stars": "Сплатити ⭐ {stars}",
        "btn_card": "Карткою · €{eur}",
        "btn_clear": "Очистити кошик",
        "btn_catalog": "Каталог",
        "sys_stale": "Екран змінився. Користуйтеся останнім повідомленням.",
        "sys_not_yours": "Це меню іншої людини. Відкрийте своє через /start.",
        "sys_expired": "Меню застаріло. Надішліть /start.",
    },
}
I18N = f.I18n(COPY)

PRODUCTS = {
    "eth": {"title": {"en": "Ethiopia Yirgacheffe", "uk": "Ефіопія Іргачеффе"},
            "note": {"en": "Jasmine, bergamot, light roast.", "uk": "Жасмин, бергамот, світле обсмаження."},
            "stars": 250, "cents": 920, "stock": 5},
    "col": {"title": {"en": "Colombia Huila", "uk": "Колумбія Уїла"},
            "note": {"en": "Caramel, red apple.", "uk": "Карамель, червоне яблуко."},
            "stars": 220, "cents": 840, "stock": 0},
    "ken": {"title": {"en": "Kenya Nyeri AA", "uk": "Кенія Ньєрі AA"},
            "note": {"en": "Blackcurrant, bright acidity.", "uk": "Чорна смородина, яскрава кислотність."},
            "stars": 300, "cents": 1100, "stock": 1},
}
DELIVERY_CENTS = 0


def eur(cents: int) -> str:
    return f"{cents // 100}.{cents % 100:02d}"


class Shop:
    def __init__(self, t: FakeTransport):
        self.t = t
        self.flow = f.ScreenFlow(t, "sh", i18n=I18N)
        self.stock = {k: p["stock"] for k, p in PRODUCTS.items()}
        self.orders: dict[str, dict] = {}            # order id -> order
        self.by_cart: dict[tuple[int, int], str] = {}  # (user, cart revision) -> order id
        self.invoices = f.OnceStore()                # one invoice per order + method
        self.payments = f.OnceStore()                # one fulfilment per charge id
        self.updates = f.UpdateDedup()
        self.next_order = 1001
        self._screens()

    # ---- state helpers ----------------------------------------------------
    @staticmethod
    def cart(s: f.Session) -> dict[str, int]:
        return s.data.setdefault("cart", {})

    @staticmethod
    def totals(cart: dict[str, int]) -> tuple[int, int, int]:
        stars = sum(PRODUCTS[k]["stars"] * q for k, q in cart.items())
        cents = sum(PRODUCTS[k]["cents"] * q for k, q in cart.items()) + (DELIVERY_CENTS if cart else 0)
        return stars, cents, sum(cart.values())

    def bump_cart(self, s: f.Session) -> None:
        s.data["cart_rev"] = s.data.get("cart_rev", 0) + 1

    def order_for_cart(self, s: f.Session) -> dict:
        """Same cart revision -> same order. A new revision supersedes the old order."""
        key = (s.owner_id, s.data.get("cart_rev", 0))
        if key in self.by_cart:
            return self.orders[self.by_cart[key]]
        for o in self.orders.values():
            if o["user"] == s.owner_id and o["status"] == "pending":
                o["status"] = "superseded"
        oid = f"SH-{self.next_order}"
        self.next_order += 1
        stars, cents, count = self.totals(self.cart(s))
        self.orders[oid] = {"id": oid, "user": s.owner_id, "chat": s.chat_id, "lang": s.lang,
                            "items": dict(self.cart(s)), "stars": stars, "cents": cents,
                            "count": count, "status": "pending"}
        self.by_cart[key] = oid
        return self.orders[oid]

    # ---- screens ------------------------------------------------------------
    def _screens(self) -> None:
        fl = self.flow

        @fl.screen("catalog")
        def catalog(fl: f.ScreenFlow, s: f.Session) -> dict:
            rows = []
            for key, p in PRODUCTS.items():
                label = f"{p['title'][s.lang]} · ⭐ {p['stars']}"
                if self.stock[key] <= 0:     # shown, not hidden: the user learns it exists
                    rows.append([f.btn(label, disabled=True)])
                else:
                    rows.append([f.btn(label, fl.cb(s, "item", key))])
            qty = sum(self.cart(s).values())
            rows.append([f.btn(fl.tr(s, "btn_cart", qty=qty), fl.cb(s, "cart"))])
            return {"text": fl.tr(s, "catalog"), "reply_markup": f.kb(*rows)}

        @fl.screen("item")
        def item(fl: f.ScreenFlow, s: f.Session) -> dict:
            key = s.args["key"]
            p = PRODUCTS[key]
            qty = self.cart(s).get(key, 0)
            text = fl.tr(s, "product", title=p["title"][s.lang], note=p["note"][s.lang],
                         stars=p["stars"], eur=eur(p["cents"]), qty=qty)
            minus = f.btn("−", fl.cb(s, "qty", key, -1)) if qty else f.btn("−", disabled=True)
            plus = (f.btn("+", fl.cb(s, "qty", key, 1)) if qty < self.stock[key]
                    else f.btn("+", disabled=True))
            add = (f.btn(fl.tr(s, "btn_add"), fl.cb(s, "qty", key, 1), style="primary")
                   if not qty else f.btn(fl.tr(s, "btn_cart", qty=sum(self.cart(s).values())),
                                         fl.cb(s, "cart"), style="primary"))
            return {"text": text, "reply_markup": f.kb([minus, f.btn(str(qty), disabled=True), plus], [add],
                                                       [f.btn(fl.tr(s, "btn_back"), fl.cb(s, "back"))])}

        @fl.screen("cart")
        def cart(fl: f.ScreenFlow, s: f.Session) -> dict:
            items = self.cart(s)
            if not items:                    # empty state: say what to do next
                return {"text": fl.tr(s, "cart_empty"),
                        "reply_markup": f.kb([f.btn(fl.tr(s, "btn_catalog"), fl.cb(s, "home"))])}
            lines = "\n".join(f"• {f.escape_html(PRODUCTS[k]['title'][s.lang])} × {q}" for k, q in items.items())
            stars, cents, _ = self.totals(items)
            return {"text": fl.tr(s, "cart", lines=f.Raw(lines), stars=stars, eur=eur(cents)),
                    "reply_markup": f.kb([f.btn(fl.tr(s, "btn_checkout"), fl.cb(s, "checkout"), style="primary")],
                                         [f.btn(fl.tr(s, "btn_clear"), fl.cb(s, "clear"), style="danger")],
                                         [f.btn(fl.tr(s, "btn_back"), fl.cb(s, "back"))])}

        @fl.screen("pay")
        def pay(fl: f.ScreenFlow, s: f.Session) -> dict:
            o = self.orders[s.args["order"]]
            return {"text": fl.tr(s, "pay", order=o["id"], stars=o["stars"], eur=eur(o["cents"])),
                    "reply_markup": f.kb(
                        [f.btn(fl.tr(s, "btn_stars", stars=o["stars"]), fl.cb(s, "inv", o["id"], "xtr"),
                               style="primary")],
                        [f.btn(fl.tr(s, "btn_card", eur=eur(o["cents"])), fl.cb(s, "inv", o["id"], "card"))],
                        [f.btn(fl.tr(s, "btn_back"), fl.cb(s, "back"))])}

        @fl.action("item")
        def a_item(fl, s, args, cq):
            fl.go(s, "item", key=args[0])

        @fl.action("qty")
        def a_qty(fl, s, args, cq):
            key, delta = args[0], int(args[1])
            items = self.cart(s)
            new = items.get(key, 0) + delta
            if key not in PRODUCTS or new > self.stock[key]:   # server-side re-check
                fl.answer(cq, fl.tr(s, "sold_out"), alert=True)
                return "sold_out"
            if new <= 0:
                items.pop(key, None)
            else:
                items[key] = new
            self.bump_cart(s)
            if delta > 0 and new == 1:
                fl.answer(cq, fl.tr(s, "added"))
            fl.refresh(s)
            return "cart_changed"

        @fl.action("cart")
        def a_cart(fl, s, args, cq):
            fl.go(s, "cart")

        @fl.action("home")
        def a_home(fl, s, args, cq):
            fl.open(s, "catalog")

        @fl.action("back")
        def a_back(fl, s, args, cq):
            fl.back(s)

        @fl.action("clear")
        def a_clear(fl, s, args, cq):
            self.cart(s).clear()
            self.bump_cart(s)
            fl.refresh(s)

        @fl.action("checkout")
        def a_checkout(fl, s, args, cq):
            order = self.order_for_cart(s)
            fl.go(s, "pay", order=order["id"])

        @fl.action("inv")
        def a_invoice(fl, s, args, cq):
            oid, method = args
            order = self.orders.get(oid)
            if not order or order["user"] != s.owner_id or order["status"] != "pending":
                fl.answer(cq, fl.tr(s, "pc_changed"), alert=True)
                return "order_gone"
            _, first = self.invoices.run(f"{oid}:{method}", lambda: self.send_invoice(order, method))
            if not first:
                fl.answer(cq, fl.tr(s, "invoice_sent"))
                return "invoice_already_sent"
            return "invoice_sent"

    # ---- payments -----------------------------------------------------------
    def send_invoice(self, o: dict, method: str) -> int:
        lang = o["lang"]
        base = {"chat_id": o["chat"], "title": I18N.t(lang, "invoice_title", order=o["id"]),
                "description": I18N.t(lang, "invoice_desc", count=o["count"]),
                "payload": f"o:{o['id']}"}                        # 1-128 bytes, never shown
        if method == "xtr":
            # Stars: currency XTR, provider_token "" (or omitted), exactly ONE price item.
            params = {**base, "provider_token": "", "currency": "XTR",
                      "prices": [{"label": base["title"], "amount": o["stars"]}]}
        else:
            prices = [{"label": PRODUCTS[k]["title"][lang] + f" × {q}", "amount": PRODUCTS[k]["cents"] * q}
                      for k, q in o["items"].items()]
            params = {**base, "provider_token": PROVIDER_TOKEN, "currency": "EUR", "prices": prices,
                      "need_name": True}
        o["method"] = method
        return self.t.call("sendInvoice", params)["message_id"]

    def on_pre_checkout(self, q: dict) -> bool:
        """Must be answered within 10 s. Re-check everything from our own records."""
        oid = q["invoice_payload"].removeprefix("o:")
        o = self.orders.get(oid)
        lang = I18N.lang_for(q["from"].get("language_code"))
        err = None
        if not o or o["status"] != "pending" or o["user"] != q["from"]["id"]:
            err = I18N.t(lang, "pc_changed")
        elif (q["currency"], q["total_amount"]) != (("XTR", o["stars"]) if q["currency"] == "XTR"
                                                     else ("EUR", o["cents"])):
            err = I18N.t(lang, "pc_changed")
        else:
            short = [k for k, n in o["items"].items() if self.stock[k] < n]
            if short:
                err = I18N.t(lang, "pc_stock", title=PRODUCTS[short[0]]["title"][lang])
        params = {"pre_checkout_query_id": q["id"], "ok": err is None}
        if err:
            params["error_message"] = err                         # shown to the user by Telegram
        self.t.call("answerPreCheckoutQuery", params)
        return err is None

    def on_successful_payment(self, msg: dict) -> str:
        sp = msg["successful_payment"]

        def fulfil() -> str:
            o = self.orders[sp["invoice_payload"].removeprefix("o:")]
            o["status"], o["charge_id"] = "paid", sp["telegram_payment_charge_id"]
            for k, n in o["items"].items():
                self.stock[k] -= n
            s = self.flow.sessions.get((o["chat"], o["user"]))
            if s:
                self.cart(s).clear()
                self.bump_cart(s)
            self.send_receipt(o)
            return o["id"]

        _, first = self.payments.run(sp["telegram_payment_charge_id"], fulfil)
        return "fulfilled" if first else "duplicate_payment"

    def send_receipt(self, o: dict) -> None:
        lang = o["lang"]
        rows = [[PRODUCTS[k]["title"][lang], str(q)] for k, q in o["items"].items()]
        total = f"⭐ {o['stars']}" if o.get("method") == "xtr" else f"€{eur(o['cents'])}"
        rows.append([{"type": "bold", "text": "Total" if lang == "en" else "Разом"}, total])
        self.t.call("sendRichMessage", {"chat_id": o["chat"], "rich_message": {"blocks": [
            {"type": "heading", "size": 2, "text": I18N.t(lang, "receipt_title", order=o["id"])},
            table(["Coffee" if lang == "en" else "Кава", "Qty" if lang == "en" else "К-сть"], rows,
                  compact=True, numeric_cols=frozenset({1})),
            {"type": "paragraph", "text": I18N.t(lang, "receipt_note")}]}})

    def dispatch(self, update: dict) -> str:
        if not self.updates.first_time(update):
            return "duplicate_update"
        if "pre_checkout_query" in update:
            return "pc_ok" if self.on_pre_checkout(update["pre_checkout_query"]) else "pc_refused"
        if "callback_query" in update:
            return self.flow.handle(update["callback_query"])
        msg = update["message"]
        if "successful_payment" in msg:
            return self.on_successful_payment(msg)
        s = self.flow.session(msg["chat"]["id"], msg["from"]["id"],
                              lang=I18N.lang_for(msg["from"].get("language_code")))
        self.flow.open(s, "catalog", new_message=True)
        return "catalog"


def run(t: FakeTransport | None = None):
    t = t or FakeTransport()
    shop = Shop(t)
    fl = shop.flow
    uid = [0]

    def tap(who: dict, action: str, *args, version_offset: int = 0) -> str:
        s = fl.sessions[(who["id"], who["id"])]
        data = f.pack("sh", f.b36(s.version - version_offset), action, *args)
        uid[0] += 1
        cq = f.callback(f"cq{uid[0]}", who, data, chat_id=who["id"], message_id=s.message_id)
        return shop.dispatch({"update_id": 1000 + uid[0], "callback_query": cq})

    out = [shop.dispatch({"update_id": 1, "message": f.text_message(ALICE, "/start")})]
    out.append(tap(ALICE, "qty", "col", 1))                 # crafted tap on a sold-out item
    out.append(tap(ALICE, "item", "eth"))
    out.append(tap(ALICE, "qty", "eth", 1))
    out.append(tap(ALICE, "qty", "eth", 1, version_offset=1))  # double tap on the old render
    out.append(tap(ALICE, "qty", "eth", 1))
    out.append(tap(ALICE, "cart"))
    out.append(tap(ALICE, "checkout"))
    oid = fl.sessions[(ALICE["id"], ALICE["id"])].args["order"]
    out.append(tap(ALICE, "inv", oid, "xtr"))
    out.append(tap(ALICE, "back"))                          # back to the cart, unchanged
    out.append(tap(ALICE, "checkout"))                      # same cart revision -> same order
    out.append(tap(ALICE, "inv", oid, "xtr"))               # no second invoice
    out.append(shop.dispatch(c.fixture("usecase_pre_checkout_stars.json")))
    pay = c.fixture("usecase_successful_payment_stars.json")
    out.append(shop.dispatch(pay))
    out.append(shop.dispatch(pay))                          # same update delivered again
    out.append(shop.dispatch({**pay, "update_id": 920099}))  # same charge, new update id

    # Olena (uk) pays by card for the last Kenya, which sells out while she pays.
    out.append(shop.dispatch({"update_id": 2, "message": f.text_message(OLENA, "/start")}))
    out.append(tap(OLENA, "item", "ken"))
    out.append(tap(OLENA, "qty", "ken", 1))
    out.append(tap(OLENA, "cart"))
    out.append(tap(OLENA, "checkout"))
    oid2 = fl.sessions[(OLENA["id"], OLENA["id"])].args["order"]
    shop.stock["ken"] = 0                                   # sold elsewhere while she pays
    out.append(tap(OLENA, "inv", oid2, "card"))
    assert oid2 == "SH-1002"                                # the fixture's invoice_payload
    out.append(shop.dispatch(c.fixture("usecase_pre_checkout_card.json")))
    # A tap that names Alice's menu message but comes from Olena (crafted, or a bug in
    # a client): refused because the message belongs to Alice.
    a = fl.sessions[(ALICE["id"], ALICE["id"])]
    stranger = f.callback("cqx", OLENA, f.pack("sh", f.b36(a.version), "clear"),
                          chat_id=ALICE["id"], message_id=a.message_id)
    out.append(shop.dispatch({"update_id": 3, "callback_query": stranger}))
    return t, shop, out


def main() -> None:
    t, shop, out = run()
    c.dump(t, "Shop")
    c.check(out[:2] == ["catalog", "sold_out"], "a crafted add for a sold-out coffee is refused")
    c.check(out[4] == "stale", "a double tap on an old render does nothing")
    c.check(len(t.params_of("sendInvoice")) == 2, "one invoice per order and method (2 buyers)")
    c.check(out[11] == "invoice_already_sent", "the second Pay for the same cart sends no invoice")
    stars = t.params_of("sendInvoice")[0]
    c.check(stars["currency"] == "XTR" and stars["provider_token"] == "" and len(stars["prices"]) == 1,
            "Stars invoice: XTR, empty provider_token, exactly one price")
    c.check(out[12:16] == ["pc_ok", "fulfilled", "duplicate_update", "duplicate_payment"],
            "pre-checkout ok, fulfilment exactly once per charge id")
    c.check(shop.orders["SH-1001"]["status"] == "paid" and shop.stock["eth"] == 3, "stock moved once")
    refused = t.params_of("answerPreCheckoutQuery")[-1]
    c.check(refused["ok"] is False and "Кенія" in refused["error_message"],
            "pre-checkout refused with a reason in the buyer's language")
    c.check(out[-1] == "not_yours", "another user's tap on Alice's menu is refused")
    c.check(len(t.params_of("sendRichMessage")) == 1, "one receipt (rich, compact table)")


if __name__ == "__main__":
    if "--write-payload" in sys.argv:
        print(f.write_payload(f.payload_doc(PAYLOAD, run()[0], status=STATUS, context=CONTEXT)))
    else:
        main()
