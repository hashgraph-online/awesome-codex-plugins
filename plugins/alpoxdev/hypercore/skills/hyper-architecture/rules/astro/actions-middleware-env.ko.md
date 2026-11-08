# Actions, 미들웨어, 세션, 환경 변수

> 모든 Action을 공개 POST 엔드포인트로 취급하고, 요청 상태는 타입이 붙은 `locals`로 공유하며, 세션은 드라이버를 먼저 확인한 뒤 쓰고, 환경 변수는 모두 `astro:env` 스키마에 선언합니다.

이 파일의 규칙은 날짜가 붙은 스냅숏에서 연 페이지가 그대로 진술한 경우 `official`, 이 패키지가 기본값으로 고른 경우 `hypercore-default`로 표시합니다.

## 1. Actions

`official` — Action은 `src/actions/index.ts`에 있고, 이 파일이 `defineAction({ input, handler })`로 만든 `server` 객체를 export합니다(L-11, L-12).

```ts
import { defineAction, ActionError } from 'astro:actions';
import { z } from 'astro/zod';

export const server = {
  logout: defineAction({
    handler: async (_input, context) => {
      const session = context.session;
      if (!session?.get('user')) {
        throw new ActionError({ code: 'UNAUTHORIZED', message: 'Not signed in' });
      }
      session.destroy();
      return { ok: true };
    },
  }),

  renameProject: defineAction({
    input: z.object({ id: z.string(), name: z.string().min(1).max(80) }),
    handler: async (input) => ({ ...input, updated: true }),
  }),
};
```

규칙:

- `official` — Action은 서버 출력을 요구합니다. 정적 전용 출력에서는 Astro가 `ActionsWithoutServerOutputError`를 던집니다(L-57).
- `official` — Action URL은 `/_actions/<name>`으로 공개됩니다. 문서는 "you must use the same authorization checks that you would consider for API endpoints"라고 밝힙니다(L-11).
- `official` — `input`은 Zod 검증기이고, 실패하면 핸들러를 호출하지 않고 `BAD_REQUEST`를 돌려줍니다.
- `official` — `input`이 없으면 JSON 요청은 `unknown`을, form 요청은 `FormData`를 받습니다. `accept: 'form'`은 FormData Action을 선언합니다.
- `official` — JavaScript 없는 form은 온디맨드 렌더 페이지에서 `<form method="POST" action={actions.logout}>`로 동작하고, 결과는 `Astro.getActionResult()`로 읽습니다.
- `official` — 권한 실패에는 `ActionError({ code: 'UNAUTHORIZED' })`를 던지고, 모든 Action에 적용되는 검사라면 미들웨어 수준에서 `getActionContext(context)`로 막습니다.
- `hypercore-default` — Action은 도메인별로 `src/actions/<domain>.ts`에 나누고 `src/actions/index.ts`에서 다시 export합니다. 그 `server` 객체 밖의 것은 호출할 수 없습니다.
- `hypercore-default` — 사소하지 않은 입력은 모두 Zod로 검증하고, 미들웨어가 라우트를 막더라도 핸들러 안에서 권한을 확인합니다. 미들웨어가 Action을 인식하지 않으면 `/_actions/<name>` 직접 호출로 우회될 수 있습니다.

## 2. Middleware

`official` — 미들웨어는 `src/middleware.ts` 또는 `src/middleware/index.ts`에 있고 명명된 `onRequest`를 export합니다(L-13).

```ts
import { defineMiddleware, sequence } from 'astro:middleware';

const auth = defineMiddleware(async (context, next) => {
  const session = context.session;
  context.locals.user = session?.get('user') ?? null;
  return next();
});

const timing = defineMiddleware(async (_context, next) => {
  const start = performance.now();
  const response = await next();
  response.headers.set('x-render-ms', String(performance.now() - start));
  return response;
});

export const onRequest = sequence(auth, timing);
```

규칙:

