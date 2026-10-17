---
name: mental-model-system-vs-interaction
description: 'Use this skill when distinguishing the two mental-model types — system models (how the user thinks the system works) and interaction models (how the user thinks they should use it). Trigger when designing onboarding (which model to teach), reviewing user confusion (which model is wrong), or building documentation (which model to explain). Sub-aspect of `mental-model`; read that first.'
---

# System models vs. interaction models

The book's distinction matters in practice because the two model types are formed differently and need different design responses.

## System models

How the user thinks the system works internally. Components, mechanisms, causal logic.

Examples:

- "The cloud" stores my files; they're somewhere on the internet.
- "The recommendation algorithm" looks at what I clicked.
- "Two-factor authentication" sends a code to verify it's me.

System models are often inaccurate without consequence. Most users don't know how email actually routes (SMTP, MX records); their model — "I type address, click send, message arrives" — is sufficient. The system doesn't *need* an accurate user system model unless the user must reason about edge cases.

When system models matter:

- **Troubleshooting** — when something goes wrong, users with better system models recover faster.
- **Privacy and security** — users with realistic models of how their data flows make better choices.
- **Power use** — users with accurate models can use features beyond the basic.

Designers tend to have rich system models (they built it); users tend to have simplified or wrong ones. The gap is acceptable up to a point.

## Interaction models

How the user thinks they should use the system. Actions, sequences, expected responses.

Examples:

- To save: Cmd-S or click File → Save.
- To navigate: click links, use back button.
- To delete: select item, press Delete or click trash icon.

Interaction models are what designers must align to. A system whose interaction model the user can't form is unusable, regardless of how cleverly its system model is conceived.

When interaction models matter:

- **Always.** Every interaction is a moment when the user's interaction model is tested.
- **Particularly** for first-use; subsequent use refines the model through experience.
- **Critically** for destructive or irreversible actions.

Users tend to have weak interaction models initially; with use, they accumulate accurate models through trial. Designers often have weak interaction models because they know "how it really works" rather than "how to use it." Bridging the gap requires user testing.

## Asymmetry between designers and users

The book makes this point compactly: designers tend to have complete system models but weak interaction models. Users have weak system models but, with use, develop accurate interaction models.

The implication: designers can't infer the user's interaction model from their own. They must test with real users.

## How to design for each

### For system models

- **Faithful system images** that surface the system's actual state.
- **Conceptual onboarding** that teaches the model when accuracy matters.
- **Documentation** that explains underlying mechanisms for users who care.
- **Visualizations** of internal state when relevant (sync status, processing pipelines).

### For interaction models

- **Conventional patterns** so users transfer prior interaction models.
- **Affordances** that signal what to do.
- **Feedback** that confirms the action did what the user expected.
- **Recovery** when the interaction didn't match expectation.

## When to invest in which

For most products, **interaction models** are the higher-priority investment. Most users don't need accurate system models; all users need accurate interaction models.

Exceptions:

- **Power-user tools** (developer tools, admin consoles) — power users benefit from system-model accuracy.
- **Privacy-sensitive products** — users need to understand the system to consent meaningfully.
- **Educational products** — teaching the system model is the point.

## Worked examples

### Example 1: a calendar app

System model: events stored in a database; synced across devices via cloud.

Interaction model: click date to create event; drag to move; click event to edit.

Most users only need the interaction model. The system model can be opaque ("it just syncs"). Investment: interaction-model design and testing.

### Example 2: a developer tool

System model: code runs in a sandboxed environment; logs stream from server; deploys are versioned.

Interaction model: type code in editor; click run; see output; click deploy.

Power users (developers) benefit from the system model. Investment: both. The IDE's UI handles interaction; documentation, error messages, and visible state handle the system model.

### Example 3: a privacy-affecting feature

System model: data is shared with third parties for ad personalization.

Interaction model: toggle in settings.

Users *must* understand the system model to consent meaningfully. Investment: clear explanation of what the toggle actually does, in plain language, at the point of decision.

## Anti-patterns

- **Optimizing for system-model purity at the expense of interaction usability.** "Our metaphor is technically accurate but users can't find anything."
- **Hiding the system model when users need it.** Privacy disclosures buried; sync status invisible; error messages that don't explain causes.
- **Designer's interaction model substituted for user's.** Designers ship a clever flow that they themselves can navigate; users can't.

## Heuristics

1. **The "what model do users need?" check.** For each feature, ask: what does the user need to know about how this works (system) vs. how to use it (interaction)?
2. **The user-test-vs-self-test.** Designers walking through their own design test the designer's model, not the user's. Watch real users.
3. **The first-error analysis.** When a user encounters their first error, was it a system-model failure (they didn't know how it works) or interaction-model failure (they didn't know what to do)? Different fixes.

## Related sub-skills

- **`mental-model`** (parent).
- **`mental-model-mismatch-and-onboarding`** — bridging the gaps when models diverge.
- **`affordance`** — interaction models at the per-element level.
- **`mimicry`** — borrowing models from familiar systems.
