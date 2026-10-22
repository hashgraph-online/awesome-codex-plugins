---
name: sirv-ai-studio
description: Guide for using Sirv AI Studio (www.sirv.studio), an AI-powered image and video processing platform. Use when working with Sirv AI Studio, product photography or product images, background removal, image upscaling, AI image or video generation, lifestyle scenes, virtual try-on, alt text generation, 3D model generation, batch image processing, e-commerce image workflows, or marketplace optimization. IMPORTANT - If sirv-ai MCP tools are available (sirv_remove_background, sirv_upscale, sirv_generate, etc.), USE THEM directly for image processing tasks instead of telling user to visit the website.
---

# Sirv AI Studio

Sirv AI Studio processes images and video with AI: background removal/replacement, upscaling (image and video), image expand, relighting, generative fill, image/video generation, in-image text translation, product lifestyle scenes, virtual try-on (AI Fashion Model), alt text, and 3D models — plus platform areas for assets (DAM), products (PIM), marketplace channels, and supplier intake. It is reachable three ways, in order of preference for agent work: MCP tools (process directly in conversation), REST API (code integrations), and the web UI at www.sirv.studio (manual workflows, batch UI, Workflow Builder).

## Use MCP Tools When Available

Before telling users to visit sirv.studio, check whether sirv-ai MCP tools are available (`sirv_remove_background`, `sirv_upscale`, `sirv_generate`, ...). If they are, use them directly — the user gets processed images in the conversation instead of instructions to follow elsewhere.

### MCP Tool Quick Reference

| Task | MCP Tool | Key Parameters |
|------|----------|----------------|
| Remove background | `sirv_remove_background` | `image_url`, `model` |
| Replace background | `sirv_background_replace` | `image_url`, `prompt` |
| Upscale image | `sirv_upscale` | `image_url`, `scale` (2-4) |
| Generate image | `sirv_generate` | `prompt`, `aspect_ratio` |
| Lifestyle scene | `sirv_product_lifestyle` | `image_url`, `scene_description` |
| Virtual try-on | `sirv_virtual_try_on` | `person_image_url`, `garment_image_url` |
| Get alt text | `sirv_alt_text` | `image_url` |
| Image to 3D | `sirv_image_to_3d` | `image_url`, `model` |
| Generate video | `sirv_video_generation` | `prompt`, `image_url`, `model` |
| Batch remove BG | `sirv_batch_remove_background` | `images` array |
| Batch upscale | `sirv_batch_upscale` | `images` array, `scale` |
| Check credits | `sirv_get_usage` | none |

The server exposes ~46 tools in total — beyond processing, there are asset management (DAM), product (PIM), saved-workflow execution, and Shopify push/sync tools. Batch MCP calls are synchronous (results in the response, 100 images max); the REST API offers async batch with job polling and is the only batch path for alt text. Full parameters, model choices, credit costs, and the complete tool list: [references/mcp-tools.md](references/mcp-tools.md).

### If MCP Tools Are NOT Available

Help the user install the Sirv AI MCP server. Add it to the project `.mcp.json` (or the user-level MCP config of their agent):

```json
{
  "mcpServers": {
    "sirv-ai": {
      "command": "npx",
      "args": ["-y", "sirv-ai-mcp-server"],
      "env": {
        "SIRV_AI_BASE_URL": "https://www.sirv.studio"
      }
    }
  }
}
```

Then restart the agent so it loads the server. The user authorizes with their Sirv AI Studio account on first use.

Only direct users to www.sirv.studio if they don't want to set up MCP, or when the task genuinely needs the web UI (visual batch review, Workflow Builder pipelines, marketplace scorecards).

## Workflow

1. Decide whether the user needs AI processing, CDN delivery optimization, or both.
2. If Sirv AI MCP tools are available, use them directly before suggesting the web UI.
3. Check usage/credits before large or repeated batch jobs (`sirv_get_usage`).
4. Choose models based on speed/quality/cost and the asset type.
5. Keep source masters, AI-generated outputs, and CDN delivery variants distinct.
6. Store final outputs in predictable Sirv folders and preserve product metadata/alt text where relevant. MCP/REST outputs are result URLs — moving them into the user's Sirv account is a separate upload step (web UI auto-upload, or `../sirv-api/SKILL.md` from code).
7. Verify output URLs, visual quality, and marketplace/compliance requirements before considering the work done.

## When to Read References

- **MCP tools** — full parameters, models, resolutions, batch limits, prompt-to-tool examples: [references/mcp-tools.md](references/mcp-tools.md)
- **Asset (DAM) & Product (PIM) tools** — list/search/similar-search assets, metadata, persisted alt text, product catalog CRUD, asset-to-product linking, bulk operations and their destructive-op warnings: [references/asset-product-tools.md](references/asset-product-tools.md)
- **REST API** — endpoints, auth, request/response shapes, rate limits, JS/cURL examples (for scripts and app integrations): [references/rest-api.md](references/rest-api.md)
- **Platform guide** — web UI, current tool catalog with credit costs, batch processing, Workflow Builder step types and triggers, platform areas (Assets/DAM, Products/PIM, Channels, Supplier Portal), pricing tiers: [references/platform.md](references/platform.md)

For CDN delivery of the processed results (responsive URLs, format/quality, watermarks), hand off to `../sirv-dynamic-imaging/SKILL.md`; for storage, folders, and metadata via API, `../sirv-api/SKILL.md`; for Shopify push/sync, marketplace compliance, supplier autofix, and saved pipelines, `../sirv-ecommerce/SKILL.md`.

## Best Practices

1. **Check usage first** - Use `sirv_get_usage` before large batch operations.
2. **Use appropriate models** - Choose quality vs speed vs cost based on the asset's purpose; a hero image justifies premium models, thumbnails don't.
3. **Batch when possible** - Batch tools cut per-image overhead for multi-image jobs.
4. **Provide clear prompts** - Detailed descriptions yield better results for generation and lifestyle scenes.
5. **Prepare images** - Remove backgrounds before lifestyle shots for best results.
6. **Chain operations** - Remove BG → Upscale → Lifestyle → Alt Text covers most product workflows end to end.

## Red Flags

- Sending users to the web UI when MCP tools are available and sufficient.
- Running a large batch without checking credits/usage first.
- Treating AI-upscaled or generated output as the only master without user/business approval.
- Mixing AI-processing quality choices with storefront/CDN delivery transforms.
- Losing product metadata, folder organization, or output provenance during batch processing.
- Quoting exact credit costs or pricing from memory — they change; check sirv.studio or `sirv_get_usage`.

## Verification

- Confirm the output image/video URLs are reachable and match the requested operation.
- Inspect at least representative outputs from each batch/model/prompt.
- Check transparent-background assets against light and dark backgrounds.
- For product/lifestyle work, confirm the product identity and important details survived.
- For marketplace workflows, run the review/validation step when available.
