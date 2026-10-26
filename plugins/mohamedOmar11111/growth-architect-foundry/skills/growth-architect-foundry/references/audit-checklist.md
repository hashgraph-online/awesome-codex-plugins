# Audit Checklist — Lazy Reference

Load this file ONLY when the `audit` command is being executed or explained.
Do not load it for other commands — it's 300+ tokens that other verbs don't need.

## Scoring Dimensions (weights sum to 100%)

### Configuration (25%)
| Condition | Points |
|---|---|
| OPERATOR_NAME set and not placeholder | 15 |
| Google Ads: 5 keys, all real (not "your_..._here") | 40 |
| Meta Ads: 2 keys, all real | 25 |
| TARGET_CPA set | 20 |

### Signal Hygiene (20%)
| Condition | Points deducted |
|---|---|
| Start | 100 |
| Each unprocessed signal | -10 (max -50) |
| Each high-priority unprocessed | -15 extra (max -30) |
| Oldest open > 7 days | -5 per week (max -20) |
| Zero signals at all | Score = 50 (neutral) |

### Task Throughput (20%)
| Condition | Points |
|---|---|
| Zero tasks | 40 (no history) |
| Closure rate × 100 | base score |
| Each stuck task (attempts >= max-attempts, status open) | -20 (floor 0) |

### Loop Activity (15%)
| Condition | Points |
|---|---|
| Distinct loops seen / 6 × 50 | proportional |
| Last run ≤ 24h ago | +50 |
| Last run ≤ 7 days | +35 |
| Last run ≤ 30 days | +15 |
| Zero entries | 10 |

### Content Readiness (20%)
| Condition | Points |
|---|---|
| STRATEGY.md sections present (Brand Overview, Target Audience, Voice, Active Directives) | 15 each (60 max) |
| ≥ 1 brief in 02_Content | +20 |
| Calendar exists | +20 |

## Grade Bands
- A ≥ 90 · B ≥ 80 · C ≥ 70 · D ≥ 60 · F < 60

## What "Do Not Touch" Means
Dimensions scoring ≥ 85 are listed as healthy — protecting what works is half the job. Don't rewrite voice rules that are already working; don't re-tune loops that are already on cadence.

## How to Raise a Low Score
1. Fix Configuration first (fill real creds, set TARGET_CPA)
2. Clear signal backlog (link or discard every unprocessed signal)
3. Drive stuck tasks to done or cancelled
4. Schedule loops on cadence
5. Fill missing STRATEGY.md sections