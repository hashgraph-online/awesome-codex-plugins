# Core surface — the default "add chat" layout

List + message pane, with thread and search as panels. Ships conversations, messages, threaded replies and search. This is the default for an unscoped request; grow to `combined-app.md` only when asked.

## Component
```ts
import { Component, inject, signal, computed, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subject, takeUntil } from 'rxjs';
import { CometChat } from '@cometchat/chat-sdk-javascript';   // Conversation / User / Group types
import {
  ChatStateService, CometChatUIKitConstants,
  CometChatConversationsComponent, CometChatMessageHeaderComponent,
  CometChatMessageListComponent, CometChatMessageComposerComponent,
  CometChatThreadHeaderComponent, CometChatErrorBoundaryComponent,
  CometChatSearchComponent,
} from '@cometchat/chat-uikit-angular';
import type { SearchConversationClickEvent, SearchMessageClickEvent } from '@cometchat/chat-uikit-angular';

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [
    CommonModule,
    CometChatErrorBoundaryComponent,
    CometChatConversationsComponent,
    CometChatMessageHeaderComponent,
    CometChatMessageListComponent,
    CometChatMessageComposerComponent,
    CometChatThreadHeaderComponent,
    CometChatSearchComponent,
  ],
  templateUrl: './chat.component.html',
  styleUrl: './chat.component.css',
})
export class ChatComponent implements OnDestroy {
  private destroy$ = new Subject<void>();
  readonly chatState = inject(ChatStateService);

  // ChatStateService signals are `T | null`; the kit's inputs are OPTIONAL
  // (`user?: CometChat.User`). Binding the raw signal fails Angular's strict
  // template check with "Type 'User | null' is not assignable to 'User | undefined'".
  // Normalise once here rather than writing `?? undefined` at every binding.
  readonly activeUser = computed(() => this.chatState.activeUser() ?? undefined);
  readonly activeGroup = computed(() => this.chatState.activeGroup() ?? undefined);
  readonly activeConversation = computed(() => this.chatState.activeConversation() ?? undefined);
  readonly hasActiveChat = computed(() => !!(this.activeUser() || this.activeGroup()));

  readonly threadParent = signal<any>(null);

  // `(itemClick)` emits a **Conversation**, never a User or a Group. Resolve the subject
  // with getConversationWith() and branch on getConversationType() — a Conversation has
  // no getGuid(), so sniffing for one silently sends every group into the user slot and
  // the header/list/composer throw "getUid is not a function".
  open(conversation: CometChat.Conversation) {
    this.threadParent.set(null);                 // closing context when switching chats
    const subject = conversation.getConversationWith();
    if (conversation.getConversationType() === CometChatUIKitConstants.MessageReceiverType.group) {
      this.chatState.setActiveGroup(subject as CometChat.Group);
    } else {
      this.chatState.setActiveUser(subject as CometChat.User);
    }
  }

  openThread(message: any) { this.threadParent.set(message); }
  closeThread() { this.threadParent.set(null); }
  back() { this.chatState.clearActiveChat(); }

  // Search is part of the core surface, not an extra — `core-chat-surface` contracts
  // both `global-conversation-search` and `in-chat-message-search-default`. It swaps
  // INTO the side column rather than overlaying it, so nothing is covered up.
  readonly searchOpen = signal(false);
  openSearch() { this.searchOpen.set(true); }
  closeSearch() { this.searchOpen.set(false); }

  // A search hit must LAND somewhere — an unwired result list is a dead affordance.
  // Both outputs emit a WRAPPER, not the domain object: `{ conversation, searchKeyword }`
  // and `{ message, searchKeyword }`. Binding them as if they emitted a Conversation is a
  // compile error, and `$event.conversation` is the field you actually want.
  onSearchConversation(e: SearchConversationClickEvent) { this.open(e.conversation); this.closeSearch(); }
  async onSearchMessage(e: SearchMessageClickEvent) {
    // Reuse open() rather than hand-deriving the counterpart: the SDK converts a message
    // back into its Conversation, which works for both 1:1 and group hits.
    const conversation = await CometChat.CometChatHelper.getConversationFromMessage(e.message);
    this.open(conversation);
    this.closeSearch();
  }

  ngOnDestroy() { this.destroy$.next(); this.destroy$.complete(); }
}
```

