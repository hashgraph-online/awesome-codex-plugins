---
name: suede-image
description: "Use when asked \"create an Open Graph image\" or to produce marketing heroes, banners, social graphics, mockups or image workflows. Suede AI chooses generation, editing, templates or real screenshots, then specifies layout, rights, export sizes, compression and image SEO. NOT FOR: paid-ad systems (use suede-ad-creative), video (use suede-video), app-store assets (use suede-aso), or social strategy (use suede-social)."
metadata:
  display-name: "Suede AI Image Skills"
  version: 2.1.0
---

# Suede AI Image Skills

Produce marketing imagery as a rights-aware, placement-specific system: choose the right production method, protect canonical brand assets, preserve real product truth, and verify the exported result. Use generation models and design tools to create efficient hero, social, mockup, banner, and preview workflows without fabricating interfaces or provenance.

## Compatibility

An agent with visual inspection and access to supplied brand assets. Image production requires an available generation or editing tool; local export commands require their named utilities. Prompt-only delivery remains available when production tools are absent.

## Before Starting

**Check for product marketing context first:**
If `.agents/product-marketing.md` exists (or `.claude/product-marketing.md`, or the legacy `product-marketing-context.md` filename, in older setups), read it before asking questions. Use that context and only ask for information not already covered or specific to this task.

Gather this context (ask if not provided):

### 1. Image Goal
- What type of image? (Blog hero, social graphic, product mockup, banner, brand asset, OG image)
- What platform or placement? (Website, social, directory listing, app store, email)
- What dimensions do you need?

### 2. Production Approach
- Do you have existing brand assets? (Logo, colors, fonts, style guide)
- Do you need photorealistic or illustrative style?
- Is this a one-off or a template for repeated use?

### 3. Technical Context
- Which image, browser, design, or local conversion tools are currently callable?
- What is the approved maximum cost and data-handling boundary?
- Do you need the image optimized for web performance?

Do not ask the user to paste API keys or secrets into the conversation.

---

## Choosing Your Approach

First discover the current production surface. Inspect callable tools and connected
accounts; do not assume a named model, provider, API, plugin, or design app is
available. Then choose among these methods:

| Approach | Best For | Candidate surface |
|----------|----------|-------------------|
| **Generation** | Original concepts and scenes | A callable image-generation tool |
| **Editing** | Authorized changes to supplied images | A callable editor with image-input support |
| **Template design** | Brand-consistent recurring assets | An authorized design app or local template |
| **Screenshot + overlay** | Truthful product showcases | Callable browser capture plus local layout |
| **Licensed media** | Existing photography or illustration | User-owned library or verified license source |

---

## AI Image Generation

Use generation only after the current tool and authority gates pass.

### Capability and authority gate

1. Confirm a generation or editing tool is callable in the current session.
2. Check its current official documentation for model availability, accepted
   inputs, output sizes, editing/reference support, safety restrictions, retention,
   commercial-use terms, and pricing. Record the source and check date.
3. Confirm rights to every uploaded logo, screenshot, photo, font, and reference
   image. Do not upload confidential or personal material outside its approved
   boundary.
4. Calculate the maximum cost for the requested attempts and get explicit approval
   before using a paid account or exceeding an already approved budget.
5. Confirm whether the user's request authorizes generation only, editing of
   supplied files, overwriting a source, or publication. These are separate gates.

Provider names and model versions are volatile. Examples such as OpenAI, Google,
Black Forest Labs, Ideogram, Midjourney, Recraft, and self-hosted diffusion are
research candidates, not routing instructions or capability claims.

### Selection criteria

- For text-heavy assets, prefer a deterministic overlay or design template; test
  any verified in-image text capability before committing to it.
- For repeated brand work, prefer locked templates and approved assets over a
  claimed consistency feature.
- For edits, use a tool whose current documentation and callable schema confirm
  image input and the required edit mode.
- For vectors, require a real vector export and inspect its paths; a raster image
  labeled as vector is not sufficient.
- For product UI, capture the live authorized interface rather than generating it.
- For volume, compare verified cost, rate limits, review time, and output quality
  on a small test batch.

