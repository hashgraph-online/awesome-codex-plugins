# 28 — Group utility: expense split on one shared card with personal panels

Product recipe (combines mechanisms; no registry row of its own). Uses 10.2-10.4 ephemeral replies
(10.4 form: `callback_query_id` without `receiver_user_id`), `editEphemeralMessageText`, 10.3
`disabled` buttons and 9.4 button `style`. Verified 2026-11-15 against Bot API 10.4 (newest release
on that date, 2026-11-09). Pattern depth: `recipes/04-shared-card-personal-panel.md` and
`references/ephemeral-and-personal.md`; index of all product recipes:
`references/use-case-playbooks.md`. Tags: **[API]** = API requirement, **[official]** = official
recommendation, **[heuristic]** = design heuristic of this skill.

1. **Request and visible result.** “We travel to Lviv as four people and keep losing track of who
   paid. A card in the group chat, and everyone's own balance only for them.” — One card in the
   supergroup (“Trip to Lviv · 4 people · total ₴2000 · Expenses: 2”) with *Add expense*,
   *My balance*, *Settle up*, edited in place and never carrying a person's amount. A tap opens a
   panel **only the presser sees**: the balance, the add-expense form (amount stepper, equal split or
   “you and …”), the personal list of payments to make or confirm. A non-member gets “join first”
   with a *Join* button.
2. **Why these features.**
   - Ephemeral reply to a callback query: `ephemeral_message_parameters: {callback_query_id}`
     **without** `receiver_user_id` shows the message only to the presser in any chat except channel
     direct-messages chats; `chat_id` may be omitted **[API, 10.4]**. It must happen within 15 seconds
     of the tap, delivery is not guaranteed, and `answerCallbackQuery` is still required
     **[API]**. The 10.3 form (`receiver_user_id` = presser plus `chat_id`) still works
     (`tgkit.ephemeral.ephemeral_params(cq, api="10.3")`).
   - Edits of a panel go through `editEphemeralMessageText(chat_id, receiver_user_id,
     ephemeral_message_id, text, reply_markup)`, deletion through `deleteEphemeralMessage`
     **[API, 10.2]**; the ids come from the tapped panel's own `message.ephemeral_message_id`
     (they “may be reused after the message is deleted or expires”) **[API]**.
   - Fallback chain that keeps the audience: ephemeral → `answerCallbackQuery` alert (text 0-200
     characters, only the presser sees it) → `answerCallbackQuery` with a `t.me/<bot>?start=…` link
     that opens the private chat. It never posts the balance to the group; `guard_audience`
     refuses a public send of personal content **[API for the fields; the rule is a heuristic]**.
     The link does not prove the user will start the bot: never promise “sent to your DM”.
   - Shared card = shared facts only (title, people, total, counts, “settling: 1 of 3”) so everyone
     may see it **[heuristic]**; individual amounts live in panels.
   - The amount counter is a `disabled` button (state, no action) between `−100` and `+100`
     **[API 10.3 for `disabled`]**; `style: "primary"` on *Add expense* on the card and on *Add ₴…*
     in the form, `"success"` on *Confirm* **[heuristic: one main action per surface]**.
   - Confirm is the creditor's alone: the server compares the presser with the creditor's id; a
     debtor or a bystander gets an alert naming who can confirm **[heuristic: group buttons are
     tappable by anyone; the API does not do this check]**.
