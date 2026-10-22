# The iOS sizing standard — why each rule exists

> Every rule below was measured on a simulator by the native review harness (iPhone 16 / iOS
> 18.2, kit 5.1.22), not reasoned across from the web UI Kit. Where a claim is unverified, it
> says so.

v5 ships **no composite chat component**. The host composes `CometChatMessageHeader` +
`CometChatMessageList` + `CometChatCompactMessageComposer` and owns the layout. That means the sizing
below is YOUR responsibility — the kit will not correct it, and every failure here is a RUNTIME
failure that compiles perfectly.

## Rule 0 — a component is a `UIViewController`, so constrain `component.view`

Every kit component (`CometChatConversations`, `CometChatMessageList`, `CometChatGroups`, …)
subclasses `UIViewController`, **not** `UIView`. Treating one as a view does not compile:

```
error: value of type 'CometChatConversations' has no member 'translatesAutoresizingMaskIntoConstraints'
error: cannot convert value of type 'CometChatConversations' to expected argument type 'UIView'
error: value of type 'CometChatConversations' has no member 'topAnchor'
```

Push or present it, or — to place it inside a screen you own — embed it as a child view
controller and constrain its `.view`:

```swift
let conversations = CometChatConversations()
addChild(conversations)                                  // BEFORE adding the view
conversations.view.translatesAutoresizingMaskIntoConstraints = false
container.addSubview(conversations.view)                 // the .view, not the component
NSLayoutConstraint.activate([
    conversations.view.topAnchor.constraint(equalTo: container.topAnchor),
    conversations.view.leadingAnchor.constraint(equalTo: container.leadingAnchor),
    conversations.view.trailingAnchor.constraint(equalTo: container.trailingAnchor),
    conversations.view.bottomAnchor.constraint(equalTo: container.bottomAnchor),
])
conversations.didMove(toParent: self)                    // AFTER; omitting it breaks
                                                         // viewWillAppear/viewDidAppear,
                                                         // so the child never loads data
```

Unlike the rules below, this one fails at COMPILE time — which is why it belongs first: the
sizing rules only matter once the thing builds. Full treatment in `references/anti-patterns.md`.

## Rule 1 — exactly one target

`conversationWith` is a `User` **or** a `Group`, never both. Set one:

```swift
if let user { list.set(user: user) } else if let group { list.set(group: group) }
```

Setting both is not a compile error; it produces a surface bound to the wrong conversation.

## Rule 2 — `set(controller:)` is REQUIRED. Omitting it CRASHES the app.

Call `set(controller: self)` on the header, the list and the composer. It hands the kit a
controller to present its OWN sub-screens from — the action sheet behind a long-press, the media
picker, the details screen.

**Measured: omitting it is not a degradation, it is a crash.** Long-press any message in a surface
built without `set(controller:)` and the app dies:

```
EXC_BREAKPOINT (SIGTRAP) — nil force-unwrap
  MessagePopupViewController.buildUI()
  ← CometChatMessageList.onCellLongPressGestureRecognized
  ← CometChatMessageBubble.onLongPressEnded
```

The kit force-unwraps the presenting controller it was never given. There is no error, no no-op,
no degraded mode — the process terminates on a gesture any user will perform within minutes.

**An earlier version of this file said the opposite.** It reported that omitting `set(controller:)`
"affects neither rendering nor primary navigation" and called the kit's presented sub-screens
"genuinely untested" — because our own gate only tapped, and a tap never reaches this path. The
sub-screens were testable all along; the answer is a crash. `Fixtures/broken-no-controller` scored
WORKING for the entire life of this project while modelling an app that dies on first long-press.
The gate now long-presses and detects process death, so the fixture fails as it always should have.

The lesson is the one this pack keeps relearning: an untested path reported as "probably fine" is a
claim, not a measurement. Say "untested" and stop there, or test it.

## Rule 3 — pin to the safe area, top AND bottom

```swift
headerView.topAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor)
composerView.bottomAnchor.constraint(equalTo: view.safeAreaLayoutGuide.bottomAnchor)
```

Both anchors come straight from the published recipe. **Do not pin the composer to
`view.keyboardLayoutGuide.topAnchor`.** `CometChatCompactMessageComposer` does its own keyboard
adjustment, so that double-applies the offset. Measured on iPhone 16 / iOS 18.2 with the keyboard
raised:

<!-- Provenance: the table below was measured against `CometChatMessageComposer`, which the golden
     path used before it moved to the compact composer. The rule carries over because the compact
     composer self-adjusts the same way — it registers
     `UIResponder.keyboardWillChangeFrameNotification` and offsets itself (source-verified on
     master-v5). The numbers are NOT a re-measurement of the compact composer; re-measure before
     quoting them as such. -->


| | safe-area pin (correct) | keyboardLayoutGuide pin |
|---|---|---|
| message list | `(0, 109, 393, 267)` — survives | **height 0 — gone** |
| composer internal stack | on the keyboard top | **`(0, -249, 393, 0)`** |

The user taps to type and the entire conversation disappears, along with the text field they were
about to type into. It compiles, and it looks perfect until that first tap.

