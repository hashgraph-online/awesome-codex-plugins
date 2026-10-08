---
title: TypeScript/JS Idioms
impact: HIGH
tags: type-assertions, optional-chaining, nullish-coalescing, barrel-files, enum, async-await
---

Applies **only to TS/JS files** (`.ts`/`.tsx`/`.js`/`.jsx`/`.mts`/`.cts`).

## Type assertions (HIGH)

**Rule**: Replace `as` type assertions with proper type guards or narrowing — an assertion silences the compiler without proving anything. Assertions in test files, where the shape is fixed by the fixture, are fine.

### Incorrect

```ts
const user = data as User;
```

### Correct

```ts
function isUser(data: unknown): data is User {
  return typeof data === "object" && data !== null && "id" in data;
}

if (isUser(data)) {
  // `data` is narrowed to User here
}
```

## Nullish coalescing (HIGH)

**Rule**: Use `??` rather than `||` when the fallback should apply only to `null`/`undefined` — `config.port || 3000` discards a legitimate `0`, and `name || "Anon"` discards a legitimate `""`. Where every falsy value genuinely should take the fallback, `||` is correct.

## Barrel re-exports (HIGH)

**Rule**: Avoid barrel `index.ts` files that re-export from other modules — they hurt tree-shaking, slow TypeScript and bundlers, and risk circular dependencies. Import directly from the source module. See `naming-format/rules/index-files.md` for the full treatment.

### Incorrect

```ts
// components/index.ts — re-exports from many modules
export * from "./button";
export * from "./input";

// consumer
import { Button } from "./components";
```

### Correct

```ts
import { Button } from "./components/button";
```

### Exception

Package entry points, where a deliberate public API boundary is the point:

```ts
// packages/ui/index.ts — intentional public API
export { Button } from "./components/button";
export { Input } from "./components/input";
```

## Optional chaining (MEDIUM)

**Rule**: Replace nested `&&` null-checks with optional chaining — `user && user.address && user.address.city` becomes `user?.address?.city`.

## Union types over string enums (MEDIUM)

**Rule**: Prefer a union type when the values are string literals: `type Status = "active" | "inactive"` over a `Status` enum. Enums earn their keep when you need a runtime object to iterate or reverse-map.

## Async/await over .then() chains (MEDIUM)

**Rule**: Prefer async/await over `.then()` chains — the control flow reads top to bottom and error handling sits in one place. Leave a chain alone when it is a deliberate pipeline of small transforms, or when its `.catch()` placement scopes rejection to one step in a way the rewrite would widen.

### Incorrect

```ts
function fetchUser(id: string) {
  return fetch(`/api/users/${id}`)
    .then((res) => res.json())
    .then((data) => transformUser(data))
    .catch((err) => handleError(err));
}
```

### Correct

```ts
async function fetchUser(id: string) {
  try {
    const res = await fetch(`/api/users/${id}`);
    const data = await res.json();
    return transformUser(data);
  } catch (err) {
    handleError(err);
  }
}
```
