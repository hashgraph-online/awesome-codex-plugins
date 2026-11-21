"""R61 - Business-account bot: a bakery owner connects the bot to their Telegram
Business account; customers write to the owner, the bot answers on their behalf.

business_connection (rights) -> business_message (auto-reply, owner proposal) ->
owner taps a quick reply / writes their own -> sendMessage(business_connection_id) ->
connection disabled.

Invariants shown (offline, against fixtures):
* what the bot may do follows the granted rights: no can_reply = read-only mode,
  readBusinessMessage only with can_read_messages, replies only inside the 24 h window;
* messages sent on behalf of a business carry only inline url buttons (a reply keyboard
  is not supported there); quick replies are proposed to the OWNER in the bot's chat;
* a quick reply is sent once however often it is tapped; only the owner can tap;
* a message for an unknown or disabled connection is ignored and logged, never answered;
* "Manage Bot" (/start bizChat<user_chat_id>) opens the panel of that customer chat.

Run:  py -3 examples/python/recipes/r61_business_account.py [--write-payload]
"""
from __future__ import annotations

import re
import sys
import time

import _common as c
from tgkit import flows as f
from tgkit.transport import FakeTransport

PAYLOAD = "r61-business-account"
STATUS = "production"
CONTEXT = "business"
WINDOW = 24 * 3600                      # can_reply: chats with incoming messages in the last 24 hours
OKSANA = f.user(111111111, "Оксана", "uk")
IVAN = f.user(222222222, "Іван", "uk")
MARIA = f.user(333333333, "Maria", "en")
QUICK = ("hours", "special")

