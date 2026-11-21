#!/usr/bin/env bun
// sheet.ts: contact sheets for review, from a video or a folder of PNG stills.
// Needs ffmpeg/ffprobe and ImageMagick 7 (`magick`). Works on builds without FreeType or Ghostscript
// (and ffmpeg without drawtext): timestamps are drawn as seven-segment digits from plain rectangles.
//
//   bun scripts/sheet.ts <video.mp4 | stills-dir> <out.png> [--n 12] [--cols 4] [--tile 640] [--phone]
//   bun scripts/sheet.ts renders/master.mp4 qa/sheet.png               # 12 evenly spaced frames, 640 px tiles
//   bun scripts/sheet.ts renders/master.mp4 qa/phone.png --phone       # 390 px tiles = a phone feed
//   bun scripts/sheet.ts qa/stills qa/stills_sheet.png --cols 3        # every PNG in the folder, sorted
//   bun scripts/sheet.ts renders/master.mp4 qa/cut.png --at 16.9,17.4,18.0,18.4   # chosen times
//
// --phone scales each tile to 390 px wide: a 1080p frame shown full-width in a portrait phone feed.
// Read it with the Read tool at 100%: a label you cannot read there cannot be read on a phone.
import { mkdtemp, rm, readdir, mkdir } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join, dirname, basename } from 'node:path';

const a = Bun.argv.slice(2);
const flag = (k: string, d?: string) => { const i = a.indexOf(`--${k}`); return i < 0 ? d : a[i + 1]; };
const [src, out] = a.filter((x, i) => !x.startsWith('--') && !(i > 0 && a[i - 1].startsWith('--') && !['--phone'].includes(a[i - 1])));
if (!src || !out) { console.log('usage: bun scripts/sheet.ts <video|dir> <out.png> [--n 12] [--cols 4] [--tile 640] [--phone] [--at t,t,..]'); process.exit(1); }
const phone = a.includes('--phone');
const tile = Number(phone ? 390 : flag('tile', '640'));
const cols = Number(flag('cols', '4')), n = Number(flag('n', '12'));
const run = (cmd: string[]) => { const p = Bun.spawnSync(cmd); if (p.exitCode) throw new Error(`${cmd[0]} failed: ${p.stderr}`); return String(p.stdout); };

// seven-segment glyphs: segments a b c d e f g
const SEG: Record<string, string> = { '0': 'abcdef', '1': 'bc', '2': 'abged', '3': 'abgcd', '4': 'fgbc', '5': 'afgcd', '6': 'afgedc', '7': 'abc', '8': 'abcdefg', '9': 'abcdfg', '-': 'g', 's': 'afgcd' };
function digits(text: string, x0: number, y0: number, h: number) {
  const w = h * 0.55, th = Math.max(2, Math.round(h / 8)), cmds: string[] = []; let x = x0;
  const r = (x1: number, y1: number, x2: number, y2: number) => cmds.push(`rectangle ${Math.round(x1)},${Math.round(y1)} ${Math.round(x2)},${Math.round(y2)}`);
  for (const ch of text) {
    if (ch === '.') { r(x, y0 + h - th, x + th, y0 + h); x += th * 3; continue; }
    const s = SEG[ch] || ''; const m = y0 + h / 2;
    if (s.includes('a')) r(x, y0, x + w, y0 + th); if (s.includes('g')) r(x, m - th / 2, x + w, m + th / 2); if (s.includes('d')) r(x, y0 + h - th, x + w, y0 + h);
    if (s.includes('f')) r(x, y0, x + th, m); if (s.includes('b')) r(x + w - th, y0, x + w, m);
    if (s.includes('e')) r(x, m, x + th, y0 + h); if (s.includes('c')) r(x + w - th, m, x + w, y0 + h);
    x += w + th * 2.2;
  }
  return { cmds, width: x - x0 };
}
function label(inp: string, text: string, outp: string) {
  const h = Math.max(10, Math.round(tile / 28)), pad = Math.round(h / 2.5);
  const d = digits(text, pad, pad, h);
  run(['magick', inp, '-resize', `${tile}x`, '-fill', '#000000b0', '-draw', `rectangle 0,0 ${Math.round(d.width + pad * 2)},${h + pad * 2}`, '-fill', '#ffffff', ...d.cmds.flatMap(c => ['-draw', c]), outp]);
}

const tmp = await mkdtemp(join(tmpdir(), 'c3d-sheet-'));
try {
  let i = 0;
  const isDir = !src.endsWith('.mp4') && !src.endsWith('.mov') && !src.endsWith('.webm');
  if (isDir) {
    const files = (await readdir(src)).filter(f => f.endsWith('.png')).sort();
    for (const f of files) { const tag = basename(f, '.png').replace(/[^0-9.\-]/g, '') || String(i); label(join(src, f), tag, join(tmp, `${String(i++).padStart(4, '0')}.png`)); }
  } else {
    const dur = Number(run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', src]).trim());
    const at = flag('at'); const times = at ? at.split(',').map(Number) : Array.from({ length: n }, (_, k) => (dur * (k + 0.5)) / n);
    for (const t of times) { const raw = join(tmp, 'raw.png'); run(['ffmpeg', '-v', 'error', '-y', '-ss', t.toFixed(3), '-i', src, '-frames:v', '1', raw]); label(raw, `${t.toFixed(1)}s`, join(tmp, `${String(i++).padStart(4, '0')}.png`)); }
  }
  await mkdir(dirname(out), { recursive: true });
  const tiles = (await readdir(tmp)).filter(f => /^\d{4}\.png$/.test(f)).sort().map(f => join(tmp, f));
  run(['magick', 'montage', ...tiles, '-tile', `${cols}x`, '-geometry', '+4+4', '-background', '#1a1a1a', out]);
  console.log(`${out} (${tiles.length} tiles, ${tile} px wide)`);
} finally { await rm(tmp, { recursive: true, force: true }); }
