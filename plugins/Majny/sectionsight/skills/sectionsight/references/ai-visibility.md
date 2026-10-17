# AI visibility: assistants, crawlers and Search Console

Three questions an owner now asks, each answered from the totals, with no
visitor identified:

1. **Do AI assistants send people here?** Visits whose referrer or
   `utm_source` is ChatGPT, Perplexity, Claude, Gemini, Copilot and others
   (collector.mjs, no extra code).
2. **Do AI crawlers read the site, and which pages?** Requests by user agent,
   counted on the server (`assets/crawlers.mjs`).
3. **What do people search for on Google before they arrive?** Search Console's
   top queries and pages, pulled once a day (`assets/gsc.mjs`).

All three feed the weekly digest (`notifications.md`). Each is optional:
ask the owner which to wire (SKILL.md, step 2).

## 1. Visits from AI assistants

The collector maps referrer hosts and known `utm_source` values to one source
key per assistant, and `AI_SOURCES` groups them. The digest shows them as one
line, "AI assistants 60 (chatgpt 40, claude 20)", and goals by source count
them as the class `ai`.

| Source key | Referrer hosts | `utm_source` values |
|---|---|---|
| `chatgpt` | `chatgpt.com`, `*.openai.com`, app `com.openai.chatgpt` | `chatgpt.com`, `chatgpt`, `openai` |
| `perplexity` | `perplexity.ai`, `perplexity.com`, `pplx.ai`, app `ai.perplexity.app.android` | `perplexity.ai`, `perplexity` |
| `claude` | `claude.ai`, `claude.com`, app `com.anthropic.claude` | `claude.ai`, `claude` |
| `gemini` | `gemini.google.com`, `bard.google.com`, app `com.google.android.apps.bard` | `gemini` |
| `copilot` | `copilot.microsoft.com`, `*.copilot.cloud.microsoft` | `copilot`, `copilot.com` |
| `deepseek` | `chat.deepseek.com`, `deepseek.com`, app `com.deepseek.chat` | `deepseek` |
| `grok` | `grok.com` | `grok.com`, `grok` |
| `meta-ai` | `meta.ai` | `meta.ai` |
| `mistral` | `chat.mistral.ai`, `mistral.ai` | `mistral` |
| `you` | `you.com` | `you.com` |

**Why one key per assistant and a group, not one source "ai".** The owner
wants to know which assistant sends people, and the group is a sum. The
goal-by-source counters use the coarse class (`ai`) because they multiply
by the number of goals.

**What is missed.** Many assistant clicks arrive with no referrer at all
(the apps, links copied out of an answer, `rel="noreferrer"`) and count as
`direct`. Grok inside x.com cannot be told from X.

