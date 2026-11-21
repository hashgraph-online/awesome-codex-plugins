# SSR And Hydration

> 라우트 SSR 모드와 hydration 안전성 규칙

---

## Rule Classifications

| Rule | Classification | Enforcement |
|---|---|---|
| route SSR option과 `ClientOnly`는 official Start concept | Official | deliberate usage |
| deterministic first render | Safety policy | hydration-unsafe output 차단 |
| SSR disable 전 stabilization 선호 | Hypercore convention | touched route에 적용 |

---

## 핵심 규칙

서버 HTML과 클라이언트 첫 렌더가 달라질 수 있으면, 단순 경고가 아니라 설계 문제로 취급해야 합니다.

---

## 비타협 규칙

| 확인 항목 | 규칙 |
|------|------|
| 첫 렌더에서 `Date.now()`, random ID, locale 의존 텍스트, viewport 분기 같은 불안정 값을 직접 렌더함? | 안정화되지 않았다면 차단 |
| 브라우저 전용 위젯을 `ClientOnly`나 SSR 제한 없이 SSR에 렌더함? | 차단 |
| `ssr: false` 또는 `ssr: 'data-only'`를 fallback 전략 없이 사용함? | 차단 |
| 루트에서 SSR을 끄면서 `shellComponent` 동작을 이해하지 못함? | 차단 |

---

## 선호하는 해결 순서

1. 서버와 클라이언트 출력이 결정적으로 같게 만든다
2. 서버에서 한 번 계산해서 loader data로 hydration한다
3. 진짜 브라우저 전용 UI만 `ClientOnly`로 감싼다
4. 꼭 필요할 때만 route `ssr: 'data-only'` 또는 `ssr: false`를 쓴다
5. `ClientOnly`보다 `useHydrated()`를, route SSR을 끄기보다 `ClientOnly`를 먼저 검토한다

---

## 허용 패턴

- locale/timezone 민감 UI는 cookie 기반의 결정적 서버 값을 사용합니다
- hydration 후 클라이언트 환경을 cookie로 저장해 이후 SSR 요청에 활용할 수 있습니다
- 불안정한 위젯은 `ClientOnly`로 감쌀 수 있습니다
- hydration 전후로 달라야 하는 값 하나만 다룰 때는 `@tanstack/react-router`의 `useHydrated()`를 우선합니다. SSR과 첫 client render에서 `false`, hydration 뒤에 `true`가 되므로 subtree 전체를 `ClientOnly`로 감싸는 것보다 좁습니다
- `ssr`에는 함수형도 있습니다. `ssr: ({ params, search }) => false | 'data-only' | true`는 초기 request의 서버에서만 실행되고 client bundle에서는 제거됩니다. `params`와 `search`는 `{ status: 'success', value }` 또는 `{ status: 'error', error }`로 들어오므로 error 분기를 처리해야 합니다
- 하위 route는 상속받은 `ssr` 모드를 더 제한하는 방향으로만 바꿀 수 있습니다. `true`는 `'data-only'`나 `false`가 될 수 있고 `'data-only'`는 `false`가 될 수 있지만 반대 방향은 안 됩니다
- `ssr: false` 또는 `ssr: 'data-only'`인 첫 route는 `pendingComponent`(없으면 `defaultPendingComponent`)를 최소 `minPendingMs` 동안 렌더합니다
- SSR 모드가 렌더링 동작을 바꾸는 라우트에는 `pendingComponent`를 둡니다
- 루트 라우트에서 SSR을 줄여도 `shellComponent`는 HTML shell을 렌더한다는 점을 이해해야 합니다

---

## 리뷰 체크리스트

- hydration에 unsafe한 첫 렌더 출력이 없음
- `ClientOnly`가 무분별한 탈출구가 아니라 의도적으로 쓰였음
- 불안정 라우트의 `ssr` 모드가 명시적이고, 함수형 `ssr`는 `{ status: 'error' }` 분기를 처리함
- hydration 민감 값 하나에는 subtree 전체 `ClientOnly` 대신 `useHydrated()`를 씀
- SSR 축소 라우트의 fallback/shell 동작을 이해하고 있음

## Sources

> 출처 확인 2026-11-04: <https://tanstack.com/start/latest/docs/framework/react/guide/selective-ssr.md>(`ssr` 모드, 함수형, 상속 제한 방향, `pendingComponent`/`minPendingMs`), <https://tanstack.com/start/latest/docs/framework/react/guide/execution-model.md>(`useHydrated`), <https://tanstack.com/start/latest/docs/framework/react/guide/hydration-errors.md>(불일치 원인과 cookie 기반 해결). 그 밖의 공식 TanStack 동작은 이 패키지 자체의 snapshot(`references/official/tanstack-start/tanstack-start-2026-11-04.md`, `references/official/tanstack-start/tanstack-router-2026-11-04.md`, `references/official/tanstack-start/current-docs-2026-11-04.md`)에 위임합니다. 공식 사실 검증 2026-11-04. 저장소 로컬 링크 확인 2026-11-04.
