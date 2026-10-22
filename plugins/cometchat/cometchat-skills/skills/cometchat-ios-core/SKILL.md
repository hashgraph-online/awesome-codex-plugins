---
name: cometchat-ios-core
description: "Add CometChat chat to an iOS app end-to-end — detect the project, get & verify dashboard credentials, init→login→render, and the drop-in conversation UI composed into a chat screen. The core knowledge every other iOS skill builds on. Triggers: 'integrate cometchat swift', 'set up cometchat credentials ios', 'show conversations and messages ios'."
license: "MIT"
compatibility: "Xcode 16+; iOS 15.1+ (the kit's deployment floor); Swift 5.0+; CometChatUIKitSwift 5.1.22 + CometChatSDK 4.1.7 + CometChatCallsSDK 5.0.3 (exact — see Install)"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat ios swift uikit core chat integration v5 setup credentials"
---

> **Ground truth:** `CometChatUIKitSwift` 5.1.22 (a prebuilt binary xcframework) + `CometChatSDK` 4.1.7. Every symbol below is verified against the shipped `.swiftinterface` (`catalogs/ios-v5.json`); the golden-path composition and its layout constraints are verified on a simulator by the native harness, not reasoned from the web pack. This file is the THIN map loaded every run; deep detail lives in `references/*`, loaded only when the task needs it.

<!-- core is the companion the other iOS skills read; it has no Companion block of its own. -->

## Use this skill when
"add chat to my iOS app", "integrate CometChat in Swift", "set up CometChat credentials", "show a conversations + messages screen", "build a chat app". An unscoped "add chat" means a **production-ready core chat surface** — a `CometChatConversations` list that pushes to a chat screen you compose — NOT a bare list, and NOT the whole combined app. It **grows on request** (users/groups tabs, group details, threads, calls); those recipes live in `cometchat-ios-placement` and `cometchat-ios-features`.

## Three things that are NOT like the web UI Kit
Setter-based API (not props) · **no** composite component in v5 (the `*WithMessages` names are v4) · navigation stack, not side-by-side panes. Full detail + why each one compiles-but-fails: `references/anti-patterns.md`.

## Install — Swift Package Manager only
**SPM only. Never CocoaPods**, even if a `Podfile` exists (its distribution is winding down; a Podfile is a detection signal, not an instruction). Add three packages at EXACT versions — the kit is a prebuilt binary compiled against one Chat SDK version and SPM will not resolve that transitively: `CometChatUIKitSwift` **5.1.22** · `CometChatSDK` **4.1.7** · `CometChatCallsSDK` **5.0.3** (required even for chat-only — see `references/install.md` for the repos, the Calls-SDK reason, and the Xcode steps).
> **Why `CometChatSDK` 4.1.7 and not the newer 4.1.9 in the docs' setup pages:** these are the versions the pinned 5.1.22 UI Kit binary was built and verified against here (catalog + simulator smoke). The kit is a prebuilt xcframework that links a specific Chat SDK — bumping only `CometChatSDK` risks a binary-compat mismatch SPM won't catch. Do NOT flip the pin on your own; it moves together with the UI Kit when this pack next upgrades the iOS family.

## Setup & credentials (essentials — full chain: `references/setup-credentials.md`)
1. **Detect** the project shape AND its lifecycle — a stock Xcode project is a SwiftUI `@main App` with **no AppDelegate/SceneDelegate**, so there is no launch hook for `init → login` until you add one (`references/swiftui.md`). A `Podfile` is a detection signal only; integrate via SPM.
2. **version_conflict — STOP** if a non-v5 kit is installed (v4 shows `*WithMessages` components). Reconcile first, never mix majors (`RULES.md`); v4 → v5 is `cometchat-ios-migration`.
3. **Credentials — OFFER to fetch from the dashboard FIRST; never silently default to "paste it yourself."** Load the CLI on demand (`references/setup-credentials.md` has the exact command), ask which EXISTING app, never auto-create. Manual paste is the fallback.
4. **Wire them**: gitignored `Secrets.xcconfig` → ATTACH to the build configurations → DECLARE each key in `Info.plist` as `$(COMETCHAT_APP_ID)` → read via `Bundle.main`, rejecting the literal `$(`. Miss a step and you get the literal, not the value. Modern projects generate `Info.plist` and cannot take custom keys through build settings — `references/setup-credentials.md` §2-§3.
5. **Authorize** = init and login both resolve. An auth failure is usually the wrong Region.

