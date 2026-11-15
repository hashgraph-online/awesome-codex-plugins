# 03 — Multi-step form: keyboard plus reply field, disabled Submit, Back, no duplicates

Registry rows: `10.3-K01`, `10.3-K02` (`recipes/registry.json`). Verified 2026-11-12, Bot API 10.4.

1. **Request and visible result.** “Our order form: pick a size or type it, then a phone, then a time. People double-tap Submit and we get two orders.” — Each step is one message with option buttons **and** the reply field open; wrong input is explained on the same step; Back keeps answers; Submit is visible but disabled until all answers are valid; old steps show a disabled “Answered”; a second Submit says “Already sent.”
2. **Why the new feature.** 10.3 `InlineKeyboardMarkup.force_reply` combines buttons with the reply UI (before: either a `ForceReply` without buttons or buttons without the reply field). `DisabledButton` shows an unavailable action without removing it.
3. **Requirements.** Bot API ≥ 10.3. Production. Private chats and groups (in groups privacy mode still delivers replies to the bot's messages). Not in channels.
4. **Payload.** Full request sequence: `examples/payloads/r03-multi-step-form.json` (generated from the code); incoming fixture: `tests/fixtures/keyboards/edit_changes_force_reply.json`. Key part:
   ```json
   {"inline_keyboard": [[{"text": "L", "callback_data": "f:F7:0:o:2"}],
                        [{"text": "Submit", "disabled": {}}]],
    "force_reply": true}
   ```
5. **Code.** `examples/python/tgkit/forms.py` (`FormRunner`, `retired()`), `examples/python/recipes/r03_multi_step_form.py`, TS `examples/ts/recipes.ts::multiStepForm`. Validate markup with `scripts/validate_keyboard.py --previous old.json new.json`.
6. **Sequence and state.** start → sendMessage(step, force_reply kb) → text reply / option tap → validate → next step = new message; previous step edited to disabled “Answered” (force_reply repeated) → Submit (disabled → enabled) → idempotent submit by form_id → edit “Sent”.
7. **Result.** Mock-up: `Step 3 of 3 · When should we deliver? [ASAP] [In 1 hour] [← Back] [Cancel] [Submit]` with the reply field open.
8. **Typical mistake, limits, alternative.** `disabled` together with `callback_data`; toggling `force_reply` in an edit; trusting a disabled button instead of re-checking state; accepting a reply to an old step. Alternative: plain `ForceReply` per step + a separate keyboard message, or a Mini App form for long input.
9. **Run and verify.** py -3 examples/python/recipes/r03_multi_step_form.py · tests/test_keyboard_validator.py (38 regression fixtures). Evidence: offline contract.
10. **Adapt.** Copy `FormRunner`; adapt `Step` validators and texts (i18n); keep `callback_data` scheme `f:<form>:<step>:…` ≤ 64 bytes; make your submit backend idempotent by form id. Related: `buttons-and-styles.md#disabled-buttons`, `reply-keyboards.md`.
