# Layout rules: where things go on a Mini App screen

Where the image sits and in what ratio, the order of title, meta, price, rating and availability, which card
variant a content type uses, how galleries, filters, forms, booking and plans are laid out. The rules have
ids (L01-L25) so a review can cite them, and a machine-readable twin:

```bash
py -3 scripts/miniapp_layout.py entities              # content types and their list variant and image ratio
py -3 scripts/miniapp_layout.py show trainer          # recommended card, detail order, MainButton text, markup
py -3 scripts/miniapp_layout.py review screen.json    # findings with rule ids and fixes
py -3 scripts/miniapp_layout.py example catalog       # a screen description to start from
```

Data: `data/mini-apps/layouts.json`. Live examples: `examples/mini-apps/catalog` (books, trainers,
workouts), `examples/mini-apps/vanilla` (menu), `examples/mini-apps/portfolio` (dashboard), the kit gallery.
These rules are **[Heuristic]**: built on Telegram's design guidelines, the iOS 27 proportions in
[design-sources.md](design-sources.md) and common commerce and booking practice; they are checked on mock
previews, not on user research. A project's own research beats them.

## 1. Card variants

| Variant | Anatomy | Kit | Use for |
|---|---|---|---|
| Row | thumbnail at the start · title · meta · value at the end | `.tma-cell` + `.tma-row-thumb` | people, services, menus, search results, history, schedules |
| Media card | full-width media on top · title · meta | `.tma-tile.is-wide` | events, courses, articles, workouts, listings |
| Grid tile | media on top · title (2 lines) · meta · price | `.tma-grid` > `.tma-tile` | products, books, workout collections |
| Scroller card | a tile in a horizontal row | `.tma-carousel` > `.tma-tile` | featured and related only (L10) |
| Plan card | name · price and period · 3-5 features | `.tma-card.tma-plan` + `.tma-checks` | SaaS plans, memberships |

## 2. Image ratio and position by content type (L02, L03, L04)

| Content | List variant | Image | Fit | Row thumbnail |
|---|---|---|---|---|
| Physical product | grid tile | 1:1 (4:5 for fashion) | cover; contain for packshots on white | 56 square |
| Book | grid tile | 2:3 cover | **contain** (never crop a cover) | 48 × 72 |
| Trainer, specialist | row | 4:5 portrait in cards and detail | cover, face centred | round 48-56 |
| Workout, video lesson | media card | 16:9 with duration badge | cover | 96 × 54 |
| Group class | row | none: the time leads | — | time column |
| Event, ticket | media card | 3:2 | cover | 56 square |
| Course | media card | 16:9 | cover | 96 × 54 |
| Listing (rental, property, car) | media card | 4:3 carousel | cover | 56 square |
| Service | row | 1:1 | cover | 56 square |
| Menu item (food, drink) | row | 1:1 photo **at the end** | cover | 64 square at the end |
| Article, news | row | 16:9 in cards | cover | 72 square at the end |
| Person (community, CRM) | row | round avatar | cover | round 40-48 |
| Photo in a gallery | grid of 3 | 1:1 in the grid, original in the viewer | cover / contain | — |

Rules: one ratio across a list; logos, covers, documents and packshots are contained on a surface, photos are
cropped; media cards and tiles put the image on top at full width; rows put the thumbnail at the start
(menus and articles may put it at the end); never an image on both sides; alt text names what is shown
(L22).

## 3. Text order in cards (L05, L06, L07, L08, L17, L18)

1. **Title** first, 2 lines at most in cards, 1 in rows (articles may take 3), ellipsis.
2. **Meta**: one line in hint colour, dot-separated (`Mira Kovac`, `Strength · 8 years`,
   `Beginner · 20 min · No equipment`).
3. **Price** under the meta in headline weight, tabular figures, the user's locale
   (`Intl.NumberFormat`): `€12.90`; an old price struck through after it (`€18.50 €24.00`); `from €25` when
   it varies; the period after it (`€12 / month`); Stars as `⭐ 250`, grams as `12.5 GRAM`
   ([telegram-elements.md](telegram-elements.md)). Never in an accent pill, never on the
   image. **Listings** are the exception: price leads, it is the deciding fact.
4. **Rating** as a short meta: a star icon (SVG) and `4.8 (120)`; star rows only in the detail screen's reviews.
5. **Availability** as quiet text: `In stock · ships in 2 days`, `3 spots left`, `Sold out` (dimmed card,
   still listed: L08). Never only a colour.
6. At most **one tag** (`−23 %`, `New`, `Ends 30 Nov`) at the media's top start or after the title. No
   ribbons, no badge stacks.
7. No descriptions in cards; the detail screen shows 3 lines, then "More".

