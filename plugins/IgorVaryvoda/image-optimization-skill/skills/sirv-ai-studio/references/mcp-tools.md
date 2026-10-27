# Sirv AI Studio MCP Tools Reference

Full parameters, models, and options for the sirv-ai MCP server tools, verified against the server source (July 2026). Server setup lives in SKILL.md.

The server registers ~46 tools. The core processing tools are documented fully below; asset management (DAM), product (PIM), workflow, Shopify, and supplier tools are listed at the end — introspect their schemas at runtime for parameters.

## Table of Contents

1. [Background Processing](#background-processing)
2. [Image Enhancement](#image-enhancement)
3. [Image Generation](#image-generation)
4. [Product & E-commerce](#product--e-commerce)
5. [3D & Video](#3d--video)
6. [Batch Operations](#batch-operations)
7. [Account](#account)
8. [Asset, Product, Workflow & Shopify Tools](#asset-product-workflow--shopify-tools)
9. [Usage Examples](#usage-examples)

Credit costs are set per model in the service and change as models evolve — confirm with `sirv_get_usage` before large jobs. Costs below are current per the source.

## Background Processing

| Tool | Parameters | Cost |
|------|------------|------|
| `sirv_remove_background` | `image_url`, `provider` (birefnet/bria), `model`, `operating_resolution` | birefnet 1, bria 2 |
| `sirv_background_replace` | `image_url`, `prompt`, `ref_image_url`, `model` | flux-kontext 3, bria 4, nano-banana 15 |
| `sirv_object_removal` | `image_url`, `mask_url` | 3 |

**Background Removal Models:**
- `General Use (Light)` - Fast processing
- `General Use (Light 2K)` - Fast, higher resolution
- `General Use (Heavy)` - Best quality (default)
- `Matting` - For hair/fur details
- `Portrait` - Optimized for people
- `General Use (Dynamic)` - Adaptive

**Operating Resolutions:** `1024x1024`, `2048x2048`, `2304x2304`

**Background Replace Models:** `bria` (default), `flux-kontext`, `nano-banana`

## Image Enhancement

| Tool | Parameters | Cost |
|------|------------|------|
| `sirv_upscale` | `image_url`, `scale` (int 2-4, default 2), `model`, `prompt`, `creativity` | dynamic by output size, see below |
| `sirv_image_to_image` | `image_url`, `prompt`, `strength` (0-1), `model` | reve-fast-edit 1, flux2-lora 3, qwen-integrate-product 4 |

**Upscale Models and costs** (cost scales with output megapixels = width×scale × height×scale):
- `esrgan` (default) - Fast, general purpose: 1 credit (2 above 48MP output)
- `clarity` - AI-enhanced with prompt guidance (`prompt`/`creativity` apply to this model only): ~3 credits per output MP, min 2
- `topaz` - Premium quality: 8 (≤24MP) / 16 (≤48MP) / 32 (≤96MP) / 136 (>96MP)

The MCP tool caps `scale` at 4; the REST API accepts up to 10 (the service clamps to each model's max).

**Image-to-Image Models:** `reve-fast-edit` (default), `flux2-lora`, `qwen-integrate-product`

## Image Generation

| Tool | Parameters | Cost per image |
|------|------------|------|
| `sirv_generate` | `prompt`, `model`, `aspect_ratio`, `num_images` (1-4) | flux2 1, zimage 2, seedream 2, gemini 15-30 |
| `sirv_image_translation` | `image_url`, `model` (gemini/gpt-image-2-edit/seedream-edit) | model-dependent |

**Generation Models:** `zimage` (fast, default), `flux2` (detailed), `gemini` (photorealistic, 15 at 1K / 30 at 4K), `seedream` (artistic)

**Aspect Ratios:** `1:1`, `16:9`, `9:16`, `4:3`, `3:4`, `21:9`

Total cost multiplies by `num_images`.

## Product & E-commerce

| Tool | Parameters | Cost |
|------|------------|------|
| `sirv_product_lifestyle` | `image_url`, `scene_description`, `ref_image_url`, `placement_type`, `position`, `num_results` | 4 (bria default) |
| `sirv_virtual_try_on` | `person_image_url`, `garment_image_url` | 4 |
| `sirv_alt_text` | `image_url`, `detail_level` | 1 |

**Placement Types:** `original`, `automatic` (default), `manual_placement`, `manual_padding`

**Positions:** `bottom_center`, `bottom_left`, `bottom_right`, `upper_center`, `upper_left`, `upper_right`, `center_vertical`, `center_horizontal`, `left_center`, `right_center`

**Alt Text Detail Levels:** `caption` (brief), `detailed-caption` (standard), `more-detailed-caption` (comprehensive)

## 3D & Video

| Tool | Parameters | Cost |
|------|------------|------|
| `sirv_image_to_3d` | `image_url`, `model`, `topology`, `target_polycount`, `enable_pbr` | by model, see below |
| `sirv_optimize_glb` | `model_url`, optimization options | 2 |
| `sirv_video_generation` | `prompt`, `image_url`, `model`, `duration`, `resolution`, `aspect_ratio`, `generate_audio` | per second, see below |
| `sirv_depth_map` | `image_url` | FREE |

**3D Models and costs:** `meshy` (default) 50, `meshy-multi` 25, `seed3d` 50, `trellis` 2, `trellis2` 30, `hunyuan3d` 25

**Video Models and per-second costs:** `veo31` (default) 10/s (15/s with audio), `ltx` 6/s at 1080p (12/s at 1440p, 24/s at 2160p), `kling` 7/s (14/s with audio). Total = per-second rate × duration.

**Video Resolutions:** `720p`, `1080p`, `1440p`, `2160p`

## Batch Operations

| Tool | Parameters | Cost |
|------|------------|------|
| `sirv_batch_remove_background` | `images` (array of {id, image_url}), `model` | 1-2/image |
| `sirv_batch_upscale` | `images` (array of {id, image_url}), `scale` (2-4), `model` | per upscale pricing/image |

Only these two batch tools exist on the MCP server. They are **synchronous**: the call blocks until all images finish (up to a 5-minute client timeout) and returns the full results array with per-image `status: success|error` — there is no job ID or polling.

**Limits:** 1-100 images per request, and account tier caps apply server-side — the Free tier cannot use API batch at all (check tier with `sirv_get_usage`; tier caps are in [platform.md](platform.md)). For very large sets, or for batch alt text (which has no MCP tool), use the REST API's async batch endpoints with job polling ([rest-api.md](rest-api.md)).

## Account

| Tool | Parameters | Returns |
|------|------------|---------|
| `sirv_get_usage` | None | `used`, `remaining`, `total`, `tier` |
| `sirv_list_organizations` | None | organizations for the account |

## Asset, Product, Workflow & Shopify Tools

The server also exposes management tools beyond image processing:

- **Assets (DAM) and Products (PIM):** 20 tools for listing/searching/updating assets (including visual similarity search and persisted alt text) and managing the product catalog with asset linking. Full parameters, semantics, and destructive-operation warnings: [asset-product-tools.md](asset-product-tools.md).
- **Workflows:** `sirv_list_workflows`, `sirv_get_workflow`, `sirv_execute_workflow` — run saved Workflow Builder pipelines
- **Shopify:** `sirv_push_image_to_shopify`, `sirv_sync_shopify_products`, `sirv_shopify_status`
- **Supplier portal:** `sirv_get_supplier_sftp_status`, `sirv_get_supplier_review_assist_requirements`, `sirv_run_supplier_autofix`

Shopify, workflow-execution, and supplier tools are covered agent-side in `../../sirv-ecommerce/SKILL.md`.

## Usage Examples

**Remove background from a product image:**
```
"Remove the background from https://example.com/product.jpg using the Heavy model"
→ sirv_remove_background(image_url, model="General Use (Heavy)")
```

**Create lifestyle scene:**
```
"Place this product on a modern kitchen counter with morning light"
→ sirv_product_lifestyle(image_url, scene_description="Modern kitchen counter with morning light")
```

**Generate product variations:**
```
"Generate 4 images of a minimalist water bottle on white background"
→ sirv_generate(prompt="minimalist water bottle on white background", num_images=4)
```

**Upscale for print:**
```
"Upscale this image 4x using the Topaz model for print quality"
→ sirv_upscale(image_url, scale=4, model="topaz")
```

**Virtual try-on:**
```
"Show this dress on the model photo"
→ sirv_virtual_try_on(person_image_url, garment_image_url)
```

**Batch processing:**
```
"Remove backgrounds from all these product images"
→ sirv_batch_remove_background(images=[{id: "1", image_url: "..."}, ...])
```

**Check credits:**
```
"How many credits do I have left?"
→ sirv_get_usage()
```

**Run a saved pipeline:**
```
"Run my Amazon-ready workflow on these images"
→ sirv_list_workflows() → sirv_execute_workflow(workflow_id, inputs)
```
