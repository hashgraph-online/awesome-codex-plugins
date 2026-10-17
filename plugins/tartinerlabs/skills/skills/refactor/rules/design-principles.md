---
title: Design Principles
impact: HIGH
tags: solid, single-responsibility, god-object, interfaces, coupling
---

Design-level checks. These apply to any language.

## Single responsibility (HIGH)

**Rule**: A module should have one reason to change. Split files that handle unrelated concerns, or that have grown into a catch-all — more than ~10 exports is a strong signal, but mixed responsibilities matter more than the count. A `utils.ts` accumulating formatters, validators, parsers, and mailers is the canonical case; so is a `user-service.ts` doing auth, profile, and notifications.

### Incorrect

```ts
// user-service.ts — handles auth, profile, and notifications
export function login(credentials: Credentials) { /* ... */ }
export function logout(userId: string) { /* ... */ }
export function updateProfile(userId: string, data: ProfileData) { /* ... */ }
export function getProfile(userId: string) { /* ... */ }
export function sendWelcomeEmail(userId: string) { /* ... */ }
export function sendPasswordReset(email: string) { /* ... */ }
```

### Correct

```ts
// auth-service.ts
export function login(credentials: Credentials) { /* ... */ }
export function logout(userId: string) { /* ... */ }

// profile-service.ts
export function updateProfile(userId: string, data: ProfileData) { /* ... */ }
export function getProfile(userId: string) { /* ... */ }

// notification-service.ts
export function sendWelcomeEmail(userId: string) { /* ... */ }
export function sendPasswordReset(email: string) { /* ... */ }
```

## Interface segregation (HIGH)

**Rule**: Large interfaces force implementors to handle methods they don't need. Split into focused interfaces. More than ~7 methods is worth a look.

### Incorrect

```ts
interface Repository {
  find(id: string): Promise<Entity>;
  findAll(): Promise<Entity[]>;
  create(data: CreateDTO): Promise<Entity>;
  update(id: string, data: UpdateDTO): Promise<Entity>;
  delete(id: string): Promise<void>;
  export(format: string): Promise<Buffer>;
  sendNotification(id: string): Promise<void>;
}
```

### Correct

```ts
interface ReadRepository {
  find(id: string): Promise<Entity>;
  findAll(): Promise<Entity[]>;
}

interface WriteRepository {
  create(data: CreateDTO): Promise<Entity>;
  update(id: string, data: UpdateDTO): Promise<Entity>;
  delete(id: string): Promise<void>;
}
```

## Tight coupling (HIGH)

**Rule**: Modules that import many siblings or reach across layers indicate coupling issues. Introduce interfaces or reorganise boundaries. Importing from more than ~5 siblings in the same layer is worth a look.

### Incorrect

```ts
// features/dashboard/stats.ts — reaches into many sibling features
import { getUser } from "../auth/get-user";
import { getOrders } from "../orders/get-orders";
import { getProducts } from "../products/get-products";
import { getPayments } from "../payments/get-payments";
import { getShipments } from "../shipping/get-shipments";
import { getReviews } from "../reviews/get-reviews";
```

### Correct

```ts
// features/dashboard/stats.ts — depends on an abstraction
import type { DashboardDataSource } from "./types";

export function buildStats(data: DashboardDataSource) {
  // works with the data it receives, not fetching it directly
}
```
