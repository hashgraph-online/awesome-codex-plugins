---
name: cometchat-angular-v5-troubleshooting
description: "Diagnose a broken CometChat Angular integration — blank panes, silent no-render, empty lists, events that never fire, UI that does not update, memory leaks, install failures. Symptom to cause to fix. Triggers: 'chat not showing', 'blank screen', 'nothing renders', 'click handler not firing', 'messages not updating', 'ERESOLVE', 'cometchat not working'."
license: "MIT"
compatibility: "@cometchat/chat-uikit-angular ^5 (5.1.0–5.2.0 verified); Angular 17-21"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat angular troubleshooting v5 debug blank-screen silent-failure diagnostics"
---

> **Ground truth:** `@cometchat/chat-uikit-angular@5` (5.1.0–5.2.0 verified). Symptoms map to causes verified against the installed kit and the live `{DOCS_BASE}/ui-kit/angular/troubleshooting.md` page (base + paths in `cometchat-angular-v5-core/references/docs-map.md`). Every `CometChat*` symbol named here exists in the `angular-v5` catalog; a fix that requires a symbol not in the catalog is a bug in this file, not a missing export.

## Companion skills (read first)
- `cometchat-angular-v5-core` — `references/anti-patterns.md` and `references/troubleshooting.md` carry the same table in more depth.

## Use this skill when
Something is wrong and the error message is unhelpful or absent.

## Start here — Angular fails SILENTLY
Four of the five most common CometChat-Angular faults produce **no error at all**. Do not wait for a stack trace.

Run these four checks in order before anything else:

**1. Is the component in `imports: []`?**
Missing → Angular treats `<cometchat-conversations>` as unknown HTML and renders nothing. No error, no warning, blank space. This is the single most common cause.

**2. Does the container have height?**
```css
html, body { height: 100%; margin: 0; }
```
Plus a `100dvh` shell and `min-height: 0` on every flex column. An unsized ancestor collapses the list to 0px — markup correct, nothing visible.

**3. Did `login()` resolve before render?**
Lists render empty with no error when there is no session. Check `CometChatUIKit.getLoggedInUser()` is non-null at the moment the component mounts.

**4. Is the binding name real?**
`(ccConversationClicked)` never fires — the real output is `(itemClick)`. Angular does not warn about unknown outputs. Verified names are in `cometchat-angular-v5-components`.

