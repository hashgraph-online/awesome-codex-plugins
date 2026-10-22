---
name: sirv-dynamic-imaging
description: Sirv dynamic imaging URL API for on-the-fly image transformation. Use when building image URLs with Sirv CDN, resizing images via URL parameters, adding watermarks/text overlays, cropping, applying filters, format conversion (WebP, AVIF), or any Sirv URL-based image manipulation. Covers 100+ URL parameters for scaling, cropping, effects, text, watermarks, frames, and optimization.
---

# Sirv Dynamic Imaging API

Transform images on-the-fly by adding URL parameters.

Base URL: `https://yourcdn.sirv.com/path/image.jpg?{options}`

Prefer high-quality masters and delivery-time transformations. Sirv applies URL parameters before profile settings, and profile settings before the Default profile. Processing order is auto-crop, scale, crop, canvas, rotate, then other effects; URL parameter order does not change that order.

## Official Sources First

Check current Sirv docs before changing parameter names, defaults, or fallback behavior:

- `https://sirv.com/help/articles/dynamic-imaging/`
- `https://sirv.com/help/articles/dynamic-imaging/format/`
- `https://sirv.com/help/articles/dynamic-imaging/crop/`
- `https://sirv.com/help/articles/responsive-images-smv/`

## Quick Reference

### Sizing

| Option | Example | Description |
|--------|---------|-------------|
| `w` | `?w=800` | Width (px or %) |
| `h` | `?h=600` | Height (px or %) |
| `s` | `?s=500` | Longest dimension |
| `thumbnail` | `?thumbnail=200` | Square thumbnail |
| `scale.option` | `?scale.option=fit` | fit, fill, ignore, noup |

```
?w=800                    # 800px wide
?w=50%                    # 50% of original width
?w=800&h=600              # Specific dimensions
?w=800&scale.option=fit   # Fit within 800px (maintain aspect)
?w=800&scale.option=fill  # Fill 800px (may crop)
```

### Cropping

| Option | Example | Description |
|--------|---------|-------------|
| `cw`, `ch` | `?cw=500&ch=300` | Crop width/height |
| `cx`, `cy` | `?cx=100&cy=50` | Crop start position |
| `crop.type` | `?crop.type=face` | Auto-crop: trim, poi, face |

```
?cw=500&ch=300&cx=100&cy=50   # Manual crop
?crop.type=face&w=400          # Face detection crop
?crop.type=trim                # Trim whitespace
```

### Format & Quality

| Option | Example | Description |
|--------|---------|-------------|
| `format` | `?format=optimal` | jpg, png, webp, avif, optimal, original |
| `q` | `?q=85` | JPEG/WebP quality 0-100; default is usually 80 |
| `subsampling` | `?subsampling=4:2:0` | JPEG chroma subsampling |

```
?format=optimal             # Auto-select best format
?format=webp&q=80           # WebP at 80% quality
?format=avif                # AVIF format
?format=original            # Preserve original format
```

Prefer `format=optimal` or the account default for web delivery unless a fixed format is required. If forcing WebP/AVIF, verify the fallback behavior in current Sirv docs and rendered responses.

### Effects

| Option | Range | Description |
|--------|-------|-------------|
| `blur` | 0-100 | Gaussian blur |
| `sharpen` | 0-100 | Sharpen |
| `brightness` | -100 to 100 | Brightness |
| `contrast` | -100 to 100 | Contrast |
| `saturation` | -100 to 100 | Saturation |
| `grayscale` | true/false | Black & white |
| `rotate` | -180 to 180 | Rotation degrees |
| `colortone` | preset name | sepia, warm, cold, sunset... |

```
?blur=10                    # Light blur
?grayscale=true&contrast=20 # B&W with more contrast
?colortone=sepia            # Sepia effect
?rotate=90                  # Rotate 90 degrees
```

### Text Overlay

```
?text=Hello%20World
?text=Hello&text.size=30%&text.color=white&text.position=southeast
?text=©%20Acme&text.font.family=Open%20Sans&text.opacity=50
```

