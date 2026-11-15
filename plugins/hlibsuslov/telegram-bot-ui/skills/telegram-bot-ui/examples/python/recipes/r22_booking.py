"""R22 - Appointment booking: service -> date -> slot -> confirm, reminders, reschedule, cancel.

Invariants shown (offline, against fixtures):
* past, closed and fully booked days are DISABLED buttons, taken slots are disabled
  (not hidden), and the server re-checks every confirm (a crafted tap is refused);
* a double confirm creates one booking (idempotency key per attempt); two users racing
  for one slot: the second gets "just taken" and a refreshed slot list;
* 24 h and 2 h reminders live in a `Scheduler` keyed by booking: rescheduling replaces
  them, cancelling removes them; the reminder's own buttons are version-guarded;
* an old slot list is refused after a reschedule; cancel goes through a danger confirm.

Run:  py -3 examples/python/recipes/r22_booking.py [--write-payload]
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone

import _common as c
from tgkit import flows as f
from tgkit.transport import FakeTransport

PAYLOAD = "r22-booking"
STATUS = "production"
CONTEXT = "private"
TZ = timezone(timedelta(hours=1))                  # the salon's time zone; <tg-time> shows each reader's own
NOW = datetime(2026, 11, 16, 16, 30, tzinfo=TZ).timestamp()   # Monday, after the last slot of the day
HOURS = (10, 11, 12, 14, 15, 16)
SERVICES = {"cut": "€35", "color": "€80", "beard": "€20"}
ALICE = f.user(111111111, "Alice", "en")
IVAN = f.user(222222222, "Иван", "ru")

COPY = {
    "en": {
        "services": "<b>Book a visit</b>\nWhat would you like?",
        "date": "<b>{svc}</b>\nPick a day. Greyed days have no free time.",
        "slots": "<b>{svc}</b> · {day}\nPick a time. Greyed times are taken.",
        "confirm": "<b>Confirm your visit</b>\n{svc} · {price}\n{when}",
        "confirm_move": "<b>Move your visit</b>\n{svc}\nFrom {old}\nTo {when}",
        "done": "<b>You are booked</b> · {bid}\n{svc}\n{when}\nWe remind you 24 h and 2 h before.",
        "cancel_ask": "<b>Cancel this visit?</b>\n{svc} · {when}\nThe time goes back to other clients.",
        "cancelled": "Visit {bid} is cancelled. Reminders are off.",
        "reminder": "<b>Reminder</b> · {hours} h to go\n{svc}\n{when}",
        "confirmed": "See you at {when}.",
        "taken": "Someone just took this time. Pick another one.",
        "day_na": "No free time that day.",
        "none": "You have no upcoming visit.",
        "wd_0": "Mon", "wd_1": "Tue", "wd_2": "Wed", "wd_3": "Thu", "wd_4": "Fri", "wd_5": "Sat", "wd_6": "Sun",
        "day_full": "full", "day_closed": "closed", "day_past": "past",
        "svc_cut": "Haircut", "svc_color": "Colour", "svc_beard": "Beard trim",
        "btn_confirm": "Confirm", "btn_back": "← Back", "btn_resched": "Reschedule", "btn_cancel": "Cancel visit",
        "btn_yes_cancel": "Yes, cancel", "btn_keep": "Keep it", "btn_again": "Book again", "btn_mine": "My visit",
        "btn_ok": "I'll be there",
        "sys_stale": "This list is out of date. Use the latest message.",
        "sys_not_yours": "This booking belongs to someone else.",
        "sys_expired": "This menu has expired. Send /start.",
    },
    "ru": {
        "services": "<b>Запись на визит</b>\nЧто хотите?",
        "date": "<b>{svc}</b>\nВыберите день. Серые дни без свободного времени.",
        "slots": "<b>{svc}</b> · {day}\nВыберите время. Серое время занято.",
        "confirm": "<b>Подтвердите визит</b>\n{svc} · {price}\n{when}",
        "confirm_move": "<b>Перенос визита</b>\n{svc}\nБыло {old}\nСтанет {when}",
        "done": "<b>Вы записаны</b> · {bid}\n{svc}\n{when}\nНапомним за 24 ч и за 2 ч.",
        "cancel_ask": "<b>Отменить визит?</b>\n{svc} · {when}\nВремя освободится для других.",
        "cancelled": "Визит {bid} отменён. Напоминания выключены.",
        "reminder": "<b>Напоминание</b> · через {hours} ч\n{svc}\n{when}",
        "confirmed": "Ждём вас: {when}.",
        "taken": "Это время только что заняли. Выберите другое.",
        "day_na": "В этот день нет свободного времени.",
        "none": "Предстоящих визитов нет.",
        "wd_0": "Пн", "wd_1": "Вт", "wd_2": "Ср", "wd_3": "Чт", "wd_4": "Пт", "wd_5": "Сб", "wd_6": "Вс",
        "day_full": "занято", "day_closed": "выходной", "day_past": "прошло",
        "svc_cut": "Стрижка", "svc_color": "Окрашивание", "svc_beard": "Борода",
        "btn_confirm": "Подтвердить", "btn_back": "← Назад", "btn_resched": "Перенести", "btn_cancel": "Отменить визит",
        "btn_yes_cancel": "Да, отменить", "btn_keep": "Оставить", "btn_again": "Записаться снова", "btn_mine": "Мой визит",
        "btn_ok": "Буду",
        "sys_stale": "Список устарел. Используйте последнее сообщение.",
        "sys_not_yours": "Эта запись другого человека.",
        "sys_expired": "Меню устарело. Отправьте /start.",
    },
}
I18N = f.I18n(COPY)


def slot_ts(day, hour: int) -> int:
    return int(datetime(day.year, day.month, day.day, hour, tzinfo=TZ).timestamp())


class Salon:
    def __init__(self, t: FakeTransport, now: float = NOW):
        self.t, self.now = t, now
        self.flow = f.ScreenFlow(t, "bk", i18n=I18N)
        self.bookings: dict[str, dict] = {}
        self.taken: dict[int, str] = {}
        self.once = f.OnceStore()
        self.sched = f.Scheduler()
        self.updates = f.UpdateDedup()
        self.next_id = 1001
        wed, thu = datetime(2026, 11, 18, tzinfo=TZ).date(), datetime(2026, 11, 19, tzinfo=TZ).date()
        for h in HOURS:                                   # Wednesday is fully booked, Thursday 11:00 is taken
            self.taken[slot_ts(wed, h)] = "B-0001"
        self.taken[slot_ts(thu, 11)] = "B-0002"
        self._screens()

    # ---- helpers -----------------------------------------------------------------
    def when(self, ts: int, lang: str) -> f.Raw:
        d = datetime.fromtimestamp(ts, TZ)
        return f.tg_time(ts, f"{I18N.t(lang, f'wd_{d.weekday()}')} {d.day}.{d.month:02d} {d.hour}:00")

    def day_state(self, day) -> str:
        if day.weekday() == 6:
            return "closed"
        times = [slot_ts(day, h) for h in HOURS]
        if all(t <= self.now for t in times):
            return "past"
        return "ok" if any(t > self.now and t not in self.taken for t in times) else "full"

    def schedule(self, b: dict) -> None:
        self.sched.cancel(f"bk:{b['id']}:")               # rescheduling replaces, never duplicates
        for hours in (24, 2):
            at = b["slot"] - hours * 3600
            if at > self.now:
                self.sched.at(at, f"bk:{b['id']}:r{hours}", booking=b["id"], hours=hours, rev=b["rev"])

    def reserve(self, s: f.Session, svc: str, slot: int) -> tuple[dict | None, bool]:
        """Create or move a booking once per attempt. (None, False) = slot just taken."""
        rid = s.data.get("resched")
        key = f"{s.owner_id}:{s.data['attempt']}:{slot}"
        if key in self.once.done:
            return self.once.done[key], False
        if slot <= self.now or self.taken.get(slot, rid) != rid:
            return None, False

        def create() -> dict:
            if rid:
                b = self.bookings[rid]
                self.taken.pop(b["slot"], None)
                b["slot"], b["rev"], b["confirmed"] = slot, b["rev"] + 1, False
            else:
                b = {"id": f"B-{self.next_id}", "user": s.owner_id, "lang": s.lang, "svc": svc, "slot": slot,
                     "rev": 1, "status": "active", "confirmed": False}
                self.next_id += 1
                self.bookings[b["id"]] = b
            self.taken[slot] = b["id"]
            self.schedule(b)
            return b
        return self.once.run(key, create)

    def mine(self, uid: int) -> dict | None:
        return next((b for b in self.bookings.values() if b["user"] == uid and b["status"] == "active"), None)

    # ---- screens -------------------------------------------------------------------
    def _screens(self) -> None:
        fl = self.flow

        @fl.screen("services")
        def services(fl, s):
            rows = [[f.btn(f"{fl.tr(s, 'svc_' + k)} · {price}", fl.cb(s, "svc", k))] for k, price in SERVICES.items()]
            if self.mine(s.owner_id):
                rows.append([f.btn(fl.tr(s, "btn_mine"), fl.cb(s, "mine"))])
            return {"text": fl.tr(s, "services"), "reply_markup": f.kb(*rows)}

        @fl.screen("date")
        def date(fl, s):
            btns = []
            for i in range(7):
                day = (datetime.fromtimestamp(self.now, TZ) + timedelta(days=i)).date()
                state, label = self.day_state(day), f"{fl.tr(s, f'wd_{day.weekday()}')} {day.day}"
                btns.append(f.btn(label, fl.cb(s, "day", day.strftime("%Y%m%d"))) if state == "ok"
                            else f.btn(f"{label} · {fl.tr(s, 'day_' + state)}", disabled=True))
            rows = [btns[i:i + 2] for i in range(0, 7, 2)] + [[f.btn(fl.tr(s, "btn_back"), fl.cb(s, "back"))]]
            return {"text": fl.tr(s, "date", svc=fl.tr(s, "svc_" + s.args["svc"])), "reply_markup": f.kb(*rows)}

        @fl.screen("slots")
        def slots(fl, s):
            day = datetime.strptime(s.args["day"], "%Y%m%d").replace(tzinfo=TZ)
            btns = []
            for h in HOURS:
                ts, label = slot_ts(day, h), f"{h}:00"
                free = ts > self.now and self.taken.get(ts, s.data.get("resched")) == s.data.get("resched")
                btns.append(f.btn(label, fl.cb(s, "slot", ts)) if free else f.btn(f"{label} ✕", disabled=True))
            rows = [btns[i:i + 3] for i in range(0, len(btns), 3)] + [[f.btn(fl.tr(s, "btn_back"), fl.cb(s, "back"))]]
            return {"text": fl.tr(s, "slots", svc=fl.tr(s, "svc_" + s.args["svc"]),
                                  day=f"{fl.tr(s, f'wd_{day.weekday()}')} {day.day}"), "reply_markup": f.kb(*rows)}

        @fl.screen("confirm")
        def confirm(fl, s):
            svc, rid = fl.tr(s, "svc_" + s.args["svc"]), s.data.get("resched")
            when = self.when(int(s.args["slot"]), s.lang)
            text = (fl.tr(s, "confirm_move", svc=svc, old=self.when(self.bookings[rid]["slot"], s.lang), when=when)
                    if rid else fl.tr(s, "confirm", svc=svc, price=SERVICES[s.args["svc"]], when=when))
            return {"text": text, "reply_markup": f.kb([f.btn(fl.tr(s, "btn_confirm"), fl.cb(s, "book"), style="primary")],
                                                       [f.btn(fl.tr(s, "btn_back"), fl.cb(s, "back"))])}

        @fl.screen("done")
        def done(fl, s):
            b = self.bookings[s.args["bid"]]
            return {"text": fl.tr(s, "done", bid=b["id"], svc=fl.tr(s, "svc_" + b["svc"]), when=self.when(b["slot"], s.lang)),
                    "reply_markup": f.kb([f.btn(fl.tr(s, "btn_resched"), fl.cb(s, "resched", b["id"]))],
                                         [f.btn(fl.tr(s, "btn_cancel"), fl.cb(s, "cancel", b["id"]))])}

        @fl.screen("cancel_ask")
        def cancel_ask(fl, s):
            b = self.bookings[s.args["bid"]]
            return {"text": fl.tr(s, "cancel_ask", svc=fl.tr(s, "svc_" + b["svc"]), when=self.when(b["slot"], s.lang)),
                    "reply_markup": f.kb([f.btn(fl.tr(s, "btn_yes_cancel"), fl.cb(s, "cancel_yes", b["id"]), style="danger")],
                                         [f.btn(fl.tr(s, "btn_keep"), fl.cb(s, "back"), style="primary")])}

        @fl.screen("cancelled")
        def cancelled(fl, s):
            return {"text": fl.tr(s, "cancelled", bid=s.args["bid"]),
                    "reply_markup": f.kb([f.btn(fl.tr(s, "btn_again"), fl.cb(s, "home"))])}

        def own(s, bid, cq) -> dict | None:
            b = self.bookings.get(bid)
            if b is None or b["user"] != s.owner_id:         # object-level check: ids travel in callback_data
                fl.answer(cq, fl.tr(s, "sys_not_yours"), alert=True)
                return None
            return b

        @fl.action("svc")
        def a_svc(fl, s, args, cq):
            s.data["attempt"], s.data["resched"] = s.data.get("attempt", 0) + 1, None
            fl.go(s, "date", svc=args[0])

        @fl.action("day")
        def a_day(fl, s, args, cq):
            if self.day_state(datetime.strptime(args[0], "%Y%m%d").replace(tzinfo=TZ).date()) != "ok":
                fl.answer(cq, fl.tr(s, "day_na"), alert=True)     # a disabled button can still be crafted
                return "day_unavailable"
            fl.go(s, "slots", svc=s.args["svc"], day=args[0])

        @fl.action("slot")
        def a_slot(fl, s, args, cq):
            fl.go(s, "confirm", svc=s.args["svc"], slot=args[0])

        @fl.action("book")
        def a_book(fl, s, args, cq):
            b, first = self.reserve(s, s.args["svc"], int(s.args["slot"]))
            if b is None:
                fl.answer(cq, fl.tr(s, "taken"), alert=True)
                fl.back(s)                                # the slot list again, now without that time
                return "taken"
            s.data["resched"] = None
            fl.open(s, "done", bid=b["id"])
            return "booked" if first else "already_booked"

        @fl.action("mine")
        def a_mine(fl, s, args, cq):
            fl.go(s, "done", bid=self.mine(s.owner_id)["id"])

        @fl.action("resched")
        def a_resched(fl, s, args, cq):
            b = own(s, args[0], cq)
            if b is None:
                return "not_yours"
            s.data["attempt"], s.data["resched"] = s.data.get("attempt", 0) + 1, b["id"]
            fl.go(s, "date", svc=b["svc"])

        @fl.action("cancel")
        def a_cancel(fl, s, args, cq):
            if own(s, args[0], cq) is None:
                return "not_yours"
            fl.go(s, "cancel_ask", bid=args[0])

        @fl.action("cancel_yes")
        def a_cancel_yes(fl, s, args, cq):
            b = own(s, args[0], cq)
            if b is None:
                return "not_yours"
            if b["status"] == "active":
                b["status"] = "cancelled"
                self.taken.pop(b["slot"], None)
                self.sched.cancel(f"bk:{b['id']}:")
            fl.open(s, "cancelled", bid=b["id"])
            return "cancelled"

        @fl.action("home")
        def a_home(fl, s, args, cq):
            fl.open(s, "services")

        @fl.action("back")
        def a_back(fl, s, args, cq):
            s.data["resched"] = s.data.get("resched") if s.screen != "done" else None
            fl.back(s)

    # ---- reminders and their buttons ----------------------------------------------
    def fire_reminders(self, now: float) -> int:
        self.now, sent = now, 0
        for job in self.sched.due(now):
            b = self.bookings[job.payload["booking"]]
            if b["status"] != "active" or job.payload["rev"] != b["rev"]:
                continue
            data = lambda a: f.pack("br", f.b36(b["rev"]), a, b["id"])  # noqa: E731
            self.t.call("sendMessage", {"chat_id": b["user"], "parse_mode": "HTML", "text": I18N.t(
                b["lang"], "reminder", hours=job.payload["hours"], svc=I18N.t(b["lang"], "svc_" + b["svc"]),
                when=self.when(b["slot"], b["lang"])),
                "reply_markup": f.kb([f.btn(I18N.t(b["lang"], "btn_ok"), data("ok"), style="success"),
                                      f.btn(I18N.t(b["lang"], "btn_resched"), data("mv"))])})
            sent += 1
        return sent

    def on_reminder_tap(self, cq: dict) -> str:
        _, ver, action, bid = f.unpack(cq["data"])
        who, b = cq["from"], self.bookings.get(bid)
        lang = I18N.lang_for(who.get("language_code"))
        if b is None or who["id"] != b["user"]:
            self.flow.answer(cq, I18N.t(lang, "sys_not_yours"), alert=True)
            return "not_yours"
        if ver != f.b36(b["rev"]) or b["status"] != "active":
            self.flow.answer(cq, I18N.t(lang, "sys_stale"))
            return "stale"
        if action == "ok":
            b["confirmed"] = True
            self.t.call("editMessageText", {"chat_id": cq["message"]["chat"]["id"], "message_id": cq["message"]["message_id"],
                                            "parse_mode": "HTML",
                                            "text": I18N.t(lang, "confirmed", when=self.when(b["slot"], lang))})
        else:
            s = self.flow.session(who["id"], who["id"], lang=lang)
            s.data["attempt"], s.data["resched"] = s.data.get("attempt", 0) + 1, b["id"]
            self.flow.open(s, "date", new_message=True, svc=b["svc"])
        self.flow.answer(cq)
        return "confirmed" if action == "ok" else "reschedule_started"

    def dispatch(self, update: dict) -> str:
        if not self.updates.first_time(update):
            return "duplicate_update"
        if "callback_query" in update:
            result = self.flow.handle(update["callback_query"])
            return self.on_reminder_tap(update["callback_query"]) if result == "foreign" else result
        msg = update["message"]
        s = self.flow.session(msg["chat"]["id"], msg["from"]["id"], lang=I18N.lang_for(msg["from"].get("language_code")))
        param = msg["text"].partition(" ")[2]
        if param.startswith("svc_") and param[4:] in SERVICES:     # deep link t.me/<bot>?start=svc_cut
            s.data["attempt"], s.data["resched"] = s.data.get("attempt", 0) + 1, None
            self.flow.open(s, "date", new_message=True, svc=param[4:])
            return "deeplink"
        self.flow.open(s, "services", new_message=True)
        return "services"


def run(t: FakeTransport | None = None):
    t = t or FakeTransport()
    salon = Salon(t)
    fl, n = salon.flow, [0]

    def tap(who: dict, action: str, *args, back: int = 0) -> str:
        s = fl.sessions[(who["id"], who["id"])]
        n[0] += 1
        data = f.pack("bk", f.b36(s.version - back), action, *args)
        return salon.dispatch({"update_id": 2000 + n[0], "callback_query":
                               f.callback(f"cq{n[0]}", who, data, chat_id=who["id"], message_id=s.message_id)})

    def say(who: dict, text: str) -> str:
        n[0] += 1
        return salon.dispatch({"update_id": 3000 + n[0], "message": f.text_message(who, text)})

    thu = slot_ts(datetime(2026, 11, 19, tzinfo=TZ), 12)
    out = {"deeplink": salon.dispatch(c.fixture("usecase_booking_deeplink.json"))}
    out["day_full"] = tap(ALICE, "day", "20261118")            # crafted tap on the fully booked Wednesday
    out["day"] = tap(ALICE, "day", "20261119")
    out["slot_taken"] = tap(ALICE, "slot", slot_ts(datetime(2026, 11, 19, tzinfo=TZ), 11))   # crafted: taken
    out["slot"] = tap(ALICE, "slot", thu)
    # Ivan (ru) reaches the same confirm screen before Alice confirms.
    say(IVAN, "/start")
    tap(IVAN, "svc", "cut"), tap(IVAN, "day", "20261119"), tap(IVAN, "slot", thu)
    out["alice_book"] = tap(ALICE, "book")
    out["double"] = tap(ALICE, "book", back=1)                 # retried tap on the old confirm screen
    bid = "B-1001"
    out["retry_api"] = salon.reserve(fl.sessions[(111111111, 111111111)], "cut", thu)[1]   # same attempt, same key
    out["race"] = tap(IVAN, "book")
    out["race_toast"] = t.params_of("answerCallbackQuery")[-1].get("text", "")
    out["race_slots"] = t.params_of("editMessageText")[-1]["reply_markup"]["inline_keyboard"]
    out["jobs"] = {k: j.at for k, j in salon.sched.jobs.items()}
    # Alice reschedules to Thursday 15:00: reminders are replaced; her old slot list is stale.
    tap(ALICE, "resched", bid)
    tap(ALICE, "day", "20261119")
    tap(ALICE, "slot", slot_ts(datetime(2026, 11, 19, tzinfo=TZ), 14))
    out["moved"] = tap(ALICE, "book")
    out["stale_list"] = tap(ALICE, "slot", thu, back=2)
    out["stolen"] = tap(IVAN, "cancel", bid)                   # Ivan on Alice's booking via his own menu
    out["jobs_moved"] = {k: j.at for k, j in salon.sched.jobs.items()}
    # 24 h before the new time the reminder fires; Alice taps Confirm; an old reminder is stale.
    when_24 = salon.bookings[bid]["slot"] - 24 * 3600
    out["sent24"] = salon.fire_reminders(when_24 + 1)
    rem = t.params_of("sendMessage")[-1]["reply_markup"]["inline_keyboard"][0][0]["callback_data"]
    stranger = f.callback("cqr1", IVAN, rem, chat_id=ALICE["id"], message_id=777)
    out["rem_stranger"] = salon.dispatch({"update_id": 4001, "callback_query": stranger})
    out["rem_ok"] = salon.dispatch({"update_id": 4002, "callback_query":
                                    f.callback("cqr2", ALICE, rem, chat_id=ALICE["id"], message_id=777)})
    stale_rem = f.pack("br", f.b36(1), "ok", bid)              # button from before the reschedule
    out["rem_stale"] = salon.dispatch({"update_id": 4003, "callback_query":
                                       f.callback("cqr3", ALICE, stale_rem, chat_id=ALICE["id"], message_id=770)})
    # Cancel: danger confirm, then reminders are gone and the slot is free again.
    tap(ALICE, "cancel", bid)
    out["cancel"] = tap(ALICE, "cancel_yes", bid)
    out["jobs_cancelled"] = dict(salon.sched.jobs)
    out["slot_free"] = salon.bookings[bid]["slot"] not in salon.taken
    return t, salon, out


def main() -> None:
    t, salon, out = run()
    c.dump(t, "Booking")
    sent = t.params_of("sendMessage") + t.params_of("editMessageText")
    page = lambda needle: next(p for p in sent if needle in p["text"])["reply_markup"]["inline_keyboard"]  # noqa: E731
    flat = [b for row in page("Pick a day") for b in row]
    c.check(flat[0].get("disabled") == {} and "past" in flat[0]["text"] and any("full" in b["text"] for b in flat)
            and any("closed" in b["text"] for b in flat), "past, full and closed days are disabled, not hidden")
    c.check(out["deeplink"] == "deeplink" and out["day_full"] == "day_unavailable",
            "a deep link opens the date picker; a crafted tap on a full day is refused")
    c.check(any(b.get("disabled") == {} and "11:00" in b["text"] for row in page("Pick a time") for b in row),
            "taken slots stay visible but disabled")
    c.check("<tg-time unix=" in next(p for p in sent if "Confirm your visit" in p["text"])["text"],
            "the confirm screen shows the time with <tg-time>")
    c.check(out["alice_book"] == "booked" and out["double"] == "stale" and out["retry_api"] is False
            and len([b for b in salon.bookings.values() if b["user"] == ALICE["id"]]) == 1,
            "a double confirm creates one booking")
    c.check(out["race"] == "taken" and out["race_toast"].startswith("Это время")
            and any("12:00" in b["text"] and "disabled" in b for row in out["race_slots"] for b in row),
            "second user racing for the slot: 'just taken' (own language) and a refreshed list")
    c.check(sorted(out["jobs"]) == ["bk:B-1001:r2", "bk:B-1001:r24"] and sorted(out["jobs_moved"]) == sorted(out["jobs"])
            and all(out["jobs_moved"][k] != out["jobs"][k] for k in out["jobs"]),
            "24 h and 2 h reminders; a reschedule replaces them (same keys, new times)")
    c.check(out["moved"] == "booked" and out["stale_list"] == "stale", "an old slot list is refused after a reschedule")
    c.check(out["stolen"] == "not_yours", "another user's booking id in a callback is refused")
    c.check(out["sent24"] == 1 and out["rem_stranger"] == "not_yours" and out["rem_ok"] == "confirmed"
            and out["rem_stale"] == "stale", "reminder buttons: owner only, version guarded")
    c.check(out["cancel"] == "cancelled" and out["jobs_cancelled"] == {} and out["slot_free"],
            "cancel removes the reminders and frees the slot")
    c.check(any(b.get("style") == "danger" for row in page("Cancel this visit?") for b in row),
            "the cancel confirm screen uses a danger button")


if __name__ == "__main__":
    if "--write-payload" in sys.argv:
        print(f.write_payload(f.payload_doc(PAYLOAD, run()[0], status=STATUS, context=CONTEXT)))
    else:
        main()
