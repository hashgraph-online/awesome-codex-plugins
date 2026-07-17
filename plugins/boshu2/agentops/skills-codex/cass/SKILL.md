---
name: cass
description: Mine past agent sessions for working
---
# cass Session Search

> **Core Insight:** Your repeated prompts are your best prompts. If you typed it 10+ times, it works. Mine your history.

`cass` is an upstream (Dicklesworthstone) tool and is **self-describing** — do not re-learn its surface from this skill. Discover it live:

```bash
cass capabilities --json      # features/connectors/limits of the installed binary
cass introspect --json        # full schema of every command + response
cass robot-docs guide|commands|examples|schemas|contracts   # machine-targeted docs
```

This skill carries only the AgentOps operating doctrine: when to reach for cass, the discovery workflow, the recovery posture, and the anti-patterns we have actually hit.

## Constraints

- Never run bare `cass` because it launches a blocking TUI; use a JSON, robot, or explicit file-output command.
- Treat a stale index as searchable and refresh it with a bounded background command because stale is not broken and an unbounded rebuild can stall the lane.
- Preserve source sessions and require explicit permission for destructive cleanup; recovery may rebuild only derived index state.

## When to Use

- "What did I ask last time?" / "find that prompt that worked" — session archaeology
- Prior-art check before inventing a new approach, plan, or prompt
- Scope archaeology: "when did we decide NOT to do X?"
- Post-context-loss recovery: what was searched for after a crash = what mattered

### Folded triggers (ag-s43tg wave 1): `casr` + `cass-memory` route here

- **`casr` → cross-harness resume.** Cross Agent Session Resumer: convert and resume sessions across Claude Code, Codex, Gemini, and other providers — `cass resume` plus [RESUME.md](references/RESUME.md) own this lane (resolve subagent logs to their parent via `cass context` first; subagent files are not resumable).
- **`cass-memory` → `cm` procedural memory.** Use when starting non-trivial work, mining lessons, or preventing repeated mistakes with cm procedural memory — mine past sessions here first, then promote the durable lessons through `cm` instead of re-deriving them each session.

## The Goldmine Principle

Your conversation history contains:
- **Refined prompts** — Every rephrase that worked better was captured
- **Working rituals** — Prompts repeated 10+ times ARE your methodology
- **Scope decisions** — "When did we decide NOT to do X?"
- **Recovery moments** — What you searched for after context loss = what mattered

**The insight:** Mining your past beats inventing new approaches. In the AgentOps loop the goal is prior-art first: mine as a research-phase move before writing a fresh plan or prompt, and feed what you find back into the corpus instead of re-deriving it.

## History-First Routing

Before deriving a plan, prompt, or approach from scratch, run one bounded
search of past sessions (one query family, `--fields minimal`, a real
`--limit`, under a minute of wall clock). Three outcomes, each with its own
routing:

- **Direct hit** — a prior session solved this. Reuse its prompt or decision;
  cite `source_path` and line in whatever you build on it.
- **Adjacent hit** — prior work borders the problem. Extract the working
  fragments, then derive only the missing part fresh.
- **Verified absence** — zero hits after retrying against discovered workspace
  keys (`--aggregate workspace`). Now derivation is justified, and the absence
  itself is worth noting: you are in new territory, so budget accordingly.

The named failure mode is re-derivation drift: solving the same problem
slightly differently each session, so the corpus accumulates near-duplicate
approaches and no single one ever hardens into a ritual. Stop condition for
the history pass itself: one query family exhausted or a direct hit found —
history search is a bounded pre-step, not an open-ended excavation that
displaces the actual task.

## Lesson Weighting: Decay and Failure Overweight

Mined lessons are evidence with a shelf life, not doctrine:

- **Confidence decays with corpus drift.** Weight a mined lesson by what has
  changed since it was captured, not by calendar age alone. A lesson about a
  tool surface or repository that has since moved is a hypothesis to re-verify
  — one probe against the current surface — before it steers a fresh plan. A
  lesson about durable method (how to decompose, how to verify) decays far
  more slowly. Never carry a stale-surface lesson forward at its original
  confidence; the named failure mode is fossil doctrine — a dead workaround
  reapplied for months because it once worked and nobody re-checked.
- **Overweight failures.** A session where an approach failed is worth more
  than a session where one worked: successes are overrepresented in what gets
  polished and remembered, while failures encode the boundary of validity.
  When mining prior art for an approach, explicitly search for its failures
  ("didn't work", "reverted", "gave up", error strings) before adopting it. A
  hit showing the approach failing in circumstances like yours outranks three
  hits showing it succeeding elsewhere.

## THE EXACT PROMPT — Discovery Workflow

