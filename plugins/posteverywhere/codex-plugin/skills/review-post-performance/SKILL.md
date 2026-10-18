---
name: review-post-performance
description: Review how social media posts performed with PostEverywhere analytics. Use when the user asks how their posts did, what performed best, which platform works, or wants a weekly or monthly social media report.
---

# Review post performance

Give the user a short, honest read of how their posts performed, and one or two concrete next steps.

## Steps

1. **Pick the period.** Default to the last 30 days. Call `get_analytics_summary` with `period` (`week`, `month`, or `all`), or with `from` and `to` dates.
2. **Find the posts.** Call `list_posts_advanced` with `status: "published"` and `published_after` for the same period, sorted by `published_at`.
3. **Look closer where it matters.** For the best and worst few posts, call `get_post_results` to see each platform's outcome and link.
4. **Write the report.** Keep it short:
   - Totals for the period: posts published and engagement, from the summary.
   - The best posts and what they have in common (format, topic, platform, time of day).
   - Anything that failed to publish, and whether it needs fixing (see `fix-failed-posts`).
   - One or two suggestions the user can act on this week.

## Be accurate

- Some platforms don't share every number (for example, some don't report views for all account types). Say "not available" rather than zero.
- Don't compare the user's numbers with other people's or invent benchmarks.
- A small number of posts can't show a trend. Say so when the sample is small.
