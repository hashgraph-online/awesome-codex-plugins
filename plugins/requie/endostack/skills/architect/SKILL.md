---
name: architect
description: Settle structure before writing logic. Ground in the current code, get competing design sketches (types, signatures, modules, trust boundaries) through arena, implement against the merged sketch, scrap it on a friction pattern. Use for "architect this", "design X first".
---

# architect

Decide the shape of the code before filling it in. You draft types, signatures, class outlines, and module boundaries with stubbed bodies, get at least two structurally different drafts, merge them, then implement against the merged sketch. If implementation keeps fighting the sketch, you throw it away and design again.

Use it when the user asks, and for any task where coding straight away would commit to a structure before anyone has compared alternatives: new types or module layout that cross a function boundary, ownership moving between modules, new trust boundaries. Skip it for small edits whose structure is obvious. Greenfield work with nothing around it skips only step 1.

Track a todo list with five items: ground, sketch, agree, implement, scrap. Keep "scrap" on the list even when you never need it, marked skipped with the reason.

## 1. Ground

Learn each subsystem that the new code will reach into. For every one, run the [`how` skill](../how/SKILL.md) and produce the architecture explanation it specifies. A list of file names is not understanding.

If the design moves ownership or changes layering, also run the [`why` skill](../why/SKILL.md) on the current structure. The reasons behind today's layout become explicit constraints for the sketch instead of guesses you design around.

Write down, as part of the grounding output:

- Types the new code must interoperate with.
- Callers that must keep working.
- Invariants that cross the boundary you are drawing.
- **Trust boundaries**: every place the new code receives data from outside the process or from a less-trusted component (user input, network, files, queues, other services, model or tool output), and every place it hands data to something that acts on it (database, shell, filesystem, outbound HTTP, a model that can call tools). Note who can control each input.

Skip this step only for fully greenfield work with nothing to integrate.

## 2. Sketch

Run the [`arena` skill](../arena/SKILL.md) with:

- Task: "produce a design sketch" for this change.
- Grounding: the path to your grounding output.
- Runner brief: [references/runner-brief.md](references/runner-brief.md), given to every runner unchanged.
- Runners: the `architect-runners` key from the EndoStack model config (`.endostack/models.toml` wins over `~/.endostack/models.toml`). This replaces arena's own runner list for this call. With no config, use `strong` and `fast`. `inherit` and rejected model names are handled the way arena handles them.

Require at least two candidates that differ in overall structure before you merge, even if the first looks fine. Two variations on one structure do not count. This puts [`principle-exhaust-the-design-space`](../principle-exhaust-the-design-space/SKILL.md) into practice: the first design you see anchors you, and the only cure is a real alternative.

**One model only.** If every runner must use the same model, say so in one line ("Single-model sketch: runners differ by brief, not model."). Give each runner a different structural starting constraint in its brief, for example "organise by data ownership", "organise around the external interface", "minimise the number of modules", so the candidates still diverge.

Screen every candidate against [references/red-flags.md](references/red-flags.md). Design for the contributor who will come next, which is usually an agent: it reads only the files it opens, copies the nearest example, and does the least work that compiles. Prefer the design in which an edit that looks right from inside one file is also right for the whole repository.

Among candidates that pass the screen, compare interface depth. Prefer the one whose public surface is small and simple while hiding the most complexity behind it. A capable interface also shortens call chains, because the capability lives in one place instead of being spread across layers.

Weigh trust boundaries explicitly. Prefer the candidate where untrusted data is parsed into domain types at exactly one place per boundary, where code that holds credentials or performs privileged actions is separated from code that handles untrusted input, and where the privileged surface is smallest. A design that needs authorization checks in many places will miss one.

Arena returns one merged design and a synthesis note. The note becomes the "Synthesis decision" section of the rationale.

Write the sketch and the rationale as described in [references/rationale-template.md](references/rationale-template.md).

## 3. Agree

By default there is no human checkpoint: go on to step 4. Stop and wait for approval only if the user asked to review the design first.

Either way, you may commit the sketch on its own before filling in bodies, per [`principle-foundational-thinking`](../principle-foundational-thinking/SKILL.md). Planned, bounded breakage while bodies are filled in is acceptable under [`principle-outcome-oriented-execution`](../principle-outcome-oriented-execution/SKILL.md).

To stress-test the sketch before coding, run the [`interrogate` skill](../interrogate/SKILL.md) on it. Its security seat reads the trust-boundary section.

Any human objection to the structure, whenever it arrives, is new grounding. Update step 1 and rerun step 2 before writing more code.

## 4. Implement

Replace stubs with code and pseudocode with logic. The sketch is binding. When the code wants something the sketch did not plan for, such as an extra parameter, a new dependency, or a second writer to some state, stop and say so instead of absorbing it. Decide which of three things happened:

1. The sketch was wrong.
2. A requirement was missed.
3. The implementation is doing more than its job.

Record the decision in the rationale's open-questions section if it is not settled.

## 5. Scrap

If implementation keeps hitting friction the sketch cannot absorb, throw the sketch away. Patching a flawed design produces a worse result than redesigning it (see [`principle-redesign-from-first-principles`](../principle-redesign-from-first-principles/SKILL.md) and [`principle-fix-root-causes`](../principle-fix-root-causes/SKILL.md)).

A pattern triggers scrapping. One incident does not. Signs of a pattern:

- The same kind of workaround appears in several unrelated places.
- Many unrelated edge cases each need their own branch.
- Types compile only with escape hatches: untyped values, casts, or optional fields that are always present.
- You want a lock for state the sketch declared unshared.
- Callers must understand the abstraction's internals to use it.
- Authorization or input validation has to be repeated at several call sites because the boundary sits in the wrong place.
- Two or more separate step 4 deviations have the same shape.

Use judgment. Some problems are complicated, and complicated data does not by itself mean a complicated design.

To scrap: run `how` again on what now exists, design again on the assumption that the new constraints existed on day one, and remove things before adding any so the new sketch starts smaller than the old one ([`principle-subtract-before-you-add`](../principle-subtract-before-you-add/SKILL.md)). Then return to step 2.

## Done when

The code is complete against an agreed sketch with every deviation raised, or the sketch was scrapped on a friction pattern and the process restarted from step 2.

## Related

- The [`correct` skill](../correct/SKILL.md) uses the same model of the next contributor and overlapping red flags, applied to an existing repository.
- The [`threat-model` skill](../threat-model/SKILL.md) goes deeper on the trust boundaries this skill records.
- The [`setup-endostack` skill](../setup-endostack/SKILL.md) writes the runner list.
