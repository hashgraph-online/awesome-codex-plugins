# Stream → CometChat feature map

**How to use:**
1. For each feature the ledger shows, find its row below.
2. Check the **CometChat id** in the TARGET family's `features.json`. Ids differ slightly per family, so match on the `id` OR the entry's `name`. Common aliases: `threaded-replies`≈`threaded-conversations`, `delivery-read-receipts`≈`read-receipts`, `typing-indicators`≈`typing-indicator`, `quoted-replies`≈`quoted-reply`, `message-search`≈`conversation-advanced-search`, `media-file-attachments`≈`media-sharing`, `users-groups`≈`group-chat`, `text-messaging`≈`instant-messaging`, `smart-reply`≈`ai-smart-replies`.
3. **Found** → migrate, wired by the skill in *Via*.
4. **Not found (or the id column says "none")** → search the docs at BOTH levels: the UI Kit and the Chat SDK / REST API (SKILL step 3). Documented at either → migrate; no UI Kit drop-in means build it on the SDK method in the app's own UI. Documented at neither → apply *If absent*.

**Actions under *If absent*** apply only AFTER both docs searches (UI Kit and SDK) come back empty. The table's REMOVE is never a shortcut past that check, and the report's evidence must quote both queries:
- `REMOVE` → UNSUPPORTED: remove it fully (SKILL step 6) and list it in the report.
- `CHANGE` → keep the capability on the closest CometChat equivalent, and list the difference under "Behavior changes".

**Enablement:** a feature whose `features.json` entry says `needs_dashboard`, or is an extension/AI feature, still migrates in code. Add "enable <feature> in the CometChat dashboard" to the action items. `@cometchat/skills-cli features enable` can do it after `auth login`.

**Rows are grouped by area.** Columns: Stream feature (signals) · CometChat id · Via · If absent.

### Messaging basics

| Stream feature (signals) | CometChat id | Via | If absent |
|---|---|---|---|
| Messaging / team / commerce / gaming channels (`client.channel(type, id)`) | `core-chat-surface`, `users-groups`, `text-messaging` | core | — (always present) |
| Channel list with unread counts, last message (`ChannelList`, `countUnread`) | `core-chat-surface` | core | — |
| Edit / delete messages (`updateMessage`, `deleteMessage`) | `text-messaging` | core | — |
| Typing indicators (`keystroke`, `typing.start`) | `typing-indicators` | core / features | CHANGE (drop the indicator) |
| Read state / receipts (`markRead`, `message.read`, `read` array) | `delivery-read-receipts` | core / features | CHANGE |
| Mark as unread (`markUnread`) | `mark-as-unread`, else the SDK's mark-as-unread call (`/sdk/<platform>/delivery-read-receipts`; needs Enhanced Messaging Status → action item) | features / SDK | REMOVE |
| Image / file / video attachments (`sendImage`, `sendFile`, `attachments`) | `media-file-attachments` | core / features | CHANGE (single file per message) |
| Voice recordings (`voiceRecording` attachment, audio recorder) | `voice-notes` | features | REMOVE the recorder, keep audio-file playback |
| Threads (`parent_id`, `<Thread>`) | `threaded-replies` | features / placement | REMOVE the thread UI |
| "Also send to channel" (`show_in_channel`) | none | docs | CHANGE (the reply stays in the thread) |
| Threads overview list (`ThreadList`, `queryThreads`) | none | docs | REMOVE |
| Quoted replies (`quoted_message_id`) | `quoted-replies` | features | REMOVE |
| Reactions (`sendReaction`) | `reactions` | features | REMOVE |
| Cumulative reaction scores ("claps", `score`), custom reaction types | none | docs | CHANGE (one reaction per emoji per user) |
| Mentions (`mentioned_users`) | `mentions` | features | REMOVE the mention picker, keep plain text |
| Polls (`createPoll`, `castPollVote`, `poll_id`) | `polls` | features | REMOVE |
| Message search (`client.search`, `ChannelSearch`/`SearchBar`) | `message-search` | features / placement | REMOVE |
| Pinned messages (`pinMessage`, `pinned_messages`) | `pin-message` | features | REMOVE |
| Message reminders / save for later (`createReminder`) | `reminders` / `save-message` | features | REMOVE |
| Silent / system messages (`silent: true`, `type: "system"`) | none | docs | CHANGE (sent as normal / action messages) |
| Drafts (`createDraft`, composer drafts) | none | docs | REMOVE the server-side drafts |
| Translation (`translateMessage`, auto-translation) | `message-translation` | features | REMOVE |
| Link previews / URL enrichment (`og_scrape_url`) | `link-preview` | features | CHANGE (plain links) |
| Giphy (`/giphy`, giphy attachments) | `gifs` | features | REMOVE |
| Custom slash commands (`commands`, custom command webhook) | none | docs | REMOVE |
| Location sharing, live location (`SharedLocation`, `startLiveLocationSharing`) | none | docs | REMOVE |
| Custom attachments / `extraData` on messages | `custom-message-types` (Angular also `card-messages`) + message metadata | customization / features | CHANGE (render as text + metadata) |

### Users and presence

| Stream feature (signals) | CometChat id | Via | If absent |
|---|---|---|---|
| Presence, last active (`online`, `last_active`, `user.presence.changed`) | `user-presence` | core | CHANGE |
| User custom fields (`extraData`, `image`, `name`) | user name / avatar / metadata (core SDK) | core | — |
| Block users (`blockUser`) | `block-unblock-user` (iOS), else the core SDK block-users call | core / docs | REMOVE |
| Mute users (`muteUser`) | none (check the notification-preferences docs; muting a 1:1 conversation is covered by mute conversations) | docs | REMOVE |

### Channels and moderation

