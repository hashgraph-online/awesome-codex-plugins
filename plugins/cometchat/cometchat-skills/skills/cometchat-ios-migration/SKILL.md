---
name: cometchat-ios-migration
description: "Upgrade an existing CometChat iOS integration from UI Kit v4 to v5 — composite components removed, theming replaced, properties renamed. Triggers: 'upgrade cometchat ios to v5', 'migrate from v4 uikit ios', 'CometChatConversationsWithMessages not found'."
license: "MIT"
compatibility: "from CometChatUIKitSwift v4 → 5.1.22 · iOS 15.1+"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat ios migration upgrade v4 v5 swift"
---

## Companion skills (read first)
- `cometchat-ios-core` describes the v5 target state. This skill is the RECONCILIATION path to it. Build from the official guide — fetch `/ui-kit/ios/upgrading-from-v4` via `cometchat-ios-core/references/docs-map.md` — then apply the deltas below.

## Use this skill when
An existing v4 integration must move to v5, or a build breaks with `cannot find 'CometChatConversationsWithMessages' in scope` after an upgrade.

## The one change that dominates the migration
**v4's composite components are gone.** `CometChatMessages`, `CometChatUsersWithMessages`, `CometChatGroupsWithMessages`, `CometChatConversationsWithMessages` do not exist in v5, and neither do the configuration objects that fed them (`MessageHeaderConfiguration`, `MessageListConfiguration`, `MessageComposerConfiguration`).

That is not a rename — it is an inversion of ownership. v4 gave you one screen that did everything; v5 gives you three components and expects **you** to own the screen and the navigation. Every place the old code pushed a composite becomes a view controller you write, composed per `cometchat-ios-core`'s golden path, with its five layout rules applied.

Budget for this honestly: it is the bulk of the work, and it is a design change in the host app, not a search-and-replace.

## Then the mechanical deltas
- **Theming was replaced.** v4's theme objects give way to `CometChatTheme`'s static colours plus per-component style objects. Re-derive the brand from the theme rather than porting v4 style code — `cometchat-ios-customization`.
- **Setter vs property split.** Several v4 setters are v5 properties: styles (`avatarStyle`, `badgeStyle`, `receiptStyle`, `statusIndicatorStyle`, `typingIndicatorStyle`), `onSearchClick`, `onSelectedItemProceed`, the call-button click handlers.
- **Renames to expect:** `set(usersRequestBuilder:)` → `set(userRequestBuilder:)` · `set(subtitleView:)` → `set(subtitle:)` and `set(trailView:)` → `set(trailingView:)` **on Users/Groups only** (Conversations and GroupMembers keep the old spelling) · `set(sessionID:)` → `set(sessionId:)` · `set(callSettingBuilder:)` → `set(callSettingsBuilder:)` · `set(onDeclineClick:)` → `set(onCancelClick:)` · `set(parentMessage:)` → `set(parentMessageId:)` on the list and composer, though the thread header still takes `set(parentMessage:)`.
- **Dependencies.** v5 is SPM-only (CocoaPods is winding down) and pins exactly: kit 5.1.22 / SDK 4.1.7 / Calls 5.0.3, all added by hand.

## Method
Upgrade the dependency first and let the compiler enumerate the work — the errors are the migration checklist. Fix composites first (they cascade), then styling, then the renames. Do it **additively**: the host app's navigation, auth and design system stay theirs.

## Gotchas
- **Never mix majors.** A half-migrated project with both v4 and v5 symbols will not build.
- **Check every symbol against `catalogs/ios-v5.json`** before porting it — if it is absent, it is gone, and a v5 doc page mentioning it is not evidence it exists.

## Verify it works
The project builds with no v4 symbols remaining; every screen that was a composite is now a composed screen that renders full-size, keyboard-avoids and navigates back; theming looks intentional rather than half-ported.
