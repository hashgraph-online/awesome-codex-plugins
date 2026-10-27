# Setup & credentials (iOS UI Kit v5)

> Verified against `CometChatUIKitSwift` 5.1.22 / `CometChatSDK` 4.1.7. Exact API always comes
> from the docs `.md` twin via `docs-map.md` — never from memory and never from `.swiftinterface`.

## 1. Detect before you add anything

Read the project, don't ask what you can see:

| Signal | Means |
|---|---|
| `Package.swift` / `*.xcodeproj` naming `CometChatUIKitSwift` | already integrated via SPM — REUSE, do not re-add |
| `Podfile` naming `CometChatUIKitSwift` | integrated via **CocoaPods** — see *version_conflict* below |
| `*.xcworkspace` present | CocoaPods project; open the workspace, never the `.xcodeproj` |
| none of the above | greenfield add |

## 2. Credentials — the full chain, including the two steps that make it work

The chain is `Secrets.xcconfig` → build settings → `Info.plist` → `Bundle.main`. Drawing the chain
is not enough: **an xcconfig that is not ATTACHED to the build configurations substitutes nothing**,
and `Info.plist` only exposes a value if the key is DECLARED there. Miss either and
`Bundle.main.infoDictionary` hands back the literal string `$(COMETCHAT_APP_ID)` — which is why the
guard in step 4 exists, and why omitting these steps drops you straight into the failure it detects.

### Step 0 — get the App ID / Region / Auth Key — OFFER to FETCH first, never default to "paste it yourself"
Before writing any file, you need three values: **App ID · Region · Auth Key** (Auth Key is dev-only).
**OFFER to fetch them from the CometChat Dashboard** — load the CLI on demand
(`@3` pins the CLI major that matches the v5 skills):

```bash
npx @cometchat/skills-cli@3 auth login
npx @cometchat/skills-cli@3 provision use --app-id <id> --json
```

Ask which EXISTING app; never auto-create. **Already have App ID / Region / Auth Key? Just paste them** —
manual paste is the fallback, not the default. Mint **auth tokens server-side** for production; never
ship the Auth Key (§4). The CLI is a dashboard/API client only (`auth`/`provision`/`config`/`features`) —
it does NOT write env files or generate code; this skill does the wiring in Steps 1–5 below.

### Step 1 — write the file (gitignored)

`Config/Secrets.xcconfig`:

```
COMETCHAT_APP_ID = 123456abcdef
COMETCHAT_REGION = us
COMETCHAT_AUTH_KEY = <dev only — see §4>
```

Add `Config/Secrets.xcconfig` to `.gitignore` **before** you put a real value in it.

> `//` starts a comment in an xcconfig, so any value containing it is silently truncated. Values
> here are plain identifiers, but keep it in mind if you ever add a URL.

### Step 2 — ATTACH it to the build configurations (the step everyone misses)

*Xcode:* select the **project** (not the target) → **Info** → **Configurations** → expand **Debug**
and **Release** → set the configuration file to `Secrets.xcconfig`.

*xcodegen* (`project.yml`), at the top level:

```yaml
configFiles:
  Debug: Config/Secrets.xcconfig
  Release: Config/Secrets.xcconfig
```

Without this the keys are not build settings at all and nothing substitutes them.

### Step 3 — DECLARE the keys in `Info.plist`

Build settings are not visible to your code on their own. Each one you want at runtime must be
declared as an `Info.plist` entry whose value is the `$(...)` reference.

> **First check whether the project HAS an `Info.plist`.** Since Xcode 13 the default is
> `GENERATE_INFOPLIST_FILE = YES` and there is no plist file in the project at all. You cannot add
> a CUSTOM key to a generated plist through build settings — measured on Xcode 16:
>
> | build setting | reaches the built `Info.plist`? |
> |---|---|
> | `INFOPLIST_KEY_NSCameraUsageDescription` (an Apple-defined key) | **yes** |
> | `INFOPLIST_KEY_COMETCHAT_APP_ID` (a custom key) | **no — silently dropped** |
>
> `INFOPLIST_KEY_*` only understands keys Apple defines. So on a generated-plist project, either
> add a real `Info.plist` and point `INFOPLIST_FILE` at it, or add the keys through the target's
> **Info** tab, which makes Xcode create one for you. The §3 usage descriptions below are Apple
> keys, so those CAN stay as `INFOPLIST_KEY_*` build settings — it is only the `COMETCHAT_*`
> credentials that need a real file.

```xml
<key>COMETCHAT_APP_ID</key>
<string>$(COMETCHAT_APP_ID)</string>
<key>COMETCHAT_REGION</key>
<string>$(COMETCHAT_REGION)</string>
<key>COMETCHAT_AUTH_KEY</key>
<string>$(COMETCHAT_AUTH_KEY)</string>
```

