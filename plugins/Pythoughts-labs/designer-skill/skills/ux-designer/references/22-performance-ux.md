# Performance & Loading UX

Perceived performance is often more important than actual performance. Users judge an app's speed not by stopwatch measurements but by how fast it *feels*. This reference covers techniques for making interfaces feel instant, responsive, and reliable.

---

## Perceived Performance

### Response Time Thresholds

| Duration | Perception | UX Treatment |
|----------|-----------|--------------|
| < 100ms | Instant | No indicator needed |
| 100-300ms | Slight delay | Subtle state change (button press) |
| 300ms-1s | Noticeable | Show spinner or progress hint |
| 1-5s | Waiting | Skeleton screen or progress bar |
| 5-10s | Frustrated | Progress bar with estimate + cancel |
| > 10s | Abandonment risk | Progress steps, background processing option |

### Techniques for Feeling Fast

1. **Optimistic updates** — Apply changes immediately, sync later
2. **Skeleton screens** — Show content shape before data arrives
3. **Progressive loading** — Show most important content first
4. **Prefetching** — Load likely-next content before user requests it
5. **Instant navigation** — Use client-side routing with prefetch
6. **Animation as distraction** — Meaningful transitions mask load time

---

## Loading Indicator Decision Tree

```
How long will the operation take?
├── < 100ms (instant)?
│   └── → No indicator (just update the UI)
├── 100ms - 1s (brief)?
│   ├── User triggered the action?
│   │   └── → Button loading state (spinner replaces label or inline spinner)
│   └── Background/automatic?
│       └── → No indicator (avoid flicker)
├── 1s - 5s (noticeable)?
│   ├── Loading content for a region/page?
│   │   └── → Skeleton screen (matches target layout)
│   ├── Processing user action?
│   │   └── → Inline spinner with status text ("Saving...")
│   └── Unknown duration?
│       └── → Indeterminate progress bar
├── 5s - 30s (long)?
│   ├── Duration is predictable?
│   │   └── → Determinate progress bar with percentage
│   └── Duration is unpredictable?
│       └── → Indeterminate progress with stage labels
└── > 30s (very long)?
    └── → Background task with notification on completion
        ("We'll email you when your export is ready")
```

---

## Skeleton Screens

Skeleton screens show a low-fidelity preview of the content layout before data loads. They reduce perceived wait time and prevent layout shifts.

### Basic Skeleton

```css
.skeleton {
  background: #e5e7eb;
  border-radius: 4px;
  position: relative;
  overflow: hidden;
}

/* Shimmer animation */
.skeleton::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(255, 255, 255, 0.4) 50%,
    transparent 100%
  );
  animation: skeleton-shimmer 1.5s infinite;
}

@keyframes skeleton-shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}
```

### Skeleton Variants

```html
<!-- Text skeleton -->
<div class="skeleton skeleton--text" style="width: 80%; height: 16px;"></div>
<div class="skeleton skeleton--text" style="width: 60%; height: 16px;"></div>

<!-- Avatar skeleton -->
<div class="skeleton skeleton--circle" style="width: 40px; height: 40px;"></div>

<!-- Image skeleton -->
<div class="skeleton skeleton--image" style="width: 100%; aspect-ratio: 16/9;"></div>

<!-- Card skeleton -->
<div class="skeleton-card">
  <div class="skeleton skeleton--image" style="height: 200px;"></div>
  <div style="padding: 16px;">
    <div class="skeleton skeleton--text" style="width: 70%; height: 20px;"></div>
    <div class="skeleton skeleton--text" style="width: 100%; height: 14px; margin-top: 8px;"></div>
    <div class="skeleton skeleton--text" style="width: 40%; height: 14px; margin-top: 8px;"></div>
  </div>
</div>
```

### Skeleton Best Practices

| Do | Don't |
|----|-------|
| Match the actual content layout | Use generic shapes unrelated to content |
| Use subtle animation (shimmer) | Use pulsing that draws too much attention |
| Show for > 300ms loads | Show for instant loads (causes flicker) |
| Transition smoothly to real content | Pop content in abruptly |
| Keep skeleton visible while data loads | Replace skeleton with spinner |

