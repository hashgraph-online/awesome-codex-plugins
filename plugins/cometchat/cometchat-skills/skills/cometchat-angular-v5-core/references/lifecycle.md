# Lifecycle — init → login → render, the Angular way

## The invariant
`init()` must RESOLVE before `login()`, and `login()` before any kit component renders. Out of order, components mount with no session and render empty lists with no error.

## Where init goes
Angular has no React-style root effect. Two correct placements:

**A. Before `bootstrapApplication` (simplest, recommended).** See the core SKILL.md recipe — init and login resolve, then the app boots. Nothing can render early because the app has not booted yet.

**B. `provideAppInitializer` (when you need DI during init).**
```ts
// src/app/app.config.ts
import { ApplicationConfig, provideAppInitializer, inject } from '@angular/core';
import { CometChatUIKit } from '@cometchat/chat-uikit-angular';
import { environment } from '../environments/environment';
import { ensureLoggedIn } from './cometchat-session';   // the guarded login below

export const appConfig: ApplicationConfig = {
  providers: [
    provideAppInitializer(() => {
      const { appId, region, authKey } = environment.cometchat;
      // initFromSettings — NOT the classic builder init — so integrationSource
      // ="ai-agent" is persisted for telemetry attribution and the Calls SDK
      // inherits the same source.
      return CometChatUIKit.initFromSettings({
        appId, region,
        credentials: { authKey },
        chatSDK: { presenceSubscription: { type: 'ALL_USERS' } },
      }).then(() => ensureLoggedIn('cometchat-uid-1'));
    }),
  ],
};
```
Angular waits for the returned promise before rendering the first component. On Angular 17-18 use the older `{ provide: APP_INITIALIZER, useFactory, multi: true }` form — same semantics.

`initFromSettings` returns `Promise<InitResult>`. `CometChatUIKit.isInitialized()` is a cheap synchronous check.

## The docs show `init(builder)` — that is CORRECT for them, and wrong for us
`{DOCS_BASE}/ui-kit/angular/integration.md` and `quickstart.md` initialise with the classic builder:
the classic `UIKitSettingsBuilder` chain (`setAppId` / `setRegion` / `setAuthKey`) passed to the UI Kit's builder-style init.

That is **not stale documentation** — it is the right recipe for its reader, and it must not be "fixed".

The SDK ships two integration sources and the init path selects between them:

| Caller | Path | Recorded as |
| --- | --- | --- |
| A developer following the docs by hand | the builder-style `init` | `manual` |
| An agent following this pack | `CometChatUIKit.initFromSettings({ … })` | `ai-agent` |

Verified in the shipped SDK: `INTEGRATION_SOURCE = { AI_AGENT: "ai-agent", MANUAL: "manual" }`, with the builder-style init storing `MANUAL` and `initFromSettings()` storing `AI_AGENT`.

So the split is deliberate on both sides. **Use `initFromSettings` here** — a static gate enforces it — and do **not** raise the docs' builder recipe as a docs bug or propose changing it. Converting the public docs to `initFromSettings` would tag every hand-built integration as agent-built and destroy the distinction the field exists to measure.

## Guarded login — the one that bites
A second `login()` while the first is still in flight throws **"Please wait until the previous login request ends."** Sequential calls are fine (the second returns the cached user); concurrent ones are not. Route guards, resolvers and a component `ngOnInit` firing together will do this.

Cache the **promise**, never a boolean flipped before the await:
```ts
// src/app/cometchat-session.ts
import { CometChatUIKit } from '@cometchat/chat-uikit-angular';

// Cache the PROMISE, once per page load. Concurrent callers await the same one;
// later callers get the resolved value. A second sequential login() returns the
// cached user, so calling it once per load is safe even with a stored session.
let session: Promise<unknown> | null = null;

export function ensureLoggedIn(uid: string) {
  if (!session) {
    session = CometChatUIKit.login(uid).catch((e) => { session = null; throw e; });
  }
  return session;
}
```

