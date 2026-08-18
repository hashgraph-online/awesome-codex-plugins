---
name: experiment-verification-monitoring
description: Verify and monitor running experiments for operational quality. Use when designing prelaunch QA, spot-check tooling, experiment canaries, A/A tests, leakage checks, interference monitoring, active experiment dashboards, alerts, or an experimentation quality roadmap.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Experiment Verification Monitoring
  category: Product Management
  tags: practical-ab-testing,next-level-ab-testing,ab-testing,experimentation,quality-assurance
---

# Experiment Verification Monitoring

Use this skill to prevent misconfigured or unhealthy experiments from producing
bad evidence. It focuses on verification before launch, canaries, A/A tests,
leakage and interference checks, active monitoring, and quality roadmap metrics.

## Source Traceability

Primary source: *Next-Level A/B Testing* by Leemay Nassery. Guidance is
transformed and paraphrased from Chapter 5 on experiment effectiveness,
prelaunch verification, QA tooling, canaries, A/A tests, spillover effects, and
active monitoring.

Related skills:

- `ab-test-design-brief` for planning an experiment before verification.
- `experimentation-throughput-strategy` for monitoring overlap conflicts.
- `trustworthy-experiment-insights` for statistical credibility after results.

## Reference Routing

| Need | Read |
|------|------|
| Verification concepts | `references/core/knowledge.md` |
| QA, canary, A/A, and monitoring rules | `references/core/rules.md` |
| Failure scenarios and examples | `references/core/examples.md` |
| Step-by-step quality roadmap | `workflows/create-experiment-quality-roadmap.md` |

## Workflow

1. Define the experiment quality risks the platform must catch.
2. Add prelaunch verification for assignment, targeting, exposure, treatment,
   metrics, and user experience.
3. Add early launch canaries and active monitoring for misconfiguration.
4. Run periodic A/A tests to validate infrastructure health.
5. Track quality metrics and update the experimentation playbook.
6. Define owners and escalation paths for active experiment issues.

## Output Format

```markdown
# Experiment Verification And Monitoring Plan

## Quality Risks
[What errors or trust failures this plan should prevent.]

## Prelaunch Checks
| Check | Method | Owner | Pass/Fail Criteria |
|-------|--------|-------|--------------------|

## Active Monitoring
- Canary:
- Dashboards:
- Alerts:
- Leakage/interference checks:

## Platform Health
- A/A test cadence:
- Quality metrics:
- Review process:

## Escalation Rules
- Pause if:
- Restart if:
- Investigate if:
```

## Quality Bar

- Do not rely on manual QA alone when the platform has recurring setup errors.
- Do not launch experiments without verifying assignment, exposure, and metrics.
- Do not treat A/A tests as one-time setup checks; use them as periodic health
  checks when platform trust matters.
- Do not monitor only final results; active tests need early health signals.
