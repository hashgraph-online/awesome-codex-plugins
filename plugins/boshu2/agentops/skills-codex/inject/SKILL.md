---
name: inject
description: Load relevant .agents context.
---
> **RETIRED CLI (memory-moat removal Phase 1b, age-abev)** — the ao inject CLI command was removed in Phase 1b; `cm`/`cass` + `ao lookup` own retrieval now. Use `ao lookup --query "topic"` for on-demand learnings retrieval and phase-scoped context packets. This skill survives only as a manual-retrieval / knowledge-activation adapter routed onto `ao lookup` + the `ao knowledge` family; it is not the canonical context path and is not called from default hooks or other skills.

# Inject Skill

## Install & refresh (absorbed from using-agentops, ag-s43tg)

**To update installed skills:** re-run the install one-liner — `bash <(curl -fsSL https://raw.githubusercontent.com/boshu2/agentops/main/scripts/install.sh)`. (There is no update skill; skill refresh is an install-script concern.)

**On-demand knowledge retrieval. Not run automatically at startup (since ag-8km).**

It is read-only: it only reads knowledge for injection and never writes to `.agents/`.

Load relevant prior knowledge into the current session as a legacy adapter.

## Lease

| Field | Value |
|---|---|
| Lease | retire-candidate |
| Replacement port | `retrieve_context` / `assemble_context` |
| Replacement adapters | `ao lookup`, knowledge brief artifacts |
| Current allowed use | manual compatibility lookup only |
| Not allowed | default startup injection, hidden hook delivery, task planning |

## Folded triggers (ag-s43tg wave 1): `session-bootstrap` + `using-agentops` route here

- **`session-bootstrap` → `ao session bootstrap`.** The Universal AgentOps init prompt
  for starting or onboarding a fresh agent session is the `ao session bootstrap`
  orientation report — run it first, then pull decay-ranked context on demand with
  `ao lookup`.
- **`using-agentops` → this skill** (skill dir removed; embedded CLI copy retired with
  it). Use when asked to Explain AgentOps workflows: start with `ao session bootstrap`
  for orientation, then walk the on-demand surfaces here (`ao lookup`,
  `ao knowledge brief`) for the workflow tour.

Codex skill orchestration default is `$skill` chaining. Terminal CLI
commands are compatibility adapters unless a workflow explicitly names the CLI
as the execution surface.

## How It Works

In the default hookless startup path, no startup injection occurs. Run `ao session bootstrap` for the standard orientation report, then pull context on demand with `ao lookup`. The `$inject` trigger is a legacy alias that routes to `ao lookup`.

On-demand retrieval is `ao lookup`:
```bash
ao lookup --query "<topic>" --limit 5     # top matches by relevance
ao lookup --bead <bead-id>                # learnings from a bead's lineage
ao lookup <artifact-id>                    # one artifact by ID
```

`ao lookup` searches the learnings / patterns / sessions corpus and returns a bounded, recency-weighted summary. (The legacy `ao inject` CLI — token-budgeted markdown injection, `--predecessor` handoff context, SessionStart-hook delivery — was retired in Phase 1b; `ao session bootstrap` + `ao lookup` cover orientation and on-demand retrieval.)

## Manual Execution

Given `$inject [topic]`:

### Step 1: Search for Relevant Knowledge

**With ao CLI:**
```bash
ao lookup --query "<topic>" --limit 5
```

**Without ao CLI, search manually:**
```bash
# Global operating memory
sed -n '1,120p' ~/.agents/MEMORY.md 2>/dev/null

# Recent learnings
ls -lt .agents/learnings/ | head -5

# Recent patterns
ls -lt .agents/patterns/ | head -5

# Recent research
ls -lt .agents/research/ | head -5

# Global learnings (cross-repo knowledge)
ls -lt ~/.agents/learnings/ 2>/dev/null | head -5

# Global patterns (cross-repo patterns)
ls -lt ~/.agents/patterns/ 2>/dev/null | head -5

# Legacy patterns (read-only fallback, no new writes)
ls -lt ~/.codex/patterns/ 2>/dev/null | head -5
```

