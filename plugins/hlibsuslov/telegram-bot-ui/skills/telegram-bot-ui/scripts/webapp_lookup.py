#!/usr/bin/env python3
# run-checks: check
"""Offline lookup over the Telegram.WebApp (Mini Apps client API) snapshot in data/mini-apps/.

Standard library only; reads local JSON, never touches the network unless `sync --fetch` is given.

  py -3 scripts/webapp_lookup.py show WebApp.requestFullscreen   # member card (owner optional)
  py -3 scripts/webapp_lookup.py show MainButton.setParams       # MainButton/SecondaryButton -> BottomButton
  py -3 scripts/webapp_lookup.py show themeChanged               # events too
  py -3 scripts/webapp_lookup.py show BottomButton               # object card with all members
  py -3 scripts/webapp_lookup.py search storage                  # names and descriptions
  py -3 scripts/webapp_lookup.py since 8.0                       # what a version added
  py -3 scripts/webapp_lookup.py gates                           # members that need isVersionAtLeast
  py -3 scripts/webapp_lookup.py theme                           # themeParams -> CSS variable -> role
  py -3 scripts/webapp_lookup.py meta                            # snapshot date and versions
  py -3 scripts/webapp_lookup.py check                           # catalog consistency (run_checks)
  py -3 scripts/webapp_lookup.py sync --html webapps.html        # offline: parse a saved page, print diff
  py -3 scripts/webapp_lookup.py sync --fetch --write            # one GET of the official page, write

Add --json to any command for machine-readable output.

Version of a member, in order of evidence: the page's own "Bot API X+" mark in the row; the page's
"Recent changes" list ("Added the field X to the class Y"); the version of the object that owns it;
6.0 (the first Mini App release). `version_source` says which one applied.
`WebApp.version` on a client is the Bot API version that client supports, not a script version.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import html
import json
import os
import re
import sys
from html.parser import HTMLParser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sync_bot_api import fetch  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data", "mini-apps")
CATALOG = "webapp-catalog.json"
THEME = "theme-params.json"
PAGE_URL = "https://core.telegram.org/bots/webapps"
SCRIPT_URL = "https://telegram.org/js/telegram-web-app.js"
PARSER_VERSION = 1
BASELINE = "6.0"

# Headings whose table belongs to a differently named owner.
OWNER_ALIASES = {"Initializing Mini Apps": "WebApp", "Events Available for Mini Apps": "events"}
CLASS_ALIASES = {"MainButton": "BottomButton"}  # renamed in 7.10
# Second tables under one heading (Serverless error object) get their own owner name.
SECOND_TABLE = {"Serverless": "ServerlessError"}
REQUIRED_MEMBERS = ("WebApp.initData", "WebApp.ready", "WebApp.MainButton", "BottomButton.setParams",
                    "ThemeParams.bg_color", "events.themeChanged", "WebAppInitData.hash")
MIN_MEMBERS = 250
# Facts the page states in prose without naming the member (re-checked on every sync).
VERSION_OVERRIDES = {
    "WebAppInitData.signature": ("8.0", "changelog prose (8.0: third-party validation without the bot token)"),
}

# Platform caveats the page states in prose elsewhere (not in the member row). Re-checked on every sync.
NOTES = {
    "WebApp.sendData": "Only for Mini Apps launched from a reply-keyboard button; the app closes after sending.",
    "WebApp.readTextFromClipboard": "Only for Mini Apps launched from the attachment menu; needs a user gesture.",
    "WebApp.openLink": "Call only from a user gesture (tap handler).",
    "WebApp.openInvoice": "Payment status in the callback is a hint; confirm by the bot's successful_payment.",
    "WebApp.setBottomBarColor": "Also tints the Android navigation bar.",
    "WebApp.requestFullscreen": "Handle fullscreenFailed (UNSUPPORTED, ALREADY_FULLSCREEN).",
    "WebApp.downloadFile": "The server must send Content-Disposition: attachment and allow web.telegram.org via CORS.",
    "WebApp.disableVerticalSwipes": "Only when the app's own gestures conflict (games, drawing, maps).",
    "WebApp.Serverless": "Only for Mini Apps hosted on Telegram Serverless (app<id>.tgcloud.ai); initData is validated by the platform.",
    "WebApp.initDataUnsafe": "Never trust on a server; validate initData instead.",
    "WebApp.switchInlineQuery": "Only when the bot has inline mode enabled.",
    "WebApp.shareToStory": "Links in stories need Premium.",
    "BottomButton.position": "SecondaryButton only; applies when both buttons are visible.",
    "BottomButton.iconCustomEmojiId": "BottomButton has no `style` field; only color and textColor.",
    "WebAppUser.photo_url": "Sent to all Mini Apps since 8.0 (before: attachment menu only), if privacy settings allow.",
    "events.invoiceClosed": "Status is a client-side hint, not proof of payment.",
}


def _text(fragment: str) -> str:
    t = re.sub(r"<br\s*/?>", " ", fragment)
    t = re.sub(r"<[^>]+>", "", t)
    return re.sub(r"\s+", " ", html.unescape(t)).strip()


def _vkey(v: str | None) -> tuple:
    return tuple(int(x) for x in v.split(".")) if v else (99,)


class _Page(HTMLParser):
    """Collects (heading, anchor) and every table (rows of cell HTML) inside #dev_page_content, in order."""

    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.blocks: list[dict] = []
        self._in_content = 0
        self._heading = None
        self._cell = None
        self._row = None
        self._table = None
        self._depth = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id") == "dev_page_content":
            self._in_content = 1
            self._depth = 0
        if not self._in_content:
            return
        if tag == "div":
            self._depth += 1
        if tag in ("h3", "h4"):
            self._heading = {"type": "heading", "text": "", "anchor": ""}
        elif tag == "a" and self._heading is not None and a.get("name"):
            self._heading["anchor"] = a["name"]
        elif tag == "table":
            self._table = {"type": "table", "rows": []}
        elif tag == "tr" and self._table is not None:
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell = ""
        elif self._cell is not None:
            attr = "".join(f' {k}="{v}"' for k, v in attrs if k == "href")
            self._cell += f"<{tag}{attr}>"

    def handle_endtag(self, tag):
        if not self._in_content:
            return
        if tag == "div":
            self._depth -= 1
            if self._depth < 0:
                self._in_content = 0
        if tag in ("h3", "h4") and self._heading is not None:
            self._heading["text"] = _text(self._heading["text"])
            self.blocks.append(self._heading)
            self._heading = None
        elif tag in ("td", "th") and self._cell is not None:
            self._row.append(self._cell)
            self._cell = None
        elif tag == "tr" and self._row is not None:
            self._table["rows"].append(self._row)
            self._row = None
        elif tag == "table" and self._table is not None:
            self.blocks.append(self._table)
            self._table = None
        elif self._cell is not None:
            self._cell += f"</{tag}>"

    def handle_data(self, data):
        if self._cell is not None:
            self._cell += data
        elif self._heading is not None:
            self._heading["text"] += data

    def handle_entityref(self, name):
        self.handle_data(f"&{name};")

    def handle_charref(self, name):
        self.handle_data(f"&#{name};")


