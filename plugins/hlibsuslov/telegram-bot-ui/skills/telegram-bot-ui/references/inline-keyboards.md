# Inline keyboards

`InlineKeyboardMarkup` = `inline_keyboard`: an array of rows, each an array of
`InlineKeyboardButton`. It belongs to **one specific message** and is the main
interactive surface of most bots.

## Button types (exactly one per button)

| Field | What tapping does | UX notes |
|---|---|---|
| `callback_data` | Sends a `callback_query` to the bot; **1–64 bytes** | Default choice. Always answer it. |
| `url` | Opens an HTTP or `tg://` link | Clients mark it as leaving the chat; label it accordingly |
| `web_app` | Opens a Mini App (private chats only) | Say what opens: "Open catalog" |
| `login_url` | Seamless HTTPS authorization | Replaces the Login Widget |
| `switch_inline_query` | Picks a chat, inserts the bot's username + query | Good for "Share…" |
| `switch_inline_query_current_chat` | Inserts the query in the current chat | Good for "search in this chat" |
| `switch_inline_query_chosen_chat` | Same, restricted to chat types | Set the allowed types deliberately |
| `copy_text` | Copies text to the clipboard (`CopyTextButton.text`, **1–256 chars**) | Use for codes/addresses instead of asking users to select text |
| `callback_game` | Launches a game — **must be the first button in the first row** | |
| `pay` | Pay button — **must be the first button in the first row**, invoice messages only | `XTR`/star substrings become the Star icon |

`text`, `style`, and `icon_custom_emoji_id` are presentation and do not count as
the action.

## `callback_data` design

- **1–64 bytes** — bytes, not characters. Cyrillic, emoji, and CJK burn 2–4
  bytes each. Keep payloads ASCII.
- Use a **namespaced scheme** the whole bot shares:
  `<screen>:<action>:<id>` → `cart:remove:8821`. It makes routing, logging, and
  auditing possible.
- Put **ids, not labels**, in the payload — labels are localized, ids are not.
- If the payload doesn't fit, store the state server-side and pass a short key.
- **Never change existing `callback_data` during a visual redesign.** Messages
  already in users' chats still send the old payload; changing the scheme
  silently breaks every historical message. If a change is genuinely required,
  keep the old handlers alive (or map old → new) and say so in the report.
- Treat incoming payloads as **untrusted input**: validate the shape and
  re-check the user's permission for that object on every callback.

## Always answer the callback

Every `callback_query` must be answered (`answerCallbackQuery`), even with no
text — otherwise the client shows a spinner and the bot feels broken.

- `text` — **0–200 characters**; a top-of-screen toast.
- `show_alert: true` — a modal the user must dismiss. Use for consequences, not
  for routine feedback.
- `cache_time` — client-side caching of the answer; keep at 0 for anything
  state-dependent.

Feedback ladder: **change the screen** (best) → toast → alert. If a tap changes
data that is visible on screen, edit the message so the screen reflects it.

## Editing in place vs sending a new message

- `editMessageText` / `editMessageCaption` / `editMessageMedia` — replace the
  screen the user is looking at. Preferred for navigation inside one flow: the
  chat stays clean and there is a single source of truth.
- `editMessageReplyMarkup` — swap only the keyboard (toggle states, disable
  buttons after use, reveal a confirmation row).
- **Send a new message** when the event is genuinely new (a notification, a
  receipt, a result the user should keep in history).
- Editing a message with identical content raises `message is not modified` —
  compare before editing (`errors-and-fallbacks.md`).
- Removing a keyboard from a finished screen (`reply_markup` omitted / empty)
  prevents double submissions on stale messages. Pair it with server-side
  idempotency; never trust the UI alone.

## Layout

```
row 1: [ the primary action                    ]
row 2: [ secondary ] [ secondary ]
row 3: [ topic group … ]
row 4: [ ← Back ]                     [ Delete ]
```

- **1–2 buttons per row** for sentence-length labels, up to 3 for short ones,
  more only for tokens (page numbers, digits, dates). The Bot API documents no
  per-row maximum; clients split the row width evenly, so long labels truncate.
  These are design heuristics — verify visually on a narrow screen.
- **Keep rows semantically homogeneous.** A row is read as a group.
- **Navigation goes last**, in the same place on every screen.
- **Destructive last, never adjacent to the primary action.**
- More than ~8 rows means you are rendering a list — paginate.

## Pagination and long lists

```
[ Item 1 ]
[ Item 2 ]
[ Item 3 ]
[ ‹ Prev ] [ 2/7 ] [ Next › ]
[ ← Back to menu ]
```

- Keep the page indicator as a **no-op button** (`callback_data` that answers
  with a toast) or fold it into the message text — never a button that looks
  tappable but does nothing.
- Encode the page in `callback_data` (`list:page:3`), not in server session
  state only, so old messages still work.
- At the edges, either disable movement (drop the button) or keep it and answer
  with a toast — pick one convention and apply it bot-wide.
- Consider `switch_inline_query_current_chat` for search instead of paging
  through hundreds of items.

## Common screen recipes

**Confirmation of a destructive action**

```json
{"inline_keyboard": [
  [{"text": "Yes, delete the account", "callback_data": "acc:del:confirm", "style": "danger"}],
  [{"text": "← Keep my account", "callback_data": "acc:menu"}]
]}
```

The safe escape is unstyled and last; the destructive confirm spells out what is
being deleted.

**Toggle row (state in the label, not in the color)**

```json
{"inline_keyboard": [
  [{"text": "Notifications: on", "callback_data": "set:notify:off"}],
  [{"text": "Language: English", "callback_data": "set:lang"}],
  [{"text": "← Back", "callback_data": "menu"}]
]}
```

The label shows the **current** state; the payload carries the **next** one.
Document which convention the project uses — mixing them causes real bugs.

**Wizard step**

```json
{"inline_keyboard": [
  [{"text": "Continue", "callback_data": "wiz:2", "style": "primary"}],
  [{"text": "Skip this step", "callback_data": "wiz:skip"}],
  [{"text": "← Back", "callback_data": "wiz:0"}, {"text": "Cancel", "callback_data": "wiz:exit"}]
]}
```

## Where inline keyboards can and cannot go

- Inline keyboards work in private chats, groups, supergroups, and channels.
- Some button types are restricted: `web_app` is private-chat only;
  `switch_inline_query*` variants are not supported in some contexts (channel
  direct-messages chats, business-account sends) — check the field's own note in
  the Bot API before relying on it.
- Ephemeral messages (Bot API 10.2) support inline keyboards and are edited with
  `editEphemeralMessageReplyMarkup` — see `navigation-and-flows.md`.

## Checklist

- [ ] Exactly one action field per button.
- [ ] `callback_data` ≤64 **bytes**, namespaced, ids not labels, unchanged by
      this redesign.
- [ ] Every callback answered; alerts reserved for consequences.
- [ ] Screen edited in place where it is the same screen.
- [ ] Rows homogeneous; navigation last; destructive isolated.
- [ ] Lists paginated with the page encoded in the payload.
- [ ] Stale-message behaviour defined (disabled keyboard + idempotent handler).
