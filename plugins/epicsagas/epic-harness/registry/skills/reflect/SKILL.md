---
name: reflect
description: "On-demand human self-assessment of AI usage quality. Scores 5 dimensions from session data. Not agent performance review."
---

# Reflect — Human AI-Usage Self-Assessment

This skill is for **you** (the human) to reflect on how well you're leveraging AI as a thought amplifier — not a review of agent performance.

**Data source**: The `reflect` hook (session-end) automatically collects observations, analyzes patterns, and updates `metrics.json`. This skill consumes that hook-produced data to produce a human-readable self-assessment.

```
Hook (auto)                    Skill (on-demand /reflect)
─────────────                  ──────────────────────────
observe → obs/*.jsonl  ──→     epic reflect --context 30
evolve → metrics.json  ──→     5-dimension scorecard
seed → evolved skills  ──→     Action items for the human
ingest → memory graph  ──→     Trend analysis
```

## Iron Law

No score without evidence. Every rating must directly cite at least one of: obs stats, evolution patterns, memory nodes, or session summaries.
Block self-serving bias: "doing well" conclusions require concrete metrics.

## Process

### Step 0 — Collect Context

```bash
# Uses Rust subcommand — works on all platforms (Linux, macOS, Windows)
epic reflect --context 30 > /tmp/reflect_ctx.json
```

Fallback if subcommand fails:
```bash
echo "obs_files: $(ls "$HARNESS_DIR/obs/" | wc -l)"
python3 -c "import json; m=json.load(open('$HARNESS_DIR/metrics.json')); print('total_sessions:', m.get('total_sessions',0))"
```

Query memory (if active):
```bash
epic mem recall "AI usage patterns decisions metacognition" --limit 8
epic mem list --type decision --limit 5
epic mem list --type pattern --limit 5
```

### Step 1 — 5-Dimension Reflection

Score each dimension independently: 1–10 + evidence citation + one-line diagnosis.

#### Dimension 1: Thought Amplification
**Question**: Is AI a mere executor (code typist) or a genuine thought partner?

Metrics:
- Agent tool call ratio (`Agent / total_obs` — higher = delegated thinking)
- Skill invocation frequency (meta-layer usage)
- council/discover/spec execution history
- Memory decision node count

Scoring:
| Score | Signal |
|-------|--------|
| 8–10  | Agent delegation ≥ 5%, diverse skill usage, council execution recorded |
| 5–7   | Mostly Bash/Read/Edit, occasional Agent, complex decisions made solo |
| 1–4   | Bash+Edit 90%+, AI at autocomplete level |

#### Dimension 2: Self-Improvement
**Question**: Learning from mistakes, or repeating the same patterns?

Metrics:
- `evolution_stats.pattern_frequency` — recurring patterns?
- `evolution_stats.stagnation_count` — stagnant sessions
- `evolution_stats.trend_last10` — improving/stable/declining distribution
- Evolved skills count vs timespan

Scoring:
| Score | Signal |
|-------|--------|
| 8–10  | Trend improving ≥ 60%, no pattern recurrence, evolved skills growing |
| 5–7   | Mostly stable trend, some pattern repeats, evolved skills plateau |
| 1–4   | Trend declining or frequent stagnation, same mistakes repeated |

#### Dimension 3: Metacognitive Expansion
**Question**: Are conversations with AI helping recognize and upgrade your own thinking?

Metrics:
- Memory concept/pattern node count and recency
- Decision/ADR recording frequency
- Session snapshots mentioning "learnings"
- `/discover` `/spec` execution history (problem-framing practice)

Scoring:
| Score | Signal |
|-------|--------|
| 8–10  | Regular decision nodes, /discover /spec used, ADRs exist |
| 5–7   | Intermittent recording, decision rationale only in code, no explicit notes |
| 1–4   | Almost no memory nodes, context breaks between sessions |

#### Dimension 4: Prompt Engineering
**Question**: Is prompt quality improving over time?

Metrics:
- `output_quality` dimension average trend (metrics score_history)
- `tool_success` rate trend
- Evolved skills with prompt improvement patterns
- Session average score trajectory (early vs recent)

Scoring:
| Score | Signal |
|-------|--------|
| 8–10  | output_quality ≥ 0.80, score trend upward, evolved prompts increasing |
| 5–7   | output_quality 0.65–0.80, improvement plateau |
| 1–4   | output_quality < 0.65, downward trend, frequent re-edits |

#### Dimension 5: Execution Efficiency
**Question**: Achieving the same goals faster and cheaper through AI?

