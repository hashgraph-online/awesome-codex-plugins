# Haptics (Taptic Engine) and device features in Mini Apps

How a Mini App uses the phone itself: haptic feedback (the Taptic Engine on iPhone, the vibration motor on
Android), motion sensors, location, biometrics, fullscreen and orientation, home-screen shortcuts, QR scanning,
the clipboard, sharing and downloads. Read it before adding any of them, and when reviewing an app that already
uses them. Verified against https://core.telegram.org/bots/webapps (Bot API 10.5) on 2026-11-24.

Labels: **[Official]** Telegram's Mini Apps page; **[API]** the member catalog (`scripts/webapp_lookup.py`);
**[Heuristic]** this skill's rule. Kit: `examples/mini-apps/_kit/tma.ts` (`tma.haptic`, `tma.motion`,
`tma.location`); live demo: the gallery's **Device** group in the stand (`scripts/preview_miniapp.py`).

## 0. Before adding any device feature

Answer three questions and write the answers in the plan:

1. **What does the user gain?** A haptic confirms something the user did; a sensor or location saves them a
   step. "It feels premium" is not a reason: decoration with vibration or sensors is slop (anti-slop §4).
2. **What happens without it?** Desktop, the web client and older clients have none of these. The app must
   work, and say why something is missing, when the feature is unavailable or refused **[Heuristic]**.
3. **What does it cost?** Sensors drain the battery and can identify a device; location and biometrics are
   personal data; every permission prompt costs trust. Ask late, ask once, explain first **[Heuristic]**.

## 1. Haptics: `Telegram.WebApp.HapticFeedback` (6.1)

### 1.1 What the API is

Three calls, all fire-and-forget; Telegram "may play the appropriate haptics", so the app never relies on
them being felt **[Official]**:

| Call | Values | Telegram's meaning |
|---|---|---|
| `impactOccurred(style)` | `light`, `medium`, `heavy` | a collision between small, medium, large UI objects |
| | `rigid`, `soft` | a collision between hard or inflexible objects; between soft or flexible ones |
| `notificationOccurred(type)` | `success`, `warning`, `error` | a task or action succeeded, produced a warning, failed |
| `selectionChanged()` | — | the user changed a selection. Not when they make or confirm one |

Platform reality **[Heuristic]**: on iPhone these map to the Taptic Engine's patterns and feel distinct; on
Android they map to the vibration motor, and cheap devices blur the styles or drop light ones; Telegram Desktop,
macOS and the web client play nothing. The user can turn system haptics off. So: **a haptic is never the only
signal**. Every haptic accompanies a visible change.

### 1.2 Which haptic for which moment

| Moment in the interface | Haptic | Kit |
|---|---|---|
| Segmented control, tab chip, toggle, radio row, checkmark row changes | selection | `tma.haptic.select()` |
| A picker or slider passes a detent (each value step, not each pixel) | selection | `select()` |
| Stepper + / −, add to cart, favourite, copy to clipboard, a quick action | light impact | `tap()` |
| A long press opens a menu; a drag lifts an item; a pull-to-refresh crosses its threshold (once) | medium impact | `impact('medium')` |
| A dragged item snaps into place; a value hits its limit (minimum, maximum, end of a list) | rigid impact | `impact('rigid')` |
| An elastic or springy element settles (a sheet lands, a card returns) | soft impact | `impact('soft')` |
| A heavy, meaningful action lands (a game hit, a big reward card flips) | heavy impact | `impact('heavy')` |
| The server confirmed a payment, a booking, a save | success | `success()` |
| Something needs attention but did not fail (a limit is close, an item is almost sold out, a timer ends) | warning | `warning()` |
| The server refused, validation failed on submit, the payment failed | error | `error()` |
| Scrolling, typing, hover, ordinary navigation taps, opening a screen, timers, animations | **none** | — |

Rules **[Heuristic]**:
- **One haptic per user moment.** A tap that saves and navigates plays one haptic, not two. The kit plays a
  repeated pattern once per 80 ms burst, so a drag across values or a double tap cannot buzz.
