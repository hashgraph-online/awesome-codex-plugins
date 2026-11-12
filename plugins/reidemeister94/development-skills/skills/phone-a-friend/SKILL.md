---
name: phone-a-friend
description: "Use when the user wants a second opinion on a plan or code change from the other CLI, Claude Code or Codex."
argument-hint: "[plan path | review scope]"
user-invocable: true
disable-model-invocation: true
effort: high
---

# Phone a friend

Get a second opinion from the other model family before sharing the first reviewer's conclusions.
Use one rebuttal round to resolve findings with evidence. Escalate material disagreements that remain; never run a third round.

## Scope and partner

Plan mode reviews the given plan path, else the active task plan. Review mode reviews the requested scope, else the current branch changes. Ambiguous → ask.

If `PHONE_A_FRIEND=1` is set, refuse: this session already is the partner.

Detect the host and call the other family, without permission prompts (the partner runs unattended):

- From Claude Code: `PHONE_A_FRIEND=1 codex exec -c model_reasoning_effort="xhigh" --sandbox read-only --cd <repo> --json --output-last-message <file> "<packet>"`, then the rebuttal with the same env guard and flags before the subcommand: `PHONE_A_FRIEND=1 codex exec -c model_reasoning_effort="xhigh" --sandbox read-only --cd <repo> resume <session-id> "<rebuttal>"` (session id from the `thread.started` JSON event; `resume` itself accepts no sandbox flag). `exec` never prompts; the read-only sandbox blocks writes instead of asking. Codex uses the model configured in `~/.codex/config.toml`; add `-m <model>` only when the user names one.
- From Codex: `PHONE_A_FRIEND=1 claude -p --model opus --effort xhigh --dangerously-skip-permissions --output-format json "<packet>"` (the `opus` alias selects the latest Opus; the result JSON carries the `session_id`; plain text output does not), then the same flags with `--resume <session-id>` for the rebuttal.

The partner keeps its own MCP servers: the same read access to code, docs, and data as the host. If the partner CLI is missing or errors, report it and stop — a same-family review is not a second opinion.

## Neutral packet

Send: the user's requirements verbatim; the artifact (plan text or diff); paths of referenced files and applicable conventions. Send the artifact and requirements without the host's conclusions, so the reviewer can make an independent assessment. Keep every working file (packet, verdicts, event logs) outside the reviewed repository, in a temp directory: a reviewer that finds another reviewer's verdict on disk is no longer independent.

State these rules to the partner:

- Material findings only; zero findings is a valid outcome; most important first.
- Every finding: location · falsifiable claim · evidence · impact · falsifier ("what would change my mind") · likelihood and confidence as two separate fields. No location or no evidence → not a finding. Reasoning is not evidence.
- Strictly read-only: no commit, merge, or push; no file writes; no writes to any database; no calls to endpoints that write or change state on any production service. Reads are fine everywhere — code, docs, services, logs, and databases alike.
- Missing context: say what is missing; do not guess.
- Plan mode only: a contested section gets a rewrite mandate (redo this, because…), not accept/reject.

## Review mode: two independent reviewers

Also dispatch the clean-context `development-skills:staff-reviewer` (reuse its verdict if this session already produced one for the same diff). The reviews must not see each other. Merge by location and claim: `cross-validated` / `external-only` / `host-only`.

## One rebuttal round

Answer each finding once, as the author: accept (update the plan or fix list) · counter with new evidence · uncertain. The partner closes each point on session resume: confirmed / withdrawn / uncertain. A changed verdict without new evidence remains unsupported; record that evidence gap.

## Close and escalate

Severity follows the [review categories](../../shared/review-categories.md), derived from impact and reversibility — never taken from a model's own label. A "critical" without location and evidence is a red flag, not a verdict. Accepted findings follow the normal loop's authority; withdrawn ones leave the report but stay in the record with the dissent verbatim.

Escalate to the user through the development loop's platform input behavior every question the protocol could not settle — no more, no fewer — each carrying both positions, the evidence each side holds, and the cost of each choice:

- still disputed or uncertain at material severity after the rebuttal;
- costly to reverse (migration, published contract, auth, data deletion) — even when the models agree;
- the disagreement is about what the work should achieve, not how.

## Record

Report the full outcome in chat: findings table (location, claim, source tag, resolution), kept dissent, escalated decisions. Record the same in the active task chronicle. With no active chronicle, still report everything in chat and write it to a dedicated file in the project's `docs/` (its chronicle convention if present, else `docs/phone-a-friend__YYYY-MM-DD__<slug>.md`).
