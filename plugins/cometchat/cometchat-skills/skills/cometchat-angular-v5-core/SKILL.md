---
name: cometchat-angular-v5-core
description: "Add CometChat chat to an Angular app end-to-end — detect the project, get & verify dashboard credentials, init→login→render with standalone components, and the drop-in conversation UI. The core knowledge every other Angular v5 skill builds on. Triggers: 'add chat to my angular app', 'integrate cometchat angular', 'set up cometchat credentials angular', 'show conversations and messages angular'."
license: "MIT"
compatibility: "Node.js >=18; Angular 17-21 (NOT 22 — see Install); @cometchat/chat-uikit-angular ^5 (5.1.0–5.2.0 verified); @cometchat/chat-sdk-javascript ^4"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat angular core chat integration uikit v5 setup credentials standalone"
---

> **Ground truth:** `@cometchat/chat-uikit-angular@^5` + `@cometchat/chat-sdk-javascript@^4`, symbols verified across 5.1.0–5.2.0 / 4.1.13–4.2.0 (unchanged set; catalog `verifiedCompatibleRange`). This file is the THIN map loaded every run; deep detail lives in `references/*`, loaded ONLY when the task needs it.

## Use this skill when
Adding CometChat to an Angular app, or you need the setup every other Angular v5 skill assumes: install, credentials, init→login→render ordering, and the component map.

## Prerequisites & install

### The three Angular rules that break everything else
Read these first. Each produces code that compiles, shows no error, and does not work.

1. **Every component must be in `imports: []`.** The kit ships *standalone* components. Use `<cometchat-conversations>` in a template without importing `CometChatConversationsComponent` into that component's `imports` array and Angular renders **nothing** — no error, no warning, blank space. This is the single most common failure.
2. **Config lives in `src/environments/environment.ts`, NOT `.env`.** Angular resolves it at build time via file replacement. Any `.env` instruction is wrong here.
3. **Class name ≠ selector ≠ docs title.** `CometChatConversationsComponent` (import) · `<cometchat-conversations>` (template) · "Conversations" (docs). All three are different; use the right one in the right place.

### Install
```bash
npm install @cometchat/chat-uikit-angular@^5 @cometchat/chat-sdk-javascript@^4 @cometchat/cards-angular@^1 dompurify@^3
```
Calls only (optional): `npm install @cometchat/calls-sdk-javascript@^5`

> ⚠️ **Angular 22 fails to install.** The kit's peer range is `@angular/core >=17.0.0 <22.0.0`, so `npm install` on Angular 22 hard-fails with `ERESOLVE`. Scaffold a new app with `npx -y @angular/cli@21 new <app>`. CometChat's stated policy is that 18+ is supported, so this range is expected to widen in a future kit release — until it ships, 22 does not work. Angular 17 works but is undocumented.

`angular.json` needs **three** changes under `projects.<app>.architect.build` — the stylesheet, the icon assets, and the production budgets.

`styles` — the kit stylesheet must come **FIRST**, before your own:
```json
"styles": [
  "node_modules/@cometchat/chat-uikit-angular/styles/css-variables.css",
  "src/styles.css"
]
```
> ⚠️ **Order decides, and failing it is SILENT** — the kit re-declares tokens under `[data-theme="dark"]` at your `:root`'s specificity, so appending the kit file makes it win and your brand colors vanish without error. Detail: `references/theming.md`.

`assets` — the kit ships ~300 SVG icons under `src/lib/assets` (the glob copies them all; count is not load-bearing):
```json
{ "glob": "**/*", "input": "node_modules/@cometchat/chat-uikit-angular/src/lib/assets", "output": "assets" }
```

**Production budgets — raise them or `ng build` HARD-FAILS.** The kit + Chat SDK is ~4.2 MB against a stock 1 MB error budget, so the DEFAULT `ng build` exits non-zero while `ng serve` is fine. Raise `budgets` + set `allowedCommonJsDependencies`: `references/dependencies.md`.

