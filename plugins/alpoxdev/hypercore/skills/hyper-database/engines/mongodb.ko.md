# MongoDB

MongoDB(자체 호스팅 복제본 세트와 샤딩 클러스터, Atlas) 엔진 가이드입니다. `rules/engine-detection.md`가 이곳으로 라우팅한 뒤 읽습니다. 발견 사항은 `MG-*` ID를 인용합니다.

## 1. 날짜가 붙은 사실

> 자주 바뀝니다. 2026-11-07에 MongoDB 9.0, 8.0 릴리스 노트와 제한 페이지에서 확인했습니다. 버전 결정을 내리기 전에 다시 확인합니다.

| Fact | Value |
|---|---|
| 현재 메이저 | 9.0(9.0.0은 2026-09-28, 9.0.4는 2026-10-13). 8.0도 계속 패치됩니다(8.0.34는 2026-10-13) |
| 설계에 영향을 주는 9.0 변경 | `maxConcurrentMultiDocumentTransactions`(기본 10000, 오류 `TooManyOpenTransactions`)로 상한이 걸린 열린 다중 문서 트랜잭션; 작업당 메모리 제한 1 GB 또는 서버 메모리의 20% 중 큰 값 |
| 8.0 변경 | `{w: "majority"}`는 과반이 oplog 항목을 내구성 있게 기록하면 보조가 적용하기 전에 승인합니다 |
| 하드 제한 | 문서 16 MiB; 중첩 깊이 100단계; 네임스페이스 255바이트(샤딩 시 235) |
| 기본값 | 쓰기 고려(write concern) `w: "majority"`(아비터가 있으면 `w: 1`로 떨어질 수 있음); 읽기 고려(read concern) `"local"`; 드라이버 `maxPoolSize` 100 |

## 2. 모델링

| ID | Severity | Rule |
|---|---|---|
| MG-MOD-01 | high | 쿼리에서 모델링합니다. 함께 읽는 데이터는 함께 저장합니다. 정규화된 관계형 스키마를 테이블 하나당 컬렉션 하나로 옮기지 않고, 엔드포인트마다 `$lookup` 단계 수를 냄새로 셉니다. |
| MG-MOD-02 | high | 자식이 부모와 함께 읽히고 갱신되며 부모에 속하고 크기가 한정되면 내장합니다. 자식 쪽 카디널리티가 크거나 한정되지 않거나, 쓰기 부하가 큰 워크로드에서 따로 쓰이거나, 독립적으로 존재하면 참조합니다. |
| MG-MOD-03 | critical | 배열이 한정 없이 커지게 두지 않습니다(부모 문서의 댓글, 이벤트, 팔로워). 문서를 16 MiB 한계로 밀어붙이고 모든 갱신이 큰 문서를 재작성하게 만듭니다. 자식 컬렉션이나 버킷으로 옮기고 `$jsonSchema`의 `maxItems`로 배열을 제한합니다. |
| MG-MOD-04 | high | 각 불변 조건을 가능하면 문서 하나 안에서 성립하게 설계합니다. 단일 문서 쓰기는 원자적입니다. 다중 문서 트랜잭션은 비용이 더 들고 스키마 설계를 대신하지 못합니다. |
| MG-MOD-05 | medium | 중복(확장 참조, 계산, 부분집합 패턴)은 변경 불가능하거나 오래된 값을 견디는 데이터에만 쓰고, 그 사본을 갱신하는 주체를 이름으로 밝힙니다. |
| MG-MOD-06 | medium | 필요에 따라 문서화된 패턴을 씁니다. 시계열 데이터에는 버킷이나 네이티브 시계열 컬렉션, 크게 넘치는 문서 몇 개에는 outlier, 큰 자식 집합의 뜨거운 일부에는 subset, 읽기 부하가 큰 집계에는 computed, 무중단 형태 변경에는 스키마 버전 필드(`schemaVersion`), 콜드 데이터에는 archive를 씁니다. |
| MG-MOD-07 | high | `$jsonSchema` 검증으로 계약을 강제합니다(쿼리가 의존하는 필드의 `bsonType`, `required`, `maxItems`). `validationLevel: "moderate"`와 `validationAction: "warn"`으로 시작해 `"error"`로 조입니다. 동작이 `"warn"`인 동안에는 아무것도 거부되지 않으므로 `maxItems` 상한은 전환 전까지 적용되지 않습니다. |
| MG-MOD-08 | medium | 중복 필드 이름과 내장 경로와 충돌하는 점이 든 최상위 필드 이름을 피합니다. |

## 3. 인덱스와 쿼리

