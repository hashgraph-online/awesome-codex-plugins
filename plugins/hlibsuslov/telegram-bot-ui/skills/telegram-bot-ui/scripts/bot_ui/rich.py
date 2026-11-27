"""Rich HTML screens (`message.format: "rich.html"`, Bot API 10.1+; buttons 10.3).

A rich screen's text is Rich HTML, sent as `sendRichMessage(rich_message={"html": ...})`. Buttons
inside the document are bound to the screen's actions, the same actions its inline keyboard
uses, so one router answers both:

    <tg-button-row align="center"><tg-button action="pay"></tg-button></tg-button-row>
    <p>Total {total}. <tg-button action="details">Details</tg-button></p>

`action="<id>"` is the bot-ui form; the renderer replaces it with the official attributes
(`type="callback_data" data="<screen>:<action>"`, or `type="url" url="..."`) and the action's
style. Empty content takes the action's label. A button written with official attributes and no
`action` (for example `type="copy_text"`) is passed through unchanged.

Tag list and button attributes: core.telegram.org/bots/api#rich-html-style, checked 2026-11-25.
Keep `studio/web/src/core/rich.ts` in step (tests/test_bot_ui_rich.py compares both).
"""
from __future__ import annotations


import re
from typing import Any

TEXT_MAX = 32768  # Rich Message Limits: UTF-8 characters of text
ROW_MAX = 8  # InputRichBlockButtons: 1-8 buttons
TAGS = {
    "a", "b", "strong", "i", "em", "u", "ins", "s", "strike", "del", "code", "mark", "sub", "sup", "tg-spoiler",
    "tg-reference", "tg-emoji", "img", "tg-time", "tg-math", "h1", "h2", "h3", "h4", "h5", "h6", "p", "pre",
    "footer", "hr", "ul", "ol", "li", "input", "blockquote", "cite", "aside", "br", "video", "audio",
    "tg-document", "figure", "figcaption", "tg-map", "tg-collage", "tg-slideshow", "table", "caption", "tr", "th",
    "td", "details", "summary", "tg-math-block", "tg-button", "tg-button-row",
}
DRAFT_TAGS = {"tg-thinking"}
BUTTON_TYPES = {"url", "callback_data", "web_app", "login_url", "switch_inline_query",
                "switch_inline_query_current_chat", "switch_inline_query_chosen_chat", "copy_text", "disabled"}
STYLES = {"primary", "success", "danger", "link"}
_ATTRS = r"""((?:[^>"']|"[^"]*"|'[^']*')*)"""  # attributes; a quoted value may hold ">"
BUTTON_RE = re.compile(r"<tg-button(?=[\s>/])" + _ATTRS + r">(.*?)</tg-button\s*>", re.S | re.I)
ROW_RE = re.compile(r"<tg-button-row(?=[\s>/])" + _ATTRS + r">(.*?)</tg-button-row\s*>", re.S | re.I)
EMOJI_RE = re.compile(r"<tg-emoji(?=[\s>/])" + _ATTRS + r">(.*?)</tg-emoji\s*>", re.S | re.I)
ATTR_RE = re.compile(r"""([a-zA-Z_][a-zA-Z0-9_-]*)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'))?""")
TAG_RE = re.compile(r"<(/?)([a-zA-Z][a-zA-Z0-9-]*)" + _ATTRS + r">")
ENTITY_RE = re.compile(r"&(#[xX][0-9a-fA-F]{1,6}|#\d{1,7}|lt|gt|quot|apos|nbsp|amp);")
NAMED = {"lt": "<", "gt": ">", "quot": '"', "apos": "'", "nbsp": " ", "amp": "&"}


