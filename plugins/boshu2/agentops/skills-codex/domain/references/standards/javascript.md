# JavaScript Standards (Tier 1)

## Required
- ES2020 or newer (Node 18+ runtime).
- `prettier` for formatting; `eslint` with the recommended ruleset.
- `package.json` declares `"type": "module"` for new packages.

## Style
- `const` by default; `let` only when reassignment is required; never `var`.
- Arrow functions for callbacks; named `function` for top-level declarations.
- Strict equality (`===` / `!==`) — no loose equality.
- One module per file; default export only when the module is the unit.

## Async
- `async`/`await` over raw `.then()` chains.
- Always `await` or explicitly handle returned Promises.
- Reject errors with `Error` instances, never raw strings.

## Error Handling
- No empty `catch {}` blocks; either re-throw or log with context.
- Use `try`/`catch` only at boundaries (HTTP, IO, IPC); let errors bubble inside pure logic.
- Validate external input before use; trust internal callers.

## Common Issues
| Pattern | Problem | Fix |
|---------|---------|-----|
| `==`, `!=` | Coerces types silently | Use `===`, `!==` |
| `parseInt(x)` | Defaults to base 10 only since ES5 but easy to miss | Pass radix: `parseInt(x, 10)` |
| `for...in` on arrays | Iterates inherited enumerable props | Use `for...of` or `.forEach` |
| Mutating shared state | Hard-to-trace bugs | Spread/`Object.assign` for copies; Array methods that return new arrays |
| Float arithmetic | `0.1 + 0.2 !== 0.3` | Round to integer cents before compare |

## Testing
- Vitest or Jest; `node --test` is acceptable for small libraries.
- Use `describe` / `it` blocks; one logical assertion per `it`.
- Mock external services; don't mock the unit under test.
- Snapshot tests only for stable serialized output, never for UI-rich strings.

## Security
- Never use `eval()`, `Function()`, or `new Function()` with untrusted input.
- Sanitize HTML before injecting into the DOM; prefer `textContent` over `innerHTML`.
- Use `crypto.randomUUID()` / `crypto.getRandomValues()`, not `Math.random()`, for tokens.
- Pin dependency versions in `package-lock.json` or `pnpm-lock.yaml`; audit with `npm audit` before release.