| ID | Severity | Rule |
|---|---|---|
| MG-IDX-01 | high | 복합 인덱스 필드는 동등(Equality), 정렬(Sort), 범위(Range) 순서(ESR)로 배치합니다. `$ne`, `$nin`, `$regex`는 범위 조건자로 동작하고, 값이 200개를 넘는 `$in`은 범위처럼 동작해 인덱스가 정렬을 처리하지 못하게 합니다. |
| MG-IDX-02 | medium | MongoDB는 보통 쿼리마다 인덱스 하나를 씁니다(`$or` 분기마다 각자의 인덱스를 쓸 수 있음). 인덱스 교집합이 빠진 복합 인덱스를 구해 주리라 기대하지 않습니다. |
| MG-IDX-03 | medium | 인덱스는 자기 정렬 방향과 완전한 역방향만 처리합니다. 혼합 정렬(`{a: 1, b: -1}`)에는 정확히 같은 패턴의 인덱스가 필요합니다. 콜레이션은 쿼리와 인덱스가 일치해야 합니다. |
| MG-IDX-04 | medium | `explain("executionStats")`를 읽습니다. `totalKeysExamined`와 `totalDocsExamined`가 `nReturned`에 가깝게 맞추고, 뜨거운 쿼리의 `COLLSCAN`과 메모리 `SORT` 단계는 발견 사항입니다. `explain`은 계획 캐시를 우회합니다. |
| MG-IDX-05 | medium | 희소 인덱스보다 부분 인덱스를 선호합니다. 부분 인덱스는 쿼리 조건자가 그 필터를 함의할 때만 쓰입니다. 샤드 키와 `_id` 인덱스는 부분 인덱스로 만들 수 없습니다. |
| MG-IDX-06 | medium | 모든 인덱스는 쓰기 증폭과 메모리 비용을 냅니다. `$indexStats`(업무 주기 하나 동안 `accesses.ops`가 0 근처)로 감사하고 `hideIndex`로 숨긴 뒤 지켜보고 삭제합니다. 인덱스가 약 20개를 훨씬 넘는 컬렉션은 검토할 가치가 있습니다. |
| MG-IDX-07 | medium | TTL 인덱스는 단일 필드입니다. 모니터는 60초마다 돌고 회차마다 정해진 배치만 제거하므로 만료가 늦어집니다. 큰 컬렉션에 TTL 인덱스를 추가하기 전에 기존 백로그를 배치로 삭제합니다. |
| MG-IDX-08 | high | 큰 컬렉션의 인덱스는 한가한 시간대에 만들고 복제 지연을 감시합니다. 인덱스 구축은 모든 멤버의 I/O를 소모합니다. |

## 4. 트랜잭션, 고려 수준, 복제

| ID | Severity | Rule |
|---|---|---|
| MG-TX-01 | high | 트랜잭션에는 복제본 세트나 샤딩 클러스터가 필요하고, 수명 제한(기본 1분 미만) 안에 끝나야 하며, 잠금을 기다리는 시간이 많아야 몇 밀리초입니다. 트랜잭션은 작게 유지하고 일시적 오류에는 재시도합니다. |
| MG-TX-02 | high | 멤버를 넘는 자기 쓰기 읽기(read-your-writes)에는 `"majority"` 읽기·쓰기 고려를 쓴 인과적 일관성 세션이 필요합니다. 기본 `"local"` 읽기 고려는 나중에 롤백되는 데이터를 반환할 수 있습니다. |
| MG-TX-03 | high | `w: "majority"`에 의존하는 복제본 세트에서는 아비터를 피합니다. 프라이머리-세컨더리-아비터 세트는 과반 쓰기를 위해 데이터 노드 둘이 모두 필요합니다. 데이터를 가진 멤버 셋을 씁니다. |
| MG-TX-04 | medium | 달성하지 못할 수 있는 쓰기 고려에는 `wtimeout`을 설정합니다. 없으면 쓰기가 무기한 막힐 수 있습니다. 긴 서버 작업은 낮은 `socketTimeoutMS`가 아니라 `maxTimeMS`로 제한합니다. |

## 5. 샤딩

| ID | Severity | Rule |
|---|---|---|
| MG-SH-01 | high | 샤드 키는 카디널리티, 빈도, 단조성으로 고릅니다. 카디널리티가 낮으면 청크 수가 제한되고, 지배적인 값은 점보 청크를 만들며, 단조 키(타임스탬프, ObjectId, 카운터)는 모든 삽입을 한 샤드로 보냅니다. 단조 키는 해시하고, 샤드 키를 흔한 쿼리 필터에 넣어 흩뿌리기-모으기(scatter-gather)를 피합니다. |
| MG-SH-02 | medium | 선택 전에 `analyzeShardKey`와 표본 쿼리로 후보를 측정합니다. 키를 바꿔야 하면 `reshardCollection`보다 `refineCollectionShardKey`(필드 추가)를 선호합니다. |
| MG-SH-03 | medium | 샤드 키 필드는 항상 씁니다. 그것이 없는 문서는 null 범위에 떨어져 숨은 핫스폿을 이룹니다. |

