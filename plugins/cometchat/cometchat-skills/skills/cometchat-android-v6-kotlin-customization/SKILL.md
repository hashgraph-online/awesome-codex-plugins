---
name: cometchat-android-v6-kotlin-customization
description: "Make the CometChat Android v6 UI match your app in the Kotlin XML Views cohort — theming via CometChatTheme.DayNight attributes, per-component styles, message-bubble styling, ViewHolder view slots, state views, long-press and composer menu options, text formatters, custom message rendering with BubbleFactory, localization and sounds. Triggers: 'change cometchat colors android', 'brand the android chat ui', 'dark mode cometchat android xml', 'custom row in conversations', 'replace the empty state', 'add a message menu option', 'custom message type android'."
license: "MIT"
compatibility: "Android minSdk >=28; compileSdk >=36; Kotlin >=2.1; AGP >=8.9.1; JVM target 11; com.cometchat:chatuikit-kotlin-android ^6 (XML Views cohort) — 6.0.x, verified 6.0.5; com.cometchat:chat-sdk-android ^5"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat android customization theming styles v6 kotlin views dark-mode bubblefactory"
---

> **Ground truth:** catalog `android-v6.json` + the live Theming/Customization pages. Slot and style setters below were verified against the INSTALLED 6.0.5 source. Fetch exact token names from `color-resources`; **never invent a token or a setter**.
>
> ⚠️ **Kotlin XML Views cohort** — theming is XML theme attributes, slots are ViewHolder listeners. The Compose cohort (`CometChatTheme {}` + style data classes) is a separate skill.

## Companion skills (read first)
- `cometchat-android-v6-core` — install, credentials, init/login, the fetch map. Assumed here, never repeated.
- `cometchat-android-v6-kotlin-components` — what exists; this skill changes how it looks/behaves.

## Use this skill when
"match the chat to our brand", "use our fonts", "support dark mode", "restyle the conversation rows or bubbles", "replace the empty/loading/error view", "add an option to the message long-press menu", "render a custom message type", "highlight #hashtags", "translate the UI", "change notification sounds". **Theming lives HERE** — there is no separate theming skill.

## Customization mechanism map (pick the smallest one that does the job)
| Intent | Mechanism | Docs page (fetch for exact names) |
|---|---|---|
| brand color, global look, light/dark | **Theme** — extend `CometChatTheme.DayNight` | `theme-introduction` |
| exact token names | **Color resources** (`cometchat*` attrs) | `color-resources` |
| fonts / text styles | **Typography** (`CometChatTextAppearance*`) | `component-styling` (NOT `theme-introduction` — it documents colours only) |
| restyle ONE component | `setStyle(@StyleRes)` / `setStyle(CometChat<X>Style)` | `component-styling` |
| bubble look per message type | **Message-bubble styling** | `message-bubble-styling` |
| replace a REGION of a row/bubble | **View slots** (ViewHolder listeners / view providers) | `customization-view-slots` |
| replace empty / error / loading | `setEmptyView` / `setErrorView` / `setLoadingView` | `customization-state-views` |
| long-press or composer actions | `setOptions` / `setAddOptions`, `CometChatMessageOption`, `CometChatMessageComposerAction` | `customization-menu-options` |
| **custom message TYPE rendering** | **`BubbleFactory` + `setBubbleFactories`** | see below — *not* the docs' `message-template` page |
| custom text patterns | `CometChatTextFormatter` / `CometChatMentionsFormatter` / `CometChatRichTextFormatter` | `customization-text-formatters` |
| change what a list fetches | request builders + `setViewModel(...)` | `customization-viewmodel-data` |
| translate the UI / locale | `CometChatLocalize` | `localize` |
| in-app sounds | `CometChatSoundManager` | `sound-manager` |

## Theming — the top mechanism (BAKED; the rest of the table is a FETCH)
Extend the kit theme, then apply it in the manifest:
```xml
<!-- app/src/main/res/values/themes.xml -->
<style name="AppTheme" parent="CometChatTheme.DayNight">
    <item name="cometchatPrimaryColor">#F76808</item>
</style>
<!-- AndroidManifest.xml: <application android:theme="@style/AppTheme" …> -->
```
Programmatic equivalent: `CometChatTheme.setPrimaryColor(Color.parseColor("#F76808"))`.

