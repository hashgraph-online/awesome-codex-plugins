#!/usr/bin/env python3
"""Snapshot the whole Telegram Bot API into data/bot-api/ and diff it.

Standard library only. Never needs a bot token, never talks to Telegram's bot
endpoint: it reads the public documentation pages.

  py -3 scripts/sync_bot_api.py                 # fetch both pages, write snapshot + diff
  py -3 scripts/sync_bot_api.py --check         # fetch and print the diff, write nothing
  py -3 scripts/sync_bot_api.py --api-html api.html --changelog-html changelog.html
                                                 # offline: parse saved pages

Fetch policy: exactly one GET per page (https://core.telegram.org/bots/api and
/bots/api-changelog), a generic user agent, no retries in a loop. The site has
no robots.txt restrictions for these pages (checked 2026-11-15: /robots.txt is
404); keep it polite anyway - run it when Telegram ships a release, not on a cron.

Output (data/bot-api/):
  catalog.json    every method and type: description, fields/parameters (type,
                  required, description), return type, section, anchor URL,
                  union subtypes, plus meta (version, release date, fetch date,
                  page hashes)
  changelog.json  every release: version, date, anchor, grouped items with the
                  symbols each item links to
  diff.json       added / removed / changed symbols against the previous
                  catalog.json (an "initial" marker on the first run)

Layout guard: if the page no longer looks like the Bot API page this parser
knows (too few methods/types, missing anchor symbols, tables without the
expected headers, no version), the script exits with code 2 and writes nothing,
instead of committing a half-empty catalog. Fix the parser, then re-run.
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
import tempfile
import urllib.request
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data", "bot-api")
API_URL = "https://core.telegram.org/bots/api"
CHANGELOG_URL = "https://core.telegram.org/bots/api-changelog"
USER_AGENT = "Mozilla/5.0 (compatible; bot-api-catalog-sync/1.0)"
PARSER_VERSION = 1

# Layout guard thresholds. Bot API 10.4 has ~190 methods and ~470 types; a real
# release never removes a large share of them at once.
MIN_METHODS = 100
MIN_TYPES = 200
REQUIRED_SYMBOLS = ("getUpdates", "sendMessage", "Update", "Message", "User", "Chat",
                    "InlineKeyboardMarkup", "InputFile")
MAX_SHRINK = 0.10  # refuse a snapshot that loses >10% of methods or types

SCALARS = {"Integer", "Int", "String", "Boolean", "True", "False", "Float", "Float number"}
IDENT_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")


class LayoutError(RuntimeError):
    """The documentation page no longer has the structure this parser knows."""


# --------------------------------------------------------------------------- HTML

class _BlockParser(HTMLParser):
    """Flatten the page into a list of blocks: h3/h4 headers, paragraphs,
    tables (rows of cells) and lists (items), keeping link targets."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks: list[dict] = []
        self._cur: dict | None = None     # p / li / td / th / h3 / h4 text collector
        self._table: dict | None = None
        self._row: list | None = None
        self._lists: list[dict] = []
        self._href: str | None = None
        self._ul_depth = 0

    # text collectors -------------------------------------------------------
    def _start_text(self, kind: str, **extra):
        self._cur = {"kind": kind, "text": "", "links": [], **extra}

    def _end_text(self) -> dict | None:
        cur, self._cur = self._cur, None
        if cur is not None:
            cur["text"] = re.sub(r"\s+", " ", cur["text"]).strip()
        return cur

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("h3", "h4"):
            self._start_text(tag, anchor=None)
        elif tag == "a":
            name = a.get("name")
            if self._cur is not None and self._cur["kind"] in ("h3", "h4") and name:
                self._cur["anchor"] = name
                return
            self._href = a.get("href")
            if self._cur is not None and self._href:
                self._cur["links"].append({"href": self._href, "text": ""})
        elif tag == "img" and self._cur is not None:
            self._cur["text"] += a.get("alt") or ""
        elif tag == "br" and self._cur is not None:
            self._cur["text"] += " "
        elif tag == "p" and not self._lists and self._table is None:
            self._start_text("p")
        elif tag == "table":
            self._table = {"kind": "table", "header": [], "rows": []}
        elif tag == "tr" and self._table is not None:
            self._row = []
        elif tag in ("td", "th") and self._table is not None:
            self._start_text(tag)
        elif tag in ("ul", "ol"):
            if self._lists and self._cur is not None and self._cur["kind"] == "li":
                self._cur["text"] += " "      # nested list: keep text in the parent item
            self._lists.append({"kind": "list", "items": []} if not self._lists else self._lists[-1])
            self._ul_depth += 1
        elif tag == "li" and self._lists:
            if self._ul_depth == 1:
                self._start_text("li")

    def handle_endtag(self, tag):
        if tag in ("h3", "h4"):
            cur = self._end_text()
            if cur:
                self.blocks.append(cur)
        elif tag == "a":
            self._href = None
        elif tag == "p" and self._cur is not None and self._cur["kind"] == "p":
            cur = self._end_text()
            if cur and cur["text"]:
                self.blocks.append(cur)
        elif tag in ("td", "th") and self._row is not None and self._cur is not None:
            self._row.append(self._end_text())
        elif tag == "tr" and self._table is not None and self._row is not None:
            if self._row and all(c["kind"] == "th" for c in self._row):
                self._table["header"] = [c["text"] for c in self._row]
            elif self._row:
                self._table["rows"].append(self._row)
            self._row = None
        elif tag == "table" and self._table is not None:
            self.blocks.append(self._table)
            self._table = None
        elif tag == "li" and self._ul_depth == 1 and self._cur is not None and self._cur["kind"] == "li":
            self._lists[-1]["items"].append(self._end_text())
        elif tag in ("ul", "ol") and self._lists:
            self._ul_depth -= 1
            lst = self._lists.pop()
            if not self._lists:
                self.blocks.append(lst)

    def handle_data(self, data):
        if self._cur is not None:
            self._cur["text"] += data
            if self._href and self._cur["links"]:
                self._cur["links"][-1]["text"] += data


