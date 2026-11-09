# Troubleshooting the Z100 and the Ultralite SDK

Last checked: 2026-11-08. Verification: docs-only (no hardware test yet). Issue states and dates from GitHub on
2026-11-08. The SDK repos are quiet (6 issues in total, last SDK release March 2025), so expect few answers there.

## Symptom first

| Symptom | Likely cause | What to do |
|---|---|---|
| Android: `isAvailable()` stays `false` | Vuzix Connect not installed, or the SDK has not bound to it yet | Check the package (see [android.md](android.md)), wait a few seconds after start, then guide the user to Google Play |
| Android: available but `isLinked()` false | Glasses never paired in Vuzix Connect | Open Connect and pair there; your app cannot pair on Android |
| iOS: `isConnected` never becomes `true` | Your app never linked the glasses (each app links once) | Show `UltralitePickerController` or your own scan and `link` flow ([Display Process](https://support.vuzix.com/docs/display-process)) |
| iOS: scan returns `.BLUETOOTH_PERMISSION_NEEDED` or `.DISABLED` | No Bluetooth permission or Bluetooth off | Add `NSBluetoothAlwaysUsageDescription`; ask the user to enable Bluetooth |
| `requestControl` returns `false` | Not available, not linked or not connected | Check the three states in that order |
| Nothing appears after drawing | Missing `commit()`, or drawing before control was granted | Commit after every frame; configure only after the control grant |
| `sendText` shows nothing | Layout is `DEFAULT` or `CANVAS` | Use `TEXT_BOTTOM_LEFT_ALIGN`, `TEXT_BOTTOM_CENTER_ALIGN` or `NAVIGATION` |
| `createText` returns `-1` / `nil`, or old text vanishes | More than 7 text blocks, or ids from an earlier control | Reuse ids, `clear()` the canvas after each new grant |
| Image never shows | Over 9900 bytes, background over 640x480, or a 1-bit background | Shrink, use `CF_INDEXED_2_BIT` for backgrounds |
| Taps never arrive | `maxNumTaps` left at 0, or no control | Pass 1-3; [iOS #4](https://github.com/Vuzix/UltraliteSDK-releases-iOS/issues/4) |
| Display went black mid-session | Display `timeout` reached, user pressed power, or another app took control | Draw again (wakes the display); on Android watch `getControlledByMe()` |
| The last frame stays on the glasses after your app quits | Control never released | Call `releaseControl()` at session end and when your service stops |
| iOS: hints stop after the app went to background | Control lost or refused in background; iOS gives no signal | Re-request in the foreground; fall back to `sendNotification` |
| Notification shows only its title | Another app holds a non-default layout, so notifications only peek | Pass `peekText` (Android 1.5+), or show it on your own canvas; [Android #1](https://github.com/Vuzix/ultralite-sdk-android/issues/1) (open) |
| Arabic or Hebrew notification reversed | Bug before SDK 1.9 | Use 1.9; [Android #2](https://github.com/Vuzix/ultralite-sdk-android/issues/2) (closed) |
| Android `getBatteryStatus()` crashes your observer | It contains `null` while disconnected | Null-check every value |
| Gradle cannot resolve the SDK | JitPack missing, wrong version string or JitPack down | Add JitPack, use `1.9` (not `1.9.0`), cache dependencies in CI |
| Release build cannot reach the glasses, debug works | Unverified R8 interaction | Try `-keep class com.vuzix.ultralite.** { *; }` |

## Known issues and threads

- [ultralite-sdk-android #1](https://github.com/Vuzix/ultralite-sdk-android/issues/1) (open, 2025-02-10): notification
  message not displayed when the layout is not `DEFAULT`. Vuzix asked the reporter to open a support ticket.
- [ultralite-sdk-android #2](https://github.com/Vuzix/ultralite-sdk-android/issues/2) (closed, 2025-02-10): RTL text
  in `sendNotification` reversed; Vuzix said the fix ships in 1.9.
- [ultralite-sdk-android #3](https://github.com/Vuzix/ultralite-sdk-android/issues/3) (open, 2026-11-07): how long can
  the display run with timeout 0, and does it keep running with the phone locked. Unanswered: measure it yourself.
- [UltraliteSDK-releases-iOS #4](https://github.com/Vuzix/UltraliteSDK-releases-iOS/issues/4) (closed, 2025-05-18):
  `onTap(taps:)` does not exist and taps never fire; the fix was passing `maxNumTaps` / setting `maximumNumTaps`.
- [UltraliteSDK-releases-iOS #3](https://github.com/Vuzix/UltraliteSDK-releases-iOS/issues/3) (closed, 2025-02-25):
  CocoaPods support for Flutter and React Native, added with 1.9.0.
- [UltraliteSDK-releases-iOS #2](https://github.com/Vuzix/UltraliteSDK-releases-iOS/issues/2) (closed, 2024-09-16):
  watchOS use; Vuzix later added a SwiftUI sample with a watchOS app to the
  [iOS sample repo](https://github.com/Vuzix/ultralite-sdk-ios-sample).
- [MentraOS #3062](https://github.com/Mentra-Community/MentraOS/issues/3062) (open, 2026-06-02): pairing a Z100 from the
  Mentra app on Android flickers between screens; iOS unaffected. Relevant only on the MentraOS path.
- [MentraOS #4120](https://github.com/Mentra-Community/MentraOS/pull/4120) (merged, 2026-09-20): on Android the display
  was never powered off on clear; the fix calls `screenOff()` and wakes the display before every later render.
- Stack Overflow answers about Vuzix M100, M300, M400 or Blade (Android on the glasses) do not apply to the Z100.

## Support channels

- No public Vuzix developer forum for the Z100 was found (as of 2026-11-08). GitHub issues on the two SDK repos are
  read by Vuzix staff, who usually redirect to a support ticket.
- Tickets: [vuzix.com/pages/support](https://www.vuzix.com/pages/support); Vuzix staff also gave
  `technical_support@vuzix.com` in [iOS #2](https://github.com/Vuzix/UltraliteSDK-releases-iOS/issues/2).
- Docs: [support.vuzix.com](https://support.vuzix.com/docs/z100-software-integration) (Z100 integration pages last
  updated in January 2024).
- Community code that drives the Z100 on both platforms: the MentraOS drivers (Apache-2.0),
  [Android](https://github.com/Mentra-Community/MentraOS/blob/dev/mobile/modules/bluetooth-sdk/android/src/main/java/com/mentra/bluetoothsdk/sgcs/Mach1.kt)
  and [iOS](https://github.com/Mentra-Community/MentraOS/blob/dev/mobile/modules/bluetooth-sdk/ios/Source/sgcs/Mach1.swift).

## What not to do when stuck

- Do not decompile the AAR or the XCFramework to find out how something works: the licence forbids it (§3.3). Ask
  Vuzix, test on hardware, or read open-source integrations.
- Do not copy SDK files into your repo or ship a modified SDK.

## First day with hardware

Run these before you trust any `unverified` note in this skill:

1. Android: Connect missing, then installed but glasses not paired, then paired: check each state message.
2. Android: start a session, open another Z100 app, confirm `getControlledByMe()` emits `false`.
3. iOS: first link with the picker; relaunch the app and confirm `currentDevice` is restored.
4. iOS: take control in the foreground, lock the phone, push updates for 5 minutes; then repeat after
   `didBecomeActive`.
5. Taps: false-tap rate over a 20-minute session with `maxNumTaps` 1, 2 and 3; the delay of each mode.
6. Text: your languages (accents, Cyrillic, CJK, RTL) through `sendText`, canvas text and `LiveText`; first-use delay.
7. Budget: characters per line at 28 and 34 px across 600 px; compare with [display.md](display.md).
8. Latency: phone to glasses with `commit(callback)` / `requestAcknowledgement`.
9. Battery: one hour with display timeout 30 s versus 0.
