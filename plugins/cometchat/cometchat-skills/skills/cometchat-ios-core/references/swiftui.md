# SwiftUI, and where `init → login` actually goes

The kit is **UIKit-only**: every component is a `UIView`/`UIViewController`. It works in a SwiftUI
app, but nothing about that is automatic, and the golden path in `SKILL.md` shows the code without
saying where it lives. This file says where.

> Verified on 5.1.22 by building and running a SwiftUI app from scratch: login succeeded and
> `CometChatConversations` rendered with live data.

## Where init and login go

`init → login` must complete **before** any component renders, and it must run **once** for the
process — not per view. SwiftUI views are values and their bodies re-evaluate freely, so a `.task`
or `.onAppear` on a view is the wrong home for it.

| lifecycle | put `init → login` in |
|---|---|
| **UIKit** (`AppDelegate` + `SceneDelegate`) | `application(_:didFinishLaunchingWithOptions:)` |
| **SwiftUI** (`@main struct App`) | an `AppDelegate` attached with `@UIApplicationDelegateAdaptor` |

A stock Xcode project today has **no `AppDelegate` and no `SceneDelegate`** — it is a SwiftUI
`App`. Adding the adaptor is how you get a launch hook back.

```swift
final class AppDelegate: NSObject, UIApplicationDelegate {
    func application(_ app: UIApplication,
                     didFinishLaunchingWithOptions opts: [UIApplication.LaunchOptionsKey: Any]? = nil) -> Bool {
        CometChatUIKit.initFromSettings { _, _ in                    // attribution — see setup-credentials §6
            CometChatUIKit.init(uiKitSettings: settings) { result in
                if case .success = result {
                    CometChatUIKit.login(uid: uid) { _ in
                        DispatchQueue.main.async { AppState.shared.ready = true }
                    }
                }
            }
        }
        return true
    }
}

@main
struct MyApp: App {
    @UIApplicationDelegateAdaptor(AppDelegate.self) var delegate
    @ObservedObject private var state = AppState.shared
    var body: some Scene {
        WindowGroup {
            if state.ready { ChatScreen() }        // render ONLY after login resolves
            else { ProgressView() }
        }
    }
}
```

`AppState` is any `ObservableObject` with a `ready` flag. Gating on it is not optional: rendering a
component before login resolves is the silent-failure case the ordering rule exists to prevent.

## Showing a UIKit component from SwiftUI

Wrap it in `UIViewControllerRepresentable`. Wrap it in a `UINavigationController` too — the kit
composes by navigation (list pushes the message pane), so without one the push has nowhere to go.

```swift
struct ConversationsView: UIViewControllerRepresentable {
    func makeUIViewController(context: Context) -> UINavigationController {
        let list = CometChatConversations()
        // wire onItemClick here exactly as in the golden path
        return UINavigationController(rootViewController: list)
    }
    func updateUIViewController(_ vc: UINavigationController, context: Context) {}
}
```

**Qualify `CometChatSDK.User` / `CometChatSDK.Group` in any file that imports SwiftUI.** SwiftUI
declares its own `Group`, so a bare `as? Group` is `'Group' is ambiguous for type lookup` — a
guaranteed compile error in the wrapper file this page tells you to write. A live test hit exactly
that. Host apps also very often define their own `User` model, so qualify both:

```swift
vc.user  = conversation.conversationWith as? CometChatSDK.User
vc.group = conversation.conversationWith as? CometChatSDK.Group
```

The golden path in `SKILL.md` and the recipe in `layout.md` are already written this way; keep them
qualified rather than "tidying" the module prefix away.

`NavigationStack` does **not** substitute for this. The kit pushes with
`UINavigationController.pushViewController`, which a SwiftUI `NavigationStack` does not provide.

Rule 5 still applies inside that navigation controller — see `layout.md`. The coordinator goes on
the `UINavigationController` you create in `makeUIViewController`, and something must hold it: the
`delegate` is weak, and a coordinator created inline is deallocated immediately.
