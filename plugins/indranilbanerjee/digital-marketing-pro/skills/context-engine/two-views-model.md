# The Two-Views Model

After Part 5 (Client Validation), every engagement carries two views of the world. Both remain authoritative for different questions. Neither is deleted.

## Why two views

The unbiased market research from Parts 2–4 produces a view of the brand that is independent of what the client thinks about themselves. The client validation in Part 5 then layers in client knowledge, client priorities, and client constraints — which often correct the unbiased view in some places and over-correct it in others.

Keeping both views available means the engagement can:

1. Run operations on what the business chose (v2)
2. Stress-test assumptions when something is not working (compare v1 vs v2)
3. Generate ideation from territory v2 deprioritised but v1 identified (v1 is a goldmine for fresh angles)
4. Have honest client conversations about why something is underperforming (cite both views)

If only v2 existed, the engagement would silently inherit every client bias as if it were ground truth. Maintaining v1 keeps the marketing strategy intellectually honest.

## What is in each view

### v1 — The Unbiased Market View

Produced in Parts 2–4, before any client document is consulted.

- All four Core Documents (3.1 Business & SBU, 3.2 Segmentation, 3.3 Brand Positioning, 3.4 DMFlow)
- All four Part 4 documents (4.1 Competitor Ad Analysis, 4.2 Competitor Positioning, 4.3 Customer Analysis, 4.4 Market Analysis)
- Part 2 external research outputs (industry analysis, customer demand signals, ecosystem scan)

Stored at: `engagements/{engagement-id}/part-03-four-core-documents/v1/` and `engagements/{engagement-id}/part-04-competitive-customer-market/v1/`

### v2 — The Client-Validated View

Produced selectively in Part 6 based on what changed in Part 5.

Only the documents flagged for re-run by the Decision Matrix get a v2. Documents not re-run inherit v1 as their canonical version (no v2 file exists).

Stored at: `engagements/{engagement-id}/part-03-four-core-documents/v2/` and `engagements/{engagement-id}/part-04-competitive-customer-market/v2/`

## Decision Rule: Which View to Consult

Skills, agents, and conversations should select the view based on the type of decision:

| Decision type | Primary view | Use both? |
|---|---|---|
| Operating decisions (channel execution, ad copy direction, content plan, budget allocation per campaign) | v2 | No — v2 only |
| Stress-testing or pivot conversations (a campaign is not working; segment not converting as expected) | Both | Yes — compare to identify whether v2 over-corrected |
| Ideation and suggestions (new campaign concepts, untested segments, alternative positioning angles) | Both | Yes — v1 often holds the most creative territory |
| Client conversations about underperformance | Both | Yes — articulate what unbiased market said, what client chose, what data is now suggesting |
| Competitive response decisions | Both | Yes — v1 holds the unfiltered competitor positioning; v2 holds how the client wants to be positioned vs them |
| Quarterly strategy refresh | Both | Yes — re-evaluate the v1→v2 transition with 3 months of data |

## How skills declare which view they need

Skills add a `view-preference` field in frontmatter:

```yaml
---
name: skill-name
view-preference: v2-primary   # or "v1-primary", "both", "v1-only", "v2-only"
---
```

When a skill loads engagement context:

- `v2-primary`: Load v2 docs; fall back to v1 only if a specific doc has no v2 (i.e., wasn't re-run)
- `v1-primary`: Load v1 docs always
- `both`: Load both v1 and v2 versions of every doc; the skill content compares them
- `v1-only`: Load only v1 (used by ideation skills)
- `v2-only`: Load only v2 (used by execution skills)

## The "gap between views" as strategic information

When v1 and v2 diverge significantly on a specific element (e.g., the unbiased research identified Segment X as highest-priority, but the client moved it to tertiary), that gap itself is strategic information.

Reasons the gap exists:

1. **Client has private information the unbiased research could not access** (e.g., supply constraints that make a high-volume segment unserviceable)
2. **Client over-weighted internal preferences** (e.g., founder's pet segment that data does not support)
3. **Client under-weighted competitive risk** (e.g., dismissed a segment because the current offering "isn't ready")
4. **Both views are partially right** (e.g., client knows the segment is hard, but the unbiased research identifies the long-term opportunity)

When stress-testing or generating ideas, the gap conversation goes:

> "v1 identified [X] as [characterisation]. v2 deprioritised it because [client reason]. The data over the past [period] suggests [observation]. Should we revisit?"

This is the most strategically valuable use of the two-views model.

## File operations

When v1 documents change after Part 5 (e.g., minor v1.1 corrections per the Decision Matrix), the file is renamed `3.1-business-and-sbu-analysis.v1.1.md` (and so on). The change log within the document records what changed and why.

When a v2 re-run produces a new document, it goes into `v2/` with the same filename pattern. The v2 document includes a header section: "v1 → v2 changes" listing what was modified vs the v1 version, with rationale.

## Related references

- [decision-matrix-rerun.md](decision-matrix-rerun.md) — the matrix that governs which docs get a v2
- [update-back-rule.md](update-back-rule.md) — versioning protocol for in-life corrections
- [living-instruction-file-spec.md](living-instruction-file-spec.md) — where the team's "currently true" state lives
