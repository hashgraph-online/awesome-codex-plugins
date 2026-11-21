# 38 — Comment threads and channel direct messages

Registry rows: none (channel publishing combines existing methods; see `references/publishing-pipeline.md`). Verified 2026-11-15, Bot API 10.4 (newest on that date).

1. **Request and visible result.** “Open every post's comments with a short rules note, remove spam, acknowledge questions; answer messages to the channel and handle suggested posts.” — Each post's thread starts with a silent note; a spam comment disappears; a question gets a reply; a DM to the channel gets an answer in the user's topic; a good suggested post is approved, an ad is declined with a polite comment.
2. **Why these features.** Discussion groups receive `is_automatic_forward` copies with `forward_origin` (channel + message id); channel DMs (9.2) are a supergroup with `is_direct_messages`, `direct_messages_topic_id`, `suggested_post_info`, `approveSuggestedPost` / `declineSuggestedPost`.
3. **Requirements.** Production. Bot admin in the discussion group (`can_delete_messages` to moderate) and in the channel (`can_post_messages` to approve, `can_manage_direct_messages` to decline/manage DMs). In DM chats: no polls, no ephemeral callback replies (10.4), no inline-query switch buttons.
4. **Payload.** `examples/payloads/r38-comments-and-direct-messages.json`; fixture `examples/fixtures/r38_channel_audience_updates.json`. Key part:
   ```json
   {"method": "sendMessage", "chat_id": -1001500000101, "reply_parameters": {"message_id": 9001}, "text": "Comments are open…", "disable_notification": true}
   {"method": "sendMessage", "chat_id": -1001500000201, "direct_messages_topic_id": 77, "text": "Thanks! …"}
   {"method": "declineSuggestedPost", "chat_id": -1001500000201, "message_id": 3003, "comment": "Sorry, we don't publish ads for this kind of service."}
   ```
5. **Code.** `examples/python/recipes/r38_comments_and_direct_messages.py` (`ChannelAudience`).
6. **Sequence and state.** `getChat(channel).linked_chat_id` → group message: auto-forward → map group id → channel post id, note → reply in thread: spam → `deleteMessage`, question → reply; DM message: suggested & pending → approve (keep the author's `send_date`) / decline (≤ 128 chars) → plain DM → reply with `direct_messages_topic_id`.
7. **Result.** Mock-up: comments under the post: “Comments are open. Be kind…”, the question with a reply; DM topic: the user's question and the bot's answer.
8. **Typical mistake, limits, alternative.** Replying to the channel post id inside the group (use the auto-forward's id); `message_thread_id` in DM chats; approving without `can_post_messages`; deleting a paid post within 24 h; editing an approved suggested post. Whether the bot sees all comments depends on admin status / privacy mode (Bots FAQ).
9. **Run and verify.** `py -3 examples/python/recipes/r38_comments_and_direct_messages.py`. Evidence: offline contract.
10. **Adapt.** Replace the regex with your moderation service; route DMs to a support queue (`references/topics-and-contexts.md`); approval of suggested posts can reuse R35's desk. Related: `references/channel-post-design.md`.
