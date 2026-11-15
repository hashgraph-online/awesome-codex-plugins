# 81 — Event registration, waitlist and staff check-in

> Evidence: offline model + private-chat callback adapter, checked 2026-11-15.
> The Telegram surface uses ordinary sendMessage/editMessageText/answerCallbackQuery.
> No live Telegram client, external backend or production concurrency is verified.

1. **Request and visible result.** Register attendees up to capacity, then promote people from the waitlist when a place opens.

2. **Reuse before extending.** Start with R22 booking, R82 reminders and R23 entry links. Domain rules live in
   `examples/python/tgkit/journeys.py::Event`; the shared UI adapter is
   `examples/python/tgkit/journey_panel.py`. It reuses `ScreenFlow`, `I18n`,
   `btn`, `kb` and `FakeTransport`, rather than inventing a second callback framework.
   Product choices below are design decisions, not Telegram API requirements.

3. **Requirements and context.** The runnable surface is private chat, standard text and
   callback buttons; no new widget, Rich Message or Premium requirement. Route `message`
   and `callback_query` updates when integrating. Domain events and operator actions are
   trusted server inputs, never instructions parsed from an arbitrary message.
   Check the actual SDK and current API before connecting a transport.

4. **Screens and payload.** Transcript:
   [r81-journey.json](../examples/payloads/r81-journey.json).
   EN/RU copy is exercised by the demo and tests.

   | State | Controls | Meaning |
   |---|---|---|
   | Full event | Join / waitlist | No false confirmation or payment. |
   | Waitlisted | Cancel registration | Private status without other attendee names. |
   | Promoted | Registration status | The model promotes FIFO; notification delivery is separate. |
   | Staff check-in | Domain call in demo; no staff UI yet | Check current staff rights and confirmed registration. |

5. **Runnable code.**
   ```bash
   python examples/python/recipes/r80_87_product_journeys.py --scenario R81
   python examples/python/recipes/r80_87_product_journeys.py --scenario R81 --lang ru
   ```
   This prints an offline verification summary. Read the transcript for exact wire
   payloads. The UI acknowledges callbacks before domain work, edits the same message,
   and refuses another user or an older screen. No token or network is used.

6. **State and invariants.** unregistered → confirmed or waitlisted → cancelled; waitlisted → confirmed → checked in.

   One attendee occupies at most one place. Cancellation promotes the first waiting attendee; duplicate check-in does not count twice.
   The callback adapter also rejects action arguments and rechecks availability server-side;
   hiding a control is not authorization. Persistent records must retain owner, business ID
   and revision independently of the Telegram message ID.

7. **User-visible outcome.** Check current staff rights and confirmed registration.
   Titles, labels and refusal messages support English and Russian. State labels are localized; terminal screens retain a Show status control.
   Adapt the sample copy and input screens to the product before shipping. No screen claims the external operation succeeded from a local model result.

8. **Failure paths and production boundary.** Duplicate joins preserve position; a waitlisted user cannot check in; cancelling after check-in is refused.

   Capacity operations are sequential in memory. Production needs one database transaction/lock for join and promotion, an outbox for promotion messages, opaque expiring ticket tokens and a separate authorized staff interface. Do not expose a user ID as a reusable entrance ticket.
   In-memory models are single-process teaching code. For multiple workers, atomically commit
   state changes and delivery intents; reconcile external outcomes rather than retrying sends blindly.

9. **Checks.** `tests/test_journey_library.py::test_event_capacity_promotion_and_checkin` covers the distinguishing
   domain behavior. The same suite replays all eight scenarios in both languages, compares EN
   payloads to committed transcripts, validates keyboard/API shape, and checks stale/foreign taps.
   `python scripts/run_checks.py` includes these tests. This is not a live-client test.

10. **Adaptation and sources.** Follow [the extension contract](../references/example-library.md); add only the
    missing domain behavior, in the user's project.
    [Telegram Bot Features](https://core.telegram.org/bots/features); [Telegram Bot API](https://core.telegram.org/bots/api).

