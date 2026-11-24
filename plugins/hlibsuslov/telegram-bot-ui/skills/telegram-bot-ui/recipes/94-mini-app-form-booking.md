# 94 — Form and booking in a Mini App, result back to the chat

Product recipe (no registry row). Verified 2026-11-23 against Bot API 10.5 and the Mini Apps page.
Layout: `references/mini-apps/layout-rules.md` §7-8. Tags: **[API]**, **[official]**, **[heuristic]**.

1. **Request and visible result.** “Let people book a table or a trainer from the bot: pick a time, how many
   people, a name.” — A reply-keyboard button opens the form; the app shows a day strip, a slot grid with
   taken times struck through, a summary line and “Book Tue 18:00 · €30”; the chat gets one confirmation;
   bad data gets a visible answer instead of silence.
2. **Why these features.** `sendData` works only for reply-keyboard launches and closes the app
   **[official]**; inline-button launches answer with `answerWebAppQuery` instead **[API]**. `web_app_data`
   comes from Telegram but its content is user-controlled: size limit and schema **[official]/[heuristic]**.
   Booking layout L16, form layout L15 **[heuristic]**. Unsaved input turns on closing confirmation
   **[official]**; drafts go to `CloudStorage` **[heuristic]**.
3. **Requirements.** Private chat (keyboard `web_app` buttons); `sendData` ≤ 4096 bytes **[official]**.
4. **Payload.** `examples/payloads/r94-form-booking.json`: the keyboard with a `web_app` button, the
   confirmation with `remove_keyboard`, and the “did not come through” answer to bad data.
5. **Code.** Bot: `r90_99_mini_apps.py::r94` (`booking_schema`), `bot_side.py::on_web_app_data`. App:
   `examples/mini-apps/catalog` → Trainers → a trainer (day strip `.tma-days`, slots `.tma-slots`, summary
   `.tma-summary`, MainButton naming the slot); the vanilla pickup form (labels above fields, error under
   the field, closing confirmation).
6. **Sequence and state.**
   ```mermaid
   sequenceDiagram
     participant B as Bot
     participant A as Mini App (reply keyboard)
     B->>A: keyboard button "Choose a time"
     A->>A: day → slot → summary (draft in CloudStorage)
     A->>B: sendData({"slot","people","name"}) (app closes)
     B->>B: schema check
     B-->>A: confirmation in the chat, keyboard removed
   ```
7. **Result.** “Table for 2 on 28 Nov at 19:30 is booked. I will remind you an hour before.”
8. **Typical mistake, limits, alternative.** Hidden taken slots; a month calendar as the only picker;
   placeholders as labels; trusting `web_app_data` without a schema; expecting `sendData` from an inline
   launch. Alternative: 1-3 questions with `force_reply` (recipe 03); a booking widget (recipe 51).
9. **Run and verify.** `py -3 examples/python/recipes/r90_99_mini_apps.py r94` (2 self-checks) ·
   `py -3 scripts/miniapp_layout.py example booking` then `review` · preview the catalogue example.
   Evidence: offline contract and mock preview.
10. **Adapt.** Keep: schema checks, visible error answers, the L16 order. Replace: slots from your
    availability API (hold a slot for a few minutes while the user confirms). Related: recipes 22 (booking
    bot), 51 (booking widget), 96 (settings).
