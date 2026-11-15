# Worked scenarios (before → after)

Sixteen situations that cover most real UI requests: 1-7 are single-screen fixes, 8-16 come
from the product playbooks (recipes 20-29 and 60-69, `use-case-playbooks.md`, verified 2026-11-15
against Bot API 10.4). Code is illustrative — adapt
to the project's actual SDK and style; never paste a framework the project
doesn't use.

---

## 1. Improve only the text — change no logic

**Request:** "Rewrite this message, it's unclear."

**Before**

```python
await message.answer(
    "ERROR: request failed with code 500. Something went wrong. "
    "Please try again later or contact the administrator if the problem persists.",
    reply_markup=kb,
)
```

**After**

```python
await message.answer(
    "⚠️ Couldn't load your orders.\n"
    "This is on our side — try again in a minute.",
    reply_markup=kb,          # untouched
)
```

**What was allowed to change:** wording only.
**What was preserved:** `reply_markup`, handler, parse mode, i18n key.
**If the project has i18n**, the edit belongs in the catalog entry
(`orders.load_failed`), in every locale — not inline at the call site.

**Report line:** *"Text only. No keyboard, callback, or handler changes."*

---

## 2. Rebuild an overloaded inline keyboard

**Request:** "This menu is a mess."

**Before** — 9 buttons in one column, no hierarchy, destructive action mixed in:

```json
{"inline_keyboard": [
  [{"text": "Profile", "callback_data": "profile"}],
  [{"text": "My orders", "callback_data": "orders"}],
  [{"text": "Order history", "callback_data": "orders_old"}],
  [{"text": "Settings", "callback_data": "settings"}],
  [{"text": "Language", "callback_data": "lang"}],
  [{"text": "Notifications", "callback_data": "notify"}],
  [{"text": "Support", "callback_data": "help"}],
  [{"text": "Delete account", "callback_data": "acc_del"}],
  [{"text": "New order", "callback_data": "order_new"}]
]}
```

**After** — grouped by topic, primary action first, settings collapsed one level
down, destruction moved off the main screen:

```json
{"inline_keyboard": [
  [{"text": "New order", "callback_data": "order_new", "style": "primary"}],
  [{"text": "My orders", "callback_data": "orders"},
   {"text": "History", "callback_data": "orders_old"}],
  [{"text": "Profile", "callback_data": "profile"},
   {"text": "Settings", "callback_data": "settings"}],
  [{"text": "Support", "callback_data": "help"}]
]}
```

"Language" and "Notifications" now live inside `settings`; "Delete account"
lives inside `profile` behind a confirmation.

**Preserved:** every `callback_data` string. The `settings` screen must now
render the two moved buttons with their original payloads (`lang`, `notify`), so
old messages keep working.

**Report line:** *"Regrouped 9 → 4 rows, moved 2 items under Settings and
`acc_del` behind a confirmation. All callback payloads unchanged; the Settings
screen now hosts `lang`/`notify` verbatim."*

---

## 3. Add `primary`, `success`, and `danger`

**Request:** "Make the important buttons stand out."

**Before**

```json
{"inline_keyboard": [
  [{"text": "Save", "callback_data": "draft:save"}],
  [{"text": "Publish", "callback_data": "draft:publish"}],
  [{"text": "Delete draft", "callback_data": "draft:delete"}],
  [{"text": "Back", "callback_data": "menu"}]
]}
```

**After**

```json
{"inline_keyboard": [
  [{"text": "Publish", "callback_data": "draft:publish", "style": "success"}],
  [{"text": "Save as draft", "callback_data": "draft:save"}],
  [{"text": "Delete draft", "callback_data": "draft:delete", "style": "danger"}],
  [{"text": "← Back", "callback_data": "menu"}]
]}
```

Reasoning to state in the report:

- `Publish` commits the flow → `success`, and it moves to the top as the
  expected action.
- `Save as draft` is a legitimate alternative, not the main path → unstyled.
- `Delete draft` is irreversible → `danger`, kept last, and it routes to a
  confirmation screen where the confirming button is `danger` and the escape is
  unstyled.
- `Back` stays unstyled.
- No `primary` here: on a screen whose job is to commit, `success` *is* the main
  action. Adding `primary` too would create two focal points.

