---
name: repurpose-content
description: Turn one long piece of content into a set of social media posts with PostEverywhere. Use when the user shares a blog post, article link, video transcript, podcast notes, newsletter or other long text and wants posts made from it, or says "repurpose this" or "turn this into posts".
---

# Repurpose content

Turn one source into several posts, each written for its platform. Everything is a draft until the user says go.

## Steps

1. **Get the source.** Use the text the user gave. If they gave a link, read it with your own web access if you have it. If you can't open it, ask the user to paste the text. Never write posts from a title or a guess.
2. **Pull out the ideas.** List the main points, useful facts, quotes and examples in the source. Each one can become a post. Keep the source's facts exactly; don't add numbers, claims or links it doesn't contain.
3. **Pick the accounts.** Call `list_accounts`. Use the accounts the user named, or ask. Skip any account that can't post and tell the user why.
4. **Plan the set.** Suggest how many posts and where, for example one LinkedIn post, three X posts and one Threads post, each from a different idea. Ask if they want them spread over several days.
5. **Write the posts.** Write each post for its platform (see the `schedule-social-posts` skill for the rules, and call `get_platform_rules` for any platform you are unsure about). Use a different angle per post: a key point, a quote, a how-to, a question. Add a link to the source when the user has one and the platform allows links. If the user has a voice guide (see `brand-voice`), follow it.
6. **Media.** Instagram, TikTok, Pinterest and YouTube need an image or video. Use media the user gives you: `upload_media_from_url` for a public link, or `list_media` for files already in their library. If there is no media, leave those platforms out and say so.
7. **Show the drafts.** Present them as a table: platform, date and time (if any), and the full text. Ask the user to confirm or change them.
8. **Create them.** After the user confirms, create them as drafts with `create_post` and `draft: true`, or several at once with `bulk_create_posts` (each with `draft: true`). Only schedule or publish when the user asks, with `schedule_post` on each draft.
9. **Report back.** List each post id, its accounts and its time.

## Be careful

- Credit the source when it isn't the user's own work.
- Don't copy long passages word for word from someone else's article.
