# Buttons, emphasis, and `style` colors

Everything here applies to both `InlineKeyboardButton` and `KeyboardButton`
unless stated otherwise. Layout specifics: `inline-keyboards.md`,
`reply-keyboards.md`. Wording: `microcopy-and-labels.md`.

## The one structural rule

Official Bot API wording:

- **`InlineKeyboardButton`** — "Exactly one of the fields other than *text*,
  *icon_custom_emoji_id*, and *style* must be used to specify the type of the
  button."
- **`KeyboardButton`** — "At most one of the fields other than *text*,
  *icon_custom_emoji_id*, and *style* must be used to specify the type of the
  button." (With none of them, pressing the button sends `text` as a message.)

So an inline button is always exactly one of: `url`, `callback_data`,
`web_app`, `login_url`, `switch_inline_query`,
`switch_inline_query_current_chat`, `switch_inline_query_chosen_chat`,
`copy_text`, `callback_game`, `pay`. `text`, `style`, and
`icon_custom_emoji_id` are presentation and do **not** count as the action.

Two action fields on one button is a 400 from Telegram, not a design choice.

## `style` — colored buttons (Bot API 9.4, 2026-02-09)

Field on both button classes. Official description: *"Optional. Style of the
button. Must be one of 'danger' (red), 'success' (green) or 'primary' (blue).
If omitted, then an app-specific style is used."*

```json
{ "text": "Continue", "callback_data": "wizard:next", "style": "primary" }
```

There is **no** HEX, RGB, CSS, theme, or custom color in the Bot API. If a user
asks for "an orange button", say what is actually available and map their intent
onto one of the three values.

### Semantic mapping (assign by meaning, not by taste)

| `style` | Color | Use when the action… | Examples |
|---|---|---|---|
| `primary` | blue | moves the user forward — the single most likely next step | Continue · Start · Open · Next · Choose plan · Go to catalog |
| `success` | green | commits, confirms, or completes something positively | Save · Confirm · Publish · Submit · Finish test · Pay · Mark as done |
| `danger` | red | destroys, resets, or is otherwise hard/impossible to undo | Delete · Reset progress · Unsubscribe · Leave chat · Cancel plan · Log out |
| *(omit)* | app default | is secondary, neutral, or navigational | Back · Home · Settings · Help · Skip · individual list items |

Borderline calls:

- **"Cancel" is ambiguous.** *Cancel this dialog* (abandon a wizard, close a
  screen) is neutral → no style. *Cancel my subscription / cancel the order*
  is destructive → `danger`.
- **Payment.** The pay/checkout button is `success` when it completes a flow the
  user already configured; `primary` when it merely opens the checkout screen.
- **Positive but not final.** "Take the test", "Try again" → `primary`, not
  `success`; nothing was committed yet.
- **A list of equal options** (products, languages, dates) gets **no** style.
  Coloring 8 equal options destroys the hierarchy it was meant to create.

### Emphasis budget per screen

- **At most one `primary`.** If two actions both look primary, the screen has
  two purposes — split it or demote one.
- **`success` and `primary` rarely co-exist.** A confirmation screen has one
  `success` (confirm) and an unstyled "Back"; a menu has one `primary`.
- **`danger` is never the default focus.** Put it last in the layout, keep it
  out of the first row, and route it through a confirmation screen where the
  confirming button is `danger` and the escape route is unstyled.
- **Rule of thumb: ≤2 styled buttons per keyboard.** More than that and nothing
  stands out. This is a design heuristic, not an API limit.

### What color must never do

- **Never carry meaning alone.** "Delete" must say *Delete*; red is
  reinforcement. Users on old clients, in accessibility modes, or with color
  vision deficiency see only the label.
- **Never replace a confirmation.** `danger` is a warning, not a safeguard.
- **Never be used decoratively** ("make the menu colorful") — say no and explain
  that the three values are semantic.
- **Never encode state.** A green "Notifications" button does not communicate
  "notifications are on" — put the state in the label (`Notifications: on`).

## Custom emoji icons

`icon_custom_emoji_id` puts one custom emoji before the label. Eligibility,
sourcing IDs, fallbacks, and the Premium/Fragment rules: `custom-emoji.md`.
Short version: **never invent an ID**, and never let the icon be the only thing
that distinguishes two buttons.

## Ordering and grouping

Order buttons by the **probability the user needs them**, then by risk:

```
[ primary / most likely action          ]
[ secondary action ] [ secondary action ]
[ other actions grouped by topic        ]
[ Back ]                    [ danger ]
```

- **One row = one meaning.** Don't put "Delete" next to "Continue" just to fill
  a row; a mis-tap should not be destructive.
- **Group by topic**, then order within the group by frequency of use.
- **Keep the navigation row last and identical on every screen** — same label,
  same position, same `callback_data` scheme (`navigation-and-flows.md`).
- **Width:** the Bot API does not document a maximum number of buttons per row;
  clients divide the row width evenly, so long labels in a 4-button row get
  truncated on narrow phones. Practical guidance: **1–2 buttons per row for
  sentence-length labels, up to 3 for short ones, up to 5–8 only for very short
  tokens** (digits, dates, page numbers, stars). Treat these as design
  heuristics and verify visually.
