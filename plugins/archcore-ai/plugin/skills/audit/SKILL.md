---
name: audit
argument-hint: "[--deep] [--drift] [category, tag, or scope]"
description: "Audit Archcore docs: dashboard (counts, status, relations, orphans), deep coverage audit, or drift detection (code/cascade/temporal staleness). Use for 'show status', 'documentation gaps', 'check if docs match code', or after a staleness warning. Not for creating docs."
---

# /archcore:audit

Audit Archcore documentation. Three modes, picked from arguments:

- **short** (default) — compact dashboard: counts, statuses, relations, orphans
- **deep** (`--deep` or any non-flag arg) — coverage gaps, staleness, relation health, prioritized recommendations
- **drift** (`--drift`) — code/cascade/temporal drift detection with assisted fix

## When to use

- "Show status" / "How many docs do we have?" / "Dashboard" → short mode
- "Audit the knowledge base" / "Documentation gaps?" → `--deep`
- "Are any docs out of date?" / "Check if documentation matches the code" → `--drift`
- Session-start staleness warning appeared → `--drift`

**Not audit:**
- Creating new documentation → `/archcore:capture`, `/archcore:plan`, `/archcore:decide`
- Reading applicable rules/ADRs/specs before coding → `/archcore:context`
- Picking up where work left off → `/archcore:context`

## Routing table

| Signal | Mode | Scope |
|---|---|---|
| No arguments | → short dashboard | All documents |
| `--deep` | → deep audit | All documents |
| `--deep <filter>` or `<filter>` (non-flag arg) | → deep audit, filtered | Filter applied |
| `--drift` | → drift detection | All documents |
| `--drift <filter>` | → drift detection, filtered | Filter applied |

The short dashboard is project-wide by design — it doesn't take filters. Any non-flag argument without `--drift` implies deep audit on a filter.

## Execution

### Step 1: Gather data

Call in parallel: `mcp__archcore__list_documents` and `mcp__archcore__list_relations`. Apply filter from `$ARGUMENTS` if present (tag, category, or type).

### Short mode (default): present dashboard

Output four tables, then a one-line issues summary. Data only, no analysis.

**Documents by Category**

| Category | Count |
|---|---|
| Vision | _n_ |
| Knowledge | _n_ |
| Experience | _n_ |
| **Total** | _n_ |

**Documents by Status**

| Status | Count |
|---|---|
| draft | _n_ |
| accepted | _n_ |
| rejected | _n_ |

**Documents by Type** — list each type with count, skip types with 0.

**Relations**

| Type | Count |
|---|---|
| related | _n_ |
| implements | _n_ |
| extends | _n_ |
| depends_on | _n_ |

**Issues** — orphaned documents (no relations), high draft count. One line each, no explanations.

End with: _For a full audit with recommendations, run `/archcore:audit --deep`. For staleness detection, run `/archcore:audit --drift`._

### Deep mode (`--deep` or any non-flag arg): analyze and report

Check for:

**Coverage gaps:**
- ADRs without rules/guides (decisions not codified)
- PRDs without plans (requirements without implementation path)
- Rules without guides (standards without instructions)
- Empty categories or types with zero documents

**Staleness:**
- Documents stuck in `draft` that may need `accepted` or `rejected`
- Documents with stale content indicators

**Relation health:**
- Orphaned documents (no incoming or outgoing relations)
- Plans without `implements` to a PRD
- Specs without `implements` to requirements
- Broken chains (ISO cascade with gaps)

**Tag hygiene:**
- Tags used only once (potential inconsistency)
- Related documents with different tags

Report with these sections:

1. **Overview** — totals by category and status
2. **Gaps** — missing documents or relations with specific recommendations
3. **Staleness** — documents needing attention
4. **Orphans** — documents with no relations
5. **Actions** — prioritized list of fixes, most impactful first

### Drift mode (`--drift`): code/cascade/temporal staleness

Read `skills/audit/lib/drift-detection.md` for the detailed staleness-detection protocol. It covers:

- **Code-drift** — cross-references document content against git changes; flags docs whose referenced source paths changed since the doc was last updated.
- **Cascade** — uses the relation graph to find sources whose targets (implements/depends_on/extends) were updated after them.
- **Temporal** — long-running drafts, accepted docs with TODO markers, rejected docs still referenced as active.
- **Assisted fix** — interactive update flow per finding, one document at a time, always confirms before applying via `mcp__archcore__update_document`.

## Result

- **Short mode**: compact dashboard, data only.
- **Deep mode**: actionable report with prioritized fixes — findings and recommendations only, no verbose analysis.
- **Drift mode**: severity-grouped findings (critical / cascade / temporal) with optional interactive fixes via MCP. No modifications without user confirmation.
