---
name: engagement-workflow
description: "Run a full marketing engagement using the 12-Part methodology. Use when starting a new engagement, advancing parts, applying the Decision Matrix, or showing engagement status."
user-invocable: true
triggers:
  - start a new engagement
  - run the 12-part methodology
  - advance engagement to next part
  - show engagement status
  - apply the decision matrix
  - re-run v2 documents
  - mark engagement part complete
  - what part of the engagement are we on
allowed-tools: Read Write Edit Bash Glob Grep
engagement-part: orchestrator
view-preference: both
---

# /digital-marketing-pro:engagement-workflow — 12-Part Engagement Orchestrator

This skill orchestrates the full marketing engagement using the 12-Part sequential methodology. Every brand engagement runs through the same 12 parts in sequence, producing a canonical set of files at each stage.

## Context efficiency

Heavy skill. **Grep before Read** any referenced file, then `Read` only matched ranges with `offset` + `limit`. List `${CLAUDE_PLUGIN_DATA}/<brand>/` before opening files. On re-invocation mid-session, skip files already in context.

Read these references before producing output:
- [engagement-flow-methodology.md](../context-engine/engagement-flow-methodology.md) — the full 12-Part flow
- [two-views-model.md](../context-engine/two-views-model.md) — v1 / v2 architecture
- [stone-vs-opinion.md](../context-engine/stone-vs-opinion.md) — confidence tagging
- [decision-matrix-rerun.md](../context-engine/decision-matrix-rerun.md) — when to re-run what
- [update-back-rule.md](../context-engine/update-back-rule.md) — versioning protocol
- [living-instruction-file-spec.md](../context-engine/living-instruction-file-spec.md) — LIF schema

## Operating Mode

This skill is invoked via the `/digital-marketing-pro:engagement` command family. Each subcommand maps to a specific lifecycle action. The skill calls `scripts/engagement-state.py` for persistence; you should never hand-edit `_engagement.json`.

## Subcommands

### `/digital-marketing-pro:engagement start <brand-slug> <engagement-id>`

**Purpose:** Initialise a new engagement.

**Steps:**

1. Validate that the brand profile exists at `~/.claude-marketing/brands/{brand-slug}/profile.json`. If not, instruct the user to run `/digital-marketing-pro:brand-setup` first.
2. Run `python ${CLAUDE_PLUGIN_ROOT}/scripts/engagement-state.py init --brand {brand-slug} --id {engagement-id}`.
3. Confirm the directory tree was created and report the next required action (Part 1 intake).
4. Walk the user through Part 1 Stone vs Opinion intake by asking the questions one batch at a time.

**Part 1 intake questions (ask in this order):**

**Stone — what the client knows for certain:**

1. Company basics: founded year, employee count, headquarters location, geographic operations
2. Business model: revenue streams, pricing tiers, primary product/service categories
3. Current marketing: channels currently active, monthly marketing spend, current measurable KPIs
4. Tech stack: CRM, email service provider, analytics setup, ad accounts
5. Customer base scale: customer count, biggest named customer, average order value if known

For each Stone fact, capture:
- The fact itself
- Source (how the user knows / what document confirmed it)

Save each via:
```
python ${CLAUDE_PLUGIN_ROOT}/scripts/engagement-state.py add-stone-fact --brand {slug} --id {id} --fact-json '{"category":"...","fact":"...","source":"..."}'
```

**Opinion — what the client believes:**

1. Brand positioning: how does the client describe their position in the market?
2. Customer base: who do they think their customers are? Why do they buy?
3. Competitors: who do they consider their main competitors?
4. Growth opportunities: where do they think the biggest opportunity is?
5. What is working: what marketing activity does the client believe is working?
6. What is not working: what does the client believe is not working?

For each Opinion, capture:
- The hypothesis
- Client's evidence for it (could be intuition, anecdote, partial data)
- Research question — what would the unbiased research need to verify or refute?

Save each via:
```
python ${CLAUDE_PLUGIN_ROOT}/scripts/engagement-state.py add-opinion --brand {slug} --id {id} --hypothesis-json '{"category":"...","hypothesis":"...","client_evidence":"...","research_question":"..."}'
```

**On completion of Part 1:** mark Part 1 as completed via `mark-part-completed --part 1`, advise the user to proceed to Part 2 (External Research).

### `/digital-marketing-pro:engagement next [brand] [id]`

**Purpose:** Advance to the next part.

**Steps:**

1. Read engagement status via `engagement-state.py status`
2. Identify the current part and next not-yet-completed part
3. Confirm with the user that the current part is genuinely complete (do not auto-advance — ask)
4. On confirmation, mark current as completed, advance current_part pointer
5. Brief the user on what the new part requires

### `/digital-marketing-pro:engagement status [brand] [id]`

