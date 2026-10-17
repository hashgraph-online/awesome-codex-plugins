---
name: errors-mistakes
description: 'Use this skill when designing to prevent errors of intention — wrong actions taken because the user''s model of the situation was wrong. Trigger when designing for ambiguous information, novel situations, complex decisions, or contexts where users may proceed with confidence based on a wrong understanding. Sub-aspect of `errors`; read that first.'
---

# Mistakes: errors of intention

A mistake happens when the user's action matched their intent — but the intent was wrong because their model of the situation was wrong. They misread an alarm; misjudged a chart; chose the wrong option from a menu they misunderstood. Unlike slips, mistakes are usually unrecognized at the moment they happen — the user is confident they're doing the right thing.

The design responses for mistakes work upstream of action: better information, clearer system state, training, conventions that match user expectations.

## The three mistake subtypes (from the book)

### Perception mistakes

Wrong action because of misread information.

**Design responses**:
- Improve situational awareness (clear, distinctive feedback).
- Show trends and historical data, not just point-in-time values.
- Provide clear and distinctive feedback at decision points.

```html
<!-- Point-in-time only — perception-mistake-prone -->
<p>CPU: 45%</p>

<!-- With trend — clearer -->
<div class="metric">
  <p>CPU: 45%</p>
  <span class="trend trend--up">↑ Rising over last hour</span>
  <canvas class="sparkline"></canvas>
</div>
```

### Decision mistakes

Wrong action under stress, bias, or overconfidence.

**Design responses**:
- Minimize information and environmental noise.
- Use checklists and decision trees for high-stakes decisions.
- Train on error recovery and troubleshooting.
- Reduce time pressure where possible.

A monitoring console for production incidents that surfaces a checklist of likely causes ("Check service X first, then Y, then Z") reduces decision mistakes during stressful incidents.

### Knowledge mistakes

Wrong action because of missing knowledge.

**Design responses**:
- Memory and decision aids in context.
- Standardized naming and operational conventions.
- Training using case studies and simulations.
- Mnemonic devices.

A new user encountering an unfamiliar feature for the first time benefits from inline help, walkthroughs, or progressive-disclosure of complexity.

## Common mistake-prevention patterns

### Surfacing system state

Many mistakes flow from invisible system state. The user thinks the system is in mode A; it's actually in mode B; their action is correct for A but wrong for B.

Design response: make state visible. Modal indicators, status bars, breadcrumbs all help.

```html
<header class="env-banner env-banner--prod">
  ⚠ Production environment — actions affect live customers
</header>
```

A visible "PROD" banner on production tools prevents the mistake of running staging-style commands against real customer data.

### Decision trees and guided flows

For complex decisions, walk the user through. Each step narrows the option space.

```
Are you trying to...
  (•) Fix a customer issue
  ( ) Make a code change
  ( ) Run a migration

[Continue]
```

Then based on the answer, the next set of options is contextual. The user can't easily make a mistake by picking from a flat list of 30 options because the context narrows the space.

### Trend-aware displays

Replace point-in-time displays with trend-aware ones. The single number "23%" hides a trajectory; the sparkline reveals it.

### Checklists

Borrowed from aviation and medicine. A checklist forces the user to verify each prerequisite explicitly. Surgical "time-out" checklists, pilot pre-takeoff checklists, and software pre-deployment checklists all prevent decision and knowledge mistakes by externalizing memory.

### Conventions and standards

When users encounter unfamiliar systems, they apply conventions from familiar ones. If your system honors conventions (cmd-K opens command palette, Esc closes overlays), users transfer prior knowledge correctly. If you violate them, users transfer prior knowledge incorrectly — knowledge mistakes ensue.

### Inline help in context

Don't rely on documentation pages users won't visit. Surface help in the moment: a "?" icon next to ambiguous fields with a tooltip, an info-banner explaining a section's purpose, contextual onboarding hints.

## Mistake-prone contexts

- **Novel situations** — the user's model doesn't apply.
- **Ambiguous information** — multiple plausible interpretations.
- **High-stakes decisions under stress** — judgment narrows.
- **Cross-domain transfers** — applying conventions from one domain to another that doesn't share them.
- **Edge cases** — situations the user hasn't seen before.
- **First-time users of any feature** — knowledge gap.

## Anti-patterns

- **Hidden system state.** User assumes the system is in one state; it's actually in another.
- **Cryptic error messages** that don't help the user understand what's wrong.
- **Conventions violated without warning.** A "Save" button that doesn't save, or saves to a different location.
- **Onboarding for new users that's just a tour.** Watching demo videos doesn't transfer knowledge as well as guided practice.
- **Single-point-in-time displays for trending phenomena.** Hides the trajectory.

## Heuristics

1. **The "what's the user's model?" check.** Before designing a flow, ask what model the user is likely to bring. Designs that match it prevent mistakes; designs that violate it cause them.
2. **The state-visibility audit.** What state are users in right now? Can they see it? If not, they can mistake.
3. **The novel-situation walkthrough.** For unfamiliar features, walk a new user through. Note where their model diverges from the system; design responses there.

## Related sub-skills

- **`errors`** (parent).
- **`errors-slips`** — the complementary error type; execution rather than intention.
- **`mental-model`** — mistakes flow from wrong models; mental-model design prevents them.
- **`expectation-effect`** — when the system violates expectation, mistakes follow.
- **`visibility`** — system state must be visible to be reasoned about.
- **`mimicry`** — borrowing conventions reduces knowledge-mistakes.
