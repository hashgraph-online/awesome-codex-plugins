# Amazon Ads creative asset specifications

Every dimension, file size, and format, grouped by the program the asset feeds.
Read the section for your program and ignore the rest — the numbers do not
transfer between programs, and neither do the content rules.

Contents: [Program routing](#program-routing) · [Sponsored Brands and Sponsored Display](#sponsored-brands-and-sponsored-display-custom-image) ·
[Brand logo](#brand-logo) · [Copy limits](#copy-and-text-asset-limits) ·
[DSP display banners](#dsp-display-banners-finished-ad-units) ·
[Standard media placements](#standard-media-placements) ·
[eCommerce display creative](#ecommerce-rec-display-creative) ·
[Conflicts to verify](#published-numbers-that-conflict)

## Program routing

The single most consequential question before generating anything: **which
program consumes this asset?** Text and logos inside the image are forbidden
in one program and expected in another.

| Program | You deliver | Text or logo inside the image? | Amazon adds automatically |
|---|---|---|---|
| **Sponsored Brands** (product collection, Store spotlight, video) | A raw lifestyle/custom image, a separate logo asset, a separate headline string | **No.** No branding text, no logos, no CTAs | Headline, logo, product tiles, CTA |
| **Sponsored Display** (custom creative) | Same: image, logo, headline, all separate | **No** | Headline, logo, price, ratings, "Shop now" |
| **Amazon DSP component-based / asset-based creative** | Image set (3 aspect ratios), logo, headline, body, disclaimer | **No** in the image; copy travels as text fields | Assembles into 12,000+ size variations |
| **eCommerce (REC) display creative** | A composed custom image per ad size | **Yes, limited:** ≤10 words, ≤2 logos, ≤2 type variations | Live price, ratings, deal badges section |
| **DSP display banners / standard media** | A finished, fully composed ad unit at exact pixel size | **Yes** — it is a finished ad | Nothing; AdChoices label only |

Getting this wrong is the most expensive mistake in the workflow, because a
beautiful lifestyle image with the brand name burned into it is an automatic
rejection for Sponsored Brands and a requirement for a banner.

## Sponsored Brands and Sponsored Display custom image

The self-service custom image. One rectangular upload can serve in up to
12,000 size variations, so Amazon crops it aggressively — keep the subject
centered and leave breathing room at every edge.

| Aspect ratio | Recommended | Minimum |
|---|---|---|
| Square 1:1 | 1200 × 1200 px | 600 × 600 px |
| Wide 1.91:1 | 1200 × 628 px | 600 × 314 px |
| Tall 9:16 | 900 × 1600 px | 338 × 600 px |

- **Minimum resolution:** 600 × 600 px. **Maximum file size:** 5 MB.
- **Resolution target:** highest possible; Amazon states 72 ppi as the floor
  for ad imagery and rejects blurry, distorted, pixelated, smudged, or
  stretched images.
- Supplying all three aspect ratios is the safe default; a single wide image
  will be center-cropped into square and tall placements.

**Content rules for the image itself** (these are policy, not preference):

- No branding elements — no text, no logos, no calls to action.
- No white or transparent backgrounds. Borderless ads also may not use white
  or off-white background colors; the creative has to contrast with the page.
- No pricing or savings claims.
- No letterbox or pillarbox formats (bars, blurred or otherwise).
- No crowded, cluttered, or poorly cropped elements.
- Nothing that contradicts the landing page.
- Lifestyle imagery is expected and encouraged; a product alone on a solid or
  transparent background is not accepted as a custom image.
- Products must be prominently displayed, either in use or on their own.
- Use diverse models — Amazon names "people of all races, ages, body types,
  ethnicities, and gender identities" as a requirement, not a suggestion.

## Brand logo

Logo rules differ by program. Check which one applies.

| Program | Minimum size | Aspect ratio | Format | Max file size |
|---|---|---|---|---|
| Sponsored Brands / Sponsored Display / DSP component-based | 400 × 400 px | 1:1 | Not published on the spec page; PNG or JPG in practice | Not published |
| eCommerce (REC) creative | 600 × 100 px | — | JPG, GIF, PNG | 1,000 KB |

Policy rules that apply to every logo:

- It must be the brand's registered logo, with legal rights to use it.
- It must fill the entire image, or sit on a white or transparent background.
- Text in the logo must be legible on both mobile and desktop.
- It must stay consistent across all ads.
- Do not combine multiple logos, place a logo on a complex graphical
  background, use a product image or ASIN as the logo, or use the logo slot as
  a headline extension.
- Content outside the published safe zones gets cropped on some ad sizes; use
  Amazon's PSD templates for anything with critical detail near an edge.
- eCommerce creative allows at most 2 logos per custom image.

## Copy and text asset limits

Character limits for the text fields that travel alongside the image
(component-based creative; Sponsored Display headline matches).

| Field | Limit | Japanese |
|---|---|---|
| Headline | 50 characters | 25 |
| Brand name | 25 characters | 15 |
| Body text | 100 characters | 50 |
| Disclaimer | 60 characters | 28 |

Copy rules live in [`02-creative-policy.md`](02-creative-policy.md).

## DSP display banners (finished ad units)

You deliver a composed banner at the exact creative dimensions. Mobile sizes
are designed at 2X and downscaled, which is why the creative dimensions differ
from the display size.

**Desktop and mobile web**

| Format | Display size | Creative dimensions | Max file size | Format |
|---|---|---|---|---|
| Medium rectangle | 300 × 250 | 300 × 250 | 40 kb static / 200 kb HTML | JPG, PNG-8 |
| Leaderboard | 728 × 90 | 728 × 90 | 40 kb static / 200 kb HTML | JPG, PNG-8 |
| Wide skyscraper | 160 × 600 | 160 × 600 | 40 kb static / 200 kb HTML | JPG, PNG-8 |
| Large rectangle | 300 × 600 | 300 × 600 | 50 kb static / 200 kb HTML | JPG, PNG-8 |
| Billboard | 970 × 250 (800 × 250 Germany) | 1940 × 500 @2X onsite | 200 kb | JPG, PNG-8 |

**Mobile app banners**

| Display size | Creative dimensions | Max file size | Notes |
|---|---|---|---|
| 320 × 50 | 640 × 100 @2X (required) | 50 kb | |
| 300 × 250 | 600 × 500 @2X | 40 kb | |
| 728 × 90 | 1456 × 180 @2X | 200 kb | Tablet leaderboard |
| 414 × 125 | 828 × 250 @2X (required) | 100–200 kb (see conflicts) | 640 × 250 safe zone; Amazon mobile web and shopping apps only |

Static file sizes drop to **50 kb in France, Italy, Spain, and Japan**.

Requirements specific to banners:

- Serving is site-served or third-party **iframe only**, over HTTPS.
- Minimum font size 16 pt at 2X resolution.
- An advertiser logo or brand name is **required** in every mobile banner.
- If the banner links to Amazon, include the Amazon logo or a textual
  reference to Amazon.
- Add a non-white 1-pixel border, or use a high-contrast background, so the
  unit separates from the page.
- Animation (GIF) is permitted but discouraged; Sponsored Display ads are
  static only, video excepted.
- Keep backgrounds simple and text minimal.
- AdChoices labels are applied by Amazon automatically.

## Standard media placements

Fixed on-Amazon placements. Formats: HTML, JPG, GIF, PNG. Locales: US, MX,
CA, UK, DE, FR, IT, ES, JP, IN.

| Placement | Size | Max file size |
|---|---|---|
| Home page | 300 × 250 | 200 kb HTML / 40 kb static |
| Detail page | 300 × 250 | 200 kb HTML / 40 kb static |
| MP3 detail page ATF | 300 × 250 | 200 kb HTML / 40 kb static |
| Read all reviews | 300 × 250 | 200 kb HTML / 40 kb static |
| Thank you page | 300 × 250 | 200 kb HTML / 40 kb static |
| Search skyscraper | 160 × 600 | 200 kb HTML / 40 kb static |
| Thank you page (half) | 300 × 600 | 200 kb HTML / 50 kb static |
| Payment method page | 180 × 150 | 15 kb, **static only** |

Static maximums are 50 kb in France, Italy, Spain, and Japan. Production
handoffs typically also want layered PSDs, vector logos (.ai or .eps),
backgrounds, fonts (.otf or .ttf), copy, brand guidelines, and the
clickthrough URL or hero ASIN.

## eCommerce (REC) display creative

The exception to the no-text rule. A REC ad is an image section you compose
plus an auto-generated eCommerce section carrying live pricing, ratings, and
deal badges.

**Responsive upload** — supply all three: square 1200 × 1200, tall 900 × 1600,
wide 1200 × 628. Minimum resolution 600 × 600, maximum 5 MB.

**Size-specific custom images**

| Ad size | Custom image | Max file size | Headline text | Disclaimer |
|---|---|---|---|---|
| 300 × 250 / 336 × 280 | 900 × 480 | 100 kb | 36–78 pt | 27–36 pt, ≤ 2 lines |
| 160 × 600 / 300 × 600 | 600 × 1020 | 100 kb | 24–52 pt | 24 pt, ≤ 4 lines |
| 728 × 90 | 1140 × 180 | 60 kb | 36–52 pt | 28 pt, ≤ 1 line |
| 300 × 50 / 320 × 50 / 414 × 125 | 570 × 375 | 60 kb | 42–78 pt | 42–78 pt, ≤ 2 lines |
| 970 × 250 | 952 × 500 | 150 kb | 36–78 pt | 27–36 pt, ≤ 2 lines |

Copy constraints inside a REC custom image: **at most 10 words total**, at
most 2 type variations excluding the disclaimer, sentence case, headline
≤ 50 characters, disclaimer ≤ 60 characters in Arial regular or equivalent.
Even here the underlying restrictions hold: no white or transparent
background, no CTAs, no letterboxing, no pricing claims, nothing crowded.

## Published numbers that conflict

Amazon's spec pages disagree in a few places. Where they do, this file gives
both and you should confirm against the console's own upload dialog, which
validates on submit:

- **414 × 125 max file size** — the DSP desktop/mobile-web page says 100 kb;
  the mobile app banner page says 200 kb. Build to 100 kb to satisfy both.
- **Tall custom image recommendation** — the component-based creative page
  lists 1000 × 1000 for the 9:16 slot, which is not a 9:16 ratio; the
  eCommerce page lists 900 × 1600. Use 900 × 1600 and treat 338 × 600 as the
  documented minimum.
- **Logo file format and size for Sponsored Brands** — not published on the
  spec page. The console enforces it at upload; ask the user or test rather
  than asserting a number.

Amazon revises these pages without notice. When a number decides whether an
asset gets built, cite the page it came from and offer to re-check it.

---

**Provenance:** Amazon Ads specification and policy pages captured 2026-09-03:
`resources/ad-specs` and its sub-pages (`standard-media`, `dsp/desktop`,
`dsp/mobile-banners`, `component-based-creative`, `ecommerce`,
`sponsored-brands-video`), plus
`library/guides/sponsored-brands-display-ads-moderation`. Policy quotations
also appear in [`02-creative-policy.md`](02-creative-policy.md).
