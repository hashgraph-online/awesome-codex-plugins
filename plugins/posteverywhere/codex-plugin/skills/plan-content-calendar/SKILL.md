---
name: plan-content-calendar
description: Plan a week or month of social media posts with PostEverywhere. Use when the user asks for a content calendar, a posting plan, a batch of posts, "fill my queue", or a campaign across several days or platforms.
---

# Plan a content calendar

Turn a goal (a launch, a campaign, "keep my accounts active") into a set of drafts the user can review before anything is scheduled.

## Steps

1. **Understand the plan.** Ask for anything missing: the topic or goal, the date range, which accounts, and how often to post. Default to one post a day per platform when the user doesn't say.
2. **See what's already there.** Call `list_posts_advanced` with `status: "scheduled"` and the date range, so the new plan doesn't clash with posts already booked. Call `get_queue` to see the user's regular posting slots.
3. **Group it.** If the posts belong to one campaign, call `list_campaigns`, and create one with `create_campaign` if the user wants it grouped.
4. **Draft the posts.** Write each post for its platform (see the `schedule-social-posts` skill for the rules). Vary the angle across days; don't post the same text daily.
5. **Show the plan.** Present it as a table: date and time, accounts, and the first line of each post. Ask the user to confirm or change it.
6. **Create the drafts.** After the user confirms, send them with `bulk_create_posts` (up to 50 per call). Create them as drafts (`draft: true` on each) unless the user said to schedule them straight away. Use each post's own `scheduled_for`, or `use_queue: true` to let the queue pick the times.
7. **Report back.** List what was created and what, if anything, failed validation and why.

## Good defaults

- Spread posts through the day instead of stacking them at the same minute.
- Keep one idea per post.
- When the user has a website or product link, include it where the platform allows links. Don't make up URLs.
