---
name: admakeai-api
description: >-
  Design, edit, and ship ad creative with AdMakeAI — finished ad designs,
  edits, batch ad sets, ad copy, UGC video ads, competitor ad research, Meta
  campaign drafts and Meta Ads reporting. Use it when a request is about
  making, publishing, researching, or reporting on ads. Default to read and
  list calls; confirm every write or credit-spending action with the user.
  Trigger words: create, generate, make, design, produce, brainstorm, batch,
  vary, mock up, upload, publish, push, ship, draft, list, browse, find, get,
  fetch, look up, audit, or recap ads, ad creatives, product photos,
  lifestyle shots, UGC, ad copy, hooks, headlines, ad sets, campaigns,
  competitor ads, competitor research, Meta ads, Facebook ads, or ad
  analytics. Also use when the user mentions AdMakeAI, admakeai, or wants to
  know their AdMakeAI credit balance.
---

# AdMakeAI

Ad-creative design, competitor ad research, Meta campaign drafting, and Meta Ads reporting through the **AdMakeAI connector** (`https://admakeai.com/api/mcp`). The user signs in to their AdMakeAI account through OAuth when they connect it; never ask them for an API key or password.

If AdMakeAI tools aren't available, or a call fails with an authorization error, ask the user to connect (or reconnect) the AdMakeAI connector. They need an AdMakeAI account at https://admakeai.com.

Tool names below are the connector's tool names, e.g. `adGeneration__create`.

## The one thing to get right: projects

Every ad design is scoped to a **project** — the brand record holding the product summary, audience, value proposition and logo. `adGeneration__create` expands your short brief into a full design prompt using that brief, which is why ads come back looking like ads (headline, badge, CTA baked in) instead of stock photos.

So `projectId` is required on `adGeneration__create`, and the rule is always the same:

1. Call `adResearch__listProjects` before the first design of a session.
2. One project? Use it. Several? Pick the one the user's request is clearly about (brand name, product, URL they mentioned) and say which one you picked. Still ambiguous? **Ask.** Never guess an id and never design into the wrong brand — that spends their credits on the wrong product.
3. No projects at all? It's a new account. Ask the user for their brand's website (never guess it), call `project__createFirst` with it (free, about 10-15 seconds: it reads the site and fills in the brand brief and logo), then carry on with what they asked. It only works while the account has no projects; later brands are set up at https://admakeai.com/dashboard.

`adResearch__getProject` gives you the full brief; read it when the user's request depends on brand details (audience, positioning, what they actually sell).

`adGeneration__generateImage` and `videoGeneration__start` also take a `projectId` — for `generateImage` it is credit scoping only, nothing from the brief reaches the prompt.

## Intent routing

Pick the right tool from natural-language intent. **Read tables top-to-bottom; first match wins.**

### Account & credits

| User says... | Tool | Notes |
| --- | --- | --- |
| "what's my balance / credits" | `user__getCredits` | Cheapest read. Returns `{ credits }`. |
| "show my profile / plan" | `user__me` | Includes credits, subscription, plan name. |

### Design ad creatives

Two renderers, same credit cost, very different output. Choose deliberately:

| Tool | What it renders |
| --- | --- |
| `adGeneration__create` | **A finished ad design.** A creative-director model rewrites your brief into the real design prompt using the project's brand brief, and that rewrite always adds a headline, a subline, a CTA button, and the project logo when the project has one. Negative instructions in the prompt ("no text", "no logo", "nothing but the product") **cannot** suppress them. |
| `adGeneration__generateImage` | **Exactly your prompt.** It goes to the image model verbatim — no creative-director rewrite, no brand brief, no added headline/subline/CTA, no logo. The image contains only what the prompt stipulates. |

| User says... | Tool | Notes |
| --- | --- | --- |
| "make / create / design an ad", "design a product ad" | `adGeneration__create` | Single design. Required: `projectId`, `prompt` (a brief, not a finished prompt). Optional: `adType`, `aspectRatio`, `quality`, `referenceImageUrls`, `inputImageId` (uploaded photo), `referenceAdId` / `referenceInspirationId` to remix. |
| "no text on it", "just the product", "a clean product / lifestyle photo", "put exactly this headline on it" | `adGeneration__generateImage` | Required: `projectId` (credit scoping only), `prompt` (used verbatim — write the full prompt yourself). Optional: `aspectRatio`, `quality`, `referenceImageUrls`, `inputImageId`. |
| "edit / change / restyle this ad", "swap the background", "make it 9:16" | `adGeneration__edit` | Source is `sourceAdId` (one of their ads) or `sourceImageUrl` (any URL). `editInstructions` reaches the model close to literally. |
| "remix this competitor ad" | `adGeneration__create` with `referenceInspirationId` | Save the competitor ad first with `adResearch__saveInspiration`. |
| "give me 5 variations", "batch", "test different hooks" | `adSet__create` then `adSet__generateBatch` | The set holds the shared brief; the batch call holds the per-variation direction. `adSet__suggestDirections` will invent the angles for you. |
| "use my product photo / logo as reference" | `upload__uploadImageBase64` → pass the returned id as `inputImageId` | Accepts JPEG/PNG/WebP base64. Already uploaded? `upload__getUserImages`. Brand assets already in the project? `project__getAssets`. |

