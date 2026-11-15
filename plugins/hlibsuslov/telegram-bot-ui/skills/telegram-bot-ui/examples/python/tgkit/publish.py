"""Channel publishing: post model -> render -> validate -> plan -> publish once.

* `Post` is a structured content model (blocks + inline spans), never raw HTML.
  One model renders to MessageEntity text (the default regular path), regular
  HTML, MarkdownV2 (both for compatibility) and InputRichBlock blocks (Rich).
* `validate()` checks limits, button rules for the target context, media refs
  and entity offsets (UTF-16) before anything reaches the network.
* `plan()` turns a post into the exact request sequence (splits, captions,
  album follow-ups, buttons on the right part).
* `Publisher` is idempotent per key: a write-ahead ledger means a timeout
  becomes "unknown" (reconcile it), never a second post. Edits are skipped when
  nothing changed.
* `FanOut` sends one prepared payload to many recipients with throttling,
  honoured `retry_after`, and per-recipient outcomes.

Bot API facts used here were re-read on 2026-11-15 (Bot API 10.4 is the newest
version on that date). The Bot API has no scheduled-send method: scheduling is
the caller's job (cron, queue) - `approveSuggestedPost.send_date` exists only
for suggested posts in channel direct-messages chats.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import tempfile
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from . import rich
from .errors import OutcomeUnknown, RetryPolicy, TelegramError, call_with_policy
from .text import escape_html, escape_markdown_v2, split_text, utf16_len

# ---- limits (Bot API pages, re-read 2026-11-15) ----------------------------
LIMITS = {
    "text": 4096,              # sendMessage.text, after entities parsing
    "caption": 1024,           # captions of media, albums, paid media
    "album_min": 2, "album_max": 10,          # sendMediaGroup.media
    "paid_media_max": 10, "stars_min": 1, "stars_max": 25000,  # sendPaidMedia
    "poll_question": 300, "poll_option": 100, "poll_options_min": 1, "poll_options_max": 12,
    "poll_explanation": 200, "poll_explanation_newlines": 2, "poll_description": 1024,
    "poll_period_min": 5, "poll_period_max": 2628000,
    "poll_country_codes": 12,
    "callback_data_bytes": 64,
    "delete_window_s": 48 * 3600,  # deleteMessage: sent less than 48 hours ago
    "decline_comment": 128,        # declineSuggestedPost.comment
    "rich_chars": rich.LIMITS["chars"], "rich_blocks": rich.LIMITS["blocks"],
    "rich_media": rich.LIMITS["media"], "rich_table_columns": rich.LIMITS["table_columns"],
}

# Button fields an inline keyboard may carry, and where they stop working.
ACTION_FIELDS = ("url", "callback_data", "web_app", "login_url", "switch_inline_query",
                 "switch_inline_query_current_chat", "switch_inline_query_chosen_chat",
                 "copy_text", "callback_game", "pay", "disabled")
NOT_IN_CHANNEL = {
    "web_app": "web_app buttons work only in private chats",
    "switch_inline_query_current_chat": "not supported in channels",
    "switch_inline_query": "the changelog (2017) says it can't be sent to channels; avoid",
    "callback_game": "game messages only",
    "pay": "invoice messages only",
}
NOT_IN_CHANNEL_DM = {
    "switch_inline_query": "not supported in channel direct messages chats",
    "switch_inline_query_current_chat": "not supported in channel direct messages chats",
    "switch_inline_query_chosen_chat": "not supported in channel direct messages chats",
    "web_app": "web_app buttons work only in private chats",
}
CONTEXTS = ("channel", "channel_dm", "group", "private")
URL_SCHEMES = ("http://", "https://", "tg://")

# ---- where HTML widgets can be sent (re-read 2026-11-15) -------------------
# sendWidget / sendSharedWidget: "in the production environment, widgets can be
# sent only to private chats"; chat_id names a chat or "the target supergroup",
# never a channel. Widgets guide: groups = test server only; "Widgets cannot be
# posted in channels, directly or via the bot" (users may forward a widget into a
# channel - test server only). Channel DM chats: not documented -> unsupported.
# Flip CHANNEL_WIDGETS only when the Bot API page lists channels for sendWidget.
CHANNEL_WIDGETS = False
_WIDGET_TARGETS = {("private", "production"), ("private", "test"), ("group", "test")}


def widget_supported(context: str, environment: str = "production") -> bool:
    if context == "channel":
        return CHANNEL_WIDGETS
    return (context, environment) in _WIDGET_TARGETS


# A decorator receives (post copy, target context) and returns the decorated post,
# e.g. the custom emoji stream's helper adding premium emoji where the bot is
# eligible. Default: no decoration. It runs before validation, so its output is
# checked like any other post.
Decorator = Callable[["Post", str], "Post"]


def decorate_post(post: "Post", context: str, decorate: Decorator | None) -> "Post":
    if decorate is None:
        return post
    out = decorate(Post.from_dict(post.to_dict()), context)
    if not isinstance(out, Post):
        raise TypeError("a decorator must return a Post")
    return out


class PostInvalid(ValueError):
    def __init__(self, issues: list["Issue"]):
        super().__init__("; ".join(f"{i.code}: {i.message}" for i in issues))
        self.issues = issues


@dataclass
class Issue:
    level: str      # "error" blocks publishing, "warn" is design advice
    code: str
    message: str


# ---- content model ---------------------------------------------------------
# Block: {"type": "heading"|"paragraph"|"list"|"quote"|"table"|"code"|"divider"|"footer"|"document", ...}
# Inline: str | [Inline, ...] | {"bold"|"italic"|"spoiler"|"underline"|"strike": Inline}
#         | {"code": str} | {"link": url, "text": Inline}

@dataclass
class Post:
    blocks: list[dict[str, Any]] = field(default_factory=list)
    kind: str = "auto"         # auto|text|rich|photo|video|document|album|poll|paid_media
    media: list[dict[str, Any]] = field(default_factory=list)   # {"type", "ref", "spoiler"?}
    buttons: list[list[dict[str, Any]]] = field(default_factory=list)
    link_preview: dict[str, Any] | None = None  # {"url", "above", "large"|"small"} or {"disabled": True}
    silent: bool = False
    protect: bool = False
    caption_above: bool = False
    poll: dict[str, Any] | None = None
    stars: int | None = None
    paid_payload: str | None = None
    followup_text: str = "Links:"   # short text that carries buttons after an album
    lang: str | None = None
    # {"html", "public_data"?, "chat_data"?, "width"?, "height"?, "allow_queries"?}.
    # Used only where widget_supported(); elsewhere the blocks are rendered instead.
    widget: dict[str, Any] | None = None
    # Authoring format of a rich post: "blocks" (typed, default), "markdown" or "html".
    rich_source: str = "blocks"

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Post":
        known = set(cls.__dataclass_fields__)
        unknown = set(d) - known
        if unknown:
            raise ValueError(f"unknown post fields: {sorted(unknown)}")
        return cls(**copy.deepcopy(d))

    def to_dict(self) -> dict[str, Any]:
        return {k: copy.deepcopy(getattr(self, k)) for k in self.__dataclass_fields__}

    def with_changes(self, **changes: Any) -> "Post":
        d = self.to_dict()
        d.update(copy.deepcopy(changes))
        return Post.from_dict(d)


def resolve_kind(post: Post, context: str = "channel", environment: str = "production") -> str:
    """Pick the delivery format. A widget only where the target supports it;
    otherwise the same blocks as rich (tables, documents, checklists, several
    headings, or text that would need splitting) or regular text."""
    if post.widget and post.kind in ("auto", "widget") and widget_supported(context, environment):
        return "widget"
    if post.kind == "widget":
        post = post.with_changes(kind="auto", widget=None)
    if post.kind != "auto":
        return post.kind
    if post.poll:
        return "poll"
    if post.stars:
        return "paid_media"
    if len(post.media) >= 2:
        return "album"
    if len(post.media) == 1:
        return post.media[0].get("type", "photo")
    needs_rich = any(b["type"] in ("table", "document") for b in post.blocks) or \
        any(b["type"] == "list" and any(isinstance(i, dict) and "done" in i for i in b["items"]) for b in post.blocks) or \
        sum(b["type"] == "heading" for b in post.blocks) >= 2
    if needs_rich:
        return "rich"
    text, _ = to_entities(post.blocks)
    return "rich" if utf16_len(text) > LIMITS["text"] else "text"


# ---- inline walking --------------------------------------------------------
_MARKS = {"bold": "bold", "italic": "italic", "spoiler": "spoiler", "underline": "underline", "strike": "strikethrough"}


def _inline_parts(node: Any):
    """Yield (mark, payload) pairs; mark None = plain text."""
    if node is None:
        return
    if isinstance(node, str):
        yield None, node
    elif isinstance(node, list):
        for x in node:
            yield from _inline_parts(x)
    elif isinstance(node, dict):
        if "link" in node:
            yield "link", node
        elif "code" in node:
            yield "code", node["code"]
        else:
            for k in _MARKS:
                if k in node:
                    yield k, node[k]
                    return
            raise ValueError(f"unknown inline span: {sorted(node)}")
    else:
        raise ValueError(f"unsupported inline value: {type(node).__name__}")


def plain(node: Any) -> str:
    out = []
    for mark, val in _inline_parts(node):
        if mark is None or mark == "code":
            out.append(val)
        elif mark == "link":
            out.append(plain(val.get("text", val["link"])))
        else:
            out.append(plain(val))
    return "".join(out)


def _item_text(item: Any) -> Any:
    return item["text"] if isinstance(item, dict) and "text" in item and "done" in item else item


def _list_mark(item: Any) -> str:
    """Static checklist marks for regular messages (no API checklist in channels:
    sendChecklist is business-only)."""
    if isinstance(item, dict) and "done" in item:
        return "☑ " if item["done"] else "☐ "
    return "• "


# ---- renderer 1: text + MessageEntity (default regular path) ---------------
class _EntityWriter:
    def __init__(self) -> None:
        self.text = ""
        self.entities: list[dict[str, Any]] = []

    def pos(self) -> int:
        return utf16_len(self.text)

    def add(self, s: str) -> None:
        self.text += s

    def span(self, etype: str, start: int, **extra: Any) -> None:
        length = self.pos() - start
        if length > 0:
            self.entities.append({"type": etype, "offset": start, "length": length, **extra})

    def inline(self, node: Any) -> None:
        for mark, val in _inline_parts(node):
            if mark is None:
                self.add(val)
                continue
            start = self.pos()
            if mark == "code":
                self.add(val)
                self.span("code", start)
            elif mark == "link":
                _check_url(val["link"])
                self.inline(val.get("text", val["link"]))
                self.span("text_link", start, url=val["link"])
            else:
                self.inline(val)
                self.span(_MARKS[mark], start)


def to_entities(blocks: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
    w = _EntityWriter()
    for i, b in enumerate(blocks):
        if i:
            w.add("\n\n")
        t = b["type"]
        start = w.pos()
        if t == "heading":
            w.inline(b["text"])
            w.span("bold", start)
        elif t == "paragraph":
            w.inline(b["text"])
        elif t == "list":
            for n, item in enumerate(b["items"]):
                if n:
                    w.add("\n")
                w.add(_list_mark(item))
                w.inline(_item_text(item))
        elif t == "quote":
            w.inline(b["text"])
            if b.get("credit"):
                w.add("\n— " + b["credit"])
            w.span("expandable_blockquote" if b.get("expandable") else "blockquote", start)
        elif t == "code":
            w.add(b["text"])
            w.span("pre", start, **({"language": b["language"]} if b.get("language") else {}))
        elif t == "footer":
            w.inline(b["text"])
            w.span("italic", start)
        elif t == "divider":
            w.add("———")
        else:
            raise ValueError(f"block {t!r} needs a rich message")
    return w.text, w.entities


# ---- renderer 2/3: regular HTML and MarkdownV2 (compatibility paths) -------
def _check_url(url: str) -> str:
    if not isinstance(url, str) or not url.startswith(URL_SCHEMES) or any(c in url for c in " \n\r\t"):
        raise ValueError(f"refusing link URL {url!r}: only http(s):// and tg:// without spaces")
    return url


def _html_inline(node: Any) -> str:
    out = []
    tags = {"bold": "b", "italic": "i", "underline": "u", "strike": "s", "spoiler": "tg-spoiler"}
    for mark, val in _inline_parts(node):
        if mark is None:
            out.append(escape_html(val))
        elif mark == "code":
            out.append(f"<code>{escape_html(val)}</code>")
        elif mark == "link":
            href = escape_html(_check_url(val["link"])).replace('"', "&quot;")
            out.append(f'<a href="{href}">{_html_inline(val.get("text", val["link"]))}</a>')
        else:
            out.append(f"<{tags[mark]}>{_html_inline(val)}</{tags[mark]}>")
    return "".join(out)


def to_html(blocks: list[dict[str, Any]]) -> str:
    parts = []
    for b in blocks:
        t = b["type"]
        if t == "heading":
            parts.append(f"<b>{_html_inline(b['text'])}</b>")
        elif t == "paragraph":
            parts.append(_html_inline(b["text"]))
        elif t == "list":
            parts.append("\n".join(_list_mark(i) + _html_inline(_item_text(i)) for i in b["items"]))
        elif t == "quote":
            body = _html_inline(b["text"]) + (f"\n— {escape_html(b['credit'])}" if b.get("credit") else "")
            parts.append(f"<blockquote{' expandable' if b.get('expandable') else ''}>{body}</blockquote>")
        elif t == "code":
            lang = f' class="language-{escape_html(b["language"])}"' if b.get("language") else ""
            parts.append(f"<pre><code{lang}>{escape_html(b['text'])}</code></pre>")
        elif t == "footer":
            parts.append(f"<i>{_html_inline(b['text'])}</i>")
        elif t == "divider":
            parts.append("———")
        else:
            raise ValueError(f"block {t!r} needs a rich message")
    return "\n\n".join(parts)


def _mdv2_inline(node: Any) -> str:
    out = []
    marks = {"bold": "*", "italic": "_", "underline": "__", "strike": "~", "spoiler": "||"}
    for mark, val in _inline_parts(node):
        if mark is None:
            out.append(escape_markdown_v2(val))
        elif mark == "code":
            out.append("`" + val.replace("\\", "\\\\").replace("`", "\\`") + "`")
        elif mark == "link":
            url = _check_url(val["link"]).replace("\\", "\\\\").replace(")", "\\)")
            out.append(f"[{_mdv2_inline(val.get('text', val['link']))}]({url})")
        else:
            m = marks[mark]
            out.append(f"{m}{_mdv2_inline(val)}{m}")
    return "".join(out)


def to_markdown_v2(blocks: list[dict[str, Any]]) -> str:
    parts = []
    for b in blocks:
        t = b["type"]
        if t == "heading":
            parts.append(f"*{_mdv2_inline(b['text'])}*")
        elif t == "paragraph":
            parts.append(_mdv2_inline(b["text"]))
        elif t == "list":
            parts.append("\n".join(_list_mark(i) + _mdv2_inline(_item_text(i)) for i in b["items"]))
        elif t == "quote":
            lines = (plain(b["text"]) + (f"\n— {b['credit']}" if b.get("credit") else "")).split("\n")
            body = "\n".join(">" + escape_markdown_v2(ln) for ln in lines)
            parts.append(("**" + body + "||") if b.get("expandable") else body)
        elif t == "code":
            parts.append("```" + (b.get("language") or "") + "\n" +
                         b["text"].replace("\\", "\\\\").replace("`", "\\`") + "\n```")
        elif t == "footer":
            parts.append(f"_{_mdv2_inline(b['text'])}_")
        elif t == "divider":
            parts.append(escape_markdown_v2("———"))
        else:
            raise ValueError(f"block {t!r} needs a rich message")
    return "\n\n".join(parts)


# ---- renderer 4: Rich Message blocks (InputRichBlock*) ----------------------
def _rich_inline(node: Any) -> Any:
    out = []
    for mark, val in _inline_parts(node):
        if mark is None:
            out.append(val)
        elif mark == "code":
            out.append({"type": "code", "text": val})
        elif mark == "link":
            out.append({"type": "url", "text": _rich_inline(val.get("text", val["link"])), "url": _check_url(val["link"])})
        else:
            out.append({"type": _MARKS[mark], "text": _rich_inline(val)})
    return out[0] if len(out) == 1 else out


def to_rich_blocks(blocks: list[dict[str, Any]], buttons: list[list[dict[str, Any]]] | None = None) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    first_heading = True
    for b in blocks:
        t = b["type"]
        if t == "heading":
            out.append({"type": "heading", "size": b.get("size", 1 if first_heading else 2), "text": _rich_inline(b["text"])})
            first_heading = False
        elif t == "paragraph":
            out.append({"type": "paragraph", "text": _rich_inline(b["text"])})
        elif t == "list":
            items = []
            for i in b["items"]:
                item: dict[str, Any] = {"blocks": [{"type": "paragraph", "text": _rich_inline(_item_text(i))}]}
                if isinstance(i, dict) and "done" in i:
                    item["has_checkbox"] = True
                    if i["done"]:
                        item["is_checked"] = True
                items.append(item)
            out.append({"type": "list", "items": items})
        elif t == "quote":
            if b.get("expandable"):
                out.append(rich.expandable_quote(_rich_inline(b["text"]), b.get("credit")))
            else:
                q: dict[str, Any] = {"type": "blockquote", "blocks": [{"type": "paragraph", "text": _rich_inline(b["text"])}]}
                if b.get("credit"):
                    q["credit"] = b["credit"]
                out.append(q)
        elif t == "table":
            out.append(rich.table(b["header"], [[_rich_inline(c) for c in r] for r in b["rows"]],
                                  compact=b.get("compact", True), numeric_cols=frozenset(b.get("numeric", [])),
                                  caption=b.get("caption")))
        elif t == "code":
            out.append({"type": "paragraph", "text": {"type": "code", "text": b["text"]}})
        elif t == "footer":
            out.append({"type": "footer", "text": _rich_inline(b["text"])})
        elif t == "divider":
            out.append({"type": "divider"})
        elif t == "document":
            out.append(rich.document_block(b["ref"], b.get("caption")))
        else:
            raise ValueError(f"unknown block type {t!r}")
    for row in buttons or []:
        out.append(rich.button_row([_rich_button(btn) for btn in row]))
    return out


def _rich_button(btn: dict[str, Any]) -> dict[str, Any]:
    copy_text = btn.get("copy_text")
    return rich.rich_button(btn["text"], callback_data=btn.get("callback_data"), url=btn.get("url"),
                            copy_text=copy_text["text"] if isinstance(copy_text, dict) else copy_text,
                            style=btn.get("style"))


# ---- renderer 5/6: Rich HTML and Rich Markdown sources -----------------------
# Same content, authored as text. Rich HTML has one escaper (&, <, >, and " in
# attributes) and expresses everything (compact tables, expandable quotes,
# buttons). Rich Markdown is shorter to read but needs HTML tags for features
# without Markdown syntax; its backslash escaping beyond the documented `\#` is
# CommonMark practice, not stated by the Bot API page [Unverified].
_RICH_HTML_TAGS = {"bold": "b", "italic": "i", "underline": "u", "strike": "s", "spoiler": "tg-spoiler"}
_RMD_INLINE = set("\\`*_[]<&|~=$^")      # can open inline markup anywhere
_RMD_LINE_START = ("#", "-", "+", ">")   # open a block only at the start of a line
_RMD_ORDERED = re.compile(r"^(\d+)\.")   # "1." at a line start would open an ordered list


def _attr(s: str) -> str:
    return escape_html(s).replace('"', "&quot;")


def _rich_html_inline(node: Any) -> str:
    out = []
    for mark, val in _inline_parts(node):
        if mark is None:
            out.append(escape_html(val).replace("\n", "<br>"))
        elif mark == "code":
            out.append(f"<code>{escape_html(val)}</code>")
        elif mark == "link":
            out.append(f'<a href="{_attr(_check_url(val["link"]))}">{_rich_html_inline(val.get("text", val["link"]))}</a>')
        else:
            tag = _RICH_HTML_TAGS[mark]
            out.append(f"<{tag}>{_rich_html_inline(val)}</{tag}>")
    return "".join(out)


def _escape_rich_md(s: str) -> str:
    lines = []
    for line in s.split("\n"):
        out = "".join("\\" + ch if ch in _RMD_INLINE else ch for ch in line)
        if out.startswith(_RMD_LINE_START):
            out = "\\" + out
        lines.append(_RMD_ORDERED.sub(r"\1\\.", out))
    return "\n".join(lines)


def _rich_md_inline(node: Any) -> str:
    marks = {"bold": "**", "italic": "_", "strike": "~~", "spoiler": "||"}
    out = []
    for mark, val in _inline_parts(node):
        if mark is None:
            out.append(_escape_rich_md(val))
        elif mark == "code":
            out.append(f"<code>{escape_html(val)}</code>" if "`" in val else f"`{val}`")
        elif mark == "link":
            url = _check_url(val["link"]).replace("(", "%28").replace(")", "%29")
            out.append(f"[{_rich_md_inline(val.get('text', val['link']))}]({url})")
        elif mark == "underline":
            out.append(f"<u>{_rich_md_inline(val)}</u>")
        else:
            out.append(f"{marks[mark]}{_rich_md_inline(val)}{marks[mark]}")
    return "".join(out)


def _rich_html_table(b: dict[str, Any]) -> str:
    numeric = set(b.get("numeric", []))
    attrs = " bordered" + (" compact" if b.get("compact", True) else "")
    cap = f"<caption>{escape_html(b['caption'])}</caption>" if b.get("caption") else ""

    def row(cells: list[Any], tag: str) -> str:
        return "<tr>" + "".join(f'<{tag} align="{"right" if i in numeric else "left"}">{_rich_html_inline(c)}</{tag}>'
                                for i, c in enumerate(cells)) + "</tr>"
    return f"<table{attrs}>{cap}" + row(b["header"], "th") + "".join(row(r, "td") for r in b["rows"]) + "</table>"


def _rich_html_quote(b: dict[str, Any]) -> str:
    cite = f"<cite>{escape_html(b['credit'])}</cite>" if b.get("credit") else ""
    return f"<blockquote{' expandable' if b.get('expandable') else ''}>{_rich_html_inline(b['text'])}{cite}</blockquote>"


def _rich_buttons_html(buttons: list[list[dict[str, Any]]]) -> list[str]:
    rows = []
    for row in buttons:
        items = []
        for btn in row:
            style = f' style="{_attr(btn["style"])}"' if btn.get("style") else ""
            if "url" in btn:
                attrs = f'type="url" url="{_attr(_check_url(btn["url"]))}"'
            elif "callback_data" in btn:
                attrs = f'type="callback_data" data="{_attr(btn["callback_data"])}"'
            elif "copy_text" in btn:
                ct = btn["copy_text"]["text"] if isinstance(btn["copy_text"], dict) else btn["copy_text"]
                attrs = f'type="copy_text" text="{_attr(ct)}"'
            else:
                raise ValueError("rich sources render url / callback_data / copy_text buttons only")
            items.append(f"<tg-button {attrs}{style}>{escape_html(btn['text'])}</tg-button>")
        rows.append("<tg-button-row>" + "".join(items) + "</tg-button-row>")
    return rows


def _media_entry(i: int, ref: str) -> tuple[str, dict[str, Any]]:
    mid = f"doc{i}"
    return mid, {"id": mid, "media": {"type": "document", "media": ref}}


def to_rich_html(blocks: list[dict[str, Any]], buttons: list[list[dict[str, Any]]] | None = None
                 ) -> tuple[str, list[dict[str, Any]]]:
    """(InputRichMessage.html, InputRichMessage.media)."""
    parts, media, first_heading = [], [], True
    for b in blocks:
        t = b["type"]
        if t == "heading":
            n = b.get("size", 1 if first_heading else 2)
            first_heading = False
            parts.append(f"<h{n}>{_rich_html_inline(b['text'])}</h{n}>")
        elif t == "paragraph":
            parts.append(f"<p>{_rich_html_inline(b['text'])}</p>")
        elif t == "list":
            lis = []
            for i in b["items"]:
                box = ""
                if isinstance(i, dict) and "done" in i:
                    box = '<input type="checkbox" checked>' if i["done"] else '<input type="checkbox">'
                lis.append(f"<li>{box}{_rich_html_inline(_item_text(i))}</li>")
            parts.append("<ul>" + "".join(lis) + "</ul>")
        elif t == "quote":
            parts.append(_rich_html_quote(b))
        elif t == "table":
            parts.append(_rich_html_table(b))
        elif t == "code":
            lang = f' class="language-{_attr(b["language"])}"' if b.get("language") else ""
            parts.append(f"<pre><code{lang}>{escape_html(b['text'])}</code></pre>")
        elif t == "footer":
            parts.append(f"<footer>{_rich_html_inline(b['text'])}</footer>")
        elif t == "divider":
            parts.append("<hr/>")
        elif t == "document":
            mid, entry = _media_entry(len(media) + 1, b["ref"])
            media.append(entry)
            cap = f"<figcaption>{escape_html(b['caption'])}</figcaption>" if b.get("caption") else ""
            parts.append(f'<figure><tg-document src="tg://document?id={mid}"></tg-document>{cap}</figure>')
        else:
            raise ValueError(f"unknown block type {t!r}")
    parts += _rich_buttons_html(buttons or [])
    return "\n".join(parts), media


def to_rich_markdown(blocks: list[dict[str, Any]], buttons: list[list[dict[str, Any]]] | None = None
                     ) -> tuple[str, list[dict[str, Any]]]:
    """(InputRichMessage.markdown, InputRichMessage.media). Features without
    Markdown syntax (compact tables, expandable quotes, credits, footers,
    buttons) are written as the documented HTML tags."""
    parts, media, first_heading = [], [], True
    for b in blocks:
        t = b["type"]
        if t == "heading":
            n = b.get("size", 1 if first_heading else 2)
            first_heading = False
            parts.append("#" * n + " " + _rich_md_inline(b["text"]))
        elif t == "paragraph":
            parts.append(_rich_md_inline(b["text"]))
        elif t == "list":
            lines = []
            for i in b["items"]:
                box = ("[x] " if i["done"] else "[ ] ") if isinstance(i, dict) and "done" in i else ""
                lines.append(f"- {box}{_rich_md_inline(_item_text(i))}")
            parts.append("\n".join(lines))
        elif t == "quote":
            if b.get("expandable") or b.get("credit"):
                parts.append(_rich_html_quote(b))
            else:
                parts.append("\n".join(">" + ln for ln in _rich_md_inline(b["text"]).split("\n")))
        elif t == "table":
            if b.get("compact", True) or b.get("caption"):
                parts.append(_rich_html_table(b))
            else:
                numeric = set(b.get("numeric", []))
                head = "| " + " | ".join(_rich_md_inline(h) for h in b["header"]) + " |"
                sep = "|" + "|".join("---:" if i in numeric else ":---" for i in range(len(b["header"]))) + "|"
                rows = ["| " + " | ".join(_rich_md_inline(c) for c in r) + " |" for r in b["rows"]]
                parts.append("\n".join([head, sep, *rows]))
        elif t == "code":
            parts.append("```" + (b.get("language") or "") + "\n" + b["text"] + "\n```")
        elif t == "footer":
            parts.append(f"<footer>{_rich_html_inline(b['text'])}</footer>")
        elif t == "divider":
            parts.append("---")
        elif t == "document":
            mid, entry = _media_entry(len(media) + 1, b["ref"])
            media.append(entry)
            title = f' "{b["caption"].replace(chr(34), chr(39))}"' if b.get("caption") else ""
            parts.append(f"![](tg://document?id={mid}{title})")
        else:
            raise ValueError(f"unknown block type {t!r}")
    parts += _rich_buttons_html(buttons or [])
    return "\n\n".join(parts), media


def rich_message(post: "Post") -> dict[str, Any]:
    """InputRichMessage in the post's chosen authoring format (exactly one of
    blocks / markdown / html, plus media for the text formats)."""
    source = post.rich_source
    if source == "blocks":
        return {"blocks": to_rich_blocks(post.blocks, post.buttons)}
    text, media = (to_rich_markdown if source == "markdown" else to_rich_html)(post.blocks, post.buttons)
    out: dict[str, Any] = {source: text}
    if media:
        out["media"] = media
    return out


def rich_size(blocks: list[dict[str, Any]]) -> tuple[int, int, int]:
    """(characters, blocks incl. nested/list items/table rows, media) of InputRichBlocks."""
    chars = blocks_n = media = 0

    def text_len(rt: Any) -> int:
        return len(rich.plain(rt))

    def walk(bs: list[dict[str, Any]]) -> None:
        nonlocal chars, blocks_n, media
        for b in bs:
            blocks_n += 1
            t = b.get("type")
            if t in ("heading", "paragraph", "footer", "expandable_blockquote"):
                chars += text_len(b.get("text"))
            if t == "list":
                for it in b["items"]:
                    blocks_n += 1
                    walk(it["blocks"])
            if t == "blockquote":
                walk(b["blocks"])
            if t == "table":
                blocks_n += len(b["cells"])
                chars += sum(text_len(c["text"]) for r in b["cells"] for c in r)
            if t == "buttons":
                chars += sum(text_len(x["text"]) for x in b["buttons"])
            if t in ("document", "photo", "video", "audio", "animation", "voice_note"):
                media += 1
    walk(blocks)
    return chars, blocks_n, media


# ---- keyboard --------------------------------------------------------------
def inline_keyboard(buttons: list[list[dict[str, Any]]]) -> dict[str, Any] | None:
    if not buttons:
        return None
    rows = []
    for row in buttons:
        out_row = []
        for btn in row:
            b = {k: v for k, v in btn.items()}
            if isinstance(b.get("copy_text"), str):
                b["copy_text"] = {"text": b["copy_text"]}
            out_row.append(b)
        rows.append(out_row)
    return {"inline_keyboard": rows}


# ---- validation ------------------------------------------------------------
def check_entities(text: str, entities: list[dict[str, Any]]) -> list[str]:
    """Offsets/lengths are UTF-16 code units and must stay inside the text."""
    n = utf16_len(text)
    bad = []
    for e in entities:
        if e["length"] <= 0 or e["offset"] < 0 or e["offset"] + e["length"] > n:
            bad.append(f"{e['type']}@{e['offset']}+{e['length']} outside 0..{n}")
    return bad


def check_media_ref(ref: Any, *, live: bool = False) -> str | None:
    """None if fine. file_id, http(s) URL, or attach://<name> (multipart only)."""
    if not isinstance(ref, str) or not ref:
        return "media ref must be a non-empty string"
    if ref.startswith("attach://"):
        return "attach:// needs a multipart upload (not supported by the JSON transport)" if live else None
    if ref.startswith(("http://", "https://")):
        return None if not any(c in ref for c in " \n\t") else "URL contains whitespace"
    if "://" in ref or "/" in ref or "\\" in ref or " " in ref or ref.startswith("."):
        return f"not a file_id, URL or attach:// reference: {ref[:40]!r} (local paths are never sent)"
    return None


