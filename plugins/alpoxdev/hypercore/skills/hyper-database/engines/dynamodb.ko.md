# Amazon DynamoDB

Amazon DynamoDB 엔진 가이드이며 글로벌 테이블을 포함합니다. `rules/engine-detection.md`가 이곳으로 라우팅한 뒤 읽습니다. `rules/data-modeling.md` §1의 접근 패턴 표가 설계 입력입니다. DynamoDB에는 기댈 임의 질의 플래너가 없습니다. 발견 사항은 `DY-*` ID를 인용합니다.

## 1. 날짜가 붙은 사실

> 자주 바뀝니다. 2026-11-07에 DynamoDB 할당량과 제약 페이지에서 확인했습니다. 설계가 어떤 수치에 달려 있으면 다시 확인합니다.

| Fact | Value |
|---|---|
| 항목 크기 | 속성 이름을 포함해 400 KB |
| 파티션당 상한 | 초당 읽기 단위 3,000과 쓰기 단위 1,000 |
| 용량 단위 | 1 RCU = 4 KB까지의 강한 일관성 읽기 초당 한 번(최종 일관성은 두 번); 1 WCU = 1 KB까지의 쓰기 초당 한 번 |
| 인덱스 | 테이블당 로컬 보조 인덱스 5개(나중에 삭제 불가); 기본으로 테이블당 전역 보조 인덱스 20개; 벡터 인덱스도 GSI 할당량에 포함됨 |
| 항목 컬렉션 | LSI가 있는 테이블은 파티션 키 값마다 10 GB로 제한됨 |
| 트랜잭션 | 트랜잭션당 유일 항목 100개와 4 MB까지; 항목마다 prepare와 commit 비용이 듦 |
| 배치 | `BatchGetItem`은 항목 100개까지, `BatchWriteItem`은 put이나 delete 25개까지. 둘 다 일부만 성공할 수 있음 |
| 기본 용량 모드 | 온디맨드 |

## 2. 테이블 설계

| ID | Severity | Rule |
|---|---|---|
| DY-MOD-01 | critical | 테이블을 만들기 전에 모든 접근 패턴(키 조건, 정렬, 필터, 페이지 크기, 속도)을 나열합니다. 각 패턴은 `GetItem`, 테이블에 대한 `Query`, 인덱스에 대한 `Query` 중 하나로 대응됩니다. `Scan`으로만 처리되는 패턴은 설계 결함입니다. |
| DY-MOD-02 | high | 접근 패턴이 허용하는 만큼 테이블을 적게 두고 관련 항목을 파티션 키 하나 아래에 저장해 `Query` 하나로 반환되게 합니다(단일 테이블 또는 소수 테이블 설계). 대량 시계열, 크게 다른 접근 패턴, 다른 운영 요구(백업, 보존, 권한)에는 별도 테이블이 정당합니다. |
| DY-MOD-03 | high | 여러 엔티티 타입이 테이블 하나를 공유하면 일반 키 이름(`PK`, `SK`)에 타입 접두사를 붙이고(`USER#123`, `ORDER#2026-11-07#456`), 키 스키마를 접근 패턴 표 옆에 적습니다. |
| DY-MOD-04 | medium | 계층 정렬 키(`COUNTRY#KR#CITY#SEOUL`)를 써서 `begins_with`와 `between`으로 어느 수준에서든 조회하고, 버전이 중요하면 이력 항목 옆에 최신 버전용 `v0` 항목을 둡니다. |
| DY-MOD-05 | high | 항목을 400 KB보다 훨씬 작게 유지합니다. 큰 부분은 같은 컬렉션의 별도 항목으로 나누거나, 압축하거나, 오브젝트를 S3에 두고 키만 저장합니다(저장소를 넘는 트랜잭션이 없으므로 고아 정리가 필요함). |
| DY-MOD-06 | medium | 단일 테이블 설계는 유연성과 분석을 희생합니다. 스캔 대신 분석 저장소로 내보내고, 새 접근 패턴에 새 키 형태가 필요하면 백필을 계획합니다. |

## 3. 파티션 키와 처리량

| ID | Severity | Rule |
|---|---|---|
| DY-PK-01 | critical | 카디널리티가 높고 트래픽이 고른 파티션 키를 고릅니다(사용자, 기기, 테넌트가 많은 테넌트). 상태값, 모든 쓰기를 받는 날짜 버킷, 단일 유명 엔티티는 절대 쓰지 않습니다. |
| DY-PK-02 | high | 항목당 계산을 합니다. 읽기는 4 KB, 쓰기는 1 KB로 올림한 항목 크기에 요청 속도를 곱해 파티션당 상한과 비교합니다. 20 KB 항목을 강한 일관성으로 읽으면 5 RCU이므로 키 하나는 초당 약 600회 강한 읽기에서 한계에 닿습니다. |
| DY-PK-03 | high | 뜨거운 쓰기 키는 접미사로 샤딩하고(무작위, 또는 단일 항목 읽기가 계속 동작하도록 알려진 속성에서 계산), 읽을 때 샤드를 합칩니다. |
| DY-PK-04 | medium | 적응형 용량과 버스트 용량은 짧은 급증을 누그러뜨리지만 파티션당 상한을 올리지 못하고, LSI가 있는 테이블에서는 적응형 용량이 항목 컬렉션을 나눌 수 없습니다. |
| DY-PK-05 | medium | 대량 적재 시 한 키의 항목을 한꺼번에 쓰지 말고 파티션 키를 번갈아 씁니다. |

## 4. 인덱스

