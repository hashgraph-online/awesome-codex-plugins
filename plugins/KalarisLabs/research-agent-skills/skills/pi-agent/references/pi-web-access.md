# pi-web-access Package

Source: https://pi.dev/packages/pi-web-access

Web search, content extraction, GitHub repo cloning, PDF conversion, YouTube and local-video understanding for Pi.

```bash
pi install npm:pi-web-access
```

Works with no API keys — Exa MCP provides zero-config search, OpenAI search can reuse Codex auth from `/login`, and DuckDuckGo HTML search is keyless (explicit-only). Optional binaries for frame extraction: `brew install ffmpeg` (frames, thumbnails, local video duration) and `brew install yt-dlp` (YouTube stream URLs). Without them, transcripts and Gemini-based analysis still work.

## Tools

### web_search

Searches via OpenAI, Brave, Parallel, TinyFish, Search1API, Searchinfinity, Querit, Tavily, Jina, SERPdive, Kagi, Bocha, Ollama, AnySearch, xAI, Bright Data SERP, SerpBase, self-hosted SearXNG, keyless DuckDuckGo, Exa, Perplexity, or Gemini, and returns a synthesized answer with citations.

```javascript
web_search({ query: "TypeScript best practices 2025" })
web_search({ queries: ["query 1", "query 2"], workflow: "auto-summary" })
web_search({ query: "latest news", numResults: 10, recencyFilter: "week" })
web_search({ query: "...", domainFilter: ["github.com", "-old.example.com"], provider: "openai" })
web_search({ query: "...", provider: "all" })
web_search({ query: "...", provider: ["brave", "exa"] })
```

Parameters: `query`/`queries`, `numResults` (default 5, max 20), `recencyFilter` (`day`/`week`/`month`/`year`), `domainFilter` (prefix `-` to exclude), `provider`, `includeContent`, `workflow` (`none`, `summary-review` default, `auto-summary`).

In `auto` mode the fallback order is configured SearXNG → OpenAI (when suitable and available) → Exa (direct API if keyed, MCP if not) → Brave → Parallel → TinyFish → Search1API → Searchinfinity → Querit → Tavily → Jina → SERPdive → Perplexity → Gemini API → Gemini Web (only with browser cookies enabled). DuckDuckGo, AnySearch, xAI, Bright Data, and SerpBase are explicit-only and never auto-selected.

`provider: "all"` runs the same query against every eligible provider simultaneously, excluding the explicit-only ones (Bright Data and SerpBase are paid Google SERP providers, so `all` never spends on them). Exa participates through its zero-config MCP path and OpenAI can use Pi auth; browser-cookie access alone does not opt Gemini in. Successful answers are preserved separately while source URLs and inline content are deduplicated, and one provider failure does not discard the rest; if every provider fails, per-provider diagnostics are returned. In the curator, **All** is selectable like any provider — each participant gets its own result card with a provider badge and checkbox, failures get a disabled error card, and the summary is generated from the selected cards. `provider` also accepts a non-empty array of named providers, which run concurrently through the same aggregation path (`"auto"` and `"all"` are invalid inside arrays, and `"all"` is invalid inside `searchRouting.providers`).

### fetch_content

Fetches URLs or local files as readable markdown, exact textual HTTP bodies, direct images, or page-grounded answers, auto-detecting GitHub repos, YouTube videos, PDFs, local video files, images, and regular pages.

```javascript
fetch_content({ url: "https://example.com/article" })
fetch_content({ urls: ["url1", "url2"] })
fetch_content({ url: "https://github.com/owner/repo" })
fetch_content({ url: "https://youtube.com/watch?v=abc", prompt: "What libraries are shown?" })
fetch_content({ url: "/path/to/recording.mp4", prompt: "What error appears on screen?" })
fetch_content({ url: "...", timestamp: "23:41-25:00", frames: 4 })
fetch_content({ url: "https://example.com/api", mode: "raw" })
fetch_content({ url: "https://example.com/guide", mode: "answer", prompt: "What are the installation steps?" })
```

