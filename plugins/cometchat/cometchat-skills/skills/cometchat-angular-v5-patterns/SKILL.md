---
name: cometchat-angular-v5-patterns
description: "Angular project-shape glue for CometChat — Angular CLI vs Nx, standalone vs NgModule, environment file wiring, SSR/Angular Universal, lazy routes, and RxJS/signals state patterns. Triggers: 'add cometchat to my nx workspace', 'ngmodule not standalone', 'angular universal ssr', 'lazy load the chat route', 'window is not defined'."
license: "MIT"
compatibility: "@cometchat/chat-uikit-angular ^5 (5.1.0–5.2.0 verified); Angular 17-21; CLI or Nx"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat angular patterns v5 nx ssr universal ngmodule standalone lazy rxjs signals"
---

> **Ground truth:** this skill is Angular PROJECT-SHAPE glue — CLI vs Nx, standalone vs NgModule, `environment.ts`, SSR, lazy routes. CometChat API surface belongs to `cometchat-angular-v5-core`; fetch any symbol via `cometchat-angular-v5-core/references/docs-map.md`. Where the Angular UI Kit docs genuinely do not cover a shape (SSR / Angular Universal), this file says so explicitly and marks the guidance as the pack's own — absence from the guide is never silently presented as documented.

## Companion skills (read first)
- `cometchat-angular-v5-core` — install, credentials, `init→login→render`. Assumed.
- `cometchat-angular-v5-placement` — routing a chat page.

## Use this skill when
The blocker is the **project shape**, not CometChat: a monorepo, NgModules, SSR, or where config lives.

## Detect the shape first
| Signal | Shape | Deltas |
| --- | --- | --- |
| `nx.json` present | **Nx workspace** | env files, project-level `styles`, path aliases |
| `angular.json` + `src/main.ts` | **Angular CLI** | the default; core's recipe applies as-is |
| `app.module.ts` present | **NgModule** app | components go in `imports:` of the module |
| `server.ts` / `@angular/ssr` | **SSR / Universal** | browser-only guards, see below |

## NgModule instead of standalone
The kit's components are standalone, which means an NgModule app imports them into the module's `imports` array — the same array, a different file:
```ts
// app.module.ts
import { NgModule } from '@angular/core';
import { CometChatConversationsComponent, CometChatMessageListComponent } from '@cometchat/chat-uikit-angular';
import { ChatComponent } from './chat/chat.component';   // YOUR (non-standalone) component

@NgModule({
  declarations: [ChatComponent],
  imports: [CometChatConversationsComponent, CometChatMessageListComponent],
})
export class AppModule {}
```
Do not add them to `declarations` — they are not yours to declare, and Angular will error. Init moves from `main.ts` into an `APP_INITIALIZER` provider on the module.

## Nx workspaces
Three things move:
- **Environment files** live under the app project, e.g. `apps/<app>/src/environments/environment.ts`. `fileReplacements` go in that project's `project.json`, not a root `angular.json`.
- **The kit stylesheet** is registered in the app project's build `styles` array with a workspace-root-relative path: `node_modules/@cometchat/chat-uikit-angular/styles/css-variables.css`.
- **Shared wrapper libs** may re-export the kit's components; a lib that re-exports must also list them in its own `imports`, or consumers get the silent no-render.

Nx does not change the CometChat API at all — only where config lives.

## SSR / Angular Universal
The kit is a browser client. The SDK touches `window`, `localStorage` and WebSockets, none of which exist on the server.

```ts
import { Component, inject, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { CometChatUIKit } from '@cometchat/chat-uikit-angular';
import { environment } from '../environments/environment';

@Component({ selector: 'app-root', standalone: true, template: '<router-outlet />' })
export class AppComponent {
  constructor() {
    if (isPlatformBrowser(inject(PLATFORM_ID))) {
      const { appId, region, authKey } = environment.cometchat;
      // init only in the browser — on the server this throws "window is not defined"
      CometChatUIKit.initFromSettings({
        appId, region,
        credentials: { authKey },
        chatSDK: { presenceSubscription: { type: 'ALL_USERS' } },
      });
    }
  }
}
```
Rules:
- Guard **every** init/login call with `isPlatformBrowser`.
- Render chat components client-side only (`@defer` on hydration, or an `*ngIf` on a browser flag). Server-rendering them produces markup that immediately mismatches.
- `ThemeService` is already SSR-safe — it writes `data-theme` through the `DOCUMENT` token rather than touching `document` directly.
- Do not attempt to prerender a chat route; there is nothing meaningful to prerender.

> **Not in the docs.** The Angular UI Kit docs do not cover SSR / Angular Universal. The guards above are derived from what the SDK touches (`window`, `localStorage`, WebSockets) and are the pack's own guidance — absence from the guide is not a signal that they are unnecessary.

## Lazy-loading the chat route
```ts
{ path: 'chat', loadComponent: () => import('./chat/chat.component').then(m => m.ChatComponent) }
```
Lazy loading the route is fine and recommended — the kit is large. Init still happens once at bootstrap, **not** in the lazy chunk, or the first navigation pays for it and a second navigation re-runs it.

## State — signals or RxJS, one of them
`ChatStateService` exposes both (`activeUser` signal, `activeUser$` observable). Pick one style per component and stay in it; mixing produces two update paths for the same value.

- Signals in templates: no subscription, no teardown, no `async` pipe.
- Observables when composing with other streams: always `takeUntil(destroy$)` in `ngOnDestroy`.

Never mirror either into your own field — see `placement`'s "two sources of truth" pitfall.

## Common pitfalls
1. **Kit components in `declarations`** → Angular error; they belong in `imports`.
2. **Unguarded init under SSR** → `window is not defined` at build or first request.
3. **Init inside a lazy chunk** → runs late, or twice.
4. **Nx: env/styles edited at the workspace root** → silently no effect; they belong to the app project.
5. **Signals and observables for the same value** → two update paths, drifting UI.

## Verify it works
`ng build` (and `ng build --ssr` where applicable) passes · chat renders in the browser · no `window is not defined` on the server · navigating to the lazy route once initialises once · config resolves in every configuration you build.
