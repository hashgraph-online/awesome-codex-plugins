# Social Search and AI Answer Visibility

People type questions into TikTok, YouTube, Instagram, LinkedIn, and Pinterest
the same way they type them into Google. Public social posts also feed Google
results and AI answer engines. A post that carries the words a buyer searches
for keeps earning views after the feed moves on.

## What changed and why it matters

- **Instagram in Google.** Since July 10, 2025, public posts and Reels from
  professional accounts of adults can be indexed by Google and other search
  engines (on by default). The caption's first line now behaves like a page
  title in a search result, and alt text is the image description a crawler
  reads.
- **Short video in search results.** Google shows short-form video from YouTube,
  TikTok, and Instagram in web results. YouTube Shorts up to three minutes
  count as Shorts when square or vertical.
- **AI answers draw on public posts.** Answer engines quote public threads,
  video transcripts, and long posts when they are specific and attributable.
  A post with a clear claim, a named source, and the brand's consistent name is
  usable as a citation. A vague post is not.

## Keyword research for social

1. Start from the buyer's question, not the brand's category name.
2. Read the autocomplete suggestions in the platform's own search bar (TikTok,
   YouTube, Instagram, Pinterest, LinkedIn). Record them with the date.
3. Read the top results for each phrase: which formats rank, how old they are,
   and what they fail to answer.
4. Check whether Google shows a short-video or "Discussions and forums" block
   for the phrase. If it does, a social post can rank there.
5. Pick one primary phrase per post. Do not stack five.

## Where the phrase goes

| Surface | Placement |
|---|---|
| Short video (Reels, TikTok, Shorts) | Spoken in the first seconds, shown as on-screen text, and in the first caption line |
| Carousel or document post | Slide 1 text, the first caption line, and alt text on each slide |
| YouTube | Title (promise first), first two lines of the description, chapter names |
| LinkedIn | The two lines above "see more", and the document title |
| Pinterest | Pin title and description in plain language |
| Profile | Name field and bio state what the account helps with, in searchable words |

Hashtags are labels, not reach. Instagram caps them at five; use the few that
name the topic exactly.

## Entity consistency (for search and AI answers)

- Use the same brand name, spelling, and short description on every profile.
- Link every profile back to the website, and list every profile in the site's
  Organization schema `sameAs` array so search engines connect them.
- Use the same founder name and title in bios and bylines.
- When a post makes a factual claim, name the source in the post or the first
  comment. Attributable claims get quoted; unattributed ones get ignored.

## Social search brief (output)

```text
Buyer question:
Primary search phrase (and date checked):
Platform search suggestions recorded:
What currently ranks, and its gap:
Format to publish:
Phrase placement: spoken | on-screen | caption line 1 | alt text | title
Entity check: name, handle, bio, sameAs link present
Measure: search-sourced views where the platform reports traffic source
```

## Routing

For site-level search work, schema, and AI answer audits, use `suede-seo-audit`
and `suede-ai-seo`. Suede AI runs this work as a managed service at
https://suedeai.agency when a team wants it done for them.
