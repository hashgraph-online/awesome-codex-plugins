# Three.js inside HyperFrames

**Offline by design.** The template loads `vendor/gsap.min.js` and `vendor/three.module.js`. After copying it into a project, run `bash <skill>/scripts/vendor_libs.sh <project> --three` once, so every render uses the same pinned copies and never fetches from a CDN.

Three.js draws 3D with WebGL. On its own it animates with a render loop that runs in real time, which a frame-by-frame renderer cannot capture reliably. The fix is to make the 3D scene a pure function of time: GSAP owns the clock, and every time HyperFrames seeks the timeline, one `draw(t)` call positions everything for second `t` and renders once.

Start from `templates/threejs/index.html`. It renders as is (10 s, a low-poly shape, a slow camera dolly, seeded stars, an HTML title on top).

## The pattern

```js
import * as THREE from "three";   // via an import map pinned to one version

const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(1);              // the canvas is already 1920x1080
renderer.setSize(1920, 1080, false);

function draw(t) {                      // t in seconds: the ONLY place that decides the frame
  camera.position.set(/* from t */);
  camera.lookAt(0, 0, 0);
  subject.rotation.y = t * 0.5;
  renderer.render(scene, camera);
}

const clock = { t: 0 };
const tl = gsap.timeline({ paused: true });
tl.to(clock, { t: DURATION, duration: DURATION, ease: "none", onUpdate: () => draw(clock.t) }, 0);
window.__timelines = window.__timelines || {};
window.__timelines["main"] = tl;
draw(0);
```

Rules:

- No `renderer.setAnimationLoop`, no `requestAnimationFrame`, no `THREE.Clock`. Time comes only from `t`.
- Compute positions from `t` directly (`x = 4 * Math.sin(t * 0.8)`), or keep GSAP tweens on plain objects and read their values in `draw`. Both are seek-safe.
- Random layouts use a seeded generator (the template includes `mulberry32`). Same seed, same stars, every render.
- `preserveDrawingBuffer: true` so the captured frame is the finished frame.
- Pin the Three.js version in the import map (the template uses 0.170.0). Do not use `latest`.

## Text and 3D together

Put headlines in HTML on top of the canvas, animated by the same GSAP timeline. HTML text is sharper than text inside WebGL and easier to check. Use 3D text (`TextGeometry`) only when the brief wants letters with depth that the camera moves around.

## Making it look designed

- **Light:** one hemisphere light for the base and one strong directional key from above and to the side. Add a rim light behind the subject in a warm or saturated colour from the palette to separate it from the background.
- **Material:** `MeshStandardMaterial` with `flatShading: true` reads as clean low-poly; `roughness` 0.3-0.6 for most surfaces.
- **Camera:** one motivated move per shot (a dolly in, an orbit, a crane up). Ease it. A camera that drifts randomly reads as unfinished.
- **Depth:** fog in the background colour (`scene.fog = new THREE.Fog(color, near, far)`) and a few thousand small points give scale cheaply.
- **Instancing:** for hundreds of the same object use `InstancedMesh` and set each matrix in `draw(t)`.

## Performance

HyperFrames uses the machine's GPU for WebGL when it can (`--browser-gpu` forces it; `--no-browser-gpu` forces software rendering, which is slow but works on any machine). A 10-second 1080p scene with a few thousand objects renders in well under a minute on a recent laptop. If a render crawls, cut shadow-map size, polygon count or post effects before anything else.

## Checks that catch 3D bugs

- Snapshot the first frame, the middle and the last: the subject must be in frame and lit in all three.
- Black frames usually mean the camera is inside an object or looking away. Print the camera position at those times.
- A flat, grey look usually means the lights are too weak for `MeshStandardMaterial`: raise the key light intensity.
