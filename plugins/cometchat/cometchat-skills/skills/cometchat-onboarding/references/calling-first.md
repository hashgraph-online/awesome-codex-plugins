# calling-first.md — the "add calling" decision tree

Load this when the PRIMARY, explicit first-contact intent is **calling** — the user opens with "add calling / add voice-video / add a video call to my app" as the GOAL, not "add chat" that merely includes calls. Standalone, build-your-own-UI calling (a video-only app, a meeting room, an embedded call widget with no chat surface) is a legitimate product, so **calling is the one intent where onboarding offers an approach choice**. (A CHAT build still gets NO approach question — the "Asking 'UI Kit or SDK?'" pitfall stands for chat.)

Run it as a consultative Q&A (clarification contract: ask **and wait** at each branch). Still run beats 1–3 (whole-repo discovery + a short plan naming the mode + packages + credential strategy) BEFORE the hand-off — this tree replaces the archetype/approach question for calling-first intent; it does not skip the plan.

## Step 1 — detect the UI Kit (beat 1)
Is a CometChat UI Kit installed? Web/RN: `@cometchat/chat-uikit-*` in `package.json`. **iOS: the `ios` row's `kit_package` (`peers.yaml`) in `Package.swift`/`Podfile`, or an `*.xcodeproj`/`*.xcworkspace` that resolves it.** Android: `com.cometchat:chatuikit-*` in the gradle files. Flutter: `cometchat_chat_uikit` in `pubspec.yaml`.

## Step 2 — branch on that
- **UI Kit IS installed** → ask:
  > *"Your UI Kit already ships a prebuilt calling UI (incoming-call surface, call buttons, ongoing-call). Use that, or build a standalone calling feature from scratch with no prebuilt UI?"*
  - **prebuilt** → hand off to `cometchat-<family>-calls` (e.g. `cometchat-react-v7-calls`, **`cometchat-ios-calls`** on iOS). It rides the SAME init/login — enable calling on the existing UIKit settings (`uiKit.callsSDK`). Done.
  - **from scratch** → Step 3.
- **UI Kit is NOT installed** → ask:
  > *"We also ship UI Kits with a prebuilt calling UI. Do you need CHAT as well, or only calling? If you'll want chat too, the UI Kit gives you both with a prebuilt call UI; if it's calling-only, we can build it from scratch."*
  - **chat too / wants prebuilt** → the normal UI-Kit journey (`cometchat-<family>-core` + `calls`).
  - **calling only / from scratch** → Step 3.

## Step 3 — from-scratch / standalone calling → ask the call SHAPE
> *"One-on-one (ringing — call a specific user, they get an incoming prompt to accept/reject) or meet-style (a session room anyone joins by id)?"*

### Step 3b — ringing on MOBILE ⇒ ask DELIVERY too (ask **and wait**; never assume)
Answered **one-on-one ringing** on a mobile platform (Android/iOS/Flutter/React-Native)? Ask this BEFORE
the plan — it is an architecture fork, not a later add-on:
> *"Do calls need to ring when the app is in the background or closed — the way WhatsApp does? Or is
> in-app ringing enough (both people have the app open)?"*

- **In-app / foreground only** → the ringing recipe (`initiateCall` / `CallListener` / `acceptCall`).
  **Say the limit out loud in the plan:** in auto socket mode the Chat SDK drops its WebSocket the moment
  the app is backgrounded, so a backgrounded callee never rings and the caller just times out (~45 s) —
  verified live on two devices. It is NOT replayed when they return.
- **Background / killed-app ringing** → that is **VoIP push**, a separate build, and a **real device**
  either way (neither emulators nor the iOS Simulator can prove it).
  *Android:* an FCM project + `FirebaseMessagingService`, `PhoneAccount` registration, a
  `ConnectionService` — `/calls/android/voip-calling`, docs-first, paired with the platform's `push` skill.
  *iOS:* the separate `CometChatPushNotifications` package (an APNs **VoIP** provider in the dashboard,
  Background Modes → Voice over IP, and a device — APNs never delivers a VoIP push to the Simulator). The
  SDK owns `PKPushRegistryDelegate` and `CXProviderDelegate`; writing either yourself fights it for the
  same callbacks. Certified on device via `cometchat-ios-v5-sdk`.
  Name it as its own plan item with its own prerequisites — do not fold it into the ringing recipe and do
  not promise it from that recipe.

**Why this is asked, not assumed.** "One-on-one ringing" reads as *WhatsApp* to most people, and the
foreground-only build passes every casual test (both apps open during development) before failing in the
user's real world. A user who wanted VoIP and got the ringing recipe does not find out until their
callee's phone stays silent. Web/JS has no VoIP-push equivalent — skip 3b there.

## Step 4 — resolve the headless skill FROM THE DETECTED PLATFORM
The headless calls skill is **per-platform** — resolve it from `peers.yaml` (the peer whose `consumption: sdk` and whose `kit_package` is a `calls-sdk-*`), never from a literal. Today's live headless-calls peers:

