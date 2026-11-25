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
  py -3 scripts/emoji_packs.py library pick --needs home,back,settings --profile style-profile.json
  py -3 scripts/emoji_packs.py library pick --profile style-profile.json --library-file emoji-library.ndjson.gz

Data: data/emoji/slots.json (slot vocabulary), data/emoji/packs.json (verified public sets,
metadata only), data/emoji/library-contract.json (the emoji library's schemas and taxonomy,
checked on every answer by emoji_contract.py). Reference: references/emoji-packs.md.
"""
from __future__ import annotations

import argparse
import io
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


# ---- library (the telegram-bot-ui emoji library: search and pick one family) -------------

EXPORT_MAX = 64 * 1024 * 1024     # the unpacked export; the real one is a few MB
FACETS_MAX = 16 * 1024 * 1024     # /api/emoji-facets carries every pack (about 1 MB today)


class LibraryClient:
    """The telegram-bot-ui emoji library through its contract (data/emoji/library-contract.json).

    Online (default): GET /api/emoji-search, /api/emoji-pack/{name} and /api/emoji-facets through the bot-ui
    resolver's origin (only search words and pack names are sent). Every answer is checked against the
    vendored schema and its `taxonomy` version before any field is read; an error answer raises its own code.
    `fetch(path) -> (status, body bytes)` replaces the network (tests).
    Offline export (`export=`): the catalog file /emoji-library.ndjson.gz, every line checked as a CatalogLine.
    It has the tags, look and descriptions of every pack but no fallback emoji and no search.
    Saved (`saved=`): canned {"search": {query: answer}, "packs": {name: answer}, "facets": answer}, unchecked."""

    def __init__(self, saved: dict | None = None, *, fetch=None, export: str | None = None):
        self.saved, self.calls, self._fetch, self._export = saved, 0, fetch, None
        self._pack_path = "/api/emoji-pack"
        if export:
            self._export = read_export(export)
        elif saved is None and fetch is None:
            from bot_ui.emoji import _Resolver, resolver_url
            base = resolver_url()
            if base is None:
                raise SystemExit("the emoji library is switched off (BOT_UI_EMOJI_RESOLVER=off); "
                                 "pass --library-file emoji-library.ndjson.gz")
            resolver = _Resolver(base)
            self._pack_path = base[len(resolver.origin):] or self._pack_path
            self._fetch = lambda path: resolver._get(resolver.origin + path, FACETS_MAX)[::2]

    @property
    def offline(self) -> bool:
        return self._export is not None

    def _answer(self, path: str, schema: str, limit: int = 2 * 1024 * 1024, missing_ok: bool = False) -> dict | None:
        from bot_ui.emoji import EmojiError
        from emoji_contract import check_answer
        self.calls += 1
        status, body = self._fetch(path)
        what = f"GET {path.split('?')[0]}"
        if len(body) > limit:
            raise EmojiError("RESOLVER_ERROR", f"{what}: the answer is larger than {limit} bytes")
        try:
            doc = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            if missing_ok and status == 404:
                return None
            raise EmojiError("RESOLVER_ERROR", f"{what} answered HTTP {status} without JSON") from None
        if status != 200 or not isinstance(doc, dict) or doc.get("ok") is not True:
            err = (doc.get("error") if isinstance(doc, dict) else None) or {}
            if missing_ok and status == 404 and not err:
                return None
            raise EmojiError(str(err.get("code") or "RESOLVER_ERROR"), f"{what}: {err.get('message') or f'HTTP {status}'}")
        return check_answer(doc, schema, what)

    def search(self, query: str, pack: str | None = None) -> dict:
        if self.saved is not None:
            self.calls += 1
            key = f"{query}|{pack}" if pack else query
            return (self.saved.get("search") or {}).get(key) or {"emoji": [], "packs": []}
        if self.offline:
            from bot_ui.emoji import EmojiError
            raise EmojiError("OFFLINE_NO_SEARCH", "the offline export has no search index and no fallback emoji: search "
                                                  "online, or rank packs by tags (library facets / pick --profile)")
        params = {"q": query[:160], **({"pack": pack} if pack else {})}
        if pack:
            _pack_name(pack)
        from urllib.parse import urlencode
        return self._answer(f"/api/emoji-search?{urlencode(params)}", "SearchResponse")

    def pack(self, name: str) -> dict:
        if self.saved is not None:
            self.calls += 1
            return (self.saved.get("packs") or {}).get(name) or {"emoji": []}
        _pack_name(name)
        if self.offline:
            line = self._export["lines"].get(name)
            return dict(line, emoji=[{"id": e["id"]} for e in line["emoji"]]) if line else {"emoji": []}
        return self._answer(f"{self._pack_path}/{name}", "PackResponse")

    def facets(self) -> dict | None:
        """The tag taxonomy and every pack's tags, look and description (GET /api/emoji-facets, or the same built
        from the offline export), or None when the library has no tags yet (an older deployment answers 404):
        picking then works from coverage alone."""
        if self.saved is not None:
            doc = self.saved.get("facets")
            return doc if isinstance(doc, dict) and isinstance(doc.get("packs"), list) else None
        if self.offline:
            return self._export["catalog"]
        return self._answer("/api/emoji-facets", "FacetsResponse", limit=FACETS_MAX, missing_ok=True)


def _pack_name(name: str) -> str:
    from bot_ui.emoji import PACK_NAME, EmojiError
    if not isinstance(name, str) or not PACK_NAME.match(name):
        raise EmojiError("PACK_NAME", f"not a pack name: {name!r}")
    return name


def read_export(path: str) -> dict:
    """The offline catalog export (gzip or plain NDJSON, one CatalogLine per pack), checked line by line, as
    {"lines": {name: line}, "catalog": the /api/emoji-facets answer it stands for}. The taxonomy labels and
    the pack threshold come from the vendored contract when the export uses its taxonomy version."""
    import gzip
    from bot_ui.emoji import EmojiError
    from emoji_contract import check_answer, check_taxonomy, load_contract
    try:
        with open(path, "rb") as fh:
            raw = fh.read(EXPORT_MAX + 1)
        if raw[:2] == b"\x1f\x8b":
            with gzip.GzipFile(fileobj=io.BytesIO(raw)) as gz:
                raw = gz.read(EXPORT_MAX + 1)
        text = raw.decode("utf-8")
    except (OSError, EOFError, UnicodeDecodeError) as err:
        raise EmojiError("EXPORT_INVALID", f"{path}: not a readable UTF-8 NDJSON or .gz file ({err})") from None
    if len(raw) > EXPORT_MAX:
        raise EmojiError("EXPORT_INVALID", f"{path}: larger than {EXPORT_MAX} bytes unpacked")
    lines: dict[str, dict] = {}
    versions = set()
    for n, row in enumerate(text.splitlines(), 1):
        if not row.strip():
            continue
        try:
            line = json.loads(row)
        except ValueError as err:
            raise EmojiError("EXPORT_INVALID", f"{path} line {n}: not JSON ({err})") from None
        check_answer(line, "CatalogLine", f"{os.path.basename(path)} line {n}")
        versions.add((line["taxonomy"], line["generated"]))
        lines[line["name"]] = line
    if not lines:
        raise EmojiError("EXPORT_INVALID", f"{path}: no packs")
    if len(versions) > 1:
        raise EmojiError("EXPORT_INVALID", f"{path}: lines from different catalog builds {sorted(versions)}")
    (version, generated), = versions
    check_taxonomy(version, path)
    contract = load_contract()
    tax = contract["taxonomy"]
    facets = tax["facets"] if tax["version"] == version else {}
    keys = ("name", "category", "count", "meanings", "facets", "compatible", "look", "description")
    packs = [{k: line[k] for k in keys if k in line} for line in lines.values()]
    return {"lines": lines, "catalog": {"ok": True, "generated": generated, "taxonomy": {"version": version, "facets": facets},
                                        "thresholds": contract["thresholds"], "packs": packs, "source": "export"}}


# ------------------------------------------------------------------ facets: context -> pack
# How much each facet counts when a pack is matched to a bot's context (normalised over the facets given).
FACET_WEIGHT = {"style": 0.28, "topic": 0.2, "use": 0.14, "fit": 0.12, "color": 0.1, "mood": 0.1, "palette": 0.04,
                "motion": 0.02}
ARCHETYPE_USE = {"shop": "shop", "monitoring": "utility", "ai": "utility", "team": "community", "support": "support",
                 "content": "content", "wallet": "finance", "games": "games"}
TRAIT_MOOD = {"calm": "calm", "plain": "calm", "quiet": "calm", "precise": "serious", "serious": "serious",
              "formal": "serious", "playful": "playful", "fun": "playful", "friendly": "joyful", "joyful": "joyful",
              "warm": "loving", "caring": "loving"}
# The profile's brand.icon_style in the library's style vocabulary ("mixed" asks for nothing).
ICON_STYLE = {"outline": "outline", "solid": "glyph", "flat": "flat", "duotone": "flat"}
HUE_FAMILIES = ((15, "red"), (40, "orange"), (52, "gold"), (70, "yellow"), (160, "green"), (195, "teal"), (255, "blue"),
                (290, "purple"), (345, "pink"), (361, "red"))


def accent_family(hex_colour: str) -> str | None:
    """Colour family of a brand accent (#RRGGBB), in the library's colour vocabulary."""
    import colorsys
    h = hex_colour.strip().lstrip("#")
    if len(h) != 6 or any(c not in "0123456789abcdefABCDEF" for c in h):
        return None
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    hue, sat, val = colorsys.rgb_to_hsv(r, g, b)
    if val < 0.16:
        return "black"
    if sat < 0.12:
        return "white" if val > 0.85 else "gray"
    deg = hue * 360
    return next(name for limit, name in HUE_FAMILIES if deg < limit)


def brief_from_profile(profile: dict) -> dict[str, list[str]]:
    """The facets a bot's style profile asks of an emoji pack: icon style, accent colour family, mood from the
    brand traits, the interface role of its icons and the bot category. Only what the profile states."""
    brand, bot = profile.get("brand") or {}, profile.get("bot") or {}
    brief: dict[str, list[str]] = {"topic": ["interface"]}
    style = brand.get("icon_style")
    if isinstance(style, str) and style and style.lower() != "mixed":
        brief["style"] = [ICON_STYLE.get(style.lower(), style.lower())]
    if isinstance(brand.get("accent"), str) and accent_family(brand["accent"]):
        brief["color"] = [accent_family(brand["accent"])]
    moods = [TRAIT_MOOD[t.lower()] for t in brand.get("traits") or [] if isinstance(t, str) and t.lower() in TRAIT_MOOD]
    if moods:
        brief["mood"] = list(dict.fromkeys(moods))
    if ARCHETYPE_USE.get(bot.get("archetype")):
        brief["use"] = [ARCHETYPE_USE[bot["archetype"]]]
    return brief


# The slot vocabulary's groups (data/emoji/slots.json) as the library's interface roles.
GROUP_ROLE = {"navigation": "navigation", "actions": "action", "status": "status", "warnings": "status",
              "time": "status", "commerce": "commerce", "finance": "commerce", "communication": "communication",
              "people": "communication", "ai": "communication", "settings": "settings", "files": "settings",
              "analytics": "settings", "media": "content", "post": "content"}


def slots_brief(slots: list[str], vocab: dict) -> dict[str, list[str]]:
    """The facets a set of icon slots asks of a pack when only the catalog is at hand (it has no fallback emoji to
    match): interface icons, in the roles of the slots' groups, the most frequent role first."""
    roles = Counter(GROUP_ROLE[g] for s in slots if (g := (vocab.get(s) or {}).get("group")) in GROUP_ROLE)
    brief: dict[str, list[str]] = {"topic": ["interface"]}
    if roles:
        brief["role"] = [r for r, _ in sorted(roles.items(), key=lambda kv: (-kv[1], kv[0]))]
    return brief


def normalize_brief(brief: dict, doc: dict | None) -> tuple[dict[str, list[str]], list[str]]:
    """Brief values as taxonomy ids (an id, or its English or Russian label); (brief, problems). Without a
    taxonomy the values are kept as given."""
    tax = ((doc or {}).get("taxonomy") or {}).get("facets") or {}
    out: dict[str, list[str]] = {}
    problems: list[str] = []
    for facet, values in brief.items():
        vals = [values] if isinstance(values, str) else list(values or [])
        if not vals:
            continue
        if tax and facet not in tax:
            problems.append(f"unknown facet {facet!r} (known: {', '.join(tax)})")
            continue
        known = (tax.get(facet) or {}).get("values") or {}
        ids = []
        for v in vals:
            low = str(v).lower()
            hit = next((k for k, d in known.items() if low in (k, str(d.get("en", "")).lower(), str(d.get("ru", "")).lower())), None)
            if tax and hit is None:
                problems.append(f"{facet}:{v} is not in the taxonomy (known: {', '.join(known)})")
            else:
                ids.append(hit or low)
        if ids:
            out[facet] = ids
    return out, problems


def facet_match(tags: dict, brief: dict[str, list[str]], threshold: float) -> tuple[float, list[list]]:
    """0..1: how well one pack's tags fit the brief, and the tags that matched [facet, value, confidence].
    A facet counts by the best confidence of a wanted value; tags below the library's pack threshold count for
    nothing; facets the brief does not name are ignored; an adaptive theme fit also serves light and dark."""
    got, total, hits = 0.0, 0.0, []
    for facet, wanted in brief.items():
        weight = FACET_WEIGHT.get(facet, 0.05)
        total += weight
        best, hit = 0.0, None
        for value, conf in tags.get(facet) or []:
            if conf < threshold or conf <= best:
                continue
            if value in wanted or (facet == "fit" and value in ("adaptive", "both") and set(wanted) & {"light", "dark", "both"}):
                best, hit = conf, [facet, value, round(conf, 2)]
        if hit:
            got += weight * best
            hits.append(hit)
    return (got / total if total else 0.0), hits


def rank_by_facets(doc: dict, brief: dict, *, require: list[str] | None = None, motion: str | None = None,
                   theme: str | None = None, top: int = 10, lang: str = "en") -> dict:
    """Packs of the library ordered by how well their tags fit a brief (no slot coverage involved).
    `require` are hard filters ("facet:value": the pack must carry the tag at or above the library's pack
    threshold). Each row also names the pack's tag-compatible companions."""
    th = (doc.get("thresholds") or {}).get("pack", 0.3)
    wanted, problems = normalize_brief(brief, doc)
    must: list[tuple[str, str]] = []
    for r in require or []:
        facet, _, v = r.partition(":")
        norm, p = normalize_brief({facet: [v]}, doc)
        if norm.get(facet):
            must.append((facet, norm[facet][0]))
        else:
            problems.extend(p or [f"bad filter {r!r}"])
            must.append((facet, ""))      # a filter that names nothing real matches no pack, never every pack
    rows = []
    for pk in doc.get("packs") or []:
        tags = pk.get("facets") or {}
        if any(not any(v == val and c >= th for val, c in tags.get(f) or []) for f, v in must):
            continue
        score, hits = facet_match(tags, wanted, th)
        # Preferences, not filters: Telegram's own icon packs are animated, and dropping them would hide
        # the best toolbar sets. Use require=["motion:static"] when it must be static.
        moving = max((c for v, c in tags.get("motion") or [] if v in ("animated", "video")), default=0)
        if motion == "static" and moving >= th:
            score -= 0.1 * moving
        fit = dict((v, c) for v, c in tags.get("fit") or [])
        if theme == "both":
            score += 0.1 * max(fit.get("adaptive", 0), fit.get("both", 0))
        elif theme in ("light", "dark"):
            score += 0.1 * max(fit.get("adaptive", 0), fit.get("both", 0), fit.get(theme, 0))
        row = {"name": pk["name"], "category": pk.get("category"), "score": round(score, 3), "matched": hits,
               "compatible": [c[0] for c in (pk.get("compatible") or [])[:4]]}
        desc = pack_description(pk, lang)
        if desc:
            row["description"] = desc
        row["why"] = explain_pack(pk, th, wanted, hits, catalog_coverage(pk, th), lang=lang)
        rows.append(row)
    rows.sort(key=lambda r: (-r["score"], r["name"]))
    tax = doc.get("taxonomy")
    return {"brief": wanted, "require": [f"{f}:{v}" for f, v in must], "problems": problems,
            "taxonomy": tax.get("version") if isinstance(tax, dict) else tax, "total": len(rows), "packs": rows[:top]}


# ------------------------------------------------------------------ explaining a choice
NEUTRAL = {"white", "gray", "black"}
HUE_RING = ("red", "orange", "gold", "yellow", "green", "teal", "blue", "purple", "pink")
WARM = {"red", "orange", "gold"}           # brown sits next to these
LANGS = ("en", "ru", "uk")


def pack_description(pk: dict, lang: str = "en") -> dict | None:
    """The pack's {what, for, not_for} in `lang` (English when that language is missing), or None."""
    desc = pk.get("description")
    if not isinstance(desc, dict):
        return None
    text = desc.get(lang) or desc.get("en")
    return text if isinstance(text, dict) else None


def _tags(pk: dict, facet: str, th: float) -> list[list]:
    return [[v, c] for v, c in (pk.get("facets") or {}).get(facet) or [] if c >= th]


def catalog_coverage(pk: dict, th: float) -> str:
    """What a pack covers, from the catalog alone (it has no fallback emoji): size, meanings, interface roles."""
    roles = [v for v, _ in _tags(pk, "role", th)[:3]]
    text = f"{pk.get('count', '?')} emoji, {pk.get('meanings', '?')} meanings"
    return text + (f", roles {'/'.join(roles)}" if roles else "")


def _facet_text(pk: dict, facet: str, th: float, wanted: dict, matched: list) -> str:
    label = "colour" if facet == "color" else facet
    hit = next((m for m in matched if m[0] == facet), None)
    if hit:
        return f"{label} {hit[1]} {hit[2]:.2f} as asked"
    tags = _tags(pk, facet, th)
    have = f"{tags[0][0]} {tags[0][1]:.2f}" if tags else "untagged"
    return f"{label} {have}" + (f" (asked {'/'.join(wanted[facet])})" if wanted.get(facet) else "")


def explain_pack(pk: dict, th: float, wanted: dict, matched: list, coverage: str, colour: dict | None = None,
                 lang: str = "en") -> str:
    """One line on why a pack ranks where it does: coverage, style, topic, colour, and what it is for."""
    parts = [coverage, _facet_text(pk, "style", th, wanted, matched), _facet_text(pk, "topic", th, wanted, matched),
             f"colour {colour['why']}" if colour else _facet_text(pk, "color", th, wanted, matched)]
    desc = pack_description(pk, lang)
    line = f"{pk['name']}: " + "; ".join(parts)
    return line + (f". For: {desc['for']}" if desc and desc.get("for") else "")


def accent_palette(hex_colour: str) -> str | None:
    """monochrome, muted or vivid: the library palette a brand accent belongs to."""
    import colorsys
    h = hex_colour.strip().lstrip("#")
    if len(h) != 6 or any(c not in "0123456789abcdefABCDEF" for c in h):
        return None
    _, sat, val = colorsys.rgb_to_hsv(*(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)))
    if sat < 0.12:
        return "monochrome"
    return "vivid" if sat >= 0.5 and val >= 0.55 else "muted"