**Brownfield — an app with its own design system NEVER re-parents its application theme.** `CometChatTheme.DayNight` parents `Theme.MaterialComponents.DayNight.NoActionBar`; re-parenting a Material3 host breaks its own screens (Material3-only attrs stop resolving), while skipping the kit theme crashes kit inflation (unresolved `?attr/cometchat*`). Keep the host theme and SCOPE the derived style to where kit views live: manifest `android:theme` on the chat Activities + `ContextThemeWrapper` for fragment/tab-embedded views — recipe: `kotlin-placement` Placement 2. App-wide re-parenting (above) is the greenfield path.

**Dark mode — follow the system by default.** Add `res/values-night/themes.xml` overriding the same attributes (`cometchatPrimaryColor`, `cometchatBackgroundColor1`, `cometchatTextColorPrimary`, …); Android applies it automatically. A theme can also be scoped to one Activity (`theme-introduction` §"Apply a Theme to a Specific Activity"). Override only the tokens you actually brand so future kit versions stay consistent.

## What's swappable — slots, verified against 6.0.5
**Lists** (`CometChatConversations`, and the same shape on `CometChatUsers`/`CometChatGroups`/`CometChatGroupMembers`):
`setItemView` · `setLeadingView` · `setTitleView` · `setSubtitleView` · `setTrailingView` — each takes a **`ConversationsViewHolderListener`** (a `createView`/`bindView` pair), not a `View`. Plus `setEmptyView`/`setErrorView`/`setLoadingView` (plain `View`), `setOptions`/`setAddOptions` for the long-press menu, `setOverflowMenu`, and `setConversationsRequestBuilder(...)` to scope the data.

**Message list** — per-region providers, each a `BubbleViewProvider`:
`setLeadingViewProvider` · `setHeaderViewProvider` · `setContentViewProvider` · `setReplyViewProvider` · `setBottomViewProvider` · `setStatusInfoViewProvider` · `setThreadViewProvider` · `setFooterViewProvider`.

## Custom message types — `BubbleFactory` (NOT message templates)
```kotlin
class ContactBubbleFactory : BubbleFactory() {
    override fun getCategory(): String = CometChatConstants.CATEGORY_CUSTOM
    override fun getType(): String = "contact"
    override fun createContentView(context: Context): View = ContactCardView(context)
    override fun bindContentView(
        view: View, message: BaseMessage,
        alignment: UIKitConstants.MessageBubbleAlignment,
        holder: RecyclerView.ViewHolder?, position: Int
    ) { (view as ContactCardView).bind(message) }
}
messageList.setBubbleFactories(listOf(ContactBubbleFactory()))
```
`createContentView()` runs **before** the message is known (only the factory key is available); the message arrives in `bindContentView()`. Optional: `createBubbleView`/`bindBubbleView` (replace the whole bubble), `createLeadingView`, `getBubbleStyle`.

⚠️ **The old v5 template API is absent from the shipped 6.0.5 artifact** — `CometChatMessageTemplate`, `setTemplates`, `setType`, `setCategory`, `setBubbleView`, `setMessageReceipt` do not compile (logged internally). The docs `message-template` page was corrected upstream (verified 2026-09-09): it is now "Message Bubble Factory" and teaches `BubbleFactory`. Use `BubbleFactory`.

## The rule
**Custom UI goes INSIDE the component** — a slot, a state view, a menu option, a formatter, a bubble factory — never a hand-built row stacked over a kit list, never a forked component. If no slot exists for what's needed, fetch the component's `.md` twin before inventing UI; if there genuinely is no hook, say so rather than re-implementing the component.

## Common pitfalls
Hardcoding hex per screen instead of theming once · inventing a token name (fetch `color-resources`) · styling only light mode (no `values-night`) · passing a `View` where a `ViewHolderListener`/`BubbleViewProvider` is required · stacking custom views on top of kit components · re-implementing a list to change one row · emitting `CometChatMessageTemplate` from the docs page · filtering data client-side instead of scoping the request builder.

## Verify it works
Compile: `./gradlew :app:assembleDebug   # in YOUR app (native-fence.mjs is a pack-repo gate, not installed by the CLI)`. On device: the brand color appears on kit surfaces; toggle system dark mode → the UI follows with readable contrast; a slotted view renders INSIDE its component; state views appear on empty/error/loading; a custom message type renders through its factory; a changed menu option shows on long-press.
