#!/usr/bin/env python3
"""Audit a bot's icon system: one consistent custom-emoji family per bot.

Input: an icon map JSON (offline, no token):
  {"bot": "...", "icons": {"<slot>": {"id": "<custom_emoji_id>", "set": "<sticker set name>",
     "fallback": "<unicode emoji or ''>", "animated": false, "family": "<optional style family>"}},
   "text_prefixes": {"<slot>": "<unicode emoji used in message text for the same meaning>"}}
`set` is Sticker.set_name from getCustomEmojiStickers; `animated` = is_animated or is_video.
Build the map live with examples/python/icons/build_icon_map.py.

Errors (exit 1): non-numeric ids; the same id used for two meanings; missing fallback.
Warnings: icons from more than one set / family; animated mixed with static; a slot whose
text prefix differs from its button fallback (two visual languages for one meaning);
a set contributing a single icon (likely a gap-filler from another style).

These are design rules of this skill (Heuristic), not Bot API requirements.
Also (v2): fixture ids (leading 0, synthetic) are errors unless --allow-fixture-ids; adaptive
(needs_repainting) mixed with fixed-colour icons is a warning; `--payload FILE` audits the
requests of a payload file: double icons (error), mixed custom/Unicode keyboards and density
over this skill's heuristic limits (warnings).

Usage: python scripts/audit_icons.py icon-map.json [--max-sets 1] [--allow-fixture-ids]
       python scripts/audit_icons.py --payload examples/payloads/r70-restyle-to-premium.json
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "examples", "python"))
from tgkit.icons import _leading_cluster, density_warnings  # noqa: E402

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

ID_RE = re.compile(r"^\d{5,}$")


def audit(doc: dict, max_sets: int = 1, allow_fixture_ids: bool = False):
    errors: list[str] = []
    warnings: list[str] = []
    icons: dict = doc.get("icons", {})
    by_id = defaultdict(list)
    sets = Counter()
    families = Counter()
    animated = Counter()
    for slot, icon in icons.items():
        iid = str(icon.get("id", ""))
        if not ID_RE.match(iid):
            errors.append(f"{slot}: id {iid!r} is not a custom_emoji_id (numeric string)")
        elif iid.startswith("0") and not allow_fixture_ids:
            errors.append(f"{slot}: id {iid} is a synthetic fixture id (leading 0) - resolve real ids with getStickerSet")
        by_id[iid].append(slot)
        if not icon.get("fallback") and icon.get("fallback") != "":
            errors.append(f"{slot}: no Unicode fallback (use '' to mean 'label only')")
        sets[icon.get("set") or "<unknown>"] += 1
        families[icon.get("family") or icon.get("set") or "<unknown>"] += 1
        animated[bool(icon.get("animated"))] += 1
    for iid, slots in by_id.items():
        if len(slots) > 1:
            errors.append(f"id {iid} is used for different meanings: {', '.join(sorted(slots))}")
    if "<unknown>" in sets:
        warnings.append(f"{sets['<unknown>']} icon(s) without a recorded set - resolve with getCustomEmojiStickers")
    real_sets = {k: v for k, v in sets.items() if k != "<unknown>"}
    if len(families) > max_sets:
        warnings.append(f"{len(families)} icon families on one bot ({', '.join(f'{k}×{v}' for k, v in families.most_common())}) "
                        f"- pick one family; fill gaps from its sibling pack or drop the icon")
    family_of = {(i.get("set") or "<unknown>"): (i.get("family") or i.get("set") or "<unknown>") for i in icons.values()}
    for name, n in real_sets.items():
        if n == 1 and len(real_sets) > 1 and families[family_of[name]] == 1:
            warnings.append(f"set {name!r} supplies a single icon - a likely style outlier")
    adaptive = Counter(bool(i.get("adaptive")) for i in icons.values() if "adaptive" in i)
    if adaptive[True] and adaptive[False]:
        warnings.append(f"{adaptive[True]} adaptive (text-coloured) and {adaptive[False]} fixed-colour icons mixed - "
                        f"they look different on dark themes; choose one kind")
    if animated[True] and animated[False]:
        warnings.append(f"{animated[True]} animated and {animated[False]} static icons mixed - choose one")
    for slot, prefix in (doc.get("text_prefixes") or {}).items():
        fb = (icons.get(slot) or {}).get("fallback")
        if fb is not None and prefix and fb and prefix != fb:
            warnings.append(f"{slot}: text uses {prefix!r} but the button fallback is {fb!r} - one symbol per meaning")
    return errors, warnings


def _buttons(markup):
    for row in (markup or {}).get("inline_keyboard") or (markup or {}).get("keyboard") or []:
        for b in row:
            yield b if isinstance(b, dict) else {"text": b}


def audit_request(params: dict, *, post: bool = False):
    """One request: double icons are errors; mixed keyboards and density are warnings."""
    errors: list[str] = []
    warnings: list[str] = []
    markups = [params.get("reply_markup")] + [r.get("reply_markup") for r in params.get("results") or [] if isinstance(r, dict)]
    for markup in markups:
        with_icon, with_emoji = [], []
        for b in _buttons(markup):
            lead = _leading_cluster(b.get("text", ""))
            if b.get("icon_custom_emoji_id"):
                with_icon.append(b["text"])
                if lead:
                    errors.append(f"double icon on {b['text']!r}: icon_custom_emoji_id plus {lead[0]} in the label")
            elif lead:
                with_emoji.append(b["text"])
        if with_icon and with_emoji:
            warnings.append(f"mixed keyboard: custom icons on {len(with_icon)} button(s), Unicode emoji on "
                            f"{', '.join(map(repr, with_emoji))}")
    warnings += density_warnings(params, post=post)
    return errors, warnings


def audit_payload(doc: dict, *, post: bool = False):
    errors: list[str] = []
    warnings: list[str] = []
    for n, step in enumerate(doc.get("steps", []), 1):
        e, w = audit_request(step.get("params") or {}, post=post)
        errors += [f"step {n} {step.get('method')}: {x}" for x in e]
        warnings += [f"step {n} {step.get('method')}: {x}" for x in w]
    return errors, warnings


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("file", nargs="?")
    ap.add_argument("--max-sets", type=int, default=1, help="allowed families (default 1)")
    ap.add_argument("--allow-fixture-ids", action="store_true", help="accept synthetic fixture ids (offline demos)")
    ap.add_argument("--payload", help="audit the requests of a payload file instead of an icon map")
    ap.add_argument("--post", action="store_true", help="with --payload: use the post density budget")
    a = ap.parse_args(argv)
    if a.payload:
        doc = json.load(open(a.payload, encoding="utf-8"))
        errors, warnings = audit_payload(doc, post=a.post)
        for w in warnings:
            print(f"WARN: {w}")
        for e in errors:
            print(f"FAIL: {e}")
        print(f"\n{len(doc.get('steps', []))} request(s): {len(errors)} error(s), {len(warnings)} warning(s). "
              f"{'INVALID' if errors else 'OK'}.")
        return 1 if errors else 0
    if not a.file:
        ap.error("pass an icon map file or --payload FILE")
    doc = json.load(open(a.file, encoding="utf-8"))
    errors, warnings = audit(doc, a.max_sets, a.allow_fixture_ids)
    for w in warnings:
        print(f"WARN: {w}")
    for e in errors:
        print(f"FAIL: {e}")
    print(f"\n{len(doc.get('icons', {}))} icon(s): {len(errors)} error(s), {len(warnings)} warning(s). "
          f"{'INVALID' if errors else 'OK'}.")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