Metrics:
- `execution_cost` dimension average (1.0 = optimal)
- Bash dominance (Bash > 50% suggests excessive low-level repetition)
- Context compaction frequency (too frequent = context waste)
- Agent sub-agent parallel usage

Scoring:
| Score | Signal |
|-------|--------|
| 8–10  | execution_cost ≥ 0.90, parallel Agent usage, compaction < 20% of sessions |
| 5–7   | Bash 40–60%, mostly single-agent serial execution |
| 1–4   | Bash 70%+, no sub-agent usage, trivial tasks delegated to AI |

### Step 2 — Summary Scorecard

```
## AI Thought-Amplifier Reflection Report
Generated: {ISO-8601}  |  Window: {N} days  |  Total sessions: {total_sessions}

| Dimension            | Score | Grade | Key Evidence |
|----------------------|-------|-------|--------------|
| Thought Amplification | X/10 | 🔴/🟡/🟢 | Agent {N}x ({P}%), Skill {M}x |
| Self-Improvement      | X/10 | 🔴/🟡/🟢 | trend={T}, stagnation={S}x |
| Metacognitive Expansion | X/10 | 🔴/🟡/🟢 | decisions {D}, session notes {M} |
| Prompt Engineering    | X/10 | 🔴/🟡/🟢 | output_quality={Q}, trend={Δ} |
| Execution Efficiency  | X/10 | 🔴/🟡/🟢 | execution_cost={C}, Bash%={B} |
| **Overall**           | **X/10** | | |

Grade: 🟢 8–10 (good)  🟡 5–7 (fair)  🔴 1–4 (needs improvement)
```

### Step 3 — Cold Summary

3–5 sentences. Rules:
- Open with the lowest-scoring dimension
- No "doing well" claims without numeric evidence
- State the single biggest bottleneck
- Classify usage as "execution automation" or "thought amplification"

### Step 4 — Action Items (minimum 3)

Format: `[Priority] Title — Concrete action — Expected impact`

```
### Next Reflection Actions

1. [HIGH] {title}
   - Action: {concrete steps}
   - Metric: {how to measure}
   - Deadline: {session count or date}

2. [MED] ...
3. [LOW] ...
```

Recommended action pool (select by low-scoring dimensions):
- Thought Amplification low → council mode weekly, /spec writing habit
- Self-Improvement low → `/evolve history` periodic review, manual pattern notes
- Metacognition low → `epic mem add --type decision` after every important decision
- Prompt low → post low-quality session prompt review → seed improved evolved skill
- Efficiency low → Agent parallel sub-agent patterns, script repetitive Bash calls

### Step 5 — Save to Memory

Save reflection to memory (if mem tools active):
```bash
epic mem add \
  --type session \
  --title "AI usage reflection {date}" \
  --tags "reflection,metacognition" \
  --importance 0.8 \
  --body "Overall: {score}/10. Lowest: {lowest_dim}. Top action: {top_action}"
```

---

## Anti-Rationalization

| Excuse | Rebuttal | What to do instead |
|--------|----------|--------------------|
| "Too few sessions for accurate reflection" | Even 3 sessions reveal patterns. Insufficient data is not an excuse for a high score. | Reflect on available data; add data collection improvement as an action item. |
| "Bash-heavy because it's a Rust project" | Tool usage distribution doesn't only reflect task type. Check for Bash calls that could be delegated to Agent. | Find ≥ 3 Bash calls that could be replaced by Agent delegation. |
| "Score 0.75 is good enough" | 0.75 is not an absolute standard. Trend vs previous period matters more. | Compare last 5-session average vs prior 5-session average in score_history. |
| "No memory needed — context is enough" | Context dies at session end. Without cross-session learning continuity, you start from scratch every time. | Start the habit of `epic mem add` after every important decision — now. |
| "Code output is already good, so it's fine" | Code output quality ≠ thought amplification. Good code can still mean AI is doing the thinking for you. | Count how many decisions in the last 5 sessions you actually designed yourself. |

## Evidence Required

- [ ] `/tmp/reflect_ctx.json` or manually collected data exists
- [ ] Each of 5 dimensions cites ≥ 1 numeric evidence
- [ ] Summary scorecard output complete
- [ ] Cold summary states 1 specific bottleneck
- [ ] Minimum 3 action items, each with measurement metric
- [ ] Anti-Rationalization table applied to low-scoring dimensions (1–4)

## Red Flags

- All dimensions ≥ 7 → suspect positive bias. Re-verify each score against evidence.
- Action items at "use more often" level → rewrite with concrete actions and metrics.
- Summary under 200 chars → insufficient analysis. Cite more evidence.
- Script failure stops reflection → fall back to manual collection and continue.
- Memory save omitted → reflection won't carry into next session.