**Purpose:** Show engagement status.

**Steps:**

1. Run `engagement-state.py status` — get the full state
2. Read the Living Project Instruction File header
3. Format a human-readable summary:
   - Engagement: brand + id + start date
   - Current part: part name + days in
   - Completed parts: list
   - Pending parts: list
   - Open re-run decisions: count
   - LIF last updated: date
4. If the engagement has open items needing resolution, list them

### `/digital-marketing-pro:engagement file-tree [brand] [id]`

**Purpose:** Show the engagement directory file tree.

**Steps:**

1. Run `engagement-state.py file-tree`
2. Format as an indented tree
3. Highlight files that are missing per the canonical structure (e.g., if Part 3 is marked completed but `3.1-business-and-sbu-analysis.md` is missing, flag it)

### `/digital-marketing-pro:engagement validate [brand] [id]`

**Purpose:** Run the Part 5 Client Validation flow.

**Pre-condition:** Parts 2, 3, 4 must be completed.

**Steps:**

1. Verify pre-conditions (Parts 2, 3, 4 completed)
2. Invoke the `client-validation-document` skill — it produces the Part 5 deliverable: a structured document presenting each finding from v1 with ACCEPT/REJECT/EDIT/DEFER options
3. After the user reviews and provides decisions, parse them into a triggers list per the Decision Matrix categories
4. Run `engagement-state.py decision-matrix --triggers "{comma-separated}"` to compute the v2 re-run plan
5. Present the re-run plan to the user
6. Mark Part 5 completed; on user approval of the re-run plan, advance to Part 6

### `/digital-marketing-pro:engagement re-run-decision [brand] [id]`

**Purpose:** Apply the Decision Matrix to compute v2 re-runs.

**Steps:**

1. Read the Part 5 Client Validation Document
2. Categorise rejected/edited findings into Decision Matrix triggers
3. Show the triggers and the computed re-runs
4. Estimate the cost (rough token count) of each re-run
5. Await user approval — they can accept, modify (skip some, add others), or reject
6. Record the executed plan via `engagement-state.py record-rerun-execution`

### `/digital-marketing-pro:engagement update-back [brand] [id] --doc <doc-id> --reason <reason>`

**Purpose:** Apply the Update-Back Rule to bump a source document version after Part 7+.

**Pre-condition:** The user has already drafted the corrected document content.

**Steps:**

1. Read the current version of the doc
2. Confirm the correction with the user (validation step per the Update-Back Rule)
3. Bump the version via `engagement-state.py bump-version --doc {id} --reason "{reason}"`
4. Save the new version file with a header noting v(prev) → v(new) changes
5. Update the Living Project Instruction File via `lif-log-change`
6. Identify downstream documents that may need review and add to the engagement's review queue

### `/digital-marketing-pro:engagement lif-show [brand] [id]`

**Purpose:** Display the Living Project Instruction File.

**Steps:** Run `engagement-state.py lif-show` and format the markdown output for readability.

### `/digital-marketing-pro:engagement list-engagements [brand]`

**Purpose:** List all engagements (optionally filtered by brand).

**Steps:** Run `engagement-state.py list-engagements --brand {slug}` and format as a table.

## Per-Part Production Skills

Each part has a dedicated skill that produces its outputs. This orchestrator delegates:

| Part | Skill |
|------|-------|
| 1 | (this skill — intake walked here directly) |
| 2 | `external-research` (use existing market-intelligence + competitive-intelligence skills) |
| 3 | `four-core-documents` (produces 3.1, 3.2, 3.3, 3.4) |
| 4 | (use existing competitor-analysis + audience-intelligence + market-intelligence) |
| 5 | `client-validation-document` |
| 6 | (re-runs invoke `four-core-documents` with view=v2) |
| 7 | `preparation-documents` (uses content-engine + campaign-orchestrator + analytics) |
| 8 | `growth-plan` + `yearly-planner` |
| 9 | `channel-strategy-fanout` (delegates to per-channel skills in paid-advertising / aeo-geo / etc.) |
| 10 | `execution-artefacts` (uses content-engine output mode) |
| 11 | `ai-creative-instructions` |
| 12 | `continuous-improvement-loop` |

## Parallel Dispatch (added v3.4)

Several parts of the engagement contain **independent sub-tasks** that should be dispatched **in parallel via multiple `Task` tool calls in a single message** — not sequentially. Claude Code's April 2026 parallel-subagent initialization makes this a real time saving — published guidance reports **4–6× parallelism** with roughly **50–80% wall-clock reduction** for 3–8 concurrent subagents. A 4-document Part 4 that took ~16 min sequentially typically completes in ~4–6 min when dispatched as four parallel subagent calls. Past 8 concurrent subagents you start queueing against API rate limits and the win drops; under 3 there's nothing to parallelize.

