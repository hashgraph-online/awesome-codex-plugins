# Sendbird → CometChat feature map

**How to use:**
1. For each feature the ledger shows, find its row below.
2. Check the **CometChat id** in the TARGET family's `features.json`. Ids differ slightly per family, so match on the `id` OR the entry's `name`. Common aliases: `threaded-replies`≈`threaded-conversations`, `delivery-read-receipts`≈`read-receipts`, `typing-indicators`≈`typing-indicator`, `quoted-replies`≈`quoted-reply`, `message-search`≈`conversation-advanced-search`, `media-file-attachments`≈`media-sharing`, `users-groups`≈`group-chat`, `text-messaging`≈`instant-messaging`, `smart-reply`≈`ai-smart-replies`.
3. **Found** → migrate, wired by the skill in *Via*.
4. **Not found (or the id column says "none")** → search the docs at BOTH levels: the UI Kit and the Chat SDK / REST API (SKILL step 3). Documented at either → migrate; no UI Kit drop-in means build it on the SDK method in the app's own UI. Documented at neither → apply *If absent*.

**Actions under *If absent*** apply only AFTER both docs searches (UI Kit and SDK) come back empty. The table's REMOVE is never a shortcut past that check, and the report's evidence must quote both queries:
- `REMOVE` → UNSUPPORTED: remove it fully (SKILL step 6) and list it in the report.
- `CHANGE` → keep the capability on the closest CometChat equivalent, and list the difference under "Behavior changes".

**Enablement:** a feature whose `features.json` entry says `needs_dashboard`, or is an extension/AI feature, still migrates in code. Add "enable <feature> in the CometChat dashboard" to the action items. `@cometchat/skills-cli features enable` can do it after `auth login`.

**Rows are grouped by area.** Columns: Sendbird feature (signals) · CometChat id · Via · If absent.

### Messaging basics