> ⚠️ **Miss the `assets` entry and icons are broken throughout the kit** (send/attach/emoji, call controls, menus) — nothing errors, it just reads as a theming problem. The single most commonly missed setup step in Angular.
> ⚠️ Do **not** `@import` the kit's `css-variables.css` in a `.scss`/`.css` file — the package's `exports` map does not expose that path and the build fails. The full `node_modules/...` path in `angular.json` bypasses it.

Full dependency table: `references/dependencies.md`.

## Setup & credentials (essentials — full detail: `references/setup-credentials.md`)
Three values: **App ID**, **Region**, **Auth Key**. When they are missing, **OFFER both paths and default to the fetch** — *"I can fetch them by logging into your CometChat dashboard, or you can paste them manually"* — and never end the build with a "add credentials yourself" TODO.

```ts
// src/environments/environment.ts
export const environment = {
  production: false,
  cometchat: { appId: 'APP_ID', region: 'REGION', authKey: 'AUTH_KEY' },
};
```
**A fourth value you must ASK for: the login UID.** The app logs in as somebody the moment it opens, and only the developer knows who that should be. **Ask — do not pick one silently:**

> *"Which user should the app log in as on startup? You'll find your UIDs under Dashboard → your app → Users. If this is a fresh app I can create `cometchat-uid-1` for you and log in as that."*

`cometchat-uid-1` is the docs **sample**, not a promise about this app — on an app whose sample users were never seeded, `login()` fails and the screen stays blank with no visible error. Never hardcode it and move on; if the developer has no UID, use the create-if-missing `ensureDevUser()` (`references/lifecycle.md`).

Create `environment.prod.ts` with the same shape and wire `fileReplacements` in `angular.json`. **The Auth Key is dev-only** — production mints an auth token server-side and calls `loginWithAuthToken`. See `references/setup-credentials.md`.

## Integration ordering (BAKED — invariant)
**`init()` must resolve BEFORE `login()`, and `login()` before any kit component renders.** Out of order, components mount with no session and render empty.

In Angular this is an app initializer, not a component effect:

```ts
// src/main.ts
import { bootstrapApplication } from '@angular/platform-browser';
import { CometChatUIKit } from '@cometchat/chat-uikit-angular';
import { environment } from './environments/environment';
// Angular 20+ scaffolds `src/app/app.ts` exporting `App`; 17-19 scaffold `app.component.ts`
// exporting `AppComponent`. Use whichever YOUR app has (wrong one → "Could not resolve …").
import { App } from './app/app';                 // Angular 20+ (CLI 21 default)
// import { AppComponent } from './app/app.component';   // Angular 17-19
import { appConfig } from './app/app.config';

const { appId, region, authKey } = environment.cometchat;
// authKey is DEV-only: prod ships it empty + logs in with a server token — so require it
// only in dev, else every prod build throws behind a green `ng build`.
if (!appId || !region) {
  throw new Error('CometChat appId/region empty — check src/environments/environment*.ts.');
}
if (!environment.production && !authKey) {
  throw new Error('CometChat authKey empty — dev login needs it (production uses an auth token).');
}

// `cometchat-uid-1` is the docs SAMPLE, not a guarantee this app has it — a missing UID renders a
// blank screen. Use a real UID from Dashboard → Users, or ensureDevUser() (references/lifecycle.md).
const uid = 'cometchat-uid-1';

// Prod only: YOUR backend mints this user's auth token (endpoint shape: cometchat-angular-v5-production).
async function fetchAuthToken(): Promise<string> {
  const res = await fetch('/api/cometchat-token', { credentials: 'include' });
  if (!res.ok) throw new Error(`CometChat token endpoint: HTTP ${res.status}`);
  return ((await res.json()) as { authToken: string }).authToken;
}

// initFromSettings (NOT the classic builder init) so integrationSource="ai-agent" propagates for
// telemetry attribution, and routes the Calls SDK too.
// Bootstrap the app in `finally` so it ALWAYS mounts: a failed init/login (empty prod authKey, a wrong
// UID, a network blip) must leave CHAT degraded, never the WHOLE Angular app blank behind a green build.
(async () => {
  try {
    await CometChatUIKit.initFromSettings({
      appId,
      region,
      credentials: { authKey },                              // dev only — empty in prod
      chatSDK: { presenceSubscription: { type: 'ALL_USERS' } },
    });
    await (environment.production
      ? CometChatUIKit.loginWithAuthToken(await fetchAuthToken())  // prod: authKey stays server-side
      : CometChatUIKit.login(uid));                                // dev: Auth-Key login
  } catch (e) {
    console.error('CometChat init/login failed', e);
  } finally {
    bootstrapApplication(App, appConfig).catch((err) => console.error(err));
  }
})();
```

