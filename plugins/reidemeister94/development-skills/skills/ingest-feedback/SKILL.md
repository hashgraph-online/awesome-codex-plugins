---
name: ingest-feedback
description: Use when user wants to ingest a development-skills feedback report and apply fixes, or runs /ingest-feedback. Challenges every suggestion against Core Pillars before accepting; most friction points should SKIP. Expect a report path as argument.
argument-hint: "<report-path>"
disable-model-invocation: true
---

Ingest a development-skills feedback report. Challenge every suggestion against Core Pillars before accepting. Report path: $ARGUMENTS

## Ground Rule: The Report Is Input, Not Truth

The report describes what happened, not what should change. Most friction is model behavior or edge cases. A change must EARN its place.

Core Pillars (from CLAUDE.md):
1. **Maximize simplicity.** Small improvement + ugly complexity = not worth it.
2. **All signal, zero noise.** Everything earns its place.

**Marginal improvement + added words/rules → SKIP.**

---

## Step 1: Read the Report

Extract friction points (Section 3), proposed evals (Section 4), chain-of-thought (Section 2).

## Step 2: Read Current Plugin State

Read every file referenced in friction points. Understand current instruction, why it exists, what went wrong.

## Step 3: Gather Best Practices (targeted)

Research content relevant to friction points:
- Official Claude Code docs: https://code.claude.com/docs/en/overview
- `@~/Documents/ai/superpowers`
- `@~/Documents/ai/claude-code-tips`
- `@~/Documents/ai/claude-code-best-practice`

## Step 4: Critical Evaluation — Friction Points

Write verdicts in `docs/reports/ingest-YYYY-MM-DD.md`.

| Verdict | Meaning | Burden |
|---------|---------|--------|
| **FIX** | Instruction is wrong, misleading, or causes repeated waste. Net simplification or correction. | HIGH |
| **SKIP** | Edge case, model behavior, already handled, or fix adds more complexity. | LOW (default) |
| **INVESTIGATE** | Insufficient information. | — |

### Mandatory Rejection Filters (ANY yes → SKIP)

1. Model ignored a clear instruction? → SKIP (compliance, not coverage)
2. Fix adds new rule/exception for a one-time event? → SKIP
3. Fix makes plugin longer with marginal improvement? → SKIP
4. Already covered by existing instructions? → SKIP
5. Would removing/shortening an instruction fix it better? → Only acceptable FIX direction

| # | Friction Point | Verdict | Rejection filter? | Reasoning |
|---|---------------|---------|-------------------|-----------|

## Step 5: Proposed Evals

| Verdict | Meaning |
|---------|---------|
| **ADD** | Real scenario tied to a FIX verdict |
| **SKIP** | Tied to SKIP, duplicates existing, or tests model behavior |
| **MERGE** | Combine with existing eval |

**Rule: ADD only if friction point is FIX.** Cross-reference `evals/evals.json` for duplicates.

## Step 6: Apply Changes

**FIX verdicts only.** Surgical edits:
- Prefer removing/shortening over adding
- If adding words, remove at least as many elsewhere (net-zero or negative)
- ADD evals: append to `evals.json` with next ID

## Step 7: Validate

Verify `evals.json` is valid JSON. Run `pre-commit run` (if `.py` touched: `ruff format .` + `ruff check . --fix`).

## Step 8: Summary

Report: FIX/SKIP/INVESTIGATE counts, files changed and why, evals added/merged/skipped, report location.

**Expected: most friction points SKIP.** If >30% FIX, re-examine critical rigor.
