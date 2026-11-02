# Asking the scoping round

Step 1 of the skill writes the job and walks the path. This file sets how the questions that follow are asked, what each one offers, and what the Scope line records. The rules the answers lean on (intents, regions, platform, relaxing a default, look words) are in [scope-and-preserve.md](scope-and-preserve.md). The options are the first text the user reads, so reread Ground rules before writing any.

## How a round is asked

Decide from the tools you can call in this turn, never from the host's name or from habit:

- **A question tool is callable** (`AskUserQuestion` in Claude Code, `request_user_input` in Codex where the mode exposes it, or the like): ask with it, one call per round, fitted to its schema. Where it takes fewer options than a question needs, drop the lowest-ranked candidates first, never Help me decide.
- **None is callable**, including a host that has one in other modes: fold every round into one **proposed scope**, below. Do not open a round you cannot ask and then describe it.
- **The call fails or returns no answer**: use the proposed scope for the rest of the run. Do not call the tool again.

Only a reply that called the tool may mention a panel, a picker, options to select, or anything "below" to click. A text round asks for a word in reply, and says so.

Ask only what the prompt leaves open. A prompt that names the target, the fault and the constraints skips the round, and the Scope line records what it took from the prompt. "Redesign my settings page" gets the full round.

One line comes before the questions, saying what the source is (a screen or a crop, the platform, the kind of product) so the options can be concrete: "An iOS paywall screen." Never describe the screen back to the user or give its dimensions; they have the image.

## The order of the rounds

1. **Mode**, unless a flag set it. Always the first question the user sees, alone in its round, because it decides which questions follow.
2. **Source**, when the codebase question applies. A round of its own.
3. **Target, Problems and Preserve**, in one round. Platform folds into Target when it is not obvious. Explore mode drops Problems, as [variations.md](variations.md) says.

## Mode

Single-select. The option the prompt points to comes first, marked recommended:

- **Explore** when the prompt names no fault, part or reference ("make this better").
- **Targeted** when it does ("the trial button is buried", "like Calm's").

A look word ("more vibrant", "less cluttered", "less slop") is not open-ended. It maps to a mode and an axis as [scope-and-preserve.md](scope-and-preserve.md) sets out, and the recommended option follows that.

## The codebase question

It applies when the only input is an image and nothing in the working directory renders it. Headed Source, single-select, one line on what each answer gets:

- **Point me at the code.** The region is named by file and symbol, the state list comes from what the source can render, the render is edits to the source, and the result can be checked.
- **Image only.** The region is named by what is visible, every state but the pictured one is missing until the user says otherwise, and the render is the before and after image alone.

It comes before the scoping questions because they are written from whichever source the answer names. A codebase that arrives after the moves are written sends the run back to step 2.

## The three scoping questions

**1. What exactly is the target?** Single-select: the three intents, each with the concrete thing you saw. The whole screen, one component in it (name the region; everything outside it is frozen), or one web section (hero, pricing, feature grid, footer). A crop is a section, not a screen, and the question says so.

**2. Which of these should this pass fix?** Multi-select from the ranked candidates of the job walk.

- **The user's own complaint is not an option.** It is already in the problem list, and the question's first line says so: "Your point about the trial button is in. Which of these should this pass also fix?"
- **A metric or a named reference is never an option.** It goes into the Scope line in the user's words, and the candidates that block it are what gets ticked.
- **Label and description.** The label names the break in the target's own terms. The description names the step of the job it blocks, then what on the screen shows it. Label: "Plan and trial button do not lead". Description: "choosing a plan is the first step here, and the yearly plan and the trial button sit below the comparison table, past the first view on the phone, so the choice is made after a scroll". The pixel measurement behind it stays in your notes.
- **Four options.** The first is always **Help me decide** ("I'll pick the ones that block the most of the job"). The three highest-ranked candidates fill the rest. Every other candidate goes to the Deferred record.
- **What the ticks mean.** The ticks are the **problem list** for this pass, in the order ticked, then by rank. Help me decide, no tick, or "just go" takes the top three by rank. Help me decide ticked beside candidates takes those and tops them up to three by rank.
- **After the round**, one line names what was picked, one short clause each with the step it blocks. The run carries on without asking again.

**3. What else must survive?** The question tool cannot pre-tick, so what holds in every run is never an option. The question's first line states it in this product's terms: "The design system, the data and routes, and the installed dependencies hold. What else must survive?"

- **Four options.** The first is always **Help me decide** ("I'll change only what makes the experience better"), so the user has an answer to pick instead of leaving the question blank. The rest come from what the source showed: the copy word for word, the layout footprint, and a named element a redesign might otherwise touch (the hero illustration, the comparison table).
- **What the ticks mean.** Help me decide, or no tick, means only what holds in every run holds. Everything else may change where a move needs it, and nowhere else. Help me decide ticked beside other options keeps those too.
- A user who wants a default relaxed types it in the free-text option. That triggers one follow-up before scoping continues, as [scope-and-preserve.md](scope-and-preserve.md) sets out.

## The proposed scope

Without a question tool, the rounds fold into one reply. It states the Scope line the run would proceed on and asks for one word. It is still a round: nothing is built before the answer.

Short lines, each with a bold lead-in, in this order:

- **Mode.** When no flag set it: the recommended mode and the word that switches it. "Explore: three directions to pick from. Say targeted to fix named problems instead." The lines under it are written for that mode.
- **Source.** When the codebase question applies, in place of its own round: "Image only. Point me at the code if there is some, and the changes land there."
- **Target.** What the source read as.
- **Fix in this pass.** The top three candidates, each with what on the screen shows it.
- **Also seen, not in this pass.** Every other candidate, so nothing deferred is hidden.
- **Holds.** What holds in every run, and anything the prompt asked to keep.

Then one closing sentence: say go, or name the change, with the edit paths in the user's terms (a narrower target such as the plan cards only, a problem to add or drop, something else that must stay). "Go" and any edit map onto the Scope line the same way ticks do. "Show me the others" gets the lettered lists in reply. The run stops until the user answers.

## The domain

The **domain** is the kind of product, in a word or two: finance, health, developer tools, food delivery. Read it off the source (the content, the units, the vocabulary on the screen), and ask only when that fails. The Preserve list's first item holds the render to it, and the report weighs a cross-domain roll call against it. A run that cannot read it says so rather than guessing.

Platform is read the same way; [scope-and-preserve.md](scope-and-preserve.md) sets how.

## The Scope line

Assume only once you have asked. A skipped question or "just go" proceeds on labelled assumptions, and an ambiguity that survives asking takes the narrowest reading.

Every answer and assumption goes into one **Scope line**: intent, region, platform, domain, source form, the job, the problem list in the user's words, the constraints. It is fixed after step 1 and kept in your notes; the report never prints it. Anything it records that the user has not been told (an Android source searched as iOS, a mockup in place of a frame) is said in the line before the scoping questions, or in the proposed scope.
