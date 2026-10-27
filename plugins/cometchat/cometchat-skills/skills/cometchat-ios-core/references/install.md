# Install — Swift Package Manager

The full install detail. The entry keeps only the three pinned versions and the SPM-only rule.

**Use SPM. Do not use CocoaPods and do not offer it as an option**, even if the user's project already has a `Podfile`: CocoaPods distribution is being wound down and its spec repo is going read-only, so a Podfile-based integration cannot receive future releases. A project already on CocoaPods should be moved to SPM as part of adding CometChat.

Add these three packages. The kit is a **prebuilt binary compiled against ONE Chat SDK version** and SPM does not resolve that transitively, so the versions are **exact, not floors** — overriding either side is unsupported and either fails to build or crashes at runtime.

| Package | Repository | Version |
|---|---|---|
| `CometChatUIKitSwift` | `https://github.com/cometchat/cometchat-uikit-ios` | **exactly 5.1.22** |
| `CometChatSDK` | `https://github.com/cometchat/chat-sdk-ios` | **exactly 4.1.7** |
| `CometChatCallsSDK` | `https://github.com/cometchat/calls-sdk-ios` | **exactly 5.0.3** |

> **All three must be added BY HAND — including the Calls SDK, and including for a chat-only app.**
> This is a **packaging regression in 5.1.19**, not a design requirement, so treat it as a workaround with a shelf life rather than a permanent rule:
> - 5.1.19's compiled `.swiftinterface` carries `import CometChatCallsSDK`, and Swift requires every import in an interface to be resolvable — so the module must be present to compile **any** integration, even one with no calling.
> - Nothing in the kit's **public API actually uses a CallsSDK type** (0 references), and **5.1.16 and 5.1.18 have no such import at all**. It appears in 5.1.19 only. That makes it an internal import leaking into the public interface, not an intentional dependency.
> - The kit's own `Package.swift` declares **neither** `CometChatSDK` nor `CometChatCallsSDK`, so SPM cannot supply them. Omit the Calls SDK and the build fails with `unable to resolve module dependency: 'CometChatCallsSDK'`.
>
> If a future release drops that import, the Calls SDK goes back to being calls-only and belongs to `cometchat-ios-calls`. Re-check the interface before assuming this still applies.

Deployment target **iOS 15.1+**. Add the usage descriptions the kit's media features need to `Info.plist` (camera, microphone, photo library) — see `references/setup-credentials.md`.