def _closeness(accent: str, colour: str) -> float:
    """1 the same family, 0.5 a neighbour on the colour wheel, 0.3 a neutral pack colour (it goes with any accent)."""
    if accent == colour:
        return 1.0
    if colour in NEUTRAL:
        return 0.3
    if accent in NEUTRAL:
        return 0.2
    if "brown" in (accent, colour):
        return 0.5 if {accent, colour} - {"brown"} <= WARM else 0.0
    if accent not in HUE_RING or colour not in HUE_RING:
        return 0.0
    i, j = HUE_RING.index(accent), HUE_RING.index(colour)
    return 0.5 if min(abs(i - j), len(HUE_RING) - abs(i - j)) == 1 else 0.0


def colour_fit(pk: dict, accent: str, th: float) -> dict:
    """How a pack's measured colours and palette sit with a brand accent: score 0..1 and the reason.
    An adaptive pack is drawn in the text colour, so it never clashes with the accent (score at least 0.6)."""
    family, palette = accent_family(accent), accent_palette(accent)
    colours = _tags(pk, "color", th)
    best = max(colours, key=lambda vc: (vc[1] * _closeness(family, vc[0]), vc[1]), default=None)
    hue = best[1] * _closeness(family, best[0]) if best else 0.0
    pal = dict((v, c) for v, c in _tags(pk, "palette", th)).get(palette, 0.0)
    adaptive = any(v == "adaptive" for v, _ in _tags(pk, "fit", th))
    score = 0.75 * hue + 0.25 * pal
    if best:
        near = "~" if best[0] == family else "near" if hue and best[0] not in NEUTRAL else "neutral with" if hue else "far from"
        why = f"{best[0]} {best[1]:.2f} {near} accent {accent} ({family})"
    else:
        why = f"untagged, accent {accent} ({family})"
    if pal:
        why += f", palette {palette} {pal:.2f}"
    if adaptive:
        score = max(score, 0.6)
        why += "; adaptive: drawn in the text colour, so it sits with any accent"
    return {"accent": accent, "family": family, "palette": palette, "best": best, "adaptive": adaptive,
            "score": round(score, 3), "why": why}


