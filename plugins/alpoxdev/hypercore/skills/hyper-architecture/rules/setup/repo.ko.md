# Repository Setup Baseline

> root `.editorconfig`와 `.gitattributes` 하나씩, hook runner 하나(lefthook), editor 권장 설정, 그리고 각 언어 setup file이 채우는 고정된 CI 검사 순서입니다.

규칙은 `## Sources`에 열거한 페이지가 그대로 진술할 때 `official`, 이 패키지가 기본값을 골랐을 때 `hypercore-default`입니다. 이 file은 package마다가 아니라 repository당 한 번 적용합니다. Template은 `assets/templates/setup/repo/`에 있습니다.

## 1. Detect first

`hypercore-default` — 쓰기 전에 읽습니다. 이미 hook runner를 돌리는 repository는 그 선택이 기록돼 있으면 유지하고, 아니면 lefthook으로 옮깁니다(§3).

| 찾을 것 | 의미 |
|---|---|
| `.editorconfig` | 적용 중인 editor 규칙. `root = true`와 언어별 indent 확인 |
| `.gitattributes` | 적용 중인 줄바꿈과 binary 규칙 |
| `lefthook.yml`, `lefthook.yaml`, `.lefthook.yml` | lefthook 이미 설치됨 |
| `.husky/`, `package.json` → `husky`, `lint-staged` | husky + lint-staged 사용 중 |
| `.vscode/extensions.json`, `.vscode/settings.json` | editor 권장 설정이 이미 있음 |
| `.github/workflows/*.yml`, `.gitlab-ci.yml`, `Makefile`, `justfile` | CI 순서가 실제로 사는 곳 |

`.git/hooks`는 생성 상태이고 편집 대상이 아닙니다.

## 2. Editor and line-ending hygiene

