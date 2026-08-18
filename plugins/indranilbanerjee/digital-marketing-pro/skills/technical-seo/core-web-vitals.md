# Core Web Vitals — Optimization Reference

A comprehensive guide to measuring, diagnosing, and fixing Core Web Vitals issues. These three metrics (LCP, INP, CLS) are Google's primary user experience signals and directly affect search rankings, ad Quality Score, and conversion rates.

---

## Thresholds Summary

| Metric | Good | Needs Improvement | Poor |
|---|---|---|---|
| **LCP** (Largest Contentful Paint) | < 2.5s | 2.5s – 4.0s | > 4.0s |
| **INP** (Interaction to Next Paint) | < 200ms | 200ms – 500ms | > 500ms |
| **CLS** (Cumulative Layout Shift) | < 0.1 | 0.1 – 0.25 | > 0.25 |

Google uses the 75th percentile of page loads (p75) from the Chrome UX Report (CrUX) for ranking signals. Optimizing for the median is not enough — you must bring the 75th percentile into the "good" range.

---

## LCP — Largest Contentful Paint

### What It Measures

The render time of the largest visible content element in the viewport. LCP elements are typically:
- `<img>` elements (most common LCP element on the web)
- `<video>` poster images
- Elements with CSS `background-image`
- Block-level text elements (`<h1>`, `<p>`, etc.)

### Common Causes of Poor LCP

**1. Slow Server Response Time (TTFB > 800ms)**
- The browser cannot start rendering until it receives the first byte of HTML
- Target TTFB: < 800ms for the document request
- Causes: Unoptimized database queries, no server-side caching, no CDN, under-provisioned hosting, application-level bottlenecks

**Fix strategies:**
- Implement a CDN for static assets and HTML (Cloudflare, Fastly, CloudFront)
- Enable server-side caching (Redis, Memcached, Varnish, full-page cache)
- Optimize database queries (indexing, query optimization, connection pooling)
- Use HTTP/2 or HTTP/3 for multiplexed connections
- Consider edge computing (Cloudflare Workers, Vercel Edge Functions) to reduce latency
- Upgrade hosting if consistently over capacity

**2. Render-Blocking Resources**
- CSS and synchronous JavaScript in the `<head>` block rendering until they download and execute
- Every additional blocking resource adds to LCP

**Fix strategies:**
- Inline critical CSS (the CSS needed for above-the-fold content) directly in the `<head>`
- Defer non-critical CSS with `media="print" onload="this.media='all'"` or load asynchronously
- Add `defer` or `async` attribute to non-critical `<script>` tags
- Remove unused CSS (PurgeCSS, Coverage tab in Chrome DevTools)
- Remove unused JavaScript (tree-shaking, code splitting)
- Minimize CSS/JS file count through bundling (but balance against cache granularity)

**3. Slow Resource Load Times (LCP Element)**
- Large, unoptimized images are the most common LCP bottleneck
- LCP image is discovered late in the loading waterfall (e.g., loaded via CSS or JavaScript)

**Fix strategies:**
- **Preload the LCP image**: `<link rel="preload" as="image" href="hero.webp">` — this is the single highest-impact LCP fix for image-based LCP elements
- **Use modern image formats**: WebP (25-35% smaller than JPEG), AVIF (50% smaller than JPEG). Serve with `<picture>` element for fallback support
- **Responsive images**: Use `srcset` and `sizes` attributes so browsers download the appropriately sized image for the viewport
- **Compress images**: Target quality 75-85 for JPEG/WebP (visually lossless for most content)
- **Set explicit width and height** on `<img>` elements (prevents layout shift AND helps browser allocate space early)
- **Do NOT lazy-load the LCP image**: `loading="lazy"` on the LCP element delays it. Only lazy-load below-the-fold images
- **Set fetchpriority="high"** on the LCP image element to prioritize its download
- **Avoid CSS background-image for LCP**: The browser cannot discover CSS background images until the CSS file is parsed. Use `<img>` with preload instead

**4. Client-Side Rendering**
- SPAs that render content with JavaScript delay LCP until JS is downloaded, parsed, and executed
- The browser sees an empty or skeleton page until JavaScript hydrates

**Fix strategies:**
- Implement Server-Side Rendering (SSR) for above-the-fold content
- Use Static Site Generation (SSG) for pages that do not change frequently
- Implement Incremental Static Regeneration (ISR) for dynamic content with SSG benefits
- If SSR is not feasible, use prerendering or document-level critical HTML injection

