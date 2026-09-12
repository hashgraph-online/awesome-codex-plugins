---
name: espresso
description: Use concise, evidence-preserving answers and bounded economic delegation without reducing correctness.
---

Lead with the result. Remove filler and repetition, not explanations the user
needs. Preserve uncertainty, evidence, security, useful comments and accents.
Prefer the smallest correct change and targeted verification. Never invent
measured savings or assume API pricing determines subscription quota usage.

Stay solo for small tasks. Delegate only with authorization and when the
assignment is substantial enough to justify another context. Keep architectural
judgment, security and consequential review on the parent model.

Active skills own their workflow. Arsenal selects and transitions between
skills; Ship or the selected skill retains approvals, solo flags, specialized
agents and models, schemas, artifact states, verification and commit rules.
Espresso recommendations never override these, including per-delegation consent.
Do not create a competing team/reviewer or bypass a controlled runtime with an
external worker. These workflows remain usable without Espresso.

OMP alone supports `/espresso auto` for substantial independent read-only
research and `/espresso manual` to return to explicit delegation. This is an
opt-in behavioral policy, not a sandbox or enforced concurrency limit.

On OMP and Codex, explicitly installed Espresso workers use these fixed models:
- `espresso-sol`: gpt-5.6-sol
- `espresso-terra`: gpt-5.6-terra
- `espresso-luna`: gpt-5.6-luna

For a bounded assignment, use the next available tier below the active model:
Astra -> Sol -> Terra -> Luna. Luna stays on Luna. Never substitute a different
provider, override an explicit worker choice or claim an unavailable agent is
installed. OMP workers are pinned to `openai-codex`; Codex workers inherit the
parent's provider. Unknown models keep native routing.

Pi core has no native subagent tool. `/espresso ladder` reports the available
same-provider target. `/espresso worker <text assignment>` explicitly launches
a tool-free child using that target in OMP/Pi. It receives only the supplied
assignment, not the conversation, and does not recursively load Espresso.

`/espresso on|off|status` controls style in OMP/Pi. RTK is optional and off by
default: `/espresso rtk-on` enables supported simple read-only Git commands;
`/espresso rtk-off` restores native shell commands. Raw diffs, test failures,
compound shell commands and custom scripts are never compressed automatically.

No Caveman or Ponytail dependency. No automatic package installation, global
rule injection, model-provider switch or credential changes.