## Integration ordering (BAKED — invariant)
`init` → `login` → **only then** render. Both are async and both must COMPLETE before the next step. Calling `login()` before init resolves fails **silently** — no crash, no error, just a screen that never populates.

```swift
import CometChatUIKitSwift
import CometChatSDK

let settings = UIKitSettings()
    .set(appID: appID)          // from Secrets.xcconfig — never a literal
    .set(region: region)
    .set(authKey: authKey)      // DEV ONLY; prod uses login(authToken:)
    .subscribePresenceForAllUsers()
    .build()

// ATTRIBUTION FIRST, then the credential-bearing init — BOTH, in this order.
// `initFromSettings` stamps integrationSource = "ai-agent". It takes no parameters because it
// reads a bundled `cometchat-settings.json` (see references/setup-credentials.md §6). Skip it and
// the app is stamped "manual" — attributed to a hand-written integration, which is worse than
// unattributed. On 5.1.19 it does NOT initialise the UI Kit layer, so calling it INSTEAD of the
// classic init makes login fail with Err_101; it runs BEFORE, never in place of.
CometChatUIKit.initFromSettings { _, _ in
    // Ignore the result deliberately: attribution is best-effort. A missing or malformed
    // settings file must not stop the app from initialising below.
    CometChatUIKit(uiKitSettings: settings) { result in
        switch result {
        case .success:
            // Guard re-login: getLoggedInUser() is SYNCHRONOUS.
            // This init callback is NOT guaranteed on the main queue — hop before any UI work.
            guard CometChatUIKit.getLoggedInUser() == nil else {
                DispatchQueue.main.async { showChat() }
                return
            }
            CometChatUIKit.login(uid: uid) { loginResult in
                switch loginResult {
                case .success:            DispatchQueue.main.async { showChat() }
                case .onError(let error): // surface it — do not render on failure
                    break
                @unknown default: break
                }
            }
        case .failure(let error):
            break                      // usually a wrong Region or App ID
        }
    }
}
```
> **Which UID?** `login()` needs a user that ALREADY EXISTS — it does not create one. ASK, or take one from Dashboard → **Users**. Never invent a UID and never suggest remembered "classic sample" UIDs; the only tentative suggestion allowed is `cometchat-uid-1`, labelled "if this is a fresh app."
> **Login result is an enum, not an error-first callback:** `ApiStatus.success(User)` / `.onError(CometChatException)`. Handle `@unknown default`.
> **UI work belongs on the main queue** — the callbacks are not guaranteed to be.

## Component / API map (BAKED closed list — all catalog-verified)
Init/auth: `CometChatUIKit`, `UIKitSettings`.
Core surface: `CometChatConversations`, `CometChatMessageHeader`, `CometChatMessageList`, `CometChatCompactMessageComposer`.
Wired affordances: `CometChatThreadedMessageHeader`, `CometChatSearch`.
Grow set (on request): `CometChatUsers`, `CometChatGroups`, `CometChatGroupMembers`, `CometChatCallLogs`, `CometChatIncomingCall`.
> **Never emit:** `CometChatMessages`, `CometChatUsersWithMessages`, `CometChatGroupsWithMessages`, `CometChatConversationsWithMessages`, `CometChatAddMembers`, `CometChatMessageHeaderOption` — all v4 or non-existent. Anything not in this list → check `catalogs/ios-v5.json` before you write it.

