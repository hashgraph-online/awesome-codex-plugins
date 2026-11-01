#!/usr/bin/env node
/* Mechanical reject for a tutorial project. Deterministic, offline, product runtime (node + ffprobe + git).
 *   node validate.mjs <project-dir>            run every check
 *   node validate.mjs <project-dir> --only <check>
 *   node validate.mjs --help
 * One line per failure: "<check>: <what to fix>". Exit 0 = ok, 1 = rejected, 2 = could not run.
 *
 * Checks (each one is a "Rejected when" in rules.md; taste lives in look.md, never here):
 *   contract-intact     contract.json still carries the digest of its own body
 *   config-schema       tutorial.config.json satisfies the kit's CONFIG_SCHEMA
 *   timeline-eval       evidence + timeline files evaluate and every evidence key they use exists
 *   timeline-authored   at least one chapter and one element authored
 *   evidence-shape      every evidence entry is {path, lines|value}
 *   assets-exist        every image/clip the timeline names exists (seq patterns expanded)
 *   script-authored     the voice script has at least one segment
 *   script-clips        every segment has a chapter, a clip, and the clip fits its chapter window
 *   captions-overlap    no caption window starts before the previous one ends
 *   display-block       no project script hard-codes display:block (it overrides display:grid)
 *   no-home-path        no /Users/ in evidence, scripts, assets, data, ref or staged MP4 metadata
 *   gitignore-music     music source, bed and out/tutorial-audio.wav are git-ignored
 *   beat-names          out/beats-*\/ frames are first.jpg or bNNN.jpg (3 digits) */
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { SKILL_DIR, kitModule } from './kit-path.mjs';

const CHECKS = ['contract-intact', 'config-schema', 'timeline-eval', 'timeline-authored', 'evidence-shape', 'assets-exist', 'script-authored',
  'script-clips', 'captions-overlap', 'display-block', 'no-home-path', 'gitignore-music', 'beat-names'];
