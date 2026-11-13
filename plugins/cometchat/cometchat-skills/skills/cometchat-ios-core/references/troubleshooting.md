# Troubleshooting — symptom → cause → fix

Every entry here is a RUNTIME failure that compiled cleanly. That is the character of this kit:
the compiler will not catch composition mistakes.

## Blank screen, nothing renders

**Cause:** `login()` ran before `init()` finished, or it failed and nothing surfaced the error.
`login()` called early fails SILENTLY.

**Fix:** nest them — never sequence with a timer. Render only after login succeeds:

```swift
CometChatUIKit.init(uiKitSettings: settings) { result in
    switch result {
    case .success:
        CometChatUIKit.login(uid: uid) { loginResult in
            switch loginResult {
            case .success:            DispatchQueue.main.async { mountChat() }
            case .onError(let e):     print("login failed:", e.errorDescription)
            @unknown default:         break
            }
        }
    case .failure(let e): print("init failed:", e.localizedDescription)
    }
}
```

Also check credentials actually resolved — an unsubstituted xcconfig value arrives as the
literal `$(COMETCHAT_APP_ID)`, not nil (see `setup-credentials.md`).

## The list renders but tapping a row does nothing

**Cause:** `set(onItemClick:)` was never wired. The rows are real; the destination is not.

**Fix:** push the message screen from the click handler, taking exactly one of user/group —
see `layout.md`.

## Tapping the composer makes the conversation disappear

**Cause:** the composer is pinned to `view.keyboardLayoutGuide.topAnchor`. The kit's composer
already adjusts for the keyboard, so this double-applies it — the message list collapses to height
0 and the composer's own text field goes with it, leaving only the attachment/mic/send icons
jammed under the header.

**Fix:** pin the composer to `view.safeAreaLayoutGuide.bottomAnchor`, as the published recipe
shows. The kit handles the keyboard from there.

## Two navigation bars stacked on the message screen

**Cause:** `CometChatMessageHeader` carries its own title and back control, and the
`UINavigationController` bar is still visible above it.

**Fix:** hide the nav bar on the message screen in `viewDidLoad`, restore it in
`viewWillDisappear`. Do not hide it globally.

## The message pane is a thin strip / everything is squashed at the top

**Cause:** the list is not pinned both top AND bottom, so it sizes to its intrinsic content
instead of filling the space between header and composer.

**Fix:** add both constraints (Rule 4 in `layout.md`). Verify by opening a conversation, not by
looking at the list screen — the collapse is only visible on the pushed screen.

## An empty list that might be an error

**Cause:** no `set(onError:)`, so a failed fetch looks exactly like an empty account.

**Fix:** wire `set(onError:)` on every list component and surface the failure.

## Replies render but never send

**Cause:** the thread's parent was set through two different APIs — see `anti-patterns.md` §4.

**Fix:** set the parent one way, per the docs for that component, then actually send a reply to
confirm.

## Link errors / missing symbols after adding the package

**Cause:** a hand-added `CometChatSDK` pin fights the kit's own rule (5.2.1+ declares
`CometChatSDK` from 4.1.10), or the kit is older than 5.2.3: 5.1.19 to 5.1.22 fail to compile
without `CometChatCallsSDK`, and 5.2.0 to 5.2.2 build but crash at launch with
`Library not loaded: @rpath/CometChatCallsSDK.framework`.

**Fix:** depend on `CometChatUIKitSwift` alone, Up to Next Major from 5.2.3, and remove any exact
`CometChatSDK` pin. See `anti-patterns.md` §5 and `install.md`.

## The group-members screen cannot be dismissed

**Symptom:** you push `CometChatGroupMembers`, it renders correctly, and then there is no way back
— the kit's Cancel control does nothing, a wired `set(onBack:)` never fires, and edge-swipe back is
inert.

**Cause (found in the kit source):** through 5.1.22, `CometChatGroupMembers.didTapBackButton()`
only called `self.dismiss(animated:)`, which does nothing on a PUSHED controller, and never called
`onBack`. **Fixed in 5.2.x** (5.2.3 `CometChatGroupMembers.swift` `didTapBackButton`): it runs
`onBack` when set, otherwise pops the navigation stack, and only dismisses when presented.

**What to do:** be on 5.2.3+ (see `install.md`). Still run "can the user leave this screen?" as a
test, since the fix is source-verified, not yet device-run.