## Hot-path API (BAKED — the golden path needs NO fetch)
- `CometChatConversations`: `set(onItemClick:)` (push the chat screen) · `set(conversationRequestBuilder:)` (scope the list) · `onSearchClick` (**property**, not a setter) · `set(subtitleView:)` / `set(trailView:)`.
- `CometChatMessageHeader` / `CometChatMessageList` / `CometChatCompactMessageComposer`: `set(user:)` **or** `set(group:)` — exactly one · `set(controller:)` on all three.
- **Thread scoping — the LIST takes its parent in the SAME call as its target.** `CometChatMessageList.set(user:parentMessage:withParent:)` (or `set(group:parentMessage:)`). A separate `set(user:)` followed by `set(parentMessageId:)` does NOT scope the list: the first call already built a request for the whole conversation, so the thread screen renders the entire conversation with the parent in it. The COMPOSER is different — `set(user:)` then `set(parentMessageId:)`. The header takes `set(parentMessage:)`. **Three components, three shapes** — verified against the shipped 5.1.22 interface by compiling each.
- Styles are **properties**, not setters: `conversations.avatarStyle = …`, `.badgeStyle`, `.dateStyle`, `.receiptStyle`, `.statusIndicatorStyle`, `.typingIndicatorStyle`.
> Exhaustive API or any other component → fetch its `.md` twin via `references/docs-map.md`. **Never** read the `.swiftinterface` or guess from memory.

## Golden path — the production-ready CORE surface
Setup → init/login (guarded) → a `CometChatConversations` list inside a `UINavigationController` → `set(onItemClick:)` pushes **your own** `MessagesVC` composing header + list + composer. This composition and its constraints are **verified on a simulator**; the five rules below are what the runtime gate actually checks, and each one is a real failure that compiles cleanly.

```swift
// List → chat screen. An unwired list is the iOS form of a dead-end affordance.
let conversations = CometChatConversations()
let nav = UINavigationController(rootViewController: conversations)
conversations.set(onItemClick: { [weak nav] conversation, _ in
    let messages = MessagesVC()
    messages.user  = conversation.conversationWith as? CometChatSDK.User   // exactly one is
    messages.group = conversation.conversationWith as? CometChatSDK.Group  // non-nil. Qualify:
                                                    // SwiftUI has its own `Group`.
    nav?.pushViewController(messages, animated: true)
})
```

```swift
final class MessagesVC: UIViewController {
    var user: CometChatSDK.User?
    var group: CometChatSDK.Group?

    private lazy var headerView: CometChatMessageHeader = {
        let v = CometChatMessageHeader()
        v.translatesAutoresizingMaskIntoConstraints = false
        if let user { v.set(user: user) } else if let group { v.set(group: group) }
        v.set(controller: self)                      // REQUIRED — see rule 2
        return v
    }()
    private lazy var messageListView: CometChatMessageList = {
        let v = CometChatMessageList()
        v.translatesAutoresizingMaskIntoConstraints = false
        if let user { v.set(user: user) } else if let group { v.set(group: group) }
        v.set(controller: self)
        return v
    }()
    private lazy var composerView: CometChatCompactMessageComposer = {
        let v = CometChatCompactMessageComposer()
        v.translatesAutoresizingMaskIntoConstraints = false
        if let user { v.set(user: user) } else if let group { v.set(group: group) }
        v.set(controller: self)
        return v
    }()

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .systemBackground
        navigationController?.setNavigationBarHidden(true, animated: false)   // rule 5
        [headerView, messageListView, composerView].forEach(view.addSubview)
        NSLayoutConstraint.activate([
            headerView.topAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor),   // rule 3
            headerView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            headerView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            headerView.heightAnchor.constraint(equalToConstant: 50),

            messageListView.topAnchor.constraint(equalTo: headerView.bottomAnchor),
            messageListView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            messageListView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            messageListView.bottomAnchor.constraint(equalTo: composerView.topAnchor),       // rule 4

            composerView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            composerView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            composerView.bottomAnchor.constraint(equalTo: view.safeAreaLayoutGuide.bottomAnchor), // rule 3
        ])
    }

    override func viewWillDisappear(_ animated: Bool) {
        super.viewWillDisappear(animated)
        navigationController?.setNavigationBarHidden(false, animated: true)   // rule 5
    }
}
```

