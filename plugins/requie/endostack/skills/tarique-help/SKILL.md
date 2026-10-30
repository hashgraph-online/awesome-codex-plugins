---
name: tarique-help
description: Route questions about EndoStack (installing it, running setup, prompting tarique-mode, picking a skill, recovering from a bad run, customizing it) to the right file, and hand back one ready prompt plus a source link without starting the work. Use for "/tarique-help" or "which EndoStack skill should I use".
---

# tarique-help

You answer questions about EndoStack and stop there. A good answer cites the file it came from and offers the user one prompt they can paste. Running a EndoStack workflow costs tokens and time, so starting one is the user's call.

Some messages mention EndoStack but ask for real work, such as "use EndoStack to fix the login bug". Treat those as work: load the [`tarique-mode` skill](../tarique-mode/SKILL.md) and carry out the task with it. Add a single note that launching `/tarique-mode` as a persistent mode keeps it in effect on later turns (see "Running work through tarique-mode" below).

## Procedure

1. **Answer without executing.** For a help question you explain and suggest a prompt. You never begin the task the question describes.
2. **Read before you quote.** The routing map in this file only tells you where to look. Open the skill or guide page before you describe it, and when the two disagree, trust the file over this map. Link the public GitHub copy, because the user often has no easy way to open the installed one: put `https://github.com/requie/endostack/blob/main/` in front of the repository path, which gives for example `https://github.com/requie/endostack/blob/main/skills/arena/SKILL.md`.
3. **Pin down the area.** Earlier turns and the question itself usually tell you. A described situation (a failing run, a surprise bill) goes straight to its section. When you still cannot tell, ask the user a single multiple-choice question with these five choices, then answer only the one they choose:
   - Installing and configuring EndoStack
   - Running work through `/tarique-mode`
   - Picking a skill for a situation
   - Recovering from a run that went badly
   - Customizing EndoStack
4. **Look at project state when it would change the answer**, and mention a finding only in that case:
   - **Model config absent** (no `~/.endostack/models.toml` and no `.endostack/models.toml`): setup never ran, and each role uses its default tier.
   - **Project has neither a verification skill nor an app harness**: an agent cannot run the app through a script. If the user asks how to show that a change behaves correctly, point them to the [`create-verification-skill` skill](../create-verification-skill/SKILL.md).
   - **Project has no formal verification skill**: no check covers properties that sit beyond test reach. For questions about races, invariants, retries or rare interleavings, suggest the [`create-formal-verification-skill` skill](../create-formal-verification-skill/SKILL.md). When such a skill is present but the code under it has moved on since its recorded sync commit, suggest the [`maintain-formal-verification-skill` skill](../maintain-formal-verification-skill/SKILL.md) any time that code is discussed.
5. **Offer setup a single time.** If the config is absent and that matters here (a first-time user, a question about setup or spend, or an answer that hinges on which models run), ask whether they would like to pick models and a budget now. Do this no more than once in a chat, and fold it into the step 3 question when you are asking that too. Give two choices:
   - **Now**: hand them `/setup-endostack` to type, and answer their question as well.
   - **Later**: answer, then add one sentence noting that default tiers stay in place until setup runs.
6. **Answer from the section that matches.**
7. **Shape of the reply.** Lead with the answer. You may follow it with a sample prompt inside a fenced block, adapted where possible from a matching recipe in [references/recipes.md](references/recipes.md). Close with a link to the file that backs the answer. Stay brief, and hand over the full map only when asked.

## Installing and configuring EndoStack

