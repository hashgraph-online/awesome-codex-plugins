"""Build a consistent icon map from ONE custom-emoji set.

  # offline (fixture = a getStickerSet result saved as JSON):
  py -3 examples/python/icons/build_icon_map.py --sticker-set examples/python/icons/fixtures/tgmacicons.partial.json \
      --slots examples/python/icons/slots.json
  # live, with a TEST bot token (read-only methods, nothing is sent):
  TELEGRAM_LIVE=1 TELEGRAM_TEST_BOT_TOKEN=... py -3 examples/python/icons/build_icon_map.py --set tgmacicons --slots slots.json

`slots.json` maps semantic slots to the Unicode emoji you'd accept for them, in order of
preference: {"settings": ["⚙️", "⚙"], "back": ["⬅️", "◀️", "←"], ...}. Each sticker in a
custom emoji set carries `emoji` (its Unicode equivalent) and `custom_emoji_id`.
The output is an icon map for scripts/audit_icons.py plus the list of uncovered slots -
fill those from the SAME family's sibling pack or leave them label-only. Never guess ids.

Bot API: getStickerSet(name) -> StickerSet{name, title, sticker_type, stickers[]};
Sticker{emoji, custom_emoji_id, is_animated, is_video, set_name}.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tgkit.transport import live_transport_from_env  # noqa: E402

for _s in (sys.stdout,):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass


def _norm(e: str) -> str:
    return unicodedata.normalize("NFC", e.replace("️", ""))


def build(sticker_set: dict, slots: dict[str, list[str]], family: str | None = None) -> tuple[dict, list[str]]:
    if sticker_set.get("sticker_type") not in (None, "custom_emoji"):
        raise ValueError("not a custom emoji set")
    index: dict[str, dict] = {}
    for st in sticker_set.get("stickers", []):
        key = _norm(st.get("emoji", ""))
        index.setdefault(key, st)            # first sticker wins for an emoji
    icons, missing = {}, []
    for slot, wanted in slots.items():
        hit = next((index[_norm(w)] for w in wanted if _norm(w) in index), None)
        if hit is None:
            missing.append(slot)
            continue
        icons[slot] = {"id": hit["custom_emoji_id"], "set": sticker_set["name"], "family": family or sticker_set["name"],
                       "fallback": wanted[0], "animated": bool(hit.get("is_animated") or hit.get("is_video"))}
    return {"bot": "", "source": f"getStickerSet({sticker_set['name']})", "icons": icons}, missing


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sticker-set", help="getStickerSet result saved as JSON (offline)")
    ap.add_argument("--set", help="set name to fetch live (needs TELEGRAM_LIVE=1)")
    ap.add_argument("--slots", required=True)
    ap.add_argument("--family")
    a = ap.parse_args()
    slots = json.load(open(a.slots, encoding="utf-8"))
    if a.sticker_set:
        data = json.load(open(a.sticker_set, encoding="utf-8"))
        sticker_set = data.get("result", data)
    else:
        t = live_transport_from_env()
        if t is None or not a.set:
            print("Pass --sticker-set FILE, or --set NAME with TELEGRAM_LIVE=1 and a test bot token.")
            return 2
        sticker_set = t.call("getStickerSet", {"name": a.set})
    icon_map, missing = build(sticker_set, slots, a.family)
    print(json.dumps(icon_map, ensure_ascii=False, indent=2))
    if missing:
        print(f"\nuncovered slots ({len(missing)}): {', '.join(missing)} - use the same family's sibling set "
              f"or keep these buttons label-only", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
