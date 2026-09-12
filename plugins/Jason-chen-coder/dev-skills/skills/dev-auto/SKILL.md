---
name: dev-auto
description: 'Explicit-only navigator for the dev-skills workflow. Use when the user names dev-auto or explicitly asks for workflow guidance across requirements, implementation, verification, and delivery. Recommends the next step from current evidence; does not execute the workflow. Generic implementation requests or an isolated "what next" do not trigger it. Supports [slug], --status, --next, and --recover.'
---

# Dev Auto

Recommend the shortest useful path through dev-skills from the user's current state. This is a read-only navigator: no code, artifact writes, subagents, or automatic skill invocation.

Read [references/dev-baseline.md](references/dev-baseline.md). Resolve project paths against the user's project, not the installed skill directory.

## Scope and modes

Use only for explicit workflow guidance. A request to fix, implement, plan, review, or commit directly belongs to that task; do not turn it into navigation. When the user has already authorized execution, this optional navigator must not replace that execution request with a suggestion-only response.

| Argument | Output |
|---|---|
| `[slug]` or default | Current evidence, useful remaining steps, and the next action |
| `--status [slug]` | Current state and uncertainty only |
| `--next [slug]` | One next command and one sentence explaining why |
| `--recover [slug]` | Failure cause or missing evidence, recovery action, and what will establish recovery |

## Resolve the work item

Use the explicit slug, current conversation, and related artifact names. `designs/<slug>.md` and `plans/<slug>.md` describe one feature; `fixes/<slug>.md` is a separate bug namespace. Count matched feature records once. A matching slug across namespaces is not an error: use the request or source links to distinguish them.

Read `.design-context.md` and `.claude/artifacts/{designs,plans,fixes}/` only as needed. Start with filenames, status, and source metadata; read relevant acceptance criteria, open questions, or review evidence when metadata cannot justify the recommendation. Do not infer completion from file existence or timestamps alone.

Infer an unambiguous current item without a confirmation turn. If several unrelated items remain plausible and the choice changes the answer, ask which item. For a new request, a descriptive proposed slug needs no approval because this skill writes no files.

## Interpret evidence

| Evidence | Meaning |
|---|---|
| No artifact | No recorded artifact; work may still exist in code or the conversation |
| Spec `DRAFT` | Intent recorded; check unresolved decisions before recommending implementation |
| Spec `ALIGNED` | Intent aligned; use scope and risk to decide whether a separate plan adds value |
| Spec `IMPLEMENTED` | Implementation recorded; verification and review still require evidence |
| Spec `STUCK` | Named blockers remain; resolve the affected scope before implementation |
| Plan `APPROVED` | Reviewed plan; not evidence that code or tests are complete |
| Plan `DRAFT` / `REVISE` / `REJECT` / `BELOW_CONSENSUS_THRESHOLD` | Inspect the unresolved issue; recommend planning recovery where it matters |
| Fix `FIXED` | Recorded fix; current verification may still be required |
| Fix `DIAGNOSED` | Cause established; implement only if a fix is requested |
| Fix `PARTIALLY_VERIFIED` | Inspect the missing proof; narrow claims or complete the relevant check |
| Fix `BLOCKED` | Resolve the named missing decision or evidence for the affected scope |
| Fix `BELOW_CONFIDENCE_THRESHOLD` | More diagnostic evidence needed |
| Fix `NEEDS_DESIGN_CHANGE` | Plan the required design change, then return to the bug workflow |
| Missing or unknown status | State uncertainty; use available contents and conversation, without inventing a phase |

User-provided recent evidence can establish progress, but qualify what has not been inspected. Do not claim to have verified code from metadata.

## Choose the next step

| Actual need | Recommendation |
|---|---|
| Establish reusable visual direction, with important gaps | `dev-design-context`; an absent file alone is not a blocker |
| Clarify feature behavior, scope, or acceptance | `dev-grill-docs` (`dev-spec` remains the spec-only compatibility alias) |
| Plan known scope with meaningful dependencies or tradeoffs | `dev-plan`; use `--deliberate` for material migration, compatibility, security, or recovery risk |
| Implement a scoped feature or refactor | `dev-tdd` |
| Diagnose or fix broken behavior | `dev-fix`; it owns the bug regression loop |
| Substantiate completion claims | `dev-verify` |
| Review pending changes before delivery | `dev-code-review` |
| Only compose a commit message | `dev-commit-writer` |
| Finish verified work through requested merge / PR / keep / discard | `dev-finish` |

These are conditional steps, not a mandatory chain. A precise small change can skip intake and planning. Urgency does not determine risk: recommend a focused bug or implementation path and retain the checks warranted by the actual change. A bug does not need a second TDD workflow after `dev-fix`.

If workspace choice affects the next action, inspect Git root, branch, and status. Preserve the user's selected checkout and dirty changes. Suggest isolation only when it resolves a concrete conflict; do not add a blanket worktree approval checkpoint.

## Recovery

Read the reported failure and relevant evidence before choosing recovery. Ask for missing output only when it is necessary and unavailable locally.

- Requirement blocker: identify the unresolved decision and resume intake when its answer is available.
- Plan feedback: revise affected steps or assumptions. Exhausted review rounds do not prove an architecture change is necessary.
- Failing regression proof: improve the reproduction or assertion before changing more code.
- Repeated fix failure: collect discriminating evidence and revise the hypothesis; consider design work only with supporting evidence.
- Verification or review failure: fix the concrete blocker and rerun affected checks. A confirmed transient environment failure can justify the same command after the environment recovers.
- Missing evidence: add the check or narrow the claim. Do not call it verified or recommend bypassing a blocking finding.
- Destructive finish action: preserve the delivery skill's explicit authorization boundary.

Keep the response proportional to the chosen mode. Link relevant artifacts and give precise skill arguments when those skills are installed; otherwise describe the next task without pretending a missing command exists. See [examples.md](examples.md) for edge cases.

## SDD Contract

Use existing spec, plan, and fix records as evidence for the recommendation. Preserve their source links, scope, acceptance criteria, and unresolved blockers. Navigation does not change their status or grant implementation or delivery authorization.

## Multi-Agent Note

Main-agent-first. This skill does not delegate. A recommended downstream task may delegate under its own rules. In the source repository, `docs/multi-agent-policy.md` provides optional team context; it is not required for standalone installation.
