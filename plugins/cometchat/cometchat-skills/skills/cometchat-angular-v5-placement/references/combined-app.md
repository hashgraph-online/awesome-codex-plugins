# Combined app — the grow target

Load this only when the user asks for the whole chat application: a tabbed selector (chats · users · groups · calls), the message pane, and details/thread panels.

Built on `core-surface.md` — the shell, `ChatStateService` wiring, teardown and responsive rules are identical. This adds the tab selector and the details panel.

> **Carry the whole core surface over, not just the shell.** `chat-experience`'s contract is a SUPERSET of `core-chat-surface`, so everything core-surface.md wires comes too — including **search** (`side-panel-or-column-search`: the toggle + `<cometchat-search>` in the list column) and the **thread panel**. Dropping search because this file does not repeat it is the easy mistake: this file shows only the DELTA.

## Tabs
```ts
type Tab = 'chats' | 'users' | 'groups' | 'calls';

export class ChatAppComponent {
  readonly tab = signal<Tab>('chats');
  readonly showDetails = signal(false);

  // THREE handlers, not one. `(itemClick)` emits a different type per list:
  //   cometchat-conversations → Conversation   (needs discriminating — see core-surface.md open())
  //   cometchat-users         → User
  //   cometchat-groups        → Group
  // Routing users/groups through open() fails the build:
  //   TS2345: Argument of type 'User' is not assignable to parameter of type 'Conversation'.
  openUser(user: CometChat.User) { this.chatState.setActiveUser(user); }
  openGroup(group: CometChat.Group) { this.chatState.setActiveGroup(group); }
}
```
```html
<aside class="cc-side">
  <nav class="cc-tabs">
    <button (click)="tab.set('chats')"  [class.active]="tab() === 'chats'">Chats</button>
    <button (click)="tab.set('users')"  [class.active]="tab() === 'users'">Users</button>
    <button (click)="tab.set('groups')" [class.active]="tab() === 'groups'">Groups</button>
    <button (click)="tab.set('calls')"  [class.active]="tab() === 'calls'">Calls</button>
  </nav>

  <cometchat-conversations class="cc-fill" *ngIf="tab() === 'chats'"  (itemClick)="open($event)"></cometchat-conversations>
  <cometchat-users         class="cc-fill" *ngIf="tab() === 'users'"  (itemClick)="openUser($event)"></cometchat-users>
  <cometchat-groups        class="cc-fill" *ngIf="tab() === 'groups'" (itemClick)="openGroup($event)"></cometchat-groups>
  <!-- Wire the calls tab too, or clicking a log dead-ends (RULES.md wire-or-hide). -->
  <!-- ⚠️ GATE the call-logs surface on callsReady(): the kit's call-logs component NPEs
       ("Cannot read properties of null (reading 'CallLogRequestBuilder')") if it mounts before
       the lazily-loaded Calls SDK populates CometChatUIKitCalls — its ngOnInit touches the builder
       synchronously, and Retry does not recover. callsReady() awaits CometChatUIKit.callingReady
       AND null-checks CometChatUIKitCalls (see cometchat-angular-v5-calls § Call history).
       STOPGAP until the kit component awaits readiness itself. -->
  <ng-container *ngIf="tab() === 'calls'">
    <cometchat-call-logs class="cc-fill" *ngIf="callsReady(); else callsLoading" (itemClick)="openCallLog($event)"></cometchat-call-logs>
    <ng-template #callsLoading><div class="cc-empty">Loading call history…</div></ng-template>
  </ng-container>
</aside>
```
```css
/* .cc-side is already display:flex;flex-direction:column from core-surface.md. The tab
   nav must not be squeezed, and whichever list is showing must be the ONE flex child
   that fills the rest — see .cc-fill's comment in core-surface.md for why this is
   required, not cosmetic: without it the list can't scroll, it gets clipped. */
.cc-tabs { flex-shrink: 0; }
```
The tab nav is yours — the kit ships no tab component. Every kit component used above must
be in this component's `imports: []`, or it renders **nothing, silently**:

