#!/usr/bin/env python3
"""Choosing several options from a list, done right: a learning bot's "categories to study" screen.

Two variants of the same screen, both built from the bot's own state (references/selection-lists.md):

  * inline_screen() - a regular message and an inline keyboard: options two per row with short localised names
    and counts, the chosen ones marked with "✓" (or a static custom emoji check of the bot's family), a summary
    line in the message, Select all / Clear, pages past PAGE_SIZE options, inline search past SEARCH_AT, Done as the
    one primary action next to Select all / Clear (disabled, with the reason in the text, while nothing is chosen),
    Back last; at most 8 rows.
  * rich_screen() - a Rich Message: the options as a list whose items carry Telegram's own checkboxes
    (InputRichBlockListItem has_checkbox / is_checked), each with a quiet link-style button in its line to add or
    remove it, and one button row at the end. Every tap re-renders the message with editMessageText(rich_message).
    Rich list checkboxes are drawn by Telegram and are not tappable themselves: the buttons are.

Standard library only; no token, no network. `py -3 pick_categories.py` prints both payloads; the test validates
them with scripts/validate_keyboard.py and scripts/validate_rich.py.
"""
from __future__ import annotations

import json
import re
import sys
from html import escape

PAGE_SIZE = 8         # options per page of the inline keyboard: four rows of two, so the screen stays <= 8 rows
SEARCH_AT = 20        # more options than this: offer inline search in the keyboard
MINI_APP_AT = 30      # more than this, or filters on top: a Mini App picker (references/selection-lists.md)

# (id, count, {lang: short name}); the names are the bot's own, in the user's language
CATEGORIES = [
    ("warning", 47, {"uk": "Попереджувальні", "en": "Warning"}),
    ("priority", 7, {"uk": "Пріоритету", "en": "Priority"}),
    ("prohibit", 48, {"uk": "Заборонні", "en": "Prohibitory"}),
    ("mandatory", 11, {"uk": "Наказові", "en": "Mandatory"}),
    ("info", 46, {"uk": "Інформаційні", "en": "Information"}),
    ("direction", 49, {"uk": "Вказівники", "en": "Direction"}),
    ("service", 23, {"uk": "Сервісу", "en": "Service"}),
    ("plates", 34, {"uk": "Таблички", "en": "Plates"}),
    ("markers", 17, {"uk": "Направляючі", "en": "Markers"}),
]

T = {
    "uk": {"title": "Категорії для навчання", "hint": "Торкніться категорії, щоб додати її до навчання або прибрати.",
           "summary": "Обрано {n} з {total} · {signs} знаків", "none": "Оберіть хоча б одну категорію.",
           "all": "Вибрати всі", "clear": "Очистити", "done": "Готово · {n}", "done0": "Готово", "back": "← Назад",
           "search": "Пошук категорії", "add": "Додати", "remove": "Прибрати", "page": "{p}/{pages}",
           "prev": "‹ Попередні", "next": "Наступні ›"},
    "en": {"title": "Categories to study", "hint": "Tap a category to add it to your studies or take it out.",
           "summary": "{n} of {total} selected · {signs} signs", "none": "Choose at least one category.",
           "all": "Select all", "clear": "Clear", "done": "Done · {n}", "done0": "Done", "back": "← Back",
           "search": "Search categories", "add": "Add", "remove": "Remove", "page": "{p}/{pages}",
           "prev": "‹ Previous", "next": "Next ›"},
}


def _summary(t: dict, selected: set[str], options: list) -> str:
    signs = sum(c for i, c, _ in options if i in selected)
    return t["summary"].format(n=len(selected), total=len(options), signs=signs)


def _option_label(name: str, count: int, chosen: bool, with_icon: bool) -> str:
    """"✓ Наказові · 11" when chosen; with a custom emoji check the icon carries the state and the text stays plain."""
    mark = "✓ " if chosen and not with_icon else ""
    return f"{mark}{name} · {count}"


OPTION_ID = re.compile(r"[a-z0-9_-]{1,40}")  # "cat:t:<id>" stays well inside callback_data's 64 bytes


def _checked(options: list) -> list:
    bad = [o[0] for o in options if not OPTION_ID.fullmatch(str(o[0]))]
    if bad:
        raise ValueError(f"option ids are 1-40 of a-z 0-9 _ - (callback data): {bad[:3]}")
    return options


