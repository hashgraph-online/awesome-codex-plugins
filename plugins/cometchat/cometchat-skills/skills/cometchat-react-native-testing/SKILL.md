---
name: cometchat-react-native-testing
description: "Test a CometChat React Native integration — mock the SDK for Jest unit tests, assert init-before-render ordering and no-Auth-Key-in-source, and use Detox for the flows only a device can prove. Triggers: test CometChat React Native, mock CometChat SDK jest, detox CometChat, unit test chat screen RN, CI tests for chat."
license: "MIT"
compatibility: "React Native >=0.77; Jest; @testing-library/react-native; Detox (e2e)"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "chat cometchat react-native testing jest detox mocking ci"
---

> **Ground truth:** `catalogs/rn-v5.json` + `catalogs/rn-sdk-v4.json`.
> **Build the feature; do NOT test it unless asked.** Use this skill only when the developer asks for
> tests. Never add a test framework, e2e suite or CI to a project that did not request one.

## Companion skills (read first)
- `cometchat-react-native-core` — install, provider chain, init→login→render. Assumed, not repeated here.

## Use this skill when
- "write tests for the chat screen" · "mock CometChat in Jest" · "add Detox coverage for chat"

## Prerequisites & install
React Native ships Jest. Add the renderer:

```bash
npm install --save-dev @testing-library/react-native
```

## Mock the SDK — never let a unit test hit the network
CometChat opens a websocket and needs real credentials. Mock at the module boundary:

```js
jest.mock("@cometchat/chat-sdk-react-native", () => ({
  CometChat: {
    init: jest.fn().mockResolvedValue(true),
    login: jest.fn().mockResolvedValue({ getUid: () => "test-uid" }),
    logout: jest.fn().mockResolvedValue(true),
    AppSettings: { SUBSCRIPTION_TYPE_ALL_USERS: "ALL_USERS" },
  },
}));
```

The UI Kit also pulls native modules, so mock the peers your test path touches —
`react-native-gesture-handler`, `react-native-svg`, `react-native-video`,
`@react-native-async-storage/async-storage`. Without them the failure is a NativeModule error that
never mentions CometChat: the same confusing shape as a missing install.

## What is worth asserting

**Ordering** — the invariant most likely to regress: `init` resolves before `login`, and no chat
component renders until login resolves.

**No Auth Key in source** — a cheap grep test that stops a shipped secret ever landing:

```js
it("has no auth key in source", () => {
  const src = require("fs").readFileSync("src/config.ts", "utf8");
  expect(src).not.toMatch(/authKey\s*:\s*["'][A-Za-z0-9]{20,}/);
});
```

**Wiring, not rendering** — that `onItemPress` navigates, that `onBack` returns, that an opened
surface can be closed. Unwired affordances are the defect class worth catching.

Do **not** assert on kit internals — bubble markup, class names, child order. Those change between
minors, so the test breaks with nothing actually wrong.

## Detox for what only a device proves

| Flow | Why it cannot be a unit test |
|---|---|
| composer survives the keyboard | needs a real soft keyboard |
| hardware back navigates | needs the OS back gesture |
| gestures respond | proves `GestureHandlerRootView` is wired |
| release-build startup | catches the gesture-handler import-order crash |

**Calls and push are outside Detox too** — they need real hardware, real permissions and a second
device. Record them as manual device checks rather than pretending they are automated.

## CI
Jest with mocks runs anywhere. Detox needs a simulator — heavier, but feasible. Neither can verify
calls or push, so a green CI run is not evidence that either works.

## Common pitfalls
1. **Unmocked native peers** — confusing NativeModule errors.
2. **Asserting kit internals** — breaks on minor upgrades.
3. **Real credentials in tests** — network flakes and leaked keys.
4. **Claiming push/calls coverage** from a simulator run.
5. **Adding tests nobody asked for.**

## Verify it works
- Tests pass with no network access.
- No real credentials anywhere in the test tree.
- `npm run verify:fences:rn-v5` is green.
