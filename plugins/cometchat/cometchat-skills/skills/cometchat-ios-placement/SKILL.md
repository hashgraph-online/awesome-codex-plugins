---
name: cometchat-ios-placement
description: "Compose CometChat iOS screens into an app — navigation stack, tab bar, user/group pickers, group details, threads, and iPad. Use when the question is layout and navigation rather than a single component. Triggers: 'tab based chat ios', 'add a groups tab', 'open group details', 'thread screen ios', 'ipad split view cometchat'."
license: "MIT"
compatibility: "CometChatUIKitSwift 5.1.22 · iOS 15.1+"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat ios placement navigation tabs threads swift v5"
---

## Companion skills (read first)
- `cometchat-ios-core` owns the default surface (list → pushed chat screen) and the five layout rules. This skill ADDS composition beyond that one screen. The five rules still apply to EVERY screen you add.

## Use this skill when
"tab-based chat", "let people browse users and groups", "open group details", "add a thread screen", "make it work on iPad".

## The shape of an iOS CometChat app
`UITabBarController` (yours) → per tab a `UINavigationController` (yours) → a kit list → **push your own chat screen**. The kit supplies screens; **you own every container and every transition**. There is no composite component and no built-in tab shell.

## Recipes
**The kit's lists draw their OWN navigation bar — the host's `navigationItem` is unused.** Setting `navigationItem.rightBarButtonItems` (a "New Group" button is the first thing anyone adds) silently renders NOTHING: measured with the button installed and both bars inspected, the control never appears, and setting `hideNavigationBar = true` removes the visible bar, proving it is the kit's. Put custom controls in the kit's own affordances — `CometChatMessageHeader.set(options:)` for the header overflow menu, or assign the list components' `menus` property (`[UIBarButtonItem]?`) — there is **no** `set(menus:)` method; `menus` is a settable property, not a setter. Otherwise hide the kit bar and use your own — do not attach them to a `navigationItem` nobody draws.

**Tabs.** One `UINavigationController` per tab, each rooted at `CometChatConversations` / `CometChatUsers` / `CometChatGroups` / `CometChatCallLogs`. Every list's selection callback pushes your chat screen — wire all of them, or a tab dead-ends.

```swift
// Tab-based placement — wire each list's selection to the chat screen.
// set(onItemClick:) is TWO-arg on the lists: (item, indexPath). A one-arg `{ user in … }` does
// NOT compile ("expects 2 arguments, but 1 was used") — take the indexPath and ignore it.
let users = CometChatUsers()
users.set(onItemClick: { user, _ in openChat(user: user, group: nil) })

let groups = CometChatGroups()
groups.set(onItemClick: { group, _ in openChat(user: nil, group: group) })

// Global search — presented from the conversations list's onSearchClick property.
// CometChatSearch's result callbacks are assignable PROPERTIES, not setters — ASSIGN them
// (`search.onConversationClicked = …`). There is no setter form; wrapping either callback in a
// `set(...)` call does not compile (it resolves to a different overload). onConversationClicked
// is (Conversation, IndexPath); onMessageClicked is (BaseMessage).
let conversations = CometChatConversations()
conversations.onSearchClick = {
    let search = CometChatSearch()
    search.onConversationClicked = { conv, _ in
        self.dismiss(animated: false); openChatFromConversation(conv)
    }
    search.onMessageClicked = { msg in
        self.dismiss(animated: false); openChatFromMessage(msg)
    }
    self.present(search, animated: true)
}
```

**Users or groups → chat.** `CometChatUsers.set(onItemClick:)` gives a `User`; `CometChatGroups.set(onItemClick:)` gives a `Group`. Pass exactly one to your chat screen — the same single-target rule as core.

**Group details / members.** `CometChatMessageHeader` has **no tap callback** — no `onItemClick`. Its only interactive surface is `set(options:)` taking `[CometChatPopupMenu.MenuItem]`, so a details/members screen is an overflow **menu item** you add, not a tap on the title. From that action, push `CometChatGroupMembers` — **which has NO `init(group:)`; construct it `init()` then attach the group with the setter** (`let members = CometChatGroupMembers(); members.set(group: group)` — guessing `CometChatGroupMembers(group:)` fails to compile, "argument passed to call that takes no arguments"). Two more things about it are not obvious:

- **When PUSHED, hide the KIT's bar or the user is stranded.** The kit draws a modal-style bar whose Cancel calls `dismiss()` — a no-op on a pushed controller — and `set(onBack:)` never fires from it (diagnosed on a tab-bar app; the same control works when the component is PRESENTED as a sheet). So: `members.hideNavigationBar = true; members.title = "Members"` and let the HOST navigation bar provide Back — measured working, edge-swipe included. This is the inverse of the chat screen's rule 5: a pushed kit LIST keeps the host bar.
- **Kick, ban and scope-change are BUILT IN — do not hand-roll them.** `hideKickMemberOption` / `hideBanMemberOption` / `hideScopeChangeOption` all default to false, and tapping a row already presents the kit's own `CometChatScopeChange` sheet. Wiring your own `set(onItemClick:)` on top produces a DOUBLE presentation (measured). Only add `set(onItemClick:)` if you first hide the built-in options.

Adding members has **no component** — build a picker from `CometChatUsers` in selection mode and call `CometChat.addMembersToGroup(guid:groupMembers:bannedUIDs:onSuccess:onError:)` (SDK fallback; `docs-map.md`).

**Threads.** `CometChatMessageList.set(onThreadRepliesClick:)` pushes a thread screen: `CometChatThreadedMessageHeader` + a thread list + composer. **Thread scoping — the LIST takes its parent in the SAME call as its target.** `CometChatMessageList.set(user:parentMessage:withParent:)` (or `set(group:parentMessage:)`). A separate `set(user:)` followed by `set(parentMessageId:)` does NOT scope the list: the first call already built a request for the whole conversation, so the thread screen renders the entire conversation with the parent in it. The COMPOSER is different — `set(user:)` then `set(parentMessageId:)`. The header takes `set(parentMessage:)`. **Three components, three shapes** — verified against the shipped 5.1.22 interface by compiling each.

**Search.** `CometChatConversations.onSearchClick` (a property) presents `CometChatSearch`. Anything you PRESENT owns its dismissal; anything you PUSH gets a back control free.

**iPad.** `UISplitViewController` with the list as primary and your chat screen as secondary. The kit components fill what you give them, so each column still needs the core layout rules applied independently.

## Gotchas
- **Selection multiplies the dead-end risk.** Every list you add is another callback that must go somewhere.
- **Hide the host nav bar only on screens that use the kit header**, and restore it in `viewWillDisappear` — otherwise the rest of the app loses its bar.
- **Modals need explicit dismissal.** A presented screen with no way out is the iOS form of an unwired back button.

## Verify it works
Every tab reaches a chat screen; every pushed screen returns; every presented screen dismisses; the composer clears the keyboard on all of them; rotation and iPhone SE → Pro Max keep the surface full-bleed.
