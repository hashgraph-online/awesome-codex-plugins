# Custom message types

Angular v5 has **no plugin architecture** — `CometChatMessagePlugin` / `CometChatPluginRegistry` are React v7 symbols and do not exist here. A custom type is three separate concerns: send it, make the list fetch it, render it.

## 1. Send — plain SDK
```ts
import { CometChat } from '@cometchat/chat-sdk-javascript';

async function sendOrderUpdate(receiverId: string) {
  const msg = new CometChat.CustomMessage(
    receiverId,
    CometChat.RECEIVER_TYPE.USER,
    'order_update',                       // your type key
    { orderId: 42, status: 'shipped' },
  );
  await CometChat.sendCustomMessage(msg);
}
```

> ⚠️ **The sender will not see this message until they refresh — unless you publish it.** `<cometchat-message-list>`/`<cometchat-conversations>` render from an internal store that `<cometchat-message-composer>` updates for you on every normal send. A raw SDK call bypasses the composer entirely, so nothing tells the currently-mounted list a message now exists — the SDK real-time listener that would otherwise deliver it does **not** echo a message back to its own sender. This is not specific to custom types: **any message sent by calling the SDK directly instead of through the composer needs this**, including the plain-text reply from a host-composed extension's affordance (`references/host-composed-extensions.md`) or from `custom-messages.md`'s own update path below.
>
> Publish it through the kit's own event bus so its list picks it up exactly as if the composer had sent it — verified against the installed 5.1.0 kit: `publishMessageSent(data: IMessages)`, where `IMessages = { message: CometChat.BaseMessage; status: MessageStatus; parentMessageId?: number | null }`. Pass the object, not the bare message — a bare message silently fails the shape the list expects. `CometChatMessageEvents.ccMessageSent` (a raw `Subject`) is the same underlying event but is `@deprecated` in favour of this typed method — do not `.next()` it directly in new code.

```ts
import { CometChatMessageEvents, MessageStatus } from '@cometchat/chat-uikit-angular';

function announceSent(msg: CometChat.BaseMessage) {
  CometChatMessageEvents.publishMessageSent({ message: msg, status: MessageStatus.success });
}
```

## 2. Make the list FETCH it
`<cometchat-message-list>` fetches only the default types unless told otherwise. Your custom type is silently absent until you widen the request — this is the step people miss.

The kit exports the defaults so you extend rather than replace them:
```ts
import { CometChat } from '@cometchat/chat-sdk-javascript';
import { DEFAULT_MESSAGE_TYPES, DEFAULT_MESSAGE_CATEGORIES } from '@cometchat/chat-uikit-angular';

class ChatComponent {
  readonly messagesRequestBuilder = new CometChat.MessagesRequestBuilder()
    .setTypes([...DEFAULT_MESSAGE_TYPES, 'order_update'])
    .setCategories([...DEFAULT_MESSAGE_CATEGORIES, CometChat.CATEGORY_CUSTOM])
    .setLimit(30);
}
```
```html
<cometchat-message-list [user]="activeUser()" [messagesRequestBuilder]="messagesRequestBuilder"></cometchat-message-list>
```
Both constants are `readonly string[]`. Spreading them keeps every built-in type working — hardcoding a list instead is how text messages disappear.

## 3. Render it — `MessageBubbleConfigService.setBubbleView()`
Register a template against your type key. This is the documented API — do **not** reach for `[listItemTemplate]`, and do not reverse-engineer the bubble internals.

> ⚠️ **The key is `{type}_{category}` — NOT your bare type.** A custom `location` message registers under **`location_custom`**, because its category is `custom`. This trips everyone: `setBubbleView('location', …)` is accepted silently, never matches, and the bubble renders the kit's fallback **"This message type is not supported."** — which reads like a missing feature rather than a key typo. Built-in keys follow the same rule (`text_message`, `image_message`). Verified against the kit: `type MessageTypeKey` — *"Format: `{type}_{category}`"*.

```ts
import { Component, ViewChild, TemplateRef, inject, AfterViewInit } from '@angular/core';
import { MessageBubbleConfigService } from '@cometchat/chat-uikit-angular';

@Component({ /* … */ })
export class ChatComponent implements AfterViewInit {
  @ViewChild('locationBubble', { static: true }) locationBubble!: TemplateRef<unknown>;
  private bubbleConfig = inject(MessageBubbleConfigService);

  ngAfterViewInit() {
    this.bubbleConfig.setBubbleView('location_custom', { contentView: this.locationBubble });
  }
}
```
```html
<ng-template #locationBubble let-message>
  <div class="location-card">{{ message?.getCustomData()?.label }}</div>
</ng-template>
```

