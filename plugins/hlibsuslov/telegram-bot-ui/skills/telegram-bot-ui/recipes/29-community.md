# 29 — Community bot: join requests with rules, welcome, roles as visible tags

Product recipe (combines mechanisms; no registry row of its own). Uses `chat_join_request` with
`user_chat_id`, Rich Messages with checklist items, 10.3 `can_send_welcome_messages` and
`community_chat_joined`, 9.5 `setChatMemberTag`, ephemeral welcome messages. Verified 2026-11-15
against Bot API 10.4 (newest release on that date, 2026-11-09). Index of all product recipes:
`references/use-case-playbooks.md`; group-side admin helpers: `references/specialized-updates.md`.
Tags: **[API]** = API requirement, **[official]** = official recommendation, **[heuristic]** =
design heuristic of this skill.

1. **Request and visible result.** “Our food club is a private supergroup. People ask to join through
   a link; I want them to read the rules first, accept or decline, and be let in automatically. New
   members should get a friendly welcome, and admins should be able to give someone a visible role
   like Mentor.” — The applicant gets a DM with the rules as a checklist and two buttons; accepting
   approves the request, declining or ignoring for five minutes declines it. The welcome is sent
   only when the bot is allowed to. Admins pick a role from a picker; the tag shows next to the
   member's name in the group.
2. **Why these features.**
   - `chat_join_request` carries `user_chat_id`: the bot may use it for **5 minutes** to message the
     applicant until the request is processed (assuming no other admin contacted the user)
     **[API]**. So the DM happens at once and the expiry job is scheduled for `date + 300 s`
     **[heuristic for the job; the window is API]**.
   - Rules as a Rich Message `list` whose items have `has_checkbox` (a checklist the user reads
     through), a `heading` and a short note **[API: InputRichBlockListItem]**; *I accept* is `style:
     "success"`, *Decline* is neutral **[heuristic]**. The DM is edited to a disabled state button
     (“✓ Accepted”, “Declined”, “Expired”) so the outcome is visible and the buttons are dead
     **[heuristic; `disabled` is 10.3 API]**.
   - `approveChatJoinRequest` / `declineChatJoinRequest(chat_id, user_id)` need the bot to be an
     administrator with `can_invite_users` **[API]**. Each request settles through a `Machine`
     (`pending → accepted | declined | expired`) and an `OnceStore`, so a second tap, a race between
     Decline and expiry, or a retried update never produces a second Telegram call **[heuristic]**.
   - Welcome gate: `can_send_welcome_messages` in `ChatMemberAdministrator` is “True, if the
     administrator can manage chat welcome messages or directly send them in the case of bots”
     **[API, 10.3]**. The bot reads it from `getChatMember(chat, bot_id)` (or the `my_chat_member`
     update) and **skips and logs** the welcome when the right is missing; approval still works
     **[heuristic]**. The welcome is an *ephemeral* message to the newcomer: an administrator bot
     may send one to any non-bot member at any time, delivery is not guaranteed **[API]**, and the
     group is not spammed **[heuristic]**.
   - `community_chat_joined` (a service message, `community: {id, name}`) lets the welcome name the
     community the member came from **[API, 10.3]**; the community id can exceed 32 bits (store it
     as 64-bit).
   - Roles: `setChatMemberTag(chat_id, user_id, tag)` — the bot must be an administrator with
     `can_manage_tags`; the tag is **0-16 characters and emoji are not allowed**; it works for
     regular members **[API, 9.5]**. The member's messages then show `sender_tag` **[API]**. The
     recipe validates the tag locally before the call, so a bad tag is an explained refusal and not
     an API error **[heuristic]**.
3. **Requirements.** Bot API ≥ 10.3 for the welcome right and `community_chat_joined` (tags: 9.5).
   The bot is an administrator with `can_invite_users` (approve/decline), `can_manage_tags`
   (roles) and, for welcomes, `can_send_welcome_messages`. The invite link must create join
   requests (`createChatInviteLink` with `creates_join_request`) **[API]**. `allowed_updates` must
   include `chat_join_request`, `my_chat_member`, `callback_query` and `message`. A bot that is
   assigned to process join requests receives `query_id` in `ChatJoinRequest` and must answer it
   within 10 seconds **[API]**; this recipe is the plain approve/decline path. Production.
4. **Payload.** Full request sequence: `examples/payloads/r29-community.json`. Incoming fixtures:
   `examples/fixtures/usecase_chat_join_request.json`, `examples/fixtures/usecase_community_bot_rights.json`,
   `examples/fixtures/message_community_chat_joined.json` and
   `examples/fixtures/chat_member_admin_welcome.json` (existing: the bot has the welcome right but
   not `can_manage_tags`).

   | Screen | Message | Buttons (row by row) | Leaves to |
   |---|---|---|---|
   | rules DM | rich: heading, intro, checklist (3 rules), 5-minute note | `I accept` success · `Decline` | accepted / declined |
   | outcome DM | rich: one paragraph (edited) | `✓ Accepted` / `Declined` / `Expired` (disabled) | — |
   | welcome (ephemeral) | “Welcome, name!” or “…from <community>” | — | — |
   | role picker (group) | “Pick a role for name.” | `Mentor` `Guide` `Translator` · `Clear role` | tag set |
   | picker done | “name is now: Ментор.” (edited) | `✓ Ментор` (disabled) | — |

   Key parts:
   ```json
   {"method": "approveChatJoinRequest", "params": {"chat_id": -1001234567890, "user_id": 222222222}}
   {"method": "sendMessage", "params": {"chat_id": -1001234567890, "text": "Вітаємо, Богдан! Правила закріплено. Привітайтесь.", "parse_mode": "HTML", "ephemeral_message_parameters": {"receiver_user_id": 222222222}}}
   {"method": "setChatMemberTag", "params": {"chat_id": -1001234567890, "user_id": 222222222, "tag": "Ментор"}}
   ```
