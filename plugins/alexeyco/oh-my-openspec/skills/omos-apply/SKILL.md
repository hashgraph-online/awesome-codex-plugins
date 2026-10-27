---
name: omos-apply
description: "Apply an OpenSpec change via $oh-my-openspec:omos-apply — implement task groups in parallel waves, verify scenarios, review the diff. Never commits. Invoke via $oh-my-openspec:omos-apply."
---

> Codex host adaptation (generated from skills/omos-apply/SKILL.md — source of truth stays there):
> - Dispatch roles with `spawn_agent` / `send_input` / `wait_agent` / `close_agent`. Subagents are asynchronous (default up to 6 concurrent threads), so a wave is one batch of `spawn_agent` calls followed by `wait_agent` collection — never poll.
> - `openspec_validate` is provided by this plugin's bundled MCP server as `mcp__openspec__openspec_validate` — call it with `cwd` set to your session's project directory (the `change` filter optional); the VALID/INVALID/UNAVAILABLE/ERROR one-look report format is identical to OpenCode.
> - This skill is invoked as a `$oh-my-openspec:omos-apply` mention (or picked from /skills). There is no argument substitution: arguments arrive as plain text in the user's message after the mention — read them from there; when absent, follow this skill's elicitation steps.
> - Roles run from `~/.codex/agents/omos-*.toml`. If `spawn_agent` reports an unknown agent, stop and tell the user to run `$oh-my-openspec:omos-setup` once.

# omos-apply

Implement `openspec/changes/<change-id>/` through dependency-ordered parallel
subagent waves with verification and review. The OpenSpec artifacts are the
contract. You never run git write commands — the user reviews and commits.

## Flow

### 1. Select the change

- `Change: <id>` given → use it.
- Otherwise run `openspec list --json` (or read `openspec/changes/`).
  Exactly one active change → confirm it. Several → ask, one per run.
  None → tell the user to run `$oh-my-openspec:omos-plan` and stop.

### 2. Mechanical gate

Run `openspec_validate` with the change id.

- `UNAVAILABLE` → offer to install the CLI now (`npm install -g
@fission-ai/openspec`, or `brew install openspec` on macOS; explicit yes
  required). **Declined** → stop — unlike plan, apply cannot verify without
  the gate.
- Not VALID → stop, report the numbered violations, suggest a
  `$oh-my-openspec:omos-plan` fix round. Do not proceed.

### 3. Wave plan

Dispatch `omos-planner` with `MODE: waves` over `tasks.md` + `design.md`.
It returns ordered waves of task groups (groups run in parallel within a
wave; overlapping files serialize groups into later waves; conservative
choices on uncertainty). Each wave-table row lists its groups' exact file
paths, and the planner's `MODE: waves` rules are the source of truth for
how waves are formed. Record the wave table in the session before
dispatching.

### 4. Execute waves

For each wave, in order:

- Dispatch one `omos-implementer` per group in the wave, all in a single
  parallel batch. On Codex the batch is one set of `spawn_agent` calls that return
  immediately — collect each report with `wait_agent`, relay follow-ups
  with `send_input`, and release threads with `close_agent`; never poll.
- Each implementer prompt carries verbatim: the group's tasks, the spec
  requirement/scenario sections they implement, design.md decisions touching
  the group, and the full wave table, including each group's assigned files.
- Implementers tick their own `- [ ]` → `- [x]` in `tasks.md`.
- A user request arriving mid-wave is first checked against the wave table —
  the single source of execution order (Guardrails) — and the remaining
  `tasks.md` items; a covering task is cited, never duplicated by a new
  dispatch.

### 5. Blockage and conflict

An implementer `BLOCKED:` answer stops the run's dispatch loop for the
affected wave:

- `file conflict` → re-dispatch the blocked group alone in a follow-up
  mini-wave after its conflicting sibling completes.