**Register only the parts you want to change; unregistered parts keep their defaults:**

| Slot | Replaces |
| --- | --- |
| `contentView` | the message content — the usual choice for a custom type |
| `bubbleView` | the entire bubble, losing the built-in frame |
| `headerView` · `footerView` · `statusInfoView` | partial overrides around the content |

Prefer `contentView`: replacing `bubbleView` discards timestamps, receipts, reactions and thread affordances that the default frame provides.

Full guide, including the type-key rules: `{DOCS_BASE}/ui-kit/angular/guides/custom-message-types.md`.

## 4. Updating a custom message after it was sent — location sharing, live status
Some custom types change after sending — a live location marker that moves, a poll-style status that ticks over. Do **not** reach for `sendTransientMessage()` for this: transient messages are explicitly *"not saved or tracked anywhere"* and only reach a receiver who is online at that instant (verified against `{SDK_DOCS_BASE}/sdk/javascript/transient-messages.md`) — a location share sent this way vanishes from chat history and never reaches an offline recipient. That is wrong for anything that must persist as a message.

**The documented mechanism is `CometChat.editMessage()`** — it accepts a `TextMessage` **or a `CustomMessage`** (`{SDK_DOCS_BASE}/sdk/javascript/edit-message.md`):
```ts
import { CometChat } from '@cometchat/chat-sdk-javascript';

async function updateLocation(message: CometChat.CustomMessage, lat: number, lng: number) {
  message.setCustomData({ ...message.getCustomData(), lat, lng });
  await CometChat.editMessage(message);   // returns the updated BaseMessage
}
```
Keep the `CustomMessage` instance you sent (or re-fetch it with `CometChat.getMessageDetails(id)`); do not construct a fresh message for an update — `editMessage` mutates the existing one in place, it does not create a new bubble.

**`editMessage()` is also a raw SDK call — the EDITOR needs the same local-echo publish as §1's send.** Without it, the person who moved the location marker will not see their own update until they refresh, even though the SDK call succeeded:
```ts
import { CometChat } from '@cometchat/chat-sdk-javascript';
import { CometChatMessageEvents, MessageStatus } from '@cometchat/chat-uikit-angular';

async function publishLocalEdit(updated: CometChat.BaseMessage) {
  CometChatMessageEvents.publishMessageEdited({ message: updated, status: MessageStatus.success });
}
```

**The receiver needs a listener, not a poll** — register `onMessageEdited` alongside your other SDK listeners (same `listenerId`/`ngOnDestroy`/repaint conventions as `cometchat-angular-v5-core/references/lifecycle.md`). Angular v21 is **zoneless by default**, so repaint by writing a **signal** (not `NgZone.run()`, which no longer triggers CD):
```ts
import { CometChat } from '@cometchat/chat-sdk-javascript';
import { WritableSignal } from '@angular/core';

function registerEditListener(messages: WritableSignal<CometChat.BaseMessage[]>, listenerId: string) {
  CometChat.addMessageListener(listenerId, {
    onMessageEdited: (message: CometChat.BaseMessage) => {
      // update your local message store via the signal so the bubble re-renders (zoneless-safe)
      messages.update((prev) => prev.map((m) => (m.getId() === message.getId() ? message : m)));
    },
  });
}
```
> **Verify in your running app** whether `<cometchat-message-list>` already re-renders a visible bubble on `onMessageEdited` for you, or whether you must update your own tracked copy of the message and let Angular's change detection pick it up through the bubble's `TemplateRef` context. This is not stated in the docs either way.

## What `CometChatTemplatesService` is (and is not)
It is **not** a custom-type registry, and it is not the API above. It is a DI-based alternative to passing `*View` inputs — `setConversationItemTemplate(TemplateRef)`, `setConversationTitleTemplate(...)`, `setSharedTemplates(...)` and their `get`/`clear` pairs. Use it when the same override applies app-wide. For custom message BUBBLES use `MessageBubbleConfigService`.

## If you find yourself reading the kit bundle here, stop
The three steps above are the documented path, verified against the installed 5.1.0 kit and the live guide. If you are searching `node_modules` for `setBubbleView`, `contentView`, `effectiveContentView` or `MessageTypeKey`, you are re-deriving something the guide already states. **And if your bubble renders "This message type is not supported", the answer is not in the bundle — it is the `{type}_{category}` key above** — fetch `{DOCS_BASE}/ui-kit/angular/guides/custom-message-types.md` instead. Reading the bundle is right only for behaviour the docs genuinely omit (`cometchat-angular-v5-core/SKILL.md`), and custom-message rendering is not one of those.
