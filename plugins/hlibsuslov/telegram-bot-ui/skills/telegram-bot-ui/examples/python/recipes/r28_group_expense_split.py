"""R28 - Group utility: expense split on one shared card with personal panels.

The card in the supergroup is shared state (title, people, total) and is edited in
place. Everything personal - a balance, who owes whom, the "add expense" form - is an
ephemeral panel shown to the presser only (Bot API 10.4: callback_query_id without
receiver_user_id). When the ephemeral reply fails, the content never goes public:
an alert of at most 200 characters, otherwise a t.me/<bot>?start deep link.

Invariants shown (offline, against fixtures):
* "Add" with the same client op id creates one expense (OnceStore);
* only the creditor's tap confirms a payment; a debtor or a bystander is refused;
* a user who is not in the trip gets "join first" with a Join button;
* the card never carries a person's amount, and nothing personal is posted to the group;
* while a settlement round is open, new expenses are refused (balances must not move).

Run:  py -3 examples/python/recipes/r28_group_expense_split.py [--write-payload]
"""
from __future__ import annotations

import html
import re
import sys

import _common as c
from tgkit import flows as f
from tgkit.ephemeral import AudienceViolation, ephemeral_params, guard_audience
from tgkit.errors import OutcomeUnknown, TelegramError
from tgkit.transport import FakeTransport, TelegramErrorResponse

PAYLOAD = "r28-group-expense-split"
STATUS = "production"
CONTEXT = "supergroup"
GROUP = -1001234567890
BOT = "trip_split_bot"
TITLE = "Trip to Lviv"
GROUP_LANG = "uk"                     # the shared card has one language; panels follow the presser
ALICE = f.user(111111111, "Alice", "en")
BOGDAN = f.user(222222222, "Богдан", "uk")
OLENA = f.user(333333333, "Олена", "uk")
DANA = f.user(444444444, "Dana", "en")
MARK = f.user(666666666, "Mark", "en")
STEP = 100
ALERT_LIMIT = 200

