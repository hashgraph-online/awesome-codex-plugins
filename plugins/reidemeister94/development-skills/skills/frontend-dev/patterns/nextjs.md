# Next.js Patterns & Standards

Next.js-specific patterns. Used alongside [react.md](react.md) for Next.js projects. Referenced by the frontend-dev skill during Research and Implementation phases.

---

## Review Standards

Enforce these during Staff Engineer Review (Phase 4) — **in addition to** React review standards:

- Server Components by default — `"use client"` only when needed (interactivity, hooks, browser APIs)
- Data fetching in Server Components (not `useEffect`)
- Server Actions for mutations (`"use server"`)
- Proper error boundaries (`error.tsx`) and loading states (`loading.tsx`)
- No client-side auth checks only — use middleware + server-side validation
- Caching strategy explicit (revalidate time or `no-store`)

---

## Architecture Patterns

### App Router (Primary — Next.js 14+)

```
app/
├── layout.tsx              # Root layout (required)
├── page.tsx                # Home page
├── loading.tsx             # Loading UI
├── error.tsx               # Error boundary
├── not-found.tsx           # 404 page
├── (auth)/                 # Route group (no URL segment)
│   ├── login/page.tsx
│   └── register/page.tsx
├── dashboard/
│   ├── layout.tsx          # Nested layout
│   ├── page.tsx
│   └── @modal/             # Parallel route
│       └── settings/page.tsx
└── api/
    └── users/
        └── route.ts        # Route Handler
```

**Flow:** Request → Middleware → Layout → Page → Server/Client Components

### Server vs Client Components

```tsx
// Server Component (default) — runs on server only
// Can: fetch data, access backend, use async/await
// Cannot: use hooks, browser APIs, event handlers
async function UserList() {
  const users = await db.user.findMany();
  return <ul>{users.map(u => <li key={u.id}>{u.name}</li>)}</ul>;
}

// Client Component — add "use client" directive
// Can: use hooks, browser APIs, event handlers
// Cannot: directly fetch from DB, use server-only code
"use client";

import { useState } from "react";

function Counter() {
  const [count, setCount] = useState(0);
  return <button onClick={() => setCount(c => c + 1)}>{count}</button>;
}
```

**Rule:** Default to Server Components. Add `"use client"` only when needed.

### Pages Router (Legacy)

```
pages/
├── _app.tsx                # App wrapper
├── _document.tsx           # HTML document
├── index.tsx               # Home page
├── users/
│   ├── index.tsx           # /users
│   └── [id].tsx            # /users/:id
└── api/
    └── users.ts            # API route
```

### Middleware

```tsx
// middleware.ts (root of project)
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  if (!request.cookies.get("session")) {
    return NextResponse.redirect(new URL("/login", request.url));
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*", "/api/protected/:path*"],
};
```

---

## Data Fetching

### Server Components (Preferred)

```tsx
// app/users/page.tsx — Server Component
async function UsersPage() {
  const users = await fetch("https://api.example.com/users", {
    next: { revalidate: 60 },
  }).then(res => res.json());

  return <UserList users={users} />;
}
```

### Server Actions (Mutations)

```tsx
// app/actions.ts
"use server";

import { revalidatePath } from "next/cache";

export async function createUser(formData: FormData) {
  const name = formData.get("name") as string;
  const email = formData.get("email") as string;

  await db.user.create({ data: { name, email } });
  revalidatePath("/users");
}
```

### Route Handlers

```tsx
// app/api/users/route.ts
import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
  const users = await db.user.findMany();
  return NextResponse.json(users);
}

export async function POST(request: NextRequest) {
  const body = await request.json();
  const user = await db.user.create({ data: body });
  return NextResponse.json(user, { status: 201 });
}
```

### Caching Strategies

```tsx
fetch(url);                                    // Cached indefinitely
fetch(url, { next: { revalidate: 60 } });      // Revalidate every 60s
fetch(url, { cache: "no-store" });             // Always fresh
fetch(url, { next: { tags: ["users"] } });     // Tag-based

import { revalidateTag, revalidatePath } from "next/cache";
revalidateTag("users");
revalidatePath("/users");
```

---

## State Management

```
Server State (preferred):     Fetched in Server Components, cached with fetch()
Client State (when needed):   UI state (modals, tabs, forms), real-time updates
URL State:                    useSearchParams + router.push for filters/pagination
```

### URL State with searchParams

```tsx
"use client";

import { useSearchParams, useRouter, usePathname } from "next/navigation";

function Filters() {
  const searchParams = useSearchParams();
  const pathname = usePathname();
  const router = useRouter();

  const updateFilter = (key: string, value: string) => {
    const params = new URLSearchParams(searchParams);
    params.set(key, value);
    router.push(`${pathname}?${params.toString()}`);
  };

  return (
    <select
      value={searchParams.get("sort") ?? "name"}
      onChange={e => updateFilter("sort", e.target.value)}
    >
      <option value="name">Name</option>
      <option value="date">Date</option>
    </select>
  );
}
```

---

## Error Handling

### Error Boundaries

```tsx
// app/dashboard/error.tsx
"use client";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div>
      <h2>Something went wrong!</h2>
      <button onClick={reset}>Try again</button>
    </div>
  );
}
```

### Not Found

```tsx
// app/users/[id]/page.tsx
import { notFound } from "next/navigation";

async function UserPage({ params }: { params: { id: string } }) {
  const user = await getUser(params.id);
  if (!user) notFound();
  return <UserProfile user={user} />;
}
```

---

## Testing Server Components

```tsx
import { UsersPage } from "@/app/users/page";

jest.mock("@/lib/db", () => ({
  user: {
    findMany: jest.fn().mockResolvedValue([{ id: "1", name: "Test" }]),
  },
}));

describe("UsersPage", () => {
  it("renders users", async () => {
    const page = await UsersPage();
    render(page);
    expect(screen.getByText("Test")).toBeInTheDocument();
  });
});
```

---

## Code Quality

```json
// .eslintrc.json
{
  "extends": ["next/core-web-vitals", "prettier"],
  "rules": {
    "@typescript-eslint/no-unused-vars": "error",
    "import/order": ["error", { "alphabetize": { "order": "asc" } }]
  }
}
```

---

## Quick Reference

| Need | Do This |
|------|---------|
| Fetch data | Server Component with fetch() or DB call |
| Handle form submission | Server Action with `"use server"` |
| Add interactivity | `"use client"` + hooks |
| Share client state | React Context |
| URL-based state | `useSearchParams` + `router.push` |
| Handle errors | `error.tsx` boundary |
| Loading states | `loading.tsx` or `Suspense` |

## What NOT to Do

| Anti-Pattern | Instead |
|--------------|---------|
| `"use client"` everywhere | Default to Server Components |
| `useEffect` for data fetching | Fetch in Server Components |
| `useState` for server data | Server Components + caching |
| Client-side auth checks only | Middleware + server-side validation |
| Hardcoded URLs | Environment variables |
