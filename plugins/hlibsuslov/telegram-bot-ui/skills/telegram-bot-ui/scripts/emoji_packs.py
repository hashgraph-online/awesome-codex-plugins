#!/usr/bin/env python3
"""Premium (custom) emoji packs for a bot: resolve, suggest, verify, capture, apply, strip.

Offline by default (saved JSON / fixtures). Live mode calls ONLY the read-only methods
getStickerSet and getCustomEmojiStickers and needs TELEGRAM_LIVE=1 plus
TELEGRAM_TEST_BOT_TOKEN (see examples/python/tgkit/transport.py). Nothing is sent to a chat.
Ids are never invented: a slot without a matching sticker stays unset.

  py -3 scripts/emoji_packs.py resolve --sticker-set examples/python/icons/fixtures/demo_line_icons.json \\
        --sticker-set examples/python/icons/fixtures/demo_line_icons_extra.json --slots home,back,settings,done
  TELEGRAM_LIVE=1 TELEGRAM_TEST_BOT_TOKEN=... py -3 scripts/emoji_packs.py resolve --set tgmacicons --set tgiosicons
  py -3 scripts/emoji_packs.py suggest --from examples/payloads/r70-restyle-to-premium.json --archetype monitoring
  py -3 scripts/emoji_packs.py verify --map icon-map.json --response saved-getCustomEmojiStickers.json
  py -3 scripts/emoji_packs.py capture [--update saved-update.json]
  py -3 scripts/emoji_packs.py apply --map icon-map.json --in payload.json --context private --owner-premium
  py -3 scripts/emoji_packs.py strip --map icon-map.json --in payload.json

Data: data/emoji/slots.json (slot vocabulary), data/emoji/packs.json (verified public sets,
metadata only). Reference: references/emoji-packs.md.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "examples", "python"))
from tgkit.icons import (EmojiMap, Eligibility, IconSystem, SendContext, apply_request, emoji_key,  # noqa: E402
                         ids_from_message, load_vocabulary, resolve_icon_map, slots_in, strip_request,
                         verify_ids)
from tgkit.transport import live_transport_from_env  # noqa: E402

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

PACKS = os.path.join(ROOT, "data", "emoji", "packs.json")


def _load(path: str):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _result(doc):
    return doc.get("result", doc) if isinstance(doc, dict) else doc


def _emit(obj, out: str | None) -> None:
    text = json.dumps(obj, ensure_ascii=False, indent=2) + "\n"
    if out:
        with open(out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
    else:
        sys.stdout.write(text)


def _live():
    t = live_transport_from_env()
    if t is None:
        raise SystemExit("live mode needs TELEGRAM_LIVE=1 and TELEGRAM_TEST_BOT_TOKEN; or pass saved JSON files")
    return t


def _slot_list(a, vocab) -> list[str] | None:
    if a.slots:
        return [s.strip() for s in a.slots.split(",") if s.strip()]
    if a.slots_file:
        data = _load(a.slots_file)
        return list(data["slots"] if "slots" in data else data)
    return None


def load_sets(files: list[str] | None, names: list[str] | None) -> list[dict]:
    sets = [_result(_load(f)) for f in files or []]
    if names:
        t = _live()
        sets += [t.call("getStickerSet", {"name": n}) for n in names]
    return sets


# ---- resolve ----------------------------------------------------------------

def cmd_resolve(a) -> int:
    vocab = load_vocabulary(a.vocabulary)
    sets = load_sets(a.sticker_set, a.set)
    if not sets:
        print("pass --sticker-set FILE (offline) or --set NAME (live)", file=sys.stderr)
        return 2
    doc, rep = resolve_icon_map(sets, vocab, _slot_list(a, vocab), family=a.family)
    _emit(doc, a.out)
    print(f"\ncoverage {rep['covered']}/{rep['requested']} ({rep['coverage']:.0%}) from {', '.join(rep['sets'])}; "
          f"per set {rep['per_set']}", file=sys.stderr)
    if rep["uncovered"]:
        print(f"uncovered ({len(rep['uncovered'])}): {', '.join(rep['uncovered'][:40])}"
              f"{' …' if len(rep['uncovered']) > 40 else ''} - keep these label-only or add a SIBLING set "
              f"of the same family", file=sys.stderr)
    for c in rep["conflicts"]:
        print(f"conflict: {c}", file=sys.stderr)
    if rep["unknown_slots"]:
        print(f"unknown slots (not in the vocabulary): {', '.join(rep['unknown_slots'])}", file=sys.stderr)
    if any(i["id"].startswith("0") for i in doc["icons"].values()):
        print("note: synthetic fixture ids (leading 0) - demo only, resolve a real set before use", file=sys.stderr)
    return 0


# ---- suggest ----------------------------------------------------------------

def needed_slots(source, vocab) -> list[str]:
    """Slots implied by the Unicode emoji found in texts/keyboards/payloads (any JSON or text)."""
    return slots_in(source, vocab)


def rank_packs(needed: list[str], vocab, packs: list[dict], *, sets: list[dict] | None = None,
               archetype: str | None = None, tone: str | None = None) -> list[dict]:
    """Real coverage when saved sets are given; otherwise a metadata-only estimate."""
    ranked = []
    by_name = {s["name"].lower(): s for s in sets or []}
    groups_needed = Counter(vocab[s]["group"] for s in needed if s in vocab)
    for p in packs:
        row = {"name": p["name"], "family": p["family"], "link": p["link"], "animation": p.get("animation")}
        st = by_name.get(p["name"].lower())
        if st:
            _, rep = resolve_icon_map([st], vocab, needed)
            row.update(basis="resolved", coverage=rep["coverage"], uncovered=rep["uncovered"])
            score = rep["coverage"]
            anim = Counter(bool(x.get("is_animated") or x.get("is_video")) for x in st["stickers"])
            row["static_share"] = round(anim[False] / max(1, sum(anim.values())), 2)
            score -= 0.2 * (1 - row["static_share"])
        else:
            hint = set(p.get("groups_hint") or [])
            share = sum(n for g, n in groups_needed.items() if g in hint) / max(1, sum(groups_needed.values()))
            row.update(basis="metadata only - resolve to confirm", coverage_estimate=round(share, 2))
            score = share * 0.8
        if archetype and archetype in (p.get("archetypes") or []):
            score += 0.1
        if tone and tone in (p.get("tone") or []):
            score += 0.05
        if (p.get("animation") or "").startswith("animated"):
            score -= 0.15          # static on buttons (design rule)
        row["score"] = round(score, 3)
        ranked.append(row)
    ranked.sort(key=lambda r: -r["score"])
    return ranked


def cmd_suggest(a) -> int:
    vocab = load_vocabulary(a.vocabulary)
    if a.needs:
        needed = [s.strip() for s in a.needs.split(",") if s.strip()]
    elif a.source:
        with open(a.source, encoding="utf-8") as fh:
            raw = fh.read()
        try:
            needed = needed_slots(json.loads(raw), vocab)
        except ValueError:
            needed = needed_slots(raw, vocab)
    else:
        print("pass --needs slot,slot or --from FILE", file=sys.stderr)
        return 2
    packs = _load(a.packs or PACKS)["packs"]
    sets = load_sets(a.sticker_set, None)
    ranked = rank_packs(needed, vocab, packs, sets=sets, archetype=a.archetype, tone=a.tone)
    _emit({"needed_slots": needed, "ranking": ranked[: a.top]}, a.out)
    print(f"\n{len(needed)} slot(s) needed. Pick ONE family; fill gaps only from its siblings. "
          f"Look at the top candidate in a chat (light + dark) before resolving.", file=sys.stderr)
    return 0


# ---- verify -----------------------------------------------------------------

class _SavedResponse:
    """Offline stand-in for getCustomEmojiStickers backed by a saved result."""

    def __init__(self, stickers):
        self.by_id = {s["custom_emoji_id"]: s for s in stickers}
        self.calls = 0

    def call(self, method, params):
        assert method == "getCustomEmojiStickers" and len(params["custom_emoji_ids"]) <= 200
        self.calls += 1
        return [self.by_id[i] for i in params["custom_emoji_ids"] if i in self.by_id]


def verify_map(icon_map: dict, transport) -> dict:
    icons = icon_map.get("icons", {})
    found, missing = verify_ids(transport, [i.get("id") for i in icons.values()])
    changed = []
    for slot, icon in icons.items():
        s = found.get(str(icon.get("id")))
        if not s:
            continue
        if icon.get("set") and s.get("set_name") and s["set_name"] != icon["set"]:
            changed.append(f"{slot}: set {icon['set']} -> {s['set_name']}")
        if s.get("emoji") and icon.get("fallback") and emoji_key(s["emoji"]) != emoji_key(icon["fallback"]):
            changed.append(f"{slot}: fallback {icon['fallback']} but sticker emoji is {s['emoji']}")
        anim = bool(s.get("is_animated") or s.get("is_video"))
        if "animated" in icon and bool(icon["animated"]) != anim:
            changed.append(f"{slot}: animated recorded {icon['animated']} but sticker is {anim}")
    removed = [s for s, i in icons.items() if str(i.get("id")) in missing]
    return {"checked": len(icons), "removed_slots": removed, "changed": changed, "ok": not removed and not changed}


def cmd_verify(a) -> int:
    icon_map = _load(a.map)
    t = _SavedResponse(_result(_load(a.response))) if a.response else _live()
    rep = verify_map(icon_map, t)
    _emit(rep, a.out)
    if rep["removed_slots"]:
        print(f"\nremoved emoji: {', '.join(rep['removed_slots'])} - unset these slots (they degrade to the "
              f"fallback) and re-resolve from the same family", file=sys.stderr)
    return 0 if rep["ok"] else 1


# ---- capture ----------------------------------------------------------------

CAPTURE_STEPS = """Collect custom_emoji_id values from the owner (no ids are guessed):
1. The owner (a Premium user) opens a private chat with the bot and sends ONE message that
   contains the emoji to use, in slot order, e.g. "home ⌂ settings ⚙ done ✅" with each
   emoji picked from the chosen pack.