COPY = {
    "en": {
        "card": "<b>{title}</b> · {people} people · total ₴{total}\nExpenses: {count}",
        "card_settling": "\nSettling up: {done} of {all} confirmed",
        "bal": "<b>Your balance</b>\nPaid by you: ₴{paid}\nYour share: ₴{share}\n{verdict}",
        "bal_plus": "You are owed ₴{amount}.", "bal_minus": "You owe ₴{amount}.", "bal_even": "You're all square.",
        "add": "<b>New expense</b>\nAmount: ₴{amount}\nSplit: {split}",
        "split_equal": "equally among {n}", "split_some": "you and {names}",
        "added": "Added ₴{amount}. Split: {split}.", "dup": "Already added.",
        "join_first": "Join <b>{title}</b> first to see balances and add expenses.",
        "joined": "You joined <b>{title}</b>.",
        "need_other": "Pick at least one person to split with.",
        "locked": "Settling up is in progress. Finish it before adding expenses.",
        "set_head": "<b>Settle up</b>\n{lines}", "set_none": "Nothing to settle for you right now.",
        "set_pay": "You pay {name} ₴{amount} — {state}", "set_get": "{name} pays you ₴{amount} — {state}",
        "st_open": "not paid yet", "st_marked": "marked as paid", "st_confirmed": "confirmed",
        "marked": "Marked as paid. {name} will confirm.", "confirmed": "Confirmed.",
        "only_creditor": "Only {name} can confirm this payment.",
        "btn_add": "Add expense", "btn_bal": "My balance", "btn_settle": "Settle up", "btn_join": "Join",
        "btn_close": "Close", "btn_equal": "Equal split", "btn_save": "Add ₴{amount}",
        "btn_paid": "I paid {name}", "btn_confirm": "Confirm {name}",
        "sys_stale": "This panel has changed. Open it again from the card.",
        "sys_not_yours": "This panel belongs to someone else.",
        "sys_expired": "This panel has expired. Tap the card again.",
    },
    "uk": {
        "card": "<b>{title}</b> · {people} учасн. · разом ₴{total}\nВитрат: {count}",
        "card_settling": "\nРозрахунок: підтверджено {done} із {all}",
        "bal": "<b>Ваш баланс</b>\nВи заплатили: ₴{paid}\nВаша частка: ₴{share}\n{verdict}",
        "bal_plus": "Вам винні ₴{amount}.", "bal_minus": "Ви винні ₴{amount}.", "bal_even": "Ви в розрахунку.",
        "add": "<b>Нова витрата</b>\nСума: ₴{amount}\nПоділ: {split}",
        "split_equal": "порівну на {n}", "split_some": "ви та {names}",
        "added": "Додано ₴{amount}. Поділ: {split}.", "dup": "Уже додано.",
        "join_first": "Спершу приєднайтеся до <b>{title}</b>, щоб бачити баланс і додавати витрати.",
        "joined": "Ви приєдналися до <b>{title}</b>.",
        "need_other": "Оберіть хоча б ще одну людину для поділу.",
        "locked": "Триває розрахунок. Завершіть його перед новими витратами.",
        "set_head": "<b>Розрахунок</b>\n{lines}", "set_none": "Зараз вам нічого розраховувати.",
        "set_pay": "Ви платите {name} ₴{amount} — {state}", "set_get": "{name} платить вам ₴{amount} — {state}",
        "st_open": "ще не сплачено", "st_marked": "позначено сплаченим", "st_confirmed": "підтверджено",
        "marked": "Позначено сплаченим. {name} підтвердить.", "confirmed": "Підтверджено.",
        "only_creditor": "Підтвердити платіж може лише {name}.",
        "btn_add": "Додати витрату", "btn_bal": "Мій баланс", "btn_settle": "Розрахуватись", "btn_join": "Приєднатись",
        "btn_close": "Закрити", "btn_equal": "Порівну", "btn_save": "Додати ₴{amount}",
        "btn_paid": "Я заплатив(ла) {name}", "btn_confirm": "Підтвердити {name}",
        "sys_stale": "Панель змінилась. Відкрийте її знову з картки.",
        "sys_not_yours": "Ця панель належить іншій людині.",
        "sys_expired": "Панель застаріла. Натисніть картку ще раз.",
    },
}
I18N = f.I18n(COPY)
TRANSFER = f.Machine({"open": {"paid": "marked"}, "marked": {"confirm": "confirmed"}, "confirmed": {}}, "open")


def plain(lang: str, key: str, **values) -> str:
    return html.unescape(I18N.t(lang, key, **values))