Guarded login, `ensureDevUser` (create-if-missing for a dev start), `provideAppInitializer`, route guards, and the `loggedInUser$` Observable: `references/lifecycle.md`.

## Docs first for the API — the installed kit for BEHAVIOUR the docs omit
**What exists and what it is called comes from the docs.** Fetch the component's page (`references/docs-map.md` → `DOCS_BASE` + path + `.md`); read its **AI Integration Quick Reference** first. Do **not** invent an API from the type declarations — they expose internal-only names and members with no defined behaviour.

**But reading the shipped bundle IS correct when the docs state a prop and not its semantics** (e.g. `attachmentOptions` — does yours *append* or *replace*? it appends; `messagesRequestBuilder` — override or merge?). When behaviour is load-bearing and undocumented, verify it in `node_modules/@cometchat/chat-uikit-angular/fesm2022/*.mjs`, then (1) say in your summary you verified against the installed kit, and (2) report it as a docs gap.

> Full methodology + the worked examples — see `references/docs-map.md` § "Docs first for the API".

## Component / API map (BAKED closed list)
Exported **class** → template **selector**. Anything not here, look up via `references/docs-map.md` — do not guess.

| Class | Selector | Purpose |
| --- | --- | --- |
| `CometChatConversationsComponent` | `<cometchat-conversations>` | conversation list |
| `CometChatMessageHeaderComponent` | `<cometchat-message-header>` | active chat header |
| `CometChatMessageListComponent` | `<cometchat-message-list>` | message pane |
| `CometChatMessageComposerComponent` | `<cometchat-message-composer>` | composer |
| `CometChatThreadHeaderComponent` | `<cometchat-thread-header>` | thread panel header |
| `CometChatUsersComponent` | `<cometchat-users>` | user directory |
| `CometChatGroupsComponent` | `<cometchat-groups>` | group directory |
| `CometChatGroupMembersComponent` | `<cometchat-group-members>` | member management |
| `CometChatSearchComponent` | `<cometchat-search>` | search surface |
| `CometChatErrorBoundaryComponent` | `<cometchat-error-boundary>` | error containment |
| `CometChatIncomingCallComponent` | `<cometchat-incoming-call>` | app-root call listener |

Non-component exports you will need: `CometChatUIKit` (init/login), `UIKitSettingsBuilder`, `ChatStateService` (active chat state), `CometChatUIKitConstants`, `CometChatLocalize`, `ThemeService`.

> **Naming exception:** the AI-assistant exports carry **no** `Component` suffix — `CometChatAIAssistantChat`, not `…ChatComponent`.

## Golden path — the production-ready CORE surface
The default for an unscoped "add chat": ships conversations · messages. **This is deliberately the CORE surface, not the whole app** — a users / groups / calls **tab selector**, a details or thread side panel, threads, search, and calling are **grow targets**, correct to omit unless asked. Build them via `cometchat-angular-v5-placement` (`references/combined-app.md` / `references/core-surface.md`), not by improvising here.

