#!/usr/bin/env python3
"""Offline lookup over the Bot API snapshot in data/bot-api/.

Standard library only; reads local JSON, never touches the network.

  py -3 scripts/tg_api_lookup.py show sendMessage          # method / type card (case-insensitive)
  py -3 scripts/tg_api_lookup.py card sendMessage          # short agent card: catalog + note + example
  py -3 scripts/tg_api_lookup.py search refund              # names, fields, descriptions
  py -3 scripts/tg_api_lookup.py version 10.4               # what a release changed (changelog)
  py -3 scripts/tg_api_lookup.py versions                   # list releases
  py -3 scripts/tg_api_lookup.py since allowed_updates      # changelog history of a symbol/field
  py -3 scripts/tg_api_lookup.py accepts reply_markup       # methods taking a parameter...
  py -3 scripts/tg_api_lookup.py accepts InputMedia         # ...or a type (incl. its union members)
  py -3 scripts/tg_api_lookup.py used-by LabeledPrice       # methods AND types that reference a type
  py -3 scripts/tg_api_lookup.py skeleton sendInvoice       # minimal request with required fields
  py -3 scripts/tg_api_lookup.py diff                       # what the last sync changed
  py -3 scripts/tg_api_lookup.py meta                       # snapshot version and fetch date

Add --json to any command for machine-readable output. --data DIR points at
another snapshot directory (tests use this).

The snapshot is a copy of the official page made on the date in `meta`. If
Telegram has shipped a newer release, run scripts/sync_bot_api.py first.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sync_bot_api import DATA_DIR, SCALARS, load_catalog, load_changelog  # noqa: E402

PLACEHOLDER = {"Integer": 0, "Float": 0.0, "Boolean": False, "True": True, "String": ""}


class Api:
    def __init__(self, data_dir: str = DATA_DIR):
        self.cat = load_catalog(data_dir)
        self.changelog = load_changelog(data_dir)
        self.data_dir = data_dir
        self.index = {}
        for kind in ("methods", "types"):
            for name, sym in self.cat[kind].items():
                self.index[name.lower()] = sym

    # -- basic -------------------------------------------------------------
    def get(self, name: str) -> dict | None:
        return self.index.get(name.lower())

    def members(self, name: str) -> list[str]:
        """A type plus, recursively, every union member it can be."""
        seen, todo = [], [name]
        while todo:
            n = todo.pop(0)
            if n in seen:
                continue
            seen.append(n)
            t = self.cat["types"].get(n)
            if t:
                todo.extend(t.get("subtypes", []))
        return seen

    def unions_of(self, name: str) -> list[str]:
        return [n for n, t in self.cat["types"].items() if name in t.get("subtypes", [])]

    # -- queries -----------------------------------------------------------
    def search(self, word: str, limit: int = 60) -> list[dict]:
        w = word.lower()
        hits = []
        for kind in ("methods", "types"):
            for name, sym in self.cat[kind].items():
                score = 0
                where = []
                if w == name.lower():
                    score += 100
                elif w in name.lower():
                    score += 30
                    where.append("name")
                rows = sym.get("parameters", []) + sym.get("fields", [])
                fields = [f["name"] for f in rows if w in f["name"].lower()]
                if fields:
                    score += 20
                    where.append("field " + ", ".join(fields[:5]))
                if w in sym["description"].lower():
                    score += 10
                    where.append("description")
                elif any(w in f["description"].lower() for f in rows):
                    score += 5
                    where.append("field description")
                if score:
                    hits.append({"name": name, "kind": sym["kind"], "score": score, "where": where,
                                 "url": sym["url"]})
        hits.sort(key=lambda h: (-h["score"], h["name"]))
        return hits[:limit]

    def accepts(self, what: str) -> dict:
        """Methods (and types) that take a parameter/field named `what`, or whose
        parameter/field type mentions type `what` or one of its unions."""
        types = self.cat["types"]
        canonical = next((n for n in types if n.lower() == what.lower()), None)
        targets = set()
        if canonical:
            targets = {canonical, *self.unions_of(canonical), *self.members(canonical)}
        res = {"query": what, "as_type": canonical, "methods": [], "types": []}
        for kind, key in (("methods", "parameters"), ("types", "fields")):
            for name, sym in self.cat[kind].items():
                for f in sym.get(key, []):
                    by_name = f["name"].lower() == what.lower()
                    by_type = bool(targets & {t["name"] for t in f["types"]})
                    if by_name or by_type:
                        res[kind].append({"symbol": name, "field": f["name"], "type": f["type"],
                                          "required": f["required"], "match": "name" if by_name else "type"})
        return res

    def skeleton(self, method: str, depth: int = 1) -> dict:
        m = self.cat["methods"].get(method) or next(
            (v for k, v in self.cat["methods"].items() if k.lower() == method.lower()), None)
        if m is None:
            raise KeyError(method)
        params = {}
        for p in m["parameters"]:
            if p["required"]:
                params[p["name"]] = self._placeholder(p, depth)
        cond = [p["name"] for p in m["parameters"] if p.get("conditional")]
        return {"method": m["name"], "params": params, "conditionally_required": cond,
                "returns": m.get("returns"), "url": m["url"]}

    def _placeholder(self, f: dict, depth: int):
        alt = f["types"][0]
        name = alt["name"]
        if name in PLACEHOLDER:
            val = PLACEHOLDER[name]
            if f["type"] == "Integer or String":
                val = "<chat_id or @username>"
            elif name == "String":
                val = f"<{f['name']}>"
        elif name == "InputFile":
            val = "<file_id, URL or attach://name>"
        else:
            t = self.cat["types"].get(name)
            if t and t["subtypes"]:
                val = {"<one of>": t["subtypes"]}
            elif t and depth > 0:
                val = {g["name"]: self._placeholder(g, depth - 1) for g in t["fields"] if g["required"]}
            else:
                val = f"<{name}>"
        for _ in range(alt["array"]):
            val = [val]
        return val

    def version(self, ver: str) -> dict | None:
        for r in self.changelog.get("releases", []) if isinstance(self.changelog, dict) else []:
            if r["version"] == ver:
                added = []
                for g in r["groups"]:
                    for it in g["items"]:
                        if it["text"].startswith("Added"):
                            for s in it["symbols"]:
                                if s not in added:
                                    added.append(s)
                return {**r, "symbols_mentioned_in_added_items": added}
        return None

    def history(self, name: str) -> list[dict]:
        """Every changelog item that links to `name` or mentions it as a word,
        oldest first: when a symbol (or a field such as `allowed_updates`) appeared
        and how it changed."""
        out = []
        rel = self.changelog.get("releases", []) if isinstance(self.changelog, dict) else []
        word = re.compile(r"(?<![A-Za-z0-9_])" + re.escape(name) + r"(?![A-Za-z0-9_])", re.I)
        for r in rel:
            for g in r["groups"]:
                for it in g["items"]:
                    if name in it["symbols"] or word.search(it["text"]):
                        out.append({"version": r["version"], "date": r["date"], "text": it["text"], "url": r["url"]})
        return list(reversed(out))

    def releases(self) -> list:
        return [{"version": r["version"], "date": r["date"], "url": r["url"]}
                for r in (self.changelog.get("releases", []) if isinstance(self.changelog, dict) else [])
                if r["version"]]

    def diff(self) -> dict | None:
        p = os.path.join(self.data_dir, "diff.json")
        if os.path.isfile(p):
            with open(p, encoding="utf-8") as fh:
                return json.load(fh)
        return None


# ------------------------------------------------------------------ printing

def card(api: Api, sym: dict) -> str:
    lines = [f"{sym['name']}  ({sym['kind']}, section: {sym['section']})", sym["url"], "", sym["description"]]
    rows = sym.get("parameters") if sym["kind"] == "method" else sym.get("fields")
    if rows:
        lines.append("")
        lines.append("Parameters:" if sym["kind"] == "method" else "Fields:")
        w = max(len(r["name"]) for r in rows)
        for r in rows:
            req = "required" if r["required"] else "optional"
            extra = f" [= {r['const']}]" if r.get("const") else ""
            cond = " (conditional)" if r.get("conditional") else ""
            lines.append(f"  {r['name']:<{w}}  {r['type']}  {req}{cond}{extra}")
            lines.append(f"  {'':<{w}}    {r['description']}")
    if sym.get("subtypes"):
        lines += ["", "One of: " + ", ".join(sym["subtypes"])]
    if sym["kind"] == "method":
        lines += ["", f"Returns (from prose): {sym.get('returns') or 'see description'}"]
    else:
        unions = api.unions_of(sym["name"])
        if unions:
            lines += ["", "Member of: " + ", ".join(unions)]
        used = api.accepts(sym["name"])
        ms = sorted({u["symbol"] for u in used["methods"]})
        if ms:
            lines += ["", f"Accepted by {len(ms)} method(s): " + ", ".join(ms)]
    meta = api.cat["meta"]
    lines += ["", f"(snapshot: Bot API {meta['bot_api_version']}, fetched {meta['fetched_at']})"]
    return "\n".join(lines)


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Offline Bot API lookup")
    ap.add_argument("--data", default=DATA_DIR)
    ap.add_argument("--json", action="store_true")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("show", "card", "search", "version", "accepts", "used-by", "skeleton", "since"):
        sp = sub.add_parser(name)
        sp.add_argument("query")
    sub.add_parser("versions")
    sub.add_parser("diff")
    sub.add_parser("meta")
    args = ap.parse_args(argv)
    api = Api(args.data)

    def out(obj, text: str | None = None):
        print(json.dumps(obj, ensure_ascii=False, indent=1) if args.json or text is None else text)

    if args.cmd in ("show", "card"):
        sym = api.get(args.query)
        if sym is None:
            # Client-side Mini App API (Telegram.WebApp.*) lives in its own catalog.
            import webapp_lookup
            if os.path.isfile(os.path.join(webapp_lookup.DATA_DIR, webapp_lookup.CATALOG)) \
                    and webapp_lookup.WebAppApi().resolve(args.query):
                return webapp_lookup.main((["--json"] if args.json else []) + ["show", args.query])
            hits = api.search(args.query, limit=8)
            print(f"not found: {args.query}. Close matches: {', '.join(h['name'] for h in hits) or 'none'}")
            return 1
        if args.cmd == "show":
            out(sym, card(api, sym))
        else:
            import api_notes
            note = api_notes.load_notes(os.path.join(args.data, "agent-notes")).get(sym["name"])
            text = api_notes.card(sym, note, api.cat["meta"])
            out({"symbol": sym["name"], "kind": sym["kind"], "note": note, "card": text}, text)
    elif args.cmd == "search":
        hits = api.search(args.query)
        out(hits, "\n".join(f"{h['name']:<40} {h['kind']:<6} {'; '.join(h['where'])}" for h in hits)
            or f"no match for {args.query}")
    elif args.cmd == "version":
        r = api.version(args.query)
        if r is None:
            print(f"no release {args.query} in data/bot-api/changelog.json; known: "
                  + ", ".join(x["version"] for x in api.releases()[:12]))
            return 1
        text = [f"Bot API {r['version']} - {r['date']}  {r['url']}"]
        for n in r["notes"]:
            text.append(f"  {n}")
        for g in r["groups"]:
            text.append(f"\n[{g['title'] or 'Changes'}]")
            text += [f"  - {it['text']}" for it in g["items"]]
        text.append("\nSymbols in 'Added ...' items: " + ", ".join(r["symbols_mentioned_in_added_items"]))
        out(r, "\n".join(text))
    elif args.cmd == "since":
        h = api.history(args.query)
        out(h, "\n".join(f"{x['version'] or '?':<6} {x['date']}  {x['text']}" for x in h)
            or f"{args.query} is not mentioned in the changelog (older than the changelog, or a typo)")
    elif args.cmd == "versions":
        rs = api.releases()
        out(rs, "\n".join(f"{r['version']:<6} {r['date']}  {r['url']}" for r in rs))
    elif args.cmd in ("accepts", "used-by"):
        res = api.accepts(args.query)
        if args.cmd == "accepts":
            res = {**res, "types": []}
        lines = []
        if res["as_type"]:
            lines.append(f"type {res['as_type']} (and unions containing it: {', '.join(api.unions_of(res['as_type'])) or 'none'})")
        for kind in ("methods", "types"):
            if res[kind]:
                lines.append(f"{kind}: {len({r['symbol'] for r in res[kind]})}")
                lines += [f"  {r['symbol']}.{r['field']}: {r['type']} ({'required' if r['required'] else 'optional'})"
                          for r in res[kind]]
        out(res, "\n".join(lines) or f"nothing takes {args.query}")
    elif args.cmd == "skeleton":
        try:
            sk = api.skeleton(args.query)
        except KeyError:
            print(f"no method {args.query}")
            return 1
        text = json.dumps({"method": sk["method"], "params": sk["params"]}, ensure_ascii=False, indent=2)
        if sk["conditionally_required"]:
            text += "\n// conditionally required (read their descriptions): " + ", ".join(sk["conditionally_required"])
        text += f"\n// returns: {sk['returns']}  {sk['url']}"
        out(sk, text)
    elif args.cmd == "diff":
        d = api.diff()
        from sync_bot_api import summarize_diff
        out(d, summarize_diff(d) if d else "no diff.json")
    elif args.cmd == "meta":
        m = api.cat["meta"]
        out(m, f"Bot API {m['bot_api_version']} released {m['release_date']}, fetched {m['fetched_at']}; "
               f"{m['counts']['methods']} methods, {m['counts']['types']} types")
    return 0


if __name__ == "__main__":
    sys.exit(main())
