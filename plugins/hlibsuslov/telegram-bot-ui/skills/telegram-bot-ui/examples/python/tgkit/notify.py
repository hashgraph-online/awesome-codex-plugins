"""Notifications and bot messages built from the pattern grammar (references/message-patterns.md).

    <b>[icon] Header: 2-5 words</b>
    Subject line
    (blank line)
    body blocks: facts, bullets, timeline, kpi, progress, grid, quote, details, code, sentence
    (blank line)
    <i>footer: meta or hint</i>

Every helper returns regular-message HTML (send with parse_mode "HTML") and escapes what it is
given, so user and model text can't break the markup. Icons are written as Unicode; an eligible
bot upgrades them to its premium pack with tgkit.icons.IconSystem.prepare(). Nothing is sent here.
"""
from __future__ import annotations

from typing import Any, Iterable, Sequence

from . import dataview
from .text import escape_html

CAPTION_LIMIT, TEXT_LIMIT = 1024, 4096  # API: characters after entity parsing
MARKS = {"done": "✓", "current": "●", "next": "○"}


def header(title: str, icon: str = "") -> str:
    """'<b>📦 Order #1042 shipped</b>': one icon (or none), the news in 2-5 words."""
    return f"<b>{escape_html(icon) + ' ' if icon else ''}{escape_html(title)}</b>"


def sentence(text: str) -> str:
    return escape_html(text)


def facts(items: Iterable[Sequence[Any]], sep: str = ": ") -> str:
    """('Label', 'value') -> 'Label: <b>value</b>'; ('Label', 'value', False) keeps the value plain."""
    out = []
    for item in items:
        label, value = item[0], item[1]
        bold = item[2] if len(item) > 2 else True
        v = escape_html(str(value))
        out.append(f"{escape_html(str(label))}{sep}{f'<b>{v}</b>' if bold else v}")
    return "\n".join(out)


def bullets(items: Iterable[str], mark: str = "•", more: str = "") -> str:
    """'• item' per line; `more` ('and 4 more') closes a clipped list."""
    lines = [f"{mark} {escape_html(str(i))}" for i in items]
    return "\n".join(lines + ([escape_html(more)] if more else []))


def timeline(steps: Sequence[Sequence[str]], current: int) -> str:
    """('Paid', '10:02') steps: ✓ before `current`, bold ● at it, ○ after; the time follows the label."""
    out = []
    for i, step in enumerate(steps):
        label = escape_html(step[0]) + (f" · {escape_html(step[1])}" if len(step) > 1 and step[1] else "")
        if i < current:
            out.append(f"{MARKS['done']} {label}")
        elif i == current:
            out.append(f"<b>{MARKS['current']} {label}</b>")
        else:
            out.append(f"{MARKS['next']} {label}")
    return "\n".join(out)


def quote(text: str, expandable: bool | None = None) -> str:
    """Someone's words, verbatim and escaped; expandable when longer than three lines (unless forced)."""
    long = text.count("\n") >= 3 or len(text) > 300
    tag = "blockquote expandable" if (long if expandable is None else expandable) else "blockquote"
    return f"<{tag}>{escape_html(text)}</blockquote>"


def details(text: str) -> str:
    """Logs, the full list, technical detail: collapsed, the main fact stays outside."""
    return f"<blockquote expandable>{escape_html(text)}</blockquote>"


def code(label: str, value: str) -> str:
    return f"{escape_html(label)}: <code>{escape_html(value)}</code>"


def kpi(items: list[dict[str, Any]], lang: str = "en") -> str:
    """'Revenue: <b>€12,400</b> ▲ 8%' lines (tgkit.dataview.kpi_lines)."""
    return dataview.kpi_lines(items, lang)


def progress(done: float, total: float, count: str = "", style: str = "blocks") -> str:
    bar = dataview.progress(done, total, style=style)
    return bar + (f"\n{escape_html(count)}" if count else "")


