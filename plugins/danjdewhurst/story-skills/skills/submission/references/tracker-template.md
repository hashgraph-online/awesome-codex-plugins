# Submission Tracker Template

Create `submission/tracker.md` the first time the author reports sending a
submission. Every row comes from the author; never add an agent, date, or
response they did not give you.

```markdown
---
type: submission-tracker
story: {story-id}
updated: YYYY-MM-DD
---

# Submission Tracker: {Title}

| Agent/Publisher | Date Sent | Materials | Status | Response Date | Notes |
|-----------------|-----------|-----------|--------|---------------|-------|
| *No submissions yet* | | | | | |

## Summary

- Queried: 0
- Requests (partial / full): 0 / 0
- Offers: 0
- Declined: 0
- No response: 0
- Withdrawn: 0
```

## Columns

- **Agent/Publisher:** the name and agency or market, as the author gives
  it.
- **Date Sent:** `YYYY-MM-DD`.
- **Materials:** what was sent, such as `query + first 10 pages`,
  `query + synopsis`, or `full`.
- **Status:** one of the statuses below.
- **Response Date:** `YYYY-MM-DD`; blank until a response arrives.
- **Notes:** the personalization used, feedback received, and follow-up
  rules.

For magazines, anthologies, and contests, `short-fiction-markets.md` adds
Story, Type (`exclusive` or `simultaneous`), and Rights Offered columns, and
a publication history section.

## Statuses

| Status | Meaning |
|--------|---------|
| `queried` | Sent; waiting for a reply |
| `submitted` | Short fiction: the full story sent to a market; waiting for a reply |
| `held` | Short fiction: the market is holding or shortlisting the story before a final decision |
| `requested-partial` | The agent asked for part of the manuscript |
| `requested-full` | The agent asked for the full manuscript |
| `offer` | An offer of representation or publication |
| `declined` | A rejection at any stage |
| `no-response` | The agent's stated response window passed, or the author closed it |
| `withdrawn` | The author withdrew the submission, for example after an offer elsewhere |

## Maintenance

- Update the row in place when the status changes, and fill in Response
  Date.
- Recount the Summary and set `updated` after every change.
- When an offer arrives, remind the author to notify every agent who still
  has the query or manuscript. Do not contact anyone yourself.
