---
name: consistency
description: 'Apply the principle of Consistency — making similar things look and behave similarly so users can transfer learning across the interface. Use when designing component libraries, defining naming conventions, choosing whether to invent or borrow patterns, auditing across surfaces (web, mobile, email, support docs), or evaluating whether two features should share or diverge in their interaction model. Strong consistency reduces cognitive load and learnability cost; aggressive consistency can flatten meaningful differences. There are four kinds — aesthetic, functional, internal, external — each with different applications.'
---

# Consistency

> **Definition.** Consistency is the principle that similar things should look and behave similarly, and that different things should look and behave differently. When two parts of a system serve the same function, they should be expressed the same way, so the user's learning about one transfers immediately to the other. When two parts serve different functions, they should be visually and behaviorally distinct, so the user is not misled into expecting the same behavior.

The principle sounds simple and is, in practice, one of the hardest to apply well. The hard part is judging *what counts as similar*. Two buttons that share a visual style but trigger different kinds of actions are misleadingly consistent — they tell the user "we work the same way" when they don't. Two equivalents in the system that are styled differently for no good reason are inconsistent — they force the user to learn the same lesson twice. The skill is calibration: enough consistency to support transfer, enough variation to honor genuine differences.

The classic taxonomy, due to Lidwell, Holden, and Butler, distinguishes four kinds of consistency.

**Aesthetic consistency.** Visual style, typography, color, spacing, iconography. The interface looks like it belongs to one product, drawn from one design system. Aesthetic consistency builds brand recognition and signals craft. Its absence — components that obviously came from different libraries, typography that varies arbitrarily — signals that the team didn't coordinate.

**Functional consistency.** Equivalent operations work the same way. The "save" gesture saves in every screen; the "delete" affordance deletes in every list; the "back" gesture goes back everywhere. Functional consistency lets users learn an interaction once and apply it throughout the product. Its absence creates "exception fatigue" — the user can't predict what any control will do without reading.

**Internal consistency.** Within the product, similar things are similar. This combines aesthetic and functional consistency at the level of "we have one design system and we apply it." Internal consistency is what users notice as "this product feels coherent."

**External consistency.** Across products and platforms, similar things follow shared conventions. The hamburger menu means menu in your app because it means menu in every app. The pinch gesture zooms because it zooms everywhere. External consistency is the user's transferred learning across products being honored. Its absence — your product reinventing standard patterns — creates avoidable friction.

## Why this matters

Every consistency violation costs the user a re-learning. When they navigate from one screen to another and discover the "Done" button is now in the top-right instead of the bottom, they spend a moment relocating it; over thousands of interactions, those moments compound. When they learn that swipe-left dismisses in your inbox but swipe-left archives in your other lists, they have to remember which surface they're on before acting. When they form an expectation from external conventions ("X means Y here, like everywhere else") and you violate it, they're surprised, and surprise in interaction is almost always a cost.

The benefits of consistency compound in the other direction. Once a pattern is established, every additional surface that uses it gets the user's accumulated learning for free. A design system that's been used consistently for years means a new feature is half-learned before anyone touches it.

## When to break consistency

Consistency is a means, not an end. There are good reasons to break it.

**The two cases are genuinely different.** A button that triggers a destructive action should be styled differently from a button that triggers a constructive one. A primary action should be visually weightier than a secondary action. A read-only display should not look like an editable field. These differences in styling reflect genuine differences in behavior and serve the user.

**A new pattern is meaningfully better.** If a new interaction pattern is significantly easier or faster than an existing one, introducing it for that case (and migrating the existing case toward it over time) is better than preserving consistency with a worse pattern. The cost of inconsistency is paid temporarily; the benefit of the better pattern accrues forever.

**The context demands it.** A "Save" button in a quick-edit modal should usually live in the modal, even if "Save" lives in the toolbar everywhere else. Local context overrides global pattern when the local case is self-contained.

These breaks should be deliberate. The failure mode is breaking consistency by accident — through hand-off losses, quick fixes, or different teams making uncoordinated decisions — without the rationale that would justify it.

## Diagnosing consistency problems

A few symptoms suggest a consistency problem worth fixing.

**Users hesitate at familiar-looking controls.** They reach for a button that looks like one they've used before, then pause to verify what it does. The visual consistency is misleading them about functional consistency.

**Documentation needs to explain "in this screen" exceptions.** "On the dashboard, the search box uses syntax X; on the settings page, it uses syntax Y." Documentation for inconsistencies is a smell — it papers over a problem that should be fixed at the design level.

**Users complete the same task differently in different parts of the product.** The same operation is achievable through inconsistent paths. Users build different mental models for what should be one thing.

**New features feel "unlike the rest of the product."** When a new screen visibly came from outside the design system — different typography, different button styling, different spacing — it stands out as not belonging. This is internal aesthetic consistency failing.

