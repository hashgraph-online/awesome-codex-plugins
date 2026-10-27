---
name: cometchat-react-native-features
description: "Turn a named CometChat capability on in a React Native app — look it up in the feature oracle, take the right enablement branch (already-on / dashboard extension / AI toggle / npm package / SDK fallback), and wire only what that branch needs. Triggers: enable reactions React Native, add polls RN chat, turn on smart replies RN, add voice video calling RN, enable message translation RN, add stickers RN, enable read receipts, typing indicator React Native, collaborative whiteboard."
license: "MIT"
compatibility: "React Native >=0.77; @cometchat/chat-uikit-react-native ^5.4.0; @cometchat/chat-sdk-react-native ^4.0.28"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "chat cometchat react-native features extensions enablement dashboard ai calls"
---

> **Ground truth:** `features.rn-v5.json` (48 entries) + catalog `rn-v5.json`.
> **The oracle decides, not memory.** Every claim below — whether a capability exists, whether it is
> on by default, which components render it — comes from that file. Fetch props via
> `core/references/docs-map.md`.

## Companion skills (read first)
- `cometchat-react-native-core` — install, provider chain, init→login→render. Assumed, not repeated here.

## Use this skill when
- "enable reactions / polls / translation / stickers" · "turn on smart replies"
- "add voice and video calling" · "is X supported" · "how do I switch on Y"

## Prerequisites & install
None beyond `core` unless the feature's branch says otherwise (only two features install a package).

## Step 1 — look the feature up in the oracle

Find the entry in `features.rn-v5.json`. **If there is no entry, the feature does not exist** — say so
rather than inventing an API. The entry tells you everything:

| Field | What it decides |
|---|---|
| `category` · `enablement` | which branch below to take |
| `ui_components` | what to render (all validated against the catalog) |
| `sdk_fallback` | the SDK methods to use when the kit has **no** component |
| `needs_stitching` | you must wire host state, not just drop a component in |
| `needs_dashboard` | a dashboard toggle is required as well as code |
| `auto_rendered_ui` | **the kit renders it — emit no client code** |
| `platform_delta` | how React Native differs from React here. Read it before writing anything. |
| `docs_gap` | the docs don't cover this yet — flag it, don't silently source-fill |

## Step 2 — take exactly one branch

### A. Already on — `category: default`, `enablement: auto` (12 features)
Nothing to enable. Reactions, mentions, typing indicators, receipts, threads and attachments are
**core messaging in v5**, not extensions.

⚠️ **Do not offer these as "enable this extension".** The dashboard still lists legacy Reactions and
Mentions extensions; their own docs say they are already part of core and scheduled for deprecation.
Suggesting them is a bug, not a helpful extra — it is the exact defect the React pack hit (AUDIT-077).
Customization is via component props, not enablement.

### B. Dashboard extension — `enablement: dashboard-extension` (20 features)
Enable in the CometChat dashboard **first**, then wire any `ui_components`. Polls, stickers,
translation, link preview, whiteboard, document and similar. Without the dashboard step the code
compiles and silently does nothing.

Some are `auto_rendered_ui: true` (e.g. polls' bubble) — the message list renders them once enabled.
**Emit no client code for those**; hand-wiring produces a duplicate.

### C. AI — `category: ai`, `needs_dashboard: true` (4 features)
Two steps, and the second is the one people miss: enable the feature in the dashboard **and** set the
code prop. The props default to **off**, so a dashboard-only change looks like nothing happened.
Smart replies, conversation starter, conversation summary, AI assistant.
Fetch the exact prop name from `/ui-kit/react-native/ai-features.md` — do not guess it.

### D. npm package — `enablement: npm-package` (2 features)
Only calling. React Native needs its **own** calls SDK:

```bash
npm install @cometchat/calls-sdk-react-native@5   # + its 6 pinned peer deps — exact list in cometchat-react-native-calls
cd ios && pod install
```

⚠️ **Not `@cometchat/calls-sdk-javascript`** — that is the web package and will not work.
Its peers include `react-native-webrtc`, a native module: declare camera and microphone permissions
(`NSCameraUsageDescription` / `NSMicrophoneUsageDescription`; `CAMERA` / `RECORD_AUDIO`).
**Simulators cannot capture camera or mic — calling must be verified on a real device.**
Depth lives in `cometchat-react-native-calls`.

### E. SDK fallback — the kit has no component (3 features)
Kit v5 removed the detail and management screens. `sdk_fallback` names the methods:

| Feature | Why | Use |
|---|---|---|
| `group-member-management` | no add/ban/transfer components | `addMembersToGroup` · `banGroupMember` · `unbanGroupMember` · `transferGroupOwnership` · `BannedMembersRequestBuilder` |
| `user-group-details` | no details component | `getUser` · `getGroup` · `updateGroup` |
| `call-log-details` | only the list ships | `CometChatCalls.CallLogRequestBuilder` (**calls** SDK) |

> **Banned members have no UI surface at all.** An app that can ban but cannot view or unban is an
> unclosed round-trip — ship both halves.

Do not invent a layout: cite the official sample app's implementation
(`github.com/cometchat/cometchat-uikit-react-native/tree/v5/examples/SampleApp`). Those are sample-app
**directory paths**, never imports.

## Step 3 — wire only what the branch needs
Render the entry's `ui_components` and nothing else. A feature that is `auto_rendered_ui` gets **no**
client code. A feature that is `needs_stitching` gets host state and callbacks wired, not just a mount.

Never enable a neighbouring feature because it seemed related — that is unrequested scope.

## Known docs gaps (flag, don't silently source-fill)
`reactions` · `typing-indicators` · `delivery-read-receipts` · `media-file-attachments` (the whole
multi-attachment cluster) · and the three SDK-fallback features above carry a `docs_gap` marker.
Build from the catalog and kit source, and **tell the developer the page is missing**.

## Common pitfalls
1. **Offering reactions/mentions as an extension** — they are core in v5; the dashboard entries are legacy.
2. **Dashboard toggled, prop not set** — AI features default to off in code.
3. **Installing the web calls SDK** — RN has its own.
4. **Hand-wiring an `auto_rendered_ui` feature** — duplicate UI.
5. **Assuming a feature exists** — no oracle entry means no feature.
6. **Testing calls on a simulator** — no camera or mic capture.

## Verify it works
- The feature has an entry in `features.rn-v5.json` and you took its branch.
- Every emitted component appears in `catalogs/rn-v5.json`.
- `npm run verify:fences:rn-v5` is green.
- On device: the capability actually appears — a dashboard-gated feature with no code change, or a
  code change with no dashboard step, produces silence rather than an error.
