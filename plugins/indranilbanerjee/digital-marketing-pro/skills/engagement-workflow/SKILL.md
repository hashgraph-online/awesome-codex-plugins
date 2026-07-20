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

Heavy skill. **Grep before Read** any referenced file, then `Read` only matched ranges with `offset` + `limit`. List the brand's workspace at `~/.claude-marketing/brands/{slug}/` (or `$CLAUDE_PLUGIN_DATA/digital-marketing-pro/brands/{slug}/` when that env var is set) before opening files. On re-invocation mid-session, skip files already in context.

Read these references before producing output:
- [engagement-flow-methodology.md](../context-engine/engagement-flow-methodology.md) — the full 12-Part flow
- [two-views-model.md](../context-engine/two-views-model.md) — v1 / v2 architecture
- [stone-vs-opinion.md](../context-engine/stone-vs-opinion.md) — confidence tagging
- [decision-matrix-rerun.md](../context-engine/decision-matrix-rerun.md) — when to re-run what
- [update-back-rule.md](../context-engine/update-back-rule.md) — versioning protocol
- [living-instruction-file-spec.md](../context-engine/living-instruction-file-spec.md) — LIF schema

## Operating Mode

This skill is invoked via the `/digital-marketing-pro:engagement` command family. The command is a thin router — **this skill is the single source of truth** for the engagement lifecycle, the checkpoint protocol, and the per-part production contract. Each subcommand maps to a specific lifecycle action. The skill calls `engagement-state.py` for persistence via:

```
python "${CLAUDE_PLUGIN_ROOT}/scripts/engagement-state.py" <subcommand> ...
```

You should never hand-edit `_engagement.json` — always go through `engagement-state.py`.

## Checkpointing & Resume (single source of truth)

Every long engagement run is resumable. The checkpoint protocol is: **init a run → save each part as it completes → finalize → publish to the visible output folder.** This lets an interrupted run (context exhaustion, user cancel, machine sleep) resume from the next un-checkpointed part instead of restarting from Part 1.

**1. On `start`, after the brand pre-condition passes, open a checkpoint run and link it to engagement state:**

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/checkpoint-manager.py" init \
    --brand "{brand_slug}" --workflow engagement --topic "{engagement_id}"

# Record the returned run_id into _engagement.json so resume can find it:
python "${CLAUDE_PLUGIN_ROOT}/scripts/engagement-state.py" set-checkpoint-run \
    --brand "{brand_slug}" --id "{engagement_id}" --run-id "{run_id}"
```

`set-checkpoint-run` stores the run_id in `_engagement.json`, making the resume linkage real (previously the run_id was never persisted).

**2. After each part completes and passes its quality gate, the orchestrator saves that part's output:**

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/checkpoint-manager.py" save \
    --brand "{brand}" --run-id "{run_id}" \
    --step {part_number} --content-file "{path_to_that_part_deliverable}" --extension md
```

Pass the **actual deliverable path for that part** (e.g. Part 3 saves the Four Core Documents path; Part 8 saves the Growth Plan path) — never a placeholder for a different part.

**3. Before saving Part 5 (Client Validation) and Part 8 (Growth Plan) deliverables, run the full quality gate:**

```bash
# BLOCKING gate — Part 5 and Part 8 deliverables cannot be checkpointed until this passes
/digital-marketing-pro:check "{path_to_deliverable}" --full --brand {brand}
```

If `/digital-marketing-pro:check --full` returns BLOCKED, fix the CRITICAL issues before checkpointing the part.

**4. After the final part, publish every artifact to the user-visible folder and finalize:**

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/output-publisher.py" publish-run \
    --brand "{brand}" --run-id "{run_id}"

python "${CLAUDE_PLUGIN_ROOT}/scripts/checkpoint-manager.py" finalize \
    --brand "{brand}" --run-id "{run_id}" --status completed
