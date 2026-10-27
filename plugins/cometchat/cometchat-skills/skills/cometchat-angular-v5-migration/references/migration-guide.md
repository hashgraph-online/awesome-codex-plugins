# migration-guide — CometChat Angular UI Kit v4 → v5 (BAKED breaking-change map)

Distilled from the official "Upgrading From V4" guide (`ui-kit/angular/customization/migration-guide`) and a real **v4.3.36 → v5.1.0 export diff** (v4 installed and catalogued the same way as v5 — `exports-only+members`). v4 names appear in tables/prose (they no longer exist in v5); v5 code is the target.

> **This map is the BAKED half. FETCH the other half — do not substitute the installed bundle for it.**
> This file is deliberately a *closed list*: what was removed, what was renamed, what replaces each concept. It is **not** a prop reference and does not try to be. For anything it does not name, fetch — never read `node_modules/**/*.d.ts` and never answer from memory (`RULES.md` § Fetch discipline):
> - **The official guide itself**, for the narrative/checklist view and anything this map omits: `{DOCS_BASE}/ui-kit/angular/customization/migration-guide.md` (route: `cometchat-angular-v5-core/references/docs-map.md`). Read it as a cross-check, **not** as the theming source — see the §3 warning.
> - **A v5 component's exact inputs/outputs/view slots** → that component's own `.md` twin (docs-map "Component docs"). Angular has **no** `migration-property-changes` page like React's, so per-component props come from the component pages — there is no single prop-diff table to fetch.
> - **A capability with no v5 component** (the host-composed group surfaces: create/join/add-members/banned-members/transfer-ownership) → the **SDK docs**, `{SDK_DOCS_BASE}/sdk/javascript/groups-overview.md` and siblings (docs-map "SDK docs"). Every `CometChat.*` group/user method signature lives there.
>
> A v4 name absent from §2/§2b is **not** proven gone — check the v5 catalog (`cometchat-angular-v5-components/references/catalog.md`) and the component docs before telling anyone a feature was dropped.

## 0. What actually changed
v5 is a rewrite: v4's composite ("WithMessages"/"WithDetails") components and web-component substrate are gone, replaced by small modular standalone Angular components you stitch together — the same shape of break React went through at v6→v7. Six real breaks: (1) shared deps + `CUSTOM_ELEMENTS_SCHEMA`, (2) composite components removed (build the surface from modules — `cometchat-angular-v5-placement`), (3) `CometChatThemeService`/`*Style` objects → CSS variables, (4) event inputs → `@Output()` EventEmitters (the `on` prefix drops), (5) `DataSource`/`ChatConfigurator`/extension decorators → direct composition + `MessageBubbleConfigService` (`cometchat-angular-v5-features/references/custom-messages.md`), (6) a handful of `CometChatLocalize` method renames. Plus: adopt `ChatStateService` (optional but recommended) instead of repeating `[user]`/`[group]` on every component.

## 1. Dependencies
```bash
npm install @cometchat/chat-uikit-angular@5 @cometchat/chat-sdk-javascript@^4.1.13
npm uninstall @cometchat/uikit-elements @cometchat/uikit-resources @cometchat/uikit-shared
```
| Package | v4 | v5 |
|---|---|---|
| `@cometchat/chat-uikit-angular` | `^4.x` | `^5.0.0` (5.1.0 verified) |
| `@cometchat/chat-sdk-javascript` | `^4.x` | `^4.1.13` (peer) |
| `@cometchat/uikit-elements` / `-resources` / `-shared` | required (web-component substrate shared across React/Angular/Vue) | **removed** — v5 is pure Angular standalone components |
| `@cometchat/cards-angular` | — | **new peer**, `^1.0.0` — required by 5.1.0, absent from the v4→v5 guide (a tracked docs gap, `cometchat-angular-v5-core/SKILL.md`) |
| Angular | v4-kit-compatible range | `>=17.0.0 <22.0.0` (verified 5.1.0; 22 hard-fails `npm install` today) |

## 2. Symbol removals — verified vs a real v4.3.36 → v5.1.0 EXPORT diff
> **146 v4 public exports have no v5 form under either name.** A separate 33 are **not removed** — only renamed, bare → `…Component` suffix (§2b). Don't grep-and-panic on a bare name before checking §2b first.