Parameters: `url`/`urls`, `prompt` (video question, or the page-local question required by `mode: "answer"`), `mode` (`readable` default, `raw`, `answer`), `answerModel` (optional `provider/model-id` for answer mode; defaults to the current enabled Pi model), `timestamp` (single `"23:41"`, range `"23:41-25:00"`, or bare seconds), `frames` (max 12), `forceClone` (clone GitHub repos over the 350 MB threshold).

Raw and direct-image requests use the same SSRF validation, hostname domain policy, redirect checks, timeout, and 5 MB streamed response bound as normal extraction. Raw mode returns textual bodies even for non-2xx responses (HTTP status is in tool details) and runs no readability or hosted-extraction fallbacks.

### get_search_content

Retrieves stored content from previous searches or fetches.

```javascript
get_search_content({ responseId: "abc123", urlIndex: 0 })
get_search_content({ responseId: "abc123", url: "https://...", offset: 30000 })
get_search_content({ responseId: "abc123", urlIndex: 0, findText: "installation" })
get_search_content({ responseId: "abc123", urlIndex: 0, findText: ["timeout", "retry"], findMode: "fuzzy" })
```

Fetched content is stored in full in a private `web-search-cache` directory under the Pi config directory — not in the session JSONL — including the original page behind `fetch_content` answer mode. The cache has a one-hour lifetime with fixed limits of 128 entries and 128 MiB, evicting oldest first; on macOS/Linux the directory is `0700` and files are `0600`. `findText` locates bounded matching passages without paging (`findMode` is `exact`, `case-insensitive` default, or `fuzzy`; output capped at 20,000 characters with match counts and nearby context) and cannot be combined with `offset`/`limit`. The default and maximum `limit` come from `maxInlineContentChars`.

### source_check

Checks a claim and returns a machine-readable artifact with exact passage citations.

```javascript
source_check({ claim: "The API supports streaming responses",
  queries: ["API streaming documentation"], fetchContent: true, domainFilter: ["docs.example.com"] })
```

Results are deduplicated and capped at 20 sources; `fetchContent` fetches at most 5 pages, and stored/retrieved content stays within the configured `maxInlineContentChars` `offset`/`limit` bounds. The artifact carries claim status (`supported`, `contradicted`, `unclear`, `missing-evidence`), source-quality hints, SHA-256 content hashes, and passage IDs with exact source offsets. Search and fetch errors stay in the artifact instead of being discarded. Artifacts are stored with the session and retrieved through `get_search_content` by `responseId`.

## Capabilities

- **GitHub repos** are cloned locally instead of scraped: root URLs return the tree plus README, `/tree/` paths return directory listings, `/blob/` paths return file contents, and the agent gets a local path to explore with `read`/`bash`. Repos over 350 MB use a lightweight API view (override with `forceClone`). Commit-SHA URLs go through the API. Clones are cached per session and wiped on session change; private repos need the `gh` CLI. Setting `githubClone.enabled: false` only skips the clone/API specialization — `fetch_content` still handles the URL through normal extraction.
- **YouTube** via Gemini: visual descriptions, timestamped transcripts, chapter markers, and the thumbnail. Fallback: Gemini Web (cookies enabled) → Gemini API → Perplexity (text only). Handles `/watch?v=`, `youtu.be/`, `/shorts/`, `/live/`, `/embed/`, `/v/`.
- **Local video** (`/`, `./`, `../`, or `file://`): MP4, MOV, WebM, AVI and other common formats up to 50 MB for Gemini analysis; a thumbnail frame is included when ffmpeg is present. Timestamp/frame extraction uses ffmpeg directly and works on larger files.
- **PDFs** are converted to Markdown and saved under the temporary `pi-web-pdf` directory so the agent can `read` sections — see below.
- **Blocked pages**: Readability (plus declared `Link`/`rel` discovery) → Next.js RSC flight-data parser → configured Firecrawl → third-party hosted fallbacks, which stay disabled for remote HTTP(S) targets unless `fetchRouting.allowRemoteHostedProviders` is enabled.

### PDF conversion

Three engines, selected with `pdf.provider` (`"auto"` default):