def _check_buttons(rows: list[list[dict[str, Any]]], context: str, *, custom_emoji_ok: bool,
                   rich_rows: bool) -> list[Issue]:
    issues: list[Issue] = []
    primaries = 0
    for row in rows:
        for btn in row:
            label = str(btn.get("text", ""))[:30]
            actions = [k for k in ACTION_FIELDS if k in btn]
            if len(actions) != 1:
                issues.append(Issue("error", "button_actions", f"{label!r}: exactly one action field, got {actions}"))
                continue
            a = actions[0]
            if context == "channel" and a in NOT_IN_CHANNEL:
                issues.append(Issue("error", "button_context", f"{label!r}: {a} - {NOT_IN_CHANNEL[a]}"))
            if context == "channel_dm" and a in NOT_IN_CHANNEL_DM:
                issues.append(Issue("error", "button_context", f"{label!r}: {a} - {NOT_IN_CHANNEL_DM[a]}"))
            if rich_rows and a not in ("url", "callback_data", "copy_text"):
                issues.append(Issue("error", "button_rich", f"{label!r}: this helper renders url/callback/copy rich buttons only"))
            if a == "callback_data" and not 1 <= len(btn[a].encode("utf-8")) <= LIMITS["callback_data_bytes"]:
                issues.append(Issue("error", "callback_data", f"{label!r}: callback_data must be 1-64 bytes"))
            if a == "url":
                try:
                    _check_url(btn[a])
                except ValueError as exc:
                    issues.append(Issue("error", "button_url", str(exc)))
            style = btn.get("style")
            allowed = ("primary", "success", "danger", "link") if rich_rows else ("primary", "success", "danger")
            if style is not None and style not in allowed:
                issues.append(Issue("error", "button_style", f"{label!r}: style must be one of {allowed}"))
            if style == "link" and a != "callback_data":
                issues.append(Issue("error", "button_style", f"{label!r}: style 'link' is for callback buttons only"))
            primaries += style == "primary"
            if "icon_custom_emoji_id" in btn:
                if rich_rows:
                    issues.append(Issue("error", "button_icon", f"{label!r}: rich buttons have no icon field"))
                elif context in ("channel", "channel_dm") and not custom_emoji_ok:
                    issues.append(Issue("error", "custom_emoji", f"{label!r}: custom emoji in channels need a bot with "
                                        "Fragment usernames (Premium owner covers private/group chats only)"))
    if primaries > 1:
        issues.append(Issue("warn", "button_primary", "more than one primary button: no single call to action"))
    return issues


