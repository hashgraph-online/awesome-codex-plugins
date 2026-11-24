# Telegram.WebApp: the client API by task

A human-readable cut of `window.Telegram.WebApp`, grouped by what a screen needs, with the Bot API
version each member appeared in and what to do on an older client. The full member list (286 fields,
methods, events and parameter objects) is the offline catalog `data/mini-apps/webapp-catalog.json`,
parsed from https://core.telegram.org/bots/webapps on **2026-11-23** (Bot API 10.5 is the latest
release; the newest Mini App change is 10.1; the highest version gate inside `telegram-web-app.js` is
`9.6`).

```bash
py -3 scripts/webapp_lookup.py show WebApp.requestFullscreen   # one member: signature, version, gate
py -3 scripts/webapp_lookup.py show BottomButton               # an object with all its members
py -3 scripts/webapp_lookup.py since 8.0                       # what a release added
py -3 scripts/webapp_lookup.py gates                           # everything that needs isVersionAtLeast
py -3 scripts/tg_api_lookup.py show WebApp.shareMessage        # the Bot API lookup falls back to it
```

Labels: **[Official]** the Mini Apps page; **[API]** the Bot API page; **[Heuristic]** this skill's advice.

## 1. Load the script and read the version

```html
<head>
  <script src="https://telegram.org/js/telegram-web-app.js?65"></script>  <!-- before your own scripts -->
</head>
```

- The script goes in `<head>`, before other scripts. `?65` is a cache-buster, not a version. **[Official]**
- `WebApp.version` is the Bot API version the **user's client** supports (for example `"8.0"`), not a
  library version; the script reports `"6.0"` when the client sends none. **[Official]**
- Outside Telegram (a plain browser, a preview) the object exists but `initData` is empty. Detect it with
  `Telegram.WebApp.initData === ""` and show a "open in Telegram" state instead of a broken screen.
  **[Heuristic]**

## 2. Gate by version, degrade on purpose

