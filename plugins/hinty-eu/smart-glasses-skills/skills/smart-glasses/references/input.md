# Input on smart glasses

Read this when you map taps, swipes, a ring, a wristband, buttons or media keys to app actions, or decide which
controls must live on the phone instead.

Last checked: 2026-11-08. Verification: docs-only (no hardware test yet). Gesture lists come from vendor docs and
help pages; anything from third-party guides is marked community.

## The rule

Give the app a tiny vocabulary and let every target map its own gestures to it. This repository uses three shared
actions: **repeat** (show or say the current item again), **skip** (drop it, wait for the next) and **hide** (blank
the display until the next repeat or new content). They travel as `{"type":"action","action":"repeat"}` in the
`examples/live-captions` protocol.

- Never take a gesture the system reserves (table below). Store review rejects it or the system eats it.
- Expect false taps when the wearer adjusts the frame: ignore taps while nothing is shown and debounce (about 300 ms).
- Anything destructive (delete, send, end a paid session) needs confirmation on the phone, never one tap.
- More than three actions belong on the phone screen, a watch, or voice through the phone microphone.

## What each brand gives you

| Glasses | Physical input | What reaches your app | Reserved by the system |
|---|---|---|---|
| [Even G2](brands/even-g2.md) + R1 ring | Tap, double tap, swipe up and down, long press and release on either temple or the R1 | `onEvenHubEvent`: taps in `sysEvent` (`eventSource` 1 right, 2 ring, 3 left), swipes as `SCROLL_TOP_EVENT` / `SCROLL_BOTTOM_EVENT`, your menu items in `menuItemClickEvent`; long press needs SDK 0.0.14+ and Even app 2.2.9+ | Tap then long press opens the system menu (Display off, Brightness, Close app, plus up to 10 of your items); a double tap on the root page must open the exit dialog (`shutDownPageContainer(1)`); swipes scroll an overflowing capture container |
| [Meta Ray-Ban Display](brands/meta-display.md), DAT | Neural Band: index-finger pinch selects, middle-finger pinch goes back, thumb swipe on the index finger scrolls. Touchpad on the right temple: one-finger tap selects, two-finger tap goes back, swipes scroll | Focus moves between your on-screen buttons; select fires `onClick`. Raw `Inputs` (Nav, Select, capture button) is beta, not for production | Back ends the DAT session and is not delivered. Meta AI: band thumb double tap on the side of the index finger, touchpad one-finger tap and hold (reassignable). Wake or sleep: band middle-finger double tap, touchpad two-finger double tap. App switcher: band middle-finger hold, touchpad two-finger tap and hold. Volume: band pinch and rotate, touchpad two-finger swipe |
| Meta Ray-Ban Display, Web App | Same gestures | `keydown` for `ArrowUp`, `ArrowDown`, `ArrowLeft`, `ArrowRight`, `Enter`; arrows move focus (spatial navigation), Enter activates the focused element | Back calls `history.back()` (`popstate`), plus everything in the row above |
| [Ray-Ban Meta, Oakley Meta](brands/meta-audio-glasses.md) (no display) | Touchpad (community guide: tap play or pause, double tap next track, triple tap previous track, swipe volume, press and hold Meta AI), capture button; Gen 3 adds an action button | Without DAT: headset media keys, delivery to your app unverified. DAT `Inputs` (beta): double tap = `Select`, swipe = `Nav`, capture button = `SHORT_PRESS`, `HOLD`, `DOUBLE_PRESS` | Press and hold (Meta AI), "Hey Meta", the action button (Meta-defined actions only: Meta AI, a saved prompt, Garmin stats, capture modes, per Meta help). In a DAT session without interactive content a tap pauses and tap and hold stops the session |
| [Rokid Glasses](brands/rokid.md), CXR-L custom view | Temple touchpad, AI key | No taps or swipes. Lifecycle only: paused for the assistant, resumed, closed by the wearer, launcher resumed, wearing on or off, screen on or off. The AI key as `onAiWake()` with `AiInterceptMode.BLOCK_AI` (experiment) | The touchpad belongs to the glasses system; real gestures need your own APK on the glasses (CXR-S) |
| [Vuzix Z100](brands/vuzix-z100.md) | Taps anywhere on the frame (no left or right, no swipes), power button | 1, 2 or 3 taps, only while you hold control and set `maxNumTaps` (default 0 reports nothing); power, display and timeout events | Power button: wake and sleep, hold 3 s to switch off |
| [Android XR glasses](brands/android-xr.md) | Touchpad, camera button, voice | Indirect pointer input through Glimmer focus; raw `MotionEvent`s in `dispatchGenericMotionEvent`; camera button as `TOGGLE_APP_CAMERA` | System Back (swipe down on display glasses, swipe back on audio glasses): handle it with `OnBackPressedDispatcher`, but it must always go back or exit, never a custom action |
| [RayNeo X3 Pro](brands/standalone-android-glasses.md) | Right temple touchpad (one axis), optional ring | `MotionEvent`s on the X axis; RayNeo's ARDK turns them into `TempleAction` (`Click`, `DoubleClick`, `TripleClick`, `LongClick`, `SlideForward`, `SlideBackward`, `SlideUpwards`, `SlideDownwards`) | Double tap is Back |
| INMO Air3 | Temple tap and slide, ring | No official mapping; community (Air2): tap = Enter, double tap = Back, slides = D-pad keys | Double tap is Back |
| [USB-C display glasses](brands/usb-c-displays.md) | Buttons for brightness and display modes | Nothing | All of them |
| [MentraOS](brands/mentra.md) | Depends on the glasses | `session.input.onTouch` (single, double, triple tap, long press, swipe up, swipe down), `onButtonPress` (short, long; declare `BUTTON`) | On G2 a double tap may open the native dashboard (unverified) |
| [Brilliant Labs Halo](brands/brilliant-labs.md) | One button, IMU | Button click, double, long press; IMU taps single, double, triple (your Lua callbacks) | One Lua VM: another host app replaces your callbacks |
| [Snap Specs](brands/snap-spectacles.md) | Hands, voice | Pinch through `GestureModule` or the Spectacles Interaction Kit; the ASR module | Not covered here |
| [Notifications](brands/notification-glasses.md) (rung 4) | Glasses: dismiss | Your notification action buttons, pressed on the phone, lock screen or watch. Android XR display glasses show only the system clear action, plus direct reply for `MessagingStyle`; whether other brands mirror your action buttons is unverified | n/a |

