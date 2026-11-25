"""Visual widget builder (builder/v1): schema, defaults, validation, generator, mock answers, eject.

A widget.json with `builder` (and no `builder.ejected`) is generated, not hand-written: the
generator turns the typed configuration into a widget source on the kit (`<!--@kit ...-->`
partials, `/*@lang xx*/` string blocks), and `widgets.build` builds it like any other source.
Format: studio/docs/widget-builder.md. Standard library only.

Design of the generated code: localized texts live in one `K.add` block per language (the build
keeps one), elements are filled by id, so the same source serves every language and an ejected
widget keeps all of them. Colours are CSS custom properties on the root block (`--c-<slot>`):
a Telegram theme variable by default, `light-dark(light, dark)` when the author picks colours.
"""
from __future__ import annotations

import copy
import html as _html
import itertools
import json
import re
import time
from typing import Any

VERSION = 1
GENERATOR = "builder/v1.0"  # part of the source hash: a generator change makes old builds stale
TYPES = ("message", "product", "promo", "countdown", "quiz")
KIT_LANGS = ("en", "ru", "uk")
DATA_MAX = 64
REVEAL_DATA = "promo"
PREVIEW_NOW = 1794736800  # widget.json "now" of new widgets: the preview shifts "fresh" times from it

_HEX = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
_ID = re.compile(r"^[A-Za-z0-9_-]{1,16}$")
_IMAGE = re.compile(r"^[\w-][\w.-]*\.svg$")
_SECRET = re.compile(r"(api[_-]?key|secret|password|bot\d{6,}:|bearer\s)", re.I)  # tgkit refuses these
_SVG_UNSAFE = re.compile(r"<\s*(script|image|foreignObject|iframe|style)\b|data:|https?:|javascript:|\son\w+\s*=", re.I)


# ------------------------------------------------------------------ schema

def _f(key: str, label: str, type_: str, **kw: Any) -> dict:
    return {"key": key, "label": label, "type": type_, **kw}


def _text(key: str, label: str, max_: int, *, loc: bool = True, multiline: bool = False, **kw: Any) -> dict:
    out = _f(key, label, "text", max=max_, **kw)
    if loc:
        out["localized"] = True
    if multiline:
        out["multiline"] = True
    return out


def _button(label: str = "Button", help_: str = "") -> list[dict]:
    act = _f("button.action", "When pressed", "action",
             help="Request: asks the bot with up to 64 bytes of data and shows the done text. Link: opens an "
                  "https:// page. Copy: copies a text (empty = the button label).")
    if help_:
        act["help"] = help_
    return [_text("button.label", label, 32, help="Empty hides the button."), act]


_ALIGN = [{"value": "start", "label": "Left"}, {"value": "center", "label": "Center"}, {"value": "end", "label": "Right"}]
_IMAGE_HELP = "An SVG file in the widget folder (inline <svg> only: no <image>, no data: images, no links)."

TYPE_SCHEMA: dict[str, dict] = {
    "message": {
        "title": "Message", "summary": "Picture, title, text and one button.", "icon": "message-square",
        "sections": [{"id": "content", "title": "Content", "fields": [
            _f("image", "Picture", "image", help=_IMAGE_HELP),
            _text("title", "Title", 80),
            _text("text", "Text", 400, multiline=True),
            *_button(),
            _text("footnote", "Footnote", 400, multiline=True, help="Small grey text at the bottom."),
        ]}],
        "states": [{"id": "default", "title": "Ready"}],
    },
    "product": {
        "title": "Product card", "summary": "Photo, name, price with a discount, quantity and a buy button.",
        "icon": "shopping-bag",
        "sections": [{"id": "content", "title": "Product", "fields": [
            _f("image", "Photo", "image", help=_IMAGE_HELP, toggle="show.image"),
            _text("badge", "Badge", 16, toggle="show.badge", help="A short label in the corner, e.g. −20% or New."),
            _f("badgeCorner", "Badge corner", "choice", toggle="show.badge",
               options=[{"value": "left", "label": "Top left"}, {"value": "right", "label": "Top right"}]),
            _text("name", "Name", 80, toggle="show.name"),
            _text("description", "Short description", 400, multiline=True, toggle="show.description"),
            _text("price", "Price", 24, loc=False, toggle="show.price",
                  help="Display only, with the currency (€14.90). The bot decides the real price."),
            _text("oldPrice", "Price before the discount", 24, loc=False, toggle="show.discount",
                  help="Struck through next to the price."),
            _f("quantityMax", "Quantity up to", "number", min=1, max=99, step=1, toggle="show.quantity",
               help="A − / + counter from 1 to this number."),
            *_button("Buy button", "{n} in the request data and the done text is the chosen quantity."),
            _text("footnote", "Footnote", 400, multiline=True, toggle="show.footnote"),
        ]}],
        "states": [{"id": "default", "title": "Ready"}, {"id": "tapped", "title": "After tap"}],
    },
    "promo": {
        "title": "Promo code", "summary": "A coupon that shows or reveals a code; a tap copies it.", "icon": "ticket",
        "sections": [{"id": "content", "title": "Coupon", "fields": [
            _text("title", "Title", 80),
            _text("text", "Text", 400, multiline=True),
            _f("reveal", "Show the code", "choice",
               options=[{"value": "now", "label": "Right away"}, {"value": "tap", "label": "On tap (the bot sends it)"}],
               help="On tap the code is not in the widget: the widget asks the bot (data \"promo\") and shows the "
                    "code from its answer."),
            _text("code", "Code", 24, loc=False,
                  help="With 'on tap' this is what the bot answers (the preview uses it); it is not in the HTML."),
            _text("closedLabel", "Label on the closed coupon", 24, when={"key": "reveal", "eq": "tap"}),
            _text("caption", "Under the coupon", 40),
            _f("look", "Coupon look", "choice", options=[
                {"value": "dashed", "label": "Dashed"}, {"value": "filled", "label": "Filled"},
                {"value": "ticket", "label": "Ticket"}]),
            *_button(),
        ]}],
        "states": [{"id": "closed", "title": "Closed"}, {"id": "revealed", "title": "Revealed"},
                   {"id": "copied", "title": "Copied"}],
    },
    "countdown": {
        "title": "Countdown offer", "summary": "A deadline with a live timer and a text after it ends.", "icon": "timer",
        "sections": [{"id": "content", "title": "Offer", "fields": [
            _text("title", "Title", 80),
            _text("text", "Text", 400, multiline=True),
            _f("deadline", "Ends at", "datetime", help="Entered in your time zone, stored as an absolute time."),
            _text("finished", "Text after the end", 60),
            _f("digits", "Digits look", "choice", options=[
                {"value": "filled", "label": "Filled"}, {"value": "outline", "label": "Outline"},
                {"value": "plain", "label": "Plain"}]),
            *_button(),
            _f("hideButton", "Hide the button after the end", "toggle"),
        ]}],
        "states": [{"id": "running", "title": "Running"}, {"id": "finished", "title": "Finished"}],
    },
    "quiz": {
        "title": "Quiz", "summary": "Up to five questions, one per screen, then a result and one button.",
        "icon": "list-checks",
        "sections": [
            {"id": "questions", "title": "Questions", "fields": [
                _f("questions", "Questions", "list", minItems=1, maxItems=5, item={"fields": [
                    _text("text", "Question", 80),
                    _f("answers", "Answers", "list", minItems=2, maxItems=4,
                       item={"fields": [_text("text", "Answer", 32)]}),
                ]}, help="Every question and answer keeps its id; the final request sends the chosen answer ids."),
            ]},
            {"id": "result", "title": "Result", "fields": [
                _text("result", "Result text", 160, multiline=True),
                *_button("Final button", "A request sends its data + ':' + the chosen answer ids joined by '.'; "
                                         "the bot decides the result and may answer a text."),
                _f("again", "Offer \u201cplay again\u201d", "toggle"),
            ]},
        ],
        "states": [*({"id": f"q{n}", "title": f"Question {n}"} for n in range(1, 6)), {"id": "result", "title": "Result"}],
    },
}

