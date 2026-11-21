# 62 — Monitoring and alerts bot: uptime and price watches, mute, quiet hours, daily digest

Product recipe (combines mechanisms; no registry row of its own). Uses `InlineKeyboardMarkup.force_reply`
(10.3), disabled buttons and compact tables (10.3), 9.4 button `style`, `disable_notification`,
`<tg-time>`. Verified 2026-11-15 against Bot API 10.4 (newest release on that date,
2026-11-09). Index of all product recipes: `references/use-case-playbooks.md`.
Tags: **[API]** = API requirement, **[official]** = official recommendation, **[heuristic]** =
design heuristic of this skill.

1. **Request and visible result.** “Tell me when my API gets slow or down, and when BTC drops
   under my level. Don't wake me at night for small things, and don't send me the same alert
   ten times.” — A list of watches (3 per page); *Add a watch* → pick a target → the bot asks for a
   threshold (reply field already open); a wrong number is explained on the same step. Each
   watch has its own screen: threshold, instant or daily digest, mute 1 h / 8 h / until
   tomorrow, quiet hours, delete (with confirmation). Alerts arrive as **new messages** with
   *Acknowledge* and *Mute 1 h*; repeats of the same problem inside 10 minutes are folded
   into “+2 similar alerts” on the next one; the digest is one message with a compact table at
   09:00, and on a quiet day nothing is sent.
2. **Why these features.**
   - `force_reply` on the inline keyboard (10.3): the threshold prompt shows the reply field
     and keeps a *Back* button. The flag cannot be changed by an edit, so the prompt is
     always a **new** message **[API]**.
   - Alerts as **new messages**, not edits of the list: an edit does not push a notification
     **[heuristic]**. `disable_notification: true` for info alerts and for non-critical alerts
     in quiet hours; critical ones always sound **[API parameter; the policy is a
     heuristic]**.
   - One primary action: **Acknowledge** is `style: "primary"` on critical alerts and plain
     on the rest. `danger` is kept for the destructive *Delete watch* / *Delete* (9.4)
     **[heuristic]**: acknowledging does not destroy anything, so a red button would shout
     at someone who is already being paged.
   - The digest is a **Rich Message** with an `is_compact` table (10.3): a comparison people
     scan, not prose **[heuristic]**. Four columns on a phone: the longest column holds a
     short severity word.
   - The pager keeps its shape: `←` / `→` disabled at the ends, the page counter a disabled
     button (10.3) **[heuristic]**. Targets already watched are disabled `✓ name` buttons.
   - Deadlines (mute until …) are `<tg-time>` entities: shown in the reader's time zone
     **[API]**.
3. **Requirements.** Bot API ≥ 10.3 for force_reply keyboards, disabled buttons and compact
   tables. Production. Private chat with the bot. The events come from your monitor (webhook,
   queue); the recipe reads them from `examples/fixtures/usecase_monitor_events.json`. A real
   deployment needs a persistent job queue for mutes and digests and a bounded window of seen
   event ids.
