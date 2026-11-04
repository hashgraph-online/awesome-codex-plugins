# AI and LLM spend

Two kinds of AI spend: **subscriptions** people use directly (chat apps, coding agents) and **API
usage** inside software. The levers differ.

## Subscriptions (chat apps, coding agents)

1. **One paid plan, not three.** Most people pay for overlapping chat apps. Keep the one they use
   most; free tiers of the others usually cover occasional use.
2. **Bundles they already pay for.** Some storage and productivity bundles include an AI plan, and
   some phone or telecom plans include AI subscriptions. Check before paying separately.
3. **Subscription vs API for personal coding agents.** For one person's daily agent use, a flat
   subscription is usually far cheaper than paying API rates. For production software, use the API.
4. **Right tier.** Start on the lowest plan that unlocks the needed model and limits; move up only
   after hitting limits in real use. Annual billing saves roughly 15 percent when usage is steady.
5. **Programs.** Open-source maintainers, students, teachers and nonprofits have dedicated offers
   from the major labs (see [../programs/README.md](../programs/README.md)).

## API usage in software

Apply in this order and measure each step with a small eval so quality does not silently drop:

1. **Smallest model that passes.** Route routine calls to a small model and keep the large one for
   the steps where evals show it matters. Re-check model choice when a new generation ships: newer
   models are often cheaper than the older ones teams leave pinned.
2. **Prompt caching** for any repeated prefix (system prompt, tools, documents). Cache reads cost a
   small fraction of normal input. Watch for providers that bill cache writes.
3. **Batch or flex tiers** for anything not interactive (evals, backfills, nightly jobs): about half
   price.
4. **Fewer tokens.** Cap output tokens, trim context, summarize history, avoid sending whole files
   when a diff will do, compare cost per task (tokenizers differ between models).
5. **Cache results** you will ask for again; deduplicate identical requests.
6. **Avoid premium options you do not need:** fast or priority tiers, data residency surcharges,
   paid web search when a fetch of a known page works.
7. **Open-weight models** on cheap hosts or locally for bulk, non-sensitive work; off-peak pricing
   where a provider offers it.
8. **Startup credits** through an investor or accelerator, when the company qualifies.

Always report the estimated monthly cost at expected volume: tokens per call x calls per day x 30 x
price.

## Reference data

### Prices and levers (checked 2026-10-29, re-verify before quoting)

Prices are USD per 1M tokens (MTok) unless noted.

