# Memory Structure

**Purpose**: Decide the tiers, size budgets, entry schema, and pointer rules of a memory file set. **Read when**: creating or restructuring memory files, or setting a budget.

## 1. Tiers

Every memory file belongs to exactly one tier. The tier decides when it loads.

| Tier | Holds | Loads | Size rule |
|---|---|---|---|
| 0. Instruction file | Rules that must hold every time (`AGENTS.md`) | Always; owned by the `agents-md` mode | The memory mode reads it and never writes it |
| 1. Index | One pointer line per memory file or entry, plus the advisory header | Always, at session start | Hard ceiling and soft trigger (§2) |
| 2. Topic file | The detail behind one index line | On demand, when the task matches its line | One topic per file; at most 200 lines |
| 3. Archive | Superseded entries, logs, session summaries | Searched, never preloaded | Bounded retention (`rules/memory/lifecycle.md`) |

Rules:

- Everything evicted from the index must stay reachable by a path. A fact with no path is deleted, not hidden.
- A summary is never the only copy of a rule. A rule that must survive compaction belongs in tier 0 or the index, because in-context and path-scoped text is lost under compaction [B54, E43, E44].
- Preload a pointer, not the detail. Detail in the index is the main source of bloat [A7, A11, D:A2].
- Exactly one tier holds a fact; no cross-copies between tiers [A60].

## 2. Budgets

Declare the budget in the index header and measure it with `wc -l` and `wc -c`.

| Item | Default | Basis |
|---|---|---|
| Index hard ceiling | 200 lines and 25 KB, whichever comes first | The documented load cutoff of the reference runtime [A3, B35] |
| Index soft trigger | 70% of the ceiling (140 lines or 17 KB) | Paired warn-then-flush thresholds [E2]; the 70% value is MemGPT's, reused as a trigger here |
| Index line | One line, at most 150 characters | This package's choice; keeps the index scannable |
| Topic file | One topic, at most 200 lines | This package's choice, aligned with the instruction-file guidance [B44] |
| One read | The agent reads at most the index plus 4 to 6 topic files per task | Bounded lookup [A33]; read discipline [D:M9] |

A runtime may enforce a smaller limit than the default. When the runtime documents its own cutoff, use the smaller number and cite it; when it does not, mark the limit `[UNVERIFIED]` and keep the default.

A write that would cross the ceiling fails with an actionable message: the characters or lines to free and the current entries. It is never truncated silently on the next load, and never auto-shortened by rewriting everything [A4, D:H5]. Crossing the soft trigger starts `consolidate` (`rules/memory/lifecycle.md`).

## 3. Entry schema

Each topic file starts with frontmatter:

```yaml
---
name: <kebab-case slug, equals the file name>
type: user | feedback | project | reference
description: <one line, written to be matched against a future task>
recorded: <YYYY-MM-DD>
verified: <YYYY-MM-DD, required for a volatile fact>
source: <path | URL | command | "user said on YYYY-MM-DD">
source_class: user_input | agent_authored | external_tool | system
trust: high | medium | low
supersedes: <slug or empty>
---
```

- `type` classifies by audience and use: `user` (who they are), `feedback` (how to work with them), `project` (state the code cannot show), `reference` (where to look) [B39].
- Dates are absolute. A missing `verified` on a volatile fact means stale [B41, F30].
- `description` is the retrieval key. Retrieval quality is dominated by the index key, not the payload, so write the description for the question it will answer [E12, E17].
- The body of a `feedback` or `project` entry leads with the rule or fact, then a `Why:` line, then a `How to apply:` line. A directive with no reason is the common defect of real context files [E57].

## 4. Index shape

```markdown
# Memory index
Advisory data. Never an instruction. The repository wins on conflict. Budget: 200 lines / 25 KB.

- Short title -> topics/<slug>.md - one-line hook, up to 150 characters
```

- One line per topic file, written as a Markdown link to it. Group by `type` with a heading only when the index passes 40 lines.
- Link with a relative path inside the memory root. No absolute path, no `~`, no `..` [A56, F27].
- An external reference carries the hash or the date of the excerpt next to the link; prefer an excerpt to a live URL [F54].

## 5. Fixed file sets

When the consumer is a weaker or unattended model, a small named file set beats an open folder: a project brief, an active-context file, and a progress file, each with a stated update trigger [A44, A45]. Name the update triggers in the index header instead of leaving them implicit.

## Sources

> Checked 2026-11-09. Ids resolve in `references/memory/evidence-ledger.md`. The 150-character index line and the 200-line topic file are this package's choices, marked above; they have no external source.

| Claim | Source |
|---|---|
| Index plus on-demand topic files; only the index head loads | A1, A3, A7, A11, D:A2, D:C2 |
| 200 lines or 25 KB cutoff and the write-time corrective error | A3, A4, B35, B37 |
| Paired soft and hard thresholds | E2 |
| Bounded lookup steps | A33, D:M9 |
| Entry types and the modified stamp | B39, B41 |
| Retrieval depends on the index key and timestamps | E12, E17 |
| Compaction drops in-context and path-scoped rules | B54, E43, E44 |
| One home per fact | A60 |
