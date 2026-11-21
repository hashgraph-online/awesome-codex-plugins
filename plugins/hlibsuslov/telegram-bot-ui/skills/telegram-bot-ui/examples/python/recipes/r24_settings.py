"""R24 - Settings and preferences: nested screens, toggles, a back stack, and
destructive actions behind a confirmation with an undo window.

Shown offline:
* one message for the whole settings tree, edited in place; Back returns to the
  parent screen with its state (stack), not to the root;
* toggles flip on tap and re-render; a second tap on the same old render is
  stale, so a double tap can't flip a setting back;
* "Delete my data": confirm screen (danger + safe Cancel), then a 30-second Undo
  window; confirming twice schedules one deletion; Undo after the deletion ran
  says so instead of pretending;
* /settings in a group never shows personal settings there: it offers a deep
  link to the private chat (personal content keeps its audience).

Run:  py -3 examples/python/recipes/r24_settings.py [--write-payload]
"""
from __future__ import annotations

import sys

import _common as c
from tgkit import flows as f
from tgkit.transport import FakeTransport

PAYLOAD = "r24-settings"
STATUS = "production"
CONTEXT = "private (+ a group entry point)"
BOT = "coffee_demo_bot"
ALICE = f.user(111111111, "Alice", "en")
BOGDAN = f.user(222222222, "Богдан", "ru")
GROUP = -1001234567890
UNDO_SECONDS = 30

COPY = {
    "en": {
        "root": "<b>Settings</b>\nLanguage: {lang} · Notifications: {notif}",
        "notif": "<b>Notifications</b>\nTap to turn on or off.",
        "quiet": "<b>Quiet hours</b>\nNo sound between {start}:00 and 08:00. Pick when they start:",
        "lang": "<b>Language</b>",
        "privacy": "<b>Privacy</b>\nShow my name on the weekly leaderboard: {shown}",
        "confirm_delete": "<b>Delete all your data?</b>\nOrders, addresses and settings will be removed. Paid orders stay with the shop for accounting.",
        "deleting": "<b>Deleting in {sec} s</b>\nChanged your mind? Tap Undo.",
        "deleted": "<b>Your data was deleted.</b>\nSend /start to begin again.",
        "undone": "Deletion cancelled. Nothing was removed.",
        "too_late": "Too late — the data is already deleted.",
        "group_hint": "Settings are personal, so they open in our private chat.",
        "on": "on", "off": "off", "shown": "yes", "hidden": "no",
        "btn_lang": "Language: {lang}",
        "btn_notif": "Notifications",
        "btn_privacy": "Privacy",
        "btn_delete": "Delete my data",
        "btn_delete_yes": "Delete everything",
        "btn_cancel": "Cancel",
        "btn_undo": "Undo",
        "btn_back": "← Back",
        "btn_toggle": "{mark} {label}",
        "btn_quiet": "Quiet hours: from {start}:00",
        "btn_open_private": "Open settings",
        "btn_start_again": "Start again",
        "t_shipping": "Shipping updates",
        "t_promos": "Offers and news",
        "t_digest": "Weekly digest",
        "sys_stale": "This screen has changed. Use the latest message.",
        "sys_not_yours": "These are someone else's settings.",
        "sys_expired": "This menu has expired. Send /settings.",
    },
    "ru": {
        "root": "<b>Настройки</b>\nЯзык: {lang} · Уведомления: {notif}",
        "notif": "<b>Уведомления</b>\nНажмите, чтобы включить или выключить.",
        "quiet": "<b>Тихие часы</b>\nБез звука с {start}:00 до 08:00. С какого часа?",
        "lang": "<b>Язык</b>",
        "privacy": "<b>Приватность</b>\nПоказывать моё имя в рейтинге недели: {shown}",
        "confirm_delete": "<b>Удалить все ваши данные?</b>\nЗаказы, адреса и настройки будут удалены. Оплаченные заказы останутся у магазина для учёта.",
        "deleting": "<b>Удаление через {sec} с</b>\nПередумали? Нажмите «Отменить».",
        "deleted": "<b>Ваши данные удалены.</b>\nОтправьте /start, чтобы начать заново.",
        "undone": "Удаление отменено. Ничего не удалено.",
        "too_late": "Поздно — данные уже удалены.",
        "group_hint": "Настройки личные, поэтому открываются в нашем личном чате.",
        "on": "вкл.", "off": "выкл.", "shown": "да", "hidden": "нет",
        "btn_lang": "Язык: {lang}",
        "btn_notif": "Уведомления",
        "btn_privacy": "Приватность",
        "btn_delete": "Удалить мои данные",
        "btn_delete_yes": "Удалить всё",
        "btn_cancel": "Отмена",
        "btn_undo": "Отменить",
        "btn_back": "← Назад",
        "btn_toggle": "{mark} {label}",
        "btn_quiet": "Тихие часы: с {start}:00",
        "btn_open_private": "Открыть настройки",
        "btn_start_again": "Начать заново",
        "t_shipping": "Статус доставки",
        "t_promos": "Акции и новости",
        "t_digest": "Дайджест недели",
        "sys_stale": "Экран изменился. Используйте последнее сообщение.",
        "sys_not_yours": "Это чужие настройки.",
        "sys_expired": "Меню устарело. Отправьте /settings.",
    },
}
I18N = f.I18n(COPY)
LANG_NAMES = {"en": "English", "ru": "Русский"}
TOGGLES = ("shipping", "promos", "digest")
DEFAULTS = {"shipping": True, "promos": False, "digest": True, "quiet": 22, "public": False}