COPY = {
    "en": {
        "conn_ok": "<b>Connected: {name}</b>\nWhat I can do:\n{can}{cant}\n\nOpen a customer chat and tap <b>Manage Bot</b> for quick replies.",
        "conn_cant": "\n\nWhat I can't do:\n{lines}",
        "r_reply": "• Reply for you within 24 h of a customer's message",
        "r_read": "• Mark customer messages as read",
        "x_reply": "• Reply: access is off, so I work read-only",
        "x_read": "• Mark messages as read: access is off",
        "conn_off": "<b>Connection turned off</b>\nI stopped replying for {name}. Turn me on in Settings → Business → Chatbots.",
        "panel": "<b>{name}</b>\nLast message: «{last}»\n\nAuto-replies: {auto}\nYou can reply until {until}",
        "panel_ro": "<b>{name}</b>\nLast message: «{last}»\n\nRead-only mode: reply access is off.",
        "auto_on": "on",
        "auto_off": "paused",
        "compose": "Reply to this message with your text for <b>{name}</b>. It is sent from your account.",
        "own_bad": "The text must be 1-4096 characters. Reply to the message above again.",
        "no_chat": "I haven't seen this chat yet. It appears after the customer's first message.",
        "no_conn": "No active connection. Add me in Settings → Business → Chatbots.",
        "auto_hours": "Hi {name}! We're open 8:00-19:00, Monday to Saturday.",
        "auto_hello": "Hi {name}! Thanks for writing. The menu and opening hours are below.",
        "qr_hours": "We're open till 19:00 today.",
        "qr_special": "Today's special: cardamom buns, fresh at 10:00.",
        "toast_sent": "Sent to {name} ✓",
        "toast_already": "Already sent.",
        "toast_window": "The 24 h window is closed: the customer must write first.",
        "toast_off": "The connection is turned off.",
        "toast_no_reply": "Reply access is off.",
        "toast_auto": "Auto-replies: {state}",
        "btn_qr_hours": "Send: open till 19:00",
        "btn_qr_special": "Send: today's special",
        "btn_own": "Write my own",
        "btn_pause": "Pause auto-replies",
        "btn_resume": "Resume auto-replies",
        "btn_no_reply": "Reply access is off",
        "btn_window": "24 h window closed",
        "btn_back": "← Back",
        "btn_menu": "Menu",
        "btn_map": "How to find us",
        "sys_stale": "This panel has changed. Use the latest message.",
        "sys_not_yours": "This panel belongs to the account owner.",
        "sys_expired": "This panel has expired. Tap Manage Bot in the chat.",
    },
    "uk": {
        "conn_ok": "<b>Підключено: {name}</b>\nЩо я можу:\n{can}{cant}\n\nВідкрийте чат клієнта й натисніть <b>Керувати ботом</b>, щоб швидко відповісти.",
        "conn_cant": "\n\nЧого я не можу:\n{lines}",
        "r_reply": "• Відповідати за вас протягом 24 год після повідомлення клієнта",
        "r_read": "• Позначати повідомлення клієнтів прочитаними",
        "x_reply": "• Відповідати: доступ вимкнено, тож працюю лише на читання",
        "x_read": "• Позначати прочитаними: доступ вимкнено",
        "conn_off": "<b>Підключення вимкнено</b>\nЯ припинив відповіді для {name}. Увімкніть мене в Налаштування → Бізнес → Чат-боти.",
        "panel": "<b>{name}</b>\nОстаннє повідомлення: «{last}»\n\nАвтовідповіді: {auto}\nВідповісти можна до {until}",
        "panel_ro": "<b>{name}</b>\nОстаннє повідомлення: «{last}»\n\nРежим читання: доступу до відповідей немає.",
        "auto_on": "увімкнено",
        "auto_off": "на паузі",
        "compose": "Дайте відповідь на це повідомлення текстом для <b>{name}</b>. Він піде з вашого акаунта.",
        "own_bad": "Текст має містити 1-4096 символів. Дайте відповідь на повідомлення вище ще раз.",
        "no_chat": "Цей чат я ще не бачив. Він з'явиться після першого повідомлення клієнта.",
        "no_conn": "Немає активного підключення. Додайте мене в Налаштування → Бізнес → Чат-боти.",
        "auto_hours": "Вітаю, {name}! Ми працюємо з 8:00 до 19:00, з понеділка по суботу.",
        "auto_hello": "Вітаю, {name}! Дякуємо за повідомлення. Меню і години роботи нижче.",
        "qr_hours": "Сьогодні працюємо до 19:00.",
        "qr_special": "Сьогодні в меню: булочки з кардамоном, свіжі о 10:00.",
        "toast_sent": "Надіслано: {name} ✓",
        "toast_already": "Уже надіслано.",
        "toast_window": "Вікно 24 год закрите: спершу має написати клієнт.",
        "toast_off": "Підключення вимкнено.",
        "toast_no_reply": "Доступу до відповідей немає.",
        "toast_auto": "Автовідповіді: {state}",
        "btn_qr_hours": "Надіслати: до 19:00",
        "btn_qr_special": "Надіслати: меню дня",
        "btn_own": "Написати свою",
        "btn_pause": "Пауза автовідповідей",
        "btn_resume": "Увімкнути автовідповіді",
        "btn_no_reply": "Немає доступу до відповідей",
        "btn_window": "Вікно 24 год закрите",
        "btn_back": "← Назад",
        "btn_menu": "Меню",
        "btn_map": "Як нас знайти",
        "sys_stale": "Панель змінилась. Користуйтеся останнім повідомленням.",
        "sys_not_yours": "Ця панель належить власнику акаунта.",
        "sys_expired": "Панель застаріла. Натисніть «Керувати ботом» у чаті.",
    },
}
I18N = f.I18n(COPY)


