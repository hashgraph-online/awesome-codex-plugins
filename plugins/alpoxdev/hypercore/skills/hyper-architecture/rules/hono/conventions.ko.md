# 코드 컨벤션

> Hono 프로젝트 코딩 규칙

---

## Stable compatibility 규칙

Formatting과 import order는 project tooling이 소유합니다. Hono는 kebab-case path, arrow function 또는 하나의 universal import grouping을 요구하지 않습니다. 이는 Hypercore convention이므로 그렇게 구분해 보고합니다.

- Style 강제 전 formatter, linter, TypeScript mode, module resolution, alias, generated file, runtime을 조사합니다.
- Hono inferred route type을 보존하며 style preference만을 위해 broad annotation을 추가하지 않습니다.
- Untrusted boundary에서는 `unknown`을 사용하고 validator 또는 explicit guard로 좁힙니다.
- Compiler/linter가 요구하면 `import type`을 유지하고 type만을 위한 runtime import를 만들지 않습니다.
- Owning tool과 repository workflow가 명시적으로 허용하지 않으면 generated route tree, declaration, OpenAPI artifact, migration을 손으로 편집하지 않습니다.
- Path rename은 behavioral change입니다. Case-sensitive import/export, test, alias, package export, config, generated reference를 원자적으로 갱신합니다.
## 폴더와 파일 이름

> camelCase와 PascalCase source path는 금지. Source folder와 file은 kebab-case 유지.

| 타입 | 규칙 | 예시 |
|------|------|------|
| 일반 파일 | kebab-case | `create-app.ts`, `request-id.ts` |
| 라우트 폴더 | kebab-case | `routes/user-profile/` |
| Feature folder | kebab-case | `services/user-profile/`, `repositories/audit-log/` |
| Database folder | kebab-case | `database/`, `drizzle/migrations/` |
| 핸들러 파일 | kebab-case | `handlers.ts`, `list-users.ts` |
| 스키마 파일 | kebab-case | `schemas.ts`, `user-payload.ts` |
| 미들웨어 | kebab-case | `auth.ts`, `request-id.ts` |

허용 예외:

- `package.json`, `tsconfig.json`, `drizzle.config.ts`, lockfile, generated declaration file처럼 tool이 요구하는 root file
- 설정된 migration tool이 특정 이름을 요구하는 provider-generated migration artifact
- rename이 외부 contract를 깨뜨릴 때, repo에 이미 존재하는 framework convention

`전체 수정` 모드에서는 감지된 Hono source folder/file 전체를 스캔하고, 모든 import, test path, route reference, config reference를 같은 변경 안에서 갱신할 수 있을 때 kebab-case 위반을 rename합니다.

---

## TypeScript 규칙

| 규칙 | 설명 | 예시 |
|------|------|------|
| 함수 스타일 | const 화살표 함수, 명시적 반환 타입 | `const handler = (c: Context): Response => {}` |
| no any | `unknown` 또는 구체 타입 사용 | `const payload: unknown = await c.req.json()` |
| type import | type import 분리 | `import type { Context } from 'hono'` |
| app generics | 쓰는 경우 `Bindings`, `Variables` 타입 명시 | `new Hono<AppEnv>()` |

---

## Import 순서

```ts
import { Hono } from 'hono'
import { createFactory } from 'hono/factory'
import { zValidator } from '@hono/zod-validator'

import { createApp } from '@/lib/create-app'
import { authMiddleware } from '@/middlewares/auth'
import { createUser } from '@/services/users/create-user'

import { userSchema } from './schemas'

import type { AppEnv } from '@/lib/types'
```

---

## 주석 스타일

- 코드 묶음에 방향 설명이 필요할 때만 짧은 블록 주석 사용
- line-by-line 설명 금지
- 주석은 아키텍처 의도 중심으로 유지

## Sources

> Checked 2026-11-04. 이 파일은 이 package 자체 참조 밖의 외부 출처를 쓰지 않았습니다. 공식 Hono 동작은 [`references/official/hono/hono-docs.ko.md`](../../references/official/hono/hono-docs.ko.md)에 위임하며, 그 문서는 2026-11-04에 확인했습니다.
