"""Escaping per format, UTF-16 offsets, and splits that keep meaning.

* One escaper per format: regular HTML, MarkdownV2. Rich HTML uses the same
  entity escaping as HTML for text nodes; Rich Markdown is NOT MarkdownV2.
* MessageEntity offsets/lengths are UTF-16 code units, not characters/bytes.
* A split never cuts a surrogate pair, a combining sequence or an entity; the
  keyboard goes on the last part; every part keeps the same address.
"""
from __future__ import annotations

import unicodedata
from typing import Any

MDV2_SPECIAL = set("_*[]()~`>#+-=|{}.!\\")


def escape_html(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def escape_markdown_v2(s: str) -> str:
    return "".join("\\" + ch if ch in MDV2_SPECIAL else ch for ch in s)


def utf16_len(s: str) -> int:
    return len(s.encode("utf-16-le")) // 2


def utf16_offset(s: str, char_index: int) -> int:
    return utf16_len(s[:char_index])


def entity_for(text: str, fragment: str, etype: str, **extra: Any) -> dict[str, Any]:
    i = text.index(fragment)
    return {"type": etype, "offset": utf16_offset(text, i), "length": utf16_len(fragment), **extra}


def _safe_cut(text: str, cut: int) -> int:
    """Move `cut` left so it doesn't split a combining sequence / ZWJ emoji."""
    while 0 < cut < len(text) and (unicodedata.combining(text[cut]) or text[cut] in "‍️"
                                   or text[cut - 1] == "‍"):
        cut -= 1
    return cut


def split_text(text: str, entities: list[dict[str, Any]] | None = None,
               limit: int = 4096) -> list[tuple[str, list[dict[str, Any]]]]:
    """Split by UTF-16 length at paragraph > line > space boundaries, never
    inside an entity (unless one entity alone exceeds the limit). Entities are
    re-based for every part."""
    entities = sorted(entities or [], key=lambda e: e["offset"])
    parts: list[tuple[str, list[dict[str, Any]]]] = []
    start = 0  # char index
    while start < len(text):
        rest = text[start:]
        if utf16_len(rest) <= limit:
            end = len(text)
        else:
            hard = start
            while hard < len(text) and utf16_len(text[start:hard + 1]) <= limit:
                hard += 1
            end = None
            for sep in ("\n\n", "\n", " "):
                pos = text.rfind(sep, start, hard)
                if pos > start and not _inside_entity(text, pos, entities):
                    end = pos + len(sep)
                    break
            if end is None:
                end = _safe_cut(text, hard)
            if end <= start:
                # One combining/ZWJ sequence longer than the limit: a hard cut is the only
                # way forward (otherwise the loop never advances).
                end = max(hard, start + 1)
        chunk = text[start:end]
        base = utf16_offset(text, start)
        span = utf16_len(chunk)
        local = []
        for e in entities:
            s, l = e["offset"] - base, e["length"]
            if s + l <= 0 or s >= span:
                continue
            ns, ne = max(s, 0), min(s + l, span)
            local.append({**e, "offset": ns, "length": ne - ns})
        stripped = chunk.rstrip("\n ")
        trim = utf16_len(chunk) - utf16_len(stripped)
        if trim:
            local = [{**e, "length": min(e["length"], utf16_len(stripped) - e["offset"])}
                     for e in local if e["offset"] < utf16_len(stripped)]
        if stripped:                      # never emit an empty (unsendable) part
            parts.append((stripped, local))
        start = end
    return parts


def _inside_entity(text: str, char_pos: int, entities: list[dict[str, Any]]) -> bool:
    off = utf16_offset(text, char_pos)
    return any(e["offset"] < off < e["offset"] + e["length"] for e in entities)


def send_long(transport: Any, address: dict[str, Any], text: str,
              entities: list[dict[str, Any]] | None = None,
              reply_markup: dict[str, Any] | None = None, limit: int = 4096) -> list[Any]:
    """Send parts in order; the same address on each part, markup on the last.
    A failure stops the sequence and propagates - no silent gap."""
    parts = split_text(text, entities, limit)
    results = []
    for i, (chunk, ents) in enumerate(parts):
        params: dict[str, Any] = {**address, "text": chunk}
        if ents:
            params["entities"] = ents
        if reply_markup and i == len(parts) - 1:
            params["reply_markup"] = reply_markup
        results.append(transport.call("sendMessage", params))
    return results
