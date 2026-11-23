# 26 — Learning bot: course map → lesson → quiz → result → streak → daily reminder

Product recipe (combines mechanisms; no registry row of its own). Uses 10.3 rich blocks (checklist
items, expandable quotation, button row), 10.3 `disabled` buttons and 9.4 button `style`. Verified
2026-11-15 against Bot API 10.4 (newest release on that date, 2026-11-09). Index of all product
recipes: `references/use-case-playbooks.md`. Tags: **[API]** = API requirement, **[official]** =
official recommendation, **[heuristic]** = design heuristic of this skill.

1. **Request and visible result.** “I teach Git basics in a bot. Show a course map, a short lesson
   with an example, a three-question quiz, a score, and a daily streak. Remind people to study, but
   not if they already did today.” — One lesson message that changes in place: a checklist course
   map, a lesson with a collapsed example and a *Start quiz* button, quiz questions whose answers
   lock after one tap (the chosen option gets ✓ or ✗, an explanation appears), a result with a
   progress bar and the streak, and a reminder that stays quiet when today's lesson is done or the
   user muted it.
2. **Why these features.**
   - Rich Message lesson: `heading`, `paragraph`, `expandable_blockquote` for the long example
     (collapsed by default, so the lesson stays short), and a `buttons` row with *Start quiz*
     inside the message **[API: InputRichBlockExpandableBlockQuotation (blocks since 10.5), InputRichBlockButtons, 10.3]**.
   - Course map as a `list` whose items carry `has_checkbox` and `is_checked` (done lessons are
     checked) **[API: InputRichBlockListItem]**; the lesson buttons stay in `reply_markup` so each
     lesson is one tap **[heuristic]**.
   - After an answer every option becomes `disabled: {}` (10.3) and the chosen one is prefixed ✓ or
     ✗ in its label: the screen shows what happened and cannot be tapped again **[heuristic]**.
     A disabled button “does nothing”, it does not stop stale or crafted callbacks, so the server
     also refuses a second answer **[API: the check is yours]**.
   - `style: "primary"` on the single next step (*Start quiz*, *Next question*, *Next lesson*)
     **[heuristic: one primary per screen]**.
   - Why buttons and not a native quiz: `sendPoll` with `type: "quiz"` and `correct_option_ids`
     (an **array** in the current API) is the standard alternative, with an `explanation` of 0-200
     characters shown on a wrong answer or the lamp **[API]**. Buttons give one message with
     “Question 2 of 3” progress, an explanation of any length for right *and* wrong answers, and a
     score and streak you own **[heuristic]**. Pick the poll when you want the native quiz look,
     quizzes in groups or no state at all.
   - Streak in the user's time zone: the `User` object has `language_code` but no time zone (the
     only `time_zone_name` in the reference is `BusinessOpeningHours`), so ask once and store it
     **[API, checked in the reference]**; day boundaries, “missed a day” and “once per day” are
     then plain integer arithmetic **[heuristic]**.
3. **Requirements.** Bot API ≥ 10.3 (button rows, expandable quotation, `disabled`); rich list
   items need 10.2. Production. Private chat. A job queue for reminders (the recipe uses the
   in-memory `Scheduler`; use a persistent one) and a stored time zone per user. Telegram does not
   deliver messages to users who blocked the bot, so a failed reminder should mute that user
   **[API: 403 Forbidden]**.
