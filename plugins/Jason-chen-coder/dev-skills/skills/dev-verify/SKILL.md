---
name: dev-verify
description: Verify implemented changes before claiming they are complete, fixed, passing, or ready for delivery. Match checks to requested behavior and risk, inspect current evidence, and report limits. Use for completion checks, not general factual answers or a replacement for code review.
---

# Dev Verify

Make completion claims no broader than the evidence. This workflow verifies behavior and artifacts; it does not authorize commits, publishing, merge, or cleanup.

## Load baseline

Read [references/dev-baseline.md](references/dev-baseline.md) before execution. Resolve paths relative to this skill directory.

## Choose evidence

Identify what the user expects to be true and the smallest sufficient proof. Use project commands and conventions; inspect their actual scope before relying on their names.

| Claim | Relevant proof |
|---|---|
| Behavior implemented | Tests or direct checks of observable acceptance criteria |
| Bug fixed | Original reproduction or faithful regression passes |
| Regression detects the defect | Observed failure on original behavior, or isolated mutation proof |
| Refactor preserves behavior | Relevant characterization tests pass before and after |
| Build/lint succeeds | Corresponding command completes successfully |
| UI works | Relevant rendered states and interactions, with viewport/device scope stated |
| Skill/document updated | Structure/link checks plus review of changed instructions/content |

Use focused checks for local changes. Broaden for shared contracts, state transitions, persistence, integrations, security, or project-required gates. Do not add tests that merely mirror reversible low-impact edits. A parser or keyword check validates structure, not instruction quality or system behavior.

## Run and inspect

- Use fresh evidence from the final relevant file state. Evidence already produced and inspected during the task remains usable if the tested inputs, dependencies, and environment have not materially changed; do not rerun solely because a new message or handoff occurred.
- Record exact commands, exit status, and meaningful output. Inspect failures, skipped tests, and warnings that affect the claim. A command being started is not evidence of completion.
- Keep verification read-only with respect to source and the Git index. Run tools that generate artifacts in an isolated output location where needed. Do not fix code in an independent verification lane unless explicitly reassigned.
- A worker's summary is not enough: inspect its output and relevant artifacts, or independently reproduce the critical check. Scale repeated verification to remaining uncertainty.
- When a check fails, distinguish a regression from a pre-existing/environmental failure using evidence. Continue authorized corrective work in the appropriate lane, then rerun affected checks. Do not quietly waive a required failure.

Unavailable hardware, credentials, production access, or test tooling limits the claim. Complete all feasible checks and report missing proof without presenting a local substitute as equivalent.

## SDD alignment and completion

Use the current request and relevant existing SDD artifacts as acceptance criteria. If present, `.claude/artifacts/{designs,plans,fixes}/` may contain the source contract; select by actual task/file relevance, not the number of artifacts. Later user corrections override stale artifacts.

For substantial work, map requirements to evidence and list missing coverage. Small changes need only a short verification statement. Report what changed, which checks passed or failed, and material residual limits; do not force a fixed checklist into every response.

Verification does not substitute for independent code review. A `READY` review is not proof that tests ran, and passing tests do not prove every review concern resolved. Use `dev-code-review` when available and required, or perform the equivalent independent review.

## Multi-Agent Profile

Recommended agent_type: worker

When delegation is permitted, give the verifier the current task contract, change scope, and raw artifacts. The verifier evaluates evidence independently and reports claims checked, commands/results, and limitations without changing source or staging files. Follow `docs/multi-agent-policy.md` if this repository is available; these rules also apply to standalone installations.
