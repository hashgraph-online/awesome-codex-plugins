"""R27 - Assistant as a product: modes, a streamed draft with real stages and Stop,
a final answer with feedback and Regenerate, history, and file input.

Builds the product around r01 (the generation state machine in tgkit.generation):
* modes screen: the current mode is a disabled "✓" button, the others switch it;
* one running answer per chat (OperationRegistry): a second question gets "wait or
  press Stop" instead of a second stream;
* Stop arrives as `stopped_message_generation`; the partial answer is kept and marked;
* the final answer carries a footer and feedback buttons; feedback counts once per
  answer, a thumbs-down asks why with a force_reply keyboard (10.3);
* Regenerate starts a new draft id and retires the old answer's buttons;
* a document is accepted or refused with a reason before any money is spent on it.

Run:  py -3 examples/python/recipes/r27_ai_assistant_product.py [--write-payload]
"""
from __future__ import annotations

import html
import sys

import _common as c
from tgkit import flows as f
from tgkit.generation import Generation, GenerationConfig, OperationRegistry, State, execute
from tgkit.transport import FakeTransport

PAYLOAD = "r27-ai-assistant-product"
STATUS = "production"
CONTEXT = "private"
ALICE = f.user(111111111, "Alice", "en")
BOGDAN = f.user(222222222, "Богдан", "ru")
MODES = ("chat", "translate", "summarize")
MAX_FILE_BYTES = 10 * 1024 * 1024          # our product limit; bots can download up to 20 MB (getFile)
FILE_TYPES = {"application/pdf", "text/plain", "text/markdown"}
PAGE_SIZE, HISTORY_KEEP = 2, 5
# Draft ids are chosen by the bot and must be non-zero; 48127 matches the Stop fixture.
DRAFT_IDS = [48120, 48127, 48128, 48129, 48130, 48131]
SEED_HISTORY = [("How do I set up a webhook?", "chat"), ("Translate “good morning” to French", "translate"),
                ("Summarize this changelog", "summarize"), ("What is a deep link?", "chat")]
ANSWER = {"en": ["Short answer first. ", "can_stop adds a Stop button under the draft. ",
                 "\n\nkeep_on_stop keeps the partial text visible after Stop."],
          "ru": ["Сначала коротко. ", "can_stop добавляет кнопку «Стоп» под черновиком. ",
                 "\n\nkeep_on_stop оставляет частичный текст после остановки."]}
SCRIPT = [("stage", "read"), ("chunk", 0), ("stage", "write"), ("chunk", 1), ("chunk", 2)]

