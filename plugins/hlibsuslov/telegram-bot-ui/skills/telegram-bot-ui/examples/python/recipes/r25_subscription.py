"""R25 - Subscription with a paywall and a 7-day trial, paid in Telegram Stars (30-day period).

Invariants shown (offline, against fixtures):
* the trial starts once per user (OnceStore + a persisted flag); a crafted second tap is refused;
* the subscribe button is a URL button with a `createInvoiceLink` link (subscription_period
  2592000, currency XTR, exactly one price item);
* pre_checkout re-checks the payload owner, currency, amount and "already subscribed";
* successful_payment is applied once per telegram_payment_charge_id; renewals
  (is_recurring) move the expiry date taken from subscription_expiration_date;
* "Cancel renewal" = editUserStarSubscription(is_canceled=true): access stays until the
  period end, and can be switched back on; expiry reminders (3 d / 1 d) live in a
  `Scheduler` and are not sent after a renewal or a resume; expiry has a grace window;
* /paysupport is answered (official requirement for bots that take payments).

Run:  py -3 examples/python/recipes/r25_subscription.py [--write-payload]
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone

import _common as c
from tgkit import flows as f
from tgkit.transport import FakeTransport

PAYLOAD = "r25-subscription"
STATUS = "production"
CONTEXT = "private"
NOW = 1794830400                       # 2026-11-16 12:00 UTC; every fixture is dated relative to it
DAY = 86400
PERIOD = 2592000                       # the only allowed subscription_period (30 days)
SUB_STARS = 150
TRIAL_DAYS = 7
GRACE = 6 * 3600                       # a renewal may arrive a little after the period ends
ALICE = f.user(111111111, "Alice", "en")
OLENA = f.user(333333333, "Олена", "uk")

COPY = {
    "en": {
        "paywall": "<b>Pro</b>\nThis part is for subscribers.\n• Unlimited exports\n• Priority support\n• Early features\n\n⭐ {stars} per month, cancel any time.",
        "status_trial": "<b>Pro trial</b>\nFull access until {until}.\nSubscribe to keep it after the trial.",
        "status_active": "<b>Pro is active</b>\nRenews on {until}.",
        "status_canceled": "<b>Pro is active</b>\nRenewal is off: access ends {until}.",
        "expired": "<b>Pro has ended</b>\nYour access ended {until}. Subscribe again to continue.",
        "export_ok": "Your export is ready.",
        "remind_trial": "<b>Your trial ends in {days} d</b> ({until}).\nSubscribe to keep Pro.",
        "remind_canceled": "<b>Pro ends in {days} d</b> ({until}).\nRenewal is off.",
        "renewed": "Pro renewed. Next payment {until}.",
        "toast_trial_used": "The free trial was already used. Subscribe to continue.",
        "toast_canceled": "Renewal is off. Access stays until the end of the period.",
        "toast_resumed": "Renewal is back on.",
        "toast_resume_allowed": "Done: now turn renewal back on in Telegram, in your Stars subscriptions.",
        "toast_resume_in_telegram": "You turned renewal off in Telegram; turn it back on there, in your Stars subscriptions.",
        "sub_failed": "<b>The renewal payment did not go through</b>\nPro stays on until {until}, then ends. Subscribe again to keep it.",
        "pc_active": "You already have an active subscription.",
        "pc_changed": "This invoice is out of date. Open the paywall again.",
        "pay_support": "<b>Payment help</b>\nWrite your question here and add the payment id from the receipt. We answer within a day.",
        "invoice_title": "Pro, 30 days",
        "invoice_desc": "Pro access, renews every 30 days. Cancel in the bot any time.",
        "btn_trial": "Start 7-day trial",
        "btn_trial_used": "Trial used",
        "btn_subscribe": "Subscribe ⭐ {stars}/month",
        "btn_cancel": "Cancel renewal",
        "btn_resume": "Resume renewal",
        "sys_stale": "This screen has changed. Use the latest message.",
        "sys_not_yours": "This menu belongs to someone else. Open your own with /start.",
        "sys_expired": "This menu has expired. Send /start.",
    },
    "uk": {
        "paywall": "<b>Pro</b>\nЦя частина для підписників.\n• Експорт без обмежень\n• Пріоритетна підтримка\n• Ранній доступ до новинок\n\n⭐ {stars} на місяць, скасувати можна будь-коли.",
        "status_trial": "<b>Пробний Pro</b>\nПовний доступ до {until}.\nОформіть підписку, щоб не втратити його.",
        "status_active": "<b>Pro активний</b>\nПродовження {until}.",
        "status_canceled": "<b>Pro активний</b>\nПродовження вимкнено: доступ до {until}.",
        "expired": "<b>Pro завершився</b>\nДоступ закінчився {until}. Оформіть підписку знову.",
        "export_ok": "Експорт готовий.",
        "remind_trial": "<b>Пробний період закінчується через {days} д</b> ({until}).\nОформіть підписку.",
        "remind_canceled": "<b>Pro закінчується через {days} д</b> ({until}).\nПродовження вимкнено.",
        "renewed": "Pro продовжено. Наступний платіж {until}.",
        "toast_trial_used": "Пробний період уже використано. Оформіть підписку.",
        "toast_canceled": "Продовження вимкнено. Доступ лишається до кінця періоду.",
        "toast_resumed": "Продовження знову увімкнено.",
        "toast_resume_allowed": "Готово: тепер увімкніть продовження в Telegram, у підписках на Stars.",
        "toast_resume_in_telegram": "Ви вимкнули продовження в Telegram; увімкніть його там, у підписках на Stars.",
        "sub_failed": "<b>Оплата продовження не пройшла</b>\nPro діє до {until}, потім вимкнеться. Оформіть підписку знову, щоб зберегти доступ.",
        "pc_active": "У вас уже є активна підписка.",
        "pc_changed": "Рахунок застарів. Відкрийте екран підписки ще раз.",
        "pay_support": "<b>Допомога з оплатою</b>\nНапишіть питання сюди й додайте номер платежу з чека. Відповімо протягом доби.",
        "invoice_title": "Pro, 30 днів",
        "invoice_desc": "Доступ до Pro, продовжується кожні 30 днів. Скасувати можна в боті.",
        "btn_trial": "Спробувати 7 днів",
        "btn_trial_used": "Пробний використано",
        "btn_subscribe": "Підписатися ⭐ {stars}/міс",
        "btn_cancel": "Скасувати продовження",
        "btn_resume": "Відновити продовження",
        "sys_stale": "Екран змінився. Користуйтеся останнім повідомленням.",
        "sys_not_yours": "Це меню іншої людини. Відкрийте своє через /start.",
        "sys_expired": "Меню застаріло. Надішліть /start.",
    },
}
I18N = f.I18n(COPY)


def date_text(ts: int) -> f.Raw:
    return f.tg_time(ts, datetime.fromtimestamp(ts, timezone.utc).strftime("%d.%m.%Y"), "d")


class Subscriptions:
    def __init__(self, t: FakeTransport):
        self.t = t
        self.now = NOW
        self.flow = f.ScreenFlow(t, "sb", i18n=I18N)
        self.subs: dict[int, dict] = {}
        self.trials, self.payments, self.links = f.OnceStore(), f.OnceStore(), f.OnceStore()
        self.sched = f.Scheduler()
        self.updates = f.UpdateDedup()
        self._screens()

    # ---- state -------------------------------------------------------------------
    def sub(self, uid: int) -> dict:
        return self.subs.setdefault(uid, {"status": "free", "until": 0, "charge": None, "trial_used": False,
                                          "canceled_by": None, "resume_allowed": False})

    def entitled(self, uid: int) -> bool:
        sb = self.sub(uid)
        return sb["status"] in ("trial", "active", "canceled", "failed") and sb["until"] > self.now  # access follows the expiry

    def schedule(self, uid: int) -> None:
        """Replace this user's jobs. Reminders only when access will really end (trial / renewal off)."""
        sb = self.sub(uid)
        self.sched.cancel(f"sb:{uid}:")
        if sb["status"] not in ("trial", "active", "canceled", "failed"):
            return
        self.sched.at(sb["until"] + GRACE, f"sb:{uid}:exp", uid=uid, until=sb["until"])
        if sb["status"] in ("trial", "canceled"):
            for days in (3, 1):
                if sb["until"] - days * DAY > self.now:
                    self.sched.at(sb["until"] - days * DAY, f"sb:{uid}:r{days}", uid=uid, days=days, until=sb["until"])

    def link(self, uid: int, lang: str) -> str:
        """One invoice link per user; subscription_period makes it a recurring 30-day Stars plan."""
        return self.links.run(f"link:{uid}", lambda: self.t.call("createInvoiceLink", {
            "title": I18N.t(lang, "invoice_title"), "description": I18N.t(lang, "invoice_desc"),
            "payload": f"sub:{uid}", "provider_token": "", "currency": "XTR",
            "prices": [{"label": I18N.t(lang, "invoice_title"), "amount": SUB_STARS}],
            "subscription_period": PERIOD}))[0]

    # ---- screens -------------------------------------------------------------------
    def home(self, s: f.Session) -> None:
        self.flow.open(s, "status" if self.entitled(s.owner_id) else
                       ("expired" if self.sub(s.owner_id)["status"] == "expired" else "paywall"), new_message=True)

    def _screens(self) -> None:
        fl = self.flow

        def subscribe_btn(s):
            return f.btn(fl.tr(s, "btn_subscribe", stars=SUB_STARS), url=self.link(s.owner_id, s.lang), style="primary")

        @fl.screen("paywall")
        def paywall(fl, s):
            used = self.sub(s.owner_id)["trial_used"]
            trial = (f.btn(fl.tr(s, "btn_trial_used"), disabled=True) if used
                     else f.btn(fl.tr(s, "btn_trial"), fl.cb(s, "trial"), style="primary"))
            return {"text": fl.tr(s, "paywall", stars=SUB_STARS),
                    "reply_markup": f.kb([trial], [f.btn(fl.tr(s, "btn_subscribe", stars=SUB_STARS),
                                                         url=self.link(s.owner_id, s.lang))])}

        @fl.screen("expired")
        def expired(fl, s):
            return {"text": fl.tr(s, "expired", until=date_text(self.sub(s.owner_id)["until"])),
                    "reply_markup": f.kb([subscribe_btn(s)])}

        @fl.screen("status")
        def status(fl, s):
            sb = self.sub(s.owner_id)
            text = fl.tr(s, f"status_{sb['status']}", until=date_text(sb["until"]))
            if sb["status"] == "trial":
                rows = [[subscribe_btn(s)]]
            elif sb["status"] == "canceled":
                rows = [[f.btn(fl.tr(s, "btn_resume"), fl.cb(s, "resume"), style="primary")]]
            else:
                rows = [[f.btn(fl.tr(s, "btn_cancel"), fl.cb(s, "cancel"), style="danger")]]
            return {"text": text, "reply_markup": f.kb(*rows)}

        @fl.action("trial")
        def a_trial(fl, s, args, cq):
            sb = self.sub(s.owner_id)
            if sb["trial_used"] or self.entitled(s.owner_id):     # a disabled button can still be crafted
                fl.answer(cq, fl.tr(s, "toast_trial_used"), alert=True)
                return "trial_refused"

            def start() -> None:
                sb.update(status="trial", until=self.now + TRIAL_DAYS * DAY, trial_used=True)
                self.schedule(s.owner_id)
            self.trials.run(f"trial:{s.owner_id}", start)
            fl.open(s, "status")
            return "trial_started"

        @fl.action("cancel")
        def a_cancel(fl, s, args, cq):
            self.cancel_renewal(s.owner_id)
            fl.answer(cq, fl.tr(s, "toast_canceled"))
            fl.refresh(s)
            return "renewal_off"

        @fl.action("resume")
        def a_resume(fl, s, args, cq):
            result = self.allow_resume(s.owner_id)
            fl.answer(cq, fl.tr(s, "toast_" + result))
            fl.refresh(s)
            return result

    def cancel_renewal(self, uid: int) -> None:
        """The bot stops renewal; access lasts to the end of the paid period."""
        sb = self.sub(uid)
        self.t.call("editUserStarSubscription", {"user_id": uid, "telegram_payment_charge_id": sb["charge"],
                                                 "is_canceled": True})
        sb.update(status="canceled", canceled_by="bot", resume_allowed=False)
        self.schedule(uid)

    def allow_resume(self, uid: int) -> str:
        """is_canceled=false does NOT turn renewal back on: it only lets the user re-enable a subscription
        the bot cancelled (Bot API). The subscription is active again when Update.subscription says
        `active`. A subscription the user cancelled in Telegram can only be re-enabled by the user there."""
        sb = self.sub(uid)
        if sb["canceled_by"] != "bot":
            return "resume_in_telegram"
        if not sb["resume_allowed"]:
            self.t.call("editUserStarSubscription", {"user_id": uid, "telegram_payment_charge_id": sb["charge"],
                                                     "is_canceled": False})
            sb["resume_allowed"] = True
        return "resume_allowed"

    def on_subscription(self, upd: dict) -> str:
        """Update.subscription (BotSubscriptionUpdated): the user cancelled or re-enabled renewal in
        Telegram, or a renewal payment failed. It has no charge id: the payload names the user."""
        uid = upd["user"]["id"]
        if upd.get("invoice_payload") != f"sub:{uid}":
            return "sub_unknown"                         # not this product's subscription
        sb, state = self.sub(uid), upd.get("state")
        if state == "canceled":
            sb.update(status="canceled", canceled_by="user", resume_allowed=False)
        elif state == "active":
            sb.update(status="active", canceled_by=None, resume_allowed=False)
        elif state == "failed":
            sb.update(status="failed", canceled_by=None, resume_allowed=False)
            lang = self.flow.session(uid, uid).lang
            self.t.call("sendMessage", {"chat_id": uid, "parse_mode": "HTML",
                                        "text": I18N.t(lang, "sub_failed", until=date_text(sb["until"]))})
        else:
            return "sub_ignored"
        self.schedule(uid)
        return f"sub_{state}"

    # ---- payments ------------------------------------------------------------------
    def on_pre_checkout(self, q: dict) -> bool:
        uid, lang = q["from"]["id"], I18N.lang_for(q["from"].get("language_code"))
        err = None
        if q["invoice_payload"] != f"sub:{uid}" or (q["currency"], q["total_amount"]) != ("XTR", SUB_STARS):
            err = I18N.t(lang, "pc_changed")
        elif self.entitled(uid) and self.sub(uid)["status"] == "active":
            err = I18N.t(lang, "pc_active")         # several concurrent subscriptions are possible: stop them
        params = {"pre_checkout_query_id": q["id"], "ok": err is None}
        if err:
            params["error_message"] = err
        self.t.call("answerPreCheckoutQuery", params)
        return err is None

    def on_payment(self, msg: dict) -> str:
        sp, uid = msg["successful_payment"], msg["from"]["id"]
        if not sp.get("is_recurring") or sp["invoice_payload"] != f"sub:{uid}":
            return "ignored"

        def apply() -> str:
            self.sub(uid).update(status="active", until=sp["subscription_expiration_date"],
                                 charge=sp["telegram_payment_charge_id"])
            self.schedule(uid)                       # moves the expiry job, drops trial/cancel reminders
            return "first" if sp.get("is_first_recurring") else "renewal"

        kind, first = self.payments.run(sp["telegram_payment_charge_id"], apply)
        if not first:
            return "duplicate_payment"
        lang = I18N.lang_for(msg["from"].get("language_code"))
        s = self.flow.session(uid, uid, lang=lang)
        if kind == "first":
            self.flow.open(s, "status", new_message=True)
        else:
            self.t.call("sendMessage", {"chat_id": uid, "parse_mode": "HTML",
                                        "text": I18N.t(lang, "renewed", until=date_text(sp["subscription_expiration_date"]))})
        return "subscribed" if kind == "first" else "renewed"

    # ---- time ---------------------------------------------------------------------
    def tick(self, now: float) -> int:
        """Run due jobs; returns how many messages went out."""
        self.now, sent = now, 0
        for job in self.sched.due(now):
            uid, sb = job.payload["uid"], self.sub(job.payload["uid"])
            if sb["until"] != job.payload["until"] or sb["status"] not in ("trial", "active", "canceled", "failed"):
                continue                              # renewed or changed since: nothing to say
            lang = self.flow.session(uid, uid).lang
            if job.key.endswith(":exp"):
                sb["status"] = "expired"
                s = self.flow.session(uid, uid, lang=lang)
                self.flow.open(s, "expired", new_message=True)
            else:
                days, until = job.payload["days"], date_text(sb["until"])
                if sb["status"] == "trial":
                    button = f.btn(I18N.t(lang, "btn_subscribe", stars=SUB_STARS), url=self.link(uid, lang), style="primary")
                else:
                    button = f.btn(I18N.t(lang, "btn_resume"), f.pack("sr", f.b36(sb["until"]), "resume"), style="primary")
                self.t.call("sendMessage", {"chat_id": uid, "parse_mode": "HTML", "reply_markup": f.kb([button]),
                                            "text": I18N.t(lang, f"remind_{sb['status']}", days=days, until=until)})
            sent += 1
        return sent

    def on_reminder_tap(self, cq: dict) -> str:
        uid, lang = cq["from"]["id"], I18N.lang_for(cq["from"].get("language_code"))
        sb = self.sub(uid)
        if f.unpack(cq["data"])[1] != f.b36(sb["until"]) or sb["status"] != "canceled":
            self.t.call("answerCallbackQuery", {"callback_query_id": cq["id"], "text": I18N.t(lang, "sys_stale")})
            return "stale"
        result = self.allow_resume(uid)
        self.t.call("answerCallbackQuery", {"callback_query_id": cq["id"], "text": I18N.t(lang, "toast_" + result)})
        return result

    def dispatch(self, update: dict) -> str:
        if not self.updates.first_time(update):
            return "duplicate_update"
        if "pre_checkout_query" in update:
            return "pc_ok" if self.on_pre_checkout(update["pre_checkout_query"]) else "pc_refused"
        if "callback_query" in update:
            result = self.flow.handle(update["callback_query"])
            return self.on_reminder_tap(update["callback_query"]) if result == "foreign" else result
        if "subscription" in update:
            return self.on_subscription(update["subscription"])
        msg = update.get("message")
        if msg is None:
            return "ignored"                              # update types this bot does not use
        if "successful_payment" in msg:
            return self.on_payment(msg)
        lang = I18N.lang_for(msg["from"].get("language_code"))
        s = self.flow.session(msg["chat"]["id"], msg["from"]["id"], lang=lang)
        text = msg.get("text", "")
        if text.startswith("/paysupport"):
            self.t.call("sendMessage", {"chat_id": msg["chat"]["id"], "parse_mode": "HTML", "text": I18N.t(lang, "pay_support")})
            return "paysupport"
        if text.startswith("/export"):             # the gated feature
            if self.entitled(s.owner_id):
                self.t.call("sendMessage", {"chat_id": msg["chat"]["id"], "text": I18N.t(lang, "export_ok")})
                return "export"
            self.flow.open(s, "paywall", new_message=True)
            return "paywall"
        self.home(s)
        return "home"


