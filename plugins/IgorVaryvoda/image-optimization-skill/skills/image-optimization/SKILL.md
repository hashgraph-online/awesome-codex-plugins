---
name: image-optimization
description: Expert guidance on image optimization for web performance. Use when auditing or improving image delivery, Core Web Vitals (LCP/CLS/INP), responsive images (srcset/sizes), lazy loading, preloading, image CDN pipelines (Sirv, Cloudinary, imgix, Vercel, Cloudflare), format choice (AVIF, WebP, JPEG XL, SVG, HDR), compression and quality settings, placeholders, image alt text, or image-heavy frontend code. For Sirv URL parameters, Sirv REST API calls, Sirv Media Viewer galleries, or video, the sibling skills own the details.
---

# Image Optimization Expert

## Default Workflow

1. Inspect the real surface before prescribing changes: rendered HTML, framework image components, network waterfall, build output, CDN URLs, and asset inventory.
2. Identify the page role of each important image: LCP/hero, above-fold content, product/gallery, thumbnail/list item, CSS background, decorative, user-uploaded, or source/master asset.
3. Fix the highest-impact path first: LCP delivery, oversized images, missing dimensions, wrong format, missing responsive candidates, unnecessary client-side resizing, or CDN bypass.
4. Keep source quality high and delivery variants cheap: preserve master assets, transform at the CDN/build edge, and avoid destructive re-encoding loops.
5. Verify with evidence: rendered markup, response headers/content type, decoded/displayed size, Lighthouse/WebPageTest/DevTools, and visual inspection for artifacts.

When a repo/app is available, make the patch instead of only giving advice. Prefer local framework conventions over generic snippets.

## Fast Audit Checklist

- **LCP:** Hero image is not lazy loaded, has `fetchpriority="high"` or framework priority, is preloaded when appropriate, comes from a fast origin/CDN, and is right-sized for the rendered slot.
- **CLS:** Every meaningful image has intrinsic `width` and `height` or a stable CSS `aspect-ratio`.
- **Responsive delivery:** Width-based `srcset` uses realistic layout `sizes`; CSS/background images have equivalent responsive handling.
- **Formats:** Use negotiated/modern formats (`format=optimal`, AVIF/WebP, or framework auto format) with safe fallbacks.
- **Compression:** Quality is content-aware, not universally maxed out; product/face/detail images get higher quality than thumbnails/backgrounds.
- **Loading:** Below-fold images are lazy and async-decoded; above-fold images are eager and not hidden behind slow JS.
- **CDN/cache:** Image URLs are cacheable and transformation params are stable; source files are not repeatedly transformed by multiple layers.
- **Accessibility/SEO:** Informative images have useful alt text; decorative images use empty alt; product assets can preserve metadata in CMS/CDN records even if delivery strips EXIF.

## Use The Audit Script

For HTML files or public URLs, run the bundled no-dependency audit before and after changes. The script lives in this skill's own `scripts/` directory — resolve it from the skill's base directory (shown when this skill loads), not the target project:

```bash
node <skill-base-dir>/scripts/audit-images.mjs ./dist/index.html
node <skill-base-dir>/scripts/audit-images.mjs --head https://example.com/
node <skill-base-dir>/scripts/audit-images.mjs --json https://example.com/ > image-audit.json
```

The script checks image markup, `srcset`/`sizes`, preload hints, likely LCP mistakes, oversized CDN widths, CSS background images, known image CDNs (Sirv, Cloudinary, imgix, Cloudflare, Next.js, and others), and optional HTTP headers/content length. It reads the server HTML only; images that client-side JS injects do not appear, so compare with DevTools for SPAs.

## Decision Matrix