- **Outcome haptics come from the outcome.** `success` fires when the server's answer arrives, not when the
  button is tapped; a tap that starts a request plays nothing or `tap()` at most. A payment's `success` comes
  after the order is confirmed (`tma.watchOrder`, [payments.md](payments.md)).
- **After the change, never before.** The haptic follows the visible state change in the same frame or right
  after it; a haptic for something that then fails is a lie.
- **Selection means change.** `selectionChanged` on every value step of a picker; never on the final
  confirmation (that is `success`, or nothing).
- **Never in streams.** No haptic inside `scroll`, `pointermove` or `input` handlers, timers or animation
  frames (lint MA36). A sensor-driven game throttles to its own events (a collision), not
  to frames.
- **Never as decoration.** No haptic on launch, on a hero animation, on a timer tick, as a "brand" pulse.
- **Games and long sessions get a switch.** "Vibration" in the app's settings, stored in DeviceStorage or
  CloudStorage, wired to `tma.haptic.setEnabled()`.
- **Native controls already play their own.** Telegram's popups and invoice sheet handle their feedback; do
  not add a haptic on top of `showPopup` or `openInvoice` opening.

### 1.3 Code

```ts
const tma = createTma();
tma.haptic.select();                 // selection changed
tma.haptic.impact('rigid');          // snapped to a limit
const ok = tma.haptic.success();     // false when not played: below 6.1, outside Telegram, turned off, or a repeat
tma.haptic.setEnabled(false);        // the in-app switch
```

Without the kit: check `Telegram.WebApp.isVersionAtLeast('6.1')` and that `HapticFeedback` exists, then call
`Telegram.WebApp.HapticFeedback.impactOccurred('light')`. Do not wrap it in try/catch to "test" support.

## 2. Motion sensors: Accelerometer, Gyroscope, DeviceOrientation (8.0)

| Object | Values | Use |
|---|---|---|
| `Accelerometer` | `x`, `y`, `z` in m/s² (gravity included) | shake, tilt games, step-like motion |
| `Gyroscope` | `x`, `y`, `z` rotation rate in rad/s | steering, fast rotation |
| `DeviceOrientation` | `alpha`, `beta`, `gamma` in radians; `absolute` | tilt parallax, level, compass (`need_absolute: true` gives attitude to magnetic north) |

Each has `start({refresh_rate}, cb)`, `stop(cb)`, `isStarted` and the events `…Started`, `…Changed`,
`…Stopped`, `…Failed` (`accelerometerChanged`, `gyroscopeChanged`, `deviceOrientationChanged`, …).
`refresh_rate` is 20-1000 ms (default 1000) and may not be honoured on every platform **[API]**.

Rules **[Heuristic]**:
- **Start on purpose, stop always.** Start when the screen that needs it opens or the user turns the feature
  on; stop when the screen closes, the app is hidden (`deactivated`) and on dispose (lint MA37). The kit's
  `tma.motion(sensor, onData, {refreshMs, absolute})` returns `stop()` and pauses itself while hidden.
- **Slowest rate that looks right.** 50-100 ms for tilt effects and a level, 20-33 ms only for games.
- **Subtle and optional.** A tilt parallax stays within about 12°; `prefers-reduced-motion` turns it off
  (`.tma-tilt`). Nothing important is reachable only by moving the phone.
- **Fallback.** `motion()` returns null below 8.0 and on Desktop; `…Failed` means no sensor or no access:
  show the static version and, for games, a touch control.
- **Keep readings on the device.** Raw motion data can identify a device; send results ("level completed"),
  not streams.
- **No shake gestures for important actions.** They fire by accident and are invisible; at most a shortcut
  for something also on screen.

## 3. Location: `LocationManager` (8.0)