STYLE_SECTIONS = [
    {"id": "block", "title": "Block", "fields": [
        _f("block.fill", "Card background", "toggle", help="Fill the block with the theme's card colour."),
        _f("block.radius", "Corner", "number", min=0, max=32, step=1, unit="px"),
        _f("block.border", "Border", "number", min=0, max=4, step=1, unit="px"),
        _f("block.padding", "Padding", "number", min=0, max=24, step=1, unit="px"),
        _f("block.gap", "Gap between blocks", "number", min=2, max=20, step=1, unit="px"),
        _f("block.align", "Alignment", "choice", options=_ALIGN, help="Mirrors in right-to-left languages."),
    ]},
    {"id": "text", "title": "Text", "fields": [
        _f("text.title", "Title size", "choice", options=[
            {"value": "s", "label": "S"}, {"value": "m", "label": "M"}, {"value": "l", "label": "L"}]),
        _f("text.body", "Text size", "choice", options=[
            {"value": "small", "label": "Small"}, {"value": "normal", "label": "Normal"}, {"value": "large", "label": "Large"}]),
    ]},
    {"id": "button", "title": "Button", "fields": [
        _f("button.look", "Look", "choice", options=[
            {"value": "native", "label": "Telegram"}, {"value": "filled", "label": "Filled"},
            {"value": "outline", "label": "Outline"}], help="Telegram: the app draws its own button."),
        _f("button.radius", "Corner", "number", min=0, max=24, step=1, unit="px",
           when={"key": "button.look", "in": ["filled", "outline"]}),
        _f("button.height", "Height", "choice", when={"key": "button.look", "in": ["filled", "outline"]}, options=[
            {"value": "low", "label": "Low"}, {"value": "normal", "label": "Normal"}, {"value": "high", "label": "High"}]),
        _f("button.width", "Width", "choice", options=[
            {"value": "full", "label": "Full"}, {"value": "half", "label": "Half"}, {"value": "auto", "label": "Fit text"}]),
        _f("button.align", "Position", "choice", options=_ALIGN, when={"key": "button.width", "in": ["half", "auto"]}),
    ]},
    {"id": "image", "title": "Picture", "fields": [
        _f("image.full", "Full width", "toggle"),
        _f("image.aspect", "Shape", "choice", when={"key": "image.full", "eq": True}, options=[
            {"value": "auto", "label": "As drawn"}, {"value": "16:9", "label": "16:9"}, {"value": "4:3", "label": "4:3"},
            {"value": "1:1", "label": "Square"}]),
        _f("image.width", "Width", "number", min=16, max=200, step=1, unit="px", when={"key": "image.full", "eq": False}),
        _f("image.align", "Position", "choice", options=_ALIGN, when={"key": "image.full", "eq": False}),
        _f("image.radius", "Corner", "number", min=0, max=48, step=1, unit="px"),
    ]},
    {"id": "motion", "title": "Motion", "fields": [
        _f("animation", "Animation", "choice", options=[
            {"value": "none", "label": "None"}, {"value": "calm", "label": "Calm"}, {"value": "lively", "label": "Lively"}],
           help="Entrance and screen changes; off when the device asks for reduced motion."),
    ]},
]


def _preset(block, text, button, image, animation, colors=None) -> dict:
    return {"block": block, "text": text, "button": button, "image": image, "animation": animation,
            "colors": colors or {"light": {}, "dark": {}}}


PRESETS = [
    {"id": "telegram", "title": "Telegram", "values": _preset(
        {"fill": False, "radius": 0, "border": 0, "padding": 0, "gap": 8, "align": "start"},
        {"title": "m", "body": "normal"},
        {"look": "native", "radius": 8, "height": "normal", "width": "full", "align": "start"},
        {"full": True, "aspect": "auto", "width": 96, "align": "start", "radius": 8}, "none")},
    {"id": "card", "title": "Card", "values": _preset(
        {"fill": True, "radius": 14, "border": 0, "padding": 12, "gap": 8, "align": "start"},
        {"title": "m", "body": "normal"},
        {"look": "filled", "radius": 10, "height": "normal", "width": "full", "align": "start"},
        {"full": True, "aspect": "16:9", "width": 96, "align": "start", "radius": 10}, "calm")},
    {"id": "soft", "title": "Soft", "values": _preset(
        {"fill": True, "radius": 22, "border": 0, "padding": 16, "gap": 10, "align": "center"},
        {"title": "l", "body": "normal"},
        {"look": "filled", "radius": 20, "height": "high", "width": "full", "align": "center"},
        {"full": False, "aspect": "auto", "width": 120, "align": "center", "radius": 20}, "lively")},
    {"id": "contrast", "title": "Contrast", "values": _preset(
        {"fill": False, "radius": 8, "border": 2, "padding": 12, "gap": 10, "align": "start"},
        {"title": "l", "body": "large"},
        {"look": "filled", "radius": 6, "height": "high", "width": "full", "align": "start"},
        {"full": True, "aspect": "auto", "width": 96, "align": "start", "radius": 6}, "none",
        {"light": {"text": "#000000", "hint": "#333333", "border": "#000000", "button": "#000000", "buttonText": "#ffffff"},
         "dark": {"text": "#ffffff", "hint": "#cccccc", "border": "#ffffff", "button": "#ffffff", "buttonText": "#000000"}})},
]
PRESET_IDS = [p["id"] for p in PRESETS]

COLOR_SLOTS = {
    "common": [{"key": "bg", "label": "Background"}, {"key": "text", "label": "Title and text"},
               {"key": "hint", "label": "Footnote and old price"}, {"key": "button", "label": "Button"},
               {"key": "buttonText", "label": "Button label"}, {"key": "border", "label": "Border"}],
    "product": [{"key": "badge", "label": "Badge"}, {"key": "badgeText", "label": "Badge text"},
                {"key": "counter", "label": "Quantity buttons"}, {"key": "counterText", "label": "Quantity signs"}],
    "promo": [{"key": "coupon", "label": "Coupon"}, {"key": "couponText", "label": "Code"}],
    "countdown": [{"key": "digits", "label": "Digits"}, {"key": "digitsText", "label": "Digit labels"}],
    "quiz": [{"key": "answer", "label": "Answers"}, {"key": "answerText", "label": "Answer labels"}],
}


def slots_for(type_: str) -> list[str]:
    return [s["key"] for s in COLOR_SLOTS["common"] + COLOR_SLOTS.get(type_, [])]


# ------------------------------------------------------------------ defaults

_EX = "https://example.com"
TEXTS: dict[str, dict[str, dict]] = {
    "message": {
        "en": {"title": "Welcome aboard", "text": "Your account is ready. Tap the button and the bot will send a "
               "two-minute tour of what it can do.", "button": "Show me around", "done": "Sent, check the chat"},
        "ru": {"title": "Добро пожаловать", "text": "Аккаунт готов. Нажмите кнопку, и бот пришлёт короткий тур "
               "по своим возможностям.", "button": "Показать", "done": "Отправили, загляните в чат"},
        "uk": {"title": "Ласкаво просимо", "text": "Акаунт готовий. Натисніть кнопку, і бот надішле короткий тур "
               "своїми можливостями.", "button": "Показати", "done": "Надіслали, загляньте в чат"},
    },
    "product": {
        "en": {"name": "Coffee beans, 250 g", "description": "Ethiopia Yirgacheffe, light roast. Jasmine, lemon and honey.",
               "badge": "−20%", "button": "Add to cart", "done": "Added {n} to the cart", "footnote": "Free delivery from €30"},
        "ru": {"name": "Кофе в зёрнах, 250 г", "description": "Эфиопия Иргачефе, светлая обжарка. Жасмин, лимон и мёд.",
               "badge": "−20%", "button": "В корзину", "done": "В корзине: {n} шт.", "footnote": "Бесплатная доставка от €30"},
        "uk": {"name": "Кава в зернах, 250 г", "description": "Ефіопія Іргачеффе, світле обсмаження. Жасмин, лимон і мед.",
               "badge": "−20%", "button": "У кошик", "done": "У кошику: {n} шт.", "footnote": "Безкоштовна доставка від €30"},
    },
    "promo": {
        "en": {"title": "−20% on your next order", "text": "Enter the code at checkout. Valid until Sunday.",
               "closedLabel": "Tap to reveal", "caption": "One use per customer", "button": "Go to the shop"},
        "ru": {"title": "−20% на следующий заказ", "text": "Введите код при оформлении. Действует до воскресенья.",
               "closedLabel": "Нажмите, чтобы открыть", "caption": "Один раз на покупателя", "button": "В магазин"},
        "uk": {"title": "−20% на наступне замовлення", "text": "Введіть код під час оформлення. Діє до неділі.",
               "closedLabel": "Натисніть, щоб відкрити", "caption": "Один раз на покупця", "button": "До магазину"},
    },
    "countdown": {
        "en": {"title": "Flash sale: −30% on coffee gear", "text": "Grinders, kettles and drippers. This week only.",
               "finished": "The sale is over. See you at the next one!", "button": "Shop the sale"},
        "ru": {"title": "Распродажа: −30% на всё для кофе", "text": "Кофемолки, чайники и воронки. Только эту неделю.",
               "finished": "Распродажа закончилась. До следующей!", "button": "К распродаже"},
        "uk": {"title": "Розпродаж: −30% на все для кави", "text": "Кавомолки, чайники та лійки. Лише цього тижня.",
               "finished": "Розпродаж завершився. До наступного!", "button": "До розпродажу"},
    },
    "quiz": {
        "en": {"q": [("How do you take your coffee?", ["Black", "With milk", "Iced"]),
                     ("When do you need it most?", ["Morning", "After lunch", "Late at night"]),
                     ("Pick a flavour", ["Chocolate", "Fruity", "Nutty"])],
               "result": "Thanks! Send your answers and the bot will pick a coffee for you.",
               "button": "Get my match", "done": "Sent! Your match is in the chat."},
        "ru": {"q": [("Какой кофе вы пьёте?", ["Чёрный", "С молоком", "Холодный"]),
                     ("Когда он нужнее всего?", ["Утром", "После обеда", "Поздно вечером"]),
                     ("Выберите вкус", ["Шоколад", "Фрукты", "Орехи"])],
               "result": "Спасибо! Отправьте ответы, и бот подберёт вам кофе.",
               "button": "Подобрать кофе", "done": "Готово! Подборка в чате."},
        "uk": {"q": [("Яку каву ви п'єте?", ["Чорну", "З молоком", "Холодну"]),
                     ("Коли вона найпотрібніша?", ["Зранку", "Після обіду", "Пізно ввечері"]),
                     ("Оберіть смак", ["Шоколад", "Фрукти", "Горіхи"])],
               "result": "Дякуємо! Надішліть відповіді, і бот підбере вам каву.",
               "button": "Підібрати каву", "done": "Готово! Добірка в чаті."},
    },
}