4. **Payload.** Full request sequence: `examples/payloads/r26-learning.json`. Incoming fixture:
   `examples/fixtures/usecase_learning_start.json` (Olena's `/start`, Ukrainian).

   | Screen | Message | Buttons (row by row) | Leaves to |
   |---|---|---|---|
   | map | rich: heading, streak line, checklist, hint | one row per lesson (`✓ ` prefix when done) | lesson |
   | lesson | rich: heading, paragraphs, expandable example, `Start quiz` row | `← Back` | quiz, map |
   | quiz (open) | rich: “Question i of 3”, question | one option per row | quiz (answered) |
   | quiz (answered) | + “Correct./Not quite.” and the explanation | options `disabled` (✓/✗ on the choice) · `Next question` / `See the result` primary | quiz, result |
   | result | rich: heading, `██░  2/3`, streak | `Next lesson` primary · `Course map` | lesson, map |
   | reminder | rich: one paragraph (new message) | `Open the lesson` primary · `Mute for a week` | lesson, map |

   Key parts:
   ```json
   {"type": "expandable_blockquote", "blocks": [{"type": "paragraph", "text": "git add notes.txt\ngit commit -m \"Add shopping list\"\ngit log --oneline\nThe log prints one line per commit: a short id and its message."}], "credit": "Example"}
   {"inline_keyboard": [[{"text": "✗ git clone", "disabled": {}}], [{"text": "git commit", "disabled": {}}], [{"text": "git fetch", "disabled": {}}], [{"text": "Next question", "callback_data": "lr:6:next", "style": "primary"}]]}
   {"type": "paragraph", "text": "██░  2/3"}
   ```
5. **Code.** `examples/python/recipes/r26_learning.py` (`Course.touch_streak`, `streak`,
   `plan_reminder`, `tick`; screens `map`, `lesson`, `quiz`, `result`, `reminder`; action `ans`) on
   top of `examples/python/tgkit/flows.py` (`ScreenFlow`, `Scheduler`, `UpdateDedup`, `I18n`) and
   `examples/python/tgkit/rich.py` (`expandable_quote`, `button_row`, `rich_button`). Lesson content
   is data (`LESSONS`), UI copy is `COPY` (en, uk). No TypeScript twin.
6. **Sequence and state.**
   ```mermaid
   stateDiagram-v2
     [*] --> map: /start
     map --> lesson: tap lesson
     lesson --> quiz: Start quiz (state reset)
     quiz --> quiz: answer (once) → Next question
     quiz --> result: See the result (progress saved, streak touched once per local day)
     result --> lesson: Next lesson
     result --> map
     [*] --> reminder: 18:00 local, not done today, not muted
     reminder --> lesson
     reminder --> map: Mute for a week
   ```
   User state: `done {lesson: best score}`, `streak`, `last_day` (local day number), `tz`,
   `muted_until`, `quiz {lesson, q, answers, score}`. The streak rule: same day → unchanged;
   yesterday → +1; anything older → 1; the map shows 0 when `today - last_day > 1`. Every render
   bumps a version carried in `callback_data` (`lr:<ver>:ans:<q>:<option>`, well under 64 bytes), so
   a tap on an older render is `stale` before any action runs. The reminder job is keyed by user
   (`rem:<uid>`) so rescheduling replaces it.
7. **Result.** Mock-ups (not client screenshots), English / Ukrainian:
   ```
   Question 2 of 3                           Питання 2 з 3
   Which command records staged changes?     Яка команда записує підготовлені зміни?
   [ ✗ git clone ]   (disabled)              [ ✗ git clone ]   (disabled)
   [ git commit ]    (disabled)              [ git commit ]    (disabled)
   [ git fetch ]     (disabled)              [ git fetch ]     (disabled)
   Not quite. git commit records what        Не зовсім. git commit записує те, що
   git add staged.                           підготував git add.
   [ Next question ]                         [ Наступне питання ]
   ```
8. **Typical mistake, limits, alternative.** Mistakes: counting the streak in UTC (a user in UTC+2
   who studies at 23:30 and 00:30 gets two days, not one); saving the streak on every lesson
   instead of once per local day; leaving answered options tappable and counting twice; sending the
   reminder without checking today's progress; no way to mute; running the reminder as a loop in
   the bot process (it dies with a restart: store jobs). Limits **[API]**: `callback_data` ≤ 64
   bytes; a rich button row holds 1-8 buttons; rich message ≤ 32768 characters; `explanation` of a
   native quiz ≤ 200 characters. Failure paths in the run: double tap on the old render →
   “screen has changed”; crafted answer for an answered question with the current version →
   “You already answered this question.”; another user's tap → “belongs to someone else”; reminder
   skipped when done, sent when not, skipped while muted; a missed day restarts the streak at 1.
   Alternative: a native quiz poll per question when no per-answer explanation is needed; a Mini
   App when you need timers, images or drag-and-drop.
9. **Run and verify.** `py -3 examples/python/recipes/r26_learning.py` (11 self-checks) ·
   `cd tests && py -3 -m unittest test_usecases` (validators on every markup and rich message,
   64-byte callbacks, copy in en/uk, payload drift) · `py -3 scripts/validate_rich.py` on an
   extracted `rich_message`. Evidence: offline contract; no real chat was used, the scheduler is
   driven by a scripted clock.
10. **Adapt.** Keep: the version-in-callback guard, “answer recorded once” on the server, the
    once-per-local-day streak rule, the skip reasons of the reminder (`done`, `muted`, `busy`).
    Replace: `LESSONS` with your course (store it in a database, one row per language), `TZ` with a
    stored per-user zone (an IANA name is better than an offset because of daylight saving), the
    in-memory `Scheduler` with a persistent queue, the 18:00 hour with a user setting. Add spaced
    repetition by scheduling a review job per lesson, or a leaderboard in a group card
    (`recipes/28-group-expense-split.md` shows the shared-card pattern). Related:
    `recipes/20-shop.md` (same screen flow), `recipes/24-settings.md` (where the time zone and
    mute setting live), `references/buttons-and-styles.md`, `references/tables.md`.