### Skeleton Transition

```javascript
function showContent(container, data) {
  const skeleton = container.querySelector('.skeleton-wrapper');
  const content = container.querySelector('.content-wrapper');

  // Populate content using safe DOM methods (e.g., textContent,
  // createElement, or a framework's reactive rendering)
  renderDataToDOM(content, data);

  // Cross-fade transition
  skeleton.style.opacity = '0';
  content.style.opacity = '1';

  setTimeout(() => skeleton.remove(), 300);
}
```

```css
.skeleton-wrapper,
.content-wrapper {
  transition: opacity 300ms ease;
}

.content-wrapper {
  opacity: 0;
}
```

---

## Optimistic Updates

Apply changes to the UI immediately before server confirmation, then reconcile.

### Pattern

```javascript
async function toggleFavorite(itemId) {
  // 1. Optimistic: update UI immediately
  const previousState = getItem(itemId).isFavorite;
  updateItemUI(itemId, { isFavorite: !previousState });

  try {
    // 2. Send to server
    await api.toggleFavorite(itemId);
    // Success: UI already correct, nothing to do
  } catch (error) {
    // 3. Rollback on failure
    updateItemUI(itemId, { isFavorite: previousState });
    showToast('Failed to update. Please try again.', { type: 'error' });
  }
}
```

### When to Use Optimistic Updates

| Use Optimistic | Don't Use |
|---------------|-----------|
| Toggles (like, favorite, bookmark) | Financial transactions |
| Status changes (read/unread) | Destructive actions (delete) |
| Form field auto-save | Multi-step workflows |
| Reordering lists | Actions requiring server validation |
| Adding/removing tags | External system integrations |

### Optimistic Update UX Requirements

- Always have a rollback path
- Show subtle "saving" indicator (not blocking)
- On failure: revert UI + show clear error message
- On conflict: show resolution UI (merge dialog)
- Debounce rapid changes (typing, slider adjustments)

---

## Progress Indicators

### Indeterminate Progress

For operations where duration is unknown.

```css
/* Indeterminate progress bar */
.progress-bar--indeterminate {
  height: 4px;
  background: #e5e7eb;
  border-radius: 2px;
  overflow: hidden;
}

.progress-bar--indeterminate::after {
  content: '';
  display: block;
  height: 100%;
  width: 40%;
  background: #3b82f6;
  border-radius: 2px;
  animation: indeterminate 1.5s infinite ease-in-out;
}

@keyframes indeterminate {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(350%); }
}
```

### Determinate Progress

For operations where progress can be measured.

```html
<div class="progress-container">
  <div class="progress-bar" role="progressbar"
       aria-valuenow="65" aria-valuemin="0" aria-valuemax="100">
    <div class="progress-bar__fill" style="width: 65%"></div>
  </div>
  <span class="progress-label">65% — Uploading 3 of 5 files</span>
</div>
```

### Multi-Step Progress

```
┌──────────────────────────────────────────────────────────────┐
│ Importing data...                                            │
│                                                              │
│ ✓ Validating file format                                     │
│ ✓ Parsing 1,234 records                                      │
│ ⟳ Importing to database (847 of 1,234)                       │
│ ○ Running post-import checks                                 │
│                                                              │
│ ████████████████████░░░░░░░░░░ 68%        [Cancel import]    │
└──────────────────────────────────────────────────────────────┘
```

### Button Loading States

```css
.btn--loading {
  position: relative;
  color: transparent; /* Hide text */
  pointer-events: none;
}

.btn--loading::after {
  content: '';
  position: absolute;
  width: 16px;
  height: 16px;
  top: 50%;
  left: 50%;
  margin: -8px 0 0 -8px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: button-spin 0.6s linear infinite;
}

@keyframes button-spin {
  to { transform: rotate(360deg); }
}
```

**Button loading best practices:**
- Disable the button to prevent double-submit
- Keep button dimensions constant (no layout shift)
- Show spinner inside the button, not replacing it
- Optionally change label: "Save" → "Saving..."

---

## Image Loading Strategies

### Lazy Loading

Only load images when they enter (or approach) the viewport.

