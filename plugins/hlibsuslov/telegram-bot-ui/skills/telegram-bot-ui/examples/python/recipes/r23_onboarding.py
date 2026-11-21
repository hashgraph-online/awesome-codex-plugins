"""R23 - Onboarding and first run: /start with deep-link payloads, language
choice, an optional permission step, empty states and returning users.

Shown offline:
* deploy-time setup: per-language commands (setMyCommands + language_code), the
  empty-chat description (setMyDescription) and the share/profile text
  (setMyShortDescription) - what a user sees BEFORE pressing Start;
* /start payload parsing: plain, ref_<code>, item_<key>, an invalid payload
  (ignored safely, never echoed), a referral credited once, self-referral refused;
* first run = 3 short steps (language, notifications opt-in, optional phone via a
  one-time reply keyboard with request_contact); "Not now" always available;
* a contact that is not the sender's own is refused;
* returning users skip onboarding ("Welcome back") and land where they left off;
* a tap on an onboarding button after onboarding finished is stale.

Run:  py -3 examples/python/recipes/r23_onboarding.py [--write-payload]
"""
from __future__ import annotations

import re
import sys

import _common as c
from tgkit import flows as f
from tgkit.transport import FakeTransport

PAYLOAD = "r23-onboarding"
STATUS = "production"
CONTEXT = "private"
BOT = "coffee_demo_bot"
ALICE = f.user(111111111, "Alice", "en")
BOGDAN = f.user(222222222, "Богдан", "uk")
START_PARAM = re.compile(r"^[A-Za-z0-9_-]{1,64}$")   # API: deep-link parameter alphabet and length

COPY = {
    "en": {
        "lang_pick": "<b>Hi, {name}!</b> Which language should I use?",
        "notify": "<b>Step 2 of 3 · Updates</b>\nI can tell you when your order ships. Nothing else, no ads.",
        "phone": "<b>Step 3 of 3 · Phone (optional)</b>\nThe courier calls this number. You can skip it.",
        "phone_kb_hint": "Tap “Share my phone” or “Skip”",
        "phone_thanks": "Saved. The courier will call {phone}.",
        "phone_not_yours": "That's someone else's contact. Share your own number or tap “Skip”.",
        "home_empty": "<b>All set, {name}</b>\nYou have no orders yet. Start with the catalog — fresh roast every Monday.",
        "home": "<b>Welcome back, {name}</b>\nOrder {order} is on its way.",
        "item_teaser": "<b>{title}</b> from your link is waiting in the cart.",
        "ref_ok": "{name} invited you: your first delivery is free.",
        "remove_kb": "Okay, no phone.",
        "desc": "Fresh coffee beans, roasted on Mondays. Order in two taps, pay with Stars or card.",
        "short_desc": "Coffee beans, roasted weekly. Order in two taps.",
        "cmd_start": "Open the shop",
        "cmd_orders": "My orders",
        "cmd_settings": "Language and notifications",
        "btn_notify_on": "Notify me",
        "btn_not_now": "Not now",
        "btn_share_phone": "Share my phone",
        "btn_skip": "Skip",
        "btn_catalog": "Open the catalog",
        "btn_orders": "My orders",
        "btn_settings": "Settings",
        "sys_stale": "This step is already done.",
        "sys_not_yours": "This menu belongs to someone else.",
        "sys_expired": "This menu has expired. Send /start.",
    },
    "uk": {
        "lang_pick": "<b>Привіт, {name}!</b> Якою мовою спілкуватися?",
        "notify": "<b>Крок 2 з 3 · Сповіщення</b>\nПовідомлю, коли замовлення відправлено. Нічого більше, без реклами.",
        "phone": "<b>Крок 3 з 3 · Телефон (необовʼязково)</b>\nНа цей номер зателефонує курʼєр. Можна пропустити.",
        "phone_kb_hint": "Натисніть «Поділитися номером» або «Пропустити»",
        "phone_thanks": "Збережено. Курʼєр зателефонує на {phone}.",
        "phone_not_yours": "Це чужий контакт. Поділіться своїм номером або натисніть «Пропустити».",
        "home_empty": "<b>Готово, {name}</b>\nЗамовлень ще немає. Почніть з каталогу — свіже обсмаження щопонеділка.",
        "home": "<b>З поверненням, {name}</b>\nЗамовлення {order} вже в дорозі.",
        "item_teaser": "<b>{title}</b> за вашим посиланням уже чекає в кошику.",
        "ref_ok": "{name} запросив(-ла) вас: перша доставка безкоштовна.",
        "remove_kb": "Гаразд, без телефону.",
        "desc": "Свіжа кава в зернах, обсмажуємо щопонеділка. Замовлення у два дотики, оплата зірками або карткою.",
        "short_desc": "Кава в зернах, свіже обсмаження щотижня.",
        "cmd_start": "Відкрити магазин",
        "cmd_orders": "Мої замовлення",
        "cmd_settings": "Мова і сповіщення",
        "btn_notify_on": "Сповіщати",
        "btn_not_now": "Не зараз",
        "btn_share_phone": "Поділитися номером",
        "btn_skip": "Пропустити",
        "btn_catalog": "Відкрити каталог",
        "btn_orders": "Мої замовлення",
        "btn_settings": "Налаштування",
        "sys_stale": "Цей крок уже пройдено.",
        "sys_not_yours": "Це меню іншої людини.",
        "sys_expired": "Меню застаріло. Надішліть /start.",
    },
}
I18N = f.I18n(COPY)
LANG_NAMES = {"en": "English", "uk": "Українська"}      # each language in its own name
ITEMS = {"eth": {"en": "Ethiopia Yirgacheffe", "uk": "Ефіопія Іргачеффе"}}
REF_CODES = {"alice7": ALICE["id"]}                     # referral code -> inviter
NAMES = {ALICE["id"]: "Alice"}                          # display names from your user store


