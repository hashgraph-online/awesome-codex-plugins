# The Update-Back Rule

After Part 7 onwards, the engagement operates on v2. But corrections continue to surface during execution — a Target Group definition turns out to be wrong in field, a competitor is mis-classified, a positioning claim does not hold up under scrutiny, a budget assumption proves unrealistic.

When this happens, the correction is made in the **source document**, not just in the deliverable that caught the error.

## Why this matters

Without the Update-Back Rule, corrections accumulate in scattered places:

- A note in a campaign report says "actually our CAC for Segment X is 40% higher than v2 estimated"
- A creative brief is amended to remove a positioning claim that didn't land
- A media buyer adjusts the channel mix because LinkedIn is not delivering

If these corrections never make it back to the source documents (Core Doc 3.1, 3.3, 3.4), the next campaign, the next creative brief, the next media plan all start from outdated assumptions. The strategy silently drifts.

The Update-Back Rule keeps the source documents as living truth instead of frozen-at-Part-5 artifacts.

## The Process

When a correction is identified during execution (Part 9 onwards):

### Step 1: Capture the correction

Record what was discovered, where it was discovered, and what evidence supports it:

```
Discovery: Segment X actual CAC is INR 4,800, not v2-estimated INR 3,000
Source: Q2 Google Ads + Meta Ads blended performance, 60-day window
Evidence: dashboard snapshot attached, performance data in part-09-channel-strategy/9.3-google-ads/performance-q2.json
Material? Yes — changes the LTV:CAC ratio for Segment X from 4.0 to 2.5 (below health threshold)
```

### Step 2: Validate the correction

A correction is not yet a fact — it must be validated:

- Is the underlying data clean? (Tracking working correctly? Attribution model appropriate?)
- Is the time window sufficient? (60+ days for paid, 90+ for SEO/content)
- Is the sample size statistically meaningful?
- Is there an alternate explanation? (Seasonality, ad fatigue, competitive pressure, landing page issue)
- Has the senior project owner / strategy lead reviewed?

If validated → proceed to Step 3. If not validated → record as "candidate correction" pending more data.

### Step 3: Update the source document as a new version

Bump the document version. Examples:

- `3.1-business-and-sbu-analysis.v2.md` → `3.1-business-and-sbu-analysis.v2.1.md`
- The previous version (`v2.md`) is preserved (renamed `v2.0.md` for clarity if it wasn't already)

The new version's frontmatter includes:

```yaml
---
document: 3.1-business-and-sbu-analysis
version: 2.1
previous-version: 2.0
updated: 2026-05-03
update-reason: Segment X CAC correction
update-source: Q2 channel performance data
---
```

The change is made in the relevant section of the document (in this example, Step 4: Unit Economics). The change is **explicit** — old value retained in a strikethrough or change-note format, new value added with citation:

> Segment X CAC: ~~INR 3,000 (estimated, v2.0)~~ → INR 4,800 (validated from Q2 paid performance, 60-day window). LTV:CAC ratio drops from 4.0 to 2.5 — below 3.0 health threshold. Strategic implication: revisit Segment X channel mix or revisit pricing.

### Step 4: Record in the document's change log

Every document carries a change log section at the bottom:

```markdown
## Change Log

### v2.1 — 2026-05-03
- **Section 4 (Unit Economics):** Segment X CAC corrected from INR 3,000 (estimated) to INR 4,800 (validated from Q2 channel data). Triggered downstream review of channel mix for Segment X.
- **Validated by:** [project owner name or role]

### v2.0 — 2026-04-15
- Initial v2 produced from v1 + client validation responses.
- v1 → v2 changes: positioning rejected, re-written; competitor list expanded.

### v1.1 — 2026-04-08
- Minor: corrected source citation for market size estimate (sub-step 1.4).

### v1.0 — 2026-04-01
- Initial unbiased research version.
```

### Step 5: Log the update in the Living Project Instruction File

The Living Project Instruction File (`living-instruction-file.md`) is the single "what is currently true" record for the engagement. When any source document gets updated, the LIF gets a corresponding entry:

```markdown
## Currently True (as of 2026-05-03)

### Segment X
- **CAC:** INR 4,800 (corrected 2026-05-03 — was INR 3,000 in v2.0; see [3.1 v2.1](../part-03-four-core-documents/v2/3.1-business-and-sbu-analysis.v2.1.md))
- **LTV:CAC ratio:** 2.5 (below 3.0 health threshold — under review)
- **Strategic implication:** channel mix or pricing under review (see channel review queue)
```

All downstream skills read the LIF before producing output. So a campaign-plan skill running after the update will see the corrected CAC and adjust its budget recommendations accordingly.

### Step 6: Trigger downstream review

Some corrections have downstream implications that need explicit review:

- A CAC correction may invalidate the budget plan in 3.4 → trigger DMFlow review
- A positioning correction may invalidate creative briefs already in production → trigger creative review
- A persona attribute correction may invalidate audience targeting → trigger Part 9 audience review

The `/digital-marketing-pro:engagement update-back` command handles this:

1. Captures the correction
2. Validates with the user
3. Updates the source document
4. Updates the Living Instruction File
5. Identifies downstream documents that may need review
6. Adds review tasks to the engagement state

## What does NOT trigger an update-back

Not every observation deserves a source-document update:

- **Speculation** — "I think CAC is rising" without data is not a correction.
- **Single data point anomalies** — one bad week of performance is not a CAC change. Wait for 60+ days.
- **Stylistic preferences** — an ad copy that the team thinks could be punchier is not an Update-Back trigger.
- **Tactical optimisations** — a bid adjustment, a budget pacing tweak, a creative refresh — these belong in execution logs, not strategy docs.

The Update-Back Rule is reserved for **validated changes to strategic assumptions** in the source documents.

## Versioning Conventions

| Pattern | Meaning |
|---|---|
| `v1.0` | Initial unbiased research version (Parts 2–4) |
| `v1.1`, `v1.2` | Minor corrections to v1 before client validation |
| `v2.0` | Initial client-validated version (after Part 6 re-run) |
| `v2.1`, `v2.2` | Update-back corrections after Part 7 onwards |
| No version suffix | Document was never re-run — v1 is the canonical version |

## Audit trail

The full versioning history (every v1.1, v2.1, v2.2, etc.) is preserved as separate files in the document directory. Nothing is overwritten. Auditors can always reconstruct what was true at any point in time.

## Related references

- [two-views-model.md](two-views-model.md) — v1/v2 architecture
- [decision-matrix-rerun.md](decision-matrix-rerun.md) — when v2 re-runs happen
- [living-instruction-file-spec.md](living-instruction-file-spec.md) — LIF schema
- [engagement-flow-methodology.md](engagement-flow-methodology.md) — the 12-Part flow
