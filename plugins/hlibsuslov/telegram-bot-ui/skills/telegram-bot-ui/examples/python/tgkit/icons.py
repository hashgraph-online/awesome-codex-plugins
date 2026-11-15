"""One icon system for buttons AND text (custom emoji, Bot API 6.2 / 9.4 / 10.3).

* Buttons: `icon_custom_emoji_id` shows the icon before the label; the label itself
  carries no emoji then (no double icon).
* Text: `<tg-emoji emoji-id="…">⚙️</tg-emoji>` in regular HTML (or a custom_emoji entity,
  or `![⚙️](tg://emoji?id=…)` in MarkdownV2) uses the SAME id, so a screen title and its
  button speak one visual language. Rich Messages use RichTextCustomEmoji nodes, the same
  `<tg-emoji>` tag in rich HTML, or `![⚙️](tg://emoji?id=…)` in rich Markdown.
* Eligibility (API, verified 2026-11-15, Bot API 10.4): custom emoji on buttons / in text
  "can only be used by bots that purchased additional usernames on Fragment or in the
  messages directly sent by the bot to private, group and supergroup chats if the owner of
  the bot has a Telegram Premium subscription."
  When not eligible (or the kill switch is off) everything degrades together to the Unicode
  fallback - never icons on some buttons and emoji on others.

v2 (backward compatible: `IconSystem(icons, enabled=..., unicode_fallback=...)`, `button`,
`text`, `title` behave as before):
  Eligibility + SendContext -> `for_context(ctx)` view; `prepare(method, params)` decorates
  or strips one whole request (all-or-nothing per message); `send(...)` retries ONCE without
  custom emoji when Telegram rejects them and flips a shared kill switch; transforms
  `apply_*` / `strip_*` for keyboards, HTML, MarkdownV2, entities and rich messages;
  `resolve_icon_map` (sticker sets -> slot map, never invents ids); `verify_ids` (batches of
  200 for getCustomEmojiStickers); `decorate_post` for channel posts.
"""
from __future__ import annotations

import copy
import html
import json
import os
import re
import unicodedata
from dataclasses import dataclass, field, replace
from typing import Any, Callable, Iterable, Iterator

from .errors import TelegramError
from .text import escape_markdown_v2, utf16_len

# ---------------------------------------------------------------------------
# Emoji clusters and matching keys
# ---------------------------------------------------------------------------

VS16, VS15, ZWJ, KEYCAP = "️", "︎", "‍", "⃣"
_EXTRA_SYMBOLS = {0x00A9, 0x00AE, 0x203C, 0x2049, 0x2122, 0x2139, 0x3030, 0x303D, 0x3297, 0x3299,
                  0x20BF, 0x2022, 0x2934, 0x2935}


def _pictographic(ch: str) -> bool:
    cp = ord(ch)
    return (0x1F000 <= cp <= 0x1FAFF or 0x2600 <= cp <= 0x27BF or 0x2190 <= cp <= 0x21FF
            or 0x2300 <= cp <= 0x23FF or 0x2B00 <= cp <= 0x2BFF or 0x25A0 <= cp <= 0x25FF
            or cp in _EXTRA_SYMBOLS)


def _regional(ch: str) -> bool:
    return 0x1F1E6 <= ord(ch) <= 0x1F1FF


def iter_clusters(text: str) -> Iterator[tuple[int, int, str]]:
    """Yield (start, end, cluster) for every emoji cluster (Python indexes).

    A cluster = base + variation selectors / skin tones / keycap / tags, joined by ZWJ to
    further pictographs; regional-indicator pairs are one flag. Text outside clusters is
    never touched, so '⚙' inside '🧑‍⚙️'-like sequences is not matched on its own.
    """
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        start = i
        if ch in "0123456789#*" and i + 1 < n and (text[i + 1] == KEYCAP or
                                                   (text[i + 1] == VS16 and i + 2 < n and text[i + 2] == KEYCAP)):
            i += 3 if text[i + 1] == VS16 else 2
            yield start, i, text[start:i]
            continue
        if _regional(ch) and i + 1 < n and _regional(text[i + 1]):
            yield start, i + 2, text[start:i + 2]
            i += 2
            continue
        if not _pictographic(ch):
            i += 1
            continue
        i += 1
        while i < n:
            c = text[i]
            cp = ord(c)
            if c in (VS16, VS15, KEYCAP) or 0x1F3FB <= cp <= 0x1F3FF or 0xE0020 <= cp <= 0xE007F:
                i += 1
            elif c == ZWJ and i + 1 < n and _pictographic(text[i + 1]):
                i += 2
            else:
                break
        yield start, i, text[start:i]


def emoji_key(e: str) -> str:
    """Matching key: NFC, variation selectors removed ('⚙' == '⚙️')."""
    return unicodedata.normalize("NFC", e.replace(VS16, "").replace(VS15, ""))


def _leading_cluster(label: str) -> tuple[str, str] | None:
    """('⚙️', 'Settings') for '⚙️ Settings'; None when the label does not start with an emoji."""
    s = label.lstrip()
    for start, end, cl in iter_clusters(s):
        if start == 0:
            return cl, s[end:].lstrip()
        break
    return None


# ---------------------------------------------------------------------------
# Eligibility
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SendContext:
    """Where ONE message goes and who sends it.

    chat_type: private | group | supergroup | channel.
    business:  sent with business_connection_id (on behalf of a business account).
    inline:    an inline-mode result / inline_message_id edit (the user sends it via the bot).
    """
    chat_type: str = "private"
    business: bool = False
    inline: bool = False

    @classmethod
    def channel(cls) -> "SendContext":
        return cls("channel")

    @property
    def direct(self) -> bool:
        return not (self.business or self.inline)