Every member newer than 6.0 needs a gate. On an older client most such **methods** (`showPopup`,
`requestFullscreen`, `shareMessage`, `openInvoice`, `requestContact`, `requestChat`, `downloadFile`…) log an
error and **throw** `Error('WebAppMethodUnsupported')`, so an ungated call breaks the tap handler it runs in.
Objects and setters (`BackButton`, `HapticFeedback`, `setBackgroundColor`, `setBottomBarColor`, vertical
swipes, closing confirmation) only log a warning and do nothing: a silent dead control. (Read in
`telegram-web-app.js` on 2026-11-23.) **[Official]**/**[Heuristic]**

```js
const tg = window.Telegram.WebApp;
const has = (v) => tg.isVersionAtLeast(v);

if (has('8.0')) tg.requestFullscreen();           // otherwise stay in the normal mode
if (has('7.10')) tg.SecondaryButton.setParams({ text: 'Details', position: 'left', is_visible: true });
else showInlineSecondaryLink();                   // a plain link in the content instead
const store = has('9.0') ? tg.DeviceStorage : (has('6.9') ? tg.CloudStorage : null);
```

| Missing on an old client | Fallback **[Heuristic]** |
|---|---|
| `SecondaryButton` (7.10) | a tonal button or link inside the content, above the MainButton |
| `BottomButton.iconCustomEmojiId` (9.5) | text only; the label must stand alone anyway |
| `section_bg_color` and other 7.0+ theme keys | the `fallback_key` chain in `data/mini-apps/theme-params.json` |
| `safeAreaInset` / `contentSafeAreaInset` (8.0) | no fullscreen; `env(safe-area-inset-*)` as the CSS fallback |
| `DeviceStorage` / `SecureStorage` (9.0) | `CloudStorage` (6.9) for non-secret data; never `localStorage` for secrets |
| `showPopup` (6.2) | an in-content confirmation step, never `window.confirm()` |
| `requestChat` (9.6) | a bot message with a `request_chat` reply keyboard |

`py -3 scripts/webapp_lookup.py gates` prints the full list; `scripts/miniapp_lint.py` flags an ungated
call of any member newer than 6.0.

## 3. Members by task

### Lifecycle and launch data

| Member | Since | Use |
|---|---|---|
| `WebApp.ready()` | 6.0 | call as soon as the first useful screen is drawn; hides Telegram's loading screen |
| `WebApp.expand()` | 6.0 | full height; only for screens that cannot work at half height |
| `WebApp.close()` | 6.0 | closes the app |
| `WebApp.isExpanded` | 6.0 | whether the app already has full height |
| `WebApp.isActive` | 8.0 | false while minimised; pause timers and polling |
| `WebApp.initData` | 6.0 | raw signed string; send to your server, verify there ([security.md](security.md)) |
| `WebApp.initDataUnsafe` | 6.0 | parsed copy for display only; never for decisions |
| `WebApp.version` | 6.1 | Bot API version the client supports, not a script version |
| `WebApp.platform` | 6.4 | `ios`, `android`, `tdesktop`, `macos`, `weba`, `webk`…; a layout hint, not a security signal |
| `WebApp.isVersionAtLeast(version)` | 6.1 | the gate for everything newer than 6.0 |
| `WebApp.onEvent(eventType, eventHandler)` | 6.0 | subscribe; pair every `onEvent` with `offEvent` on teardown |
| `WebApp.offEvent(eventType, eventHandler)` | 6.0 | unsubscribe |

### Theme, colours, viewport

| Member | Since | Use |
|---|---|---|
| `WebApp.colorScheme` | 6.0 | `light` or `dark`; also `--tg-color-scheme` |
| `WebApp.themeParams` | 6.0 | 15 colours, also `--tg-theme-*` CSS variables (`data/mini-apps/theme-params.json`) |
| `WebApp.headerColor` | 6.1 | current header colour |
| `WebApp.setHeaderColor(color)` | 6.1 | `#RRGGBB` or `bg_color` / `secondary_bg_color`; any colour since 6.9 |
| `WebApp.backgroundColor` | 6.1 | current background colour |
| `WebApp.setBackgroundColor(color)` | 6.1 | colour behind the page (overscroll, transitions) |
| `WebApp.bottomBarColor` | 7.10 | current bottom bar colour |
| `WebApp.setBottomBarColor(color)` | 7.10 | also the `bottom_bar_bg_color` keyword; tints the Android navigation bar |
| `WebApp.viewportHeight` | 6.0 | live; too slow to pin bottom UI to |
| `WebApp.viewportStableHeight` | 6.0 | after the last drag; use for layout |

Prefer the colour keywords: they follow theme changes by themselves. A literal colour must be re-applied in
`themeChanged`. **[Official]**/**[Heuristic]**

### Fullscreen, safe areas, orientation, gestures

| Member | Since | Use |
|---|---|---|
| `WebApp.requestFullscreen()` | 8.0 | handle `fullscreenFailed` (`UNSUPPORTED`, `ALREADY_FULLSCREEN`) |
| `WebApp.exitFullscreen()` | 8.0 | back to the normal mode |
| `WebApp.isFullscreen` | 8.0 | current mode |
| `WebApp.safeAreaInset` | 8.0 | device insets; `--tg-safe-area-inset-*` |
| `WebApp.contentSafeAreaInset` | 8.0 | Telegram's overlaid controls; `--tg-content-safe-area-inset-*` |
| `WebApp.lockOrientation()` | 8.0 | games and media only |
| `WebApp.unlockOrientation()` | 8.0 | release the lock when the game screen closes |
| `WebApp.isOrientationLocked` | 8.0 | current lock |
| `WebApp.enableVerticalSwipes()` | 7.7 | the default; swipe down minimises or closes |
| `WebApp.disableVerticalSwipes()` | 7.7 | only when your own gestures conflict (games, drawing, maps) |
| `WebApp.isVerticalSwipesEnabled` | 7.7 | current state |
| `WebApp.enableClosingConfirmation()` | 6.2 | only while there is unsaved input |
| `WebApp.disableClosingConfirmation()` | 6.2 | as soon as the input is saved |
| `WebApp.isClosingConfirmationEnabled` | 6.2 | current state |
| `WebApp.hideKeyboard()` | 9.1 | dismiss the on-screen keyboard after submit |

### Native controls

