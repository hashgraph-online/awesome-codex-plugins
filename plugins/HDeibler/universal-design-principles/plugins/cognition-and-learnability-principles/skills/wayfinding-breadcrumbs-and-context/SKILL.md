---
name: wayfinding-breadcrumbs-and-context
description: 'Use this skill when designing the orientation chrome that tells users where they are — breadcrumbs, current-page indicators, page titles, header context, "you are here" markers, parent-link affordances. Trigger when designing a multi-level IA, when users complain "I lost track of where I was," when reviewing whether to add or remove a breadcrumb, or when picking between navigation patterns for hierarchical content. Sub-aspect of `wayfinding`; read that first.'
---

# Wayfinding: breadcrumbs and "you are here" context

The orientation stage of wayfinding is largely served by the chrome a user sees on every page: the breadcrumb at the top, the highlighted item in the nav, the page title, the URL pattern. Done well, this chrome is invisible (the user just knows where they are). Done poorly, it forces the user to actively reconstruct their location every time they look up.

## What "you are here" chrome must do

Three jobs, on every page:

1. **Confirm location.** Where am I in the IA right now?
2. **Show parents.** What contains this page? How did I get here?
3. **Offer escape.** How do I go back up the tree?

Each job has standard patterns; combining them produces a complete orientation system.

## Breadcrumbs

Breadcrumbs are the most-cited orientation pattern: a horizontal path from the root to the current page.

```html
<nav aria-label="Breadcrumb">
  <ol>
    <li><a href="/">Home</a></li>
    <li><a href="/projects">Projects</a></li>
    <li><a href="/projects/acme">Acme</a></li>
    <li aria-current="page">Settings</li>
  </ol>
</nav>
```

### When breadcrumbs help

- **Hierarchical IA** with ≥ 3 levels of depth (e.g., e-commerce: Home › Electronics › Cameras › DSLR).
- **Documentation sites** with sectioned content.
- **Settings pages** that nest into sub-sections.
- **Deep app shells** where the user might forget how they got somewhere.

### When breadcrumbs are noise

- **Flat IA** (≤ 2 levels). A breadcrumb saying "Home › Profile" doesn't add information; the page title does the work.
- **Single-page apps with no hierarchical structure.** A breadcrumb on a Trello board is awkward — Trello's "spatial" model is the wayfinding chrome.
- **Mobile contexts** where horizontal space is precious. Often replaced by a "Back to ..." button that names the parent.

### Breadcrumb anti-patterns

- **Breadcrumb that doesn't match the URL.** "Home › Settings › Notifications" but the URL is `/u/3829/p/abc/n` — confusion.
- **Breadcrumb whose intermediate items aren't real pages.** Clicking "Projects" in the breadcrumb above should take you to a Projects index, not 404.
- **Breadcrumb showing the user's *path*, not the IA *hierarchy*.** "Home › Search Results › Project Acme › Settings" mixes navigation history with structure. Pick one.
- **Breadcrumb instead of a current-page indicator.** Breadcrumbs supplement nav highlighting; they don't replace it.

## Current-page indicator in primary nav

The user looks at the primary nav and sees one item highlighted: the current page (or current section).

```html
<nav>
  <a href="/dashboard">Dashboard</a>
  <a href="/projects" aria-current="page">Projects</a>
  <a href="/team">Team</a>
  <a href="/settings">Settings</a>
</nav>

<style>
  nav a[aria-current="page"] {
    background: var(--bg-active);
    color: var(--fg-active);
    font-weight: 500;
  }
</style>
```

`aria-current="page"` makes the indicator accessible to screen readers; CSS makes it visible.

For sidebar navs with sections and sub-items, both the section header and the current sub-item should have indicators — the user sees the section context as well as the specific page.

## Page titles

The page's `<h1>` and the browser tab's `<title>` are wayfinding chrome.

- **`<h1>`** confirms what page you're on. It should match the nav item that brought you here.
- **`<title>`** appears in the browser tab and in browser history. It should be descriptive enough to identify the page without context.

```html
<title>Q4 plan — Notes — Acme — MyProduct</title>
<h1>Q4 plan</h1>
```

The tab title shows the path from specific to general (current page → context → product); the H1 shows just the current page (since context is visible elsewhere on the page).

## URL patterns

The URL is wayfinding for power users and for shared/bookmarked links.

