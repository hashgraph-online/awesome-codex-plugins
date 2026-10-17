---
name: cross-post-video
description: Post one video to several platforms with PostEverywhere, with the right title and caption for each. Use when the user wants to share a video, Reel, Short or TikTok across TikTok, Instagram Reels, YouTube Shorts, LinkedIn and Facebook Reels, or asks to "post this video everywhere".
---

# Cross-post a video

Upload the video once, write a caption for each platform, and pick the right format on each one.

## Steps

1. **Get the video.** The user gives a public link to an MP4 file. Call `upload_media_from_url` with the `url`. Videos import in the background: call `get_media` with the returned `media_id` until `media_status` is `"ready"`. If it becomes `"failed"`, tell the user the `error_message` in plain words. Never attach a video that isn't ready. For a video already in their library, find it with `list_media` and `type: "video"`.
2. **Check the rules.** Call `get_platform_rules` and compare the video with each platform's limits for length, size and aspect ratio. `get_media` shows the video's details. If the video breaks a platform's rule, leave that platform out and tell the user why.
3. **Pick the accounts.** Call `list_accounts`. Use the accounts the user named, or every healthy account on a video platform. Skip any account that can't post and say why.
4. **Write a caption for each platform.** Put a general caption in `content`, and set each platform's own in `platform_content`:
   - **TikTok:** `{"tiktok": {"content": "..."}}`. Short, hook first, hashtags at the end.
   - **Instagram Reels:** `{"instagram": {"content": "...", "contentType": "Reels"}}`. Hashtags at the end.
   - **YouTube Shorts:** `{"youtube": {"content": "<description>", "contentType": "Short", "settings": {"title": "<title>"}}}`. The title is up to 100 characters, and YouTube doesn't allow `<` or `>`. Put what the video is about in the first two lines of the description. For a normal YouTube video, use `"contentType": "Video"`.
   - **LinkedIn:** `{"linkedin": {"content": "..."}}`. A first line that earns the click, short paragraphs.
   - **Facebook Reels:** `{"facebook": {"content": "...", "contentType": "Reels"}}`.
   Follow the user's voice guide if there is one (see `brand-voice`). Don't invent facts about the video; ask the user what it shows if you don't know.
5. **Show the drafts.** Show, per platform: format, title (YouTube), caption and time. Ask the user to confirm.
6. **Create it.** Call `create_post` with `content`, `account_ids`, `media_ids: [<media_id>]`, `platform_content`, and `draft: true`, unless the user already said to publish now or gave a time for this exact post.
7. **Publish or schedule.** After the user confirms, call `schedule_post` with the `post_id` and `scheduled_for` (with `timezone`) or `publish_now: true`.
8. **Check the result.** Videos take a few minutes to process on each platform. Call `get_post_results` after a short wait and report which platforms published, with links, and any failure in plain words (see `fix-failed-posts`).

## Good defaults

- Vertical video (9:16) suits TikTok, Reels and Shorts. For a wide video, check `get_platform_rules` before you pick a short-form format.
- One video per post. To post two videos, make two posts.