| Member | Since | Use |
|---|---|---|
| `WebApp.MainButton` | 6.0 | the screen's primary action |
| `WebApp.SecondaryButton` | 7.10 | a second action next to it |
| `BottomButton.setParams(params)` | 6.0 | `text`, `color`, `text_color`, `has_shine_effect`, `position`, `is_active`, `is_visible`; `icon_custom_emoji_id` since 9.5 |
| `BottomButton.showProgress(leaveActive)` | 6.0 | for any action over ~300 ms |
| `BottomButton.hasShineEffect` | 7.10 | a shine animation; at most on one paid or final action |
| `BottomButton.position` | 7.10 | `left`, `right`, `top`, `bottom`; secondary only, when both are visible |
| `BottomButton.iconCustomEmojiId` | 9.5 | custom emoji before the text; there is **no** `style` field |
| `WebApp.BackButton` | 6.1 | every screen below a tab root |
| `WebApp.SettingsButton` | 7.0 | the Settings item in the ⋯ menu |
| `WebApp.showPopup(params[, callback])` | 6.2 | title ≤ 64, message 1-256, 1-3 buttons |
| `WebApp.showAlert(message[, callback])` | 6.2 | one-button notice |
| `WebApp.showConfirm(message[, callback])` | 6.2 | OK / Cancel |
| `WebApp.showScanQrPopup(params[, callback])` | 6.4 | return `true` in the callback to close |
| `WebApp.closeScanQrPopup()` | 6.4 | close the scanner from code |
| `WebApp.HapticFeedback` | 6.1 | `impactOccurred`, `notificationOccurred`, `selectionChanged` |