def validate(post: Post, *, context: str = "channel", custom_emoji_ok: bool = False,
             live: bool = False, environment: str = "production") -> list[Issue]:
    if context not in CONTEXTS:
        raise ValueError(f"context must be one of {CONTEXTS}")
    issues: list[Issue] = []
    kind = resolve_kind(post, context, environment)
    err = lambda code, msg: issues.append(Issue("error", code, msg))  # noqa: E731
    warn = lambda code, msg: issues.append(Issue("warn", code, msg))  # noqa: E731
    if post.widget:
        if not post.blocks:
            err("widget_fallback", "a widget post needs blocks: they are the caption and the fallback rendering")
        if kind == "widget":
            issues += _validate_widget(post, context, environment, custom_emoji_ok)
            return issues
        warn("widget_fallback", f"widgets are not available for {context!r} ({environment}): "
             "the blocks are sent as a regular / rich post instead")
    for b in post.blocks:
        for mark, val in _inline_parts(b.get("text")) if b.get("type") in ("heading", "paragraph", "footer", "quote") else ():
            if mark == "link":
                try:
                    _check_url(val["link"])
                except ValueError as exc:
                    err("link_url", str(exc))
        if b["type"] == "document":
            msg = check_media_ref(b.get("ref"), live=live)
            if msg:
                err("media_ref", msg)
    issues += _check_buttons(post.buttons, context, custom_emoji_ok=custom_emoji_ok, rich_rows=(kind == "rich"))

    if kind in ("text", "photo", "video", "document", "album", "paid_media"):
        try:
            text, ents = to_entities(post.blocks)
        except ValueError as exc:
            err("format", f"{exc}; use kind 'rich' or 'auto'")
            text, ents = "", []
        for bad in check_entities(text, ents):
            err("entities", bad)
        if kind == "text" and not text.strip():
            err("empty", "a text post needs text")
        first = text.split("\n", 1)[0]
        if len(first) > 120:
            warn("first_line", "first line > 120 chars: the notification and pinned preview cut it")
    if kind == "rich":
        if post.rich_source not in ("blocks", "markdown", "html"):
            err("rich_source", "rich_source must be blocks, markdown or html")
        else:
            try:
                rich_message(post)
            except ValueError as exc:
                err("format", str(exc))
        if post.link_preview:
            warn("link_preview", "sendRichMessage has no link_preview_options: the preview setting is ignored")
        try:
            blocks = to_rich_blocks(post.blocks, post.buttons)
            chars, n, media = rich_size(blocks)
            if chars > LIMITS["rich_chars"]:
                err("rich_chars", f"{chars} > {LIMITS['rich_chars']} characters")
            if n > LIMITS["rich_blocks"]:
                err("rich_blocks", f"{n} > {LIMITS['rich_blocks']} blocks")
            if media > LIMITS["rich_media"]:
                err("rich_media", f"{media} > {LIMITS['rich_media']} media")
            for b in blocks:
                if b["type"] == "table" and len(b["cells"][0]) > LIMITS["rich_table_columns"]:
                    err("rich_table", "more than 20 table columns")
        except ValueError as exc:
            err("format", str(exc))
    if kind in ("photo", "video", "document", "album", "paid_media"):
        if not post.media:
            err("media", f"{kind} needs media")
        for m in post.media:
            msg = check_media_ref(m.get("ref"), live=live)
            if msg:
                err("media_ref", msg)
        if post.caption_above and kind == "document":
            warn("caption_above", "show_caption_above_media is ignored for documents")
    if kind == "album":
        n = len(post.media)
        if not LIMITS["album_min"] <= n <= LIMITS["album_max"]:
            err("album_size", f"albums take 2-10 items, got {n}")
        types = {m.get("type", "photo") for m in post.media}
        if types & {"document", "audio"} and len(types) > 1:
            err("album_mix", "documents and audio can be grouped only with the same type")
        if post.buttons:
            warn("album_buttons", "sendMediaGroup takes no reply_markup: buttons go to a follow-up message")
    if kind == "paid_media":
        if not (post.stars and LIMITS["stars_min"] <= post.stars <= LIMITS["stars_max"]):
            err("stars", "star_count must be 1-25000")
        if len(post.media) > LIMITS["paid_media_max"]:
            err("paid_media", "paid media takes up to 10 items")
        if post.paid_payload and len(post.paid_payload.encode()) > 128:
            err("paid_payload", "payload is 0-128 bytes")
    if kind == "poll":
        issues += _validate_poll(post.poll or {}, context)
    return issues


