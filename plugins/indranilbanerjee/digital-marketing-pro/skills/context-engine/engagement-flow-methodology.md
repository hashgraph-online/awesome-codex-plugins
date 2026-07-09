# Engagement Flow Methodology

The 12-Part sequential engagement methodology used by every brand engagement in this plugin. This is the spine that every command, skill, and agent reads back to.

## Why this exists

Most marketing tools generate isolated outputs — a campaign brief here, an email there, a content piece somewhere else. There is no canonical sequence, no shared state, no enforced structure. The result is inconsistent depth, missed dependencies, and outputs that do not compound across engagements.

This methodology fixes that by making every engagement run through the same 12-Part sequence, producing the same set of files in the same order, with explicit dependency rules between them.

## The 12 Parts

| Part | Name | Type | Output |
|------|------|------|--------|
| 1 | Client Inputs | Intake | Stone vs Opinion intake document |
| 2 | External Research | Unbiased research | 3 research documents (industry, customer demand signals, ecosystem scan) |
| 3 | Four Core Documents | Proprietary strategy depth | 4 documents, 61 total steps |
| 4 | Competitive + Customer + Market Analysis | Unbiased research | 4 documents (4.1–4.4) |
| 5 | Client Validation Document | Client-facing | The one true stop. Client accepts/rejects/edits each finding |
| 6 | Selective v2 Re-runs | Proprietary strategy depth | Subset of Part 3 + Part 4 docs re-run per Decision Matrix |
| 7 | Preparation Documents | Internal operating | 6 documents (campaign architecture, naming conventions, approval chains, KPI tree, content pillars, asset inventory) |
| 8 | Growth Plan + Yearly Planner | Client-facing | The flagship deliverables (11-section Growth Plan + 12-month Yearly Planner) |
| 9 | Channel Strategy Fan-out | Channel execution | Up to 17 channel documents grouped into 7 families |
| 10 | Execution Artefacts | Channel execution | Communication outputs (ad copy, post copy, headlines, CTAs) |
| 11 | AI Creative Instructions | Channel execution | Visual asset briefs |
| 12 | Continuous Improvement Loop | Continuous | Market + operating signals → product/offering decisions |

## Why this sequence

The order is not arbitrary. Each part feeds the next:

1. **Part 1 captures only what the client knows for certain (Stone) and what they believe (Opinion, tagged as hypothesis).** This separation matters — the unbiased research phase that follows must not be contaminated by what the client thinks about themselves.

2. **Parts 2–4 are unbiased external research — no client documents used.** This produces a market view that is independently validated.

3. **Part 5 is where the unbiased view meets the client.** The client accepts, rejects, or edits each element. This is the one true stop in the flow.

4. **Part 6 selectively re-runs Parts 3 and 4 only where client validation materially changed something.** Most engagements need only a subset of these re-runs, not all.

5. **Parts 7–8 translate the validated position into the operating layer (preparation documents) and the client-facing deliverables (Growth Plan, Yearly Planner).**

6. **Part 9 produces the channel-by-channel strategies. Part 10 produces the execution artefacts. Part 11 produces the AI creative instructions for visual assets.**

7. **Part 12 runs continuously from go-live**: market and operating signals flow back into product and offering decisions.

## The Two-Views Model

After Part 5, the engagement carries both views — never delete v1.

- **v1** = the unbiased market view from Parts 2–4 (what the market said before the client lens was applied)
- **v2** = the client-validated view (after Part 5 acceptances/edits)

Both views remain authoritative for different questions. The team and Claude select which view to consult based on the type of decision being made:

- **Operating decisions** (channel execution, ad copy direction, content plan) — primarily v2. The business chose this path.
- **Stress-testing or pivot conversations** (a campaign is not working; a segment is not converting as expected) — both views. v1 may have been right where v2 over-corrected, or vice versa.
- **Ideation and suggestions** (new campaign concepts, untested segments, alternative positioning angles) — both views. Often the best ideas come from territory v1 identified that v2 deprioritised.
- **Client conversations about why certain things are not performing** — both views. The team can articulate what the unbiased market said, what the client chose, and what the data is now suggesting.

## Decision Matrix for v2 Re-runs

Not every Part 5 client validation triggers a full v2 re-build. The Decision Matrix governs which documents need re-running:

| If this changed in Part 5 | Re-run these documents |
|---|---|
| Competitors changed (added, removed, re-tiered) | All four Core Documents (3.1–3.4) AND 4.1 Competitor Ad Analysis AND 4.2 Competitor Positioning |
| Target market data changed (geography, market size, segments) | 4.3 Customer Analysis AND 4.4 Market Analysis |
| Audiences changed | Core Doc 2 (Segmentation) + Core Doc 3 (Brand Positioning) + Core Doc 4 (DMFlow) |
| Positioning changed | Core Doc 3 (Brand Positioning) |
| Budget / scope changed | Core Doc 4 (DMFlow) |
| Minor corrections only | Update inline in v1, tag as v1.1. No full re-run |

Most engagements trigger only a subset of these. The matrix prevents over-re-running (which wastes tokens) and under-re-running (which leaves stale assumptions in the v2 layer).

See [decision-matrix-rerun.md](decision-matrix-rerun.md) for the full specification.

## The Update-Back Rule

