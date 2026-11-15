# Reply keyboards, ForceReply, and the input field

`ReplyKeyboardMarkup` replaces the user's letter keyboard with your buttons.
Pressing a plain button **sends its `text` as an ordinary message** — the bot
receives text, not a callback. That single fact drives every rule below.

Not supported in channels or for messages sent on behalf of a business account.

## When a reply keyboard is the right tool

| Use it for | Because |
|---|---|
| A small, stable "app menu" (2–6 entries) always within reach | It persists across messages; no need to scroll up to an old inline keyboard |
| Requesting a contact, location, poll, user, chat, or managed bot | These `KeyboardButton` request types exist **nowhere else** |
| Guiding non-technical users who won't discover `/commands` | It is visible without any exploration |

Prefer an **inline** keyboard when the action belongs to a specific message,
when you need `callback_data`, when the action is destructive, or when the set
of options changes per message.

## `ReplyKeyboardMarkup` fields that shape the UX

| Field | Effect | Guidance |
|---|---|---|
| `resize_keyboard` | Shrinks the keyboard to fit its rows | **Set it to true** — the default is a full-height keyboard, which looks broken for 2 rows |
| `one_time_keyboard` | Hides after one press (still reachable via the keyboard icon) | Use for a one-off choice; not for a main menu |
| `is_persistent` | Asks clients to always show it | Use for a real main menu |
| `input_field_placeholder` | Placeholder in the input field, **1–64 characters** | Free real estate for a hint: "Type a city or tap a button" |
| `selective` | Show only to mentioned users / the replied-to sender | Essential in groups; otherwise you change the keyboard for everyone |

`ReplyKeyboardRemove` (`remove_keyboard: true`, plus `selective`) restores the
normal keyboard. **Remove it when the flow ends** — a stale menu from a finished
wizard is one of the most common Telegram-bot UI bugs.

## Button types (`KeyboardButton`)

Per the Bot API, **at most one** of the fields other than `text`,
`icon_custom_emoji_id`, and `style` may be used:

| Field | Result | Availability |
|---|---|---|
| *(none)* | Sends `text` as a message | anywhere |
| `request_contact` | Shares the user's phone number | private chats only |
| `request_location` | Shares current location | private chats only |
| `request_poll` | Asks the user to create a poll | private chats only |
| `request_users` | Opens a user picker → `users_shared` service message | private chats only |
| `request_chat` | Opens a chat picker → `chat_shared` service message | private chats only |
| `request_managed_bot` | Asks the user to create/share a managed bot (Bot API 9.6) | private chats only |
| `web_app` | Opens a Mini App → `web_app_data` service message | private chats only |

`style` and `icon_custom_emoji_id` (Bot API 9.4) work here exactly as on inline
buttons — see `buttons-and-styles.md` and `custom-emoji.md`. Coloring is even
more sparing here: a reply keyboard is chrome, and a wall of green chrome reads
as an error state.

Mini App context: `savePreparedKeyboardButton` (Bot API 9.6) stores a
`request_users` / `request_chat` / `request_managed_bot` button for a specific
user so a Mini App can trigger it — relevant when the bot's UI spans both
surfaces.

## The plain-text trap

Because a plain button just sends text, the handler matches on the **label** —
which is localized, user-typable, and changes whenever a designer edits copy.

Rules:

- **Route by a stable key, not by raw display text.** Resolve the incoming text
  through the i18n catalog (reverse lookup over all locales) or match a stable
  prefix; never scatter `if text == "Мой профиль"` across the codebase.
- **Assume a user can type the same string by hand** — validate state, don't
  trust that the button was pressed.
- **Never build a destructive action** as a bare reply button; a stray text
  message must not delete anything. Use an inline confirmation.
- Renaming a reply-keyboard label is a **behavioural change**, not a cosmetic
  one — update the matcher in the same commit, and keep accepting the old label
  for a grace period if long-lived keyboards are out there.

## `ForceReply`

Shows the reply interface as if the user tapped *Reply* on the bot's message.
Fields: `force_reply`, `input_field_placeholder` (**1–64 chars**), `selective`.

Use it for **one free-text answer inside a step-by-step flow**, especially in
groups where privacy mode would otherwise hide the message. Always set a
placeholder that states the expected input ("e.g. +47 900 00 000"). Provide an
escape route in the message text ("send /cancel to stop") — `ForceReply` has no
buttons of its own.

## Layout

- **2–3 buttons per row, ≤4 rows.** A reply keyboard eats screen height that
  belongs to the conversation.
- Keep labels **short** — they are echoed into the chat as messages, so long
  labels produce ugly transcripts.
- Order by frequency; keep a "⬅️ Back"/"🏠 Menu" entry in the same slot on every
  keyboard version.
- Keep the label set **disjoint** from likely free-text input, or the router will
  misfire.

## Migration heuristic

Moving a reply keyboard to inline is usually right when: the options depend on
the message, you need per-item ids, you want to edit the screen in place, or the
chat transcript is polluted by echoed labels. Keep the reply keyboard when its
job is *persistent, global navigation* or a `request_*` capability.

When you do migrate, keep both paths alive during the transition: old clients
may still have the reply keyboard on screen.

## Checklist

- [ ] `resize_keyboard` set; `is_persistent` / `one_time_keyboard` chosen
      deliberately.
- [ ] `input_field_placeholder` used as a hint (≤64 chars).
- [ ] `selective` set for group flows.
- [ ] Keyboard removed (`ReplyKeyboardRemove`) when the flow ends.
- [ ] Handlers route by stable keys/i18n lookup, not hardcoded display text.
- [ ] No destructive action reachable from a bare text button.
- [ ] `request_*` buttons only where private-chat-only is acceptable.
- [ ] Labels short, rows ≤3 wide, navigation entry in a fixed slot.
