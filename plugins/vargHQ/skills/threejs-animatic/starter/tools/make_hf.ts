// Builds hf/: a HyperFrames composition that renders the same film (same js/ modules, approved edits baked in).
// HyperFrames seeks a paused timeline frame by frame and fires `hf-seek`; we render exactly that time.
// Use it when the animatic itself is the deliverable, or to lay HTML text, captions or a logo over it.
//   bun tools/make_hf.ts
//   npx hyperframes lint hf && npx hyperframes render hf -o renders/animatic_hf.mp4
import { mkdir, copyFile, readdir } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { join } from 'node:path';
import { FILM } from '../js/config.js';

const ROOT = join(import.meta.dir, '..'), HF = join(ROOT, 'hf');
const THREE_URL = 'https://cdn.jsdelivr.net/npm/three@0.181.2/build/three.module.js'; // same pin as index.html
const { width: W, height: H } = FILM.export;
await mkdir(join(HF, 'js'), { recursive: true });
for (const f of await readdir(join(ROOT, 'js'))) if (f.endsWith('.js') && f !== 'main.js') await copyFile(join(ROOT, 'js', f), join(HF, 'js', f));
const editsPath = join(ROOT, 'data', 'edits.json');
const edits = existsSync(editsPath) ? await Bun.file(editsPath).text() : '{}';
await Bun.write(join(HF, 'js', 'edits.js'), `// baked from data/edits.json by tools/make_hf.ts\nexport default ${edits.trim()};\n`);

let audio = '';
if (FILM.audio && existsSync(join(ROOT, FILM.audio))) {
  await mkdir(join(HF, 'assets'), { recursive: true });
  const name = FILM.audio.split('/').pop();
  await copyFile(join(ROOT, FILM.audio), join(HF, 'assets', name!));
  audio = `\n  <audio id="music" class="clip" data-start="0" data-duration="${FILM.duration}" data-track-index="2" src="assets/${name}"></audio>`;
}

await Bun.write(join(HF, 'index.html'), `<!doctype html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=${W}, height=${H}" />
<script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
<script type="importmap">{ "imports": { "three": "${THREE_URL}" } }</script>
<style>
  html, body { margin: 0; width: ${W}px; height: ${H}px; overflow: hidden; background: #000; }
  #root { position: relative; width: 100%; height: 100%; overflow: hidden; background: #000; }
  #gl { position: absolute; inset: 0; width: 100%; height: 100%; display: block; }
</style>
</head>
<body>
<!-- data-duration is required: the three adapter cannot infer a length from the scene -->
<div id="root" data-composition-id="main" data-start="0" data-duration="${FILM.duration}" data-width="${W}" data-height="${H}">
  <canvas id="gl" width="${W}" height="${H}" data-layout-allow-overflow></canvas>${audio}
</div>
<script>
  window.__timelines = window.__timelines || {};
  window.__timelines["main"] = gsap.timeline({ paused: true });
</script>
<script type="module">
  import { createFilm, createVideoRenderer } from './js/film.js';
  import edits from './js/edits.js';
  const film = createFilm(edits);
  const renderer = createVideoRenderer(document.getElementById('gl'), ${W}, ${H});
  film.setLabels(false);
  film.camera.aspect = ${W} / ${H};
  film.camera.updateProjectionMatrix();
  // every frame is a pure function of the HyperFrames time: no rAF, no clock
  function renderAt(t) { film.pose(t); renderer.render(film.set.scene, film.camera); }
  window.addEventListener('hf-seek', e => renderAt(e.detail.time));
  renderAt(window.__hfThreeTime || 0);
</script>
</body>
</html>
`);
await Bun.write(join(HF, 'hyperframes.json'), JSON.stringify({ $schema: 'https://hyperframes.heygen.com/schema/hyperframes.json', paths: { assets: 'assets' } }, null, 2) + '\n');
console.log(`hf/ ready (${W}x${H}, ${FILM.duration} s). Next: npx hyperframes lint hf && npx hyperframes render hf -o renders/animatic_hf.mp4`);
