# 84 — Moderation report review with scoped staff decisions

> Evidence: offline model + private-chat callback adapter, checked 2026-11-15.
> The Telegram surface uses ordinary sendMessage/editMessageText/answerCallbackQuery.
> No live Telegram client, external backend or production concurrency is verified.

1. **Request and visible result.** Send a report to moderators; only staff of the correct group can decide on the current case.

2. **Reuse before extending.** Start with R29 community and R40 bound approvals. Domain rules live in
   `examples/python/tgkit/journeys.py::Moderation`; the shared UI adapter is
   `examples/python/tgkit/journey_panel.py`. It reuses `ScreenFlow`, `I18n`,
   `btn`, `kb` and `FakeTransport`, rather than inventing a second callback framework.
   Product choices below are design decisions, not Telegram API requirements.

3. **Requirements and context.** The runnable surface is private chat, standard text and
   callback buttons; no new widget, Rich Message or Premium requirement. Route `message`
   and `callback_query` updates when integrating. Domain events and operator actions are
   trusted server inputs, never instructions parsed from an arbitrary message.
   Check the actual SDK and current API before connecting a transport.

4. **Screens and payload.** Transcript:
   [r84-journey.json](../examples/payloads/r84-journey.json).
   EN/RU copy is exercised by the demo and tests.

   | State | Controls | Meaning |
   |---|---|---|
   | Review | Dismiss report | Private staff case, not a public accusation. |
   | Planned | No repeated decision | Records a decision only; no deletion request is sent. |
   | Remove alternative | Domain method, not an executable UI button | Requires a confirmation and current bot rights before real execution. |

5. **Runnable code.**
   ```bash
   python examples/python/recipes/r80_87_product_journeys.py --scenario R84
   python examples/python/recipes/r80_87_product_journeys.py --scenario R84 --lang ru
   ```
   This prints an offline verification summary. Read the transcript for exact wire
   payloads. The UI acknowledges callbacks before domain work, edits the same message,
   and refuses another user or an older screen. No token or network is used.

6. **State and invariants.** pending → planned; external execution would add executing / applied / unknown / failed.

   Decision binds actor, chat, message and revision. A new report on a pending case (`add_report`) bumps the revision, so a screen opened before it is stale; the second decision is stale even if it comes from another valid moderator.
   The callback adapter also rejects action arguments and rechecks availability server-side;
   hiding a control is not authorization. Persistent records must retain owner, business ID
   and revision independently of the Telegram message ID.

7. **User-visible outcome.** Requires a confirmation and current bot rights before real execution.
   Titles, labels and refusal messages support English and Russian. State labels are localized; terminal screens retain a Show status control.
   Adapt the sample copy and input screens to the product before shipping. No screen claims the external operation succeeded from a local model result.

8. **Failure paths and production boundary.** Wrong group or non-staff actor is refused; forged action is refused; competing moderator decisions cannot both apply in the sequential model.

   The supplied staff set is a trusted test input, not proof of live rights. Refresh membership/rights at execution, redact report previews, add an appeal path, and store a case/audit log. The example deliberately has no ban or delete transport. For a removal request, preserve an unknown outcome on timeout and reconcile before retry.
   In-memory models are single-process teaching code. For multiple workers, atomically commit
   state changes and delivery intents; reconcile external outcomes rather than retrying sends blindly.

9. **Checks.** `tests/test_journey_library.py::test_moderation_scope_and_revision` covers the distinguishing
   domain behavior. The same suite replays all eight scenarios in both languages, compares EN
   payloads to committed transcripts, validates keyboard/API shape, and checks stale/foreign taps.
   `python scripts/run_checks.py` includes these tests. This is not a live-client test.

10. **Adaptation and sources.** Follow [the extension contract](../references/example-library.md); add only the
    missing domain behavior, in the user's project.
    [Telegram Bot Features](https://core.telegram.org/bots/features); [Telegram Bot API](https://core.telegram.org/bots/api).