def parse_blocks(page: str) -> list[dict]:
    p = _BlockParser()
    p.feed(page.split('<div class="footer_wrap"', 1)[0])  # site footer: link lists, not API
    p.close()
    return p.blocks


# ------------------------------------------------------------------ type exprs

def parse_type_expr(expr: str) -> list[dict]:
    """'Array of Array of InlineKeyboardButton' -> [{'name': ..., 'array': 2}];
    'Integer or String' -> two alternatives. Also splits ', ' lists used for
    long unions ('InputMediaAudio, InputMediaDocument, ... and InputMediaVideo')."""
    expr = expr.replace(" and ", " or ").replace(", ", " or ")
    out = []
    array = 0
    for raw in expr.split(" or "):
        part = raw.strip()
        depth = 0
        while part.startswith("Array of "):
            depth += 1
            part = part[len("Array of "):].strip()
        if not part:
            continue
        # 'Array of A or B' means Array of (A or B) in the docs
        if depth:
            array = depth
        out.append({"name": part, "array": depth or (array if out else 0)})
    return out


def normalize_scalar(name: str) -> str:
    return {"Int": "Integer", "Float number": "Float"}.get(name, name)


def field_const(description: str) -> str | None:
    """The fixed discriminator value of a union member field, e.g.
    'Type of the result, must be article' or 'always “emoji”'."""
    m = re.search(r"(?:always|must be) [“\"]([^”\"]+)[”\"]", description)
    if m:
        return m.group(1)
    m = re.search(r"\bmust be ([a-z_][a-z0-9_]*)\b", description)
    if m and m.group(1) not in ("used", "specified", "sent", "one", "a", "an", "the", "in", "at", "non"):
        return m.group(1)
    return None


# ------------------------------------------------------------------ api page

def _anchor_name(href: str) -> str | None:
    if "#" not in href:
        return None
    base, frag = href.split("#", 1)
    if base not in ("", "/bots/api", "https://core.telegram.org/bots/api"):
        return None
    return frag or None


