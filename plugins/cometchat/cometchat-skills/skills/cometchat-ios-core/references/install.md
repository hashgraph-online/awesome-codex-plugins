# Install — Swift Package Manager

The full install detail. The entry keeps only the version rule and the SPM-only rule.

**Use SPM. Do not use CocoaPods and do not offer it as an option**, even if the user's project already has a `Podfile`: CocoaPods distribution is being wound down and its spec repo is going read-only, so a Podfile-based integration cannot receive future releases. A project already on CocoaPods should be moved to SPM as part of adding CometChat.

Add the UI Kit package. Since 5.2.1 its own `Package.swift` declares `CometChatSDK` (`from: "4.1.10"`) and `CometChatCardsSwift` (`from: "1.2.0"`), so SPM resolves both for you. Add the Calls SDK only when the app places calls.

| Package | Repository | Version rule (Xcode: *Dependency Rule*) |
|---|---|---|
| `CometChatUIKitSwift` | `https://github.com/cometchat/cometchat-uikit-ios` | **Up to Next Major Version, from 5.2.3** |
| `CometChatSDK` | `https://github.com/cometchat/chat-sdk-ios` | resolved by the kit (4.1.10 today). Do NOT add it yourself |
| `CometChatCallsSDK` | `https://github.com/cometchat/calls-sdk-ios` | **calling only:** Up to Next Major Version, from 5.0.4 (`cometchat-ios-calls`) |

> **Why 5.2.3 is the floor, not just "the latest":**
> - 5.1.19 to 5.1.22 shipped a `.swiftinterface` with an unconditional `import CometChatCallsSDK`, so every app had to link the Calls SDK. Fixed in 5.1.23: the 5.2.3 interface imports only `CometChatSDK` and `CometChatCardsSwift`.
> - 5.2.0 to 5.2.2 strongly linked the Calls SDK and crashed at launch without it (`Library not loaded: @rpath/CometChatCallsSDK.framework`). Fixed in 5.2.3, which links it optionally again. A chat-only app on 5.2.3 builds and launches with the kit package alone.
> - Before 5.2.1 the kit's `Package.swift` did not declare `CometChatSDK` (only `CometChatCardsSwift`), which is why older guidance pinned `CometChatSDK` by hand at the exact version the binary was built against. That is no longer needed. The kit now sets a floor (the version its binary is built against) and accepts newer 4.x, because both binaries ship with library evolution.
>
> If the project already pins `CometChatSDK` by hand (an older integration), loosen it to *Up to Next Major from 4.1.10* or remove it. An exact pin below 4.1.10 makes package resolution fail.

Deployment target **iOS 15.1+**. Add the usage descriptions the kit's media features need to `Info.plist` (camera, microphone, photo library) — see `references/setup-credentials.md`.