def profile_lang(profile: dict) -> str:
    """The language of the pack descriptions for a bot: its primary locale when the library has it."""
    lang = str(((profile or {}).get("bot") or {}).get("primary_locale") or "en").split("-")[0].lower()
    return lang if lang in LANGS else "en"


def profile_request(profile: dict | None, flags: dict | None = None) -> tuple[dict[str, list[str]], list[str]]:
    """(brief, brand accents) from a style profile, overridden flag by flag. The accent is compared with each
    pack's colours and palette (colour_fit) instead of being matched as a colour tag; an explicit colour or
    palette flag replaces that comparison."""
    brief = brief_from_profile(profile) if profile else {}
    brief.pop("color", None)
    brief.update({k: v for k, v in (flags or {}).items() if v})
    accent = ((profile or {}).get("brand") or {}).get("accent")
    if "color" in brief or "palette" in brief or not isinstance(accent, str) or not accent_family(accent):
        return brief, []
    return brief, ["#" + accent.strip().lstrip("#").upper()]


def pick_by_profile(doc: dict, brief: dict, accents: list[str], *, require: list[str] | None = None,
                    motion: str = "static", theme: str = "both", top: int = 10, lang: str = "en") -> dict:
    """Packs ranked for a bot from the catalog alone (the /api/emoji-facets answer or the offline export: both
    give the same result): the brief's tags (style, topic, mood, bot category, theme fit), the brand accent
    against each pack's measured colours and palette, and a little for breadth (meanings). Each row says why."""
    th = (doc.get("thresholds") or {}).get("pack", 0.3)
    ask = dict(brief)
    ask.setdefault("fit", [theme])
    ranked = rank_by_facets(doc, ask, require=require, motion="static" if motion == "static" else None,
                            top=len(doc.get("packs") or []), lang=lang)
    by_name = {p["name"]: p for p in doc.get("packs") or []}
    rows = []
    for r in ranked["packs"]:
        pk = by_name[r["name"]]
        colour = colour_fit(pk, accents[0], th) if accents else None
        breadth = min(1.0, (pk.get("meanings") or 0) / 60)
        score = r["score"] + (0.15 * colour["score"] if colour else 0.0) + 0.05 * breadth
        row = {**r, "score": round(score, 3), "coverage": {"emoji": pk.get("count"), "meanings": pk.get("meanings"),
                                                          "roles": [v for v, _ in _tags(pk, "role", th)]}}
        if colour:
            row["colour"] = colour
        row["why"] = explain_pack(pk, th, ranked["brief"], r["matched"], catalog_coverage(pk, th), colour, lang)
        rows.append(row)
    rows.sort(key=lambda r: (-r["score"], r["name"]))
    return {"brief": ranked["brief"], "accents": accents, "require": ranked["require"], "problems": ranked["problems"],
            "taxonomy": ranked["taxonomy"], "generated": doc.get("generated"), "total": len(rows), "packs": rows[:top]}