def parse_api(page: str) -> dict:
    blocks = parse_blocks(page)
    methods: dict[str, dict] = {}
    types: dict[str, dict] = {}
    section = None
    current: dict | None = None
    anchors: dict[str, str] = {}

    def finish(sym: dict | None):
        if sym is None:
            return
        sym["description"] = " ".join(sym.pop("_paras")).strip()
        if sym["kind"] == "method":
            sym["returns"] = extract_return(sym["description"], sym.pop("_return_links"))
        else:
            sym.pop("_return_links")

    for b in blocks:
        kind = b["kind"]
        if kind == "h3":
            finish(current)
            current = None
            section = b["text"]
            continue
        if kind == "h4":
            finish(current)
            current = None
            name = b["text"]
            if not IDENT_RE.match(name) or not b.get("anchor"):
                continue
            is_method = name[0].islower()
            current = {
                "name": name,
                "kind": "method" if is_method else "type",
                "section": section,
                "anchor": b["anchor"],
                "url": f"{API_URL}#{b['anchor']}",
                "_paras": [],
                "_return_links": [],
            }
            current["parameters" if is_method else "fields"] = []
            if not is_method:
                current["subtypes"] = []
            (methods if is_method else types)[name] = current
            anchors[b["anchor"]] = name
            continue
        if current is None:
            continue
        if kind == "p":
            current["_paras"].append(b["text"])
            current["_return_links"].extend(l["text"] for l in b["links"])
        elif kind == "list":
            items = b["items"]
            linked = [it for it in items if it and len(it["links"]) == 1 and it["text"] == it["links"][0]["text"].strip()]
            if current["kind"] == "type" and items and len(linked) == len(items):
                current["subtypes"].extend(it["text"] for it in items)
            else:
                current["_paras"].append(" ".join("- " + it["text"] for it in items if it))
        elif kind == "table":
            rows = parse_table(b, current)
            current["parameters" if current["kind"] == "method" else "fields"].extend(rows)

    finish(current)
    return {"methods": methods, "types": types, "anchors": anchors}


def parse_table(table: dict, sym: dict) -> list[dict]:
    header = table["header"]
    method = sym["kind"] == "method"
    expected = ["Parameter", "Type", "Required", "Description"] if method else ["Field", "Type", "Description"]
    if header != expected:
        raise LayoutError(f"{sym['name']}: table header {header!r}, expected {expected!r}")
    out = []
    for row in table["rows"]:
        cells = [c["text"] for c in row]
        if len(cells) != len(expected):
            raise LayoutError(f"{sym['name']}: row with {len(cells)} cells, expected {len(expected)}")
        if method:
            name, typ, req, desc = cells
            if req not in ("Yes", "Optional"):
                raise LayoutError(f"{sym['name']}.{name}: Required column is {req!r}")
            required = req == "Yes"
        else:
            name, typ, desc = cells
            required = not desc.startswith("Optional.")
            if desc.startswith("Optional."):
                desc = desc[len("Optional."):].strip()
        item = {
            "name": name,
            "type": typ,
            "types": [{"name": normalize_scalar(t["name"]), "array": t["array"]} for t in parse_type_expr(typ)],
            "required": required,
            "description": desc,
        }
        const = field_const(desc) if name in ("type", "source", "status", "kind") else None
        if const:
            item["const"] = const
        if re.search(r"\brequired (?:if|unless|for|when)\b|\bmust be (?:specified|used) (?:if|unless)\b", desc):
            item["conditional"] = True
        out.append(item)
    return out


RETURN_SENT_RE = re.compile(r"[^.]*\b(?:[Rr]eturns?|returned|On success)\b[^.]*\.")


def extract_return(description: str, links: list[str]) -> str | None:
    """Best-effort return type from prose such as 'On success, the sent Message
    is returned' or 'Returns an Array of Update objects'. Kept next to the raw
    description; treat it as a hint, the description is authoritative."""
    sentences = RETURN_SENT_RE.findall(description)
    for s in sentences:
        found = []
        for m in re.finditer(r"(Array of )?([A-Z][A-Za-z0-9]+)", s):
            word = m.group(2)
            if word in ("On", "Returns", "Return", "Use", "If", "Otherwise", "In", "The", "A", "An",
                        "Requires", "Note", "Please", "Telegram", "Bot", "API", "After", "Currently",
                        "Each", "For", "Only", "This", "Can", "Also", "No", "HTTP", "JSON", "URL"):
                continue
            if word in links or word in ("True", "String", "Integer", "Boolean", "Int"):
                found.append((m.group(1) or "") + normalize_scalar(word))
        if found:
            seen = []
            for f in found:
                if f not in seen:
                    seen.append(f)
            return " or ".join(seen)
    return None


