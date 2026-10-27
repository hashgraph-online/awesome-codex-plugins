#!/usr/bin/env python3
"""Build a research knowledge graph (papers, authors, venues, topics, citations).

Input: a BibTeX (.bib) or CSL-JSON (.json) library. With --openalex, each DOI is
enriched from OpenAlex (authors with IDs, venue, topics, referenced works) and
citation edges are added between papers in the library.

Outputs (in --out directory):
    graph.json      NetworkX node-link JSON (nx.node_link_graph(data, edges="links"))
    graph.graphml   GraphML for Gephi, yEd, Cytoscape, NetworkX, igraph
    nodes.csv / edges.csv   bulk import for Neo4j (LOAD CSV / neo4j-admin) or Gephi
    vault/          Obsidian-style Markdown notes linked with [[wikilinks]]; also ingestible
                    by Markdown-graph tools such as graphify (links become `references` edges)

Usage:
    python build_graph.py references.bib --out kg/
    python build_graph.py references.bib --out kg/ --openalex --mailto you@uni.edu
Standard library only.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

UA = "research-agent-skills-knowledge-graph/1.0 (https://github.com/KalarisLabs/research-agent-skills)"


def slug(s: str, n: int = 60) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:n] or "item"


def norm_doi(d: str) -> str:
    return re.sub(r"^(https?://(dx\.)?doi\.org/|doi:)", "", (d or "").strip(), flags=re.I).lower()


# ---------- library readers ----------
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


def read_library(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8-sig")
    papers = []
    if path.suffix.lower() == ".json":
        for it in json.loads(text):
            authors = [f"{a.get('given', '')} {a.get('family', '')}".strip() or a.get("literal", "")
                       for a in it.get("author", [])]
            year = ((it.get("issued") or {}).get("date-parts") or [[None]])[0][0]
            papers.append({"key": str(it.get("id") or slug(it.get("title", ""))), "title": it.get("title", ""),
                           "authors": authors, "year": year, "venue": it.get("container-title", ""),
                           "doi": norm_doi(it.get("DOI", "")), "keywords": []})
        return papers
    for m in re.finditer(r"@(\w+)\s*[{(]\s*([^,\s]+)\s*,", text):
        if m.group(1).lower() in ("comment", "preamble", "string"):
            continue
        f, i = {}, m.end()
        while True:
            fm = re.match(r"\s*([A-Za-z][\w:-]*)\s*=\s*", text[i:])
            if not fm:
                break
            v, i = _bib_value(text, i + fm.end())
            f[fm.group(1).lower()] = re.sub(r"\s+", " ", re.sub(r"(?<!\\)[{}]", "", v)).strip()
            cm = re.match(r"\s*,", text[i:])
            if not cm:
                break
            i += cm.end()
        authors = []
        for a in re.split(r"\s+and\s+", f.get("author", "")):
            a = a.strip()
            if a and a.lower() != "others":
                authors.append(" ".join(reversed([p.strip() for p in a.split(",", 1)])) if "," in a else a)
        papers.append({"key": m.group(2), "title": f.get("title", ""), "authors": authors,
                       "year": int(f["year"][:4]) if f.get("year", "")[:4].isdigit() else None,
                       "venue": f.get("journal") or f.get("booktitle", ""), "doi": norm_doi(f.get("doi", "")),
                       "keywords": [k.strip() for k in re.split(r"[;,]", f.get("keywords", "")) if k.strip()]})
    return papers


# ---------- OpenAlex enrichment ----------
def openalex(doi: str, mailto: str | None) -> dict | None:
    params = {"select": "id,doi,title,publication_year,authorships,primary_location,topics,referenced_works,cited_by_count"}
    if mailto:
        params["mailto"] = mailto
    url = f"https://api.openalex.org/works/doi:{urllib.parse.quote(doi, safe='/')}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=20) as r:  # noqa: S310
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise


def build(papers: list[dict], enrich: bool, mailto: str | None, max_topics: int) -> tuple[dict, dict]:
    nodes: dict[str, dict] = {}
    edges: set[tuple[str, str, str]] = set()
    oa_to_paper: dict[str, str] = {}
    refs: dict[str, list[str]] = {}

    def node(nid: str, ntype: str, label: str, **attrs) -> str:
        if nid not in nodes:
            nodes[nid] = {"id": nid, "type": ntype, "label": label, **{k: v for k, v in attrs.items() if v not in (None, "")}}
        return nid

    for p in papers:
        pid = node(f"paper:{p['key']}", "paper", p["title"] or p["key"], year=p["year"], doi=p["doi"], key=p["key"])
        data = None
        if enrich and p["doi"]:
            try:
                data = openalex(p["doi"], mailto)
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
                print(f"warn: OpenAlex lookup failed for {p['doi']}: {exc}", file=sys.stderr)
            time.sleep(0.1)
        if data:
            oa_to_paper[data["id"]] = pid
            nodes[pid]["openalex"] = data["id"]
            nodes[pid]["cited_by_count"] = data.get("cited_by_count")
            refs[pid] = data.get("referenced_works") or []
            for a in data.get("authorships") or []:
                au = a.get("author") or {}
                aid = node(f"author:{(au.get('id') or '').rsplit('/', 1)[-1] or slug(au.get('display_name', ''))}",
                           "author", au.get("display_name", ""), openalex=au.get("id"), orcid=au.get("orcid"))
                edges.add((pid, aid, "authored_by"))
            src = ((data.get("primary_location") or {}).get("source") or {})
            if src.get("display_name"):
                edges.add((pid, node(f"venue:{slug(src['display_name'])}", "venue", src["display_name"],
                                     openalex=src.get("id")), "published_in"))
            for t in (data.get("topics") or [])[:max_topics]:
                edges.add((pid, node(f"topic:{slug(t.get('display_name', ''))}", "topic", t.get("display_name", ""),
                                     openalex=t.get("id")), "about"))
        else:
            for a in p["authors"]:
                edges.add((pid, node(f"author:{slug(a)}", "author", a), "authored_by"))
            if p["venue"]:
                edges.add((pid, node(f"venue:{slug(p['venue'])}", "venue", p["venue"]), "published_in"))
        for k in p["keywords"]:
            edges.add((pid, node(f"topic:{slug(k)}", "topic", k), "about"))
    for pid, works in refs.items():
        for w in works:
            if w in oa_to_paper and oa_to_paper[w] != pid:
                edges.add((pid, oa_to_paper[w], "cites"))
    graph = {"directed": True, "multigraph": False, "graph": {"generator": "research-agent-skills/research-knowledge-graph"},
             "nodes": list(nodes.values()),
             "links": [{"source": s, "target": t, "type": ty} for s, t, ty in sorted(edges)]}
    return graph, nodes


def write_graphml(graph: dict, path: Path) -> None:
    keys = sorted({k for n in graph["nodes"] for k in n if k != "id"})
    out = ['<?xml version="1.0" encoding="UTF-8"?>', '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">']
    out += [f'  <key id="n_{k}" for="node" attr.name="{k}" attr.type="string"/>' for k in keys]
    out.append('  <key id="e_type" for="edge" attr.name="type" attr.type="string"/>')
    out.append('  <graph id="research-kg" edgedefault="directed">')
    for n in graph["nodes"]:
        out.append(f'    <node id="{escape(n["id"], {chr(34): "&quot;"})}">'
                   + "".join(f'<data key="n_{k}">{escape(str(n[k]))}</data>' for k in keys if k in n) + "</node>")
    for i, e in enumerate(graph["links"]):
        out.append(f'    <edge id="e{i}" source="{escape(e["source"], {chr(34): "&quot;"})}" '
                   f'target="{escape(e["target"], {chr(34): "&quot;"})}"><data key="e_type">{e["type"]}</data></edge>')
    out += ["  </graph>", "</graphml>", ""]
    path.write_text("\n".join(out), encoding="utf-8")


def write_csv(graph: dict, out: Path) -> None:
    with (out / "nodes.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["id:ID", "label", ":LABEL", "year", "doi"])
        for n in graph["nodes"]:
            w.writerow([n["id"], n["label"], n["type"].capitalize(), n.get("year", ""), n.get("doi", "")])
    with (out / "edges.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow([":START_ID", ":END_ID", ":TYPE"])
        for e in graph["links"]:
            w.writerow([e["source"], e["target"], e["type"].upper()])


def write_vault(graph: dict, nodes: dict, out: Path) -> None:
    vault = out / "vault"
    names = {}
    for n in graph["nodes"]:
        folder = {"paper": "papers", "author": "authors", "venue": "venues", "topic": "topics"}[n["type"]]
        base = slug(n["label"] if n["type"] != "paper" else f"{n.get('key', '')}-{n['label']}", 80)
        names[n["id"]] = f"{folder}/{base}"
    outgoing: dict[str, list[tuple[str, str]]] = {}
    incoming: dict[str, list[tuple[str, str]]] = {}
    for e in graph["links"]:
        outgoing.setdefault(e["source"], []).append((e["type"], e["target"]))
        incoming.setdefault(e["target"], []).append((e["type"], e["source"]))
    for n in graph["nodes"]:
        path = vault / f"{names[n['id']]}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        meta = {k: v for k, v in n.items() if k not in ("label",)}
        lines = ["---"] + [f"{k}: {json.dumps(v, ensure_ascii=False)}" for k, v in meta.items()] + ["---", "",
                                                                                                     f"# {n['label']}", ""]
        for title, rel in (("Links", outgoing.get(n["id"], [])), ("Linked from", incoming.get(n["id"], []))):
            if rel:
                lines.append(f"## {title}")
                lines += [f"- {etype.replace('_', ' ')}: [[{names[other]}|{nodes[other]['label']}]]"
                          for etype, other in sorted(rel)]
                lines.append("")
        path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("library", type=Path)
    ap.add_argument("--out", type=Path, default=Path("knowledge-graph"))
    ap.add_argument("--openalex", action="store_true", help="enrich via OpenAlex (network)")
    ap.add_argument("--mailto", help="email for the OpenAlex polite pool")
    ap.add_argument("--max-topics", type=int, default=3)
    ap.add_argument("--no-vault", action="store_true")
    args = ap.parse_args()
    try:
        papers = read_library(args.library)
    except (OSError, ValueError, IndexError, AttributeError) as exc:
        print(f"error: cannot read {args.library}: {exc}", file=sys.stderr)
        return 2
    graph, nodes = build(papers, args.openalex, args.mailto, args.max_topics)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "graph.json").write_text(json.dumps(graph, indent=2, ensure_ascii=False), encoding="utf-8")
    write_graphml(graph, args.out / "graph.graphml")
    write_csv(graph, args.out)
    if not args.no_vault:
        write_vault(graph, nodes, args.out)
    counts: dict[str, int] = {}
    for n in graph["nodes"]:
        counts[n["type"]] = counts.get(n["type"], 0) + 1
    ecounts: dict[str, int] = {}
    for e in graph["links"]:
        ecounts[e["type"]] = ecounts.get(e["type"], 0) + 1
    print(json.dumps({"nodes": counts, "edges": ecounts, "out": str(args.out)}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