### LCP Optimization Priority Checklist

1. Identify the LCP element (Chrome DevTools > Performance panel > Timings > LCP)
2. Check TTFB (target < 800ms) — if high, fix server/CDN first
3. Check if LCP image is preloaded — if not, add preload link
4. Check image format and compression — convert to WebP/AVIF
5. Check for render-blocking CSS/JS — defer or inline critical
6. Check if LCP element requires JavaScript to render — implement SSR if so
7. Verify `fetchpriority="high"` is set on LCP image
8. Verify `loading="lazy"` is NOT set on LCP image

---

## INP — Interaction to Next Paint

### What It Measures

INP measures the latency of all user interactions (clicks, taps, keyboard inputs) throughout the page lifecycle and reports the worst interaction (with outliers excluded). It replaced FID (First Input Delay) as a Core Web Vital in March 2024.

Key difference from FID: FID only measured the delay of the first interaction. INP measures ALL interactions and reports the worst one, making it a much more comprehensive responsiveness metric.

### Common Causes of Poor INP

**1. Long Tasks on the Main Thread**
- Any JavaScript task longer than 50ms blocks the main thread and delays interaction response
- Common offenders: large framework initialization, complex DOM manipulation, synchronous API calls, heavy computation

**Fix strategies:**
- **Break long tasks**: Use `setTimeout(fn, 0)`, `requestAnimationFrame`, or `scheduler.yield()` to break work into smaller chunks (< 50ms each)
- **Use web workers**: Offload heavy computation (data processing, parsing, calculations) to web workers so they do not block the main thread
- **Defer non-critical initialization**: Lazy-load components and initialize them on user interaction rather than on page load
- **Code-split aggressively**: Only load the JavaScript needed for the current view. Use dynamic `import()` for below-the-fold and interaction-triggered features

**2. Expensive Event Handlers**
- Click, input, and keydown handlers that perform heavy DOM manipulation, state recalculation, or synchronous layout queries
- React/Angular/Vue re-renders triggered by state changes during interaction

**Fix strategies:**
- **Debounce and throttle**: For scroll, resize, and input handlers, debounce (wait for pause) or throttle (limit frequency)
- **Minimize DOM reads/writes in handlers**: Batch DOM mutations, avoid forced synchronous layout (reading offsetHeight after a write)
- **Use CSS for visual feedback**: CSS transitions and animations run on the compositor thread, not the main thread. Use CSS for hover states, button press feedback, and simple animations
- **Virtualize long lists**: Do not render 10,000 DOM nodes. Use virtual scrolling (react-virtualized, vue-virtual-scroller) to render only visible items
- **Optimize React re-renders**: Use `React.memo`, `useMemo`, `useCallback` to prevent unnecessary re-renders. Use `useTransition` for non-urgent state updates

**3. Large DOM Size**
- Pages with > 1,500 DOM elements are at risk; > 3,000 is a red flag
- Large DOM increases memory usage and slows style recalculation, layout, and paint operations

**Fix strategies:**
- Reduce DOM nodes by simplifying layout (fewer nested containers)
- Use CSS Grid/Flexbox instead of deeply nested `<div>` structures
- Virtualize long lists and tables
- Lazy-render offscreen content
- Remove hidden elements from the DOM instead of using `display: none` on thousands of nodes

**4. Third-Party Script Impact**
- Tag managers, analytics, chat widgets, A/B testing tools, and ad scripts all compete for main thread time
- Third-party scripts are the most common source of long tasks on content-heavy sites

**Fix strategies:**
- Audit all third-party scripts with Chrome DevTools Performance panel (filter by domain)
- Load non-essential third-party scripts with `defer` or `async`
- Delay chat widgets and feedback tools until user interaction or scroll event
- Use `requestIdleCallback` for non-urgent analytics calls
- Consider Partytown or similar libraries to offload third-party scripts to web workers
- Regularly audit tag manager containers and remove unused tags

### INP Diagnosis Workflow

1. Open Chrome DevTools > Performance panel > Record a session with real interactions
2. Look for long tasks (red-flagged bars > 50ms in the main thread)
3. Identify which script/function is responsible (call stack in the task detail)
4. Check the "Interactions" track to see which user interactions had high latency
5. Use the Web Vitals Chrome extension to get real-time INP readings per interaction
6. Cross-reference with CrUX data to see field INP at the p75 level

