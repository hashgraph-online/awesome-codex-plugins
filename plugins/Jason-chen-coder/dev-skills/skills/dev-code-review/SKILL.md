---
name: dev-code-review
description: Review a requested Git diff for bugs, regressions, integration gaps, and material risks before commit. Use for review requests and the review phase of requests such as 帮我 commit. A request for only a commit message belongs to dev-commit-writer. Review is read-only; a broader authorized commit workflow may continue after review.
---

# Dev Code Review

Evaluate the requested change against its intended behavior and surrounding code. Prioritize actionable defects over stylistic preferences. Review and implementation are separate passes.

## Load baseline

Read [references/dev-baseline.md](references/dev-baseline.md) before execution. Resolve paths relative to this skill directory.

## Establish exact scope

Inspect the actual repository root, branch, working-tree status, and staged/unstaged diffs. Honor named paths, exclusions, commits, and `--staged` / `--cached` / `--path=<glob>` arguments.

For a general working-tree review, review staged and unstaged changes while distinguishing them. For a commit request with no explicit scope, use staged changes when present; otherwise infer the requested change from task context. Never silently include unrelated work. If commit scope cannot be determined, finish the readable review and clarify only the ambiguous staging decision before mutation.

Untracked files are absent from `git diff`; inspect them when they belong to the requested scope. For a staged review, read index versions and evaluate the staged snapshot, including caller relationships. A working-tree test run does not prove a staged snapshot with different contents passes. Use an isolated snapshot when necessary or state that verification limit.

Read changed logic and enough callers, definitions, tests, and configuration to assess behavior. Expand context where a question requires it; do not read entire large files by default. Inspect generated code, dependency resolution, or data changes when they can alter behavior. Binary or generated files may need source or artifact checks, not an unconditional skip.

## Review behavior and integration

Use the current request and relevant SDD spec/plan/fix artifacts as the contract. Existing artifacts may live in `.claude/artifacts/{designs,plans,fixes}/`. Select by actual relevance; a lone artifact is not automatically related. The latest user correction overrides stale text.

Trace changed behavior from its entry point through important transitions and effects. For a new route, component, configuration key, event, or public symbol, verify its registration, consumer, or intended external entry point. Use structural tools or repository search as appropriate, and inspect matches: a textual hit is not proof of a working call path; zero hits is not proof of a defect. Account for framework discovery, reflection, generated registration, and exported library APIs.

Prioritize:

- Incorrect outputs, error handling, state recovery, and reachable edge cases.
- Broken registrations, save/restore paths, request transformations, or cross-module contracts.
- Security boundaries, sensitive data exposure, integrity, concurrency, and resource usage relevant to the diff.
- Missing tests for consequential behavior, and tests that cannot detect the claimed defect.
- Unrelated changes that violate the requested commit scope, newly obsolete code, or misleading comments with concrete consequences.

Read [references/risk-checklist.md](references/risk-checklist.md) when the diff touches trust boundaries, persistence, concurrency, dependencies, or performance-sensitive paths. Read only relevant language sections of [references/lang-conventions.md](references/lang-conventions.md) when convention guidance is needed; project configuration and local conventions govern. Style, line count, debug-like logging, or absent callers alone do not establish severity.

## Severity and evidence

- **P0:** An immediate, critical defect such as broadly exploitable compromise, severe data loss, or an unconditional release-wide failure. Establish impact and reachability.
- **P1:** A high-impact defect in supported use that should be fixed before delivery.
- **P2:** A concrete, lower-impact defect or meaningful maintenance/test gap worth fixing.
- **P3:** Optional polish, only when useful or requested.

Base priority on consequences and likelihood, not the category of code or a grep count. Mark uncertainty and required conditions. Pre-existing defects are findings only when this change introduces, worsens, or exposes them; identify unrelated observations separately.

Each finding needs a verified location, trigger, consequence, and actionable correction. Do not invent line numbers or claim a vulnerability without a supported path. Avoid reproducing secret values in the report.

## Report and continuation

Lead with findings ordered by severity, followed by open questions, verification gaps, and a brief scope/result. When no actionable issue is found, say so and state material untested areas. Keep the report proportional to the diff; omit empty checklist sections.

Preserve the existing verdict names: `BLOCK` for critical issues, `FIX P1` for high-priority defects that should be fixed before delivery, and `READY` when review finds no blockers. Use `INCOMPLETE` when missing evidence prevents a verdict. `READY` is limited to the reviewed scope and is not a blanket test or production guarantee. Do not emit an unqualified `READY` while a material review gap remains.

A review-only request does not authorize editing, staging, stashing, or committing. If the user already requested fixes or the full commit flow, report the review result, then let the authorized implementation/delivery lane continue in the same task; do not demand a new user turn solely because review finished. After edits, review the changed result again in a separate pass.

Generate a commit message only when requested by the user or as part of an authorized commit flow and the intended commit is ready. Follow repository history and actual diff intent. Add artifact `Refs:` only when the association is supported and compatible with repository convention; omit uncertain associations. `dev-commit-writer`, when installed, may help with formatting but is not required.

## Multi-Agent Profile

Recommended agent_type: worker

When independent review is required and delegation is available and permitted, use a reviewer who did not author the implementation. Provide raw scope and requirements rather than the author's preferred conclusion. Keep the reviewer read-only; the main agent owns integration, staging, and authorized delivery. If no independent reviewer is available, disclose that limitation rather than labeling self-review independent.

Use `docs/multi-agent-policy.md` for repository coordination conventions when available. Standalone installations follow the same separation, scope, and evidence rules above.
