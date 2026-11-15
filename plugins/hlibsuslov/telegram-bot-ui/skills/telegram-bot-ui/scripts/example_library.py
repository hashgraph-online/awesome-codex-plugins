#!/usr/bin/env python3
"""Find examples by user intent and validate the use-case catalog offline.

python scripts/example_library.py --query "бот запись мероприятие"
python scripts/example_library.py --query "CRM" --json
python scripts/example_library.py --check
"""
# run-checks: --check
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "recipes/use-cases.json"


def load():
    return json.loads(CATALOG.read_text(encoding="utf-8"))


def recipes():
    return {r["id"]: r for r in json.loads((ROOT / "recipes/manifest.json").read_text(encoding="utf-8"))["recipes"]}


def validate(catalog, manifest):
    errors, seen = [], set()
    if not isinstance(catalog, dict) or catalog.get("schema_version") != 1:
        return ["catalog: expected schema_version 1"]
    if not isinstance(catalog.get("use_cases"), list) or not isinstance(catalog.get("sources"), dict):
        return ["catalog: use_cases must be a list and sources an object"]
    if not isinstance(catalog.get("verified"), str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", catalog["verified"]):
        errors.append("catalog: verified must be YYYY-MM-DD")
    if not isinstance(catalog.get("scope"), str) or not catalog["scope"].strip():
        errors.append("catalog: missing scope")
    for sid, source in catalog["sources"].items():
        if not isinstance(source, dict) or any(not isinstance(source.get(k), str) or not source[k].strip()
                                               for k in ("title", "url", "supports")):
            errors.append(f"source {sid}: expected title, url and supports")
        elif not source["url"].startswith("https://"):
            errors.append(f"source {sid}: expected HTTPS URL")
    for row in catalog["use_cases"]:
        if not isinstance(row, dict):
            errors.append("use-case row must be an object")
            continue
        rid = row.get("id")
        if not isinstance(rid, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", rid) or rid in seen:
            errors.append(f"invalid/duplicate use-case id: {rid}")
            continue
        seen.add(rid)
        for key in ("title", "surface", "gap", "priority_reason"):
            if not isinstance(row.get(key), str) or not row[key].strip():
                errors.append(f"{rid}: missing {key}")
        invalid_lists = False
        for key in ("intent", "contexts", "recipes", "sources"):
            value = row.get(key)
            if not isinstance(value, list) or not value or any(not isinstance(v, str) or not v.strip() for v in value):
                errors.append(f"{rid}: {key} must be a nonempty list of strings")
                invalid_lists = True
        if invalid_lists:
            continue
        if any(c not in {"private", "group", "channel", "inline", "business", "mini-app"} for c in row["contexts"]):
            errors.append(f"{rid}: unknown context")
        if len(row["recipes"]) != len(set(row["recipes"])):
            errors.append(f"{rid}: repeated recipe")
        if row.get("coverage") not in {"existing-example", "new-offline-model", "composition", "planned"}:
            errors.append(f"{rid}: unknown coverage")
        if row.get("priority") not in {"P0", "P1", "P2"}:
            errors.append(f"{rid}: unknown priority")
        for source in row.get("sources", []):
            if source not in catalog["sources"]:
                errors.append(f"{rid}: unknown source {source}")
        for recipe_id in row.get("recipes", []):
            rec = manifest.get(recipe_id)
            if rec is None:
                errors.append(f"{rid}: unknown recipe {recipe_id}")
                continue
            for key in ("doc", "python", "payload"):
                path = (ROOT / rec[key]).resolve()
                if not path.is_relative_to(ROOT) or not path.is_file():
                    errors.append(f"{rid}: missing/outside {key}: {rec[key]}")
    return errors


def _related(term, word):
    """Whole-word prefix match, plus a 5-letter shared stem for inflected forms
    (remind/reminder, напомни/напоминание)."""
    if word.startswith(term) or (len(word) >= 3 and term.startswith(word)):
        return True
    return len(term) >= 5 and len(word) >= 5 and term[:5] == word[:5]


def search(catalog, manifest, query="", context=None):
    # Short words ("a", "me", "в") match nearly everything and only add noise.
    terms = {t for t in re.findall(r"\w+", query.casefold()) if len(t) >= 3}
    if query.strip() and not terms:
        return []
    matches = []
    for row in catalog["use_cases"]:
        if context and context not in row["contexts"]:
            continue
        words = set(re.findall(r"\w+", " ".join([row["id"], row["title"], *row["intent"]]).casefold()))
        score = sum(1 for term in terms if any(_related(term, w) for w in words))
        if terms and not score:
            continue
        matches.append({**row, "score": score, "examples": [manifest[r] for r in row["recipes"]]})
    return sorted(matches, key=lambda r: (-r["score"], r["priority"], r["id"]))


def main(argv=None):
    # Windows pipes otherwise default to an ANSI codec and cannot emit RU intent.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--query", default="")
    ap.add_argument("--context", choices=["private", "group", "channel", "inline", "business", "mini-app"])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--limit", type=int, default=8)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    if args.limit < 1:
        ap.error("--limit must be positive")
    catalog, manifest = load(), recipes()
    errors = validate(catalog, manifest)
    if errors:
        print("\n".join(errors))
        return 1
    if args.check:
        print(f"OK: {len(catalog['use_cases'])} use cases and their recipe paths")
        return 0
    hits = search(catalog, manifest, args.query, args.context)[:args.limit]
    if args.json:
        print(json.dumps(hits, ensure_ascii=False, indent=2))
    elif not hits:
        print("No match. Try another intent, then use references/example-library.md to compose or extend.")
    else:
        for hit in hits:
            print(f"{hit['id']}: {hit['title']} [{hit['coverage']}]")
            for example in hit["examples"]:
                print(f"  {example['id']}: {example['doc']} -> {example['python']}")
            print(f"  Gap: {hit['gap']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
