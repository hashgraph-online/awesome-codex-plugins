---
name: dev-fix
description: Investigate bugs, regressions, failing tests, or broken behavior by tracing evidence to the root cause, then implement and verify a scoped fix when requested. For explanation-only requests, diagnose without editing. Does not handle new feature design or commit-message-only requests.
---

# Dev Fix

Trace the failure to the state or value that first violates the intended contract. Fix the supported cause, and verify the original symptom rather than treating a plausible patch as proof.

## Load baseline

Read [references/dev-baseline.md](references/dev-baseline.md) before execution. Resolve paths relative to this skill directory.

## Scope and triage

- Distinguish diagnosis-only requests from requests to fix. "Why does this fail?" or "先别动代码" authorizes investigation, not file edits.
- Establish the symptom, expected behavior, trigger, and relevant environment from the request, logs, code, and recent changes. Investigate available evidence before asking for missing facts; continue independent work while a necessary clarification is pending.
- `--quick` requests a concise investigation; `--deep` requests deeper diagnosis and an RCA. Adapt depth to evidence and consequence without fixed hypothesis counts, fabricated probabilities, or mode-confirmation exchanges.
- Before any write, identify the actual repository root, branch, working tree, and index. Preserve existing edits and partial staging. Use an isolated checkout when useful and authorized by task scope; do not force a worktree question or treat unrelated dirty files as a reason to stop.

## Reproduce and trace

Capture the smallest faithful reproduction available: preferably an automated failing regression test, otherwise a command, request, trace, or repeatable UI/device action. Failure to reproduce locally is a limitation to investigate, not a prohibition on reading code or collecting logs.

For intermittent failures, record observed frequency and control the relevant event ordering. Prefer deterministic barriers, fake clocks, or condition-based waits over arbitrary sleeps. Repeat only enough to characterize uncertainty; three failures alone do not prove reliability.

Trace the actual data/control path from trigger to failure, including callers, transformations, serialization, configuration, generated clients, and external boundaries when relevant. Follow bad state backward to where it first violates the contract. A guard at the crash site is insufficient when the bad value originates upstream.

Use competing hypotheses only where there is real uncertainty. For each useful hypothesis, identify a predicted observation, collect discriminating evidence, and update its status. Existing logs and debugging tools may suffice; add temporary instrumentation only when it resolves a specific gap, without exposing secrets or changing timing unnecessarily.

When repeated attempts fail, reassess assumptions and choose a different evidence source or independent diagnostic pass. Do not infer an architectural defect from an arbitrary attempt count. Pause dependent edits only when the remaining decision exceeds task scope, changes a user-facing contract, or requires unavailable access; state the concrete blocker.

## Fix and regression evidence

When a fix is requested and the causal explanation is supported:

1. Prefer a regression test that fails for the original symptom before editing production code. Existing failing tests may already provide this evidence.
2. Change the cause and directly required callers or restore/save paths together. Avoid speculative fallbacks and unrelated cleanup. Add boundary validation only when necessary to establish the intended invariant.
3. Rerun the original reproduction, then checks covering affected neighboring behavior. Scale wider testing to blast radius and project requirements.
4. Remove temporary instrumentation introduced for this investigation and rerun affected checks if removal changes executable code. Preserve intentional project logging.

If an automated regression is infeasible, use the strongest feasible proof and say exactly what remains unverified. A code-level test is not evidence of a real device, production service, or authenticated browser succeeding.

An observed red result before the fix followed by green is normally sufficient. Use isolated mutation/reversal testing only if test sensitivity remains uncertain: retain the test, reverse only this fix in a temporary copy, observe the expected failure, then verify the final implementation. Never use a blanket `git stash`, `git reset`, or checkout restoration on shared user changes to manufacture proof.

## SDD Contract and report

The failure contract is: symptom and expectation, reproduction, causal trace, fix, regression evidence, and remaining limits. Use it to align with relevant existing SDD spec/plan artifacts; the latest user correction governs.

For a short fix, report that contract concisely in the answer. Maintain `.claude/artifacts/fixes/<bug-slug>.md` when requested, required by the project, or useful for a substantial investigation's durable handoff. Record status accurately, such as `FIXED`, `DIAGNOSED`, `PARTIALLY_VERIFIED`, or `BLOCKED`; include only observed commands/results, and never invent an introduction commit or RCA history.

Search for analogous defects when the root cause plausibly recurs; report out-of-scope findings separately. Finish authorized investigation/fix work without requiring the user to manually invoke another skill. Use `dev-plan` or equivalent reasoning when design work is needed within scope; use `dev-verify` or equivalent checks before a completion claim. Bug regression work stays here and does not require a second TDD workflow.

For examples of diagnosis-only work, deterministic reproduction, and evidence limits, read [examples.md](examples.md) when useful.

## Multi-Agent Profile

Recommended agent_type: worker

When delegation is permitted, assign a bounded failure path or independent hypothesis with explicit read/write ownership. Workers report raw observations, the causal trace, changed files, and verification limits. A separate reviewer/verifier evaluates the resulting fix rather than rubber-stamping the author's diagnosis.

When this repository is available, consult `docs/multi-agent-policy.md` for additional coordination conventions. Standalone installations use the ownership and evidence rules above.
