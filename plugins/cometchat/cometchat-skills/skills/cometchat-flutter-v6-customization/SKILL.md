---
name: cometchat-flutter-v6-customization
description: "Theme and brand the Flutter v6 UI Kit — light/dark mode, the CometChatColorPalette / CometChatTypography / CometChatSpacing theme extensions, per-widget style objects, and view slots. Triggers: 'change chat colors flutter', 'dark mode chat flutter', 'match my brand flutter', 'customize cometchat theme flutter', 'override message bubble styles'."
license: "MIT"
compatibility: "Flutter >=3.38.9; cometchat_chat_uikit ^6.2.0 (6.2.x; catalog compiler-verified vs 6.1.0, source-checked vs 6.2.0)"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat flutter customization theming theme-extension styles v6"
---

> **Ground truth:** theming is Flutter's own `ThemeExtension` mechanism — `CometChatColorPalette`, `CometChatTypography`, `CometChatSpacing`, all catalog-verified against 6.1.0 and still present in 6.2.0. The exhaustive token list is FETCHED from the docs (`theme-introduction` · `color-resources` · `component-styling` · `message-bubble-styling` via `../cometchat-flutter-v6-core/references/docs-map.md`) — do NOT bake it.

## Companion skills (read first)
- `cometchat-flutter-v6-core` — install, credentials, `init→login→render`. This skill ASSUMES it.
- `cometchat-flutter-v6-components` — the widget catalog whose style objects and slots this skill sets.

## Use this skill when
Branding or theming: colors, fonts, light/dark, or per-widget style overrides.

**Cloning a named app, or mixing kit components with your own UI?** Measure the target's colors, type, spacing and radii into ONE token source, theme the kit from it, and style every custom component from the same tokens so kit and custom parts look like one design; host a kit component in your own dialog/panel when only its placement differs. Flow: `cometchat-onboarding` → `references/clone-mode.md` (Design sync, build levels L0–L6).

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
- **Localization** — via **`Translations`** (Flutter has no `CometChatLocalize`, through 6.2.0): `MaterialApp(localizationsDelegates: Translations.localizationsDelegates, supportedLocales: Translations.supportedLocales, ...)`, read strings with `Translations.of(context)`, override a language by extending its class (e.g. `TranslationsEn`) with your own delegate. Verified vs 6.2.0 source (`shared_ui/l10n/translations.dart`). The live `localize` page's intro says `CometChatLocalize` but its code uses `Translations`; follow the code.

### Avatar and sender name on every message (BAKED — verified vs 6.2.0)
The kit shows them only on others' messages in groups. From 6.2.0 `alignment: ChatAlignment.leftAligned` puts every bubble on the left, but it adds no avatar or name. When the target shows them (Slack, Discord, Teams), set `leftAligned`, wrap the default templates' `contentView` with an avatar + name row and set `avatarVisibility: false`, without asking first. This covers own and others' messages in 1:1 and group chats. Code and limits: `references/message-chrome.md`.

## Common pitfalls (BAKED)
- **Inventing a CometChat dark-mode switch.** Use `ThemeData` + `themeMode`; register the palette on both themes.
- **Guessing style parameter names.** They differ per widget — fetch the twin.
- **Hard-coding colours in a custom slot** instead of reading `CometChatThemeHelper`.
- **v5 theming APIs** — `CometChatTheme` is now only a `mergeThemeExtensions` helper, not a palette holder; the v5 `CometChatThemeData`/`DataSource` styling path is gone (→ `-migration`).
- **Restyling by wrapping the widget** rather than passing its style object or slot.

## Verify it works
The brand colour appears on the surfaces you expect, light and dark both render (toggle the OS setting), custom slot UI matches the kit's palette, and no widget silently kept its default because the palette was registered on only one theme.
