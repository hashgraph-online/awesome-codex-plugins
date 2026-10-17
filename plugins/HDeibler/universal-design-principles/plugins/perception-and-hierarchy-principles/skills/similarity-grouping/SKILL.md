---
name: similarity-grouping
description: 'Use visual similarity to create perceptual groups — making related items look alike so users perceive them as a set. Use when designing lists with categorized items, navigation systems, status displays, dashboards with multiple data series, or any layout where you want users to see "these things go together" at a glance. The strongest grouping cues, in order, are color, size, shape, and orientation; combine multiple cues for the strongest grouping.'
---

# Similarity — grouping

When you want users to perceive a set of items as belonging together — as a category, as related, as the same kind of thing — visual similarity is the most direct way to communicate it. Two items styled the same way are perceived as a pair; ten items styled the same way are perceived as a set; an entire list styled consistently is perceived as a category.

## Core grouping techniques

**Same color.** The strongest grouping cue. All "active" items in one color; all "inactive" items in another. All items in a category share a color tag or background tint.

**Same size.** Items at the same visual scale group. All section headings at the same size; all body text at the same size; all icons at the same size.

**Same shape.** Items in the same shape group. All cards have the same proportions; all buttons have the same corner radius; all icons share a stroke style.

**Same icon or symbol.** Items marked with the same icon group. All "important" items get a star; all "deletable" items get a trash icon visible on hover.

**Same typographic treatment.** Bold weight, italic, color shift — applied consistently — makes a class of words read as a group (every link, every keyword, every status name).

Combine multiple cues for stronger grouping. A "selected" item with both a colored background AND a colored border AND a checkmark icon is grouped much more strongly than an item with just one of those cues.

## When grouping by similarity is the right move

**Related items spread across a layout.** If items aren't physically close (proximity grouping isn't available) but should be perceived as related, similarity carries the grouping. Selected items in a long list, for example.

**Mixed categories in a single view.** A dashboard showing servers in different statuses, files of different types, projects in different stages. Similarity by category lets users scan and segment.

**Repeating elements with shared role.** Buttons of the same priority; navigation items at the same level; cards of the same type. Consistent styling makes the role recognizable.

**Status communication.** Active vs. inactive, healthy vs. failing, approved vs. pending. Different visual treatment for each status; consistent within each status.

## Worked examples

### A multi-status dashboard

A monitoring dashboard shows 50 services. Each service can be in one of four states: healthy, degraded, down, unknown.

- Healthy: green background tint + checkmark icon.
- Degraded: yellow background tint + warning icon.
- Down: red background tint + X icon.
- Unknown: gray background tint + dash icon.

The user can scan all 50 services and immediately see the distribution of states. Color does most of the grouping; icons reinforce.

If only one cue had been used (only icons, no color), the perceptual grouping would be much weaker; users would have to focus on each item individually.

### A document list with file-type grouping

A file manager shows mixed file types. PDFs all have a red PDF icon; Word docs have a blue Word icon; images have a small thumbnail; folders have a folder icon. The visual similarity within each file type makes scanning easy: "show me all the PDFs" is just "find all the items with the red icon."

If file types had been distinguished only by extension in the filename, scanning would be much harder.

### A navigation hierarchy

A sidebar nav has primary nav items (top level) and secondary nav items (children, indented). Primary items use a slightly larger size, bolder weight, and consistent icon treatment. Secondary items use smaller size, regular weight, indented position.

Within each level, items group by similarity. The two levels are distinguished by their differences. Users see the hierarchy at a glance.

### Selected items in a long list

A list of 100 items. The user has selected 12 of them. Selected items have a colored background tint (the brand color at 15% opacity); unselected items have no background.

Even though selected items are scattered through the list, the color similarity makes them visually group. The user can see how many are selected, and where they are, without scrolling carefully.

If selection had been indicated with just a small checkmark in the corner, the selected items wouldn't group as strongly; the user would need to scan more carefully.

### A pricing table

A pricing table shows three plans (Basic, Pro, Enterprise). Each plan card has the same visual structure (price, features list, CTA button). Within each card, the features list uses the same typography, the same checkmark icon for included features, the same X icon for excluded features.

The structural similarity across cards makes them comparable: the user can scan horizontally to compare features. The styling similarity within each card makes each card readable as a coherent unit.

## Anti-patterns

**Grouping cues that conflict.** A card with a colored background that says "Important" but a small subtle border that says "Inactive." The user gets contradictory grouping signals.

**Inconsistent styling within a category.** Some items in the "important" category styled with a red border, others with a red background, others with just a red icon. The category fragments visually.

**Subtle differences that don't communicate.** A 5% opacity change between two states. The visual similarity is so strong the dissimilarity goes unnoticed; users don't perceive distinct groups.

**Overgrouping.** Trying to make every item in a long list look subtly different to encode many dimensions of metadata. Users can't process more than ~5 visual categories at a time without effort. Reduce the categories or use other mechanisms (filters, sort) for the rest.

**Color used for grouping but accessible only by color.** Color-blind users can't perceive color-only grouping. Always pair color with shape or position.

## Heuristic checklist

When designing a layout with multiple item types, ask: **What are the categories of items?** Each category should have a consistent visual treatment. **Which similarity cues am I using to communicate each category?** Color is strongest; combine with shape or icon for accessibility. **Are items within each category styled consistently?** Inconsistency fragments the grouping. **Are different categories distinguished sufficiently?** Subtle differences may not be perceived.

## Related sub-skills

- `gestalt-similarity` — parent principle on similarity-based perception.
- `similarity-and-contrast` — sibling skill on dissimilarity for distinction.
- `proximity` — proximity grouping; complementary to similarity.
- `color` — color is the strongest similarity cue.
- `consistency` — consistency creates similarity within a product.

## See also

- `references/grouping-patterns.md` — patterns for specific grouping situations.