| Provider | Engine | Trade-offs |
|---|---|---|
| `datalab` | Datalab hosted conversion (Marker) | Deterministic layout-aware output — tables, multi-column reading order, headings, math; `accurate` mode handles scanned pages; may return `parse_quality_score` (0–5); requires a Datalab key, billed per page with a free monthly credit |
| `gemini` | Gemini API (vision LLM) | Best on scanned/complex pages; LLM transcription can drift or truncate; requires a Gemini key |
| `unpdf` | Local pdf.js text extraction | Free, offline, no key; flattened text only — no layout, tables, or OCR |

`auto` order: Datalab (when keyed) → Gemini (when keyed) → local `unpdf`, continuing down the chain on failure including exhausted free credit. Pinning a provider skips the other remote tiers but still falls back to `unpdf` on error (except credential/config errors and caller cancellation). No Datalab key simply skips that tier.

Datalab pricing is per processed page: fast/balanced $4 per 1,000 pages, accurate $10 per 1,000. The free tier gives a $10 monthly credit (personal email; $20 with a work email) at 25 requests/minute — roughly 2,500 pages/month free in `fast` mode. Processing defaults to the US region; EU data residency costs 1.25× usage via `DATALAB_PROCESSING_LOCATION=eu`. Like the Gemini tier, PDF bytes are uploaded to the cloud and deleted best-effort after conversion.

```jsonc
{
  "datalabApiKey": "$DATALAB_API_KEY",
  "pdf": { "enabled": true, "maxSizeMB": 20, "provider": "auto",
           "datalabMode": "balanced", "datalabTimeoutMs": 120000 }
}
```

Env vars: `DATALAB_API_KEY`, `DATALAB_PROCESSING_LOCATION`, `DATALAB_MODE`, `DATALAB_API_BASE`. `pdf.datalabMode` overrides `DATALAB_MODE`; `datalabTimeoutMs` defaults to 120s and is capped at 300s. `pdf.maxSizeMB` defaults to 20 and is capped at 50.

## Commands

```text
/websearch [queries]            # open the curator; comma-separated pre-fill
/curator [on|off|summary-review]
/search                         # browse stored session results
/google-account                 # active Google account for Gemini Web
```

`Ctrl+Shift+W` toggles a live activity monitor of request/response data. Results are injected when you approve the curator summary or send selected results without one; on timeout the curator auto-submits with a deterministic fallback summary. If a browser cannot be opened (Docker, WSL, SSH, headless), the curator URL appears in the tool output.

### Remote curator access

By default the curator HTTP server binds `127.0.0.1` and hands out `http://localhost:<port>/?session=<token>`. Opt in to remote access when Pi runs somewhere other than your browser:

| `curatorRemote` value | URL host | Bind address |
|---|---|---|
| omitted or `false` | `localhost` | `127.0.0.1` |
| `true` | `os.hostname()` | `0.0.0.0` |
| `{ "host": "h" }` | `h` | `0.0.0.0` |
| `{ "bind": "b" }` | `os.hostname()` | `b` |
| `{ "host": "h", "bind": "b" }` | `h` | `b` |

Anything else (a string, `null`, an array) is treated as unconfigured and stays local. `host` only changes the printed URL; `bind` determines who can reach the server — set a matching pair, and prefer one private-network interface over `0.0.0.0`. **Security**: the only access control is the unguessable session token, carried over plain HTTP with no TLS, so anyone observing the traffic or reaching the port with the token can run searches against your configured providers (spending your credits) and edit the summary returned into the agent's context. Remote sessions print the URL instead of opening a browser and raise the default curator idle timeout from 20 to 60 seconds; set `autoOpenBrowser: true` to launch a browser on the remote host anyway. `autoOpenBrowser: false` is also useful locally — it always prints the URL instead of opening Glimpse or a browser, and changes nothing about binding.

## Configuration

Config defaults to `~/.pi/web-search.json`, or `web-search.json` under `PI_CODING_AGENT_DIR` / `XDG_CONFIG_HOME/pi`. Every field is optional. Config changes require a Pi restart.

