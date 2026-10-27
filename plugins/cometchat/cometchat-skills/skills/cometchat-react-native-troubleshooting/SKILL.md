---
name: cometchat-react-native-troubleshooting
description: "Diagnose a broken CometChat React Native integration — blank chat screen, gestures not responding, Android build failures, calls not ringing, notifications not arriving, custom UI not showing. Symptom to root cause to fix. Triggers: CometChat React Native not working, blank chat screen RN, gestures not working chat, android build fails CometChat, calls not ringing RN, my custom view isn't showing."
license: "MIT"
compatibility: "React Native >=0.77; @cometchat/chat-uikit-react-native ^5.4.0"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "chat cometchat react-native troubleshooting diagnostics errors debugging"
---

> **Ground truth:** `@cometchat/chat-uikit-react-native@5` + catalog `rn-v5.json`.
> Docs: `/ui-kit/react-native/troubleshooting`.

## Companion skills (read first)
- `cometchat-react-native-core` — install, provider chain, init→login→render. Assumed, not repeated here.

## Use this skill when
- anything is broken and the error does not say why — which on React Native is most of the time

## Prerequisites & install
None.

## Read this first: RN failures usually name the wrong thing
Three properties make React Native bugs hard to read, and all three appear below:
- **native modules fail at MOUNT, not at build** — so the app starts, then a screen explodes
- **the error names a peer dependency**, not CometChat — `gesture-handler`, `svg`, `video`
- **an unknown prop is silently ignored** — no error, nothing renders

So "it says nothing about CometChat" is not evidence the problem is elsewhere.

## Symptom → root cause → fix

### Blank chat screen, no error
| Cause | Fix |
|---|---|
| rendering before `login()` resolved | gate render on a `loggedIn` flag; `init` → `login` → render |
| `initFromSettings()` failed | you **cannot** catch it — `CometChatUIKit.initFromSettings()` swallows init errors (its rejection handler is a no-op), so `await`/`.catch()` see nothing. Instead assert on the NEXT step: `await login(...)` (which DOES reject) or check `await CometChatUIKit.getLoggedInUser()`; a bad appId/region surfaces there as an auth failure |
| an ancestor is not `flex: 1` | every ancestor `flex: 1`; a scrolling column also needs `minHeight: 0` |

### The UI renders but nothing responds to touch
**`GestureHandlerRootView` is missing, or is not outermost, or lacks `flex: 1`.**
No error is thrown. On bare RN also confirm `import 'react-native-gesture-handler'` is the **first
line of `index.js`** — wrong ordering there often works in debug and crashes in release.

### `NativeModule … null` / "cannot read property of null" on a chat screen
A native peer is missing or unlinked. Install the full peer list (`core`), then `pod install` (bare)
or a fresh development build (Expo). **Metro reload does not pick up native changes — rebuild.**

### Android build fails, error never mentions CometChat
`@react-native-async-storage/async-storage` must be `^2.1.2` — the Chat SDK requires it at load and the Calls SDK peer-requires 2.x. Unpinned resolves to 3.x, which fails `npm install @cometchat/calls-sdk-react-native@5` with ERESOLVE. Check: `npm ls @react-native-async-storage/async-storage`.

### Expo: works in Expo Go until a chat screen opens
Expo Go **cannot** load custom native modules. Use a development build (`npx expo run:ios`). There is
no workaround.

### My custom view does not appear
**Slot props are PascalCase on RN** — `ItemView`, not `itemView`. React's casing is silently ignored:
no error, nothing renders. Same class of bug as a typo'd prop name.

### Two headers stacked on the message screen
The navigator's header plus `CometChatMessageHeader`. Set `headerShown: false` on that screen.

### The composer is hidden when the keyboard opens
A fixed height somewhere in the ancestor chain, or the message screen is nested **inside** the tab
navigator so the tab bar overlaps it. Put the message screen on the stack **above** the tabs.

### Sending a message throws on iOS (React Native >= 0.87)
React Native **0.87 removed `InteractionManager` from core**, and `CometChatMessageComposer` (kit
through 5.5.0) still calls `InteractionManager.runAfterInteractions()` in four **iOS-only** branches
of its send path. Tapping send throws and the message never leaves the device. Android is unaffected;
so is RN <= 0.86, where the export is deprecated but still resolves — which is why the same code
sends fine on an older app and dies on a fresh template.

