#!/usr/bin/env bun
// check_labels.ts: QA of on-screen text from the per-frame boxes that capture.ts --labels writes.
//
//   bun scripts/check_labels.ts <labels.json> [--safe-x 64] [--safe-y 48] [--phone 390] [--wps 4.5]
//
// Checks every frame (items with opacity >= 0.15 count):
//   overlap     two text boxes intersect (4 px margin)                                  -> FAIL
//   safe area   a box is closer than --safe-x px to the left/right edge or --safe-y to the top/bottom -> FAIL
//   anchor      a label box covers its own anchor point (the leader points into its own text)         -> WARN
//   phone size  font px x (phone / frame width): names, tags and titles need >= 9 px on a 390 px phone,
//               every other line >= 6.5 px (a 1080p frame shown full-width in a portrait feed)       -> FAIL
//   reading     each label/text is readable (opacity >= 0.5) for >= 0.3 s + words / wps seconds      -> FAIL
// Exit code 1 if anything FAILs. Prints a one-line summary per check.
import { readFile } from 'node:fs/promises';

const a = Bun.argv.slice(2);
const flag = (k: string, d: number) => { const i = a.indexOf(`--${k}`); return i < 0 ? d : Number(a[i + 1]); };
const file = a.find(x => x.endsWith('.json'));
if (!file) { console.log('usage: bun scripts/check_labels.ts <labels.json> [--safe-x 64] [--safe-y 48] [--phone 390] [--wps 4.5]'); process.exit(1); }
const safeX = flag('safe-x', 64), safeY = flag('safe-y', 48), phone = flag('phone', 390), wps = flag("wps", 4.5);
const L = JSON.parse(await readFile(file, 'utf8'));
const W = L.width, H = L.height, fps = L.fps, scale = phone / W;
type Item = { kind: string; id: string; text: string[]; box: number[]; anchor?: number[]; opacity: number; fontPx?: number[]; role?: string };

const issues: Record<string, Map<string, number[]>> = { overlap: new Map(), safe: new Map(), anchor: new Map(), phone: new Map(), reading: new Map() };
const note = (kind: string, key: string, t: number) => { const m = issues[kind]; if (!m.has(key)) m.set(key, []); m.get(key)!.push(t); };
const readable = new Map<string, { frames: number; words: number; text: string }>();
const hit = (p: number[], q: number[], m = 4) => p[0] < q[0] + q[2] + m && q[0] < p[0] + p[2] + m && p[1] < q[1] + q[3] + m && q[1] < p[1] + p[3] + m;

for (const f of L.frames as { t: number; items: Item[] }[]) {
  if (!f) continue;
  const on = f.items.filter(i => i.opacity >= 0.15);
  for (let i = 0; i < on.length; i++) for (let j = i + 1; j < on.length; j++) if (hit(on[i].box, on[j].box)) note('overlap', `${on[i].id} x ${on[j].id}`, f.t);
  for (const it of on) {
    const [x, y, w, h] = it.box;
    if (x < safeX || x + w > W - safeX || y < safeY || y + h > H - safeY) note('safe', `${it.id} (box ${x.toFixed(0)},${y.toFixed(0)} ${w.toFixed(0)}x${h.toFixed(0)})`, f.t);
    if (it.anchor && it.kind === 'label') { const [ax, ay] = it.anchor; if (ax > x && ax < x + w && ay > y && ay < y + h) note('anchor', it.id, f.t); }
    (it.fontPx || []).forEach((px, k) => {
      const primary = k === 0 && ['label', 'tag', 'title'].includes(it.role || '');
      const need = primary ? 9 : 6.5;
      if (px * scale < need) note('phone', `${it.id} line ${k + 1}: ${px}px -> ${(px * scale).toFixed(1)}px on a ${phone}px phone (need ${need})`, f.t);
    });
    if (it.opacity >= 0.5 && it.kind !== 'scalebar') {
      const key = it.id, words = it.text.join(' ').split(/\s+/).filter(w => /[\p{L}\p{N}]/u.test(w)).length;
      const r = readable.get(key) || { frames: 0, words, text: it.text.join(' / ') }; r.frames++; readable.set(key, r);
    }
  }
}
for (const [id, r] of readable) { const secs = r.frames / fps, need = 0.3 + r.words / wps; if (secs < need) note('reading', `${id}: ${secs.toFixed(2)} s readable, needs ${need.toFixed(2)} s for ${r.words} words ("${r.text}")`, 0); }

const span = (ts: number[]) => ts.length ? `${Math.min(...ts).toFixed(2)}-${Math.max(...ts).toFixed(2)} s (${ts.length} frames)` : '';
let fail = 0;
for (const [kind, label, severity] of [['overlap', 'overlaps', 'FAIL'], ['safe', 'outside the safe area', 'FAIL'], ['anchor', 'label covers its anchor', 'WARN'], ['phone', 'too small on a phone', 'FAIL'], ['reading', 'too short to read', 'FAIL']] as const) {
  const m = issues[kind];
  if (!m.size) { console.log(`ok    ${kind}`); continue; }
  if (severity === 'FAIL') fail++;
  console.log(`${severity.padEnd(5)} ${kind}: ${m.size} ${label}`);
  for (const [k, ts] of m) console.log(`        ${k}${kind === 'reading' ? '' : `  @ ${span(ts)}`}`);
}
console.log(`${L.frames.length} frames, ${readable.size} texts checked: ${fail ? `${fail} check(s) FAILED` : 'all checks passed'}`);
process.exit(fail ? 1 : 0);