- Guardrail or plan defect → halt and ask the user (irreversible action,
  security change, external side effect, broken plan are always user
  decisions). Never lower the bar to get green. Exception: a
  prompt-truncation `BLOCKED:` is the orchestrator's defect, not the
  plan's — re-dispatch the group with a numbered edit list of ≤150 lines
  referencing `file:line`, not inlined spec or transcript text.

### 6. Verify

Before §7 Review, the orchestrator's ordering gate: every manual/eyeball
acceptance group in `tasks.md` is executed with the user and its
confirmation recorded — no change enters Review with any such group
unticked. `DEFERRED:` is inadmissible for tasks in those groups — they end
ticked or the run halts. This gate is ordering only; the verifier's
`tasks.md` consistency check stays a separate mechanical audit.

After the final wave: dispatch one `omos-verifier` per capability spec
file in parallel. Each runs the mechanical gate, executes every scenario's
WHEN/THEN, and checks `tasks.md` consistency.

- Any FAIL → one fix round: dispatch `omos-implementer` per failing
  capability with the exact scenario lines, then re-run only the failed
  verifiers.
- Rejected: verifier reports that repeat the original claim with a weakened
  bar (skipped test, widened assertion) → treat as FAIL, do not re-dispatch
  the same implementer unchanged.
- Relay every implementer `DEFERRED:` line (`DEFERRED: <task-id> — <reason>
— <user action>`) verbatim to the user before §7 Review starts; a
  deferral naming a task in a manual/eyeball group halts at the gate above
  instead of being relayed.
- After the final wave, before §7 Review, the orchestrator (or a designated
  dispatch) performs the post-final-wave full check suite run once and
  cites its output in the reviewer payload; implementer-scoped runs do
  not replace it.

### 7. Review

Dispatch `omos-reviewer` over the cumulative diff (`git diff --stat` +
full diff) with a `REVIEW FOCUS:` block: the riskiest hunks from the wave
table, verifier notes, and the verbatim `Choices:` report lines of every
wave implementer (including `Choices: none`).

- `CHANGES-REQUESTED` → fix round (implementer), then scoped re-review: only
  the open findings, answered `ADDRESSED` / `NOT-ADDRESSED`.
- On `CHANGES-REQUESTED`, before dispatching the re-review, run the repo's
  own markdown/lint check over every `openspec/` artifact the fix round
  touched, when the repo has one, and paste its output into the re-review
  dispatch.
- BLOCKING findings left at the user's explicit choice only, recorded as
  `ruling:` lines.

### 8. Done

Final report:

- Groups completed per wave with evidence one-liners.
- `choice:` entries — every implementer `Choices:` decision worth the user's
  eye, one line each (`none` if empty).
- `ruling:` entries — user-approved deviations, verbatim.
- `DEFERRED:` entries — verbatim, one line each
  (`DEFERRED: <task-id> — <reason> — <user action>`).
- Verification summary: scenarios PASS count / total, gate VALID;
  `PASS (composited)` lines count as passes.
- `NO-REGRESSION-TEST:` entries — every verifier line relayed verbatim,
  one line each.
- `git diff --stat` of the working tree.
- Next steps for the user, in their hands: review the diff, commit, then
  archive with `$oh-my-openspec:omos-archive <change-id>`. Offered invocations are the
  plugin's `$oh-my-openspec:omos-*` skill mentions whenever one exists for the action;
  the upstream `openspec` CLI is offered only where the plugin has no
  equivalent.
- Branching questions are answered by citing the repo's `CONTRIBUTING.md`
  branch-naming convention, e.g. `feat/<topic>` — branch creation, renaming,
  and commits stay the user's; the flow performs no git writes.

## Guardrails

- Implementation is bounded by the spec delta: any needed change outside it
  is a plan defect → stop and ask, do not sneak it in.
- Never commit, push, or stage; never run `openspec archive` — archiving is
  a deliberate user act after review.
- The wave table is the single source of execution order for this run.
