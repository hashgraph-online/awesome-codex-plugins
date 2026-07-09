---
name: evolve
description: "Ring 3 evolution engine. Analyzes session observations, generates and improves evolved skills, shows metrics dashboard. Subcommands: status, history, rollback, reset. Use for post-session review and skill improvement."
---

# /evolve — Manual Evolution Trigger

**CRITICAL**: Run `HARNESS_DIR=$(epic path)` first. NEVER use `.harness/` in the project directory.

You are the **Evolution Engine** — analyze past sessions to improve skills.

## Sub-commands

### `/evolve` (default) — Run evolution now
1. Read observation logs from `$HARNESS_DIR/obs/`
2. Analyze failure patterns across all sessions
3. Identify weak areas (error types, recurring failures)
4. Generate or improve evolved skills in `$HARNESS_DIR/evolved/`
5. Gate: validate new skills (format, dedup, cap of 10)
6. Report what changed

### `/evolve status` — Show evolution dashboard

Read `$HARNESS_DIR/metrics.json` and `$HARNESS_DIR/evolution.jsonl`, then display:

```
## Evolution Dashboard

### Overview
- Sessions analyzed: {total_sessions}
- Average success rate: {avg_success_rate}%
- Best score: {best_score} (session: {best_session})
- Trend: {trend} ({score_history.length} data points)
- Stagnation count: {stagnation_count} / 3 (rollback at 3)

### Score History (last 5 sessions)
| Session | Success Rate | Avg Score | Observations | Tool Success | Output Quality |
|---------|-------------|-----------|--------------|-------------|---------------|

### Evolved Skills
(list $HARNESS_DIR/evolved/*/SKILL.md with name and description from frontmatter)

### Last Session Analysis
(read last entry from evolution.jsonl)
- Error patterns: {error_patterns}
- Failure patterns: {failure_patterns[].pattern_type}
- Skills seeded: {skills_seeded}
- Skills rolled back: {skills_rolled_back}
- Analysis: {analysis_summary}
```

### `/evolve history` — Long-term analysis

Read `$HARNESS_DIR/evolution.jsonl` (full history), then display:

```
## Evolution History

### Trend Over Time
| Session # | Date | Success Rate | Avg Score | Skills | Patterns |
|-----------|------|-------------|-----------|--------|----------|

### Cumulative Pattern Frequency
| Pattern | Total Count | First Seen | Last Seen |
|---------|-------------|------------|-----------|

### Skill Effectiveness
| Skill | Sessions Active | Avg Score With | Avg Score Without | Delta |
|-------|----------------|----------------|-------------------|-------|

### Dispatch Analysis
| Skill | Times Invoked | Top Trigger Signals |
|-------|--------------|---------------------|
```

### `/evolve rollback` — Undo last evolution
1. If `$HARNESS_DIR/evolved_backup/` exists, restore it to `$HARNESS_DIR/evolved/`
2. Otherwise, read `$HARNESS_DIR/evolution.jsonl` for last entry, remove skills seeded in that entry
3. Append a rollback record to evolution.jsonl
4. Report what was rolled back

### `/evolve reset` — Clear all evolution data
1. Remove `$HARNESS_DIR/evolved/`, `$HARNESS_DIR/evolved_backup/`
2. Clear `metrics.json` and `evolution.jsonl`
3. Confirm with user first

## How Evolution Works

```
Observe (PostToolUse — multi-dimensional scoring)
    ↓ $HARNESS_DIR/obs/session_YYYYMMDD.jsonl
Analyze (Stop or /evolve)
    ↓ SessionAnalysis: per-tool, per-ext, score distribution
    ↓ Pattern detection: repeated_same_error, fix_then_break, long_debug_loop, thrashing
Seed (auto-generate targeted skills)
    ↓ 4 seeding paths: pattern / weak tool / weak file type / high-freq error
Gate (validate: format, dedup, cap of 10)
    ↓ Stagnation check: 3 sessions no improvement → rollback to best checkpoint
Reload (next session resume reports metrics + loads evolved skills)
```

## Skill Synthesis (host-agent)

When `epic-harness reflect` seeds a skill, it emits a pending-synthesis manifest
to `$HARNESS_DIR/pending_synth.jsonl` (failure evidence + template body). To
synthesize a better body:

1. Read `$HARNESS_DIR/pending_synth.jsonl`; for each record with `status: "pending"`:
2. Launch a subagent (use your host's subagent mechanism — do not name a specific
   tool or model) with the manifest's `prompt_guidance` + `evidence`, instructing
   it to write a markdown skill body with the required sections (`## Process`,
   `## Anti-Rationalization`, `## Evidence Required`, `## Red Flags`).
3. Apply the result:
   ```bash
   epic-harness evolve accept-synth --skill <name> --file <body.md>
   ```
4. The CLI validates the body, runs the Critic gate, overwrites the template
   skill, and marks the manifest consumed.

If no host runs `accept-synth`, the template body persists — synthesis can only
improve a skill, never block it.

## Scoring System
- **Composite**: `0.5 × tool_success + 0.3 × output_quality + 0.2 × execution_cost`
- **Failure classification**: 9 categories (type_error, syntax_error, test_fail, lint_fail, build_fail, permission_denied, timeout, not_found, runtime_error)
- **Pattern detection**: 4 types (repeated_same_error, fix_then_break, long_debug_loop, thrashing)

## Red Flags
- Evolving after only 1-2 observations (not enough data)
- Keeping evolved skills that never trigger
- Not reviewing evolved skills periodically
- Ignoring stagnation warnings
