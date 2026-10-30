---
name: sharpen
description: Rewrite a draft prompt so it asks for an expert-depth version of the same task (expert moves, raw sources, named methods, an outside check) without widening scope. Returns the rewritten prompt and does not do the task. Use for "/sharpen <prompt>" or "make this prompt better before I send it".
---

# sharpen

Take the prompt the user is about to send and return a deeper version of it. Depth means the same task done the way the best practitioner would do it. Scope stays the same: do not add features, extra deliverables, or neighbouring problems.

Do not start the task. If the user wants the work done now, do it without this skill. If the user wants to check that you understood them, use the [`in-your-own-words` skill](../in-your-own-words/SKILL.md).

## Steps

1. Answer four questions about the task in the draft, one short paragraph each:
   1. **Expert moves.** What would a top practitioner in this field do here that the draft does not ask for?
   2. **Raw sources.** What primary, unprocessed material would that expert start from, instead of the summaries or second-hand material the draft relies on? For example the source code instead of the docs, the raw logs instead of a dashboard, the specification instead of a blog post, the production data instead of a fixture.
   3. **Methods.** Which concrete methods and tools would that expert apply? Name them.
   4. **Outside check.** What check, independent of your opinion and the user's, would show the result is correct? For example a test that fails before and passes after, a comparison against a reference implementation, a measurement, a second reviewer from outside the work.
2. Rewrite the draft so it asks explicitly for those things. Keep the user's goal, constraints, and voice. Keep it about as short as the work allows: a prompt that names the method and the check is enough, and the agent receiving it will fill in the steps.
3. Leave decisions that belong to the user open in the rewrite, and mark each one, for example "(you decide: keep backward compatibility or not)". Do not settle them on the user's behalf.

## Output

The four answers, then the rewritten prompt in a code block so the user can copy it. Nothing else.
