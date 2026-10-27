# Troubleshooting — symptom → cause → fix

| Symptom | Cause | Fix |
| --- | --- | --- |
| Element renders nothing, no error | class not in `imports: []` | add it to that component's `imports` array |
| `npm install` fails with `ERESOLVE` | project is on Angular 22 | scaffold with `@angular/cli@21`; peer range is `<22.0.0` |
| Build error: path not exported by package | `@import` of the kit stylesheet | register the full `node_modules/...` path in `angular.json` `styles` |
| Blank pane, correct markup | ancestor has no height | `html, body { height: 100% }` + `100dvh` shell + `min-height: 0` |
| Lists render but always empty | rendering before `login()` resolved | init → login must resolve before bootstrap |
| "Please wait until the previous login request ends." | concurrent `login()` | cache the in-flight promise (`lifecycle.md`) |
| Config appears empty at runtime | credentials put in `.env` | Angular reads `environment.ts`, not `.env` |
| Messages arrive but UI does not update | Async SDK callback doesn't repaint (Angular v21 is zoneless by default, so `NgZone.run()` won't help) | write to a **signal** or call `ChangeDetectorRef.markForCheck()` after the update (`lifecycle.md`) |
| Memory grows on each route change | no teardown | `takeUntil(destroy$)` + `removeMessageListener(id)` in `ngOnDestroy` |
| Import fails to compile | used the bare class name | use the exported `…Component` form (AI-assistant exports are the exception) |
| Header shows one chat, messages another | `[user]`/`[group]` mismatch across components | pass the same subject to header, list and composer |
| Clicking a conversation does not highlight it | `activeConversation` not bound | bind it to the same state that drives the message pane |
| Reply button does nothing | thread surface not rendered | wire a thread panel or hide the affordance |
| Dropdown or menu clipped | ancestor `overflow: hidden` or `transform` | remove it from the chain, or move the overlay root |
| Composer off-screen on mobile | `100vh` instead of `100dvh` | use `100dvh` |
| Layout jumps when messages load | box sizes to content | pin the height so loading and loaded share one box |
| Calls never ring | calls SDK missing or calling not enabled | install `@cometchat/calls-sdk-javascript@^5`; check `isCallingEnabled()` |
| Feature absent with no error | dashboard extension not enabled | enable it in the dashboard; most extensions need no client code |

## When none of these fit
1. Confirm the symbol exists — the exported name, not the docs title.
2. Fetch the component's docs page (`docs-map.md`) and compare inputs against what you passed.
3. Check the browser console for a CometChat error code before assuming it is a UI problem.