If no suitable renderer or editor is callable, deliver a production-ready prompt,
layout spec, asset manifest, rights checklist, and export checklist. State clearly
that no image was generated; do not route the user to an unavailable tool as
though execution occurred. Use these exact headings:

```markdown
## Prompt
<Subject + Setting + Style + Lighting + Composition + Technical, one block,
ready to paste; note any text that must be a deterministic overlay instead>

## Layout Spec
Canvas WxH + ratio | safe margins | focal point | text zones with max character
counts | logo placement and clear space | color values

## Asset Manifest
Asset | origin (owned / licensed / captured / to be generated) | rights basis
and holder | attribution or expiry | file path or "to source"

## Rights Checklist
- [ ] Every uploaded or referenced asset has a confirmed rights basis
- [ ] No real person, endorsement, or product interface is fabricated
- [ ] Brand mark is the approved file, unmodified, or omitted
- [ ] Paid-tool cost approved, or no paid tool used

## Export Checklist
Destination | dimensions | format | quality target | file-size budget | alt text
Then apply the Optimization Checklist in "Image Optimization" before delivery.

## Not Done
No image was generated. What would unblock production: <tool, authority, asset>
```

### Prompting Basics

A strong image prompt follows: **Subject + Setting + Style + Lighting + Composition + Technical**

```
A laptop on a minimal white desk with an abstract analytics motif,
soft directional lighting from the left, shallow depth of field,
clean commercial photography style, 16:9 aspect ratio, 4K
```

**Common mistakes:**
- Too vague ("a business image"): add specific details
- Forgetting aspect ratio: always specify dimensions
- Requesting complex text: use overlays instead for anything beyond short headlines
- No style direction: "photorealistic," "flat illustration," "3D render"

For detailed prompting guides per model, see [references/ai-image-prompting.md](references/ai-image-prompting.md).

---

## Design Tools

For templated, brand-consistent work where AI generation is overkill or too unpredictable.

### Canva

Can be a candidate for template-driven social graphics, presentations, email
headers, and banners. Verify the connected account, current features, export
rights, plan limits, API availability, and callable integration before routing
work to it. Keep a human review gate for brand output.

### Figma

Can be a candidate when an authorized design file or component system exists.
Verify current account access and whether the available integration can read,
edit, export, or only inspect. Do not claim write access or create files merely
because a connector exists.

### When to Use Design Tools vs. AI Generation

| Scenario | Design Tool | AI Generation |
|----------|:-:|:-:|
| Exact brand guidelines must be followed | Yes | Maybe (with strong ref images) |
| Need many size variants of one design | Yes, if current resize/export capability is verified | Usually no |
| Unique hero image for a blog post | No | Yes |
| Recurring social media template | Yes | No |
| Product mockup with real UI | No (use screenshots) | No (hallucinated UI) |
| Abstract/creative visual | No | Yes |

---

## Marketing Image Workflows

### Blog & Article Hero Images

The image at the top of every post. Sets tone, improves shareability, required for OG/social previews.

1. **Define the concept**: what visual metaphor represents the topic?
2. **Choose the verified method**: callable generator, approved media, or a
   deterministic local/design template
3. **Confirm dimensions** from the actual site component and current social
   preview requirements
4. **Optimize to a measured quality and performance budget**

**Prompt pattern:**
```
[Visual metaphor for topic], clean modern style,
bright natural lighting, shallow depth of field,
professional blog header aesthetic, [verified width]x[verified height]
```

### Social Media Graphics

Platform-specific images for organic posts.

The values below are planning defaults, not current platform guarantees. Check the
platform's official specification on the work date and use its current safe zones,
file limits, and format rules.

| Platform | Planning size | Aspect ratio | Notes |
|----------|-------------|:---:|-------|
| X | 1200x675 | 16:9 | Large image card |
| LinkedIn | 1200x627 | 1.91:1 | Feed image |
| Instagram Feed | 1080x1350 | 4:5 | Profile grid crops to 3:4 since January 2025; keep the subject centered |
| Instagram Stories | 1080x1920 | 9:16 | Full screen vertical |
| Facebook | 1200x630 | 1.91:1 | Link share image |

