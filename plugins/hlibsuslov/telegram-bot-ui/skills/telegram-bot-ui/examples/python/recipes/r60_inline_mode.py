"""R60 - Inline mode: share a place card into any chat, then let the chat vote on it.

inline_query -> answerInlineQuery (articles, paging, empty/none states) ->
chosen_inline_result (creates the per-message state) -> callbacks from the inline
message -> editMessageText(inline_message_id=...).

Invariants shown (offline, against fixtures):
* every article carries an inline keyboard, otherwise chosen_inline_result has no
  inline_message_id and the message can never be edited;
* "nothing found" is an empty result list plus a button that opens the bot, never fake cards;
* the shared counter is keyed by inline_message_id; one vote per user, a second tap
  toggles it off, the same update delivered twice counts once;
* the keyboard of a shared message is the same for everyone, so "you voted" is
  answered with a toast, not with a per-user button label;
* a callback for an unknown inline message or a removed place gets a toast, not silence.

Run:  py -3 examples/python/recipes/r60_inline_mode.py [--write-payload]
"""
from __future__ import annotations

import sys

import _common as c
from tgkit import flows as f
from tgkit.errors import TelegramError
from tgkit.transport import FakeTransport

PAYLOAD = "r60-inline-mode"
STATUS = "production"
CONTEXT = "inline"
APP = "pl"
BOT = "placecards_bot"
PAGE = 3
ALICE = f.user(111111111, "Alice", "en")
BOGDAN = f.user(222222222, "Богдан", "uk")
EVE = f.user(333333333, "Eve <script>", "en")

COPY = {
    "en": {
        "card": "<b>{title}</b>\n{area} · {note}\n\n{going}",
        "desc": "{area} · {note}",
        "going_none": "Who is in? Tap the button.",
        "going_some": "Going ({n}): {names}",
        "toast_in": "You are in ✓",
        "toast_out": "Removed: you are not going",
        "btn_in": "👍 I'm in",
        "btn_in_n": "👍 I'm in · {n} going",
        "btn_open": "Open in the bot",
        "btn_more": "Open the bot for more",
        "btn_none": "Nothing found: open the bot",
        "sys_stale": "This card is out of date. Share it again.",
        "sys_not_yours": "This card belongs to someone else.",
        "sys_expired": "This card is no longer tracked. Share it again.",
    },
    "uk": {
        "card": "<b>{title}</b>\n{area} · {note}\n\n{going}",
        "desc": "{area} · {note}",
        "going_none": "Хто йде? Натисніть кнопку.",
        "going_some": "Йдуть ({n}): {names}",
        "toast_in": "Ви йдете ✓",
        "toast_out": "Скасовано: ви не йдете",
        "btn_in": "👍 Я йду",
        "btn_in_n": "👍 Я йду · {n}",
        "btn_open": "Відкрити в боті",
        "btn_more": "Більше в боті",
        "btn_none": "Нічого не знайшли: у бот",
        "sys_stale": "Картка застаріла. Поділіться нею знову.",
        "sys_not_yours": "Ця картка належить комусь іншому.",
        "sys_expired": "Картку більше не відстежуємо. Поділіться знову.",
    },
}
I18N = f.I18n(COPY)

