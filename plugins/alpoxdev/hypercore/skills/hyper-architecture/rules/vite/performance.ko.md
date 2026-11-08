# 성능

> 프로덕션 빌드를 측정하고, 배럴 대신 개별 모듈을 가져오며, Rolldown 청크 분할을 근거로 정합니다.

규칙은 날짜가 붙은 스냅숏에서 연 페이지가 그대로 진술하면 `official`, 이 패키지가 기본값으로 고르면 `hypercore-default`로 표시합니다. 순서는 흔한 영향 순이며 측정으로 매긴 순위가 아닙니다.

## Measure first

| 목표 | 명령 또는 도구 |
|---|---|
| 프로덕션 빌드 | `vite build` |
| 빌드 결과 확인 | `vite preview` |
| 빌드의 CPU 프로필 | `vite --profile`이 쓰는 `.cpuprofile` |
| 파일별 transform 시간 | `vite --debug plugin-transform` |
| 번들 구성 | 프로덕션 빌드에 붙인 visualizer |
| 필드 Core Web Vitals | 앱의 `useReportWebVitals` 또는 동등한 RUM hook |
| 랩 Core Web Vitals | 프로덕션 배포에 대한 `lhci autorun` |

`rollup-plugin-visualizer` 7.1.2는 `rollup` 2–4와 `rolldown` 1.x를 모두 peer로 선언하므로 Vite 8에서 돌 수 있습니다. 다만 이 사실은 레지스트리 메타데이터에서만 나왔고 문서 페이지를 열지 않았으므로, 출력을 믿기 전에 설치된 버전에서 확인합니다.

개발 서버 수치와 개발 모드 렌더는 성능 근거가 아닙니다. 빌드 시점 회귀와 런타임 회귀는 다른 측정이므로 어느 쪽이 움직였는지 기록합니다.

## Rules

