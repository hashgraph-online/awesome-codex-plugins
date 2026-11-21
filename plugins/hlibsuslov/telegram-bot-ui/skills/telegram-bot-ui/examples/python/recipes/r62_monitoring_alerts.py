"""R62 - Monitoring bot: uptime and price watches, alerts, mute, quiet hours, digest.

Subscriptions (paginated) -> add a watch (target buttons + typed threshold behind a
force_reply keyboard) -> per-watch settings -> incoming events -> alerts / digest.

Invariants shown (offline, against fixtures):
* an event id is processed once; the same watch does not alert again within
  FLAP seconds (flapping suppression, the count is shown on the next alert);
* alerts are NEW messages (a push); info alerts and quiet-hours alerts are silent
  (disable_notification), critical ones always sound;
* a digest is one Rich Message with a compact table at the digest hour, and no digest
  is sent when nothing happened;
* an alert is acknowledged once, only by its owner; an event for a deleted watch is dropped;
* mute is a Scheduler job: "until tomorrow" unmutes by itself and reports what was held back.

Run:  py -3 examples/python/recipes/r62_monitoring_alerts.py [--write-payload]
"""
from __future__ import annotations

import re
import sys

import _common as c
from tgkit import flows as f
from tgkit.rich import table
from tgkit.transport import FakeTransport

PAYLOAD = "r62-monitoring-alerts"
STATUS = "production"
CONTEXT = "private"
PAGE, FLAP, DIGEST_HOUR = 3, 600, 9
ALICE = f.user(111111111, "Alice", "en")
IGOR = f.user(222222222, "Игорь", "ru")
TARGETS = {"api": ("api.example.com", "uptime"), "shop": ("shop.example.com", "uptime"),
           "btc": ("BTC/USD", "price"), "eth": ("ETH/USD", "price")}
SEV = {"info": 0, "warning": 1, "critical": 2}

