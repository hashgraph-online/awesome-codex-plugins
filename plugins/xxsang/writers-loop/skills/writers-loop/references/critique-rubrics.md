# Critique Rubrics

Use the rubric that matches the artifact. Keep critique specific and tied to
revision proposals.

## Universal Rubric

Check every substantial artifact for:

- Purpose: Does the text serve the stated goal?
- Audience fit: Does it match the reader's context and expectations?
- Structure: Is the order easy to follow?
- Specificity: Are claims, steps, or scenes concrete enough?
- Completeness: Are important requirements or constraints missing?
- Coherence: Do sections support each other without contradiction?
- Style: Does tone match the task?
- Actionability: Does the reader know what to do next?

## Coding Plan Rubric

- Can an engineer execute it without hidden context?
- Are files, interfaces, tests, and commands concrete?
- Does each task have one clear responsibility?
- Are risky migrations or shared contracts isolated?
- Is verification proportional to risk?
- Are placeholders and vague steps removed?

Specific critique example:
> "Tasks 3 and 5 both modify `session.ts` without assigning ownership — one
> team will block the other. Assign one task to own the interface change."

Generic critique to avoid:
> "Are file boundaries clear?"

## Report Rubric

- Is the conclusion visible early?
- Are findings separated from interpretation?
- Is evidence strong enough for the recommendation?
- Are assumptions and uncertainty named?
- Are tradeoffs explicit?
- Are next steps concrete?

Specific critique example:
> "The recommendation appears on page 3. A senior reader skimming this will not
> act. Move the recommendation to the first paragraph; keep the supporting
> evidence where it is."

Generic critique to avoid:
> "Consider leading with the conclusion."

## Proposal Rubric

- Is the ask explicit?
- Is the benefit credible and specific?
- Are costs and risks honestly represented?
- Are objections anticipated?
- Is the implementation path believable?
- Does the close make the decision easy?

## Documentation Rubric

- Can the target user complete the task?
- Are prerequisites clear?
- Does the first example work as written?
- Are edge cases and failures explained where useful?
- Is reference detail separated from the main path?
- Is terminology consistent?

## Design Doc Rubric

- Are goals and non-goals explicit?
- Does the design solve the stated problem?
- Are alternatives and tradeoffs covered?
- Are failure modes named?
- Are rollout and validation paths realistic?
- Are open questions separated from decisions?

## Fiction Rubric

- Does every scene have a purpose?
- Are character choices motivated?
- Does tension escalate?
- Is POV stable unless intentionally shifted?
- Are continuity facts respected?
- Does prose style match the desired tone?
- Does the ending create the intended effect?

Specific critique example:
> "The framing says 'quiet, tense.' Paragraph 4 opens with 'The air hung heavy
> with dread' — the stated feeling, told outright. Replace with an observable
> detail that creates the same tension without naming it."

Generic critique to avoid:
> "The prose style doesn't fully match the desired tone."

For emotional or personal writing (memoir, personal essay, grief writing), apply
this rubric carefully. "Specificity" and emotional truth can be in tension: a
vague sentence may be intentional restraint, not a weakness. Flag it as a
candidate for discussion rather than a required fix.

## Revision Proposal Format

Use this format for targeted changes:

```text
Change: [short label]
Change size: [sentence | paragraph | section | scene | whole artifact]
Location: [quote or describe the target]
Revision: [replacement or instruction]
Reason: [why this improves the artifact]
Risk: [what might be lost or changed]
Decision: apply | reject | adjust | unresolved
```
