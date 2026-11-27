"""R26 - Learning bot: course map -> lesson -> 3-question quiz -> result -> streak,
with a daily reminder that stays quiet when today's lesson is already done.

Invariants shown (offline, against fixtures and a scripted clock):
* one answer per question: a double tap on the old render is stale, and a crafted
  tap with the current version for an answered question is refused too;
* after an answer the chosen option is marked and EVERY option is disabled, the
  explanation appears (native sendPoll quizzes cannot explain per option);
* the streak counts days in the USER's time zone, resets after a missed day and
  is saved once per day even when two lessons are finished;
* the reminder is not sent when today's lesson is done or while it is muted.

Run:  py -3 examples/python/recipes/r26_learning.py [--write-payload]
"""
from __future__ import annotations

import calendar
import html
import sys

import _common as c
from tgkit import flows as f
from tgkit.rich import expandable_quote
from tgkit.transport import FakeTransport

PAYLOAD = "r26-learning"
STATUS = "production"
CONTEXT = "private"
ALICE = f.user(111111111, "Alice", "en")
OLENA = f.user(333333333, "Олена", "uk")
# The Bot API gives a bot no time zone for a user (only language_code): ask once and
# store it. Offsets here stand in for that stored setting (Kyiv in winter is UTC+2).
TZ = {111111111: 0, 333333333: 2 * 3600}
DAY = 86400
REMIND_HOUR = 18
MUTE_DAYS = 7

COPY = {
    "en": {
        "map_title": "Git basics",
        "map_streak": "Streak: {n} day(s) in a row",
        "map_hint": "Pick a lesson. Each one takes about two minutes.",
        "lesson_label": "Lesson {n}: {title}",
        "example_credit": "Example",
        "quiz_title": "Question {i} of {n}",
        "right": "Correct. {why}",
        "wrong": "Not quite. {why}",
        "result_title": "Result: {title}",
        "result_score": "{bar}  {score}/{total}",
        "result_streak": "Streak: {n} day(s) in a row",
        "reminder": "You haven't done today's lesson yet. Two minutes keep your streak alive.",
        "muted": "Reminders are paused for 7 days.",
        "btn_lesson": "{mark}{n} · {title}",
        "btn_start": "Start quiz",
        "btn_next": "Next question",
        "btn_finish": "See the result",
        "btn_map": "Course map",
        "btn_back": "← Back",
        "btn_next_lesson": "Next lesson",
        "btn_open": "Open the lesson",
        "btn_mute": "Mute for a week",
        "sys_stale": "This screen has changed. Use the latest message.",
        "sys_not_yours": "This lesson belongs to someone else. Open your own with /start.",
        "sys_expired": "This lesson has expired. Send /start to open it again.",
        "sys_answered": "You already answered this question.",
    },
    "uk": {
        "map_title": "Основи Git",
        "map_streak": "Серія: {n} дн. поспіль",
        "map_hint": "Оберіть урок. Кожен займає близько двох хвилин.",
        "lesson_label": "Урок {n}: {title}",
        "example_credit": "Приклад",
        "quiz_title": "Питання {i} з {n}",
        "right": "Правильно. {why}",
        "wrong": "Не зовсім. {why}",
        "result_title": "Результат: {title}",
        "result_score": "{bar}  {score}/{total}",
        "result_streak": "Серія: {n} дн. поспіль",
        "reminder": "Сьогоднішній урок ще не пройдено. Дві хвилини збережуть вашу серію.",
        "muted": "Нагадування вимкнено на 7 днів.",
        "btn_lesson": "{mark}{n} · {title}",
        "btn_start": "Почати тест",
        "btn_next": "Наступне питання",
        "btn_finish": "Показати результат",
        "btn_map": "Карта курсу",
        "btn_back": "← Назад",
        "btn_next_lesson": "Наступний урок",
        "btn_open": "Відкрити урок",
        "btn_mute": "Вимкнути на тиждень",
        "sys_stale": "Екран змінився. Користуйтеся останнім повідомленням.",
        "sys_not_yours": "Цей урок належить іншій людині. Відкрийте свій через /start.",
        "sys_expired": "Урок застарів. Надішліть /start.",
        "sys_answered": "Ви вже відповіли на це питання.",
    },
}
I18N = f.I18n(COPY)