COPY = {
    "en": {
        "list": "<b>Your watches</b> · {n}\nTap one to change it.",
        "list_empty": "<b>No watches yet</b>\nAdd a site to monitor or a price level.",
        "add": "<b>What should I watch?</b>",
        "ask_uptime": "Alert when <b>{target}</b> answers slower than N ms. Reply with N (100-60000).",
        "ask_price": "Alert when <b>{target}</b> falls to or below a price. Reply with the price in USD.",
        "err_uptime": "That is not a number from 100 to 60000. Reply with N, for example 800.",
        "err_price": "I need a price above 0, for example 62000. Reply with the number.",
        "watch": "<b>{target}</b>\nAlert at: {limit}\nMode: {mode}\nMuted: {muted}\nQuiet hours 23:00-07:00: {quiet}",
        "limit_uptime": "slower than {n} ms",
        "limit_price": "at or below ${n}",
        "mode_instant": "instant",
        "mode_digest": "daily digest at 09:00",
        "no": "no",
        "on": "on",
        "off": "off",
        "until": "until {when}",
        "confirm": "<b>Delete the watch for {target}?</b>\nIts alerts stop right away.",
        "sev_critical": "🔴 Critical",
        "sev_warning": "🟠 Warning",
        "sev_info": "🔵 Info",
        "d_slow": "Answering in {value} ms (limit {limit} ms)",
        "d_down": "No answer (limit {limit} ms)",
        "d_price": "Price ${value} (limit ${limit})",
        "again": "\n+{n} similar alerts in the last 10 minutes",
        "acked": "✓ Acknowledged by {who}",
        "unmuted": "<b>Unmuted: {target}</b>\n{n} alert(s) were held back. Latest: {latest}",
        "digest_title": "Daily digest · {n} event(s)",
        "col_watch": "Watch",
        "col_events": "Events",
        "col_worst": "Worst",
        "col_last": "Last value",
        "toast_ack": "Acknowledged",
        "toast_already": "Already acknowledged.",
        "toast_muted": "Muted until {when}",
        "toast_gone": "This watch was deleted.",
        "btn_add": "Add a watch",
        "btn_back": "← Back",
        "btn_threshold": "Threshold",
        "btn_instant": "Instant",
        "btn_digest": "Digest",
        "btn_m1": "Mute 1 h",
        "btn_m8": "Mute 8 h",
        "btn_mt": "Until tomorrow",
        "btn_unmute": "Unmute",
        "btn_quiet": "Quiet hours",
        "btn_delete": "Delete watch",
        "btn_confirm": "Delete",
        "btn_cancel": "Cancel",
        "btn_ack": "Acknowledge",
        "btn_acked": "✓ Acknowledged",
        "btn_settings": "Settings",
        "sys_stale": "This screen has changed. Use the latest message.",
        "sys_not_yours": "This message belongs to someone else.",
        "sys_expired": "This menu has expired. Send /start.",
    },
    "ru": {
        "list": "<b>Ваши наблюдения</b> · {n}\nНажмите, чтобы изменить.",
        "list_empty": "<b>Наблюдений пока нет</b>\nДобавьте сайт для проверки или уровень цены.",
        "add": "<b>За чем следить?</b>",
        "ask_uptime": "Сообщу, если <b>{target}</b> отвечает дольше N мс. Ответьте числом N (100-60000).",
        "ask_price": "Сообщу, когда цена <b>{target}</b> упадёт до порога или ниже. Ответьте ценой в USD.",
        "err_uptime": "Это не число от 100 до 60000. Ответьте числом N, например 800.",
        "err_price": "Нужна цена больше 0, например 62000. Ответьте числом.",
        "watch": "<b>{target}</b>\nСигнал: {limit}\nРежим: {mode}\nБез звука: {muted}\nТихие часы 23:00-07:00: {quiet}",
        "limit_uptime": "дольше {n} мс",
        "limit_price": "не выше ${n}",
        "mode_instant": "сразу",
        "mode_digest": "сводка в 09:00",
        "no": "нет",
        "on": "вкл.",
        "off": "выкл.",
        "until": "до {when}",
        "confirm": "<b>Удалить наблюдение за {target}?</b>\nСигналы по нему сразу прекратятся.",
        "sev_critical": "🔴 Критично",
        "sev_warning": "🟠 Внимание",
        "sev_info": "🔵 Инфо",
        "d_slow": "Отвечает за {value} мс (порог {limit} мс)",
        "d_down": "Нет ответа (порог {limit} мс)",
        "d_price": "Цена ${value} (порог ${limit})",
        "again": "\n+{n} похожих сигналов за последние 10 минут",
        "acked": "✓ Принял: {who}",
        "unmuted": "<b>Звук включён: {target}</b>\nПропущено сигналов: {n}. Последний: {latest}",
        "digest_title": "Сводка за день · событий: {n}",
        "col_watch": "Наблюдение",
        "col_events": "События",
        "col_worst": "Худшее",
        "col_last": "Последнее",
        "toast_ack": "Принято",
        "toast_already": "Уже принято.",
        "toast_muted": "Без звука до {when}",
        "toast_gone": "Это наблюдение удалено.",
        "btn_add": "Добавить",
        "btn_back": "← Назад",
        "btn_threshold": "Порог",
        "btn_instant": "Сразу",
        "btn_digest": "Сводка",
        "btn_m1": "Тишина 1 ч",
        "btn_m8": "Тишина 8 ч",
        "btn_mt": "До завтра",
        "btn_unmute": "Включить звук",
        "btn_quiet": "Тихие часы",
        "btn_delete": "Удалить",
        "btn_confirm": "Удалить",
        "btn_cancel": "Отмена",
        "btn_ack": "Принять",
        "btn_acked": "✓ Принято",
        "btn_settings": "Настройки",
        "sys_stale": "Экран изменился. Пользуйтесь последним сообщением.",
        "sys_not_yours": "Это сообщение другого человека.",
        "sys_expired": "Меню устарело. Отправьте /start.",
    },
}
I18N = f.I18n(COPY)


