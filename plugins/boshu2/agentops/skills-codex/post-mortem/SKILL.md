---
name: post-mortem
description: "Review completed work and learn."
---
# Post-Mortem Skill

> **Purpose:** Wrap up completed work — validate it shipped correctly, extract learnings, process the knowledge backlog, activate high-value insights, and retire stale knowledge.
>
> **Runtime note:** Hook-driven closeout is runtime-dependent. Claude/OpenCode can wire Phase 2-5 maintenance through lifecycle hooks. Codex does not expose that hook surface, so Codex sessions should finish closeout with `ao codex ensure-stop`.

Six phases:
1. **Council** — Did we implement it correctly?
2. **Extract** — What did we learn?
3. **Process Backlog** — Score, deduplicate, and flag stale learnings
4. **Activate** — Promote high-value learnings to MEMORY.md and constraints
5. **Retire** — Archive stale and superseded learnings
6. **Harvest** — Surface next work for the flywheel

---

## Quick Start

```bash
$post-mortem                    # wraps up recent work
$post-mortem epic-123           # wraps up specific epic
$post-mortem --quick "insight"  # quick-capture single learning (no council)
$post-mortem --process-only     # skip council+extraction, run Phase 3-5 on backlog
$post-mortem --skip-activate    # extract + process but don't write MEMORY.md
$post-mortem --deep recent      # thorough council review
$post-mortem --mixed epic-123   # cross-vendor (Claude + Codex)
$post-mortem --skip-checkpoint-policy epic-123  # skip ratchet chain validation
```

### Codex Closeout

In Codex hookless mode, run these after the post-mortem workflow writes learnings and next work:

```bash
ao codex ensure-stop --auto-extract
ao codex status
```

`ao codex ensure-stop` is idempotent for the current Codex thread. It uses the latest transcript or history fallback to queue/persist learnings and run close-loop maintenance without runtime hooks.

---

## Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--quick "text"` | off | Quick-capture a single learning directly to `.agents/learnings/` without running a full post-mortem. Formerly handled by `$retro --quick`. |
| `--process-only` | off | Skip council and extraction (Phase 1-2). Run Phase 3-5 on the existing backlog only. |
| `--skip-activate` | off | Extract and process learnings but do not write to MEMORY.md (skip Phase 4 promotions). |
| `--deep` | off | 3 judges (default for post-mortem) |
| `--mixed` | off | Cross-vendor (Claude + Codex) judges |
| `--explorers=N` | off | Each judge spawns N explorers before judging |
| `--debate` | off | Two-round adversarial review |
| `--skip-checkpoint-policy` | off | Skip ratchet chain validation |
| `--skip-sweep` | off | Skip pre-council deep audit sweep |

---

## Quick Mode

Given `$post-mortem --quick "insight text"`:

### Quick Step 1: Generate Slug

Create a slug from the content: first meaningful words, lowercase, hyphens, max 50 chars.

### Quick Step 2: Write Learning Directly

**Write to:** `.agents/learnings/YYYY-MM-DD-quick-<slug>.md`

```markdown
---
type: learning
source: post-mortem-quick
date: YYYY-MM-DD
maturity: provisional
utility: 0.5
---

# Learning: <Short Title>

**Category**: <auto-classify: debugging|architecture|process|testing|security>
**Confidence**: medium

## What We Learned

<user's insight text>

## Source

Quick capture via `$post-mortem --quick`
```

This skips the full pipeline — writes directly to learnings, no council or backlog processing.

### Quick Step 3: Confirm

```
Learned: <one-line summary>
Saved to: .agents/learnings/YYYY-MM-DD-quick-<slug>.md

For deeper reflection, use `$post-mortem` without --quick.
```

**Done.** Return immediately after confirmation.

---

## Execution Steps

### Pre-Flight Checks

