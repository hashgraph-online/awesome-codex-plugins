---
title: General Patterns
impact: HIGH
tags: dead-code, nesting, long-functions, duplication, magic-values, boolean-params
---

Language-neutral refactoring patterns. Each applies to any codebase.

## Dead code (HIGH)

**Rule**: Remove unused variables, unreachable branches, and commented-out code. Version control is the history — commented-out code is noise that goes stale silently.

## Deep nesting (HIGH)

**Rule**: Flatten logic beyond 3 levels of indentation using early returns and guard clauses.

### Incorrect

```ts
function processOrder(order: Order) {
  if (order) {
    if (order.items.length > 0) {
      if (order.status === "pending") {
        if (order.total > 0) {
          return submitOrder(order);
        }
      }
    }
  }
  return null;
}
```

### Correct

```ts
function processOrder(order: Order) {
  if (!order) return null;
  if (order.items.length === 0) return null;
  if (order.status !== "pending") return null;
  if (order.total <= 0) return null;

  return submitOrder(order);
}
```

## Long functions (HIGH)

**Rule**: Functions exceeding ~40 lines likely do too many things. Extract cohesive blocks into named functions.

### Incorrect

```ts
function handleSubmit(data: FormData) {
  // 15 lines of validation...
  // 10 lines of transformation...
  // 15 lines of API call + error handling...
}
```

### Correct

```ts
function handleSubmit(data: FormData) {
  const errors = validateForm(data);
  if (errors.length > 0) return { errors };

  const payload = transformFormData(data);
  return submitToApi(payload);
}
```

## Duplication (HIGH)

**Rule**: Extract repeated logic into a shared function when the same pattern appears 3+ times. Below that, duplication is often cheaper than the wrong abstraction.

### Incorrect

```ts
// handler-a.ts, handler-b.ts and handler-c.ts each contain:
const user = await db.user.findUnique({ where: { id } });
if (!user) throw new NotFoundError("User not found");
if (!user.isActive) throw new ForbiddenError("User is inactive");
```

### Correct

```ts
// get-active-user.ts
async function getActiveUser(id: string) {
  const user = await db.user.findUnique({ where: { id } });
  if (!user) throw new NotFoundError("User not found");
  if (!user.isActive) throw new ForbiddenError("User is inactive");
  return user;
}

// handler-a.ts
const user = await getActiveUser(id);
```

## Magic values (MEDIUM)

**Rule**: Replace hardcoded numbers and strings with named constants when the value carries meaning or repeats. A literal used once and obvious in context (`array[0]`, `retries + 1`) needs no name.

### Incorrect

```ts
if (retries > 3) throw new Error("Failed");
setTimeout(callback, 86400000);
```

### Correct

```ts
const MAX_RETRIES = 3;
const ONE_DAY_MS = 24 * 60 * 60 * 1000;

if (retries > MAX_RETRIES) throw new Error("Failed");
setTimeout(callback, ONE_DAY_MS);
```

## Boolean parameters (MEDIUM)

**Rule**: Functions with boolean flags often hide two distinct behaviours. Prefer splitting or using an options object — at the call site, `renderList(items, true)` says nothing about what `true` means.

### Incorrect

```ts
renderList(items, true);
```

### Correct

```ts
// Option 1: options object
renderList(items, { numbered: true });

// Option 2: separate functions when behaviour diverges significantly
renderNumberedList(items);
renderBulletList(items);
```
