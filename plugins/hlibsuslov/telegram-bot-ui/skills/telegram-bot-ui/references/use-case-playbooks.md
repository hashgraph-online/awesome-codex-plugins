---
summary: "Complete product playbooks for 'build me a bot for X', indexed by product and by user phrase, with shared invariants and a newest-feature chooser; read when a request names a whole product."
verified: "2026-11-15"
bot_api: "10.4"
---

# Use-case playbooks: complete product models for "build me a bot for X"

> Verified 2026-11-15 against Bot API 10.4 (newest release on that date). Each playbook is a
> runnable recipe (`recipes/NN-*.md` + `examples/python/recipes/rNN_*.py` + payload file) with a
> screen/state map, every message and keyboard, handlers, state, errors, copy in two languages and
> the 9.4-10.4 features that make it better. Mechanism recipes 01-09 teach single features; these
> teach whole products. Archetype view: [bot-archetypes.md](bot-archetypes.md).

## Contents

- [How to use a playbook](#how-to-use-a-playbook)
- [Index by product](#index-by-product)
- [Index by what the user says](#index-by-what-the-user-says)
- [Shared invariants (all playbooks)](#shared-invariants-all-playbooks)
- [Choosing among the newest features (9.4-10.4)](#choosing-among-the-newest-features-94-104)

## How to use a playbook

For broader discovery, search `recipes/use-cases.json` and read the
[reuse/extension contract](example-library.md). Recipes R80–R87 add distinct offline
models for leads, events/waitlists, reminders, file jobs, moderation review, feedback,
loyalty and service queues. Their docs explicitly distinguish implemented callback
demos from production integration work; they are not full deployed bot products.

1. Match the request to a row below (by product **or** by the phrasing users actually use).
2. Read the recipe's screen/state map first, then its failure paths (point 8).
3. Copy the runnable code, keep its invariants (see "Shared invariants"), replace the catalog,
   copy and storage. Validate every keyboard with `scripts/validate_keyboard.py` and every rich
   message with `scripts/validate_rich.py`; audit the copy with `scripts/audit_copy.py`.
4. Combine playbooks freely: a café bot = 22 booking + 20 shop + 23 onboarding + 24 settings.

## Index by product

| # | Product | Typical requests | Key screens | Features used (version) | Context |
|---|---|---|---|---|---|
| [20](../recipes/20-shop.md) | Shop / ordering | "catalog with a cart", "pay with Stars or card", "people pay twice" | catalog · item · cart · checkout · invoice · receipt | disabled buttons (10.3), `style` (9.4), Stars `XTR` / provider invoice, `pre_checkout_query`, compact table (10.3) | private |
| [21](../recipes/21-support-desk.md) | Support desk | "tickets to our operators", "answer from the group", "rate the support" | new ticket · operator topic · relay · status · rating | `force_reply` on keyboards (10.3), forum topics per ticket, `style`, disabled rating | private + operator forum |
| [22](../recipes/22-booking.md) | Appointment booking | "book a slot", "reschedule", "send reminders" | service · date · slot · confirm · my bookings · reminder | disabled taken slots (10.3), `<tg-time>`, danger confirm (9.4), scheduled reminders | private |
| [23](../recipes/23-onboarding.md) | Onboarding / first run | "people leave after /start", "referral links", "ask for the phone" | (empty chat) · language · updates · phone · home | per-language commands/descriptions, deep links, `request_contact`, `is_ephemeral` commands (10.2) | private |
| [24](../recipes/24-settings.md) | Settings / preferences | "settings are a mess", "Back goes to the start", "accidental delete" | root · toggles · pickers · confirm · undo | back stack, disabled selected value (10.3), `danger` (9.4) | private (+ group redirect) |
| [25](../recipes/25-subscription-paywall.md) | Subscription / paywall / trial | "monthly plan in Stars", "free trial", "remind before it ends" | paywall · trial · invoice link · status · cancel · expired | `createInvoiceLink` + `subscription_period`, `editUserStarSubscription`, `is_recurring`, `/paysupport` | private |
| [26](../recipes/26-learning-bot.md) | Learning bot | "lesson then quiz", "progress and streaks" | course · lesson · quiz · result · streak · reminder | Rich Messages (headings, expandable quote; Start quiz on the keyboard), disabled answered options (10.3) | private |
| [27](../recipes/27-ai-assistant-product.md) | AI assistant product | "modes", "stream with Stop", "regenerate", "thumbs up/down", "send a PDF" | modes · draft · answer · feedback · history · file | `sendRichMessageDraft` + `can_stop` (10.3), `stopped_message_generation` (10.3), `force_reply` reasons (10.3) | private |
| [28](../recipes/28-group-expense-split.md) | Group utility (expense split) | "split costs in our group chat", "my balance privately" | shared card · personal panel · add expense · settle up | ephemeral replies to callbacks (10.3/10.4), shared card edited in place | supergroup |
| [29](../recipes/29-community.md) | Community bot | "approve join requests after rules", "welcome newcomers", "roles" | join request DM · rules · approve · welcome · role picker | `chat_join_request` + `user_chat_id` (5 min), `can_send_welcome_messages` (10.3), `community_chat_joined` (10.3), `setChatMemberTag` | supergroup + private |
| [60](../recipes/60-inline-mode.md) | Inline-mode bot | "share a card in any chat", "@bot search" | query · results · chosen result · shared message with buttons | `answerInlineQuery` (`button`, `next_offset`, `is_personal`), `chosen_inline_result`, edits by `inline_message_id` | any chat via inline |
| [61](../recipes/61-business-account.md) | Business-account assistant | "reply to my customers for me", "quick replies" | connection rights · customer chat · owner panel · quick reply | `business_connection` rights, `business_message`, `business_connection_id` sends, `readBusinessMessage` | business chats + private |
| [62](../recipes/62-monitoring-alerts.md) | Monitoring / alerts | "alert me when it's down", "mute", "daily digest" | watches · add watch · settings · alert · digest | `force_reply` threshold input (10.3), `disable_notification`, compact table digest (10.3), mute jobs | private |
| [63](../recipes/63-search-and-long-lists.md) | Search and long lists | "filters", "pagination", "nothing found" | query · filters · results · detail · empty · too many | `pager_row` with disabled ends (10.3), compact table compare (10.3), server-side query ids | private |
| [64](../recipes/64-delivery-tracker.md) | Delivery / order tracker | "one status card that updates", "notify when it's close" | status card · ETA · change address · rate | in-place edits, `<tg-time>`, disabled "too late" action (10.3), widget alternative (10.4, private) | private |

Neighbouring streams (reference by name): channel posting and mailings —
[channels-and-broadcasting.md](channels-and-broadcasting.md) and recipes 30-39; agents operating a
bot for an operator — recipes 40-49; HTML widgets and their design system — recipes 50-59 and
`references/widget-*.md`; payments and inline mode in depth — `references/payments-and-stars.md`,
`references/inline-mode.md`.

## Index by what the user says

| They say… | Start with |
|---|---|
| "people pay twice" / "two orders from one tap" | 20 (`OnceStore` by order), 03 |
| "it shows sold-out things" / "hide what isn't available" | 20, 22 (disable, don't hide) |
| "our operators answer in a group" | 21 |
| "remind them before the appointment" / "before the trial ends" | 22, 25 |
| "the bot is confusing for new users" / "deep link to a product" | 23 |
| "what the bot says after /start" / "the greeting with a picture" / "приветственное сообщение" | `welcome-message.md`, then 23 |
| "our notifications look messy" / "a template for alerts and reports" / "оформи уведомления" | `message-patterns.md` |
| "Back takes me to the start" / "settings everywhere" | 24 |
| "free trial" / "monthly subscription" / "paywall" | 25 |
| "quiz" / "course" / "streak" | 26 |
| "like ChatGPT" / "stop button" / "regenerate" / "rate the answer" | 27, 01 |
| "private answer in the group" / "split the bill" / "lunch order" | 28, 04 |
| "approve join requests" / "welcome message" for group newcomers / "rules" / "roles" | 29 |
| "@mybot in any chat" / "share a card" | 60 |
| "answer my customers" / "Telegram Business" | 61 |
| "alert", "threshold", "mute", "digest" | 62, 09 |
| "too many results" / "filters" / "pagination" / "nothing found" | 63 |
| "one message that updates" / "where's my order" | 64, 05, 09 |

## Shared invariants (all playbooks)

These are implemented once in `examples/python/tgkit/flows.py` and its TypeScript twin
`examples/ts/usecases/flows.ts`:

| Invariant | Why | Mechanism |
|---|---|---|
| `callback_data` ≤ 64 **bytes** | **[API]** 1-64 bytes; Cyrillic is 2 bytes per letter | `pack()` refuses longer data; keep ids short, store queries server-side |
| An old render's buttons don't act | Telegram delivers every tap, also from old messages and double taps **[heuristic]** | version in `callback_data`, `ScreenFlow.handle()` → `stale` |
| One user can't act on another's state | anyone in a group can tap any button **[API behaviour]** | message → owner map → `not_yours` (alert in the presser's language) |
| Creating / charging / sending happens once | retries, double taps and redelivered updates **[heuristic]** | `OnceStore` keyed by a business id; `UpdateDedup` by `update_id` |
| Every callback is answered exactly once | the client spinner waits otherwise **[API]** | `ScreenFlow.answer()` dedupes by query id |
| Status changes are explicit | a delivered parcel can't go back to "packed" **[heuristic]** | `Machine` raises `IllegalTransition` |
| Unavailable ≠ invisible | users learn what exists and why it's unavailable **[heuristic]** | `disabled: {}` (10.3) + reason in text; server re-checks anyway **[API]** |
| Copy exists in every language | missing keys fall back silently otherwise | `I18n.missing()` is empty; `audit_copy.py` |
| Personal content keeps its audience | group chats are shared timelines **[heuristic]** | ephemeral replies, deep links to the private chat |
| Time is shown in the reader's time zone | users travel; servers are UTC | `<tg-time unix=…>` / `date_time` entities (`flows.tg_time`) |

## Choosing among the newest features (9.4-10.4)

| Need | Use | Not |
|---|---|---|
| pick an option **or** type a value | inline keyboard + `force_reply: true` (10.3) | two messages |
| show an option that exists but can't be chosen | `disabled: {}` (10.3) with the reason in text | removing it |
| one clear next step | `style: "primary"` on one button (9.4) | styling every button |
| irreversible action | `style: "danger"` + confirmation + undo window | a one-tap delete |
| a private answer inside a group | ephemeral reply to the callback (10.3/10.4) | posting it "for everyone" |
| a long answer that streams | `sendRichMessageDraft` + `can_stop` (10.3) | per-token edits |
| a table people compare | Rich Message table with `is_compact` (10.3) | monospace art |
| an object whose state moves (private chat) | widget (10.4, production private only) or an edited message | a new message per step |
| a brand icon on a button | `icon_custom_emoji_id` (9.4) with a Unicode fallback | emoji in some labels, icons in others |
