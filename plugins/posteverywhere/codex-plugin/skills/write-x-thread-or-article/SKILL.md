---
name: write-x-thread-or-article
description: Write an X (Twitter) thread or a long-form X Article and post it with PostEverywhere. Use when the user asks for a thread, a tweetstorm, a long post on X, an X Article, or wants to turn a blog post or idea into a thread or article on X.
---

# X threads and X Articles

A **thread** is a chain of short posts, each a reply to the one before. An **X Article** is one long-form piece with a title, headings and images, for X Premium accounts only.

## Pick the format

- The idea fits in a few short points, or the account isn't on X Premium: a **thread**.
- The piece is long, needs headings or images in the body, and the account is on X Premium: an **article**.
- Ask the user when it isn't clear. Call `list_accounts` to get the X account ids.

## Write a thread

1. **Plan it.** 3 to 10 parts. The first part is the hook: it must work on its own, because most people see only that one.
2. **Write each part** in 280 characters or fewer (X Premium accounts can go longer; `get_platform_rules` has the limit). One idea per part. Number the parts (1/6) only if the user likes that.
3. **Show the thread.** Show every part with its character count. Ask the user to confirm.
4. **Post it as a real thread.** Call `create_post` with the X `account_ids`, `content` set to part 1, and `thread_posts` set to the other parts, in order. PostEverywhere posts each part as a reply to the one before, so it goes out as one linked thread.
   - To let the user check it first, add `draft: true`. After they confirm, call `schedule_post` with the `post_id` and `scheduled_for` (with `timezone`) or `publish_now: true`. The whole thread goes out.
   - Threads and Bluesky accounts can take the same thread (Threads allows 500 characters a part, Bluesky 300). Other accounts in the same post get only part 1, so make a separate post for them.
   - If a part is too long, the post is refused before anything goes out and the error names the part. Shorten that part or split it, then try again.
   - After it publishes, call `get_post_results` and give the user the link.
   Don't schedule the parts as separate posts. They would not be linked as replies.

## Write an X Article

1. **Check the limits.** X Premium accounts only. Title up to 100 characters. Body up to 25,000 characters. Each X account can publish 2 articles in 24 hours.
2. **Write the body** in simple formatting: `# ` headings, `- ` lists, `> ` quotes, `**bold**`, `*italic*`, `[links](https://...)`, `---` dividers, code blocks and tables. A line that is only an X post link embeds that post.
3. **Images (optional).** Up to 5 images, no video. Upload each with `upload_media_from_url`. The first image is the cover (2000 x 800 looks best). Place others in the body with a line like `![caption](image:2)`, or they go at the end.
4. **Show the draft.** Show the title, the body and which images go where. Ask the user to confirm.
5. **Create it.** Call `create_post` with only X `account_ids`, `content` set to the body, `media_ids` if any, `draft: true`, and `platform_content`:
   `{"x": {"content": "<body>", "settings": {"post_type": "article", "title": "<title>"}}}`
6. **Publish or schedule.** After the user confirms, call `schedule_post` with the `post_id` and `scheduled_for` (with `timezone`) or `publish_now: true`. Then call `get_post_results` and give the user the link.

## Be careful

- An article goes to X accounts only. If the user also wants other platforms, make a separate post for them.
- A post is a thread or an article, not both: `thread_posts` can't be used with an X Article.
- X Articles need X Premium. Ask the user if the account has it before you choose an article.
- Don't invent facts, numbers or quotes to fill a thread or an article.
