# Server Actions

> `use server` 기반 mutation, validation, dispatch 순서, freshness, security 규칙입니다.

---

## Core Rule

모든 Server Action을 reachable POST entry point처럼 취급합니다.

App Router에서 앱 UI에서 시작된 mutation의 기본 surface는 Server Actions입니다.

즉:

- 입력 검증
- 호출자 인증
- resource access 권한 확인
- UI에 필요한 최소 반환값만 제공
- 영향을 받은 데이터를 의도적으로 refresh 또는 revalidate

page-level UI gating만 신뢰하지 않습니다.

## Placement

- 재사용 가능한 actions, 특히 Client Components로 import되는 actions는 top-level `'use server'` 전용 파일을 사용합니다.
- 특정 route에 강하게 묶여 있고 closure가 의도적이면 Server Component 내부 inline action도 허용됩니다.
- 반복되는 DB/auth logic은 server-only DAL 또는 helper로 이동합니다.
- internal app UI에서 시작된 쓰기이고 HTTP-native contract가 필요 없다면 `route.ts`보다 Server Action을 우선합니다.

## Sequential Dispatch

Next.js는 client마다 Server Action을 한 번에 하나씩 dispatch합니다. 두 번째 action은 첫 번째가 끝나기를 기다리고 세 번째는 두 번째를 기다립니다. 재렌더된 server tree가 그 결과를 낳은 action 결과와 일치하게 유지하기 위해서입니다.

- client에서 `Promise.all`로 Server Actions를 병렬 실행하려 하지 않습니다. client가 어차피 줄을 세웁니다.
- 독립적인 작업을 겹쳐야 하면 하나의 Server Action 안에서 처리하거나, Server Component에서 병렬 fetch하거나, mutation이 아닌 요청에 Route Handler를 씁니다.
- 이것은 client dispatcher의 성질입니다. server는 action을 대기열에 넣지 않고 도착하는 대로 각각의 요청에서 실행합니다.

## Single-Response Data and UI

즉시 재검증을 일으키는 action은 mutation과 재렌더를 한 HTTP 요청 안에서 끝냅니다. 응답에는 action의 반환값과 현재 route의 새 RSC payload가 함께 담깁니다.

action이 다음을 하면 같은 응답에 재렌더가 포함됩니다:

- `updateTag` 또는 `revalidatePath` 호출
- `refresh` 호출
- `cookies()`를 통한 cookie 변경
- `redirect` 호출

stale-while-revalidate 프로필의 `revalidateTag`는 예외입니다. tag를 background refresh 대상으로 표시할 뿐 재렌더를 포함하지 않으므로 페이지는 이후 읽기에서 변경을 반영합니다. 위 어느 것도 하지 않는 action은 반환값만 담습니다.

## Forms and Client Calls

- Forms는 `action` attribute로 Server Actions를 호출하고 `FormData`를 받을 수 있습니다.
- authoritative checks에는 server-side validation을 사용합니다. client validation은 UX 보조일 뿐입니다.
- UI에 필요할 때만 좁은 Client Component wrapper에서 `useActionState`, pending state, optimistic updates, transitions를 사용합니다.
- dispatch가 client마다 순차이므로 여러 단계 UI는 호출을 경쟁시키지 말고 명시적 순서나 하나의 복합 action으로 설계합니다.

## Freshness APIs

- read-your-own-writes cache expiration에는 Server Actions 안에서 `updateTag`를 사용합니다. Server Action 전용입니다.
- stale-while-revalidate 동작이 허용되면 `revalidateTag(tag, 'max')`를 사용합니다. Route Handlers에서는 동작하지만 Client Components와 Proxy에서는 안 됩니다.
- path-based invalidation에는 `revalidatePath`를 사용합니다.
- tag invalidation 없이 current client router를 refresh해야 하면 Server Action 안에서 `next/cache`의 `refresh`를 사용합니다. Server Action 전용입니다.
- 필요한 invalidation은 `redirect()` 전에 호출합니다.

