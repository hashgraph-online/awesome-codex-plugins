---
name: interrogate
description: Adversarial multi-model review of a diff or branch. Several read-only reviewers, plus a security seat, try to break the change; you sort every finding into act on, consider, noted, or dismissed. Use for "interrogate this", "tear this apart", "stress-test my branch". Reports only, never fixes.
---

# interrogate

Several reviewers attack the same change independently, and you act as lead reviewer over what they return. The pressure comes from reviewers that think differently: different model families when the agent offers them, different briefs and stances when it does not. One extra seat always reviews from the attacker's side. You never edit code in this skill. The output is a verdict the user acts on.

Run it only when the user asks. Two cases belong elsewhere. If the user wants fixes applied, finish the verdict and let them choose what to act on. If the worry is what the change breaks outside its own lines, use the [`blast-radius` skill](../blast-radius/SKILL.md). Do not interrogate an abstract plan that has no code yet: reviewers of a plan invent risks because nothing constrains them. A prototype answers a design question better than a review panel does.

## Steps

Track a todo list with these six items: scope, intent, launch, merge, judge, report.

### 1. Scope

Pick what to review in this order, stopping at the first that applies:

1. Files or a diff the user named.
2. The current branch against its base: run a shell command for the three-dot diff (`git diff <base>...HEAD`) so commits already on the base are excluded.
3. The files tied to the recent work the user mentions.

Bundle the changed code with the neighbouring files a reader needs: callers of changed functions, the types they use, the tests that cover them, and any config the change reads.

### 2. Intent

Write one paragraph on the purpose of the change. Your sources are what the user said, the commit messages, any PR description, and the code itself. Ask the user before launching reviewers if those sources leave the intent unclear. Reviewers will be told to accept this intent as given and attack only the execution, so a wrong intent paragraph wastes the whole panel.

### 3. Launch the panel

Read the `interrogate-reviewers` key from the EndoStack model config (`.endostack/models.toml` in the project, which wins key by key over `~/.endostack/models.toml`). Each entry in the list is one reviewer seat, labelled A, B, C in order. With no config, use two seats: `strong` and `fast`. An `inherit` (or `auto`) entry runs on the session's model and still counts as a seat.

Add one more seat, labelled S, for the security reviewer. It runs on the `judgment` role (default `strong`). Its brief adds the security stance in [references/reviewer-brief.md](references/reviewer-brief.md).

Spawn every seat as a read-only subagent in one parallel batch. Each gets the same brief, built from [references/reviewer-brief.md](references/reviewer-brief.md) and filled with the intent paragraph, the bundled code, the full rubric in [references/rubric.md](references/rubric.md), and the full quality lens in [references/quality-lens.md](references/quality-lens.md). If the agent passes a reasoning-effort setting, use the one that matches the config's `budget`.

**Model problems never block the review.** If the agent rejects a configured model name, run that seat on its default tier and tell the user in one line. If a tier itself cannot be resolved, use the closest model the agent's error lists and note it. Never treat `inherit` as a rejected name.

**One model only.** If the agent cannot choose a model per subagent, or only one model is available, say so in one line ("Single-model panel: reviewers differ by stance, not model."). Then give each seat a different stance from the list in [references/reviewer-brief.md](references/reviewer-brief.md) so the seats look for different failures. Weigh agreement between seats lower than you would agreement between model families, because the same model shares the same blind spots.

### 4. Merge

As results arrive, parse each finding. Combine findings that describe the same defect in different words and record which seats raised each one. A finding raised independently by two or more seats on different models is the strongest signal you will get. Read single-seat findings in full but weigh them lower, except for correctness and security findings, which get full scrutiny even from one seat. Record direct disagreements, especially where one seat claims the opposite of another.

### 5. Judge

Act as the lead reviewer using [references/lead-judgment.md](references/lead-judgment.md). You have more context than the reviewers, so trace call sites before accepting a hypothetical input problem. Sort each finding into one bucket only, and record next to it which seats reported it plus a single-line justification:

- **Act on**: a real correctness, security, or maintainability defect given the stated intent, serious enough to hold the merge.
- **Consider**: valid, but the fix may not be worth its cost now. The user decides.
- **Noted**: true but not actionable now, for example context-dependent or low impact.
- **Dismissed**: wrong, a nitpick, or caused by missing context, with the reason.

### 6. Report

Reply in this order:

1. The intent paragraph, quoted.
2. The roster: one line per seat with its model (or stance, on a single-model panel) and its finding count.
3. Act on: each finding with location, the seats behind it, and why it matters.
4. Consider: each finding with the seats behind it and the tradeoff.
5. Noted: a short list.
6. Dismissed: each finding with its reason. Tell the user to read this section, since a wrong dismissal is the most expensive mistake a lead reviewer makes.
7. Agreement map: where the seats agreed, where they split, and what the split suggests.

Do not edit code, commit, or post review comments.

## Done when

Every finding from every seat sits in exactly one bucket with attribution and a reason, and the report is delivered.

## Related

- The [`tarique-mode` skill](../tarique-mode/SKILL.md) can call this skill as a review step.
- The [`architect` skill](../architect/SKILL.md) can run it on a design sketch before coding starts.
- The [`setup-endostack` skill](../setup-endostack/SKILL.md) writes the reviewer roster.
- The rubric draws on [`principle-boundary-discipline`](../principle-boundary-discipline/SKILL.md), [`principle-fix-root-causes`](../principle-fix-root-causes/SKILL.md), [`principle-make-operations-idempotent`](../principle-make-operations-idempotent/SKILL.md), [`principle-separate-before-serializing-shared-state`](../principle-separate-before-serializing-shared-state/SKILL.md), [`principle-prove-it-works`](../principle-prove-it-works/SKILL.md), [`principle-encode-lessons-in-structure`](../principle-encode-lessons-in-structure/SKILL.md), [`principle-migrate-callers-then-delete-legacy-apis`](../principle-migrate-callers-then-delete-legacy-apis/SKILL.md), [`principle-subtract-before-you-add`](../principle-subtract-before-you-add/SKILL.md), and [`principle-treat-input-as-untrusted`](../principle-treat-input-as-untrusted/SKILL.md).