1. `official` — 배럴 파일을 피하고 개별 모듈을 직접 가져옵니다. 공식 성능 가이드가 이 항목을 문서화된 빌드 비용의 으뜸으로 지목합니다. 배럴을 쓰면 모든 소비자가 재수출 그래프 전체를 읽습니다.
2. `official` — 상대 import에는 파일 확장자를 남기고, tsconfig에 `moduleResolution: "bundler"`와 `allowImportingTsExtensions`를 켭니다. `resolve.extensions` 기본값이 `['.mjs', '.js', '.mts', '.ts', '.jsx', '.tsx', '.json']`이라 확장자 없는 import는 파일 시스템 조회를 최대 여섯 번 합니다.
3. `official` — 청크 분할은 `build.rolldownOptions.output.codeSplitting.groups`에 `name`, `test`, `priority`, `minSize`로 설정합니다. `output.manualChunks`의 객체 형태는 제거됐고 함수 형태는 폐기됐습니다. `codeSplitting: true`(기본값)는 이미 자동 분할이고, `false`는 동적 import를 인라인합니다.
4. `official` — 폐기된 별칭인 `build.rollupOptions` 대신 `build.rolldownOptions`를 쓰고, `optimizeDeps.esbuildOptions` 대신 `optimizeDeps.rolldownOptions`를 씁니다. `worker.rollupOptions`는 `worker.rolldownOptions`로 대응되고 `build.commonjsOptions`는 no-op입니다.
5. `official` — 기본값 `'baseline-widely-available'`보다 낮은 브라우저를 지원해야 하면 `build.target`을 명시합니다. 기본 해석 값은 `chrome111`, `edge111`, `firefox114`, `safari16.4`, `ios16.4`입니다.
6. `official` — `vite --debug plugin-transform`으로 찾은 가장 느린 개발 서버 파일 몇 개에 `server.warmup.clientFiles`를 붙입니다. 이 레버는 개발 루프용이고 프로덕션 번들을 바꾸지 않습니다.
7. `official` — 의존성 스캐너가 아직 import를 발견하는 중에는 `optimizeDeps.holdUntilCrawlEnd`를 기본값으로 둡니다. 정적 import 크롤이 끝날 때까지 첫 결과를 붙잡는 옵션이므로, 스캐너가 모든 것을 찾는 것이 확인된 경우에만 끕니다.
8. `official` — `vite:preloadError`를 처리하고 HTML 진입점을 `Cache-Control: no-cache`로 제공합니다. 재배포 뒤 오래된 클라이언트가 삭제된 청크를 import하면 예외가 나고, 이 실패는 흔히 성능 문제로 오독됩니다.
9. `official` — Full Bundle Mode를 사용 가능한 기능으로 제시하지 않습니다. experimental이고, 릴리스 글의 잠정 수치(개발 시작 약 3배, 전체 새로고침 40% 향상, 네트워크 요청 10분의 1)는 지원되는 기본값이 아닙니다.
10. `official` — `build.minify: 'esbuild'`를 쓰지 않습니다. 폐기됐고 CSS 압축은 이미 `lightningcss`가 기본입니다.
11. `official` — Vite에서 React Compiler는 `react()`와 `@rolldown/plugin-babel`의 `babel({ presets: [reactCompilerPreset()] })`로 붙입니다. `@vitejs/plugin-react` 6.0.0이 인라인 `babel` 옵션을 없애고 Babel 의존성도 제거했기 때문입니다. 컴파일러는 Babel 파이프라인의 첫 번째에 둡니다.
12. `official` — `react({ compiler: true })`는 experimental로 취급합니다. `oxc-transform-react`를 거치고, 플러그인이 네이티브 React Compiler 지원을 experimental로 표시합니다. 현재 옵션은 `compiler.reportDiagnostics`이고 `compiler.logDiagnostics`는 6.1.2부터 폐기됐습니다.
13. `official` — React Compiler가 초기 로드를 개선한다고 주장하지 않습니다. 갱신 성능을 목표로 하고 컴포넌트와 hook만 메모이즈하며 메모이제이션은 컴포넌트 사이에서 공유되지 않습니다. 수동 `useMemo`/`useCallback`/`memo` 삭제는 그 파일에서 컴파일러가 실제로 도는 경우에만 허용합니다.
14. `official` — 컴파일러 lint 규칙(`react-hooks`의 `recommended`/`recommended-latest`, 또는 oxlint `react` 플러그인 동등 규칙)을 켜고, 보고는 "이 컴포넌트는 최적화되지 않는다"로 읽습니다. oxlint에서 `rules-of-hooks`는 `correctness`가 아니라 `pedantic`에 있습니다.
15. `hypercore-default` — `codeSplitting.groups`를 추가하기 전에 `vite --profile`과 visualizer로 측정합니다. 그룹은 측정된 분할 문제의 처방이지 시작 설정이 아닙니다.
16. `hypercore-default` — 75백분위에서 LCP 2.5초 이하, INP 200밀리초 이하, CLS 0.1 이하를 게이트로 두고 모바일과 데스크톱을 따로 보고하며, 스크립트와 이미지 크기 예산을 CI에 함께 둡니다.

## Do not

- 개발 서버를 프로파일링할 때 DevTools의 "Disable Cache"를 켜 두지 않습니다. 코드와 무관한 큰 시작·새로고침 비용이 붙습니다.
- `config`, `configResolved`, `buildStart` 플러그인 hook에 비싼 작업을 두지 않습니다. 셋 다 시작 시점에 await됩니다.
- 파일별 비용을 먼저 재지 않고 무거운 `resolveId`, `load`, `transform` hook을 넣지 않습니다.
- 객체 형태 `manualChunks`를 쓰지 않고 새 설정에 `rollupOptions`를 섞지 않습니다.
- 스캐너가 모든 엔트리를 찾는 것을 확인하기 전에 `holdUntilCrawlEnd`를 끄지 않습니다.
- Rolldown의 "Rollup보다 10–30배 빠름" 수치를 프로젝트 성과로 인용하지 않습니다. 릴리스 글의 공급자 벤치마크입니다.
- `vite-bundle-visualizer`가 Vite 8에서 검증됐다고 가정하지 않습니다. `rolldown` peer를 선언한 것은 `rollup-plugin-visualizer`뿐이고 그것도 레지스트리 메타데이터입니다.
- 지원 브라우저 범위를 실수로 넓히지 않습니다. 낮춘 target은 transform과 폴리필 무게를 더해 번들 증가로 나타납니다.

## Checklist

