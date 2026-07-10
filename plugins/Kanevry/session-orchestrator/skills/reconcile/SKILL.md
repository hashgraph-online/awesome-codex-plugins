---
name: reconcile
user-invocable: true
tags: [learning, rules, intelligence, meta]
model: sonnet
model-preference: sonnet
model-preference-codex: gpt-5.4-mini
model-preference-cursor: claude-sonnet-4-6
args-schema:
  - flag: --dry-run
    description: "Print proposals without writing anything or rendering the approval AUQ"
description: >
  Use this skill when the user wants to reconcile learnings into rules, run /reconcile, propose
  rules from learnings, turn learnings into .claude/rules/ entries, or review what rules would be
  generated from current session learnings. On-demand version of session-end Phase 3.6.8.
---

> **Platform Note:** State files use the platform's native directory: `.claude/` (Claude Code), `.codex/` (Codex CLI), or `.cursor/` (Cursor IDE). Shared metrics live in `.orchestrator/metrics/`. See `skills/_shared/platform-tools.md`.

# Reconcile Skill

On-demand version of the session-end Phase 3.6.8 reconciliation flow. Turns eligible learnings
from `.orchestrator/metrics/learnings.jsonl` into proposed `.claude/rules/<slug>.md` entries,
presenting each batch of 4 to the coordinator via AUQ multiSelect for operator approval before
any file is written. Advisory-only — rules are NEVER auto-applied.

## Posture Contract (load-bearing — read before executing)

- **Advisory-only.** No rule is ever written without explicit operator approval via AUQ.
  The AUQ multiSelect is the mandatory gate; there is no bypass.
- **Never-always-on invariant.** The reconcile engine's emitter (`emitter.mjs`) throws
  on any eligible learning that would produce an `alwaysApply: true` rule — the engine
  structurally cannot emit always-on rules. This invariant is enforced upstream, not by
  this skill.
- **Engine never writes `.claude/rules/`.** `runReconcile` computes proposals and records
  them in the idempotency sidecar only. The only module that writes `.claude/rules/` is
  `writer.mjs`, and only AFTER the operator approves proposals via AUQ.
- **Same pipeline as session-end Phase 3.6.8.** This skill uses the identical engine and
  writer seams as the automatic session-end reconciliation phase — operator experience is
  consistent, and any fixes to the engine benefit both paths.
- **`reconcile.enabled` gates the AUTOMATIC session-end phase only.** `/reconcile` is an
  on-demand command and runs regardless of `reconcile.enabled`. It still honours
  `rule-expiry-days` and `confidence-floor` from the `reconcile` config block.

---

## Phase 0: Bootstrap Gate

Read `skills/_shared/bootstrap-gate.md` and execute the gate check. If the gate is CLOSED,
invoke `skills/bootstrap/SKILL.md` and wait for completion before proceeding. If the gate
is OPEN, continue to Phase 1.

<HARD-GATE>
Do NOT proceed past Phase 0 if GATE_CLOSED. There is no bypass. Refer to
`skills/_shared/bootstrap-gate.md` for the full HARD-GATE constraints.
</HARD-GATE>

---

## Phase 1: Config & Argument Loading

### 1.1 Read Session Config

Read and parse Session Config per `skills/_shared/config-reading.md`. Store result as `$CONFIG`.

### 1.2 Extract Reconcile Config

Extract the `reconcile` block from `$CONFIG`:

```bash
# rule-expiry-days defaults to EMPTY (not a number) so the engine falls back to
# its per-type TTL (deriveExpiresAt, default 60d). A numeric override forces flat
# N-day expiry — matching the `null` default of the reconcile: config resolver.
RULE_EXPIRY_DAYS=$(echo "$CONFIG" | jq -r '.reconcile["rule-expiry-days"] // empty')
CONFIDENCE_FLOOR=$(echo "$CONFIG" | jq -r '.reconcile["confidence-floor"] // 0.5')
RECONCILE_MODE=$(echo "$CONFIG"   | jq -r '.reconcile.mode // "warn"')
MIN_RULE_DAYS=$(echo "$CONFIG"    | jq -r '.reconcile["min-rule-days"] // 7')
MIN_INSIGHT_CHARS=$(echo "$CONFIG" | jq -r '.reconcile["min-insight-chars"] // 24')
```