- `official` — export는 default가 아니라 명명된 `onRequest`입니다.
- `official` — `context.locals`는 요청마다 새로 만들어지고 재할당할 수 없습니다. 필드를 채웁니다.
- `official` — `locals`는 `src/env.d.ts`에서 `declare namespace App { interface Locals { user: User | null } }`로 타입을 붙입니다.
- `official` — 미들웨어는 `sequence(a, b, c)`로 조합하고, 순서가 실행 순서입니다.
- `hypercore-default` — 권한 확인과 값 가리기를 미들웨어에 두는 것은 라우트 그룹 전체에 적용되는 규칙일 때만입니다. 상태를 바꾸는 Action 안의 확인은 그대로 남깁니다.
- `hypercore-default` — 미들웨어에 페이지 렌더링 관심사를 넣지 않습니다. 요청을 정규화하고 신원을 해석해 `locals`를 채우며, 페이지는 `locals`를 읽습니다.

## 3. Sessions

`official` — 세션(5.7+)은 `Astro.session` 또는 `context.session`으로 읽고 쓰며 `get`, `set`, `regenerate`, `destroy`를 씁니다(L-14).

- `official` — 세션에는 드라이버가 필요합니다. Node, Cloudflare, Netlify 어댑터는 자동으로 설정하고 Vercel은 명시 설정이 필요합니다.
- `official` — `session: false`(7.2+)는 런타임과 어댑터의 기본 드라이버를 제거합니다.
- `official` — 로그인처럼 권한이 바뀌는 지점 뒤에 `regenerate()`를 호출하고, 로그아웃에는 `destroy()`를 호출합니다.
- `hypercore-default` — 세션에는 식별자만 저장하고 사용자 레코드 전체를 넣지 않습니다. 요청마다 레코드를 다시 읽어야 권한 회수가 즉시 반영됩니다.

## 4. Environment variables

`official` — 변수는 `astro.config.*`의 `env.schema`에 선언하고 `astro:env/client` 또는 `astro:env/server`에서 import합니다(L-15, L-17).

```js
import { defineConfig, envField } from 'astro/config';

export default defineConfig({
  env: {
    schema: {
      PUBLIC_API_URL: envField.string({ context: 'client', access: 'public' }),
      API_SECRET: envField.string({ context: 'server', access: 'secret' }),
      PORT: envField.number({ context: 'server', access: 'public', default: 4321 }),
      MODE: envField.enum({
        context: 'server',
        access: 'public',
        values: ['development', 'staging', 'production'],
      }),
    },
    validateSecrets: true,
  },
});
```

규칙:

- `official` — 필드 도우미는 `envField.string`, `number`, `boolean`, `enum`이고, 각각 `context: 'client' | 'server'`, `access: 'public' | 'secret'`, 선택적 `optional`/`default`를 받습니다.
- `official` — `context: 'client'` 필드는 절대 `access: 'secret'`일 수 없습니다. 문서는 이것을 설계상 불가능하다고 부릅니다("no safe way to send this data to the client").
- `official` — 비밀 값은 무엇이든 `astro:env/server`를 import할 때 검증되므로 빌드에 자리 표시 값이 필요할 수 있습니다. `env.validateSecrets: true`는 dev와 빌드 시작 시점에 검증합니다.
- `official` — `astro:env`는 `astro.config.mjs`나 단독 스크립트에서 쓸 수 없습니다. 그곳에서는 `process.env`를 씁니다.
- `official` — `getSecret('KEY')`는 원시 값을 프로그램으로 읽습니다. 어댑터가 제공하며 기본값은 `process.env`입니다.
- `official` — `import.meta.env.PUBLIC_*`는 여전히 동작하고 클라이언트에 보이지만, 그 경로로 클라이언트에 도달하는 것은 `PUBLIC_` 접두사가 붙은 변수뿐입니다.
- `official` — `astro:env`의 공개 클라이언트 변수는 `PUBLIC_` 접두사와 무관하게 스키마에서 클라이언트 번들로 컴파일됩니다.
- `hypercore-default` — 모든 변수를 스키마에 선언하고 `astro:env`에서 import합니다. 공유 코드에서 `import.meta.env`로 비밀 값을 읽지 않습니다. 그 경로에는 검증도 문맥 보장도 없습니다.

## 5. Security settings

`official` — `security.checkOrigin`은 기본값이 `true`인 CSRF 방어입니다. 콘텐츠 타입이 없거나 form 호환 타입인 `POST`/`PATCH`/`DELETE`/`PUT` 요청에 대해 `Sec-Fetch-Site`(없으면 `Origin`)를 확인하고, 교차 출처 요청에는 403을 돌려줍니다(L-17).

