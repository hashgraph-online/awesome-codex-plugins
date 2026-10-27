---
name: cometchat-angular-v5-components
description: "Choose, compose and customize CometChat Angular UI Kit components — the closed component list, real @Input/@Output names, view-slot overrides via ng-template, and the surfaces that have NO kit component and must be host-composed. Triggers: 'which components exist', 'customize the conversation list', 'custom message bubble', 'create a group', 'show banned members', 'swap the list item'."
license: "MIT"
compatibility: "@cometchat/chat-uikit-angular ^5 (5.1.0–5.2.0 verified); Angular 17-21"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat angular components uikit v5 slots content-projection customization"
---

> **Ground truth:** the existence oracle is the `angular-v5` catalog (`references/catalog.md`, generated from the installed 5.1.0 kit). Not listed = not importable. Exact inputs/outputs/view slots are FETCHED from each component's `.md` twin via `cometchat-angular-v5-core/references/docs-map.md` — every page opens with an **AI Integration Quick Reference**; read that first. Never answer an input or output from memory or from the type declarations.

## Companion skills (read first)
- `cometchat-angular-v5-core` — install, credentials, `init→login→render`, the golden-path surface. This skill ASSUMES it and never restates it.

## Use this skill when
Picking which component to use, overriding part of one, or discovering that the thing asked for has no component at all.

## Naming — three different strings per component
`CometChatConversationsComponent` (import) · `<cometchat-conversations>` (template) · "Conversations" (docs title). The bare `CometChatConversations` is **internal-only and not importable** — 109 such names exist. The AI-assistant exports are the sole suffix exception (`CometChatAIAssistantChat`).

## Output names carry NO prefix
Angular outputs are plain: `itemClick`, `select`, `error`, `closeClick`, `selectionChange`. There is **no** `cc` prefix — that is React's convention. Binding `(ccConversationClicked)` silently never fires.
> ⚠️ An output that does not exist fails the SAME silent way — Angular treats an unknown event on a component as a plain DOM listener, so `(closeClick)` on `<cometchat-message-header>` compiles clean and never fires. `closeClick` is real on `<cometchat-thread-header>` but NOT on the message header (verified vs compiled 5.1.0). Use `backClick` there.

| Component | Outputs |
| --- | --- |
| `<cometchat-conversations>` | `itemClick` `select` `error` `searchBarClick` `contextMenuOpen` `contextMenuClose` `scrollToTop` `scrollToBottom` `selectionChange` |
| `<cometchat-users>` | `itemClick` `select` `error` `empty` `selectionChange` |
| `<cometchat-groups>` | `itemClick` `select` `error` `selectionChange` |
| `<cometchat-group-members>` | `itemClick` `error` `empty` `selectionChange` |
| `<cometchat-message-list>` | `threadRepliesClick` `reactionClick` `reactionListItemClick` `smartReplyClick` `conversationStarterClick` `messagePrivatelyClick` `replyClick` `error` |
| `<cometchat-message-composer>` | `sendButtonClick` `textChange` `attachmentAdded` `attachmentRemoved` `mentionSelected` `closePreview` `error` |
| `<cometchat-message-header>` | `backClick` `itemClick` `searchClick` `voiceCallClick` `videoCallClick` `conversationSummaryClick` `error` |
| `<cometchat-thread-header>` | `closeClick` `backClick` |
| `<cometchat-search>` | `backClick` `conversationClick` `messageClick` `searchError` |

Anything not listed: fetch the component's docs page (`cometchat-angular-v5-core/references/docs-map.md`). Do not guess an output name.

## Component catalog (BAKED closed list)
Full per-component inputs live in the docs — this is the "which one do I reach for" map. Complete list: `references/catalog.md`.

**Lists** `<cometchat-conversations>` · `<cometchat-users>` · `<cometchat-groups>` · `<cometchat-group-members>`
**Message pane** `<cometchat-message-header>` · `<cometchat-message-list>` · `<cometchat-message-composer>` · `<cometchat-thread-header>`
**Bubbles** text · image · video · audio · file · card · poll · sticker · action · delete · call · collaborative-document · collaborative-whiteboard *(all rendered BY the message list — see below)*
**Calls** `<cometchat-call-buttons>` · `<cometchat-incoming-call>` · `<cometchat-outgoing-call>` · `<cometchat-ongoing-call>` · `<cometchat-call-logs>`
**Search** `<cometchat-search>` · `<cometchat-search-bar>` · `<cometchat-search-conversations-list>` · `<cometchat-search-messages-list>`
**AI** `CometChatAIAssistantChat` · `<cometchat-smart-replies>` · `<cometchat-conversation-starter>` · `<cometchat-conversation-summary>`
**Reactions** `<cometchat-reactions>` · `<cometchat-reaction-list>` · `<cometchat-reaction-info>` · `<cometchat-emoji-keyboard>`
**Support** `<cometchat-error-boundary>` · `<cometchat-notification-feed>` · `<cometchat-notification-badge>` · `<cometchat-change-scope>` · `<cometchat-flag-message-dialog>` · `<cometchat-media-recorder>`

