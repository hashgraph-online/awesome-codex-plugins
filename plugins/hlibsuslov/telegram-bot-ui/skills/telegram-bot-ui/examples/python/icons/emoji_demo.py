"""Offline helpers shared by recipes 70-75: load the SYNTHETIC fixture packs and the vocabulary.

The fixture ids start with 0 and are not real custom_emoji_id values (audit_icons.py rejects
them unless --allow-fixture-ids). In a real project replace `fixture_set(...)` with a live
getStickerSet(name) through scripts/emoji_packs.py resolve.
"""
from __future__ import annotations

import importlib.util
import json
import os

from tgkit.icons import load_vocabulary, resolve_icon_map

HERE = os.path.dirname(os.path.abspath(__file__))
VOCAB = load_vocabulary()


def fixture_set(name: str) -> dict:
    with open(os.path.join(HERE, "fixtures", f"{name}.json"), encoding="utf-8") as fh:
        return json.load(fh)["result"]


def resolve(names: list[str], slots: list[str], family: str | None = None) -> tuple[dict, dict]:
    """getStickerSet results (primary first) -> (icon map document, coverage report)."""
    return resolve_icon_map([fixture_set(n) for n in names], VOCAB, slots, family=family)


def sticker_lookup(names: list[str]):
    """A getCustomEmojiStickers responder for FakeTransport backed by fixture sets."""
    by_id = {s["custom_emoji_id"]: s for n in names for s in fixture_set(n)["stickers"]}

    def respond(method: str, params: dict):
        assert len(params["custom_emoji_ids"]) <= 200
        return [by_id[i] for i in params["custom_emoji_ids"] if i in by_id]
    return respond


def audit_map(doc: dict, **kw):
    """scripts/audit_icons.py audit() without putting scripts/ on sys.path."""
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(HERE))), "scripts", "audit_icons.py")
    spec = importlib.util.spec_from_file_location("_audit_icons", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.audit(doc, **kw)
