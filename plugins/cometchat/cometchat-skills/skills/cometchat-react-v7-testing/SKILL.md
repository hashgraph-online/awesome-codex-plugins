---
name: cometchat-react-v7-testing
description: "Test a React app that embeds CometChat v7 — what to mock vs exercise for real, rendering kit components under a test provider, waiting out the async init→login gate, and a lean E2E smoke. Triggers: 'test my cometchat react app', 'mock cometchat in jest/vitest', 'unit test chat component', 'playwright test for chat', 'how do I test cometchat'."
license: "MIT"
compatibility: "@cometchat/chat-uikit-react ^7 (7.1.x–7.2.x verified); React 18–19; Vitest / Jest / React Testing Library / Playwright"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat react v7 testing vitest jest playwright mock rtl"
---

> **Ground truth:** `@cometchat/chat-uikit-react@7`. Component/method names come from `cometchat-react-v7-core` + its catalog; signatures are FETCHED via `cometchat-react-v7-core/references/docs-map.md`. **The UI Kit docs have no dedicated testing page** — this is the pack's own guidance (tracked DOCS GAP). Never assert against kit-internal DOM classes; they are not a public contract.

## Companion skills (read first)
- `cometchat-react-v7-core` — the init→login→render lifecycle these tests exercise.

## Use this skill when
Adding tests around a CometChat integration, or a "how do I test this" question. NOT part of a normal build — only when tests are explicitly asked for (`RULES.md` → Verification scope).

## Decide what you are testing
You are testing **your** code, not CometChat's kit. Three layers:
- **Your logic** (token fetch, UID mapping, routing, state) → unit-test in isolation, **mock the SDK**.
- **Your wiring** (does the surface mount after init+login, are the right props passed) → render under a test provider with the SDK mocked.
- **The real round-trip** (send → receive) → a thin E2E against a test app, not a unit test.

Do not unit-test that `CometChatMessageList` renders messages — that is the kit's own test surface.

## Mock the SDK in unit tests
Mock the two entry modules so nothing hits the network and no real login is attempted:
```tsx
vi.mock("@cometchat/chat-sdk-javascript", () => ({ CometChat: { getLoggedinUser: vi.fn().mockResolvedValue(null) } }));
vi.mock("@cometchat/chat-uikit-react", async (orig) => ({
  ...(await orig()),
  CometChatUIKit: { initFromSettings: vi.fn().mockResolvedValue(null), getLoggedInUser: vi.fn().mockReturnValue(null), login: vi.fn().mockResolvedValue({ getUid: () => "u1" }), loginWithAuthToken: vi.fn().mockResolvedValue({ getUid: () => "u1" }), logout: vi.fn().mockResolvedValue(undefined) },
}));
```
(Jest: swap `vi` for `jest`.) Now assert your own token-fetch and error handling without a backend.

## Render the surface under test
The kit surface mounts only **after** init+login resolve. Tests must await that gate, not assert synchronously:
```tsx
render(<App />);
expect(await screen.findByText(/sign in|loading|chats/i)).toBeInTheDocument();
```
Prefer `findBy*` (async) over `getBy*`; a synchronous query runs before the init promise settles and fails intermittently. Wrap the surface in `CometChatErrorBoundary` in the app so a thrown error surfaces as a testable fallback, not an unhandled rejection.

## E2E smoke (Playwright)
One high-value path against a **real test app** (seeded users, dev Auth Key in a test-only env): load the app, sign in, assert the conversation list renders with real height and a message can be sent. Assert on **your** visible text/roles and the presence of the mounted surface — not on kit BEM classes. Keep it to the happy path plus one auth-failure path; the kit's internals are already tested upstream.

## Not worth automating
Kit component internals, exhaustive prop matrices, live calls/push (device-dependent), and pixel snapshots of kit UI (they churn across minor kit versions). Spend the budget on your token flow, UID mapping, and the init-gate wiring.

## Common pitfalls
1. **Synchronous assertions before init resolves** — flaky; use `findBy*`/`waitFor`.
2. **Asserting on kit DOM classes** — they change across versions; assert your own markup + roles.
3. **A real login in unit tests** — mock `CometChatUIKit`; never ship a test Auth Key to prod env files.
4. **StrictMode double-invoke** — mocks must be idempotent (return the same resolved user), mirroring the app's in-flight guard.

## Verify it works
Unit tests pass with the SDK mocked (no network) · the surface test awaits the init gate and finds the mounted UI · the E2E smoke signs in and renders conversations against a test app · no test asserts a kit-internal class.
