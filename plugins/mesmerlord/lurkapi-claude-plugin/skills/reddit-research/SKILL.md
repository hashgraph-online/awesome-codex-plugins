---
name: reddit-research
description: Find out what real people say about a product, brand, competitor or problem on Reddit. Searches posts, finds the communities that discuss it, reads the most-discussed threads and their comments, then reports the pains, wants, objections, alternatives and exact phrases people use, with links. Use for voice-of-customer and market research, product validation, brand monitoring, "what does Reddit think of X", or before posting in a subreddit.
---

# Reddit research

What people really say about something when they aren't talking to the brand: their problems, what they've tried, what they recommend and the words they use. Every finding links to the thread it came from.

<!-- lurkapi:access -->
## Calling LurkAPI

**With MCP** (the LurkAPI plugin or connector), call the tools by name, like `tiktok_profile`; your client may prefix them (`mcp__plugin_lurkapi_lurkapi__tiktok_profile`). With only `find_endpoints` and `call_endpoint`, run a tool as `call_endpoint` with `endpoint` set to its name and `params` to its arguments. Results come trimmed: no nulls, one URL per image or video. A long result comes in parts: its `_note` gives the `offset` for the next part, which is free.

**Without MCP** (Codex, Cursor, scripts), every tool is `GET https://api.lurkapi.com` plus its path, with the same params as a query string (URL-encoded) and the key from `LURKAPI_API_KEY` in the `x-api-key` header:

```bash
curl -s "https://api.lurkapi.com/v1/tiktok/profile?handle=nike" -H "x-api-key: $LURKAPI_API_KEY"
```

If `LURKAPI_API_KEY` isn't set but `LURKAPI_KEY` is (the name older docs used), use that. Raw answers are big: pipe them through `jq` to keep the fields you need. No key yet? Ask the user to create one at https://lurkapi.com/dashboard (100 free credits on sign-up, then a balance below 25 tops back up to 25 every day) and to set `LURKAPI_API_KEY` in their shell. Never ask for the key in the chat, and never print it.

**Credits.** Each call costs what the table at the end says, `not_found` included; failures on our side (5xx) are free. Every answer carries `credits_remaining`. Before a run of more than 20 calls, check the balance with `account_credit_balance` (free) and tell the user what the run will cost. If a call answers `missing_api_key`, `insufficient_credits` or `signup_required`, stop and pass on what it says.
<!-- /lurkapi:access -->

## Run

1. **Search wide.** Start with the plain name: `reddit_search(query=<topic>, timeframe=year)`. Then one or two more phrasings, each short: the problem in the user's words ("<problem> recommendations"), "<competitor> alternative", "<x> vs <y>". Long queries, OR, and `sort=comment_count` drag in megathreads that only mention a word; drop any result whose title isn't about the topic. Results have `title`, `subreddit`, `score`, `num_comments`, `created_at_iso` and `permalink`, but no body text. Note which communities keep coming up. `sort=top` finds the classics; `sort=new` with `timeframe=month` what's current.
2. **Go where it's discussed.** In the one or two communities that recur, `reddit_subreddit_search(subreddit=<name>, query=<topic>, sort=comments)` finds the most argued-over threads. To size one up, or before posting there, `reddit_subreddit_details(subreddit=<name>)` gives `weekly_active_users` and its `rules`.
3. **Read the threads.** Pick 5 to 10 by `num_comments` and relevance, not score alone. `reddit_post_comments(url=<thread url>, trim=true)` returns the post (`post.title`, `post.selftext`) and its comments, best first, with replies nested. The thread URL is https://www.reddit.com plus the search result's `permalink` (subreddit search results carry a full `url`). When `more.has_more` is true on a rich thread, `more.next_cursor` as `cursor` loads the next batch.
4. **Write it up** (below).

## Budget

Three searches and eight threads is about 11 calls; a deep look at one community adds two or three. Stay under about 25 calls unless the user wants more, and say so before going further.

## What to pull out

Read for these, and count how many threads each theme shows up in:

- **Pains:** what people are stuck on, in their words.
- **What they've tried:** products and workarounds named, and what they liked or hated about each.
- **Recommendations:** what the community steers people toward, and why.
- **Objections:** price, trust, switching cost, missing features.
- **Triggers:** what made someone go looking.
- **Language:** phrases that recur, worth reusing in copy.

## Report

```markdown
# Reddit research: <topic>, <date>

<n> threads read across r/<a>, r/<b>, … from <searches run>.

## Themes
| Theme | Threads | Representative quote |
| --- | --- | --- |

## Alternatives people mention
| Product | Said for it | Said against it |

## Exact phrases
- "<verbatim>" ([thread](<url>))

## What this means
3 to 5 takeaways for the user's goal.

## Sources
- [<thread title>](<url>), r/<subreddit>, <score> points, <comments> comments
```

## Pitfalls

- Search covers post titles and text, not comments: phrase queries the way people title posts.
- A loud thread is one sample. Report how many threads a theme appears in, not just the best quote.
- Upvotes measure agreement in that community, not the market.
- Quote content, not people: link threads and leave usernames out unless the user needs them.
- Deleted and removed posts answer `not_found`, and still cost a call.

<!-- lurkapi:calls -->
## Calls and credits

| Tool | REST path | Credits |
| --- | --- | --- |
| [`reddit_search`](https://lurkapi.com/docs/reddit/search.md) | `/v1/reddit/search` | 1 credit |
| [`reddit_subreddit_search`](https://lurkapi.com/docs/reddit/subreddit-search.md) | `/v1/reddit/subreddit/search` | 1 credit |
| [`reddit_subreddit_details`](https://lurkapi.com/docs/reddit/subreddit-details.md) | `/v1/reddit/subreddit/details` | 1 credit |
| [`reddit_post_comments`](https://lurkapi.com/docs/reddit/post-comments.md) | `/v1/reddit/post/comments` | 1 credit |

Each tool's link opens its docs as markdown: every param and its values, and a real response.
<!-- /lurkapi:calls -->
