# Sirv Image Optimization Workflows

Use this reference when an image optimization task can be solved with Sirv CDN, Sirv Dynamic Imaging, Sirv REST API, or Sirv AI Studio.

## Table of Contents

1. [Choose the Sirv path](#choose-the-sirv-path)
2. [Dynamic imaging URL strategy](#dynamic-imaging-url-strategy)
3. [LCP hero pattern](#lcp-hero-pattern)
4. [Next.js custom loader](#nextjs-custom-loader)
5. [Sirv JS and Media Viewer decision guide](#sirv-js-and-media-viewer-decision-guide)
6. [REST API migration workflow](#rest-api-migration-workflow)
7. [Product media workflow](#product-media-workflow)
8. [Verification](#verification)
9. [Pitfalls](#pitfalls)

## Choose The Sirv Path

| Need | Use |
| --- | --- |
| Resize, crop, format, quality, watermark, canvas, text overlay | Sirv Dynamic Imaging URLs or profiles. |
| Inventory, upload, fetch remote files, metadata, search, account limits | Sirv REST API. |
| Background removal, upscaling, product lifestyle, generation, alt text | Sirv AI Studio/MCP/API. |
| Automatic responsive/lazy loading without framework image components | Sirv JS. |
| Product gallery, zoom, spin, video, 3D model, PDF gallery, smart gallery | Sirv Media Viewer; load `../sirv-media-viewer/SKILL.md`. |

For performance work in a codebase, start with native HTML/framework markup plus Sirv transformed URLs. Add Sirv JS only when its automatic resizing/viewer behavior is actually needed.

## Dynamic Imaging URL Strategy

For parameter names, profiles, crops, and processing order, use `../../sirv-dynamic-imaging/SKILL.md`. For optimization work, these defaults apply:

- Size with `w`/`h`/`s` and add `scale.option=noup` so candidates never upscale.
- Use `format=optimal` (or the account default) for negotiated AVIF/WebP. Do not hard-code `format=avif`.
- Use `q=75-85` for normal delivery, higher for product detail, lower for thumbnails.
- Use a `profile=` for any recipe that repeats across many images.
- Upload high-quality masters (usually 2500-4000px, JPEG 92%+). Let Sirv generate the delivery variants.
- Images larger than 16MB may be pre-processed; do not delete `/.processed` derivatives that you see through FTP/S3/API.

## LCP Hero Pattern

```html
<link rel="preconnect" href="https://account.sirv.com" crossorigin>

<img
  src="https://account.sirv.com/heroes/home.jpg?w=1600&q=82&scale.option=noup"
  srcset="
    https://account.sirv.com/heroes/home.jpg?w=800&q=80&scale.option=noup 800w,
    https://account.sirv.com/heroes/home.jpg?w=1200&q=82&scale.option=noup 1200w,
    https://account.sirv.com/heroes/home.jpg?w=1600&q=82&scale.option=noup 1600w
  "
  sizes="100vw"
  width="1600"
  height="900"
  alt="Kitchen island with the featured espresso machine"
  fetchpriority="high"
>
```

Do not add `loading="lazy"` to the LCP image. Add a `<link rel="preload" imagesrcset imagesizes>` only when the image is not in the initial HTML (for example, a CSS background).

For grids, the `sizes` value must match the column width, for example `(min-width: 1200px) 25vw, (min-width: 768px) 33vw, 50vw`. `sizes="100vw"` in a grid downloads images that are 3-4 times too large.

## Next.js Custom Loader

Use this when Sirv should perform resizing/format negotiation instead of the default optimizer.

```js
// sirv-loader.js
const sirvBase = process.env.NEXT_PUBLIC_SIRV_CDN_URL;

export default function sirvLoader({ src, width, quality }) {
  const url = new URL(src.startsWith("http") ? src : `${sirvBase}${src}`);
  url.searchParams.set("w", String(width));
  url.searchParams.set("q", String(quality ?? 80));
  url.searchParams.set("format", "optimal");
  url.searchParams.set("scale.option", "noup");
  return url.toString();
}
```

```js
// next.config.js
module.exports = {
  images: {
    loader: "custom",
    loaderFile: "./sirv-loader.js",
    remotePatterns: [
      {
        protocol: "https",
        hostname: "account.sirv.com"
      }
    ]
  }
};
```

```jsx
import Image from "next/image";

<Image
  src="/products/shoe.jpg"
  width={1200}
  height={800}
  sizes="(min-width: 1024px) 50vw, 100vw"
  fetchPriority="high"
  alt="Blue suede running shoe side view"
/>;
```

For an LCP image, use `fetchPriority="high"` or `loading="eager"`. Next.js 16 deprecates the `priority` prop; use `preload` only when exactly one image is the LCP element. For below-fold images, keep the default lazy loading and realistic `sizes`.

The custom loader bypasses the Next.js optimizer, so the `images.qualities` allowlist does not limit the `q` value that Sirv receives.

## Sirv JS And Media Viewer Decision Guide

Sirv JS can automatically resize and lazy load images with:

```html
<script src="https://scripts.sirv.com/sirvjs/v3/sirv.js"></script>
<img class="Sirv" data-src="https://account.sirv.com/products/shoe.jpg" width="1200" height="800" alt="Blue suede running shoe">
```

Use Sirv JS when:

- The site is not using a capable framework image component.
- You want Sirv's automatic lazy/responsive behavior across many simple pages.
- You need Sirv Media Viewer, zoom, spin, fullscreen, or gallery features.

Avoid Sirv JS for the critical hero path if it delays LCP behind script execution. In component apps, native `srcset`/framework image components with Sirv URLs are often easier to verify and optimize.

For product galleries, use Sirv Media Viewer instead of recreating slider/zoom/spin behavior; markup and options are in `../../sirv-media-viewer/SKILL.md`. Use `autostart:created` only for above-fold viewers, and reserve layout space to avoid CLS.

Useful Sirv JS options:

- `autostart:created` for eager/above-fold images.
- `autostart:visible` for lazy images.
- `threshold:200` to start lazy loading before the viewport.
- `quality` and `hdQuality` for standard and retina delivery.
- `fit:contain|cover|crop` for container handling.
- `resize:false` if viewport resize should not trigger a new variant.

## REST API Migration Workflow

Use `../sirv-api/SKILL.md` for endpoint details.

1. Confirm credentials and token handling. Tokens from `/v2/token` expire quickly, so refresh them in scripts rather than hard-coding.
2. Inventory current assets:
   - Local repo assets with `rg --files` plus file sizes.
   - Current Sirv assets with `/v2/files/search`.
   - Production usage with rendered HTML/network logs.
3. Check account limits before bulk work via `/v2/account/limits`.
4. Upload local masters with `/v2/files/upload` or import remote originals with `/v2/files/fetch`.
5. Preserve catalog context with metadata:
   - `meta.title`, `meta.description`, `meta.tags`
   - `meta.product.id`, `name`, `brand`, categories
   - approval status when the workflow needs review gates
6. Rewrite app URLs to Sirv CDN paths and transform params/profiles.
7. Verify rendered pages and Sirv responses.

Path encoding, search pagination and scrolling, token expiry, and rate limits are in `../../sirv-api/SKILL.md`. Read it before you write the migration script.

## Product Media Workflow

For catalogs, combine Sirv capabilities deliberately:

1. Use Sirv AI Studio/MCP/API for asset improvement: background removal, upscaling, lifestyle scenes, alt text, product descriptions.
2. Auto-upload or move final outputs to Sirv CDN folders.
3. Attach product metadata and tags through the REST API.
4. Use Dynamic Imaging profiles for storefront delivery variants.
5. Validate against marketplace requirements when relevant.

Do not use AI-upscaled/generated output as the only master unless the business accepts that as the canonical source.

## Verification

Minimum checks after a Sirv optimization patch:

```bash
curl -I "https://account.sirv.com/products/shoe.jpg?w=800&q=80"
curl -I -H "Accept: image/avif,image/webp,image/*,*/*;q=0.8" "https://account.sirv.com/products/shoe.jpg?w=800"
```

Confirm:

- HTTP status is 200, not a custom 404 fallback.
- `content-type` matches expected negotiated output.
- `content-length` is reasonable for the rendered size.
- Cache headers are present and stable.
- The rendered image dimensions are close to the displayed dimensions multiplied by DPR.
- LCP image is not lazy and is requested early.
- Below-fold images are not all requested at initial load.
- Sirv Media Viewer markup has the Sirv JS script, viewer assets load with 200s, and thumbnails/fullscreen/zoom/spin/video/model interactions work at desktop and mobile breakpoints.
- Visual quality is acceptable at desktop and mobile breakpoints.

For live pages, also run:

- Lighthouse or PageSpeed for LCP/CLS and image opportunities.
- DevTools Network filtered by `Img`.
- The bundled `audit-images.mjs` script for markup regressions.

## Pitfalls

- Adding Sirv JS to fix all images but slowing down the LCP image.
- Using `scale.option=ignore` and distorting products.
- Cropping product images without explicit business approval.
- Using `sizes="100vw"` in grids, causing oversized downloads.
- Hard-coding `format=avif` without fallback or negotiation.
- Uploading already-compressed tiny sources as masters.
- Deleting `/.processed` large-image derivatives visible through API/FTP.
- Treating CDN metadata as a replacement for HTML `alt`.
- Letting Next.js optimize already-optimized Sirv variants unless that layering is intentional.
- Adding SMV `data-src` markup without loading Sirv JS, reserving viewer space, or providing `data-alt`/Sirv file descriptions.
