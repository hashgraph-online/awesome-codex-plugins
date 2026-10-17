---
name: writers-loop
description: Use when working on substantial writing artifacts where structure, audience fit, critique, revision, translation, style learning, or decision-backed preference learning matters; also when learning reusable writing style from the user's own writing or permitted reference samples.
---

# Writer's Loop

## Core Rule

Extract preferences only from explicit user decisions:
- Approved or rejected plans
- Accepted, rejected, or undone edits
- Manual rewrites that change style, voice, or structure (not fact corrections)
- Explicit standing preferences declared by the user

Never extract preferences from unreviewed drafts, one-off comments, fact
corrections, or current-task constraints.
Learn from decisions, not raw drafts.

## When to Use

Use for writing where quality depends on structure, audience fit, correctness,
style, or iteration — typically 300+ words or any writing where feedback and
refinement are expected:

- Coding plans, implementation plans, and technical proposals
- Business reports, research summaries, executive updates, and memos
- Product specs, design docs, documentation, and tutorials
- Fiction chapters, essays, scripts, speeches, and narrative outlines
- Poetry (limited support — use custom rubric; see `references/artifact-types.md`)
- Academic papers and whitepapers (limited support — adapt to venue requirements)
- Brand-governed or legally constrained writing (legal, clinical, regulatory, corporate)
- Style learning or style distillation from the user's own writing, permitted reference samples, files, pasted text, chapters, reports, docs, or codebase prose
- Translation where meaning, source-language writing style, voice, rhythm, formatting, terminology, or cultural effect matters

Do not use for tiny one-off text edits unless the user asks for a reusable
process or preference learning.

## Core Loop

Follow the loop in order. Do not emit a later-stage section before its gate
has passed:

1. **Frame**: Identify artifact type, audience, purpose, constraints, success criteria, and desired tone.
2. **Question Gate**: Ask only blocking questions. If context is enough, state assumptions and continue.
3. **Plan**: Create the outline, argument, task sequence, scene plan, or section structure before drafting.
4. **Plan Checkpoint**: Stop and wait for the user to approve or request changes before drafting.
   ⚠ Do not draft before approval. Exception: fast draft path (see Entry Modes).
5. **Replan**: If the plan is rejected, revise only the criticized parts, reissue the full plan, and ask again.
6. **Draft**: Write from the approved plan. Preserve declared constraints.
7. **Critique**: Evaluate against the artifact-specific rubric. Every critique must point to a specific location and name a concrete problem — not a generic observation.
8. **Propose**: Suggest targeted revisions with reason and expected improvement. Stop and wait for the user's decision on each.
   ⚠ Do not apply changes before the user responds.
9. **Decide**: Record the user's apply, reject, or adjust response. Do not skip this step — preference learning depends on explicit decisions.
10. **Revise**: Apply accepted changes. Keep rejected changes out.
11. **Evaluate**: Check the revised artifact against the original success criteria.
12. **Learn**: Extract preference signals from decisions collected above. Record the signal type, applies-to scope, and evidence.
13. **Distill**: Promote repeated, high-confidence patterns into reusable rules.
14. **Reuse**: Apply stable rules in later tasks, scoped to artifact type and stage.

## Entry Modes

- **New artifact**: start at `Frame`, then `Question Gate`, then `Plan`.
- **Fast draft** (questions waived): Frame → state Assumptions → compact inline Plan → Draft → Learning Status. Use only when the user clearly waives questions and asks for an immediate draft. Do not use this path when the user asks to bypass, ignore, or override a known plan checkpoint; in that case, present the plan and stop at `PLAN CHECKPOINT`. Skipped questions are weak signals and will not become preferences.
- **Multi-agent**: default to single-agent. Use multi-agent only for high-stakes, long, ambiguous, or multi-audience artifacts where independent planning or critique would materially improve quality. Read `references/multi-agent.md` first.
- **Existing draft**: start at `Frame`, then `Critique`; plan only if structure is unclear. If source text is missing or placeholder-only, ask for it and use this wording: "preserve user intent, voice, plot facts, and continuity."
- **Targeted revision**: start at `Frame`, then `Propose`; keep changes at sentence or paragraph level unless the user explicitly asked for section-scale changes.
- **Style learning**: start at `Frame`, then read `references/style-distillation.md`. Output `Frame`, `Style Versus Content`, `Style Pack`, and `Storage Decision`. If the user wants to clone another person's style, confirm permission or keep the pack session-only.
- **Using a learned style**: before asking artifact questions or drafting, load the style pack from the conversation or from `.writers-loop/styles/` only when the user opted into local storage. State which pack is loaded. Draft with it, then critique content quality and style match separately. Do not copy source passages or facts from the style pack evidence. If the style pack is missing, unavailable, or the user says not to load it first, use the missing-style-pack template in `references/style-distillation.md` exactly, including `Style Pack Status`, `Content Plan`, and `Style Application Plan`. Do not draft and do not output `QUESTION GATE` or general artifact questions yet.
- **Translation**: start at `Frame`, then read `references/translation.md`. Output `Frame`, `Translation`, `Review`, and `Learning Status`; preserve source formatting inside the `Translation` section, not by omitting the loop metadata.
- **Preference update**: start at `Learn`. For storage-mode requests, confirm whether `.writers-loop/`, `journal.jsonl`, `prefs.md`, or style packs will be created before asking artifact questions. Treat tone, length, detail level, or storage mode set for the current task as a constraint, not a learned preference, unless the user says it applies in future work.