Rows: the value (price, amount, time) sits at the end, right-aligned, tabular (L21); in schedules the time
is the leading column.

## 4. Card controls (L01, L19)

The whole card opens the detail screen. At most one control on it: favourite at the media's top end, or a
quick add at the bottom end (44 px target, `aria-pressed`, `selectionChanged`). The screen's primary action
(buy, book, subscribe, start) is the **MainButton** on the detail screen, never a button on every card.

## 5. Lists and catalogues (L09, L10, L13, L14, L23, L24)

- Order on a catalogue root: large title → search → filter chips (≤ 5) and sort → result count → list or
  grid. More than 5 filters go in a sheet opened by "Filters (n)".
- Grid columns: 2 from 320 to 559 px, 3 from 560 px; gaps 8-12 px; equal tiles from a fixed ratio and
  clamped titles.
- At most one horizontal scroller per screen (featured or related), 10 items, the next card peeking.
- Loading: skeletons in the card's own shape; empty results say why and offer to clear search and filters.
- Tablets and desktop clients: content capped near 600 px and centred (`.tma-content-cap`); grids gain a
  column instead of stretching.

## 6. Detail screens (L11, L12)

Order: media → title and price → selectors (size, format, date) → availability → key facts (`dl.tma-kv`) →
description (3 lines + More) → reviews → related. The primary action in the MainButton, naming the choice
and the price (`Add to cart · €12.90`, `Book Tue 18:00 · €30`, `Buy 2 tickets · €40`). Disable it with the
reason in the content when a choice is missing.

| Content | Detail order |
|---|---|
| Product | gallery (carousel, dots, counter) · title · price · variant chips or segmented · stock · description · details · reviews · related |
| Book | cover centred (≈ 160 px) · title · author · rating · format segmented with price · about · details (pages, year) · reviews · similar |
| Trainer | 4:5 portrait · name · specialty and rating · key facts · about · session gallery (3-col) · booking (L16) · reviews |
| Workout | 16:9 video with play · title · meta chips · program steps · related; members-only → MainButton offers the membership |
| Event | 3:2 cover · title · date and time · venue with map · ticket types with steppers · description · organiser |
| Listing | 4:3 gallery · price · title · key facts (beds · m² · floor) · map · description · amenities · contact |

Galleries: a carousel with dots and a counter on a detail screen; tap opens a viewer screen with BackButton
and `n / total`; a 3-column square grid for collections; 16:9 tiles with duration for videos; no masonry, no
autoplay (Android `LOW` and reduced motion especially).

## 7. Forms (L15)

One column; labels above fields (placeholders are examples, not labels); related fields grouped in a
section; `inputmode`, `autocomplete` and `enterkeyhint` set; the error under the field naming the fix; long
forms split into steps with a progress line; the submit action in the MainButton (disabled with the reason);
`enableClosingConfirmation` while something is unsaved; a draft in `CloudStorage`.

## 8. Booking and scheduling (L16)

Day strip (7-14 days, unavailable days disabled) → slot grid (3-4 columns, taken slots struck through and
disabled, never hidden) → one-line summary (`Tue 24, 18:00 · 60 min · €30`) → MainButton naming the slot and
the price. Specialist choice comes before the slot when the specialist matters (trainers, doctors, barbers),
after it when only the time matters (cleaning, delivery windows). The bot sends the confirmation and the
reminder.

## 9. Plans and pricing (L25)

Stacked plan cards on phones (never side by side under 600 px), a monthly/yearly segmented control above
them, one quietly recommended plan (a tag, not a glow), 3-5 features each with a check icon **and** text;
more than 3 plans or 6 features → a comparison table. The MainButton subscribes with the price and period
(`Subscribe · ⭐ 250 / month`); terms in the footnote with `openLink`.

## 10. Dashboards (SaaS)

One main figure or at most two KPI tiles per row on a phone; a chart under it; then breakdown rows; filters
as a segmented period control and chips. Actions live on detail screens, not on the dashboard. See the
`metric` entity and the portfolio example.

## 11. Reviewing a screen

1. Describe it as a screen JSON (`miniapp_layout.py example catalog` shows the shape): screen type, entity,
   width, variant and columns, card image (ratio, fit, position), slots in order, title lines, tags, card
   actions, price style, primary action, scrollers, filters, search, unavailable items, sections, booking,
   form, plans.
2. `py -3 scripts/miniapp_layout.py review screen.json` lists findings with rule ids and fixes.
3. `py -3 scripts/miniapp_layout.py show <entity>` gives the recommended layout and markup to move to.
4. Fix, lint (`miniapp_lint.py --strict`), preview the matrix, and cite the rule ids in the report.

## 12. Rule index

