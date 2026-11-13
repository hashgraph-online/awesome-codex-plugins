---
name: cometchat-ios-customization
description: "Brand and restyle the CometChat iOS UI Kit — theme colours, typography, per-component styles, localisation and sounds. Use for any 'make it match our brand' or 'change how it looks' request. Triggers: 'change cometchat colors ios', 'brand the chat ui swift', 'dark mode cometchat ios', 'custom font chat kit', 'localize cometchat ios'."
license: "MIT"
compatibility: "CometChatUIKitSwift 5.2.3+ (Up to Next Major) · iOS 15.1+"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat ios theming customization branding swift v5"
---

## Companion skills (read first)
- `cometchat-ios-core` owns setup and the golden path. This skill ADDS appearance. Exact token lists live in the docs — fetch via `cometchat-ios-core/references/docs-map.md` (`theme-introduction`, `color-resources`, `component-styling`, `message-bubble-styling`).

## Use this skill when
"match our brand", "change the accent colour", "use our font", "dark mode", "restyle the bubbles", "translate the UI".

**Cloning a named app, or mixing kit components with your own UI?** Measure the target's colors, type, spacing and radii into ONE token source, theme the kit from it, and style every custom component from the same tokens so kit and custom parts look like one design; host a kit component in your own dialog/panel when only its placement differs. Flow: `cometchat-onboarding` → `references/clone-mode.md` (Design sync, build levels L0–L6).

## Three levels — go global first, per-component only when you must
**1. Global theme (start here).** `CometChatTheme` exposes **static** colour vars — `primaryColor`, `extendedPrimaryColor50...900`, `neutralColor50...`, `white`, `black`. Set them once at startup, before rendering, and every component follows. This is the branding lever: one primary colour usually does the whole job.

**2. Typography.** `CometChatTypography.setFont(name:)` swaps the family app-wide. Do this alongside the theme, not per component.

**3. Per-component styles.** Each component takes a style object — `ConversationsStyle`, `SearchStyle`, `AvatarStyle`, `BadgeStyle`, `ReceiptStyle`, `StatusIndicatorStyle`, `TypingIndicatorStyle`, `DateStyle` and the per-bubble styles (`TextBubbleStyle`, `AudioBubbleStyle`, `CallBubbleStyle`, `BaseMessageBubbleStyle`, ...). **These are assigned as properties, not passed through setters**: `conversations.avatarStyle = style`, `conversations.style = ConversationsStyle()`. Reach for these only when the global theme cannot express what you need.

> Style type names are **mostly un-prefixed** — it is `ConversationsStyle`, `AvatarStyle`, `DateStyle`, with no `CometChat` prefix on any of them. 491 of the kit's 638 public types are un-prefixed, so prefixing a style name is the most common way to invent a type that does not exist. Check `catalogs/ios-v5.json` before writing one.

## Avatar and sender name on every message
Kit default: avatar + name only on OTHERS' messages in GROUPS; none on your own rows, and 1:1 chats never get a name. When the target shows them on every message (Slack, Discord, Teams), apply the fix yourself, without asking, for own and others' messages in 1:1 and group chats: `references/message-chrome.md` (BAKED — verified vs 5.1.22): `.leftAligned` + `hideAvatar = false` + wrapped templates.

## Dark mode — the kit already does it

**Do NOT write trait-collection observers or reassign theme values on appearance changes.** The iOS
kit follows the OS light/dark setting by ITSELF: its components override `traitCollectionDidChange`
and its palette is built from dynamic colours. Flipping the simulator (or the device) between light
and dark repaints the whole surface with **zero theming code** in the host app.

This is the opposite of the web kit, where `theme="system"` does not exist and the core must sync
`theme` ↔ `prefers-color-scheme` (AUDIT-004). Do not carry that habit across — on iOS the work is
already done, and an observer you add is redundant at best.

For BRAND colours that must differ per appearance, build them with the kit's helper rather than
branching on the current style yourself:

```swift
let brand = UIColor.dynamicColor(lightModeColor: .systemIndigo, darkModeColor: .systemTeal)
```

It resolves per trait collection automatically, so it keeps working when the OS setting changes.

## Localisation & sounds
`CometChatLocalize` for strings, `CometChatSoundManager` for the audio cues; per-component overrides via `set(customSoundForMessages:)`. **Never render a raw localisation key** — the kit's keys are SCREAMING_SNAKE (`TYPE_A_MESSAGE`, `CHATS`); if one appears on screen it means a missing or wrong key, not a label.

## Gotchas
- **Set the theme BEFORE the first render.** Restyling after components are on screen does not retroactively repaint them.
- **Styles are properties.** `component.set(avatarStyle:)` does not exist on the list components; assignment does.
- **Don't restyle what the theme already covers** — a per-component style that hardcodes a colour will drift from the brand the moment the theme changes.

## Verify it works
The brand colour appears on send buttons, badges and highlights without per-component work; the font applies across every screen; dark mode flips cleanly; no SCREAMING_SNAKE keys are visible anywhere.