class Settings:
    def __init__(self, t: FakeTransport):
        self.t = t
        self.flow = f.ScreenFlow(t, "st", i18n=I18N)
        self.jobs = f.Scheduler()
        self.deletions = f.OnceStore()
        self.deleted: set[int] = set()
        self.now = 0.0
        self._screens()

    @staticmethod
    def prefs(s: f.Session) -> dict:
        return s.data.setdefault("prefs", dict(DEFAULTS))

    def _screens(self) -> None:
        fl = self.flow
        back = lambda s: f.btn(fl.tr(s, "btn_back"), fl.cb(s, "back"))   # noqa: E731

        @fl.screen("root")
        def root(fl, s):
            p = self.prefs(s)
            on = sum(p[k] for k in TOGGLES)
            return {"text": fl.tr(s, "root", lang=LANG_NAMES[s.lang], notif=f"{on}/{len(TOGGLES)}"),
                    "reply_markup": f.kb(
                        [f.btn(fl.tr(s, "btn_lang", lang=LANG_NAMES[s.lang]), fl.cb(s, "go", "lang"))],
                        [f.btn(fl.tr(s, "btn_notif"), fl.cb(s, "go", "notif")),
                         f.btn(fl.tr(s, "btn_privacy"), fl.cb(s, "go", "privacy"))],
                        [f.btn(fl.tr(s, "btn_delete"), fl.cb(s, "go", "confirm_delete"), style="danger")])}

        @fl.screen("notif")
        def notif(fl, s):
            p = self.prefs(s)
            rows = [[f.btn(fl.tr(s, "btn_toggle", mark="✓" if p[k] else "✗", label=fl.tr(s, "t_" + k)),
                           fl.cb(s, "tog", k))] for k in TOGGLES]
            rows.append([f.btn(fl.tr(s, "btn_quiet", start=p["quiet"]), fl.cb(s, "go", "quiet"))])
            rows.append([back(s)])
            return {"text": fl.tr(s, "notif"), "reply_markup": f.kb(*rows)}

        @fl.screen("quiet")
        def quiet(fl, s):
            cur = self.prefs(s)["quiet"]
            hours = [f.btn(f"{h}:00", disabled=True) if h == cur else f.btn(f"{h}:00", fl.cb(s, "quiet", h))
                     for h in (20, 21, 22, 23)]
            return {"text": fl.tr(s, "quiet", start=cur), "reply_markup": f.kb(hours, [back(s)])}

        @fl.screen("lang")
        def lang(fl, s):
            rows = [[f.btn(("✓ " if code == s.lang else "") + name, fl.cb(s, "lang", code))]
                    for code, name in LANG_NAMES.items()]
            return {"text": fl.tr(s, "lang"), "reply_markup": f.kb(*rows, [back(s)])}

        @fl.screen("privacy")
        def privacy(fl, s):
            shown = self.prefs(s)["public"]
            return {"text": fl.tr(s, "privacy", shown=fl.tr(s, "shown" if shown else "hidden")),
                    "reply_markup": f.kb([f.btn(fl.tr(s, "btn_toggle", mark="✓" if shown else "✗",
                                                      label=fl.tr(s, "btn_privacy")), fl.cb(s, "tog", "public"))],
                                         [back(s)])}

        @fl.screen("confirm_delete")
        def confirm_delete(fl, s):
            # The destructive button is red AND not the first thing under the thumb;
            # Cancel is a plain, safe way out [heuristic].
            return {"text": fl.tr(s, "confirm_delete"), "reply_markup": f.kb(
                [f.btn(fl.tr(s, "btn_cancel"), fl.cb(s, "back"))],
                [f.btn(fl.tr(s, "btn_delete_yes"), fl.cb(s, "delete"), style="danger")])}

        @fl.screen("deleting")
        def deleting(fl, s):
            return {"text": fl.tr(s, "deleting", sec=UNDO_SECONDS),
                    "reply_markup": f.kb([f.btn(fl.tr(s, "btn_undo"), fl.cb(s, "undo"), style="primary")])}

        @fl.screen("deleted")
        def deleted(fl, s):
            return {"text": fl.tr(s, "deleted"), "reply_markup": f.kb(
                [f.btn(fl.tr(s, "btn_start_again"), url=f"https://t.me/{BOT}?start=new")])}

        @fl.action("go")
        def a_go(fl, s, args, cq):
            fl.go(s, args[0])

        @fl.action("back")
        def a_back(fl, s, args, cq):
            fl.back(s)

        @fl.action("tog")
        def a_toggle(fl, s, args, cq):
            if args[0] not in DEFAULTS or not isinstance(DEFAULTS[args[0]], bool):
                return "bad_toggle"
            p = self.prefs(s)
            p[args[0]] = not p[args[0]]
            fl.refresh(s)
            return f"{args[0]}={'on' if p[args[0]] else 'off'}"

        @fl.action("quiet")
        def a_quiet(fl, s, args, cq):
            self.prefs(s)["quiet"] = int(args[0])
            fl.back(s)                   # a picker returns to where it was opened from
            return "quiet_set"

        @fl.action("lang")
        def a_lang(fl, s, args, cq):
            if args[0] in COPY:
                s.lang = args[0]
            fl.back(s)                   # the parent re-renders in the new language
            return "lang_" + s.lang

        @fl.action("delete")
        def a_delete(fl, s, args, cq):
            def schedule():
                self.jobs.at(self.now + UNDO_SECONDS, f"del:{s.owner_id}", user=s.owner_id)
                return True
            _, first = self.deletions.run(f"del:{s.owner_id}:{s.data.get('del_round', 0)}", schedule)
            fl.open(s, "deleting")
            return "deletion_scheduled" if first else "deletion_already_scheduled"

        @fl.action("undo")
        def a_undo(fl, s, args, cq):
            if s.owner_id in self.deleted:
                fl.answer(cq, fl.tr(s, "too_late"), alert=True)
                return "too_late"
            self.jobs.cancel(f"del:{s.owner_id}")
            s.data["del_round"] = s.data.get("del_round", 0) + 1     # a later Delete is a new request
            fl.answer(cq, fl.tr(s, "undone"))
            fl.open(s, "root")
            return "undone"

    def tick(self, now: float) -> list[str]:
        self.now = now
        done = []
        for job in self.jobs.due(now):
            uid = job.payload["user"]
            s = self.flow.sessions[(uid, uid)]
            self.deleted.add(uid)
            lang, msg, ver = s.lang, s.message_id, s.version
            s.data.clear()               # your real deletion: DB rows, files, analytics ids
            s.lang = lang
            s.message_id, s.version = msg, ver
            self.flow.open(s, "deleted")
            done.append(f"deleted:{uid}")
        return done

    def on_command(self, msg: dict) -> str:
        frm, chat = msg["from"], msg["chat"]
        lang = I18N.lang_for(frm.get("language_code"))
        if chat["type"] != "private":
            # Personal settings never render in a group [heuristic: personal content keeps its audience].
            self.t.call("sendMessage", {"chat_id": chat["id"], "text": I18N.t(lang, "group_hint"),
                                        "reply_parameters": {"message_id": msg["message_id"]},
                                        "reply_markup": f.kb([f.btn(I18N.t(lang, "btn_open_private"),
                                                                    url=f"https://t.me/{BOT}?start=settings")])})
            return "group_redirect"
        s = self.flow.session(chat["id"], frm["id"], lang=lang)
        self.flow.open(s, "root", new_message=True)
        return "root"


