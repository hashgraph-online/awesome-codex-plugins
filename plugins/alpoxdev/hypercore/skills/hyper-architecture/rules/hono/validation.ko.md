# Validation

> Hono 요청 검증 규칙

---

## Stable package 기준

2026-11-04 확인 기준으로 `@hono/zod-validator` 0.9.1은 Hono `>=4.11.2`와 Zod `^3.25.0 || ^4.0.0`을 지원하고, `@hono/standard-validator` 0.4.1은 Hono `>=4.11.2`와 Standard Schema `^1.0.0`을 지원합니다. 이 파일의 Hono 하한은 `4.13.16`입니다. 그 아래 version은 `charset` 같은 추가 parameter가 붙은 `multipart/form-data` 요청에서 `validator('form')` 검증을 건너뜁니다. API나 syntax를 적용하기 전에 installed lockfile을 조사합니다.

- Behavior에 영향을 주는 외부 제어 `param`, `query`, `header`, `cookie`, `json`, `form` 값을 모두 검증합니다.
- Validator output은 `c.req.valid(target)`으로만 소비하고 같은 body를 다시 parse하지 않습니다.
- Header schema key는 lowercase여야 합니다.
- JSON validation에는 적절한 `Content-Type`이 필요합니다. 누락/오류 content type과 malformed body를 test합니다.
- Form과 multipart validation은 `charset`이나 boundary parameter가 붙은 실제 `multipart/form-data` 요청으로 검사합니다. Hono 4.13.16 미만에서는 validator가 빈 객체를 보는 동안 handler는 모든 field를 읽으므로, 평범한 test는 통과하면서 validation이 우회됩니다.
- API surface마다 hook/error behavior를 하나로 정해 validation error가 안정적이고 민감정보 없는 envelope를 공유하게 합니다.
- Coercion/default는 의도적으로 사용합니다. Query/path input은 string에서 시작하며 예상하지 못한 domain semantics를 만들면 안 됩니다.
- 이 skill에 맞추기 위해 validation library를 새로 추가하거나 교체하지 않습니다.
## 핵심 규칙

서비스 로직이 요청 데이터를 소비하기 전에 먼저 검증합니다.

## 허용 옵션

- 좁은 범위 검증에는 `validator()`
- 저장소가 Zod를 쓰면 `@hono/zod-validator`
- 저장소가 Standard Schema 계열을 표준화했다면 `@hono/standard-validator`

`@hono/standard-validator` 0.4.0은 form 단위와 field 단위 오류를 path로 정렬하는 `flattenErrors`를 추가했습니다. 0.4.1은 `header` validation의 기본 400 body에서 `cookie` header를 빼므로, custom error payload에 raw request header를 다시 넣지 않습니다.

## 예시

```ts
import { z } from 'zod'
import { zValidator } from '@hono/zod-validator'

const createUserSchema = z.object({
  email: z.email(),
  name: z.string().min(1),
})

const app = new Hono().post(
  '/',
  zValidator('json', createUserSchema),
  async (c) => {
    const payload = c.req.valid('json')
    return c.json({ payload }, 201)
  }
)
```

## 리뷰 체크리스트

- params/query/json/form이 의미 있는 경우 validator middleware 사용
- form과 multipart route에 content-type 추가 parameter를 넣은 회귀 test가 있음
- validation이 domain logic보다 먼저 실행
- 한 기능 안에서 이유 없이 validation 스타일을 섞지 않음
- 필요 없는 새 dependency 추가 금지
- `validator('form')`을 쓰는 곳의 Hono가 최소 4.13.16


## Sources

> Checked 2026-11-04.

| 주장 | 출처 |
|---|---|
| validator package version과 peer 범위 | [npm registry: `@hono/zod-validator`](https://registry.npmjs.org/@hono/zod-validator), [npm registry: `@hono/standard-validator`](https://registry.npmjs.org/@hono/standard-validator) |
| `validator('form')` multipart 우회와 4.13.16 수정 | [`hono` v4.13.16 release](https://github.com/honojs/hono/releases/tag/v4.13.16) |
| `flattenErrors`와 400 body에서 `cookie` header 제거 | [`@hono/standard-validator` releases](https://github.com/honojs/middleware/releases) |
| Middleware 기반 validation과 third-party validator 권장 | [Validation Guide](https://hono.dev/docs/guides/validation) |