```
1. Bootstrap: Check health, refresh index, get project overview
   cass status --json && cass index --json
   cass search "*" --workspace /data/projects/PROJECT --aggregate agent,date --limit 1 --json

2. Find prompts: Search for keywords, filter to user prompts (lines 1-3)
   cass search "KEYWORD" --workspace /data/projects/PROJECT --json --fields minimal --limit 50 \
     | jq '[.hits[] | select(.line_number <= 3)]'

3. Follow hits: View the actual content
   cass view /path/from/source_path.jsonl -n LINE -C 20

4. Expand context: See the full conversation flow
   cass expand /path/from/source_path.jsonl --line LINE --context 3

5. Discover related: Find the whole work cluster
   cass context /path/from/source_path.jsonl --json
```

Why it works: aggregations first (know the terrain), `--fields minimal` (5x smaller output), `line_number <= 3` (user prompts live at the top), context clustering (one good hit → many related sessions). >10 matches for a prompt = a ritual; document and reuse it.

## Operating Doctrine: Stale ≠ Broken

Three index states matter — never conflate them:

| State | Meaning | Do |
|-------|---------|----|
| `cass health` exit 0 | Healthy | Search immediately |
| stale (`index.stale=true`) | Usable but old | Search NOW; refresh in background with a wall-clock cap: `( timeout 600 cass index --json &>/tmp/cass-bg.log </dev/null & )` — NEVER a bare `&`, cass index can hang |
| broken (`database.exists=false` or `documents=0`) | Truly uninitialized | `cass doctor --fix --json`, then `cass index --full --json` |