## 6. 연결과 변경 스트림

| ID | Severity | Rule |
|---|---|---|
| MG-CN-01 | high | 프로세스마다 `MongoClient` 하나를 만들어 재사용합니다. 서버리스 함수에서는 핸들러 밖에서 작은 `maxPoolSize`와 `minPoolSize` 0으로 만듭니다. 서버 연결 수는 풀 크기 × 멤버 수 × 애플리케이션 인스턴스 수로 늘어납니다. |
| MG-CN-02 | medium | 열린 변경 스트림마다 연결을 하나씩 잡습니다. 풀을 스트림 수보다 크게 잡고 재개 토큰을 저장하며 invalidate 이벤트를 처리합니다. 시계열 컬렉션은 변경 스트림을 지원하지 않습니다. |
| MG-OPS-01 | high | 연속 백업이나 스냅샷 백업(Atlas 백업, 모든 복제본 세트와 구성 서버의 파일 시스템 스냅샷, 작은 세트에는 `mongodump`)으로 백업하고, 별도 배포로 복구해 증명합니다(OP-02). 쓰기가 이어지는 샤딩 클러스터에서 `mongodump`만으로는 일관된 백업이 아닙니다. |

## 7. 검증 명령

```javascript
db.orders.find({ tenantId: t, status: "open" }).sort({ createdAt: -1 }).explain("executionStats")
db.orders.aggregate([{ $indexStats: {} }])
db.orders.aggregate([{ $project: { size: { $bsonSize: "$$ROOT" } } }, { $sort: { size: -1 } }, { $limit: 5 }])
db.currentOp({ "secs_running": { $gte: 5 } })
rs.status()   // replication lag and member health
```

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| 9.0 릴리스 날짜, 트랜잭션 상한, 작업당 메모리 제한 | <https://www.mongodb.com/docs/manual/release-notes/9.0/> |
| 8.0 라인과 패치 릴리스 | <https://www.mongodb.com/docs/manual/release-notes/8.0/> |
| 문서 크기, 중첩 깊이, 네임스페이스 제한 | <https://www.mongodb.com/docs/manual/reference/limits/> |
| 함께 접근하는 데이터를 함께 저장, 내장과 참조 판단 기준 | <https://www.mongodb.com/docs/manual/data-modeling/>, <https://www.mongodb.com/docs/manual/data-modeling/best-practices/> |
| 스키마 설계 패턴 | <https://www.mongodb.com/docs/manual/data-modeling/design-patterns/> |
| 스키마 검증 수준과 동작 | <https://www.mongodb.com/docs/manual/core/schema-validation/> |
| 쿼리당 인덱스 하나 | <https://www.mongodb.com/docs/manual/applications/indexes/> |
| ESR 지침, 범위 연산자, `$in` 임계값 | <https://www.mongodb.com/docs/manual/tutorial/equality-sort-range-guideline/> |
| 부분 인덱스 규칙 | <https://www.mongodb.com/docs/manual/core/index-partial/> |
| TTL 인덱스 동작 | <https://www.mongodb.com/docs/manual/core/index-ttl/> |
| explain 출력과 단계 | <https://www.mongodb.com/docs/manual/reference/explain-results/> |
| 쓰기 고려 기본값, 아비터, 8.0의 majority 변경 | <https://www.mongodb.com/docs/manual/reference/write-concern/> |
| 읽기 고려 기본값과 인과적 일관성 | <https://www.mongodb.com/docs/manual/reference/mongodb-defaults/> |
| 트랜잭션 제한과 운영 고려 사항 | <https://www.mongodb.com/docs/manual/core/transactions-production-consideration/> |
| 샤드 키 선택과 샤드 키 변경 | <https://www.mongodb.com/docs/manual/core/sharding-choose-a-shard-key/>, <https://www.mongodb.com/docs/manual/core/sharding-shard-key/> |
| 변경 스트림 요구 사항 | <https://www.mongodb.com/docs/manual/changestreams/> |
| 커넥션 풀 기본값과 시간 제한 | <https://www.mongodb.com/docs/manual/administration/connection-pool-overview/> |
| 규칙 ID와 심각도 | 이 패키지가 고른 설계이며 검증된 최적값이 아님 |