PLACES = {   # pop = rank in the "popular" list shown for an empty query
    "kaffa": {"pop": 1, "tags": "coffee кава", "title": {"en": "Kaffa Roasters", "uk": "Каффа Ростерс"},
              "area": {"en": "Podil", "uk": "Поділ"}, "note": {"en": "Filter coffee, oat milk", "uk": "Фільтр-кава, вівсяне молоко"}},
    "pie": {"pop": 2, "tags": "bakery випічка", "title": {"en": "Pie Lab", "uk": "Пай Лаб"},
            "area": {"en": "Podil", "uk": "Поділ"}, "note": {"en": "Apple pie", "uk": "Яблучний пиріг"}},
    "tea": {"pop": 3, "tags": "tea чай", "title": {"en": "Tea Room", "uk": "Чайна кімната"},
            "area": {"en": "Lukianivka", "uk": "Лук'янівка"}, "note": {"en": "Oolong, quiet tables", "uk": "Улун, тихі столики"}},
    "jam": {"pop": 4, "tags": "coffee кава", "title": {"en": "Jam Espresso", "uk": "Джем Еспресо"},
            "area": {"en": "Centre", "uk": "Центр"}, "note": {"en": "Espresso bar, open late", "uk": "Еспресо-бар, до пізна"}},
    "bean": {"pop": 5, "tags": "coffee кава", "title": {"en": "Bean There", "uk": "Бін Дер"},
             "area": {"en": "Pechersk", "uk": "Печерськ"}, "note": {"en": "Pour-over flights", "uk": "Пуровер-сети"}},
    "mono": {"pop": 6, "tags": "coffee кава bakery", "title": {"en": "Mono Cup", "uk": "Моно Кап"},
             "area": {"en": "Obolon", "uk": "Оболонь"}, "note": {"en": "Cardamom bun", "uk": "Булочка з кардамоном"}},
    "nut": {"pop": 7, "tags": "bakery випічка", "title": {"en": "Nut Oven", "uk": "Горішкова піч"},
            "area": {"en": "Centre", "uk": "Центр"}, "note": {"en": "Rye bread", "uk": "Житній хліб"}},
}
RANKED = sorted(PLACES, key=lambda k: PLACES[k]["pop"])


def haystack(key: str) -> str:
    p = PLACES[key]
    return " ".join([*p["title"].values(), p["tags"]]).lower()


