---
name: recycle-top-posts
description: Find the user's best past social media posts in PostEverywhere and schedule fresh versions of them. Use when the user wants to reuse, recycle, reshare or "bring back" posts that did well, fill gaps in their schedule with proven content, or asks which old posts are worth posting again.
---

# Recycle top posts

Find what worked before, write new versions of it, and space them out. A new version says the same idea in new words; it is never a copy.

## Steps

1. **Pick the period.** Default to the last 90 days. Call `get_analytics_summary` (`period: "custom"` with `from` and `to`) to see which platforms did best.
2. **Find the posts.** Call `list_posts_advanced` with `status: "published"`, `published_after` and `published_before`, `sort: "published_at"`, and `limit: 100`. Page with `offset` if there are more. Each destination carries its own numbers (views, likes, comments, shares) where the platform reports them.
3. **Rank them.** Rank by engagement on each platform, not across platforms: a good LinkedIn post and a good X post have different numbers. Use `get_post_results` for a closer look at the top few. Leave out posts that were about a date or offer that has passed.
4. **Show the shortlist.** List the top five to ten posts: platform, date, first line, and the numbers. Say "not available" when a platform didn't report a number. Ask the user which to recycle.
5. **Write new versions.** For each chosen post, write a fresh version: a new first line, a new angle or example, the same core idea and the same facts. Change the format when it helps (a tip list becomes a question, a quote becomes a short story). Follow the user's voice guide if there is one (see `brand-voice`).
6. **Space them out.** Leave at least a few weeks between a post and its new version on the same account. Call `list_posts_advanced` with `status: "scheduled"` to avoid clashes, or offer to use the posting queue (`get_queue`, then `use_queue: true`).
7. **Show the plan.** Present a table: date and time, accounts, the old first line and the new text. Ask the user to confirm.
8. **Create them.** After the user confirms, create them as drafts with `bulk_create_posts` (`draft: true` on each), or schedule them with each post's `scheduled_for` if the user said to. To reuse the original media, get its ids with `get_post`, check each one is still in the library with `get_media`, and pass them in `media_ids`.
9. **Report back.** List each new post id, its accounts and its time.

## Be honest

- A small number of posts can't show what works. Say so when the sample is small.
- Some platforms don't report every number. Don't rank a post low because its numbers are missing.