| 설정 | 기본값 | 효과 |
|---|---|---|
| `security.checkOrigin` | `true` | 안전하지 않은 메서드의 CSRF 방어 |
| `security.allowedDomains` | 없음 | `X-Forwarded-Host`를 허용 패턴과 대조 |
| `security.csp` | `false` | Astro 출력의 해시를 담은 페이지별 CSP `<meta>` 출력 |
| `security.actionBodySizeLimit` | 1MB | Action 요청 본문 상한 |
| `security.serverIslandBodySizeLimit` | 1MB | 서버 아일랜드 요청 본문 상한 |

규칙:

- `official` — 기록된 이유가 없으면 `checkOrigin`을 켜 둡니다.
- `official` — `allowedDomains`는 `X-Forwarded-Host`를 다시 쓰는 프록시나 CDN 뒤에서 설정합니다. 일치하지 않는 헤더는 무시되고 원래 호스트를 씁니다.
- `official` — CSP는 Astro가 내보낸 스크립트와 스타일의 해시를 담아 페이지마다 `<meta http-equiv="content-security-policy">`를 출력합니다. `algorithm`은 `'SHA-256'`, `'SHA-384'`, `'SHA-512'`를 받고 `directives`는 추가 지시어를 받습니다.
- `official` — CSP 제한: 외부 스크립트와 스타일은 직접 해시를 넣어야 하고, `<ClientRouter />` 뷰 전환은 지원되지 않으며, Shiki는 지원되지 않고(Prism 사용), `'unsafe-inline'`은 해당 지시어의 해시를 무력화하며, 개발 모드에서는 동작하지 않으므로 빌드와 preview로 시험합니다.
- `official` — 문서화된 것은 meta 태그 방식뿐입니다. 이 출처로 헤더 기반 CSP 전달을 주장하지 않습니다.
- `hypercore-default` — `<ClientRouter />`와 `security.csp`를 함께 켜지 않습니다. 그 조합은 지원되지 않습니다.

## 6. Advanced routing in `src/fetch.ts`

`official` — `src/fetch.ts`는 `Fetchable`을 만족하는 `{ async fetch(request) { ... } }`를 default export하고 `.ts`, `.js`, `.mjs`, `.mts`를 지원합니다(L-06, L-17, L-32).

- `official` — 기본 파이프라인 순서는 트레일링 슬래시 정규화, 리다이렉트, 세션, 액션, 사용자 미들웨어, 페이지 렌더링, i18n, 캐싱입니다.
- `official` — `astro/fetch`의 `astro()`는 pre/post 훅과 함께 내장 파이프라인 전체를 돌립니다. 개별 핸들러를 직접 조합할 수 있고, `astro/hono`는 같은 이름을 Hono 미들웨어로 export합니다.
- `official` — 들어오는 `url.pathname`은 "is not guaranteed to be the same as the route Astro matches internally"이므로 pathname 접두사 검사는 우회될 수 있습니다.
- `official` — 커스텀 워커 진입점에서 `notFound()`(7.4)는 `pages()`보다 앞에 있어야 합니다. 그렇지 않으면 매칭되지 않은 라우트가 `X-Astro-Error`와 함께 빈 404를 돌려줍니다.
- `official` — `fetchFile: null | 'handler'`는 예약 파일의 이름을 바꾸거나 비활성화합니다.
- `hypercore-default` — `src/fetch.ts`에서 `url.pathname` 접두사로 권한을 판정하지 않습니다. 라우트 매칭이 권위를 갖도록 `astro/hono` 핸들러를 조합합니다.

## 7. What not to do

- 정적 전용 출력 프로젝트에 Action을 추가하지 않습니다.
- Zod 스키마 없이 `FormData`나 JSON 입력을 신뢰하지 않습니다.
- Action에 페이지 수준 인증을 기대지 않습니다. `/_actions/<name>`은 직접 도달할 수 있습니다.
- `context.locals`를 재할당하지 않고 필드를 채웁니다.
- 미들웨어를 default 함수로 export하지 않습니다.
- 드라이버 없이 세션을 읽거나 쓰지 않습니다.
- `context: 'client'`에 `access: 'secret'`을 선언하지 않습니다.
- `<ClientRouter />`와 `security.csp`를 함께 켜지 않습니다.
- `src/fetch.ts`에서 `url.pathname` 접두사로 권한을 판정하지 않습니다.

