---
name: phone-a-friend
description: "Get an independent second opinion on a plan or code change from the other CLI, Claude Code or Codex."
argument-hint: "[plan path | review scope]"
user-invocable: true
disable-model-invocation: true
effort: xhigh
---

# Phone a friend

Get a second opinion from the other model family before sharing the first reviewer's conclusions.
Use one rebuttal round to resolve findings with evidence. Escalate unresolved material disagreements; never run a third round.

## Scope and partner

Plan mode reviews the given plan path, or the active task plan.
Review mode reviews the requested scope, or current branch changes.
Ask when the mode is ambiguous.

If `PHONE_A_FRIEND=1` is set, refuse because this session is already the partner.

Detect the host and call the other CLI without interactive permission prompts:

- From Claude Code: `PHONE_A_FRIEND=1 codex exec -c model_reasoning_effort="xhigh" --sandbox read-only --cd <repo> --json --output-last-message <file> "<packet>"`. Resume with the same environment, reasoning, sandbox, and repository flags before `resume <session-id> "<rebuttal>"`.
- From Codex: `PHONE_A_FRIEND=1 claude -p --permission-mode plan --effort xhigh --output-format json "<packet>"`. Resume with the same environment, permission mode, effort, and `--resume <session-id>` flags.

Use the configured high-capability model and highest supported reasoning effort.
The partner must run unattended and read-only. Never use Claude's bypass permission mode.
If the partner CLI is missing or fails, report it and stop. A same-family review is not a second opinion.

## Neutral packet

Send the user's requirements verbatim, the plan or diff, referenced paths, and applicable project rules.
Do not include the host's conclusions or suspected defects.
Keep packets, verdicts, and event logs in a temporary directory outside the reviewed repository.

Tell the partner:

- Report material findings only. Zero findings is valid.
- Each finding needs a location, falsifiable claim, evidence, impact, falsifier, likelihood, and confidence.
- Missing context must be named, not guessed.
- Stay read-only. Do not commit, merge, push, write files, modify databases, or call mutating production endpoints.
- In plan mode, give a rewrite mandate for a contested section instead of an accept or reject label.

## Review mode

Also dispatch the clean-context `development-skills:staff-reviewer`.
Reuse its verdict when the same session already reviewed the same diff.
The reviewers must not see each other's conclusions.
Merge findings by location and claim as `cross-validated`, `external-only`, or `host-only`.

## Rebuttal

Answer each finding once as the author: accept, counter with new evidence, or mark uncertain.
Resume the partner session for a final `confirmed`, `withdrawn`, or `uncertain` verdict.
A changed verdict without new evidence remains unsupported.

## Close and record

Derive severity from the [review categories](../../shared/review-categories.md), impact, and reversibility.
Do not accept a model's severity label without evidence.

Escalate to the user when a material point remains disputed, a choice is costly to reverse, or the disagreement concerns the required outcome.
Include both positions, their evidence, and each option's cost.

Report findings, source tags, resolutions, dissent, and escalated decisions in chat.
Record the same result in the active chronicle.
Without one, write a dedicated report under the project's existing documentation convention only when the user authorized repository writes.