def run(t: FakeTransport | None = None):
    t = t or FakeTransport()
    st = Settings(t)
    fl = st.flow
    n = [0]

    def tap(who, action, *args, old=False):
        s = fl.sessions[(who["id"], who["id"])]
        n[0] += 1
        data = f.pack("st", f.b36(s.version - (1 if old else 0)), action, *args)
        return fl.handle(f.callback(f"q{n[0]}", who, data, chat_id=who["id"], message_id=s.message_id))

    out = [st.on_command(f.text_message(BOGDAN, "/settings", chat_id=GROUP, chat_type="supergroup", message_id=9))]
    out.append(st.on_command(f.text_message(BOGDAN, "/settings")))
    out.append(tap(BOGDAN, "go", "notif"))
    out.append(tap(BOGDAN, "tog", "promos"))
    out.append(tap(BOGDAN, "tog", "promos", old=True))        # double tap: must not flip back
    out.append(tap(BOGDAN, "go", "quiet"))
    out.append(tap(BOGDAN, "quiet", 23))
    out.append(tap(BOGDAN, "back"))                             # notif -> root
    out.append(tap(BOGDAN, "go", "lang"))
    out.append(tap(BOGDAN, "lang", "en"))
    out.append(tap(BOGDAN, "go", "confirm_delete"))
    out.append(tap(BOGDAN, "back"))                             # Cancel
    out.append(tap(BOGDAN, "go", "confirm_delete"))
    out.append(tap(BOGDAN, "delete"))
    out.append(tap(BOGDAN, "undo"))
    out.append(tap(BOGDAN, "go", "confirm_delete"))
    out.append(tap(BOGDAN, "delete"))
    s = fl.sessions[(BOGDAN["id"],) * 2]
    undo_data = f.pack("st", f.b36(s.version), "undo")
    out.extend(st.tick(UNDO_SECONDS + 1))
    out.append(fl.handle(f.callback("q-late", BOGDAN, undo_data, chat_id=BOGDAN["id"], message_id=s.message_id)))
    # Alice tries Bogdan's settings message (crafted callback): refused.
    out.append(fl.handle(f.callback("q-alice", ALICE, f.pack("st", f.b36(s.version), "tog", "promos"),
                                    chat_id=BOGDAN["id"], message_id=s.message_id)))
    return t, st, out


