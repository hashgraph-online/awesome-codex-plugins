# 코드 컨벤션

> Vite + TanStack Router 프로젝트 코딩 규칙

---

## 파일 네이밍

> camelCase 파일명 금지 - 모든 파일명은 kebab-case 사용

| 타입 | 규칙 | 예시 |
|------|------|---------|
| **일반 파일** | kebab-case | `user-profile.tsx`, `auth-service.ts` |
| **라우트 파일** | TanStack Router 규칙 | `__root.tsx`, `index.tsx`, `$id.tsx` |
| **훅 파일** | `use-` 접두사 + kebab-case | `use-user-filter.ts`, `use-auth.ts` |
| **컴포넌트** | PascalCase 컴포넌트, kebab-case 파일 | `user-card.tsx`에 `UserCard` |
| **서비스 파일** | kebab-case | `get-users.ts`, `create-post.ts` |

```
금지된 camelCase: getUserById.ts, authService.ts, useUserFilter.ts
필수 kebab-case: get-user-by-id.ts, auth-service.ts, use-user-filter.ts
```

---

## TypeScript 규칙

| 규칙 | 설명 | 예시 |
|------|-------------|---------|
| **함수 선언** | const 화살표 함수, 명시적 반환 타입 | `const fn = (): ReturnType => {}` |
| **타입 정의** | interface (객체), type (유니온) | `interface User {}`, `type Status = 'a' \| 'b'` |
| **any 금지** | unknown 사용 | `const data: unknown = JSON.parse(str)` |
| **타입 임포트** | 타입 임포트 분리 | `import type { User } from '@/types'` |

```typescript
// const 화살표 함수, 명시적 타입
const getUserById = async (id: string): Promise<User> => {
  const response = await apiClient.get(`/users/${id}`)
  return response.data
}

// any 금지 -> unknown 사용
const parseJSON = (data: string): unknown => {
  return JSON.parse(data)
}

// function 키워드 금지
// function badFunction() {} -> const 화살표 함수 사용
```

---

## 임포트 순서

```typescript
// 1. 외부 라이브러리
import { createFileRoute } from '@tanstack/react-router'
import { useQuery } from '@tanstack/react-query'
import { z } from 'zod'

// 2. 내부 패키지 (@/)
import { Button } from '@/components/ui/button'
import { apiClient } from '@/config/api-client'
import { usersQueryOptions } from '@/services/user/queries'

// 3. 상대 임포트 (라우트 전용)
import { UserCard } from './-components/user-card'
import { useUsers } from './-hooks/use-users'

// 4. 타입 임포트
import type { User } from '@/types'
import type { UseUsersReturn } from './-hooks/use-users'
```

---

## 한국어 블록 주석 (그룹당)

```typescript
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 유저 관련 상태
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
const [user, setUser] = useState<User | null>(null)
const [isLoading, setIsLoading] = useState(false)

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 데이터 페칭
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
const { data: users } = useQuery(usersQueryOptions())
```

줄별 주석 금지. 코드 그룹/블록당 주석만 허용.

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

---

## Sources

> 이 파일의 네이밍, TypeScript, import 순서, 주석, 에러 처리 규칙은 official Vite 또는 TanStack Router 요구사항이 아니라 Hypercore/repo-local convention입니다. TanStack Router route 파일 이름 항목은 이 패키지 자체의 guidance이며 `references/official/vite/current-docs-2026-11-04.ko.md`에 기록된 dated snapshot에서 가져온 사실이 아닙니다(그 스냅샷이 기록한 자체 검증일은 2026-11-04). 이 파일을 위해 페이지를 다시 가져오지 않았고 다른 외부 출처도 인용하지 않습니다. 규칙 문장과 저장소 로컬 경로 확인 2026-11-04.
