# Huddle / docked call — Android how-to (BAKED — verified vs chatuikit 6.1.1 + calls-sdk-android 5.0.4)

The pattern (start -> join -> dock -> indicator -> leave) and when to use it are platform-independent:
`cometchat-onboarding/references/clone-mode.md` -> *Huddle / drop-in room pattern*. This is the Android
code for it, for both cohorts (Views and Compose). Prerequisites from `SKILL.md`: the Calls SDK artifact,
`enableCalling`, a login AFTER calling was enabled, and `RECORD_AUDIO` granted before the dock joins.

## Why not the kit's call screen
- The kit's group call button (`CometChatCallButtons`, inside `CometChatMessageHeader`) sends a `meeting`
  custom message and then calls `CometChatCallActivity.launchConferenceCallScreen(...)`; the meeting
  bubble's Join does the same. Both open the full-screen `CometChatOngoingCallActivity`.
- **Views:** `CometChatOngoingCall` is a `View`, but on call end or timeout it calls `activity?.finish()`,
  so mounted in your panel it closes YOUR screen (still so in 6.1.1). Don't dock it.
- **Compose:** `CometChatOngoingCall(...)` fills its parent, but it does nothing when `callSettingsBuilder`
  is null (the ViewModel returns early, no error; still so in 6.1.1) and its default `viewModel()` is shared per screen.
- So the dock joins the session itself through the Calls SDK, into a `RelativeLayout` you own.
- **Kit bug (6.0.5 and 6.1.1):** the kit sends the session id under `"sessionID"`, but both meet
  bubbles read `"sessionId"`, so the bubble's own session id is `""`. Read `"sessionID"` yourself (below).

## Shared code (both cohorts)
```kotlin
import android.widget.RelativeLayout
import androidx.lifecycle.LifecycleOwner
import com.cometchat.calls.core.CallSession
import com.cometchat.calls.core.CometChatCalls
import com.cometchat.calls.listeners.ButtonClickListener
import com.cometchat.calls.listeners.ParticipantEventListener
import com.cometchat.calls.listeners.SessionStatusListener
import com.cometchat.calls.model.Participant
import com.cometchat.calls.model.SessionType
import com.cometchat.chat.constants.CometChatConstants
import com.cometchat.chat.core.CometChat
import com.cometchat.chat.exceptions.CometChatException
import com.cometchat.chat.models.BaseMessage
import com.cometchat.chat.models.CustomMessage
import com.cometchat.chat.models.Group
import com.cometchat.uikit.core.CometChatUIKit
import com.cometchat.uikit.core.constants.UIKitConstants
import org.json.JSONObject

// 1. Start: the same "meeting" message the kit's group call button sends (Join bubble +
// conversation preview). Session id = group GUID, so the whole channel shares one room.
fun startHuddle(group: Group, onSent: (sessionId: String) -> Unit, onError: (CometChatException) -> Unit) {
    val sessionId = group.guid
    val data = JSONObject()
        .put(UIKitConstants.CallingJSONConstants.CALL_TYPE, CometChatConstants.CALL_TYPE_AUDIO)
        .put(UIKitConstants.CallingJSONConstants.CALL_SESSION_ID, sessionId) // the key is "sessionID"
    val msg = CustomMessage(sessionId, CometChatConstants.RECEIVER_TYPE_GROUP, UIKitConstants.MessageType.MEETING, data)
    msg.metadata = JSONObject().put("incrementUnreadCount", true).put("pushNotification", UIKitConstants.MessageType.MEETING)
    msg.shouldUpdateConversation(true)
    CometChatUIKit.sendCustomMessage(msg, object : CometChat.CallbackListener<CustomMessage>() {
        override fun onSuccess(sent: CustomMessage) = onSent(sessionId)
        override fun onError(e: CometChatException) = onError(e)
    })
}

// Read "sessionID" yourself: the kit's meet bubble reads "sessionId" (6.0.5, 6.1.1) and gets "".
fun meetingSessionId(message: BaseMessage): String =
    (message as? CustomMessage)?.customData?.optString(UIKitConstants.CallingJSONConstants.CALL_SESSION_ID).orEmpty()

// 3. Dock: join INTO a RelativeLayout you own (fixed size). joinSession(sessionId, ...) makes the
// call token itself from the Calls login that CometChatUIKit.login did.
class HuddleDock(
    private val owner: LifecycleOwner,
    private val onParticipants: (List<Participant>) -> Unit,
    private val onClosed: () -> Unit,
) {
    private var session: CallSession? = null
    private var closed = false

    fun join(sessionId: String, container: RelativeLayout) {
        val settings = CometChatCalls.SessionSettingsBuilder()
            .setSessionType(SessionType.VOICE) // audio-only huddle
            .hideChangeLayoutButton(true)
            .build()
        CometChatCalls.joinSession(sessionId, settings, container, object : CometChatCalls.CallbackListener<CallSession>() {
            override fun onSuccess(s: CallSession) {
                if (closed) { s.leaveSession(); return } // dock closed while joining
                session = s
                s.addSessionStatusListener(owner, object : SessionStatusListener() {
                    override fun onSessionLeft() = close()
                    override fun onSessionTimedOut() = close()
                })
                s.addButtonClickListener(owner, object : ButtonClickListener() {
                    override fun onLeaveSessionButtonClicked() = leave()
                })
                // 4. Indicator: the live participant list comes only from these events.
                s.addParticipantEventListener(owner, object : ParticipantEventListener() {
                    override fun onParticipantListChanged(participants: List<Participant>) = onParticipants(participants)
                })
            }
            override fun onError(e: com.cometchat.calls.exceptions.CometChatException) = close()
        })
    }

    // 5. Leave: releases the mic and camera. Call it when the dock closes.
    fun leave() {
        session?.leaveSession()
        close()
    }

    private fun close() {
        if (closed) return
        closed = true
        session = null
        onClosed()
    }
}
```
`Participant` has `uid`, `name`, `avatar`, `isAudioMuted`; `ParticipantEventListener` also has
`onParticipantJoined` / `onParticipantLeft` / `onDominantSpeakerChanged`. "Huddle active, started by X"
comes from the latest `meeting` message in the channel (`sender`, `sentAt`).

