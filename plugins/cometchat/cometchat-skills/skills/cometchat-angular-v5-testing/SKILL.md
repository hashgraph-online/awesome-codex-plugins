---
name: cometchat-angular-v5-testing
description: "Test an Angular app that embeds CometChat — what to mock vs exercise for real, TestBed setup for standalone kit components, avoiding real network in unit tests, and a two-account manual pass for realtime. Triggers: 'write tests for my chat', 'mock cometchat in jest', 'testbed cometchat', 'my tests hang', 'e2e test the chat'."
license: "MIT"
compatibility: "@cometchat/chat-uikit-angular ^5 (5.1.0–5.2.0 verified); Angular 17-21; Jest / Karma / Vitest / Playwright"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat angular testing v5 testbed jest mock e2e playwright"
---

> **Ground truth:** `@cometchat/chat-uikit-angular@5` (5.1.0–5.2.0 verified). **The Angular UI Kit docs have no testing page** — the strategy here is the pack's own, and is labelled as such rather than presented as documented (a tracked DOCS GAP). Any kit symbol a test mocks must still exist in the `angular-v5` catalog, and its real shape comes from the component's `.md` twin via `cometchat-angular-v5-core/references/docs-map.md` — mock the API the kit actually exposes, never one invented to fit the test.

## Companion skills (read first)
- `cometchat-angular-v5-core` — init/login lifecycle, which is what makes tests hang if unmocked.

## Use this skill when
Writing tests for a component that renders kit components, or diagnosing tests that hang or fail on network.

## Decide what you are testing
| Testing | Approach |
| --- | --- |
| **Your** logic — selection, routing, state | Unit test with CometChat **mocked** |
| Kit component internals | Don't. It is a third-party dependency with its own tests |
| Your app's chat flow end-to-end | Playwright against a real dev app, two accounts |
| Realtime delivery | Manual, two browsers. Not automatable cheaply |

The common mistake is unit-testing kit internals. Test the seam: given a click, does your component set the right active chat?

## Mock CometChat in unit tests
Kit components open sockets and call the API at construction. Left real, tests hang, fail offline, and pollute a live app with test data.

```ts
// src/testing/cometchat.mock.ts
export const cometChatUIKitMock = {
  initFromSettings: jest.fn().mockResolvedValue({}),
  login: jest.fn().mockResolvedValue({ getUid: () => 'test-uid' }),
  loginWithAuthToken: jest.fn().mockResolvedValue({ getUid: () => 'test-uid' }),
  logout: jest.fn().mockResolvedValue(undefined),
  getLoggedInUser: jest.fn().mockReturnValue({ getUid: () => 'test-uid' }),
  isInitialized: jest.fn().mockReturnValue(true),
  isCallingEnabled: jest.fn().mockReturnValue(false),
};
```
Point the module at it (Jest):
```ts
jest.mock('@cometchat/chat-uikit-angular', () => ({
  ...jest.requireActual('@cometchat/chat-uikit-angular'),
  CometChatUIKit: cometChatUIKitMock,
}));
```
Keep `requireActual` so real component classes and `ChatStateService` still exist — you want your own wiring exercised, only the network faked.

## TestBed with standalone kit components
They are standalone, so they go in `imports`, exactly as in the app:
```ts
import { TestBed } from '@angular/core/testing';
import { ChatComponent } from './chat.component';

beforeEach(async () => {
  await TestBed.configureTestingModule({ imports: [ChatComponent] }).compileComponents();
});
```
If a test fails with "is not a known element", the component under test is missing it from its own `imports` — a real bug the test just caught, not a test problem.

## Prefer testing ChatStateService over the DOM
Assert state, not kit markup. Kit internals change between releases; your wiring should not.
```ts
it('sets the active group when a group conversation is clicked', () => {
  const fixture = TestBed.createComponent(ChatComponent);
  const cmp = fixture.componentInstance;

  // Mock the SHAPE the kit actually emits: a Conversation whose subject is a Group.
  // Handing open() a bare { getGuid } instead lets a duck-typing bug pass the test
  // while every group chat throws "getUid is not a function" in the browser.
  const group = new CometChat.Group('g1', 'Team', CometChat.GROUP_TYPE.PUBLIC);
  const conversation = { getConversationType: () => 'group', getConversationWith: () => group };

  cmp.open(conversation as unknown as CometChat.Conversation);
  expect(cmp.chatState.getActiveGroup()).toBeTruthy();
  expect(cmp.chatState.getActiveUser()).toBeFalsy();      // the group must NOT land in the user slot
});
```
> **Mock the emitted shape, not the shape your code happens to check.** A mock built backwards from the implementation can only confirm the implementation — including its bugs. `(itemClick)` emits a `Conversation`; a test that passes anything else is not exercising the wiring.

## E2E with Playwright
Use a real dev app and two seeded users. What is worth asserting:
- The conversation list renders rows
- Clicking one opens header + list + composer
- Sending text makes it appear
- **No console errors** — the kit fails quietly, so this catches a lot
- **Nothing collapsed** — assert the message list's height is non-zero; a zero-height pane is the most common silent break

```ts
const box = await page.locator('cometchat-message-list').boundingBox();
expect(box!.height).toBeGreaterThan(100);
```
Seed users and conversations through the REST API in setup, not the UI.

## Not worth automating
Realtime delivery between two clients, calls (needs media permissions and two peers), and push (needs a real device and a backgrounded app). Verify these manually and say so in the test plan rather than writing brittle automation.

## Common pitfalls
1. **Unmocked CometChat in unit tests** → hangs, flakes, offline failures.
2. **Mocking the whole module** without `requireActual` → your own wiring never runs.
3. **Asserting kit DOM internals** → breaks on every kit release.
4. **Tests against a production app** → real users, real data.
5. **No zero-height assertion in E2E** → the most common visual break goes unnoticed.
6. **No teardown in tests** → leaked listeners bleed across specs.

## Verify it works
Unit tests pass offline · no test opens a real socket · a missing `imports` entry fails a test · E2E asserts non-zero height and no console errors · manual checks are documented, not faked.