Designs render in the background. After queueing one, **tell the user** it takes a minute and offer to check on it.

### Ad copy

| User says... | Tool | Notes |
| --- | --- | --- |
| "write copy / headlines / hooks for this ad" | `adCopyGeneration__generate` | Needs the finished `imageUrl`. Pass `projectId` so it uses the brand brief. Returns up to 5 variations with hook angles. |
| "what copy styles are there" | `adCopyGeneration__getMessagingStyles` | clickbait / professional / UGC / direct response / storytelling / ... |

### Video ads

| User says... | Tool | Notes |
| --- | --- | --- |
| "make a UGC video ad", "video version of this" | `videoGeneration__start` | Needs `projectId` and an active subscription. Costs 5 / 15 / 50 credits for low / medium / high. |
| "is my video done" | `videoGeneration__getStatus` | Poll until COMPLETED. Videos take minutes, not seconds. |
| "show my videos" | `videoGeneration__list` / `videoGeneration__listPending` | |

### Competitor research

| User says... | Tool | Notes |
| --- | --- | --- |
| "what ads is <brand> running" | `adResearch__searchCompanies` then `adResearch__getCompanyAds` | Live Meta Ad Library. Works for any advertiser, no project needed. |
| "add <brand> as a competitor" | `adResearch__addCompetitors` | Scrapes their ads into the project. |
| "show competitor ads for my project" | `adResearch__getScrapedAds` | Sort by `longest_running` to find their proven winners. |
| "what have we got on competitor X" | `adResearch__getCompetitorPreview` | Quick preview of the ads already scraped for one competitor. |
| "details of that competitor ad" | `adResearch__getAdDetails` | Needs `projectId` + `scrapedAdId`. |
| "save that one for inspiration" | `adResearch__saveInspiration` | Returns an inspiration ID for `adGeneration__create`. |
| "what have we saved as inspiration" | `adResearch__getSavedInspirations` | Lists saved ads with their inspiration IDs. |
| "re-scrape / refresh competitor ads" | `adResearch__scrapeCompetitor` | Async; poll `adResearch__pollStatus`. |

### Find existing ads

| User says... | Tool | Notes |
| --- | --- | --- |
| "show my recent ads" | `adGeneration__getRecent` | Default 12. Returns image URLs + prompts. |
| "list / browse / paginate my ads" | `adGeneration__list` | Cursor-paginated. |
| "search my ads for X" | `adGeneration__searchAll` | Full-text on prompts. |
| "what's still rendering" | `adGeneration__listPending` | Only PENDING status. |
| "show the details of ad <id>" | `adGeneration__getById` | Returns the full record. |
| "star / favorite that one", "this is the winner" | `adGeneration__toggleFavorite` | Free toggle. Good way to mark the pick of a batch. |

### Ad sets

| User says... | Tool | Notes |
| --- | --- | --- |
| "list my ad sets" | `adSet__list` | Page-paginated. |
| "show ad set <id>" | `adSet__get` | Includes `generalInstructions`. |
| "what's in this ad set" | `adSet__getGenerations` | Ads in that set. |
| "create an ad set" | `adSet__create` | Free. Holds project + shared brief + ad type + quality + aspect ratio. |
| "change the brief / quality of the set" | `adSet__update` | Overwrites the set's settings. |
| "generate a batch in ad set X" | `adSet__generateBatch` | See the design table. |
| "what angles should we test" | `adSet__suggestDirections` | Free. Model-written creative directions to feed back in as per-variation instructions. |

### Projects

