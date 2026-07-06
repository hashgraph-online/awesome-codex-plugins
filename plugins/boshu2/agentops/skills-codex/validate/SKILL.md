---
name: validate
description: Produce PASS/WARN/FAIL verdicts for
---
# $validate — Canonical Validator Skill

> **Loop position:** move 6 (prove acceptance) of the [operating loop](../../docs/architecture/operating-loop.md) — the driving adapter for the `validate_acceptance` port: every Given/When/Then must map to a passing test before a bead closes.

> **Role:** validator. Input = artifact (plan, spec, code, PR, fitness gate). Output = `verdict.v1` (PASS / WARN / FAIL with rationale + findings).

> **Status (2026-05-08):** introduced ADDITIVE in Phase 1 (m6v5.D.1 / soc-78s2v). Existing validators (councilvibe/pre-mortem/red-team/review/eval-outcomes plus retired pr-validate and validation lanes) stayed until Phase 2 shim conversion (m6v5.D.2). Fix-C smoke (`soc-wb2aa`) gates Phase 2.

`$validate` is a driving adapter for the `validate_acceptance` port in the
[Intent-to-Loop Hexagon](../../docs/architecture/intent-to-loop-hexagon.md).
When the artifact contains a `hexagon:` block, preserve the bounded context,
context packet, guard adapters, and done state in the verdict.
When the artifact claims DONE/closed/green, apply the
[Completion-Claim Kernel](../shared/validation-contract.md#completion-claim-kernel)
before returning PASS.

**A verdict is re-plan evidence, not just a retry trigger.** Under `$rpi`, a
FAIL/WARN (and its findings) surfaces UP to the orchestrator's
[Agile Re-Plan Loop](../rpi/SKILL.md#agile-re-plan-loop-the-anti-waterfall-rule):
the *remaining* waves may be refactored, inserted, dropped, or reordered in
response — not only the failed objective re-cranked. Under `--auto` that pivot is
autonomous. Looping a failed objective forever without asking whether the plan
should change is the waterfall anti-pattern.

## Modes (≤8 per Fix-F mode-flag budget)

| Mode | Purpose | Replaces (post-Phase 2) |
|---|---|---|
| (default) | 2-judge multi-judge consensus on any artifact | `$council` default |
| `--quick` | Inline single-agent structured review | `$council --quick` |
| `--deep` | 4-judge thorough review | `$council --deep` |
| `--mixed` | Cross-vendor (Claude + Codex), N×2 judges | `$council --mixed` |
| `--debate` | Adversarial 2-round refinement | `$council --debate`, `$red-team` |
| `--mode=post-impl` | Code-readiness pipeline (complexity → bug-hunt → council) | `vibe` |
| `--mode=pre-impl [--target=X]` | Plan/spec validation; target ∈ {scenario,fitness,ratchet,scope,skill,health} | `$pre-mortem`, `$eval-outcomes`, `$goals measure`, `$flywheel`, `$scope`, `$heal-skill` (deep audit), `ao doctor` |
| `--mode=pr` | PR-shape verdict (diff review + acceptance check) | `$review` |

**Mode-budget assertion:** 8 modes. Adding a 9th requires demoting an existing one OR refusing the addition (per Fix-F § continuous CI gate).

### Folded skills (cp-ki8): `validation` + `pr-validate` retired into these modes

The retired validation and pr-validate lanes were the Phase-1 placeholders for `--mode=post-impl`
and `--mode=pr`; both are now retired (cp-ki8) and their load-bearing contract folded
here so no capability is lost:

- **`--mode=post-impl` (was the validation lane) — full close-out + no-self-grading invariant.**
  Beyond the inline `complexity → bug-hunt → council` pipeline, this mode owns the
  `validate_acceptance` port: every Given/When/Then from the intent issue must map to a
  passing test (criterion→test roll-up; activity logs do not close beads), and the
  acceptance verdict **must be produced by a blind, context-isolated sub-agent judge that
  did not author the code** (author ≠ validator — `ag-9jle.5` / `ag-lmdx.4`). Refuse to
  certify acceptance when `judge_id == author_id`; the only escape is an inline-fallback
  self-grade that is stamped as *waived, not independently validated*. Apply the
  [Completion-Claim Kernel](../shared/validation-contract.md#completion-claim-kernel)
  before accepting any DONE/closed/green claim. For epic-scope close-out this mode may
  delegate to `vibe`, `$post-mortem`, and `$curate --mode=forge` rather than inlining them.
- **`--mode=pr` (was the pr-validate lane) — submission-readiness checks.** In addition to the
  diff/acceptance verdict, run, in order: (1) **upstream alignment FIRST** (BLOCKING —
  `git rev-list --count HEAD..origin/main`; fail if many commits behind or merge would
  conflict), (2) CONTRIBUTING.md compliance (BLOCKING), (3) **isolation** — single commit
  type + thematic files + atomic scope, (4) scope-creep containment, (5) quality gate
  (tests/lint, non-blocking). On FAIL, emit remediation steps (split-by-type cherry-pick,
  rebase-on-upstream) so the verdict is actionable.

### Folded triggers (ag-s43tg wave 1): `vibe` + `bead-completion-audit` route here

- **`vibe` → `--mode=post-impl`.** Use when doing a quick readiness or sanity check
  that code is ready to commit or ship, short of a full review — the post-impl
  pipeline (complexity → bug-hunt → council) is the vibe check.
- **`bead-completion-audit` → `--mode=post-impl` close-out.** Use when
  auditing closed beads for real shipped evidence, acceptance proof, and truthful
  closeout — the Completion-Claim Kernel and the no-self-grading invariant above
  own this audit.

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
- bug-hunt sweep (skill-body convention; no `$review` skill needed)

For `--mode=pr`, fetch the PR diff (`gh pr diff <id>` or path).

### Step 3: Determine spawn backend

1. `spawn_agent` available → Codex sub-agent
2. `TeamCreate` available → Claude native team
3. `task` (read-only skill tool, OpenCode) → opencode subagent
4. None → fall back to `--quick` (inline single-agent)

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

The exact heading `## Council Verdict: PASS / WARN / FAIL` is mandatory — downstream validators and ledger readers parse it with anchored regex.

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
| scenario | Holdout scenario gate | `$eval-outcomes` |
| fitness | GOALS.md fitness gates | `$goals measure`, `ao goals measure` |
| ratchet | Brownian Ratchet checkpoint | `$flywheel`, `ao ratchet status` |
| scope | Frozen-dirs declaration | `$scope` |
| skill | SKILL.md hygiene + audit | `$heal-skill` (heal.sh hygiene + audit.sh deep audit) |
| health | Repo health probe | `ao doctor` |

Each target has its own inline check rubric until Phase 2 extraction.

## Validation discipline (2026-06-09, cards 6–10, cp-hhd7)

### Verdict form — the gate parses these lines anchored

```
VERDICT: PASS
(blank line)
COMMANDS RUN:
<actual commands + verbatim output snippets>
REASONS:
- bullet citing a COMMANDS RUN line
```

A verdict with no `COMMANDS RUN:` section is **unverified** — reject it and
dispatch a fresh validator. A verdict whose `COMMANDS RUN:` lists only commands
the **author** ran (not the judge) is a **counterfeit judge** — treat as FAIL and
re-route to a genuinely independent validator. No `##` headings or parentheticals
on `VERDICT:` or `COMMANDS RUN:` lines; the gate parses them anchored.

### Cross-family floor (POLICY → gate icb6 enforces; this skill supports)

For **assurance closes** (the control-plane verdict-gate, cp-icb6), the floor is
≥2 verdicts from ≥2 distinct model families, author family excluded, fail-closed.
**This skill supports that policy via `--mixed` mode and the verdict form above;
the policy itself lives in the gate, not here.** A same-model council is valid for
non-assurance decisions (design brainstorms, quick checks) — do not refuse those.
Tier mapping:
- **STRICT** (irreversible, security, production close): Codex + strong-Gemini (A1); or Fable + Codex (A2).
- **ROUTINE** (everyday close): Codex + non-author-Claude (A3); or Fable + non-author (A4).

The A7 ruling (2026-06-09, memory `validation-family-policy-risk-tiered`):
Gemini is currently **benched** for STRICT validation — use Codex + Fable for A1/A2
tiers. Gemini may return for STRICT when Bo graduates it from the bench. Do not
present Gemini paths as live for tier A1/A2 until then.

### Judge empirically on a differentiating fixture (card 9, cp-8720)

When two implementations of the same intent exist, do NOT award based on
authorship or surface aesthetics. Run both on a **differentiating fixture** (an
input that exposes their behavioral difference), record the outputs verbatim, and
graft the loser's unique assets onto the winner. "My worker wrote it" is not
evidence.

### Dispatch record first (card 3, cp-hhtu)

Before dispatching a validator, register intent on the bead graph (update status,
assign actor). **Two parallel validators on the same bead produce a dedup incident,
not a cross-family quorum.** Check for an existing actor before spawning.

### Judge lanes carry an explicit write-scope clamp (2026-07-02, showcase kernel R2)

Every judge brief states, verbatim: **"READ-ONLY except writing your single verdict
file at `<path>`. Do NOT commit, push, or run tracker/infra ops (git push, br/bd,
dolt)."** The clamp is role-scoped, not model-scoped — crank workers legitimately
hold broad write scopes; judges re-measure, they never mutate. Proven live: an
unclamped codex acceptance judge pushed the feature branch unprompted and attempted
`bd dolt push` twice mid-judgment. A judge that mutates while judging can corrupt
the artifact under judgment or preempt the pawl.

### Judges re-measure; they do not read (card 8)

A judge re-runs the cited commands on the actual artifacts. It does not read the
author's evidence file and agree. Attest `judge_source: <model>` inside `COMMANDS RUN`
so the gate can confirm the judge identity. A judge that ran nothing is a reader, not
a verifier — discard its verdict.

## Evidence figures are measured, never inferred (the cp-801l lesson)

A worker's evidence file may only contain numbers and outputs that were **captured** —
pasted verbatim from a command's output — never reconstructed from memory. The
canonical failure: "36 checks — 35 pass" stated with confidence was inference; the
measured reality was 36 run / 34 pass / 1 fail / 1 skip, on a different commit.

- **Validators:** treat any uncited figure (a count, a pass-rate, a timing, a commit
  hash) as **unverifiable → FAIL** until a log is produced or the claim is corrected.
- **Corrections happen by APPENDED erratum** — a dated erratum block crediting the
  source measurement — never by silently editing the original figure. A silently
  edited evidence file is indistinguishable from a fabricated one.

## Constraints (one-role-per-skill)

- **One role: validator.** Output is always a verdict. Never mutates code (delegates to `$implement` for fixes).
- **No new modes** without dropping/merging an existing one (Fix-F mode-budget cap = 8).
- **Verdict heading is regex-anchored** — do not alter the `## Council Verdict: ...` text format.

## Output Specification

**Format:** a PASS/WARN/FAIL validation verdict plus a markdown council summary to stdout; machine-readable `result.json`.
**Files:** writes `.agents/council/YYYY-MM-DD-validate-<slug>.md` and `result.json`; appends reusable findings to `.agents/findings/registry.jsonl`; may refresh `.agents/planning-rules/` and `.agents/pre-mortem-checks/`.
**Exit signal:** FAIL re-cranks on the same objective (up to 3 attempts); DONE on a fully-green acceptance roll-up.

## See Also

- `skills/rpi/SKILL.md` — orchestrator that fires `$validate --mode=pre-impl` after `$plan`
- `skills/curate/SKILL.md` — miner role (paired canonical skill)
- `schemas/verdict.v1.schema.json` — output contract
- [`pre-land-refuters`](../pre-land-refuters/SKILL.md) — the mutate-shared-trunk pawl: a self-administered DONE is a claim, so an unbiased fresh-context refuter (model-agnostic by default; multi-model ≥2 families opt-in for the highest-irreversibility doors) attacks it at the push boundary **regardless of complexity** (complexity scales the panel's depth, never exempts the gate); its CONFIRMED verdict is enforced executably by `scripts/reconcile-pr.sh`

## Reference Documents

- [references/validate.feature](references/validate.feature) — Executable spec: verdict.v1 PASS/WARN/FAIL for any artifact, --mode selects shape, 8-mode budget (soc-qk4b)

## Reference library (incl. rescued vibe references, ag-s43tg)

- [references/complexity-analysis.md](references/complexity-analysis.md)
- [references/deep-audit-protocol.md](references/deep-audit-protocol.md)
- [references/deep-checks.md](references/deep-checks.md)
- [references/examples.md](references/examples.md)
- [references/go-patterns.md](references/go-patterns.md)
- [references/go-standards.md](references/go-standards.md)
- [references/json-standards.md](references/json-standards.md)
- [references/markdown-standards.md](references/markdown-standards.md)
- [references/patterns.md](references/patterns.md)
- [references/post-verdict-actions.md](references/post-verdict-actions.md)
- [references/python-standards.md](references/python-standards.md)
- [references/quick-mode-vibe.md](references/quick-mode-vibe.md)
- [references/report-format.md](references/report-format.md)
- [references/rust-standards.md](references/rust-standards.md)
- [references/shell-standards.md](references/shell-standards.md)
- [references/test-pyramid-inventory.md](references/test-pyramid-inventory.md)
- [references/test-pyramid-weighting.md](references/test-pyramid-weighting.md)
- [references/typescript-standards.md](references/typescript-standards.md)
- [references/verification-report.md](references/verification-report.md)
- [references/vibe-coding.md](references/vibe-coding.md)
- [references/vibe-suppressions.md](references/vibe-suppressions.md)
- [references/write-time-quality.md](references/write-time-quality.md)
- [references/yaml-standards.md](references/yaml-standards.md)
- [references/validate.feature](references/validate.feature)
- [references/vibe.feature](references/vibe.feature) — rescued vibe executable spec
- [scripts/prescan.sh](scripts/prescan.sh) — rescued vibe pre-scan helper