## Do NOT hand-roll what the list already renders
Message bubbles, receipts, reaction pickers, typing indicators, attachment previews and the context menu are rendered **by** `<cometchat-message-list>` when the corresponding feature is on. Rebuilding them by hand loses realtime updates and every future fix. If an affordance looks broken it is nearly always a missing `@Input()` or an unsized container, not a missing component. **`<cometchat-conversations>` / `-users` / `-groups` / `-call-logs` / `-search` / `-message-list` specifically all rely on an internal `height: 100%` down to their own scroll region — none sizes itself.** Placed in a flex column without `flex: 1; min-height: 0` (the `.cc-fill` class, `cometchat-angular-v5-placement/references/core-surface.md`), a list doesn't scroll: it grows past its container and gets silently clipped.

## Building your OWN chrome? The kit exports the atoms too
The rule above covers what `<cometchat-message-list>` renders for you. A second case is your own UI — a signed-in user bar, a profile header, a custom row — where the kit still ships the piece you are about to rebuild:

| Atom | Selector | Use it for |
| --- | --- | --- |
| `CometChatAvatarComponent` | `<cometchat-avatar>` | any user/group avatar — `[image]`, `[name]`, `[loading]` |
| `CometChatListItemComponent` | `<cometchat-list-item>` | a row with avatar + title + trailing content |
| `CometChatButtonComponent` | `<cometchat-button>` | an action button that matches kit styling |
| `CometChatDateComponent` | `<cometchat-date>` | a timestamp with the kit's formatting |
| `CometChatPopoverComponent` | `<cometchat-popover>` | anchored menus/pickers |

```html
<!-- ✅ themed, falls back to initials when there is no picture, follows light/dark -->
<cometchat-avatar [image]="user?.getAvatar()" [name]="user?.getName()"></cometchat-avatar>

<!-- ❌ hand-rolled: needs your own fallback URL, ignores the theme, drifts from the kit -->
<img [src]="user?.getAvatar() || 'https://…/astronaut.png'" class="my-avatar" />
```

A hand-rolled `<img>` is the common one. It forces you to invent a placeholder, it does not render initials when the user has no picture, and it ignores every avatar token in the theme. **Before styling a presentational element yourself, check this table** — and remember these are standalone components, so each one you use goes in the consuming component's `imports: []`.

## Customizing part of a component — view slots
Override a region with a `<ng-template>` bound to a `*View` input. This is Angular's content projection; it replaces React's render props.

```ts
import { Component, ViewChild, TemplateRef } from '@angular/core';
import { CometChatConversationsComponent } from '@cometchat/chat-uikit-angular';

@Component({
  selector: 'app-convo-list',
  standalone: true,
  imports: [CometChatConversationsComponent],
  templateUrl: './convo-list.component.html',
})
export class ConvoListComponent {
  @ViewChild('customItem', { static: true }) customItem!: TemplateRef<unknown>;

  // A trigger must have a handler in the SAME class, or the template fails to compile
  // (TS2339). `(itemClick)` emits a Conversation — discriminate it before binding the
  // subject to [user] or [group] (see cometchat-angular-v5-placement).
  open(conversation: CometChat.Conversation) { /* select the conversation */ }
}
```
```html
<ng-template #customItem let-conversation>
  <div class="my-row">{{ conversation?.getConversationId() }}</div>
</ng-template>

<cometchat-conversations [itemView]="customItem" (itemClick)="open($event)"></cometchat-conversations>
```

Slots available per component (verified against the kit):

| Component | View slots |
| --- | --- |
| conversations · users · groups | `headerView` `menuView` `loadingView` `emptyView` `errorView` `itemView` `leadingView` `titleView` `subtitleView` `trailingView` (+ `searchView` on conversations) |
| message-header | `headerView` `itemView` `leadingView` `titleView` `subtitleView` `trailingView` `backButtonView` `auxiliaryButtonView` |
| message-list | `headerView` `footerView` `emptyView` `errorView` `loadingView` `bubbleFooterView` `appendView` |

Override the smallest slot that does the job — replacing `itemView` when you only wanted a different subtitle loses selection, presence and receipts.

## Surfaces with NO kit component (host-composed)
Requested often, and there is nothing to import. Build these yourself against the SDK — see `references/host-composed.md`.
- **Create a group** — no component. Offer all three types: public, private, **and password-protected**.
- **Banned members** — no component; `<cometchat-group-members>` covers view/kick/ban/scope but the banned LIST comes from the SDK.
- **Login / user picker** — no component; app-owned.

## Common pitfalls
1. Component not in `imports: []` → renders nothing, silently. Every component, every consuming component.
2. Guessing an output name (`ccItemClicked`) → binding never fires and Angular does not warn.
3. Replacing `itemView` for a cosmetic tweak → loses built-in selection/presence/receipts.
4. Mixing `[user]` and `[group]` across header/list/composer → one conversation's header over another's messages.
5. Hand-rolling bubbles → loses realtime updates.

## Verify it works
The overridden region renders your template · the rest of the component is unchanged · clicks still fire · realtime updates still arrive · nothing collapsed to zero height.