2. The bot logs message.entities of type "custom_emoji" (handler below) and replies with
   nothing sensitive - only the ids it saw.
3. Save the update JSON and run:  py -3 scripts/emoji_packs.py capture --update saved.json
4. Confirm the ids with getCustomEmojiStickers (verify) and record set_name + emoji.
Alternative without the owner's help: resolve the whole pack with getStickerSet(name)."""

CAPTURE_SNIPPET = '''def log_custom_emoji(update: dict) -> list[dict]:
    """Return [{"id", "emoji", "offset"}] for every custom emoji in an incoming message."""
    msg = update.get("message") or {}
    text = msg.get("text") or msg.get("caption") or ""
    units = text.encode("utf-16-le")
    out = []
    for e in msg.get("entities") or msg.get("caption_entities") or []:
        if e["type"] == "custom_emoji":
            emoji = units[2 * e["offset"]: 2 * (e["offset"] + e["length"])].decode("utf-16-le")
            out.append({"id": e["custom_emoji_id"], "emoji": emoji, "offset": e["offset"]})
    return out'''


def captured(update: dict, vocab) -> list[dict]:
    return ids_from_message(update, vocab)


def cmd_capture(a) -> int:
    if not a.update:
        print(CAPTURE_STEPS + "\n\n" + CAPTURE_SNIPPET)
        return 0
    rows = captured(_load(a.update), load_vocabulary(a.vocabulary))
    _emit({"captured": rows, "next": "verify these ids with getCustomEmojiStickers before use"}, a.out)
    return 0 if rows else 1


