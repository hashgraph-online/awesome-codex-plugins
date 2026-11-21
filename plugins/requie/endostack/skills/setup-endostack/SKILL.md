---
name: setup-endostack
description: Configure EndoStack. Detect which models this agent's subagents can use, pick a reasoning budget, map each EndoStack role to a tier or model, and write models.toml. Use for "set up EndoStack", first-time setup, changing models or budget, or cutting EndoStack's cost.
---

# setup-endostack

Decide which model each EndoStack role runs on and how hard it reasons, using only models this agent can actually reach, and save the result to a TOML file that every EndoStack skill reads before it spawns a subagent. Then, once, offer to generate verification skills for the project.

This is the one EndoStack skill that may start from a plain request such as "set up EndoStack" without the user typing the command. Every other skill loads when typed or when the [`tarique-mode` skill](../tarique-mode/SKILL.md) calls it.

Picking a model for a single run, such as one competitor in a [`swarm`](../swarm/SKILL.md) model race, is handled by that skill, not here.

Track a todo list with these items: detect, baseline, budget, review, validate, write, confirm, offers.

## 1. Detect models

Find out which models the agent's subagent tool accepts in this session. Ask yourself first: check the subagent tool's description or schema for a list or enum of model values, and check `docs/agents/<agent>.md` for this agent's notes. If the agent also has a command or API that lists the models the user is entitled to, run it for a fuller list.

If you cannot list them, ask the user which model names their agent lets subagents use.

Record a model name only if you saw it in one of those sources or the user gave it. Never write a name you guessed. `inherit` is always valid even though no detection returns it.

**No per-subagent model choice.** Some agents run every subagent on the session's model and have no way to choose per subagent. If that is the case here, tell the user plainly: every EndoStack role will run on whatever model the chat uses, so the role table has no effect on which model runs, and only the budget (if the agent exposes a reasoning setting) and panel sizes matter. Still write the file, with every role set to `inherit`, so that panel sizes are recorded and the file is ready if the agent gains the feature. Skills that run panels on such an agent vary each reviewer's brief and stance instead of its model, and say so in one line.

## 2. Establish the baseline

Start from these defaults. They put `strong` on judgment, prose, and the hardest code, and `fast` on mechanical code and verification sweeps. With the `large` budget they match what each skill does with no config file. The first seven keys are the ones the [`tarique-mode` skill](../tarique-mode/SKILL.md) reads.

| Key | Used by | Default |
| --- | --- | --- |
| `feature` | `tarique-mode` delegates for features and refactors | `fast` |
| `bug-fix` | `tarique-mode` delegates for bug fixes | `fast` |
| `perf` | `tarique-mode` delegates for performance fixes | `fast` |
| `hillclimb` | `tarique-mode` hillclimb attempts | `fast` |
| `hardest` | cross-cutting design, tricky concurrency, subtle algorithms | `strong` |
| `judgment` | prose, reviews, judgment calls; `interrogate`'s security seat | `strong` |
| `swarm-workers` | every `swarm` worker and verification lane, unless a race assigns models | `fast` |
| `how-explorer` | explorer subagents in `how` | `fast` |
| `how-explainer` | explainer subagent in `how` | `strong` |
| `why-investigator` | investigator subagents in `why` | `fast` |
| `why-synthesizer` | synthesizer subagent in `why` | `strong` |
| `recall-miner` | transcript miners in `recall` | `fast` |
| `reflect-tooling` | tooling reviewer in `reflect` | `fast` |
| `reflect-judgment` | judgment reviewer, divergent reviewer, and synthesizer in `reflect` | `strong` |
| `arena-runners` | `arena` runners (list, one entry per runner) | `["strong", "fast"]` |
| `arena-judges` | `arena` judge pool (list, one judge drawn) | `["strong", "fast"]` |
| `architect-runners` | `architect` sketch runners (list) | `["strong", "fast"]` |
| `interrogate-reviewers` | `interrogate` reviewer seats (list) | `["strong", "fast"]` |

