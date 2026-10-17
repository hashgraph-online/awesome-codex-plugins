---
name: fix-failed-posts
description: Find and fix social media posts that failed to publish in PostEverywhere. Use when the user says a post didn't go out, a platform failed, an account stopped working, or asks what went wrong with a post.
---

# Fix failed posts

Find what failed, explain why in plain words, fix the cause, and retry only when a retry can work.

## Steps

1. **Find the failures.** Call `list_posts_advanced` with `status: "failed"` (and `"partially_failed"`), newest first. For one post the user named, call `get_post_results` with its id.
2. **Read the reason.** Each failed destination carries an error. Sort it into one of these:
   - **The account needs reconnecting** (expired or revoked login, missing permission). Call `get_account_health` for that account to confirm, then `create_reconnect_link` and give the user the link. They open it and sign in again.
   - **The post broke a platform rule** (too long, wrong media, missing media). Fix it with `update_post`, then retry.
   - **A temporary problem** at the platform (rate limit, timeout, the platform was down). Retry.
   - **Something the user must change on the platform itself** (for example, an Instagram account that isn't a Business or Creator account). Tell them exactly what to change.
3. **Retry.** For one post, call `retry_failed_post`. For many, call `retry_failed_posts` with the post ids, or filter by `account_id` or `platform`. Don't retry a failure that needs the user to act first; it will fail the same way.
4. **Confirm.** Call `get_post_results` again after a short wait and tell the user what published.

## Be careful

- Never retry the same post in a loop. One retry after a fix is enough.
- Retrying a post that already published on some platforms only retries the failed ones.
