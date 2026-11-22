# Point cloud and lidar scan

Also called: lidar scan, point cloud scan, 3d scan.

Family: Geometry, pixels and 3D. Cadence: smooth, full frame rate. Usual tool: Three.js inside HyperFrames.

An object or scene made of thousands of glowing points on black, in blue and gold, turning slowly, with points that fade and shrink as they recede. The demo is drawn in 2D, so it renders with no WebGL; the Three.js recipe below is how to build the real thing.

A point cloud is a discrete set of data points in space; each has X, Y and Z coordinates and may carry colour and other data. Point clouds are produced by 3D scanners or photogrammetry software. Lidar measures distance by timing the return of laser light, and is used to make high-resolution maps.

## What makes it read as this

- Only points, no surfaces or lines
- Glowing points on black, in two hues: blue for the ground, gold for the object
- Depth: far points are smaller and dimmer
- Scan structure: rings or lines of points, and a pulse of brighter points sweeping over them
- A slow turn, a high camera, and a faint vignette

## Timing

A slow turn at the full frame rate; the cloud builds up over about 1.6 seconds and the scan pulse crosses the ground every 3 to 4 seconds.

## How to build it

- Three.js: `Points` with a `BufferGeometry`, `PointsMaterial` (`sizeAttenuation: true`, `vertexColors`, `AdditiveBlending`, `depthWrite: false`)
- Size by depth in a custom shader: `gl_PointSize = base / -mvPosition.z`
- Real data: load a PLY or PCD scan with the examples loaders
- Scan pulse: a uniform radius that brightens the points near it
- In the 2D demo: project each point with a turn, a tilt and a perspective factor, and draw it as a tiny square with `lighter` compositing (`plot()`)

## Assets

All in code here. Real scans come from a lidar device or a photogrammetry run. Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.

## Sound and pacing

A low synth pulse and a soft ping as the scan passes. Practice note.

## What makes it look wrong

- Joining the points with lines or surfaces
- Opaque, same-sized points: no depth
- Too few points: it reads as sparkle, not as an object

## Tested demo

This is the look from `art-forms/looks-3d.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. View it: open `art-forms/gallery.html?look=point-cloud` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of `art-forms/looks.js`. Take the technique, not the picture.

```js
  'point-cloud': { kind: '2d', fps: null, draw(g, t, W, H) {
    // a scan made of about six thousand glowing points on black: a gold knot over a blue ground that a pulse of light sweeps across, turning slowly, with points fading and shrinking as they recede
    g.fillStyle = '#04050a'; g.fillRect(0, 0, W, H); const vg = g.createRadialGradient(480, 280, 40, 480, 280, 520); vg.addColorStop(0, 'rgba(20,30,70,.5)'); vg.addColorStop(1, 'rgba(0,0,0,0)'); g.fillStyle = vg; g.fillRect(0, 0, W, H);
    const a = t * 0.35, tilt = 0.55, sweep = (t * 2.2) % 8, grow = easeOut(prog(t, 0, 1.6)); g.globalCompositeOperation = 'lighter';
    const plot = (p, col, boost) => {
      const [x, y, z] = turn(p, a, tilt), f = 640 / (640 - z * 60), sx = 480 + x * 78 * f, sy = 292 - y * 78 * f, zn = clamp((z + 5) / 10), al = clamp((0.2 + 0.8 * zn * zn) * boost), sz = (1.1 + 2.4 * zn) * (boost > 1 ? 1.4 : 1);
      g.fillStyle = rgba(col, al); g.fillRect(sx - sz / 2, sy - sz / 2, sz, sz);
    };
    for (let i = 0; i < 5200 * grow; i++) {   // a trefoil knot, thickened into a tube of points
      const u = (i / 5200) * TAU, r = 2 + Math.cos(3 * u), k = [r * Math.cos(2 * u) * 0.85 + (hash(i, 1) - 0.5) * 0.4, Math.sin(3 * u) * 0.85 + 0.2 + (hash(i, 2) - 0.5) * 0.4, r * Math.sin(2 * u) * 0.85 + (hash(i, 3) - 0.5) * 0.4];
      plot(k, mix([255, 196, 80], [255, 240, 190], clamp((k[1] + 1) / 2)), 1);
    }
    for (let i = 0; i < 5200 * grow; i++) {   // the ground, scanned in rings: a disc of points with low hills, and a bright ring where the pulse is passing
      const r = 0.6 + Math.floor(Math.sqrt(hash(i, 4)) * 30) * 0.2 + hash(i, 9) * 0.03, th = hash(i, 5) * TAU, hgt = -2.3 + 0.38 * Math.sin(r * 1.5 + th * 3) + 0.2 * Math.sin(th * 5 + r), near = Math.abs(r - sweep) < 0.28;
      plot([Math.cos(th) * r, hgt, Math.sin(th) * r], near ? [190, 230, 255] : mix([50, 110, 255], [120, 180, 255], clamp(1 - r / 7)), near ? 2.4 : 1.3);
    }
    for (let i = 0; i < 260; i++) { const th = hash(i, 6) * TAU, r = 3.5 + hash(i, 7) * 0.2, hh = hash(i, 8) * 2.6 - 2.3; plot([Math.cos(th) * r * 0.5 + 3.4, hh, Math.sin(th) * r * 0.5 - 2], [120, 190, 255], 1); }   // a thin tower
    g.globalCompositeOperation = 'source-over';
  } }
```

To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object's `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.

## Sources

- <https://en.wikipedia.org/wiki/Point_cloud>
- <https://en.wikipedia.org/wiki/Lidar>

Facts checked on 2026-11-21. Lines marked "practice note" are working advice, not sourced facts.