Sources for Meta gestures: [Neural Band](https://www.meta.com/help/ai-glasses/764536076119235/) and
[touchpad](https://www.meta.com/help/ai-glasses/1405261544503794/) help pages,
[Web Apps input](https://wearables.developer.meta.com/docs/develop/webapps/build/input-and-navigation/),
[action button](https://www.meta.com/help/ai-glasses/1767196644651038/) (all read 2026-11-08); Ray-Ban Meta touchpad
from a [third-party guide, 2025-03-16](https://brandxr.io/ray-ban-meta-smart-glasses-guide). Android XR:
[physical input](https://developer.android.com/develop/xr/jetpack-xr-sdk/glasses/physical-input).

## Mapping to repeat, skip and hide

| Target | repeat | skip | hide | Notes |
|---|---|---|---|---|
| Even G2 | Tap | Swipe down (`SCROLL_BOTTOM_EVENT`) | Long press | Double tap on the root page = exit (review rule); keep the capture container from overflowing so swipes arrive |
| Meta Display, DAT | "Repeat" button | Optional "Skip" button | "Hide" button | Back ends the session: offer "show on glasses again" on the phone |
| Meta Web App, glasses browsers | Enter on a focused "Repeat" button | Enter on "Skip" | Enter on "Hide" | Arrows move focus through the browser's spatial navigation; do not handle them yourself (Meta: let the WebView own directional focus). Only a page with nothing focusable maps keys directly: Enter repeat, `ArrowDown`/`ArrowRight` skip, `ArrowUp`/`ArrowLeft` hide (`examples/live-captions/web-glasses` with `?buttons=0`) |
| Ray-Ban Meta, Oakley Meta | Play or pause (tap) | Next track (double tap) | Previous track (triple tap) or a phone button | Media keys are unverified on these glasses: always keep phone buttons |
| Rokid, custom view | Phone button; AI key in `BLOCK_AI` (experiment) | Phone button | Phone button, or automatic when the wearer closes the view, goes to the launcher or takes the glasses off | |
| Vuzix Z100 | 1 tap | 2 taps | Phone button or the display timeout | `maxNumTaps` 2 (recommended, as in the examples): every extra tap count delays each report. Use 3 taps for hide only if it must be on the glasses |
| Android XR | Tap on the focused card or button | Swipe to the next item | On-screen "Hide" button | Never on Back |
| RayNeo X3 Pro, native | `Click` | `SlideForward` | `LongClick` | Keep `DoubleClick` free for Back |
| MentraOS | Single tap | Swipe down | Long press | Avoid double tap on G2 |
| Halo | Button click | Button double click | Button long press | IMU taps as a second choice |
| USB-C, notifications | Phone UI, notification action, headset media key | Same | Same | The glasses give you nothing |

## Implementing the mappings

**One gate for every source** (Kotlin). Every adapter calls it; the app only sees actions.

```kotlin
class ActionGate(private val windowMs: Long = 300, private val sink: (InputAction) -> Unit) {
    private var lastAt = 0L
    var contentVisible = false            // set by the display

    fun offer(action: InputAction, nowMs: Long = SystemClock.uptimeMillis()) {
        // On a blank display only repeat (bring it back) counts; skip or hide there is usually a false tap
        if (action != InputAction.REPEAT && !contentVisible) return
        if (nowMs - lastAt < windowMs) return
        lastAt = nowMs
        sink(action)
    }
}
// Vuzix, maxNumTaps 2: override fun onTap(tapCount: Int) { if (tapCount == 1) gate.offer(REPEAT) else if (tapCount == 2) gate.offer(SKIP) }
// Rokid: onSessionClosed(CloseReason.GLASSES_EXIT) or onWearingStatusChanged(false) -> the app's hide path
// Meta DAT: button(label = "Hide", onClick = { gate.offer(InputAction.HIDE) })
```

**Even G2** (TypeScript, names from SDK 0.0.16 typings). A single tap has no `eventType`: treat a present envelope
without one as `CLICK_EVENT`, and test double tap and long press before tap.

```ts
import { OsEventTypeList, type EvenHubEvent } from '@evenrealities/even_hub_sdk'

export function evenAction(e: EvenHubEvent): 'repeat' | 'skip' | 'hide' | 'exit' | null {
  const types = [e.sysEvent, e.textEvent, e.listEvent]
    .filter((x) => x !== undefined)
    .map((x) => x!.eventType ?? OsEventTypeList.CLICK_EVENT)
  if (types.includes(OsEventTypeList.DOUBLE_CLICK_EVENT)) return 'exit' // root page: bridge.shutDownPageContainer(1)
  if (types.includes(OsEventTypeList.LONG_PRESS_EVENT)) return 'hide'
  if (types.includes(OsEventTypeList.SCROLL_BOTTOM_EVENT)) return 'skip'
  if (types.includes(OsEventTypeList.CLICK_EVENT)) return 'repeat'
  return null
}
// bridge.onEvenHubEvent((e) => { const a = evenAction(e); if (a) handle(a) })
```

**Web pages on glasses** (Meta Web Apps, glasses browsers). With real `<button>`s, let the browser move focus and
click on Enter; listen to `click`, never synthesise a second click, and do not handle arrow keys while focusable
controls exist ([Meta](https://wearables.developer.meta.com/docs/develop/webapps/build/input-and-navigation/): call
`preventDefault()` only when you mean to replace the default). Handle Back without trapping it:

```ts
// act() sends the shared action, leaveRoom() is your own exit path; Meta keeps five history entries
addEventListener('popstate', () => { act('hide'); leaveRoom() })   // Back means leave: do not push state to trap it
```

**Media keys from audio glasses or any Bluetooth headset** (Android). Android 8.0+ sends media buttons to "the last
app with a MediaSession that played audio locally"
([Android docs](https://developer.android.com/media/legacy/media-buttons)). `TextToSpeech` audio is played by the
TTS engine's process, so it may not make your app that app (unverified); a short earcon through your own player
should, by the rule above. Music apps the user opens later take the keys back.

```kotlin
fun headsetButtons(ctx: Context, gate: ActionGate) = MediaSession(ctx, "glasses-actions").apply {
    setCallback(object : MediaSession.Callback() {
        override fun onPlay() = gate.offer(InputAction.REPEAT)
        override fun onPause() = gate.offer(InputAction.REPEAT)       // the play/pause key toggles: both mean "again"
        override fun onSkipToNext() = gate.offer(InputAction.SKIP)
        override fun onSkipToPrevious() = gate.offer(InputAction.HIDE)
    })
    setPlaybackState(PlaybackState.Builder()
        .setActions(PlaybackState.ACTION_PLAY_PAUSE or PlaybackState.ACTION_PLAY or PlaybackState.ACTION_PAUSE or
            PlaybackState.ACTION_SKIP_TO_NEXT or PlaybackState.ACTION_SKIP_TO_PREVIOUS)
        .setState(PlaybackState.STATE_PLAYING, PlaybackState.PLAYBACK_POSITION_UNKNOWN, 1f)
        .build())
    isActive = true                                                     // release() when the session ends
}
```

**Media keys on iOS.** Remote commands go to the Now Playing app, which needs a non-mixable audio session and audio
it actually played ([WWDC22 session 110338](https://developer.apple.com/videos/play/wwdc2022/110338/)). `.duckOthers`
implicitly sets `.mixWithOthers` ([Apple](https://developer.apple.com/documentation/avfaudio/avaudiosession/categoryoptions-swift.struct/duckothers)),
so an app that ducks other audio for TTS receives no remote commands. Becoming Now Playing stops the user's music.

```swift
import MediaPlayer

func listenForHeadsetButtons(_ onAction: @escaping @Sendable @MainActor (InputAction) -> Void) {
  let c = MPRemoteCommandCenter.shared()
  let send: (InputAction) -> MPRemoteCommandHandlerStatus = { a in Task { @MainActor in onAction(a) }; return .success }
  c.togglePlayPauseCommand.addTarget { _ in send(.repeatCaption) }
  c.playCommand.addTarget { _ in send(.repeatCaption) }
  c.nextTrackCommand.addTarget { _ in send(.skip) }
  c.previousTrackCommand.addTarget { _ in send(.hide) }
  MPNowPlayingInfoCenter.default().nowPlayingInfo = [MPMediaItemPropertyTitle: "Captions"]
}
```

**Notification action buttons** (rung 4). Android: `Notification.Action` with a `PendingIntent.getBroadcast(...,
FLAG_IMMUTABLE)` per action and a `BroadcastReceiver` that calls the gate. iOS: a `UNNotificationCategory` with one
`UNNotificationAction` per shared action, handled in `userNotificationCenter(_:didReceive:)`. Both are implemented in
`examples/live-captions` (`NotificationDisplay.kt`, `NotificationDisplay.swift`).

Brand depth: Even (`npx skills add even-realities/everything-evenhub`, skill `even-handle-input`), Meta DAT (official
`inputs` skills), Vuzix ([smart-glasses-vuzix input](../../smart-glasses-vuzix/references/input.md)), Rokid
([smart-glasses-rokid input](../../smart-glasses-rokid/references/input.md)).

## Related
- [display-text-ladder.md](display-text-ladder.md), [ui-small-screens.md](ui-small-screens.md),
  [audio-routing.md](audio-routing.md), [troubleshooting.md](troubleshooting.md).
