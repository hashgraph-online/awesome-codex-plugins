# Complexity Scaling

Automatic complexity detection determines the level of validation ceremony applied to each RPI cycle.

## Classification Table

| Level | Issue Count | Wave Count | Ceremony |
|-------|------------|------------|----------|
| **low** | ≤2 | 1 | fast-path: `--quick` on pre-mortem, vibe, post-mortem |
| **medium** | 3-6 | 1-2 | lean: `--quick` on pre-mortem, vibe, post-mortem (same as low — inline review is sufficient for most work) |
| **high** | 7+ OR 3+ waves | any | thorough: full council on pre-mortem and vibe, standard post-mortem |

> **Design rationale (2026-02-18):** `--quick` (inline single-agent structured review) catches the same class of bugs as full multi-judge council at ~10% of the token cost. The value of multi-judge consensus scales with stakes, not linearly with issue count. Medium-complexity epics (3-6 issues) don't benefit enough from multi-agent spawning to justify the 5-10x cost multiplier. Full council is reserved for high-stakes work where cross-model disagreement has real ROI.

## Detection

Complexity is auto-detected after plan completes (Phase 2) by examining:
- Issue count: `br children <epic-id> | wc -l`
- Wave count: derived from dependency depth

## Flag Precedence (explicit always wins)

| Flag | Effect |
|------|--------|
| `--fast-path` | Forces `low` regardless of auto-detection |
| `--deep` (passed to $rpi) | Forces `high` regardless of auto-detection |
| No flag | Auto-detect from epic structure |

Existing mandatory pre-mortem gate (3+ issues) still applies regardless of complexity level.
