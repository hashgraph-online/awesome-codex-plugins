# 성능

> 릴리스 빌드를 재고, 첫 노력은 배포 프로필, 풀 크기, 응답 바이트에 쓰며, 개발 빌드 숫자를 근거로 인용하지 않습니다.

Axum 서비스에서 느림, 처리량, 지연, 메모리, 바이너리 크기, "최적화"를 언급할 때 읽습니다. 아키텍처 트랙은 코드가 어디에 사는지를 소유하고, 이 파일은 측정된 비용을 바꾸는 레버를 소유합니다.

## 먼저 측정

어떤 레버도 건드리기 전에 릴리스 빌드에서만 숫자를 기록합니다. Cargo 기본값은 성능 프로필이 아닙니다: `opt-level = 3`, `lto = false`, `codegen-units = 16`, `panic = 'unwind'`, `strip = "none"` [L-58].

```bash
cargo build --release
cargo build --release 2>&1 | tail -1        # after each profile change, same machine
```

그다음 저장소 자체의 부하 도구나 벤치 하네스로 빌드된 서버에 대해:

- 대표 읽기 라우트 하나와 쓰기 라우트 하나의 p50/p95 지연과 초당 요청 수를 기록합니다.
- 가장 무거운 JSON 응답의 압축 전후 바이트를 기록합니다.
- 부하 실행 후 프로세스 RSS와 `ls -l target/release/<bin>`으로 바이너리 크기를 기록합니다.
- 실제 설정에서 유효 풀 크기와 워커 수를 확인하지, 기억에서 옮겨 적지 않습니다.

여기서 효과를 측정할 수 없는 레버(부하 생성기, 스테이징 데이터베이스, 릴리스 툴체인이 없음)는 측정하지 못했다고 보고합니다. 이득으로 주장하지 않습니다.

## 규칙

요청을 처리하는 Axum 바이너리에서 흔한 영향 순서입니다.

1. **`official` — 릴리스 프로필을 명시합니다.** 서비스에는 `lto = "thin"`, `codegen-units = 1`, `strip = true`, `panic = "abort"`로 시작합니다. `"thin"`은 "실행 시간이 상당히 짧으면서 'fat'과 비슷한 성능 이득"을 내고, 최종 바이너리와 최고 속도가 링크 시간보다 중요하면 `true`/"fat"이 의존성 그래프 전체를 덮습니다 [L-58]. 기본값이 `lto = false`, `codegen-units = 16`이므로 이 설정은 항상 선택 사항입니다 [L-58].
2. **`official` — SQLx 풀을 운영과 데이터베이스 자체 한도에 맞춰 정합니다.** 크레이트 기본값은 `max_connections: 10`, `min_connections: 0`, `acquire_timeout: 30s`, `idle_timeout: 10 min`, `max_lifetime: 30 min`, `test_before_acquire: true`이고, `Pool::connect`는 이 기본값이 "주로 테스트와 가벼운 용도에 적합"하다고 말합니다 [L-59][L-60]. `max_connections × replicas ≤ 서버 max_connections − superuser 예약분`으로 제한하며, PostgreSQL 기본은 100 슬롯에 3이 예약되어 97을 쓸 수 있습니다 [L-60].
3. **`official` — 실제로 서비스하는 코덱으로만 응답 바이트를 줄입니다.** `CompressionLayer`는 feature gate(`compression-br`, `compression-gzip`, `compression-zstd`, `compression-deflate`)이고 `Accept-Encoding`을 존중하므로 클라이언트가 실제로 협상하는 부분집합만 켭니다 [L-61]. `(StatusCode, Version, &HeaderMap, &Extensions)`에 대한 predicate로 `compress_when`을 써서 오류 응답과 이미 압축된 payload를 건너뜁니다 [L-69].
4. **`official` — 요청과 body를 따로 제한합니다.** `TimeoutLayer::with_status_code(StatusCode::REQUEST_TIMEOUT, Duration::from_secs(30))`은 연결을 끊지 않고 의도한 상태를 반환합니다 [L-62]. 순수 `TimeoutLayer`는 요청을 제한할 뿐 body는 아닙니다. 응답이 끝없이 흐를 수 있으면 `RequestBodyTimeoutLayer`/`RequestBodyDeadlineLayer`와 `ResponseBodyTimeoutLayer`를 더하고, "idle timeout과 absolute deadline을 모두 원하면 둘 다" 씁니다 [L-62].
5. **`official` — 측정이 다른 결론을 주지 않으면 tokio 워커 스레드를 기본값으로 둡니다.** 기본값은 `available_parallelism`으로 구한 시스템 병렬성이고 `TOKIO_WORKER_THREADS`를 덮어쓰며, 문서는 이 값을 "작은 쪽으로 유지"하라고 권합니다. `current_thread`는 `worker_threads`를 무시합니다 [L-57]. 나머지 knob(`max_blocking_threads`, `thread_keep_alive`, `thread_stack_size`, `event_interval`, `global_queue_interval`, `disable_lifo_slot`)은 근거가 있을 때만 바꿉니다 [L-57].
6. **`hypercore-default` — allocator가 비용이라는 증거가 선 뒤에만 mimalloc을 검토합니다.** `#[global_allocator] static GLOBAL: MiMalloc = MiMalloc;`은 교체가 간단하지만 크레이트가 실제 tradeoff를 적습니다. `secure` feature는 guard page, 무작위 할당, 암호화된 free list를 더하고 "성능 패널티가 보통 약 10%"입니다 [L-63]. 공식 axum이나 tokio 문서가 사용자 allocator를 권하지 않으므로 이 항목은 스택의 규칙이 아니라 팀 선택으로 다룹니다 [L-63].
7. **`hypercore-default` — 요청 span을 싸게 유지합니다.** `tower-http`의 `TraceLayer`와 `tracing`이 지원 경로입니다. body를 포맷하지 말고 필드(메서드, 경로 템플릿, 상태, 지연)를 더하며, poll hot path 안에서 log를 남기지 않습니다. layer 순서는 미들웨어 규칙이 소유하고, 이 파일은 p99가 logging에 지배될 때 tracing 설정이 측정 레버라고만 말합니다.

