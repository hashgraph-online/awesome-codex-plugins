# 80 — Lead intake with review and contact consent

> Evidence: offline model + private-chat callback adapter, checked 2026-11-15.
> The Telegram surface uses ordinary sendMessage/editMessageText/answerCallbackQuery.
> No live Telegram client, external backend or production concurrency is verified.

1. **Request and visible result.** Collect a quote request and pass it to sales only after the user reviews it.

2. **Reuse before extending.** Start with R03 form and R21 human handoff. Domain rules live in
   `examples/python/tgkit/journeys.py::Lead`; the shared UI adapter is
   `examples/python/tgkit/journey_panel.py`. It reuses `ScreenFlow`, `I18n`,
   `btn`, `kb` and `FakeTransport`, rather than inventing a second callback framework.
   Product choices below are design decisions, not Telegram API requirements.

3. **Requirements and context.** The runnable surface is private chat, standard text and
   callback buttons; no new widget, Rich Message or Premium requirement. Route `message`
   and `callback_query` updates when integrating. Domain events and operator actions are
   trusted server inputs, never instructions parsed from an arbitrary message.
   Check the actual SDK and current API before connecting a transport.

4. **Screens and payload.** Transcript:
   [r80-journey.json](../examples/payloads/r80-journey.json).
   EN/RU copy is exercised by the demo and tests.

   | State | Controls | Meaning |
   |---|---|---|
   | Draft | Use sample details; Submit; Discard draft | No data is submitted yet. |
   | Review | Allow contact about this request; Submit | Shows contact and request purpose. |
   | Missing consent | Same draft controls | Names what must be completed. |
   | Submitted | No duplicate submit control | Acknowledges local acceptance, not CRM delivery. |

5. **Runnable code.**
   ```bash
   python examples/python/recipes/r80_87_product_journeys.py --scenario R80
   python examples/python/recipes/r80_87_product_journeys.py --scenario R80 --lang ru
   ```
   This prints an offline verification summary. Read the transcript for exact wire
   payloads. The UI acknowledges callbacks before domain work, edits the same message,
   and refuses another user or an older screen. No token or network is used.

6. **State and invariants.** draft → reviewed details → consent → submitted; draft → cancelled.

   Consent goes through `give_consent` (owner, draft, details present). Editing details clears the previous consent. A repeat submit returns the same snapshot; a different actor cannot read it.
   The callback adapter also rejects action arguments and rechecks availability server-side;
   hiding a control is not authorization. Persistent records must retain owner, business ID
   and revision independently of the Telegram message ID.

7. **User-visible outcome.** Acknowledges local acceptance, not CRM delivery.
   Titles, labels and refusal messages support English and Russian. State labels are localized; terminal screens retain a Show status control.
   Adapt the sample copy and input screens to the product before shipping. No screen claims the external operation succeeded from a local model result.

8. **Failure paths and production boundary.** Submit before details/consent is refused; cancel clears the draft; submitted or cancelled drafts cannot be edited.

   The demo preloads synthetic details. Add real step-by-step text handlers using R03, validation, consent purpose/version, a durable submission ID and a transactional CRM outbox. CRM timeout means delivery unknown, not permission to create another lead.
   In-memory models are single-process teaching code. For multiple workers, atomically commit
   state changes and delivery intents; reconcile external outcomes rather than retrying sends blindly.

9. **Checks.** `tests/test_journey_library.py::test_lead_consent_snapshot_and_owner` covers the distinguishing
   domain behavior. The same suite replays all eight scenarios in both languages, compares EN
   payloads to committed transcripts, validates keyboard/API shape, and checks stale/foreign taps.
   `python scripts/run_checks.py` includes these tests. This is not a live-client test.

10. **Adaptation and sources.** Follow [the extension contract](../references/example-library.md); add only the
    missing domain behavior, in the user's project.
    [Introducing Telegram Business](https://telegram.org/blog/telegram-business).