When `RULE_EXPIRY_DAYS` is empty, pass `ruleExpiryDays: undefined` to `runReconcile` so the engine uses its per-type TTL. Defaults when the `reconcile` block is absent or a field is missing:
- `rule-expiry-days`: empty → per-type TTL (`deriveExpiresAt`, default 60d). Preserves FA2 behaviour; matches the `null` resolver default.
- `confidence-floor`: 0.5
- `mode`: warn (enum `off` | `warn`)
- `min-rule-days`: 7 — floor window (days) applied to a proposed rule's `expires-at` so a
  near-dead or already-elapsed natural expiry never produces a born-dead rule (issue #741.1).
- `min-insight-chars`: 24 — opt-in minimum insight length gating the eligibility
  placeholder-insight check (issue #741.2).

Note: `reconcile.enabled` is intentionally NOT checked — this on-demand command always runs.

### 1.3 Parse Arguments

Check `$ARGUMENTS` for `--dry-run`:

```bash
DRY_RUN=false
if echo "$ARGUMENTS" | grep -q -- '--dry-run'; then
  DRY_RUN=true
fi
```

---

## Phase 2: Run the Reconciliation Engine

### 2.1 Resolve Plugin Root

Resolve `$PLUGIN_ROOT` per `skills/_shared/config-reading.md` (the standard resolution chain:
`$CLAUDE_PLUGIN_ROOT` → `$CODEX_PLUGIN_ROOT` → `$CURSOR_RULES_DIR` → common install locations).

### 2.2 Invoke `runReconcile`

```javascript
import { runReconcile } from '$PLUGIN_ROOT/scripts/lib/reconcile/engine.mjs';

const { proposals, rejected, summary, error } = await runReconcile({
  repoRoot,             // absolute path from git rev-parse --show-toplevel
  ruleExpiryDays: RULE_EXPIRY_DAYS,   // empty → undefined → engine per-type TTL
  minRuleDays: MIN_RULE_DAYS,         // default 7 — floors a near-dead expires-at
  minInsightChars: MIN_INSIGHT_CHARS, // default 24 — opt-in placeholder-insight length gate
  now: new Date(),
  dryRun: DRY_RUN,     // true → engine touches no disk (no idempotency sidecar write)
});

// The engine does NOT apply a confidence floor — it proposes every eligible
// learning and carries each one's `confidence` through. `confidence-floor` is a
// DELIVERY gate: filter proposals here before the sidecar + AUQ (mirrors
// session-end Phase 3.6.8). Use `surfaced` everywhere "proposals" appears below.
const surfaced = proposals.filter((p) => typeof p.confidence === 'number' && p.confidence >= CONFIDENCE_FLOOR);
```

`runReconcile` NEVER throws — a top-level error populates `result.error` instead.

If `error` is present, surface it to the user and abort:
> "Reconcile engine error: `<error>`. Check `.orchestrator/metrics/learnings.jsonl` and retry."

### 2.3 Handle Empty / Zero-Proposal Cases

If `summary.totalLearnings === 0`:
> "No learnings found in `.orchestrator/metrics/learnings.jsonl`. Run `/evolve analyze` first to extract session patterns."
Exit cleanly.

If `summary.eligible === 0` (learnings exist but none are eligible — already proposed,
or wrong learning type — eligibility is type/`file_paths`-based, NOT confidence-based):
> "No eligible learnings for rule proposals (total: `summary.totalLearnings`, already proposed or ineligible type: all). Run more sessions to accumulate evidence."
Exit cleanly. Optionally list the rejection reasons from `rejected[]` (field `reason`) as an
informational table.

If `summary.eligible > 0` but `surfaced.length === 0` (proposals exist but ALL fall below
`confidence-floor`):
> "No proposals above the confidence floor (`CONFIDENCE_FLOOR`). Lower `reconcile.confidence-floor` or run more sessions so the underlying learnings accrue confidence."
Exit cleanly.

If `summary.proposed === 0` but `summary.eligible > 0` (emit/render failures consumed all
candidates — unusual):
> "Engine produced 0 proposals from N eligible learnings. See rejection log."
List `rejected[].reason` and exit.

---

## Phase 3: Dry-Run Branch

**Only when `DRY_RUN=true`.**

Print the proposals in a readable table. Do NOT write the sidecar, do NOT render an AUQ.

```
## Reconcile — Dry Run  (N proposals, M rejected)

| # | Slug | Confidence | Learning Key | Rule Path |
|---|------|-----------|-------------|-----------|
| 1 | <slug> | 0.72 | <learningKey> | .claude/rules/<slug>.md |
| 2 | ...   | ...  | ...          | ...                     |

Rejected (not eligible for proposal):
| Learning Key | Reason |
|-------------|--------|
| <key> | <reason> |

Re-run without --dry-run to enter the approval flow.
```

Exit after printing. Do not proceed to Phase 4.

---

## Phase 4: Write Pending Sidecar (Normal Mode Only)

Write the proposals to `.orchestrator/metrics/reconcile-pending.md` as a human-readable
record before presenting the AUQ. This sidecar is informational only — it lets the operator
see the full proposal set in an editor alongside the AUQ prompt.

```markdown
# Reconcile Pending — <ISO date>

Generated by `/reconcile` on <timestamp>. N proposals, M rejected.

## Proposals

| # | Slug | Confidence | Learning Key | Rendered Rule Path |
|---|------|-----------|-------------|-------------------|
| 1 | <slug> | 0.72 | <key> | .claude/rules/<slug>.md |
...

## Rejected

| Learning Key | Type | Reason |
|-------------|------|--------|
| <key> | <type> | <reason> |
...
```

Write via standard file write (not atomic, not lock-protected — this is a disposable sidecar,
not a critical artifact).

---

## Phase 5: AUQ Approval Flow (Normal Mode Only)

Present proposals to the operator in batches of 4. Mirror the session-end Phase 3.6.3 / 3.6.8
multiSelect pattern exactly.

For each batch (proposals sliced into groups of 4):

```
AskUserQuestion({
  questions: [{
    question: "Which rule proposals should be written to .claude/rules/?  (batch K of N)",
    header: "Reconcile — Approve Rule Proposals",
    options: [
      {
        label: "<slug>.md (confidence: 0.72)",
        description: "Learning: <learningKey> | Path: .claude/rules/<slug>.md | <first 100 chars of rendered content>"
      },
      ...up to 4 options per batch...
      {
        label: "Skip all in this batch",
        description: "Decline all proposals in this batch — they are archived to the rejected log."
      }
    ],
    multiSelect: true
  }]
})
```

Collect responses across all batches:
- Selected options (excluding "Skip all") → `approved[]`
- Unselected options + "Skip all" batches → `rejected_by_operator[]`

> **Codex CLI fallback:** AskUserQuestion is unavailable in subagents and on Codex CLI
> (AUQ-004). In those contexts, present proposals as a numbered Markdown list and ask
> the operator to reply with the numbers they wish to approve.

---

## Phase 6: Write Approved Rules

### 6.1 Invoke `writeApprovedRules`

```javascript
import { writeApprovedRules } from '$PLUGIN_ROOT/scripts/lib/reconcile/writer.mjs';

const { written, archived, errors } = await writeApprovedRules({
  approved: approved,             // proposals the operator approved
  rejected: rejected_by_operator, // proposals the operator declined
  repoRoot,
  sessionId: currentSessionId,    // informational; from STATE.md or 'manual'
});
```

`writeApprovedRules` NEVER throws — per-item failures are collected in `errors[]`.

### 6.2 Handle Errors

If `errors.length > 0`, surface each error to the operator:
> "Warning: `N` rule(s) failed to write: `<error list>`. Successfully written: `written`. Archived: `archived`."

Log each error but do NOT abort — partial success is acceptable.

### 6.3 Report

```
## Reconcile Complete

- Written:  <written> rule file(s) to .claude/rules/
- Archived: <archived> declined proposal(s) to .orchestrator/reconcile.rejected.log
- Errors:   <errors.length> (see warnings above, if any)

New rules take effect immediately — they are loaded by the wave-executor's rule-loader
on the next wave dispatch.
```

If `written === 0` and `approved.length === 0`:
> "No proposals approved. No rules written."

---

## Critical Rules

- **NEVER** call `writeApprovedRules` before the operator has confirmed via AUQ — this is the
  only write-protection gate for `.claude/rules/`.
- **NEVER** pass `dryRun: false` to `runReconcile` and then skip the AUQ — the idempotency
  sidecar is written during the engine run; writing rules without AUQ confirmation would create
  an inconsistency between the sidecar and the actual rule files.
- **ALWAYS** surface `errors[]` from `writeApprovedRules` — per-item isolation must not
  silently swallow failures.
- **ALWAYS** present proposals in batches of ≤4 via AUQ multiSelect — mirrors session-end
  3.6.3 / 3.6.8 and keeps the operator prompt readable.
- **ALWAYS** honour `confidence-floor`, `rule-expiry-days`, `min-rule-days`, and
  `min-insight-chars` from Session Config `reconcile` block — the engine reads these, but
  the skill must pass them explicitly.

## Anti-Patterns

- **DO NOT** write any file to `.claude/rules/` without AUQ operator confirmation.
- **DO NOT** check `reconcile.enabled` — that flag gates the automatic session-end phase, not
  this on-demand command.
- **DO NOT** emit or approve a rule with `alwaysApply: true` — the engine structurally prevents
  it, but the reviewer should reject any proposal that would produce an always-on rule.
- **DO NOT** skip the dry-run branch when `--dry-run` is passed — the entire AUQ + write flow
  must be bypassed.
- **DO NOT** treat `runReconcile` failures as fatal — check the `error` field and surface it,
  then exit cleanly.