def _validate_widget(post: Post, context: str, environment: str, custom_emoji_ok: bool) -> list[Issue]:
    from .widgets import check_widget       # owned by the widget stream; imported, not changed
    w = post.widget or {}
    out: list[Issue] = []
    caption, _, overflow = _caption_split(post)
    rep = check_widget(w.get("html", ""), caption=caption, public_data=w.get("public_data"),
                       chat_data=w.get("chat_data"), context="private" if context == "channel" else context,
                       environment=environment)
    out += [Issue("error", "widget", e) for e in rep.errors]
    out += [Issue("warn", "widget", x) for x in rep.warnings]
    if overflow:
        out.append(Issue("warn", "widget_caption", "the caption keeps only the blocks that fit 1024 characters"))
    if context == "channel":                 # broadcast audience: no per-user or per-chat state
        if w.get("chat_data"):
            out.append(Issue("error", "widget_channel", "channel widgets must not carry chat_data (one state for all)"))
        if w.get("allow_queries"):
            out.append(Issue("error", "widget_channel", "channel widgets must be read-only (no allow_queries)"))
    out += _check_buttons(post.buttons, context, custom_emoji_ok=custom_emoji_ok, rich_rows=False)
    return out


def _validate_poll(p: dict[str, Any], context: str) -> list[Issue]:
    out: list[Issue] = []
    e = lambda c, m: out.append(Issue("error", c, m))  # noqa: E731
    if context == "channel_dm":
        e("poll_context", "polls can't be sent to channel direct messages chats")
    if not 1 <= len(p.get("question", "")) <= LIMITS["poll_question"]:
        e("poll_question", "question is 1-300 characters")
    opts = p.get("options", [])
    if not LIMITS["poll_options_min"] <= len(opts) <= LIMITS["poll_options_max"]:
        e("poll_options", "1-12 options")
    for o in opts:
        if not 1 <= len(o) <= LIMITS["poll_option"]:
            e("poll_option", f"option {o[:20]!r}: 1-100 characters")
    if p.get("type") == "quiz":
        ids = p.get("correct_option_ids") or []
        if not ids or ids != sorted(set(ids)) or any(not 0 <= i < len(opts) for i in ids):
            e("poll_quiz", "quiz needs increasing, valid correct_option_ids")
    exp = p.get("explanation", "")
    if len(exp) > LIMITS["poll_explanation"] or exp.count("\n") > LIMITS["poll_explanation_newlines"]:
        e("poll_explanation", "explanation: 0-200 characters, at most 2 line feeds")
    if len(p.get("description", "")) > LIMITS["poll_description"]:
        e("poll_description", "description: 0-1024 characters")
    if p.get("open_period") and p.get("close_date"):
        e("poll_period", "open_period and close_date are mutually exclusive")
    if p.get("open_period") and not LIMITS["poll_period_min"] <= p["open_period"] <= LIMITS["poll_period_max"]:
        e("poll_period", "open_period is 5-2628000 seconds")
    if (p.get("members_only") or p.get("country_codes")) and context != "channel":
        e("poll_channel_only", "members_only / country_codes are for channel chats only")
    if len(p.get("country_codes", [])) > LIMITS["poll_country_codes"]:
        e("poll_country_codes", "0-12 country codes")
    if p.get("allow_adding_options") and (p.get("type") == "quiz" or p.get("is_anonymous", True)):
        e("poll_adding", "allow_adding_options is not supported for anonymous polls and quizzes")
    return out


