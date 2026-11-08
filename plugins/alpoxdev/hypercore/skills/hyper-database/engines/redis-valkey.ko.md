# Redis와 Valkey

Redis와 Valkey(자체 호스팅, ElastiCache, MemoryDB, Upstash, Redis Cloud 등)를 위한 엔진 가이드이며, Memcached와 그 밖의 RESP 서버를 다루는 참고도 담습니다. `rules/engine-detection.md`가 이곳으로 라우팅한 뒤에 읽습니다. 둘 다 RESP로 통신하고 대부분의 명령을 공유하며, 아래 규칙은 둘이 갈라지는 곳을 표시합니다. 발견 사항은 `RV-*` ID를 인용합니다.

## 1. 날짜가 붙은 사실

> 자주 바뀝니다. 2026-11-07에 <https://redis.io/legal/licenses/>, <https://valkey.io/download/>, GitHub 릴리스 목록을 확인했습니다. 라이선스나 버전 결정 전에 다시 확인합니다.

| Fact | Value |
|---|---|
| 버전별 Redis 라이선스 | 7.2 이하: BSD-3-Clause. 7.4: RSALv2 또는 SSPLv1(둘 다 오픈 소스가 아님). 8.0 이상: 사용자가 RSALv2, SSPLv1, AGPLv3 중 선택 |
| Redis 8 패키징 | 쿼리 엔진(검색), JSON, 시계열, 확률적 타입이 같은 라이선스로 Redis Open Source 안에 포함되고 Redis와 함께 버전이 매겨집니다. 벡터 집합은 내장 타입입니다 |
| Redis 현재 버전 | 8.10.x 안정(8.10.3, 2026-10-26), 8.12는 릴리스 후보, 보안 패치는 8.8, 8.6, 8.4, 8.2, 7.4, 7.2 계열에도 제공 |
| Valkey | Linux Foundation 프로젝트, BSD-3-Clause, Redis 7.2.4에서 포크해 2024-03-28에 발표 |
| Valkey 현재 버전 | 지원 계열 9.1(9.1.3), 9.0(9.0.7), 8.1, 8.0, 7.2 모두 2026-10-26/27에 패치됨, 9.2는 릴리스 후보 |
| 매니지드 | ElastiCache는 Valkey, Redis OSS, Memcached 엔진을 제공하고, MemoryDB는 내구성을 갖춘 Multi-AZ 변형을 제공합니다 |

## 2. 역할

| ID | Severity | Rule |
|---|---|---|
| RV-ROL-01 | high | 설계가 그 내구성을 받아들이지 않는 한 Redis나 Valkey를 파생 저장소(캐시, 세션, 속도 제한, 큐, 리더보드)로 다룹니다. 기본 `appendfsync everysec`에서는 확인된 쓰기가 최대 약 1초까지 유실될 수 있고, RDB만 쓰면 수 분이 유실되며, 복제는 비동기입니다. 다시 만들 수 없는 데이터는 트랜잭션 원본 저장소에 둡니다(DM-50, DM-60). |
| RV-ROL-02 | medium | 코드가 대상으로 하는 서버와 버전을 밝힙니다. 명령 표면의 차이가 이식성을 깨뜨립니다. Redis 전용 내장 검색, JSON, 시계열, 확률적 타입, 벡터 집합, `DELEX`, `lrm` 축출 정책이 있고, Valkey 전용으로 클러스터 모드의 번호 있는 데이터베이스(9.0+), 원자적 슬롯 마이그레이션, `DELIFEQ`, `COMMANDLOG`가 있습니다. 해시 필드 만료(`HEXPIRE`)는 Redis 7.4+에 있지만 Valkey는 9.0+에만 있습니다. |
| RV-ROL-03 | medium | 기본값이 다릅니다. Valkey 9.0은 lazy-free 옵션(`lazyfree-lazy-eviction`, `-expire`, `-server-del`, `-user-del`, `-user-flush`)을 `yes`로 두고, Redis 8.10은 `no`로 둡니다. 공유 설정에서는 명시적으로 지정합니다. |
| RV-ROL-04 | low | Memcached에는 영속성, 복제, 자료 구조가 없습니다. 클라이언트 측 샤딩으로 다시 계산할 수 있는 블롭에만 고릅니다. 다른 RESP 서버를 도입하기 전에 라이선스를 확인합니다(Dragonfly의 소스 공개 라이선스는 무료 운영 사용을 제한합니다). |

## 3. 키와 자료 구조

