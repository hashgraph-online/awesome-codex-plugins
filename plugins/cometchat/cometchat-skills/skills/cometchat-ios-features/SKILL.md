---
name: cometchat-ios-features
description: "Turn on and wire individual CometChat features on iOS — threads, search, reactions, receipts, mentions, AI, moderation, extensions like polls and stickers. Use when the ask is one capability rather than the whole surface. Triggers: 'add reactions ios', 'enable polls cometchat', 'smart replies ios', 'add threads', 'turn on read receipts'."
license: "MIT"
compatibility: "CometChatUIKitSwift 5.1.22 · iOS 15.1+"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat ios features extensions ai moderation swift v5"
---

## Companion skills (read first)
- `cometchat-ios-core` owns setup and the default surface. This skill ADDS one capability at a time. The feature list is `features.ios-v5.json`; never claim a feature that is not in it.

## Use this skill when
"add reactions", "enable polls", "turn on smart replies", "add message search", "let people report a message".

## First: which KIND of feature is it? This decides the work.
| Kind | What it needs | Examples |
|---|---|---|
| **Already on** | nothing — say so | text, media, receipts, typing, reactions, mentions |
| **Code-wired** | a callback + a destination screen | threads, search, mark-as-unread, quoted reply |
| **Dashboard extension** | a toggle in the Dashboard; **no code** | polls, stickers, whiteboard, document, translation, link preview, thumbnails |
| **AI** | a Dashboard AI toggle, then wire the surface | conversation starters, smart replies, summary, assistant history |
| **SDK fallback** | no kit component — call the SDK | AI agents, campaigns, add-members, moderation actions |

**Never re-suggest something already on.** Reactions and mentions are core messaging in v5; offering them as "add a feature" is the AUDIT-077 mistake. The legacy moderation filters (profanity, data masking, image moderation) route to legacy docs — never offer them.

## Dashboard-gated features: enable, then verify — do not write code
The Dashboard toggle is the whole job for extensions: *"Code required: None — extensions work out of the box."* Use the CLI to flip it (`skills-cli features enable <id>`), then confirm it appears. If it does not, that is a Dashboard/plan issue, not a code one — say so rather than hand-rolling a replacement.

## Code-wired features: wire the round trip
A feature that opens something must also close it. Threads: `set(onThreadRepliesClick:)` → thread screen (**header `set(parentMessage:)`; LIST `set(user:parentMessage:withParent:)` — parent in the SAME call as the target, or the thread shows the whole conversation; composer `set(user:)` + `set(parentMessageId:)`**). Search: set `conversations.hideSearch = false` FIRST — it is true by default, so wiring only `conversations.onSearchClick` (property) renders no search field at all → `CometChatSearch`, with `onConversationClicked` / `onMessageClicked` assigned or results dead-end.

## SDK fallback — UI Kit first, SDK only when the kit has nothing
If no component exists, drop to the Chat SDK and **look the method up** in the SDK docs via `docs-map.md` — never guess a signature. Worked example: adding group members has no component → `CometChat.addMembersToGroup(guid:groupMembers:bannedUIDs:onSuccess:onError:)`.

## Gotchas
- **`verify: true` entries in `features.ios-v5.json` are unconfirmed** — read the feature's own page before asserting how it is enabled.
- **Smart Replies is documented two ways** (composer extension vs AI toggle) — treat it as AI and say the docs disagree.
- **Never invent an enablement story.** If you cannot find how a feature turns on, say so.

## Verify it works
The feature appears in the running app, its entry point leads somewhere and back, and nothing you added duplicates what the kit already does.
