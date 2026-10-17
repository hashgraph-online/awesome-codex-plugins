---
name: hicks-law-menus
description: 'Use this skill when designing menus, dropdowns, navigation, command palettes, or any interface where the user picks from a list. Trigger when the menu has more than ~7 items, when navigation feels overwhelming, when designing a cmd-K palette, when picking what goes in a "More" overflow, or when arguing about whether to add another menu item. Sub-aspect of `hicks-law`; read that first if you haven''t already.'
---

# Hick's Law in menus and navigation

Menus are the canonical Hick's Law surface — every item adds decision cost, and the structure of the menu determines whether that cost compounds or stays bounded. This skill covers the practical patterns for menus, dropdowns, navigation, and command palettes.

## The menu-size ladder

Different menu sizes call for different interaction patterns:

```
1–4 items     →  inline buttons, tabs, or segmented control (all visible)
5–8 items     →  dropdown menu, sidebar nav (scan-friendly)
9–15 items    →  grouped dropdown with section headings
16–50 items   →  searchable combobox / dropdown with type-to-filter
50+ items     →  command palette (cmd-K) or full-page browser with filters
```

Picking the wrong rung is the most common Hick's Law failure: a `<select>` of 200 timezones, a sidebar of 30 flat items, a context menu with every conceivable action.

## Top navigation

Top-level navigation should land at 5–7 items in left-to-right scripts. Beyond that, the eye can't hold the structure in working memory while picking.

If your IA naturally has more, group:

```
Sales | Marketing | Engineering | Finance | HR | Legal | Operations | IT | Facilities

→ regroups as

Departments | Projects | Reports | Settings
```

Where `Departments` opens a sub-menu with the 9 specifics.

The trade-off: sub-menus add a click. Worth it when the alternative is a wall of top-level items.

## Sidebar navigation

Sidebar nav can hold more items than top nav (scrolling and grouping help), but the same rules apply within each group. Aim for groups of 3–7 items.

```
Workspace
  Dashboard
  Projects
  Team

Personal
  Profile
  Notifications

Account
  Billing
  Security
  Sign out
```

Three groups, each with 2–3 items. Total 8 items, but the user reads it as "3 things" then "the right thing within."

## Dropdown menus (action menus)

A `DropdownMenu` triggered by a "more" button on a row, header, or toolbar. Common Hick's Law mistake: dumping every action into one menu.

Better:

- **Surface common actions inline** (icon-buttons in the row); reserve the menu for the long tail.
- **Group menu items** by purpose (Edit / Share / Move / Delete) with separators.
- **Put destructive actions at the bottom**, after a separator (Serial Position Effect: visually distant from common items, also remembered better).

```
[Edit]
[Duplicate]
[Move to…]
[Share]
─────────
[Archive]
[Delete]    ← red, after separator
```

The user scans top-to-bottom; the structure aids the choice.

## Command palettes (cmd-K)

The command palette is the modern answer to "we have hundreds of commands and can't surface them all." The pattern:

1. User presses `⌘K` (or types `/`).
2. A search input appears.
3. User types; results filter.
4. User presses Enter on a result.

This collapses Hick's Law — the user no longer scans a long list, they recall a name (or fragment) and the system shows matches. Combined with:

- **Recents** at the top (no typing required for recently-used commands).
- **Categorical groups** ("Actions / Navigation / Files / Help") so even un-typed exploration is structured.
- **Fuzzy matching** so partial recall ("invoic" matches "Create invoice") works.

Command palettes scale to hundreds of items because the interaction has changed.

## Mobile menus

Mobile bottom-nav: 3–5 items, no more. The thumb can't reach more than ~5 targets across the bar comfortably, and the screen has no room for labels at higher counts.

If your app needs more entry points than 5, the bottom nav holds 4 primaries plus a "More" tab that opens a sheet with the rest.

## Toolbars

Application toolbars (think Word, Figma, Notion's slash-menu) have the same Hick's Law problem at extreme scale. Strategies:

- **Tab the toolbar** (Office's ribbon: `Home / Insert / Layout / References / Mailings`). Each tab shows ~10 actions; total may be 80, but visible at any moment is one tab's worth.
- **Contextual toolbars** that show actions relevant to the current selection. The user never sees the irrelevant 90%.
- **Reserve the persistent toolbar for the 5–7 most-used actions across the entire app.**

## Anti-patterns

- **The "more is more" toolbar.** All actions visible all the time. Looks powerful, performs slow.
- **The flat 50-item dropdown.** A `<select>` with no grouping, no search. Hick's Law tax compounded by the lack of within-list navigation.
- **The context menu of doom.** Right-click reveals 25 actions, none separated, none grouped, including 3 destructive ones interspersed. Users learn to fear right-click.
- **The "everything's a tab" pattern.** A page with 8 tabs across the top. The user has to commit to one to see what's there; restructure as nav or sections.

## Heuristics

1. **Count the visible options.** On a glance, how many distinct things can the user pick? More than 7? Group, default, or hide the long tail.
2. **The fresh-user time-to-pick.** Watch a new user pick from your menu. Time it. >5 seconds suggests Hick's Law cost is too high.
3. **The category test.** Can you label every group of items with a single noun? If yes, your grouping is conceptually clean. If you find yourself reaching for "Misc," you have ungrouped items that need a home.

## Related sub-skills

- **`hicks-law`** (parent).
- **`hicks-law-defaults`** — for menus where one option dominates probability.
- **`hicks-law-pricing`** — for the menu of plan tiers as a conversion event.
- **`recognition-over-recall`** — the principle behind why command palettes work.
- **`chunking`** — the perceptual basis for grouping menu items.