**Composite components — no v5 replacement; compose from modules instead.**

> **Which target shape? The v4 SOURCE decides, not preference: port to `core-surface.md` unless the v4 screen actually rendered a tab bar.** Verified against installed **4.3.36**: `cometchat-tabs` appears in exactly **one** v4 component — `CometChatContacts` — and **no composite renders an app-level tab bar**. `CometChatConversationsWithMessages` renders `cometchat-conversations` (sidebar) + `cometchat-messages` (pane) + `cometchat-contacts` (the "start conversation" **overlay**); the only tabs in that screen are Users/Groups *inside* the overlay (`CometChatContacts.tabVisibility` defaults to `TabsVisibility.usersAndGroups` — `cometchat-contacts.component.mjs:33`), which is a picker, not an app-level selector.
> So **every** rebuilt composite lands on `core-surface.md`. `combined-app.md` (the tabbed selector) is a **grow target — added only when the user asks**, per `cometchat-angular-v5-core/SKILL.md`'s core-vs-grow rule. Porting a composite straight onto the tabbed app invents a navigation level the v4 app never had.
> When the user *does* ask for tabs, build against the documented reference layout: `{DOCS_BASE}/ui-kit/angular/angular-tab-based-chat.md` (`@switch (activeTab)` over `ChatStateService`, left sidebar) — routed from `cometchat-angular-v5-core/references/docs-map.md` § Reference layouts. That page's own tab set is **one example** (Chats · Call Logs · Users), not the definitive list; `combined-app.md` ships four (chats · users · groups · calls). Compose the tabs the app needs.

(`cometchat-angular-v5-placement/references/core-surface.md` for the 1:1 pattern, `combined-app.md` only on request):

| v4 composite | Build in v5 from |
|---|---|
| `CometChatConversationsWithMessages` | `CometChatConversationsComponent` + `CometChatMessageHeaderComponent` + `CometChatMessageListComponent` + `CometChatMessageComposerComponent`, stitched via `(itemClick)` or `ChatStateService` |
| `CometChatUsersWithMessages` / `CometChatGroupsWithMessages` | `CometChatUsersComponent` / `CometChatGroupsComponent` + the same message-pane trio |
| `CometChatMessages` | The message-pane trio alone (no list) |
| `CometChatThreadedMessages` | `CometChatThreadHeaderComponent` + a second `CometChatMessageListComponent` bound to `[parentMessageId]` (`cometchat-angular-v5-placement/SKILL.md` "Threaded Messages") |
| `CometChatCallLogsWithDetails` | `CometChatCallLogsComponent` + your own detail panel (`cometchat-angular-v5-calls`) |
| `CometChatDetails` | Compose your own — header + `CometChatGroupMembersComponent` for a group (`cometchat-angular-v5-placement/references/combined-app.md` "Details panel") |