- [ ] `vite build` 출력과 visualizer 실행, CWV 측정으로 기준선을 기록했습니다.
- [ ] 손댄 코드에 새 배럴 import가 없고 상대 import에 확장자가 붙어 있습니다.
- [ ] 청크 그룹이 있다면 프로덕션 빌드의 전후 측정으로 정당화됩니다.
- [ ] 빌드 설정이 `rolldownOptions`, `oxc`, `codeSplitting`을 쓰고 `manualChunks` 객체와 `esbuild` 압축기가 없습니다.
- [ ] `build.target`이 프로젝트가 실제로 지원하는 브라우저와 맞습니다.
- [ ] `vite:preloadError`를 처리하고 HTML 진입점을 `Cache-Control: no-cache`로 제공합니다.
- [ ] React Compiler 경로를 정확히 표기했고 네이티브 경로를 쓰는 곳에는 experimental 표시가 있습니다.
- [ ] 측정마다 레버 하나만 바꾸고 전후 수치를 기록했습니다.

## Sources

> Checked 2026-11-07. 아래 사실과 URL은 성능 조사 레인의 Vite와 React Compiler 항목에서 가져왔습니다. 레인은 2026-11-07에 각 페이지를 열었고 출처 id를 괄호에 남겼습니다.

| Claim | Source |
|---|---|
| `build.target` 기본값, `baseline-widely-available` 해석, 폐기된 `esbuild` 압축기, `lightningcss` CSS 기본값 (L-29) | https://vite.dev/config/build-options |
| `rolldownOptions` 별칭, 제거된 객체 형태 `manualChunks`, `codeSplitting`, `vite:preloadError`, HTML 캐시 헤더 (L-30) | https://raw.githubusercontent.com/vitejs/vite/main/docs/guide/build.md |
| 배럴 파일, `resolve.extensions`, 확장자 명시, 플러그인 hook, `server.warmup.clientFiles`, `vite --debug plugin-transform`, `vite --profile` (L-31) | https://raw.githubusercontent.com/vitejs/vite/main/docs/guide/performance.md |
| Vite 8의 Rolldown/Oxc 단일 번들러와 공급자 빌드 벤치마크 (L-32) | https://vite.dev/blog/announcing-vite8 |
| `codeSplitting.groups` 옵션 형태와 전역 크기 기본값 (L-33) | https://rolldown.rs/reference/OutputOptions.codeSplitting.md |
| `optimizeDeps.holdUntilCrawlEnd`와 폐기된 `optimizeDeps.disabled` (L-34) | https://raw.githubusercontent.com/vitejs/vite/main/docs/config/dep-optimization-options.md |
| plugin-react 6의 Babel 제거, 네이티브 컴파일러 experimental 표시, `reportDiagnostics`의 `logDiagnostics` 대체 (L-35) | https://raw.githubusercontent.com/vitejs/vite-plugin-react/main/packages/plugin-react/CHANGELOG.md |
| React Compiler 1.0 안정성, 갱신 성능 범위, Meta 수치 (L-01, L-02) | https://react.dev/blog/2025/10/07/react-compiler-1, https://react.dev/learn/react-compiler/introduction |
| 컴파일러 선행 Babel 순서, lint는 최적화 건너뜀, `panicThreshold` (L-03, L-04) | https://react.dev/learn/react-compiler/installation, https://react.dev/reference/react-compiler/configuration |
| 컴파일러 lint 규칙 이름과 프리셋 (L-65) | https://raw.githubusercontent.com/facebook/react/main/packages/eslint-plugin-react-hooks/README.md |
| oxlint `react` 플러그인 규칙과 카테고리 매핑 (L-66) | https://oxc.rs/docs/guide/usage/linter/rules.html |
| 75백분위 Core Web Vitals 임계값, 기기별 구분 (L-67) | https://web.dev/articles/vitals |
| CI 하네스로서의 Lighthouse CI와 예산 권고 (L-68) | https://raw.githubusercontent.com/GoogleChrome/lighthouse-ci/main/README.md |
| `rollup-plugin-visualizer`와 `vite-bundle-visualizer`의 레지스트리 peer (L-70, 레지스트리 메타데이터만) | https://registry.npmjs.org/{next,vite,expo,expo-router,react-native,hono,oxlint,babel-plugin-react-compiler,eslint-plugin-react-hooks,@vitejs/plugin-react,@tanstack/react-router,@tanstack/react-query,@tanstack/react-start,expo-image}/latest |