class BizBot:
    def __init__(self, t: FakeTransport, now: int):
        self.t, self.now = t, now
        self.conns: dict[str, dict] = {}
        self.chats: dict[tuple[str, int], dict] = {}     # (connection id, customer chat) -> state
        self.sent = f.OnceStore()                        # one send per (connection, chat, message, reply)
        self.updates = f.UpdateDedup()
        self.log: list[dict] = []
        self.flow = f.ScreenFlow(t, "bz", i18n=I18N, log=self.log.append)
        self._screens()

    # ---- rights and sending ------------------------------------------------------
    def can_send(self, cid: str, chat: int) -> str | None:
        conn = self.conns.get(cid)
        if not conn or not conn["enabled"]:
            return "off"
        if not conn["rights"].get("can_reply"):
            return "no_reply"
        if self.now - self.chats[(cid, chat)]["last_date"] > WINDOW:
            return "window"
        return None

    def send(self, cid: str, chat: int, text: str, markup: dict | None = None) -> int:
        params = {"business_connection_id": cid, "chat_id": chat, "text": text, "parse_mode": "HTML"}
        if markup:
            params["reply_markup"] = markup      # inline keyboard only: no reply keyboard on behalf of a business
        return self.t.call("sendMessage", params)["message_id"]

    def owner_session(self, conn: dict) -> f.Session:
        return self.flow.session(conn["user_chat_id"], conn["owner"], lang=conn["lang"])

    # ---- business_connection ---------------------------------------------------------
    def on_connection(self, bc: dict) -> str:
        user = bc["user"]
        old = self.conns.get(bc["id"], {})
        conn = {"id": bc["id"], "owner": user["id"], "user_chat_id": bc["user_chat_id"], "name": user["first_name"],
                "lang": I18N.lang_for(user.get("language_code")), "rights": bc.get("rights") or {},
                "enabled": bc["is_enabled"]}
        self.conns[bc["id"]] = conn
        lang = conn["lang"]
        if not conn["enabled"]:
            if old.get("enabled"):               # tell the owner once, not on every redelivery
                self.t.call("sendMessage", {"chat_id": conn["user_chat_id"], "parse_mode": "HTML",
                                            "text": I18N.t(lang, "conn_off", name=conn["name"])})
            return "disabled"
        r = conn["rights"]
        can = [I18N.t(lang, k) for k, on in (("r_reply", r.get("can_reply")), ("r_read", r.get("can_read_messages"))) if on]
        cant = [I18N.t(lang, k) for k, on in (("x_reply", r.get("can_reply")), ("x_read", r.get("can_read_messages"))) if not on]
        self.t.call("sendMessage", {"chat_id": conn["user_chat_id"], "parse_mode": "HTML", "text": I18N.t(
            lang, "conn_ok", name=conn["name"], can=f.Raw("\n".join(can)),
            cant=f.Raw(I18N.t(lang, "conn_cant", lines=f.Raw("\n".join(cant))) if cant else ""))})
        return "connected"

    # ---- business_message ---------------------------------------------------------------
    def on_business_message(self, m: dict) -> str:
        cid = m["business_connection_id"]
        conn = self.conns.get(cid)
        if not conn or not conn["enabled"]:
            self.log.append({"event": "business_message_ignored", "connection": cid,
                             "why": "disabled" if conn else "unknown"})
            return "ignored_disabled" if conn else "ignored_unknown"
        if m["from"]["id"] == conn["owner"]:     # the owner's own messages arrive here too
            return "own_message"
        chat = m["chat"]["id"]
        self.chats[(cid, chat)] = {"name": m["from"]["first_name"], "lang": I18N.lang_for(m["from"].get("language_code")),
                                   "last_text": m.get("text", ""), "last_date": m["date"], "last_msg": m["message_id"],
                                   "auto": self.chats.get((cid, chat), {}).get("auto", True)}
        st = self.chats[(cid, chat)]
        if conn["rights"].get("can_read_messages"):
            self.t.call("readBusinessMessage", {"business_connection_id": cid, "chat_id": chat,
                                                "message_id": m["message_id"]})
        outcome = "read_only"
        if self.can_send(cid, chat) is None and st["auto"]:
            self.sent.run(f"auto:{cid}:{chat}:{m['message_id']}", lambda: self.auto_reply(cid, chat, st))
            outcome = "replied"
        s = self.owner_session(conn)
        self.flow.open(s, "panel", new_message=True, conn=cid, chat=chat)    # proposal to the OWNER
        return outcome

    def auto_reply(self, cid: str, chat: int, st: dict) -> int:
        asks_hours = re.search(r"hours|open|годин|відкрит|працю", st["last_text"].lower())
        text = I18N.t(st["lang"], "auto_hours" if asks_hours else "auto_hello", name=st["name"])
        urls = f.kb([f.btn(I18N.t(st["lang"], "btn_menu"), url="https://bakery.example/menu"),
                     f.btn(I18N.t(st["lang"], "btn_map"), url="https://bakery.example/map")])
        return self.send(cid, chat, text, urls)

    # ---- owner panel (the bot's private chat with the owner) --------------------------------
    def _screens(self) -> None:
        fl = self.flow

        @fl.screen("panel")
        def panel(fl, s):
            st = self.chats[(s.args["conn"], s.args["chat"])]
            why = self.can_send(s.args["conn"], s.args["chat"])
            base = {"name": st["name"], "last": st["last_text"][:80]}
            if why == "no_reply":
                return {"text": fl.tr(s, "panel_ro", **base),
                        "reply_markup": f.kb([f.btn(fl.tr(s, "btn_no_reply"), disabled=True)])}
            until = f.tg_time(st["last_date"] + WINDOW, time.strftime("%d %b %H:%M UTC", time.gmtime(st["last_date"] + WINDOW)))
            auto = fl.tr(s, "auto_on" if st["auto"] else "auto_off")
            rows = ([[f.btn(fl.tr(s, "btn_window"), disabled=True)]] if why == "window" else
                    [[f.btn(fl.tr(s, "btn_qr_hours"), fl.cb(s, "qr", "hours"), style="primary")],
                     [f.btn(fl.tr(s, "btn_qr_special"), fl.cb(s, "qr", "special"))],
                     [f.btn(fl.tr(s, "btn_own"), fl.cb(s, "own"))]])
            rows.append([f.btn(fl.tr(s, "btn_resume" if not st["auto"] else "btn_pause"), fl.cb(s, "auto"))])
            return {"text": fl.tr(s, "panel", **base, auto=auto, until=until), "reply_markup": f.kb(*rows)}

        @fl.screen("compose")
        def compose(fl, s):       # force_reply is fixed for a message: this screen is always a NEW message
            st = self.chats[(s.args["conn"], s.args["chat"])]
            return {"text": fl.tr(s, "compose", name=st["name"]),
                    "reply_markup": f.kb([f.btn(fl.tr(s, "btn_back"), fl.cb(s, "panel"))], force_reply=True)}

        @fl.action("qr")
        def a_qr(fl, s, args, cq):
            cid, chat = s.args["conn"], s.args["chat"]
            why = self.can_send(cid, chat)
            if why or args[0] not in QUICK:      # a disabled/old button can still be tapped: re-check
                fl.answer(cq, fl.tr(s, f"toast_{why}") if why else fl.sys_text("stale", cq, s), alert=True)
                fl.refresh(s)
                return f"refused_{why}" if why else "stale"
            st = self.chats[(cid, chat)]
            _, first = self.sent.run(f"qr:{cid}:{chat}:{st['last_msg']}:{args[0]}",
                                     lambda: self.send(cid, chat, I18N.t(st["lang"], f"qr_{args[0]}")))
            if not first:
                fl.answer(cq, fl.tr(s, "toast_already"))
                return "already_sent"
            fl.answer(cq, fl.tr(s, "toast_sent", name=st["name"]))
            fl.refresh(s)                        # bumps the version: a second tap on this button is stale
            return "sent"

        @fl.action("own")
        def a_own(fl, s, args, cq):
            fl.open(s, "compose", new_message=True, conn=s.args["conn"], chat=s.args["chat"])

        @fl.action("panel")
        def a_panel(fl, s, args, cq):
            fl.open(s, "panel", new_message=True, conn=s.args["conn"], chat=s.args["chat"])

        @fl.action("auto")
        def a_auto(fl, s, args, cq):
            st = self.chats[(s.args["conn"], s.args["chat"])]
            st["auto"] = not st["auto"]
            fl.answer(cq, fl.tr(s, "toast_auto", state=fl.tr(s, "auto_on" if st["auto"] else "auto_off")))
            fl.refresh(s)

    def on_owner_message(self, msg: dict) -> str:
        uid, chat = msg["from"]["id"], msg["chat"]["id"]
        text = msg.get("text", "")
        lang = I18N.lang_for(msg["from"].get("language_code"))
        start = re.fullmatch(r"/start bizChat(\d+)", text)
        s = self.flow.sessions.get((chat, uid))
        if start:                                # "Manage Bot": the id is the customer chat
            conn = next((x for x in self.conns.values() if x["owner"] == uid and x["enabled"]), None)
            if not conn:
                self.t.call("sendMessage", {"chat_id": chat, "text": I18N.t(lang, "no_conn")})
                return "no_connection"
            if (conn["id"], int(start[1])) not in self.chats:
                self.t.call("sendMessage", {"chat_id": chat, "text": I18N.t(conn["lang"], "no_chat")})
                return "no_chat"
            self.flow.open(self.owner_session(conn), "panel", new_message=True, conn=conn["id"], chat=int(start[1]))
            return "panel"
        reply_to = (msg.get("reply_to_message") or {}).get("message_id")
        if not (s and s.screen == "compose" and reply_to == s.message_id):
            return "ignored"
        cid, cust = s.args["conn"], s.args["chat"]
        why = self.can_send(cid, cust)
        if why:
            self.t.call("sendMessage", {"chat_id": chat, "text": I18N.t(s.lang, f"toast_{why}")})
            return f"refused_{why}"
        if not 1 <= len(text) <= 4096:           # error on the same step: the prompt stays open
            self.t.call("sendMessage", {"chat_id": chat, "text": I18N.t(s.lang, "own_bad"),
                                        "reply_parameters": {"message_id": s.message_id}})
            return "invalid_text"
        self.sent.run(f"own:{cid}:{cust}:{msg['message_id']}", lambda: self.send(cid, cust, f.escape_html(text)))
        self.flow.open(s, "panel", new_message=True, conn=cid, chat=cust)
        return "sent_own"

    def dispatch(self, update: dict) -> str:
        if not self.updates.first_time(update):
            return "duplicate_update"
        if "business_connection" in update:
            return self.on_connection(update["business_connection"])
        if "business_message" in update:
            return self.on_business_message(update["business_message"])
        if "callback_query" in update:
            return self.flow.handle(update["callback_query"])
        return self.on_owner_message(update["message"])


