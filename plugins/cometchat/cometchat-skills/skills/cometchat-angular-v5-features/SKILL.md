---
name: cometchat-angular-v5-features
description: "Enable or build any CometChat feature in an Angular app, and say which need zero client code. Covers: reactions · mentions · threaded replies · search · read receipts · typing indicators · presence · media & file attachments · voice notes · polls · stickers · GIFs · message translation · link preview · thumbnails · pin message · save / bookmark messages · reminders · message shortcuts · voice transcription · rich media preview · URL shortener · collaborative whiteboard & document · disappearing messages · support desk integrations · AI smart replies, conversation starter, summary and assistant · voice & video calling · push notifications · notification feed · moderation & reporting · campaigns · custom message types · text formatters & rich text · card messages. Triggers: 'add polls angular', 'enable reactions', 'let users save/bookmark messages', 'pin a message', 'add smart replies', 'turn on translation', 'add stickers or GIFs', 'send a custom message type', 'enable an extension angular'."
license: "MIT"
compatibility: "@cometchat/chat-uikit-angular ^5 (5.1.0–5.2.0 verified); Angular 17-21"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat angular features v5 extensions ai reactions polls stickers translation"
---

> **Ground truth:** the feature existence oracle is `features.angular-v5.json` (pack root). A feature a user asks for MUST be an `id` there — if it is not listed it does not exist; do not invent it. Exact enablement steps and payloads are FETCHED from each entry's `docs_topic` (a PATH — resolve it against `DOCS_BASE` in `cometchat-angular-v5-core/references/docs-map.md`). UI component names come from the `angular-v5` catalog.

## Companion skills (read first)
- `cometchat-angular-v5-core` — install, credentials, `init→login→render`. Assumed, never restated.
- `cometchat-angular-v5-components` — component names, inputs/outputs, slots.

## Use this skill when
Someone asks to add or enable a capability: "add polls", "enable reactions", "turn on smart replies".

## FIRST — classify the request
Most features need **no client code at all**. Writing some is the most common mistake here.

| Class | What you do | Examples |
| --- | --- | --- |
| **Already on** | Nothing. Confirm and show where it appears. | reactions, mentions, receipts, typing, media attachments, voice notes |
| **Dashboard extension — zero code** | Enable in the dashboard. Nothing else — the kit either mounts a dedicated bubble component or renders it inline automatically. | polls, stickers, collaborative whiteboard, collaborative document, message translation, link preview, thumbnail generation |
| **Dashboard extension — HOST-COMPOSED** | Enable in the dashboard, **then you build the UI**: `CometChat.callExtension()` to send/fetch, your own component to render. The dashboard toggle alone does nothing visible. | pin message, save message, message shortcuts, voice transcription, rich media preview, GIFs, reminders, URL shortener, disappearing messages, support integrations |
| **Dashboard + AI** | Enable in the dashboard, then optionally place a component. | smart replies, conversation starter, conversation summary, AI assistant |
| **Client code** | Real wiring. | threads, search, custom message types, text formatters, rich text, calls |

**10 of the 17 extensions are host-composed — nearly two-thirds.** `needs_stitching: true` in `features.angular-v5.json` is the authoritative signal (not `ui_components`: three zero-code entries — message translation, link preview, thumbnail generation — legitimately have `ui_components: []` because they render inline into an existing bubble/menu rather than through a separately-importable component). Verify against `needs_stitching` before answering, never from memory or from this table's examples alone.

Ask which app in the dashboard before telling someone to toggle something.

## Already on by default — do NOT "add" these
`reactions` · `mentions` · delivery/read receipts · typing indicators · media & file attachments · voice notes.

These are **core in v5, not extensions**. Angular's extensions page does not list reactions or mentions, which confirms it. If one is not visible the cause is a missing `@Input()` or an unsized container — not a missing feature. Never write a reaction picker or typing indicator by hand.

## Dashboard extensions — enabling is necessary, NOT always sufficient
Dashboard → your app → Extensions → enable. Then **check the running app**, because there are two kinds:

**Auto-rendered — emit nothing.** The kit surfaces these itself once enabled: polls, stickers, collaborative document/whiteboard (bubbles in the message list), link preview and thumbnails (inside the bubble), message translation (an entry in the message menu).

**Host-composed — the kit renders NO affordance.** Enabling them changes nothing visible; you must call the extension and render your own control:

```ts
import { CometChat } from '@cometchat/chat-sdk-javascript';

// SEND — exact slug, endpoint and payload are on the extension's own docs page
await CometChat.callExtension('pin-message', 'POST', 'v1/pin', { msgId, receiverType });
```
**Send is only a third of the job.** You also need to FETCH the pinned/saved list back and RENDER it — full pattern, incl. the type-safe way to turn a fetched entry into displayable text: `references/host-composed-extensions.md`.

