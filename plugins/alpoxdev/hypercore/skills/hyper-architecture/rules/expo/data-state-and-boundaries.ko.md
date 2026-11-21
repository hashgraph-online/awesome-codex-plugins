# Data, State와 Boundary

server state, client state, persistence, dependency 방향을 바꿀 때 읽습니다. 이 파일은 state ownership, runtime boundary, transport 계약, offline 규칙을 소유합니다.

## Owner별 state 분리

- **Server state**: remote cache, request status, invalidation, retry. Query/data layer에 두고 전역 client state로 통째로 복제하지 않습니다.
- **Feature/UI state**: 그 state를 조정하는 가장 작은 screen/feature가 소유하는 일시적 상호작용 state.
- **Form state**: form workflow 안에 있는 input, validation, dirty/submission lifecycle.
- **Persisted device state**: versioning/migration과 failure handling을 갖춘 의도적 storage schema.
- **Session secret**: secure-storage adapter 뒤의 최소한의 값이며 일반 persistence store에 두지 않습니다.

Library 선택은 설치 project 근거와 요구사항으로 정합니다. 이 스킬은 TanStack Query, Zustand, Redux, form/schema library를 강제하지 않습니다.

## Runtime boundary

TypeScript type은 runtime data를 검증하지 않습니다. API response, deep link, push payload, persisted record, environment 값, native-module 결과를 entry boundary에서 검증합니다. 의미가 다르면 transport DTO를 domain model로 변환합니다. Network/auth/domain error는 presentation 전에 정규화합니다.

Feature application code는 screen global이 아니라 `AuthRepository` 같은 port나 좁은 API module에 의존합니다. Infrastructure가 그 port를 구현합니다. 사소한 호출에 추측성 repository layer를 만들지 않고, substitution, test, mapping, caching, platform divergence가 실제로 있을 때 추상화를 더합니다.

## Transport

`expo/fetch`가 SDK 56부터 `globalThis.fetch`로 설치되며 `AbortSignal.timeout`과 `AbortSignal.any`를 지원하는 WinterTC 준수 구현입니다. 그 위에 두 번째 fetch polyfill을 더하지 않습니다. Opt-out에는 `EXPO_PUBLIC_USE_RN_FETCH=1`이 필요하고 이는 기본값이 아니라 의도적인 migration 결정입니다. Test에서 network를 mock할 때는 fetch 경계에서 mock하고, 다른 구현이 아니라 abort와 timeout 같은 `expo/fetch` 동작을 기준으로 검증합니다.

Base URL, header, auth refresh, cancellation, timeout, error 정규화를 한곳에 모읍니다. Token이나 sensitive payload를 log에 남기지 않습니다. Retry는 safe/idempotent 작업에만 정의하고 app background/network 전환을 의도적으로 처리합니다.

## Persistence API

`expo-file-system`과 `expo-sqlite` API는 동기/비동기 write를 나누므로 storage adapter가 이를 지켜야 합니다.

- SDK 58에서 `File.write()`는 async이고 동기 경로는 `File.writeSync()`입니다. 반환 promise를 버리는 adapter는 write를 조용히 잃습니다.
- `File.copy()`와 `File.move()`는 SDK 56에서 async가 되었습니다.
- `expo-sqlite`는 libSQL을 더 이상 지원하지 않습니다. `syncLibSQL()`, `libSQLOptions`, `useLibSQL` plugin property는 제거되었거나 무효입니다.
- `File.md5`는 `File.digest()`로 deprecated입니다.

Offline persistence가 필요하면 source of truth, conflict 정책, queue idempotency, schema migration, encryption 요구, recovery를 정의합니다. Caching만으로 offline-first 동작을 주장하지 않습니다.

## Configuration

Public environment variable은 하나의 검증된 config module로 읽습니다. `EXPO_PUBLIC_*`는 client에 보이는 bundled data입니다. Server secret과 signing credential은 app bundle 밖에 둡니다.

다음 세 가지 inlining 제약은 style 선호가 아니라 architecture 규칙입니다.

- `process.env.EXPO_PUBLIC_API_URL` 같은 정적 dot access만 build 시점에 치환됩니다. 계산된 접근(`process.env['EXPO_PUBLIC_API_URL']`)과 `const { EXPO_PUBLIC_X } = process.env` 같은 구조 분해는 치환되지 않습니다.
- `node_modules` 안의 code는 재작성되지 않으므로 library가 자기 module을 통해 app의 public variable을 읽을 수 없습니다.
- Inline된 값은 transform cache에 기록되므로 값이 바뀌면 cached output이 무효화됩니다. 따라서 오래된 값은 variable 누락이 아니라 stale cache를 뜻합니다.

필요한 config는 값 노출 없이 적절한 build/runtime 경로에서 일찍 실패시킵니다.

## Sources

> 확인 2026-11-04. 이 서술은 이 패키지의 공식 snapshot `references/official/expo/expo-react-native-2026-11-04.md`를 재진술한 것이며, 그 파일이 다음 URL을 인용합니다: https://docs.expo.dev/guides/environment-variables/, https://expo.dev/changelog/sdk-56, https://expo.dev/changelog/sdk-58, https://docs.expo.dev/versions/v58.0.0/sdk/filesystem/..
