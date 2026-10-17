---
name: control-locus
description: 'Apply locus of control — the design choice between making the system appear to act on the user''s behalf (external locus) and making the user appear to direct the system (internal locus). Use when designing AI-assisted features, autocorrect/autocomplete behaviors, recommendation surfaces, automated workflows, and any feature where the system could either do things automatically or wait for user instruction. Internal locus produces higher engagement, learning, and satisfaction; external locus produces higher convenience but lower agency. The skill is choosing deliberately and explaining the choice in the UI.'
---

# Control — locus

Locus of control is the perception of who is doing the doing. An *internal* locus of control means the user feels they are directing the system; an *external* locus means the user feels the system is directing them. Both can be useful depending on the task — but the choice has psychological consequences that often go unconsidered, especially in automated and AI-assisted features.

A well-designed system makes a deliberate choice about locus, usually shifting it depending on the task: internal for creative or judgment-intensive work, external for routine or expertise-deficient tasks. The same product can have different loci in different surfaces.

## Why locus matters

The psychological evidence is consistent. Users with a stable internal locus of control — across life, not just in software — report higher motivation, persistence, and satisfaction. Users with a stable external locus tend toward passivity and learned helplessness. While these are stable personality traits, *situational* locus is malleable, and software design can push it in either direction.

A product that does things on the user's behalf without asking — autocorrects their typing, autocategorizes their email, auto-generates recommendations — moves the situational locus toward external. Useful in moderation, this becomes problematic when overdone: users feel the product is doing the work and they're just observing. They lose the sense of authorship over the output. They learn less about the underlying system. They have less to point to as their own.

A product that waits for explicit user direction — asks for confirmation before acting, presents options without picking one, requires the user to invoke each capability — moves the locus toward internal. Useful when the user has expertise and judgment, this becomes burdensome when overdone: users feel they're doing all the work and the product is just a passive instrument. They get tired. They make errors that the product could have prevented. They wonder why the product doesn't help more.

The right locus depends on the task and the user, and the choice deserves more attention than it usually gets.

## When external locus is appropriate

External locus — the system acting on the user's behalf — is appropriate when:

**The user lacks the expertise to make the choice well.** Spell-check correcting a misspelled word. Photo software auto-correcting white balance. Email apps grouping conversations into threads. The user can't reliably make these decisions, and the system can. Letting the system act creates value that wouldn't exist otherwise.

**The decision is routine and recurring.** Auto-saving a document. Auto-syncing data. Auto-paying recurring bills. The user has already implicitly authorized the system to handle this category of task; making them confirm each instance would be exhausting.

**The cost of error is low and recovery is easy.** Auto-correcting a typo is fine if the user can immediately re-correct it. Auto-categorizing an expense is fine if it's easy to recategorize. The system can act first because the cost of being wrong is small.

**The user explicitly delegated the task.** "Set up auto-pay for this account" — the user has actively chosen to externalize the locus. The system is now expected to act without asking.

## When internal locus is appropriate

Internal locus — the user directing the system — is appropriate when:

**The user has expertise and the choice expresses their judgment.** A musician choosing which take to keep. A photographer choosing the crop. A writer choosing the phrasing. These are the moments where the user's authorship is the entire point; the system should not pre-empt them.

**The cost of error is high and recovery is hard.** Sending a message to a customer. Deleting a database row. Moving money. The system should not act on the user's behalf for actions that, if wrong, would be expensive to undo. Internal locus here is not just psychological — it's protective.

**The user is learning the system.** A novice exploring a new tool benefits from seeing what each action does, building a mental model. A system that "helps" by doing things automatically prevents that learning from happening. Once expert, the user can tolerate (and welcome) more automation; while learning, more internal locus is better.

**The decision is value-laden or contested.** Recommendations that imply judgment ("you should buy this," "you should follow this person") are stronger when framed as suggestions the user is evaluating rather than as actions the system is taking. The user keeps the locus by deciding; the system supports the decision.

## Designing for locus deliberately

The design choices that shift locus include:

**Action without asking vs. suggestion with confirmation.** "Auto-categorized as 'Travel'" with a small undo affordance vs. "Suggested category: Travel — confirm?" with options. The first is external locus, the second internal.

**Showing what was done vs. asking what to do.** "Removed 47 duplicate rows" vs. "We found 47 likely duplicate rows — review and remove?" Both useful in different contexts.

**Defaults presented as suggestions vs. defaults presented as decisions.** A form pre-filled with values the user can change conveys "we suggest these"; the same form pre-filled with values the user has to actively change conveys "we decided these for you." The design implementations may be similar, but the framing matters.

**Visibility of automated actions.** Actions performed automatically should be visible — at minimum in a log, ideally in the moment they happen. A hidden auto-action is the worst of both worlds: external locus, with no opportunity for the user to notice or learn.

