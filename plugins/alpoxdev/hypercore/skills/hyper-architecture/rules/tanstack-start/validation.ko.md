# Validation and Readback

> TanStack Start architecture 작업의 완료 검증.

## Project Work Validation

변경 표면에 맞는 check를 실행합니다:

```bash
# route export와 직접 DB 접근 검사
rg -n "const Route = createFileRoute|export const Route" src/routes 2>/dev/null
rg -n "from ['\"]@/database|from ['\"].*/database|@prisma/client|drizzle-orm" src/routes 2>/dev/null

# server function 검증과 낡은 API 검사
# 탐지 grep: 두 철자를 모두 유지합니다. `.inputValidator(`는 1.169.0에서 제거됐으므로 발견되면 legacy 스타일이 아니라 깨진 코드입니다
rg -n "\.validator\(|\.inputValidator\(|createServerFn" src 2>/dev/null

# import 경계 검사
rg -n "server-only|client-only|\.server\.|\.client\.|importProtection|tanstackStart" vite.config.* src 2>/dev/null

# loader와 hydration 위험 검사
rg -n "loader:|beforeLoad:|Date\.now\(|Math\.random\(|localStorage|window\." src/routes src/components 2>/dev/null

# per-request env 규칙: edge SSR runtime에서 module scope process.env 읽기는 틀림
rg -n "^\s*(const|let|var|export const)\s+\w+\s*=\s*process\.env\." src 2>/dev/null

# v1 업그레이드 표면: 제거된 API와 Vite 8 / Node 22.12 하한
rg -n "nitro-v2-vite-plugin|useSession|inputValidator" src vite.config.* package.json 2>/dev/null
rg -n '"(vite|node)"' package.json 2>/dev/null

# env validation을 손대거나 scaffold할 때의 env 설정 검사
test ! -d src/env
test ! -f src/env.ts
test -f src/config/env.ts
rg -n "@t3-oss/env-core|createEnv" src/config/env.ts
rg -n "clientPrefix: ['\"]VITE_|runtimeEnvStrict|runtimeEnv|emptyStringAsUndefined|isServer" src/config/env.ts
rg -n "VITE_.*(SECRET|TOKEN|PASSWORD|DATABASE_URL|PRIVATE)" src/config/env.ts .env* 2>/dev/null
```

grep 결과만으로 판단하지 말고 topic rule file과 함께 해석합니다.

## Completion Checklist

- [ ] project validation으로 이 스킬 적용 여부를 확인하거나 route-away함.
- [ ] 필요한 rule/reference file만 읽음.
- [ ] 적용 규칙을 Official, Safety policy, Hypercore convention으로 분류함.
- [ ] blocking safety gate를 style convention보다 먼저 수정함.
- [ ] env scaffold를 건드렸다면 `src/config/env.ts`를 사용하고 `src/env/`를 만들지 않음.
- [ ] broad migration은 요청 없으면 피함.
- [ ] verification command를 실행하고 결과를 읽음.
- [ ] server function wrapper/helper split, static imports, auth/CSRF boundary, no mixed barrels를 확인함.
- [ ] 남은 risk 또는 TanStack API ambiguity가 정확한 source/date를 인용함.

## Sources

> 출처 확인 2026-11-04: <https://tanstack.com/start/latest/docs/framework/react/migrate-from-release-candidate.md>(삭제된 API, Vite 8), <https://tanstack.com/start/latest/docs/framework/react/guide/environment-variables.md>(request 단위 env 읽기), <https://tanstack.com/start/latest/docs/framework/react/guide/import-protection.md>(문서화된 option 표면), <https://registry.npmjs.org/@tanstack/react-start/latest>(Node engine 하한). 그 밖의 공식 TanStack 동작은 이 패키지 자체의 snapshot(`references/official/tanstack-start/tanstack-start-2026-11-04.md`, `references/official/tanstack-start/tanstack-router-2026-11-04.md`, `references/official/tanstack-start/current-docs-2026-11-04.md`)에 위임합니다. 공식 사실 검증 2026-11-04. 저장소 로컬 링크 확인 2026-11-04.