`official` — repository root에 `root = true`를 둔 `.editorconfig` 하나를 두고, 표준 property는 `end_of_line`, `insert_final_newline`, `trim_trailing_whitespace`, `indent_style`, `indent_size`, `charset`입니다(https://editorconfig.org/).

| 복사 | 대상 | 목적 |
|---|---|---|
| `assets/templates/setup/repo/editorconfig` | `.editorconfig` | root editor 규칙 |
| `assets/templates/setup/repo/gitattributes` | `.gitattributes` | 줄바꿈, binary 표시, 생성 lockfile |

`hypercore-default` — indent는 web 언어에 2, Rust에 4이며 Prettier 기본값과 rustfmt `tab_spaces`에 맞습니다. Prettier는 Prettier config가 덮지 않는 한 `.editorconfig`의 `indent_size`, `end_of_line`, `max_line_length`를 읽으므로 두 file이 일치해야 합니다(https://prettier.io/docs/options).

`hypercore-default` — `*.md`는 `trim_trailing_whitespace = false`입니다. 끝의 공백 두 칸은 hard line break이고, 지우면 rendering 결과가 달라집니다.

`official` — `* text=auto`가 있는 `.gitattributes`는 commit 시 줄바꿈을 정규화하고, 확장자별 `eol` 규칙이 이를 덮습니다(https://git-scm.com/docs/gitattributes).

`hypercore-default` — working tree는 `* text=auto eol=lf`로 전부 LF를 유지하고, `*.sh text eol=lf`를 명시하며, Windows 전용 launcher(`*.bat`, `*.cmd`, `*.ps1`)는 `eol=crlf`로 고정합니다. binary asset은 `binary`로 표시해 diff가 merge를 시도하지 않게 하고, lockfile은 `linguist-generated=true`로 표시해 review tool이 접게 합니다.

`hypercore-default` — formatter와 다투는 `*.md text=auto` 같은 예외를 더하지 않습니다. Markdown file이 CRLF를 유지해야 하면 attribute 규칙을 넓히지 말고 그 file을 고칩니다.

## 3. Git hooks

`hypercore-default` — 기본 hook runner는 lefthook입니다. 여러 언어가 섞인 repository에서 binary 하나로 끝나고, job을 병렬로 돌리며, `stage_fixed`로 staged file을 다시 씁니다. Rust crate와 TypeScript package가 Node 전용 tool 두 개 대신 config 하나를 공유합니다(https://raw.githubusercontent.com/evilmartians/lefthook/master/docs/configuration.md).

| 복사 | 대상 | 목적 |
|---|---|---|
| `assets/templates/setup/repo/lefthook.yml` | `lefthook.yml` | pre-commit format/lint, pre-push typecheck/test |

`official` — `stage_fixed: true`는 `pre-commit`에서만 동작합니다. 명령이 다시 쓴 file을 다시 stage해 commit에 format된 version이 들어가게 합니다(https://raw.githubusercontent.com/evilmartians/lefthook/master/docs/configuration/stage_fixed.md).

`official` — legacy `commands:` 대신 `jobs:`를 씁니다. `jobs`는 lefthook 1.10.0에 추가됐고, `glob`은 1.10.10부터 list를 받으며, `root`는 `pre-commit`과 `pre-push`에서 file 경로를 걸러냅니다(https://raw.githubusercontent.com/evilmartians/lefthook/master/docs/configuration/jobs.md, https://raw.githubusercontent.com/evilmartians/lefthook/master/docs/configuration/glob.md).

`hypercore-default` — `lefthook`을 dev dependency(npm `latest` 2.2.2)로 넣고 clone마다 `lefthook install`을 한 번 실행합니다. 생성된 `.git/hooks` script는 commit하지 않습니다(https://registry.npmjs.org/lefthook).

`hypercore-default` — husky + lint-staged는 대안이지 기본이 아닙니다. 둘 다 Node 전용이라 Rust 단독이나 혼합 repository는 hook logic을 중복하거나 format하려고 Node를 설치해야 합니다. 이미 husky를 돌리는 repository는 `AGENTS.md`에 그 결정이 기록돼 있으면 유지합니다.

`hypercore-default` — hook 범위는 다음과 같습니다.

| 단계 | job | 이유 |
|---|---|---|
| `pre-commit` | staged web file에 `prettier --write`, staged JS/TS에 `oxlint`, staged `*.rs`에 `cargo fmt --all`과 `cargo clippy` | 빠르고 file 범위이며 고칠 수 있는 것은 고침 |
| `pre-push` | `typecheck`와 `test` | formatting이 못 잡는 것을 잡음 |

`hypercore-default` — hook이 commit마다 전체 test suite를 돌리지 않습니다. 그 일은 CI나 `pre-push` 소관입니다. 몇 초를 넘기는 hook은 습관적으로 건너뛰게 되고, 건너뛴 hook은 아무것도 검사하지 않습니다.

## 4. Editors

`official` — oxlint editor extension은 `oxc.oxc-vscode`입니다. `.vscode/extensions.json`에 권장으로 넣고, 저장 시 fix는 `"editor.codeActionsOnSave": {"source.fixAll.oxc": "always"}`로, type-aware mode는 `"oxc.typeAware": true`로 켭니다(https://oxc.rs/docs/guide/usage/linter/editors.html).

`hypercore-default` — `.vscode/extensions.json`에는 lint fix용 `oxc.oxc-vscode`와 format용 Prettier editor extension을 권장으로 넣습니다. Prettier extension의 marketplace id는 이 snapshot의 검증된 증거에 없으므로 기억에서 복사하지 말고 extension 자체 listing에서 읽습니다.

`hypercore-default` — repository config와 맞아야 하는 editor 설정입니다. `editor.defaultFormatter`에는 Prettier extension의 공개 id를 그 listing에서 읽어 넣습니다.

```json
{
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": { "source.fixAll.oxc": "always" },
  "oxc.typeAware": true
}
```

`hypercore-default` — project가 ESLint를 유지하면(`rules/setup/typescript.md`의 Expo 예외) `editor.codeActionsOnSave`에 `"source.fixAll.eslint": "explicit"`을 더합니다. 빠른 단계가 먼저 돌도록 `oxc`는 `always`로 둡니다.

`hypercore-default` — Rust editor 설정은 `rust-analyzer`와 저장 시 `rustfmt`를 씁니다. clippy 진단은 CI가 쓰는 같은 `cargo clippy` 실행에서 오므로 editor 전용 설정이 정책이 되지 않습니다.

## 5. CI check order

`hypercore-default` — 각 단계가 다음보다 싸므로 순서를 고정하고, 실패하면 pipeline을 일찍 멈춥니다.

```text
format check → lint → typecheck → test → build
```

`hypercore-default` — 언어별로 단계는 다음 명령에 대응합니다.

| 단계 | TypeScript | Rust |
|---|---|---|
| format check | `prettier --check .`(`npm run format:check`) | `cargo fmt --all --check` |
| lint | `oxlint`(`npm run lint`, Expo는 `oxlint && eslint`) | `CARGO_BUILD_WARNINGS=deny cargo clippy --all-targets --all-features` |
| typecheck | `tsc --noEmit`(`npm run typecheck`, Astro는 `astro check`) | `cargo check`/`cargo clippy`에 포함. job에 clippy가 없을 때만 `cargo check --all-targets` 추가 |
| test | `npm test` | `cargo test --all-targets` |
| build | stack의 build 명령 | `cargo build --release` |

`hypercore-default` — 두 언어가 있는 monorepo는 합친 job 하나가 아니라 package마다 전체 순서를 돕니다. Rust 실패가 TypeScript formatting 실패를 가리면 안 됩니다. dependency 설치와 `target/`은 cache하고 lint 결과는 cache하지 않습니다.

`official` — `prettier --check`는 format이 필요한 file이 있으면 non-zero로 끝나므로 첫 gate로 쓸 수 있습니다(https://prettier.io/docs/cli).

`hypercore-default` — build 단계는 마지막에, green pipeline에서만 돕니다. build가 `typecheck`를 대신하지 않고 `astro check`는 typecheck 단계이지 build 단계가 아닙니다.

`hypercore-default` — `oxlint --type-check`를 돌리는 CI 단계는 이미 `tsc --noEmit`을 덮습니다. 둘을 함께 돌리면 같은 finding에 두 배로 기다립니다. 하나를 고르고 workflow file에 어느 쪽인지 적습니다.

## Checklist

- [ ] 기존 `.editorconfig`, `.gitattributes`, hook runner, editor 설정을 먼저 읽었습니다.
- [ ] `root = true`인 root `.editorconfig`가 하나 있고 `*.md`는 끝 공백을 유지합니다.
- [ ] `.gitattributes`에 `* text=auto`, script의 명시적 LF, binary 표시, 생성 lockfile 표시가 있습니다.
- [ ] 기록된 결정으로 husky를 유지하는 경우가 아니면 hook runner는 lefthook입니다.
- [ ] hook config가 `commands:`가 아니라 `jobs:`를 쓰고 `stage_fixed`가 `pre-commit`에만 있습니다.
- [ ] `lefthook install`을 clone마다 실행하고 `.git/hooks` file을 commit하지 않습니다.
- [ ] `.vscode/extensions.json`에 `oxc.oxc-vscode`와 Prettier extension을 권장으로 넣었습니다.
- [ ] CI가 package마다 format check → lint → typecheck → test → build를 실행합니다.
- [ ] lint 단계가 warning에서 실패합니다(clippy는 `CARGO_BUILD_WARNINGS=deny`).
- [ ] 같은 job에서 `oxlint --type-check`와 `tsc --noEmit`을 함께 돌리지 않습니다.

## Sources

> 확인 2026-11-07. 아래 인용 페이지와 `references/official/tooling/tooling-2026-11-07.md`에 기록된 페이지에서 사실을 가져왔습니다. hook runner 선택, editor 설정, CI 순서는 이 패키지의 convention입니다.

| Claim | Source |
|---|---|
| EditorConfig property와 `root = true` | https://editorconfig.org/ |
| `* text=auto`와 `eol` attribute 동작 | https://git-scm.com/docs/gitattributes |
| lefthook config 구성, 1.10.0의 `jobs` 추가 | https://raw.githubusercontent.com/evilmartians/lefthook/master/docs/configuration.md, https://raw.githubusercontent.com/evilmartians/lefthook/master/docs/configuration/jobs.md |
| `stage_fixed`는 pre-commit 전용 | https://raw.githubusercontent.com/evilmartians/lefthook/master/docs/configuration/stage_fixed.md |
| `glob`이 1.10.10부터 list를 받음 | https://raw.githubusercontent.com/evilmartians/lefthook/master/docs/configuration/glob.md |
| lefthook npm latest 2.2.2 | https://registry.npmjs.org/lefthook |
| `oxc.oxc-vscode` id, `source.fixAll.oxc`, `oxc.typeAware` | https://oxc.rs/docs/guide/usage/linter/editors.html |
| Prettier가 `.editorconfig` 값을 읽음, `--check` 종료 동작 | https://prettier.io/docs/options, https://prettier.io/docs/cli |
| lefthook 우선, hook 범위, editor 권장 집합, CI 검사 순서 | 이 패키지의 convention |