Values are a tier (`strong`, `standard`, `fast`), `inherit` (the chat's model; `auto` is accepted as an alias), or a model name this agent accepts. The full file layout is in [references/roles.md](references/roles.md).

If a config file already exists, read it. Its `budget` and each role's value become the current selections. Drop any key that names a role no longer in the role list, and keep a note of what you dropped to show the user in step 4.

Config locations:

- User: `~/.endostack/models.toml`
- Project: `.endostack/models.toml` at the repository root. When both exist, the project file wins key by key.

Ask the user which one to write if it is not obvious. Personal model preferences go in the user file. A team that wants the same panel for everyone commits the project file.

## 3. Choose the budget

Ask the user, with a multiple-choice question if the agent has one, which budget to use:

| Budget | Reasoning effort |
| --- | --- |
| `unlimited` | maximum |
| `large` | high (the default) |
| `medium` | medium |
| `small` | low |

If the file records a budget, say which one is current. If there is no file, say that `large` matches the built-in defaults.

The budget sets the reasoning effort for every subagent EndoStack spawns, on agents that accept an effort or thinking setting per subagent. On agents whose model names encode effort (a name with a `-high` or `-low` variant, for example), rewrite the effort part of each concrete name to the budget's level. If that exact variant was not detected, use the detected variant in the same family with the highest effort not above the target. If none exists, mark the role as needing the user's choice. Tier values and `inherit` are not rewritten: the skill that reads them applies the budget at spawn time.

## 4. Review the table

Show every role with its value after the budget is applied. Mark any concrete name that was not detected as needing a choice, and list any keys dropped in step 2.

Ask the user whether to keep the table or change specific roles. Offer the three tiers, `inherit`, and the detected model names. Explain these points briefly, once:

- **Tiers.** `strong` is the most capable judgment model available, used for review, design, prose, and the hardest code. `fast` is a quick, capable model, used for mechanical code changes, exploration, and verification sweeps. `standard` sits between them. Each skill maps the tier to a concrete model at spawn time using `docs/agents/<agent>.md`.
- **`inherit`.** The role runs on the same model as the chat that spawned it (the skill passes no model). This is how someone who uses their agent's automatic model picker stays on it, and it is the cheapest choice when the chat itself runs a cheaper model.
- **A specific model name.** Pins the role to that model regardless of the chat.
- **Lists.** Four roles hold lists: `arena-runners`, `architect-runners`, `interrogate-reviewers`, and `arena-judges`. In the first three, each entry, `inherit` included, launches one subagent, so the list length is the panel size. `arena-judges` is a pool: arena draws one judge from it, preferring a family different from the chat's.
- **`swarm-workers`** applies to every swarm worker except where a model race assigns a model per competitor.

## 5. Validate

Before writing, compare each concrete model name against the models you detected. A name passes if detection found it or the user typed it. Tier names and `inherit` need no check. For any name that fails, stop and ask the user again about that role.

## 6. Write the file

Replace the whole file each time, so running setup twice with the same answers produces the same file. Use the layout in [references/roles.md](references/roles.md): a header comment, `budget`, then one key per role in the listed order.

The header comments state:

- The file records per-role model choices that override each EndoStack skill's default.
- Deleting a key restores that role's default.
- `inherit` means the role uses the chat's model, and an `inherit` entry in a panel list still adds a seat.
- Which budget was chosen and the effort it maps to.

## 7. Confirm

Tell the user:

- Where the file was saved.
- That only chats started from now on will read it, because skills read the config when they load. Open a new chat.
- That running `/setup-endostack` again revises it.
- To cut cost: choose a smaller budget, set code roles to `fast` or `inherit`, shorten the panel lists (each entry is one subagent), and keep `/tarique-mode` for work that needs its rigour.

## 8. One-time offers

Make each offer at most once. If the user declines, continue and do not raise it again in this chat.

1. **Verification skill.** If the project has no way for an agent to run the real application and prove behaviour (no project verification skill and no existing test harness that drives the app), offer to run the [`create-verification-skill` skill](../create-verification-skill/SKILL.md). With such a skill, an agent runs the app to test its own change and keeps going until that test passes. Without one, the agent tends to stop as soon as the build succeeds.
2. **Formal verification skill.** If the project has no skill that runs a model checker, theorem prover, or similar verifier, offer to run the [`create-formal-verification-skill` skill](../create-formal-verification-skill/SKILL.md). Explain that it shows an important property holds in every case within scope, where tests only cover the cases someone thought to write. It pays off most where there is concurrency, retries, state machines, or parsers.

## How skills read the file

For builders and for skills that spawn subagents:

1. Read the role's key from `.endostack/models.toml`, then `~/.endostack/models.toml`. The first file that has the key wins.
2. If neither file has the key, use the default in the table in step 2.
3. `inherit` or `auto`: pass no model, so the subagent runs on the chat's model.
4. A tier: map it to a concrete model using `docs/agents/<agent>.md`.
5. If the agent rejects the model, fall back to the role's default tier and tell the user in one line. If the default is rejected too, use the closest valid model the agent's error lists, and suggest rerunning setup.
6. Apply the budget's effort level if the agent accepts one.
7. If the agent has no per-subagent model choice, run on the chat's model and, for panels, vary each seat's brief instead.

## Done when

Every concrete model in the file was detected or supplied by the user, the file is saved, the user knows only new chats read it, and each verification offer was made at most once.
