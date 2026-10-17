---
name: figure-ground-overlays-and-modals
description: 'Apply figure-ground separation specifically for overlays — modals, dialogs, drawers, popovers, dropdowns, toasts. Use when designing or auditing the moments when a UI element appears over the underlying page and needs to clearly come forward. The most common figure-ground design problem; getting it right means users naturally focus on the overlay, getting it wrong means modals blur into the page or feel jarring.'
---

# Figure-Ground — overlays and modals

The most common figure-ground design problem in modern UI: an element appears over the underlying page and needs to clearly come forward. Modals, dialogs, drawers, popovers, dropdowns, toasts, tooltips, lightboxes — all are overlays that need to win the figure-ground sorting against the page beneath.

When the figure-ground separation is clear, users naturally focus on the overlay; the page recedes. When it's unclear, users may not notice the overlay, or they may be uncertain about whether to focus on the overlay or the page.

## Anatomy of a well-designed modal

A modal that wins figure-ground separation typically uses several cues together:

**1. Scrim.** A semi-transparent overlay (40–60% opacity black, typically) between the modal and the page. The scrim does several jobs: visually separates the modal from the page, mutes the page's color and detail, and indicates that the page is currently inactive.

**2. Elevation (shadow).** The modal has a prominent drop shadow (16–24px blur, low opacity), suggesting it's sitting above everything else.

**3. Background.** The modal's background is sharp and solid (typically white in light mode, slightly elevated dark gray in dark mode), in clear contrast with the scrim.

**4. Close affordance.** A clear way to dismiss (X in the corner, button, escape key, click outside on the scrim). Users need to know how to return to the page.

**5. Focus trap.** Keyboard focus is contained within the modal until it closes. Tab key cycles through the modal's interactive elements; tab doesn't escape to the page beneath.

**6. ARIA roles and labels.** The modal is announced as a modal; screen readers know to focus on it.

When all these align, the modal is clearly figure, the page clearly ground, and the user can interact with the modal without confusion.

## Common modal failure modes

**No scrim.** The modal floats over the page with no visual separation. The page is still visible at full strength; the figure-ground separation is weak.

**Scrim too light.** A scrim at 10% opacity that's barely perceptible. The visual cue isn't strong enough to push the page into ground.

**Modal too subtle.** A modal with no shadow, no border, light gray background that blends with surrounding gray UI. The modal doesn't read as elevated.

**No clear close.** Users can't figure out how to dismiss the modal. They click around looking for the exit. The modal becomes an interruption rather than a focus point.

**Focus not trapped.** Tab key escapes the modal and starts cycling through the page beneath, leading to confusion about where focus is.

**Multiple modals stacked.** A modal opens, then another opens on top of it. The figure-ground sorting becomes ambiguous (which modal is figure?), and users can lose track of state.

**Inconsistent modal styles.** Different modals in the same product use different scrim opacities, different shadows, different close patterns. Users can't form expectations.

## Variations: drawers, popovers, dropdowns

Different overlay types have different figure-ground requirements.

