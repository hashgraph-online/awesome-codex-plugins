# Living Project Instruction File — Specification

Every engagement maintains a single Living Project Instruction File (LIF) at:

```
~/.claude-marketing/brands/{brand-slug}/engagements/{engagement-id}/living-instruction-file.md
```

This file is the single source of truth for **what is currently true about the engagement**. All skills read it before producing output. All updates land here when source documents change.

## Why this exists

In a long-running engagement, source documents (Core Docs, Channel Docs, Growth Plan) get updated as the team learns. Without a single "currently true" record, every skill has to re-derive the current state from the latest version of every document — which is expensive and error-prone.

The LIF is the cached "current truth" view. It is auto-maintained whenever a source document is updated.

## Schema

The LIF is a markdown file with structured sections:

```markdown
# Living Project Instruction File

**Engagement:** {engagement-id}
**Brand:** {brand-name}
**Started:** {iso-date}
**Last updated:** {iso-date}
**Current part:** {1–12}

---

## Quick Status

- **Engagement phase:** {Setup / Research / Validation / Strategy / Channel Build / Execution / Optimization / Continuous}
- **Active campaigns:** {count}
- **Open review items:** {count}
- **Outstanding corrections:** {count}

---

## Currently True — Strategic Facts

### Brand Identity

- **Positioning statement:** {current positioning, with version reference}
- **Brand promise:** {current brand promise}
- **Tone-of-voice profile:** {current ToV summary}
- **Source:** {Core Doc 3.3 vX.Y}

### Target Audience

- **Primary persona:** {persona name + 1-line summary}
- **Secondary persona:** {if any}
- **Anti-personas:** {who we explicitly do NOT target}
- **Source:** {Core Doc 3.2 vX.Y}

### Unit Economics

- **Blended CAC:** {value} ({date confirmed})
- **Blended LTV:** {value} ({date confirmed})
- **LTV:CAC ratio:** {value} ({status: healthy ≥3 / warning 2-3 / critical <2})
- **Payback period:** {months}
- **Source:** {Core Doc 3.1 vX.Y}

### Channels & Budget

- **Active channels:** {comma-separated list with funnel stage}
- **Monthly fixed budget:** {amount}
- **Variable budget headroom:** {amount}
- **In-Market vs Out-Market split:** {percentage split}
- **Source:** {Core Doc 3.4 vX.Y}

### Compliance Profile

- **Privacy regulations applicable:** {list — DPDP, GDPR, CCPA, etc.}
- **Industry-specific regulations:** {list — HIPAA, FINRA, FTC, etc.}
- **Approval chain:** {who approves what at what spend level}
- **Source:** {brand profile + Core Doc 3.1}

---

## Recent Corrections (Last 30 Days)

| Date | What changed | Why | Source doc | Downstream impact |
|------|--------------|-----|------------|-------------------|
| 2026-05-03 | Segment X CAC corrected INR 3,000 → INR 4,800 | Q2 channel performance data | 3.1 v2.1 | Channel mix review for Segment X triggered |

---

## Open Items Requiring Resolution

### Pending Validation

- {Item 1: what needs validation, why, who is accountable}
- {Item 2: ...}

### Stress-Test Findings

- {Finding 1: campaign / segment / channel that is not performing as v2 predicted; recommended action}

### Open Opinions (Unresolved Hypotheses)

- {Opinion ID, hypothesis, why still unresolved, evidence accumulated to date}

---

## Current Part Status

**Part {N}: {Part name}**

- Started: {date}
- Status: {in-progress / awaiting-input / blocked / completed}
- Progress: {X of Y deliverables completed}
- Next required action: {what needs to happen next}
- Blocked on: {if blocked, what blocker}

---

## Version History (Source Docs)

| Document | Latest version | Last updated |
|----------|----------------|--------------|
| 3.1 Business & SBU Analysis | v2.1 | 2026-05-03 |
| 3.2 Segmentation Framework | v2.0 | 2026-04-15 |
| 3.3 Brand Positioning | v2.0 | 2026-04-15 |
| 3.4 DMFlow | v1.0 | 2026-04-01 |
| 4.1 Competitor Ad Analysis | v1.0 | 2026-04-05 |
| ... | ... | ... |

---

## Engagement Health Indicators

- **Days since last LIF update:** {N}
- **Days since last source doc update:** {N}
- **Open review items aging > 14 days:** {count}
- **Compliance violations in last 30 days:** {count}
- **Campaigns above target CPA:** {count}
- **Campaigns below target CPA (scaling candidates):** {count}

---

## Notes

(Free-form section for engagement-specific notes that do not fit the structured sections above. Used for context that future skill runs should consider.)

```

## How the LIF is updated

### Auto-updated triggers

The LIF is automatically updated when:

1. **A source document version is bumped.** When `3.1-business-and-sbu-analysis.v2.0.md` becomes `3.1-business-and-sbu-analysis.v2.1.md`, the LIF's "Currently True" section is refreshed with the changed values.

2. **An Update-Back action completes.** Every Update-Back operation (see [update-back-rule.md](update-back-rule.md)) writes both the source doc update AND a Recent Corrections entry in the LIF.

3. **An engagement part is completed or started.** The Current Part Status section is updated.

4. **A compliance violation is detected.** The Engagement Health Indicators section is updated.

5. **Daily background pull (if scheduled).** Health indicators (campaigns above/below CPA, days since update, etc.) are refreshed from cached performance data.

### Manual update

```
/digital-marketing-pro:engagement lif update --section "open-items" --add "{item description}"
```

### Manual read

```
/digital-marketing-pro:engagement lif show
/digital-marketing-pro:engagement lif show --section "currently-true"
```

## How skills consume the LIF

Every skill that produces engagement-related output reads the LIF first. A skill's reading sequence:

1. Read `_engagement.json` for current part + state
2. Read `living-instruction-file.md` for currently-true facts
3. Read the relevant source documents (using the version pointers from LIF Version History)
4. Produce output
5. Trigger LIF update if the skill changed any source doc

This means the LIF is the **first read** for any skill that consults engagement state. Faster than rebuilding context from scratch.

## File location and atomic updates

- Path: `~/.claude-marketing/brands/{brand-slug}/engagements/{engagement-id}/living-instruction-file.md`
- Updates are atomic: write to `.living-instruction-file.md.tmp`, then rename. Prevents partial writes corrupting the file.
- A change log of LIF updates lives in `_engagement.json` under `lif_change_log` (so the LIF itself stays focused on current state, not its own history).

## What does NOT belong in the LIF

The LIF is **state**, not **strategy**. It captures what is currently true, not why it became true.

- Strategic rationale → belongs in source documents (Core Docs, Channel Docs)
- Detailed performance data → belongs in performance tracking files
- Discussion threads → belongs in conversation logs
- Speculation → does not belong anywhere yet (unless captured as an Opinion)

The LIF is intentionally compact. If it grows beyond ~3,000 lines, restructure or archive — it must remain fast to read.

## Related references

- [engagement-flow-methodology.md](engagement-flow-methodology.md) — the 12-Part flow
- [update-back-rule.md](update-back-rule.md) — how source doc updates flow into the LIF
- [stone-vs-opinion.md](stone-vs-opinion.md) — how confidence tagging maps to LIF entries
