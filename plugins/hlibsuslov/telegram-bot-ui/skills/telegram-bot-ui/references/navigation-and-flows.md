# Navigation, screens, and chat-level chrome

A bot's "pages" are messages. Its "router" is `callback_data` plus conversation
state. Without an explicit map, navigation rots into dead ends and orphan
screens. Build the map first.

## Screen/state map (produce this before changing anything)

For every screen record:

| Field | Example |
|---|---|
| Screen id | `cart.review` |
| Reached from | `catalog.item` (Add to cart), `menu` (Cart) |
| Message body | title + item table |
| Keyboard | Checkout `primary` · Remove item · ← Back to catalog |
| `callback_data` scheme | `cart:*` |
| Exits | `checkout.pay`, `catalog.list`, `menu` |
| State required | cart non-empty |
| Empty/error variant | "Your cart is empty" + Browse catalog |

Then look for the classic defects:

- **Dead ends** — a screen with no way back or home.
- **Orphans** — a screen nothing links to (usually a leftover).
- **Ambiguous returns** — "Back" that means different things on different
  screens.
- **State-free screens** — an old message whose buttons still act on stale data.
- **Duplicate paths** — two routes to the same screen with different labels.
- **Missing empty/error variants** — a list screen that renders an empty table.

## Back, home, and depth

- **Every non-root screen has exactly one "Back"**, in the last row, same label
  and same position everywhere. Back means "one level up", not "previous
  message".
- Add **"🏠 Menu"** once depth exceeds ~2 levels, so users can escape without
  tapping Back repeatedly.
- Keep hierarchy **shallow**: 2–3 levels covers most bots. Deeper means the menu
  is doing the job of search or filters.
- Show **where the user is** in the message text (a title line, or
  `Catalog › Shoes › Filters`), not only in the keyboard.
- Prefer **editing the current message** for in-flow navigation
  (`inline-keyboards.md`); send a new message when the user should keep the old
  one.

## Wizards and multi-step forms

- State the **step** ("Step 2 of 4") and what is being asked, in one line.
- Offer **Back** to the previous step and **Cancel** for the whole flow —
  Cancel here is a neutral action (no `danger`).
- Accept the answer via inline buttons where the option set is finite; use
  `ForceReply` with a placeholder for free text (`reply-keyboards.md`).
- **Echo what was captured** after each step so users can trust the state.
- On completion, remove or disable the flow's keyboard and show a result screen
  with the next sensible action.
- Handle the user going off-script (a random text message mid-wizard) with a
  gentle re-prompt, not silence.

## Chat-level chrome

**Commands (`setMyCommands`)** — the discoverability layer.

- `BotCommand.command`: **1–32 chars**, lowercase English letters, digits,
  underscores. `description`: **1–256 chars**. **At most 100 commands** per
  scope.
- Keep the visible list to the handful users actually need; put the rest behind
  menus. A 30-item command list is not a menu.
- Descriptions are microcopy: verb-first, lowercase-consistent, no ending
  period, no restating the command name.
- Use **`scope`** (`BotCommandScope*`) to split user/admin/group commands, and
  **`language_code`** to localize the list — commands are part of your i18n
  surface, not an exception to it.
- `BotCommand.is_ephemeral` (Bot API 10.2) marks commands whose reply is visible
  only to the sender — see *Ephemeral messages* below.

**Menu button (`setChatMenuButton`)** — `MenuButtonCommands` (default, opens the
command list), `MenuButtonWebApp` (opens a Mini App), or `MenuButtonDefault`.
Set it per chat or globally. If the bot's centre of gravity is a Mini App, point
the menu button at it and say what opens; otherwise leave the commands menu.

**Deep links (`/start` payloads)** — `t.me/<bot>?start=<payload>` lands the user
on a specific screen. Keep payloads short, opaque, and validated; **never**
encode privileges in them. Deep links used in ads/QR codes are long-lived:
treat them as a public API and don't break them during a redesign.

**First run** — `/start` with no payload is the bot's landing page: one line of
what the bot does, one primary action, no wall of text. It must work for a user
who has never seen the bot.

## Newer navigation surfaces (verify SDK + Bot API support first)

These exist in recent Bot API versions and change what "a screen" can be. Full
version list: `ui-changelog.md`.

- **Ephemeral messages (10.2)** — group messages visible only to one user and
  the bot; edited via `editEphemeralMessageText` /
  `editEphemeralMessageReplyMarkup`, deleted via `deleteEphemeralMessage`, and
  replied to through `ReplyParameters.ephemeral_message_id`. Ideal for
  per-user menus inside a group without spamming everyone. Note the API's own
  caveat: edit events are not guaranteed to reach an offline user, so never make
  correctness depend on an edit landing.
- **Topics in private chats (9.3/9.4)** — `message_thread_id` in private chats
  and `createForumTopic` let a bot split a conversation into threads (support,
  orders, alerts) instead of one flat log. `User.has_topics_enabled` and
  `User.allows_users_to_create_topics` tell you what is available.
- **Streaming drafts (`sendMessageDraft`, 9.3; all bots since 9.5)** — a
  temporary ~30-second preview of a message being generated; the final message
  must still be sent with `sendMessage`. Perceived-latency UX, not a screen.
  See `streaming-and-editing.md`.
- **`date_time` entity (9.5)** — renders a timestamp in the *user's* locale and
  timezone (relative, weekday, short/long date, short/long time) instead of a
  server-formatted string. Use it for deadlines, schedules, and "expires in…".
- **Guest mode (10.0)** and **join-request queries (10.1)** — bot UI surfaces
  outside normal membership; check the current docs before designing around
  them.

## Notifications and interruptions

- Use `disable_notification` for anything the user did not ask for right now.
- Don't send a new message when editing the current screen would do.
- Group related updates into one message rather than a burst.
- Give every notification a way to act (a button) or to stop (settings link).

## Checklist

- [ ] Screen/state map produced and included in the report.
- [ ] No dead ends, no orphan screens, no ambiguous "Back".
- [ ] Back/Home labels and positions identical bot-wide.
- [ ] Wizards show step, allow Back and Cancel, echo captured values.
- [ ] Command list short, scoped, localized, verb-first.
- [ ] Menu button deliberate; deep links preserved and validated.
- [ ] `/start` works cold, with one clear primary action.
- [ ] Stale-message taps handled (state re-validated server-side).
- [ ] Empty and error variants exist for every list/result screen.
