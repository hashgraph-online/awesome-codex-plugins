# Frontend verification

Load the relevant sections only.

## Behavior

- Verify the primary user flow.
- Verify reachable loading, empty, success, validation, error, and disabled states.
- Confirm repeated actions do not create duplicate requests or stale state.
- Check navigation, refresh, and deep-link behavior when routing changes.

## Accessibility

- Prefer semantic elements before ARIA.
- Verify accessible names for controls and images.
- Use the keyboard for the complete interaction.
- Keep visible focus and restore focus after dialogs or route transitions.
- Connect form labels, help text, and errors programmatically.
- Confirm dynamic status changes are announced when necessary.
- Do not rely on color alone.

## Responsive layout

- Check the project’s supported breakpoints.
- Test long labels, localized text, missing images, and dense data.
- Look for overflow, clipped focus rings, fixed-height bugs, and unusable touch targets.

## Visual consistency

- Reuse spacing, typography, color, elevation, and motion tokens.
- Compare alignment and hierarchy with adjacent screens.
- Avoid adding a new pattern when an existing component covers the need.

## Browser health

- Inspect console errors and failed network requests.
- Verify hydration and server/client rendering behavior when applicable.
- Check interaction under slow or failed responses when tooling supports it.

## Evidence

Report which viewports, browsers, tests, and states were actually checked. Never imply a visual or browser check occurred when it did not.
