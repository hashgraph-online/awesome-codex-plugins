# Public Endpoints

> Tier 0: when the platform publishes its own endpoint, read the data there before touching the HTML.

## 1. Endpoint Index

| Platform | Endpoint | Probe 2026-11-07 | Notes |
|---|---|---|---|
| Bluesky | `https://public.api.bsky.app/xrpc/app.bsky.actor.getProfile?actor=<handle>`, `app.bsky.feed.getAuthorFeed?actor=<handle>&limit=<n>` | 200 | Profiles and feeds are public; search may need auth |
| Mastodon | `https://<instance>/api/v1/accounts/lookup?acct=<user>`, then `/api/v1/accounts/<id>/statuses` | not probed | Public timelines differ per instance |
| Hacker News | `https://hacker-news.firebaseio.com/v0/item/<id>.json`, `topstories.json`; search via `https://hn.algolia.com/api/v1/search?query=<q>` | 200 | No auth |
| Reddit | `<post or listing URL>.json` | 403 for desktop and mobile user agents; `old.reddit.com` answered 302 | Treat as unavailable without the official API and its OAuth; do not climb past a refusal that is a policy decision |
| X / Twitter | `https://syndication.twitter.com/srv/timeline-profile/screen-name/<handle>`; single post via `https://publish.twitter.com/oembed?url=<post URL>` | syndication 200; oEmbed 301 redirect | Follow the oEmbed redirect once and re-check the host |
| Wikipedia | `https://<lang>.wikipedia.org/api/rest_v1/page/summary/<title>`, `/page/html/<title>` | 200 | Send a descriptive user agent |
| arXiv | `https://export.arxiv.org/api/query?search_query=<q>&max_results=<n>` | 200 | Atom; at most one request every three seconds |
| Stack Exchange | `https://api.stackexchange.com/2.3/search?intitle=<q>&site=stackoverflow` | not probed | Anonymous quota per IP per day |
| CrossRef | `https://api.crossref.org/works?query=<q>` | not probed | Add `mailto` only when the user supplies an address |
| GitHub | `gh api repos/<owner>/<repo>` or `https://api.github.com/repos/<owner>/<repo>` | not probed | Anonymous rate limit is low; use the user's existing `gh` login only for their own request |
| npm / PyPI | `https://registry.npmjs.org/<pkg>`, `https://pypi.org/pypi/<pkg>/json` | PyPI 200 | No auth |
| Wayback | see `references/headless-recipes.md` §6 | 200 | Archive copies are tier 2 |
| YouTube and other media | `yt-dlp --dump-json` | not probed | Media extractor, `references/headless-recipes.md` §5 |
| Feeds | the page's `<link rel="alternate" type="application/rss+xml">` | not probed | A feed is the cleanest source for recent posts |

## 2. Rules for Endpoints

- An endpoint result is provenance `api`; name the endpoint path in the report.
- Positive proof for an endpoint is a documented key with a non-empty value (`displayName`, `title`, `extract`, `entry`).
- An endpoint that answers 401 or 403 for anonymous use is an authorization signal, not a client filter. Do not switch to scraping the HTML to get the same data around it; report it under `rules/access-policy.md` §2, or use the user's own credentials only when the user asked.
- Follow the documented rate limit, and the bulk gate for lists.
- Platform names here are an index of published endpoints, not site-specific scraping rules.

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| The endpoint list | The `ultimate-browsing` skill in `code-yeongyu/oh-my-openagent` (branch `dev`), read 2026-11-07 |
| Probe results | requests from this repository's network on 2026-11-07; results depend on the network and change without notice |
| arXiv request spacing | <https://info.arxiv.org/help/api/tou.html> |
| Bluesky public API host | <https://docs.bsky.app/docs/advanced-guides/api-directory> |
