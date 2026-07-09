# Seven Compiled Planning Rules

> Extracted from 14,753 production sessions, 544,906 messages, 946 council verdicts (124 FAILs analyzed).
> These rules are the top cross-cutting failure patterns — each prevented by a specific planning discipline.

## How to Use

During plan creation (Step 2), evaluate each issue and wave against all 7 rules. For each rule, ask the Detection Question. If the answer is "no" or "unclear," add a mitigation to the plan before proceeding.

---

## PR-001: Mechanical Enforcement

**Rule:** Every silent-failure risk needs a gate (test, lint, or validation) that mechanically prevents it. Plans must not rely on human vigilance for correctness.

**Evidence:** ArgoCD CMP timeout mismatch caused cache poisoning with no gate to enforce alignment. K8s status subresource omission caused invisible data loss. SSH parameter parity failures in retry paths silently diverged.

**Detection Question:** Does every integration point, timeout, and configuration boundary have a mechanical validation gate?

**Checklist Item:** Each external dependency and configuration boundary has an automated conformance check (test, lint rule, or CI gate).

---

## PR-002: External Validation

**Rule:** Success criteria must be external and measurable. Workers must not declare their own work complete — external gates (tests, validators, reviewers) must confirm.

**Evidence:** Ralph Loop uses test gates, not agent declarations. Zero-context smoke tests find 3–5x more issues than self-review. Unit tests found zero bugs in production; L3+ testing (integration, E2E) found all real bugs.

**Detection Question:** Does the plan use external validation gates (test commands, CI checks) rather than self-reported completion?

**Checklist Item:** Every task has a runnable validation command — no "verify manually" acceptance criteria.

---

## PR-003: Feedback Loops

**Rule:** Any system that captures knowledge without a citation/reuse mechanism is a cemetery. Plans must include how outputs will be consumed, not just produced.

**Evidence:** Knowledge flywheel formula: velocity (σ) × reuse (ρ) must exceed decay (δ). Platform-lab flywheel decaying at σ=0.02 — producing artifacts nobody consumes. Four-surface closure requires capture → index → retrieval → application.

**Detection Question:** Does the plan close the feedback loop — who consumes the output, how is it cited, and what triggers reuse?

**Checklist Item:** Each output artifact has a named consumer and a defined consumption mechanism.

---

## PR-004: Separation Over Layering

**Rule:** Organize components around clear contracts and boundaries, not hierarchical layers. Each component should have a single, unambiguous responsibility.

**Evidence:** OpenClaw succeeds with horizontal separation (SOUL/AGENTS/IDENTITY own contracts completely). ArgoCD sync waves enforce ordering without external tooling. Prior attempts at adding a third layer with fuzzy boundaries produced unclear ownership and bugs at every seam.

**Detection Question:** Does the plan add layers or separate concerns? Are boundaries between components explicit contracts?

**Checklist Item:** Each new component has a defined contract (input/output/error) specified before implementation begins.

---

## PR-005: Process Gates First

**Rule:** When execution is failing, fix the process first. Model/tool improvements compound only after process is stable.

**Evidence:** 6,367 execution failures solved by process gates, not model upgrades. Pre-worktree sync prevents 82.6/1K git conflicts. Standards guides loaded upfront prevent 13+ violations per session.

**Detection Question:** Is the plan proposing a tool/model change when a process gate would solve the problem?

**Checklist Item:** Existing process gates are verified as in place and enforced before any new tool or model change is proposed.

---

## PR-006: Cross-Layer Consistency

**Rule:** Distributed systems fail when adjacent layers have different assumptions. Enforce consistency explicitly at every boundary.

**Evidence:** ArgoCD 3-layer timeout stack (CMP, repo-server, application) that disagrees causes silent cache poisoning. SSH parameter forwarding through retry paths — primary and retry must carry identical parameters. Plan/tracker/artifacts must stay in lockstep.

**Detection Question:** Does the plan verify configuration consistency across all layers it touches (timeouts, parameters, schemas)?

