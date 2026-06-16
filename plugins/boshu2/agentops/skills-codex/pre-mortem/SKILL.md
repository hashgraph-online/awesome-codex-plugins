---
name: pre-mortem
description: "Run pre mortem."
---
# Pre-Mortem Skill

> **Purpose:** Is this plan/spec good enough to implement?

> **Mandatory for 3+ issue epics.** Pre-mortem is enforced by hook when `$crank` is invoked on epics with 3+ child issues. 6/6 consecutive positive ROI. Bypass: `--skip-pre-mortem` flag or `AGENTOPS_SKIP_PRE_MORTEM_GATE=1`.

Run `$council validate` on a plan or spec to get multi-model judgment before committing to implementation.

---

## Quick Start

```bash
$pre-mortem                                         # validates most recent plan (inline, no spawning)
$pre-mortem path/to/PLAN.md                         # validates specific plan (inline)
$pre-mortem --deep path/to/SPEC.md                  # 4 judges (thorough review, spawns agents)
$pre-mortem --mixed path/to/PLAN.md                 # cross-vendor (Claude + Codex)
$pre-mortem --preset=architecture path/to/PLAN.md   # architecture-focused review
$pre-mortem --explorers=3 path/to/SPEC.md           # deep investigation of plan
$pre-mortem --debate path/to/PLAN.md                # two-round adversarial review
```

---

## Execution Steps

### Step 0: Bead-Input Pre-Flight (Mandatory)

When the input to `$pre-mortem` is a bead ID (`[a-z]{2,6}-[0-9a-z.]+`) and the plan is full-complexity, older than 7 days, or inherited from a prior session, run `ao beads verify <bead-id>` as the first action.

```bash
if [[ "$INPUT" =~ ^[a-z]{2,6}-[0-9a-z.]+$ ]]; then
    ao beads verify "$INPUT" || true
fi
```

If verification reports STALE citations, stop in interactive mode and ask for scope re-validation before council review. In autonomous RPI mode, record the stale-scope evidence in the council packet and do not continue the go/no-go judgment against stale evidence.

This implements the shared stale-scope validation rule: inherited scope estimates must be re-validated against HEAD before acting on deferred beads, handoff docs, or prior-session plans.

### Step 1: Find the Plan/Spec

**If path provided:** Use it directly.

**If no path:** Find most recent plan:
```bash
ls -lt .agents/plans/ 2>/dev/null | head -3
ls -lt .agents/specs/ 2>/dev/null | head -3
```

Use the most recent file. If nothing found, ask user.

### Step 1.4: Retrieve Prior Learnings (Mandatory)

Before review, retrieve learnings relevant to this plan's domain:
```bash
if command -v ao &>/dev/null; then
    ao lookup --query "<plan goal or title>" --limit 5 2>/dev/null | head -30
fi
```
If learnings are returned, include them as `known_context` in the review packet. Cite any learning by filename when it influences a prediction. Skip silently if ao is unavailable or returns no results.

### Step 1.4b: Load Compiled Prevention First (Mandatory)

Before quick or deep review, load compiled checks from `.agents/pre-mortem-checks/*.md` when they exist. This is separate from flywheel search and does NOT get skipped by `--quick`.

Use the tracked contracts in `docs/contracts/finding-compiler.md` and `docs/contracts/finding-registry.md`:

- prefer compiled pre-mortem checks first
- rank by severity, `applicable_when` overlap, language overlap, and literal plan-text overlap
- when the plan names files, rank changed-file overlap ahead of generic keyword matches
- cap at top 5 findings / check files
- if compiled checks are missing, incomplete, or fewer than the matched finding set, fall back to `.agents/findings/registry.jsonl`
- fail open:
  - missing compiled directory or registry -> skip silently
  - empty compiled directory or registry -> skip silently
  - malformed line -> warn and ignore that line
  - unreadable file -> warn once and continue without findings

Include matched entries in the council packet as `known_risks` with:
- `id`
- `pattern`
- `detection_question`
- `checklist_item`