## 하지 말 것

- `cargo run`이나 디버그 `cargo build` 숫자를 성능 결과로 인용하지 않습니다. 디버그 빌드는 최적화가 없고 그 시간은 릴리스 바이너리에 대해 아무것도 말하지 않습니다 [L-58].
- `lto`, `codegen-units`, `panic`, `strip`을 바꾸고 before/after 빌드 시간과 실행 숫자 없이 이득이라 부르지 않습니다. 넷 모두 빌드 시간과 실행 성능의 tradeoff입니다 [L-58].
- "스레드가 많으면 빠르다"는 이유로 `worker_threads`를 손으로 정하지 않습니다. 기본값이 이미 시스템 병렬성이고 문서는 작게 유지하라고 권합니다 [L-57].
- SQLx 기본값을 운영에 내보내고 데이터베이스를 탓하지 않습니다. `max_connections: 10`과 `test_before_acquire: true`는 테스트 설정입니다 [L-59][L-60].
- 레플리카 하나에서만 맞는 풀 크기를 모든 앱 레플리카에 주지 않습니다. 모든 애플리케이션의 합이 서버 한도 아래에 있어야 합니다 [L-60].
- 이미 압축된 응답, 아주 작은 응답, 바이너리에 압축을 더하지 않고, `compress_when`을 빼서 `CompressionLayer`가 오류 body까지 다시 쓰게 두지 않습니다 [L-61][L-69].
- 지연 예산을 가진 채 `secure` feature를 켠 `mimalloc`을 넣지 않고, 그것을 공식 axum 지침으로 제시하지 않습니다 [L-63].
- 검토 안에서 비동기 런타임 교체, 다른 TLS 백엔드, 드라이버 교체를 "성능 수정"으로 꺼내지 않습니다. 그 결정은 `rules/axum/platform.md`와 아키텍처 트랙이 소유합니다.

## 체크리스트

- [ ] 주장하는 모든 이득에 릴리스 빌드의 before/after 숫자가 있습니다.
- [ ] `[profile.release]`가 `lto`, `codegen-units`, `panic`, `strip`을 명시하고, 선택을 Cargo 기본값과 대조해 설명합니다.
- [ ] 풀 크기가 명시되어 있고 `max_connections × replicas`가 데이터베이스 한도에서 superuser 예약분을 뺀 값에 들어갑니다.
- [ ] `acquire_timeout`, `idle_timeout`, `max_lifetime`, `test_before_acquire`가 운영 의도와 맞습니다.
- [ ] 압축 코덱이 feature로 켜져 있고 `compress_when`이 오류와 압축 불가 content를 건너뜁니다.
- [ ] 요청 타임아웃이 상태를 반환하고, 스트리밍 응답에는 body 수준 타임아웃이 있습니다.
- [ ] 워커 스레드 수가 기본값이거나 기록된 측정으로 바뀌었습니다.
- [ ] 사용자 allocator를 쓴다면 프로파일로 정당화했고 지연 예산 아래에서 `secure`를 켜지 않았습니다.
- [ ] 변경이 `stacks/axum/architecture-rules.md`의 게이트와 `rules/setup/rust.md`의 검사를 모두 통과시킵니다.

## Sources

> 확인 2026-11-07. 프로필과 런타임 의미는 Cargo Book, tokio·SQLx API 문서, tower-http 크레이트 문서에서 확인했고 version은 crates.io registry에서 가져왔습니다.

| 주장 | 출처 |
|---|---|
| 릴리스 프로필 기본값과 `lto`/`codegen-units` 의미 | [Profiles – The Cargo Book](https://doc.rust-lang.org/cargo/reference/profiles.html) |
| tokio `worker_threads` 기본값, 환경변수 override, tuning knob | [tokio::runtime::Builder](https://docs.rs/tokio/latest/tokio/runtime/struct.Builder.html) |
| SQLx 풀 기본값(`max_connections`, timeout, `test_before_acquire`) | [sqlx pool options source](https://raw.githubusercontent.com/launchbadge/sqlx/main/sqlx-core/src/pool/options.rs), [sqlx::Pool](https://docs.rs/sqlx/latest/sqlx/struct.Pool.html) |
| PostgreSQL 연결 한도와 다중 애플리케이션 풀 예산 | [sqlx::Pool](https://docs.rs/sqlx/latest/sqlx/struct.Pool.html) |
| `CompressionLayer` 코덱 feature와 `Accept-Encoding` 동작 | [tower_http::compression](https://docs.rs/tower-http/latest/tower_http/compression/index.html) |
| `compress_when` predicate 시그니처 | [tower-http compression predicate source](https://raw.githubusercontent.com/tower-rs/tower-http/main/tower-http/src/compression/predicate.rs) |
| 요청·body 타임아웃 layer, `with_status_code` | [tower_http::timeout](https://docs.rs/tower-http/latest/tower_http/timeout/index.html) |
| mimalloc 전역 allocator와 `secure` feature 패널티 | [mimalloc crate](https://docs.rs/mimalloc/latest/mimalloc/) |
| 현재 크레이트 version(axum 0.8.9, tokio 1.54.1, tower-http 0.7.1, mimalloc 0.1.52) | [crates.io API](https://crates.io/api/v1/crates/axum) |