COPY = {
    "en": {
        "modes": "<b>Assistant</b>\nChoose what I do with your next message.\nMode: <b>{mode}</b>",
        "mode_chat": "Chat", "mode_translate": "Translate", "mode_summarize": "Summarize",
        "history": "<b>History</b> · page {page} of {pages}\n{lines}",
        "history_empty": "<b>History</b>\nNo conversations yet. Ask me something.",
        "footer": "{mode} · Answers can be inaccurate. Check important facts.",
        "busy": "I'm still writing the previous answer. Wait for it, or press Stop under the draft.",
        "fb_thanks": "Thanks for the feedback.", "fb_done": "You already rated this answer.",
        "fb_ask": "What was wrong with the answer? Tap a reason or reply with your own words.",
        "fb_noted": "Noted, thank you.",
        "doc_ok": "Got <b>{name}</b> ({size}). Ask your question about it.",
        "doc_big": "<b>{name}</b> is too large: {size}. The limit is {limit}.",
        "doc_type": "Files of type {mime} aren't supported. Send a PDF or a text file.",
        "stage_start": "Starting…", "stage_read": "Reading your question…", "stage_write": "Writing the answer…",
        "gen_stopped_note": "Stopped by you — the answer is incomplete.",
        "gen_stopped_discarded": "Stopped. Nothing was saved.",
        "gen_stopped_offer": "Stopped. Continue from here or start over?",
        "gen_failed": "Couldn't finish the answer. Nothing was charged.",
        "gen_timed_out": "This is taking too long, so I stopped.",
        "gen_continue": "Continue", "gen_retry": "Try again",
        "btn_mode_chat": "Chat", "btn_mode_translate": "Translate", "btn_mode_summarize": "Summarize",
        "btn_history": "History", "btn_back": "← Back", "btn_regen": "↻ Regenerate",
        "btn_up": "👍", "btn_down": "👎", "btn_retired": "Replaced by a newer answer",
        "btn_r_wrong": "Incorrect", "btn_r_long": "Too long", "btn_r_off": "Off topic",
        "sys_stale": "This screen has changed. Use the latest message.",
        "sys_not_yours": "This answer belongs to someone else.",
        "sys_expired": "This menu has expired. Send /start.",
    },
    "ru": {
        "modes": "<b>Ассистент</b>\nВыберите, что делать с вашим следующим сообщением.\nРежим: <b>{mode}</b>",
        "mode_chat": "Чат", "mode_translate": "Перевод", "mode_summarize": "Пересказ",
        "history": "<b>История</b> · страница {page} из {pages}\n{lines}",
        "history_empty": "<b>История</b>\nРазговоров пока нет. Спросите что-нибудь.",
        "footer": "{mode} · Ответ может быть неточным. Проверяйте важные факты.",
        "busy": "Я ещё пишу предыдущий ответ. Дождитесь его или нажмите «Стоп» под черновиком.",
        "fb_thanks": "Спасибо за отзыв.", "fb_done": "Вы уже оценили этот ответ.",
        "fb_ask": "Что было не так? Нажмите причину или ответьте своими словами.",
        "fb_noted": "Записал, спасибо.",
        "doc_ok": "Получил <b>{name}</b> ({size}). Задайте вопрос по нему.",
        "doc_big": "<b>{name}</b> слишком большой: {size}. Лимит: {limit}.",
        "doc_type": "Файлы типа {mime} не поддерживаются. Пришлите PDF или текстовый файл.",
        "stage_start": "Начинаю…", "stage_read": "Читаю ваш вопрос…", "stage_write": "Пишу ответ…",
        "gen_stopped_note": "Остановлено вами — ответ неполный.",
        "gen_stopped_discarded": "Остановлено. Ничего не сохранено.",
        "gen_stopped_offer": "Остановлено. Продолжить отсюда или начать заново?",
        "gen_failed": "Не удалось дописать ответ. Ничего не списано.",
        "gen_timed_out": "Это занимает слишком долго, поэтому я остановился.",
        "gen_continue": "Продолжить", "gen_retry": "Ещё раз",
        "btn_mode_chat": "Чат", "btn_mode_translate": "Перевод", "btn_mode_summarize": "Пересказ",
        "btn_history": "История", "btn_back": "← Назад", "btn_regen": "↻ Заново",
        "btn_up": "👍", "btn_down": "👎", "btn_retired": "Заменён новым ответом",
        "btn_r_wrong": "Неверно", "btn_r_long": "Слишком длинно", "btn_r_off": "Не по теме",
        "sys_stale": "Экран изменился. Используйте последнее сообщение.",
        "sys_not_yours": "Этот ответ принадлежит другому человеку.",
        "sys_expired": "Меню устарело. Отправьте /start.",
    },
}
I18N = f.I18n(COPY)
REASONS = ("r_wrong", "r_long", "r_off")


def plain(lang: str, key: str, **values) -> str:
    return html.unescape(I18N.t(lang, key, **values))


def gen_config(lang: str) -> GenerationConfig:
    return GenerationConfig(
        deadline=60.0,
        stage_labels={k: plain(lang, f"stage_{k}") for k in ("start", "read", "write")},
        texts={k: plain(lang, f"gen_{k}") for k in ("stopped_note", "stopped_discarded", "stopped_offer",
                                                    "failed", "timed_out", "continue", "retry")})


class Busy(Exception):
    pass


