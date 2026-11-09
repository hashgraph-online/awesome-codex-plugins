# Troubleshooting glasses apps by symptom

Read this when something on the glasses does not behave: start from the symptom, follow the branch that matches, and
each leaf gives the likely cause, how to confirm it, the fix and a link.

Last checked: 2026-11-08. Verification: docs-only (no hardware test yet). Causes come from vendor docs and public
issue trackers; none were reproduced on hardware by us.

Brand-specific tables go deeper: [Rokid troubleshooting](../../smart-glasses-rokid/references/troubleshooting.md),
[Vuzix troubleshooting](../../smart-glasses-vuzix/references/troubleshooting.md), and the Pitfalls section of each
brand file in [brands/](brands/).

Before any branch, make the problem visible:
- Log every send to the glasses with its result code and a timestamp, and log every link state change.
- Log versions: glasses firmware, companion app (Meta AI, Hi Rokid, Vuzix Connect, Even app) and SDK.
- Run the same flow against the simulator or a fake ([testing-without-hardware.md](testing-without-hardware.md)). If
  the fake is fine and the glasses are not, the problem is in the link, the companion app or the device.

## 1. Nothing appears on the glasses

**Is the link up (your state says connected or started)?** If not, go to section 3.

**The send call returned an error:**

| Leaf | Likely cause | Confirm | Fix | Link |
|---|---|---|---|---|
| Even: `createStartUpPageContainer` returns 1 | Called twice, often after hot reload | Happens only after an edit | Restart the simulator or relaunch the plugin; create once per launch | [#32](https://github.com/even-realities/everything-evenhub/issues/32) |
| Even: returns 2 or 3 | Oversize or out of memory | Count containers and text length | Max 8 text plus 4 image containers; 1000 characters on create | [even-g2.md](brands/even-g2.md#getting-text-on-the-display) |
| Meta: `addDisplay` or `sendContent` fails | Display added before the session reached `STARTED`, or session not started by the wearer | Print the session state before the call | Start from a button; add Display on `STARTED` | [meta-display.md](brands/meta-display.md#dat-display-flow-and-minimal-kotlin) |
| Rokid: `SESSION_NOT_STARTED` / `SESSION_PAUSED` | Sent before `onSessionStarted`, or the Rokid assistant is in front | Lifecycle log | Keep the latest text, send it on start and resume | [Rokid skill](../../smart-glasses-rokid/SKILL.md#the-core-flow) |
| Vuzix: `requestControl` is `false` | SDK not available, glasses not linked or not connected | Check the three states in that order | Fix the first state that is false | [Vuzix troubleshooting](../../smart-glasses-vuzix/references/troubleshooting.md) |

**The call succeeded but the display stays empty:**

| Leaf | Likely cause | Confirm | Fix | Link |
|---|---|---|---|---|
| Any brand, dark or grey text | Black is "off" on these displays; dark colours are near invisible | Send pure white or full green | Bright text on black | [ui-small-screens.md](ui-small-screens.md) |
| Vuzix | No `commit()`, drawing before control, or `sendText` on the `CANVAS` layout | Add `commit(callback)` and log it | Commit every frame, configure after the grant | [Vuzix skill](../../smart-glasses-vuzix/SKILL.md#pitfalls) |
| Rokid | Indented JSON, `id` outside `props`, or a Global Hi Rokid build that acks without redrawing | Same JSON as one line; try recreating the session | Compact JSON from a library; recreate-the-session fallback | [Rokid display](../../smart-glasses-rokid/references/display.md) |
| Even | Script without glyphs (dropped silently) or `textColor` 0 | Same call with ASCII text | Filter text to verified glyphs; colour 4 | [#37](https://github.com/even-realities/everything-evenhub/issues/37) |
| Meta | Panel dimmed after 20 s and asleep at 25 s; no API to wake it | Touch the glasses, content returns | Earcon or short TTS when the wearer must look | [discussion #152](https://github.com/meta/meta-wearables-dat-android/discussions/152) |
| Notification rung | App not enabled in the companion app, low-importance or ongoing channel, empty title, Focus mode | `adb shell dumpsys notification`; another app's notification shows | High-importance non-ongoing channel; post once during onboarding (Even lists only apps that posted); iOS "Show Previews: Always" for Even | [notification-glasses.md](brands/notification-glasses.md#pitfalls) |
| USB-C glasses, Android | Presentation went to the wrong display or was refused | Log `display.displayId` and catch `InvalidDisplayException` | Filter built-in displays; listen for display add and remove | [usb-c-displays.md](brands/usb-c-displays.md#pitfalls) |
| USB-C glasses, iOS | iOS 27 connects the scene only after a scene accessory is registered; mirroring while not in the foreground | Check `UIApplication.shared.openSessions` roles | Register the accessory; keep the app in front | [usb-c-displays.md](brands/usb-c-displays.md) |
| Web app on the glasses | See section 6 | | | |

## 2. It worked, then stopped

**After the phone locked or your app went to the background:**
- Even plugin, iOS, screen turns white: iOS killed the WebView content process and the host does not reload it
  ([#16](https://github.com/even-realities/everything-evenhub/issues/16)). Confirm: only after time in the background.
  Fix: persist state on every change, repaint on `FOREGROUND_ENTER`. A QR-sideloaded build stops on lock by design; test
  with a private or beta build ([even-g2.md](brands/even-g2.md#testing-without-hardware)).
- Android, updates stop or the transcript goes empty: process frozen or mic silenced. Confirm with `adb shell dumpsys
  activity services <package>` and `isClientSilenced()`. Fix: a typed foreground service started while visible;
  battery-optimisation exemption for your app and the companion app ([audio-routing.md](audio-routing.md#background-audio)).
- iOS, Vuzix stops after backgrounding: control in the background is undocumented and lost silently. Fix: re-request on
  `didBecomeActive`, fall back to `sendNotification` ([Vuzix iOS](../../smart-glasses-vuzix/references/ios.md#background-and-the-locked-phone)).
- USB-C glasses show a clock instead of your text: the lock screen owns external displays (AOSP keyguard
  presentation). Fix: `FLAG_KEEP_SCREEN_ON` while a session runs ([usb-c-displays.md](brands/usb-c-displays.md#pitfalls)).
- Meta Web App freezes: a hidden page suspends timers. Fix: close the socket on `hidden`, reconnect and fetch the
  latest state on `visible` ([meta-display.md](brands/meta-display.md#web-app-minimal-page)).

**After some time with no input:** Meta panel sleep (20/25 s), Rokid screen off after about 20 s, the Vuzix `timeout`
you passed to the layout, Android XR display snooze. On-glasses Meta `Speech` "silently stops reporting text" after
about a minute ([known issues](https://wearables.developer.meta.com/docs/develop/dat/knownissues/)): restart the
capability. Even's `audioControl` can stop delivering frames until reopen
([#35](https://github.com/even-realities/everything-evenhub/issues/35)): watch for "no frames for 3 s" and say so on
the glasses.

**After the wearer did something:**
- Meta Back (two-finger temple tap or band gesture) ends the DAT session and is not delivered to your app
  ([ios #349](https://github.com/meta/meta-wearables-dat-ios/issues/349)). Fix: on-screen "Hide", "show again" on the phone.
- Rokid `onSessionClosed(GLASSES_EXIT)`: the wearer closed your view. Reopen only on a new user action.
- Rokid `onSessionPaused(AI_ASSIST)`: the assistant is in front; wait for resume.
- Vuzix `getControlledByMe()` emits `false`: another Z100 app took the display (last requester wins). Never re-request
  in a loop.
- Meta Developer Mode: registering a second dev app unregisters the first.

**After a disconnect, out of range or a glasses restart:**
- Meta session `STOPPED` is terminal: create a new session. Sessions "ended by device" on some glasses releases
  ([android #227](https://github.com/meta/meta-wearables-dat-android/issues/227)); a dead data link sometimes needs a
  glasses reboot ([android #208](https://github.com/meta/meta-wearables-dat-android/issues/208)).
- Rokid `LINK_LOST` or `CHAIN_TORN`: the token is void and a closed session cannot reconnect. Re-authorise, then create
  a new session.
- Vuzix: everything you configured is gone after control is lost; rebuild the canvas on the next grant.

**After an update (firmware, companion app, SDK):** Meta's on-glasses DAT app missing after an OTA
([ios #245](https://github.com/meta/meta-wearables-dat-ios/issues/245)); camera capture after v128 needs a glasses
reboot (known issue); Even SDK 0.0.14 and 0.0.15 repeat timer callbacks (use 0.0.16) and SDK timers clash with native
timer ids ([#47](https://github.com/even-realities/everything-evenhub/issues/47)); a Rokid firmware update broke APK
install from the phone ([Rokid-APKs #2](https://github.com/Anezium/Rokid-APKs/issues/2)). Pin versions, read changelogs
before updating test devices, and record the versions with every bug.

## 3. Registration or pairing fails

**Meta (DAT):**
- `DAT_APP_ON_THE_GLASSES_UPDATE_REQUIRED`. Check in this order: Meta AI app V292+ and glasses V128+ for DAT 1.0.1;
  `Wearables.isDevMode` (it resets if you call `startRegistration()` while registered, or after a reinstall);
  `APPLICATION_ID` `0` in Developer Mode; glasses battery above 10%. Recover with one unregister plus one register,
  then one `Wearables.reset()` plus `initialize()` (never in a loop), then reboot the glasses
  ([android #192](https://github.com/meta/meta-wearables-dat-android/issues/192), [ios #180](https://github.com/meta/meta-wearables-dat-ios/issues/180)).
  It has also been a Meta server bug ([android #97](https://github.com/meta/meta-wearables-dat-android/issues/97)), so if
  everything checks out, wait and retry before rewriting code.
- `NO_ELIGIBLE_DEVICE`. Android: grant `BLUETOOTH_SCAN` ("Nearby devices") as well as `BLUETOOTH_CONNECT`; detection
  fails silently without it ([android #144](https://github.com/meta/meta-wearables-dat-android/issues/144)). iOS: create
  the `AutoDeviceSelector` early or wait for an active device. Ray-Ban Meta Audio never appears: not supported by DAT.
- Registration loops or never calls back. Android: register from a `ComponentActivity` that stays alive until Meta AI
  returns ([android #223](https://github.com/meta/meta-wearables-dat-android/issues/223)). `startRegistration()` fails
  silently with Developer Mode off ([ios #109](https://github.com/meta/meta-wearables-dat-ios/issues/109)). iOS Beta: a
  version or ID mismatch in Developer Center ([ios #219](https://github.com/meta/meta-wearables-dat-ios/issues/219)).
- Registered but the device list stays empty after unpairing ([android #197](https://github.com/meta/meta-wearables-dat-android/issues/197)).
- A store user sees "Error loading this integration": they are not in your Beta channel; see [publishing.md](publishing.md).
- `INSUFFICIENT_SDK_VERSION` needs a new build; `CAPABILITY_DENIED` can be per-user server gating
  ([version dependencies](https://wearables.developer.meta.com/docs/develop/dat/version-dependencies/)).

**Rokid (CXR-L through Hi Rokid):**
- Authorisation never calls back: no compatible Hi Rokid. Call `checkRokidAppCompatibility()` first and add a timeout.
- Worked before a restart, now fails: the Global or China choice lives in the process; authorise again (silently)
  before every `connect`. With both builds installed the China build wins; uninstall the unused one.
- `BT_NOT_CONNECTED` / `LINK_NOT_READY`: glasses paired in Android settings but not connected inside Hi Rokid.
- Community wrappers stuck "connecting" on Global Hi Rokid G1.12+: use the official `client-l` 1.1.2.
- Full table: [Rokid troubleshooting](../../smart-glasses-rokid/references/troubleshooting.md#authorisation-and-connection).

**Vuzix Z100:** Android `isAvailable()` false means Vuzix Connect is missing or not bound yet (wait a few seconds);
`isLinked()` false means the glasses were never paired in Connect. iOS `isConnected` never true means your app never
linked the glasses (each app links once). Control not granted: see section 1.
[Vuzix troubleshooting](../../smart-glasses-vuzix/references/troubleshooting.md#symptom-first).

**Others:** Even developer section missing in the phone app: force-quit and reopen, and check the moved entry point
([#34](https://github.com/even-realities/everything-evenhub/issues/34)); beta testers must show `Active`. Android XR
emulator pairing: see Google's [glasses emulator troubleshooting](https://developer.android.com/develop/xr/jetpack-xr-sdk/run/emulator/glasses-troubleshoot).
Halo on iOS already connected to the system may not advertise: look it up with
`retrieveConnectedPeripherals(withServices:)` ([brilliant-labs.md](brands/brilliant-labs.md#pitfalls), unverified).

## 4. Text is cut, wrapped wrong or missing characters

- **Characters missing.** Even drops Arabic, Hebrew, Thai and Devanagari without a placeholder and has no emoji
  ([#37](https://github.com/even-realities/everything-evenhub/issues/37)); Halo fonts are ASCII only; Korean was split
  into single jamo on G1 through MentraOS ([#3740](https://github.com/Mentra-Community/MentraOS/issues/3740)); Meta DAT
  glyph coverage is undocumented. Confirm with one test string per script. Fix: filter to a verified glyph set, render
  that text to an image where the SDK allows, or keep that language on the phone.
- **Right-to-left text reversed.** Vuzix notifications before SDK 1.9 ([android #2](https://github.com/Vuzix/ultralite-sdk-android/issues/2));
  Rokid RTL is unknown ([rokid/community #20](https://github.com/rokid/community/issues/20)). Test before you promise RTL.
- **Cut at the end, or not updated at all.** Hard limits: Even 1000 characters on create, 2000 on upgrade, and
  simulator 0.9.5 rejects (returns `false`) a rebuild or upgrade over about 1000 UTF-8 bytes (our run, 2026-11-09);
  more than 7 Vuzix canvas texts overwrite older ones; Rokid's visible area is smaller than its 480x640 Android display.
  No brand scrolls live text for you ([#45](https://github.com/even-realities/everything-evenhub/issues/45)): keep the
  tail that fits yourself.
- **Wrapped in the wrong place.** You budgeted characters, the glasses wrap pixels in a proportional font. Measure
  (Even: `measureTextWrap` in `@evenrealities/pretext`), or use the per-target budgets in
  [display-text-ladder.md](display-text-ladder.md) and [ui-small-screens.md](ui-small-screens.md). Halo has no word
  wrap at all.
- **Text broken by quotes or new lines.** JSON built by string concatenation (Rokid's sample helper does not escape).
  Build it with a JSON library.
- **Lines flicker, arrive late or out of order.** More than one write in flight. Keep one in flight and let the newest
  partial result replace queued ones; a few updates per second is the ceiling on BLE links.

## 5. Audio breaks when the camera or display starts

- **Meta, display or camera session ends when the mic opens.** HFP ends Display sessions
  ([android #210](https://github.com/meta/meta-wearables-dat-android/issues/210), [ios #342](https://github.com/meta/meta-wearables-dat-ios/issues/342))
  and ended camera sessions on firmware `72387580077200100` ([android #206](https://github.com/meta/meta-wearables-dat-android/issues/206));
  Meta staff (2026-11-04) say glasses software 192.1 fixes most displayless cases, Display later (unconfirmed). Log the
  glasses version with the bug. Confirm: the end
  follows the route change to `.bluetoothHFP` / SCO. Fix: phone mic for captions; for camera plus glasses mic, start HFP
  first, wait for the route, verify it, then start the stream. The phone-call UI on the display
  ([ios #186](https://github.com/meta/meta-wearables-dat-ios/issues/186)) and failing photos in HFP
  ([ios #260](https://github.com/meta/meta-wearables-dat-ios/issues/260)) have the same root.
- **Output turns mono or quiet when recording starts.** Something opened HFP: your `setCommunicationDevice`, the iOS
  `.voiceChat` mode, voice processing, or another app. Confirm with the current route. Fix:
  [audio-routing.md](audio-routing.md#ios-setup-swift).
- **Mic stream stops while the vendor assistant runs.** Rokid pauses your session (expected, resumes); Mentra lets the
  assistant hear and answer the same speech ([#3893](https://github.com/Mentra-Community/MentraOS/issues/3893)).
- **Android `AudioRecord` delivers silence.** A higher-priority capture (assistant, call, `VOICE_COMMUNICATION` app)
  won. Confirm with `isClientSilenced()`. Fix: tell the user; retry when it ends.
- **Even mic returns `false` or no frames.** Start the glasses source only after the startup page exists; reopen the
  plugin if it stays off ([#35](https://github.com/even-realities/everything-evenhub/issues/35)); `getUserMedia` does not
  work in the iOS WebView ([#11](https://github.com/even-realities/everything-evenhub/issues/11)).
- **Android XR camera stalls.** The glasses allow one stream at a time and CameraX's forced repeating stream blocks it
  (official `projected-hardware` skill, [android-xr.md](brands/android-xr.md#pitfalls)).
- **USB-C glasses: capture moved to the glasses.** Pin the built-in mic with `setPreferredDevice`.

## 6. Web app or WebView goes white or loses its WebSocket

- **White page.** Even on iOS: WebView killed in the background ([#16](https://github.com/even-realities/everything-evenhub/issues/16)).
  Meta Web Apps: stale build (Restart from the app menu), SVG favicons fail, an exception before the first render with
  no console on the glasses; log errors to your server and load the page in the simulator extension.
- **Socket never connects.**
  - Even: the origin is not in the `network` whitelist (exact origin, including `wss://`) or CORS headers are missing
    ([templates #1](https://github.com/even-realities/evenhub-templates/issues/1)).
  - Mixed content: an HTTPS page cannot open `ws://`. Meta Web Apps are HTTPS only; on Snap, `ws://` needs Experimental
    APIs, which block publishing. Serve `wss://` with a valid certificate (a TLS tunnel works for development).
  - Android apps and WebViews block cleartext by default (targetSdk 28+); allow your dev host in a network security
    config or use TLS.
  - `localhost` on the phone or glasses is the device itself: use the LAN IP, `adb reverse tcp:8787 tcp:8787` on
    Android, or a tunnel. The Mentra CLI may print a WSL or Tailscale address the phone cannot reach
    ([#3889](https://github.com/Mentra-Community/MentraOS/issues/3889)).
- **Socket drops after a while.** The page went hidden or the WebView was backgrounded; tunnels and proxies close
  idle sockets. Reconnect with backoff, send a ping every 20-30 s, and catch up through the HTTP fallback
  (`GET /latest?room=CODE` in the shared caption protocol). On Meta Display, joining glasses Wi-Fi has dropped
  connections after 6 s ([discussion #212](https://github.com/meta/meta-wearables-dat-android/discussions/212)).
- **Install fails.** Meta Web Apps: Developer Mode prompt missing on iOS ([#21](https://github.com/meta/meta-wearables-webapp/issues/21)),
  menu missing on Android ([#26](https://github.com/meta/meta-wearables-webapp/issues/26)), deep link "Something went
  wrong" ([#29](https://github.com/meta/meta-wearables-webapp/issues/29)), and an unencoded `?room=` dropped from the QR
  deep link (percent-encode both values).