# ---- apply / strip ----------------------------------------------------------

def _requests(doc, method: str | None):
    """A payload file {"steps": [...]}, a list of steps, or one params object (--method)."""
    if isinstance(doc, dict) and "steps" in doc:
        return doc, doc["steps"]
    if isinstance(doc, list):
        return doc, doc
    return None, [{"method": method or "sendMessage", "params": doc}]


def cmd_apply(a, strip: bool = False) -> int:
    icon_map = _load(a.map)
    vocab = load_vocabulary(a.vocabulary)
    emap = EmojiMap(icon_map["icons"], vocab)
    if a.text_format:
        with open(a.source, encoding="utf-8") as fh:
            text = fh.read()
        params = {"text": text}
        if a.text_format in ("html", "markdownv2"):
            params["parse_mode"] = {"html": "HTML", "markdownv2": "MarkdownV2"}[a.text_format]
        if a.text_format == "rich-markdown":
            params = {"rich_message": {"markdown": text}}
        out = strip_request(params, emap) if strip else apply_request("sendMessage", params, emap)[0]
        sys.stdout.write((out.get("text") if "text" in out else out["rich_message"]["markdown"])
                         if a.text_format != "entities" else json.dumps(out, ensure_ascii=False, indent=2) + "\n")
        return 0
    doc = _load(a.source)
    container, steps = _requests(doc, a.method)
    ic = IconSystem(icon_map["icons"], vocabulary=vocab,
                    eligibility=Eligibility(fragment_usernames=a.fragment, owner_premium=a.owner_premium)
                    if (a.fragment or a.owner_premium or a.context) else None)
    ctx = SendContext(a.context or "private", business=a.business, inline=a.inline)
    view = ic.for_context(ctx)
    total = Counter()
    for step in steps:
        if strip:
            step["params"] = strip_request(step["params"], emap)
            continue
        if view.active:
            step["params"], rep = apply_request(step["method"], step["params"], emap)
            total["replaced"] += rep["replaced"]
            for w in rep["warnings"]:
                print(f"WARN {step['method']}: {w}", file=sys.stderr)
            if rep["unmapped"]:
                print(f"note {step['method']}: unmapped emoji {' '.join(sorted(set(rep['unmapped'])))}", file=sys.stderr)
        else:
            step["params"] = strip_request(step["params"], emap)
    _emit(container if container is not None else steps[0]["params"], a.out)
    if not strip:
        state = "custom emoji ON" if view.active else f"custom emoji OFF ({ic.eligibility.explain(ctx) if ic.eligibility else 'disabled'})"
        print(f"\n{state}; {total['replaced']} emoji replaced", file=sys.stderr)
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p):
        p.add_argument("--vocabulary", help="slot vocabulary (default data/emoji/slots.json)")
        p.add_argument("--out")
        return p

    r = common(sub.add_parser("resolve", help="pack(s) -> slot map with real ids"))
    r.add_argument("--sticker-set", action="append", help="saved getStickerSet JSON (repeatable; primary first)")
    r.add_argument("--set", action="append", help="set name to fetch live (repeatable)")
    r.add_argument("--slots", help="comma-separated slots (default: whole vocabulary)")
    r.add_argument("--slots-file", help="JSON list/dict of slots")
    r.add_argument("--family")

    s = common(sub.add_parser("suggest", help="rank packs for the slots a project needs"))
    s.add_argument("--needs", help="comma-separated slots")
    s.add_argument("--from", dest="source", help="texts/keyboards/payload JSON or plain text")
    s.add_argument("--sticker-set", action="append", help="saved getStickerSet JSON for real coverage")
    s.add_argument("--packs", help="pack registry (default data/emoji/packs.json)")
    s.add_argument("--archetype", help="monitoring|ai|shop|team|support|content|wallet|games")
    s.add_argument("--tone", help="neutral|native|playful|editorial|…")
    s.add_argument("--top", type=int, default=5)

    v = common(sub.add_parser("verify", help="re-check a stored map with getCustomEmojiStickers"))
    v.add_argument("--map", required=True)
    v.add_argument("--response", help="saved getCustomEmojiStickers result (offline)")

    c = common(sub.add_parser("capture", help="steps + snippet to collect ids from custom_emoji entities"))
    c.add_argument("--update", help="saved update/message JSON to extract ids from")

    for name in ("apply", "strip"):
        p = common(sub.add_parser(name, help="rewrite requests to use (apply) or drop (strip) custom emoji"))
        p.add_argument("--map", required=True)
        p.add_argument("--in", dest="source", required=True)
        p.add_argument("--method", help="method name when --in holds one params object")
        p.add_argument("--text-format", choices=["html", "markdownv2", "rich-markdown", "entities"],
                       help="--in is a raw text file in this format")
        p.add_argument("--context", choices=["private", "group", "supergroup", "channel"])
        p.add_argument("--business", action="store_true")
        p.add_argument("--inline", action="store_true")
        p.add_argument("--fragment", action="store_true", help="bot has Fragment usernames")
        p.add_argument("--owner-premium", action="store_true", help="bot owner has Telegram Premium")
    a = ap.parse_args(argv)
    return {"resolve": cmd_resolve, "suggest": cmd_suggest, "verify": cmd_verify, "capture": cmd_capture,
            "apply": cmd_apply, "strip": lambda x: cmd_apply(x, strip=True)}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
