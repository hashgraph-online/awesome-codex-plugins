# Message chrome on iOS — avatar and sender name

### Avatar and sender name on every message (BAKED — verified vs 5.2.3)
What to check and why: `cometchat-onboarding/references/clone-mode.md` → *Message chrome*. This is the iOS (UIKit/Swift) how-to.

**Kit default (5.2.3 `CometChatMessageList` cell code, unchanged since 5.1.22):**
- Own messages (`messageAlignment = .standard`, right side): no avatar, no name.
- Others' messages in a **group**: avatar + name (name only on the first row of a multi-attachment batch).
- Others' messages in a **1:1** chat: no avatar (`hideAvatar` is `Bool?`, default `nil`, and `nil` means hidden in 1:1) and **never a name**: for `receiverType == .user` the list calls `cell.hide(headerView: true)` AFTER applying your template's `headerView`, so no flag or header slot can show a name in 1:1.
- With `.leftAligned`, your own group messages get the kit's header, which reads "You", not your name.

**Do this whenever the target shows avatars/names on every message (Slack, Discord, Teams) — it is the default fix, not an option to offer.** It covers own and others' messages in 1:1 and group chats:
1. `set(messageAlignment: .leftAligned)` — every row is drawn as "incoming", so every row gets the avatar column.
2. `hideAvatar = false` — the explicit `false` is what turns the avatar on in 1:1 chats.
3. Wrap every default template: `headerView` = the sender's real name (groups), and in 1:1 chats put the same name label above the default `contentView` (the only per-message slot the kit does not hide in 1:1).

```swift
import UIKit
import CometChatSDK
import CometChatUIKitSwift

extension CometChatMessageList {
    /// Avatar + sender name on every message: own and others', 1:1 and group.
    func showSenderOnEveryMessage() {
        set(messageAlignment: .leftAligned) // every row is drawn "incoming": avatar column on all rows
        hideAvatar = false                  // nil (the default) hides it in 1:1; false shows it
        let defaults = CometChatUIKit.getDataSource()
            .getAllMessageTemplates(additionalConfiguration: getAdditionalConfiguration())
        set(templates: defaults.map { template in
            if template.category == "action"
                || template.category == "call" { return template } // centered rows, no avatar
            var t = template
            // Groups: your real name instead of the kit's "You".
            t.headerView = { message, _, _ in senderNameLabel(message) }
            // 1:1: the kit always hides the header row, so put the name above the content.
            let content = template.contentView
            t.contentView = { message, alignment, controller in
                guard let inner = content?(message, alignment, controller) else { return nil }
                guard message?.receiverType == .user else { return inner }
                let stack = UIStackView(arrangedSubviews: [senderNameLabel(message), inner])
                stack.axis = .vertical
                stack.alignment = .leading
                stack.spacing = 2
                return stack
            }
            return t
        })
    }
}

private func senderNameLabel(_ message: BaseMessage?) -> UILabel {
    let label = UILabel()
    label.text = message?.sender?.name
    label.font = CometChatTypography.Caption1.medium
    label.textColor = CometChatTheme.textColorPrimary
    return label
}
// messageList.set(group: group) / set(user: user); messageList.showSenderOnEveryMessage()
```
- **Order:** `set(templates:)` REPLACES every template. Call this first, then `add(templates:)` for any custom bubble (e.g. the huddle Join bubble in `cometchat-ios-calls/references/huddle.md`), or the custom one is lost.
- **Avatar is not a slot:** `CometChatMessageTemplate` has no leading/avatar view. The kit draws the avatar from `message.sender` (image or initials); you can only show or hide it. A fully custom avatar means `bubbleView`, which replaces the whole row and drops swipe-to-reply, context menu, receipts and reactions — don't.
- **1:1 name sits inside the bubble** (it is part of the content). Team-app clones usually clear the bubble background anyway (`message-bubble-styling` docs); then it reads like a normal name line.
- **Once per run** isn't reachable: a template closure gets one message, not the previous one (L4). The kit only groups multi-attachment batches.
- **Docs drift (still on the live page, 2026-10-15):** the docs' message-list page names the type `MessageAlignment` with `.left` and says `hideAvatar` defaults to `false`; the 5.2.3 API is `MessageListAlignment` with `.standard` / `.leftAligned`, and `hideAvatar` is `Bool?` (default `nil`). `.left` does not compile.
- **Verified 2026-10-15:** source of `cometchat-uikit-ios` tag 5.2.3 (`CometChatMessageList.swift` cell setup, `CometChatMessageBubble.swift`, `CometChatMessageTemplate.swift`) and the 5.2.3 binary `.swiftinterface`; this block type-checks with `swiftc` (Swift 5, Swift 6, Swift 6 + default MainActor isolation) against the 5.2.3 / Chat SDK 4.1.10 / Calls SDK 5.0.4 binaries. Not yet run on a device: open a 1:1 and a group and check your own and others' rows.
