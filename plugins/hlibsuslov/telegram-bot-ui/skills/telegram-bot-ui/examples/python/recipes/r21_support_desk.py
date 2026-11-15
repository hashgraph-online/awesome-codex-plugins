"""R21 - Support desk: private chat <-> one forum topic per ticket in an operator group.

Invariants shown (offline, against fixtures):
* the ticket id exists even when the topic can't be created (403): the user still
  gets an id and the bot reports to a fallback admin chat;
* operator replies are relayed to the user, user replies into the topic; operator
  messages in OTHER topics are ignored and "//" notes never leave the group;
* statuses new/open/waiting/resolved go through a `Machine` - illegal moves are
  refused - and the status is visible in the topic name (editForumTopic);
* resolve closes the topic and asks for a 1-5 rating: once per resolution cycle,
  only by the ticket's owner, and never from a stale (older cycle) button;
* a redelivered message does not create a second ticket.

Run:  py -3 examples/python/recipes/r21_support_desk.py [--write-payload]
"""
from __future__ import annotations

import itertools
import sys

import _common as c
from tgkit import flows as f
from tgkit.errors import TelegramError
from tgkit.transport import FakeTransport, TelegramErrorResponse

PAYLOAD = "r21-support-desk"
STATUS = "production"
CONTEXT = "private chat + forum supergroup"
OPS_CHAT = -1001234567890          # operator supergroup (forum, bot has can_manage_topics)
ADMIN_CHAT = -1002222222222        # fallback: where the bot reports its own problems
OPS_LANG = "en"
ALICE = f.user(111111111, "Alice", "en")
IVAN = f.user(222222222, "Иван", "ru")
OLEG = f.user(333333333, "Oleg", "en")            # operator
NOTE_MARK = "//"                                    # internal note marker (never relayed)
CATEGORIES = {"billing": "Billing", "bug": "Bug", "other": "Other"}
EMOJI = {"new": "🆕", "open": "🟢", "waiting": "⏳", "resolved": "✅"}

COPY = {
    "en": {
        "menu": "<b>Support</b>\nWhat is this about?",
        "ask": "<b>{category}</b>\nDescribe the problem in one message. Screenshots are fine.",
        "created": "Ticket <b>{tid}</b> is open. An agent will reply right here.",
        "created_late": "Ticket <b>{tid}</b> is open. Replies may take a little longer today.",
        "from_agent": "<b>Support · {tid}</b>\n{text}",
        "to_topic": "<b>{name}:</b> {text}",
        "resolved": "<b>{tid} is resolved.</b> How did we do?",
        "thanks": "Thanks! You rated {tid}: {stars}/5.",
        "reopened": "Ticket <b>{tid}</b> reopened. An agent will reply here.",
        "card": "<b>{tid}</b> · {category}\nFrom: {name} · status: <b>{status}</b>\n\n{text}",
        "admin_alert": "No topic for <b>{tid}</b> ({reason}). Check can_manage_topics for the bot in the support group.",
        "status_new": "new", "status_open": "open", "status_waiting": "waiting for user", "status_resolved": "resolved",
        "cat_billing": "Billing", "cat_bug": "Bug", "cat_other": "Other",
        "btn_cancel": "Cancel", "btn_take": "Take", "btn_wait": "Wait for user",
        "btn_resolve": "Resolve", "btn_reopen": "Reopen",
        "toast_rated": "You already rated this ticket.",
        "toast_illegal": "Not possible for a {status} ticket.",
        "sys_stale": "This button is out of date.",
        "sys_not_yours": "This ticket belongs to someone else.",
        "sys_expired": "This menu has expired. Send /start.",
    },
    "ru": {
        "menu": "<b>Поддержка</b>\nПо какому вопросу?",
        "ask": "<b>{category}</b>\nОпишите проблему одним сообщением. Скриншоты можно.",
        "created": "Обращение <b>{tid}</b> открыто. Оператор ответит прямо здесь.",
        "created_late": "Обращение <b>{tid}</b> открыто. Сегодня ответ может прийти чуть позже.",
        "from_agent": "<b>Поддержка · {tid}</b>\n{text}",
        "to_topic": "<b>{name}:</b> {text}",
        "resolved": "<b>{tid} решено.</b> Как мы справились?",
        "thanks": "Спасибо! Оценка {tid}: {stars}/5.",
        "reopened": "Обращение <b>{tid}</b> снова открыто. Оператор ответит здесь.",
        "card": "<b>{tid}</b> · {category}\nОт: {name} · статус: <b>{status}</b>\n\n{text}",
        "admin_alert": "Нет темы для <b>{tid}</b> ({reason}). Проверьте право can_manage_topics у бота в группе поддержки.",
        "status_new": "новое", "status_open": "в работе", "status_waiting": "ждём клиента", "status_resolved": "решено",
        "cat_billing": "Оплата", "cat_bug": "Ошибка", "cat_other": "Другое",
        "btn_cancel": "Отмена", "btn_take": "Взять", "btn_wait": "Ждать клиента",
        "btn_resolve": "Решено", "btn_reopen": "Открыть снова",
        "toast_rated": "Вы уже оценили это обращение.",
        "toast_illegal": "Нельзя для обращения в статусе «{status}».",
        "sys_stale": "Эта кнопка устарела.",
        "sys_not_yours": "Это обращение другого человека.",
        "sys_expired": "Меню устарело. Отправьте /start.",
    },
}
I18N = f.I18n(COPY)

