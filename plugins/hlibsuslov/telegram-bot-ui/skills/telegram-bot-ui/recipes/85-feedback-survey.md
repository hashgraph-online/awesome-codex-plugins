# 85 — Identified feedback with required answers and withdrawal

> Evidence: offline model + private-chat callback adapter, checked 2026-11-15.
> The Telegram surface uses ordinary sendMessage/editMessageText/answerCallbackQuery.
> No live Telegram client, external backend or production concurrency is verified.

1. **Request and visible result.** Ask for a rating, allow skipping the comment, and let the user withdraw their response.

2. **Reuse before extending.** Start with R03 forms and R33 native polls for aggregate anonymous voting. Domain rules live in
   `examples/python/tgkit/journeys.py::Survey`; the shared UI adapter is
   `examples/python/tgkit/journey_panel.py`. It reuses `ScreenFlow`, `I18n`,
   `btn`, `kb` and `FakeTransport`, rather than inventing a second callback framework.
   Product choices below are design decisions, not Telegram API requirements.

3. **Requirements and context.** The runnable surface is private chat, standard text and
   callback buttons; no new widget, Rich Message or Premium requirement. Route `message`
   and `callback_query` updates when integrating. Domain events and operator actions are
   trusted server inputs, never instructions parsed from an arbitrary message.
   Check the actual SDK and current API before connecting a transport.

4. **Screens and payload.** Transcript:
   [r85-journey.json](../examples/payloads/r85-journey.json).
   EN/RU copy is exercised by the demo and tests.

   | State | Controls | Meaning |
   |---|---|---|
   | Question | Rate 5 / 5; Submit without comment | One example rating option; real questionnaire supplies the scale. |
   | Incomplete | Same draft actions | Names the required missing answer. |
   | Submitted | Withdraw response | Response is tied to the account, explicitly not anonymous. |
   | Withdrawn | No answer controls | Stored answers removed in this model. |

5. **Runnable code.**
   ```bash
   python examples/python/recipes/r80_87_product_journeys.py --scenario R85
   python examples/python/recipes/r80_87_product_journeys.py --scenario R85 --lang ru
   ```
   This prints an offline verification summary. Read the transcript for exact wire
   payloads. The UI acknowledges callbacks before domain work, edits the same message,
   and refuses another user or an older screen. No token or network is used.

6. **State and invariants.** draft → submitted → withdrawn; draft answers remain editable.

   Rating is mandatory and constrained to 1–5; comments are optional. A withdrawn response cannot be resubmitted by replaying its old controls.
   The callback adapter also rejects action arguments and rechecks availability server-side;
   hiding a control is not authorization. Persistent records must retain owner, business ID
   and revision independently of the Telegram message ID.

7. **User-visible outcome.** Stored answers removed in this model.
   Titles, labels and refusal messages support English and Russian. State labels are localized; terminal screens retain a Show status control.
   Adapt the sample copy and input screens to the product before shipping. No screen claims the external operation succeeded from a local model result.

8. **Failure paths and production boundary.** Missing rating or an invalid field/value is refused; another user cannot read/withdraw the response; repeated submit returns the same answers.

   Add question navigation, a full rating scale and review UI. Document retention, backups and how aggregate analytics handle withdrawal. Do not advertise anonymity while retaining user IDs. Use a native anonymous poll when individual follow-up is unnecessary.
   In-memory models are single-process teaching code. For multiple workers, atomically commit
   state changes and delivery intents; reconcile external outcomes rather than retrying sends blindly.

9. **Checks.** `tests/test_journey_library.py::test_survey_optional_comment_and_withdrawal` covers the distinguishing
   domain behavior. The same suite replays all eight scenarios in both languages, compares EN
   payloads to committed transcripts, validates keyboard/API shape, and checks stale/foreign taps.
   `python scripts/run_checks.py` includes these tests. This is not a live-client test.

10. **Adaptation and sources.** Follow [the extension contract](../references/example-library.md); add only the
    missing domain behavior, in the user's project.
    [Telegram Bot Features](https://core.telegram.org/bots/features); [Telegram Bot API](https://core.telegram.org/bots/api).

