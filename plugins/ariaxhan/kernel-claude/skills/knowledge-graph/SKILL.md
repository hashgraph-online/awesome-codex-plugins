---
name: knowledge-graph
description: "Build + keep-fresh + query a deterministic code knowledge graph to cut agent orientation-token cost. Triggers: knowledge graph, graphify, code graph, god nodes, orientation cost, token bill, map the codebase, what connects X to Y, callers of, blast radius."
allowed-tools: Read, Bash, Grep, Glob
kernel:
  kind: methodology
  version: 1
  side_effects: filesystem
  confirmation: none
---

<skill id="knowledge-graph">

<purpose>
An agent's token bill splits into ORIENTATION (finding where the answer lives — reading
files, following imports, grepping) and REASONING (actually solving). On a large, tangled
repo the orientation half dominates, and it is pure overhead: the model is not thinking yet,
it is still navigating. A pre-built code knowledge graph replaces that file-crawl with one
query, so you pay orientation tokens once (at build) instead of every session.

The saving is CONDITIONAL on repo size × tangle, not a fixed multiplier. Measured on real
repos: ~5.7x fewer tokens/query on a mid-size service, ~73x on a large interconnected one,
~13% on a tiny library. The graph query cost is ~constant; naive full-corpus cost scales with
size — so reduction = corpus ÷ constant. Do the arithmetic on YOUR repo, don't quote a headline.

Hard boundary: the graph helps NAVIGATION, not REASONING. "Design a cache", "why is this slow"
get zero lift. It gathers context efficiently; it does not think for the model.
</purpose>

<prerequisite>
Uses `graphify` (open-source, tree-sitter + NetworkX, MIT). Code extraction is local +
deterministic + free (no API key). Install once: `uv tool install graphifyy` (or `pipx`/`pip`).
If graphify is absent, this skill degrades to a no-op — never a hard failure.
</prerequisite>

<build>
Code-layer graph (free, offline, seconds):
```bash
graphify extract <path> --code-only        # local AST only; skips docs; no LLM, no cost
```
Outputs `graphify-out/graph.json` (+ report; +interactive graph.html under ~5000 nodes).
NEVER commit `graphify-out/` — it is DERIVED. Gitignore it and rebuild on demand
(the sqlite-mirror discipline: commit the source, rebuild the artifact).
</build>

<query>
```bash
graphify query "what connects auth to the database?"      # BFS over the graph, token-budgeted
graphify path "UserService" "DatabasePool"                # shortest path between two symbols
graphify god-nodes --top 12                                # architectural hubs (most-connected)
graphify affected "RateLimiter"                            # reverse traversal = change blast radius
graphify benchmark                                         # measure YOUR token reduction, per question
```
`god-nodes` doubles as a comprehension + pruning lens: hubs are the real spine; low-degree,
never-linked nodes are dead-code / consolidation candidates. Also available as an MCP server
(`query_graph`, `shortest_path`, `get_neighbors`) for repeated structured access.
</query>

<automatic>
The graph pays off only if it is CONSULTED. A skill telling the agent to reach for it is opt-in
and unreliable, so the orientation layer is AMBIENT: when the working repo has a graph, the
session-start hook injects its architectural spine (top god-nodes + the query commands) directly
into context — the agent boots already oriented, no tool call, no human ask. Deep on-demand
queries ("what calls this exact function") still go through `graphify query`/`path`/`affected`
or the MCP tools; those are available + steered, but the baseline map arrives for free.
</automatic>

<continuous>
A stale graph is worse than none. Keep it fresh, cheaply:
- **Code layer (free):** `graphify extract <path> --code-only` is incremental via its AST cache
  ("N cached/unchanged, 0 re-extracted"). Wire it into `post-commit` so the graph is never more
  than one commit stale, at ~zero cost. Opt-in installer: `hooks/scripts/knowledge-graph.sh install`
  (gated on `KERNEL_GRAPH_ON=1`, mirroring autopush — never stamps hooks by surprise).
- **NEVER `graphify update`** for the code graph: it re-scans ALL files and adds docs as bare
  nodes (measured 1506 → 13156 on one tree). Always `extract --code-only`.
- **Doc/semantic layer** (summaries, tags, prose edges) needs a model and is OPTIONAL polish.
  Run it incrementally (changed files only), never full-corpus, never on every commit. Local
  models are "good enough for orientation, not a top-tier artefact"; a frontier model is sharper.
</continuous>

<boundaries>
- Free + deterministic is the CODE layer only. The doc/paper/image "why" layer sends semantic
  descriptions (never raw source) to a configured backend — that costs a model.
- Small or reasoning-heavy repos: the graph is a solved problem you did not have. Skip it.
- The graph is a comprehension artefact that also saves tokens — value it as a map first.
</boundaries>

</skill>