def run(t: FakeTransport | None = None):
    t = t or FakeTransport()
    msg = c.fixture("usecase_business_message.json")["business_message"]
    bot = BizBot(t, now=msg["date"] + 60)
    n = [100]

    def upd(**kw) -> dict:
        n[0] += 1
        return {"update_id": 962000 + n[0], **kw}

    def tap(who: dict, action: str, *args, offset: int = 0, owner: dict = OKSANA) -> str:
        s = bot.flow.sessions[(owner["id"], owner["id"])]
        data = f.pack("bz", f.b36(s.version - offset), action, *args)
        cq = f.callback(f"cq{n[0] + 1}", who, data, chat_id=owner["id"], message_id=s.message_id)
        return bot.dispatch(upd(callback_query=cq))

    def owner_says(text: str, **kw) -> str:
        return bot.dispatch(upd(message=f.text_message(OKSANA, text, **kw)))

    out = [bot.dispatch(c.fixture("usecase_business_connection.json")),             # 0 rights: can_reply only
           bot.dispatch(c.fixture("usecase_business_connection_readonly.json")),    # 1 rights: read only
           bot.dispatch(c.fixture("usecase_business_message.json")),                # 2 auto-reply + proposal
           bot.dispatch(upd(business_message={**msg, "business_connection_id": "bizconn_bob", "message_id": 5,
                                              "chat": {"id": 333333333, "type": "private"}, "from": MARIA,
                                              "text": "Do you have vegan buns?"})),  # 3 read-only
           bot.dispatch(upd(business_message={**msg, "business_connection_id": "bizconn_gone"}))]   # 4 unknown
    out.append(tap(OKSANA, "qr", "hours"))                                           # 5 sent on behalf
    out.append(tap(OKSANA, "qr", "hours", offset=1))                                 # 6 double tap: stale
    out.append(owner_says("/start bizChat222222222"))                                # 7 Manage Bot -> panel
    out.append(tap(OKSANA, "qr", "hours"))                                           # 8 same reply, same message
    out.append(tap(IVAN, "qr", "special"))                                           # 9 a stranger
    out.append(tap(OKSANA, "own"))                                                   # 10 force_reply prompt
    prompt = bot.flow.sessions[(OKSANA["id"], OKSANA["id"])].message_id
    out.append(owner_says("x" * 5000, reply_to=prompt, message_id=9))                # 11 invalid, same step
    out.append(owner_says("Ваш торт готовий <o_O>", reply_to=prompt, message_id=10)) # 12 sent
    out.append(owner_says("/start bizChat999"))                                      # 13 unknown chat
    out.append(owner_says("/start bizChat222222222", message_id=11))                 # 14 fresh panel
    bot.now += WINDOW                                                                # the window closes
    out.append(tap(OKSANA, "qr", "special"))                                         # 15 refused, re-checked
    out.append(bot.dispatch(c.fixture("usecase_business_connection_disabled.json"))) # 16 turned off
    out.append(bot.dispatch(upd(business_message={**msg, "message_id": 78})))        # 17 ignored
    out.append(bot.dispatch(c.fixture("usecase_business_connection_disabled.json"))) # 18 duplicate delivery
    return t, bot, out