def assert_valid(post: Post, **kw: Any) -> list[Issue]:
    issues = validate(post, **kw)
    errors = [i for i in issues if i.level == "error"]
    if errors:
        raise PostInvalid(errors)
    return issues


# ---- planning --------------------------------------------------------------
def _common(post: Post) -> dict[str, Any]:
    p: dict[str, Any] = {}
    if post.silent:
        p["disable_notification"] = True
    if post.protect:
        p["protect_content"] = True
    return p


def _link_preview(post: Post) -> dict[str, Any] | None:
    lp = post.link_preview
    if not lp:
        return None
    if lp.get("disabled"):
        return {"is_disabled": True}
    out: dict[str, Any] = {}
    if lp.get("url"):
        out["url"] = _check_url(lp["url"])
    if lp.get("large"):
        out["prefer_large_media"] = True
    if lp.get("small"):
        out["prefer_small_media"] = True
    if lp.get("above"):
        out["show_above_text"] = True
    return out


def _caption_split(post: Post) -> tuple[str, list[dict[str, Any]], list[dict[str, Any]]]:
    """(caption, caption_entities, overflow_blocks). The caption keeps whole
    blocks while they fit in 1024 characters; the rest becomes a follow-up."""
    if not post.blocks:
        return "", [], []
    for cut in range(len(post.blocks), 0, -1):
        text, ents = to_entities(post.blocks[:cut])
        if utf16_len(text) <= LIMITS["caption"]:
            return text, ents, post.blocks[cut:]
    text, ents = to_entities(post.blocks[:1])
    parts = split_text(text, ents, LIMITS["caption"])
    return parts[0][0], parts[0][1], post.blocks[1:]


