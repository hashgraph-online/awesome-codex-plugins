# Similarity grouping — patterns

Specific patterns for using similarity to group items in common UI contexts.

## Pattern: status-by-color

Each status has a distinct color (often paired with an icon). Items in the same status share the visual treatment.

Common status palette:
- Healthy / success / active: green (#10B981 or similar)
- Warning / pending: yellow or amber (#F59E0B)
- Error / down / destructive: red (#EF4444)
- Informational / in-progress: blue (#3B82F6)
- Neutral / disabled / unknown: gray (#6B7280)

Pair color with shape (icon) for accessibility. Avoid using ten different colors for ten different statuses; users can't track that many distinct categories.

## Pattern: category-by-icon

Each category gets a consistent icon. All items in the category display the icon. Users learn the icon-category mapping after a few exposures.

Useful when:
- The categories are fixed and limited (5–15 categories).
- Users will encounter many items across categories.
- The icons are visually distinct enough to be quickly identified.

Less useful when:
- Categories are too numerous.
- Categories are user-defined (icons can't anticipate them).
- The visual real estate doesn't accommodate icons.

## Pattern: badge-or-tag

A small visual element (badge, tag, label) attached to items in a particular state or category. The badges share visual treatment within a state but differ across states.

Common uses:
- "New" badge on recently added items.
- "Pro" or "Premium" badge on paywalled features.
- Status badges (e.g., "Draft," "Published," "Archived").
- Tags on content (genres, topics, owners).

Badges are highly visible and quick to scan. They can stack (an item can have multiple badges) but stacking too many becomes cluttered.

## Pattern: row-style alternation

In a long list or table, alternating background colors (zebra striping) helps users track horizontally without losing the row.

Use carefully:
- Subtle alternation (2–5% darker on alternate rows) is usually right.
- Heavy alternation (high contrast) can be visually noisy.
- For very long rows, alternation aids scanning; for short rows, it may not be needed.
- Alternation doesn't communicate categorical information; it's purely a scan-aid.

## Pattern: indented hierarchy

Hierarchical lists (a tree, an outline, a nested file structure) use indentation to indicate parent-child relationships. Items at the same indentation level are siblings (peers); deeper indentation means children.

Combined with similarity by typography (headings vs. body, parent vs. child styling), indentation creates clear hierarchy that users can scan.

## Pattern: card-based list

Items in a list each presented as a card with consistent internal structure (title, image, metadata, action). Each card looks the same; users scan a list of structurally identical cards.

The card pattern is common because:
- Cards have clear boundaries (visual chunking).
- The internal structure can be elaborate while staying scannable.
- Cards can be designed to work in both list and grid layouts.

## Pattern: avatar/icon-led list

Items in a list each prefaced with a small avatar or icon. The avatar/icon position is consistent (always left, same size).

Common uses:
- Contact lists (avatar + name).
- Team member lists.
- Comment threads (avatar + content).
- Activity feeds.

The visual rhythm of avatars helps users scan vertically and identify items by associated person/icon.

## Pattern: priority-by-weight

Important items styled with bold weight; less important items with regular or light weight. The weight similarity groups items at each priority level.

Common uses:
- Task lists with priority indication.
- News feeds with featured/standard distinction.
- Inbox lists with unread/read distinction (unread bold, read regular).

The weight contrast is subtle but effective; it doesn't add visual noise the way color does.

## Pattern: type-by-shape

Different content types displayed with different shapes:
- Square cards for one type.
- Circle avatars for another.
- Pill-shaped tags for another.

The shape similarity within each type makes scanning by type easy. Use sparingly — too many shape types in a single layout becomes chaotic.

## Pattern: interactive-by-style

Interactive elements (buttons, links, controls) styled distinctly from non-interactive content. Within interactive, primary actions styled distinctly from secondary actions.

Common implementation:
- All buttons share a common style (rounded, with padding, with state changes).
- All links share a common style (underlined or colored, with hover state).
- All non-interactive text uses a standard body style.

Users can scan the page and immediately identify what's clickable.

## Pattern: data-series in charts

In multi-series charts (line charts, bar charts), each series uses a distinct color consistently. The line for revenue is always blue across the dashboard; profit is always green; expenses are always red.

This is similarity grouping across the whole product: a user looking at any chart can identify which line is which series by color, without needing to consult the legend each time.

Cross-product semantic colors (revenue is always blue) deserve documentation in the design system so they're applied consistently.

## Pattern: state-by-treatment

Different interaction states (default, hover, active, focus, disabled) get distinct visual treatment, applied consistently across all interactive elements.

A button's hover state is the same shift across all buttons (e.g., 10% darker background). A focus ring is the same color across all focusable elements. A disabled state is the same opacity across all disabled controls.

Consistent state treatments make interactive behavior predictable and accessible.

## Anti-patterns

**Ad-hoc grouping treatments.** Each part of the product invents its own grouping cues. Users can't transfer their understanding between sections.

**Color-only grouping.** Without shape or label reinforcement, color-blind users can't perceive the grouping.

**Subtle differences that don't communicate.** A "selected" state that's barely distinguishable from "unselected." Users can't see what's grouped with what.

**Cues that fight each other.** A red background that says "danger" combined with a checkmark that says "approved." Users don't know which signal to trust.

**Overuse of all available cues.** A single item highlighted with color, bold weight, large size, distinct shape, badge, AND icon. The item screams; the rest of the layout falls away. Reserve heavy emphasis for moments that warrant it.

## Cross-reference

For dissimilarity used to distinguish, see `similarity-and-contrast`. For the parent principle, see `gestalt-similarity`.
