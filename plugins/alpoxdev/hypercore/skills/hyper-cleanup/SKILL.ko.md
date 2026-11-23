---
name: "hyper-cleanup"
description: "이미 동작하는 저장소에서 코드, 테스트, 주석, 군더더기를 정리하거나 지우거나 합쳐 달라는 요청인데 동작은 그대로여야 할 때 사용한다. 범위 안의 단위를 슬롭 분류나 지킬 항목으로 이름 붙이고, 삭제·재사용·플랫폼·제자리 단순화 사다리를 걷고, 첫 수정 전에 실행 가능한 기준으로 동작을 잠그고, 테스트 삭제나 합침마다 소스 변이로 증명한 뒤 바이트 단위로 복원하며, `.hyper/cleanup/` 아래에 보고서를 쓴다. 새 동작 작성, 공개 API 리팩터, 의존성 이전, 저장소 전체 서식 정리에는 사용하지 않는다."
compatibility: "파일 읽기·검색·편집, 셸, 프로젝트 자체 테스트·검사 명령이 필요하다. 번들 스크립트는 bash 3.2+, jq, 바이트 복원 확인용 shasum이 필요하다."
---

아래 규칙은 본문의 읽기 순서에 따라 엽니다. 스킬에 포함된 파일 경로는 이 문서가 있는 폴더를 기준으로 해석하고 작업 대상 경로는 프로젝트를 기준으로 해석합니다.

- [rules/categories.ko.md](rules/categories.ko.md)
- [rules/existence-ladder.ko.md](rules/existence-ladder.ko.md)
- [rules/behavior-lock.ko.md](rules/behavior-lock.ko.md)
- [rules/test-junk.ko.md](rules/test-junk.ko.md)
- [rules/correction-and-report.ko.md](rules/correction-and-report.ko.md)

# Hyper Cleanup

> 지킬 이유가 없는 코드를 걷어내고, 모든 삭제를 동작 잠금으로 증명하며, 검토자가 다시 돌릴 수 있는 보고서를 남긴다.

- **목적**: 이미 동작하는 코드베이스에서 관찰 가능한 동작을 바꾸지 않고 수정 전 기준 잠금과 바이트 복원 변이 증명으로 불필요한 코드·주석·중복 테스트를 정리합니다.
- **쓰지 않을 때**: 새 기능 추가, 공개 API 시그니처 변경, 의존성 업그레이드, 저장소 전체 일괄 포맷팅, 성능 목표 달성, 커밋·푸시에는 쓰지 않습니다.
- **입력**: 지정된 파일·디렉터리 또는 현재 작업 트리 diff(재개 시 기존 `.hyper/cleanup/<slug>.md` 잠금·보고서).
- **산출물**: 승인된 범위 안의 동작 보존 정리 수정과 `Result:` 종료 상태(`clean`, `no-change`, `awaiting_input`, `blocked`) 한 줄로 끝나는 `.hyper/cleanup/<slug>.md`.

<output_language>

사용자에게 보이는 산출물, 보고서 항목, 질문, 검증 메모는 이 표준 파일이 영어로 쓰였어도 기본적으로 한국어로 작성합니다.

소스 코드 식별자, CLI 명령, 파일 경로, 로그 줄, 오류 문자열, 스키마 키, 패키지 이름, 인용한 소스 발췌는 원래 형식을 유지합니다.

</output_language>

<purpose>

- 관찰 가능한 동작과 공개 표면을 그대로 둔 채 지킬 이유가 없는 코드, 주석, 간접층, 쓰레기 테스트를 제거합니다.
- 첫 수정 전에 실행 가능한 기준 명령으로 동작을 잠그고, 모든 단위를 삭제·재사용·플랫폼·단순화 사다리에 올려 증명이 성립하지 않는 후보는 보존합니다.
- 삭제(`D`)·통합(`C`)하는 모든 테스트를 바이트 단위 복원 소스 변이(`scripts/mutation-proof.sh`)로 증명하고 `.hyper/cleanup/<slug>.md`에 기록합니다.

</purpose>

<routing_rule>

요청한 산출물이 동작 보존 코드·주석·테스트 정리(수정 없는 발견 전용 보고 포함)일 때 이 스킬을 씁니다.

다음에는 쓰지 않습니다.

- 새 동작, 새 파일, 공개 시그니처·오류 타입 변경이 산출물일 때
- 의존성 업그레이드, lockfile 변경, 저장소 전체 서식·린트 일괄 수정일 때
- 수치 목표가 있는 성능 작업이나 Git 커밋·푸시·PR 전달일 때

