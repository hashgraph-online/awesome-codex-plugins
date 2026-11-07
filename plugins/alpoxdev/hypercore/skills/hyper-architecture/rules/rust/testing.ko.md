# 테스트

> 바이너리를 프로세스로 구동하고, 문자열 대신 전사 전체를 스냅숏하며, WASM 경계는 출하하는 런타임에서 테스트하고, MCP 도구는 전송 없이 호출합니다.

이 파일의 규칙은 `references/official/rust/rust-crates-2026-11-07.md`에서 연 페이지가 그대로 진술한 경우 `official`, 이 패키지가 기본값으로 고른 경우 `hypercore-default`로 표시합니다.

## 1. 실패할 수 있는 계층에서 테스트

`hypercore-default` — 프로필마다 먼저 테스트하는 표면이 다릅니다.

| Profile | Primary test | Tool |
|---|---|---|
| `cli` | 프로세스 동작: 종료 코드, stdout, stderr | `assert_cmd` + `predicates` |
| `cli` | 많은 작은 인자 사례와 사용 안내 | `trycmd` |
| `cli` | 큰 구조적 출력 | `insta` 스냅숏 |
| `wasm` | 실제 JS 또는 WASM 런타임 안의 export 함수 | `wasm-pack test`를 통한 `wasm-bindgen-test` |
| `mcp-server` | 평범한 Rust 함수로서의 도구 함수 | `cargo test` |
| `mcp-server` | 고른 전송에서의 왕복 한 번 | stdio 스트림을 구동하는 통합 테스트 |
| `library` | 공개 API 동작과 오류 변형 | `cargo test` 단위·통합 테스트 |

내부 도우미를 호출하는 단위 테스트는 CLI가 동작함을 증명하지 못하고, 종료 코드만 보는 프로세스 테스트는 메시지를 증명하지 못합니다. 둘 다 계약이면 둘 다 테스트합니다.

## 2. `assert_cmd`

