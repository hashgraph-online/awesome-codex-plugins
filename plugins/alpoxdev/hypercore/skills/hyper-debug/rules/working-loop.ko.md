# Working Loop

첫 재현 시도 전에 이 파일을 읽는다. 준비, 재현, 일지를 맡는다.

## 1. Fix The Four Facts Before Anything Else

probe를 돌리기 전에 네 가지를 일지에 적는다. 여기서 값이 틀리면 이후 라운드가 모두 낭비된다.

| Fact | 확인 방법 | 나머지를 결정하는 이유 |
|---|---|---|
| 런처 | 사용자나 CI가 실제로 실행하는 명령. `package.json` scripts, `Makefile`, `justfile`, `pyproject.toml`, `Cargo.toml`, `go.mod`, workflow 파일, 보고 원문에서 찾는다 | 프로그램을 다른 방식으로 띄우는 재현은 통과할 수 있지만 실제 경로는 실패한다 |
| 런타임 정체 | 버전과 `PATH`에서 실제로 잡히는 바이너리(`node -v`, `python3 -V`, `rustc -V`, `go version`, `file <binary>`) | 한 버전의 실패는 다른 버전의 실패가 아니고, 낡은 전역 설치본은 흔한 오답 유도다 |
| 입력 | 보고를 만든 정확한 파일, 요청 본문, 행, 픽스처, 환경 변수, 시드 | 입력이 근사하면 증상도 근사해진다 |
| 기대 동작 | 명세, 테스트, 문서, 사용자 말에서 가져온 정상 동작 | 이것이 없으면 "잘못된 출력"이 정의되지 않고 수정도 검증할 수 없다 |

네 가지 중 보고에 없는 것이 있으면 그 하나만 묻고 실행을 `awaiting_input`으로 표시한다. 지어내지 않는다.

## 2. Reproduce First

- 무엇이든 바꾸기 전에 보고된 경로를 그대로 실행한다. 명령, 작업 디렉터리, 출력을 그대로 기록한다.
- 재현되면 줄인다. 입력, 플래그, 계층, 의존성을 하나씩 제거하고 매번 다시 실행해 실패가 사라질 때까지 줄이며, 마지막으로 여전히 실패하는 준비를 남긴다. 그것이 재현이다.
- 재현되지 않으면 결론을 내리기 전에 네 가지 사실을 보고와 대조한다. 다른 버전, 다른 작업 디렉터리, 데워진 캐시, 다른 환경 변수는 다른 프로그램이다.
- 보고된 실패를 재현한다. 옆에 있는 다른 실패를 재현해도 이 보고에 대한 증명이 되지 않는다.

## 3. Smallest Safe Setup

- 일회용 대상을 선호한다. 임시 디렉터리, 로컬 파일 사본, 스크래치 데이터베이스, 임시 포트의 로컬 서버다. 재현을 공유·스테이징·production 시스템으로 겨냥하지 않는다.
- 증상을 보이는 최소 데이터만 복사한다. 일지에 붙이는 값에서 비밀을 지우고, 값 자체가 아니라 값의 모양을 적는다.
- 준비가 만드는 자원(파일, 디렉터리, 프로세스, 포트, 컨테이너, 환경 덮어쓰기)은 만들기 전에 일지의 Resources 표에 적는다. 그래야 정리가 기억력 시험이 아니라 체크리스트가 된다.
- 이번 실행이 띄운 프로세스는 실행이 끝나기 전에 멈춘다. 사용자의 프로세스는 그대로 두고, 그것이 재현을 막을 때는 그 사실을 적는다.
- credential, 유료 서비스, 장치, 세션에 없는 네트워크가 있어야 재현되는 실패는 짐작이 아니라 구체적인 질문 하나를 붙인 `awaiting_input`이다.

## 4. Read Before Instrumenting

- probe를 하나라도 더하기 전에 실패하는 코드, 그 호출자, 이미 그 경로를 덮는 테스트를 읽는다.
- 이미 경로를 덮는 테스트나 픽스처가 있으면 재현으로 재사용한다. 그것을 확장하는 편이 더 싸고 저장소에 진짜 회귀 case가 남는다.
- 런타임이 이미 주는 관찰을 먼저 쓴다. 종료 코드, stderr, 스택 트레이스, 로그 줄, 요청과 응답 쌍, 반환값이다.
- 기존 신호가 가설에 답하지 못할 때만 계측을 더한다. hunk마다 파일, 줄, 답하려는 질문을 일지의 Instrumentation 표에 적는다.

