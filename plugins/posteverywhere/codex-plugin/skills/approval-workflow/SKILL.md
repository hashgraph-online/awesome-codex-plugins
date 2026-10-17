---
name: approval-workflow
description: Draft social media posts for someone else to review before they go live in PostEverywhere. Use when the user works in a team or agency, needs a client, manager or colleague to approve posts, says "send these for review", "what's waiting for approval", "make the changes they asked for", or "they approved it, schedule it".
---

# Approval workflow

Posts wait as drafts until the right person says yes. Approval is the user telling you, in this conversation, that a post is approved. Never treat silence, or your own judgement, as approval.

## Create posts for review

1. **Find the accounts.** Call `list_accounts` and confirm which accounts the posts are for.
2. **Write the posts** (see `schedule-social-posts` for the platform rules).
3. **Save them as drafts.** Call `create_post` with `draft: true`, or `bulk_create_posts` with `draft: true` on each. You may set `scheduled_for` on a draft: it only suggests a time and publishes nothing.
4. **Share them for review.** Drafts appear in the PostEverywhere app, where a reviewer with access to the workspace can read them. Also give the user a short list to send: post id, accounts, suggested time and the full text.

## See what is waiting

1. Call `list_posts` with `status: "draft"` (or `list_posts_advanced` with `status: "draft"` and `search` for a word in the post).
2. Show each draft: id, accounts, suggested time and the first line. Use `get_post` for the full text and media.

## Apply requested changes

1. The user tells you what the reviewer asked for. Change only that.
2. Call `update_post` with the `post_id` and the new `content`, `platform_content`, `media_ids`, `account_ids` or `scheduled_for`.
3. Show the changed post again and ask if it now has approval.

## Schedule after approval

1. When the user says a post is approved, repeat the post id, accounts and time, so both of you are sure it is the right one.
2. Call `schedule_post` with the `post_id` and `scheduled_for` (with `timezone`), or `publish_now: true` if they want it out now.
3. Report the post id, accounts and time. For "publish now", call `get_post_results` after a short wait.

## If a post is rejected

Ask the user whether to rewrite it (`update_post`) or remove it. Delete a draft with `delete_post` only when the user asks.

## Be careful

- Only schedule the posts the user said are approved. If they approve "the first three", confirm which three by id.
- `schedule_post` only works on drafts. To change a post that is already scheduled, use `update_post`.
