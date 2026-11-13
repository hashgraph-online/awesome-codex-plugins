# Huddle / docked call — React Native

### Huddle / docked call — React Native how-to (BAKED — verified vs @cometchat/chat-uikit-react-native 5.5.1 + @cometchat/calls-sdk-react-native 5.0.6)
The pattern (start → join → dock → indicator → leave) and when to use it are platform-independent: `cometchat-onboarding/references/clone-mode.md` → *Huddle / drop-in room pattern*. This is the React Native code for it.

**Why the default is wrong for a huddle:** the kit's group call button sends a `meeting` message and opens `CometChatOutgoingCall`, which renders `CometChatOngoingCall` inside a React Native `<Modal>` (full screen). The meeting bubble's Join also wraps `CometChatOngoingCall` in a `<Modal>`, and that modal lives in the open `CometChatMessageList`'s state, so it belongs to that one chat screen. `CometChatOngoingCall` itself is only a 100%-size `View` around `CometChatCalls.Component`; the full screen comes from the wrapping Modal. So: send the meeting message yourself, replace the bubble's Join, and render the Calls SDK component in your own fixed-size View.
```tsx
import { useEffect, useRef, useState } from "react";
import { ActivityIndicator, View } from "react-native";
import { CometChat } from "@cometchat/chat-sdk-react-native";
import { CometChatCalls } from "@cometchat/calls-sdk-react-native";
import {
  ChatConfigurator, CometChatMeetCallBubble, CometChatUIKit, DataSourceDecorator, Icon,
  type CometChatMessageTemplate, type CometChatTheme, type DataSource,
} from "@cometchat/chat-uikit-react-native";

// 1. Start: the same "meeting" message the kit's group call button sends (CometChatCallButtons).
// Session id = group GUID, so the whole channel shares one room. Group calls never ring.
export async function startHuddle(group: CometChat.Group): Promise<string> {
  const sessionId = group.getGuid();
  const msg = new CometChat.CustomMessage(sessionId, CometChat.RECEIVER_TYPE.GROUP, "meeting", { callType: "audio", sessionId });
  msg.setMetadata({ incrementUnreadCount: true });
  msg.shouldUpdateConversation(true);
  await CometChatUIKit.sendCustomMessage(msg); // kit helper: the bubble appears in the open list
  return sessionId;
}

// 2. Join: replace the meeting template's bubble so Join opens YOUR dock, not the kit's Modal.
class HuddleDataSource extends DataSourceDecorator {
  constructor(source: DataSource, private onJoin: (sessionId: string) => void) {
    super(source);
  }
  getId(): string {
    return "huddle_datasource"; // REQUIRED: the base getId() throws
  }
  getAllMessageTemplates(theme: CometChatTheme, params?: any): CometChatMessageTemplate[] {
    // Replace in place: the list keeps the FIRST template per category_type, so appending loses.
    return super.getAllMessageTemplates(theme, params).map((t) => {
      if (t.category !== "custom" || t.type !== "meeting") return t;
      t.ContentView = (m) => {
        const data = (m as CometChat.CustomMessage).getCustomData() as { sessionId?: string; sessionID?: string };
        const sessionId = data?.sessionId ?? data?.sessionID ?? "";
        return (
          <CometChatMeetCallBubble
            titleText="Huddle"
            subTitleText={m.getSender()?.getName() ?? ""}
            buttonText="Join"
            icon={<Icon name="incoming-audio-fill" />}
            onClick={() => this.onJoin(sessionId)}
            style={theme?.messageListStyles?.incomingMessageBubbleStyles?.meetCallBubbleStyles ?? {}}
          />
        );
      };
      return t;
    });
  }
}
// After EVERY login (login() re-runs ChatConfigurator.init() and drops decorators):
export const registerHuddle = (openDock: (sessionId: string) => void) =>
  ChatConfigurator.enable((source) => new HuddleDataSource(source, openDock));

// 3. Dock: the Calls SDK component inside a fixed-size View you own.
// Module scope: the component re-applies its config whenever this object's identity changes.
const VOICE = { sessionType: "VOICE", layout: "TILE" } as const;

export function HuddleDock({ sessionId, onLeave }: { sessionId: string; onLeave: () => void }) {
  const [token, setToken] = useState<string | null>(null);
  const onLeaveRef = useRef(onLeave);
  onLeaveRef.current = onLeave;
  useEffect(() => {
    let left = false;
    const closed = () => { if (left) return; left = true; onLeaveRef.current(); };
    const unsubs = [
      CometChatCalls.addEventListener("onSessionLeft", closed),
      // The SDK's own leave button already calls leaveSession(); just close the dock.
      CometChatCalls.addEventListener("onLeaveSessionButtonClicked", closed),
    ];
    CometChat.getLoggedinUser()
      .then((u) => (u ? CometChatCalls.generateToken(sessionId, u.getAuthToken()) : Promise.reject(new Error("not logged in"))))
      .then((res) => { if (!left) setToken(res.token); })
      .catch(closed);
    // 5. Leave: unmounting the component does NOT leave the session; do it here.
    return () => {
      unsubs.forEach((u) => u());
      if (!left) { left = true; CometChatCalls.leaveSession(); }
    };
  }, [sessionId]);
  return (
    <View style={{ width: "100%", height: 220 }}>
      {token ? <CometChatCalls.Component callToken={token} sessionSettings={VOICE} /> : <ActivityIndicator />}
    </View>
  );
}

// 4. Indicator: live participants come only from the session you have joined.
export function useHuddleParticipants() {
  const [names, setNames] = useState<string[]>([]);
  useEffect(() => CometChatCalls.addEventListener("onParticipantListChanged", (list) => setNames(list.map((p) => p.name))), []);
  return names;
}
```
- **Wire it:** in the channel header, `AuxiliaryButtonView` replaces the kit's call buttons. Return your Huddle button for a group (it calls `startHuddle(group).then(openDock)`) and `<CometChatCallButtons user={user} />` for a 1:1 chat so 1:1 calls keep ringing. Call `registerHuddle(openDock)` right after `CometChatUIKit.login(...)`. Mount `<HuddleDock>` once, above the navigator (next to `CometChatIncomingCall`), at the place the target shows it (Slack: bottom of the sidebar), so it stays up while the user moves between channels; closing it is unmounting it.
- **Size:** give the dock a fixed height (and a width from its parent). Expanding it into a window is just a bigger View.
- **Indicator:** "huddle active" and who started it come from the latest `meeting` message in the group; participant names come from `onParticipantListChanged` (payload `{ pid, name, uid, avatar? }[]`) and only fire for a user who has joined.
- **One session at a time:** `CometChatCalls` holds a single active session. A 1:1 call started while the dock is up must wait until the huddle is left (`onSessionLeft`).
- **Verified 2026-10-15 (kit 5.5.1, calls-sdk 5.0.6):** strict `tsc` clean against both packages; names and behaviour read from the shipped source and `/calls/react-native/join-session`. Not run on a device: do the two-user check on two real devices (simulators capture no audio) before calling it done.
