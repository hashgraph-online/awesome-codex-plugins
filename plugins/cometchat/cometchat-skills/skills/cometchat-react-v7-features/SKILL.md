---
name: cometchat-react-v7-features
description: "Enable a specific CometChat feature in a React v7 app — reactions, polls, stickers, mentions, translation, link preview, smart replies and other AI, calls, push notifications, moderation. Looks the feature up in the features.json oracle, then wires enablement. Triggers: 'add reactions', 'enable polls', 'turn on smart replies', 'enable message translation', 'add voice/video calling'."
license: "MIT"
compatibility: "React >=18; @cometchat/chat-uikit-react ^7 (7.1.x, verified 7.1.0)"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat react features extensions ai calls push moderation v7"
---

> **Ground truth:** the feature existence oracle is `features.json` (pack root). A feature a user asks for MUST be an `id` there — if it's not listed, it does not exist; do not invent it. Exact enablement steps + current dashboard nav + config keys: FETCH from the feature's `docs_topic` (docs flag dashboard paths as fragile). UI component names come from the `web-v7` catalog. Status: **oracle curated from live docs 2026-07-29; entries marked VERIFY need confirming before shipping enablement steps.**

## Companion skills (read first)
- `cometchat-react-v7-core` — install, credentials, `init→login→render`, provider. This skill ASSUMES it.
- `cometchat-react-v7-components` — the component catalog features render through.

## Use this skill when
The user wants to turn ON a specific capability: "add reactions", "enable polls", "turn on smart replies", "add push notifications", "enable message translation", "add calling", "add moderation".

## Prerequisites & install
Core setup done (credentials + init/login). Most features add no package; `voice-video-calls` needs the separate calls package.

