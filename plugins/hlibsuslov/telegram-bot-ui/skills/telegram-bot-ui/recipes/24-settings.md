# 24 — Settings and preferences: toggles, back stack, destructive actions with confirm and undo

Product recipe (no registry row of its own). Uses 10.3 disabled buttons, 9.4 `style`.
Verified 2026-11-15 against Bot API 10.4. Tags: **[API]** · **[official]** · **[heuristic]**.

1. **Request and visible result.** “Our settings are five separate commands. People can't find
   notifications, Back throws them to the start, and someone deleted their account with one
   accidental tap.” — One settings message that changes in place: root → Notifications (✓/✗
   toggles, quiet hours) / Language / Privacy, Back returns to the parent with its state; *Delete
   my data* opens a confirmation with a red button below a safe Cancel, then a 30-second Undo;
   `/settings` in a group answers with a button that opens the private chat.
2. **Why these features.**
   - One message edited per screen + a back stack (`ScreenFlow.go/back`) **[heuristic: the chat
     doesn't fill with menus; Back means “parent”, not “home”]**.
   - Version-in-callback: each render bumps a version carried in `callback_data`, so a double
     tap on a toggle hits a stale render and can't flip the value back **[heuristic; Telegram
     delivers every tap]**.
   - `disabled: {}` (10.3) for the currently selected quiet-hour value — visible, not tappable
     **[API: DisabledButton does nothing]**.
   - `style: "danger"` only on the destructive button, Cancel plain and on top (9.4)
     **[heuristic]**; Undo `primary` during the window.
   - Group entry point: URL button `t.me/<bot>?start=settings` instead of rendering personal
     settings in the group **[heuristic: personal content keeps its audience]**. An ephemeral
     reply (recipe 04) is the alternative when the entry is a button tap.
3. **Requirements.** Bot API ≥ 10.3 for disabled buttons (fallback: a plain label without an
   action is not possible — use a callback that answers “already selected”). Production. Private
   chat for the settings; any chat for the entry command.
4. **Payload.** Full request sequence: `examples/payloads/r24-settings.json`.

   | Screen | Message | Buttons | Leaves to |
   |---|---|---|---|
   | root | “Settings · Language: … · Notifications: 2/3” | `Language: English` · `Notifications` `Privacy` · `Delete my data` danger | lang, notif, privacy, confirm |
   | notif | “Tap to turn on or off.” | `✓ Shipping updates` · `✗ Offers and news` · `✓ Weekly digest` · `Quiet hours: from 22:00` · `← Back` | quiet, back |
   | quiet | “No sound between 22:00 and 08:00…” | `20:00` `21:00` `22:00`(disabled) `23:00` · `← Back` | back to notif |
   | lang | “Language” | `✓ English` · `Русский` · `← Back` | back to root (re-rendered) |
   | privacy | “Show my name on the weekly leaderboard: no” | toggle · `← Back` | back |
   | confirm_delete | “Delete all your data? …” | `Cancel` · `Delete everything` danger | back / deleting |
   | deleting | “Deleting in 30 s” | `Undo` primary | root / deleted |
   | deleted | “Your data was deleted.” | `Start again` (URL `t.me/<bot>?start=new`) | `/start` |

   Key part (confirmation):
   ```json
   {"inline_keyboard": [[{"text": "Cancel", "callback_data": "st:e:back"}],
                        [{"text": "Delete everything", "callback_data": "st:e:delete", "style": "danger"}]]}
   ```
5. **Code.** `examples/python/recipes/r24_settings.py` (`Settings`, `tick`, `on_command`) on
   `examples/python/tgkit/flows.py` (`ScreenFlow`, `Scheduler`, `OnceStore`). TypeScript twin:
   `examples/ts/usecases/settings.ts`.
6. **Sequence and state.**
   ```mermaid
   stateDiagram-v2
     root --> notif
     notif --> quiet
     quiet --> notif: hour picked (back)
     notif --> root: Back
     root --> lang
     lang --> root: language picked (back)
     root --> confirm_delete
     confirm_delete --> root: Cancel
     confirm_delete --> deleting: Delete everything (job del:<user> in 30 s, once)
     deleting --> root: Undo (job cancelled)
     deleting --> deleted: job ran
   ```
   Preferences: `{shipping, promos, digest, quiet, public}`. The deletion job key is per user;
   the idempotency key includes a round number, so Delete → Undo → Delete schedules a fresh
   request while a double Delete in one round schedules one.
7. **Result.** Mock-ups (not client screenshots), Russian / English:
   ```
   Уведомления                               Delete all your data?
   Нажмите, чтобы включить или выключить.     Orders, addresses and settings will be removed.
   [ ✓ Статус доставки ]                      [ Cancel ]
   [ ✓ Акции и новости ]                      [ Delete everything ]  (red)
   [ ✓ Дайджест недели ]
   [ Тихие часы: с 23:00 ]
   [ ← Назад ]
   ```
8. **Typical mistake, limits, alternative.** Mistakes: a new message per toggle; Back to the root
   from every depth; toggles whose label states the action (“Turn off”) instead of the state
   (✓/✗); a one-tap delete; red on every button; pretending Undo worked after the deletion ran;
   rendering personal settings in a group. Limits: `callback_data` ≤ 64 bytes **[API]** — the
   scheme `st:<ver>:tog:<key>` stays short; answer every callback once **[API]**. Failure paths in
   the run: stale double tap, late Undo, another user's crafted tap, group entry. Alternative: a
   Mini App settings page when there are dozens of fields; per-chat (group) settings belong to
   admins and need a separate permission check.
9. **Run and verify.** `py -3 examples/python/recipes/r24_settings.py` (10 self-checks) ·
   `py -3 -m unittest tests/test_usecases.py`. Evidence: offline contract.
10. **Adapt.** Keep: one message + back stack, state-shaped toggle labels, confirm + undo window
    for anything irreversible, the group redirect. Replace: `DEFAULTS`/`TOGGLES` with your
    preferences, the deletion body in `tick()` with your real deletion (and what you must retain
    by law), the undo window length. Related: recipe 23 (language step), recipe 62 (alert mute and
    quiet hours), `references/navigation-and-flows.md`, `references/buttons-and-styles.md#disabled-buttons`.