def _slot_keys(vocab: dict, slot: str) -> set[str]:
    return {emoji_key(u) for u in (vocab.get(slot) or {}).get("unicode") or []}


def pick_family(needed: list[str], vocab: dict, client: LibraryClient, *, candidates: int = 6,
                motion: str = "static", theme: str = "both", brief: dict | None = None,
                require: list[str] | None = None, facets: dict | None = None, lang: str = "en") -> dict:
    """Rank whole packs for the slots a bot needs and build the icon map from the best one.

    1. Discovery: search the library for each slot's first unicode emoji; a hit whose fallback is
       one of the slot's emoji votes for its pack. With a brief, packs whose tags fit it (style, colour,
       mood, topic, bot category: the library's faceted tags, weighted by their confidence) join the
       candidates even when the search did not vote for them; `require` ("facet:value") drops packs
       without that tag.
    2. Coverage: fetch each top candidate pack and match every slot by fallback emoji.
    3. Score = coverage, then fit to the brief, then theme safety (adaptive share when both themes
       matter), then motion (static preferred on buttons), then one format across the pack.
    A library without tags ignores the brief; the answer's `notes` say so. Every ranked pack carries its
    description (what it is, what it suits and does not) and `why`, one line on coverage, style, topic, colour.
    """
    unknown = [x for x in needed if x not in vocab]
    slots = [x for x in needed if x in vocab]
    votes: Counter = Counter()
    for slot in slots:
        keys = _slot_keys(vocab, slot)
        query = (vocab[slot].get("unicode") or [vocab[slot].get("label", slot)])[0]
        seen = set()
        for hit in client.search(query).get("emoji") or []:
            if emoji_key(hit.get("fallback") or "") in keys and hit.get("pack") not in seen:
                votes[hit["pack"]] += 1
                seen.add(hit["pack"])
    fit: dict[str, tuple[float, list]] = {}
    wanted: dict[str, list[str]] = {}
    notes: list[str] = []
    catalog: dict[str, dict] = {}
    th = 0.3
    if brief or require:
        doc = facets if facets is not None else client.facets()
        if doc is not None:
            catalog = {p["name"]: p for p in doc.get("packs") or [] if isinstance(p, dict) and "name" in p}
            th = (doc.get("thresholds") or {}).get("pack", th)
        if doc is None:
            notes.append("the library has no tags yet: ranked by coverage only")
        else:
            ask = dict(brief or {})
            if ask and "fit" not in ask:
                ask["fit"] = [theme]          # the theme the bot must look right in is part of the brief
            ranked = rank_by_facets(doc, ask, require=require, top=len(doc.get("packs") or []))
            wanted, notes = ranked["brief"], list(ranked["problems"])
            fit = {r["name"]: (r["score"], r["matched"]) for r in ranked["packs"]}
            if require:
                votes = Counter({n: v for n, v in votes.items() if n in fit})
                if not fit:
                    notes.append("no pack carries every required tag")
    pool = dict(votes)
    for name, (score, _) in sorted(fit.items(), key=lambda kv: (-kv[1][0], kv[0]))[:candidates]:
        if score > 0:
            pool.setdefault(name, 0)
    order = sorted(pool, key=lambda n: (-(pool[n] / max(1, len(slots)) + 0.5 * fit.get(n, (0.0, []))[0]), n))
    ranking = []
    for name in order[:candidates]:
        vote = pool[name]
        doc = client.pack(name)
        emoji = [e for e in doc.get("emoji") or [] if isinstance(e, dict) and str(e.get("id", "")).isdigit()]
        by_key: dict[str, dict] = {}
        for e in emoji:
            by_key.setdefault(emoji_key(e.get("fallback") or ""), e)
        icons, missing = {}, []
        for slot in slots:
            hit = next((by_key[emoji_key(k)] for k in vocab[slot].get("unicode") or [] if emoji_key(k) in by_key), None)
            if hit is None:
                missing.append(slot)
                continue
            icons[slot] = {"id": str(hit["id"]), "set": name, "fallback": hit.get("fallback"),
                           "animated": hit.get("format") != "static", "adaptive": bool(hit.get("adaptive"))}
        used = list(icons.values())
        coverage = len(icons) / max(1, len(slots))
        adaptive = sum(i["adaptive"] for i in used) / max(1, len(used))
        static = sum(not i["animated"] for i in used) / max(1, len(used))
        formats = Counter(e.get("format") for e in emoji)
        score = coverage
        match, hits = fit.get(name, (0.0, []))
        if wanted:
            score += 0.35 * match
        if theme == "both":
            score += 0.15 * adaptive
        if motion == "static":
            score += 0.1 * static
        if emoji:
            score += 0.05 * formats.most_common(1)[0][1] / len(emoji)
        row = {"name": name, "title": doc.get("title"),
               "link": doc.get("telegramUrl") or f"https://t.me/addemoji/{name}",
               "votes": vote, "coverage": round(coverage, 3), "adaptive_share": round(adaptive, 2),
               "static_share": round(static, 2), "formats": dict(formats), "missing": missing,
               "score": round(score, 3), "icons": icons}
        if wanted:
            row.update(brief_match=round(match, 2), matched=hits)
        pk = catalog.get(name) or {"name": name, "facets": doc.get("facets") or {}, "description": doc.get("description")}
        desc = pack_description(pk, lang)
        if desc:
            row["description"] = desc
        covers = f"covers {len(icons)}/{len(slots)} slots" + (f" (missing {', '.join(missing)})" if missing else "")
        row["why"] = explain_pack({**pk, "name": name}, th, wanted, hits, covers, lang=lang)
        ranking.append(row)
    ranking.sort(key=lambda r: (-r["score"], -r["votes"], r["name"]))
    best = ranking[0] if ranking else None
    out = {"needed_slots": slots, "unknown_slots": unknown, "requests": client.calls,
           "ranking": [{k: v for k, v in r.items() if k != "icons"} for r in ranking],
           "map": {"family": best["name"], "source": "telegram-bot-ui emoji library", "icons": best["icons"],
                   "missing": best["missing"]} if best else None}
    if wanted:
        out["brief"] = wanted
    if notes:
        out["notes"] = notes
    return out