5. **Code.** `examples/python/recipes/r29_community.py` (`Community.on_join_request`, `settle`, `tick`,
   `welcome`, `bot_rights`, `on_role_command`, `on_role_tap`, `set_tag`, `validate_tag`) on top of
   `examples/python/tgkit/flows.py` (`Machine`, `OnceStore`, `Scheduler`, `UpdateDedup`, `pack`,
   `btn`, `kb`). Copy: en, uk (the DM follows the applicant's `language_code`; tags use the chat's
   language because everyone sees them). No TypeScript twin.
6. **Sequence and state.**
   ```mermaid
   stateDiagram-v2
     [*] --> pending: chat_join_request (DM within 5 min, expiry job at date+300)
     pending --> accepted: I accept → approveChatJoinRequest (once) → welcome if allowed
     pending --> declined: Decline → declineChatJoinRequest (once)
     pending --> expired: no answer → Scheduler → declineChatJoinRequest
     accepted --> accepted: second tap → "already accepted", no call
     expired --> expired: late accept → refused politely
   ```
   Roles: an admin replies `/role` to a member's message; the bot checks the sender with
   `getChatMember`, checks its own `can_manage_tags`, and posts the picker (`cm:role:<picker>:<role>`,
   under 64 bytes). A tap re-checks the presser is an administrator, validates the tag, calls
   `setChatMemberTag` once (the picker is marked done) and edits the picker to a disabled “✓ role”.
   A request seen after its 5 minutes is not DMed (the log says `join_request_too_late`) and stays
   pending for the admins. A failed DM send leaves the request pending too (decide per community).
7. **Result.** Mock-ups (not client screenshots), English / Ukrainian:
   ```
   Rules of Kyiv Foodies Club                Правила: Kyiv Foodies Club
   Please read the rules and accept          Прочитайте правила та прийміть їх,
   them to join.                             щоб приєднатися.
   ☐ Be kind and stay on topic.              ☐ Будьте добрими й пишіть по темі.
   ☐ No ads, no spam.                        ☐ Без реклами та спаму.
   ☐ Share only what you may share.          ☐ Діліться лише тим, чим можна ділитися.
   You have 5 minutes to answer.             На відповідь у вас 5 хвилин.
   [ I accept ] [ Decline ]                  [ Приймаю ] [ Відхилити ]
   ```
8. **Typical mistake, limits, alternative.** Mistakes: approving without any rules step; trying to
   DM the applicant after the 5 minutes; approving twice when the button is tapped twice; accepting
   after the request expired; sending the welcome without the right and getting an error on every
   join; welcoming publicly and spamming the chat; letting any member use the role picker (buttons
   in a group are tappable by everyone); sending tags with emoji or longer than 16 characters;
   forgetting that `setChatMemberTag` is for regular members. Limits **[API]**: `user_chat_id` works
   5 minutes; tag 0-16 characters, no emoji (the local emoji check is an approximation, the server
   is the judge); `callback_data` ≤ 64 bytes (the chat id travels in base 36). Failure paths in the
   run: accept twice → `already_accepted`, one approval; no answer → declined by the Scheduler, the
   late accept → “This request is no longer open.”; Decline → one decline; non-admin on the picker →
   “Only administrators can use this.”; second admin tap → “This role is already set.”; emoji tag and
   a 17-character tag → refused locally; welcome right lost → welcome skipped and logged, approval
   unaffected; no `can_manage_tags` → explanation instead of the picker. Alternative: a plain
   `/start` captcha in a public group, or letting admins approve by hand with the join-request
   notification.
9. **Run and verify.** `py -3 examples/python/recipes/r29_community.py` (9 self-checks) ·
   `cd tests && py -3 -m unittest test_usecases` (validators on every markup and rich message,
   copy in en/uk, payload drift) · `py -3 scripts/validate_rich.py` on the DM. Evidence: offline
   contract; `getChatMember` is scripted from the fixtures, real join requests, approvals and tags
   were not executed.
10. **Adapt.** Keep: DM at once with a scheduled expiry, `Machine` + `OnceStore` per request, the
    right check before every welcome or tag, local tag validation, admin check on every picker tap.
    Replace: the rules text and roles with yours, the in-memory request table and `Scheduler` with
    a database and a persistent queue, `GROUP_LANG` with a chat setting. Add: a captcha question
    in the rules DM, a log channel for decisions (`references/channels-and-broadcasting.md`), role
    expiry, a welcome that links the pinned rules. Related: `recipes/04-shared-card-personal-panel.md`
    (ephemeral messages), `recipes/28-group-expense-split.md` (guards in groups),
    `recipes/24-settings.md`, `references/specialized-updates.md`.
