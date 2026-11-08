# Redis and Valkey

Engine guide for Redis and Valkey (self-hosted, ElastiCache, MemoryDB, Upstash, Redis Cloud, and others), with notes on Memcached and other RESP servers. Read it after `rules/engine-detection.md` routes here. Both speak RESP and share most commands; the rules below mark where they diverge. Findings cite the `RV-*` IDs.

## 1. Dated Facts

> Volatile. Checked 2026-11-07 against <https://redis.io/legal/licenses/>, <https://valkey.io/download/>, and the GitHub release lists; recheck before a license or version decision.

| Fact | Value |
|---|---|
| Redis license by version | 7.2 and earlier: BSD-3-Clause. 7.4: RSALv2 or SSPLv1 (neither is open source). 8.0 and later: RSALv2, SSPLv1, or AGPLv3 at the user's choice |
| Redis 8 packaging | Query engine (search), JSON, time series, and probabilistic types ship inside Redis Open Source under the same license, versioned with Redis; vector sets are a built-in type |
| Redis current | 8.10.x stable (8.10.3, 2026-10-26); 8.12 at release candidate; security patches also on 8.8, 8.6, 8.4, 8.2, 7.4, 7.2 lines |
| Valkey | Linux Foundation project, BSD-3-Clause, forked from Redis 7.2.4 and announced 2024-03-28 |
| Valkey current | Supported lines 9.1 (9.1.3), 9.0 (9.0.7), 8.1, 8.0, 7.2, all patched 2026-10-26/27; 9.2 at release candidate |
| Managed | ElastiCache offers Valkey, Redis OSS, and Memcached engines; MemoryDB offers a durable Multi-AZ variant |

## 2. Role

