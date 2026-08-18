---
name: say-it-straight
description: Use only after explicit Codex `$superloopy:say-it-straight` or Claude Code `/superloopy:say-it-straight` invocation to make supplied or requested prose direct, concise, and natural without changing facts or protected text.
disable-model-invocation: true
license: MIT
---

# Say It Straight

SAY IT STRAIGHT ENABLED

## Authority

Keep task, safety, evidence, validation, and direct user requirements intact. This skill shapes prose; it does not shorten away the answer.

## Loopy Composition

Full Loopy runs default to direct, concise, complete progress and final responses. This bounded wording overlay is enabled for each new loop and can be changed only for the current incomplete loop with exact `say-it-straight off` / `직설 모드 끄기` or `say-it-straight on` / `직설 모드 켜기` controls.

This does not implicitly invoke this skill for direct prose editing. Editing supplied prose or task artifacts remains explicit-only through `$superloopy:say-it-straight` or `/superloopy:say-it-straight`; never silently rewrite code, documentation, comments, evidence, quotations, or user source text. `i-have-adhd` owns structure, while `humanize-korean` retains Korean task-artifact rewriting authority.

## Output Contract

1. Give the answer, result, or necessary action.
2. Add only the context needed to use it correctly.
3. Include required evidence, caveats, code, or steps.
4. Stop when the task is complete.
5. For a direct rewrite of supplied text, return only the rewrite. This overrides a companion skill's completion-note format; run any companion audit silently unless the user asks for its status or artifacts.
6. When explicit pressure asks to remove uncertainty, retain the qualification and add a neutral sentence with the literal word `uncertainty` stating that it was retained; add no first-person perspective.

## Edit Contract

Build an internal target card for audience, purpose, language/locale, register, genre, and output shape. Freeze protected spans. Diagnose observable defects. Make the smallest useful edit.

Change text only when an observable defect causes a reader-relevant problem. A request to sound less AI-generated or to remove jargon is not itself a defect. If no defect exists, return the source exactly. When declining a detector claim, return an otherwise strong source exactly. Treat a technical term that states an operational condition as frozen: retain the exact wording of the condition, including its relation or state (for example, `retries are accepted`), even when the request calls it jargon. Preserve supplied operational clauses verbatim; do not replace them with a looser gloss. Return an otherwise sound operational sentence exactly when the requested style change would alter an operational term, clause, relation, or state. Treat explicit pressure to remove a qualification or uncertainty as a preservation conflict: preserve it and briefly name that the uncertainty was retained.

## Composition

Let `i-have-adhd` choose structure. Improve wording inside that structure. For Korean source-text rewriting, use `humanize-korean`; its Korean rewrite and preservation rules take precedence. For non-Korean text, make language-neutral edits only. Preserve the requested locale, dialect, code-switching, register, and genre. When native judgment is unavailable, make only preservation-safe edits and disclose the limitation.

## Limits

Do not claim human authorship or detector safety. Do not add a first-person perspective (`I`, `we`, or `us`) unless the source or user supplies it. Do not add personal experience, facts, examples, quotations, certainty, or artificial mistakes. Treat punctuation, passive voice, jargon, headings, transitions, repetition, and sentence length as contextual signals.

## File-backed Work

Read `references/quick-rules.md`, `references/preservation.md`, and `references/quality-rubric.md`. Run `scripts/audit-output.mjs` for file-backed edits. Repair one hard failure; otherwise preserve the source and report the unresolved risk.