def _recent_changes(raw: str) -> list[tuple[str, list[str]]]:
    """[(version, [item text, ...])] oldest first, from the page's "Recent changes" section."""
    start = raw.find('name="recent-changes"')
    if start < 0:
        return []
    end = raw.find("<h3", start)
    seg = raw[start:end if end > 0 else start + 60000]
    out = []
    for m in re.finditer(r"<strong>Bot API (\d+\.\d+)</strong>(.*?)(?=<h4|\Z)", seg, re.S):
        items = [_text(li) for li in re.findall(r"<li>(.*?)</li>", m.group(2), re.S)]
        out.append((m.group(1), items))
    return list(reversed(out))


def _owner_in_item(item: str, owner: str) -> bool:
    classes = {CLASS_ALIASES.get(c, c) for c in re.findall(r"class (\w+)", item)}
    if owner == "events":
        return bool(re.search(r"\bevents?\b", item)) and not classes
    if classes:
        return owner in classes
    return owner == "WebApp" and not re.search(r"\bevents?\b", item)


def parse(raw: str) -> dict:
    page = _Page()
    page.feed(raw)
    members: dict[str, dict] = {}
    objects: dict[str, dict] = {}
    heading = None
    seen_tables: dict[str, int] = {}
    for block in page.blocks:
        if block["type"] == "heading":
            heading = block
            continue
        if heading is None or not block["rows"]:
            continue
        head = [_text(c) for c in block["rows"][0]]
        if head[:1] not in (["Field"], ["eventType"]):
            continue
        owner = OWNER_ALIASES.get(heading["text"], heading["text"])
        seen_tables[owner] = seen_tables.get(owner, 0) + 1
        if seen_tables[owner] > 1:
            owner = SECOND_TABLE.get(owner, f"{owner}{seen_tables[owner]}")
        anchor = heading["anchor"]
        objects.setdefault(owner, {"name": owner, "anchor": anchor, "url": f"{PAGE_URL}#{anchor}", "members": []})
        for row in block["rows"][1:]:
            if owner == "events":
                name_html, desc_html, typ = row[0], row[-1], "event"
            else:
                name_html, typ, desc_html = row[0], _text(row[1]), row[-1]
            sig = _text(name_html)
            badge = None
            if sig.endswith(" NEW"):
                sig, badge = sig[:-4].strip(), "NEW"
            name = sig.split("(", 1)[0].strip()
            desc = _text(desc_html)
            # A mark at the start (after "Optional.") dates the member; a mark later in the text dates a
            # parameter or option of it (openLink options 6.4, setParams icon_custom_emoji_id 9.5).
            lead = re.sub(r"^\s*(<em>\s*Optional\.?\s*</em>\.?\s*)?", "", desc_html)
            mark = re.match(r"<mark>\s*Bot API (\d+\.\d+)\+\s*</mark>", lead)
            later = [v for v in re.findall(r"<mark>\s*Bot API (\d+\.\d+)\+\s*</mark>", desc_html)
                     if not mark or v != mark.group(1)]
            kind = ("event" if owner == "events" else
                    "method" if typ == "Function" or "(" in sig else
                    "object" if re.fullmatch(r"[A-Z]\w+", name) and name == typ else "field")
            if owner != "WebApp" and owner != "events" and kind == "object":
                kind = "field"
            links = re.findall(r'href="#([a-z0-9-]+)"', row[1] if owner != "events" else "") + \
                re.findall(r'href="#([a-z0-9-]+)"', desc_html)
            key = f"{owner}.{name}"
            members[key] = {
                "key": key, "owner": owner, "name": name, "kind": kind,
                "type": typ, "signature": sig if "(" in sig else None,
                "version": mark.group(1) if mark else None,
                "version_source": "mark" if mark else None,
                "description": re.sub(r"^Bot API \d+\.\d+\+\s*", "", desc),
                "links": sorted(set(links)), "url": f"{PAGE_URL}#{anchor}",
            }
            if badge:
                members[key]["badge"] = badge
            if later:
                members[key]["option_versions"] = sorted(set(later), key=_vkey)
            if key in NOTES:
                members[key]["note"] = NOTES[key]
            objects[owner]["members"].append(key)

    # Recent changes: first (oldest) item that names the member for its owner.
    changes = _recent_changes(raw)
    for m in members.values():
        if m["version"]:
            continue
        word = re.compile(r"(?<![\w])" + re.escape(m["name"]) + r"(?![\w])")
        for ver, items in changes:
            if any(it.startswith(("Added", "Further added")) and word.search(it) and _owner_in_item(it, m["owner"])
                   for it in items):
                m["version"], m["version_source"] = ver, "changelog"
                break

    # Objects inherit the version of the member that introduces them (type or link to their anchor).
    def object_version(obj: dict) -> str | None:
        if obj["name"] in ("WebApp", "events"):
            return BASELINE
        best = None
        for m in members.values():
            if m["owner"] == obj["name"] or not m["version"]:
                continue
            if obj["anchor"] in m["links"] or m["type"] == obj["name"]:
                if best is None or _vkey(m["version"]) < _vkey(best):
                    best = m["version"]
        return best

    for key, (ver, why) in VERSION_OVERRIDES.items():
        if key in members:
            members[key]["version"], members[key]["version_source"] = ver, why
    for m in members.values():  # untagged top-level members are part of the first release
        if not m["version"] and m["owner"] in ("WebApp", "events"):
            m["version"], m["version_source"] = BASELINE, "baseline"
    for _ in range(4):  # nested objects (PopupParams -> PopupButton) settle in a few passes
        for obj in objects.values():
            obj["version"] = object_version(obj)
        for m in members.values():
            parent = objects[m["owner"]].get("version")
            if not m["version"] and parent:
                m["version"], m["version_source"] = parent, "parent"
    for m in members.values():
        if not m["version"]:
            m["version"], m["version_source"] = BASELINE, "baseline"
    # Serverless carries a "NEW" badge and no Bot API mark: keep it unversioned rather than invent one.
    for key in ("WebApp.Serverless",):
        if key in members and members[key]["version_source"] == "baseline":
            members[key]["version"], members[key]["version_source"] = None, "unversioned (NEW badge, 2026-10)"
    for obj in objects.values():
        if obj["name"] in ("Serverless", "ServerlessError"):
            obj["version"] = None
            for key in obj["members"]:
                members[key]["version"], members[key]["version_source"] = None, "unversioned (NEW badge, 2026-10)"

    versions = [m["version"] for m in members.values() if m["version"]]
    return {
        "meta": {
            "source": PAGE_URL,
            "fetched_at": _dt.date.today().isoformat(),
            "html_sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
            "parser_version": PARSER_VERSION,
            "newest_member_version": max(versions, key=_vkey) if versions else None,
            "bot_api_version_checked": None,
            "script": SCRIPT_URL,
            "script_highest_gate": None,
            "counts": {"members": len(members), "objects": len(objects),
                       "events": sum(1 for m in members.values() if m["kind"] == "event")},
            "note": ("Machine-readable copy of the official Mini Apps page. Descriptions are the official text. "
                     "WebApp.version on a client is the Bot API version that client supports."),
        },
        "objects": {k: {**v, "members": v["members"]} for k, v in objects.items()},
        "members": dict(sorted(members.items())),
    }