| ID | Severity | Rule |
|---|---|---|
| RV-KEY-01 | medium | 키를 `<type>:<id>[:<field>]`로 이름 짓고 서비스나 환경 접두사를 붙입니다. 콜론은 관례일 뿐 네임스페이스가 아니므로 충돌은 애플리케이션의 몫입니다. 길이 제한 없는 사용자 입력을 키에 이어 붙이지 않고, 긴 식별자는 해시합니다. |
| RV-KEY-02 | high | 캐시 형태의 모든 키 계열은 TTL을 갖습니다. 한 계열의 키가 같은 순간에 많이 쓰여 함께 만료될 때는 지터를 줍니다(예: 기준값 곱하기 0.9에서 1.1). 키가 몇 개뿐이면 필요 없습니다. TTL이 없으면 `noeviction`은 `maxmemory`에서 쓰기를 실패시키고 `volatile-*` 정책은 아무것도 축출하지 못합니다. |
| RV-KEY-03 | high | 큰 키(수 메가바이트 값, 수백만 구성원 컬렉션)와 핫 키를 피합니다. 큰 키를 삭제, 만료, 마이그레이션하면 스레드가 막힙니다. `redis-cli --bigkeys`, `--memkeys`, `--keystats`(SCAN 기반, `-i`로 스로틀), `MEMORY USAGE key`, 명령별 통계로 찾고, 핫 키를 쪼개거나 로컬 캐시를 더합니다. |
| RV-KEY-04 | medium | 접근 형태로 구조를 고릅니다. 객체 필드에는 해시, 순위와 시간 순서 인덱스에는 정렬 집합, 소속 여부에는 집합, 소비자 그룹을 둔 내구성 이벤트 로그에는 스트림, 근사 고유 개수에는 HyperLogLog, ID별 플래그가 촘촘하면 비트맵, 반경 쿼리에는 geo입니다. |
| RV-KEY-05 | medium | 작은 컬렉션은 압축 인코딩 임계값(`hash-max-listpack-entries` 512와 `-value` 64, `set-max-intset-entries` 512, 정렬 집합 listpack 한도) 안에 둡니다. 넘으면 원소당 메모리가 대략 두 배가 됩니다. |
| RV-KEY-06 | high | 모든 스트림에 상한을 둡니다(`XADD key MAXLEN ~ n ...` 또는 `XTRIM`). 상한 없는 스트림은 메모리가 바닥날 때까지 자랍니다. |

## 4. 메모리, 축출, 영속성

| ID | Severity | Rule |
|---|---|---|
| RV-MEM-01 | critical | `maxmemory`를 컨테이너나 호스트 한도 아래로 명시하고, 여기에 계산되지 않는 복제 및 AOF 버퍼 몫을 남깁니다. 기본 `maxmemory 0`은 64비트 호스트에서 제한 없음을 뜻합니다. |
| RV-MEM-02 | high | 역할에 맞게 `maxmemory-policy`를 정합니다. 캐시에는 `allkeys-lru` 또는 `allkeys-lfu`, 사라지면 안 되는 데이터에만 `noeviction`(기본값)을 쓰고 한도 전에 경보를 겁니다. `volatile-ttl`은 TTL이 의미 있게 다를 때만 동작합니다. |
| RV-MEM-03 | medium | `INFO stats`의 `keyspace_hits / (keyspace_hits + keyspace_misses)`, `evicted_keys`, `expired_keys`로 정책을 판단합니다. |
| RV-PER-01 | high | 역할별로 영속성을 고릅니다. 순수 캐시는 없음(그리고 워밍업 계획), 중요한 데이터는 RDB에 `appendfsync everysec`를 쓴 AOF를 더합니다. `always`는 매우 느립니다. 기본값은 `save 3600 1 300 100 60 10000` 일정의 RDB 스냅샷과 `appendonly no`입니다. |
| RV-PER-02 | high | 라이브 서버에서 AOF를 켤 때는 `CONFIG SET appendonly yes`를 실행한 뒤 `CONFIG REWRITE`를 실행합니다. 아니면 다음 재시작에서 설정이 되돌아갑니다. |
| RV-PER-03 | medium | 포크 기반 저장에는 `vm.overcommit_memory = 1`과 투명 거대 페이지 비활성이 필요합니다. 포크 시간은 메모리 크기에 비례해 늘어나므로 `latest_fork_usec`를 지켜봅니다. |

## 5. 복제, Sentinel, 클러스터