---

## 4. Custom emoji and color together

**Request:** "Put our branded icons on the quiz buttons."

**Preconditions to check first** (`custom-emoji.md`): the bot either purchased
additional usernames on Fragment, or its owner has Telegram Premium and the
message goes directly to a private/group/supergroup chat. Bot API ≥ 9.4 in the
installed SDK.

```json
{"inline_keyboard": [
  [{"text": "Finish the test",
    "icon_custom_emoji_id": "5368324170671202286",
    "style": "success",
    "callback_data": "finish_test"}],
  [{"text": "Continue later",
    "icon_custom_emoji_id": "5368324170671202111",
    "callback_data": "pause_test"}],
  [{"text": "← Back to topics", "callback_data": "topics"}]
]}
```

Rules applied: the icons cover a coherent group (the two test actions) rather
than one lonely button; the navigation row stays plain; both labels are complete
sentences without their icons; the IDs came from `getCustomEmojiStickers` and
live in config, not inline; no Unicode emoji were mixed into the same keyboard.

---

## 5. The `custom_emoji_id` is unknown

**Request:** "Add a custom emoji to the Confirm button."

**Do not** put a plausible-looking number in the code. Do this instead:

1. Implement the button with the field plumbed through from config, unset by
   default, so the UI works today:

```python
def confirm_button(icon_id: str | None = None) -> dict:
    btn = {"text": "Confirm order", "callback_data": "order:confirm", "style": "success"}
    if icon_id:
        btn["icon_custom_emoji_id"] = icon_id
    return btn
```

2. Ask the user for the ID **and** show them how to get one:

> I need the actual `custom_emoji_id` — it can't be guessed. Any of these works:
> **(a)** send the emoji to the bot once and read `custom_emoji_id` from the
> `custom_emoji` entity in that message; **(b)** call `getStickerSet` for the
> pack and read `custom_emoji_id` off the sticker; **(c)** if you already have
> candidate IDs, confirm them with `getCustomEmojiStickers` (≤200 per call).
> Also: is the bot eligible — Fragment usernames, or owner Premium with the
> message going to a private/group/supergroup chat?

3. Ship the rest of the redesign; don't block it on the ID.

---

## 6. The SDK doesn't support Bot API 9.4 yet

**Symptom:** the installed SDK's `InlineKeyboardButton` has no `style` /
`icon_custom_emoji_id`; a strict, typed SDK raises on unknown kwargs, or the
field is silently dropped before it reaches Telegram.

**Step 1 — verify, don't guess** (`sdk-compatibility.md`):

```bash
python -c "from aiogram.types import InlineKeyboardButton as B; print('style' in B.model_fields)"
grep -rn "icon_custom_emoji_id" node_modules/@grammyjs/types node_modules/typegram 2>/dev/null
```

**Step 2 — present both options with their cost:**

- **Upgrade the SDK** to a version implementing Bot API ≥ 9.4. Review its
  breaking changes first; this is the clean path when the project can absorb it.
- **Raw payload for these calls only** — keep it behind one adapter, never in
  business logic:

```python
markup = {"inline_keyboard": [[
    {"text": "Confirm", "callback_data": "ok", "style": "success"},
]]}
await bot_api_raw("sendMessage", {          # existing project transport
    "chat_id": chat_id,
    "text": text,
    "reply_markup": json.dumps(markup),      # JSON-serialized
})
```

**Step 3 — degrade honestly.** If neither is acceptable right now, ship the
keyboard without `style`, note it as a deferred item, and **say so** — never
claim colors were added when the field never left the process.

**Report line:** *"aiogram 3.x here has no `style`; shipped the restructured
keyboard without color and added `bot_api_raw` as an opt-in path. Colors turn on
after the SDK upgrade tracked in <issue>."*

---

## 7. When color and emoji should NOT be added

**Request:** "Make the catalog colorful."

**Refuse with a reason and offer the real fix.**