class Trip:
    def __init__(self, t: FakeTransport, members: dict[int, str]):
        self.t, self.members = t, dict(members)
        self.expenses: list[dict] = []
        self.transfers: dict[str, dict] = {}
        self.drafts: dict[str, dict] = {}
        self.ops = f.OnceStore()                      # one expense per client op id
        self.updates = f.UpdateDedup()
        self.card_id: int | None = None
        self.panels: dict[tuple[int, int], int] = {}  # (chat, user) -> ephemeral_message_id
        self.log: list[dict] = []
        self._answered: set[str] = set()

    # ---- money ----------------------------------------------------------------
    @staticmethod
    def shares(e: dict) -> dict[int, int]:
        ids = sorted(e["split"])
        base, rest = divmod(e["amount"], len(ids))
        return {u: base + (1 if i < rest else 0) for i, u in enumerate(ids)}

    def net(self) -> dict[int, int]:
        n = dict.fromkeys(self.members, 0)
        for e in self.expenses:
            n[e["payer"]] += e["amount"]
            for u, share in self.shares(e).items():
                n[u] -= share
        for tr in self.transfers.values():
            if tr["state"] == "confirmed":
                n[tr["frm"]] += tr["amount"]
                n[tr["to"]] -= tr["amount"]
        return n

    def round_open(self) -> bool:
        return any(tr["state"] != "confirmed" for tr in self.transfers.values())

    def open_round(self) -> None:
        if self.round_open():
            return
        n = self.net()
        debt = sorted(([-a, u] for u, a in n.items() if a < 0), reverse=True)
        owed = sorted(([a, u] for u, a in n.items() if a > 0), reverse=True)
        rnd = len({tr["round"] for tr in self.transfers.values()}) + 1
        while debt and owed:
            pay = min(debt[0][0], owed[0][0])
            tid = f"t{len(self.transfers) + 1}"
            self.transfers[tid] = {"id": tid, "frm": debt[0][1], "to": owed[0][1], "amount": pay,
                                   "state": "open", "round": rnd}
            debt[0][0] -= pay
            owed[0][0] -= pay
            debt, owed = [d for d in debt if d[0]], [o for o in owed if o[0]]

    # ---- shared card ------------------------------------------------------------
    def card(self) -> dict:
        last = max((tr["round"] for tr in self.transfers.values()), default=0)
        cur = [tr for tr in self.transfers.values() if tr["round"] == last]
        text = I18N.t(GROUP_LANG, "card", title=TITLE, people=len(self.members),
                      total=sum(e["amount"] for e in self.expenses), count=len(self.expenses))
        if self.round_open():
            text += I18N.t(GROUP_LANG, "card_settling", done=sum(tr["state"] == "confirmed" for tr in cur), all=len(cur))
        kb = f.kb([f.btn(plain(GROUP_LANG, "btn_add"), f.pack("ex", "add"), style="primary"),
                   f.btn(plain(GROUP_LANG, "btn_bal"), f.pack("ex", "bal"))],
                  [f.btn(plain(GROUP_LANG, "btn_settle"), f.pack("ex", "set"))])
        return {"text": text, "parse_mode": "HTML", "reply_markup": kb}

    def post_card(self) -> None:
        self.card_id = self.t.call("sendMessage", {"chat_id": GROUP, **self.card()})["message_id"]

    def refresh_card(self) -> None:
        try:
            self.t.call("editMessageText", {"chat_id": GROUP, "message_id": self.card_id, **self.card()})
        except TelegramError as err:
            if err.category != "not_modified":
                raise

    # ---- personal panels (ephemeral, with a fallback that keeps the audience) -------
    def answer(self, cq: dict, text: str | None = None, *, alert: bool = False, url: str | None = None) -> None:
        if cq["id"] in self._answered:
            return
        self._answered.add(cq["id"])
        p: dict = {"callback_query_id": cq["id"]}
        if text:
            p.update(text=text[:ALERT_LIMIT], **({"show_alert": True} if alert else {}))
        if url:
            p["url"] = url
        self.t.call("answerCallbackQuery", p)

    def respond(self, cq: dict, text: str, rows: list[list[dict]]) -> str:
        """Edit the presser's panel if the tap came from one, else open a new ephemeral panel."""
        markup = f.kb(*rows)
        msg = cq["message"]
        if msg.get("ephemeral_message_id"):
            self.t.call("editEphemeralMessageText", {
                "chat_id": msg["chat"]["id"], "receiver_user_id": cq["from"]["id"],
                "ephemeral_message_id": msg["ephemeral_message_id"], "text": text, "parse_mode": "HTML",
                "reply_markup": markup})
            self.answer(cq)
            return "edited"
        return self.show_panel(cq, text, markup)

    def show_panel(self, cq: dict, text: str, markup: dict) -> str:
        params = {**ephemeral_params(cq), "text": text, "parse_mode": "HTML", "reply_markup": markup}
        guard_audience("sendMessage", params, personal=True, owner_id=cq["from"]["id"])
        try:
            sent = self.t.call("sendMessage", params)
        except OutcomeUnknown:                         # it may have appeared: a repeat tap re-renders
            self.answer(cq)
            return "unknown"
        except TelegramError as err:
            self.log.append({"event": "ephemeral_failed", "class": err.category})
            return self.fallback(cq, text)
        self.panels[(cq["message"]["chat"]["id"], cq["from"]["id"])] = sent["ephemeral_message_id"]
        self.answer(cq)                                # an ephemeral reply does not replace this
        return "ephemeral"

    def fallback(self, cq: dict, text: str) -> str:
        shown = html.unescape(re.sub(r"<[^>]+>", "", text))
        if len(shown) <= ALERT_LIMIT:                  # only the presser sees an alert
            self.answer(cq, shown, alert=True)
            return "alert"
        chat = cq["message"]["chat"]["id"]
        self.answer(cq, url=f"https://t.me/{BOT}?start=bal_{f.b36(abs(chat))}")   # the DM is built per user
        return "deep_link"

    # ---- callbacks ----------------------------------------------------------------
    def names(self, ids) -> str:
        return ", ".join(self.members[u] for u in sorted(ids))

    def split_text(self, lang: str, d: dict) -> str:
        if set(d["split"]) == set(self.members):
            return I18N.t(lang, "split_equal", n=len(self.members))
        return I18N.t(lang, "split_some", names=f.Raw(f.escape_html(self.names(set(d["split"]) - {d["user"]}))))

    def draft_panel(self, cq: dict, lang: str, op: str) -> str:
        d = self.drafts[op]
        rows = [[f.btn(f"−{STEP}", f.pack("ex", "amt", op, -STEP)), f.btn(f"₴{d['amount']}", disabled=True),
                 f.btn(f"+{STEP}", f.pack("ex", "amt", op, STEP))],
                [f.btn(plain(lang, "btn_equal"), f.pack("ex", "eq", op))],
                [f.btn(("✓ " if u in d["split"] else "") + self.members[u], f.pack("ex", "tog", op, u))
                 for u in sorted(self.members) if u != d["user"]],
                [f.btn(plain(lang, "btn_save", amount=d["amount"]), f.pack("ex", "save", op), style="primary")]]
        return self.respond(cq, I18N.t(lang, "add", amount=d["amount"], split=f.Raw(self.split_text(lang, d))), rows)

    def settle_panel(self, cq: dict, lang: str) -> str:
        me, lines, rows = cq["from"]["id"], [], []
        for tr in self.transfers.values():
            if me not in (tr["frm"], tr["to"]):
                continue
            other = self.members[tr["to"] if me == tr["frm"] else tr["frm"]]
            state = I18N.t(lang, "st_" + tr["state"])
            lines.append(I18N.t(lang, "set_pay" if me == tr["frm"] else "set_get", name=other, amount=tr["amount"],
                                state=state))
            if me == tr["frm"] and tr["state"] == "open":
                rows.append([f.btn(plain(lang, "btn_paid", name=other), f.pack("ex", "paid", tr["id"]))])
            if me == tr["to"] and tr["state"] == "marked":
                rows.append([f.btn(plain(lang, "btn_confirm", name=other), f.pack("ex", "ok", tr["id"]), style="success")])
        if not lines:
            return self.respond(cq, I18N.t(lang, "set_none"), [[f.btn(plain(lang, "btn_close"), f.pack("ex", "close"))]])
        rows.append([f.btn(plain(lang, "btn_close"), f.pack("ex", "close"))])
        return self.respond(cq, I18N.t(lang, "set_head", lines=f.Raw("\n".join(lines))), rows)

    def on_callback(self, cq: dict) -> str:
        parts = f.unpack(cq.get("data"))
        if parts[0] != "ex":
            return "foreign"
        user, msg = cq["from"], cq["message"]
        lang, action, me = I18N.lang_for(user.get("language_code")), parts[1], user["id"]
        if (msg.get("receiver_user") or {}).get("id", me) != me:       # someone else's panel
            self.answer(cq, plain(lang, "sys_not_yours"), alert=True)
            return "not_yours"
        if action == "close":
            self.t.call("deleteEphemeralMessage", {"chat_id": msg["chat"]["id"], "receiver_user_id": me,
                                                   "ephemeral_message_id": msg["ephemeral_message_id"]})
            self.answer(cq)
            return "closed"
        if action == "join":
            self.members.setdefault(me, user["first_name"])
            self.refresh_card()
            return self.respond(cq, I18N.t(lang, "joined", title=TITLE), [[f.btn(plain(lang, "btn_close"), f.pack("ex", "close"))]])
        if me not in self.members:                                      # not a participant: join first
            return self.respond(cq, I18N.t(lang, "join_first", title=TITLE),
                                [[f.btn(plain(lang, "btn_join"), f.pack("ex", "join"), style="primary")]])
        if action == "bal":
            paid = sum(e["amount"] for e in self.expenses if e["payer"] == me)
            share = sum(self.shares(e).get(me, 0) for e in self.expenses)
            n = self.net()[me]
            verdict = I18N.t(lang, "bal_plus" if n > 0 else "bal_minus" if n < 0 else "bal_even", amount=abs(n))
            return self.respond(cq, I18N.t(lang, "bal", paid=paid, share=share, verdict=verdict),
                                [[f.btn(plain(lang, "btn_settle"), f.pack("ex", "set")),
                                  f.btn(plain(lang, "btn_close"), f.pack("ex", "close"))]])
        if action == "add":
            if self.round_open():
                self.answer(cq, plain(lang, "locked"), alert=True)
                return "locked"
            op = f.b36(len(self.drafts) + 1)
            self.drafts[op] = {"user": me, "amount": 12 * STEP, "split": set(self.members)}
            return self.draft_panel(cq, lang, op)
        if action == "set":
            self.open_round()
            return self.settle_panel(cq, lang)
        if action in ("amt", "eq", "tog", "save"):
            return self.on_draft(cq, lang, action, parts[2], parts[3:])
        if action in ("paid", "ok"):
            return self.on_transfer(cq, lang, action, parts[2])
        self.answer(cq, plain(lang, "sys_stale"))
        return "stale"

    def on_draft(self, cq: dict, lang: str, action: str, op: str, args: list[str]) -> str:
        d, me = self.drafts.get(op), cq["from"]["id"]
        if d is None:
            self.answer(cq, plain(lang, "sys_expired"))
            return "expired"
        if d["user"] != me:
            self.answer(cq, plain(lang, "sys_not_yours"), alert=True)
            return "not_yours"
        if action == "save":
            if len(d["split"]) < 2:
                self.answer(cq, plain(lang, "need_other"), alert=True)
                return "need_other"
            _, first = self.ops.run(f"{op}", lambda: self.add_expense(d))
            if not first:
                self.answer(cq, plain(lang, "dup"))
                return "duplicate_add"
            self.refresh_card()
            return self.respond(cq, I18N.t(lang, "added", amount=d["amount"], split=f.Raw(self.split_text(lang, d))),
                                [[f.btn(plain(lang, "btn_close"), f.pack("ex", "close"))]])
        if op in self.ops.done:                                         # already saved: the form is dead
            self.answer(cq, plain(lang, "sys_stale"))
            return "stale"
        if action == "amt":
            d["amount"] = max(STEP, d["amount"] + int(args[0]))
        elif action == "eq":
            d["split"] = set(self.members)
        else:
            uid = int(args[0])
            d["split"] ^= {uid} if uid in self.members and uid != me else set()
        return self.draft_panel(cq, lang, op)

    def add_expense(self, d: dict) -> dict:
        e = {"id": len(self.expenses) + 1, "payer": d["user"], "amount": d["amount"], "split": sorted(d["split"])}
        self.expenses.append(e)
        return e

    def on_transfer(self, cq: dict, lang: str, action: str, tid: str) -> str:
        tr, me = self.transfers.get(tid), cq["from"]["id"]
        if tr is None:
            self.answer(cq, plain(lang, "sys_expired"))
            return "expired"
        who = tr["frm"] if action == "paid" else tr["to"]
        if me != who:                                   # only the creditor's tap confirms a payment
            key, other = ("sys_not_yours", None) if action == "paid" else ("only_creditor", tr["to"])
            self.answer(cq, plain(lang, key, **({"name": self.members[other]} if other else {})), alert=True)
            return "not_yours" if action == "paid" else "not_creditor"
        try:
            tr["state"] = TRANSFER.next(tr["state"], action if action == "paid" else "confirm")
        except f.IllegalTransition:
            self.answer(cq, plain(lang, "sys_stale"))
            return "stale"
        self.refresh_card()
        self.answer(cq, plain(lang, "marked", name=self.members[tr["to"]]) if action == "paid" else plain(lang, "confirmed"))
        return self.settle_panel(cq, lang)

    def on_message(self, msg: dict) -> str:
        if msg["chat"]["id"] == GROUP and msg.get("text", "").startswith("/trip"):
            self.post_card()
            return "card"
        return "ignored"

    def dispatch(self, update: dict) -> str:
        if not self.updates.first_time(update):
            return "duplicate_update"
        if "callback_query" in update:
            return self.on_callback(update["callback_query"])
        return self.on_message(update["message"])


