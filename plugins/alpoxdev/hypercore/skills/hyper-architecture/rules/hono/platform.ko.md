# 플랫폼 설정

> adapter와 runtime 관심사는 edge에 격리

---

## Stable runtime 기준

2026-11-07 확인 기준 Hono는 4.13.17이고(4.13.16은 라우터와 form 검증 결함을 고친 보안 하한으로 남습니다) `@hono/node-server`는 2.1.6입니다. Adapter는 Node `>=20`과 Hono `^4 || ^5.0.0-0`을 요구하며, 이 package manifest가 아직 18.x 최소 버전을 적고 있는 Node.js guide page보다 엄격합니다. Installed package metadata와 선택한 runtime의 최신 공식 guide가 우선합니다.

- Cloudflare/Deno/Bun runtime은 일반적으로 Fetch-compatible app entry를 제공하고 Node는 공식 adapter를 사용합니다.
- Adapter는 자체 package에서 가져옵니다(`@hono/bun`, `@hono/deno`, `@hono/cloudflare-workers`, `@hono/aws-lambda`, `@hono/lambda-edge`, `@hono/netlify`, `@hono/vercel`, `@hono/service-worker`). `hono/<adapter>`는 v4에서 동작하지만 deprecated이고 v5에서 제거되므로 새 code에 추가하지 않습니다. `hono/cloudflare-pages`는 대체 package가 없습니다.
- Node WebSocket은 `@hono/node-server`에 내장되어 있습니다. `ws`를 설치하고 `{ noServer: true }`로 `WebSocketServer`를 만든 뒤 `serve()`에 `websocket: { server: wss }`로 넘기고, `@hono/node-server`의 `upgradeWebSocket`을 사용합니다. `@hono/node-ws`는 deprecated입니다.
- `app.fetch` 또는 reusable Hono app을 process startup, listener, WebSocket server, static-file root, shutdown hook과 분리합니다.
- Node raw request/response API, Cloudflare `executionCtx`/binding, provider-specific wait-until behavior를 adapter capability로 취급합니다.
- `serveStatic`은 `GET`과 `HEAD`만 제공하고, decoding 후에도 `%`가 남은 path를 거부하며, 이름에 literal `%`가 든 file을 제공하려면 `allowPercentInPath: true`가 필요합니다. 이 option은 path 단위 middleware를 우회할 수 있으므로 접근 제어는 static handler가 제공하는 것과 같은 pattern에 걸어야 합니다.
- 가능하면 startup에서 environment configuration을 검증합니다. Secret을 client-visible config, log, generated OpenAPI example에 넣지 않습니다.
- Streaming, WebSocket, static file, raw API, execution context, provider binding을 사용하면 runtime adapter를 test합니다. `app.request()`만으로 충분하지 않습니다.
- 명시적 scope와 provider-specific verification 없이 adapter, deployment manifest, compatibility date, runtime version을 바꾸지 않습니다.

## 규칙

- runtime adapter 코드는 `src/index.ts`, `src/server.ts`, `src/worker.ts` 같은 entry 파일에 둡니다
- route module은 가능하면 adapter에 독립적으로 유지합니다
- adapter import는 `@hono/*` package에서 가져오고 deprecated된 `hono/<adapter>` subpath를 쓰지 않습니다
- 환경 bindings/config는 명시적으로 타입화합니다
- Database binding과 connection string은 feature handler가 아니라 platform/config boundary를 통해 읽습니다
- Runtime에 맞는 database client를 사용합니다. D1 같은 Workers binding은 Hono `Bindings` / `c.env`, Node/Bun server runtime은 validated config를 사용합니다
- `showRoutes()` 같은 helper는 dev-only
- `basePath()` 또는 API version prefix는 composition boundary에서 의도적으로 정의합니다
- static file 접근 제어는 static handler가 제공하는 것과 같은 path pattern에 적용하고, `allowPercentInPath`를 권한 우회 수단으로 쓰지 않습니다

## 리뷰 체크리스트

- adapter import가 route module에 섞이지 않음
- adapter import가 `@hono/*` package에서 오고 deprecated된 `hono/<adapter>` subpath를 쓰지 않음
- Node WebSocket bootstrap이 `@hono/node-ws`가 아니라 `@hono/node-server`와 `ws`를 사용함
- runtime 전용 관심사가 격리됨
- config와 bindings가 타입화됨
- Database client setup이 runtime과 일치하고 route module 밖에 있음
- static file route가 제공 pattern에서 보호되고 `allowPercentInPath`에 의존하지 않음
- debug helper가 실수로 켜져 있지 않음

## Sources

> 확인 2026-11-07. adapter 분리, deprecation, static-file 동작은 링크한 release note와 guide에서, package version은 npm registry에서 확인했습니다.

| 주장 | 출처 |
|---|---|
| registry `latest` Hono 4.13.17, `@hono/node-server` 2.1.6과 각각의 peer·engine 범위 | [npm registry: hono](https://registry.npmjs.org/hono), [npm registry: `@hono/node-server`](https://registry.npmjs.org/@hono/node-server) |
| adapter package와 `hono/<adapter>` deprecation | [`hono` v4.13.10 release](https://github.com/honojs/hono/releases/tag/v4.13.10) |
| Node WebSocket bootstrap과 `@hono/node-ws` deprecation | [Node.js Guide](https://hono.dev/docs/getting-started/nodejs), [`@hono/node-server` README](https://github.com/honojs/node-server) |
| `serveStatic`의 `%` 거부, `allowPercentInPath`, GET/HEAD 한정 | [`hono` v4.13.11 release](https://github.com/honojs/hono/releases/tag/v4.13.11), [`hono` v4.13.14 release](https://github.com/honojs/hono/releases/tag/v4.13.14) |