**Granularity of control over automation.** Even when the system acts automatically, the user should be able to disable or tune the automation. A spell-checker the user can't turn off feels imposed; one with a clear settings panel feels delegated.

## Worked examples

### AI writing assistants

An AI writing tool can operate at different loci. A high-external version: the user types a single sentence and the AI writes the rest, presenting it for acceptance. A medium version: the AI suggests a continuation that the user can accept, modify, or reject. A high-internal version: the AI provides on-demand help (rewrite, summarize, brainstorm) only when explicitly invoked.

For users who want speed and don't care about authorship — a busy executive churning out routine emails — high external is fine. For users who care about voice and authorship — a writer working on a novel — high internal is essential. The same tool may need both modes for different users or different moments.

The failure mode: a writing tool that auto-completes aggressively for all users. Users who want the help benefit; users who care about authorship feel their voice being replaced and disengage. The fix is to make the locus a deliberate choice the user controls.

### Autocorrect on mobile keyboards

The classic external-locus feature, useful in most cases — typos are routine, recovery is easy, the user knows the correction is happening — and frustrating when wrong. The keyboard that learns the user's vocabulary and stops correcting their custom terms maintains a productive external locus; the keyboard that insists on correcting your friend's name to a common word every time produces the worst kind of automation surprise.

The lesson: external locus requires the system to be reliably right, or the user feels they're fighting an uncooperative tool.

### Recommendation feeds

A social-media feed that shows recommended content interleaved with content from people you follow shifts locus toward external. Over time, users may feel they're consuming what the algorithm chooses rather than what they chose to follow. Some users like this (effort-free discovery); others resent it (loss of authorship over their attention).

A feed that shows only what the user followed and provides recommendations as a separate, clearly-labeled section maintains an internal locus. The user sees what they chose and explicitly visits the recommended section when they want.

### Rule-based automations

Email rules ("when X arrives, do Y") are a high-internal-locus form of automation: the user wrote the rule, the user understands what will happen, the user can change or disable it. The locus is internal even though the system is acting automatically, because the user is the author of the action.

This is one of the cleanest patterns for combining automation with internal locus: the user delegates explicitly, with clear visibility into what will happen.

### Confirmation dialogs

The classic mechanism for shifting locus toward internal at moments of high stakes. "Delete 47 files? This cannot be undone." The user pauses, decides, confirms. The locus stays internal because the user actively chose, even though the system did the deletion.

The failure mode: confirmation dialogs for everything, including low-stakes actions. The user starts clicking through them without reading, which puts them effectively in external locus (the dialog is now ignored noise) while still imposing the friction. Calibrate confirmation to actual stakes.

## Anti-patterns

**Hidden automation.** The system does things on the user's behalf but doesn't show what or when. The user notices later that something changed and can't trace it back. This is the worst case: external locus with no transparency, eroding trust in the system. Always make automated actions visible.

**Forced choice when the system has a confident answer.** Asking the user to choose between "Delete this draft" and "Keep this draft" when an empty draft has obviously been abandoned. The system has the information to make the call; forcing the user to choose just adds friction. Move to external locus when you can do so accurately.

**Internal-locus theater.** Asking for the user's choice but presenting it in a way that funnels everyone to the same answer (a bright "Recommended" badge on one option, the other options small and gray). The locus appears internal but is actually external — the user's "choice" is the system's choice with extra steps. Either own the decision or actually present it as a real choice.

**Automation that learns the wrong thing.** A system that adapts to user behavior in ways the user can't see or control. The user trains the system inadvertently and is then surprised by what it does. Adaptive automation needs visibility into what the system has learned and easy ways to correct it.

**Oscillating locus.** A product that switches between automatic and manual behavior unpredictably ("usually it does X for you, but sometimes it asks"). Users can't form a stable mental model. Pick a locus per task and stick to it.

## Heuristic checklist

For each automated or semi-automated feature, ask: **What is the locus of control here, and is it appropriate to the user, the task, and the stakes?** If the user lacks expertise and the stakes are low, external is probably right. If the user has expertise and the stakes are high, internal is probably right. **Is the automation visible?** If not, make it so. **Can the user adjust or disable the automation?** If not, build that affordance. **Does the locus match across the surface?** Inconsistent locus within a single product confuses users.

## Related sub-skills

- `control` — parent principle on the level of authority delegated to the user.
- `control-power-vs-simplicity` — sibling skill on layering controls for mixed audiences.
- `forgiveness` — undo and reversibility allow the system to operate at a more external locus safely.
- `feedback-loop` — the mechanism by which automated actions become visible enough to maintain trust.
- `mental-model` — stable locus supports a stable mental model; oscillating locus undermines it.

## See also

- `references/automation-design.md` — patterns for designing automation that maintains appropriate locus.