```ts
// src/app/chat/chat.component.ts
import { Component, inject } from '@angular/core';
import { CometChat } from '@cometchat/chat-sdk-javascript';   // Conversation / User / Group types
import {
  CometChatConversationsComponent, CometChatMessageHeaderComponent,
  CometChatMessageListComponent, CometChatMessageComposerComponent,
  CometChatErrorBoundaryComponent, CometChatUIKitConstants, ThemeService,
} from '@cometchat/chat-uikit-angular';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [                                 // ← omit this and NOTHING renders
    CommonModule,
    CometChatErrorBoundaryComponent,
    CometChatConversationsComponent,
    CometChatMessageHeaderComponent,
    CometChatMessageListComponent,
    CometChatMessageComposerComponent,
  ],
  templateUrl: './chat.component.html',
  styleUrl: './chat.component.css',
})
export class ChatComponent {
  // FOLLOW THE OS light/dark setting: the kit ships both themes but does NOT follow the OS itself.
  // `initFromPreference()` reads prefers-color-scheme + keeps its own matchMedia listener live — do
  // not hand-roll one; put it in the ROOT component for a multi-page app (references/theming.md).
  constructor() { inject(ThemeService).initFromPreference(); }

  // TWO slots, never one: `(itemClick)` emits a Conversation whose subject is a User (1:1) OR a Group.
  // Binding one `selected` to `[user]` ships clean on 1:1 and throws "getUid is not a function" on a GROUP.
  // `| undefined`, NOT `| null` — the kit declares `user?`/`group?` and strictTemplates (ON by default)
  // rejects `| null` with TS2322. Full rationale: references/anti-patterns.md.
  selectedUser: CometChat.User | undefined = undefined;
  selectedGroup: CometChat.Group | undefined = undefined;
  get hasChat() { return !!(this.selectedUser || this.selectedGroup); }

  onItemClick(conversation: CometChat.Conversation) {
    const subject = conversation.getConversationWith();
    // Ask the Conversation what it is — do NOT duck-type on getGuid() (a Conversation has none, so it
    // silently sends every group down the user path).
    if (conversation.getConversationType() === CometChatUIKitConstants.MessageReceiverType.group) {
      this.selectedGroup = subject as CometChat.Group;
      this.selectedUser = undefined;
    } else {
      this.selectedUser = subject as CometChat.User;
      this.selectedGroup = undefined;
    }
  }
}
```

```html
<!-- chat.component.html -->
<cometchat-error-boundary>
  <div class="cc-shell">
    <aside class="cc-side">
      <cometchat-conversations class="cc-fill" (itemClick)="onItemClick($event)"></cometchat-conversations>
    </aside>
    <!-- Pass BOTH slots on all three components; exactly one is non-null. -->
    <main class="cc-main" *ngIf="hasChat; else empty">
      <cometchat-message-header [user]="selectedUser" [group]="selectedGroup"></cometchat-message-header>
      <!-- The thread-reply indicator is clickable whether or not you bind (threadRepliesClick);
           unwired it emits into a dead handler (RULES §12 wire-or-hide). This golden path omits the
           thread PANEL (first GROW step), so HIDE the affordance here; add panel + wire when you grow
           into it — references/layout.md. -->
      <cometchat-message-list class="cc-fill" [user]="selectedUser" [group]="selectedGroup"
        [hideReplyInThreadOption]="true"></cometchat-message-list>
      <cometchat-message-composer [user]="selectedUser" [group]="selectedGroup"></cometchat-message-composer>
    </main>
    <ng-template #empty><div class="cc-empty">Select a conversation</div></ng-template>
  </div>
</cometchat-error-boundary>
```

```css
/* chat.component.css — the shell MUST be sized or the list collapses to 0px. `.cc-fill`
   (flex: 1; min-height: 0) is REQUIRED on every kit list (-conversations/-users/-groups/
   -call-logs/-search/-message-list): each resolves an internal height:100% to its own
   overflow-y:auto region and does not size itself. <cometchat-error-boundary> ships NO :host
   rule (verified vs 5.1.0), so size it too. Full rationale: `references/layout.md`. */
cometchat-error-boundary { display: flex; flex-direction: column; flex: 1; min-height: 0; overflow: hidden; }
/* The kit themes its OWN surfaces only — without this your own regions stay browser-white. */
html, body { height: 100%; margin: 0;
  background: var(--cometchat-background-color-01);
  color: var(--cometchat-text-color-primary); }

.cc-shell { display: flex; height: 100dvh; width: 100%; min-height: 0; overflow: hidden; }
.cc-side  { width: 320px; min-height: 0; overflow: hidden; display: flex; flex-direction: column; border-right: 1px solid var(--cometchat-border-color-default); }
.cc-fill  { flex: 1; min-height: 0; overflow: hidden; }
.cc-main  { flex: 1; display: flex; flex-direction: column; min-height: 0; overflow: hidden; }
.cc-empty { flex: 1; display: grid; place-items: center; color: var(--cometchat-text-color-secondary); }
```

