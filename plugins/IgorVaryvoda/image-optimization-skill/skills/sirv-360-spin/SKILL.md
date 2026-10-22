---
name: sirv-360-spin
description: Create and embed Sirv 360 spins - interactive rotating product views. Use when creating a 360 spin, shooting or preparing spin frames, naming spin image sequences, configuring .spin files, embedding spins with Sirv, tuning spin options (autospin, zoom, hint, speed), building 3D multi-row spins, adding spin hotspots, converting video to spin or spin to video, or debugging a spin that won't rotate or generates wrongly. Triggers on 360 spin, product spin, 360 product photography, spin viewer, or rotating product view.
---

# Sirv 360 Spin

A 360 spin is a sequence of frames (product rotated in steps) that Sirv assembles into an interactive drag-to-rotate viewer. Spins are Sirv's flagship media type: lighter and more engaging than video for rotating products.

## Official Sources First

Check current Sirv docs before changing naming rules, option names, or defaults:

- `https://sirv.com/help/articles/how-spin-files-are-created/`
- `https://sirv.com/help/articles/sirv-spin/`
- `https://sirv.com/help/articles/images-for-a-360-spin/`
- `https://sirv.com/help/articles/hotspots-on-360-spin/`
- `https://sirv.com/help/articles/convert-video-to-spin/`

## Default Workflow

1. Decide the source: photographed frame sequence, rendered frames, or an existing rotating video (convert with `video2spin`).
2. Choose frame count: 24-36 frames for smooth rotation at reasonable weight (36 is the usual sweet spot; 72+ glides but doubles weight; minimum 8, maximum 1000).
3. Name files so Sirv auto-generates the `.spin`: one folder per product spin, filenames with ascending numbers.
4. Upload to Sirv - the `.spin` file is created automatically; verify frame order and start frame.
5. Embed with Sirv JS + `class="Sirv"` markup; configure behavior via `data-options` or the `.spin` file.
6. Verify: drag rotation, zoom, mobile swipe vs page scroll, load performance, and CLS.

## Naming Conventions (what makes auto-generation work)

- **Single-row spin (rotate around one axis):** one ascending number sequence: `chair-01.jpg` ... `chair-36.jpg`.
- **Multi-row 3D spin (multiple camera heights):** two number sequences - Sirv reads the **first as row, second as column**: `chair-r01-c01.jpg`, `chair-r01-c02.jpg`, ... `chair-r03-c36.jpg`. The `r`/`c` (and `s` for spin number) prefixes are best practice for clarity.
- The `.spin` filename comes from the folder name (one spin per folder) or the common filename stem (digits stripped).
- 8-1000 images per spin. Keep one spin per folder for predictable naming.

Source frames: shoot/render at 2500-4000px wide. Sirv resizes and compresses delivery automatically (aggressive ~60% quality for retina), so keep masters high quality.

## Embedding

```html
<link rel="preconnect" href="https://youraccount.sirv.com" crossorigin>
<link rel="dns-prefetch" href="https://scripts.sirv.com">
<script src="https://scripts.sirv.com/sirvjs/v3/sirv.js"></script>

<div class="Sirv" data-src="https://youraccount.sirv.com/products/chair/chair.spin"></div>
```

Inside a product gallery, add the `.spin` as one `data-src` item among images/videos - see `../sirv-media-viewer/SKILL.md` for gallery composition, thumbnails, and fullscreen.

## Key Options

Set via `data-options`, the `.spin` file (JSON - also holds image list and hotspots), profiles, or `SirvOptions`:

| Option | Default | Purpose |
| --- | --- | --- |
| `spin` | `drag` | Interaction: `drag` or `hover` |
| `speed` | 50 | Drag sensitivity (0-100) |
| `autospin` | - | `once`, `twice`, `infinite`, or off |
| `autospinSpeed` | 3600 | ms per full rotation |
| `autospinDirection` | - | `clockwise`, `anticlockwise`, `alternate` |
| `autospinStart` | - | `load`, `hover`, `click` (combinable) |
| `hint` / `hintText` / `mobileHintText` | true / "Drag to spin" / "Swipe to spin" | Interaction hint |
| `zoom` | 2.5 | Click-to-zoom magnification (0 disables; activates when source exceeds display by 20%) |
| `fullscreen` | true | Fullscreen button |
| `startColumn` / `startRow` | - | Initial frame |
| `loopColumn` / `loopRow` | true / false | Wrap past the last frame on each axis |
| `spinOnAnyDrag` | false | Single-row spins: also react to vertical drags |

Mobile: keep `spinOnAnyDrag:false` (via `data-mobile-options="spinOnAnyDrag:false;"`) so vertical swipes still scroll the page.

## Video ↔ Spin Conversion

- **Video → spin:** UI (right-click video → Convert to spin) or API `POST /v2/files/video2spin`. Choose duration, JPEG (faster) or PNG (sharper), and frame count from 18/24/36/72/120/180/360. Video max 512MB; compress to under 300MB first when near the limit. Hourly API limits by plan (Free 0, Business 200, Enterprise 400).
- **Spin → video:** `POST /v2/files/spin2video` renders an MP4 for marketplaces/social that accept video but not embeds.
- API auth, job polling, and endpoint details: `../sirv-api/SKILL.md`.

## Red Flags

- Hand-building a drag-to-rotate widget when a `.spin` + Sirv JS does it in two lines.
- Filenames without a clean ascending sequence - frames assemble out of order or the `.spin` never generates.
- Two digit groups in single-row filenames (e.g. `2024-chair-01.jpg`) - Sirv reads the first digits as the row. Keep dates out of frame filenames.
- 100+ frames "for smoothness" on a product page - weight without benefit; 36 is usually enough.
- Low-res source frames (under ~1500px) - zoom becomes useless.
- Embedding a spin above the fold without reserving layout space (CLS) or preconnecting to the Sirv domain.
- Editing generated `.spin` JSON without checking current docs for valid settings/hotspot syntax.

## Verification

- The `.spin` URL loads in a browser and rotation follows drag direction in the right order (no jumps or reversals).
- First frame appears fast; preconnect hints present for above-fold spins; no CLS when the viewer initializes.
- Zoom activates and is sharp; fullscreen works; hint text shows once.
- Mobile: swipe rotates the spin, vertical swipe still scrolls the page.
- For multi-row spins: vertical drag changes rows as intended.
- For conversions: frame count and start frame match what was requested; spot-check frames for motion blur.
