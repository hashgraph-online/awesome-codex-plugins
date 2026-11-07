# 분석·특수 목적 엔진

ClickHouse, 시계열 확장, 벡터 검색, 검색 엔진의 엔진 가이드입니다. 이 저장소들은 원본 저장소 옆에 놓입니다. 파생 저장소가 따르는 일관성 규칙은 `rules/data-modeling.md` §6을 읽습니다. 발견 사항은 `AN-*` ID를 인용합니다.

> 자주 바뀝니다. 아래 기본값과 임계값은 2026-11-07에 각 프로젝트 문서에서 확인했습니다. 설계가 어떤 수치에 달려 있으면 다시 확인합니다.

## 1. ClickHouse

| ID | Severity | Rule |
|---|---|---|
| AN-CH-01 | high | `ORDER BY`가 디스크 순서, 압축, 희소 기본 인덱스를 결정하고 나중에 테이블을 재작성하지 않고는 추가할 수 없습니다. 쿼리가 필터로 쓰는 카디널리티가 낮은 컬럼을 앞세우고 그다음 시간(흔히 `toDate(ts)`)을 둡니다. 보통 네다섯 컬럼이면 충분합니다. |
| AN-CH-02 | high | 배치로 삽입하고(최소 1,000행, 이상적으로 10,000~100,000행) 테이블당 초당 약 한 번 삽입합니다. 작고 잦은 삽입은 파트를 너무 많이 만듭니다. 클라이언트가 배치할 수 없으면 `async_insert=1`과 `wait_for_async_insert=1`을 씁니다. |
| AN-CH-03 | high | 뜨거운 경로에서 `ALTER TABLE ... UPDATE/DELETE` 뮤테이션을 피합니다. 파트 전체를 비동기로 재작성하고 롤백할 수 없습니다. 변경은 `ReplacingMergeTree`나 `CollapsingMergeTree`로 삽입하거나, 경량 삭제를 드물게 씁니다. |
| AN-CH-04 | medium | 파티셔닝은 쿼리 속도가 아니라 수명 주기(오래된 데이터 삭제나 이동)를 위한 것입니다. 파티션 키를 카디널리티가 낮게(예: `toStartOfMonth(date)`, 1,000개 값 훨씬 아래) 유지하거나 파티셔닝하지 않습니다. |
| AN-CH-05 | medium | 서로 다른 값이 대략 10,000개까지인 문자열에는 `LowCardinality(String)`을 씁니다. |
| AN-CH-06 | medium | 재시도한 삽입은 배치가 바이트 단위로 동일하고 테이블이 중복 제거 창을 유지할 때만(복제 테이블은 기본) 중복 제거됩니다. |

## 2. PostgreSQL의 시계열

| ID | Severity | Rule |
|---|---|---|
| AN-TS-01 | medium | TimescaleDB 하이퍼테이블은 시간으로 청크에 파티셔닝합니다. 활성 청크와 그 인덱스가 메모리에 들어가도록 청크 간격을 정하고 유일 제약에 시간 컬럼을 포함합니다. 행 단위 삭제 대신 보존과 압축 정책을 씁니다. |
| AN-TS-02 | low | 확장 없이도 시간 기준 기본 range 파티셔닝에 `DETACH PARTITION ... CONCURRENTLY`와 `DROP`을 쓰면 같은 보존 패턴을 얻습니다. |

## 3. 벡터 검색(pgvector와 그 밖)