`html, body { height: 100%; margin: 0; }` is required — an unprepared ancestor chain collapses the kit. Full sizing rules, thread/search wiring and the mobile one-pane fallback: `references/layout.md`.

## Deep references (load ONLY when the task needs them)
| File | Load when |
| --- | --- |
| `references/lifecycle.md` | init/login ordering, guarded login, `loggedInUser$`, logout, route guards |
| `references/setup-credentials.md` | dashboard steps, environment files, production auth tokens |
| `references/layout.md` | sizing, collapse, thread/search panels, responsive |
| `references/component-props.md` | inputs/outputs beyond the golden path, content projection |
| `references/theming.md` | CSS variables, brand colours, dark mode, following the OS theme |
| `references/anti-patterns.md` | "it compiles but does nothing" failures |
| `references/troubleshooting.md` | symptom → cause → fix |
| `references/dependencies.md` | versions, peers, Angular support matrix |
| `references/docs-map.md` | anything not baked here — component docs + SDK fallback |

## Common pitfalls (top 4 — full list in `references/anti-patterns.md`)
1. **Component missing from `imports: []`** → renders nothing, silently.
2. **Unsized ancestor chain** → the message list collapses to zero height.
3. **No `ngOnDestroy` teardown** → RxJS subscriptions and CometChat listeners leak on every route change.
4. **Async SDK callbacks don't repaint** → messages arrive but the view never updates. Angular v21 is **zoneless by default**, so `NgZone.run()` is a no-op for CD — write to a **signal** or call `ChangeDetectorRef.markForCheck()` (see `lifecycle.md`).

## Verify it works
`ng serve`, then confirm: conversations list renders with data · clicking one opens header+list+composer · **clicking a GROUP conversation works too** (not just 1:1) · sending a message appears immediately · a second browser receives it live · no console errors · nothing collapsed to zero height · **OS set to dark renders dark** (`document.documentElement.getAttribute('data-theme')` is `"dark"`, not `null`) · **`ng build` (PRODUCTION config) succeeds** — see the budget note in Install.

## Explain what you built (REQUIRED close)
Tell the developer: which files changed, where credentials live and that the Auth Key is dev-only, that components must stay in `imports: []`, and what to run next.

**Then state the SCOPE BOUNDARY explicitly — do not leave it implied:**
> *"This is the core chat surface: a conversation list beside the message pane. It does **not** include a users / groups / calls tab selector, a details or thread side panel, search, or voice/video calling — say the word and I'll add any of them."*

Without this the developer cannot tell a deliberate default from an incomplete build.

**Then offer these THREE options as a SELECTABLE choice and WAIT for the pick — never auto-continue (`RULES.md` §19):**

- **① Add another feature** → **check what is already wired FIRST, then suggest only the gap.** Read the code you just emitted, and **ASK** which dashboard-gated items are already on (per-app dashboard state can't be read reliably — never assume off). Suggest 3–4 from the grow-set in `features.angular-v5.json`: voice/video **calls** (`npm-package`) · **push** / **AI** smart replies · starter · summary (`dashboard-toggle`) · **polls · stickers · translation · pin · save** (`dashboard-extension`) · **threads · search · custom message types** (`code-prop`). **Never suggest an `auto` entry** — reactions, mentions, receipts, typing and media are core in v5 and already on; offer to customize instead. Then route to `-features` / `-calls` / `-push`.
- **② Customize theming** → ask whether they have a preset/brand theme (brand colour, light/dark, match an existing design system) or want to talk it through, then wire it (→ `cometchat-angular-v5-customization`).
- **③ Test it manually** → do NOTHING further — hand back so the user runs and checks it themselves. (`cometchat-angular-v5-testing` covers what to mock; `-production` covers hardening before ship.)
