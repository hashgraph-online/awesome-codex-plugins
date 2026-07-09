---
name: image-seo-audit
description: "Audit image SEO. Use when: checking alt text, file sizes, WebP/AVIF formats, lazy loading, or responsive images."
argument-hint: "[URL]"
user-invocable: true
---

# /digital-marketing-pro:image-seo-audit

## Purpose

Perform a dedicated image optimization audit that evaluates all images on a page or site for SEO, performance, and accessibility. Produces a prioritized optimization list sorted by file size impact.

## Input Required

- **URL**: Page or site to audit
- **Scope**: Single page or site-wide crawl (default: single page)

## Process

1. **Load brand context**: Read active brand profile for industry context.
2. **Discover images**: Find all `<img>`, `<picture>`, CSS `background-image`, and `<source>` elements.
3. **Alt text audit**: Check presence, quality, keyword inclusion, length (10-125 chars). Flag: missing, filename-only ("image.jpg"), keyword-stuffed, non-descriptive ("click here").
4. **File size audit**: Apply tiered thresholds by image category — thumbnails (<50KB target, >200KB critical), content images (<100KB target, >500KB critical), hero/banner (<200KB target, >700KB critical).
5. **Format audit**: Check for modern formats. Recommend WebP (97%+ support) or AVIF (92%+ support) over JPEG/PNG. Check for `<picture>` element with format fallbacks. Note: JPEG XL restored in Chromium (Nov 2025) but not yet in Chrome stable — monitor, don't recommend yet.
6. **Responsive images**: Check for `srcset` and `sizes` attributes, appropriate resolution for device pixel ratios.
7. **Lazy loading**: Verify `loading="lazy"` on below-fold images. Flag `loading="lazy"` on above-fold/hero images (directly harms LCP).
8. **fetchpriority**: Check for `fetchpriority="high"` on LCP/hero images. Check for `decoding="async"` on non-LCP images.
9. **CLS prevention**: Check for `width` and `height` attributes or `aspect-ratio` CSS on all `<img>` elements. Flag images without dimensions.
10. **File naming**: Check for descriptive, hyphenated, lowercase file names vs generic names (IMG_1234.jpg).
11. **CDN usage**: Check if images are served from a CDN (different domain, CDN headers, edge caching).
12. **Score and prioritize**: Sort by file size savings impact (largest first).

## Recommended Picture Element Pattern

```html
<picture>
  <source srcset="image.avif" type="image/avif">
  <source srcset="image.webp" type="image/webp">
  <img src="image.jpg" alt="Descriptive alt text" width="800" height="600" loading="lazy" decoding="async">
</picture>
```

## Hero/LCP Image Pattern

```html
<img src="hero.webp" fetchpriority="high" alt="Hero image description" width="1200" height="630">
```

Do NOT lazy-load above-fold/LCP images. Do NOT add `decoding="async"` to LCP images.

## Output

### Image Audit Summary

| Metric | Status | Count |
|--------|--------|-------|
| Total Images | — | XX |
| Missing Alt Text | issues | XX |
| Oversized (>200KB) | issues | XX |
| Wrong Format (not WebP/AVIF) | issues | XX |
| No Dimensions (CLS risk) | issues | XX |
| Not Lazy Loaded (below-fold) | issues | XX |
| No fetchpriority on LCP | issues | XX |

### Prioritized Optimization List

Sorted by estimated file size savings (largest first):

| Image | Current Size | Format | Issues | Est. Savings |
|-------|-------------|--------|--------|-------------|
| hero.jpg | 450KB | JPEG | No WebP, no fetchpriority | ~300KB |
| ... | ... | ... | ... | ... |

### Recommendations (prioritized)
1. Convert X images to WebP format (est. XX KB total savings)
2. Add alt text to X images
3. Add width/height dimensions to X images
4. Enable lazy loading on X below-fold images
5. Add fetchpriority="high" to LCP image
6. Compress X oversized images
7. Implement `<picture>` element with AVIF/WebP fallbacks

## Agents Used

- **seo-specialist** — Image optimization analysis, CWV impact assessment

## Scripts Used

- **tech-seo-auditor.py** — Fetch page and analyze image elements
