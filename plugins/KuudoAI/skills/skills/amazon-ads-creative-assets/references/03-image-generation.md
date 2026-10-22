# Generating compliant ad images

How to turn a brief into images that clear moderation on the first submission.
Written for an agent driving an image model; the constraints are the same
whether a person or a model produces the file.

Contents: [The failure modes](#the-three-failure-modes) · [Before generating](#before-generating) ·
[Prompt pattern](#prompt-pattern) · [The negative list](#the-negative-list) ·
[Product fidelity](#product-fidelity) · [Composition for cropping](#composition-for-aggressive-cropping) ·
[Templates](#templates-by-brief-type) · [Validation](#validate-before-handoff)

## The three failure modes

Almost every rejected generated asset fails one of these, and all three are
predictable enough to design against.

1. **The model adds text.** Image models put words on things — a logo on the
   mug, a label on the box, a slogan across the sky. For a Sponsored Brands or
   Sponsored Display custom image that is an automatic rejection, because no
   branding text, logos, or CTAs may appear. This is the single most common
   defect, and it needs an explicit negative instruction plus a visual check
   of the output, since the prompt alone will not reliably suppress it.
2. **The product is wrong.** A generated product that differs from the real
   one is misleading content, not an artistic choice. Amazon judges the ad
   against the detail page.
3. **The background is white.** Models default to clean studio white, which is
   exactly what a custom image may not have, and what a borderless banner may
   not use either.

## Before generating

Settle these five, because each one changes the file you produce:

1. **Program** — Sponsored Brands, Sponsored Display, DSP component-based,
   eCommerce REC, or a finished banner. This decides whether text and logos
   belong in the image at all. See the routing table in
   [`01-asset-specs.md`](01-asset-specs.md).
2. **Aspect ratios** — for custom images, produce square, wide, and tall
   unless the user says otherwise; a single wide image gets center-cropped
   into the other placements.
3. **Real product references** — get the seller's actual product photos. Any
   shot where the product is visible should be generated with those as
   reference images rather than from a text description.
4. **Marketplace** — decides the language of any permitted text and pulls in
   regional file-size limits.
5. **What the ad has to communicate** — the product in use, the benefit, the
   moment. The image carries this alone; the headline is a separate asset.

## Prompt pattern

Build the prompt in this order. It mirrors how a photographer would brief a
shoot, which is the register these models respond to best.

```
[Shot type] lifestyle photograph of [real product, named with its visible
physical details] being [used / held / worn] by [subject, described with
inclusive specificity] in [setting].
[What the subject is doing and why it reads as a genuine moment].
[Lighting: source, direction, quality]. [Colour palette that contrasts with a
white page]. [Depth of field and focal length].
Composition: product prominent and unobstructed, subject centred with clear
margin on all four edges for cropping.
No text, no words, no letters, no logos, no signage, no watermarks, no
graphic overlays anywhere in the image.
```

The final line is not optional decoration. State it every time, even when the
brief says nothing about text, because the model will otherwise invent some.

## The negative list

Carry this into every generation for a Sponsored Brands, Sponsored Display, or
DSP component-based custom image:

> No text, words, letters, numbers, or typography of any kind. No brand logos,
> wordmarks, or emblems. No call-to-action buttons or badges. No price tags,
> discount stickers, star ratings, review quotes, or award seals. No Amazon
> branding, packaging, boxes, smile marks, or delivery vans. No watermarks or
> signatures. No white, off-white, or transparent background. No letterboxing,
> pillarboxing, or borders. No collage, split-screen, or multi-panel layout.
> No clutter — one clear subject.

For a **finished banner** the list changes: text and the advertiser's logo are
required, so drop those clauses and keep the rest, adding "no fake buttons or
UI elements that imply clickable functionality."

## Product fidelity

Where the product appears, treat its appearance as data, not style. Append to
the prompt:

> Preserve exactly, as in the reference images: the product's shape,
> proportions, colours, materials, finish, and the placement and count of every
> visible component. Reproduce packaging text and labels exactly as they appear
> in the references, sharp and legible; do not re-letter, restyle, translate,
> or invent any label. Do not add features, accessories, or variants that are
> not in the references.

Then check the render against the reference before it moves on. Naturally
occurring packaging text is permitted, which is why it must be *correct*
rather than absent.

## Composition for aggressive cropping

One custom image serves up to 12,000 size variations, spanning square, wide,
and tall. Amazon crops toward the centre.

- Keep the product and the subject's face inside the central 60% of the frame.
- Leave even margin on all four edges. Anything at an edge will be cut on some
  placement.
- Avoid compositions whose meaning depends on the full width — a subject at
  the far left reading toward empty space at the right survives neither the
  square nor the tall crop.
- For DSP component-based creative, respect the published safe zones and use
  Amazon's PSD templates when detail sits near an edge.
- Contrast the background against a white page, since the ad may render
  borderless.

## Templates by brief type

**Product in use (the default for a custom image)**

> Eye-level lifestyle photograph of [product] being used by [subject] in
> [setting]. [Action that shows the benefit]. Warm directional window light
> from the left, soft shadows. [Palette] tones filling the frame. 50 mm lens,
> shallow depth of field with the product sharp. Product prominent and
> centred, generous margin on all edges. No text, logos, watermarks, or
> overlays; no white or transparent background.

**Product alone, in context**

> Three-quarter view of [product] resting on [surface] in [environment], with
> [contextual props that imply use without clutter]. Soft natural light,
> [palette] background that contrasts with white. Macro detail on [material].
> Single clear subject, centred with margin. No text, logos, badges, or
> overlays; no white or transparent background.

**Seasonal or occasion**

> [Occasion] scene: [subject] and [product] in [setting] with [seasonal cue
> that is not a holiday trademark]. [Light quality]. Palette of [colours]. No
> text, logos, gift-card art, or promotional badges; no white background.

Note on seasonal work: the creative may evoke a season, but any deal language
belongs in the headline, and only when a live Amazon deal backs it.

**Finished mobile banner (composed, text allowed)**

> [Size] banner at 2X: [product] on the [left/right] third, brand logo in the
> [corner], headline "[≤ 50 characters, sentence case]" at ≥ 16 pt at 2X.
> High-contrast [palette] background, non-white 1-pixel border. Clean margins,
> no fake buttons, no CTA text, nothing crowded.

## Validate before handoff

Check every generated file against this list. It is fast, and it is cheaper
than a 72-hour review cycle.

**Technical**
- [ ] Dimensions match the program's spec for that aspect ratio; ≥ 600 × 600
- [ ] File size within budget (5 MB custom images; kb budgets for banners,
      halved in FR, IT, ES, JP)
- [ ] Format accepted for the program; not blurry, pixelated, or stretched

**Content**
- [ ] Zero text anywhere, unless the program allows it — read the image, don't
      trust the prompt
- [ ] No logo inside the image (unless a banner or REC creative)
- [ ] No prices, ratings, reviews, badges, or Amazon marks
- [ ] Background is not white, off-white, or transparent
- [ ] No letterbox, pillarbox, or border bars
- [ ] Product prominent, unobstructed, matching the real product
- [ ] Subject and product inside the central 60%, margins on all edges
- [ ] Models are diverse across the campaign's asset set
- [ ] Nothing contradicts the landing page

Anything failing content checks gets regenerated, not patched in the caption.
Record which checks ran in the handoff manifest
([`06-handoff-contract.md`](06-handoff-contract.md)) so the reviewing human
sees what was verified and what wasn't.
