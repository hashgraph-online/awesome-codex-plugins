# Browser JavaScript TDD Patterns

## Smoke Test First

Before testing real behavior, prove the test runner can fail and pass:

```javascript
describe("test runner", () => {
  it("runs specs", () => {
    expect(true).toBe(true);
  });
});
```

Delete or leave only if the project convention keeps runner smoke tests.

## DOM Fixture Pattern

Build the smallest HTML needed by the behavior:

```javascript
beforeEach(() => {
  document.body.innerHTML = `
    <form>
      <input id="id_text" />
      <button disabled>Add</button>
    </form>
  `;
});

afterEach(() => {
  document.body.innerHTML = "";
});
```

Avoid copying full templates into JavaScript tests. The fixture should show the contract the script needs.

## Initialization Function

Prefer an explicit initializer:

```javascript
export function initializeListForm(root = document) {
  const input = root.querySelector("[data-list-input]");
  const button = root.querySelector("[data-list-submit]");
  if (!input || !button) return;
  input.addEventListener("input", () => {
    button.disabled = input.value.trim() === "";
  });
}
```

Then the page entrypoint can call it on load, and tests can call it directly.

## Selector Refactoring

Use semantic hooks for JavaScript-owned behavior:

- `data-testid` for tests only when acceptable in the project.
- `data-js` or behavior-specific data attributes for runtime hooks.
- Avoid binding behavior to CSS classes whose purpose is styling.

Refactor selectors under green tests.

## JS Unit Test Versus E2E

| Risk | Best Proof |
| --- | --- |
| Function output | JS unit test |
| DOM mutation | JS DOM test |
| Script loaded on page | One browser integration test |
| Server response plus JS behavior | Browser/end-to-end test |
| CSS framework interaction | Browser test only if user-visible behavior matters |

## CI Integration

When adding browser JavaScript tests to CI:

- Install Node dependencies deterministically.
- Run the JS test command as a separate step or clearly named part of the test job.
- Save browser artifacts if failures are hard to diagnose.
- Keep unit-level JS tests faster than Selenium tests.
