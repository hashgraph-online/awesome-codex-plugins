---
name: cometchat-android-v6-compose-customization
description: "Make the CometChat Android v6 UI match your app in the Jetpack Compose cohort — theming with the CometChatTheme composable and lightColorScheme/darkColorScheme, per-component style data classes, @Composable view slots, state views, menu options, text formatters, custom message rendering with bubble factories, localization and sounds. Triggers: 'cometchat compose theme', 'brand colors jetpack compose cometchat', 'dark mode compose cometchat', 'custom row composable', 'custom message type compose'."
license: "MIT"
compatibility: "Android minSdk >=28; compileSdk >=36; Kotlin >=2.1; AGP >=8.9.1; JVM target 11; com.cometchat:chatuikit-compose-android ^6 (Jetpack Compose cohort) — 6.1.x, verified 6.1.1; com.cometchat:chat-sdk-android ^5"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat android customization theming v6 compose dark-mode colorscheme"
---

> **Ground truth:** catalog `android-v6.json` + the Compose theme source. ⚠️ The theming API below was read from the INSTALLED 6.0.5 source (factories re-checked on 6.1.1) and **differs from the docs** — see the callout. Fetch token names from `color-resources`; never invent one.
>
> ⚠️ **Jetpack Compose cohort** — theming is the `CometChatTheme` composable + colour-scheme factories; slots are `@Composable` lambdas. The Views cohort (XML theme attributes + ViewHolder listeners) is a separate skill.

## Companion skills (read first)
- `cometchat-android-v6-core` — install, credentials, init/login, the fetch map. Assumed here, never repeated.
- `cometchat-android-v6-compose-components` — what exists and its param conventions.

## Use this skill when
"match the chat to our brand", "use our typography", "support dark mode", "restyle rows or bubbles", "replace the empty/loading/error view", "add a long-press option", "render a custom message type", "translate the UI".  **Theming lives HERE** — there is no separate theming skill.

**Cloning a named app, or mixing kit components with your own UI?** Measure the target's colors, type, spacing and radii into ONE token source, theme the kit from it, and style every custom component from the same tokens so kit and custom parts look like one design; host a kit component in your own dialog/panel when only its placement differs. Flow: `cometchat-onboarding` → `references/clone-mode.md` (Design sync, build levels L0–L6).

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
    // Setting `primary` DERIVES the whole extended ramp (extendedPrimaryColor50...900) for you.
    val scheme = if (isSystemInDarkTheme()) {
        darkColorScheme(primary = Color(0xFF8B7FFF))
    } else {
        lightColorScheme(primary = Color(0xFFF76808))
    }
    CometChatTheme(colorScheme = scheme) { content() }
}
```
`CometChatTheme(colorScheme, shapes, typography, content)` provides all three through composition locals; read them anywhere with `CometChatTheme.colorScheme` / `.typography` / `.shapes`. **Follow the system by default** on a fresh integration (`isSystemInDarkTheme()`), and override only the tokens you actually brand so future kit versions stay consistent.

> ⚠️ **Docs drift — trust this file.** The docs Compose tab teaches `CometChatColorScheme.light()` / `.dark()`. Those factories **do not exist** in 6.0.5 or 6.1.1: the real ones are **top-level `lightColorScheme()` / `darkColorScheme()`** in `com.cometchat.uikit.compose.theme`, configured by **named params, not `.copy()`** (`CometChatColorScheme` is a plain class). Logged internally. The compile gate rejects both wrong forms.

## Customization mechanism map (pick the smallest one that does the job)
| Intent | Mechanism | Docs page (fetch for exact names) |
|---|---|---|
| brand colour, light/dark | `CometChatTheme(colorScheme = ...)` + `lightColorScheme()`/`darkColorScheme()` | `theme-introduction` (Compose tab) |
| exact token names | `CometChatColorScheme` fields | `color-resources` |
| fonts / text styles | `CometChatTypography` (28 `TextStyle` named params: `titleBold`, `heading1Bold`, ...), passed as `CometChatTheme(typography = ...)` | **no shipped page documents Compose typography** — `theme-introduction` is colours-only and `component-styling` covers Views (`cometchatFontBold`). Use the signature here; do not fetch. |
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

### Avatar and sender name on every message (BAKED — verified vs 6.1.1 source + compiled)
What to check and why: `cometchat-onboarding/references/clone-mode.md` -> *Message chrome*. This is the Compose how-to.
**Kit default:** avatar and sender name only on INCOMING messages in a GROUP (`shouldShowAvatar`: LEFT and `isGroupConversation`; `DefaultHeaderView` shows the name only for group messages). Your own messages and every 1:1 chat get neither, and `messageAlignment = LEFT_ALIGNED` alone still leaves 1:1 chats bare.
**Do this whenever the target shows avatars/names (Slack, Discord, Teams); don't ask.** Fill the per-message `leadingView` (avatar) and `headerView` (name) slots on `CometChatMessageList`. A provided slot wins over the kit's rule for every message, own and others', in 1:1 and group chats:
```kotlin
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.cometchat.chat.constants.CometChatConstants
import com.cometchat.chat.models.BaseMessage
import com.cometchat.chat.models.Group
import com.cometchat.chat.models.User
import com.cometchat.uikit.compose.presentation.messagelist.ui.CometChatMessageList
import com.cometchat.uikit.compose.presentation.shared.baseelements.avatar.CometChatAvatar
import com.cometchat.uikit.compose.theme.CometChatTheme
import com.cometchat.uikit.core.constants.UIKitConstants

