"""The telegram-bot-ui emoji library's catalog on the Studio's Emoji page: every pack filtered by style, colour,
theme fit and motion, and a pack picked for the icon slots the project's screens use.

The catalog is the library's /api/emoji-facets answer, or the same built from the offline export
(emoji-library.ndjson.gz), both read through emoji_packs.LibraryClient and the vendored contract.
Network: only on the user's action in the local Studio (load the library, pick), through the resolver's
origin; none with an export (`bot-ui studio --emoji-library-file F`). The last catalog and pick stay in
the local cache (.bot-ui/emoji/catalog.json and pick.json, never committed): export-snapshot embeds them,
so the single-file page needs no network.

Picking: online, emoji_packs.pick_family matches every slot to each candidate pack's fallback emoji
(coverage first). Catalog only (the export, or the snapshot redoing a stale pick), emoji_packs.pick_by_profile
ranks the packs by the slots' interface roles, since the catalog has no fallback emoji.
"""
from __future__ import annotations

import json
import os
import uuid
from typing import Any

from . import skill
from .emoji import CACHE, EmojiError, PACK_NAME, _cache_dir, resolver_url, usage
from .project import PathError, Snapshot, resolve_inside

CATALOG = f"{CACHE}/catalog.json"
PICK = f"{CACHE}/pick.json"
FILTERS = ("style", "color", "fit", "motion")
TEXT_MAX = 400
PICK_TOP = 10


def _packs():
    return skill.load("emoji_packs")


def library_client(library_file: str | None = None):
    """The export when one is given, else the online library (EmojiError LIBRARY_OFF when the resolver is off)."""
    mod = _packs()
    if library_file:
        return mod.LibraryClient(export=library_file)
    if resolver_url() is None:
        raise EmojiError("LIBRARY_OFF", "the emoji library is switched off (BOT_UI_EMOJI_RESOLVER=off): start the "
                                        "Studio with --emoji-library-file emoji-library.ndjson.gz")
    return mod.LibraryClient()


# ------------------------------------------------------------------ cache

def _read(root: str, rel: str) -> dict | None:
    try:
        with open(resolve_inside(root, rel), encoding="utf-8") as fh:
            doc = json.load(fh)
    except (PathError, OSError, UnicodeDecodeError, ValueError):
        return None
    return doc if isinstance(doc, dict) else None