def plan(post: Post, chat_id: int | str, *, address: dict[str, Any] | None = None, context: str = "channel",
         environment: str = "production", decorate: Decorator | None = None) -> list[tuple[str, dict[str, Any]]]:
    """Exact request sequence. `address` adds message_thread_id or
    direct_messages_topic_id. Buttons always ride on the LAST message the
    reader reaches; later parts never ping again. `decorate` (optional) runs
    first; a widget is planned only where the context supports it."""
    post = decorate_post(post, context, decorate)
    kind = resolve_kind(post, context, environment)
    base = {"chat_id": chat_id, **(address or {})}
    common = _common(post)
    markup = inline_keyboard(post.buttons)
    reqs: list[tuple[str, dict[str, Any]]] = []

    def text_messages(blocks: list[dict[str, Any]], *, preview: bool, silent_all: bool) -> None:
        text, ents = to_entities(blocks)
        parts = split_text(text, ents, LIMITS["text"])
        for i, (chunk, pe) in enumerate(parts):
            p = {**base, "text": chunk, **common}
            if pe:
                p["entities"] = pe
            # One preview per post: on the first part, as configured; later parts
            # and text that follows media get none (their links would add cards).
            lp = _link_preview(post) if (preview and i == 0) else {"is_disabled": True}
            if lp:
                p["link_preview_options"] = lp
            if i > 0 or silent_all:
                p["disable_notification"] = True
            reqs.append(("sendMessage", p))
        if markup and reqs:
            reqs[-1][1]["reply_markup"] = markup

    if kind == "text":
        text_messages(post.blocks, preview=True, silent_all=False)
    elif kind == "rich":
        p = {**base, "rich_message": rich_message(post), **common}
        reqs.append(("sendRichMessage", p))
    elif kind in ("photo", "video", "document"):
        m = post.media[0]
        caption, ents, overflow = _caption_split(post)
        field_ = {"photo": "photo", "video": "video", "document": "document"}[kind]
        p = {**base, field_: m["ref"], **common}
        if caption:
            p["caption"] = caption
        if ents:
            p["caption_entities"] = ents
        if post.caption_above and kind != "document":
            p["show_caption_above_media"] = True
        if m.get("spoiler") and kind != "document":
            p["has_spoiler"] = True
        reqs.append(("send" + kind.capitalize(), p))
        if overflow:
            text_messages(overflow, preview=False, silent_all=True)
        elif markup:
            p["reply_markup"] = markup
    elif kind == "album":
        caption, ents, overflow = _caption_split(post)
        media = []
        for i, m in enumerate(post.media):
            item: dict[str, Any] = {"type": m.get("type", "photo"), "media": m["ref"]}
            if i == 0 and caption:
                item["caption"] = caption       # one caption on the first item = the album caption
                if ents:
                    item["caption_entities"] = ents
                if post.caption_above and item["type"] in ("photo", "video"):
                    item["show_caption_above_media"] = True
            if m.get("spoiler") and item["type"] in ("photo", "video"):
                item["has_spoiler"] = True
            media.append(item)
        reqs.append(("sendMediaGroup", {**base, "media": media, **common}))
        if overflow:
            text_messages(overflow, preview=False, silent_all=True)
        elif markup:
            reqs.append(("sendMessage", {**base, "text": post.followup_text, **common, "disable_notification": True,
                                         "reply_markup": markup}))
    elif kind == "paid_media":
        caption, ents, _ = _caption_split(post)
        p = {**base, "star_count": post.stars,
             "media": [{"type": m.get("type", "photo"), "media": m["ref"]} for m in post.media], **common}
        if caption:
            p["caption"] = caption
        if ents:
            p["caption_entities"] = ents
        if post.paid_payload:
            p["payload"] = post.paid_payload
        if post.caption_above:
            p["show_caption_above_media"] = True
        if markup:
            p["reply_markup"] = markup
        reqs.append(("sendPaidMedia", p))
    elif kind == "widget":
        w = post.widget or {}
        caption, ents, _ = _caption_split(post)     # the caption carries the meaning (notifications, search)
        p = {**base, "html": w["html"], **common}
        for k in ("width", "height", "public_data", "chat_data"):
            if w.get(k) is not None:
                p[k] = w[k]
        if w.get("allow_queries"):
            p["allow_queries"] = True
        if caption:
            p["caption"] = caption
        if ents:
            p["caption_entities"] = ents
        if post.caption_above:
            p["show_caption_above_media"] = True
        if markup:
            p["reply_markup"] = markup
        reqs.append(("sendWidget", p))
    elif kind == "poll":
        q = dict(post.poll or {})
        p = {**base, "question": q.pop("question"), "options": [{"text": o} for o in q.pop("options")], **common}
        p.update(q)
        if markup:
            p["reply_markup"] = markup
        reqs.append(("sendPoll", p))
    else:
        raise ValueError(f"unknown kind {kind!r}")
    return reqs


# ---- ledger ----------------------------------------------------------------
def fingerprint(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:16]