```json
{
  "openaiApiKey": "sk-...",
  "openaiResponsesUrl": "https://gateway.example.com/v1/responses",
  "braveApiKey": "BSA_...",
  "exaApiKey": "exa-...",
  "parallelApiKey": "...",
  "tinyfishApiKey": "sk-tinyfish-...",
  "search1apiApiKey": "...",
  "searchinfinityApiKey": "...",
  "queritApiKey": "...",
  "tavilyApiKey": "tvly-...",
  "jinaApiKey": "$JINA_API_KEY",
  "serpdiveApiKey": "sd_live_...",
  "serpdiveModel": "krill",
  "kagiApiKey": "$KAGI_API_KEY",
  "bochaApiKey": "sk-...",
  "ollamaApiKey": "$OLLAMA_API_KEY",
  "serpbaseApiKey": "$SERPBASE_API_KEY",
  "brightdataApiKey": "$BRIGHTDATA_API_KEY",
  "brightdataSerpZone": "pi_serp",
  "brightdataUnlockerZone": "pi_unlocker",
  "perplexityApiKey": "pplx-...",
  "geminiApiKey": "AIza...",
  "geminiBaseUrl": "https://my-gateway.example.com/gemini",
  "cloudflareApiKey": "...",
  "datalabApiKey": "$DATALAB_API_KEY",
  "searxngBaseUrl": "https://search.example.com",
  "searxngHeaders": { "CF-Access-Client-Id": "...", "CF-Access-Client-Secret": "..." },
  "firecrawlBaseUrl": "https://crawl.example.com",
  "firecrawlApiKey": "fc-...",
  "firecrawlApiVersion": "v2",
  "firecrawlFreshScrape": false,
  "provider": "openai",
  "searchRouting": { "providers": ["openai", "brave", "exa"],
                     "fallbackOn": ["transient", "quota", "network", "invalid-response"] },
  "fetchRouting": { "providers": ["http", "firecrawl", "jina", "tinyfish", "search1api",
                                  "querit", "kagi", "ollama", "parallel", "brightdata", "gemini"],
                    "allowRemoteHostedProviders": false },
  "tools": { "webSearch": { "enabled": true }, "sourceCheck": { "enabled": true },
             "fetchContent": { "enabled": true }, "getSearchContent": { "enabled": true } },
  "commands": { "websearch": { "enabled": true }, "curator": { "enabled": true },
                "search": { "enabled": true }, "google-account": { "enabled": true } },
  "image": { "enabled": true },
  "toolNames": { "webSearch": "web_search", "sourceCheck": "source_check", "fetchContent": "fetch_content", "getSearchContent": "get_search_content" },
  "searchModel": "gemini-3.6-flash",
  "summaryModel": "anthropic/claude-haiku-4-5",
  "summaryGenerationDeadlineMs": 30000,
  "maxInlineContentChars": 30000,
  "workflow": "summary-review",
  "curatorTimeoutSeconds": 20,
  "curatorRemote": { "host": "my-box.tailnet.ts.net", "bind": "100.101.102.103" },
  "autoOpenBrowser": true,
  "chromeProfile": "Profile 2",
  "allowBrowserCookies": false,
  "githubClone": { "enabled": true, "maxRepoSizeMB": 350, "cloneTimeoutSeconds": 30, "clonePath": "/tmp/pi-github-repos" },
  "youtube": { "enabled": true, "preferredModel": "gemini-3.6-flash" },
  "video": { "enabled": true, "preferredModel": "gemini-3.6-flash", "maxSizeMB": 50 },
  "pdf": { "enabled": true, "maxSizeMB": 20, "provider": "auto" },
  "fetchContent": { "domainPolicy": { "allow": ["example.com"], "deny": ["blocked.example.com"] } },
  "shortcuts": { "curate": "ctrl+shift+s", "activity": "ctrl+shift+w" },
  "ssrf": { "allowRanges": ["198.18.0.0/15"], "trustEnvProxy": false }
}
```

