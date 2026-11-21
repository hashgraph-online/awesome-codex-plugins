# 플랫폼 설정

> 런타임, 설정, 관측성을 경계에 둡니다

---
## 안정 런타임 기준선

2026-11-05에 확인한 대로 axum은 0.8.9이고 MSRV는 1.80입니다. `axum::serve`는 `TcpListener`와 make-service로 변환되는 것, 즉 `Router`를 포함한 무엇이든 받습니다. axum 0.8부터 `serve`는 리스너와 IO 타입에 대해 제네릭이고, `Serve::tcp_nodelay`는 임의 스트림 속성을 위한 `serve::ListenerExt`로 대체되어 제거되었습니다.

- `#[tokio::main]`, 설정 로딩, tracing 설정, 풀 생성, 상태 조립, 리스너 바인딩, 정상 종료를 `main.rs`나 `bin/*.rs`에 둡니다.
- `Router`를 반환하는 조립 함수를 노출하고 바이너리가 그것을 호출합니다. 테스트도 같은 함수를 호출합니다.
- 설정을 한 번 타입이 있는 구조체로 만들고 검증한 뒤 `AppState`에 둡니다. handler에서 `std::env::var`를 호출하지 않습니다.
- tracing을 서비스 전에 한 번 초기화하고 `RUST_LOG`나 저장소의 필터 설정을 존중합니다. `EnvFilter`는 `tracing-subscriber`의 `env-filter` feature를 요구합니다(기본 feature가 아닙니다). `EnvFilter::from_default_env()`는 `RUST_LOG`를 읽고 변수가 비었거나 없으면 `ERROR` 수준 지시자를 더합니다.
- 기본 주소에 기대지 않고 명시적으로 바인딩하며, 고른 주소를 구조화된 필드로 기록합니다.
- 시그널 future와 함께 `with_graceful_shutdown`을 써서 처리 중인 요청이 SIGINT/SIGTERM에서 끝나게 합니다.
- health와 readiness 엔드포인트를 선택적 의존성과 분리합니다. readiness는 풀을 확인해도 되지만 liveness는 안 됩니다.
- CORS, 압축, 타임아웃, 요청 ID를 layer 스택에 두고 환경별 하드코딩이 아니라 타입이 있는 값으로 설정합니다.
- 아키텍처 검토 안에서 비동기 런타임, TLS 백엔드, 리스너 모델, 배포 manifest를 바꾸지 않습니다.

## 예시

`EnvFilter`는 `tracing-subscriber`의 기본 feature가 아닙니다(기본값은 `ansi`, `fmt`, `smallvec`, `std`, `tracing-log`). 따라서 의존성에서 이 feature를 켜야 하며, 그렇지 않으면 아래 코드는 컴파일되지 않습니다.

```toml
[dependencies]
tracing = "0.1"
tracing-subscriber = { version = "0.3", features = ["env-filter"] }
```

```rust
use std::net::SocketAddr;

use tokio::net::TcpListener;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    dotenvy::dotenv().ok();

    tracing_subscriber::registry()
        .with(tracing_subscriber::EnvFilter::from_default_env())
        .with(tracing_subscriber::fmt::layer())
        .init();

    let config = crate::config::Config::from_env()?;
    let pool = crate::db::pool::connect(&config.database_url).await?;
    let state = crate::state::AppState::new(config.clone(), pool);

    let app = crate::app(state);
    let addr: SocketAddr = config.bind_address()?;
    let listener = TcpListener::bind(addr).await?;

    tracing::info!(%addr, "server listening");
    axum::serve(listener, app)
        .with_graceful_shutdown(shutdown_signal())
        .await?;

    Ok(())
}

async fn shutdown_signal() {
    let ctrl_c = async {
        tokio::signal::ctrl_c().await.expect("ctrl-c handler");
    };

    #[cfg(unix)]
    let terminate = async {
        tokio::signal::unix::signal(tokio::signal::unix::SignalKind::terminate())
            .expect("SIGTERM handler")
            .recv()
            .await;
    };

    #[cfg(not(unix))]
    let terminate = std::future::pending::<()>();

    tokio::select! {
        _ = ctrl_c => {},
        _ = terminate => {},
    }

    tracing::info!("shutdown signal received");
}
```

