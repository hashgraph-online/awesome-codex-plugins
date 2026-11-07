# 실행 모델

> Vite + TanStack Router route 코드의 런타임 경계 규칙

---

## 핵심 규칙

route module이나 loader를 private server boundary처럼 취급하지 않습니다.

일반적인 SPA-only Vite 앱에서는 loader가 브라우저 탐색 중 실행됩니다. 저장소가 나중에 SSR 또는 manual server rendering을 추가하면 같은 loader가 서버 렌더에도 참여할 수 있습니다. 따라서 어떤 경우에도 안전한 코드만 loader에 둡니다.

---

## 비타협 규칙

| 확인 항목 | 규칙 |
|-----------|------|
| loader 또는 route module이 secret, DB client, filesystem, privileged SDK를 직접 읽음? | 차단 |
| 클라이언트에서 도달 가능한 코드가 `VITE_`가 아닌 env 값을 읽음? | 차단 |
| 브라우저 전용 API를 module scope나 shared route utility에서 경계 없이 사용함? | 차단 |
| module-level side effect가 브라우저 전역 객체에 의존함? | 차단 |
| loader가 service layer를 우회해 직접 네트워킹을 수행함? | 차단. `services/`로 이동 |

---

## 안전한 패턴

- route loader는 service가 소유한 query options에 대해 `queryClient.query({ ...options, staleTime: 'static' })`를 호출합니다
- 브라우저 전용 동작은 component, hook, effect 또는 명시적 client-only wrapper 안에 둡니다
- 공개 가능한 런타임 설정은 `import.meta.env.VITE_*`를 사용합니다
- private secret은 실제 backend/API 경계 뒤에 둡니다

---

## 리뷰 체크리스트

- loader 또는 route module이 secret/private env를 직접 읽지 않음
- route 코드가 DB client나 privileged SDK를 import하지 않음
- 브라우저 전용 코드가 module scope에서 실행되지 않음
- loader의 네트워킹이 service/query-option 헬퍼 뒤에 있음

---

## Sources

> route module과 loader의 client-reachability, client env에 `VITE_`만 허용하는 규칙은 `references/official/vite/current-docs-2026-11-04.ko.md`에 기록된 dated snapshot에서 왔고, 그 스냅샷이 기록한 자체 검증일은 2026-11-04입니다. server render 주의점과 loader 네트워킹을 service helper 뒤로 두는 규칙은 이 패키지 자체의 guidance이자 Hypercore/repo-local convention이며 스냅샷에서 가져온 사실이 아닙니다. 이 파일을 위해 페이지를 다시 가져오지 않았습니다. 규칙 문장과 저장소 로컬 경로 확인 2026-11-04.