MACHINE = f.Machine({
    "new": {"take": "open", "operator_reply": "waiting", "user_msg": "new", "wait": "waiting", "resolve": "resolved"},
    "open": {"operator_reply": "waiting", "user_msg": "open", "wait": "waiting", "resolve": "resolved"},
    "waiting": {"take": "open", "operator_reply": "waiting", "user_msg": "open", "resolve": "resolved"},
    "resolved": {"user_msg": "open", "reopen": "open"},
}, "new")


class Desk:
    def __init__(self, t: FakeTransport):
        self.t = t
        self.flow = f.ScreenFlow(t, "sf", i18n=I18N)
        self.tickets: dict[str, dict] = {}
        self.by_thread: dict[tuple[int, int], str] = {}
        self.created = f.OnceStore()       # one ticket per user message
        self.ratings = f.OnceStore()       # one rating per ticket and resolution cycle
        self.updates = f.UpdateDedup()
        self.next_id = 1001
        self._screens()

    # ---- user wizard: category buttons, then a forced reply ------------------
    def _screens(self) -> None:
        fl = self.flow

        @fl.screen("menu")
        def menu(fl, s):
            rows = [[f.btn(fl.tr(s, f"cat_{k}"), fl.cb(s, "cat", k))] for k in CATEGORIES]
            return {"text": fl.tr(s, "menu"), "reply_markup": f.kb(*rows)}

        @fl.screen("ask")
        def ask(fl, s):
            # force_reply (10.3) opens the reply field with the buttons; it can't be
            # changed by an edit, so this screen is always a NEW message.
            return {"text": fl.tr(s, "ask", category=fl.tr(s, f"cat_{s.args['key']}")),
                    "reply_markup": f.kb([f.btn(fl.tr(s, "btn_cancel"), fl.cb(s, "cancel"))], force_reply=True)}

        @fl.action("cat")
        def a_cat(fl, s, args, cq):
            s.data["category"] = args[0]
            fl.open(s, "ask", new_message=True, key=args[0])

        @fl.action("cancel")
        def a_cancel(fl, s, args, cq):
            s.data.pop("category", None)
            fl.open(s, "menu", new_message=True)

    # ---- tickets -----------------------------------------------------------------
    def topic_name(self, tk: dict) -> str:
        return f"{EMOJI[tk['status']]} {tk['id']} · {CATEGORIES[tk['category']]}"[:128]

    def card(self, tk: dict) -> dict:
        def b(event: str, key: str, style: str | None = None) -> dict:
            label = I18N.t(OPS_LANG, key)
            if event in MACHINE.allowed(tk["status"]):
                return f.btn(label, f.pack("sd", f.b36(tk["rev"]), "op", tk["id"], event), style=style)
            return f.btn(label, disabled=True)

        last = b("reopen", "btn_reopen") if tk["status"] == "resolved" else b("resolve", "btn_resolve", "success")
        text = I18N.t(OPS_LANG, "card", tid=tk["id"], category=CATEGORIES[tk["category"]], name=tk["name"],
                      status=I18N.t(OPS_LANG, f"status_{tk['status']}"), text=tk["text"])
        return {"text": text, "parse_mode": "HTML",
                "reply_markup": f.kb([b("take", "btn_take", "primary"), b("wait", "btn_wait")], [last])}

    def open_ticket(self, user: dict, category: str, text: str) -> str:
        tid = f"T-{self.next_id}"
        self.next_id += 1
        lang = I18N.lang_for(user.get("language_code"))
        tk = {"id": tid, "user": user["id"], "name": user["first_name"], "lang": lang, "category": category,
              "text": text, "status": "new", "thread": None, "card": None, "rev": 0, "cycle": 1}
        self.tickets[tid] = tk
        try:
            topic = self.t.call("createForumTopic", {"chat_id": OPS_CHAT, "name": self.topic_name(tk)})
            tk["thread"] = topic["message_thread_id"]
            self.by_thread[(OPS_CHAT, tk["thread"])] = tid
            tk["card"] = self.t.call("sendMessage", {"chat_id": OPS_CHAT, "message_thread_id": tk["thread"],
                                                     **self.card(tk)})["message_id"]
        except TelegramError as err:
            if err.category != "permission":
                raise
            # The user must not notice: ticket id given, the problem goes to the admins.
            self.t.call("sendMessage", {"chat_id": ADMIN_CHAT, "parse_mode": "HTML",
                                        "text": I18N.t(OPS_LANG, "admin_alert", tid=tid, reason=err.description)})
        key = "created" if tk["thread"] else "created_late"
        self.t.call("sendMessage", {"chat_id": user["id"], "parse_mode": "HTML", "text": I18N.t(lang, key, tid=tid)})
        return tid

    def move(self, tk: dict, event: str) -> str:
        """Machine transition + everything that mirrors the status. Raises IllegalTransition."""
        old, tk["status"] = tk["status"], MACHINE.next(tk["status"], event)
        if tk["status"] == old:
            return old
        tk["rev"] += 1
        if tk["thread"]:
            self.t.call("editForumTopic", {"chat_id": OPS_CHAT, "message_thread_id": tk["thread"],
                                           "name": self.topic_name(tk)})
            self.t.call("editMessageText", {"chat_id": OPS_CHAT, "message_id": tk["card"], **self.card(tk)})
            if tk["status"] == "resolved":
                self.t.call("closeForumTopic", {"chat_id": OPS_CHAT, "message_thread_id": tk["thread"]})
            elif old == "resolved":
                self.t.call("reopenForumTopic", {"chat_id": OPS_CHAT, "message_thread_id": tk["thread"]})
        if tk["status"] == "resolved":
            row = [f.btn(str(n), f.pack("sd", f.b36(tk["cycle"]), "rate", tk["id"], n)) for n in range(1, 6)]
            self.t.call("sendMessage", {"chat_id": tk["user"], "parse_mode": "HTML", "reply_markup": f.kb(row),
                                        "text": I18N.t(tk["lang"], "resolved", tid=tk["id"])})
        elif old == "resolved":
            tk["cycle"] += 1                   # buttons of the previous resolution are now stale
            self.t.call("sendMessage", {"chat_id": tk["user"], "parse_mode": "HTML",
                                        "text": I18N.t(tk["lang"], "reopened", tid=tk["id"])})
        return tk["status"]

    # ---- incoming messages -------------------------------------------------------
    def on_private(self, msg: dict) -> str:
        user = msg["from"]
        lang = I18N.lang_for(user.get("language_code"))
        s = self.flow.session(user["id"], user["id"], lang=lang)
        text = msg.get("text") or ""
        if f"{user['id']}:{msg['message_id']}" in self.created.done:
            return "duplicate"                  # the same message again (new update id): no second ticket
        if text.startswith("/"):
            s.data.pop("category", None)
            self.flow.open(s, "menu", new_message=True)
            return "menu"
        if s.data.get("category"):
            category = s.data.pop("category")
            _, first = self.created.run(f"{user['id']}:{msg['message_id']}",
                                        lambda: self.open_ticket(user, category, text))
            return "created" if first else "duplicate"
        mine = [t for t in self.tickets.values() if t["user"] == user["id"]]
        if not mine:
            self.flow.open(s, "menu", new_message=True)
            return "menu"
        tk = mine[-1]
        before = tk["status"]
        self.move(tk, "user_msg")
        if tk["thread"]:
            self.t.call("sendMessage", {"chat_id": OPS_CHAT, "message_thread_id": tk["thread"], "parse_mode": "HTML",
                                        "text": I18N.t(OPS_LANG, "to_topic", name=tk["name"], text=text)})
        else:                                   # no topic: the admins still see it
            self.t.call("sendMessage", {"chat_id": ADMIN_CHAT, "text": f"{tk['id']}: {text}"})
        return "reopened" if before == "resolved" else "relayed_to_topic"

    def on_ops_message(self, msg: dict) -> str:
        thread = msg.get("message_thread_id") if msg.get("is_topic_message") else None
        tid = self.by_thread.get((msg["chat"]["id"], thread))
        if tid is None or msg["from"].get("is_bot"):
            return "ignored"                   # General topic, other topics, our own messages
        text = msg.get("text") or ""
        if text.startswith(NOTE_MARK):
            return "internal_note"             # never leaves the group
        tk = self.tickets[tid]
        try:
            self.move(tk, "operator_reply")
        except f.IllegalTransition:
            return "refused_resolved"
        self.t.call("sendMessage", {"chat_id": tk["user"], "parse_mode": "HTML",
                                    "text": I18N.t(tk["lang"], "from_agent", tid=tid, text=text)})
        return "relayed_to_user"

    # ---- operator buttons and rating ------------------------------------------------
    def on_callback(self, cq: dict) -> str:
        _, ver, action, tid, arg = (f.unpack(cq["data"]) + [""] * 5)[:5]
        who = cq["from"]
        lang = I18N.lang_for(who.get("language_code"))
        tk = self.tickets.get(tid)
        chat = (cq.get("message") or {}).get("chat", {}).get("id")

        def refuse(status: str, alert: bool = False) -> str:
            self.flow.answer(cq, I18N.t(lang, f"sys_{status}"), alert=alert)
            return status

        if tk is None:
            return refuse("expired")
        if action == "op":
            if chat != OPS_CHAT:
                return refuse("not_yours", True)
            if ver != f.b36(tk["rev"]):
                return refuse("stale")
            try:
                result = "status:" + self.move(tk, arg)
            except f.IllegalTransition:
                self.flow.answer(cq, I18N.t(lang, "toast_illegal", status=tk["status"]), alert=True)
                return "illegal"
            self.flow.answer(cq)
            return result
        if who["id"] != tk["user"]:
            return refuse("not_yours", True)
        if ver != f.b36(tk["cycle"]) or tk["status"] != "resolved":
            return refuse("stale")
        _, first = self.ratings.run(f"{tid}:{tk['cycle']}", lambda: arg)
        if not first:
            self.flow.answer(cq, I18N.t(lang, "toast_rated"))
            return "already_rated"
        self.t.call("editMessageText", {"chat_id": chat, "message_id": cq["message"]["message_id"],
                                        "parse_mode": "HTML",
                                        "text": I18N.t(lang, "thanks", tid=tid, stars=arg)})
        self.flow.answer(cq)
        return "rated"

    def dispatch(self, update: dict) -> str:
        if not self.updates.first_time(update):
            return "duplicate_update"
        if "callback_query" in update:
            result = self.flow.handle(update["callback_query"])
            return self.on_callback(update["callback_query"]) if result == "foreign" else result
        msg = update["message"]
        if msg["chat"]["id"] == OPS_CHAT:
            return self.on_ops_message(msg)
        return self.on_private(msg) if msg["chat"]["type"] == "private" else "ignored"