## Planning Gates

Ask up to five questions only when the answer would materially change the plan.
If the user skips questions, state working assumptions and continue. Skipped
questions are weak or neutral signals, not strong preferences.

Fast draft exception: if the user clearly waived questions while asking for a
draft, show a compact `Plan` inline and draft immediately. Do not pause for plan
approval. End with `Learning Status`.

Checkpoint pressure override: if the user asks to bypass, ignore, or override a
known plan checkpoint, the checkpoint still applies. Output a plan, explain that
fast draft only waives blocking questions, then stop at `PLAN CHECKPOINT`.

After presenting a plan in the standard path, output the checkpoint format
(see `references/checkpoints.md`) and wait. Do not draft until the user
replies. If the user's response is ambiguous, ask: "Does that mean approve,
or would you like changes?"

## Constraint vs. Preference

A constraint applies to one artifact ("for this memo, use short sentences").
A preference applies to future artifacts ("I always prefer short sentences in memos").
Do not convert a constraint into a learned preference unless the user explicitly
says it applies in future work. When unsure, ask.

If the current request conflicts with an older preference, output `Preference
Handling`: say that the current explicit instruction wins for this task, keep
the older preference scoped, and do not archive it without repeated
contradictory evidence.

## Signal Rules

Extract preferences only from:
- Approved plans (`plan_approved`)
- Rejected plans with reasons (`plan_revision_requested`)
- Accepted edits (`proposal_applied`)
- Rejected edits (`proposal_rejected`)
- Undone edits (`proposal_undone`)
- Manual rewrites that change style, voice, or structure (`manual_rewrite`)
- Explicit standing preferences (`preference_declared`)

Discard for preference learning:
- Unreviewed drafts
- Model-generated text that was never reviewed
- One-off style comments or ambiguous praise
- Fact, date, citation, or domain corrections
- Current-task constraints ("this time", "for this memo", storage mode, tone,
  length, or detail level) unless the user says it is a standing preference

## Distillation Rules

Promote a pattern into a reusable rule only when:
- It repeats across at least two meaningful decisions, or the user explicitly declared it
- It is specific enough to guide future output
- It is not contradicted by more recent or stronger evidence

Format:
```text
Rule: [short imperative instruction]
Applies to: [artifact-type/stage, e.g. coding-plan/planning or report/critique]
Evidence: [accepted/rejected/manual decision summary]
Confidence: low | medium | high
```

Apply only `medium` or `high` confidence rules without asking. Ask before
applying `low` confidence rules. Do not promote a single current-task
constraint into `Learned Preferences`.

## Reference Loading

Load only the references needed for the current task. State which reference
you are reading before using it. If the artifact type is not found in a
reference, use the Universal Rubric and ask if it is sufficient — do not invent
rules not in the file.

- `references/artifact-types.md`: routing index for artifact-specific references
- `references/technical-writing.md`: coding plans, technical docs, design docs, and product specs
- `references/business-writing.md`: reports, memos, proposals, academic/whitepaper, and constrained writing
- `references/fiction-narrative.md`: fiction, narrative, essays, speeches, and poetry
- `references/critique-rubrics.md`: artifact-specific critique criteria
- `references/preference-signals.md`: signal examples and weighting guidance
- `references/checkpoints.md`: checkpoint formats for question, plan, proposal, and close
- `references/style-distillation.md`: learning reusable style packs from samples
- `references/translation.md`: translating while preserving source style
- `references/multi-agent.md`: optional multi-agent workflow
- `references/preference-journal.md`: optional durable journal format
- `references/validation-scenarios.md`: pressure tests for validating this skill

Release validation includes `tools/validate-skill.mjs` through `npm run validate`.

## Optional Tool

Use bundled scripts only when the user opts into durable local preferences or
durable local style packs:

- `scripts/journal.mjs`: initialize `.writers-loop/`, append decision events, and derive `prefs.md`.
- `scripts/style-pack.mjs`: initialize `.writers-loop/styles/`, save reviewed style packs, list saved style packs, and show a selected style pack.

## Common Mistakes

- Drafting before framing audience and success criteria
- Using multi-agent by default for ordinary tasks
- Applying broad rewrites when targeted edits preserve intent better
- Treating a single accepted edit as a permanent global rule
- Converting "this time" or session-only storage into a durable preference
- Reusing fiction style preferences in coding plans or reports without evidence
- Loading a style pack without stating which one is loaded
- Judging only content quality when a style-match review is also required
- Treating a fact-correction rewrite as a style preference signal
- Copying source passages or content facts into a reusable style pack
- Flattening source-language voice or rhythm into generic target-language prose
- Translating code, commands, file paths, URLs, or IDs