def inline_screen(lang: str, selected: set[str], page: int = 0, *, options: list | None = None,
                  check_icon_id: str | None = None) -> dict:
    """sendMessage / editMessageText params for one page. `check_icon_id`: a STATIC custom emoji check from the
    bot's own family (only when the bot may use custom emoji); without it the state is a "✓" text mark."""
    options = _checked(CATEGORIES if options is None else options)
    t = T[lang]
    pages = max(1, -(-len(options) // PAGE_SIZE))
    page = min(max(0, page), pages - 1)
    shown = options[page * PAGE_SIZE:(page + 1) * PAGE_SIZE]
    rows: list[list[dict]] = []
    for k in range(0, len(shown), 2):
        row = []
        for oid, count, names in shown[k:k + 2]:
            chosen = oid in selected
            btn = {"text": _option_label(names[lang], count, chosen, bool(check_icon_id)), "callback_data": f"cat:t:{oid}"}
            if chosen and check_icon_id:
                btn["icon_custom_emoji_id"] = check_icon_id
            row.append(btn)
        rows.append(row)
    if pages > 1:
        rows.append([
            {"text": t["prev"], "callback_data": f"cat:p:{page - 1}"} if page > 0 else {"text": t["prev"], "disabled": {}},
            {"text": t["page"].format(p=page + 1, pages=pages), "disabled": {}},
            {"text": t["next"], "callback_data": f"cat:p:{page + 1}"} if page < pages - 1 else {"text": t["next"], "disabled": {}},
        ])
    if len(options) > SEARCH_AT:
        rows.append([{"text": t["search"], "switch_inline_query_current_chat": ""}])
    bulk = {"text": t["clear"], "callback_data": "cat:none"} if selected else {"text": t["all"], "callback_data": "cat:all"}
    done = ({"text": t["done"].format(n=len(selected)), "callback_data": "cat:done", "style": "primary"} if selected
            else {"text": t["done0"], "disabled": {}})
    rows.append([bulk, done])
    rows.append([{"text": t["back"], "callback_data": "settings"}])
    status = _summary(t, selected, options) if selected else t["none"]
    text = f"<b>{escape(t['title'])}</b>\n{escape(status)}\n\n{escape(t['hint'])}"
    return {"text": text, "parse_mode": "HTML", "reply_markup": {"inline_keyboard": rows}}


def rich_screen(lang: str, selected: set[str], *, options: list | None = None) -> dict:
    """sendRichMessage params (editMessageText takes the same rich_message on every tap)."""
    options = _checked(CATEGORIES if options is None else options)
    t = T[lang]
    items = []
    for oid, count, names in options:
        chosen = oid in selected
        toggle = {"text": t["remove"] if chosen else t["add"], "callback_data": f"cat:t:{oid}", "style": "link"}
        items.append({"has_checkbox": True, **({"is_checked": True} if chosen else {}), "blocks": [
            {"type": "paragraph", "text": [f"{names[lang]} · {count}  ", {"type": "button", "button": toggle}]}]})
    status = _summary(t, selected, options) if selected else t["none"]
    bulk = {"text": t["clear"], "callback_data": "cat:none"} if selected else {"text": t["all"], "callback_data": "cat:all"}
    done = ({"text": t["done"].format(n=len(selected)), "callback_data": "cat:done", "style": "primary"} if selected
            else {"text": t["done0"], "disabled": {}})
    blocks = [
        {"type": "heading", "size": 3, "text": t["title"]},
        {"type": "paragraph", "text": {"type": "bold", "text": status}},
        {"type": "list", "items": items},
        {"type": "buttons", "buttons": [bulk, done], "align": "left"},
    ]
    return {"rich_message": {"blocks": blocks}}


def toggle(selected: set[str], data: str, options: list | None = None) -> set[str]:
    """The bot's side of a tap: cat:t:<id> toggles one, cat:all / cat:none set every option. Ids are checked
    against the bot's own list; the state lives on the server, the callback only names the change."""
    ids = [i for i, _, _ in (CATEGORIES if options is None else options)]
    if data == "cat:all":
        return set(ids)
    if data == "cat:none":
        return set()
    if data.startswith("cat:t:") and data[6:] in ids:
        return selected ^ {data[6:]}
    return selected


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    chosen = {"mandatory", "service", "plates"}
    print(json.dumps({"inline": inline_screen("uk", chosen), "rich": rich_screen("uk", chosen)}, ensure_ascii=False, indent=1))
