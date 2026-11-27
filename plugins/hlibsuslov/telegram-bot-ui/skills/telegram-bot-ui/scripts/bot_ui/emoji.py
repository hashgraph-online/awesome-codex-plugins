"""Premium (custom) emoji library of a bot-ui project: packs imported by link, the bot's icon
map, and the brief an agent reads before it places custom emoji.

Files
* `emoji/library.json` (in the project, committed with it): every imported pack with its emoji
  (id, fallback, format, adaptive) and `icons`, the bot's icon map: slot (a meaning from the
  skill's `data/emoji/slots.json`, or the user's own) -> {id, set, fallback, animated, adaptive,
  note}. `icons` has the skill's icon-map shape, so `scripts/audit_icons.py emoji/library.json`
  audits it as is.
* `.bot-ui/emoji/<id>.<webp|webm|png|jpg>`: local preview cache, never committed. Without it
  every surface shows the fallback emoji instead of the picture.

Network: only `import_pack` goes online, and only when the user imports a pack by link.
By default it asks the telegram-bot-ui resolver (the project site; BOT_UI_EMOJI_RESOLVER sets
another URL or "off"), which reads the pack with its own bot: only the pack name is sent and the
user needs no token. With a token of their own (the import form, or TELEGRAM_TEST_BOT_TOKEN /
BOT_TOKEN when the resolver is off) the pack is read directly through the read-only
getStickerSet and getFile on api.telegram.org; the token is never stored, logged or returned.
A saved getStickerSet response imports the ids offline, without previews.
"""
from __future__ import annotations

import json
import os
import re
import time
import uuid
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable

from . import rich, skill
from .project import STATE_DIR, PathError, Snapshot, resolve_inside

LIBRARY = "emoji/library.json"
FORMAT = "bot-ui-emoji/v1"
CACHE = f"{STATE_DIR}/emoji"
API_HOST = "https://api.telegram.org"
TOKEN_ENV = ("TELEGRAM_TEST_BOT_TOKEN", "BOT_TOKEN")
RESOLVER_ENV = "BOT_UI_EMOJI_RESOLVER"
DEFAULT_RESOLVER = "https://telegram-bot-ui.hlixli.com/api/emoji-pack"
RESOLVER_RE = re.compile(r"^(https://[A-Za-z0-9.-]+(:\d+)?|http://(127\.0\.0\.1|localhost)(:\d+)?)(/[A-Za-z0-9._~/-]*)?$")
PICTURE_PATH = re.compile(r"^/api/emoji-pack/[A-Za-z0-9_]{1,64}/\d{1,20}$")
PICTURE_TYPES = {"image/webp": "webp", "video/webm": "webm", "image/png": "png", "image/jpeg": "jpg"}

PACK_NAME = re.compile(r"^[A-Za-z0-9_]{1,64}$")
LINK_RE = re.compile(r"^(?:https?://)?(?:www\.)?(?:t\.me|telegram\.me|telegram\.dog)/(addemoji|addstickers)/([^/?#\s]+)/?(?:[?#].*)?$", re.I)
TG_LINK_RE = re.compile(r"^tg://(addemoji|addstickers)\?set=([^&#\s]+)", re.I)
TOKEN_RE = re.compile(r"^\d{5,16}:[A-Za-z0-9_-]{30,64}$")
EMOJI_ID = re.compile(r"^\d{1,20}$")
SLOT_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,47}$")
PREVIEW_RE = re.compile(r"^(\d{1,20})\.(webp|webm|png|jpg)$")
FILE_PATH_RE = re.compile(r"^[A-Za-z0-9_-]+(/[A-Za-z0-9_.-]+)*$")
PREVIEW_MAX = 512 * 1024
PACK_MAX = 200  # Telegram's limit for a custom emoji set
TG_EMOJI = re.compile(r'<tg-emoji\s+emoji-id="(\d{1,20})"\s*>(.*?)</tg-emoji>', re.S)


class EmojiError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code, self.message = code, message

    def to_json(self) -> dict:
        return {"code": self.code, "message": self.message}


# ------------------------------------------------------------------ library file

def empty_library() -> dict:
    return {"format": FORMAT, "bot": "", "packs": {}, "icons": {}}


def load_library(root: str) -> dict:
    path = os.path.join(root, *LIBRARY.split("/"))
    return read_library(path) if os.path.isfile(path) else empty_library()


def read_library(path: str) -> dict:
    """The library document at `path` (a project's emoji/library.json), sanitized."""
    try:
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as err:
        raise EmojiError("LIBRARY_INVALID", f"{LIBRARY} is not valid UTF-8 JSON: {err}") from None
    if not isinstance(doc, dict) or doc.get("format") != FORMAT:
        raise EmojiError("LIBRARY_INVALID", f"{LIBRARY} is not a {FORMAT} document")
    return _sanitized(doc)


def _sanitized(doc: dict) -> dict:
    """Drop entries of the wrong shape (a hand-edited file must not break every surface)."""
    packs = {}
    for name, pack in (doc.get("packs") if isinstance(doc.get("packs"), dict) else {}).items():
        if not isinstance(pack, dict) or not PACK_NAME.match(str(name)):
            continue
        emoji = [{**e, "fallback": e.get("fallback") if isinstance(e.get("fallback"), str) else ""}
                 for e in (pack.get("emoji") if isinstance(pack.get("emoji"), list) else [])
                 if isinstance(e, dict) and isinstance(e.get("id"), str) and EMOJI_ID.match(e["id"])]
        packs[name] = {**pack, "title": str(pack.get("title") or name), "link": str(pack.get("link") or ""), "emoji": emoji}
    icons = {slot: {**i, "fallback": i.get("fallback") if isinstance(i.get("fallback"), str) else ""}
             for slot, i in (doc.get("icons") if isinstance(doc.get("icons"), dict) else {}).items()
             if isinstance(i, dict) and isinstance(i.get("id"), str) and EMOJI_ID.match(i["id"]) and SLOT_RE.match(str(slot))}
    return {**doc, "packs": packs, "icons": icons}


def has_library(root: str) -> bool:
    return os.path.isfile(os.path.join(root, *LIBRARY.split("/")))


