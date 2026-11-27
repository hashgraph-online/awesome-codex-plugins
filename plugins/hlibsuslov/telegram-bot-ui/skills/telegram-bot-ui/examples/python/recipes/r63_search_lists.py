"""R63 - Search and long lists: a job board.

Query (typed behind force_reply, or a recent one) -> filters -> paginated results
(5 per page) -> detail -> Back to the SAME page; a compact Rich table to compare.

Invariants shown (offline, against fixtures):
* the query lives on the server; callback_data carries a short id and a snapshot
  version, so a Cyrillic query can never overflow the 64-byte limit;
* the data changes while the user pages: a page button from an older snapshot is
  refused, the list is re-rendered; a job that disappeared is a toast, not an error;
* an empty result says why and offers one-tap "Remove filter" buttons that would help;
* more than MAX_BROWSE results: no pager, the top 5 and facet buttons to narrow down;
* titles are clipped BEFORE escaping, so an HTML entity is never cut in half;
* Back from a detail returns to the same page with the same filters.

Run:  py -3 examples/python/recipes/r63_search_lists.py [--write-payload]
"""
from __future__ import annotations

import re
import sys

import _common as c
from tgkit import flows as f
from tgkit.rich import table
from tgkit.transport import FakeTransport

PAYLOAD = "r63-search-lists"
STATUS = "production"
CONTEXT = "private"
PAGE, MAX_BROWSE, TITLE_MAX = 5, 200, 44
ALICE = f.user(111111111, "Alice", "en")
OLENA = f.user(333333333, "Олена", "uk")
FILTERS = ("remote", "junior", "senior")

COPY = {
    "en": {
        "home": "<b>Job search</b>\nType a role, a skill or a city, or pick a recent search.",
        "ask": "What are you looking for? Reply with a role, a skill or a city (up to 64 characters).",
        "err_query": "Please send 1-64 characters, for example: python.",
        "results": "<b>«{q}»</b> · {n} jobs · page {page}/{pages}{flt}\n\n{items}",
        "too_many": "<b>«{q}» · {n} jobs</b>\nToo many to browse. Narrow it down; the top {k} for now:\n\n{items}",
        "flt_line": "\nFilters: {names}",
        "item": "{n}. <b>{title}</b>\n    {city} · {level}{remote}",
        "remote_tag": " · remote",
        "empty": "<b>Nothing for «{q}»</b>\n{why}",
        "why_filters": "No job matches with these filters: {names}. Remove one to see more:",
        "why_query": "No job matches this word at all. Check the spelling or try a broader one.",
        "filters": "<b>Filters</b>\nPick what to keep, then apply.",
        "detail": "<b>{title}</b>\n{company}\n{city} · {level}{remote}\nSalary: {salary}\n\n{summary}",
        "cmp_title": "Compare · page {page}/{pages}",
        "col_job": "Job",
        "col_city": "City",
        "col_level": "Level",
        "col_pay": "Salary",
        "lvl_junior": "Junior",
        "lvl_middle": "Middle",
        "lvl_senior": "Senior",
        "f_remote": "Remote",
        "f_junior": "Junior",
        "f_senior": "Senior",
        "toast_changed": "The list was updated. Showing the latest results.",
        "toast_gone": "This job is no longer available.",
        "btn_new": "New search",
        "btn_filters": "Filters",
        "btn_filters_n": "Filters ({n})",
        "btn_compare": "Compare",
        "btn_apply": "Apply · {n}",
        "btn_reset": "Reset",
        "btn_back": "← Back",
        "btn_open": "Open vacancy",
        "btn_list": "← List",
        "btn_remove": "Remove filter: {name}",
        "btn_facet": "{name} ({n})",
        "btn_recent": "🕘 {q}",
        "sys_stale": "This list has changed. Use the latest message.",
        "sys_not_yours": "This search belongs to someone else. Send /start for your own.",
        "sys_expired": "This search has expired. Send /start.",
    },
    "uk": {
        "home": "<b>Пошук роботи</b>\nНапишіть посаду, навичку чи місто або оберіть недавній пошук.",
        "ask": "Що шукаєте? Відповідьте посадою, навичкою чи містом (до 64 символів).",
        "err_query": "Надішліть від 1 до 64 символів, наприклад: python.",
        "results": "<b>«{q}»</b> · вакансій: {n} · сторінка {page}/{pages}{flt}\n\n{items}",
        "too_many": "<b>«{q}» · вакансій: {n}</b>\nЗанадто багато. Звузьте пошук; поки що топ {k}:\n\n{items}",
        "flt_line": "\nФільтри: {names}",
        "item": "{n}. <b>{title}</b>\n    {city} · {level}{remote}",
        "remote_tag": " · віддалено",
        "empty": "<b>Нічого за «{q}»</b>\n{why}",
        "why_filters": "З цими фільтрами нічого немає: {names}. Приберіть один, щоб побачити більше:",
        "why_query": "За цим словом вакансій немає взагалі. Перевірте написання або спробуйте ширше слово.",
        "filters": "<b>Фільтри</b>\nОберіть, що залишити, і застосуйте.",
        "detail": "<b>{title}</b>\n{company}\n{city} · {level}{remote}\nЗарплата: {salary}\n\n{summary}",
        "cmp_title": "Порівняння · сторінка {page}/{pages}",
        "col_job": "Вакансія",
        "col_city": "Місто",
        "col_level": "Рівень",
        "col_pay": "Зарплата",
        "lvl_junior": "Junior",
        "lvl_middle": "Middle",
        "lvl_senior": "Senior",
        "f_remote": "Віддалено",
        "f_junior": "Junior",
        "f_senior": "Senior",
        "toast_changed": "Список оновився. Показую свіжі результати.",
        "toast_gone": "Ця вакансія вже недоступна.",
        "btn_new": "Новий пошук",
        "btn_filters": "Фільтри",
        "btn_filters_n": "Фільтри ({n})",
        "btn_compare": "Порівняти",
        "btn_apply": "Застосувати · {n}",
        "btn_reset": "Скинути",
        "btn_back": "← Назад",
        "btn_open": "Відкрити вакансію",
        "btn_list": "← Список",
        "btn_remove": "Прибрати: {name}",
        "btn_facet": "{name} ({n})",
        "btn_recent": "🕘 {q}",
        "sys_stale": "Список змінився. Користуйтеся останнім повідомленням.",
        "sys_not_yours": "Цей пошук належить комусь іншому. Надішліть /start.",
        "sys_expired": "Пошук застарів. Надішліть /start.",
    },
}
I18N = f.I18n(COPY)