## Views wiring
```kotlin
import android.content.Context
import android.view.View
import androidx.recyclerview.widget.RecyclerView
import com.cometchat.chat.constants.CometChatConstants
import com.cometchat.chat.models.BaseMessage
import com.cometchat.chat.models.CustomMessage
import com.cometchat.uikit.core.constants.UIKitConstants
import com.cometchat.uikit.kotlin.presentation.messageheader.ui.CometChatMessageHeader
import com.cometchat.uikit.kotlin.presentation.messagelist.ui.CometChatMessageList
import com.cometchat.uikit.kotlin.presentation.shared.messagebubble.BubbleFactory
import com.cometchat.uikit.kotlin.presentation.shared.messagebubble.meetcallbubble.CometChatMeetCallBubble
import com.cometchat.uikit.kotlin.presentation.shared.messagebubble.meetcallbubble.CometChatMeetCallBubbleStyle

// 2. Join: replace the meeting bubble so Join opens YOUR dock, not CometChatCallActivity.
class HuddleMeetingFactory(private val onJoin: (sessionId: String) -> Unit) : BubbleFactory() {
    override fun getCategory(): String = CometChatConstants.CATEGORY_CUSTOM
    override fun getType(): String = UIKitConstants.MessageType.MEETING
    override fun createContentView(context: Context): View = CometChatMeetCallBubble(context)
    override fun bindContentView(
        view: View, message: BaseMessage,
        alignment: UIKitConstants.MessageBubbleAlignment,
        holder: RecyclerView.ViewHolder?, position: Int
    ) {
        val bubble = view as CometChatMeetCallBubble
        bubble.setStyle(
            if (alignment == UIKitConstants.MessageBubbleAlignment.RIGHT) CometChatMeetCallBubbleStyle.outgoing(view.context)
            else CometChatMeetCallBubbleStyle.incoming(view.context)
        )
        bubble.setMessage(message as? CustomMessage)
        bubble.setOnJoinClick { onJoin(meetingSessionId(message)) }
    }
}

fun wireHuddle(header: CometChatMessageHeader, list: CometChatMessageList, isGroup: Boolean, openDock: (String) -> Unit) {
    // Group chats only: this callback also replaces the voice button's 1:1 call.
    if (isGroup) header.setOnVoiceCallClick { _, group ->
        group?.let { startHuddle(it, onSent = openDock, onError = { /* show it */ }) }
    }
    list.setBubbleFactories(listOf(HuddleMeetingFactory(openDock))) // one list: it REPLACES earlier factories
}
```
- The dock is a fixed-size `RelativeLayout` in the layout that outlives channel switches (Slack: bottom
  of the sidebar, in the Activity, not the chat Fragment), e.g. `320dp x 220dp`, `visibility="gone"`.
  `openDock(id)`: if no dock is open, show the container and
  `HuddleDock(this, onParticipants = { ... }, onClosed = { container.removeAllViews(); container.visibility = View.GONE }).join(id, container)`.
  Call `leave()` from your close button and from `onDestroy`.
