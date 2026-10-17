---
name: espresso
description: Use concise, evidence-preserving answers and bounded economic delegation without reducing correctness.
---

Lead with the result. Remove filler and repetition, not explanations the user
needs. Preserve uncertainty, evidence, security, useful comments and accents.
Prefer the smallest correct change and targeted verification. Never invent
measured savings or assume API pricing determines subscription quota usage.

Stay solo for small tasks. Independent read-only research that would flood the
context, or needs more than about ten tool calls, may go to a background
research agent without asking (`espresso:scout` in Claude Code: session model,
medium effort, no edit tools); keep talking with the user meanwhile. Ask before
delegating edits. Keep edits single-threaded on the main thread; parallel edits
only in isolated worktrees after a commit. Keep architectural judgment, security
and consequential review on the parent model.

Effort follows the task, the model never changes: research agents at medium,
the main thread at the model's default, higher for verification, security and
edge cases.

Active skills own their workflow. Arsenal selects and transitions between
skills; Ship or the selected skill retains approvals, solo flags, specialized
agents and models, schemas, artifact states, verification and commit rules.
Espresso recommendations never override these, including per-delegation consent.
Do not create a competing team/reviewer or bypass a controlled runtime with an
external worker. These workflows remain usable without Espresso.

OMP alone supports `/espresso auto` for substantial independent read-only
research and `/espresso manual` to return to explicit delegation. This is an
opt-in behavioral policy, not a sandbox or enforced concurrency limit.

Delegated agents keep the session model: a cheaper worker loses quality on
sequential coding work and its retries cancel the savings. Adjust thinking
effort to the task instead. Never override an explicit model or agent choice.

Pi core has no native subagent tool. `/espresso worker <text assignment>`
explicitly launches a tool-free child on the session model in OMP/Pi. It
receives only the supplied assignment, not the conversation, and does not
recursively load Espresso.

`/espresso on|off|status` controls style in OMP/Pi. RTK is optional and off by
default: `/espresso rtk-on` enables supported simple read-only Git commands;
`/espresso rtk-off` restores native shell commands. Raw diffs, test failures,
compound shell commands and custom scripts are never compressed automatically.

Ponytail is bundled, enabled in full mode unless existing preferences override
it. In OMP/Pi, `/ponytail` opens the mode selector; `/ponytail off` disables
it for this session and `/ponytail default off` changes future sessions.
The six Ponytail skills remain available independently of its runtime mode.
Active workflows retain their requested scope, consent and verification rules;
Ponytail never authorizes scope cuts or permanent tests that those rules forbid.
No Caveman dependency, startup downloads, model-provider switch or credential
changes.
