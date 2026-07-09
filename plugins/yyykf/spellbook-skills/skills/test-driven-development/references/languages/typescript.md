# TDD in TypeScript / JavaScript

**Load this reference when:** doing TDD in TypeScript or JavaScript. The core skill is language-agnostic; this file adds only TS/JS framework choices, idioms, anti-patterns, and tooling. Generic mock pitfalls live in [../testing-anti-patterns.md](../testing-anti-patterns.md) and are not repeated here.

## Test framework & runner

**Default: [Vitest](https://vitest.dev/) (4.x — npm `latest` as of 2026-06; 5.0 is still beta, so verify dist-tags before pinning a fresh project).** It is the modern default because it reuses your Vite/`tsconfig` pipeline (ESM + TS run natively, no separate `ts-jest`/Babel transform), it is Jest-API-compatible (`describe`/`it`/`expect`/`vi`), and its watch mode is fast. Pick **[Jest](https://jestjs.io/)** instead only for an existing Jest codebase, React Native, or a non-Vite toolchain — the idioms below port 1:1 (`vi.*` ↔ `jest.*`).

Runner has no TS opinion: Vitest/Jest find files by config (`*.test.ts`, `*.spec.ts`). Test files compile through the same `tsconfig` as source, so type errors in a test fail the run.

```bash
npx vitest run                      # whole suite, single run (CI mode, no watch)
npx vitest run src/calc.test.ts     # one file
npx vitest run -t "rejects negative" # one test by name (regex on full describe+it name)
npx vitest                          # watch mode (local TDD loop)
```

For an agent loop, add `--reporter=dot` (one char per test) or `--silent` (drops `console.log` noise) — full detail still prints on failure; keep verbose reporters for humans debugging.

Minimal failing test (RED) — note it imports a function that does not exist yet, so it fails to compile, which *is* the red:

```typescript
// calc.test.ts
import { describe, it, expect } from 'vitest';
import { add } from './calc'; // ./calc.ts not written yet -> RED

describe('add', () => {
  it('sums two numbers', () => {
    expect(add(2, 3)).toBe(5);
  });
});
```

## Idioms & conventions

- **Structure:** `describe` groups, `it`/`test` cases. Co-locate `foo.test.ts` next to `foo.ts`.
- **Matchers:** `toBe` (Object.is / primitives), `toEqual` (deep, ignores `undefined` props), `toStrictEqual` (deep + type + `undefined`), `toThrow`, `resolves`/`rejects` for promises.
- **Parametrized tests** — prefer `it.each` over a hand-rolled loop so each row reports as its own case:
  ```typescript
  it.each([
    [0, 0, 0],
    [2, 3, 5],
    [-1, 1, 0],
  ])('add(%i, %i) -> %i', (a, b, expected) => {
    expect(add(a, b)).toBe(expected);
  });
  ```
- **Async:** make the test `async` and `await`, or return the promise. For rejections use `await expect(fn()).rejects.toThrow()` — do not wrap in try/catch (a thrown-but-not-caught path can pass silently).
- **Setup/teardown:** `beforeEach`/`afterEach`/`beforeAll`/`afterAll`. Reset mocks between tests with `vi.restoreAllMocks()` (or `restoreMocks: true` in config).
- **Spies/mocks, smallest tool first:** `vi.fn()` for a standalone stub; `vi.spyOn(obj, 'method')` to wrap one real method (and assert on calls); `vi.mock('module')` to replace a whole module — reach for it only when DI and `spyOn` can't isolate the boundary (see hoisting pitfall below).
- **Guard async tests:** when correctness depends on a callback/`catch` firing, add `expect.assertions(n)` so a path that never reaches the `expect` fails loudly instead of passing as a no-op.

## TS/JS-specific anti-patterns

**❌ Asserting on `data-testid` / CSS classes / internal React state.**
Why wrong: these are implementation details — a refactor (renaming a class, restructuring state) breaks tests without any user-visible change, and `getByTestId` does not exercise the accessibility tree real users (and screen readers) rely on.
✅ Query the way a user perceives the UI: `getByRole('button', { name: /save/i })`, `getByLabelText`, `getByText`. `getByTestId` is the documented last resort. *Source: [Testing Library — query priority](https://testing-library.com/docs/queries/about/#priority); [Kent C. Dodds, "Common mistakes with RTL"](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library).*

**❌ `vi.mock`/`jest.mock` factory referencing an outer `const`.**
Why wrong: `vi.mock`/`jest.mock` calls are **hoisted to the top of the file**, above your imports and variable declarations, so a factory that closes over a module-scoped variable throws `Cannot access '...' before initialization`.
✅ Define such variables inside [`vi.hoisted`](https://vitest.dev/api/vi.html#vi-hoisted) and reference its return value, or inline the value in the factory:
```typescript
const { sendMock } = vi.hoisted(() => ({ sendMock: vi.fn() }));
vi.mock('./mailer', () => ({ send: sendMock }));
```
*Source: [Vitest — vi.mock / vi.hoisted](https://vitest.dev/api/vi.html#vi-mock); [Vitest mocking guide](https://vitest.dev/guide/mocking).*

**❌ Mocking the wrong module path / mocking modules you own.**
Why wrong: `vi.mock('./utils')` must match the *specifier the code under test imports* (a re-export or alias path won't intercept), and mocking your own code means you test the mock, not the unit. Module mocks also leak across files if not reset.
✅ Mock only the I/O boundary (network, fs, clock); for code you own, prefer **dependency injection** — pass the collaborator as a parameter so the test supplies a real or fake without `vi.mock` at all. *Source: [Vitest mocking guide](https://vitest.dev/guide/mocking).*

**❌ Real timers for debounce / polling / `setTimeout` code.**
Why wrong: the test either sleeps for real (slow, flaky) or races the timer.
✅ `vi.useFakeTimers()` (replaces `setTimeout`/`setInterval`/`Date`/`performance.now`), drive with `vi.advanceTimersByTimeAsync(ms)` / `vi.runAllTimersAsync()`, restore in `afterEach` with `vi.useRealTimers()`. *Source: [Vitest — fake timers](https://vitest.dev/guide/mocking/timers).*

**❌ Hand-rolled `fetch`/`axios` mocks (`global.fetch = vi.fn()`).**
Why wrong: you re-implement HTTP semantics (status, headers, JSON body) per test, and the assertion proves your stub matches your stub, not that the code handles real responses.
✅ Use **[MSW](https://mswjs.io/) (v2)**: intercept at the network layer so the code runs real `fetch`/`axios`/React Query. *Source: [MSW docs](https://mswjs.io/docs/).*
```typescript
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';
const server = setupServer(
  http.get('/api/user/:id', () => HttpResponse.json({ id: '1', name: 'Ada' })),
);
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

**❌ Giant auto-updated snapshots as a substitute for assertions.**
Why wrong: a 200-line `toMatchSnapshot` against a separate `.snap` file gets blindly `--update`d on every change, so it asserts "nothing changed" rather than "behavior is correct," and diffs get rubber-stamped in review.
✅ Keep snapshots tiny and prefer [`toMatchInlineSnapshot`](https://vitest.dev/guide/snapshot.html) (lives next to the test, gets reviewed); pair with explicit `expect(...).toBe(...)` on the values that matter. *Source: [Vitest snapshot guide](https://vitest.dev/guide/snapshot.html); [Jest snapshot docs](https://jestjs.io/docs/snapshot-testing).*

**❌ Asserting on TS types at runtime (`expect(typeof x).toBe('string')`) to "test types."**
Why wrong: types are erased at runtime, so this checks JS values, not the type contract; a wrong generic still compiles and the test still passes.
✅ Write **type-level tests** with [`expectTypeOf`](https://vitest.dev/api/expect-typeof) / `assertType` run under `vitest --typecheck.enabled`; keep runtime tests for behavior. *Source: [Vitest — testing types](https://vitest.dev/guide/testing-types).*

## Tooling notes

- **Coverage:** Vitest `--coverage` (provider `v8`, the default, or `istanbul`); Jest ships Istanbul-based coverage built in. Treat coverage as a gap-finder, not a target.
- **Network mocking:** [MSW](https://mswjs.io/) v2 (`http`/`HttpResponse`, `setupServer` for Node, `setupWorker` for the browser; requires Node 18+). Same handlers work in tests, Storybook, and dev.
- **Fake timers:** `vi.useFakeTimers()` / `jest.useFakeTimers()` for time, debounce, polling, and `Date.now`.
- **Type-level tests:** `expectTypeOf().toEqualTypeOf<T>()` / `assertType<T>(x)` (Vitest, run with `--typecheck.enabled`), or [`tsd`](https://github.com/tsdjs/tsd) / `@ts-expect-error` for library `.d.ts` contracts.
- **Property-based:** [fast-check](https://fast-check.dev/) — `fc.assert(fc.property(fc.integer(), n => ...))` generates many inputs and *shrinks* a failure to a minimal counterexample. Runner-agnostic (works inside Vitest/Jest `it`).

## Quick reference

| Need | Vitest | Jest |
|---|---|---|
| Run suite once | `vitest run` | `jest` (or `jest --ci`) |
| Run one test by name | `vitest run -t "name"` | `jest -t "name"` |
| Stub fn / spy | `vi.fn()` / `vi.spyOn()` | `jest.fn()` / `jest.spyOn()` |
| Mock module | `vi.mock()` + `vi.hoisted()` | `jest.mock()` |
| Fake time | `vi.useFakeTimers()` | `jest.useFakeTimers()` |
| Reset mocks | `vi.restoreAllMocks()` | `jest.restoreAllMocks()` |
| Parametrize | `it.each` | `it.each` |
| Type tests | `expectTypeOf` + `--typecheck.enabled` | `tsd` |
| HTTP mocking | MSW (`setupServer`) | MSW (`setupServer`) |
| Property-based | fast-check | fast-check |
| User-facing queries | `@testing-library/*` `getByRole` | `@testing-library/*` `getByRole` |
