"""R29 - Community bot: join requests with rules, welcome, roles as visible tags.

Flow (offline, against fixtures):
  chat_join_request -> DM the applicant through user_chat_id within 5 minutes with the
  rules as a checklist and "I accept" / "Decline" -> approveChatJoinRequest /
  declineChatJoinRequest; no answer in 5 minutes -> the Scheduler declines.
  Welcome: only if the bot has can_send_welcome_messages (10.3; read with getChatMember
  or my_chat_member), otherwise skipped and logged. community_chat_joined (10.3) gets a
  welcome that names the community. Admins assign a visible role with setChatMemberTag
  (0-16 characters, no emoji, needs can_manage_tags) from a picker.

Invariants shown: accept twice -> one approval; accept after expiry is refused politely;
a non-admin cannot use the picker; a tag is validated locally before the API call.

Run:  py -3 examples/python/recipes/r29_community.py [--write-payload]
"""
from __future__ import annotations

import html
import re
import sys

import _common as c
from tgkit import flows as f
from tgkit.errors import TelegramError
from tgkit.transport import FakeTransport

PAYLOAD = "r29-community"
STATUS = "production"
CONTEXT = "supergroup"
CHAT = -1001234567890
BOT_ID = 999000111
GROUP_LANG = "uk"                       # tags are visible to everyone: one language per chat
RULES_TTL = 300                         # user_chat_id works for 5 minutes (API)
ALICE = f.user(111111111, "Alice", "en")
BOGDAN = f.user(222222222, "Богдан", "uk")
OLENA = f.user(333333333, "Олена", "uk")
DANA = f.user(444444444, "Dana", "en")
MARK = f.user(666666666, "Mark", "en")
ADMINS = {OLENA["id"]}
ROLES = {"mentor": {"en": "Mentor", "uk": "Ментор"}, "guide": {"en": "Guide", "uk": "Гід"},
         "translator": {"en": "Translator", "uk": "Перекладач"}, "clear": {"en": "", "uk": ""}}
# Approximation of "emoji are not allowed": pictographs, symbols, joiners, keycaps, flags.
EMOJI = re.compile("[\U0001F000-\U0001FAFF←-⇿⌀-⏿☀-➿⬀-⯿"
                   "‍️⃣©®™‼⁉]")

