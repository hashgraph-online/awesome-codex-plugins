# Image & Media Skills

Skills for AI coding agents covering image optimization and media APIs.

## Install

Any agent (Claude Code, Codex, Cursor, OpenCode, and others):

```bash
npx skills add https://github.com/igorvaryvoda/image-optimization-skill
```

Claude Code plugin (all 8 skills, with updates):

```bash
claude plugin marketplace add igorvaryvoda/image-optimization-skill
claude plugin install sirv-media-skills@imageguide
```

Or inside a session: `/plugin install sirv-media-skills --marketplace igorvaryvoda/image-optimization-skill`

Each skill includes `agents/openai.yaml` metadata for skill pickers. Core workflows also include `evals/evals.json` prompts that can be used to regression-test agent behavior.

## Skills

### image-optimization

Execution-focused image optimization for web performance.

- **Image Formats** - JPEG, PNG, WebP, AVIF, GIF, SVG, HEIC, JPEG XL, HDR, wide color gamut
- **Optimization** - Quality settings, SSIM/VMAF thresholds, compression techniques
- **Responsive Images** - srcset, sizes, picture element, fetchpriority, container queries
- **Performance** - Core Web Vitals, placeholder strategies (LQIP, blur-up, blurhash), lazy loading
- **Sirv Workflows** - Dynamic Imaging URLs, profiles, REST inventory/upload/search, Next.js loader, Sirv JS tradeoffs
- **Audit Script** - No-dependency page/HTML image audit for markup, LCP hints, oversized CDN widths, CSS backgrounds, known image CDNs, and optional HTTP headers (tested in CI against `evals/files/broken-landing.html`)
- **Tools** - Image CDN URL syntax, Next.js 16/Astro/Vite/Eleventy integration, encoder flags, Sharp, Sirv AI Studio alt text/background removal/upscaling

### sirv-api

Sirv REST API integration for image and file management.

- **Authentication** - JWT token auth
- **File Operations** - Upload, download, copy, delete, rename, directory listing
- **Metadata** - Title, description, tags, product info, approval status
- **Search** - Query files by name, date, size, metadata with Lucene-style syntax
- **Async Jobs** - Video/spin conversion, ZIP creation, batch operations
- **Account** - Usage stats, billing, events, folder options

### sirv-ai-studio

Guide for using Sirv AI Studio (www.sirv.studio), an AI-powered image and video processing platform.

- **Background Processing** - Removal, replacement, object removal
- **Image Enhancement** - Upscaling (up to 8x), AI editing
- **Image Generation** - FLUX 2, Gemini Pro, Z-Image, Seedream
- **Product Tools** - Lifestyle scenes, virtual try-on, color variants, alt text
- **3D Generation** - Image to 3D (GLB, OBJ, FBX, USDZ)
- **Video Tools** - LTX, Kling, Veo, captions
- **Batch Processing** - Process hundreds of images at once
- **Workflow Builder** - Visual DAG pipeline for multi-step operations
- **MCP Server** - Natural language image processing via Claude/ChatGPT
- **REST API** - Endpoints for scripts and app integrations

### sirv-media-viewer

Sirv Media Viewer implementation for product galleries and rich media.

- **Viewer Markup** - `class="Sirv"`, child `data-src` items, single-div galleries, smart `.view` galleries
- **Media Types** - Zoomable images, 360 spins, videos, YouTube/Vimeo, 3D models, PDF galleries
- **Options** - Thumbnails, slider/grid layouts, fullscreen, mobile breakpoints, quality, autostart, item ordering
- **Performance** - Sirv JS loading, module-limited scripts, preconnect/DNS-prefetch, LCP/CLS-aware viewer setup
- **Accessibility** - `data-alt`, Sirv file descriptions, ARIA labels, keyboard/fullscreen checks
- **Advanced Hooks** - Sirv viewer API, events, analytics hooks, CSP requirements

### video-optimization

Execution-focused video optimization for web performance.

- **Delivery** - Progressive MP4/WebM vs adaptive HLS, codec choice (H.264, VP9, AV1)
- **Performance** - Posters and LCP, preload strategies, lazy loading, CLS-safe players
- **Patterns** - Background/hero video, GIF-to-video, YouTube/Vimeo facades, reduced motion
- **Sirv Video** - Automatic HLS ladder, SMV video options, thumbnails, video-to-spin
- **Encoding** - ffmpeg recipes for loops, GIF replacement, content video, poster extraction

### sirv-360-spin

Create and embed Sirv 360 spins - interactive rotating product views.

- **Creation** - Frame counts, shooting resolution, file naming for auto-generated .spin files
- **3D Spins** - Multi-row naming (row/column sequences)
- **Embedding** - Sirv JS markup, preconnect, gallery integration
- **Options** - Autospin, zoom, hint, speed, start frame, mobile drag behavior
- **Conversion** - Video-to-spin and spin-to-video via API

### sirv-ecommerce

Store-facing product imagery workflows with Sirv AI Studio.

- **Shopify** - Connection checks, product sync (inbound), image push with safe upload strategies
- **Pipelines** - Discover and execute saved Workflow Builder pipelines on image batches
- **Compliance** - Marketplace presets (Amazon, eBay, Walmart), review and autofix loops
- **Supplier Portal** - SFTP intake status, review-assist requirements, AI autofix

### sirv-dynamic-imaging

Sirv dynamic imaging URL API for on-the-fly image transformation.

- **Sizing** - Width, height, scale options, thumbnails
- **Cropping** - Manual crop, face detection, trim, point of interest
- **Effects** - Blur, sharpen, brightness, contrast, color tones, grayscale
- **Text Overlays** - Custom fonts, positioning, colors, backgrounds, outlines
- **Watermarks** - Logo placement, opacity, tiling, scaling
- **Formats** - WebP, AVIF, optimal auto-selection, quality settings
- **Profiles** - Reusable option presets as JSON

## Learn More

[imageguide.dev/tools/claude-skill](https://imageguide.dev/tools/claude-skill/)

## License

MIT
