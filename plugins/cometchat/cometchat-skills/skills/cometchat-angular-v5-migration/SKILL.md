---
name: cometchat-angular-v5-migration
description: "Upgrade an Angular app from CometChat UI Kit v4 → v5 (`@cometchat/chat-uikit-angular` ^4 → ^5). Reads the repo's CometChat usage, applies the breaking-change map (deps, composite components removed, bare→Component renames, CometChatThemeService → CSS variables, event inputs → Outputs, DataSource → composition, localization renames), fetches the exhaustive guide, and verifies the build. Triggers: 'upgrade my v4 uikit to v5', 'migrate cometchat angular v4 to v5', 'upgrade @cometchat/chat-uikit-angular to v5', 'cometchat angular v4 to v5', 'bump cometchat angular uikit'."
license: "MIT"
compatibility: "Angular 17-21; FROM @cometchat/chat-uikit-angular ^4 (4.3.36) → ^5 (5.1.0–5.2.0 verified); @cometchat/chat-sdk-javascript ^4.1.13 (peer); @cometchat/cards-angular ^1.0.0 (new peer, undocumented in the official guide); @cometchat/uikit-elements/-resources/-shared removed"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat angular migration upgrade v4 v5 uikit"
---

> **Ground truth:** migrates an Angular app **FROM `@cometchat/chat-uikit-angular@4` TO `@5`**. v5 target symbols are catalog-verified vs installed 5.1.0; the v4→v5 breaking-change map is BAKED in `references/migration-guide.md` (distilled from the official "Upgrading From V4" guide + a real v4.3.36→v5.1.0 export diff — 146 genuine removals, 33 bare→`Component` renames, kept separate). The exhaustive per-component prop table is FETCHED from `cometchat-angular-v5-components/references/catalog.md` + the docs `.md` twins. **APPEND/transform the user's code — never wipe it; work on a branch and confirm before bulk edits** (`RULES.md`).

## Companion skills (read first)
- `cometchat-angular-v5-core` — the v5 init/login/render the migrated app lands on. This skill ASSUMES it.
- `cometchat-angular-v5-components` — the v5 component catalog (the target names + real inputs/outputs).
- `cometchat-angular-v5-placement` — how to rebuild a v4 composite from v5 modules (§2 of the migration guide points here per composite).

## Use this skill when
"upgrade my v4 UI Kit to v5", "migrate CometChat Angular v4→v5", "bump `@cometchat/chat-uikit-angular` to v5". Precondition: the project currently has `@cometchat/chat-uikit-angular@4`.

