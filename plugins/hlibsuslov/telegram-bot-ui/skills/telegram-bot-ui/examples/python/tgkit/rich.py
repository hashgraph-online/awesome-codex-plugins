"""Rich-message builders and readers for the 10.3/10.4 additions.

Input side (InputRichBlock*): compact tables, expandable quotations, document
blocks, button rows. Output side (RichText / TextQuote): flattening rich texts,
reading TON addresses, building quote_rich_texts for a reply.
"""
from __future__ import annotations

from typing import Any

RichText = Any  # str | list | dict - the Bot API RichText union

# Rich Message Limits (Bot API, "Rich Message Limits", verified 2026-11-12).
LIMITS = {"chars": 32768, "blocks": 500, "depth": 16, "media": 50, "table_columns": 20}
BUTTON_ROW_MAX = 8      # InputRichBlockButtons.buttons: 1-8
QUOTE_MAX_TEXTS = 32
QUOTE_MAX_CHARS = 1024


def cell(text: RichText, *, header: bool = False, align: str = "left", valign: str = "middle") -> dict[str, Any]:
    c: dict[str, Any] = {"text": text, "align": align, "valign": valign}
    if header:
        c["is_header"] = True
    return c


def table(header: list[str], rows: list[list[RichText]], *, compact: bool = False,
          numeric_cols: frozenset[int] = frozenset(), caption: RichText | None = None) -> dict[str, Any]:
    cells = [[cell(h, header=True, align="right" if i in numeric_cols else "left") for i, h in enumerate(header)]]
    for r in rows:
        cells.append([cell(v, align="right" if i in numeric_cols else "left") for i, v in enumerate(r)])
    t: dict[str, Any] = {"type": "table", "cells": cells, "is_bordered": True}
    if compact:
        t["is_compact"] = True       # 10.3: smaller cell indents (dense data on phones)
    if caption is not None:
        t["caption"] = caption
    return t


def expandable_quote(text: RichText, credit: RichText | None = None) -> dict[str, Any]:
    q: dict[str, Any] = {"type": "expandable_blockquote", "text": text}
    if credit is not None:
        q["credit"] = credit
    return q


def document_block(file_ref: str, caption: RichText | None = None) -> dict[str, Any]:
    """file_ref: a file_id (preferred), an HTTP URL, or attach://<name>.
    Not allowed in sendRichMessageDraft for new uploads or explicit URLs."""
    b: dict[str, Any] = {"type": "document", "document": {"type": "document", "media": file_ref}}
    if caption is not None:
        b["caption"] = {"text": caption}
    return b


def rich_button(text: RichText, *, callback_data: str | None = None, url: str | None = None,
                copy_text: str | None = None, disabled: bool = False, style: str | None = None) -> dict[str, Any]:
    actions = [a for a in (callback_data, url, copy_text) if a is not None] + ([True] if disabled else [])
    if len(actions) != 1:
        raise ValueError("a RichMessageButton needs exactly one action")
    if style == "link" and callback_data is None:
        raise ValueError('style "link" is allowed only for callback buttons')
    b: dict[str, Any] = {"text": text}
    if callback_data is not None:
        b["callback_data"] = callback_data
    elif url is not None:
        b["url"] = url
    elif copy_text is not None:
        b["copy_text"] = {"text": copy_text}
    else:
        b["disabled"] = {}
    if style:
        b["style"] = style
    return b


def button_row(buttons: list[dict[str, Any]], align: str = "left") -> dict[str, Any]:
    if not 1 <= len(buttons) <= BUTTON_ROW_MAX:
        raise ValueError("InputRichBlockButtons takes 1-8 buttons")
    return {"type": "buttons", "buttons": buttons, "align": align}


def inline_button_text(rich_text: RichText, button: dict[str, Any]) -> list[RichText]:
    """RichTextButton: a button inside a paragraph."""
    return [rich_text, {"type": "button", "button": button}]


# ---- reading ---------------------------------------------------------------

def plain(rt: RichText) -> str:
    if rt is None:
        return ""
    if isinstance(rt, str):
        return rt
    if isinstance(rt, list):
        return "".join(plain(x) for x in rt)
    if rt.get("type") == "button":
        return ""                     # buttons are not quotable text
    return plain(rt.get("text"))


def find_ton_addresses(rt: RichText) -> list[str]:
    """RichTextTonAddress (10.4) nodes -> addresses (shown text may be shortened)."""
    if isinstance(rt, list):
        return [a for x in rt for a in find_ton_addresses(x)]
    if isinstance(rt, dict):
        if rt.get("type") == "ton_address":
            return [rt["address"]]
        return find_ton_addresses(rt.get("text"))
    return []


def quote_text(quote: dict[str, Any]) -> str:
    """TextQuote -> plain text. Since 10.4 `text` may be EMPTY for a quote from a
    rich message; the content is in `rich_texts`. Code that reads only
    quote["text"] silently loses it."""
    if quote.get("text"):
        return quote["text"]
    return "\n".join(plain(rt) for rt in quote.get("rich_texts") or [])


def slice_rich(rt: RichText, start: int, end: int) -> RichText:
    """Characters [start, end) of a RichText, keeping nested formatting."""
    out, _ = _slice(rt, start, end, 0)
    return out


def _slice(rt: RichText, start: int, end: int, pos: int):
    if isinstance(rt, str):
        s, e = max(start - pos, 0), min(end - pos, len(rt))
        return (rt[s:e] if s < e else None), pos + len(rt)
    if isinstance(rt, list):
        items = []
        for x in rt:
            part, pos = _slice(x, start, end, pos)
            if part not in (None, "", []):
                items.append(part)
        return (items[0] if len(items) == 1 else items or None), pos
    inner, newpos = _slice(rt.get("text"), start, end, pos)
    return ({**rt, "text": inner} if inner not in (None, "", []) else None), newpos


def quote_from_paragraph(paragraph_text: RichText, start: int, end: int) -> list[RichText]:
    """quote_rich_texts for a quote inside ONE quotable text (a paragraph):
    a single element, possibly partial. Spanning several quotable texts needs
    one element per text, whole except the first and last."""
    part = slice_rich(paragraph_text, start, end)
    if not plain(part) or len(plain(part)) > QUOTE_MAX_CHARS:
        raise ValueError("quote must be 1-1024 characters")
    return [part]