> ⚠️ **Do NOT short-circuit on `CometChatUIKit.getLoggedInUser()`.** It is tempting:
> ```ts
> const existing = CometChatUIKit.getLoggedInUser();   // ← don't
> if (existing) return Promise.resolve(existing);
> ```
> `initFromSettings` hydrates the kit's own `_loggedInUser` from storage when a session exists, so this returns a user **before `login()` has run in this page**. You then skip `login()` entirely and the kit's post-login wiring never executes. Worse, the kit's view and the SDK's can disagree — `CometChatUIKit.getLoggedInUser()` returning a user does **not** guarantee `CometChat.getLoggedinUser()` is populated or that requests will authorise. Trust the promise, not the cached flag.

## Dev-only: `ensureDevUser` — create-if-missing, then log in

`login(uid)` authenticates a user that **must already exist**; it does not create one. `cometchat-uid-1` is the docs sample, **not a guarantee about this app** — on an app whose sample users were never seeded or have been cleaned up, login fails with a user-not-found and the screen stays blank with no obvious cause.

You cannot pre-check existence: `CometChat.getUser()` needs a session, and in dev you hold only the Auth Key, not the REST key. Probing `uid-1..5` would mean up to five failed login attempts. So **create-if-missing, then log in** — one deterministic call that is valid on any app, fresh or customised:

```ts
// src/app/cometchat-session.ts — continued: add below ensureLoggedIn() (merge the imports)
import { CometChat } from '@cometchat/chat-sdk-javascript';        // for CometChat.User
import { CometChatUIKit } from '@cometchat/chat-uikit-angular';

// createUser uses the Auth Key configured in init — verified vs installed 5.1.0:
//   static createUser(user: CometChat.User): Promise<CometChat.User>
export async function ensureDevUser(uid = 'cometchat-uid-1', name = 'Demo User') {
  try {
    const u = new CometChat.User(uid);
    u.setName(name);
    await CometChatUIKit.createUser(u);
  } catch {
    // ERR_UID_ALREADY_EXISTS is EXPECTED — the user is there. Fall through to login.
  }
  return ensureLoggedIn(uid);                                       // now guaranteed to succeed
}
```

**DEV ONLY.** It depends on the Auth Key being in the browser. Production mints a per-user auth token server-side and calls `loginWithAuthToken` — see `setup-credentials.md`. When the developer names a real UID, log in as that instead; only fall back to this when no UID is known.

## Readiness gap — `login()` resolving is not "ready to fetch"
`login()` can resolve slightly before the session can authorise requests. A list that mounts in that window fires its first fetch, gets an auth error, and — for `ConversationsService` — **caches the failure**: the built-in Retry button does not re-attempt, so a transient startup error becomes a permanent "OOPS!" until a page reload.

