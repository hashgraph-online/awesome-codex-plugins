# Validation and Readback

> Completion checks for Vite + TanStack Router architecture work.

## Project Work Validation

Run checks appropriate to the touched surfaces:

```bash
# Project indicators and Start route-away
rg -n '"vite"|"@tanstack/react-router"|"@tanstack/router-plugin"|"@tanstack/react-start"' package.json
find . -maxdepth 2 \( -name 'vite.config.ts' -o -name 'vite.config.mts' -o -name 'app.config.ts' -o -name 'tsr.config.json' \)

# Route tree and route files
find src/routes -maxdepth 5 -type f \( -name 'index.tsx' -o -name 'route.tsx' -o -name '__root.tsx' \) 2>/dev/null
rg -n 'export const Route|const Route|createFileRoute|validateSearch|zodValidator|fallback|loader:' src/routes 2>/dev/null
rg -n 'createServerFn|useServerFn|createMiddleware|/-functions|/-components|/-hooks' src/routes src 2>/dev/null

# Query prefetch API and Vite 8 bundler names
rg -n 'ensureQueryData|fetchQuery|prefetchQuery|queryClient\.query' src 2>/dev/null
rg -n 'esbuild|rollupOptions|manualChunks|rolldownOptions|codeSplitting|oxc' vite.config.* 2>/dev/null

# Layer and runtime-boundary checks
rg -n 'fetch\(|axios\.|import\.meta\.env\.(?!VITE_)|process\.env|DB_|DATABASE_URL|SECRET|TOKEN|PASSWORD|fs\b|@prisma/client|drizzle-orm' src/routes src/hooks src/services src/lib 2>/dev/null

# Shared nested folder checks
find src/lib src/services lib services -maxdepth 2 -type f 2>/dev/null
rg -n 'src/lib|src/services|direct leaf|explicit project exception' skills/hyper-architecture/stacks/vite/architecture-rules.md skills/hyper-architecture/rules/vite/services.md 2>/dev/null

# Platform checks
rg -n 'tanstackRouter|@tanstack/router-plugin/vite|@vitejs/plugin-react|react\(|routeTree\.gen|createRouter|RouterProvider|ImportMetaEnv|vite/client|loadEnv|resolve:\s*\{' vite.config.* tsr.config.json src/router.tsx src/main.tsx src/vite-env.d.ts 2>/dev/null
```

Interpret grep output with the relevant topic rule files; grep output alone is not a verdict.

## Readback Evidence

Before reporting completion, record:

- the claim being verified and the check that covers it
- the exact invocation
- a binary observable such as an exit code, a missing-file count, or a diff result
- any captured artifact path

Read back the project files the change touched and confirm that links, headings, and rule responsibilities still match.

## Sources

> This file's validation and readback commands are this package's own checks over project state. The official-snapshot reference they cite is `references/official/vite/current-docs-2026-11-04.md`, whose own verification date is 2026-11-04; no external source was used to author the commands and no page was re-fetched for this file. Command text and repository-local paths checked 2026-11-04.