def grid(head: list[str], rows: list[list[str]], right: Iterable[int] = ()) -> str:
    """A small aligned table in <pre> (≤ 4 columns, ≤ 10 rows); bigger ones are Rich tables."""
    lines = dataview.mono_lines(head, rows, right=frozenset(right))
    return "<pre>" + escape_html("\n".join(lines)) + "</pre>"


def tg_time(unix: int, fallback: str, fmt: str = "wDT") -> str:
    """<tg-time> (Bot API 9.5+): the reader's time zone and language; `fallback` is what old clients show."""
    return f'<tg-time unix="{int(unix)}" format="{escape_html(fmt)}">{escape_html(fallback)}</tg-time>'


def message(title: str, *, icon: str = "", subject: str = "", blocks: Iterable[str] = (),
            footer: str = "", footer_html: bool = False) -> str:
    """Header group, a blank line, the body blocks, a blank line, the italic footer."""
    head = header(title, icon) + (f"\n{escape_html(subject)}" if subject else "")
    body = "\n".join(b for b in blocks if b)
    foot = f"<i>{footer if footer_html else escape_html(footer)}</i>" if footer else ""
    return "\n\n".join(part for part in (head, body, foot) if part)


BLOCKS = {
    "sentence": lambda b, lang: sentence(b["text"]),
    "facts": lambda b, lang: facts(b["items"], b.get("sep", ": ")),
    "bullets": lambda b, lang: bullets(b["items"], b.get("mark", "•"), b.get("more", "")),
    "timeline": lambda b, lang: timeline(b["steps"], int(b["current"])),
    "quote": lambda b, lang: quote(b["text"], b.get("expandable")),
    "details": lambda b, lang: details(b["text"]),
    "code": lambda b, lang: code(b["label"], b["value"]),
    "kpi": lambda b, lang: kpi(b["items"], lang),
    "progress": lambda b, lang: progress(b["done"], b["total"], b.get("count", ""), b.get("style", "blocks")),
    "grid": lambda b, lang: grid(b["header"], b["rows"], b.get("right", ())),
}


def render(spec: dict[str, Any]) -> str:
    """A slots spec -> HTML: {icon, title, subject?, blocks: [{type, ...}], footer?, lang?}."""
    lang = spec.get("lang", "en")
    blocks = []
    for b in spec.get("blocks", []):
        if b.get("type") not in BLOCKS:
            raise ValueError(f"unknown block {b.get('type')!r}; one of {', '.join(BLOCKS)}")
        blocks.append(BLOCKS[b["type"]](b, lang))
    return message(spec["title"], icon=spec.get("icon", ""), subject=spec.get("subject", ""), blocks=blocks,
                   footer=spec.get("footer", ""))


def payload(spec: dict[str, Any], *, chat_id: int | str = 0, sound: str = "ping") -> dict[str, Any]:
    """The request for a rendered spec: sendPhoto with a caption when spec has "photo", else sendMessage.
    sound "silent" sets disable_notification; `buttons` are inline rows of InlineKeyboardButton dicts."""
    html = render(spec)
    params: dict[str, Any] = {"chat_id": spec.get("chat_id", chat_id), "parse_mode": "HTML"}
    if spec.get("photo"):
        method, params["photo"], params["caption"], limit = "sendPhoto", spec["photo"], html, CAPTION_LIMIT
    else:
        method, params["text"], limit = "sendMessage", html, TEXT_LIMIT
        params["link_preview_options"] = {"is_disabled": True}
    if len(html) > limit:  # conservative: the HTML source is never shorter than the parsed text
        raise ValueError(f"{method}: {len(html)} characters of HTML, the limit is {limit}; shorten or split")
    if sound == "silent":
        params["disable_notification"] = True
    if spec.get("buttons"):
        params["reply_markup"] = {"inline_keyboard": spec["buttons"]}
    return {"method": method, "params": params}
