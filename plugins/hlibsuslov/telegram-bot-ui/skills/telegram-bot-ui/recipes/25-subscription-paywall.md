# 25 — Subscription: paywall, one 7-day trial, a Stars subscription, cancel and expiry

Product recipe (combines mechanisms; no registry row of its own). Uses `createInvoiceLink` with
`subscription_period`, `editUserStarSubscription`, `successful_payment` recurring fields, regular-HTML
`<tg-time>`, 9.4 button `style`, `10.3` disabled buttons. Verified 2026-11-15 against Bot API 10.4
(newest release on that date, 2026-11-09). Payments depth: `references/payments-and-stars.md`
(payments stream); one-off purchases: [recipe 20](20-shop.md); index of all product recipes:
`references/use-case-playbooks.md`. Tags: **[API]** = API requirement, **[official]** = official
recommendation, **[heuristic]** = design heuristic of this skill.

1. **Request and visible result.** “Part of the bot is for subscribers: ⭐ 150 a month, with a free
   7-day trial. People must be able to cancel inside the bot, we must remind them before it ends, and
   nobody gets two trials or two charges.” — A free user who opens the gated feature sees the
   paywall: what Pro includes, the price, a primary `Start 7-day trial` and `Subscribe ⭐ 150/month`.
   The trial starts once. `Subscribe` is a URL button to an invoice link. After paying, the status
   screen says “Renews on <date>” with `Cancel renewal`; cancelling keeps access until the period
   ends and shows `Resume renewal`. Reminders go out 3 and 1 days before the end of a trial or of a
   cancelled subscription; after the end the user sees an expired screen with `Subscribe ⭐ …`.
