# Image stack and merchandising

Use this reference after compliance requirements are satisfied. Everything here is optimization guidance unless explicitly tied to a current category requirement.

Sources: stack sequencing and per-image design guidance adapted from Pixii, *What Images Should I Have on an Amazon Listing?* (2025-12-26), <https://www.pixii.ai/updates/what-images-should-i-have-on-an-amazon-listing/>, which is practitioner guidance rather than Amazon policy; competitor-comparison guidance from Amazon's seller blog, *How to create A+ Content* (2025-09-24), <https://sell.amazon.com/blog/a-plus-content-design-guide>.

## Build the stack around buyer questions

Use the image slots exposed by the current listing workflow. Do not assume that upload capacity, visible gallery positions, or video placement is identical across marketplaces, categories, devices, or time.

Shoppers decide in two steps. The main image earns the click from search results. Every later image earns the purchase by answering a question the buyer would otherwise have to ask, return the item over, or leave a negative review about. Give each image one buyer question; an image that tries to answer three answers none of them at thumbnail size.

A useful default sequence for hard goods:

| Position | Image | Buyer question |
|---|---|---|
| 1 | Compliant main image | "Is this what I searched for?" |
| 2 | Benefit overview infographic | "Why this one?" |
| 3 | Lifestyle / in use | "Does it fit my life?" |
| 4 | Feature close-up or materials | "Is it well made?" |
| 5 | Size and scale | "How big is it really?" |
| 6 | Comparison, or a use-case chooser | "Which one is right for me?" |
| 7 | What's in the box and compatibility | "What exactly do I get, and will it work with mine?" |
| Later | Category-dependent | Alternate angles, assembly or care, fit, or a truthful outcome. |

Adapt the order to whichever question is most decisive for this product — if size or fit drives returns, move the scale image up. Position 2 is the next image a shopper sees when swiping or scanning thumbnails, so it carries the summary pitch; a single close-up there wastes the handoff from the main image. Later positions get less attention, and some layouts show only the first several thumbnails, so order by importance.

Choose only the images needed to answer important purchase questions. Slot count is not a quality target. Missing scale and missing contents images are, however, common and avoidable causes of "smaller than expected" and "missing parts" returns.

## Per-image guidance

Every added string on these images is subject to the claim-coverage gate in `06-generation-editing-and-audit.md`.

### Benefit overview infographic

- One headline stating the core promise, then 3–5 callouts. More than five reads as a flyer on a phone.
- Each callout pairs a visible feature with its concrete outcome — for example, "Double-wall steel → cold 24 hours" — and points at that feature on the product.
- Short phrases, not sentences or paragraphs; one idea per callout; simple icons where they speed scanning.
- Large type with high contrast against its background. Keep added text off the product itself.

### Lifestyle

- The product stays the focal point: prominent, unobstructed by hands or props, and the sharpest element in the frame.
- The scene is believable for the real customer and use; avoid over-styling that hides the product or confuses its size.
- Props must not read as included items. If a shopper could reasonably expect a prop in the box, remove it.
- Lighting, shadows, reflections, and white balance stay consistent within the scene and with the rest of the stack.

### Feature close-up

- A macro or tight crop of the one feature that most justifies the price — texture, finish, stitching, hardware, or mechanism.
- Critical sharpness and clean edges; a soft or noisy close-up signals low quality, the opposite of its job.
- At most one short callout naming the feature and its outcome, pointing at something visible in the frame.

### Size and scale

- Show the product beside a familiar reference — a hand, countertop, backpack pocket, shelf, or common object — at true relative size.
- Use clean dimension lines with simple units, taking every number from the seller's specification. Never estimate dimensions from a photograph.
- Use a neutral, normal-focal-length perspective. Wide-angle exaggeration or forced perspective that makes the product look larger misrepresents it.
- A couple of dimension lines beat a cluttered ruler overlay.

### Comparison, or its replacement

A comparison is only as honest as its weakest cell: every value in the "other" column needs a source too. Decide which comparison the evidence supports:

1. **The seller has a lineup** (sizes, tiers, models, or bundles): compare up to three of the seller's own products, every cell from the seller's specifications. This is the strongest option — it helps shoppers choose the right variant and keeps them within the brand — and it mirrors Amazon's A+ comparison chart, which compares products the brand sells.
2. **A single product, with sourced data against an alternative the shopper is genuinely weighing:** use an unbranded column such as "Typical plastic container". Every cell in that column must come from the seller's test data or be true by definition.
3. **Neither:** skip the comparison. Give the position to the next buyer question no other image answers — a use-case chooser across the product's own configurations (for example, two included lids and when to use each), instructional steps, or care.

Do not build a strawman. A comparison against a category the shopper has already ruled out — single-wall versus insulated, for someone who searched "insulated bottle" — fills the position without informing the decision.

Amazon's A+ guidance says "Never reference or compare products with competitors." The general image requirements in `01-policy-and-technical-requirements.md` do not state this for gallery images, and third-party guidance disagrees, so leaving competitor names and products out is a cautious recommendation that echoes the A+ rule. In an audit, report a named competitor as a risk with that requirement class, not as a verified image-policy failure.

Design for a phone: 3–6 rows with one attribute per row; at most three product columns plus the label column; short values, numbers, or check marks rather than sentences; the column for this listing's product highlighted; no unsupported superlatives such as "best", "#1", or "strongest".

### What's in the box

- Lay out every included item at correct relative scale, with quantities labeled where helpful. The seller's contents list is the source of truth.
- Show nothing that isn't included.
- Factual compatibility statements (devices, sizes, refills) belong here.
- Do not add certification, approval, warranty, or guarantee badges as "trust signals"; `01-policy-and-technical-requirements.md` restricts them across image roles. A mark printed on genuine packaging may appear only as part of a truthful photograph of that packaging.

## Image roles

- **Feature image:** isolates a material product detail.
- **Infographic:** explains factual dimensions, materials, quantities, compatibility, or operation.
- **Lifestyle image:** shows realistic use, environment, scale, and audience context.
- **Detail image:** shows texture, hardware, controls, seams, ingredients, or construction.
- **Instructional image:** explains assembly, installation, cleaning, care, fit, or use.
- **Comparison image:** distinguishes verified product options or capabilities without disparaging competitors or inventing claims.
- **Rendered or cutaway image:** explains an otherwise invisible structure while remaining faithful to the actual product. Build it only from seller evidence of that structure, such as a cross-section photograph or engineering drawing.

## Stack-level checks

- **Same product, same look.** Color, finish, and proportions must match across every image; a shift between positions reads as a different product. Generate each image from the original source photography, then compare the finished images with each other, not only with the source.
- **Phone legibility.** Preview every text-bearing image scaled to phone width, about 400 px wide. If any text needs pinch-zoom to read, cut words or enlarge type. A generation prompt is written before any preview exists, so state a size in it: values and callouts at about 4 percent of canvas height or more, roughly 16 px when a 2,000 px image is shown 400 px wide. That figure is a working heuristic derived from the phone test, not an Amazon requirement.
- **One visual system.** Use consistent fonts, icon style, and palette across infographic, comparison, and scale images.

## Optimization criteria

- Make each image answer one primary buyer question.
- Preserve consistent product identity, color, proportions, and included contents across the stack.
- Keep text legible on mobile and remove copy that does not improve understanding.
- Show real scale, fit, texture, and functional detail.
- Use lifestyle context that matches plausible use.
- Keep comparisons factual, supportable, and category-appropriate.
- Review performance data before attributing conversion changes to imagery.

## Common failures

- Treating alternate-image flexibility as permission for unsupported claims.
- Moving multiple views, feature panels, or infographic content into the main image.
- Treating every image like a flyer: too much text, no hierarchy, unreadable on a phone.
- Omitting a scale image when dimensions are not visually evident, or a contents image when the box holds more than the product.
- Showing props that appear included.
- Building a comparison whose "other" column the seller cannot source, or against an alternative the shopper has already ruled out.
- Using generated or composited scenes that alter product shape, material, scale, color, or capability.
- Inconsistent lighting or color between images.
- Filling every slot with redundant angles.
- Presenting a merchandising recommendation as an Amazon requirement.

## Outcome language

State recommendations as hypotheses tied to a customer question—for example, "Add a scale image because dimensions are not visually evident"—rather than claiming a universal conversion lift.