---

## CLS — Cumulative Layout Shift

### What It Measures

CLS quantifies how much visible content shifts during the page lifecycle. Each layout shift is scored by multiplying the impact fraction (percentage of viewport affected) by the distance fraction (how far elements moved). CLS is the sum of all unexpected layout shift scores, grouped into session windows of maximum 5 seconds with 1-second gaps.

A CLS of 0.1 means the equivalent of 10% of the viewport shifting by 10% of the viewport height.

### Common Causes of Poor CLS

**1. Images and Iframes Without Explicit Dimensions**
- When the browser does not know an image's dimensions in advance, it allocates zero space, then shifts content when the image loads

**Fix strategies:**
- Always set `width` and `height` attributes on `<img>` and `<iframe>` elements
- Use CSS `aspect-ratio` property for responsive images: `aspect-ratio: 16 / 9`
- For responsive images with `srcset`, the `width` and `height` attributes still help the browser calculate aspect ratio before download

**2. Dynamically Injected Content**
- Banners, cookie consent bars, newsletter pop-ins, or promotional bars inserted above existing content push everything down

**Fix strategies:**
- Reserve space for dynamic content with CSS `min-height` on container elements
- Insert dynamic content below the fold when possible
- Use CSS `transform` animations instead of changing `top`, `margin`, or `height` (transforms do not cause layout shifts)
- For cookie banners and notification bars, use fixed/sticky positioning so they overlay rather than push content
- Avoid inserting content above existing content unless in response to a user interaction (user-initiated shifts are excluded from CLS)

**3. Web Fonts Causing Layout Shift (FOUT/FOIT)**
- When a web font loads and replaces a fallback font, text reflows if the fonts have different metrics (line height, letter spacing, word width)

**Fix strategies:**
- Use `font-display: optional` — the best option for CLS; if the font is not already cached, the fallback is used for the entire page visit, and the web font is cached for next visit
- Use `font-display: swap` with font metric overrides (`ascent-override`, `descent-override`, `line-gap-override`, `size-adjust` on the `@font-face` of the fallback font) to match fallback metrics to web font metrics
- Preload critical fonts: `<link rel="preload" as="font" type="font/woff2" href="font.woff2" crossorigin>`
- Subset fonts to include only needed characters (Latin, Latin Extended) using tools like glyphhanger or fonttools
- Self-host fonts instead of using Google Fonts CDN (eliminates the extra DNS lookup and connection)

**4. Ads and Embeds Without Reserved Space**
- Ad slots that resize after loading or load asynchronously without placeholder space
- Third-party embeds (YouTube, Twitter, maps) that load with unknown dimensions

**Fix strategies:**
- Set fixed `min-height` on ad containers based on the most common ad size for that slot
- Use CSS `aspect-ratio` or explicit dimensions for embed containers
- For responsive ad slots, set the minimum size and allow growth only downward (below the ad)
- Load ads below the fold where possible
- Consider static/reserved ad slots rather than dynamic ad insertion

**5. Late-Loading CSS or JavaScript Causing Reflow**
- CSS files loaded after initial render can change layout
- JavaScript that modifies element sizes, positions, or visibility after page load

**Fix strategies:**
- Inline critical CSS to ensure above-the-fold layout is stable from first paint
- Load non-critical CSS asynchronously but ensure it does not affect above-the-fold layout
- Avoid JavaScript that modifies layout properties on visible elements after load
- Use CSS `contain: layout` on components that should not affect siblings when they change

### CLS Debugging Workflow

1. Open Chrome DevTools > Performance panel > Record page load
2. Check the "Layout Shifts" track for blue markers
3. Click each shift to see which elements moved, shift score, and whether it was user-initiated
4. Use the Layout Shift Regions feature (Chrome DevTools > Rendering > Layout Shift Regions) for a visual overlay of shifting elements during real browsing
5. Check field CLS in CrUX data — lab data often underestimates CLS because automated tools do not scroll or interact with the page

---

## Measurement: Field Data vs Lab Data

### Field Data (Real User Monitoring)

