# layout — the mobile sizing standard (bounded height, safe area, keyboard)

The Flutter instance of the pack's reflow-free-surface standard. The web recipe (`100dvh`, `min-height:0`
columns, prepared ancestor chain) does NOT apply here; the principle does: **the kit's list widgets expand
to fill their parent, so the parent must supply a bounded height — never let content drive it.**

## The four invariants

**1. Bounded height for every list.** `CometChatConversations`, `CometChatMessageList`, `CometChatUsers`,
`CometChatGroups`, `CometChatGroupMembers` and `CometChatSearch` all want to fill their parent. Inside a
`Column`, wrap them in `Expanded` (or `Flexible`); otherwise Flutter throws
*"RenderFlex children have non-zero flex but incoming height constraints are unbounded"* — or the list
collapses to zero height.
```dart
Widget messagePane(User user) => Column(children: [
      CometChatMessageHeader(user: user),
      Expanded(child: CometChatMessageList(user: user)),   // REQUIRED — bounds the list
      CometChatMessageComposer(user: user),
    ]);
```

**2. Never nest the surface in an unbounded scroll parent.** A `SingleChildScrollView`, a `ListView`, or a
`Column` inside one gives its children *infinite* height, so a kit list inside it throws or renders
nothing. If chat must sit inside a scrolling page, give it a **fixed** height (`SizedBox(height: 480)`) or
a sized cell — a content-driven box is the defect, not the kit.

**3. `Scaffold` + `SafeArea`.** The surface belongs in a `Scaffold` (it supplies the `Material` ancestor the
kit's widgets need) with `SafeArea` so the composer clears the home indicator and the header clears the
notch. A bare `Container` at the root is the usual cause of "the composer is under the home bar".

**4. Keyboard avoidance — leave `resizeToAvoidBottomInset` alone.** It defaults to `true`, which is what
keeps `CometChatMessageComposer` above the keyboard. Setting it to `false`, or placing the surface inside a
widget that swallows the inset, hides the input the moment the user types. If the composer is covered:
check for `resizeToAvoidBottomInset: false`, a nested `Scaffold`, or a manual `MediaQuery.viewInsets` hack.

## No load-transition reflow
The kit ships its own loading and empty states, so give it the full box immediately and let it render its
loader **inside** that box. Do not gate the whole screen behind your own placeholder→chat swap sized
differently from the final surface — that is what makes the UI jump when messages arrive. (The init/login
gate in `lifecycle.md` is different and correct: it runs *before* the chat screen exists at all.)

## Embedded / modal placements
A bottom sheet, dialog, or embedded panel must still supply a bounded height — `showModalBottomSheet` with
a `SizedBox(height: MediaQuery.of(context).size.height * 0.9)`, or a `Container` with a fixed height.
Recipes: `cometchat-flutter-v6-placement`.
