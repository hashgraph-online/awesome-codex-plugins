---
name: gestalt-similarity
description: 'Apply the Gestalt principle of Similarity — elements that share visual attributes (color, shape, size, orientation) are perceived as belonging together, regardless of their physical proximity. Use when grouping related items in a list, status indicators, dashboard cards, navigation, or any context where you want the user to perceive certain items as a set. Similarity is one of the strongest grouping cues; it works even when proximity says otherwise. Color is the strongest similarity cue, then size, then shape; orientation is weakest.'
---

# Gestalt Similarity

> **Definition.** Similarity is the Gestalt principle that elements sharing visual attributes — color, shape, size, orientation, texture — are perceived as belonging together. Two red dots in a sea of blue dots form a group, even when they're not physically close. Three identical icons in a row of varied icons form a set. Items styled the same way "go together" in the user's perception, regardless of their position in the layout.

Similarity is one of the original Gestalt grouping principles, established by Wertheimer in the early 20th century. It's one of the strongest perceptual forces in visual design: the user's brain automatically segments the visual field into groups based on visual similarity, before any conscious analysis. Designs that exploit this segmentation work with the user's perception; designs that fight it work against it.

## The hierarchy of similarity cues

Not all similarity is equally strong. Research consistently finds:

**Color is the strongest grouping cue.** Two items with the same color are perceived as a group even when many other attributes differ. Highlighting selected items with color is one of the most reliable design techniques.

**Size is second.** Items of the same size group together; different sizes form different groups. This is why heading hierarchy works — large text reads as one set (headings), smaller text as another set (body).

**Shape is third.** Items with the same shape group together. Round buttons read as a different set than square buttons. Cards of the same proportions feel like one set.

**Orientation is weakest.** Items oriented the same way group, but the cue is subtle. Useful for distinguishing axes (vertical vs. horizontal) more than for grouping items.

When you want to group items strongly, reach for color. When you want to distinguish groups, reach for color difference. Other similarity cues are reinforcement, not primary.

## Why similarity matters

Similarity is doing two jobs at once:

**It groups items that should be perceived together.** A row of similar buttons reads as a button bar. A column of similarly-styled cards reads as a list. A set of items with the same icon reads as the same kind of thing.

**It distinguishes items that should be perceived as different.** A "destructive" button styled differently from "constructive" buttons signals its different role. A "primary" action styled differently from "secondary" actions reveals its priority. Status indicators in different colors communicate different states.

The principle is: **make similar things look similar, and make different things look different**. This sounds obvious and is often violated. Two visually-identical buttons that behave differently mislead the user. Two functionally-equivalent items styled differently fragment the user's perception.

## Diagnosing similarity problems

Symptoms of similarity issues:

**Users miss related items.** They see one item but don't realize there are others "like it" elsewhere on the screen because the visual treatment doesn't link them.

**Users confuse different items as the same.** They click the destructive button thinking it was the constructive one because both are styled the same way.

**A list looks fragmented.** Items in the same list have inconsistent visual treatment, so the user can't see them as a coherent set.

**Status is ambiguous.** Without distinct visual treatment, statuses (active/inactive, success/failure, available/unavailable) blur together.

## Sub-skills in this cluster

- **similarity-grouping** — Using similarity to group related items: navigation items, status indicators, list items, dashboard cards.
- **similarity-and-contrast** — Using deliberate dissimilarity (contrast) to distinguish items: primary vs. secondary actions, error states, emphasis.

## Worked examples

### Status indicators

A dashboard shows servers with various statuses: green check (healthy), yellow warning (slow), red X (down), gray dash (unknown).

Each status is consistently colored and shaped throughout the product. The color is the primary similarity cue (all greens are healthy), reinforced by shape (always a check) and color (always green). Users can scan a long list and identify all healthy servers at a glance.

### A primary vs. secondary button distinction

A form has a primary "Submit" action and secondary "Cancel" and "Save Draft" actions.

The primary button uses a strong color (the brand color), bold weight, larger size. Secondary buttons use a neutral color, regular weight, same size as primary or slightly smaller. The contrast in color and weight makes the primary action immediately distinguishable.

If both buttons were styled the same way, users would have to read the labels to know which was primary. With clear similarity-based contrast, the primary button is recognizable at a glance.

### A list with inconsistent styling

A settings page lists toggles for various options. Some toggles are styled with the system component (consistent shape, color, behavior); others are custom-styled with different colors and shapes. The user sees what should be a single list of toggles as a fragmented set of unrelated controls.

The fix: apply the same toggle component (and styling) to all options. Similarity unifies the list.

### Highlighting selected items

A list shows multiple items, with two selected. The selected items are highlighted with a colored background (the brand color at 10% opacity). The non-selected items have no background.

The color similarity makes the selected set immediately visible — even if the items are spread across a long list. The user can see at a glance how many are selected.

If "selected" had been indicated with a small icon or subtle border instead, the similarity would be much weaker; users would have to scan to find selected items.

### Different shapes for different roles

A toolbar has navigation buttons (square), action buttons (rounded), and link buttons (no background). The shape difference signals the different roles. Within each role, the buttons share the same shape and behave similarly.

This is similarity within roles and contrast between roles. Users learn the convention quickly because the shape is doing the categorization work.

## Anti-patterns

**Visual similarity without functional similarity.** Two buttons that look identical but trigger different kinds of actions (one navigates, one submits a form). The visual mislead is dangerous.

**Functional similarity without visual similarity.** Two buttons with the same function styled differently because they appear in different parts of the UI. Users don't recognize them as related.

**Color overload.** Using too many colors so similarity by color loses meaning. Five colors with clear semantic roles (primary, secondary, success, warning, error) is better than fifteen colors used arbitrarily.

**Subtle differences that don't communicate.** Two button styles where the only difference is a 5% opacity change. Users can't perceive the difference, so the styling isn't doing distinguishing work.

**Heavy similarity that masks real differences.** When everything in the UI is styled the same way (every card looks the same, every list item looks the same), the user can't distinguish the things that genuinely warrant different treatment.

## Heuristic checklist

Before settling on visual treatment, ask: **Are similar items styled similarly, and different items styled differently?** Mismatches cost user comprehension. **Is color (the strongest cue) being used to group the things that most need grouping?** If yes, reinforce with secondary cues. **Are status indicators visually distinguishable beyond just color (for accessibility)?** Pair color with shape or label. **Does the design reduce to a recognizable pattern for the user?** If users can predict that "this kind of item always looks like X," similarity is doing its job.

## Related principles

- **Gestalt grouping principles generally** — proximity, similarity, continuity, closure.
- **Proximity** — items that are close in space group together; similarity reinforces or sometimes overrides proximity.
- **Color** — color is the strongest similarity cue.
- **Hierarchy** — similarity is one mechanism by which hierarchy is expressed.
- **Consistency** — similarity within a product is what consistency feels like.
- **Signal-to-Noise Ratio** — coherent similarity reduces visual noise.

## See also

- `references/lineage.md` — origins in Gestalt psychology and design.
- `similarity-grouping/` — sub-skill on using similarity to create groups.
- `similarity-and-contrast/` — sub-skill on using contrast to distinguish.