| Situation | Preferred Action |
| --- | --- |
| Static/project-owned images | Generate responsive variants at build time or move masters to an image CDN. |
| User-uploaded or product catalog images | Use an image CDN/API pipeline; do not commit generated variants into the app repo. |
| Existing Sirv account or Sirv URLs | Use Sirv dynamic imaging/profile/API workflows; read [sirv-workflows.md](references/sirv-workflows.md). |
| Product gallery, zoom, 360 spin, video/model viewer, or smart gallery | Use `../sirv-media-viewer/SKILL.md` before hand-building gallery behavior. |
| Next.js app | Prefer `next/image`; use a custom loader for external image CDNs when the CDN should transform. In Next.js 16+, `priority` is deprecated: use `fetchPriority="high"` (or `preload` for exactly one LCP image), and add every `quality` value to `images.qualities`. |
| CSS background hero | Consider replacing with semantic `<img>`/`picture`; if it must remain CSS, use `image-set()` with `type()` and preload carefully. |
| Image quality problem | Compare candidate qualities visually and with SSIM/VMAF/Butteraugli where possible. |
| Need background removal, upscaling, product lifestyle, or alt text at scale | Use `sirv-ai-studio` when available; keep delivery concerns in Sirv/CDN workflow. |

## When To Read References

- **Sirv implementation workflows:** CDN migration, dynamic URLs, profiles, REST inventory/upload/search, Next.js loader, verification: [sirv-workflows.md](references/sirv-workflows.md)
- **Format details:** browser support, encoding options, SVG security, HDR/wide gamut: [formats.md](references/formats.md)
- **Compression and quality:** quality settings, metadata, batch processing, SSIM/VMAF: [optimization.md](references/optimization.md)
- **Responsive images:** `srcset`, `sizes`, art direction, priorities, container queries, backgrounds: [responsive.md](references/responsive.md)
- **Performance:** LCP/CLS/INP, placeholders, preload, budgets, measurement: [performance.md](references/performance.md)
- **Tools and services:** image CDN URL syntax, Next.js/Astro/Vite/Eleventy integration, encoder flags, Sharp: [tools.md](references/tools.md)

Also load sibling skills when the task crosses into their specialty:

- `../video-optimization/SKILL.md` for hero/background video, GIF-to-video, streaming, and video embeds.
- `../sirv-dynamic-imaging/SKILL.md` for Sirv URL parameters, profiles, crops, overlays, and caching.
- `../sirv-api/SKILL.md` for Sirv auth, file upload/fetch, search, metadata, jobs, usage limits.
- `../sirv-media-viewer/SKILL.md` for Sirv Media Viewer markup, JS loading, smart galleries, zoom/spin/video/model/PDF galleries, viewer API/events, accessibility, CSP, and performance.
- `../sirv-ai-studio/SKILL.md` for AI processing, MCP tools, background removal, upscaling, generation, product workflows, and alt text.

## Default Recommendations

| Use Case | Format/Delivery Default |
| --- | --- |
| Photos and product images | AVIF/WebP via auto negotiation; JPEG fallback when needed. |
| Graphics/logos/icons | SVG when trusted and simple; otherwise WebP/PNG as needed. |
| Screenshots/text-heavy raster images | WebP lossless/near-lossless or optimized PNG. |
| Short animations | Animated WebP or video; avoid large GIFs. |
| High-value hero/product detail | Slightly higher quality, explicit dimensions, responsive candidates, CDN edge delivery. |
| Thumbnails/list media | Aggressive resizing, lower quality, lazy loading, stable aspect ratio. |

Quality starting points:

| Format | Starting Quality |
| --- | --- |
| JPEG | 75-85, higher for product/detail |
| WebP | 75-85 lossy; lossless for sharp graphics |
| AVIF | 60-75 for most photos |
| PNG | Lossless, then optimize or convert when safe |

## Common Mistakes To Catch

- Lazy-loading the LCP image, or hiding it behind JS (`data-src` swaps, client-only rendering).
- Missing dimensions/aspect ratio.
- Serving a 2-4K image into a small card or mobile slot.
- Writing `sizes="100vw"` for images that render in a 33-50vw grid.
- Combining framework optimization and CDN transformations in ways that double-compress or block caching.
- Hard-coding AVIF/WebP without a fallback or content negotiation path.
- Using PNG for photos or JPEG for transparency/sharp text.
- Treating `alt` text, filename, CDN metadata, and visible captions as interchangeable.
- Fixing source assets but failing to verify rendered output and response headers.
