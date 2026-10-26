# Diagnosis Ladder — Lazy Reference

Load this file ONLY when the `diagnose` command is being executed or explained.

## Layer Order (top-down, first failing layer wins)

### 1. Tracking / Config
- **Pass:** all ad credentials configured, no placeholders
- **Fail:** any integration has placeholder values → fix before anything below matters
- **Rule:** "Signal before bids" — broken tracking means every downstream number is provisional

### 2. Ops Health
- **Pass:** no high-priority unprocessed signals, no stuck tasks
- **Fail:** high-priority signals waiting > 7 days, tasks at max attempts
- **Evidence:** signals/ with `linked-task: none` and `priority: high`

### 3. Attention (Impressions)
- **Pass:** ≥ 1,000 impressions across captured campaigns
- **Weak:** < 1,000 → delivery problem before it's a creative problem
- **Evidence:** latest ad-intel report campaign table

### 4. Traffic Quality (CTR)
- **Strong:** ≥ 5.0% (content-opportunity threshold in ad_intel.py)
- **Pass:** 3.0-5.0%
- **Weak:** 1.0-3.0%
- **Fail:** < 1.0%
- **Evidence:** total clicks / total impressions × 100

### 5. Conversion (CPA)
- **Pass:** CPA ≤ target
- **Warning:** CPA 1.0-1.2× target
- **Fail:** CPA > 1.2× target
- **Unknown:** no TARGET_CPA configured → "advice without a target is content, not media buying"
- **Evidence:** total spend / total conversions

## Confidence Labels
- **confirmed by data** — number comes from a captured report or file on disk
- **hypothesis — verify with X** — inference from pattern, needs a real test to confirm

## "The One Fix" Rule
A diagnosis that lists six problems is a way to fix none of them. The output names ONE bottleneck and ONE fix. Re-run `diagnose` after fixing it to see if the ladder moves.