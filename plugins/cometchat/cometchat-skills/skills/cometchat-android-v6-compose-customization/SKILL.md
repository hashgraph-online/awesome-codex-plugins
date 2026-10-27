---
name: cometchat-android-v6-compose-customization
description: "Make the CometChat Android v6 UI match your app in the Jetpack Compose cohort — theming with the CometChatTheme composable and lightColorScheme/darkColorScheme, per-component style data classes, @Composable view slots, state views, menu options, text formatters, custom message rendering with bubble factories, localization and sounds. Triggers: 'cometchat compose theme', 'brand colors jetpack compose cometchat', 'dark mode compose cometchat', 'custom row composable', 'custom message type compose'."
license: "MIT"
compatibility: "Android minSdk >=28; compileSdk >=36; Kotlin >=2.1; AGP >=8.9.1; JVM target 11; com.cometchat:chatuikit-compose-android ^6 (Jetpack Compose cohort) — 6.0.x, verified 6.0.5; com.cometchat:chat-sdk-android ^5"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat android customization theming v6 compose dark-mode colorscheme"
---

> **Ground truth:** catalog `android-v6.json` + the Compose theme source. ⚠️ The theming API below was read from the INSTALLED 6.0.5 source and **differs from the docs** — see the callout. Fetch token names from `color-resources`; never invent one.
>
> ⚠️ **Jetpack Compose cohort** — theming is the `CometChatTheme` composable + colour-scheme factories; slots are `@Composable` lambdas. The Views cohort (XML theme attributes + ViewHolder listeners) is a separate skill.

## Companion skills (read first)
- `cometchat-android-v6-core` — install, credentials, init/login, the fetch map. Assumed here, never repeated.
- `cometchat-android-v6-compose-components` — what exists and its param conventions.

## Use this skill when
"match the chat to our brand", "use our typography", "support dark mode", "restyle rows or bubbles", "replace the empty/loading/error view", "add a long-press option", "render a custom message type", "translate the UI".  **Theming lives HERE** — there is no separate theming skill.

## Theming — the top mechanism (BAKED)
Wrap the kit UI in the `CometChatTheme` composable and override the colour scheme:
```kotlin
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import com.cometchat.uikit.compose.theme.CometChatTheme
import com.cometchat.uikit.compose.theme.darkColorScheme
import com.cometchat.uikit.compose.theme.lightColorScheme

@Composable
fun AppChatTheme(content: @Composable () -> Unit) {
    // Pass named params — CometChatColorScheme is NOT a data class, so there is no .copy().
    // Setting `primary` DERIVES the whole extended ramp (extendedPrimaryColor50…900) for you.
    val scheme = if (isSystemInDarkTheme()) {
        darkColorScheme(primary = Color(0xFF8B7FFF))
    } else {
        lightColorScheme(primary = Color(0xFFF76808))
    }
    CometChatTheme(colorScheme = scheme) { content() }
}
```
`CometChatTheme(colorScheme, shapes, typography, content)` provides all three through composition locals; read them anywhere with `CometChatTheme.colorScheme` / `.typography` / `.shapes`. **Follow the system by default** on a fresh integration (`isSystemInDarkTheme()`), and override only the tokens you actually brand so future kit versions stay consistent.

> ⚠️ **Docs drift — trust this file.** The docs Compose tab teaches `CometChatColorScheme.light()` / `.dark()`. Those factories **do not exist** in 6.0.5: the real ones are **top-level `lightColorScheme()` / `darkColorScheme()`** in `com.cometchat.uikit.compose.theme`, configured by **named params, not `.copy()`** (`CometChatColorScheme` is a plain class). Logged internally. The compile gate rejects both wrong forms.

