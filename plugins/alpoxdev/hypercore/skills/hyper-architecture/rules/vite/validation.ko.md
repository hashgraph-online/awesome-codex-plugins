# Validation and Readback

> Vite + TanStack Router architecture 작업 완료 검증.

## Project Work Validation

변경 표면에 맞는 check를 실행합니다:

```bash
rg -n '"vite"|"@tanstack/react-router"|"@tanstack/router-plugin"|"@tanstack/react-start"' package.json
find . -maxdepth 2 \( -name 'vite.config.ts' -o -name 'vite.config.mts' -o -name 'app.config.ts' -o -name 'tsr.config.json' \)
find src/routes -maxdepth 5 -type f \( -name 'index.tsx' -o -name 'route.tsx' -o -name '__root.tsx' \) 2>/dev/null
rg -n 'export const Route|const Route|createFileRoute|validateSearch|zodValidator|fallback|loader:' src/routes 2>/dev/null
rg -n 'createServerFn|useServerFn|createMiddleware|/-functions|/-components|/-hooks' src/routes src 2>/dev/null
rg -n 'ensureQueryData|fetchQuery|prefetchQuery|queryClient\.query' src 2>/dev/null
rg -n 'esbuild|rollupOptions|manualChunks|rolldownOptions|codeSplitting|oxc' vite.config.* 2>/dev/null
rg -n 'fetch\(|axios\.|import\.meta\.env\.(?!VITE_)|process\.env|DB_|DATABASE_URL|SECRET|TOKEN|PASSWORD|fs\b|@prisma/client|drizzle-orm' src/routes src/hooks src/services src/lib 2>/dev/null
find src/lib src/services lib services -maxdepth 2 -type f 2>/dev/null
rg -n 'src/lib|src/services|direct leaf|explicit project exception' skills/hyper-architecture/stacks/vite/architecture-rules.md skills/hyper-architecture/rules/vite/services.md 2>/dev/null
rg -n 'tanstackRouter|@tanstack/router-plugin/vite|@vitejs/plugin-react|react\(|routeTree\.gen|createRouter|RouterProvider|ImportMetaEnv|vite/client|loadEnv|resolve:\s*\{' vite.config.* tsr.config.json src/router.tsx src/main.tsx src/vite-env.d.ts 2>/dev/null
```

grep 결과만으로 판단하지 말고 relevant topic rule files와 함께 해석합니다.

## Readback Evidence

completion을 보고하기 전에 다음을 기록합니다:

- 검증하는 claim과 그것을 담당하는 check
- exact invocation
- exit code, missing-file count, diff result 같은 binary observable
- captured artifact path가 있으면 그 경로

변경이 닿은 프로젝트 파일을 read back하고 links, headings, rule responsibilities가 그대로 맞는지 확인합니다.

## Sources

> 이 파일의 validation/readback 명령은 project 상태에 대한 이 패키지 고유의 check입니다. 이 명령들이 인용하는 official snapshot 참조는 `references/official/vite/current-docs-2026-11-04.ko.md`이고, 그 스냅샷이 기록한 자체 검증일은 2026-11-04입니다. 명령 작성에 외부 출처를 사용하지 않았고 이 파일을 위해 페이지를 다시 가져오지 않았습니다. 명령 문장과 저장소 로컬 경로 확인 2026-11-04.
