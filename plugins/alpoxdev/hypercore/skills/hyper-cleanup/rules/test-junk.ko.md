# 테스트 쓰레기

파일 집합에 테스트가 들어 있거나, 정리가 어떤 삭제를 증명할 테스트를 필요로 할 때 이 파일을 읽습니다. 표시, 쓰레기 분류, 분류마다 필요한 증명, 두 스크립트를 돌리는 방법을 맡습니다.

## 1. 표시

범위 안의 모든 테스트 선언은 표시 하나를 받습니다. 표시가 그 선언이 남을지, 바뀔지, 합쳐질지, 갈지 정합니다.

| 표시 | 뜻 | 원장 줄이 대는 것 |
|---|---|---|
| `R` 유지 | 계약을 지킨다 | 그 계약과 그것이 잡을 회귀 |
| `F` 고침 | 계약은 진짜인데 단언이 약하다 | 고친 단언 |
| `C` 합침 | 단언이 지키는 쪽으로 옮겨가고 선언은 사라진다 | 지키는 쪽 |
| `D` 삭제 | 계약이 없거나 다른 테스트가 이미 소유한다 | 소유 테스트, 또는 계약이 없는 이유, 그리고 증명 |

`F`는 약한 `D`가 아닙니다. 진짜 계약을 지키는 약한 단언은 제자리에서 고칩니다. 지우면 계약이 사라집니다.

## 2. 쓰레기 분류

아래 분류에 드는 선언은 `D`나 `C`의 후보이고, 자동 삭제 대상은 아닙니다. §3의 KEEP 목록이 분류보다 우선합니다.

| 분류 | 모양 | 쓰레기라는 증명 |
|---|---|---|
| 실패할 수 없음 | 단언이 없거나, 값을 자기 자신과 비교하거나, 기대값을 테스트 대상 코드가 계산한다 | 테스트가 통과하는 운영 코드 변이 |
| 변경 증명서 | diff를 고정한다. 상수, 문자열, 호출, 수정의 모양 | 변경을 되돌리면 회귀가 아니라 diff 때문에 실패한다 |
| 모의 메아리 | 모의 객체가 테스트가 단언할 값을 그대로 돌려준다 | 소유자를 변이해도 테스트가 초록이다 |
| 구현 거울 | 호출 순서, 호출 횟수, 사설 인자, 내부 상태 모양을 단언한다 | 실제 경계의 지키는 쪽이 동작 변이를 잡는다 |
| 산문 고정 | 문서의 문구, 제목, 순서, 스냅숏, 길이를 단언한다 | 변이할 동작이 없다. 저장소의 산문 테스트 규칙을 인용한다 |
| 복사한 목록 | 소스를 비추는 export, 파일, 도구, 키의 하드코딩 목록 | 생성기, 신선도 검사, 실제 소비자가 이미 목록을 소유한다 |
| 소스 grep | 소스 파일을 읽어 문자열이나 import를 맞춘다 | 이름만 바꾸는 리팩터에도 빨개지고 동작은 그대로다 |
| 중복 계약 | 전송이나 생명주기 위험이 다르지 않은데 같은 입출력을 두 계층에서 단언한다 | 변이를 둘 다 잡는다. 더 강한 경계를 남긴다 |
| 계층 재생 | 공유 도우미를 그것을 부르는 모든 감싸개로 다시 테스트한다 | 도우미 소유 테스트 하나와 실제 감싸개별 배선 테스트 하나 |
| 조작된 사후 조건 | fixture가 소유자가 만들어야 할 상태를 미리 넣고, 아무것도 쓰지 않는 저장소를 단언한다 | 쓰는 쪽을 변이해도 테스트가 초록이다 |
| 능력 재진술 | 플래그가 약속하는 전달 대신 플래그가 `true`임을 단언한다 | 전달 테스트가 소유하거나, 아예 없다 |
| 입력 기록 | 자식 프로세스가 해석한 상태가 아니라 넘긴 argv, URL, 요청을 단언한다 | 자식의 그 입력 처리를 변이해도 테스트가 초록이다 |
| 근접 중복 | 입력 리터럴만 다른 N개 선언 | 표 하나로 합친다. 모든 옛 단언이 행으로 남는다 |