```html
<!-- Native lazy loading -->
<img src="photo.jpg" loading="lazy" alt="Description"
     width="800" height="600">
```

### Blur-Up / LQIP (Low Quality Image Placeholder)

Show a tiny, blurred preview that transitions to the full image.

```html
<div class="image-wrapper">
  <img class="image-placeholder" src="photo-20px.jpg"
       style="filter: blur(20px); transform: scale(1.1);"
       aria-hidden="true">
  <img class="image-full" src="photo-800px.jpg" loading="lazy"
       alt="Description"
       onload="this.classList.add('loaded')">
</div>
```

```css
.image-wrapper {
  position: relative;
  overflow: hidden;
}

.image-placeholder {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.image-full {
  opacity: 0;
  transition: opacity 300ms ease;
}

.image-full.loaded {
  opacity: 1;
}
```

### Responsive Images

```html
<img
  srcset="photo-400w.jpg 400w,
          photo-800w.jpg 800w,
          photo-1200w.jpg 1200w"
  sizes="(max-width: 600px) 400px,
         (max-width: 1000px) 800px,
         1200px"
  src="photo-800w.jpg"
  alt="Description"
  loading="lazy"
>
```

### Image Loading Decision Tree

```
What type of image is it?
├── Above the fold (hero, logo, critical UI)?
│   └── → Eager load, preload via <link>, use srcset
├── Below the fold (content images)?
│   └── → loading="lazy", use LQIP/blur-up for large images
├── Thumbnail in a list/grid?
│   └── → loading="lazy", fixed dimensions, skeleton placeholder
├── Background/decorative?
│   └── → CSS background with lazy class, low priority
└── User avatar?
    └── → Eager load if visible, fixed dimensions, fallback initial
```

---

## Content Layout Shift Prevention

Layout shifts are disorienting and frustrating. They happen when content dimensions change after initial render.

### Core Web Vitals: CLS

- **Good:** CLS < 0.1
- **Needs improvement:** 0.1 - 0.25
- **Poor:** CLS > 0.25

### Prevention Techniques

#### Reserve Space for Images

```css
/* Always specify dimensions */
img {
  width: 100%;
  height: auto;
  aspect-ratio: 16 / 9; /* Reserve space before load */
}

/* Container with aspect ratio */
.image-container {
  position: relative;
  width: 100%;
  aspect-ratio: 4 / 3;
  background: #f3f4f6;
}
```

#### Reserve Space for Fonts

```css
/* Use font-display to control FOIT/FOUT */
@font-face {
  font-family: 'CustomFont';
  src: url('font.woff2') format('woff2');
  font-display: swap; /* Show fallback immediately, swap when loaded */
}

/* Match fallback font metrics to reduce shift */
body {
  font-family: 'CustomFont', system-ui, sans-serif;
  font-size-adjust: 0.5; /* Normalize x-height */
}
```

#### Reserve Space for Dynamic Content

```css
/* Fixed-height containers for dynamic content */
.ad-slot {
  min-height: 250px;
  background: #f3f4f6;
}

.notification-area {
  min-height: 0;
  transition: min-height 300ms ease; /* Smooth expansion */
}
```

#### Avoid CLS-Causing Patterns

| Pattern | Problem | Solution |
|---------|---------|----------|
| Images without dimensions | Jump when loaded | Always set width/height or aspect-ratio |
| Injected content above viewport | Pushes content down | Insert below or use overlay |
| Web fonts without fallback | Text reflows | Use font-display: swap + size-adjust |
| Dynamic ads/banners | Layout shift on load | Reserve fixed space |
| Late-loading components | Layout reflowing | Use skeleton placeholders |

---

## Offline-First & Cached State UX

### Connection Status

```css
/* Offline indicator */
.offline-banner {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 8px 16px;
  background: #fef3c7;
  color: #92400e;
  text-align: center;
  font-size: 14px;
  z-index: 9999;
  transform: translateY(100%);
  transition: transform 300ms ease;
}

.offline-banner--visible {
  transform: translateY(0);
}
```

### Stale Content Indicators

