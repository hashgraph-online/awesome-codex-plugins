# Menu pattern library

A reference complementing `hicks-law-menus` with a broader pattern catalog and platform notes.

## Menu type by purpose

| Pattern | Best for | Example apps |
|---|---|---|
| Top horizontal nav | 5–7 primary destinations | Most marketing sites, GitHub |
| Sidebar nav (collapsible) | Complex IA, ≥ 8 destinations | Notion, Linear, Slack |
| Bottom tab bar (mobile) | 3–5 primary destinations | Most native iOS/Android apps |
| Hamburger drawer | Many low-frequency destinations | Mobile webs, Gmail mobile |
| Dropdown menu | 4–10 actions/links from a single point | Account menus, file menus |
| Mega menu | Wide content sites with many categories | Amazon, NYT |
| Command palette | 100+ commands, expert users | VSCode, Linear, Notion |
| Context menu (right-click) | Item-specific actions | File managers, IDEs |
| Action sheet (mobile) | Item actions; takeover popup | iOS Files, sharing menus |
| Toolbar | High-frequency formatting/actions | Word processors, design tools |

Pick by user frequency × number of items × form factor.

## Cross-domain examples

### Restaurant menus

Restaurant menus organize by course (appetizer, main, dessert) — a mix of Hick's Law mitigation (chunking) and convention. The fast-food drive-through menu (typically displayed above the order window) is constrained by readable distance; usually has 8–12 items grouped into 3–4 categories.

Software menus can borrow: chunk by purpose, label groups clearly, show only what fits the user's reading distance (or attention span).

### Library card catalogs

Pre-digital library card catalogs offered three search routes: by author, title, and subject. Three top-level menu items, each leading to alphabetical scanning. The Dewey Decimal classification system is itself a hierarchical menu tree.

The lesson: when content vastly exceeds menu capacity, route the user to a search/scan mechanism rather than enumerating all options.

### TV channel guide

Modern TV guides handle 200–500 channels by using grid layout (channel × time) rather than a list. Multi-dimensional categorization beats flat menus when categorization actually helps navigation.

## Platform-specific menu conventions

### macOS

- **Menu bar** at top of screen: persistent, application-specific. App developers expected to expose all functionality here for keyboard-shortcut discoverability.
- **Apple menu** (top-left): system-wide actions.
- **Status menus** (top-right): always-visible OS/app indicators.

### iOS

- **Tab bar** at bottom: 2–5 primary destinations.
- **Navigation bar** at top: title + back + actions (≤ 3 right actions).
- **Toolbar** at bottom: contextual actions for the current screen.
- **Action sheet**: modal popup for item-level actions.

### Android (Material)

- **Bottom navigation** (3–5 destinations) or **navigation drawer** (more, swipe to open).
- **App bar** at top.
- **Floating action button** (FAB) for the screen's primary action.
- **Bottom sheet** for item actions.

### Web

- No platform convention; many patterns coexist. The norm has shifted over time:
  - 2000s: top-nav with dropdowns.
  - 2010s: hamburger everywhere (overcorrection).
  - 2020s: persistent sidebar for app shells, sticky top for content sites, command palette as power-user backstop.

## Searchable vs. scannable

A menu becomes "searchable" when users type to filter; "scannable" when they read top-to-bottom.

- **Scannable** is faster for ≤ 7 items (no typing overhead).
- **Searchable** is faster for ≥ 20 items (collapses Hick's Law).
- The transition zone (8–20 items) depends on user proficiency: experts know what to type; novices scan.

The best modern menus support both: visible scannable items by default; type-to-filter when the user starts typing.

## Resources

- **WAI-ARIA Authoring Practices**, Menu and Menubar patterns.
- **Apple HIG: Menus**, **Material Design: Menus**, both publicly documented.
- **Refactoring UI** — chapter on menu and dropdown design.