class Assistant:
    def __init__(self, t: FakeTransport):
        self.t = t
        self.flow = f.ScreenFlow(t, "as", i18n=I18N)
        self.registry = OperationRegistry()
        self.updates = f.UpdateDedup()
        self.answers: dict[str, dict] = {}
        self.prompts: dict[int, str] = {}              # feedback prompt message id -> answer id
        self.drafts_used = 0
        self.clock = 0.0
        self.last: dict | None = None
        self._answered: set[str] = set()
        self._screens()

    # ---- screens ------------------------------------------------------------
    def _screens(self) -> None:
        fl = self.flow

        @fl.screen("modes")
        def modes(fl, s):
            cur = s.data.get("mode", "chat")
            row = [f.btn("✓ " + fl.tr(s, f"btn_mode_{m}"), disabled=True) if m == cur
                   else f.btn(fl.tr(s, f"btn_mode_{m}"), fl.cb(s, "mode", m)) for m in MODES]
            return {"text": fl.tr(s, "modes", mode=fl.tr(s, f"mode_{cur}")),
                    "reply_markup": f.kb(row, [f.btn(fl.tr(s, "btn_history"), fl.cb(s, "history"))])}

        @fl.screen("history")
        def history(fl, s):
            items = list(reversed(s.data.get("history", [])))[:HISTORY_KEEP]
            back = [f.btn(fl.tr(s, "btn_back"), fl.cb(s, "back"))]
            if not items:
                return {"text": fl.tr(s, "history_empty"), "reply_markup": f.kb(back)}
            part, page, pages = f.paginate(items, s.args.get("page", 0), PAGE_SIZE)
            lines = "\n".join(f"{page * PAGE_SIZE + i + 1}. {f.escape_html(q)} · {fl.tr(s, 'mode_' + m)}"
                              for i, (q, m) in enumerate(part))
            return {"text": fl.tr(s, "history", page=page + 1, pages=pages, lines=f.Raw(lines)),
                    "reply_markup": f.kb(f.pager_row(fl, s, page, pages), back)}

        @fl.action("mode")
        def a_mode(fl, s, args, cq):
            s.data["mode"] = args[0] if args[0] in MODES else "chat"
            fl.refresh(s)

        @fl.action("history")
        def a_history(fl, s, args, cq):
            fl.go(s, "history", page=0)

        @fl.action("page")
        def a_page(fl, s, args, cq):
            s.args["page"] = int(args[0])
            fl.refresh(s)

        @fl.action("back")
        def a_back(fl, s, args, cq):
            fl.back(s)

    # ---- generation -----------------------------------------------------------
    def begin(self, s: f.Session, question: str, mode: str) -> dict:
        gen = Generation(op_id=f.b36(len(self.answers) + 1), chat_id=s.chat_id, draft_id=DRAFT_IDS[self.drafts_used],
                         config=gen_config(s.lang))
        try:
            self.registry.add(gen)
        except RuntimeError:
            raise Busy from None
        self.drafts_used += 1                           # a refused question does not burn a draft id
        rec = {"id": gen.op_id, "user": s.owner_id, "chat": s.chat_id, "lang": s.lang, "question": question,
               "mode": mode, "gen": gen, "message_id": None, "retired": False, "feedback": None,
               "reason": None, "prompt_id": None, "script": list(SCRIPT)}
        self.answers[rec["id"]] = rec
        self.last = rec
        self.pump(rec, gen.start(self.clock))
        return rec

    def advance(self, rec: dict, steps: int | None = None) -> None:
        """Feed the scripted model stream: `steps` events, or all of them and then completion."""
        gen = rec["gen"]
        while rec["script"] and steps != 0 and not gen.terminal:
            kind, value = rec["script"].pop(0)
            self.clock += 1.2
            effects = (gen.on_stage(value, self.clock) if kind == "stage"
                       else gen.on_chunk(ANSWER[rec["lang"]][value], self.clock))
            self.pump(rec, effects)
            steps = steps - 1 if steps else steps
        if steps is None and not gen.terminal:
            self.pump(rec, gen.on_done(self.clock))

    def pump(self, rec: dict, effects: list) -> None:
        gen = rec["gen"]
        for eff in effects:
            if eff.get("final"):
                self.decorate(rec, eff)
        results = execute(effects, self.t, gen, now=self.clock, cancel_upstream=lambda: rec.update(cancelled=True))
        if any(e.get("final") for e in effects):
            rec["message_id"] = results[-1]["message_id"]
            if gen.outcome == State.COMPLETED:
                s = self.flow.sessions[(rec["chat"], rec["user"])]
                s.data.setdefault("history", []).append((rec["question"], rec["mode"]))

    def decorate(self, rec: dict, eff: dict) -> None:
        params, lang, aid = eff["params"], rec["lang"], rec["id"]
        regen = [f.btn(plain(lang, "btn_regen"), f.pack("ai", aid, "re"))]
        if rec["gen"].outcome == State.COMPLETED:
            footer = plain(lang, "footer", mode=plain(lang, f"mode_{rec['mode']}"))
            params["rich_message"]["blocks"].append({"type": "footer", "text": footer})
            params["reply_markup"] = f.kb([f.btn(plain(lang, "btn_up"), f.pack("ai", aid, "up")),
                                           f.btn(plain(lang, "btn_down"), f.pack("ai", aid, "dn"))], regen)
        else:                                           # stopped / failed / timed out: only a retry
            params["reply_markup"] = f.kb(regen)

    # ---- incoming updates -----------------------------------------------------
    def toast(self, cq: dict, key: str, *, alert: bool = False) -> None:
        if cq["id"] in self._answered:
            return
        self._answered.add(cq["id"])
        p = {"callback_query_id": cq["id"]}
        if key:
            p["text"] = plain(I18N.lang_for(cq["from"].get("language_code")), key)
            p["show_alert"] = alert or None
        self.t.call("answerCallbackQuery", {k: v for k, v in p.items() if v is not None})

    def on_answer_button(self, cq: dict) -> str:
        _, aid, action, *rest = f.unpack(cq["data"])
        rec = self.answers.get(aid)
        if rec is None:
            self.toast(cq, "sys_expired")
            return "expired"
        if rec["user"] != cq["from"]["id"]:
            self.toast(cq, "sys_not_yours", alert=True)
            return "not_yours"
        if rec["retired"] and action in ("up", "dn", "re"):
            self.toast(cq, "sys_stale")
            return "stale"
        if action == "re":
            return self.regenerate(rec, cq)
        if rec["feedback"] and action in ("up", "dn") or rec["reason"] and action == "rs":
            self.toast(cq, "fb_done")
            return "feedback_done"
        lang = rec["lang"]
        if action == "rs":
            rec["reason"] = REASONS[int(rest[0])]
            self.toast(cq, "fb_noted")
            return "reason_saved"
        rec["feedback"] = action
        mark = f.btn(plain(lang, "btn_up" if action == "up" else "btn_down") + " ✓", disabled=True)
        self.t.call("editMessageReplyMarkup", {"chat_id": rec["chat"], "message_id": rec["message_id"],
                                               "reply_markup": f.kb([mark], [f.btn(plain(lang, "btn_regen"),
                                                                                  f.pack("ai", rec["id"], "re"))])})
        if action == "dn":                              # force_reply: buttons AND the reply field
            rows = [[f.btn(plain(lang, f"btn_{k}"), f.pack("ai", rec["id"], "rs", i)) for i, k in enumerate(REASONS)]]
            msg = self.t.call("sendMessage", {"chat_id": rec["chat"], "text": I18N.t(lang, "fb_ask"),
                                              "parse_mode": "HTML", "reply_markup": f.kb(*rows, force_reply=True)})
            rec["prompt_id"] = msg["message_id"]
            self.prompts[msg["message_id"]] = rec["id"]
        self.toast(cq, "fb_thanks")
        return "feedback_" + action

    def regenerate(self, old: dict, cq: dict) -> str:
        s = self.flow.sessions[(old["chat"], old["user"])]
        try:
            new = self.begin(s, old["question"], old["mode"])     # new draft id; refused while one runs
        except Busy:
            self.toast(cq, "busy", alert=True)
            return "busy"
        old["retired"] = True
        self.t.call("editMessageReplyMarkup", {"chat_id": old["chat"], "message_id": old["message_id"],
                                               "reply_markup": f.kb([f.btn(plain(old["lang"], "btn_retired"),
                                                                           disabled=True)])})
        self.toast(cq, "")
        return "regenerating"

    def on_message(self, msg: dict) -> str:
        user = msg["from"]
        s = self.flow.session(msg["chat"]["id"], user["id"], lang=I18N.lang_for(user.get("language_code")))
        if "document" in msg:
            return self.on_document(s, msg)
        text = msg.get("text", "")
        if text.startswith("/start"):
            s.data.setdefault("history", list(SEED_HISTORY) if user["id"] == ALICE["id"] else [])
            self.flow.open(s, "modes", new_message=True)
            return "modes"
        reply_to = (msg.get("reply_to_message") or {}).get("message_id")
        if reply_to in self.prompts:                    # a typed reason for a thumbs-down
            rec = self.answers[self.prompts[reply_to]]
            if rec["user"] != user["id"] or rec["reason"]:
                return "ignored"
            rec["reason"] = "text"
            self.t.call("sendMessage", {"chat_id": s.chat_id, "text": I18N.t(s.lang, "fb_noted"),
                                        "parse_mode": "HTML"})
            return "reason_saved"
        try:
            self.begin(s, text, s.data.get("mode", "chat"))
        except Busy:                                    # one stream per chat: wait or Stop
            self.t.call("sendMessage", {"chat_id": s.chat_id, "text": I18N.t(s.lang, "busy"), "parse_mode": "HTML"})
            return "busy"
        return "generating"

    def on_document(self, s: f.Session, msg: dict) -> str:
        doc = msg["document"]
        name, size, mime = doc.get("file_name", "file"), doc.get("file_size", 0), doc.get("mime_type") or "unknown"
        if mime not in FILE_TYPES:
            key, values, outcome = "doc_type", {"mime": mime}, "doc_type_refused"
        elif size > MAX_FILE_BYTES:
            key, values, outcome = "doc_big", {"name": name, "size": mb(size), "limit": mb(MAX_FILE_BYTES)}, "doc_too_big"
        else:
            key, values, outcome = "doc_ok", {"name": name, "size": mb(size)}, "doc_accepted"
        self.t.call("sendMessage", {"chat_id": s.chat_id, "text": I18N.t(s.lang, key, **values),
                                    "parse_mode": "HTML", "reply_parameters": {"message_id": msg["message_id"]}})
        return outcome

    def dispatch(self, update: dict) -> str:
        if not self.updates.first_time(update):
            return "duplicate_update"
        if "stopped_message_generation" in update:
            stop = update["stopped_message_generation"]
            gen = self.registry.find_for_stop(stop)
            if gen is None:
                return "unknown_draft"
            self.pump(self.answers[gen.op_id], gen.on_stop(self.clock))
            return "stopped"
        if "callback_query" in update:
            cq = update["callback_query"]
            if f.unpack(cq.get("data"))[0] == "ai":
                return self.on_answer_button(cq)
            return self.flow.handle(cq)
        return self.on_message(update["message"])


