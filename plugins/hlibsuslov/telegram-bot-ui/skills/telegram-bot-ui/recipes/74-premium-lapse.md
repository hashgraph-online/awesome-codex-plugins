# 74 — Recover after the owner's Premium lapses

Registry rows: none of its own. Verified 2026-11-15, Bot API 10.4. Background:
`references/custom-emoji.md#runtime-errors-and-the-kill-switch`, `references/errors-and-fallbacks.md`.

1. **Request and visible result.** “Messages started failing after the owner's Premium
   expired.” — The refused message is delivered with Unicode fallbacks, the bot stops
   sending custom emoji until an operator re-enables them, and nothing loops.
2. **Why the new features.** The owner-Premium route depends on the owner's subscription;
   when it ends, requests with custom emoji can be refused.
3. **Requirements.** Telegram does not document the exact error text; detection is a 400 on
   a request that carried custom emoji whose description matches `CUSTOM_EMOJI_ERROR_HINTS`.
4. **Payload.** `examples/payloads/r74-premium-lapse.json` (the error text is illustrative).
5. **Code.** `examples/python/recipes/r74_premium_lapse.py`, `tgkit/icons.py`
   (`IconSystem.send`, `kill`, `reset_kill_switch`, `is_custom_emoji_rejection`).
6. **Sequence and state.** send with icons → refused → `kill(reason)` (shared, logged once) →
   one retry via `strip_request` → later sends plain at the first attempt → owner renews →
   `reset_kill_switch()` → icons return.
7. **Result.** Mock-up: `🔔 Alert 2` delivered once, no duplicate.
8. **Typical mistake, limits, alternative.** Retrying in a loop; retrying an unrelated 400;
   flipping only one view's flag so other handlers keep failing. Alternative: Fragment
   usernames do not depend on a subscription.
9. **Run and verify.** `py -3 examples/python/recipes/r74_premium_lapse.py` · tests in
   `tests/test_emoji_icons.py`. Evidence: offline contract with a scripted error.
10. **Adapt.** Persist the kill-switch state (env or DB) so restarts keep it; alert the
    operator from the `log` callback; add the observed description to the hints. Related: 71, 73.