// The kit never draws the leading slot on centered action/call rows, but headerView renders on EVERY row.
private fun BaseMessage.hasSender() =
    category != CometChatConstants.CATEGORY_ACTION && category != CometChatConstants.CATEGORY_CALL

@Composable
fun ChannelMessageList(user: User?, group: Group?) {
    CometChatMessageList(
        user = user, group = group,
        messageAlignment = UIKitConstants.MessageListAlignment.LEFT_ALIGNED, // one left column, like Slack
        leadingView = { message, _ ->
            CometChatAvatar(modifier = Modifier.padding(end = 8.dp).size(32.dp),
                name = message.sender?.name ?: "?", avatarUrl = message.sender?.avatar)
        },
        headerView = { message, _ ->
            if (message.hasSender()) Text(message.sender?.name ?: "", style = CometChatTheme.typography.caption1Medium,
                color = CometChatTheme.colorScheme.textColorPrimary, modifier = Modifier.padding(bottom = 4.dp))
        },
    )
}
```
- Keep `LEFT_ALIGNED` for a Slack-style column: in `STANDARD` the leading slot of your own messages renders on the right. The slot's second argument is the core `MessageAlignment` (sender side), not the forced bubble alignment.
- A custom `headerView` replaces the kit's (time-in-header with `TimeStampAlignment.TOP` and the multi-attachment batch suppression go with it). Style the name from your token source.
- **Once per run** isn't reachable: a slot sees one message, not the previous one (L4).

## Custom message types — bubble factories, not templates
Register factories on the message list for custom categories/types; `createContentView` runs before the message is known, `bindContentView` receives it. ⚠️ **`CometChatMessageTemplate` and `setTemplates` are absent from the shipped 6.0.5 and 6.1.1 artifacts** (logged internally). The docs `message-template` page was corrected upstream (verified 2026-09-09): it is now "Message Bubble Factory" and teaches the factory API — fetch its Compose tab for the current signatures.

## The rule
**Custom UI goes INSIDE the component** — a slot param, a style copy, a menu option, a formatter — never a composable stacked over a kit component with a `Box`, and never a forked component. If no slot exists, fetch the page's Compose tab before inventing UI; if there genuinely is no hook, say so rather than re-implementing the component.

## Common pitfalls
`CometChatColorScheme.light()` from the docs (use `lightColorScheme()`) · calling `.copy()` on a colour scheme (not a data class — pass named params) · forgetting `CometChatTheme { }` around kit UI (falls back to defaults) · theming only light mode (no `isSystemInDarkTheme()` branch) · hardcoding colours per screen · `Box`-stacking custom UI instead of using a slot param · re-implementing a list to change one row · client-side filtering instead of a scoped request builder · emitting `CometChatMessageTemplate`.

## Verify it works
Compile: `./gradlew :app:assembleDebug   # in YOUR app (native-fence.mjs is a pack-repo gate, not installed by the CLI)`. On device: the brand colour appears on kit surfaces; toggle system dark mode → the UI follows with readable contrast; a slot composable renders INSIDE its component; state views appear on empty/error/loading; a changed menu option shows on long-press.
