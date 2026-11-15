# 82 — Personal reminders with rescheduling and cancellation

> Evidence: offline model + private-chat callback adapter, checked 2026-11-15.
> The Telegram surface uses ordinary sendMessage/editMessageText/answerCallbackQuery.
> No live Telegram client, external backend or production concurrency is verified.

1. **Request and visible result.** Let users save, move and cancel a reminder without an old queued job firing later.

2. **Reuse before extending.** Start with Scheduler, R22 appointment reminders and R24 preferences. Domain rules live in
   `examples/python/tgkit/journeys.py::Reminder`; the shared UI adapter is
   `examples/python/tgkit/journey_panel.py`. It reuses `ScreenFlow`, `I18n`,
   `btn`, `kb` and `FakeTransport`, rather than inventing a second callback framework.
   Product choices below are design decisions, not Telegram API requirements.

3. **Requirements and context.** The runnable surface is private chat, standard text and
   callback buttons; no new widget, Rich Message or Premium requirement. Route `message`
   and `callback_query` updates when integrating. Domain events and operator actions are
   trusted server inputs, never instructions parsed from an arbitrary message.
   Check the actual SDK and current API before connecting a transport.

4. **Screens and payload.** Transcript:
   [r82-journey.json](../examples/payloads/r82-journey.json).
   EN/RU copy is exercised by the demo and tests.

   | State | Controls | Meaning |
   |---|---|---|
   | Schedule preview | Schedule for 10:00 UTC | Absolute date and UTC zone, visibly a fixed example. |
   | Scheduled | Move to 11:00 UTC; Cancel reminder | Shows the current time; replaces the same job key. |
   | Cancelled | Schedule for 10:00 UTC | Late leased jobs fail the generation check. |

5. **Runnable code.**
   ```bash
   python examples/python/recipes/r80_87_product_journeys.py --scenario R82
   python examples/python/recipes/r80_87_product_journeys.py --scenario R82 --lang ru
   ```
   This prints an offline verification summary. Read the transcript for exact wire
   payloads. The UI acknowledges callbacks before domain work, edits the same message,
   and refuses another user or an older screen. No token or network is used.

6. **State and invariants.** draft → scheduled → replaced schedule; scheduled → claimed; scheduled → cancelled. A claimed reminder is final: moving or cancelling it is refused, because the worker already owns delivery.

   A cancellation or reschedule increments the generation. A worker can claim only the current generation once. Claimed does not mean delivered.
   The callback adapter also rejects action arguments and rechecks availability server-side;
   hiding a control is not authorization. Persistent records must retain owner, business ID
   and revision independently of the Telegram message ID.

7. **User-visible outcome.** Late leased jobs fail the generation check.
   Titles, labels and refusal messages support English and Russian. State labels are localized; terminal screens retain a Show status control.
   Adapt the sample copy and input screens to the product before shipping. No screen claims the external operation succeeded from a local model result.

8. **Failure paths and production boundary.** Naive timestamps and past times are rejected; repeated worker claim returns false; cancellation invalidates an already leased job.

   This is a one-shot scheduling model with an injected clock, not a running daemon. Add an IANA time-zone picker, explicit handling of ambiguous/nonexistent DST times, durable jobs, leases and an outbox. Define snooze relative to the actual current time. Recurrence, quiet hours and post-send reconciliation are separate work.
   In-memory models are single-process teaching code. For multiple workers, atomically commit
   state changes and delivery intents; reconcile external outcomes rather than retrying sends blindly.

9. **Checks.** `tests/test_journey_library.py::test_reminder_timezone_cancel_and_lease` covers the distinguishing
   domain behavior. The same suite replays all eight scenarios in both languages, compares EN
   payloads to committed transcripts, validates keyboard/API shape, and checks stale/foreign taps.
   `python scripts/run_checks.py` includes these tests. This is not a live-client test.

10. **Adaptation and sources.** Follow [the extension contract](../references/example-library.md); add only the
    missing domain behavior, in the user's project.
    [Telegram: introduction to bots](https://core.telegram.org/bots); [Telegram Bot API](https://core.telegram.org/bots/api).

