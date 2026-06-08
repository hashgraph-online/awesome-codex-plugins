# Model Routing by Task Complexity

> Route tasks to the right model tier for cost optimization without quality loss.

## Decision Matrix

| Task Type | Recommended Tier | Cost Multiplier | Examples |
|-----------|-----------------|-----------------|----------|
| **Classification / Narrow** | Haiku (budget) | 1x | File categorization, boilerplate generation, narrow single-line edits, format conversion |
| **Implementation** | Sonnet (balanced) | ~4x | Feature implementation, refactoring, test writing, multi-file edits |
| **Architecture / Judgment** | Opus (quality) | ~19x | Root-cause analysis, multi-file invariants, security review, design decisions |

## Complexity Signals

Use these signals to auto-route when `--tier` is not explicitly set:

### Route to Budget (Haiku)
- Single-file change with clear template
- Text length < 1000 chars
- Item count < 10
- Task description matches: "format", "rename", "move", "copy", "stub"

### Route to Balanced (Sonnet)
- Multi-file changes
- Text length >= 1000 chars OR item count >= 10
- Requires understanding existing patterns
- Task description matches: "implement", "refactor", "test", "fix"

### Route to Quality (Opus)
- Cross-cutting concerns (auth, data flow, error handling)
- Security-sensitive code
- Architecture decisions
- Task description matches: "design", "review", "audit", "analyze", "debug"
- Prior attempts at balanced tier failed

## Council Integration

### Per-Judge Routing
Council judges can use different tiers based on their role:

```
Judge 1 (implementation review): balanced tier
Judge 2 (security review):       quality tier
Judge 3 (style/lint review):     budget tier
```

This reduces council cost by ~40% vs all-quality while maintaining judgment quality where it matters.

### Debate Routing
- Round 1 (initial positions): balanced tier
- Round 2 (rebuttals): quality tier (needs deeper reasoning)

## Crank Integration

### Per-Wave Routing
```
Spec waves:     budget tier  (generating templates)
Test waves:     balanced tier (requires understanding)
Impl waves:     balanced tier (standard implementation)
Vibe gate:      quality tier  (judgment call)
De-sloppify:    budget tier  (pattern matching)
```

### Dynamic Escalation
If a balanced-tier worker fails twice on a task:
1. Escalate to quality tier
2. Log the escalation for cost tracking
3. If quality tier also fails, mark task as DECOMPOSE

## Cost Tracking

Track model usage per phase for retrospective optimization:

```yaml
cost_summary:
  phase: crank-ag-xyz
  waves: 5
  model_usage:
    haiku:   { calls: 12, tokens: 45000 }
    sonnet:  { calls: 28, tokens: 180000 }
    opus:    { calls: 4,  tokens: 32000 }
  estimated_cost: "$X.XX"
  quality_score: "PASS"  # from vibe
```

Include in `$post-mortem` output when available.

## Prompt Caching

For system prompts > 1024 tokens (common in council):
- Cache the system prompt across judge calls in the same council session
- Saves ~50% on input tokens for multi-judge councils
- Particularly effective for `--deep` mode (3+ judges sharing the same system prompt)

## Flag Reference

| Flag | Effect |
|------|--------|
| `--tier=quality` | Force Opus for all calls |
| `--tier=balanced` | Force Sonnet for all calls |
| `--tier=budget` | Force Haiku for all calls |
| (no flag) | Auto-route by complexity signals |