# Lesson content is data, not UI copy. Every text is an (en, uk) pair.
LESSONS = {
    "commits": {
        "title": ("Commits", "Коміти"),
        "text": (("A commit is a saved snapshot of the project with a message that says why it changed.",
                  "Small, focused commits are easy to review and to undo."),
                 ("Коміт — це збережений знімок проєкту з повідомленням про те, чому він змінився.",
                  "Малі та зосереджені коміти легко перевіряти й скасовувати.")),
        "example": ("git add notes.txt\ngit commit -m \"Add shopping list\"\ngit log --oneline\n"
                    "The log prints one line per commit: a short id and its message.",
                    "git add notes.txt\ngit commit -m \"Add shopping list\"\ngit log --oneline\n"
                    "Журнал показує по рядку на коміт: короткий id і повідомлення."),
        "quiz": [
            {"q": ("What does a commit store?", "Що зберігає коміт?"), "ok": 0,
             "o": (("A snapshot with a message", "Only file names", "A copy of the server"),
                   ("Знімок із повідомленням", "Лише назви файлів", "Копію сервера")),
             "why": ("A commit is a snapshot plus the message that explains it.",
                     "Коміт — це знімок плюс повідомлення, що його пояснює.")},
            {"q": ("Which command records staged changes?", "Яка команда записує підготовлені зміни?"), "ok": 1,
             "o": (("git clone", "git commit", "git fetch"), ("git clone", "git commit", "git fetch")),
             "why": ("git commit records what git add staged.", "git commit записує те, що підготував git add.")},
            {"q": ("A good commit is…", "Хороший коміт…"), "ok": 2,
             "o": (("as large as possible", "without a message", "small and focused"),
                   ("якомога більший", "без повідомлення", "малий і зосереджений")),
             "why": ("Small commits are easier to review.", "Малі коміти легше перевіряти.")},
        ],
    },
    "branches": {
        "title": ("Branches", "Гілки"),
        "text": (("A branch is a movable pointer to a commit. Work on a branch never touches main.",
                  "Merge the branch when the work is ready."),
                 ("Гілка — це рухомий вказівник на коміт. Робота в гілці не чіпає main.",
                  "Зливайте гілку, коли робота готова.")),
        "example": ("git switch -c fix-typo\ngit commit -am \"Fix typo\"\ngit switch main\ngit merge fix-typo",
                    "git switch -c fix-typo\ngit commit -am \"Fix typo\"\ngit switch main\ngit merge fix-typo"),
        "quiz": [
            {"q": ("What is a branch?", "Що таке гілка?"), "ok": 1,
             "o": (("A copy of the disk", "A pointer to a commit", "A remote server"),
                   ("Копія диска", "Вказівник на коміт", "Віддалений сервер")),
             "why": ("A branch only points at a commit.", "Гілка лише вказує на коміт.")},
            {"q": ("Which command creates and opens a branch?", "Яка команда створює й відкриває гілку?"), "ok": 0,
             "o": (("git switch -c", "git merge", "git log"), ("git switch -c", "git merge", "git log")),
             "why": ("switch -c creates the branch and moves to it.", "switch -c створює гілку й переходить на неї.")},
            {"q": ("How do you bring finished work into main?", "Як додати готову роботу в main?"), "ok": 2,
             "o": (("Delete main", "git init", "git merge"), ("Видалити main", "git init", "git merge")),
             "why": ("Switch to main and merge the branch.", "Перейдіть на main і злийте гілку.")},
        ],
    },
}
ORDER = list(LESSONS)
LANG_IX = {"en": 0, "uk": 1}


def pick(pair, lang: str) -> str:
    return pair[LANG_IX[lang]]


def plain(lang: str, key: str, **values) -> str:
    """Rich text strings are plain text, not HTML: undo the HTML escaping of I18n."""
    return html.unescape(I18N.t(lang, key, **values))