FACET_FLAGS = ("style", "color", "mood", "topic", "use", "palette")


def _flags(a) -> dict[str, list[str]]:
    return {f: [v.strip() for v in getattr(a, f).split(",") if v.strip()] for f in FACET_FLAGS if getattr(a, f, None)}


def _brief_from_args(a) -> dict[str, list[str]]:
    """The profile's brief (--profile), overridden facet by facet by explicit flags (--style outline ...)."""
    brief: dict[str, list[str]] = {}
    if a.profile:
        brief.update(brief_from_profile(_load(a.profile)))
    brief.update(_flags(a))
    return brief


def _needed(a, vocab) -> list[str] | None:
    if a.needs:
        return [x.strip() for x in a.needs.split(",") if x.strip()]
    if a.source:
        with open(a.source, encoding="utf-8") as fh:
            raw = fh.read()
        try:
            return needed_slots(json.loads(raw), vocab)
        except ValueError:
            return needed_slots(raw, vocab)
    return None


def cmd_contract(a) -> int:
    from emoji_contract import CONTRACT, load_contract, vendor
    if a.openapi or a.facets_file:
        if not (a.openapi and a.facets_file):
            print("pass both --openapi (saved /api/emoji-openapi.json) and --facets-file (saved /api/emoji-facets)",
                  file=sys.stderr)
            return 2
        import datetime
        doc = vendor(_load(a.openapi), _load(a.facets_file), datetime.date.today().isoformat())
        with open(a.out or CONTRACT, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
        load_contract(a.out or CONTRACT)          # refuses schema keywords the validator does not check
        print(f"vendored {len(doc['schemas'])} schemas, taxonomy {doc['taxonomy']['version']} -> {a.out or CONTRACT}",
              file=sys.stderr)
        return 0
    doc = load_contract()
    _emit({"source": doc["source"], "sourceCode": doc["sourceCode"], "vendored": doc["vendored"],
           "apiVersion": doc["apiVersion"], "catalog": doc["catalog"], "taxonomy": doc["taxonomy"]["understood"],
           "thresholds": doc["thresholds"], "schemas": sorted(doc["schemas"])}, a.out)
    return 0


def cmd_library(a) -> int:
    from bot_ui.emoji import EmojiError
    try:
        return _library(a)
    except EmojiError as err:
        print(f"error {err.code}: {err.message}", file=sys.stderr)
        return 1


def _library(a) -> int:
    if a.action == "contract":
        return cmd_contract(a)
    vocab = load_vocabulary(a.vocabulary)
    if a.library_json and a.library_file:
        print("pass --library-json or --library-file, not both", file=sys.stderr)
        return 2
    client = LibraryClient(_load(a.library_json) if a.library_json else None, export=a.library_file)
    profile = _load(a.profile) if a.profile else {}
    lang = a.lang or profile_lang(profile)
    brief = _brief_from_args(a)
    if a.action == "facets":
        doc = client.facets()
        if doc is None:
            print("the library has no tags yet (no /api/emoji-facets)", file=sys.stderr)
            return 1
        if not brief and not a.require:
            tax = (doc.get("taxonomy") or {}).get("facets") or {}
            _emit({"taxonomy": doc.get("taxonomy", {}).get("version"), "generated": doc.get("generated"),
                   "thresholds": doc.get("thresholds"), "packs": len(doc.get("packs") or []),
                   "facets": {f: {"label": d.get("label", {}).get("en"), "scope": d.get("scope"),
                                  "values": list((d.get("values") or {}))} for f, d in tax.items()}}, a.out)
            return 0
        res = rank_by_facets(doc, brief, require=a.require, motion="static" if a.motion == "static" else None,
                             theme=a.theme, top=a.top, lang=lang)
        _emit(res, a.out)
        for note in res["problems"]:
            print(note, file=sys.stderr)
        return 0 if res["packs"] else 1
    if a.action == "search":
        if not a.query:
            print("pass the words or emoji to search for", file=sys.stderr)
            return 2
        query = " ".join(a.query)
        ans = client.search(query, a.pack)
        rows = [{"pack": e.get("pack"), "id": e.get("id"), "fallback": e.get("fallback"), "format": e.get("format"),
                 "adaptive": e.get("adaptive")} for e in (ans.get("emoji") or [])[: a.top * 4]]
        _emit({"query": query, "packs": (ans.get("packs") or [])[: a.top], "emoji": rows}, a.out)
        return 0
    needed = _needed(a, vocab)
    if needed is None:
        if not (a.profile or _flags(a) or a.require):
            print("pass --needs slot,slot or --from FILE (an icon map for those slots), or --profile / facet flags "
                  "(packs ranked for the bot)", file=sys.stderr)
            return 2
        doc = client.facets()
        if doc is None:
            print("the library has no tags yet (no /api/emoji-facets): pass --needs to pick by coverage", file=sys.stderr)
            return 1
        brief, accents = profile_request(profile, _flags(a))
        res = pick_by_profile(doc, brief, accents, require=a.require, motion=a.motion, theme=a.theme, top=a.top, lang=lang)
        _emit(res, a.out)
        for row in res["packs"]:
            print(row["why"], file=sys.stderr)
        for note in res["problems"]:
            print(note, file=sys.stderr)
        return 0 if res["packs"] else 1
    if client.offline:
        print("--needs/--from match each pack's fallback emoji, which the offline export does not carry: run online "
              "for the icon map, or drop --needs to rank packs by the profile (pick --profile)", file=sys.stderr)
        return 2
    result = pick_family(needed, vocab, client, candidates=a.candidates, motion=a.motion, theme=a.theme,
                         brief=brief, require=a.require, lang=lang)
    result["ranking"] = result["ranking"][: a.top]
    _emit(result, a.out)
    best = result["map"]
    if not best:
        print("\nno pack in the library matched these slots", file=sys.stderr)
        return 1
    for row in result["ranking"]:
        print(row["why"], file=sys.stderr)
    print(f"\nbest family: {best['family']} covers {len(best['icons'])}/{len(result['needed_slots'])} slots; "
          f"missing: {', '.join(best['missing']) or 'none'}. Keep missing slots label-only or Unicode; "
          f"never mix in another pack's drawing style. {result['requests']} library request(s).", file=sys.stderr)
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
    lib = common(sub.add_parser("library", help="search the emoji library; pick ONE pack that covers the bot's slots"))
    lib.add_argument("action", choices=["search", "pick", "facets", "contract"])
    lib.add_argument("query", nargs="*", help="search: words or an emoji")
    lib.add_argument("--pack", help="search inside one pack")
    lib.add_argument("--needs", help="pick: comma-separated slots")
    lib.add_argument("--from", dest="source", help="pick: texts/keyboards/payload JSON or plain text")
    lib.add_argument("--motion", choices=["static", "any"], default="static", help="static icons are preferred on buttons")
    lib.add_argument("--theme", choices=["both", "light", "dark"], default="both", help="both: prefer adaptive emoji")
    lib.add_argument("--candidates", type=int, default=6, help="packs fetched in full for real coverage")
    lib.add_argument("--profile", help="pick/facets: the bot's style profile JSON; icon style, traits and archetype become "
                                       "the brief, the brand accent is compared with each pack's colours and palette")
    for facet in FACET_FLAGS:
        lib.add_argument(f"--{facet}", help=f"pick/facets: wanted {facet} (taxonomy id or label; comma-separated)")
    lib.add_argument("--require", action="append", metavar="FACET:VALUE",
                     help="pick/facets: hard filter, the pack must carry this tag (repeatable)")
    lib.add_argument("--top", type=int, default=5)
    lib.add_argument("--library-json", help="saved answers instead of the network (tests)")
    lib.add_argument("--library-file", help="the offline catalog export (emoji-library.ndjson.gz) instead of the network: "
                                            "facets and pick --profile give the same result as online")
    lib.add_argument("--lang", choices=list(LANGS), help="language of the pack descriptions (default: the profile's "
                                                         "primary locale, else en)")
    lib.add_argument("--openapi", help="contract: a saved emoji-openapi.json to vendor into data/emoji/library-contract.json")
    lib.add_argument("--facets-file", help="contract: a saved /api/emoji-facets answer (taxonomy and thresholds)")
    a = ap.parse_args(argv)
    return {"library": cmd_library, "resolve": cmd_resolve, "suggest": cmd_suggest, "verify": cmd_verify, "capture": cmd_capture,
            "apply": cmd_apply, "strip": lambda x: cmd_apply(x, strip=True)}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
