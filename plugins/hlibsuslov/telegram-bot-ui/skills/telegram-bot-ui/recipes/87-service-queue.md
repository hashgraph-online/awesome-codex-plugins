# 87 — Service queue with private tickets and staff advancement

> Evidence: offline model + private-chat callback adapter, checked 2026-11-15.
> The Telegram surface uses ordinary sendMessage/editMessageText/answerCallbackQuery.
> No live Telegram client, external backend or production concurrency is verified.

1. **Request and visible result.** Give each customer one place in a queue and let staff call one customer at a time.

2. **Reuse before extending.** Start with R21 staff handoff and R64 private status card. Domain rules live in
   `examples/python/tgkit/journeys.py::ServiceQueue`; the shared UI adapter is
   `examples/python/tgkit/journey_panel.py`. It reuses `ScreenFlow`, `I18n`,
   `btn`, `kb` and `FakeTransport`, rather than inventing a second callback framework.
   Product choices below are design decisions, not Telegram API requirements.

3. **Requirements and context.** The runnable surface is private chat, standard text and
   callback buttons; no new widget, Rich Message or Premium requirement. Route `message`
   and `callback_query` updates when integrating. Domain events and operator actions are
   trusted server inputs, never instructions parsed from an arbitrary message.
   Check the actual SDK and current API before connecting a transport.

4. **Screens and payload.** Transcript:
   [r87-journey.json](../examples/payloads/r87-journey.json).
   EN/RU copy is exercised by the demo and tests.

   | State | Controls | Meaning |
   |---|---|---|
   | Entry | Take a ticket | Shows only the viewer's place. |
   | Waiting | Leave queue | Position is not an ETA. |
   | Called | "It is your turn" | Only staff can advance and complete; the staff surface remains to build. |
   | Closed | Domain refusal | No new tickets; existing queue can be drained. |

5. **Runnable code.**
   ```bash
   python examples/python/recipes/r80_87_product_journeys.py --scenario R87
   python examples/python/recipes/r80_87_product_journeys.py --scenario R87 --lang ru
   ```
   This prints an offline verification summary. Read the transcript for exact wire
   payloads. The UI acknowledges callbacks before domain work, edits the same message,
   and refuses another user or an older screen. No token or network is used.

6. **State and invariants.** outside → waiting → called → completed; waiting → cancelled.

   Joining twice preserves one position. Calling next twice returns the same active customer; completion binds the expected customer.
   The callback adapter also rejects action arguments and rechecks availability server-side;
   hiding a control is not authorization. Persistent records must retain owner, business ID
   and revision independently of the Telegram message ID.

7. **User-visible outcome.** No new tickets; existing queue can be drained.
   Titles, labels and refusal messages support English and Russian. State labels are localized; terminal screens retain a Show status control.
   Adapt the sample copy and input screens to the product before shipping. No screen claims the external operation succeeded from a local model result.

8. **Failure paths and production boundary.** Non-staff call/complete is refused; cancelling a called ticket is refused; a stale completion cannot clear a different active customer.

   Add a shared transactional queue per branch, stable ticket IDs instead of identities in callbacks, staff UI, accessibility, no-show handling and durable notification delivery. Do not estimate wait time from queue length without service-duration evidence.
   In-memory models are single-process teaching code. For multiple workers, atomically commit
   state changes and delivery intents; reconcile external outcomes rather than retrying sends blindly.

9. **Checks.** `tests/test_journey_library.py::test_queue_identity_and_staff_advancement` covers the distinguishing
   domain behavior. The same suite replays all eight scenarios in both languages, compares EN
   payloads to committed transcripts, validates keyboard/API shape, and checks stale/foreign taps.
   `python scripts/run_checks.py` includes these tests. This is not a live-client test.

10. **Adaptation and sources.** Follow [the extension contract](../references/example-library.md); add only the
    missing domain behavior, in the user's project.
    [Telegram: introduction to bots](https://core.telegram.org/bots); [Telegram Bot API](https://core.telegram.org/bots/api).

