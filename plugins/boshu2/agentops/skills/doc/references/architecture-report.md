# Codebase Report

> **Core Insight:** Understanding is ephemeral. Documents survive context compaction.

## The Problem

You explore a codebase, build a mental model, then context compacts. When the
caller asks for a persisted codebase report, this reference shapes it.

**Scope:** answering how the code works needs no document; write this report
only when the caller requests one (see [Doc](../SKILL.md#grounded-writing) step 5).

---

## THE EXACT PROMPT

```
Produce a Comprehensive Technical Architecture Report for this codebase:

1. Executive summary (what is it, key stats)
2. Entry points (main, routes, handlers)
3. Key types (3-5 core domain objects)
4. Data flow (input → processing → output)
5. External dependencies (DBs, APIs, critical libs)
6. Configuration (env, files, CLI, precedence)
7. Test infrastructure

Include file:line references. Output as markdown I can reference later.
```

---

## Quick Start

No scaffold script ships with this skill — explore manually, then fill the
template from the structure below:

```bash
cat README.md AGENTS.md 2>/dev/null | head -200
ls src/ lib/ cmd/ pkg/ 2>/dev/null
rg "fn main|func main|if __name__" --type-add 'all:*.*' -l | head -5
```

---

## Report Modes

| Mode | Time | Depth | Use When |
|------|------|-------|----------|
| **Quick Scan** | 10 min | Entry + types + flow | Orientation, PR context |
| **Standard** | 30 min | Full template | Onboarding, docs |
| **Deep Dive** | 1+ hr | + diagrams, all paths | Audits, major decisions |

### Quick Scan (Minimal)

```
Quick architecture overview:
- What is it? (1 sentence)
- Entry points (list)
- 3 key types
- Main data flow (1 diagram)
Keep under 150 lines.
```

---

## Output Structure

```markdown
# [Project] - Technical Architecture Report

## Executive Summary
[What + stats in 3 lines]

## Entry Points
| Entry | Location | Purpose |
|-------|----------|---------|

## Key Types
| Type | Location | Purpose |
|------|----------|---------|

## Data Flow
[ASCII diagram + 2-sentence description]

## External Dependencies
| Dependency | Purpose | Critical? |
|------------|---------|-----------|

## Configuration
| Source | Priority | Example |
|--------|----------|---------|

## Test Infrastructure
| Type | Location | Count |
|------|----------|-------|
```

---

## Delegation Pattern

For large codebases, delegate exploration:

```
Use a read-only subagent to explore this codebase.
Return structured findings, then I'll compile the final report.
```

The subagent explores in read-only mode and returns findings in report-ready format.
On Claude Code with the AgentOps plugin, its `researcher` agent fits this role.

---

## Anti-Patterns

| Don't | Do |
|-------|-----|
| Vague descriptions | Include `file:line` refs |
| Skip data flow | Trace end-to-end |
| One giant report | Match depth to purpose |

---

## Integration

### With New Projects

On a fresh clone, start the report by hand: copy the section structure from
this reference into `ARCHITECTURE.md`, then fill it from manual exploration
(Quick Start above). There is no auto-scaffold script.

### With Other Work

| After... | Consider... |
|----------|-------------|
| Exploring a codebase to understand it | Offering this report if the findings should persist |
| A bug hunt or code review | Adding "Known Issues" section |
| Comparing patterns across projects | Noting patterns in "Notes & Gotchas" |

---

## Deep dive additions

A deep report can add, where the code has them: module structure (a directory
tree with one-line purposes), error handling (error types and how they
propagate), logging (framework, levels, output), sequence diagrams for critical
flows, performance characteristics, security considerations, a technical-debt
inventory, and notes and gotchas (non-obvious behavior, known limitations).
Every entry cites a `file:line` you read; leave a section out rather than fill
it with placeholders.