**Cost note:** total token usage is broadly similar (you're doing the same work) but billed-per-turn input costs trend up slightly because each parallel subagent re-loads its context.

**Parts that benefit from parallel dispatch:**

| Part | Parallel-eligible work | How to dispatch |
|---|---|---|
| **Part 2 — External Research** | Market sizing, competitor landscape, customer signals, regulatory landscape — none depend on each other | One `Task` call per dimension (market-intelligence + competitive-intelligence + audience-intelligence + compliance-rules) in a single message |
| **Part 4 — Competitive + Customer + Market** | Four documents (4.1, 4.2, 4.3, 4.4) are independent — they reference Part 2 only | Dispatch all four in a single message with the four respective subagents |
| **Part 9 — Channel Strategy Fan-out** | Up to 17 channel docs in 7 families. Families 2 (Paid platforms), 3 (Organic & Influencer), 4 (Marketplace & CRM), 5 (Content/ATL/BTL/PR) are independent after Families 1 (Search & Campaign) and 6 (Web + Measurement) complete | Sequence: F1 → (F2 ∥ F3 ∥ F4 ∥ F5 in parallel) → F6 → F7. The middle batch is four parallel `Task` calls in one message. |
| **Part 10 — Execution Artefacts** | Ad copy, post copy, headlines, CTAs across channels — independent per channel | Dispatch one subagent per channel in parallel |
| **Part 11 — AI Creative Instructions** | Visual asset briefs — independent per asset | Dispatch in parallel per asset |

**Parts that MUST stay sequential** (have hard data dependencies):

- Part 1 → Part 2 (intake feeds research scope)
- Part 3 → Part 4 (Four Core Documents feed competitive/customer/market analysis)
- Part 5 → Part 6 (Client Validation drives which docs need v2 re-runs)
- Part 7 → Part 8 (prep docs feed the Growth Plan)
- Part 8 → Part 9 (Growth Plan drives channel fan-out)

**Cross-cutting rules:**

1. Never dispatch parallel agents that need to write to the same file simultaneously — chunk by output file.

## Opus 4.7 1M context — single-conversation 12-part engagements (May 2026)

As of May 2026, Claude Opus 4.7 with the 1M-token context window is generally available to Max, Team, and Enterprise users. The full 12-part engagement — Stone-vs-Opinion intake, external research, Four Core Documents (61 explicit steps), competitive/customer/market analysis, Client Validation Document, selective v2 re-runs, preparation docs, Growth Plan + Yearly Planner, channel fan-out, execution artefacts, AI creative briefs, continuous improvement loop — typically produces 50–60 canonical documents totaling 250K–600K tokens depending on engagement depth.

**This now fits in a single conversation context.** Cross-conversation continuity tricks (writing intermediate state to disk + re-loading it on the next conversation) that v3.0–v3.3 relied on are no longer strictly necessary for engagements that complete within one working session.

When 1M context is available:
- Skip the LIF re-load between parts — the Living Project Instruction File and all earlier-part outputs are already in context
- Run Parts 1–8 sequentially in a single conversation, dispatch Part 9 channel families in parallel, complete Parts 10–12 in the same conversation
- Engagement-state.py is still useful for audit trail + cross-conversation resume + multi-user team scenarios, but not required for the active engagement

When 1M context is NOT available (Pro tier, third-party API access, batch mode):
- Use the existing engagement-state.py persistence pattern; chunk by Part; re-load the LIF at each Part transition

Keep using the persistence pattern by default — it's correct in both worlds and the only one that works for multi-day / multi-author engagements.
2. Each parallel subagent gets the engagement slug and the LIF path so it can read shared context but writes to its own numbered subdirectory (01-… 12-…).
3. After a parallel batch completes, ALWAYS re-read the LIF before the next step in case a parallel subagent updated it (use `engagement-state.py lif-log-change` from inside each subagent).
4. If a parallel batch fails partway, the failed subagent's outputs are NOT auto-rolled-back — re-dispatch only the failed ones, the successful peers stay valid.

For multi-dimensional commands outside the 12-part flow (e.g. `/digital-marketing-pro:competitor-analysis`, `/digital-marketing-pro:seo-audit`, `/digital-marketing-pro:content-engine`), the same pattern applies — dispatch independent dimensions in parallel via multiple `Task` calls in a single message.

## Quality Discipline

1. **Never hand-edit `_engagement.json`.** Always go through `engagement-state.py`.
2. **Never delete v1.** When v2 is produced, both stay.
3. **Always update the LIF when source docs change.** Use `lif-log-change`.
4. **Always cite source per fact.** Stone facts cite the validation source; Opinion hypotheses cite the client's evidence.
5. **Never auto-advance parts.** The user confirms part completion explicitly.
6. **Always parallelize independent work.** When a Part has 2+ independent sub-tasks (see Parallel Dispatch above), dispatch them in a single message with multiple Task calls. Sequential dispatch of independent work wastes wall-clock time and API turns.
6. **Never auto-execute v2 re-runs without user approval.** Show the plan, get approval, then run.

## Examples

### Example: Starting a new engagement

```
User: I want to start a new engagement for Acme Corp this quarter.

Skill response:
1. Verify Acme has a brand profile (slug: acme-corp). Found.
2. Initialise engagement: engagement-state.py init --brand acme-corp --id 2026-q2
3. Engagement directory created at ~/.claude-marketing/brands/acme-corp/engagements/2026-q2/
4. Walk Part 1 intake. Begin with Stone questions:
   "Let's start with what we know for certain. What year was Acme founded? Where is it headquartered? How many employees today?"
5. (User answers; each fact captured via add-stone-fact)
6. Move to Opinion questions:
   "Now let's capture what you believe but haven't formally validated. How would you describe Acme's positioning in the market today?"
7. (User answers; each hypothesis captured via add-opinion)
8. Mark Part 1 completed. Advise: "Part 1 is complete. The unbiased External Research (Part 2) is next — recommend running it now or scheduling it for the next session."
```

### Example: Mid-engagement status check

```
User: Where are we on the Beta Industries engagement?

Skill response:
- Reads engagement-state.py status --brand beta-industries --id 2026-h1
- Shows:
  Engagement: beta-industries / 2026-h1
  Started: 2026-04-01 (32 days in)
  Current part: Part 9 — Channel Strategy Fan-out (in progress)
  Completed parts: 1, 2, 3, 4, 5, 6, 7, 8
  Pending parts: 9 (in progress), 10, 11, 12
  Open re-run decisions: 1 (Part 6 v2 re-runs in progress)
  Open items requiring resolution: 2 (LinkedIn Ads CPL forecast pending; Q3 budget envelope pending)
  LIF last updated: 2 days ago
  Next required action: complete remaining Part 9 channel docs (5 of 9 complete)
```

### Example: Applying the Decision Matrix

```
User: We just finished Part 5 client validation. The client rejected our positioning recommendation and added two new competitors. What re-runs do we need?

Skill response:
1. Categorise the changes:
   - Two new competitors → trigger "competitors_changed"
   - Positioning rejected → trigger "positioning_changed"
2. Run engagement-state.py decision-matrix --triggers "competitors_changed,positioning_changed"
3. Output the triggered re-runs:
   Triggered re-runs: 3.1, 3.2, 3.3, 3.4, 4.1, 4.2
   (competitors_changed triggers all four Core Docs + 4.1 + 4.2; positioning_changed adds 3.3 which is already in scope)
4. Estimate token cost: ~85K tokens for the full re-run set
5. Ask: "Approve all? Modify? Skip any?"
6. On user approval, mark Part 6 started and invoke four-core-documents skill with view=v2 for each triggered doc
```

### Example: Update-Back correction in flight

```
User: We've been live for two months. Q1 channel data shows our actual CAC for Segment X is INR 4,800 — but Core Doc 3.1 v2.0 had it estimated at INR 3,000. Need to update.

Skill response:
1. Validate the correction: 60+ days of data, statistically meaningful sample. ✓
2. Read current 3.1 v2.0
3. Bump version: engagement-state.py bump-version --doc 3.1 --reason "Segment X CAC corrected from INR 3,000 to INR 4,800 based on Q1 channel data"
4. Save 3.1 v2.1 with header note: "v2.0 → v2.1 changes: Section 4 (Unit Economics) — Segment X CAC corrected. LTV:CAC drops from 4.0 to 2.5; below 3.0 health threshold."
5. lif-log-change --section "Recent Corrections" --summary "Segment X CAC corrected to INR 4,800. Channel mix for Segment X under review."
6. Identify downstream review needed: Core Doc 3.4 (DMFlow) channel allocation for Segment X may need revision
7. Add to engagement review queue
```

## Related skills

- `four-core-documents` — produces Part 3 deliverables
- `client-validation-document` — produces Part 5 deliverable
- `growth-plan` + `yearly-planner` — produce Part 8 deliverables
- `continuous-improvement-loop` — handles Part 12

## Related references

- [engagement-flow-methodology.md](../context-engine/engagement-flow-methodology.md)
- [four-core-documents-spec.md](../context-engine/four-core-documents-spec.md)
- [decision-matrix-rerun.md](../context-engine/decision-matrix-rerun.md)
- [update-back-rule.md](../context-engine/update-back-rule.md)
- [living-instruction-file-spec.md](../context-engine/living-instruction-file-spec.md)
- [stone-vs-opinion.md](../context-engine/stone-vs-opinion.md)
- [two-views-model.md](../context-engine/two-views-model.md)
