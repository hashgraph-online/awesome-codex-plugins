---
name: inject
description: 'Load relevant .agents context.'
---
> **DEPRECATED (removal target: v3.0.0)** — Use `ao lookup --query "topic"` for on-demand learnings retrieval and `ao context assemble` for phase-scoped context packets. This skill and the `ao inject` CLI command still work as compatibility adapters, but they are not the canonical context path and are not called from default hooks or other skills.

# Inject Skill

**On-demand knowledge retrieval. Not run automatically at startup (since ag-8km).**

Load relevant prior knowledge into the current session as a legacy adapter.
Treat `$inject` as passive compatibility lookup, not as a task-planning or task-execution entrypoint.

## Lease

| Field | Value |
|---|---|
| Lease | retire-candidate |
| Replacement port | `retrieve_context` / `assemble_context` |
| Replacement adapters | `ao lookup`, `ao context assemble`, knowledge brief artifacts |
| Current allowed use | manual compatibility lookup only |
| Not allowed | default startup injection, hidden hook delivery, task planning |

## How It Works

In the default `manual` startup mode, MEMORY.md is auto-loaded by Codex and no startup injection occurs. Prefer `ao lookup` for on-demand retrieval and `ao context assemble` when a phase needs a bounded packet. Use `$inject` or `ao inject` only for legacy compatibility.

In `lean` or `legacy` startup modes (set via `AGENTOPS_STARTUP_CONTEXT_MODE`), the SessionStart hook runs:
```bash
# lean mode (MEMORY.md fresh): 400 tokens
ao inject --apply-decay --format markdown --max-tokens 400 \
  [--bead <bead-id>] [--predecessor <handoff-path>]

# legacy mode: 800 tokens
ao inject --apply-decay --format markdown --max-tokens 800 \
  [--bead <bead-id>] [--predecessor <handoff-path>]
```

This legacy path searches for relevant knowledge and prints a bounded summary.

### Work-Scoped Injection

When `--bead` is provided (via `HOOK_BEAD` env var from Gas Town):
- Learnings tagged with the same bead ID get a 1.5x score boost
- Learnings matching bead labels get a 1.2x boost
- Untagged learnings still appear but ranked lower

### Predecessor Context

When `--predecessor` is provided (path to a handoff file):
- Extracts structured context: progress, blockers, next steps
- Injected as "Predecessor Context" section before learnings
- Supports explicit handoffs, auto-handoffs, and pre-compact snapshots

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

Read the most relevant artifacts based on topic.

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

### SessionStart Hook Invocation (lean/legacy modes only)

**Hook triggers:** `session-start.sh` runs at session start with `AGENTOPS_STARTUP_CONTEXT_MODE=lean` or `legacy`

**What happens:**
1. Hook calls `ao inject --apply-decay --format markdown --max-tokens 400` (lean) or `--max-tokens 800` (legacy)
2. CLI searches `.agents/learnings/`, `.agents/patterns/`, `.agents/research/` for relevant artifacts
3. CLI applies recency-weighted decay (~17%/week) to rank results
4. CLI outputs top-ranked knowledge as markdown within token budget
5. Agent presents injected knowledge in session context

**Result:** Prior learnings, patterns, and research are available for legacy hook profiles. This is not the default AgentOps 3.0 path.

**Note:** In the default `manual` mode, MEMORY.md is auto-loaded by Codex and this hook emits only a pointer to on-demand retrieval commands (`ao search`, `ao lookup`).

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
| Irrelevant knowledge | Topic mismatch or stale artifacts dominate | Use `--context "<topic>"` to filter; prune stale artifacts |
| Token budget exceeded | Too many high-relevance artifacts | Reduce `--max-tokens` or increase topic specificity |
| Decay too aggressive | Recent learnings not prioritized | Check artifact modification times; verify `--apply-decay` flag |

## Local Resources

### scripts/

- `scripts/validate.sh`
