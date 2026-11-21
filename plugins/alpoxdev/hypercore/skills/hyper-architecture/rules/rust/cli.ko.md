# CLI

> clap이 파싱과 종료 코드를 소유하게 하고, 동사마다 서브커맨드 모듈 하나를 두며, 기계 출력을 명시적 계약으로 만들고, `dist`로 릴리스 바이너리를 냅니다.

이 파일의 규칙은 `references/official/rust/rust-crates-2026-11-07.md`에서 연 페이지가 그대로 진술한 경우 `official`, 이 패키지가 기본값으로 고른 경우 `hypercore-default`로 표시합니다. 오류와 종료 코드 정책은 `rules/rust/errors-and-logging.md`가 소유하고, 이 파일은 인자 표면, 출력 계약, 배포를 다룹니다.

## 1. clap 4.6

`official` — 메이저는 4입니다. crate에는 기능이 20개, 기본값이 6개(`color`, `error-context`, `help`, `std`, `suggestions`, `usage`)이므로 `derive`와 `env`는 선택 사항이고 선언해야 합니다(https://docs.rs/crate/clap/latest/features). `env` 기능 없이 `#[arg(env = ...)]`를 쓰는 crate는 컴파일되지 않습니다.

```toml
[dependencies]
clap = { version = "4.6", features = ["derive"] }        # add "env" only when an env fallback exists
clap_complete = "4.6"
```

`official` — derive 표면은 `Parser`(인자 구조체 또는 서브커맨드 enum), `Args`(재사용 그룹, 다른 구조체에 flatten 가능), `Subcommand`, `ValueEnum`입니다(https://docs.rs/clap/latest/clap/_derive/index.html). 리뷰에서 중요한 기본값 세 가지입니다.

- `rename_all`은 `kebab-case`가 기본이므로 `dry_run` 필드가 자동으로 `--dry-run`이 됩니다.
- `rename_all_env`는 `SCREAMING_SNAKE_CASE`가 기본이므로 `dry_run`이 `DRY_RUN`을 읽습니다.
- 표현식 없는 `#[command(version)]`은 crate의 `version`을 취합니다.

`official` — `ValueEnum`은 "데이터를 가진 변형이 있는 enum에서는 그 변형을 건너뛰지 않는 한 동작하지 않습니다"(https://docs.rs/clap/latest/clap/_derive/index.html). 데이터를 가진 변형이 있는 enum은 그 변형을 skip하거나 그 입력을 다른 플래그로 옮겨야 합니다.

`official` — 문서 주석이 `about`과 `long_about`이 되므로, 짧은 형식만 보여야 할 때의 문서화된 요령은 `#[command(version, about, long_about = None)]`입니다(https://docs.rs/clap/latest/clap/_derive/index.html).

## 2. 한 번만, `main`에서 파싱

`official` — `try_parse()`를 `unwrap()`하지 않습니다. `Parser::parse()`나 `err.exit()`가 clap의 계약을 그대로 적용하게 합니다. 도움말과 버전은 stdout으로 상태 0, 파싱 오류는 stderr로 상태 2입니다(https://docs.rs/clap/latest/clap/error/struct.Error.html). 손으로 쓴 `.expect("bad args")`는 사용 안내를 panic과 101로 바꿉니다.

`hypercore-default` — 파싱 지점은 하나이고, subscriber나 I/O 작업 전에 `main`에서 합니다. 파싱된 `Cli`는 값으로 아래에 전달됩니다. `run` 아래 어디에서도 `std::env::args`를 읽지 않습니다.

`hypercore-default` — `try_parse()`가 정당한 곳은 한 곳뿐입니다. 오류가 단언 대상인 테스트입니다. 그때도 포맷된 문자열이 아니라 `ErrorKind`를 단언합니다.

## 3. 서브커맨드 구조

`hypercore-default` — enum 하나가 모든 동사를 명명하고, 동사마다 모듈 하나가 실행합니다.

```rust
#[derive(clap::Parser)]
#[command(name = "mytool", version, about, long_about = None)]
pub struct Cli {
    #[command(subcommand)]
    pub command: Command,
    #[arg(long, global = true)]
    pub json: bool,
    #[arg(long, short, global = true, action = clap::ArgAction::Count)]
    pub verbose: u8,
}

#[derive(clap::Subcommand)]
pub enum Command {
    /// Validate the manifest without writing.
    Check(CheckArgs),
    /// Build every target.
    Build(BuildArgs),
}

#[derive(clap::Args)]
pub struct CheckArgs {
    /// Path to the manifest.
    #[arg(default_value = "Cargo.toml")]
    pub manifest: std::path::PathBuf,
}
```

- 교차 관심 플래그(`--json`, `--verbose`, `--quiet`)에는 `global = true`를 붙여 서브커맨드 앞뒤 어디서든 동작하게 합니다.
- `-vv`에는 `ArgAction::Count`, 플래그에는 `ArgAction::SetTrue`, 값에는 `ArgAction::Set`을 씁니다. 필드 타입에 따라 기본이 달라지므로 명시합니다.
- 모든 인자와 서브커맨드에 문서 주석을 답니다. 그것이 도움말입니다.
- 기본값은 도움말에 보여야 합니다. 숨은 기본값은 지원 요청입니다.
- 환경 폴백은 `#[arg(env = "MYTOOL_LEVEL")]`을 쓰고, 실제 배포가 필요로 할 때만 씁니다. CLI 자체 플래그가 항상 이깁니다.

`hypercore-default` — 재사용 그룹은 필드 목록을 복제하지 않고 `#[command(flatten)]`을 씁니다. 여러 동사가 공유하는 flatten 그룹은 trait가 아니라 `Args` 구조체입니다.

## 4. 출력 계약

`official` — 기계 소비자에 대해 CLI 책은 메시지당 JSON 문서 하나, 줄 단위, 모든 레코드가 `type` 필드를 갖는 형식을 권고하고, 그 예시는 레코드가 `begin`/`match`/`end`/`summary`인 ripgrep의 `--json`입니다(https://rust-cli.github.io/book/in-depth/machine-communication.html).

`hypercore-default` — 이 패키지가 표준화하는 계약입니다.

- `--json`은 stdout에 NDJSON을 쓰고, 줄마다 레코드 하나, 각 레코드에 `type` 판별자를 둡니다. 여러 줄로 예쁘게 출력하지 않습니다. 줄 단위 소비자가 개행으로 나눌 수 있어야 합니다.
- 모든 레코드는 손으로 만든 문자열이 아니라 `output/`의 `serde::Serialize` 값입니다. 필드 이름은 메이저 버전 안에서 안정적입니다.
- 레코드 종류는 페이로드만이 아니라 생애 주기를 덮습니다. 최소한 개수를 담은 `summary` 레코드와 기계 코드 및 짧은 메시지를 담은 `error` 레코드입니다. `summary`만 읽는 소비자가 페이로드 레코드 없이도 동작해야 합니다.
- 사람용 출력은 stdout이 터미널이고 `--json`이 없을 때의 기본입니다. 파이프된 stdout에 `--json`이 없으면 사람용 출력을 유지합니다. 플래그가 결정하고 파이프는 결정하지 않으므로 스크립트 동작이 명시적입니다.
- `std::io::IsTerminal`은 진행과 색을 결정하고 레코드 모양은 결정하지 않습니다(https://rust-cli.github.io/book/in-depth/machine-communication.html).
- 종료는 `--json`에 따라 바뀌지 않습니다. 같은 실패가 같은 종료 코드를 내고, 문장 대신 `error` 레코드를 냅니다.

`official` — `serde_json`은 `to_writer` 호출마다 문서 하나를 씁니다. 레코드마다 `\n`을 쓰고 실행 끝에 flush하는 것이 관찰 가능한 모양입니다. 프로세스 종료에서만 flush하는 버퍼링 writer는 프로세스가 죽으면 레코드를 잃습니다.

## 5. 완성 스크립트

`official` — `clap_complete` 4.6.11은 `generate`(런타임)와 `generate_to`(컴파일 타임), `Shell`, `aot` 모듈을 제공하고, `generator`와 `shells` 모듈은 `aot` 대신 폐기로 표시됩니다(https://docs.rs/clap_complete/latest/clap_complete/). `CompleteEnv`는 `COMPLETE=$SHELL <bin>`을 통한 동적 완성을 지원합니다.

`hypercore-default` — 빌드 시 파일을 써도 되는지에 따라 두 모양 중 하나를 고릅니다.

| Shape | When | Cost |
|---|---|---|
| `OUT_DIR`으로 `generate_to`를 빌드 타임에 실행하고 릴리스 아카이브에 포함 | 릴리스 과정이 이미 아카이브를 냄 | 완성 스크립트가 빌드 시점만큼만 최신 |
| `generate`를 쓰는 숨은 `completions` 서브커맨드 | 사용자가 패키지 관리자나 `cargo install`로 설치 | 파서에 숨은 동사가 생김 |

어느 쪽이든 완성 스크립트를 손으로 쓰지 않습니다. 생성된 스크립트는 파서를 따르고, 손으로 쓴 것은 첫 플래그 이름 변경에서 어긋납니다.

## 6. `dist`로 배포

`official` — 도구는 `dist`이고 이전 이름은 `cargo-dist`입니다. README가 그 이름 변경으로 시작합니다(https://raw.githubusercontent.com/axodotdev/cargo-dist/main/README.md). crates.io 패키지는 여전히 `cargo-dist`(0.34.0)이고 "패키지 이름은 현재 모두 원래 이름을 쓰지만" "`dist ...`로 호출할 수 있어야 합니다"(https://axodotdev.github.io/cargo-dist/book/install.html).

`official` — 워크플로는 이렇습니다. `dist init`(대화형, 재실행 가능, 기본값은 `--yes`)이 dist 설정을 쓰고, `Cargo.toml`에 배포용 빌드 프로필을 추가하며, `.github/workflows/release.yml`을 생성합니다. 릴리스는 `v0.1.0` 같은 태그를 푸시해 시작하고, `dist build`는 현재 플랫폼을 빌드하며, `dist plan`은 CI가 빌드할 것을 출력합니다(https://axodotdev.github.io/cargo-dist/book/quickstart/rust.html).

`official` — 생성되는 프로필은 `[profile.dist]`이고 `inherits = "release"`, `lto = "thin"`입니다. 공격적인 릴리스 설정이 로컬 빌드를 느리게 하지 않도록 분리해 둡니다(https://axodotdev.github.io/cargo-dist/book/reference/concepts.html). `[profile.*]` 섹션은 루트 manifest에서만 읽습니다.

`hypercore-default` — 규칙:

- 저장소마다 `dist init --yes`를 한 번 실행하고, 타깃이 바뀌면 생성 워크플로를 손으로 고치지 말고 다시 실행합니다.
- 태그 전에 `dist plan`으로 타깃 행렬을 릴리스 없이 검토합니다.
- `[profile.dist]`는 `release`를 상속한 채로 둡니다. 미미한 크기 이득을 위해 로컬 빌드를 느리게 하는 것은 팀이 합의한 거래가 아닙니다.
- 인스톨러는 의도적으로 고르고 기록합니다. 인스톨러 목록은 init에서 조사되며 기본값은 결정이 아닙니다.
- 릴리스는 태그 기반으로만 합니다. 로컬 `dist build`는 검증용이고 게시용이 아닙니다.
- `cargo-binstall` 지원은 릴리스 산출물에 달려 있습니다. 호환 아카이브를 내지 않으면 `cargo binstall`을 약속하지 않습니다.

## 7. 설정 파일

`official` — 공식 CLI 책의 설정 장은 아직 초안입니다. "TODO / Evaluate crates that exist / Cli-args + multiple configs + env variables"입니다(https://rust-cli.github.io/book/print.html). 인용할 공식 권고가 없습니다.

`hypercore-default` — 설정 파일이 있으면 `--help`에도 진술하는 우선순위입니다. 명령줄 플래그, 그다음 환경 변수, 그다음 설정 파일, 그다음 내장 기본값입니다. `figment`(0.10.19)와 `config`(0.15.27)가 존재하며 이 스냅숏에서는 버전만 확인했습니다. 어느 것도 이 패키지의 공식 기본값이 아니고, 채택은 기록된 프로젝트 결정입니다. 설정 한 계층만 필요한 crate는 `serde`로 파일 하나를 파싱하고 둘 다 건너뛸 수 있습니다.

## Checklist

- [ ] `derive`를 명시적으로 선언하고, `env`는 환경 폴백이 있을 때만 쓴다.
- [ ] 파싱은 `main`에서 한 번이며 `try_parse().unwrap()`이 없다.
- [ ] clap의 종료 계약을 건드리지 않는다. 도움말·버전은 stdout+0, 파싱 오류는 stderr+2다.
- [ ] `Subcommand` enum 하나가 모든 동사를 명명하고 동사마다 명령 모듈이 하나다.
- [ ] 교차 관심 플래그가 `global = true`이고 명시적 `ArgAction`을 쓴다.
- [ ] 모든 인자와 서브커맨드의 도움말이 문서 주석이다.
- [ ] `--json`이 `type` 필드를 가진 NDJSON 레코드를 줄마다 하나씩 내고, summary와 error 레코드를 포함한다.
- [ ] 기계 출력이 포맷 문자열이 아니라 직렬화 가능한 구조체에서 나온다.
- [ ] `--json`에 따라 종료 코드가 바뀌지 않는다.
- [ ] 진행과 색은 `IsTerminal`을 따르고 레코드 모양은 따르지 않는다.
- [ ] 완성 스크립트를 손으로 쓰지 않고 `clap_complete`로 생성한다.
- [ ] 릴리스 바이너리가 `dist`에서 나오고, `[profile.dist]`가 루트 manifest에 있으며, 워크플로가 태그 기반이다.
- [ ] 설정 파일이 있으면 우선순위를 문서화했다.

## Sources

> Checked 2026-11-07. 사실은 `references/official/rust/rust-crates-2026-11-07.md`에 기록된 페이지에서 왔습니다.

| Claim | Source |
|---|---|
| clap 4.6.7의 기능, 기본값, 20/6 기능 수 | https://docs.rs/crate/clap/latest/features |
| derive 표면, `ValueEnum`의 unit 변형 제한, `rename_all`·`rename_all_env` 기본값, `long_about = None` | https://docs.rs/clap/latest/clap/_derive/index.html |
| `Error::exit`의 stdout+0 / stderr+2 계약 | https://docs.rs/clap/latest/clap/error/struct.Error.html |
| `clap_complete`의 `generate`, `generate_to`, `aot`, `CompleteEnv` | https://docs.rs/clap_complete/latest/clap_complete/ |
| `type` 판별자를 가진 NDJSON과 ripgrep의 레코드 종류 | https://rust-cli.github.io/book/in-depth/machine-communication.html |
| 사람과 파이프 출력을 가르는 `IsTerminal` | https://rust-cli.github.io/book/in-depth/machine-communication.html |
| `dist` 이름 변경, 패키지 이름, 설치 바이너리 이름 | https://raw.githubusercontent.com/axodotdev/cargo-dist/main/README.md, https://axodotdev.github.io/cargo-dist/book/install.html |
| `dist init`, 태그 기반 릴리스, `dist plan`, `dist build` | https://axodotdev.github.io/cargo-dist/book/quickstart/rust.html |
| `[profile.dist]`가 `release`를 상속 | https://axodotdev.github.io/cargo-dist/book/reference/concepts.html |
| 설정 장이 아직 초안 | https://rust-cli.github.io/book/print.html |
| `figment`과 `config` 버전만(권고 없음) | https://crates.io/api/v1/crates/figment, https://crates.io/api/v1/crates/config |
| 레코드 타입 계약, 플래그 액션, 배포 규칙 | 이 패키지의 규약이며 공식 Rust 요구가 아님 |
