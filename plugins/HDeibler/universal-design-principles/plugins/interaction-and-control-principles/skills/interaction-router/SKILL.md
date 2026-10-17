---
name: interaction-router
description: 'Use this skill whenever a design task involves what users *can do* and what happens when they do it — affordances, feedback, errors, undo, confirmation, target sizing, keyboard handling, modal vs. non-modal decisions, destructive actions, validation. Trigger when the user mentions buttons, forms, validation, error states, loading states, drag-and-drop, undo, confirmation dialogs, keyboard shortcuts, target sizes, "users keep deleting things," misclicks, or "should this be a popover or a dialog." Framework-agnostic. Routes the model to the right interaction principle in this plugin.'
---

# Interaction & control — router

This plugin holds the principles that govern interaction: what is clickable, what happens when it's clicked, how mistakes are prevented and recovered. They apply to web, mobile, desktop, voice, and physical product interfaces.

## Principles in this plugin

Each principle has its own skill (with sub-aspect skills where useful). Principles marked **[full]** have reference-grade skill files; the rest are planned and will be added in subsequent passes.

### Affordance and target sizing

- **`affordance`** *[full]* — visual and behavioral cues that suggest how an element is used.
  - Sub-skills: `affordance-buttons-vs-links`, `affordance-disabled-states`, `affordance-non-obvious-targets`.
- **`constraint`** — limit interactions to those that are valid in context.
- **`fitts-law`** *[full]* — time to acquire a target depends on its size and distance.
  - Sub-skills: `fitts-law-touch-targets`, `fitts-law-screen-edges`, `fitts-law-pointer-acceleration`.
- **`defensible-space`** — separate destructive controls from common ones.
- **`entry-point`** — the first point of contact must invite engagement.

### Feedback and errors

- **`feedback-loop`** — every action gets a perceptible response.
- **`errors`** — slips (skill failures) vs. mistakes (knowledge failures); design for both.
- **`forgiveness`** — make actions reversible or confirmable.
- **`garbage-in-garbage-out`** — validate at the boundary; don't let bad data flow inward.
- **`cost-benefit`** — don't ask the user to pay for an action whose payoff isn't clear.
- **`convergence`** — design conventions converge over time; deviate only with reason.

### Control and behavior

- **`control`** — users should feel in command of the system, not the reverse.
- **`flexibility-usability-tradeoff`** — every added option harms usability for the simple case.
- **`most-advanced-yet-acceptable`** — push novel only as far as users will tolerate.
- **`performance-vs-preference`** — what users prefer isn't always what makes them effective.
- **`hierarchy-of-needs`** — functionality, reliability, usability, proficiency, creativity (in order).

### Persuasion and behavior shaping

- **`nudge`** — small choice-architecture changes that make the better path easier.
- **`operant-conditioning`** — behavior shaped by reinforcement; use sparingly and honestly.
- **`classical-conditioning`** — emotional associations transfer.
- **`shaping`** — gradually increase task complexity through practice.
- **`expectation-effect`** — users perceive what they expect to perceive.
- **`freeze-flight-fight-forfeit`** — under stress, users default to instinctive responses.
- **`desire-line`** — the path users actually take, often diverging from the planned one.
- **`interference-effects`** — competing stimuli (Stroop) slow processing.

## Heuristic for which to read first

- **Designing buttons/CTAs** → `affordance`, `fitts-law`, `defensible-space`.
- **Designing forms** → `affordance`, `constraint`, `feedback-loop`, `errors`, `forgiveness`.
- **Mobile target sizing** → `fitts-law-touch-targets`.
- **Destructive actions** → `defensible-space`, `forgiveness`, `freeze-flight-fight-forfeit`, `expectation-effect`.
- **Validation and error copy** → `errors`, `forgiveness`, `garbage-in-garbage-out`.
- **Modal vs. non-modal decisions** → `control`, `entry-point`, `interference-effects`.
- **"Should we add this option?"** → `flexibility-usability-tradeoff`, `most-advanced-yet-acceptable`.

## Cross-plugin pointers

- For *visual* layout, hierarchy, and grouping, see `perception-and-hierarchy-principles`.
- For *learnability* (mental models, defaults, recognition), see `cognition-and-learnability-principles`.
- For *aesthetic and tonal* decisions, see `aesthetics-and-emotion-principles`.
- For *accessibility*, see `process-and-robustness-principles`.