# Chrome strings of the generated widgets (the kit's i18n.js has the request outcomes).
CHROME = {
    "en": {"cp": "Copied", "tc": "Tap the code to copy it", "qn": "Question # of %", "ag": "Play again",
           "u0": "days", "u1": "hours", "u2": "min", "u3": "sec"},
    "ru": {"cp": "Скопировано", "tc": "Нажмите на код, чтобы скопировать", "qn": "Вопрос # из %", "ag": "Пройти ещё раз",
           "u0": "дн", "u1": "ч", "u2": "мин", "u3": "сек"},
    "uk": {"cp": "Скопійовано", "tc": "Натисніть на код, щоб скопіювати", "qn": "Питання # з %", "ag": "Пройти ще раз",
           "u0": "дн", "u1": "год", "u2": "хв", "u3": "с"},
}


def _locs(locales: list[str] | None) -> list[str]:
    return list(dict.fromkeys(locales or ["en"]))


def defaults(type_: str, locales: list[str] | None = None, now: int | None = None) -> dict:
    """Example content of a type in the given locales (unknown locales get the English text)."""
    if type_ not in TYPES:
        raise ValueError(f"unknown builder type {type_!r}")
    locs = _locs(locales)
    tx = TEXTS[type_]

    def m(key: str) -> dict:
        return {loc: (tx.get(loc) or tx["en"])[key] for loc in locs}

    if type_ == "message":
        return {"image": "", "title": m("title"), "text": m("text"), "footnote": {},
                "button": {"label": m("button"), "action": {"kind": "request", "data": "tour", "done": m("done")}}}
    if type_ == "product":
        return {"image": "", "badge": m("badge"), "badgeCorner": "right", "name": m("name"),
                "description": m("description"), "price": "€14.90", "oldPrice": "€18.50", "quantityMax": 10,
                "footnote": m("footnote"),
                "show": {"image": True, "badge": True, "name": True, "description": True, "price": True,
                         "discount": True, "quantity": True, "footnote": True},
                "button": {"label": m("button"), "action": {"kind": "request", "data": "add:{n}", "done": m("done")}}}
    if type_ == "promo":
        return {"title": m("title"), "text": m("text"), "reveal": "tap", "code": "SPRING20",
                "closedLabel": m("closedLabel"), "caption": m("caption"), "look": "dashed",
                "button": {"label": m("button"), "action": {"kind": "link", "url": f"{_EX}/shop"}}}
    if type_ == "countdown":
        base = int(now if now is not None else time.time())
        return {"title": m("title"), "text": m("text"), "deadline": (base // 3600 + 7 * 24) * 3600,
                "finished": m("finished"), "digits": "filled", "hideButton": True,
                "button": {"label": m("button"), "action": {"kind": "link", "url": f"{_EX}/sale"}}}
    questions = []
    for qi in range(3):
        answers = [{"id": f"a{qi * 3 + ai + 1}",
                    "text": {loc: (tx.get(loc) or tx["en"])["q"][qi][1][ai] for loc in locs}} for ai in range(3)]
        questions.append({"id": f"q{qi + 1}", "text": {loc: (tx.get(loc) or tx["en"])["q"][qi][0] for loc in locs},
                          "answers": answers})
    return {"questions": questions, "result": m("result"), "again": True,
            "button": {"label": m("button"), "action": {"kind": "request", "data": "quiz", "done": m("done")}}}


def default_style(preset: str = "telegram") -> dict:
    values = copy.deepcopy(_preset_values(preset))
    values.pop("colors", None)
    return {"preset": preset, "custom": values, "palette": "per-theme", "colors": {"light": {}, "dark": {}}}


def default_config(type_: str, locales: list[str] | None = None, now: int | None = None) -> dict:
    return {"type": type_, "version": VERSION, "content": defaults(type_, locales, now), "style": default_style()}


def schema(locales: list[str] | None = None) -> dict:
    """The form description for POST /api/widget/builder-schema."""
    types = {}
    for t in TYPES:
        types[t] = {**copy.deepcopy(TYPE_SCHEMA[t]), "defaults": defaults(t, locales or list(KIT_LANGS))}
    return {"version": VERSION, "generator": GENERATOR,
            "types": types,
            "style": {"sections": copy.deepcopy(STYLE_SECTIONS), "presets": copy.deepcopy(PRESETS),
                      "colorSlots": copy.deepcopy(COLOR_SLOTS)},
            "limits": {"dataBytes": DATA_MAX, "linkChars": 256, "copyChars": 256, "doneChars": 64},
            "languages": list(KIT_LANGS)}


# ------------------------------------------------------------------ helpers

def _get(obj: Any, path: str) -> Any:
    cur = obj
    for k in path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(k)
    return cur


def _loc(value: Any, lang: str, default_locale: str) -> str:
    """Localized text: the language, else the default locale, else ''. A plain string is every locale's."""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for k in (lang, default_locale):
            if isinstance(value.get(k), str) and value[k].strip():
                return value[k]
    return ""


def _any_text(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    return isinstance(value, dict) and any(isinstance(v, str) and v.strip() for v in value.values())


def _shown(content: dict, name: str) -> bool:
    return _get(content, f"show.{name}") is not False


def _preset_values(pid: str) -> dict:
    return next(p["values"] for p in PRESETS if p["id"] == pid)


def _num(v: Any, lo: float, hi: float, d: float) -> float:
    return min(hi, max(lo, v)) if isinstance(v, (int, float)) and not isinstance(v, bool) else d


def _choice(v: Any, options: tuple, d: str) -> str:
    return v if v in options else d


def effective_style(style: dict | None) -> tuple[dict, dict]:
    """(values, {"light": slots, "dark": slots}) the generator uses: an active preset wins; else the
    author's `custom` over the Telegram preset, and `colors` (shared = the light slots for both)."""
    style = style if isinstance(style, dict) else {}
    pid = style.get("preset")
    if pid in PRESET_IDS:
        vals = copy.deepcopy(_preset_values(pid))
        colors = vals.pop("colors")
        return vals, {"light": dict(colors.get("light") or {}), "dark": dict(colors.get("dark") or {})}
    vals = copy.deepcopy(_preset_values("telegram"))
    vals.pop("colors")
    custom = style.get("custom") if isinstance(style.get("custom"), dict) else {}
    for sec in ("block", "text", "button", "image"):
        if isinstance(custom.get(sec), dict):
            vals[sec].update({k: v for k, v in custom[sec].items() if v is not None})
    if custom.get("animation") is not None:
        vals["animation"] = custom["animation"]
    raw = style.get("colors") if isinstance(style.get("colors"), dict) else {}
    light = dict(raw.get("light") or {}) if isinstance(raw.get("light"), dict) else {}
    dark = dict(raw.get("dark") or {}) if isinstance(raw.get("dark"), dict) else {}
    if style.get("palette") == "shared":
        dark = dict(light)
    return vals, {"light": light, "dark": dark}


def _js(v: Any) -> str:
    """A JS literal safe inside <script> and outside the build's /*@lang*/ markers."""
    s = json.dumps(v, ensure_ascii=False, separators=(",", ":"))
    return (s.replace("</", "<\\/").replace("<!--", "<\\!--").replace("*/", "*\\/").replace("/*", "\\/*")
            .replace("\u2028", "\\u2028").replace("\u2029", "\\u2029"))


def _esc(s: str) -> str:
    return _html.escape(s, quote=True)


def clean_svg(text: str) -> str:
    text = re.sub(r"^\s*<\?xml[^>]*>\s*", "", text.replace("\r\n", "\n"))
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = re.sub(r'\s+xmlns(:\w+)?="[^"]*"', "", text)
    return text.strip()


# ------------------------------------------------------------------ generator

_J = {"start": "flex-start", "center": "center", "end": "flex-end"}
_TITLE = {"s": "1em", "m": "1.13em", "l": "1.33em"}
_BODY = {"small": ".9em", "normal": "1em", "large": "1.1em"}
_HEIGHT = {"low": 32, "normal": 38, "high": 46}
_ASPECT = {"16:9": "16/9", "4:3": "4/3", "1:1": "1"}


class _Gen:
    def __init__(self, config: dict, langs: list[str], default_locale: str, assets: dict[str, str],
                 preview: tuple[dict | None, str] = (None, "")) -> None:
        self.type = config["type"]
        self.preview = preview
        self.c = config.get("content") if isinstance(config.get("content"), dict) else {}
        self.langs, self.dl, self.assets = langs, default_locale, assets
        self.v, self.colors = effective_style(config.get("style"))
        b, bt, im = self.v["block"], self.v["button"], self.v["image"]
        self.align = _choice(b.get("align"), ("start", "center", "end"), "start")
        self.look = _choice(bt.get("look"), ("native", "filled", "outline"), "native")
        self.anim = _choice(self.v.get("animation"), ("none", "calm", "lively"), "none")
        self.radius = int(_num(bt.get("radius"), 0, 24, 8)) if self.look != "native" else 10
        self.im = im
        self.strings: dict[str, dict[str, str]] = {lang: {} for lang in langs}
        self.fill: list[str] = []
        self.markup: list[str] = []
        self.css: dict[str, str] = {}
        self.init: list[str] = []
        self.draw: list[str] = []
        self.status = False
        self.request = False

    # strings and text blocks
    def put(self, key: str, value: Any, force: bool = False) -> bool:
        vals = {lang: _loc(value, lang, self.dl) for lang in self.langs}
        if not force and not any(v.strip() for v in vals.values()):
            return False
        for lang, s in vals.items():
            self.strings[lang][key] = s
        return True

    def chrome(self, *keys: str) -> None:
        for lang in self.langs:
            table = CHROME.get(lang, CHROME["en"])
            for k in keys:
                self.strings[lang][k] = table[k]

    def para(self, key: str, value: Any, cls: str) -> bool:
        if not self.put(key, value):
            return False
        self.markup.append(f'<p class="{cls}" id="{key}"></p>')
        self.fill.append(key)
        self.css[cls] = {"t": f".t{{font-weight:600;font-size:{_TITLE.get(self.v['text'].get('title'), '1.13em')};"
                              "line-height:1.25}",
                         "x": f".x{{font-size:{_BODY.get(self.v['text'].get('body'), '1em')};white-space:pre-line}}",
                         "f": ".f{font-size:.87em;color:var(--c-hint);white-space:pre-line}"}[cls]
        return True

    # actions
    def action_js(self, n: str | None = None, ids: str | None = None) -> str:
        a = _get(self.c, "button.action") or {}
        kind = a.get("kind") if isinstance(a, dict) else None
        if kind == "link":
            return f"W&&W.openLink({_js(str(a.get('url') or ''))});"
        if kind == "copy":
            text = a.get("text") if _any_text(a.get("text")) else _get(self.c, "button.label")
            self.put("ct", text, force=True)
            self.chrome("cp")
            self.status = True
            return 'W&&W.copyText(K.t("ct"));K.st(K.t("cp"),"ok");'
        self.request = self.status = True
        self.put("dn", a.get("done") if isinstance(a, dict) else "", force=True)
        data = _js(str(a.get("data") or "") if isinstance(a, dict) else "")
        if ids:
            return f'K.ask({data}+":"+{ids},{{done:K.t("dn")}});'
        if n:
            return f'K.ask({data}.split("{{n}}").join({n}),{{done:K.t("dn").split("{{n}}").join({n})}});'
        return f'K.ask({data},{{done:K.t("dn")}});'

    def button(self, n: str | None = None, ids: str | None = None, pre: str = "") -> bool:
        if not self.put("go", _get(self.c, "button.label")):
            return False
        self.markup.append('<button class="bt" id="go"></button>')
        self.fill.append("go")
        self.init.append(f'K.$("go").onclick=function(){{{pre}{self.action_js(n, ids)}}};')
        if self.request:
            self.draw.append('K.$("go").disabled=K.busy||!K.can();')
        width = _choice(self.v["button"].get("width"), ("full", "half", "auto"), "full")
        place = "stretch" if width == "full" else _J[_choice(self.v["button"].get("align"), tuple(_J), self.align)]
        rule = f".bt{{align-self:{place}" + (";width:50%" if width == "half" else "")
        if self.look == "native":
            if self._set("button") or self._set("buttonText"):
                rule += ";background:var(--c-button);color:var(--c-buttonText)"
        else:
            h = _HEIGHT.get(self.v["button"].get("height"), 38)
            rule += (f";min-height:{h}px;padding:6px 16px;border-radius:{self.radius}px;font:inherit;font-weight:500;"
                     + ("background:var(--c-button);color:var(--c-buttonText);border:0" if self.look == "filled"
                        else "background:none;color:var(--c-button);border:1.5px solid var(--c-button)"))
        if self.anim == "lively":
            rule += ";transition:transform .15s}.bt:active{transform:scale(.96)"
        self.css["bt"] = rule + "}"
        return True

    def status_line(self) -> None:
        if self.status:
            self.markup.append('<div class="st" id="st"></div>')

    def _set(self, slot: str) -> bool:
        return any(isinstance(self.colors[t].get(slot), str) and _HEX.match(self.colors[t][slot]) for t in ("light", "dark"))

    def image(self, badge: str = "") -> bool:
        name = self.c.get("image")
        if not isinstance(name, str) or not name or not _shown(self.c, "image") or name not in self.assets:
            return False
        svg = clean_svg(self.assets[name])
        if not svg.startswith("<svg") or _SVG_UNSAFE.search(svg):
            return False
        im = self.im
        full = im.get("full") is not False
        aspect = _choice(im.get("aspect"), tuple(_ASPECT) + ("auto",), "auto") if full else "auto"
        if aspect != "auto":
            svg = re.sub(r"<svg\b", '<svg preserveAspectRatio="xMidYMid slice"', svg, count=1)
        self.markup.append(f'<div class="im">{svg}{badge}</div>')
        size = ("align-self:stretch" + (f";aspect-ratio:{_ASPECT[aspect]}" if aspect != "auto" else "") if full else
                f"align-self:{_J[_choice(im.get('align'), tuple(_J), self.align)]};width:{int(_num(im.get('width'), 16, 200, 96))}px;"
                "max-width:100%")
        self.css["im"] = (f".im{{position:relative;line-height:0;overflow:hidden;border-radius:"
                          f"{int(_num(im.get('radius'), 0, 48, 8))}px;{size}}}"
                          f".im svg{{display:block;width:100%;height:{'100%' if aspect != 'auto' else 'auto'}}}")
        return True

    def fx(self, base: str, toggle: str) -> str:
        """JS expression for a class that restarts the entrance animation when `toggle` changes."""
        return f'"{base} "+({toggle}?"fa":"fb")' if self.anim != "none" else f'"{base}"'

    # types
    def gen_message(self) -> None:
        self.image()
        self.para("ti", self.c.get("title"), "t")
        self.para("tx", self.c.get("text"), "x")
        self.button()
        self.status_line()
        self.para("ft", self.c.get("footnote"), "f")

    def gen_product(self) -> None:
        c = self.c
        corner = "right" if c.get("badgeCorner") != "left" else "left"
        badge = _shown(c, "badge") and self.put("bd", c.get("badge"))
        if badge:
            self.fill.append("bd")
        tag = '<span class="bd" id="bd"></span>' if badge else ""
        on_image = bool(badge and self.image(tag))
        if badge:
            pos = (f".im .bd{{position:absolute;top:8px;{corner}:8px}}" if on_image else
                   f".bd{{align-self:{'flex-start' if corner == 'left' else 'flex-end'}}}")
            self.css["bd"] = (".bd{background:var(--c-badge);color:var(--c-badgeText);font-size:.8em;font-weight:600;"
                              "line-height:1.7;padding:0 8px;border-radius:999px}" + pos)
            if not on_image:
                self.markup.append(tag)
        elif not badge:
            self.image()
        if _shown(c, "name"):
            self.para("nm", c.get("name"), "t")
        if _shown(c, "description"):
            self.para("ds", c.get("description"), "x")
        price = str(c.get("price") or "").strip() if _shown(c, "price") else ""
        old = str(c.get("oldPrice") or "").strip() if _shown(c, "discount") else ""
        if price or old:
            row = f"<b>{_esc(price or old)}</b>" + (f"<s>{_esc(old)}</s>" if price and old else "")
            self.markup.append(f'<p class="pr">{row}</p>')
            self.css["pr"] = (f".pr{{display:flex;flex-wrap:wrap;gap:8px;align-items:baseline;justify-content:{_J[self.align]}}}"
                              ".pr b{font-size:1.2em;font-weight:600}" + (".pr s{color:var(--c-hint)}" if price and old else ""))
        uses_n = "{n}" in str(_get(c, "button.action.data") or "")
        qty = _shown(c, "quantity") and _get(c, "button.label") is not None and _any_text(_get(c, "button.label"))
        if qty:
            mx = int(_num(c.get("quantityMax"), 1, 99, 10))
            self.markup.append('<div class="qt"><button class="qb" id="mi">\u2212</button><b id="q"></b>'
                               '<button class="qb" id="pl">+</button></div>')
            self.css["qt"] = (f".qt{{display:flex;align-items:center;gap:12px;justify-content:{_J[self.align]}}}"
                              ".qb{min-width:36px;min-height:34px;padding:0;border:0;border-radius:999px;"
                              "background:var(--c-counter);color:var(--c-counterText);font:inherit;font-size:1.15em}"
                              ".qt b{min-width:1.5em;text-align:center;font-weight:600}")
            self.init.append(f"var q=1,M={mx};")
            self.init.append('K.$("mi").onclick=function(){q--;draw();};')
            self.init.append('K.$("pl").onclick=function(){q++;draw();};')
            self.draw.append('K.$("q").textContent=q;K.$("mi").disabled=q<2;K.$("pl").disabled=q>=M;')
        if self.button(n=("q" if qty else '"1"') if uses_n else None) and self.request:
            n = "s.n" if uses_n else ""
            done = f'K.t("dn").split("{{n}}").join({n})' if n else 'K.t("dn")'
            self.draw.append(f'var s=K.S.chatData;if(s&&s.n&&!K.busy&&!K.$("st").textContent)K.st({done},"ok");')
        self.status_line()
        if _shown(c, "footnote"):
            self.para("ft", c.get("footnote"), "f")

    def gen_promo(self) -> None:
        c = self.c
        self.para("ti", c.get("title"), "t")
        self.para("tx", c.get("text"), "x")
        tap = c.get("reveal") == "tap"
        code = "" if tap else str(c.get("code") or "")
        if tap:
            self.put("cl", c.get("closedLabel") or {lang: "?" for lang in self.langs}, force=True)
            self.chrome("tc")
        self.chrome("cp")
        self.status = True
        self.markup.append('<button class="cp" id="cp"></button>')
        look = _choice(c.get("look"), ("dashed", "filled", "ticket"), "dashed")
        paint = ("background:none;color:var(--c-couponText);border:2px dashed var(--c-coupon)" if look == "dashed" else
                 "background:var(--c-coupon);color:var(--c-couponText);border:0"
                 + (";outline:2px dashed var(--c-couponText);outline-offset:-6px" if look == "ticket" else ""))
        self.css["cp"] = (f".cp{{min-height:48px;padding:8px 12px;border-radius:{self.radius}px;font:inherit;"
                          "font-family:ui-monospace,monospace;font-size:1.25em;font-weight:600;letter-spacing:.08em;"
                          f"{paint}}}.cp.c{{font-family:inherit;font-size:1em;letter-spacing:0}}")
        self.init.append(f'var c={_js(code)},cp=K.$("cp");')
        ask = ('K.ask("promo",{done:K.t("tc"),then:function(r){if(r.c)c=r.c;}});' if tap else "")
        self.init.append(f'cp.onclick=function(){{if(c){{W&&W.copyText(c);K.st(K.t("cp"),"ok");}}{"else " + ask if ask else ""}}};')
        cls = '"cp"+(c?"' + (" fa" if self.anim != "none" else "") + '":" c")'
        self.draw.append('var s=K.S.chatData;if(s&&s.c)c=s.c;cp.textContent=c||K.t("cl");'
                         f'cp.className={cls};' + ('cp.disabled=!c&&(K.busy||!K.can());' if tap else "")
                         + 'if(s&&s.cp&&!K.busy&&!K.$("st").textContent)K.st(K.t("cp"),"ok");')
        self.para("cn", c.get("caption"), "f")
        self.status_line()
        self.status = False  # the button's action must not add a second status line
        self.button()

    def gen_countdown(self) -> None:
        c = self.c
        self.para("ti", c.get("title"), "t")
        self.para("tx", c.get("text"), "x")
        self.chrome("u0", "u1", "u2", "u3")
        units = "".join(f'<span id="w{i}"><b id="v{i}"></b><i id="u{i}"></i></span>' for i in range(4))
        self.fill += ["u0", "u1", "u2", "u3"]
        self.markup.append(f'<div class="cd" id="cd">{units}</div>')
        look = _choice(c.get("digits"), ("filled", "outline", "plain"), "filled")
        paint = {"filled": "background:var(--c-digits);color:var(--c-digitsText)",
                 "outline": "border:1.5px solid var(--c-digits);color:var(--c-digitsText)",
                 "plain": "color:var(--c-digitsText)"}[look]
        self.css["cd"] = (f".cd{{display:flex;gap:6px;justify-content:{_J[self.align]}}}"
                          f".cd span{{min-width:3.2em;padding:6px 4px;border-radius:{min(self.radius, 12)}px;"
                          f"text-align:center;font-size:.8em;{paint}}}"
                          ".cd b{display:block;font-size:1.75em;font-weight:600;line-height:1.15"
                          + (";color:var(--c-digits)" if look == "plain" else "") + "}.cd i{font-style:normal}")
        deadline = int(_num(c.get("deadline"), 0, 4102444800, 0))
        self.init.append(f"var D={deadline},iv=0;")
        fin = self.para("fn", c.get("finished"), "x")
        has_button = self.button()
        self.status_line()
        self.draw.append('var s=K.S.chatData,t=Math.max(0,((s&&s.d)||D)-Date.now()/1000|0),'
                         'v=[t/86400|0,t/3600%24|0,t/60%60|0,t%60],i;')
        self.draw.append('for(i=0;i<4;i++)K.$("v"+i).textContent=(v[i]<10?"0":"")+v[i];')
        self.draw.append('K.$("w0").style.display=v[0]?"":"none";K.$("cd").style.display=t?"":"none";')
        if fin:
            self.draw.append('K.$("fn").style.display=t?"none":"";')
        if has_button and c.get("hideButton") is not False:
            self.draw.append('K.$("go").style.display=t?"":"none";')
        self.draw.append("if(!t&&iv){clearInterval(iv);iv=0;}if(t&&!iv)iv=setInterval(draw,1000);")

    def gen_quiz(self) -> None:
        c = self.c
        qs = [q for q in (c.get("questions") or []) if isinstance(q, dict)]
        ids = []
        for i, q in enumerate(qs):
            self.put(f"q{i}", q.get("text"), force=True)
            ans = [a for a in (q.get("answers") or []) if isinstance(a, dict)]
            for j, a in enumerate(ans):
                self.put(f"q{i}_{j}", a.get("text"), force=True)
            ids.append([str(a.get("id") or f"{i}{j}") for j, a in enumerate(ans)])
        self.chrome("qn")
        gap = int(_num(self.v["block"].get("gap"), 2, 20, 8))
        self.css["g"] = (f".g{{display:flex;flex-direction:column;gap:{gap}px}}"
                         ".pg{height:4px;border-radius:2px;background:var(--c-answer);overflow:hidden}"
                         ".pg i{display:block;height:100%;background:var(--c-button)"
                         + (";transition:width .3s" if self.anim != "none" else "") + "}"
                         ".ol{display:flex;flex-direction:column;gap:6px}"
                         f".o{{min-height:40px;padding:8px 12px;border:0;border-radius:{self.radius}px;"
                         "background:var(--c-answer);color:var(--c-answerText);font:inherit;text-align:inherit}")
        self.css.setdefault("f", ".f{font-size:.87em;color:var(--c-hint);white-space:pre-line}")
        self.css.setdefault("t", f".t{{font-weight:600;font-size:{_TITLE.get(self.v['text'].get('title'), '1.13em')};"
                                 "line-height:1.25}")
        self.markup.append('<div class="g" id="qz"><p class="f" id="qn"></p><div class="pg"><i id="pb"></i></div>'
                           '<p class="t" id="qq"></p><div class="ol" id="an"></div></div>')
        self.markup.append('<div class="g" id="rs">')
        self.para("rt", c.get("result"), "x")
        self.init.append(f'var Q={_js(ids)},i=0,A=[],re=0,qz=K.$("qz"),rs=K.$("rs");')
        self.button(ids='(i<Q.length&&s&&s.a?s.a:A.join("."))', pre="var s=K.S.chatData;")
        if c.get("again") is not False:
            self.chrome("ag")
            self.fill.append("ag")
            self.markup.append('<button class="o" id="ag"></button>')
            self.init.append('K.$("ag").onclick=function(){i=0;A=[];re=1;K.st("");draw();};')
        self.markup.append("</div>")
        self.status_line()
        self.draw.append('var s=K.S.chatData,e=i>=Q.length||!!(s&&s.a&&!re),an=K.$("an");'
                         'qz.style.display=e?"none":"";rs.style.display=e?"":"none";')
        self.draw.append("if(e)return;")
        self.draw.append('K.$("qn").textContent=K.t("qn").replace("#",i+1).replace("%",Q.length);'
                         'K.$("pb").style.width=100*i/Q.length+"%";K.$("qq").textContent=K.t("q"+i);an.innerHTML="";')
        self.draw.append('Q[i].forEach(function(a,j){var b=K.h("button","o",K.t("q"+i+"_"+j));'
                         'b.onclick=function(){A[i]=a;i++;draw();};an.appendChild(b);});')
        if self.anim != "none":
            self.draw.append(f"qz.className={self.fx('g', 'i%2')};")

    # assembly
    def render(self) -> str:
        getattr(self, f"gen_{self.type}")()
        b = self.v["block"]
        border = int(_num(b.get("border"), 0, 4, 0))
        rules = [f".b{{position:relative;display:flex;flex-direction:column;gap:{int(_num(b.get('gap'), 2, 20, 8))}px;"
                 f"padding:{int(_num(b.get('padding'), 0, 24, 0))}px;border-radius:{int(_num(b.get('radius'), 0, 32, 0))}px;"
                 "background:var(--c-bg);color:var(--c-text);"
                 f"text-align:{self.align}" + (f";border:{border}px solid var(--c-border)" if border else "") + "}",
                 ".b>*,.g>*{margin:0}", *self.css.values()]
        if self.anim != "none":
            d, ease, frm = ((".3s", "ease-out", "translateY(6px)") if self.anim == "calm"
                            else (".45s", "cubic-bezier(.2,1.4,.4,1)", "scale(.92)"))
            rules.append(f".fa{{animation:fa {d} {ease}}}.fb{{animation:fb {d} {ease}}}"
                         f"@keyframes fa{{from{{opacity:0;transform:{frm}}}}}@keyframes fb{{from{{opacity:0;transform:{frm}}}}}")
        css = "\n".join(rules)
        css = f".k{{{self._vars(css)}}}\n" + css
        cls = "b fa" if self.anim != "none" else "b"
        out = [f"<!-- Generated by the bot-ui visual builder ({GENERATOR}, {self.type}). Edit it in the Studio form, "
               "or eject to edit the code. -->",
               "<style>", "/*@kit tokens.css*/", css + "\n</style>",
               '<div class="k">', f'<div class="{cls}">', *self.markup, "</div>", "</div>",
               "<!--@kit runtime.js-->", "<!--@kit i18n.js-->", "<script>"]
        for lang in self.langs:
            out.append(f"/*@lang {lang}*/K.add({{{lang}:{_js(self.strings[lang])}}});/*@end*/")
        if self.fill:
            out.append(f'{_js(self.fill)}.forEach(function(i){{var e=K.$(i),t=K.t(i);e.textContent=t;'
                       'if(!t)e.style.display="none";});')
        out += self.init
        data, js = self.preview
        if data is not None or js:  # preview builds only: the state chosen in the Studio
            out.append("/* preview state */" + (f'K.take("chatData",{_js(data)});' if data is not None else "") + js)
        out.append("function draw(){" + "".join(self.draw) + "}")
        out.append("K.start(draw);")
        out.append("</script>")
        return "\n".join(out) + "\n"

    def _vars(self, css: str) -> str:
        """Definitions of every --c-* slot the CSS reads (and the slots their defaults read)."""
        look = self.c.get("look")
        digits = self.c.get("digits")
        defaults = {
            "bg": "var(--k-sec)" if self.v["block"].get("fill") else "transparent",
            "text": "var(--k-tx)", "hint": "var(--k-hint)", "button": "var(--k-btn)", "buttonText": "var(--k-btx)",
            "border": "var(--k-sep)", "badge": "var(--k-bad)", "badgeText": "var(--k-btx)",
            "counter": "rgba(128,128,128,.16)", "counterText": "var(--c-text)",
            "answer": "rgba(128,128,128,.16)", "answerText": "var(--c-text)",
            "coupon": "var(--k-btn)", "couponText": "var(--c-text)" if look not in ("filled", "ticket") else "var(--k-btx)",
            "digits": "var(--c-text)" if digits == "plain" else "var(--k-btn)",
            "digitsText": {"filled": "var(--k-btx)", "outline": "var(--c-text)", "plain": "var(--c-hint)"}.get(digits, "var(--k-btx)"),
        }
        need, todo = [], re.findall(r"var\(--c-(\w+)\)", css)
        while todo:
            s = todo.pop(0)
            if s in need or s not in defaults:
                continue
            need.append(s)
            todo += re.findall(r"var\(--c-(\w+)\)", defaults[s])
        out = []
        for s in sorted(need):
            lv, dv = (self.colors[t].get(s) for t in ("light", "dark"))
            lv = lv if isinstance(lv, str) and _HEX.match(lv) else None
            dv = dv if isinstance(dv, str) and _HEX.match(dv) else None
            value = defaults[s] if lv is None and dv is None else f"light-dark({lv or defaults[s]},{dv or defaults[s]})"
            out.append(f"--c-{s}:{value}")
        return ";".join(out)


def content_languages(config: dict, default_locale: str = "en") -> list[str]:
    """Every locale that any localized text of the content names, default locale first."""
    found: list[str] = [default_locale]

    def walk(v: Any) -> None:
        if isinstance(v, dict):
            for k, x in v.items():
                if isinstance(x, str) and re.match(r"^[a-z]{2}(-[A-Za-z]{2})?$", k):
                    found.append(k)
                else:
                    walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)

    walk(config.get("content") or {})
    return list(dict.fromkeys(found))


def generate(config: dict, lang: str | None = None, assets: dict[str, str] | None = None, *,
             default_locale: str = "en", langs: list[str] | None = None, state: str | None = None) -> str:
    """Widget source (HTML on the kit) of a builder configuration. With `lang` only that language's
    strings are emitted; otherwise every language in `langs` (default: those the content names).
    `state` (a preview state id other than the first) bakes that state in: preview builds only."""
    if not isinstance(config, dict) or config.get("type") not in TYPES:
        raise ValueError(f"unknown builder type {config.get('type') if isinstance(config, dict) else config!r}")
    use = [lang] if lang else list(langs or content_languages(config, default_locale))
    return _Gen(config, use, default_locale, assets or {}, preview_data(config, state)).render()


# ------------------------------------------------------------------ validation

def _bytes(s: str) -> int:
    return len(s.encode("utf-8"))


def _check_text(f: dict, v: Any, ptr: str, add) -> None:
    if v is None:
        return
    if f.get("localized") and isinstance(v, dict):
        items = [(f"{ptr}/{k}", t) for k, t in v.items()]
    else:
        items = [(ptr, v)]
    for p, t in items:
        if not isinstance(t, str):
            add(p, "TYPE_INVALID", "a text is expected")
            continue
        if f.get("max") and len(t) > f["max"]:
            add(p, "TOO_LONG", f"{len(t)} characters; at most {f['max']}")
        if "http://" in t:
            add(p, "TEXT_REFUSED", "an http:// address makes Telegram refuse the widget; write https://")
        elif _SECRET.search(t):
            add(p, "TEXT_REFUSED", "words like 'password' or 'secret' make Telegram refuse the widget as carrying "
                                   "a secret; rephrase")


def _check_action(v: Any, ptr: str, add) -> None:
    if not isinstance(v, dict) or v.get("kind") not in ("request", "link", "copy"):
        add(ptr, "ACTION_INVALID", "choose what the button does: request, link or copy")
        return
    kind = v["kind"]
    if kind == "request":
        data = v.get("data")
        if not isinstance(data, str) or not data:
            add(f"{ptr}/data", "DATA_EMPTY", "the bot needs 1-64 bytes of request data")
        elif _bytes(data) > DATA_MAX:
            add(f"{ptr}/data", "DATA_TOO_LONG", f"{_bytes(data)} bytes; the bot accepts at most {DATA_MAX}")
        _check_text({"max": 64, "localized": True}, v.get("done"), f"{ptr}/done", add)
    elif kind == "link":
        url = v.get("url")
        if not isinstance(url, str) or not re.match(r"^https://[^\s/$.?#][^\s]*$", url) or len(url) > 256:
            add(f"{ptr}/url", "URL_INVALID", "an https:// link of up to 256 characters")
    else:
        _check_text({"max": 256, "localized": True}, v.get("text"), f"{ptr}/text", add)


def _applies(f: dict, scope: dict) -> bool:
    w = f.get("when")
    if w:
        v = _get(scope, w["key"])
        if "eq" in w and not (v == w["eq"] or (w["eq"] is False and v is None)):
            return False
        if "in" in w and v not in w["in"]:
            return False
    return not (f.get("toggle") and _get(scope, f["toggle"]) is False)


def _check_fields(fields: list[dict], scope: dict, base: str, add, assets: dict | None) -> None:
    for f in fields:
        if not _applies(f, scope):
            continue
        v = _get(scope, f["key"])
        ptr = f"{base}/{f['key'].replace('.', '/')}"
        t = f["type"]
        if t == "text":
            _check_text(f, v, ptr, add)
        elif t == "number" and v is not None:
            if not isinstance(v, (int, float)) or isinstance(v, bool):
                add(ptr, "TYPE_INVALID", "a number is expected")
            elif "min" in f and v < f["min"]:
                add(ptr, "TOO_SMALL", f"at least {f['min']}")
            elif "max" in f and v > f["max"]:
                add(ptr, "TOO_BIG", f"at most {f['max']}")
        elif t == "toggle" and v is not None and not isinstance(v, bool):
            add(ptr, "TYPE_INVALID", "on or off")
        elif t == "choice" and v is not None and v not in [o["value"] for o in f["options"]]:
            add(ptr, "CHOICE_INVALID", "one of " + ", ".join(str(o["value"]) for o in f["options"]))
        elif t == "datetime":
            if not isinstance(v, int) or isinstance(v, bool) or v <= 0:
                add(ptr, "DATETIME_INVALID", "pick a date and time")
        elif t == "image" and v:
            if not isinstance(v, str) or not _IMAGE.match(v):
                add(ptr, "IMAGE_INVALID", "the name of an .svg file in the widget folder")
            elif assets is not None and v not in assets:
                add(ptr, "IMAGE_MISSING", f"{v} is not in the widget folder")
            elif assets is not None and (not clean_svg(assets[v]).startswith("<svg") or _SVG_UNSAFE.search(clean_svg(assets[v]))):
                add(ptr, "IMAGE_UNSAFE", "inline <svg> shapes only: no <image>, <script>, data: or links")
        elif t == "action":
            label = _get(scope, f["key"].rsplit(".", 1)[0] + ".label")
            if _any_text(label):
                _check_action(v, ptr, add)
        elif t == "list":
            if v is None:
                v = []
            if not isinstance(v, list):
                add(ptr, "TYPE_INVALID", "a list is expected")
                continue
            if len(v) < f.get("minItems", 0):
                add(ptr, "TOO_FEW", f"at least {f['minItems']}")
            if "maxItems" in f and len(v) > f["maxItems"]:
                add(ptr, "TOO_MANY", f"at most {f['maxItems']}")
            for i, item in enumerate(v):
                if not isinstance(item, dict):
                    add(f"{ptr}/{i}", "TYPE_INVALID", "an item is an object")
                    continue
                if not isinstance(item.get("id"), str) or not _ID.match(item["id"]):
                    add(f"{ptr}/{i}/id", "ID_INVALID", "an id is 1-16 letters, digits, _ or -")
                _check_fields(f["item"]["fields"], item, f"{ptr}/{i}", add, assets)


def validate_config(config: Any, assets: dict[str, str] | None = None) -> list[dict]:
    """Diagnostics [{pointer, code, message}] of a builder configuration. Pointers are relative to
    `builder` (/content/title/en, /style/colors/dark/bg). `assets` (name -> SVG text) checks images."""
    out: list[dict] = []

    def add(pointer: str, code: str, message: str) -> None:
        out.append({"pointer": pointer, "code": code, "message": message})

    if not isinstance(config, dict):
        add("", "CONFIG_INVALID", "the builder configuration is an object")
        return out
    t = config.get("type")
    if t not in TYPES:
        add("/type", "TYPE_UNKNOWN", f"unknown type {t!r}; one of {', '.join(TYPES)}")
        return out
    if config.get("version", VERSION) != VERSION:
        add("/version", "VERSION_UNSUPPORTED", f"builder/v{VERSION} only")
    content = config.get("content")
    if not isinstance(content, dict):
        add("/content", "TYPE_INVALID", "content is an object")
        content = {}
    for sec in TYPE_SCHEMA[t]["sections"]:
        _check_fields(sec["fields"], content, "/content", add, assets)
    _check_type(t, content, add)
    _check_style(t, config.get("style"), add)
    return out


def _check_type(t: str, c: dict, add) -> None:
    data = _get(c, "button.action.data")
    request = _any_text(_get(c, "button.label")) and _get(c, "button.action.kind") == "request" and isinstance(data, str)
    if t == "product" and request and "{n}" in data:
        mx = int(_num(c.get("quantityMax"), 1, 99, 10)) if _shown(c, "quantity") else 1
        n = _bytes(data.replace("{n}", str(mx)))
        if n > DATA_MAX:
            add("/content/button/action/data", "DATA_TOO_LONG",
                f"with the quantity {mx} the request is {n} bytes; the bot accepts at most {DATA_MAX}")
    if t == "promo" and not str(c.get("code") or "").strip():
        add("/content/code", "CODE_MISSING", "the code the coupon shows (with 'on tap': what the bot answers)")
    if t == "quiz":
        qs = [q for q in c.get("questions") or [] if isinstance(q, dict)]
        seen_q, seen_a = set(), set()
        for i, q in enumerate(qs):
            if q.get("id") in seen_q:
                add(f"/content/questions/{i}/id", "ID_DUPLICATE", f"question id {q.get('id')!r} is used twice")
            seen_q.add(q.get("id"))
            for j, a in enumerate(a for a in q.get("answers") or [] if isinstance(a, dict)):
                if a.get("id") in seen_a:
                    add(f"/content/questions/{i}/answers/{j}/id", "ID_DUPLICATE",
                        f"answer id {a.get('id')!r} is used twice; answer ids are unique in the quiz")
                seen_a.add(a.get("id"))
        if request and qs:
            longest = sum(max([_bytes(str(a.get("id") or "")) for a in q.get("answers") or [] if isinstance(a, dict)] or [0])
                          for q in qs)
            n = _bytes(data) + 1 + longest + len(qs) - 1
            if n > DATA_MAX:
                add("/content/button/action/data", "DATA_TOO_LONG",
                    f"with the answer ids the request can be {n} bytes; the bot accepts at most {DATA_MAX}: "
                    "shorten the data or the answer ids")


def _check_style(t: str, style: Any, add) -> None:
    if style is None:
        return
    if not isinstance(style, dict):
        add("/style", "TYPE_INVALID", "style is an object")
        return
    if style.get("preset") is not None and style["preset"] not in PRESET_IDS:
        add("/style/preset", "PRESET_UNKNOWN", f"one of {', '.join(PRESET_IDS)} or none")
    if style.get("palette") not in (None, "per-theme", "shared"):
        add("/style/palette", "CHOICE_INVALID", "per-theme or shared")
    custom = style.get("custom")
    if isinstance(custom, dict):
        for sec in STYLE_SECTIONS:
            _check_fields(sec["fields"], custom, "/style/custom", add, None)
    colors = style.get("colors")
    if isinstance(colors, dict):
        allowed = slots_for(t)
        for theme, slots in colors.items():
            if theme not in ("light", "dark") or not isinstance(slots, dict):
                add(f"/style/colors/{theme}", "COLOR_THEME_UNKNOWN", "light or dark")
                continue
            for slot, value in slots.items():
                if slot not in allowed:
                    add(f"/style/colors/{theme}/{slot}", "COLOR_SLOT_UNKNOWN", f"no colour {slot!r} for a {t}")
                elif value is not None and (not isinstance(value, str) or not _HEX.match(value)):
                    add(f"/style/colors/{theme}/{slot}", "COLOR_INVALID", "#rgb or #rrggbb, or empty for the Telegram theme")


# ------------------------------------------------------------------ preview: states and mock answers

def state_ids(config: dict) -> list[str]:
    """Preview state ids of the config's type; the first is what production shows (no state)."""
    t = config.get("type") if isinstance(config, dict) else None
    ids = [s["id"] for s in TYPE_SCHEMA[t]["states"]] if t in TYPES else ["default"]
    if t == "quiz":
        n = len([q for q in (config.get("content") or {}).get("questions") or [] if isinstance(q, dict)]) or 1
        ids = [f"q{i}" for i in range(1, min(n, 5) + 1)] + ["result"]
    return ids


def is_preview_state(config: dict, state: str | None) -> bool:
    """A state other than the first one: only preview builds bake it into the widget."""
    return bool(state) and state in state_ids(config)[1:]


def preview_data(config: dict, state: str | None) -> tuple[dict | None, str]:
    """(chat data, JS) a preview build starts from for `state`. The chat data is what a real bot
    stores: product {n} (it confirmed n), promo {c: code, cp?}, countdown {d: deadline}, quiz {a: ids}."""
    if not is_preview_state(config, state):
        return None, ""
    t = config["type"]
    c = config.get("content") or {}
    code = str(c.get("code") or "")
    if t == "product":
        return {"n": 1, "r": 1}, ""
    if t == "promo":
        return ({"c": code, "r": 1} if state == "revealed" else {"c": code, "cp": 1, "r": 1}), ""
    if t == "countdown":  # any past instant: finished on every clock
        return {"d": 1, "r": 1}, ""
    if t == "quiz":
        firsts = [str(((q.get("answers") or [{}])[0]).get("id") or "")
                  for q in c.get("questions") or [] if isinstance(q, dict)]
        if state == "result":
            return {"a": ".".join(firsts), "r": 1}, ""
        k = int(state[1:]) - 1
        return None, f"i={k};A={_js(firsts[:k])};"
    return None, ""


def preview_states(config: dict) -> dict:
    """widget.json `states` + `fresh` of a new builder widget: one empty entry per state id (the
    preview build bakes the state's data itself, see preview_data)."""
    return {"states": {sid: {} for sid in state_ids(config)}, "fresh": []}


def requests_of(config: dict) -> list[tuple[str, dict | None]]:
    """Every request the generated widget can send, with the chat data a bot would store for it."""
    t = config.get("type")
    c = config.get("content") or {}
    out: list[tuple[str, dict | None]] = []
    if t == "promo" and c.get("reveal") == "tap":
        out.append((REVEAL_DATA, {"c": str(c.get("code") or ""), "r": 2}))
    action = _get(c, "button.action") or {}
    if not (_any_text(_get(c, "button.label")) and isinstance(action, dict) and action.get("kind") == "request"):
        return out
    data = str(action.get("data") or "")
    if not data:
        return out
    if t == "product":
        if "{n}" in data:
            mx = int(_num(c.get("quantityMax"), 1, 99, 10)) if _shown(c, "quantity") else 1
            out += [(data.replace("{n}", str(n)), {"n": n, "r": 2}) for n in range(1, mx + 1)]
        else:
            out.append((data, {"n": 1, "r": 2}))
    elif t == "quiz":
        lists = [[str(a.get("id") or "") for a in q.get("answers") or [] if isinstance(a, dict)]
                 for q in c.get("questions") or [] if isinstance(q, dict)]
        for combo in itertools.islice(itertools.product(*lists), 1024):
            ids = ".".join(combo)
            out.append((f"{data}:{ids}", {"a": ids, "r": 2}))
    else:
        out.append((data, None))
    return [(d, s) for d, s in out if 1 <= _bytes(d) <= DATA_MAX]


def mock_answers(config: dict) -> dict:
    """Synthetic answers for the preview, in the shape of widgets.mock_answers:
    {state: {data: {"pushes": [...], "result": "<JSON string>"}}}. Local only; no bot logic."""
    entries = {}
    for data, state in requests_of(config):
        answer: dict = {"ok": True}
        pushes = []
        if state is not None:
            answer["s"] = state
            pushes.append({"field": "chatData", "text": json.dumps(state, ensure_ascii=False, separators=(",", ":"))})
            if "c" in state:
                answer["c"] = state["c"]
        entries[data] = {"pushes": pushes, "result": json.dumps(answer, ensure_ascii=False, separators=(",", ":"))}
    return {state: dict(entries) for state in state_ids(config)}


def needs_queries(config: dict) -> bool:
    return bool(requests_of(config))


# ------------------------------------------------------------------ project integration

def active(meta: dict | None) -> bool:
    """The generator owns this widget's source (builder present, not ejected)."""
    b = (meta or {}).get("builder")
    return isinstance(b, dict) and not b.get("ejected")


def assets_of(snap, wid: str) -> dict[str, str]:
    base = f"widgets/{wid}/"
    return {rel[len(base):]: snap.files[rel].decode("utf-8", "replace") for rel in snap.files
            if rel.startswith(base) and rel.endswith(".svg") and "/" not in rel[len(base):]}


def caption_text(config: dict, lang: str, default_locale: str = "en") -> str:
    c = config.get("content") or {}
    t = config.get("type")
    if t == "product":
        parts = [_loc(c.get("name"), lang, default_locale), str(c.get("price") or "")]
        return " · ".join(p for p in parts if p.strip())
    if t == "quiz":
        return _loc((c.get("questions") or [{}])[0].get("text"), lang, default_locale)
    return _loc(c.get("title"), lang, default_locale)


PLACEHOLDER = ("<!-- This widget is generated from widget.json (builder) by the bot-ui visual builder.\n"
               "     Edit it in the Studio form; \"Edit the code\" (eject) writes the code here. -->\n")


def creation_files(type_: str, locales: list[str], now: int | None = None) -> tuple[dict, dict]:
    """(widget.json fields, files) of a new builder widget."""
    config = default_config(type_, locales, now)
    states = preview_states(config)
    meta = {"builder": config, "send": {"allow_queries": needs_queries(config)}, "states": states["states"],
            "queries": [], "fresh": states["fresh"]}
    return meta, {"index.html": PLACEHOLDER}


def eject(config: dict, langs: list[str] | None = None, assets: dict[str, str] | None = None, *,
          default_locale: str = "en") -> dict:
    """{"files": {index.html, style.css, widget.js}, "builder": config with ejected: true}. The files
    assemble to exactly the generated source (every language kept), so the next build is the same."""
    from .widgets import split_html
    src = generate(config, assets=assets, default_locale=default_locale, langs=langs)
    files = split_html(src)
    return {"files": files, "builder": {**copy.deepcopy(config), "ejected": True}}


def eject_patch(snap, wid: str) -> dict:
    """bot-ui-patch/v1 that writes the generated code and marks the widget ejected."""
    from . import PATCH_FORMAT
    from .widgets import WidgetError
    w = snap.widgets.get(wid)
    if w is None:
        raise WidgetError("WIDGET_NOT_FOUND", f"widget {wid} does not exist")
    if not isinstance(w.get("builder"), dict):
        raise WidgetError("NOT_A_BUILDER_WIDGET", f"widget {wid} is hand-written; there is nothing to eject")
    if w["builder"].get("ejected"):
        raise WidgetError("ALREADY_EJECTED", f"widget {wid} is already ejected; edit its files")
    p = snap.project or {}
    dl = p.get("defaultLocale", "en")
    langs = [lang for lang in (w.get("languages") or []) if isinstance(lang, str)] or None
    res = eject(w["builder"], langs, assets_of(snap, wid), default_locale=dl)
    meta = {**w, "builder": res["builder"], "entry": "index.html"}
    changes = [{"widgetId": wid, "file": "widget.json", "content": json.dumps(meta, ensure_ascii=False, indent=2) + "\n"}]
    changes += [{"widgetId": wid, "file": name, "content": text} for name, text in res["files"].items()]
    return {"format": PATCH_FORMAT, "projectId": p.get("projectId"), "baseRevision": snap.revision, "changes": changes}
