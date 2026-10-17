---
name: proximity-navigation
description: 'Use this skill when designing or fixing navigation — sidebars, top nav, footer nav, mobile menus, breadcrumbs, tab bars, command palette groupings. Trigger when grouping related links, deciding when to add section dividers, fixing a sidebar where every link feels like a separate item, or designing a mobile bottom-nav with multiple action groups. Sub-aspect of `proximity`; read that first if you haven''t already.'
---

# Proximity in navigation

Navigation is a sequence of links where some belong to the same group and others to different groups. Proximity is the cheapest way to communicate the structure — far cheaper and lighter than dividers, sub-headers, or color shifts.

## The navigation proximity ladder

```
Inside a section: gap-1   (4px) between adjacent links
Between sections: gap-6   (24px) — visibly larger
Section heading:  closer to its first link than to the previous section
```

Keep the inside-section gap tight. Aggressive whitespace inside a sidebar wastes vertical space and makes the eye treat each link as its own region.

## Sidebar with grouped sections

```html
<nav style="display: grid; gap: 1.5rem; padding: 1rem;">
  <div style="display: grid; gap: 0.125rem;">
    <p class="nav-heading">Workspace</p>
    <a class="nav-link" href="/dashboard">Dashboard</a>
    <a class="nav-link" href="/projects">Projects</a>
    <a class="nav-link active" href="/team">Team</a>
  </div>

  <div style="display: grid; gap: 0.125rem;">
    <p class="nav-heading">Personal</p>
    <a class="nav-link" href="/profile">Profile</a>
    <a class="nav-link" href="/notifications">Notifications</a>
  </div>

  <div style="display: grid; gap: 0.125rem;">
    <p class="nav-heading">Account</p>
    <a class="nav-link" href="/billing">Billing</a>
    <a class="nav-link" href="/security">Security</a>
  </div>
</nav>

<style>
  .nav-heading {
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: hsl(0 0% 50%);
    padding: 0 0.5rem;
    margin-bottom: 0.25rem;       /* slightly closer to its first link */
  }
  .nav-link {
    padding: 0.375rem 0.5rem;
    border-radius: 0.25rem;
    font-size: 0.875rem;
    color: hsl(0 0% 25%);
    text-decoration: none;
  }
  .nav-link:hover { background: hsl(0 0% 96%); }
  .nav-link.active { background: hsl(0 0% 92%); font-weight: 500; }
</style>
```

Three sections, no dividers. The 24px gap between sections is unmistakably looser than the 2px gap between links. Section headings recede in tone (uppercase + small + grey) so they don't compete with the links.

## When to add a divider

If sections need *more* separation than proximity alone provides — typically when:

- Sections are conceptually very different (workspace links vs. account/sign-out).
- The sidebar is short (3–4 sections) and you want a strong visual rhythm.
- A sub-section of links is visually similar enough to its parent that proximity alone won't differentiate.

Use the lightest divider that does the job:

```html
<hr style="border: 0; border-top: 1px solid hsl(0 0% 90%); margin: 0;" />
```

Resist heavy dividers (2px, dark colors) — they read as walls.

## Mobile bottom nav

Bottom nav with 3–5 primary destinations should bind tightly horizontally:

```html
<nav class="bottom-nav">
  <a href="/feed"><HomeIcon /><span>Home</span></a>
  <a href="/search"><SearchIcon /><span>Search</span></a>
  <a href="/post"><PlusIcon /><span>New</span></a>
  <a href="/inbox"><InboxIcon /><span>Inbox</span></a>
  <a href="/me"><UserIcon /><span>You</span></a>
</nav>

<style>
  .bottom-nav {
    position: fixed; bottom: 0; left: 0; right: 0;
    display: grid; grid-template-columns: repeat(5, 1fr);
    border-top: 1px solid hsl(0 0% 88%);
    background: white;
    padding: 0.5rem 0 calc(0.5rem + env(safe-area-inset-bottom));
  }
  .bottom-nav a {
    display: grid; gap: 0.125rem; justify-items: center;
    font-size: 0.625rem;
    color: hsl(0 0% 40%);
  }
  .bottom-nav a[aria-current="page"] { color: hsl(220 90% 50%); font-weight: 500; }
</style>
```

The icon and label are tightly bound (2px gap). The five items distribute equal space across the bar. No dividers; the equal distribution is the proximity signal that they're a peer group.

## Breadcrumbs

Breadcrumbs are a rare case where proximity is more uniform — each segment is a separate jump, but they're conceptually a continuous path:

```html
<nav aria-label="Breadcrumb">
  <ol style="display: flex; gap: 0.5rem; align-items: center; list-style: none; padding: 0;">
    <li><a href="/projects">Projects</a></li>
    <li aria-hidden style="color: hsl(0 0% 60%);">/</li>
    <li><a href="/projects/acme">Acme</a></li>
    <li aria-hidden style="color: hsl(0 0% 60%);">/</li>
    <li aria-current="page">Settings</li>
  </ol>
</nav>
```

Equal gaps between segments. Separators (`/`) live in the gap, recessed in tone. The current page is unlinked and slightly heavier — the only proximity *break* is the recessive separator.

## Command palette groupings

A `cmd-K` palette typically shows actions grouped by category. Proximity holds groups together:

```
Recent
  Create invoice
  Open settings

Actions
  Search
  Invite teammate
  Export workspace

Navigation
  Go to dashboard
  Go to projects
```

Each group has a lightly-styled heading (small, uppercase, low contrast). Within each group, items are tightly stacked. Between groups, looser spacing. No dividers needed.

## Anti-patterns

- **Equal-spaced sections.** Sidebar with sections at the same gap as items inside sections. The eye reads it as one long list, not multiple groups.
- **Heavy dividers between every section.** A sidebar with `<hr>` between every group looks like a form. Use space first; dividers only when space alone is insufficient.
- **Section headings as items.** A sidebar where the section heading is styled like a link. Users try to click it. Style headings distinctly (smaller, uppercase, lower contrast, non-clickable cursor) so they read as labels.
- **Nested-tree creep.** Every link nested under a parent, with indentation creating proximity confusion. Flat structure beats deep nesting in nav.

## Heuristics

1. **Read groups aloud.** "Workspace: Dashboard, Projects, Team." If you can hear the pause between groups, proximity is working.
2. **Compress test.** Reduce the section gap to half. If the structure becomes unclear, you needed that gap. If it's still clear, your sections were over-spaced.
3. **No-divider test.** Remove all dividers. If structure collapses, proximity wasn't doing the work and you were over-relying on chrome.

## Related sub-skills

- **`proximity`** (parent).
- **`proximity-form-fields`** and **`proximity-data-tables`** — same principle in different layouts.
- **`hicks-law`** (cognition plugin) — reducing the count of nav items matters more than how they're grouped; pair this skill with that one.
- **`signal-to-noise-ratio`** — nav is a primary case for SNR discipline; keep chrome minimal.