## Hard Rules

| 확인 | 규칙 |
|---|---|
| Action이 `FormData`, params, headers, search params를 직접 신뢰 | 차단 |
| Action이 page-level auth redirect/gating에만 의존 | 차단 |
| Action이 raw DB records 또는 internal objects 반환 | 차단 |
| Action이 form/event/transition path가 아니라 render 중 mutation | 차단 |
| Action이 반복 domain authorization logic을 매번 inline 수행 | 경고. DAL로 이동 |
| 필요한 `updateTag`, `revalidatePath`, `revalidateTag` 전에 `redirect()` 사용 | 차단 |
| client code가 `Promise.all`로 Server Actions를 병렬화하고 동시 실행을 기대 | 차단 |
| `revalidateTag(tag, 'max')`가 응답에서 현재 route를 다시 렌더링한다고 가정 | 차단 |
| Server Action 밖에서 `updateTag` 또는 `refresh` 호출 | 차단 |

## DAL Guidance

권장 분리:

- Action: input edge, auth re-check, mutation orchestration, freshness, redirect
- DAL/server-only module: DB access, authorization logic, DTO shaping, sensitive business rules/nextjs

## Security Notes

- auth는 action에 넘겨진 trusted client token이 아니라 cookies 또는 headers에서 읽습니다.
- Server Action return values는 client로 serialize되어 돌아가므로 최소화합니다.
- client 입력은 참조와 변경 내용으로 좁힙니다. schema validation은 형태를 볼 뿐 소유권을 보지 않으므로 세션 기준으로 row를 다시 읽습니다.
- 비용이 큰 actions에는 rate limiting과 abuse controls를 고려합니다.
- Next.js는 `Origin`과 `Host` 또는 `X-Forwarded-Host` 비교, 기본 1MB body 제한, 암호화된 action ID, closure 변수 암호화를 적용합니다.
- proxy나 CDN host에는 `experimental.serverActions.allowedOrigins`를 설정합니다. `*`는 한 라벨, `**`는 한 개 이상 라벨과 맞고 포트는 그대로 적어야 합니다.

## Deployment

- action ID는 source가 그대로여도 최대 14일마다 회전합니다. 이전 build의 client는 더 이상 없는 ID를 호출해 "Failed to find Server Action"을 볼 수 있습니다.
- 인스턴스 사이에서 `NEXT_SERVER_ACTIONS_ENCRYPTION_KEY`를 고정해 action 참조가 어디서나 복호화되게 합니다.
- 사용자가 mutation 중일 수 있으면 급격한 전환보다 rolling deployment를 쓰고, 실패는 단단한 오류가 아니라 재시도 경로로 노출합니다.

## Review Checklist

- input validation 존재
- auth/authz가 action 내부 또는 delegated server-only layer에서 재확인됨
- return values 최소화
- client 호출부가 병렬 dispatch를 가정하지 않음
- 필요할 때 redirect 전 freshness 수행
- 같은 응답 재렌더를 기대하는지에 맞게 freshness 방식을 골랐음
- multi-instance 또는 proxy 배포에서 암호화 키와 origin 설정이 의도적임
- 반복 domain logic이 여러 actions에 중복되지 않음

## Sources

> 확인 2026-11-04. `https://nextjs.org/docs/app/guides/server-actions`, `https://nextjs.org/docs/app/api-reference/config/next-config-js/serverActions`, `https://nextjs.org/docs/app/api-reference/functions/updateTag`, `https://nextjs.org/docs/app/api-reference/functions/revalidateTag`, `https://nextjs.org/docs/app/api-reference/functions/refresh`, `https://nextjs.org/docs/app/guides/data-security`를 확인했습니다. 날짜가 붙은 스냅숏은 `references/official/nextjs/current-docs-2026-11-04.md`입니다.