def deploy_setup(t: FakeTransport) -> None:
    """Run once per deploy/language, not per user. Commands are 1-32 chars of
    a-z0-9_, descriptions 1-256; description 0-512; short description 0-120 [API]."""
    for lang in COPY:
        code = {} if lang == I18N.default else {"language_code": lang}
        t.call("setMyCommands", {"commands": [
            {"command": "start", "description": I18N.t(lang, "cmd_start")},
            {"command": "orders", "description": I18N.t(lang, "cmd_orders")},
            {"command": "settings", "description": I18N.t(lang, "cmd_settings")}], **code})
        t.call("setMyDescription", {"description": I18N.t(lang, "desc"), **code})
        t.call("setMyShortDescription", {"short_description": I18N.t(lang, "short_desc"), **code})


class Onboarding:
    def __init__(self, t: FakeTransport):
        self.t = t
        self.flow = f.ScreenFlow(t, "ob", i18n=I18N)
        self.users: dict[int, dict] = {}         # profile: lang, onboarded, notify, phone, orders
        self.referrals = f.OnceStore()
        self.updates = f.UpdateDedup()
        self._screens()

    def _screens(self) -> None:
        fl = self.flow

        @fl.screen("lang")
        def lang(fl, s):
            detected = s.lang
            rows = [[f.btn(("✓ " if code == detected else "") + name, fl.cb(s, "lang", code),
                           style="primary" if code == detected else None)]
                    for code, name in LANG_NAMES.items()]
            return {"text": fl.tr(s, "lang_pick", name=s.data["name"]), "reply_markup": f.kb(*rows)}

        @fl.screen("notify")
        def notify(fl, s):
            return {"text": fl.tr(s, "notify"), "reply_markup": f.kb(
                [f.btn(fl.tr(s, "btn_notify_on"), fl.cb(s, "notify", 1), style="primary"),
                 f.btn(fl.tr(s, "btn_not_now"), fl.cb(s, "notify", 0))])}

        @fl.screen("home")
        def home(fl, s):
            prof = self.users[s.owner_id]
            if prof["orders"]:
                text = fl.tr(s, "home", name=s.data["name"], order=prof["orders"][-1])
            else:                                # empty state: one clear next step
                text = fl.tr(s, "home_empty", name=s.data["name"])
            if s.data.get("teaser"):
                text += "\n\n" + fl.tr(s, "item_teaser", title=ITEMS[s.data["teaser"]][s.lang])
            if s.data.get("ref_by"):
                text += "\n\n" + fl.tr(s, "ref_ok", name=s.data["ref_by"])
            return {"text": text, "reply_markup": f.kb(
                [f.btn(fl.tr(s, "btn_catalog"), fl.cb(s, "noop", "catalog"), style="primary")],
                [f.btn(fl.tr(s, "btn_orders"), fl.cb(s, "noop", "orders")),
                 f.btn(fl.tr(s, "btn_settings"), fl.cb(s, "noop", "settings"))])}

        @fl.action("lang")
        def a_lang(fl, s, args, cq):
            if args[0] not in COPY:
                return "bad_lang"
            s.lang = self.users[s.owner_id]["lang"] = args[0]
            fl.go(s, "notify")
            return "lang_set"

        @fl.action("notify")
        def a_notify(fl, s, args, cq):
            self.users[s.owner_id]["notify"] = args[0] == "1"
            self.ask_phone(s)
            return "notify_" + ("on" if args[0] == "1" else "off")

        @fl.action("noop")
        def a_noop(fl, s, args, cq):
            return "home_" + args[0]

    def ask_phone(self, s: f.Session) -> None:
        """Reply keyboard: the only way to ask for a contact. one_time_keyboard hides
        it after use; input_field_placeholder 1-64 chars [API]. A separate message
        because an inline menu can't carry a reply keyboard."""
        self.flow.owners.pop((s.chat_id, s.message_id), None)   # step 2's buttons retire
        s.data["step"] = "phone"
        self.t.call("sendMessage", {"chat_id": s.chat_id, "parse_mode": "HTML", "text": self.flow.tr(s, "phone"),
                                    "reply_markup": {"keyboard": [[
                                        {"text": self.flow.tr(s, "btn_share_phone"), "request_contact": True}],
                                        [{"text": self.flow.tr(s, "btn_skip")}]],
                                        "one_time_keyboard": True, "resize_keyboard": True,
                                        "input_field_placeholder": self.flow.tr(s, "phone_kb_hint")[:64]}})

    def finish(self, s: f.Session, note: str) -> None:
        self.users[s.owner_id]["onboarded"] = True
        s.data.pop("step", None)
        self.t.call("sendMessage", {"chat_id": s.chat_id, "text": note, "reply_markup": {"remove_keyboard": True}})
        s.message_id = None                       # the home menu is a new message under the note
        self.flow.open(s, "home")
        s.data.pop("teaser", None)                # one-time notes: shown once, then gone
        s.data.pop("ref_by", None)

    # ---- /start -------------------------------------------------------------
    def on_start(self, msg: dict) -> str:
        frm = msg["from"]
        parts = msg["text"].split(maxsplit=1)
        param = parts[1] if len(parts) > 1 else ""
        malformed = bool(param) and not START_PARAM.match(param)
        if malformed:
            param = ""                            # never echo or trust a malformed payload
        prof = self.users.get(frm["id"])
        is_new = prof is None
        if is_new:
            prof = self.users[frm["id"]] = {"lang": I18N.lang_for(frm.get("language_code")),
                                            "onboarded": False, "notify": None, "phone": None, "orders": []}
        s = self.flow.session(frm["id"], frm["id"], lang=prof["lang"])
        s.data["name"] = frm.get("first_name", "")
        outcome = "start_new" if is_new else "start_returning"
        if param.startswith("item_") and param[5:] in ITEMS:
            s.data["teaser"] = param[5:]
            outcome += "+item"
        elif param.startswith("ref_"):
            outcome += "+" + self.credit_referral(frm["id"], param[4:], is_new, s)
        elif param:
            outcome += "+unknown_param"           # logged for analytics, not shown
        elif malformed:
            outcome += "+malformed_param"
        if prof["onboarded"]:
            self.flow.open(s, "home", new_message=True)
        else:
            self.flow.open(s, "lang", new_message=True)
        return outcome

    def credit_referral(self, uid: int, code: str, is_new: bool, s: f.Session) -> str:
        inviter = REF_CODES.get(code)
        if inviter is None:
            return "ref_unknown"
        if inviter == uid:
            return "ref_self"
        if not is_new:
            return "ref_existing_user"            # only new users count
        _, first = self.referrals.run(f"ref:{uid}", lambda: inviter)
        if first:
            s.data["ref_by"] = NAMES.get(inviter, "")
        return "ref_credited" if first else "ref_duplicate"

    def on_message(self, msg: dict) -> str:
        uid = msg["from"]["id"]
        s = self.flow.sessions.get((msg["chat"]["id"], uid))
        if (msg.get("text") or "").startswith("/start"):
            return self.on_start(msg)
        if not s or s.data.get("step") != "phone":
            return "ignored"
        if "contact" in msg:
            contact = msg["contact"]
            if contact.get("user_id") != uid:     # a forwarded/attached contact of someone else
                self.t.call("sendMessage", {"chat_id": s.chat_id, "text": self.flow.tr(s, "phone_not_yours")})
                return "contact_not_own"
            self.users[uid]["phone"] = contact["phone_number"]
            self.finish(s, I18N.t(s.lang, "phone_thanks", phone=contact["phone_number"]))
            return "phone_saved"
        if msg.get("text") == self.flow.tr(s, "btn_skip"):
            self.finish(s, I18N.t(s.lang, "remove_kb"))
            return "phone_skipped"
        return "ignored"

    def dispatch(self, update: dict) -> str:
        if not self.updates.first_time(update):
            return "duplicate_update"
        if "callback_query" in update:
            return self.flow.handle(update["callback_query"])
        return self.on_message(update["message"])