| ID | Severity | Rule |
|---|---|---|
| RV-HA-01 | high | 복제는 비동기이므로 장애 조치 시 확인된 쓰기가 유실될 수 있습니다. `WAIT`는 장벽을 더하지만 선형화 가능성을 주지는 않습니다. |
| RV-HA-02 | high | Sentinel은 독립적으로 장애가 나는 호스트에 최소 세 인스턴스가 필요하고, 설정 파일에 쓸 수 있어야 합니다. Sentinel 두 개는 문서화된 안티패턴입니다. |
| RV-HA-03 | high | 클러스터 모드는 해시 슬롯 16384개(`CRC16(key) mod 16384`)를 씁니다. 슬롯을 넘는 다중 키 명령, 트랜잭션, 스크립트는 `CROSSSLOT`으로 실패합니다. 관련 키를 해시 태그로 묶되(`order:{42}:items`), 한 슬롯이 뜨거워질 만큼 넓게 태그하지 않습니다. |
| RV-HA-04 | medium | 운영 클러스터는 복제본을 하나씩 둔 프라이머리를 최소 세 개 돌립니다. 클러스터 버스 포트(기본적으로 클라이언트 포트 + 10000)는 노드 사이에서만 닿아야 하고 다른 곳에서는 닿지 않아야 합니다. |
| RV-HA-05 | medium | Redis Cluster는 데이터베이스 0만 지원합니다. 코드가 의도적으로 Valkey 9.0+의 번호 있는 데이터베이스를 대상으로 하지 않는 한 테넌트 격리는 키 접두사나 별도 클러스터로 유지합니다. |
| RV-HA-06 | medium | 복제본 읽기는 오래된 값입니다. 이를 감당하는 읽기만 그곳으로 라우팅합니다. |

## 6. 원자성과 명령

| ID | Severity | Rule |
|---|---|---|
| RV-CMD-01 | critical | 운영 경로에서 `KEYS`, `FLUSHALL`, `FLUSHDB`, `DEBUG`, 큰 키의 컬렉션 전체 읽기(`SMEMBERS`, `HGETALL`, `LRANGE 0 -1`)를 실행하지 않습니다. `SCAN`, `SSCAN`, `HSCAN`, `ZSCAN`을 멱등 소비자와 함께 씁니다(`SCAN`은 중복을 반환할 수 있습니다). |
| RV-CMD-02 | high | `MULTI`/`EXEC`는 원자적이지만 롤백이 없습니다. 낙관적 동시성에는 `WATCH`를, 읽기-수정-쓰기에는 Lua 스크립트나 함수를 씁니다. 스크립트는 서버를 막으므로 짧게 유지하고 키를 선언합니다. |
| RV-CMD-03 | high | 속도 제한과 카운터는 값과 만료를 원자적으로 설정합니다(`SET key 0 EX n NX` 후 `INCR`, 또는 스크립트 하나). `INCR`과 `EXPIRE`를 따로 실행하면 영원히 만료되지 않는 카운터가 남을 수 있습니다. |
| RV-CMD-04 | high | cache-aside 쓰기는 원본을 먼저 갱신한 뒤 캐시 키를 삭제합니다. 짧은 잠금(`SET lock:k <token> NX PX ms`), 이른 확률적 갱신, 한 호출자가 다시 계산하는 동안 오래된 값을 내주기로 몰림(stampede)을 막습니다. |
| RV-CMD-05 | high | 단일 인스턴스 잠금은 `SET key <random-token> NX PX <ms>`이고 소유자만 해제합니다(Redis 8.4+는 `DELEX key IFEQ token`, Valkey 9.0+는 `DELIFEQ`, 그 밖에는 비교 후 삭제 스크립트). Redlock은 펜싱 토큰을 주지 않습니다. 잠금이 정합성을 지키는 자리라면 저장 계층에서 펜싱 토큰을 강제합니다. |
| RV-CMD-06 | medium | Pub/Sub은 최대 한 번 전달입니다. 메시지를 잃으면 안 될 때는 소비자 그룹을 둔 스트림(`XREADGROUP`, `XACK`, 막힌 항목에는 `XAUTOCLAIM`)을 씁니다. 클러스터 모드에서는 샤딩된 Pub/Sub을 씁니다. |
| RV-CMD-07 | medium | 독립 명령은 파이프라인으로 묶어 왕복을 줄입니다. 블로킹 명령(`BLPOP`, `XREAD BLOCK`)은 각각 연결을 붙잡으므로 이들을 위해 풀 크기를 정합니다. |
| RV-CMD-08 | high | 요청마다 연결을 새로 열지 말고 프로세스마다 풀이나 다중화(multiplexed) 클라이언트를 재사용합니다. 다른 호출자와 공유하는 다중화 연결로 블로킹 명령을 보내지 않고, 연결 시간 제한은 명령 시간 제한보다 짧게 둡니다. |

## 7. 보안

