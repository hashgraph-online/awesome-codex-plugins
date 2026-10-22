---
name: cometchat-angular-v5-placement
description: "Where CometChat components go in an Angular app — the chat shell layout, thread and details panels, search, routing a chat page, and the mobile one-pane fallback. Triggers: 'add a chat page', 'put chat in my dashboard', 'conversation list beside messages', 'open a thread panel', 'chat route', 'make chat responsive'."
license: "MIT"
compatibility: "@cometchat/chat-uikit-angular ^5 (5.1.0–5.2.0 verified); Angular 17-21"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat angular placement v5 layout routing panels responsive shell"
---

> **Ground truth:** `@cometchat/chat-uikit-angular@5` (5.1.0–5.2.0 verified). Uses only components in the `angular-v5` catalog. The layouts here are built FROM the live task guides — `{DOCS_BASE}/ui-kit/angular/guides/new-chat.md`, `/guides/group-chat.md`, `/guides/threaded-messages.md`, `/guides/search-messages.md`, plus `/angular-conversation`, `/angular-one-to-one-chat`, `/angular-tab-based-chat` and `/api-reference/chat-state-service.md`; base + paths in `cometchat-angular-v5-core/references/docs-map.md`. Fetch layout-specific inputs from the component's `.md` twin rather than reading the installed bundle. **APPEND to the user's app — additive only** (`RULES.md`).

## Companion skills (read first)
- `cometchat-angular-v5-core` — install, credentials, `init→login→render`, and `references/layout.md` for the sizing rules this skill assumes.
- `cometchat-angular-v5-components` — which component to use and its real inputs/outputs.

## Use this skill when
Deciding **where** chat lives: a dedicated route, a panel inside an existing dashboard, a widget, or the full multi-pane app.

## Pick a placement
| Ask | Placement | Recipe |
| --- | --- | --- |
| "add chat to my app" (unscoped) | **Core surface** — list + message pane, thread and search as panels | `references/core-surface.md` |
| "the whole chat app" — users, groups, calls, details | **Combined app** — tabbed selector + panels | `references/combined-app.md` |
| "chat inside my dashboard" | Embed the core surface in an existing layout slot | below |
| "a support widget" | Single conversation — header + list + composer, no list pane | below |

Default to the **core surface** for an unscoped request. Grow to the combined app only when asked.

## Active item — use ChatStateService, not your own field
Angular ships an injectable source of truth for the active chat. It exposes **signals** and **observables**; prefer signals in templates. This is what satisfies "the selected row is visually reflected" and makes panel-close round-trip correctly.

```ts
import { Component, computed, inject } from '@angular/core';
import { CometChat } from '@cometchat/chat-sdk-javascript';
import { ChatStateService, CometChatUIKitConstants } from '@cometchat/chat-uikit-angular';

@Component({ selector: 'app-chat-shell', standalone: true, template: '' })
export class ChatShellComponent {
  readonly chatState = inject(ChatStateService);
  // The service's signals are `T | null`, but the kit's inputs are optional
  // (`T | undefined`) — bind the raw signal and Angular's strict template check
  // rejects it. Normalise once, here.
  readonly activeUser = computed(() => this.chatState.activeUser() ?? undefined);
  readonly activeGroup = computed(() => this.chatState.activeGroup() ?? undefined);

  // (itemClick) emits a Conversation — resolve the subject, then branch on its TYPE.
  // A Conversation has no getGuid(), so duck-typing routes groups into the user slot
  // and the message pane throws "getUid is not a function". See references/core-surface.md.
  open(conversation: CometChat.Conversation) {
    const subject = conversation.getConversationWith();
    if (conversation.getConversationType() === CometChatUIKitConstants.MessageReceiverType.group) {
      this.chatState.setActiveGroup(subject as CometChat.Group);
    } else {
      this.chatState.setActiveUser(subject as CometChat.User);
    }
  }
  closeChat() { this.chatState.clearActiveChat(); }
}
```
Available: `activeUser` `activeGroup` `activeConversation` (signals) · `activeUser$` `activeGroup$` `activeConversation$` (observables) · `setActiveUser/Group/Conversation` · `getActiveChatEntity()` · `clearActiveChat()`.

