# Input: taps, power button and display events

Last checked: 2026-11-08. Verification: docs-only (no hardware test yet). Sources:
[User Input](https://support.vuzix.com/docs/user-input), the
[Android Javadoc](https://vuzix.github.io/ultralite-sdk-android/javadoc/com/vuzix/ultralite/EventListener.html), the
[iOS DocC](https://vuzix.github.io/UltraliteSDK-releases-iOS/documentation/ultralitesdk/) and the Vuzix
[power page](https://support.vuzix.com/docs/how-to-power-on-device).

## What the glasses offer

- **Taps on the frame.** "Touching any part of the frame will send a tap event. There is no differentiation between
  left-side or right-side touches" (Vuzix). Single, double and triple taps.
- **No** swipes, long presses, head gestures or IMU data in the SDK, and **no microphone**, so no voice commands on
  the glasses.
- **Power button.** Short press wakes or sleeps the display; hold 3 s to shut down; hold 12 s to factory reset
  ([reset page](https://support.vuzix.com/docs/how-to-factory-reset-the-z100)). Some pages say an 8 s hold enters
  pairing mode; we could not confirm that for the Z100. Your app is told about presses, but Vuzix discourages using the
  power button as general input (a brief, specific confirmation is acceptable).

## Turn taps on

Taps are reported only while you hold control **and** you asked for them:

- Android: `setLayout(layout, timeout, hideStatusBar, showTapAnimation, maxNumTaps)` (1.1+).
- iOS: `requestControl(layout:timeout:hideStatusBar:showTapAnimation:maxNumTaps:autoReleaseControlOnDisplayTimeout:)`,
  or set `maximumNumTaps` on `UltraliteBaseViewController` before `startControl()`.

| `maxNumTaps` | Reported | Delay before a tap is reported |
|---|---|---|
| 0 (default) | nothing | n/a |
| 1 | single taps | shortest |
| 2 | single and double | medium |
| 3 | single, double, triple | longest |

Any other value counts as 0. Pick the lowest number you need: in multi-tap mode the glasses wait after each tap to see
whether another follows. `showTapAnimation` shows a tap animation on the glasses. The official Android sample notes
that taps work in every layout.

## Receive taps

Android: implement `EventListener` (all methods have default bodies) and register it.

```kotlin
import com.vuzix.ultralite.EventListener
import com.vuzix.ultralite.UltraliteSDK

fun listen(sdk: UltraliteSDK, onTaps: (Int) -> Unit): EventListener {
    val listener = object : EventListener {
        override fun onTap(tapCount: Int) = onTaps(tapCount)               // 1, 2 or 3; more than 3 is not reported
        override fun onPowerButtonPress(turningOn: Boolean) { /* display going on (true) or off (false) */ }
        override fun onDisplayTimeout() { /* your timeout hit: consider clearing state */ }
    }
    sdk.addEventListener(listener)
    return listener                                                       // removeEventListener(listener) later
}
```

The callback thread is not documented; post to the main thread before touching UI.

iOS: observe `Notification.Name.tap`. The count is in `userInfo["tap"]`; DocC does not state its type and the official
sample casts it to `Int64`, so accept the common numeric types (see `tapCount(_:)` in the skill's `SKILL.md`). With
`UltraliteBaseViewController`, override `onTapEvent(taps:)`. There is no `onTap(taps:)`: code that overrides it does not
compile ([iOS #4](https://github.com/Vuzix/UltraliteSDK-releases-iOS/issues/4)). The `onTap(notification:)` family is
deprecated.

Other events:

| Event | Android `EventListener` | iOS `Notification.Name` / base VC |
|---|---|---|
| Power button | `onPowerButtonPress(turningOn)` | `.power_button` / `onPowerButtonEvent(isOn:)` |
| Display on / off | `onDisplayOn()`, `onDisplayOff()` (1.2+) | `.display_state` / `onDisplayStateEvent(isOn:)` |
| Display timeout | `onDisplayTimeout()` | `.displayTimeout` / `onDisplayTimeoutEvent()` |
| Scroll layout advanced | `onScrolled(isScreenEmpty)` (1.3+) | `.scrolled` |
| Disconnected | `getConnected()` emits `false` | `isConnected` listener, `onDisconnected()` |

The `userInfo` keys of the iOS notifications other than `.tap` are not documented on DocC. Log `userInfo` once on
hardware before relying on them (unverified).

## Map taps to app actions

Keep the gesture layer separate from the app: the glasses produce tap counts, your app consumes actions. The shared
actions used across this repo are `repeat`, `skip` and `hide`.

| Setup | 1 tap | 2 taps | 3 taps | Hide |
|---|---|---|---|---|
| `maxNumTaps = 2` (recommended) | `repeat` (show the last item again) | `skip` (next or dismiss) | n/a | display timeout or `screenOff()` |
| `maxNumTaps = 3` | `repeat` | `skip` | `hide` | explicit |
| `maxNumTaps = 1` (fastest) | one action only, for example `skip` | n/a | n/a | timeout |

Leave the power button to the system: users expect it to wake and sleep the display.

## False taps and debounce

Vuzix: "Although rare, false touch events may be detected," especially when the user adjusts the glasses or wipes
their forehead. Two cheap guards:

```kotlin
/** Drops taps that arrive while nothing is shown, and repeats within a short window. */
class TapFilter(private val windowMs: Long = 300) {
    private var lastAt = 0L
    var contentVisible = false

    fun accept(nowMs: Long = System.currentTimeMillis()): Boolean {
        if (!contentVisible || nowMs - lastAt < windowMs) return false
        lastAt = nowMs
        return true
    }
}
```

Make destructive actions (delete, send, end session) need confirmation on the phone, never a single tap.

## Input the glasses cannot give you

For anything beyond two or three actions, use the phone: on-screen controls, a watch app, headset media buttons
routed through your phone app, or voice through the phone microphone. The Z100 has nothing else to offer.