def guard(cat: dict) -> list[str]:
    problems = []
    if len(cat["members"]) < MIN_MEMBERS:
        problems.append(f"only {len(cat['members'])} members (expected >= {MIN_MEMBERS})")
    for key in REQUIRED_MEMBERS:
        if key not in cat["members"]:
            problems.append(f"missing {key}")
    return problems


def diff(old: dict | None, new: dict) -> dict:
    if not old:
        return {"initial": True}
    o, n = old.get("members", {}), new["members"]
    changed = [k for k in n if k in o and (o[k].get("version"), o[k].get("type"), o[k].get("description"))
               != (n[k].get("version"), n[k].get("type"), n[k].get("description"))]
    return {"added": sorted(set(n) - set(o)), "removed": sorted(set(o) - set(n)), "changed": sorted(changed)}


# ------------------------------------------------------------------ lookup

class WebAppApi:
    def __init__(self, data_dir: str = DATA_DIR):
        with open(os.path.join(data_dir, CATALOG), encoding="utf-8") as fh:
            self.cat = json.load(fh)
        theme_path = os.path.join(data_dir, THEME)
        self.theme = None
        if os.path.isfile(theme_path):
            with open(theme_path, encoding="utf-8") as fh:
                self.theme = json.load(fh)
        self.by_lower = {k.lower(): k for k in self.cat["members"]}

    def resolve(self, query: str) -> tuple[str, str] | None:
        """('member'|'object', key) for 'WebApp.expand', 'expand', 'MainButton.setText', 'BottomButton'."""
        q = query.strip()
        if q.lower().startswith("telegram."):
            q = q[len("telegram."):]
        owner, _, name = q.rpartition(".")
        owner = {"MainButton": "BottomButton", "SecondaryButton": "BottomButton"}.get(owner, owner)
        if owner.lower() == "webapp" and name in ("MainButton", "SecondaryButton"):
            return ("member", f"WebApp.{name}")
        if not owner and q in self.cat["objects"]:
            return ("object", q)
        objs = {k.lower(): k for k in self.cat["objects"]}
        if not owner and q.lower() in objs:
            return ("object", objs[q.lower()])
        if owner:
            key = self.by_lower.get(f"{owner}.{name}".lower())
            return ("member", key) if key else None
        for prefix in ("WebApp", "events", "BottomButton", "ThemeParams"):
            key = self.by_lower.get(f"{prefix}.{q}".lower())
            if key:
                return ("member", key)
        hits = [k for k in self.cat["members"] if k.split(".", 1)[1].lower() == q.lower()]
        return ("member", hits[0]) if len(hits) == 1 else None

    def search(self, word: str, limit: int = 40) -> list[dict]:
        w = word.lower()
        hits = []
        for k, m in self.cat["members"].items():
            score = 100 if m["name"].lower() == w else 30 if w in m["name"].lower() else \
                10 if w in m["description"].lower() else 0
            if score:
                hits.append({"key": k, "kind": m["kind"], "version": m["version"], "score": score})
        hits.sort(key=lambda h: (-h["score"], h["key"]))
        return hits[:limit]

    def since(self, ver: str) -> list[dict]:
        return [m for m in self.cat["members"].values() if m["version"] == ver]

    def gates(self) -> dict[str, str]:
        """WebApp-level members newer than 6.0: calling them needs isVersionAtLeast (or a feature check)."""
        out = {}
        for k, m in self.cat["members"].items():
            if m["owner"] in ("WebApp", "BottomButton", "events") and m["version"] and _vkey(m["version"]) > _vkey(BASELINE):
                out[k] = m["version"]
        return out