def _write(root: str, rel: str, doc: dict) -> None:
    cache = _cache_dir(root)
    tmp = os.path.join(cache, f".{uuid.uuid4().hex}.tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, ensure_ascii=False)
    os.replace(tmp, resolve_inside(root, rel))


def load_catalog(root: str) -> dict | None:
    doc = _read(root, CATALOG)
    return doc if doc and isinstance(doc.get("packs"), list) and isinstance(doc.get("taxonomy"), dict) else None


def load_pick(root: str) -> dict | None:
    doc = _read(root, PICK)
    return doc if doc and isinstance(doc.get("packs"), list) and isinstance(doc.get("slots"), list) else None


def fetch_catalog(root: str, *, library_file: str | None = None, client: Any = None) -> dict:
    """Read the catalog (online, or from the export) and keep it in the cache."""
    c = client or library_client(library_file)
    doc = c.facets()
    if doc is None:
        raise EmojiError("LIBRARY_NO_TAGS", "the emoji library publishes no tags yet (no /api/emoji-facets)")
    doc = {**doc, "source": "export" if c.offline else "online"}
    _write(root, CATALOG, doc)
    return doc


# ------------------------------------------------------------------ slots and the pick

def screen_slots(snap: Snapshot, lib: dict) -> list[str]:
    """Vocabulary slots the screens use: their ordinary emoji in texts and labels, then the icon map's slots
    whose emoji is placed on a screen."""
    try:
        mod = skill.load("tgkit.icons")
        vocab = mod.load_vocabulary()
    except (RuntimeError, ImportError, OSError):
        return []
    texts = [{"m": s.get("message"), "a": [a.get("label") for a in (s.get("actions") or {}).values() if isinstance(a, dict)]}
             for s in snap.screens.values()]
    slots = list(mod.slots_in(texts, vocab))
    placed = {u["id"] for u in usage(snap)}
    for slot, icon in (lib.get("icons") or {}).items():
        if slot in vocab and slot not in slots and isinstance(icon, dict) and icon.get("id") in placed:
            slots.append(slot)
    return slots


def _row(r: dict, coverage: bool) -> dict:
    return {"name": r["name"], "title": r.get("title"), "link": r.get("link") or f"https://t.me/addemoji/{r['name']}",
            "score": r["score"], "why": r.get("why", ""), "description": r.get("description"),
            "coverage": r.get("coverage") if coverage else None, "missing": r.get("missing") if coverage else None}


def pick_for_screens(snap: Snapshot, lib: dict, catalog: dict, *, client: Any = None, lang: str = "en",
                     top: int = PICK_TOP) -> dict:
    """Packs ranked for the screens' slots, each with its one-line reason and description.
    `client` online: coverage of every slot (pick_family); None or the export: the catalog alone."""
    mod = _packs()
    vocab = mod.load_vocabulary(None)
    slots = screen_slots(snap, lib)
    brief = mod.slots_brief(slots, vocab)
    notes: list[str] = []
    if not slots:
        notes.append("the screens use no emoji of the slot vocabulary yet: packs are ranked for interface icons in general")
    if client is not None and not client.offline and slots:
        res = mod.pick_family(slots, vocab, client, candidates=top, brief=brief, facets=catalog, lang=lang)
        mode, rows, notes = "coverage", [_row(r, True) for r in res["ranking"]], notes + res.get("notes", [])
    else:
        res = mod.pick_by_profile(catalog, brief, [], top=top, lang=lang)
        mode, rows = "tags", [_row(r, False) for r in res["packs"]]
        notes = notes + res["problems"]
        if slots:
            notes.append("ranked by the slots' interface roles from the catalog, which has no fallback emoji: "
                         "pick online in the local Studio for the real coverage")
    return {"mode": mode, "slots": slots, "generated": catalog.get("generated"), "source": catalog.get("source"),
            "packs": rows, "notes": notes}


def pick(root: str, snap: Snapshot, *, library_file: str | None = None, client: Any = None) -> dict:
    """The Studio's pick: the cached catalog (read first when missing), the slots, the ranking, cached."""
    from .emoji import load_library
    c = client or library_client(library_file)
    catalog = load_catalog(root) or fetch_catalog(root, client=c)
    res = pick_for_screens(snap, load_library(root), catalog, client=c, lang=lang_of(snap))
    _write(root, PICK, res)
    return res


def lang_of(snap: Snapshot) -> str:
    lang = str((snap.project or {}).get("defaultLocale") or "en").split("-")[0].lower()
    return lang if lang in ("en", "ru", "uk") else "en"


# ------------------------------------------------------------------ the client's view

def _text(value: Any) -> str:
    return value[:TEXT_MAX] if isinstance(value, str) else ""


def _label(d: Any, lang: str) -> str:
    return _text(d.get(lang) or d.get("en")) if isinstance(d, dict) else ""


def catalog_view(doc: dict, lang: str = "en") -> dict:
    """What the Emoji page shows of the catalog: the four filter facets with their values, and every pack's
    tags (at or above the library's pack threshold), size and description. Anything outside the taxonomy goes."""
    th = (doc.get("thresholds") or {}).get("pack", 0.3)
    tax = (doc.get("taxonomy") or {}).get("facets") or {}
    facets = {}
    for f in FILTERS:
        d = tax.get(f)
        if isinstance(d, dict) and isinstance(d.get("values"), dict):
            facets[f] = {"label": _label(d.get("label"), lang) or f,
                         "values": [{"id": v, "label": _label(x, lang) or v} for v, x in d["values"].items()]}
    known = {f: {v["id"] for v in d["values"]} for f, d in facets.items()}
    packs = []
    for pk in doc.get("packs") or []:
        if not isinstance(pk, dict) or not isinstance(pk.get("name"), str) or not PACK_NAME.match(pk["name"]):
            continue
        tags = {}
        for f in facets:
            vals = [[v, c] for v, c in ((pk.get("facets") or {}).get(f) or [])
                    if v in known[f] and isinstance(c, (int, float)) and c >= th]
            if vals:
                tags[f] = vals
        desc = _packs().pack_description(pk, lang) or {}
        row = {"name": pk["name"], "category": _text(pk.get("category")), "count": pk.get("count"),
               "meanings": pk.get("meanings"), "tags": tags}
        if desc:
            row["description"] = {k: _text(desc.get(k)) for k in ("what", "for", "not_for") if desc.get(k)}
        packs.append(row)
    version = (doc.get("taxonomy") or {}).get("version")
    return {"generated": doc.get("generated"), "taxonomy": version, "source": doc.get("source"), "threshold": th,
            "facets": facets, "packs": packs}


def client_fields(root: str, snap: Snapshot, lib: dict) -> dict:
    """The Studio's emoji document fields: the cached catalog and pick, and the screens' slots."""
    catalog = load_catalog(root)
    return {"catalog": catalog_view(catalog, lang_of(snap)) if catalog else None, "pick": load_pick(root) if catalog else None,
            "screenSlots": screen_slots(snap, lib)}


def snapshot_fields(snap: Snapshot, lib: dict, library_file: str | None = None) -> dict:
    """The catalog and a pick for the single-file page, without network: the export when given, else the cached
    catalog; the cached pick when it was made for these screens and this catalog, else one from the catalog."""
    catalog = library_client(library_file).facets() if library_file else (load_catalog(snap.root) if snap.root else None)
    if not catalog:
        return {}
    catalog = {**catalog, "source": "export"} if library_file else catalog
    cached = None if library_file else load_pick(snap.root)
    slots = screen_slots(snap, lib)
    if not (cached and cached.get("slots") == slots and cached.get("generated") == catalog.get("generated")):
        cached = pick_for_screens(snap, lib, catalog, lang=lang_of(snap))
    return {"catalog": catalog_view(catalog, lang_of(snap)), "pick": cached, "screenSlots": slots}
