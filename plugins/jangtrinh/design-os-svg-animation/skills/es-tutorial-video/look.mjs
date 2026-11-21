#!/usr/bin/env node
/* Visual evidence for a tutorial project: renders the fixed shot list from look.md into ONE sheet PNG and
 * measures what a machine can measure. Eye-checks (look.md items 1-6) are printed as reminders, never scored.
 *   node look.mjs <project-dir> [--out <sheet.png>]     default out: <project>/out/look/look-sheet.png
 * Shots, per aspect: every chapter at 0.75 bar (settled chapter card), every chapter at its midpoint (settled content),
 * and the two frames on each side of the 2 seams a 3-shard render would join. Needs Chrome + ImageMagick montage.
 * Machine items (exit 1 when any fails):
 *   L1 fonts      Geist and Geist Mono loaded before every capture
 *   L2 edge       no settled element (opacity >= 0.9) sticks out of the stage
 *   L3 portrait   in 9:16 no settled content (full-bleed backgrounds excepted) below y = 1600 (caption zone starts there)
 *   L4 caption    the visible caption stays 24 px inside the stage
 *   L5 requests   no page error, failed request or broken image
 * Exit 0 ok, 1 machine item failed, 2 cannot run (no browser, no montage, no puppeteer-core). Never installs anything. */
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { kitModule } from './kit-path.mjs';