Generated from `data/mini-apps/layouts.json` (the test suite keeps them in step).

| Rule | What | Fix |
|---|---|---|
| L01 | One primary action per screen, in the MainButton | Move the main action (Buy, Book, Subscribe, Start) to the MainButton; cards and rows open a detail screen. |
| L02 | Image ratio follows the content type | Use the entity's ratio (book cover 2:3, portrait 4:5, product 1:1, video, course and workout 16:9, listing 4:3, event 3:2) and keep it identical across a list. |
| L03 | Covers, logos and packshots are contained; photos are cropped | object-fit: contain on a surface for covers, logos, packshots and documents; cover for photos of people, places, food and video frames. |
| L04 | Image position by card variant | Media cards and grid tiles: image on top, full width. Rows: a thumbnail at the start (people round, products square, covers 2:3); food menus may put a square photo at the end. Never an image on both sides. |
| L05 | Title first among the text, clamped | Order the text: title, then meta, then price. Titles take 2 lines at most in cards and 1 in rows, with an ellipsis. |
| L06 | Price under the title, plain and comparable | Price in headline weight with tabular figures and the user's locale; an old price struck through in hint after it; 'from' for variable prices; the period after it ('/ month'); never in an accent pill or on the image. |
| L07 | Rating is a short meta, not a star row | Show a star icon (SVG) with '4.8 (120)' in subhead hint next to or under the title; five-star rows only on the detail screen's reviews section. |
| L08 | Unavailable stays visible | Sold out, full or closed items stay in the list, dimmed, with the reason in text ('Sold out', 'Full · join waitlist'); never hidden or shown only by colour. |
| L09 | Grid columns by width | 2 columns from 320 to 559 px, 3 from 560 px, gaps 8-12 px; equal tile heights from a fixed media ratio and clamped titles. |
| L10 | Horizontal scrollers only for featured or related | At most one horizontal scroller per screen and never as the main catalogue; 10 items at most, the next card peeking. |
| L11 | Detail screens follow one section order | Media, title and price, selectors (size, format, date), key facts, description, details list, reviews, related. The primary action in the MainButton. |
| L12 | Galleries by purpose | On a detail screen: one carousel with dots and a counter, tap opens a viewer screen with BackButton. For a collection: a 3-column square grid. For videos and workouts: 16:9 tiles with a duration badge. No masonry, no autoplaying sliders. |
| L13 | Filters and sort sit under the title | Up to 5 quick filters as a chip row under the title (sticky on scroll), sort as a pill select; more than 5 filters go in a sheet opened by 'Filters (n)'. Always show the result count. |
| L14 | Search at the top of list screens | A search field under the large title of a list or catalogue root; placeholder 'Search'; results as you type; an empty result explains and offers to clear filters. |
| L15 | Forms are one column with labels above | Labels above fields, one column, related fields grouped in a section, inputmode and autocomplete set, the error under the field, submit in the MainButton (disabled with the reason in the content). |
| L16 | Booking: day strip, slot grid, summary, then the MainButton | A horizontal strip of days, a grid of time slots (3-4 columns), unavailable slots disabled not hidden, a one-line summary of the choice, and a MainButton naming the slot and price ('Book Tue 18:00 · €30'). |
| L17 | Card text stays short | One meta line in cards; descriptions only on the detail screen, 3 lines then 'More'; no paragraphs in lists. |
| L18 | One tag per card, no ribbons | At most one quiet tag (top-start on the media or after the title): 'New', 'Ends 30 Nov', '−20 %'. No corner ribbons, no stacks of badges. |
| L19 | One secondary control on a card at most | The whole card opens the detail screen; at most one icon button on it (favourite at the media's top end, or quick add at the bottom end), 44 px target. |
| L20 | No text on images | Put text under the media. If a title must sit on a photo, use a bottom scrim and check 4.5:1 in both themes. |
| L21 | Values align at the end of rows | Prices, amounts and times right-aligned (start in RTL) in tabular figures; times in schedules form the leading column. |
| L22 | Media carries meaning in alt text | alt names what the image shows (product and variant, trainer's name, workout title); decorative images alt="". |
| L23 | Loading and empty keep the anatomy | Skeletons in the card's own shape (media ratio, two text lines, price); empty results say why and offer a way out. |
| L24 | Wide screens cap the content | Content up to ~600 px wide and centred on tablets and desktop clients; images capped in height; grids gain a column instead of stretching tiles. |
| L25 | Plans: stacked cards on phones, a table to compare | Plans as stacked cards (not side by side) under 600 px with a monthly/yearly segmented control; one quietly recommended plan; 3-5 features each with check icons and text; a comparison table when there are more than 3 plans or 6 features. |