def member_card(m: dict, meta: dict) -> str:
    lines = [f"{m['key']}  ({m['kind']}, {m['type']})", m["url"]]
    if m.get("signature"):
        lines.append(f"Signature: {m['signature']}")
    ver = m["version"] or "unversioned"
    lines.append(f"Since: Bot API {ver}  [{m['version_source']}]")
    if m["version"] and _vkey(m["version"]) > _vkey(BASELINE):
        lines.append(f"Gate: Telegram.WebApp.isVersionAtLeast('{m['version']}')")
    lines += ["", m["description"]]
    if m.get("note"):
        lines += ["", f"Note: {m['note']}"]
    lines += ["", f"(snapshot of {meta['source']}, fetched {meta['fetched_at']})"]
    return "\n".join(lines)


def object_card(api: WebAppApi, name: str) -> str:
    obj = api.cat["objects"][name]
    lines = [f"{name}  (object, since Bot API {obj.get('version') or 'unversioned'})", obj["url"], ""]
    for key in obj["members"]:
        m = api.cat["members"][key]
        lines.append(f"  {m['name']:<32} {m['kind']:<7} {m['version'] or '-':<6} {m['type']}")
    return "\n".join(lines)


def check(api: WebAppApi) -> list[str]:
    errors = list(guard(api.cat))
    for k, m in api.cat["members"].items():
        if not m.get("url", "").startswith(PAGE_URL + "#"):
            errors.append(f"{k}: no anchor URL")
        if m["version"] is None and not str(m.get("version_source", "")).startswith("unversioned"):
            errors.append(f"{k}: no version")
    if api.theme:
        keys = {m["name"] for m in api.cat["members"].values() if m["owner"] == "ThemeParams"}
        theme_keys = {row["key"] for row in api.theme["params"]}
        if keys != theme_keys:
            errors.append(f"theme-params.json keys differ from ThemeParams: {sorted(keys ^ theme_keys)}")
        for row in api.theme["params"]:
            m = api.cat["members"].get(f"ThemeParams.{row['key']}")
            if m and m["version"] != row["since"]:
                errors.append(f"theme-params.json {row['key']}: since {row['since']} != catalog {m['version']}")
    return errors


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Offline Telegram.WebApp lookup")
    ap.add_argument("--data", default=DATA_DIR)
    ap.add_argument("--json", action="store_true")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("show", "search", "since"):
        sub.add_parser(name).add_argument("query")
    for name in ("gates", "theme", "meta", "check"):
        sub.add_parser(name)
    sp = sub.add_parser("sync")
    sp.add_argument("--html", help="saved copy of the official page")
    sp.add_argument("--fetch", action="store_true", help="one GET of the official page")
    sp.add_argument("--write", action="store_true", help="write data/mini-apps/webapp-catalog.json")
    sp.add_argument("--bot-api", default=None, help="latest Bot API version seen on the changelog")
    sp.add_argument("--script-gate", default=None, help="highest isVersionAtLeast() gate in telegram-web-app.js")
    args = ap.parse_args(argv)

    def out(obj, text: str | None = None):
        print(json.dumps(obj, ensure_ascii=False, indent=1) if args.json or text is None else text)

    if args.cmd == "sync":
        if not (args.html or args.fetch):
            print("sync needs --html FILE or --fetch")
            return 2
        if args.html:
            with open(args.html, encoding="utf-8", errors="replace") as fh:
                raw = fh.read()
        else:
            raw = fetch(PAGE_URL)
        new = parse(raw)
        problems = guard(new)
        if problems:
            print("layout guard: " + "; ".join(problems) + ". Nothing written; fix the parser.")
            return 2
        path = os.path.join(args.data, CATALOG)
        old = None
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as fh:
                old = json.load(fh)
        meta = new["meta"]
        meta["bot_api_version_checked"] = args.bot_api or (old or {}).get("meta", {}).get("bot_api_version_checked")
        meta["script_highest_gate"] = args.script_gate or (old or {}).get("meta", {}).get("script_highest_gate")
        d = diff(old, new)
        out(d, json.dumps(d, indent=1))
        if args.write:
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                json.dump(new, fh, ensure_ascii=False, indent=1)
                fh.write("\n")
            print(f"wrote {path}: {meta['counts']}")
        return 0

    api = WebAppApi(args.data)
    meta = api.cat["meta"]
    if args.cmd == "show":
        hit = api.resolve(args.query)
        if hit is None:
            close = ", ".join(h["key"] for h in api.search(args.query.rpartition(".")[2], limit=8))
            print(f"not found: {args.query}. Close matches: {close or 'none'}")
            return 1
        kind, key = hit
        if kind == "object":
            out(api.cat["objects"][key], object_card(api, key))
        else:
            out(api.cat["members"][key], member_card(api.cat["members"][key], meta))
    elif args.cmd == "search":
        hits = api.search(args.query)
        out(hits, "\n".join(f"{h['key']:<44} {h['kind']:<7} {h['version'] or '-'}" for h in hits)
            or f"no match for {args.query}")
    elif args.cmd == "since":
        rows = api.since(args.query)
        out(rows, "\n".join(f"{m['key']:<44} {m['kind']}" for m in rows) or f"nothing added in {args.query}")
    elif args.cmd == "gates":
        g = api.gates()
        out(g, "\n".join(f"{k:<44} isVersionAtLeast('{v}')" for k, v in sorted(g.items(), key=lambda x: (_vkey(x[1]), x[0]))))
    elif args.cmd == "theme":
        if not api.theme:
            print("no theme-params.json")
            return 1
        rows = api.theme["params"]
        out(rows, "\n".join(f"{r['key']:<26} {r['css_var']:<38} {r['since']:<5} {r['role']}" for r in rows))
    elif args.cmd == "meta":
        out(meta, f"Telegram.WebApp snapshot of {meta['source']}, fetched {meta['fetched_at']}; "
                  f"{meta['counts']['members']} members in {meta['counts']['objects']} objects; newest member "
                  f"version {meta['newest_member_version']}; Bot API checked {meta['bot_api_version_checked']}; "
                  f"script gate {meta['script_highest_gate']}")
    elif args.cmd == "check":
        errors = check(api)
        for e in errors:
            print(f"FAIL: {e}")
        if errors:
            return 1
        print(f"OK: {meta['counts']['members']} WebApp members, every one with a version and an anchor URL")
    return 0


if __name__ == "__main__":
    sys.exit(main())