## Enable a feature (BODY — the oracle-driven flow)
1. **Look it up in `features.json`.** Match the request to a feature `id`. Not listed → tell the user it isn't an available feature (don't invent one).
2. **Branch on `category` + `enablement`:**
   - `default` / `auto` → the SDK-side capability is on, but **check `needs_stitching` first**. If `needs_stitching: true`, the drop-in renders a default-ON affordance that is INERT/partial until the host wires it — you MUST either stitch it (callback + companion panel/component) or hide it; never leave it dead-ending (see the "Default-on affordances" pitfall). Otherwise nothing to enable — point at the `ui_components` if they want to surface/customize it.
   - `extension` + `dashboard-extension` → enable the extension, then wire the client. **Two ways to enable: (a) via the CLI — `npx @cometchat/skills-cli@3 features enable <id>` flips the dashboard toggle via the API (reads the App ID from `.cometchat/config.json`; `features list` shows current state); OR (b) manually in the CometChat Dashboard → Extensions.** Offer the CLI (faster), fall back to the dashboard. The CLI only flips the toggle — YOU still wire the client component/prop. FETCH the current dashboard steps from `docs_topic` — do not bake the path.
   - `ai` → enable via **dashboard-toggle** (AI User Copilot) AND wire the code prop — NOT zero-code (AUDIT-009). The toggle can be flipped by the CLI too — `@cometchat/skills-cli@3 features enable <id>` (an AI feature may first need an OpenAI key set on the app; the CLI reports that). Then wire the props: The copilot props DEFAULT TO OFF, so nothing appears until you set them: smart-reply → `showSmartReplies` on `CometChatMessageList` (default false; renders in the list FOOTER, not the composer); conversation-starter → `showConversationStarters` on `CometChatMessageList` (default false); conversation-summary → `showConversationSummaryButton` + `onSummaryClick` on `CometChatMessageHeader` (default false). These are `needs_stitching:true`. Only `ai-assistant` renders a distinct component (`CometChatAIAssistantChat`). Plan-gating is often 'unknown' — verify, don't assert.
   - `package-install` (calls) → install the separate calls package (FETCH the exact coordinate/version from `docs_topic`), then wire the `ui_components`.
   - **No UI Kit component (SDK-backed feature)** → the capability exists in the SDK but the UI Kit ships NO component for it (AI agents, campaigns, advanced/AI moderation, bots, webhooks, transient messages). Wire it from the **JavaScript Chat SDK** directly — look the exact method up in `cometchat-react-v7-core/references/docs-map.md` → **SDK docs** (the `llms.txt` index → the feature's page → its **AI-Integration-Quick-Reference accordion** for the method signatures; e.g. AI agents → `CometChat.addAIAssistantListener(...)`). This is the UI-Kit-first / SDK-fallback rule (`RULES.md`) — don't skip the feature and don't hand-roll what the SDK already exposes.
   - `dashboard-only` (moderation) → configured ENTIRELY in the dashboard; emit **ZERO moderation UI code (AUDIT-078)**. Its `ui_components` (`CometChatModerationView` / `CometChatFlagMessageDialog`) are **AUTO-RENDERED / INTERNAL**, NOT host-wired: the kit auto-shows the moderation **footer** for blocked/pending messages (`CometChatMessageList hideModerationView` defaults false = shown), and the message list already ships a **built-in "Report message" option** that opens the flag dialog internally. So do **NOT** hand-roll a custom Report option (plugin `getOptions`) and do **NOT** mount `CometChatFlagMessageDialog` yourself — that duplicates the built-in. The only work is in the **Dashboard**: set up the Rules Engine (auto block/flag on send) + turn ON **Report Message / Report User**; the kit then surfaces everything with no code. (Rules Engine is not a classic extension → the CLI can't toggle it; give the user the dashboard steps.)
3. **Wire the UI** using only the feature's `ui_components` (they exist in the `web-v7` catalog); fetch exact props from each component's `.md` twin (`cometchat-react-v7-core/references/docs-map.md`). **If the feature is a whole TASK with an end-to-end guide (check the docs-map "Task guides (recipes)" section — e.g. group chat, search, threads, new-chat, message-privately, block/unblock), BUILD FROM the guide and COMPARE your implementation against it for completeness — then apply the hardening deltas on top (docs-maximal; docs-map). No matching guide? → wire the `ui_components` the normal way (above) + fetch props; the guide is an enhancement, not required.**
4. **Respect VERIFY notes** — any entry noting VERIFY (or an `ai`/`e2e-encryption`/`moderation` entry) must be confirmed against live docs for plan-gating and exact slugs before you emit steps.

## Advanced / extensibility recipes (curated — verified against installed 7.1.x types)

### Custom message types → the message-plugin architecture
v7 replaces v6's `CometChatMessageTemplate` with **plugins**. A custom message type is an object implementing `CometChatMessagePlugin` (`id`, `messageTypes`, `messageCategories`, `renderBubble`), registered on the provider. The `plugins` prop is MERGED with `defaultPlugins` internally — pass ONLY your extras; use `removePlugins` to override a built-in type.
```tsx
import { CometChatProvider } from "@cometchat/chat-uikit-react";
import type { CometChatMessagePlugin } from "@cometchat/chat-uikit-react";

const productCardPlugin: CometChatMessagePlugin = {
  id: "product-card",
  messageTypes: ["product_card"],      // your custom SDK message type
  messageCategories: ["custom"],
  renderBubble: (message) => <div className="product-card">{message.getSender().getName()}</div>,
};

<CometChatProvider plugins={[productCardPlugin]}>
  <div>{/* your chat UI */}</div>
</CometChatProvider>
```
> `CometChatProvider` REQUIRES `children`. Optional plugin-interface hooks: `getOptions`, `getLastMessagePreview`, `renderHeaderView`/`renderFooterView`, `getTextFormatters`. This is provider-level config — there's no standalone screen to render.

### Text formatters / rich text
The default text plugin already applies **@mentions, URLs, and markdown**. Add CUSTOM formatting by subclassing the abstract `CometChatTextFormatter` (`id` + `getRegex()` + `format()`) and passing it via the `textFormatters` prop on `CometChatMessageComposer` (input) and the bubble components — it is **NOT** a prop on `CometChatMessageList`. The built-in formatters (`CometChatMentionsFormatter`, `CometChatUrlFormatter`, `CometChatMarkdownFormatter`, `CometChatRichTextFormatter`) have **no-arg constructors**.
```tsx
import { CometChatMessageComposer, CometChatTextFormatter } from "@cometchat/chat-uikit-react";

class HashtagFormatter extends CometChatTextFormatter {
  readonly id = "hashtag-formatter";
  getRegex() { return /#(\w+)/g; }
  format(text: string) { return text.replace(this.getRegex(), '<span class="hashtag">#$1</span>'); }
}

<CometChatMessageComposer textFormatters={[new HashtagFormatter()]} />
```
> **The message LIST ignores these props** — its text bubbles use the text plugin's `getTextFormatters()` (default markdown + mentions + URL). To format hashtags in the list too, override that method via the provider: `plugins={[{ ...CometChatTextPlugin, getTextFormatters: () => [new CometChatMarkdownFormatter(), new CometChatMentionsFormatter(), new CometChatUrlFormatter(), new HashtagFormatter()] }]}` (provider plugins precede the defaults, so it wins; verified vs 7.1.0).
> **RTE toolbar ≠ `textFormatters` (AUDIT-051).** The **rich-text editor TOOLBAR** (bold/italic/underline/lists/links buttons in the composer) is a SEPARATE feature: toggle it with the `enableRichTextEditor` PROP on `CometChatMessageComposer` — `<CometChatMessageComposer enableRichTextEditor />` — a prop, NOT a component swap. (There is **no** `CometChatCompactMessageComposer` in v7 — that was a v6 phantom.) `textFormatters` above is for CUSTOM inline formatters (hashtags, @mentions, custom markup); they're orthogonal and can be used together. (There is no CLI shortcut — the skill sets the `enableRichTextEditor` prop directly.)

### Calls / push operational depth
**Calls now has its own skill — `cometchat-react-v7-calls`.** For "add voice/video calling", route there: it bakes the install (`@cometchat/calls-sdk-javascript@5`, not bundled), the calling-on switch (`uiKit:{callsSDK:{}}` on `CometChatUIKit.initFromSettings` — the `initFromSettings` equivalent of the classic `setCallingEnabled(true)`), the root `CometChatIncomingCall` wiring, 1:1-rings-vs-group-joins, and the gotchas (idle-timeout in **ms**, zero-dimension call surface, Next.js SSR + webpack fallback, no group-ring, HTTPS/`getUserMedia`).
**Push notifications → the `cometchat-react-v7-push` skill** (thin + docs-first: it fetches CometChat's notifications docs and bakes the hardening deltas + SDK symbols). Route "add push" there — do NOT re-derive push here (single source).

## Common pitfalls (BAKED)
- **Default-on affordances that need stitching** (`features.json` `needs_stitching: true`). Some drop-ins render a live-looking control BY DEFAULT that no-ops until the host wires it — do NOT treat these as "already on, nothing to do":
  - `CometChatConversations` search bar (`showSearchBar` default `true`) only client-side-filters already-loaded conversation names — it is NOT real search. Wire `onSearchBarClicked` → open `CometChatSearch`, or hide it with `showSearchBar={false}`. (Real search may also need a Dashboard toggle — VERIFY.)
  - `CometChatMessageList` thread-reply indicator / "Reply in Thread" no-ops until `onThreadRepliesClick` opens a thread panel (`CometChatThreadHeader` + `CometChatMessageList parentMessageId` + `CometChatMessageComposer parentMessageId`) — wire it or hide with `hideReplyInThreadOption`.
  - Rule: never emit a default-on affordance that dead-ends. Either wire the destination or hide the trigger.
- Emitting a feature/component below its `contracts.json` minimum (e.g. group details without ban/kick/scope) — always cover the full min_capabilities (deterministic minimum, same every prompt).
- Claiming a feature that isn't in `features.json` (phantom feature) — the #1 hallucination here.
- Emitting a baked dashboard nav path — it rots; FETCH it.
- Rendering a feature's UI component without enabling its extension first (renders empty/no-ops).
- **Hand-rolling moderation UI (AUDIT-078).** Moderation is dashboard-only AND auto-surfaced: the kit renders the moderation footer for blocked/pending messages and the message list already ships a built-in "Report message" option (which opens the flag dialog internally). Do NOT add a custom Report option (plugin `getOptions`) or mount `CometChatModerationView`/`CometChatFlagMessageDialog` yourself — that duplicates the built-in. Emit ZERO moderation UI code; the only work is the Dashboard Rules Engine + Report Message/User toggles.
- Assuming an AI/E2EE feature is available on every plan — it's plan-gated; verify.

## Verify it works
The enabled feature actually works in the running app (reactions appear, a poll sends, smart replies show, etc.) and any Dashboard toggle it needs is ON. If it renders empty, the extension/feature likely isn't enabled in the CometChat Dashboard.

**Close (after it builds):** end with the shared 3-option selectable menu and WAIT for the pick — **① add another feature** (suggest a few not-yet-wired) · **② customize theming** · **③ test it manually** (stop; let the user check). Same contract as the `cometchat-react-v7-core` close (`RULES.md` §19).