| Stream feature (signals) | CometChat id | Via | If absent |
|---|---|---|---|
| Livestream channels (`livestream` type, large audiences) | `users-groups` (a **public** group) | core | CHANGE (over 300 members → no receipts/typing) |
| Join a public/preview channel (channel preview + Join button, `addMembers`, `channel.watch`) | join a public group: `CometChatGroups` (joinable list) + the SDK's `CometChat.joinGroup(guid, type)` (`/sdk/<platform>/groups-join-leave`) | components / SDK | REMOVE |
| Member-based 1:1 channels (`!members-…`, 2 members) | a **user** conversation | core | — |
| Channel name, image, custom fields (`channel.data`, `extraData`) — incl. editing them | group name / icon / metadata; editing = the SDK's update-group call (`/sdk/<platform>/update-group`) | core / SDK | — |
| Channel roles, permissions, grants (`channel_role`, custom roles) | group scopes admin / moderator / participant (+ CometChat roles, docs) | components / docs | CHANGE |
| Ban / remove members, banned list + unban (`banUser`, `removeMembers`, `unbanUser`) | group member management: the kit's members list + the SDK's banned-members request + unban (`/sdk/<platform>/group-kick-ban-members`) | components / SDK | REMOVE |
| Shadow ban (`shadowBan`) | none | docs | REMOVE |
| Freeze channel, slow mode (`frozen`, `enableSlowMode`) | none | docs | REMOVE |
| Invites with accept/reject (`inviteMembers`, `acceptInvite`) | none (members are added directly) | docs | CHANGE (invite = add member) + REMOVE the accept/reject UI |
| Mute a channel per user (`channel.mute`) | notification preferences: mute conversations (`/notifications/preferences`) | push / SDK | REMOVE |
| Hide / pin / archive a channel per user (`hide`, `pin`, `archive`) | none | docs | REMOVE |
| Truncate channel (`truncate`) | none (check the delete-conversation docs) | docs | REMOVE |
| Flag / report (`flagMessage`, `flagUser`) | `report-message` / `moderation` | features | REMOVE |
| AutoMod, blocklists, review queue (dashboard) | `moderation` | features + dashboard | action item: recreate the rules |

### Push, calls and other products

| Stream feature (signals) | CometChat id | Via | If absent |
|---|---|---|---|
| Push devices (`addDevice(token, 'firebase' / 'apn')`, push templates) | `push-notifications` | push | action item (credentials in the dashboard) |
| Push preferences (`setPushPreferences`, per-channel) | notification preferences: mute conversations, DND, schedules (`/notifications/preferences`) | push / SDK | REMOVE only what the preferences page lacks |
| Stream Video calls, ringing (`StreamCall`, `call.ring`) | `voice-video-calls` | calls (or the headless calls peer) | REMOVE |
| Video livestream, audio rooms (Stream Video) | `live-streaming` | features / docs | REMOVE |
| **Activity Feeds** (`getstream`, `@stream-io/feeds-*`, `feed(`, `addActivity`, follows) | none | — | **REMOVE** (no CometChat equivalent) |
| AI assistant (`ai_indicator`, Stream AI components) | `ai-assistant`, `ai-agents`, `smart-reply`, `conversation-summary` | features | REMOVE |
| Offline storage (`@op-engineering/op-sqlite`, `stream_chat_persistence`, `StreamOfflinePluginFactory`, the local DB) | none | core | CHANGE (online-first; list the offline gap) |

### Look and feel, server

| Stream feature (signals) | CometChat id | Via | If absent |
|---|---|---|---|
| Theme, CSS variables (`--str-chat__*`), `StreamChatTheme`, `ChatTheme`, `Appearance` | theming | customization | — |
| i18n (`Streami18n`, `StreamI18nService`, `stream_chat_localizations`) | localization (docs) | customization | CHANGE (the kit's defaults) |
| Webhooks (`verifyWebhook`, `x-signature`) | CometChat webhooks | server (SKILL step 7) | REMOVE (and list) each event with no equivalent |
| Before-message-send hook, SQS/SNS delivery | none (check the moderation / webhook docs) | server / docs | REMOVE |

A feature in the ledger that has no row here: treat it like a `none` row. Check `features.json`, then the docs, then REMOVE or CHANGE, and say which in the report.

## Deciding "unsupported" — the verification ladder (read before any REMOVE)

**An MCP search that returns NOTHING is NOT evidence of "unsupported" — nor is the MCP being down.** An empty result (or "no dedicated page") is INCONCLUSIVE: the feature is often documented under CometChat's OWN term (a vendor "voice message recorder" is CometChat's **media recorder** / **voice notes**), folded into a broader page (a composer prop, not its own page), or just ranked out of the top hits. So when the MCP doesn't surface it, walk this ladder BEFORE any verdict:

1. **Re-query with CometChat vocabulary** — component/product names; drop over-qualifiers like the version/platform.
2. **LIVE-FETCH the likely docs page** — `fetch_cometchat_doc_page` (or a plain fetch of the docs URL + `.md`) of the family's composer / features / component page.
3. **Cross-check the family CATALOG** (the installed component/symbol list) — if the component is there, it IS supported, migrate it.

Mark **UNSUPPORTED only** when the CATALOG lacks it AND the live doc fetch (not merely an empty MCP search) also finds nothing. If it genuinely can't be checked (tooling down, network blocked), KEEP it and mark `needs-verification` — never REMOVE a feature you could not verify is absent. **Every UNSUPPORTED row needs evidence** in the report: the `features.json` result plus the exact UI Kit AND SDK docs queries you ran and what each returned. A REMOVE with no docs query is not allowed. Docs MCP not connected? Use a plain fetch (`RULES.md` → Fetch discipline).
