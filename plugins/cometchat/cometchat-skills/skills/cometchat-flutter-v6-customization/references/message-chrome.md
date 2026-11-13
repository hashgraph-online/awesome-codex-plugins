# Message chrome — Flutter v6 (avatar and sender name on every message)

### Avatar and sender name on every message (BAKED — verified vs 6.2.0)
What to check and why: `cometchat-onboarding/references/clone-mode.md` → *Message chrome*. This is the Flutter how-to.
> Source-verified against the `cometchat_chat_uikit` 6.2.0 tarball (`CometChatMessageList._buildMessageItem`); the per-message rules below are not in the Flutter docs — DOCS-BACKLOG.

**Kit default:** avatar and sender name only on OTHER people's messages in a GROUP. The list decides "outgoing" from `message.sender.uid == loggedInUser.uid` (not from alignment), builds the name only when `!isOutgoing && group != null`, and the avatar only when `!isOutgoing && avatarVisibility == true && group != null`. Your own messages and every 1:1 chat get none.
- **`alignment: ChatAlignment.leftAligned` works from 6.2.0** (6.1.x ignored it): every bubble, your own included, sits on the left. It moves bubbles only. It adds no avatar or name, because the checks above read the sender, not the alignment: with the setting alone your own messages sit left with neither, and a 1:1 chat shows none.
- **The template `headerView` doesn't help either:** the list only calls it for others' messages in a group. There is no per-message leading (avatar) slot.

**Do this whenever the target shows avatar and name on messages (team apps: Slack, Discord, Teams) — no need to ask.** Set `alignment: ChatAlignment.leftAligned` for the single left column, and wrap the default templates' `contentView` so every message draws its own sender row (the part the setting can't do). That covers own and others' messages in 1:1 and group chats. Turn off the kit's group avatar and name so they don't show twice:
```dart
import 'package:cometchat_chat_uikit/cometchat_chat_uikit.dart';
import 'package:flutter/material.dart';

Widget _senderRow(BaseMessage m, BuildContext context, Widget? content) {
  final sender = m.sender;
  final batchIndex = m.metadata?['batchIndex'];
  if (sender == null || (batchIndex is int && batchIndex > 0)) {
    return content ?? const SizedBox.shrink(); // multi-attachment batch: once, on the first
  }
  final palette = CometChatThemeHelper.getColorPalette(context);
  final typography = CometChatThemeHelper.getTypography(context);
  return Column(
    mainAxisSize: MainAxisSize.min,
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Row(mainAxisSize: MainAxisSize.min, children: [
        CometChatAvatar(image: sender.avatar, name: sender.name, width: 28, height: 28),
        const SizedBox(width: 8),
        Text(sender.name, style: typography.caption1?.medium?.copyWith(color: palette.textPrimary)),
      ]),
      const SizedBox(height: 4),
      if (content != null) content,
    ],
  );
}

/// Build once after init + login (it reads `enableCalls`), keep it in State, never per build.
List<CometChatMessageTemplate> senderTemplates() => MessageTemplateUtils.getAllMessageTemplates()
    .where((t) => t.category == MessageCategoryConstants.message ||
        t.category == MessageCategoryConstants.custom ||
        t.category == MessageCategoryConstants.interactive)
    .map((t) {
      final base = t.contentView;
      t.contentView = (m, context, alignment, {additionalConfigurations}) => _senderRow(
          m, context, base?.call(m, context, alignment, additionalConfigurations: additionalConfigurations));
      t.headerView = (m, context, alignment) => null; // kit's own group name: off
      return t;
    })
    .toList();

Widget messages({User? user, Group? group, required List<CometChatMessageTemplate> templates}) =>
    CometChatMessageList(
      user: user,
      group: group,
      alignment: ChatAlignment.leftAligned, // 6.2.0+: own messages join the left column
      avatarVisibility: false,
      addTemplate: templates,
    );
```
- **`addTemplate`, never `templates`:** `addTemplate` merges with the defaults and a later entry with the same category+type wins. Put any other override for the same type (the calls skill's meeting template, a custom bubble) AFTER these in the list.
- **The row sits inside the bubble.** For a flat, bubble-less look (Slack), make both bubble backgrounds transparent through `CometChatIncomingMessageBubbleStyle` / `CometChatOutgoingMessageBubbleStyle` (`message-bubble-styling`).
- **Not covered:** action and call rows (centered, no avatar by design); deleted messages (the list draws its own delete bubble before any template).
- **Own bubbles keep the outgoing colour** on the left: the bubble background is picked by sender, not alignment. Give both styles the same background (or transparent, above) for a uniform column.
- **On 6.1.x `leftAligned` is ignored** and own messages stay on the right. Pin `cometchat_chat_uikit: ^6.2.0`.
- **Once per run** isn't reachable: `contentView` gets only the message, never the previous one (L4).

**Check:** a 1:1 chat and a group, your own messages and others': every message sits on the left with one avatar and one name, none show two.
