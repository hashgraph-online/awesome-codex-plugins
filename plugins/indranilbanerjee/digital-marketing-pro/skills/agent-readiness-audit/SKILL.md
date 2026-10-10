---
name: agent-readiness-audit
description: "Audit agent readiness by script: AI-crawler rules, product schema, no-JS HTML, feeds. \"can AI agents use our site\""
argument-hint: "[site URL, or paths to robots.txt / HTML / feed exports]"
---

# /digital-marketing-pro:agent-readiness-audit

> **Script location.** If your host does not set `${CLAUDE_PLUGIN_ROOT}`, the scripts are in this plugin's `scripts/` folder, next to `skills/`.

## Purpose

Answer one question with evidence: **can AI agents and AI crawlers use this site?** Concretely, the audit checks five things:
- AI crawlers are allowed to reach the content.
- The content is in the HTML the server sends, so it does not depend on JavaScript running.
- Structured data says what the page is.
- The product feed is complete enough for AI shopping surfaces.
- Optionally, the site exposes agent tools (WebMCP).

Every check is deterministic and runs in `scripts/agent-readiness-audit.py`. The skill adds interpretation and the brand's policy decisions on top of the script's output; it never replaces that output with judgment.

## What the primary sources say (checked 2026-10-04)

From Google's [AI optimization guide](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide) (last updated 2026-07-10):
- **No special files.** Under the heading "Mythbusting generative AI search", Google lists "LLMS.txt files and other 'special' markup". It says "You don't need to create new machine readable files, AI text files, markup, or Markdown to appear in Google Search (including its generative AI capabilities), as Google Search itself doesn't use them." **This skill never recommends llms.txt for Google.**
- **Structured data:** "Structured data isn't required for generative AI search, and there's no special schema.org markup you need to add." The audit checks JSON-LD because it powers **rich results** (merchant listings, organization info), not because AI features require it.
- **JavaScript:** "Google is able to process content within JavaScript as long as it isn't blocked." The no-JS check is a robustness test: content that is already in the server HTML can be read by every crawler and agent, whether or not it runs JavaScript.
- **Agents:** browser agents may analyze screenshots, inspect the DOM structure, and interpret the accessibility tree. Hence the accessibility-basics check. Google names the Universal Commerce Protocol (UCP) as an emerging protocol.

### AI crawler tokens (each verified on the vendor's own page)