- A Views `BubbleFactory` drives ALL slots of its type, so meeting rows lose the kit's avatar, name and
  time; add `createStatusInfoView` / `createLeadingView` on the factory if the target shows them.

## Compose wiring
```kotlin
import android.widget.RelativeLayout
import androidx.compose.foundation.layout.size
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.lifecycle.compose.LocalLifecycleOwner
import com.cometchat.calls.model.Participant
import com.cometchat.chat.constants.CometChatConstants
import com.cometchat.chat.models.BaseMessage
import com.cometchat.chat.models.CustomMessage
import com.cometchat.chat.models.Group
import com.cometchat.uikit.compose.presentation.messageheader.ui.CometChatMessageHeader
import com.cometchat.uikit.compose.presentation.messagelist.ui.CometChatMessageList
import com.cometchat.uikit.compose.presentation.shared.formatters.CometChatTextFormatter
import com.cometchat.uikit.compose.presentation.shared.messagebubble.BubbleFactory
import com.cometchat.uikit.compose.presentation.shared.messagebubble.style.CometChatMessageBubbleStyle
import com.cometchat.uikit.compose.presentation.shared.messagebubble.ui.CometChatMeetCallBubble
import com.cometchat.uikit.core.constants.UIKitConstants

// 2. Join: replace the meeting bubble's content so Join opens YOUR dock. Name, thread and reactions
// stay the kit's; the default avatar does not (a factory row uses getLeadingView, null here) unless
// the list's own leadingView slot is set (customization skill, Avatar and sender name).
class HuddleMeetingFactory(private val onJoin: (sessionId: String) -> Unit) : BubbleFactory {
    override fun getCategory(): String = CometChatConstants.CATEGORY_CUSTOM
    override fun getType(): String = UIKitConstants.MessageType.MEETING
    override fun getContentView(
        message: BaseMessage,
        alignment: UIKitConstants.MessageBubbleAlignment,
        style: CometChatMessageBubbleStyle,
        textFormatters: List<CometChatTextFormatter>,
    ): @Composable () -> Unit = {
        (message as? CustomMessage)?.let { m ->
            CometChatMeetCallBubble(message = m, alignment = alignment, onJoinClick = { onJoin(meetingSessionId(m)) })
        }
    }
}

// 3. Dock: a fixed-size composable; leaving composition leaves the call.
@Composable
fun HuddleDockView(
    sessionId: String,
    onParticipants: (List<Participant>) -> Unit,
    onClosed: () -> Unit,
    modifier: Modifier = Modifier.size(width = 320.dp, height = 220.dp),
) {
    val owner = LocalLifecycleOwner.current
    val dock = remember(sessionId) { HuddleDock(owner, onParticipants, onClosed) }
    AndroidView(factory = { ctx -> RelativeLayout(ctx).also { dock.join(sessionId, it) } }, modifier = modifier)
    DisposableEffect(dock) { onDispose { dock.leave() } }
}

@Composable
fun ChannelWithHuddle(group: Group) {
    var huddleId by remember { mutableStateOf<String?>(null) } // hoist above the nav host in a real app
    val factories = remember { listOf(HuddleMeetingFactory { id -> huddleId = id }) }
    CometChatMessageHeader(
        group = group,
        hideVoiceCallButton = false,
        onVoiceCallClick = { _, g -> g?.let { startHuddle(it, onSent = { id -> huddleId = id }, onError = {}) } },
    )
    CometChatMessageList(group = group, bubbleFactories = factories)
    huddleId?.let { HuddleDockView(it, onParticipants = { }, onClosed = { huddleId = null }) }
}
```
- Hoist `huddleId` and render `HuddleDockView` OUTSIDE the per-channel screen (e.g. in the sidebar of the
  app shell): leaving composition calls `leave()`, so a dock inside the chat screen hangs up on channel switch.
- Pass `onVoiceCallClick` only for groups: it replaces the 1:1 voice call too.

## Verified
Every symbol above was read in the 6.1.1 kit source (tag `v6.1.1` of `cometchat/cometchat-uikit-android`) and
the calls-sdk-android 5.0.4 AAR (`javap`), and the three code blocks compiled against the published 6.1.1
artifacts (chat-sdk 5.0.7) + calls-sdk 5.0.4 (2026-10-15; first verified on 6.0.5). `joinSession(sessionId, settings, container, listener)` matches the
docs page `/calls/android/join-session`. NOT yet run on a device: the call view in a 320x220 container and
the two-user connect are unverified. Do the two-user check before calling it done.