```html
<div class="stale-notice">
  <span>Last updated 5 minutes ago</span>
  <button class="refresh-btn">Refresh</button>
</div>
```

**Stale data guidelines:**
- Show "last updated" timestamp for cached data
- Provide manual refresh option
- Auto-refresh when connection restores
- Differentiate between "cached" and "live" data visually
- Never silently show outdated data as if it were current

### Offline-Capable Actions

| Action Type | Offline Behavior |
|-------------|-----------------|
| Read cached data | Show with "offline" indicator |
| Create new items | Queue locally, sync when online |
| Edit existing items | Queue changes, show "pending sync" |
| Delete items | Mark as "pending delete", hide from view |
| Search | Search local cache only, note limitation |

### Sync Status Indicators

```
┌──────────────────────────────────────────┐
│ ✓ All changes saved                      │  — Everything synced
│ ⟳ Saving...                              │  — Sync in progress
│ ⚠ Offline — changes will sync later      │  — Queued changes
│ ✕ Save failed — click to retry           │  — Error state
└──────────────────────────────────────────┘
```

---

## Prefetching & Preloading

### Link Prefetching

```html
<!-- Prefetch likely next pages -->
<link rel="prefetch" href="/dashboard">
<link rel="prefetch" href="/api/user-data.json">

<!-- Preload critical resources -->
<link rel="preload" href="/fonts/main.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/hero.jpg" as="image">
```

### Hover Prefetch

```javascript
// Prefetch on hover (before click)
document.querySelectorAll('a[data-prefetch]').forEach(link => {
  let prefetched = false;

  link.addEventListener('mouseenter', () => {
    if (prefetched) return;
    prefetched = true;

    const prefetchLink = document.createElement('link');
    prefetchLink.rel = 'prefetch';
    prefetchLink.href = link.href;
    document.head.appendChild(prefetchLink);
  });
});
```

### Prefetch Strategy Decision

| Signal | Action |
|--------|--------|
| User hovers over link | Prefetch page |
| User types in search | Prefetch top results |
| User reaches 80% of list | Prefetch next page |
| User is on step 2 of 4 | Prefetch step 3 resources |
| Viewport approaches lazy content | Prefetch images |

---

## Key Metrics

| Metric | Value | Context |
|--------|-------|---------|
| Instant response | < 100ms | No loading indicator needed |
| Skeleton threshold | > 300ms | Show skeleton after this delay |
| Toast error display | >= 5s | Longer than success toasts |
| CLS target | < 0.1 | Core Web Vitals "good" |
| LCP target | < 2.5s | Largest Contentful Paint |
| FID target | < 100ms | First Input Delay |
| INP target | < 200ms | Interaction to Next Paint |
| Optimistic rollback | < 5s | Show error if no confirmation |
| Prefetch hover delay | 65ms | Wait before prefetching |

---

## Anti-Patterns

1. **Spinner for everything** - Use skeletons for content, spinners for actions
2. **Full-page loader** - Block only the region that's loading, not the whole page
3. **No minimum display time** - Skeleton that flashes for 50ms is worse than nothing
4. **Layout shifts on load** - Always reserve space for async content
5. **Silent failures** - User doesn't know their action failed
6. **Optimistic without rollback** - Showing success then silently losing data
7. **Blocking UI during save** - Use background save with status indicator
8. **No offline indication** - Users assume they're connected
9. **Stale data shown as current** - Always indicate data freshness
10. **Retry without feedback** - Show what's happening during retry attempts

---

## Sources

- [web.dev - Core Web Vitals](https://web.dev/vitals/) - Google's performance metrics
- [web.dev - Optimize CLS](https://web.dev/optimize-cls/) - Layout shift prevention
- [Nielsen Norman Group - Response Times](https://www.nngroup.com/articles/response-times-3-important-limits/) - Perception thresholds
- [Smashing Magazine - Skeleton Screens](https://www.smashingmagazine.com/2020/04/skeleton-screens-react/) - Implementation patterns
- [Luke Wroblewski - Mobile Input](https://www.lukew.com/ff/entry.asp?1950) - Perceived performance research
- [Instant.page](https://instant.page/) - Prefetch on hover library