def main() -> None:
    t, st, out = run()
    c.dump(t, "Settings")
    c.check(out[0] == "group_redirect", "/settings in a group links to the private chat, shows nothing personal")
    group_msg = t.params_of("sendMessage")[0]
    c.check(group_msg["reply_markup"]["inline_keyboard"][0][0]["url"].endswith("?start=settings"), "deep link")
    c.check(out[3:5] == ["promos=on", "stale"], "a double tap on a toggle can't flip it back")
    c.check(out[6:8] == ["quiet_set", "ok"], "a picker returns to its parent; Back walks the stack")
    c.check(out[9] == "lang_en", "language switch re-renders the parent in the new language")
    c.check(out[13:15] == ["deletion_scheduled", "undone"], "delete -> undo inside the window")
    c.check(out[16:18] == ["deletion_scheduled", f"deleted:{BOGDAN['id']}"], "second request runs after the window")
    c.check(out[18] in ("stale", "too_late"), "Undo after the deletion ran is refused")
    c.check(out[19] == "not_yours", "another user can't change these settings")
    confirm = next(p for m, p in t.calls if m == "editMessageText" and "Delete everything" in str(p.get("reply_markup")))
    rows = confirm["reply_markup"]["inline_keyboard"]
    c.check(rows[1][0]["style"] == "danger" and "style" not in rows[0][0], "danger on the destructive button only")


if __name__ == "__main__":
    if "--write-payload" in sys.argv:
        print(f.write_payload(f.payload_doc(PAYLOAD, run()[0], status=STATUS, context=CONTEXT)))
    else:
        main()