COPY = {
    "en": {
        "rules_title": "Rules of {chat}", "rules_intro": "Please read the rules and accept them to join.",
        "rule1": "Be kind and stay on topic.", "rule2": "No ads, no spam.", "rule3": "Share only what you may share.",
        "rules_note": "You have 5 minutes to answer.",
        "accepted": "Done. Your request is approved. Welcome!",
        "declined": "Request declined. You can apply again any time.",
        "expired": "Time ran out, so the request was declined. Apply again when you're ready.",
        "already": "You already accepted: your request is approved.",
        "welcome": "Welcome, {name}! The rules are pinned. Say hi.",
        "welcome_community": "Welcome, {name}! Glad to have you from {community}.",
        "role_pick": "Pick a role for {name}.", "role_done": "{name} is now: {role}.",
        "role_cleared": "{name} has no role now.",
        "role_no_right": "I need the “Manage tags” right to set roles.",
        "role_denied": "Only administrators can assign roles.", "role_again": "This role is already set.",
        "role_bad": "That tag can't be used: {why}",
        "why_long": "more than 16 characters", "why_emoji": "emoji are not allowed",
        "btn_accept": "I accept", "btn_decline": "Decline",
        "btn_mentor": "Mentor", "btn_guide": "Guide", "btn_translator": "Translator", "btn_clear": "Clear role",
        "btn_state_accepted": "✓ Accepted", "btn_state_declined": "Declined", "btn_state_expired": "Expired",
        "sys_stale": "This screen has changed. Use the latest message.",
        "sys_not_yours": "Only administrators can use this.",
        "sys_expired": "This request is no longer open. Apply again via the invite link.",
    },
    "uk": {
        "rules_title": "Правила: {chat}", "rules_intro": "Прочитайте правила та прийміть їх, щоб приєднатися.",
        "rule1": "Будьте добрими й пишіть по темі.", "rule2": "Без реклами та спаму.",
        "rule3": "Діліться лише тим, чим можна ділитися.",
        "rules_note": "На відповідь у вас 5 хвилин.",
        "accepted": "Готово. Заявку схвалено. Ласкаво просимо!",
        "declined": "Заявку відхилено. Подати її знову можна будь-коли.",
        "expired": "Час вийшов, тож заявку відхилено. Подайте її знову, коли будете готові.",
        "already": "Ви вже погодились: заявку схвалено.",
        "welcome": "Вітаємо, {name}! Правила закріплено. Привітайтесь.",
        "welcome_community": "Вітаємо, {name}! Раді бачити вас зі спільноти {community}.",
        "role_pick": "Оберіть роль для {name}.", "role_done": "{name} тепер: {role}.",
        "role_cleared": "У {name} більше немає ролі.",
        "role_no_right": "Мені потрібне право «Керувати тегами», щоб призначати ролі.",
        "role_denied": "Призначати ролі можуть лише адміністратори.", "role_again": "Цю роль уже встановлено.",
        "role_bad": "Цей тег не підходить: {why}",
        "why_long": "понад 16 символів", "why_emoji": "емодзі заборонені",
        "btn_accept": "Приймаю", "btn_decline": "Відхилити",
        "btn_mentor": "Ментор", "btn_guide": "Гід", "btn_translator": "Перекладач", "btn_clear": "Зняти роль",
        "btn_state_accepted": "✓ Прийнято", "btn_state_declined": "Відхилено", "btn_state_expired": "Час вийшов",
        "sys_stale": "Екран змінився. Користуйтеся останнім повідомленням.",
        "sys_not_yours": "Це доступно лише адміністраторам.",
        "sys_expired": "Заявка вже не активна. Подайте її знову за посиланням.",
    },
}
I18N = f.I18n(COPY)
REQUEST = f.Machine({"pending": {"accept": "accepted", "decline": "declined", "expire": "expired"}}, "pending")


def plain(lang: str, key: str, **values) -> str:
    return html.unescape(I18N.t(lang, key, **values))


def validate_tag(tag: str) -> str | None:
    """setChatMemberTag: 0-16 characters, emoji not allowed. Returns a copy key or None."""
    if len(tag) > 16:
        return "why_long"
    return "why_emoji" if EMOJI.search(tag) else None