**Checklist Item:** A consistency check verifies all layers agree on shared parameters (timeouts, schemas, feature flags, env vars).

---

## PR-007: Phased Rollout

**Rule:** Big changes decompose into low-risk immediate wins + moderate-risk follow-ups. Ship the cheap wins first.

**Evidence:** ArgoCD fix order: CMP timeout (low-risk) → replicas (moderate) → Redis HA (evaluate). Swarm gates: Week 1 (sync) → Week 2 (ship gate) → Week 3 (role split) → Week 4 (closeout). Bootstrap: infrastructure → core → applications via sync waves.

**Detection Question:** Is the plan deploying everything at once, or is it phased with risk isolation between waves?

**Checklist Item:** Changes are ordered into waves by risk level, with Wave 1 being the safest and most reversible.

---

## PR-008: Pre-Decomposition Symbol Verify

**Rule:** Plans that touch code with deletion patches in the last 30 days must symbol-verify every named function, type, file, and import path against current HEAD before decomposition. Stale inventory silently invalidates wave acceptance criteria.

**Evidence:** agentops-zm8 was the 5th inventory-vs-reality drift strike in 24 hours — the plan named symbols (functions, helpers, type identifiers) that had been deleted in recent commits. Decomposition assumed they existed; Wave 1 workers couldn't find the symbol and the wave failed mid-cycle. Pattern: plan author scanned an older snapshot or stale doc, not HEAD.

**Detection Question:** Does the plan touch a region with deletions in `git log --since='30 days ago' --diff-filter=D --name-only`? If yes, has every symbol named in the plan been grep-verified against HEAD?

**Checklist Item:** For deletion-adjacent plans, run `git log --since='30 days ago' --diff-filter=D --name-only` to identify the touched region, then `grep -rn '<symbol>' <region>` for each named symbol before Wave 1. Plans where any named symbol grep returns zero hits are rejected back to research.

---

## PR-009: Mechanical Count Verification

**Rule:** Plans that claim a count ("there are 47 commands", "12 hooks fail", "this affects 3 packages") must back the claim with a runnable command in the plan body. Hand-counts in agent-generated plans drift; mechanical counts catch the drift at plan time.

**Evidence:** Agent-generated docs have shipped numeric claims that didn't match reality — function counts, job counts, hook counts off by 5–30%. Reviewers couldn't distinguish "fact" from "rounded estimate" because no command was attached. Once the count was verified mechanically, the plan claim was either right or had to be corrected.

**Detection Question:** Does every numeric claim in the plan have a `command + result` pair in the Baseline Audit table or inline in the section?

**Checklist Item:** For each numeric assertion, include the producing command:
- counts of commands → `ao --help | extract_commands | wc -l`
- counts of files → `git ls-files | grep -c <pattern>`
- counts of test functions → `grep -rn "^func Test" <pkg>/ | wc -l`
- counts of br issues → `ao beads exec list --status=open --json | jq '.issues | length'`
Plans where any numeric claim has no producing command are rejected back to research.

---

## PR-010: Small Batches + Refactor Separation

**Rule:** Decompose by *behavior*, not by file or feature-bundle. Each slice delivers **one** Given/When/Then behavior (a small batch), and a refactor is **its own slice** — never folded into a feature slice. A slice that delivers two or more behaviors, or that mixes "make it work" with "make it clean," must split.

**Evidence:** A controlled study of agent-run workflows (Finster 2026, `skills/standards/references/agentic-workflow-evidence.md`) found small batches (one behavior per cycle) beat all-at-once across every measurement, and that **refactor-after-every-green is the load-bearing quality move** — stripping the refactor step out of TDD erased its entire quality advantage, while test-first *ordering* alone contributed nothing measurable. Workflows that deferred refactoring to one final pass landed in the worst-performing cluster. Two invariants follow at plan time: bias slices small (one behavior), and schedule refactor as a distinct unit so it actually happens after each green rather than being deferred or skipped.

