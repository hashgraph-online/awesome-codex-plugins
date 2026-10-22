---
name: cometchat-flutter-v6-features
description: "Enable a specific CometChat feature in a Flutter v6 app — polls, stickers, collaborative whiteboard/document, translation, link preview, AI smart replies, moderation, calls, push. Looks the feature up in the features oracle, then wires only what the kit does not already do. Triggers: 'add polls in flutter', 'enable stickers', 'turn on smart replies in flutter', 'enable message translation in flutter', 'add moderation', 'enable an extension in flutter'."
license: "MIT"
compatibility: "Flutter >=3.38.9; cometchat_chat_uikit ^6 (6.1.x, verified 6.1.0)"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat flutter features extensions ai moderation v6"
---

> **Ground truth:** the feature-existence oracle is `features.flutter-v6.json` (pack root). A feature the user asks for MUST be an `id` there — if it is not listed, it does not exist; do not invent it. Exact dashboard steps come from the feature's `docs_topic` (dashboard paths rot — FETCH them). Widget names come from `catalogs/flutter-v6.json`.

## Companion skills (read first)
- `cometchat-flutter-v6-core` — install, credentials, `init→login→render`. This skill ASSUMES it.
- `cometchat-flutter-v6-components` — the widget catalog features render through.

## Use this skill when
The user wants to turn ON a capability: "add polls", "enable stickers", "turn on translation", "add smart replies", "add moderation", "enable an extension".

## Prerequisites & install
Core done. Most features add NO package; `voice-video-calls` adds one (→ `-calls`), push adds Firebase (→ `-push`).

## THE v6 RULE THAT CHANGES EVERYTHING
**v6 deleted the entire v5 extension architecture.** There is no `UIKitSettings.extensions`, no `CometChatUIKitChatExtensions`, no `DataSource`, no `ChatConfigurator`, no `*ExtensionDecorator`, no `CometChatUIKit.getDataSource()`. A dashboard-enabled extension surfaces **automatically** through `MessageTemplateUtils` — composer action sheet, message bubbles — with **zero client registration code**.
> So for most extensions the correct answer is: **flip the Dashboard toggle and write NO code.** Emitting v5-style registration into a v6 app is a defect, not a harmless no-op. If the user already has such code, that is a migration problem (→ `-migration`).

## Enable a feature (the oracle-driven flow)
1. **Look it up in `features.flutter-v6.json`.** Match the request to an `id`. Not listed → say so; don't invent one.
2. **Branch on `category` + `enablement`:**
   - **`default` / `auto`** → already on. Check `needs_stitching`: if true, the kit renders an affordance that is inert until the host navigates somewhere (thread indicator, search field) — wire it or hide it, never dead-end. Otherwise there is nothing to do; point at the `ui_components` if they want to restyle it (→ `-customization`).
   - **`extension` / `dashboard-extension`** → **Dashboard toggle only.** Confirm it's on, then verify it appears (composer action sheet for polls/stickers/collaborative; bubbles for link-preview/translation/thumbnails). **Write no registration code.** Entries carry `auto_rendered_ui: true` — their widgets exist for *styling*, not for you to mount.
   - **`ai`** → Dashboard toggle (AI features may need an OpenAI key on the app) **and** the view must be surfaced. VERIFY per feature whether v6 auto-renders it or the host places `CometChatAISmartRepliesView` / `CometChatAIConversationStarterView` / `CometChatAIConversationSummaryView`. Plan-gating is often unknown — verify, don't assert.
   - **`package-install`** → calls (→ `-calls`) or push (→ `-push`). Do not re-derive those here.
   - **`dashboard-only`** (moderation) → configured ENTIRELY in the Dashboard; emit **ZERO** moderation UI. `CometChatMessageList` already renders blocked/moderated content and already ships a built-in "Report message" action. Hand-rolling either duplicates the built-in.
   - **`sdk-only`** (campaigns, AI agents, advanced moderation) → no kit widget; call the Chat SDK directly, looking the method up in `../cometchat-flutter-v6-core/references/docs-map.md` → SDK docs. UI-Kit-first, SDK-fallback.

**Announce anything you send via the SDK.** The v6 Flutter `events` page now enumerates the `ccMessage*` events (DOCS-BACKLOG F6 corrected upstream — verified against `cometchat/docs`@`2ebb1db`, 2026-09-09); the guidance below matches both the page and the installed kit 6.1.0.

A message sent with `CometChat.send*Message` instead of `CometChatMessageComposer` does not reach kit widgets on its own — CometChat does not echo your own sends back through the realtime listener, so an on-screen `CometChatMessageList` only learns about it on its next fetch (which looks like "it works" if the list is opened fresh each time, and "nothing happens" if it is always mounted). Emit the event yourself in `onSuccess`:
```dart
import 'package:cometchat_chat_uikit/cometchat_chat_uikit.dart';
// The barrel exports TWO enums named MessageStatus; ccMessageSent wants the core
// one, so import it under a prefix exactly as the kit's own composer does.
import 'package:cometchat_chat_uikit/shared_ui/src/clean_architecture/core/constants/enums.dart'
    as core_enums;

Future<void> post(CustomMessage msg) => CometChat.sendCustomMessage(
      msg,
      onSuccess: (sent) =>
          CometChatMessageEvents.ccMessageSent(sent, core_enums.MessageStatus.sent),
      onError: (e) {},
    );
```
3. **Wire only the `ui_components` the entry names**, fetching props from the widget's `.md` twin.
4. **Respect VERIFY notes** — any entry marked VERIFY (AI, notification-feed, campaigns, search dashboard-gating) must be confirmed against live docs before you state enablement steps.

## Already ON by default in v6 — never offer these as "add a feature"
**reactions · mentions (incl. `@all`) · quoted reply · threaded replies · read receipts · typing indicators · presence · mark-as-unread · report message · media sharing · voice notes.** They are core messaging, not extensions. If asked, say they're already on and offer to customize them. (Their legacy extension pages exist but are marked deprecated — the oracle flags them.)

## Deprecated — never suggest
`email-replies`, `e2e-encryption`: absent from the Flutter v6 extensions page and legacy docs-wide. Flagged `deprecated: true` in the oracle.

## Common pitfalls (BAKED)
- **Writing v5 extension-registration code** — the #1 v6 error (see above).
- **Mounting an `auto_rendered_ui` widget yourself** (moderation view, flag dialog, sticker keyboard) — duplicates the built-in.
- **Claiming a feature that isn't in the oracle** — the #1 hallucination.
- **Baking a dashboard nav path** — it rots; FETCH it.
- **Offering reactions/mentions/threads as add-ons** — already on.
- **Rendering a feature's widget without the Dashboard toggle** → renders empty and looks broken.
- **Assuming an AI feature is on every plan** — plan-gated; verify.

## Verify it works
The feature actually works in the running app (a poll sends, a sticker appears, translation shows in the action sheet), and any Dashboard toggle it needs is ON. Renders empty ⇒ the toggle is off, not a code problem.

**Close (after it builds):** end with the shared 3-option selectable menu and WAIT — **① add another feature · ② customize theming · ③ test it manually** (`RULES.md` §19).