## Symptom → cause → fix
| Symptom | Cause | Fix |
| --- | --- | --- |
| Icons missing/blank across the kit | `assets` not registered in `angular.json` | add the `src/lib/assets` glob → `output: assets`; the most commonly missed step |
| Scrolling the list scrolls the WHOLE page | shell/columns missing `overflow: hidden` | `min-height: 0` lets it shrink; `overflow: hidden` keeps the scroll inside the pane — both are required |
| List doesn't scroll at all — bottom items unreachable | `<cometchat-conversations>`/`-users`/`-groups`/`-call-logs`/`-search`/`-message-list` has no `flex: 1; min-height: 0` of its OWN | add the `.cc-fill` class to the tag itself, not just its ancestors — the list resolves an internal `height: 100%` and does not size itself |
| Whole surface runs past the viewport / clipped, on a **routed** page only | `<cometchat-error-boundary>` is the template root and ships **no** `:host` sizing, so a `height: 100%` shell under it resolves against nothing | add `cometchat-error-boundary { display: flex; flex-direction: column; flex: 1; min-height: 0; overflow: hidden; }` — it is styled by ELEMENT, not by a class. Symptom hides when the shell uses `100dvh` (viewport-relative), appears the moment it becomes `100%` under a routed outlet |
| `<cometchat-call-logs>` shows "OOPS! Looks like something went wrong" | KIT BUG (5.1.0), not your code: `CallLogsService` builds `new CometChatUIKitCalls.CallLogRequestBuilder()` without awaiting the lazy calls-SDK load, so the accessor is still `null`. Zero network requests are made — it fails before fetching, and Retry does not recover | No host-side fix. Do not hand-roll around it; report it. Note `(error)` will NOT surface it — call-logs has no `error` output (it takes an `onError` INPUT) |
| Blank space where chat should be | component not in `imports: []` | add the class to that component's `imports` |
| Blank pane, markup correct | ancestor has no height | `html, body { height: 100% }` + `100dvh` + `min-height: 0` |
| Lists render but always empty | rendered before `login()` resolved | init → login before bootstrap, or gate the route |
| Click handler never fires | wrong output name | use the verified name; there is no `cc` prefix |
| Selected row never highlights | `activeConversation` not bound | bind it to the same state as the message pane |
| Messages arrive, UI does not update | async SDK callback doesn't repaint (Angular 21 is zoneless by default, so `NgZone.run()` won't help) | write to a signal or call `ChangeDetectorRef.markForCheck()` after the update (core `lifecycle.md`) |
| Memory grows per route change | no teardown | `takeUntil(destroy$)` + `removeMessageListener(id)` in `ngOnDestroy` |
| Duplicate messages after navigating | listener registered twice, never removed | register with a stable id; remove on destroy |
| "Please wait until the previous login request ends." | concurrent `login()` | cache the in-flight promise |
| `npm install` fails `ERESOLVE` | project on Angular 22 | peer range is `<22.0.0`; use `@angular/cli@21` |
| Build error: path not exported by package | `@import` of the kit stylesheet | register the full `node_modules/...` path in `angular.json` |
| Config empty at runtime | credentials in `.env` | Angular reads `environment.ts`, not `.env` |
| Import will not compile | bare class name used | use the exported `…Component` form |
| Header shows one chat, messages another | `[user]`/`[group]` mismatch | pass the same subject to header, list and composer |
| Reply button does nothing | no thread surface rendered | wire a thread panel or hide the affordance |
| Feature missing, no error | dashboard extension off | enable it for the app the credentials point at |
| Call buttons render as empty zero-size elements | `uiKit.callsSDK` missing from `initFromSettings` | add `uiKit: { callsSDK: {} }`; installing the package does not enable calling. Check `CometChatUIKit.isCallingEnabled()` |
| Lists show "OOPS!" on first load and Retry does nothing | first fetch raced login; ConversationsService caches the failure | bootstrap AFTER login resolves; give the user a retry that remounts the component |
| Calls never ring | listener not at app root, or calls SDK absent | mount `<cometchat-incoming-call>` at root; install the calls SDK |
| Calls fail on a LAN IP | `getUserMedia` needs a secure context | use HTTPS or localhost |
| `window is not defined` | SSR running browser code | guard with `isPlatformBrowser` |
| Dropdown clipped | ancestor `overflow: hidden` or `transform` | remove it from the chain |
| Layout jumps when data loads | box sizes to content | pin the height so loading and loaded share one box |

## Where the docs contradict this skill
One entry above still disagrees with `{DOCS_BASE}/ui-kit/angular/overview.md`, and this skill is right because it is verified against the published package:
- **Angular 22** — the docs list it as supported; the peer range excludes it and `npm install` hard-fails. Do not follow the docs here, and never `--force` past it.

Also verify against the installed package:
- **`@cometchat/cards-angular`** — required since 5.1.0. (The overview's peer list now lists it — corrected upstream, verified against cometchat/docs, 2026-09-09.)

If a fix in this table seems to contradict a guide, check the installed package before changing course.

## When the table does not cover it
1. **Confirm the symbol is real.** The exported class name, not the docs title.
2. **Fetch the component's docs page** (`core/references/docs-map.md`) and compare every input you pass.
3. **Check the browser console for a CometChat error code** before assuming it is a UI problem.
4. **Raise the log level**: `CometChatUIKit.setLogLevel(...)`.
5. **Reduce to the golden path** from `core`. If that works, the fault is in your composition; if it does not, it is setup.

## Verify it works
A fix is done when the symptom is gone **and** you can say which of the four silent-failure causes it was. If you cannot name the cause, the fix is a coincidence and it will come back.

Re-check after any fix: chat renders with real data · clicking a conversation opens it · sending a message appears immediately · a second browser receives it live · no console errors · nothing collapsed to zero height.

## What NOT to do
- Do not `--force` or `--legacy-peer-deps` past an `ERESOLVE` — you install an untested combination and the failure moves somewhere harder to find.
- Do not add `!important` to fight the kit's styles — a token is not applying because the stylesheet is not registered.
- Do not rebuild a component by hand because an affordance looks broken. It is nearly always a missing input or an unsized container.