> **Swift concurrency: several kit initialisers are `@MainActor`-isolated** (`CometChatUsers` among them). Any factory method that constructs kit components must be `@MainActor` too, or the build fails with *"call to main actor-isolated initializer … in a synchronous nonisolated context"*. Inside a `UIViewController` this is free — it is already main-actor — so it only bites in a `static`/`enum` factory.
> **The message header has NO tap callback.** `CometChatMessageHeader` exposes no `onItemClick`; its only interactive surface is `set(options:)` taking `[CometChatPopupMenu.MenuItem]`. So "tap the header to open details" is not a thing on iOS — a details or members screen is an overflow **menu item** you add.

**The five rules — each one compiles fine and fails at runtime:**
1. **One target, never both.** `conversationWith` is a `User` **or** a `Group`; pass the same single target to all three components. Two targets, or none, and the screen loads empty.
2. **`set(controller:)` on every component — omitting it CRASHES the app.** No React analogue: it hands the kit a controller to present its OWN sub-screens from. Long-press a message without it and the process dies (`EXC_BREAKPOINT`, nil force-unwrap in `MessagePopupViewController.buildUI`). Not a no-op, not a degraded mode — a crash on a gesture users perform within minutes. Call it on the header, the list AND the composer.
   **Be precise about why, because this was measured.** Omitting it does *not* break rendering or list→chat navigation: the harness ran a fixture with it removed everywhere and got a byte-identical surface (393x750) plus a passing navigation step. What is genuinely unverified is the kit-presented sub-screens above — driving those needs an element the kit ships no accessibility identifier for. So follow the docs and call it, but do **not** tell a user their surface will break without it.
3. **Pin both to the SAFE AREA — never the composer to the keyboard.** Header to `safeAreaLayoutGuide.topAnchor`, composer to `safeAreaLayoutGuide.bottomAnchor`, as the published recipe shows. it does its OWN keyboard adjustment; pinning it to `keyboardLayoutGuide` double-applies it and the message list collapses to height 0 the moment the keyboard rises (measured — `references/layout.md`).
4. **Divide the space explicitly.** Header fixed height, composer at the bottom, list filling between — so the list scrolls internally instead of growing its parent. A list with no bottom constraint collapses; that is the single most common broken surface.
5. **One navigation bar — own it on the NAVIGATION CONTROLLER.** The kit header carries its own title and back control, so a visible host bar means two headers. Hiding it in the message screen's `viewDidLoad` is what the docs publish and is NOT enough: it never runs again, and on a push the outgoing screen's `viewWillDisappear` restore lands after the incoming hide, so the bar returns and the pane loses 91pt (measured). Use a `UINavigationControllerDelegate` — `references/layout.md`.

