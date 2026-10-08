---
name: magic-hour-product-visuals
description: Create or edit a Magic Hour product image with controlled composition, geometry, branding and copy space. Use for product shots, hero images, packaging and ecommerce visuals when Magic Hour is requested or is the project's chosen media provider.
license: MIT
metadata:
  author: magichourhq
  version: "1.3.0"
---

# Magic Hour product visuals

Deliver a product image that fits its intended placement and preserves the details that make the product recognizable. Treat a project ID as an intermediate result and inspect the finished image before calling it complete.

Generation consumes Magic Hour credits. Use a connected Magic Hour creation MCP at `https://mcp.magichour.ai/` when available. Otherwise read `references/setup.md`. Discover the current schema before choosing a model, resolution, image count, or cost.

Infer the treatment from the customer's intended use; recommend one direction instead of asking them to choose technical parameters. Honor existing budget and delegated creative decisions, inspect intermediate results yourself and continue unless the user requested draft approval. Show the finished image first; retain technical records with the project. For catalog, lifestyle, detail, in-hand or coordinated sets, read [reference photoshoot](references/photoshoot.md).

## Define the deliverable

Extract or infer:

- where the image will appear, such as a product page, ad, marketplace listing, or website hero
- aspect ratio, resolution, crop tolerance, and required negative space
- product shape, material, finish, color, label, logo, and exact text
- camera angle, scale in frame, surface, background, lighting, and shadow
- details that must remain unchanged
- visible failures that make the image unusable

For a hero, specify which side needs empty space for copy. For an ecommerce listing, keep the full product inside the frame with a clean silhouette. When exact product identity, packaging, or branding matters, use an authorized reference and edit it rather than recreating it from text.

## Choose generation or editing

- With no source image, call `ai_image_generator_create_image`.
- With a usable source that needs a new setting, cleanup, relighting, repositioning, or other controlled change, call `ai_image_editor_create_image`.
- AI Image Editor requires an input image. Never route a prompt-only creation request to it.

Use one image at a resolution that reveals the product's critical details and fits its placement. A low-resolution preview is useful for composition, not final label fidelity. Check cost against existing authorization and ask only when it does not cover the intended work. Prefer the live recommended model for a general request and choose a specialist only when the current schema describes the needed behavior.

## Write a production brief

Write the prompt in this order:

1. intended image type and aspect ratio
2. one product with material, shape, color, and orientation
3. exact composition and space allocation
4. lighting, surface, background, shadow, and reflection
5. required label, logo, or text in quotation marks
6. elements that must remain fixed
7. concrete rejection conditions

Use direct visual language. A useful pattern is:

`Premium 16:9 product hero photograph. One [product] in the right third, fully visible, with clean negative space across the left 40 percent. [Camera and material]. [Lighting, surface, and background]. Preserve [shape, colors, logo, and exact label]. No extra objects, duplicate text, warped geometry, unintended marks, or watermark.`

For editing, describe the change first and then state what remains unchanged. Compare against the original reference, not just the prompt: a prettier bottle with a different cap or viewpoint is still a failed preservation edit. Do not stack unrelated styles or ask one image to show several scenes. Keep promotional copy in a separate layout layer when a suitable tool is available; preserve text already printed on the product.

## Inspect before delivery

Wait for the existing image project with `wait_for_image_project`. After it reports `complete`, use the exact returned download URL and inspect the actual output for:

- actual downloaded dimensions, aspect ratio, crop, product scale, and requested negative space; do not trust the requested ratio alone
- straight edges, plausible materials, and coherent reflections and shadows
- accurate product geometry, cap, handle, controls, packaging, and colors
- one correct instance of required text or logo
- no misspelling, duplicate label, invented brand-like mark, or distracting object; disclose any service watermark and do not promise an unwatermarked file without checking eligibility
- no anatomy or identity problem when a person is intentionally present

If the result fails, change the smallest useful variable. Use AI Image Editor for a localized correction when the rest of the image is strong; regenerate when composition or product identity is fundamentally wrong. Another generation spends credits, so stay inside the user's authorized budget.

When the product image will become video, accept the still first and use the image-to-video skill when installed. Otherwise discover `image_to_video_create_video`, pass the accepted image, prompt for motion, retain the ID, wait and inspect the complete clip. Do not require another skill installation to finish a supported request. Return the finished artifact, its saved location and any material limitation; retain project IDs for recovery.
