---
name: sirv-ecommerce
description: End-to-end product imagery workflows for e-commerce with Sirv AI Studio - Shopify image push and product sync, marketplace compliance (Amazon, eBay, Walmart), supplier portal review and autofix, saved workflow pipelines, and PIM/DAM product-asset management. Use when pushing images to Shopify, syncing Shopify products, preparing marketplace-compliant product images, automating supplier image intake, running multi-step product image pipelines, or wiring AI processing into a store catalog.
---

# Sirv E-commerce Workflows

Product imagery operations from processing to publishing: AI Studio processes images, Sirv stores and delivers them, and the MCP tools below push results into Shopify, run saved pipelines, and enforce marketplace/supplier standards.

Prerequisite: the sirv-ai MCP server (setup in `../sirv-ai-studio/SKILL.md`). Processing tools themselves (remove background, upscale, lifestyle, alt text) are documented there; this skill covers the store-facing layer.

## Default Workflow

1. Check the connection state before promising anything: `sirv_shopify_status` returns `connected`, `valid`, and `needsReconnect` - if not connected/valid, stop and have the user connect the store in Sirv AI Studio.
2. Get products into the PIM when working catalog-wide: `sirv_sync_shopify_products` imports products and images **from Shopify into Sirv AI Studio** (inbound only; max 500 per call, default 100).
3. Process images per `../sirv-ai-studio/SKILL.md` (single tools) or run a saved pipeline with `sirv_execute_workflow` for repeatable multi-step jobs.
4. Validate against marketplace rules before publishing: image review presets (Amazon, eBay, Shopify, Walmart) and `sirv_run_supplier_autofix` for automated correction.
5. Push results to the store with `sirv_push_image_to_shopify` - choose the `upload_strategy` deliberately (see below).
6. Verify in the store: image visible on the product, correct position/featured state, alt text present.

## Shopify Tools

All accept optional `orgId` (UUID) - omitted means the default organization.

| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `sirv_shopify_status` | Validate store connection/token | none |
| `sirv_sync_shopify_products` | Import products + images Shopify → PIM | `maxProducts` (1-500, default 100), `importImages` (default true) |
| `sirv_push_image_to_shopify` | Publish an image to a product | `productId`, `image_url`, `alt_text`, `upload_strategy`, `set_as_featured`, `source_image_id` |

### Push semantics - read before pushing

- `productId` accepts numeric or `gid://shopify/Product/...` form.
- `upload_strategy`:
  - `add` (default) - appends to the product's images.
  - `replace_source` - deletes one existing image (`source_image_id` required) then adds. Use for "replace this photo with the processed version".
  - `replace_all` - **deletes every image on the product** before adding. Destructive; confirm with the user before using it.
- `set_as_featured: true` puts the new image at position 1.
- Push attaches media at the **product level**, not to variants - it will not create or link variant images.
- Sync direction is inbound-only via MCP; pushing is the only outbound operation. Don't tell users "sync will upload your images to Shopify" - it won't.

## Saved Workflows (Pipelines)

Users build pipelines visually in Sirv AI Studio (e.g. Remove BG → Validate → Autofix → Alt Text); agents execute them:

| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `sirv_list_workflows` | Discover saved pipelines | none |
| `sirv_get_workflow` | Inspect steps/config | `workflow_id` (UUID) |
| `sirv_execute_workflow` | Run on images | `workflow_id`, `image_urls` (1-100) |

Execution facts: runs take 30 seconds to several minutes; every step spends credits per image (result reports `totalCreditsUsed` and per-step `creditsUsed`); interactive steps (`review`/`imageReview`) and client-side steps (`saveToCsv`) are skipped in MCP runs; `saveToSirv`, `addMetaTags`, and `setProductMeta` steps require the user's Sirv account to be connected. Results are per-image with `success`/`partial`/`error` status and `finalOutputs` URLs.

Prefer a saved workflow over hand-chaining single tools when the user will repeat the process - it keeps settings consistent across batches.

Store-facing step types worth knowing when reading a workflow: `pushToShopify`, `channelReadinessGate` (marketplace channel readiness), the DAM/PIM steps (`saveToDam`, `linkToProduct`, `writeProductAttributes`, `addToCollection`), and e-commerce AI steps that exist only as workflow steps, not standalone tools: smart crop, add shadow, color variants, ghost mannequin, image review. Workflow Triggers can run pipelines automatically on events (configured in the web app).

## Supplier Portal (Supplier Portal Pro tier)

For teams receiving product images from suppliers/vendors:

| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `sirv_get_supplier_sftp_status` | Check SFTP intake config (host, port, username, root path) | none |
| `sirv_get_supplier_review_assist_requirements` | Fetch the active image spec: rules, `passThreshold`, `failAction` (reject/warn/queue_manual), filename policy | none |
| `sirv_run_supplier_autofix` | AI-fix an image against failed rules | `image_url`, `mode` (auto/prompt), `failed_rules`, `max_iterations` (1-5, default 3), `enabled_fixes` (upscale/remove_background/smart_crop/image_to_image), `upscale_model` |

Autofix spends AI credits per iteration. Fetch requirements first, pass the actual `failed_rules` in, and report `appliedFixes` from the response rather than assuming what changed.

## Marketplace Compliance

- Image Review validates dimensions, background, watermarks, and frame fill against marketplace presets (Amazon, eBay, Shopify, Walmart) - run it before pushing to a marketplace channel, then autofix and re-review.
- Typical Amazon main-image loop: remove background (pure white) → validate → autofix failures → alt text → push.
- Delivery formatting (exact pixel sizes, padding, white canvas) belongs in Sirv Dynamic Imaging profiles (`../sirv-dynamic-imaging/SKILL.md`), not in repeated AI processing.

## Red Flags

- Using `replace_all` without explicit user confirmation - it wipes the product's existing gallery.
- Expecting `sirv_sync_shopify_products` to upload images to Shopify (it imports, never exports).
- Pushing before checking `sirv_shopify_status` - a stale token fails with a confusing error; `needsReconnect: true` means the user must re-auth in the web app.
- Running `sirv_execute_workflow` on 100 images without checking credits (`sirv_get_usage`) or warning about runtime.
- Expecting variant-level image assignment from the push tool.
- Calling supplier tools for accounts without Supplier Portal Pro - they will fail on tier access.

## Verification

- After push: fetch the product (store admin or `sirv_list_products_with_assets`) and confirm the image, its position, and alt text. PIM/DAM tool parameters live in `../sirv-ai-studio/references/asset-product-tools.md` — note product deletes are permanent there, unlike soft asset deletes.
- After sync: report `products.created/updated` and `images.imported/skipped` from the result, not assumptions.
- After a workflow run: check per-image statuses; surface `partial`/`error` items with their step errors instead of declaring success on the batch.
- After autofix: re-run the review/requirements check to confirm the image now passes.
