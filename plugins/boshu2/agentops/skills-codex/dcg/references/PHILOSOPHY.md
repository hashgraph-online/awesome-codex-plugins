# DCG Philosophy

## The Core Asymmetry

```
Execute "rm -rf /":  0.001 seconds
Recover from it:     impossible
```

DCG exists because the cost of a false negative (destructive command runs) far exceeds the cost of a false positive (safe command blocked for 30 seconds).

## Mechanical Enforcement vs Instructions

```
AGENTS.md says "don't run destructive commands"  →  Agent might ignore
DCG blocks destructive commands before execution →  Physically impossible to run
```

Instructions in AGENTS.md are suggestions. DCG is enforcement. This is the key differentiator.

## Why Pre-Execution Blocking

```
Your Decision → DCG Hook → Shell → Kernel
                   ↑
            Intercept HERE
```

- No partial execution
- No cleanup needed
- Clear audit trail

Alternatives (backups, permissions, monitoring) all act too late.

## Human Context You Lack

When blocked, you're being told "get human confirmation" because they know:
- Production vs test environment
- Whether uncommitted changes matter
- Who else is working on this branch
- Actual blast radius

## Why Patterns, Not AI

| Property | Pattern Matching |
|----------|------------------|
| Speed | <2ms |
| Determinism | Same input → same result |
| Auditability | Exact pattern visible |
| Predictability | No model variance |

## Allow-Once Codes

```
ALLOW-24H CODE: [12345]
```

- Cryptographically bound to exact command + directory
- Time-limited, single-use, logged
- Human explicitly accepts responsibility

## Why Never Circumvent

1. Your context may be incomplete
2. Human loses visibility
3. Erodes trust in all your actions

Correct response: explain why you think it's safe, let human decide.

## Design Principles

| Principle | Meaning |
|-----------|---------|
| Fail-closed on match | Pattern hits → block |
| Fail-open on error | DCG breaks → allow |
| Fail-open on timeout | >200ms → allow + warning |
| Fast safe path | Most commands <1ms |
| Human override | Never permanent, just confirmed |

## Performance Contract

**Latency Tiers:**
| Tier | Stage | Target | Panic Threshold |
|------|-------|--------|-----------------|
| 0 | Quick Reject | <1μs | >50μs |
| 1 | Normalization | <5μs | >100μs |
| 2 | Safe Pattern Check | <50μs | >500μs |
| 3 | Destructive Pattern Check | <50μs | >500μs |
| 4 | Heredoc Extraction | <1ms | >20ms |
| 5 | Heredoc Evaluation | <2ms | >30ms |
| 6 | Full Pipeline | <5ms | >50ms |

**Absolute Max:** 200ms (fail-open threshold)

**SIMD Optimizations:**
- `memchr` crate for fast substring search
- `Aho-Corasick` for multi-pattern keyword matching
- `LazyLock` for one-time pattern compilation
- `SmallVec` for stack-allocated collections

DCG will never significantly slow your workflow. If something goes wrong, commands run (with warnings logged).

You can always run `dcg explain "command"` to see exactly why something was blocked.

DCG makes you more useful: humans trust you more when safety rails exist.
