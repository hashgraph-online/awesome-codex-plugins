# Host-composed extensions — send, fetch, render

10 of the 17 dashboard extensions render **no kit affordance at all**. Enabling one in the dashboard changes nothing visible — you send through the generic `CometChat.callExtension()`, fetch the same way, and render the result yourself. This file is the full send→fetch→render pattern for `pin-message` and `save-message`; the other 8 host-composed extensions follow the same three-call shape against their own `docs_topic` page.

## 1. Send
```ts
import { CometChat } from '@cometchat/chat-sdk-javascript';

// exact slug, endpoint and payload are on the extension's own docs page
await CometChat.callExtension('pin-message', 'POST', 'v1/pin', { msgId, receiverType });
```

## 2. Fetch
```ts
import { CometChat } from '@cometchat/chat-sdk-javascript';

async function fetchPinned(receiverType: string, receiverId: string) {
  const url = `v1/fetch?receiverType=${receiverType}&receiver=${receiverId}`;
  // The 4th param is `data?: Object` — optional, no `| null` in its type. The docs'
  // own JS example passes `null` for a GET with no body; that fails strict TS. Omit
  // the argument instead (verified against the installed SDK's callExtension signature).
  return CometChat.callExtension('pin-message', 'GET', url);
  // response: { pinnedMessages: [...] } — per the extension's docs page
}
```

> **The docs show only `{ pinnedMessages: [] }` / `{ savedMessages: [] }` — never the shape of one ENTRY in that array.** Both `/fundamentals/pin-message` and `/fundamentals/save-message` stop exactly at the point that matters for rendering. This is a genuine **DOCS GAP** (recorded `AUDIT-145`, owner: docs) — do not silently guess a field name and present it as fact. **Log the raw response once in the running app** (`console.log(response)`) to see the real entry shape before writing render code against it.

## 3. Render — go through `getMessageDetails()`, not the raw JSON directly
The response is **plain JSON from an HTTP call**, not an SDK message instance — it does not have `.getText()` or any other SDK method on it. Whatever ID field the entry carries (send it a `msgId` when pinning, so the fetched entry almost certainly carries an identifier back — confirm the exact key from the logged response), resolve it into a real, typed message through the SDK's own lookup:

```ts
import { CometChat } from '@cometchat/chat-sdk-javascript';

// static getMessageDetails(messageId: string | any):
//   Promise<TextMessage | MediaMessage | CustomMessage | InteractiveMessage | BaseMessage>
// Verified in the angular-v5 catalog — this IS the documented, type-safe path from an
// id to a real message instance. Never assume the raw extension entry exposes .getText()
// itself; only an SDK-constructed message instance does.
async function labelForPinnedEntry(entry: any) {
  const message = await CometChat.getMessageDetails(entry.msgId ?? entry.messageId ?? entry.id);
  // instanceof narrows the union cleanly — .getText() only exists on TextMessage,
  // so guard it rather than assuming every pinned/saved message is text.
  return message instanceof CometChat.TextMessage
    ? message.getText()
    : message.getCategory();   // non-text (media/custom/interactive): show the category, not invented text
}
```

Render each entry as its own row (a "Saved messages" / "Pinned messages" panel) — there is no kit component for this list; it is your own `*ngFor`.

## 4. Integrating a per-message action — pin/unpin, not a bolted-on button
For an action that acts ON an existing message (pin, save, star), do **not** add a separate, unstyled control below the kit's own context menu — `<cometchat-message-list>` has a real input for exactly this, so your action gets the kit's own icon slot and styling instead of looking like an unrelated append:

```ts
import { CometChatActionsIcon } from '@cometchat/chat-uikit-angular';

class ChatComponent {
  // A single shared option — CometChatActionsIcon is a STATIC array entry, so every
  // message's context menu shows the SAME title/icon. onClick(id) receives the
  // clicked message's numeric id; branch inside it if the label needs to differ
  // (e.g. check whether `id` is already pinned before deciding what to do).
  readonly pinOption = new CometChatActionsIcon({
    id: 'pin-toggle',
    title: 'Pin message',
    iconURL: 'data:image/svg+xml;base64,…',   // supply your own — the kit ships no pin icon asset
    onClick: (id: number) => this.togglePin(id),
  });

  togglePin(id: number) { /* your pin/unpin logic */ }
}
```
```html
<cometchat-message-list [user]="activeUser()" [additionalOptions]="[pinOption]"></cometchat-message-list>
```
> **Known limitation, stated plainly rather than glossed over:** because `additionalOptions` is one static array shared by every message, you cannot show "Pin message" on an unpinned message and "Unpin message" on a pinned one through this input alone — every message's menu displays the identical entry. The workable pattern is a single, generically-labelled toggle (`"Pin / Unpin"`) whose shared `onClick(id)` checks the message's current pinned state and acts accordingly, or a visually different affordance elsewhere in the bubble driven by `MessageBubbleConfigService.setBubbleView()`'s `statusInfoView` slot (`references/custom-messages.md` §3) for messages you already know are pinned. Verified against the installed 5.1.0 kit: `additionalOptions: CometChatActionsIcon[]`, `CometChatActionsIcon`'s constructor takes `{ id, title, iconURL, onClick: (id: number) => void }`.

## The 10 host-composed extensions
`pin-message` · `save-message` · `message-shortcuts` · `voice-transcription` · `rich-media-preview` · `gifs` · `reminders` · `url-shortener` · `disappearing-messages` · `support-integrations`

> **Do not conclude a feature "does not exist" because the kit has no component and the SDK has no named method for it.** Extensions are reached through the generic `CometChat.callExtension()` — there is no `pinMessage()` to grep for. Searching `node_modules` for one will find nothing, and that is expected for the SEND/FETCH calls. Reading source **is** correct for the ONE thing the docs genuinely omit here — the response entry shape — but log the running app's response first; don't reverse-engineer it from the SDK's `.d.ts`, which describes the SDK's own classes, not this extension's ad-hoc REST payload.

Each entry in `features.angular-v5.json` carries its own `docs_topic`; `needs_stitching: true` marks all 10.

> **`docs_topic` is a PATH, not a URL.** Prefix it with `DOCS_BASE` from `cometchat-angular-v5-core/references/docs-map.md`, then append `.md`: `{DOCS_BASE}` + `/fundamentals/pin-message` + `.md`. Do **not** hardcode `https://www.cometchat.com/docs/...` — `DOCS_BASE` may point at a preview while a docs change is in flight, and a hardcoded production URL silently reads the pre-change page.
