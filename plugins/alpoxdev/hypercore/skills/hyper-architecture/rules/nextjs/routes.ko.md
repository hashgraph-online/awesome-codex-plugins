# Routes and File Conventions

> 공식 App Router 구조, special files, segments, route groups, private organization.

---

## Core Structure

```text
app/
├── layout.tsx
├── page.tsx
├── dashboard/
│   ├── layout.tsx
│   ├── page.tsx
│   ├── loading.tsx
│   ├── error.tsx
│   ├── not-found.tsx
│   ├── _components/
│   └── _lib/
└── api/
    └── webhooks/
        └── route.ts
```

## Segment File Meaning

| File | Purpose |
|---|---|
| `page.tsx` | route segment의 UI entry; 해당 route를 public accessible하게 만들기 위해 필요 |
| `layout.tsx` | segment와 children의 shared UI shell |
| `template.tsx` | navigation 때 remount되는 layout-like wrapper |
| `loading.tsx` | segment용 Suspense fallback |
| `error.tsx` | segment-level error boundary; Client Component여야 함 |
| `not-found.tsx` | segment-level 404 UI |
| `forbidden.tsx` / `unauthorized.tsx` | Experimental auth interruption UI; `experimental.authInterrupts`와 명시적 risk acceptance 필요 |
| `route.ts` | HTTP-native Route Handler |

컴포넌트 단위 에러 복구는 파일 관례가 아닙니다. `next/error`의 `catchError`(`v16.3` stable)는 `redirect()`와 `notFound()`와 공존하는 error boundary로 컴포넌트 tree 일부를 감싸고, fallback은 실패한 server 작업을 다시 받아오는 `retry()`를 받습니다. 경계가 route 세그먼트보다 잘아야 할 때 씁니다.

## Non-Routable Organization

| Pattern | Meaning |
|---|---|
| `(marketing)` | Route group; URL에 영향 없이 files organization |
| `_components/` | Private folder; colocated route internals에 안전 |
| `_lib/` | segment-local helpers용 private folder |
| `@slot` | parent layout으로 전달되는 parallel route slot |
| `(.)`, `(..)`, `(...)` | modal/overlay style navigation용 intercepting route patterns |

route segment가 되면 안 되는 colocated implementation files에는 private folders를 사용합니다. shared/global folder structure, `src`, nested `lib` grouping은 `rules/nextjs/project-structure.md`를 읽습니다.

## Hard Rules

| 확인 | 규칙 |
|---|---|
| 같은 route segment에 `route.ts`와 `page.tsx` 존재 | 차단 |
| `app/`가 이미 담당하는 surface의 App Router feature work를 `pages/` 아래에 추가 | 명시 요청 없으면 차단 |
| route groups를 URL 변경 수단처럼 사용 | 차단 |
| internal route helpers를 private folders 대신 route segments로 노출 | 차단 |
| parent layout slot props와 default/fallback behavior 없이 parallel routes 추가 | 차단 |
| hard-navigation fallback behavior 없이 intercepted routes 추가 | 위험도에 따라 경고/차단 |

## Placement Guidance

- page UI는 `page.tsx`에 둡니다.
- segment-shared UI는 `layout.tsx`에 둡니다.
- route-specific helper modules는 `_` private folders에 둡니다.
- page UI가 아니라 HTTP semantics로 응답할 때만 `route.ts`를 사용합니다.
- pathname은 유지하고 organization만 필요하면 route groups를 사용합니다.
- 적합하면 custom handlers보다 metadata file conventions(`sitemap`, `robots`, icons, Open Graph images)를 먼저 사용합니다.

## Error and Loading Boundaries

- `error.tsx`는 Client Component여야 하고, 실패한 server render 뒤 세그먼트를 다시 렌더링하는 `retry()`를 받습니다.
- `catchError`는 세그먼트 하위 경계를 맡습니다. `error.tsx` default export는 이미 프레임워크 error boundary 안에서 렌더링되므로 `catchError`로 감싸지 않습니다.
- `loading.tsx`는 segment-level streaming fallback에 적합합니다.
- blocking work가 tree 깊은 곳에 있으면 segment root `loading.tsx`에만 맡기지 말고 더 가까운 `<Suspense>` boundary를 선호합니다.
- missing resource flow에는 `notFound()`와 `not-found.tsx`를 사용합니다.
- `forbidden()` / `unauthorized()` 및 해당 special files는 experimental `authInterrupts`가 활성화되어 있고 프로젝트가 instability를 수용할 때만 사용합니다.

## Mixed Router Repos

- untouched `pages/` routes에 `page.tsx` / `layout.tsx` conventions를 강요하지 않습니다.
- legacy compatibility가 필요하지 않다면 새 `pages/api/*` endpoints보다 App Router `route.ts` 또는 Server Action이 자연스러운지 먼저 확인합니다.

## Review Checklist

- Special files가 valid route segments에 있음.
- `route.ts` / `page.tsx` conflict 없음.
- Route groups와 private folders를 의도적으로 사용함.
- Parallel/intercepted route patterns에 필요한 layout 및 navigation behavior가 있음.
- UX에 필요한 loading, error, not-found, auth interruption boundaries가 있음.

## Sources

> 확인 2026-11-04. `https://nextjs.org/docs/app/api-reference/file-conventions`, `https://nextjs.org/docs/app/api-reference/functions/catchError`, `https://nextjs.org/docs/app/api-reference/file-conventions/error`, `https://nextjs.org/docs/app/getting-started/project-structure`를 확인했습니다. 날짜가 붙은 스냅숏은 `references/official/nextjs/current-docs-2026-11-04.md`입니다.