- **Hierarchical paths** (`/projects/acme/notes/q4-plan`) reflect IA depth. Each segment is a real, navigable level.
- **Flat slugs with no hierarchy** (`/p/8f3c7a`) are opaque. Useful for stable IDs; bad for orientation.
- **Search-state URLs** (`/search?q=q4+plan&filter=notes`) carry orientation about *what the user did*, not where they are in the IA.

The pragmatic rule: hierarchical URLs for content that has a hierarchy; opaque URLs for objects that don't (a chat message, a notification). Don't mix.

## Header context

The persistent app header carries orientation information beyond the nav:

- **The current workspace / organization name.** Important for users with access to multiple.
- **The current user's avatar / account menu.** Confirms which account they're signed in as.
- **The current environment** (production vs. staging) — critical for power-user safety.

```html
<header class="app-header">
  <a href="/" class="logo">MyProduct</a>
  <button class="org-switcher">Acme Inc ▾</button>
  <nav>...</nav>
  <button class="user-menu">
    <img alt="Maria Mendoza" src="/avatar/maria.jpg" />
  </button>
</header>
```

In settings or developer tools, an environment indicator ("PROD", "STAGING", "DEV") in a strong color belongs in the header — it's safety-critical orientation.

## "Back to ..." patterns

For pages that exist *below* a parent (a detail view of an item in a list), a "Back to ..." link at the top is more compact and sometimes more useful than a full breadcrumb:

```html
<a class="back-link" href="/projects/acme">
  ← Back to Acme
</a>
<h1>Q4 plan</h1>
```

This works well when the user came *from* the parent. It's less appropriate when the user landed on the detail directly (e.g., from a notification or shared link), because they may not have a clear "back" in mind.

## Mobile constraints

Mobile screens compress orientation chrome. Patterns:

- **Replace breadcrumbs with a single "Back" arrow** in the top nav, naming the parent ("← Acme").
- **Use the page title as the entire orientation.** Don't try to fit a multi-level breadcrumb on a 375px screen.
- **Bottom nav highlights the current section** rather than a sidebar showing all of them.

## Testing orientation chrome

The single most useful test: **the deep-link test.**

1. Open your app to a page deep in the IA — say, three levels down.
2. Note the URL.
3. Open it in a new browser window with no history.
4. Look at the page for 5 seconds.
5. Without scrolling, can you tell:
   - What page this is?
   - What section it belongs to?
   - How to get to the home page?
   - What the parent of this page is?

If yes to all four, your orientation chrome is working. If no, the chrome is too thin.

## Anti-patterns

- **The mystery URL.** Page at `/p/8f3c7a` with no breadcrumb, no nav highlight, no clear title. The user can't form a cognitive map even if they want to.
- **Two indicators in conflict.** The breadcrumb says "Settings" but the active nav item is "Profile." The user trusts neither.
- **Page titles that don't match nav labels.** Nav says "Documents," page title is "File Repository." Each rename is a mental-map cost.
- **Breadcrumbs to nowhere.** Clicking an intermediate level 404s because that intermediate page doesn't exist.
- **Headers without environment indication on multi-environment products.** A user runs a destructive script in prod thinking they're in staging.
- **No orientation on overlays.** A modal floats with no indication of what page is behind it; the user closes it and isn't sure where they are.

## Heuristics

1. **Glance test.** Land on a page; in 1 second, can you say its name? In 3 seconds, can you say its parent's name? In 5 seconds, can you say its grandparent? If the chain breaks somewhere, that level's chrome is missing or weak.
2. **Highlight audit.** Click through every nav item. For each destination, is the active state correctly highlighted? Stale or missing highlight is a common bug.
3. **Title parity.** Does every page's H1 match the nav label that points to it? Mismatches degrade trust.

## Related sub-skills

- **`wayfinding`** (parent).
- **`wayfinding-physical-spatial-metaphors`** — spatial metaphors set the high-level wayfinding model; breadcrumbs handle the per-page orientation.
- **`wayfinding-search-and-recovery`** — when orientation fails, search recovers.
- **`hierarchy`** (perception) — visual hierarchy on a page is page-internal wayfinding.
- **`recognition-over-recall`** — orientation chrome lets users recognize where they are; without it, they recall (slower, error-prone).
- **`visibility`** — chrome must be visible to do its job.