## Customization mechanism map (pick the smallest one that does the job)
| Intent | Mechanism | Docs page (fetch for exact names) |
|---|---|---|
| brand colour, light/dark | `CometChatTheme(colorScheme = …)` + `lightColorScheme()`/`darkColorScheme()` | `theme-introduction` (Compose tab) |
| exact token names | `CometChatColorScheme` fields | `color-resources` |
| fonts / text styles | `CometChatTypography` (28 `TextStyle` named params: `titleBold`, `heading1Bold`, …), passed as `CometChatTheme(typography = …)` | **no shipped page documents Compose typography** — `theme-introduction` is colours-only and `component-styling` covers Views (`cometchatFontBold`). Use the signature here; do not fetch. |
| restyle ONE component | `style = CometChat<X>Style.default().copy(...)` (style classes ARE data classes) | `component-styling` |
| bubble look per type | bubble style data classes | `message-bubble-styling` |
| replace a REGION of a row | `@Composable` slot params — `itemView`, `leadingView`, `subtitleView`, `trailingView` | `customization-view-slots` |
| empty / error / loading | `hideEmptyState`/`hideErrorState`/`hideLoadingState` + your own composable | `customization-state-views` |
| long-press / composer actions | `options` / `addOptions` params | `customization-menu-options` |
| **custom message TYPE** | bubble factories (see below) | *not* the docs `message-template` page |
| custom text patterns | `textFormatters` + `CometChatTextFormatter`/`CometChatMentionsFormatter` | `customization-text-formatters` |
| what a list fetches | `conversationsRequestBuilder` (and the per-list equivalents) | `customization-viewmodel-data` |
| translate the UI | `CometChatLocalize` | `localize` |
| in-app sounds | `CometChatSoundManager` | `sound-manager` |

## What's swappable — slots are `@Composable` lambdas
```kotlin
CometChatConversations(
    modifier = Modifier.fillMaxSize(),
    trailingView = { conversation, typing -> MyUnreadPill(conversation) },   // (Conversation, TypingIndicator?)
    options = { context, conversation -> myMenuItems(conversation) },
    hideEmptyState = true,                                                   // then render your own
    conversationsRequestBuilder = ConversationsRequest.ConversationsRequestBuilder()
        .setConversationType("user"),                                        // scope in the REQUEST, not a client filter
    onItemClick = { /* navigate */ },
)
```
Slot params take `(@Composable (Conversation, TypingIndicator?) -> Unit)?` on the conversations list, with the analogous shape on users/groups/members. Style params take a data class: `style = CometChatConversationsStyle.default().copy(...)`.

## Custom message types — bubble factories, not templates
Register factories on the message list for custom categories/types; `createContentView` runs before the message is known, `bindContentView` receives it. ⚠️ **`CometChatMessageTemplate` and `setTemplates` are absent from the shipped 6.0.5 artifact** (logged internally). The docs `message-template` page was corrected upstream (verified 2026-09-09): it is now "Message Bubble Factory" and teaches the factory API — fetch its Compose tab for the current signatures.

## The rule
**Custom UI goes INSIDE the component** — a slot param, a style copy, a menu option, a formatter — never a composable stacked over a kit component with a `Box`, and never a forked component. If no slot exists, fetch the page's Compose tab before inventing UI; if there genuinely is no hook, say so rather than re-implementing the component.

## Common pitfalls
`CometChatColorScheme.light()` from the docs (use `lightColorScheme()`) · calling `.copy()` on a colour scheme (not a data class — pass named params) · forgetting `CometChatTheme { }` around kit UI (falls back to defaults) · theming only light mode (no `isSystemInDarkTheme()` branch) · hardcoding colours per screen · `Box`-stacking custom UI instead of using a slot param · re-implementing a list to change one row · client-side filtering instead of a scoped request builder · emitting `CometChatMessageTemplate`.

## Verify it works
Compile: `./gradlew :app:assembleDebug   # in YOUR app (native-fence.mjs is a pack-repo gate, not installed by the CLI)`. On device: the brand colour appears on kit surfaces; toggle system dark mode → the UI follows with readable contrast; a slot composable renders INSIDE its component; state views appear on empty/error/loading; a changed menu option shows on long-press.