Before proceeding, verify:
1. **Git repo exists:** `git rev-parse --git-dir 2>/dev/null` — if not, error: "Not in a git repository"
2. **Work was done:** `git log --oneline -1 2>/dev/null` — if empty, error: "No commits found. Run `$implement` first."
3. **Epic context:** If epic ID provided, verify it has closed children. If 0 closed children, error: "No completed work to review."

**If `--process-only`:** Skip Pre-Flight Checks through Step 3. Jump directly to Phase 3: Process Backlog.

### Step 0.4: Load Reference Documents (MANDATORY)

Before Step 0.5 and Step 2.5, read the required reference docs into context:

```
REQUIRED_REFS=(
  "skills/post-mortem/references/checkpoint-policy.md"
  "skills/post-mortem/references/metadata-verification.md"
  "skills/post-mortem/references/closure-integrity-audit.md"
  "skills/post-mortem/references/four-surface-closure.md"
)
```

For each reference file, read its content and hold it in context for use in later steps. Do NOT just test file existence with `[ -f ]` -- actually read the content so it is available when Steps 0.5 and 2.5 need it.

If a reference file does not exist (Read returns an error), log a warning and add it as a checkpoint warning in the council context. Proceed only if the missing reference is intentionally deferred.

### Step 0.5: Checkpoint-Policy Preflight (MANDATORY)

Read `references/checkpoint-policy.md` for the full checkpoint-policy preflight procedure. It validates the ratchet chain, checks artifact availability, and runs idempotency checks. BLOCK on prior FAIL verdicts; WARN on everything else.

### Step 1: Identify Completed Work and Record Timing

**Record the post-mortem start time for cycle-time tracking:**
```bash
PM_START=$(date +%s)
```

**If epic/issue ID provided:** Use it directly.

**If no ID:** Find recently completed work:
```bash
# Check for closed beads
br list --status closed --since "7 days ago" 2>/dev/null | head -5

# Or check recent git activity
git log --oneline --since="7 days ago" | head -10
```

### Step 1.5: RPI Session Metrics

Read `.agents/rpi/rpi-state.json` and extract session ID, phase, verdicts, and streak data. If absent or unparseable, skip silently. Prepend a tweetable summary to the report: `> RPI streak: N consecutive days | Sessions: N | Last verdict: PASS/WARN/FAIL`. See [references/streak-tracking.md](references/streak-tracking.md) for extraction logic and fallback behavior.

### Step 2: Load the Original Plan/Spec

Before invoking council, load the original plan for comparison:

1. **If epic/issue ID provided:** `br show <id>` to get the spec/description
2. **Search for plan doc:** `ls .agents/plans/ | grep <target-keyword>`
3. **Check git log:** `git log --oneline | head -10` to find the relevant bead reference

If a plan is found, include it in the council packet's `context.spec` field:
```json
{
  "spec": {
    "source": "bead na-0042",
    "content": "<the original plan/spec text>"
  }
}
```

### Step 2.1: Load Compiled Prevention Context

Before council and retro synthesis, load compiled prevention outputs when they exist:

- `.agents/planning-rules/*.md`
- `.agents/pre-mortem-checks/*.md`

Use these compiled artifacts first, then fall back to `.agents/findings/registry.jsonl` only when compiled outputs are missing or incomplete. Carry matched finding IDs into the retro as `Applied findings` / `Known risks applied` context so post-mortem can judge whether the flywheel actually prevented rediscovery.

### Step 2.2: Load Implementation Summary

Check for a crank-generated phase-2 summary:

```bash
PHASE2_SUMMARY=$(ls -t .agents/rpi/phase-2-summary-*-crank.md 2>/dev/null | head -1)
if [ -n "$PHASE2_SUMMARY" ]; then
    echo "Phase-2 summary found: $PHASE2_SUMMARY"
    # Read the summary with the Read tool for implementation context
fi
```

If available, use the phase-2 summary to understand what was implemented, how many waves ran, and which files were modified.

### Step 2.3: Reconcile Plan vs Delivered Scope

