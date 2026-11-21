# Runtime Evidence

## Contents

1. [사용법](#1-사용법)
2. [Node.js](#2-nodejs)
3. [Python](#3-python)
4. [Rust](#4-rust)
5. [Go](#5-go)
6. [네이티브 바이너리](#6-네이티브-바이너리)
7. [조용한 실패 표](#7-조용한-실패-표)
8. [Sources](#sources)

## 1. 사용법

probe는 가설 하나에 답한다. 두 경쟁 가설 아래에서 다르게 읽히는 probe를 고른다. 어느 쪽이어도 똑같이 읽히는 probe는 증거가 아니다.

- capability를 먼저 정하고 명령을 고른다. 런타임의 플래그 묶음은 버전마다 바뀌므로, 가정한 버전이 아니면 `--help`로 확인한다.
- 소스 편집이 필요 없는 probe를 먼저 쓴다. 외부 probe로 값을 읽을 수 없을 때만 소스를 고친다.
- 명령과 출력을 그대로 기록한다. 출력을 인용하지 않은 probe는 다음 엔지니어가 다시 확인할 수 없다.
- 이 probe는 값을 관찰할 뿐 아무것도 고치지 않는다. 이 파일의 어떤 항목도 디버거를 열거나, 돌고 있는 프로세스에 붙거나, 바이너리를 계측하지 않는다.

## 2. Node.js

| 질문 | Probe |
|---|---|
| 실제로 도는 런타임과 버전은? | `node -v`, `which -a node`, `npm ls --depth=0`, TypeScript면 `npx tsx --version` |
| 내가 읽은 모듈이 실제 로드되는 모듈인가? | `node -e "console.log(require.resolve('<module>'))"`, ESM이면 `node --input-type=module -e "console.log(import.meta.resolve('<module>'))"` |
| 쓰는 지점에서 환경 변수가 설정돼 있는가? | 같은 런처로 `node -e "console.log(JSON.stringify({KEY: process.env.KEY}))"` |
| 처리되지 않은 rejection이 새고 있는가? | 스크래치 진입점에 `process.on('unhandledRejection', e => { console.error(e); process.exitCode = 1 })`를 넣거나 `--trace-uncaught`로 실행 |
| 어떤 비동기 작업이 아직 대기 중인가? | `node --report-on-signal`과 `SIGUSR2` 신호로 보고서를 받아 `libuv` 핸들을 읽거나, 스크래치 진입점에서 `process._getActiveHandles()` 확인 |
| 스택이 소스를 가리키는가, 트랜스파일 출력을 가리키는가? | `--enable-source-maps`로 실행하고 두 트레이스를 비교 |
| 종료 코드가 실패와 맞는가? | `node script.js; echo "exit=$?"` — 미처리 rejection이 예전 버전에서는 0으로 끝난 사례가 있다 |
| 서버가 클라이언트가 호출하는 곳에서 듣고 있는가? | `lsof -nP -iTCP -sTCP:LISTEN`으로 설정 포트와 비교 |

`--trace-warnings`는 경고의 발생 지점을 보여 준다. `--trace-sync-io`는 타이밍 가설에서 동기 I/O를 찾는다.

## 3. Python

| 질문 | Probe |
|---|---|
| 어떤 인터프리터가 도는가? | `which -a python3`, `python3 -VV`, `python3 -c "import sys; print(sys.executable, sys.prefix)"` |
| 어떤 모듈 파일이 import됐는가? | `python3 -c "import m; print(m.__file__)"`, `.pth`나 로컬 그림자 파일이 있는 패키지면 `sys.path`도 출력 |
| 설치된 버전이 선언한 버전인가? | `python3 -m pip show <pkg>` 또는 `importlib.metadata.version('<pkg>')` |
| 예외가 삼켜졌는가? | `-X dev`로 실행하고 `sys.excepthook`을 읽고, 맨 `except`, `except Exception: pass`, `contextlib.suppress`를 찾는다 |
| asyncio 작업이 조용히 실패했는가? | 스크래치 진입점에 `loop.set_exception_handler`를 넣거나, 종료 시 `asyncio.all_tasks()`의 대기 작업을 확인 |
| 경고가 원인인가? | `python3 -W error::DeprecationWarning`으로 그 분류를 실패로 바꿔 보이게 한다 |
| 호출 지점의 값이 기대한 값인가? | 같은 입력으로 그 함수를 직접 호출하는 스크래치 스크립트를 임시 디렉터리에서 돌려 값을 출력한다. 서버 전체를 띄우는 것보다 직접 호출이 좁다 |
| 프로세스가 어떤 파일을 여는가? | import 순서는 `python3 -X importtime`, 파일은 Linux `strace -f -e trace=openat`, macOS는 허용될 때 `dtruss` |

재현의 기본 실행으로 `python3 -X dev`를 선호한다. 정상 실행이 숨기는 자원 경고와 unraisable 예외가 드러난다.

## 4. Rust

| 질문 | Probe |
|---|---|
| 어떤 빌드가 도는가? | `cargo build --message-format=json`의 `compiler-artifact` 레코드에서 `executable`을 고르고 `cargo metadata`의 타깃과 비교 |
| debug 빌드인가 release 빌드인가? | 가능하면 `cargo run -- --version`, `target/debug`와 `target/release` 비교, 바이너리는 `file <binary>`로 `with debug_info` 확인 |
| panic이 정확히 어디서 났는가? | `RUST_BACKTRACE=1 cargo run`, 짧은 트레이스가 인라인되면 `RUST_BACKTRACE=full` |
| 오류가 버려지고 있는가? | `.unwrap_or_default()`, `let _ = `, `.ok()`, `if let Ok(_)`, `Err(_) => {}`를 찾는다 |
| panic이 잡혀서 숨는가? | `catch_unwind`, `panic::set_hook`을 찾는다. 실행이 읽지 않는 sink에 기록하는 hook은 조용한 실패다 |
| 어떤 feature 플래그가 켜졌는가? | `cargo tree -e features -i <crate>`, `cargo metadata --format-version 1` |
| 잠금인가 교착인가? | `RUST_BACKTRACE=1`과 멈춤 재현, 스크래치 사본에서 `Mutex::try_lock`으로 정지를 오류로 바꿔 본다 |
| 비동기 런타임이 future를 버리는가? | await하지 않는 `tokio::spawn` 핸들과 `select!`에서 작업을 취소하는 분기를 본다 |

`RUST_LOG`는 그 크레이트가 로깅 파사드를 쓸 때만 도움이 된다. 빈 로그를 믿기 전에 subscriber가 초기화됐는지 확인한다.

## 5. Go

| 질문 | Probe |
|---|---|
| 어떤 바이너리와 모듈 버전이 도는가? | `go version -m <binary>`, `go list -m all` |
| panic이 어디서 시작됐는가? | panic이 고루틴 덤프를 출력한다. 첫 `created by` 줄과 잠금을 쥔 고루틴을 읽는다 |
| 오류가 무시되는가? | `go vet ./...`와 `_ = `, `if err != nil { }`, re-panic 없는 `recover()` 검색 |
| 고루틴이 새는가? | `net/http/pprof` 엔드포인트에 `go tool pprof`, 또는 스크래치 테스트의 `runtime.NumGoroutine()` |
| 채널이 조용히 막히는가? | `-race`와 경계 있는 타임아웃 아래 재현한다. 가득 찬 송신이나 읽히지 않는 수신은 멈춘 고루틴으로 보인다 |
| 경쟁이 실제인가? | `go test -race -count=10 ./...` — 테스트를 바꾸지 않고 경쟁 가능성만 높인다 |
| 실행 중인 빌드가 그 빌드인가? | `go build -o /tmp/<name> .`로 그 경로를 직접 실행. `go run` 캐시나 낡은 설치는 흔한 불일치다 |
| 어떤 context 데드라인이 걸렸는가? | 호출 지점에서 `ctx.Err()`을 기록한다. `context.Canceled`와 `context.DeadlineExceeded`는 원인이 다르다 |

## 6. 네이티브 바이너리

| 질문 | Probe |
|---|---|
| 이 바이너리는 무엇인가? | `file <path>`, `uname -m`, 로드 라이브러리는 macOS `otool -L`, Linux `ldd` |
| 어떤 빌드가 배포됐는가? | build-id나 해시 비교: `shasum -a 256 <binary>`를 아티팩트 저장소 값과 비교 |
| 어떻게 끝났는가? | `echo "exit=$?"`. `128 + signal`은 정상 종료가 아니라 신호다. Linux에서는 OOM kill을 `dmesg`로 확인 |
| 시스템 호출이 거부됐는가? | Linux `strace -f -e trace=%file,%network -o /tmp/trace <cmd>`, macOS는 허용될 때 `dtruss -f <cmd>` |
| 반환 코드가 무시되는가? | 버려진 `int` 반환 호출 지점, `-Wunused-result`, `warn_unused_result` 확인 |
| 라이브러리 버전 불일치인가? | 빌드가 기대한 버전과 `otool -L`/`ldd` 비교. macOS `DYLD_PRINT_LIBRARIES=1`, Linux `LD_DEBUG=libs` |
| 부하에서만 실패하는가? | 경계 있는 동시 실행으로 재현 창 동안 `ulimit -n`, 스레드 수, RSS를 지켜본다 |

코어 덤프나 신호 번호는 관찰이지 원인이 아니다. 다시 가설 묶음에 넣는다.

## 7. 조용한 실패 표

증상은 효과 없는 성공 응답이다. 검사 대상 코드의 모양과 맞는 행을 모두 확인한다.

| 패턴 | 읽을 것 | 성공처럼 보이는 이유 |
|---|---|---|
| 빈 본문이나 기본 본문의 HTTP 2xx | 경계에서 본문, 길이, content type | 클라이언트가 가장 먼저 보는 것이 상태 줄이다 |
| 실패한 하위 필드를 가진 `ok: true` | 최상위 플래그가 아니라 전체 payload | 집계 상태는 항목별 오류를 숨긴다 |
| await하지 않은 promise | 호출 지점, 호출자가 promise를 반환하는지 | 작업이 예약될 뿐이라 호출에서 아무것도 던지지 않는다 |
| `try { } catch { }` 또는 `except: pass` | catch 블록과 그것이 삼키는 것 | 실패가 호출자에게 도달하지 않는다 |
| `let _ = result` / `.ok()` / `.unwrap_or_default()` | 오류 경로와 대신 넣는 기본값 | 값이 반환되므로 코드가 진행한다 |
| 아무 데도 기록하지 않는 `recover()`나 잡힌 panic | 복구 핸들러와 그 sink | 프로세스가 계속 돈다 |
| 오류를 전파하지 않는 `if err != nil { return }` | 호출자의 오류 처리 | 호출자는 오류가 아니라 제로 값을 본다 |
| 쓰기가 적용됐다는데 읽으면 예전 값 | 같은 세션에서 쓰기 뒤의 읽기 | 쓰기 호출이 오류 없이 반환됐다 |
| 부수 효과 전에 완료로 표시된 작업 | 완료 신호와 부수 효과 확인 | 상태 기계가 앞으로 갔다 |
| 낡은 항목을 돌려주는 캐시 히트 | 캐시 키, TTL, 무효화 경로 | 값이 빠르게 돌아왔다 |
| stderr에 트레이스가 있는데 종료 코드 0 | 두 스트림과 종료 코드를 함께 | harness가 종료 코드만 읽는 경우가 많다 |
| 단언이 실행되지 않아 통과한 테스트 | 단언 횟수, 일부러 실패시켜 실패할 수 있는지 확인 | 초록 실행이 증명처럼 보인다 |
| 실패가 사라질 때까지 올린 타임아웃 | 설정된 타임아웃과 실제 소요 시간 | 실행이 더 느리게 통과한다 |
| 첫 시도의 오류를 숨기는 재시도 | 시도 횟수와 첫 오류 | 최종 결과가 초록이다 |

보고된 증상 밖에서 찾은 조용한 실패는 이번 실행의 수정이 아니라 일지의 후속 항목이다. `path:line`, 패턴, 한 줄 수정 초안, 방치했을 때의 위험을 기록한다.

## Sources

> Checked 2026-11-09.

| Claim | Source |
|---|---|
| 조용한 실패 목록(빈 본문 2xx, await 없는 promise, 삼킨 예외, 잡힌 panic, 무시한 반환값, 쓰기 뒤 낡은 읽기, 이른 완료, 낡은 캐시, stderr가 있는 종료 코드 0) | `dbc-hbin/omp-ulw@74df40f debugging/references/methodology/08-qa.md` (mechanism reference, re-authored) |
| Node·Python probe 형태와 `--enable-source-maps`, `-X dev` 신호 | `dbc-hbin/omp-ulw@74df40f debugging/references/runtimes/node.md`, `debugging/references/runtimes/python.md` (mechanism reference, re-authored) |
| 관찰 도구로서의 `RUST_BACKTRACE`, `go test -race`, `go vet`, `strace`, `otool -L`, `ldd` | 설치된 런타임 문서와 명령 도움말, 2026-11-09 확인 |

### Evidence grade

표 구조와 probe 선택은 `LOCAL`, 명령은 런타임 자체의 문서화된 인터페이스라 `PRIMARY`다. 버전마다 바뀌는 플래그는 목적으로 서술했으므로, 읽는 사람이 설치된 버전에서 `--help`로 정확한 표기를 확인한다. 조용한 실패 행은 라이선스가 없는 저장소에서 자기 말로 다시 쓴 메커니즘 인용이며 텍스트나 코드를 복사하지 않았다.