| Name | Who qualifies | What you get | Official URL | Status | Verified |
|---|---|---|---|---|---|
| Anthropic prompt caching | Any Claude API user | Cache read 0.1x base input (0.05x on Opus 5.5 / Sonnet 5.5, 0.025x on Fable 5.1 / Mythos 5.1). Writes: 5m TTL 1.25x, 1h TTL 2x. Automatic mode = one top-level `cache_control`. Stacks with Batch. | https://platform.claude.com/docs/en/about-claude/pricing#prompt-caching | changed - deeper read discount on newest models | 2026-10-29 |
| Anthropic Message Batches API | Any Claude API user | 50% off input and output, async. Stacks with caching and data-residency multipliers; not available with fast mode. | https://platform.claude.com/docs/en/about-claude/pricing#batch-processing | active | 2026-10-29 |
| Claude model tiering (downgrade lever) | Any Claude API user | Fable 5.1 $10/$50; Opus 5.5 $4/$20; Sonnet 5.5 $2/$10; Haiku 5.5 $0.10/$0.50 (prompts up to 100K; $0.50/$2.50 above). Opus 5.5 is cheaper than Opus 4.5-5 ($5/$25): do not pin old models. | https://platform.claude.com/docs/en/about-claude/pricing | changed - new 5.x lineup, lower prices | 2026-10-29 |
| Anthropic premiums to avoid | Any Claude API user | US-only `inference_geo` = 1.1x; fast mode Opus 5.5 = 2x ($8/$40); Bedrock/Vertex regional endpoints +10%; web search $10/1K. Claude 4.7+ tokenizer yields about 30% more tokens. Code execution free with web search/fetch, else 50 free hours/day. | https://platform.claude.com/docs/en/about-claude/pricing | active | 2026-10-29 |
| Claude subscriptions for coding (Claude Code) | Individuals and teams | Pro $20/mo ($17/mo annual), Max 5x $100, Max 20x $200, Team $25/$125 seat monthly ($20/$100 annual). Claude Code in all paid plans, shared 5-hour + weekly limits; overage via usage credits at API rates. Enterprise $20/seat + usage at API rates. | https://claude.com/pricing | changed - Enterprise now seat + API-rate usage | 2026-10-29 |
| Claude Max / Team monthly API credits | Max 5x, Max 20x, Team (incl. nonprofit/scientist Team) after 7 days on plan | $100/mo (Max 5x), $200/mo (Max 20x), Team $20/Standard and $100/Premium seat pooled, capped $500. Claude API, Managed Agents, Agent SDK only; not Claude Code; expires monthly, no rollover. | https://platform.claude.com/docs/en/about-claude/api-credits-for-subscribers | active - new since 2024 | 2026-10-29 |
| OpenAI Batch API + Flex processing | Any OpenAI API user | Batch: 50% off, 24h completion window. Flex (`service_tier: "flex"`): Batch rates on synchronous calls, slower and may return resource-unavailable; beta, limited models. | https://developers.openai.com/api/docs/guides/flex-processing | active | 2026-10-29 |
| OpenAI prompt caching | Any OpenAI API user | Cached input up to 95% off (gpt-6.1-sol $0.10 vs $2.00; gpt-6-astra $1 vs $10). GPT-5.6+ now bills cache writes: 1.25x for 30m TTL, 2.5x for 12h TTL; explicit breakpoints supported. | https://developers.openai.com/api/docs/guides/prompt-caching | changed - cache writes now billed | 2026-10-29 |
| OpenAI model tiering and speed tiers | Any OpenAI API user | gpt-6-astra $10/$50, gpt-6.1-sol $2/$10, gpt-6.1-terra $1/$5, gpt-6-luna $0.10/$0.50. Fast (ex-Priority, renamed 2026-07-30) = 2x, Ultrafast = 6x. Data residency and FedRAMP +10%. | https://developers.openai.com/api/docs/pricing | changed - GPT-6 lineup, Fast/Ultrafast tiers | 2026-10-29 |
| ChatGPT plans with Codex | Individuals and businesses | Free $0 and Go $8 (Codex with GPT-6 Luna in desktop app), Plus $20, Pro $100 / $200 / $500 tiers, Business $20/user/mo annual ($25 monthly). Codex via API key billed at API rates. | https://developers.openai.com/codex/pricing | changed - Pro split into 3 tiers, Codex on Free/Go | 2026-10-29 |
| GitHub Copilot plans | Individuals | Free $0, Pro $10, Pro+ $39, Max $100. Usage now paid in GitHub AI Credits ($0.01 each): Pro gets $15/mo, Pro+ $70, Max $200 (base + flex). Completions and next-edit suggestions unlimited on paid plans. | https://github.com/features/copilot/plans | changed - premium requests replaced by AI credits | 2026-10-29 |
| Cursor plans | Individuals and teams | Free $0, Plus $8 (Grok models only), Premium $30, Super $100, Ultra $200, Teams from $30/user. Claude/GPT and other third-party models billed separately at API list price. | https://cursor.com/pricing | changed - rebuilt around Grok/X bundle (Oct 2026) | 2026-10-29 |
| Gemini API free tier (Google AI Studio) | Any AI Studio project without billing | Free input/output on Gemini 3.8 Flash, 3.6 Flash, 3.5 and 3.1 Flash-Lite, 2.5 Pro/Flash/Flash-Lite and others. Not on Gemini 4 Argon or 3.1 Pro preview. Free-tier data used to improve products; per-project limits shown only in AI Studio. | https://ai.google.dev/gemini-api/docs/pricing | changed - top models excluded from free tier | 2026-10-29 |
| Gemini Batch, Flex and context caching | Paid Gemini API (Tier 1+ = billing linked) | Batch and Flex = 50% off Standard; Priority about 1.8x. Context caching about 10% of input price plus storage $0.50-$1.00 per MTok-hour; Gemini 4 Argon implicit caching only. Search grounding 5,000 free/mo then $14/1K. | https://ai.google.dev/gemini-api/docs/pricing | active | 2026-10-29 |
| Gemini introductory pricing (time-limited) | Paid Gemini API | Gemini 4 Argon $2/$10 until 2026-11-30, then $4/$20. Gemini 3.8 Flash and 3.6 Flash $0.75/$3.75 until 2026-12-31, then $1.50/$7.50. Budget for prices doubling. | https://ai.google.dev/gemini-api/docs/pricing | active - expires Nov/Dec 2026 | 2026-10-29 |
| Gemini CLI free quota | Anyone with a Google account | Login with Google (Code Assist for individuals): 1,000 requests/day; free Gemini API key: 250/day, Flash only. Google AI Pro 1,500/day, Ultra 2,000/day. | https://github.com/google-gemini/gemini-cli/blob/main/docs/resources/quota-and-pricing.md | active (doc last edited 2026-06-18) | 2026-10-29 |
| OpenRouter free models (`:free`) | Any OpenRouter account | 20 requests/min; 50 requests/day if under 10 credits ($10) ever purchased, 1,000/day once 10+ purchased. Negative balance blocks free models too. | https://openrouter.ai/docs/api/reference/limits | active | 2026-10-29 |
| Groq free plan | Any GroqCloud account | Free plan e.g. gpt-oss-120b, gpt-oss-20b, qwen3.8-27b: 30 RPM, 1K requests/day, 8K TPM, 200K tokens/day. Developer plan adds higher limits plus Batch and Flex. | https://console.groq.com/docs/rate-limits | active | 2026-10-29 |
| Cerebras inference free trial | New accounts that add a payment method | One-time $5 credit, expires 30 days; access pauses after unless you buy PayGo credits. Trial limits e.g. gpt-oss-120b 5 RPM, 1M tokens/day. | https://www.cerebras.ai/pricing | changed - free tier now $5 card-gated trial | 2026-10-29 |
| Ollama local + Ollama Cloud | Anyone | Local models free, no subscription. Cloud: pay-as-you-go per token ($0 plan), Pro $20/mo incl. $60 credits, Max $100 incl. $300, Team $500 incl. $1,000; off-peak rates on some models outside 12:00-18:00 UTC weekdays. | https://ollama.com/pricing | changed - cloud tiers with usage credits | 2026-10-29 |
| DeepSeek API off-peak pricing | Any DeepSeek API user | Off-peak = 50% of peak. Peak 01:00-04:00 and 06:00-10:00 UTC Mon-Fri; all else off-peak. deepseek-flash peak $0.30/$1.20, v4-pro $1.32/$3.96; cache hits about 98% off. | https://api-docs.deepseek.com/quick_start/pricing | changed - reintroduced as peak/off-peak Aug 2026 | 2026-10-29 |

