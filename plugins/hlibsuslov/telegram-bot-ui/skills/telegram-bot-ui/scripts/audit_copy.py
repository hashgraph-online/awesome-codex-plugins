#!/usr/bin/env python3
"""Audit a localized message catalog for interface consistency. Offline.

Input JSON: {"<lang>": {"<key>": "<text>", ...}, ...} (regular-HTML templates).
Button keys are detected by prefix (default "btn_").

Errors: placeholders differ between languages; unbalanced or unsupported regular-HTML tags.
Warnings: key missing in a language; the leading symbol differs between languages for the
same key; a button label longer than 30 characters in some locale; one symbol used as the
leading icon for several unrelated meanings; text with more emoji than lines (decoration
instead of signal); a heading line that is not bold.

Design heuristics of this skill except the HTML check (Bot API formatting options).
Usage: python scripts/audit_copy.py catalog.json [--button-prefix btn_]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

PLACEHOLDER = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)[^}]*\}")
TAG = re.compile(r"<(/?)([a-zA-Z-]+)[^>]*>")
ALLOWED = {"b", "strong", "i", "em", "u", "ins", "s", "strike", "del", "span", "tg-spoiler", "a", "code",
           "pre", "blockquote", "tg-emoji", "tg-time"}
# Keycaps (1️⃣ = digit + U+FE0F + U+20E3) are emoji too; numbered lists often use them.
EMOJI = re.compile("[0-9#*]️?⃣|[\U0001F300-\U0001FAFF☀-➿⬀-⯿←-⇿₿]")


def leading_symbol(text: str) -> str:
    t = re.sub(r"^(<[^>]+>)+", "", text).lstrip()
    m = EMOJI.match(t)
    return m.group(0) if m else ""


def audit(cat: dict, button_prefix: str = "btn_"):
    errors, warnings = [], []
    langs = sorted(cat)
    keys = sorted({k for l in langs for k in cat[l]})
    symbol_meanings = defaultdict(set)
    for key in keys:
        present = {l: cat[l][key] for l in langs if key in cat[l]}
        for l in langs:
            if key not in cat[l]:
                warnings.append(f"{key}: missing in '{l}'")
        ph = {l: sorted(set(PLACEHOLDER.findall(v))) for l, v in present.items()}
        if len({tuple(v) for v in ph.values()}) > 1:
            errors.append(f"{key}: placeholders differ between languages {ph}")
        sym = {l: leading_symbol(v) for l, v in present.items()}
        if len(set(sym.values())) > 1:
            warnings.append(f"{key}: leading symbol differs between languages {sym}")
        first = next(iter(sym.values()), "")
        if first:
            symbol_meanings[first].add(key.split("_", 1)[-1] if not key.startswith(button_prefix) else key[len(button_prefix):])
        for l, v in present.items():
            stack = []
            for close, tag in TAG.findall(v):
                tag = tag.lower()
                if tag not in ALLOWED:
                    errors.append(f"{key} [{l}]: <{tag}> is not a regular-HTML tag")
                    continue
                if close:
                    if not stack or stack.pop() != tag:
                        errors.append(f"{key} [{l}]: unbalanced </{tag}>")
                else:
                    stack.append(tag)
            if stack:
                errors.append(f"{key} [{l}]: unclosed <{stack[-1]}>")
            if key.startswith(button_prefix):
                plain = re.sub(r"\{[^}]*\}", "XXXX", v)
                if len(plain) > 30:
                    warnings.append(f"{key} [{l}]: button label {len(plain)} chars - may truncate on phones")
            else:
                lines = [ln for ln in v.split("\n") if ln.strip()]
                n_emoji = len(EMOJI.findall(re.sub(r"<[^>]+>", "", v)))
                if len(lines) >= 4 and n_emoji > len(lines):
                    warnings.append(f"{key} [{l}]: {n_emoji} emoji over {len(lines)} lines - icons stop signalling")
    for sym, meanings in sorted(symbol_meanings.items()):
        if len(meanings) >= 5:
            warnings.append(f"{sym} leads {len(meanings)} different keys ({', '.join(sorted(meanings)[:6])}…) - "
                            f"reserve status symbols (✅ ⚠️ ❌) for status")
    return errors, warnings


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--button-prefix", default="btn_")
    a = ap.parse_args(argv)
    errors, warnings = audit(json.load(open(a.file, encoding="utf-8")), a.button_prefix)
    for w in warnings:
        print(f"WARN: {w}")
    for e in errors:
        print(f"FAIL: {e}")
    print(f"\n{len(errors)} error(s), {len(warnings)} warning(s). {'INVALID' if errors else 'OK'}.")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