`official` — `assert_cmd` 2.2.2는 `predicates`와 함께 `[dev-dependencies]`에 둡니다(https://rust-cli.github.io/book/print.html). 매크로 형식은 두 가지입니다. `assert_cmd::pkg_name!()`은 컴파일 시점에 `CARGO_PKG_NAME`을 읽고, `cargo_bin!("bin-name")`은 `env!("CARGO_BIN_EXE_<bin>")`을 해석합니다. 후자는 "통합 테스트/벤치 안에서만 동작"하는데 Cargo가 그 변수를 거기서만 설정하기 때문입니다(https://docs.rs/assert_cmd/latest/assert_cmd/, https://doc.rust-lang.org/cargo/reference/cargo-targets.html). `crate_name!`은 2.1.0부터 `pkg_name!` 대신 폐기되었고, `Command::cargo_bin`은 2.1.3에서 폐기가 해제되었습니다.

```toml
[dev-dependencies]
assert_cmd = "2.2"
predicates = "3.1"
```

```rust
use assert_cmd::Command;
use predicates::prelude::*;

#[test]
fn rejects_unknown_target() {
    Command::cargo_bin("mytool")
        .unwrap()
        .args(["build", "--target", "nope"])
        .assert()
        .failure()
        .code(2)
        .stdout(predicate::str::is_empty())
        .stderr(predicate::str::contains("invalid value"));
}
```

`hypercore-default` — 문장이 아니라 계약을 단언합니다.

- 종료 코드, stdout이 비었는지, stderr의 안정된 부분 문자열 하나입니다. 전체 메시지 동등성 단언은 도움말 문구 변경마다 깨집니다.
- `--json` 실행은 줄을 파싱하고 레코드 타입과 필드를 단언하며, 직렬화된 문자열을 단언하지 않습니다.
- 타임스탬프, PID, 임시 경로, 터미널 너비를 단언하지 않습니다. 출력에 그런 값이 있으면 가리거나 단언을 뺍니다.
- 종료 코드 표의 실패 종류마다 테스트 하나를 두어, 매핑이 바뀌면 크게 실패하게 합니다.

## 3. `trycmd`와 `insta`

`official` — `trycmd` 1.2.1은 `.toml`/`.trycmd` 사례 묶음 전체를 실행하고, `TRYCMD=dump`와 `TRYCMD=overwrite`가 스냅숏 워크플로를 제어합니다. `snapbox`(1.2.2)는 그 아래의 단발·맞춤 계층이고, `insta` 1.49.0은 `cargo-insta`를 통한 값·인라인 스냅숏을 덮습니다(https://docs.rs/trycmd/latest/trycmd/, https://raw.githubusercontent.com/mitsuhiko/insta/master/README.md).

`hypercore-default` — 선호가 아니라 모양으로 고릅니다.

| Need | Tool |
|---|---|
| 각각 명령줄과 기대 stdout/stderr인 호출 20개 | `trycmd` |
| 큰 구조 값 하나(보고서, 파싱된 manifest, 오류 트리) | `insta` |
| 맞춤 술어가 필요한 테스트 하나 | 평범한 `assert_cmd` |

`hypercore-default` — 규칙:

- 스냅숏 파일은 코드처럼 변경 검토에서 읽습니다. `TRYCMD=overwrite`와 `cargo insta accept`는 작성자 기계용이고 CI용이 아닙니다.
- 버전 문자열이나 경로만 바뀐 스냅숏 차이는 의도적으로 재생성하며, 무심코 병합하지 않습니다.
- 스냅숏 파일로 충분한 기대 출력을 테스트 소스에 손으로 유지하지 않습니다. 같은 문장 사본 둘이 어긋나는 길입니다.
- `insta` 인라인 스냅숏은 단언 옆에서 읽기 좋은 짧은 값에 씁니다. 여러 화면짜리 인라인 스냅숏은 파일로 갑니다.

## 4. `wasm-bindgen-test`

`official` — `wasm-bindgen-test` 0.3.80은 `#[wasm_bindgen_test]`를 제공하고, 브라우저는 `wasm-pack test --node --firefox --chrome --safari --headless`로 구동합니다(https://docs.rs/wasm-bindgen-test/latest/wasm_bindgen_test/, https://wasm-bindgen.github.io/wasm-pack/book/commands/test.html).

`hypercore-default` — 테스트 두 종류입니다.

- 순수 로직은 네이티브 `cargo test`로 테스트합니다. crate가 `cdylib` 옆에 `rlib`를 두고 로직이 `#[cfg(target_arch = "wasm32")]` 뒤에 있지 않은 이유입니다.
- 경계 동작은 WASM에서 테스트합니다. `web-sys`를 만지는 함수, `JsValue` 변환, promise, DOM 상호작용입니다.

`hypercore-default` — 규칙:

- CI는 모든 WASM crate에 최소 `wasm-pack test --node`를 돌립니다. 네이티브 테스트는 ABI 실수를 볼 수 없습니다.
- DOM API를 만지는 crate에는 브라우저 행렬(`--chrome --firefox --headless`)을 더합니다. CI 시간이 들지만 `--node`가 놓치는 부류를 잡습니다.
- async export 함수는 `async` 테스트 본문으로 테스트합니다. sleep으로 폴링하는 테스트는 불안정성입니다.
- 런타임이 없을 때 조용히 건너뛰는 `wasm-bindgen-test` 사례는 테스트가 없는 것보다 나쁩니다. 런타임이 있음을 단언합니다.

## 5. MCP 서버 테스트

`hypercore-default` — 계층 셋, 값싼 것부터 비싼 것 순입니다.

1. 도구 함수를 인자 구조체에 직접 호출합니다. 검증, 결과 매핑, 오류 변형을 덮고 평범한 `#[test]`입니다.
2. 도구 아래 서비스 함수를 테스트 상태로 호출합니다. 비즈니스 동작을 덮습니다.
3. 전송 테스트 하나. 바이너리를 띄우고, 줄 단위 `initialize` 요청과 `tools/call` 하나를 쓰고, 응답 줄을 읽어 결과를 단언합니다. stdout 오염, 프레이밍, 버전 협상을 한 번에 잡습니다.

`hypercore-default` — 추가 규칙:

- JSON-RPC 프레임을 직접 쓰는 테스트는 SDK의 serde 타입이 공개되어 있으면 그것으로 만들고, 프로토콜 모양 변경이 컴파일에서 실패하게 합니다.
- 원시 프레임 텍스트가 아니라 파싱한 응답 값을 단언합니다. 개행 처리와 키 순서는 계약이 아닙니다.
- HTTP 전송은 마운트한 경로에 실제 본문을 POST하고 JSON 또는 스트리밍 응답을 단언하는 테스트 하나를 둡니다. 라우터 테스트 하네스는 Axum 가이드와 같습니다.
- 고정 포트에 의존하는 전송 테스트를 남기지 않습니다. 포트 0을 바인딩해 할당된 포트를 읽거나 프로세스 내 서비스를 씁니다.
- stdio 테스트가 멈추면 서버의 EOF 처리 버그입니다. 자식에 타임아웃을 주고 종료시킨 뒤 캡처한 stderr와 함께 실패합니다.

## 6. 테스트하지 않을 것

`hypercore-default` — 컴파일러나 프레임워크를 다시 진술하는 테스트는 건너뜁니다.

- clap 플래그가 선언되어 존재한다는 것. 도움말 스냅숏이 이미 사용자 표면을 덮습니다.
- serde가 derive를 왕복한다는 것. 맞춤 직렬화나 이름 변경이 있는 매핑만 테스트합니다.
- WASM export가 등록되었다는 것. 호출합니다.
- mock이 시킨 대로 반환한다는 것.
- `cargo test` 안의 벽시계 시간, 할당 수, 바이너리 크기. 그것들은 `rules/rust/performance.md`의 것이고 단언이 아니라 측정입니다.

## 7. 스위트 실행

`hypercore-default` — 순서와 각 단계의 목적입니다.

```bash
cargo check --workspace --all-targets
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
wasm-pack test --node            # WASM crates
cargo test --test cli_transcripts # trycmd herd
```

- `--all-targets`가 `check`와 `clippy`를 테스트와 벤치까지 덮게 합니다.
- 무시된 테스트는 `#[ignore]` 이유와 함께 보고합니다. 조용히 건너뛴 스위트는 거짓 초록입니다.
- 네트워크, 데이터베이스, 브라우저가 필요한 테스트는 표시하고 문서화해, 그 의존성이 없는 기여자가 무엇이 돌지 않았는지 알게 합니다.

## Checklist

- [ ] 프로필마다 주 표면에 테스트가 있다. 프로세스 동작, WASM 경계, 도구 함수, 또는 공개 API.
- [ ] `assert_cmd`와 `predicates`가 dev-dependency이고 바이너리를 `cargo_bin!`으로 지목한다.
- [ ] CLI 단언이 종료 코드와 안정된 부분 문자열을 확인하고 전체 문장을 확인하지 않는다.
- [ ] 종료 코드 분류마다 테스트 하나가 있다.
- [ ] `trycmd`나 `insta`가 큰 기대 출력을 담고, 스냅숏을 변경에서 검토한다.
- [ ] 모든 WASM crate에 `wasm-pack test --node` 사례가 최소 하나 있고, DOM API를 만지면 브라우저 사례도 있다.
- [ ] 런타임이 없을 때 조용히 건너뛰는 WASM 테스트가 없다.
- [ ] MCP 도구를 평범한 함수로 테스트하고, 전송 테스트 하나가 실제 스트림을 구동한다.
- [ ] 전송 테스트가 고정 포트를 바인딩하지 않고 타임아웃 없이 멈출 수 없다.
- [ ] 타임스탬프, PID, 임시 경로, 직렬화 순서를 단언하는 테스트가 없다.
- [ ] `cargo check`, `cargo clippy`, `cargo test`를 `--all-targets`로 실행하고 무시된 테스트를 보고했다.

## Sources

> Checked 2026-11-07. 사실은 `references/official/rust/rust-crates-2026-11-07.md`에 기록된 페이지에서 왔습니다.

| Claim | Source |
|---|---|
| `assert_cmd`를 `predicates`와 함께 dev-dependency로 | https://rust-cli.github.io/book/print.html |
| `pkg_name!`, `cargo_bin!`, `CARGO_BIN_EXE_<name>` 범위, `crate_name!` 폐기 | https://docs.rs/assert_cmd/latest/assert_cmd/, https://doc.rust-lang.org/cargo/reference/cargo-targets.html |
| `trycmd` 사례 묶음과 `TRYCMD=dump`/`TRYCMD=overwrite`, 그 아래의 `snapbox` | https://docs.rs/trycmd/latest/trycmd/ |
| `cargo-insta`를 통한 `insta` 값·인라인 스냅숏 | https://raw.githubusercontent.com/mitsuhiko/insta/master/README.md |
| `wasm-bindgen-test`와 `wasm-pack test` 런타임 플래그 | https://docs.rs/wasm-bindgen-test/latest/wasm_bindgen_test/, https://wasm-bindgen.github.io/wasm-pack/book/commands/test.html |
| `cdylib`과 `rlib`가 네이티브 테스트를 가능하게 함 | https://doc.rust-lang.org/cargo/reference/cargo-targets.html |
| 전송 테스트가 실행해야 하는 `rmcp` stdio 프레이밍과 EOF 동작 | https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/stdio.md |
| 테스트 계층, 단언 규칙, skip 정책 | 이 패키지의 규약이며 공식 Rust 요구가 아님 |