def clip(text: str, limit: int = TITLE_MAX) -> str:
    """Cut RAW text, then let the template escape it: an entity is never split."""
    return text if len(text) <= limit else text[:limit - 1].rstrip() + "…"


class JobBoard:
    def __init__(self, t: FakeTransport, jobs: list[dict]):
        self.t = t
        self.jobs = {j["id"]: j for j in jobs}
        self.version = 1                          # snapshot version of the catalog
        self.queries: dict[str, str] = {}         # id -> text; only the id goes into callback_data
        self.flow = f.ScreenFlow(t, "sr", i18n=I18N)
        self.updates = f.UpdateDedup()
        self._screens()

    # ---- data ------------------------------------------------------------------
    def search(self, q: str, filt: set[str]) -> list[str]:
        words, levels = q.lower().split(), filt & {"junior", "senior"}
        return [j["id"] for j in self.jobs.values()
                if all(w in f"{j['title']} {j['city']}".lower() for w in words)
                and (j["remote"] or "remote" not in filt) and (not levels or j["level"] in levels)]

    def change_data(self, remove: str, add: dict) -> None:
        self.jobs.pop(remove, None)
        self.jobs[add["id"]] = add
        self.version += 1

    def add_bulk(self, count: int) -> None:
        for i in range(count):
            self.jobs[f"b{i}"] = {"id": f"b{i}", "title": f"Support specialist #{i}", "company": "Contoso",
                                  "city": ("Berlin", "Kyiv", "Lviv")[i % 3], "level": ("junior", "middle", "senior")[i % 3],
                                  "remote": i % 2 == 0, "salary": "€1.5k", "summary": "Chat and email support."}
        self.version += 1

    def query_id(self, text: str) -> str:
        for qid, known in self.queries.items():
            if known.lower() == text.lower():
                return qid
        qid = f"q{len(self.queries) + 1}"
        self.queries[qid] = text
        return qid

    def state(self, s: f.Session) -> tuple[str, set[str]]:
        return self.queries[s.data["q"]], s.data.setdefault("filters", set())

    def names(self, s: f.Session, keys) -> str:
        return ", ".join(self.flow.tr(s, f"f_{k}") for k in FILTERS if k in keys)

    def items_text(self, s: f.Session, ids: list[str], start: int = 1) -> f.Raw:
        lines = [self.flow.tr(s, "item", n=start + i, title=clip(self.jobs[j]["title"]), city=self.jobs[j]["city"],
                              level=self.flow.tr(s, f"lvl_{self.jobs[j]['level']}"),
                              remote=f.Raw(self.flow.tr(s, "remote_tag") if self.jobs[j]["remote"] else ""))
                 for i, j in enumerate(ids)]
        return f.Raw("\n".join(lines))

    # ---- screens ----------------------------------------------------------------------
    def _screens(self) -> None:
        fl = self.flow

        @fl.screen("home")
        def home(fl, s):
            recent = [[f.btn(fl.tr(s, "btn_recent", q=clip(self.queries[qid], 28)), fl.cb(s, "recent", qid))]
                      for qid in s.data.get("recent", [])]
            return {"text": fl.tr(s, "home"), "reply_markup": f.kb(*recent, [f.btn(fl.tr(s, "btn_new"), fl.cb(s, "new"), style="primary")])}

        @fl.screen("ask")
        def ask(fl, s):                           # force_reply is fixed for a message: a NEW message
            return {"text": fl.tr(s, "ask"),
                    "reply_markup": f.kb([f.btn(fl.tr(s, "btn_back"), fl.cb(s, "home"))], force_reply=True)}

        @fl.screen("results")
        def results(fl, s):
            q, filt = self.state(s)
            ids, snap = self.search(q, filt), f.b36(self.version)
            filters_btn = f.btn(fl.tr(s, "btn_filters_n", n=len(filt)) if filt else fl.tr(s, "btn_filters"), fl.cb(s, "filters"))
            new_btn = f.btn(fl.tr(s, "btn_new"), fl.cb(s, "new"))
            if not ids:
                helpful = [k for k in FILTERS if k in filt and self.search(q, filt - {k})]
                why = (fl.tr(s, "why_filters", names=self.names(s, filt)) if filt and helpful else fl.tr(s, "why_query"))
                rows = [[f.btn(fl.tr(s, "btn_remove", name=fl.tr(s, f"f_{k}")), fl.cb(s, "unfilter", k),
                               style="primary" if i == 0 else None)] for i, k in enumerate(helpful)]
                return {"text": fl.tr(s, "empty", q=q, why=f.Raw(why)), "reply_markup": f.kb(*rows, [new_btn])}
            if len(ids) > MAX_BROWSE:             # do not page through hundreds: ask to narrow down
                facets = [[f.btn(fl.tr(s, "btn_facet", name=fl.tr(s, f"f_{k}"), n=len(self.search(q, filt | {k}))), fl.cb(s, "facet", k))]
                          for k in FILTERS if k not in filt]
                return {"text": fl.tr(s, "too_many", q=q, n=len(ids), k=PAGE, items=self.items_text(s, ids[:PAGE])),
                        "reply_markup": f.kb(*facets, [new_btn])}
            part, page, pages = f.paginate(ids, s.args.get("page", 0), PAGE)
            s.args["page"] = page
            flt = f.Raw(fl.tr(s, "flt_line", names=self.names(s, filt)) if filt else "")
            numbers = [f.btn(str(page * PAGE + i + 1), fl.cb(s, "open", j)) for i, j in enumerate(part)]
            return {"text": fl.tr(s, "results", q=q, n=len(ids), page=page + 1, pages=pages, flt=flt,
                                  items=self.items_text(s, part, page * PAGE + 1)),
                    "reply_markup": f.kb(numbers, f.pager_row(fl, s, page, pages, "page", snap),
                                         [filters_btn, f.btn(fl.tr(s, "btn_compare"), fl.cb(s, "compare"))], [new_btn])}

        @fl.screen("filters")
        def filters(fl, s):
            q, filt = self.state(s)
            n = len(self.search(q, filt))
            rows = [[f.btn(("✓ " if k in filt else "") + fl.tr(s, f"f_{k}"), fl.cb(s, "toggle", k))] for k in FILTERS]
            apply_btn = (f.btn(fl.tr(s, "btn_apply", n=n), fl.cb(s, "apply"), style="primary") if n
                         else f.btn(fl.tr(s, "btn_apply", n=0), disabled=True))
            return {"text": fl.tr(s, "filters"), "reply_markup": f.kb(
                *rows, [apply_btn, f.btn(fl.tr(s, "btn_reset"), fl.cb(s, "reset"))])}

        @fl.screen("detail")
        def detail(fl, s):
            j = self.jobs[s.args["job"]]
            text = fl.tr(s, "detail", title=clip(j["title"], 200), company=j["company"], city=j["city"],
                         level=fl.tr(s, f"lvl_{j['level']}"), salary=j["salary"], summary=j["summary"],
                         remote=f.Raw(fl.tr(s, "remote_tag") if j["remote"] else ""))
            return {"text": text, "reply_markup": f.kb(
                [f.btn(fl.tr(s, "btn_open"), url=f"https://jobs.example/{j['id']}")], [f.btn(fl.tr(s, "btn_back"), fl.cb(s, "back"))])}

        @fl.screen("compare")
        def compare(fl, s):
            q, filt = self.state(s)
            part, page, pages = f.paginate(self.search(q, filt), s.args.get("page", 0), PAGE)
            rows = [[clip(self.jobs[j]["title"], 36), self.jobs[j]["city"], fl.tr(s, f"lvl_{self.jobs[j]['level']}"),
                     self.jobs[j]["salary"]] for j in part]
            return {"rich_message": {"blocks": [
                {"type": "heading", "size": 2, "text": fl.tr(s, "cmp_title", page=page + 1, pages=pages)},
                table([fl.tr(s, k) for k in ("col_job", "col_city", "col_level", "col_pay")], rows, compact=True)]},
                # navigation is the keyboard, not a button in the document (references/rich-message-buttons.md)
                "reply_markup": f.kb([f.btn(fl.tr(s, "btn_list"), fl.cb(s, "back"))])}

        # ---- actions
        @fl.action("new")
        def a_new(fl, s, args, cq):
            fl.open(s, "ask", new_message=True)

        @fl.action("home")
        def a_home(fl, s, args, cq):
            fl.open(s, "home", new_message=True)

        @fl.action("recent")
        def a_recent(fl, s, args, cq):
            if args[0] in self.queries:
                s.data["q"] = args[0]
                fl.open(s, "results", page=0)

        @fl.action("filters")
        def a_filters(fl, s, args, cq):
            fl.go(s, "filters")

        @fl.action("toggle")
        def a_toggle(fl, s, args, cq):
            if args[0] in FILTERS:
                s.data.setdefault("filters", set()).symmetric_difference_update({args[0]})
                fl.refresh(s)

        @fl.action("reset")
        def a_reset(fl, s, args, cq):
            s.data["filters"] = set()
            fl.refresh(s)

        @fl.action("apply")
        def a_apply(fl, s, args, cq):
            fl.open(s, "results", page=0)

        @fl.action("unfilter")
        def a_unfilter(fl, s, args, cq):
            s.data["filters"].discard(args[0])
            fl.open(s, "results", page=0)

        @fl.action("facet")
        def a_facet(fl, s, args, cq):
            if args[0] in FILTERS:
                s.data["filters"].add(args[0])
                fl.open(s, "results", page=0)

        @fl.action("page")
        def a_page(fl, s, args, cq):
            page, snap = int(args[0]), args[1]
            if snap != f.b36(self.version):       # the catalog changed after this page was rendered
                fl.answer(cq, fl.tr(s, "toast_changed"))
                s.args["page"] = page
                fl.refresh(s)                     # re-render from the new snapshot, page clamped
                return "snapshot_stale"
            s.args["page"] = page
            fl.refresh(s)

        @fl.action("open")
        def a_open(fl, s, args, cq):
            if args[0] not in self.jobs:
                fl.answer(cq, fl.tr(s, "toast_gone"), alert=True)
                fl.refresh(s)
                return "job_gone"
            fl.go(s, "detail", job=args[0])

        @fl.action("compare")
        def a_compare(fl, s, args, cq):
            fl.go(s, "compare", page=s.args.get("page", 0))

        @fl.action("back")
        def a_back(fl, s, args, cq):
            fl.back(s)                            # the stack holds the results screen WITH its page

    # ---- text ----------------------------------------------------------------------------------
    def on_text(self, msg: dict) -> str:
        uid, chat, text = msg["from"]["id"], msg["chat"]["id"], (msg.get("text") or "").strip()
        s = self.flow.session(chat, uid, lang=I18N.lang_for(msg["from"].get("language_code")))
        if text.startswith("/start"):
            self.flow.open(s, "home", new_message=True)
            return "home"
        if s.screen != "ask" or (msg.get("reply_to_message") or {}).get("message_id") != s.message_id:
            return "ignored"
        if not 1 <= len(text) <= 64:              # error on the same step: the prompt stays live
            self.t.call("sendMessage", {"chat_id": chat, "text": I18N.t(s.lang, "err_query"),
                                        "reply_parameters": {"message_id": s.message_id}})
            return "invalid"
        qid = self.query_id(text)
        s.data["q"] = qid
        s.data["recent"] = [qid, *[x for x in s.data.get("recent", []) if x != qid]][:3]
        self.flow.open(s, "results", new_message=True, page=0)
        return "searched"

    def dispatch(self, update: dict) -> str:
        if not self.updates.first_time(update):
            return "duplicate_update"
        if "callback_query" in update:
            return self.flow.handle(update["callback_query"])
        return self.on_text(update["message"])