**`utm_source=chatgpt.com`.** OpenAI's publishers FAQ says ChatGPT adds it to
the referral URLs of its search results
([Publishers and developers FAQ](https://help.openai.com/en/articles/12627856-publishers-and-developers-faq),
checked 2026-10-09). Independent tests found it on citations but not on every
link ([Seer Interactive](https://www.seerinteractive.com/insights/are-ai-sites-like-chatgpt-sending-your-website-traffic)),
so treat it as one signal beside the referrer. k.js's `data-strip-utm="on"`
removes such tags from the address bar after reading them (`tracker.md`).

## 2. AI crawlers (`assets/crawlers.mjs`)

Crawlers run no JavaScript, so k.js never sees them. `countCrawler` runs in
the server, middleware or Worker that answers pages, after the response:

```text
crawl.<bot>.<2xx|3xx|4xx|5xx|unknown>   requests by answer class
crawlp.<bot>.<path>                     per page (up to 30 per bot per day, then (other))
```

both on the day's `"<day> *"` totals document. It never stores the IP, the
user agent or the query string. A path that is private (`skip`, the same
rule as the collector) or carries a token counts as `(other)`.

**The list.** `assets/crawlers-list.mjs` is a vendored snapshot of the
[ai.robots.txt](https://github.com/ai-robots-txt/ai.robots.txt) list (MIT;
its date and source URL are in the file), each entry with its name, a
short operator name and a purpose:

| Purpose | Meaning | Examples |
|---|---|---|
| `live` | **fetched live for an answer**: a user asked an assistant, which fetched the page then | ChatGPT-User, Claude-User, Perplexity-User, MistralAI-User |
| `agent` | an agent acting for a user | ChatGPT Agent, Claude-Code, Google-Agent, Devin |
| `search` | indexing for an AI search engine | OAI-SearchBot, PerplexityBot, Claude-SearchBot |
| `training` | collecting training data or datasets | GPTBot, ClaudeBot, CCBot, Bytespider |
| `other` | anything else, or unclear | Amazonbot, facebookexternalhit |

Refresh it with `node scripts/update-crawlers.mjs`: it takes the newest
commit that changed `robots.json` and records its hash in the file
(`CRAWLERS_SNAPSHOT.commit`; the vendored one is upstream commit 9ad8a47 of
2026-10-03). `--check` prints what would change; review the diff: the
purpose is derived from the list's own description text. Search engines'
ordinary crawlers (Googlebot, Bingbot) are not on it.

**Local overrides** (in `crawlers.mjs`, applied after the list, kept
across refreshes):

- `NOT_IN_USER_AGENTS`: names never matched in a user agent, with the
  reason: `Code` (VS Code and other Electron apps send `Code/1.95`),
  `Cursor` (the editor sends `Cursor/0.42`), `Trae` (the editor sends
  `Trae/1.x`), `Operator` (a common word),
  and `Google-Extended` and `Applebot-Extended` (robots.txt tokens only:
  Google's and Apple's crawlers never send them as user agents; blocking
  them in robots.txt is how an owner opts out of training, but they cannot
  be counted).
- `LOCAL_CRAWLERS`: entries to add or reclassify (`{ name, operator,
  purpose }`), empty by default.
- A user agent with `Electron/<version>` is never a crawler: it is a
  desktop app (an editor, a chat client) that a person uses.

Add to them when a name on the list turns out to match ordinary
software.

**Matching.** One precompiled regex, names as whole tokens, case-sensitive
as the list spells them (it lists both spellings where two are in use):
`NotGPTBot`, `GPTBotX` and `Sogou web spider` do not match. About 0.2 µs
for an ordinary browser's user agent; a request that is not a crawler
touches nothing.

**A user agent is a claim.** Anyone can send `GPTBot`. The counts say what
requests called themselves. Operators publish IP ranges for verification;
this code does not look at IPs, by design.

**On Cloudflare, prefer AI Crawl Control.** For a site behind Cloudflare
it already shows requests per AI crawler in the dashboard, from Cloudflare's
own bot detection rather than the user agent alone, and lets the owner
allow or block each one. Use `countCrawler` there only if the owner wants
the numbers in the digest. (This skill has not verified it against a live
account; check the zone's AI Crawl Control page.)

### Wiring

`countCrawler(request, store, { status, timeZone, skip })` always returns a
promise that never rejects; for any other request it resolves to `null`
without touching the store. Hand it to the runtime's "after the response"
hook so it never delays an answer:

```js
// Cloudflare Worker (or Pages middleware)
export default {
  async fetch(request, env, ctx) {
    const response = await handle(request, env);
    ctx.waitUntil(countCrawler(request, store(env), { status: response.status, timeZone: 'Europe/Berlin', skip: PRIVATE }));
    return response;
  },
};
```

```js
// Express / Node http: after the response is sent, with its status
app.use((req, res, next) => {
  res.on('finish', () => void countCrawler(req, store, { status: res.statusCode, timeZone: 'Europe/Berlin', skip: PRIVATE }));
  next();
});
```

```ts
// Next.js middleware.ts: it runs before the page, so the status is not known ("unknown")
import { NextResponse, type NextFetchEvent, type NextRequest } from 'next/server';
export function middleware(req: NextRequest, event: NextFetchEvent) {
  event.waitUntil(countCrawler(req, store, { timeZone: 'Europe/Berlin', skip: PRIVATE }));
  return NextResponse.next();
}
```

In a Next.js route handler or server component, `after(() => countCrawler(…))`
from `next/server` runs it after the response, with the status the handler
chose. The store is the collector's (any store with `write`; Analytics
Engine works too). With several instances the per-day path cap is per
instance.

## 3. Search Console (`assets/gsc.mjs`)

`gscDaily` runs once a day, pulls the day **3 days ago in Pacific Time**
(Search Console's days are Pacific days, and its data settles after 2–3
days), fetches again any of the 3 days before it that is missing or was
stored with no clicks and no impressions (a run before Google had the data,
or a missed run; at most 3 fetches per day, counted in the document's
`fetches`), and stores the top 50 queries and the top 50
pages of that day, plus the day's clicks and impressions, as one document
per day (`store.saveGsc`; memory, files, Mongo `web_gsc`, SQL `web_gsc`; not
Analytics Engine). They are kept **16 months** (`gscDays: 490` in
`enforceRetention`, a TTL in Mongo), as Search Console itself keeps them. The
digest shows the week's clicks and the queries whose clicks moved most.

- **No `googleapis` package.** It signs the service account's JWT with
  `node:crypto` (RS256), exchanges it for an access token, and calls
  `searchAnalytics.query` with the `webmasters.readonly` scope. `fetch` is
  injectable.
- **What it drops.** Google already omits rare ("anonymized") queries. A
  query that still looks personal (an e-mail, a phone number, a token:
  `looksPersonal`) and a page that is private or carries a token are
  dropped and counted in `hidden`. Pages are stored as paths, without the
  query.
- **Names are not caught.** A query like "jane doe" reads like any other
  words. Google's anonymisation of rare queries is the only guard against a
  person's name, and a name searched often enough passes it. Ask the owner
  whether the digest may list queries at all: `weeklyDigest({ gscQueries:
  false })` shows Search Console's totals only (the documents still hold
  the queries, for the owner's own reading).
- **The key** never appears in a log, an error or a return value. Errors
  name the HTTP status and Google's error code only.

**Setup (the owner):**

1. In Google Cloud, create a project (or use one), enable the **Google
   Search Console API**, create a service account and a JSON key for it. It
   needs no IAM role.
2. In Search Console, open the property, Settings → Users and permissions →
   Add user: the service account's e-mail (`…@….iam.gserviceaccount.com`),
   permission **Restricted** (read-only is all it needs).
3. Put the key file's content into an environment variable of the job
   (`GSC_SERVICE_ACCOUNT`), never into the repository.
4. `siteUrl` is the property exactly as Search Console names it:
   `sc-domain:example.com` for a domain property, or
   `https://www.example.com/` (with the trailing slash) for a URL prefix.

```js
import { gscDaily } from './gsc.mjs';
await gscDaily({ serviceAccount: process.env.GSC_SERVICE_ACCOUNT, siteUrl: 'sc-domain:example.com', store, skip: PRIVATE });
```

Schedule it like the retention job (once a day). Users of a hosted
analytics tool with its own Search Console integration (e.g. Plausible)
can connect Search Console there instead, which shows the queries in its
dashboard; then skip this file.

Search Console data is about Google's search results, not about visitors of
the site: it adds no line to the privacy page's list of what is measured.
