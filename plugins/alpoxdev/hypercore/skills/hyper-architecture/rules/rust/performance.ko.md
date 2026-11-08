# 성능

> 릴리스 빌드 기준선을 먼저 기록하고, 레버 하나를 바꾼 뒤, 같은 산출물을 다시 측정합니다. 바이너리 크기, `*_bg.wasm` 크기, 또는 실제 시간입니다.

이 파일의 규칙은 `references/official/rust/rust-crates-2026-11-07.md`에서 연 페이지가 그대로 진술한 경우 `official`, 이 패키지가 기본값으로 고른 경우 `hypercore-default`로 표시합니다. 규칙 순서는 흔한 영향 순이며 측정으로 매긴 순위가 아닙니다. 같은 명령에서 잰 before/after 수치가 없는 성능 주장은 결과가 아닙니다.

## 1. 먼저 측정

`hypercore-default` — 성능 작업은 릴리스 빌드에서 합니다. 디버그 빌드의 시간, 크기, 할당 프로필은 근거가 아닙니다.

| Goal | Command | Record |
|---|---|---|
| 바이너리 크기 | `cargo build --release` 후 `target/release/<bin>`에 `stat -c%s`/`wc -c` | 바이트, 타깃 트리플, 프로필 이름 |
| 빌드 시간 | 깨끗한 `target`에서 `cargo build --release`(또는 crate 하나면 `cargo clean -p <crate>`) | 벽시계 초, 기계, crate 수 |
| WASM 크기 | 빌드 후 wasm-bindgen/wasm-pack 실행, 그다음 `*_bg.wasm`에 `wc -c` | 바이트, 타깃, `--target` 모드 |
| 시작 시간 | 바이너리 자체 타이밍 플래그, 또는 warm 캐시에서 `time`을 쓰는 셸 루프, N=20 | 중앙값 벽시계 시간 |
| 핫 패스 | 릴리스 빌드의 `perf`/Instruments 프로필, 또는 crate 안 타이밍 하네스 | 함수 이름과 비율 |

`hypercore-default` — 기준선 규칙입니다.

- 측정마다 명령 하나, 기계 하나, 프로필 하나입니다. 노트북 수치와 CI 수치를 섞으면 허구의 차이가 나옵니다.
- warm 실행과 cold 실행은 다른 수치입니다. 어느 쪽을 기록했는지 밝힙니다.
- 깨끗한 빌드는 컴파일 시간을, 증분 빌드는 링크 시간을 잽니다. 어느 쪽인지 진술합니다.
- 라이브러리는 소비 바이너리에서 잽니다. 라이브러리 단독으로는 런타임이 없습니다.

`hypercore-default` — 벤치마킹 crate(`criterion`, `hyperfine`)는 이 스냅숏에서 확인하지 않았고 여기서 강제하지 않습니다. 프로젝트가 이미 쓰면 유지하고 버전을 기록하며, 아니면 warm 캐시를 쓰는 셸 루프가 첫 측정으로 충분합니다.

## 2. 릴리스 프로필 레버

