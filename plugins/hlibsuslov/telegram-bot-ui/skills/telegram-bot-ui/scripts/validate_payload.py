#!/usr/bin/env python3
"""Structural check of Bot API requests (and objects) against data/bot-api/.

Standard library only; reads local files, never needs a token, never sends.

  py -3 scripts/validate_payload.py examples/payloads/r07-wallet.json
  py -3 scripts/validate_payload.py --method sendMessage params.json
  py -3 scripts/validate_payload.py --type Update examples/fixtures/widget_query_ship.json
  echo '{"method":"sendMessage","params":{"chat_id":1,"text":"hi"}}' | py -3 scripts/validate_payload.py -

Accepted inputs: {"method", "params"}; {"steps": [{"method", "params"}, ...]}
(the examples/payloads format); a list of steps; or bare params with --method.
Bare objects with --type (incoming updates, API results).

What it checks (errors -> exit 1)
  * unknown method; unknown parameters / fields (typos, fields from another type)
  * missing required parameters / fields
  * basic types: Integer, Float, String, Boolean, True, arrays (with depth),
    "X or Y" alternatives, nested objects, `null` values
  * unions ("one of" types such as InputMedia, ReactionType, BotCommandScope,
    InlineQueryResult): the discriminator (`type` / `source` / `status`) must
    select exactly one member, and the object must fit that member

What it does NOT check - this is a structural check, not semantic validation:
  string lengths and byte limits, enum values written only in prose, mutually
  exclusive parameters described in text ("required unless ..." is listed as a
  note), rights, chat types, production vs test-server availability, file sizes.
  Specialised validators own their areas and go deeper:
    buttons / keyboards  -> scripts/validate_keyboard.py
    rich messages        -> scripts/validate_rich.py
    HTML widgets         -> scripts/validate_widget.py
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sync_bot_api import DATA_DIR, load_catalog  # noqa: E402

DISCRIMINATORS = ("type", "source", "status")
DEFER = {
    "reply_markup": "buttons: run scripts/validate_keyboard.py on reply_markup",
    "rich_message": "rich message: run scripts/validate_rich.py",
    "html": "widget HTML: run scripts/validate_widget.py",
}
MAX_DEPTH = 12


@dataclass
class Report:
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    notes: list = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


class Validator:
    def __init__(self, catalog: dict):
        self.cat = catalog
        self.types = catalog["types"]
        self.methods = catalog["methods"]

    # ---------------------------------------------------------------- entry
    def check_request(self, method: str, params) -> Report:
        rep = Report()
        m = self.methods.get(method)
        if m is None:
            close = [n for n in self.methods if n.lower() == method.lower()]
            rep.errors.append(f"unknown method {method!r}" + (f" (did you mean {close[0]}?)" if close else ""))
            return rep
        if not isinstance(params, dict):
            rep.errors.append(f"{method}: params must be an object, got {type(params).__name__}")
            return rep
        self._check_fields(params, m["parameters"], method, rep, 0, what="parameter")
        for name, hint in DEFER.items():
            if name in params and not (name == "html" and method not in ("sendWidget",)):
                rep.notes.append(hint)
        if method.startswith(("sendRichMessage",)) and "rich_message: run" not in " ".join(rep.notes):
            rep.notes.append(DEFER["rich_message"])
        missing_cond = [p["name"] for p in m["parameters"]
                        if p.get("conditional") and p["name"] not in params and not _alternative_present(p, params)]
        if missing_cond:
            rep.notes.append("conditionally required, check the description: " + ", ".join(missing_cond))
        return rep

    def check_object(self, type_name: str, value) -> Report:
        rep = Report()
        if type_name not in self.types:
            rep.errors.append(f"unknown type {type_name!r}")
            return rep
        self._check_type(value, type_name, type_name, rep, 0)
        return rep

    # ---------------------------------------------------------------- core
    def _check_fields(self, obj: dict, spec: list, path: str, rep: Report, depth: int, what: str = "field"):
        known = {f["name"]: f for f in spec}
        for key, val in obj.items():
            if key.startswith("_") and key not in known:
                rep.warnings.append(f"{path}: annotation key {key!r} ignored (not part of the API)")
                continue
            if key not in known:
                rep.errors.append(f"{path}: unknown {what} {key!r}")
                continue
            if val is None:
                rep.errors.append(f"{path}.{key}: null - omit the field instead (null is not a documented value)")
                continue
            self._check_value(val, known[key], f"{path}.{key}", rep, depth + 1)
        for f in spec:
            if f["required"] and f["name"] not in obj:
                rep.errors.append(f"{path}: missing required {what} {f['name']!r} ({f['type']})")

    def _check_value(self, val, f: dict, path: str, rep: Report, depth: int):
        alts = f["types"]
        if len(alts) == 1:
            self._check_alt(val, alts[0], path, rep, depth)
            return
        trials = []
        for alt in alts:
            r = Report()
            self._check_alt(val, alt, path, r, depth)
            if r.ok:
                rep.warnings.extend(r.warnings)
                return
            trials.append((len(r.errors), alt, r))
        trials.sort(key=lambda t: t[0])
        _, alt, best = trials[0]
        rep.errors.append(f"{path}: value fits none of {f['type']!r}; closest is {alt['name']}:")
        rep.errors.extend("  " + e for e in best.errors[:6])

    def _check_alt(self, val, alt: dict, path: str, rep: Report, depth: int):
        name, array = alt["name"], alt["array"]
        if array:
            if not isinstance(val, list):
                rep.errors.append(f"{path}: expected Array of {name}, got {_kind(val)}")
                return
            for i, item in enumerate(val):
                self._check_alt(item, {"name": name, "array": array - 1}, f"{path}[{i}]", rep, depth + 1)
            return
        self._check_scalar_or_type(val, name, path, rep, depth)

    def _check_scalar_or_type(self, val, name: str, path: str, rep: Report, depth: int):
        if name == "Integer":
            if isinstance(val, bool) or not isinstance(val, int):
                if isinstance(val, str) and val.lstrip("-").isdigit():
                    rep.warnings.append(f"{path}: Integer sent as a string {val!r}")
                else:
                    rep.errors.append(f"{path}: expected Integer, got {_kind(val)}")
        elif name == "Float":
            if isinstance(val, bool) or not isinstance(val, (int, float)):
                rep.errors.append(f"{path}: expected Float, got {_kind(val)}")
        elif name == "String":
            if not isinstance(val, str):
                rep.errors.append(f"{path}: expected String, got {_kind(val)}")
        elif name == "Boolean":
            if not isinstance(val, bool):
                rep.errors.append(f"{path}: expected Boolean, got {_kind(val)}")
        elif name == "True":
            if val is not True:
                rep.errors.append(f"{path}: type True accepts only true (omit the field for false), got {val!r}")
        elif name == "InputFile":
            if not isinstance(val, str):
                rep.errors.append(f"{path}: InputFile in a JSON request must be a file_id, an HTTP URL or "
                                  f"'attach://<name>', got {_kind(val)}")
        elif name in self.types:
            if isinstance(val, str) and name != "RichText" and val[:1] in "{[":
                try:
                    val = json.loads(val)
                    rep.warnings.append(f"{path}: {name} passed as a JSON string (fine for form-encoded requests)")
                except ValueError:
                    pass
            self._check_type(val, name, path, rep, depth)
        else:
            rep.warnings.append(f"{path}: type {name!r} is not in the snapshot; not checked")

    def _check_type(self, val, name: str, path: str, rep: Report, depth: int):
        if depth > MAX_DEPTH:
            return
        t = self.types[name]
        if name == "RichText" and (isinstance(val, str) or isinstance(val, list)):
            # documented: "either a String for plain text, an Array of RichText, or ..."
            if isinstance(val, list):
                for i, item in enumerate(val):
                    self._check_type(item, "RichText", f"{path}[{i}]", rep, depth + 1)
            return
        if t["subtypes"]:
            self._check_union(val, name, path, rep, depth)
            return
        if not isinstance(val, dict):
            rep.errors.append(f"{path}: expected {name} object, got {_kind(val)}")
            return
        self._check_fields(val, t["fields"], path, rep, depth)

    def _members(self, name: str) -> list[str]:
        out = []
        for s in self.types[name]["subtypes"]:
            if s in self.types and self.types[s]["subtypes"]:
                out.extend(self._members(s))
            else:
                out.append(s)
        return out

    def _check_union(self, val, name: str, path: str, rep: Report, depth: int):
        members = [m for m in self._members(name) if m in self.types]
        if isinstance(val, dict):
            for disc in DISCRIMINATORS:
                consts = {}
                for m in members:
                    f = next((f for f in self.types[m]["fields"] if f["name"] == disc and f.get("const")), None)
                    if f:
                        consts.setdefault(f["const"], []).append(m)
                if not consts:
                    continue
                if disc not in val:
                    rep.errors.append(f"{path}: {name} needs {disc!r} to pick one of {sorted(consts)}")
                    return
                picked = consts.get(val[disc])
                if not picked:
                    rep.errors.append(f"{path}: {disc}={val[disc]!r} is not a {name}; expected one of {sorted(consts)}")
                    return
                if len(picked) == 1:
                    self._check_fields(val, self.types[picked[0]]["fields"], f"{path}<{picked[0]}>", rep, depth)
                    return
                members = picked  # same discriminator value, decide structurally below
                break
        best = None
        for m in members:
            r = Report()
            self._check_type(val, m, f"{path}<{m}>", r, depth + 1)
            if r.ok:
                rep.warnings.extend(r.warnings)
                return
            if best is None or len(r.errors) < len(best[1].errors):
                best = (m, r)
        if best is None:
            rep.errors.append(f"{path}: {name} has no known members")
            return
        rep.errors.append(f"{path}: value is not any {name} member; closest is {best[0]}:")
        rep.errors.extend("  " + e for e in best[1].errors[:6])


ALT_RE = re.compile(r"required (?:if|unless) (?:the )?(?:parameter |field )?([a-z_]+) (?:isn't|is not|is) (?:specified|used|passed)")


def _alternative_present(p: dict, params: dict) -> bool:
    """'text ... required if rich_message isn't specified' is satisfied by rich_message."""
    return any(name in params for name in ALT_RE.findall(p["description"]))


