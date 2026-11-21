# Input: what reaches a phone app

Last checked: 2026-11-08. Verification: docs-only. Event names are from the CXR-L 1.1.x session API; the claim
that taps do not arrive comes from two independent community tests on real glasses (Android and iOS).

## The short answer

In a `CUSTOM_VIEW` session **touchpad taps and swipes do not reach your phone app**. The glasses system consumes
them (you hear the system click), and nothing arrives through CXR-L. Sources:
an Android test on Global Hi Rokid G1.12.10 found no callback for operator taps
([TroroOrosi/rokid-docscan-starter](https://github.com/TroroOrosi/rokid-docscan-starter)); an iOS test reports "no key
events reach either companion SDK" in custom view mode
([fasaiph/rokid-cxr-glasses](https://github.com/fasaiph/rokid-cxr-glasses)). The Rokid docs route key events only
through a glasses-side app.

So: put buttons for repeat, skip and hide in your **phone** UI (or on a watch, or on a Bluetooth remote paired with
the phone), and treat the glasses as output.

## What you do get

| Signal | API | Use it for |
|---|---|---|
| Wearer started the Rokid assistant | `ISessionLifecycleCbk.onSessionPaused(PausedReason.AI_ASSIST)`, then `onSessionResumed()` | stop sending, re-send latest text on resume |
| Bluetooth gap | `onSessionPaused(PausedReason.BT_DISCONNECTED)` | show "reconnecting" on the phone |
| Wearer left your view | `onSessionTerminating(TerminatingReason.GLASSES_APP_EXIT, ms)`, then `onSessionClosed(CloseReason.GLASSES_EXIT)` | treat as "hide"; do not reopen until there is a reason |
| Wearer went to the glasses home screen | `IGlassesEventListener.onLauncherResumed()` | same as above |
| Glasses on / off the head | `IGlassesEventListener.onWearingStatusChanged(Boolean)` | pause captions while the glasses are off |
| Screen off / on | `onScreenOff()`, `onScreenOn()` | stop updates while off |
| AI key while blocking the assistant | `onAiWake()` with `AiInterceptMode.BLOCK_AI` | a single "button", see below |

`IGlassesEventListener` also has `onGlassesAppResumed`, `onGlassesAppPaused`, `onDeviceInfoChanged` and
`onAiInterruptChanged`. All listener methods have default implementations; override only what you use.

```kotlin
import com.rokid.cxr.session.IGlassesEventListener

val glassesEvents = object : IGlassesEventListener {
    override fun onWearingStatusChanged(wearing: Boolean) { if (!wearing) captions.pause() else captions.resume() }
    override fun onScreenOff() { captions.holdUpdates(true) }
    override fun onScreenOn() { captions.holdUpdates(false) }
    override fun onLauncherResumed() { captions.hiddenByWearer() }
}
// session.addGlassesEventListener(glassesEvents) before connect; removeGlassesEventListener on teardown.
```

(`captions` stands for your own controller.)

## The AI key as one button (experiment)

With `SessionConfig(aiInterceptMode = AiInterceptMode.BLOCK_AI, ...)` the docs say a press of the AI key calls
`onAiWake()` instead of pausing your session. That gives you one physical input, for example "repeat the last line".
Unverified points: whether the system assistant is fully suppressed, and our notes on the binary flag this mode as
deprecated in the SDK's own log text. Treat it as an experiment behind a setting, and tell the user that the Rokid
assistant is blocked while your view is open.

## Real touchpad events: put an app on the glasses

To get click, double click, long press and swipes you need code on the glasses. Two ways:

1. **CXR-L `CUSTOM_APP` + CXR-S.** Your phone app opens a session with `SessionType.CUSTOM_APP`, naming your glasses
   package (and since 1.1.1 an APK path the SDK installs on connect). Your glasses APK uses CXR-S
   (`cxr-service-bridge`) to talk back. The CXR-L docs have chapters on the glasses-side app, custom commands, and
   keys and system broadcasts. On the phone, custom messages arrive through
   `CxrSession.addCustomCmdCallback(ICustomCmdSessionCallback)` (`onCustomCmdResult(name, bytes)`), and you send with
   `sendCustomCmd(...)`; custom commands do not work in `CUSTOM_VIEW`.
   Community reports to read first:
   - [Anezium/Rokid-Relay](https://github.com/Anezium/Rokid-Relay) ships a phone app that installs and starts its
     glasses helper through CXR-L on Global Hi Rokid.
   - [fasaiph/rokid-cxr-glasses](https://github.com/fasaiph/rokid-cxr-glasses) (iOS phone, August 2026) found small
     custom commands unreliable after the glasses app idles and glasses-to-phone payloads arriving empty; it moved
     return data to HTTPS from the glasses, which have their own Wi-Fi.
   - Firmware updates have broken third-party APK installs before (YodaOS 1.19.009, reported in
     [Anezium/Rokid-APKs](https://github.com/Anezium/Rokid-APKs/issues/2)). Log the firmware version.
2. **A standalone app on the glasses.** YodaOS-Sprite is Android-based; on-glasses apps read the touchpad as key
   events. That is a different product path: see [RealComputer/GlassKit](https://github.com/RealComputer/GlassKit)
   (`npx skills add RealComputer/GlassKit`, MIT) and Rokid's bare-metal documentation linked from
   https://developerdoc.rokid.com/sdk. Lock the activity to portrait.

## Mapping to the shared actions

The caption protocol of the `smart-glasses-live-captions` skill uses `repeat`, `skip` and `hide`. For Rokid in
`CUSTOM_VIEW`:

| Action | Trigger |
|---|---|
| `repeat` | phone button; optionally the AI key in `BLOCK_AI` mode |
| `skip` | phone button |
| `hide` | phone button, or automatically on `GLASSES_EXIT`, `onLauncherResumed` or the glasses coming off |

## Ring

Rokid announced the Rokid Ring in China on 2026-10-27, next to Rokid Glasses 2 and Rokid Color (swipes, taps,
finger snap; [Wareable](https://www.wareable.com/wearable-tech/rokid-glasses-2-color-ring-announcement-international-availability), press).
Whether its events reach phone apps through CXR-L is unknown as of 2026-11-08.
