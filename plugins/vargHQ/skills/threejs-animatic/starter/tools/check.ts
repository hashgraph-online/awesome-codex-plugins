// Headless check, run it after every change (server running):
//   bun tools/check.ts [--url http://localhost:8777/] [--out checks]
// 1. loads the review UI, screenshots it, prints each shot's automatic warnings
// 2. loads the clean export, renders START / middle / last frame before the cut of every shot
//    and a contact sheet (checks/sheet.png): look at it, do not guess
// 3. seek-safety: renders the same moments in a different order and compares the pixels
// Exits 1 on any page error or a seek-safety mismatch.
import { mkdir } from 'node:fs/promises';
import { join } from 'node:path';
import { launch, args } from './cdp.ts';
import { FILM } from '../js/config.js';

const o = args({ url: 'http://localhost:8777/', out: 'checks' });
const out = String(o.out);
await mkdir(out, { recursive: true });
let failed = false;

// 1 · review UI
let c = await launch({ width: 1440, height: 900 });
try {
  await c.goto(String(o.url), 'window.__ready === true && !!window.app');
  await Bun.sleep(800); // a few frames
  await c.screenshot(join(out, 'ui.png'));
  const warn = await c.evaluate('app.shots.map(s => ({ id: s.id, spec: app.describe(s), warn: app.check(s) }))');
  for (const s of warn) console.log(`${s.id}  ${s.spec.size} · ${s.spec.angle} · ${s.spec.lens} · ${s.spec.move}${s.warn.length ? '\n     ⚠ ' + s.warn.join('\n     ⚠ ') : ''}`);
  if (c.errors.length) { failed = true; console.error(`UI errors:\n  ${c.errors.join('\n  ')}`); }
  console.log(`ui -> ${out}/ui.png`);
} finally { await c.close(); }

// 2 · clean export frames + contact sheet
const { width: w, height: h } = FILM.export, fps = FILM.fps;
c = await launch({ width: w, height: h });
try {
  await c.goto(`${o.url}?export=1`);
  const film = await c.evaluate('window.__film');
  let n = 0;
  for (const s of film.shots) {
    // the last frame before a cut is (ceil(end * fps) - 1) / fps: check it, not just the middle
    for (const t of [s.start, (s.start + s.end) / 2, (Math.ceil(s.end * fps) - 1) / fps]) {
      await Bun.write(join(out, `f_${String(n++).padStart(3, '0')}.png`), await c.frame(`window.__frame(${t})`));
    }
  }
  const sheet = Bun.spawnSync(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '1', '-i', join(out, 'f_%03d.png'),
    '-vf', `scale=${Math.round(w / 2)}:-2,tile=3x${film.shots.length}:padding=4:color=black`, '-frames:v', '1', join(out, 'sheet.png')]);
  console.log(sheet.exitCode === 0 ? `contact sheet -> ${out}/sheet.png (rows = shots; START, middle, last frame before the cut)` : 'ffmpeg contact sheet failed');

  // 3 · seek-safety: forward, backward, random order must give identical frames
  const times = [0.5, 3.99, 4.0, 7.3, 9.9];
  const fwd: string[] = [];
  for (const t of times) fwd.push(await c.evaluate(`window.__frame(${t})`));
  const order = [3, 0, 4, 1, 2, 3];
  let same = true;
  for (const i of order) if ((await c.evaluate(`window.__frame(${times[i]})`)) !== fwd[i]) { same = false; console.error(`seek-safety: t=${times[i]} differs when rendered out of order`); }
  console.log(same ? 'seek-safety: identical frames in any order' : 'seek-safety: FAILED');
  if (!same) failed = true;
  if (c.errors.length) { failed = true; console.error(`export errors:\n  ${c.errors.join('\n  ')}`); }
} finally { await c.close(); }

console.log(failed ? 'CHECK FAILED' : 'check ok');
process.exit(failed ? 1 : 0);