**Drawers (side panels).** Slide in from one edge of the screen. The page beneath is partially visible (drawer doesn't cover the whole screen). Use scrim to push the visible page area into ground. Drawer itself uses elevation (shadow on the inner edge) to come forward.

**Popovers (small overlays attached to a trigger).** Smaller than modals, attached to a specific UI element (a button, a link). Scrim is usually unnecessary — the popover is small and obviously associated with its trigger. Use elevation (shadow) to come forward.

**Dropdowns (menus expanded from a control).** Similar to popovers but specifically a list of options. Elevation cue alone is usually enough; no scrim. The dropdown should clearly close when the user clicks outside or selects an option.

**Toasts (transient notifications).** Brief overlays that appear and dismiss themselves. High elevation (shadow) makes them clearly above other content. No scrim — the page beneath should remain interactive. Toast colors usually distinct (success green, error red, info blue).

**Tooltips (very transient overlays on hover).** Lowest elevation among overlays — they're informational, not action-requiring. Subtle shadow or border is sufficient.

**Lightbox (full-screen image viewer).** Maximum scrim (often pure black) because the image needs full attention. The image is the only figure; everything else is hidden.

Each type has its own figure-ground recipe based on its purpose.

## Worked examples

### A confirmation dialog

User clicks "Delete account." A modal opens:

- Scrim at 50% opacity black covers the page.
- Modal centered, white background, 600px wide, with prominent shadow.
- Headline: "Delete your account?"
- Body: "This will permanently delete your account and all associated data. This cannot be undone."
- Two buttons: "Cancel" (secondary) and "Delete account" (destructive primary, red).
- X close button in upper-right.
- Click on scrim or escape key dismisses (canceling).

Figure-ground is unambiguous. The modal commands attention; the page is clearly inactive. The user can make the decision without distraction.

### A dropdown menu

User clicks "User settings" in the nav. A dropdown opens below the trigger:

- No scrim (page remains active).
- Dropdown has subtle shadow (4px blur) and 1px border.
- Background white; menu items inside.
- Click outside dismisses.
- Escape key dismisses.

The dropdown clearly comes forward through elevation but doesn't dominate; the user can dismiss easily and continue with the page.

### A side drawer

User clicks "Settings" icon. A side drawer slides in from the right:

- Drawer takes 400px on the right side of the screen.
- Visible page area to the left of the drawer is darkened with a scrim.
- Drawer has shadow on its left edge (where it meets the visible page).
- Drawer background white; settings content inside.
- Click on scrim, X button, or escape dismisses.

The drawer is figure within its layer; the visible page area is clearly secondary; the user knows where to focus.

### A toast notification

User saves a document. A toast appears:

- Toast positioned in lower-right of screen.
- Toast has prominent shadow and rounded background.
- Background green (success color); text in white.
- Auto-dismisses after 4 seconds, or user can click to dismiss.
- No scrim (page remains active and interactive).

The toast is figure briefly, then disappears. The page never becomes ground; the user can continue working uninterrupted.

### A failure: modal without scrim

A modal opens but no scrim is added. The page is fully visible behind the modal. Users see the modal but also see the page; figure-ground is ambiguous. They sometimes click on the page (thinking they're interacting) and miss the modal entirely.

The fix: add a scrim. Even a light one (40% opacity) dramatically improves figure-ground separation.

## Anti-patterns

**Modals without scrim.** As above, the modal blurs into the page.

**Modals that auto-dismiss while user is reading.** A modal that times out is an interruption that ended before users could engage.

**Stacked modals.** Modal A opens; from Modal A, the user triggers an action that opens Modal B. Now there are two modals; figure-ground is ambiguous; state is hard to track. Avoid stacking modals; replace one modal with another or use a non-modal pattern.

**Modal animations that are too slow or too theatrical.** A modal that takes 800ms to slide in feels sluggish; a modal with elaborate effects feels distracting. Quick (200–300ms) and clean is best.

**Click-outside dismissal that loses user data.** A user has typed in a form modal and accidentally clicks outside; the modal dismisses and their input is lost. Either confirm dismissal when there's unsaved input, or don't allow click-outside to dismiss for input-containing modals.

**Inconsistent overlay patterns.** Different drawers in the same product behave differently; some have scrim, others don't; some close on click-outside, others don't. Codify the patterns.

**Tooltips that act like modals.** A tooltip that requires the user to click to dismiss, blocks page interaction, or contains a lot of content. Tooltips should be lightweight; if you need more, use a popover or modal.

## Heuristic checklist

For every overlay you ship, ask: **Does it have appropriate figure-ground separation from the underlying page?** Test by glancing — what stands forward? **Are the cues (scrim, elevation, shadow) calibrated to the overlay type?** Modals get more; toasts get less. **Is the close path clear?** Users should always know how to dismiss. **Is focus managed correctly?** Tab should be trapped in modals; not in toasts. **Does the overlay match the patterns established elsewhere in the product?** Inconsistency confuses users.

## Related sub-skills

- `figure-ground-relationship` — parent principle on figure-ground perception.
- `figure-ground-cues` — sibling skill on the specific visual cues.
- `forgiveness` — modal dismissal patterns interact with forgiveness (don't lose user input on accidental dismiss).
- `feedback-loop` — toasts are feedback; their figure-ground supports their feedback role.
- `accessibility` — overlays have specific accessibility requirements (focus trap, ARIA, escape key).

## See also

- `references/overlay-recipes.md` — specific design recipes for each overlay type.
