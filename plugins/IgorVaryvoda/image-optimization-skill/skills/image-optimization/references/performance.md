# Image Performance Reference

## Table of Contents
1. [Core Web Vitals](#core-web-vitals)
2. [Loading Strategies](#loading-strategies)
3. [Image Placeholder Strategies](#image-placeholder-strategies)
4. [Lazy Loading](#lazy-loading)
5. [Preloading](#preloading)
6. [CDN and Caching](#cdn-and-caching)
7. [HTTP Headers](#http-headers)
8. [Performance Budgets](#performance-budgets)
9. [Measuring Performance](#measuring-performance)

---

## Core Web Vitals

### LCP (Largest Contentful Paint)

**What it measures:** Time until largest content element is visible
**Target:** < 2.5 seconds
**Images impact:** Hero images often ARE the LCP element

**Optimization strategies:**
- Preload LCP images
- Use `fetchpriority="high"` for LCP images (critical!)
- Use optimal format (AVIF/WebP)
- Right-size images (don't serve 4K to mobile)
- Serve from CDN with preconnect
- Avoid lazy loading LCP images
- Keep the LCP `<img>` in the server HTML; do not inject it with client-side JS

```html
<!-- Resource hints for image CDN -->
<link rel="preconnect" href="https://your-cdn.sirv.com" crossorigin>
<link rel="dns-prefetch" href="https://your-cdn.sirv.com">

<!-- Preload LCP hero image with fetchpriority -->
<link
  rel="preload"
  as="image"
  href="hero.webp"
  type="image/webp"
  fetchpriority="high"
>

<!-- With responsive images -->
<link
  rel="preload"
  as="image"
  href="hero-1200.webp"
  imagesrcset="hero-600.webp 600w, hero-1200.webp 1200w, hero-1800.webp 1800w"
  imagesizes="100vw"
  type="image/webp"
  fetchpriority="high"
>

<!-- LCP image in HTML -->
<img
  src="hero.webp"
  fetchpriority="high"
  decoding="sync"
  alt="Hero"
  width="1200"
  height="600"
>
```

### CLS (Cumulative Layout Shift)

**What it measures:** Visual stability (unexpected layout shifts)
**Target:** < 0.1
**Images impact:** Images without dimensions cause major shifts

**Optimization strategies:**
- Always include width and height attributes
- Use CSS aspect-ratio
- Reserve space with containers
- Avoid inserting content above images

```html
<!-- Prevents layout shift -->
<img
  src="photo.jpg"
  width="800"
  height="600"
  alt="Description"
>

<!-- Or with CSS -->
<style>
  .image-container {
    aspect-ratio: 4 / 3;
  }
</style>
```

### INP (Interaction to Next Paint)

**What it measures:** Input responsiveness. INP replaced FID as a Core Web Vital in March 2024.
**Target:** < 200 ms
**Images impact:** Large image decoding can block main thread

**Optimization strategies:**
- Use `decoding="async"` for non-critical images
- Compress images to reduce decode time
- Avoid huge images that take long to decode

```html
<img
  src="photo.jpg"
  decoding="async"
  loading="lazy"
  alt="Description"
>
```

---

## Loading Strategies

### Eager Loading (Default)

Image loads immediately with page.

```html
<img src="hero.jpg" alt="Hero">
<!-- or explicitly -->
<img src="hero.jpg" loading="eager" alt="Hero">
```

**Use for:**
- Above-the-fold images
- LCP images
- Critical content

### Lazy Loading

Image loads when approaching viewport.

```html
<img src="photo.jpg" loading="lazy" alt="Photo">
```

**Use for:**
- Below-the-fold images
- Image galleries
- Long lists of images

### Priority Hints

Control fetch priority:

```html
<!-- High priority (LCP images) -->
<img src="hero.jpg" fetchpriority="high" alt="Hero">

<!-- Low priority (decorative, below fold) -->
<img src="decoration.jpg" fetchpriority="low" loading="lazy" alt="">
```

### Decoding Hints

Control decode timing:

```html
<!-- Async decode (non-blocking) -->
<img src="photo.jpg" decoding="async" alt="Photo">

<!-- Sync decode (blocking, use for critical images) -->
<img src="hero.jpg" decoding="sync" alt="Hero">

<!-- Let browser decide -->
<img src="photo.jpg" decoding="auto" alt="Photo">
```

---

## Image Placeholder Strategies

Placeholders improve perceived performance by showing something immediately while the full image loads.

### LQIP (Low Quality Image Placeholder)

Show a tiny, heavily compressed version as a CSS background behind the real image. The real `<img>` keeps its normal `src`/`srcset`, so the browser discovers it from HTML and LCP is not delayed by JS:

```html
<div class="lqip" style="background-image: url('hero-lqip.jpg'); aspect-ratio: 16 / 9;">
  <img src="hero.jpg" width="1600" height="900" alt="Hero">
</div>
```

```css
.lqip {
  background-size: cover;
}

.lqip img {
  display: block;
  width: 100%;
  height: auto;
}
```

Do not swap `data-src` into `src` with JS for the LCP image. The browser cannot discover the real URL until the script runs.

**Generation with Sharp:**
```javascript
await sharp('hero.jpg')
  .resize(20)
  .blur()
  .jpeg({ quality: 20 })
  .toFile('hero-lqip.jpg');
```

### Blur-Up Technique with Base64

Inline tiny images as base64 data URIs:

```html
<img
  src="data:image/jpeg;base64,/9j/4AAQSkZJRg..."
  data-src="hero-full.jpg"
  class="blur-up"
  alt="Hero"
>
```

**Generation with Sharp:**
```javascript
const placeholder = await sharp('hero.jpg')
  .resize(10)
  .blur()
  .jpeg({ quality: 20 })
  .toBuffer();

const base64 = `data:image/jpeg;base64,${placeholder.toString('base64')}`;
```

### Dominant Color Extraction

Extract the dominant color and use as placeholder background:

```html
<div class="image-wrapper" style="background-color: #3b82f6;">
  <img src="hero.jpg" loading="lazy" alt="Hero">
</div>
```

**Extraction with Sharp:**
```javascript
const { dominant } = await sharp('hero.jpg').stats();
const color = `rgb(${dominant.r}, ${dominant.g}, ${dominant.b})`;
```

### Skeleton Loaders

CSS-only animated placeholders:

```html
<div class="skeleton-image" style="aspect-ratio: 16/9;">
  <img src="hero.jpg" loading="lazy" onload="this.parentElement.classList.remove('loading')" alt="Hero">
</div>
```

```css
.skeleton-image.loading {
  background: linear-gradient(
    90deg,
    #f0f0f0 25%,
    #e0e0e0 50%,
    #f0f0f0 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

.skeleton-image.loading img {
  opacity: 0;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
```

### Placeholder Strategy Comparison

| Strategy | Initial Load | Visual Quality | Implementation |
|----------|--------------|----------------|----------------|
| LQIP | +1-2KB | Good preview | Medium |
| Base64 blur | +200-500 bytes | Blurry preview | Easy |
| Dominant color | 0 extra | Solid color | Easy |
| Skeleton | 0 extra | Animated shape | Easy |
| None | 0 extra | Flash of empty | None |

### Blurhash (Compact Representation)

Encode images as compact strings for client-side decoding:

```javascript
import { encode, decode } from 'blurhash';

// Server-side: encode image to blurhash string
const hash = encode(pixels, width, height, 4, 3);
// Result: "LEHV6nWB2yk8pyo0adR*.7kCMdnj"

// Client-side: decode to placeholder
const pixels = decode(hash, 32, 32);
```

**Framework integrations:**
- React: `react-blurhash`
- Vue: `vue-blurhash`
- Next.js: Built-in with `placeholder="blur"`

---

## Lazy Loading

### Native Lazy Loading

```html
<img src="photo.jpg" loading="lazy" alt="Photo">
```

**Browser behavior:**
- Chrome/Edge: Starts loading ~1250-2500px before viewport
- Firefox: Similar approach
- Safari: Supported since iOS 15.4, Safari 15.4

**Caveats:**
- Threshold not configurable
- No placeholder support
- No fade-in animations

### JavaScript Lazy Loading

For more control, use Intersection Observer:

```javascript
const lazyImages = document.querySelectorAll('img[data-src]');

const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const img = entry.target;
      img.src = img.dataset.src;
      img.removeAttribute('data-src');
      observer.unobserve(img);
    }
  });
}, {
  rootMargin: '200px' // Start loading 200px before viewport
});

lazyImages.forEach(img => observer.observe(img));
```

HTML:
```html
<img data-src="photo.jpg" alt="Photo">
```

Native `loading="lazy"` covers most cases. Lazy-loading libraries such as lazysizes are not needed in current browsers, and their `data-src` markup hides images from the preload scanner.

### Best Practices

- Never lazy load LCP/hero images
- Use native `loading="lazy"` when sufficient
- Provide low-quality placeholders (LQIP) for better UX
- Set width/height to prevent layout shift
- Consider using blur-up technique

---

## Preloading

### Basic Preload

```html
<link rel="preload" as="image" href="hero.jpg">
```

### With Modern Formats

```html
<link
  rel="preload"
  as="image"
  href="hero.avif"
  type="image/avif"
>
```

### Responsive Preload

```html
<link
  rel="preload"
  as="image"
  href="hero.jpg"
  imagesrcset="
    hero-400.jpg 400w,
    hero-800.jpg 800w,
    hero-1200.jpg 1200w
  "
  imagesizes="100vw"
>
```

### With Fetch Priority

```html
<link
  rel="preload"
  as="image"
  href="hero.jpg"
  fetchpriority="high"
>
```

### Preload vs Prefetch

**Preload:** Current page, high priority, fetch immediately
```html
<link rel="preload" as="image" href="hero.jpg">
```

**Prefetch:** Future navigation, low priority, fetch when idle
```html
<link rel="prefetch" as="image" href="next-page-hero.jpg">
```

---

## CDN and Caching

### Why Use an Image CDN?

1. **Edge caching** - Serve from nearest location
2. **Automatic optimization** - Convert to modern formats
3. **On-the-fly resize** - Generate sizes as needed
4. **Reduced origin load** - CDN handles requests

URL syntax for each image CDN: see [tools.md](tools.md#image-cdn-url-syntax).

### Cache Headers

**Long cache with versioning:**
```
Cache-Control: public, max-age=31536000, immutable
```

Use with content-hashed filenames: `image.abc123.jpg`

**Shorter cache for dynamic:**
```
Cache-Control: public, max-age=86400, stale-while-revalidate=604800
```

### Service Worker Caching

```javascript
// Cache images with stale-while-revalidate
workbox.routing.registerRoute(
  ({request}) => request.destination === 'image',
  new workbox.strategies.StaleWhileRevalidate({
    cacheName: 'images',
    plugins: [
      new workbox.expiration.ExpirationPlugin({
        maxEntries: 100,
        maxAgeSeconds: 30 * 24 * 60 * 60 // 30 days
      })
    ]
  })
);
```

---

## HTTP Headers

### Content-Type

Always serve correct MIME type:
```
Content-Type: image/webp
Content-Type: image/avif
Content-Type: image/jpeg
Content-Type: image/png
```

### Accept Header for Format Negotiation

Browser sends:
```
Accept: image/avif,image/webp,image/apng,image/*,*/*;q=0.8
```

Server can respond with best supported format.

### Content-Length

Enable for progress indication:
```
Content-Length: 45678
```

### Compression

Images are already compressed. Don't gzip/brotli them:
```
# In nginx, exclude images from gzip
gzip_types text/plain application/json text/css;
```

Exception: SVG benefits from compression:
```
Content-Encoding: gzip
Content-Type: image/svg+xml
```

---

## Performance Budgets

### Image Size Budgets

| Page Type | Total Images | Per Image (avg) |
|-----------|--------------|-----------------|
| Landing page | < 500KB | < 100KB |
| Blog post | < 1MB | < 150KB |
| E-commerce | < 2MB | < 200KB |
| Portfolio | < 3MB | < 300KB |

### Request Budgets

| Metric | Target |
|--------|--------|
| Image requests | < 20 per page |
| Above-fold images | < 5 |
| Total page weight | < 3MB |

### LCP Budget

| Rating | Time |
|--------|------|
| Good | < 2.5s |
| Needs work | 2.5-4s |
| Poor | > 4s |

### Enforcing Budgets

**Webpack:**
```javascript
performance: {
  maxAssetSize: 200000, // 200KB per asset
  maxEntrypointSize: 500000, // 500KB total
  hints: 'error'
}
```

**Lighthouse CI:**
```json
{
  "assertions": {
    "resource-summary:image:size": ["error", {"maxNumericValue": 500000}],
    "largest-contentful-paint": ["error", {"maxNumericValue": 2500}]
  }
}
```

---

## Measuring Performance

### Chrome DevTools

**Network tab:**
- Filter by "Img"
- Check file sizes and load times
- Look for unnecessary large images

**Performance tab:**
- Record page load
- Find LCP element
- Check image decode time

**Lighthouse (13+):**
- Run in incognito
- Check the "Improve image delivery" insight (`image-delivery-insight`). It replaces the old "Properly size images", "Serve images in modern formats", and "Efficiently encode images" audits.
- Check the "LCP request discovery" insight (`lcp-discovery-insight`) for lazy-loaded or late-discovered LCP images.
- Scripts or CI that use the old audit IDs need the new insight IDs.

### PageSpeed Insights

- Real user data (CrUX)
- Lab data (Lighthouse)
- Specific image recommendations
- LCP element identification

### WebPageTest

- Multi-location testing
- Filmstrip view
- Request breakdown
- Waterfall analysis

### Key Metrics to Track

| Metric | Tool | Target |
|--------|------|--------|
| LCP | Lighthouse, CrUX | < 2.5s |
| CLS | Lighthouse, CrUX | < 0.1 |
| Total image weight | DevTools | < 1MB |
| Image requests | DevTools | < 20 |
| Format adoption | DevTools | > 80% modern |

### Real User Monitoring (RUM)

Track LCP in production:
```javascript
new PerformanceObserver((entryList) => {
  for (const entry of entryList.getEntries()) {
    console.log('LCP:', entry.startTime, entry.element);
    // Send to analytics
  }
}).observe({type: 'largest-contentful-paint', buffered: true});
```