| Sendbird feature (signals) | CometChat id | Via | If absent |
|---|---|---|---|
| 1:1 + group chat (`GroupChannel`, `isDistinct`) | `core-chat-surface`, `users-groups`, `text-messaging` | core | — (always present) |
| Channel list with unread badges, last message (`GroupChannelList`, `unreadMessageCount`) | `core-chat-surface` | core | — |
| Edit / delete messages (`updateUserMessage`, `deleteMessage`) | `text-messaging` | core | — |
| Typing indicators (`startTyping`, `onTypingStatusUpdated`) | `typing-indicators` | core / features | CHANGE (drop the indicator) |
| Read + delivery receipts (`markAsRead`, `getReadMembers`, `onDeliveryReceiptUpdated`) | `delivery-read-receipts` | core / features | CHANGE |
| Mark as unread (`markAsUnread`) | `mark-as-unread`, else the SDK's mark-as-unread call (`/sdk/<platform>/delivery-read-receipts`; needs Enhanced Messaging Status → action item) | features / SDK | REMOVE |
| Files, images, video, multi-file (`sendFileMessage(s)`) | `media-file-attachments` | core / features | CHANGE (single file per message) |
| Voice messages (voice recorder, `VoiceMessage`) | `voice-notes` | features | REMOVE the recorder, keep audio-file playback |
| Threads (`parentMessageId`, `Thread`, `ThreadInfo`) | `threaded-replies` | features / placement | REMOVE the thread UI |
| Quote reply (`ReplyType.QUOTE_REPLY`) | `quoted-replies` | features | REMOVE |
| Reactions (`addReaction`, `onReactionUpdated`) | `reactions` | features | REMOVE |
| Custom emoji sets for reactions (`getAllEmoji`, emoji categories) | none | docs | CHANGE (the kit's default emoji) |
| Mentions (`mentionedUsers`, `MentionType`) | `mentions` | features | REMOVE the mention picker, keep plain text |
| Polls (`sb.poll`, `PollCreateParams`) | `polls` | features | REMOVE |
| Message search (`MessageSearchQuery`) | `message-search` | features / placement | REMOVE |
| Pinned messages (`pinMessage`, `pinnedMessageIds`) | `pin-message` | features | REMOVE |
| Scheduled messages (`createScheduledUserMessage`) | none | docs | REMOVE |
| Forward / copy message to another channel (`copyUserMessage`) | none | docs | REMOVE |
| Translation (`translateUserMessage`, `translationTargetLanguages`) | `message-translation` | features | REMOVE |
| Link previews (`ogMetaData`) | `link-preview` | features | CHANGE (plain links) |
| Disappearing messages / retention (`messageSurvivalSeconds`) | `disappearing-messages` | features | REMOVE |
| Custom message types, `customType`, `data`, message templates | `custom-message-types` (Angular also `card-messages`) | customization / features | CHANGE (render as text + metadata) |
| Message `metaArrays` / `data` payloads | message metadata (core SDK) | core | — |

### Users and presence

| Sendbird feature (signals) | CometChat id | Via | If absent |
|---|---|---|---|
| Presence, last seen (`connectionStatus`, `lastSeenAt`) | `user-presence` | core | CHANGE |
| User profile: nickname, profile image, metadata (`updateCurrentUserInfo`) | user name / avatar / metadata (core SDK) | core | — |
| Block / unblock users (`blockUser`) | `block-unblock-user` (iOS), else the core SDK block-users call | core / docs | REMOVE |

### Channels and moderation

| Sendbird feature (signals) | CometChat id | Via | If absent |
|---|---|---|---|
| Open channels (`OpenChannel`, `enter`, `OpenChannelHandler`) | `users-groups` (a **public** group) | core / components | CHANGE (members join; history persists) |
| Join a public channel / group (`OpenChannel.enter`, join button, `addMembers`) | join a public group: `CometChatGroups` (joinable list) + the SDK's `CometChat.joinGroup(guid, type)` (`/sdk/<platform>/groups-join-leave`) | components / SDK | REMOVE |
| Supergroups, broadcast channels (`isSuper`, `isBroadcast`) | `users-groups` | core | CHANGE (over 300 members → no receipts/typing; broadcast → admins-only posting only if the docs document a send restriction) |
| Ephemeral channels (`isEphemeral`) | none | docs | CHANGE (messages are now stored) |
| Channel name, cover, custom type, `data` — incl. an owner's rename / re-cover screen | group name / icon / tags / metadata; editing = the SDK's update-group call (`/sdk/<platform>/update-group`) | core / SDK | — |
| Channel metadata (`createMetaData`) | group metadata (docs) | core / docs | CHANGE |
| Metacounters (`createMetaCounters`, atomic increments) | none | docs | REMOVE (or CHANGE to group metadata, non-atomic — say which) |
| Operators, roles (`addOperators`, `role`) | group member scopes: admin / moderator / participant (`users-groups`) | components / docs | CHANGE |
| Ban / kick members, banned-members list + unban (`banUser`, `removeMember`, `BannedUserListQuery`, `unbanUser`) | group member management: the kit's members list + the SDK's banned-members request + unban (`/sdk/<platform>/group-kick-ban-members`) | components / SDK | REMOVE |
| Mute a member, freeze a channel (`muteUser`, `freeze`) | none | docs | REMOVE |
| Invitations with accept/decline (`invite`, `acceptInvitation`) | none (members are added directly) | docs | CHANGE (invite = add member) + REMOVE the accept/decline UI |
| Hide / archive channel (`hide`, `unhide`) | none | docs | REMOVE |
| Report user/message/channel (`report*`) | `report-message` / `moderation` | features | REMOVE |
| Profanity / domain / image filters (dashboard) | `moderation` | features + dashboard | action item: recreate the rules |

### Push, calls and other products

| Sendbird feature (signals) | CometChat id | Via | If absent |
|---|---|---|---|
| Push (`registerFCMPushTokenForCurrentUser`, `registerAPNSPushTokenForCurrentUser`) | `push-notifications` | push | action item (credentials in the dashboard) |
| Push preferences: DND, per-channel mute, trigger options, snooze | notification preferences: mute/unmute conversations, DND, schedules (`/notifications/preferences`) | push / SDK | REMOVE only what the preferences page lacks (e.g. snooze) |
| Sendbird Calls: 1:1 `dial`, group `Room` | `voice-video-calls` | calls (or the headless calls peer) | REMOVE |
| AI chatbot, bot users | `ai-assistant`, `ai-agents`, `smart-reply`, `conversation-summary` | features | REMOVE |
| Sendbird Desk (tickets) | `support-integrations` | features / docs | REMOVE |
| Sendbird Live (`@sendbird/live`) | `live-streaming` | features / docs | REMOVE |
| Business Messaging / notification feed (`FeedChannel`, notification templates) | `notification-feed` / `campaigns` | features / docs | REMOVE |
| Local caching / collections (`localCacheEnabled`, `*Collection`) | none | core | CHANGE (online-first; list the offline gap) |

### Look and feel, server

| Sendbird feature (signals) | CometChat id | Via | If absent |
|---|---|---|---|
| Theme, colors, dark mode (`colorSet`, `SBUTheme`, `setDefaultThemeMode`) | theming | customization | — |
| String sets / localization (`stringSet`, `SBUStringSet`) | localization (docs) | customization | CHANGE (the kit's defaults) |
| Webhooks (`x-sendbird-signature`) | CometChat webhooks | server (SKILL step 7) | REMOVE (and list) each event with no equivalent |
| Platform API admin calls (bulk users, channel admin) | CometChat REST (docs) | server | REMOVE the call + list it |

A feature in the ledger that has no row here: treat it like a `none` row. Check `features.json`, then the docs, then REMOVE or CHANGE, and say which in the report.

## Deciding "unsupported" — the verification ladder (read before any REMOVE)

**An MCP search that returns NOTHING is NOT evidence of "unsupported" — nor is the MCP being down.** An empty result (or "no dedicated page") is INCONCLUSIVE: the feature is often documented under CometChat's OWN term (a vendor "voice message recorder" is CometChat's **media recorder** / **voice notes**), folded into a broader page (a composer prop, not its own page), or just ranked out of the top hits. So when the MCP doesn't surface it, walk this ladder BEFORE any verdict:

1. **Re-query with CometChat vocabulary** — component/product names; drop over-qualifiers like the version/platform.
2. **LIVE-FETCH the likely docs page** — `fetch_cometchat_doc_page` (or a plain fetch of the docs URL + `.md`) of the family's composer / features / component page.
3. **Cross-check the family CATALOG** (the installed component/symbol list) — if the component is there, it IS supported, migrate it.

Mark **UNSUPPORTED only** when the CATALOG lacks it AND the live doc fetch (not merely an empty MCP search) also finds nothing. If it genuinely can't be checked (tooling down, network blocked), KEEP it and mark `needs-verification` — never REMOVE a feature you could not verify is absent. **Every UNSUPPORTED row needs evidence** in the report: the `features.json` result plus the exact UI Kit AND SDK docs queries you ran and what each returned. A REMOVE with no docs query is not allowed. Docs MCP not connected? Use a plain fetch (`RULES.md` → Fetch discipline).
