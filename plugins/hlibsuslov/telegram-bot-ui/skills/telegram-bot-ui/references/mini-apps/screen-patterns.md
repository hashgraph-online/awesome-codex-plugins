---
summary: "Screen patterns by product type (commerce, booking, learning, SaaS, money, social): sections, screens, content types, primary actions, routes, mistakes; read to plan or audit a Mini App."
verified: "2026-11-24"
bot_api: "10.5"
---

# Screen patterns by product type

## Contents

- [1. Commerce](#1-commerce)
- [2. Booking and services](#2-booking-and-services)
- [3. Learning and content](#3-learning-and-content)
- [4. SaaS and tools](#4-saas-and-tools)
- [5. Money and loyalty](#5-money-and-loyalty)
- [6. Social and play](#6-social-and-play)
- [7. Lessons from the analysed reference (a wallet Mini App, iOS, dark)](#7-lessons-from-the-analysed-reference-a-wallet-mini-app-ios-dark)
- [8. Auditing an app against a pattern](#8-auditing-an-app-against-a-pattern)

What a Mini App for each common product looks like: its sections (tab roots), level-2 screens, the content
types it lists (with their layout from [layout-rules.md](layout-rules.md)), the primary action of each
screen, `startapp` routes, what the bot says before and after, and the usual mistakes. Use it to plan a new
app or to audit one: every row names the pattern an existing app can be compared with. Labels:
**[Heuristic]** unless marked. Decide first whether it should be a Mini App at all: [decide.md](decide.md).

Conventions for every pattern: tab bar of 2-5 sections; BackButton on every level-2 screen; the MainButton
for the one primary action of a screen; skeletons, empty and error states everywhere; the bot sends
notifications, receipts and reminders.

## 1. Commerce

### Shop (physical goods, books, merch)
| | |
|---|---|
| Sections | Catalogue · Cart · Orders (· Profile) |
| Lists | `product` / `book` grid tiles (2 columns, image 1:1 or cover 2:3 contained) |
| Level 2 | product detail (gallery, variants, stock) · cart · checkout (address or pickup, slot) · order status |
| Primary action | detail: `Add to cart · €X` · cart: `Checkout · €X` · checkout: `Pay €X` / `Pay ⭐ N` |
| startapp | `product-<id>`, `cart`, `order-<id>` |
| Bot before / after | promo or restock alert with a link to the product · receipt and order status updates |
| Mistakes | prices taken from the client · cart lost on reload (keep it in `CloudStorage` or the server) · hidden sold-out items · a checkout that asks for the name Telegram already gave |

Payment: the server creates the invoice (`createInvoiceLink`; digital goods in Stars, physical goods through a
provider) and the app opens it with `openInvoice`; the order is paid only on `successful_payment`. Flow,
statuses and screens: [payments.md](payments.md). Recipe 93.

### Food and drink ordering (café, restaurant, delivery)
| | |
|---|---|
| Sections | Menu · Order (· History) |
| Lists | `menu-item` rows: title, 2-line description, price, square photo at the end, quick-add stepper |
| Level 2 | item (size, milk, extras, quantity) · order (lines, steppers) · pickup or delivery details |
| Primary action | item: `Add to order · €X` · details: `Place order · €X` |
| startapp | `item-<id>`, `tab-order`, `reorder-<orderId>` |
| Bot | "Your order is ready" · repeat-order button in the chat for regulars |
| Mistakes | a menu PDF in an image · modifiers in a long form instead of chips and segmented controls · no ETA after ordering |

Example: `examples/mini-apps/vanilla`. Recipes 91, 93.

### Tickets and events
| | |
|---|---|
| Sections | Events · My tickets |
| Lists | `event` media cards (3:2): date first, title, venue, `from €X` |
| Level 2 | event detail (date, venue + map, ticket types with steppers) · seat map (if any) · ticket with QR |
| Primary action | `Buy 2 tickets · €40` · ticket screen: none (show the QR, brightness note) |
| startapp | `event-<id>`, `ticket-<id>` |
| Bot | reminder the day before with the ticket link · changes and cancellations |
| Mistakes | the QR only inside the app (also send it to the chat) · seat maps that need pinch-zoom with vertical swipes on (disable swipes only while the map is touched) |

## 2. Booking and services

### Gym, trainers, studios
| | |
|---|---|
| Sections | Trainers · Classes · My bookings (· Membership) |
| Lists | `trainer` rows (round photo, specialty · years, `from €X`, rating) · `class` schedule rows grouped by day (time first, title, trainer, spots left) · `workout` media cards for on-demand videos |
| Level 2 | trainer (4:5 portrait, facts, about, session gallery, day strip + slot grid) · class (time, room, spots, policy) · membership plans |
| Primary action | `Book Tue 18:00 · €30` · `Book 19:00 class` · full class: `Join the waitlist` · plans: `Subscribe · ⭐ N / month` |
| startapp | `trainer-<id>`, `class-<id>`, `tab-classes` |
| Bot | confirmation, reminder an hour before, "a spot opened" for waitlists, cancellation with one tap |
| Mistakes | hiding taken slots · a calendar month grid as the only picker on a phone · booking without showing the price · cancellation only by writing to support |

Examples: `examples/mini-apps/catalog` (Trainers, Workouts), `examples/mini-apps/rework` (class schedule,
membership, the full payment flow). Recipes 94, 96.

### Appointments (barber, beauty, clinic, tutor, repair)
| | |
|---|---|
| Sections | Book · My appointments (· Profile) |
| Flow | service (rows: title, `45 min · €30`) → specialist (or "any") → day strip + slots → details → confirm |
| Primary action | step by step: `Continue` disabled until chosen · last step `Book Thu 10:30 · €30` |
| startapp | `service-<id>`, `specialist-<id>`, `reschedule-<bookingId>` |
| Bot | confirmation, reminder, reschedule link, review request after the visit |
| Mistakes | asking for the phone before the slot (ask only if the business needs it, with `requestContact` and a reason) · free-text dates |

Clinics: never put diagnoses or test results in bot messages or previews; show them inside the app behind
fresh `initData` and your own session ([security.md](security.md)).

### Rentals and listings (property, cars, equipment)
| | |
|---|---|
| Sections | Search · Saved · Requests |
| Lists | `listing` media cards: 4:3 photo carousel with favourite, **price first**, title, key facts (beds · m² · floor), location |
| Level 2 | listing (gallery, price, facts, map, description, amenities, contact) · filters sheet · request form |
| Primary action | `Request a viewing` / `Book 3 nights · €360` |
| startapp | `listing-<id>`, `search-<savedSearchId>` |
| Bot | new matches for a saved search · request status |
| Mistakes | a dozen filters in a row (use a sheet) · map-only results without a list · photos with text baked in |

## 3. Learning and content

### Courses and lessons
| | |
|---|---|
| Sections | Learn · Catalogue · Profile |
| Lists | `course` media cards (16:9, lessons · hours · level, progress bar when enrolled) · lessons as rows with check states |
| Level 2 | course (outcomes, lessons, author, reviews) · lesson (video 16:9, text in `.tma-prose`, quiz) |
| Primary action | `Enrol · €X` / `Continue lesson 4` / `Check answer` |
| startapp | `course-<id>`, `lesson-<id>` |
| Bot | streak and reminder messages · new lesson released |
| Mistakes | locking navigation between lessons · autoplay with sound |

### Media library, articles, news
| | |
|---|---|
| Lists | `article` rows (title up to 3 lines, source · time, square thumbnail at the end) or 16:9 cards for the lead story |
| Level 2 | article in `.tma-prose` with h1-h6, quotes, images with captions |
| Primary action | none while reading; `Share` via `shareMessage` |
| Mistakes | infinite feeds without a way back to the top · hero images on every story |

## 4. SaaS and tools

### SaaS dashboard (analytics, monitoring, CRM-lite)
| | |
|---|---|
| Sections | Overview · Items (deals, tickets, projects) · Settings |
| Lists | `metric` (one figure, or two KPI tiles per row, delta with period) · `person` / item rows with status tags |
| Level 2 | metric detail (chart, period segmented, breakdown) · item detail (fields as `dl.tma-kv`, timeline `.tma-steps`, actions) |
| Primary action | overview: none · item: the next state (`Mark as paid`, `Assign to me`) |
| startapp | `item-<id>`, `metric-<key>`, `tab-items` |
| Bot | alerts with a link to the exact item · daily digest in the chat |
| Mistakes | a desktop table squeezed onto a phone (use rows; a table only for compared columns) · six charts on one screen · actions on the overview |

Style: usually `dense`; `fintech` when one number leads.

### Plans, billing, subscription
Plan cards stacked or one radio list, one recommended plan, features with icons and text, a comparison table
for more than 3 plans; MainButton `Subscribe · ⭐ 250 / month` or a card invoice. Stars subscriptions are
30-day only: a longer term is a one-off payment. A Premium / Pro paywall: [payments.md](payments.md) §9
(P1-P12) and `examples/mini-apps/paywall`.
Show current plan, renewal date and a clear `Cancel subscription` (destructive, confirmed). Recipe 96.

### Admin and moderation
Queue rows with the item, the reporter and the age; detail with the content, history and two decisions
(`Approve` as MainButton, `Reject` as SecondaryButton with `position: left`); a confirmation for
irreversible actions; the result posted back by the bot. Style `dense`.

### Editor and builder
Dense input, autosave with revisions (a stale save is a conflict, never an overwrite), a preview, leaving
with unsaved changes behind `enableClosingConfirmation`, publishing confirmed by the bot. Recipe 99.

### Forms and surveys
One question group per screen for long forms, progress at the top, MainButton `Continue` / `Send`, draft in
`CloudStorage`, results to the chat (`sendData` for reply-keyboard launches, `answerWebAppQuery` for inline
launches). Recipe 94.

## 5. Money and loyalty

### Wallet, portfolio, points
One large figure with its change, quick actions (2-4), one promo moment, asset rows, a chart on detail
screens, MainButton + SecondaryButton for the two actions of an asset. Style `fintech`. Example:
`examples/mini-apps/portfolio`. Recipe 95. TON specifics: [../wallet-and-ton.md](../wallet-and-ton.md).

### Loyalty and referrals
Balance figure, level progress (`.tma-progress` with the numbers in text), "how to earn" rows, a referral
link with `shareMessage` and a copy button, history rows. The bot announces earned points.

## 6. Social and play

### Community, clubs, membership
Members as `person` rows, events, a feed; join requests through the 10.1 join-request Mini App when the
community verifies people ([launch-and-lifecycle.md](launch-and-lifecycle.md)).

### Games and leaderboards
Fullscreen (`requestFullscreen`, safe areas), orientation lock only while playing, vertical swipes disabled
only during gestures, a leaderboard table with the user's row, results shared with `shareMessage` /
`shareToStory`. Recipe 97.

### Sharing a result
Prepared inline messages (`savePreparedInlineMessage` → `shareMessage`), `switchInlineQuery` for picking a
chat, `answerWebAppQuery` for query launches. Recipe 98.

## 7. Lessons from the analysed reference (a wallet Mini App, iOS, dark)

1. Telegram draws the chrome; the app colours it: the header follows the top of the screen.
2. One rich moment per screen (a promo, a 3D emoji, a hero); everything else stays quiet grouped lists.
3. Numbers are the main typography: a figure, a smaller fraction, sign and colour of direction.
4. Tabs at the bottom for sections, BackButton for depth, MainButton for the main action.
5. Coloured icon backgrounds are tints of a role, not new colours.
6. Light theme: a light grey page, white groups, the same radii; check the chrome contrast in both themes.
7. Corner ribbons are the reference's signature, not a default: use a quiet tag (L18).

## 8. Auditing an app against a pattern

1. Name the pattern (one of the above) and its sections.
2. For each screen: is the primary action in the MainButton? Are states drawn? Is the content type laid
   out per [layout-rules.md](layout-rules.md) (`miniapp_layout.py review`)?
3. Does the bot send the before and after messages the pattern lists?
4. Lint, preview, and report findings with the rule ids (MA.. from the lint, L.. from layout rules).