@dataclass(frozen=True)
class Eligibility:
    """Which route the bot has. API wording (both button classes and Formatting options):
    Fragment usernames -> no chat restriction is stated; owner Premium -> only messages
    'directly sent by the bot to private, group and supergroup chats'.

    Reading of 'directly sent by the bot' (conservative, verified 2026-11-15): business
    sends (on behalf of a user) and inline results (sent by the user via the bot) are NOT
    covered by the Premium route; channels are not listed, so not covered either.
    """
    fragment_usernames: bool = False
    owner_premium: bool = False

    def route(self, ctx: SendContext) -> str | None:
        if self.fragment_usernames:
            return "fragment"
        if self.owner_premium and ctx.direct and ctx.chat_type in ("private", "group", "supergroup"):
            return "owner_premium"
        return None

    def explain(self, ctx: SendContext) -> str:
        r = self.route(ctx)
        if r == "fragment":
            return "eligible: bot has Fragment usernames"
        if r == "owner_premium":
            return f"eligible: owner Premium covers a {ctx.chat_type} message sent directly by the bot"
        if self.owner_premium:
            why = "business send" if ctx.business else "inline result" if ctx.inline else f"{ctx.chat_type} chat"
            return f"not eligible: owner Premium does not cover a {why}; Fragment usernames would"
        return "not eligible: no Fragment usernames and owner Premium not declared"


# Telegram does not document the exact error text for a refused custom emoji. These hints
# are matched (lower-case) only on a 400 for a request that actually carried custom emoji,
# and only one retry follows. Add the description you observe in your logs.
CUSTOM_EMOJI_ERROR_HINTS = ["custom emoji", "custom_emoji", "emoji", "icon_custom_emoji_id", "premium", "fragment"]
_NOT_EMOJI_HINTS = ("can't parse entities", "message is not modified", "too long")


def is_custom_emoji_rejection(err: TelegramError) -> bool:
    d = err.description.lower()
    return (err.error_code == 400 and not any(h in d for h in _NOT_EMOJI_HINTS)
            and any(h in d for h in CUSTOM_EMOJI_ERROR_HINTS))


# ---------------------------------------------------------------------------
# Matching map (unicode -> slot)
# ---------------------------------------------------------------------------

_VOCAB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))), "data", "emoji", "slots.json")


def load_vocabulary(path: str | None = None) -> dict[str, dict[str, Any]]:
    """data/emoji/slots.json -> {slot: {"group", "unicode", "label", "use", "note"}}."""
    with open(path or _VOCAB_PATH, encoding="utf-8") as fh:
        return json.load(fh)["slots"]


class EmojiMap:
    """Unicode key -> slot, built from an icon map (+ the vocabulary's accepted equivalents)."""

    def __init__(self, icons: dict[str, dict[str, Any]], vocabulary: dict[str, dict[str, Any]] | None = None):
        self.icons = {s: i for s, i in icons.items() if i.get("id")}
        self.keys: dict[str, str] = {}
        self.conflicts: list[str] = []
        # Pass 1: each slot's own fallback (the sticker's emoji) and explicit aliases win;
        # pass 2: the vocabulary's other accepted equivalents fill in where still free.
        primary = {slot: [icon.get("fallback") or ""] + list(icon.get("aliases") or []) for slot, icon in self.icons.items()}
        extra = {slot: (vocabulary[slot]["unicode"] if vocabulary and slot in vocabulary else []) for slot in self.icons}
        for cands_by_slot, report in ((primary, True), (extra, False)):
            for slot, cands in cands_by_slot.items():
                for u in cands:
                    k = emoji_key(u)
                    if not k:
                        continue
                    if k in self.keys and self.keys[k] != slot:
                        if report:
                            self.conflicts.append(f"{u} accepted by {self.keys[k]} and {slot}; kept {self.keys[k]}")
                        continue
                    self.keys[k] = slot
        self.by_id = {i["id"]: (s, i) for s, i in self.icons.items()}

    def slot_for(self, cluster: str) -> str | None:
        return self.keys.get(emoji_key(cluster))

    def fallback_for_id(self, cid: str) -> str:
        hit = self.by_id.get(cid)
        return (hit[1].get("fallback") or "") if hit else ""


def _report() -> dict[str, Any]:
    return {"replaced": 0, "slots": [], "unmapped": [], "protected": 0, "warnings": []}


