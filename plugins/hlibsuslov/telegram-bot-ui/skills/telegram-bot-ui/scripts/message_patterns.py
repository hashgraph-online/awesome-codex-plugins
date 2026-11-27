#!/usr/bin/env python3
"""Notification and message patterns: find the pattern for a message, show it, render it, check a payload.

Standard library only; reads local files, never needs a token, never sends.

  py -3 scripts/message_patterns.py list
  py -3 scripts/message_patterns.py find "Заказ отправлен, трек-номер 2045…"
  py -3 scripts/message_patterns.py show alert-threshold --lang ru
  py -3 scripts/message_patterns.py render spec.json          (slots -> HTML and the sendMessage payload)
  py -3 scripts/message_patterns.py check payload.json [--pattern report-kpi] [--json]

The grammar and every rule: references/message-patterns.md. Catalog: data/message-patterns.json.
`check` reads {method, params}, {steps: [...]} or a list of them, and checks every text or caption. It is
meant for messages the bot sends on its own; header rules skip one-line replies unless --pattern is given.
Findings are warnings and notes (design defects to fix); exit 1 only when the file can't be read.

  warnings  HEADER_NOT_BOLD, HEADER_LONG, HEADER_PUNCTUATION, HEADER_ICONS, FIRST_LINE_LONG, NO_GAP,
            EMOJI_PER_LINE, EMOJI_TOTAL, DECOR_RULE, SHOUTING, GREETING, SIGN_OFF, SEPARATOR_MIX, ISO_TIME,
            BODY_LONG, LINE_LONG, PATTERN_HEADER_WORDS, PATTERN_SOUND, PATTERN_NO_ACTION
  notes     PATTERN_NO_PRIMARY
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOG = os.path.join(SKILL, "data", "message-patterns.json")
sys.path.insert(0, os.path.join(SKILL, "examples", "python"))
from tgkit import notify  # noqa: E402

EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿⬀-⯿⌚-⏿←-⇿]️?")
TAG = re.compile(r"<[^>]+>")
PRE = re.compile(r"<pre>.*?</pre>", re.S)
RULE_LINE = re.compile(r"^\s*([━─—–\-=_~*•·➖▬═.]|[\U0001F300-\U0001FAFF☀-➿]️?)\1{2,}\s*$")
SHOUT = re.compile(r"\b[A-ZА-ЯЁІЇЄҐ]{5,}\b")
GREETING = re.compile(r"^(hi|hello|hey|dear|good (morning|afternoon|evening)|здравствуй|привет|добр(ый|ое|ого) "
                      r"(день|вечер|утро|утра)|уважаем|вітаю|привіт|добр(ий|ого) (день|вечір|ранку)|шановн)", re.I)
SIGN_OFF = re.compile(r"(best regards|kind regards|regards|sincerely|your [\w\s]{0,20}team|с уважением|ваша команда|"
                      r"команда [\w\s-]{1,20}$|з повагою)", re.I)
ISO = re.compile(r"\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}")
SEPS = {":": re.compile(r"^[^\s:][^:]{0,30}:\s\S"), "—": re.compile(r"^\S[^—]{0,30}\s—\s\S"),
        "-": re.compile(r"^\S[^-]{0,30}\s-\s\S")}
DIGIT_GROUP = re.compile(r"(?<=\d)[\s  ](?=\d{3}\b)")
TEXT_METHODS = {"sendMessage": "text", "editMessageText": "text", "sendPhoto": "caption", "sendVideo": "caption",
                "sendAnimation": "caption", "sendDocument": "caption", "sendAudio": "caption", "sendLivePhoto": "caption",
                "editMessageCaption": "caption"}
# A footer is the last single line after a blank line that carries meta: as-of time, source, update time.
FOOTER_META = re.compile(r"\bas of\b|\bupdated\b|\bsource\b|данные на|по состоянию|обновлено|источник|дані на|"
                         r"станом на|оновлено|джерело|<tg-time", re.I)
CLOCK = re.compile(r"\b\d{1,2}:\d{2}\b")
HEADER_WORDS_MAX = 7  # without a pattern: only clearly overlong headers are flagged


def load_catalog() -> dict:
    with open(CATALOG, encoding="utf-8") as fh:
        return json.load(fh)


def patterns() -> dict[str, dict]:
    return {p["id"]: p for p in load_catalog()["patterns"]}


# ---------------------------------------------------------------- find

def find(text: str, limit: int = 3) -> list[tuple[int, dict]]:
    """Patterns whose search words occur in the text (any language), best first."""
    low = text.lower().replace("ё", "е")
    scored = []
    for p in load_catalog()["patterns"]:
        words = [w for lang in p["find"].values() for w in lang] + [n for n in p["names"].values()]
        score = sum(2 if " " in w else 1 for w in {w.lower().replace("ё", "е") for w in words} if w in low)
        if score:
            scored.append((score, p))
    scored.sort(key=lambda sp: -sp[0])
    return scored[:limit]


# ---------------------------------------------------------------- check

def visible(text: str) -> str:
    return html.unescape(TAG.sub("", text))


def header_words(header: str) -> int:
    plain = DIGIT_GROUP.sub("", EMOJI.sub("", visible(header)))
    return sum(1 for w in plain.split() if re.search(r"\w", w))


def _bold_first(first: str, entities: list | None) -> bool:
    if entities is not None:
        return any(e.get("type") == "bold" and e.get("offset", 99) <= 3 for e in entities if isinstance(e, dict))
    rest = first.strip()
    m = re.match(r"(<tg-emoji[^>]*>.*?</tg-emoji>|[^\s<]{1,4})\s+(?=<)", rest)
    if m and EMOJI.search(visible(m.group(1))):
        rest = rest[m.end():]
    return rest.startswith(("<b>", "<strong>"))


def _footer_italic(last_raw: str, text: str, parse_mode: str | None, entities: list | None) -> bool:
    mode = (parse_mode or "").lower()
    if mode.startswith("markdown"):
        return True  # not parsed here; no claim either way
    if mode == "html":
        return last_raw.strip().startswith(("<i>", "<em>"))
    u16 = lambda t: len(t.encode("utf-16-le")) // 2  # noqa: E731 (entity offsets are UTF-16 units)
    start = u16(text.rstrip()) - u16(visible(last_raw).strip())
    return any(isinstance(e, dict) and e.get("type") == "italic" and e.get("offset", -1) <= start
               and e.get("offset", 0) + e.get("length", 0) >= u16(text.rstrip()) for e in entities or [])


def check_text(text: str, *, parse_mode: str | None, entities: list | None, where: str,
               pattern: dict | None = None, params: dict | None = None) -> list[dict]:
    found: list[dict] = []

    def add(level: str, code: str, message: str) -> None:
        found.append({"level": level, "code": code, "where": where, "message": message})

    raw = text if (parse_mode or "").lower() == "html" else html.escape(text, quote=False)
    no_pre = PRE.sub("", raw)
    lines = raw.split("\n")
    shown = [visible(ln) for ln in no_pre.split("\n")]
    nonempty = [ln for ln in shown if ln.strip()]
    if not nonempty:
        return found
    first_raw = next(ln for ln in lines if ln.strip())
    first = visible(first_raw).strip()
    if len(nonempty) >= 2 and not _bold_first(first_raw, entities if parse_mode is None else None):
        add("warning", "HEADER_NOT_BOLD", "the first line is the header: icon + 2-5 words in bold")
    words = header_words(first_raw)
    structured = len(nonempty) >= 2 or pattern is not None  # a one-line reply in a dialogue has no header
    if structured and pattern is None and words > HEADER_WORDS_MAX:
        add("warning", "HEADER_LONG", f"header has {words} words: say the news in 2-5")
    if structured and (first.rstrip().endswith((".", "!")) or "!" in first):
        add("warning", "HEADER_PUNCTUATION", "no period or '!' in the header")
    if structured and len(EMOJI.findall(first)) > 1:
        add("warning", "HEADER_ICONS", f"{len(EMOJI.findall(first))} emoji in the header: exactly one icon (or none)")
    if len(first) > 80:
        add("warning", "FIRST_LINE_LONG", f"first line is {len(first)} characters; previews cut at about 80")
    blank_at = next((i for i, ln in enumerate(shown) if not ln.strip() and i > 0), None)
    if len(nonempty) >= 4 and (blank_at is None or blank_at > 2):
        add("warning", "NO_GAP", "no blank line after the header group: header (+ subject), blank line, body")
    for ln in shown:
        if len(EMOJI.findall(ln)) > 1 and not RULE_LINE.match(ln):
            add("warning", "EMOJI_PER_LINE", f"{len(EMOJI.findall(ln))} emoji on one line: {ln.strip()[:40]!r}")
            break
    total = len(EMOJI.findall("\n".join(shown)))
    if total > 5:
        add("warning", "EMOJI_TOTAL", f"{total} emoji in one message: the header icon and status marks only")
    if any(RULE_LINE.match(ln) for ln in shown):
        add("warning", "DECOR_RULE", "a decorative separator line: use a blank line, it doesn't wrap on phones")
    shouted = [w for w in SHOUT.findall("\n".join(shown)) if not any(c.isdigit() for c in w)]
    if shouted or "!!" in "\n".join(shown):
        add("warning", "SHOUTING", "ALL CAPS or '!!' (" + ", ".join(shouted[:3] or ["!!"]) + "): the icon and words carry it")
    after_header = [ln.strip() for ln in nonempty if not RULE_LINE.match(ln)][:3]
    if any(GREETING.match(ln) for ln in after_header):
        add("warning", "GREETING", "a greeting in a notification: start with the news")
    if SIGN_OFF.search(nonempty[-1]):
        add("warning", "SIGN_OFF", "a sign-off: the chat already says who writes")
    used = {sep for sep, rx in SEPS.items() if sum(1 for ln in nonempty[1:] if rx.match(ln.strip())) >= 2}
    if len(used) > 1:
        add("warning", "SEPARATOR_MIX", f"fact lines use {' and '.join(sorted(used))}: one separator bot-wide")
    if ISO.search("\n".join(shown)):
        add("warning", "ISO_TIME", "a raw ISO timestamp: use <tg-time> or local time with the zone")
    if len(nonempty) > 11:
        add("warning", "BODY_LONG", f"{len(nonempty)} lines: keep the body to 8, move the rest to a button, Rich or a file")
    if any(len(ln) > 160 for ln in shown):
        add("warning", "LINE_LONG", "a line over 160 characters: split it into facts or sentences")
    groups = [g.strip() for g in re.split(r"\n\s*\n", no_pre.strip()) if g.strip()]
    if len(groups) >= 3 and "\n" not in groups[-1]:
        last = groups[-1]
        meta = FOOTER_META.search(last) or (CLOCK.search(visible(last))
                                            and not any(rx.match(visible(last)) for rx in SEPS.values()))
        if meta and not _footer_italic(last, text, parse_mode, entities):
            add("warning", "FOOTER_NOT_ITALIC", "the last line is the footer (time, source): set it in italic, <i>…</i>")
    if pattern is not None:
        lo, hi = pattern["header"]["words"]
        if not lo <= words <= hi:
            add("warning", "PATTERN_HEADER_WORDS", f"{pattern['id']} headers are {lo}-{hi} words; this one has {words}")
        silent = bool((params or {}).get("disable_notification"))
        if pattern["sound"] == "silent" and not silent:
            add("warning", "PATTERN_SOUND", f"{pattern['id']} is silent: set disable_notification")
        if pattern["sound"] == "ping" and silent:
            add("warning", "PATTERN_SOUND", f"{pattern['id']} needs the reader now: don't send it silently")
        rows = ((params or {}).get("reply_markup") or {}).get("inline_keyboard") or []
        buttons = [b for row in rows if isinstance(row, list) for b in row if isinstance(b, dict)]
        if pattern["buttons"] == "required" and not buttons:
            add("warning", "PATTERN_NO_ACTION", f"{pattern['id']} needs an action button")
        if pattern["buttons"] == "required" and buttons and not any(b.get("style") in ("primary", "success") for b in buttons):
            add("note", "PATTERN_NO_PRIMARY", "mark the forward action with style primary (or success when it commits)")
    return found


def steps_of(doc) -> list[tuple[str, dict]]:
    items = doc.get("steps") if isinstance(doc, dict) and isinstance(doc.get("steps"), list) else \
        [doc] if isinstance(doc, dict) else doc if isinstance(doc, list) else []
    return [(s["method"], s.get("params") if isinstance(s.get("params"), dict) else {}) for s in items
            if isinstance(s, dict) and isinstance(s.get("method"), str)]


def check_doc(doc, pattern: dict | None = None) -> list[dict]:
    found: list[dict] = []
    for i, (method, params) in enumerate(steps_of(doc)):
        field = TEXT_METHODS.get(method)
        if method == "editMessageMedia" and isinstance(params.get("media"), dict):
            params = {**params, "caption": params["media"].get("caption", ""),
                      "parse_mode": params["media"].get("parse_mode")}
            field = "caption"
        text = params.get(field) if field else None
        if not isinstance(text, str):
            continue
        ent = params.get("entities" if field == "text" else "caption_entities")
        found += check_text(text, parse_mode=params.get("parse_mode"), entities=ent, where=f"step {i + 1} {method}",
                            pattern=pattern, params=params)
    return found


# ---------------------------------------------------------------- commands

def cmd_list(args) -> int:
    for p in load_catalog()["patterns"]:
        print(f"{p['id']:16} {p['names']['en']:28} {p['names']['ru']:36} sound={p['sound']}")
    return 0


def cmd_find(args) -> int:
    hits = find(args.text)
    if args.json:
        print(json.dumps([{"id": p["id"], "score": s, "name": p["names"]} for s, p in hits], ensure_ascii=False, indent=2))
        return 0
    if not hits:
        print("no pattern matched: read references/message-patterns.md section 7 (five questions)")
        return 0
    for s, p in hits:
        print(f"{p['id']:16} score {s}  {p['names'].get(args.lang, p['names']['en'])}")
    return 0


def card(p: dict, lang: str) -> dict:
    ex = p["examples"].get(lang) or p["examples"]["en"]
    pay = notify.payload(ex, chat_id=111111111, sound="silent" if p["sound"] == "silent" else "ping")
    return {"id": p["id"], "name": p["names"].get(lang, p["names"]["en"]), "header": p["header"], "blocks": p["blocks"],
            "buttons": p["buttons"], "sound": p["sound"], "lifecycle": p["lifecycle"], "grouping": p["grouping"],
            "html": notify.render(ex), "payload": pay}


def cmd_show(args) -> int:
    pats = patterns()
    if args.id not in pats:
        print(f"unknown pattern {args.id!r}; one of: {', '.join(pats)}", file=sys.stderr)
        return 2
    c = card(pats[args.id], args.lang)
    if args.json:
        print(json.dumps(c, ensure_ascii=False, indent=2))
        return 0
    h = c["header"]
    print(f"{c['id']} · {c['name']}")
    print(f"header:    {h['form']}, {h['words'][0]}-{h['words'][1]} words, icon {h['icon']}")
    print(f"blocks:    {', '.join(c['blocks'])}")
    print(f"buttons:   {c['buttons']} · sound: {c['sound']} · grouping: {c['grouping']}")
    print(f"lifecycle: {c['lifecycle']}")
    print("\n--- HTML (parse_mode HTML)\n" + c["html"])
    print("\n--- payload\n" + json.dumps(c["payload"], ensure_ascii=False, indent=2))
    return 0


def cmd_render(args) -> int:
    with open(args.spec, encoding="utf-8") as fh:
        spec = json.load(fh)
    pat = patterns().get(spec.get("pattern", ""))
    sound = spec.get("sound") or ("silent" if pat and pat["sound"] == "silent" else "ping")
    try:
        pay = notify.payload(spec, chat_id=spec.get("chat_id", 0), sound=sound)
    except (KeyError, ValueError) as exc:
        print(f"FAIL: {exc}")
        return 1
    found = check_doc(pay, pat)
    if args.json:
        print(json.dumps({"payload": pay, "findings": found}, ensure_ascii=False, indent=2))
    else:
        print(pay["params"].get("text") or pay["params"].get("caption"))
        print("\n" + json.dumps(pay, ensure_ascii=False, indent=2))
        for f in found:
            print(f"WARN: {f['code']}: {f['message']}")
    return 0


def cmd_check(args) -> int:
    pat = None
    if args.pattern:
        pat = patterns().get(args.pattern)
        if pat is None:
            print(f"unknown pattern {args.pattern!r}", file=sys.stderr)
            return 2
    try:
        raw = sys.stdin.read() if args.file == "-" else open(args.file, encoding="utf-8").read()
        found = check_doc(json.loads(raw), pat)
    except (OSError, ValueError) as exc:
        print(f"FAIL: {exc}")
        return 1
    if args.json:
        print(json.dumps({"findings": found}, ensure_ascii=False, indent=2))
    else:
        for f in found:
            print(f"{'WARN' if f['level'] == 'warning' else 'NOTE'}: {f['code']} {f['where']}: {f['message']}")
        print(f"{sum(f['level'] == 'warning' for f in found)} warning(s), {sum(f['level'] == 'note' for f in found)} note(s)")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list").set_defaults(fn=cmd_list)
    p = sub.add_parser("find")
    p.add_argument("text")
    p.add_argument("--lang", default="en")
    p.add_argument("--json", action="store_true")
    p.set_defaults(fn=cmd_find)
    p = sub.add_parser("show")
    p.add_argument("id")
    p.add_argument("--lang", default="en", choices=("en", "ru"))
    p.add_argument("--json", action="store_true")
    p.set_defaults(fn=cmd_show)
    p = sub.add_parser("render")
    p.add_argument("spec")
    p.add_argument("--json", action="store_true")
    p.set_defaults(fn=cmd_render)
    p = sub.add_parser("check")
    p.add_argument("file", help="a payload file, or - for stdin")
    p.add_argument("--pattern")
    p.add_argument("--json", action="store_true")
    p.set_defaults(fn=cmd_check)
    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError):
            pass
    sys.exit(main())
