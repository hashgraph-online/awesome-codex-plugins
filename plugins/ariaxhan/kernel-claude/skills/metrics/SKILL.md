---
name: metrics
description: "Observability dashboard. Session stats, agent tracking, hook performance, learning health. Triggers: metrics, stats, dashboard, observability."
user-invocable: true
allowed-tools: Read, Bash, Grep, Glob
kernel:
  kind: workflow
  version: 1
  side_effects: none
  confirmation: none
---

<skill id="metrics">

<purpose>
Surface actionable insights from KERNEL telemetry. Wraps `agentdb metrics` with analysis and recommendations.
</purpose>

<execution>
1. Run `agentdb metrics` to get raw data
2. Analyze patterns and surface insights:
   - Session duration trends (are sessions getting longer? that may indicate complexity creep)
   - Agent success rates (are adversary verdicts calibrated?)
   - Hook failure rates (which guards need attention?)
   - Learning utilization (which learnings get reinforced vs ignored?)
3. Present dashboard with actionable recommendations

Example recommendations:
- "64% tier 1 work — your skill set matches well"
- "Adversary sample size < 5 — run /kernel:tearitapart more on tier 2+ work"
- "detect-secrets had 2 failures — check patterns are current"
- "3 learnings never reinforced in 30d — will be auto-pruned"
</execution>

<on_start>
```bash
agentdb metrics
agentdb health
```

<ask_user>
  Use AskUserQuestion when: dashboard displayed and anomalies found
  Ask: "Anomaly in {metric}: {detail}. Want to investigate, or just note it?"
  Options: investigate, note and move on
</ask_user>
</on_start>

</skill>
