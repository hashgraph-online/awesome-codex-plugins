# 성능

> 문서에 있는 릴리스 프로필을 쓰고, 쓰지 않는 command를 바이너리에서 빼며, 웹뷰 번들은 별도 예산으로 다룹니다.

규칙은 날짜가 붙은 스냅숏에서 연 페이지가 그대로 진술하면 `official`, 이 패키지가 기본값으로 고르면 `hypercore-default`로 표시합니다. 순서는 흔한 영향 순이며 측정으로 매긴 순위가 아닙니다.

## Measure first

Tauri 앱에는 독립적인 무게 문제가 둘 있습니다. Rust 바이너리와 웹뷰 자산입니다. 둘을 모두 재고, 느린 시작을 엉뚱한 쪽 탓으로 돌리지 않습니다.

| 목표 | 명령 또는 도구 |
|---|---|
| 릴리스 빌드와 설치 파일 | `tauri build` |
| 바이너리 크기 | 빌드된 바이너리와 `src-tauri/target/release/` 아래 번들에 대한 `ls -l` |
| Rust 의존성 무게 | `src-tauri/Cargo.toml`의 릴리스 프로필, 그리고 프로필 변경 하나당 바이너리 크기 전후 비교 |
| 웹뷰 번들 구성 | 프런트엔드 스택 자체 분석기를 프로덕션 빌드에 적용 (Vite 프런트엔드면 Vite 성능 규칙) |
| 시작 시간 | 개발 루프 밖에서 띄운 릴리스 빌드, 웹뷰 devtools를 닫은 상태 |
| 웹뷰의 필드 Core Web Vitals | 프런트엔드에 계측이 있으면 그 앱의 RUM hook |

모든 측정은 릴리스 빌드에서 합니다. 개발 빌드는 증분 컴파일 설정과 최적화되지 않은 의존성을 안고 있어 그 크기와 시작 시간으로 출하 앱을 판단할 수 없습니다.

## Rules

1. `official` — `src-tauri/Cargo.toml`에 문서화된 `[profile.release]`를 넣습니다. `codegen-units = 1`, `lto = true`, `panic = "abort"`, `strip = true`입니다. 바이너리 크기가 속도보다 중요하면 `opt-level = "s"`, 아니면 `opt-level = 3`을 고릅니다.
2. `official` — 개발 루프가 빠르도록 `[profile.dev] incremental = true`를 둡니다. 릴리스 프로필 설정을 `dev`로 복사하지 않습니다.
3. `official` — `tauri.conf.json`에서 `build.removeUnusedCommands: true`를 켭니다. capability 파일에서 허용되지 않은 command를 제거해, 앱이 호출할 수 없는 command 값을 치르지 않게 합니다.
4. `official` — capability 파일에는 `defaults`에 기대지 말고 앱이 실제로 쓰는 command만 나열합니다. `removeUnusedCommands`의 나머지 절반입니다. 제거는 ACL이 배제한 것까지만 닿습니다.
5. `official` — nightly 전용 추가 항목(`trim-paths = "all"`, `rustflags = ["-Cdebuginfo=0", "-Zthreads=8"]`)은 nightly 툴체인의 선택 사항으로 다룹니다. 안정 프로필의 일부가 아니며 기본값으로 제시하지 않습니다.
6. `official` — Rust 프로필을 만지기 전에 웹뷰 번들을 프런트엔드 스택 자체 분석기로 점검합니다. Rust 릴리스 프로필은 부푼 웹뷰 번들을 고치지 못하고, Tauri 앱 시작 무게의 대부분은 프런트엔드에서 옵니다.
7. `hypercore-default` — 프로필 변경마다 바이너리 크기를 재고, 한 번에 하나만 바꿉니다. `lto = true`와 `codegen-units = 1`은 링크 시간을 런타임과 크기로 맞바꾸므로, 그 거래가 수치로 보인 뒤에 남깁니다.
8. `hypercore-default` — 웹뷰 표면에는 웹 앱과 같은 성능 예산을 둡니다. 해당 지표가 앱에서 의미가 있는 범위에서 75백분위 LCP 2.5초 이하, INP 200밀리초 이하, CLS 0.1 이하입니다.

## Do not

- `opt-level = "s"`가 기본적으로 옳다고 가정하지 않습니다. 크기를 우선하는 값이고, CPU를 많이 쓰는 프런트엔드 브리지는 `3`을 원할 수 있습니다.
- nightly `rustflags` 블록을 안정 툴체인 프로젝트로 복사하지 않습니다.
- `removeUnusedCommands`가 바이너리를 줄여 주리라 기대하면서 capability 파일에 `defaults`를 남기지 않습니다. 둘은 서로 맞아야 합니다.
- 웹뷰 번들이 일으킨 느린 첫 페인트를 Rust 프로필 탓으로 돌리지 않습니다.
- `cargo build`만 돌려 놓고 출하 크기라고 부르지 않습니다. 사용자가 내려받는 번들은 `tauri build`가 만듭니다.
- 앱이 링크하는 라이브러리 crate에 `panic = "abort"`를 켜 놓고 unwinding 기반 복구가 계속 동작하리라 기대하지 않습니다.
- Tauri 성능 패스 안에서 프런트엔드 빌드를 다시 조정하거나 재포맷하지 않습니다. 그 일은 프런트엔드 스택의 성능 규칙에 속합니다.

## Checklist

- [ ] 변경 전 릴리스 빌드를 쟀고 바이너리 크기와 웹뷰 번들 크기를 따로 기록했습니다.
- [ ] `[profile.release]`가 문서의 집합과 맞고 `opt-level` 선택이 설명됩니다.
- [ ] `[profile.dev] incremental = true`가 있습니다.
- [ ] `build.removeUnusedCommands: true`가 켜져 있고 capability 파일이 `defaults` 대신 사용 command를 나열합니다.
- [ ] 툴체인이 nightly가 아니면 nightly 전용 프로필 키가 없습니다.
- [ ] 웹뷰 번들을 프런트엔드 분석기로 점검했고 그 발견을 Rust 프로필 탓으로 돌리지 않았습니다.
- [ ] 측정마다 프로필 레버 하나만 바꾸고 전후 수치를 기록했습니다.

## Sources

> Checked 2026-11-07. 아래 사실과 URL은 성능 조사 레인의 Tauri 항목에서 가져왔습니다. 레인은 2026-11-07에 각 페이지를 열었고 출처 id를 괄호에 남겼습니다.

| Claim | Source |
|---|---|
| 문서화된 `[profile.release]` 값, `opt-level` 크기 대 속도 설명, `[profile.dev] incremental`, nightly 전용 추가 항목 (L-64) | https://raw.githubusercontent.com/tauri-apps/tauri-docs/v2/src/content/docs/concept/size.mdx |
| `build.removeUnusedCommands`와 `defaults` 대신 사용 command를 나열하라는 조언 (L-64) | https://raw.githubusercontent.com/tauri-apps/tauri-docs/v2/src/content/docs/concept/size.mdx |
| 프런트엔드 번들 분석은 프런트엔드 스택 자체 분석기에 속합니다 (L-64, L-17) | https://raw.githubusercontent.com/tauri-apps/tauri-docs/v2/src/content/docs/concept/size.mdx, https://nextjs.org/docs/app/guides/package-bundling |
| 현재 `tauri` crate 2.12.5, 기록된 기준선과 일치 (L-71) | https://crates.io/api/v1/crates/{axum,tauri,tower-http} |
| 75백분위 Core Web Vitals 임계값, 기기별 구분 (L-67) | https://web.dev/articles/vitals |