def contact_message(frm: dict, phone: str, name: str, contact_user_id: int) -> dict:
    """A message with a Contact (phone_number, first_name, user_id?) - no text."""
    return {"message_id": 1, "date": 0, "from": frm, "chat": {"id": frm["id"], "type": "private"},
            "contact": {"phone_number": phone, "first_name": name, "user_id": contact_user_id}}


def run(t: FakeTransport | None = None):
    t = t or FakeTransport()
    deploy_setup(t)
    ob = Onboarding(t)
    fl = ob.flow
    n = [0]

    def upd(**kw) -> dict:
        n[0] += 1
        return {"update_id": 5000 + n[0], **kw}

    def tap(who, action, *args, old=False):
        s = fl.sessions[(who["id"], who["id"])]
        data = f.pack("ob", f.b36(s.version - (1 if old else 0)), action, *args)
        return ob.dispatch(upd(callback_query=f.callback(f"q{n[0]}", who, data, chat_id=who["id"],
                                                         message_id=s.message_id)))

    out = []
    # Bogdan opens a referral link from Alice: new user, Ukrainian client.
    start = upd(message=f.text_message(BOGDAN, "/start ref_alice7"))
    out.append(ob.dispatch(start))
    out.append(ob.dispatch(start))                       # webhook retry of the same update
    out.append(tap(BOGDAN, "lang", "uk"))
    stale_lang = f.pack("ob", f.b36(fl.sessions[(BOGDAN["id"],) * 2].version - 1), "lang", "en")
    out.append(tap(BOGDAN, "notify", 1))
    out.append(ob.dispatch(upd(message=contact_message(BOGDAN, "+380441112233", "Мама", 999999999))))
    out.append(ob.dispatch(upd(message=contact_message(BOGDAN, "+380501234567", "Богдан", BOGDAN["id"]))))
    s = fl.sessions[(BOGDAN["id"],) * 2]
    out.append(ob.dispatch(upd(callback_query=f.callback("qs", BOGDAN, stale_lang, chat_id=BOGDAN["id"],
                                                         message_id=s.message_id))))   # old step's button
    # The same referral link opened again by an existing user: not credited twice.
    out.append(ob.dispatch(upd(message=f.text_message(BOGDAN, "/start ref_alice7"))))
    # Alice: deep link to a product, self-referral later, a malformed payload, then a returning visit.
    out.append(ob.dispatch(upd(message=f.text_message(ALICE, "/start item_eth"))))
    out.append(tap(ALICE, "lang", "en"))
    out.append(tap(ALICE, "notify", 0))
    out.append(ob.dispatch(upd(message=f.text_message(ALICE, "Skip"))))
    out.append(ob.dispatch(upd(message=f.text_message(ALICE, "/start ref_alice7"))))
    out.append(ob.dispatch(upd(message=f.text_message(ALICE, "/start <script>alert(1)</script>"))))
    ob.users[ALICE["id"]]["orders"].append("SH-1001")
    out.append(ob.dispatch(upd(message=f.text_message(ALICE, "/start"))))
    return t, ob, out


