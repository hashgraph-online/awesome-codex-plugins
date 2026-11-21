# 86 — Custom loyalty points with replay-safe earning and redemption

> Evidence: offline model + private-chat callback adapter, checked 2026-11-15.
> The Telegram surface uses ordinary sendMessage/editMessageText/answerCallbackQuery.
> No live Telegram client, external backend or production concurrency is verified.

1. **Request and visible result.** Credit points once per settled order and redeem a reward once per request.

2. **Reuse before extending.** Start with R20 order lifecycle; R25 for actual Stars purchases. Domain rules live in
   `examples/python/tgkit/journeys.py::Loyalty`; the shared UI adapter is
   `examples/python/tgkit/journey_panel.py`. It reuses `ScreenFlow`, `I18n`,
   `btn`, `kb` and `FakeTransport`, rather than inventing a second callback framework.
   Product choices below are design decisions, not Telegram API requirements.

3. **Requirements and context.** The runnable surface is private chat, standard text and
   callback buttons; no new widget, Rich Message or Premium requirement. Route `message`
   and `callback_query` updates when integrating. Domain events and operator actions are
   trusted server inputs, never instructions parsed from an arbitrary message.
   Check the actual SDK and current API before connecting a transport.

4. **Screens and payload.** Transcript:
   [r86-journey.json](../examples/payloads/r86-journey.json).
   EN/RU copy is exercised by the demo and tests.

   | State | Controls | Meaning |
   |---|---|---|
   | Balance | Redeem 80 points | 100 sample points; clearly not money or Stars. |
   | Redeemed | No additional redeem button for this reward | Balance 20 and original redemption retained. |
   | Insufficient / conflicting request | Domain refusals | No negative balance or changed amount under the same key. |

5. **Runnable code.**
   ```bash
   python examples/python/recipes/r80_87_product_journeys.py --scenario R86
   python examples/python/recipes/r80_87_product_journeys.py --scenario R86 --lang ru
   ```
   This prints an offline verification summary. Read the transcript for exact wire
   payloads. The UI acknowledges callbacks before domain work, edits the same message,
   and refuses another user or an older screen. No token or network is used.

6. **State and invariants.** trusted settled event → credited; reward preview → redeemed or insufficient balance.

   Credit deduplication uses a receipt ID and validates the original amount. Redemption uses an owner-bound request ID and fixed server-side cost.
   The callback adapter also rejects action arguments and rechecks availability server-side;
   hiding a control is not authorization. Persistent records must retain owner, business ID
   and revision independently of the Telegram message ID.

7. **User-visible outcome.** No negative balance or changed amount under the same key.
   Titles, labels and refusal messages support English and Russian. State labels are localized; terminal screens retain a Show status control.
   Adapt the sample copy and input screens to the product before shipping. No screen claims the external operation succeeded from a local model result.

8. **Failure paths and production boundary.** Duplicate events are no-ops; same key with another amount is a conflict; foreign user and insufficient balance are refused.

   Trusted credit is never a callback handler. Production requires a transactional ledger, unique constraints, refund/reversal events, reward inventory and fulfillment. Add a reward preview and confirmation before a real redemption. This is neither a Telegram Stars wallet nor Telegram's native Affiliate Programs.
   In-memory models are single-process teaching code. For multiple workers, atomically commit
   state changes and delivery intents; reconcile external outcomes rather than retrying sends blindly.

9. **Checks.** `tests/test_journey_library.py::test_loyalty_replay_conflict_and_balance` covers the distinguishing
   domain behavior. The same suite replays all eight scenarios in both languages, compares EN
   payloads to committed transcripts, validates keyboard/API shape, and checks stale/foreign taps.
   `python scripts/run_checks.py` includes these tests. This is not a live-client test.

10. **Adaptation and sources.** Follow [the extension contract](../references/example-library.md); add only the
    missing domain behavior, in the user's project.
    [Telegram: introduction to bots](https://core.telegram.org/bots); [Affiliate Programs](https://telegram.org/blog/affiliate-programs-ai-sticker-search).

