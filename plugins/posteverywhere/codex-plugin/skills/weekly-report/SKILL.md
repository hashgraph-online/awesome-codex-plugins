---
name: weekly-report
description: Write a short weekly or monthly social media report from PostEverywhere data, ready to paste into an email. Use when the user asks for a weekly report, a monthly recap, a client report, a summary to send their boss or team, or "how did this week go" in a form they can share.
---

# Weekly report

A short report the user can paste into an email without editing. Numbers come only from PostEverywhere.

## Steps

1. **Pick the period.** Default to the last 7 days for a weekly report and the last calendar month for a monthly one. Ask who will read it: the user, their team, or a client.
2. **Get the totals.** Call `get_analytics_summary` with `period: "week"` or `"month"`, or `period: "custom"` with `from` and `to`. It gives posts published and failed, engagement totals, a per-platform breakdown and follower change per account.
3. **Get the posts.** Call `list_posts_advanced` with `status: "published"`, `published_after` and `published_before`, `sort: "published_at"`. Pick the top three posts by engagement. Use `get_post_results` for their links.
4. **Check for problems.** Call `list_posts_advanced` with `status: "failed,partially_failed"`, and `scheduled_after` and `scheduled_before` for the same period. Note what failed and whether it is fixed (see `fix-failed-posts`).
5. **See what's next.** Call `list_posts_advanced` with `status: "scheduled"` and `scheduled_after` set to now, to list what goes out next period.
6. **Write the report.** Use `references/email-template.md`. Keep it to one screen.
7. **Offer changes.** Ask if they want it shorter, in a different tone, or with a section removed.

## Be accurate

- Say "not available" when a platform doesn't report a number. Never show a missing number as zero.
- Follower change needs two readings. If `change_in_period` is null, say the change isn't available yet.
- Don't compare with other companies or invent benchmarks. Compare only with the user's own earlier period, and only if you fetched it.
- For a client report, leave out internal notes, failures that were fixed, and anything the user says to keep private. Ask before including failures.
