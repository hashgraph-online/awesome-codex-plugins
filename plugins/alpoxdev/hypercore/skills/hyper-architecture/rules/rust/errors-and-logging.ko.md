# 오류와 로깅

> 모든 라이브러리 경계에 `thiserror` enum을, 애플리케이션 경계에 `anyhow`를 두고, 맨 위에서 종료 코드를 한 번 매핑하며, 진단은 stderr로 쓰는 `tracing` subscriber를 둡니다.

이 파일의 규칙은 `references/official/rust/rust-crates-2026-11-07.md`에서 연 페이지가 그대로 진술한 경우 `official`, 이 패키지가 기본값으로 고른 경우 `hypercore-default`로 표시합니다.

## 1. 오류 라이브러리 둘, 역할 둘

`official` — `anyhow`는 애플리케이션 오류 타입입니다. 그 문서는 사람에게 실패를 보고하는 코드에 `anyhow::Result<T>`를 쓰라고 설명하고, 이 crate가 "`derive(Error)` 매크로를 묶어 제공하지 않는다"고 진술합니다(https://docs.rs/anyhow/latest/anyhow/). `thiserror`는 `std::error::Error`를 derive하며 그 문서는 이 crate가 "의도적으로 공개 API에 나타나지 않는다"고 말합니다(https://docs.rs/thiserror/latest/thiserror/).

`hypercore-default` — 이 패키지가 쓰는 분담입니다.

| Layer | Type | Why |
|---|---|---|
| 라이브러리 crate 공개 API | `thiserror` enum | 호출자가 변형을 match할 수 있고 오류가 계약의 일부입니다 |
| 바이너리 `run()`과 명령 | `anyhow::Result` | 실패 지점에서 맥락을 더하고 타입은 공개되지 않습니다 |
| 도메인 함수 | `thiserror` enum 또는 `Result<T, DomainError>` | 도메인 실패를 빠짐없이 match할 수 있습니다 |
| WASM export 함수 | 경계에서 `Result<T, JsValue>`, 안쪽은 타입 있는 오류 | JavaScript 경계는 Rust enum을 실을 수 없습니다 |
| MCP 도구 handler | SDK의 `Result<CallToolResult, McpError>` | 프로토콜 오류 모양을 SDK가 소유합니다 |

`official` — 둘을 섞는 방식은 정의된 이음매 하나로 지원됩니다. `anyhow::Error`를 감싼 `thiserror` 변형에 `#[error(transparent)]`를 붙이면 `Display`와 `source`를 위임합니다(https://docs.rs/thiserror/latest/thiserror/). 라이브러리 오류가 명령을 거쳐 위로 올라가야 할 때 애플리케이션 계층에서 정확히 한 번 씁니다.

`hypercore-default` — 라이브러리 crate의 공개 함수 시그니처에 `anyhow::Error`를 두지 않습니다. 호출자가 match할 수 없고, 앞으로 생길 모든 변형이 돌발 상황이 됩니다.

## 2. 장식이 아니라 맥락

`hypercore-default` — 정보가 존재하고 나중에 재구성할 수 없는 곳에서 맥락을 더합니다.

```rust
let text = std::fs::read_to_string(&path)
    .with_context(|| format!("reading config {}", path.display()))?;
```

- 실패 경계를 넘을 때마다 `.context(...)` 하나입니다. 줄마다 하나가 아닙니다.
- 맥락은 함수가 아니라 자원을 명명합니다. `"reading config /etc/app.toml"`이 `"failed in load"`보다 낫습니다.
- 메시지가 이미 자원을 명명한 오류를 다시 감싸지 않습니다. 중첩된 중복은 소음으로 읽힙니다.
- `anyhow`의 backtrace는 Rust 1.65 이상에서 캡처되고 `RUST_BACKTRACE`나 `RUST_LIB_BACKTRACE`로 표시됩니다(https://docs.rs/anyhow/latest/anyhow/). backtrace를 직접 출력하지 않습니다.

`official` — `unwrap()`과 `expect()`는 panic합니다. 바이너리에서는 종료 코드 101로, WASM 모듈에서는 인스턴스 중단으로, 서버에서는 태스크 종료로 이어집니다. 타입 시스템이 표현할 수 없는 불변 조건에만 남기고, 그 조건을 메시지에 진술합니다.

## 3. 종료 코드

`official` — 종료 코드 0–255는 이식 가능하고, "Rust는 프로세스가 panic하면 종료 코드 `101`을 설정합니다"(https://rust-cli.github.io/book/in-depth/exit-code.html). 책은 서로 다른 실패 종류의 어휘로 BSD `sysexits` — `exitcode::USAGE`, `CONFIG`, `DATAERR`, `NOINPUT`, `IOERR` 등 — 를 가리킵니다.

`official` — clap은 이미 파싱 실패를 소유합니다. `Error::exit`는 "`stderr`에 출력하고 상태 `2`로 종료하거나 `stdout`에 출력하고 상태 `0`으로 종료"하며, `exit_code()`는 오류 종류가 stderr에 쓰는 경우에만 정확히 2를 반환합니다(https://docs.rs/clap/latest/clap/error/struct.Error.html). 따라서 `--help`와 `--version`은 stdout으로 0을, 잘못된 플래그는 프로그램 자체 코드가 돌기 전에 stderr로 2를 냅니다.

`hypercore-default` — 정책입니다.

| Outcome | Code | Owner |
|---|---|---|
| 성공 | 0 | `ExitCode::SUCCESS` |
| 도움말 또는 버전 요청 | 0 | clap |
| 인자 파싱 실패 | 2 | clap, 건드리지 않음 |
| 파서가 감지할 수 없는 사용 오류 | `exitcode::USAGE`(64) | 바이너리 |
| 설정이나 입력 데이터가 잘못됨 | `exitcode::CONFIG`/`DATAERR` | 바이너리 |
| 환경이나 I/O 실패 | `exitcode::IOERR` | 바이너리 |
| panic | 101 | Rust, 직접 쓰지 않음 |

```rust
fn main() -> std::process::ExitCode {
    let cli = Cli::parse();               // clap handles help/version/parse errors
    init_tracing(cli.verbose, cli.quiet);
    match app::run(cli) {
        Ok(()) => std::process::ExitCode::SUCCESS,
        Err(err) => {
            tracing::error!("{err:#}");
            std::process::ExitCode::from(exitcode_for(&err))
        }
    }
}
```

- 호출 경로 안에서 `process::exit`를 부르는 대신 `main`에서 `ExitCode`를 반환합니다. 소멸자와 버퍼링된 writer가 끝까지 돕니다.
- 오류 종류를 코드로 매핑하는 곳은 함수 하나입니다. 매핑 지점이 둘이면 어긋납니다.
- `exitcode`는 책의 권고지만, 이 스냅숏에서 현재 버전과 유지보수 상태를 확인하지 않았습니다. 이미 의존성이 아니라면 같은 값을 가진 평범한 상수도 허용되며 근거를 기록합니다.
- WASM 모듈과 MCP 서버에는 설정할 종료 코드가 없습니다. WASM export는 JavaScript에 `Result`를 반환하고, MCP 서버는 프로토콜로 실패를 보고합니다.

## 4. 로깅

`official` — `tracing` 이벤트가 프로그램 산출물이 아닌 모든 것에서 `println!`을 대체합니다. `tracing-subscriber`의 기본 기능은 `ansi`, `fmt`, `smallvec`, `std`, `tracing-log`이고 `env-filter`는 그 안에 없으므로, `EnvFilter`는 명시적 기능을 요구합니다(https://docs.rs/tracing-subscriber/latest/tracing_subscriber/).

```toml
[dependencies.tracing-subscriber]
version = "0.3"
features = ["env-filter"]
```

`official` — `EnvFilter::DEFAULT_ENV`는 `RUST_LOG`이고, `from_default_env()`는 변수가 비었거나 없을 때 "ERROR 레벨을 켜는 기본 지시문"을 추가합니다(https://docs.rs/tracing-subscriber/latest/tracing_subscriber/). 따라서 설정하지 않은 실행은 장황하지 않고 조용하며, CLI가 원하는 동작입니다.

`official` — 사람용 로그에 관한 CLI 책의 지침은 기본 레벨 `info`, `grep`이 동작하는 일관된 접두사, `--verbose`나 `RUST_LOG`로 고르는 상세도입니다(https://rust-cli.github.io/book/in-depth/human-communication.html).

`hypercore-default` — 설정입니다.

```rust
use tracing_subscriber::{fmt, EnvFilter};

pub fn init(verbose: u8, quiet: bool) {
    let default = match (verbose, quiet) {
        (_, true) => "error",
        (0, _) => "warn",
        (1, _) => "info",
        (2, _) => "debug",
        _ => "trace",
    };
    let filter = EnvFilter::try_from_default_env()
        .unwrap_or_else(|_| EnvFilter::new(default));
    fmt()
        .with_env_filter(filter)
        .with_writer(std::io::stderr)     // stdout stays the deliverable
        .without_time()                   // a CLI log line rarely needs a timestamp
        .init();
}
```

- 명시적 플래그가 환경 변수보다 앞섭니다. `--verbose`가 주어졌으면 `RUST_LOG`를 이겨야 합니다. 아니면 그 플래그는 거짓말입니다.
- `.with_writer(std::io::stderr)`는 관례가 아니라 구조입니다. stdio MCP 서버에서는 스타일이 아니라 프로토콜 요구입니다.
- subscriber는 하나이고, 프로세스 경계에서 한 번 초기화합니다. 라이브러리는 `.init()`을 호출하지 않습니다. 두 번째 호출은 panic합니다.
- 명령과 도메인 함수의 `tracing::instrument`는 인자를 값싸게 렌더하고 span이 실제 맥락을 더할 때만 씁니다. 핫 루프와 비밀을 기록할 수 있는 곳에는 쓰지 않습니다.

## 5. stdout과 stderr

`official` — `std::io::IsTerminal`은 사람과 파이프를 구분하는 표준 방법입니다(https://rust-cli.github.io/book/in-depth/machine-communication.html). 기계 출력에 관한 책의 규칙은 메시지당 JSON 문서 하나, 즉 줄 단위 JSON이고, 그 예시는 모든 레코드가 `type` 필드(`begin`, `match`, `end`, `summary`)를 갖는 ripgrep의 `--json` 스트림입니다.

`hypercore-default` — 라우팅 표입니다.

| Output kind | Stream | Condition |
|---|---|---|
| 사람을 위한 주 결과 | stdout | 항상 |
| 기계를 위한 주 결과 | stdout | `--json`이 있거나 stdout이 터미널이 아닐 때 |
| 진행, 스피너, "wrote 3 files" | stderr | 항상 |
| 경고와 오류 | stderr | 항상 |
| MCP 프로토콜 프레임 | stdout | stdio 전송에서만, 그것 말고는 없음 |
| 디버그와 진단 | stderr | `tracing`을 거쳐 |

- `--quiet` 플래그는 진행과 경고를 억제하며, 오류와 산출물은 절대 억제하지 않습니다.
- `--json` 스트림에 진행 줄을 끼우지 않습니다. 줄 단위로 파싱하는 소비자는 첫 사람 문장에서 실패합니다.
- 출력이 터미널이면 진행 표시가 ANSI를 쓸 수 있고, 아니면 아무것도 출력하지 않습니다. `anstream`의 `AutoStream`은 ANSI를 터미널 능력에 맞추고, clap은 이미 비TTY에서 색을 끕니다(https://docs.rs/anstream/latest/anstream/).

## 6. 절대 흘리지 않기

`hypercore-default` — 사용자에게 보이는 오류 메시지는 파일, 자원, 작업을 명명합니다. 아래는 담지 않습니다.

- 자격 증명, 토큰, 접속 문자열, 환경 전체 덤프.
- 서비스로 실행될 때 배포 배치를 드러내는 내부 경로.
- 운영자가 의도적으로 `RUST_BACKTRACE`를 설정하지 않은 한 스택 추적.

상세 원인은 stderr의 `error`나 `debug` 레벨에 기록하고 호출자에게는 짧은 메시지를 반환합니다. WASM 모듈에도 같은 규칙이 적용됩니다. 상세는 `console.error`로, 반환하는 `Result`에는 짧은 메시지를 싣습니다.

## Checklist

- [ ] 모든 라이브러리 공개 오류를 `thiserror` enum이 받치고, `anyhow`가 공개 시그니처에 없다.
- [ ] `anyhow::Result`는 `run`까지의 애플리케이션 계층에서만 쓴다.
- [ ] 둘을 섞는 `#[error(transparent)]` 이음매는 최대 하나이고 애플리케이션 계층에 있다.
- [ ] 실패 경계를 넘을 때마다 자원을 명명하는 `.context(...)`를 하나 더한다.
- [ ] `main`이 `ExitCode`를 반환하고 어느 경로도 `process::exit`를 부르지 않는다.
- [ ] 오류 종류를 종료 코드로 매핑하는 함수가 하나이고, 0·2·101이 의미를 유지한다.
- [ ] clap의 `Error`를 다시 포맷하거나 다시 종료하지 않는다.
- [ ] `EnvFilter`를 만드는 모든 곳에서 `tracing-subscriber`가 `env-filter`를 켠다.
- [ ] subscriber를 프로세스 경계에서 한 번 초기화하고 stderr에 쓴다.
- [ ] 명시적 상세도 플래그가 `RUST_LOG`보다 앞선다.
- [ ] stdout은 산출물만, 또는 대상이 stdio MCP 서버일 때 프로토콜 프레임만 담는다.
- [ ] `--quiet`가 진행과 경고를 억제하지만 오류와 산출물은 억제하지 않는다.
- [ ] 오류 메시지에 자격 증명, 토큰, 내부 경로가 없다.

## Sources

> Checked 2026-11-07. 사실은 `references/official/rust/rust-crates-2026-11-07.md`에 기록된 페이지에서 왔습니다.

| Claim | Source |
|---|---|
| `anyhow`는 애플리케이션 오류 타입이고 derive 매크로가 없으며, `RUST_BACKTRACE`로 backtrace 표시 | https://docs.rs/anyhow/latest/anyhow/ |
| `thiserror`가 `std::error::Error`를 derive하고 공개 API 밖에 머물며 `#[error(transparent)]`를 지원 | https://docs.rs/thiserror/latest/thiserror/ |
| 종료 코드 0–255, panic 코드 101, `exitcode` 권고 | https://rust-cli.github.io/book/in-depth/exit-code.html |
| clap은 도움말·버전을 stdout+0으로, 오류를 stderr+2로 매핑 | https://docs.rs/clap/latest/clap/error/struct.Error.html |
| `env-filter`는 기본 기능이 아니고 `RUST_LOG` 기본 지시문은 ERROR | https://docs.rs/tracing-subscriber/latest/tracing_subscriber/ |
| 기본 레벨 `info`, 일관된 접두사, `--verbose` 또는 `RUST_LOG` | https://rust-cli.github.io/book/in-depth/human-communication.html |
| `IsTerminal`, 줄 단위 JSON, ripgrep의 `type` 태그 레코드 | https://rust-cli.github.io/book/in-depth/machine-communication.html |
| `anstream` `AutoStream`이 ANSI를 터미널 능력에 맞춤 | https://docs.rs/anstream/latest/anstream/ |
| 종료 코드 표, subscriber 설정, 위 스트림 라우팅 표 | 이 패키지의 규약이며 공식 Rust 요구가 아님 |