| Where | What you see |
|---|---|
| dev build | `Uncaught Error: InteractionManager has been removed from react-native core. Please refactor long tasks into smaller ones, and use 'requestIdleCallback' instead.` in `CometChatMessageComposer` -> `sendTextMessage` |
| release build | the same line reads `undefined` -> `TypeError: Cannot read property 'runAfterInteractions' of undefined` |
| CI | **nothing** — it typechecks, bundles and builds on both platforms; only a person tapping send sees it |

Until the kit drops the call, restore a minimal implementation **before the kit loads** — the first
import in `index.js`:

```js
// interactionManagerCompat.js — delete when the kit stops calling InteractionManager.
const ReactNative = require('react-native');

const missing = () => {
  try {
    return !ReactNative.InteractionManager;
  } catch {
    return true; // RN >= 0.87 in __DEV__: the getter throws.
  }
};

if (missing()) {
  Object.defineProperty(ReactNative, 'InteractionManager', {
    configurable: true,
    get: () => ({
      runAfterInteractions: (task) => {
        const run = () => (typeof task === 'function' ? task() : task && task.gen && task.gen());
        let settle;
        const ran = new Promise((resolve) => { settle = resolve; });
        const timer = setTimeout(() => { run(); settle(); }, 0);   // resolve AFTER the task runs
        return {
          then: (onResolve, onReject) => ran.then(onResolve, onReject),
          done: (onDone) => { ran.then(onDone); },
          cancel: () => clearTimeout(timer),
        };
      },
      createInteractionHandle: () => 0,
      clearInteractionHandle: () => {},
      setDeadline: () => {},
      addListener: () => ({ remove: () => {} }),
    }),
  });
}
```

### `ReferenceError: Property '<name>' doesn't exist` right after a `try`/`catch`
Hermes loses a `catch (error)` binding that is only read inside a closure created in the same block —
`catch (error) { setLogs((prev) => [describe(error), ...prev]) }` throws the first time the catch
runs, while the identical code with the value read first works. It typechecks and bundles either way.
Read the caught value into a local, then use the local inside the closure.

### Calls do not ring
| Cause | Fix |
|---|---|
| `CometChatIncomingCall` mounted inside one screen | mount it **once above the navigator** |
| calls SDK installed but pods not run | `pod install` / rebuild — otherwise it crashes at first call |
| camera/mic permission not declared | add them (`calls`), then rebuild |
| testing on a simulator | simulators capture no camera or mic — use real devices |

### Notifications never arrive
Registered before `login()` resolved · wrong platform constant · token rotated and never re-registered
· missing `google-services.json` / `GoogleService-Info.plist` · iOS simulator. See `push`.

### A feature was "enabled" but nothing changed
| Cause | Fix |
|---|---|
| dashboard toggled, code prop not set | AI features need **both**; the props default to off |
| it is already core in v5 | reactions and mentions are on by default — nothing to enable |
| the kit auto-renders it | `auto_rendered_ui` features need no client code |

### A symbol does not compile
Check `catalogs/rn-v5.json`. Likely a React name: `UIKitSettingsBuilder`, `login(uid)`,
`onItemClick`, `CometChatErrorBoundary`, `CometChatDetails`, `CometChatMessagePlugin`. See the
React→RN table in `core/references/docs-map.md`.

## First moves, in order
1. Does `init` resolve, and does `login` resolve after it? Log both.
2. Is `GestureHandlerRootView` outermost with `flex: 1`?
3. Is every ancestor of the kit component `flex: 1`?
4. Did you **rebuild** after the last native change, rather than reload?
5. Does every emitted symbol exist in the catalog?

## Verify it works
- The symptom is reproducibly gone on a device, not only in a simulator.
- `npm run verify:fences:rn-v5` is green.
- If the fix was a native change, a **clean** build still works.

## `tsc --noEmit` reports errors inside the UI Kit, not your app

The kit's `package.json` has `main: "src/index"` and ships **uncompiled `.tsx`** — there is no `lib/` and
no `types` field. So `tsc` follows the import into the kit's own source and reports ~30 errors under
`node_modules/@cometchat/chat-uikit-react-native/src/*.tsx` while your own code is clean.

`skipLibCheck` does **not** help (it only skips `.d.ts`, and there are none here), and
`exclude: ["node_modules"]` does not either (TypeScript still follows imports). Metro strips types, so the
bundle and the app are fine — this only bites a CI typecheck. Scope the check to your own sources:

```bash
tsc --noEmit -p tsconfig.json 2>&1 | grep -v 'node_modules/@cometchat/'
```
