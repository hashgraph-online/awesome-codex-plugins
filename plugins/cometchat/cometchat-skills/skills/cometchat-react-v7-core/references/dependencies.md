# dependencies — packages, pins, SDK types (React v7)

## Packages (two)
```json
{ "@cometchat/chat-uikit-react": "^7", "@cometchat/chat-sdk-javascript": "^4" }
```
UI Kit = the React components; SDK = the `CometChat` namespace (types + methods).
> **Keep the `@^7` / `@^4` major pins — never a bare `npm install @cometchat/chat-uikit-react`.** A bare install resolves to `latest`; these skills teach v7, so an unpinned install can pull the wrong major and break the integration.

## SDK types you'll use
```typescript
import { CometChat } from "@cometchat/chat-sdk-javascript";
CometChat.User          // a chat user
CometChat.Group         // a chat group
CometChat.Conversation  // wraps a User or Group
CometChat.BaseMessage   // any message
CometChat.TextMessage   // a text message
CometChat.getUser(uid): Promise<CometChat.User>
CometChat.getGroup(guid): Promise<CometChat.Group>
```

## Cost transparency (disclose when integrating into a new project) — **[v7-verify numbers]**
The v6 kit added ~2.8 MB JS (~860 KB gzip), ~860 KB CSS, ~1.5 MB Roboto fonts (9 weights). Re-measure for v7. If the app already loads custom fonts, override `--cometchat-font-family` to skip preloading kit fonts. For evaluators: pricing at cometchat.com/pricing (free tier for dev/test); data export via REST (`GET /v3/users|groups|messages`) — no lock-in.
