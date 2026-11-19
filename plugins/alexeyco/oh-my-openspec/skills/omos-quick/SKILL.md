---
name: omos-quick
description: "Quickly plan and apply one bounded change via $oh-my-openspec:omos-quick — short interview, focused research, one plan confirmation, and full verification; archive separately. Invoke via $oh-my-openspec:omos-quick."
---

> Codex host adaptation (generated from skills/omos-quick/SKILL.md — source of truth stays there):
> - Dispatch roles with `spawn_agent` / `send_input` / `wait_agent` / `close_agent`. Subagents are asynchronous (default up to 6 concurrent threads), so a wave is one batch of `spawn_agent` calls followed by `wait_agent` collection — never poll.
> - `openspec_validate` is provided by this plugin's bundled MCP server as `mcp__openspec__openspec_validate` — call it with `cwd` set to your session's project directory (the `change` filter optional); the VALID/INVALID/UNAVAILABLE/ERROR one-look report format is identical to OpenCode.
> - This skill is invoked as a `$oh-my-openspec:omos-quick` mention (or picked from /skills). There is no argument substitution: arguments arrive as plain text in the user's message after the mention — read them from there; when absent, follow this skill's elicitation steps.
> - Roles run from `~/.codex/agents/omos-*.toml`. If `spawn_agent` reports an unknown agent, stop and tell the user to run `$oh-my-openspec:omos-setup` once.

# omos-quick

Plan and apply one small, bounded change in a single run. Keep the OpenSpec
artifacts and implementation evidence; shorten the interaction, not the
quality gates. Never commit, push, or archive.

## 1. Capture and triage the request

Use the request text supplied by `$oh-my-openspec:omos-quick`. If none was supplied, ask the
user what single behavior they want to change.

The quick path is eligible only when all of these are true:

- The request changes exactly one externally observable behavior in one
  capability.
- It does not change a public API or architecture, require a data migration,
  or affect security or privacy behavior.
- It has no material unresolved risk and does not contain multiple independent
  behaviors or broad, cross-capability scope.

If any condition is false or unclear, use the ordinary plan and apply gates in
this same run. Do not silently split a broad request or guess that an excluded
change is safe to quick-apply. The ordinary path includes the full coverage
interview, research, adversarial grill, confirmed playback, planning and
critique, mechanical validation, and the usual apply approvals and checks.

## 2. Short interview and focused research

For an eligible request, ask only for missing information needed to define the
observable behavior, its acceptance scenario, constraints, and out-of-scope
work. Keep this to one concise interview round. Label unconfirmed inferences
`ASSUMPTION:`. If answers reveal broad scope, an excluded change, or material
unresolved risk, switch to the ordinary path above.

Research only the relevant capability and conventions. Dispatch an
`omos-researcher` for material codebase unknowns; cite its findings by path and
line. Do not run the multi-area research or adversarial grill used by the
ordinary planning flow.

## 3. Draft and validate the change

Dispatch `omos-planner` with `MODE: plan` to create one OpenSpec change for
the confirmed request. Include the observed behavior, acceptance scenario,
constraints, research facts, and labeled assumptions. Keep the change to one
capability.

Dispatch `omos-critic` to check the artifacts against the request and the
relevant specs. Follow the ordinary planning critique loop: fix blocking
findings with the planner and repeat, up to three rounds. Then call
`openspec_validate` for the change. If it is not `VALID`, do not edit project
code; send the exact findings to the planner and revalidate after each
revision. Stop and report the remaining findings if they cannot be resolved
safely.

## 4. Confirm the compact plan

After the critic and mechanical gate pass, show the user a compact summary:
change id, behavior being changed, capability, planned files and tasks,
acceptance scenario, assumptions, and validation result. Ask for one
confirmation before editing project code.

If the user declines, stop before project-code edits. Report the OpenSpec
change id and ask whether they want to revise the plan or stop. Do not treat
silence as confirmation.

## 5. Apply and verify

After confirmation, implement the approved tasks in this same run; do not
require a separate `$oh-my-openspec:omos-apply` invocation. Follow the apply flow's gates:
build dependency-ordered waves, dispatch implementers with the assigned tasks
and spec scenarios, honor manual acceptance gates, verify each capability,
run the full project check suite once after the final wave, and review the
cumulative diff. Record concrete verification evidence for every scenario.

Pause on a plan divergence. Get explicit user approval before changing
contractual behavior or scope, and follow the apply flow's recovery and
revalidation rules. Do not weaken checks or skip failed scenarios to finish.

## 6. Report and leave archive separate

Report completed groups, scenario evidence, validation and check results,
review findings, assumptions, choices, and any deferred work. Do not archive,
commit, push, or stage. Offer the host's archive command as a separate next
step: `$oh-my-openspec:omos-archive <change-id>`.
