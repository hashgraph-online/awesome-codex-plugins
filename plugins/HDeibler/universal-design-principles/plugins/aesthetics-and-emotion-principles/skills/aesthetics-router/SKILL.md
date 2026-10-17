---
name: aesthetics-router
description: 'Use this skill whenever a design task involves the felt quality of an interface — beauty, polish, brand voice, persuasion, emotional response, marketing surfaces, hero sections, onboarding tone, empty/celebration states, illustrations, mascots, avatars. Trigger when the user mentions tone, polish, brand, "feels cold/cheap/premium," personality, voice, mascot, hero, "make it more delightful," or asks how a screen should make the user feel. Framework-agnostic. Routes the model to the right aesthetics principle in this plugin.'
---

# Aesthetics & emotion — router

This plugin holds the principles that govern how an interface *feels* — beautiful, premium, friendly, trustworthy, alarming. They matter most on expressive surfaces (marketing, brand, onboarding) and least on instrumental surfaces (data tables, settings).

## Principles in this plugin

Each principle has its own skill (with sub-aspect skills where useful). Principles marked **[full]** have reference-grade skill files; the rest are planned and will be added in subsequent passes.

### Perceived quality

- **`aesthetic-usability-effect`** — beautiful designs are perceived as more usable.
- **`form-follows-function`** — form should derive from function; gratuitous decoration costs trust.
- **`wabi-sabi`** — beauty in imperfection, asymmetry, transience.
- **`veblen-effect`** — desirability that increases with price.
- **`most-average-facial-appearance-effect`** — average faces are perceived as attractive.

### Personality and tone

- **`archetypes`** — recurring character patterns inform brand voice.
- **`anthropomorphic-form`** — humanlike features evoke warmth.
- **`baby-face-bias`** — round, big-eyed forms evoke trust and protectiveness.
- **`attractiveness-bias`** — attractive subjects credited with unrelated positive traits.
- **`phonetic-symbolism`** — sounds carry inherent connotations (sharp/soft, fast/slow).
- **`personas`** — fictional users that anchor design decisions to a coherent audience.

### Persuasion and emotional pull

- **`exposure-effect`** — repeated exposure increases preference.
- **`scarcity`** — perceived scarcity increases desirability.
- **`supernormal-stimulus`** — exaggerated cues that out-compete natural ones.
- **`immersion`** — flow state, distraction-free, full-attention.

### Evolutionary biases

- **`biophilia-effect`** — affinity for living things and natural patterns.
- **`savanna-preference`** — preference for open landscapes with scattered cover.
- **`prospect-refuge`** — preference for vantage points that allow seeing without being seen.
- **`hunter-nurturer-fixations`** — gendered attention patterns (controversial).
- **`face-ism-ratio`** — ratio of head to body shifts perceived authority vs. emotion.
- **`waist-to-hip-ratio`** — body-shape bias in portraiture.
- **`uncanny-valley`** — near-human faces that fail "human" cues evoke revulsion.

## Heuristic for which to read first

- **Designing a marketing landing page** → `aesthetic-usability-effect`, `archetypes`, `exposure-effect`.
- **Choosing a brand voice** → `archetypes`, `phonetic-symbolism`, `anthropomorphic-form`.
- **Designing a mascot or avatar** → `anthropomorphic-form`, `baby-face-bias`, `uncanny-valley`, `most-average-facial-appearance-effect`.
- **Premium tier marketing** → `veblen-effect`, `aesthetic-usability-effect`.
- **Onboarding tone** → `archetypes`, `storytelling` (cognition), `aesthetic-usability-effect`.
- **Empty / celebration states** → `wabi-sabi`, `anthropomorphic-form`.

## Cross-plugin pointers

- For *visual* hierarchy and grouping, see `perception-and-hierarchy-principles`.
- For *learnability*, see `cognition-and-learnability-principles`.
- For *behavior*, see `interaction-and-control-principles`.
- For *accessibility*, see `process-and-robustness-principles`.