def mb(n: int) -> str:
    return f"{n / 1048576:.1f} MB"


def run(t: FakeTransport | None = None):
    t = t or FakeTransport()
    app = Assistant(t)
    fl = app.flow
    n = [0]
    log: dict[str, object] = {}

    def update(**kw) -> dict:
        n[0] += 1
        return {"update_id": 3000 + n[0], **kw}

    def say(who: dict, text: str, **extra) -> str:
        return app.dispatch(update(message=f.text_message(who, text, message_id=100 + n[0], **extra)))

    def tap(who: dict, action: str, *args, offset: int = 0) -> str:
        s = fl.sessions[(who["id"], who["id"])]
        cq = f.callback(f"cq{n[0] + 1}", who, f.pack("as", f.b36(s.version - offset), action, *args),
                        chat_id=who["id"], message_id=s.message_id)
        return app.dispatch(update(callback_query=cq))

    def tap_ai(who: dict, rec: dict, action: str, *extra, message_id: int | None = None) -> str:
        cq = f.callback(f"cq{n[0] + 1}", who, f.pack("ai", rec["id"], action, *extra), chat_id=rec["chat"],
                        message_id=message_id or rec["message_id"])
        return app.dispatch(update(callback_query=cq))

    say(ALICE, "/start")
    log["modes"] = [tap(ALICE, "mode", "translate"), tap(ALICE, "mode", "chat", offset=1), tap(ALICE, "mode", "chat")]
    log["docs"] = [app.dispatch(c.fixture("usecase_ai_document_pdf.json"))]
    # Q1: a second question while it streams is refused; then it completes.
    say(ALICE, "What does can_stop do?")
    q1 = app.last
    app.advance(q1, 2)
    log["busy"] = say(ALICE, "And keep_on_stop?")
    app.advance(q1)
    log["fb"] = [tap_ai(ALICE, q1, "up"), tap_ai(ALICE, q1, "dn"), tap_ai(BOGDAN, q1, "re")]
    # Q2: the user presses Stop (the fixture's draft id) while it streams.
    say(ALICE, "Explain Stop in drafts")
    q2 = app.last
    app.advance(q2, 2)
    log["stop"] = app.dispatch(c.fixture("stopped_message_generation.json"))
    app.advance(q2)                                    # late events after Stop are dropped
    log["regen"] = [tap_ai(ALICE, q2, "re")]
    q3 = app.last
    app.advance(q3)
    log["regen"].append(tap_ai(ALICE, q2, "re"))       # the retired answer's button
    log["down"] = [tap_ai(ALICE, q3, "dn")]
    log["down"].append(say(ALICE, "Too vague", reply_to=q3["prompt_id"]))
    log["down"].append(tap_ai(ALICE, q3, "rs", 1, message_id=q3["prompt_id"]))
    # History: last 5 conversations, two per page.
    log["history"] = [tap(ALICE, "history"), tap(ALICE, "page", 1)]
    # Bogdan (ru): file checks, then one answer in Russian.
    say(BOGDAN, "/start")
    big = c.fixture("usecase_ai_document_pdf.json")
    big["update_id"] = 99001
    big["message"]["from"], big["message"]["chat"] = BOGDAN, {"id": BOGDAN["id"], "type": "private"}
    big["message"]["document"]["file_size"] = 30 * 1024 * 1024
    zipped = c.fixture("usecase_ai_document_zip.json")
    zipped["message"]["from"], zipped["message"]["chat"] = BOGDAN, {"id": BOGDAN["id"], "type": "private"}
    log["docs"] += [app.dispatch(big), app.dispatch(zipped)]
    say(BOGDAN, "Что делает can_stop?")
    app.advance(app.last)
    return t, app, log