2. **Why these features.**
   - Subscription link: `createInvoiceLink` with `subscription_period: 2592000` (30 days is the only
     value), `currency: "XTR"`, **exactly one** `LabeledPrice`, price ≤ 10000 Stars **[API]**. A link
     opens the invoice from a URL button, so the paywall stays one edited message **[heuristic]**.
   - `successful_payment` carries `is_recurring`, `is_first_recurring` and
     `subscription_expiration_date` **[API]**: take the expiry from the update, never compute it.
   - `editUserStarSubscription(user_id, telegram_payment_charge_id, is_canceled)`: `true` stops the
     next extension (the subscription stays active to the period end), `false` re-enables one the bot
     cancelled **[API]**. This is the in-bot “Cancel renewal” people expect **[heuristic]**.
   - `/paysupport` must be answered by any bot that takes payments **[official,
     https://core.telegram.org/bots/payments-stars]**.
   - Digital goods and services are sold for Stars **[official, same page]**.
   - `disabled: {}` for the used trial: the option stays visible and says why **[heuristic]**; the
     server still refuses a crafted tap **[API: "does nothing"; the check is yours]**.
   - Stars subscriptions are not tied to one per user: *“Any number of subscriptions can be active
     for a given bot at the same time, including multiple concurrent subscriptions from the same
     user”* **[API]** — so pre-checkout refuses a second one.
3. **Requirements.** Bot API ≥ 10.3 for the disabled button (subscriptions and `<tg-time>` are older).
   Production. Private chat. `allowed_updates` must include `pre_checkout_query`, `message` (the
   payment arrives as a service message) and `callback_query`. A job queue that survives restarts
   (here an in-memory `Scheduler`). Store the latest `telegram_payment_charge_id` per user: both
   cancelling and refunds (`refundStarPayment`) need it.
4. **Payload.** Full request sequence: `examples/payloads/r25-subscription.json`. Incoming fixtures:
   `examples/fixtures/usecase_subscription_pre_checkout.json`,
   `examples/fixtures/usecase_subscription_first_payment.json`,
   `examples/fixtures/usecase_subscription_renewal.json`.

   | Screen | Message | Buttons (row by row) | Leaves to |
   |---|---|---|---|
   | paywall | “Pro — what is included, ⭐ 150 per month” | `Start 7-day trial` primary (disabled `Trial used` after) · `Subscribe ⭐ 150/month` (URL) | status / invoice |
   | status (trial) | “Pro trial — full access until <date>” | `Subscribe ⭐ 150/month` (URL) primary | invoice |
   | status (active) | “Pro is active — renews on <date>” | `Cancel renewal` danger | status (canceled) |
   | status (canceled) | “Renewal is off: access ends <date>” | `Resume renewal` primary | status (active) |
   | reminder | “Your trial ends in 3 d” / “Pro ends in 3 d” | URL subscribe / `Resume renewal` | invoice / status |
   | expired | “Pro has ended — your access ended <date>” | `Subscribe ⭐ …` (URL) | invoice |

   Key parts:
   ```json
   {"method": "createInvoiceLink", "params": {"title": "Pro, 30 days", "payload": "sub:111111111",
     "provider_token": "", "currency": "XTR", "prices": [{"label": "Pro, 30 days", "amount": 150}],
     "subscription_period": 2592000}}
   {"method": "editUserStarSubscription", "params": {"user_id": 111111111,
     "telegram_payment_charge_id": "stxDEMOsub0001", "is_canceled": true}}
   ```
   Incoming `successful_payment` (first payment): `{"currency": "XTR", "total_amount": 150,
   "invoice_payload": "sub:111111111", "subscription_expiration_date": 1797854400, "is_recurring": true,
   "is_first_recurring": true, "telegram_payment_charge_id": "stxDEMOsub0001", …}`.
5. **Code.** `examples/python/recipes/r25_subscription.py` (`Subscriptions.link`, `schedule`,
   `on_pre_checkout`, `on_payment`, `set_renewal`, `tick`) on top of
   `examples/python/tgkit/flows.py` (`ScreenFlow`, `OnceStore`, `UpdateDedup`, `Scheduler`,
   `tg_time`, `btn(url=…)`). No TypeScript twin.
6. **Sequence and state.**
   ```mermaid
   stateDiagram-v2
     [*] --> free: /start
     free --> trial: Start trial (once per user)
     free --> active: payment (is_first_recurring)
     trial --> active: payment
     trial --> expired: until + grace
     active --> active: renewal (is_recurring, new expiry)
     active --> canceled: Cancel renewal
     canceled --> active: Resume (screen or reminder)
     canceled --> expired: until + grace
     active --> expired: no renewal by until + grace
     expired --> active: payment
   ```
   Subscription record: `{status, until, charge, trial_used}`. Jobs per user, replaced by key on every
   change: `sb:<uid>:exp` at `until + 6 h` (a renewal can arrive a little after the period ends),
   `sb:<uid>:r3` / `r1` only for `trial` and `canceled` (an auto-renewing user is not warned). Every
   job carries the `until` it was made for; at run time a changed `until` or status means it is
   skipped. Payments are applied once per `telegram_payment_charge_id`; a webhook retry has the same
   `update_id` and is dropped earlier.
7. **Result.** Mock-ups (not client screenshots), English / Ukrainian:
   ```
   Pro                                   Pro
   This part is for subscribers.         Ця частина для підписників.
   • Unlimited exports                   • Експорт без обмежень
   • Priority support                    • Пріоритетна підтримка
   ⭐ 150 per month, cancel any time.    ⭐ 150 на місяць, скасувати можна будь-коли.
   [ Start 7-day trial ]                 [ Спробувати 7 днів ]
   [ Subscribe ⭐ 150/month ]            [ Підписатися ⭐ 150/міс ]
   Pro is active                         Pro активний
   Renewal is off: access ends 15.12     Продовження вимкнено: доступ до 15.12
   [ Resume renewal ]                    [ Відновити продовження ]
   ```
8. **Typical mistake, limits, alternative.** Mistakes: computing the expiry yourself instead of using
   `subscription_expiration_date`; fulfilling on pre-checkout; applying a redelivered payment twice;
   expiring a user at exactly `until` before the renewal update arrives (hence the grace window);
   reminders that still go out after a renewal or a resume; a second trial after resubscribing;
   forgetting `/paysupport`; a concurrent second subscription. Limits **[API]**: title 1–32,
   description 1–255, payload 1–128 bytes, exactly one price item, `subscription_period` only
   `2592000`, `answerPreCheckoutQuery` within 10 s, `callback_data` ≤ 64 bytes. Failure paths in the
   run: second trial tap → alert; another user's tap → alert; a second pre-checkout while active →
   refused with a reason; duplicate payment (same update and same charge id) → applied once; a stale
   reminder button → toast. Alternative: a one-off “pass” (recipe 20 pattern) when users don't want
   recurring billing; channel access with `createChatSubscriptionInviteLink` (separate API) when the
   product is a paid channel (`references/channels-and-broadcasting.md`).
9. **Run and verify.** `py -3 examples/python/recipes/r25_subscription.py` (11 self-checks) ·
   `py -3 -m unittest tests/test_usecases.py` (validators on every markup, 64-byte callbacks, copy in
   en/uk, payload drift). Evidence: offline contract; real Stars charges, renewals and
   `editUserStarSubscription` were not executed.
10. **Adapt.** Keep: expiry from the update, one `OnceStore` key per charge id, jobs keyed per user
    with the `until` guard, the grace window, the pre-checkout re-check. Replace: `SUB_STARS`, the
    feature list, the entitlement check (`entitled`), the in-memory dicts (a `subscriptions` table
    with `charge_id` and `until`), the clock (`NOW` → real time), `Scheduler` → your queue. Add a
    refund path (`refundStarPayment`) and a daily reconciliation for users whose renewal never
    arrived. Related: `recipes/20-shop.md` (one-off payments), `references/buttons-and-styles.md`,
    `references/localization-and-rtl.md`, `references/errors-and-fallbacks.md`.