### Step 2: Read Relevant Files

Use the Read tool to load the most relevant artifacts based on topic.

### Step 3: Summarize for Context

Present the injected knowledge:
- Global principles or constraints that apply everywhere
- Key learnings relevant to current work
- Patterns that may apply
- Recent research on related topics

### Step 4: Record Citations (Feedback Loop)

After presenting injected knowledge, record which files were injected for the feedback loop:

```bash
mkdir -p .agents/ao
# Record each injected learning file as a citation
for injected_file in <list of files that were read and presented>; do
  echo "{\"artifact_path\": \"$injected_file\", \"cited_at\": \"$(date -Iseconds)\", \"session_id\": \"$(date +%Y-%m-%d)\", \"workspace_path\": \"$PWD\"}" >> .agents/ao/citations.jsonl
done
```

Citation tracking enables the feedback loop: learnings that are frequently cited get confidence boosts during `$post-mortem`, while uncited learnings decay faster.

## Knowledge Sources

| Source | Location | Priority | Weight |
|--------|----------|----------|--------|
| Global Memory | `~/.agents/MEMORY.md` | Highest | 1.0 |
| Learnings | `.agents/learnings/` | High | 1.0 |
| Patterns | `.agents/patterns/` | High | 1.0 |
| Global Learnings | `~/.agents/learnings/` | High | 0.8 (configurable) |
| Global Patterns | `~/.agents/patterns/` | High | 0.8 (configurable) |
| Research | `.agents/research/` | Medium | — |
| Retros | `.agents/learnings/` | Medium | — |
| Legacy Patterns | `~/.codex/patterns/` | Low | 0.6 (read-only, no new writes) |

## Decay Model

Knowledge relevance decays over time (~17%/week). More recent learnings are weighted higher.

## Key Rules

- **Does not run automatically** - default context delivery is explicit
- **Context-aware** - filters by current directory/topic
- **Token-budgeted** - respects max-tokens limit
- **Recency-weighted** - newer knowledge prioritized

## Examples

### Manual Context Injection

**User says:** `$inject authentication` or "recall knowledge about auth"

**What happens:**
1. Agent calls `ao lookup --query "authentication" --limit 5`
2. CLI filters artifacts by topic relevance
3. Agent reads top-ranked learnings and patterns
4. Agent summarizes injected knowledge for current work
5. Agent references artifact paths for deeper exploration

**Result:** Topic-specific knowledge retrieved and summarized, enabling faster context loading than full artifact reads.

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| No knowledge injected | Empty knowledge pools or ao CLI unavailable | Run `$post-mortem` to seed pools; verify ao CLI installed |
| Irrelevant knowledge | Topic mismatch or stale artifacts dominate | Use `ao lookup --query "<topic>"` to filter; prune stale artifacts |
| Too many results | Too many high-relevance artifacts | Reduce `ao lookup --limit` or increase topic specificity |
| Decay too aggressive | Recent learnings not prioritized | Check artifact modification times (recency-weighted scoring is applied automatically) |

## Knowledge Activation (merged from `knowledge-activation`, cp-auc)

`inject` and `ao lookup` *retrieve* knowledge for the current session. **Activation** is the complementary capability — folded in here from the former `knowledge-activation` skill — that *operationalizes* a mature `.agents` corpus into durable operator surfaces (beliefs, playbooks, briefings, gaps). Where `inject` reads, activation promotes; the two are the read and write-to-surface halves of the same flywheel. Activation is the **fourth step** of the global-corpus workflow:

1. `$curate --mode=harvest` — gather artifacts from many rigs into `~/.agents/learnings/`
2. `$compile` — synthesize raw artifacts into `.agents/compiled/`
3. *(optional)* `$curate --mode=dream` overnight — bounded compounding loop
4. **knowledge activation** — lift compiled knowledge into playbooks, beliefs, and runtime briefings