```

Then point the user at the visible output folder via `/digital-marketing-pro:output-folder {brand}`.

To resume an interrupted run, use `/digital-marketing-pro:resume` — it reloads every saved part and continues from the next un-checkpointed part.

## State validation & rework caps

- **Validate a part's outputs against the manifest** before marking it complete:
  ```bash
  python "${CLAUDE_PLUGIN_ROOT}/scripts/engagement-state.py" validate-part \
      --brand "{brand}" --id "{id}" --part {N}
  ```
  This diffs the actual files on disk against the `PART_DEFINITIONS` manifest and flags missing deliverables. Use it in `file-tree` and before `next`.

- **Repair a partially-initialised engagement directory** (instead of crashing on a non-empty dir):
  ```bash
  python "${CLAUDE_PLUGIN_ROOT}/scripts/engagement-state.py" init --repair \
      --brand "{brand}" --id "{id}"
  ```
  `--repair` completes the canonical directory tree and state file on a dir that holds only partial state.

- **v2 re-run cap:** a maximum of **2 v2 re-run rounds per part** is allowed without explicit user override. The round count is stored in `_engagement.json`. If a part would exceed 2 rounds, stop and ask the user to explicitly approve further re-runs (records the override in state). This prevents unbounded re-run loops.

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
3. Highlight files that are missing per the canonical structure. Use `engagement-state.py validate-part --part {N}` to diff each completed part's actual files against the `PART_DEFINITIONS` manifest (e.g., if Part 3 is marked completed but `3.1-business-and-sbu-analysis.md` is missing, `validate-part` flags it deterministically instead of eyeballing).

### `/digital-marketing-pro:engagement validate [brand] [id]`

**Purpose:** Run the Part 5 Client Validation flow.

**Pre-condition:** Parts 2, 3, 4 must be completed.

**Steps:**

1. Verify pre-conditions (Parts 2, 3, 4 completed)
2. Invoke the `client-validation-document` skill — it produces the Part 5 deliverable: a structured document presenting each finding from v1 with ACCEPT/REJECT/EDIT/DEFER options
3. **Run the full quality gate on the Part 5 deliverable before it goes to the client:** `/digital-marketing-pro:check "{part5_path}" --full --brand {brand}`. If it returns BLOCKED, fix the CRITICAL issues first (this gate is mandatory before Part 5 and Part 8 deliverables).
4. After the user reviews and provides decisions, parse them into a triggers list per the Decision Matrix categories
5. Run `engagement-state.py decision-matrix --triggers "{comma-separated}"` to compute the v2 re-run plan
6. Present the re-run plan to the user
7. Mark Part 5 completed; on user approval of the re-run plan, advance to Part 6

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
5. Update the Living Project Instruction File via `lif-log-change` — it now appends the change to `living-instruction-file.md` and refreshes the header date, so the LIF reflects the correction immediately
6. Identify downstream documents that may need review and add to the engagement's review queue

### `/digital-marketing-pro:engagement lif-show [brand] [id]`

**Purpose:** Display the Living Project Instruction File.

**Steps:** Run `engagement-state.py lif-show` and format the markdown output for readability.

### `/digital-marketing-pro:engagement list-engagements [brand]`

**Purpose:** List all engagements (optionally filtered by brand).

**Steps:** Run `engagement-state.py list-engagements --brand {slug}` and format as a table.

### Production shorthands

The command family also exposes four production shorthands that route straight to the part-producing skills (documented in *Per-Part Production Targets* below). These match the command surface one-to-one:

- `/digital-marketing-pro:engagement four-core <brand> <id> [--doc 3.X] [--view v2] [--combined]` — Part 3, invokes the `four-core-documents` skill
- `/digital-marketing-pro:engagement growth-plan <brand> <id>` — Part 8, invokes the `growth-plan` skill
- `/digital-marketing-pro:engagement yearly-planner <brand> <id>` — Part 8 companion, invokes the `yearly-planner` skill
- `/digital-marketing-pro:engagement loop <brand> <id>` — Part 12, invokes the `continuous-improvement-loop` skill

## Per-Part Production Targets

Each part is produced by real, existing agents and skills. This orchestrator dispatches to the targets below — there are **no** wrapper skills named `external-research` / `preparation-documents` / `channel-strategy-fanout` / `execution-artefacts` / `ai-creative-instructions`; those never existed. Use the exact targets named here:

| Part | Real target(s) |
|------|----------------|
| 1 | (this skill — intake walked here directly) |
| 2 | agents `market-intelligence` + `competitive-intel`; skill `audience-intelligence` (invoke as a skill); reference `compliance-rules.md` (load as context) |
| 3 | skill `four-core-documents` (produces 3.1, 3.2, 3.3, 3.4) |
| 4 | command `competitor-analysis` + skills `audience-intelligence` + agent `market-intelligence` |
| 5 | skill `client-validation-document` |
| 6 | re-runs invoke skill `four-core-documents` with `--view v2` |
| 7 | skills `content-engine` + `campaign-orchestrator` + `analytics-insights` |
| 8 | skills `growth-plan` + `yearly-planner` |
| 9 | per-channel skills — `paid-advertising`, `aeo-geo`, `social-strategy`, `seo-plan`, `email-sequence` (one per channel family) |
| 10 | skill `content-engine` (execution / output mode) |
| 11 | skills `content-engine` + `ad-creative` + `video-script` (creative briefs); asset rendering happens in your own creative tooling (design team, AI image/video tools, or a connected design platform), then finished assets are signed via `c2pa-metadata` |
| 12 | skill `continuous-improvement-loop` |

## Parallel Dispatch

Several parts of the engagement contain **independent sub-tasks** that should be dispatched **in parallel via multiple `Task` tool calls in a single message** — not sequentially. Dispatching independent sub-tasks concurrently is substantially faster than running them one after another; actual time varies by engagement depth, model, and rate limits. Keep concurrent subagents to a handful (roughly 3–8) — past that you queue against API rate limits and the win drops; under 3 there is nothing to parallelize.

**Cost note:** total token usage is broadly similar (you're doing the same work) but billed-per-turn input costs trend up slightly because each parallel subagent re-loads its context.

**Parts that benefit from parallel dispatch:**

| Part | Parallel-eligible work | How to dispatch |
|---|---|---|
| **Part 2 — External Research** | Market sizing, competitor landscape, customer signals, regulatory landscape — none depend on each other | Dispatch the `market-intelligence` agent and the `competitive-intel` agent as parallel `Task` calls; invoke `audience-intelligence` as a skill; load `compliance-rules.md` (a reference file) as context — not as a subagent |
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
2. Each parallel subagent gets the engagement slug and the LIF path so it can read shared context, but writes ONLY to its own numbered per-part subdirectory (01-… 12-…).
3. **Subagents never mutate engagement state.** A subagent must NOT call `lif-log-change`, `mark-part-completed`, `bump-version`, or any other `engagement-state.py` write, and must NOT touch `_engagement.json` or `living-instruction-file.md`. Those are unlocked read-modify-write files; concurrent writers lose updates. Each subagent returns its output as per-part files only. After a parallel batch completes, the **orchestrator alone** applies state mutations — one `lif-log-change` per batch, plus `mark-part-completed` / `bump-version` as needed — and then re-reads the LIF before the next step.
4. If a parallel batch fails partway, the failed subagent's outputs are NOT auto-rolled-back — re-dispatch only the failed ones; the successful peers stay valid.

For multi-dimensional commands outside the 12-part flow (e.g. `/digital-marketing-pro:competitor-analysis`, `/digital-marketing-pro:seo-audit`, `/digital-marketing-pro:content-engine`), the same pattern applies — dispatch independent dimensions in parallel via multiple `Task` calls in a single message.

## Running an engagement in a single conversation

A large-context model can hold much of an engagement — intake, external research, the Four Core Documents (61 steps), competitive/customer/market analysis, Client Validation, selective v2 re-runs, preparation docs, Growth Plan + Yearly Planner, channel fan-out, execution artefacts, creative briefs, and the continuous-improvement loop — within one working session (a full engagement typically produces 50–60 canonical documents).

**The checkpoint + persistence pattern is still the default — always.** Even when everything fits in one conversation:

- `engagement-state.py` + `checkpoint-manager.py` remain the system of record: audit trail, cross-conversation resume, and multi-user / multi-day continuity all depend on persisted state.
- Do NOT skip LIF updates or state writes on the assumption that "it's all in context." An interruption still loses in-memory work, and a teammate resuming the engagement reads persisted state — not your conversation.
- The only single-conversation convenience is that you re-read fewer files mid-session because they are already in context. It does not remove the need to persist, checkpoint, and update the LIF.

## Quality Discipline

1. **Never hand-edit `_engagement.json`.** Always go through `engagement-state.py`.
2. **Never delete v1.** When v2 is produced, both stay.
3. **Always update the LIF when source docs change.** Use `lif-log-change` — it appends to the change-log section of `living-instruction-file.md` and refreshes the header date, so the LIF never goes stale.
4. **Always cite source per fact.** Stone facts cite the validation source; Opinion hypotheses cite the client's evidence.
5. **Never auto-advance parts.** The user confirms part completion explicitly.
6. **Always parallelize independent work.** When a Part has 2+ independent sub-tasks (see Parallel Dispatch above), dispatch them in a single message with multiple Task calls. Sequential dispatch of independent work wastes wall-clock time and API turns.
7. **Never auto-execute v2 re-runs without user approval.** Show the plan, get approval, then run. Cap: 2 v2 re-run rounds per part without an explicit user override (stored in state).

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