def escape(value: str) -> str:
    """Escaper for a placeholder value in Rich HTML text or a quoted attribute (either quote)."""
    return (value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;").replace("'", "&#39;"))


def unescape(s: str) -> str:
    """The entities both engines decode (the TypeScript port has no full HTML5 table): the XML five,
    &nbsp; and valid numeric code points. Anything else stays as written."""
    def sub(m: re.Match) -> str:
        e = m.group(1)
        if e[0] != "#":
            return NAMED[e]
        cp = int(e[2:], 16) if e[1] in "xX" else int(e[1:])
        return chr(cp) if 0 < cp <= 0x10FFFF and not 0xD800 <= cp <= 0xDFFF else m.group(0)
    return ENTITY_RE.sub(sub, s)


def attrs(raw: str) -> dict[str, str]:
    out = {}
    for m in ATTR_RE.finditer(raw):
        value = m.group(2) if m.group(2) is not None else m.group(3)
        out[m.group(1).lower()] = unescape(value) if value is not None else ""
    return out


def visible_text(text: str) -> str:
    return unescape(TAG_RE.sub("", text))


def action_ids(text: str) -> list[str]:
    """Action ids that `<tg-button action="...">` refers to, in document order."""
    return [a["action"] for a in (attrs(m.group(1)) for m in BUTTON_RE.finditer(text)) if a.get("action")]


def custom_emoji(text: str) -> list[tuple[str, str, bool]]:
    """(id, fallback, on a button) of every `<tg-emoji emoji-id="...">` in a Rich HTML text, in document order.
    One inside a `<tg-button>` is the button's icon: a button takes a static custom emoji only."""
    spans = [m.span(2) for m in BUTTON_RE.finditer(text)]
    out = []
    for m in EMOJI_RE.finditer(text):
        eid = attrs(m.group(1)).get("emoji-id", "")
        if re.fullmatch(r"\d{1,20}", eid):
            out.append((eid, m.group(2), any(a <= m.start() < b for a, b in spans)))
    return out


# Where a button inside the document does not belong (references/rich-message-buttons.md §6, §10). The keyboard
# is the default; a document button is for a press that changes one part of the same message.
OUTSIDE_KINDS = {"url", "web_app", "login_url", "switch_inline_query", "switch_inline_query_current_chat",
                 "switch_inline_query_chosen_chat"}
FILLED_STYLES = {"primary", "success", "danger"}
NAV_LABEL = re.compile(r"^\s*(?:[←‹«]|back\b|menu\b|home\b|назад|меню|головн|главн)", re.I)
ROW_SOFT_MAX = 4   # the API allows 8 in a row; past 4 a row turns into slivers
DOC_SOFT_MAX = 8   # bubbles (buttons not styled "link") in one message; past this: a keyboard picker, search, a Mini App
LINK_SOFT_MAX = 20  # quiet per-line "link" buttons (one per list item) before the list wants paging or a Mini App


def placement(buttons: list[dict], rows: list[int]) -> list[tuple[str, str]]:
    """(code, message) warnings for the buttons of one document. `buttons`: {kind, style, label, nav?} where kind
    is the button's action field (url, callback_data, ...; "" when unknown) and nav marks a known move to another
    screen; `rows`: the size of each button row."""
    out: list[tuple[str, str]] = []

    def labels(pred) -> str:
        hits = [b.get("label") or b.get("kind") or "?" for b in buttons if pred(b)]
        return ", ".join(repr(h[:24]) for h in hits[:4]) + (" …" if len(hits) > 4 else "")

    if any(b.get("nav") or NAV_LABEL.match(b.get("label") or "") for b in buttons):
        out.append(("RICH_BUTTON_NAVIGATION", f"{labels(lambda b: b.get('nav') or NAV_LABEL.match(b.get('label') or ''))} "
                    "moves to another screen: navigation lives on the keyboard under the message"))
    if any(b.get("style") in FILLED_STYLES for b in buttons):
        out.append(("RICH_BUTTON_MAIN_ACTION", f"{labels(lambda b: b.get('style') in FILLED_STYLES)} has a filled style "
                    "inside the document: the main action and commitments go on the keyboard (its style there); "
                    "a document button is a quiet per-element control"))
    if any(b.get("kind") in OUTSIDE_KINDS for b in buttons):
        out.append(("RICH_BUTTON_OUTSIDE", f"{labels(lambda b: b.get('kind') in OUTSIDE_KINDS)} opens something outside "
                    "the message: a link in the sentence (<a href>) or a keyboard button"))
    links = sum(1 for b in buttons if b.get("style") == "link")
    bubbles = len(buttons) - links
    if any(n > ROW_SOFT_MAX for n in rows) or bubbles > DOC_SOFT_MAX or links > LINK_SOFT_MAX:
        shape = f"{bubbles} button(s) and {links} link button(s)" + (f", rows of {', '.join(map(str, rows))}" if rows else "")
        out.append(("RICH_BUTTON_DENSITY", f"{shape} in the document: at most {ROW_SOFT_MAX} in a row, about "
                    f"{DOC_SOFT_MAX} buttons and {LINK_SOFT_MAX} per-line links in a message; more is a keyboard "
                    "picker, inline search or a Mini App"))
    return out


def html_buttons(text: str) -> tuple[list[dict], list[int]]:
    """The buttons of a Rich HTML text for placement(): official-attribute buttons carry their kind and style;
    bot-ui `action=` buttons are reported with kind "" (the screen's action types decide those)."""
    buttons = []
    for m in BUTTON_RE.finditer(text):
        a = attrs(m.group(1))
        buttons.append({"kind": "" if a.get("action") else a.get("type", ""), "style": a.get("style", ""),
                        "label": visible_text(m.group(2)).strip(), "action": a.get("action")})
    rows = [len(BUTTON_RE.findall(r.group(2))) for r in ROW_RE.finditer(text)]
    return buttons, rows


def screen_action_ids(screen: dict) -> set[str]:
    """Every action a rich screen's text binds, across locales and state variants."""
    msg = screen.get("message") or {}
    if msg.get("format") != "rich.html":
        return set()
    sources = [msg.get("text")] + [v.get("text") for v in (msg.get("states") or {}).values() if isinstance(v, dict)]
    out: set[str] = set()
    for src in sources:
        for t in ([src] if isinstance(src, str) else list(src.values()) if isinstance(src, dict) else []):
            if isinstance(t, str):
                out.update(action_ids(t))
    return out


def compile_buttons(text: str, screen_id: str, actions: dict, label_of: Any, callback_of: Any
                    ) -> tuple[str, list[dict], list[dict]]:
    """Replace bot-ui `action=` buttons with official ones. Returns (html, buttons, diagnostics);
    buttons are in document order with the same keys as keyboard buttons."""
    buttons: list[dict] = []
    diags: list[dict] = []

    def sub(m: re.Match) -> str:
        a = attrs(m.group(1))
        inner = m.group(2)
        aid = a.get("action")
        if not aid:
            btn: dict[str, Any] = {"actionId": None, "text": visible_text(inner).strip(), "type": a.get("type", "")}
            if a.get("type") == "callback_data":
                btn["callbackData"] = a.get("data", "")
            elif "url" in a:
                btn["url"] = a["url"]
            if a.get("style") in STYLES:
                btn["style"] = a["style"]
            buttons.append(btn)
            return m.group(0)
        act = actions.get(aid)
        if not isinstance(act, dict) or act.get("hidden"):
            diags.append({"code": "RICH_BUTTON_ACTION_MISSING", "severity": "warning", "pointer": "/message/text",
                          "message": f"<tg-button action=\"{aid}\"> has no visible action; it is left out"})
            return ""
        label = label_of(act, aid)
        content = inner if visible_text(inner).strip() else escape(label)
        btn = {"actionId": aid, "text": visible_text(content).strip(), "type": act.get("type")}
        style = act.get("style") if act.get("style") in STYLES else None
        if act.get("type") == "url":
            btn["url"] = act.get("url") or ""
            tag = f'<tg-button type="url" url="{escape(btn["url"])}"'
            if style == "link":
                style = None  # "link" is allowed only for callback buttons
        else:
            btn["callbackData"] = callback_of(aid, act)
            tag = f'<tg-button type="callback_data" data="{escape(btn["callbackData"])}"'
        if style:
            btn["style"] = style
            tag += f' style="{style}"'
        buttons.append(btn)
        return f"{tag}>{content}</tg-button>"

    return BUTTON_RE.sub(sub, text), buttons, diags


def check(text: str, *, draft: bool = False) -> list[tuple[str, str, str]]:
    """(code, severity, message) for one Rich HTML text: tags, button rows, button attributes, length."""
    out: list[tuple[str, str, str]] = []
    allowed = TAGS | (DRAFT_TAGS if draft else set())
    for close, tag, _ in TAG_RE.findall(text):
        t = tag.lower()
        if t not in allowed:
            out.append(("RICH_TAG_UNSUPPORTED", "warning", f"<{t}> is not in Telegram's Rich HTML tag list"))
    for row in ROW_RE.finditer(text):
        n = len(BUTTON_RE.findall(row.group(2)))
        if not 1 <= n <= ROW_MAX:
            out.append(("RICH_BUTTON_ROW_SIZE", "error", f"a <tg-button-row> holds 1-{ROW_MAX} buttons, found {n}"))
    for m in BUTTON_RE.finditer(text):
        a = attrs(m.group(1))
        if a.get("action"):
            continue
        t = a.get("type")
        if t not in BUTTON_TYPES:
            out.append(("RICH_BUTTON_TYPE", "error", f"<tg-button> needs action=\"<id>\" or a type from {sorted(BUTTON_TYPES)}"))
        elif t == "callback_data" and not 1 <= len(a.get("data", "").encode("utf-8")) <= 64:
            out.append(("RICH_BUTTON_DATA", "error", "callback data must be 1-64 bytes"))
        elif t in ("url", "web_app", "login_url") and not a.get("url"):
            out.append(("RICH_BUTTON_URL", "error", f"a {t} button needs url=\"...\""))
        if a.get("style") and a["style"] not in STYLES:
            out.append(("RICH_BUTTON_STYLE", "error", f"style must be one of {sorted(STYLES)}"))
        elif a.get("style") == "link" and t != "callback_data":
            out.append(("RICH_BUTTON_STYLE", "error", "style \"link\" is allowed only for callback buttons"))
        if not visible_text(m.group(2)).strip():
            out.append(("RICH_BUTTON_TEXT", "error", "a button needs visible text"))
    n = len(visible_text(text))
    if n > TEXT_MAX:
        out.append(("TEXT_TOO_LONG", "error", f"{n} characters > {TEXT_MAX} (Rich Message Limits)"))
    return out
