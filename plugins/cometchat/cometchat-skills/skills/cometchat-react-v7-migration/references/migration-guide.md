# migration-guide — CometChat React UI Kit v6 → v7 (BAKED breaking-change map)

Distilled from the official migration docs (`ui-kit/react/migration-overview` + `migration-property-changes`) and a real **v6.5.4 → v7.1.0** export diff. Bake this map; **fetch the exhaustive prop-by-prop table** from `migration-property-changes` (docs-map) for anything not covered here. v6 names appear in tables/prose (they no longer exist in v7); v7 code is the target.

## 0. What actually changed
v7 is a rewrite that keeps **init/login and most component props compatible**, but replaces global singletons with React-native patterns. Five real breaks: (1) deps (incl. Calls SDK v4→v5 and the dropped `./css-variables.css` export), (2) RxJS events → a hook, (3) `DataSource`/`ChatConfigurator` → plugins, (4) `CometChatMessageTemplate`/`templates` props → plugins (**`textFormatters` is NOT removed** — it just relocated off `CometChatMessageList` to the composer/bubbles), (5) a handful of symbol renames (incl. `CometChatUIKit.getLoggedinUser()` async → `getLoggedInUser()` sync). Plus: wrap in `CometChatProvider`, `theme` prop, calling on via `uiKit:{callsSDK:{}}` (initFromSettings) / classic `.setCallingEnabled(true)`.

## 1. Dependencies
```bash
npm install @cometchat/chat-uikit-react@7 @cometchat/chat-sdk-javascript@^4.1.13 dompurify@^3.3.1
npm uninstall rxjs   # v7 drops the rxjs dependency
```
| Package | v6 | v7 |
|---|---|---|
| `@cometchat/chat-uikit-react` | `^6.x` | `^7.0.0` |
| `@cometchat/chat-sdk-javascript` | `^4.x` | `^4.1.13` (peer) |
| `react` | `>=18` | `>=18 <21` |
| `dompurify` | — | **`^3.3.1` — v7 needs it** (the kit imports it at runtime). It's in the kit's `dependencies`, but **install it explicitly** (the official docs do) — transitive-only resolution breaks in strict/pnpm/bundler setups. |
| `@cometchat/calls-sdk-javascript` (if calling) | `^4.x` | **`^5.x`** — bump the major (`npm install @cometchat/calls-sdk-javascript@5`); v7 pins `^5.x` (verified). NOT the same major as v6-era, so it is NOT "unchanged". |
| `rxjs` | required | **removed** |
| **CSS import** | `import "@cometchat/chat-uikit-react/css-variables.css"` | **that export is GONE in v7** — use `import "@cometchat/chat-uikit-react/styles"` (the only CSS export; package `exports` = `.` + `./styles`). A leftover `css-variables.css` import fails to resolve. See `cometchat-react-v7-core/references/theming.md`. |

## 2. Symbol removals / renames (v6 → v7) — verified vs a real v6.5.4 → v7.1.0 EXPORT diff
> **Init class is `CometChatUIKit` in BOTH v6 and v7 — no casing change.** `CometChatMessageComposer` and `CometChatMessageList` etc. keep the same names. Below are the ACTUAL removed/renamed public exports.