# ------------------------------------------------------------------ changelog

VERSION_RE = re.compile(r"Bot API (\d+(?:\.\d+)*)")


def parse_changelog(page: str) -> list[dict]:
    blocks = parse_blocks(page)
    releases: list[dict] = []
    cur = None
    group = None
    for b in blocks:
        if b["kind"] == "h4":
            try:
                date = _dt.datetime.strptime(b["text"], "%B %d, %Y").date().isoformat()
            except ValueError:
                cur = None
                continue
            cur = {"date": date, "version": None, "anchor": b.get("anchor"),
                   "url": f"{CHANGELOG_URL}#{b.get('anchor')}", "notes": [], "groups": []}
            group = None
            releases.append(cur)
        elif b["kind"] == "h3":
            continue
        elif cur is None:
            continue
        elif b["kind"] == "p":
            m = VERSION_RE.fullmatch(b["text"]) or (VERSION_RE.match(b["text"]) if cur["version"] is None and len(b["text"]) < 20 else None)
            if m and cur["version"] is None:
                cur["version"] = m.group(1)
            elif len(b["text"]) < 60 and not b["text"].endswith("."):
                group = {"title": b["text"], "items": []}
                cur["groups"].append(group)
            else:
                cur["notes"].append(b["text"])
        elif b["kind"] == "list":
            if group is None:
                group = {"title": None, "items": []}
                cur["groups"].append(group)
            for it in b["items"]:
                if not it:
                    continue
                syms = []
                for l in it["links"]:
                    a = _anchor_name(l["href"])
                    if a and l["text"].strip() and IDENT_RE.match(l["text"].strip()):
                        if l["text"].strip() not in syms:
                            syms.append(l["text"].strip())
                group["items"].append({"text": it["text"], "symbols": syms})
            group = None if group["title"] is None else group
    return releases


# ------------------------------------------------------------------ catalog

def build_catalog(api_page: str, changelog_page: str | None, fetched_at: str,
                  min_methods: int = MIN_METHODS, min_types: int = MIN_TYPES) -> dict:
    parsed = parse_api(api_page)
    methods, types = parsed["methods"], parsed["types"]
    releases = parse_changelog(changelog_page) if changelog_page else []

    # version: the 'Recent changes' block of the API page is the spec itself
    recent = parse_changelog(api_page)
    head = next((r for r in recent if r["version"]), None)
    if head is None:
        raise LayoutError("no 'Bot API X.Y' release header found on the API page")
    if releases and releases[0]["version"] and releases[0]["version"] != head["version"]:
        print(f"WARN: changelog newest is {releases[0]['version']}, API page says {head['version']}",
              file=sys.stderr)

    check_layout(methods, types, min_methods, min_types)
    catalog = {
        "meta": {
            "bot_api_version": head["version"],
            "release_date": head["date"],
            "fetched_at": fetched_at,
            "source": API_URL,
            "changelog_source": CHANGELOG_URL,
            "api_sha256": hashlib.sha256(api_page.encode("utf-8")).hexdigest(),
            "changelog_sha256": hashlib.sha256(changelog_page.encode("utf-8")).hexdigest() if changelog_page else None,
            "parser_version": PARSER_VERSION,
            "counts": {"methods": len(methods), "types": len(types),
                       "unions": sum(1 for t in types.values() if t["subtypes"])},
            "note": "Machine-readable copy of the public Bot API page. Descriptions are the "
                    "official text; 'returns' is extracted from prose and is a hint.",
        },
        "methods": dict(sorted(methods.items())),
        "types": dict(sorted(types.items())),
    }
    return {"catalog": catalog, "changelog": releases}