Changes vs 2024:
- Cache reads got even cheaper on the newest models (Claude Opus/Sonnet 5.5 at 0.05x, Fable 5.1 at 0.025x; OpenAI up to 95% off), but OpenAI now charges for cache writes (1.25x / 2.5x) where 2024 caching was automatic and free to write.
- Flagship list prices fell sharply: Claude Opus 5.5 is $4/$20 (Opus 3 was $15/$75) and Haiku 5.5 is $0.10/$0.50; older pinned models now cost more than the newest ones. Claude 4.7+ tokenizer adds about 30% tokens, so compare per-task, not per-token.
- Subscriptions are now the main coding-agent lever and bundle API money: Claude Max includes $100-$200/mo API credits (not for Claude Code), ChatGPT Pro has $100/$200/$500 tiers, Copilot moved to dollar-denominated AI credits, and Cursor moved third-party models to API list price.
- Free inference tightened: Cerebras replaced its free tier with a one-time $5 card-gated trial, OpenRouter free models cap at 50/day without a $10 lifetime purchase, and Gemini's free tier excludes the top models and trains on your data.
- Time-based pricing is a real lever again: DeepSeek peak/off-peak (50%) since Aug 2026, Ollama Cloud off-peak rates, and Gemini introductory prices that double on 2026-12-01 (Argon) and 2027-01-01 (3.8/3.6 Flash).
