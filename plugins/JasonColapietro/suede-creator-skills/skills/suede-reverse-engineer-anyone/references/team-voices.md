# Team Voices

Stage 4 in full: what the target's founders, leaders, staff, or (for a creator) the artist and their public team say about how they grew. Interviews and talks are often the strongest evidence a teardown gets, because people say outright what worked, when, and why. Job posts say what a company plans to do next.

## Contents
- Finding the people
- Finding what they said
- Getting the words
- Extracting claims
- Job posts as strategy documents

---

## Finding the People

Start with the people whose work shapes growth:

- **Company:** founders, CEO, heads of growth, marketing, product, sales, partnerships, community, and devrel.
- **Creator, artist, or band:** the creator or band members, plus their manager, label, producer, or collaborators when they speak publicly about the project.
- **Founder or personal brand:** the person themselves; their co-hosts or business partners when they speak about it.
- **App or game:** the studio's founders, producers, and community or marketing leads.

Sources: team, about, and press pages; bylines; social bios that name the target; podcast guest pages; conference speaker lists; funding and label announcements; LinkedIn company pages read by hand.

Keep it to people speaking publicly in a work capacity. Don't profile private lives, and don't contact anyone.

## Finding What They Said

| Source | How to find it |
|---|---|
| Podcasts | Search "[name] podcast" and "[target] founder interview" in podcast apps; a podcast search API if the user has a key |
| Video talks and interviews | Search "[name]" and "[target] [conference]", sorted by views |
| Conference talks | Event sites; slides on public slide hosts |
| Social threads | The person's top posts, and searches for "how we grew", "lessons", "ARR", "users", "streams", "subscribers" from their handle |
| Music press | Artist interviews, live sessions, label press releases, "making of" features |
| Blog posts and newsletters | Their own posts, investor or label blogs, newsletters that interviewed them |
| AMAs | Reddit, Hacker News, Indie Hackers, launch-platform maker comments |

## Getting the Words

- **Video:** the platform's own captions, or an authorized transcript tool (see `data-sources.md`).
- **Podcasts:** a `podcast:transcript` tag in the feed, the show's video upload, or download the audio and transcribe it locally.
- Save each transcript to `teardowns/<target-slug>/voices/<date>-<person>-<show>.txt` with the source link.

## Extracting Claims

Read every transcript and pull out claims about growth into `voices.csv`:

`said_on,person,role,source,claim,topic,dated_to,quote,link`

- **Topics:** channel, tactic, number, mistake, hire, pricing, positioning, audience, release strategy, what's next.
- **dated_to** is when the thing they describe happened ("our first 1,000 users came from Reddit in early 2024", "the song took off after a creator used it in March"), which often differs from when they said it.
- **Quote** the exact words, short. Label every claim **Reported**: it's what they say, quoted and dated, not verified.
- Each claim with a `dated_to` also becomes a row in `moves.csv` with `evidence` set to Reported.

Then look for:
- **Claims that match the data** (they credit templates, and the template family grew before the inflection): strong support.
- **Claims the data doesn't back:** note them. People remember the story, not always the order.
- **Things they say didn't work:** these go straight to plays to skip.
- **Repeated phrases** across interviews: that's the rehearsed positioning.

## Job Posts as Strategy Documents

For companies, apps, and studios, read the full text of current and past job posts, not just titles.

**Procedure:**
1. Find the careers page and follow it to a public ATS board (Greenhouse, Lever, Ashby, or similar). Read the board's public listing.
2. Record each open role in `jobs.csv`: `collect.mjs jobs <board-slug> --out jobs.csv` writes `title,department,location,posted,url,channels,function,source` from public Greenhouse, Lever, and Ashby boards. Add `tools` and `mandate` columns by hand as you read each full post; for boards it cannot reach, record the same columns manually.
3. Find past posts on Wayback (`web.archive.org/web/*/target.com/careers*`) and on job boards.
4. Save `jobs.csv` each month so Watch mode can spot new roles.

What to pull from each post:
- **The mandate:** "own our PLG motion", "scale programmatic SEO to 10,000 pages", "launch our creator program", "build our first outbound team". This is the plan, written down.
- **Numbers:** team size, targets, budgets ("manage $2M/year in paid").
- **Tools named:** the stack the team uses.
- **Reports to:** where the function sits.
- **First seen:** the date the post first appeared, which dates the push.

Add each mandate to `moves.csv` as `kind: hire`, with the posting date and `evidence` Observed (the post exists) for the role and Inferred for the strategy it implies.

For creators and personal brands, skip job posts. Log a publicly announced manager, label, agency, or editor hire as a move instead.
