# Message chrome — React Native

### Avatar and sender name on every message (BAKED — verified vs @cometchat/chat-uikit-react-native 5.5.1)
What to check and why: `cometchat-onboarding/references/clone-mode.md` → *Message chrome*. This is the React Native how-to.

**Kit default** (`alignment="standard"`): avatar and sender name only on OTHER people's messages in a GROUP. 5.5.1 `CometChatMessageList` shows them when `alignment === "leftAligned" || (isIncomingMessage && !user)`. Your own messages and every 1:1 chat get neither.

Whenever the target shows an avatar and name on every message (Slack, Discord, Teams-style team apps), do both steps below yourself, without asking. They apply to own AND others' messages, in 1:1 AND group chats.

**Step 1 — alignment.** `alignment="leftAligned"` on `CometChatMessageList`. With it the kit's own leading view (avatar) and header view (name) render on every message, own and others', 1:1 and group, all in one left column. `avatarVisibility` (default `true`) must stay on. Side effect: `leftAligned` also hides the receipt ticks on your own messages (`receiptsVisibility && alignment !== "leftAligned"`), which matches Slack.

**Step 2 — per-message slots.** Do this whenever Step 1 alone doesn't match the target: own messages stay on the right (`standard`) but still carry an avatar/name, receipts must stay, or the avatar/name need the target's own look. A message template's `LeadingView` (avatar) and `HeaderView` (name) replace the kit's slot for every message the template renders, whatever the alignment or chat type. Override them in a `DataSourceDecorator` so every message list (main and thread) gets them and the list's `hide*Option` flags keep working (passing the `templates` prop instead replaces ALL templates and drops those flags):
```tsx
import { Text } from "react-native";
import { CometChat } from "@cometchat/chat-sdk-react-native";
import {
  ChatConfigurator, CometChatAvatar, CometChatUIKit, DataSourceDecorator,
  type CometChatMessageTemplate, type CometChatTheme,
} from "@cometchat/chat-uikit-react-native";

// Action rows (joined/left) and call rows render centred with no avatar: leave them alone.
const NO_CHROME: string[] = [CometChat.CATEGORY_ACTION, CometChat.CATEGORY_CALL];

class SenderChromeDataSource extends DataSourceDecorator {
  getId(): string {
    return "sender_chrome_datasource"; // REQUIRED: the base getId() throws
  }

  getAllMessageTemplates(theme: CometChatTheme, params?: any): CometChatMessageTemplate[] {
    return super.getAllMessageTemplates(theme, params).map((t) => {
      if (NO_CHROME.includes(t.category)) return t;
      t.LeadingView = (m) => {
        const sender = m.getSender();
        const avatar = sender?.getAvatar();
        return <CometChatAvatar name={sender?.getName() ?? ""} image={avatar ? { uri: avatar } : undefined} />;
      };
      t.HeaderView = (m) => (
        <Text numberOfLines={1} style={{ color: theme?.color?.textPrimary, fontWeight: "600" }}>
          {m.getSender()?.getName()}
        </Text>
      );
      return t;
    });
  }
}

// After EVERY login(): login() re-runs ChatConfigurator.init(), which drops earlier decorators.
export async function loginWithSenderChrome(uid: string) {
  await CometChatUIKit.login({ uid });
  ChatConfigurator.enable((source) => new SenderChromeDataSource(source));
}
// <CometChatMessageList user={user} group={group} alignment="leftAligned" />  (or "standard" for right-aligned own bubbles)
```
- Style the name from the target's tokens (font, size, color); `theme.color.textPrimary` keeps it readable in both modes. Pass the kit's `avatarStyle` through `CometChatAvatar`'s `style` prop if the size must match the target.
- The template slot replaces the kit's batch handling: in a multi-attachment batch the kit shows the avatar only on the first item; with your `LeadingView` every item gets one.
- **Once per run** (avatar and name only on the first of several messages from the same sender) isn't reachable: `LeadingView(message, alignment)` gets no neighbour messages, and the kit's own collapsing only covers multi-attachment batches (L4).
- **Set `alignment` once, at mount.** In 5.5.1 the list's leading/header/alignment callbacks are memoized with empty deps, so changing `alignment` on a mounted list doesn't re-render existing rows; remount the list (change its `key`) if you switch.
- **Check:** open a 1:1 chat and a group; your own and the other person's messages both show avatar + name, and join/leave rows still render centred.
