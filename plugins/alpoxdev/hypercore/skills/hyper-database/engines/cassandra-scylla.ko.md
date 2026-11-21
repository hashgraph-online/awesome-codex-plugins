# Apache Cassandra와 ScyllaDB

Apache Cassandra와 ScyllaDB(자체 호스팅, Astra, ScyllaDB Cloud, CQL 호환 서비스인 Amazon Keyspaces) 엔진 가이드입니다. `rules/engine-detection.md`가 이곳으로 라우팅한 뒤 읽습니다. 표시가 없는 규칙은 둘 다에 적용됩니다. ScyllaDB는 컴팩션, 인덱싱, 도구 구현이 다릅니다. 발견 사항은 `CS-*` ID를 인용합니다.

## 1. 날짜가 붙은 사실

> 자주 바뀝니다. 2026-11-07에 Cassandra 다운로드 페이지, ScyllaDB 버전 지원 페이지, ScyllaDB 라이선스 파일에서 확인했습니다. 도입이나 업그레이드 결정을 내리기 전에 다시 확인합니다.

| Fact | Value |
|---|---|
| Cassandra 현재 | 5.0 라인(5.0.9, 2026-08-07)이고 8.0 릴리스까지 유지됩니다. 4.1과 4.0 라인도 패치됩니다. 5.0은 JDK 17이 필요합니다 |
| Cassandra 5.0 추가 사항 | 스토리지 연결 인덱스(SAI), 통합 컴팩션 전략(UCS), 트라이 멤테이블과 SSTable, vector 타입, 동적 데이터 마스킹 |
| ScyllaDB 라이선스 | ScyllaDB Software License Agreement v1.1(2026-04-12 갱신). 소스 공개 방식이고, 지난 12개월에 ScyllaDB와 유료 관계가 없는 주체만 무료로 쓸 수 있으며, 배포 전체에서 스토리지 10 TB와 vCPU 50개로 제한됩니다. 오픈 소스가 아닙니다 |
| ScyllaDB 릴리스 | 달력 버전 `YYYY.N`. 지원 대상은 2026.3, 2026.2, 2026.1 LTS, 2025.1 LTS입니다 |

## 2. 모델링

| ID | Severity | Rule |
|---|---|---|
| CS-MOD-01 | critical | 쿼리마다 테이블 하나로 설계합니다. 파티션 키는 쿼리가 동등 조건으로 거르는 값이고, 클러스터링 컬럼이 정렬과 범위를 담당합니다. 조인 대신 여러 테이블로 반정규화합니다. 조인도 파티션을 넘는 트랜잭션도 없습니다. |
| CS-MOD-02 | high | 카디널리티가 높고 트래픽이 고른 파티션 키를 고릅니다. 인기 있는 엔티티를 파티션 키로 쓰면(유명 사용자의 메시지) 핫 파티션이 됩니다. |
| CS-MOD-03 | high | 파티션 키에 시간 버킷을 더해 파티션 크기를 제한합니다(`PRIMARY KEY ((user_id, day), event_time)`). 한정 없는 파티션은 읽기, 복구, 컴팩션이 느려집니다. Cassandra는 기본으로 크기 제한을 강제하지 않으므로 `partition_size_warn_threshold`를 설정하고 `nodetool tablestats`를 감시합니다. |
| CS-MOD-04 | medium | 스키마 검토에 테이블마다 파티션 키, 클러스터링 순서, 그것이 처리하는 쿼리를 적습니다. 테이블이 없는 쿼리는 인덱스가 빠진 것이 아니라 테이블이 빠진 것입니다. |
| CS-MOD-05 | medium | 갱신은 셀 단위로 타임스탬프 기준 마지막 쓰기 승리로 해결되는 업서트입니다. 시계를 동기화하고 클라이언트가 보내는 타임스탬프를 제한합니다. |
| CS-MOD-06 | low | 애플리케이션마다 키스페이스 하나를 `NetworkTopologyStrategy`로 씁니다. `SimpleStrategy`는 데이터센터 배치를 무시하므로 운영에 쓰지 않습니다. |

## 3. 쿼리와 인덱스

| ID | Severity | Rule |
|---|---|---|
| CS-QRY-01 | high | 애플리케이션 코드의 `ALLOW FILTERING`은 설계 결함으로 봅니다. 코디네이터에서 파티션을 스캔합니다. |
| CS-QRY-02 | medium | Cassandra 5.0에서는 가끔 쓰는 추가 필터에 레거시 보조 인덱스보다 SAI를 선호합니다(컬럼당 인덱스 하나, 테이블당 설정 가능한 상한, 디스크 약 20~35% 추가). 자주 쓰는 쿼리는 여전히 자기 테이블을 가질 자격이 있습니다. ScyllaDB 보조 인덱스는 구체화 뷰 위에 만들어지고 그 쓰기 비용을 함께 집니다. |
| CS-QRY-03 | high | 파티션 키에 대한 `IN`은 드물게 쓰고 배치는 작고 단일 파티션으로 유지합니다. 다중 파티션 배치는 속도가 아니라 원자성을 위한 것입니다(기본 경고 5 KiB, 실패 50 KiB). |
| CS-QRY-04 | high | 경량 트랜잭션(`IF NOT EXISTS`, `IF col = ...`)은 여러 번 왕복합니다. 뜨거운 경로에서 빼 둡니다. |
| CS-QRY-05 | medium | 큰 읽기는 큰 `LIMIT` 대신 드라이버의 페이징 상태로 나눕니다. |