- **Chrome UX Report (CrUX)**: The dataset Google uses for ranking signals. Aggregated from opted-in Chrome users. Available via PageSpeed Insights, CrUX API, BigQuery, and GSC Core Web Vitals report
- **Real User Monitoring (RUM)**: Custom instrumentation using the `web-vitals` JavaScript library. Provides per-page, per-segment, per-geography breakdowns
- **Google Search Console CWV report**: Aggregates CrUX data at the URL group level. Shows good/needs improvement/poor distribution

**Field data is what Google uses for ranking.** Lab data is for diagnosis only.

### Lab Data (Synthetic Testing)

- **Lighthouse** (Chrome DevTools, PageSpeed Insights, CI/CD): Simulated page load on a throttled connection. Good for diagnosis, not representative of real user experience
- **WebPageTest**: Advanced synthetic testing with real browsers, real network conditions, and filmstrip/waterfall views. Best lab tool for deep performance analysis
- **Chrome DevTools Performance panel**: Real-time recording on your local machine. Not throttled by default — enable CPU and network throttling for realistic results

### Common Discrepancies Between Field and Lab

| Scenario | Lab Shows | Field Shows | Explanation |
|---|---|---|---|
| CLS from scrolling | Low CLS | High CLS | Lab tools only measure load CLS; field captures all user-session shifts |
| INP from real interactions | Not measurable | Poor INP | Lab tools cannot simulate diverse real user interactions |
| LCP on slow networks | Good LCP (fast local network) | Poor LCP | Field includes users on 3G, 4G, and congested networks |
| Third-party script impact | Minimal | Significant | Lab may not load all third-party scripts (ad blockers, consent managers blocking tags) |
| Geographic latency | Low TTFB | High TTFB | Lab tests from one location; field includes users far from servers |

Always prioritize field data for decision-making. Use lab data to diagnose specific issues identified in field data.

---

## Optimization Priority Framework

When multiple CWV metrics need improvement, prioritize using this framework:

### Priority 1: Metric in "Poor" Range
Any metric in the poor range (LCP > 4s, INP > 500ms, CLS > 0.25) should be addressed first. Poor CWV can directly suppress rankings.

### Priority 2: LCP
LCP is the most impactful CWV for user experience and is often the easiest to improve with targeted fixes (image preload, CDN, format optimization). A 1-second LCP improvement can increase conversions by 2-5%.

### Priority 3: CLS
CLS fixes are typically low-effort (adding image dimensions, reserving ad space, font-display settings) with immediate impact. CLS is also the most noticeable metric to users — layout shift is visually jarring and erodes trust.

### Priority 4: INP
INP is often the hardest to fix because it requires JavaScript refactoring, framework-level changes, or third-party script auditing. Improvements may require development sprints rather than quick configuration changes.

### Cross-Metric Quick Wins

| Fix | LCP Impact | INP Impact | CLS Impact | Effort |
|---|---|---|---|---|
| Preload LCP image | High | None | None | 5 minutes |
| Add image dimensions | None | None | High | 30 minutes |
| Convert images to WebP/AVIF | Medium | None | None | 1-2 hours |
| Inline critical CSS | Medium | Low | Low | 2-4 hours |
| Defer third-party scripts | Low | High | Medium | 1-2 hours |
| Implement CDN | High | None | None | 2-4 hours |
| font-display: optional | None | None | High | 15 minutes |
| Code-split JavaScript | Low | High | None | 1-2 days |
| SSR for above-fold content | High | Medium | Low | 1-2 weeks |

---

## Tools Reference

| Tool | Best For | Cost |
|---|---|---|
| PageSpeed Insights | Quick CWV check with field + lab data | Free |
| Google Search Console CWV Report | Site-wide CWV status and URL grouping | Free |
| Chrome DevTools Performance Panel | Deep diagnosis of specific pages | Free |
| WebPageTest | Advanced waterfall analysis and filmstrip comparison | Free (public) / Paid (private) |
| CrUX API | Programmatic access to field data | Free |
| CrUX BigQuery Dataset | Large-scale CWV analysis across sites | Free (BigQuery free tier) |
| `web-vitals` JS Library | Real user monitoring instrumentation | Free (open source) |
| Lighthouse CI | Automated CWV regression testing in CI/CD | Free (open source) |
| Chrome Web Vitals Extension | Real-time CWV overlay during browsing | Free |
| DebugBear | Continuous CWV monitoring with alerts | Paid |
| SpeedCurve | Performance monitoring with CWV trends | Paid |
| Calibre | Automated performance budgets and alerts | Paid |
