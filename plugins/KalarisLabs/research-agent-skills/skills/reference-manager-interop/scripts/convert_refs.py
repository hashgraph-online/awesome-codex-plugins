#!/usr/bin/env python3
"""Convert references between BibTeX, RIS and CSL-JSON.

These three formats move libraries between Zotero, Mendeley, EndNote, JabRef,
Paperpile, Pandoc/Quarto (CSL-JSON) and LaTeX (BibTeX). Formats are inferred from
file extensions (.bib, .ris, .json) unless given explicitly.

Usage:
    python convert_refs.py library.ris refs.bib
    python convert_refs.py refs.bib refs.json            # CSL-JSON for pandoc --citeproc / Quarto
    python convert_refs.py export.json out.ris --from csljson --to ris

Standard library only. Lossy by nature: exotic fields are dropped. Diff the
result against the source before relying on it.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

# CSL type <-> BibTeX type <-> RIS type
TYPES = [
    ("article-journal", "article", "JOUR"),
    ("paper-conference", "inproceedings", "CONF"),
    ("book", "book", "BOOK"),
    ("chapter", "incollection", "CHAP"),
    ("thesis", "phdthesis", "THES"),
    ("report", "techreport", "RPRT"),
    ("dataset", "misc", "DATA"),
    ("webpage", "misc", "ELEC"),
    ("article", "misc", "GEN"),
]
CSL2BIB = {c: b for c, b, _ in TYPES}
BIB2CSL = {"article": "article-journal", "inproceedings": "paper-conference", "conference": "paper-conference",
           "book": "book", "incollection": "chapter", "inbook": "chapter", "phdthesis": "thesis",
           "mastersthesis": "thesis", "techreport": "report", "misc": "article", "online": "webpage",
           "dataset": "dataset", "software": "software"}
CSL2RIS = {c: r for c, _, r in TYPES}
RIS2CSL = {r: c for c, _, r in reversed(TYPES)}


# ---------- CSL-JSON is the internal representation ----------
def parse_name(s: str) -> dict:
    s = s.strip().strip("{}")
    if "," in s:
        family, given = [p.strip() for p in s.split(",", 1)]
        return {"family": family, "given": given}
    parts = s.split()
    return {"family": parts[-1], "given": " ".join(parts[:-1])} if len(parts) > 1 else {"literal": s}


def name_str(n: dict, bib: bool = True) -> str:
    if "literal" in n:
        return "{" + n["literal"] + "}" if bib else n["literal"]
    return f"{n.get('family', '')}, {n.get('given', '')}".strip(", ")


def make_key(item: dict, used: set[str]) -> str:
    fam = (item.get("author") or [{}])[0]
    fam = fam.get("family") or fam.get("literal") or "anon"
    word = next((w for w in re.findall(r"[A-Za-z]+", item.get("title", "")) if len(w) > 3), "ref")
    year = str(((item.get("issued") or {}).get("date-parts") or [[""]])[0][0])
    base = unicodedata.normalize("NFKD", f"{fam}{year}{word}").encode("ascii", "ignore").decode().lower()
    base = re.sub(r"[^a-z0-9]", "", base) or "ref"
    key, i = base, 1
    while key in used:
        i += 1
        key = f"{base}{chr(96 + i)}"
    used.add(key)
    return key


# ---------- BibTeX ----------
def _bib_value(text: str, i: int) -> tuple[str, int]:
    parts = []
    while True:
        while text[i].isspace():
            i += 1
        if text[i] == "{":
            depth, j = 0, i
            while True:
                depth += (text[j] == "{") - (text[j] == "}")
                if depth == 0:
                    break
                j += 1
            parts.append(text[i + 1:j])
            i = j + 1
        elif text[i] == '"':
            j = text.index('"', i + 1)
            parts.append(text[i + 1:j])
            i = j + 1
        else:
            m = re.match(r"[^,}\s#]+", text[i:])
            parts.append(m.group(0))
            i += m.end()
        while i < len(text) and text[i].isspace():
            i += 1
        if i < len(text) and text[i] == "#":
            i += 1
            continue
        return "".join(parts), i


def read_bib(text: str) -> list[dict]:
    items = []
    for m in re.finditer(r"@(\w+)\s*[{(]\s*([^,\s]+)\s*,", text):
        btype = m.group(1).lower()
        if btype in ("comment", "preamble", "string"):
            continue
        f, i = {}, m.end()
        while True:
            fm = re.match(r"\s*([A-Za-z][\w:-]*)\s*=\s*", text[i:])
            if not fm:
                break
            v, i = _bib_value(text, i + fm.end())
            f[fm.group(1).lower()] = re.sub(r"\s+", " ", v).strip()
            cm = re.match(r"\s*,", text[i:])
            if not cm:
                break
            i += cm.end()
        item = {"id": m.group(2), "type": BIB2CSL.get(btype, "article")}
        clean = lambda s: re.sub(r"(?<!\\)[{}]", "", s)  # noqa: E731
        if "title" in f:
            item["title"] = clean(f["title"])
        for role in ("author", "editor"):
            if role in f:
                item[role] = [parse_name(a) for a in re.split(r"\s+and\s+", f[role]) if a.strip()]
        if "year" in f and f["year"][:4].isdigit():
            item["issued"] = {"date-parts": [[int(f["year"][:4])]]}
        container = f.get("journal") or f.get("booktitle")
        if container:
            item["container-title"] = clean(container)
        for src, dst in (("volume", "volume"), ("number", "issue"), ("doi", "DOI"), ("url", "URL"),
                         ("publisher", "publisher"), ("abstract", "abstract"), ("isbn", "ISBN"), ("issn", "ISSN"),
                         ("note", "note")):
            if src in f:
                item[dst] = f[src]
        if "pages" in f:
            item["page"] = f["pages"].replace("--", "-")
        if btype in ("phdthesis", "mastersthesis") and "school" in f:
            item["publisher"] = f["school"]
        items.append(item)
    return items


def write_bib(items: list[dict]) -> str:
    used: set[str] = set()
    out = []
    for it in items:
        key = it.get("id") if re.fullmatch(r"[\w:.-]+", str(it.get("id", ""))) and it.get("id") not in used else None
        key = key or make_key(it, used)
        used.add(key)
        btype = CSL2BIB.get(it.get("type", ""), "misc")
        f: dict[str, str] = {}
        if it.get("author"):
            f["author"] = " and ".join(name_str(n) for n in it["author"])
        if it.get("editor"):
            f["editor"] = " and ".join(name_str(n) for n in it["editor"])
        if it.get("title"):
            f["title"] = it["title"]
        if it.get("container-title"):
            f["journal" if btype == "article" else "booktitle"] = it["container-title"]
        year = ((it.get("issued") or {}).get("date-parts") or [[None]])[0][0]
        if year:
            f["year"] = str(year)
        for src, dst in (("volume", "volume"), ("issue", "number"), ("DOI", "doi"), ("URL", "url"),
                         ("publisher", "publisher"), ("ISBN", "isbn"), ("ISSN", "issn"), ("note", "note")):
            if it.get(src):
                f[dst] = str(it[src])
        if it.get("page"):
            f["pages"] = str(it["page"]).replace("-", "--")
        width = max((len(k) for k in f), default=0)
        body = ",\n".join(f"  {k.ljust(width)} = {{{v}}}" for k, v in f.items())
        out.append(f"@{btype}{{{key},\n{body}\n}}\n")
    return "\n".join(out)


# ---------- RIS ----------
def read_ris(text: str) -> list[dict]:
    items, cur = [], {}
    for line in text.splitlines():
        m = re.match(r"^([A-Z][A-Z0-9])  - ?(.*)$", line.rstrip())
        if not m:
            continue
        tag, val = m.groups()
        val = val.strip()
        if tag == "TY":
            cur = {"type": RIS2CSL.get(val, "article")}
        elif tag == "ER":
            items.append(cur)
            cur = {}
        elif tag in ("AU", "A1"):
            cur.setdefault("author", []).append(parse_name(val))
        elif tag in ("ED", "A2") and cur.get("type") != "article-journal":
            cur.setdefault("editor", []).append(parse_name(val))
        elif tag in ("TI", "T1"):
            cur.setdefault("title", val)
        elif tag in ("JO", "JF", "T2", "BT"):
            cur.setdefault("container-title", val)
        elif tag in ("PY", "Y1", "DA") and re.match(r"\d{4}", val):
            cur.setdefault("issued", {"date-parts": [[int(val[:4])]]})
        elif tag == "SP":
            cur["page"] = val + cur.get("page", "")
        elif tag == "EP":
            cur["page"] = cur.get("page", "") + f"-{val}"
        else:
            dst = {"VL": "volume", "IS": "issue", "DO": "DOI", "UR": "URL", "PB": "publisher", "AB": "abstract",
                   "N2": "abstract", "SN": "ISSN", "N1": "note"}.get(tag)
            if dst:
                cur.setdefault(dst, val)
    return items


def write_ris(items: list[dict]) -> str:
    out = []
    for it in items:
        lines = [f"TY  - {CSL2RIS.get(it.get('type', ''), 'GEN')}"]
        lines += [f"AU  - {name_str(n, bib=False)}" for n in it.get("author", [])]
        lines += [f"ED  - {name_str(n, bib=False)}" for n in it.get("editor", [])]
        if it.get("title"):
            lines.append(f"TI  - {it['title']}")
        if it.get("container-title"):
            lines.append(f"{'JO' if it.get('type') == 'article-journal' else 'T2'}  - {it['container-title']}")
        year = ((it.get("issued") or {}).get("date-parts") or [[None]])[0][0]
        if year:
            lines.append(f"PY  - {year}")
        if it.get("page"):
            sp, _, ep = str(it["page"]).partition("-")
            lines.append(f"SP  - {sp}")
            if ep:
                lines.append(f"EP  - {ep}")
        for src, tag in (("volume", "VL"), ("issue", "IS"), ("DOI", "DO"), ("URL", "UR"), ("publisher", "PB"),
                         ("abstract", "AB"), ("ISSN", "SN"), ("note", "N1")):
            if it.get(src):
                lines.append(f"{tag}  - {it[src]}")
        lines.append("ER  - ")
        out.append("\n".join(lines))
    return "\n\n".join(out) + "\n"


FORMATS = {"bib": (read_bib, write_bib), "ris": (read_ris, write_ris),
           "csljson": (lambda t: json.loads(t), lambda items: json.dumps(items, indent=2, ensure_ascii=False) + "\n")}
EXT = {".bib": "bib", ".bibtex": "bib", ".ris": "ris", ".txt": "ris", ".json": "csljson"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--from", dest="src", choices=FORMATS)
    ap.add_argument("--to", dest="dst", choices=FORMATS)
    args = ap.parse_args()
    src = args.src or EXT.get(args.input.suffix.lower())
    dst = args.dst or EXT.get(args.output.suffix.lower())
    if not src or not dst:
        ap.error("cannot infer formats from extensions; pass --from/--to")
    try:
        items = FORMATS[src][0](args.input.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError, IndexError, AttributeError) as exc:
        print(f"error: cannot parse {args.input} as {src}: {exc}", file=sys.stderr)
        return 2
    args.output.write_text(FORMATS[dst][1](items), encoding="utf-8", newline="\n")
    print(f"converted {len(items)} references: {src} -> {dst} ({args.output})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