- **Height:** if a keyboard needs more than ~8 rows, it is a list, not a menu —
  paginate it (`inline-keyboards.md`).

## Inline vs reply — which one is a "button" here

| Situation | Use |
|---|---|
| Action tied to *this* message (confirm, page, open, expand) | Inline keyboard |
| A persistent, always-available "app menu" (2–6 sections) | Reply keyboard |
| Sharing a contact / location / user / chat / poll | Reply keyboard (only these exist there) |
| Opening a Mini App from a fixed place | Menu button, or a `web_app` inline button |
| One-off free-text answer in a step-by-step form | `ForceReply` with a placeholder |

Details and trade-offs: `inline-keyboards.md`, `reply-keyboards.md`,
`navigation-and-flows.md`.

## Anti-patterns

| Anti-pattern | Why it hurts | Fix |
|---|---|---|
| Every button styled | No hierarchy; the screen reads as noise | ≤2 styled, ≤1 `primary` |
| `style` used for branding | The three values are semantic, not a palette | Explain the constraint |
| `danger` on "Back"/"Cancel dialog" | Trains users to fear a safe action | Leave unstyled |
| Emoji-only labels (`🔙`, `✅`) | Ambiguous, unsearchable, bad for screen readers | Emoji **+** word |
| 12 options in one column | Endless scroll, no structure | Group + paginate |
| Same action named differently per screen | Users can't build a model of the bot | One label per action, everywhere |
| Changing `callback_data` during a restyle | Breaks live sessions and old messages | Keep payloads; restyle only |
| A button that does nothing on tap | Reads as a broken bot | Always `answerCallbackQuery` |

## Before/after

**Before** — flat, unlabeled hierarchy, destructive action beside a safe one:

```json
{"inline_keyboard": [[
  {"text": "OK", "callback_data": "ok"},
  {"text": "Delete", "callback_data": "del"},
  {"text": "Back", "callback_data": "back"}
]]}
```

**After** — one clear commit action, destruction separated and confirmed,
navigation predictable:

```json
{"inline_keyboard": [
  [{"text": "Save changes", "callback_data": "ok", "style": "success"}],
  [{"text": "Delete draft", "callback_data": "del", "style": "danger"}],
  [{"text": "← Back", "callback_data": "back"}]
]}
```

`callback_data` values are untouched — only presentation changed. More worked
cases: `examples-before-after.md`.

## Three button models

Verified 2026-11-12. Fields do **not** carry over between models — `scripts/validate_keyboard.py`
rejects cross-model fields.

| | `InlineKeyboardButton` | `KeyboardButton` (reply) | `RichMessageButton` (10.3, inside rich messages) |
|---|---|---|---|
| Action rule | exactly one action | at most one | exactly one |
| Actions | url, callback_data, web_app, login_url, switch_inline_query*, copy_text, callback_game, pay, **disabled** | request_users/chat/managed_bot/contact/location/poll, web_app | url, callback_data, web_app, login_url, switch_inline_query*, copy_text, **disabled** |
| Text | String | String | RichText: plain, custom emoji, date-time only |
| `style` | primary/success/danger | primary/success/danger | + **`link`** (callback buttons only) |
| `icon_custom_emoji_id` | yes | yes | no (put custom emoji in the text) |
| Placement | under the message | replaces the user's keyboard | in a `<tg-button-row>` block (1–8) or inline in text (`RichTextButton`) |

## Disabled buttons

10.3: `InlineKeyboardButton.disabled = {}` (a `DisabledButton` object, currently empty) is the
button's **only** action — `{"text": "Sold out", "disabled": {}}`; `disabled` + `callback_data`,
`disabled: true`, `disabled: false` and `disabled: null` are all wrong. Rich buttons have the
same field. Choose deliberately:

| Situation | Do |
|---|---|
| Action temporarily unavailable, user should know it exists (Submit before the form is complete, sold-out size) | **disable** + say why in the text |
| Action will never apply to this user/state | **remove** the button |
| Action finished (Approved, Sent) | replace with a disabled status label, or remove the keyboard |
| User can still act but needs an explanation | keep it enabled and explain on tap (`answerCallbackQuery`) |

Disabled is presentation, not authorization: old messages, other clients and crafted callbacks
still reach the bot — re-check state and rights on every callback. Old clients may render an
unknown field differently; the label must make sense either way. After an error, restore a
working control (re-enable or offer Retry) — never leave a screen with only disabled buttons.

## force_reply on keyboards

10.3 added `force_reply` to `InlineKeyboardMarkup` and `ReplyKeyboardMarkup`: keep the buttons
**and** open the reply field, so the user can tap an option or type an answer. The old `ForceReply`
object shows the reply field but then the message has no keyboard.

* Inline `force_reply` "can't be changed when the inline keyboard is edited" — decide it when
  sending; repeat the same value in every edit of that message; for a different value send a new
  message (`--previous` check in the validator).
* Use for form steps whose answer may be typed (name, phone, amount) with quick options;
  don't use it on menus (it steals the keyboard) or in channels.
* The bot still receives the reply as a normal message: validate it and check it replies to the
  **current** step's message (`examples/python/tgkit/forms.py`).