두 가지 결과는 표가 아니라 여기에 속합니다. **이름이 틀린** 테스트는 이름이 아니라 실제로 검사하는 것으로 표시합니다. **바뀌지 않은 기준에서 빨간** 테스트는 제품 버그이고, 원장을 떠나 [behavior-lock.md](behavior-lock.md) §2의 보고서로 갑니다.

## 3. 유지 기준선

아래에 해당하면 위 분류에 걸려도 `R`로 남습니다. 원장에 그 테스트를 지키는 행을 적습니다.

- 공개 API, SDK, RPC, 프로토콜 계약
- 설정 스키마나 기본값
- 마이그레이션, 저장 형식, 호환 스위트
- 보안 경계나 권한 검사
- 플랫폼 동작. 실제 런타임에서 도는 배포 산출물 포함
- 실제 산출물 둘 사이의 배포 사본 동등성
- 기계가 소비하는 토큰: 파싱하는 필드, 런타임이 grep하는 표식, 스키마 키, 파싱한 frontmatter의 라우팅 관련 조각
- 이슈 회귀. 다른 테스트가 그 회귀에서 실패함이 증명될 때까지

정적이거나 느리다는 것은 삭제 이유가 아닙니다. 산문 파일에는 행동 이음매가 없습니다. 문구, 단어 수, 제목 고정을 더하지 말고, 기계가 실제로 파싱하는 값만 덮습니다.

## 4. `D`와 `C`의 증명

운영 소유자를 깨뜨린 뒤, 수정하지 않은 테스트 트리에서 후보와 이름 붙인 지키는 쪽을 돌립니다.

| 후보 | 지키는 쪽 | 판정 |
|---|---|---|
| 초록 | 빨강 | 후보가 이것을 잡지 못한다 → `D` 증명 |
| 빨강 | 빨강 | 이미 덮였다 → `D` 또는 `C` 증명 |
| 빨강 | 초록 | 후보가 유일한 증명이다 → `R`, 또는 지키는 쪽에 합치고 다시 돌린다 |
| 초록 | 초록 | 변이가 동작을 놓쳤다 → 수정이 들어갔는지 확인하고 다른 변이를 고른다 |

행마다 소유자를 바이트 단위로 되돌리고, 변이는 절대 커밋하지 않습니다. 그 복원을 `scripts/mutation-proof.sh`가 합니다.

```sh
bash scripts/mutation-proof.sh --file src/pricing.ts --find 'if (total > 0)' --replace 'if (total >= 0)' --test 'npm test -- pricing'
bash scripts/mutation-proof.sh --file src/pricing.ts --find 'a' --replace 'b' --test 'npm test -- pricing' --json
```

스크립트는 판정 하나를 냅니다. 변이가 들어간 상태에서 테스트가 실패하면 `caught`, 통과하면 `survived`입니다. 보고 전에 파일을 복원하고 SHA-256을 비교하므로 `survived` 판정도 트리를 깨끗하게 남깁니다. 종료 코드 0은 판정과 무관하게 증명이 돌았다는 뜻이고, 2는 사용법이나 대상 오류, 3은 복원을 확인하지 못했으며 백업 경로를 출력합니다. `--find`는 정확히 한 번 나와야 하며, 한 실행에 변이 하나를 유지합니다.

`--test`는 현재 디렉터리의 `sh -c`로 돌아 실제 프로젝트와 실제 러너를 봅니다. 같은 파일의 변이는 다른 변이와 병렬로 돌지 않습니다. 둘이 서로의 복원을 덮어쓰기 때문입니다.