class Ledger:
    """Key -> record. In memory, or a JSON file (written atomically) when a
    path is given. Production systems keep this in their database; the rule
    is the same: write "pending" BEFORE the request leaves."""

    def __init__(self, path: str | None = None):
        self.path = path
        self.records: dict[str, dict[str, Any]] = {}
        if path and os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                self.records = json.load(fh)

    def get(self, key: str) -> dict[str, Any] | None:
        return self.records.get(key)

    def put(self, key: str, **fields: Any) -> dict[str, Any]:
        rec = self.records.setdefault(key, {"key": key})
        rec.update(fields)
        self._save()
        return rec

    def _save(self) -> None:
        if not self.path:
            return
        # exclusive random temp file: a planted `<ledger>.tmp` link can't redirect the write
        fd, tmp = tempfile.mkstemp(prefix=".ledger-", suffix=".tmp",
                                   dir=os.path.dirname(os.path.abspath(self.path)))
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(self.records, fh, ensure_ascii=False, indent=1, sort_keys=True)
        os.replace(tmp, self.path)


def _message_ids(result: Any) -> list[int]:
    if isinstance(result, list):
        return [m["message_id"] for m in result if isinstance(m, dict)]
    if isinstance(result, dict) and "message_id" in result:
        return [result["message_id"]]
    return []


@dataclass
class Result:
    status: str              # sent|already_sent|unknown|partial|failed|unchanged|edited|repost_required|locked|...
    key: str
    message_ids: list[int] = field(default_factory=list)
    detail: str = ""


class Publisher:
    def __init__(self, transport: Any, ledger: Ledger | None = None, *, policy: RetryPolicy | None = None,
                 sleep: Callable[[float], None] = time.sleep, clock: Callable[[], float] = time.time,
                 log: Callable[[dict[str, Any]], None] | None = None, context: str = "channel",
                 custom_emoji_ok: bool = False, environment: str = "production",
                 decorate: Decorator | None = None):
        self.t = transport
        self.ledger = ledger or Ledger()
        self.policy = policy or RetryPolicy()
        self.sleep, self.clock, self.log = sleep, clock, log
        self.context, self.custom_emoji_ok = context, custom_emoji_ok
        self.environment, self.decorate = environment, decorate

    def _prepare(self, post: Post, chat_id: int | str, address: dict[str, Any] | None):
        """Decorate -> validate -> plan. The ledger keeps the SOURCE post, so an
        unchanged source is detected even if decoration is not deterministic."""
        dec = decorate_post(post, self.context, self.decorate)
        assert_valid(dec, context=self.context, custom_emoji_ok=self.custom_emoji_ok, environment=self.environment)
        kind = resolve_kind(dec, self.context, self.environment)
        return kind, plan(dec, chat_id, address=address, context=self.context, environment=self.environment)

    def _call(self, method: str, params: dict[str, Any]) -> Any:
        return call_with_policy(self.t, method, params, policy=self.policy, sleep=self.sleep, log=self.log)

    # -- publish -------------------------------------------------------------
    def publish(self, post: Post, chat_id: int | str, key: str, *,
                address: dict[str, Any] | None = None) -> Result:
        rec = self.ledger.get(key)
        if rec and rec["state"] == "sent":
            return Result("already_sent", key, rec["message_ids"], "ledger says sent; nothing was called")
        if rec and rec["state"] in ("pending", "unknown", "partial"):
            return Result("unknown", key, rec.get("message_ids", []),
                          "a previous attempt may have been delivered: reconcile() before retrying")
        kind, reqs = self._prepare(post, chat_id, address)
        self.ledger.put(key, state="pending", chat_id=chat_id, kind=kind, message_ids=[],
                        parts=[fingerprint(p) for _, p in reqs], methods=[m for m, _ in reqs],
                        post=post.to_dict(), address=address or {}, sent_at=self.clock())
        ids: list[int] = []
        for i, (method, params) in enumerate(reqs):
            try:
                got = _message_ids(self._call(method, params))
            except OutcomeUnknown:
                self.ledger.put(key, state="unknown", message_ids=ids, failed_part=i)
                return Result("unknown", key, ids, f"{method} timed out: it may have been posted")
            except TelegramError as exc:
                state = "partial" if ids else "failed"
                self.ledger.put(key, state=state, message_ids=ids, failed_part=i, error=exc.category)
                return Result(state, key, ids, str(exc))
            ids += got
        server_scheduled = 0 in ids   # video in a large channel: posted later by the server, id 0 until then
        self.ledger.put(key, state="sent", message_ids=ids, server_scheduled=server_scheduled)
        return Result("sent", key, ids, "server-scheduled: wait for the channel_post update" if server_scheduled else "")

    def reconcile(self, key: str, *, found_message_ids: list[int] | None) -> Result:
        """Resolve an unknown outcome with evidence (an operator looked at the
        channel, or a channel_post update with this post arrived). Found ->
        sent. Not found -> 'absent', and publish() may run again."""
        rec = self.ledger.get(key)
        if not rec:
            raise KeyError(key)
        if found_message_ids:
            self.ledger.put(key, state="sent", message_ids=found_message_ids)
            return Result("sent", key, found_message_ids, "reconciled")
        if rec.get("message_ids"):
            return Result("partial", key, rec["message_ids"], "some parts exist: delete them or finish by hand")
        del self.ledger.records[key]
        self.ledger._save()
        return Result("absent", key, [], "confirmed not posted; safe to publish again")

    # -- after publishing ----------------------------------------------------
    def edit(self, key: str, new_post: Post) -> Result:
        rec = self._sent(key)
        if rec.get("paid_post") or rec.get("suggested_final"):
            return Result("locked", key, rec["message_ids"], "paid / approved suggested posts can't be edited")
        if fingerprint(new_post.to_dict()) == fingerprint(rec["post"]):
            return Result("unchanged", key, rec["message_ids"], "no request sent")
        new_kind, new_reqs = self._prepare(new_post, rec["chat_id"], rec.get("address") or None)
        old_methods = rec["methods"]
        if [m for m, _ in new_reqs] != old_methods or new_kind != rec["kind"]:
            return Result("repost_required", key, rec["message_ids"], "layout changed (kind or part count)")
        edits = []
        id_iter = iter(rec["message_ids"])
        for (method, params), old_fp in zip(new_reqs, rec["parts"]):
            mids = [next(id_iter) for _ in (params["media"] if method == "sendMediaGroup" else [0])]
            if fingerprint(params) == old_fp:
                continue
            if method == "sendPoll":
                return Result("repost_required", key, rec["message_ids"], "a sent poll can't be edited (stopPoll only)")
            if method == "sendWidget":
                return Result("repost_required", key, rec["message_ids"],
                              "widget code is immutable; change state with editMessageWidgetData (references/widgets.md)")
            edits += _edit_requests(method, params, rec["chat_id"], mids)
        for m, p in edits:
            self._call(m, p)
        self.ledger.put(key, post=new_post.to_dict(), parts=[fingerprint(p) for _, p in new_reqs])
        return Result("edited" if edits else "unchanged", key, rec["message_ids"], f"{len(edits)} edit request(s)")

    def pin(self, key: str) -> Result:
        rec = self._sent(key)
        self._call("pinChatMessage", {"chat_id": rec["chat_id"], "message_id": rec["message_ids"][0]})
        self.ledger.put(key, pinned=True)
        return Result("pinned", key, rec["message_ids"])

    def unpin(self, key: str) -> Result:
        rec = self._sent(key)
        self._call("unpinChatMessage", {"chat_id": rec["chat_id"], "message_id": rec["message_ids"][0]})
        self.ledger.put(key, pinned=False)
        return Result("unpinned", key, rec["message_ids"])

    def delete(self, key: str) -> Result:
        rec = self._sent(key)
        if self.clock() - rec["sent_at"] >= LIMITS["delete_window_s"]:
            return Result("too_old", key, rec["message_ids"], "deleteMessage works only within 48 hours")
        if rec.get("paid_post") and self.clock() - rec["sent_at"] < 24 * 3600:
            return Result("locked", key, rec["message_ids"], "paid posts must stay 24 hours to be paid")
        self._call("deleteMessages", {"chat_id": rec["chat_id"], "message_ids": rec["message_ids"]})
        self.ledger.put(key, state="deleted")
        return Result("deleted", key, rec["message_ids"])

    def copy_to(self, key: str, chat_id: int | str, new_key: str, **extra: Any) -> Result:
        """Cross-post an identical post with copyMessage(s). Refuses kinds the
        API can't copy (paid media, widgets, ...)."""
        rec = self._sent(key)
        if rec["kind"] == "paid_media":
            raise ValueError("paid media messages can't be copied: send a new paid post instead")
        done = self.ledger.get(new_key)
        if done:
            return Result("already_sent" if done["state"] == "sent" else "unknown", new_key, done.get("message_ids", []))
        ids = rec["message_ids"]
        method, params = (("copyMessage", {"chat_id": chat_id, "from_chat_id": rec["chat_id"], "message_id": ids[0], **extra})
                          if len(ids) == 1 else
                          ("copyMessages", {"chat_id": chat_id, "from_chat_id": rec["chat_id"], "message_ids": ids, **extra}))
        self.ledger.put(new_key, state="pending", chat_id=chat_id, kind=rec["kind"], post=rec["post"],
                        methods=[method], parts=[fingerprint(params)], message_ids=[], copied_from=key, sent_at=self.clock())
        try:
            got = _message_ids(self._call(method, params))
        except OutcomeUnknown:
            self.ledger.put(new_key, state="unknown")
            return Result("unknown", new_key, [], "copy timed out")
        self.ledger.put(new_key, state="sent", message_ids=got)
        return Result("sent", new_key, got)

    def _sent(self, key: str) -> dict[str, Any]:
        rec = self.ledger.get(key)
        if not rec or rec["state"] != "sent":
            raise KeyError(f"{key}: not a sent post ({rec and rec['state']})")
        return rec


