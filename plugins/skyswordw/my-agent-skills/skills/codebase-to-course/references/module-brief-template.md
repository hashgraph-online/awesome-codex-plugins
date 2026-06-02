# Module Brief Template

Use this template for complex codebases before writing lesson modules. Save one brief per planned module under `briefs/`.

## Module Identity

- Module title:
- Output filename: `modules/<slug>.html`
- Root section id:
- Optional `data-title` navigation label:
- Audience promise:
- Why this module exists:

## Module HTML Contract

- Author exactly one root `<section id="...">` per module file.
- Put the module title in `data-title` when the navigation label should differ from the visible heading.
- If `data-title` is omitted, make sure the first heading in the module gives the correct navigation label.
- Do not add extra `<link>` tags or extra `<script>` includes in the module file.
- Prefer shipped runtime widgets when available. If no shipped widget fits, fall back to static or minimal local HTML/CSS/JS patterns that remain offline-readable without introducing extra asset includes.

## Source Scope

- Primary files or directories:
- Entry file to anchor the lesson:
- Related files worth mentioning:
- Files to ignore for this module:

## Learner Questions

- Main question this module answers:
- Two or three supporting questions:
- What the learner should already know before starting:

## Evidence Plan

- Short excerpt candidates:
- Diagrams or visual structures to include:
- Config, permissions, or environment details that matter:
- Terms that need plain-language translation:

## Interaction Plan

Choose only the interaction patterns that sharpen the lesson, and note whether each one uses a shipped runtime widget or a static/local fallback:

- translation block
- quiz
- drag/drop
- group chat
- data flow
- architecture diagram
- layer toggle
- bug challenge
- scenario quiz
- callout
- pattern card
- flow diagram
- permission/config badge
- glossary tooltip
- visual file tree
- icon-label row
- numbered step card

## Story Order

1. Opening scene or user-visible behavior
2. Key moving parts
3. Where the data or control flow goes
4. Code evidence and translation
5. Practical takeaway

## Safety And Scope Checks

- Are all examples public-safe and sanitized?
- Are excerpt plans short enough to avoid file dumping?
- Is anything sensitive better explained than quoted?
- Is the lesson focused, or is it trying to cover too much?

## Done When

- The learner can explain this module's core idea in plain language.
- The module points to real files without overwhelming the learner.
- The next module has a clear handoff.
