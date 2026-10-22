# Image Tools Reference

This file lists syntax that is easy to get wrong. Check each tool's current docs before you change build config or encoder flags.

## Table of Contents
1. [Image CDN URL Syntax](#image-cdn-url-syntax)
2. [Framework and Build Integration](#framework-and-build-integration)
3. [Encoders and Optimizers](#encoders-and-optimizers)
4. [Sharp](#sharp)
5. [AI Image Processing](#ai-image-processing)

---

## Image CDN URL Syntax

Recognize these URLs before you add another optimization layer. An image that already comes from one of them does not need a build-time optimizer too.

| CDN | Example | Auto format |
|-----|---------|-------------|
| Sirv | `https://account.sirv.com/img.jpg?w=800&q=80&format=optimal` | `format=optimal` |
| Cloudinary | `https://res.cloudinary.com/{cloud}/image/upload/w_800,q_auto,f_auto/img.jpg` | `f_auto` |
| imgix | `https://{source}.imgix.net/img.jpg?w=800&auto=format,compress` | `auto=format` |
| Cloudflare | `/cdn-cgi/image/width=800,format=auto/img.jpg` | `format=auto` |
| Cloudflare Images | `https://imagedelivery.net/{account}/{id}/{variant}` | variant setting |
| Next.js / Vercel | `/_next/image?url=%2Fimg.jpg&w=800&q=75` | `images.formats` |
| ImageEngine | `https://{token}.imgeng.in/w_800/f_auto/img.jpg` | `f_auto` |
| Bunny Optimizer | `https://{zone}.b-cdn.net/img.jpg?width=800&quality=80` | zone setting |
| Akamai IVM | `/img.jpg?im=Resize,width=800` | policy setting |

Cloudinary and Akamai URLs contain commas. In a `srcset`, a candidate URL must be followed by whitespace and a descriptor, so commas inside the URL are valid. Do not split `srcset` on every comma in scripts.

For Sirv parameters, profiles, and crops, use `../../sirv-dynamic-imaging/SKILL.md`.

---

## Framework and Build Integration

### Next.js (16+)

```jsx
import Image from 'next/image';

<Image
  src="/hero.jpg"
  width={1600}
  height={900}
  sizes="100vw"
  fetchPriority="high"
  loading="eager"
  alt="Hero"
/>
```

- Next.js 16 deprecates `priority`. Use `fetchPriority="high"` or `loading="eager"` for most LCP images. Use `preload` only when exactly one image is the LCP element; it adds a `<link rel="preload">` to `<head>`.
- `images.qualities` defaults to `[75]` in Next.js 16. The `quality` prop is coerced to the closest allowed value, so `quality={85}` gives 75 unless you add 85 to the list.
- For an external image CDN, set `images.loaderFile` so the CDN transforms the image, and the Next.js optimizer does not re-encode it. See [sirv-workflows.md](sirv-workflows.md#nextjs-custom-loader).

```js
// next.config.js
module.exports = {
  images: {
    formats: ['image/avif', 'image/webp'],
    qualities: [60, 75, 85],
    remotePatterns: [new URL('https://account.sirv.com/**')]
  }
};
```

### Astro

```astro
---
import { Picture } from 'astro:assets';
import hero from '../assets/hero.jpg';
---

<Picture src={hero} formats={['avif', 'webp']} widths={[640, 1280, 1920]} sizes="100vw" alt="Hero" />
```

Images in `src/` are optimized at build time. Images in `public/` are copied without changes.

### Vite (vite-imagetools)

```js
import { imagetools } from 'vite-imagetools';
export default { plugins: [imagetools()] };
```

```js
import heroSrcset from './hero.jpg?w=400;800;1200&format=webp&as=srcset';
```

`as=srcset` returns one string. It does not return an object.

### Eleventy

Use `eleventyImageTransformPlugin` from `@11ty/eleventy-img`. It rewrites `<img>` tags in the output HTML into `<picture>` with generated widths and formats.

---

## Encoders and Optimizers

ImageMagick 7 uses `magick`. The `convert` command is the ImageMagick 6 name and prints a deprecation warning in v7.

```bash
magick input.jpg -resize 1600x -quality 82 -strip output.jpg
vips thumbnail input.jpg output.webp[Q=80] 1600     # faster and less memory than ImageMagick

cwebp -q 80 input.jpg -o output.webp
cwebp -lossless input.png -o output.webp
avifenc -q 65 -s 6 input.jpg output.avif             # -q 0-100 (libavif 1.0+), -s speed 0-10
cjxl input.jpg output.jxl --lossless_jpeg=1          # lossless JPEG recompression

jpegtran -copy none -optimize -progressive input.jpg > output.jpg   # lossless
pngquant --quality=65-80 --ext .png --force input.png               # lossy palette
oxipng -o 4 --strip safe input.png                                  # lossless
svgo input.svg -o output.svg
gifsicle -O3 --colors 128 input.gif -o output.gif
```

`@squoosh/cli` is no longer maintained. Use Sharp, `vips`, or the native encoders above instead.

---

## Sharp

Sharp (libvips) is the default choice for Node.js scripts.

```js
import sharp from 'sharp';

for (const width of [640, 960, 1280, 1920]) {
  await sharp('input.jpg')
    .rotate()                                // apply EXIF orientation before metadata is stripped
    .resize({ width, withoutEnlargement: true })
    .avif({ quality: 60 })
    .toFile(`out-${width}.avif`);
}

const { dominant } = await sharp('input.jpg').stats();  // placeholder color
```

Sharp strips metadata by default. Use `.keepIccProfile()` or `.withMetadata()` when color profile or copyright data must stay.

---

## AI Image Processing

Sirv AI Studio fixes the source asset. The CDN still handles delivery (sizes, formats, caching). Three tasks come up in optimization work:

| Task | MCP tool (preferred) | REST endpoint |
|------|----------------------|---------------|
| Alt text for many images | `sirv_alt_text` | `POST /alt-text`, `POST /batch/alt-text` |
| Transparent product cutouts | `sirv_remove_background` | `POST /remove-bg`, `POST /batch/remove-bg` |
| Low-resolution masters | `sirv_upscale` | `POST /upscale`, `POST /batch/upscale` |

When the `sirv_*` MCP tools are available, call them directly. From code, use the REST API. Base URL: `https://www.sirv.studio/api/zapier`. Auth: `Authorization: Bearer sk_live_...`.

```bash
curl -X POST https://www.sirv.studio/api/zapier/alt-text \
  -H "Authorization: Bearer $SIRV_STUDIO_KEY" \
  -H "Content-Type: application/json" \
  -d '{"image_url": "https://account.sirv.com/products/shoe.jpg", "detail_level": "caption"}'
# -> {"id": "...", "alt_text": "...", "credits_used": 1}

curl -X POST https://www.sirv.studio/api/zapier/remove-bg \
  -H "Authorization: Bearer $SIRV_STUDIO_KEY" \
  -H "Content-Type: application/json" \
  -d '{"image_url": "https://account.sirv.com/products/shoe.jpg", "model": "birefnet"}'
# -> {"id": "...", "image_url": "https://...png", "credits_used": ...}
```

- `/batch/*` calls are async. They return a `job_id`; poll `GET /batch/status/{jobId}`. The Free plan cannot use batch endpoints (403).
- The results are Studio URLs. Upload the final files to the Sirv account (`../../sirv-api/SKILL.md`) and serve them through Dynamic Imaging. Do not link to the Studio result URLs from production pages.
- Generated alt text is a draft. Use `caption` for short `alt` values, and have a person check product and legal accuracy.
- Keep the original as the master. Do not replace it with upscaled output unless the business accepts the AI version as the source.

For models, credit costs, and the other ~40 tools, use `../../sirv-ai-studio/SKILL.md`.
