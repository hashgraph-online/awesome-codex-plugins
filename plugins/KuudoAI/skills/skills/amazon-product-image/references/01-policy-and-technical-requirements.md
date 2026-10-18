# Policy and technical requirements

Use this reference for technical validation, main-image review, product identity, and restrictions that apply across image roles.

## Source status

This guidance is distilled from Amazon Seller Central product-image material. Amazon can vary requirements by marketplace, category, product type, and upload workflow. Treat the applicable current Seller Central requirement or API schema as authoritative when it differs from this reference.

## Technical validation

Commonly accepted product-image formats are JPEG, TIFF, PNG, and non-animated GIF. JPEG is generally preferred for photographic imagery. Verify the active upload workflow before relying on a format for a category-specific or offer-photo use case.

Check the actual file, not only its extension:

- The file opens and decodes completely.
- Extension and encoded format agree.
- Layered source files are flattened for delivery.
- Color is represented accurately; sRGB is the safest web-delivery choice.
- The image is sharp and free of visible pixelation, jagged edges, or destructive compression.
- Dimensions fall within the limits accepted by the active listing workflow.

The working general-product guidance in this package uses these tiers on the longest side:

| Size | Interpretation |
|------|----------------|
| Under 500 px | Below the general product-image minimum |
| 500–999 px | May display, but normally lacks zoom eligibility |
| 1,000 px or more | General zoom threshold |
| 1,600–2,000+ px | Useful production target when source detail supports it |
| Over 10,000 px | Above the general maximum |

Do not upscale a weak source merely to cross a threshold. Report the source limitation.

## Product identity

Every image must accurately represent the item attached to the listing. Compare the image with available title, ASIN, variant, quantity, color, material, model/version, and included contents.

Materially different products require the correct product identity rather than an image substitution. A visually polished image still fails if it changes the item, conceals a meaningful defect, invents included accessories, or shows the wrong quantity.

## Main-image requirements

For a general product main image, verify:

- a pure white open background, specified as RGB `255,255,255`;
- the complete product is visible and not cropped;
- the product covers about 85 percent of the image area without touching the edge (Amazon states fill as area, so never substitute coverage along one dimension; a long or thin product that cannot cover 85 percent of a square needs a canvas closer to its own proportions);
- one clear product view is shown;
- only the item and contents included with purchase appear;
- quantity, scale, color, and configuration match the listing; and
- there are no added callouts, badges, borders, inset views, watermarks, or promotional graphics.

Category rules can alter presentation, especially for apparel, footwear, multipacks, sets, and products whose packaging conveys delivered contents. Load the relevant special-case or fashion reference before declaring a result.

### White-background validation

Prompting for white does not verify white. Inspect the rendered file by sampling multiple open-background areas, including corners, and distinguish the open field from legitimate product pixels and a permitted contact shadow. If sampled background pixels are not pure white, use an image-processing or background-normalization step and inspect the result again.

Do not infer that a particular model, provider, or file format caused a near-white field without evidence from the actual file.

## Restrictions across image roles

All product imagery must remain accurate and must not add prohibited or misleading content. Review for:

- customer reviews, star ratings, or endorsement signals;
- prices, deals, discounts, coupons, shipping claims, or limited-time promotions;
- seller-specific contact details or watermarks;
- unsupported warranty, guarantee, certification, regulatory, safety, or health claims;
- Amazon names, logos, program marks, badges, or confusing imitations;
- nudity, sexualized presentation, exploitative content, or prohibited depictions of children; and
- text, graphics, or compositing that causes confusion about the delivered product.

Alternate images can use factual labels, diagrams, environments, and product-in-use context when the current category permits them. Main and swatch images are more restrictive. A claim printed on genuine packaging is different from an added overlay, but it must still accurately depict the product being sold.

## Brand and text accuracy

Labels, logos, tags, and printed product text are product-identity evidence. They must remain accurate, legible, and correctly placed. When an edit cannot preserve them reliably, retain those source pixels or composite verified artwork rather than accepting generated approximations.

## File naming and URL delivery

Where the upload workflow uses filename association, the common shape is:

```text
ProductIdentifier.VariantCode.Extension
```

Examples include `ASIN.MAIN.jpg` and numbered alternate-image codes. Use the codes required by the actual workflow.

For URL-based ingestion, provide a retrievable image URL that returns the image bytes directly. Pages, authentication barriers, redirects, incorrect content types, and mismatched identifiers can prevent association.
