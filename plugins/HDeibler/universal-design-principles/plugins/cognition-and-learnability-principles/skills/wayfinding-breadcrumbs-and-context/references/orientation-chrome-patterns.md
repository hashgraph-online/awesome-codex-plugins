# Orientation chrome: pattern reference

A reference complementing `wayfinding-breadcrumbs-and-context` with a pattern catalog and history.

## Breadcrumb taxonomy

Three distinct breadcrumb types, often confused:

### Location breadcrumbs (most common)

Show the user's position in the IA hierarchy:

```
Home › Projects › Acme › Settings
```

Each segment is a real page; clicking goes "up" the tree. This is what most users mean by "breadcrumbs."

### Path breadcrumbs

Show the user's actual navigation history:

```
Dashboard › Search › Results › Project Acme › Settings
```

Mirrors browser history. Less common; can be useful for complex flows where users want to retrace their steps. Confusing if mixed with location breadcrumbs.

### Attribute breadcrumbs

Show the *filters* applied rather than the IA path:

```
All projects › Active › Owned by me › Q4 deadline
```

Common in faceted-search UIs (e-commerce category pages). Each segment is a filter the user can remove.

The three types serve different jobs; mixing them creates confusion. Pick one per surface.

## "You are here" indicators in nav

Every nav item that points to the user's current page should have a visible active state. Common patterns:

```css
/* Subtle background tint */
nav a[aria-current="page"] {
  background: var(--color-active-bg);
  color: var(--color-active-fg);
}

/* Left border (for sidebar nav) */
nav a[aria-current="page"] {
  border-left: 3px solid var(--color-brand);
  padding-left: calc(1rem - 3px);
}

/* Bold weight + underline (for top nav) */
nav a[aria-current="page"] {
  font-weight: 600;
  border-bottom: 2px solid var(--color-brand);
}
```

For sub-section pages, *both* the section and the sub-item should be marked: section has a section-level highlight; sub-item has a stronger highlight. This shows the user where they are at every level of the IA.

## URL design as wayfinding

URLs are wayfinding chrome that lives outside the rendered page. Patterns:

| URL style | Wayfinding signal | When it fits |
|---|---|---|
| `/projects/acme/notes/q4-plan` | Hierarchical; reflects IA depth | Content with a clear hierarchy |
| `/p/8f3c7a` | Opaque; ID-only | Stable IDs for objects, deep-linking |
| `/projects?team=acme&status=active` | State-bearing | Filtered views, search results |
| `/u/maria/timeline` | User-scoped | Per-user content (profiles, dashboards) |
| `/?modal=settings` | Modal-state in URL | Allows shareable links to modal-open states |

Hierarchical URLs are the strongest wayfinding signal but require URL changes when IA shifts. Opaque URLs are stable but uninformative. Most apps use a mix.

## Page title patterns

The `<title>` element appears in browser tabs, browser history, and search-engine results. It's wayfinding chrome that follows the page out into the user's environment.

A useful pattern:

```
[Specific Page] — [Section] — [Product]
```

Examples:

```
Q4 plan — Notes — Acme — MyProduct
Settings: Notifications — Acme — MyProduct
Dashboard — Acme — MyProduct
```

This puts specific information first (visible when tabs are narrow) and product name last (consistent across all tabs).

## Header chrome elements

The persistent app header carries wayfinding signals beyond navigation:

- **Workspace / org switcher.** For multi-tenant products, which workspace you're in is critical context.
- **Account / user indicator.** Confirms the signed-in user (avoids "I changed something on the wrong account").
- **Environment indicator.** "PROD" / "STAGING" / "DEV" — mission-critical for power tools.
- **Notification indicator.** Count of unread items as a soft "you have business elsewhere" signal.
- **Search input.** Always available; supports recovery from any wayfinding failure.

For products with multiple workspaces, the workspace indicator should be visually distinct enough that users can tell at a glance — color, name, or both.

## Mobile orientation patterns

Mobile compresses orientation chrome. Patterns:

### Stacked back-stack

iOS pattern: a "back" button at top-left names the parent ("← Acme"). Tapping returns to the parent. Builds a stack the user can unwind one level at a time.

### Bottom-tab persistent context

The currently-active tab is always indicated in the bottom nav, even when the user is deep in a sub-screen. Returns to root by tapping the active tab again.

### Pull-down navigation

Some apps (Twitter / X, Threads) use pull-down gestures to surface global navigation. Costs discoverability; suits power users.

## Wayfinding for keyboard users

Keyboard users navigate by tab order, focus, and shortcuts — not by clicking visible chrome. Wayfinding for them needs:

- **Visible focus indicators** (`:focus-visible` outlines) so they can see where they are.
- **Skip links** ("Skip to main content") that jump past nav chrome.
- **Predictable focus order** that matches the visual reading order.
- **Keyboard shortcuts for common navigation** (`g h` to go home, `g s` to go to settings — the GitHub pattern).
- **Focus restoration after modal close** so the user returns to where they were.

## Accessibility intersection

Orientation chrome that helps sighted users also helps screen-reader users — but only if marked correctly:

- `aria-current="page"` on the active nav item is announced.
- `<nav aria-label="Breadcrumb">` and `<nav aria-label="Main">` distinguish navigation regions.
- `<main>` and `<aside>` landmark elements let screen-reader users jump between regions.
- Page `<title>` is the first thing announced on page load.

A common bug: visual nav highlighting via class (`.active`) without the corresponding `aria-current`. The visual chrome works for sighted users; screen reader users get no signal.

## Cross-domain examples

### Wayfinding signs in airports

Airport signs often include the equivalent of a breadcrumb: "Concourse C → Gates C20–C40 → Gate C26." Each segment narrows the location. The same logic underlies software breadcrumbs.

### Address bars in browsers

The browser's URL address bar is the most-used wayfinding chrome ever built. It tells users where they are (URL), where they've been (history), and lets them go elsewhere (typing). Apps that hide or obscure URL information forfeit a major orientation tool.

### Mile markers on highways

Mile markers serve route-monitoring (you've traveled X distance) and orientation (you're at mile 247 in California). The "page X of Y" indicator in long flows or paginated docs is the same idea.

## Resources

- **Krug, S.** *Don't Make Me Think* — chapter on navigation and the trunk test.
- **NN/g** — many publicly available articles on breadcrumbs, page titles, and navigation indicators.
- **GOV.UK Design System** — example of orientation chrome at high quality.

## Closing

Orientation chrome is one of those design layers that's invisible when correct and brutal when missing. The user doesn't notice the breadcrumb that helps them; they notice the missing breadcrumb that doesn't. Building it well is mostly about consistency: same patterns, same locations, every page.