**Credential sources** (provider API-key fields only — including `tinyfishApiKey`, `search1apiApiKey`, `searchinfinityApiKey`, `queritApiKey`, `jinaApiKey`, `kagiApiKey`, `bochaApiKey`, `ollamaApiKey`, `serpbaseApiKey`, `xaiApiKey`, `brightdataApiKey`, `datalabApiKey`): `$NAME` / `${NAME}` reads one env var; a leading `!` runs a trusted local command at provider request time; `$$` and `$!` escape literal prefixes. Commands never run at load or tool registration — each selected provider request re-runs them with a 5-second timeout, 16 KiB output limit, minimized environment, and one-line non-empty stdout requirement (`OP_SESSION_*` is forwarded for 1Password). An explicit source overrides legacy env vars and fails that provider locally rather than falling back on a stale credential. Non-credential fields (`firecrawlBaseUrl`, `firecrawlApiVersion`, `firecrawlFreshScrape`, `brightdataSerpZone`, `brightdataUnlockerZone`) are literal.

**Legacy env vars** (lower precedence than an explicit source, higher than literal config values): `OPENAI_API_KEY`, `BRAVE_API_KEY`, `PARALLEL_API_KEY`, `TINYFISH_API_KEY`, `SEARCH1API_KEY`, `SEARCHINFINITY_API_KEY`, `QUERIT_API_KEY`, `TAVILY_API_KEY`, `JINA_API_KEY`, `SERPDIVE_API_KEY`, `KAGI_API_KEY`, `BOCHA_API_KEY`, `OLLAMA_API_KEY`, `SERPBASE_API_KEY`, `ANYSEARCH_API_KEY`, `XAI_API_KEY`, `BRIGHTDATA_API_KEY`, `FIRECRAWL_API_KEY`, `EXA_API_KEY`, `GEMINI_API_KEY`, `DATALAB_API_KEY`, `PERPLEXITY_API_KEY`, `GOOGLE_GEMINI_BASE_URL`, `CLOUDFLARE_API_KEY`. Also `SEARXNG_BASE_URL`, `FIRECRAWL_BASE_URL`, `FIRECRAWL_API_VERSION`, `FIRECRAWL_FRESH_SCRAPE`, `SERPDIVE_MODEL`, `PI_ALLOW_BROWSER_COOKIES`.

**Routing**: `provider` (or `searchProvider`) sets the default and takes precedence over `searchRouting`. `searchRouting` opts into an ordered `providers` list plus `fallbackOn` (`transient`, `quota`, `network`, `invalid-response`) — only those typed failures continue to the next candidate. Named providers stay strict and exhausted routes return per-provider diagnostics. `fetchRouting.providers` reorders or restricts the `fetch_content` chain (`http`, `firecrawl`, `jina`, `tinyfish`, `search1api`, `querit`, `kagi`, `ollama`, `parallel`, `brightdata`, `gemini`); when absent the default order is unchanged. Third-party hosted fetchers are disabled for remote HTTP(S) targets unless `fetchRouting.allowRemoteHostedProviders: true`, because a hosted service performs its own fetch and can see a different redirect chain than the local safety gate.

**Enabling and naming tools**: set `"enabled": false` under `tools`, `commands`, `image`, or `pdf` to disable a feature. Tool-specific settings override the legacy `webSearch.enabled` shorthand, which otherwise still disables `web_search` and `source_check`. `image.enabled: false` blocks direct image fetches, video frame extraction, and thumbnails; `pdf.enabled: false` blocks PDF extraction. `toolNames` renames the public tools where the defaults collide. Tool and command registration changes need a Pi restart.

**Models**: `searchModel` overrides only the Gemini API model used for search (default `gemini-3.6-flash`); Gemini Web browser-cookie fallback has its own `gemini-3.1-pro` default, and explicitly configured unsupported Web models fail rather than silently downgrading. `openaiSearchModel` pins the OpenAI `web_search` model verbatim (bypassing automatic newest-terra selection, so gateway-only ids work), and `xaiSearchModel` does the same for xAI. `openaiResponsesUrl` points OpenAI `web_search`/`source_check` at a third-party Responses-compatible gateway (default `https://api.openai.com/v1/responses`). `summaryModel` sets the curator/`auto-summary` draft model, resolving through routed provider registrations such as OpenRouter when the native provider is unavailable; when Pi's `enabledModels` is configured, summaries are limited to that allowlist and fall back to a deterministic summary rather than calling an unrelated model. `summaryGenerationDeadlineMs` bounds one summary attempt (default 30000, capped at 600000). `maxInlineContentChars` sets the direct `fetch_content` slice plus the default and maximum `get_search_content` slice (default 30000, capped at 200000; full content stays stored for later retrieval).