| User says... | Tool | Notes |
| --- | --- | --- |
| "list my projects" | `adResearch__listProjects` | One entry per brand/product. Start here, every session. |
| "set up my brand" (no projects yet) | `project__createFirst` | Free. From the brand's website; ask for the URL. Only the account's first project. |
| "set up another brand / project" | *(none)* | Not available through the connector. Point the user at https://admakeai.com/dashboard. |
| "show the brand brief" | `adResearch__getProject` | Brief + competitors + research jobs + ad counts. |
| "fix / update the brief, audience, industry" | `project__updateBrief` | Overwrites the brief fields you pass. A sharper brief improves every later design. |
| "what product photos do we have" | `project__getAssets` | Asset URLs usable as `referenceImageUrls`. |
| "upload this photo" | `upload__uploadImageBase64` | Returns an image ID + public URL for designs or campaign drafts. |
| "what have I uploaded before" | `upload__getUserImages` | Newest first, paginated. |
| "is the research done" | `adResearch__pollStatus` | Pipeline stage + running scrape jobs. |

### Facebook ad accounts

| User says... | Tool | Notes |
| --- | --- | --- |
| "show my connected fb accounts" | `facebookConnection__list` | Returns ad accounts + Pages with cached identity. |
| "list campaigns" | `facebookUpload__getCampaigns` | Needs `connectionId` + `adAccountId`. Cold cache triggers a Meta refresh. |
| "list ad sets in campaign X" | `facebookUpload__getAdSets` | Needs `connectionId` + `campaignId`. |

### Upload ads to Meta

| User says... | Tool | Notes |
| --- | --- | --- |
| "preflight / validate this for fb" | `facebookUpload__runPreflight` | Checks image dims, copy length. Free, no live action. |
| "upload / publish / push this ad to meta" | `facebookUpload__request` | **Live action — creates a real ad on Meta. Costs 3 credits.** Always confirm with the user first. |
| "show my uploaded ads" | `facebookUpload__list` | Filterable by account + state. |
| "status of upload <id>" | `facebookUpload__get` | Returns Meta IDs + state. |

### Meta campaign drafts

| User says... | Tool | Notes |
| --- | --- | --- |
| "what creatives can we reuse from past uploads" | `facebookCampaignDraft__sourceAssets` | Read-only. Resolves previously-uploaded Meta ads into reusable creative assets for a draft. |
| "show me the draft before we push it" | `facebookCampaignDraft__getAgentDraft` | Read-only. Fetch a saved draft by draft ID. |
| "push that draft to meta" | `facebookCampaignDraft__pushAgentDraft` | **Live action.** Pushes a saved draft to Meta as draft campaigns / ad sets / ads. Confirm first. |
| "build a whole campaign from these images" | `facebookCampaignDraft__pushDraftCampaign` | **Live action.** Creates Meta draft campaigns / ad sets / ads from explicit campaign data, ad sets, ad copy and image URLs. Confirm first. |

Both push tools create real objects inside the user's Meta ad account. They land as drafts rather than live ads, but they are still writes to Meta — read the plan back to the user and get an explicit yes before calling.

### Meta analytics

All read-only and free.

| User says... | Tool | Notes |
| --- | --- | --- |
| "how did the account do last month", "total spend / ROAS" | `zernioAnalytics__accountOverview` | Account-level spend, impressions, clicks, CTR, CPC, conversions, ROAS for a range like `last_30_days`, with previous-period comparison. Best first call. |
| "campaign tree", "what's the structure" | `zernioAnalytics__tree` | Campaign → ad set → ad hierarchy. |
| "performance over time", "timeline" | `zernioAnalytics__timeline` | Time-series for an ad account. |
| "list / recap campaigns" | `zernioAnalytics__listCampaigns` | Includes rolled-up metrics. |
| "list ads in campaign X" | `zernioAnalytics__listAds` | Filterable by campaign / ad set. |
| "details of ad <id>" | `zernioAnalytics__getAd` | Metadata + creative. |
| "daily analytics for ad <id>" | `zernioAnalytics__getAdAnalytics` | Spend, CTR, CPC, conversions. |
| "what are people saying about this ad" | `zernioAnalytics__getAdComments` | Public comments on the boosted post behind a Meta ad (Facebook or Instagram placement). |

## Credit costs

Design tools and Meta uploads spend credits from the user's plan. Every read (list / get / analytics) is free.

