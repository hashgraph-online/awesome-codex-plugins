# Content Philosophy

The course is for someone who can follow cause and effect but does not already think like a maintainer. Teach the codebase as a practical system, not as a directory inventory.

## What The Learner Should Get

Each module should help the learner answer three plain questions:

1. What part of the product or workflow are we looking at?
2. Why does this piece matter?
3. Where in the code can I see the evidence?

If a section does not improve one of those answers, cut it.

## Start With Visible Behavior

Open with the user-facing or operator-facing effect before you zoom into implementation. Good starting points include:

- a request entering the system
- a button triggering a result
- a document being transformed
- a job moving through stages
- a configuration switch changing behavior

The learner should understand the outer story before they meet internal abstractions.

## Use Code As Evidence

Code excerpts are proof, not wallpaper.

- Quote only the lines needed to support the teaching point.
- Keep the excerpt short enough that the learner can hold it in memory.
- Translate the excerpt into plain language immediately after showing it.
- Prefer one strong excerpt over five weak ones.

When a file is important but the exact source text is not, summarize the file's job instead of quoting it.

## Make Jargon Earn Its Place

Introduce specialist terms only after the learner has a mental picture. A good pattern is:

1. describe the job in everyday language
2. name the engineering term
3. reuse the term consistently from then on

This keeps the course approachable without becoming vague.

## Favor Orientation Over Exhaustion

The learner does not need every helper, branch, or utility. They need the landmarks that make the rest of the codebase navigable:

- entry points
- core state or data models
- important boundaries between layers
- permissions, config, or environment switches
- the files where behavior changes are most likely to happen

Show how the system hangs together before you enumerate internals.

## Interactions Must Teach Something

Interactive pieces are useful when they help the learner test or manipulate a concept:

- translation blocks help decode dense code or config
- drag and drop helps sequence events or responsibilities
- scenario quizzes help check whether the learner can predict behavior
- layer toggles help compare abstraction levels
- glossary tooltips reduce interruption without hiding meaning

Avoid decorative interactions that do not deepen understanding.

## End With Confidence

A good module closes by lowering the learner's next-step friction. End with a short recap and a clear statement of what they can inspect next. The reader should feel more oriented than impressed.