## Migration workflow (BAKED)
1. **Detect the starting point.** Confirm `package.json` has `@cometchat/chat-uikit-angular@4` (already `@5` → STOP, nothing to migrate). Note whether the app uses composite components (`…WithMessages`/`…WithDetails`), `CometChatThemeService`, `*Style` inputs, `DataSource`/`ChatConfigurator`, or custom localization keys — each drives a later step. **Work on a branch; transform in place, never delete the user's code.**
2. **Update dependencies.** `npm install @cometchat/chat-uikit-angular@5 @cometchat/chat-sdk-javascript@^4.1.13 @cometchat/cards-angular@^1.0.0` then `npm uninstall @cometchat/uikit-elements @cometchat/uikit-resources @cometchat/uikit-shared`. `@cometchat/cards-angular` is a genuine new 5.1.0 peer the official guide never mentions — install it or the build fails on a missing peer, not a CometChat error.
3. **Scan the repo for v4 usage.** Grep for every symbol in `references/migration-guide.md` §2 (composites, no-equivalent standalones, `DataSource`/decorators, the ~35 `*Style` objects) and §2b (the 33 bare-name renames) — produce the concrete change list before editing anything. A bare name is not automatically "removed"; check §2b first.
4. **Apply the breaking-change map** (`references/migration-guide.md`): §2/§2b symbol removals + renames, §3 theming (`CometChatThemeService` + `*Style` → CSS variables + the real `ThemeService`, **not** the official guide's own hand-rolled `matchMedia` example — see the warning in §3), §4 event-input → Output rename, §5 `DataSource`/`ChatConfigurator` → `MessageBubbleConfigService` or "nothing, it's auto-rendered," §6 drop `CUSTOM_ELEMENTS_SCHEMA` + convert to standalone, §7 optional `ChatStateService` adoption, §8 localization method renames.
   **The baked map is a closed list, not a prop reference — FETCH the rest** (`RULES.md` § Fetch discipline; **never** `node_modules/**/*.d.ts`), routed from `cometchat-angular-v5-core/references/docs-map.md`: the **official guide** `{DOCS_BASE}/ui-kit/angular/customization/migration-guide.md` for anything the map omits; a **component's** exact inputs/outputs/slots from its own `.md` twin (Angular has no `migration-property-changes` page — there is no single prop-diff table); an **SDK method** for a capability with no v5 component (`{SDK_DOCS_BASE}/sdk/javascript/groups-overview.md` et al.) — that is where the host-composed group surfaces in step 5 come from.
5. **Rebuild every composite from modules.** v5 has no composite components at all — `CometChatConversationsWithMessages` etc. must become a hand-stitched surface. Use `cometchat-angular-v5-placement/references/core-surface.md` (1:1) or `combined-app.md` (tabbed) as the target shape, not a literal prop-for-prop port — the composite's *configuration options* (which v4 had many of) don't exist in v5; its *behavior* is what you're reproducing.
6. **Verify.** Build/typecheck passes; NO v4 symbols remain (grep `references/migration-guide.md` §2's full list); every kit component is in its consumer's `imports: []`; the app renders after init→login resolves (`cometchat-angular-v5-core/references/lifecycle.md`). Reuse `cometchat-angular-v5-core` "Verify it works".

## Common pitfalls (BAKED)
- **Porting the official guide's own theming example.** It shows a hand-rolled `matchMedia` listener for OS-follow — that predates the real v5 mechanism. `ThemeService.initFromPreference()` already does this; don't reintroduce v4-era manual theme-tracking code (§3).
- **Treating a bare v4 name as removed when it's only renamed.** Check §2b (33 bare→`Component` renames) before concluding a component is gone — most "missing" names are one word away from their v5 form.
- **Missing `@cometchat/cards-angular`.** Genuinely undocumented in the official migration guide; the install fails on a peer-dependency error that looks unrelated to the migration.
- **Forgetting `imports: []` after dropping `CUSTOM_ELEMENTS_SCHEMA`.** v4's schema tolerated unregistered elements; v5's standalone components render **nothing, silently** if omitted from `imports: []` — the single most common v5 failure mode, and migrated code is exactly where it's missed (`cometchat-angular-v5-core/SKILL.md`).
- **Rebuilding a composite as a literal prop-for-prop port.** v4 composites had large configuration surfaces (`*Style` objects, callback inputs) with no v5 equivalent — port the *behavior*, not the *configuration*, using `cometchat-angular-v5-placement`'s real recipes as the target.
- **Assuming every `DataSourceDecorator` needs `MessageBubbleConfigService`.** Some were registering a *built-in extension* (polls, stickers, translation) — v5 auto-renders most of those once enabled in the dashboard, with nothing to register (`cometchat-angular-v5-features/SKILL.md`; verify against `needs_stitching` in `features.angular-v5.json`, never assume).

## Verify it works
Build/typecheck is green; a repo-wide grep finds NO §2 v4 symbols (composites, `CometChatThemeService`, `DataSource`/`ChatConfigurator`, any `*Style` object, any bare §2b name unqualified); every kit component is in `imports: []`; the app renders once init→login resolves; migrated theming follows the OS via `ThemeService`, not a leftover `matchMedia` listener. Full per-component prop reference: `cometchat-angular-v5-components/references/catalog.md` + the docs `.md` twins.