def _merge(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    a["replaced"] += b["replaced"]
    a["slots"] += b["slots"]
    a["unmapped"] += b["unmapped"]
    a["protected"] += b["protected"]
    a["warnings"] += b["warnings"]
    return a


def _replace_clusters(s: str, emap: EmojiMap, render: Callable[[str, dict[str, Any], str], str],
                      rep: dict[str, Any]) -> str:
    out, last = [], 0
    for start, end, cl in iter_clusters(s):
        slot = emap.slot_for(cl)
        if not slot:
            rep["unmapped"].append(cl)
            continue
        out.append(s[last:start])
        out.append(render(slot, emap.icons[slot], cl))
        rep["replaced"] += 1
        rep["slots"].append(slot)
        last = end
    out.append(s[last:])
    return "".join(out)


def _fb(icon: dict[str, Any], original: str) -> str:
    # Official recommendation: the alternative emoji is the sticker's own `emoji` field,
    # which resolve_icon_map stores as `fallback`.
    return icon.get("fallback") or original


# ---- regular HTML (and rich HTML) -------------------------------------------

_TAG = re.compile(r"<[^>]+>")
_PROTECTED_TAGS = {"a", "code", "pre", "tg-emoji", "tg-time", "tg-math", "tg-button"}


def apply_html(text: str, emap: EmojiMap) -> tuple[str, dict[str, Any]]:
    """Unicode emoji -> <tg-emoji>, outside <a>/<code>/<pre>/existing <tg-emoji> (API:
    custom_emoji cannot be nested in links or code). `tg-button` texts in rich HTML are
    left alone here; build rich buttons with IconSystem.rich()."""
    rep = _report()
    depth: dict[str, int] = {}
    out, pos = [], 0
    render = lambda slot, icon, cl: f'<tg-emoji emoji-id="{icon["id"]}">{html.escape(_fb(icon, cl))}</tg-emoji>'
    for m in _TAG.finditer(text):
        out.append(_html_segment(text[pos:m.start()], emap, render, rep, depth))
        tag = m.group(0)
        name = re.match(r"</?\s*([a-zA-Z0-9-]+)", tag)
        if name:
            n = name.group(1).lower()
            if n in _PROTECTED_TAGS and not tag.endswith("/>"):
                depth[n] = depth.get(n, 0) + (-1 if tag.startswith("</") else 1)
        out.append(tag)
        pos = m.end()
    out.append(_html_segment(text[pos:], emap, render, rep, depth))
    return "".join(out), rep


def _html_segment(seg, emap, render, rep, depth):
    if any(v > 0 for v in depth.values()):
        rep["protected"] += sum(1 for _ in iter_clusters(seg))
        return seg
    return _replace_clusters(seg, emap, render, rep)


_TG_EMOJI = re.compile(r'<tg-emoji\s+emoji-id="\d+"\s*>(.*?)</tg-emoji>', re.S)
_IMG_EMOJI = re.compile(r'<img\s+src="tg://emoji\?id=\d+"\s+alt="([^"]*)"\s*/?>')


def strip_html(text: str) -> str:
    return _IMG_EMOJI.sub(r"\1", _TG_EMOJI.sub(r"\1", text))


# ---- MarkdownV2 (and rich Markdown) -----------------------------------------

def apply_markdown(text: str, emap: EmojiMap, *, v2: bool = True) -> tuple[str, dict[str, Any]]:
    """Unicode emoji -> ![e](tg://emoji?id=…), skipping code spans, ``` blocks, links and
    existing custom emoji. v2=False: rich Markdown (alt text not MarkdownV2-escaped)."""
    rep = _report()
    out: list[str] = []
    buf: list[str] = []
    render = lambda slot, icon, cl: (f"![{escape_markdown_v2(_fb(icon, cl)) if v2 else _fb(icon, cl)}]"
                                     f"(tg://emoji?id={icon['id']})")

    def flush():
        if buf:
            out.append(_replace_clusters("".join(buf), emap, render, rep))
            buf.clear()

    def protect(chunk):
        flush()
        rep["protected"] += sum(1 for _ in iter_clusters(chunk))
        out.append(chunk)

    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c == "\\" and i + 1 < n:
            buf.append(text[i:i + 2]); i += 2; continue
        if text.startswith("```", i):
            j = text.find("```", i + 3)
            j = n if j < 0 else j + 3
            protect(text[i:j]); i = j; continue
        if c == "`":
            j = text.find("`", i + 1)
            j = n if j < 0 else j + 1
            protect(text[i:j]); i = j; continue
        if c == "[" or text.startswith("![", i):
            j = _link_end(text, i + (2 if c == "!" else 1))
            if j:
                protect(text[i:j]); i = j; continue
        buf.append(c); i += 1
    flush()
    return "".join(out), rep


def _link_end(text: str, i: int) -> int | None:
    """End index of '[…](…)' whose label starts at i, honouring backslash escapes."""
    n = len(text)
    while i < n and text[i] != "]":
        i += 2 if text[i] == "\\" else 1
    if i + 1 >= n or text[i + 1] != "(":
        return None
    i += 2
    while i < n and text[i] != ")":
        i += 2 if text[i] == "\\" else 1
    return i + 1 if i < n else None


_MD_EMOJI = re.compile(r"!\[((?:\\.|[^\]\\])*)\]\(tg://emoji\?id=\d+\)")


def strip_markdown(text: str) -> str:
    return _MD_EMOJI.sub(r"\1", text)


apply_markdown_v2 = apply_markdown
strip_markdown_v2 = strip_markdown


# ---- MessageEntity lists ----------------------------------------------------

_CONTAINERS = {"bold", "italic", "underline", "strikethrough", "spoiler", "blockquote", "expandable_blockquote"}


def apply_entities(text: str, entities: list[dict[str, Any]] | None, emap: EmojiMap
                   ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Add custom_emoji entities (UTF-16 offsets) over emoji in `text`; the text itself is
    unchanged (its emoji is the alternative). Emoji inside entities that may not contain
    others (code, pre, links, mentions, existing custom_emoji…) are skipped (API nesting rule)."""
    rep = _report()
    ents = [dict(e) for e in entities or []]
    blocked = [(e["offset"], e["offset"] + e["length"]) for e in ents if e["type"] not in _CONTAINERS]
    for start, end, cl in iter_clusters(text):
        slot = emap.slot_for(cl)
        if not slot:
            rep["unmapped"].append(cl)
            continue
        off, ln = utf16_len(text[:start]), utf16_len(cl)
        if any(a < off + ln and off < b for a, b in blocked):
            rep["protected"] += 1
            continue
        ents.append({"type": "custom_emoji", "offset": off, "length": ln, "custom_emoji_id": emap.icons[slot]["id"]})
        rep["replaced"] += 1
        rep["slots"].append(slot)
    ents.sort(key=lambda e: (e["offset"], -e["length"]))
    return ents, rep


def strip_entities(entities: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    return [e for e in entities or [] if e.get("type") != "custom_emoji"]


# ---- Rich messages (RichText / InputRichBlock) ------------------------------

_RICH_RECURSE = {"bold", "italic", "underline", "strikethrough", "spoiler", "marked", "subscript", "superscript"}
_RICH_SKIP_BLOCKS = {"pre", "mathematical_expression", "anchor", "divider"}


def apply_rich_text(rt: Any, emap: EmojiMap, rep: dict[str, Any]) -> Any:
    if isinstance(rt, str):
        parts: list[Any] = []
        last = 0
        for start, end, cl in iter_clusters(rt):
            slot = emap.slot_for(cl)
            if not slot:
                rep["unmapped"].append(cl)
                continue
            if rt[last:start]:
                parts.append(rt[last:start])
            icon = emap.icons[slot]
            parts.append({"type": "custom_emoji", "custom_emoji_id": icon["id"], "alternative_text": _fb(icon, cl)})
            rep["replaced"] += 1
            rep["slots"].append(slot)
            last = end
        if not parts:
            return rt
        if rt[last:]:
            parts.append(rt[last:])
        return parts
    if isinstance(rt, list):
        out: list[Any] = []
        for x in rt:
            y = apply_rich_text(x, emap, rep)
            out.extend(y if isinstance(y, list) and not isinstance(x, list) else [y])
        return out
    if isinstance(rt, dict):
        t = rt.get("type")
        if t in _RICH_RECURSE:
            return {**rt, "text": apply_rich_text(rt.get("text"), emap, rep)}
        if t == "button" and isinstance(rt.get("button"), dict):   # RichTextButton
            b = rt["button"]
            return {**rt, "button": {**b, "text": apply_rich_text(b.get("text"), emap, rep)}}
        rep["protected"] += 1 if t not in ("custom_emoji",) and _has_emoji(rt) else 0
        return rt     # code, url, mention, date_time, custom_emoji, math… stay as they are
    return rt


def _has_emoji(x: Any) -> bool:
    return any(True for _ in iter_clusters(json.dumps(x, ensure_ascii=False)))


def _walk_blocks(node: Any, emap: EmojiMap, rep: dict[str, Any]) -> Any:
    if isinstance(node, list):
        return [_walk_blocks(x, emap, rep) for x in node]
    if not isinstance(node, dict):
        return node
    if node.get("type") in _RICH_SKIP_BLOCKS:
        return node
    out = {}
    for k, v in node.items():
        if k in ("text", "credit", "summary") and not (isinstance(v, dict) and "type" not in v):
            out[k] = apply_rich_text(v, emap, rep)
        elif k in ("url", "callback_data", "copy_text", "media", "html", "markdown"):
            out[k] = v
        else:
            out[k] = _walk_blocks(v, emap, rep)
    return out


def apply_rich_message(rm: dict[str, Any], emap: EmojiMap) -> tuple[dict[str, Any], dict[str, Any]]:
    """InputRichMessage: exactly one of blocks / html / markdown (API)."""
    rep = _report()
    if "blocks" in rm:
        return {**rm, "blocks": _walk_blocks(rm["blocks"], emap, rep)}, rep
    if "html" in rm:
        h, r = apply_html(rm["html"], emap)
        return {**rm, "html": h}, _merge(rep, r)
    if "markdown" in rm:
        m, r = apply_markdown(rm["markdown"], emap, v2=False)
        return {**rm, "markdown": m}, _merge(rep, r)
    return rm, rep


def strip_rich_text(rt: Any) -> Any:
    if isinstance(rt, list):
        items = [strip_rich_text(x) for x in rt]
        merged: list[Any] = []
        for x in items:
            if isinstance(x, str) and merged and isinstance(merged[-1], str):
                merged[-1] += x
            else:
                merged.append(x)
        return merged[0] if len(merged) == 1 and isinstance(merged[0], str) else merged
    if isinstance(rt, dict):
        if rt.get("type") == "custom_emoji":
            return rt.get("alternative_text", "")
        return {k: strip_rich_text(v) for k, v in rt.items()}
    return rt


def strip_rich_message(rm: dict[str, Any]) -> dict[str, Any]:
    if "blocks" in rm:
        return {**rm, "blocks": strip_rich_text(rm["blocks"])}
    if "html" in rm:
        return {**rm, "html": strip_html(rm["html"])}
    if "markdown" in rm:
        return {**rm, "markdown": strip_markdown(rm["markdown"])}
    return rm


# ---- keyboards --------------------------------------------------------------

def apply_keyboard(markup: dict[str, Any], emap: EmojiMap) -> tuple[dict[str, Any], dict[str, Any]]:
    """Leading Unicode emoji in labels -> icon_custom_emoji_id; never a double icon."""
    rep = _report()
    key = "inline_keyboard" if "inline_keyboard" in markup else "keyboard" if "keyboard" in markup else None
    if not key:
        return markup, rep
    rows = []
    for row in markup[key]:
        new_row = []
        for b in row:
            b = {"text": b} if isinstance(b, str) else dict(b)
            lead = _leading_cluster(b.get("text", ""))
            if b.get("icon_custom_emoji_id"):
                if lead and lead[1]:
                    b["text"] = lead[1]           # icon already set: drop the duplicate emoji
                    rep["warnings"].append(f"removed duplicate emoji {lead[0]} next to an icon")
            elif lead:
                slot = emap.slot_for(lead[0])
                if not slot:
                    rep["unmapped"].append(lead[0])
                elif not lead[1]:
                    rep["warnings"].append(f"emoji-only label {lead[0]!r} kept as text: a label must stand alone")
                else:
                    b["icon_custom_emoji_id"] = emap.icons[slot]["id"]
                    b["text"] = lead[1]
                    rep["replaced"] += 1
                    rep["slots"].append(slot)
            new_row.append(b)
        rows.append(new_row)
    if rep["replaced"] and rep["unmapped"]:
        rep["warnings"].append(f"mixed keyboard: {len(rep['unmapped'])} label(s) keep Unicode emoji "
                               f"({' '.join(rep['unmapped'])}) next to custom icons - map those slots or drop the emoji")
    return {**markup, key: rows}, rep


def strip_keyboard(markup: dict[str, Any], emap: EmojiMap | None = None, *, unicode_fallback: bool = True) -> dict[str, Any]:
    key = "inline_keyboard" if "inline_keyboard" in markup else "keyboard" if "keyboard" in markup else None
    if not key:
        return markup
    rows = []
    for row in markup[key]:
        new_row = []
        for b in row:
            if isinstance(b, dict) and b.get("icon_custom_emoji_id"):
                b = dict(b)
                cid = b.pop("icon_custom_emoji_id")
                fb = emap.fallback_for_id(cid) if emap else ""
                if unicode_fallback and fb and not _leading_cluster(b.get("text", "")):
                    b["text"] = f"{fb} {b['text']}"
            new_row.append(b)
        rows.append(new_row)
    return {**markup, key: rows}


# ---------------------------------------------------------------------------
# Whole requests
# ---------------------------------------------------------------------------

def uses_custom_emoji(params: Any) -> bool:
    s = json.dumps(params, ensure_ascii=False)
    return ('"icon_custom_emoji_id"' in s or '"custom_emoji"' in s or "tg://emoji?id=" in s or "<tg-emoji" in s)


def message_has_custom_emoji(message: dict[str, Any]) -> bool:
    """True if a returned Message still carries custom emoji (entities, rich nodes, buttons)."""
    s = json.dumps(message, ensure_ascii=False)
    return '"custom_emoji"' in s or '"icon_custom_emoji_id"' in s


def silently_stripped(params: dict[str, Any], message: Any) -> bool:
    """The request carried custom emoji, the returned Message is a full echo (has its text,
    caption, rich message or keyboard) and none survived: Telegram stripped them without an
    error, which is what it does for an ineligible bot (live Bot API, 2026-08-05)."""
    if not (isinstance(message, dict) and uses_custom_emoji(params)):
        return False
    if not any(k in message for k in ("text", "caption", "rich_message", "reply_markup")):
        return False                       # bare ack (test doubles, some edits): can't tell
    return not message_has_custom_emoji(message)


def _text_fields(params: dict[str, Any]) -> Iterable[tuple[str, str, str]]:
    """(text key, parse_mode key, entities key) triples present in a send/edit request."""
    for t, pm, ent in (("text", "parse_mode", "entities"), ("caption", "parse_mode", "caption_entities"),
                       ("question", "question_parse_mode", "question_entities")):
        if t in params and isinstance(params[t], str):
            yield t, pm, ent


def _apply_text_field(p: dict[str, Any], t: str, pm: str, ent: str, emap: EmojiMap, rep: dict[str, Any]) -> None:
    mode = (p.get(pm) or "").lower()
    if mode == "html":
        p[t], r = apply_html(p[t], emap)
    elif mode == "markdownv2":
        p[t], r = apply_markdown(p[t], emap)
    elif mode == "markdown":
        r = _report()
        r["warnings"].append("legacy Markdown cannot express custom emoji (API); switch to HTML or MarkdownV2")
    else:
        ents, r = apply_entities(p[t], p.get(ent), emap)
        if ents:
            p[ent] = ents
    _merge(rep, r)


def _strip_text_field(p: dict[str, Any], t: str, pm: str, ent: str) -> None:
    mode = (p.get(pm) or "").lower()
    if mode == "html":
        p[t] = strip_html(p[t])
    elif mode == "markdownv2":
        p[t] = strip_markdown(p[t])
    if ent in p:
        p[ent] = strip_entities(p[ent])
        if not p[ent]:
            del p[ent]


def apply_request(method: str, params: dict[str, Any], emap: EmojiMap) -> tuple[dict[str, Any], dict[str, Any]]:
    """Decorate one Bot API request: text/caption/poll question/options, reply_markup,
    rich_message, inline results' input_message_content. Returns (params, report)."""
    p = copy.deepcopy(params)
    rep = _report()
    for t, pm, ent in _text_fields(p):
        _apply_text_field(p, t, pm, ent, emap, rep)
    for opt in p.get("options") or []:            # InputPollOption: only custom emoji entities allowed
        if isinstance(opt, dict) and isinstance(opt.get("text"), str):
            _apply_text_field(opt, "text", "text_parse_mode", "text_entities", emap, rep)
    if isinstance(p.get("rich_message"), dict):
        p["rich_message"], r = apply_rich_message(p["rich_message"], emap)
        _merge(rep, r)
    if isinstance(p.get("reply_markup"), dict):
        p["reply_markup"], r = apply_keyboard(p["reply_markup"], emap)
        _merge(rep, r)
    for res in p.get("results") or []:           # answerInlineQuery
        if isinstance(res, dict):
            if isinstance(res.get("input_message_content"), dict):
                res["input_message_content"], r = apply_request("", res["input_message_content"], emap)
                _merge(rep, r)
            if isinstance(res.get("reply_markup"), dict):
                res["reply_markup"], r = apply_keyboard(res["reply_markup"], emap)
                _merge(rep, r)
    return p, rep


def strip_request(params: dict[str, Any], emap: EmojiMap | None = None, *, unicode_fallback: bool = True) -> dict[str, Any]:
    """Remove every custom emoji from one request (the reverse of apply_request)."""
    p = copy.deepcopy(params)
    for t, pm, ent in _text_fields(p):
        _strip_text_field(p, t, pm, ent)
    for opt in p.get("options") or []:
        if isinstance(opt, dict):
            _strip_text_field(opt, "text", "text_parse_mode", "text_entities")
    if isinstance(p.get("rich_message"), dict):
        p["rich_message"] = strip_rich_message(p["rich_message"])
    if isinstance(p.get("reply_markup"), dict):
        p["reply_markup"] = strip_keyboard(p["reply_markup"], emap, unicode_fallback=unicode_fallback)
    for res in p.get("results") or []:
        if isinstance(res, dict):
            if isinstance(res.get("input_message_content"), dict):
                res["input_message_content"] = strip_request(res["input_message_content"], emap, unicode_fallback=unicode_fallback)
            if isinstance(res.get("reply_markup"), dict):
                res["reply_markup"] = strip_keyboard(res["reply_markup"], emap, unicode_fallback=unicode_fallback)
    return p


def count_custom_emoji(params: Any) -> dict[str, int]:
    s = json.dumps(params, ensure_ascii=False)
    return {"buttons": s.count('"icon_custom_emoji_id"'),
            "text": s.count("<tg-emoji") + s.count("tg://emoji?id=") + s.count('"type": "custom_emoji"')}


# Density heuristics of this skill (not API limits).
DENSITY = {"screen_text": 3, "post_text": 8, "per_line": 1}


def density_warnings(params: dict[str, Any], *, post: bool = False) -> list[str]:
    c = count_custom_emoji(params)
    limit = DENSITY["post_text"] if post else DENSITY["screen_text"]
    out = []
    if c["text"] > limit:
        out.append(f"{c['text']} custom emoji in one {'post' if post else 'screen'} text (heuristic limit {limit})")
    text = params.get("text") or params.get("caption") or ""
    for line in text.split("\n"):
        n = line.count("<tg-emoji") + line.count("tg://emoji?id=")
        if n > DENSITY["per_line"]:
            out.append(f"{n} custom emoji on one line: {strip_html(strip_markdown(line))[:40]!r}")
    return out


# ---------------------------------------------------------------------------
# IconSystem
# ---------------------------------------------------------------------------

@dataclass
class IconSystem:
    icons: dict[str, dict[str, Any]]     # slot -> {"id", "fallback", "set", ...}
    enabled: bool = True                  # owner Premium / Fragment eligibility, env kill switch
    unicode_fallback: bool = True         # False = label-only when custom emoji are off
    eligibility: Eligibility | None = None
    vocabulary: dict[str, dict[str, Any]] | None = None
    log: Callable[[str], None] | None = None
    strict: bool = False                  # True: a message mixing custom icons and unmapped Unicode emoji is stripped
    _state: dict[str, Any] = field(default_factory=lambda: {"killed": False, "reason": ""}, repr=False)

    # ---- state ----
    @property
    def active(self) -> bool:
        return self.enabled and not self._state["killed"]

    @property
    def killed(self) -> bool:
        return self._state["killed"]

    def kill(self, reason: str) -> None:
        """Flip the shared kill switch (all views). Logged once."""
        if not self._state["killed"]:
            self._state.update(killed=True, reason=reason)
            if self.log:
                self.log(f"custom emoji disabled: {reason}")

    def reset_kill_switch(self) -> None:
        """Only after the owner confirms the route is back (Premium renewed, usernames bought)."""
        self._state.update(killed=False, reason="")

    def for_context(self, ctx: SendContext) -> "IconSystem":
        """A view for ONE message: on/off for the whole message, sharing the kill switch."""
        ok = self.enabled and (self.eligibility is None or self.eligibility.route(ctx) is not None)
        return replace(self, enabled=ok, _state=self._state)

    @property
    def emap(self) -> EmojiMap:
        return EmojiMap(self.icons, self.vocabulary)

    # ---- single icons ----
    def _icon(self, slot: str | None) -> dict[str, Any] | None:
        icon = self.icons.get(slot or "")
        return icon if icon and (icon.get("id") or icon.get("fallback")) else None

    def _on(self, icon: dict[str, Any] | None) -> bool:
        return bool(icon and icon.get("id") and self.active)

    def _uncovered(self, icon: dict[str, Any]) -> bool:
        """Icons are on but this slot has no id: show nothing rather than a Unicode look-alike."""
        return self.active and not icon.get("id") and any(i.get("id") for i in self.icons.values())

    def button(self, text: str, slot: str | None = None, *, style: str | None = None, **action: Any) -> dict[str, Any]:
        b: dict[str, Any] = {"text": text, **action}
        icon = self._icon(slot)
        lead = _leading_cluster(text)
        if self._on(icon):
            b["icon_custom_emoji_id"] = icon["id"]
            if lead and lead[1]:
                b["text"] = lead[1]           # no double icon
        elif icon and self._uncovered(icon):
            pass                              # uncovered slot while icons are on: label only, no foreign style
        elif icon and self.unicode_fallback and icon.get("fallback") and not lead:
            b["text"] = f"{icon['fallback']} {text}"
        if style:
            b["style"] = style
        return b

    def text(self, slot: str) -> str:
        """Icon for regular-HTML message text (escape the rest of the text yourself)."""
        icon = self._icon(slot)
        if not icon:
            return ""
        fb = html.escape(icon.get("fallback") or "•")
        if self._on(icon):
            return f'<tg-emoji emoji-id="{icon["id"]}">{fb}</tg-emoji>'
        return fb if self.unicode_fallback and not self._uncovered(icon) else ""

    html = text

    def title(self, slot: str, title: str) -> str:
        prefix = self.text(slot)
        return f"<b>{prefix + ' ' if prefix else ''}{html.escape(title)}</b>"

    def md2(self, slot: str) -> str:
        """Icon for MarkdownV2 text."""
        icon = self._icon(slot)
        if not icon:
            return ""
        fb = escape_markdown_v2(icon.get("fallback") or "•")
        if self._on(icon):
            return f"![{fb}](tg://emoji?id={icon['id']})"
        return fb if self.unicode_fallback and not self._uncovered(icon) else ""

    def rich_markdown(self, slot: str) -> str:
        icon = self._icon(slot)
        if not icon:
            return ""
        fb = icon.get("fallback") or "•"
        if self._on(icon):
            return f"![{fb}](tg://emoji?id={icon['id']})"
        return fb if self.unicode_fallback and not self._uncovered(icon) else ""

    def rich(self, slot: str) -> Any:
        """RichTextCustomEmoji node for rich blocks (or the fallback string)."""
        icon = self._icon(slot)
        if not icon:
            return ""
        if self._on(icon):
            return {"type": "custom_emoji", "custom_emoji_id": icon["id"],
                    "alternative_text": icon.get("fallback") or "•"}
        return (icon.get("fallback") or "") if self.unicode_fallback and not self._uncovered(icon) else ""

    def rich_label(self, slot: str, label: str) -> Any:
        """Rich text 'icon + label' (headings, RichMessageButton text, table cells)."""
        r = self.rich(slot)
        if not r:
            return label
        return [r, f" {label}"] if isinstance(r, dict) else f"{r} {label}"

    def composer(self) -> "TextComposer":
        return TextComposer(self)

    # ---- whole messages ----
    def prepare(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        """All-or-nothing per message: decorate when active, strip every custom emoji when not."""
        if self.active:
            p, rep = apply_request(method, params, self.emap)
            if not (self.strict and rep["replaced"] and rep["unmapped"]):
                return p
        return strip_request(params, self.emap, unicode_fallback=self.unicode_fallback)

    def send(self, transport: Any, method: str, params: dict[str, Any], ctx: SendContext | None = None,
             *, decorate: bool = True) -> Any:
        """Send once; if Telegram refuses the custom emoji, flip the kill switch and retry ONCE
        without them. A second failure is raised. Never loops."""
        view = self.for_context(ctx) if ctx else self
        if decorate:
            p = view.prepare(method, params)
        else:
            p = params if view.active else strip_request(params, self.emap, unicode_fallback=self.unicode_fallback)
        try:
            sent = transport.call(method, p)
        except TelegramError as err:
            if not (uses_custom_emoji(p) and is_custom_emoji_rejection(err)):
                raise
            self.kill(f"{method}: {err.error_code} {err.description}")
            return transport.call(method, strip_request(p, self.emap, unicode_fallback=self.unicode_fallback))
        # An ineligible bot gets NO error: Telegram answers ok and strips the custom emoji
        # (live Bot API, 2026-08-05). Read the message back; a strip means the route is gone.
        if silently_stripped(p, sent):
            self.kill(f"{method}: custom emoji silently removed (owner Premium / Fragment missing?)")
        return sent


class TextComposer:
    """Plain text + MessageEntity list with correct UTF-16 offsets (no parse_mode needed)."""

    def __init__(self, icons: IconSystem):
        self.icons = icons
        self.parts: list[str] = []
        self.entities: list[dict[str, Any]] = []

    def _pos(self) -> int:
        return utf16_len("".join(self.parts))

    def add(self, s: str, *etypes: str) -> "TextComposer":
        off = self._pos()
        self.parts.append(s)
        for t in etypes:
            self.entities.append({"type": t, "offset": off, "length": utf16_len(s)})
        return self

    def icon(self, slot: str, space: bool = True) -> "TextComposer":
        icon = self.icons._icon(slot)
        if not icon:
            return self
        fb = icon.get("fallback") or ""
        if self.icons._on(icon):
            fb = fb or "•"
            self.entities.append({"type": "custom_emoji", "offset": self._pos(), "length": utf16_len(fb),
                                  "custom_emoji_id": icon["id"]})
        elif not self.icons.unicode_fallback or not fb or self.icons._uncovered(icon):
            return self
        self.parts.append(fb + (" " if space else ""))
        return self

    def build(self) -> tuple[str, list[dict[str, Any]]]:
        return "".join(self.parts), sorted(self.entities, key=lambda e: (e["offset"], -e["length"]))


# ---------------------------------------------------------------------------
# Resolving and verifying ids (never invented)
# ---------------------------------------------------------------------------

def resolve_icon_map(sticker_sets: list[dict[str, Any]], vocabulary: dict[str, dict[str, Any]],
                     slots: Iterable[str] | None = None, *, family: str | None = None
                     ) -> tuple[dict[str, Any], dict[str, Any]]:
    """Map slots to stickers of the given sets (primary first, then siblings for gaps).

    Ids come only from Sticker.custom_emoji_id; a slot without a matching sticker stays
    UNSET (listed in report["uncovered"]). One sticker serves one meaning: a second slot
    that would reuse it gets its next acceptable candidate or stays uncovered (conflict).
    """
    index: list[tuple[str, dict[str, dict[str, Any]]]] = []
    for st in sticker_sets:
        if st.get("sticker_type") not in (None, "custom_emoji"):
            raise ValueError(f"{st.get('name')}: not a custom emoji set")
        idx: dict[str, dict[str, Any]] = {}
        for s in st.get("stickers", []):
            if s.get("custom_emoji_id") and s.get("emoji"):
                idx.setdefault(emoji_key(s["emoji"]), s)
        index.append((st["name"], idx))
    wanted = list(slots) if slots is not None else list(vocabulary)
    icons: dict[str, Any] = {}
    used: dict[str, str] = {}
    uncovered, conflicts, unknown = [], [], []
    for slot in wanted:
        v = vocabulary.get(slot)
        if not v:
            unknown.append(slot)
            continue
        hit = None
        for set_name, idx in index:
            for u in v["unicode"]:
                s = idx.get(emoji_key(u))
                if s is None:
                    continue
                if s["custom_emoji_id"] in used:
                    conflicts.append(f"{slot}: {u} is already {used[s['custom_emoji_id']]} in {set_name}")
                    continue
                hit = (set_name, s)
                break
            if hit:
                break
        if not hit:
            uncovered.append(slot)
            continue
        set_name, s = hit
        used[s["custom_emoji_id"]] = slot
        icons[slot] = {"id": s["custom_emoji_id"], "set": s.get("set_name") or set_name,
                       "family": family or sticker_sets[0]["name"], "fallback": s["emoji"],
                       "animated": bool(s.get("is_animated") or s.get("is_video")),
                       "adaptive": bool(s.get("needs_repainting")), "label": v.get("label", "")}
    covered = len(icons)
    report = {"sets": [n for n, _ in index], "requested": len(wanted), "covered": covered,
              "coverage": round(covered / len(wanted), 3) if wanted else 0.0,
              "uncovered": uncovered, "conflicts": conflicts, "unknown_slots": unknown,
              "per_set": {n: sum(1 for i in icons.values() if i["set"] == n) for n, _ in index}}
    doc = {"bot": "", "source": "getStickerSet(" + ", ".join(n for n, _ in index) + ")", "icons": icons}
    return doc, report


def _vocab_keys(vocabulary: dict[str, dict[str, Any]]) -> dict[str, str]:
    """Unicode key -> slot; a slot's FIRST (preferred) emoji wins over other slots' alternates."""
    keys: dict[str, str] = {}
    for slot, v in vocabulary.items():
        if v["unicode"]:
            keys.setdefault(emoji_key(v["unicode"][0]), slot)
    for slot, v in vocabulary.items():
        for u in v["unicode"][1:]:
            keys.setdefault(emoji_key(u), slot)
    return keys


def slots_in(source: Any, vocabulary: dict[str, dict[str, Any]]) -> list[str]:
    """Slots implied by the Unicode emoji in texts/keyboards/payloads, most used first."""
    blob = source if isinstance(source, str) else json.dumps(source, ensure_ascii=False)
    keys = _vocab_keys(vocabulary)
    counts: dict[str, int] = {}
    for _, _, cl in iter_clusters(blob):
        slot = keys.get(emoji_key(cl))
        if slot:
            counts[slot] = counts.get(slot, 0) + 1
    return sorted(counts, key=lambda s: -counts[s])


def ids_from_message(message: dict[str, Any], vocabulary: dict[str, dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """Capture path: [{"id", "emoji", "suggested_slot"}] from custom_emoji entities of a
    message the owner sent to the bot (offsets are UTF-16 code units)."""
    msg = message.get("message") or message
    text = msg.get("text") or msg.get("caption") or ""
    units = text.encode("utf-16-le")
    keys = _vocab_keys(vocabulary) if vocabulary else {}
    out = []
    for e in msg.get("entities") or msg.get("caption_entities") or []:
        if e.get("type") == "custom_emoji" and e.get("custom_emoji_id"):
            emoji = units[2 * e["offset"]: 2 * (e["offset"] + e["length"])].decode("utf-16-le")
            out.append({"id": e["custom_emoji_id"], "emoji": emoji, "suggested_slot": keys.get(emoji_key(emoji))})
    return out


GET_CUSTOM_EMOJI_MAX = 200   # API: "At most 200 custom emoji identifiers can be specified."


def batched(ids: list[str], size: int = GET_CUSTOM_EMOJI_MAX) -> list[list[str]]:
    return [ids[i:i + size] for i in range(0, len(ids), size)]


def verify_ids(transport: Any, ids: Iterable[str]) -> tuple[dict[str, dict[str, Any]], list[str]]:
    """getCustomEmojiStickers in batches of <= 200 -> ({id: Sticker}, [missing ids])."""
    uniq = list(dict.fromkeys(str(i) for i in ids if i))
    found: dict[str, dict[str, Any]] = {}
    for chunk in batched(uniq):
        for s in transport.call("getCustomEmojiStickers", {"custom_emoji_ids": chunk}) or []:
            if s.get("custom_emoji_id"):
                found[s["custom_emoji_id"]] = s
    return found, [i for i in uniq if i not in found]


# ---------------------------------------------------------------------------
# Posts
# ---------------------------------------------------------------------------

POST_ROLES = {"headline": "headline", "section": "section", "bullet": "bullet", "cta": "cta",
              "done": "check_item", "fail": "cross_item", "note": "callout"}


def decorate_post(post: dict[str, Any], icons: IconSystem, *, roles: dict[str, str] | None = None,
                  max_accents: int = DENSITY["post_text"]) -> dict[str, Any]:
    """Neutral post model -> regular-HTML sendMessage params with accents from ONE family.

    post = {"headline": str, "lead": str?, "sections": [{"title": str, "bullets": [str],
            "body": str?, "status": "done"|"fail"?}], "cta": {"text": str, "url": str}?}
    Accents: one before the headline, one per section title, bullets only in the first list,
    one before the CTA; capped at `max_accents` (heuristic). Pass a view from
    `icons.for_context(SendContext.channel())` - channels need the Fragment route (API).
    """
    r = {**POST_ROLES, **(roles or {})}
    budget = [max_accents]

    def acc(role: str) -> str:
        if budget[0] <= 0:
            return ""
        a = icons.text(r[role])
        if a:
            budget[0] -= 1
            return a + " "
        return ""

    e = html.escape
    lines = [f"<b>{acc('headline')}{e(post['headline'])}</b>"]
    if post.get("lead"):
        lines += ["", e(post["lead"])]
    for n, sec in enumerate(post.get("sections") or []):
        role = {"done": "done", "fail": "fail"}.get(sec.get("status", ""), "section")
        lines += ["", f"<b>{acc(role)}{e(sec['title'])}</b>"]
        if sec.get("body"):
            lines.append(e(sec["body"]))
        for b in sec.get("bullets") or []:
            mark = acc("bullet") if n == 0 else ""
            lines.append(f"{mark or '• '}{e(b)}")
    cta = post.get("cta")
    params: dict[str, Any] = {"parse_mode": "HTML"}
    if cta:
        lines += ["", f'{acc("cta")}<a href="{e(cta["url"], quote=True)}">{e(cta["text"])}</a>']
    params["text"] = "\n".join(lines)
    return params


__all__ = ["IconSystem", "TextComposer", "Eligibility", "SendContext", "EmojiMap", "iter_clusters", "emoji_key",
           "apply_html", "strip_html", "apply_markdown", "strip_markdown", "apply_markdown_v2", "strip_markdown_v2",
           "apply_entities", "strip_entities", "apply_rich_message", "strip_rich_message", "apply_keyboard",
           "strip_keyboard", "apply_request", "strip_request", "uses_custom_emoji", "is_custom_emoji_rejection",
           "message_has_custom_emoji", "silently_stripped",
           "CUSTOM_EMOJI_ERROR_HINTS", "resolve_icon_map", "verify_ids", "batched", "load_vocabulary",
           "decorate_post", "density_warnings", "slots_in", "ids_from_message", "count_custom_emoji", "DENSITY", "GET_CUSTOM_EMOJI_MAX"]