```ts
import { Component, inject, signal, computed } from '@angular/core';
import { CometChat } from '@cometchat/chat-sdk-javascript';
import { CommonModule } from '@angular/common';
import {
  ChatStateService,
  CometChatUIKit,
  CometChatUIKitCalls,
  CometChatConversationsComponent,
  CometChatUsersComponent,
  CometChatGroupsComponent,
  CometChatCallLogsComponent,
  CometChatGroupMembersComponent,
  CometChatIncomingCallComponent,
} from '@cometchat/chat-uikit-angular';

@Component({
  selector: 'app-chat-tabs',
  standalone: true,
  imports: [                      // ← omit any of these and that tab renders blank
    CommonModule,
    CometChatConversationsComponent,
    CometChatUsersComponent,
    CometChatGroupsComponent,
    CometChatCallLogsComponent,
    // The Details panel and Incoming calls sections below use these two. Omitting them is
    // NG8001 ("not a known element") plus NG8002 on [group] — this file's own #1 pitfall.
    CometChatGroupMembersComponent,
    CometChatIncomingCallComponent,
  ],
  templateUrl: './chat-tabs.component.html',
})
export class ChatTabsComponent {
  private readonly chatState = inject(ChatStateService);
  readonly tab = signal<'chats' | 'users' | 'groups' | 'calls'>('chats');

  // The template below binds these — declare them here or the build fails TS2339.
  readonly activeUser = computed(() => this.chatState.activeUser() ?? undefined);
  readonly activeGroup = computed(() => this.chatState.activeGroup() ?? undefined);
  readonly activeConversation = computed(() => this.chatState.activeConversation() ?? undefined);
  readonly showDetails = signal(false);
  readonly threadParent = signal<any>(null);

  // Gate the call-logs tab: <cometchat-call-logs> NPEs if it mounts before the lazily-loaded
  // Calls SDK populates CometChatUIKitCalls. callingReady ALONE is not enough (it defaults to a
  // pre-resolved Promise and the namespace can still be null) — also null-check CometChatUIKitCalls.
  // STOPGAP (AUDIT-163, proven live).
  readonly callsReady = signal(false);
  constructor() {
    CometChatUIKit.callingReady
      .then(() => this.callsReady.set(!!CometChatUIKitCalls))
      .catch(() => this.callsReady.set(false));
  }

  open(conversation: CometChat.Conversation) { /* see core-surface.md open() */ }
  openUser(user: CometChat.User) { this.chatState.setActiveUser(user); }
  openGroup(group: CometChat.Group) { this.chatState.setActiveGroup(group); }
  openCallLog(_log: any) { /* render your own detail pane — v5 ships none */ }
  openDetails() { this.threadParent.set(null); this.showDetails.set(true); }
  closeDetails() { this.showDetails.set(false); }
  closeThread() { this.threadParent.set(null); }
  openThread(m: any) { this.showDetails.set(false); this.threadParent.set(m); }
}
```

## Details panel
There is no single "details" component. Compose it: your own header plus `<cometchat-group-members>` for a group.
```html
<!-- The OPENER: the message header's own (itemClick) — clicking the avatar/name area.
     Without it openDetails() is never called and the panel is unreachable. -->
<cometchat-message-header
  [user]="activeUser()" [group]="activeGroup()"
  (itemClick)="openDetails()">
</cometchat-message-header>

<aside class="cc-panel" *ngIf="showDetails()">
  <header class="cc-panel-head">
    <span>{{ activeGroup()?.getName() ?? activeUser()?.getName() }}</span>
    <button (click)="showDetails.set(false)">Close</button>
  </header>
  <!-- `[group]` is REQUIRED (Group, not Group | undefined). `*ngIf="activeGroup()"` guards at
       runtime but does NOT narrow the type: activeGroup() is a signal CALL, and Angular's
       strict template checker cannot narrow a call expression across the binding. Written the
       obvious way it fails the build with
         TS2322: Type 'Group | undefined' is not assignable to type 'Group'.
       Bind the `as` alias instead — that narrows, and the *ngIf still guards. -->
  <ng-container *ngIf="activeGroup() as group">
    <cometchat-group-members class="cc-fill" [group]="group"></cometchat-group-members>
  </ng-container>
</aside>
```
Banned members and create-group have no component — see `cometchat-angular-v5-components/references/host-composed.md`.

## Incoming calls
Mount the listener **once at app root**, not inside the chat page, or it stops working the moment the user navigates away.
```html
<!-- app.component.html -->
<cometchat-incoming-call></cometchat-incoming-call>
<router-outlet></router-outlet>
```

## Panel arbitration
Thread and details compete for the same column. Decide explicitly — opening one should close the other:
```ts
openThread(m: any) { this.showDetails.set(false); this.threadParent.set(m); }
openDetails()      { this.threadParent.set(null);  this.showDetails.set(true); }
// Call logs: v5 ships no detail component — render your own pane (cometchat-angular-v5-calls).
openCallLog(log: any) { this.selectedCallLog.set(log); }
```
Two panels open at once on a 1280px screen leaves the message pane unusably narrow.

## Verify
Every tab renders its list · switching tabs keeps the open conversation · details and thread never both open · incoming calls ring from any route · one pane on mobile.