The trap: treating stale as broken triggers an unneeded 8–25s full rebuild when a 1–3s incremental (or a stale-but-correct query) would do. `scripts/recover.sh` implements the full decision tree with timeouts. Detailed symptom→fix tables (issue #196 hang, stale locks, `database is busy` race, etc.): [RECOVERY.md](references/RECOVERY.md), [OBSERVABILITY.md](references/OBSERVABILITY.md), [PITFALLS.md](references/PITFALLS.md).

### Incremental refresh can become authoritative

An invocation requested as `cass index --json` may discover that incremental
state cannot be reconciled and expand into an authoritative rebuild over the
full conversation corpus. A large total or a longer run is evidence of recovery
mode, **not evidence that source sessions were lost**. Do not start a second
indexer or report a zero-result search while the first call is still converging.

Concurrent status and search reads can exceed their normal latency during that
rebuild. Bound observations with a wall-clock timeout, retain the exit status,
and distinguish timeout from an empty result:

```bash
status_rc=0
timeout 15 cass status --json > /tmp/cass-status.json || status_rc=$?
# Exit 124 means status was not observed within the cap.

search_rc=0
timeout 30 cass search "QUERY" --json --fields minimal --limit 20 \
  > /tmp/cass-search.json || search_rc=$?
# Exit 124 is NOT zero hits; retry after the rebuild settles.
```

If status returns, inspect `.rebuild.active`, `.rebuild.phase`,
`.rebuild.processed_conversations`, `.rebuild.total_conversations`, and
`.rebuild.updated_at`. When `updated_at` or processed count advances, wait for
that bounded run rather than stacking recovery. If a bounded read times out,
report only that the read was not observed within the cap and keep the last
known freshness; do not infer corruption or data loss. See
[OBSERVABILITY.md](references/OBSERVABILITY.md#authoritative-fallback-and-concurrent-read-latency).

## Version Pinning

cass evolves quickly; the released binary may lack HEAD features. When a flag returns "unrecognized", do not guess — probe: `cass capabilities --json` and `cass introspect --json | jq '.commands[].name'`, and check `cass --version`.

## Anti-Patterns (Don't Do These)

| Anti-pattern | Why it's wrong | Do instead |
|--------------|----------------|------------|
| Asking the user "should I rebuild the index?" | They have agents waiting; rebuild is safe and idempotent | Just run `cass doctor --fix --json` (preserves source data) |
| Running `cass index --full` whenever `status` says unhealthy | A 25s rebuild for a 30-min stale index is wasteful | Check `index.stale` separately from `database.exists`; prefer incremental |
| Running bare `cass` to "see what's there" | Launches blocking TUI in the agent's session | Always `--json` or `--robot`; never bare |
| Piping `cass export` into `head`/`jq` | Broken-pipe panic on large sessions | `cass export ... -o /tmp/x.json` first, then operate on the file |
| Treating subagent files as parent sessions | Subagents are separate logs with their own line-2 prompt; also NOT resumable | Filter by `select(.source_path \| contains("subagent"))`; resolve to parent via `cass context` before `cass resume` |
| Using `--limit 0` for "no limit" | Earlier cass panics | Use a real limit (`--limit 50`); `--limit 1` minimum for aggregations |
| Trusting 0 hits with `--workspace /X` | Workspace strings are case- and trailing-slash-sensitive | Re-run with `--aggregate workspace --limit 1` to discover the canonical key |
| Skipping `--fields minimal` on wide scans | ~3KB per hit × 100 hits = 300KB context burn | `--fields minimal` for wide passes; upgrade to `summary`/`full` for keepers |
| Reading session files with `cat` | Loads the full conversation into context | `cass view PATH -n LINE -C 5` or `cass expand PATH --line LINE --context 3` |
| Re-indexing on every search | Index is shared across processes | Refresh only when `status` says stale |
| Treating a timed-out search during rebuild as 0 hits | Concurrent reads may exceed normal latency while an authoritative rebuild holds shared resources | Preserve exit 124 as "not observed" and retry once the active rebuild settles |
| Falling back to manual `find`/`grep` when cass misbehaves | Recovery is autonomous; skipping cass loses the corpus | Walk the recovery tree in [RECOVERY.md](references/RECOVERY.md). One real exception: terms inside tool stdout/stderr are skipped at index time — there `rg -n "TERM" /path.jsonl` is correct |

Long-form versions with mined evidence: [ANTI_PATTERNS.md](references/ANTI_PATTERNS.md).

## Safety Boundaries

Pre-authorized (rebuilds derived index data only, never destroys source sessions): `cass doctor --fix --json`, `cass index --full --force-rebuild --json`, `cass sources doctor/sync`, `cass models install/verify`.

Do NOT without explicit permission: delete `core.NNNNN` coredumps, delete `.beads/`, `git reset --hard`, or hand-edit `~/.config/cass/sources.toml` — the CLI commands above already do everything safely. Never run bare `cass` (blocking TUI) inside an agent loop.

## Reference Index

| Need | Reference |
|------|-----------|
| Full command reference | [COMMANDS.md](references/COMMANDS.md) |
| Workflow recipes | [RECIPES.md](references/RECIPES.md) |
| jq patterns | [PATTERNS.md](references/PATTERNS.md) |
| Pitfalls & fixes | [PITFALLS.md](references/PITFALLS.md) |
| Session file formats | [SESSION_FORMATS.md](references/SESSION_FORMATS.md) |
| Remote sources, multi-machine search | [REMOTE_SOURCES.md](references/REMOTE_SOURCES.md) |
| Semantic / hybrid / models | [SEMANTIC_AND_HYBRID.md](references/SEMANTIC_AND_HYBRID.md) |
| Token / tool / model analytics | [ANALYTICS.md](references/ANALYTICS.md) |
| Cross-harness session resume | [RESUME.md](references/RESUME.md) |
| Doctor + autonomous recovery | [RECOVERY.md](references/RECOVERY.md) |
| Mined gold-standard prompts | [PROMPTS.md](references/PROMPTS.md) |
| Anti-patterns (long form) | [ANTI_PATTERNS.md](references/ANTI_PATTERNS.md) |
| Health vs status vs index nuance | [OBSERVABILITY.md](references/OBSERVABILITY.md) |
| Pages encrypted archive + HTML export | [PAGES_AND_EXPORT.md](references/PAGES_AND_EXPORT.md) |
| Harness exclusion (`disabled_agents`) | [HARNESS_EXCLUSION.md](references/HARNESS_EXCLUSION.md) |
| Schema introspection contracts | [INTROSPECTION.md](references/INTROSPECTION.md) |

When the right reference isn't obvious from titles, `grep -ni "SYMPTOM" references/*.md` — cheaper than loading whole files into context.

## Scripts

Scripts live under `scripts/`. They execute, never load — zero context tokens. None mutate state without explicit confirmation.

| Script | Usage |
|--------|-------|
| `./scripts/quick_analysis.sh /path` | One-command project overview (status → aggregate agent/date → top prompts) |
| `./scripts/prompt_miner.py --workspace /path` | Find repeated prompts (ritual detection) |
| `./scripts/validate.sh` | Validate cass install + skill structure |
| `./scripts/recover.sh` | Autonomous recovery decision tree (READY → STALE_BUT_USABLE → BROKEN); wraps every `cass index` in `timeout` |
| `./scripts/multi_machine_search.sh "QUERY" [host…]` | Parallel fan-out across the fleet; merges + dedups hits |

## Validation

```bash
# Quick health check
cass status --json | jq '.index.fresh'

# Should return: true
```

If `false`, run: `cass index --json`

## Output Specification

- **Path:** stdout for search, status, capability, and introspection results; this skill creates no artifact directory by default.
- **Filename:** none unless the caller explicitly requests an export path such as `/tmp/cass-export.json` with `-o`.
- **Format:** use the installed command's JSON schema from `cass introspect --json`; wide searches should keep `--fields minimal` and downstream narrowing must preserve `source_path` and line location.
- **Exit code:** validate with `cass status --json | jq -e .` and parse every selected result with `jq`; a nonzero command, malformed JSON, or unresolved source path blocks the handoff.
- **Downstream handoff:** consumed by research, planning, recovery, or postmortem work with the exact query, canonical workspace, selected source paths/lines, and index freshness noted.

## Quality Checklist

- Results come from a canonical workspace key and include enough source location to reopen the session context.
- A zero-hit result was retried against discovered workspace keys before concluding that no prior art exists.
- Index recovery stayed bounded and preserved source sessions; no stale state was misreported as broken.
