# 22 — Appointment booking: service → day → time → confirm, with reminders, reschedule and cancel

Product recipe (combines mechanisms; no registry row of its own). Uses `10.3-K01` disabled buttons,
regular-HTML `<tg-time>` (the reader's own time zone), 9.4 button `style`. Verified 2026-11-15 against
Bot API 10.4 (newest release on that date, 2026-11-09). Index of all product recipes:
`references/use-case-playbooks.md`. Tags: **[API]** = API requirement, **[official]** = official
recommendation, **[heuristic]** = design heuristic of this skill.

1. **Request and visible result.** “A salon takes bookings by phone. Let people book in the bot:
   pick a service, a day this week, a free time, and get reminded. Two people must never get the same
   slot, and cancelling must not be one careless tap.” — One menu message that changes in place
   (services → days → times → confirm → “You are booked”). Days with no free time and times already
   taken are visible but greyed out. The confirm screen shows the visit with `<tg-time>`, so a
   traveller sees it in their own zone. Reminders arrive 24 h and 2 h before with `I'll be there` /
   `Reschedule`. Cancel asks first with a red button.
2. **Why these features.**
   - `disabled: {}` (10.3) for past, closed and full days and for taken slots: the user sees *why* an
     option is missing instead of a shorter list that looks like a bug **[heuristic]**. The API only
     says a disabled button "does nothing"; the server still re-checks on confirm because stale lists
     and crafted callbacks exist **[API]**.
   - `<tg-time unix="…" format="wDT">` (regular HTML): clients render the visit in the viewer's time
     zone and language **[API]**; keep a readable fallback text inside the tag **[heuristic]**. Slots are *computed* in the business's zone, displayed per reader.
   - `style: "primary"` on `Confirm`, `"danger"` on `Yes, cancel`, `"success"` on `I'll be there`
     (9.4) **[heuristic: danger only on the irreversible step, and on its own confirm screen]**.
   - Version-in-`callback_data` (`bk:<ver>:…`): after a reschedule the old slot list is refused as
     stale, so a tap on yesterday's list can't move the booking again **[heuristic]**.
   - Idempotent booking: key = user + attempt + slot, so a retried confirm returns the same booking
     **[heuristic]**; the slot dict is the race arbiter (the first write wins).
3. **Requirements.** Bot API ≥ 10.3 for disabled buttons (`<tg-time>` needs 9.5+, everything else is older). Production.
   Private chat. A real job queue for reminders (here an in-memory `Scheduler` stands in): it must
   survive restarts and replace jobs by key. Time zone of the business, stored explicitly. `allowed_updates`
   must include `message` and `callback_query`. A deep link `t.me/<bot>?start=svc_cut` (1–64 chars,
   `A-Z a-z 0-9 _ -` **[API]**) opens the date picker for one service.
4. **Payload.** Full request sequence: `examples/payloads/r22-booking.json`. Incoming fixture:
   `examples/fixtures/usecase_booking_deeplink.json` (`/start svc_cut`).

   | Screen | Message | Buttons (row by row) | Leaves to |
   |---|---|---|---|
   | services | “Book a visit — What would you like?” | one row per service with price · `My visit` (if any) | date, done |
   | date | service, “Greyed days have no free time” | 7 days from today, two per row; `Fri 20 · full` disabled · `← Back` | slots |
   | slots | service and day | 3 per row; `11:00 ✕` disabled · `← Back` | confirm |
   | confirm | `Confirm your visit` + `<tg-time>` (or “Move your visit: from … to …”) | `Confirm` primary · `← Back` | done / slots (taken) |
   | done | “You are booked · B-1001” + time | `Reschedule` · `Cancel visit` | date, cancel_ask |
   | cancel_ask | “Cancel this visit?” | `Yes, cancel` danger · `Keep it` primary | cancelled / done |
   | reminder (own message) | “Reminder · 24 h to go” + time | `I'll be there` success · `Reschedule` | edit / date |

   Key parts:
   ```json
   {"method": "editMessageText", "params": {"chat_id": 111111111, "message_id": 1001,
     "text": "<b>Confirm your visit</b>\nHaircut · €35\n<tg-time unix=\"1795082400\" format=\"wDT\">Thu 19.11 11:00</tg-time>",
     "reply_markup": {"inline_keyboard": [[{"text": "Confirm", "callback_data": "bk:3:book", "style": "primary"}],
       [{"text": "← Back", "callback_data": "bk:3:back"}]]}, "parse_mode": "HTML"}}
   {"method": "sendMessage", "params": {"chat_id": 111111111, "parse_mode": "HTML",
     "text": "<b>Reminder</b> · 24 h to go\nHaircut\n<tg-time unix=\"1795093200\" format=\"wDT\">Thu 19.11 14:00</tg-time>",
     "reply_markup": {"inline_keyboard": [[{"text": "I'll be there", "callback_data": "br:2:ok:B-1001", "style": "success"},
       {"text": "Reschedule", "callback_data": "br:2:mv:B-1001"}]]}}}
   ```
5. **Code.** `examples/python/recipes/r22_booking.py` (`Salon.day_state`, `reserve`, `schedule`,
   `fire_reminders`, `on_reminder_tap`) on top of `examples/python/tgkit/flows.py` (`ScreenFlow`,
   `OnceStore`, `Scheduler`, `tg_time`, `btn`, `kb`, `pack`). No TypeScript twin.
6. **Sequence and state.**
   ```mermaid
   stateDiagram-v2
     [*] --> services: /start or deep link
     services --> date: service
     date --> slots: free day
     slots --> confirm: free slot
     confirm --> done: Confirm (once per attempt)
     confirm --> slots: slot just taken (toast + refreshed list)
     done --> date: Reschedule (reminders replaced on confirm)
     done --> cancel_ask: Cancel visit
     cancel_ask --> cancelled: Yes, cancel (reminders removed, slot freed)
     cancel_ask --> done: Keep it
   ```
   Booking record: `{id, user, svc, slot, rev, status: active|cancelled, confirmed}`. Reminder jobs:
   `bk:<id>:r24` and `bk:<id>:r2` at `slot − 24 h / 2 h`, created only when still in the future;
   rescheduling calls `cancel("bk:<id>:")` and re-adds them, bumping `rev`, which also kills the old
   reminder's buttons (`br:<rev>:…`). `day_state` = `closed` (Sunday) / `past` / `full` / `ok`.
7. **Result.** Mock-ups (not client screenshots), English / Russian:
   ```
   Haircut                               Стрижка
   Pick a day. Greyed days have no       Выберите день. Серые дни без
   free time.                            свободного времени.
   [Mon 16 · past] [Tue 17]              [Пн 16 · прошло] [Вт 17]
   [Wed 18 · full] [Thu 19]              [Ср 18 · занято] [Чт 19]
   ...  [Sun 22 · closed]                ...  [Вс 22 · выходной]
   Haircut · Thu 19                      Стрижка · Чт 19
   [10:00] [11:00 ✕] [12:00]             [10:00] [11:00 ✕] [12:00]
   ```
8. **Typical mistake, limits, alternative.** Mistakes: showing only free times (people think the
   bot is broken); letting the disabled button be the only guard; a booking key without the attempt
   (a cancelled-then-rebooked slot returns the old booking); reminders that survive a reschedule or a
   cancel; computing the day in the server's zone; trusting a booking id from `callback_data`
   without checking its owner (the run refuses another user's id). Limits **[API]**: `callback_data`
   ≤ 64 bytes (a slot is a unix timestamp: `bk:<ver>:slot:1795082400`); `answerCallbackQuery` text
   ≤ 200 chars. Failure paths in the run: a crafted tap on a full day → alert; a crafted tap on a taken
   slot is refused by `reserve`; a double confirm → one booking (stale tap, and the same key through
   the API path); a race for one slot → the second user gets “Это время только что заняли” and the
   list without that time; a stale slot list after a reschedule → toast; another user's booking id →
   alert; a reminder button after a reschedule or from another user → refused. Alternative: a Mini
   App calendar for many resources and long ranges (a 7-day list is the sweet spot for buttons).
9. **Run and verify.** `py -3 examples/python/recipes/r22_booking.py` (12 self-checks) ·
   `py -3 -m unittest tests/test_usecases.py` (validators on every markup, 64-byte callbacks, copy
   in en/ru, payload drift). Evidence: offline contract; the real clients' rendering of `<tg-time>`
   was not checked in this run.
10. **Adapt.** Keep: server re-check on confirm, one key per attempt, keyed jobs
    (`cancel(prefix)` then `at`), version in callbacks, owner check on every booking id. Replace:
    `SERVICES`, `HOURS`, the closed-day rule, the in-memory dicts (a unique constraint on
    `(resource, slot)` is the real race arbiter), the clock (`NOW` → real time), `Scheduler` → your
    queue. Add a waitlist button on a full day, or payment through recipe 20. Related:
    `recipes/20-shop.md` (payments), `recipes/03-multi-step-form.md` (multi-step flows),
    `references/buttons-and-styles.md`, `references/localization-and-rtl.md`.