`$compile` remains the hygiene loop; activation owns corpus operationalization. Use it when the problem is no longer "capture more knowledge" but: promote the strongest recurring claims into a belief system, turn healthy topics into reusable playbooks, compile a small goal-time briefing, and surface thin topics and promotion gaps before they calcify.

### Command Contract

The stable product surface is the `ao knowledge` command family:

```bash
ao knowledge activate --goal "turn agents into usable information"  # full outer loop
ao knowledge beliefs                                                # refresh belief book only
ao knowledge playbooks                                              # refresh candidate playbooks
ao knowledge brief --goal "fix auth startup"                       # goal-time briefing
ao knowledge gaps                                                   # thin topics, promotion gaps, weak claims, next work
```

`ao` owns the belief/playbook/brief/gap product surfaces directly; the skill owns routing, sequencing, interpretation, and next-step recommendations. `ao lookup` and `ao codex start` consume these outputs as operator context — matched briefings are the preferred dynamic startup surface, while selected beliefs and healthy playbooks provide bounded supporting guidance. When a retrieved briefing, belief, or playbook changes a recommendation, record it with `ao metrics cite "<path>" --type applied 2>/dev/null || true` (use `--type retrieved` for loaded-but-unused context).

### Activation Steps

1. **Preflight** — verify `.agents/` exists. To run `ao knowledge activate`, verify at least one evidence substrate is present: packet builders (`source_manifest_build.py`, `topic_packet_build.py`, `corpus_packet_promote.py`, `knowledge_chunk_build.py`) under `.agents/scripts/`; or the harvest fallback `.agents/harvest/latest.json`; or the native operator surfaces (`ao knowledge beliefs|playbooks|brief|gaps`).
2. **Consolidate evidence** — run packet layers in order: source manifests → topic packets → promoted packets → historical chunk bundles. See [references/knowledge-activation-dag.md](references/knowledge-activation-dag.md) for the full DAG and its trust gates.
3. **Distill operator surfaces** — `ao knowledge beliefs` then `ao knowledge playbooks` materialize consumer surfaces under `.agents/knowledge/` and `.agents/playbooks/`.
4. **Compile a goal-time briefing** — when there is an active objective: `ao knowledge brief --goal "..."`. Keep it small, cite source surfaces, warn when a selected topic is thin.
5. **Surface gaps** — `ao knowledge gaps` reports thin topics, missing promotions, weak claims needing review, and the next recommended mining work.
6. **Full outer loop** — `ao knowledge activate --goal "..."` sequences evidence consolidation, belief/playbook refresh, optional briefing compilation, and a gap summary in one pass.

### Activation Trust Rules

- packetization is substrate, not the product
- beliefs, playbooks, and briefings are the real operator surfaces
- thin topics stay discovery-only until evidence improves
- every generated surface should name its consumer
- repeated unchanged runs should stay structurally deterministic

### Activation Output Surfaces

Consumer-facing outputs: `.agents/knowledge/book-of-beliefs.md`, `.agents/playbooks/index.md`, `.agents/playbooks/<topic>.md`, `.agents/briefings/YYYY-MM-DD-<goal>.md`, `.agents/retro/`. Substrate surfaces: `.agents/packets/`, `.agents/topics/`, `.agents/packets/chunks/catalog.jsonl`. See [references/knowledge-activation-output-surfaces.md](references/knowledge-activation-output-surfaces.md) and [references/knowledge-activation-script-contracts.md](references/knowledge-activation-script-contracts.md) for trust boundaries and the builder inventory.

## Reference Documents

- [references/knowledge-activation.feature](references/knowledge-activation.feature) — Executable spec: consolidate evidence, distill beliefs/playbooks, compile goal-time briefing, surface gaps (soc-qk4b)
- [references/knowledge-activation-dag.md](references/knowledge-activation-dag.md) — DAG and trust gates for evidence consolidation
- [references/knowledge-activation-output-surfaces.md](references/knowledge-activation-output-surfaces.md) — canonical activation output surfaces and trust boundaries
- [references/knowledge-activation-script-contracts.md](references/knowledge-activation-script-contracts.md) — builder inventory and `ao knowledge` command ownership
