# Responsive Images Reference

## Table of Contents
1. [Core Concepts](#core-concepts)
2. [srcset Attribute](#srcset-attribute)
3. [sizes Attribute](#sizes-attribute)
4. [Picture Element](#picture-element)
5. [Art Direction](#art-direction)
6. [Common Patterns](#common-patterns)
7. [Priority and Loading Hints](#priority-and-loading-hints)
8. [Container Queries for Images](#container-queries-for-images)
9. [Breakpoint Selection](#breakpoint-selection)
10. [CSS Background Images](#css-background-images)
11. [Aspect Ratio Handling](#aspect-ratio-handling)

---

## Core Concepts

### Why Responsive Images?

**Problems solved:**
- Mobile users downloading desktop-sized images
- Retina displays showing blurry images
- Different screen sizes needing different crops
- New formats not supported by all browsers

**Three main techniques:**
1. **Resolution switching** - Same image, different sizes
2. **Density descriptors** - Same size, different resolutions
3. **Art direction** - Different images for different contexts

---

## srcset Attribute

### Width Descriptors (w)

Tell browser available image widths:

```html
<img
  src="image-800.jpg"
  srcset="
    image-320.jpg 320w,
    image-480.jpg 480w,
    image-768.jpg 768w,
    image-1024.jpg 1024w,
    image-1600.jpg 1600w,
    image-2000.jpg 2000w
  "
  sizes="(max-width: 768px) 100vw, 50vw"
  alt="Description"
>
```

**How browsers choose:**
1. Parse `sizes` to determine display width
2. Calculate effective pixel density: `image_width / display_width`
3. Select closest match to device pixel ratio

### Density Descriptors (x)

For fixed-size images with different resolutions:

```html
<img
  src="logo.png"
  srcset="
    logo.png 1x,
    logo@2x.png 2x,
    logo@3x.png 3x
  "
  alt="Logo"
  width="200"
  height="50"
>
```

**Use when:**
- Image has fixed display size
- Only resolution varies, not layout

**Don't use when:**
- Image width changes with viewport
- Use width descriptors instead

---

## sizes Attribute

Tells browser how wide image will display at different viewport sizes.

### Syntax

```
sizes="[media condition] [length], [fallback length]"
```

### Media Conditions

```html
<!-- Full width on mobile, half on desktop -->
sizes="(max-width: 768px) 100vw, 50vw"

<!-- Multiple breakpoints -->
sizes="
  (max-width: 480px) 100vw,
  (max-width: 768px) 80vw,
  (max-width: 1200px) 50vw,
  33vw
"

<!-- Fixed width at certain sizes -->
sizes="(min-width: 1024px) 400px, 100vw"
```

### Length Values

| Unit | Description | Example |
|------|-------------|---------|
| `vw` | Viewport width percentage | `100vw`, `50vw` |
| `px` | Fixed pixels | `400px` |
| `calc()` | Calculated value | `calc(100vw - 32px)` |
| `em` | Relative to font size | `30em` |

### Common Patterns

```html
<!-- Full bleed image -->
sizes="100vw"

<!-- Contained with padding -->
sizes="calc(100vw - 32px)"

<!-- Max-width container -->
sizes="(min-width: 1200px) 1200px, 100vw"

<!-- Two-column layout -->
sizes="(min-width: 768px) 50vw, 100vw"

<!-- Three-column on desktop -->
sizes="(min-width: 1024px) 33vw, (min-width: 768px) 50vw, 100vw"

<!-- Lazy image: browser measures the real layout width -->
<img loading="lazy" sizes="auto, (min-width: 1024px) 33vw, 100vw" ...>
```

`sizes="auto"` works only with `loading="lazy"` and only in Chromium 126+. Keep a normal `sizes` list after `auto` as the fallback for other browsers. Do not use it on the LCP image.

---

## Picture Element

Use `<picture>` for:
- Format fallbacks (AVIF → WebP → JPEG)
- Art direction (different crops)
- Media-based image selection

### Format Fallbacks

```html
<picture>
  <source srcset="image.avif" type="image/avif">
  <source srcset="image.webp" type="image/webp">
  <img src="image.jpg" alt="Description">
</picture>
```

Browser uses first supported format.

### Combined with srcset

```html
<picture>
  <source
    srcset="
      image-400.avif 400w,
      image-800.avif 800w,
      image-1200.avif 1200w
    "
    sizes="(min-width: 768px) 50vw, 100vw"
    type="image/avif"
  >
  <source
    srcset="
      image-400.webp 400w,
      image-800.webp 800w,
      image-1200.webp 1200w
    "
    sizes="(min-width: 768px) 50vw, 100vw"
    type="image/webp"
  >
  <img
    src="image-800.jpg"
    srcset="
      image-400.jpg 400w,
      image-800.jpg 800w,
      image-1200.jpg 1200w
    "
    sizes="(min-width: 768px) 50vw, 100vw"
    alt="Description"
  >
</picture>
```

---

## Art Direction

Different images for different contexts (not just scaled versions).

### Cropping for Different Screens

```html
<picture>
  <!-- Wide crop for desktop -->
  <source
    media="(min-width: 1024px)"
    srcset="hero-wide.jpg"
  >
  <!-- Square crop for tablet -->
  <source
    media="(min-width: 768px)"
    srcset="hero-square.jpg"
  >
  <!-- Tall crop for mobile -->
  <img src="hero-tall.jpg" alt="Hero image">
</picture>
```

### Different Content for Contexts

```html
<picture>
  <!-- Full product shot for desktop -->
  <source
    media="(min-width: 768px)"
    srcset="product-full.jpg"
  >
  <!-- Close-up detail for mobile -->
  <img src="product-detail.jpg" alt="Product">
</picture>
```

### Combining Art Direction with Formats

```html
<picture>
  <!-- Desktop: wide crop, modern formats -->
  <source
    media="(min-width: 1024px)"
    srcset="hero-wide.avif"
    type="image/avif"
  >
  <source
    media="(min-width: 1024px)"
    srcset="hero-wide.webp"
    type="image/webp"
  >
  <source
    media="(min-width: 1024px)"
    srcset="hero-wide.jpg"
  >

  <!-- Mobile: tall crop, modern formats -->
  <source
    srcset="hero-tall.avif"
    type="image/avif"
  >
  <source
    srcset="hero-tall.webp"
    type="image/webp"
  >
  <img src="hero-tall.jpg" alt="Hero">
</picture>
```

---

## Common Patterns

### Full-Width Hero Image

```html
<picture>
  <source srcset="hero.avif" type="image/avif">
  <source srcset="hero.webp" type="image/webp">
  <img
    src="hero-1600.jpg"
    srcset="
      hero-640.jpg 640w,
      hero-960.jpg 960w,
      hero-1280.jpg 1280w,
      hero-1600.jpg 1600w,
      hero-1920.jpg 1920w,
      hero-2560.jpg 2560w
    "
    sizes="100vw"
    alt="Hero image"
    fetchpriority="high"
  >
</picture>
```

### Product Grid (3 columns)

```html
<img
  src="product-400.jpg"
  srcset="
    product-200.jpg 200w,
    product-300.jpg 300w,
    product-400.jpg 400w,
    product-600.jpg 600w,
    product-800.jpg 800w
  "
  sizes="(min-width: 1024px) 33vw, (min-width: 640px) 50vw, 100vw"
  alt="Product name"
  loading="lazy"
>
```

### Blog Post Thumbnail

```html
<img
  src="thumb-600.jpg"
  srcset="
    thumb-300.jpg 300w,
    thumb-450.jpg 450w,
    thumb-600.jpg 600w,
    thumb-900.jpg 900w
  "
  sizes="(min-width: 768px) 300px, 100vw"
  alt="Article thumbnail"
  loading="lazy"
>
```

### Logo (Fixed Size)

```html
<img
  src="logo.png"
  srcset="
    logo.png 1x,
    logo@2x.png 2x,
    logo@3x.png 3x
  "
  alt="Company logo"
  width="180"
  height="40"
>
```

---

## Priority and Loading Hints

### fetchpriority Attribute

Control the fetch priority of images:

```html
<!-- High priority for LCP/hero images -->
<img
  src="hero.jpg"
  fetchpriority="high"
  alt="Hero"
>

<!-- Low priority for below-fold decorative images -->
<img
  src="decoration.jpg"
  fetchpriority="low"
  loading="lazy"
  alt=""
>

<!-- Auto (default) for standard images -->
<img
  src="content.jpg"
  fetchpriority="auto"
  alt="Content"
>
```

### Combined with Picture Element

```html
<picture>
  <source srcset="hero.avif" type="image/avif">
  <source srcset="hero.webp" type="image/webp">
  <img
    src="hero.jpg"
    fetchpriority="high"
    decoding="sync"
    alt="Hero"
    width="1200"
    height="600"
  >
</picture>
```

### Priority Decision Matrix

| Image Type | fetchpriority | loading | decoding |
|------------|---------------|---------|----------|
| LCP/Hero | high | eager | sync |
| Above-fold content | auto | eager | async |
| Below-fold | low | lazy | async |
| Decorative | low | lazy | async |
| Thumbnails | auto | lazy | async |

---

## Container Queries for Images

Container queries enable responsive images based on container size, not viewport.

### Basic Container Query Setup

```css
.card {
  container-type: inline-size;
  container-name: card;
}

.card img {
  width: 100%;
  height: auto;
}

/* Small container: square thumbnail */
@container card (max-width: 300px) {
  .card img {
    aspect-ratio: 1;
    object-fit: cover;
  }
}

/* Medium container: 4:3 ratio */
@container card (min-width: 301px) and (max-width: 600px) {
  .card img {
    aspect-ratio: 4/3;
    object-fit: cover;
  }
}

/* Large container: wide banner */
@container card (min-width: 601px) {
  .card img {
    aspect-ratio: 16/9;
    object-fit: cover;
  }
}
```

### Container-Based Image Selection with JavaScript

```html
<img
  src="image-medium.jpg"
  data-small="image-small.jpg"
  data-medium="image-medium.jpg"
  data-large="image-large.jpg"
  class="container-responsive"
  alt="Product"
>
```

```javascript
const observer = new ResizeObserver(entries => {
  entries.forEach(entry => {
    const img = entry.target.querySelector('.container-responsive');
    if (!img) return;

    const width = entry.contentRect.width;
    if (width < 300) {
      img.src = img.dataset.small;
    } else if (width < 600) {
      img.src = img.dataset.medium;
    } else {
      img.src = img.dataset.large;
    }
  });
});

document.querySelectorAll('.card').forEach(card => observer.observe(card));
```

### Container Query Units

```css
.card {
  container-type: inline-size;
}

.card img {
  /* Container query units */
  width: 100cqw;    /* 100% of container width */
  height: 50cqh;    /* 50% of container height (if defined) */
  font-size: 5cqi;  /* 5% of container inline size */
}
```

### Browser Support

Container queries are supported in:
- Chrome 105+
- Firefox 110+
- Safari 16+
- Edge 105+

For older browsers, the base styles apply as fallback.

---

## Breakpoint Selection

### Recommended Image Widths

Generate images at these widths to cover common scenarios:

**Minimum set:**
320, 640, 960, 1280, 1920

**Comprehensive set:**
320, 480, 640, 768, 960, 1024, 1280, 1440, 1600, 1920, 2560

### Calculating Breakpoints

Consider:
- Common viewport widths
- Your layout breakpoints
- Device pixel ratios (1x, 2x, 3x)

Formula for max needed width:
```
max_image_width = max_display_width × max_dpr

Example: 800px display × 3 DPR = 2400px image needed
```

### Avoiding Redundancy

Don't create variants that are too close:
- Minimum 20-25% difference between sizes
- Example: 400, 500, 625, 800, 1000, 1250...

---

## CSS Background Images

### Basic Responsive Background

```css
.hero {
  background-image: url('hero-mobile.jpg');
  background-size: cover;
  background-position: center;
}

@media (min-width: 768px) {
  .hero {
    background-image: url('hero-tablet.jpg');
  }
}

@media (min-width: 1024px) {
  .hero {
    background-image: url('hero-desktop.jpg');
  }
}
```

### With Resolution Switching

```css
.hero {
  background-image: url('hero-1x.jpg');
}

@media (min-resolution: 2dppx) {
  .hero {
    background-image: url('hero-2x.jpg');
  }
}
```

### image-set() Function

```css
.hero {
  background-image: image-set(
    url('hero.avif') type('image/avif'),
    url('hero.webp') type('image/webp'),
    url('hero.jpg') type('image/jpeg')
  );
}

/* With resolution variants */
.logo {
  background-image: image-set(
    url('logo-1x.png') 1x,
    url('logo-2x.png') 2x,
    url('logo-3x.png') 3x
  );
}
```

---

## Aspect Ratio Handling

### Preventing Layout Shift

Always set dimensions:

```html
<img
  src="image.jpg"
  width="800"
  height="600"
  alt="Description"
>
```

Or use CSS aspect-ratio:

```css
img {
  aspect-ratio: 4 / 3;
  width: 100%;
  height: auto;
}
```

### object-fit Options

```css
img {
  width: 100%;
  height: 300px;
  object-fit: cover; /* Crops to fill */
  /* object-fit: contain; */ /* Shows all, may letterbox */
  /* object-fit: fill; */ /* Stretches, may distort */
  object-position: center; /* Or: top, bottom, left, right */
}
```

### Container with Fixed Aspect Ratio

```css
.image-container {
  aspect-ratio: 16 / 9;
  overflow: hidden;
}

.image-container img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
```

### Common Aspect Ratios

| Ratio | Decimal | Use Case |
|-------|---------|----------|
| 1:1 | 1.0 | Profile pics, thumbnails |
| 4:3 | 1.33 | Traditional photos |
| 3:2 | 1.5 | DSLR photos |
| 16:9 | 1.78 | Videos, hero images |
| 21:9 | 2.33 | Cinematic banners |
| 2:3 | 0.67 | Portrait/mobile |