class Community:
    def __init__(self, t: FakeTransport):
        self.t = t
        self.now = 0.0
        self.reqs: dict[tuple[int, int], dict] = {}
        self.sched = f.Scheduler()
        self.once = f.OnceStore()                # one approve/decline per request, however many taps
        self.updates = f.UpdateDedup()
        self.pickers: dict[str, dict] = {}
        self.rights: dict[int, dict] = {}        # chat -> the bot's ChatMemberAdministrator
        self.log: list[dict] = []
        self._answered: set[str] = set()

    # ---- helpers ---------------------------------------------------------------
    def answer(self, cq: dict, text: str | None = None, *, alert: bool = False) -> None:
        if cq["id"] in self._answered:
            return
        self._answered.add(cq["id"])
        self.t.call("answerCallbackQuery", {"callback_query_id": cq["id"],
                                            **({"text": text[:200], **({"show_alert": True} if alert else {})} if text else {})})

    def bot_rights(self, chat: int) -> dict:
        if chat not in self.rights:              # first use: ask the server, then keep it fresh from my_chat_member
            self.rights[chat] = self.t.call("getChatMember", {"chat_id": chat, "user_id": BOT_ID})
        return self.rights[chat]

    def is_admin(self, chat: int, uid: int) -> bool:
        return self.t.call("getChatMember", {"chat_id": chat, "user_id": uid}).get("status") in ("administrator", "creator")

    def on_my_chat_member(self, upd: dict) -> str:
        new = upd["my_chat_member"]["new_chat_member"]
        self.rights[upd["my_chat_member"]["chat"]["id"]] = new
        return "rights_updated"

    # ---- join requests ----------------------------------------------------------------
    def on_join_request(self, jr: dict) -> str:
        chat, user = jr["chat"], jr["from"]
        deadline = jr["date"] + RULES_TTL
        if self.now > deadline:                  # user_chat_id is no longer usable: leave it to the admins
            self.log.append({"event": "join_request_too_late", "user": user["id"]})
            return "too_late"
        lang = I18N.lang_for(user.get("language_code"))
        key = (chat["id"], user["id"])
        self.reqs[key] = {"state": REQUEST.initial, "lang": lang, "name": user["first_name"], "title": chat["title"],
                          "deadline": deadline, "dm_chat": jr["user_chat_id"]}
        items = [{"blocks": [{"type": "paragraph", "text": plain(lang, k)}], "has_checkbox": True}
                 for k in ("rule1", "rule2", "rule3")]
        ref = f.b36(abs(chat["id"]))
        sent = self.t.call("sendRichMessage", {
            "chat_id": jr["user_chat_id"],
            "rich_message": {"blocks": [{"type": "heading", "size": 2, "text": plain(lang, "rules_title", chat=chat["title"])},
                                        {"type": "paragraph", "text": plain(lang, "rules_intro")},
                                        {"type": "list", "items": items},
                                        {"type": "paragraph", "text": plain(lang, "rules_note")}]},
            "reply_markup": f.kb([f.btn(plain(lang, "btn_accept"), f.pack("cm", "ok", ref), style="success"),
                                  f.btn(plain(lang, "btn_decline"), f.pack("cm", "no", ref))])})
        self.reqs[key]["dm"] = sent["message_id"]
        self.sched.at(deadline, f"exp:{chat['id']}:{user['id']}", chat=chat["id"], user=user["id"])
        return "rules_sent"

    def settle(self, key: tuple[int, int], event: str) -> str:
        """pending -> accepted/declined/expired, with exactly one Telegram call per request."""
        req = self.reqs[key]
        req["state"] = REQUEST.next(req["state"], event)
        method = "approveChatJoinRequest" if event == "accept" else "declineChatJoinRequest"
        self.once.run(f"{method}:{key}", lambda: self.t.call(method, {"chat_id": key[0], "user_id": key[1]}))
        label = f.btn(plain(req["lang"], "btn_state_" + req["state"]), disabled=True)
        text = plain(req["lang"], {"accepted": "accepted", "declined": "declined", "expired": "expired"}[req["state"]])
        try:                                     # after expiry the DM edit is best effort
            self.t.call("editMessageText", {"chat_id": req["dm_chat"], "message_id": req["dm"],
                                            "rich_message": {"blocks": [{"type": "paragraph", "text": text}]},
                                            "reply_markup": f.kb([label])})
        except TelegramError as err:
            self.log.append({"event": "dm_edit_failed", "class": err.category})
        return req["state"]

    def tick(self, now: float) -> list[str]:
        self.now = now
        out = []
        for job in self.sched.due(now):
            key = (job.payload["chat"], job.payload["user"])
            if self.reqs[key]["state"] == "pending":
                out.append(self.settle(key, "expire"))
        return out

    def welcome(self, chat: int, user: dict, lang: str, community: str | None = None) -> str:
        r = self.bot_rights(chat)
        if r.get("status") != "administrator" or r.get("can_send_welcome_messages") is not True:
            self.log.append({"event": "welcome_skipped", "why": "no can_send_welcome_messages", "user": user["id"]})
            return "skipped"
        key, values = ("welcome_community", {"community": community}) if community else ("welcome", {})
        # An administrator bot may send an ephemeral message to a member at any time: only they see it.
        self.t.call("sendMessage", {"chat_id": chat, "text": I18N.t(lang, key, name=user["first_name"], **values),
                                    "parse_mode": "HTML", "ephemeral_message_parameters": {"receiver_user_id": user["id"]}})
        return "welcomed"

    # ---- roles --------------------------------------------------------------------------
    def set_tag(self, chat: int, uid: int, tag: str) -> str | None:
        why = validate_tag(tag)
        if why:
            return why                           # never send a tag the API will reject
        self.t.call("setChatMemberTag", {"chat_id": chat, "user_id": uid, "tag": tag})
        return None

    def on_role_command(self, msg: dict) -> str:
        chat, admin = msg["chat"]["id"], msg["from"]
        target = (msg.get("reply_to_message") or {}).get("from")
        lang = I18N.lang_for(admin.get("language_code"))
        if not self.is_admin(chat, admin["id"]) or not target:
            self.log.append({"event": "role_command_ignored", "user": admin["id"]})
            return "ignored"
        if self.bot_rights(chat).get("can_manage_tags") is not True:
            self.t.call("sendMessage", {"chat_id": chat, "text": I18N.t(lang, "role_no_right"), "parse_mode": "HTML"})
            return "no_right"
        pid = f.b36(len(self.pickers) + 1)
        self.pickers[pid] = {"target": target["id"], "name": target["first_name"], "done": False}
        row = [f.btn(plain(lang, f"btn_{k}"), f.pack("cm", "role", pid, k)) for k in ("mentor", "guide", "translator")]
        sent = self.t.call("sendMessage", {
            "chat_id": chat, "text": I18N.t(lang, "role_pick", name=target["first_name"]), "parse_mode": "HTML",
            "reply_markup": f.kb(row, [f.btn(plain(lang, "btn_clear"), f.pack("cm", "role", pid, "clear"))])})
        self.pickers[pid]["message_id"] = sent["message_id"]
        return "picker"

    # ---- callbacks and dispatch ----------------------------------------------------------
    def on_callback(self, cq: dict) -> str:
        parts = f.unpack(cq["data"])
        if parts[0] != "cm":
            return "foreign"
        user, chat_here = cq["from"], cq["message"]["chat"]["id"]
        lang = I18N.lang_for(user.get("language_code"))
        if parts[1] == "role":
            return self.on_role_tap(cq, lang, parts[2], parts[3])
        key = (-int(parts[2], 36), user["id"])
        req = self.reqs.get(key)
        if req is None:
            self.answer(cq, plain(lang, "sys_expired"))
            return "expired"
        if req["state"] == "accepted" and parts[1] == "ok":
            self.answer(cq, plain(req["lang"], "already"))
            return "already_accepted"
        if req["state"] == "pending" and self.now > req["deadline"]:
            self.settle(key, "expire")           # the job has not run yet, but the time is up
        if req["state"] != "pending":
            self.answer(cq, plain(req["lang"], "sys_expired"), alert=True)
            return "refused_closed"
        outcome = self.settle(key, "accept" if parts[1] == "ok" else "decline")
        self.answer(cq)
        if outcome == "accepted":
            self.welcome(key[0], user, req["lang"])
        return outcome

    def on_role_tap(self, cq: dict, lang: str, pid: str, role: str) -> str:
        chat = cq["message"]["chat"]["id"]
        picker = self.pickers.get(pid)
        if picker is None:
            self.answer(cq, plain(lang, "sys_expired"))
            return "expired"
        if not self.is_admin(chat, cq["from"]["id"]):
            self.answer(cq, plain(lang, "role_denied"), alert=True)
            return "not_admin"
        if picker["done"]:
            self.answer(cq, plain(lang, "role_again"))
            return "already_set"
        why = self.set_tag(chat, picker["target"], ROLES[role][GROUP_LANG])
        if why:
            self.answer(cq, plain(lang, "role_bad", why=plain(lang, why)), alert=True)
            return "invalid_tag"
        picker["done"] = True
        text = (I18N.t(lang, "role_done", name=picker["name"], role=ROLES[role][GROUP_LANG]) if role != "clear"
                else I18N.t(lang, "role_cleared", name=picker["name"]))
        self.t.call("editMessageText", {"chat_id": chat, "message_id": picker["message_id"], "text": text,
                                        "parse_mode": "HTML",
                                        "reply_markup": f.kb([f.btn("✓ " + (ROLES[role][lang] or plain(lang, "btn_clear")),
                                                                    disabled=True)])})
        self.answer(cq)
        return "tag_set"

    def dispatch(self, update: dict) -> str:
        if not self.updates.first_time(update):
            return "duplicate_update"
        if "chat_join_request" in update:
            return self.on_join_request(update["chat_join_request"])
        if "my_chat_member" in update:
            return self.on_my_chat_member(update)
        if "callback_query" in update:
            return self.on_callback(update["callback_query"])
        msg = update["message"]
        if "community_chat_joined" in msg:
            return self.welcome(msg["chat"]["id"], msg["from"], I18N.lang_for(msg["from"].get("language_code")),
                                msg["community_chat_joined"]["community"]["name"])
        if msg.get("text", "").startswith("/role"):
            return self.on_role_command(msg)
        return "ignored"