4. **Payload.** Full request sequence: `examples/payloads/r62-monitoring-alerts.json`.
   Incoming fixture (not a Telegram update, the monitor's feed):
   `examples/fixtures/usecase_monitor_events.json`.

   | Screen | Message | Buttons (row by row) | Leaves to |
   |---|---|---|---|
   | list / empty | “Your watches · n” / “No watches yet” | one row per watch (🔕 when muted) · `← 1/2 →` · `Add a watch` primary | watch, add |
   | add | “What should I watch?” | one row per target (`✓ name` disabled if watched) · `← Back` | threshold |
   | threshold | “Alert when … Reply with N” | `← Back` + force_reply | watch (new message) |
   | watch | target, limit, mode, mute, quiet hours | `Threshold: …` · `Instant` / `Digest` (current disabled) · `Mute 1 h` `Mute 8 h` `Until tomorrow` (or `Unmute`) · `Quiet hours: on/off` · `← Back` `Delete watch` danger | list, confirm |
   | confirm | “Delete the watch for …?” | `Delete` danger · `Cancel` | list |
   | alert | severity, detail, “+n similar” | `Acknowledge` primary (critical) · `Mute 1 h` | acked, muted |
   | alert, acknowledged | same + “✓ Acknowledged by …” | `✓ Acknowledged` (disabled) | — |
   | digest | heading + compact table | — | — |

   Key parts:
   ```json
   {"method": "sendMessage", "params": {"chat_id": 111111111,
     "text": "Alert when <b>api.example.com</b> answers slower than N ms. Reply with N (100-60000).",
     "reply_markup": {"inline_keyboard": [[{"text": "← Back", "callback_data": "mo:3:back_from_ask"}]], "force_reply": true}}}
   {"method": "sendMessage", "params": {"chat_id": 111111111,
     "text": "<b>🔵 Info · shop.example.com</b>\nAnswering in 900 ms (limit 500 ms)", "parse_mode": "HTML",
     "reply_markup": {"inline_keyboard": [[{"text": "Acknowledge", "callback_data": "al:ack:a8"},
       {"text": "Mute 1 h", "callback_data": "al:m1:a8"}]]}, "disable_notification": true}}
   {"method": "sendRichMessage", "params": {"chat_id": 111111111, "rich_message": {"blocks": [
     {"type": "heading", "size": 2, "text": "Daily digest · 1 event(s)"},
     {"type": "table", "is_compact": true, "is_bordered": true, "cells": [[{"text": "Watch", "is_header": true, …}, …],
       [{"text": "BTC/USD", …}, {"text": "1", "align": "right", …}, {"text": "🟠 Warning", …}, {"text": "61000", …}]]}]}}}
   ```
5. **Code.** `examples/python/recipes/r62_monitoring_alerts.py` (`Monitor.on_text`, `on_event`,
   `deliver`, `send_alert`, `on_alert_tap`, `tick`, `send_digest`) on top of
   `examples/python/tgkit/flows.py` (`ScreenFlow`, `paginate`, `pager_row`, `Scheduler`,
   `UpdateDedup`, `tg_time`, `I18n`) and `examples/python/tgkit/rich.py::table`. No TypeScript twin.
6. **Sequence and state.**
   ```mermaid
   stateDiagram-v2
     [*] --> event: monitor event (id, target, severity, value, at)
     event --> dropped: id seen / no watch (deleted) / below limit
     event --> held: watch muted -> held list
     held --> unmuted: Scheduler job -> "n alerts held back"
     event --> suppressed: same watch alerted < 10 min ago (counter)
     event --> digested: digest mode and not critical
     event --> alert: instant (silent if info, or quiet hours and not critical)
     alert --> acked: Acknowledge (once, owner only)
     digested --> digest: Scheduler 09:00 -> one Rich Message, or nothing
   ```
   Business keys **[heuristic]**: a watch is unique per `(user, target)` (typing the threshold
   again edits it, never duplicates); an event is processed once per event `id`; an
   alert belongs to its user (`al:ack:<alert id>`, the alert id is server-side), and its
   buttons are refused when the watch is gone (“This watch was deleted.”). Flapping:
   `last_alert_at` per watch, `FLAP = 600` s; suppressed events are counted and shown on the
   next alert. Mute is a `Scheduler` job keyed `unmute:<watch id>`: re-muting replaces it,
   deleting the watch cancels it. The digest job (`digest:<user>`) reschedules itself +24 h
   and sends nothing when the buffer is empty. Time in the recipe is UTC; use the user's time
   zone for quiet hours and the digest hour in production.
7. **Result.** Mock-ups (not client screenshots), English / Russian:
   ```
   🔴 Critical · api.example.com             🔴 Критично · api.example.com
   No answer (limit 800 ms)                  Нет ответа (порог 800 мс)
   +2 similar alerts in the last 10 minutes  +2 похожих сигналов за последние 10 минут
   [ Acknowledge ] [ Mute 1 h ]              [ Принять ] [ Тишина 1 ч ]

   Daily digest · 1 event(s)                 Сводка за день · событий: 1
   Watch    Events  Worst       Last value   Наблюдение  События  Худшее      Последнее
   BTC/USD       1  🟠 Warning       61000   BTC/USD           1  🟠 Внимание     61000
   ```
8. **Typical mistake, limits, alternative.** Mistakes: editing one status message instead of
   sending alerts (no push); an alert on every poll of a flapping service; a digest sent “empty”
   every morning; `danger` on *Acknowledge*; two primaries on one screen; a threshold typed
   as text with no validation (“abc”, “-5”, “1e9”); losing the “muted” state on restart;
   acknowledging twice; keeping a watch's alerts after the watch was deleted; callback data that
   carries the target name instead of a server-side id. Limits **[API]**:
   `callback_data` ≤ 64 bytes (`al:ack:a8`, `mo:3:mute:1h` stay under 20), Rich Message ≤ 32768
   chars / 20 table columns; **[official]** avoid more than about one message per second in one
   chat (bursts of alerts need a queue and grouping; see `references/limits-and-splitting.md`). Failure paths in
   the run: duplicate event id → dropped; suppressed repeat; event for a deleted watch →
   dropped and logged; muted watch → held and reported on unmute; stranger taps someone's
   alert → alert-style toast; deleted watch → “was deleted”; invalid threshold → error on the
   same step with the prompt still open. Alternative: a channel for team-wide alerts
   (`references/channels-and-broadcasting.md`) when nobody needs individual mute settings.
9. **Run and verify.** `py -3 examples/python/recipes/r62_monitoring_alerts.py` (10 self-checks)
   · `py -3 -m unittest tests/test_usecases.py` (validators on every keyboard and the digest,
   64-byte callbacks, copy in en/ru, payload drift). Evidence: offline contract; no
   real monitor was connected and no real notification sounds were heard.
10. **Adapt.** Keep: event-id dedup, per-watch flapping window, alert-as-new-message,
    severity → sound policy, one primary per message, digest only when non-empty,
    server-side alert ids, `Scheduler` jobs keyed by watch. Replace: `TARGETS` and the breach
    rule (`value >= limit` for latency, `<=` for price), the thresholds' validation, the
    in-memory stores with a database and a persistent queue, UTC with each user's time zone.
    Group chat variant: an alert in a group needs an owner guard on *Acknowledge* (anyone can
    tap) and an ephemeral reply (`references/ephemeral-and-personal.md`). Related:
    `recipes/09-tracker-bot.md` (live tracker card), `recipes/24-settings.md` (settings
    screens), `references/tables.md#compact-tables`, `references/buttons-and-styles.md`.