**Security**: `fetchContent.domainPolicy` is an optional hostname allow/deny policy checked before HTTP(S) handling and each redirect this extension follows — bare hostnames match subdomains, `deny` wins, and local/non-HTTP sources are exempt. It adds to, not replaces, the SSRF guard. `ssrf.allowRanges` exempts specific CIDRs (for TUN + fake-IP proxies such as Surge/Clash/Mihomo/Stash); it is off by default and all-address CIDRs are rejected. `ssrf.trustEnvProxy` skips local DNS preflight for proxied hostnames only, still blocking localhost, literal private IPs, and `NO_PROXY` matches. Firecrawl requests are cache-only (`lockdown: true`) unless `firecrawlFreshScrape` is set — only enable that for an isolated Firecrawl deployment, since this extension cannot control the Firecrawl server's own egress.

## Provider Notes

**SearXNG**: `searxngBaseUrl` / `SEARXNG_BASE_URL` enables a self-hosted JSON API, preferred first in `auto` mode. Its base URL and redirects remain subject to the SSRF guard — add only the narrowest self-hosted range to `ssrf.allowRanges` when it resolves privately. Optional `searxngHeaders` merges extra HTTP headers (string values only; invalid names ignored) for reverse-proxy or Zero Trust auth such as Cloudflare Access service tokens, overriding the default `Accept: application/json` when the same name is supplied.

**SERPdive**: `serpdiveModel` picks retrieval depth: `krill` (free default, extracted page content, answer assembled from sources), `mako` (1 credit, fact-carrying sentences plus synthesized answer), `moby` (1.5 credits, full readable content plus cited answer). Unrecognized values fall back to `krill` so a typo cannot cost money. SERPdive has no time-range or domain parameter, so `recencyFilter` is a ranking hint appended to the question and `domainFilter` is applied locally; `numResults` maps to `max_results`, a cap between 1 and 10.