class PlaceBot:
    def __init__(self, t: FakeTransport):
        self.t = t
        self.msgs: dict[str, dict] = {}                 # inline_message_id -> {item, lang, voters}
        self.updates = f.UpdateDedup()
        self.log: list[dict] = []

    # ---- inline_query -> answerInlineQuery ------------------------------------
    def keyboard(self, lang: str, key: str, n: int) -> dict:
        label = I18N.t(lang, "btn_in_n", n=n) if n else I18N.t(lang, "btn_in")
        return f.kb([f.btn(label, f.pack(APP, "vote", key), style="primary")],
                    [f.btn(I18N.t(lang, "btn_open"), url=f"https://t.me/{BOT}?start=place_{key}")])

    def card(self, lang: str, key: str, voters: dict[int, str]) -> str:
        p = PLACES[key]
        going = (I18N.t(lang, "going_some", n=len(voters),
                        names=f.Raw(", ".join(f.escape_html(v) for v in voters.values())))
                 if voters else I18N.t(lang, "going_none"))
        return I18N.t(lang, "card", title=p["title"][lang], area=p["area"][lang],
                      note=p["note"][lang], going=f.Raw(going))

    def article(self, lang: str, key: str) -> dict:
        p = PLACES[key]
        return {"type": "article", "id": key, "title": p["title"][lang],
                "description": I18N.t(lang, "desc", area=p["area"][lang], note=p["note"][lang]),
                "input_message_content": {"message_text": self.card(lang, key, {}), "parse_mode": "HTML"},
                "reply_markup": self.keyboard(lang, key, 0)}

    def on_inline_query(self, iq: dict) -> str:
        lang = I18N.lang_for(iq["from"].get("language_code"))
        q = iq["query"].strip().lower()
        offset = int(iq["offset"]) if iq["offset"].isdigit() else 0
        # Localised results depend on the asker: cache them per user (is_personal).
        params: dict = {"inline_query_id": iq["id"], "is_personal": True, "cache_time": 60}
        if not q:        # popular places, no paging; a button leads to the full search in the bot
            page, next_offset, state = RANKED[:PAGE], "", "popular"
            params["button"] = {"text": I18N.t(lang, "btn_more"), "start_parameter": "search"}
        else:
            hits = [k for k in RANKED if q in haystack(k)]
            page = hits[offset:offset + PAGE]
            more = offset + PAGE < len(hits)
            next_offset, state = (str(offset + PAGE) if more else ""), "results"
            if not hits:
                state = "none"
                params["button"] = {"text": I18N.t(lang, "btn_none"), "start_parameter": "search"}
        params["results"] = [self.article(lang, k) for k in page]
        params["next_offset"] = next_offset              # "" = no more pages; <= 64 bytes
        self.t.call("answerInlineQuery", params)
        return state

    # ---- chosen_inline_result: needs /setinlinefeedback in @BotFather ----------
    def on_chosen(self, cr: dict) -> str:
        imid = cr.get("inline_message_id")
        if cr["result_id"] not in PLACES or not imid:    # not ours, or no keyboard -> not editable
            self.log.append({"event": "chosen_ignored", "result_id": cr["result_id"]})
            return "ignored"
        if imid in self.msgs:                            # redelivery must not reset the votes
            return "duplicate"
        lang = I18N.lang_for(cr["from"].get("language_code"))
        self.msgs[imid] = {"item": cr["result_id"], "lang": lang, "voters": {}}
        return "tracked"

    # ---- callbacks from the inline message ------------------------------------
    def on_callback(self, cq: dict) -> str:
        parts = f.unpack(cq.get("data"))
        if parts[0] != APP or len(parts) != 3:
            return "foreign"
        lang = I18N.lang_for(cq["from"].get("language_code"))
        imid = cq.get("inline_message_id")               # an inline message has no `message`
        m = self.msgs.get(imid)
        if m is None:
            self.t.call("answerCallbackQuery", {"callback_query_id": cq["id"], "text": I18N.t(lang, "sys_expired")})
            return "expired"
        if parts[1] != "vote" or parts[2] != m["item"] or parts[2] not in PLACES:
            self.t.call("answerCallbackQuery", {"callback_query_id": cq["id"], "text": I18N.t(lang, "sys_stale")})
            return "stale"
        uid = cq["from"]["id"]
        joined = uid not in m["voters"]
        if joined:
            m["voters"][uid] = cq["from"]["first_name"]
        else:
            del m["voters"][uid]
        try:
            self.t.call("editMessageText", {
                "inline_message_id": imid, "text": self.card(m["lang"], m["item"], m["voters"]),
                "parse_mode": "HTML", "reply_markup": self.keyboard(m["lang"], m["item"], len(m["voters"]))})
        except TelegramError as err:
            if err.category != "not_modified":
                raise
        self.t.call("answerCallbackQuery", {"callback_query_id": cq["id"],
                                            "text": I18N.t(lang, "toast_in" if joined else "toast_out")})
        return "joined" if joined else "left"

    def dispatch(self, update: dict) -> str:
        if not self.updates.first_time(update):
            return "duplicate_update"
        if "inline_query" in update:
            return self.on_inline_query(update["inline_query"])
        if "chosen_inline_result" in update:
            return self.on_chosen(update["chosen_inline_result"])
        return self.on_callback(update["callback_query"])