def main() -> None:
    t, app, log = run()
    c.dump(t, "Assistant product")
    q1, q2, q3 = (app.answers[k] for k in ("1", "2", "3"))
    c.check(log["modes"] == ["ok", "stale", "ok"], "mode switch works; a tap on the old render is stale")
    c.check(log["docs"] == ["doc_accepted", "doc_too_big", "doc_type_refused"],
            "a 2 MB PDF is accepted; 30 MB and a zip are refused with a reason")
    refusals = [p["text"] for p in t.params_of("sendMessage") if "слишком" in p["text"] or "не поддерж" in p["text"]]
    c.check(len(refusals) == 2, "refusals use the sender's language (ru)")
    c.check(log["busy"] == "busy" and q1["gen"].outcome == State.COMPLETED and q1["gen"].finalizations == 1,
            "a second question while one runs is refused; the first finishes once")
    drafts = t.params_of("sendRichMessageDraft")
    c.check(all(d["can_stop"] for d in drafts) and any(b["text"] == "Reading your question…"
            for d in drafts for b in d["rich_message"]["blocks"] if b["type"] == "thinking"),
            "drafts offer Stop and show a real stage label (localized)")
    final = next(p for p in t.params_of("sendRichMessage") if p["chat_id"] == ALICE["id"])
    c.check(final["rich_message"]["blocks"][-1]["type"] == "footer" and len(final["reply_markup"]["inline_keyboard"]) == 2,
            "final answer: footer, 👍 👎 row and Regenerate")
    c.check(log["fb"] == ["feedback_up", "feedback_done", "not_yours"], "feedback counts once; another user is refused")
    c.check(log["stop"] == "stopped" and q2["gen"].outcome == State.STOPPED and q2.get("cancelled"),
            "Stop (fixture) finalizes once and cancels the model")
    c.check(log["regen"] == ["regenerating", "stale"] and q2["retired"] and q3["gen"].draft_id != q2["gen"].draft_id,
            "Regenerate uses a new draft id and retires the old buttons")
    prompt = next(p for p in t.params_of("sendMessage") if p.get("reply_markup", {}).get("force_reply"))
    c.check(log["down"] == ["feedback_dn", "reason_saved", "feedback_done"] and prompt["reply_markup"]["force_reply"],
            "thumbs-down asks why (force_reply); a typed reason counts once")
    hist = [p["text"] for p in t.params_of("editMessageText") if "History" in p.get("text", "")]
    c.check(len(hist) == 2 and "page 2 of 3" in hist[1], "history: last 5 conversations, paged with a pager row")
    c.check(any("Ответ может быть неточным" in str(p) for p in t.params_of("sendRichMessage")),
            "the final answer's footer is localized (ru)")


if __name__ == "__main__":
    if "--write-payload" in sys.argv:
        print(f.write_payload(f.payload_doc(PAYLOAD, run()[0], status=STATUS, context=CONTEXT)))
    else:
        main()