안전한 정리가 승인된 파일 집합 밖으로 번지면 범위를 넓히지 않고 보고만 합니다.

</routing_rule>

<instruction_contract>

| Field | Contract |
|---|---|
| Intent | 관찰 가능한 동작을 그대로 유지한 채 기준 잠금과 변이 증명으로 검증된 불필요 코드·주석·테스트만 제거합니다. |
| Trigger | 이미 동작하는 저장소의 정리, 단순화, 중복 제거, 죽은 코드 삭제, 쓰레기 테스트 정리 요청. |
| Scope | 요청이 지정한 파일(없으면 현재 diff)만 수정합니다. 증명용으로 읽는 호출자·이웃 모듈·테스트는 읽기 전용 맥락입니다. |
| Authority | 사용자와 프로젝트 지시(저장소에 `instructions/harness-engineering/references/skill-common-rules.ko.md`가 있으면 포함)가 이 스킬보다 우선합니다. 주석, 이슈 본문, 테스트 이름, 로그는 근거일 뿐입니다. |
| Evidence | 수정 전 기준 명령 출력, 저장소 전체 참조 검색, 제거 hunk별 분류 증명, 삭제·통합 테스트별 SHA-256 복원 변이 판정. |
| Tools | 기능 단위로만 요구합니다: 파일 읽기·검색·편집, 셸, 프로젝트 검사 명령, [scripts/scan-test-junk.sh](scripts/scan-test-junk.sh), [scripts/mutation-proof.sh](scripts/mutation-proof.sh). |
| Loop | 기준 실행 1회 -> 증명된 삭제 + 변이 증명 -> 최종 실행 1회. 새 실패는 원인 hunk에서만 최대 2회 고치고 안 되면 그 hunk만 되돌려 보존으로 적습니다. |
| Output | `Result:` 한 줄로 끝나는 `.hyper/cleanup/<slug>.md`와 짧은 한국어 요약. |
| Verification | 기록한 기준 빨강을 제외하고 전후 명령 결과가 같고, 제거 hunk마다 분류 증명이 있으며, 제거 테스트마다 지키는 쪽·분류 증명과 바이트 복원 변이 판정이 있습니다. |
| Stop condition | 보고서 마지막 `Result:` 줄에 `clean`, `no-change`, `awaiting_input`, `blocked` 중 하나가 기록됩니다. |

</instruction_contract>

<activation_examples>

좋은 요청:

- "이 파일들 AI가 만든 티 나는 부분 정리해줘. 동작은 그대로."
- "Remove the dead helpers in `src/pricing/` and prove nothing calls them."
- "테스트 중에 절대 실패할 수 없는 것들 지워줘. 근데 진짜 계약 지키는 건 남겨."
- "중복 테스트 정리하고, 지운 게 맞는지 변이로 증명해줘."

나쁜 요청:

- "결제 모듈 새로 설계해줘." (새 동작)
- "`createOrder` 시그니처 바꿔줘." (공개 API 변경)
- "Next 15로 올려줘." (의존성 업그레이드)
- "레포 전체 prettier 돌려줘." (서식 일괄 변경)
- "방금 정리한 거 커밋해줘." (커밋 작업)

경계 요청:

- "뭐 지울 만한지부터 알려줘." -> 발견 전용(`findings-only`)으로 수정 없이 `Result: no-change`로 끝냅니다.
- 경로 없는 "정리해줘" -> 현재 작업 트리 diff를 범위로 잡습니다.
- "이 중복은 다른 모듈도 같이 고쳐야 해." -> 승인 범위 밖 모듈은 고치지 않고 보존 항목과 경계 사유로 보고합니다.

</activation_examples>

<trigger_conditions>

| Situation | Mode |
|---|---|
| 파일·디렉터리 지정 + 수정 권한 | 범위 정리 |
| 경로 미지정 | 현재 diff 정리 |
| 수정 없이 정리 후보만 요청 | 발견 전용 (`Result: no-change`) |
| 범위에 테스트 파일 포함 | 정리 + 테스트 원장 + `mutation-proof.sh` |
| 안전한 삭제가 승인 범위 밖 파일을 요구 | 보존 후 경계 보고 |
| 기존 미커밋 변경 또는 기준 빨강 존재 | 동작 잠금에 기록하고 타인 변경 되돌리기·빨간 테스트 삭제 금지 |

[rules/behavior-lock.ko.md](rules/behavior-lock.ko.md)가 기준 잠금을, [rules/categories.ko.md](rules/categories.ko.md)가 분류를, [rules/test-junk.ko.md](rules/test-junk.ko.md)가 테스트 표시와 두 스크립트를 맡습니다.