`official` — Cargo 릴리스 기본값은 `opt-level = 3`, `debug = false`, `lto = false`, `codegen-units = 16`, `panic = "unwind"`, `strip = "none"`, `incremental = false`입니다(https://doc.rust-lang.org/cargo/reference/profiles.html). 따라서 아래의 강한 설정은 모두 명시적 선택이고, 프로젝트에 이미 있는 것이 아닙니다.

| Lever | Values | Effect | Cost |
|---|---|---|---|
| `lto` | `true`/`"fat"`, `"thin"`, `false`, `"off"` | crate 간 인라인과 죽은 코드 제거. 더 작고 빠름 | 빌드·링크 시간 |
| `codegen-units` | 1–256(기본 16, 증분은 256) | 단위가 적으면 프로그램 전체 최적화가 늘어남 | 병렬성 상실, 빌드 느려짐 |
| `opt-level` | `0`–`3`, `"s"`, `"z"` | `"z"`는 루프 벡터화도 끔 | 크기 대 속도 |
| `panic` | `"unwind"`, `"abort"` | `"abort"`는 unwind 표를 제거 | `catch_unwind` 없음, backtrace 없음 |
| `strip` | `"none"`, `"debuginfo"`, `"symbols"`, `true` | `true`는 `"symbols"`와 같음 | 출하 산출물 디버깅 가능성 |
| `debug` | `false`, `0`–`2`, `"none"`/`"line-tables-only"`/`"full"` | 디버그 정보 존재 | 크기 |

`official` — `[profile.*]` 섹션은 "루트 manifest에서만 인식되고 멤버 crate manifest에서는 무시됩니다"(https://doc.rust-lang.org/cargo/reference/workspaces.html). 자체 `[profile.release]`를 선언하는 멤버는 아무것도 바꾸지 않습니다.

`official` — "테스트, 벤치마크, 빌드 스크립트, proc macro는 `panic` 설정을 무시합니다"(https://doc.rust-lang.org/cargo/reference/profiles.html). 따라서 테스트 스위트 동작이 `panic = "abort"`에 의존하면 안 되고, `panic = "abort"` 테스트는 nightly `panic-abort-tests` 플래그가 필요합니다.

`hypercore-default` — 시작점이며, 각각 유지하기 전에 측정합니다.

```toml
# Shipped CLI or MCP server: smaller binary, no unwinding tables
[profile.release]
lto = "thin"          # "fat" only when the last few percent justify the link time
codegen-units = 1
strip = "debuginfo"   # keep symbols out of the shipped artifact, keep them in a debug split
panic = "abort"

# WASM module: size is the metric, not throughput
[profile.release]
lto = true
codegen-units = 1
opt-level = "z"       # measure "s" too; the docs warn "s" can win
panic = "abort"
strip = "symbols"
```

`hypercore-default` — 측정마다 값 하나를 바꿉니다. 한 실행에서 레버 둘을 바꾸면 아무도 귀속시킬 수 없는 수치가 나옵니다.

`hypercore-default` — `dist`가 릴리스를 구동할 때 `release`를 상속하는 별도 `[profile.dist]`가 공격적 설정을 로컬 빌드 밖에 둡니다. dist 전용 설정은 `rules/rust/cli.md`의 것이고, 위의 `[profile.release]` 값은 각각 측정과 함께 바꾸므로 이 파일의 것입니다. `rules/setup/rust.md`는 기준선 프로필 값만 정하고 릴리스 모양을 바꾸는 레버는 여기에 남깁니다.

## 3. WASM 크기 레버

`official` — `target/wasm32-unknown-unknown/release/foo.wasm` 원본은 "크기 최적화가 되어 있지 않으므로 측정하면 안 됩니다". wasm-bindgen CLI가 실행된 뒤 생성된 `foo_bg.wasm`을 측정합니다. CLI가 "불필요한 기능을 자동으로 모두 제거"하기 때문입니다(https://wasm-bindgen.github.io/wasm-bindgen/reference/optimize-size.html).

`official` — `lto = true`는 "LLVM이 함수를 인라인하고 제거할 기회를 훨씬 많이 주므로 … `.wasm`을 더 작게 만듭니다". `opt-level = "s"`가 `"z"`를 이길 수 있고 문서는 "항상 측정하세요!"라고 합니다. `wasm-opt -Os`/`-Oz` 후처리는 "흔히 15-20%를 더 줄입니다"(https://rustwasm.github.io/docs/book/reference/code-size.html).

`hypercore-default` — 너무 큰 모듈에 대한 공격 순서입니다.

1. 쓰지 않는 `web-sys` 기능과 쓰지 않는 의존성을 뺍니다. 대개 모든 컴파일러 플래그를 이기고, 빌드도 함께 줄이는 유일한 레버입니다.
2. 디버그 정보를 끕니다(`strip = "symbols"`, 출하 빌드에서 `--keep-debug`를 넘기지 않음).
3. `opt-level = "z"`와 `"s"`를 둘 다 측정합니다.
4. `lto = true`와 `codegen-units = 1`을 씁니다.
5. Binaryen이 있으면 `wasm-opt -Os`/`-Oz`를 후처리로 씁니다.
6. `--split-debug-info`/`--split-linked-modules`는 소비자가 결과 분할을 지원할 때만 씁니다. 둘 다 대부분의 번들러를 깨뜨립니다.

`hypercore-default` — 사용자가 내려받는 산출물의 크기를 기록합니다. 중간 파일의 수치가 아닙니다. `target/`에서 얻은 수치는 출하 수치가 아닙니다.

## 4. 할당과 핫 패스

`hypercore-default` — 할당 작업은 측정을 따릅니다. 프로필 없이 "할당을 줄인다"는 것은 가독성을 아무것도 얻지 못하는 것과 바꾸는 추측입니다.

먼저 측정하고, 그다음 국소적인 것부터 레버를 씁니다.

| Symptom | Lever |
|---|---|
| 루프 안의 clone | clone 대신 차용(`&str`, `&[T]`)하거나 이동 |
| 값 하나를 만들며 작은 `String`을 많이 할당 | `String::with_capacity` / `Vec::with_capacity`로 미리 확보 |
| 핫 루프의 반복 포맷 | 루프 밖에서 한 번 포맷하거나 재사용 버퍼에 쓰기 |
| 항목마다 `HashMap` 조회 | 정렬 후 이진 탐색, 또는 다른 키 고려 |
| 서버 경로의 경합 | 공유 lock 대신 태스크별 상태. `.await`를 넘어 lock을 잡지 않음 |
| 프로필이 보여주는 할당자 압력 | 전역 할당자는 후보이지 기본이 아님. 후보 crate 자체 문서는 강화 모드의 성능 페널티를 보고하고, 이를 지지하는 공식 Rust 페이지는 없음 |

`hypercore-default` — WASM 모듈에서 할당은 JavaScript도 값을 치르는 경계를 넘습니다. 큰 페이로드는 숫자 배열보다 `Uint8Array`/`js_sys` 타입으로 넘기고, 항목마다 `JsValue`를 만드는 대신 구조 값 하나를 씁니다.

`hypercore-default` — CLI에서는 작은 작업에서 프로세스 시작이 지배적인 경우가 많습니다. 내부 루프를 최적화하기 전에 전체 벽시계 시간을 측정합니다. 40ms cold start 옆의 2ms 루프 개선은 보이지 않습니다.

## 5. 하지 말 것

`hypercore-default` — 아래를 "최적화"로 받아들이지 않습니다.

- 빠를 것 같아서 모든 곳에 `lto = true`를 두는 것. 빌드 시간을 쓰고 이득은 노이즈 안일 수 있습니다.
- 불변 조건과 벤치마크 없이 속도를 위해 `unsafe`를 쓰는 것.
- 프로필이 지목하기 전에 핫 함수를 재작성하는 것.
- 후처리 파일이 아니라 `target/` 산출물에서 크기 이득을 주장하는 것.
- 디버그 빌드와 릴리스 빌드를, warm 실행과 cold 실행을 비교하는 것.
- 한 번의 실행에서 나온 백분율을 보고하는 것. 수치가 안정될 때까지 반복하거나 범위로 보고합니다.
- 다른 사람이 의존하는 라이브러리에서 `panic`을 `"abort"`로 바꾸는 것. 그 선택은 최종 바이너리의 것입니다.

## 6. 결과 기록

`hypercore-default` — 성능 변경 노트는 이렇게 적습니다.

```text
artifact: target/release/mytool (aarch64-apple-darwin, profile.release)
before: 4_812_904 bytes   (lto = false, codegen-units = 16, strip = none)
after:  2_140_112 bytes   (lto = "thin", codegen-units = 1, strip = "debuginfo")
command: cargo build --release && wc -c target/release/mytool
```

- 산출물, 프로필, 정확한 명령을 명명합니다.
- 바꾼 레버를 줄마다 하나씩 적어 귀속이 보이게 합니다.
- 진 측정도 남깁니다. 버린 레버는 유용한 기록입니다.

## Checklist

- [ ] 릴리스 빌드에서 기준선을 기록하고 산출물 경로와 프로필을 명명했다.
- [ ] 측정 명령이 진술되었고 같은 기계에서 재현 가능하다.
- [ ] 측정마다 레버 하나를 바꾸고 before/after 수치를 기록했다.
- [ ] `[profile.*]` 설정이 루트 manifest에만 있다.
- [ ] WASM 크기를 `target/`의 rustc 출력이 아니라 `*_bg.wasm`에서 측정했다.
- [ ] 컴파일러 플래그보다 쓰지 않는 `web-sys` 기능과 의존성을 먼저 확인했다.
- [ ] 크기가 지표이면 `opt-level = "s"`와 `"z"`를 비교했다.
- [ ] `panic = "abort"`가 테스트, 벤치, 빌드 스크립트, proc macro에 영향을 준다고 가정하지 않았다.
- [ ] 할당 작업을 추측이 아니라 프로필에서 시작했다.
- [ ] 불변 조건과 벤치마크 없이 속도용 `unsafe`를 추가하지 않았다.
- [ ] 변경 노트가 산출물, 프로필, 명령, 차이를 명명한다.

## Sources

> Checked 2026-11-07. 사실은 `references/official/rust/rust-crates-2026-11-07.md`에 기록된 페이지에서 왔습니다.

| Claim | Source |
|---|---|
| 릴리스 프로필 기본값, `lto`/`codegen-units`/`opt-level`/`strip`/`panic` 값과 효과, 테스트·벤치 panic 예외 | https://doc.rust-lang.org/cargo/reference/profiles.html |
| `[profile.*]`는 루트 manifest에서만 읽힘 | https://doc.rust-lang.org/cargo/reference/workspaces.html |
| wasm-bindgen이 strip한 뒤 `*_bg.wasm`을 측정 | https://wasm-bindgen.github.io/wasm-bindgen/reference/optimize-size.html |
| `lto = true`, `opt-level = "s"` 대 `"z"`, `wasm-opt`의 15–20% 수치 | https://rustwasm.github.io/docs/book/reference/code-size.html |
| `--keep-debug`, `--split-debug-info`, `--split-linked-modules` 동작 | https://wasm-bindgen.github.io/wasm-bindgen/reference/cli.html |
| `dist`가 릴리스를 구동할 때의 프로필 분리 | https://axodotdev.github.io/cargo-dist/book/reference/concepts.html |
| 측정-변경-측정 절차, 레버 순서, 기록 형식 | 이 패키지의 규약이며 공식 Rust 요구가 아님 |
