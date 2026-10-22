# Anti-patterns — code that compiles, shows no error, and does not work

## 1. Component missing from `imports: []`  ⭐ most common
```ts
@Component({ standalone: true, imports: [CommonModule], template: '<cometchat-conversations></cometchat-conversations>' })
```
Angular treats the unknown element as plain HTML and renders **nothing**. No error, no warning, blank space.
**Fix:** import the class into that component's `imports` array. Every kit component, in every component that uses it.

## 2. Unsized ancestor chain
The kit fills its container. If any ancestor has no resolved height, the list computes to 0px and you see a blank pane.
**Fix:** `html, body { height: 100%; margin: 0; }`, a `100dvh` shell, and `min-height: 0` on every flex column. See `layout.md`.

## 3. No teardown in `ngOnDestroy`
RxJS subscriptions and CometChat listeners survive the component. Symptoms: memory grows per route change, handlers fire against destroyed views, duplicate messages.
**Fix:** `takeUntil(this.destroy$)` on every subscription and `CometChat.removeMessageListener(id)` in `ngOnDestroy`.

## 4. Async SDK-callback state doesn't repaint
`onTextMessageReceived` fires asynchronously, so assigning to a plain field does not trigger change detection. The message is in memory; the DOM never updates.
**Fix:** Angular v21 is **zoneless by default**, so `NgZone.run()` is a no-op for CD — write to a **signal** (`messages.update(...)`) or call `ChangeDetectorRef.markForCheck()` after the update. (`NgZone.run()` only helps if you've opted back into zones with `provideZoneChangeDetection()`.) Kit components handle this internally — this applies to your own listeners.

## 5. Rendering before `login()` resolves
Components mount with no session and render empty lists with no error, which looks like "the API returned nothing".
**Fix:** init and login must resolve before bootstrap, or gate the chat route. See `lifecycle.md`.

## 6. Concurrent `login()`
Two callers racing throws **"Please wait until the previous login request ends."** A route guard plus a component `ngOnInit` is enough to cause it.
**Fix:** cache the in-flight **promise**, never a boolean. See `lifecycle.md`.

## 7. Using the class name as a selector, or the docs title as either
`<CometChatConversations>` and `<cometchat-conversations-component>` are both wrong. Class `CometChatConversationsComponent`, selector `<cometchat-conversations>`, docs title "Conversations" — three different strings.

## 8. Guessing the bare class name
`CometChatConversations` (no suffix) exists inside the package but is **not exported** — importing it fails to compile. 109 such internal-only names exist. Always use the exported `…Component` form. The AI-assistant exports are the sole exception and carry no suffix.

## 9. Putting credentials in `.env`
Angular does not read `.env`. Values must be in `src/environments/environment.ts` and swapped via `fileReplacements`. A `.env` file is silently ignored, so config appears empty at runtime.

## 10. Shipping the Auth Key to production
The Auth Key can mint a session for **any** user. Production must call `loginWithAuthToken` with a token minted server-side. See `setup-credentials.md`.

## 11. `@import` of the kit stylesheet
`@import '@cometchat/chat-uikit-angular/styles/css-variables.css'` fails the build — the package `exports` map does not expose that path. Register the full `node_modules/...` path in `angular.json` `styles` instead.

## 12. Installing on Angular 22
`npm install` hard-fails with `ERESOLVE` (peer range `>=17.0.0 <22.0.0`). Do not "fix" it with `--force` or `--legacy-peer-deps` — that installs a combination nobody has tested. Scaffold with `@angular/cli@21`.

## 13. Hand-rolling what the kit already renders
Message bubbles, receipts, reaction pickers, typing indicators and attachment previews are rendered by the kit. Rebuilding them by hand means losing realtime updates and every future fix. If an affordance appears not to work, it is nearly always a missing input or an unsized container.
