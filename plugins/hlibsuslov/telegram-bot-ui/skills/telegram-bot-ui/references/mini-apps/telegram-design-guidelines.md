---
summary: "Telegram's official Mini App design rules G1-G7 and other design-relevant instructions turned into implementation steps and checks; read before judging a Mini App against Telegram's rules."
verified: "2026-11-23"
bot_api: "10.5"
---

# Telegram Mini App design guidelines, rule by rule

## Contents

- [0. The seven official rules at a glance](#0-the-seven-official-rules-at-a-glance)
- [1. Theme (G1)](#1-theme-g1)
- [2. Responsive, mobile-first (G2)](#2-responsive-mobile-first-g2)
- [3. Native consistency (G3)](#3-native-consistency-g3)
- [4. Motion, 60 fps (G4)](#4-motion-60-fps-g4)
- [5. Labels and accessibility (G5)](#5-labels-and-accessibility-g5)
- [6. Safe area and content safe area (G6)](#6-safe-area-and-content-safe-area-g6)
- [7. Android performance class (G7)](#7-android-performance-class-g7)
- [8. Loading and first paint [Official]](#8-loading-and-first-paint-official)
- [9. Viewport [Official]](#9-viewport-official)
- [10. Chrome colours [Official]](#10-chrome-colours-official)
- [11. Native controls and feedback [Official]](#11-native-controls-and-feedback-official)
- [12. Store presentation and testing [Official]](#12-store-presentation-and-testing-official)
- [13. CSS variables Telegram sets [Official]](#13-css-variables-telegram-sets-official)
- [14. Review checklist (every screen)](#14-review-checklist-every-screen)

Telegram's official design rules for Mini Apps and every design-relevant instruction elsewhere on the
same page, turned into implementation steps and checks. Source:
https://core.telegram.org/bots/webapps#design-guidelines, read on **2026-11-23** (Bot API 10.5; the
newest Mini App change is 10.1). The official text is paraphrased. Labels: **[Official]** stated by Telegram;
**[Heuristic]** this skill's way to satisfy it. How the rules combine with the visual sources:
`design-sources.md`.

## 0. The seven official rules at a glance

| # | Rule [Official] | Section |
|---|---|---|
| G1 | Follow the user's live colour theme, including day/night switches and custom themes, and use the theme colours consistently | §1 |
| G2 | Every element is responsive; design mobile-first | §2 |
| G3 | Interactive elements match the style, behaviour and intent of Telegram's own UI components | §3 |
| G4 | Animations are smooth, ideally 60 fps | §4 |
| G5 | Every input and image has a label | §5 |
| G6 | Respect the safe area and the content safe area, especially in fullscreen | §6 |
| G7 | On Android, read the performance class and cut animations and effects on weak devices | §7 |

Sections 8-12 cover the rest of the page: loading, viewport, chrome colours, native controls, feedback,
store presentation, testing.

## 1. Theme (G1)

What Telegram gives **[Official]**:

- `WebApp.colorScheme`: `"light"` or `"dark"`, also `--tg-color-scheme`.
- `WebApp.themeParams`, all optional `#RRGGBB`, each also set as a CSS variable `--tg-theme-<key with dashes>`:

| Key | Purpose | Since |
|---|---|---|
| `bg_color` | main background | 6.0 |
| `text_color` | main text | 6.0 |
| `hint_color` | hint text | 6.0 |
| `link_color` | links | 6.0 |
| `button_color` / `button_text_color` | button fill / text on it | 6.0 |
| `secondary_bg_color` | secondary background | 6.1 |
| `header_bg_color` | header background | 7.0 |
| `accent_text_color` | accent text | 7.0 |
| `section_bg_color` | section background, meant to sit on `secondary_bg_color` | 7.0 |
| `section_header_text_color` | section header text | 7.0 |
| `subtitle_text_color` | subtitles | 7.0 |
| `destructive_text_color` | destructive actions | 7.0 |
| `section_separator_color` | separators between items in a section | 7.6 |
| `bottom_bar_bg_color` | bottom bar background | 7.10 |

- `themeChanged` fires on every theme change (night mode included) with no arguments; read the new values
  from `WebApp.themeParams` and `WebApp.colorScheme` inside the handler.

How to satisfy it **[Heuristic]**:

1. Style only with the `--tg-theme-*` variables (or `color-mix()` derived from them). Literal colours appear
   only as `var()` fallbacks for an older client or a plain browser.
2. Fallback chain for keys an older client does not send: `section_bg → bg`, `subtitle_text → hint`,
   `accent_text → link`, `section_header_text → hint`, `section_separator → text at 12 %`,
   `bottom_bar_bg → secondary_bg`, `header_bg → bg`.
3. Grouped screens: page = `secondary_bg_color`, groups = `section_bg_color`. Flat screens: `bg_color`.
4. Never assume the user's theme is the default blue one: custom themes change the accent, backgrounds and
   text. Brand colour is allowed only where it does not carry text contrast (an illustration, a chart series).
5. CSS variables update live, so CSS needs no listener. Re-read in `themeChanged` only for values used in
   JS (canvas charts, `setHeaderColor` with a computed colour).
6. Check: switch day/night and one custom theme while the app is open; nothing keeps the old colour.

Violations: white flash on launch in dark mode, hard-coded `#fff` cards, a brand-blue button in a user's green
theme, text over brand colour that fails contrast in one scheme.

## 2. Responsive, mobile-first (G2)

- Design for 320-430 px width first; then tablet and desktop clients (Telegram Desktop opens Mini Apps in
  a resizable window, typically about 380-420 px wide; web clients may be wider). **[Heuristic]**
- Use fluid widths, `min-width: 0` on flex children that truncate, and no fixed widths above 320 px.
- Height: never `100vh`. Use `var(--tg-viewport-stable-height)` for full-height layouts (§9).
- Compact mode (half height, `mode=compact` links or the @BotFather setting) must still show the screen's
  main content and action without scrolling to find them.
- Landscape and fullscreen: content stays inside the safe areas (§6); a locked orientation is only for
  games and media (`lockOrientation`).
- Check at 320, 375, 390 and 430 px, compact and full height, and in a desktop window.

## 3. Native consistency (G3)

Telegram's own components set the expectations. **[Official]** In practice **[Heuristic]**:

| Need | Use | Not |
|---|---|---|
| Primary action of a screen | `MainButton` | own fixed button at the bottom |
| Secondary action next to it | `SecondaryButton` (`position` left/right/top/bottom) | a second custom bar |
| Going back | `BackButton` + `backButtonClicked` | own arrow in the content |
| App settings | `SettingsButton` (item in the ⋯ menu) | a gear in the header area |
| Confirm, alert, choice of up to 3 | `showConfirm`, `showAlert`, `showPopup` | `alert()`, `confirm()`, custom modal for a simple question |
| QR scan | `showScanQrPopup` | own camera UI |
| Lists, settings | grouped sections with cells like Telegram's settings | card stacks, web tables |
| Tactile feedback | `HapticFeedback` (§11) | vibration API |

Behaviour must match too: back closes the topmost layer first (sheet, then screen); destructive actions ask
for confirmation; the app never traps the user (back on the first screen closes the app via Telegram).

## 4. Motion, 60 fps (G4)

- Animate only `transform` and `opacity`; no layout properties, no large animated blurs. **[Heuristic]**
- 150-300 ms, one ease-out curve; screen pushes slide, sheets rise, dismissal reverses the entrance.
- Respect `prefers-reduced-motion` (crossfade or instant) and the Android class (§7).
- No idle loops on things that are not live; skeletons shimmer only while loading.
- Check: record a trace on a mid-range Android; long frames over 16 ms during scroll or transitions are bugs.

## 5. Labels and accessibility (G5)

- Every input has a visible label or an `aria-label`; placeholders are not labels. **[Official]**/**[Heuristic]**
- Every meaningful image has `alt`; decorative images use `alt=""`.
- Icon-only buttons get `aria-label`; state changes (toggles, selected tab) use `aria-pressed` /
  `aria-selected`.
- Contrast ≥ 4.5:1 for text in both schemes and on any glass surface; colour is never the only signal
  (gains and losses carry a sign or an arrow).
- Touch targets ≥ 44 px; focus visible for keyboard use on desktop clients.
- Follow the user's text size: sizes in `rem`/`em`, layouts that grow.

## 6. Safe area and content safe area (G6)

What Telegram gives **[Official]**:

- `safeAreaInset {top, bottom, left, right}` — the device's insets (notch, status bar, home indicator,
  navigation bar). CSS: `--tg-safe-area-inset-*`. Event `safeAreaChanged`.
- `contentSafeAreaInset` — the area free from Telegram's own UI drawn over the app (the header controls in
  fullscreen). CSS: `--tg-content-safe-area-inset-*`. Event `contentSafeAreaChanged`.
- In fullscreen the header is transparent; still call `setHeaderColor` so the status bar and Telegram's
  controls stay readable.

How **[Heuristic]**:

```css
.screen {
  padding-top: calc(var(--tg-safe-area-inset-top, 0px) + var(--tg-content-safe-area-inset-top, 0px));
  padding-bottom: calc(var(--tg-safe-area-inset-bottom, 0px) + var(--tg-content-safe-area-inset-bottom, 0px));
  padding-left: max(16px, var(--tg-safe-area-inset-left, 0px));
  padding-right: max(16px, var(--tg-safe-area-inset-right, 0px));
}
```

- Both insets add up at the top in fullscreen; in the normal mode they are usually 0 because Telegram's header
  is outside the WebView.
- Floating own controls (tab bar, floating button) sit above the bottom inset; scroll content gets bottom
  padding equal to the floating control's height plus the inset.
- Check in fullscreen portrait and landscape on a notched iPhone and on Android with gesture and 3-button
  navigation.

## 7. Android performance class (G7)

On Android the User-Agent ends with
`Telegram-Android/{app_version} ({manufacturer} {model}; Android {version}; SDK {sdk}; {performance_class})`,
where the class is `LOW`, `AVERAGE` or `HIGH`. **[Official]**

```js
const perf = (navigator.userAgent.match(/Telegram-Android\/\S+ \([^)]*;\s*(LOW|AVERAGE|HIGH)\)/) || [])[1] || 'HIGH';
document.documentElement.dataset.perf = perf.toLowerCase();
```

On `LOW` **[Heuristic]**: no `backdrop-filter` (solid surfaces instead of glass), no parallax or auto-playing
carousels, shorter or no transitions, static images instead of Lottie/TGS loops, lighter charts (fewer points,
no animated drawing), smaller images. Treat a missing value as unknown, not as weak.

## 8. Loading and first paint [Official]

- Call `WebApp.ready()` as soon as the essential interface is drawn; it removes Telegram's loading
  placeholder. Without it the placeholder waits for the full page load.
- The placeholder itself (icon, separate light and dark colours) is configured in @BotFather → Bot Settings →
  Configure Mini App. Do not add an own splash with a logo after it. **[Heuristic]**
- Set chrome colours (§10) before `ready()` so there is no colour jump.
- First screen: real layout with skeletons where data loads; no empty white page, no spinner-only screen.
- Save the launch parameters from `location.hash` at start: hash routers can erase them. **[Heuristic]**

## 9. Viewport [Official]

- `viewportHeight` (`--tg-viewport-height`) changes continuously while the user drags the app; it is too
  slow to pin elements to the bottom.
- Pin bottom elements to `viewportStableHeight` (`--tg-viewport-stable-height`), which changes only when the
  drag ends; `viewportChanged` reports `isStateStable`.
- `expand()` opens the app to full height; `isExpanded` tells whether it already is. Main Mini Apps and
  direct links open at full height by default; `mode=compact` opens half height.
- **[Heuristic]**: call `expand()` only for screens that cannot work in half height (a long form, a game);
  never fight the user's drag.

## 10. Chrome colours [Official]

| Call | Accepts | Note |
|---|---|---|
| `setHeaderColor(c)` | `#RRGGBB` or `bg_color` / `secondary_bg_color` | any colour since 6.9 |
| `setBackgroundColor(c)` | same | colour behind the app (overscroll, transitions) |
| `setBottomBarColor(c)` | `#RRGGBB`, `bg_color`, `secondary_bg_color`, `bottom_bar_bg_color` | 7.10; also tints the Android navigation bar |

**[Heuristic]**: header colour = the colour at the top of the current screen (grouped page →
`secondary_bg_color`, flat → `bg_color`, brand hero → the hero's colour, then back to the page colour when the
hero scrolls away). Background colour = page colour. Bottom bar colour = the surface under it (the page, or a
sheet's surface while a sheet uses the MainButton). Prefer the keywords: they follow theme changes by
themselves; a literal colour must be re-applied in `themeChanged`.

## 11. Native controls and feedback [Official]

**MainButton / SecondaryButton** (`BottomButton`): text, `color`, `textColor`, `isActive`, `isVisible`,
`hasShineEffect`, `iconCustomEmojiId` (9.5), `showProgress(leaveActive)` / `hideProgress()`. Secondary
`position`: `left`, `right`, `top`, `bottom`; it shows only when both are visible. A button opened from the
attachment menu stays hidden until the user interacts with the app. **[Heuristic]**: short verb labels
("Pay ₴450", "Save"); show progress for every action longer than ~300 ms; disable instead of hiding when a form
is incomplete, and say what is missing in the content.

**BackButton / SettingsButton**: show the back button on every screen below a tab root; handle
`backButtonClicked` and `settingsButtonClicked`.

**Popups**: `showPopup({title ≤ 64, message 1-256, buttons 1-3})`, button types `default`, `ok`, `close`,
`cancel`, `destructive` (default and destructive need text); `showAlert`, `showConfirm`.

**Haptics**: `impactOccurred('light'|'medium'|'heavy'|'rigid'|'soft')` for physical contact (a tap on a large
control, a snap); `notificationOccurred('success'|'error'|'warning')` for outcomes;
`selectionChanged()` only when a selection changes, not when it is confirmed. **[Heuristic]**: no haptics on
scroll or on every tap.

**Closing and gestures**: `enableClosingConfirmation()` while there is unsaved input; switch it off when saved.
Keep vertical swipes enabled; `disableVerticalSwipes()` only when the app's own gestures conflict (games,
drawing, maps). The header swipe still closes or minimises the app.

**User-gesture-only calls**: `openLink`, `openInvoice` and similar must run inside a tap handler.

## 12. Store presentation and testing [Official]

- Main Mini App: upload demo videos and screenshots to the bot profile, localised per language. Featuring in
  the Mini App Store favours apps with high-quality media that follow these guidelines (and Stars payments).
- Test environment: separate account and bot; plain HTTP URLs allowed there.
- Debug: iOS — Safari Web Inspector after enabling WebView inspection in Telegram's hidden settings; Android —
  WebView debugging and `chrome://inspect`; Telegram Desktop beta and macOS have their own debug switches.
- Handle every failure event with a distinct message: `fullscreenFailed` (`UNSUPPORTED`,
  `ALREADY_FULLSCREEN`), `shareMessageFailed`, `emojiStatusFailed`, sensor `*Failed`, and the
  `homeScreenChecked` statuses (`unsupported`, `unknown`, `added`, `missed`).

## 13. CSS variables Telegram sets [Official]

`--tg-color-scheme`, `--tg-viewport-height`, `--tg-viewport-stable-height`, the 15 `--tg-theme-*` colours
(§1), `--tg-safe-area-inset-{top,bottom,left,right}`, `--tg-content-safe-area-inset-{top,bottom,left,right}`.

## 14. Review checklist (every screen)

- [ ] G1 All colours from theme variables; day, night and a custom theme checked live.
- [ ] G2 320-430 px, compact and full height, desktop window; no `100vh`.
- [ ] G3 Main/Secondary/Back/Settings buttons and native popups instead of custom chrome.
- [ ] G4 Transform/opacity only, reduced motion respected, no long frames on mid Android.
- [ ] G5 Labels on all inputs and images, contrast in both schemes, targets ≥ 44 px.
- [ ] G6 Safe area + content safe area applied; fullscreen checked in both orientations.
- [ ] G7 `LOW` class gets the light variant.
- [ ] `ready()` after the first useful paint; chrome colours set before it; no own splash.
- [ ] Bottom-pinned UI uses the stable viewport height.
- [ ] Haptics per the table; closing confirmation only with unsaved input; swipes left enabled.
