# Host-composed surfaces — no kit component exists

These are asked for regularly. There is nothing to import; build them against the SDK. Say so plainly rather than inventing a component name.

## Create a group
No kit component. Offer **all three** types — omitting password-protected is a real gap, not a simplification.

```ts
import { CometChat } from '@cometchat/chat-sdk-javascript';
import { CometChatUIKitConstants } from '@cometchat/chat-uikit-angular';

type GroupType = 'public' | 'private' | 'password';

async function createGroup(guid: string, name: string, type: GroupType, password?: string) {
  const t =
    type === 'public'  ? CometChatUIKitConstants.GroupTypes.public  :
    type === 'private' ? CometChatUIKitConstants.GroupTypes.private :
                         CometChatUIKitConstants.GroupTypes.password;
  const group = new CometChat.Group(guid, name, t, password);
  return CometChat.createGroup(group);
}
```
The form is yours: a name field, a type selector with all three options, and a password field revealed only for `password`. After creation, refresh the groups list.

## Banned members
`<cometchat-group-members>` handles view / kick / ban / scope change, but the banned LIST has no component. Fetch it:

```ts
import { CometChat } from '@cometchat/chat-sdk-javascript';

async function bannedMembers(guid: string) {
  const req = new CometChat.BannedMembersRequestBuilder(guid).setLimit(30).build();
  return req.fetchNext();
}

async function unban(guid: string, uid: string) {
  return CometChat.unbanGroupMember(guid, uid);
}
```
Render with your own list UI and give each row an unban action. Paginate with repeated `fetchNext()` — do not assume one page is all of them.

## Login / user picker
No component, by design — authentication is app-owned. Development can log in a known UID; production mints an auth token server-side (`cometchat-angular-v5-core/references/setup-credentials.md`).

## Rule
If a request maps to none of the shipped components, say so, point at the SDK docs (`cometchat-angular-v5-core/references/docs-map.md` → SDK section), and build it host-side. Never invent a component name to fill the gap — it will not compile, and a plausible-looking name is worse than an honest "there isn't one".
