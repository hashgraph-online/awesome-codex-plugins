# Validation and Readback

> Next.js architecture 작업 완료 검증.

## Project Work Validation

변경 표면에 맞는 check를 실행합니다:

```bash
rg -n '"next"' package.json
find . -maxdepth 3 \( -path './app' -o -path './src/app' -o -path './pages' -o -path './src/pages' \)
find app src/app -maxdepth 5 -type f \( -name 'page.tsx' -o -name 'route.ts' -o -name 'layout.tsx' -o -name 'loading.tsx' -o -name 'error.tsx' \) 2>/dev/null
rg -n "^['\"]use client['\"]|server-only|client-only|cookies\(|headers\(|process\.env|NEXT_PUBLIC_" app src/app src/components src/lib src/services 2>/dev/null
rg -n "cacheComponents|partialPrefetching|use cache|cacheTag|cacheLife|io\(|connection\(|navigation\(|prefetch\(|ensureStatic|instant|updateTag|revalidateTag|revalidatePath|refresh\(|redirect\(" next.config.* app src/app src/lib src/services 2>/dev/null
rg -n "export const runtime|export const ensureStatic|export const instant|export const prefetch" app src/app 2>/dev/null
rg -n "export async function (GET|POST|PUT|PATCH|DELETE)|NextResponse\.next\(|RouteContext" app src/app 2>/dev/null
rg -n "drizzle|drizzle.config|schema|migrate|push|pull|check|prepared|relations|RQB" drizzle.config.* src/db db src/modules src/services 2>/dev/null
find . -maxdepth 2 \( -name 'proxy.ts' -o -name 'middleware.ts' -o -name 'middleware.js' \)
rg -n "NEXT_PUBLIC_.*(SECRET|TOKEN|PASSWORD|DATABASE_URL|PRIVATE)|process\.env\.(?!NEXT_PUBLIC_)" app src/app src/components 2>/dev/null
```

grep 결과만으로 판단하지 말고 relevant topic rules와 함께 해석합니다.

## Readback Evidence

completion을 보고하기 전에 다음을 기록합니다:

- 검증하는 scenario name과 claim
- exact invocation
- exit code, missing-file count, diff result 같은 binary observable
- captured artifact path

변경이 닿은 프로젝트 파일을 read back하고 links, headings, rule responsibilities가 그대로 맞는지 확인합니다.

## Sources

> 이 파일에는 외부 출처를 사용하지 않았습니다. 저장소 로컬 명령과 readback 절차만 다룹니다. 프레임워크 사실은 `rules/nextjs/` 아래 topic rule 파일과 `references/official/nextjs/`에 있습니다. 저장소 로컬 링크 확인 2026-11-04.
