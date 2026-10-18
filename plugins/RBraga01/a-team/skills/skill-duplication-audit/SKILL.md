---
name: skill-duplication-audit
version: v0.1
state: Approved
owner: Miguel
target: a-team
created: 2026-06-14
updated: 2026-06-14
score: 88
compliance-risk: Low
---

# skill-duplication-audit

## Problem

Skills across the 5 ecosystem repositories overlap in scope without documented distinctions. This creates confusion about which skill to invoke, silent redundancy in packs, and conflicting guidance when two skills are active in the same session. Without a structured way to detect and classify overlaps, the ecosystem grows noisier over time.

## Objective

Given 2 or more skills with their triggers and objectives, identify pairs that have overlapping scope and classify each pair. Produce a duplication report with a classification and a specific recommendation for each pair.

## When to Use

- When adding a new skill and checking whether an existing skill already covers the same use case
- When auditing a pack for internal redundancy
- When comparing skills across packs after an ecosystem audit
- When a user reports confusion about which of two skills to invoke

## When NOT to Use

- For a single skill — needs at least 2 skills to compare
- For agents — agents have tool scope and state, not just trigger scope; use a separate analysis
- When the boundary is already documented in an existing boundary doc — verify first
- When the skills are from completely different domains with no plausible trigger overlap

## Inputs

| Input | Required | Description |
| --- | --- | --- |
| skill-list | required | 2+ skills, each with: name, trigger (when to use), objective (one sentence), and optionally the repo |
| scope | optional | `pack` (compare within one repo) or `ecosystem` (compare across repos). Default: `ecosystem` |

## Outputs

| Output | Description |
| --- | --- |
| duplication-report | List of pairs with classification and recommendation |
| boundary-docs-needed | List of pairs requiring a documented distinction (partial-overlap pairs only) |

## Steps

1. Read all inputs. For each skill, extract: name, trigger (what situation invokes it?), objective (what does it produce?).
2. Group skills by domain. Only compare skills where triggers could plausibly describe the same situation.
3. For each pair within the same domain, compare triggers and outputs:
   - **Triggers:** do they describe the same situation or context?
   - **Outputs:** do they produce the same type of result?
4. Classify each pair using exactly one label:
   - **True duplicate:** same trigger AND same output type → recommend merge
   - **Partial overlap:** triggers overlap but differ, OR outputs overlap but differ → recommend document boundary
   - **Complementary:** same domain, different workflow stage, no trigger overlap → keep both, note relationship
   - **False positive:** similar name but different trigger and output → no action required
5. For each partial-overlap pair, draft a one-sentence boundary statement: "Use [A] when [condition A]; use [B] when [condition B]."
6. List pairs that need a boundary doc (partial-overlap only).
7. Fill the Completion Statement.

## Completion Statement Format

```text
skill-duplication-audit complete.
Skills analysed: [count]
Pairs evaluated: [count]
True duplicates: [count] — [names or NONE]
Partial overlaps: [count] — [names or NONE]
Complementary pairs: [count] — [names or NONE]
False positives: [count] — [names or NONE]
Boundary docs needed: [count] — [skill pairs or NONE]
Recommendation: [summary action]
```

## Red Flags

- "These two skills have similar names so they must be duplicates" — name similarity is not scope overlap; compare triggers and outputs, not names
- "I'll merge them to reduce complexity" — merging loses scope distinctions; only recommend a merge if triggers AND outputs are genuinely identical
- "The boundary is obvious so it doesn't need documentation" — undocumented boundaries get violated; if there is overlap, document it
- "They're in different repos so they can't conflict" — cross-repo skills are the most common source of undocumented overlap in the ecosystem
- "I'll classify as partial overlap to be safe" — over-classifying creates unnecessary boundary docs; only classify as partial overlap if trigger overlap is real and observable

## Examples

### Example 1 — True duplicate

**Input:**
- api-doc-writer: trigger "when writing documentation for a REST API", objective "produce API reference docs"
- api-reference-generator: trigger "when documenting a REST API", objective "generate API reference documentation"

**Expected output:** True duplicate. Triggers and outputs are semantically identical. Recommend merge. Keep the skill with stronger test coverage.

### Example 2 — Complementary

**Input:**
- prd-quality-gate (builder-product): trigger "when a PRD is drafted and ready for engineering review", objective "gate PRD quality before handoff"
- copy-quality-gate (builder-growth): trigger "when landing page copy is written", objective "gate copy quality before publishing"

**Expected output:** Complementary. Same quality gate pattern, different domains (product vs. growth), no trigger overlap. No action needed.

## Counter-Examples

### Counter-Example 1 — False positive mistakenly treated as duplicate

**Input:**
- design-token-audit (builder-design): trigger "when reviewing design token consistency across components"
- positioning-audit (builder-growth): trigger "when evaluating brand positioning and messaging clarity"

**What should happen:** False positive. "Audit" in the name is irrelevant — triggers are in completely different domains. No action.

**What the skill must NOT do:** Recommend a merge or boundary doc based on shared vocabulary alone.

### Counter-Example 2 — Complementary pair forced into partial-overlap

**Input:**
- eval-before-ship (builder-ai): trigger "before deploying an LLM model or prompt to production"
- prd-quality-gate (builder-product): trigger "when a PRD is drafted and ready for engineering review"

**What should happen:** Complementary — different stages of the product lifecycle, no trigger overlap.

**What the skill must NOT do:** Classify these as partial-overlap because both are "gates" in an AI product workflow.

## Test Cases

| ID | File | Description | Pass |
| --- | --- | --- | --- |
| TC-001 | test-cases/case-001-true-duplicate.md | True duplicate: identical trigger and output type | ✅ |
| TC-002 | test-cases/case-002-complementary-quality-gates.md | Complementary: prd-quality-gate vs copy-quality-gate | ✅ |
| TC-003 | test-cases/case-003-partial-overlap-ai-reviewers.md | Partial overlap: ai-reviewer vs ai-safety-reviewer | ✅ |
| TC-004 | test-cases/case-004-false-positive-audit-name.md | False positive: same word in name, different domain | ✅ |
| TC-005 | test-cases/case-005-ecosystem-experiment-ab-test.md | Ecosystem: experiment-design vs ab-test-design | ✅ |
| TC-006 | test-cases/case-006-ecosystem-ai-feature-safety.md | Ecosystem: ai-feature-validation vs ai-safety-review | ✅ |
| TC-007 | test-cases/case-007-ecosystem-messaging-safety.md | Ecosystem: ai-messaging-review vs ai-safety-review | ✅ |
| TC-008 | test-cases/case-008-no-duplicates.md | No duplicates: 3 skills in different domains | ✅ |
| TC-009 | test-cases/case-009-large-list.md | Large list: 5 skills, 1 true duplicate, 1 partial overlap | ✅ |
| TC-010 | test-cases/case-010-low-context.md | Low context: skill names only, no triggers provided | ✅ |

## Evaluation History

| Version | Date | Score | Recommendation | Report |
| --- | --- | --- | --- | --- |
| v0.1 | 2026-06-14 | 88 | Approved — promotion proposal pending | evaluations/skills/skill-duplication-audit/eval-001.md |