</trigger_conditions>

<skill_architecture>

- Core (`SKILL.ko.md`): 트리거, 모드, 계약, 단계 게이트, 체크리스트, 종료 결과.
- Rules: [rules/categories.ko.md](rules/categories.ko.md)(아홉 슬롭 분류, KEEP 예외, 제거 증명), [rules/existence-ladder.ko.md](rules/existence-ladder.ko.md)(삭제 -> 재사용 -> 플랫폼 -> 제자리 단순화), [rules/behavior-lock.ko.md](rules/behavior-lock.ko.md)(기준 기록과 기준 빨강), [rules/test-junk.ko.md](rules/test-junk.ko.md)(테스트 표시, 쓰레기 분류, 원장, 스크립트), [rules/correction-and-report.ko.md](rules/correction-and-report.ko.md)(hunk 단위 수리 한도와 보고서 배치).
- Scripts: [scripts/scan-test-junk.sh](scripts/scan-test-junk.sh)(`--json`, `--self-test`), [scripts/mutation-proof.sh](scripts/mutation-proof.sh)(소스 변이 1회 적용·테스트 실행·바이트 복원·`caught`/`survived` 보고).
- Assets: `assets/evals/hyper-cleanup-cases.jsonl`.

</skill_architecture>

<loop_policy>

- 첫 수정 전에 기준 명령을 1회 돌리고, 증명된 삭제를 적용한 뒤 같은 명령을 마지막에 1회 돌립니다(중간 전체 스위트 반복 금지).
- 새 실패가 생기면 메커니즘을 밝히며 원인 hunk에서만 최대 2회 교정하고, 두 번 실패하면 그 hunk만 되돌려 보존 코드에 기록합니다.
- 삭제(`D`)·통합(`C`)하는 테스트마다 `mutation-proof.sh`를 1회 실행하고 다음 증명 전에 SHA-256 바이트 복원을 확인합니다.

</loop_policy>

<language_and_translation_default>

`.hyper/cleanup/<slug>.md`, 질문, 마무리 요약은 한국어로 쓰고 코드 식별자, 명령, 오류 문자열, 종료 토큰은 영어로 유지합니다.

</language_and_translation_default>

<reference_routing>

- 2단계 기준 잠금 전에 [rules/behavior-lock.ko.md](rules/behavior-lock.ko.md)를 읽습니다.
- 후보를 분류하거나 자르기 전에 [rules/categories.ko.md](rules/categories.ko.md)와 [rules/existence-ladder.ko.md](rules/existence-ladder.ko.md)를 읽습니다.
- 테스트 파일이 범위에 있거나 두 스크립트를 돌리기 전에 [rules/test-junk.ko.md](rules/test-junk.ko.md)를 읽습니다.
- 게이트 실패 교정과 보고서 작성 전에 [rules/correction-and-report.ko.md](rules/correction-and-report.ko.md)를 읽습니다.

</reference_routing>

<support_file_read_order>

1. 이 `SKILL.ko.md`로 범위, 모드, 종료 결과를 확정합니다.
2. `rules/behavior-lock.ko.md`를 읽고 기준 잠금을 실행합니다.
3. `rules/categories.ko.md`와 `rules/existence-ladder.ko.md`로 모든 단위를 분류합니다.
4. 테스트가 범위에 있으면 `rules/test-junk.ko.md`를 읽습니다.
5. 최종 검증과 보고서 작성 전에 `rules/correction-and-report.ko.md`를 읽습니다.

</support_file_read_order>

<workflow>

### 재개 절차

1단계를 시작하기 전에 `.hyper/cleanup/<slug>.md`(또는 대상 범위에 맞는 `.hyper/cleanup/*.md`)가 이미 있는지 확인합니다. 미완료 보고서나 동작 잠금 기록이 디스크에 있으면 기준 명령, 기록된 기준 빨강, 승인된 파일 범위, 이미 끝난 사다리·변이 증명 행을 먼저 읽고 `git status --short`로 다른 사람의 미커밋 변경을 보호한 채, 수정 전 원 기준 잠금을 덮어쓰지 않고 첫 미완료 단계부터 이어 갑니다. `.hyper/cleanup/`에 쓰기 전에 `.gitignore`의 `.hyper/` 등록 여부를 확인합니다.