def check_layout(methods: dict, types: dict, min_methods: int = MIN_METHODS, min_types: int = MIN_TYPES) -> None:
    problems = []
    if len(methods) < min_methods:
        problems.append(f"only {len(methods)} methods parsed (expected >= {min_methods})")
    if len(types) < min_types:
        problems.append(f"only {len(types)} types parsed (expected >= {min_types})")
    for s in REQUIRED_SYMBOLS:
        if s not in methods and s not in types:
            problems.append(f"anchor symbol {s} not found")
    no_desc = [n for n, m in methods.items() if not m["description"]]
    if len(no_desc) > 5:
        problems.append(f"{len(no_desc)} methods without description, e.g. {no_desc[:3]}")
    with_params = sum(1 for m in methods.values() if m["parameters"] or "Requires no parameters" in m["description"]
                      or "no parameters" in m["description"])
    if methods and with_params / len(methods) < 0.8:
        problems.append(f"only {with_params}/{len(methods)} methods have a parameter table")
    if "sendMessage" in methods and not any(p["name"] == "text" and p["required"] for p in methods["sendMessage"]["parameters"]):
        problems.append("sendMessage.text is not a required parameter - table parsing is off")
    if problems:
        raise LayoutError("; ".join(problems))


def referenced_types(catalog: dict) -> set[str]:
    out = set()
    for kind in ("methods", "types"):
        for sym in catalog[kind].values():
            for f in sym.get("parameters", []) + sym.get("fields", []):
                for t in f["types"]:
                    out.add(t["name"])
            for s in sym.get("subtypes", []):
                out.add(s)
    return out - SCALARS


def diff_catalogs(old: dict | None, new: dict) -> dict:
    if old is None:
        return {"from_version": None, "to_version": new["meta"]["bot_api_version"],
                "initial": True, "added": {}, "removed": {}, "changed": {}}
    res = {"from_version": old["meta"].get("bot_api_version"),
           "to_version": new["meta"]["bot_api_version"],
           "from_fetched_at": old["meta"].get("fetched_at"),
           "to_fetched_at": new["meta"].get("fetched_at"),
           "initial": False, "added": {}, "removed": {}, "changed": {}}
    for kind in ("methods", "types"):
        o, n = old.get(kind, {}), new[kind]
        res["added"][kind] = sorted(set(n) - set(o))
        res["removed"][kind] = sorted(set(o) - set(n))
        changed = {}
        for name in sorted(set(o) & set(n)):
            c = diff_symbol(o[name], n[name])
            if c:
                changed[name] = c
        res["changed"][kind] = changed
    return res


def diff_symbol(o: dict, n: dict) -> dict:
    key = "parameters" if n["kind"] == "method" else "fields"
    of = {f["name"]: f for f in o.get(key, [])}
    nf = {f["name"]: f for f in n.get(key, [])}
    c: dict = {}
    if set(nf) - set(of):
        c["added_" + key] = sorted(set(nf) - set(of))
    if set(of) - set(nf):
        c["removed_" + key] = sorted(set(of) - set(nf))
    mod = {}
    for name in sorted(set(of) & set(nf)):
        d = {}
        for attr in ("type", "required"):
            if of[name].get(attr) != nf[name].get(attr):
                d[attr] = [of[name].get(attr), nf[name].get(attr)]
        if of[name].get("description") != nf[name].get("description"):
            d["description_changed"] = True
        if d:
            mod[name] = d
    if mod:
        c["modified_" + key] = mod
    if o.get("subtypes") != n.get("subtypes"):
        c["subtypes"] = [o.get("subtypes"), n.get("subtypes")]
    if o.get("returns") != n.get("returns"):
        c["returns"] = [o.get("returns"), n.get("returns")]
    if o.get("description") != n.get("description"):
        c["description_changed"] = True
    return c


def check_shrink(old: dict | None, new: dict) -> None:
    if not old:
        return
    for kind in ("methods", "types"):
        before, after = len(old.get(kind, {})), len(new[kind])
        if before and (before - after) / before > MAX_SHRINK:
            raise LayoutError(f"{kind} dropped from {before} to {after}; refusing (use --allow-shrink if real)")