Use the same ranked packet contract as `$plan`: compiled checks first, then active findings fallback, then matching high-severity next-work context when relevant. Avoid re-ranking with an unrelated heuristic inside pre-mortem; the point is consistent carry-forward, not a fresh retrieval policy per phase.

**Record citations for applied knowledge:**

After including matched entries as `known_risks`, record each citation so the flywheel feedback loop can track influence:
```bash
# Only use "applied" when the finding actually influenced the council packet.
# Use "retrieved" for items loaded but not referenced in the risk assessment.
ao metrics cite "<finding-path>" --type applied 2>/dev/null || true   # influenced risk assessment
ao metrics cite "<finding-path>" --type retrieved 2>/dev/null || true # loaded but not used
```

**Section evidence:** When lookup results include `section_heading`, `matched_snippet`, or `match_confidence` fields, prefer the matched section over the whole file — it pinpoints the relevant portion. Higher `match_confidence` (>0.7) means the section is a strong match; lower values (<0.4) are weaker signals. Use the `matched_snippet` as the primary context rather than reading the full file.

### Step 1.5: Fast Path (--quick mode)

**By default, pre-mortem runs inline (`--quick`)** — single-agent structured review, no spawning. This catches real implementation issues at ~10% of full council cost (proven in ag-nsx: 3 actionable bugs found inline that would have caused runtime failures).

In `--quick` mode, skip Steps 1a and 1b as standalone pre-processing phases. If `PRODUCT.md` exists, Step 1b's product context is still loaded inline during the quick review. The mandatory `ao lookup` retrieval in Step 1.4 and compiled prevention load in Step 1.4b still run in quick mode. `--deep`, `--mixed`, `--debate`, and `--explorers` add the dedicated product perspective and wider council fan-out.

To escalate to full multi-judge council, use `--deep` (4 judges) or `--mixed` (cross-vendor).

### Step 1.6: Scope Mode Selection

Before running council, determine the review posture. Three modes:

| Mode | When to Use | Posture |
|------|-------------|---------|
| **SCOPE EXPANSION** | Greenfield features, user says "go big" | Dream big. What's the 10-star version? Push scope UP. |
| **HOLD SCOPE** | Bug fixes, refactors, most plans | Maximum rigor within accepted scope. Make it bulletproof. |
| **SCOPE REDUCTION** | Plan touches >15 files, overbuilt | Strip to essentials. What's the minimum that ships value? |

