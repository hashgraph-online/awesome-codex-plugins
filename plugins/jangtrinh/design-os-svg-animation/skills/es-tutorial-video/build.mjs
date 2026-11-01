#!/usr/bin/env node
/* Assemble a tutorial video from a project folder. This script never calls a network service (no voice API):
 * clips are produced elsewhere, after the owner approves the script, and only read here.
 *   node build.mjs scaffold <build-dir> <slug> [--into <promo-dir>]   create <promo-dir>/<slug>-tutorial/ from templates/
 *   node build.mjs render <project> [--aspect landscape|portrait] --beats [--out-dir <dir>]
 *   node build.mjs mix <project>                                       voice + music bed -> out/tutorial-audio.wav (owner gate 1)
 *   node build.mjs render <project> [--aspect a] --full [--shards N]   60 fps MP4 (owner gate 1), shards render in parallel
 * Prints the output path(s). Exit 0 ok, 1 refused or failed, 2 cannot run. */
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { SKILL_DIR, kitDir, kitModule } from './kit-path.mjs';

const [cmd, ...rest] = process.argv.slice(2);
const flag = (n, d) => { const i = rest.indexOf(n); return i < 0 ? d : (rest[i + 1] === undefined || rest[i + 1].startsWith('--') ? true : rest[i + 1]); };
const positional = rest.filter((a, i) => !a.startsWith('--') && !['--aspect', '--shards', '--into', '--out-dir'].includes(rest[i - 1]));
const die = (code, msg) => { (code === 0 ? console.log : console.error)(msg); process.exit(code); };
if (!cmd || cmd === '--help') die(cmd ? 0 : 2, fs.readFileSync(new URL(import.meta.url), 'utf8').split('*/')[0].replace(/^#!.*\n/, '').replace(/^\/\* ?/, '').replace(/^ \* ?/gm, ''));

const run = (args) => new Promise((res) => { const p = spawn(process.execPath, args, { stdio: 'inherit' }); p.on('close', (c) => res(c ?? 1)); });
const fill = (text, vars) => Object.entries(vars).reduce((t, [k, v]) => t.replaceAll(`{{${k}}}`, v), text);
const homeTilde = (p) => (p.startsWith(os.homedir() + path.sep) ? '~' + p.slice(os.homedir().length) : p);

async function scaffold() {
  const [buildDirArg, slug] = positional;
  if (!buildDirArg || !slug) die(2, 'usage: build.mjs scaffold <build-dir> <slug> [--into <promo-dir>]');
  if (!/^[a-z0-9]+(-[a-z0-9]+)*$/.test(slug)) die(2, `slug "${slug}" must be kebab-case`);
  const buildDir = path.resolve(buildDirArg);
  if (!fs.existsSync(buildDir)) die(2, `build folder ${buildDir} does not exist`);
  const into = path.resolve(flag('--into', path.join(process.cwd(), 'promo')));
  const target = path.join(into, `${slug}-tutorial`);
  if (fs.existsSync(target)) die(1, `${target} already exists; refusing to overwrite`);
  const vars = { SLUG: slug, TITLE: slug.toUpperCase(), BUILD_DIR: homeTilde(buildDir) };
  const files = [['tutorial.config.json.tpl', 'tutorial.config.json'], ['tutorial-timeline.js.tpl', 'tutorial-timeline.js'], ['extract-evidence.py.tpl', 'extract-evidence.py'],
    ['project-gitignore.tpl', '.gitignore'], ['script-vi.json.tpl', 'voiceover/script-vi.json'], ['storyboard.md.tpl', 'storyboard.md']];
  for (const [src, dst] of files) {
    const out = path.join(target, dst);
    fs.mkdirSync(path.dirname(out), { recursive: true });
    fs.writeFileSync(out, fill(fs.readFileSync(path.join(SKILL_DIR, 'templates', src), 'utf8'), vars));
  }
  fs.mkdirSync(path.join(target, 'data'), { recursive: true });
  fs.writeFileSync(path.join(target, 'data', 'evidence.js'), 'window.EVIDENCE = {};\n');
  console.log(target);
  console.error(`scaffolded: nothing authored yet. Next: owner gate 1 (storyboard.md), then extract-evidence.py and the timeline. Run validate.mjs to see what is missing.`);
}

async function loadGuarded(needScript) {
  const [projArg] = positional;
  if (!projArg) die(2, 'project folder required');
  const kit = await kitModule();
  let project;
  try { project = kit.loadProject(projArg); } catch (e) { die(2, e.message); }
  const a = project.cfg.approvals;
  const missing = [!a.storyboard && 'storyboard', needScript && !a.script && 'script'].filter(Boolean);
  if (missing.length) die(1, `gate: owner approval missing for ${missing.join(' + ')} in ${path.relative(process.cwd(), project.file)} (approvals). Stop here: ask the owner, record who and when, then re-run. No voice credit is spent before that.`);
  return project;
}

async function mix() {
  const project = await loadGuarded(true);
  process.exit(await run([path.join(kitDir(), 'voiceover', 'mix-voiceover.mjs'), '--project', project.dir]));
}

async function render() {
  const beats = rest.includes('--beats'), full = rest.includes('--full');
  if (beats === full) die(2, 'give exactly one of --beats or --full');
  const [projArg] = positional;
  const kit = await kitModule();
  let project;
  try { project = kit.loadProject(projArg); } catch (e) { die(2, e.message); }
  if (full) project = await loadGuarded(true);
  const aspects = flag('--aspect') && flag('--aspect') !== true ? [flag('--aspect')] : ['landscape', 'portrait'];
  if (aspects.some((a) => !['landscape', 'portrait'].includes(a))) die(2, '--aspect must be landscape or portrait');
  const renderer = path.join(kitDir(), 'render-tutorial.mjs');
  const base = ['--project', project.dir];
  if (beats) {
    const outDir = path.resolve(flag('--out-dir', path.join(project.dir, 'out')));
    const codes = await Promise.all(aspects.map((a) => run([renderer, ...base, '--aspect', a, '--beats', '--out-dir', outDir])));
    if (codes.some((c) => c !== 0)) die(1, 'beat render failed');
    aspects.forEach((a) => console.log(path.join(outDir, `beat-sheet-${a}.jpg`)));
    return;
  }
  const audio = path.join(project.dir, 'out', 'tutorial-audio.wav');
  if (!fs.existsSync(audio)) die(2, `${audio} missing: run "build.mjs mix ${projArg}" first`);
  const shards = Math.max(1, parseInt(flag('--shards', '1'), 10) || 1);
  const jobs = aspects.map(async (a) => {
    if (shards === 1) return run([renderer, ...base, '--aspect', a, '--full']);
    const codes = await Promise.all(Array.from({ length: shards }, (_, i) => run([renderer, ...base, '--aspect', a, '--full', '--shard', `${i}/${shards}`])));
    if (codes.some((c) => c !== 0)) return 1;
    return run([path.join(kitDir(), 'join-shards.mjs'), ...base, a, String(shards)]);
  });
  if ((await Promise.all(jobs)).some((c) => c !== 0)) die(1, 'full render failed');
  aspects.forEach((a) => console.log(path.join(project.dir, 'out', `${project.cfg.output}-${a}.mp4`)));
}

const table = { scaffold, mix, render };
if (!table[cmd]) die(2, `unknown command "${cmd}"; use scaffold | render | mix`);
await table[cmd]();