Flow **[API]**: `init()` → read `isLocationAvailable` → `getLocation(cb)`; the callback gets `null` when access
was not granted, else `LocationData` (`latitude`, `longitude`, `altitude`, `course`, `speed`, the matching
`*_accuracy` fields; unavailable ones are `null`). `isAccessRequested` / `isAccessGranted` tell the state;
`openSettings()` opens the bot's location settings and **only works from a user action** (a tap in the app or
on the MainButton).

Rules **[Heuristic]**:
- **Explain before the prompt.** The button says what location is for ("Nearest pickup point"); the native
  prompt appears only after that tap. Never on launch.
- **Once per need.** Request when the user asks for something location-based; reuse the answer for the
  session; do not poll. Store "asked and refused" in DeviceStorage and stop asking.
- **Refused is a normal path.** Offer a city list or a search field; after a refusal, a "Turn on location"
  row may call `openSettings()` from the tap.
- **Show the uncertainty.** "400 m away (±25 m)"; with a large `horizontal_accuracy` say "about".
- **Treat it as user input.** Coordinates can be spoofed; a server rule that depends on them (delivery zone)
  checks again with the address.
- **Store coarse.** Round or drop coordinates you do not need later.

Kit: `await tma.location()` initialises once and resolves `LocationData` or `null`.

## 4. Biometrics: `BiometricManager` (7.2)

Flow **[API]**: `init()` → `isBiometricAvailable`, `biometricType` (`finger`, `face`, `unknown`) →
`requestAccess({reason})` → `authenticate({reason}, (ok, token))`. `updateBiometricToken(token)` stores a token
in the device's secure storage (an empty string removes it); `isBiometricTokenSaved` and `deviceId` describe
it. `openSettings()` works only from a user action.

Rules **[Heuristic]**:
- **Use it to unlock something already set up on this device**: a saved session, a local secret, a
  "confirm with Face ID" step before a sensitive action the user started.
- **The token is yours.** Issue a random secret from your server, store it with `updateBiometricToken`, and
  let `authenticate` hand it back; the server checks that secret together with the verified `initData`.
  Biometrics alone never authorise money or account changes.
- **Name the reason.** `reason` is shown in the prompt: "Confirm the transfer of 250 points".
- **Fallback.** No biometrics, refused or failed: the same action with a code, a confirmation popup or the
  bot. Never lock someone out.
- **Say it the device's way.** "Face ID" or "fingerprint" from `biometricType`; "biometrics" when unknown.

## 5. Screen and system features

| Feature | Since | Use when | Rules |
|---|---|---|---|
| `requestFullscreen()` / `exitFullscreen()` | 8.0 | games, video, maps, immersive viewers | pad with `--tg-safe-area-inset-*` + `--tg-content-safe-area-inset-*`; Telegram's controls stay on top ([design-system.md](design-system.md) §5) |
| `lockOrientation()` / `unlockOrientation()` | 8.0 | a game or player built for one orientation | lock after the user starts the game, unlock when they leave it |
| `disableVerticalSwipes()` / `enableVerticalSwipes()` | 7.7 | the app has its own vertical drag (a canvas, a sortable list) | only on that screen; re-enable after |
| `enableClosingConfirmation()` | 6.2 | unsaved input, a running order | only while it is true; disable after saving ([launch-and-lifecycle.md](launch-and-lifecycle.md)) |
| `addToHomeScreen()` / `checkHomeScreenStatus()` | 8.0 | a habit app opened often | offer once after a success moment, never on first launch; hide the offer when already added (`homeScreenAdded`) |
| `showScanQrPopup({text})` / `closeScanQrPopup()` | 6.4 | scanning a ticket, a table code, a wallet address | the text says what to point at; handle `qrTextReceived`, close on success; a typed fallback |
| `readTextFromClipboard()` | 6.4 | paste a code (attachment-menu apps only) | only from a tap; most apps use a paste-friendly input instead |
| `shareToStory(media_url, params)` | 7.8 | a result worth showing (a score, a booking) | a real image on HTTPS; one share button on the result screen |
| `shareMessage(id)` / prepared messages | 8.0 | sending a result to a chat | prepared on the server ([../mini-apps-bridge.md](../mini-apps-bridge.md)) |
| `downloadFile({url, file_name})` | 8.0 | receipts, tickets, exports | Telegram shows the native prompt; the file is on HTTPS |
| `setEmojiStatus(id, params)` / `requestEmojiStatusAccess()` | 8.0 | a reward or a membership badge | after the user chooses it; Telegram confirms |
| `requestContact()` | 6.9 | a phone number is needed (delivery) | say why first; never for login (initData already identifies the user) |
| `requestWriteAccess()` | 6.9 | the bot must message the user (receipts, reminders) | before the first such message; the kit's `tma.writeAccess()` skips it when already allowed |
| `DeviceStorage` / `SecureStorage` | 9.0 | per-device data; secrets | [security.md](security.md) |

