---
name: sirv-media-viewer
description: Sirv Media Viewer guidance. Use when building, auditing, or debugging Sirv product galleries, zoom viewers, 360 spins, videos, YouTube/Vimeo embeds, 3D models, PDF galleries, smart .view galleries, thumbnails, fullscreen/mobile behavior, SMV class="Sirv" markup, data-src/data-options/data-breakpoints, Sirv JS loading, viewer API/events, CSP, accessibility, or Core Web Vitals for Sirv interactive media.
---

# Sirv Media Viewer

Sirv Media Viewer (SMV) is the right path when the user needs interactive product media rather than just a transformed image URL. It handles galleries, thumbnails, zoom, spins, video, 3D models, smart galleries, fullscreen, lazy loading, and responsive behavior.

## Official Sources First

Check current Sirv docs before changing option names, module names, event/API calls, or CSP rules:

- `https://docs.sirv.com/sirv-media-viewer`
- `https://docs.sirv.com/sirv-media-viewer/core-features/responsive-images`
- `https://docs.sirv.com/sirv-media-viewer/core-features/smart-gallery`
- `https://docs.sirv.com/sirv-media-viewer/core-features/accessibility`
- `https://docs.sirv.com/sirv-media-viewer/advanced-implementation/api`
- `https://docs.sirv.com/sirv-media-viewer/advanced-implementation/events`
- `https://docs.sirv.com/sirv-media-viewer/advanced-implementation/content-security-policy-for-sirv`

Read [implementation.md](references/implementation.md) when writing or reviewing viewer markup, script loading, options, breakpoints, smart galleries, API/events, or CSP.

For creating the spin assets themselves (frame naming, .spin generation, spin options, video-to-spin), use `../sirv-360-spin/SKILL.md`; for video encoding/streaming strategy outside the viewer, `../video-optimization/SKILL.md`.

## Default Workflow

1. Identify the media set: zoomable images, static images, `.spin`, video, YouTube/Vimeo, `.glb`/`.gltf`, PDF gallery, or `.view` smart gallery.
2. Choose the viewer shape: single item, explicit child-item gallery, single-div comma-separated gallery, smart `.view` gallery, grid, or slider.
3. Load Sirv JS once, ideally in the document head for important above-fold viewers. Use a module-limited Sirv JS URL only after checking the current docs and required media modules.
4. Use SMV markup: a `class="Sirv"` container with child `div data-src` assets, or a single `div class="Sirv" data-src="...">`.
5. Put viewer behavior in `data-options`, `SirvOptions.viewer`, or `data-breakpoints`; put image transforms in Sirv Dynamic Imaging URLs/profiles.
6. For above-fold/LCP-relevant viewers, avoid default lazy delays by using `autostart:created`, preconnect to Sirv domains, and reserve stable layout space.
7. Provide meaningful `data-alt` or Sirv file descriptions. Keep ARIA labels intentional when customizing a11y prompts.
8. Verify in a real browser: first asset load, thumbnail navigation, fullscreen, zoom, spin drag, video/model controls, mobile behavior, keyboard/focus, network requests, LCP, and CLS.

## Core Patterns

### Mixed Product Gallery

```html
<link rel="preconnect" href="https://scripts.sirv.com" crossorigin>
<link rel="preconnect" href="https://account.sirv.com" crossorigin>
<script src="https://scripts.sirv.com/sirvjs/v3/sirv.js"></script>

<div class="Sirv" data-options="autostart:created; layout.aspectRatio:1/1; thumbnails.position:bottom">
  <div data-src="https://account.sirv.com/products/sku-123-front.jpg" data-type="zoom" data-alt="SKU 123 front view"></div>
  <div data-src="https://account.sirv.com/products/sku-123-side.jpg" data-type="zoom" data-alt="SKU 123 side view"></div>
  <div data-src="https://account.sirv.com/products/sku-123.spin" data-alt="SKU 123 360 spin"></div>
  <div data-src="https://account.sirv.com/products/sku-123-demo.mp4" data-options="autoplay:false" data-alt="SKU 123 demo video"></div>
</div>
```

### Smart Gallery

```html
<script src="https://scripts.sirv.com/sirvjs/v3/sirv.js"></script>
<div
  class="Sirv"
  data-src="https://account.sirv.com/products/sku-123.view"
  data-options="itemsOrder:spin, zoom, video, model, image; fullscreen.enable:true"
></div>
```

### Single-Div Gallery

```html
<div
  class="Sirv"
  data-src="https://account.sirv.com/products/sku-123.spin, https://account.sirv.com/products/sku-123-front.jpg, https://account.sirv.com/products/sku-123-demo.mp4"
  data-options="layout.type:slider; thumbnails.type:square"
></div>
```

## Option Boundaries

- `data-options` on the viewer controls all items unless item-level options override it.
- Item-level `data-options` should be used for one asset's zoom mode, video autoplay, spin hints, or model options.
- `SirvOptions.viewer` is useful for page/site defaults.
- `data-breakpoints` is for per-viewer responsive behavior and has higher priority than normal options.
- Use `SirvMobileOptions` or SMV breakpoints for mobile-specific quality/layout only when the behavior should diverge.

## Red Flags

- Hand-building a product gallery/zoom/spin slider when SMV should own the interaction.
- Adding `class="Sirv"`/`data-src` markup without the Sirv JS script.
- Loading the full Sirv JS bundle when a documented module-limited script would cover a narrow use case.
- Leaving an above-fold product viewer on default lazy loading when it is the LCP path.
- Not reserving viewer space, causing CLS while thumbnails or first media initialize.
- Missing `data-alt` and relying on unlabeled media unless Sirv file descriptions are verified.
- Mixing transform concerns into viewer options or gallery behavior into Dynamic Imaging URL params.
- Forgetting CSP allowances for `scripts.sirv.com`, the account/custom Sirv domain, `video.sirv.com`, `stats.sirv.com`, `blob:`, `data:`, and the inline/eval requirements documented by Sirv.

## Verification

- Sirv JS is loaded once and before the viewer needs to initialize.
- Every SMV `data-src` URL returns 200 and is the intended media type.
- The first visible viewer requests media early enough for LCP; lower-page viewers remain lazy.
- Viewer space is stable before media loads; CLS is not introduced.
- Thumbnails, arrows, fullscreen, zoom, spin, video, model, and smart gallery ordering work at desktop and mobile breakpoints.
- `data-alt` or Sirv file descriptions produce useful alt/ARIA output.
- API/event code uses documented calls such as `Sirv.getInstance(...)`, `Sirv.viewer.getInstance(...)`, `Sirv.on(...)`, or DOM `sirv:*` events.
- CSP is adjusted when a strict policy blocks scripts, images, media, stats, frames, blobs, or inline styles required by Sirv.
