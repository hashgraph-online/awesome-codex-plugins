# Inputs, outputs & content projection

Beyond the golden path. Anything not here: fetch the component's docs page (`docs-map.md`) — do not guess.

## The Angular shape
- Props are `@Input()` → template attribute binding: `[user]="selected"`
- Events are `@Output()` → template event binding: `(itemClick)="fn($event)"`. Output names are plain (`itemClick`, `error`, `closeClick`) — there is **no** `cc` prefix; that is the React convention, not Angular's.
- Slots are **content projection** — you pass a `<ng-template>` or project children, not a render-prop function as in React.

## Conversations
```html
<cometchat-conversations
  [activeConversation]="selected"
  (itemClick)="onOpen($event)"
  (error)="onError($event)">
</cometchat-conversations>
```
`activeConversation` is what visually reflects the selected row. Omit it and the list looks stateless even though clicking works — a real defect, not cosmetic.

## Message header / list / composer
All three take the same subject — one of `[user]` or `[group]`, never both:
```html
<cometchat-message-header [user]="selectedUser"></cometchat-message-header>
<cometchat-message-list   [user]="selectedUser"></cometchat-message-list>
<cometchat-message-composer [user]="selectedUser"></cometchat-message-composer>
```
For a group, swap all three to `[group]`. Mixing them across the three components shows one conversation's header above another's messages.

## Thread
```html
<cometchat-thread-header [parentMessage]="threadParent" (closeClick)="threadParent = null"></cometchat-thread-header>
<cometchat-message-list  [user]="selectedUser" [parentMessageId]="threadParent?.getId()"></cometchat-message-list>
```
The reply affordance in a bubble is on by default but inert until you render a thread surface — wire it or hide it, never leave a dead button.

## Users / Groups / Group members
```html
<cometchat-users  (itemClick)="onUser($event)"></cometchat-users>
<cometchat-groups (itemClick)="onGroup($event)"></cometchat-groups>
<cometchat-group-members [group]="activeGroup"></cometchat-group-members>
```
Group members must expose view · kick · ban · banned list · change scope · search to be complete. Change-scope uses `CometChatChangeScopeComponent`; the banned list comes from the SDK.

## Content projection instead of render props
```html
<cometchat-conversations>
  <ng-template #itemView let-conversation>
    <div class="my-row">{{ conversation.getConversationId() }}</div>
  </ng-template>
</cometchat-conversations>
```
Slot names vary per component — confirm on the component's docs page before using one.

## Services for headless control
Some behaviour is reachable without a component, via DI: `ChatStateService` (active chat), `MessageListService`, `ConversationsService`, `SearchMessagesService`, `GroupMembersService`, `ThemeService`. Inject with `inject(ChatStateService)`. Use these for state coordination, not for rebuilding UI the kit already renders.
