---
name: research-knowledge-graph
description: Turn a bibliography or literature corpus into a knowledge graph of papers, authors, venues, topics and citation links, then analyze it (citation clusters, key papers, bridging work, research gaps) or export it to Neo4j, Gephi, NetworkX, Obsidian or Markdown-graph tools such as graphify. Use when mapping a research field, building a citation network, finding influential or bridging papers, or visualizing how a literature connects. Zero-dependency builder with optional OpenAlex enrichment.
license: MIT
compatibility: Python 3.9+ standard library; network access to api.openalex.org for --openalex. networkx optional for analysis.
metadata:
  version: "1.0"
  category: knowledge-and-rag
  maintainer: Kalaris Labs
  author: Kalaris Labs (Sayan Chowdhury)
  tags: knowledge graph, citation network, bibliometrics, OpenAlex, Neo4j, Gephi, NetworkX, Obsidian, graphify, science mapping
---

# Research Knowledge Graphs

A literature review is a graph problem in disguise: which papers everyone
builds on, which clusters talk past each other, which work bridges them, and
where the gaps are. This skill builds that graph from a reference library and
hands it to whichever graph tool the user prefers.

## Build

```bash
# Offline: authors, venues and keywords from the .bib itself
python scripts/build_graph.py references.bib --out kg/

# Enriched: disambiguated authors (OpenAlex IDs, ORCID), venues, topics, and
# citation edges between papers in the library
python scripts/build_graph.py references.bib --out kg/ --openalex --mailto you@university.edu
```

CSL-JSON (`.json`, exported by Zotero or `reference-manager-interop`) also works as input.

| Output | Use it with |
|---|---|
| `graph.json` | NetworkX: `nx.node_link_graph(json.load(f), edges="links")`, or any JS graph lib |
| `graph.graphml` | Gephi, yEd, Cytoscape, igraph, `nx.read_graphml` |
| `nodes.csv`, `edges.csv` | Neo4j (`neo4j-admin database import full --nodes=nodes.csv --relationships=edges.csv`) or Gephi spreadsheet import |
| `vault/` | Obsidian (graph view), and Markdown-graph tools such as graphify, which read `[[wikilinks]]` as edges |

**Schema.** Node `type` ∈ {`paper`, `author`, `venue`, `topic`}. Edge `type` ∈
{`authored_by`, `published_in`, `about`, `cites`}. Paper nodes carry `doi`, `year`,
`openalex`, `cited_by_count` when known.

## Expand beyond the library (snowballing)

Citation edges only connect papers you already have. To map a field:

1. Seed with 5-20 core papers.
2. Backward: collect each seed's `referenced_works` from OpenAlex. Forward: query
   `https://api.openalex.org/works?filter=cites:W123...` for citing works.
3. Keep candidates cited by ≥2 seeds (co-citation), export them to `.bib`, rebuild.
4. Stop when a round adds few new highly connected papers. Report the rounds and thresholds (reproducibility).

## Analyze (NetworkX)

```python
import json, networkx as nx
g = nx.node_link_graph(json.load(open("kg/graph.json")), edges="links")
papers = [n for n, d in g.nodes(data=True) if d["type"] == "paper"]
cit = g.edge_subgraph([(u, v) for u, v, d in g.edges(data=True) if d["type"] == "cites"]).copy()

influential = sorted(cit.in_degree(), key=lambda x: -x[1])[:10]            # most cited within corpus
bridges = sorted(nx.betweenness_centrality(cit.to_undirected()).items(), key=lambda x: -x[1])[:10]
communities = nx.community.louvain_communities(cit.to_undirected(), seed=0)  # research clusters
```

Interpretation guidelines:
- **High in-degree** within the corpus = foundational for *this* literature (not globally important).
- **High betweenness** = bridges clusters, often the best papers to read for synthesis sections.
- **Communities** = candidate subsections of a review. Name each by its top topics and most cited paper.
- **Sparse links between clusters that share topics** = a potential research gap worth stating (and verifying).
- Co-authorship components show research groups. Beware name-based author merging without `--openalex`.

## Visualize

- Gephi: open `graph.graphml` → ForceAtlas2 → size by in-degree → color by modularity class.
- Obsidian: open `kg/vault` as a vault and use Graph view, filtering by folder (papers/authors/topics).
- Small graphs in documents: convert the citation subgraph to Mermaid (`flowchart LR`, one edge per `cites`).

## Integrity rules

- Never invent edges or papers. Every node and edge must come from the library or the OpenAlex record.
- Verify surprising structure, such as an apparent gap, by reading the papers before claiming it.

## Caveats to state in any write-up

Coverage depends on OpenAlex/Crossref metadata; citation edges are only as complete as
`referenced_works`. Keyword/topic nodes are coarse. Always report the data source,
retrieval date and filtering thresholds.

## Related skills

`paper-corpus-rag` (full-text QA over the same papers), `literature-review`,
`systematic-review-prisma`, `networkx`, `reference-manager-interop`, `citation-verification`.