def run(t: FakeTransport | None = None):
    t = t or FakeTransport()
    bot = {"rights": c.fixture("usecase_community_bot_rights.json")["my_chat_member"]["new_chat_member"]}

    def get_chat_member(method: str, params: dict) -> dict:
        uid = params["user_id"]
        if uid == BOT_ID:
            return bot["rights"]
        return {"status": "administrator" if uid in ADMINS else "member", "user": {"id": uid, "is_bot": False, "first_name": "x"}}

    t.script("getChatMember", *[get_chat_member] * 40)
    app = Community(t)
    n = [0]
    log: dict[str, object] = {}
    base = c.fixture("usecase_chat_join_request.json")
    date = base["chat_join_request"]["date"]

    def request(who: dict, at: int) -> dict:
        upd = {**base, "update_id": base["update_id"] + n[0] + 1}
        upd["chat_join_request"] = {**base["chat_join_request"], "from": who, "user_chat_id": who["id"], "date": at}
        return upd

    def tap(who: dict, data: str, chat_id: int | None = None, message_id: int = 0) -> str:
        n[0] += 1
        cq = f.callback(f"cq{n[0]}", who, data, chat_id=chat_id or who["id"], message_id=message_id,
                        chat_type="private" if chat_id is None else "supergroup")
        return app.dispatch({"update_id": 6000 + n[0], "callback_query": cq})

    ref = f.b36(abs(CHAT))
    # Bogdan accepts (twice); the welcome needs the right, read through getChatMember on first use.
    app.now = date + 5
    log["join"] = [app.dispatch(base)]
    log["accept"] = [tap(BOGDAN, f"cm:ok:{ref}"), tap(BOGDAN, f"cm:ok:{ref}")]
    # Alice does not answer in time; accepting afterwards is refused.
    app.now = date + 1000
    log["join"].append(app.dispatch(request(ALICE, date + 1000)))
    log["expire"] = app.tick(date + 1000 + RULES_TTL + 1)
    log["accept"].append(tap(ALICE, f"cm:ok:{ref}"))
    # Mark declines; Dana's request is processed after the 5 minutes: nothing is sent.
    app.now = date + 2005
    log["join"].append(app.dispatch(request(MARK, date + 2000)))
    log["decline"] = tap(MARK, f"cm:no:{ref}")
    app.now = date + 3000
    log["join"].append(app.dispatch(request(DANA, date + 2000)))
    # Roles: a member (Bogdan) is picked by an administrator (Olena); a non-admin tap is refused.
    reply = f.text_message(OLENA, "/role", chat_id=CHAT, message_id=710, chat_type="supergroup", reply_to=700)
    reply["reply_to_message"]["from"] = BOGDAN
    log["role"] = [app.dispatch({"update_id": 6500, "message": reply})]
    picker = app.pickers["1"]
    log["role"].append(tap(BOGDAN, f"cm:role:1:mentor", CHAT, picker["message_id"]))
    log["role"].append(tap(OLENA, f"cm:role:1:mentor", CHAT, picker["message_id"]))
    log["role"].append(tap(OLENA, f"cm:role:1:guide", CHAT, picker["message_id"]))
    log["tags"] = [app.set_tag(CHAT, BOGDAN["id"], "Mentor ⭐"), app.set_tag(CHAT, BOGDAN["id"], "x" * 17),
                   app.set_tag(CHAT, BOGDAN["id"], "Ментор")]
    # A member arrives through a community; then the bot loses can_send_welcome_messages.
    log["community"] = app.dispatch(c.fixture("message_community_chat_joined.json"))
    lost = c.fixture("usecase_community_bot_rights.json")
    lost["update_id"] += 1
    lost["my_chat_member"]["new_chat_member"]["can_send_welcome_messages"] = False
    app.dispatch(lost)
    app.now = date + 4000
    app.dispatch(request(DANA, date + 3900))
    log["accept"].append(tap(DANA, f"cm:ok:{ref}"))
    # Without can_manage_tags the picker is not offered (the older fixture has no such right).
    app.dispatch(c.fixture("chat_member_admin_welcome.json"))
    log["role"].append(app.dispatch({"update_id": 6501, "message": reply}))
    return t, app, log