## Sub-skills in this cluster

- **consistency-internal** — Maintaining consistency within your own product: design systems, component libraries, audit and enforcement, handling legacy patterns.
- **consistency-external** — Honoring conventions from outside your product: platform conventions, category conventions, when to follow vs. when to lead.

## Worked examples

### A multi-platform product

A productivity tool ships native apps for iOS, Android, web, and desktop. Each platform has its own conventions: iOS expects bottom tabs, Android expects a navigation drawer, web expects a top nav. Forcing one navigation pattern across all platforms violates external consistency on three of them. Honoring each platform's conventions violates internal consistency across the company's product.

The right tradeoff is usually to honor external conventions (platform-native navigation patterns) while keeping internal consistency in everything that's the user's *content* (data model, terminology, workflows). The chrome adapts; the substance is consistent.

### Two confirmation patterns in one product

A product has two confirmation flows. In one, deleting an item shows a modal: "Delete this? Cancel / Delete." In the other, deleting shows an inline confirm: "Are you sure?" with Yes/No buttons appearing where the original button was. Both work. But users encountering the second flow after the first are momentarily confused — the action is the same but the interface is different.

The fix: pick one pattern (the modal, if the action is high-stakes; the inline if it's low-stakes) and apply it consistently for all confirmations of similar weight. If two different weights of confirmation actually deserve different treatments, distinguish them deliberately and document the rule.

### A button styling drift

Over time, a product accumulates buttons in seven different shades of blue, three different border-radius values, and two different padding scales. Each individual choice was made in good faith — a designer fixing a specific issue, an engineer matching a design they had at hand — but the accumulated drift is visible. Users don't have a single "primary action" visual to learn; instead they see a sea of similar-but-not-identical buttons.

The fix: a design-system audit, consolidating the variants down to a small set with clear semantic roles. Then ongoing enforcement (linting, design reviews) to prevent re-drift.

### Inventing a new pattern when a convention exists

A team designs a search interface using a custom icon and a custom keyboard shortcut, ignoring the magnifying glass and Cmd-F that users expect. The team's reasoning: "Our icon is more on-brand, and Cmd-F is taken by our other feature." The result: users don't recognize the search affordance and can't find the shortcut. External consistency would have served them better even at some brand cost.

The fix: use the convention. If you really need to take Cmd-F for something else, find a different shortcut — but the search itself should look like search.

### Honoring a convention while extending it

A messaging product uses the standard send-on-Enter convention. They want to add the option to send on Cmd-Enter for users who prefer to use Enter for new lines. The right pattern is to honor both: Enter sends by default (matching the convention), and a setting lets users switch to Cmd-Enter (extending the convention). Users who don't change the setting get the expected behavior; users who switch get a workflow that matches their preference.

This is consistency that honors external conventions while accommodating differences — the right balance.

## When the principle is misapplied

**Consistency for its own sake.** Forcing every screen into the same template even when the screens have meaningfully different content. The result is a product that's coherent but bland; the visual rhythm doesn't reflect the actual variety of content.

**Aesthetic consistency masking functional inconsistency.** Two buttons that look identical (same color, same size, same icon style) but behave differently. The user learns the visual pattern and is then surprised when behavior doesn't match. Visual identity is a strong implicit promise of behavioral identity; honor it.

**External consistency that actively hurts the user.** Some platform conventions are legacy and should be broken. Apple's "tap-and-hold for context menu" was historically inconsistent across apps and is still being normalized; in 2010, following the inconsistent convention was worse than picking a coherent pattern of your own. When a convention is genuinely bad and the cost of breaking it is small, do.

**Premature consistency.** Locking down patterns too early in a product's life, before you know which patterns work. Better to allow some inconsistency in early development and consolidate as patterns prove themselves than to enforce consistency around patterns that turn out to be wrong.

## Heuristic checklist

Before making a design decision, ask: **Does an existing pattern in our product serve this case?** If yes, use it. **Does an external convention serve this case?** If yes, use it unless you have a strong reason not to. **If I'm departing from an existing pattern, is the new approach genuinely better, or am I just reinventing?** If the latter, stop. **If two cases look the same, do they behave the same?** If not, distinguish them visually so users can predict behavior.

## Related principles

- **Mental Model** — consistency lets users transfer their mental model across surfaces.
- **Mapping** — consistent mappings reinforce each other; inconsistent ones interfere.
- **Recognition Over Recall** — consistency strengthens recognition by stabilizing patterns.
- **Affordance** — consistent affordances mean users can predict what's interactive.
- **Mimicry** — consistency with external conventions is one form of mimicry.
- **Iconic Representation** — consistent icon use across the product builds recognition.

## See also

- `references/lineage.md` — origins in HCI, design systems literature, and platform conventions.
- `consistency-internal/` — sub-skill on internal consistency.
- `consistency-external/` — sub-skill on external consistency.