| Detected platform | Peer | Skill | Calls package | Ringing also needs |
|---|---|---|---|---|
| web / JS | `js-calls` | `cometchat-js-v5-sdk` | `@cometchat/calls-sdk-javascript@5` | `@cometchat/chat-sdk-javascript@4` |
| React Native | `react-native-calls` | `cometchat-react-native-v5-sdk` | `@cometchat/calls-sdk-react-native@5` | `@cometchat/chat-sdk-react-native@4` |
| iOS | `ios-calls` | `cometchat-ios-v5-sdk` | `CometChatCallsSDK` | the Chat SDK for signaling |
| Android | `android-calls` | `cometchat-android-v5-calls-sdk` | `com.cometchat:calls-sdk-android` | the Chat SDK for signaling |
| Flutter | `flutter-calls` | `cometchat-flutter-v5-sdk` | `cometchat_calls_sdk: ^5.0.7` | `cometchat_sdk` v5 |

**Is that skill installed?** `add` installs ONE family per run — a UI-Kit install carries only that family's skills, so the headless calls skill may not be in the project's skills folder yet. If it isn't, install it before the hand-off — it is added ALONGSIDE the existing UI Kit skills (nothing is removed):
`npx @cometchat/skills add --family <js-calls|react-native-calls|ios-calls|android-calls|flutter-calls>` (same `--ide` you installed with). Never hand off to a skill that is not present.

> ⚠️ **The JOIN STEP IS NOT PORTABLE — do not copy it across platforms.** Web joins with `joinSession(token, sessionSettings, containerEl)` into a sized **DOM element**. React Native has **no `joinSession` at all**: you join by RENDERING `<CometChatCalls.Component callToken sessionSettings />` inside a flex-sized `View`. Flutter is a third shape again — `joinSession` RETURNS a `Widget?` and mounts nothing, so the app must place it in the widget tree; an agent that ports another platform's snippet produces a call that joins successfully and renders a blank screen. Name the mode and let the platform's own skill own the recipe.

Then hand off to the resolved skill with the chosen mode named in the directive:
- **meet-style** → Calls SDK only (`generateToken` → the platform's join step). No Chat SDK.
- **one-on-one ringing** → Calls SDK media + **Chat SDK signaling** (`initiateCall` / `CallListener` / `acceptCall`) — note the platform's extra chat-SDK dependency from the table in the plan, and carry the Step-3b delivery answer through.

## Hand-off directive shape
`"standalone <meet-style|one-on-one ringing> calling via cometchat-js-v5-sdk, <session-room|ring-a-user> surface, dev Auth-Key, package(s): @cometchat/calls-sdk-javascript@5[ + @cometchat/chat-sdk-javascript@4 for ringing], touch <paths>"`. Android: `"standalone <meet-style|one-on-one ringing> calling via cometchat-android-v5-calls-sdk, <session-room|ring-a-user> surface, <in-app ringing (foreground-only)|+ VoIP push for background/killed>, dev Auth-Key in assets/cometchat-settings.json, package(s): com.cometchat:calls-sdk-android:5.0.+[ + com.cometchat:chat-sdk-android:5.0.+ for ringing], touch <paths>"`. The headless skill owns install, init→login→generateToken→joinSession, listeners, and teardown. **A ringing directive on mobile MUST carry the Step 3b delivery answer** — without it the recipe silently defaults to foreground-only and the user learns the limit after the build.

**iOS:** `"standalone <meet-style|one-on-one ringing> calling via cometchat-ios-v5-sdk, <session-room|ring-a-user> surface, <in-app ringing (foreground-only)|+ VoIP push for background/killed>, dev Auth-Key, package(s): CometChatCallsSDK@5 via SPM (github.com/cometchat/calls-sdk-ios)[ + CometChatSDK@4 for ringing][ + CometChatPushNotifications@1 for VoIP], Info.plist camera+mic usage strings, touch <paths>"`. The headless iOS skill owns install, init->login->join, listeners and teardown.

**Flutter:** `"standalone <meet-style|one-on-one ringing> calling via cometchat-flutter-v5-sdk, <session-room|ring-a-user> surface, <in-app ringing (foreground-only)|+ push for background/killed>, dev Auth-Key in cometchat-settings.json (a registered Flutter ASSET — commit a placeholder with no real key so a fresh clone builds; real keys supplied locally / generated in CI, per `cometchat-flutter-v6-core`), package(s): cometchat_calls_sdk: ^5.0.7[ + cometchat_sdk v5 for ringing], minSdk 26 / iOS 15.1, touch <paths>"`. Three Flutter-specific things the directive must not lose:
- the token API is **`generateCallToken`**, not `generateToken` — the latter is deprecated and the live docs still show it.
- ⚠️ **do not carry another platform's calling snippet across.** Flutter's `joinSession` returns a `Widget?` and mounts nothing; the app places it in the widget tree. An agent that pattern-matches the container-based platforms produces a call that joins and renders a blank screen.
- for Step 3b, Flutter has **no first-party CometChat push package** — background ringing is FCM on Android and APNs/CallKit on iOS, wired by the app. Say so rather than promising a package that does not exist.