## 4. 일관성과 복제

| ID | Severity | Rule |
|---|---|---|
| CS-CON-01 | high | 쓰기는 모든 복제본으로 갑니다. 일관성 수준은 승인 몇 개를 기다릴지만 정합니다. 자기 쓰기 읽기를 원하면 읽기와 쓰기 복제본 수의 합이 복제 계수보다 커야 합니다(RF 3이면 `QUORUM`/`QUORUM`, 데이터센터 안이면 `LOCAL_QUORUM`). |
| CS-CON-02 | high | 내구성이 중요한 곳에 `ANY`를 쓰지 않습니다. 힌트로만 보관된 쓰기를 승인할 수 있습니다. 가능하면 가드레일로 키스페이스마다 허용 수준을 제한합니다. |
| CS-CON-03 | medium | 복구(repair)를 `gc_grace_seconds` 안에서 정기적으로(지원되면 증분으로) 실행합니다. 그 기간보다 오래 꺼져 있던 노드는 삭제된 데이터를 되살릴 수 있습니다. |

## 5. 삭제, 묘비, 컴팩션

| ID | Severity | Rule |
|---|---|---|
| CS-TMB-01 | high | 삭제와 TTL 만료는 묘비를 쓰고, 묘비는 `gc_grace_seconds`(기본 10일)가 지나고 가려진 데이터를 덮는 컴팩션이 실행된 뒤에만 정리됩니다. 삭제가 많은 큐나 "삭제 후 삽입으로 갱신" 패턴을 피합니다. 묘비 실패 임계값(쿼리당 기본 100,000)을 넘으면 읽기가 실패합니다. |
| CS-TMB-02 | medium | `nodetool tablestats`, 묘비 히스토그램, `sstableexpiredblockers`로 묘비를 조사합니다. |
| CS-CMP-01 | medium | Cassandra의 코드 기본값은 여전히 크기 계층(size-tiered) 컴팩션입니다. 5.0에서는 UCS를 명시적으로 설정하고(문서가 대부분 워크로드에 권함) 읽기 부하, 쓰기 부하, 시계열 테이블에 맞는 스케일링 파라미터를 고릅니다. ScyllaDB는 자체 컴팩션 전략이 있으므로 Cassandra의 것을 가정하지 말고 그 문서를 읽습니다. |

## 6. 운영

| ID | Severity | Rule |
|---|---|---|
| CS-OPS-01 | high | 스냅숏에 증분 백업이나 벤더 백업 도구를 더해 백업하고, 별도 클러스터로 복구 시험을 합니다. |
| CS-OPS-02 | medium | 기본으로 꺼져 있는 가드레일(파티션 크기, 묘비, 테이블당 컬럼 수, 페이지 크기, `IN` 카티션 곱)을 팀이 합의한 값으로 켭니다. |
| CS-OPS-03 | high | ScyllaDB를 도입하기 전에 조직의 상업적 관계와 사용량에 비추어 라이선스 조건을 확인합니다. 무료 허용에는 자격과 규모 제한이 있습니다. |

## 7. 검증 명령

```bash
nodetool status                 # ring and node health
nodetool tablestats ks.table    # partition sizes, tombstones, read latency
nodetool tablehistograms ks.table
nodetool compactionstats
cqlsh -e "TRACING ON; SELECT ... ;"   # per-query trace on a disposable cluster
```

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| Cassandra 릴리스 라인과 지원 | <https://cassandra.apache.org/_/download.html> |
| Cassandra 5.0 신규 기능과 JDK 17 | <https://cassandra.apache.org/doc/latest/cassandra/new/index.html> |
| 키스페이스, `NetworkTopologyStrategy`, DDL 규칙 | <https://cassandra.apache.org/doc/latest/cassandra/developing/cql/ddl.html> |
| 단일 파티션 보장, 일관성 수준, 마지막 쓰기 승리 | <https://cassandra.apache.org/doc/latest/cassandra/architecture/dynamo.html> |
| SAI 동작과 제한 | <https://cassandra.apache.org/doc/latest/cassandra/developing/cql/indexing/sai/sai-faq.html> |
| UCS 권고와 파라미터 | <https://cassandra.apache.org/doc/latest/cassandra/managing/operating/compaction/ucs.html> |
| 묘비와 `gc_grace_seconds` | <https://cassandra.apache.org/doc/latest/cassandra/managing/operating/compaction/tombstones.html> |
| 배치, 묘비, 가드레일 기본값 | <https://raw.githubusercontent.com/apache/cassandra/trunk/conf/cassandra.yaml> |
| 코드 기본값으로서의 크기 계층 컴팩션 | <https://raw.githubusercontent.com/apache/cassandra/trunk/src/java/org/apache/cassandra/schema/CompactionParams.java> |
| ScyllaDB 라이선스 조건과 사용 한도 | <https://raw.githubusercontent.com/scylladb/scylladb/master/LICENSE-ScyllaDB-Source-Available.md> |
| ScyllaDB 지원 릴리스 | <https://docs.scylladb.com/stable/versioning/version-support.html> |
| ScyllaDB 파티션 키와 쿼리 설계 지침, 구체화 뷰 위의 보조 인덱스 | <https://docs.scylladb.com/stable/get-started/data-modeling/best-practices.html>, <https://docs.scylladb.com/main/get-started/data-modeling/query-design.html> |
| 규칙 ID와 심각도 | 이 패키지가 고른 설계이며 검증된 최적값이 아님 |