const args = process.argv.slice(2);
if (args.includes('--help') || args.includes('-h')) {
  console.log(fs.readFileSync(new URL(import.meta.url), 'utf8').split('*/')[0].replace(/^#!.*\n/, '').replace(/^\/\* ?/, '').replace(/^ \* ?/gm, ''));
  process.exit(0);
}
const only = args.includes('--only') ? args[args.indexOf('--only') + 1] : null;
const dirArg = args.find((a, i) => !a.startsWith('--') && args[i - 1] !== '--only');
if (!dirArg || (only && !CHECKS.includes(only))) { console.error(`usage: validate.mjs <project-dir> [--only ${CHECKS.join('|')}]`); process.exit(2); }
const dir = path.resolve(dirArg);
if (!fs.existsSync(dir)) { console.error(`cannot run: ${dir} does not exist`); process.exit(2); }

const kit = await kitModule();
const lines = [];
const fail = (check, msg) => lines.push(`${check}: ${msg}`);
const want = (c) => !only || only === c;
const rel = (p) => path.relative(dir, p) || '.';
const walk = (d, out = []) => { for (const e of fs.existsSync(d) ? fs.readdirSync(d, { withFileTypes: true }) : []) { const p = path.join(d, e.name); e.isDirectory() ? walk(p, out) : out.push(p); } return out; };
const cannotRun = (msg) => { console.error(`cannot run: ${msg}`); process.exit(2); };

// ---- contract
if (want('contract-intact')) {
  try {
    const contract = JSON.parse(fs.readFileSync(path.join(SKILL_DIR, 'contract.json'), 'utf8'));
    if (!kit.contractIntact(contract)) fail('contract-intact', 'contract.json was edited by hand; regenerate it with node scripts/build-tutorial-contract.mjs');
  } catch (e) { fail('contract-intact', `contract.json unreadable (${e.message}); regenerate it with node scripts/build-tutorial-contract.mjs`); }
}

// ---- config
let project = null;
try { project = kit.loadProject(dir); } catch (e) {
  if (!fs.existsSync(path.join(dir, kit.CONFIG_FILE))) cannotRun(`${kit.CONFIG_FILE} not found in ${dir}`);
  if (want('config-schema')) for (const l of String(e.message).split('\n').slice(1).map((x) => x.trim()).filter(Boolean)) fail('config-schema', l);
  if (want('config-schema') && !String(e.message).includes('\n')) fail('config-schema', e.message);
}
if (!project) { for (const l of lines) console.log(l); process.exit(lines.length ? 1 : 2); }
const cfg = project.cfg;
const exists = (rp) => fs.existsSync(path.join(dir, rp));
if (want('config-schema')) {
  for (const f of [cfg.evidence, ...cfg.timeline, cfg.voiceover.script]) if (!exists(f)) fail('config-schema', `${f} is listed in the config but missing`);
  if (/^\s*not measured/i.test(cfg.grid.measuredBy)) fail('config-schema', 'grid.measuredBy says the bar grid is not measured yet; measure it with numpy and record how (rules.md, grid rule)');
}

// ---- timeline
let tl = null;
try { tl = kit.loadTimeline(project); } catch (e) { if (want('timeline-eval')) fail('timeline-eval', `${String(e.message).split('\n')[0]}; the timeline may only read keys present in ${cfg.evidence}`); }
if (tl) {
  if (want('timeline-authored') && (tl.CH.length === 0 || tl.EL.length === 0)) {
    fail('timeline-authored', `nothing authored yet (${tl.CH.length} chapters, ${tl.EL.length} elements, ${tl.CAP.length} captions); author the timeline from concepts.md`);
  }
  if (want('evidence-shape')) {
    for (const [k, v] of Object.entries(tl.evidence)) {
      if (!v || typeof v.path !== 'string' || !(Array.isArray(v.lines) || v.value !== undefined)) fail('evidence-shape', `evidence "${k}" must be {path, lines|value}; regenerate it with extract-evidence.py, never by hand`);
    }
  }
  if (want('assets-exist')) {
    const seen = new Set(); const missing = new Set();
    const note = (s) => { if (!s.includes('%') && /\.(png|jpe?g|webp|gif|svg|mp4|webm)$/i.test(s) && !/^https?:/.test(s)) seen.add(s); };
    const visit = (v) => { if (typeof v === 'string') note(v); else if (Array.isArray(v)) v.forEach(visit); else if (v && typeof v === 'object') Object.values(v).forEach(visit); };
    tl.CH.forEach((c) => visit(c.img)); tl.EL.forEach((e) => {
      visit(e);
      if (e.type === 'seq' && e.pattern) for (const i of [1, e.n]) seen.add(e.pattern.replace('%03d', String(i).padStart(3, '0')));
    });
    for (const s of seen) if (!exists(s)) missing.add(s);
    for (const m of [...missing].sort().slice(0, 20)) fail('assets-exist', `${m} is named by the timeline but does not exist`);
    if (missing.size > 20) fail('assets-exist', `... and ${missing.size - 20} more missing assets`);
  }
  if (want('captions-overlap')) {
    const cap = [...tl.CAP].sort((a, b) => a.t0 - b.t0);
    for (let i = 1; i < cap.length; i++) if (cap[i - 1].t1 > cap[i].t0 + 1e-9) fail('captions-overlap', `caption "${String(cap[i - 1].en || cap[i - 1].vi).slice(0, 30)}" ends at ${cap[i - 1].t1.toFixed(2)} s after the next one starts at ${cap[i].t0.toFixed(2)} s; shorten it`);
  }
}

// ---- voice script
if (want('script-authored') || want('script-clips')) {
  let segments = [];
  try { segments = JSON.parse(fs.readFileSync(path.join(dir, cfg.voiceover.script), 'utf8')).segments || []; } catch { /* reported as config-schema when the file is missing */ }
  if (want('script-authored') && segments.length === 0) fail('script-authored', `${cfg.voiceover.script} has no segments yet; write one segment per chapter after the owner approves the storyboard`);
  if (want('script-clips') && tl && segments.length) {
    if (spawnSync('ffprobe', ['-version']).error) cannotRun('ffprobe not found (needed to measure clip lengths)');
    for (const r of kit.placementTable(project, tl)) {
      if (!r.chapter) fail('script-clips', `segment "${r.id}" has no chapter with that id in the timeline`);
      else if (!r.clip) fail('script-clips', `segment "${r.id}" has no clip at ${rel(r.file)}; render it only after the owner approves the script`);
      else if (r.overrun) fail('script-clips', `clip "${r.id}" ends ${r.end.toFixed(2)} s but its chapter ends ${r.limit.toFixed(2)} s (needs ${kit.GAP} s clearance); widen the chapter in the timeline WARP`);
    }
  }
}

// ---- source hygiene
if (want('display-block')) {
  for (const f of cfg.timeline) {
    (exists(f) ? fs.readFileSync(path.join(dir, f), 'utf8') : '').split('\n').forEach((l, i) => {
      if (/display\s*=\s*['"]block['"]|display\s*:\s*['"]?block/.test(l)) fail('display-block', `${f}:${i + 1} hard-codes display:block; use display='' so display:grid survives`);
    });
  }
}
if (want('no-home-path')) {
  const needle = Buffer.from('/Users/');
  // a Set: data/evidence.js is both the configured evidence file and part of the data/ walk
  const targets = new Set([path.join(dir, kit.CONFIG_FILE), ...[cfg.evidence, ...cfg.timeline, cfg.voiceover.script].map((f) => path.join(dir, f)),
    ...['assets', 'data', 'ref'].flatMap((d) => walk(path.join(dir, d))), ...walk(path.join(dir, 'out')).filter((f) => /\.(mp4|jpe?g|png)$/i.test(f) && !/[\\/](beats-|shards)/.test(f))]);
  for (const f of targets) if (fs.existsSync(f) && fs.readFileSync(f).includes(needle)) fail('no-home-path', `${rel(f)} contains "/Users/"; strip the metadata (mogrify -strip) or fix the extractor, then re-check`);
}
if (want('gitignore-music')) {
  const probe = spawnSync('git', ['rev-parse', '--is-inside-work-tree'], { cwd: dir, encoding: 'utf8' });
  if (probe.status !== 0) cannotRun('git is not available or the project is not inside a git work tree (needed for the music licence check)');
  for (const f of [cfg.music.file, cfg.music.bed, 'out/tutorial-audio.wav']) {
    if (spawnSync('git', ['check-ignore', '-q', f], { cwd: dir }).status !== 0) fail('gitignore-music', `${f} is not git-ignored; the music licence forbids committing the track or any mix, add it to .gitignore`);
  }
}
if (want('beat-names')) {
  for (const d of fs.existsSync(path.join(dir, 'out')) ? fs.readdirSync(path.join(dir, 'out')).filter((n) => n.startsWith('beats-')) : []) {
    for (const f of fs.readdirSync(path.join(dir, 'out', d))) if (!/^(first|b\d{3})\.jpg$/.test(f)) fail('beat-names', `out/${d}/${f} is not first.jpg or bNNN.jpg (3 digits); re-render with the kit`);
  }
}

if (lines.length) { for (const l of lines) console.log(l); process.exit(1); }
console.log(`ok: ${only ? only : `${CHECKS.length} checks`} passed for ${rel(dir) === '.' ? dir : rel(dir)}`);
