---
name: write-blog-post
description: Write and publish a WordPress blog post with PostEverywhere. Use when the user wants a blog post, an article for their website, to publish to WordPress, to save a WordPress draft, or to turn notes, a transcript or a social post into a blog post.
---

# Write a blog post

Write a full blog post, show it, and send it to the user's WordPress site as a draft or a live post.

## Steps

1. **Find the site.** Call `list_accounts` and find the WordPress accounts. `get_account` names the site. If there is none, use the `connect-social-accounts` skill first.
2. **Agree the brief.** Ask for anything missing: topic, reader, key points, length, and any links or facts to include. Use only facts the user gives you or that are in their source. Follow the user's voice guide if there is one (see `brand-voice`).
3. **Write the post.** Write the body in simple formatting: `## ` headings, `- ` lists, `> ` quotes, `**bold**`, `*italic*`, `[links](https://...)`, `---` dividers, code blocks and tables. Raw HTML is kept as it is. The body can be up to 200,000 characters.
4. **Set the details.** Write:
   - **title** (required, up to 200 characters)
   - **excerpt** (optional, up to 1,000 characters)
   - **slug** (optional, the web address ending, for example `spring-menu-2026`)
   - **tags** and **categories** (optional), by name. Tags that don't exist on the site yet are created. Categories also take the site's category numbers.
   - **status:** `draft` (saved in WordPress, not public), `publish`, `pending` (waiting for review in WordPress) or `private`. Default to `draft` unless the user says to publish.
5. **Images and video (optional).** Up to 20 images and 1 video. Upload each with `upload_media_from_url` (for a video, wait with `get_media` until it is `"ready"`). The first image is the featured image; set `"featuredImage": "none"` to turn that off. Place other images in the body with a line like `![caption](image:2)`, where the number is the image's place among the attached images, counting from 1. Images you don't place go at the end. The video goes at the top.
6. **Show the draft.** Show the title, excerpt, tags, categories, status and the full body, and say where each image goes. Ask the user to confirm.
7. **Create it.** Call `create_post` with the WordPress `account_ids`, `content` (a short version for any other platforms in the same post, or the body), `media_ids`, `draft: true`, and `platform_content`:
   `{"wordpress": {"content": "<body>", "settings": {"title": "...", "status": "draft", "excerpt": "...", "tags": ["..."], "categories": ["..."], "slug": "...", "featuredImage": "first"}}}`
8. **Send it.** After the user confirms, call `schedule_post` with the `post_id` and `publish_now: true`, or `scheduled_for` (with `timezone`) for a set time. The WordPress `status` decides whether it is public on the site.
9. **Report back.** Call `get_post_results` and give the user the link. For a WordPress draft, tell them to review and publish it in WordPress.

## Changes

- Before it is sent, change it with `update_post` (the same `platform_content.wordpress` shape).
- After it is sent, edit it in WordPress. Published posts can't be changed through PostEverywhere.

## Share it

After it is live, offer to write social posts that link to it (see `repurpose-content`).