def run(t: FakeTransport | None = None):
    t = t or FakeTransport()
    feed = c.fixture("usecase_search_jobs.json")
    bot = JobBoard(t, feed["jobs"])
    n = [0]

    def upd(**kw) -> dict:
        n[0] += 1
        return {"update_id": 964000 + n[0], **kw}

    def sess(who: dict) -> f.Session:
        return bot.flow.sessions[(who["id"], who["id"])]

    def tap(who: dict, action: str, *args, v: int = 0) -> str:
        s = sess(who)
        data = f.pack("sr", f.b36(s.version - v), action, *args)
        return bot.dispatch(upd(callback_query=f.callback(f"q{n[0]}", who, data, chat_id=who["id"], message_id=s.message_id)))

    def say(who: dict, text: str) -> str:
        s = bot.flow.sessions.get((who["id"], who["id"]))
        reply = s.message_id if s and s.screen == "ask" else None
        return bot.dispatch(upd(message=f.text_message(who, text, reply_to=reply)))

    def search(who: dict, text: str) -> str:
        tap(who, "new")
        return say(who, text)

    def last_markup(who: dict) -> list:
        return bot.flow._params(sess(who))["reply_markup"]["inline_keyboard"]

    out: dict = {"home": say(ALICE, "/start")}
    out["bad_query"] = (search(ALICE, "x" * 100), say(ALICE, "engineer"))             # same step, then ok
    out["pager_first"] = last_markup(ALICE)[1]
    tap(ALICE, "page", 1, f.b36(bot.version))
    tap(ALICE, "page", 2, f.b36(bot.version))
    out["pager_last"] = last_markup(ALICE)[1]
    tap(ALICE, "page", 1, f.b36(bot.version))
    out["detail"] = tap(ALICE, "open", "j6")                                           # the long title
    out["detail_text"] = bot.flow._params(sess(ALICE))["text"]
    tap(ALICE, "back")
    out["back_page"] = (sess(ALICE).screen, sess(ALICE).args["page"])
    tap(ALICE, "filters")
    tap(ALICE, "toggle", "remote")
    tap(ALICE, "toggle", "senior")
    tap(ALICE, "apply")                                                                 # sticky filters
    out["filtered"] = len(bot.search("engineer", sess(ALICE).data["filters"]))
    tap(ALICE, "compare")
    out["compare"] = sess(ALICE).screen
    tap(ALICE, "back")
    out["empty"] = search(ALICE, "embedded")                                            # Embedded is on-site
    out["empty_buttons"] = [b["text"] for row in last_markup(ALICE) for b in row]
    out["unfilter"] = tap(ALICE, "unfilter", "remote")
    out["after_unfilter"] = bot.search("embedded", sess(ALICE).data["filters"])
    tap(ALICE, "filters")
    tap(ALICE, "reset")
    tap(ALICE, "apply")
    out["olena_start"] = say(OLENA, "/start")
    out["cyr"] = search(OLENA, "інженер")
    out["cyr_buttons"] = [b for row in last_markup(OLENA) for b in row]
    say(OLENA, "/start")                                                                # home lists the recent query
    out["cyr_buttons"] += [b for row in last_markup(OLENA) for b in row]
    out["stranger"] = bot.dispatch(upd(callback_query=f.callback("qx", OLENA, f.pack("sr", f.b36(sess(ALICE).version), "reset"),
                                                                  chat_id=ALICE["id"], message_id=sess(ALICE).message_id)))
    out["crafted_stale"] = tap(ALICE, "new", v=2)
    search(ALICE, "engineer")
    bot.change_data("j3", {"id": "j17", "title": "Platform Engineer", "company": "Litware", "city": "Gdańsk",
                           "level": "middle", "remote": True, "salary": "€5k", "summary": "Internal developer platform."})
    out["gone"] = tap(ALICE, "open", "j3")                                              # removed after the render
    out["snapshot"] = tap(ALICE, "page", 1, f.b36(1))                                   # a button of snapshot 1
    out["pages_after"] = sess(ALICE).args["page"]
    bot.add_bulk(230)
    out["many"] = search(ALICE, "support")
    out["many_rows"] = last_markup(ALICE)
    out["many_text"] = bot.flow._params(sess(ALICE))["text"]
    out["facet"] = tap(ALICE, "facet", "remote")
    out["narrowed"] = last_markup(ALICE)
    return t, bot, out