## 5. 후보 찾기

`scripts/scan-test-junk.sh`는 정적 읽기로 보이는 분류를 보고합니다. 그 발견은 원장의 후보이고 삭제가 아닙니다.

```sh
bash scripts/scan-test-junk.sh tests/ src/pricing.test.ts
bash scripts/scan-test-junk.sh tests/ --json
bash scripts/scan-test-junk.sh --self-test
```

| 코드 | 잡는 것 |
|---|---|
| `FOCUSED_TEST` | `.only`, `fit`, `fdescribe`, `focus: true`, 집중 표시 |
| `SKIPPED_TEST` | `.skip`, `xit`, `xdescribe`, `todo`, `#[ignore]`, skip 표시 |
| `FIXED_SLEEP` | 숫자 `sleep`, `waitForTimeout`, 고정 지연 `setTimeout` |
| `SELF_COMPARISON` | 값을 자기 자신과 비교하는 단언 |
| `WEAK_ASSERTION` | 길이나 비어 있지 않음만 증명하는 단언 |
| `SOURCE_TEXT_GREP` | 소스 파일을 읽어 텍스트를 맞추는 테스트 |

스캔은 읽기 전용이고 받은 경로 밖으로 넓히지 않습니다. 디렉터리는 흔한 러너의 테스트 파일 이름 규칙으로 검색합니다. 종료 코드 0은 발견이 있든 없든 스캔이 끝났다는 뜻이고, 2는 사용법, 경로, 도구 오류입니다.

출력의 코드는 그 줄을 읽으라는 이유이고, 자르라는 이유가 아닙니다. 독립적으로 계산한 두 값을 비교하는 `SELF_COMPARISON`은 오탐이고, 유지 기준선 테스트의 `WEAK_ASSERTION`도 원장이 기록하는 오탐입니다.

## 6. 원장 쓰기

`D`, `C`, `F`마다 행 하나입니다. 행은 감사 기록이므로 요약이 아니라 경로와 case를 이름으로 댑니다.

```markdown
| Test | Mark | Keeper or reason | Proof |
|---|---|---|---|
| tests/pricing.test.ts:88 `totals` | D | tests/checkout.test.ts:120 owns the contract | mutation `> 0` → `>= 0`; candidate green, keeper red |
| tests/format.test.ts:31 `pads` | F | keeps the contract for zero padding | assertion repaired to compare the padded string |
| tests/api.test.ts:14 `returns list` | R | public API contract | — |
```

## Sources

> Checked 2026-11-10.

| Claim | Source |
|---|---|
| 테스트 쓰레기를 제거·고침·합침·문서화로 분류하고 분류마다 증명을 붙임 | `dbc-hbin/omp-ulw@74df40f remove-ai-slops/SKILL.md` (mechanism reference, re-authored) |
| 쓰레기 분류 표, 유지 기준선, R/F/C/D 표시 | `dbc-hbin/omp-ulw@74df40f programming/references/testing/junk-classes.md` (mechanism reference, re-authored) |
| 후보와 지키는 쪽 판정 표, 변이마다 바이트 동일 복원 | `dbc-hbin/omp-ulw@74df40f remove-ai-slops/SKILL.md` (mechanism reference, re-authored) |
| 정적 검출기의 발견은 후보이고 자동 삭제가 아님 | `dbc-hbin/omp-ulw@74df40f remove-ai-slops/SKILL.md` (mechanism reference, re-authored) |
| 두 스크립트의 인터페이스, 코드, 종료 코드 의미 | integrator contract, 2026-11-10 (issue #24) |

### Evidence grade

`LOCAL` - 표시 집합, 정적 코드 이름, 원장 행 형태는 이 패키지의 설계입니다. 분류 목록과 증명 표는 라이선스가 없는 저장소에서 자기 말로 다시 썼으며 텍스트나 코드를 복사하지 않았습니다.
