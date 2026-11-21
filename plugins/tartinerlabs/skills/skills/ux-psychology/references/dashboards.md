# Dashboards and Admin Panels

How the rules apply to the signed-in home of a product and the pages around it — a SaaS dashboard, admin panel, analytics view, or internal tool. The user is a repeat visitor who arrives to check the state of something and then act on it. Load this alongside the platform guide (usually `references/web.md`).

## One Job per Dashboard

Few (*Information Dashboard Design*, 2006) defines a dashboard as the most important information needed to reach an objective, on one screen, readable at a glance. A dashboard that shows everything the product knows fails that definition: every extra card is one more thing to scan past (`rules/cognitive-load.md`).

- **Name the question the user arrives with**, and put its answer in the top position — the status of their projects, their balances, the items they manage. What sits there is a statement about what matters most in the product
- **Overview first, detail on demand** — Shneiderman's mantra ("The Eyes Have It", 1996): overview, then zoom and filter, then details. The home screen summarises; the full table, the full report, and the single item live one click away (`rules/progressive-disclosure.md`)
- **Managing or monitoring?** A product where people work on objects (links, invoices, tickets) leads with the list of those objects and keeps metrics below. A product where people watch numbers leads with the metrics
- **A page header that stays put** — the page title, the scope controls (workspace, date range), and the page's one primary action ("New invoice") in the same place on every page (`rules/von-restorff.md`, `rules/jakobs-law.md`)
- **A strict grid** — dashboards use most of the screen, so cards align to shared columns and a few row heights. Density runs higher than on a marketing page: smaller type with fewer size steps, tighter spacing (`references/web.md` covers when density is right)
- **Design the empty state with the layout** — a list that can show "nothing yet, here is how to add the first one" is easier to get right than a grid of blank cards (`rules/microcopy.md`)

## The Sidebar

The sidebar holds what is global and persistent: navigation, the account or workspace switcher, and often search. NN/g ("Left-Side Vertical Navigation on Desktop", 2021) found a left-hand vertical list scales to more items than a top bar and is located with fewer eye fixations.

- **An icon and a short label on every link** — the icon speeds recognition on return visits, the label removes the guessing; together they let the sidebar collapse to icons with tooltips (`rules/signifiers.md`)
- **Group links by what belongs together**, with a small heading per group once there are more than about seven (`rules/gestalt-grouping.md`, `rules/hicks-law.md`)
- **Rarely used links go to the bottom** — settings, help, documentation — where convention says to look for them (`rules/jakobs-law.md`)
- **A visible active state**, shown with two cues (background and weight, or an indicator bar and colour) so it survives a glance
- **Nest only when the list outgrows the screen**, and keep nesting to two levels; a deep tree hides where things are
- **Counts and "New" chips only when they call for action** — an unread count the user will clear, not a decoration (`rules/cognitive-load.md`)
- **Promotions and announcements in the sidebar read as ads** and are skipped (banner blindness, `rules/scanning.md`). At most one, dismissible, and never the only place important news appears
- **Small screens** — the sidebar becomes the platform's own navigation (tab bar, drawer), and cards stack in priority order

## Charts

Cleveland & McGill (1984, *Journal of the American Statistical Association*) found people judge position along a common scale and length most accurately, and angle and area worst. NN/g ("Dashboards: Making Charts and Graphs Easier to Understand") draws the same conclusion for dashboards: length and 2D position communicate quantity fastest; gauges take more space and are harder to read.

- **A line for change over time, bars for comparing categories.** Reach for a pie, donut, gauge, or radial chart only for a simple part-of-whole with two or three slices; decorative or novel chart shapes make the reader decode the chart before the data
- **Axis labels, units, and light gridlines** — the parts most often left out, and the ones that let a value be read at all
- **A summary number above the chart**, with its comparison ("1,204 clicks, +12% vs last week") — most visits end at that number (`rules/cognitive-load.md`)
- **A date range the user can change**, shown on the chart or once for the whole page; charts side by side that silently use different ranges invite wrong comparisons
- **Name the categories directly** — a label or recognisable icon beside each bar rather than a legend to match by colour
- **Hover adds precision**: the exact value at the pointer, the other series dimmed. The chart must still be readable without it (`references/web.md`, pointer and hover)

## Where an Action Opens

A dashboard that only displays is a report. Each action needs a surface sized to its context:

| Surface | Use when | Behaviour |
|---|---|---|
| Popover | The context is small and the change is safe — display settings, a filter, a quick pick | Non-blocking: clicking away closes it with no consequence |
| Modal | A short, self-contained task tied to the page behind it — creating an item for the list on screen | Blocking: explicit confirm and cancel; closing keeps or asks about entered data (`rules/error-prevention.md`) |
| Side panel | Inspecting or editing one row while the list stays in view | Non-blocking; the list remains usable |
| New page | The context is large or lasting — an existing item's detail, a settings area | Its own URL, plus a back link or breadcrumb to where the user came from |

Modals interrupt, add a dismissal step, and hide the content they relate to (Fessenden, "Modal & Nonmodal Dialogs", NN/g 2017), so use the lightest surface that fits. Because a modal covers the page, confirm its result when it closes: the new item appears in place, with a brief confirmation.

## Feedback After an Action

- **Toasts confirm what just happened** — "Link created", "3 items archived" — and carry Undo for reversible actions (`rules/error-prevention.md`). Announce them to assistive technology as status messages (WCAG 4.1.3)
- **Errors that need fixing stay where the problem is**, inline and persistent. A toast that disappears takes the instructions with it; keep toasts for failures the user only needs to know about, and never make a toast button the only route to an action
- **Optimistic updates keep the tool fast** — remove the deleted row at once and roll back with a message if the request fails (`rules/system-status.md`)
- **Spend interruptions sparingly** (`rules/cognitive-load.md`)

## Lists and Tables

NN/g ("Data Tables: Four Major User Tasks", Laubheimer 2022) names what people do with a table: find records that match criteria, compare values, view or edit one row, and act on records. Displaying the data covers only part of that.

- **Search, filter, and sort** once a table can outgrow one screen
- **Bulk actions appear on selection** — selecting rows reveals a contextual bar with the count and the actions, so the controls are absent until they apply (`rules/progressive-disclosure.md`)
- **Home-screen lists stay short**: the few fields that identify an item and its state, with the full table one click away
- **Separate rows one way** — spacing, dividers, or alternating tint — not all three (`rules/gestalt-grouping.md`)

`references/web.md` covers table mechanics (sticky headers, number alignment, row actions, long operations).

## Tabs

In-page tabs give related views of the same thing without adding sidebar entries — an item's overview, activity, and settings. NN/g ("Tabs, Used Right", 2024) sets the limits:

- Tabs hold views the user does not need to compare; content compared across tabs belongs on one page
- Few tabs, short labels, one row; the default tab holds what most visits need, since the others are often never opened
- Do not mix tabs that switch a panel with tabs that navigate elsewhere in one control

## Build the Rest From the Same Parts

Most pages in a dashboard are combinations of four parts: lists and tables, cards, forms, and tabs. Solve each once and reuse it — the same table controls, card padding, form layout, and tab style on every page — so a user who has learned one page has learned the product (`rules/jakobs-law.md`).

## Neighbouring Skills

This guide decides what a dashboard shows, where, and how it responds. When installed, defer to:

- a **visual-design skill** for the type scale, colour, and card treatment (border or fill)
- a **data-visualisation skill** for chart colours and mark styling
- an **animation skill** for the timing of hover, toast, and chart transitions