def main() -> None:
    t, bot, o = run()
    c.dump(t, "Search")
    c.check(o["bad_query"] == ("invalid", "searched") and o["home"] == "home",
            "a 100-character query is refused on the same step, a normal one searches")
    first, last = o["pager_first"], o["pager_last"]
    c.check(first[0].get("disabled") == {} and first[1]["text"] == "1/3" and first[1].get("disabled") == {} and "callback_data" in first[2]
            and last[1]["text"] == "3/3" and "callback_data" in last[0] and last[2].get("disabled") == {},
            "5 per page: ← and the counter are disabled on page 1, → on the last page")
    c.check(o["back_page"] == ("results", 1) and "Search &amp; Ranking &lt;Core&gt;" in o["detail_text"],
            "detail -> Back returns to the same page; HTML in a title is escaped")
    c.check(o["filtered"] == 4 and o["compare"] == "compare" and len(t.params_of("sendRichMessage")) >= 1
            and t.params_of("sendRichMessage")[0]["rich_message"]["blocks"][1]["is_compact"],
            "filters narrow 12 -> 4; Compare is a Rich message with a compact table")
    c.check(any(b == "Remove filter: Remote" for b in o["empty_buttons"]) and o["after_unfilter"] == ["j8"]
            and not any("Senior" in b for b in o["empty_buttons"]),
            "empty result: only the filter whose removal helps is offered, one tap")
    data = [b["callback_data"] for b in o["cyr_buttons"] if "callback_data" in b]
    c.check(all(len(d.encode()) <= 64 for d in data) and not any("інженер" in d for d in data)
            and "інженер" in bot.queries.values(), "Cyrillic query stays on the server; callback_data is an id")
    c.check(o["gone"] == "job_gone" and o["snapshot"] == "snapshot_stale" and o["pages_after"] == 1,
            "removed job -> toast; an older snapshot's page button is refused and the list re-rendered")
    c.check(o["many"] == "searched" and not any("callback_data" in b and ":page:" in b["callback_data"] for r in o["many_rows"] for b in r)
            and any("(" in b["text"] for r in o["many_rows"] for b in r) and "Too many" in o["many_text"]
            and o["many_text"].count("<b>") == 6, "over 200 results: top 5 and facet buttons, no pager")
    c.check(any(re.fullmatch(r"\d+/\d+", b["text"]) for r in o["narrowed"] for b in r), "a facet narrows to a pageable list")
    c.check(o["stranger"] == "not_yours" and o["crafted_stale"] == "stale", "another user's tap and a stale render are refused")
    c.check(len(clip("A" * 39 + "&" + "B" * 20, 40)) <= 40 and not re.search(r"&(?!amp;|lt;|gt;)", I18N.t("en", "item", n=1, title=clip("R&D " * 20), city="X", level="L", remote="")),
            "clip before escaping: no half entities")


if __name__ == "__main__":
    if "--write-payload" in sys.argv:
        print(f.write_payload(f.payload_doc(PAYLOAD, run()[0], status=STATUS, context=CONTEXT)))
    else:
        main()
