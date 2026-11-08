# Import Protection

> Start의 기본 client/server import boundary를 인정하면서 hypercore safety deny rules를 적용합니다.

## Rule Classifications

| Rule | Classification | Enforcement |
|---|---|---|
| Start import protection은 기본 enabled | Official | custom config 전 behavior 확인 |
| 문서화된 옵션 표는 신뢰할 수 있고 `mockAccess`는 미문서 옵션 | Official | 문서화된 옵션만 인용하고 `mockAccess`는 버전마다 다시 확인 |
| `.server.*`는 client에서, `.client.*`는 server에서 deny | Official | leak 차단 |
| marker import는 module을 한 environment로 제한 | Official | suffix가 부족할 때 사용 |
| `database/`, `server/`, ORM package custom deny rules/tanstack-start | Safety policy | 프로젝트에 필요하면 추가/확장 |
| import protection 비활성화 금지 | Safety policy | 명시 요청 없으면 차단 |

## Official Defaults

TanStack Start import protection은 기본 enabled입니다. explicit `importProtection` object가 항상 필요하다고 말하지 않습니다.

가이드에는 더 이상 Experimental 표시가 없습니다. defaults 표, replace-vs-additive 시맨틱, `include`, `exclude`, `ignoreImporters`, `maxTraceDepth`, `onViolation` 옵션을 문서화합니다. `mockAccess`는 예외입니다. plugin schema에는 실제로 있지만 가이드에는 없으므로 미문서 항목으로 남깁니다.

dev mode 위반은 오탐일 수 있습니다. build mode는 tree-shaking 뒤까지 검사를 미루기 때문에 production graph에서 사라지는 import가 dev에서는 경고로 남을 수 있습니다. 의심스러운 dev 경고는 boundary를 고치기 전에 production build로 확인합니다.

문서화된 기본값 (Official, 가이드 option table):

| Option | Default |
|---|---|
| `enabled` | `true` |
| `behavior` | `{ dev: 'mock', build: 'error' }` |
| `log` | `'once'` |
| `include` | Start의 `srcDirectory` |
| `maxTraceDepth` | `20` |

기본 deny pattern:

- Client environment: `**/*.server.*`, Start server specifiers.
- Server environment: `**/*.client.*`.

Type-only imports and re-exports are ignored because runtime bundle에서 제거됩니다. Runtime value를 포함하는 mixed imports는 여전히 검사 대상입니다.

## Marker Imports

```typescript
import '@tanstack/react-start/server-only'
import '@tanstack/react-start/client-only'
```

- 한 파일에는 marker 하나만 사용합니다.
- 파일명만으로 boundary가 명확하지 않을 때 사용합니다.

## Custom Deny Rules

프로젝트가 directory/package 추가 차단을 필요로 할 때 explicit `tanstackStart({ importProtection })` config를 추가합니다:

```typescript
import { tanstackStart } from '@tanstack/react-start/plugin/vite'

tanstackStart({
  importProtection: {
    behavior: { dev: 'mock', build: 'error' },
    client: {
      files: ['**/*.server.*', '**/server/**', '**/database/**', '**/db/**'],
      specifiers: ['@prisma/client', 'bcrypt'],
    },
    server: {
      files: ['**/*.client.*', '**/client/**'],
      specifiers: ['localforage'],
    },
  },
})
```

## Replace vs Additive (Official)

가이드 option table은 각 key가 어느 쪽인지 표시합니다. 여기가 함정입니다. 어떤 key는 내장 규칙에 더해지고, 어떤 key는 내장 규칙을 통째로 대체합니다.

| Key | Semantics | 대체하는 기본값 |
|---|---|---|
| `client.specifiers` | Additive with defaults | framework server specifiers |
| `client.files` | Replaces defaults | `['**/*.server.*']` |
| `client.excludeFiles` | Replaces defaults | `['**/node_modules/**']` |
| `server.files` | Replaces defaults | `['**/*.client.*']` |
| `server.specifiers` | Replaces defaults | `[]` — 그래서 `client.specifiers`와 달리 실제로는 additive가 아닙니다 |
| `server.excludeFiles` | Replaces defaults | `['**/node_modules/**']` |

`client.files`를 설정하면서 `'**/*.server.*'`를 다시 적지 않으면 기본 deny rule이 조용히 사라집니다. 위 예시가 그 값을 다시 적은 이유입니다. `excludeFiles`는 기본값 `['**/node_modules/**']`를 **fully replaces**, 즉 통째로 대체합니다. `node_modules`는 계속 건너뛰면서 경로를 더 제외하려면 두 pattern을 함께 넘깁니다: `excludeFiles: ['**/node_modules/**', '**/vendor/**']`.