def main() -> None:
    t, ob, out = run()
    c.dump(t, "Onboarding")
    c.check(out[:3] == ["start_new+ref_credited", "duplicate_update", "lang_set"],
            "new user via a referral link; a redelivered /start does nothing")
    c.check(out[4:6] == ["contact_not_own", "phone_saved"], "someone else's contact is refused")
    c.check(out[6] == "stale", "a tap on a finished onboarding step is stale")
    c.check(out[7] == "start_returning+ref_existing_user", "a referral counts for new users only")
    c.check(out[8] == "start_new+item" and out[12] == "start_returning+ref_self", "item deep link; self-referral refused")
    c.check(out[13] == "start_returning+malformed_param", "a malformed payload is ignored, never echoed")
    c.check(not any("script" in (p.get("text") or "") for p in t.params_of("sendMessage")), "nothing echoed")
    c.check(len(t.params_of("setMyCommands")) == 2 and t.params_of("setMyCommands")[1]["language_code"] == "uk",
            "commands per language; the default list has no language_code")
    homes = [p["text"] for _, p in t.calls if "text" in p and ("Welcome back" in p["text"] or "All set" in p["text"])]
    c.check("All set" in homes[0] and "Welcome back" in homes[-1], "empty state first, returning user later")
    kb = next(p["reply_markup"] for p in t.params_of("sendMessage") if "keyboard" in p.get("reply_markup", {}))
    c.check(kb["keyboard"][0][0].get("request_contact") is True and kb["one_time_keyboard"] is True,
            "phone step: one-time reply keyboard with request_contact, Skip always offered")
    c.check(any(p.get("reply_markup") == {"remove_keyboard": True} for p in t.params_of("sendMessage")),
            "the reply keyboard is removed after the step")


if __name__ == "__main__":
    if "--write-payload" in sys.argv:
        print(f.write_payload(f.payload_doc(PAYLOAD, run()[0], status=STATUS, context=CONTEXT)))
    else:
        main()
