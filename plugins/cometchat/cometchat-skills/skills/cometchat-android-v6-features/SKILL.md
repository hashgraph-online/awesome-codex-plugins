---
name: cometchat-android-v6-features
description: "Add or enable a specific CometChat feature in an Android v6 app — receipts, typing, reactions, mentions, threads, search, polls, stickers, translation, link previews, AI smart replies / conversation starter / summary, AI agents, moderation, notification feed, campaigns — by resolving the ask to the feature oracle and taking the right enablement path (already-on vs Dashboard toggle vs Gradle package vs code wiring). Triggers: 'add search to my android chat', 'enable polls android', 'turn on smart replies android', 'add reactions android', 'is X supported in the android ui kit'."
license: "MIT"
compatibility: "Android minSdk >=28; compileSdk >=36; Kotlin >=2.1; AGP >=8.9.1; JVM target 11; com.cometchat:chatuikit-kotlin-android ^6 (XML Views) OR com.cometchat:chatuikit-compose-android ^6 (Compose) — 6.0.x, verified 6.0.5; com.cometchat:chat-sdk-android ^5"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat android features v6 enablement extensions ai search compose views"
---

> **Ground truth:** `features.android-v6.json` (the feature-existence + enablement oracle) + catalog `android-v6.json` + the live feature pages (`core-features`, `extensions`, `ai-features`, `call-features`, the `guide-*` recipes). A feature not in the oracle does NOT exist for this kit — say so; never invent one. Fetch component params from docs (`core` → `references/docs-map.md`).