def run(t: FakeTransport | None = None):
    t = t or FakeTransport()
    t.script("createInvoiceLink", *[lambda m, p: f"https://t.me/$sub{p['payload'][4:]}"] * 4)
    bot = Subscriptions(t)
    fl, n = bot.flow, [0]

    def tap(who: dict, action: str, *args) -> str:
        s = fl.sessions[(who["id"], who["id"])]
        n[0] += 1
        return bot.dispatch({"update_id": 6000 + n[0], "callback_query": f.callback(
            f"cq{n[0]}", who, f.pack("sb", f.b36(s.version), action, *args), chat_id=who["id"], message_id=s.message_id)})

    def say(who: dict, text: str) -> str:
        n[0] += 1
        return bot.dispatch({"update_id": 7000 + n[0], "message": f.text_message(who, text)})

    def ticked(who: dict, now: float) -> int:
        """Messages bot.tick() sent to `who` (other users' jobs may run in the same tick)."""
        before = len([p for p in t.params_of("sendMessage") if p["chat_id"] == who["id"]])
        bot.tick(now)
        return len([p for p in t.params_of("sendMessage") if p["chat_id"] == who["id"]]) - before

    def remind_data() -> str:
        return t.params_of("sendMessage")[-1]["reply_markup"]["inline_keyboard"][0][0].get("callback_data", "")

    out = {"start": say(ALICE, "/start"), "gate": say(ALICE, "/export"), "uk_start": say(OLENA, "/start")}
    out["trial"] = tap(ALICE, "trial")
    out["trial_again"] = tap(ALICE, "trial")                        # crafted: current version, trial already used
    a = fl.sessions[(ALICE["id"], ALICE["id"])]
    out["stranger"] = bot.dispatch({"update_id": 6900, "callback_query": f.callback(      # Olena on Alice's menu
        "cqx", OLENA, f.pack("sb", f.b36(a.version), "cancel"), chat_id=ALICE["id"], message_id=a.message_id)})
    out["export_trial"] = say(ALICE, "/export")
    out["rem_trial"] = bot.tick(NOW + 4 * DAY + 1)                  # 3 days before the trial ends
    bot.tick(NOW + 5 * DAY)
    out["pc"] = bot.dispatch(c.fixture("usecase_subscription_pre_checkout.json"))
    first = c.fixture("usecase_subscription_first_payment.json")
    out["pay"] = bot.dispatch(first)
    out["pay_dup_update"] = bot.dispatch(first)                     # webhook retry
    out["pay_dup_charge"] = bot.dispatch({**first, "update_id": 950099})   # same charge, new update id
    out["pc_again"] = bot.dispatch({**c.fixture("usecase_subscription_pre_checkout.json"), "update_id": 950010})
    out["after_pay"] = bot.tick(NOW + 6 * DAY + 1)                  # the trial's 1-day reminder is gone
    out["cancel"] = tap(ALICE, "cancel")
    out["reminder_canceled"] = bot.tick(NOW + 32 * DAY + 1)         # renewal off: 3 days before the end
    out["resume"] = bot.dispatch({"update_id": 7100, "callback_query": f.callback(
        "cqr", ALICE, remind_data(), chat_id=ALICE["id"], message_id=555)})
    out["resume_again"] = bot.dispatch({"update_id": 7102, "callback_query": f.callback(
        "cqr3", ALICE, remind_data(), chat_id=ALICE["id"], message_id=555)})   # second tap: no second API call
    out["status_after_allow"] = bot.sub(ALICE["id"])["status"]          # still canceled until Telegram says so
    out["reenabled"] = bot.dispatch({"update_id": 7103, "subscription": {
        "user": ALICE, "invoice_payload": f"sub:{ALICE['id']}", "state": "active"}})
    out["stale_rem"] = bot.dispatch({"update_id": 7101, "callback_query": f.callback(
        "cqr2", ALICE, remind_data(), chat_id=ALICE["id"], message_id=555)})   # now active: refused
    out["silent"] = bot.tick(NOW + 34 * DAY + 1)                    # resumed: no 1-day reminder
    out["renewal"] = bot.dispatch(c.fixture("usecase_subscription_renewal.json"))
    out["renewed_tick"] = bot.tick(NOW + 35 * DAY + GRACE + 1)      # old expiry job was replaced
    out["alice_until"] = bot.sub(ALICE["id"])["until"]
    out["user_cancel"] = bot.dispatch({"update_id": 7200, "subscription": {
        "user": ALICE, "invoice_payload": f"sub:{ALICE['id']}", "state": "canceled"}})
    edits_before = len(t.params_of("editUserStarSubscription"))
    out["resume_user_cancel"] = tap(ALICE, "resume")
    out["no_edit_for_user_cancel"] = len(t.params_of("editUserStarSubscription")) == edits_before
    out["other_payload"] = bot.dispatch({"update_id": 7201, "subscription": {
        "user": ALICE, "invoice_payload": "something-else", "state": "active"}})
    out["failed"] = bot.dispatch({"update_id": 7202, "subscription": {
        "user": ALICE, "invoice_payload": f"sub:{ALICE['id']}", "state": "failed"}})
    out["failed_entitled"] = bot.entitled(ALICE["id"])            # still paid for: access follows the expiry
    out["failed_after_end"] = bot.tick(bot.sub(ALICE["id"])["until"] + GRACE + 1) == 1 and not bot.entitled(ALICE["id"])
    out["unused_update"] = bot.dispatch({"update_id": 7203, "message_reaction_count": {"chat": {"id": 1}}})
    # Olena (uk): pays, cancels renewal, gets both reminders, then the access expires.
    bot.tick(NOW + 40 * DAY)
    pay = c.fixture("usecase_subscription_first_payment.json")
    olena_pay = {**pay, "update_id": 950200, "message": {**pay["message"], "chat": {"id": 333333333, "type": "private"},
        "from": OLENA, "date": NOW + 40 * DAY, "successful_payment": {**pay["message"]["successful_payment"],
        "invoice_payload": "sub:333333333", "subscription_expiration_date": NOW + 70 * DAY,
        "telegram_payment_charge_id": "stxDEMOsub0003"}}}
    out["olena_pay"] = bot.dispatch(olena_pay)
    out["olena_cancel"] = tap(OLENA, "cancel")
    out["olena_r3"], out["olena_r1"] = ticked(OLENA, NOW + 67 * DAY + 1), ticked(OLENA, NOW + 69 * DAY + 1)
    out["olena_exp"] = ticked(OLENA, NOW + 70 * DAY + GRACE + 1)
    out["olena_gate"] = say(OLENA, "/export")
    out["support"] = say(OLENA, "/paysupport")
    return t, bot, out