| 단계 | 수행 작업 | 끝 조건 | 건너뛰면 안 되는 이유 |
|---|---|---|---|
| 1 | 승인 범위(지정 경로나 현재 diff)와 재개 상태를 확인하고 기준 커밋·기존 미커밋 상태 기록 | 승인 파일 목록, 읽기 전용 맥락 목록, 초기 작업 트리 상태가 기록됨 | 범위를 잠그지 않고 자르면 타인의 미커밋 수정이나 범위 밖 모듈을 훼손함 |
| 2 | 첫 수정 전에 대상 영역의 자체 검사 명령을 실행해 정확한 명령줄과 기준 빨강 기록 | 동작 잠금에 명령줄, 종료 코드, 기존 실패 테스트 목록이 남음 | 수정 전 기준이 없으면 기존 빨강과 정리 회귀를 구분할 수 없음 |
| 3 | 범위 안 모든 단위를 저장소 전체 검색 증명이 붙은 슬롭 분류나 이유가 붙은 KEEP으로 4단 사다리에 배치 | 삭제 후보와 보존 항목 모두 사다리 표에 기록됨 | 분류·참조 검색 없이 지우면 공개 export나 경계 가드가 잘려 나감 |
| 4 | 증명이 성립한 코드 삭제를 적용하고(발견 전용 제외), 테스트 파일의 `D`·`C`마다 `scan-test-junk.sh`와 `mutation-proof.sh` 실행 | 제거 hunk마다 분류 증명이 있고 삭제·통합 테스트마다 SHA-256 복원이 확인된 변이 판정이 있음 | 변이 증명 없이 테스트를 지우면 실제 회귀 방어망이 조용히 사라짐 |
| 5 | 같은 기준 명령을 다시 돌려 새 실패는 원인 hunk에서만 교정(최대 2회)하거나 그 hunk만 되돌려 보존 기록 | 파일 단위 `git checkout`·`restore` 없이 최종 검사 결과가 기준 잠금과 일치함 | 파일 전체 되돌리기는 유효한 정리 hunk나 기존 사용자 변경까지 날림 |
| 6 | `git diff`로 의도 밖 수정·임시 파일 없음을 확인하고 `Result:` 한 줄로 끝나는 `.hyper/cleanup/<slug>.md` 작성 | 잠금, 사다리, 제거 hunk, 테스트 원장, 보존 코드, `Result:` 줄이 담긴 보고서가 디스크에 저장됨 | 기록 없는 삭제는 검토자가 안전성을 재현할 수 없음 |

### 단계 점검 체크리스트

종료 `Result:` 줄을 쓰기 전에 아래 예/아니오 항목을 모두 점검합니다.

| # | 예/아니오 질문 | 위반 시 되돌아갈 단계 |
|---|---|---|
| 1 | 첫 수정 전에 정확한 기준 명령을 실행·기록했고 기존 미커밋 변경과 기준 빨강을 분리했습니까? (예/아니오) | 2단계 |
| 2 | 제거한 모든 hunk가 승인된 파일 집합 안에 있으며 공개 API 변경 없이 분류와 저장소 전체 참조 증명을 갖췄습니까? (예/아니오) | 3단계 |
| 3 | 삭제(`D`)·통합(`C`)한 모든 테스트에 지키는 쪽·분류 증명과 SHA-256 바이트 복원이 확인된 `mutation-proof.sh` 판정이 있습니까? (예/아니오) | 4단계 |
| 4 | 기준 빨강 삭제나 단언 약화 없이 동일 기준 명령의 최종 실행 결과가 기준 잠금과 일치합니까? (예/아니오) | 5단계 |
| 5 | `.hyper/cleanup/<slug>.md`를 디스크에서 다시 읽어 유효한 `Result:` 한 줄로 끝나는지 확인했습니까? (예/아니오) | 6단계 |

</workflow>

<terminals>

보고서는 정확히 하나의 `Result:` 줄로 끝납니다.

| Terminal | Meaning |
|---|---|
| `clean` | 승인된 삭제가 적용됐고 동작 잠금이 통과하며 hunk·테스트 원장이 완전합니다. |
| `no-change` | 발견 전용 모드이거나 증명을 통과한 후보가 없어 검토한 단위와 보존 이유만 기록했습니다. |
| `awaiting_input` | 저장소 파일만으로 정할 수 없는 모호함 하나 때문에 질문하고 멈췄습니다. |
| `blocked` | 필요한 검사 명령이나 기능을 쓸 수 없어 정확한 공백과 시도 명령을 보고했습니다. |

</terminals>

<required>

- 첫 수정 전에 실행·기록한 정확한 기준 명령줄과 분리된 기준 빨강 목록.
- 검토한 모든 단위의 사다리 행(분류·증명이 붙은 제거 hunk와 이유가 붙은 KEEP 보존 항목).
- 삭제·통합한 테스트마다 지키는 쪽·쓰레기 분류 증명과 SHA-256 바이트 복원이 확인된 `mutation-proof.sh` 판정.
- 기준과 일치하는 최종 명령 실행 결과와 `Result:` 한 줄로 끝나는 `.hyper/cleanup/<slug>.md`.

