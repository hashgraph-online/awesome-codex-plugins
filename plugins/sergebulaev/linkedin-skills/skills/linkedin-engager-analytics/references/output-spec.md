# Mode 2. Engager analytics — output spec

Canonical sample outputs for the engager-analytics report. See `SKILL.md` for the workflow steps.

## Engager roster

| # | Type | Name | Title | Company | Profile | ICP tier |
|---|---|---|---|---|---|---|
| 1 | commenter | Author A | Director | Cosmetics Co | linkedin.com/in/... | Prospect |
| 2 | commenter | Author B | Senior PM | Enterprise SaaS Co | linkedin.com/in/... | Aspirational |
| 3 | liker | Author C | Founder | Solo brand LLC | linkedin.com/in/... | Peer |

## Tier breakdown

| Tier | Definition | Count | % of total |
|---|---|---|---|
| Peer | Founder / operator at company in same niche, 5-50 employees | 12 | 24% |
| Aspirational | Senior leader at 50+ company in adjacent niche | 9 | 18% |
| Prospect | Director / C-suite at company matching ICP | 18 | 36% |
| Other | Doesn't fit any tier | 11 | 22% |

## Action lists

- **Follow back** (peers worth reciprocal engagement): top 5 by activity
- **Comment-drop targets** (aspirational creators with their own posts): top 5
- **DM-able prospects** (with the rationale): top 5 with one-line opener seed

## Example run

> Input: analyze engagers on https://www.linkedin.com/posts/<author>_..., max 100

> Output:
> - 50 commenters fetched ($0.25)
> - Tier split: 6 Peer / 14 Aspirational / 18 Prospect / 12 Other
> - 3 cross-post engagers detected (also engaged with my post 2 weeks ago)
> - Top 5 DM-able prospects with one-line openers attached