### Step 4 — read it back, and fail loudly

An unsubstituted value arrives as the literal `$(COMETCHAT_APP_ID)`, not as `nil` — a
silent-wrong-value trap, so reject that form explicitly:

```swift
func credential(_ key: String) -> String? {
    guard let v = Bundle.main.infoDictionary?[key] as? String,
          !v.isEmpty, !v.hasPrefix("$(") else { return nil }   // reject the un-substituted form
    return v
}
```

### Step 5 — verify the substitution before blaming CometChat

Build, then print `Bundle.main.infoDictionary?["COMETCHAT_APP_ID"]`. A real App ID means the chain
works. The literal `$(COMETCHAT_APP_ID)` means step 2 or step 3 is missing — the credentials are
fine and the wiring is not. An init/login failure here is NOT a CometChat problem.

> For a shipping build, do not carry the Auth Key in the Release configuration at all — see §4.

## 3. `Info.plist` usage descriptions

The kit's media affordances call system pickers, and iOS terminates the app if the matching
usage string is absent. Add the ones your chosen features actually need:

| Key | Needed by |
|---|---|
| `NSCameraUsageDescription` | camera attachments, video calling |
| `NSMicrophoneUsageDescription` | voice notes, voice/video calling |
| `NSPhotoLibraryUsageDescription` | image/video attachments |

Write a real sentence for each ("Take photos to send in chat") — App Review rejects placeholders.

## 4. Auth Key vs auth token — the production rule

- **Auth Key** authenticates as ANY user. It is a development convenience only. Shipping it in
  an app binary hands every account to anyone who unzips the IPA.
- **Production**: mint an auth token **server-side** and log in with it. The client never holds
  the Auth Key.

`login(uid:)` does NOT create users. On a fresh app the docs' pre-created test users are
`cometchat-uid-1 … 5`; for any real app, ASK which UID to use rather than guessing.

## 5. version_conflict

CocoaPods distribution is winding down and its spec repo is going read-only, so **SPM is the
only supported integration path**. A `Podfile` is a DETECTION signal, never an instruction.

If the project already integrates via CocoaPods, STOP and surface the choice — do not silently
add SPM alongside it. Two package managers resolving the same binary xcframework is the
`version_conflict` case: state it, recommend migrating to SPM, and let the user decide.

The kit is a prebuilt binary compiled against ONE SDK version, and SPM does not resolve that
transitively — pin `CometChatSDK` to the exact version the kit requires, or you get link errors
that look like missing symbols.

## 6. `cometchat-settings.json` — telemetry attribution

Separate from the xcconfig chain above, and required for CometChat to attribute the integration
to the skills rather than to a hand-written one.

`CometChatUIKit.initFromSettings` takes **no parameters**. That is not a limitation — it reads a
JSON file from the app bundle. Create `cometchat-settings.json` and add it to the target's **Copy
Bundle Resources**:

```json
{
  "appId": "<your app id>",
  "region": "<your region>",
  "authKey": "<dev only — see §4>",
  "presenceSubscription": { "type": "ALL_USERS" }
}
```

Valid `presenceSubscription.type` values are `ALL_USERS`, `ROLES`, `FRIENDS`, `NONE` — the SDK
rejects anything else by name. **Gitignore this file**: it carries the Auth Key, exactly like
`Secrets.xcconfig`.

### Call it BEFORE the classic init, not instead of it

| init path | `integrationSource` | login / render |
|---|---|---|
| classic `CometChatUIKit(uiKitSettings:)` alone | *absent* — calls stamped **`"manual"`** | works |
| `initFromSettings` alone | `"ai-agent"` | **fails — `Err_101`** |
| `initFromSettings` **then** classic | `"ai-agent"` | works |

Measured on 5.1.19 with the app container wiped between runs. On this version
`initFromSettings` initialises the Chat SDK but leaves the UI Kit layer uninitialised, so using it
alone breaks login — a kit defect, and the reason the recipe runs both.

> Why this is worth the extra call: without it every app you build is attributed to
> `"manual"`. That is not merely missing attribution, it is **wrong** attribution.

> A note on verifying this API: `integrationSource` appears **nowhere** in the shipped
> `.swiftinterface`, and an earlier version of this pack concluded from that fact that attribution
> was impossible on iOS. That was wrong. The interface lists which SYMBOLS EXIST; it says nothing
> about runtime behaviour or where a function's inputs come from. Both facts here came from the
> shipped binaries and from measuring `UserDefaults`, not from the interface.
