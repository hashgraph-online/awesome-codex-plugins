# Mini App performance and testing

Budgets that keep a Mini App fast on a weak Android phone, and the ladder of evidence from a static check
to a real device. Checked on **2026-11-23**. Labels: **[Official]**, **[Heuristic]**.

## 1. Budgets [Heuristic]

| Item | Budget |
|---|---|
| First useful screen (skeletons in the real layout) and `ready()` | ≤ 1 s on a mid-range Android over 4G |
| JavaScript for a simple app (shop, form, settings) | ≤ ~150 KB gzip in the first load |
| CSS | ≤ ~30 KB gzip; no render-blocking web fonts (system font) |
| Images in lists | sized to the slot (2× for retina), `loading="lazy"` below the fold, modern formats |
| Main-thread tasks during scroll and transitions | none over 50 ms; frames under 16 ms (G4) |
| Animated stickers / Lottie | one per screen, paused when off-screen or `deactivated` |

Telegram shows its loading screen until `ready()` (or the full page load without it). **[Official]** Call it
after the first screen is drawn, not after data arrives.

## 2. Weak devices (G7)

- Read the Android performance class from the User-Agent (`tma.ts` sets `<html data-tma-perf>`). **[Official]**
- On `low`: no `backdrop-filter`, no parallax, no auto-advancing carousels, static images instead of Lottie
  or TGS loops, charts with fewer points and no animated drawing, smaller images. The kit already drops
  blur and screen animations. **[Heuristic]**
- A missing class is unknown, not weak. **[Heuristic]**
- Pause timers, polling and video on `deactivated`; resume on `activated` (8.0). **[Official]**/**[Heuristic]**

## 3. The ladder of evidence

| Level | What it proves | How |
|---|---|---|
| 1. Lint | source patterns: tokens, native controls, gates, labels, safe areas | `py -3 scripts/miniapp_lint.py <app> --strict` |
| 2. Unit tests | kit and app logic: navigation stack, buttons, gates, storage, `start_param` parsing | `node --test` (`examples/mini-apps/_kit/tma.test.ts`) |
| 3. Server tests | `initData` HMAC and Ed25519, expiry, tampering | `examples/mini-apps/server` tests (Python unittest, `node --test`) |
| 4. Preview stand | layout in iOS/Android × light/dark × 320/390/430, fullscreen, compact, old versions | `py -3 scripts/preview_miniapp.py <app> --serve 8790` |
| 5. Test environment | real client, real `initData`, real chrome | Telegram test server, test bot, plain HTTP allowed |
| 6. Production devices | what users get | iPhone, mid-range Android (and a `LOW` one), Telegram Desktop, Telegram Web |

Name the level reached in every report. Levels 1-4 never prove how a real Telegram client renders.

## 4. The preview stand

`scripts/preview_miniapp.py` (with `--api mock.json` for the app's own server routes) serves the app folder on 127.0.0.1, swaps `telegram-web-app.js` for a mock of
`Telegram.WebApp` and draws Telegram's chrome around it:

- controls: platform (iOS, Android, Desktop), scheme, width (320, 375, 390, 430, desktop 384), mode
  (compact, full, fullscreen), client version (6.0 … 10.1), Android performance class, `start_param`;
- the matrix view (`/?view=matrix`): iOS and Android × light and dark × 320/390/430, plus fullscreen iOS
  dark, fullscreen Android light and compact iOS light;
- a call log: haptics, popups, chrome colours, BackButton, storage, links, payments (never paid), and every
  member the selected version does not support (methods throw `WebAppMethodUnsupported` like the real
  script; objects and setters warn).

What it does **not** prove: real palettes (approximations of Telegram's defaults), real header and bottom
bar sizes, Liquid Glass, keyboard and viewport behaviour on phones, `initData` signatures, payments, Android
back, iOS edge swipe, performance. The stand says "MOCK" on every page.

## 5. Manual checks on a device

| Check | iOS | Android | Desktop / Web |
|---|---|---|---|
| Day, night and one custom theme while open | ✓ | ✓ | ✓ |
| Compact (half height), full, fullscreen portrait and landscape | ✓ | ✓ | full |
| BackButton on every level-2 screen; edge swipe (iOS) / system back (Android) | ✓ | ✓ | header |
| MainButton text, progress, disabled reason | ✓ | ✓ | ✓ |
| Keyboard over a form: the focused field stays visible; `hideKeyboard()` after submit | ✓ | ✓ | — |
| Notch and home indicator in fullscreen; 3-button and gesture navigation | ✓ | ✓ | — |
| Minimise and return (`deactivated` / `activated`) | ✓ | ✓ | ✓ |
| Large text size (Dynamic Type / font scale) | ✓ | ✓ | — |
| Offline and slow network: skeletons, error with retry | ✓ | ✓ | ✓ |
| Performance class `LOW` device | — | ✓ | — |

Debugging: iOS Safari Web Inspector (Telegram settings → tap 10 times → Allow Web View Inspection); Android
`chrome://inspect` after enabling WebView debugging in Telegram; Telegram Desktop and macOS betas have debug
switches. **[Official]**

## 6. Screenshots for a pull request

From the stand: the matrix view, one fullscreen screen per platform, one level-2 screen with BackButton and
MainButton, and the empty and error states. Mark them "mock preview". Real-device screenshots, when taken,
go in their own section.
