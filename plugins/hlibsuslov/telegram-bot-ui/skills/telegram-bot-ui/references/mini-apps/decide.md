# Messages, widget or Mini App: deciding the surface

A Mini App is a hosted web app with its own server, auth and release cycle. It is the right surface when the
task needs a real interface, and the wrong one when a message, a keyboard or a widget would do. Decide per
**task**, not per bot: most good products are hybrids where the bot notifies and the Mini App acts.

Related: the whole-bot format table [../format-selection.md](../format-selection.md), widgets
[../widget-patterns.md](../widget-patterns.md) §1 and §12. Labels: **[Official]**, **[API]**,
**[Heuristic]**.

## 1. The three surfaces

| | Messages and keyboards | HTML widget (10.4) | Mini App |
|---|---|---|---|
| Lives | in the chat history | inside one message | a sheet or fullscreen page over the chat |
| Input | taps, typed replies, `force_reply` | taps and drags on a custom layout; no text input | any web input, files, camera, gestures |
| Network at view time | — | none; state only from the bot's edits | yes, your API |
| Size | text limits | ≤ 32 KB code, clips at ~600 px | any |
| Where | every chat type | production: private chats | private chats for keyboard/inline buttons; links and the profile button anywhere |
| Cost | lowest | low, no hosting | hosting, auth (`initData`), a second codebase, releases |

Widget facts **[API]**/**[Official]**: [../widgets.md](../widgets.md). Mini App entries:
[launch-and-lifecycle.md](launch-and-lifecycle.md).

## 2. Signals that call for a Mini App [Heuristic]

Pick a Mini App when at least one of these is true and central to the task, not incidental:

1. **Live network data while looking at it**: search with results as you type, a live price, availability
   that changes between taps.
2. **Uploads or capture**: several photos, documents, a QR scan inside a flow, a signature.
3. **Long forms**: more than ~3 fields, conditional fields, validation that needs the server, a draft to
   come back to.
4. **Navigation deeper than two levels** or more than ~8 choices per level: catalogues with filters,
   settings with groups, history with detail pages.
5. **Dense data**: charts, tables wider than a phone message, comparisons, maps, calendars with slots.
6. **Gestures and canvases**: games, drawing, drag to reorder, maps.
7. **Fullscreen or landscape**: media, games, immersive views.
8. **One task, many sessions**: a cart, an editor, a portfolio the user returns to.

## 3. Signals against a Mini App [Heuristic]

| Situation | Better |
|---|---|
| One choice from ≤ 8 options, a yes/no, a rating | inline keyboard |
| 1-3 short answers | `force_reply` steps or reply keyboard ([../reply-keyboards.md](../reply-keyboards.md)) |
| A status that changes in place (order, build, delivery) | an edited message, or a widget in a private chat |
| A one-off notification or report | a message or a Rich Message |
| Repeat order of a known item | a message with "Order again" |
| Content meant to be read in the chat, quoted, forwarded | a message |
| The team cannot host and secure a web app | stay in the chat; a widget if a custom layout is needed |
| Groups and channels where everyone acts on one object | a shared widget or a message with buttons; a Mini App acts per user |

## 4. Decision path

1. Can the task finish in the chat with buttons and up to three typed answers? → **messages**.
2. Does it need a custom layout but no text input, no network and fits ~600 px (private chat)? → **widget**.
3. Otherwise → **Mini App**, and decide the entry point before the screens: reply keyboard (`sendData`),
   inline or menu button (`answerWebAppQuery`), Main Mini App or direct link (no chat access)
   ([launch-and-lifecycle.md](launch-and-lifecycle.md) §1).
4. For every Mini App screen ask what the bot says **before** (the entry message, an alert) and **after**
   (a receipt, a status) the app. If nothing, check the user is not left wondering whether it worked.

## 5. Hybrids that work [Heuristic]

| Pattern | Bot does | Mini App does |
|---|---|---|
| Notify → act | sends the alert ("Order #8812 is ready") with a `web_app` button or `startapp` link to that exact screen | shows the order and the one action |
| Summary card → full view | keeps a widget or message summary up to date | full list, filters, edits; the server tells the bot to update the card |
| Act → receipt | posts the confirmation (`answerWebAppQuery`, or a message after `requestWriteAccess`) | performs the action and shows success in place |
| Pick in the app, send to a chat | `savePreparedInlineMessage` | `shareMessage(id)` |
| Join request gate (10.1) | answers within 10 s by opening the app | verifies the applicant, the server decides |

The Mini App is never the only place where a user learns that something happened to them: notifications,
receipts and reminders are the bot's job.

## 6. Per-interface defaults

| Interface | Mini App when | Messages or widget when |
|---|---|---|
| Shop / catalogue | > ~10 items, filters, galleries, variants | 3-5 items, reorder |
| Cart and checkout | address, slots, promo code, several items | one item → invoice directly |
| Form | > 3 fields, files, conditional fields | 1-3 questions |
| Dashboard | charts, filters, several metrics | one number or status |
| Profile and settings | many groups, toggles, linked accounts | 3-5 settings |
| Leaderboard / game | real time, gestures, fullscreen | a top-10 table |
| Booking | calendar, slot grid, several resources | one resource, next 7 days |
| Editor | long document, preview, media | a short text |
| Wallet / portfolio | balance, history, charts | a transfer notice |

Screens, states, native buttons and bot messages for each: [screen-patterns.md](screen-patterns.md); where the image, title and price go: [layout-rules.md](layout-rules.md).

## 7. Anti-patterns

- A Mini App that is only a menu of links back into the chat.
- A Mini App for a single yes/no confirmation the bot could ask with two buttons.
- A web login screen inside a Mini App: the user is already identified by `initData`.
- Copying a website into a Mini App: desktop navigation, hamburger menu, hero banner on every launch
  ([telegram-design-guidelines.md](telegram-design-guidelines.md)).
- Moving notifications into the app: users do not open an app to learn their order shipped.