After Part 7 onwards, the team operates on v2. But corrections continue to surface — a TG definition turns out to be wrong in field, a competitor is mis-classified, a positioning claim does not hold up. When this happens, the correction is made in the source document, not just in the deliverable that caught the error.

**Process:**

1. Validate the correction with the senior project owner / strategy lead
2. Update the source document as a new version (v2.1, v2.2, etc.)
3. Record the change in the document's change log
4. Log the update in the Living Project Instruction File so the rest of the team picks it up

This keeps the project honest over the life of the engagement instead of silently drifting.

See [update-back-rule.md](update-back-rule.md) for the full protocol.

## File Counts per Engagement

A typical full-suite engagement produces ~50–60 files. The breakdown:

- **Numbered flow files (Parts 1 through 11):** ~28 to 48 files depending on scope. The variability is mostly in Part 9 (1 to 17 channels in scope) and Part 6 (0 to 6 v2 re-runs).
- **Project-layer files:** Living Project Instruction File, Setup + Orientation + Inventory guides, performance data exports (6 to 9 files), Current Standing Document, QC library (8 documents), reference framework guides (3 to 5).
- **Supplementary research** as engagements demand it.

Out of the entire numbered flow, only **Parts 5 and 8 produce client-facing deliverables** — the Client Validation Document and the Growth Plan + Yearly Planner. That is two to three branded files out of ~30+ internal documents. This is intentional. The internal documents prioritise depth, rationale, and assumption discipline; the client-facing documents prioritise polish and narrative coherence.

## The Engagement Directory Structure

Every engagement lives at `~/.claude-marketing/brands/{brand-slug}/engagements/{engagement-id}/` with this canonical structure:

```
engagements/{engagement-id}/
├── _engagement.json                # State: current part, completed parts, change log
├── living-instruction-file.md      # Persistent "what's currently true" record
├── part-01-client-inputs/
│   ├── stone-facts.json
│   ├── opinion-hypotheses.json
│   └── intake-questionnaire.md
├── part-02-external-research/
│   └── (3 research docs)
├── part-03-four-core-documents/
│   ├── v1/
│   │   ├── 3.1-business-and-sbu-analysis.md
│   │   ├── 3.2-segmentation-framework.md
│   │   ├── 3.3-brand-positioning-and-communications.md
│   │   └── 3.4-dmflow.md
│   └── v2/
│       └── (re-runs per decision matrix)
├── part-04-competitive-customer-market/
│   ├── v1/
│   │   ├── 4.1-competitor-ad-analysis.md
│   │   ├── 4.2-competitor-positioning.md
│   │   ├── 4.3-customer-analysis.md
│   │   └── 4.4-market-analysis.md
│   └── v2/
├── part-05-client-validation/
│   └── client-validation-document.md
├── part-06-v2-reruns/
│   └── (re-run docs land in part-03/v2 and part-04/v2)
├── part-07-preparation/
│   └── (6 prep docs)
├── part-08-growth-plan/
│   ├── growth-plan.md            # Client-facing
│   └── yearly-planner.md         # Client-facing
├── part-09-channel-strategy/
│   └── (up to 17 channel docs grouped by family)
├── part-10-execution-artefacts/
├── part-11-ai-creative-instructions/
└── part-12-continuous-improvement/
    └── (signals + product/offering recommendations)
```

## Account / Compute Split

The methodology supports running parts from different Claude accounts to leverage token limits. None of this is strict — any team can produce any part from any account. The recommendation simply optimises across token limits and the typical workflow:

- **Part 1** (Client Inputs) — done during engagement setup
- **Parts 2 and 4** (External research) — these do not depend on the proprietary framework library, so they can be produced without any setup overhead. This frees other accounts to focus on the deeper strategy work.
- **Parts 3, 6, 7** (Proprietary strategy) — typically done where the Four Core Documents framework, B2B Pointers, Communication Playbook, and other reference guides are loaded.
- **Part 5** (Client Validation Document) — requires branded output.
- **Part 8** (Client-facing strategy) — same; client-branded.
- **Part 9** (Channel strategy) — typically done where each channel doc benefits from access to the channel-specific guides.
- **Parts 10 and 11** (Execution + AI Creative) — typically distributed to delivery teams' own accounts.

All outputs land in the same per-engagement directory regardless of which account produced them.

## How skills consult this methodology

Every skill in this plugin that produces engagement-related output:

1. Reads the current part from `_engagement.json`
2. Reads the Living Instruction File for "what is currently true"
3. Reads the relevant v1/v2 source documents
4. Produces output that lands in the canonical part directory
5. Updates `_engagement.json` and the Living Instruction File on completion

Skills must declare which part they belong to in their frontmatter:

```yaml
engagement-part: 3.1   # or "9", "8", "12", etc.
```

## Related References

- [four-core-documents-spec.md](four-core-documents-spec.md) — 61-step specification for Part 3
- [two-views-model.md](two-views-model.md) — full v1/v2 architecture
- [decision-matrix-rerun.md](decision-matrix-rerun.md) — when to re-run what
- [update-back-rule.md](update-back-rule.md) — versioning protocol
- [stone-vs-opinion.md](stone-vs-opinion.md) — confidence tagging
- [living-instruction-file-spec.md](living-instruction-file-spec.md) — LIF schema
- [channel-families.md](channel-families.md) — Part 9 channel grouping
- [growth-plan-template.md](growth-plan-template.md) — Part 8 deliverable template