Check any member's version and parameters offline: `py -3 scripts/webapp_lookup.py show WebApp.requestFullscreen`.

## 6. The permission pattern (location, biometrics, contact, write access, emoji status)

1. **Context first:** the feature is visible and its button explains the benefit.
2. **Native prompt from the tap:** Telegram's prompt appears in response to that tap, never on launch.
3. **Handle every answer:** granted → do it; refused → the fallback path and a quiet note; not available →
   hide the feature or explain once.
4. **Remember:** store that it was asked (DeviceStorage) so the app does not ask again on every open.
5. **Way back:** a settings row ("Location: off · Turn on") that calls `openSettings()` from a tap.

## 7. Testing

- **Mock stand.** Haptic calls appear in the call log; motion sensors produce smooth synthetic readings at the
  requested rate; location returns demo coordinates with ±25 m; old client versions show what throws or is
  ignored. The gallery's **Device** group exercises all of it. It proves wiring, not feel.
- **Unit tests.** Fake `WebApp` objects with `Accelerometer`, `LocationManager` and a recording
  `HapticFeedback`; `_kit/tma.test.ts` shows the pattern (burst guard, stop on hide, null on old clients).
- **Devices.** Feel every haptic on an iPhone and on a mid-range Android; check that each one matches a
  visible change and that a fast drag does not buzz; check sensors stop when the app is hidden (battery);
  deny every permission once and walk the fallback.
- **Lint.** `miniapp_lint.py` flags haptics in event streams (MA36), sensors never stopped (MA37) and members
  newer than 6.0 used without a version gate (MA15).

## 8. Digging deeper

When a request goes beyond this page (a new API, an odd device, a game):

1. **The member catalog first:** `py -3 scripts/webapp_lookup.py search haptic`, `… since 8.0`,
   `… show WebApp.DeviceOrientation`; it gives versions, signatures, events and the anchor on Telegram's page.
2. **Telegram's page:** https://core.telegram.org/bots/webapps (sections on haptics, sensors, location,
   biometrics, fullscreen) and the Bot API changelog for anything newer than the catalog; refresh the catalog
   with `webapp_lookup.py sync` and note the date.
3. **Platform meaning:** for how a haptic style should feel, Apple's Human Interface Guidelines "Playing
   haptics" and Android's haptics design guidance; map their vocabulary onto §1.2, never their APIs.
4. **When Telegram adds a device member:** update the catalog, add a kit wrapper with a version gate and a
   stop path, add it to the stand's mock, add a lint check if misuse is likely, add a row to §5, then test.

## 9. Checklist

- [ ] Each device feature has a stated user gain and a working path without it.
- [ ] Haptics: one per user moment, the right type from §1.2, after the visible change, outcomes from the
      server, none in streams or decoration; a switch in games.
- [ ] Sensors start on purpose, stop on leave and hide, at the slowest useful rate; reduced motion respected.
- [ ] Location and biometrics: explained before the prompt, asked once, refusals handled, `openSettings` only
      from a tap; biometrics never the only authorisation.
- [ ] Every member gated by version; checked in the stand, then on an iPhone and an Android phone.