**Workflow:**
1. Create the hero concept at highest resolution needed
2. Use a verified resize/export feature or manual crop for platform variants
3. Add text overlays deterministically when accurate text is required
4. Export at platform-specific dimensions

### Product Mockups & Screenshots

Showcase your product UI in context. AI models hallucinate UI: don't use them for this.

1. **Capture real screenshots** of your product at 2x resolution
2. **Frame in device mockups**: use browser frame, laptop, or phone templates
3. **Add context**: callout arrows, verified feature labels, before/after comparisons
4. **Annotate deterministically**: use a callable local layout workflow or an
   authorized design tool

Possible capture surfaces include browser tooling or an installed OS capture
utility. Discover what is currently callable, confirm authorization for the live
surface, and omit tools that are not available.

### Profile & Listing Banners

Banners for profiles, directory listings, and marketplace pages. Often the first visual impression.

These are planning references and can drift. Verify current official dimensions,
cropping behavior, safe zones, file limits, and format rules before production.

| Platform | Planning size | Notes |
|----------|------|-------|
| LinkedIn personal cover | 1584x396 | 4:1, safe zone center |
| LinkedIn company cover | 1128x191 | 5.9:1; LinkedIn recommends up to 4200x700 |
| Twitter/X header | 1500x500 | 3:1, partially obscured by avatar |
| Product Hunt gallery | 1270x760 | 5:3, up to 6 images |
| G2 profile | 1280x720 | 16:9, product screenshots preferred |
| GitHub social preview | 1280x640 | 2:1, shows in link cards |
| App Store screenshots | Varies by device | See suede-aso skill for full specs |
| Google Play feature graphic | 1024x500 | ~2:1, required for store listing |

**Best practices:**
- **Keep text minimal**: banners are seen at small sizes on mobile
- **Center critical content**: edges get cropped differently per device
- **Show the product truthfully**: use real UI screenshots when the listing is
  meant to demonstrate the interface
- **Match your brand**: use consistent colors, fonts, logo placement
- **Update deliberately**: refresh when the product, campaign, or positioning changes

**Workflow:**
1. Pick the platform(s) and note exact dimensions
2. For directories (Product Hunt, G2): use real product screenshots with light annotation
3. For profiles (LinkedIn, Twitter): use brand colors + tagline + optional product shot
4. Produce with a verified callable template workflow; add text deterministically
5. Test at actual display size: zoom out to check readability

### Brand Assets

Logos, icons, and illustrations. AI generation has limits here.

| Asset | AI Generation | Design Tool | Notes |
|-------|:-:|:-:|-------|
| Logo | Poor: inconsistent, not vector | Yes | Always design or commission logos |
| App icon | Concept exploration only | Yes | Refine manually and verify store rules |
| Illustrations | Good for style exploration | Depends | AI for concepts, finalize in design tool |
| Favicons | No | Yes | Derive from logo |
| Social icons | No | Yes | Use platform-provided assets |

---

## Image Optimization

Image bytes and dimensions can affect page performance. Measure the actual page
before attributing search or conversion results to image changes.

### Format Guide

| Format | Best For | Compression |
|--------|----------|-------------|
| **WebP** | Photos and graphics when target browsers support it | Lossy + lossless |
| **AVIF** | High-compression delivery when target browsers support it | Lossy + lossless |
| **JPEG** | Broad photo compatibility | Lossy |
| **PNG** | Transparency and lossless screenshots | Lossless |
| **SVG** | Trusted vector logos, icons, and illustrations | Vector |

### Optimization Checklist

- [ ] **Use a supported delivery format** and fallback strategy for the target browser matrix
- [ ] **Resize to display size**: don't serve 4000px images in 800px containers
- [ ] **Compress**: choose quality from visual review and the page's measured byte budget
- [ ] **Lazy load** below-the-fold images (`loading="lazy"`)
- [ ] **Set explicit dimensions**: `width` and `height` attributes prevent layout shift (CLS)
- [ ] **Use verified CDN optimization** when the current stack supports it
- [ ] **Add alt text**: describe what the image shows in plain words, using the
  page's topic phrase only where it is the honest description
