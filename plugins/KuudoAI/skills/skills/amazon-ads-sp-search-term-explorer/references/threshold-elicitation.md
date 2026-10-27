# Threshold elicitation (before segment tables)

If the user has **not** supplied thresholds, run this **four-question** pass **before** producing Gold / Rising / Negative tables — **in the same pre-table batch as `brand_markers`** (one conversation turn if possible). Defaults below are **fallbacks only** when the user explicitly says “use defaults” — otherwise pause for answers.

## Questions (in order)

1. **Gold ACoS ceiling** — “What **maximum ACoS %** still counts as *gold* for your account (same attribution as the file)?”
   - Single number (e.g. 25 means “at or below target efficiency”).

2. **Negative spend floor** — “What **minimum spend** (in **account currency**) should a term need before we flag it as a negative **candidate**?”

3. **Minimum clicks for negatives** — “What **minimum clicks** on a term before we recommend **keyword** negatives (not just ‘watch’)?”
   - Suggest: **~10** if window ≈ daily, **~20** if ≈ weekly, **~30** if ≈ monthly — user picks.

4. **Minimum analysis window** — “How many **days** does this file cover, and what is your **minimum** window for **strict** negative recommendations?”
   - If actual window **<** user minimum (or skill default **14** days when user has no opinion), **do not** output strict negative recommendations — see `segment-rules.md` (sufficiency gate).

## After answers

Record all four in the report header. If the user refuses, print **PLACEHOLDER** for each missing value and run in **degraded** mode with prominent caveats (prefer elicitation over silent placeholders).