def update_library(root: str, change: Callable[[dict], Any]) -> tuple[dict, Any]:
    """Re-read the library under the project write lock, apply `change`, write it atomically.
    Returns (library, what `change` returned); an EmojiError from `change` writes nothing."""
    from .store import _atomic_write, write_lock
    with write_lock(root):
        lib = load_library(root)
        out = change(lib)
        data = (json.dumps(lib, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        _atomic_write(resolve_inside(root, LIBRARY), data)
    return lib, out


def same_emoji(a: str, b: str) -> bool:
    """Equal ignoring variation selectors ('⚙' == '⚙️')."""
    strip = lambda s: s.replace("️", "").replace("︎", "").strip()  # noqa: E731
    return strip(a) == strip(b)


def emoji_index(lib: dict) -> dict[str, dict]:
    """id -> {id, fallback, format, adaptive, pack} over every pack (first pack wins)."""
    out: dict[str, dict] = {}
    for name, pack in (lib.get("packs") or {}).items():
        for e in pack.get("emoji") or []:
            if isinstance(e, dict) and isinstance(e.get("id"), str):
                out.setdefault(e["id"], {**e, "pack": name})
    for slot, icon in (lib.get("icons") or {}).items():
        if isinstance(icon, dict) and isinstance(icon.get("id"), str) and icon["id"] not in out:
            out[icon["id"]] = {"id": icon["id"], "fallback": icon.get("fallback", ""),
                               "format": "animated" if icon.get("animated") else "static",
                               "adaptive": bool(icon.get("adaptive")), "pack": icon.get("set") or ""}
    return out


MOVING = ("animated", "video")  # custom emoji formats that move; a button takes a static one only


def is_moving(e: dict | None) -> bool:
    """An index entry whose format is animated or video (an unknown id, or one without a format, is not)."""
    return bool(e) and e.get("format") in MOVING


def moving_ids(lib: dict) -> dict[str, str]:
    """id -> format of every animated or video custom emoji of a library."""
    return {i: e["format"] for i, e in emoji_index(lib).items() if is_moving(e)}


def static_twin(idx: dict[str, dict], e: dict) -> dict | None:
    """`e` when it is static, else a static emoji with the same fallback (its own pack first), else None."""
    if not is_moving(e):
        return e
    fb = e.get("fallback") or ""
    twins = [t for t in idx.values() if fb and t.get("format") == "static" and same_emoji(t.get("fallback") or "", fb)]
    return next((t for t in twins if t.get("pack") == e.get("pack")), twins[0] if twins else None)


# ------------------------------------------------------------------ meaning: does the icon say what the label says

WORD_RE = re.compile(r"[^\W\d_]+(?:['’][^\W\d_]+)?")
PLACEHOLDER_RE = re.compile(r"\{[^{}]*\}")


def _phrases(entry: dict) -> list[list[str]]:
    """The label words of a vocabulary slot as token lists: its `words` in every language plus its own label."""
    out = []
    for words in (entry.get("words") or {}).values():
        out += [w.lower().split() for w in words if isinstance(w, str) and w.strip()]
    if isinstance(entry.get("label"), str) and entry["label"].strip():
        out.append(entry["label"].lower().split())
    return out


def _says(tokens: list[str], phrase: list[str]) -> bool:
    """`phrase` occurs in `tokens`; a phrase word ending in * matches any ending."""
    def one(tok: str, pat: str) -> bool:
        return tok.startswith(pat[:-1]) if pat.endswith("*") else tok == pat
    n = len(phrase)
    return any(all(one(tokens[i + k], phrase[k]) for k in range(n)) for i in range(len(tokens) - n + 1))


def label_slots(label: str, vocab: dict[str, dict]) -> set[str]:
    """Slots whose words the label says ("Мої замовлення" -> {"order"}); only slots that carry `words` count."""
    text = rich.visible_text(label) if "<" in (label or "") else (label or "")
    tokens = [t.lower() for t in WORD_RE.findall(PLACEHOLDER_RE.sub(" ", text))]  # {order.total} is data, not words
    if not tokens:
        return set()
    return {slot for slot, entry in vocab.items() if entry.get("words") and any(_says(tokens, p) for p in _phrases(entry))}


def meaning_mismatch(labels: list[str], slots: list[str], vocab: dict[str, dict]) -> list[str] | None:
    """The slots the labels say instead, when none of the labels says any of the icon's possible slots; None when
    the icon fits, when none of its slots has `words`, or when the labels say no known slot at all."""
    if not any((vocab.get(s) or {}).get("words") for s in slots):
        return None
    said: set[str] = set()
    for label in labels:
        hit = label_slots(label, vocab)
        if hit & set(slots):
            return None
        said |= hit
    return sorted(said) or None


def slots_of(eid: str, lib: dict, idx: dict[str, dict], vocab: dict[str, dict]) -> list[str]:
    """What a custom emoji can mean: its slot in the icon map; else every vocabulary slot that accepts its fallback
    emoji, the slots where it is the first choice first (📦 -> product, then order, archive, delivery)."""
    for slot, icon in (lib.get("icons") or {}).items():
        if isinstance(icon, dict) and icon.get("id") == eid:
            return [slot]
    fb = (idx.get(eid) or {}).get("fallback") or ""
    if not fb:
        return []
    hits = [(next(i for i, u in enumerate(v.get("unicode") or []) if same_emoji(u, fb)), s) for s, v in vocab.items()
            if any(same_emoji(u, fb) for u in v.get("unicode") or [])]
    return [s for _, s in sorted(hits, key=lambda h: h[0])]


def button_icons(snap: Snapshot) -> list[dict]:
    """Every button that carries a custom emoji, with its labels: keyboard actions with `icon` (labels of every
    locale) and rich `<tg-button>` with a `<tg-emoji>` inside (the button's visible text in that locale).
    [{screenId, pointer, id, labels: {locale: text}, kind: action|rich}]"""
    out: list[dict] = []
    for sid, screen in sorted(snap.screens.items()):
        for aid, act in (screen.get("actions") or {}).items():
            icon = act.get("icon") if isinstance(act, dict) else None
            if isinstance(icon, dict) and isinstance(icon.get("customEmojiId"), str):
                label = act.get("label")
                labels = label if isinstance(label, dict) else {"": label or ""}
                out.append({"screenId": sid, "pointer": f"/actions/{aid}/icon", "id": icon["customEmojiId"],
                            "labels": {k: str(v) for k, v in labels.items()}, "kind": "action"})
        msg = screen.get("message")
        text = msg.get("text") if isinstance(msg, dict) else None
        texts = text if isinstance(text, dict) else {"": text} if isinstance(text, str) else {}
        for loc, value in texts.items():
            if not isinstance(value, str):
                continue
            for m in rich.BUTTON_RE.finditer(value):
                for e in rich.EMOJI_RE.finditer(m.group(2)):
                    eid = rich.attrs(e.group(1)).get("emoji-id", "")
                    if re.fullmatch(r"\d{1,20}", eid):
                        words = rich.visible_text(rich.EMOJI_RE.sub("", m.group(2))).strip()
                        ptr = "/message/text" + (f"/{loc}" if loc else "")
                        out.append({"screenId": sid, "pointer": ptr, "id": eid, "labels": {loc: words}, "kind": "rich"})
    return out


def meaning_issues(snap: Snapshot, lib: dict) -> list[dict]:
    """Buttons whose icon means something else than their label says (the label says another slot's words and
    none of the icon's). [{screenId, pointer, id, slot, says: [slots], labels}]"""
    vocab = {v["slot"]: v for v in vocabulary()}
    if not vocab:
        return []
    idx = emoji_index(lib)
    issues = []
    for b in button_icons(snap):
        slots = slots_of(b["id"], lib, idx, vocab)
        says = meaning_mismatch(list(b["labels"].values()), slots, vocab)
        if says:
            issues.append({**{k: b[k] for k in ("screenId", "pointer", "id", "labels")}, "slot": "/".join(slots), "says": says})
    return issues


def review_sheet(snap: Snapshot, lib: dict | None = None) -> str:
    """One HTML page to look at before shipping: every button icon next to its label, with its slot, pack, format,
    the meaning check and a FAIL line for an animated icon. Pictures come from the library's preview cache."""
    from html import escape as esc
    import base64
    lib = lib if lib is not None else load_library(snap.root)
    vocab = {v["slot"]: v for v in vocabulary()}
    idx = emoji_index(lib)
    pics = previews(snap.root) if snap.root else {}
    mime = {"webp": "image/webp", "png": "image/png", "jpg": "image/jpeg", "webm": "video/webm"}
    rows, fails = [], 0
    for b in button_icons(snap):
        e = idx.get(b["id"]) or {}
        slot = "/".join(slots_of(b["id"], lib, idx, vocab))
        says = meaning_mismatch(list(b["labels"].values()), slots_of(b["id"], lib, idx, vocab), vocab)
        problems = []
        if is_moving(e):
            problems.append(f"{e.get('format')}: a button takes a static custom emoji only")
        if says:
            problems.append(f"the label says {', '.join(says)}, the icon means {slot}")
        if not e:
            problems.append("not in the library: nobody has seen this picture")
        fails += bool(problems)
        pic = ""
        name = pics.get(b["id"])
        path = preview_file(snap.root, name) if name and snap.root else None
        if path:
            with open(path, "rb") as fh:
                data = base64.b64encode(fh.read()).decode()
            ext = name.rsplit(".", 1)[-1]
            src = f"data:{mime.get(ext, 'image/webp')};base64,{data}"
            pic = (f'<video src="{src}" muted loop autoplay></video>' if ext == "webm" else f'<img src="{src}" alt="">')
        else:
            pic = f'<span class="fb">{esc(e.get("fallback") or "?")}</span>'
        labels = "<br>".join(f"<b>{esc(k or '-')}</b> {esc(v)}" for k, v in b["labels"].items())
        verdict = "<br>".join(esc(p) for p in problems) or "fits: meaning, static, family"
        rows.append(f'<tr class="{"bad" if problems else "ok"}"><td class="pic">{pic}</td><td>{labels}</td>'
                    f"<td>{esc(slot or '?')}</td><td>{esc(e.get('pack') or '?')}</td><td>{esc(e.get('format') or '?')}</td>"
                    f"<td>{esc(b['screenId'])}<br><code>{esc(b['pointer'])}</code></td><td>{verdict}</td></tr>")
    packs = sorted({(idx.get(b['id']) or {}).get('pack') or '?' for b in button_icons(snap)})
    head = (f"<p>{len(rows)} button icon(s), {fails} to fix; packs: {esc(', '.join(packs) or '-')}. Look at every row: "
            "does the picture say what the label says, is it static, does it look like its neighbours "
            "(outline or filled, weight, colour)?</p>")
    return ("<!doctype html><meta charset=utf-8><title>Button icon review</title><style>"
            "body{font:14px system-ui;margin:24px;color:#222}table{border-collapse:collapse;width:100%}"
            "td,th{border-bottom:1px solid #ddd;padding:8px;text-align:start;vertical-align:middle}"
            ".pic img,.pic video{width:40px;height:40px}.fb{font-size:32px}.bad{background:#fff1f0}"
            "</style><h1>Button icon review</h1>" + head +
            "<table><tr><th>icon</th><th>label</th><th>slot</th><th>pack</th><th>format</th><th>where</th><th>check</th></tr>"
            + "".join(rows) + "</table>")


# ------------------------------------------------------------------ the icon plan (scripts/emoji_plan.py)

PLAN = "emoji/icon-plan.json"


def plan_places(snap: Snapshot) -> list[dict]:
    """Every place of the screens that may carry an icon: keyboard buttons and in-document `<tg-button action>`
    (labels of every locale, the keyboard they share, a leading ordinary emoji, the current icon) and titles that
    open with an emoji. The input of emoji_plan.inventory()."""
    places: list[dict] = []
    for sid, screen in sorted(snap.screens.items()):
        if not isinstance(screen, dict):
            continue
        kb = screen.get("keyboard") if isinstance(screen.get("keyboard"), dict) else {}
        on_kb = {a for row in (kb.get("rows") or []) if isinstance(row, list) for a in row if isinstance(a, str)} \
            if kb.get("type") in ("inline", "reply") else set()
        in_doc = rich.screen_action_ids(screen)
        for aid, act in (screen.get("actions") or {}).items():
            if not isinstance(act, dict) or (aid not in on_kb and aid not in in_doc) or act.get("hidden"):
                continue
            label = act.get("label")
            labels = {k: str(v) for k, v in (label if isinstance(label, dict) else {"": label or ""}).items()}
            lead = next((le for t in labels.values() if (le := leading_emoji(t))), None)
            icon = act.get("icon") if isinstance(act.get("icon"), dict) else {}
            places.append({"where": f"{sid}/actions/{aid}", "kind": "button", "labels": labels, "lead": lead,
                           "keyboard": sid if aid in on_kb else None, "icon": icon.get("customEmojiId")})
        msg = screen.get("message")
        text = msg.get("text") if isinstance(msg, dict) else None
        texts = text if isinstance(text, dict) else {"": text} if isinstance(text, str) else {}
        firsts = {loc: rich.visible_text(v).strip().splitlines()[0] for loc, v in texts.items()
                  if isinstance(v, str) and rich.visible_text(v).strip()}
        lead = next((le for t in firsts.values() if (le := leading_emoji(t))), None)
        if lead:
            places.append({"where": f"{sid}/message/title", "kind": "title", "lead": lead, "keyboard": None,
                           "labels": {loc: t.replace(lead, "", 1).strip() for loc, t in firsts.items()}})
    return places


def _plan_mod():
    return skill.load("emoji_plan")


def locked_icons(lib: dict) -> dict[str, dict]:
    """Icons of the map that a person chose (anything the plan did not write): the plan keeps them."""
    return {s: i for s, i in (lib.get("icons") or {}).items() if isinstance(i, dict) and i.get("by") != "plan"}


def make_plan(root: str, snap: Snapshot, *, client: Any = None, profile: dict | None = None, theme: str = "both",
              controls: bool = False, candidates: int = 6) -> dict:
    """Stages 0-5 of the icon plan for this project: the route and audiences from the project, the places from its
    screens, the brief from a style profile (else the Mini App kit's line icons), locks from the icon map."""
    ep = _plan_mod()
    packs = skill.load("emoji_packs")
    vocab = skill.load("tgkit.icons").load_vocabulary()
    lib = load_library(root)
    inv = ep.inventory(plan_places(snap), vocab)
    p = snap.project or {}
    audiences = sorted({s.get("audience") for s in snap.screens.values() if isinstance(s, dict) and s.get("audience")})
    gate = ep.gate((p.get("capabilities") or {}).get("customEmoji", "none"), len(inv["slots"]), audiences)
    brief, source = ep.brief_for(packs.brief_from_profile(profile) if profile else None)
    return ep.plan_icons(inv, vocab, client or packs.LibraryClient(), brief=brief, brief_source=source, theme=theme,
                         locks=locked_icons(lib), gate_info=gate, candidates=candidates, controls=controls)


def save_plan(root: str, plan: dict) -> str:
    from .store import _atomic_write, write_lock
    with write_lock(root):
        _atomic_write(resolve_inside(root, PLAN), (json.dumps(plan, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    return PLAN


def load_plan(root: str) -> dict:
    path = resolve_inside(root, PLAN)
    try:
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
    except FileNotFoundError:
        raise EmojiError("PLAN_MISSING", f"no {PLAN}: run `bot-ui emoji plan` first") from None
    except (OSError, ValueError) as err:
        raise EmojiError("PLAN_INVALID", f"{PLAN}: {err}") from None
    if not isinstance(doc, dict) or doc.get("format") != _plan_mod().FORMAT or not isinstance(doc.get("slots"), dict):
        raise EmojiError("PLAN_INVALID", f"{PLAN} is not a {_plan_mod().FORMAT} document")
    return doc


def plan_review(root: str, plan: dict) -> str:
    """The plan's review sheet with the pictures this project has cached and the library's own for the rest."""
    import base64
    pics: dict[str, str] = {}
    mime = {"webp": "image/webp", "png": "image/png", "jpg": "image/jpeg"}
    for cid, name in previews(root).items():
        ext = name.rsplit(".", 1)[-1]
        path = preview_file(root, name)
        if ext in mime and path:
            with open(path, "rb") as fh:
                pics[cid] = f"data:{mime[ext]};base64,{base64.b64encode(fh.read()).decode('ascii')}"
    try:
        base = resolver_url()
        site = _Resolver(base).origin if base else None
    except EmojiError:
        site = None
    return _plan_mod().review_html(plan, site=site, pictures=pics)


def apply_plan(root: str, plan: dict) -> dict:
    """Stage 7: the slots the review accepted (verdict ok) go into the icon map, marked by="plan" with their reason.
    Locked slots (a person's choice) are never overwritten; a blocked route writes nothing."""
    if not (plan.get("gate") or {}).get("ok", True):
        raise EmojiError("NOT_ELIGIBLE", "the plan's route is none: Telegram would strip these icons; set "
                                         "capabilities.customEmoji first, or keep words")
    accepted = _plan_mod().accepted(plan)
    pending = sorted(s for s, r in plan["slots"].items() if r.get("status") == "chosen" and s not in accepted)

    def change(lib: dict) -> dict:
        icons, applied, skipped = dict(lib.get("icons") or {}), [], []
        for slot, c in sorted(accepted.items()):
            if not SLOT_RE.match(slot) or not EMOJI_ID.match(str(c.get("id", ""))):
                skipped.append({"slot": slot, "why": "not a slot or an id"})
                continue
            if slot in icons and icons[slot].get("by") != "plan":
                skipped.append({"slot": slot, "why": "chosen by a person: kept"})
                continue
            other = next((s for s, i in icons.items() if i.get("id") == c["id"] and s != slot), None)
            if other:
                skipped.append({"slot": slot, "why": f"the same emoji already means {other}"})
                continue
            reason = next(iter(plan["slots"][slot].get("reasons") or []), "")
            icons[slot] = {"id": str(c["id"]), "set": c.get("pack") or "", "fallback": (c.get("fallback") or "")[:16],
                           "animated": False, "adaptive": bool(c.get("adaptive")), "by": "plan",
                           **({"note": reason[:200]} if reason else {})}
            applied.append(slot)
        lib["icons"] = icons
        return {"applied": applied, "skipped": skipped}

    _, res = update_library(root, change)
    packs = sorted({c.get("pack") for s, c in accepted.items() if s in res["applied"] and c.get("pack")})
    return {"ok": True, **res, "pending": pending,
            "next": ([f"bot-ui emoji import {n}" for n in packs] +
                     ["bot-ui validate", "bot-ui emoji review --out icon-review.html", "check on a real client"])}


# ------------------------------------------------------------------ links and packs

def parse_pack_link(text: str) -> str:
    """Pack name from t.me/addemoji/<name>, tg://addemoji?set=<name> or a bare name."""
    s = (text or "").strip()
    m = LINK_RE.match(s) or TG_LINK_RE.match(s)
    name = m.group(2) if m else s
    if not PACK_NAME.match(name):
        raise EmojiError("PACK_LINK", "paste a pack link like https://t.me/addemoji/<name> or the pack name "
                                      "(letters, digits and _)")
    return name


def pack_from_sticker_set(st: Any, link: str | None = None) -> dict:
    """A library pack from a getStickerSet result (or the whole {"ok", "result"} response)."""
    if isinstance(st, dict) and "result" in st and isinstance(st["result"], dict):
        st = st["result"]
    if not isinstance(st, dict) or not isinstance(st.get("stickers"), list) or not PACK_NAME.match(str(st.get("name", ""))):
        raise EmojiError("PACK_INVALID", "not a getStickerSet result: it needs name and stickers")
    if st.get("sticker_type") != "custom_emoji":
        raise EmojiError("NOT_EMOJI_PACK", f"{st['name']} is a {st.get('sticker_type', 'regular')} sticker set, not an "
                                           "emoji pack: use a https://t.me/addemoji/<name> link")
    emoji = []
    for s in st["stickers"][:PACK_MAX]:
        cid = s.get("custom_emoji_id") if isinstance(s, dict) else None
        if not isinstance(cid, str) or not EMOJI_ID.match(cid):
            continue
        fmt = "video" if s.get("is_video") else "animated" if s.get("is_animated") else "static"
        emoji.append({"id": cid, "fallback": s["emoji"][:16] if isinstance(s.get("emoji"), str) else "", "format": fmt,
                      "adaptive": bool(s.get("needs_repainting"))})
    formats = sorted({e["format"] for e in emoji})
    return {"title": str(st.get("title") or st["name"])[:128], "link": link or f"https://t.me/addemoji/{st['name']}",
            "importedAt": time.strftime("%Y-%m-%d"), "formats": formats, "emoji": emoji}


def token_from_env() -> tuple[str | None, str | None]:
    """(token, env var name) of the first configured token variable."""
    for name in TOKEN_ENV:
        value = (os.environ.get(name) or "").strip()
        if value:
            return value, name
    return None, None


class _Bot:
    """Read-only Bot API calls with the token kept out of every message."""

    def __init__(self, token: str, timeout: float = 20.0) -> None:
        if not TOKEN_RE.fullmatch(token or ""):
            raise EmojiError("TOKEN_INVALID", "that does not look like a bot token (digits:letters from @BotFather)")
        self._token, self._timeout = token, timeout

    def __repr__(self) -> str:
        return "_Bot(<token hidden>)"

    def _clean(self, text: str) -> str:
        return str(text).replace(self._token, "<token>")

    def call(self, method: str, params: dict) -> Any:
        if method not in ("getStickerSet", "getFile", "getCustomEmojiStickers"):
            raise EmojiError("METHOD_REFUSED", method)
        req = urllib.request.Request(f"{API_HOST}/bot{self._token}/{method}",
                                     data=json.dumps(params).encode("utf-8"), headers={"Content-Type": "application/json"})
        try:
            with _OPENER.open(req, timeout=self._timeout) as resp:
                doc = json.loads(resp.read(BODY_MAX).decode("utf-8"))
        except urllib.error.HTTPError as err:
            try:
                doc = json.loads(err.read(64 * 1024).decode("utf-8"))
            except ValueError:
                doc = {"ok": False, "description": f"HTTP {err.code}"}
        except (urllib.error.URLError, OSError, ValueError) as err:
            raise EmojiError("TELEGRAM_UNREACHABLE", self._clean(f"Telegram did not answer: {err}")) from None
        if not doc.get("ok"):
            raise EmojiError("TELEGRAM_ERROR", self._clean(f"{method}: {doc.get('description', 'error')}"))
        return doc.get("result")

    def download(self, file_path: str) -> bytes:
        if not FILE_PATH_RE.match(file_path) or ".." in file_path:
            raise EmojiError("FILE_PATH", "unexpected file path")
        try:
            with _OPENER.open(f"{API_HOST}/file/bot{self._token}/{file_path}", timeout=self._timeout) as resp:
                data = resp.read(PREVIEW_MAX + 1)
        except (urllib.error.URLError, OSError) as err:
            raise EmojiError("TELEGRAM_UNREACHABLE", self._clean(f"download failed: {err}")) from None
        if len(data) > PREVIEW_MAX:
            raise EmojiError("FILE_TOO_LARGE", f"> {PREVIEW_MAX} bytes")
        return data


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """A redirect could lead to another host or an unbounded body: treat it as an error."""

    def redirect_request(self, *args, **kwargs):
        return None


_OPENER = urllib.request.build_opener(_NoRedirect)
BODY_MAX = 2 * 1024 * 1024


def resolver_url() -> str | None:
    """Base URL of the pack resolver, or None when it is turned off."""
    value = (os.environ.get(RESOLVER_ENV) or DEFAULT_RESOLVER).strip().rstrip("/")
    if value.lower() in ("off", "none", "0", "false"):
        return None
    if not RESOLVER_RE.match(value):
        raise EmojiError("RESOLVER_URL", f"{RESOLVER_ENV} must be an https URL (or http://localhost for testing)")
    return value


class _Resolver:
    """The telegram-bot-ui pack resolver: GET <base>/<name> and the picture paths it returns.
    Only the pack name leaves this machine; pictures come only from the resolver's own origin."""

    def __init__(self, base: str, timeout: float = 30.0) -> None:
        self.base, self._timeout = base, timeout
        self.origin = "/".join(base.split("/", 3)[:3])
        self.host = self.origin.split("://", 1)[1]

    def _get(self, url: str, limit: int) -> tuple[int, str, bytes]:
        req = urllib.request.Request(url, headers={"User-Agent": "bot-ui-studio", "Accept": "application/json, image/*, video/webm"})
        try:
            with _OPENER.open(req, timeout=self._timeout) as resp:
                return resp.status, resp.headers.get("Content-Type", ""), resp.read(limit + 1)
        except urllib.error.HTTPError as err:
            return err.code, (err.headers.get("Content-Type", "") if err.headers else ""), err.read(64 * 1024)
        except (urllib.error.URLError, OSError, ValueError) as err:
            raise EmojiError("RESOLVER_UNREACHABLE", f"the emoji resolver ({self.host}) did not answer: "
                                                     f"{getattr(err, 'reason', err)}") from None

    def pack(self, name: str) -> dict:
        status, _, body = self._get(f"{self.base}/{name}", BODY_MAX)
        if len(body) > BODY_MAX:
            raise EmojiError("RESOLVER_ERROR", "the emoji resolver answer is too large")
        try:
            doc = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            raise EmojiError("RESOLVER_ERROR", f"the emoji resolver answered HTTP {status} without JSON") from None
        if status != 200 or not isinstance(doc, dict) or not doc.get("ok"):
            err = (doc.get("error") if isinstance(doc, dict) else None) or {}
            raise EmojiError(str(err.get("code") or "RESOLVER_ERROR"), str(err.get("message") or f"HTTP {status}"))
        return doc

    def search(self, query: str, pack: str | None = None) -> dict:
        """The library's ranked search (GET <origin>/api/emoji-search?q=...&pack=...): emoji with
        real ids and the packs they come from. Only the query words leave this machine."""
        params = {"q": query[:160]}
        if pack:
            if not PACK_NAME.match(pack):
                raise EmojiError("PACK_NAME", f"not a pack name: {pack!r}")
            params["pack"] = pack
        status, _, body = self._get(f"{self.origin}/api/emoji-search?{urllib.parse.urlencode(params)}", BODY_MAX)
        try:
            doc = json.loads(body.decode("utf-8")) if len(body) <= BODY_MAX else None
        except (UnicodeDecodeError, ValueError):
            doc = None
        if status != 200 or not isinstance(doc, dict) or not doc.get("ok"):
            err = (doc.get("error") if isinstance(doc, dict) else None) or {}
            raise EmojiError(str(err.get("code") or "RESOLVER_ERROR"), str(err.get("message") or f"search: HTTP {status}"))
        return doc

    def facets(self) -> dict:
        """GET <origin>/api/emoji-facets: the tag taxonomy and every listed pack's faceted tags with their
        confidence (style, colour, theme fit, motion, topic, mood, interface roles, bot categories)."""
        status, _, body = self._get(f"{self.origin}/api/emoji-facets", BODY_MAX)
        try:
            doc = json.loads(body.decode("utf-8")) if len(body) <= BODY_MAX else None
        except (UnicodeDecodeError, ValueError):
            doc = None
        if status != 200 or not isinstance(doc, dict) or not doc.get("ok") or not isinstance(doc.get("packs"), list):
            err = (doc.get("error") if isinstance(doc, dict) else None) or {}
            raise EmojiError(str(err.get("code") or "RESOLVER_ERROR"), str(err.get("message") or f"facets: HTTP {status}"))
        return doc

    def sets_of(self, ids: list[str]) -> dict[str, str]:
        """{custom emoji id: its pack name} through GET <base>/by-id?ids=1,2,3 (ids Telegram knows only)."""
        status, _, body = self._get(f"{self.base}/by-id?ids={','.join(ids)}", BODY_MAX)
        try:
            doc = json.loads(body.decode("utf-8")) if len(body) <= BODY_MAX else None
        except (UnicodeDecodeError, ValueError):
            doc = None
        if status in (400, 404) and (not isinstance(doc, dict) or (doc.get("error") or {}).get("code") in ("PACK_NAME", "PACK_NOT_FOUND", None)):
            raise EmojiError("RESOLVER_NO_IDS", f"the emoji resolver ({self.host}) cannot look up packs by emoji id yet: "
                                                f"set {' or '.join(TOKEN_ENV)} (the bot's own token works) and run again")
        if status != 200 or not isinstance(doc, dict) or not doc.get("ok") or not isinstance(doc.get("emoji"), list):
            err = (doc.get("error") if isinstance(doc, dict) else None) or {}
            raise EmojiError(str(err.get("code") or "RESOLVER_ERROR"), str(err.get("message") or f"HTTP {status}"))
        return {e["id"]: e["set"] for e in doc["emoji"] if isinstance(e, dict) and isinstance(e.get("id"), str)
                and isinstance(e.get("set"), str) and PACK_NAME.match(e["set"])}

    def picture(self, path: Any) -> tuple[str, bytes] | None:
        if not isinstance(path, str) or not PICTURE_PATH.match(path):
            return None
        try:
            status, ctype, body = self._get(self.origin + path, PREVIEW_MAX)
        except EmojiError:
            return None
        ext = PICTURE_TYPES.get(ctype.split(";")[0].strip())
        if status != 200 or not ext or len(body) > PREVIEW_MAX:
            return None
        return ext, body


def _save_preview(root: str, cid: str, ext: str, data: bytes) -> None:
    """Write one picture into the cache: a unique temp file, then an atomic replace; the same
    emoji's picture in another format goes afterwards. Links in the path are refused."""
    if not EMOJI_ID.match(cid) or ext not in ("webp", "webm", "png", "jpg"):
        return
    cache = _cache_dir(root)
    target = resolve_inside(root, f"{CACHE}/{cid}.{ext}")
    tmp = os.path.join(cache, f".{cid}.{uuid.uuid4().hex}.tmp")
    with open(tmp, "wb") as fh:
        fh.write(data)
    os.replace(tmp, target)
    for other in ("webp", "webm", "png", "jpg"):
        if other != ext:
            try:
                os.remove(resolve_inside(root, f"{CACHE}/{cid}.{other}"))
            except (FileNotFoundError, PathError):
                pass


def _preview_source(sticker: dict) -> str | None:
    """file_id to show in a browser: the sticker itself (WEBP, WEBM) or the thumbnail of a TGS."""
    if sticker.get("is_animated"):
        thumb = sticker.get("thumbnail") or sticker.get("thumb")
        return thumb.get("file_id") if isinstance(thumb, dict) else None
    return sticker.get("file_id")


def _cache_dir(root: str) -> str:
    from .store import _state_dir
    _state_dir(root)
    os.makedirs(os.path.join(root, *CACHE.split("/")), exist_ok=True)
    return resolve_inside(root, CACHE)


def fetch_previews(root: str, stickers: list[dict], bot: Any, workers: int = 6) -> tuple[int, int]:
    """Download a preview per sticker into the cache. Returns (saved, failed)."""
    def one(s: dict) -> bool:
        cid, fid = s.get("custom_emoji_id"), _preview_source(s)
        if not isinstance(cid, str) or not EMOJI_ID.match(cid) or not fid:
            return False
        try:
            path = (bot.call("getFile", {"file_id": fid}) or {}).get("file_path") or ""
            ext = path.rsplit(".", 1)[-1].lower() if "." in path else ""
            ext = "jpg" if ext == "jpeg" else ext
            if ext not in ("webp", "webm", "png", "jpg"):
                return False
            data = bot.download(path)
        except EmojiError:
            return False
        _save_preview(root, cid, ext, data)
        return True

    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(one, stickers[:PACK_MAX]))
    return sum(results), sum(1 for r in results if not r)


def _from_resolver(root: str, name: str, resolver: Any) -> tuple[dict, str, int, int]:
    """A pack and its pictures through the resolver: (pack, name, pictures saved, without one)."""
    doc = resolver.pack(name)
    real = str(doc.get("name") or name)
    if not PACK_NAME.match(real):
        raise EmojiError("RESOLVER_ERROR", "the emoji resolver returned a bad pack name")
    items = [e for e in (doc.get("emoji") if isinstance(doc.get("emoji"), list) else [])[:PACK_MAX]
             if isinstance(e, dict) and isinstance(e.get("id"), str) and EMOJI_ID.match(e["id"])]
    if not items:
        raise EmojiError("RESOLVER_ERROR", "the emoji resolver returned no emoji for this pack; nothing was changed")
    emoji = [{"id": e["id"], "fallback": str(e.get("fallback") or "")[:16],
              "format": e["format"] if e.get("format") in ("static", "animated", "video") else "static",
              "adaptive": bool(e.get("adaptive"))} for e in items]
    pack = {"title": str(doc.get("title") or real)[:128], "link": f"https://t.me/addemoji/{real}",
            "importedAt": time.strftime("%Y-%m-%d"), "formats": sorted({e["format"] for e in emoji}), "emoji": emoji}
    def one(e: dict) -> bool:
        got = resolver.picture(e.get("preview"))
        if not got:
            return False
        _save_preview(root, e["id"], *got)
        return True

    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(one, items))
    return pack, real, sum(results), sum(1 for r in results if not r)


def import_pack(root: str, *, link: str | None = None, token: str | None = None, sticker_set: Any = None,
                bot: Any = None, resolver: Any = None) -> dict:
    """Add (or refresh) a pack in the library. `sticker_set` = a saved getStickerSet response
    (offline, no previews); `token` (or `bot`, for tests) reads it directly from Telegram;
    otherwise the telegram-bot-ui resolver reads it (`resolver`, for tests). Only when the
    resolver is off does a token from the environment take over."""
    load_library(root)  # an unreadable library stops the import before any network call
    source = "file"
    saved = failed = 0
    pack = None
    if sticker_set is None:
        name = parse_pack_link(link or "")
        if bot is None and not token and resolver is None:
            base = resolver_url()
            if base:
                resolver = _Resolver(base)
            else:
                token = token_from_env()[0]
                if not token:
                    raise EmojiError("TOKEN_NEEDED", f"the emoji resolver is off ({RESOLVER_ENV}): reading a pack needs any "
                                                     f"bot token (read-only getStickerSet): set {' or '.join(TOKEN_ENV)}; "
                                                     "it is never saved")
        if resolver is not None:
            pack, name, saved, failed = _from_resolver(root, name, resolver)
            source = "resolver"
        else:
            bot = bot or _Bot(token or "")
            sticker_set = bot.call("getStickerSet", {"name": name})
            source = "getStickerSet"
    if pack is None:
        pack = pack_from_sticker_set(sticker_set, link if link and LINK_RE.match(link.strip()) else None)
        raw = sticker_set.get("result", sticker_set) if isinstance(sticker_set, dict) else {}
        name = raw["name"]
        if bot is not None and source == "getStickerSet":
            saved, failed = fetch_previews(root, raw.get("stickers") or [], bot)
    pack["source"] = source

    def merge(lib: dict) -> None:
        lib["packs"] = {**lib["packs"], name: pack}
        # Icons keep their slot; a refreshed pack updates their fallback and format.
        idx = {e["id"]: e for e in pack["emoji"]}
        for icon in lib["icons"].values():
            e = idx.get(icon.get("id"))
            if e and icon.get("set") == name:
                icon.update(fallback=e["fallback"], animated=e["format"] != "static", adaptive=e["adaptive"])

    update_library(root, merge)
    return {"ok": True, "pack": name, "title": pack["title"], "count": len(pack["emoji"]), "source": source,
            "previews": saved, "previewsFailed": failed}


IDS_BATCH = 200  # getCustomEmojiStickers takes at most 200 ids
IMPORT_MAP = "import-map.json"


def source_ids(root: str) -> dict[str, str]:
    """Custom emoji ids `bot-ui import` found in the bot's code ({id: file:line}), kept in import-map.json."""
    try:
        with open(os.path.join(root, IMPORT_MAP), encoding="utf-8") as fh:
            found = json.load(fh).get("customEmoji")
    except (OSError, ValueError, AttributeError):
        return {}
    if not isinstance(found, dict):
        return {}
    return {k: str(v)[:200] for k, v in found.items() if isinstance(k, str) and EMOJI_ID.match(k)}


def used_ids(snap: Snapshot) -> dict[str, list[str]]:
    """Every custom emoji the bot uses: its screens and, after `bot-ui import`, its code. {id: [where]}"""
    out: dict[str, list[str]] = {}
    for u in usage(snap):
        out.setdefault(u["id"], []).append(f"{u['screenId']}{u['pointer']}")
    for cid, where in source_ids(snap.root).items() if snap.root else ():
        out.setdefault(cid, []).append(where)
    return out


def missing_ids(snap: Snapshot, lib: dict) -> list[str]:
    """Ids the bot uses whose pack is not in the library yet."""
    known = emoji_index({**lib, "icons": {}})  # an icon set by hand still has no pack
    return [cid for cid in used_ids(snap) if cid not in known]


def _transport(token: str | None, bot: Any, resolver: Any) -> tuple[Any, Any]:
    """(bot, resolver) the same way import_pack picks them: a given token or bot, else the
    resolver, else a token from the environment."""
    if bot is not None or resolver is not None:
        return bot, resolver
    if token:
        return _Bot(token), None
    base = resolver_url()
    if base:
        return None, _Resolver(base)
    env = token_from_env()[0]
    if not env:
        raise EmojiError("TOKEN_NEEDED", f"the emoji resolver is off ({RESOLVER_ENV}): looking up packs needs any bot "
                                         f"token (read-only getCustomEmojiStickers): set {' or '.join(TOKEN_ENV)}; "
                                         "it is never saved")
    return _Bot(env), None


def sets_of(ids: list[str], *, bot: Any = None, resolver: Any = None) -> dict[str, str]:
    """{custom emoji id: pack name}; ids Telegram does not know (or whose pack is gone) are left out."""
    out: dict[str, str] = {}
    for i in range(0, len(ids), IDS_BATCH):
        chunk = ids[i:i + IDS_BATCH]
        if resolver is not None:
            out.update({k: v for k, v in resolver.sets_of(chunk).items() if k in chunk})
            continue
        for s in bot.call("getCustomEmojiStickers", {"custom_emoji_ids": chunk}) or []:
            cid, name = (s.get("custom_emoji_id"), s.get("set_name")) if isinstance(s, dict) else (None, None)
            if isinstance(cid, str) and cid in chunk and isinstance(name, str) and PACK_NAME.match(name):
                out[cid] = name
    return out


def adopt_icons(root: str, snap: Snapshot) -> list[dict]:
    """Button icons of the bot become slots of the icon map by their emoji's meaning, so new
    screens reuse them. Only a free slot whose first emoji is the pack emoji's own; never a
    second meaning for one emoji. A button's animated or video emoji enters the map as its static
    twin (same emoji, same pack first); without one it is left out, buttons take static emoji only."""
    vocab = [v for v in vocabulary() if v.get("unicode")]
    buttons = list(dict.fromkeys(u["id"] for u in usage(snap) if u["where"] == "button"))

    def plan(lib: dict) -> list[dict]:
        idx, icons, out = emoji_index({**lib, "icons": {}}), dict(lib["icons"]), []
        for used in buttons:
            e = idx.get(used)
            e = static_twin(idx, e) if e else None
            if e is None or not e["fallback"] or any(i.get("id") == e["id"] for i in icons.values()):
                continue
            slot = next((v["slot"] for v in vocab if v["slot"] not in icons and same_emoji(v["unicode"][0], e["fallback"])), None)
            if slot:
                icons[slot] = {"id": e["id"]}
                out.append({"slot": slot, "id": e["id"], "fallback": e["fallback"], "set": e["pack"]})
        return out

    if not buttons or not vocab or not plan(load_library(root)):
        return []

    def change(lib: dict) -> list[dict]:
        todo = plan(lib)
        for a in todo:
            _set_icon(lib, a["slot"], a["id"], "adopted from the bot's buttons", None)
        return todo

    return update_library(root, change)[1]


def import_used(root: str, snap: Snapshot, *, token: str | None = None, bot: Any = None, resolver: Any = None,
                map_icons: bool = True) -> dict:
    """Import every pack the bot already uses: find the pack of each custom emoji id (screens and
    code) with getCustomEmojiStickers, import those packs, then adopt the button icons into the
    icon map. One bad pack does not stop the others; ids without a pack are reported."""
    lib = load_library(root)
    used = used_ids(snap)
    missing = missing_ids(snap, lib)
    result: dict[str, Any] = {"ok": True, "used": len(used), "missing": len(missing), "packs": [], "failed": [],
                              "unresolved": [], "adopted": []}
    if missing:
        bot, resolver = _transport(token, bot, resolver)
        found = sets_of(missing, bot=bot, resolver=resolver)
        result["unresolved"] = [{"id": cid, "where": used[cid][:3]} for cid in missing if cid not in found]
        for name in sorted(set(found.values())):
            try:
                res = import_pack(root, link=name, bot=bot, resolver=resolver)
                result["packs"].append({k: res[k] for k in ("pack", "title", "count", "previews")}
                                       | {"ids": sum(1 for v in found.values() if v == name)})
            except EmojiError as err:
                result["failed"].append({"pack": name, **err.to_json()})
    if map_icons:
        result["adopted"] = adopt_icons(root, snap)
    return result


def import_used_markdown(res: dict) -> str:
    if not res["used"]:
        return "the bot uses no custom emoji: nothing to import"
    lines = [f"{res['used']} custom emoji in use, {res['missing']} were not in {LIBRARY}"]
    lines += [f"  + {p['title']} ({p['pack']}): {p['count']} emoji, {p['ids']} used by the bot, {p['previews']} previews"
              for p in res["packs"]]
    lines += [f"  ! {f['pack']}: {f.get('code')} {f.get('message', '')}" for f in res["failed"]]
    if res["unresolved"]:
        lines.append(f"  ? {len(res['unresolved'])} id(s) Telegram does not know (deleted pack or not an emoji id): "
                     + ", ".join(f"{u['id']} ({'; '.join(u['where'])})" for u in res["unresolved"][:10]))
    lines += [f"  = icon map: {a['slot']} <- {a['fallback']} {a['id']} ({a['set']})" for a in res["adopted"]]
    return "\n".join(lines)


def remove_pack(root: str, name: str) -> dict:
    def drop(lib: dict) -> None:
        if name not in lib["packs"]:
            raise EmojiError("PACK_NOT_FOUND", str(name))
        del lib["packs"][name]

    lib, _ = update_library(root, drop)
    kept = [s for s, i in lib["icons"].items() if i.get("set") == name]
    return {"ok": True, "removed": name, "iconsKept": kept}


def set_icon(root: str, slot: str, emoji_id: str | None, *, note: str | None = None, fallback: str | None = None) -> dict:
    """Put an emoji on a slot of the icon map (or clear the slot with emoji_id None)."""
    if not isinstance(slot, str) or not SLOT_RE.match(slot):
        raise EmojiError("SLOT_INVALID", "a slot is a short meaning in lowercase: home, back, cart, paid, ...")
    if fallback is not None and not isinstance(fallback, str):
        raise EmojiError("FALLBACK_INVALID", "the fallback is one ordinary emoji")
    if note is not None and not isinstance(note, str):
        raise EmojiError("NOTE_INVALID", "the note is text")
    lib, icons = update_library(root, lambda lib: _set_icon(lib, slot, emoji_id, note, fallback))
    return {"ok": True, "icons": icons}


def _set_icon(lib: dict, slot: str, emoji_id: str | None, note: str | None, fallback: str | None) -> dict:
    icons = dict(lib["icons"])
    if emoji_id is None:
        icons.pop(slot, None)
    else:
        if not isinstance(emoji_id, str) or not EMOJI_ID.match(emoji_id):
            raise EmojiError("EMOJI_INVALID", "a custom emoji id is digits")
        other = next((s for s, i in icons.items() if i.get("id") == emoji_id and s != slot), None)
        if other:
            raise EmojiError("ICON_DUPLICATE", f"this emoji already means '{other}': one emoji, one meaning")
        e = emoji_index({**lib, "icons": {}}).get(emoji_id)
        if e is None and not fallback:
            raise EmojiError("EMOJI_UNKNOWN", "import its pack first, or give the fallback emoji")
        icon = {"id": emoji_id, "set": e["pack"] if e else "", "fallback": ((e or {}).get("fallback") or fallback or "")[:16],
                "animated": bool(e and e["format"] != "static"), "adaptive": bool(e and e["adaptive"])}
        prev = icons.get(slot) or {}
        if note is not None or prev.get("note"):
            icon["note"] = (note if note is not None else prev.get("note", "")).strip()[:200]
            if not icon["note"]:
                icon.pop("note")
        icons[slot] = icon
    lib["icons"] = icons
    return icons


def previews(root: str) -> dict[str, str]:
    """id -> cached preview file name."""
    try:
        path = resolve_inside(root, CACHE)
    except PathError:
        return {}
    if not os.path.isdir(path):
        return {}
    out = {}
    for name in sorted(os.listdir(path)):
        m = PREVIEW_RE.match(name)
        if m:
            out[m.group(1)] = name
    return out


def preview_file(root: str, name: str) -> str | None:
    if not PREVIEW_RE.match(name):
        return None
    try:
        full = resolve_inside(root, f"{CACHE}/{name}")
    except PathError:
        return None
    return full if os.path.isfile(full) else None


# ------------------------------------------------------------------ usage, vocabulary, brief

def _walk(node: Any, pointer: str, visit: Callable[[str, str], None]) -> None:
    if isinstance(node, str):
        visit(pointer, node)
    elif isinstance(node, dict):
        for k, v in node.items():
            _walk(v, f"{pointer}/{str(k).replace('~', '~0').replace('/', '~1')}", visit)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            _walk(v, f"{pointer}/{i}", visit)


def usage(snap: Snapshot) -> list[dict]:
    """Every custom emoji in the screens: {screenId, pointer, id, fallback, where: text|button}. One inside
    a rich `<tg-button>` is a button's."""
    out: list[dict] = []
    for sid, screen in sorted(snap.screens.items()):
        for part in ("message",):
            def text(pointer: str, value: str, sid=sid) -> None:
                for eid, fallback, on_button in rich.custom_emoji(value):
                    out.append({"screenId": sid, "pointer": pointer, "id": eid, "fallback": fallback,
                                "where": "button" if on_button else "text"})
            _walk(screen.get(part), f"/{part}", text)
        for aid, act in (screen.get("actions") or {}).items():
            icon = act.get("icon") if isinstance(act, dict) else None
            if isinstance(icon, dict) and isinstance(icon.get("customEmojiId"), str):
                out.append({"screenId": sid, "pointer": f"/actions/{aid}/icon", "id": icon["customEmojiId"],
                            "fallback": None, "where": "button"})
    return out


def leading_emoji(label: str) -> str | None:
    """The emoji a button label starts with ('🛒' for '🛒 Cart'), if any."""
    mod = _icons_mod()
    hit = mod._leading_cluster(label) if mod is not None and isinstance(label, str) else None
    return hit[0] if hit else None


def vocabulary() -> list[dict]:
    """The skill's slot vocabulary for the slot picker: [{slot, group, label, unicode, use, note}]."""
    try:
        vocab = skill.load("tgkit.icons").load_vocabulary()
    except (RuntimeError, OSError, ImportError):
        return []
    return [{"slot": s, **{k: v.get(k) for k in ("group", "label", "unicode", "use", "note", "words")}} for s, v in vocab.items()]


def _icons_mod():
    try:
        return skill.load("tgkit.icons")
    except (RuntimeError, ImportError):
        return None


def candidates(snap: Snapshot, lib: dict) -> list[dict]:
    """Ordinary emoji in texts and labels that an icon of the map could replace. The icon is the slot's
    static emoji: an animated or video one gives way to its static twin, and on a button (a label) to
    nothing when it has none."""
    icons = {s: i for s, i in (lib.get("icons") or {}).items() if isinstance(i, dict) and i.get("id")}
    mod = _icons_mod()
    if not icons or mod is None:
        return []
    emap = mod.EmojiMap(icons, mod.load_vocabulary())
    idx = emoji_index(lib)
    out: list[dict] = []
    seen: set[tuple[str, str, str]] = set()

    def visit(sid: str, pointer: str, value: str, button: bool = False) -> None:
        plain = TG_EMOJI.sub("", value)
        for _, _, cl in mod.iter_clusters(plain):
            slot = emap.slot_for(cl)
            if slot and (sid, pointer, slot) not in seen:
                seen.add((sid, pointer, slot))
                cid, e = icons[slot]["id"], idx.get(icons[slot]["id"])
                twin = static_twin(idx, e) if e else None
                if twin:
                    cid = twin["id"]
                elif button and is_moving(e):
                    continue
                out.append({"screenId": sid, "pointer": pointer, "emoji": cl, "slot": slot, "id": cid})

    for sid, screen in sorted(snap.screens.items()):
        _walk(screen.get("message"), "/message", lambda p, v, sid=sid: visit(sid, p, v))
        for aid, act in (screen.get("actions") or {}).items():
            if isinstance(act, dict):
                _walk(act.get("label"), f"/actions/{aid}/label", lambda p, v, sid=sid: visit(sid, p, v, True))
    return out


def suggest_icons(snap: Snapshot, lib: dict) -> list[dict]:
    """Slots the screens imply (their ordinary emoji) matched to emoji of the imported packs. A static
    emoji wins over an animated or video one of the same meaning; a slot only animated emoji cover is
    still suggested, with `animated` true (a button cannot take it)."""
    mod = _icons_mod()
    packs = lib.get("packs") or {}
    if mod is None or not packs:
        return []
    vocab = mod.load_vocabulary()
    taken = {s for s, i in (lib.get("icons") or {}).items() if i.get("id")}
    texts = [{"m": s.get("message"), "a": [a.get("label") for a in (s.get("actions") or {}).values() if isinstance(a, dict)]}
             for s in snap.screens.values()]
    wanted = [s for s in mod.slots_in(texts, vocab) if s not in taken]
    if not wanted:
        return []
    sets = [{"name": n, "sticker_type": "custom_emoji",
             "stickers": [{"custom_emoji_id": e["id"], "emoji": e["fallback"], "is_animated": e.get("format") == "animated",
                           "is_video": e.get("format") == "video"} for e in p.get("emoji") or []]}
            for n, p in packs.items()]
    static_sets = [{**s, "stickers": [x for x in s["stickers"] if not (x["is_animated"] or x["is_video"])]} for s in sets]
    found = dict(mod.resolve_icon_map(static_sets, vocab, wanted)[0].get("icons") or {})
    rest = [s for s in wanted if s not in found]
    if rest:  # no static emoji of that meaning in the packs
        more = mod.resolve_icon_map(sets, vocab, rest)[0].get("icons") or {}
        found.update({s: i for s, i in more.items() if i["id"] not in {f["id"] for f in found.values()}})
    used = {i.get("id") for i in (lib.get("icons") or {}).values()}
    return [{"slot": s, "id": i["id"], "set": i.get("set"), "fallback": i.get("fallback"), "animated": bool(i.get("animated"))}
            for s, i in found.items() if i.get("id") and i["id"] not in used]


ROUTE_TEXT = {
    "fragment": "fragment: the bot bought extra usernames on Fragment; custom emoji work in every chat type",
    "owner_premium": "owner_premium: private, group and supergroup chats only (not channels, inline or business sends); "
                     "if the owner's Premium lapses Telegram drops them silently",
    "none": "none: Telegram drops custom emoji from this bot without an error; set capabilities.customEmoji first, "
            "or keep ordinary emoji",
}

RULES = [
    "Use only ids from the icon map below (or from an imported pack); never invent or guess an id.",
    "Choose by meaning (slot), not by look: the same meaning always gets the same icon; one icon never means two things.",
    "Text: `<tg-emoji emoji-id=\"ID\">FALLBACK</tg-emoji>` in regular.html, with the map's fallback (the sticker's own emoji) inside.",
    "Button: `\"icon\": {\"customEmojiId\": \"ID\"}`; do not also start the label with an emoji; the label must read well without the icon.",
    "Buttons take STATIC custom emoji only, never an animated or video one: not as `icon`, not inside a rich `<tg-button>` "
    "(`validate` reports BUTTON_EMOJI_ANIMATED as an error). Text: static is the default; an animated or video emoji is a "
    "flagged exception (CUSTOM_EMOJI_ANIMATED), only when no static emoji of that meaning exists.",
    "The icon says what the label says: a button labelled Orders carries the order icon, never a near look-alike "
    "(ICON_MEANING_MISMATCH). A slot the main pack cannot say well comes from another STATIC pack of the same style "
    "(outline or filled, weight, colour treatment) or stays label-only; a wrong meaning to stay in one pack is never "
    "acceptable. Icons the user chose themselves stay as they are.",
    "One family: prefer one pack for the icons you pick (a same-style sibling only fills gaps).",
    "Double check before shipping: `bot-ui emoji review --out icon-review.html`, open it, look at every row (meaning, "
    "static, family) and fix every red row.",
    "Restraint: one accent per title or line, not every button of a keyboard; a keyboard is either all icons or none.",
    "Every locale gets the same icons; only the words change.",
    "Check: `bot-ui validate`, `bot-ui emoji brief` (no unknown ids), and the skill's `scripts/audit_icons.py emoji/library.json`.",
]


def brief(snap: Snapshot, lib: dict | None = None) -> dict:
    """Everything an agent needs to place custom emoji in this project, as one object."""
    lib = lib if lib is not None else load_library(snap.root)
    p = snap.project or {}
    route = (p.get("capabilities") or {}).get("customEmoji", "none")
    vocab = {v["slot"]: v for v in vocabulary()}
    idx = emoji_index(lib)
    used = usage(snap)
    by_id: dict[str, list[dict]] = {}
    for u in used:
        by_id.setdefault(u["id"], []).append(u)
    slot_of = {i.get("id"): s for s, i in (lib.get("icons") or {}).items()}
    icons = []
    for slot, i in (lib.get("icons") or {}).items():
        e = idx.get(i.get("id")) or {}
        v = vocab.get(slot) or {}
        icons.append({"slot": slot, "id": i.get("id"), "fallback": i.get("fallback", ""), "set": i.get("set", ""),
                      "format": e.get("format", "animated" if i.get("animated") else "static"),
                      "use": v.get("use") or [], "label": v.get("label") or "", "note": i.get("note") or v.get("note") or "",
                      "placed": [f"{u['screenId']}{u['pointer']}" for u in by_id.get(i.get("id"), [])]})
    unknown = [u for u in used if u["id"] not in idx]
    mismatched = [{**u, "expected": idx[u["id"]]["fallback"]} for u in used
                  if u["where"] == "text" and u["id"] in idx and idx[u["id"]]["fallback"]
                  and not same_emoji(u["fallback"], idx[u["id"]]["fallback"])]
    return {
        "project": p.get("projectId"), "title": p.get("title"), "library": LIBRARY, "route": route,
        "routeText": ROUTE_TEXT.get(route, route),
        "packs": [{"name": n, "title": pk.get("title"), "link": pk.get("link"), "count": len(pk.get("emoji") or []),
                   "formats": pk.get("formats") or []} for n, pk in (lib.get("packs") or {}).items()],
        "icons": icons,
        "placed": [{**u, "slot": slot_of.get(u["id"])} for u in used],
        "unknown": unknown, "fallbackMismatch": mismatched,
        "candidates": candidates(snap, lib),
        "meaningMismatch": meaning_issues(snap, lib),
        "rules": RULES,
    }


def brief_markdown(b: dict) -> str:
    out = [f"# Premium emoji for {b.get('title') or b.get('project')}", "",
           f"Library: `{b['library']}` (bot-ui project). Eligibility: `capabilities.customEmoji` = {b['routeText']}.", ""]
    if b["packs"]:
        out.append("Packs: " + "; ".join(f"{pk['title']} ({pk['link']}, {pk['count']} emoji, {'/'.join(pk['formats']) or '-'})"
                                         for pk in b["packs"]) + ".")
        out.append("")
    if b["icons"]:
        out += ["## Icon map: place these, by meaning", "", "| slot | id | fallback | use | format | note | placed |",
                "| --- | --- | --- | --- | --- | --- | --- |"]
        for i in b["icons"]:
            out.append(f"| {i['slot']} | {i['id']} | {i['fallback']} | {', '.join(i['use']) or '-'} | {i['format']} | "
                       f"{i['note'] or '-'} | {', '.join(i['placed']) or '-'} |")
        out.append("")
    else:
        out += ["No icon map yet: pick emoji for meanings in the Studio (Emoji page) before placing them.", ""]
    if b["candidates"]:
        out += ["## Candidates: ordinary emoji an icon of the map can replace", ""]
        out += [f"- {c['screenId']} `{c['pointer']}`: {c['emoji']} -> {c['slot']} ({c['id']})" for c in b["candidates"]]
        out.append("")
    if b["unknown"]:
        out += ["## Ids not in the library (check or replace)", ""]
        out += [f"- {u['screenId']} `{u['pointer']}`: {u['id']}" for u in b["unknown"]]
        out.append("")
    if b.get("meaningMismatch"):
        out += ["## Icons that mean something else than their label", ""]
        out += [f"- {u['screenId']} `{u['pointer']}`: icon {u['id']} means {u['slot']}, the label says {', '.join(u['says'])}"
                for u in b["meaningMismatch"]]
        out.append("")
    if b["fallbackMismatch"]:
        out += ["## Fallback differs from the pack's emoji", ""]
        out += [f"- {u['screenId']} `{u['pointer']}`: {u['fallback']} (pack: {u['expected']})" for u in b["fallbackMismatch"]]
        out.append("")
    out += ["## Rules", ""] + [f"- {r}" for r in b["rules"]]
    return "\n".join(out) + "\n"


def client_document(root: str, snap: Snapshot, library_file: str | None = None) -> dict:
    """What the Studio client needs: the library, cached previews, usage, the slot vocabulary, and the emoji
    library's catalog and pick for the screens when they were loaded (emoji_catalog)."""
    from . import emoji_catalog
    try:
        lib = load_library(root)
        error = None
    except EmojiError as err:
        lib, error = empty_library(), err.to_json()
    token, env = token_from_env()
    try:
        base = resolver_url()
    except EmojiError:
        base = None
    return {"library": lib, "previews": previews(root), "usage": usage(snap), "vocabulary": vocabulary(),
            "suggestions": suggest_icons(snap, lib) if not error else [], "tokenEnv": env if token else None,
            "missing": missing_ids(snap, lib) if not error else [],
            "resolver": _Resolver(base).host if base else None, "error": error,
            "libraryFile": bool(library_file), **emoji_catalog.client_fields(root, snap, lib)}


def snapshot_block(snap: Snapshot, budget: int = 1_500_000, previews_of: str = "used",
                   library_file: str | None = None) -> dict | None:
    """The library for the offline artifact: ids, icons, usage, and pictures inlined as data: URLs
    (images only, within `budget` bytes). previews_of="used": the bot's icons and the emoji its
    screens use; "all": every emoji of every imported pack (for a public demo of the packs).
    With the emoji library's catalog (cached by the Studio, or `library_file`, the offline export) the
    block also carries it and a pick for the screens, so the page filters and picks without network."""
    import base64
    from . import emoji_catalog
    if not snap.root:
        return None
    try:
        lib = load_library(snap.root) if has_library(snap.root) else None
    except EmojiError:
        return None
    extra = emoji_catalog.snapshot_fields(snap, lib or empty_library(), library_file)
    if lib is None:
        if not extra:
            return None
        lib = empty_library()
    used = usage(snap)
    files = previews(snap.root)
    wanted = list(dict.fromkeys([i.get("id") for i in (lib.get("icons") or {}).values()] + [u["id"] for u in used]))
    if previews_of == "all":
        wanted += [e.get("id") for pack in (lib.get("packs") or {}).values() for e in (pack.get("emoji") or [])
                   if isinstance(e, dict) and e.get("id") not in wanted]
    inlined: dict[str, str] = {}
    mime = {"webp": "image/webp", "png": "image/png", "jpg": "image/jpeg"}
    for cid in wanted:
        name = files.get(cid)
        ext = name.rsplit(".", 1)[-1] if name else ""
        if ext not in mime:
            continue
        with open(os.path.join(snap.root, *CACHE.split("/"), name), "rb") as fh:
            data = base64.b64encode(fh.read()).decode("ascii")
        if len(data) > budget:
            break
        budget -= len(data)
        inlined[cid] = f"data:{mime[ext]};base64,{data}"
    return {"library": lib, "previews": inlined, "usage": used, "vocabulary": [], "suggestions": [], "tokenEnv": None,
            **extra}