3. **Requirements.** Bot API ≥ 10.4 for the callback-only ephemeral form (10.3 form needs the
   presser's id and `chat_id`); ephemeral messages in groups and supergroups, not in channel
   direct-messages chats. `allowed_updates` must include `callback_query` and `message`. An
   ephemeral message cannot carry `web_app` or `login_url` buttons (checked by
   `scripts/validate_keyboard.py --context ephemeral`). Production. The card itself is an ordinary
   message the bot may send and edit in the group.
4. **Payload.** Full request sequence: `examples/payloads/r28-group-expense-split.json`. Incoming
   fixture: `examples/fixtures/usecase_expense_panel_callback.json` (a callback *from an ephemeral
   panel*: `message.message_id` 0, `ephemeral_message_id`, `receiver_user`).

   | Screen | Message | Buttons (row by row) | Leaves to |
   |---|---|---|---|
   | card (group, shared) | “Trip to Lviv · 4 people · total ₴… / Expenses: n” (+ “Settling up: k of m confirmed”) | `Add expense` primary `My balance` · `Settle up` | panels |
   | balance (ephemeral) | paid by you, your share, “You owe / are owed ₴…” | `Settle up` `Close` | settle, closed |
   | add (ephemeral) | “Amount ₴1200 · Split: equally among 4” | `−100` `₴1200`(disabled) `+100` · `Equal split` · `✓ Name`… · `Add ₴1200` primary | saved |
   | settle (ephemeral) | “You pay Alice ₴200 — not paid yet” | `I paid Alice` · `Confirm Dana` success · `Close` | settle |
   | join first (ephemeral) | “Join Trip to Lviv first…” | `Join` primary | card updated |
   | long panel fallback | — | `answerCallbackQuery` alert, else deep link | — |

   Key parts:
   ```json
   {"method": "sendMessage", "params": {"ephemeral_message_parameters": {"callback_query_id": "cq1"}, "text": "<b>New expense</b>\nAmount: ₴1200\nSplit: equally among 4", "parse_mode": "HTML", "reply_markup": {"inline_keyboard": [[{"text": "−100", "callback_data": "ex:amt:1:-100"}, {"text": "₴1200", "disabled": {}}, {"text": "+100", "callback_data": "ex:amt:1:100"}], [{"text": "Equal split", "callback_data": "ex:eq:1"}], [{"text": "✓ Богдан", "callback_data": "ex:tog:1:222222222"}, {"text": "✓ Олена", "callback_data": "ex:tog:1:333333333"}, {"text": "✓ Dana", "callback_data": "ex:tog:1:444444444"}], [{"text": "Add ₴1200", "callback_data": "ex:save:1", "style": "primary"}]]}}}
   {"method": "editEphemeralMessageText", "params": {"chat_id": -1001234567890, "receiver_user_id": 111111111, "ephemeral_message_id": 5, "text": "Added ₴1200. Split: equally among 4.", "parse_mode": "HTML", "reply_markup": {"inline_keyboard": [[{"text": "Close", "callback_data": "ex:close"}]]}}}
   {"method": "answerCallbackQuery", "params": {"callback_query_id": "cq-long", "url": "https://t.me/trip_split_bot?start=bal_cryl7kya"}}
   ```
5. **Code.** `examples/python/recipes/r28_group_expense_split.py` (`Trip.card`, `refresh_card`, `respond`,
   `show_panel`, `fallback`, `on_draft`, `on_transfer`, `open_round`) on top of
   `examples/python/tgkit/ephemeral.py` (`ephemeral_params`, `guard_audience`) and
   `examples/python/tgkit/flows.py` (`pack`, `OnceStore`, `Machine`, `UpdateDedup`, `btn`, `kb`). The
   card is a shared message, so it does not use `ScreenFlow`'s per-user owner guard; the owner checks
   are per draft (`drafts[op].user`), per panel (`receiver_user`) and per payment
   (`transfers[id].to`). Copy: en, uk (the shared card uses the group language, panels the presser's).
6. **Sequence and state.**
   ```mermaid
   stateDiagram-v2
     [*] --> card: /trip in the group
     card --> balance: My balance (ephemeral)
     card --> add: Add expense (ephemeral, op id)
     add --> add: amount / split changes
     add --> card: Save (OnceStore per op id) → total updated
     card --> settle: Settle up (round of transfers)
     settle --> settle: debtor "I paid" (open → marked)
     settle --> card: creditor Confirm (marked → confirmed), round closes at 3 of 3
     card --> joinfirst: not a participant → Join
   ```
   Money: shares of one expense are integer; the remainder goes to the first participants in id
   order. Balance = paid − share (+/− confirmed transfers). A settlement round is a greedy match of
   the largest debtor with the largest creditor, frozen as transfers `t1…` with the `Machine`
   `open → marked → confirmed`. While a round is open, *Add expense* is refused (“Settling up is in
   progress”), because the balances must not move under people's feet. The op id of a form is
   issued by the server; `OnceStore` keyed by it makes a retried Save (new callback id, same op)
   create nothing.
7. **Result.** Mock-ups (not client screenshots), English panel / Ukrainian card:
   ```
   Group (everyone)                          Only you (ephemeral)
   Trip to Lviv · 4 учасн. · разом ₴2000     Your balance
   Витрат: 2                                 Paid by you: ₴800
   [ Додати витрату ] [ Мій баланс ]         Your share: ₴700
   [ Розрахуватись ]                         You are owed ₴100.
                                             [ Settle up ] [ Close ]
   ```
8. **Typical mistake, limits, alternative.** Mistakes: answering “My balance” with a public message
   (the whole chat reads it); putting amounts per person on the card; trusting that a button in a
   group belongs to whoever sees it; letting anyone confirm a payment; forgetting
   `answerCallbackQuery` after an ephemeral reply; creating the expense on every Save tap; changing
   balances while a settlement is in progress; telling the user “sent to your DM” after a deep
   link. Limits **[API]**: ephemeral reply within 15 s of the tap; alert text ≤ 200 characters;
   `start` parameter 1-64 characters of `A-Z a-z 0-9 _ -` (the recipe uses a counter-based token;
   in production use a random one stored per user); `callback_data` ≤ 64 bytes (`ex:tog:2:222222222`
   is 18). Failure paths in the run: ephemeral reply fails (403) → balance as a private alert; a
   long panel → deep link; a retried Save → “Already added.”; Save with only yourself in the split →
   “Pick at least one person”; Dana taps Bogdan's form → “belongs to someone else”; second “I paid”
   → stale; debtor or bystander confirming → “Only Alice can confirm this payment.”; Add during a
   round → locked. Alternative: a widget in a private chat for a rich balance view (production
   widgets are private-chat only, see `recipes/05-private-widget.md`); a web app when expenses need
   receipts and categories.
9. **Run and verify.** `py -3 examples/python/recipes/r28_group_expense_split.py` (10 self-checks) ·
   `cd tests && py -3 -m unittest test_usecases` (ephemeral sends are validated with the
   `ephemeral` context, 64-byte callbacks, copy in en/uk, payload drift) ·
   `py -3 scripts/validate_keyboard.py keyboard.json --context ephemeral`. Evidence: offline
   contract; the ephemeral failure is scripted, real delivery to a group was not exercised.
10. **Adapt.** Keep: the audience guard and the fallback order, shared facts on the card and
    personal facts in panels, `OnceStore` by client op id, the creditor-only confirm, the lock
    during settlement. Replace: the in-memory `Trip` with a database (members, expenses, transfers),
    whole-hryvnia amounts with minor units and a currency, `GROUP_LANG` with a chat setting, the
    greedy match with your own netting rule, the deep-link token with a random stored one and a
    `/start bal_<token>` handler that builds the private balance for the *starting* user. Add:
    comments on expenses, edit/delete by the payer, an export. Related:
    `recipes/04-shared-card-personal-panel.md`, `recipes/29-community.md`,
    `references/ephemeral-and-personal.md`, `references/errors-and-fallbacks.md`.
