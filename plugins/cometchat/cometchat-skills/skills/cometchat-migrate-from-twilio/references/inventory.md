<!-- family-agnostic: per-platform-by-design — this reference IS the per-platform Twilio inventory + target-family table; one row per platform by design. -->
# Twilio Conversations inventory — what to find, and where it goes

Search case-insensitively. Skip `node_modules/`, `Pods/`, `build/`, `.dart_tool/`, `.gradle/`, `.git/`. "Twilio" is distinctive; match the package + class names below. Twilio Conversations is **headless** — the app has its own UI on the Twilio client, so most hits are in a data/service layer, and each becomes a ledger row (`file:line → purpose`).

## Target family (where each platform lands)
| App platform (detect `framework`) | Twilio packages you'll see | CometChat family (`peers.yaml`) | Default = client/SDK mode → | Optional (fresh UI) → |
|---|---|---|---|---|
| React / Next / Vite / CRA / Astro | `@twilio/conversations` (+ `twilio-chat` if legacy) | `react-v7` | the core's Chat SDK fallback (`@cometchat/chat-sdk-javascript`) | `cometchat-react-v7-core` UI Kit |
| Angular | `@twilio/conversations` | `angular-v5` | JS Chat SDK | `cometchat-angular-v5-core` |
| React Native / Expo | `@twilio/conversations` (RN-compatible) | `react-native` | `cometchat-react-native-sdk` | `cometchat-react-native-core` |
| iOS (Swift) | `TwilioConversationsClient` (pod/SPM `twilio-conversations`) | `ios` | the iOS core's SDK fallback (`CometChatSDK`) | `cometchat-ios-core` |
| Android | `com.twilio:conversations-android` | `android-v6` | `cometchat-android-v5-sdk` | `cometchat-android-v6-core` |
| Flutter | `twilio_conversations` | `flutter-v6` | the Flutter core's SDK fallback (`cometchat_sdk`) | `cometchat-flutter-v6-core` |
| Server (Node, Python, Go, Java, Ruby, PHP, C#) | `twilio` server SDK → Conversations REST; access-token minting | — (REST) | — | CometChat REST (`/rest-api/…`) |

Because Twilio ships no UI Kit, the **default** target is client/SDK mode (keep the app's UI). Offer the UI Kit path only if the user wants CometChat's prebuilt UI. A platform not in this table → STOP: report only.

## Grep signals
**Manifests**: `package.json`, `Podfile`, `Package.swift`, `build.gradle(.kts)`, `pubspec.yaml`, `requirements.txt`, `go.mod`, `Gemfile`, `composer.json`, `*.csproj` → `twilio/conversations`, `twilio-conversations`, `twilio_conversations`, `@twilio/conversations`, `twilio-chat` (legacy Programmable Chat), `TwilioConversationsClient`, `com.twilio:conversations`.

**Client / auth**:
- JS: `Client` / `Conversations.Client`, `new Client(token)`, `Client.create(token)`, `client.updateToken(...)`, `'stateChanged'` → `'initialized'`, `'tokenAboutToExpire'` / `'tokenExpired'`.
- iOS: `TwilioConversationsClient.conversationsClient(withToken:...)`.
- Android: `ConversationsClient.create(...)`.
- Flutter: `TwilioConversations.create(...)`.
- **Access token fetch**: a call to your server for a Twilio JWT (the client never holds the API secret).

**Conversations (channels)**:
- `client.getConversationBySid` / `getConversationByUniqueName` / `createConversation` / `getSubscribedConversations`.
- `conversation.add(...)` / `join()` / `leave()` / `delete()`, `friendlyName`, `uniqueName`, `attributes`.

**Participants**:
- `conversation.getParticipants()`, `add(identity)` / `addNonChatParticipant` (SMS/WhatsApp), `removeParticipant`, `participant.identity`.

**Messages**:
- `conversation.sendMessage(...)` (text or a `MessageBuilder` with media), `getMessages(...)`, `message.body`, `message.attributes`, `message.media` / `attachedMedia`, `updateBody`, `remove`.
- Delivery/read: `conversation.setAllMessagesRead()`, `getUnreadMessagesCount()`, `advanceLastReadMessageIndex`, `AggregatedDeliveryReceipt` / `DetailedDeliveryReceipt`.
- Typing: `conversation.typing()`, `'typingStarted'` / `'typingEnded'`.

**Events**: `client.on('conversationAdded'|'messageAdded'|'participantJoined'|'typingStarted'|'connectionStateChanged'|...)`, `conversation.on('messageAdded'|...)`.

**Media**: `message.media.getContentTemporaryUrl()`, `MessageBuilder.addMedia(...)`, `media.filename`/`contentType`/`size`.

**Other**: `user`/`User` (friendlyName, attributes, online/notifiable), push (`client.setPushRegistrationId` / FCM/APNs binding), `attributes` (JSON on conversation/message/participant/user).

**Legacy Programmable Chat** (`twilio-chat`, deprecated): `Channel`, `Member`, `Message`, `client.getChannelBySid` — same shapes as Conversations; map identically and note it's the legacy SDK.

**Server**: `AccessToken` + `ChatGrant`/`ConversationsGrant` (API Key SID/Secret + Conversations Service SID), Conversations REST (`conversations.v1.conversations…`), webhooks (`onMessageAdded`, `onConversationAdded`, scoped/global).

**Env / config**: `TWILIO_ACCOUNT_SID`, `TWILIO_API_KEY`, `TWILIO_API_SECRET`, `TWILIO_CONVERSATIONS_SERVICE_SID`, `VITE_TWILIO_*`, tokens endpoints; CI secrets `TWILIO_*`.

**Tests / mocks**: `jest.mock('@twilio/conversations')`, fake `Client`/`Conversation`.