| ID | Severity | Rule |
|---|---|---|
| RV-ROL-01 | high | Treat Redis or Valkey as a derived store (cache, session, rate limit, queue, leaderboard) unless the design accepts its durability: with default `appendfsync everysec` up to about a second of acknowledged writes can be lost, RDB-only loses minutes, and replication is asynchronous. Keep data you cannot rebuild in a transactional system of record (DM-50, DM-60). |
| RV-ROL-02 | medium | State which server and version the code targets. Command-surface differences break portability: Redis-only built-in search, JSON, time series, probabilistic types, vector sets, `DELEX`, and `lrm` eviction policies; Valkey-only numbered databases in cluster mode (9.0+), atomic slot migration, `DELIFEQ`, and `COMMANDLOG`. Hash-field expiration (`HEXPIRE`) exists in Redis 7.4+ but only Valkey 9.0+. |
| RV-ROL-03 | medium | Defaults differ: Valkey 9.0 ships the lazy-free options (`lazyfree-lazy-eviction`, `-expire`, `-server-del`, `-user-del`, `-user-flush`) set to `yes`, Redis 8.10 ships them `no`. Set them explicitly in shared configuration. |
| RV-ROL-04 | low | Memcached has no persistence, replication, or data structures; choose it only for recomputable blobs with client-side sharding. Check the license of other RESP servers before adopting them (Dragonfly's source-available license caps free production use). |

## 3. Keys and Data Structures

| ID | Severity | Rule |
|---|---|---|
| RV-KEY-01 | medium | Name keys `<type>:<id>[:<field>]` with a service or environment prefix; colons are a convention, not a namespace, so collisions are the application's problem. Never concatenate unbounded user input into keys; hash long identifiers. |
| RV-KEY-02 | high | Every cache-shaped key family has a TTL. Add jitter (for example base times 0.9 to 1.1) when many keys of a family are written at the same moment and would expire together; a handful of keys does not need it. Without TTLs, `noeviction` fails writes at `maxmemory` and `volatile-*` policies cannot evict anything. |
| RV-KEY-03 | high | Avoid big keys (multi-megabyte values, collections with millions of members) and hot keys; deleting, expiring, or migrating a big key blocks the thread. Find them with `redis-cli --bigkeys`, `--memkeys`, or `--keystats` (SCAN-based, throttle with `-i`), `MEMORY USAGE key`, and per-command stats; split hot keys or add a local cache. |
| RV-KEY-04 | medium | Choose the structure by access shape: hash for an object's fields, sorted set for rankings and time-ordered indexes, set for membership, stream for durable event logs with consumer groups, HyperLogLog for approximate distinct counts, bitmap for dense per-ID flags, geo for radius queries. |
| RV-KEY-05 | medium | Keep small collections within the compact encoding thresholds (`hash-max-listpack-entries` 512 and `-value` 64, `set-max-intset-entries` 512, and the sorted-set listpack limits); crossing them roughly doubles memory per element. |
| RV-KEY-06 | high | Cap every stream (`XADD key MAXLEN ~ n ...` or `XTRIM`); unbounded streams grow until memory runs out. |

## 4. Memory, Eviction, Persistence

| ID | Severity | Rule |
|---|---|---|
| RV-MEM-01 | critical | Set `maxmemory` explicitly below the container or host limit with headroom for replication and AOF buffers, which are not counted against it; the default `maxmemory 0` means no limit on 64-bit hosts. |
| RV-MEM-02 | high | Set `maxmemory-policy` for the role: `allkeys-lru` or `allkeys-lfu` for caches; `noeviction` (the default) only for data that must not disappear, with alerts before the limit. `volatile-ttl` works only when TTLs differ meaningfully. |
| RV-MEM-03 | medium | Judge the policy by `keyspace_hits / (keyspace_hits + keyspace_misses)`, `evicted_keys`, and `expired_keys` from `INFO stats`. |
| RV-PER-01 | high | Pick persistence per role: none for pure caches (and plan a warm-up), RDB plus AOF with `appendfsync everysec` for data that matters; `always` is very slow. Defaults are RDB snapshots on the `save 3600 1 300 100 60 10000` schedule and `appendonly no`. |
| RV-PER-02 | high | When enabling AOF on a live server, run `CONFIG SET appendonly yes` and then `CONFIG REWRITE`, or the next restart reverts the setting. |
| RV-PER-03 | medium | Fork-based saves need `vm.overcommit_memory = 1` and transparent huge pages off; watch `latest_fork_usec` because fork time grows with memory size. |

## 5. Replication, Sentinel, Cluster

| ID | Severity | Rule |
|---|---|---|
| RV-HA-01 | high | Replication is asynchronous; acknowledged writes can be lost on failover. `WAIT` adds a barrier but not linearizability. |
| RV-HA-02 | high | Sentinel needs at least three instances on independently failing hosts, with a writable configuration file; two Sentinels is a documented anti-pattern. |
| RV-HA-03 | high | Cluster mode has 16384 hash slots (`CRC16(key) mod 16384`). Multi-key commands, transactions, and scripts across slots fail with `CROSSSLOT`; group related keys with a hash tag (`order:{42}:items`) but do not tag so broadly that one slot becomes hot. |
| RV-HA-04 | medium | Production clusters run at least three primaries with a replica each; the cluster bus port (client port plus 10000 by default) must be reachable between nodes and nowhere else. |
| RV-HA-05 | medium | Redis Cluster supports only database 0; keep tenant isolation in key prefixes or separate clusters unless the code targets Valkey 9.0+ numbered databases on purpose. |
| RV-HA-06 | medium | Replica reads are stale; route only tolerant reads there. |

## 6. Atomicity and Commands

| ID | Severity | Rule |
|---|---|---|
| RV-CMD-01 | critical | Never run `KEYS`, `FLUSHALL`, `FLUSHDB`, `DEBUG`, or whole-collection reads of large keys (`SMEMBERS`, `HGETALL`, `LRANGE 0 -1`) on production paths; use `SCAN`, `SSCAN`, `HSCAN`, `ZSCAN` with idempotent consumers (`SCAN` can return duplicates). |
| RV-CMD-02 | high | `MULTI`/`EXEC` is atomic but has no rollback; use `WATCH` for optimistic concurrency, or a Lua script or function for read-modify-write. Scripts block the server; keep them short and declare their keys. |
| RV-CMD-03 | high | Rate limits and counters set the value and its expiry atomically (`SET key 0 EX n NX` then `INCR`, or one script); a separate `INCR` then `EXPIRE` can leave a counter that never expires. |
| RV-CMD-04 | high | Cache-aside writes update the source first, then delete the cache key; prevent stampedes with a short lock (`SET lock:k <token> NX PX ms`), early probabilistic refresh, or serving stale data while one caller recomputes. |
| RV-CMD-05 | high | A single-instance lock is `SET key <random-token> NX PX <ms>` and is released only by its owner (`DELEX key IFEQ token` on Redis 8.4+, `DELIFEQ` on Valkey 9.0+, otherwise a compare-and-delete script). Redlock gives no fencing token: when the lock guards correctness, enforce a fencing token in the storage layer. |
| RV-CMD-06 | medium | Pub/Sub is at-most-once; use streams with consumer groups (`XREADGROUP`, `XACK`, `XAUTOCLAIM` for stuck entries) when messages must not be lost. In cluster mode use sharded Pub/Sub. |
| RV-CMD-07 | medium | Pipeline batches of independent commands to cut round trips; blocking commands (`BLPOP`, `XREAD BLOCK`) each hold a connection, so size pools for them. |
| RV-CMD-08 | high | Reuse a pooled or multiplexed client per process instead of opening a connection per request; never send blocking commands over a multiplexed connection shared by other callers, and give the connect timeout a shorter value than the command timeout. |

## 7. Security

| ID | Severity | Rule |
|---|---|---|
| RV-SEC-01 | critical | Never expose the port to an untrusted network: bind to private interfaces, keep `protected-mode yes`, and require authentication. |
| RV-SEC-02 | high | Use ACL users with least privilege (`ACL SETUSER app on >secret ~app:* +@read +@write -@dangerous`); `requirepass` only protects the all-powerful `default` user, and `rename-command` is deprecated in favor of ACLs. `+@all` also grants future module commands. |
| RV-SEC-03 | high | Enable TLS for clients, replication, and the cluster bus; the cluster bus has no authentication of its own, so restrict it at the network layer. |
| RV-SEC-04 | medium | Run the server as an unprivileged user, and keep `CONFIG`, `MODULE`, `DEBUG`, and `SHUTDOWN` away from application credentials. |

## 8. Verification Commands

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

`valkey-cli` accepts the same options. Run these against a disposable or explicitly provided instance only (`rules/database-workflow.md` §4).

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| Redis license history and the Redis 8 tri-license and bundled components | <https://redis.io/legal/licenses/> |
| Valkey fork from 7.2.4 under BSD-3-Clause, announced 2024-03-28 | <https://www.linuxfoundation.org/press/linux-foundation-launches-open-source-valkey-community> |
| Valkey supported lines and release dates | <https://valkey.io/download/> |
| Redis release lines and dates | <https://github.com/redis/redis/releases> |
| Valkey 9.0 numbered databases in cluster mode, atomic slot migration, and hash-field expiration | <https://valkey.io/blog/introducing-valkey-9/> |
| Hash slots, hash tags, `CROSSSLOT`, database 0 only in Redis Cluster | <https://redis.io/docs/latest/operate/oss_and_stack/reference/cluster-spec/> |
| Cluster bus port and minimum cluster shape | <https://valkey.io/topics/cluster-tutorial/> |
| Eviction policies, `maxmemory` defaults, and hit-ratio diagnosis | <https://redis.io/docs/latest/develop/reference/eviction/>, <https://valkey.io/topics/lru-cache/> |
| Persistence options, `appendfsync`, and switching to AOF live | <https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/> |
| Lazy-free defaults per server | <https://raw.githubusercontent.com/valkey-io/valkey/9.0/valkey.conf>, <https://raw.githubusercontent.com/redis/redis/8.10/redis.conf> |
| Key naming and size guidance | <https://redis.io/docs/latest/develop/using-commands/keyspace/> |
| Big-key scanning options | <https://redis.io/docs/latest/develop/tools/cli/> |
| Pub/Sub at-most-once delivery | <https://redis.io/docs/latest/develop/pubsub/> |
| Lock acquire and release pattern, `DELEX` | <https://redis.io/docs/latest/develop/clients/patterns/distributed-locks/> |
| Redlock's lack of fencing tokens and timing assumptions | <https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html> |
| Security model, protected mode, ACLs over `rename-command`, TLS | <https://redis.io/docs/latest/operate/oss_and_stack/management/security/>, <https://redis.io/docs/latest/operate/oss_and_stack/management/security/acl/> |
| Latency diagnosis, fork cost, and transparent huge pages | <https://redis.io/docs/latest/operate/oss_and_stack/management/optimization/latency/> |
| ElastiCache engines | <https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/WhatIs.html> |
| The rule IDs and severities | this package's chosen design, not a validated optimum |
