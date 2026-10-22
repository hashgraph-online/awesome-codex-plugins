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

**Cause:** `CometChatSDK` is not pinned to the exact version the binary kit was compiled
against, or (on 5.1.19) `CometChatCallsSDK` is absent — the shipped interface hard-imports it,
so even a chat-only app fails to compile without it.

**Fix:** pin both exactly. See `anti-patterns.md` §5.

## The group-members screen cannot be dismissed

**Symptom:** you push `CometChatGroupMembers`, it renders correctly, and then there is no way back
— the kit's Cancel control does nothing, a wired `set(onBack:)` never fires, and edge-swipe back is
inert.

**Status: reported and NOT reproduced by us.** An acceptance pass measured it (Cancel
`action=didTapBackButton` inert across 3 taps, `set(onBack:)` instrumented and never called); an
attempt to reproduce it in the review harness did not get far enough to confirm or refute. So there
is no verified fix here, and none is invented: we do not know whether the fault is the recipe or
the kit.

**What to do:** treat "can the user leave this screen?" as a test you run, not a property you
assume. If you hit it, give yourself a dismissal path you control — your own bar button, or
presenting rather than pushing — and please report the exact flow so this can be pinned down.