def run(t: FakeTransport | None = None):
    t = t or FakeTransport()
    bot = PlaceBot(t)
    imid = c.fixture("usecase_chosen_inline_result.json")["chosen_inline_result"]["inline_message_id"]
    n = [100]

    def tap(who: dict, data: str = f.pack(APP, "vote", "kaffa"), at: str = imid) -> str:
        n[0] += 1
        cq = f.callback(f"cq{n[0]}", who, data, inline_message_id=at)
        return bot.dispatch({"update_id": 961000 + n[0], "callback_query": cq})

    out = [bot.dispatch(c.fixture(name)) for name in (
        "usecase_inline_query_empty.json", "usecase_inline_query_text.json",
        "usecase_inline_query_page2.json", "usecase_inline_query_none.json")]
    chosen = c.fixture("usecase_chosen_inline_result.json")
    out.append(bot.dispatch(chosen))                                        # 4 tracked
    out.append(bot.dispatch({**chosen, "update_id": 960055}))                # 5 redelivered under a new id
    foreign = {"update_id": 960006, "chosen_inline_result": {**chosen["chosen_inline_result"],
               "result_id": "removed", "inline_message_id": "AQAAOTHER"}}
    out.append(bot.dispatch(foreign))                                       # 6 not ours -> ignored
    out += [tap(ALICE), tap(BOGDAN), tap(EVE)]                              # 7-9 three joins
    out.append(tap(ALICE))                                                  # 10 second tap toggles off
    out.append(tap(BOGDAN, at="AQAAUNKNOWN"))                               # 11 unknown inline message
    out.append(tap(ALICE, f.pack(APP, "vote", "closed")))                   # 12 place no longer exists
    again = {"update_id": 961777, "callback_query": f.callback("cqdup", BOGDAN, f.pack(APP, "vote", "kaffa"),
                                                              inline_message_id=imid)}
    out += [bot.dispatch(again), bot.dispatch(again)]                       # 13-14 toggle once, redelivery dropped
    return t, bot, out


def main() -> None:
    t, bot, out = run()
    c.dump(t, "Inline mode")
    answers = t.params_of("answerInlineQuery")
    c.check(out[:4] == ["popular", "results", "results", "none"], "four inline queries answered")
    first = answers[0]
    c.check(len(first["results"]) == PAGE and first["next_offset"] == "" and first["is_personal"]
            and first["button"]["start_parameter"] == "search",
            "empty query: popular places, personal, button that opens the bot")
    c.check(answers[1]["next_offset"] == "3" and len(answers[2]["results"]) == 1 and answers[2]["next_offset"] == "",
            "paging: next_offset '3' on page 1, '' on the last page")
    c.check(answers[3]["results"] == [] and answers[3]["button"]["start_parameter"] == "search",
            "nothing found: no fake cards, one button that opens the bot")
    ids = [r["id"] for a in answers for r in a["results"]]
    c.check(all(len(i.encode()) <= 64 for i in ids) and all(len(a["results"]) <= 50 for a in answers)
            and all(len(a["next_offset"].encode()) <= 64 for a in answers),
            "result ids, results count and next_offset within limits")
    c.check(all(r["reply_markup"]["inline_keyboard"] for a in answers for r in a["results"]),
            "every article has an inline keyboard (so inline_message_id arrives)")
    c.check(out[4:7] == ["tracked", "duplicate", "ignored"] and list(bot.msgs) == ["AQAAAKx2nwABCDEF"],
            "chosen_inline_result creates state once, foreign result ignored")
    edits = t.params_of("editMessageText")
    c.check(out[7:11] == ["joined"] * 3 + ["left"] and "chat_id" not in edits[0]
            and edits[0]["inline_message_id"] == "AQAAAKx2nwABCDEF",
            "votes edit the inline message by inline_message_id; second tap toggles off")
    c.check(edits[2]["reply_markup"]["inline_keyboard"][0][0]["text"] == "👍 I'm in · 3 going"
            and "Eve &lt;script&gt;" in edits[2]["text"], "shared counter 3, names escaped")
    toasts = [p["text"] for p in t.params_of("answerCallbackQuery")]
    c.check(out[11:13] == ["expired", "stale"] and "більше не відстежуємо" in toasts[4]
            and "out of date" in toasts[5], "unknown message / removed place: localized toast")
    c.check(out[13:] == ["left", "duplicate_update"] and bot.msgs["AQAAAKx2nwABCDEF"]["voters"] == {333333333: "Eve <script>"},
            "the same update delivered twice counts once; one vote per user")


if __name__ == "__main__":
    if "--write-payload" in sys.argv:
        print(f.write_payload(f.payload_doc(PAYLOAD, run()[0], status=STATUS, context=CONTEXT)))
    else:
        main()