| v6 symbol | v7 | Action |
|---|---|---|
| `CometChatDocumentBubble` | — (removed) | **REMOVED.** Not a rename: v6 shipped `CometChatDocumentBubble` AND `CometChatFileBubble` side by side; v7 keeps `CometChatFileBubble` (unchanged) and drops `CometChatDocumentBubble`. |
| `CometChatCompactMessageComposer` | `CometChatMessageComposer layout="compact"` | removed as a component (→ the composer's `layout` prop) |
| `CometChatMessageTemplate` | plugin `renderBubble()` (see §4) | removed |
| `CometChatMessageEvents`, `CometChatGroupEvents`, `CometChatCallEvents`, `CometChatUserEvents`, `CometChatConversationEvents`, `CometChatUIEvents` | `useCometChatEvents` / `usePublishEvent` (see §3) | removed (RxJS) |
| `CometChatUIKitLoginListener` | removed (init/login is imperative; gate on `getLoggedInUser()`) | removed |
| `CometChatUIKit.getLoggedinUser()` (async, lowercase "in") | `CometChatUIKit.getLoggedInUser()` (**capital "In", SYNCHRONOUS**, returns `CometChat.User \| null`) | **RENAMED + return-type change.** v6's `getLoggedinUser()` returned a `Promise`; v7's `getLoggedInUser()` is sync — drop the `await`/`.then()` and read the return value directly. (The Chat SDK still has the async `CometChat.getLoggedinUser()`; the UIKit wrapper is the one that changed.) |
| `CometChatEmojiKeyboard`, `CometChatMediaRecorder` | built into `CometChatMessageComposer` | removed |
| `CometChatToast`, `CometChatListItem`, `CometChatNotificationBadge` | internal to their host components | removed |
| `CometChatUrlsFormatter` | `CometChatUrlFormatter` | rename (plural→singular; `id="url-formatter"`) |
| `CometChatTextHighlightFormatter` | — (removed) | **REMOVED** (no direct replacement). v7 formatter set: `CometChatTextFormatter` · `CometChatMentionsFormatter` · `CometChatUrlFormatter` · `CometChatMarkdownFormatter` · `CometChatRichTextFormatter`. |
| monolithic prop bags | composable **slot props** (`*RootProps`/`*HeaderProps`/`*ItemProps`) | additive — flat props still work |

> The message list's DEFAULT bubble routing moved to the multi-attachment bubbles: `CometChatImageBubble`→`CometChatImagesBubble`, `CometChatVideoBubble`→`CometChatVideosBubble`, `CometChatFileBubble`→`CometChatFilesBubble`, `CometChatAudioBubble`→`CometChatAudiosBubble`/`CometChatVoiceNoteBubble`. The singular bubbles still ship for standalone use — only the list's routing changed.

## 3. RxJS events → the unified event hook
v6 exposed per-domain RxJS Subjects; v7 merges SDK + UI events into one bus.
```diff
- import { CometChatMessageEvents } from "@cometchat/chat-uikit-react";
- CometChatMessageEvents.ccMessageSent.subscribe((data) => { /* … */ });
```
```tsx
import { useCometChatEvents } from "@cometchat/chat-uikit-react";
useCometChatEvents((event) => {
  if (event.type === "ui:message/sent") { /* … */ }
}, []); // 2nd arg (React.DependencyList) is REQUIRED
// publish: const publish = usePublishEvent(); publish({ /* … */ });
```

## 4. DataSource / ChatConfigurator → plugins
```diff
- class MyDecorator extends DataSourceDecorator { getTextMessageBubble() { /* … */ } }
- ChatConfigurator.enable(new MyDecorator());
```
```tsx
const MyPlugin: CometChatMessagePlugin = {
  id: "my-plugin",
  messageTypes: ["custom-type"],
  messageCategories: ["custom"],
  renderBubble(message, context) { return <MyBubble message={message} />; },
  getOptions(message, context) { return []; },
  getLastMessagePreview(message, loggedInUser, t) { return "Preview text"; }, // optional; (message, loggedInUser, t?)
};
<CometChatProvider plugins={[MyPlugin]}><div>{/* your chat UI */}</div></CometChatProvider>   // `children` is REQUIRED
```
The `templates` prop is removed → move custom message rendering to a plugin. **`textFormatters` is NOT removed** (verified vs 7.1.0): it's still a prop on `CometChatMessageComposer`, the bubble components, `CometChatSearch` and `CometChatMessageInformation` — but NOT on `CometChatMessageList`/`CometChatConversations`. The list's text bubbles are rendered by the text plugin, which reads its own `getTextFormatters()` (default: markdown + mentions + URL), so a v6 list-level formatter moves to an override of that one method:
```tsx
import { CometChatProvider, CometChatTextPlugin, CometChatMarkdownFormatter, CometChatMentionsFormatter, CometChatUrlFormatter } from "@cometchat/chat-uikit-react";
// HashtagFormatter = the app's own CometChatTextFormatter subclass (the migrated v6 formatter)
const textPlugin = { ...CometChatTextPlugin, getTextFormatters: () => [new CometChatMarkdownFormatter(), new CometChatMentionsFormatter(), new CometChatUrlFormatter(), new HashtagFormatter()] };
<CometChatProvider plugins={[textPlugin]}><div>{/* your chat UI */}</div></CometChatProvider>;   // provider plugins precede defaultPlugins → this wins
```
Full plugin API: fetch `plugins/overview` (docs-map).

## 5. Component prop changes (the common ones — exhaustive table = fetch `migration-property-changes`)
| Pattern | v6 | v7 |
|---|---|---|
| View prop type | `JSX.Element` | `ReactNode` (compatible) |
| Date format type | `CalendarObject` | `CometChatDateFormatConfig` (same shape) |
| Error UI | `hideError` prop (removed from lists; **retained on `CometChatMessageComposer`**) | `errorView` prop (pass custom error UI) |
| Loading UI | `disableLoadingState` prop | `loadingView` prop (pass custom loading UI) |
| Message templates | `templates` prop | plugins (§4) |
| Text formatters on LIST components | `textFormatters` prop (message list / conversations) | no list prop — override the text plugin's `getTextFormatters()` (§4); the `textFormatters` PROP remains on the composer, bubbles, `CometChatSearch`, `CometChatMessageInformation` |
| Bubbles | presentational (`src`/`text`/`isSentByMe` required) | self-extracting — pass `message`; overrides optional |

## 6. Provider, theming, calling (minor)
- **Provider (required):** wrap the chat tree in `CometChatProvider` (init/login stay imperative + unchanged from v6).
- **Theming:** same CSS variables; `data-theme="dark"` attribute → `theme="dark"` prop on `CometChatProvider` (or the `useTheme()` hook).
- **Calling:** enable in the init settings — `uiKit: { callsSDK: {} }` passed to `CometChatUIKit.initFromSettings` (the classic `new UIKitSettingsBuilder()…setCallingEnabled(true).build()` + `init()` still works but skips the ai-agent telemetry path). Not a provider prop. Without it, call UI hides + the Calls SDK doesn't load.
- **Localization:** v7 localizes via `CometChatProvider` (auto `LocaleProvider`); switch language with its `locale` prop (`<CometChatProvider locale="fr">`). `init` / `setCurrentLanguage` / `addTranslation` are **INSTANCE** methods on `CometChatLocalize`, NOT statics — reach the live instance with `CometChatLocalize.getSharedInstance()` (e.g. `CometChatLocalize.getSharedInstance()?.addTranslation({ "en-us": { … } })`, **nested per-language** `Record<lang, Record<key,string>>`; other config via `getSharedInstance()?.init({ translationsForLanguage, timezone, calendarObject, … })`). **Don't `new CometChatLocalize(...)`** — the provider reads only the shared instance (registered by `CometChatUIKit.init*` / the provider), so a constructed one isn't wired to the UI; and the `locale` prop (default `"en-us"`) is applied on mount/change, overriding an earlier `init({ language })`. Read strings via the `useLocale()` hook. **Some KEYS changed v6→v7** — a stale v6 key falls through to the raw string (`getLocalizedString` returns the key on a miss), so a snake_case token like `group_info` in the UI = a missing key. Re-verify any custom translation keys against v7; never render a key literally.

## 7. Localization migration (the `sample_` raw-key trap) — EDIT the app
**Symptom:** the UI renders raw keys like `group_info`, `add_members`, `delete_chat`, `view_members`, `banned_members` (snake_case) instead of "Group Info" etc. **Cause:** v7 **namespaced the sample-app strings under a `sample_` prefix**, so the v6 unprefixed keys now MISS and `getLocalizedString` returns the raw key.

**Fix the client's app (this skill edits it):**
1. Find every localization key the app uses — `getLocalizedString("<key>")`, custom panel/button/tab labels, any hardcoded `sample_*`/unprefixed key.
2. **Look up the EXACT v7 key — never guess.** The kit ships them in its source: `@cometchat/chat-uikit-react` → `src/resources/CometChatLocalize/resources/<lang>/translation.json` (en-us default), also the public GitHub repo + the localization docs `.md`. The sample-app strings are prefixed **`sample_`** — ~77 of them (`sample_group_info` = "Group Info", `sample_add_members`, `sample_delete_chat`, `sample_view_members`, `sample_banned_members`, `sample_delete_and_exit`, `sample_delete_chat_confirm`, `sample_delete_exit_confirm`, `sample_add_1_member`/`sample_add_n_members`, `sample_create_group`, `sample_block_contact`, …).
3. **Two strategies (prefer A — keeps it bundled):**
   - **A — map to the bundled `sample_` key:** `getLocalizedString("group_info")` → `getLocalizedString("sample_group_info")`. Resolves from the kit's built-in translations; no registration.
   - **B — keep the app's key + register the value** (only if the key isn't in the kit): `addTranslation` is an INSTANCE method — `CometChatLocalize.getSharedInstance()?.addTranslation({ "en-us": { group_info: "Group Info", add_members: "Add Members" /* … */ } })` (nested per-language), once at startup after the provider mounts.
4. **Migrate the init to the v7 method:** `CometChatProvider` auto-localizes (default en-us); switch language with its `locale` prop (`<CometChatProvider locale="fr">`). `init` / `setCurrentLanguage` are INSTANCE methods (`CometChatLocalize.getSharedInstance()?.setCurrentLanguage(lang)`), NOT statics. Drop any obsolete v6 localization init.
5. **Verify:** build/typecheck passes and no snake_case token renders as a label when you open the app.

## Removed concepts → replacement
| v6 | v7 |
|---|---|
| `DataSource` / `DataSourceDecorator` | `CometChatMessagePlugin` |
| `ChatConfigurator.enable()` | `plugins` prop on `CometChatProvider` |
| `*Events` (RxJS) | `useCometChatEvents` / `usePublishEvent` |
| `CometChatMessageTemplate` | plugin `renderBubble()` |
| `*Configuration` objects | direct props on compound sub-components |

> For anything not listed, fetch the prop-by-prop reference: `migration-property-changes` and `migration-overview` (via `cometchat-react-v7-core/references/docs-map.md`). Do NOT guess a v6→v7 mapping — verify against the docs.