def clock(ts: int) -> str:
    return f"{ts % 86400 // 3600:02d}:{ts % 3600 // 60:02d} UTC"


def quiet_hour(ts: int) -> bool:
    return ts % 86400 // 3600 >= 23 or ts % 86400 // 3600 < 7


class Monitor:
    def __init__(self, t: FakeTransport, now: int):
        self.t, self.now = t, now
        self.flow = f.ScreenFlow(t, "mo", i18n=I18N)
        self.sched, self.updates, self.seen = f.Scheduler(), f.UpdateDedup(), set()
        self.alerts: dict[str, dict] = {}
        self.log: list[dict] = []
        self.n = 0
        self._screens()

    # ---- helpers ------------------------------------------------------------------
    def watches(self, s: f.Session) -> dict[str, dict]:
        return s.data.setdefault("watches", {})

    def limit_text(self, lang: str, w: dict) -> str:
        return I18N.t(lang, f"limit_{TARGETS[w['target']][1]}", n=w["limit"])

    def when(self, lang: str, ts: int) -> f.Raw:
        return f.tg_time(ts, clock(ts))

    def mute(self, s: f.Session, w: dict, until: int) -> None:
        w["muted_until"] = until
        self.sched.at(until, f"unmute:{w['id']}", uid=s.owner_id)      # replaces a previous mute job

    # ---- screens ------------------------------------------------------------------
    def _screens(self) -> None:
        fl = self.flow

        @fl.screen("list")
        def list_(fl, s):
            ws = list(self.watches(s).values())
            if not ws:
                return {"text": fl.tr(s, "list_empty"),
                        "reply_markup": f.kb([f.btn(fl.tr(s, "btn_add"), fl.cb(s, "add"), style="primary")])}
            part, page, pages = f.paginate(ws, s.args.get("page", 0), PAGE)
            rows = [[f.btn(f"{'🔕 ' if w['muted_until'] > self.now else ''}{TARGETS[w['target']][0]} · "
                           f"{self.limit_text(s.lang, w)}", fl.cb(s, "watch", w["id"]))] for w in part]
            return {"text": fl.tr(s, "list", n=len(ws)),
                    "reply_markup": f.kb(*rows, f.pager_row(fl, s, page, pages, "page"),
                                         [f.btn(fl.tr(s, "btn_add"), fl.cb(s, "add"), style="primary")])}

        @fl.screen("add")
        def add(fl, s):
            have = {w["target"] for w in self.watches(s).values()}
            rows = [[f.btn(f"✓ {name}", disabled=True) if k in have else f.btn(name, fl.cb(s, "pick", k))]
                    for k, (name, _) in TARGETS.items()]
            return {"text": fl.tr(s, "add"),
                    "reply_markup": f.kb(*rows, [f.btn(fl.tr(s, "btn_back"), fl.cb(s, "list"))])}

        @fl.screen("threshold")
        def threshold(fl, s):        # force_reply is fixed for a message: always a NEW message
            name, kind = TARGETS[s.args["target"]]
            return {"text": fl.tr(s, f"ask_{kind}", target=name),
                    "reply_markup": f.kb([f.btn(fl.tr(s, "btn_back"), fl.cb(s, "back_from_ask"))], force_reply=True)}

        @fl.screen("watch")
        def watch(fl, s):
            w = self.watches(s)[s.args["wid"]]
            muted = w["muted_until"] > self.now
            text = fl.tr(s, "watch", target=TARGETS[w["target"]][0], limit=self.limit_text(s.lang, w),
                         mode=fl.tr(s, f"mode_{w['mode']}"), quiet=fl.tr(s, "on" if w["quiet"] else "off"),
                         muted=f.Raw(fl.tr(s, "until", when=self.when(s.lang, w["muted_until"])) if muted else fl.tr(s, "no")))
            mode = [f.btn(fl.tr(s, "btn_instant"), disabled=True) if w["mode"] == "instant" else f.btn(fl.tr(s, "btn_instant"), fl.cb(s, "mode", "instant")),
                    f.btn(fl.tr(s, "btn_digest"), disabled=True) if w["mode"] == "digest" else f.btn(fl.tr(s, "btn_digest"), fl.cb(s, "mode", "digest"))]
            mutes = ([f.btn(fl.tr(s, "btn_unmute"), fl.cb(s, "unmute"))] if muted else
                     [f.btn(fl.tr(s, "btn_m1"), fl.cb(s, "mute", "1h")), f.btn(fl.tr(s, "btn_m8"), fl.cb(s, "mute", "8h")),
                      f.btn(fl.tr(s, "btn_mt"), fl.cb(s, "mute", "tomorrow"))])
            return {"text": text, "reply_markup": f.kb(
                [f.btn(f"{fl.tr(s, 'btn_threshold')}: {self.limit_text(s.lang, w)}", fl.cb(s, "edit"))], mode, mutes,
                [f.btn(f"{fl.tr(s, 'btn_quiet')}: {fl.tr(s, 'on' if w['quiet'] else 'off')}", fl.cb(s, "quiet"))],
                [f.btn(fl.tr(s, "btn_back"), fl.cb(s, "list")), f.btn(fl.tr(s, "btn_delete"), fl.cb(s, "delete"), style="danger")])}

        @fl.screen("confirm")
        def confirm(fl, s):
            w = self.watches(s)[s.args["wid"]]
            return {"text": fl.tr(s, "confirm", target=TARGETS[w["target"]][0]),
                    "reply_markup": f.kb([f.btn(fl.tr(s, "btn_confirm"), fl.cb(s, "drop"), style="danger"),
                                          f.btn(fl.tr(s, "btn_cancel"), fl.cb(s, "back"))])}

        def act(name):
            return fl.action(name)

        @act("list")
        def a_list(fl, s, args, cq):
            fl.open(s, "list")

        @act("page")
        def a_page(fl, s, args, cq):
            s.args["page"] = int(args[0])
            fl.refresh(s)

        @act("add")
        def a_add(fl, s, args, cq):
            fl.go(s, "add")

        @act("pick")
        def a_pick(fl, s, args, cq):
            if args[0] in TARGETS:
                fl.open(s, "threshold", new_message=True, target=args[0])

        @act("back_from_ask")
        def a_ask_back(fl, s, args, cq):
            if s.args.get("wid"):
                fl.open(s, "watch", new_message=True, wid=s.args["wid"])
            else:
                fl.open(s, "add", new_message=True)

        @act("watch")
        def a_watch(fl, s, args, cq):
            fl.go(s, "watch", wid=args[0]) if args[0] in self.watches(s) else fl.answer(cq, fl.tr(s, "toast_gone"))

        @act("edit")
        def a_edit(fl, s, args, cq):
            w = self.watches(s)[s.args["wid"]]
            fl.open(s, "threshold", new_message=True, target=w["target"], wid=w["id"])

        @act("mode")
        def a_mode(fl, s, args, cq):
            self.watches(s)[s.args["wid"]]["mode"] = "digest" if args[0] == "digest" else "instant"
            fl.refresh(s)

        @act("quiet")
        def a_quiet(fl, s, args, cq):
            w = self.watches(s)[s.args["wid"]]
            w["quiet"] = not w["quiet"]
            fl.refresh(s)

        @act("mute")
        def a_mute(fl, s, args, cq):
            w = self.watches(s)[s.args["wid"]]
            day = self.now // 86400 * 86400
            until = {"1h": self.now + 3600, "8h": self.now + 8 * 3600, "tomorrow": day + 86400 + 8 * 3600}[args[0]]
            self.mute(s, w, until)
            fl.refresh(s)

        @act("unmute")
        def a_unmute(fl, s, args, cq):
            w = self.watches(s)[s.args["wid"]]
            w["muted_until"], w["held"] = 0, []
            self.sched.cancel(f"unmute:{w['id']}")
            fl.refresh(s)

        @act("delete")
        def a_delete(fl, s, args, cq):
            fl.go(s, "confirm", wid=s.args["wid"])

        @act("back")
        def a_back(fl, s, args, cq):
            fl.back(s)

        @act("drop")
        def a_drop(fl, s, args, cq):
            wid = s.args["wid"]
            self.watches(s).pop(wid, None)
            self.sched.cancel(f"unmute:{wid}")
            fl.open(s, "list")

    # ---- typed threshold (reply to the force_reply prompt) ---------------------------------
    def on_text(self, msg: dict) -> str:
        uid, chat, text = msg["from"]["id"], msg["chat"]["id"], msg.get("text", "")
        lang = I18N.lang_for(msg["from"].get("language_code"))
        s = self.flow.session(chat, uid, lang=lang)
        if text.startswith("/start"):
            self.sched.at((self.now // 86400 + (self.now % 86400 >= DIGEST_HOUR * 3600)) * 86400 + DIGEST_HOUR * 3600,
                          f"digest:{uid}", uid=uid)
            self.flow.open(s, "list", new_message=True)
            return "list"
        if s.screen != "threshold" or (msg.get("reply_to_message") or {}).get("message_id") != s.message_id:
            return "ignored"
        kind = TARGETS[s.args["target"]][1]
        m = re.fullmatch(r"\s*(\d{1,7}(?:[.,]\d{1,2})?)\s*", text)
        value = float(m[1].replace(",", ".")) if m else 0
        ok = 100 <= value <= 60000 and value == int(value) if kind == "uptime" else 0 < value <= 10_000_000
        if not ok:                               # error on the same step: the prompt stays live
            self.t.call("sendMessage", {"chat_id": chat, "text": I18N.t(lang, f"err_{kind}"),
                                        "reply_parameters": {"message_id": s.message_id}})
            return "invalid"
        limit = int(value) if value == int(value) else value
        w = next((x for x in self.watches(s).values() if x["target"] == s.args["target"]), None)   # key: (user, target)
        if w is None:
            self.n += 1
            w = {"id": f"w{self.n}", "target": s.args["target"], "mode": "instant", "muted_until": 0, "quiet": False,
                 "last_alert_at": None, "suppressed": 0, "held": []}
            self.watches(s)[w["id"]] = w
        w["limit"] = limit
        self.flow.open(s, "watch", new_message=True, wid=w["id"])
        return "saved"

    # ---- incoming events ----------------------------------------------------------------------
    def on_event(self, ev: dict) -> list[str]:
        if ev["id"] in self.seen:                # a bounded window in production
            return ["duplicate"]
        self.seen.add(ev["id"])
        self.now = max(self.now, ev["at"])
        hits = [(s, w) for s in self.flow.sessions.values() for w in self.watches(s).values() if w["target"] == ev["target"]]
        if not hits:
            self.log.append({"event": "dropped", "id": ev["id"], "why": "no watch"})
            return ["dropped"]
        return [self.deliver(s, w, ev) for s, w in hits]

    def deliver(self, s: f.Session, w: dict, ev: dict) -> str:
        uptime = TARGETS[w["target"]][1] == "uptime"
        if not (ev["value"] >= w["limit"] if uptime else ev["value"] <= w["limit"]):
            return "below_limit"
        if w["muted_until"] > ev["at"]:
            w["held"].append(ev)
            return "muted"
        if w["last_alert_at"] is not None and ev["at"] - w["last_alert_at"] < FLAP:
            w["suppressed"] += 1                 # flapping: counted, not sent
            return "suppressed"
        critical = ev["severity"] == "critical"
        if w["mode"] == "digest" and not critical:       # critical never waits for the digest
            s.data.setdefault("digest", []).append(ev)
            return "digested"
        w["last_alert_at"] = ev["at"]
        silent = ev["severity"] == "info" or (w["quiet"] and quiet_hour(ev["at"]) and not critical)
        self.send_alert(s, w, ev, silent)
        return "alerted_silent" if silent else "alerted"

    def detail(self, lang: str, w: dict, ev: dict) -> str:
        if TARGETS[w["target"]][1] == "price":
            return I18N.t(lang, "d_price", value=ev["value"], limit=w["limit"])
        return I18N.t(lang, "d_down" if ev["value"] >= 60000 else "d_slow", value=ev["value"], limit=w["limit"])

    def send_alert(self, s: f.Session, w: dict, ev: dict, silent: bool) -> None:
        self.n += 1
        aid, lang = f"a{self.n}", s.lang
        head = f"<b>{I18N.t(lang, 'sev_' + ev['severity'])} · {f.escape_html(TARGETS[w['target']][0])}</b>\n{self.detail(lang, w, ev)}"
        if w["suppressed"]:
            head += I18N.t(lang, "again", n=w["suppressed"])
            w["suppressed"] = 0
        # One primary action per message. Acknowledge is not destructive, so it is primary, never danger.
        keys = f.kb([f.btn(I18N.t(lang, "btn_ack"), f.pack("al", "ack", aid), style="primary" if ev["severity"] == "critical" else None),
                     f.btn(I18N.t(lang, "btn_m1"), f.pack("al", "m1", aid))])
        params = {"chat_id": s.chat_id, "text": head, "parse_mode": "HTML", "reply_markup": keys}
        if silent:
            params["disable_notification"] = True
        self.alerts[aid] = {"uid": s.owner_id, "chat": s.chat_id, "wid": w["id"], "head": head, "acked": False,
                            "message_id": self.t.call("sendMessage", params)["message_id"]}

    def on_alert_tap(self, cq: dict) -> str:
        _, action, aid = f.unpack(cq["data"])
        a = self.alerts.get(aid)
        s = self.flow.sessions.get((a["chat"], a["uid"])) if a else None
        lang = I18N.lang_for(cq["from"].get("language_code"))
        if a is None or s is None:
            self.flow.answer(cq, I18N.t(lang, "sys_expired"))
            return "expired"
        if cq["from"]["id"] != a["uid"]:
            self.flow.answer(cq, I18N.t(lang, "sys_not_yours"), alert=True)
            return "not_yours"
        w = self.watches(s).get(a["wid"])
        if w is None:
            self.flow.answer(cq, I18N.t(lang, "toast_gone"), alert=True)
            return "watch_deleted"
        if action == "ack":
            if a["acked"]:                       # second tap: refused, nothing changes
                self.flow.answer(cq, I18N.t(lang, "toast_already"))
                return "already_acked"
            a["acked"] = True
            self.t.call("editMessageText", {"chat_id": a["chat"], "message_id": a["message_id"], "parse_mode": "HTML",
                        "text": f"{a['head']}\n{I18N.t(lang, 'acked', who=cq['from']['first_name'])}",
                        "reply_markup": f.kb([f.btn(I18N.t(lang, "btn_acked"), disabled=True)])})
            self.flow.answer(cq, I18N.t(lang, "toast_ack"))
            return "acked"
        self.mute(s, w, self.now + 3600)
        self.flow.answer(cq, I18N.t(lang, "toast_muted", when=clock(self.now + 3600)))
        return "muted"

    # ---- scheduler: unmute and digest --------------------------------------------------------------
    def tick(self, now: int) -> list[str]:
        self.now, out = max(self.now, now), []
        for job in self.sched.due(now):
            kind, key = job.key.split(":")
            s = self.flow.sessions.get((job.payload["uid"], job.payload["uid"]))
            if kind == "digest":
                self.sched.at(job.at + 86400, job.key, **job.payload)
                out.append(self.send_digest(s))
            elif s and key in self.watches(s) and self.watches(s)[key]["muted_until"] <= now:
                w = self.watches(s)[key]
                if w["held"]:
                    self.t.call("sendMessage", {"chat_id": s.chat_id, "parse_mode": "HTML", "text": I18N.t(
                        s.lang, "unmuted", target=TARGETS[w["target"]][0], n=len(w["held"]),
                        latest=self.detail(s.lang, w, w["held"][-1]))})
                out.append(f"unmuted:{len(w['held'])}")
                w["held"] = []
        return out

    def send_digest(self, s: f.Session) -> str:
        events = s.data.get("digest", [])
        if not events:
            return "no_digest"                   # nothing to report: say nothing
        lang, rows = s.lang, []
        for key in dict.fromkeys(e["target"] for e in events):
            mine = [e for e in events if e["target"] == key]
            worst = max(mine, key=lambda e: SEV[e["severity"]])["severity"]
            rows.append([TARGETS[key][0], str(len(mine)), I18N.t(lang, f"sev_{worst}"), str(mine[-1]["value"])])
        self.t.call("sendRichMessage", {"chat_id": s.chat_id, "rich_message": {"blocks": [
            {"type": "heading", "size": 2, "text": I18N.t(lang, "digest_title", n=len(events))},
            table([I18N.t(lang, k) for k in ("col_watch", "col_events", "col_worst", "col_last")], rows,
                  compact=True, numeric_cols=frozenset({1, 3}))]}})
        s.data["digest"] = []
        return "digest"

    def dispatch(self, update: dict) -> str:
        if not self.updates.first_time(update):
            return "duplicate_update"
        if "callback_query" in update:
            cq = update["callback_query"]
            return self.on_alert_tap(cq) if cq["data"].startswith("al:") else self.flow.handle(cq)
        return self.on_text(update["message"])


def run(t: FakeTransport | None = None):
    t = t or FakeTransport()
    feed = c.fixture("usecase_monitor_events.json")
    t0 = feed["base_time"]
    bot = Monitor(t, now=t0)
    n = [0]

    def upd(**kw) -> dict:
        n[0] += 1
        return {"update_id": 963000 + n[0], **kw}

    def tap(who: dict, action: str, *args, stale: bool = False) -> str:
        s = bot.flow.sessions[(who["id"], who["id"])]
        data = f.pack("mo", f.b36(s.version - stale), action, *args)
        return bot.dispatch(upd(callback_query=f.callback(f"q{n[0]}", who, data, chat_id=who["id"], message_id=s.message_id)))

    def say(who: dict, text: str) -> str:
        s = bot.flow.sessions.get((who["id"], who["id"]))
        reply = s.message_id if s and s.screen == "threshold" else None
        return bot.dispatch(upd(message=f.text_message(who, text, reply_to=reply)))

    def watch(who: dict, target: str, value: str) -> str:
        tap(who, "add")
        tap(who, "pick", target)
        return say(who, value)

    def alert_tap(who: dict, aid: str, action: str = "ack") -> str:
        a = bot.alerts[aid]
        cq = f.callback(f"al{n[0]}", who, f.pack("al", action, aid), chat_id=a["chat"], message_id=a["message_id"])
        return bot.dispatch(upd(callback_query=cq))

    out = {"start": say(ALICE, "/start"), "igor_start": say(IGOR, "/start")}
    out["invalid_then_saved"] = (watch(ALICE, "api", "abc"), say(ALICE, "800"))     # error on the same step, then ok
    out["alice_btc"] = watch(ALICE, "btc", "62000")
    tap(ALICE, "mode", "digest")
    watch(ALICE, "shop", "500")
    tap(ALICE, "quiet")
    watch(ALICE, "eth", "3000")                                                      # 4th watch: second page
    tap(ALICE, "list")
    alice = bot.flow.sessions[(ALICE["id"], ALICE["id"])]
    out["pager"] = bot.flow._params(alice)["reply_markup"]["inline_keyboard"][-2]
    tap(ALICE, "watch", "w4")
    tap(ALICE, "delete")
    tap(ALICE, "drop")                                                               # eth deleted
    watch(IGOR, "api", "500")

    ev = feed["events"]
    out["e1001"] = bot.on_event(ev[0])
    out["e1001_again"] = bot.on_event(ev[1])
    out["e1002"] = bot.on_event(ev[2])
    out["e1003"] = bot.on_event(ev[3])
    out["e1004"] = bot.on_event(ev[4])
    out["e1005"] = bot.on_event(ev[5])
    alert_ids = list(bot.alerts)
    out["ack"] = alert_tap(ALICE, alert_ids[0])
    out["ack_again"] = alert_tap(ALICE, alert_ids[0])
    out["ack_stranger"] = alert_tap(IGOR, alert_ids[0])
    out["mute"] = alert_tap(ALICE, alert_ids[2], "m1")                               # shop alert: mute 1 h
    out["e1006"] = bot.on_event(ev[6])
    out["unmute_tick"] = bot.tick(t0 + 4100)
    tap(IGOR, "watch", next(iter(bot.watches(bot.flow.sessions[(IGOR["id"], IGOR["id"])]))))
    tap(IGOR, "delete")
    tap(IGOR, "drop")                                                                # Igor deletes his api watch
    out["gone_tap"] = alert_tap(IGOR, alert_ids[1])
    out["e1007"] = bot.on_event(ev[7])
    out["e1008"] = bot.on_event(ev[8])
    out["digest_tick"] = bot.tick(t0 + 83700)
    out["digest_next_day"] = bot.tick(t0 + 83700 + 86400)
    return t, bot, out


def main() -> None:
    t, bot, o = run()
    c.dump(t, "Monitoring")
    sends = t.params_of("sendMessage")
    alerts = [p for p in sends if "al:ack" in str(p.get("reply_markup"))]
    c.check(o["invalid_then_saved"] == ("invalid", "saved") and len(bot.watches(bot.flow.sessions[(111111111, 111111111)])) == 3,
            "a bad threshold is refused on the same step; one watch per (user, target)")
    pager = o["pager"]
    c.check(pager[0].get("disabled") == {} and pager[1]["text"] == "1/2" and "callback_data" in pager[2],
            "4 watches -> page 1 of 2: disabled ← and counter, active →")
    c.check(o["e1001"] == ["alerted", "alerted"] and o["e1001_again"] == ["duplicate"]
            and "No answer" in alerts[0]["text"] and "Нет ответа" in alerts[1]["text"],
            "critical alert to both users in their language; duplicate event id dropped")
    ack_btn = alerts[0]["reply_markup"]["inline_keyboard"][0][0]
    c.check(ack_btn["style"] == "primary" and "disable_notification" not in alerts[0]
            and all(b.get("style") != "danger" for p in alerts for b in f.callback_buttons(p["reply_markup"])),
            "Acknowledge is the one primary action, never danger; critical alerts sound")
    c.check(o["e1002"] == ["suppressed", "suppressed"] and o["e1003"] == ["digested"] and o["e1004"] == ["dropped"],
            "flapping suppressed, digest-mode event queued, event for a deleted watch dropped")
    c.check(o["e1005"] == ["alerted_silent"] and alerts[2].get("disable_notification") is True,
            "info alert is silent (disable_notification)")
    c.check(o["ack"] == "acked" and o["ack_again"] == "already_acked" and o["ack_stranger"] == "not_yours"
            and o["gone_tap"] == "watch_deleted", "acknowledge once; stranger and deleted watch refused")
    c.check(o["mute"] == "muted" and o["e1006"] == ["muted"] and o["unmute_tick"] == ["unmuted:1"],
            "mute holds events; the Scheduler unmutes and reports what was held")
    quiet = [p for p in alerts if p.get("disable_notification")]
    c.check(o["e1007"] == ["alerted_silent"] and o["e1008"] == ["alerted"] and len(quiet) == 2,
            "quiet hours: a warning is silent, a critical alert still sounds")
    rich = t.params_of("sendRichMessage")
    c.check(len(rich) == 1 and rich[0]["rich_message"]["blocks"][1]["is_compact"] and o["digest_next_day"] == ["no_digest", "no_digest"],
            "one digest with a compact table; nothing to report -> no digest")


if __name__ == "__main__":
    if "--write-payload" in sys.argv:
        print(f.write_payload(f.payload_doc(PAYLOAD, run()[0], status=STATUS, context=CONTEXT)))
    else:
        main()
