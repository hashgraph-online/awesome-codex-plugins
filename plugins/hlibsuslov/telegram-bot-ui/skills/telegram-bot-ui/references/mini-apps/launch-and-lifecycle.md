---
summary: "Mini App entry points, startapp, main app, startup, running, ending, hosting, test environment, fullscreen on phones with the sheet as fallback; read when wiring how an app opens and lives."
verified: "2026-11-23"
bot_api: "10.5"
---

# Launching a Mini App and living through its session

Where a Mini App can be opened from, what each entry gives it, how it starts, pauses and ends, and where
it is hosted. Checked on **2026-11-23** against https://core.telegram.org/bots/webapps, the Bot API 10.5
page and https://core.telegram.org/bots/serverless. The bot-side calls behind each entry (and what the
bot receives) are in [../mini-apps-bridge.md](../mini-apps-bridge.md); this page is the app's side.

Labels: **[API]** Bot API; **[Official]** Mini Apps page; **[Heuristic]** this skill's advice.

## Contents

- [1. Entry points](#1-entry-points)
- [2. `startapp` and opening mode](#2-startapp-and-opening-mode)
- [3. Main Mini App and the Apps catalogue](#3-main-mini-app-and-the-apps-catalogue)
- [4. Starting: from tap to first useful screen](#4-starting-from-tap-to-first-useful-screen)
- [5. Running: visibility, viewport, theme](#5-running-visibility-viewport-theme)
- [6. Ending and returning to the chat](#6-ending-and-returning-to-the-chat)
- [7. Hosting: your domain or Telegram Serverless](#7-hosting-your-domain-or-telegram-serverless)
- [8. Test environment and debugging](#8-test-environment-and-debugging)
- [9. Opening mode: fullscreen on phones, the sheet elsewhere](#9-opening-mode-fullscreen-on-phones-the-sheet-elsewhere)

## 1. Entry points

| Entry | Set up | `initData` beyond `user`, `auth_date`, `hash`, `signature` | Return a result by |
|---|---|---|---|
| Reply keyboard `KeyboardButton.web_app` (private chats) | bot sends the keyboard | nothing (the page calls it empty) | `WebApp.sendData(data)` ≤ 4096 bytes → `web_app_data`; the app closes |
| Inline button `InlineKeyboardButton.web_app` (private chat with the bot; not business or ephemeral messages) | bot sends the button | `query_id`, `can_send_after` | your server → `answerWebAppQuery` (message from the user "via @bot"; the app closes) |
| Menu button (`setChatMenuButton` with `MenuButtonWebApp`, or @BotFather) | per chat or default | `query_id` | `answerWebAppQuery`; since 7.6 the menu button URL may be a `t.me` link to the bot's Mini App |
| Main Mini App (profile button; `t.me/<bot>?startapp=<p>&mode=compact\|fullscreen`) | @BotFather only (no Bot API method) | `start_param`, `chat_type`, `chat_instance` | no chat access: `shareMessage`, inline mode, or a bot message after `requestWriteAccess` |
| Direct link `t.me/<bot>/<app>?startapp=<p>&mode=…` | @BotFather `/newapp` | `start_param`, `chat_type`, `chat_instance` | same as Main Mini App |
| Inline mode (`answerInlineQuery` `button.web_app`) | bot answers inline queries | nothing; `tgWebAppBotInline` launch param | `WebApp.switchInlineQuery(query)`; the user picks a result |
| Attachment menu (`?startattach`) | @BotFather `/setattach`; production only for major Telegram Ad Platform advertisers | `query_id`, `receiver` or `chat`, `start_param` | `answerWebAppQuery` into that chat |
| Chat join request (10.1) | the bot handles join requests for the chat | `chat_join_request_query_id`, `chat` | your server → `answerChatJoinRequestQuery` (`approve`, `decline`, `queue`) |
| Home-screen shortcut (8.0) | `WebApp.addToHomeScreen()` | not documented | — |

All rows **[Official]**/**[API]**. Consequences **[Heuristic]**:

- Decide the entry before the screens: only reply-keyboard apps can `sendData`; only `query_id` apps can
  post into the chat; Main Mini App and direct links cannot write to the chat at all.
- Never infer the entry from `platform` or the URL; read which fields `initData` actually has, on the
  server, after validation.
- One app usually serves several entries. Route by the presence of `query_id`, `start_param` and
  `chat_join_request_query_id`, and keep a screen for "opened without context".

```json
{"method": "setChatMenuButton", "params": {"chat_id": 111111111,
  "menu_button": {"type": "web_app", "text": "Open shop", "web_app": {"url": "https://shop.example.com/?lang=en"}}}}
```

```json
{"method": "answerInlineQuery", "params": {"inline_query_id": "4920000000000001",
  "results": [], "cache_time": 0, "is_personal": true,
  "button": {"text": "Pick a coffee in the app", "web_app": {"url": "https://shop.example.com/inline"}}}}
```

A join request with a `query_id` must be answered within 10 seconds, either by opening the Mini App or by
deciding directly. **[API]**

```json
{"method": "sendChatJoinRequestWebApp", "params": {
  "chat_join_request_query_id": "AAEAAAE-join-7781",
  "web_app_url": "https://club.example.com/verify"}}
```

## 2. `startapp` and opening mode

- `startapp=<param>` reaches the app as `initData.start_param` and as the `tgWebAppStartParam` query
  parameter. Keep it to `[A-Za-z0-9_-]` and short; use base64url for structured data. A 512-character cap is widely quoted but is not stated on core.telegram.org/bots/webapps or /api/links (checked 2026-11-25): **[Unverified]**, test the length you need.
- It is text from a link anyone can write: parse it against an allowlist (`order-8812`, `tab-bonus`),
  never use it as a path, a SQL fragment, an HTML fragment or an authorization claim. **[Heuristic]**
- `mode=compact` opens at half height; `mode=fullscreen` asks for fullscreen; Main Mini Apps and direct
  links open at full height by default (direct links since 7.6). **[Official]**
- Map each `startapp` to a screen in one table in code, with a default for unknown values. A bot alert
  that says "Payment received" opens `startapp=order-8812`, not the home screen. **[Heuristic]**

## 3. Main Mini App and the Apps catalogue

- Enabled in @BotFather (Bot Settings → Configure Mini App). It adds the "Open app" button to the bot's
  profile, `t.me/<bot>?startapp` links, media previews (localised screenshots and videos) and listing in
  search's Apps tab for users who opened it. **[Official]**
- Featuring in the Mini App Store favours apps with a Main Mini App, quality previews, Stars payments for
  digital goods and design that follows Telegram's guidelines
  ([telegram-design-guidelines.md](telegram-design-guidelines.md)). **[Official]**

## 4. Starting: from tap to first useful screen

Telegram shows its loading screen (icon and separate light and dark colours, set in @BotFather → Configure
Mini App) until the app calls `ready()`. **[Official]** The order **[Heuristic]**:

1. Copy `location.hash` launch parameters on the first line of the entry script (a hash router may clear
   them).
2. Apply theme CSS (variables are already set) and chrome colours: `setHeaderColor`,
   `setBackgroundColor`, `setBottomBarColor` (gated).
3. Draw the real first screen with skeletons where data loads.
4. Call `ready()`. Then fetch data with `Authorization: tma <initData>` ([security.md](security.md)).
5. Configure native buttons for this screen (MainButton, BackButton) after the screen exists.

No own splash or logo screen after Telegram's, no blank page, no spinner-only screen. How the app opens
(fullscreen on phones, the expanded sheet elsewhere) is one call before `ready()`: §9.

## 5. Running: visibility, viewport, theme

| Moment | Signal | Do **[Heuristic]** |
|---|---|---|
| User minimises the app or switches tabs (8.0) | `deactivated`, `isActive = false` | pause polling, timers, video, live tickers |
| User returns | `activated` | resume; refetch anything older than its freshness budget |
| User drags the sheet | `viewportChanged` with `isStateStable: false` | nothing; wait for `true` |
| Theme switch, night mode | `themeChanged` | re-read JS-held colours; CSS variables update themselves |
| Fullscreen toggled, rotation | `fullscreenChanged`, `safeAreaChanged`, `contentSafeAreaChanged` | CSS variables update; re-measure JS layouts |

## 6. Ending and returning to the chat

- Unsaved input: `enableClosingConfirmation()` while it exists; off after saving. **[Official]**
- `close()` after a final action only when the result is visible elsewhere (a bot message in the chat,
  `answerWebAppQuery`). A confirmation screen inside the app is often better than closing. **[Heuristic]**
- After an action the user expects to see in the chat, the bot posts it: `answerWebAppQuery` for
  `query_id` launches, `sendData` for reply-keyboard launches, otherwise a bot message — only if the user
  allowed it (`requestWriteAccess` → `write_access_allowed`, or the user started the bot). **[API]**
- Since 7.0 `openTelegramLink` keeps the app open; `openLink` always does. **[Official]**

## 7. Hosting: your domain or Telegram Serverless

| | Own domain | Telegram Serverless (2026-10) |
|---|---|---|
| Front-end URL | your HTTPS origin, set in @BotFather or `web_app.url` | `https://app<app_id>.tgcloud.ai/` |
| Server code | yours | endpoints in `tgcloud/endpoints/*`, called with `WebApp.Serverless.call(name, input, cb)` |
| `initData` | you validate it on every request ([security.md](security.md)) | the platform validates it and rejects with `UNAUTHORIZED` before your code runs |
| Database | yours | platform SQLite |
| Framing | Telegram Web opens the app in an iframe: do not send `X-Frame-Options: DENY` or a `frame-ancestors` that excludes Telegram Web | handled by the platform |

All **[Official]** except the framing advice for own domains **[Heuristic, verify in Telegram Web]**.
Since Bot API 10.2 Mini App methods are refused when called from an origin other than the app's own
(enabled for all apps on 2026-07-20, can be turned off in @BotFather): one app, one origin; no iframes of
other sites that call `Telegram.WebApp`, no redirects to another domain mid-session. **[API]**

## 8. Test environment and debugging

- A separate test account and bot on Telegram's test server; plain HTTP Mini App URLs are allowed there.
  Bot API test endpoint: `https://api.telegram.org/bot<token>/test/METHOD`. **[Official]**
- iOS: tap Settings 10 times → Allow Web View Inspection → Safari Develop menu. Android: enable USB
  debugging and WebView debugging in Telegram's settings → `chrome://inspect`. Telegram Desktop and macOS
  betas have their own debug switches. **[Official]**
- The local preview stand (`scripts/preview_miniapp.py`) mocks the client for layout work; it proves nothing
  about real clients ([performance-and-testing.md](performance-and-testing.md)).

## 9. Opening mode: fullscreen on phones, the sheet elsewhere

The skill's default for every Mini App it builds or restyles **[Heuristic, owner decision 2026-11-26]**: the
app fills the phone screen, keeps Telegram's controls readable and degrades to the expanded sheet wherever
fullscreen does not exist. One call before `ready()`:

```ts
tma.start();                          // = { fullscreen: 'mobile' }
tma.start({ fullscreen: 'always' });  // games, video, maps: fullscreen on Desktop too
tma.start({ fullscreen: 'never' });   // a deliberate sheet (a quick picker over the chat)
```

| Client | What `tma.start()` does | `<html data-tma-fullscreen>` |
|---|---|---|
| iOS, Android, 8.0+ | `expand()`, then `requestFullscreen()`; `fullscreenChanged` confirms | `on` |
| Desktop, macOS, Web, 8.0+ | `expand()` only: a fullscreen window over the desktop reads as a takeover | `off` |
| older than 8.0, or no `requestFullscreen` | `expand()` only | `unsupported` |
| refused (`fullscreenFailed: UNSUPPORTED`) | stays expanded | `unsupported` |
| outside Telegram (plain browser) | nothing | `unsupported` |

- **[Official]** `requestFullscreen` is 8.0; the result comes as `fullscreenChanged` or `fullscreenFailed`
  (`UNSUPPORTED`, `ALREADY_FULLSCREEN`). Links can ask too: `t.me/<bot>/<app>?startapp&mode=fullscreen`, and
  the Main Mini App's launch mode is set in @BotFather; the app still calls `tma.start()`, because a launch
  from a menu button, an inline button or an older link does not carry the mode.
- **Safe areas.** In fullscreen Telegram draws its Close and ⋯ controls over the content and the status bar is
  transparent. Content pads with `--tg-safe-area-inset-*` plus `--tg-content-safe-area-inset-*` (the kit's
  `--tma-safe-*` add both; [telegram-design-guidelines.md](telegram-design-guidelines.md) §6). Floating own
  controls (tab bar) sit above the bottom inset. Keep `setHeaderColor` and `setBottomBarColor`: they colour the
  status bar area and the bottom bar in both modes.
- **Rotation and the user leaving fullscreen** arrive as `fullscreenChanged`, `safeAreaChanged` and
  `contentSafeAreaChanged`; CSS variables follow, `tma.fullscreen` and `data-tma-fullscreen` follow.
- **Accidental closing.** Swipe down still minimises the app in fullscreen. The kit turns vertical swipes off
  only while a sheet is open (the sheet's own scroll and drag would otherwise close the app) and back on after;
  `tma.verticalSwipes(false)` for apps whose own gestures are vertical (drawing, maps, games). Unsaved input:
  `tma.closingConfirmation(true)` until it is saved.
- **Check:** `scripts/preview_miniapp.py <app> --serve 8790`, then `?platform=ios&version=9.6` (fullscreen,
  floating Close), `?platform=ios&version=7.10` (expanded sheet with the header), `?platform=tdesktop`
  (sheet). Lint MA46 flags an app that never decides its opening mode.
