# 코드 컨벤션

> TanStack Start 프로젝트 코드 작성 규칙

---

## Rule Classifications

| Rule | Classification | Enforcement |
|---|---|---|
| route filename은 TanStack Router convention 준수 | Official | official route name 유지 |
| route 외 filename은 kebab-case | Hypercore convention | touched file에 적용 |
| no `any`, explicit return type, const arrow function | Hypercore convention | touched code에 적용 |
| 의미 있는 code group의 Korean block comment | Hypercore convention | touched implementation file에 적용 |

---

## 파일 네이밍

> camelCase 파일명 금지 - 모든 파일명은 kebab-case 사용

| 타입 | 규칙 | 예시 |
|------|------|------|
| **일반 파일** | kebab-case | `user-profile.tsx`, `auth-service.ts` |
| **Route 파일** | TanStack Router 규칙 | `__root.tsx`, `index.tsx`, `$id.tsx` |
| **Hook 파일** | `use-` 접두사 + kebab-case | `use-user-filter.ts`, `use-auth.ts` |
| **Component** | PascalCase 컴포넌트, kebab-case 파일 | `UserCard` in `user-card.tsx` |
| **Server Function** | kebab-case | `get-users.ts`, `create-post.ts` |

```
camelCase 금지: getUserById.ts, authService.ts, useUserFilter.ts
kebab-case 필수: get-user-by-id.ts, auth-service.ts, use-user-filter.ts
```

Folder shape와 placement(route root, shared folder, co-located `-hooks/` / `-components/` / `-functions/` directory)는 [`rules/tanstack-start/project-structure.md`](project-structure.md)가 소유하고, 이 파일은 파일 명명을 소유합니다. 파일을 추가할 때 두 규칙을 함께 적용합니다.

---

## TypeScript 규칙

| 규칙 | 설명 | 예시 |
|------|------|------|
| **함수 선언** | const 함수, 명시적 return type (아래 framework entrypoint 예외) | `const fn = (): ReturnType => {}` |
| **타입 정의** | interface (객체), type (유니온) | `interface User {}`, `type Status = 'a' \| 'b'` |
| **any 금지** | unknown 사용 | `const data: unknown = JSON.parse(str)` |
| **Import 타입** | type import 분리 | `import type { User } from '@/types'` |

```typescript
// const 함수, 명시적 타입
const getUserById = async (id: string): Promise<User> => {
  return prisma.user.findUnique({ where: { id } })
}

// any 금지 -> unknown 사용
const parseJSON = (data: string): unknown => {
  return JSON.parse(data)
}

// function 키워드 금지, 단 공식 예시가 declaration인 framework entrypoint는 예외
// function badFunction() {} -> const 화살표 함수 사용
```

**Framework entrypoint 예외 (Official).** function declaration 금지에는 예외가 정확히 하나 있습니다. 공식 예시가 declaration을 쓰는 framework-mandated entrypoint입니다. `src/router.tsx`는 `export function getRouter()`를 써야 하므로 (Official), 그 파일 하나만 declaration을 유지합니다. 예외는 declaration이라는 형태에만 적용합니다 - 명시적 return type, `any` 금지, kebab-case 파일명, Korean block comment는 그 파일에도 그대로 적용되고, const 화살표 함수 규칙은 나머지 모든 파일(route file, hook, component, server function, lib)에 그대로 적용됩니다.

---

## Import 순서

```typescript
// 1. External libraries
import { createFileRoute } from '@tanstack/react-router'
import { useQuery } from '@tanstack/react-query'
import { z } from 'zod'

// 2. Internal packages (@/)
import { Button } from '@/components/ui/button'
import { prisma } from '@/database/prisma'
import { getUsers } from '@/modules/users/list/users.functions'

// 3. Relative imports (route-specific)
import { UserCard } from './-components/user-card'
import { useUsers } from './-hooks/use-users'

// 4. Type imports
import type { User } from '@/types'
import type { UseUsersReturn } from './-hooks/use-users'
```

---

## 한글 주석 (묶음 단위)

```typescript
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 사용자 관련 상태
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
const [user, setUser] = useState<User | null>(null)
const [isLoading, setIsLoading] = useState(false)

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 데이터 조회
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
const { data: users } = useQuery({
  queryKey: ['users'],
  queryFn: () => getUsers(),
})
```

세세한 줄별 주석 금지. 코드 묶음 단위로만 주석 작성.

---

## 에러 처리 패턴

```typescript
// lib/errors.ts
export class AppError extends Error {
  constructor(
    message: string,
    public statusCode: number = 500,
    public code: string = 'INTERNAL_ERROR'
  ) {
    super(message)
    this.name = 'AppError'
  }
}

export class NotFoundError extends AppError {
  constructor(resource: string) {
    super(`${resource} not found`, 404, 'NOT_FOUND')
  }
}

export class ValidationError extends AppError {
  constructor(message: string) {
    super(message, 400, 'VALIDATION_ERROR')
  }
}

export class UnauthorizedError extends AppError {
  constructor() {
    super('Unauthorized', 401, 'UNAUTHORIZED')
  }
}
```

## Sources

> 출처 확인 2026-11-04. 이 파일은 이 패키지 자체의 snapshot(`references/official/tanstack-start/tanstack-start-2026-11-04.md`, `references/official/tanstack-start/tanstack-router-2026-11-04.md`, `references/official/tanstack-start/current-docs-2026-11-04.md`)에 담기지 않은 공식 사실을 주장하지 않습니다. 그 snapshot의 공식 사실은 거기 나열된 TanStack guide page에서 2026-11-04에 다시 검증했습니다. 저장소 로컬 링크 확인 2026-11-04.