- [ ] **Name files descriptively**: `pricing-calculator-dashboard.webp`, not
  `IMG_2041.webp`
- [ ] **Keep important images crawlable**: a real `<img>` with `src`, not a CSS
  background, and not blocked in robots.txt
- [ ] **Place the image near the text it illustrates** and give charts a
  caption that states the finding, so search and AI answers can quote it

The largest above-the-fold image is usually the Largest Contentful Paint
element. Do not lazy-load it; give it `fetchpriority="high"` and explicit
dimensions. Core Web Vitals and image-indexing audits route to
`suede-seo-audit`.

### Quick Optimization Commands

```bash
# Run only after confirming the named local utility is installed.
# Convert to WebP (using cwebp)
cwebp -q 80 input.png -o output.webp

# Batch convert with ImageMagick
mogrify -format webp -quality 80 *.png

# Optimize JPEG (using jpegoptim)
jpegoptim --max=80 --strip-all *.jpg
```

To inspect image references on a page, use the host's approved read-only HTTP
or browser tool against a verified public HTTPS URL. Refuse loopback,
link-local, or private-network destinations; do not attach ambient cookies or
authentication headers; and do not send local files, credentials, or workspace
content. Inspect the returned HTML for image `src` values and report a failed or
unsafe fetch as unverified.

---

## OG & Social Preview Images

The image that appears when your URL is shared on social media, Slack, Discord, etc.

### Common Meta Tags

Verify the current crawler/platform specification and use absolute public URLs.
The values below are a starting template, not proof of platform compliance.

```html
<meta property="og:image" content="https://yoursite.com/og/page-name.jpg" />
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="630" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:image" content="https://yoursite.com/og/page-name.jpg" />
```

### Dynamic OG Images

Generate OG images programmatically for dynamic pages only after verifying the
project's current framework, installed packages, and supported runtime:

- An installed framework-native image route
- A local HTML/SVG-to-image renderer
- An authorized media service with verified template and export capabilities

For repeated page types, a deterministic template can reduce manual work. Measure
preview correctness and production time; do not promise a search outcome.

---

## Common Mistakes

1. **Skipping image optimization**: oversized images can materially hurt page performance
2. **No preview image**: platforms may fall back to a less useful preview
3. **Inconsistent brand visuals**: use locked, approved templates for consistency

---

## Halt Contract

Use this exact format when a callable tool, cost approval, rights confirmation,
or the approved brand asset blocks the requested result:

```text
HALT: <one-line blocker>
Why it blocks: <specific missing authority or evidence>
Resolve with:
1. <option>
2. <option>
3. <option, when useful>
Waiting for: <the exact item or approval>
```

Continue with the no-tool handoff artifacts above only when they remain useful
and do not imply an image was produced.

---

## Boundaries

- For Suede visuals, use only `docs/assets/suede-ai-logo-transparent.png` with SHA-256 `83a7ee0317e4debe2e7b076c20ba067feb76a587f9e829dc6310ae4be4b44dfa`.
- Do not redraw, trace, approximate, recolor, distort, typeset, or generate a replacement for the approved Suede S mark. If the canonical file is missing or its checksum differs, omit the mark, name the blocker, and request the approved file.
- Do not claim an image is licensed, rights-cleared, authentic, accessible, optimized, or platform-compliant without verifying the relevant source or output.
- Do not use a paid provider, upload protected material, or cross an approved
  account or data boundary without explicit authority and a verified maximum cost.
- Do not publish, overwrite source assets, or replace real product screenshots without explicit authorization.
- Do not invent people, endorsements, product interfaces, performance results, or provenance, and do not decide rights or brand exceptions for the user.

## Routing

- Use `suede-ad-creative` for paid-ad production and `suede-video` for motion.
- Use `suede-social` for channel strategy and `suede-site-alchemy` for conversion placement.
- Use `suede-social` for platform format contracts (Reel covers, carousel slide counts, Story frames) before producing those assets here.
- Use `suede-seo-audit` for image-search checks and `suede-aso` for app-store screenshots.
- Use `suede-directory-submissions` for directory gallery planning.

## Worked contract

[Worked contract](references/usage-contract.md) gives a bounded input, expected output and failure check for this workflow.
