---
name: magic-hour-marketplace-images
description: Build a product listing image set with Magic Hour, including a clean main image, detail and lifestyle images, and accurate feature layouts. Use for marketplace or ecommerce listing assets when Magic Hour is the chosen media provider.
license: MIT
metadata:
  author: magichourhq
  version: "1.0.0"
---

# Magic Hour marketplace images

Deliver individual listing assets that answer a buyer's questions while preserving the actual product. A beautiful but different product, invented feature or flattened sheet of six images fails the job.

Use the connected Magic Hour MCP at `https://mcp.magichour.ai/` or the project's existing API integration. For setup, use the [connection guide](https://github.com/magichourhq/skills/blob/main/docs/quickstart.md#connect-once). Verify `account_retrieve`, inspect current schemas and check the intended generation cost against existing authorization.

## Plan from facts and destination

Read the supplied product photos, listing copy, specifications and brand files first. Separate verified facts from visual observations and missing information. Ask only for an absent reference or fact that prevents the requested asset. Infer layout, lighting and typography when delegated.

For a named marketplace, verify its current official image requirements for the locale, category and placement; main-image and secondary/A+ rules differ. Do not hardcode a universal image count, size or compliance guarantee. If the destination is unspecified, create a clearly labeled general product-page set and state its actual dimensions.

Choose roles from the buyer's unanswered questions. A useful default is a clean main image, one genuine detail and one contextual image; expand only when the brief or product warrants it. For larger sets, read [listing roles](references/listing-roles.md). Do not manufacture five benefits to fill five slots.

## Preserve the product; vary the explanation

Use `ai_image_editor_create_image` with the original authorized product photo. Preserve exact geometry, material, controls, label, color and pack contents. Reuse the accepted source for each scene instead of feeding every derivative into the next edit. Use `ai_image_generator_create_image` only for an original fictional product or a background that does not replace the real product.

Start with one demanding image at a resolution that reveals critical product details. Inspect the downloaded image before producing the rest. A small thumbnail is not proof of label accuracy. Use a neutral background and full silhouette for a clean main image; put explanatory copy in secondary layouts only when the destination permits it.

Create or edit photographic layers first. Compose exact headlines, dimensions and callouts using local/design tools when available. This makes a copy change cheap and avoids regenerated misspellings. Keep the product label intact; do not cover a changed label with promotional copy and call preservation successful.

Request only a supported number of images. Record each project ID immediately and poll it with `wait_for_image_project`. Retrieve the exact returned download URLs; do not duplicate paid jobs after a polling timeout. Retry a failed creative result only within the existing budget, changing the smallest useful variable.

## Finish each asset

Compare each image with the reference: silhouette, cap/handle, visible side, label, color and quantities. New camera angles require matching reference views when unseen construction matters. If only one view exists, reuse that view or identify a simulated angle; never present an invented back panel as documentary product photography.

Inspect actual pixels, dimensions, crop, text accuracy and mobile readability. A detail crop cannot reveal information absent from the source. Check neighboring images together for consistent product color and scale, then export individually with descriptive filenames. Preserve any service watermark and disclose whether it prevents the requested placement.

Return the files in listing order, editable copy/layout sources, and a short mapping of image to supported fact. Identify any image still unsuitable for upload and why. Publishing to a store is a separate action. Keep accepted photography for later variants; new copy or a different crop should not spend generation credits.
