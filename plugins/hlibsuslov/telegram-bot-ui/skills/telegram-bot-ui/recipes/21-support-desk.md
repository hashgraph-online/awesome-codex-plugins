# 21 — Support desk: a private chat for the customer, one forum topic per ticket for the team

Product recipe (combines mechanisms; no registry row of its own). Uses `10.3` inline `force_reply`,
`10.3` disabled buttons, 9.4 button `style`, forum topics (`createForumTopic`, `editForumTopic`,
`closeForumTopic`, `reopenForumTopic`). Verified 2026-11-15 against Bot API 10.4 (newest release on
that date, 2026-11-09). Topic addressing in general: `references/topics-and-contexts.md`;
index of all product recipes: `references/use-case-playbooks.md`. Tags: **[API]** = API requirement,
**[official]** = official recommendation, **[heuristic]** = design heuristic of this skill.

1. **Request and visible result.** “Customers write to our bot. I want every problem in its own
   thread for the team, with a status I can see in the list, replies that reach the customer, notes
   the customer never sees, and a 1–5 rating when we close it.” — The customer taps a category,
   types the problem in the reply field that opens with the buttons, and gets a ticket id. In the
   operator supergroup a topic `🆕 T-1001 · Billing` appears with a card (`Take` / `Wait for user` /
   `Resolve`). Operator messages in that topic reach the customer, customer messages reach the
   topic, `// …` stays inside. The topic name follows the status (`🆕` new, `🟢` open, `⏳` waiting
   for the user, `✅` resolved). Resolve closes the topic and asks the customer for a rating.
2. **Why these features.**
   - Forum topic per ticket: the team reads one conversation per thread instead of an interleaved
     group, and the status lives in the topic list where people already look. Bot needs
     `can_manage_topics` **[API]**; topic `name` is 1–128 characters **[API]**; the status in the name
     is a **[heuristic]** (`editForumTopic` renames it).
   - Inline `force_reply` (10.3): the category buttons are inline, but the next screen shows its own
     buttons **and** opens the reply field, so the customer types instead of hunting for the input
     **[API: fixed for the message's lifetime, it can't be changed by an edit]**, hence that screen is
     always a new message.
   - `disabled: {}` on the operator card (10.3): `Take` greys out once taken, `Wait for user` once
     waiting; a disabled button does not stop a crafted callback, so the `Machine` re-checks
     **[API: "does nothing"; the check is yours]**.
   - `style`: `primary` on `Take`, `success` on `Resolve` (9.4) **[heuristic: one accent per card]**.
   - `Machine` for statuses: an illegal move (reply to a resolved ticket, `take` in `open`) raises and
     is refused with a toast instead of corrupting the record **[heuristic]**.
   - Rating buttons carry the **resolution cycle**: a reopened ticket makes the old buttons stale
     **[heuristic]**.
