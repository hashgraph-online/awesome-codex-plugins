---
name: launch-announcement
description: Plan and schedule a multi-day announcement campaign with PostEverywhere. Use when the user is launching a product or feature, promoting an event, running a sale or offer, opening a waitlist or sign-ups, or wants teaser, launch-day, reminder and last-call posts.
---

# Launch announcement

Build a short campaign around one date: tease it, launch it, remind people, and close it. The user sees every post before anything is scheduled.

## Steps

1. **Get the facts.** Ask for anything missing: what is launching, the launch date and time zone, the end date (for an offer or event), the link, the price or offer terms, and which accounts. Use only facts the user gives. Never invent prices, dates, discounts or features.
2. **Check the calendar.** Call `list_accounts` to get the account ids. Call `list_posts_advanced` with `status: "scheduled"` and the campaign dates, so the new posts don't clash with posts already booked.
3. **Pick a cadence.** Use the template in `references/launch-cadence.md`. Shorten it for a small launch. Tell the user the plan in one line per day before you write the posts.
4. **Write the posts.** Write each post for its platform (see `schedule-social-posts` for the rules). Each stage says something new: the teaser builds interest without giving everything away, launch day says what it is and where to get it, the reminder adds a detail or a proof point the user gave you, and the last call states the deadline plainly. Follow the user's voice guide if there is one (see `brand-voice`).
5. **Media.** Use images or videos the user gives you (`upload_media_from_url` or `list_media`). Instagram, TikTok, Pinterest and YouTube posts need media; leave those platforms out if there is none, and say so.
6. **Show the plan.** Present a table: date and time, stage, accounts, and the full text. Ask the user to confirm or change it.
7. **Group it.** Call `list_campaigns` and reuse a matching campaign, or create one with `create_campaign` (a name like "Spring sale 2026").
8. **Create the posts.** After the user confirms, pick one of two ways and tell the user which:
   - **Schedule now:** `bulk_create_posts` with each post's `account_ids`, `scheduled_for`, `timezone` and `campaign_id`. The posts are booked and grouped in the campaign.
   - **Save as drafts** for a last check in the app: `bulk_create_posts` with `draft: true` on each. Drafts are not linked to the campaign. Schedule each one later with `schedule_post`.
9. **Report back.** List every post with its id, date and accounts. Mention anything that failed validation and why.

## Changes after scheduling

- To move or edit a scheduled post, use `update_post`. To cancel one, use `delete_post`.
- If the launch date moves, move every post in the campaign. Find them with `list_posts_advanced` and `campaign_id`.
