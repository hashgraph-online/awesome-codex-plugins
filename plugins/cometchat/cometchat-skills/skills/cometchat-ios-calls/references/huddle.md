# Huddle / docked call on iOS

### Huddle / docked call — iOS how-to (BAKED — verified vs CometChatUIKitSwift 5.2.3 + CometChatCallsSDK 5.0.4)
The pattern (start → join → dock → indicator → leave) and when to use it are platform-independent: `cometchat-onboarding/references/clone-mode.md` → *Huddle / drop-in room pattern*. This is the UIKit/Swift code for it. The Calls SDK bootstrap (`initFromSettings` + `CometChatCalls.login`) in `SKILL.md` must have run first.

**Why not the kit's screens:** the group call button (`CometChatCallButtons` for a group) and the meeting bubble's Join both create `CometChatOngoingCall` and `present` it with `modalPresentationStyle = .fullScreen`. Embedding `CometChatOngoingCall` as a child view controller is no fix: when the call ends (and on a join error) it calls `self.dismiss(animated:)`, which dismisses whatever your nearest presented ancestor is. Since 5.2.1 its `setOnCallEnded` closure does fire, but right before that same `dismiss`, so it cannot stop it. The meeting bubble view (`CometChatCallBubble`) is internal, so you can't reuse it, and `CallBubbleConfiguration.setOnClick` takes `() -> Void` with no message or session id. So: send the meeting message yourself, replace the meeting template, and join the session into your own view with the Calls SDK.

```swift
import UIKit
import CometChatSDK
import CometChatCallsSDK
import CometChatUIKitSwift

// 1. Start: the same "meeting" message the kit's group call button sends (Join bubble +
// conversation preview). Session id = group GUID, so the whole channel shares one room.
@discardableResult
func startHuddle(in group: Group) -> String {
    let sessionId = group.guid
    let meeting = CustomMessage(receiverUid: group.guid, receiverType: .group,
                                customData: ["sessionID": sessionId, "callType": "audio"], type: "meeting")
    meeting.updateConversation = true
    meeting.metaData = ["incrementUnreadCount": true]
    CometChatUIKit.sendCustomMessage(message: meeting)
    return sessionId
}

// 2. Join: replace the kit's meeting bubble, so Join opens YOUR dock.
func huddleTemplate(onJoin: @escaping (String) -> Void) -> CometChatMessageTemplate {
    CometChatMessageTemplate(
        category: "custom", type: "meeting",
        contentView: { message, _, _ in
            guard let sessionId = (message as? CustomMessage)?.customData?["sessionID"] as? String else { return nil }
            let join = UIButton(type: .system)
            join.setTitle("Join huddle", for: .normal)
            join.addAction(UIAction { _ in onJoin(sessionId) }, for: .touchUpInside)
            return join
        },
        bubbleView: nil, headerView: nil, footerView: nil, bottomView: nil, options: nil)
}

// 3 + 5. Dock and leave: the Calls SDK renders tiles + controls into this view, at the size you give it.
final class HuddleDockView: UIView, SessionStatusListener, ButtonClickListener {
    private(set) var sessionId: String?
    var onClose: (() -> Void)?

    func join(sessionId: String) {
        guard self.sessionId == nil else { return }
        self.sessionId = sessionId
        let settings = SessionSettingsBuilder()
            .setSessionType(.voice)     // audio-only huddle
            .setLayout(.tile)
            .hideChangeLayoutButton(true)
            .build()
        CometChatCalls.joinSession(sessionID: sessionId, callSetting: settings, container: self,
            onSuccess: { [weak self] _ in
                guard let self else { return }
                CallSession.shared.addSessionStatusListener(self)
                CallSession.shared.addButtonClickListener(self)
            },
            onError: { [weak self] error in
                debugPrint("huddle join:", error?.errorDescription ?? "nil")
                DispatchQueue.main.async { self?.finish() }
            })
    }

    func leave() { CallSession.shared.leaveSession() } // onSessionLeft then cleans up

    nonisolated func onLeaveSessionButtonClicked() { CallSession.shared.leaveSession() }
    nonisolated func onSessionLeft() { DispatchQueue.main.async { self.finish() } }

    private func finish() {
        CallSession.shared.removeSessionStatusListener(self)
        CallSession.shared.removeButtonClickListener(self)
        sessionId = nil
        onClose?()
    }
}
```
- **Wire it:** in the channel header, set `onVoiceCallClick` on the group's `CometChatCallButtons` (when set, the kit calls it INSTEAD of sending its meeting and presenting full screen): `buttons.onVoiceCallClick = { _, group in if let group { dock.join(sessionId: startHuddle(in: group)) } }`. Or hide the kit buttons and put your own Huddle button there. On the message list, `messageList.add(templates: [huddleTemplate { dock.join(sessionId: $0) }])`, AFTER any `set(templates:)` (that call replaces all templates, e.g. the avatar wrapper in `cometchat-ios-customization/references/message-chrome.md`).
- **Where the dock lives:** a view owned by a container that outlives the chat screen (Slack: bottom of the sidebar / split view's primary column), not the pushed messages view controller, so the huddle keeps running while the user moves between channels. Close it with `dock.leave()`, never by just removing the view.
- **Size:** give the dock non-zero Auto Layout constraints (e.g. 320x220). Expanding it is just a bigger container.
- **Indicator:** "huddle active" and who started it from the latest `meeting` message (the conversation's `lastMessage` as `CustomMessage` with `type == "meeting"`). The live list comes only from the Calls SDK while you are in the session: an `NSObject` conforming to `ParticipantEventListener`, registered with `CallSession.shared.addParticipantEventListener(_:)`, gets `onParticipantListChanged(participants: [Participant])`, `onParticipantJoined(participant:)`, `onParticipantLeft(participant:)` (`Participant.uid`, `.name`, `.avatar`). Remove it with `removeParticipantEventListener(_:)`.
- **Kit bug (still in 5.2.3):** the kit's own meeting message sets its push text with `String(describing: CometChat.getLoggedInUser()?.name)`, so it reads `Optional("Name")has initiated group audio call`. The snippet above leaves `pushNotification` out; add your own text if you need one.
- **Verified 2026-10-15:** kit source at tag 5.2.3 (`CometChatCallButton.swift` `buildButton(forGroup:)` / `startGroupCall`, `CallingExtensionDecorator.swift` `getConferenceCallTemplate`, `CometChatOngoingCall.swift`) and the 5.2.3 / Calls 5.0.4 `.swiftinterface`s; Calls docs `calls/ios/join-session`, `participant-management`, `events`. The block type-checks with `swiftc` (Swift 5, Swift 6, Swift 6 + default MainActor isolation) against the 5.2.3 / Chat SDK 4.1.10 / Calls SDK 5.0.4 binaries. Not run on devices: do the two-user check (two devices, same channel, both hear each other) before calling it done.
