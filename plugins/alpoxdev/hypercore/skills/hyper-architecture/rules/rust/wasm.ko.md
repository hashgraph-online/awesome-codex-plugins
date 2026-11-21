# WASM

> 도구보다 타깃을 먼저 고르고, `cdylib`에서 모듈을 만들며, wasm-bindgen 이후 산출물을 측정하고, JavaScript 경계를 타입 있게 유지합니다.

이 파일의 규칙은 `references/official/rust/rust-crates-2026-11-07.md`에서 연 페이지가 그대로 진술한 경우 `official`, 이 패키지가 기본값으로 고른 경우 `hypercore-default`로 표시합니다.

## 1. 아키텍처 둘, 프로필 하나

`official` — `wasm32-unknown-unknown`, `wasm32-wasip1`, `wasm32-wasip2`는 모두 `std`를 갖춘 Tier 2입니다(https://doc.rust-lang.org/rustc/platform-support.html). 서로 바꿔 쓸 수 없습니다.

| Target | Host | Output | JavaScript glue |
|---|---|---|---|
| `wasm32-unknown-unknown` + wasm-bindgen | 브라우저 또는 JavaScript 런타임 | 코어 모듈과 생성된 JS | 있음 |
| `wasm32-wasip1` | WASI 런타임 | 코어 모듈 | 없음 |
| `wasm32-wasip2` | 컴포넌트 모델 런타임(Wasmtime 17 이상) | 코어 모듈이 아니라 컴포넌트 | 없음 |

`official` — wasm-bindgen은 "`wasm32-unknown-unknown` 타깃을 대상으로 설계되었습니다. … 표준 라이브러리는 대부분 무력해서 `std::fs`나 `std::net` 같은 모듈은 단순히 오류를 반환합니다"(https://wasm-bindgen.github.io/wasm-bindgen/reference/rust-targets.html). 그 가이드는 WASI 타깃을 문서화하지 않으므로, WASI 모듈은 바인딩 없이 평범한 rustc 출력을 씁니다.

`official` — `wasm32-wasip1`은 `std`를 지원하지만 "스레드를 생성하면 항상 오류가 나고", "프로세스를 생성하면 항상 오류가 나며", 파일 API는 WASI를 거칩니다. 게이트는 `#[cfg(all(target_os = "wasi", target_env = "p1"))]`이고, `target_env = "p1"`은 Rust 1.80부터 존재합니다(https://doc.rust-lang.org/rustc/platform-support/wasm32-wasip1.html). `wasm32-wasip2`는 "코어 wasm 모듈이 아니라 컴포넌트를 출력"하고 "현재 CI에서 테스트되지 않습니다"(https://doc.rust-lang.org/rustc/platform-support/wasm32-wasip2.html).

`hypercore-default` — 선택은 manifest나 `README` 한 줄에, 그것이 섬기는 호스트와 함께 기록합니다. 툴체인에 설치된 타깃은 결정이 아닙니다.

## 2. crate 타입과 타깃 범위

`official` — `crate-type`은 `bin`, `lib`, `rlib`, `dylib`, `cdylib`, `staticlib`, `proc-macro`를 받고 라이브러리와 예제 타깃에만 적용됩니다(https://doc.rust-lang.org/cargo/reference/cargo-targets.html). 공식 wasm-bindgen 예제 manifest는 `[lib] crate-type = ["cdylib"]`, 명시적 기능 목록의 `web-sys`, `[lints] workspace = true`를 씁니다(https://raw.githubusercontent.com/wasm-bindgen/wasm-bindgen/main/examples/dom/Cargo.toml).

`hypercore-default` — 배치입니다.

```toml
[lib]
crate-type = ["cdylib", "rlib"]

[target.'cfg(target_arch = "wasm32")'.dependencies]
wasm-bindgen = "0.2"
wasm-bindgen-futures = "0.4"
console_error_panic_hook = "0.1"
js-sys = "0.3"

[target.'cfg(target_arch = "wasm32")'.dependencies.web-sys]
version = "0.3"
features = ["Window", "Document", "Element", "HtmlElement"]
```

`official` — 타깃 범위 의존성 섹션이 "컴파일 시간을 줄이기 위해" 가이드가 권하는 방식입니다(https://wasm-bindgen.github.io/wasm-bindgen/reference/rust-targets.html).

`official` — 네이티브로 테스트해야 하는 로직은 `#[cfg(target_arch = "wasm32")]` 뒤에 두면 안 됩니다. 바인딩 계층만 그 뒤에 둡니다. `cdylib` 옆에 `rlib`를 두는 이유입니다.

## 3. rustwasm은 옮겨 갔습니다

`official` — Rust 프로젝트는 2025-07-21에 "Sunsetting the rustwasm GitHub org"를 발표했습니다. 워킹 그룹은 약 5년의 무활동 끝에 2024년에 보관 처리되었고, `wasm-bindgen`은 "새 유지보수자를 더한 새 wasm-bindgen 조직으로 이전"하며, 조직 자체는 2025년 9월에 보관되었습니다(https://blog.rust-lang.org/inside-rust/2025/07/21/sunsetting-the-rustwasm-github-org/). 보관된 `rustwasm/team` README는 이제 Rust와 WebAssembly 활동이 일어나는 곳이 아니라고 진술합니다.

`hypercore-default` — 규칙 집합이 담아야 하는 결과입니다.

- 공식 거처는 `github.com/wasm-bindgen/wasm-bindgen`과 `github.com/wasm-bindgen/wasm-pack`입니다. `rustwasm/*` URL을 인용하지 않습니다. 그 URL들은 리다이렉트됩니다.
- wasm-bindgen 가이드와 wasm-pack 책은 `wasm-bindgen.github.io` 아래에 있습니다. 이전의 `rustwasm.github.io/wasm-pack/installer/` URL은 폐기되었습니다.
- `wasm-pack`은 여전히 유지보수됩니다. 0.15.1이 2026-10-30에 출시되었고 README는 `@drager`의 유지보수를 언급합니다.
- `console_error_panic_hook`은 옮기지 않았습니다. 저장소가 보관되었고, 마지막 푸시는 2022-12-04이며, crate는 2021-10-11의 0.1.7에 머물러 있습니다. 여전히 동작하고 여전히 문서화된 hook이지만, 활발히 유지보수된다고 서술하면 안 됩니다.
- `serde-wasm-bindgen`도 그 조직 밖에 있지만, 그 문서는 "요즘 `serde-wasm-bindgen`이 공식적으로 선호되는 접근"이며 "JSON보다 훨씬 작은 코드 크기 오버헤드"를 준다고 밝힙니다.

## 4. 버전과 툴체인

`official` — `wasm-bindgen`은 0.2.130입니다. MSRV 정책은 "라이브러리는 MSRV v1.81, CLI 도구와 그에 대응하는 지원 라이브러리는 MSRV v1.86"이라고 진술하며, 라이브러리 MSRV 2년 정책과 패치 릴리스에서의 MSRV 변경을 허용합니다(https://raw.githubusercontent.com/wasm-bindgen/wasm-bindgen/main/README.md). 게시된 메타데이터도 일치합니다. `rust_version = "1.81"`입니다.

`official` — CLI는 별도 crate인 `wasm-bindgen-cli`이며 라이브러리와 버전이 일치해야 합니다. `wasm-bindgen` crate와 CLI의 버전 불일치는 바인딩 시점의 하드 오류입니다. 툴체인 단계에서 둘을 함께 고정하거나, CLI를 `cargo install wasm-bindgen-cli --version <same>`으로 설치합니다.

`hypercore-default` — 모든 기여자가 같은 산출물을 빌드하도록 타깃을 `rust-toolchain.toml`에 둡니다.

```toml
[toolchain]
channel = "1.99"
components = ["rustfmt", "clippy"]
targets = ["wasm32-unknown-unknown"]
profile = "minimal"
```

`wasm-pack` 0.15.1이 CLI를 구동하고 `package.json`을 씁니다. 프로젝트가 분할, strip, 도구가 노출하지 않는 `--target` 조합을 필요로 하지 않는 한 손으로 만든 빌드 스크립트보다 이것을 씁니다.

## 5. 배포 타깃

`official` — `wasm-bindgen --target`은 `bundler`(기본), `web`, `nodejs`, `deno`, `no-modules`, `experimental-nodejs-module`, `module`을 받습니다(https://wasm-bindgen.github.io/wasm-bindgen/reference/deployment.html). 기본 출력은 모듈이 네이티브 ES 모듈이라고 가정하는데 오늘날 어떤 JavaScript 구현도 이를 지원하지 않으므로 번들러가 필요합니다. "`wasm-bindgen`과 완전히 호환되는 것으로 알려진 유일한 번들러는 webpack입니다. Rolldown도 `rolldown-plugin-wasm`으로 호환됩니다". `--target module`은 source phase import를 쓰고 "현재 ESBuild와 Node.js 24에서만 지원됩니다".

`hypercore-default` — 소비자로 고르고 그 선택을 진술합니다.

| Consumer | Target | Note |
|---|---|---|
| Webpack 또는 Rolldown 번들러 | `bundler` | 기본이고 문서화된 호환 경로 |
| 번들러 없는 페이지 | `web` | promise를 반환하는 `init()`을 냄 |
| CommonJS Node 도구 | `nodejs` | `require()` 스타일 출력 |
| Deno | `deno` | 런타임이 생성된 import를 읽을 때만 |

Vite 전용 설정은 이 스냅숏에서 확인하지 않았으므로, Vite + WASM 구성은 여기서 단정하지 않고 그 플러그인 자체 문서로 확인해야 합니다.

## 6. 크기: 올바른 파일 측정

`official` — `target/wasm32-unknown-unknown/release/foo.wasm` 원본은 "크기 최적화가 되어 있지 않으므로 측정하면 안 됩니다". wasm-bindgen CLI가 실행된 뒤 생성된 `foo_bg.wasm`을 측정합니다. CLI가 "불필요한 기능을 자동으로 모두 제거"하기 때문입니다(https://wasm-bindgen.github.io/wasm-bindgen/reference/optimize-size.html).

`official` — Rust and WebAssembly 책의 레버입니다. `lto = true`는 "LLVM이 함수를 인라인하고 제거할 기회를 훨씬 많이 주므로 … `.wasm`을 더 작게 만듭니다". `opt-level = "s"`나 `"z"`는 명시적 경고와 함께입니다. "`opt-level = "s"`가 `opt-level = "z"`보다 작은 바이너리를 낼 때가 있습니다. 항상 측정하세요!". `wasm-opt -Os`/`-Oz` 후처리는 "흔히 15-20%를 더 줄입니다"(https://rustwasm.github.io/docs/book/reference/code-size.html).

`hypercore-default` — 출하 모듈의 크기 프로필이며, Cargo 릴리스 기본값이 `lto = false`, `codegen-units = 16`, `opt-level = 3`, `panic = "unwind"`, `strip = "none"`이므로 모든 값이 명시적 선택입니다.

```toml
[profile.release]
lto = true
codegen-units = 1
opt-level = "z"
panic = "abort"
strip = "symbols"
```

`hypercore-default` — 측정 절차입니다. 빌드하고, wasm-bindgen을 실행하고, `*_bg.wasm`에 `stat -c%s`(또는 `wc -c`)를 적용하고, 레버를 하나 바꾼 뒤 반복합니다. 두 수치를 변경 노트에 기록합니다. `wasm-opt`는 Binaryen에서 오며, 이 스냅숏에서 설치 경로와 버전을 확인하지 않았으므로 이를 켜는 프로젝트는 설치 방법을 기록합니다.

## 7. panic과 abort 동작

`official` — wasm-pack: "기본적으로 WebAssembly에서 Rust panic은 `panic=abort`로 컴파일되며, panic 시 WebAssembly 인스턴스를 중단합니다". `--panic-unwind`는 nightly와 `-Z build-std=std,panic_unwind`, `-Cpanic=unwind`로 전환하고 `wasm-opt`에 `--enable-exception-handling`을 넘기며, 그렇게 해도 "실제 'panic = 복구 가능한 JavaScript 예외' 동작은 바인딩 계층의 런타임 글루를 필요로 합니다"(https://wasm-bindgen.github.io/wasm-pack/book/commands/build.html).

`official` — wasm-bindgen의 abort 기구도 조건부입니다. 하드 abort 감지와 `set_on_abort`는 "`panic=unwind`로 빌드할 때 자동으로 켜지고", `panic=abort`에서는 `--force-enable-abort-handler`를 넘겨야 합니다(https://wasm-bindgen.github.io/wasm-bindgen/reference/handling-aborts.html). `schedule_reinit()`은 두 모드 모두에서 동작합니다.

`hypercore-default` — `panic = "abort"`를 모듈의 정상 실패 모드로 받아들이고 실패를 읽을 수 있게 만듭니다.

```rust
#[wasm_bindgen(start)]
pub fn start() {
    console_error_panic_hook::set_once();
}
```

잡히지 않은 panic은 그러면 `RuntimeError: Unreachable executed` 대신 메시지가 붙은 `console.error` 줄로 나타납니다. hook crate는 보관되었고 오래되었습니다. 이는 진술할 유지보수 사실이고, 유일하게 문서화된 hook을 버릴 이유는 아닙니다. 복구 가능한 panic이 필요한 프로젝트는 nightly 요구와 글루 계층을 진술하며, 그것은 기본이 아닙니다.

`official` — `wasm32-unknown-unknown` 자체의 정확한 기본 panic 전략은 이 스냅숏에서 읽지 않았습니다. 위에서 단언하는 것은 `wasm-pack`과 WASI 진술입니다.

## 8. `web-sys` 기능

`official` — `web-sys`는 "각 웹 인터페이스를 cargo 기능 뒤에" 두어 빌드 시간을 줄이고, API 문서는 타입과 메서드마다 필요한 기능을 알려줍니다. 예를 들어 `Window::resize_to`는 `Window` 기능을 요구합니다(https://wasm-bindgen.github.io/wasm-bindgen/web-sys/using-web-sys.html).

`hypercore-default` — 코드가 만지는 인터페이스만 정확히 켭니다. 통째로 켜는 기능 목록이나 `features = ["all"]`은 빌드 시간을 배로 늘리고 모듈이 실제로 쓰는 API를 숨깁니다. 타입에 메서드가 없으면 빠진 기능을 먼저 확인하지, `js_sys` 캐스트로 달려가지 않습니다.

## 9. 타입 있는 경계

`official` — `tsify` 0.5.8은 `json`이 기본 기능이고, `js`는 "`serde-wasm-bindgen`을 통한 직렬화를 켜며 … 향후 버전에서 기본이 됩니다"(https://docs.rs/tsify/latest/tsify/). `into_wasm_abi`와 `from_wasm_abi` 속성은 `Ts<T>` 대신 폐기되었습니다. "그 경계가 실패를 보고할 수 없기" 때문입니다. `FromWasmAbi::from_abi`가 `Self`를 반환하므로 serde 실패는 `throw_str`를 강제하고, 이는 "소멸자를 실행하지 않아" 부분 역직렬화된 값과 이미 변환된 모든 인자를 누출합니다. `Ts<T>`는 (역)직렬화를 함수 안으로 옮겨 평범한 `Result`로 만듭니다. `Ts<Vec<T>>`는 지원되지 않으므로 `Vec<Ts<T>>`를 씁니다.

```rust
#[derive(serde::Serialize, serde::Deserialize, tsify::Tsify)]
pub struct Options {
    /// Rendered width in CSS pixels.
    pub width: u32,
}

#[wasm_bindgen]
pub fn render(options: Ts<Options>) -> Result<JsValue, JsValue> {
    // Convert `Ts<Options>` into `Options` here; the conversion returns a
    // `Result`, so a malformed argument is an error rather than an abort.
    // ...
}
```

derive가 TypeScript 선언을 생성하고 `Ts<T>`가 값을 나릅니다. 새 타입에 `into_wasm_abi`/`from_wasm_abi` 속성을 붙이지 않습니다. (역)직렬화를 실패할 수 없는 ABI 경로로 되돌리기 때문입니다. 정확한 변환 메서드 이름은 기억에서 옮기지 말고 설치된 `tsify` 버전 문서에서 확인합니다.

`official` — `serde_wasm_bindgen::to_value`와 `from_value`는 `HashMap`을 `Map`으로, 구조체를 객체로, `Vec`과 튜플을 배열로, `serde_bytes`를 `Uint8Array`로 매핑합니다. `Serializer::json_compatible()`은 "JSON 모양이 필요할 때" `serialize_missing_as_null`, `serialize_maps_as_objects`, `serialize_bytes_as_arrays`를 켭니다. `serde_wasm_bindgen::preserve`는 `Date`, `RegExp` 같은 JavaScript 객체를 그대로 통과시킵니다(https://docs.rs/serde-wasm-bindgen/latest/serde_wasm_bindgen/).

`hypercore-default` — 경계에는 `serde_json`과 문자열 대신 `serde-wasm-bindgen`을 쓰고, `json_compatible()`은 호출자와의 JSON 모양이 계약일 때만 고릅니다. 크기를 쓰고 JavaScript 고유 타입을 잃기 때문입니다.

`official` — 유용한 CLI 플래그입니다. `--keep-debug`, `--split-debug-info`와 `--debug-info-url`, `--no-typescript`, `--omit-imports`, `--split-linked-modules`(지연 로딩과 더 엄격한 CSP에 권장되지만 대부분의 번들러를 깨뜨림), `--js-string-builtins`(webpack이 실패해 기본 꺼짐), `--ts-typed-array-buffers`(기본 꺼짐, TypeScript 5.7 이상 소비자 필요)(https://wasm-bindgen.github.io/wasm-bindgen/reference/cli.html).

## Checklist

- [ ] WASM 타깃과 그 호스트를 기록했고, WASI 호스트에 `wasm32-unknown-unknown`을 쓰지 않았다.
- [ ] `[lib] crate-type`에 `cdylib`이 있고, 네이티브 테스트가 로직에 도달해야 하면 `rlib`를 더했다.
- [ ] `wasm-bindgen`과 JS 경계 형제 crate가 `[target.'cfg(target_arch = "wasm32")'.dependencies]`에 있다.
- [ ] `wasm-bindgen` crate와 `wasm-bindgen-cli` 버전이 일치한다.
- [ ] `rust-toolchain.toml`에 타깃이 있어 모든 기여자가 같은 모듈을 빌드한다.
- [ ] `--target` 배포 모드가 소비자와 맞고 번들러 호환성이 진술되어 있다.
- [ ] 크기를 rustc 원본이 아니라 `*_bg.wasm`에서 측정했다.
- [ ] 모든 크기 변경이 같은 명령에서 잰 before/after 수치를 기록한다.
- [ ] `web-sys` 기능이 쓰는 인터페이스와 정확히 일치한다.
- [ ] 경계 구조체가 `tsify`와 `Ts<T>`를 쓰고, 새 타입에 폐기된 `into_wasm_abi` 속성이 없다.
- [ ] 모듈 초기화에서 panic hook을 설치했고, hook crate의 유지보수 상태를 진술했다.
- [ ] 문서가 `rustwasm/*` URL을 인용하지 않는다.

## Sources

> Checked 2026-11-07. 사실은 `references/official/rust/rust-crates-2026-11-07.md`에 기록된 페이지에서 왔습니다.

| Claim | Source |
|---|---|
| 타깃 계층과 `wasm32-wasip1`/`wasm32-wasip2` 동작 | https://doc.rust-lang.org/rustc/platform-support.html, https://doc.rust-lang.org/rustc/platform-support/wasm32-wasip1.html, https://doc.rust-lang.org/rustc/platform-support/wasm32-wasip2.html |
| `wasm32-unknown-unknown` 설계, 무력한 `std`, 타깃 범위 의존성 | https://wasm-bindgen.github.io/wasm-bindgen/reference/rust-targets.html |
| `crate-type` 값과 적용 범위 | https://doc.rust-lang.org/cargo/reference/cargo-targets.html |
| 예제 `cdylib` manifest | https://raw.githubusercontent.com/wasm-bindgen/wasm-bindgen/main/examples/dom/Cargo.toml |
| rustwasm 조직 선셋과 새 거처 | https://blog.rust-lang.org/inside-rust/2025/07/21/sunsetting-the-rustwasm-github-org/, https://raw.githubusercontent.com/rustwasm/team/master/README.md |
| `wasm-bindgen` 0.2.130, MSRV 정책, 별도 CLI crate | https://raw.githubusercontent.com/wasm-bindgen/wasm-bindgen/main/README.md, https://crates.io/api/v1/crates/wasm-bindgen |
| `wasm-pack` 0.15.1 유지보수와 기본 panic 동작 | https://raw.githubusercontent.com/wasm-bindgen/wasm-pack/master/README.md, https://wasm-bindgen.github.io/wasm-pack/book/commands/build.html |
| 배포 `--target` 값과 번들러 호환성 | https://wasm-bindgen.github.io/wasm-bindgen/reference/deployment.html |
| `*_bg.wasm` 측정, 크기 레버, `wasm-opt`의 15–20% 수치 | https://wasm-bindgen.github.io/wasm-bindgen/reference/optimize-size.html, https://rustwasm.github.io/docs/book/reference/code-size.html |
| abort 처리와 `set_on_abort` 조건 | https://wasm-bindgen.github.io/wasm-bindgen/reference/handling-aborts.html |
| `console_error_panic_hook` 0.1.7과 보관된 저장소 | https://docs.rs/console_error_panic_hook/latest/console_error_panic_hook/ |
| `web-sys` 인터페이스별 기능 게이팅 | https://wasm-bindgen.github.io/wasm-bindgen/web-sys/using-web-sys.html |
| `tsify`의 `Ts<T>`, 폐기된 ABI 속성, `Ts<Vec<T>>` | https://docs.rs/tsify/latest/tsify/ |
| `serde-wasm-bindgen` 매핑, `json_compatible()`, `preserve` | https://docs.rs/serde-wasm-bindgen/latest/serde_wasm_bindgen/ |
| wasm-bindgen CLI 플래그 | https://wasm-bindgen.github.io/wasm-bindgen/reference/cli.html |
| 크기 프로필, 측정 절차, panic hook 규칙 | 이 패키지의 규약이며 공식 Rust 요구가 아님 |
