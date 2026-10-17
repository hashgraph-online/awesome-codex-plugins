---
name: schedule-social-posts
description: Write, schedule or publish a social media post with PostEverywhere. Use when the user wants to post, cross-post, schedule, or queue content to Instagram, TikTok, YouTube, LinkedIn, Facebook, X, Threads, Pinterest, Bluesky, Telegram, Discord or WordPress, or asks to "post this everywhere".
---

# Schedule social posts

Use the PostEverywhere connector to turn what the user wants to say into posts on their connected accounts. Posting is public and hard to undo, so confirm before anything goes live.

## Steps

1. **Find the accounts.** Call `list_accounts`. Note each account's `id`, platform and health. If the user has no accounts, or none for a platform they named, use the `connect-social-accounts` skill first.
2. **Pick the targets.** Use the accounts the user named. If they said "everywhere", use every healthy account. Skip an account whose health says it needs reconnecting, and tell the user which one and why.
3. **Check the rules.** For any platform you are unsure about, call `get_platform_rules` once and read the character limit, media rules and supported features. Common limits are in `references/platform-limits.md`.
4. **Write the post.** Write one main caption in `content`. When a platform needs something different, set it in `platform_content` keyed by platform, for example a shorter X version: `{"x": {"content": "..."}}`. Keep the user's voice and facts. Don't invent claims, prices, links or statistics.
5. **Add media.** For an image or video at a public URL, call `upload_media_from_url` and use the returned media id in `media_ids`. Instagram and TikTok need media. YouTube needs a video.
6. **Confirm first.** Show the user, per account, the text, the media and the time. Unless they already said "publish now" or "schedule it" for this exact post, create it as a draft: `create_post` with `draft: true`. Then ask for a go-ahead.
7. **Publish or schedule.** After the user confirms, call `schedule_post` with the draft's `post_id` and either `scheduled_for` (ISO 8601, with `timezone`, for example `"Europe/London"`) or `publish_now: true`. To let the user's posting queue choose the time, create the post with `use_queue: true` instead of a time. Call `get_queue` first if they want to know which slot they'll get.
8. **Report back.** Give the post id, the accounts and the time. For "publish now", call `get_post_results` after a short wait and report which platforms published and any failure in plain words.

## Timing

- Ask for the time zone if the user gives a time without one and their account time zone is unknown. `get_me` returns account details.
- A time in the past publishes immediately. Check with the user before sending one.

## When something fails

- If `create_post` returns a validation error (too long, missing media, unsupported format), fix the post and try again. Tell the user what you changed.
- For a failed destination after publishing, use the `fix-failed-posts` skill.

## Special formats

- **X Articles** (long-form, X Premium accounts only): `platform_content` `{"x": {"content": "<body>", "settings": {"post_type": "article", "title": "<max 100 characters>"}}}` with X accounts only.
- **WordPress blog posts**: `platform_content` `{"wordpress": {"content": "<body>", "settings": {"title": "...", "status": "publish|draft", "tags": ["a"]}}}` with WordPress accounts only. The first image is the featured image.
- **Pinterest**: set the board with `{"pinterest": {"settings": {"boardId": "...", "link": "https://..."}}}`. `get_account` lists the boards.