def main() -> None:
    t, bot, out = run()
    c.dump(t, "Subscription")
    links = t.params_of("createInvoiceLink")
    c.check(out["start"] == "home" and out["gate"] == "paywall" and len(links) == 2
            and links[0]["subscription_period"] == PERIOD and links[0]["currency"] == "XTR" and len(links[0]["prices"]) == 1,
            "free user sees the paywall; invoice link: XTR, one price, subscription_period 2592000")
    c.check(out["trial"] == "trial_started" and out["trial_again"] == "trial_refused" and bot.trials.runs == 1,
            "the trial starts once; a second trial is refused")
    c.check(out["stranger"] == "not_yours" and out["export_trial"] == "export", "another user's tap refused; trial = access")
    c.check(out["rem_trial"] == 1 and out["after_pay"] == 0, "trial reminder sent; not sent after subscribing")
    c.check([out["pc"], out["pay"], out["pay_dup_update"], out["pay_dup_charge"]] ==
            ["pc_ok", "subscribed", "duplicate_update", "duplicate_payment"], "payment applied once per charge id")
    c.check(out["pc_again"] == "pc_refused" and "active subscription" in t.params_of("answerPreCheckoutQuery")[-1]["error_message"],
            "pre-checkout refuses a second concurrent subscription")
    edits = t.params_of("editUserStarSubscription")
    c.check(out["cancel"] == "renewal_off" and edits[0]["is_canceled"] is True and edits[0]["telegram_payment_charge_id"] == "stxDEMOsub0001",
            "cancel renewal = editUserStarSubscription(is_canceled=true)")
    c.check(out["reminder_canceled"] == 1 and out["resume"] == "resume_allowed" and edits[1]["is_canceled"] is False
            and out["resume_again"] == "resume_allowed" and sum(e["is_canceled"] is False for e in edits) == 1 and out["status_after_allow"] == "canceled"
            and out["reenabled"] == "sub_active" and out["stale_rem"] == "stale" and out["silent"] == 0,
            "resume = allow the user to re-enable (one API call); active only after Update.subscription; then no reminder")
    c.check(out["user_cancel"] == "sub_canceled" and out["resume_user_cancel"] == "resume_in_telegram"
            and out["no_edit_for_user_cancel"] and out["other_payload"] == "sub_unknown"
            and out["failed"] == "sub_failed" and out["failed_entitled"] is True and out["failed_after_end"]
            and out["unused_update"] == "ignored",
            "a cancel made in Telegram is re-enabled there; a failed renewal ends access at the expiry; other updates do not crash")
    c.check(out["renewal"] == "renewed" and out["renewed_tick"] == 0 and bot.sub(ALICE["id"])["until"] == out["alice_until"] > NOW + 60 * DAY,
            "a renewal moves the expiry; the old expiry job does not fire")
    c.check([out["olena_pay"], out["olena_r3"], out["olena_r1"], out["olena_exp"]] == ["subscribed", 1, 1, 1]
            and bot.sub(OLENA["id"])["status"] == "expired", "3 d and 1 d reminders, then the expired state")
    c.check(out["olena_gate"] == "paywall" and out["support"] == "paysupport", "expired user is gated; /paysupport answered")


if __name__ == "__main__":
    if "--write-payload" in sys.argv:
        print(f.write_payload(f.payload_doc(PAYLOAD, run()[0], status=STATUS, context=CONTEXT)))
    else:
        main()