def run(t: FakeTransport | None = None):
    t = t or FakeTransport()
    threads = itertools.count(5001)
    topic = lambda m, p: {"message_thread_id": next(threads), "name": p["name"], "icon_color": 7322096}  # noqa: E731
    t.script("createForumTopic", topic, TelegramErrorResponse(403, "Forbidden: not enough rights to create a topic"))
    desk = Desk(t)
    n = itertools.count(1)

    def say(who: dict, text: str, mid: int | None = None) -> str:
        mid = mid or 100 + next(n)
        return desk.dispatch({"update_id": 500 + next(n) + mid, "message": f.text_message(who, text, message_id=mid)})

    def tap(who: dict, data: str, chat: int, message_id: int) -> str:
        return desk.dispatch({"update_id": 800 + next(n), "callback_query":
                              f.callback(f"cq{next(n)}", who, data, chat_id=chat, message_id=message_id)})

    def ui_tap(who: dict, action: str, *args) -> str:
        s = desk.flow.sessions[(who["id"], who["id"])]
        return tap(who, f.pack("sf", f.b36(s.version), action, *args), who["id"], s.message_id)

    out = {}
    out["menu"] = say(ALICE, "/start")
    out["cat"] = ui_tap(ALICE, "cat", "billing")
    out["create"] = say(ALICE, "I was charged twice for the same order.", mid=201)
    out["redeliver"] = say(ALICE, "I was charged twice for the same order.", mid=201)     # same message again
    tk = desk.tickets["T-1001"]
    out["reply"] = desk.dispatch(c.fixture("usecase_support_operator_reply.json"))
    out["other_topic"] = desk.dispatch(c.fixture("usecase_support_other_topic.json"))
    out["note"] = desk.dispatch({"update_id": 930010, "message": {
        **c.fixture("usecase_support_operator_reply.json")["message"], "message_id": 7010,
        "text": f"{NOTE_MARK} check the ledger before refunding"}})
    out["user_reply"] = say(ALICE, "Thanks, take your time.")
    out["illegal"] = tap(OLEG, f.pack("sd", f.b36(tk["rev"]), "op", "T-1001", "take"), OPS_CHAT, tk["card"])  # open
    out["wait"] = tap(OLEG, f.pack("sd", f.b36(tk["rev"]), "op", "T-1001", "wait"), OPS_CHAT, tk["card"])
    out["stale_op"] = tap(OLEG, f.pack("sd", f.b36(tk["rev"] - 1), "op", "T-1001", "wait"), OPS_CHAT, tk["card"])
    out["resolve"] = tap(OLEG, f.pack("sd", f.b36(tk["rev"]), "op", "T-1001", "resolve"), OPS_CHAT, tk["card"])
    rate = lambda n: f.pack("sd", f.b36(1), "rate", "T-1001", n)  # noqa: E731
    out["rate_stranger"] = tap(IVAN, rate(1), ALICE["id"], 900)
    out["rate"] = tap(ALICE, rate(5), ALICE["id"], 900)
    out["rate_twice"] = tap(ALICE, rate(4), ALICE["id"], 900)
    out["op_after_resolve"] = desk.on_ops_message({**c.fixture("usecase_support_operator_reply.json")["message"],
                                                   "message_id": 7020})
    out["reopen"] = say(ALICE, "It happened again today.")
    out["rate_stale"] = tap(ALICE, rate(3), ALICE["id"], 900)
    # Ivan (ru) opens a ticket while the bot can't create topics: 403 -> fallback.
    say(IVAN, "/start")
    ui_tap(IVAN, "cat", "bug")
    out["fallback"] = say(IVAN, "Бот не отвечает на /start.", mid=301)
    return t, desk, out