`MainButton` and `SecondaryButton` are both `BottomButton` objects (the class was named `MainButton`
before 7.10). Chat-message buttons got `style` and `icon_custom_emoji_id` in Bot API 9.4; the Mini App
bottom buttons have only `color`, `textColor` and, since 9.5, `iconCustomEmojiId`. **[Official]**/**[API]**

### Storage

| Member | Since | Use |
|---|---|---|
| `WebApp.CloudStorage` | 6.9 | per user, synced across devices: 1024 keys (1-128 chars `[A-Za-z0-9_-]`), value ≤ 4096 chars |
| `WebApp.DeviceStorage` | 9.0 | per device, 5 MB per user per bot, like `localStorage` |
| `WebApp.SecureStorage` | 9.0 | iOS Keychain / Android Keystore, 10 items: secrets and session tokens; `restoreItem` asks the user |

All three are asynchronous (callbacks). Which one for what: [security.md](security.md) §6.

### Device

| Member | Since | Use |
|---|---|---|
| `WebApp.BiometricManager` | 7.2 | `init`, `requestAccess({reason})`, `authenticate({reason})` → token |
| `WebApp.LocationManager` | 8.0 | `init`, `getLocation`; `openSettings` needs a user gesture |
| `WebApp.Accelerometer` | 8.0 | `start({refresh_rate})`, `stop` |
| `WebApp.Gyroscope` | 8.0 | same shape |
| `WebApp.DeviceOrientation` | 8.0 | same shape, plus `need_absolute` |

Ask for device access only from a tap on a control that explains why, and handle the denied state with a
way forward (`openSettings`). **[Heuristic]**

### Leaving the app and talking to Telegram

| Member | Since | Use |
|---|---|---|
| `WebApp.openLink(url[, options])` | 6.1 | external browser; the app stays open; user gesture only (`try_instant_view` option since 6.4) |
| `WebApp.openTelegramLink(url)` | 6.1 | `t.me` links; since 7.0 the app stays open |
| `WebApp.openInvoice(url[, callback])` | 6.1 | Stars and card invoices: [payments.md](payments.md) (app side), [payments-and-stars.md](../payments-and-stars.md) (bot side) |
| `WebApp.sendData(data)` | 6.0 | reply-keyboard launches only; ≤ 4096 bytes; closes the app |
| `WebApp.switchInlineQuery(query[, choose_chat_types])` | 6.7 | back to inline mode with a query (bot needs inline mode) |
| `WebApp.shareMessage(msg_id[, callback])` | 8.0 | needs a `PreparedInlineMessage` id from the bot |
| `WebApp.shareToStory(media_url[, params])` | 7.8 | links in stories need Premium |
| `WebApp.downloadFile(params[, callback])` | 8.0 | server sends `Content-Disposition: attachment` and CORS for `web.telegram.org` |
| `WebApp.requestWriteAccess([callback])` | 6.9 | before the bot may message the user first |
| `WebApp.requestContact([callback])` | 6.9 | only with a reason the user sees |
| `WebApp.requestChat(req_id[, callback])` | 9.6 | needs a `PreparedKeyboardButton` id from the bot |
| `WebApp.setEmojiStatus(custom_emoji_id[, params, callback])` | 8.0 | native confirmation dialog |
| `WebApp.requestEmojiStatusAccess([callback])` | 8.0 | then the bot calls `setUserEmojiStatus` |
| `WebApp.addToHomeScreen()` | 8.0 | home-screen shortcut |
| `WebApp.checkHomeScreenStatus([callback])` | 8.0 | `unsupported`, `unknown`, `added`, `missed` |
| `WebApp.readTextFromClipboard([callback])` | 6.4 | attachment-menu apps only |

The bot side of `shareMessage`, `requestChat`, `requestWriteAccess` and `sendData`:
[../mini-apps-bridge.md](../mini-apps-bridge.md).

### Hosting on Telegram

| Member | Since | Use |
|---|---|---|
| `WebApp.Serverless` | new (2026-10) | `Serverless.call(name, input, callback)`; `initData` is validated by the platform |

`Serverless` carries a "NEW" badge and no Bot API version mark on the page; check
`typeof Telegram.WebApp.Serverless?.call === 'function'` instead of a version gate. Errors carry `type`
(`ENDPOINT_ERROR`, `UNAUTHORIZED`), `status` and optional `parameters`. **[Official]**

How and when to use haptics, sensors, location, biometrics and the screen features above: [haptics-and-device.md](haptics-and-device.md).

## 4. Events worth handling

| Event | Since | Do |
|---|---|---|
| `themeChanged` | 6.0 | re-read colours used in JS (canvas, computed header colour); CSS variables update by themselves |
| `viewportChanged` | 6.0 | act on `isStateStable === true` only |
| `mainButtonClicked`, `secondaryButtonClicked` | 6.0, 7.10 | or `MainButton.onClick`; one handler per screen, removed on leave |
| `backButtonClicked` | 6.1 | pop the top layer: sheet first, then screen |
| `settingsButtonClicked` | 6.1 | open the settings screen |
| `invoiceClosed` | 6.1 | update the UI; the order is paid only when the bot gets `successful_payment` |
| `popupClosed` | 6.2 | `button_id` or empty when dismissed |
| `activated`, `deactivated` | 8.0 | resume or pause timers, polling, video |
| `safeAreaChanged`, `contentSafeAreaChanged` | 8.0 | CSS variables update; re-measure only JS layouts |
| `fullscreenChanged`, `fullscreenFailed` | 8.0 | adjust layout; explain an `UNSUPPORTED` failure, never loop |
| `shareMessageSent`, `shareMessageFailed` | 8.0 | confirm or explain (`MESSAGE_EXPIRED`: ask the bot for a new id) |
| `writeAccessRequested`, `contactRequested` | 6.9 | `allowed` / `sent` or `cancelled`; no nagging after a cancel |
| `fileDownloadRequested` | 8.0 | `downloading` or `cancelled` |

All 44 events: `py -3 scripts/webapp_lookup.py show events`.

## 5. Launch parameters

Telegram passes launch parameters in `location.hash` (`tgWebAppData`, `tgWebAppVersion`, `tgWebAppPlatform`,
`tgWebAppThemeParams`, `tgWebAppFullscreen`…) and `start_param` also as the `tgWebAppStartParam` query
parameter. **[Official]** A hash router can erase the hash before your code reads it, so copy it on the first
line of your entry script. **[Heuristic]** Details and per-launch contents:
[launch-and-lifecycle.md](launch-and-lifecycle.md).

## 6. Not in this skill

`telegram-web-app.js` also contains an undocumented camera and microphone bridge for iframe hosts
(`web_app_request_media_access`). It is not on the official page; do not build on it. Use the standard
`getUserMedia` with a fallback, or a file input with `capture`. **[Heuristic]**
