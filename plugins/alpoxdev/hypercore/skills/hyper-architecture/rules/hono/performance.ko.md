# 성능

> 배포된 런타임에서 재고, 기본 SmartRouter를 선호하며, 플랫폼이 이미 하지 않는 곳에서만 `compress()`/`etag()`/`cache()`로 전송 바이트를 줄입니다.

Hono 앱에서 지연, 처리량, 번들 크기, 콜드 스타트, 캐싱, "최적화"를 언급할 때 읽습니다. 이 파일은 라우터 선택, 응답 바이트 미들웨어, 공유 캐시 계약을 소유하고, 어느 런타임에서 재는지는 `rules/hono/platform.md`가 소유합니다.

## 먼저 측정

숫자의 의미는 런타임이 정하므로 재기 전에 런타임을 밝힙니다. 로컬 Node 서버, Cloudflare Worker invocation, Deno Deploy isolate는 콜드 스타트와 CPU 예산이 다릅니다.

```bash
# local Node/Bun/Docker target
node dist/index.js &            # or bun run start, or the repo's start script
wrk -t4 -c50 -d20s http://127.0.0.1:3000/<route>
curl -s -o /dev/null -w 'ttfb=%{time_starttransfer}s size=%{size_download}B\n' http://127.0.0.1:3000/<route>
```

- 앱이 실제로 서비스하는 동시성에서 읽기 라우트 하나와 쓰기 라우트 하나의 p50/p95 지연과 초당 요청 수를 기록합니다.
- 압축이나 ETag 변경 전후의 응답 바이트를 기록하고, 런타임이 이미 body를 인코딩하지 않는지 확인합니다.
- 워커 플랫폼에서는 로컬 `wrangler dev`만이 아니라 배포 대상(`wrangler dev --remote` 또는 `deploy` 후 부하 실행)을 잽니다. 플랫폼이 자체 압축, 캐시, CPU 한도를 더하기 때문입니다.
- 2026-11-07 기준 registry `latest` `hono`는 4.13.17이고, 4.13.16은 라우터와 form 검증 결함을 고친 보안 하한으로 남습니다 [L-70]. `package.json`의 설치 version을 기록하고, 확인하지 않은 드리프트를 측정 대상으로 삼지 않습니다.

여기서 측정할 수 없는 레버는 측정하지 못했다고 보고하고 이득으로 주장하지 않습니다.

## 규칙

흔한 영향 순서입니다.

1. **`official` — 측정이 근거가 되기 전에는 기본 `SmartRouter`를 유지합니다.** `SmartRouter`는 라우터를 조립하고 그 소스는 `new SmartRouter({ routers: [new RegExpRouter(), new TrieRouter()] })`입니다. `RegExpRouter`는 pattern을 하나의 regex로 컴파일하며 "JavaScript 세계에서 가장 빠른 라우터"로 설명됩니다 [L-51]. 교체는 `new Hono({ router: new RegExpRouter() })` 생성자 option 하나입니다 [L-52]. `RegExpRouter`는 `TrieRouter`가 받는 pattern을 거부하므로 route 집합을 모르는 채 전역으로 고정하지 않습니다 [L-51].
2. **`official` — 런타임의 실제 비용 모델에 맞춰 라우터를 고릅니다.** `LinearRouter`는 요청마다 초기화하는 런타임용이고 등록이 훨씬 빠릅니다. `TrieRouter`는 모든 pattern을 지원하고 `RegExpRouter`보다 느리지만 Express보다 훨씬 빠릅니다. `PatternRouter`는 가장 작아서 "PatternRouter만 쓰는 애플리케이션은 15KB 미만"입니다 [L-51]. `hono/tiny`는 `PatternRouter` preset이므로 라우트 처리량이 아니라 크기를 삽니다 [L-56].
3. **`official` — 미들웨어와 라우트를 실행 순서대로 등록합니다.** "handler나 middleware는 등록 순서대로 실행됩니다" [L-51]. 넓은 미들웨어를 뒤로 옮기면 그 앞의 모든 라우트에서 동작과 비용이 함께 바뀌므로 mount 표를 명시적으로 유지하고 순서를 바꾼 뒤 다시 측정합니다.
4. **`official` — 이미 압축하는 플랫폼에서는 압축하지 않습니다.** `compress()`는 `Accept-Encoding`에 응답하고 `'gzip'`과 `'deflate'`만 지원하며 기본 임계값은 1024바이트입니다. Cloudflare Workers와 Deno Deploy에서는 "응답 body가 자동으로 압축되므로 이 미들웨어를 쓸 필요가 없습니다" [L-53]. Node 같은 맨 런타임에서는 `contentTypeFilter`(기본값은 export된 `COMPRESSIBLE_CONTENT_TYPE_REGEX`)와 함께 넣어 이미지와 압축 파일을 건너뜁니다 [L-53].
5. **`hypercore-default` — GET이 많은 JSON 라우트에서 304를 반환합니다.** 미들웨어 동작은 공식이고, 그것을 기본 정책으로 삼는 것은 우리 판단입니다. `etag()`는 ETag header를 더하고 일치하는 조건부 요청에 `304`로 답합니다. 기본 유지 header(`Cache-Control`, `Content-Location`, `Date`, `ETag`, `Expires`, `Vary`) 밖의 custom header가 304를 살아남아야 하면 `retainedHeaders`를 넓힙니다 [L-54].
6. **`official` — `cache()`는 인증 뒤에 등록하고 사용자별 캐시 header를 설정합니다.** 이 미들웨어는 Cloudflare custom domain과 Deno 1.26+/Deno Deploy에서 Web Cache API를 쓰며, "캐시는 모든 클라이언트가 공유합니다. 미들웨어는 `Cookie` header를 보지 않습니다" [L-55]. 사용자별 응답에는 `Cache-Control: private`이나 `no-store`, 또는 `vary: 'Cookie'`를 보내고, `maxQueryBodySize`(기본 64 KiB)를 넘는 QUERY 요청은 캐시를 우회한다는 점을 기록합니다 [L-55].
7. **`hypercore-default` — Hono 앱이 page를 서비스하면 Core Web Vitals로 게이트합니다.** LCP ≤ 2.5초, INP ≤ 200ms, CLS ≤ 0.1을 p75 기준으로, mobile과 desktop을 따로 보고합니다 [L-67]. API 전용 앱에는 이 규칙이 적용되지 않으므로 지연을 잽니다.