## Companion skills (read first)
- `cometchat-android-v6-core` — install, credentials, `initFromSettings → login → render`, hot-path callbacks, the fetch map. Assumed here, never repeated.
- Deeper slices: `cometchat-android-v6-extensions` (the 8 Dashboard extensions in detail) · `cometchat-android-v6-calls` (voice/video) · `cometchat-android-v6-push` (FCM) · `cometchat-android-v6-{kotlin,compose}-customization` (styling a feature's UI).

## Use this skill when
"add `<feature>` to my Android chat", "enable `<feature>`", "does the Android UI Kit support `<X>`?", "why isn't `<feature>` showing up?". The job: resolve the ask against the oracle, take the right enablement branch, wire only what needs wiring, and tell the user honestly what it needs (Dashboard? package? code?).

## Prerequisites & install
Same kit + `initFromSettings → login` gate as `core`. Some features add a Gradle artifact (calls, push) or need a Dashboard toggle — the branch below says which.

## Feature lookup — resolve the ask, then branch
1. **Find the id** in `features.android-v6.json` (table below). No match ⇒ the kit has no built-in for it: check whether the **Chat SDK** covers it (`core/references/docs-map.md` → SDK section) and say plainly that there's no UI-Kit component.
2. **Read `enablement`** and take exactly one branch:
   - **`auto`** — already ON in v6. Do NOT "add" it; confirm it's there and offer to *customize* it (`cometchat-android-v6-{kotlin,compose}-customization`). Applies to reactions, mentions, receipts, typing, presence, quoted replies, rich text, media, mark-as-unread, report.
   - **`dashboard-toggle` / `dashboard-extension`** — enable it in the **CometChat Dashboard**; the kit auto-integrates it after `init`+`login`, **no client code**. Your job: tell the user exactly where it will appear (composer action sheet, message list, bubble) and how to verify. Ask which are already enabled — you cannot read per-app Dashboard state.
   - **`gradle-package`** — add the artifact, then wire (calls: `com.cometchat:calls-sdk-android` + `uiKit.enableCalling` in `assets/cometchat-settings.json`; push: `com.cometchat:push-notifications-android` + Firebase). Route to the dedicated skill.
   - **`code-prop`** — the kit ships the component/affordance but the HOST wires it (a screen, a callback, a formatter). This is real work: build it, wire the round-trip, verify.
   - **`dashboard-only`** — no client code at all (moderation, campaigns); explain the effect users will see.
3. **Check `needs_stitching` (⚙ below)** — a default-ON affordance that dead-ends until you wire a destination (or hide it). Wire it or hide it; never leave it inert.
4. **Guide-first**: if the docs ship a `guide-*` recipe for this feature (see `core/references/docs-map.md` → "Task guides"), BUILD FROM the guide, then DIFF your implementation against it, then apply the hardening deltas (credentials via the settings file, init→login gate, thread targets, IME/insets sizing, listener teardown).
5. **Wire the feature's `ui_components`** — fetch exact params for YOUR cohort from the component page's `.md` twin.

## Feature table (BAKED from `features.android-v6.json` — ⚙ = needs stitching)
| Feature id | Enablement | Components |
|---|---|---|
| `text-messaging` | auto | CometChatMessageList, CometChatMessageComposer |
| `media-file-attachments` | auto | CometChatMessageComposer, CometChatMessageList |
| `delivery-read-receipts` | auto | CometChatMessageList, CometChatReceipts, CometChatConversations |
| `mark-as-unread` | auto | CometChatConversations |
| `typing-indicators` | auto | CometChatMessageList, CometChatConversations |
| `user-presence` | auto | CometChatConversations, CometChatMessageHeader, CometChatStatusIndicator |
| `reactions` | auto | CometChatMessageList |
| `mentions` | auto | CometChatMessageComposer, CometChatMessageList, CometChatMentionsFormatter |
| `rich-text-formatting` | auto | CometChatMessageComposer, CometChatRichTextFormatter |
| `quoted-replies` | auto | CometChatMessageList, CometChatMessageComposer |
| `users-groups` | auto | CometChatUsers, CometChatGroups, CometChatGroupMembers |
| `report-message` | auto | CometChatMessageList |
| `threaded-replies` | code-prop ⚙ | CometChatMessageList, CometChatThreadHeader, CometChatMessageComposer |
| `message-search` | code-prop ⚙ | CometChatSearch |
| `custom-message-types` | code-prop | CometChatMessageList |
| `text-formatters` | code-prop | CometChatTextFormatter, CometChatMentionsFormatter, CometChatRichTextFormatter |
| `notification-feed` | code-prop | CometChatNotificationFeed |
| `stickers` | dashboard-extension | CometChatMessageComposer, CometChatStickerBubble, CometChatStickerKeyboard |
| `polls` | dashboard-extension | CometChatMessageComposer, CometChatCreatePoll, CometChatPollBubble |
| `collaborative-whiteboard` | dashboard-extension | CometChatMessageComposer, CometChatMessageList |
| `collaborative-document` | dashboard-extension | CometChatMessageComposer, CometChatMessageList |
| `message-translation` | dashboard-extension | CometChatMessageList |
| `link-preview` | dashboard-extension | CometChatMessageList |
| `thumbnail-generation` | dashboard-extension | CometChatMessageList |
| `message-shortcuts` | dashboard-extension ⚙ | CometChatTextFormatter |
| `profanity-filter` | dashboard-extension **LEGACY** | CometChatMessageList |
| `smart-reply` | dashboard-toggle | CometChatMessageComposer |
| `conversation-starter` | dashboard-toggle | CometChatMessageList |
| `conversation-summary` | dashboard-toggle | CometChatMessageComposer |
| `ai-assistant` | dashboard-toggle ⚙ | CometChatAIAssistantChatHistory, CometChatAIAssistantBubble, CometChatMessageList, CometChatMessageComposer |
| `moderation` | dashboard-only | — (dashboard rules; no client code) |
| `campaigns` | dashboard-only | — (authored in Dashboard) |
| `voice-video-calls` | gradle-package ⚙ | CometChatCallButtons, CometChatIncomingCall, CometChatOutgoingCall, CometChatCallLogs, CometChatCallActivity |
| `push-notifications` | gradle-package ⚙ | — (SDK token registration + FCM) |

## Enablement rules that trip people up
- **`reactions` and `mentions` are ON BY DEFAULT in v6** (core messaging). Never offer to "add" or "enable" them — if asked, say they're already on and offer to customize them.
- **`profanity-filter` is LEGACY** — its guide points at legacy docs; steer to **`moderation`** instead. Never suggest it as a new feature.
- **Dashboard-gated ≠ broken**: if a toggled feature doesn't appear, the usual cause is the Dashboard toggle or a stale session — re-login after enabling.
- **Pinned messages / saved messages / thread subscription** are NOT in the current v6 docs set (they're pending on a docs branch). Don't claim them; say they're not documented for v6 yet and offer the SDK path if one exists.
- A feature's UI appears **only after `init` + `login` succeed** — a "missing feature" is often an init/login failure (`core/references/troubleshooting.md`).

## Common pitfalls
Suggesting an `auto` feature as new work · hand-rolling a feature the kit auto-renders (translation, previews, stickers) · wiring a `code-prop` feature's entry point but no way back (dead-end) · a thread screen missing the `user`/`group` target (replies silently don't send) · assuming Dashboard state instead of asking · adding the calls/push artifact without the Dashboard side · guessing component params instead of fetching.

## Verify it works
Every symbol you emitted is in the catalog (Tier-1) and the app compiles (`./gradlew :app:assembleDebug   # in YOUR app (npm run verify:fences:android-v6 is a pack-repo gate)`). On device: the feature's UI appears where the docs say (composer action sheet / message list / bubble / its own screen); a stitched feature round-trips (open AND back); an `auto` feature was left alone; anything requiring the Dashboard was called out explicitly to the user with where-to-click. If it doesn't show, check init/login, then the Dashboard toggle, then re-login — in that order.