def _kind(v) -> str:
    if v is None:
        return "null"
    if isinstance(v, bool):
        return f"Boolean {v}"
    if isinstance(v, (int, float)):
        return f"number {v}"
    if isinstance(v, str):
        return f"String {v[:30]!r}"
    if isinstance(v, list):
        return "Array"
    return "object"


def steps_from(doc, method: str | None):
    if method:
        return [(method, doc)]
    if isinstance(doc, dict) and "steps" in doc:
        doc = doc["steps"]
    if isinstance(doc, dict) and "method" in doc:
        return [(doc["method"], doc.get("params", {}))]
    if isinstance(doc, list):
        return [(s.get("method"), s.get("params", {})) for s in doc if isinstance(s, dict)]
    raise ValueError("input is not {method, params}, {steps: [...]} or a list of steps; use --method for bare params")


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Structural Bot API payload check (not full semantic validation)")
    ap.add_argument("files", nargs="+", help="JSON files, or - for stdin")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--method", help="treat each file as bare params of this method")
    g.add_argument("--type", help="treat each file as an object of this type (e.g. Update, Message)")
    ap.add_argument("--data", default=DATA_DIR)
    ap.add_argument("--quiet", action="store_true", help="print only failures")
    args = ap.parse_args(argv)

    cat = load_catalog(args.data)
    v = Validator(cat)
    meta = cat["meta"]
    print(f"Structural check against Bot API {meta['bot_api_version']} (snapshot fetched {meta['fetched_at']}). "
          "Not full semantic validation: limits, prose-only rules, rights and availability are not checked.")
    failed = 0
    for path in args.files:
        try:
            if path == "-":
                doc = json.load(sys.stdin)
            else:
                with open(path, encoding="utf-8") as fh:
                    doc = json.load(fh)
        except (OSError, ValueError) as exc:
            print(f"FAIL {path}: cannot read JSON: {exc}")
            failed += 1
            continue
        if args.type and isinstance(doc, dict) and "ok" in doc and ("result" in doc or "error_code" in doc):
            if not doc.get("ok"):
                print(f"SKIP {path}: an error response (error_code {doc.get('error_code')}), not a {args.type}")
                continue
            doc = doc["result"]  # unwrap the {"ok": true, "result": ...} response envelope
        if args.type:
            items = [(f"<{args.type}>", v.check_object(args.type, doc))]
        else:
            try:
                items = [(f"{i}:{m}", v.check_request(m or "", p)) for i, (m, p) in enumerate(steps_from(doc, args.method))]
            except ValueError as exc:
                print(f"FAIL {path}: {exc}")
                failed += 1
                continue
        for label, rep in items:
            if rep.ok and args.quiet:
                continue
            print(f"{'OK  ' if rep.ok else 'FAIL'} {path} [{label}]")
            for e in rep.errors:
                print(f"    error: {e}")
            for w in rep.warnings:
                print(f"    warn:  {w}")
            for n in sorted(set(rep.notes)):
                print(f"    note:  {n}")
            failed += 0 if rep.ok else 1
    print(f"\n{failed} failing request(s)/object(s)." if failed else "\nall structurally valid.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
