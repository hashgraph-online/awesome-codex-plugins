#!/usr/bin/env python3
"""Render a PRISMA 2020 flow diagram from screening counts.

Input is a JSON file of counts (see --template). Output is Mermaid (for Markdown,
GitHub, Quarto, Obsidian) or Graphviz DOT (for `dot -Tsvg`/`-Tpdf`). Arithmetic is
checked so the diagram cannot silently disagree with itself.

Usage:
    python prisma_flow.py --template > counts.json    # fill in the numbers
    python prisma_flow.py counts.json                 # Mermaid to stdout
    python prisma_flow.py counts.json --format dot -o prisma.dot && dot -Tsvg prisma.dot -o prisma.svg

Exit codes: 0 ok, 1 inconsistent counts, 2 bad input. Standard library only.
"""

from __future__ import annotations

import argparse
import json
import sys

TEMPLATE = {
    "identification": {
        "databases": {"PubMed": 0, "Embase": 0, "Web of Science": 0},
        "registers": {"ClinicalTrials.gov": 0},
        "other_sources": {"citation searching": 0, "websites": 0},
    },
    "removed_before_screening": {"duplicates": 0, "automation_ineligible": 0, "other": 0},
    "records_excluded_screening": 0,
    "reports_not_retrieved": 0,
    "reports_excluded": {"wrong population": 0, "wrong outcome": 0, "wrong study design": 0},
    "other_sources_not_retrieved": 0,
    "other_sources_excluded": {},
    "studies_included": 0,
    "reports_included": 0,
}


def total(d: dict | int) -> int:
    return d if isinstance(d, int) else sum(total(v) for v in d.values())


def compute(c: dict) -> dict:
    ident = c["identification"]
    db_n, reg_n = total(ident.get("databases", {})), total(ident.get("registers", {}))
    other_n = total(ident.get("other_sources", {}))
    removed = total(c.get("removed_before_screening", {}))
    screened = db_n + reg_n - removed
    sought = screened - c.get("records_excluded_screening", 0)
    assessed = sought - c.get("reports_not_retrieved", 0)
    excluded = total(c.get("reports_excluded", {}))
    other_assessed = other_n - c.get("other_sources_not_retrieved", 0)
    other_excluded = total(c.get("other_sources_excluded", {}))
    return {"db": db_n, "reg": reg_n, "other": other_n, "removed": removed, "screened": screened, "sought": sought,
            "assessed": assessed, "excluded": excluded, "other_assessed": other_assessed,
            "other_excluded": other_excluded,
            "included_expected": assessed - excluded + other_assessed - other_excluded}


def check(c: dict, n: dict) -> list[str]:
    problems = []
    for k in ("screened", "sought", "assessed", "other_assessed"):
        if n[k] < 0:
            problems.append(f"negative count for '{k}' ({n[k]}): exclusions exceed records")
    if c.get("reports_included") and c["reports_included"] != n["included_expected"]:
        problems.append(f"reports_included={c['reports_included']} but the flow implies {n['included_expected']}")
    if c.get("studies_included", 0) > c.get("reports_included", 0) and c.get("reports_included"):
        problems.append("more studies than reports included (each study needs at least one report)")
    return problems


def breakdown(d: dict) -> str:
    return "".join(f"<br/>{k}: n = {v}" for k, v in d.items() if v)


def mermaid(c: dict, n: dict) -> str:
    ident = c["identification"]
    L = ["flowchart TD", "  classDef box fill:#fff,stroke:#333,stroke-width:1px,color:#000;"]
    L.append(f'  A["Records identified from:<br/>Databases (n = {n["db"]}){breakdown(ident.get("databases", {}))}'
             f'<br/>Registers (n = {n["reg"]}){breakdown(ident.get("registers", {}))}"]')
    L.append(f'  B["Records removed before screening:{breakdown(c.get("removed_before_screening", {}))}"]')
    L.append(f'  C["Records screened<br/>(n = {n["screened"]})"]')
    L.append(f'  D["Records excluded<br/>(n = {c.get("records_excluded_screening", 0)})"]')
    L.append(f'  E["Reports sought for retrieval<br/>(n = {n["sought"]})"]')
    L.append(f'  F["Reports not retrieved<br/>(n = {c.get("reports_not_retrieved", 0)})"]')
    L.append(f'  G["Reports assessed for eligibility<br/>(n = {n["assessed"]})"]')
    L.append(f'  H["Reports excluded:{breakdown(c.get("reports_excluded", {})) or "<br/>n = 0"}"]')
    L.append(f'  I["Studies included in review<br/>(n = {c.get("studies_included", 0)})'
             f'<br/>Reports of included studies<br/>(n = {c.get("reports_included", 0)})"]')
    L += ["  A --> B", "  A --> C", "  C --> D", "  C --> E", "  E --> F", "  E --> G", "  G --> H", "  G --> I"]
    if n["other"]:
        L.append(f'  O["Records identified from:{breakdown(ident.get("other_sources", {}))}"]')
        L.append(f'  P["Reports sought for retrieval<br/>(n = {n["other"]})"]')
        L.append(f'  Q["Reports not retrieved<br/>(n = {c.get("other_sources_not_retrieved", 0)})"]')
        L.append(f'  R["Reports assessed for eligibility<br/>(n = {n["other_assessed"]})"]')
        L.append(f'  S["Reports excluded:{breakdown(c.get("other_sources_excluded", {})) or "<br/>n = 0"}"]')
        L += ["  O --> P", "  P --> Q", "  P --> R", "  R --> S", "  R --> I"]
    L.append("  class A,B,C,D,E,F,G,H,I" + (",O,P,Q,R,S" if n["other"] else "") + " box;")
    return "\n".join(L) + "\n"


def dot(c: dict, n: dict) -> str:
    def lab(s: str) -> str:
        return s.replace("<br/>", "\\n").replace('"', '\\"')
    m = mermaid(c, n)
    nodes = [ln.strip() for ln in m.splitlines() if '["' in ln]
    edges = [ln.strip() for ln in m.splitlines() if "-->" in ln]
    out = ["digraph PRISMA {", '  rankdir=TB; node [shape=box, fontname="Helvetica", fontsize=10];']
    for nd in nodes:
        key, text = nd.split('["', 1)
        out.append(f'  {key.strip()} [label="{lab(text.rstrip(chr(34) + "]"))}"];')
    out += [f"  {e.replace('-->', '->')};" for e in edges]
    out.append("  {rank=same; A; B;} {rank=same; C; D;} {rank=same; E; F;} {rank=same; G; H;}")
    out.append("}")
    return "\n".join(out) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("counts", nargs="?")
    ap.add_argument("--format", choices=["mermaid", "dot"], default="mermaid")
    ap.add_argument("-o", "--output")
    ap.add_argument("--template", action="store_true", help="print an input template")
    args = ap.parse_args()
    if args.template:
        print(json.dumps(TEMPLATE, indent=2))
        return 0
    if not args.counts:
        ap.error("counts JSON required (or --template)")
    try:
        with open(args.counts, encoding="utf-8") as fh:
            c = json.load(fh)
        n = compute(c)
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    problems = check(c, n)
    text = mermaid(c, n) if args.format == "mermaid" else dot(c, n)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(text)
    else:
        sys.stdout.write(text)
    for p in problems:
        print(f"inconsistent: {p}", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