기존 `tanstackStart()`가 있으면 관련 nested option만 확장합니다. plugin을 중복 추가하거나 unrelated option을 덮어쓰지 않습니다.

Project가 development에서도 violation을 실패시키길 원하면 `behavior: 'error'`를 사용합니다. Current options에는 scoped enforcement와 diagnostics를 위한 `log`, `include`, `exclude`, `ignoreImporters`, `maxTraceDepth`, `onViolation`도 포함됩니다.

`client`와 `server` rules는 `files`, `specifiers`, `excludeFiles`를 지원합니다(설정 전에 위의 replace-vs-additive 표를 먼저 확인합니다). Default는 `node_modules` 아래 resolved files를 제외합니다. `excludeFiles: []`는 선택한 environment에서 이 검사를 다시 켜므로, third-party package false positive 가능성을 고려해 의도적으로만 사용합니다.

`mockAccess`(`'error' | 'warn' | 'off'`, default `'error'`)는 `@tanstack/start-plugin-core@1.171.55`의 `schema.d.ts`에 존재하며, `behavior: 'mock'`일 때 mock된 import가 runtime console diagnostic을 내보낼지 제어합니다. 공식 가이드의 option table에는 **없습니다**. 문서가 다루지 않는 실제 schema option입니다. 인용할 때는 undocumented로 표시하고, 의존하기 전에 설치된 package types와 다시 대조합니다. 문서화된 option처럼 적지 않습니다.

## Compiler Boundary Leak Rule

`createServerFn` handler 내부 server-only import는 client build에서 제거될 수 있습니다. 같은 import가 client compilation 후 살아남는 코드에서 참조되면 import protection violation입니다.

수정 방법:

- surviving helper를 `*.server.*`로 분리.
- helper를 `createServerOnlyFn`으로 감싸기.
- browser-only code는 `*.client.*` 또는 `createClientOnlyFn` 뒤로 이동.
- server function wrapper는 `*.functions.ts`에 두고 DB/secret/filesystem helper는 sibling `*.server.ts`로 분리.
- `src/modules/<domain>/<feature>/index.ts`나 `-functions/index.ts`에서 safe exports와 server-only exports를 섞지 않기.

## Server Function Import Shape

Server function wrapper 자체는 loader/component/hook에서 static import할 수 있습니다. 하지만 wrapper file이 client build에서 살아남는 export를 통해 server-only helper를 참조하면 leak입니다.

권장:

```text
src/modules/users/profile/
├── profile.functions.ts  # createServerFn exports
├── profile.server.ts     # DB/secret helper
└── profile.schemas.ts    # client-safe schema
```

금지/경고:

- `profile.functions.ts`가 handler 밖 helper export에서 `profile.server.ts`를 참조
- `index.ts`가 `profile.functions.ts`와 `profile.server.ts`를 함께 re-export
- client component가 `*.server.ts`, `src/db/**`, privileged SDK를 직접 import
- server function을 dynamic import해서 bundler rewrite/import-protection trace를 흐리게 함

## Validation Checklist

- [ ] import protection이 disabled가 아님.
- [ ] project directory/package에 필요하면 custom deny rules가 있음.
- [ ] Type-only imports를 runtime boundary leak로 잘못 보고하지 않음.
- [ ] 기존 `tanstackStart()` option을 덮어쓰지 않고 확장함.
- [ ] `behavior: 'error'`와 `{ dev, build }` behavior를 의도적으로 선택함.
- [ ] Custom `client.files` / `server.files` / `excludeFiles` list가 대체하는 기본값을 다시 적었음.
- [ ] Third-party resolved-file checks가 의도적으로 필요할 때만 `excludeFiles: []`를 사용함.
- [ ] `.server.*`, `.client.*`, marker import가 일관됨.
- [ ] server-only import가 recognized boundary 밖에 살아남지 않음.
- [ ] `*.functions.ts` wrapper와 `*.server.ts` helper가 split되어 있음.
- [ ] safe/server-only mixed barrel이 없음.
- [ ] tree-shaking false positive 가능성이 있으면 production build로 확인함.

## Sources

> 출처 확인 2026-11-04: <https://tanstack.com/start/latest/docs/framework/react/guide/import-protection.md>(defaults 표, replace-vs-additive 시맨틱, 문서화된 옵션 표면. 페이지에 Experimental 표시가 없습니다)와 `@tanstack/start-plugin-core@1.171.55`의 `schema.d.ts`(`mockAccess` enum과 기본값)입니다. 이 사실은 이 패키지 자체의 2026-11-04 snapshot `references/official/tanstack-start/current-docs-2026-11-04.md`에 담겨 있고, 외부 출처는 runtime 의존이 아닙니다. 저장소 로컬 링크 확인 2026-11-04.
