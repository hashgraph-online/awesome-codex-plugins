<!-- family-agnostic: per-platform-by-design — this reference IS the per-platform Stream inventory + target-family table; one row per platform by design. -->
# Stream (GetStream) inventory — what to find, and where it goes

Search case-insensitively. Skip `node_modules/`, `Pods/`, `build/`, `.dart_tool/`, `.gradle/` and `.git/`. "Stream" is also a common English word, so match the **package and type names below**, never the bare word `stream`. A package hit tells you Stream is present. The **import/API hits** tell you *what the app does with it*, and each one becomes a ledger row (`file:line → purpose`).

## Target family (where each platform lands)
| App platform (detect `framework`) | Stream packages you'll see | CometChat family (`peers.yaml`) | UI SDK mode → | Client mode (own UI) → |
|---|---|---|---|---|
| React / Next / Vite / CRA / Astro / React Router | `stream-chat-react`, `stream-chat`, `@stream-io/stream-chat-css`, `@stream-io/video-react-sdk` | `react-v7` | `cometchat-react-v7-core` + `-components`/`-placement` | the core's SDK fallback (`@cometchat/chat-sdk-javascript`, docs-map → SDK docs) |
| Angular | `stream-chat-angular`, `stream-chat`, `@ngx-translate/core` (Stream i18n) | `angular-v5` | `cometchat-angular-v5-core` | the core's SDK fallback (JS Chat SDK) |
| React Native / Expo | `stream-chat-react-native`, `stream-chat-expo`, `stream-chat`, `@stream-io/video-react-native-sdk` | `react-native` | `cometchat-react-native-core` | `cometchat-react-native-sdk` |
| iOS (Swift) | SPM `stream-chat-swift` (`StreamChat`, `StreamChatUI`), `stream-chat-swiftui` (`StreamChatSwiftUI`), `stream-video-swift`; pods `StreamChat`, `StreamChatUI`, `StreamChatSwiftUI` | `ios` | `cometchat-ios-core` (UIKit; host SwiftUI screens via a representable) | the iOS core's SDK fallback (`CometChatSDK`) |
| Android | `io.getstream:stream-chat-android-client`, `-offline`, `-state`, `-ui-components` (Views), `-compose`, `io.getstream:stream-video-android-*` | `android-v6` (cohort from `android_variant`: Compose → `compose-*`, Views → `kotlin-*`) | `cometchat-android-v6-core` | `cometchat-android-v5-sdk` |
| Flutter | `stream_chat_flutter`, `stream_chat_flutter_core`, `stream_chat`, `stream_chat_persistence`, `stream_chat_localizations`, `stream_video_flutter` | `flutter-v6` | `cometchat-flutter-v6-core` | the Flutter core's SDK fallback (`cometchat_sdk`, re-exported by the kit) |
| Video only (no chat) | `@stream-io/video-react-sdk`, `@stream-io/video-client`, `@stream-io/video-react-native-sdk`, `stream-video-swift`, `io.getstream:stream-video-android-*`, `stream_video_flutter` | the matching headless calls peer (`js-calls`, `react-native-calls`, `ios-calls`, `android-calls`, `flutter-calls`) | — | `cometchat-js-v5-sdk` / `cometchat-react-native-v5-sdk` / `cometchat-ios-v5-sdk` / `cometchat-android-v5-calls-sdk` / `cometchat-flutter-v5-sdk` |
| Server | `stream-chat` (Node, with the API secret), `@stream-io/node-sdk`, Python `stream-chat`/`getstream`, `stream-chat-go`, `stream-chat-ruby`, `get-stream/stream-chat` (PHP), `io.getstream:stream-chat-java`, `stream-chat-net` | — (REST, no UI Kit) | — | CometChat REST (`/rest-api/…`) |

A platform that isn't in this table (Vue, Svelte, Unity, .NET MAUI…) has no family in this pack → STOP (2): report only.

### React Native is a native platform for the build, not a web one
The migration is not done when Metro bundles: `cd ios && pod install` (the kit's Podfile needs the
`modular_headers` lines the family `-core` lists, or `pod install` itself fails), then BUILD **and
RUN** both platforms. Three failures never appear in CI — only when a person uses the app:

| Trap | What you see |
|---|---|
| React Native >= 0.87 on iOS | the kit's composer calls `InteractionManager`, removed from RN core in 0.87 — tapping send throws (`InteractionManager has been removed from react-native core`); Android is unaffected. Shim: the family `-troubleshooting` |
| a missing native peer | fails at MOUNT, and the error names the peer (`gesture-handler`, `svg`, `video`), never CometChat |
| `tsc --noEmit` | reports errors from inside the kit's own shipped source (it ships raw `src/*.tsx`), so gate on the Metro bundle — see the family `-core` -> Verify it works, which also carries the run recipe for a machine where port 8081 is taken |

## Grep signals
**Manifests**: `package.json`, `pubspec.yaml`, `build.gradle(.kts)`, `gradle/libs.versions.toml`, `Podfile`, `Package.swift`, `*.xcodeproj/project.pbxproj`, `Package.resolved`, `requirements.txt`, `go.mod`, `Gemfile`, `composer.json` → `stream-chat`, `stream_chat`, `@stream-io/`, `io.getstream`, `GetStream/stream-`, `getstream` (also the Feeds package).

