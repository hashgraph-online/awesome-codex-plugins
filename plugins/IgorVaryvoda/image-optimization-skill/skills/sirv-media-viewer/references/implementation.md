# Sirv Media Viewer Implementation Reference

Use this reference when implementing, auditing, or debugging Sirv Media Viewer (SMV) markup and behavior.

## Official Docs Map

- Main viewer, usage, options, autostart, layouts, breakpoints, alt text, faster initialization: `https://docs.sirv.com/sirv-media-viewer`
- Responsive/lazy images and CLS placeholders: `https://docs.sirv.com/sirv-media-viewer/core-features/responsive-images`
- Smart `.view` galleries: `https://docs.sirv.com/sirv-media-viewer/core-features/smart-gallery`
- Accessibility and `a11y.*` labels: `https://docs.sirv.com/sirv-media-viewer/core-features/accessibility`
- Viewer API: `https://docs.sirv.com/sirv-media-viewer/advanced-implementation/api`
- Viewer events: `https://docs.sirv.com/sirv-media-viewer/advanced-implementation/events`
- CSP rules: `https://docs.sirv.com/sirv-media-viewer/advanced-implementation/content-security-policy-for-sirv`
- 3D models: `https://docs.sirv.com/sirv-media-viewer/media-types/3d-model`
- PDF galleries: `https://docs.sirv.com/sirv-media-viewer/media-types/show-pdf-as-zoomable-gallery`

## Script Loading

Basic load:

```html
<script src="https://scripts.sirv.com/sirvjs/v3/sirv.js"></script>
```

For important above-fold viewers, place Sirv JS early in the `<head>` so media requests can start sooner. Add resource hints:

```html
<link rel="preconnect" href="https://scripts.sirv.com" crossorigin>
<link rel="preconnect" href="https://account.sirv.com" crossorigin>
<link rel="dns-prefetch" href="https://scripts.sirv.com">
<link rel="dns-prefetch" href="https://account.sirv.com">
```

Sirv supports smaller `sirv.js` bundles using a `modules` parameter. Check the current docs before choosing module names; include every media type the viewer uses. For example, the 3D model docs show:

```html
<script src="https://scripts.sirv.com/sirvjs/v3/sirv.js?modules=model"></script>
```

## Markup Patterns

Explicit child items:

```html
<div class="Sirv">
  <div data-src="https://account.sirv.com/products/item.spin"></div>
  <div data-src="https://account.sirv.com/products/item-front.jpg" data-type="zoom"></div>
  <div data-src="https://account.sirv.com/products/item.mp4"></div>
</div>
```

Single-div gallery:

```html
<div class="Sirv" data-src="https://account.sirv.com/products/item.spin, https://account.sirv.com/products/item-front.jpg, https://account.sirv.com/products/item.mp4"></div>
```

Smart gallery from a folder:

```html
<div class="Sirv" data-src="https://account.sirv.com/products/item.view"></div>
```

3D model:

```html
<div class="Sirv">
  <div data-src="https://account.sirv.com/models/item.glb" data-options="preload:true; zoom:true"></div>
</div>
```

External video:

```html
<div class="Sirv">
  <div data-src="https://www.youtube.com/watch?v=VIDEO_ID"></div>
  <div data-src="https://player.vimeo.com/video/VIDEO_ID"></div>
</div>
```

## Options And Priority

Common viewer options:

- `autostart:visible|created|off`
- `threshold:200`
- `quality:80`
- `hdQuality:60`
- `itemsOrder:zoom, spin, video, model, image`
- `layout.type:slider|grid`
- `layout.aspectRatio:1/1`
- `layout.grid.columns:2`
- `thumbnails.enable:true|false`
- `thumbnails.position:bottom|top|left|right`
- `thumbnails.type:square|crop|auto|bullets|grid`
- `fullscreen.enable:true|false`

Apply options in the narrowest maintainable place:

```html
<div class="Sirv" data-options="fullscreen.enable:false; thumbnails.type:bullets">
  <div data-src="https://account.sirv.com/products/item.spin" data-options="inactivity:7000"></div>
  <div data-src="https://account.sirv.com/products/item.jpg" data-type="zoom" data-options="mode:right"></div>
  <div data-src="https://account.sirv.com/products/item.mp4" data-options="autoplay:false"></div>
</div>
```

For site defaults:

```html
<script>
var SirvOptions = {
  viewer: {
    quality: 85,
    hdQuality: 70,
    thumbnails: {
      position: "bottom"
    }
  }
};
</script>
```

Priority from lowest to highest:

1. Viewer `data-options`
2. Item `data-options`
3. Global breakpoints
4. Viewer `data-breakpoints`

## Performance Rules

- Above-fold/LCP viewer: place script early, use preconnect/DNS-prefetch, reserve space, and consider `autostart:created`.
- Below-fold viewer: keep default lazy behavior (`autostart:visible`) or tune `threshold`.
- Use SMV layout/aspect options or CSS to prevent CLS.
- Use Dynamic Imaging URLs/profiles for delivery sizing/quality; do not try to solve image transforms with viewer options.
- If only one module is needed, use a documented module-limited Sirv JS URL.
- Do not load every gallery asset eagerly unless the UX requires it.

## Accessibility

- Add `data-alt` to each meaningful item or verify Sirv file descriptions are populated.
- Spins use `role="img"` and `aria-label` from alt text; verify this in rendered DOM when accessibility matters.
- Customize `a11y.*` labels for product-specific or localized gallery language.
- Check keyboard/focus order for thumbnails, arrows, fullscreen, zoom, and embedded video/model controls.

## API And Events

Use the API for product configurators, custom controls, or analytics. Do not use it for simple static galleries.

```html
<script>
const viewer = Sirv.viewer.getInstance("#product-viewer");
viewer.next();
viewer.jump(2);
viewer.disableGroup("color-navy");

Sirv.on("viewer:ready", (instance) => {
  if (instance.id === "product-viewer") {
    // Wire analytics or custom controls here.
  }
});

document
  .querySelector("#product-viewer")
  .addEventListener("sirv:viewer:afterSlideIn", (event) => {
    console.log(event.detail);
  });
</script>
```

Relevant event families include `viewer:*`, `spin:*`, `zoom:*`, `video:*`, and `image:*`.

## CSP Checklist

Strict CSPs commonly need allowances for:

- `script-src`: `https://scripts.sirv.com`, `https://video.sirv.com`, and Sirv's documented inline/eval requirements.
- `style-src`: `https://scripts.sirv.com` and inline styles when required.
- `img-src`: the Sirv account/custom domain plus `data:`.
- `media-src`: `https://video.sirv.com`, `blob:`, `data:`.
- `connect-src`: Sirv account/custom domain, `https://video.sirv.com`, `https://stats.sirv.com`, and `blob:`.
- `frame-src`: Sirv account/custom domain for embeds.

Use the official CSP page as the source of truth before editing production policies.