Defend against it:
- **Bootstrap after login resolves** (core's `main.ts` recipe) rather than rendering a chat route that races it. Nothing mounts until the session exists.
- If you must gate a route instead, resolve `ensureLoggedIn()` in the guard and let the route render only after it settles.
- Handle `(error)` on lists and give the user a real retry that **remounts** the component, since the built-in one may not recover.
- Do not "fix" this with a `setTimeout` — it hides a race rather than ordering it.
Production uses a server-minted token instead: `CometChatUIKit.loginWithAuthToken(token)`. Never ship the Auth Key to the browser — see `setup-credentials.md`.

## Reading the session — `loggedInUser$`
The kit exposes an RxJS Observable. This is the Angular-idiomatic way to react to login/logout; React has no equivalent.
```ts
import { Component, OnDestroy, inject, ChangeDetectorRef } from '@angular/core';
import { CometChatUIKit } from '@cometchat/chat-uikit-angular';
import { Subject, takeUntil } from 'rxjs';

@Component({ selector: 'app-shell', standalone: true, template: '' })
export class ShellComponent implements OnDestroy {
  private destroy$ = new Subject<void>();
  user: unknown = null;

  constructor() {
    CometChatUIKit.loggedInUser$
      .pipe(takeUntil(this.destroy$))
      .subscribe((u) => { this.user = u; });
  }

  ngOnDestroy() { this.destroy$.next(); this.destroy$.complete(); }
}
```
`CometChatUIKit.getLoggedInUser()` is the synchronous one-shot equivalent.

## Teardown — required, not optional
Every subscription and every CometChat SDK listener must be released in `ngOnDestroy`, or the app leaks on each route change and stale handlers fire against destroyed views.
```ts
import { CometChat } from '@cometchat/chat-sdk-javascript';

class ExampleComponent {
  private listenerId = 'chat-example';
  private destroy$ = { next: () => {}, complete: () => {} };

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
    CometChat.removeMessageListener(this.listenerId);   // same id used to register
  }
}
```
Register listeners with a stable id you keep on the component instance.

## Async SDK callbacks — messages arrive but the UI does not update
CometChat SDK callbacks fire asynchronously (and, with zones, outside Angular's zone), so state you set inside them does not repaint on its own. Symptom: the message exists in memory, the DOM never changes.

**Angular v21 is ZONELESS by default** — no provider needed: `ng new` (21.2.x) adds no `zone.js` and no `provideZoneChangeDetection()`, and does NOT add `provideZonelessChangeDetection()` or `OnPush` either (components stay `Default` CD) — so **`NgZone.run()` does NOT trigger change detection**; there's no zone to re-enter. Use a **signal** (the cleanest zoneless pattern — writing it schedules CD) or call **`ChangeDetectorRef.markForCheck()`** after mutating plain state. Both work whether the app is zoneless or (legacy) zone-based:
```ts
import { CometChat } from '@cometchat/chat-sdk-javascript';
import { signal } from '@angular/core';

class ExampleComponent {
  private listenerId = 'chat-example';
  // signal: writing to it schedules change detection under the zoneless default
  messages = signal<unknown[]>([]);

  constructor() {
    CometChat.addMessageListener(this.listenerId, {
      onTextMessageReceived: (msg: unknown) => {
        this.messages.update((prev) => [...prev, msg]);   // repaints — no NgZone needed
      },
    });
  }
}
```
Prefer a signal (template reads `messages()`); if you keep a plain field instead, inject `ChangeDetectorRef` and call `this.cdr.markForCheck()` after the mutation. Only if you have deliberately opted back into zones with `provideZoneChangeDetection()` is `NgZone.run()` the right remedy. The kit's own components handle this internally — you only need this for your own SDK listeners.

## Logout — cleanup only runs if the SDK call resolves
```ts
import { CometChatUIKit } from '@cometchat/chat-uikit-angular';

export async function signOut(navigateToLogin: () => void) {
  try {
    await CometChatUIKit.logout();
  } catch {
    // swallow — still treat the user as signed out locally, see below
  } finally {
    navigateToLogin();   // unconditional — do not gate this on the promise resolving
  }
}
```
Verified in the installed 5.1.0 bundle: `CometChatUIKit.logout()` only runs its local cleanup (`detachListeners`, clearing the cached user, `loggedInUser$` → `null`) **inside** `CometChat.logout()`'s `.then()`. A rejection (reproduced: `USER_NOT_LOGED_IN` — *"an authToken is need to use the userLogout end-point"*) skips cleanup entirely — `getLoggedInUser()`/`loggedInUser$` keep reporting the old session, and `initFromSettings` rehydrates that same stale user on the next reload (§ above), so sign-out silently doesn't stick. Undocumented in the pack and the official docs.

Never drive a login-screen redirect off `loggedInUser$` emitting `null` after calling logout — on a rejection it may not. `catch` the call and navigate/clear your own app-level "signed in" state unconditionally in a `finally`; treat the kit's local cache as advisory, not authoritative, for this one transition.
