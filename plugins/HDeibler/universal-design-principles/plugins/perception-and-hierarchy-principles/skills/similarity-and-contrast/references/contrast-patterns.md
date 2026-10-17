# Similarity and contrast — patterns

Specific contrast patterns for common UI situations.

## Pattern: primary vs. secondary actions

Primary: brand color background, white text, medium weight, full opacity. Sometimes slightly larger or with a subtle shadow.

Secondary: neutral background or transparent background with border, dark text on neutral, regular weight.

Tertiary (text-only links): brand color text on transparent, no border, medium weight.

The hierarchy clearly visible: primary > secondary > tertiary in visual weight.

## Pattern: hero element vs. supporting

Hero: large size, bold weight, brand or accent color, often a distinct background or container, optional shadow or elevation.

Supporting: standard size, regular weight, neutral colors, plain containers.

The hero immediately draws attention; supporting elements are scannable but don't compete.

## Pattern: featured card in a grid

Among a grid of similarly-styled cards, one card receives differential treatment: larger size, accent color, prominent badge, distinct shape, or a combination. The featured card stands out clearly.

This pattern works when used sparingly. Two featured cards in the same grid weakens the emphasis; three or more eliminates it.

## Pattern: error or warning states

Normal items: neutral colors, standard styling.

Error items: red/danger color (background tint, border, icon), bold weight on the error message, possibly shake animation on appearance.

The contrast must be strong enough that error states are immediately noticed in a list or feed of normal items.

## Pattern: current step in a flow

Past steps (completed): muted color, possibly with a checkmark.

Current step: brand color, full saturation, possibly larger or bolder.

Future steps: gray, deemphasized.

The contrast tells users where they are in the flow at a glance.

## Pattern: active vs. inactive navigation

Active nav item: brand color background or text, bold weight, possibly an indicator (left bar, underline).

Inactive items: neutral text, regular weight, no background.

When users navigate, the active item is immediately distinguishable.

## Pattern: emphasized text within prose

Body text: regular weight, body color.

Emphasized text (bold, italic, underlined link): clearly distinct treatment.

Code (inline): monospace typeface, slight tinted background, slight color shift.

Each kind of emphasis is visually distinct from the body and from the other kinds of emphasis.

## Pattern: foreground vs. background panels

Active workspace: full color, full saturation, primary content treatment.

Chrome (sidebar, header, footer): muted color, lower contrast, secondary treatment.

Modals or overlays over the main content: shadow or scrim behind the modal pulls focus.

The visual hierarchy moves attention to the right thing.

## Pattern: emphasized rows in a table

Standard rows: alternating subtle backgrounds (or no alternation).

Emphasized rows (selected, hovered, important): distinct background color and possibly border.

Headers: bold weight, slight background tint.

The contrast lets users track which row they're interacting with and which rows are categorically different.

## Pattern: badge or tag emphasis

Standard items: no badge.

Categorized items: small badge in category color (e.g., "New," "Beta," "Premium").

Critical items: large badge or prominent visual treatment.

Badges are highly visible by design; reserve them for items that warrant the attention.

## Pattern: progressive emphasis in a sequence

In a multi-step or progressive-disclosure context:

Step 1 emphasized; later steps muted.

After completing step 1, step 2 emphasized; step 1 fades to "completed"; step 3 still muted.

The contrast moves with the user's progress.

## Anti-patterns

**Multiple "primary" elements at the same level.** Two brand-color buttons next to each other, both labeled "Save". Users can't tell which is the actual primary.

**Contrast that doesn't follow hierarchy.** Subtle visual choices that don't track to importance. Visually loud elements that aren't actually important; visually quiet elements that are critical.

**Different contrast styles for the same purpose across the product.** Primary buttons one shade of blue on the home screen and a different shade on settings. Inconsistency.

**Subtle differences read as accidental.** Two card styles that differ by 5% padding. Users can't tell whether the difference is intentional.

**Contrast that's strong but invisible to a fraction of users.** Color-only contrast that fails for color-blind users. Always pair with shape or text.

**Too many simultaneously emphasized elements.** A page with 8 things all visually emphasized. The emphasis cancels.

## Cross-reference

For grouping by similarity, see `similarity-grouping`. For the parent principle, see `gestalt-similarity`.