## 설정 규칙

- 명시적 필드와 검증이 있는 타입 `Config` 구조체 하나를 씁니다. 필수 값이 없거나 잘못되었으면 시작을 실패시킵니다.
- 흩어진 읽기보다 파싱 지점 하나(`Config::from_env` 또는 저장소에 이미 있는 config crate)를 선호합니다.
- 비밀을 절대 기록하지 않습니다. `Debug` 구현에서 데이터베이스 URL과 토큰 필드를 가립니다.
- 환경별 값(바인드 주소, 로그 필터, CORS origin, 풀 크기)은 코드 분기가 아니라 설정에 둡니다.
- 시작 설정과 요청 시점 기능 플래그를 분리합니다.

## 관측성 규칙

- 요청 처리 주위에 span을 두고 `tracing`을 쓰며, HTTP 수준 span에는 `tower-http::trace::TraceLayer`를 씁니다.
- 요청 span에 메서드, 경로 템플릿, 상태, 지연을 넣습니다. 원시 본문이나 자격 증명은 절대 넣지 않습니다.
- 오류는 처리되는 경계에서 내부 원인과 함께 한 번만 기록합니다.
- 지표는 저장소에 이미 있는 exporter로만 노출합니다. 아키텍처 검토 안에서 새 텔레메트리 스택을 추가하지 않습니다.

## 검토 체크리스트

- `main.rs`가 serve, 종료, tracing, 설정, 풀 생성을 소유합니다.
- 조립 함수를 포트 바인딩 없이 테스트에서 호출할 수 있습니다.
- 설정이 타입이 있고 검증되며 흩어진 `env::var` 호출이 없습니다.
- 비밀이 로그와 오류 본문에서 가려집니다.
- Unix에서 정상 종료가 SIGINT와 SIGTERM에 연결되어 있습니다.
- health와 readiness 엔드포인트가 저렴하고 의존성 수준에 맞습니다.
- CORS와 타임아웃 값이 설정에서 옵니다.
- 라우트 모듈이 리스너를 바인딩하거나 전역 상태를 초기화하지 않습니다.

## Sources

> 확인 2026-11-07. 런타임과 serve 동작은 axum·tokio 문서로 다시 확인했고, `env-filter` feature 요구는 tracing-subscriber feature 목록과 `EnvFilter` 소스에서 확인했습니다.

| Claim | Source |
|---|---|
| 리스너와 make-service를 받는 `axum::serve`, `with_graceful_shutdown` | [axum serve](https://docs.rs/axum/latest/axum/fn.serve.html), [Serve](https://docs.rs/axum/latest/axum/serve/struct.Serve.html) |
| 리스너에 대한 `serve` 제네릭, `tcp_nodelay` 제거, MSRV 1.80 | [axum 0.8.0 changelog](https://github.com/tokio-rs/axum/blob/main/axum/CHANGELOG.md), [axum 0.8.9 changelog](https://github.com/tokio-rs/axum/blob/main/axum/CHANGELOG.md) |
| Tokio 런타임과 시그널 처리 | [tokio](https://docs.rs/tokio/latest/tokio/), [tokio::signal](https://docs.rs/tokio/latest/tokio/signal/index.html) |
| `tracing` subscriber 설정 | [tracing-subscriber](https://docs.rs/tracing-subscriber/latest/tracing_subscriber/) |
| `EnvFilter`가 `env-filter` feature를 요구하고 `from_default_env()`가 `RUST_LOG`를 읽음 | [tracing-subscriber features](https://docs.rs/tracing-subscriber/latest/tracing_subscriber/), [EnvFilter source](https://raw.githubusercontent.com/tokio-rs/tracing/master/tracing-subscriber/src/filter/env/mod.rs) |
| `TraceLayer` | [tower-http trace](https://docs.rs/tower-http/latest/tower_http/trace/index.html) |
