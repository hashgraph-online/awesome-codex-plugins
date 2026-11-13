# Huddle / docked call — Angular how-to (BAKED — verified vs chat-uikit-angular 5.2.2 + calls-sdk-javascript 5.0.8)

The pattern (start → join → dock → indicator → leave) and when to use it are platform-independent: `cometchat-onboarding/references/clone-mode.md` → *Huddle / drop-in room pattern*. This is the Angular code for it.

**`<cometchat-ongoing-call>` can't be docked.** Its `:host` style is `position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: 9999`, so it covers the whole viewport wherever you mount it. Its `callScreenView` input doesn't help: it replaces the frame the kit joins into, so the session never starts. The kit's own group call button and the default meeting bubble's Join button (localized `message_list_join_call` since 5.2.2, "Join" in English; a hard-coded "Join Call" up to 5.2.1) both open that full-screen screen (`CallButtonsService.joinMeeting` → `ccShowOngoingCall`). So join the session into your own element the way the kit's `OngoingCallService.startCall` does internally: `generateToken(sessionId, authToken)` then `joinSession(token, settings, element)`, on the kit's `CometChatUIKitCalls` (the Calls SDK object, typed `any`; null until the SDK has loaded).

```ts
import { Component, ElementRef, Injectable, OnDestroy, OnInit, TemplateRef, ViewChild, inject, input, output, signal } from '@angular/core';
import { CometChat, type Group } from '@cometchat/chat-sdk-javascript';
import {
  CometChatCallBubbleComponent, CometChatMessageEvents, CometChatUIKit, CometChatUIKitCalls, CometChatUIKitConstants,
  MessageBubbleConfigService, MessageStatus,
} from '@cometchat/chat-uikit-angular';

@Injectable({ providedIn: 'root' })
export class HuddleService {
  /** Non-null while the dock is open. */
  readonly sessionId = signal<string | null>(null);

  // Start: the same "meeting" message the kit's group call button sends (Join bubble + conversation
  // preview). Session id = group GUID, so the whole channel shares one room.
  async start(group: Group): Promise<void> {
    const sessionId = group.getGuid();
    const msg = new CometChat.CustomMessage(sessionId, CometChat.RECEIVER_TYPE.GROUP,
      CometChatUIKitConstants.calls.meeting, { sessionID: sessionId, sessionId, callType: 'audio' });
    msg.setMetadata({ incrementUnreadCount: true });
    msg.shouldUpdateConversation(true);
    const sent = await CometChat.sendCustomMessage(msg);
    // The list shows your OWN sends only through this event (the SDK listener doesn't echo them).
    CometChatMessageEvents.ccMessageSent.next({ message: sent, status: MessageStatus.success });
    this.sessionId.set(sessionId);
  }
  join(sessionId: string): void { this.sessionId.set(sessionId); }
  close(): void { this.sessionId.set(null); }
}

// Join: replace the meeting bubble's content so "Join" opens YOUR dock, not the full-screen call.
@Component({
  selector: 'app-huddle-join',
  standalone: true,
  imports: [CometChatCallBubbleComponent],
  template: `
    <ng-template #meeting let-m>
      <cometchat-call-bubble [message]="m" alignment="left" buttonText="Join huddle"
        (buttonClick)="huddle.join($event.sessionId)" />
    </ng-template>`,
})
export class HuddleJoinComponent implements OnInit, OnDestroy {
  readonly huddle = inject(HuddleService);
  private readonly bubbles = inject(MessageBubbleConfigService);
  @ViewChild('meeting', { static: true }) meeting!: TemplateRef<unknown>;
  ngOnInit(): void { this.bubbles.setBubbleView('meeting_custom', { contentView: this.meeting }); }
  ngOnDestroy(): void { this.bubbles.clearType('meeting_custom'); }
}

// Dock: a fixed-size element you own; the Calls SDK renders tiles + controls into it.
@Component({
  selector: 'app-huddle-dock',
  standalone: true,
  template: `<div #frame class="cc-huddle-dock" style="position:relative;width:320px;height:220px"></div>`,
})
export class HuddleDockComponent implements OnInit, OnDestroy {
  readonly sessionId = input.required<string>();
  readonly left = output<void>();
  @ViewChild('frame', { static: true }) frame!: ElementRef<HTMLDivElement>;
  private unsubs: Array<() => void> = [];
  private done = false;

  async ngOnInit(): Promise<void> {
    await CometChatUIKit.callingReady;
    const calls = CometChatUIKitCalls; // the Calls SDK object; null if it never loaded
    const user = CometChatUIKit.getLoggedInUser();
    if (!user || !calls || this.done) return;
    const leave = () => { if (this.done) return; this.done = true; calls.leaveSession(); this.left.emit(); };
    this.unsubs = [calls.addEventListener('onSessionLeft', leave), calls.addEventListener('onLeaveSessionButtonClicked', leave)];
    const { token }: { token: string } = await calls.generateToken(this.sessionId(), user.getAuthToken());
    if (this.done) return; // dock closed while the token was in flight
    await calls.joinSession(token, {
      sessionType: 'VOICE', layout: 'TILE', hideChangeLayoutButton: true, hideVirtualBackgroundButton: true,
    }, this.frame.nativeElement);
  }
  ngOnDestroy(): void {
    this.unsubs.forEach((u) => u());
    if (!this.done) { this.done = true; CometChatUIKitCalls?.leaveSession(); }
  }
}

// Indicator: live participant names (payload items have uid, name, avatar). Returns an unsubscribe.
export function watchParticipants(onChange: (names: string[]) => void): () => void {
  return CometChatUIKitCalls.addEventListener('onParticipantListChanged',
    (list: Array<{ uid: string; name: string; avatar?: string }>) => onChange(list.map((p) => p.name)));
}
```

- **Wire it:** in the group header set `[hideVoiceCallButton]="true"` and `[hideVideoCallButton]="true"` on `<cometchat-message-header>` (the kit's group buttons open the full-screen call) and put a "Huddle" button in its `[auxiliaryButtonView]` template that calls `huddle.start(group)`. Mount `<app-huddle-join />` once next to the message list. Render `@if (huddle.sessionId(); as id) { <app-huddle-dock [sessionId]="id" (left)="huddle.close()" /> }` where the target shows it (Slack: bottom of the sidebar), in a component that stays alive while the user switches channels: destroying the dock leaves the call.
- **Size:** the dock needs a fixed width and height (zero-height pitfall in `SKILL.md`). Expanding it into a window is just a bigger container.
- **Indicator:** "huddle active" and who started it from the latest `meeting` message (`getCustomData()` holds `sessionID` and `callType`); live names from `onParticipantListChanged`. `onParticipantJoined` / `onParticipantLeft` also exist.
- **Calling must be on** (`uiKit: { callsSDK: {} }`, `SKILL.md`), or `CometChatUIKitCalls` stays null and the dock does nothing.
- **Verified 2026-10-15:** every name read from the shipped 5.2.2 fesm2022 + `.d.ts` (5.2.0 identical for these names) and calls-sdk 5.0.8 `index.d.ts`; this file compiles with `ng build` (`strictTemplates`) + strict TS, and the dock's Calls SDK calls type-check against the Calls SDK 5.0.8's own typings. Not yet run in a browser or with two users: do the two-user check before calling it done.
