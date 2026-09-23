# TypeScript Standards (Tier 1)

## Required
- `strict: true` in tsconfig.json
- `prettier` for formatting
- `eslint` with recommended rules

## Type Safety
- No `any` - use `unknown` + type guards
- No `@ts-ignore` without explanation
- Prefer `interface` for objects, `type` for unions

## Common Issues
| Pattern | Problem | Fix |
|---------|---------|-----|
| `as Type` | Unsafe cast | Type guards or `satisfies` |
| `!` (non-null) | Runtime errors | Proper null checks |
| `== null` | Loose equality | `=== null \|\| === undefined` |
| Implicit `any` | Type safety loss | Enable `noImplicitAny` |

## React (if applicable)
- Functional components only
- `useState` / `useReducer` for state
- `useEffect` with proper deps array
- No inline object/function props (memo issues)

## Testing
- Jest or Vitest
- React Testing Library for components
- MSW for API mocking