**Auto-detection (when user doesn't specify):**
- Greenfield feature → default EXPANSION
- Bug fix or hotfix → default HOLD SCOPE
- Refactor → default HOLD SCOPE
- Plan touching >15 files → suggest REDUCTION
- User says "go big" / "ambitious" → EXPANSION

**Critical rule:** Once mode is selected, COMMIT to it in the council packet. Do not silently drift. Include `scope_mode: <expansion|hold|reduction>` in the council packet context.

**Mode-specific council instructions:**
- **EXPANSION:** Add to judge prompt: "What would make this 10x more ambitious for 2x the effort? What's the platonic ideal? List 3 delight opportunities."
- **HOLD SCOPE:** Add to judge prompt: "The plan's scope is accepted. Your job: find every failure mode, test every edge case, ensure observability. Do not argue for less work."
- **REDUCTION:** Add to judge prompt: "Find the minimum viable version. Everything else is deferred. What can be a follow-up? Separate must-ship from nice-to-ship."

### Step 1a: Search Knowledge Flywheel

**Skip if `--quick`.** Only run this step for `--deep`, `--mixed`, or `--debate`.

```bash
if command -v ao &>/dev/null; then
    ao search "plan validation lessons <goal>" 2>/dev/null | head -10
fi
```
If ao returns prior plan review findings, include them as context for the council packet. Skip silently if ao is unavailable or returns no results.

### Step 1b: Check for Product Context

**Skip if `--quick` as a separate pre-processing phase.** In quick mode, the same product context is still loaded inline during review. In non-quick modes, add the dedicated product perspective.

```bash
if [ -f PRODUCT.md ]; then
  # PRODUCT.md exists — include product perspectives alongside plan-review
fi
```

When `PRODUCT.md` exists in the project root AND the user did NOT pass an explicit `--preset` override:
1. Read `PRODUCT.md` content and include in the council packet via `context.files`
2. In `--quick` mode, keep the review inline and require the reviewer to assess user-value, adoption-barriers, and competitive-position directly from `PRODUCT.md`.
3. In non-quick modes, add a single consolidated `product` perspective to the council invocation:
   ```
   $council --preset=plan-review --perspectives="product" validate <plan-path>
   ```
   This yields 3 judges total (2 plan-review + 1 product). The product judge covers user-value, adoption-barriers, and competitive-position in a single review.
4. With `--deep`: 5 judges (4 plan-review + 1 product).

When `PRODUCT.md` exists BUT the user passed an explicit `--preset`: skip product auto-include (user's explicit preset takes precedence).

When `PRODUCT.md` does not exist: proceed to Step 2 unchanged.

> **Tip:** Create `PRODUCT.md` from `docs/PRODUCT-TEMPLATE.md` to enable product-aware plan validation.

### Step 1.7: Load Council FAIL Patterns (Mandatory)

Read `skills/pre-mortem/references/council-fail-patterns.md` for the top 8 council FAIL patterns to check against.

These patterns are derived from 124 analyzed FAIL verdicts across 946 council sessions. They apply to both `--quick` and `--deep` modes.

### Step 2: Run Council Validation

**Default (inline, no spawning):**
```
$council --quick validate <plan-path>
```
Single-agent structured review. Catches real implementation issues at ~10% of full council cost. Sufficient for most plans (proven across 6+ epics).

Default (2 judges with plan-review perspectives) applies when you intentionally run non-quick council mode.

**With --deep (4 judges with plan-review perspectives):**
```
$council --deep --preset=plan-review validate <plan-path>
```
Spawns 4 judges:
- `missing-requirements`: What's not in the spec that should be? What questions haven't been asked?
- `feasibility`: What's technically hard or impossible here? What will take 3x longer than estimated?
- `scope`: What's unnecessary? What's missing? Where will scope creep?
- `spec-completeness`: Are boundaries defined? Do conformance checks cover all acceptance criteria? Is the plan mechanically verifiable?

Use `--deep` for high-stakes plans (migrations, security, multi-service, 7+ issues).

**With --mixed (cross-vendor):**
```
$council --mixed --preset=plan-review validate <plan-path>
```
3 Claude + 3 Codex agents for cross-vendor plan validation with plan-review perspectives.

**With explicit preset override:**
```
$pre-mortem --preset=architecture path/to/PLAN.md
```
Explicit `--preset` overrides the automatic plan-review preset. Uses architecture-focused personas instead.

**With explorers:**
```
$council --deep --preset=plan-review --explorers=3 validate <plan-path>
```
Each judge spawns 3 explorers to investigate aspects of the plan's feasibility against the codebase. Useful for complex migration or refactoring plans.

**With debate mode:**
```
$pre-mortem --debate
```
Enables adversarial two-round review for plan validation. Use for high-stakes plans where multiple valid approaches exist. See `$council` docs for full --debate details.

### Step 2.4: Temporal Interrogation (--deep and --temporal)

**Included automatically with `--deep`.** Also available via `--temporal` flag for quick reviews.

Walk through the plan's implementation timeline to surface time-dependent risks:

| Phase | Questions |
|-------|-----------|
| **Hour 1: Setup** | What blocks the first meaningful code change? Are dependencies available? |
| **Hour 2: Core** | Which files change in what order? Are there circular dependencies? |
| **Hour 4: Integration** | What fails when components connect? Which error paths are untested? |
| **Hour 6+: Ship** | What "should be quick" but historically isn't? What context is lost overnight? |

Add to each judge's prompt when temporal interrogation is active:

```
TEMPORAL INTERROGATION: Walk through this plan's implementation timeline.
For each phase (Hour 1, 2, 4, 6+), identify:
1. What blocks progress at this point?
2. What fails silently at this point?
3. What compounds if not caught at this point?
Report temporal findings in a separate "Timeline Risks" section.
```

**Auto-triggered** (even without `--deep`) when the plan has 5+ files or 3+ sequential dependencies.

**Retro history correlation:** When `.agents/retro/index.jsonl` has 2+ entries, load the last 5 retros and check for recurring timeline-phase failures. Auto-escalate severity for phases that caused issues in prior retros.

Temporal findings appear in the report as a `## Timeline Risks` table. See [references/temporal-interrogation.md](references/temporal-interrogation.md) for the full framework.

### Step 2.5: Error & Rescue Map (Mandatory for plans with external calls)

When the plan introduces methods, services, or codepaths that can fail, the council packet MUST include an Error & Rescue Map. If the plan omits one, generate it during review.

Include in the council packet as `context.error_map`:

| Method/Codepath | What Can Go Wrong | Exception/Error | Rescued? | Rescue Action | User Sees |
|-----------------|-------------------|-----------------|----------|---------------|-----------|
| `ServiceName#method` | API timeout | `TimeoutError` | Y/N | Retry 2x, then raise | "Service unavailable" |

**Rules:**
- Every external call (API, database, file I/O) must have at least one row
- `rescue StandardError` or bare `except:` is always a smell — name specific exceptions
- Every rescued error must: retry with backoff, degrade gracefully, OR re-raise with context
- For LLM/AI calls: map malformed response, empty response, hallucinated JSON, and refusal as separate failure modes
- Each GAP (unrescued error) is a finding with severity=significant

See `references/error-rescue-map-template.md` for the full template with worked examples.

### Step 2.6: Council FAIL Pattern Check (Mandatory)

**Council FAIL Pattern Check:** Evaluate the plan against the top 8 council FAIL patterns (see [references/council-fail-patterns.md](references/council-fail-patterns.md)): missing mechanical verification, self-assessment, context rot, propagation blindness, plan oscillation, dead infrastructure activation, missing rollback map, and four-surface closure gap. Each pattern violation is a finding with severity based on the calibration table in the reference.

Add to each judge's prompt:

```
COUNCIL FAIL PATTERN CHECK: Review this plan for the top 8 council FAIL patterns:
1. Missing mechanical verification — are all gates automated?
2. Self-assessment — is validation external to the implementer?
3. Context rot — are phase boundaries enforced with fresh sessions?
4. Propagation blindness — is the full change surface enumerated?
5. Plan oscillation — is direction validated before propagation?
6. Dead infrastructure activation — does the plan provision anything without activation tests?
7. Missing rollback map — does any production-state change lack a rollback procedure?
8. Four-surface closure — does the plan address Code + Docs + Examples + Proof for every feature?
Report FAIL pattern findings in a "FAIL Pattern Risks" section.
```

**Auto-triggered** for all plans (both `--quick` and `--deep` modes).

### Step 2.7: Test Pyramid Coverage Check (Mandatory)

Validate that the plan includes appropriate test levels per the test pyramid standard (`test-pyramid.md` in the standards skill).

**Check each issue in the plan:**

| Question | Expected | Finding if Missing |
|----------|----------|--------------------|
| Does any issue touching external APIs include L0 (contract) tests? | Yes | severity=significant: "Missing contract tests for API boundary" |
| Does every feature/bug issue include L1 (unit) tests? | Yes | severity=significant: "Missing unit tests for feature/bug issue" |
| Do cross-module changes include L2 (integration) tests? | Yes | severity=moderate: "Missing integration tests for cross-module change" |
| Are L4+ levels deferred to human gate (not agent-planned)? | Yes | severity=low: "Agent planning L4+ tests — these require human-defined scenarios" |

Add to each judge's prompt when test pyramid check is active:

```
TEST PYRAMID CHECK: Review the plan's test coverage against the L0-L7 pyramid.
For each issue, verify:
1. Are the right test levels specified? (L0 for boundaries, L1 for behavior, L2 for integration)
2. Are there gaps where tests should exist but aren't planned?
3. Are any agent-autonomous levels (L0-L3) missing from code-change issues?
Report test pyramid findings in a "Test Coverage Gaps" section.
```

**Auto-triggered** when any issue in the plan modifies source code files (`.go`, `.py`, `.ts`, `.rs`, `.js`).

### Step 2.8: Input Validation Check (Mandatory for enum-like fields)

When the plan introduces or modifies fields with a bounded set of valid values (enums, tier names, mode strings, status codes), verify the plan includes validation logic.

| Question | Expected | Finding if Missing |
|----------|----------|--------------------|
| Does every new enum-like field have a validation guard? | Yes | severity=significant: "No validation for enum field — invalid values pass silently" |
| Is there a defined fallback for unrecognized values? | Yes | severity=moderate: "No fallback behavior specified for invalid input" |
| Are valid values defined as a constant set (not inline strings)? | Yes | severity=low: "Valid values are inline strings — extract to named constant set" |

**Auto-triggered** when the plan introduces struct fields with comments mentioning valid values, config fields with bounded options, or string fields parsed from user input.

### Step 2.9: No-self-grading invariant (author ≠ validator)

The pre-mortem verdict must NOT be graded by the plan's own author. A verdict produced by the authoring context is autocorrelated — the same assumptions that shaped the plan pass it. This is the no-self-grading invariant (`ag-lmdx.4`): the independent-trust-domain check on the plan-acceptance verdict.

**Rule:** the judge context MUST be distinct from the author context. Validation MAY run inside the authoring session, but the judge MUST be a **blind sub-agent** — a fresh, context-isolated agent acting as if it has no authoring context. Record `judge_id` (the isolated sub-agent context) distinct from `author_id` (the planning context). The `--deep`/`--mixed` council judges satisfy this when they are context-isolated sub-agents; an inline self-review by the planning agent does NOT.

**Refuse** to emit a PASS verdict when the judge context equals the author context (`judge_id == author_id`) — re-run the verdict through a blind sub-agent judge instead.

**Escape:** `--allow-self` (default OFF) waives the invariant for the inline fallback only (e.g. no sub-agent runtime available). Using it stamps the verdict as self-graded; downstream `ao turn verify` reports it as waived, not independently validated.

**Enforcement:** `ao turn verify <bead>` evaluates the `author_neq_validator` predicate from the turn-input file's `author_id`/`judge_id` and fails the Evidenced-Turn DoD on a self-graded verdict unless `--allow-self` is passed.

### Step 3: Interpret Council Verdict

| Council Verdict | Pre-Mortem Result | Action |
|-----------------|-------------------|--------|
| PASS | Ready to implement | Proceed |
| WARN | Review concerns | Address warnings or accept risk |
| FAIL | Not ready | Fix issues before implementing |

### Step 4: Write Pre-Mortem Report

**Write to:** `.agents/council/YYYY-MM-DD-pre-mortem-<topic>.md`

```markdown
---
id: pre-mortem-YYYY-MM-DD-<topic-slug>
type: pre-mortem
date: YYYY-MM-DD
source: "[[.agents/plans/YYYY-MM-DD-<plan-slug>]]"
prediction_ids:
  - pm-YYYYMMDD-001
  - pm-YYYYMMDD-002
---

# Pre-Mortem: <Topic>

## Council Verdict: PASS / WARN / FAIL

| ID | Judge | Finding | Severity | Prediction |
|----|-------|---------|----------|------------|
| pm-YYYYMMDD-001 | Missing-Requirements | ... | significant | <what will go wrong> |
| pm-YYYYMMDD-002 | Feasibility | ... | significant | <what will go wrong> |
| pm-YYYYMMDD-003 | Scope | ... | moderate | <what will go wrong> |

## Pseudocode Fixes

**Every finding that implies a code change MUST include implementation-ready pseudocode**, not prose-only descriptions. Write the pseudocode in the language of the target file. Workers read issue descriptions, not pre-mortem reports — vague prose leads to workers reimplementing the bug.

Format each code-fix finding as:

```
Finding: F1 — <concise description>
Severity: <severity>
Fix (pseudocode):
  ```<language>
  // pseudocode in the target file's language
  if tier == "inherit" || tier == "" {
      return "balanced"  // inherit always resolves to balanced
  }
  ```
Affected files: <path(s)>
```

Prose-only fix descriptions (e.g., "The inherit tier should fall back to balanced") are insufficient when the fix involves specific logic. If a finding is purely architectural or process-related with no code change, prose is acceptable.

## Shared Findings
- ...

## Known Risks Applied
- `<finding-id>` — `<why it matched this plan>`

## Concerns Raised
- ...

## Recommendation
<council recommendation>

## Decision Gate

[ ] PROCEED - Council passed, ready to implement
[ ] ADDRESS - Fix concerns before implementing
[ ] RETHINK - Fundamental issues, needs redesign
```

Each finding gets a unique prediction ID (`pm-YYYYMMDD-NNN`) for downstream correlation. See [references/prediction-tracking.md](references/prediction-tracking.md) for the full tracking lifecycle.

### Step 4.5: Persist Reusable Findings

If the verdict is `WARN` or `FAIL`, persist only the reusable plan/spec failures to `.agents/findings/registry.jsonl`.

Use the finding-registry contract:

- required fields: `dedup_key`, provenance, `pattern`, `detection_question`, `checklist_item`, `applicable_when`, `confidence`
- `applicable_when` must use the controlled vocabulary from the contract
- append or merge by `dedup_key`
- use the contract's temp-file-plus-rename atomic write rule

Do NOT write every comment. Persist only findings that should change future planning or review behavior.

After the registry update, if `hooks/finding-compiler.sh` exists, run:

```bash
bash hooks/finding-compiler.sh --quiet 2>/dev/null || true
```

Every reusable finding write must include `dedup_key` and refresh compiled findings with `finding-compiler.sh` when that hook exists.

This refreshes `.agents/findings/*.md`, `.agents/planning-rules/*.md`, `.agents/pre-mortem-checks/*.md`, and draft constraint metadata in the same session. `session-end-maintenance.sh` remains the idempotent backstop.

### Step 4.6: Copy Pseudocode Fixes into Plan Issues

When pre-mortem findings are applied to plan issues (via `bd update` or manual issue/task edits), **copy the pseudocode block verbatim into the issue body**. Workers read issue descriptions — they do not read pre-mortem reports. If the pseudocode lives only in the pre-mortem report, workers will reimplement the fix from scratch and often get it wrong.

For each finding with a pseudocode fix:
1. Identify which plan issue the finding applies to
2. Append a `## Pre-Mortem Fix` section to that issue's description containing the pseudocode block and affected file paths
3. If no matching issue exists, note the gap in the report's Recommendation section

### Step 5: Record Ratchet Progress

```bash
ao ratchet record pre-mortem 2>/dev/null || true
```

### Step 6: Report to User

Tell the user:
1. Council verdict (PASS/WARN/FAIL)
2. Key concerns (if any)
3. Recommendation
4. Location of pre-mortem report

---

## Integration with Workflow

```
$plan epic-123
    │
    ▼
$pre-mortem                    ← You are here
    │
    ├── PASS → $implement
    ├── WARN → Review, then $implement or fix
    └── FAIL → Fix plan, re-run $pre-mortem
```

---

## Examples

### Validate a Plan (Default — Inline)

**User says:** `$pre-mortem .agents/plans/2026-02-05-auth-system.md`

**What happens:**
1. Agent reads the auth system plan
2. Runs `$council --quick validate <plan-path>` (inline, no spawning)
3. Single-agent structured review finds missing error handling for token expiry
4. Council verdict: WARN
5. Output written to `.agents/council/2026-02-13-pre-mortem-auth-system.md`

**Result:** Fast pre-mortem report with actionable concerns. Use `--deep` for high-stakes plans needing multi-judge consensus.

### Cross-Vendor Plan Validation

**User says:** `$pre-mortem --mixed .agents/plans/2026-02-05-auth-system.md`

**What happens:**
1. Agent runs mixed-vendor council (3 Claude + 3 Codex)
2. Cross-vendor perspectives catch platform-specific issues
3. Verdict: PASS with 2 warnings

**Result:** Higher confidence from cross-vendor validation before committing resources.

### Auto-Find Recent Plan

**User says:** `$pre-mortem`

**What happens:**
1. Agent scans `.agents/plans/` for most recent plan
2. Finds `2026-02-13-add-caching-layer.md`
3. Runs inline council validation (no spawning, ~10% of full council cost)
4. Records ratchet progress

**Result:** Frictionless validation of most recent planning work.

### Deep Review for High-Stakes Plan

**User says:** `$pre-mortem --deep .agents/plans/2026-02-05-migration-plan.md`

**What happens:**
1. Agent reads the migration plan
2. Searches knowledge flywheel for prior migration learnings
3. Checks PRODUCT.md for product context
4. Runs `$council --deep --preset=plan-review validate <plan-path>` (4 judges)
5. Council verdict with multi-perspective consensus

**Result:** Thorough multi-judge review for plans where the stakes justify spawning agents.

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Council times out | Plan too large or complex for judges to review in allocated time | Split plan into smaller epics or increase timeout via council config |
| FAIL verdict on valid plan | Judges misunderstand domain-specific constraints | Add context via `--perspectives-file` with domain explanations |
| Product perspectives missing | PRODUCT.md exists but not included in council packet | Verify PRODUCT.md is in project root and no explicit `--preset` override was passed |
| Pre-mortem gate blocks $crank | Epic has 3+ issues and no pre-mortem ran | Run `$pre-mortem` before `$crank`, or use `--skip-pre-mortem` flag (not recommended) |
| Spec-completeness judge warns | Plan lacks Boundaries or Conformance Checks sections | Add SDD sections or accept WARN (backward compatibility — not a failure) |
| Mandatory for epics enforcement | Hook blocks $crank on 3+ issue epic without pre-mortem | Run `$pre-mortem` first, or set `AGENTOPS_SKIP_PRE_MORTEM_GATE=1` to bypass |

---

## See Also

- `../council/SKILL.md` — Multi-model validation council
- `../plan/SKILL.md` — Create implementation plans
- `../validate/SKILL.md` — Validate code after implementation

## Reference Documents

- [references/council-fail-patterns.md](references/council-fail-patterns.md)
- [references/enhancement-patterns.md](references/enhancement-patterns.md)
- [references/error-rescue-map-template.md](references/error-rescue-map-template.md)
- [references/failure-taxonomy.md](references/failure-taxonomy.md)
- [references/simulation-prompts.md](references/simulation-prompts.md)
- [references/prediction-tracking.md](references/prediction-tracking.md)
- [references/spec-verification-checklist.md](references/spec-verification-checklist.md)
- [references/temporal-interrogation.md](references/temporal-interrogation.md)
- [references/scope-predicate-positive-negative-cases.md](references/scope-predicate-positive-negative-cases.md)

## Local Resources

### references/

- [references/council-fail-patterns.md](references/council-fail-patterns.md)
- [references/enhancement-patterns.md](references/enhancement-patterns.md)
- [references/error-rescue-map-template.md](references/error-rescue-map-template.md)
- [references/failure-taxonomy.md](references/failure-taxonomy.md)
- [references/prediction-tracking.md](references/prediction-tracking.md)
- [references/scope-predicate-positive-negative-cases.md](references/scope-predicate-positive-negative-cases.md)
- [references/simulation-prompts.md](references/simulation-prompts.md)
- [references/spec-verification-checklist.md](references/spec-verification-checklist.md)
- [references/temporal-interrogation.md](references/temporal-interrogation.md)

### scripts/

- `scripts/validate.sh`
