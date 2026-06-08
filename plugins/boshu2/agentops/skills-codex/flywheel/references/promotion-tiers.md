# Knowledge Promotion Tiers

Defines the maturity pipeline for knowledge artifacts.

## Tier 0: Forge Candidates (`.agents/forge/`)

- **Source:** `$forge` (transcript mining), SessionEnd hook
- **Confidence:** 0.0-0.6
- **Citations:** 0
- **Promotion criteria:** Auto-promote to Tier 1 when confidence >= 0.7 OR cited >= 2 times (ao-free fallback promotes automatically)
- **Eviction:** Candidates older than 90 days with 0 citations are archived

## Tier 1: Learnings (`.agents/learnings/`)

- **Source:** `$post-mortem`, `$post-mortem --quick`, `$extract`, promoted from forge
- **Confidence:** 0.3-1.0
- **Citations:** 1+
- **Promotion criteria:** Promote to Tier 2 when confidence >= 0.8 AND cited >= 3 times AND age > 30 days
- **Eviction:** Learnings older than 90 days with 0 citations decay to archive

## Tier 2: Patterns (`.agents/patterns/`)

- **Source:** Promoted from learnings (manual or automated)
- **Confidence:** 0.8-1.0
- **Citations:** 3+
- **Age:** 30+ days
- **Eviction:** Protected — patterns are long-lived and rarely archived

## Cross-Repo Promotion

- Any tier can be promoted to `~/.codex/patterns/` via `$post-mortem --global`
- Global patterns are user-level, shared across all repositories
- Promotion is a manual decision (human judgment on cross-repo applicability)
- Global patterns are found by `$research`, `$knowledge`, and `$inject` via grep

## Confidence Normalization

When comparing confidence across formats:
- Categorical: high = 0.9, medium = 0.6, low = 0.3
- Numeric: 0.0-1.0 pass through unchanged

## Citation Tracking

Citations are recorded in `.agents/ao/citations.jsonl`:
```json
{"artifact_path": ".agents/learnings/example.md", "cited_at": "2026-02-19T12:00:00Z", "session_id": "session-id", "workspace_path": "/abs/workspace"}
```

The `$inject` skill records citations when knowledge is loaded into a session.
The `$post-mortem` skill processes citations to update confidence scores.
The `$flywheel` skill reports citation metrics in health checks.
