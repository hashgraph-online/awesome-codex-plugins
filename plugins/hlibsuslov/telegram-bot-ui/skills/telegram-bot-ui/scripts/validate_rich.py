#!/usr/bin/env python3
"""Check an InputRichMessage (or a sendRichMessage / draft payload) offline.

Errors
  * exactly one of html / markdown / blocks
  * Rich Message Limits (Bot API, verified 2026-11-12): 32768 UTF-8 characters,
    500 blocks (nested blocks, list items, table rows, quotations and details
    count), 16 nesting levels, 50 media, 20 table columns
  * `thinking` blocks only in sendRichMessageDraft (--draft)
  * drafts: no new uploads (attach://) and no explicit URL uploads in media
  * markdown/html `tg://photo|video|document|audio?id=X` must have a media[] entry
    with id X (1-64 of A-Z a-z 0-9 _ -), and every media entry should be used
  * every button row / RichTextButton (via validate_keyboard rich model): 1-8 buttons, exactly one
    action, callback_data 1-64 bytes, style "link" only on callback buttons, label text plain,
    custom emoji and date-time only, align left / center / right
  * reply_parameters.quote_rich_texts: <= 32 texts, <= 1024 characters in total
Blocks are checked against the catalog (data/bot-api/catalog.json), as deeply as HTML:
  * the block and RichText `type` must be an InputRichBlock / RichText member; unknown and missing
    required fields of blocks, texts, list items, table cells and captions are errors
  * nesting depth counts blocks and nested formatting (a bold inside an italic is two levels)
  * the rules the catalog states in prose, quoted in QUOTES: heading size, list item label type,
    table cell align / valign, map zoom / size / ratio, the InputMedia* a media block takes and its
    ignored caption, `media` being for markdown/html, thinking only in drafts
  * table width counts colspan and the rows a rowspan reaches; text counts every RichText once,
    plus custom emoji alternative text, formula source and button labels
For markdown/html the character and block counts are approximations from the
source text (the server parses it); for blocks they are counted exactly.

Usage: python scripts/validate_rich.py payload.json [--draft]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from functools import lru_cache

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import validate_keyboard  # noqa: E402
from sync_bot_api import DATA_DIR, load_catalog  # noqa: E402

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

LIMITS = {"chars": 32768, "blocks": 500, "depth": 16, "media": 50, "columns": 20}
MEDIA_REF_RE = re.compile(r"tg://(photo|video|document|audio)\?id=([^\s\"')>]+)")
MEDIA_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
# Markdown code (fenced to the closing fence or the end, then inline spans) shows tags, it does not use them.
FENCE_RE = re.compile(r"^ {0,3}(?P<f>`{3,}|~{3,})[^\n]*\n.*?(?:^ {0,3}(?P=f)[`~]*[ \t]*$|\Z)", re.M | re.S)
CODE_SPAN_RE = re.compile(r"(?<!`)(`+)(?!`).+?(?<!`)\1(?!`)", re.S)

# Rules the catalog states in prose: key -> (type, field or None for the type's own description, quote).
# tests/test_rich_blocks.py fails when a quote is no longer the catalog's text (straight quotes).
QUOTES = {
    "heading_size": ("InputRichBlockSectionHeading", "size", "1-6, 1 is the largest, 6 is the smallest"),
    "list_label": ("InputRichBlockListItem", "type",
                   'must be one of "a" for lowercase letters, "A" for uppercase letters, "i" for lowercase Roman '
                   'numerals, "I" for uppercase Roman numerals, or "1" for decimal numbers'),
    "cell_align": ("RichBlockTableCell", "align", 'must be one of "left", "center", or "right"'),
    "cell_valign": ("RichBlockTableCell", "valign", 'must be one of "top", "middle", or "bottom"'),
    "map_zoom": ("InputRichBlockMap", "zoom", "Map zoom level; 0-24"),
    "map_width": ("InputRichBlockMap", "width", "Map width; 0-10000"),
    "map_height": ("InputRichBlockMap", "height", "Map height; 0-10000"),
    "map_size": ("InputRichBlockMap", None, "The map's width and height must not exceed 10000 in total. "
                                            "The width and height ratio must be at most 20."),
    "media_caption": ("InputRichBlockPhoto", "photo", "Caption is ignored."),
    "media_field": ("InputRichMessage", "media", "List of media that are specified in the markdown or html fields"),
    "thinking": ("InputRichBlockThinking", None, "may be used only in sendRichMessageDraft"),
    "button_row": ("InputRichBlockButtons", "buttons", "List of 1-8 buttons to send"),
    "button_text": ("RichMessageButton", "text",
                    "May contain only plain text, RichTextCustomEmoji and RichTextDateTime entities."),
    "callback_data": ("RichMessageButton", "callback_data", "1-64 bytes"),
}
LIST_LABELS = {"a", "A", "i", "I", "1"}
CELL_ALIGN = {"left", "center", "right"}
CELL_VALIGN = {"top", "middle", "bottom"}
RANGES = {"heading": {"size": (1, 6)}, "map": {"zoom": (0, 24), "width": (0, 10000), "height": (0, 10000)}}
MAP_TOTAL, MAP_RATIO = 10000, 20
# Official, not the catalog: the Rich HTML style section lists <img> and <video> as the children of
# <tg-collage> and <tg-slideshow> (core.telegram.org/bots/api#rich-html-style, checked 2026-11-25).
GALLERY_ITEMS = {"photo", "video", "animation"}
IGNORED_MEDIA_KEYS = ("caption", "parse_mode", "caption_entities", "show_caption_above_media")


def _without_markdown_code(src: str) -> str:
    return CODE_SPAN_RE.sub(" ", FENCE_RE.sub("\n", src))


def _text_len(rt) -> int:
    if isinstance(rt, str):
        return len(rt)
    if isinstance(rt, list):
        return sum(_text_len(x) for x in rt)
    if isinstance(rt, dict):
        return _text_len(rt.get("text")) + _text_len(rt.get("credit"))
    return 0


@lru_cache(maxsize=1)
def _spec() -> tuple[dict, dict[str, str], dict[str, str]]:
    """(catalog types, block type constant -> InputRichBlock member, text type constant -> RichText member)."""
    types = load_catalog(DATA_DIR)["types"]

    def members(union: str) -> dict[str, str]:
        out = {}
        for name in types[union]["subtypes"]:
            const = next((f.get("const") for f in types[name]["fields"] if f["name"] == "type"), None)
            if const:
                out[const] = name
        return out
    return types, members("InputRichBlock"), members("RichText")


def _array(v) -> list:
    """The value when it is a JSON array, else nothing to walk (the wrong kind is reported where it is read)."""
    return v if isinstance(v, list) else []


def _int(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


class Counter:
    def __init__(self, draft: bool = False) -> None:
        self.blocks = self.chars = self.media = self.max_depth = 0
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.draft = draft

    def deeper(self, depth: int) -> None:
        self.max_depth = max(self.max_depth, depth)

    def fields(self, obj: dict, type_name: str, path: str) -> dict:
        """Unknown and missing required fields of one object, from the catalog. Returns the field specs."""
        spec = {f["name"]: f for f in _spec()[0][type_name]["fields"]}
        for key in obj:
            if key not in spec:
                self.errors.append(f"{path}: {type_name} has no field {key!r}")
        for name, f in spec.items():
            if f["required"] and name not in obj:
                self.errors.append(f"{path}: {type_name} is missing required field {name!r} ({f['type']})")
        return spec


def text(rt, depth: int, c: Counter, path: str) -> None:
    """A RichText at block depth `depth`: each formatting object nests one level deeper."""
    if rt is None:
        return
    if isinstance(rt, str):
        c.chars += len(rt)
        c.deeper(depth)
        return
    if isinstance(rt, list):
        for i, x in enumerate(rt):
            text(x, depth, c, f"{path}[{i}]")
        return
    if not isinstance(rt, dict):
        c.errors.append(f"{path}: RichText is a string, an array of RichText or a RichText object")
        return
    t = rt.get("type")
    name = _spec()[2].get(t) if isinstance(t, str) else None
    if name is None:
        c.errors.append(f"{path}: {t!r} is not a RichText type")
        return
    c.fields(rt, name, path)
    c.deeper(depth + 1)
    for key in ("alternative_text", "expression"):  # "including custom emoji alternative text and formula source"
        if isinstance(rt.get(key), str):
            c.chars += len(rt[key])
    if t == "button" and isinstance(rt.get("button"), dict):
        text(rt["button"].get("text"), depth + 1, c, f"{path}.button.text")
    text(rt.get("text"), depth + 1, c, f"{path}.text")


def _caption(cap, depth: int, c: Counter, path: str) -> None:
    if not isinstance(cap, dict):
        c.errors.append(f"{path}: a block caption is a RichBlockCaption object {{\"text\", \"credit\"?}}")
        return
    c.fields(cap, "RichBlockCaption", path)
    text(cap.get("text"), depth, c, f"{path}.text")
    text(cap.get("credit"), depth, c, f"{path}.credit")


def _media(block: dict, field: dict, c: Counter, path: str) -> None:
    c.media += 1
    t, expected = block["type"], field["types"][0]["name"]
    want = next((f.get("const") for f in _spec()[0][expected]["fields"] if f["name"] == "type"), None)
    media = block.get(t)
    if not isinstance(media, dict) or media.get("type") != want:
        c.errors.append(f"{path}.{t}: a {t} block takes {expected} (type {want!r})")
        return
    c.fields(media, expected, f"{path}.{t}")
    ignored = [k for k in IGNORED_MEDIA_KEYS if k in media]
    if ignored:
        c.warnings.append(f"{path}.{t}: {', '.join(ignored)}: \"{QUOTES['media_caption'][2]}\" "
                          f"(catalog) - put the caption in the block's caption")
    ref = media.get("media", "")
    if "media" in media and (not isinstance(ref, str) or not ref):
        c.errors.append(f"{path}.{t}.media: a file_id, an HTTP URL or attach://<name> (a non-empty string)")
    if c.draft and isinstance(ref, str) and (ref.startswith("attach://") or ref.startswith("http")):
        c.errors.append(f"{path}: drafts can't upload new files or fetch by URL - send the file first, reuse file_id")


def _ranges(block: dict, c: Counter, path: str) -> None:
    for key, (lo, hi) in RANGES.get(block["type"], {}).items():
        v = block.get(key)
        if v is not None and not (_int(v) and lo <= v <= hi):
            quote = QUOTES["heading_size"][2] if key == "size" else f"{lo}-{hi}"
            c.errors.append(f"{path}: {key} {v}: {quote}")
    if block["type"] != "map":
        return
    w, h = block.get("width"), block.get("height")
    if _int(w) and _int(h):
        if w + h > MAP_TOTAL:  # "must not exceed 10000 in total", read as width + height
            c.errors.append(f"{path}: width {w} + height {h}: \"{QUOTES['map_size'][2]}\"")
        elif min(w, h) > 0 and max(w, h) / min(w, h) > MAP_RATIO:
            c.errors.append(f"{path}: width/height ratio {max(w, h) / min(w, h):.1f} > {MAP_RATIO}")


def _list(block: dict, depth: int, c: Counter, path: str) -> None:
    for i, item in enumerate(_array(block.get("items"))):
        at = f"{path}.items[{i}]"
        if not isinstance(item, dict):
            c.errors.append(f"{at}: a list item is an InputRichBlockListItem object")
            continue
        c.blocks += 1
        c.fields(item, "InputRichBlockListItem", at)
        label = item.get("type")
        if label is not None and (not isinstance(label, str) or label not in LIST_LABELS):
            c.errors.append(f"{at}: type {label!r}: {QUOTES['list_label'][2]}")
        if "blocks" in item and not isinstance(item["blocks"], list):
            c.errors.append(f"{at}.blocks: an array of InputRichBlock")
        for j, b in enumerate(_array(item.get("blocks"))):
            walk(b, depth + 2, c, f"{at}.blocks[{j}]")


def _table(block: dict, depth: int, c: Counter, path: str) -> None:
    rows = _array(block.get("cells"))
    c.blocks += len(rows)
    carried = [0] * len(rows)  # columns taken by rowspans from the rows above
    for r, row in enumerate(rows):
        if not isinstance(row, list):
            c.errors.append(f"{path}.cells[{r}]: a row is an array of RichBlockTableCell")
            continue
        width = carried[r]
        for k, cell in enumerate(row):
            at = f"{path}.cells[{r}][{k}]"
            if not isinstance(cell, dict):
                c.errors.append(f"{at}: a cell is a RichBlockTableCell object")
                continue
            c.fields(cell, "RichBlockTableCell", at)
            for key, allowed, quote in (("align", CELL_ALIGN, "cell_align"), ("valign", CELL_VALIGN, "cell_valign")):
                if key in cell and (not isinstance(cell[key], str) or cell[key] not in allowed):
                    c.errors.append(f"{at}: {key} {cell[key]!r}: {QUOTES[quote][2]}")
            span = cell.get("colspan", 1) if _int(cell.get("colspan", 1)) else 1
            width += span
            rowspan = cell.get("rowspan", 1) if _int(cell.get("rowspan", 1)) else 1
            for below in range(r + 1, min(r + rowspan, len(rows))):
                carried[below] += span
            text(cell.get("text"), depth + 1, c, f"{at}.text")
        if width > LIMITS["columns"]:
            c.errors.append(f"{path}.cells[{r}]: {width} columns > {LIMITS['columns']}")


def walk(block, depth: int, c: Counter, path: str) -> None:
    if not isinstance(block, dict):
        c.errors.append(f"{path}: block must be an object")
        return
    c.blocks += 1
    c.deeper(depth)
    t = block.get("type")
    name = _spec()[1].get(t) if isinstance(t, str) else None
    if name is None:
        c.errors.append(f"{path}: {t!r} is not an InputRichBlock type (one of {', '.join(sorted(_spec()[1]))})")
        return
    if t == "thinking" and not c.draft:
        c.errors.append(f"{path}: 'thinking' blocks are allowed only in sendRichMessageDraft")
    spec = c.fields(block, name, path)
    for key, f in spec.items():
        if key == "type" or key not in block:
            continue
        value, kind = block[key], f["type"]
        if value is None:
            c.errors.append(f"{path}.{key}: null - leave an optional field out, a required one needs a {kind}")
            continue
        if kind.startswith("Array of") and not isinstance(value, list):
            c.errors.append(f"{path}.{key}: an array of {kind[len('Array of '):]}")
            continue
        if kind == "RichText":
            text(value, depth, c, f"{path}.{key}")
        elif kind == "RichBlockCaption":
            _caption(value, depth, c, f"{path}.{key}")
        elif kind == "Array of InputRichBlock":
            for i, b in enumerate(value):
                walk(b, depth + 1, c, f"{path}.{key}[{i}]")
        elif kind.startswith("InputMedia"):
            _media(block, f, c, path)
    if t == "mathematical_expression" and isinstance(block.get("expression"), str):
        c.chars += len(block["expression"])
    if t == "buttons":
        for i, b in enumerate(_array(block.get("buttons"))):
            if isinstance(b, dict):  # the button rules are validate_keyboard's; the labels are text
                text(b.get("text"), depth, c, f"{path}.buttons[{i}].text")
    if t in ("collage", "slideshow") and any(isinstance(b, dict) and str(b.get("type")) not in GALLERY_ITEMS
                                             for b in _array(block.get("blocks"))):
        c.warnings.append(f"{path}: a {t} holds photos and videos (Official: Rich HTML style lists <img> and "
                          f"<video> as its children)")
    _ranges(block, c, path)
    if t == "list":
        _list(block, depth, c, path)
    elif t == "table":
        _table(block, depth, c, path)


def validate(payload: dict, *, draft: bool = False):
    errors: list[str] = []
    warnings: list[str] = []
    msg = payload.get("rich_message", payload)
    forms = [k for k in ("html", "markdown", "blocks") if k in msg]
    if len(forms) != 1:
        errors.append(f"InputRichMessage needs exactly one of html/markdown/blocks, found {forms}")
    c = Counter(draft)
    if "blocks" in msg:
        if not isinstance(msg["blocks"], list):
            errors.append("blocks: an array of InputRichBlock")
        for i, b in enumerate(_array(msg["blocks"])):
            walk(b, 1, c, f"blocks[{i}]")
        if msg.get("media"):
            warnings.append(f"media: \"{QUOTES['media_field'][2]}\" - a blocks message carries its media "
                            f"inside the media blocks")
    else:
        src = msg.get("html") or msg.get("markdown") or ""
        c.chars = len(src)  # upper bound: markup characters included
        c.blocks = len(re.findall(r"<(p|h[1-6]|li|tr|blockquote|details|figure|table|ul|ol)\b", src)) + \
            len([ln for ln in src.splitlines() if ln.strip()]) * (1 if "markdown" in msg else 0)
        if draft and "<tg-thinking" not in src and "thinking" in src:
            warnings.append("draft mentions 'thinking' but has no <tg-thinking> block")
        if not draft and "<tg-thinking" in src:
            errors.append("<tg-thinking> is allowed only in sendRichMessageDraft")
        refs = {m.group(2) for m in MEDIA_REF_RE.finditer(src)}
        media = msg.get("media") or []
        ids = {m.get("id") for m in media}
        for r in sorted(refs - ids):
            errors.append(f"tg://…?id={r} has no media[] entry")
        for m in media:
            if not MEDIA_ID_RE.match(str(m.get("id", ""))):
                errors.append(f"media id {m.get('id')!r} must be 1-64 of A-Z a-z 0-9 _ -")
            ref = (m.get("media") or {}).get("media", "")
            if draft and (ref.startswith("attach://") or ref.startswith("http")):
                errors.append(f"media {m.get('id')}: drafts can't upload new files or fetch by URL")
        for unused in sorted(ids - refs):
            warnings.append(f"media id {unused!r} is never referenced")
        c.media = len(media)
        from bot_ui import rich as rich_html  # button rows, button types and styles in the HTML tags
        for code, sev, message in rich_html.check(_without_markdown_code(src) if "markdown" in msg else src, draft=draft):
            if code == "TEXT_TOO_LONG" or (code == "RICH_TAG_UNSUPPORTED" and "markdown" in msg):
                continue  # length is counted below; Rich Markdown may hold other HTML
            (errors if sev == "error" else warnings).append(f"{code}: {message}")
    checks = [("chars", c.chars), ("blocks", c.blocks), ("media", c.media), ("depth", c.max_depth)]
    for name, value in checks:
        if value > LIMITS[name]:
            errors.append(f"{name}: {value} > {LIMITS[name]} (Rich Message Limits)")
    errors += c.errors
    warnings += c.warnings
    if "blocks" in msg:
        kb = validate_keyboard.validate({"blocks": msg["blocks"]})
        errors += kb.errors
        warnings += [w for w in kb.warnings if w != "rich message has no buttons"]
    rp = payload.get("reply_parameters") or {}
    q = rp.get("quote_rich_texts")
    if q is not None:
        if not isinstance(q, list) or not 1 <= len(q) <= 32:
            errors.append("quote_rich_texts: 1-32 quoted texts")
        elif sum(_text_len(x) for x in q) > 1024:
            errors.append("quote_rich_texts: more than 1024 characters in total")
    if "reply_markup" in payload:
        kb = validate_keyboard.validate(payload["reply_markup"])
        errors += kb.errors
        warnings += kb.warnings
    return errors, warnings, c


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--draft", action="store_true", help="payload is for sendRichMessageDraft")
    a = ap.parse_args(argv)
    with open(a.file, encoding="utf-8") as fh:
        payload = json.load(fh)
    errors, warnings, c = validate(payload, draft=a.draft)
    for w in warnings:
        print(f"WARN: {w}")
    for e in errors:
        print(f"FAIL: {e}")
    print(f"\nblocks={c.blocks} chars={c.chars} media={c.media} depth={c.max_depth}. "
          f"{'INVALID' if errors else 'OK'}.")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
