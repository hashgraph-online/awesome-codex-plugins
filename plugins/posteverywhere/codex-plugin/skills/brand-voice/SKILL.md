---
name: brand-voice
description: Learn how the user writes on social media and write a short voice guide from their own posts in PostEverywhere. Use when the user says posts don't sound like them, asks Claude to "write like me" or "match my brand voice", or wants a style guide for their social accounts.
---

# Brand voice

Read the user's own published posts, describe how they write, and use that description for every post you write after.

## Steps

1. **Collect their posts.** Call `list_posts_advanced` with `status: "published"`, `sort: "published_at"`, `order: "desc"` and `limit: 50`. If the user writes differently per platform, add `platform` (for example `"linkedin"`) and do one pass per platform.
2. **Check there is enough.** Fewer than about 10 posts is a thin sample. Say so, and ask the user for a few more examples they like, or a link to their website or newsletter to read.
3. **Describe the voice.** Write a guide of no more than 10 short lines. Cover:
   - Tone (for example: warm, direct, dry humour).
   - Sentence length and structure.
   - Point of view ("I", "we", or no person).
   - How posts open and how they end (question, call to action, link).
   - Emoji and hashtag use: how many, and where.
   - Words and phrases they use often, and words they never use.
   - Formatting: line breaks, lists, capital letters.
   - Differences between platforms, if any.
4. **Show examples.** Quote two or three of their posts that show the voice best.
5. **Confirm.** Ask the user to correct anything that is wrong. Update the guide until they agree.
6. **Use it.** Apply the guide to every post you write in this conversation, including with the other PostEverywhere skills.
7. **Keep it.** PostEverywhere has no place to store the guide through the connector. Tell the user to save it where Claude can read it next time, for example as a project instruction or in a saved note, and to paste it in when they start a new conversation.

## Be careful

- Describe what the posts actually do. Don't invent a voice the posts don't show.
- The guide is about style. Don't copy their old posts as new ones.