## Template
```html
<cometchat-error-boundary>
  <div class="cc-shell">
    <aside class="cc-side">
      <ng-container *ngIf="!searchOpen(); else searchPane">
        <!-- Global search is ENTERED from the conversation list's OWN search bar, not a separate
             button stacked above it: [showSearchBar] renders the built-in bar in the Conversations
             header and (searchBarClick) opens the search pane. Do NOT hand-roll a search button. -->
        <cometchat-conversations
          class="cc-fill"
          [showSearchBar]="true"
          [activeConversation]="activeConversation()"
          (searchBarClick)="openSearch()"
          (itemClick)="open($event)">
        </cometchat-conversations>
      </ng-container>
      <ng-template #searchPane>
        <cometchat-search
          class="cc-fill"
          [uid]="activeUser()?.getUid()"
          [guid]="activeGroup()?.getGuid()"
          (conversationClick)="onSearchConversation($event)"
          (messageClick)="onSearchMessage($event)"
          (backClick)="closeSearch()">
        </cometchat-search>
      </ng-template>
    </aside>

    <main class="cc-main" *ngIf="hasActiveChat(); else empty">
      <cometchat-message-header [user]="activeUser()" [group]="activeGroup()"></cometchat-message-header>
      <cometchat-message-list
        class="cc-fill"
        [user]="activeUser()"
        [group]="activeGroup()"
        (threadRepliesClick)="openThread($event)">
      </cometchat-message-list>
      <cometchat-message-composer [user]="activeUser()" [group]="activeGroup()"></cometchat-message-composer>
    </main>
    <ng-template #empty><div class="cc-empty">Select a conversation</div></ng-template>

    <aside class="cc-panel" *ngIf="threadParent()">
      <cometchat-thread-header [parentMessage]="threadParent()" (closeClick)="closeThread()"></cometchat-thread-header>
      <cometchat-message-list
        class="cc-fill"
        [user]="activeUser()"
        [group]="activeGroup()"
        [parentMessageId]="threadParent()?.getId()">
      </cometchat-message-list>
      <cometchat-message-composer
        [user]="activeUser()"
        [group]="activeGroup()"
        [parentMessageId]="threadParent()?.getId()">
      </cometchat-message-composer>
    </aside>
  </div>
</cometchat-error-boundary>
```

## Styles
```css
/* <cometchat-error-boundary> ships NO :host rule (verified vs 5.1.0 — its styles array
   only covers .cometchat-error-boundary__fallback). As the template ROOT it therefore
   sits BETWEEN your sized ancestor and .cc-shell as an auto-height flex item, and a
   `height: 100%` below it resolves against an indefinite height. Size it or the whole
   surface balloons to content height and is clipped by the ancestor's overflow: hidden.
   `height: 100dvh` on .cc-shell below happens to survive this (viewport-relative, so it
   ignores the broken chain) — but the moment this recipe is ROUTED and .cc-shell becomes
   `height: 100%` under a 100dvh outlet, the missing rule silently breaks every pane.
   Field-proven: a real v4→v5 migration made exactly that (correct) routed adaptation and
   measured 4120px of list inside an 827px viewport, unscrollable. */
cometchat-error-boundary { display: flex; flex-direction: column; flex: 1; min-height: 0; overflow: hidden; }

.cc-shell { display: flex; height: 100dvh; width: 100%; min-height: 0; overflow: hidden; }
.cc-side  { width: 320px; min-height: 0; overflow: hidden; display: flex; flex-direction: column; border-right: 1px solid var(--cometchat-border-color-default); }
.cc-main  { flex: 1; display: flex; flex-direction: column; min-height: 0; overflow: hidden; }
.cc-panel { width: 360px; min-height: 0; overflow: hidden; display: flex; flex-direction: column; border-left: 1px solid var(--cometchat-border-color-default); }

/* The thread panel needs its own background so it reads as a distinct surface. Unlike
   React — where the message list paints an OPAQUE token and a wrapper background never
   shows (AUDIT-020/024) — Angular's `--cometchat-message-list-background` defaults to
   **transparent** (verified in the shipped kit), so the wrapper's own background shows
   through and is all you need. Do NOT copy React's `--cometchat-message-list-bg`
   override: that token does not exist in this kit and the rule silently does nothing. */
.cc-panel { background: var(--cometchat-background-color-01); }
.cc-empty { flex: 1; display: grid; place-items: center; color: var(--cometchat-text-color-secondary); }

/* Every cometchat-conversations / -users / -groups / -call-logs / -search / -message-list
   host resolves an internal `height: 100%` down to its OWN scroll region
   (.cometchat-paginated-list { overflow-y: auto }) — it does not size itself. Left
   unsized inside a flex column it defaults to min-height: auto (refuses to shrink below
   its content), so the list balloons past the shell and gets hard-clipped by .cc-side's
   overflow: hidden instead of scrolling. flex: 1 gives it the column's remaining space;
   min-height: 0 lets it actually shrink to that space so overflow-y: auto can engage. */
.cc-fill { flex: 1; min-height: 0; overflow: hidden; }

@media (max-width: 768px) {
  .cc-shell { flex-direction: column; }
  .cc-side, .cc-panel { width: 100%; }
}
```
`html, body { height: 100%; margin: 0; }` in `styles.css` is required.

## Notes
- `[user]` and `[group]` are both bound and one is always undefined — the components accept that and it avoids branching the template twice. What they do **not** accept is the wrong kind in either slot: a `Group` in `[user]` throws `getUid is not a function`, which is why `open()` branches on `getConversationType()` rather than duck-typing the emitted object.
- Switching conversation clears the open thread; leaving it open would show a thread from the previous chat.
- Search is wired above, swapped into `.cc-side` behind a toggle — never overlaid. Binding `[uid]`/`[guid]` scopes it to the open chat (`in-chat-message-search-default`); with neither bound it searches everything (`global-conversation-search`). Both outputs are handled: an unwired result list is a dead affordance (`RULES.md` §12).