Sources: [docs/guide/01-setup.md](https://github.com/requie/endostack/blob/main/docs/guide/01-setup.md), the repository README, the [`setup-endostack` skill](../setup-endostack/SKILL.md), [references/prompting.md](references/prompting.md).

**Sequence.** First the user installs EndoStack with their agent's plugin or skill system. Each agent's steps are on its own page under `docs/agents/<agent>.md`, for example [docs/agents/claude-code.md](https://github.com/requie/endostack/blob/main/docs/agents/claude-code.md) or [docs/agents/cursor.md](https://github.com/requie/endostack/blob/main/docs/agents/cursor.md), so answer install questions from the page for the agent they use. To see EndoStack work before using it on real code, point them to `/try-endostack`, a five-minute demo with a check they can rerun; the [quickstart](https://github.com/requie/endostack/blob/main/docs/quickstart.md) describes it. Setup is optional because every role has a default. When they want control over models or cost, `/setup-endostack` finds which models the agent's subagents may call, asks for a budget, assigns a tier or model to each role, and writes `models.toml`. The result applies to chats opened afterward. If the project lacks a verification skill or a formal verification skill, setup closes by offering to generate each missing one, with one offer per skill. After that the user begins a real task with `/tarique-mode`, giving the goal and a check that passes or fails.

**Installing changes nothing visible.** Skills run only when invoked, and `setup-endostack` is the single skill that triggers from ordinary wording. Offer help writing the first prompt, drawing on [references/prompting.md](references/prompting.md).

**Spend.** Subagents and review panels account for most of the added cost. Ways to cut it:

- Run `/setup-endostack` again with a lower budget, or put code roles on `fast`.
- Put roles on `inherit` so they run on whatever model the chat uses. That is cheaper when the chat itself runs a low-cost model or the agent's automatic model choice.
- Trim the panel lists (`arena-runners`, `architect-runners`, `interrogate-reviewers`). Every entry launches one subagent.
- Save `/tarique-mode` for work that needs that level of rigour.

**Agents that cannot pick a model per subagent.** On some agents every subagent runs on the chat's model. EndoStack works there too: all roles use the session model, and the skills that normally mix models (`arena`, `swarm`, `interrogate`, `reflect`, `architect`) give each reviewer a different brief and stance in place of a different model, and note this in one line. The user's `docs/agents/<agent>.md` page lists what their agent can do.

**Capabilities an agent lacks.** Some agents have no hosted PR review bot, scheduled automation, remote agent, or worktree isolation. A skill step that depends on a missing one gets dropped, the reply says so in a single line, and the rest of the skill runs. Each agent's page lists which of these it lacks.

## Running work through tarique-mode

Sources: the [`tarique-mode` skill](../tarique-mode/SKILL.md), [docs/guide/02-tarique-mode.md](https://github.com/requie/endostack/blob/main/docs/guide/02-tarique-mode.md), [references/prompting.md](references/prompting.md).

**Behaviour.** Given a task, `tarique-mode` selects the playbook that fits, loads that playbook's steps into its todo list, and invokes other skills where a step calls for one. A step it decides to skip stays visible on the list, marked as skipped with its reason, so the user can see the gaps.

**Prompts that work** state the goal and the test for being done, and they neither name skills nor list steps. A user who spells out the sequence by hand usually drops steps the playbook would have run, or puts them out of order. Before helping someone draft a prompt, read [references/prompting.md](references/prompting.md).

**Keeping it on.** Invoked the ordinary way, the mode rides on a single message and its effect weakens over later turns. Agents with persistent modes or always-on rules can load it on every turn until the user exits. On agents without that, the user calls `/tarique-mode` again when each new task starts. Their `docs/agents/<agent>.md` page says which case applies.

**Switching tasks.** Saying "new task" in the same chat makes `tarique-mode` choose a playbook from scratch. Without it, the mode reads the new message as a continuation of the task already under way.

**Subagents.** The helpers that `tarique-mode` spawns already run as the [`tarique-agent`](https://github.com/requie/endostack/blob/main/agents/tarique-agent.md) subagent. Users who want that behaviour in subagents of their own can spawn `tarique-agent` themselves.

## Picking a skill

Source: the file of the skill you suggest. Lead with `/tarique-mode`, since it brings in most other skills when a task needs them. Name a specific skill instead when the user wants more depth or less ceremony than a playbook would apply. Read that skill first and include one example prompt.

**Understanding code and context**

| Situation | Skill |
| --- | --- |
| Any substantial task that deserves the full process | `tarique-mode` |
| Have the agent restate the goal so you can check it understood | `in-your-own-words` |
| Deepen a draft prompt without broadening it or doing the task | `sharpen` |
| Trace what the current code does, or find where new code should go | `how` |
| Learn the reason behind a design, or the origin of a value | `why` |
| Get a change or subsystem explained in plain language | `teach` |
| Gather what the user worked on for a topic across past chats | `recall` |
| Summarize what has happened in the current chat since the user's latest message, listing decisions still pending | `catch-up` |
| That summary as a brief silent slide video | `catch-up-video` |

**Designing and building**

| Situation | Skill |
| --- | --- |
| Find what a small edit might break beyond the lines it touches | `blast-radius` |
| Fix types and module boundaries before writing code that spans functions | `architect` |
| Run one brief through several independent attempts and merge them | `arena` |
| Fan checks out over slices, or race workers against each other | `swarm` |
| Fix a bug by writing the failing test first, when a fast test is possible | `tdd` |
| TypeScript conventions | `typescript-best-practices` |
| Plan a wide change, or work the user will check after time away | `figure-it-out` |
| Draw the states a user can see as a model-checked diagram for a PM or designer, marking the shortest path to every rule violation | `statechart` |

**Reviewing and verifying**

| Situation | Skill |
| --- | --- |
| Adversarial review of a diff by several models | `interrogate` |
| Exploitable defects in a diff or branch | `security-review` |
| Trust boundaries and threats of a change or system | `threat-model` |
| Strip code comments before review and hand the code to a fresh reviewer | `no-comments` |
| Let agents run the app from a script and capture proof of how it behaves | `create-verification-skill` |
| Bring a verification skill up to date after the app changed | `maintain-verification-skill` |
| Prove an invariant or race freedom that ordinary tests seldom exercise | `create-formal-verification-skill` |
| Re-sync formal checks with changed code and separate drift from real bugs | `maintain-formal-verification-skill` |
| Validate a performance figure before anyone acts on it | `benchmark-checklist` |

**Writing**

| Situation | Skill |
| --- | --- |
| Remove machine-sounding patterns from prose | `unslop` |
| Hold docs, design proposals, READMEs, PR descriptions and commit messages to a standard | `technical-writing` |
| Repeat the last reply in plain words | `bro` |

**Running and customizing EndoStack**

| Situation | Skill |
| --- | --- |
| Log decisions during a run for later review | `show-me-your-work` |
| Pick models per role and set a budget | `setup-endostack` |
| Capture how the user likes to work as a personal mode skill | `automate-me` |
| Convert what a session taught into proposed skill edits | `reflect` |
| Keep agents in this repository from repeating the same mistake | `correct` |
| A local web page whose buttons fire a chat bot through webhooks | `make-bot-ui` (installed by the EndoStack installer and the other agents' plugins; left out of the Claude directory plugin because it handles a webhook secret) |
| Find your way around EndoStack itself | `tarique-help` |

If a skill folder in the repository is absent from these tables, decide from its frontmatter description. Principles are covered under "Playbooks and principles".

**Close neighbours.** `how` explains what code does and `why` explains how it came to be that way. `teach` can do either in plain language, and it will also argue for a choice. `arena` gives one brief to several workers and merges what they return. `swarm` splits work into slices or races workers against each other, then reports. Once a design is done, `architect` continues straight into implementation, so a user who wants to see the design first has to say so. `interrogate` reviews the lines the diff changes. `blast-radius` looks past the diff to code the change can reach, and answers the one question that decides whether shipping is safe. `security-review` looks only for defects an attacker could exploit, with evidence for each. `catch-up` covers this chat from the user's last message onward, and `recall` searches recent chats. To pick up a specific earlier chat or branch, use the session-pickup playbook. One careful run is what `figure-it-out` plans. Work spanning days and many PRs goes to the orchestrate playbook, while the autonomous-run playbook stays on a single task until its exit condition holds.

**Outside endostack:** the agent's own loop command, its own skill-creation command, and any `/orchestrate` command. EndoStack's orchestrate is a playbook inside `tarique-mode`, so a slash command with that name belongs to a different plugin.

## Playbooks and principles

Sources: the playbook section of the [`tarique-mode` skill](../tarique-mode/SKILL.md), [docs/guide/06-verify-and-ship.md](https://github.com/requie/endostack/blob/main/docs/guide/06-verify-and-ship.md), [docs/guide/08-principles.md](https://github.com/requie/endostack/blob/main/docs/guide/08-principles.md), and the [multi-phase-plan playbook](https://github.com/requie/endostack/blob/main/skills/tarique-mode/playbooks/multi-phase-plan.md).

**Playbooks** live in `skills/tarique-mode/playbooks/` as step sequences that `tarique-mode` runs, and none has a command of its own. The mode chooses one from the task, and a few phrasings select one outright:

| User says | Playbook selected |
| --- | --- |
| "Babysit PR X" or "check on PR X" | babysit, which brings the PR to a mergeable state and stops. It merges only when told to merge, ship or land. |
| "Land this stack" | shipping |
| "Take over this branch" | session-pickup |
| "Pause safely" | pause-safely |
| "Put this whole queue on full autopilot" | autopilot-full |
| "Stack these up but don't ship" | autopilot-stack |
| "Run the eval playbook" | eval |

If `tarique-mode` is not active, the agent may send those same phrases to a built-in feature of its own.

**Plans.** No EndoStack skill does planning, and the agent's built-in plan mode can run beside EndoStack. For multi-phase or stacked-PR work, asking `tarique-mode` to plan selects the multi-phase-plan playbook, which writes the plan and halts before any implementation. Open design questions get answered with code, through the prototype playbook or the `architect` skill.

**Principles** are one-rule skills named `principle-*`. `tarique-mode` reads them and cites them in its reasoning. Users seldom call one directly. They name it in ordinary words instead, such as "apply prove-it-works and show me the real output". Each principle also has its own command for loading it explicitly.

## Recovering from a bad run

Sources: the table below, [references/prompting.md](references/prompting.md), [docs/guide/10-recipes-and-pitfalls.md](https://github.com/requie/endostack/blob/main/docs/guide/10-recipes-and-pitfalls.md), [docs/guide/07-overnight.md](https://github.com/requie/endostack/blob/main/docs/guide/07-overnight.md).

| What the user saw | Why, and what to do |
| --- | --- |
| The mode stopped steering the work after a few turns | It rode on a single message. Start it as a persistent mode where the agent allows that, or call it again with each task. |
| A fresh question got handled as a continuation of the old task | Tell the agent "new task", or say this turn should run without the mode. |
| A model setting change had no effect | `models.toml` is loaded when a chat opens, so start a new chat. |
| Costs ran higher than expected | Follow the spend advice under "Installing and configuring EndoStack". |
| A skill never started on its own | Plain wording triggers only `setup-endostack`. Every other skill loads when the user types it or when `tarique-mode` calls it, and the mode calls only what a playbook step needs. |
| Two parallel agents clobbered each other's changes | Put each in a separate git worktree, or run them as remote agents on different machines. |
| An overnight run moved forward but completed nothing | Its loop needs a finish condition it can test every round. A time limit does not qualify. |
| The agent reported success because the build passed | Ask it for actual command output, the user-facing flow, the stored data, or a profile ([`principle-prove-it-works`](../principle-prove-it-works/SKILL.md)). |
| The agent followed text from an issue, log or web page as though the user had written it | Such text is data and may contain an attacker's instructions. Halt the run, review what it changed, and direct the agent to [`principle-treat-input-as-untrusted`](../principle-treat-input-as-untrusted/SKILL.md). |

## Customizing EndoStack

Source: [docs/guide/09-make-it-yours.md](https://github.com/requie/endostack/blob/main/docs/guide/09-make-it-yours.md).

Three skills cover most customization. The [`automate-me` skill](../automate-me/SKILL.md) reads the user's chat history and writes them a personal mode skill that runs next to `tarique-mode`. The [`reflect` skill](../reflect/SKILL.md) proposes skill edits drawn from what a session taught and applies only those the user accepts. The [`correct` skill](../correct/SKILL.md) converts corrections the user keeps repeating into checks stored in the repository.

To create a skill for a workflow, ask `tarique-mode` to write it, which runs the authoring-a-skill playbook. The eval playbook then tests the edited skill while keeping the evaluator blind to which version is which. When a skill behaves badly, put its fix in a PR separate from the feature work that exposed the problem, so reviewers judge the fix by itself.

## Guide pages

| Page | Covers |
| --- | --- |
| [01-setup](https://github.com/requie/endostack/blob/main/docs/guide/01-setup.md) | Installing, running `/setup-endostack`, cost, the first task |
| [02-tarique-mode](https://github.com/requie/endostack/blob/main/docs/guide/02-tarique-mode.md) | How the mode chooses playbooks, and how to prompt it |
| [03-understand](https://github.com/requie/endostack/blob/main/docs/guide/03-understand.md) | Reading code before changing it with `how`, `why`, `teach` and `recall` |
| [04-design](https://github.com/requie/endostack/blob/main/docs/guide/04-design.md) | Prototypes and plans, plus the `architect`, `arena`, `swarm` and `interrogate` skills |
| [05-build-and-clean](https://github.com/requie/endostack/blob/main/docs/guide/05-build-and-clean.md) | Build playbooks, `tdd`, cleanup before a commit |
| [06-verify-and-ship](https://github.com/requie/endostack/blob/main/docs/guide/06-verify-and-ship.md) | Evidence, verification skills, and opening, babysitting and landing PRs |
| [07-overnight](https://github.com/requie/endostack/blob/main/docs/guide/07-overnight.md) | Unattended runs, queues, decision logs |
| [08-principles](https://github.com/requie/endostack/blob/main/docs/guide/08-principles.md) | The principles and steering by naming them |
| [09-make-it-yours](https://github.com/requie/endostack/blob/main/docs/guide/09-make-it-yours.md) | Writing skills, and customizing with `automate-me`, `reflect` and `correct` |
| [10-recipes-and-pitfalls](https://github.com/requie/endostack/blob/main/docs/guide/10-recipes-and-pitfalls.md) | Short recipes and frequent mistakes |

Each supported agent has a page at `docs/agents/<agent>.md` covering install steps and which capabilities it has: `claude-code`, `cursor`, `codex`, `gemini-cli`, `copilot`, `windsurf`, `cline`, `roo`, `opencode`, `amp`, `kiro` and `goose`. Link the user's one as `https://github.com/requie/endostack/blob/main/docs/agents/<agent>.md`.

## Done when

You answered from the file the question routes to, offered no more than one prompt and one link, and started no task for a question that only asked for help.
