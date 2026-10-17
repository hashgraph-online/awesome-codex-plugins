---
name: graphify-integration
description: |
  Optional knowledge-graph integration. When `graphify-out/graph.json` is
  present, architect/researcher/reviewer/task-builder agents can query
  symbol-level dependencies (IMPORTS, CALLS, EXTENDS, IMPLEMENTS, DEPENDS_ON)
  instead of grepping. Degrades gracefully when the graph is missing. Trigger
  phrases: "knowledge graph", "graphify", "blast radius", "dependency graph".
---

# Graphify Integration

A knowledge graph turns "what will break if I change this file" from a guess
into a query. Cavekit uses it only when it is available — nothing in the
pipeline depends on it.

## Installation (optional)

```bash
pip install graphifyy
graphify build .          # writes graphify-out/graph.json
```

If the file is missing, this skill returns no-ops and every caller falls back
to grep + ripgrep search.

## Graph shape

NetworkX node-link JSON. Nodes are symbols (functions, classes, modules).
Edges carry:

- `type`: `DEPENDS_ON` | `IMPORTS` | `CALLS` | `EXTENDS` | `IMPLEMENTS`
- `confidence`: `EXTRACTED` (high) | `INFERRED` (medium) | `AMBIGUOUS` (low)
- `community`: cluster ID (for partitioning big graphs into readable slices)

## CLI surface (via cavekit-tools)

```bash
cavekit-tools.cjs graph-status                 # is the graph present?
cavekit-tools.cjs graph-query --term auth      # search by name substring
cavekit-tools.cjs graph-dependents --file X    # who imports/calls this?
cavekit-tools.cjs graph-summary                # top-level community list
```

(These subcommands are optional extensions; the base `cavekit-tools.cjs`
ships without them, and they activate only if `graphify-out/graph.json` is
present.)

## Per-phase use

- **Draft (`/ck:sketch`)** — query existing symbols for a proposed kit name
  to avoid collision with existing code.
- **Map (`/ck:map`)** — use `community` IDs to partition tasks into coherent
  tiers. Two tasks whose affected symbols share no edges can run in parallel.
- **Research (`ck:researcher`)** — query existing before fetching external.
  If the graph already answers the question, skip the web.
- **Build (`/ck:make`)** — load the subgraph of the current task's files only.
  Smaller context → faster, cheaper agent.
- **Review / Inspect** — compute blast radius of the diff. Files touched ∪
  transitive dependents = review scope.

## Confidence tiers

Do not treat low-confidence edges (`AMBIGUOUS`) as true without verification.
When blast radius includes an `AMBIGUOUS` edge, fall back to grep and confirm.

## Stub mode

When the graph is missing, every graph-* query returns:

```json
{ "available": false, "fallback": "grep" }
```

Callers check `available` and fall back to `Grep` + `Read`. No error is
raised — this is a degradation, not a failure.
