---
name: cometchat-flutter-v6-customization
description: "Theme and brand the Flutter v6 UI Kit — light/dark mode, the CometChatColorPalette / CometChatTypography / CometChatSpacing theme extensions, per-widget style objects, and view slots. Triggers: 'change chat colors flutter', 'dark mode chat flutter', 'match my brand flutter', 'customize cometchat theme flutter', 'override message bubble styles'."
license: "MIT"
compatibility: "Flutter >=3.38.9; cometchat_chat_uikit ^6 (6.1.x, verified 6.1.0)"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat flutter customization theming theme-extension styles v6"
---

> **Ground truth:** theming is Flutter's own `ThemeExtension` mechanism — `CometChatColorPalette`, `CometChatTypography`, `CometChatSpacing`, all catalog-verified against 6.1.0. The exhaustive token list is FETCHED from the docs (`theme-introduction` · `color-resources` · `component-styling` · `message-bubble-styling` via `../cometchat-flutter-v6-core/references/docs-map.md`) — do NOT bake it.

## Companion skills (read first)
- `cometchat-flutter-v6-core` — install, credentials, `init→login→render`. This skill ASSUMES it.
- `cometchat-flutter-v6-components` — the widget catalog whose style objects and slots this skill sets.

## Use this skill when
Branding or theming: colors, fonts, light/dark, or per-widget style overrides.

## Prerequisites & install
Covered by core. No new package.

## Customization mechanism (BAKED — v6)
Three tiers, in the order you should reach for them:

**1. App-wide theme — `ThemeExtension` on your `ThemeData`.** This is the main lever; it restyles every CometChat widget at once.
```dart
import 'package:cometchat_chat_uikit/cometchat_chat_uikit.dart';
import 'package:flutter/material.dart';

final cometchatLight = ThemeData(
  fontFamily: 'Inter',
  extensions: [
    CometChatColorPalette(primary: const Color(0xFFF76808)),
    CometChatTypography(),
    CometChatSpacing(),
  ],
);
```

**2. Light / dark — Flutter's own switching, nothing CometChat-specific.** Supply both themes and let `themeMode` decide; `ThemeMode.system` follows the OS, which is the right default for a fresh app.
```dart
import 'package:cometchat_chat_uikit/cometchat_chat_uikit.dart';
import 'package:flutter/material.dart';

Widget app(Widget home) => MaterialApp(
      theme: ThemeData(extensions: [CometChatColorPalette(primary: const Color(0xFFF76808))]),
      darkTheme: ThemeData.dark().copyWith(
        extensions: [CometChatColorPalette(primary: const Color(0xFFF76808))],
      ),
      themeMode: ThemeMode.system,   // follow the device setting
      home: home,
    );
```
> Unlike the web kit (a `theme` prop + CSS variables), Flutter has no CometChat-specific mode switch — **do not invent one**. Register the palette on BOTH themes or dark mode falls back to defaults.

**3. Per-widget style objects — scope one surface only.** Every widget takes a `*Style` object: `CometChatConversationsStyle` · `CometChatMessageHeaderStyle` · `CometChatMessageListStyle` · `CometChatMessageComposerStyle` · `CometChatThreadedHeaderStyle` · `CometChatSearchStyle` · `CometChatIncomingMessageBubbleStyle` / `CometChatOutgoingMessageBubbleStyle` · `CometChatCallLogsStyle`.
```dart
import 'package:cometchat_chat_uikit/cometchat_chat_uikit.dart';
import 'package:flutter/material.dart';

Widget themedHeader(User user) => CometChatMessageHeader(
      user: user,
      messageHeaderStyle: const CometChatMessageHeaderStyle(
        backgroundColor: Color(0xFFFFFFFF),
        titleTextColor: Color(0xFF141414),
        subtitleTextColor: Color(0xFF727272),
        onlineStatusColor: Color(0xFF09C26F),
      ),
    );
```
> **Style parameter names are per-widget and NOT guessable** — the header uses `titleTextColor`/`onlineStatusColor`, the threaded header uses `bubbleContainerBackGroundColor`/`countTextColor`, search uses `searchBackgroundColor`/`searchBorderRadius`. Fetch the widget's `.md` twin before writing a style block.
> Message bubbles are themed app-wide through `CometChatIncomingMessageBubbleStyle` / `CometChatOutgoingMessageBubbleStyle` registered as theme extensions — see `message-bubble-styling`.

## Reading theme values in your own widgets
`CometChatThemeHelper.getColorPalette(context)` (and the typography/spacing equivalents) returns the resolved palette, so custom UI in a slot matches the kit instead of hard-coding hexes.

## Beyond colour — the other customization axes (FETCH the page)
- **View slots** — replace any row/section (`customization-view-slots`); custom UI goes IN the slot.
- **State views** — `loadingStateView` / `emptyStateView` / `errorStateView` (`customization-state-views`).
- **Menu options** — add or remove message actions via `CometChatMessageOption` and the template's `options` (`customization-menu-options`). The callback is `onItemClick(message, state)`.
- **Text formatters** — `CometChatMentionsFormatter` and custom `CometChatTextFormatter` subclasses (`customization-text-formatters`, `custom-text-formatter-guide`). A subclass must implement `init`, `getMessageInputTextStyle`, `handlePreMessageSend`, `onChange` and `onScrollToBottom` — the class is abstract.
- **Message templates** — custom message types and bubbles (`message-template`, → `-components`).
- **Sounds** — the class is **`SoundManager`**, UN-prefixed (there is no `CometChatSoundManager`), a singleton: `SoundManager().play(sound: Sound.incomingMessage, customSound: "assets/ping.mp3")` / `.stop()`. Compiler-verified vs 6.1.0. It is absent from the catalog only because that tracks `CometChat*` symbols — same as `User`/`Group`. Page: `sound-manager`.
- **Localization** — via `CometChatLocalize`, the same localization class the other families use: register its delegate in `MaterialApp.localizationsDelegates` and read/override strings through it. Fetch the exact Flutter API from the live `localize` page (`references/docs-map.md` → Localization). **[STAGED — needs the UI Kit change]** `CometChatLocalize` requires a `cometchat_chat_uikit` version that exposes it; the pinned **6.1.0 does not** (it exposes `Translations`). Bump the pin + refresh `catalogs/flutter-v6.json` when that kit ships — until then Flutter localization emitted this way will not compile.

## Common pitfalls (BAKED)
- **Inventing a CometChat dark-mode switch.** Use `ThemeData` + `themeMode`; register the palette on both themes.
- **Guessing style parameter names.** They differ per widget — fetch the twin.
- **Hard-coding colours in a custom slot** instead of reading `CometChatThemeHelper`.
- **v5 theming APIs** — `CometChatTheme` is now only a `mergeThemeExtensions` helper, not a palette holder; the v5 `CometChatThemeData`/`DataSource` styling path is gone (→ `-migration`).
- **Restyling by wrapping the widget** rather than passing its style object or slot.

## Verify it works
The brand colour appears on the surfaces you expect, light and dark both render (toggle the OS setting), custom slot UI matches the kit's palette, and no widget silently kept its default because the palette was registered on only one theme.
