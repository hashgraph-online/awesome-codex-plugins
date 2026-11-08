# Client Hooks and Orchestration Boundaries

> server, data, privileged runtime layers를 넘지 않는 client orchestration을 위한 Next.js hook guidance입니다.

## Rule Classifications

| Rule | Classification | Enforcement |
|---|---|---|
| Hooks는 Client Components 또는 client modules에서만 실행됨 | React/Next.js fact | client entry point에 `'use client'`를 추가하거나 좁힘 |
| Client hooks는 server-only code를 import할 수 없음 | Safety policy | DB, private env, `cookies()`, `headers()`, DAL, provider secret imports 차단 |
| Hooks는 UI state와 client-side effects를 orchestrate함 | Hypercore local convention | touched interactive UI에 적용 |
| Server reads/writes는 Server Components 또는 Server Actions를 우선함 | Official + safety policy | privileged data를 hook으로 우회하지 않음 |

## Boundary Rule

훅은 client orchestration boundary이지 server/data layer가 아닙니다. hook은 UI state, browser APIs, optimistic UI, transitions, client cache libraries, Server Actions 호출을 조율할 수 있습니다. database access, Drizzle queries, private env, cookies/headers reads, provider SDK secrets, authorization decisions를 소유하면 안 됩니다.

기본 flow:

```text
Client Component
  -> useFeatureHook()
  -> Server Action or client-safe query/cache call
  -> server-only service/DAL
  -> DB or integration
```

초기 page data는 Server Components를 우선하고 serializable minimal props를 client leaf로 넘깁니다. client hooks는 hydration 후 interaction이나 진짜 browser-only data에 사용합니다.

## Placement

repository의 기존 convention을 먼저 따릅니다. 흔한 Hypercore local shapes:

```text
src/app/dashboard/_hooks/use-dashboard-filters.ts
src/modules/billing/invoices/hooks/use-invoice-selection.ts
src/components/data-table/use-column-visibility.ts
```

하나의 App Router segment에만 쓰이는 segment-local hooks는 그 segment의 `_hooks/` 아래에 둘 수 있습니다. cross-route hooks는 domain module 또는 shared component folder에 둡니다.

## Hook Responsibilities

좋은 hook responsibilities:

- UI state, reducers, refs, browser events
- form pending/error state와 optimistic client state
- `useActionState`, transitions, Server Action invocation state
- project가 client cache library를 쓸 때 client cache invalidation wrappers
- 이미 safe한 DTO에서 파생된 view state

server-side에 남아야 하는 responsibilities:

- Drizzle queries, repository calls, transactions, schema migration concerns
- protected data 또는 mutations에 대한 auth/authz decisions
- private env reads, `cookies()`, `headers()`, filesystem, server-only provider clients
- security-sensitive output을 위한 raw DB row shaping
- public HTTP contracts에 대한 Route Handler 또는 Server Action 대체

## Navigation and Effect Lifecycle

Cache Components가 켜지면 navigate해서 떠난 route는 unmount되지 않고 React `<Activity mode="hidden">`로 숨겨집니다. hook은 이 모델에 맞춰 작성합니다:

- route가 숨겨질 때 effect와 구독이 정리되고 다시 보일 때 재생성됩니다. 컴포넌트 수명당 한 번 listener를 등록하는 hook은 navigation 뒤에 그것을 잃고, effect 기반이 아니면 복구하지 못합니다.
- 로컬 상태가 왕복을 넘어 살아남으므로 navigation 뒤에 dropdown이 닫혀 있거나 draft가 비워져 있을 거라 기대하는 hook은 그 초기화를 보지 못합니다. UX상 필요하면 visibility 전환에서 초기화를 명시적으로 겁니다.
- hidden route가 영원히 mount된 채 남는다고 가정하지 않습니다. Next.js는 최근 방문 route 몇 개만 hidden으로 유지합니다.

## Server Action Invocation State

Server Actions는 client마다 한 번에 하나씩 dispatch되므로 client hook은 두 호출이 동시에 실행된다고 가정할 수 없습니다. 한 handler에서 여러 action을 쏘는 hook은 실행이 줄을 서고, `Promise.all`로도 바뀌지 않습니다. 의존 관계가 있는 쓰기는 하나의 복합 action으로 순서를 정하거나, 뒤 호출이 기다린다는 사실을 받아들입니다.

## Internal Order

touched non-trivial hooks는 일관된 순서를 선호합니다:

```typescript
export const useInvoices = (): UseInvoicesReturn => {
  // 1. Local state and refs
  // 2. Context/global client stores
  // 3. Server Action state or client cache bindings
  // 4. Handlers and callbacks
  // 5. Memoized derived view data
  // 6. Effects
  // 7. Return object
}
```

## Review Checklist

- [ ] Hook file은 필요한 경우에만 client-reachable이고 broad root-level `'use client'`를 강제하지 않음.
- [ ] Hook이 DB client, Drizzle schema, private env, `server-only`, `cookies()`, `headers()`, privileged provider client를 import하지 않음.
- [ ] browser-only reason 없이 initial Server Component data를 client-side에서 다시 fetch하지 않음.
- [ ] Server Action calls는 여전히 server-side에서 validate/authorize됨. hook-level checks는 UX aid일 뿐임.
- [ ] Hook이 병렬 Server Action dispatch나 navigation 뒤의 새 mount를 가정하지 않음.
- [ ] hidden route가 다시 보일 때 effect가 재등록됨.
- [ ] Hook은 internal records가 아니라 client-safe DTO/view state를 반환함.
- [ ] segment-local hooks는 `_hooks/`에 있고 cross-route hooks는 shared domain/component folder로 이동함.

## Sources

> 확인 2026-11-04. `https://nextjs.org/docs/app/api-reference/config/next-config-js/cacheComponents`, `https://nextjs.org/docs/app/guides/preserving-ui-state`, `https://nextjs.org/docs/app/guides/server-actions`, `https://nextjs.org/docs/app/getting-started/server-and-client-components`를 확인했습니다. 날짜가 붙은 스냅숏은 `references/official/nextjs/current-docs-2026-11-04.md`입니다.
