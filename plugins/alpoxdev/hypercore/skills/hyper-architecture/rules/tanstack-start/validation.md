# Validation and Readback

> Completion checks for TanStack Start architecture work.

## Project Work Validation

Run checks appropriate to the touched surfaces:

```bash
# Route export and direct DB access checks
rg -n "const Route = createFileRoute|export const Route" src/routes 2>/dev/null
rg -n "from ['\"]@/database|from ['\"].*/database|@prisma/client|drizzle-orm" src/routes 2>/dev/null

# Server function validation and stale API checks
# Detection grep: keep BOTH spellings. `.inputValidator(` was removed in 1.169.0, so a hit is broken code, not legacy style
rg -n "\.validator\(|\.inputValidator\(|createServerFn" src 2>/dev/null

# Import boundary checks
rg -n "server-only|client-only|\.server\.|\.client\.|importProtection|tanstackStart" vite.config.* src 2>/dev/null

# Loader and hydration risk checks
rg -n "loader:|beforeLoad:|Date\.now\(|Math\.random\(|localStorage|window\." src/routes src/components 2>/dev/null

# Per-request env rule: module-scope process.env reads are wrong on edge SSR runtimes
rg -n "^\s*(const|let|var|export const)\s+\w+\s*=\s*process\.env\." src 2>/dev/null

# v1 upgrade surface: removed APIs and the Vite 8 / Node 22.12 floors
rg -n "nitro-v2-vite-plugin|useSession|inputValidator" src vite.config.* package.json 2>/dev/null
rg -n '"(vite|node)"' package.json 2>/dev/null

# Env config checks when env validation is touched or scaffolded
test ! -d src/env
test ! -f src/env.ts
test -f src/config/env.ts
rg -n "@t3-oss/env-core|createEnv" src/config/env.ts
rg -n "clientPrefix: ['\"]VITE_|runtimeEnvStrict|runtimeEnv|emptyStringAsUndefined|isServer" src/config/env.ts
rg -n "VITE_.*(SECRET|TOKEN|PASSWORD|DATABASE_URL|PRIVATE)" src/config/env.ts .env* 2>/dev/null
```

Interpret results with the topic rule files; grep output alone is not a verdict.

## Completion Checklist

- [ ] Project validation confirmed this skill applies, or route-away happened.
- [ ] Only relevant rule/reference files were loaded.
- [ ] Applicable rules/tanstack-start were classified as Official, Safety policy, or Hypercore convention.
- [ ] Blocking safety gates were fixed before style conventions.
- [ ] Env scaffolds, when touched, use `src/config/env.ts` and do not create `src/env/`.
- [ ] Broad migrations were avoided unless requested.
- [ ] Verification commands were run and read.
- [ ] Server function wrapper/helper split, static imports, auth/CSRF boundary, and no mixed barrels were checked.
- [ ] Remaining risks or TanStack API ambiguities cite exact sources and dates.

## Sources

> Sources checked 2026-11-04: <https://tanstack.com/start/latest/docs/framework/react/migrate-from-release-candidate.md> (removed APIs, Vite 8), <https://tanstack.com/start/latest/docs/framework/react/guide/environment-variables.md> (per-request env reads), <https://tanstack.com/start/latest/docs/framework/react/guide/import-protection.md> (documented option surface), <https://registry.npmjs.org/@tanstack/react-start/latest> (Node engine floor). Official TanStack behavior is otherwise delegated to this package's own snapshots: `references/official/tanstack-start/tanstack-start-2026-11-04.md`, `references/official/tanstack-start/tanstack-router-2026-11-04.md`, and `references/official/tanstack-start/current-docs-2026-11-04.md` (official facts verified 2026-11-04). Repository-local links checked 2026-11-04.