> **Surface errors — the list components fail silently otherwise.** `set(onError:)` on the conversation list and message list, or assign `errorStateView` / `errorStateTitleText` (inherited from `CometChatListBase`). Without it a failed fetch renders an empty list indistinguishable from "no conversations yet", leaving the user nothing to act on.
> ```swift
> conversations.set(onError: { error in /* surface it — do not swallow */ })
> ```
> **Wire or hide every default-on affordance.** `CometChatConversations` HIDES its search entry by default (`hideSearch` is true on `CometChatListBase`). Assigning `onSearchClick` alone renders NOTHING — measured: 0 search fields. To ship search you need BOTH `conversations.hideSearch = false` and `conversations.onSearchClick = { … }` (which then shows 1 search field); wire it to `CometChatSearch` or leave search off deliberately. `CometChatMessageList` shows a thread indicator that dead-ends until `set(onThreadRepliesClick:)` opens a thread screen. Anything you PRESENT modally owns its own dismissal; a pushed screen gets its back control from the navigation controller for free.
> **Scope the list to the request.** A 1:1-only ask should not show the app's seeded groups — use `set(conversationRequestBuilder:)` with `ConversationRequest.ConversationRequestBuilder(limit: 30).setConversationType(conversationType: .user)` (`.group` for groups-only). Note the method is **`setConversationType(conversationType:)`**, not `set(conversationType:)`, and the cases are `.user` / `.group` / `.none` — there is **no `.both`**; omit the call entirely to keep both.
> **Grows on request → the full app.** Users/groups tabs, group details, call logs, threads, calls — `cometchat-ios-placement` (composition) and `cometchat-ios-features` (per-feature).

## Deep references (load ONLY when the task needs them)
- `references/setup-credentials.md` — detect, `Secrets.xcconfig` → `Info.plist` → `Bundle.main`, `Info.plist` usage descriptions, version_conflict, prod auth token.
- `references/swiftui.md` — where `init → login` goes per lifecycle, and showing a UIKit-only component from SwiftUI.
- `references/docs-map.md` — intent → the exact docs `.md` twin to fetch, plus the SDK-fallback section. **Never** read the `.swiftinterface`; never answer API from memory.
- `references/layout.md` — the iOS sizing standard (safe area · keyboard layout guide · explicit vertical division), the five rules above in depth, and why each fails at runtime rather than compile time.
- `references/anti-patterns.md` — the v4-carryover phantoms, the two-parent-API thread trap, missing `set(controller:)`, and the wrong-call-form class (styles are properties).
- `references/troubleshooting.md` — symptom → cause → fix (blank screen, list renders but taps do nothing, composer hidden by the keyboard, two headers, replies never send).

## Common pitfalls (top 5 — full list in `references/anti-patterns.md`)
**Every kit component is a `UIViewController`, never a `UIView`** — `addSubview(component)` or `component.topAnchor` does not compile; push it, or embed it with `addChild` + constrain `component.view` + `didMove(toParent:)` (see `references/layout.md`) · emitting a v4 composite · omitting `set(controller:)` · composer pinned to `keyboardLayoutGuide` instead of the safe area (double-applies the kit's own keyboard handling — see rule 3) · rendering before `login()` resolves.

## Verify it works
Build and run → `init` then `login` both resolve → the conversation list renders full-screen (not a sliver) → tap a conversation → the chat screen pushes and shows header, messages and composer → tap the composer and confirm **it rises above the keyboard** → send a message and see it appear → back returns to the list. A blank screen means something rendered before `login()` resolved, or the Region/App ID is wrong. A list whose taps do nothing means `set(onItemClick:)` was never wired; affordances that render but do nothing when tapped mean `set(controller:)` was omitted.

## Explain what you built (REQUIRED close)
After it builds, tell the user briefly: **(1) what I wired** (3–5 bullets, NAME the files); **(2) decisions & why**, flagging dev-only as dev-only (the **Auth Key** is dev-only → server-minted auth token for production; the `<uid>` you used); **(3) what I did NOT touch** (additive — their navigation, auth and styling are intact). Then **offer these THREE options as a selectable choice and WAIT — do not auto-continue:**
- **① Add another feature** → first read what is already wired and ASK which dashboard-gated features are on, then suggest only the GAP (calls · search · threads · push · AI) → `cometchat-ios-features` / `cometchat-ios-calls`.
- **② Customize theming** → ask whether they have a brand/preset or want to talk through options → `cometchat-ios-customization`.
- **③ Test it manually** → do nothing further; hand it back.