## 하지 말 것

- 습관처럼 `RegExpRouter`로 바꾸지 않습니다. 가장 빠른 단일 라우터지만 기본 조립이 `TrieRouter`로 되돌리는 pattern을 거부하므로, 측정 없는 교체는 동작하던 라우트를 시작 오류로 만들 수 있습니다 [L-51][L-52].
- 기존 API가 지연 예산을 통과하게 하려고 `hono/tiny`를 채택하지 않습니다. 라우트 처리량을 크기와 맞바꿉니다 [L-56].
- Cloudflare Workers나 Deno Deploy에 `compress()`를 더하고 플랫폼이 이미 준 바이트 감소를 성과로 주장하지 않습니다 [L-53].
- 인증 전에 `cache()`를 켜거나 사용자별 응답에 기본 `Cache-Control`을 두지 않습니다. 캐시가 `Cookie`를 무시하므로 한 사용자의 payload를 다른 사용자에게 서비스합니다 [L-55].
- QUERY body가 `maxQueryBodySize`를 넘는 endpoint 앞에 `cache()`를 두고 cache hit를 기대하지 않습니다 [L-55].
- `etag()`나 `cache()`를 공짜라고 제시하지 않습니다. ETag는 miss마다 body를 읽거나 hash를 계산하고, 공유 캐시는 올바른 private/no-store header가 먼저 있어야 안전합니다 [L-54][L-55].
- 로컬 `wrangler dev` 숫자를 배포 결과로 인용하지 않습니다. 플랫폼이 압축, 캐시, CPU 한도를 더합니다 [L-53][L-55].

## 체크리스트

- [ ] 런타임을 밝혔고 로컬 dev server만이 아니라 그 런타임에서 측정했습니다.
- [ ] 주장하는 모든 이득에 before/after 숫자가 있습니다.
- [ ] 라우터 선택이 기본값이거나, route 집합 제약을 밝힌 측정 근거가 있습니다.
- [ ] 미들웨어와 라우트 등록 순서가 명시되어 있고 다시 측정하지 않고 흔들지 않았습니다.
- [ ] 압축하는 플랫폼에는 `compress()`가 없거나, 그 밖의 런타임에서는 content-type filter와 함께 설정했습니다.
- [ ] 조건부 GET이 중요한 곳에 `etag()`를 적용했고 `retainedHeaders`가 custom header를 덮습니다.
- [ ] `cache()`가 인증 뒤에 있고 사용자별 응답이 `private`/`no-store` 또는 `vary: 'Cookie'`를 가집니다.
- [ ] `maxQueryBodySize`를 넘는 QUERY endpoint가 캐시를 우회함을 알고 있습니다.
- [ ] HTML 응답이 p75에서 CWV 임계값을 만족하거나, API 전용이라 이 항목이 범위 밖임을 명시했습니다.
- [ ] 변경이 `stacks/hono/architecture-rules.md`의 게이트와 `rules/setup/typescript.md`의 검사를 모두 통과시킵니다.

## Sources

> 확인 2026-11-07. 라우터, 미들웨어, 캐시 서술은 Hono 문서와 `hono/tiny` preset 소스에서 확인했고 현재 version은 npm registry에서 가져왔습니다.

| 주장 | 출처 |
|---|---|
| 라우터 목록, `SmartRouter` 조립, 등록 순서, `RegExpRouter` 속도 주장 | [Routers – Hono](https://hono.dev/docs/concepts/routers) |
| `new Hono({ router })` 생성자 option과 기본값 | [Hono API](https://hono.dev/docs/api/hono) |
| `hono/tiny` preset이 `PatternRouter`를 import | [hono/tiny preset source](https://raw.githubusercontent.com/honojs/hono/main/src/preset/tiny.ts) |
| `compress()` 코덱, 기본 임계값, content-type filter, 플랫폼 주의 | [Compress Middleware – Hono](https://hono.dev/docs/middleware/builtin/compress) |
| `etag()` 304 동작과 유지 header | [ETag Middleware – Hono](https://hono.dev/docs/middleware/builtin/etag) |
| `cache()` 플랫폼 지원, 공유 캐시, `Cookie` 주의, `maxQueryBodySize` | [Cache Middleware – Hono](https://hono.dev/docs/middleware/builtin/cache) |
| p75 기준 Core Web Vitals 임계값 | [Web Vitals](https://web.dev/articles/vitals) |
| registry `latest` `hono` 4.13.17 | [npm registry: hono](https://registry.npmjs.org/hono) |