## Checklist

- [ ] Action이 `src/actions/`에 있고, Zod로 입력을 검증하며, 핸들러나 Action 인식 미들웨어 게이트에서 권한을 확인합니다.
- [ ] Action은 어댑터와 서버 출력이 있는 프로젝트에서만 씁니다.
- [ ] 미들웨어가 명명된 `onRequest`를 export하고 `sequence()`로 조합하며 `locals`를 재할당하지 않습니다.
- [ ] `App.Locals`를 `src/env.d.ts`에 선언했고 미들웨어가 쓰는 값과 맞습니다.
- [ ] 세션에 드라이버가 있고 권한 변경 시 `regenerate()`/`destroy()`가 돕니다.
- [ ] 모든 환경 변수를 `env.schema`에 선언하고 `astro:env/client` 또는 `astro:env/server`에서 import합니다.
- [ ] 클라이언트 문맥 필드가 비밀이 아니고, `import.meta.env`로 비밀 값을 읽지 않습니다.
- [ ] `checkOrigin`이 켜져 있고, 프록시 뒤에서 `allowedDomains`를 설정했으며, CSP를 `<ClientRouter />`와 함께 쓰지 않습니다.
- [ ] `src/fetch.ts` 권한 판정이 pathname 접두사에 기대지 않습니다.

## Sources

> Checked 2026-11-07. 사실은 2026-11-07에 해당 페이지를 연 Astro 조사 레인에서 나왔고, 레인 출처 id를 괄호에 남겼습니다.

| Claim | Source |
|---|---|
| `src/actions/index.ts`의 Actions, `defineAction`, `server` 객체 (L-11, L-12) | https://docs.astro.build/en/guides/actions/ |
| Action은 서버 출력을 요구하고 `ActionsWithoutServerOutputError`를 던집니다 (L-57) | https://docs.astro.build/en/reference/errors/actions-without-server-output-error/ |
| Action URL은 `/_actions/<name>`으로 공개되고 API 수준 권한이 필요합니다 (L-11) | https://docs.astro.build/en/guides/actions/ |
| `input` Zod 검증, 핸들러 이전 `BAD_REQUEST`, `accept: 'form'` (L-11, L-12) | https://docs.astro.build/en/reference/modules/astro-actions/ |
| JavaScript 없는 form과 `Astro.getActionResult()` (L-11) | https://docs.astro.build/en/guides/actions/ |
| 명명된 `onRequest`, `defineMiddleware()`, `sequence()`, `context.locals` 타입 (L-13) | https://docs.astro.build/en/guides/middleware/ |
| 세션 API, 드라이버 요구, 어댑터 기본값, `session: false` (L-14, L-17, L-50) | https://docs.astro.build/en/guides/sessions/ |
| `env.schema` 필드 도우미, context/access 조합, 불가능한 클라이언트 비밀 값 (L-15, L-17) | https://docs.astro.build/en/guides/environment-variables/ |
| import 시점 비밀 값 검증과 `env.validateSecrets` (L-15, L-17) | https://docs.astro.build/en/guides/environment-variables/ |
| config나 단독 스크립트에서 `astro:env`를 쓸 수 없음, `getSecret()` (L-15, L-16) | https://docs.astro.build/en/reference/modules/astro-env/ |
| `import.meta.env.PUBLIC_*`와 스키마 기반 클라이언트 컴파일 (L-15) | https://docs.astro.build/en/guides/environment-variables/ |
| `security.checkOrigin`, `allowedDomains`, CSP 방식과 제한, 본문 크기 상한 (L-17, L-50) | https://docs.astro.build/en/reference/configuration-reference/ |
| `src/fetch.ts` 파이프라인 순서, `astro/fetch`와 `astro/hono` 조합, pathname 주의 (L-06, L-32, L-33) | https://docs.astro.build/en/reference/modules/astro-fetch/ |
| 커스텀 진입점에서 `pages()`보다 앞선 `notFound()` (L-50) | https://docs.astro.build/en/reference/modules/astro-fetch/ |
