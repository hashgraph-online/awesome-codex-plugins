# Sirv AI Studio Platform Guide

Web app features, current tool catalog, batch processing, Workflow Builder, platform areas, pricing, and integrations. Use this when advising on the web UI, comparing tools/models, or planning multi-step and batch workflows.

Verified against the product source (July 2026). The catalog evolves quickly — when precision matters, confirm in the app or at sirv.studio.

## Table of Contents

1. [Web UI Basics](#web-ui-basics)
2. [Tool Catalog](#tool-catalog)
3. [Batch Processing](#batch-processing)
4. [Workflow Builder (Orchestrator)](#workflow-builder-orchestrator)
5. [Platform Areas](#platform-areas)
6. [Credit System](#credit-system)
7. [Sirv CDN Integration](#sirv-cdn-integration)
8. [Integrations](#integrations)
9. [File Formats](#file-formats)
10. [Tips](#tips)

## Web UI Basics

Users access Sirv AI Studio at www.sirv.studio. Create opens as an operations dashboard; tools live in a composer picker and the workspace sidebar, organized in six categories (below). Typical flow: upload via drag-drop or URL → pick tool → configure → process → download or auto-upload to Sirv/Assets.

## Tool Catalog

Current categories and tools (display names as shown in the app):

### Edit
| Tool | Notes / Credits |
|------|---------|
| Remove background | BiRefNet 1, Bria 2; batch variant available |
| Change background | FLUX Kontext 3, Bria 4, Nano Banana 15, Solid Background 1+; batch variant |
| Expand image (uncrop) | Bria Expand, 2; batch variant |
| Fix Lighting (Relight) | Nano Banana 2 Edit-backed, ~5 |
| Remove object / Generative Fill | Object removal 3 (Qwen); fill mode uses Bria GenFill 4 |
| Translate text in images | Gemini default; batch variant |
| Background sheets | Spreadsheet/URL-driven bulk background work |

### Product
| Tool | Notes / Credits |
|------|---------|
| Product lifestyle | Bria 4 default, Nano Banana Lite 2; batch variant |
| Combine photos (Bundle Composer) | GPT Image 2 Edit-backed |
| Marketplace optimizer | Compliance scorecard + one-click fixes (Amazon, eBay, Shopify, Walmart) |
| AI Fashion Model | Virtual try-on: default 4; Fashn 8, Gemini 10, GPT 13, FLUX 2 |
| Fashion video | Try-on video, 11/second (Kling) |

### Enhance
| Tool | Notes / Credits |
|------|---------|
| Upscale image | ESRGAN 1-2, Clarity ~3/output-MP, Topaz 8-136 by output size; batch + sheets variants |
| Upscale video | Topaz Video (per-second, min 5) or SeedVR (per output data); NEW |
| Image optimizer | Social presets, resize/crop/convert |
| GLB optimizer | 3D model optimization, 2; batch variant |

### Create
| Tool | Notes / Credits |
|------|---------|
| Generate image | Nano Banana 2 default 5-15 by res; FLUX 2 1, Z-Image 2, Seedream 2, Gemini Pro 15-30, GPT Image 2 13; batch variant |
| Transform image (image-to-image) | Nano Banana 2 Edit 5 default; Reve 1, Z-Image 1, FLUX 2 Edit 3, Seedream Edit 4 |
| Video generation | Veo 3.1 10-15/s, LTX 6-24/s, Kling 7-14/s, Kling 3.0/Pro 8.4-16.8/s, Seedance 2 Fast ~24/s |
| Image to 3D | Meshy 50, Multi-view 25, Seed3D 50, Trellis 2, Trellis 2 (v2) 30, Hunyuan3D 25 |
| SVG generation | QuiverAI generation 15; Recraft vectorize mode 1 |

### Analyze
| Tool | Notes / Credits |
|------|---------|
| Alt text | 1; batch variant |
| Product descriptions | 1 (12+ languages) |
| Document summary | Document analysis |
| PDF translation | 3; NEW |
| Video captions | Multi-language transcription |
| Depth map | FREE |

### Automation
Workflows (Orchestrator) — see below.

Note: Smart Crop, Add Shadow, Color Variants, Ghost Mannequin, and Image Review exist as **Workflow steps**, not standalone tools in the picker. If a user asks for them, route through a workflow.

## Batch Processing

Standard batch operations (upload set → shared settings → preview → process → ZIP or auto-upload): background removal, upscale, alt text, virtual try-on, depth map, product lifestyle, background replace, image expand, image translation, GLB optimize, and image generation. Spreadsheet/URL-driven "sheets" surfaces exist for background work and upscaling.

**Batch size limits by plan:**
- Free: 25 in-app; API batch endpoints require a paid plan
- Core: 500
- Growth: 2,000
- Enterprise / Volume+: custom/unlimited
- Legacy plans: Starter 100, Pro 500, Team 750, Business Classic 1,500, Business 3,000, Scale custom

## Workflow Builder (Orchestrator)

Visual DAG pipeline builder. Step types span three groups:

- **AI steps:** generate, upscale, remove/change background, image expand, relight, image-to-image, image translation, product lifestyle, depth map, alt text, product description, smart crop, add shadow, color variants, ghost mannequin, AI fashion model (+video), image to 3D, video generation, video upscale, bundle composer
- **Sirv/DAM steps:** save to Sirv, add meta tags, set product meta, save to Assets, add to collection, add tags, move to folder, link to product, write product attributes, set favorite
- **Control steps:** push to Shopify, review / image review (interactive - pause execution), auto fix, AI router (classify + branch), channel readiness gate, save to CSV

**Workflow Triggers** run pipelines automatically on events; workflow limits are plan-enforced.

**Example workflows:** Amazon-Ready (Remove BG → Validate → Autofix → Alt text), Fashion (Ghost mannequin → Remove BG → Shadow → Bundle), Color Variants (Remove BG → Generate colors → Review).

Saved workflows can also be executed from the MCP server (`sirv_execute_workflow` — interactive and CSV steps are skipped there).

## Platform Areas

Beyond one-shot tools, the app has grown into a product-content platform. Know these exist so you route users correctly:

- **Assets (DAM):** the former Library - asset metadata and licensing, saved views, advanced filters, collections. MCP asset tools operate on this.
- **Products (PIM):** product records with custom attributes, bulk editing, AI Fill for attribute fields, import mapping, and a product readiness command center.
- **Channels:** publish/readiness management for marketplaces (Amazon, eBay, Google, ...) with channel readiness gates in workflows.
- **Supplier/Vendor Portal:** B2B media intake - supplier uploads (TIFF-preserving), review queues with reviewer roles, autofix, rejection reasons, submission quotas, SFTP intake. Covered agent-side in `../../sirv-ecommerce/SKILL.md`.
- **Dashboards:** workspace overview and analytics command centre.

## Credit System

### Current Plans

| Plan | Price | Monthly Credits | Batch |
|------|-------|---------|-------|
| Free | $0 | 25 | 25 in-app, no API batch |
| Core | $149/mo | 1,500 | 500 |
| Growth | $499/mo | 5,000 | 2,000 |
| Enterprise | from $3,500/mo | custom | custom |

Grandfathered plans still in service: Starter (150), Pro (600), Team (1,000), Business Classic (1,800), Business (5,000), Scale (10,000), and Volume+ tiers from 5K to 250K credits/month.

Unused paid credits roll over up to 2× the monthly allowance.

### Credit Packs (One-time top-ups)

- 500 credits: $49
- 1,000 credits: $89
- 2,500 credits: $199

## Sirv CDN Integration

Connect Sirv account for:
- Browse Sirv library in app
- Auto-upload processed images
- Per-tool upload destinations (e.g., `/products/cutouts/`)
- Instant global CDN delivery
- Shopify integration sync

## Integrations

| Platform | Use Case |
|----------|----------|
| Shopify | Embedded admin app; browse products, push results, sync catalog |
| Zapier | Trigger processing from workflows |
| n8n | Self-hosted automation |
| Claude/ChatGPT MCP | Natural language image processing |
| REST API | Custom integrations |

## File Formats

**Input:** JPG, PNG, WebP, GIF, AVIF, HEIF, BMP, TIFF (suppliers can preserve TIFF masters)

**Output:** PNG, JPEG, WebP, GIF (images), MP4/WebM (video), GLB/OBJ/FBX/USDZ/STL (3D), SVG (vectorize)

## Tips

- **Eager upload**: Files upload immediately on selection for faster processing
- **Hash caching**: Identical files skip re-upload
- **Soft delete**: Recover deleted assets from trash
- **Mobile**: Long-press for context menu actions
- **Shortcuts**: Use keyboard shortcuts in dashboard for power workflows
