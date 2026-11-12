# Content Teardown

Stage 6 in full: what the target's best posts have in common, turned into formulas the user can reuse. This covers what the target publishes. What others say about it belongs to Stage 2's social and creators row. For a creator, artist, or personal brand, this stage is often the heart of the teardown.

## Contents
- Sampling
- The posts file
- Splitting into thirds
- Reading the images
- Channel checklists
- Write-up
- Contact sheets

---

## Sampling

- **Handles:** only accounts linked from the target's site or link-in-bio, or whose bio links back. Founders' and members' personal accounts count when the site, label, or press links them.
- **Window:** up to 100 posts from the last 180 days per channel.
- **Settle time:** posts younger than 10 days are excluded. Their numbers are still moving.
- **Source:** an authorized connector or official API, a data vendor the user licenses (within its terms), or manual reading with dated captures. LinkedIn is read by hand. See `data-sources.md`.

| Channel | Score each post by |
|---|---|
| YouTube | Views (score long-form and Shorts as separate channels) |
| TikTok | Views, with saves and shares as tiebreaks |
| Instagram | Likes + comments (views for reels when available) |
| X | Views |
| LinkedIn | Reactions + comments |
| Reddit | Score |
| Streaming tracks | Streams on one platform (each release type as its own channel if counts allow) |
| Newsletter or podcast | The public metric they show, if any; otherwise skip scoring |

## The Posts File

Save to `teardowns/<target-slug>/posts.csv`, one row per post, with the pull date in the method notes:

`channel,date,url,title,format,views,likes,comments,shares,saves,image`

- `channel` keeps formats that score differently apart (`youtube-long`, `youtube-shorts`).
- `date` is `YYYY-MM-DD`.
- `image` is the local path of the downloaded thumbnail or cover, blank if it didn't download.
- If a metric is a sum (likes + comments), add it as its own column and pass that column name to `--metric`.

## Splitting into Thirds

The script ranks posts within each channel and splits them into thirds:

```bash
node <skill-dir>/scripts/timeline.mjs thirds --posts teardowns/<target-slug>/posts.csv --metric views --min-age-days 10 --as-of YYYY-MM-DD
```

- Set `--as-of` to the pull date, so settle time is measured from when the numbers were read.
- Compare the top third with the bottom third. Leave the middle out; it blurs the contrast.
- Never compare scores across channels. A weak TikTok often outscores a strong LinkedIn post.
- **Fewer than 24 settled posts on a channel:** the script refuses that channel. List the posts with their numbers and call no pattern.

## Reading the Images

Download the thumbnail, cover, or first slide for every top-third post and a matching number of bottom-third posts, in one batch. Short-form media links expire within hours. Open each file before describing it.

- What the image shows is **Observed**. Why it might work is **Inferred**.
- A file that didn't download is "not read". Never describe an image from its caption or title.

## Channel Checklists

### YouTube
- **Title:** word count, a number or dollar figure, first person, a question, brackets or a tag, the promise
- **Thumbnail:** a face and its expression, text on it (word count), the product or the outcome, a split or before/after, the dominant color, the logo
- **Pairing:** does the thumbnail repeat the title or add a second idea?
- **Format:** Shorts vs long-form, length, series or one-offs

### TikTok
- **Cover:** which frame, and its text
- **Opening:** the first caption line and on-screen text in the first seconds
- **Format:** talking head, screen recording, slideshow, skit, green screen, duet or stitch, performance clip
- **Sound:** trending or original; for musicians, whether the post seeds their own track
- Length, hashtag count, posting rhythm

### Instagram
- **Mix:** reels vs carousels vs single images, and which wins
- **Cover or first slide:** headline size, word count, template
- **Carousels:** slide count, and what the final slide asks for
- **Caption:** the line shown before "more"
- **Grid:** recurring colors, type, frames, logo position

### X
- **The first line** shown before "Show more", and total length
- **Thread or single post**
- **Media:** none, product screenshot, chart or metric card, video, meme
- **Account:** founder vs brand, and which performs better
- Whether the best posts share numbers (revenue, users, streams, growth)

### LinkedIn
- **The opening two lines** shown before "see more"
- **Format:** text only, image, document carousel, video
- People vs product in the visuals
- Company page vs employee posts, and whether employee posts match the company's LinkedIn ads

### Reddit
- **Title pattern:** question, story, "I built..."
- Subreddits, self vs link posts
- Whether the account says who it works for

### Music releases
- **Cadence:** days between singles, single-to-album ratio, waterfall releases
- **Artwork:** face vs no face, color, type, consistency across a campaign
- **Rollout:** teaser posts per release, pre-save window length, the day-of post format
- **Versions:** sped up, acoustic, remix, live; which versions carried streams
- **Features:** solo vs feature, and the feature's audience size at the time

## Write-Up

Per channel:

- **What the winners share:** three to five traits, each counted for both thirds ("7 of 10 top thumbnails show a face, 1 of 10 bottom ones"). Counts are **Observed**; the reason is **Inferred**.
- **House style:** what holds across every post: named colors with hex values read off the images, type, templates, logo placement, recurring series.
- **Formulas:** two or three fill-in templates behind the top titles, covers, or openings, with one real example each: "[Number] [audience] use [product] to [outcome]. Here's how."
- **What changed:** before vs after each inflection from Stage 1, where dates allow.

For why one specific post spread, use `$suede-social`. To produce the posts, `$suede-social` and `$suede-video`; for clip-based guides, `$suede-clip-to-guide`.

## Contact Sheets

Per channel, one image with the top third in one row and the bottom-third sample in the row below, each labeled with its score and date. It's the fastest way to check a claimed pattern. Build it from the downloaded files (for example with ffmpeg's `tile` filter) and link it in the write-up. Images not read are listed by URL in the method notes.