### Watermark

```
?watermark=/logo.png
?watermark=/logo.png&watermark.position=southeast&watermark.opacity=50
?watermark=/logo.png&watermark.scale.width=20%
```

### Canvas & Frame

```
?canvas.width=1200&canvas.height=800&canvas.color=white
?frame.style=solid&frame.color=black&frame.width=10
```

## Common Patterns

### Responsive srcset
```html
<img
  src="https://cdn.sirv.com/image.jpg?w=800&q=80"
  srcset="
    https://cdn.sirv.com/image.jpg?w=400&q=78 400w,
    https://cdn.sirv.com/image.jpg?w=800&q=80 800w,
    https://cdn.sirv.com/image.jpg?w=1200&q=82 1200w
  "
  sizes="(max-width: 600px) 100vw, 50vw"
  width="1200"
  height="800"
  alt="Description"
>
```

### Modern format with fallback
```html
<picture>
  <source srcset="https://cdn.sirv.com/image.jpg?format=avif" type="image/avif">
  <source srcset="https://cdn.sirv.com/image.jpg?format=webp" type="image/webp">
  <img src="https://cdn.sirv.com/image.jpg" alt="Description">
</picture>
```

### Product thumbnail
```
?w=400&h=400&scale.option=fit&canvas.width=400&canvas.height=400&canvas.color=white
```

### LCP hero
```
?w=1600&q=82&scale.option=noup
```

Pair with preconnect/preload, `fetchpriority="high"`, explicit dimensions, and no lazy loading.

### Watermarked download
```
?watermark=/logo.png&watermark.position=southeast&watermark.opacity=30&dl
```

## When to Read Reference Files

- **Sizing & cropping** (scale options, crop modes, canvas): See [sizing.md](references/sizing.md)
- **Effects & filters** (color, blur, sharpen, colortone presets): See [effects.md](references/effects.md)
- **Text & watermarks** (fonts, positioning, styling): See [overlays.md](references/overlays.md)
- **Profiles & optimization** (reusable presets, caching, formats): See [profiles.md](references/profiles.md)

## Profiles

Save reusable option sets as JSON profiles in `/Profiles/`:

```
?profile=my-thumbnail
```

Profile example:
```json
{
  "image": {
    "scale": {"width": 400},
    "format": "optimal",
    "quality": 80
  }
}
```

Use profiles for repeated recipes such as product cards, marketplace exports, watermarked downloads, and social previews. Keep one-off layout sizing in URL params.

## Workflow

1. Decide whether the transform is one-off markup, a reusable profile, or code that should use a helper/builder.
2. Check the official docs for exact parameter names and value ranges.
3. Preserve existing query params unless the task explicitly replaces them.
4. Use `format=optimal` or account defaults for browser delivery unless a fixed format is required.
5. Add or update assertions for final URL shape when the transform is business-critical.

Use `../sirv-media-viewer/SKILL.md` instead when the change is about gallery behavior, zoom/spin/video/model/PDF viewing, thumbnails, fullscreen, mobile breakpoints, Sirv JS loading, viewer API/events, or SMV accessibility. Dynamic Imaging owns delivery transforms; Sirv Media Viewer owns the interactive presentation.

## Red Flags

- Hand-writing many repeated query strings instead of using a profile or helper.
- Dropping existing query params, custom domains, signed URLs, or source URL behavior by accident.
- Treating thumbnails, AI-source images, and final delivery URLs as the same transform contract.
- Using `scale.option=ignore` unless distortion is explicitly desired.
- Changing format, quality, crop, or upscaling defaults without visual or byte-size verification.

## Verification

- Confirm final URLs use documented parameter names and values.
- Check `content-type`, `content-length`, and cache headers with `curl -I`.
- Verify rendered dimensions are close to display size multiplied by DPR.
- Compare desktop/mobile crops visually when using `fill`, `poi`, `face`, or manual crop params.
- Confirm LCP images request early and below-fold images do not all load immediately.