| ID | Severity | Rule |
|---|---|---|
| RV-SEC-01 | critical | 포트를 신뢰할 수 없는 네트워크에 노출하지 않습니다. 사설 인터페이스에 바인드하고, `protected-mode yes`를 유지하며, 인증을 요구합니다. |
| RV-SEC-02 | high | 최소 권한의 ACL 사용자를 씁니다(`ACL SETUSER app on >secret ~app:* +@read +@write -@dangerous`). `requirepass`는 모든 권한을 가진 `default` 사용자만 보호하고, `rename-command`는 ACL로 대체되어 폐기 예정입니다. `+@all`은 앞으로 추가될 모듈 명령에도 권한을 줍니다. |
| RV-SEC-03 | high | 클라이언트, 복제, 클러스터 버스에 TLS를 켭니다. 클러스터 버스는 자체 인증이 없으므로 네트워크 계층에서 제한합니다. |
| RV-SEC-04 | medium | 서버를 권한 없는 사용자로 실행하고, 애플리케이션 자격 증명에서 `CONFIG`, `MODULE`, `DEBUG`, `SHUTDOWN`을 멀리 둡니다. |

## 8. 검증 명령

```bash
redis-cli --latency            # client-observed latency
redis-cli --intrinsic-latency 100   # run on the server host: platform stall floor
redis-cli --bigkeys -i 0.01    # largest keys by element count, throttled
redis-cli INFO memory          # used_memory, maxmemory, mem_fragmentation_ratio
redis-cli CONFIG GET 'maxmemory*'   # limit and eviction policy; on managed services read the parameter group instead
redis-cli INFO stats           # keyspace_hits, keyspace_misses, evicted_keys
redis-cli SLOWLOG GET 32
redis-cli LATENCY DOCTOR
```

`valkey-cli`도 같은 옵션을 받습니다. 이 명령은 일회용이거나 사용자가 명시적으로 제공한 인스턴스에만 실행합니다(`rules/database-workflow.md` §4).

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| Redis 라이선스 이력과 Redis 8의 삼중 라이선스 및 포함 구성 요소 | <https://redis.io/legal/licenses/> |
| Valkey가 7.2.4에서 BSD-3-Clause로 포크되어 2024-03-28에 발표됨 | <https://www.linuxfoundation.org/press/linux-foundation-launches-open-source-valkey-community> |
| Valkey 지원 계열과 릴리스 날짜 | <https://valkey.io/download/> |
| Redis 릴리스 계열과 날짜 | <https://github.com/redis/redis/releases> |
| Valkey 9.0의 클러스터 모드 번호 있는 데이터베이스, 원자적 슬롯 마이그레이션, 해시 필드 만료 | <https://valkey.io/blog/introducing-valkey-9/> |
| 해시 슬롯, 해시 태그, `CROSSSLOT`, Redis Cluster의 데이터베이스 0 전용 | <https://redis.io/docs/latest/operate/oss_and_stack/reference/cluster-spec/> |
| 클러스터 버스 포트와 최소 클러스터 형태 | <https://valkey.io/topics/cluster-tutorial/> |
| 축출 정책, `maxmemory` 기본값, 적중률 진단 | <https://redis.io/docs/latest/develop/reference/eviction/>, <https://valkey.io/topics/lru-cache/> |
| 영속성 옵션, `appendfsync`, 라이브에서 AOF로 전환 | <https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/> |
| 서버별 lazy-free 기본값 | <https://raw.githubusercontent.com/valkey-io/valkey/9.0/valkey.conf>, <https://raw.githubusercontent.com/redis/redis/8.10/redis.conf> |
| 키 이름 규칙과 크기 지침 | <https://redis.io/docs/latest/develop/using-commands/keyspace/> |
| 큰 키 스캔 옵션 | <https://redis.io/docs/latest/develop/tools/cli/> |
| Pub/Sub의 최대 한 번 전달 | <https://redis.io/docs/latest/develop/pubsub/> |
| 잠금 획득·해제 패턴, `DELEX` | <https://redis.io/docs/latest/develop/clients/patterns/distributed-locks/> |
| Redlock의 펜싱 토큰 부재와 타이밍 가정 | <https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html> |
| 보안 모델, protected mode, `rename-command` 대신 ACL, TLS | <https://redis.io/docs/latest/operate/oss_and_stack/management/security/>, <https://redis.io/docs/latest/operate/oss_and_stack/management/security/acl/> |
| 지연 시간 진단, 포크 비용, 투명 거대 페이지 | <https://redis.io/docs/latest/operate/oss_and_stack/management/optimization/latency/> |
| ElastiCache 엔진 | <https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/WhatIs.html> |
| 규칙 ID와 심각도 | 이 패키지가 고른 설계이며 검증된 최적값이 아님 |