def run(t: FakeTransport | None = None):
    t = t or FakeTransport()
    trip = Trip(t, {111111111: "Alice", 222222222: "Богдан", 333333333: "Олена", 444444444: "Dana"})
    n = [0]
    log: dict[str, object] = {}

    def upd(cq: dict) -> dict:
        n[0] += 1
        return {"update_id": 4000 + n[0], "callback_query": cq}

    def ctap(who: dict, data: str) -> str:               # a button on the shared card
        cq = f.callback(f"cq{n[0] + 1}", who, data, chat_id=GROUP, message_id=trip.card_id, chat_type="supergroup")
        return trip.dispatch(upd(cq))

    def ptap(who: dict, data: str) -> str:               # a button inside the presser's own panel
        cq = f.callback(f"cq{n[0] + 1}", who, data, chat_id=GROUP, message_id=0, chat_type="supergroup")
        cq["message"].update(ephemeral_message_id=trip.panels[(GROUP, who["id"])], receiver_user=who)
        return trip.dispatch(upd(cq))

    trip.dispatch({"update_id": 3999, "message": f.text_message(ALICE, "/trip Trip to Lviv", chat_id=GROUP,
                                                                 chat_type="supergroup")})
    # Alice adds 1200 split equally; the Save tap arrives twice (fixture, retried).
    log["add"] = [ctap(ALICE, "ex:add")]
    saved = c.fixture("usecase_expense_panel_callback.json")
    log["save"] = [trip.dispatch(saved)]
    retry = c.fixture("usecase_expense_panel_callback.json")
    retry["update_id"], retry["callback_query"]["id"] = 920777, "4382000000000000099"
    log["save"].append(trip.dispatch(retry))
    # Bogdan: 800 for himself and Olena only; Dana crafts a tap on his form.
    log["draft"] = [ctap(BOGDAN, "ex:add"), ptap(BOGDAN, "ex:amt:2:-400"), ptap(BOGDAN, "ex:tog:2:111111111"),
                    ptap(BOGDAN, "ex:tog:2:444444444")]
    log["draft"].append(ptap(BOGDAN, "ex:tog:2:333333333"))            # alone: Save must be refused
    log["draft"].append(ptap(BOGDAN, "ex:save:2"))
    log["draft"].append(ptap(BOGDAN, "ex:tog:2:333333333"))
    trip.panels[(GROUP, DANA["id"])] = 7
    log["draft"].append(ptap(DANA, "ex:save:2"))
    log["draft"].append(ptap(BOGDAN, "ex:save:2"))
    # Bogdan's ephemeral reply fails: the balance is short enough for a private alert.
    t.script("sendMessage", TelegramErrorResponse(403, "Forbidden: not enough rights"))
    log["fallback"] = [ctap(BOGDAN, "ex:bal")]
    cq = f.callback("cq-long", OLENA, "ex:bal", chat_id=GROUP, message_id=trip.card_id, chat_type="supergroup")
    t.script("sendMessage", TelegramErrorResponse(403, "Forbidden: not enough rights"))
    many = f.Raw("\n".join(["Олена платить вам ₴700 — ще не сплачено"] * 6))  # a big group: a long panel
    log["fallback"].append(trip.show_panel(cq, I18N.t("uk", "set_head", lines=many),
                                           f.kb([f.btn(plain("uk", "btn_close"), f.pack("ex", "close"))])))
    log["bal"] = [ctap(ALICE, "ex:bal")]
    # Settle up: Dana (debtor) marks, tries to confirm her own payment; Alice (creditor) confirms.
    log["settle"] = [ctap(DANA, "ex:set"), ctap(OLENA, "ex:add"), ptap(DANA, "ex:paid:t2"), ptap(DANA, "ex:paid:t2"),
                     ptap(DANA, "ex:ok:t2"), ctap(BOGDAN, "ex:set")]
    log["settle"].append(trip.dispatch(upd(f.callback(f"cq{n[0] + 1}", BOGDAN, "ex:ok:t2", chat_id=GROUP, message_id=0,
                                                      chat_type="supergroup"))))
    log["settle"] += [ctap(ALICE, "ex:set"), ptap(ALICE, "ex:ok:t2")]
    # Mark is not in the trip: "join first", then Join.
    log["join"] = [ctap(MARK, "ex:bal"), ptap(MARK, "ex:join")]
    return t, trip, log


