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
  * every button row / RichTextButton (via validate_keyboard rich model)
  * reply_parameters.quote_rich_texts: <= 32 texts, <= 1024 characters in total
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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import validate_keyboard  # noqa: E402

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

LIMITS = {"chars": 32768, "blocks": 500, "depth": 16, "media": 50, "columns": 20}
MEDIA_TYPES = {"photo", "video", "animation", "audio", "voice_note", "document"}
MEDIA_REF_RE = re.compile(r"tg://(photo|video|document|audio)\?id=([^\s\"')>]+)")
MEDIA_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def _text_len(rt) -> int:
    if isinstance(rt, str):
        return len(rt)
    if isinstance(rt, list):
        return sum(_text_len(x) for x in rt)
    if isinstance(rt, dict):
        return _text_len(rt.get("text")) + _text_len(rt.get("credit"))
    return 0


class Counter:
    def __init__(self) -> None:
        self.blocks = self.chars = self.media = self.max_depth = 0
        self.errors: list[str] = []


def walk(block, depth: int, c: Counter, path: str, draft: bool) -> None:
    if not isinstance(block, dict):
        c.errors.append(f"{path}: block must be an object")
        return
    c.blocks += 1
    c.max_depth = max(c.max_depth, depth)
    t = block.get("type")
    if t == "thinking" and not draft:
        c.errors.append(f"{path}: 'thinking' blocks are allowed only in sendRichMessageDraft")
    for key in ("text", "credit", "caption"):
        c.chars += _text_len(block.get(key) if key != "caption" else (block.get("caption") or {}))
    if t in MEDIA_TYPES:
        c.media += 1
        media = block.get(t) or {}
        ref = media.get("media", "") if isinstance(media, dict) else ""
        if draft and (ref.startswith("attach://") or ref.startswith("http")):
            c.errors.append(f"{path}: drafts can't upload new files or fetch by URL - send the file first, reuse file_id")
    if t == "table":
        rows = block.get("cells") or []
        c.blocks += len(rows)
        for r, row in enumerate(rows):
            width = sum(int(cell.get("colspan", 1)) for cell in row if isinstance(cell, dict))
            if width > LIMITS["columns"]:
                c.errors.append(f"{path}.cells[{r}]: {width} columns > {LIMITS['columns']}")
            for cell in row:
                if isinstance(cell, dict):
                    c.chars += _text_len(cell.get("text"))
        c.chars += _text_len(block.get("caption"))
    if t == "list":
        for i, item in enumerate(block.get("items") or []):
            c.blocks += 1
            for j, b in enumerate(item.get("blocks") or []):
                walk(b, depth + 2, c, f"{path}.items[{i}].blocks[{j}]", draft)
    for key in ("blocks",):
        for i, b in enumerate(block.get(key) or []):
            walk(b, depth + 1, c, f"{path}.{key}[{i}]", draft)


def validate(payload: dict, *, draft: bool = False):
    errors: list[str] = []
    warnings: list[str] = []
    msg = payload.get("rich_message", payload)
    forms = [k for k in ("html", "markdown", "blocks") if k in msg]
    if len(forms) != 1:
        errors.append(f"InputRichMessage needs exactly one of html/markdown/blocks, found {forms}")
    c = Counter()
    if "blocks" in msg:
        for i, b in enumerate(msg["blocks"]):
            walk(b, 1, c, f"blocks[{i}]", draft)
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
    checks = [("chars", c.chars), ("blocks", c.blocks), ("media", c.media), ("depth", c.max_depth)]
    for name, value in checks:
        if value > LIMITS[name]:
            errors.append(f"{name}: {value} > {LIMITS[name]} (Rich Message Limits)")
    errors += c.errors
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