```json
{"inline_keyboard": [
  [{"text": "Running shoes", "callback_data": "cat:1"}],
  [{"text": "Trail shoes", "callback_data": "cat:2"}],
  [{"text": "Sandals", "callback_data": "cat:3"}],
  [{"text": "‹ Prev", "callback_data": "cat:p:1"},
   {"text": "2/7", "callback_data": "noop"},
   {"text": "Next ›", "callback_data": "cat:p:3"}],
  [{"text": "← Back to menu", "callback_data": "menu"}]
]}
```

Why nothing is styled: these are **equal options**. `style` is semantic — if all
of them are `primary`, none of them is. The three values also can't express a
brand palette (no HEX/RGB/CSS exists in the Bot API).

The same applies to emoji: a per-category emoji here would add noise, not
information, and a custom emoji would additionally require Fragment/Premium
eligibility for zero UX gain.

**What actually improves this screen:** clearer category names, pagination that
tells you where you are, a search entry point
(`switch_inline_query_current_chat`), and a fixed navigation row.

**Report line:** *"Left the option list unstyled deliberately — `style` is
semantic (primary/success/danger only) and coloring equal options removes
hierarchy. Added pagination context and search instead."*

---

## 8. Hidden sold-out items → disabled, with the reason (shop, recipe 20)

**Request:** "People ask whether we still sell the Colombia. It's sold out, so we removed it."

**Before** — the item disappears; the `+` button is hidden at the stock limit, so the row jumps:

```json
{"inline_keyboard": [[{"text": "Ethiopia · ⭐ 250", "callback_data": "item:eth"}],
                     [{"text": "Kenya · ⭐ 300", "callback_data": "item:ken"}]]}
```

**After** — visible but unavailable (Bot API 10.3 `DisabledButton`), same row shape:

```json
{"inline_keyboard": [[{"text": "Ethiopia Yirgacheffe · ⭐ 250", "callback_data": "sh:1:item:eth"}],
                     [{"text": "Colombia Huila · ⭐ 220", "disabled": {}}],
                     [{"text": "Kenya Nyeri AA · ⭐ 300", "callback_data": "sh:1:item:ken"}]]}
```

`disabled` is the button's only action field **[API]**. The server still refuses a crafted or
stale "add" for a sold-out item **[API: the button "does nothing"; your check does the rest]**.

**Report line:** *"Sold-out items are shown disabled instead of hidden; stock is re-checked on
every add and again at pre-checkout."*

---

## 9. "Pay" sends a new invoice every tap → one invoice per cart revision (shop, recipe 20)

**Request:** "Customers tap Pay three times and get three invoices; some paid twice."

**Before**

```python
async def on_pay(cq):
    await bot.send_invoice(cq.from_user.id, "Order", "Coffee", payload=str(uuid4()),
                           currency="XTR", prices=[LabeledPrice("Coffee", total)])
```

**After** — the order belongs to the cart revision; the invoice is sent once per order and method;
`pre_checkout_query` compares currency, amount and stock with the stored order; fulfilment is
keyed by `telegram_payment_charge_id`:

```python
order = order_for_cart(session)                      # same cart revision -> same order
_, first = invoices.run(f"{order.id}:xtr", lambda: send_invoice(order, "xtr"))
if not first:
    answer(cq, "Your invoice is below ↓")            # no second invoice
```

**Report line:** *"Pay is idempotent per cart revision; an invoice for a changed cart is refused
at pre-checkout with a reason; a redelivered successful_payment is applied once."*

---

## 10. Four onboarding messages → three skippable steps and a useful empty state (recipe 23)

**Request:** "New users get four messages after /start and leave."

**Before** — welcome text, rules, a phone request and a menu at once; the phone keyboard never
goes away; returning users see it all again.

**After** — the empty chat already explains the bot (`setMyDescription`, per language); `/start`
shows *Language → Updates (Notify me / Not now) → Phone (Share / Skip)*; then:

```
All set, Bogdan
You have no orders yet. Start with the catalog — fresh roast every Monday.
[ Open the catalog ]          (primary)
[ My orders ] [ Settings ]
```

The reply keyboard is one-time and removed afterwards; a returning `/start` says "Welcome back"
with the latest order.

**Report line:** *"Onboarding cut to 3 skippable steps; descriptions and commands set per
language; returning users skip it; empty states name one next action."*

---

## 11. A delete button on the settings root → confirm + undo window (recipe 24)