Currently host-composed in Angular (10): **pin message · save message · message shortcuts · voice transcription · rich media preview · GIFs · reminders · URL shortener · disappearing messages · support integrations.** `needs_stitching: true` in `features.angular-v5.json` is the authoritative signal — not `ui_components`, see the table above.

> **Do not conclude a feature "does not exist" because the kit has no component and the SDK has no named method for it.** Extensions are reached through the generic `CometChat.callExtension()` — there is no `pinMessage()` to grep for. Searching `node_modules` for the SEND/FETCH calls will find nothing and that is expected.

> **`docs_topic` is a PATH, not a URL.** Prefix it with `DOCS_BASE` from `cometchat-angular-v5-core/references/docs-map.md`, then append `.md`:
> `{DOCS_BASE}` + `/fundamentals/pin-message` + `.md`
> Do **not** hardcode `https://www.cometchat.com/docs/...`. `DOCS_BASE` may point at a docs preview while a docs change is in flight, and a hardcoded production URL silently reads the pre-change page — so you would fetch a page that is missing the very detail you were sent to find.

Available (from Angular's extensions page): Bitly · Link Preview · Message Shortcuts · Pin Message · Rich Media Preview · Save Message · Thumbnail Generation · TinyURL · Voice Transcription · Giphy · Message Translation · Polls · Reminders · Stickers · Stipop · Tenor · Collaborative Document · Collaborative Whiteboard · Disappearing Messages · Chatwoot · Intercom.

Two have a bubble you may reference when customizing, but you still do not mount them yourself: `CometChatPollBubbleComponent`, `CometChatStickerBubbleComponent`.

**Not available for Angular:** end-to-end encryption, live streaming, email replies. They exist for other platforms. Say so plainly rather than improvising.

## AI features
Enable in the dashboard (AI section), then place the component you need:
```html
<cometchat-smart-replies></cometchat-smart-replies>
<cometchat-conversation-starter></cometchat-conversation-starter>
<cometchat-conversation-summary></cometchat-conversation-summary>
```
`<cometchat-message-list>` also emits `smartReplyClick` and `conversationStarterClick` when those are enabled, so the built-in surfaces work without extra components. The AI assistant is `CometChatAIAssistantChat` — no `Component` suffix.

## Features that DO need code
| Feature | Where |
| --- | --- |
| Threaded replies | `cometchat-angular-v5-placement` — thread panel |
| Search | `cometchat-angular-v5-placement` — search column |
| Custom message types | `references/custom-messages.md` |
| Text formatters / rich text | `references/formatters.md` |
| Voice & video calls | `cometchat-angular-v5-calls` |
| Push notifications | `cometchat-angular-v5-push` |

## Common pitfalls
1. **Building a feature that is already on** — hand-rolled reaction pickers are the classic. Check the "already on" list first.
2. **Assuming every extension is zero-code** — 10 of them render no affordance and need `CometChat.callExtension()`. Equally, do not write code for the auto-rendered ones.
3. **Declaring a feature absent because `node_modules` has no method for it** — extensions have no named SDK method; they go through the generic `callExtension()`. Check the extension's docs page before saying it is unsupported.
4. **Re-implementing a server-side feature in the browser** — `localStorage`, an in-memory `Map`, or a local `BehaviorSubject` where an extension exists. Saved/pinned messages, reminders and shortcuts are stored **server-side and are per-user across devices**; a browser-local copy does not sync to the user's phone and dies with the cache. If a request is about remembering something *about a message*, check `features.angular-v5.json` before writing storage of your own.
5. **Offering a feature Angular does not have** — E2E encryption, live streaming, email replies.
6. **Forgetting the dashboard step** — the code is right, the feature is off, and it looks broken.
7. **Treating reactions/mentions as extensions** — they are core in v5.

## Verify it works
The feature appears in a real conversation · you wrote no code for a dashboard-only feature · the dashboard toggle is on for the app the credentials point at.

## Explain what you built (REQUIRED close)
Tell the developer what changed, naming the files: the feature you just enabled (and whether it needed a dashboard toggle). Flag anything dev-only as dev-only, and say what you did **not** touch — this is additive.

**Then offer these THREE options as a SELECTABLE choice and WAIT for the pick — never auto-continue (`RULES.md` §19):**
1. **Add another feature** → another grow-set feature from `features.angular-v5.json` that is NEITHER wired NOR already enabled — ASK about dashboard state rather than assuming. **Never offer an `auto` entry** (reactions, mentions, receipts, typing, media) — those are core in v5 and already on.
2. **Customize theming** → `cometchat-angular-v5-customization`.
3. **Test it manually** → do nothing further; hand back so the user runs it.