This skill previously taught the keyboardLayoutGuide pin as a "hardening delta" over the docs, and
asserted it was simulator-verified. That assertion was false: no gate raised the keyboard, so
nothing could contradict it. The gate now taps the composer and grades whether a list survives
above the keyboard (`Fixtures/broken-keyboard-double-pin` is the standing regression case).

## Rule 4 — divide the vertical space EXPLICITLY

The list must be pinned top and bottom so it scrolls internally instead of growing its parent:

```swift
messageListView.topAnchor.constraint(equalTo: headerView.bottomAnchor),
messageListView.bottomAnchor.constraint(equalTo: composerView.topAnchor),
```

Without both, the surface collapses to its intrinsic content height. **This is the defect the
harness catches most often**: a collapsed pane measured 10% of screen height where a correct one
measures ~90%. It compiles, it mounts, and a launch-only screenshot of the conversation list
looks perfectly fine — the collapse is one tap away, on the pushed screen.

## Rule 5 — one navigation bar, not two

`CometChatMessageHeader` carries its own title and back control. Left alone, `UINavigationController`
adds a second bar above it:

```swift
override func viewDidLoad() {
    super.viewDidLoad()
    navigationController?.setNavigationBarHidden(true, animated: false)
}
override func viewWillDisappear(_ animated: Bool) {
    super.viewWillDisappear(animated)
    navigationController?.setNavigationBarHidden(false, animated: true)   // restore for the list
}
```

Hide it on the message screen only, and restore it on the way out — hiding it globally strips
the conversation list's own bar.

## Navigation, not panes

The web kit's default is side-by-side. iOS composes by NAVIGATION: the conversation list
pushes the message pane. Wire selection or the list is a dead end:

```swift
conversations.set(onItemClick: { [weak nav] conversation, _ in
    let vc = MessagesVC()
    vc.user  = conversation.conversationWith as? CometChatSDK.User
    vc.group = conversation.conversationWith as? CometChatSDK.Group
    nav?.pushViewController(vc, animated: true)
})
```

## Surface errors

A failed load and an empty account render the SAME empty list. Wire `set(onError:)` or a
failure is indistinguishable from "no conversations yet".

### Own the bar centrally — the per-screen recipe does not survive real flows

The published recipe (hide in `viewDidLoad`, restore in `viewWillDisappear`) works for a single
push and breaks in three flows we measured:

| flow | result |
|---|---|
| activate the list's search field, then open a conversation | host bar returns |
| chat → thread | host bar returns — and on the THREAD screen that is what you want: it has no back control of its own (see below) |
| pop back thread → chat | chat screen ends with two headers |

Measured on the search flow: `(0,109,393,579)` becomes `(0,199,393,488)` — two headers, 91pt lost.

**Why the obvious fixes fail.** `viewDidLoad` runs once, so it cannot correct a later transition.
`viewWillAppear` cannot either: the INCOMING screen's `viewWillAppear` runs BEFORE the outgoing
screen's `viewWillDisappear`, so the restore lands last and clobbers the hide. `isMovingFromParent`
handles the pushes but not the pop-back.

**What works, measured, with no flash** — decide the bar on the navigation controller:

```swift
final class NavBarCoordinator: NSObject, UINavigationControllerDelegate {
    // Hide the bar ONLY on screens whose kit header has its own back control (your composed chat
    // screen). Do NOT hide it on a pushed thread screen: CometChatThreadedMessageHeader ships NO
    // back/close of its own (measured — its public surface is hideReceipt/hideBubbleHeader/
    // hideReplyCount/hideReplyCountBar/hideAvatar plus setters), and edge-swipe does not pop it.
    // Hiding the host bar there removes the ONLY exit and strands the user. Same rule for any
    // pushed kit list (CometChatGroupMembers etc.): keep the host bar, hide the KIT's — see the
    // placement skill.
    private func shouldHide(_ vc: UIViewController) -> Bool { vc is MessagesVC }   // your chat screens ONLY

    func navigationController(_ nav: UINavigationController, willShow vc: UIViewController, animated: Bool) {
        nav.setNavigationBarHidden(shouldHide(vc), animated: animated)
    }
    func navigationController(_ nav: UINavigationController, didShow vc: UIViewController, animated: Bool) {
        let want = shouldHide(vc)                       // re-assert ONLY if clobbered, so no flash
        if nav.isNavigationBarHidden != want { nav.setNavigationBarHidden(want, animated: false) }
    }
}
```

Hold the coordinator somewhere that outlives the push — `UINavigationController.delegate` is weak.
With it in place the message pane measures `(0,109,393,579)` through all four flows.

**Note on how this was found.** An earlier pass reported the defect with `CometChatSearch` as the
trigger; a fixture built around presenting and dismissing `CometChatSearch` measured clean every
time, and this file recorded it as unreproduced. The real trigger is activating the list's OWN
`UISearchController` — which is simply how a user reaches search, so the original report was right
about the symptom and wrong about the cause. `Fixtures/broken-navbar-after-search` is the standing
regression case, and the gate now asserts `navBars == 0` on the message pane, because the collapse
ratio cannot see this (488/852 = 57%, over the 50% minimum).