def main() -> None:
    t, bot, out = run()
    c.dump(t, "Business account")
    behalf = [p for p in t.params_of("sendMessage") if "business_connection_id" in p]
    c.check(out[:2] == ["connected", "connected"] and "не можу" in t.params_of("sendMessage")[0]["text"]
            and "read-only" in t.params_of("sendMessage")[1]["text"],
            "owners are told what the bot can and can't do (uk and en, read-only without can_reply)")
    c.check(out[2:5] == ["replied", "read_only", "ignored_unknown"] and behalf[0]["chat_id"] == 222222222
            and "8:00" in behalf[0]["text"],
            "auto-reply only with can_reply; read-only and unknown connections stay silent")
    c.check(all("keyboard" not in p.get("reply_markup", {}) and
                all("url" in b for b in f.callback_buttons(p.get("reply_markup"))) for p in behalf),
            "on-behalf messages carry only inline url buttons, never a reply keyboard")
    reads = t.params_of("readBusinessMessage")
    c.check(len(reads) == 1 and reads[0]["business_connection_id"] == "bizconn_bob",
            "readBusinessMessage only for the connection with can_read_messages")
    c.check(any(e["why"] == "unknown" for e in bot.log if e.get("event") == "business_message_ignored"),
            "a message for an unknown connection is logged and ignored")
    qr = [p["text"] for p in behalf if p["text"].startswith("Сьогодні працюємо")]
    c.check(out[5:10] == ["sent", "stale", "panel", "already_sent", "not_yours"] and len(qr) == 1,
            "quick reply sent once: stale double tap, same reply again refused, stranger refused")
    prompt = t.params_of("sendMessage")
    c.check(any(p.get("reply_markup", {}).get("force_reply") is True for p in prompt)
            and out[11:13] == ["invalid_text", "sent_own"]
            and sum("&lt;o_O&gt;" in p["text"] for p in behalf) == 1,
            "Write my own: force_reply prompt, invalid text rejected on the same step, valid text sent escaped")
    c.check(out[13:16] == ["no_chat", "panel", "refused_window"], "unknown chat id explained; closed window refused at tap time")
    c.check(out[16:] == ["disabled", "ignored_disabled", "duplicate_update"]
            and not [p for p in behalf if p["text"].startswith("Вітаю")][1:]
            and sum("Підключення вимкнено" in p.get("text", "") for p in t.params_of("sendMessage")) == 1,
            "disabled connection: owner told once, later customer messages ignored")


if __name__ == "__main__":
    if "--write-payload" in sys.argv:
        print(f.write_payload(f.payload_doc(PAYLOAD, run()[0], status=STATUS, context=CONTEXT)))
    else:
        main()