**Standalone v4 components with NO v5 equivalent at all — the feature must be rebuilt, not renamed:**
`CometChatContacts` · `CometChatTransferOwnership` · `CometChatUserMemberWrapper` · `CometChatAddMembers` · `CometChatBannedMembers` (v5: `<cometchat-group-members>`'s built-in ban/unban view — `cometchat-angular-v5-components/references/host-composed.md`) · `CometChatCreateGroup` · `CometChatJoinGroup` (both host-composed in v5 — no kit component; same file) · `CometChatDocumentBubble` (v5 keeps only `CometChatFileBubble` for documents) · `CometChatCallLogDetails` / `-History` / `-Participants` / `-Recordings` (no v5 call-log detail sub-components at all — `cometchat-angular-v5-calls` for what v5 does ship).

**Customization-layer classes removed — the whole v4 decorator/DataSource pattern is gone:**
`DataSource`, `DataSourceDecorator`, `ChatConfigurator`, `ExtensionsDataSource`, `AIExtensionDataSource`, and one `*Decorator`/`*Extension` pair per built-in extension (`PollsExtensionDecorator`, `StickersExtensionDecorator`, `MessageTranslationExtensionDecorator`, `LinkPreviewExtensionDecorator`, `ImageModerationExtensionDecorator`, `TextModeratorExtensionDecorator`, `ThumbnailGenerationExtensionDecorator`, `CollaborativeDocumentExtensionDecorator`, `CollaborativeWhiteBoardExtensionDecorator`, `CallingExtensionDecorator`, `AIAssistBotDecorator`, `AIConversationStarterDecorator`, `AIConversationSummaryDecorator`, `AISmartRepliesExtensionDecorator`, and their non-`Decorator` counterparts). **v5 replacement depends on what the decorator did:** a custom message type → `MessageBubbleConfigService.setBubbleView()` (`cometchat-angular-v5-features/references/custom-messages.md`); a built-in extension (polls, stickers, translation, …) → nothing to register at all, most are auto-rendered once enabled in the dashboard (`cometchat-angular-v5-features/SKILL.md`'s classify table — verify against `needs_stitching` in `features.angular-v5.json`, never assume).

**`*Style` config-object inputs — an entire category, not individually deprecated.** Every per-component style object (`AvatarStyle`, `BadgeStyle`, `ButtonGroupStyle`, `CallscreenStyle`, `CardStyle`, `CheckboxStyle`, `ConfirmDialogStyle`, `ConversationsStyle`, `CreateGroupStyle`, `DateStyle`, `DocumentBubbleStyle`, `DropdownStyle`, `EmojiKeyboardStyle`, `FileBubbleStyle`, `FullScreenViewerStyle`, `IconStyle`, `ImageBubbleStyle`, `InputStyle`, `JoinGroupStyle`, `LabelStyle`, `ListItemStyle`, `LoaderStyle`, `MediaRecorderStyle`, `MenuListStyle`, `MessageInputStyle`, `ModalStyle`, `PanelStyle`, `PopoverStyle`, `PreviewStyle`, `QuickViewStyle`, `RadioButtonStyle`, `ReceiptStyle`, `SearchInputStyle`, `SingleSelectStyle`, `TextBubbleStyle`, `TextInputStyle`, `ThumbnailGenerationExtensionStyle` — ~35 total) is **removed**. Do not hunt for a v5 renamed form; there isn't one. Delete the input and its object, then set the same values via CSS variables (§3).

**Small v4 UI atoms/primitives with no direct v5 export** (were public in v4, are internal to their host component in v5, OR have a differently-shaped v5 counterpart worth checking against the catalog before assuming gone): `CometChatIcon`, `CometChatLabel`, `CometChatInput`, `CometChatTextInput`, `CometChatSearchInput`, `CometChatDropdown`, `CometChatSingleSelect`, `CometChatModal`, `CometChatPanel`, `CometChatLoader`, `CometChatDivider`, `CometChatBackdrop`, `CometChatDraggable`, `CometChatQuickView`, `CometChatPreview`, `CometChatStatusIndicator`, `CometChatMenuList`, `CometChatList`, `CometChatReceipt`, `CometChatMessageInput`, `CometChatCard`. If one of these was load-bearing in the v4 app, check `cometchat-angular-v5-components/references/catalog.md` for a same-purpose v5 atom (`CometChatButtonComponent`, `CometChatAvatarComponent`, `CometChatDateComponent`, `CometChatPopoverComponent`, `CometChatCheckboxComponent`, `CometChatListItemComponent` cover several of these) before concluding the feature is gone.

## 2b. Renames — bare v4 name → `…Component` suffix, SAME component (33)
Not a removal. v4 exported the bare class name directly; v5's export always carries the `Component` suffix (the bare form is internal-only — `cometchat-angular-v5-core/SKILL.md` "Class name ≠ selector ≠ docs title"). Mechanical `sed`-safe rename, one for one:

`CometChatConversations` · `CometChatUsers` · `CometChatGroups` · `CometChatGroupMembers` · `CometChatMessageHeader` · `CometChatMessageList` · `CometChatMessageComposer` · `CometChatMessageBubble` · `CometChatMessageInformation` · `CometChatIncomingCall` · `CometChatOutgoingCall` · `CometChatOngoingCall` · `CometChatCallButtons` · `CometChatCallLogs` · `CometChatAvatar` · `CometChatButton` · `CometChatCheckbox` · `CometChatRadioButton` · `CometChatDate` · `CometChatPopover` · `CometChatContextMenu` · `CometChatActionSheet` · `CometChatConfirmDialog` · `CometChatChangeScope` · `CometChatFullScreenViewer` · `CometChatEmojiKeyboard` · `CometChatMediaRecorder` · `CometChatListItem` · `CometChatTextBubble` · `CometChatImageBubble` · `CometChatVideoBubble` · `CometChatAudioBubble` · `CometChatFileBubble`

Each rename adds the `Component` suffix to both the import and every usage site — e.g. `import { CometChatConversations } from '@cometchat/chat-uikit-angular'` becomes `import { CometChatConversationsComponent } from '@cometchat/chat-uikit-angular'`. Selectors are unaffected (kebab-case, unrelated to the class name).

## 2c. One rename outside the pattern — theming's entry point
`CometChatThemeService` (v4) → **`ThemeService`** (v5, `CometChat` prefix dropped — the one exception to §2b's suffix rule, because the whole theming *mechanism* changed too, not just the export name). See §3.

## 3. Theming — `CometChatThemeService` + `*Style` objects → CSS variables + `ThemeService`
v4 injected `CometChatThemeService` and called `theme.palette.setPrimary(...)`/`setMode(...)`; per-component `*Style` inputs (§2) covered everything CSS couldn't. v5 removes BOTH mechanisms — theming is CSS variables, full stop:
```css
/* styles.css */
@import '@cometchat/chat-uikit-angular/styles/css-variables.css';

.cometchat {
  --cometchat-primary-color: #f76808;
  --cometchat-neutral-color-300: #ffffff;
}
@media (prefers-color-scheme: dark) {
  .cometchat {
    --cometchat-primary-color: #f76808;
    --cometchat-neutral-color-300: #311502;
  }
}
```
> ⚠️ **The official migration guide's own OS-theme-follow example is a hand-rolled `matchMedia` listener — do not port it.** That recipe predates the real v5 mechanism. `ThemeService` (verified against the installed 5.1.0 kit) already does this natively: `initFromPreference()` reads `prefers-color-scheme` on construction and keeps its own `matchMedia` listener live; `setTheme('dark' | 'light')` / `toggleTheme()` set it manually. It writes `data-theme` on `<html>` through Angular's `DOCUMENT` token — SSR-safe. Use it instead of migrating the guide's own snippet (`cometchat-angular-v5-core/references/theming.md`, `cometchat-angular-v5-customization/SKILL.md`). **Known kit divergence, not this pack's error:** `ThemeService`'s own docstrings additionally claim it persists a manual choice to `localStorage` — it does not (`AUDIT-143`, owner uikit). Don't port v4 persistence logic expecting v5's service to already do it.

## 4. Event inputs → `@Output()` EventEmitters, `on` prefix dropped
| v4 (callback input) | v5 (`@Output()`) |
|---|---|
| `[onItemClick]="handler"` | `(itemClick)="handler($event)"` |
| `[onSelect]="handler"` | `(select)="handler($event)"` |
| `[onError]="handler"` | `(error)="handler($event)"` |
| `[onBack]="handler"` | `(backClick)="handler()"` |
| `[onThreadRepliesClick]="handler"` | `(threadRepliesClick)="handler($event)"` |
Mechanical per call site — drop `on`, lower-case the first letter after, move from `[ ]` to `( )`, add `($event)` if the v4 handler took an argument. **Verify the exact v5 output name against `cometchat-angular-v5-components/SKILL.md`'s per-component table before assuming a 1:1 drop-the-prefix match** — a few renamed further (`onBack` → `backClick`, not `back`).

## 5. `DataSource`/`ChatConfigurator` → direct composition
```diff
- class MyDecorator extends DataSourceDecorator { getTextMessageBubble() { /* … */ } }
- ChatConfigurator.enable(new MyDecorator());
```
```ts
import { MessageBubbleConfigService } from '@cometchat/chat-uikit-angular';
import { TemplateRef, inject } from '@angular/core';

class ChatComponent {
  private bubbleConfig = inject(MessageBubbleConfigService);
  myBubble!: TemplateRef<unknown>;

  registerBubble() {
    // v5: register a template against the message TYPE_CATEGORY key — see
    // custom-messages.md for send/fetch/render and the {type}_{category} key-format trap.
    this.bubbleConfig.setBubbleView('order_update_custom', { contentView: this.myBubble });
  }
}
```
Full pattern — including the local-echo requirement raw SDK sends need (`publishMessageSent`) and the `{type}_{category}` key rule: `cometchat-angular-v5-features/references/custom-messages.md`.

## 6. Shared web-component packages removed — pure standalone components now
```diff
- import { CUSTOM_ELEMENTS_SCHEMA, NgModule } from '@angular/core';
- import "@cometchat/uikit-elements";   // side-effect import
- @NgModule({ imports: [CometChatConversations], schemas: [CUSTOM_ELEMENTS_SCHEMA] })
```
```ts
// v5: standalone, no schema, no side-effect import, full type safety
import { Component } from '@angular/core';
import { CometChatConversationsComponent } from '@cometchat/chat-uikit-angular';

@Component({ standalone: true, imports: [CometChatConversationsComponent], template: `<cometchat-conversations></cometchat-conversations>` })
export class ChatComponent {}
```
Every component must be in the consuming component's `imports: []` or it renders nothing, silently — the #1 v5 failure mode (`cometchat-angular-v5-core/SKILL.md`).

## 7. State management — `ChatStateService` (optional, recommended)
v4 repeated `[user]`/`[group]` on every component. v5's `ChatStateService` (verified: `setActiveUser`/`setActiveGroup`/`setActiveConversation`/`activeUser`/`activeGroup`/`activeConversation` signals/`clearActiveChat`) centralizes it — set once, every subscribed component reacts. Explicit `[user]`/`[group]` props still work and take priority when passed, so this is additive, not required. Full pattern: `cometchat-angular-v5-placement/references/core-surface.md`.

## 8. Localization — method renames, not a new system
Both majors use `CometChatLocalize`; the class survives, some methods don't:

| v4 method | v5 method |
|---|---|
| `CometChatLocalize.setLocale("hi")` | `CometChatLocalize.setCurrentLanguage("hi")` |
| `CometChatLocalize.getLocale()` | `CometChatLocalize.getCurrentLanguage()` |
| `CometChatLocalize.init()` | not needed — auto-initializes |

v5 adds a `translate` pipe (`{{ 'SEND_MESSAGE' | translate }}`) and expands to 19 languages (from 12). Verified in the angular-v5 catalog: `setCurrentLanguage`/`getCurrentLanguage` exist, `setLocale` does not.

## Quick migration checklist
- [ ] `npm install @cometchat/chat-uikit-angular@5 @cometchat/chat-sdk-javascript@^4.1.13 @cometchat/cards-angular@^1.0.0` (the last is an undocumented new 5.1.0 peer — see §1)
- [ ] `npm uninstall @cometchat/uikit-elements @cometchat/uikit-resources @cometchat/uikit-shared`
- [ ] Remove `CUSTOM_ELEMENTS_SCHEMA` + any `import "@cometchat/uikit-elements"` side-effect import
- [ ] Convert to standalone components; every kit component in `imports: []` (§6)
- [ ] Rebuild every composite (`…WithMessages`, `…WithDetails`, `CometChatThreadedMessages`) from modules (§2)
- [ ] Grep for the 33 §2b bare names → add `Component` suffix
- [ ] Grep for `CometChatThemeService` → `ThemeService`, migrate to CSS variables + `initFromPreference()` (§3) — not the guide's own `matchMedia` example
- [ ] Delete every `*Style` input + object (§2), replace with CSS variable overrides
- [ ] Grep for `[onXxx]` inputs → `(xxx)` outputs (§4)
- [ ] Grep for `DataSource`/`DataSourceDecorator`/`ChatConfigurator`/`*Extension(Decorator)` → `MessageBubbleConfigService` or "nothing, it's auto-rendered" per §5
- [ ] Optionally adopt `ChatStateService` (§7)
- [ ] Grep for `setLocale`/`getLocale`/`CometChatLocalize.init()` → §8 renames
- [ ] Build/typecheck green; grep confirms **zero** §2 names remain; app renders after `init→login`

> **For anything not listed above, FETCH — do not guess and do not read the installed bundle.** The official guide (`{DOCS_BASE}/ui-kit/angular/customization/migration-guide.md`), the target component's `.md` twin, or the SDK page for a host-composed capability — all routed from `cometchat-angular-v5-core/references/docs-map.md`. Do NOT infer a v4→v5 mapping from `node_modules/**/*.d.ts`: the bundle tells you a symbol's *shape*, never whether it is the *sanctioned* replacement, and a `declare class` that isn't publicly exported reads identically to one that is (`CometChatSoundManager`, AUDIT-152).