Keeping a separate `selected` field alongside this is how the two drift and the list stops highlighting the open conversation.

## Panels are columns, not overlays
Thread, user/group details and search are **additional columns in the same flex shell**. Opening one must not resize or remount the message list, and closing must return to the exact prior layout.

```html
<div class="cc-shell">
  <aside class="cc-side"><!-- list --></aside>
  <main class="cc-main"><!-- header · list · composer --></main>
  <aside class="cc-panel" *ngIf="threadParent()"><!-- thread --></aside>
</div>
```
```css
.cc-shell { display: flex; height: 100dvh; width: 100%; min-height: 0; overflow: hidden; }
.cc-side  { width: 320px; min-height: 0; overflow: hidden; }
.cc-main  { flex: 1; display: flex; flex-direction: column; min-height: 0; overflow: hidden; }
.cc-panel { width: 360px; min-height: 0; overflow: hidden; border-left: 1px solid var(--cometchat-border-color-default); }
```
`min-height: 0` on every column is required — see core's `references/layout.md`.

## Routing a chat page
```ts
// app.routes.ts
import { Routes } from '@angular/router';
export const routes: Routes = [
  { path: 'chat', loadComponent: () => import('./chat/chat.component').then(m => m.ChatComponent) },
  { path: 'chat/:uid', loadComponent: () => import('./chat/chat.component').then(m => m.ChatComponent) },
];
```
Two rules:
1. **Do not re-init CometChat per route.** Init happens once at bootstrap (core). A route guard may await login, never re-init.
2. **Tear down on leave.** Every subscription in the chat component needs `takeUntil(destroy$)` in `ngOnDestroy`, or navigating away leaks listeners that keep firing.

Reading `:uid` into the active chat belongs in the component's `ngOnInit`, resolved through `ChatStateService`.

## Embedding in an existing dashboard
Give the host slot a resolved height and let the shell fill it — do **not** put the kit inside a container sized by its content.
```css
.dashboard-chat-slot { height: calc(100dvh - var(--app-header-height)); min-height: 0; display: flex; }
```
If the surrounding app uses `transform` or `filter` on an ancestor, the height chain breaks — core's `layout.md` covers why.

## Mobile — one pane at a time (mandatory for any multi-pane layout)
Below ~768px show the list **or** the conversation, never both.
```html
<div class="cc-shell">
  <aside class="cc-side" [hidden]="isMobile() && hasActiveChat()"><!-- list --></aside>
  <main class="cc-main" [hidden]="isMobile() && !hasActiveChat()"><!-- message pane --></main>
</div>
```
Drive `[hidden]` from the same `ChatStateService` state as the message components, and give the mobile conversation view a back control that calls `clearActiveChat()`. A multi-pane layout squeezed onto a phone is a defect, not a style choice.

## Common pitfalls
1. **Two sources of truth** — a local `selected` field plus `ChatStateService`. They drift; the list stops highlighting.
2. **Panels as overlays** — thread rendered over the list instead of beside it, so closing does not restore layout.
3. **Re-initialising per route** — init belongs at bootstrap, once.
4. **No teardown on navigate** — leaked listeners keep firing against a destroyed view.
5. **Unsized embed slot** — the kit collapses to zero height inside a content-sized container.
6. **Both panes on mobile** — unusable at 375px.

## Verify it works
Clicking a conversation opens it AND highlights the row · opening a thread does not resize the message list · closing returns to the exact prior layout · navigating away and back does not duplicate messages · at 375px only one pane is visible with a working back control · no console errors.

## Explain what you built (REQUIRED close)
Tell the developer what changed, naming the files: the layout you built — which panes exist, and how the mobile one-pane fallback behaves. Flag anything dev-only as dev-only, and say what you did **not** touch — this is additive.

**Then offer these THREE options as a SELECTABLE choice and WAIT for the pick — never auto-continue (`RULES.md` §19):**
1. **Add another feature** → a feature from `features.angular-v5.json`, or growing the surface — users/groups tabs, a details panel, calling. **Never offer an `auto` entry** (reactions, mentions, receipts, typing, media) — those are core in v5 and already on.
2. **Customize theming** → `cometchat-angular-v5-customization`.
3. **Test it manually** → do nothing further; hand back so the user runs it.