def main() -> None:
    t, trip, log = run()
    c.dump(t, "Expense split")
    c.check(log["save"][1] == "duplicate_add",
            "the same client op id twice creates one expense")
    c.check(len(trip.expenses) == 2 and trip.ops.runs == 2, "two expenses in total (one per op id)")
    c.check(log["draft"][5] == "need_other" and log["draft"][7] == "not_yours", "a split of only yourself and another user's form are refused")
    c.check(log["fallback"] == ["alert", "deep_link"], "ephemeral failure: short text -> private alert, long -> deep link")
    answers = t.params_of("answerCallbackQuery")
    c.check(any("url" in a and a["url"].startswith(f"https://t.me/{BOT}?start=") for a in answers) and
            all(len(a.get("text", "")) <= ALERT_LIMIT for a in answers), "alert text and deep link stay within the limits")
    group_calls = [(m, p) for m, p in t.calls if m in ("sendMessage", "editMessageText") and p.get("chat_id") == GROUP
                   and "ephemeral_message_parameters" not in p]
    names = ("Alice", "Богдан", "Олена", "Dana")
    c.check(group_calls and not any(nm in p["text"] for _, p in group_calls for nm in names),
            "nothing personal reaches the group: only the card (no names, no per-person amounts)")
    c.check(log["settle"][3] == "stale" and log["settle"][4] == "not_creditor" and log["settle"][6] == "not_creditor",
            "a second 'I paid' is stale; the debtor and a bystander cannot confirm")
    c.check(log["settle"][1] == "locked" and log["settle"][-1] == "edited" and trip.transfers["t2"]["state"] == "confirmed",
            "expenses are locked during a round; the creditor's tap confirms")
    c.check(log["join"][0] == "ephemeral" and MARK["id"] in trip.members and "5 учасн." in trip.card()["text"],
            "a non-participant gets 'join first' with a Join button; joining updates the card")
    try:
        guard_audience("sendMessage", {"chat_id": GROUP, "text": "balance"}, personal=True, owner_id=111111111)
        c.check(False, "guard must refuse")
    except AudienceViolation:
        c.check(True, "the audience guard refuses a public send of a balance")


if __name__ == "__main__":
    if "--write-payload" in sys.argv:
        print(f.write_payload(f.payload_doc(PAYLOAD, run()[0], status=STATUS, context=CONTEXT)))
    else:
        main()
