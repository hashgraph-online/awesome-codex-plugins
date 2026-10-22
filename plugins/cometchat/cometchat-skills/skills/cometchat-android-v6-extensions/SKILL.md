---
name: cometchat-android-v6-extensions
description: "Turn on CometChat Dashboard extensions in an Android v6 app — stickers, polls, collaborative whiteboard and document, message translation, link preview, thumbnail generation, message shortcuts — and know exactly where each one appears in the UI once enabled (mostly zero client code). Triggers: 'enable stickers android', 'add polls to my android chat', 'message translation android cometchat', 'link previews not showing', 'what extensions does the android ui kit support'."
license: "MIT"
compatibility: "Android minSdk >=28; compileSdk >=36; Kotlin >=2.1; AGP >=8.9.1; JVM target 11; com.cometchat:chatuikit-kotlin-android ^6 OR com.cometchat:chatuikit-compose-android ^6 (6.0.x, verified 6.0.5); com.cometchat:chat-sdk-android ^5"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat android extensions v6 stickers polls translation dashboard"
---

> **Ground truth:** `features.android-v6.json` (the extension entries + their `enablement`) + catalog `android-v6.json` + the live page `/ui-kit/android/extensions` (the manual — 8 built-ins) and each extension's `/fundamentals/*` page. Verify symbols against the catalog; fetch details from docs; never invent an extension.

## Companion skills (read first)
- `cometchat-android-v6-core` — install, credentials, `initFromSettings → login → render`, the fetch map. Assumed here, never repeated.
- `cometchat-android-v6-features` — the general feature-lookup skill; come here for the Dashboard-extension slice specifically.

## Use this skill when
"enable stickers/polls/whiteboard/document/translation/link preview/thumbnails", "add message shortcuts", "which extensions work with the Android UI Kit?", "I enabled it in the Dashboard but nothing shows up".

## Prerequisites & install
Same kit + `initFromSettings → login` as `core`. **No Gradle dependency and (for the 7 auto-rendered ones) no client code** — the UI Kit detects an enabled extension after init+login and renders it in the right component.

## The 8 built-ins — enable in Dashboard, appears here
| Extension | Enable | Where it appears once enabled |
|---|---|---|
| **Stickers** | Dashboard → Extensions | Composer (sticker keyboard → `CometChatStickerKeyboard`; sent as `CometChatStickerBubble`) |
| **Polls** | Dashboard → Extensions | Composer action sheet (`CometChatCreatePoll`; rendered as `CometChatPollBubble`) |
| **Collaborative Whiteboard** | Dashboard → Extensions | Composer action sheet; opens as a collaborative bubble in the list |
| **Collaborative Document** | Dashboard → Extensions | Composer action sheet; opens as a collaborative bubble in the list |
| **Message Translation** | Dashboard → Extensions | Message long-press/action sheet in `CometChatMessageList` |
| **Link Preview** | Dashboard → Extensions | Automatically inside message bubbles for URLs |
| **Thumbnail Generation** | Dashboard → Extensions | Automatically on image/video bubbles (smaller previews) |
| **Profanity Filter** | Dashboard → Extensions | Message bubbles (censored text) — ⚠️ **LEGACY** |

**Message Shortcuts** is the one extension that is NOT zero-code: enable it in the Dashboard, then implement a shortcut formatter extending `CometChatTextFormatter` — build it from the docs recipe `/ui-kit/android/shortcut-formatter-guide` (→ `cometchat-android-v6-{kotlin,compose}-customization` for the formatter mechanism).

## Enablement — the whole flow
1. **Ask which are already enabled** — per-app Dashboard state is not readable from code; never assume OFF (and never re-suggest one that's already on).
2. **Enable in the CometChat Dashboard** → your app → Extensions → the extension. That's the actual "installation".
3. **Re-login / restart the app** — the kit picks extensions up at init+login; a session started before you toggled won't show it.
4. **Verify in the right place** (table above). No code change, no rebuild, for the 7 auto-rendered ones.
5. Only if the ask is *styling* the extension's UI → `cometchat-android-v6-{kotlin,compose}-customization`.

## Deprecated / superseded — don't offer these
**Profanity Filter is LEGACY**: the extensions page still lists it, but its guide points at the legacy-docs archive. For new work steer to the **Moderation** product (`features.android-v6.json` → `moderation`, dashboard-configured rules + AI moderation) — say this plainly rather than wiring the legacy path. Anything not in the table above and not in `features.android-v6.json` does not exist for this kit: don't invent extensions (no "reactions extension" — reactions are core in v6; same for mentions).

## Common pitfalls
Writing client code for an auto-rendered extension (never needed) · hand-rolling polls/stickers UI that the kit already renders · enabling in the Dashboard but not re-logging in · expecting an extension before `init`+`login` succeed · offering Profanity Filter for new work · treating reactions/mentions as extensions (they're core in v6) · assuming an extension enabled on one app applies to another (per-app setting).

## Verify it works
No catalog/compile change is expected for the auto-rendered ones (nothing was emitted); for Message Shortcuts, compile (`./gradlew :app:assembleDebug   # in YOUR app (npm run verify:fences:android-v6 is a pack-repo gate)`) and confirm the formatter is registered. On device, after enabling + re-login: the extension's entry point is present where the table says (composer action sheet / sticker keyboard / message action sheet / inside the bubble) and a sent artifact renders as its bubble type. Nothing showing ⇒ check init/login succeeded, then the Dashboard toggle for THIS app, then re-login — in that order.