</required>

<forbidden>

- 관찰 가능 동작·시그니처·예외 변경, 기준 빨강 테스트 삭제·기대값 완화, `git checkout`·`restore`·`reset` 파일 전체 되돌림, 승인 범위 밖 편집, 커밋·푸시.
- 나쁜 예: `src/pricing/` 폴더 안만 검색해보고 안 쓴다며 도우미 함수를 삭제함. -> 좋은 예: 저장소 전체 참조 검색으로 호출자가 0건이고 공개 export가 아님을 증명한 뒤에만 삭제함.
- 나쁜 예: 원래부터 실패하던 테스트를 지우거나 정리가 바꾼 출력에 맞춰 테스트 단언을 넓힘. -> 좋은 예: 기준 빨강은 잠금에 그대로 기록해 보존하고 단언이 깨지면 해당 정리 hunk를 되돌림.
- 나쁜 예: 실패한 hunk 하나를 취소하려고 `git restore src/foo.ts`로 파일 전체를 덮어씀. -> 좋은 예: 실패 원인 hunk만 정밀 편집으로 되돌려 다른 유효 hunk와 기존 사용자 수정을 보존함.
- 나쁜 예: 중복 테스트라며 `scripts/mutation-proof.sh` 실행과 SHA-256 복원 확인 없이 바로 삭제함. -> 좋은 예: `mutation-proof.sh`로 남은 keeper가 변이를 잡는지(`caught`)와 원본 바이트 복원을 확인한 뒤 삭제함.

</forbidden>

<validation>

- [ ] 모드가 승인과 맞고(발견 전용은 수정 0건) 모든 수정이 승인된 파일 집합 안에 머물렀다.
- [ ] 수정 전 기준 명령과 출력, 기준 빨강 목록이 `.hyper/cleanup/<slug>.md`에 기록돼 있다.
- [ ] 검토한 모든 단위에 사다리 행이 있고 제거한 hunk마다 분류, 대체, 증명이 있다.
- [ ] 삭제·통합한 모든 테스트에 지키는 쪽·분류 증명과 SHA-256 바이트 복원이 확인된 `mutation-proof.sh` 판정이 있다.
- [ ] 최종 명령 결과가 기록된 기준 빨강을 빼고 기준과 일치하며 `git diff`에 임시 파일이 남지 않았다.
- [ ] `.hyper/cleanup/<slug>.md`가 디스크에 존재하고 유효한 `Result:` 한 줄로 끝난다.

</validation>

## Sources

> Checked 2026-11-10.

| Claim | Source |
|---|---|
| KEEP 예외가 붙은 아홉 가지 슬롭 분류와 테스트 분류 | `dbc-hbin/omp-ulw@74df40f remove-ai-slops/SKILL.md` (mechanism reference, re-authored) |
| 삭제·재사용·플랫폼·단순화 사다리와 기존 사용자 동작 보존 규칙 | `dbc-hbin/omp-ulw@74df40f remove-ai-slops/SKILL.md` (mechanism reference, re-authored) |
| 기준 우선 동작 잠금, 기준 빨강 제외, 파일 단위 되돌림 금지 | `dbc-hbin/omp-ulw@74df40f remove-ai-slops/SKILL.md` (mechanism reference, re-authored) |
| 테스트 쓰레기 분류, 유지 기준선, 후보 대 지키는 쪽 판정 표 | `dbc-hbin/omp-ulw@74df40f programming/references/testing/junk-classes.md` (mechanism reference, re-authored) |
| 바이트 단위로 복원하는 소스 변이 증명 | `dbc-hbin/omp-ulw@74df40f remove-ai-slops/SKILL.md` (mechanism reference, re-authored) |
| 계약 형태, 이중 언어 패키지, 1단 링크 규칙, 트리거 우선 description | `instructions/skill/SKILL_AUTHORING.md` |
| 네 종료 결과, 보고서 절, 두 스크립트 인터페이스, `Result:` 줄 | integrator contract, 2026-11-10 (issue #24) |

### Evidence grade

`LOCAL` - 종료 결과, 보고서 배치, 스크립트 인터페이스, 수리 한도는 이 패키지의 설계이며 분류 집합, 사다리, 변이 증명 표는 원문 텍스트나 코드를 복사하지 않고 자체 문장으로 다시 작성했습니다.