**Client / auth**:
- JS: `StreamChat.getInstance(`, `new StreamChat(`, `useCreateChatClient`, `connectUser(`, `disconnectUser`, `devToken(`, `tokenProvider`, `createToken(` (server).
- iOS: `ChatClient(config:`, `ChatClientConfig`.
- Android: `ChatClient.Builder`, `StreamOfflinePluginFactory`, `StreamStatePluginFactory`.
- Flutter: `StreamChatClient(`.
- Angular: `ChatClientService.init`.

**UI components**:
- React: `<Chat`, `<ChannelList`, `<Channel`, `<Window`, `<ChannelHeader`, `<MessageList`, `<VirtualizedMessageList`, `<MessageInput`, `<Thread`, `<ThreadList`, `<ChannelSearch`/`<SearchBar`.
  - Hooks: `useChatContext`, `useChannelStateContext`, `useMessageContext`.
  - CSS: `stream-chat-react/dist/css/…`, `@stream-io/stream-chat-css`.
- Angular: `StreamChatModule`, `StreamAutocompleteTextareaModule`, `ChannelService`, `StreamI18nService`, `<stream-channel-list>`, `<stream-channel>`, `<stream-message-list>`, `<stream-message-input>`, `<stream-thread>`.
- React Native: `OverlayProvider`, `Chat`, `ChannelList`, `Channel`, `MessageList`, `MessageInput`, `Thread`, `ImageGallery`.
- iOS: `ChatChannelListVC`, `ChatChannelVC`, `ChatThreadVC`, `Components.default`, `Appearance.default`; SwiftUI `StreamChat(chatClient:)`, `ChatChannelListView`, `ChatChannelView`, `ViewFactory`.
- Android Views: `ChannelListView`, `MessageListView`, `MessageComposerView`, `MessageListHeaderView`, `ChannelListViewModel`, `bindView`, `ChannelListActivity`, `MessageListActivity`.
- Android Compose: `ChatTheme`, `ChannelsScreen`, `MessagesScreen`, `MessagesViewModelFactory`.
- Flutter: `StreamChat(`, `StreamChannel(`, `StreamChannelListView`, `StreamChannelListController`, `StreamChannelHeader`, `StreamMessageListView`, `StreamMessageInput`, `StreamChatTheme`.

**Channels**:
- Handles: `client.channel('<type>', …)`, `channel.watch()`, `queryChannels(`, `cid`, channel types (`messaging`, `team`, `livestream`, `commerce`, `gaming`, custom).
- Members: `members:` (member-based distinct channels → `!members-` IDs), `addMembers`, `removeMembers`, `addModerators`.
- Invites: `inviteMembers`, `acceptInvite`.
- State: `channel.update`/`updatePartial`, `hide`, `show`, `truncate`, `freeze`/`frozen`, `enableSlowMode`, `mute`/`unmute`, `pin`/`archive`.

**Messages**:
- Send/edit/delete: `sendMessage(`, `updateMessage`, `partialUpdateMessage`, `deleteMessage`.
- Reply types: `parent_id`, `show_in_channel`, `quoted_message_id`.
- Reactions: `sendReaction`/`deleteReaction`.
- Mentions: `mentioned_users`.
- Uploads: `sendImage`/`sendFile`, `attachments` (`image`, `file`, `video`, `audio`, `voiceRecording`, `giphy`, custom types).
- Flags: `pinMessage`, `silent`, `markRead`/`markUnread`, `translateMessage`.
- Extras: polls (`createPoll`, `castPollVote`), reminders (`createReminder`), drafts (`createDraft`), location (`SharedLocation`, `startLiveLocationSharing`), `extraData`/custom fields.

**Events**: `client.on(`, `channel.on(`, `message.new`, `typing.start`/`typing.stop`, `message.read`, `notification.message_new`, `user.presence.changed`, `connection.changed`, `channel.updated`, `member.added`.

**Moderation**: `banUser`, `shadowBan`, `muteUser`, `blockUser`, `flagMessage`/`flagUser`, blocklists, AutoMod config, roles/grants, `channel_role`.

**Push**: `addDevice(`, `removeDevice(`, `PushProvider`, `firebase`/`apn` provider names, `setPushPreferences`, `getstream` keys in the notification payload handlers.

**Other Stream products**:
- Video: `StreamVideoClient`, `StreamCall`, `useCall`, `call.join`/`call.ring`, `SpeakerLayout`, `CallControls`.
- **Activity Feeds**: npm `getstream`, `@stream-io/feeds-client`/`@stream-io/feeds-react-sdk`, `client.feed(`, `addActivity`, `follow(`, Python `stream`/`getstream` feeds.
- AI: `ai_indicator`, `@stream-io/chat-react-ai`.

**Server**: `createToken(`, `upsertUser(s)`, `deleteUser(s)`, `exportChannels`, `verifyWebhook(`, the `x-signature` header, `before_message_send_hook_url`, custom command URLs, SQS/SNS config.

**Env / config**: `STREAM_API_KEY`, `STREAM_API_SECRET`, `STREAM_KEY`, `VITE_STREAM_*`, `NEXT_PUBLIC_STREAM_*`, `EXPO_PUBLIC_STREAM_*`, `REACT_APP_STREAM_*`, keys in plists/`local.properties`/`--dart-define`, and CI secrets named `STREAM_*`.

**Tests / mocks**: `jest.mock('stream-chat…')`, `generateChannel`/`generateUser` test utilities, `getTestClient`.