def summarize_diff(d: dict) -> str:
    if d["initial"]:
        return f"initial snapshot of Bot API {d['to_version']} (no previous catalog to compare)"
    lines = [f"Bot API {d['from_version']} -> {d['to_version']}"]
    for kind in ("methods", "types"):
        if d["added"][kind]:
            lines.append(f"  added {kind}: {', '.join(d['added'][kind])}")
        if d["removed"][kind]:
            lines.append(f"  removed {kind}: {', '.join(d['removed'][kind])}")
        for name, c in d["changed"][kind].items():
            parts = []
            for k, v in c.items():
                if k.startswith(("added_", "removed_")):
                    parts.append(f"{k.split('_')[0]} {', '.join(v)}")
                elif k.startswith("modified_"):
                    parts.append("modified " + ", ".join(f"{f}({'/'.join(x for x in m if x != 'description_changed') or 'text'})"
                                                         for f, m in v.items()))
                elif k == "description_changed":
                    parts.append("description text")
                else:
                    parts.append(k)
            lines.append(f"  changed {name}: {'; '.join(parts)}")
    if len(lines) == 1:
        lines.append("  no structural changes")
    return "\n".join(lines)


# ------------------------------------------------------------------ io

def fetch(url: str, timeout: int = 30) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # one request per page
        return resp.read().decode("utf-8")


def load_json(path: str):
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: str, obj) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".snapshot-", suffix=".tmp", dir=os.path.dirname(os.path.abspath(path)))
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    os.replace(tmp, path)


def load_catalog(data_dir: str = DATA_DIR) -> dict:
    cat = load_json(os.path.join(data_dir, "catalog.json"))
    if cat is None:
        raise SystemExit(f"no catalog at {data_dir}; run scripts/sync_bot_api.py first")
    return cat


def load_changelog(data_dir: str = DATA_DIR) -> list:
    return load_json(os.path.join(data_dir, "changelog.json")) or []


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--api-html", help="parse this saved copy of /bots/api instead of fetching")
    ap.add_argument("--changelog-html", help="parse this saved copy of /bots/api-changelog")
    ap.add_argument("--out", default=DATA_DIR, help="output directory (default data/bot-api)")
    ap.add_argument("--check", action="store_true", help="print the diff, write nothing")
    ap.add_argument("--allow-shrink", action="store_true", help="accept a large drop in symbol count")
    ap.add_argument("--fetched-at", help="override the recorded fetch date (YYYY-MM-DD)")
    args = ap.parse_args(argv)

    try:
        if args.api_html:
            with open(args.api_html, encoding="utf-8") as fh:
                api_page = fh.read()
            changelog_page = None
            if args.changelog_html:
                with open(args.changelog_html, encoding="utf-8") as fh:
                    changelog_page = fh.read()
        else:
            api_page = fetch(API_URL)
            changelog_page = fetch(CHANGELOG_URL)
    except OSError as exc:
        print(f"FAIL: cannot read the documentation: {exc}", file=sys.stderr)
        return 3

    fetched_at = args.fetched_at or _dt.date.today().isoformat()
    try:
        built = build_catalog(api_page, changelog_page, fetched_at)
        old = load_json(os.path.join(args.out, "catalog.json"))
        if not args.allow_shrink:
            check_shrink(old, built["catalog"])
    except LayoutError as exc:
        print(f"FAIL: documentation layout changed, nothing written: {exc}", file=sys.stderr)
        return 2

    cat = built["catalog"]
    diff = diff_catalogs(old, cat)
    missing = sorted(referenced_types(cat) - set(cat["types"]))
    print(f"Bot API {cat['meta']['bot_api_version']} ({cat['meta']['release_date']}): "
          f"{cat['meta']['counts']['methods']} methods, {cat['meta']['counts']['types']} types, "
          f"{len(built['changelog'])} changelog releases")
    if missing:
        print(f"WARN: referenced but undefined types: {', '.join(missing)}")
    print(summarize_diff(diff))
    if args.check:
        return 0
    write_json(os.path.join(args.out, "catalog.json"), cat)
    if built["changelog"]:
        write_json(os.path.join(args.out, "changelog.json"), {
            "meta": {"source": CHANGELOG_URL, "fetched_at": fetched_at,
                     "newest_version": next((r["version"] for r in built["changelog"] if r["version"]), None)},
            "releases": built["changelog"],
        })
    if old is None or diff["initial"] or any(diff["added"].values()) or any(diff["removed"].values()) \
            or any(diff["changed"].values()) or not os.path.isfile(os.path.join(args.out, "diff.json")):
        write_json(os.path.join(args.out, "diff.json"), diff)
    print(f"wrote {os.path.relpath(args.out, ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
