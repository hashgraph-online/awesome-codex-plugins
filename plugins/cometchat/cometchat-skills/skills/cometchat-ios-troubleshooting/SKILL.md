---
name: cometchat-ios-troubleshooting
description: "Diagnose a broken CometChat iOS (Swift) integration — a screen that never populates, credentials read as the literal $(...), login that silently fails, empty lists, no messages, or a version/SDK mismatch. Triggers: 'cometchat ios not working', 'chat screen blank swift', 'cometchat login not working ios', 'credentials not read swift', 'conversations empty ios', 'cometchat swift errors'."
license: "MIT"
compatibility: "CometChatUIKitSwift 5.1.22 + CometChatSDK 4.1.7; Xcode 16+; iOS 15.1+; SPM only"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat ios swift troubleshooting debug diagnostics blank-screen spm"
---

> **Ground truth:** `CometChatUIKitSwift` 5.1.22 + `CometChatSDK` 4.1.7 (symbols verified vs `catalogs/ios-v5.json`); signatures FETCHED via `cometchat-ios-core/references/docs-map.md`; the invariants below (init→login order, credentials flow, SPM-only) are `RULES.md` + `cometchat-ios-core`. This diagnostics catalog is cross-checked against the live `{DOCS_BASE}/ui-kit/ios/troubleshooting.md` page (base + paths in `cometchat-ios-core/references/docs-map.md`), and adds the host-side/runtime symptoms it doesn't cover.

## Companion skills (read first)
- `cometchat-ios-core` — the correct init→login→render order, the `Secrets.xcconfig`→Info.plist→`Bundle.main` credential flow, and the SwiftUI launch hook the fixes below restore.

## Use this skill when
An iOS CometChat integration compiles but misbehaves at runtime: a screen that never fills, login that does nothing, or empty data.

## Start here — iOS fails SILENTLY, on ORDER and CREDENTIALS
The two dominant causes of "the screen never populates":
1. **`login()` was called before `initFromSettings` resolved.** Both are async and must COMPLETE in order; login-before-init fails with no crash and no visible error — just a screen that never loads (`cometchat-ios-core`).
2. **Credentials came through as the literal `$(COMETCHAT_APP_ID)`.** The `Secrets.xcconfig` → attach-to-configs → declare-in-Info.plist → read-via-`Bundle.main` chain has four steps; miss one and you init with the literal placeholder, which then fails auth.

## Symptom → cause → fix
| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Screen never populates, no error | `login` before `init` resolved | Chain them: call login only inside the init completion (`cometchat-ios-core` `references/swiftui.md`) |
| Auth fails immediately | Wrong Region, or creds read as `$(...)` | Region must match the dashboard app; verify `Bundle.main` returns the value, not the literal `$(` |
| Values are the literal `$(...)` | `xcconfig` not attached, or Info.plist key missing | Attach `Secrets.xcconfig` to the build configs AND declare each key in Info.plist (`references/setup-credentials.md` §2-§3) |
| SPM won't resolve / kit crashes at runtime | `CometChatSDK` version drifted from the kit's exact pin | Pin CometChatUIKitSwift 5.1.22 + CometChatSDK 4.1.7 + CometChatCallsSDK 5.0.3 exactly (`cometchat-ios-core` Install) |
| Build fails after adding a Podfile | Tried CocoaPods | SPM only — a Podfile is a detection signal, not an instruction; remove the pod integration |
| Conversations empty | New app has no conversations, or wrong scope | Send a first message; check the request scope |
| `login` "user not found" | UID does not exist in the app | Use a real UID (Dashboard → Users; fresh apps seed `cometchat-uid-1`) — never a guessed `superhero*` |
| Calls fail / no permission prompt | Missing usage-description strings or VoIP entitlement | Add `NSCameraUsageDescription` + `NSMicrophoneUsageDescription`; enable the VoIP entitlement (`cometchat-ios-push`/`-calls`) |
| Works in dev, fails in release | Auth Key stripped for release but still using `login(uid:)` | Switch to `login(authToken:)` with a server token (`cometchat-ios-production`) |

## When the table does not cover it
Enable SDK logging and read the Xcode console: an init/lifecycle error (a call made before `init()` resolved) is the usual "nothing renders" cause; auth errors are almost always Region or a literal-placeholder credential. Then fetch the feature's page via `cometchat-ios-core/references/docs-map.md`. Never diagnose from the binary framework's headers or from memory — fetch the documented signature.

## Verify it works
init and login both resolve (in order) before the chat screen renders · `Bundle.main` returns real credential values, not `$(...)` · the exact kit/SDK versions are pinned · conversations render or show the empty state · a message sends and arrives · calls prompt for permission.

## What NOT to do
Do not hard-code credentials to get past the `$(...)` literal — fix the xcconfig/Info.plist chain; do not add CocoaPods to work around an SPM resolve issue — pin the exact versions; do not hard-code a UID to dodge "user not found."