3. **Requirements.** Bot API ≥ 10.3 for inline `force_reply` and disabled buttons (topics and styles
   are older). Production. A **forum** supergroup for operators with the bot as administrator holding
   `can_manage_topics` **[API]**; the customer side is a private chat. `allowed_updates` must include
   `message` and `callback_query`. Keep a **fallback admin chat**: topic creation can fail (403 or a
   missing right) and that must not lose the customer. Bots run in privacy mode by default, but bot admins always receive all group messages, so the
   administrator role the bot needs for topics also lets it read operator replies **[official,
   https://core.telegram.org/bots/features#privacy-mode]**.
4. **Payload.** Full request sequence: `examples/payloads/r21-support-desk.json`. Incoming fixtures:
   `examples/fixtures/usecase_support_operator_reply.json` (operator message in topic 5001),
   `examples/fixtures/usecase_support_other_topic.json` (operator message in an unrelated topic).

   | Screen | Message | Buttons (row by row) | Leaves to |
   |---|---|---|---|
   | menu | “Support — What is this about?” | `Billing` · `Bug` · `Other` | ask |
   | ask | “Billing — Describe the problem in one message” (**force_reply**) | `Cancel` | ticket created / menu |
   | topic card | ticket, category, user, status, first message | `Take` primary · `Wait for user` / `Resolve` success or `Reopen` (disabled when the Machine refuses) | card edits |
   | resolved (user) | “T-1001 is resolved. How did we do?” | `1` `2` `3` `4` `5` | thanks (keyboard removed) |

   Key parts:
   ```json
   {"method": "createForumTopic", "params": {"chat_id": -1001234567890, "name": "🆕 T-1001 · Billing"}}
   {"method": "sendMessage", "params": {"chat_id": 111111111, "text": "<b>Billing</b>\nDescribe the problem in one message. Screenshots are fine.",
     "reply_markup": {"inline_keyboard": [[{"text": "Cancel", "callback_data": "sf:2:cancel"}]], "force_reply": true}, "parse_mode": "HTML"}}
   {"method": "editForumTopic", "params": {"chat_id": -1001234567890, "message_thread_id": 5001, "name": "⏳ T-1001 · Billing"}}
   ```
5. **Code.** `examples/python/recipes/r21_support_desk.py` (`Desk.open_ticket`, `move`, `on_private`,
   `on_ops_message`, `on_callback`) on top of `examples/python/tgkit/flows.py` (`ScreenFlow`,
   `Machine`, `OnceStore`, `UpdateDedup`, `btn`, `kb(force_reply=True)`, `pack`). No TypeScript twin.
6. **Sequence and state.**
   ```mermaid
   stateDiagram-v2
     [*] --> new: customer submits (topic created)
     new --> open: Take
     new --> waiting: operator reply
     open --> waiting: operator reply / Wait for user
     waiting --> open: customer message / Take
     new --> resolved: Resolve
     open --> resolved: Resolve
     waiting --> resolved: Resolve
     resolved --> open: customer message / Reopen
   ```
   Ticket record: `{id, user, lang, category, status, thread, card, rev, cycle}`; `rev` is in the
   operator buttons (`sd:<rev>:op:<id>:<event>`), `cycle` in the rating buttons
   (`sd:<cycle>:rate:<id>:<n>`). Routing: `(chat, message_thread_id) → ticket`; a message in the
   operator group with no mapped thread (General, another topic) is ignored; a text starting with
   `//` is an internal note and is never relayed; a reply on a resolved ticket is refused (the topic
   is closed anyway). Resolve → `editForumTopic` + `editMessageText` (card) + `closeForumTopic` +
   rating message; reopen → `reopenForumTopic`, cycle + 1.
7. **Result.** Mock-ups (not client screenshots), English / Russian:
   ```
   Topic list                         Customer chat (ru)
   🆕 T-1001 · Billing                Обращение T-1002 открыто. Сегодня ответ может
   ⏳ T-1003 · Bug                    прийти чуть позже.
   ✅ T-0998 · Other
   Card in the topic                  Rating
   T-1001 · Billing                   T-1001 is resolved. How did we do?
   From: Alice · status: open         [ 1 ] [ 2 ] [ 3 ] [ 4 ] [ 5 ]
   [ Take (greyed) ] [ Wait for user ]
   [ Resolve ]
   ```
8. **Typical mistake, limits, alternative.** Mistakes: relaying every message in the operator group
   (other topics, `//` notes, the bot's own messages); keying tickets by user instead of thread, so
   two tickets of one customer mix; resolving without closing the topic or without invalidating the
   old rating buttons; letting a failing `createForumTopic` swallow the ticket. Limits **[API]**:
   topic name 1–128; `callback_data` ≤ 64 bytes (`sd:<ver>:op:T-1001:resolve` stays under 30);
   `force_reply` can't be changed by an edit. Failure paths in the run: topic creation 403 → the
   customer still gets `T-1002`, the fallback admin chat gets the reason, customer messages go to
   the admin chat; a redelivered customer message → one ticket; illegal move → toast; stale operator
   button → toast; another user's rating tap → alert; second rating → toast; rating after a reopen →
   stale. Alternative: forward customer messages with `copyMessage` when attachments matter (this
   recipe relays text only); a business-account inbox for support from a personal account
   (`recipes/61-business-account.md`, another stream).
9. **Run and verify.** `py -3 examples/python/recipes/r21_support_desk.py` (12 self-checks) ·
   `py -3 -m unittest tests/test_usecases.py` (validators on every markup, 64-byte callbacks, copy in
   en/ru, payload drift). Evidence: offline contract against fixtures; a real forum group and the
   403 case were not exercised live.
10. **Adapt.** Keep: thread↔ticket map, `Machine`, status in the topic name, cycle-guarded rating,
    the fallback admin report. Replace: `CATEGORIES`, copy, `NOTE_MARK`, the in-memory dicts (a
    database row per ticket, with the thread id unique), operator authorization (here: anyone in the
    operator chat; add an allow-list or `getChatMember` check for sensitive actions), relay of
    attachments, an SLA timer with the `Scheduler` (flag `new` tickets older than N minutes).
    Related: `recipes/08-multi-topic-bot.md` (addressing in topics),
    `recipes/03-multi-step-form.md` (force_reply forms), `references/buttons-and-styles.md`,
    `references/errors-and-fallbacks.md`, `references/security-and-escaping.md`.
