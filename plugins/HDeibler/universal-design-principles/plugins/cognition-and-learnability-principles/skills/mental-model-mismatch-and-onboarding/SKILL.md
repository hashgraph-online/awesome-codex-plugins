---
name: mental-model-mismatch-and-onboarding
description: 'Use this skill when designing onboarding, when diagnosing why users keep getting confused, when migrating users from one product convention to another, or when the system genuinely differs from familiar comparable products. Trigger when the user mentions "users don''t get it," "we keep getting the same support tickets," or "this is a new pattern they need to learn." Sub-aspect of `mental-model`; read that first.'
---

# Mental-model mismatches and onboarding

When the user's mental model and the system's actual behavior diverge, three things can be done: change the system to match the user's model; change the user's model through onboarding and teaching; or surface the divergence so the user knows when their model doesn't apply.

## Diagnosing mismatches

Common signals of mental-model mismatch:

- **Repeated support tickets** about the same misunderstanding ("Why doesn't X work?" when X works fine — the user's expectation didn't match).
- **Drop-off at the same flow step** (the user reached this step expecting one thing; got another; left).
- **High undo / cancel rate** at a particular action.
- **Forum / community questions** asking how to do things the system doesn't actually do.
- **Negative reviews** mentioning unmet expectations.

Each pattern points to a divergence between user model and system reality. The fix depends on which side to change.

## Three fix strategies

### 1. Change the system

If the user's model is reasonable and many users share it, change the system to match. Often this is also the simpler design.

Example: users expect "save" to commit immediately. If your system actually queues the save for later, either make save immediate or rename the action to reflect the actual behavior.

### 2. Teach the model

If the system's behavior is genuinely better and users can learn it, invest in onboarding.

Examples:
- Anti-lock brakes required teaching: "brake firmly, steer; don't pump." Manufacturer campaigns and driver-ed material taught the new model.
- Spreadsheets taught a new computing model in the early 1980s; once learned, transferable.
- Modal editors (vim) require learning that "modes" exist; users who learn become extremely productive.

Onboarding that teaches a model:
- **Walks the user through** the first task with explicit guidance.
- **Provides explanation in context** — not a separate tutorial page.
- **Shows the system's state** as actions happen, so the user observes the model.
- **Uses progressive disclosure** of complexity over time.

### 3. Surface the divergence

When the system genuinely differs and you can't (or shouldn't) change the system, surface the difference at the moment it matters.

Examples:
- A "soft-deleted" item shows "Deleted (recoverable for 30 days)" — surfaces the system's actual model.
- A subscription cancellation shows "Canceled — access continues until [date]" — surfaces what canceled actually means.
- A search that ranks by relevance (not chronologically) shows "Sorted by relevance" — explains the unexpected order.

The point is to expose the divergence at the moment of the action, not buried in documentation.

## Onboarding patterns that teach mental models

### Guided first task

Walk the user through their first concrete task — not "here's a tour" but "let's create your first project."

```html
<aside class="onboarding-guide">
  <h3>Let's create your first project</h3>
  <p>1. Click the + button at the top right →</p>
  <!-- The new-project button is highlighted; the user clicks; next step appears -->
</aside>
```

Active practice teaches the interaction model better than passive watching.

### Inline explanation at the moment of action

When the user encounters a feature whose model differs from common expectations, explain in line:

```html
<div class="field">
  <label for="visibility">Project visibility</label>
  <select id="visibility">
    <option value="private">Private (default)</option>
    <option value="team">Team</option>
    <option value="public">Public</option>
  </select>
  <p class="hint">
    Private = only you. Team = everyone in your workspace. Public = anyone with the link.
  </p>
</div>
```

The explanation prevents knowledge mistakes by surfacing the actual model.

### Progressive complexity

Don't expose every feature on day one. Reveal them as the user encounters surfaces where they apply. The user's interaction model grows with their need.

### "What's new" surfaces

When you ship a feature whose model users wouldn't predict from prior versions, announce explicitly. A "what's new in v2" panel that explains how the new feature works, with brief examples, prevents widespread misunderstanding.

## Anti-patterns

- **Tour-only onboarding.** Walk the user through a passive demo. They forget within hours; their interaction model isn't reinforced.
- **Documentation-as-onboarding.** "If you have questions, see the help center." Most users don't.
- **Hidden divergences.** A system that differs from expectation but doesn't say so. Users assume; produce errors.
- **Over-explanation in normal flows.** If you have to constantly explain how things work, the design isn't matching mental models well; redesign rather than over-tutorialize.

## Heuristics

1. **The "first surprise" diagnostic.** Watch a new user. Where do they say "huh, that's not what I expected"? Each surprise is a mental-model mismatch — fix the system or the surfaced model.
2. **The support-ticket pattern audit.** Cluster recent support tickets by the misunderstanding behind them. Patterns reveal mismatches.
3. **The cancel-rate signal.** Steps with high cancel rates often mean users reached them with the wrong expectation. Investigate.

## Related sub-skills

- **`mental-model`** (parent).
- **`mental-model-system-vs-interaction`** — distinguishing the two model types.
- **`expectation-effect`** — mental models *are* the user's expectations.
- **`affordance`** — affordance teaches interaction models at the per-element level.
- **`mimicry`** — borrowing familiar patterns leverages existing models.