Compare the original plan scope against what was actually delivered:

1. Read the plan from `.agents/plans/` (most recent)
2. Compare planned issues against closed issues (`br dep tree <epic-id>` and `br list --status closed`)
3. Note any scope additions, removals, or modifications
4. Include scope delta in the post-mortem findings

### Step 2.4: Closure Integrity Audit (MANDATORY)

Read `references/closure-integrity-audit.md` for the full procedure. Mechanically verifies:

1. **Evidence precedence per child** — every closed child resolves on the strongest available evidence in this order: `commit`, then `staged`, then `worktree`
2. **Phantom bead detection** — flags children with generic titles ("task") or empty descriptions
3. **Orphaned children** — beads in `br list` but not linked to parent in `br dep tree`
4. **Multi-wave regression detection** — for crank epics, checks if a later wave removed code added by an earlier wave
5. **Stretch goal audit** — verifies deferred stretch goals have documented rationale

Include results in the council packet as `context.closure_integrity`. WARN on 1-2 findings, FAIL on 3+.

If a closure is evidence-only, emit a proof artifact with `bash skills/post-mortem/scripts/write-evidence-only-closure.sh` and cite at `.agents/releases/evidence-only-closures/<target-id>.json`. Record `evidence_mode` plus repo-state detail for replayability.

### Step 2.5: Pre-Council Metadata Verification (MANDATORY)

Read `references/metadata-verification.md` for the full verification procedure. Mechanically checks: plan vs actual files, file existence in commits, cross-references in docs, and ASCII diagram integrity. Failures are included in the council packet as `context.metadata_failures`.

### Step 2.6: Pre-Council Deep Audit Sweep

**Skip if `--quick` or `--skip-sweep`.**

Before council runs, dispatch a deep audit sweep to systematically discover issues across all changed files. This uses the same protocol as `$validate --deep` — see the deep audit protocol in the vibe skill (`skills/validate/`) for the full specification.

In summary:

1. Identify all files in scope (from epic commits or recent changes)
2. Chunk files into batches of 3-5 by line count (<=100 lines -> batch of 5, 101-300 -> batch of 3, >300 -> solo)
3. Dispatch up to 8 Explore agents in parallel, each with a mandatory 8-category checklist per file (resource leaks, string safety, dead code, hardcoded values, edge cases, concurrency, error handling, HTTP/web security)
4. Merge all explorer findings into a sweep manifest at `.agents/council/sweep-manifest.md`
5. Include sweep manifest in council packet — judges shift to adjudication mode (confirm/reject/reclassify sweep findings + add cross-cutting findings)

**Why:** Post-mortem council judges exhibit satisfaction bias when reviewing monolithic file sets — they stop at ~10 findings regardless of actual issue count. Per-file explorers with category checklists find 3x more issues, and the sweep manifest gives judges structured input to adjudicate rather than discover from scratch.

**Skip conditions:**
- `--quick` flag -> skip (fast inline path)
- `--skip-sweep` flag -> skip (old behavior: judges do pure discovery)
- No source files in scope -> skip (nothing to audit)

### Step 3: Council Validates the Work

## Council Verdict:

Run `$council` with the **retrospective** preset and always 3 judges:

```
$council --deep --preset=retrospective validate <epic-or-recent>
```

**Default (3 judges with retrospective perspectives):**
- `plan-compliance`: What was planned vs what was delivered? What's missing? What was added?
- `tech-debt`: What shortcuts were taken? What will bite us later? What needs cleanup?
- `learnings`: What patterns emerged? What should be extracted as reusable knowledge?

Post-mortem always uses 3 judges (`--deep`) because completed work deserves thorough review.

**Four-Surface Closure:** Validate all four surfaces -- Code, Documentation, Examples, and Proof. A PASS verdict requires all four surfaces addressed, not just code correctness. Read `skills/post-mortem/references/four-surface-closure.md` for the closure checklist and common gaps.

