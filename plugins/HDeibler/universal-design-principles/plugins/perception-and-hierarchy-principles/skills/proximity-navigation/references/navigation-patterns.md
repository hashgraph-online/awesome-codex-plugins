# Navigation patterns: cross-platform reference

A reference complementing `proximity-navigation` SKILL.md with deeper patterns and platform-specific conventions.

## Established navigation patterns

### Top navigation bar

Convention: 5–7 items at top, brand mark left, account/utility menu right. Used by virtually every web app. Works because:

- Users are habituated.
- Top edge has Fitts's Law advantage.
- Width permits text labels at typical viewports.

Limit: text labels become uncomfortable past 7 items at 1024px.

### Sidebar (left, persistent)

Convention: vertical stack of links/groups, often with icons. Used by web apps with deep IA (admin tools, productivity software, dashboards).

Trade-offs: takes 200–280px of horizontal space; provides "you are here" context; supports more items than top nav (groups + scroll).

Variations: collapsible (toggles between icon-only and icon+label) for power users who want screen space.

### Sidebar (right, contextual)

Used for properties panes, detail views, secondary navigation related to current selection. Different role from primary nav.

### Hamburger / drawer

Convention on mobile: hidden behind a menu icon (typically top-left), opens a sheet. Used because mobile screens can't fit persistent nav.

Trade-offs: hides navigation; users must remember it exists. Good for low-frequency nav items; bad for primary navigation. Hence the rise of bottom-nav for primary mobile destinations.

### Bottom tab bar (mobile)

Convention: 3–5 items at the bottom of mobile screens, primary navigation. Apple HIG and Material both endorse for primary destinations.

Trade-offs: limited to ~5 items (thumb reach + label width); always visible; combines edge advantage and thumb-reach advantage.

### Breadcrumbs

Used for hierarchical navigation showing the user's location and offering up-tree navigation. Best for deep IA (file systems, e-commerce categories, settings).

Pattern: small, low-contrast, separated by `/` or `›`. Current page is unlinked.

### Mega menu

A wide drop-down panel with grouped links, used for content-rich sites (e-commerce, news). Trades simplicity for breadth — accommodates many sections without forcing tab-by-tab navigation.

Risks: high cognitive load; only works when groups are clearly labeled and visually distinct.

### Command palette

`Cmd-K` invocation; type to filter; press Enter to execute. Originated in editors (Sublime, VSCode), now widespread in modern web apps (Linear, Notion, GitHub, Slack).

Doesn't replace navigation; complements it for power users who want fast keyboard access.

## Cross-domain examples

### Wayfinding signage (physical)

Airport, hospital, museum signage all use proximity to group destinations:

- Departures, Arrivals, Baggage Claim — three columns or three sections, with clear gaps.
- "This level" vs. "Other levels" sections.
- Line-color coding for transit transfers.

Software navigation can borrow: clear group labels, generous gaps, color coding for categorical distinction.

### Restaurant menus

A restaurant menu is hierarchical navigation: Appetizers, Mains, Desserts, Drinks. Within each: subgroups (Salads, Soups). Each item has a description and price.

Typical menu proximity ladder: tight pair (item name + description); medium gap (between items); large gap (between sections, often with section header).

Software nav follows the same structure: tight gap (link to nav-meta), medium gap (between links in a section), large gap (between sections).

### Book table of contents

A book's TOC is a navigation index. Structure:

- Part / Section (largest type, generous space above).
- Chapter (medium type, medium gap).
- Section within chapter (smaller, tighter gap, often indented).
- Page numbers right-aligned.

Software docs sites mirror this — collapsible TOC sidebars descend from book TOC conventions.

## Platform conventions

### iOS

- Tab bar at bottom for ≤ 5 primary destinations.
- Top navigation bar with title and back button (large title pattern in iOS 11+).
- Hamburger menus discouraged for primary nav.

### Android (Material)

- Bottom navigation for top-level destinations (3–5 items).
- Navigation drawer (left swipe) for many destinations.
- Top app bar.

### Desktop OS

- Menu bar at top of screen (macOS) or top of window (Windows).
- Toolbars beneath menu bar.
- Sidebar in many apps for navigation within document/project.

### Web

- No platform convention; many patterns coexist.
- Sticky top nav is the most common modern default for SaaS.
- Sidebar nav for app shells (Notion, Linear, Slack).

## Heuristics for choosing nav style

Pick based on:

1. **Number of primary destinations.**
   - ≤ 5 → top nav or bottom tabs (mobile).
   - 5–12 → top nav with sub-menus, or sidebar.
   - 12+ → sidebar with groups, or sidebar + command palette.

2. **Depth of IA.**
   - Flat (1 level) → top nav.
   - Hierarchical → sidebar with collapsible sections, or breadcrumb-driven.
   - Deeply hierarchical → tree view in sidebar.

3. **User proficiency.**
   - Casual / one-time → simpler, more visible nav.
   - Power users → command palette for everything; minimal visible nav.

4. **Form factor.**
   - Mobile → bottom tabs or hamburger.
   - Tablet → sidebar that collapses on rotation.
   - Desktop → persistent sidebar or sticky top.

## Anti-patterns

- **Mega menus on mobile.** They don't fit; they don't work touch-friendly.
- **Hamburger menus for primary nav on desktop.** Hides things that don't need hiding.
- **More than ~7 top-nav items.** Hick's Law cost stops being worth the visibility.
- **Inconsistent nav across sub-sections.** A section with custom navigation patterns disorients users.
- **Hidden nav with no escape hatch.** A drawer with no obvious close affordance.

## Resources

- **Material Design Navigation docs** — material.io.
- **Apple HIG: Navigation** — developer.apple.com/design.
- **NN/g: navigation patterns** — nngroup.com (multiple articles).
- **Refactoring UI** — ch. on navigation.