def _edit_requests(method: str, params: dict[str, Any], chat_id: Any, mids: list[int]) -> list[tuple[str, dict[str, Any]]]:
    addr = {"chat_id": chat_id, "message_id": mids[0]}
    if method == "sendMessage":
        p = {**addr, "text": params["text"]}
        for k in ("entities", "link_preview_options", "reply_markup"):
            if k in params:
                p[k] = params[k]
        return [("editMessageText", p)]
    if method == "sendRichMessage":
        return [("editMessageText", {**addr, "rich_message": params["rich_message"]})]
    if method in ("sendPhoto", "sendVideo", "sendDocument", "sendPaidMedia"):
        p = {**addr, "caption": params.get("caption", "")}
        for k in ("caption_entities", "show_caption_above_media", "reply_markup"):
            if k in params:
                p[k] = params[k]
        return [("editMessageCaption", p)]
    if method == "sendMediaGroup":
        first = params["media"][0]
        p = {**addr, "caption": first.get("caption", "")}
        if "caption_entities" in first:
            p["caption_entities"] = first["caption_entities"]
        return [("editMessageCaption", p)]
    raise ValueError(f"no edit for {method}")


# ---- correction decision ---------------------------------------------------
def decide_correction(rec: dict[str, Any], new_post: Post, now: float, *, repost_window_s: float = 15 * 60,
                      context: str = "channel", environment: str = "production") -> str:
    """edit | repost | append_note | unchanged | locked.

    API facts: edits keep views, reactions and comments; deleteMessage works
    for 48 h; paid posts can't be edited. Heuristic: a delete-and-repost loses
    the engagement and notifies again, so do it only for a young post whose
    layout must change; otherwise reply with a visible correction note."""
    if fingerprint(new_post.to_dict()) == fingerprint(rec["post"]):
        return "unchanged"
    if rec.get("paid_post") or rec.get("suggested_final"):
        return "append_note"
    same_layout = resolve_kind(new_post, context, environment) == rec["kind"] and \
        [m for m, _ in plan(new_post, rec["chat_id"], context=context, environment=environment)] == rec["methods"] \
        and rec["kind"] not in ("poll", "widget")
    if same_layout:
        return "edit"
    age = now - rec["sent_at"]
    if age < min(repost_window_s, LIMITS["delete_window_s"]):
        return "repost"
    return "append_note"


# ---- fan-out ---------------------------------------------------------------
@dataclass
class FanOutReport:
    sent: dict[str, list[int]] = field(default_factory=dict)
    blocked: list[str] = field(default_factory=list)      # 403: blocked / kicked / no rights
    invalid: list[str] = field(default_factory=list)      # 400: payload for this recipient is wrong
    unknown: list[str] = field(default_factory=list)      # timeout: do NOT resend blindly
    deferred: list[str] = field(default_factory=list)     # long flood wait: reschedule
    skipped: list[str] = field(default_factory=list)      # already sent in an earlier run

    def summary(self) -> dict[str, int]:
        return {k: len(getattr(self, k)) for k in ("sent", "blocked", "invalid", "unknown", "deferred", "skipped")}


class FanOut:
    """Send prepared jobs to many chats. Throttled (`per_second`, default 25 to
    stay under the ~30/s broadcast ceiling from the Bots FAQ), 429 honoured via
    call_with_policy, one failing recipient never stops the batch, and a ledger
    makes a re-run skip what already went out."""

    def __init__(self, transport: Any, *, per_second: float = 25.0, ledger: Ledger | None = None,
                 policy: RetryPolicy | None = None, sleep: Callable[[float], None] = time.sleep,
                 clock: Callable[[], float] = time.monotonic, log: Callable[[dict[str, Any]], None] | None = None):
        self.t, self.interval = transport, 1.0 / per_second
        self.ledger = ledger or Ledger()
        self.policy = policy or RetryPolicy(max_attempts=3, max_wait=60.0)
        self.sleep, self.clock, self.log = sleep, clock, log
        self._last = None

    def _throttle(self) -> None:
        now = self.clock()
        if self._last is not None and now - self._last < self.interval:
            self.sleep(self.interval - (now - self._last))
            now = self.clock()
        self._last = now

    def run(self, campaign: str, jobs: list[tuple[str, list[tuple[str, dict[str, Any]]]]]) -> FanOutReport:
        """jobs: [(recipient_id, [(method, params), ...]), ...]"""
        report = FanOutReport()
        for n, (rid, reqs) in enumerate(jobs):
            key = f"{campaign}:{rid}"
            rec = self.ledger.get(key)
            if rec and rec["state"] == "sent":
                report.skipped.append(rid)
                continue
            if rec and rec["state"] == "unknown":
                report.unknown.append(rid)
                continue
            if rec and rec["state"] == "failed" and rec.get("error") == "permission":
                report.blocked.append(rid)         # blocked the bot / left: don't knock again
                continue
            self.ledger.put(key, state="pending")
            ids: list[int] = []
            try:
                for method, params in reqs:
                    self._throttle()
                    ids += _message_ids(call_with_policy(self.t, method, params, policy=self.policy,
                                                         sleep=self.sleep, log=self.log))
            except OutcomeUnknown:
                self.ledger.put(key, state="unknown", message_ids=ids)
                report.unknown.append(rid)
                continue
            except TelegramError as exc:
                cat = exc.category
                if cat == "rate_limited":            # flood wait longer than policy.max_wait
                    self.ledger.records.pop(key, None)
                    report.deferred += [r for r, _ in jobs[n:]]
                    self.ledger._save()
                    return report
                self.ledger.put(key, state="failed", error=cat)
                (report.blocked if cat == "permission" else report.invalid).append(rid)
                continue
            self.ledger.put(key, state="sent", message_ids=ids)
            report.sent[rid] = ids
        return report


def cross_post(publisher: Publisher, post: Post, targets: list[dict[str, Any]], key: str) -> dict[str, Result]:
    """One logical post -> many channels. Each target: {"chat_id", "lang"?,
    "changes"?: Post fields to override (translated blocks, buttons)}. Each
    target gets its own idempotency key, so a re-run only fills the gaps."""
    results = {}
    for t in targets:
        variant = post.with_changes(**t.get("changes", {}), lang=t.get("lang", post.lang))
        results[str(t["chat_id"])] = publisher.publish(variant, t["chat_id"], f"{key}@{t['chat_id']}")
    return results


__all__ = ["LIMITS", "Post", "Issue", "PostInvalid", "resolve_kind", "to_entities", "to_html", "to_markdown_v2",
           "to_rich_blocks", "rich_size", "inline_keyboard", "validate", "assert_valid", "check_entities",
           "check_media_ref", "plan", "Ledger", "Publisher", "Result", "decide_correction", "FanOut",
           "FanOutReport", "cross_post", "fingerprint", "plain", "widget_supported", "decorate_post", "Decorator",
           "CHANNEL_WIDGETS", "to_rich_html", "to_rich_markdown", "rich_message"]