| Token | Vendor | Role in the audit | What blocking it means (vendor's words, paraphrased) | Source |
|---|---|---|---|---|
| `OAI-SearchBot` | OpenAI | search: **must be allowed** | Site not surfaced in ChatGPT search features | [OpenAI bots](https://developers.openai.com/api/docs/bots) |
| `ChatGPT-User` | OpenAI | user fetch: **must be allowed** | User-initiated visits. OpenAI: robots.txt "may not apply" to these | same |
| `OAI-AdsBot` | OpenAI | ads: **must be allowed** if the brand runs ChatGPT Ads | Validates the safety of pages submitted as ChatGPT ads | same |
| `GPTBot` | OpenAI | training: **policy** | Content excluded from foundation-model training | same |
| `Claude-SearchBot` | Anthropic | search: **must be allowed** | Content not indexed for Claude's search results | [Anthropic](https://support.claude.com/en/articles/8896518) |
| `Claude-User` | Anthropic | user fetch: **must be allowed** | Claude can't retrieve the page for a user's question. Anthropic honors robots.txt for all three of its bots | same |
| `ClaudeBot` | Anthropic | training: **policy** | Future content excluded from training datasets | same |
| `PerplexityBot` | Perplexity | search: **must be allowed** | Not surfaced or linked in Perplexity results (Perplexity says it is not used for model training) | [Perplexity bots](https://docs.perplexity.ai/guides/bots) |
| `Perplexity-User` | Perplexity | user fetch: **must be allowed** | Perplexity says this fetcher "generally ignores robots.txt rules" | same |
| `Google-Extended` | Google | training: **policy** | Controls use for Gemini training and grounding. It "does not impact a site's inclusion in Google Search nor is it used as a ranking signal", and it has no separate user-agent string | [Google crawlers](https://developers.google.com/crawling/docs/crawlers-fetchers/google-common-crawlers) |
| `Applebot-Extended` | Apple | training: **policy** | Controls use in Apple foundation-model training. It does not crawl, and pages that disallow it "can still be included in search results" | [Apple](https://support.apple.com/en-us/119829) |

"Policy" means that blocking training crawlers is the brand's choice. The audit reports it as info unless the brand sets `--training-policy allow|block`, in which case a mismatch fails the check.

## Inputs

All checks run **offline** on files the user exports. The script fetches over the network only with `--fetch`.

- **robots.txt**: `--robots FILE`, or `--site URL --fetch`. Add `--path /products/` (repeatable) to test the paths that matter, beyond `/`.
- **Server HTML**: `--html FILE` (repeatable). Save it as the server sends it, for example with `curl -L URL > page.html`, **not** "Save as" from a browser, which saves the post-JavaScript DOM. Add `--expect "Product name"` (repeatable) for text that must be in that HTML, such as a product name or price.
- **Merchant Center feed export**: `--feed FILE` (TSV, CSV, or RSS/Atom XML with `g:` attributes).
- **Agentic-commerce product feed (optional)**: `--acp-feed FILE`. Accepts the JSONL "OpenAI format" or the Google-compatible CSV/TSV ([spec](https://developers.openai.com/commerce/specs/file-upload/products)).
- **WebMCP (optional, experimental)**: `--webmcp`.
- **Brand policy**: `--training-policy either|allow|block`. The default, `either`, reports training-crawler rules without judging them.

## Process

1. **Load brand context.** Read `~/.claude-marketing/brands/_active-brand.json`, then `~/.claude-marketing/brands/{slug}/profile.json`.
   - From the profile, take the domain, whether the brand sells products (feed checks apply), and any stated AI-training policy (sets `--training-policy`).
   - If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" or proceed with the inputs the user gives.
2. **Collect inputs.** Ask for exports first. If the user only has a URL, confirm they want a live fetch before using `--fetch`.
3. **Run the audit.**
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/scripts/agent-readiness-audit.py" \
       --robots robots.txt --path /products/ \
       --html home.html --html product.html --expect "Acme Anvil" \
       --feed products.tsv --acp-feed openai-feed.jsonl --webmcp \
       --training-policy either --format json > "${CLAUDE_PLUGIN_DATA}/{brand}/seo/agent-readiness/{date}/02-audit.json"
   ```
   Live variant, used only when the user agreed to network access:
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/scripts/agent-readiness-audit.py" --site https://example.com --fetch \
       --page https://example.com/products/anvil --format json
   ```
   Exit codes:
   - `0`: no check failed (warnings allowed)
   - `1`: at least one check failed
   - `2`: bad input (nothing to audit, a missing or unparseable file, a bad flag)

   On `2`, fix the input and re-run. Do not interpret a partial run.
4. **Interpret each check.** Report the script's status per check: `pass`, `warn`, `fail`, `info` or `skipped`.
   - **robots_ai_crawlers**: a blocked search, user-fetch or ads bot is a **fail**. Name the bot and quote what blocking it costs, from the table above.
   - **structured_data**:
     - an unparseable JSON-LD block is a **fail**
     - a Product without `offers` is a **warn**, because merchant-listing rich results require name, image and offers ([Google](https://developers.google.com/search/docs/appearance/structured-data/merchant-listing))
     - no Organization markup anywhere is a **warn**
     - FAQPage is fine to keep, but Google shows FAQ rich results only for "well-known, authoritative government and health websites" ([Google](https://developers.google.com/search/docs/appearance/structured-data/faqpage))
   - **no_js_render**: a **fail** when visible text is below the floor (`--min-text`, default 250 characters), when an app-shell root (`#root`, `#__next`, `#app`, ...) holds little text, or when an `--expect` phrase is missing from the server HTML.
   - **accessibility_basics**: **warn** only. Covers a missing `<html lang>`, images without alt, unlabelled inputs, and unnamed buttons.
   - **merchant_feed**:
     - **Fail** conditions:
       - any required attribute is missing: `id`, `title`, `description`, `link`, `image_link`, `availability`, `price` ([product data spec](https://support.google.com/merchants/answer/7052112))
       - an `availability` value is outside `in_stock`, `out_of_stock`, `preorder`, `backorder`
       - a `native_commerce(checkout_eligibility)` value is not TRUE/FALSE
     - **`native_commerce`**: report how many products opt into checkout on Google. Only listings with `native_commerce(checkout_eligibility)` = TRUE show the "Buy" button. The feature is for select merchants, with products eligible in the US, Canada and Australia ([Merchant Center help](https://support.google.com/merchants/answer/16837055); [UCP guide](https://developers.google.com/merchant/ucp/guides/merchant-center)). The account-level return policy and customer-support contact can't be checked from a feed, so list them as manual checks.
     - **Conversational attributes** (`question_and_answer`, `document_link`, `related_product`, `item_group_title`, `variant_option`, `popularity_rank`) are optional ([help](https://support.google.com/merchants/answer/17085370)). Report their coverage; never fail on them.
   - **acp_feed**: optional. If supplied, missing required fields are a **fail**. Report the `is_eligible_search` / `is_eligible_checkout` counts.
   - **webmcp**: always `info`. WebMCP is a Chrome origin trial (from Chrome 149) and "under active discussion and subject to change" ([Chrome docs](https://developer.chrome.com/docs/ai/webmcp)). Report the declarative `toolname` / `tooldescription` forms and the inline `registerTool` calls found. Recommend nothing beyond "optional experiment".
5. **Decide policy questions with the user, not for them.** Two are the brand's call: whether to block training crawlers, and whether to opt products into checkout on Google. Present the trade-off and the source.
6. **Prioritize fixes.** Use the script's `recommendations` array as the backbone.
   - Order by impact: blocked answer engines → content missing from server HTML → broken JSON-LD → feed required attributes → everything else.
   - Route the work: rendering to `/digital-marketing-pro:tech-seo-audit`, markup to `/digital-marketing-pro:entity-audit`, and visibility follow-up to `/digital-marketing-pro:aeo-geo`.

## Numbered output convention

All outputs go to `${CLAUDE_PLUGIN_DATA}/{brand}/seo/agent-readiness/{YYYY-MM-DD}/`:

```
00-input.md            domain, which exports were supplied, fetch yes/no, training policy
01-inputs/             the robots.txt, HTML and feed files actually audited (for reproducibility)
02-audit.json          raw script output
03-findings.md         per-check status, findings, sources (with the 2026-10-04 check date)
04-policy-decisions.md training-crawler stance, checkout opt-in decision — with rationale
05-fix-plan.md         prioritized fixes with owners and the skill each routes to
PLAN.md                one-page summary: verdict, top 3 fixes, re-audit date
```

## Quality scorecard

| Gate | Pass when |
|---|---|
| **script_ran_clean** | Exit code 0 or 1 (never 2). A `2` means the inputs were wrong, not the site |
| **inputs_are_server_html** | `00-input.md` states the HTML was captured as served (curl or `--fetch`), not from a browser's saved DOM |
| **sources_cited** | Every finding in `03-findings.md` carries the source URL from the script output or this skill |
| **policy_explicit** | `04-policy-decisions.md` records the training-crawler stance and checkout opt-in as the brand's decisions |
| **no_llms_txt_for_google** | Nothing in the deliverable recommends llms.txt as a Google visibility lever |

## Output

- **Verdict**: `ready` (no warnings or failures), `needs_work` (warnings only), or `not_ready` (any failure). Experimental and skipped checks do not count.
- **Crawler access table**: every token, its role, `allowed` / `partially_blocked` / `blocked` per tested path, the deciding robots rule, and the vendor's caveat.
- **Rendering and markup report**: per page, the visible-text size, app-shell markers, missing expected phrases, JSON-LD types found, and parse errors.
- **Feed readiness**: required-attribute gaps, the native_commerce opt-in count, conversational-attribute coverage, and the optional agentic-commerce feed result.
- **WebMCP note** (if requested): tools found, clearly marked experimental.
- **Fix plan** in priority order, each fix routed to the skill that implements it.

## Caveats

1. **robots.txt is a request, not a wall, for user-initiated fetchers.** OpenAI says robots.txt "may not apply" to ChatGPT-User. Perplexity says Perplexity-User "generally ignores robots.txt rules". Don't promise that blocking them keeps content out.
2. **The no-JS check is not a rendering test.** It reads the HTML as served. It cannot tell you how a JavaScript-capable crawler renders the page; use `/digital-marketing-pro:tech-seo-audit` for that.
3. **A feed export is not Merchant Center's verdict.** The audit checks the file. Merchant Center diagnostics, account-level policies, and UCP onboarding status live in the account.
4. **Being allowed is not being cited.** This audit checks whether agents *can* use the site. Whether they *do* is measured by `/digital-marketing-pro:geo-monitor` (probes plus Bing Webmaster AI Performance) and `/digital-marketing-pro:gsc-ai-performance`.
5. **An unreachable robots.txt fails the robots check.** With `--fetch`, a 4xx robots.txt means allow-all, and a 5xx or network error means every crawler must assume complete disallow (RFC 9309). The first finding says so; if the cause was your own network rather than the site, re-run.

## Agents used

- **seo-specialist** (primary): crawler policy, rendering, structured data, and the AI-visibility hand-offs
- **media-buyer**: feed and checkout implications for Shopping, AI Max, and ChatGPT Ads product feeds (see `skills/paid-advertising/ads-in-ai-answers.md`)

## See also

- `/digital-marketing-pro:tech-seo-audit`: full technical crawl and rendering
- `/digital-marketing-pro:entity-audit`: Organization and entity consistency
- `/digital-marketing-pro:aeo-geo`: optimizing for AI answers once agents can read the site
- `/digital-marketing-pro:geo-monitor`: whether AI answers actually cite the brand