**Request:** "Someone deleted their account with one accidental tap."

**Before**

```json
{"inline_keyboard": [[{"text": "Language", "callback_data": "lang"}],
                     [{"text": "Delete account", "callback_data": "delete_now"}]]}
```

**After** — the root only opens a confirmation; the red button is not the first under the thumb;
deletion runs after a 30-second Undo window:

```json
{"inline_keyboard": [[{"text": "Cancel", "callback_data": "st:e:back"}],
                     [{"text": "Delete everything", "callback_data": "st:e:delete", "style": "danger"}]]}
```

**Report line:** *"Destructive action moved behind a confirmation with `style: danger` and a
30 s undo; a double confirm schedules one deletion; a late Undo is refused."*

---

## 12. Toggle labels that state the action → labels that state the state (recipe 24)

**Request:** "Users can't tell whether notifications are on."

**Before:** `[Turn off shipping updates]` `[Turn on offers]` — the label flips meaning after each
tap, and a double tap turns it back.

**After:** `[✓ Shipping updates]` `[✗ Offers and news]` — one message edited in place; each render
carries a version in `callback_data`, so the second tap of a double tap is refused as stale and
can't flip the value back.

**Report line:** *"Toggles show state (✓/✗), edit in place, and ignore double taps."*

---

## 13. A typed date → date and slot pickers with taken slots disabled (booking, recipe 22)

**Request:** "Clients type dates in ten formats and book taken slots."

**Before:** "Send the date and time (DD.MM HH:MM)".

**After:** a 7-day picker (past and full days disabled), then slots with taken ones disabled, then
a confirmation that shows the time with `<tg-time unix="…" format="wDT">…</tg-time>`, so every
reader sees their own time zone. Two clients racing for one slot: the second gets "just taken" and
a refreshed list; reminders are keyed jobs that a reschedule replaces.

**Report line:** *"Free-text dates replaced by pickers; taken slots disabled, not hidden; the
confirmation shows a date-time entity; a double confirm creates one booking."*

---

## 14. Personal balances posted in the group → shared card + ephemeral panels (recipe 28)

**Request:** "When someone taps 'My balance', the bot posts everyone's debts in the chat."

**Before:** `sendMessage(chat_id=group, text="Alice owes Bogdan ₴450 …")` for every tap.

**After:** the shared card shows only totals; "My balance" answers with an ephemeral message to
the presser (10.4: `ephemeral_message_parameters: {"callback_query_id": …}`), falling back to an
alert (≤ 200 chars) or a deep link to the private chat — never to the group.

**Report line:** *"Personal data moved to ephemeral panels; the group card shows totals only;
fallbacks keep the audience."*

---

## 15. A silent 20-second wait → a streamed answer with Stop, then feedback (AI, recipe 27)

**Request:** "Our assistant is silent while it thinks and people tap 'Regenerate' blindly."

**Before:** `sendChatAction(typing)` … then one long message.

**After:** `sendRichMessageDraft` with real stage labels and `can_stop: true` (10.3); a Stop
(`stopped_message_generation`) cancels the model and keeps the partial answer marked incomplete;
the final answer carries `👍 / 👎 / Regenerate`; 👎 asks for a reason with an inline keyboard of
reasons **plus** the reply field (`force_reply: true` on the keyboard, 10.3).

**Report line:** *"Answers stream with Stop; one finalization per answer; feedback once per
answer; regenerate retires the old buttons."*

---

## 16. "No results." → why, and the one tap that fixes it (search, recipe 63)

**Request:** "Search often says 'No results' and people give up."

**Before**

```
No results.
```

**After**

```
Nothing matches “дизайнер” with Remote + Senior.
Try without a filter:
[ Remove filter: Remote ] [ Remove filter: Senior ]
[ Change the query ]
```

Pagination keeps its shape with `← 2/5 →`: the arrows are disabled at the ends (10.3) and the
counter is a disabled button. The query itself is stored on the server and only its id travels in
`callback_data` (a Cyrillic query exceeds 64 bytes quickly: 2 bytes per letter).

**Report line:** *"Empty results explain the cause and offer one-tap filter removal; pagination
shows position; callback data carries ids, not queries."*
