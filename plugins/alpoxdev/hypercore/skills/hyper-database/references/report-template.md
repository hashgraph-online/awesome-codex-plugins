# Report Template

Use this reference when writing `.hyper/database/<slug>/report.md`. Write the report in Korean; keep SQL, commands, identifiers, and rule IDs in English. Omit a section only when the mode table below marks it optional and it has nothing to say; write `해당 없음` rather than deleting a required one.

## Section Matrix

| Section | design | review | change | tune | operate | choose |
|---|---|---|---|---|---|---|
| 1. 요약 | required | required | required | required | required | required |
| 2. 감지 근거 | required | required | required | required | required | optional |
| 3. 입력과 가정 | required | optional | required | required | required | required |
| 4. 발견 사항 | optional | required | required | required | required | optional |
| 5. 설계 또는 변경 | required | - | required | required | required | - |
| 6. 비교와 권고 | optional | - | - | - | - | required |
| 7. 운영 영향 | required | optional | required | optional | required | required |
| 8. 검증 | required | required | required | required | required | optional |
| 9. 남은 위험과 다음 단계 | required | required | required | required | required | required |

## Template

````markdown
# <작업 제목>

- 모드: design | review | change | tune | operate | choose
- 대상: <저장소 경로, 패키지, 데이터베이스 이름(값 없이)>
- 기준일: YYYY-MM-DD

## 1. 요약

<결론 세 줄 이내: 무엇을 판단했고, 무엇을 바꿨고, 가장 큰 위험은 무엇인가>

## 2. 감지 근거

| 엔진 | 근거 파일 | 신호 | 적용 가이드 |
|---|---|---|---|
| postgres | drizzle.config.ts | `dialect: 'postgresql'` | engines/postgres.md |

## 3. 입력과 가정

| 접근 패턴 | 읽기/쓰기 | 조건·정렬 | 빈도 | 담당 키·인덱스 |
|---|---|---|---|---|
| 사용자별 최근 주문 20개 | 읽기 | `user_id =`, `created_at desc` | 초당 300 | `orders (user_id, created_at desc)` |

- 데이터 규모: <현재 행·항목 수, 일 증가량, 보존 기간>
- 불변 조건: <깨지면 안 되는 규칙>
- 가정: <사용자 답이 없어 정한 값과 그 이유>

## 4. 발견 사항

| ID | 심각도 | 위치 | 근거 | 수정 |
|---|---|---|---|---|
| PG-IDX-01 | high | `migrations/0042.sql:7` | `CREATE INDEX`가 `CONCURRENTLY` 없이 1억 행 테이블에 걸림 | `CREATE INDEX CONCURRENTLY`로 분리, 트랜잭션 밖에서 실행 |

## 5. 설계 또는 변경

<스키마·키 배치·마이그레이션 단계. 단계마다 잠금, 소요 시간, 되돌리는 방법>

## 6. 비교와 권고

| 기준 | 후보 A | 후보 B |
|---|---|---|

- 권고: <선택과 이유>
- 판단을 바꿀 근거: <어떤 사실이 나오면 다른 선택이 맞는가>

## 7. 운영 영향

- 백업·복구: <방식, RPO/RTO, 복구 시험 여부>
- 용량: <저장 공간·메모리·IOPS 추정과 공식>
- 보안: <역할, 권한, 암호화, 개인정보>
- 모니터링: <지표와 경보 기준>

## 8. 검증

| 확인 | 명령·방법 | 결과 | 출처 파일 |
|---|---|---|---|
| 인덱스 사용 | `EXPLAIN (ANALYZE, BUFFERS) ...` (일회용 DB, 100만 행) | Index Scan, 412ms -> 3ms | plan-after.txt |
| 복구 시험 | - | not run: 백업 접근 권한 없음 | - |

## 9. 남은 위험과 다음 단계

- <위험과 그 결과, 담당, 다음 행동>
````

## Rules

- Every number names its lineage: `측정`(with the command), `추정`(with the formula), or `사용자 제공`.
- Plans, linter output, and detector JSON go beside the report as files and are linked, not pasted in full.
- Redact connection strings, passwords, tokens, and customer rows as `<redacted>`.

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| The section set and the mode matrix | this package's chosen design, not a validated optimum |