**Jina**: `jinaApiKey` / `JINA_API_KEY` enables [Jina Search](https://s.jina.ai); in `auto` mode it runs after Tavily and before SERPdive. `numResults` maps to its bounded `count`, included domains become `site` filters, and excluded domains plus recency go into the query. Without `includeContent` it requests SERP metadata only; with it, Jina visits pages and returns Markdown inline (slower, more tokens). Jina Reader remains a `fetch_content` fallback.

**TinyFish**: `tinyfishApiKey` / `TINYFISH_API_KEY` enables the Search and Fetch APIs (endpoints are built in). In `auto` mode it runs after Parallel and before Search1API. Supports `numResults`, `recencyFilter`, and include/exclude domain filters, paginating above 10 results; with `includeContent`, URLs go to TinyFish Fetch in batches of up to 10. TinyFish Fetch is also a `fetch_content` fallback after Jina Reader. Both APIs are documented as credit-free with Free-plan limits of 30 searches/minute and 150 fetched URLs/minute.

**Search1API**: `search1apiApiKey` / `SEARCH1API_KEY` enables Search and Crawl; in `auto` mode it runs after TinyFish and before Searchinfinity. `includeContent` maps to Deep Search and returns crawled result content inline. Credit-based: a basic search is 1 credit, Deep Search adds 1 per successfully crawled page, and a Crawl request is 1 — Deep Search is never enabled unless `includeContent` is true. The Crawl endpoint is a `fetch_content` fallback after Jina Reader and TinyFish.

**Searchinfinity**: `searchinfinityApiKey` / `SEARCHINFINITY_API_KEY` enables Byteplus Searchinfinity (the Global edition of Volcengine 豆包搜索); in `auto` mode it runs after Search1API and before Querit.

**Kagi**: `kagiApiKey` / `KAGI_API_KEY` enables Kagi Search as a normal configured provider, mapping `numResults` to Kagi's `limit`; when Kagi includes extracted Markdown, `includeContent` exposes it inline. Kagi Extract is a `fetch_content` fallback after Querit and before Ollama/Parallel, with local target validation and authorization stripped across cross-origin API redirects.

**Ollama**: `ollamaApiKey` / `OLLAMA_API_KEY` enables Ollama Cloud Web Search without a local daemon — the same account key used for Cloud inference authenticates `POST https://ollama.com/api/web_search`, with `numResults` capped at Ollama's documented max of 10. Ollama Web Fetch is a `fetch_content` fallback after Kagi and before Parallel.

**DuckDuckGo**: keyless and explicit-only — select `provider: "duckduckgo"` or place it in `searchRouting`; it is never chosen by `auto` and never participates in `provider: "all"`. Domain filters are enforced locally after redirect URLs are decoded, and `recencyFilter` is not guaranteed because the HTML endpoint has no documented stable time parameter. A 200 page with no parseable results is reported as an invalid response.

**Bright Data**: `brightdataApiKey` / `BRIGHTDATA_API_KEY` plus a zone. The SERP provider needs `brightdataSerpZone` (a zone of type `serp`); the Web Unlocker extraction fallback needs `brightdataUnlockerZone` (type `unblocker`). The zones are never substituted for each other, so enabling one product does not opt into the other. Search is explicit-only, maps domain filters to Google `site:` clauses and recency to `tbs`, validates the returned SERP envelope, and surfaces provider errors rather than converting them to empty results — every billed `200` that cannot be read throws instead of reporting zero results, and quoted upstream text cannot impersonate a status or rate-limit phrase. Web Unlocker runs last of the remote scraping providers, ahead of only the Gemini fallbacks, and applies no minimum-length check — any non-empty body it returns (including a short consent or paywall stub) is final for that URL. Keep `brightdataUnlockerZone` unset for URLs that must not be disclosed to a third party.

**SerpBase**: `serpbaseApiKey` / `SERPBASE_API_KEY` with `provider: "serpbase"` queries SerpBase's Google Search Results API. Explicit-only, because each request can consume paid Google SERP credits. Domain filters become Google `site:` clauses (reapplied locally) and recency maps to `tbs`.

**Gemini gateway**: `geminiBaseUrl` / `GOOGLE_GEMINI_BASE_URL` overrides the Gemini API host (bare host, no trailing slash or version segment). When the host contains `gateway.ai.cloudflare.com`, auth uses `cf-aig-authorization: Bearer <token>` from `cloudflareApiKey`/`CLOUDFLARE_API_KEY` and `GEMINI_API_KEY` is not required for generate-content calls — but local video upload still uses Google's Files API directly.

## Limits and Limitations

Perplexity is capped at 10 requests/minute client-side; Jina Search, TinyFish, Search1API, and Searchinfinity apply their documented plan limits, and Querit Search and Contents subscriptions are independent. Content fetches run 3 concurrent with a 30s timeout for the direct HTTP fetch of each URL; remote extraction fallbacks carry their own budgets — Jina Reader 30s, Firecrawl 60s, Kagi Extract 60s, Ollama Web Fetch 60s, Bright Data Web Unlocker 60s, TinyFish up to 150s, Gemini 120s, Datalab 120s (capped at 300s, 25 requests/minute on the free tier). Gemini handles videos up to ~1 hour; local video upload is 50 MB max. Chromium cookie extraction for Gemini Web is opt-in (`allowBrowserCookies: true` or `PI_ALLOW_BROWSER_COOKIES=1`) and may trigger a macOS Keychain dialog; cookie DBs are copied to a temporary read-only working copy. Private/age-restricted YouTube videos may fail on all paths, GitHub branch names with slashes may misresolve file paths, and non-code GitHub URLs (issues, PRs, wiki) fall through to normal web extraction.