| ID | Severity | Rule |
|---|---|---|
| AN-VE-01 | high | 근사 인덱스는 결과를 바꿉니다. 인덱스가 없으면 완전한 재현율(recall)의 정확 검색입니다. HNSW나 IVFFlat을 추가하기 전과 후에 표본에서 정확 검색 대비 재현율을 측정합니다. |
| AN-VE-02 | high | 필터는 근사 스캔 후에 적용되므로 선택도가 높은 필터는 `LIMIT`보다 훨씬 적은 행을 낼 수 있습니다. 선택도가 높은 필터에는 필터 컬럼의 B-tree와 정확 검색을, 뜨거운 필터 값마다 부분 인덱스를, 테넌트별 파티셔닝을, 지원되면 반복 스캔을 씁니다. |
| AN-VE-03 | medium | HNSW(기본값 `m = 16`, `ef_construction = 64`, 쿼리 `hnsw.ef_search = 40`)는 구축 시간과 메모리가 더 드는 대신 속도와 재현율이 좋습니다. IVFFlat은 데이터를 먼저 적재해야 하고 `lists`는 행/1000 근처(100만 행까지) 또는 그 이상에서 sqrt(행), `probes`는 기본값 1에서 올립니다. |
| AN-VE-04 | medium | 연산자를 연산자 클래스와 맞춥니다(`<->`는 `vector_l2_ops`, `<#>`는 `vector_ip_ops`, `<=>`는 `vector_cosine_ops`). 맞지 않으면 순차 스캔으로 폴백합니다. |
| AN-VE-05 | medium | 차원 제한을 지킵니다(`vector` 인덱스는 2,000차원까지, `halfvec`은 4,000까지). 더 큰 임베딩은 `halfvec`, 양자화, 또는 차원 축소가 필요합니다. |
| AN-VE-06 | medium | 벡터 인덱스는 대량 적재 후 `CREATE INDEX CONCURRENTLY`, 충분한 `maintenance_work_mem`, 병렬 유지보수 워커로 만듭니다. |
| AN-VE-07 | medium | 테넌트가 공유하는 벡터 인덱스 하나는 한 테넌트의 데이터가 다른 테넌트의 재현율을 떨어뜨리게 합니다. 격리가 중요하면 테넌트별로 파티셔닝합니다. |

## 4. 검색 엔진(Elasticsearch, OpenSearch)

| ID | Severity | Rule |
|---|---|---|
| AN-SE-01 | high | 운영에서는 명시적 매핑을 정의합니다. 기존 필드 매핑은 재인덱싱 없이 바꿀 수 없습니다. |
| AN-SE-02 | high | 문서에 사용자가 제공한 키가 있으면 동적 필드를 제한합니다(`index.mapping.total_fields.limit`, `dynamic: strict` 또는 `false`). 무제한 매핑은 메모리를 고갈시킵니다. |
| AN-SE-03 | medium | 필드에 검색과 정렬·집계·정확 필터가 모두 필요하면 `text`(검색)와 `keyword`(정렬, 집계, 정확 필터) 양쪽으로 매핑합니다. |
| AN-SE-04 | medium | 검색 인덱스는 파생 저장소입니다. 재인덱싱 작업과 앨리어스 교체로 원본 저장소에서 다시 만들 수 있어야 합니다. |

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| 희소 기본 인덱스, 그래뉼, 키 순서 | <https://clickhouse.com/docs/guides/clickhouse/data-modelling/sparse-primary-indexes> |
| 정렬 키는 나중에 추가할 수 없음 | <https://clickhouse.com/docs/concepts/best-practices/choosing-a-primary-key> |
| 배치 크기, 삽입 속도, 비동기 삽입, 중복 제거 | <https://clickhouse.com/docs/concepts/best-practices/selecting-an-insert-strategy> |
| 뮤테이션이 파트를 재작성함 | <https://clickhouse.com/docs/concepts/best-practices/avoid-mutations> |
| 데이터 관리로서의 파티셔닝과 낮은 파티션 키 카디널리티 | <https://clickhouse.com/docs/concepts/best-practices/partitioning-keys> |
| `LowCardinality` 임계값 | <https://clickhouse.com/docs/reference/data-types/lowcardinality> |
| 하이퍼테이블과 청크 크기 | <https://www.tigerdata.com/docs/learn/hypertables/understand-hypertables> |
| pgvector 정확 검색, HNSW와 IVFFlat 파라미터, 연산자, 필터링, 차원 제한 | <https://github.com/pgvector/pgvector> |
| Elasticsearch 매핑, 불변성, 매핑 폭증 | <https://www.elastic.co/docs/manage-data/data-store/mapping> |
| 규칙 ID와 심각도 | 이 패키지가 고른 설계이며 검증된 최적값이 아님 |
