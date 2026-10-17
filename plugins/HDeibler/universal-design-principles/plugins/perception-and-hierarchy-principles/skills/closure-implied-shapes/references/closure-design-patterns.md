# Closure — design patterns

Specific patterns for applying closure in different design contexts.

## Pattern: minimal icon set

An icon system using outlined shapes with consistent stroke weight and selective omission of detail. Each icon implies its form through a few strokes; the user's perception completes the rest.

Examples: Material Symbols, Phosphor Icons, Lucide, Tabler Icons, Heroicons.

Design considerations:
- Stroke weight consistent across the set (typically 1.5–2px at 24px).
- Corner treatment consistent (sharp, rounded, or in between).
- Forms recognizable at the smallest rendering size (16–18px usually the floor).
- Avoid forms that require detail to recognize (skip facial expressions, complex objects).

## Pattern: card containment without borders

Cards that feel contained without an explicit border:
- Subtle background color (slightly different from the surrounding surface, often by 3–5% lightness).
- Subtle drop shadow (2–4px blur, very low opacity).
- Consistent internal padding establishing the "edges" through spacing.

Pairs well with:
- Generous gaps between cards (so cards don't feel crowded against each other).
- Consistent corner radius (rounded uniformly).
- Hover states that subtly increase elevation (subtle interaction feedback).

## Pattern: text containment by spacing alone

Text blocks separated by spacing rather than visual dividers. A paragraph followed by space followed by a heading followed by space followed by another paragraph: the structure is implied by the rhythm.

Useful when:
- The content is conceptually structured.
- The visual context is clean (not competing with other elements).
- Users will read sequentially (top to bottom).

Requires:
- Consistent spacing (so the user can perceive the rhythm).
- Sufficient spacing to make the breaks visible.

## Pattern: implied structure in charts

Charts that omit explicit axes, gridlines, or legends in favor of inferred structure:
- Bars rising from an inferred baseline.
- Lines on a chart with subtle (not dominant) reference points.
- Color-coded series identified through visual matching with the legend.

Works when:
- The data is clear enough that the reference points aren't ambiguous.
- The chart is simple (few series, clear values).

Less useful for:
- Charts where exact values matter (omit gridlines and users can't read precisely).
- Highly technical charts where structure must be unambiguous.

## Pattern: logo with hidden shape

A logo that uses negative space or alignment to imply a meaningful shape that's not explicitly drawn.

Famous examples:
- FedEx (arrow between E and X).
- Toblerone (bear hidden in the mountain silhouette).
- Amazon's smile (arrow from A to Z).
- WWF panda (form implied by black shapes; white parts are negative space).

Requirements:
- The hidden shape should be discoverable but not immediately obvious (the moment of noticing is part of the appeal).
- Once seen, the shape should be unmistakable.
- The shape should reinforce the brand meaning, not be arbitrary.

## Pattern: skeleton loading state

Pulsing rectangles in the shape of upcoming content. The user sees the structure of the page being formed; the wait feels productive.

Design considerations:
- Match the actual content's layout (titles, body, images all at appropriate proportions).
- Subtle animation (gentle pulse or shimmer, not distracting).
- Replace seamlessly when content arrives (no jarring transition).

## Pattern: visual hierarchy through proximity and similarity

Multiple elements at different hierarchy levels, with the levels implied through spacing and styling rather than explicit separators:

- A page title with significant space below.
- Section headings with moderate space above and below.
- Body text packed tighter, with smaller paragraph spacing.

The hierarchy is perceived through the rhythmic structure; explicit dividers (lines, boxes) aren't needed.

## Pattern: implied chart legend

Chart series labeled directly on the data (the line's label appears at the line's endpoint, in the line's color) rather than in a separate legend box. The connection between label and data is implied by position and color.

This is one of the highest-ROI improvements in chart design. It removes the cognitive cost of looking back and forth between chart and legend.

## Pattern: inferred form in illustration

Illustrations using:
- Silhouettes (form implied by outline).
- Partial details (focus on key features, omit the rest).
- Abstracted shapes (geometric forms suggesting subjects).
- Negative space (parts of the form left empty for the viewer to complete).

Common in modern editorial and product illustration. Works because the audience can fill in the missing detail; doesn't work for technical illustrations where precision matters.

## Pattern: visual rhythm without lines

A page layout that uses consistent spacing and sizing to create a perceived grid, without drawing the grid lines. Elements align to the same vertical positions; columns share the same widths; spacing matches across the layout.

The user perceives the structure; the visual weight stays low.

## Anti-patterns

**Closure where clarity is paramount.** A "delete" or "irreversible" action represented by an ambiguous form. The user needs to be sure of what they're triggering.

**Hidden shapes that are too hidden.** A logo with a hidden meaning that no one notices. The closure adds nothing.

**Closure that breaks at common rendering sizes.** A minimal icon that works at 24px and disintegrates at 16px. Test at the actual sizes.

**Closure incompatible with accessibility.** A form that requires visual perception that some users lack (color, fine detail). Provide alternatives.

**Closure as substitute for thought.** Stripping detail reflexively without considering whether the form will still communicate. Reduction should be deliberate.

## Cross-reference

For when closure is the wrong choice, see `closure-completion-cost`. For the parent principle, see `closure`.
