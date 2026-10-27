---
name: cometchat-react-native-customization
description: "Theme, restyle and extend the CometChat React Native UI Kit v5 — theme modes and color tokens, per-component style objects, view slots, and the DataSource decorator chain for custom message types. Triggers: change CometChat colors React Native, dark mode RN chat, custom message bubble RN, brand the RN chat UI, custom message type React Native, restyle the message bubble, change the chat font, add a custom bubble RN."
license: "MIT"
compatibility: "React Native >=0.77; @cometchat/chat-uikit-react-native ^5.4.0"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "chat cometchat react-native customization theming styling datasource decorator"
---

> **Ground truth:** `@cometchat/chat-uikit-react-native@5` + catalog `rn-v5.json`.
> Docs: `/ui-kit/react-native/theme` · `colors` · `component-styling` · `message-bubble-styling`.
> Fetch token names and style keys from docs — never invent them.

## Companion skills (read first)
- `cometchat-react-native-core` — install, provider chain, init→login→render. Assumed, not repeated here.

## Use this skill when
- "change the chat colors" · "brand the chat UI" · "dark mode" · "restyle the bubbles"
- "custom message type" · "render my own bubble" · "add an option to the message menu"

## Prerequisites & install
None beyond `core`. Theming needs `CometChatThemeProvider` already in the chain (see `core`).

## Customization mechanism — three layers, cheapest first

**There is no CSS.** No stylesheets, no `className`, no `--cometchat-*` variables. If you are
holding a React snippet with CSS custom properties, it does not apply here.

### Layer 1 — theme mode + color tokens (whole app)
The provider takes a `theme` prop shaped `{ mode, light, dark }`. `mode` is `"light"` · `"dark"` ·
`"auto"` — **`"auto"` is what makes the kit follow the device (OS) light/dark setting** (it reads
`useColorScheme()`); the provider default is already `"auto"`.

```tsx
// Fixed dark for the whole app.
<CometChatThemeProvider theme={{ mode: "dark" }}>{/* … */}</CometChatThemeProvider>
```

```tsx
// Follow the OS, branded in BOTH schemes. mode:"auto" is the switch;
// set BOTH light and dark or dark falls back to defaults.
<CometChatThemeProvider
  theme={{
    mode: "auto",
    light: { color: { primary: "#F76808" } },
    dark: { color: { primary: "#F8935B" } },
  }}
>
  {/* … */}
</CometChatThemeProvider>
```

`primary` drives buttons, outgoing bubbles and active states — it is usually the only token a brand
change needs. Other common tokens: `textPrimary`, `background1`, `neutral50`, `extendedPrimary500`.
**Fetch the full list** from `/ui-kit/react-native/colors.md` rather than guessing a token name.

To follow the OS, use **`mode: "auto"`** and set both `light` and `dark`. Without the provider,
system theme changes are not reflected at all.

### Layer 2 — per-component style objects
Every component takes a `style` prop holding named sub-style objects — plain RN style objects,
not CSS:

```tsx
<CometChatConversations style={{ containerStyle: { backgroundColor: "#F7F7F7" } }} />
```

The same style keys can be set globally through the theme instead, which is preferable when the
change should apply everywhere:

```tsx
<CometChatThemeProvider theme={{ light: { conversationStyles: { /* … */ } } }}>
```

