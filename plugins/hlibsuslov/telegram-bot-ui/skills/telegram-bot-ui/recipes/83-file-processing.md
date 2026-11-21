# 83 — File processing with cancellation and late-result protection

> Evidence: offline model + private-chat callback adapter, checked 2026-11-15.
> The Telegram surface uses ordinary sendMessage/editMessageText/answerCallbackQuery.
> No live Telegram client, external backend or production concurrency is verified.

1. **Request and visible result.** Summarize a PDF, show progress and let the user cancel without receiving a late result.

2. **Reuse before extending.** Start with R27 AI assistant, R54 job progress and Machine. Domain rules live in
   `examples/python/tgkit/journeys.py::FileJob`; the shared UI adapter is
   `examples/python/tgkit/journey_panel.py`. It reuses `ScreenFlow`, `I18n`,
   `btn`, `kb` and `FakeTransport`, rather than inventing a second callback framework.
   Product choices below are design decisions, not Telegram API requirements.

3. **Requirements and context.** The runnable surface is private chat, standard text and
   callback buttons; no new widget, Rich Message or Premium requirement. Route `message`
   and `callback_query` updates when integrating. Domain events and operator actions are
   trusted server inputs, never instructions parsed from an arbitrary message.
   Check the actual SDK and current API before connecting a transport.

4. **Screens and payload.** Transcript:
   [r83-journey.json](../examples/payloads/r83-journey.json).
   EN/RU copy is exercised by the demo and tests.

   | State | Controls | Meaning |
   |---|---|---|
   | Waiting | Use sample PDF | PDF and 5 MB are this product's sample policy. |
   | Queued | Cancel processing | No invented percentage. |
   | Cancelled | No result actions | Late completion cannot deliver a result. |
   | Running / ready / failed | Domain transitions tested separately | Worker and result-upload interfaces are not implemented. |

5. **Runnable code.**
   ```bash
   python examples/python/recipes/r80_87_product_journeys.py --scenario R83
   python examples/python/recipes/r80_87_product_journeys.py --scenario R83 --lang ru
   ```
   This prints an offline verification summary. Read the transcript for exact wire
   payloads. The UI acknowledges callbacks before domain work, edits the same message,
   and refuses another user or an older screen. No token or network is used.

6. **State and invariants.** waiting → queued → running → ready or failed; queued/running → cancelled.

   Completion applies only to the active generation in running state. Cancellation removes the file reference and invalidates worker output.
   The callback adapter also rejects action arguments and rechecks availability server-side;
   hiding a control is not authorization. Persistent records must retain owner, business ID
   and revision independently of the Telegram message ID.

7. **User-visible outcome.** Worker and result-upload interfaces are not implemented.
   Titles, labels and refusal messages support English and Russian. State labels are localized; terminal screens retain a Show status control.
   Adapt the sample copy and input screens to the product before shipping. No screen claims the external operation succeeded from a local model result.

8. **Failure paths and production boundary.** Wrong MIME hint, zero bytes or over-policy size is refused; repeated completion is a no-op; cancellation wins over a later completion.

   No PDF is downloaded or processed here. Wire document/voice updates only after checking owner, limits and subscription. Stream with an actual size cap, inspect file signatures, isolate conversion/OCR, limit CPU/time, and delete temporary bytes on completion or cancellation. MIME and file name are untrusted. Deliver artifacts only to the requesting user's private chat.
   In-memory models are single-process teaching code. For multiple workers, atomically commit
   state changes and delivery intents; reconcile external outcomes rather than retrying sends blindly.

9. **Checks.** `tests/test_journey_library.py::test_file_job_late_completion_and_failure` covers the distinguishing
   domain behavior. The same suite replays all eight scenarios in both languages, compares EN
   payloads to committed transcripts, validates keyboard/API shape, and checks stale/foreign taps.
   `python scripts/run_checks.py` includes these tests. This is not a live-client test.

10. **Adaptation and sources.** Follow [the extension contract](../references/example-library.md); add only the
    missing domain behavior, in the user's project.
    [Telegram: introduction to bots](https://core.telegram.org/bots); [Telegram Bot API](https://core.telegram.org/bots/api).