## 5. Journal

`.hyper/debug/<slug>.md`에 쓴다. `<slug>`는 짐작한 원인이 아니라 증상의 짧은 kebab-case 이름이다. 디렉터리가 없으면 만든다.

````markdown
# <증상 한 줄>

- 모드: findings-only | minimal-fix
- 런처: `<command>`
- 런타임: `<name and version>`
- 입력: `<the exact inputs>`
- 기대 동작: <what should happen>
- 보고: "<the user's report, quoted>"

## Resources

| Kind | Path / port / pid | Created by this run | Cleanup |
|---|---|---|---|
| temp dir | `/tmp/debug-<slug>` | yes | removed |

## Reproduction

- Command: `<exact command>`
- Working directory: `<path>`
- Output:
```text
<verbatim>
```
- Shrink steps: <what was removed, and what still failed>

## Hypotheses

| # | Axis | Claim | Distinguishing observation | If true, the fix is |
|---|---|---|---|---|
| H1 | ... | ... | ... | ... |
| H2 | ... | ... | ... | ... |

## Evidence

### <timestamp> — <what was observed>
- Source: `path:line` | `<command>` | `<log source>`
- Value: `<verbatim>`
- Interpretation: <one line>
- Confirms / refutes: H<n>

## Instrumentation

| File:line | Added | Question it answered | Removed |
|---|---|---|---|
| `path:line` | `console.log(...)` | which branch ran | yes |

## Root cause

- Mechanism: <the causal chain in one paragraph>
- Toggle proof: "With <change>, the repro produces <good>; reverting it produces <bad>."
- Fix scope: <files and approximate size>

## Verification

- Red: `<command>` → <verbatim failure>
- Green: `<command>` → <verbatim pass>
- Area checks: `<command>` → <result>

## Result: <terminal>
````

일지 규칙:

- 값을 그대로 인용한다. `items.length=0`은 증거이고, "목록이 비어 보였다"는 관찰의 기억일 뿐이다.
- 관찰마다 증거 항목 하나를 쓰고, 출처와 그 항목이 닿는 가설을 적는다.
- 일지는 실행이 진행되는 동안 고친다. 끝나고 쓰면 증거가 아니라 이야기가 된다.
- 마지막 줄은 정확히 `Result: <terminal>`이고, 값은 core의 종료 상태 표에서 하나를 고른다.

## 6. Cleanup

- 이번 실행이 만든 임시 파일, 디렉터리, 프로세스, 포트, 컨테이너, 환경 덮어쓰기를 모두 제거하고 Resources 표의 행을 하나씩 지운다.
- 이번 실행이 더한 계측 hunk를 모두 제거하고 Instrumentation 표의 행을 하나씩 지운다. 영구히 남을 자격을 얻은 로그 줄 하나의 예외는 `rules/fix-and-proof.md` §4가 맡는다.
- 디버그 포트, 백그라운드 서버, 남은 임시 디렉터리를 남긴 실행은 끝난 것이 아니다.

## Sources

> Checked 2026-11-09.

| Claim | Source |
|---|---|
| 재현 우선, 가장 작은 실패 준비로 줄이기, 자원·계측 일지 | `dbc-hbin/omp-ulw@74df40f debugging/SKILL.md` (mechanism reference, re-authored) |
| 계측을 더하기 전에 기존 테스트와 로그를 읽기 | `dbc-hbin/omp-ulw@74df40f debugging/SKILL.md` (mechanism reference, re-authored) |
| 그대로 인용한 값만 증거로 인정 | `dbc-hbin/omp-ulw@74df40f debugging/references/methodology/02-investigate.md` (mechanism reference, re-authored) |
| `Result:` 줄과 여섯 종료 상태 | integrator contract, 2026-11-09 |

### Evidence grade

`LOCAL` - 네 가지 사실, 일지 필드, 정리 체크리스트는 이 패키지의 설계다. 메커니즘 행은 라이선스가 없는 저장소에서 자기 말로 다시 쓴 것이며 텍스트나 코드를 복사하지 않았다.
