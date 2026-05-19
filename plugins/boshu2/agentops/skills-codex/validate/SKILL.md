---
name: validate
description: 'Produce PASS/WARN/FAIL verdicts.'
---

# $validate — Canonical Validator Skill

> **Role:** validator. Input = artifact (plan, spec, code, PR, fitness gate). Output = `verdict.v1` (PASS / WARN / FAIL with rationale + findings).

> **Status (2026-05-08):** introduced ADDITIVE in Phase 1 (m6v5.D.1 / soc-78s2v). Existing validators (council, vibe, pre-mortem, red-team, pr-validate, validation, review, scenario) stay until Phase 2 shim conversion (m6v5.D.2). Fix-C smoke (`soc-wb2aa`) gates Phase 2.

`$validate` is a driving adapter for the `validate_acceptance` port in the
[Intent-to-Loop Hexagon](../../docs/architecture/intent-to-loop-hexagon.md).
When the artifact contains a `hexagon:` block, preserve the bounded context,
context packet, guard adapters, and done state in the verdict.
When the artifact claims DONE/closed/green, apply the
[Completion-Claim Kernel](../shared/validation-contract.md#completion-claim-kernel)
before returning PASS.

## Modes (≤8 per Fix-F mode-flag budget)

| Mode | Purpose | Replaces (post-Phase 2) |
|---|---|---|
| (default) | 2-judge multi-judge consensus on any artifact | `$council` default |
| `--quick` | Inline single-agent structured review | `$council --quick` |
| `--deep` | 4-judge thorough review | `$council --deep` |
| `--mixed` | Cross-vendor (Claude + Codex), N×2 judges | `$council --mixed` |
| `--debate` | Adversarial 2-round refinement | `$council --debate`, `$red-team` |
| `--mode=post-impl` | Code-readiness pipeline (complexity → bug-hunt → council) | `$vibe` |
| `--mode=pre-impl [--target=X]` | Plan/spec validation; target ∈ {scenario,fitness,ratchet,scope,skill,health} | `$pre-mortem`, `$scenario`, `$goals measure`, `$ratchet`, `$scope`, `$skill-auditor`, `ao doctor` |
| `--mode=pr` | PR-shape verdict (diff review + acceptance check) | `$pr-validate`, `$review` |

**Mode-budget assertion:** 8 modes. Adding a 9th requires demoting an existing one OR refusing the addition (per Fix-F § continuous CI gate).

## Quick Start

```bash
$validate path/to/plan.md                  # default 2-judge consensus
$validate --quick path/to/plan.md          # inline single-agent
$validate --deep path/to/spec.md           # 4-judge thorough
$validate --mode=pre-impl path/to/plan.md  # pre-mortem mode
$validate --mode=post-impl recent          # vibe mode (post-implement)
$validate --mode=pr 123                    # PR review by PR number
$validate --mode=pre-impl --target=fitness # fitness gate against GOALS.md
```

Default uses runtime-native subagent spawning. Falls back to `--quick` (inline) when no multi-agent capability detected.

## Execution

### Step 1: Resolve mode + target

Parse `--mode` and `--target`. Default mode is multi-judge. Validate combinations:

| Mode | Allowed `--target` |
|---|---|
| default, --quick, --deep, --mixed, --debate | n/a |
| --mode=post-impl | n/a (pipeline scope is recent code changes) |
| --mode=pre-impl | scenario, fitness, ratchet, scope, skill, health (default: pre-mortem on plan) |
| --mode=pr | n/a (PR ID/path is positional) |

Reject invalid combinations (e.g., `--mode=pr --target=fitness`).

### Step 2: Load artifact + context

```bash
# resolve artifact:
ARTIFACT="${1:-recent}"  # path, PR ID, or "recent"

# load FAIL patterns:
# (folded into skill body; not a separate hook)
```

For `--mode=pre-impl`, also load:
- `.agents/planning-rules/*.md` (compiled planning rules)
- `.agents/findings/registry.jsonl` (active findings)
- `.agents/pre-mortem-checks/*.md` (compiled prevention)

For `--mode=post-impl`, run pre-checks:
- complexity audit (radon for python, gocyclo for go)
- bug-hunt sweep (skill-body convention; no `$bug-hunt` skill needed)

For `--mode=pr`, fetch the PR diff (`gh pr diff <id>` or path).

### Step 3: Determine spawn backend

1. `spawn_agent` available → Codex sub-agent
2. `--mixed` requested and Codex CLI available → spawn native judges and pair
   with Codex CLI judge runs
3. No multi-agent backend available → fall back to `--quick` (inline
   single-agent)

Log selected backend in the verdict frontmatter.

### Step 4: Run judges

| Mode | Judges | Perspectives |
|---|---|---|
| default | 2 | independent (no labeled perspectives) |
| --deep | 4 | missing-requirements, feasibility, scope, spec-completeness |
| --mixed | 2N (default N=3) | same N perspectives across Claude + Codex |
| --debate | 2+ rounds | adversarial; 2 rounds with critique-rebuttal |
| --quick | 0 (inline self) | structured review |
| --mode=post-impl | 2 + pipeline | complexity → bug-hunt → 2-judge council |
| --mode=pre-impl | 2-4 | per target preset |
| --mode=pr | 2 | diff-review + acceptance-check |

Each judge gets:
- artifact path
- relevant context (planning rules, findings)
- council FAIL pattern check prompt (top 8)
- temporal interrogation prompt (--deep + --target=plan)

### Step 5: Mandatory checks (auto-trigger)

For `--mode=pre-impl --target=plan`:
- temporal interrogation (auto for plans with 5+ files or 3+ deps)
- error & rescue map
- council FAIL pattern check (top 8)
- test pyramid coverage check
- input validation check (enum-like fields)

For `--mode=post-impl`:
- L0/L1/L2 coverage check on changed files

For `--mode=pre-impl --target=fitness`:
- read GOALS.md
- evaluate each gate against current state
- report PASS/WARN/FAIL per gate + aggregate

### Step 6: Consolidate to verdict

Each judge returns a per-judge result. Consolidate:
- PASS only if all judges PASS (or majority for --deep)
- WARN if any judge raises a warning the others don't dispute
- FAIL if any judge raises a blocker the others don't override

### Step 7: Write verdict

Output path: `.agents/council/YYYY-MM-DD-validate-<topic-slug>.md`

```markdown
---
id: validate-YYYY-MM-DD-<slug>
type: verdict
date: YYYY-MM-DD
mode: <mode>
target: <target or n/a>
artifact: <path>
backend: <codex-subagents | claude-teams | opencode | inline>
---

# Validate Verdict — <topic>

## Council Verdict: PASS / WARN / FAIL

| Failure mode | Risk | Severity | Addressed? |
|---|---|---|---|
| ... | ... | ... | ... |

## Pseudocode Fixes (when WARN/FAIL)
(copy-pastable into affected issues per pre-mortem 4.6 contract)

## FAIL Pattern Check
(top 8 patterns — status per pattern)

## Verdict
PASS — proceed
WARN — review concerns, accept risk, or apply fixes
FAIL — block; revise artifact and rerun
```

The exact heading `## Council Verdict: PASS / WARN / FAIL` is mandatory — `ao rpi phased` (when present) parses with anchored regex.

### Step 8: Persist findings (when applicable)

For `--mode=pre-impl` reusable findings: append to `.agents/findings/registry.jsonl` (atomic temp+rename).

### Step 9: Report

1. Verdict (PASS/WARN/FAIL).
2. Key concerns (when not PASS).
3. Output path.
4. Recommended next action.

## --target taxonomy (pre-impl)

| `--target` | What gets graded | Replaces |
|---|---|---|
| (default) | Plan/spec for an upcoming `$implement` | `$pre-mortem` |
| scenario | Holdout scenario gate | `$scenario` |
| fitness | GOALS.md fitness gates | `$goals measure`, `ao goals measure` |
| ratchet | Brownian Ratchet checkpoint | `$ratchet`, `ao ratchet status` |
| scope | Frozen-dirs declaration | `$scope` |
| skill | SKILL.md hygiene + audit | `$skill-auditor`, `$heal-skill` (audit half) |
| health | Repo health probe | `ao doctor` |

Each target has its own inline check rubric until Phase 2 extraction.

## Constraints (one-role-per-skill)

- **One role: validator.** Output is always a verdict. Never mutates code (delegates to `$implement` for fixes).
- **No new modes** without dropping/merging an existing one (Fix-F mode-budget cap = 8).
- **Verdict heading is regex-anchored** — do not alter the `## Council Verdict: ...` text format.

## See Also

- `skills/rpi/SKILL.md` — orchestrator that fires `$validate --mode=pre-impl` after `$plan`
- `skills/curate/SKILL.md` — miner role (paired canonical skill)
- `schemas/verdict.v1.schema.json` — output contract
