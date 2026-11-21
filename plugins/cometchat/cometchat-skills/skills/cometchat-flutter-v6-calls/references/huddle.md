# Huddle / docked call — Flutter v6

### Huddle / docked call — Flutter how-to (BAKED — verified vs cometchat_chat_uikit 6.2.0 + cometchat_calls_sdk 5.0.9)
The pattern (start → join → dock → indicator → leave) and when to use it are platform-independent: `cometchat-onboarding/references/clone-mode.md` → *Huddle / drop-in room pattern*. This is the Flutter code for it.
> Source-verified against the pub.dev tarballs (the 6.2.0 kit's `^5.0.8` floor resolves to calls SDK 5.0.9). That `joinSession` returns a `Widget?` you place anywhere is in the docs (`calls/flutter/join-session`); the kit internals below (meeting message shape, `CallScreenOverlay`, the session helpers) are not — DOCS-BACKLOG.

- **The kit's group call button and its meeting bubble's Join both call `CallScreenOverlay.show(...)`**, which inserts a full-screen `MaterialApp` running `CometChatOngoingCall` over your root navigator. That is the default full-screen call, not a dock.
- **Don't host `CometChatOngoingCall` in a panel:** it holds the device in portrait while it is open and, when the call ends outside the overlay, closes the route it sits in (`ModalRoute.of(context)`: in a panel, that is your host page) or, with no route, pops your root navigator. Join the session yourself instead, the way its bloc does:
```dart
import 'package:cometchat_chat_uikit/cometchat_calls_uikit.dart';
import 'package:cometchat_chat_uikit/cometchat_chat_uikit.dart';
import 'package:flutter/material.dart';

// Start: the same "meeting" message the kit's group call button sends (Join bubble +
// conversation preview). Session id = group GUID, so the whole channel shares one room.
Future<String> startHuddle(Group group) async {
  await CometChatUIKit.sendCustomMessage(CustomMessage(
    receiverUid: group.guid,
    receiverType: CometChatReceiverType.group,
    receiver: group,
    type: MessageTypeConstants.meeting,
    customData: {'callType': CallTypeConstants.audioCall, 'sessionID': group.guid},
    updateConversation: true,
    sendNotification: true, // members get a push, as from the kit's button
    metadata: {
      UpdateSettingsConstant.incrementUnreadCount: true,
      'pushNotification': MessageTypeConstants.meeting,
    },
  ));
  return group.guid;
}

// Join: replace the kit's meeting bubble so "Join" opens YOUR dock, not the full-screen overlay.
CometChatMessageTemplate huddleTemplate(void Function(String sessionId) onJoin) => CometChatMessageTemplate(
      type: MessageTypeConstants.meeting,
      category: MessageCategoryConstants.custom,
      options: MessageTemplateUtils.getCommonOptions,
      contentView: (m, context, alignment, {additionalConfigurations}) {
        final id = m is CustomMessage ? m.customData?['sessionID'] as String? : null;
        return CometChatCallBubble(
          title: Translations.of(context).voiceCall,
          alignment: alignment,
          onTap: (_) => onJoin(id ?? m.receiverUid),
        );
      },
    );

// The dock: a fixed-size box you own; the Calls SDK widget renders inside it.
class HuddleDock extends StatefulWidget {
  const HuddleDock({super.key, required this.sessionId, required this.onLeave});
  final String sessionId;
  final VoidCallback onLeave;
  @override
  State<HuddleDock> createState() => _HuddleDockState();
}

class _HuddleDockState extends State<HuddleDock> {
  Widget? _call;
  bool _left = false;
  late final _status = _Status(() => _leave(notify: true));
  late final _buttons = _Buttons(() => _leave(notify: true));

  @override
  void initState() {
    super.initState();
    _join();
  }

  Future<void> _join() async {
    await CallEventService.instance.waitForCallsSdk();
    if (!await CallPermissions.requestForCallType(isVideoCall: false) || !mounted) return;
    // Audio-only the way the 6.2.0 kit does it: Android runs the audio type as a voice session
    // (its call service asks only for the mic); iOS ignores the type, so keep the paused camera.
    final settings = SessionSettingsBuilder()
        .setLayout(LayoutType.tile)
        .setType(SessionType.audio)
        .startVideoPaused(true)
        .hideToggleVideoButton(true)
        .hideSwitchCameraButton(true)
        .hideChangeLayoutButton(true)
        .build();
    CometChatUIKitCalls.startSession(widget.sessionId, settings, onSuccess: (Widget? w) {
      CallSession.getInstance()
        ?..addSessionStatusListener(_status)
        ..addButtonClickListener(_buttons);
      CallStateService.instance.setActiveCallValue(true);
      if (mounted) setState(() => _call = w);
    }, onError: (_) => _leave(notify: true));
  }

  Future<void> _leave({required bool notify}) async {
    if (_left) return;
    _left = true;
    CallSession.getInstance()
      ?..removeSessionStatusListener(_status)
      ..removeButtonClickListener(_buttons);
    await CometChatUIKitCalls.endSession(); // stops the Android call service, then leaves the session
    CallStateService.instance.setActiveCallValue(false);
    // No reinitializeAfterSession(): deprecated in 6.2.0, the kit keeps the Calls SDK ready.
    if (notify) widget.onLeave();
  }

  @override
  void dispose() {
    _leave(notify: false);
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => SizedBox(
        width: 320,
        height: 220,
        child: _call ?? const Center(child: CircularProgressIndicator()),
      );
}

class _Status extends SessionStatusListeners {
  _Status(this.onEnd);
  final VoidCallback onEnd;
  @override
  void onSessionLeft() => onEnd();
  @override
  void onConnectionClosed() => onEnd();
}

class _Buttons extends ButtonClickListeners {
  _Buttons(this.onEnd);
  final VoidCallback onEnd;
  @override
  void onLeaveSessionButtonClicked() => onEnd();
}
```
- **Wire it:** a "Huddle" button in the channel header: `CometChatMessageHeader(group: g, auxiliaryButtonView: (group, user, context) => ...)`. That slot replaces the kit's call buttons, so they stop opening the full-screen call. Its `onPressed` calls `startHuddle` and opens `HuddleDock` where the target shows it (Slack: bottom of the sidebar). Pass `addTemplate: [...senderTemplates, huddleTemplate(openDock)]` to `CometChatMessageList`, built once in State and not per build. Keep the dock above the per-channel route so it stays mounted while the user switches channels; disposing it leaves the call.
- **Size:** the dock needs a bounded width and height (zero-dimension pitfall in `SKILL.md`). Expanding it into a window is just a bigger box.
- **Indicator:** "huddle active" and who started it come from the latest `meeting` message. Live participants: a `ParticipantEventListeners` subclass on `CallSession.getInstance()` (`addParticipantEventListener`), whose `onParticipantListChanged(List<Participant>)` gives `name` / `avatar` / `uid` per participant.
- **If `w` comes back null** (older Calls SDK builds on Android drew the call natively), there is nothing to dock: report it as a limitation, don't fake it.
- **Not run yet:** source-checked only, no compile or device run. Do the two-user check on two devices before calling it done.