**Detection Question:** Does each slice map to exactly one behavior (one Given/When/Then), and is every refactor a separate slice (not bundled into a feature slice)?

**Checklist Item:** No slice delivers >1 behavior; every "refactor then feature" is split into two slices; test-first *ordering* is not treated as the quality lever (the acceptance test as contract + refactor-after-green are). Slice-sizing detail: `references/decomposition.md` → "Behavior batch size (small batches)". Caveat (Finster's scope): the small-batch/refactor-cadence evidence holds for small-to-medium, fully-specified tasks — it does not license skipping the requirements-clarity gate owned by `behavior-first-planning`.

---

## PR-011: Test Thoroughness Matched to Stakes

**Rule:** Test-level and bug-finding thoroughness planned per slice must be throttled to the slice's stakes and blast radius, not maximized. Do not plan full mutation (BF3) or the whole BF1–BF9 corpus onto small, low-risk, fully-specified slices.

**Evidence:** The same study (Finster 2026) found the highest mutation-score arms (0.93–0.98) *lost* on both cost and changeability — the extra thoroughness cost multiples and produced code that was harder to change later. On small-to-medium tasks coverage saturated near 100% regardless of workflow, so planning maximal thoroughness bought nothing measurable and made the code ossify. (Consistent with PR-002: L2+/L3 find the real bugs; padding L1 count or mutation score on low-risk slices is the over-testing tax.)

**Detection Question:** Does the plan reserve BF3 (mutation, top 3–5 modules only), BF4 (chaos), BF8, BF9 for critical/high-blast-radius/security/format-contract slices — and keep small low-risk slices at L2 + L1 regression guards?

**Checklist Item:** Each slice's `test_levels` metadata is stakes-justified: small/low-risk → L2 + L1 only (no full mutation/BF corpus); critical/security/high-blast-radius → the heavier BF levels earn their cost. See `test-pyramid.md` → "Match thoroughness to task stakes — the over-testing tax".

---

## Quick-Reference Checklist

Use this during plan review:

| # | Rule | Detection Question |
|---|------|--------------------|
| 1 | Mechanical Enforcement | Does every integration point have a mechanical gate? |
| 1b | Mechanical Enforcement | Does the plan include activation tests for any provisioned infrastructure? (Dead infrastructure = provisioned but never tested under real load) |
| 2 | External Validation | Are all validation gates external (not self-reported)? |
| 3 | Feedback Loops | Who consumes each output, and how? |
| 3b | Feedback Loops | Does the plan specify who consumes each output artifact? (Capture without consumption is a knowledge cemetery) |
| 4 | Separation Over Layering | Are component boundaries explicit contracts? |
| 5 | Process Gates First | Could a process gate solve this instead of a tool change? |
| 5b | Process Gates First | Does the plan enforce commit-per-wave and worktree-commit-before-exit? (Branch hygiene prevents merge conflict accumulation) |
| 6 | Cross-Layer Consistency | Do all layers agree on shared parameters? |
| 7 | Phased Rollout | Are changes phased by risk with validation between waves? |
| 7b | Phased Rollout | Is the 40% context budget respected? (Sessions that load >40% context for knowledge leave insufficient room for implementation work) |
| 8 | Pre-Decomposition Symbol Verify | Are all named symbols grep-verified against current HEAD before decomposition? (Required for plans touching deletion-adjacent code in the last 30 days) |
| 9 | Mechanical Count Verification | Does every numeric claim have a producing command in the plan? (Hand-counts in agent-generated plans drift; counts must be reproducible by reviewers) |
| 10 | Small Batches + Refactor Separation | Does each slice deliver exactly one behavior, and is every refactor its own slice? (Small batches + refactor-after-green are the load-bearing quality moves; test-first ordering is not — Finster 2026) |
| 11 | Test Thoroughness Matched to Stakes | Is per-slice test/BF thoroughness throttled to stakes (small low-risk → L2+L1; critical/security → heavier BF)? (Over-testing costs multiples and ossifies code — the over-testing tax) |