def main() -> None:
    t, desk, out = run()
    c.dump(t, "Support desk")
    topic = t.params_of("createForumTopic")[0]
    c.check(out["create"] == "created" and "T-1001" in topic["name"] and topic["name"].startswith("🆕"),
            "a ticket creates a topic named with its id and status")
    c.check(any(p.get("reply_markup", {}).get("force_reply") for p in t.params_of("sendMessage")),
            "the category step uses a force_reply keyboard")
    c.check(out["redeliver"] == "duplicate" and len(desk.tickets) == 2, "a redelivered message opens one ticket, not two")
    c.check(out["reply"] == "relayed_to_user" and out["other_topic"] == "ignored" and out["note"] == "internal_note",
            "operator reply relayed; other topic ignored; // note stays internal")
    c.check(not any("check the ledger" in p.get("text", "") for p in t.params_of("sendMessage")),
            "the internal note reached no one")
    c.check(out["user_reply"] == "relayed_to_topic" and desk.tickets["T-1001"]["thread"] == 5001,
            "the user's reply goes into the ticket's topic")
    c.check(out["wait"] == "status:waiting" and out["illegal"] == "illegal" and out["stale_op"] == "stale",
            "Machine refuses an illegal move; a stale operator button is refused")
    c.check(len(t.params_of("closeForumTopic")) == 1 and out["resolve"] == "status:resolved",
            "resolve closes the topic and asks for a rating")
    c.check([out["rate_stranger"], out["rate"], out["rate_twice"]] == ["not_yours", "rated", "already_rated"],
            "rating: another user refused, once only")
    c.check(out["op_after_resolve"] == "refused_resolved" and out["reopen"] == "reopened"
            and len(t.params_of("reopenForumTopic")) == 1, "a new user message reopens a resolved ticket")
    c.check(out["rate_stale"] == "stale", "a rating button of the previous resolution is stale")
    c.check(out["fallback"] == "created" and desk.tickets["T-1002"]["thread"] is None
            and any(p["chat_id"] == ADMIN_CHAT for p in t.params_of("sendMessage")),
            "403 on createForumTopic: ticket id still delivered, admins told")


if __name__ == "__main__":
    if "--write-payload" in sys.argv:
        print(f.write_payload(f.payload_doc(PAYLOAD, run()[0], status=STATUS, context=CONTEXT)))
    else:
        main()