class Course:
    def __init__(self, t: FakeTransport):
        self.t = t
        self.now = 0.0
        self.flow = f.ScreenFlow(t, "lr", i18n=I18N)
        self.sched = f.Scheduler()
        self.updates = f.UpdateDedup()
        self.log: list[dict] = []
        self._screens()

    # ---- time and streak ------------------------------------------------------
    def today(self, s: f.Session) -> int:
        return int(self.now + s.data["tz"]) // DAY

    def streak(self, s: f.Session) -> int:
        last = s.data.get("last_day")
        return s.data.get("streak", 0) if last is not None and self.today(s) - last <= 1 else 0

    def touch_streak(self, s: f.Session) -> None:
        today, last = self.today(s), s.data.get("last_day")
        if last == today:
            return                                    # one save per local day, however many lessons
        s.data["streak"] = s.data.get("streak", 0) + 1 if last == today - 1 else 1
        s.data["last_day"] = today

    def plan_reminder(self, s: f.Session) -> None:
        local = int(self.now + s.data["tz"])
        at = (local // DAY) * DAY + REMIND_HOUR * 3600 - s.data["tz"]
        self.sched.at(at if at > self.now else at + DAY, f"rem:{s.owner_id}", uid=s.owner_id)

    def tick(self, now: float) -> None:
        self.now = now
        for job in self.sched.due(now):
            s = self.flow.sessions[(job.payload["uid"], job.payload["uid"])]
            why = ("done" if s.data.get("last_day") == self.today(s)
                   else "muted" if s.data.get("muted_until", 0) > now
                   else "busy" if s.screen == "quiz" else None)
            self.log.append({"uid": s.owner_id, "reminder": why or "sent"})
            if why is None:
                self.flow.open(s, "reminder", new_message=True)
            self.plan_reminder(s)

    # ---- screens ----------------------------------------------------------------
    def _screens(self) -> None:
        fl = self.flow

        def head(text: str, size: int = 2) -> dict:
            return {"type": "heading", "size": size, "text": text}

        def para(text: str) -> dict:
            return {"type": "paragraph", "text": text}

        @fl.screen("map")
        def course_map(fl, s):
            done = s.data.get("done", {})
            items = [{"blocks": [para(pick(LESSONS[k]["title"], s.lang))], "has_checkbox": True,
                      **({"is_checked": True} if k in done else {})} for k in ORDER]
            rows = [[f.btn(fl.tr(s, "btn_lesson", mark="✓ " if k in done else "", n=i + 1,
                                 title=pick(LESSONS[k]["title"], s.lang)), fl.cb(s, "lesson", k))]
                    for i, k in enumerate(ORDER)]
            blocks = [head(plain(s.lang, "map_title")), para(plain(s.lang, "map_streak", n=self.streak(s))),
                      {"type": "list", "items": items}, para(plain(s.lang, "map_hint"))]
            return {"rich_message": {"blocks": blocks}, "reply_markup": f.kb(*rows)}

        @fl.screen("lesson")
        def lesson(fl, s):
            les = LESSONS[s.args["id"]]
            title = plain(s.lang, "lesson_label", n=ORDER.index(s.args["id"]) + 1, title=pick(les["title"], s.lang))
            blocks = [head(title), *[para(p) for p in pick(les["text"], s.lang)],
                      expandable_quote(pick(les["example"], s.lang), plain(s.lang, "example_credit"))]
            # "Start quiz" is the screen's main action: the keyboard, not a filled button at the end of the
            # document (references/rich-message-buttons.md §6)
            return {"rich_message": {"blocks": blocks},
                    "reply_markup": f.kb([f.btn(plain(s.lang, "btn_start"), fl.cb(s, "start"), style="primary")],
                                         [f.btn(fl.tr(s, "btn_back"), fl.cb(s, "back"))])}

        @fl.screen("quiz")
        def quiz(fl, s):
            qz = s.data["quiz"]
            q = LESSONS[qz["lesson"]]["quiz"][qz["q"]]
            total, chosen = len(LESSONS[qz["lesson"]]["quiz"]), qz["answers"].get(qz["q"])
            blocks = [head(plain(s.lang, "quiz_title", i=qz["q"] + 1, n=total)), para(pick(q["q"], s.lang))]
            rows = []
            for k, opt in enumerate(pick(q["o"], s.lang)):
                if chosen is None:
                    rows.append([f.btn(opt, fl.cb(s, "ans", qz["q"], k))])
                else:                                  # answered: mark the choice, disable everything
                    mark = "" if k != chosen else "✓ " if k == q["ok"] else "✗ "
                    rows.append([f.btn(mark + opt, disabled=True)])
            if chosen is not None:
                key = "right" if chosen == q["ok"] else "wrong"
                blocks.append(para(plain(s.lang, key, why=pick(q["why"], s.lang))))
                last = qz["q"] == total - 1
                rows.append([f.btn(fl.tr(s, "btn_finish" if last else "btn_next"), fl.cb(s, "next"), style="primary")])
            return {"rich_message": {"blocks": blocks}, "reply_markup": f.kb(*rows)}

        @fl.screen("result")
        def result(fl, s):
            qz = s.data["quiz"]
            total = len(LESSONS[qz["lesson"]]["quiz"])
            bar = "█" * qz["score"] + "░" * (total - qz["score"])
            blocks = [head(plain(s.lang, "result_title", title=pick(LESSONS[qz["lesson"]]["title"], s.lang))),
                      para(plain(s.lang, "result_score", bar=bar, score=qz["score"], total=total)),
                      para(plain(s.lang, "result_streak", n=self.streak(s)))]
            return {"rich_message": {"blocks": blocks},
                    "reply_markup": f.kb([f.btn(fl.tr(s, "btn_next_lesson"), fl.cb(s, "next_lesson"), style="primary")],
                                         [f.btn(fl.tr(s, "btn_map"), fl.cb(s, "map"))])}

        @fl.screen("reminder")
        def reminder(fl, s):
            return {"rich_message": {"blocks": [para(plain(s.lang, "reminder"))]},
                    "reply_markup": f.kb([f.btn(fl.tr(s, "btn_open"), fl.cb(s, "next_lesson"), style="primary")],
                                         [f.btn(fl.tr(s, "btn_mute"), fl.cb(s, "mute"))])}

        def next_lesson_id(s):
            return next((k for k in ORDER if k not in s.data.get("done", {})), ORDER[0])

        @fl.action("lesson")
        def a_lesson(fl, s, args, cq):
            fl.go(s, "lesson", id=args[0])

        @fl.action("start")
        def a_start(fl, s, args, cq):
            s.data["quiz"] = {"lesson": s.args["id"], "q": 0, "answers": {}, "score": 0}
            fl.go(s, "quiz")

        @fl.action("ans")
        def a_ans(fl, s, args, cq):
            qz, q, k = s.data["quiz"], int(args[0]), int(args[1])
            if q in qz["answers"]:                     # current version, but already answered
                fl.answer(cq, fl.i18n.t(s.lang, "sys_answered"))
                return "already_answered"
            if q != qz["q"]:
                return "stale"
            qz["answers"][q] = k
            qz["score"] += k == LESSONS[qz["lesson"]]["quiz"][q]["ok"]
            fl.refresh(s)

        @fl.action("next")
        def a_next(fl, s, args, cq):
            qz = s.data["quiz"]
            if qz["q"] < len(LESSONS[qz["lesson"]]["quiz"]) - 1:
                qz["q"] += 1
                fl.refresh(s)
                return
            s.data.setdefault("done", {})[qz["lesson"]] = max(qz["score"], s.data.get("done", {}).get(qz["lesson"], 0))
            self.touch_streak(s)
            fl.go(s, "result")

        @fl.action("back")
        def a_back(fl, s, args, cq):
            fl.back(s) if s.stack else fl.open(s, "map")

        @fl.action("map")
        def a_map(fl, s, args, cq):
            fl.open(s, "map")

        @fl.action("next_lesson")
        def a_next_lesson(fl, s, args, cq):
            fl.open(s, "lesson", id=next_lesson_id(s))

        @fl.action("mute")
        def a_mute(fl, s, args, cq):
            s.data["muted_until"] = self.now + MUTE_DAYS * DAY
            fl.answer(cq, fl.i18n.t(s.lang, "muted"))
            fl.open(s, "map")

    def dispatch(self, update: dict) -> str:
        if not self.updates.first_time(update):
            return "duplicate_update"
        if "callback_query" in update:
            return self.flow.handle(update["callback_query"])
        msg = update["message"]
        s = self.flow.session(msg["chat"]["id"], msg["from"]["id"],
                              lang=I18N.lang_for(msg["from"].get("language_code")))
        s.data.setdefault("tz", TZ.get(msg["from"]["id"], 0))
        self.plan_reminder(s)
        self.flow.open(s, "map", new_message=True)
        return "map"


def run(t: FakeTransport | None = None):
    t = t or FakeTransport()
    app = Course(t)
    fl = app.flow
    uid = [0]
    d1 = calendar.timegm((2026, 11, 16, 0, 0, 0))

    def tap(who: dict, action: str, *args, offset: int = 0) -> str:
        s = fl.sessions[(who["id"], who["id"])]
        uid[0] += 1
        cq = f.callback(f"cq{uid[0]}", who, f.pack("lr", f.b36(s.version - offset), action, *args),
                        chat_id=who["id"], message_id=s.message_id)
        return app.dispatch({"update_id": 1000 + uid[0], "callback_query": cq})

    def start(who: dict) -> str:
        uid[0] += 1
        if who is OLENA:
            return app.dispatch(c.fixture("usecase_learning_start.json"))
        return app.dispatch({"update_id": 500 + uid[0], "message": f.text_message(who, "/start")})

    def take(who: dict, lesson: str, picks: list[int], extra: bool = False) -> list[str]:
        out = [tap(who, "lesson", lesson), tap(who, "start")]
        for q, k in enumerate(picks):
            out.append(tap(who, "ans", q, k))
            if extra and q == 0:
                out.append(tap(who, "ans", q, k, offset=1))      # double tap on the old render
                out.append(tap(who, "ans", q, 2))                  # current version, answered question
            out.append(tap(who, "next"))
        return out

    log: dict[str, object] = {}
    app.tick(d1 + 9 * 3600)
    start(ALICE)
    log["alice1"] = take(ALICE, "commits", [0, 0, 2], extra=True)          # 2 of 3
    a = fl.sessions[(ALICE["id"], ALICE["id"])]
    log["alice_streak1"] = app.streak(a)
    log["alice2"] = take(ALICE, "branches", [1, 0, 2])                    # same day, second lesson
    log["alice_streak2"] = app.streak(a)
    app.tick(d1 + 18 * 3600)                                               # done today: no reminder
    app.tick(d1 + DAY + 18 * 3600)                                         # nothing done today: reminder
    tap(ALICE, "mute")
    app.tick(d1 + 2 * DAY + 18 * 3600)                                     # muted
    # Olena (UTC+2): 23:30 and 00:30 local fall on the same UTC day but on two local days.
    app.now = d1 + 21 * 3600 + 1800
    start(OLENA)
    log["olena1"] = take(OLENA, "commits", [0, 1, 2])
    app.now = d1 + 22 * 3600 + 1800
    log["olena2"] = take(OLENA, "branches", [1, 0, 2])
    o = fl.sessions[(OLENA["id"], OLENA["id"])]
    log["olena_streak"] = app.streak(o)
    # Alice returns on day 5 after missing days 2-4: the streak restarts.
    app.now = d1 + 4 * DAY + 10 * 3600
    start(ALICE)
    log["alice3"] = take(ALICE, "commits", [0, 1, 2])
    log["alice_streak3"] = app.streak(a)
    # Olena taps a button of Alice's menu message.
    stranger = f.callback("cqx", OLENA, f.pack("lr", f.b36(a.version), "map"), chat_id=ALICE["id"],
                          message_id=a.message_id)
    log["stranger"] = app.dispatch({"update_id": 7, "callback_query": stranger})
    return t, app, log


def main() -> None:
    t, app, log = run()
    c.dump(t, "Learning bot")
    a1 = log["alice1"]
    c.check(a1[2] == "ok" and a1[3] == "stale" and a1[4] == "already_answered",
            "double tap on the old render is stale; crafted answer for an answered question is refused")
    lesson_sends = [p for p in t.params_of("sendRichMessage")]
    rich = lesson_sends[0]["rich_message"]["blocks"]
    c.check(any(b["type"] == "list" and b["items"][0].get("has_checkbox") for b in rich),
            "course map is a checklist (list items with has_checkbox)")
    edits = [p for p in t.params_of("editMessageText") if "rich_message" in p]
    lesson = next(p for p in edits if any(b["type"] == "expandable_blockquote" for b in p["rich_message"]["blocks"]))
    c.check(not any(b["type"] == "buttons" for b in lesson["rich_message"]["blocks"])
            and lesson["reply_markup"]["inline_keyboard"][0][0].get("style") == "primary",
            "lesson: expandable quote for the long example; Start quiz on the keyboard, not in the document")
    answered = next(p for p in edits if p["reply_markup"]["inline_keyboard"][0][0].get("disabled") is not None)
    labels = [r[0]["text"] for r in answered["reply_markup"]["inline_keyboard"][:3]]
    c.check(labels[0].startswith("✓ ") and all("disabled" in r[0] for r in answered["reply_markup"]["inline_keyboard"][:3]),
            "after an answer the chosen option is marked and every option is disabled")
    c.check(any("2/3" in str(p) and "██░" in str(p) for p in edits), "result screen shows a progress bar and the score")
    c.check(log["alice_streak1"] == 1 and log["alice_streak2"] == 1,
            "a second lesson on the same day does not change the streak")
    c.check(log["olena_streak"] == 2, "streak days follow the user's time zone (23:30 and 00:30 local)")
    c.check(app.log[:3] == [{"uid": 111111111, "reminder": "done"}, {"uid": 111111111, "reminder": "sent"},
                            {"uid": 111111111, "reminder": "muted"}],
            "reminder: skipped when today's lesson is done, sent otherwise, skipped while muted")
    c.check(log["alice_streak3"] == 1, "a missed day resets the streak")
    c.check(log["stranger"] == "not_yours", "another user's tap on Alice's lesson is refused")
    c.check(any("Серія" in str(p) for p in edits), "the same screens render in Ukrainian for a Ukrainian user")


if __name__ == "__main__":
    if "--write-payload" in sys.argv:
        print(f.write_payload(f.payload_doc(PAYLOAD, run()[0], status=STATUS, context=CONTEXT)))
    else:
        main()
