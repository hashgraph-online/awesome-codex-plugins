# Twilio Conversations → CometChat feature map

**How to use:** for each feature the ledger shows, find its row; check the CometChat **id** in the TARGET family's `features.json` (match id OR name). Found → migrate via *Via*. Not found → search the docs at BOTH levels (UI Kit `search_cometchat_docs "<feature> <platform> ui kit"` AND SDK `"<feature> <platform> sdk"`). Documented at either → migrate (no UI Kit drop-in ≠ unsupported — build on the SDK). Documented at neither → apply *If absent*. Twilio is headless, so most of these are wired on the **CometChat Chat SDK** in the app's own UI (the *Via* names the closest UI-Kit component for the optional UI-Kit path).

**Actions:** `REMOVE` → UNSUPPORTED, remove fully + list; `CHANGE` → nearest equivalent, list the difference. Never REMOVE without a docs query in both levels; a docs-tool outage is never "unsupported" (`RULES.md`).

| Twilio feature (signals) | CometChat id | Via | If absent |
|---|---|---|---|
| Conversations client + token login (`Client`, access token) | `core-chat-surface` | core / SDK init+login | — |
| Conversation list / subscribed conversations (`getSubscribedConversations`) | `core-chat-surface`, `users-groups` | conversations request builder / `CometChatConversations` | — |
| 1:1 conversation (2 participants) | `text-messaging` (a **user** conversation) | core / SDK | — |
| Group conversation (3+ participants, `friendlyName`) | `users-groups` (a group) | core / components | — |
| Send / get / edit / delete messages (`sendMessage`, `getMessages`, `updateBody`, `remove`) | `text-messaging` | core / SDK | — |
| Media messages (`MessageBuilder.addMedia`, `media`) | `media-file-attachments` | core / features | CHANGE (single file per message) |
| Typing indicators (`typing()`, `typingStarted`) | `typing-indicators` | core / features | CHANGE |
| Read horizon / unread count (`setAllMessagesRead`, `getUnreadMessagesCount`, delivery receipts) | `delivery-read-receipts` | core / features | CHANGE |
| Participants add/remove (`add(identity)`, `removeParticipant`) | group member management | components / SDK | — |
| Non-chat participants (SMS / WhatsApp / MMS via `addNonChatParticipant`) | none | docs | REMOVE (CometChat is in-app chat; SMS/WhatsApp bridging is a Twilio-specific product — list it) |
| Conversation/message/participant `attributes` (JSON) | metadata (user/group/message) | core / SDK | — |
| User profile (`User`, friendlyName, attributes, online/notifiable) | user name / avatar / metadata / presence | core | CHANGE (presence model differs) |
| Push (registration id, FCM/APNs binding) | `push-notifications` | push | action item (credentials in dashboard) |
| Webhooks (`onMessageAdded`, scoped/global) | CometChat webhooks | server | REMOVE + list any event with no equivalent |
| Reactions | native? no — Twilio has no built-in reactions | `reactions` | (if the app hand-built reactions on attributes) migrate to `reactions`; else n/a |
| Threads / replies | Twilio has no native threads | `threaded-replies` | n/a unless the app built them; then migrate |
| Media redaction / message scheduling / delivery to SMS | none | docs | REMOVE + list |

Twilio Conversations is deliberately minimal (messaging + participants + media + attributes), so most migrations are **feature-for-feature clean** with few removals — the big Twilio-only items are the **omnichannel bridges** (SMS/WhatsApp/MMS participants), which have no CometChat equivalent and are removed + listed. A feature not in this table: treat as `none` — check `features.json` + docs (both levels), then REMOVE or CHANGE, and say which.
