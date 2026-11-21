# Android XR glasses (Projected activities, Jetpack Compose Glimmer)

Last checked: 2026-11-08. Verification: docs-only (no hardware test yet). Pointer coverage: Google ships official
skills, use them for the details.

## At a glance
- Display: Google uses two names now, **display glasses** (screen in the lens) and **audio glasses** (no screen,
  camera and speakers). No display glasses are on sale as of 2026-11-08; no vendor gives a date.
- How your app puts text on it: rung 1. A projected activity inside your phone app, UI in Jetpack Compose Glimmer.
  Rung 4 also works: phone notifications are bridged to both types under documented rules (shown on display
  glasses, read aloud on audio glasses).
- Input: touchpad on the frame (indirect pointer gestures), camera button (`TOGGLE_APP_CAMERA`), voice. System Back is
  swipe down on display glasses and swipe back on audio glasses.
- Microphone for your app: yes, over Bluetooth HFP (16 kHz) after `RECORD_AUDIO` and `BLUETOOTH_CONNECT`.
- Speaker: yes (standard Bluetooth audio).
- Phones / where your code runs: Android phone; the projected activity runs in your phone app's process.
- Publishing to everyone today: audio glasses through the normal Google Play mobile track; display glasses "stay
  tuned" ([package and distribute](https://developer.android.com/develop/xr/package-and-distribute)).
- Test without hardware: Android Studio Canary, Device Manager > XR > Display Glasses or Audio Glasses, paired with a
  host phone emulator.
- Official agent skill: `display-glasses-with-jetpack-compose-glimmer` and `projected-hardware` in `android/skills`.

## Status (as of 2026-11-08)
- Libraries are alpha: `androidx.xr.projected:projected` 1.0.0-alpha14 and `androidx.xr.glimmer:glimmer`
  1.0.0-alpha22 (both 2026-10-21). Recent Glimmer needs compileSdk 37.1, AGP 9.2.0 or newer and Kotlin 2.2
  ([release notes](https://developer.android.com/jetpack/androidx/releases/xr-glimmer)). Older toolchains (for example
  React Native apps pinned to AGP 8.x) cannot take it; plain Views in a projected activity still work.
- Google's setup page pins exact versions and asks you to use them even if newer ones exist.
- Audio glasses: Warby Parker opens pre-orders for its first Android XR collection on 2026-11-12 with delivery in the
  holiday season (company release via [press](https://9to5google.com/2026/11/05/android-xr-glasses-pre-order/)).
  Launch countries are not official; reports say the US and South Korea first (unverified).
- XREAL Aura runs Android XR on its own compute puck: optical see-through glasses for spatial apps, not the projected
  glasses API in this file. It is orderable now: XREAL's page has "Buy Now" and a launch offer "starting at $1,099"
  through the end of 2026 ([XREAL](https://www.xreal.com/aura), checked 2026-11-09). The lower price applies to orders
  from 2026-10-28, and shipping "is expected to start in mid-November" ([MIXED, 2026-10-29](https://mixed-news.com/en/?p=38674),
  press); we could not confirm that units have shipped.

## Getting text on the display
Declare a projected activity and start it with projected options from your phone UI. The manifest attributes and the
call below are on [the first-activity guide](https://developer.android.com/develop/xr/jetpack-xr-sdk/glasses/first-activity):

```xml
<activity
    android:name=".GlassesActivity"
    android:exported="true"
    android:requiredDisplayCategory="android.hardware.display.category.XR_PROJECTED">
    <intent-filter>
        <action android:name="android.intent.action.MAIN" />
        <category android:name="android.intent.category.XR_PROJECTED_LAUNCHER" />
    </intent-filter>
</activity>
```

```kotlin
@OptIn(ExperimentalProjectedApi::class)
fun openOnGlasses(activity: Activity): Boolean = try {
    val options = ProjectedContext.createProjectedActivityOptions(activity)
    activity.startActivity(Intent(activity, GlassesActivity::class.java), options.toBundle())
    true
} catch (e: IllegalStateException) {
    false // no projected device connected
}
```

For the UI, follow the official Glimmer skill (black background, focus-driven navigation, cards). For notifications,
see `notification-glasses.md`: high-importance channel, non-empty title, not ongoing unless it is a Live Update, and
the user must enable your app in the Glasses app.

## Pitfalls
- Do not build hardware services from `getApplicationContext()` while a projected activity exists: Google warns it can
  return the glasses' context. Use the activity context or `ProjectedContext.createHostDeviceContext()`.
- Glasses camera allows one stream at a time; CameraX's forced repeating stream stalls it (see the official
  `projected-hardware` skill).
- Google's policies for audio-only experiences ("all apps must comply") forbid persistent background recording or
  transcription when the wearer is not actively engaged on a user-initiated task, and using the mic array to identify
  non-wearer voices. Back swipe must always exit or go back, never a custom action
  ([quality guidelines](https://developer.android.com/docs/quality-guidelines/android-xr/augmented)).
- Notifications on audio glasses are read aloud by the system. If your app also speaks the same text, the user hears it
  twice (inference, test in the emulator's audio-only mode).
- `display-ai-glasses-with-jetpack-compose-glimmer` was renamed to `display-glasses-with-jetpack-compose-glimmer` in
  May 2026; some skill directories still list the old name.

## Official resources and skills
- Install (official Android CLI): `android skills add display-glasses-with-jetpack-compose-glimmer --project=.` and
  `android skills add projected-hardware --project=.`
- Claude Code plugin: `/plugin marketplace add android/skills`, then `/plugin install android-skills@android-skills`
- Skills CLI (community): `npx skills add android/skills --skill display-glasses-with-jetpack-compose-glimmer`
- https://github.com/android/skills (folders `xr/display-glasses-with-jetpack-compose-glimmer`, `xr/projected-hardware`)
- https://developer.android.com/develop/xr/devices
- https://developer.android.com/develop/xr/jetpack-xr-sdk/glasses/first-activity
- https://developer.android.com/develop/xr/jetpack-xr-sdk/glasses/physical-input
- https://developer.android.com/develop/xr/jetpack-xr-sdk/access-hardware-projected-context
- https://developer.android.com/develop/xr/jetpack-xr-sdk/glasses/notifications/behavior
- https://developer.android.com/develop/xr/jetpack-xr-sdk/run/emulator/glasses
