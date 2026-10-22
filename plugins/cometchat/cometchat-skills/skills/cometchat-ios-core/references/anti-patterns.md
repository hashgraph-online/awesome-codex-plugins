# Anti-patterns — what does NOT exist, and what compiles but is wrong

> Catalog-verified against the shipped 5.1.22 `.swiftinterface`. If a symbol is not in
> `catalogs/ios-v5.json`, it does not exist in the installed kit — no matter where you saw it.

## 1. v4 composite components — they do not exist in v5

The single most damaging carry-over. These are **v4** names and are NOT in the v5 public API:

- `CometChatConversationsWithMessages`
- `CometChatUsersWithMessages`
- `CometChatGroupsWithMessages`
- `CometChatMessages`

They appeared on v5 documentation pages (tracked as **IOS-DOCS-001**), which is exactly why the
rule is "verify against the catalog", not "trust a code sample". v5 has **no composite** — the
host composes header + list + composer itself and owns the navigation. See `layout.md`.

If you find yourself reaching for a one-liner chat screen: there isn't one. That is the design.

## 2. Styles are PROPERTIES, not setters

The kit's API is setter-based and returns `Self`, so `set(...)` is the reflex — but styling is
not applied that way:

```swift
// wrong — no such setter
list.set(style: myStyle)

// right — assign the style property
list.style = myStyle
```

Guessing the call form is the most common compile failure. Fetch the component's `.md` twin via
`docs-map.md` and match the shape exactly.

## 3. `CometChatCallLogs` hands back `Any`

Unlike every other list component, five of its setters pass untyped values. Using them directly
does not compile — cast first:

```swift
callLogs.set(onItemClick: { callLog, _ in
    guard let log = callLog as? CallLog else { return }
    // …
})
```

This is a property of the shipped binary, not a docs error. Treat every `CometChatCallLogs`
callback parameter as `Any` until proven otherwise.

## 4. The thread trap — two parent APIs

A threaded reply view needs its parent message, and there is more than one way to hand it over.
Mixing them (setting a parent message id on one component and a parent message object on
another) yields a view that renders but never sends. Set the parent ONE way, on the component
the docs prescribe for that surface, and verify by actually sending a reply.

## 5. Assuming the SDK ships with the kit's dependencies resolved

The kit is a prebuilt binary xcframework compiled against ONE `CometChatSDK` version, and SPM
does **not** resolve that transitively. Pin the exact version. On 5.1.19 the shipped
`.swiftinterface` also hard-imports `CometChatCallsSDK`, so the Calls SDK must resolve for ANY
integration to compile — even a chat-only one that never places a call. 5.1.18 built without it,
so treat this as a packaging regression to state plainly, not as a design requirement to teach.

## 6. Answering API from memory

The kit's surface is largely un-prefixed (`User`, `Group`, `ConversationRequest`), so a
plausible-looking name is often a real type from a DIFFERENT module — which is why guessing here
fails silently rather than loudly. Always fetch the `.md` twin via `docs-map.md`. Never read the
`.swiftinterface` as a substitute for the docs; it is the catalog's source, not user-facing API
guidance.

## 7. Three things that are NOT like the web UI Kit

Read these before writing any Swift, or you will carry React habits across and they will compile but not work.
1. **The API is SETTER-based, not prop-based.** `view.set(user: user)`, `view.set(controller: self)` — chained, returning `Self`. There are no props.
2. **There is NO composite/all-in-one component.** `CometChatMessages`, `CometChatConversationsWithMessages` and friends are **v4** and do not exist in v5 — never emit them, in any file. You compose the chat screen from three components. (Some v5 doc pages still showed them; that is tracked as IOS-DOCS-001 and corrected upstream.)
3. **The default UX is a NAVIGATION STACK**, not side-by-side panes. The list pushes the chat screen. There is nothing to "collapse on mobile" — iOS is one-pane by construction.

## 8. Kit components are VIEW CONTROLLERS, not views

`CometChatConversations`, `CometChatMessageHeader`, `CometChatMessageList`,
`CometChatCompactMessageComposer`, `CometChatGroups`, `CometChatUsers`, `CometChatCallLogs` — every
one is a `UIViewController`. The names read like views, and `addSubview` + Auto Layout is the
reflex, but it does not compile:

```
error: value of type 'CometChatConversations' has no member 'translatesAutoresizingMaskIntoConstraints'
error: cannot convert value of type 'CometChatConversations' to expected argument type 'UIView'
error: value of type 'CometChatConversations' has no member 'topAnchor'
```

**Push or present it** (see the core skill's navigation stack), or, to place it inside a screen you
own, **embed it as a child view controller** — never `addSubview(component)`:

```swift
let conversations = CometChatConversations()
addChild(conversations)
conversations.view.translatesAutoresizingMaskIntoConstraints = false
container.addSubview(conversations.view)          // the .view, not the component
NSLayoutConstraint.activate([
    conversations.view.topAnchor.constraint(equalTo: container.topAnchor),
    conversations.view.leadingAnchor.constraint(equalTo: container.leadingAnchor),
    conversations.view.trailingAnchor.constraint(equalTo: container.trailingAnchor),
    conversations.view.bottomAnchor.constraint(equalTo: container.bottomAnchor),
])
conversations.didMove(toParent: self)             // omitting this breaks appearance callbacks
```

Constrain `component.view`; `addChild` before adding the view and `didMove(toParent:)` after, or
the child never receives `viewWillAppear`/`viewDidAppear` and its data never loads.
