# Debate Phase (`--adversarial`)

When `--adversarial` is passed, council runs two rounds instead of one. Round 1 produces independent verdicts. Round 2 lets judges review each other's work and revise.


## Execution Flow (with --adversarial)

```
Phase 1: Build Packet + Create Team + Spawn R1 judges as teammates
                              |
                    Judges go idle after R1 (stay alive)
                              |
Phase 1.5: Prepare R2 context (--adversarial only)
  - For each OTHER judge's R1 verdict, extract full JSON verdict
  - Each judge already has its own R1 in context (no truncation needed)
  - Each judge receives other judges' verdicts (full JSON, not truncated)
                              |
Phase 2: Judges wake up for Round 2 (--adversarial only)
  - Same judge instances as R1 (not re-spawned)
    - Other judges' full R1 JSON verdicts
    - Steel-manning rebuttal prompt
    - Branch: disagreed OR agreed
  - Judges write R2 files + send completion message
                              |
                    Collect all R2 verdicts
                              |
Phase 3: Consolidation (uses R2 verdicts when --adversarial)
                              |
```

## Round 2 via Agent Messaging

**Branch selection (lead responsibility):**
```
r1_verdicts = [extract JSON verdict from each R1 output file]
r1_unanimous = all verdicts have same verdict value (PASS/WARN/FAIL)

For each judge:
  other_verdicts = [v for v in r1_verdicts if v.judge != this_judge]
  branch = "agreed" if r1_unanimous else "disagreed"
  send message to judge with build_r2_message(other_verdicts, branch)
```

**R2 message content:** See "Debate Round 2 Message" in `agent-prompts.md`.

**R2 output files:** Use `-r2` suffix to preserve R1 files:
```
.agents/council/YYYY-MM-DD-<target>-claude-{perspective}-r2.md
```

**With --explorers:** Explorers run in R1 only. R2 judges do not spawn explorers. Explorer findings from R1 are already in the judge's context (no truncation loss).

**With --mixed:** Only Claude judges participate in R2 (they stay alive on the team). Codex agents run once in R1 (Bash-spawned, cannot join teams). For consolidation, use Claude R2 verdicts + Codex R1 verdicts.

## R1 Verdict Injection for R2

Since judges stay alive, truncation is no longer needed for a judge's **own** R1 verdict -- it's already in their context.


```json
{
  "judge": "judge-1 (or perspective name when using presets)",
  "verdict": "WARN",
  "confidence": "HIGH",
  "key_insight": "Rate limiting missing on auth endpoints",
  "findings": [
    {"severity": "significant", "description": "No rate limiting on /login"},
    {"severity": "significant", "description": "JWT expiry too long (1h)"},
    {"severity": "minor", "description": "Missing request ID in error responses"}
  ],
  "recommendation": "Add rate limiting to auth endpoints"
}
```

Full Markdown analysis remains in `.agents/council/YYYY-MM-DD-<target>-claude-{perspective}.md` files and can be referenced by the team lead during consolidation.

## Anti-Anchoring Protocol

Before reviewing other judges' verdicts in R2:

1. **RESTATE your R1 position** -- Write 2-3 sentences summarizing your own R1 verdict and the key evidence that led to it. This anchors you to YOUR OWN reasoning before exposure to others.

2. **Then review other verdicts** -- Only after restating your position, read the other judges' JSON verdicts.

3. **Evidence bar for changing verdict** -- You may only change your verdict if you can cite a SPECIFIC technical detail, code location, or factual error that you missed in R1. "Judge 2 made a good point" is NOT sufficient. "Judge 2 found an unchecked error path at auth.py:45 that I missed" IS sufficient.

## Timeout and Failure Handling

| Scenario | Behavior |
|----------|----------|
| No R2 completion message within `COUNCIL_R2_TIMEOUT` (default 90s) | Read their R1 output file, use R1 verdict for consolidation |
| All judges fail R2 | Fall back to R1-only consolidation (note in report) |
| R1 judge timed out | No R2 message for that perspective (N-1 in R2) |
| Mixed R2 timeout | Consolidate with available R2 verdicts + R1 fallbacks |

## Cost and Latency

`--adversarial` adds R2 latency but **reduces spawn overhead** vs the old re-spawn approach:
- **Agents spawned:** N judges total (same instances for both rounds, not 2N)
- **Wall time:** R1 time + R2 time (sequential rounds, but R2 is faster -- no spawn delay)
- **With --mixed:** Only Claude judges get R2. Codex agents run once (Bash-spawned, cannot join teams). For consolidation, use Claude R2 verdicts + Codex R1 verdicts for consensus computation.
- **With --explorers:** Explorers run in R1 only. R2 cost = judge processing time (no explorer multiplication).
- **Non-verdict modes:** `--adversarial` is only supported with validate mode. If combined with brainstorm or research, exit with error: "Error: --adversarial is only supported with validate mode. Debate requires PASS/WARN/FAIL verdicts."
