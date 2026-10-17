---
name: cognition-router
description: 'Use this skill whenever a design task involves cognition, mental models, learnability, complexity reduction, defaults, memory, scanning, or comprehension — regardless of framework or platform. Trigger when the user is designing forms, settings, onboarding, dashboards with many widgets, complex tables, navigation IA, search experiences, or any flow that has many options or asks the user to learn something new. Trigger when the user mentions "too complex," "too many options," "users keep getting confused," defaults, labels, copy, mental models, progressive disclosure, autocomplete, or ergonomics. Routes the model to the right cognition principle in this plugin.'
---

# Cognition & learnability — router

This plugin holds the principles that govern how easily a user can understand, learn, and remember an interface. They are framework-agnostic and apply equally to web apps, mobile apps, desktop software, control panels, in-car displays, and printed forms.

## Principles in this plugin

Each principle has its own skill (with sub-aspect skills where useful). Principles marked **[full]** have reference-grade skill files; the rest are planned and will be added in subsequent passes.

### Complexity reduction

- **`hicks-law`** *[full]* — decision time grows with the log of the number of options.
  - Sub-skills: `hicks-law-menus`, `hicks-law-defaults`, `hicks-law-pricing`.
- **`80-20-rule`** — 80% of usage flows through 20% of features; design the default for the 80%.
- **`chunking`** — group items into ~4±1 chunks so working memory can hold them.
- **`performance-load`** — total cognitive + kinesthetic effort to do a task; minimize both.
- **`progressive-disclosure`** — show only what's needed now; reveal advanced controls on demand.
- **`satisficing`** — users pick the first acceptable option, not the optimal one.
- **`ockhams-razor`** — among solutions that work, prefer the simplest.

### Mental models and recognition

- **`mental-model`** — users come with a model of how the system works; design to match it.
- **`recognition-over-recall`** — recognizing is easier than remembering; show options.
- **`visibility`** — features that aren't visible aren't used.
- **`mapping`** — controls map onto what they affect.
- **`constancy`** — visual properties remain stable across state changes.
- **`iconic-representation`** — pictures are recognized faster than words but only when conventional.
- **`mimicry`** — borrow successful familiar patterns rather than invent.
- **`rosetta-stone`** — pair a known referent with a novel concept.

### Chunking, scanning, and memory

- **`inverted-pyramid`** — most important info first, then supporting detail.
- **`five-hat-racks`** — five ways to organize: Location, Alphabet, Time, Category, Hierarchy.
- **`advance-organizer`** — a structural preview before content (TOC, breadcrumbs).
- **`serial-position-effects`** — first and last items are remembered best.
- **`stickiness`** — memorable, concrete content earns repeat use.
- **`storytelling`** — narrative encodes meaning more memorably than bullets.
- **`picture-superiority-effect`** — images outlast text in memory.
- **`mnemonic-device`** — explicit memory aids reduce recall cost.
- **`propositional-density`** — meaning per visible mark; high density reads as polished.

### Wayfinding and navigation

- **`wayfinding`** *[full]* — orienting, choosing routes, monitoring progress, recognizing destinations.
  - Sub-skills: `wayfinding-physical-spatial-metaphors`, `wayfinding-search-and-recovery`, `wayfinding-breadcrumbs-and-context`.
- **`progressive-disclosure`** *[full]* — show what's needed now; tuck the rest behind explicit affordances.
  - Sub-skills: `progressive-disclosure-defaults-and-tucking`, `progressive-disclosure-disclosure-affordances`.

### Consistency and encoding

- **`consistency`** — same things look and behave the same.
- **`cognitive-dissonance`** — contradictions between expectation and behavior cost trust.
- **`confirmation-bias`** — users notice what confirms their model and ignore what doesn't.
- **`comparison`** — comparison is easier than evaluation.
- **`depth-of-processing`** — interactive engagement yields better memory than passive reading.
- **`priming`** — exposure shapes how a subsequent stimulus is processed.
- **`framing`** — how information is framed changes the choice users make.
- **`modularity`** — break complex systems into independent, recombinable units.
- **`redundancy`** — multiple independent signals make critical info reliable.

## Heuristic for which to read first

- **Designing a long form or settings page** → `chunking`, `progressive-disclosure`, `hicks-law`, `mental-model`.
- **Picking defaults** → `satisficing`, `80-20-rule`, `hicks-law-defaults`, `framing`.
- **Picking an icon set** → `iconic-representation`, `recognition-over-recall`, `mimicry`.
- **Designing a dashboard** → `propositional-density`, `chunking`, `inverted-pyramid`.
- **Onboarding** → `mental-model`, `advance-organizer`, `depth-of-processing`, `storytelling`.
- **Search / navigation IA** → `wayfinding`, `recognition-over-recall`, `five-hat-racks`, `visibility`.
- **"Users keep getting lost"** → `wayfinding`, `wayfinding-breadcrumbs-and-context`, `wayfinding-search-and-recovery`.
- **Settings / forms feel overwhelming** → `progressive-disclosure`, `chunking`, `hicks-law`.
- **Reviewing a confusing flow** → `mental-model`, `cognitive-dissonance`, `consistency`.

## Cross-plugin pointers

- For *visual* layout and grouping, see `perception-and-hierarchy-principles`.
- For *behavior* (errors, undo, target sizing, feedback), see `interaction-and-control-principles`.
- For *aesthetic and tonal* decisions, see `aesthetics-and-emotion-principles`.
- For *accessibility*, see `process-and-robustness-principles`.
