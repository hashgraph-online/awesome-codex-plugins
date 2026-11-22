# Parallax 2.5D

Also called: 2.5d parallax, parallax scrolling, multiplane.

Family: Geometry, pixels and 3D. Cadence: smooth, full frame rate. Usual tool: HyperFrames (canvas or Three.js).

Four to six flat painted layers moving at different speeds as the camera pans: a sky, far mountains, hills, a row of trees, a field and grass in front, so that a flat scene feels deep. The demo is drawn in 2D, so it renders with no WebGL; the Three.js recipe below is how to build the real thing.

Parallax scrolling is a technique where background images move past the camera more slowly than foreground images, creating an illusion of depth in a 2D scene. It grew out of the multiplane camera used in traditional animation since the 1930s, which moved layers of artwork at different speeds and distances.

## What makes it read as this

- Layers, each one flat: sky, far mountains, hills, trees, field, foreground
- Each layer moves at its own speed: the nearer, the faster
- Distant layers are hazier and lighter; near layers darker and more saturated
- Layers repeat seamlessly as the camera pans
- A fixed or very slow sky and sun

## Timing

A steady pan to the right at about 90 px a second; speeds from 0.02 for the sun to 1.8 for the grass blades. Smooth, full frame rate.

## How to build it

- Three.js: flat `PlaneGeometry` layers with textured `MeshBasicMaterial` at different `z` depths and a `PerspectiveCamera` moving along x, or the same layers with an orthographic camera scaling each layer's x motion
- In the 2D demo: each layer is drawn in screen columns offset by `camera * speed`, wrapping with `Math.floor(offset / width)`, and ridges come from value noise of world x (`ridge()`)
- Add atmospheric haze by mixing far layers toward the sky colour
- Add a slight vertical bob to the camera

## Assets

All in code here. For real layers, paint each on a transparent PNG. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

Wind, birdsong, a gentle acoustic bed. Practice note.

## What makes it look wrong

- All layers moving at the same speed
- Visible seams where a layer repeats
- Detail in the far layers that competes with the foreground

## Tested demo

This is the look from `art-forms/looks-3d.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=parallax-2-5d` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  'parallax-2-5d': { kind: '2d', fps: null, draw(g, t, W, H) {
    // flat painted layers as the camera pans: a sky, far mountains, rolling hills, a row of pines, a field with flowers and a fence, and dark grass blades in front, each moving at its own speed
    const cam = t * 90, bob = Math.sin(t * 1.1) * 3, haze = (col, k) => rgba(mix(col, [255, 226, 180], k));
    const sky = g.createLinearGradient(0, 0, 0, 400); sky.addColorStop(0, '#6fb8f0'); sky.addColorStop(1, '#ffe7b0'); g.fillStyle = sky; g.fillRect(0, 0, W, H);
    const sx = 700 - ((cam * 0.02) % 1400), sunG = g.createRadialGradient(sx, 130, 10, sx, 130, 160); sunG.addColorStop(0, 'rgba(255,250,210,1)'); sunG.addColorStop(0.3, 'rgba(255,240,170,.6)'); sunG.addColorStop(1, 'rgba(255,230,160,0)'); g.fillStyle = sunG; g.fillRect(sx - 170, -40, 340, 340);
    const col = (speed, cw, fn) => { const off = cam * speed; for (let i = Math.floor(off / cw) - 1; i * cw - off < W + cw; i++) fn(i, i * cw - off, cw); };
    col(0.07, 320, (i, x) => { const y = 70 + hash(i, 1) * 90, w = 90 + hash(i, 2) * 70; g.fillStyle = 'rgba(255,255,255,.85)'; for (const [dx, dy, r] of [[0, 0, 28], [30, -10, 34], [66, 2, 26]]) { g.beginPath(); g.arc(x + dx + w * 0.2, y + dy, r, 0, TAU); g.fill(); } });
    const ridge = (speed, base, amp, scale, seed, colr, top) => { const off = cam * speed; g.beginPath(); g.moveTo(0, H); for (let x = 0; x <= W; x += 6) g.lineTo(x, base - amp * vnoise((x + off) / scale, 0, seed)); g.lineTo(W, H); g.closePath(); const gr = g.createLinearGradient(0, base - amp, 0, base + 60); gr.addColorStop(0, top); gr.addColorStop(1, colr); g.fillStyle = gr; g.fill(); };
    ridge(0.12, 330 + bob * 0.2, 170, 90, 3, haze([120, 140, 200], 0.35), haze([220, 230, 250], 0.2));   // far mountains
    ridge(0.28, 380 + bob * 0.5, 80, 160, 7, haze([84, 150, 90], 0.2), haze([140, 190, 110], 0.1));   // rolling hills
    col(0.55, 70, (i, x) => { const h = 70 + hash(i, 3) * 70, y = 408 + bob; if (hash(i, 4) < 0.2) return; g.fillStyle = '#2a5a34'; g.fillRect(x + 30, y - 10, 8, 16); for (let k = 0; k < 3; k++) { g.beginPath(); g.moveTo(x + 6 + k * 4, y - 6 - k * h * 0.28); g.lineTo(x + 34, y - 20 - h * (0.35 + k * 0.28)); g.lineTo(x + 62 - k * 4, y - 6 - k * h * 0.28); g.closePath(); g.fillStyle = k % 2 ? '#2f6b3a' : '#2a5a34'; g.fill(); } });
    g.fillStyle = '#5aa63e'; g.fillRect(0, 420 + bob, W, H); const grass = g.createLinearGradient(0, 420, 0, H); grass.addColorStop(0, '#6cba46'); grass.addColorStop(1, '#3f8a2e'); g.fillStyle = grass; g.fillRect(0, 420 + bob, W, H);
    col(1, 120, (i, x) => { g.fillStyle = '#e8d3a8'; g.fillRect(x, 452 + bob, 8, 46); g.fillRect(x + 40, 452 + bob, 8, 46); g.fillRect(x - 4, 462 + bob, 128, 7); g.fillRect(x - 4, 480 + bob, 128, 7); for (let k = 0; k < 2; k++) { const fx = x + 20 + hash(i, k) * 90, fy = 500 + hash(i, k + 5) * 30 + bob; g.fillStyle = '#f2f2e6'; for (let p = 0; p < 5; p++) { g.beginPath(); g.arc(fx + Math.cos(p * 1.26) * 6, fy + Math.sin(p * 1.26) * 6, 4, 0, TAU); g.fill(); } g.fillStyle = hash(i, k + 9) > 0.5 ? '#f5c518' : '#e24634'; g.beginPath(); g.arc(fx, fy, 3.4, 0, TAU); g.fill(); } });
    col(1.8, 26, (i, x) => { const h = 50 + hash(i, 7) * 60, sw = Math.sin(t * 2 + i) * 6; g.fillStyle = hash(i, 8) > 0.5 ? '#2a6a2a' : '#1f5420'; g.beginPath(); g.moveTo(x, H); g.quadraticCurveTo(x + 6 + sw * 0.5, H - h * 0.6, x + 12 + sw, H - h); g.quadraticCurveTo(x + 16, H - h * 0.5, x + 22, H); g.closePath(); g.fill(); });
    speckle(g, W, H, 7, 22, [255, 240, 200]);
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Parallax_scrolling>
- <https://en.wikipedia.org/wiki/Multiplane_camera>

Facts checked on 2026-11-21. Lines marked "practice note" are working advice, not sourced facts.
