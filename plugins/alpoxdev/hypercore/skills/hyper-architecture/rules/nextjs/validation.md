# Validation and Readback

> Completion checks for Next.js architecture work.

## Project Work Validation

Run checks appropriate to the touched surfaces:

```bash
# Project and router mode
rg -n '"next"' package.json
find . -maxdepth 3 \( -path './app' -o -path './src/app' -o -path './pages' -o -path './src/pages' \)

# App Router special-file conflicts and private folders
find app src/app -maxdepth 5 -type f \( -name 'page.tsx' -o -name 'route.ts' -o -name 'layout.tsx' -o -name 'loading.tsx' -o -name 'error.tsx' \) 2>/dev/null

# Server/Client boundary and secret import checks
rg -n "^['\"]use client['\"]|server-only|client-only|cookies\(|headers\(|process\.env|NEXT_PUBLIC_" app src/app src/components src/lib src/services 2>/dev/null

# Cache, mutation freshness, and route handler checks
rg -n "cacheComponents|partialPrefetching|use cache|cacheTag|cacheLife|io\(|connection\(|navigation\(|prefetch\(|ensureStatic|instant|updateTag|revalidateTag|revalidatePath|refresh\(|redirect\(" next.config.* app src/app src/lib src/services 2>/dev/null
rg -n "export const runtime|export const ensureStatic|export const instant|export const prefetch" app src/app 2>/dev/null
rg -n "export async function (GET|POST|PUT|PATCH|DELETE)|NextResponse\.next\(|RouteContext" app src/app 2>/dev/null
rg -n "drizzle|drizzle.config|schema|migrate|push|pull|check|prepared|relations|RQB" drizzle.config.* src/db db src/modules src/services 2>/dev/null

# Proxy / env checks
find . -maxdepth 2 \( -name 'proxy.ts' -o -name 'middleware.ts' -o -name 'middleware.js' \)
rg -n "NEXT_PUBLIC_.*(SECRET|TOKEN|PASSWORD|DATABASE_URL|PRIVATE)|process\.env\.(?!NEXT_PUBLIC_)" app src/app src/components 2>/dev/null
```

Interpret grep output with the relevant topic rules; grep output alone is not a verdict.

## Readback Evidence

Before reporting completion, record:

- scenario name and claim being verified
- exact invocation
- binary observable such as an exit code, a missing-file count, or a diff result
- captured artifact path

Read back the project files the change touched and confirm that links, headings, and rule responsibilities still match.

## Sources

> No external sources were used in this file; it describes repository-local commands and readback steps. Framework facts live in the topic rule files under `rules/nextjs/` and in `references/official/nextjs/`. Repository-local links checked 2026-11-04.
