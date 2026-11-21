# App Quality and Theming

Read this reference for every user-visible app change. Functional tests are necessary; they do not prove that the product is understandable, polished, themed, responsive, or accessible.

## Define the experience before coding

For a material feature or new app, state:

- who the user is and the job they are trying to finish;
- the primary information and action on each screen;
- route/navigation hierarchy;
- expected data density and long-content behavior;
- the visual language to preserve, or a deliberate direction for a new app;
- loading, empty, error, validation, permission-denied, disabled, destructive, and success states.

Use this in the implementation plan. Do not default every problem to a generic dashboard, interchangeable cards, excessive borders, or decorative chrome. Make the primary task and current status legible at a glance.

## Use the Bifrost design foundation

Start from the scaffolded Tailwind v4 and shadcn token layer. Prefer semantic utilities:

- `bg-background` / `text-foreground`
- `bg-card` / `text-card-foreground`
- `bg-muted` / `text-muted-foreground`
- `border-border`
- `bg-primary` / `text-primary-foreground`
- `text-destructive`

Use the app's local shadcn components consistently instead of rebuilding basic buttons, inputs, dialogs, tabs, or menus with one-off markup. Establish a compact type and spacing hierarchy, then repeat it.

Avoid hardcoded light-only utilities such as `bg-white`, `text-slate-*`, and `border-gray-*` for ordinary surfaces. Intentional brand and data-series colors may be custom, but define paired light/dark variables and verify contrast.

## Treat theme support as a contract

`supportsTheme` on `BifrostProvider` is an app-wide capability declaration. It exposes the host theme control and applies the root `.dark` class; it does not theme the app automatically.

Keep `supportsTheme` only when all of these work in both modes:

- every route and layout surface;
- navigation, menus, dialogs, sheets, popovers, and tooltips;
- inputs, disabled controls, validation, and focus rings;
- tables, charts, badges, and status colors;
- loading, empty, error, and success states.

If full support is outside scope, remove `supportsTheme` rather than shipping a toggle that themes only the header.

## Design every state

For data-backed views:

- Show intentional loading structure without moving the whole layout.
- Explain empty state and provide the next useful action.
- Render actionable errors without discarding usable page context.
- Make success visible and update stale data.

For mutations:

- expose progress and disable accidental duplicate submission;
- preserve user input when recovery is possible;
- confirm destructive actions in proportion to their consequence;
- distinguish validation, permission, missing-resource, and server failures when the user can act differently.

## Layout and responsiveness

A V2 app owns the whole viewport: the host mounts it in a full-height, non-scrolling region and draws no navigation around it, so the app provides its own nav shell and its own scrolling (see `best-practices/apps.md`). The root must fill the available mount, while individual lists and panels should remain content-sized until constrained.

- Keep fixed headers and metadata outside the scrolling region.
- Put `overflow-auto` on the content region that can actually grow.
- Use `min-h-0`/`min-w-0` where a flex child must shrink.
- Avoid forcing short content into an unnecessary full-height scroller.
- Test narrow widths, long labels, large result sets, empty content, and zoom.

Use responsive priority rather than shrinking everything: preserve the primary action and content, collapse secondary controls, and let dense tables become an intentional mobile alternative when necessary.

## Accessibility

- Use semantic headings, landmarks, buttons, links, labels, and table structure.
- Ensure every control works by keyboard and has a visible focus state.
- Give icon-only controls accessible names.
- Associate validation messages with their fields.
- Maintain readable contrast in both themes and do not rely on color alone for status.
- Manage focus when dialogs open/close and when an action materially changes the page.

## Rendered acceptance

Preview the actual app and inspect representative data. For every changed route:

1. Complete the primary workflow.
2. Trigger the important empty/error/validation states.
3. Toggle light and dark when supported.
4. Check narrow and wide layouts, overflow, keyboard navigation, and focus.
5. Correct visible hierarchy, spacing, clipping, contrast, inconsistency, and unclear copy.

Do not mark an app complete from source review, compilation, or automated tests alone. State the routes, states, viewports, and themes actually checked in the final handoff.
