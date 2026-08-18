# Decision Matrix for v2 Re-runs

After Part 5 Client Validation, the Decision Matrix governs exactly which Part 3 and Part 4 documents need to be re-run as v2 versions. The matrix prevents over-re-running (which wastes compute) and under-re-running (which leaves stale assumptions in the v2 layer).

## How it works

In Part 5, the client reviews the Client Validation Document and makes one of four decisions on each finding:

- **ACCEPT** — finding is correct as stated
- **REJECT** — finding is wrong; client provides correction
- **EDIT** — finding is partially correct; client provides amended version
- **DEFER** — needs further investigation; flag for follow-up

The Decision Matrix then triggers v2 re-runs based on which categories of findings were rejected or edited.

## The Matrix

| Category of change in Part 5 | Re-run these v2 documents |
|---|---|
| **Competitors changed** (added new competitors, removed competitors, changed competitive tier rankings) | All four Core Documents (3.1, 3.2, 3.3, 3.4) AND 4.1 Competitor Ad Analysis AND 4.2 Competitor Positioning |
| **Target market data changed** (geography, market sizing, addressable segments) | 4.3 Customer Analysis AND 4.4 Market Analysis |
| **Audiences changed** (TG priorities reshuffled, new persona added, persona attributes corrected) | Core Doc 3.2 (Segmentation) + Core Doc 3.3 (Brand Positioning) + Core Doc 3.4 (DMFlow) |
| **Positioning changed** (positioning statement amended, messaging pillars revised) | Core Doc 3.3 (Brand Positioning) only |
| **Budget / scope changed** (budget envelope changed, channel scope changed) | Core Doc 3.4 (DMFlow) only |
| **Pricing or offering changed** (pricing model amended, offering scope corrected) | Core Doc 3.1 (Business & SBU Analysis) — section 4 (Unit Economics) and section 7 (Pricing Architecture) |
| **Unit economics changed** (CAC range corrected, LTV range corrected, margin corrected) | Core Doc 3.1 — section 4 only (do not re-run full doc unless other changes warrant it) |
| **Minor corrections only** (typos, factual fixes, source updates that do not change the conclusion) | NO full re-run. Update inline in v1, tag the file as v1.1, log the change in the document's change log |

## Trigger detection

The `/digital-marketing-pro:engagement re-run-decision` command:

1. Reads the Client Validation Document responses
2. Categorises each REJECTED or EDITED finding by type (competitor / market / audience / positioning / budget / pricing / unit-economics / minor)
3. Computes the union of triggered re-runs
4. Outputs the re-run plan: which docs need v2, which can stay as v1
5. Returns the estimated compute cost (rough token estimate for each re-run)
6. Awaits user approval before running

## Rules

1. **Never auto-execute re-runs without showing the plan.** The user always sees and approves what will run.
2. **Re-runs always produce a "v1 → v2 changes" header** in the new document, listing what was modified and why.
3. **If a re-run produces a v2 that is structurally identical to v1**, do not save a redundant v2 — note this in the change log instead.
4. **Re-runs honour the original document's evidence discipline** — every change in v2 must cite a source (the client validation, in this case, with the specific finding ID).
5. **Re-runs do not delete v1.** Always two views.

## When the matrix says "no re-run" but the user wants one

The matrix is a guideline, not a hard rule. The user can override:

```
/digital-marketing-pro:engagement re-run-decision --override "rerun 3.3"
```

This forces a re-run even if the matrix didn't trigger it. Useful when the user has external context that justifies a refresh (e.g., a major industry event since v1 was produced).

## When the matrix triggers re-runs but the user wants to skip

```
/digital-marketing-pro:engagement re-run-decision --skip "rerun 4.4"
```

This skips a triggered re-run. Useful when the changed information is minor and the user judges v1 is still good enough. The skipped re-run is logged so future audits can understand why v1 wasn't refreshed.

## Audit trail

Every re-run decision (auto-triggered, override, skip) is logged to `_engagement.json` under the `rerun_decisions` array:

```json
{
  "rerun_decisions": [
    {
      "timestamp": "2026-05-03T12:00:00Z",
      "trigger": "competitors changed",
      "triggered_reruns": ["3.1", "3.2", "3.3", "3.4", "4.1", "4.2"],
      "user_decision": "approved",
      "executed_reruns": ["3.1", "3.2", "3.3", "3.4", "4.1", "4.2"],
      "skipped_reruns": [],
      "notes": "client added 2 new competitors and removed 1"
    }
  ]
}
```

This audit trail lets future engagement reviews understand what was re-run, when, and why.

## Related references

- [two-views-model.md](two-views-model.md) — the v1/v2 architecture
- [engagement-flow-methodology.md](engagement-flow-methodology.md) — the 12-Part flow context
- [update-back-rule.md](update-back-rule.md) — what happens for corrections AFTER Part 7