Style-key names differ per component. Fetch them from that component's page
(`/ui-kit/react-native/component-styling.md` and the component's own page) — do not pattern-match
from another component.

### Layer 3 — read the active theme in your own views
`useTheme()` returns the **resolved** theme (already light-or-dark per `mode`), so custom views match
the kit without re-deriving the palette:

```tsx
import { useTheme } from "@cometchat/chat-uikit-react-native";
import { Text } from "react-native";

const Label = () => {
  const theme = useTheme();
  return <Text style={{ color: theme.color.textPrimary }}>Chats</Text>;
};
```

## Custom message types — the DataSource decorator chain

⚠️ **RN does NOT have the React plugin API.** `CometChatMessagePlugin` and `CometChatPluginRegistry`
do not exist in this kit; emitting them will not compile. RN uses a decorator chain.

Extend `DataSourceDecorator`, override what you need, and register it with `ChatConfigurator.enable`:

```tsx
import {
  ChatConfigurator, DataSourceDecorator, CometChatMessageTemplate,
} from "@cometchat/chat-uikit-react-native";

const ORDER_TYPE = "order";

class OrderDataSource extends DataSourceDecorator {
  // 0. IDENTITY — REQUIRED. The base DataSourceDecorator.getId() THROWS
  // ("Method not implemented.") and ChatConfigurator.enable() calls getId() to
  // dedupe the registry — so a subclass without this override crashes at
  // ChatConfigurator.enable(...), NOT at render. Return a stable, unique id.
  getId(): string {
    return "order_message_datasource";
  }

  // 1. RENDER — how the bubble draws.
  getAllMessageTemplates(theme?: any, params?: any): CometChatMessageTemplate[] {
    const templates = super.getAllMessageTemplates(theme, params);
    // append or replace a template here
    return templates;
  }

  // 2. FETCH — WITHOUT THESE TWO THE MESSAGE IS NEVER RETRIEVED.
  // CometChatMessageList builds its request from them:
  //   requestBuilder.setTypes(ChatConfigurator.dataSource.getAllMessageTypes())
  //   requestBuilder.setCategories(ChatConfigurator.dataSource.getAllMessageCategories())
  // A type absent from those filters is excluded server-side. The bubble appears
  // optimistically when sent, then vanishes on reload — with no error anywhere.
  getAllMessageTypes(): string[] {
    return [...super.getAllMessageTypes(), ORDER_TYPE];
  }

  getAllMessageCategories(): string[] {
    const categories = super.getAllMessageCategories();
    return categories.includes(CometChat.CATEGORY_CUSTOM)
      ? categories
      : [...categories, CometChat.CATEGORY_CUSTOM];
  }
}

// AFTER login(), not merely after init(). CometChatUIKit.login() calls enableExtensions(),
// whose first statement is ChatConfigurator.init() — "re-initialize data source". Anything
// registered earlier is DISCARDED, so a decorator wired at module scope, or straight after
// init(), silently disappears.
await CometChatUIKit.login({ uid: UID });
ChatConfigurator.enable((source) => new OrderDataSource(source));
```

**`getId()` is REQUIRED on every `DataSourceDecorator` subclass.** It is the ONE base method that
does not delegate to the wrapped source — the base throws `Error("Method not implemented.")`, and
`ChatConfigurator.enable()` calls `getId()` to dedupe the registry. Omit it and registration crashes
at `ChatConfigurator.enable(...)` with `Method not implemented.` — NOT at render, so it reads as
unrelated. Every built-in decorator (Polls, Stickers, Translation, LinkPreview, Collaborative*)
overrides it; yours must too, returning a stable unique string.

A custom message type is **two halves, and only one of them is obvious.** Render is
`getAllMessageTemplates` / `getMessageTemplate`. Fetch is `getAllMessageTypes` /
`getAllMessageCategories`. Ship the render half alone and everything looks right until the first
reload, when every message of your type is gone — no error, no warning.

`DataSourceDecorator` exposes ~50 overridable methods; the ones you usually want are **`getId`**
(mandatory — see above), `getAllMessageTemplates`, `getMessageTemplate`, **`getAllMessageTypes`**,
**`getAllMessageCategories`**, `getMessageOptions` (the long-press menu) and
`getAuxiliaryOptions` (composer actions). Always call `super.<method>(...)` and modify the result —
replacing it wholesale drops every built-in message type.

> **DOCS GAP (RN-G10):** `DataSourceDecorator` / `MessageDataSource` / `ExtensionsDataSource` and
> `ChatConfigurator.enable` are **not documented** on any RN page — the docs show only mutating
> existing templates via `getAllMessageTemplates()`. Built from the kit source; flag this to the
> developer rather than presenting it as documented.
>
> **Partially closed (2026-08-20).** `ui-kit/react-native/message-list` now documents the
> half that actually breaks builds: a custom type must be registered for **fetch**
> (`getAllMessageTypes` / `getAllMessageCategories`), not only for render, and the decorator must
> be registered **after `login()`** because `enableExtensions()` re-runs `ChatConfigurator.init()`.
> Still missing: a dedicated RN custom-message-types page covering `DataSourceDecorator` /
> `MessageDataSource` / `ExtensionsDataSource` end to end. Owner: docs.

## Customizing an existing bubble without a decorator
To restyle rather than replace, prefer the theme's bubble style keys —
`textBubbleStyles`, `imageBubbleStyles`, `fileBubbleStyles`, `pollBubbleStyles` and siblings.
Fetch exact keys from `/ui-kit/react-native/message-bubble-styling.md`.

## Common pitfalls
1. **Reaching for CSS** — no stylesheets, no `className`, no `--cometchat-*`. Theme object + RN styles.
2. **Emitting the React plugin API** — does not exist; use `ChatConfigurator` + `DataSourceDecorator`.
3. **Omitting `getId()` on a decorator** — the base throws; `ChatConfigurator.enable()` calls it → crash at registration with `Method not implemented.`
4. **Not calling `super`** in a decorator override — silently drops all built-in templates.
5. **Setting only `light`** when the app follows the OS — dark mode then falls back to defaults.
6. **Guessing token or style-key names** — fetch them; a wrong key fails silently rather than erroring.

## Verify it works
- Every symbol appears in `catalogs/rn-v5.json`.
- `npm run verify:fences:rn-v5` compiles the examples against the pinned kit.
- On device: toggle OS dark mode and confirm the surface follows; confirm a custom template renders
  and built-in types still render alongside it.