def main() -> None:
    t, app, log = run()
    c.dump(t, "Community bot")
    dm = t.params_of("sendRichMessage")[0]
    c.check(dm["chat_id"] == BOGDAN["id"] and any(b["type"] == "list" and b["items"][0].get("has_checkbox")
                                                  for b in dm["rich_message"]["blocks"]),
            "applicant gets the rules as a checklist in a DM through user_chat_id")
    c.check(log["accept"][:2] == ["accepted", "already_accepted"] and len(t.params_of("approveChatJoinRequest")) == 2,
            "accept twice -> one approval (Bogdan) and one more for Dana")
    c.check(log["expire"] == ["expired"] and log["accept"][2] == "refused_closed"
            and {"chat_id": CHAT, "user_id": ALICE["id"]} in t.params_of("declineChatJoinRequest"),
            "no answer in 5 minutes -> declined by the Scheduler; a late accept is refused")
    c.check(log["decline"] == "declined" and len(t.params_of("declineChatJoinRequest")) == 2, "decline -> one declineChatJoinRequest")
    c.check(log["join"][3] == "too_late" and any(e["event"] == "join_request_too_late" for e in app.log),
            "a request seen after 5 minutes is not DMed (user_chat_id expired)")
    welcomes = [p for p in t.params_of("sendMessage") if "ephemeral_message_parameters" in p]
    c.check(len(welcomes) == 2 and "Вітаємо, Богдан!" in welcomes[0]["text"] and "Foodies of Kyiv" in welcomes[1]["text"],
            "welcome after approval, and a community welcome naming the community")
    c.check(any(e["event"] == "welcome_skipped" for e in app.log) and log["accept"][3] == "accepted",
            "without can_send_welcome_messages the approval still works, the welcome is skipped and logged")
    c.check(log["role"][:4] == ["picker", "not_admin", "tag_set", "already_set"]
            and t.params_of("setChatMemberTag")[0] == {"chat_id": CHAT, "user_id": BOGDAN["id"], "tag": "Ментор"},
            "role picker: a non-admin is refused, the admin sets a tag once")
    c.check(log["tags"] == ["why_emoji", "why_long", None], "tag validated locally: emoji and 17 characters never reach the API")
    c.check(log["role"][4] == "no_right", "no can_manage_tags -> the picker is replaced by an explanation")


if __name__ == "__main__":
    if "--write-payload" in sys.argv:
        print(f.write_payload(f.payload_doc(PAYLOAD, run()[0], status=STATUS, context=CONTEXT)))
    else:
        main()
