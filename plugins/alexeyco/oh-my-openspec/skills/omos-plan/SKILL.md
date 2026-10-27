---
name: omos-plan
description: "Plan an OpenSpec change via $oh-my-openspec:omos-plan — coverage interview, parallel research, adversarial grill, agent-drafted artifacts, critique loop, mechanical CLI validation. Invoke via $oh-my-openspec:omos-plan."
---

> Codex host adaptation (generated from skills/omos-plan/SKILL.md — source of truth stays there):
> - Dispatch roles with `spawn_agent` / `send_input` / `wait_agent` / `close_agent`. Subagents are asynchronous (default up to 6 concurrent threads), so a wave is one batch of `spawn_agent` calls followed by `wait_agent` collection — never poll.
> - `openspec_validate` is provided by this plugin's bundled MCP server as `mcp__openspec__openspec_validate` — call it with `cwd` set to your session's project directory (the `change` filter optional); the VALID/INVALID/UNAVAILABLE/ERROR one-look report format is identical to OpenCode.
> - This skill is invoked as a `$oh-my-openspec:omos-plan` mention (or picked from /skills). There is no argument substitution: arguments arrive as plain text in the user's message after the mention — read them from there; when absent, follow this skill's elicitation steps.
> - Roles run from `~/.codex/agents/omos-*.toml`. If `spawn_agent` reports an unknown agent, stop and tell the user to run `$oh-my-openspec:omos-setup` once.

# omos-plan

Turn the user's request into one complete, validated OpenSpec change under
`openspec/changes/<change-id>/`. The orchestrator dispatches, never drafts —
all artifact writing is done by role subagents. You never run git write
commands: the user reviews files and decides what happens to them.

## Flow

### 1. Preconditions

- Check the CLI: call `openspec_validate` once. `UNAVAILABLE` → offer to
  install it now: run `npm install -g @fission-ai/openspec` (or
  `brew install openspec` on macOS) — a global install is a system change,
  so proceed only on an explicit yes. Installed → re-check and continue.
  **Declined** → offer to continue critic-only (non-mechanical validation)
  — their explicit yes required.
- Check the project: `openspec/` directory must exist. **Missing** → ask the
  user for consent, then run `openspec init --tools none` (project artifacts
  only; the plugin already provides every OpenSpec skill — never re-init
  tool files). **User declines** → stop.

### 2. Scope check

One change per run. If the request spans independent capabilities, produce a
capability map (`<name>: <one line> — depends on: <names|none>`) and ask the
user which capability to plan first.

### 3. Coverage interview

Keep an internal coverage map over six categories — `Outcome + scenarios /
Constraints + compat / Data + integrations / Failure + edge / Out of scope /
Success metric` — each `Clear / Partial / Missing` from the request text.
Ask about at most 5 questions per round, ordered by `Impact × Uncertainty`
(Missing categories first), each with a recommended answer:

- Outcome: what the user observes when this is done.
- Why now, and what "good" looks like (these become spec scenarios).
- Constraints: platforms, libraries, performance, compatibility.
- Out of scope: what this change must not touch.
- Capability name(s) the behavior belongs to.

Skip questions the request already answers. Every question defines its terms
with a concrete example or an either/or gloss; when the user signals
non-understanding, in any language, restate the question with the gloss before
recording an answer as `ASSUMPTION:`. Label anything the user leaves implicit
`ASSUMPTION:` — the planner seeds these into the artifacts.

### 4. Research

Dispatch `omos-researcher` subagents in parallel — one per unknown area
(codebase region, existing capability, conventions). Wait for every report.
Every Unknown a read-only local command can answer (`<binary> --help`, a
no-arg subcommand that performs no action) is re-dispatched to a researcher
with a `PROBE:` line; no probe-resolvable Unknown survives into the §6
playback. Feed facts into the next steps; surface their `Unknowns:` questions
in the following interview round.

### 5. Grill (1–3 rounds, up to 5)

Adversarial pass over the user's answers — the point is to break weak
intent before it becomes paper.

- Every attack must cite evidence: a research fact (`path:line`) or the
  user's own words. No invented what-ifs; an attack you cannot ground is
  dropped.
- Attack checklist per material claim: alternative ("why not the existing
  `X`?"), edge/failure case, "what would make this decision wrong",
  scope-reduction pressure, scenario prioritization ("which two would you
  still ship without?").
- Normally 1–3 rounds; up to 5 only when the change is large-scale —
  multiple capabilities in the map, compatibility/migration risk, or the
  user calls it big. At most 3 attacks per claim per round.
- A round that produces no grounded attack ends the grill — intensity is
  set by what the evidence challenges, not by a quota.
- The user may end the grill at any time with "enough".
- **Saturation (grill is done when all three hold):** no category of the
  §3 coverage map is `Missing`; every vague adjective is pinned to a
  metric ("fast" → fast = how much, measured where?); and the last round
  produced no new grounded attack.
- Each risk the user dismisses is recorded as
  `REJECTED-RISK: <risk> — <their reason or "no reason given">`.
  The grill does not override the user — it makes the dismissal visible.

### 6. Playback gate

Restate intent in seven lines — `Outcome / Why now / Success / Constraints /
Out of scope / Rejected risks / Established` — and get explicit confirmation
before any file is written. `Established:` recites up to five decision-relevant
research findings the user might re-ask, one per line, absences included (e.g.
"X exposes no theme API").

### 7. Draft

Dispatch `omos-planner` with `MODE: plan`: the confirmed playback,
research facts, assumptions, `REJECTED-RISK:` lines, and a proposed change
id (kebab-case verb-ish noun). It writes proposal, spec deltas, design
(when non-trivial), tasks.

### 8. Critique loop (≤3 rounds)

Dispatch `omos-critic` on the drafted change.

- `NEEDS-FIX` → dispatch `omos-planner` with the exact BLOCKING list to
  revise; repeat.
- Wait for the planner revision to report DONE (the role's Status line)
  before dispatching the next critic; never batch a critic with the revision
  whose files it reads.
- `CLEAN` → continue.
- After 3 rounds still `NEEDS-FIX` → present the open findings to the user
  and ask: accept them, run one final planner revise plus mechanical
  `openspec_validate` with no further critic, or stop. A final revise ending
  with INVALID output is fixed mechanically and re-validated until VALID —
  never waived, the next bullet holds at loop end; only editorial findings
  are acceptable by user choice.
- Mechanical INVALID lines from the critic are always fixed first, never
  waived by you.

### 9. Approval

Present: change id, file list with one-line summaries, every `ASSUMPTION:`
and `REJECTED-RISK:` line verbatim, validation result. Ask the user to
confirm.

- Confirmed → final report: files, gate output, the current branch read from
  a read-only `git branch --show-current`-style check or "no branch yet"
  (reporting only — not a §1 precondition, no branch creation), next step
  `$oh-my-openspec:omos-apply <change-id>`. Stop — do not implement in the same breath.
  Offered invocations are the plugin's `$oh-my-openspec:omos-*` skill mentions
  whenever one exists for the action; the upstream `openspec` CLI is
  offered only where the plugin has no equivalent.
- Rejected → collect the fix list as one interview round, go to §7.

## Guardrails

- No file outside `openspec/changes/<change-id>/` and `openspec/specs/` is
  written by any dispatched role; project code is untouched in this command.
- Never commit, push, or stage anything.
- The user's confirmed playback, not chat history, is the drafting contract.
