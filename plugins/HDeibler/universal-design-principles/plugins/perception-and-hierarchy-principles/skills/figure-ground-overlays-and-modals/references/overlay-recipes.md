# Overlay design — recipes

Specific design recipes for each common overlay type.

## Recipe: confirmation modal

**Use for:** important decisions that interrupt the user's flow (delete account, discard unsaved changes, irreversible action).

**Components:**
- Scrim: 50% opacity black overlay.
- Modal container: white background (or elevated dark in dark mode), rounded corners, max-width ~500px, centered horizontally and (slightly) vertically.
- Elevation: prominent shadow (16–24px blur).
- Headline: 18–22px, medium or semibold weight.
- Body text: 14–16px, regular weight, max ~3 lines.
- Primary action: button using the appropriate color (red for destructive, brand color for constructive).
- Secondary action: neutral-styled cancel button.
- Close affordance: X in upper-right corner.
- Dismiss: click outside (on scrim), escape key, X button.
- Focus: trap within modal; first focusable element auto-focused.

**Animation:** quick fade-in for scrim and modal; modal scales in from 95% to 100% to feel like it's coming forward.

## Recipe: form modal

**Use for:** longer interactions that need focused input (creating a record, editing settings, complex configurations).

**Components:**
- Scrim: 40–50% opacity black.
- Modal container: white, rounded corners, max-width 600–800px.
- Elevation: prominent shadow.
- Header: title + close X.
- Body: scrollable form content.
- Footer: action buttons (typically right-aligned).
- Dismiss: X button, escape, possibly click-outside (with confirmation if there's unsaved input).
- Focus: trap; first input auto-focused.

**Considerations:** if the form is very long, consider whether a modal is the right pattern (drawer or full page might be better).

## Recipe: drawer (side panel)

**Use for:** secondary interactions that don't require fully covering the page (settings, details, secondary navigation).

**Components:**
- Position: anchored to one edge (typically right; sometimes left for navigation drawers).
- Width: 320–500px depending on content.
- Scrim: 40–50% opacity over the visible page area.
- Elevation: shadow on the inner edge of the drawer.
- Header: title + close X.
- Body: scrollable content.
- Dismiss: X button, escape, click on scrim.

**Animation:** slide in from the anchored edge over 250–300ms.

## Recipe: popover

**Use for:** small contextual content attached to a trigger (option lists, brief detail views, color pickers).

**Components:**
- Container: small (typically 200–400px wide), positioned next to the trigger element.
- Elevation: subtle shadow (4–8px blur).
- Border: optional 1px border for cleaner edge.
- Background: white (or elevated in dark mode).
- Arrow / pointer: optional, indicating the connection to the trigger.
- Dismiss: click outside, escape, or selecting an option (if it's a menu).

**No scrim:** popovers don't need to push the page into ground because they're small and obviously contextual.

## Recipe: dropdown menu

**Use for:** lists of options or commands (account menu, more-actions menu, select dropdown).

**Components:**
- Container: sized to content; typically 150–300px wide.
- Position: below the trigger by default; flips up if not enough space below.
- Elevation: subtle shadow.
- Items: standard list rows with hover state.
- Dismiss: click outside, escape, selecting an item.

**Considerations:** for very long lists, consider scrolling within the dropdown or switching to a different pattern (autocomplete, modal).

## Recipe: toast notification

**Use for:** transient feedback about an action (saved successfully, error occurred, processing complete).

**Components:**
- Container: pill-shaped or rounded rectangle.
- Position: lower-right corner (web), bottom edge (mobile).
- Color: success green / error red / info blue / warning yellow.
- Text: concise (one line, max 50–60 characters).
- Optional action button (e.g., "Undo," "View details").
- Auto-dismiss: 3–5 seconds typically; longer for errors.
- Manual dismiss: X button or swipe.

**No scrim, no focus trap:** toasts don't interrupt the user's work.

**Considerations:** stack toasts if multiple appear; older toasts shift up. Don't overwhelm with too many simultaneous toasts.

## Recipe: tooltip

**Use for:** brief explanatory text on hover or focus (button labels, icon meanings, term definitions).

**Components:**
- Container: small (sized to content; typically 100–250px wide).
- Position: adjacent to the triggering element.
- Background: dark (typically), with white text. Or light with dark text — pick one and stay consistent.
- Border: usually none.
- Shadow: subtle.
- Arrow / pointer: optional, indicating the connection.
- Trigger: hover, focus, or long-press.
- Dismiss: mouse leaves trigger, focus moves, or after a brief timeout.

**Accessibility:** tooltips must be reachable by keyboard (focus, not just hover). Mobile tooltips often use long-press or are replaced with always-visible labels.

## Recipe: lightbox

**Use for:** image or video viewing where the content needs full attention (gallery, attachment preview).

**Components:**
- Scrim: heavy (80–95% opacity black or pure black).
- Image/video centered, sized to fit while preserving aspect ratio.
- Navigation: previous/next arrows, close X.
- Optional controls: zoom, download, share.
- Dismiss: X button, escape, click outside the image area.

**Considerations:** heavy scrim helps the image read clearly. Page beneath should be effectively invisible.

## Recipe: full-screen modal (sheet)

**Use for:** complex flows that don't fit in a centered modal but should still be modal (mobile editing flows, multi-step wizards, immersive tasks).

**Components:**
- Container: takes most or all of the viewport.
- Header: with title and close action.
- Body: scrollable content.
- Footer: actions if needed.
- Dismiss: typically explicit X or "Cancel" button (not always click-outside, since there's nothing outside to click).

**Considerations:** essentially a full-page replacement temporarily. Often used on mobile where there's no room for a centered modal.

## Cross-overlay patterns

**Stacking:** generally avoid overlay-on-overlay. If a modal needs to lead to another action, replace the modal content rather than opening a new modal. Exception: very specific cases like a date picker popover within a modal.

**Persistent vs. dismissible:** most overlays should be dismissible. Persistent overlays (that block until something happens) should be reserved for genuinely critical situations.

**Blocking vs. non-blocking:** modals block; toasts don't. Drawers can be either depending on whether the page beneath is interactive. Be deliberate about which pattern your overlay needs.

**Animation:** quick (200–300ms) and physically meaningful (slide from the edge it's anchored to; fade for centered overlays). Avoid elaborate animation.

## Anti-patterns

**Cookie banners as modals.** Cookie consent banners that block all interaction until acknowledged. Annoying and often illegal in some jurisdictions; consider less aggressive patterns.

**Marketing modals on first visit.** Aggressive newsletter signup or feature-promotion modals on the user's first visit. Damages first impression.

**Modals that disable scrolling on mobile.** Without explicit handling, opening a modal on mobile can leave the page scroll position locked weirdly.

**Tooltip-only critical information.** Important help text only available via hover. Mobile users can't hover; some keyboard users miss tooltips. Critical info should be always visible.

**Drawer that takes up almost the whole screen.** A drawer covering 90% of the viewport is essentially a modal but without the centering. Use the right pattern.

## Cross-reference

For figure-ground cues in general, see `figure-ground-cues`. For the parent principle, see `figure-ground-relationship`.