| ID | Severity | Rule |
|---|---|---|
| DY-IX-01 | high | 기본은 GSI입니다. 같은 파티션 안의 강한 일관성 대체 정렬이 필요하고 10 GB 항목 컬렉션 상한을 받아들일 수 있을 때만 LSI를 만듭니다. LSI는 테이블과 함께 만들 수만 있고 절대 제거할 수 없습니다. |
| DY-IX-02 | medium | 인덱스의 쿼리가 반환하는 속성만 투영합니다. `ALL`은 저장과 쓰기 비용을 거의 두 배로 만듭니다. 투영된 비키 속성은 인덱스 전체에서 할당량 100개를 공유합니다. |
| DY-IX-03 | medium | 희소 인덱스(인덱스 키 속성을 노출할 항목에만 씀)를 써서 필터 없이 부분집합을 조회합니다. |
| DY-IX-04 | high | 쓰기 용량이 부족한 GSI는 기본 테이블 쓰기를 제한합니다. GSI 용량을 테이블과 함께 잡고 그 제한 지표를 감시합니다. GSI는 최종 일관성입니다. |

## 5. 읽기, 쓰기, 트랜잭션

| ID | Severity | Rule |
|---|---|---|
| DY-RW-01 | high | `Query`, `Limit`, `ExclusiveStartKey`로 페이지를 나눕니다. 필터 표현식은 읽은 뒤에 실행되고 읽은 모든 항목의 용량을 그대로 소모합니다. |
| DY-RW-02 | high | `Scan`은 내보내기와 유지보수에만 쓰고 작은 `Limit`과 별도 용량 예산을 둡니다. 스캔 페이지 하나가 파티션 하나의 용량을 급격히 소모할 수 있습니다. |
| DY-RW-03 | high | 낙관적 잠금과 유일성에는 조건부 쓰기(버전 속성을 쓴 `ConditionExpression`)를 씁니다. 항목 하나에 대한 `UpdateItem`은 이미 원자적입니다. |
| DY-RW-04 | high | `TransactWriteItems`는 실제 다중 항목 불변 조건에만 씁니다. 용량이 두 배가 되고, 취소된 트랜잭션도 용량을 소모하며, 스트림 소비자는 항목을 따로 봅니다. 멱등 재시도에는 `ClientRequestToken`을 씁니다. |
| DY-RW-05 | high | 배치 호출의 `UnprocessedItems`와 `UnprocessedKeys`는 지수 백오프로 재시도합니다. |
| DY-RW-06 | medium | 글로벌 테이블은 마지막 쓰기 승리로 충돌을 해결합니다. 낙관적 잠금은 리전을 넘어 성립하지 않고 트랜잭션은 복제본 사이에서 원자적이지 않습니다. 충돌이 중요하면 한 항목의 쓰기를 한 리전으로 보냅니다. |

## 6. TTL, 스트림, 운영

| ID | Severity | Rule |
|---|---|---|
| DY-OP-01 | medium | TTL 속성은 Unix 에포크 초 단위 숫자입니다. 삭제는 만료 시점이 아니라 며칠 안에 일어나므로 읽기에서 만료된 항목을 걸러냅니다. |
| DY-OP-02 | medium | 스트림은 레코드를 24시간 보관하고 항목별로만 순서를 보장합니다. 소비자는 멱등하게 만들고, 스트림을 다시 만들지 않고는 뷰 타입을 바꿀 수 없습니다. |
| DY-OP-03 | high | 다시 만들 수 없는 데이터를 담은 테이블에는 특정 시점 복구를 켜고, 새 테이블로 복구 시험을 합니다. |
| DY-OP-04 | medium | 알 수 없거나 몰아치는 트래픽에는 온디맨드를, 꾸준한 트래픽에는 자동 확장을 붙인 프로비저닝을 고릅니다. 온디맨드로의 전환은 하루 전환 횟수가 제한됩니다. |
| DY-OP-05 | medium | `ReturnConsumedCapacity`, CloudWatch 제한 지표, 핫 키용 Contributor Insights로 근거를 모읍니다. |

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| 인덱스 할당량, 벡터 인덱스 할당량, 투영 속성 할당량, 기본 처리량 할당량 | <https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/ServiceQuotas.html> |
| 항목 크기, 용량 단위 크기, 배치와 트랜잭션 제한, 키 길이, 모드 전환 | <https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Constraints.html> |
| 접근 패턴 우선 설계와 소수 테이블 | <https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-general-nosql-design.html>, <https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-table-design.html> |
| 파티션당 상한과 20 KB 항목 예시 | <https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-partition-key-design.html> |
| 쓰기 샤딩 | <https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-partition-key-sharding.html> |
| 정렬 키 계층과 버전 항목 | <https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-sort-keys.html> |
| LSI의 영구성, 10 GB 항목 컬렉션 상한, 투영 | <https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-indexes-general.html> |
| 쿼리와 스캔 | <https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-query-scan.html> |
| 트랜잭션 비용, 취소, 멱등 토큰, 격리 | <https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/transaction-apis.html> |
| 낙관적 잠금과 글로벌 테이블 충돌 해결 | <https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/BestPractices_ImplementingVersionControl.html> |
| 버스트와 적응형 용량 | <https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/burst-adaptive-capacity.html> |
| 스트림 보존과 순서 | <https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Streams.html> |
| TTL 형식과 삭제 시점 | <https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/TTL.html> |
| 용량 모드 | <https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/capacity-mode.html> |
| 규칙 ID와 심각도 | 이 패키지가 고른 설계이며 검증된 최적값이 아님 |