| Tool | Cost |
| --- | --- |
| `adGeneration__create`, `adGeneration__generateImage`, `adGeneration__edit` | 2 (low) / 8 (high) / 20 (ultra) credits |
| `adSet__generateBatch` | `count × per-design cost`. A batch of 10 high-quality designs = 80 credits. |
| `videoGeneration__start` | 5 (low) / 15 (medium) / 50 (high) credits per video |
| `facebookUpload__request` | 3 credits per upload (`facebookUpload__runPreflight` is free) |
| `adCopyGeneration__generate`, `adSet__create` / `__update` / `__suggestDirections`, `adGeneration__toggleFavorite`, `project__*`, `upload__*`, `adResearch__*` | Free |

Failed designs are refunded automatically.

**Always call `user__getCredits` before a batch of more than 10 designs** and warn the user if the balance is close.

## Pagination

List tools use one of three patterns:

| Pattern | Used by | How to advance |
| --- | --- | --- |
| `{ page, perPage }` | `adSet__list`, `adSet__getGenerations`, `videoGeneration__list`, `zernioAnalytics__listAds`, `zernioAnalytics__listCampaigns` | Increment `page`. |
| `{ limit, cursor }` | `adGeneration__list`, `adGeneration__searchAll`, `adResearch__listProjects`, `upload__getUserImages` | Pass the `nextCursor` from the previous response. |
| `{ limit, offset }` | `adResearch__getScrapedAds`, `adResearch__getSavedInspirations` | Increment `offset` by `limit`. |

Stop paginating when you have what the user asked for.

## Common optional params

These appear on multiple tools and mean the same thing everywhere:

- `projectId`: the brand to design for. Required on `adGeneration__create`, `adGeneration__generateImage`, `adSet__create`, `videoGeneration__start`.
- `aspectRatio`: `"1:1" | "4:5" | "9:16" | "16:9"`. Defaults to `"1:1"`. Use `"4:5"` for Instagram feed, `"9:16"` for Reels/Stories, `"16:9"` for YouTube/desktop.
- `quality`: `"low" | "high" | "ultra"`. Defaults to `"low"`. Use `"low"` while exploring angles, `"high"` for the one they'll actually run.
- `adType`: `"product_showcase" | "promotional" | "testimonial" | "lifestyle" | "comparison" | "announcement"`. Defaults to `"product_showcase"`. Only meaningful on `adGeneration__create` and `adSet__create`.
- `inputImageId`: ID of an uploaded product photo (from `upload__uploadImageBase64`) to use as a reference.

## Brief patterns for `adGeneration__create`

`prompt` is a **creative brief, not a finished prompt** — the renderer expands it with the project's brand brief, then lays on headline, badge and CTA. Describe the scene and the angle; don't hand-write the whole prompt.

Good briefs are concrete and visual. Bad ones are abstract or list-y.

| User intent | Good brief template |
| --- | --- |
| Product on lifestyle background | `"<Product> placed on <surface> with <prop>, soft natural light, <style> aesthetic"` |
| Selfie-style UGC | `"First-person selfie of a <demo> holding <product>, casual <setting>, iPhone photo aesthetic"` |
| Before/after | `"Split-screen: left side <before state>, right side <after state with product>, clean comparison"` |
| Bold statement | `"<Product> on <bg color>, oversized typography reading '<headline>', minimalist composition"` |

If the user gives only a tagline ("matcha for tired founders") and no visual, **ask them one clarifying question** about setting/mood before designing.

For `adGeneration__generateImage` the opposite applies: you are writing the final prompt, so be fully specific about subject, lighting, lens, background and any on-image text — nothing is added for you.

## Known limitations

- Designs are **async**. `adGeneration__create` returns immediately with `{ id, status: "PENDING", creditCost, ... }`. Poll `adGeneration__getById` every few seconds until `status === "COMPLETED"`. Typical completion: 20-60s low quality, 60-120s high quality. The record's `prompt` field stays empty until the brief has been expanded.
- The connector creates only an account's first project (`project__createFirst`). Further projects are made in the dashboard, so an existing brand is never duplicated by mistake.
- **Pausing, resuming, or launching Meta ads isn't available.** Tell the user to change ad status in Meta Ads Manager.
- The free plan has a **daily design cap**. The error says `Daily generation limit reached`. Tell the user to upgrade at https://admakeai.com/pricing.
- Facebook tools need a **paid AdMakeAI plan** (free accounts get `FORBIDDEN: The Facebook Ads integration is available on paid plans`) and a **connected Facebook account**. If `facebookConnection__list` returns empty, point them to https://admakeai.com/dashboard/integrations/facebook.
- Nothing is ever **deleted** through the connector — not AdMakeAI ads or ad sets, and not Meta resources. If the user asks to delete something, tell them to do it in the AdMakeAI web app or Meta Ads Manager.
