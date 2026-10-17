---
name: wayfinding-search-and-recovery
description: 'Use this skill when designing search as the universal wayfinding recovery, or when designing for users who got lost — 404 pages, "results not found," "you''ve reached an unexpected page," empty states that should orient, and any moment where the user''s mental map has failed and the system must repair it. Trigger when designing global search, command palette, error pages, or recovery flows. Sub-aspect of `wayfinding`; read that first.'
---

# Wayfinding: search and recovery

Wayfinding fails. Users mistype URLs, follow stale links, click on a section that doesn't have what they thought it would, get teleported by a notification into a context they don't recognize. When wayfinding fails, the system has two jobs: (1) help the user find what they were after, (2) rebuild their orientation so they can navigate again on their own.

## Search as universal recovery

For complex apps, **search is the most reliable wayfinding repair tool the user has**. When the cognitive map breaks, the user types what they want and the system locates it. This works because:

- It collapses the user's failure to find through navigation into a single recall task.
- It surfaces results from across the entire IA, regardless of where the user currently is.
- Modern fuzzy matching handles typos and partial recall.
- It scales to IAs of any size without restructuring.

A robust search experience for wayfinding recovery has these properties:

### 1. Always reachable

Global search must be one keystroke or one click away from anywhere in the app. Common patterns:

- **`/` to focus search.** A long-standing convention from GitHub, Twitter, Slack.
- **`⌘K` / `Ctrl+K` to open command palette.** Newer; faster for power users; widespread in modern dev tools.
- **Persistent search input in the header.** Always visible; lower friction than keyboard shortcut.

```html
<header class="app-header">
  <input type="search"
         placeholder="Search anything (or press /)"
         id="global-search"
         aria-label="Search" />
</header>
```

### 2. Searches across the whole IA, not just one domain

A search that only finds documents (and not also settings, people, projects) is incomplete recovery. The user often doesn't know the *category* of what they want; they just know the name.

```
Results
  Documents
    "Q4 plan"
    "Q4 review notes"
  Settings
    "Quarterly notification frequency"
  People
    "Quentin Ramirez"
```

Categorical grouping in results restores the user's cognitive map even as it answers their query.

### 3. Shows location for each result

Each result should display where it lives in the IA — its breadcrumb. This serves two purposes:

- The user picks the right result (some have similar names).
- After clicking, the user knows where they're being taken — orientation begins before they arrive.

```html
<ul class="search-results">
  <li>
    <a href="/projects/acme/notes/q4-plan">
      <h3>Q4 plan</h3>
      <p class="path">Projects › Acme › Notes</p>
      <p class="snippet">Our Q4 plan focuses on three priorities...</p>
    </a>
  </li>
</ul>
```

### 4. Recents and suggestions

Empty search inputs should show recents (the user's frequent destinations) and suggestions (likely searches based on context). This makes search useful even before the user has typed anything.

### 5. Recovers gracefully from no-results

A "No results for 'qrt plnan'" page is the most common search-recovery moment. Patterns:

- **Suggest spelling corrections** ("Did you mean *q4 plan*?").
- **Show partial matches** ("Showing results for 'plan' instead").
- **Offer common starting points** ("Or browse: Recent / Pinned / Templates").

Never just say "no results" with no path forward.

## Lost-state pages: 404 and friends

A 404 (Not Found) page is the most common explicit wayfinding failure. The user followed a link or typed a URL and arrived nowhere.

A wayfinding-aware 404 does five things:

1. **States plainly what happened.** "This page doesn't exist." Not "Error 404" — the user doesn't care about the HTTP code.
2. **Explains likely causes.** "The page may have moved, the URL may be mistyped, or the content may have been removed."
3. **Offers recovery options.** "Search for what you were looking for: [search input]."
4. **Provides escape paths to known territory.** "Go to home" / "Go to your dashboard."
5. **Acknowledges the user's situation, not just the system's.** Skip the "Oops!" mascots; treat the user as someone trying to do something legitimate.

```html
<main class="error-page">
  <h1>This page doesn't exist</h1>
  <p>
    The link you followed may be broken, the URL may be mistyped,
    or the page may have been moved. Try searching for what you need:
  </p>
  <form action="/search">
    <input type="search" name="q" placeholder="Search..." autofocus />
    <button>Search</button>
  </form>
  <p>
    Or go to <a href="/">your dashboard</a>.
  </p>
</main>
```

For *internal* errors (500, service unavailable, timeout), the same wayfinding-recovery principles apply, but the apology and reassurance content shift slightly: it's the system's fault, not the user's URL. Still: state plainly, offer recovery, provide escape.

## Recovery from "I'm in the wrong context"

Sometimes the user isn't lost in URL space — they're lost in mental-model space. They opened a settings panel and don't recognize where they are; they navigated into a deep flow and forgot where it started.

Patterns that help:

- **Persistent breadcrumbs** showing the user's current depth and offering up-tree links.
- **"Back to ..." buttons** at the top of detail pages, naming the parent (not just an arrow).
- **Cancel / Close affordances on every modal/sheet/drawer** that return the user to a known state.
- **Esc key escape** from any overlay, popover, modal — keyboard recovery without thinking.

## Recovery from accidental destination

The user clicked a link they didn't mean to and arrived somewhere unintended. They need:

- **Browser back to work** (don't break it with single-page-app history mismanagement).
- **Visible "go back" affordance** in case they don't know browser back exists.
- **Stable URL** so they can copy it / bookmark it / share it / understand it.

If you've ever shipped an SPA where the back button leads to a confused state, you've created a wayfinding trap.

## The empty state as wayfinding

Empty states are wayfinding moments: the user arrived at a page expecting content, found none, and now needs orientation about what to do.

A wayfinding-aware empty state:

- Confirms they're in the right place ("This is your inbox. It's currently empty.").
- Suggests an action that makes the page useful ("Send your first invoice to see it here.").
- Doesn't punish the user for being early ("Welcome! Nothing here yet, and that's fine.").

## Anti-patterns

- **Search that only searches one domain.** If the user has to know which specific search to use, search has failed as wayfinding recovery.
- **404 pages with no escape.** A "404 Not Found" with a logo and nothing else is a dead end.
- **Mascots over function on error pages.** A cute illustration above unclear copy and no recovery path is decoration replacing function.
- **No recents in search.** Forcing the user to type their frequent destinations every time.
- **Broken back button.** SPAs that mismanage history; users lose their place and trust.
- **Modal traps.** Overlays that don't close on Esc, don't close on backdrop click, don't have a visible close button.
- **"You may also like" instead of recovery.** Recommendations on a 404 don't replace a search box and a home link.

## Heuristics

1. **The teleport test.** Drop yourself onto a random URL with no nav memory. Can you orient and recover within 10 seconds? If no, your recovery affordances are too thin.
2. **The broken-link test.** Type a deliberately-broken URL (`/nope-this-doesnt-exist`). What does the page do? Does it help you, or just say no?
3. **The "I forgot where I was" test.** Open a deep page, then a modal, then another modal. Close everything. Can you tell what page you're back on? If not, route monitoring failed.
4. **Search reach test.** Try to search for a setting from inside the search input. Does it find it? If not, search isn't a complete recovery tool.

## Related sub-skills

- **`wayfinding`** (parent).
- **`wayfinding-physical-spatial-metaphors`** — when spatial metaphors fail, search compensates.
- **`wayfinding-breadcrumbs-and-context`** — the orientation chrome that prevents recovery from being needed.
- **`recognition-over-recall`** — search results work because recognizing the right one is easy; recalling its path was hard.
- **`forgiveness`** (interaction) — recovery from wayfinding errors is part of forgiveness.
