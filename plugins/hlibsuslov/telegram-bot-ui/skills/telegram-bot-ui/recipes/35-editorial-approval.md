# 35 — Editorial approval before publishing

Registry rows: none (channel publishing combines existing methods; see `references/publishing-pipeline.md`). Verified 2026-11-15, Bot API 10.4 (newest on that date).

1. **Request and visible result.** “The bot drafts posts, but an editor must approve each one, fix the text if needed, or reject it.” — The editor gets the exact post as a preview in a private chat, with [Approve and publish] [Edit text] [Reject]. Edit asks for the corrected text and shows v2. Approve publishes once; the control message turns into a link to the live post.
2. **Why these features.** A preview sent from the same plan is byte-identical to the channel post; `style` (9.4) marks commit (`success`) and destructive (`danger`) actions; `force_reply` collects the new text; the idempotent publisher absorbs double taps.
3. **Requirements.** Production. Editor's private chat with the bot (the editor pressed Start); channel admin rights for the bot. Every callback answered.
4. **Payload.** `examples/payloads/r35-editorial-approval.json`; incoming fixture `examples/fixtures/r35_editor_updates.json`. Key part:
   ```json
   {"text": "Draft d42 · v1 → City News. The preview is above.", "reply_markup": {"inline_keyboard": [
     [{"text": "Approve and publish", "callback_data": "pub:approve:d42:1", "style": "success"}],
     [{"text": "Edit text", "callback_data": "pub:edit:d42:1"}, {"text": "Reject", "callback_data": "pub:reject:d42:1", "style": "danger"}]]}}
   ```
5. **Code.** `examples/python/recipes/r35_editorial_approval.py` (`ApprovalDesk`), `examples/python/tgkit/publish.py` (`plan`, `Publisher.publish`).
6. **Sequence and state.** submit → preview (plan to editor) + control message → callback → editor allow-list → version check (stale → alert) → approve: `publish(key=draft:<id>:v<n>)` → answer → control message edited with the post link; edit: `force_reply` prompt → reply → version+1 → new preview; reject: state `rejected`.
7. **Result.** Mock-up: [post preview] / “Draft d42 · v2 → City News” [Approve and publish] / [Edit text] [Reject] → “Draft d42 · v2 published by Alice. [Open the post]”.
8. **Typical mistake, limits, alternative.** No version in `callback_data` (an old preview publishes old text); checking editors only in the UI; not answering callbacks; publishing on each tap. Alternative: a group of editors with the same desk (callback `from` is still the authority).
9. **Run and verify.** `py -3 examples/python/recipes/r35_editorial_approval.py`. Evidence: offline contract.
10. **Adapt.** Store drafts in your DB; add a scheduled time field and let your scheduler call `publish`; log who approved what. Related: `references/publishing-pipeline.md`, R03.
