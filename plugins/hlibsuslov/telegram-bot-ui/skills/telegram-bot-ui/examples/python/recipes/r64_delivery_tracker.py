"""R64 - Delivery tracker: ONE status card per order, edited in place.

Invariants shown (offline, against a courier-webhook fixture):
* statuses move only through a `Machine` (placed > packed > shipped > out_for_delivery >
  delivered); a courier event with an older or repeated sequence number is ignored, and an
  event that skips a state is refused WITHOUT advancing the sequence (the missing one may
  still arrive);
* updates are silent edits of the same card; only out_for_delivery and delivered also send
  a short NEW message (the one that rings the phone - a design heuristic);
* "Change address" works until shipped; afterwards the button is disabled and a crafted tap
  is refused with the reason;
* edit failures: "message to edit not found" -> send a fresh card and remember its id;
  429 -> wait the retry_after the server gave (tgkit.errors.call_with_policy);
* the delivery is rated once, by the order's owner, from the current card only.

Run:  py -3 examples/python/recipes/r64_delivery_tracker.py [--write-payload]
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone

import _common as c
from tgkit import flows as f
from tgkit.errors import TelegramError, call_with_policy
from tgkit.transport import FakeTransport, TelegramErrorResponse

PAYLOAD = "r64-delivery-tracker"
STATUS = "production"
CONTEXT = "private"
NOW = 1794830400
ALICE = f.user(111111111, "Alice", "en")
OLENA = f.user(333333333, "Олена", "uk")
STEPS = ["placed", "packed", "shipped", "out_for_delivery", "delivered"]
MACHINE = f.Machine({"placed": {"pack": "packed"}, "packed": {"ship": "shipped"},
                     "shipped": {"out": "out_for_delivery"}, "out_for_delivery": {"deliver": "delivered"},
                     "delivered": {}}, "placed")
TRACK_URL = "https://track.example.com/"           # placeholder carrier page

COPY = {
    "en": {
        "card": "<b>Order {oid}</b>\n{bar} {step}/5 · {status}\n{eta}\nAddress: {address}",
        "eta": "Expected {when}",
        "done_at": "Delivered {when}",
        "rate_ask": "\nHow was the delivery?",
        "rated": "\nThanks, you rated it {n}/5.",
        "st_placed": "placed", "st_packed": "packed", "st_shipped": "shipped",
        "st_out_for_delivery": "out for delivery", "st_delivered": "delivered",
        "alert_out": "<b>{oid} is out for delivery</b>\nCourier {name}, arriving {when}.",
        "alert_done": "<b>{oid} is delivered.</b> Enjoy!",
        "ask_addr": "Send the new delivery address as a reply to this message.",
        "addr_saved": "Address updated.",
        "addr_locked": "The parcel is already shipped, so the address can't change. The courier can still call you.",
        "courier_info": "Courier {name}: {phone}",
        "toast_rated": "You already rated this delivery.",
        "btn_track": "Track", "btn_courier": "Contact courier", "btn_addr": "Change address",
        "btn_addr_locked": "Change address · shipped", "btn_keep": "Keep address",
        "sys_stale": "This card has changed. Use the latest one.",
        "sys_not_yours": "This order belongs to someone else.",
        "sys_expired": "This order is not available any more.",
    },
    "uk": {
        "card": "<b>Замовлення {oid}</b>\n{bar} {step}/5 · {status}\n{eta}\nАдреса: {address}",
        "eta": "Очікуємо {when}",
        "done_at": "Доставлено {when}",
        "rate_ask": "\nЯк пройшла доставка?",
        "rated": "\nДякуємо, оцінка {n}/5.",
        "st_placed": "оформлено", "st_packed": "зібрано", "st_shipped": "відправлено",
        "st_out_for_delivery": "кур'єр в дорозі", "st_delivered": "доставлено",
        "alert_out": "<b>{oid}: кур'єр уже в дорозі</b>\nКур'єр {name}, прибуде {when}.",
        "alert_done": "<b>{oid} доставлено.</b> Смачного!",
        "ask_addr": "Надішліть нову адресу доставки у відповідь на це повідомлення.",
        "addr_saved": "Адресу оновлено.",
        "addr_locked": "Посилку вже відправлено, тож адресу не змінити. Кур'єр може зателефонувати вам.",
        "courier_info": "Кур'єр {name}: {phone}",
        "toast_rated": "Ви вже оцінили цю доставку.",
        "btn_track": "Відстежити", "btn_courier": "Зв'язатися з кур'єром", "btn_addr": "Змінити адресу",
        "btn_addr_locked": "Адреса · вже відправлено", "btn_keep": "Лишити адресу",
        "sys_stale": "Картка змінилась. Користуйтеся найновішою.",
        "sys_not_yours": "Це замовлення іншої людини.",
        "sys_expired": "Це замовлення вже недоступне.",
    },
}
I18N = f.I18n(COPY)


def when(ts: int, with_date: bool = True) -> f.Raw:
    return f.tg_time(ts, datetime.fromtimestamp(ts, timezone.utc).strftime("%d.%m %H:%M"), "wDT" if with_date else "t")


class Tracker:
    def __init__(self, t: FakeTransport):
        self.t = t
        self.orders: dict[str, dict] = {}
        self.rated = f.OnceStore()
        self.waits: list[float] = []             # every sleep the retry policy asked for
        self.awaiting: dict[int, str] = {}       # user id -> order id waiting for a new address

    # ---- card --------------------------------------------------------------------
    def card(self, o: dict) -> dict:
        lang, st = o["lang"], o["status"]
        step = STEPS.index(st) + 1
        eta = I18N.t(lang, "done_at", when=when(o["delivered_at"])) if st == "delivered" else (
            I18N.t(lang, "eta", when=when(o["eta"])))
        text = I18N.t(lang, "card", oid=o["id"], bar="▰" * step + "▱" * (5 - step), step=step,
                      status=I18N.t(lang, f"st_{st}"), eta=f.Raw(eta), address=o["address"])
        data = lambda a, *x: f.pack("dt", f.b36(o["rev"]), a, o["id"], *x)  # noqa: E731
        rows = []
        if step >= 3:
            rows.append([f.btn(I18N.t(lang, "btn_track"), url=TRACK_URL + o["id"])])
        if st == "out_for_delivery":
            rows.append([f.btn(I18N.t(lang, "btn_courier"), data("courier"))])
        if st in ("placed", "packed"):
            rows.append([f.btn(I18N.t(lang, "btn_addr"), data("addr"))])
        elif st != "delivered":
            rows.append([f.btn(I18N.t(lang, "btn_addr_locked"), disabled=True)])   # shown, with its reason
        if st == "delivered":
            if o.get("rating"):
                text += I18N.t(lang, "rated", n=o["rating"])
            else:
                text += I18N.t(lang, "rate_ask")
                rows.append([f.btn(str(n), data("rate", n)) for n in range(1, 6)])
        return {"text": text, "parse_mode": "HTML", "reply_markup": f.kb(*rows)}

    def place(self, user: dict, oid: str, address: str, eta: int) -> dict:
        o = {"id": oid, "user": user["id"], "lang": I18N.lang_for(user.get("language_code")), "status": "placed",
             "address": address, "eta": eta, "seq": 0, "rev": 1, "card": None, "courier": None}
        self.orders[oid] = o
        self.send_card(o)
        return o

    def send_card(self, o: dict) -> None:
        o["card"] = self.t.call("sendMessage", {"chat_id": o["user"], **self.card(o)})["message_id"]

    def refresh(self, o: dict) -> str:
        """Edit the card in place; survive a deleted card and a flood wait."""
        o["rev"] += 1
        try:
            call_with_policy(self.t, "editMessageText", {"chat_id": o["user"], "message_id": o["card"], **self.card(o)},
                             sleep=self.waits.append)
            return "edited"
        except TelegramError as err:
            if "message to edit not found" not in err.description.lower():
                raise
            self.send_card(o)                        # the user deleted the card: a fresh one, new id remembered
            return "resent"

    # ---- courier events ----------------------------------------------------------
    def on_courier_event(self, ev: dict) -> str:
        o = self.orders.get(ev["order"])
        if o is None:
            return "unknown_order"
        if ev["seq"] <= o["seq"]:
            return "ignored_old_seq"                 # replayed or out-of-order: never roll the card back
        try:
            nxt = MACHINE.next(o["status"], ev["event"])
        except f.IllegalTransition:
            return "refused_illegal"                 # seq NOT advanced: the skipped event may still come
        o["seq"], o["status"] = ev["seq"], nxt
        o["eta"] = ev.get("eta", o["eta"])
        o["courier"] = ev.get("courier", o["courier"])
        if nxt == "delivered":
            o["delivered_at"] = NOW + 2 * 86400 + 14 * 3600
        self.refresh(o)                              # silent edit
        lang = o["lang"]
        if nxt == "out_for_delivery":                # the only two events that ring the phone
            self.t.call("sendMessage", {"chat_id": o["user"], "parse_mode": "HTML", "text": I18N.t(
                lang, "alert_out", oid=o["id"], name=o["courier"]["name"], when=when(o["eta"], False))})
        elif nxt == "delivered":
            self.t.call("sendMessage", {"chat_id": o["user"], "parse_mode": "HTML",
                                        "text": I18N.t(lang, "alert_done", oid=o["id"])})
        return nxt

    # ---- user side ---------------------------------------------------------------
    def on_callback(self, cq: dict) -> str:
        _, ver, action, oid, *rest = f.unpack(cq["data"])
        who, o = cq["from"], self.orders.get(oid)
        lang = I18N.lang_for(who.get("language_code"))

        def answer(text: str | None = None, alert: bool = False) -> None:
            params = {"callback_query_id": cq["id"]}
            if text:
                params.update(text=text, show_alert=alert)
            self.t.call("answerCallbackQuery", params)

        if o is None:
            answer(I18N.t(lang, "sys_expired"))
            return "expired"
        if who["id"] != o["user"]:
            answer(I18N.t(lang, "sys_not_yours"), True)
            return "not_yours"
        if ver != f.b36(o["rev"]):
            answer(I18N.t(lang, "sys_stale"))
            return "stale"
        if action == "addr":
            if o["status"] not in ("placed", "packed"):
                answer(I18N.t(o["lang"], "addr_locked"), True)
                return "addr_locked"
            self.awaiting[o["user"]] = o["id"]
            self.t.call("sendMessage", {"chat_id": o["user"], "text": I18N.t(o["lang"], "ask_addr"), "reply_markup": f.kb(
                [f.btn(I18N.t(o["lang"], "btn_keep"), f.pack("dt", f.b36(o["rev"]), "keep", o["id"]))], force_reply=True)})
            answer()
            return "address_requested"
        if action == "keep":
            self.awaiting.pop(o["user"], None)
            answer()
            return "kept"
        if action == "courier":
            c_ = o["courier"] or {}
            answer(I18N.t(o["lang"], "courier_info", name=c_.get("name", ""), phone=c_.get("phone", "")), True)
            return "courier_shown"
        if action == "rate":
            _, first = self.rated.run(o["id"], lambda: int(rest[0]))
            if not first:
                answer(I18N.t(o["lang"], "toast_rated"))
                return "already_rated"
            o["rating"] = int(rest[0])
            self.refresh(o)
            answer()
            return "rated"
        answer(I18N.t(lang, "sys_stale"))
        return "stale"

    def on_text(self, msg: dict) -> str:
        oid = self.awaiting.pop(msg["from"]["id"], None)
        if oid is None:
            return "ignored"
        o = self.orders[oid]
        if o["status"] not in ("placed", "packed"):     # shipped while the user was typing
            return "addr_locked"
        o["address"] = msg["text"][:200]
        self.refresh(o)
        return "address_saved"


def run(t: FakeTransport | None = None):
    t = t or FakeTransport()
    tr = Tracker(t)
    a = tr.place(ALICE, "O-5001", "12 Harbour St, Gdansk", NOW + 4 * 86400)
    tr.place(OLENA, "O-5002", "вул. Хрещатик 1, Київ", NOW + 3 * 86400)
    n = [0]

    def tap(who: dict, o: dict, action: str, *args, rev: int | None = None, chat: int | None = None) -> str:
        n[0] += 1
        data = f.pack("dt", f.b36(o["rev"] if rev is None else rev), action, o["id"], *args)
        return tr.on_callback(f.callback(f"cq{n[0]}", who, data, chat_id=chat or o["user"], message_id=o["card"]))

    out = {}
    # Alice changes the address while the parcel is still being packed.
    out["addr"] = tap(ALICE, a, "addr")
    out["saved"] = tr.on_text(f.text_message(ALICE, "5 Long Market, Gdansk"))
    events = c.fixture("usecase_delivery_courier_events.json")
    out["events"] = [tr.on_courier_event(ev) for ev in events[:6]]
    out["addr_late"] = tap(ALICE, a, "addr")                       # crafted: the button is disabled now
    out["courier"] = tap(ALICE, a, "courier")
    out["events"].append(tr.on_courier_event(events[6]))
    out["stranger"] = tap(OLENA, a, "rate", 5, chat=ALICE["id"])
    out["rate_stale"] = tap(ALICE, a, "rate", 5, rev=a["rev"] - 1)
    out["rate"] = tap(ALICE, a, "rate", 5)
    out["rate_again"] = tap(ALICE, a, "rate", 1)                   # current card, crafted data: refused
    # Olena (uk): her card was deleted by her; later the server asks for a flood wait.
    b = tr.orders["O-5002"]
    t.script("editMessageText", TelegramErrorResponse(400, "Bad Request: message to edit not found"))
    out["b_pack"] = tr.on_courier_event({"order": "O-5002", "seq": 1, "event": "pack"})
    out["b_card_after"] = b["card"]
    t.script("editMessageText", TelegramErrorResponse(429, "Too Many Requests: retry after 3", retry_after=3))
    out["b_ship"] = tr.on_courier_event({"order": "O-5002", "seq": 2, "event": "ship"})
    out["b_addr_locked"] = tap(OLENA, b, "addr")
    return t, tr, out


def main() -> None:
    t, tr, out = run()
    c.dump(t, "Delivery tracker")
    a = tr.orders["O-5001"]
    c.check(out["events"] == ["packed", "shipped", "ignored_old_seq", "ignored_old_seq", "refused_illegal",
                              "out_for_delivery", "delivered"] and a["status"] == "delivered",
            "statuses follow the Machine; older/replayed/skipping courier events are ignored")
    c.check(a["seq"] == 5, "a refused event does not advance the sequence (seq 4 was still accepted)")
    alice_msgs = [p for p in t.params_of("sendMessage") if p["chat_id"] == ALICE["id"]]
    c.check(len(alice_msgs) == 4 and sum("disable_notification" in p for p in alice_msgs) == 0,
            "card + address prompt + exactly two alert messages (out for delivery, delivered)")
    c.check(any("tg-time" in p["text"] for p in t.params_of("editMessageText")), "ETA is a <tg-time> entity")
    c.check(out["addr"] == "address_requested" and out["saved"] == "address_saved" and "5 Long Market" in a["address"]
            and out["addr_late"] == "addr_locked", "address change works before shipped, refused after with the reason")
    shipped = next(p for p in t.params_of("editMessageText") if "shipped" in p["text"] and p["chat_id"] == ALICE["id"])
    c.check({"text": "Change address · shipped", "disabled": {}} in shipped["reply_markup"]["inline_keyboard"][-1]
            and "Track" in str(shipped["reply_markup"]), "after shipping: Track appears, Change address is a disabled button")
    c.check(out["courier"] == "courier_shown", "Contact courier works once the courier is assigned")
    c.check([out["stranger"], out["rate_stale"], out["rate"], out["rate_again"]] ==
            ["not_yours", "stale", "rated", "already_rated"], "rating: owner only, current card only, once")
    c.check(out["b_pack"] == "packed" and tr.orders["O-5002"]["card"] != 1002 and out["b_card_after"] == tr.orders["O-5002"]["card"],
            "'message to edit not found' -> a fresh card, new id remembered")
    c.check(tr.waits == [3], "429: the retry_after from the server was waited, once")
    c.check(out["b_ship"] == "shipped" and out["b_addr_locked"] == "addr_locked", "second order: uk copy and the same lock")


if __name__ == "__main__":
    if "--write-payload" in sys.argv:
        print(f.write_payload(f.payload_doc(PAYLOAD, run()[0], status=STATUS, context=CONTEXT)))
    else:
        main()