**Timeout:** Post-mortem inherits council timeout settings. If judges time out,
the council report will note partial results. Post-mortem treats a partial council
report the same as a full report — the verdict stands with available judges.

The plan/spec content is injected into the council packet context so the `plan-compliance` judge can compare planned vs delivered.

**With --quick (inline, no spawning):**
```
$council --quick validate <epic-or-recent>
```
Single-agent structured review. Fast wrap-up without spawning.

**With debate mode:**
```
$post-mortem --debate epic-123
```
Enables adversarial two-round review for post-implementation validation. Use for high-stakes shipped work where missed findings have production consequences. See `$council` docs for full --debate details.

**Advanced options (passed through to council):**
- `--mixed` — Cross-vendor (Claude + Codex) with retrospective perspectives
- `--preset=<name>` — Override with different personas (e.g., `--preset=ops` for production readiness)
- `--explorers=N` — Each judge spawns N explorers to investigate the implementation deeply before judging
- `--debate` — Two-round adversarial review (judges critique each other's findings before final verdict)

### Step 3.5: Prediction Accuracy (Pre-Mortem Correlation)

When a pre-mortem report exists for the current epic (`ls -t .agents/council/*pre-mortem*.md`), cross-reference its prediction IDs against actual vibe/implementation findings. Score each as HIT (prediction confirmed), MISS (did not materialize), or SURPRISE (unpredicted issue). Write a `## Prediction Accuracy` table in the report. Skip silently if no pre-mortem exists. See [references/prediction-tracking.md](references/prediction-tracking.md) for the full table format and scoring rules.

### Phase 2: Extract Learnings

Inline extraction of learnings from the completed work (formerly delegated to the retro skill).

#### Step EX.1: Gather Context

```bash
# Recent commits
git log --oneline -20 --since="7 days ago"

# Epic children (if epic ID provided)
br dep tree <epic-id> 2>/dev/null | head -20

# Recent plans and research
ls -lt .agents/plans/ .agents/research/ 2>/dev/null | head -10
```

Read relevant artifacts: research documents, plan documents, commit messages, and code changes. Use file reads and git commands to understand what was done.

**If retrospecting an epic:** Run the closure integrity quick-check from `references/context-gathering.md` (Phantom Bead Detection + Multi-Wave Regression Scan). Include any warnings in findings.

#### Step EX.2: Classify Learnings

Ask these questions:

**What went well?**
- What approaches worked?
- What was faster than expected?
- What should we do again?

**What went wrong?**
- What failed?
- What took longer than expected?
- What would we do differently?

**What did we discover?**
- New patterns found
- Codebase quirks learned
- Tool tips discovered
- Debugging insights
- Test pyramid gaps found during implementation or review

For each learning, capture:
- **ID**: L1, L2, L3...
- **Category**: debugging, architecture, process, testing, security
- **What**: The specific insight
- **Why it matters**: Impact on future work
- **Confidence**: high, medium, low

#### Step EX.3: Write Learnings

**Write to:** `.agents/learnings/YYYY-MM-DD-<topic>.md`

```markdown
---
id: learning-YYYY-MM-DD-<slug>
type: learning
date: YYYY-MM-DD
category: <category>
confidence: <high|medium|low>
maturity: provisional
utility: 0.5
---

# Learning: <Short Title>

## What We Learned

<1-2 sentences describing the insight>

## Why It Matters

<1 sentence on impact/value>

## Source

<What work this came from>

---

# Learning: <Next Title>

**ID**: L2
...
```

#### Step EX.3.5: Test Pyramid Gap Analysis

Compare planned vs actual test levels per the test pyramid standard (`test-pyramid.md` in the standards skill). For each closed issue: check planned `test_levels` metadata against actual test files. Write a `## Test Pyramid Assessment` table (Issue | Planned | Actual | Gaps | Action). Gaps with severity >= moderate become `next-work.jsonl` items with type `tech-debt`.

#### Step EX.4: Classify Learning Scope

For each learning extracted in Step EX.3, classify:

**Question:** "Does this learning reference specific files, packages, or architecture in THIS repo? Or is it a transferable pattern that helps any project?"

- **Repo-specific** -> Write to `.agents/learnings/` (existing behavior from Step EX.3). Use `git rev-parse --show-toplevel` to resolve repo root — never write relative to cwd.
- **Cross-cutting/transferable** -> Rewrite to remove repo-specific context (file paths, function names, package names), then:
  1. Write abstracted version to `~/.agents/learnings/YYYY-MM-DD-<slug>.md` (NOT local — one copy only)
  2. Run abstraction lint check:
     ```bash
     file="<path-to-written-global-file>"
     grep -iEn '(internal/|cmd/|\.go:|/pkg/|/src/|AGENTS\.md|CLAUDE\.md)' "$file" 2>/dev/null
     grep -En '[A-Z][a-z]+[A-Z][a-z]+\.(go|py|ts|rs)' "$file" 2>/dev/null
     grep -En '\./[a-z]+/' "$file" 2>/dev/null
     ```
     If matches: WARN user with matched lines, ask to proceed or revise. Never block the write.

**Note:** Each learning goes to ONE location (local or global). No `promoted_to` needed — there's no local copy to mark when writing directly to global.

**Example abstraction:**
- Local: "Compile's validate package needs O_CREATE|O_EXCL for atomic claims because Zeus spawns concurrent workers"
- Global: "Use O_CREATE|O_EXCL for atomic file creation when multiple processes may race on the same path"

#### Step EX.5: Write Structured Findings to Registry

Before backlog processing, normalize reusable council findings into `.agents/findings/registry.jsonl`.

Use the tracked contract in `docs/contracts/finding-registry.md`:

- persist only reusable findings that should change future planning or review behavior
- require `dedup_key`, provenance, `pattern`, `detection_question`, `checklist_item`, `applicable_when`, and `confidence`
- `applicable_when` must use the controlled vocabulary from the contract
- append or merge by `dedup_key`
- use the contract's temp-file-plus-rename atomic write rule

This registry is the v1 advisory prevention surface. It complements learnings and next-work; it does not replace them.

#### Step EX.6: Refresh Compiled Prevention Outputs

After the registry mutation, refresh compiled outputs immediately so the same session can benefit from the updated prevention set.

If `hooks/finding-compiler.sh` exists, run:

```bash
bash hooks/finding-compiler.sh --quiet 2>/dev/null || true
```

This promotes registry rows into `.agents/findings/*.md`, refreshes `.agents/planning-rules/*.md` and `.agents/pre-mortem-checks/*.md`, and rewrites draft constraint metadata under `.agents/constraints/`. Active enforcement still depends on the constraint index lifecycle and runtime hook support, but compilation itself is no longer deferred.

#### Step ACT.3: Feed Next-Work

Actionable improvements identified during processing -> append one schema v1.4
batch entry to `.agents/rpi/next-work.jsonl` using the tracked contract in
[`../../docs/contracts/next-work.schema.md`](../../docs/contracts/next-work.schema.md)
and the write procedure in
[`references/harvest-next-work.md`](references/harvest-next-work.md).
Follow the claim/finalize lifecycle documented in `references/harvest-next-work.md`.

```bash
mkdir -p .agents/rpi
# Build VALID_ITEMS via the schema-validation flow in references/harvest-next-work.md
# Then append one entry per post-mortem / epic.
# If a harvested item already maps to a known proof surface, preserve it on the
# item as "proof_ref" instead of burying target IDs in free text. Example item:
# [{"title":"Verify the parity gate after proof propagation lands","type":"task","severity":"medium","source":"council-finding","description":"Re-run the targeted validator after the follow-up lands.","target_repo":"agentops","proof_ref":{"kind":"execution_packet","run_id":"6f36a5640805","path":".agents/rpi/runs/6f36a5640805/execution-packet.json"}}]
ENTRY_TIMESTAMP="$(date -Iseconds)"
SOURCE_EPIC="${EPIC_ID:-recent}"
VALID_ITEMS_JSON="${VALID_ITEMS_JSON:-[]}"

printf '%s\n' "$(jq -cn \
  --arg source_epic "$SOURCE_EPIC" \
  --arg timestamp "$ENTRY_TIMESTAMP" \
  --argjson items "$VALID_ITEMS_JSON" \
  '{
    source_epic: $source_epic,
    timestamp: $timestamp,
    items: $items,
    consumed: false,
    claim_status: "available",
    claimed_by: null,
    claimed_at: null,
    consumed_by: null,
    consumed_at: null
  }'
)" >> .agents/rpi/next-work.jsonl
```

#### Step ACT.4: Update Marker

```bash
date -Iseconds > .agents/ao/last-processed
```

This must be the LAST action in Phase 4.

**Phases 3-6 (Maintenance):** Read `references/maintenance-phases.md` for backlog processing, activation, retirement, and harvesting phases. Load when `--process-only` flag is set or when running full post-mortem.

### Close the ms outcome loop (optional)

If `ms` is installed (`command -v ms`), grade each skill whose guidance this session **actually used** (genuinely consulted, not merely trigger-matched): `ms outcome <skill> --success` (helped) or `ms outcome <skill> --failure` (misled/didn't apply) — only real consultations, an honest empty set beats a padded one. Skip silently if `ms` is not present.

### Step 7: Report to User

Tell the user:
1. Council verdict on implementation
2. Key learnings
3. Any follow-up items
4. Location of post-mortem report
5. Knowledge flywheel status
6. **Suggested next `$rpi` command** from the harvested `## Next Work` section (ALWAYS — this is how the flywheel spins itself)
7. ALL proactive improvements, organized by priority (highlight one quick win)
8. Knowledge lifecycle summary (Phase 3-5 stats)

**The next `$rpi` suggestion is MANDATORY, not opt-in.** After every post-mortem, present the highest-severity harvested item as a ready-to-copy command:

```markdown
## Flywheel: Next Cycle

Based on this post-mortem, the highest-priority follow-up is:

> **<title>** (<type>, <severity>)
> <1-line description>

Ready to run:
```
$rpi "<title>"
```

Or see all N harvested items in `.agents/rpi/next-work.jsonl`.
```

If no items were harvested, write: "Flywheel stable — no follow-up items identified."

---

## Integration with Workflow

```
$plan epic-123
    |
    v
$pre-mortem (council on plan)
    |
    v
$implement
    |
    v
$validate (council on code)
    |
    v
Ship it
    |
    v
$post-mortem              <-- You are here
    |
    |-- Phase 1: Council validates implementation
    |-- Phase 2: Extract learnings (inline)
    |-- Phase 3: Process backlog (score, dedup, flag stale)
    |-- Phase 4: Activate (promote to MEMORY.md, compile constraints)
    |-- Phase 5: Retire stale learnings
    |-- Phase 6: Harvest next work
    |-- Suggest next $rpi --------------------+
                                              |
    +----------------------------------------+
    |  (flywheel: learnings become next work)
    v
$rpi "<highest-priority enhancement>"
```

---

## Examples

### Wrap Up Recent Work

**User says:** `$post-mortem`

**What happens:**
1. Agent scans recent commits.
2. Runs `$council --deep validate recent`.
3. Extracts learnings, processes backlog, and promotes items.
4. Harvests next-work to `.agents/rpi/next-work.jsonl`.

**Result:** Report with learnings, stats, and a suggested `$rpi` command.

### Other Modes

- **Epic-specific:** `$post-mortem ag-5k2` — review against the target plan
- **Quick capture:** `$post-mortem --quick "insight"` — write a learning without council
- **Process-only:** `$post-mortem --process-only` — run backlog processing only
- **Cross-vendor:** `$post-mortem --mixed ag-3b7` — broaden judgment coverage

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Council times out | Epic too large or too many files changed | Split post-mortem into smaller reviews or increase timeout |
| No next-work items harvested | Council found no tech debt or improvements | Flywheel stable — write entry with empty items array to next-work.jsonl |
| Checkpoint-policy preflight blocks | Prior FAIL verdict in ratchet chain without fix | Resolve prior failure (fix + re-vibe) or skip checkpoint-policy via `--skip-checkpoint-policy` |
| Metadata verification fails | Plan vs actual files mismatch or missing cross-references | Include failures in council packet as `context.metadata_failures` — judges assess severity |

---

## Compound-Engineering Retro (`--compound`)

A comparative-delta mode for projects that run `ao goals measure` repeatedly
across iterations of the same domain slice. Use when a slice has ≥2 iterations
in the verdict ledger and you want to know: what improved, what regressed, and
what the learning yield was since the last run.

**Trigger:** run this mode after any `ao goals measure` where the slice has a
prior iteration record in `.agents/goals/verdict-ledger.json`.

```bash
# Confirm ≥2 iterations exist for a directive in the slice:
jq '[.records[] | select(.record_type=="iteration" and .directive_id=="d-<id>")] | length' \
   .agents/goals/verdict-ledger.json

# Run a new iteration (appends one record per directive):
ao goals measure

# Browse iteration history:
ao goals history --goal <directive-id>
```

Then follow the step-by-step procedure in
[references/compound-engineering-retro.md](references/compound-engineering-retro.md)
(Steps CE.0–CE.5): extract N and N-1 records from the ledger, compute the
verdict and satisfaction delta, count learning yield, and write the delta as a
draft learning to `.agents/learnings/YYYY-MM-DD-<slice>-iter-delta.md`.

The output learning carries `status: draft` and the run IDs of both iterations;
human or Tier-3 synthesis promotes it to `status: reviewed`.

**Closing the loop with re-steer.** When the delta shows a directive failing
chronically, the verdict ledger also drives auto re-steer: `ao goals steer
recommend` prints policy-driven directive mutations from the same ledger, and
`ao goals steer apply` writes the chosen mutation to GOALS.md — human-gated, via
the non-lossy patcher (policy `auto_apply` plus explicit confirmation; ADR-0006).
The compound retro names *what* regressed; re-steer proposes *how* the directive
should change. See `skills/goals/SKILL.md`.

---

## See Also

- `skills/council/SKILL.md` — Multi-model validation council
- `skills/validate/SKILL.md` — Council validates code (`$validate` after coding)
- `skills/pre-mortem/SKILL.md` — Council validates plans (before implementation)


## Reference Documents

- [references/harvest-next-work.md](references/harvest-next-work.md)
- [references/learning-templates.md](references/learning-templates.md)
- [references/plan-compliance-checklist.md](references/plan-compliance-checklist.md)
- [references/closure-integrity-audit.md](references/closure-integrity-audit.md)
- [references/security-patterns.md](references/security-patterns.md)
- [references/checkpoint-policy.md](references/checkpoint-policy.md)
- [references/metadata-verification.md](references/metadata-verification.md)
- [references/context-gathering.md](references/context-gathering.md)
- [references/output-templates.md](references/output-templates.md)
- [references/backlog-processing.md](references/backlog-processing.md)
- [references/activation-policy.md](references/activation-policy.md)
- [references/prediction-tracking.md](references/prediction-tracking.md)
- [references/retro-history.md](references/retro-history.md)
- [references/streak-tracking.md](references/streak-tracking.md)
- [references/maintenance-phases.md](references/maintenance-phases.md)
- [references/four-surface-closure.md](references/four-surface-closure.md)
- [references/compound-engineering-retro.md](references/compound-engineering-retro.md)