const args = process.argv.slice(2);
if (args.includes('--help') || args.includes('-h')) { console.log(fs.readFileSync(new URL(import.meta.url), 'utf8').split('*/')[0].replace(/^#!.*\n/, '').replace(/^\/\* ?/, '').replace(/^ \* ?/gm, '')); process.exit(0); }
const dirArg = args.find((a, i) => !a.startsWith('--') && args[i - 1] !== '--out');
const cannot = (m) => { console.error(`cannot run: ${m}`); process.exit(2); };
if (!dirArg) cannot('usage: look.mjs <project-dir> [--out <sheet.png>]');
const CHROME = process.env.CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
if (!fs.existsSync(CHROME)) cannot(`no browser at ${CHROME} (set CHROME_PATH); without a browser do the eye-checks in look.md on a rendered beat sheet instead`);
if (spawnSync('montage', ['-version']).error) cannot('ImageMagick montage not found');
let puppeteer;
try { puppeteer = (await import('puppeteer-core')).default; } catch { cannot('puppeteer-core is not installed next to this skill (npm i puppeteer-core in the repo)'); }

const kit = await kitModule();
let project;
try { project = kit.loadProject(dirArg); } catch (e) { cannot(e.message); }
const tl = kit.loadTimeline(project);
if (!tl.CH.length) { console.error('look: nothing authored yet (0 chapters); nothing to look at'); process.exit(1); }
const T = project.cfg.duration, FPS = 60, BAR = project.bar;
const outSheet = path.resolve(args.includes('--out') ? args[args.indexOf('--out') + 1] : path.join(project.dir, 'out', 'look', 'look-sheet.png'));
const shotDir = path.join(path.dirname(outSheet), 'shots');
fs.rmSync(shotDir, { recursive: true, force: true }); fs.mkdirSync(shotDir, { recursive: true });

const shots = []; // [name, t, kind]
tl.CH.forEach((c, i) => {
  const n = String(i).padStart(2, '0');
  shots.push([`${n}-${c.id}-card`, Math.min(T, c.t0 + 0.75 * BAR), 'card']);
  shots.push([`${n}-${c.id}-content`, Math.min(T, (c.t0 + c.t1) / 2), 'content']);
});
const frames = Math.round(T * FPS);
for (const i of [1, 2]) { const f = Math.floor(frames * i / 3); shots.push([`seam${i}-a`, (f - 1) / FPS, 'seam'], [`seam${i}-b`, f / FPS, 'seam']); }

const problems = [];
const note = (id, msg) => { if (!problems.some((p) => p.startsWith(`${id} ${msg}`))) problems.push(`${id} ${msg}`); };
const browser = await puppeteer.launch({ executablePath: CHROME, headless: true, args: ['--hide-scrollbars', '--allow-file-access-from-files', '--force-color-profile=srgb'] });
try {
  for (const aspect of ['landscape', 'portrait']) {
    const portrait = aspect === 'portrait', [W, H] = portrait ? [1080, 1920] : [1920, 1080];
    const page = await browser.newPage();
    await page.setViewport({ width: W, height: H, deviceScaleFactor: 1 });
    page.on('pageerror', (e) => note('L5', `${aspect}: page error ${String(e.message).slice(0, 80)}`));
    page.on('requestfailed', (r) => note('L5', `${aspect}: request failed ${r.url().split('/').slice(-2).join('/')}`));
    const built = kit.writePage(project, aspect);
    await page.goto(built.url, { waitUntil: 'networkidle0', timeout: 120000 });   // the page loads Geist from Google Fonts; a loaded machine needs more than the 30 s default
    const fonts = await page.evaluate(async () => { await document.fonts.ready; return [...new Set([...document.fonts].filter((f) => f.status === 'loaded').map((f) => f.family))]; });
    for (const need of ['Geist', 'Geist Mono']) if (!fonts.includes(need)) note('L1', `${aspect}: font ${need} did not load; glyphs fall back and the layout is wrong`);
    for (const [name, t, kind] of shots) {
      const info = await page.evaluate(async (x, kindIn, w, h) => {
        window.seek(x); if (window.__framesReady) await window.__framesReady();
        const out = { edge: [], low: [], broken: [], cap: null };
        for (const n of document.querySelectorAll('#stage .el')) {
          const cs = getComputedStyle(n); if (cs.display === 'none' || parseFloat(cs.opacity) < 0.9) continue;
          const r = n.getBoundingClientRect(); if (!r.width || !r.height) continue;
          if (kindIn !== 'seam' && (r.left < -1 || r.top < -1 || r.right > w + 1 || r.bottom > h + 1)) out.edge.push(`${n.className.replace('el ', '')} [${Math.round(r.left)},${Math.round(r.top)},${Math.round(r.right)},${Math.round(r.bottom)}]`);
          if (kindIn === 'content' && h > w && r.bottom > 1600 && r.top > 1) out.low.push(`${n.className.replace('el ', '')} bottom ${Math.round(r.bottom)}`);
        }
        for (const im of document.images) { const cs = getComputedStyle(im); if (im.src && im.offsetParent !== null && cs.visibility === 'visible' && !(im.complete && im.naturalWidth)) out.broken.push(im.src.split('/').slice(-2).join('/')); }
        const cap = document.querySelector('#cap'); if (cap && parseFloat(getComputedStyle(cap).opacity) >= 0.9) { const r = cap.getBoundingClientRect(); out.cap = [r.left, r.top, r.right, r.bottom]; }
        return out;
      }, t, kind, W, H);
      info.edge.forEach((e) => note('L2', `${aspect} ${name}: ${e}`));
      info.low.forEach((e) => note('L3', `${aspect} ${name}: ${e}`));
      info.broken.forEach((e) => note('L5', `${aspect} ${name}: image not decoded ${e}`));
      if (info.cap && (info.cap[0] < 24 || info.cap[2] > W - 24 || info.cap[3] > H - 24)) note('L4', `${aspect} ${name}: caption [${info.cap.map(Math.round)}] is closer than 24 px to the stage edge`);
      fs.writeFileSync(path.join(shotDir, `${aspect}-${name}.jpg`), await page.screenshot({ type: 'jpeg', quality: 88 }));
    }
    built.cleanup(); await page.close();
  }
} finally { await Promise.race([browser.close(), new Promise((r) => setTimeout(r, 10000))]); }

const sheetPart = (aspect, tile, geom) => {
  const part = path.join(shotDir, `sheet-${aspect}.png`);
  const files = fs.readdirSync(shotDir).filter((f) => f.startsWith(`${aspect}-`)).sort().map((f) => path.join(shotDir, f));
  const r = spawnSync('montage', [...files, '-tile', tile, '-geometry', geom, '-background', '#cfccc6', part]);
  if (r.status !== 0) cannot(`montage failed: ${String(r.stderr).slice(0, 200)}`);
  return part;
};
const cols = 8;
const a = sheetPart('landscape', `${cols}x`, '320x180+4+4'), b = sheetPart('portrait', `${cols * 2}x`, '180x320+4+4');
const joined = spawnSync('magick', [a, b, '-background', '#cfccc6', '-gravity', 'center', '-append', outSheet]);
if (joined.status !== 0) cannot(`magick -append failed: ${String(joined.stderr).slice(0, 200)}`);

console.log(`sheet: ${outSheet} (${shots.length} shots x 2 aspects: landscape on top, portrait below; order = chapter card, chapter content, 2 seams)`);
for (const [id, label] of [['L1', 'fonts'], ['L2', 'edge'], ['L3', 'portrait'], ['L4', 'caption'], ['L5', 'requests']]) {
  const mine = problems.filter((p) => p.startsWith(id + ' '));
  console.log(`${id} ${label}: ${mine.length ? 'FAIL' : 'ok'}`);
  mine.slice(0, 8).forEach((p) => console.log(`  ${p}`));
  if (mine.length > 8) console.log(`  ... ${mine.length - 8} more`);
}
console.log('eye-checks still yours (look.md 1-7): captions readable, nothing cut at the edge you cannot measure, cards fan on stage, portrait slots, seam frames, honest-limits chapter.');
process.exit(problems.length ? 1 : 0);
