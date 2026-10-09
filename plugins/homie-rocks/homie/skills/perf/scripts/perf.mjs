#!/usr/bin/env node
/**
 * perf.mjs: make a studio's game faster one measured change at a time, and keep only what really helped.
 *
 *   baseline <game> --url <site> [--goal <metric>] [--devices computer,phone] [--runs 6] [--seconds 15] [--cpu 4] [--min 3]
 *       build the game (keeping its source map), keep that build and the game's source as the one to beat, run the
 *       studio's own two-browser check, measure it `runs` times per device, profile it once per device, and write
 *       BASELINE.md: the numbers, how much they move run to run, where the time goes, and what a player downloads.
 *   try <game> --name "<the one change>" --looks same|"<how it looks now>" --plays same|"<how it plays now>" [--goal <metric>] [--measure]
 *       after ONE change to games/<game>/: build it, run the two-browser check (it must pass), then measure the build to
 *       beat and this one in alternating order (before, after, after, before, ...), `runs` times each per device, and
 *       compare (homie-studio perf compare). KEEP when the goal is better beyond the noise and nothing guarded got
 *       worse; otherwise REVERT: games/<game>/ goes back to the kept source (only that folder) and the kept build is
 *       served again. A busy computer gives BLOCKED: nothing decided, the change left in place to try again. --goal judges
 *       this change on another metric than the loop's (a change aimed at load time is judged on load time); the guards
 *       still hold everything else. --measure: a change kept for another reason (how a move feels, the lab skill) is
 *       measured the same way and gets the same verdict, as MEASURED, and is never reverted: it stays in games/<game>/
 *       and is served, and the build to beat stays what it was.
 *   revert <game>       put games/<game>/ and the served build back to the kept one (a change you drop untried)
 *   report <game> [--final-runs <n>]
 *       write perf/<game>/ in the studio: README.md (the goal, before and after with intervals and p, every change tried
 *       and its verdict, what changed in how it looks or plays, where the time goes, what a player downloads, how it was
 *       measured), numbers.json, and before-after/ (screenshots of the first and the kept build, the kept changes as
 *       patches). With more than one change kept, the first build and the kept one are measured against each other again.
 *   status <game>       the loop so far: the goal, the build to beat, each change and its verdict
 *   goals               the metrics a goal or a guard can name
 *
 * Run from inside the studio with its site running (npm run dev, a background task). It drives the studio's own
 * @homie-rocks/studio (0.19.0 or later; 0.19.1 also reads whether each big script is minified): `homie-studio perf`,
 * `perf compare`, `check` and `build --maps`. Two browsers at a time, muted. Everything it measures stays in
 * .perf/<game>/ (git-ignored); only `report` writes into the studio's tracked files. Output is paths and a few numbers,
 * never the data.
 *
 * Before every run it checks the site serves exactly the build it means to measure: every file by SHA-256, and the game
 * page as the build made it with the scripts the site's Worker adds set aside (HOMIE_NET, and any a studio's own Worker
 * injects; lib/page.mjs), which must stay the same through a loop. It waits up to 60 s for a dev server to pick up a
 * build (HOMIE_PERF_SERVE_WAIT_MS sets another wait).
 */
import { spawn, spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { cpSync, existsSync, mkdirSync, readFileSync, readdirSync, rmSync, statfsSync, writeFileSync } from 'node:fs';
import { dirname, join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { experienceDir, experienceJson, findStudio, readJson, slugify, writeJson } from '../../music/scripts/lib/studio.mjs';
import { gamePageCheck, sameAdditions } from './lib/page.mjs';
import { sizeHints } from './lib/sizes.mjs';
import { finish } from '../../playtest/scripts/lib/exit.mjs';
import { preflight } from '../../playtest/scripts/lib/preflight.mjs';

const argv = process.argv.slice(2);
const flags = new Map();
const pos = [];
for (let i = 0; i < argv.length; i++) {
  const a = argv[i];
  if (a.startsWith('--')) { const k = a.slice(2); const v = argv[i + 1]; if (v === undefined || v.startsWith('--')) flags.set(k, true); else { flags.set(k, v); i++; } } else pos.push(a);
}
const JSON_OUT = flags.has('json');
const log = (m) => { if (!JSON_OUT) process.stderr.write(`${m}\n`); };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const sha256 = (buf) => createHash('sha256').update(buf).digest('hex');
const NEEDS = [0, 19, 0];
/** No synchronous child (git diff, diff, ffmpeg) may hold the loop for longer than this: it is stopped and its result treated as missing. */
const CHILD_TIMEOUT_MS = 60_000;
const SKIP = new Set(['node_modules', '.port', 'dist', '.git', '.wrangler', '.DS_Store']);

/* ------------------------------------------------------------------------------------------- the studio */

function studioOrThrow() {
  const root = findStudio();
  if (!root) throw new Error('not inside a Homie studio (no studio.json here or above). The studio-setup skill makes one.');
  return root;
}

/** Run the studio's own `homie-studio <args> --json`; resolves { code, json, err }. */
function cli(root, args, { timeoutMs = 20 * 60_000 } = {}) {
  return new Promise((ok) => {
    const bin = join(root, 'node_modules', '.bin', 'homie-studio');
    if (!existsSync(bin)) { ok({ code: 1, json: null, err: '@homie-rocks/studio is not installed in this studio (npm install)' }); return; }
    const child = spawn(bin, [...args, '--json'], { cwd: root, stdio: ['ignore', 'pipe', 'pipe'] });
    let out = '';
    let err = '';
    child.stdout.on('data', (d) => { out += d; });
    child.stderr.on('data', (d) => { err += d; if (err.length > 20_000) err = err.slice(-10_000); });
    // Bounded all the way down: asked to stop at the timeout, killed 5 s later, and answered 5 s after that even if
    // `close` never comes (a helper process that inherited the pipes keeps them open after the child is gone).
    let settled = false;
    const timers = [];
    const done = (code, timedOut = false) => {
      if (settled) return; settled = true;
      for (const t of timers) clearTimeout(t);
      let json = null;
      try { json = JSON.parse(out); } catch { /* not JSON */ }
      ok({ code, json, timedOut, err: timedOut ? `homie-studio ${args.join(' ')} did not finish in ${Math.round(timeoutMs / 1000)} s and was stopped` : err.trim().split('\n').slice(-3).join(' ') });
    };
    timers.push(setTimeout(() => { try { child.kill('SIGTERM'); } catch { /* gone */ } }, timeoutMs));
    timers.push(setTimeout(() => { try { child.kill('SIGKILL'); } catch { /* gone */ } }, timeoutMs + 5000));
    timers.push(setTimeout(() => { try { child.stdout.destroy(); child.stderr.destroy(); } catch { /* */ } done(1, true); }, timeoutMs + 10_000));
    child.on('close', (code) => done(code));
  });
}

async function needsPerf(root) {
  const v = await cli(root, ['version'], { timeoutMs: 60_000 });
  const have = String(v.json?.version ?? '0.0.0').split('.').map(Number);
  const older = have[0] < NEEDS[0] || (have[0] === NEEDS[0] && (have[1] < NEEDS[1] || (have[1] === NEEDS[1] && have[2] < NEEDS[2])));
  if (older) throw new Error(`this studio's @homie-rocks/studio is ${v.json?.version ?? 'unknown'}; perf needs ${NEEDS.join('.')} or later (homie-studio perf). Pin the newer version in package.json, npm install, then npx --no-install homie-studio upgrade`);
  return v.json.version;
}

/**
 * Can this process reach the play page? A name Node cannot resolve while a browser can (they do not resolve names the
 * same way) is a network preflight failure: BLOCKED, nothing measured, with local testing as the way round it. It is
 * never reported as the game or the site failing.
 */
async function alive(url, game) {
  const pre = await preflight(`${url}/${game}/play`, { timeoutMs: 15_000 });
  if (pre.ok) return;
  const e = new Error(pre.verdict === 'BLOCKED' ? `BLOCKED ${pre.why}` : `${pre.why} (--url ${url})`);
  e.verdict = pre.verdict; e.kind = pre.kind;
  throw e;
}

function diskOk(root) {
  try { const f = statfsSync(root); const gb = (f.bavail * f.bsize) / 1e9; if (gb < 10) throw new Error(`only ${gb.toFixed(1)} GB free on this disk: free some space before a perf loop (it keeps every build it measures)`); } catch (e) { if (/GB free/.test(e.message)) throw e; }
}

/* ------------------------------------------------------------------------------------------- the loop's files */

const loopsDir = (root, game) => join(root, '.perf', game);
function currentLoop(root, game) {
  const name = readJson(join(loopsDir(root, game), 'current.json'), null)?.loop;
  const dir = name ? join(loopsDir(root, game), name) : null;
  if (!dir || !existsSync(join(dir, 'session.json'))) throw new Error(`no perf loop for ${game} yet: run baseline first (perf.mjs baseline ${game} --url <site>)`);
  return { dir, s: readJson(join(dir, 'session.json')) };
}
const saveSession = (dir, s) => writeJson(join(dir, 'session.json'), s);

function listFiles(dir, rel = '') {
  if (!existsSync(join(dir, rel))) return [];
  const out = [];
  for (const e of readdirSync(join(dir, rel), { withFileTypes: true })) {
    if (SKIP.has(e.name)) continue;
    const p = rel ? `${rel}/${e.name}` : e.name;
    if (e.isDirectory()) out.push(...listFiles(dir, p)); else if (e.isFile()) out.push(p);
  }
  return out;
}

/** Keep the built game (and its source map) as build `v`, with a manifest of every file's SHA-256. */
function keepBuild(root, game, dir, v) {
  const to = join(dir, 'builds', v);
  rmSync(to, { recursive: true, force: true });
  const dist = join(root, 'site', 'dist', 'games', game);
  cpSync(dist, join(to, 'files'), { recursive: true });
  const maps = join(root, '.studio', 'maps', game);
  if (existsSync(maps)) cpSync(maps, join(to, 'maps'), { recursive: true });
  const files = Object.fromEntries(listFiles(join(to, 'files')).map((f) => [f, sha256(readFileSync(join(to, 'files', f)))]));
  writeJson(join(to, 'manifest.json'), { v, files });
  return to;
}

/** Keep the game's source folder as `v` (everything but node_modules, .port and build output). */
function keepSource(root, game, dir, v) {
  const from = experienceDir(root, game);
  const to = join(dir, 'sources', v);
  rmSync(to, { recursive: true, force: true });
  for (const f of listFiles(from)) { mkdirSync(dirname(join(to, f)), { recursive: true }); cpSync(join(from, f), join(to, f)); }
  return to;
}

/** The files of games/<game>/ that differ from source `v` (changed, added, removed). */
function sourceDiff(root, game, dir, v) {
  const a = join(dir, 'sources', v);
  const b = experienceDir(root, game);
  const fa = new Set(listFiles(a));
  const fb = new Set(listFiles(b));
  const changed = [];
  for (const f of new Set([...fa, ...fb])) {
    if (!fa.has(f)) changed.push({ file: f, how: 'added' });
    else if (!fb.has(f)) changed.push({ file: f, how: 'removed' });
    else if (sha256(readFileSync(join(a, f))) !== sha256(readFileSync(join(b, f)))) changed.push({ file: f, how: 'changed' });
  }
  return changed.sort((x, y) => x.file.localeCompare(y.file));
}

/** Put games/<game>/ back to source `v`: changed files restored, files the change added removed. Only that folder. */
function restoreSource(root, game, dir, v) {
  const snap = join(dir, 'sources', v);
  const gameDir = experienceDir(root, game);
  const diff = sourceDiff(root, game, dir, v);
  for (const d of diff) {
    const target = join(gameDir, d.file);
    if (d.how === 'added') rmSync(target, { force: true });
    else { mkdirSync(dirname(target), { recursive: true }); cpSync(join(snap, d.file), target); }
  }
  return diff;
}

/** A patch from source a to source b, as games/<game>/… paths (git diff --no-index; diff -ru when there is no git). */
function patchOf(dir, game, a, b, root) {
  const r = spawnSync('git', ['diff', '--no-index', '--no-color', '--src-prefix=a/', '--dst-prefix=b/', join('sources', a), join('sources', b)], { cwd: dir, encoding: 'utf8', maxBuffer: 64 * 1024 * 1024, timeout: CHILD_TIMEOUT_MS, killSignal: 'SIGKILL' });
  let text = r.stdout ?? '';
  if (r.error || (r.status !== 0 && r.status !== 1)) text = spawnSync('diff', ['-ru', join('sources', a), join('sources', b)], { cwd: dir, encoding: 'utf8', maxBuffer: 64 * 1024 * 1024, timeout: CHILD_TIMEOUT_MS, killSignal: 'SIGKILL' }).stdout ?? '';
  return text.split(`sources/${a}/`).join(relative(root, experienceDir(root, game)) + '/').split(`sources/${b}/`).join(relative(root, experienceDir(root, game)) + '/');
}

/** Serve build `v`: its files into site/dist/games/<game>/ (the dev server picks them up) and its map into .studio/maps. */
function installBuild(root, game, dir, v) {
  const from = join(dir, 'builds', v);
  const dist = join(root, 'site', 'dist', 'games', game);
  rmSync(dist, { recursive: true, force: true });
  cpSync(join(from, 'files'), dist, { recursive: true });
  const maps = join(root, '.studio', 'maps', game);
  rmSync(maps, { recursive: true, force: true });
  if (existsSync(join(from, 'maps'))) cpSync(join(from, 'maps'), maps, { recursive: true });
}

/** How long to wait for the site to serve a build it was just given (a dev server notices new files in a second or two). */
const SERVE_WAIT_MS = Math.max(1000, Number(process.env.HOMIE_PERF_SERVE_WAIT_MS) || 60_000);

/**
 * Wait until the site serves exactly build `v`: every file's SHA-256, and the game page as the build made it plus the
 * scripts the site's Worker adds (lib/page.mjs: HOMIE_NET, and any a studio's own Worker injects, such as a small
 * inline shim). A run must never measure the build it did not mean to. Returns the scripts the site added; with
 * `added` (the baseline's), the site must add the same ones: a Worker that changed in the middle of a loop serves a
 * different page to the builds it compares.
 */
async function servedIs(url, game, dir, v, { added = null, timeoutMs = SERVE_WAIT_MS } = {}) {
  const man = readJson(join(dir, 'builds', v, 'manifest.json'));
  const files = Object.entries(man.files).filter(([f]) => !f.startsWith('_landing/') && !(/\.html?$/i.test(f) && f !== 'index.html')).slice(0, 300);
  const until = Date.now() + timeoutMs;
  let wrong = null;
  let page = null;
  while (Date.now() < until) {
    wrong = null;
    for (const [f, want] of files) {
      try {
        if (f === 'index.html') {
          const body = await fetch(`${url}/${game}/__game/`, { signal: AbortSignal.timeout(15_000) }).then((r) => r.text());
          page = gamePageCheck(readFileSync(join(dir, 'builds', v, 'files', 'index.html'), 'utf8'), body);
          if (!page.same) { wrong = `${f}: ${page.why}`; break; }
          if (added && !sameAdditions(added, page.added)) { wrong = `${f}: the site now adds ${addedSaid(page.added)} to the game page, and added ${addedSaid(added)} when the loop began`; break; }
        } else {
          const buf = Buffer.from(await fetch(`${url}/${game}/__game/${f.split('/').map(encodeURIComponent).join('/')}`, { signal: AbortSignal.timeout(30_000) }).then((r) => r.arrayBuffer()));
          if (sha256(buf) !== want) { wrong = `${f} differs`; break; }
        }
      } catch (e) { wrong = `${f}: ${e instanceof Error ? e.message : e}`; break; }
    }
    if (!wrong) return page?.added ?? [];
    await sleep(1500);
  }
  throw new Error(`the site at ${url} did not start serving build ${v} within ${Math.round(timeoutMs / 1000)} s (${wrong}): is the dev server still running? (npm run dev, as a background task)${/the site now adds/.test(wrong) ? '. The site\'s Worker changed since the baseline: put it back, or start a new loop (baseline)' : ''}`);
}

/** The scripts a site adds to the game page, for a person. */
function addedSaid(added) {
  if (!added?.length) return 'no scripts';
  return added.map((x) => (x.kind === 'homie-net' ? 'the HOMIE_NET line' : x.kind === 'src' ? `a script from ${x.src}` : `an inline script of ${x.bytes} B (sha256 ${x.sha256}, "${x.starts}…")`)).join(', ');
}

/* ------------------------------------------------------------------------------------------- measuring */

/** One run of build `v` on `device`, into `out` (homie-studio perf --runs 1). Returns the run, or throws. */
async function oneRun(root, s, device, out, pair = null) {
  mkdirSync(out, { recursive: true });
  const r = await cli(root, ['perf', s.game, '--url', s.url, '--device', device, '--runs', '1', '--seconds', String(s.seconds), '--cpu', String(s.cpu), '--out', out, '--max-load', String(s.maxLoad), ...(pair ? ['--pair', pair] : [])], { timeoutMs: 12 * 60_000 });
  const file = r.json?.runs?.[0] ? resolve(root, r.json.runs[0]) : null;
  if (!file || !existsSync(file)) throw new Error(`homie-studio perf gave no run: ${r.json?.why ?? r.err ?? `exit ${r.code}`}`);
  return { file, run: readJson(file) };
}

/** `runs` runs of one build per device (no alternation: the baseline). */
async function measureBuild(root, s, out, { runs = s.runs, profile = false } = {}) {
  const files = [];
  for (const device of s.devices) {
    if (profile) {
      const r = await cli(root, ['perf', s.game, '--url', s.url, '--device', device, '--runs', '1', '--seconds', String(s.seconds), '--cpu', String(s.cpu), '--out', out, '--max-load', String(s.maxLoad), '--profile'], { timeoutMs: 12 * 60_000 });
      if (!r.json?.runs?.length) throw new Error(`homie-studio perf --profile gave no run: ${r.json?.why ?? r.err}`);
      files.push(...r.json.runs.map((f) => resolve(root, f)));
      continue;
    }
    for (let k = 0; k < runs; k++) {
      log(`  ${device} run ${k + 1} of ${runs}`);
      files.push((await oneRun(root, s, device, out)).file);
    }
  }
  return files;
}

/**
 * Two builds in alternating order: before, after, after, before, … for each device, `runs` runs each. A run that
 * started on a busy computer is taken again (up to `runs` more per device), so both sides keep runs that count.
 */
async function alternate(root, s, dir, a, b, out) {
  for (const device of s.devices) {
    let extra = 0;
    for (let k = 0; k < s.runs; k++) {
      const order = k % 2 === 0 ? [a, b] : [b, a];
      for (const v of order) {
        installBuild(root, s.game, dir, v);
        await servedIs(s.url, s.game, dir, v, { added: s.pageAdded ?? null });
        log(`  ${device} ${k + 1}/${s.runs}: ${v === a ? 'before' : 'after'} (${v})`);
        // Both runs of a turn carry the same pair label: compare judges each after-run against its neighbour.
        const pair = `${device}-${k + 1}`;
        let got = await oneRun(root, s, device, join(out, v), pair);
        while (got.run.loaded && extra < s.runs) {
          extra++;
          log(`    that run started on a busy computer (load ${got.run.load?.before?.load1}); again`);
          got = await oneRun(root, s, device, join(out, v), pair);
        }
      }
    }
  }
}

/** The look of each build, from its runs' screenshots: brightness, contrast, detail, colour (playtest's pixels.mjs). */
async function looksOf(dirA, dirB) {
  let pixels;
  try { pixels = await import('../../playtest/scripts/lib/pixels.mjs'); } catch { return null; }
  if (spawnSync('ffmpeg', ['-version'], { encoding: 'utf8', timeout: 15_000, killSignal: 'SIGKILL' }).status !== 0) return { note: 'ffmpeg is not installed: the pictures were not measured (look at them)' };
  const median = (xs) => { const s = [...xs].sort((x, y) => x - y); return s.length ? s[Math.floor((s.length - 1) / 2)] : null; };
  const spread = (xs) => { const s = [...xs].sort((x, y) => x - y); return s.length > 2 ? s[Math.ceil(s.length * 0.75) - 1] - s[Math.floor(s.length * 0.25)] : 0; };
  const out = {};
  for (const device of ['computer', 'phone']) {
    const shots = (d) => (existsSync(d) ? readdirSync(d).filter((f) => new RegExp(`^${device}-\\d+-host\\.png$`).test(f)).map((f) => join(d, f)) : []);
    const sa = shots(dirA).map((f) => { try { return pixels.stats(pixels.decode(f, 320)); } catch { return null; } }).filter(Boolean);
    const sb = shots(dirB).map((f) => { try { return pixels.stats(pixels.decode(f, 320)); } catch { return null; } }).filter(Boolean);
    if (!sa.length || !sb.length) continue;
    const row = {};
    const floor = { mean: 6, sd: 4, edges: 0.01, saturation: 0.03 };
    for (const k of Object.keys(floor)) {
      const a = sa.map((x) => x[k]); const b = sb.map((x) => x[k]);
      const d = median(b) - median(a);
      row[k] = { before: median(a), after: median(b), moved: Math.abs(d) > Math.max(floor[k], 2 * spread(a)) };
    }
    out[device] = row;
  }
  const moved = Object.entries(out).flatMap(([d, row]) => Object.entries(row).filter(([, x]) => x.moved).map(([k, x]) => `${d} ${k} ${x.before} → ${x.after}`));
  return { devices: out, moved, note: moved.length ? `the screenshots differ beyond their own run-to-run spread: ${moved.join(', ')}. Look at them; if the game looks different, the change must say how (--looks)` : 'the screenshots measure the same (brightness, contrast, detail, colour) within their run-to-run spread' };
}

/* ------------------------------------------------------------------------------------------- baseline */

async function baseline() {
  const game = pos[1];
  const url = String(flags.get('url') ?? '').replace(/\/+$/, '');
  if (!game || !/^https?:\/\//.test(url)) throw new Error('usage: baseline <game> --url <site> (http://127.0.0.1:8787 from npm run dev)');
  const root = studioOrThrow();
  if (!existsSync(experienceJson(experienceDir(root, game)))) throw new Error(`no games/${game}/game.json in this studio`);
  diskOk(root);
  const version = await needsPerf(root);
  await alive(url, game);
  const devices = String(flags.get('devices') ?? 'computer,phone').split(',').map((d) => d.trim()).filter((d) => ['computer', 'phone'].includes(d));
  if (!devices.length) throw new Error('--devices: computer, phone or both');
  const num = (k, d, lo, hi) => Math.max(lo, Math.min(hi, Number(flags.get(k) ?? d) || d));
  const goal = String(flags.get('goal') ?? (devices.includes('phone') ? 'phone.host.frame.p95' : 'computer.host.frame.p95'));
  const stamp = new Date().toISOString().replace(/[-:]/g, '').replace(/\..*/, '');
  const name = `loop-${stamp}`;
  const dir = join(loopsDir(root, game), name);
  mkdirSync(dir, { recursive: true });
  const s = { v: 1, game, url, goal, devices, runs: num('runs', 6, 3, 20), seconds: num('seconds', 15, 5, 120), cpu: num('cpu', 4, 1, 20), min: num('min', 3, 0.5, 50), maxLoad: num('max-load', 0.8, 0.1, 10), studio: version, created: new Date().toISOString(), kept: 'base', history: [] };
  saveSession(dir, s);
  writeJson(join(loopsDir(root, game), 'current.json'), { loop: name });
  log(`… building ${game} (with its source map)`);
  const b = await cli(root, ['build', game, '--maps'], { timeoutMs: 15 * 60_000 });
  if (!b.json?.ok) throw new Error(`the build failed: ${b.json?.why ?? b.err}`);
  keepBuild(root, game, dir, 'base');
  keepSource(root, game, dir, 'base');
  // The scripts the site adds to the game page (HOMIE_NET, and any of the studio's own Worker): every later build must
  // be served with the same ones.
  s.pageAdded = await servedIs(url, game, dir, 'base');
  saveSession(dir, s);
  log('… the two-browser check (homie-studio check): two fresh browsers must finish a round together');
  const ck = await cli(root, ['check', game, '--url', url], { timeoutMs: 8 * 60_000 });
  s.baseCheck = { ok: Boolean(ck.json?.ok), why: ck.json?.why ?? (ck.json ? null : ck.err), seconds: ck.json?.totalMs ? Math.round(ck.json.totalMs / 1000) : null };
  saveSession(dir, s);
  if (!s.baseCheck.ok) throw new Error(`the game does not pass its own two-browser check before any change (${s.baseCheck.why}): fix that first; a faster game that does not work is not faster`);
  log(`… measuring the build to beat: ${s.runs} runs per device (${s.devices.join(', ')}), ${s.seconds} s each`);
  await measureBuild(root, s, join(dir, 'runs', 'base'));
  log('… one profiled run per device (a window of its own: a profiler slows what it watches)');
  await measureBuild(root, s, join(dir, 'profile', 'base'), { profile: true });
  const sizes = await cli(root, ['perf', 'sizes', game]);
  if (sizes.json?.ok) writeJson(join(dir, 'sizes-base.json'), sizes.json);
  // Each run was its own `homie-studio perf` call, so the medians are taken here, over every run in the folder.
  const summary = summaryFromRuns(join(dir, 'runs', 'base'));
  writeFileSync(join(dir, 'BASELINE.md'), baselineMd(s, summary, profiles(join(dir, 'profile', 'base')), sizes.json, s.devices.map((d) => fetchedOf(join(dir, 'runs', 'base'), d))));
  return { ok: true, command: 'baseline', game, loop: dir, goal: s.goal, check: `passed in ${s.baseCheck.seconds} s`, page: `the build's page plus ${addedSaid(s.pageAdded)} from the site`, baseline: join(dir, 'BASELINE.md'), headline: headline(s, summary), next: 'read BASELINE.md (where the time goes, what to try), make ONE change, then: perf.mjs try <game> --name "<what it does>" --looks same --plays same' };
}

/** A summary of the runs in a folder written by several single-run calls (each wrote its own summary.json). */
function summaryFromRuns(folder) {
  const runs = existsSync(folder) ? readdirSync(folder).filter((f) => /^(computer|phone)-\d+\.json$/.test(f)).map((f) => readJson(join(folder, f))).filter((r) => r?.kind === 'homie-perf-run') : [];
  const by = {};
  for (const r of runs.filter((x) => !x.blocked && !x.loaded)) {
    for (const b of r.browsers ?? []) {
      const p = `${r.device}.${b.role}`;
      const put = (k, v) => { if (Number.isFinite(v)) (by[`${p}.${k}`] ??= []).push(v); };
      put('frame.p50', b.frames?.p50); put('frame.p95', b.frames?.p95); put('frame.p99', b.frames?.p99); put('frame.over33', b.frames?.over33); put('frame.over50', b.frames?.over50);
      put('work.mean', b.work?.mean); put('work.p95', b.work?.p95); put('busy', b.main?.busyPerFrame); put('heap', b.heap?.afterGcMb); put('heap.growth', b.heap?.gcGrowthMbPerMin);
      put('load.look', b.load?.lookMs); put('load.firstFrame', b.load?.firstFrameMs); put('load.playable', b.load?.playableMs); put('load.ready', b.load?.readyMs); put('load.gameKb', b.load?.gameKb); put('load.prePlayKb', b.load?.prePlay?.kb); put('render.calls', b.render?.drawCalls?.median); put('render.triangles', b.render?.triangles?.median);
      put('net.msgsOut', b.net?.msgsOut); put('net.msgsIn', b.net?.msgsIn); put('net.kbOut', b.net?.kbOut); put('net.kbIn', b.net?.kbIn);
    }
  }
  const med = (xs) => { const s = [...xs].sort((a, b) => a - b); const q = (p) => { const at = (s.length - 1) * p; const lo = Math.floor(at); return s[lo] + (s[Math.ceil(at)] - s[lo]) * (at - lo); }; return { n: s.length, median: +q(0.5).toFixed(3), q1: +q(0.25).toFixed(3), q3: +q(0.75).toFixed(3), spread: q(0.5) ? +((q(0.75) - q(0.25)) / Math.abs(q(0.5))).toFixed(4) : null }; };
  const slow = runs.map((r) => r.cpuMeasured).filter(Number.isFinite).sort((x, y) => x - y);
  // The arrival each role reported (homie-studio perf, from the play page's __shell.arrival): who was to say the
  // game is playable, and the worst lateness of the game's own word under an automatic arrival.
  const arrival = {};
  for (const r of runs.filter((x) => !x.blocked && !x.loaded)) for (const b of r.browsers ?? []) {
    const a = b.load?.arrival; if (!a) continue;
    const row = (arrival[`${r.device}.${b.role}`] ??= { mode: null, lateMs: null });
    row.mode ??= a.mode ?? null;
    if (Number.isFinite(a.lateMs)) row.lateMs = Math.max(row.lateMs ?? 0, a.lateMs);
  }
  return { arrival, cpuMeasured: slow.length ? slow[Math.floor((slow.length - 1) / 2)] : null, runs: runs.length, counted: runs.filter((x) => !x.blocked && !x.loaded).length, devices: [...new Set(runs.map((r) => r.device))], renderers: [...new Set(runs.map((r) => r.renderer).filter(Boolean))], machine: runs[0]?.machine ?? null, chrome: runs[0]?.chrome ?? null, deviceLabels: Object.fromEntries(runs.map((r) => [r.device, r.deviceLabel])), load: runs.map((r) => ({ device: r.device, before: r.load?.before?.load1 ?? null, after: r.load?.after?.load1 ?? null, busyPct: r.load?.busyPct ?? null, loaded: Boolean(r.loaded), blocked: r.blocked ?? null })), metrics: Object.fromEntries(Object.entries(by).sort(([a], [b]) => a.localeCompare(b)).map(([k, xs]) => [k, med(xs)])) };
}

/** The profiled runs in a folder: per device and role, the summary `homie-studio perf --profile` wrote. */
function profiles(folder) {
  if (!existsSync(folder)) return [];
  return readdirSync(folder).filter((f) => /^(computer|phone)-\d+\.json$/.test(f)).map((f) => readJson(join(folder, f))).filter(Boolean).flatMap((r) => (r.browsers ?? []).filter((b) => b.profile).map((b) => ({ device: r.device, role: b.role, ...b.profile, file: join(folder, b.profile.file) })));
}

const fmt = (x, unit = '') => (x === null || x === undefined ? '–' : `${x}${unit}`);

/** Beside control-ready: the game's own "ready" and the arrival mode (the same words as homie-studio perf's headline). */
function readyWords(a, readyMs) {
  if (!a?.mode && readyMs === undefined) return '';
  const said = readyMs !== undefined ? `the game said ready at ${readyMs} ms` : 'the game never said ready itself';
  return `, ${said} (arrival ${a?.mode ?? 'unknown'}${Number.isFinite(a?.lateMs) ? `: ${a.lateMs} ms after the cover had lifted` : ''})`;
}

function headline(s, summary) {
  const out = [];
  for (const d of s.devices) for (const role of ['host', 'replica']) {
    const m = (k) => summary.metrics?.[`${d}.${role}.${k}`]?.median;
    if (m('frame.p50') === undefined) continue;
    out.push(`${d} ${role}: frames ${fmt(m('frame.p50'))}/${fmt(m('frame.p95'))} ms (median/p95), ${fmt(m('frame.over50'), '%')} over 50 ms; game JS ${fmt(m('work.mean'))} ms a frame; main thread ${fmt(m('busy'))} ms a frame; first look ${fmt(m('load.look'))} ms, playable (control-ready) ${fmt(m('load.playable'))} ms${readyWords(summary.arrival?.[`${d}.${role}`], m('load.ready'))}; heap ${fmt(m('heap'))} MB; netplay ${fmt(m('net.msgsOut'))} out, ${fmt(m('net.msgsIn'))} in a second`);
  }
  return out;
}

/** What to try first, from the numbers: plain rules, each saying which number it read. */
function hints(s, summary, profs, sizes) {
  const h = [];
  const m = (k) => summary.metrics?.[k]?.median;
  for (const d of s.devices) {
    const p95 = m(`${d}.host.frame.p95`); const over50 = m(`${d}.host.frame.over50`); const busy = m(`${d}.host.busy`); const p50 = m(`${d}.host.frame.p50`);
    if (p95 !== undefined && p95 <= 17.5) h.push(`${d}: frames already keep pace with the display (p95 ${p95} ms against 16.7). A faster frame cannot show on this profile; aim at the work per frame (\`${d}.host.busy\`: ${busy} ms of main thread a frame), which is battery and headroom on slower phones${d === 'phone' ? `, or measure a slower phone (baseline --cpu ${Math.min(20, s.cpu * 2)})` : ''}.`);
    else if (p50 !== undefined && p50 > 18) h.push(`${d}: the median frame takes ${p50} ms (under 60 fps): the steady cost per frame is the problem. Start from the hottest game function in the profile below.`);
    if (over50 !== undefined && over50 >= 0.5) h.push(`${d}: ${over50}% of frames take over 50 ms (hitches anyone sees). Look for long tasks, garbage collection and work that runs only now and then (a spawn, a big message, a texture upload).`);
  }
  for (const p of profs) {
    if (p.gcPct >= 8) h.push(`${p.device} ${p.role}: ${p.gcPct}% of the busy time is garbage collection: something allocates every frame (arrays, objects, closures, strings in a loop).`);
    const top = p.top?.find((t) => t.game);
    if (top) h.push(`${p.device} ${p.role}: the hottest game function is ${top.name} (${top.where}), ${top.selfPct}% of the busy time itself and ${top.totalPct}% with what it calls.`);
  }
  for (const d of s.devices) {
    const g = m(`${d}.host.heap.growth`);
    if (g === undefined || g <= 1) continue;
    // A short window mostly sees buffers filling: the port probe alone keeps its last 4,000 frames (about a minute).
    h.push(s.seconds < 90
      ? `${d}: the heap grew ${g} MB a minute after garbage collection over ${s.seconds} s windows. Over a short window that is often a buffer filling (the port probe keeps its last 4,000 frames, about a minute): measure once with \`homie-studio perf ${s.game} --device ${d} --seconds 180\`; growth that keeps going after the first minute is a leak (a list that only grows, listeners added every round).`
      : `${d}: the heap grows ${g} MB a minute after garbage collection: something is kept that should not be (a list that only grows, listeners added every round).`);
  }
  if (sizes?.ok) h.push(...sizeHints(sizes));
  return h;
}

/** What a browser actually fetched before it was playable, from the first counted run of a device (its host). */
function fetchedOf(folder, device) {
  if (!existsSync(folder)) return null;
  const runs = readdirSync(folder).filter((f) => new RegExp(`^${device}-\\d+\\.json$`).test(f)).sort().map((f) => readJson(join(folder, f))).filter((r) => r && !r.blocked && !r.loaded);
  const host = runs[0]?.browsers?.find((b) => b.role === 'host');
  return host?.load ? { device, ...host.load } : null;
}

function baselineMd(s, summary, profs, sizes, fetched = []) {
  const L = [`# Perf baseline: ${s.game}`, '', `${s.created} · goal \`${s.goal}\` (lower is better) · ${s.runs} runs per device, ${s.seconds} s windows · @homie-rocks/studio ${s.studio}`, ''];
  L.push(`Measured on ${summary.machine?.cpu ?? '?'} (${summary.machine?.cores ?? '?'} cores), ${summary.chrome ?? 'Chrome'}, ${summary.renderers?.join(', ') || 'renderer unknown'}.`, '');
  for (const [d, label] of Object.entries(summary.deviceLabels ?? {})) L.push(`- **${d}**: ${label}`);
  if (summary.cpuMeasured) L.push(`- The phone's throttle measured **${summary.cpuMeasured}x** here (the median run): its work is that much slower than this computer's, not ${s.cpu}x.`);
  if (s.pageAdded) L.push(`- The game page as the site serves it is the build's page plus ${addedSaid(s.pageAdded)}: the site's, not the build's, and the same for every build this loop measures. Before every run the page is checked against the build's (every script and the markup) and every other file by SHA-256.`);
  L.push('', '## The numbers (median of the runs; the spread is the middle half as a share of the median)', '', '| metric | median | spread |', '| --- | --- | --- |');
  const keep = /\.(frame\.(p50|p95|p99|over50)|work\.(mean|p95)|busy|heap|heap\.growth|load\.(look|firstFrame|playable|gameKb|prePlayKb)|render\.(calls|triangles)|net\.(msgsOut|msgsIn|kbOut|kbIn))$/;
  for (const [k, v] of Object.entries(summary.metrics ?? {})) if (keep.test(k)) L.push(`| \`${k}\` | ${v.median} | ${v.spread === null ? '–' : `${Math.round(v.spread * 100)}%`} |`);
  L.push('', 'A change has to beat the spread to count: `try` measures both builds in turns and only keeps a change that is better beyond the noise.', '');
  L.push('## Load during the runs', '', ...summary.load.map((x, i) => `- run ${i + 1} (${x.device}): load ${x.before} → ${x.after}, cores ${x.busyPct}% busy${x.loaded ? ' — **started on a busy computer, left out**' : ''}${x.blocked ? ` — **blocked: ${x.blocked}**` : ''}`), '');
  L.push('## Where the time goes (one profiled run per device)', '');
  for (const p of profs) {
    L.push(`### ${p.device} · ${p.role}`, '', `${p.seconds} s profiled: ${p.idlePct}% idle; of the busy time, the game's own code ${p.gamePct}%, Chrome's own work ("(program)": drawing, compositing) ${p.programPct}%, garbage collection ${p.gcPct}%. ${p.mapped ? 'Read through the build\'s source map.' : 'No source map (a static game, or a build without --maps).'} Profile: \`${relative(process.cwd(), p.file)}\` (Chrome DevTools, Performance, opens it).`, '', '| self | with callees | function | where |', '| --- | --- | --- | --- |');
    for (const t of p.top.slice(0, 12)) L.push(`| ${t.selfPct}% | ${t.totalPct}% | ${t.name.replace(/\|/g, '/')} | ${t.where} |`);
    L.push('');
  }
  if (sizes?.ok) {
    const kb = (b) => `${(b / 1024).toFixed(1)} KB`;
    L.push('## What a player downloads', '');
    for (const f of fetched.filter((x) => x && Number.isFinite(x.requests))) L.push(`Fetched before playable (${f.device}, the host's first run): ${f.requests} requests, ${f.kb} KB on the wire, the game's own files ${f.gameKb} KB: ${(f.biggest ?? []).slice(0, 6).map((b) => `${b.path} ${b.kb} KB`).join(', ')}.`, '');
    L.push(`The built game (every file the site serves for it; the landing page's art is not counted): ${sizes.total.files} files, ${kb(sizes.total.bytes)} (${kb(sizes.total.gzip)} gzipped); JavaScript ${kb(sizes.js.bytes)} (${kb(sizes.js.gzip)} gzipped).`, '', '| bytes | gzipped | file |', '| --- | --- | --- |', ...sizes.biggest.slice(0, 10).map((f) => `| ${kb(f.bytes)} | ${kb(f.gzip)} | ${f.path} |`), '');
    if (sizes.modules) L.push('Bundle modules:', '', ...sizes.modules.top.slice(0, 8).map((m) => `- ${kb(m.bytes)} ${m.module}`), '');
  }
  const hs = hints(s, summary, profs, sizes);
  L.push('## What to try first', '', ...(hs.length ? hs.map((x) => `- ${x}`) : ['- Nothing stands out in the numbers. Read the profile from the top.']), '');
  L.push('One change at a time, small enough to say in one line, and never one that changes how the game looks or plays unless the person asked for that trade (then say so with `--looks` / `--plays`).', '');
  return `${L.join('\n')}\n`;
}

/* ------------------------------------------------------------------------------------------- try */

async function tryChange() {
  const game = pos[1];
  const name = String(flags.get('name') ?? '').trim();
  const looks = flags.get('looks'); const plays = flags.get('plays');
  // --measure: what this change costs or saves, said in numbers, and nothing reverted (the person keeps it for its feel).
  const measureOnly = flags.has('measure');
  if (!game || !name || looks === undefined || plays === undefined || looks === true || plays === true) throw new Error('usage: try <game> --name "<the one change>" --looks same|"<how it looks now>" --plays same|"<how it plays now>" (say both, every time: a faster game that looks or plays differently has to say so)');
  const root = studioOrThrow();
  diskOk(root);
  const { dir, s } = currentLoop(root, game);
  await alive(s.url, game);
  const changed = sourceDiff(root, game, dir, s.kept);
  if (!changed.length) throw new Error(`games/${game}/ is the same as the kept build (${s.kept}): make the change first`);
  const n = s.history.length + 1;
  const v = `c${n}`;
  const exp = join(dir, 'experiments', `${String(n).padStart(2, '0')}-${slugify(name).slice(0, 40)}`);
  mkdirSync(exp, { recursive: true });
  log(`… change ${n}: ${name} (${changed.map((c) => `${c.how} ${c.file}`).join(', ')})`);
  const b = await cli(root, ['build', game, '--maps'], { timeoutMs: 15 * 60_000 });
  const goal = flags.get('goal') && flags.get('goal') !== true ? String(flags.get('goal')) : s.goal;
  const rec = { n, v, name, goal, looks: String(looks), plays: String(plays), files: changed, at: new Date().toISOString(), against: s.kept, folder: relative(dir, exp) };
  const finish = (verdict, why, extra = {}) => {
    const r = { ...rec, verdict, why, ...extra };
    writeJson(join(exp, 'result.json'), r);
    writeFileSync(join(exp, 'RESULT.md'), resultMd(s, r));
    s.history.push({ n, v, name, verdict, why, looks: r.looks, plays: r.plays, folder: rec.folder, aim: goal, goal: r.compare?.goal ?? null });
    if (verdict === 'keep') s.kept = v;
    saveSession(dir, s);
    return r;
  };
  if (!b.json?.ok) {
    if (!measureOnly) { restoreSource(root, game, dir, s.kept); installBuild(root, game, dir, s.kept); }
    const r = finish(measureOnly ? 'measured' : 'revert', `it did not build: ${b.json?.why ?? b.err}`);
    return { ok: false, command: 'try', game, verdict: measureOnly ? 'MEASURED' : 'REVERT', why: r.why, result: join(exp, 'RESULT.md') };
  }
  keepBuild(root, game, dir, v);
  keepSource(root, game, dir, v);
  writeFileSync(join(exp, 'change.patch'), patchOf(dir, game, s.kept, v, root));
  await servedIs(s.url, game, dir, v, { added: s.pageAdded ?? null });
  log('… the two-browser check on the changed build');
  const ck = await cli(root, ['check', game, '--url', s.url], { timeoutMs: 8 * 60_000 });
  const check = { ok: Boolean(ck.json?.ok), why: ck.json?.why ?? (ck.json ? null : ck.err), seconds: ck.json?.totalMs ? Math.round(ck.json.totalMs / 1000) : null };
  if (!check.ok && measureOnly) {
    const r = finish('measured', `the two-browser check failed with this change (${check.why}): fix that before anything else`, { check });
    return { ok: false, command: 'try', game, verdict: 'MEASURED', why: r.why, result: join(exp, 'RESULT.md') };
  }
  if (!check.ok) {
    const restored = restoreSource(root, game, dir, s.kept); installBuild(root, game, dir, s.kept); await servedIs(s.url, game, dir, s.kept);
    const r = finish('revert', `the two-browser check failed with this change (${check.why}): a faster game that does not work is not faster`, { check, restored });
    return { ok: true, command: 'try', game, verdict: 'REVERT', why: r.why, result: join(exp, 'RESULT.md'), restored: restored.map((x) => x.file) };
  }
  log(`… measuring ${s.kept} (before) and ${v} (after) in turns, ${s.runs} runs each per device`);
  await alternate(root, s, dir, s.kept, v, join(exp, 'runs'));
  const cmp = await cli(root, ['perf', 'compare', join(exp, 'runs', s.kept), join(exp, 'runs', v), '--goal', goal, '--min', String(s.min)]);
  if (!cmp.json?.ok) throw new Error(`perf compare failed: ${cmp.json?.why ?? cmp.err}`);
  const look = await looksOf(join(exp, 'runs', s.kept), join(exp, 'runs', v));
  const compare = { verdict: cmp.json.verdict, why: cmp.json.why, goal: pick(cmp.json.goal), guards: cmp.json.guards.map(pick), left: cmp.json.left, file: relative(dir, cmp.json.file) };
  if (cmp.json.verdict === 'blocked') {
    installBuild(root, game, dir, s.kept); await servedIs(s.url, game, dir, s.kept);
    // Nothing decided: the change stays in games/<game>/ so it can be measured again when the computer is calmer.
    writeJson(join(exp, 'result.json'), { ...rec, verdict: 'blocked', why: cmp.json.why, check, compare, look });
    return { ok: false, command: 'try', game, verdict: 'BLOCKED', why: cmp.json.why, next: 'the change is still in games/; run try again with the same --name when the computer is calmer, or revert', result: join(exp, 'result.json') };
  }
  if (measureOnly) {
    installBuild(root, game, dir, v); await servedIs(s.url, game, dir, v);
    const r = finish('measured', `${cmp.json.verdict}: ${cmp.json.why}`, { check, compare, look });
    return {
      ok: true, command: 'try', game, change: name, verdict: 'MEASURED', against: s.kept, why: r.why,
      goal: `${compare.goal.metric}: ${compare.goal.why}`,
      guardsWorse: compare.guards.filter((g) => g.verdict === 'worse').map((g) => `${g.metric}: ${g.why}`),
      looks: look?.note ?? null, declared: { looks: r.looks, plays: r.plays }, result: join(exp, 'RESULT.md'),
      next: 'the change stays in games/ and is served; say what it costs in these numbers, and commit it if the person keeps it',
    };
  }
  const keep = cmp.json.verdict === 'better';
  let restored = [];
  if (keep) { installBuild(root, game, dir, v); await servedIs(s.url, game, dir, v); }
  else { restored = restoreSource(root, game, dir, s.kept); installBuild(root, game, dir, s.kept); await servedIs(s.url, game, dir, s.kept); }
  const why = keep ? cmp.json.why : cmp.json.verdict === 'worse' ? cmp.json.why : `not better beyond the noise: ${cmp.json.why}`;
  const r = finish(keep ? 'keep' : 'revert', why, { check, compare, look, restored });
  return {
    ok: true, command: 'try', game, change: name, verdict: keep ? 'KEEP' : 'REVERT', why,
    goal: `${compare.goal.metric}: ${compare.goal.why}`,
    guardsWorse: compare.guards.filter((g) => g.verdict === 'worse').map((g) => `${g.metric}: ${g.why}`),
    looks: look?.note ?? null,
    declared: { looks: r.looks, plays: r.plays },
    ...(keep ? {} : { restored: restored.map((x) => `${x.how === 'added' ? 'removed' : 'restored'} games/${game}/${x.file}`) }),
    result: join(exp, 'RESULT.md'),
    next: keep ? 'this build is now the one to beat; the next change, or report' : 'games/ is back to the kept build; try another change, or report',
  };
}

/** A patch bigger than this goes into a report as a list of files, not as a diff. */
const PATCH_MAX = 256 * 1024;

/** Every file that differs between two kept sources, with sizes and SHA-256 on each side. */
function filesBetween(dir, a, b) {
  const da = join(dir, 'sources', a);
  const db = join(dir, 'sources', b);
  const fa = new Set(listFiles(da));
  const fb = new Set(listFiles(db));
  const out = [];
  for (const f of [...new Set([...fa, ...fb])].sort()) {
    const ba = fa.has(f) ? readFileSync(join(da, f)) : null;
    const bb = fb.has(f) ? readFileSync(join(db, f)) : null;
    if (ba && bb && sha256(ba) === sha256(bb)) continue;
    out.push({ file: f, how: !ba ? 'added' : !bb ? 'removed' : 'changed', before: ba?.length ?? null, after: bb?.length ?? null, shaBefore: ba ? sha256(ba).slice(0, 16) : null, shaAfter: bb ? sha256(bb).slice(0, 16) : null });
  }
  return out;
}

const pick = (x) => ({ metric: x.metric, verdict: x.verdict, before: x.before?.median ?? null, after: x.after?.median ?? null, change: x.change, ci: x.ci, p: x.p, pWorse: x.pWorse, n: x.n ?? null, why: x.why });

function resultMd(s, r) {
  const L = [`# Change ${r.n}: ${r.name}`, '', `**${r.verdict.toUpperCase()}**: ${r.why}`, '', `Goal \`${r.goal ?? s.goal}\` · against ${r.against} · ${r.at} · files: ${r.files.map((f) => `${f.how} \`${f.file}\``).join(', ')}`, ''];
  L.push(`- Looks: ${r.looks === 'same' ? 'the same (said by the change)' : `**different: ${r.looks}**`}${r.look?.note ? `; screenshots: ${r.look.note}` : ''}`);
  L.push(`- Plays: ${r.plays === 'same' ? 'the same (said by the change)' : `**different: ${r.plays}**`}`);
  if (r.check) L.push(`- Two-browser check: ${r.check.ok ? `passed (${r.check.seconds} s)` : `**failed**: ${r.check.why}`}`);
  if (r.compare) {
    L.push('', `## ${r.compare.goal.metric} (the goal)`, '', r.compare.goal.why, '', '## Guards', '', '| metric | verdict | before → after |', '| --- | --- | --- |');
    for (const g of r.compare.guards) L.push(`| \`${g.metric}\` | ${g.verdict} | ${g.why.replace(/\|/g, '/')} |`);
    if (r.compare.left.before + r.compare.left.after) L.push('', `Left out: ${r.compare.left.before} run(s) before and ${r.compare.left.after} after (blocked, or started on a busy computer).`);
  }
  if (r.restored?.length) L.push('', `Reverted: ${r.restored.map((x) => `${x.how === 'added' ? 'removed' : 'restored'} \`games/${s.game}/${x.file}\``).join(', ')}.`);
  L.push('', 'The change: `change.patch` in this folder. The runs: `runs/`.', '');
  return `${L.join('\n')}\n`;
}

/* ------------------------------------------------------------------------------------------- revert, status */

async function revert() {
  const game = pos[1];
  if (!game) throw new Error('usage: revert <game>');
  const root = studioOrThrow();
  const { dir, s } = currentLoop(root, game);
  const restored = restoreSource(root, game, dir, s.kept);
  installBuild(root, game, dir, s.kept);
  await servedIs(s.url, game, dir, s.kept).catch(() => {});
  return { ok: true, command: 'revert', game, kept: s.kept, restored: restored.map((x) => `${x.how === 'added' ? 'removed' : 'restored'} games/${game}/${x.file}`) };
}

function status() {
  const game = pos[1];
  if (!game) throw new Error('usage: status <game>');
  const root = studioOrThrow();
  const { dir, s } = currentLoop(root, game);
  const pending = sourceDiff(root, game, dir, s.kept);
  return { ok: true, command: 'status', game, loop: dir, goal: s.goal, devices: s.devices, runs: s.runs, kept: s.kept, changes: s.history.map((h) => `${h.n}. ${h.verdict.toUpperCase()} ${h.name}: ${h.goal ? `${h.goal.before} → ${h.goal.after} (${h.goal.change === null ? '?' : `${(h.goal.change * 100).toFixed(1)}%`}, p ${h.goal.p})` : h.why}`), uncommittedChange: pending.length ? pending.map((x) => `${x.how} ${x.file}`) : null };
}

function goals() {
  return {
    ok: true,
    command: 'goals',
    metrics: [
      '<device>.<role>.<metric>: device computer or phone, role host (runs the rules, bots and snapshots) or replica; all lower is better',
      'frame.p50 / frame.p95 / frame.p99 / frame.max: ms between animation frames (16.7 at 60 Hz). p95 is what stutter feels like',
      'frame.over33 / frame.over50: % of frames slower than 33 ms (a dropped frame twice) / 50 ms (a hitch anyone sees)',
      'work.mean / work.p95: ms of the game\'s JavaScript inside each animation frame',
      'busy: ms of the page\'s main thread per frame (scripts, style, layout, socket messages): CPU per frame, battery',
      'script: ms of script a second',
      'heap / heap.growth: MB of JavaScript heap after a garbage collection / its growth in MB a minute',
      'load.look / load.firstFrame / load.seated / load.playable: ms from opening the page (look: the first meaningful frame, the play page\'s arrival card with the game\'s title and art; playable: control-ready, which is seated, the body drawn, the card lifted); load.ready: ms to the game\'s OWN word that it was ready (net.playable()), absent when it never said so; with the arrival mode `auto` and a ready later than playable, players are shown the game before it is ready: declare arrival: \'game\' (NETPLAY.md section 21); load.gameKb: KB of the game\'s files on the wire; load.prePlayKb: KB really fetched (every request, bytes of those still in flight included) up to playable: measured first-play traffic, which is not the shipped payload under bytes.*',
      'render.calls / render.triangles: the renderer\'s own draw calls and triangles while playing, when the game exposes them (exposePort extra: drawCalls, triangles): measured runtime scene cost, not the asset inventory\'s estimate; absent when not exposed',
      'net.msgsOut / net.msgsIn / net.kbOut / net.kbIn: netplay messages and KB a second on the room\'s socket',
      'bytes.total / bytes.gzip / bytes.js / bytes.jsGzip: the built game on disk (no device, no role; the same every run)',
    ],
    examples: ['phone.host.frame.p95 (stutter on a phone)', 'phone.host.busy (CPU per frame when frames already keep up)', 'phone.host.load.playable (time to play on 4G)', 'phone.host.load.look (time to the first meaningful frame)', 'computer.host.net.kbOut (the host\'s upload)', 'bytes.jsGzip (the download)'],
  };
}

/* ------------------------------------------------------------------------------------------- report */

async function report() {
  const game = pos[1];
  if (!game) throw new Error('usage: report <game> [--final-runs <n>]');
  const root = studioOrThrow();
  const { dir, s } = currentLoop(root, game);
  const kept = s.history.filter((h) => h.verdict === 'keep');
  const outDir = join(root, 'perf', game);
  const ba = join(outDir, 'before-after');
  rmSync(ba, { recursive: true, force: true });
  mkdirSync(ba, { recursive: true });
  let final = null;
  if (kept.length === 1) {
    // One change kept: its own comparison was the first build against it.
    const r = readJson(join(dir, kept[0].folder, 'result.json'));
    final = { from: kept[0].folder, compare: r.compare, runsBefore: join(dir, kept[0].folder, 'runs', 'base'), runsAfter: join(dir, kept[0].folder, 'runs', s.kept) };
  } else if (kept.length > 1) {
    await alive(s.url, game);
    const runs = Number(flags.get('final-runs') ?? s.runs) || s.runs;
    log(`… ${kept.length} changes kept: measuring the first build and the kept one against each other (${runs} runs each per device)`);
    const fdir = join(dir, 'final');
    rmSync(fdir, { recursive: true, force: true });
    await alternate(root, { ...s, runs }, dir, 'base', s.kept, fdir);
    installBuild(root, game, dir, s.kept);
    await servedIs(s.url, game, dir, s.kept);
    // The loop's goal, with every kept change's own goal held as a guard.
    const aims = [...new Set(kept.map((k) => k.aim).filter((a) => a && a !== s.goal))];
    const cmp = await cli(root, ['perf', 'compare', join(fdir, 'base'), join(fdir, s.kept), '--goal', s.goal, '--min', String(s.min), ...(aims.length ? ['--also', aims.join(',')] : [])]);
    if (cmp.json?.ok) final = { from: 'final', compare: { verdict: cmp.json.verdict, why: cmp.json.why, goal: pick(cmp.json.goal), guards: cmp.json.guards.map(pick), left: cmp.json.left }, runsBefore: join(fdir, 'base'), runsAfter: join(fdir, s.kept) };
  }
  // Pictures: the host's screenshot from the middle run of each side, per device (JPEG when ffmpeg is here).
  const pictures = [];
  const shotFrom = (folder, device) => { if (!folder || !existsSync(folder)) return null; const f = readdirSync(folder).filter((x) => new RegExp(`^${device}-\\d+-host\\.png$`).test(x)).sort(); return f.length ? join(folder, f[Math.floor((f.length - 1) / 2)]) : null; };
  const before = final?.runsBefore ?? join(dir, 'runs', 'base');
  for (const device of s.devices) {
    for (const [side, folder] of [['before', before], ['after', final?.runsAfter ?? null]]) {
      const src = shotFrom(folder, device);
      if (!src) continue;
      const jpg = join(ba, `${device}-${side}.jpg`);
      const ff = spawnSync('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', '-i', src, '-q:v', '4', jpg], { timeout: CHILD_TIMEOUT_MS, killSignal: 'SIGKILL' });
      if (ff.status === 0 && existsSync(jpg)) pictures.push(relative(outDir, jpg));
      else { const png = join(ba, `${device}-${side}.png`); cpSync(src, png); pictures.push(relative(outDir, png)); }
    }
  }
  // A kept change as a patch; a change too big to read as one (a minified library, a new texture) as a list of its
  // files with their sizes and SHA-256 before and after, so the studio's history never carries megabytes of diff.
  const keepPatch = (text, a, b, file) => {
    if (Buffer.byteLength(text) <= PATCH_MAX) { writeFileSync(`${file}.patch`, text); return `${file}.patch`; }
    const rows = filesBetween(dir, a, b).map((f) => `${f.how.padEnd(8)} games/${game}/${f.file}  ${f.before ?? '-'} B → ${f.after ?? '-'} B  sha256 ${f.shaBefore ?? '-'} → ${f.shaAfter ?? '-'}`);
    writeFileSync(`${file}.files.txt`, `The change, as files (its diff is ${(Buffer.byteLength(text) / 1048576).toFixed(1)} MB; the whole diff stays on this computer in .perf/${game}/):\n\n${rows.join('\n')}\n`);
    return `${file}.files.txt`;
  };
  const patches = new Map();
  for (const k of kept) { const p = join(dir, k.folder, 'change.patch'); if (existsSync(p)) patches.set(k.n, relative(outDir, keepPatch(readFileSync(p, 'utf8'), readJson(join(dir, k.folder, 'result.json'))?.against ?? 'base', k.v, join(ba, `${String(k.n).padStart(2, '0')}-${slugify(k.name).slice(0, 40)}`)))); }
  if (kept.length > 1) keepPatch(patchOf(dir, game, 'base', s.kept, root), 'base', s.kept, join(ba, 'all-kept'));
  const baseSummary = summaryFromRuns(join(dir, 'runs', 'base'));
  const profs = profiles(join(dir, 'profile', 'base'));
  // Both builds' files measured the same way now (the first build put back for a moment), the kept one left serving.
  const sizesOf = async (v) => { installBuild(root, game, dir, v); const sz = await cli(root, ['perf', 'sizes', game]); return sz.json?.ok ? sz.json : null; };
  const sizesBase = await sizesOf('base');
  const sizesKept = kept.length ? await sizesOf(s.kept) : null;
  installBuild(root, game, dir, s.kept);
  const results = s.history.map((h) => readJson(join(dir, h.folder, 'result.json')) ?? h);
  // The throttle's real slow-down, from every phone run of the loop that measured it (the median).
  const measured = [];
  const walk = (d) => { if (!existsSync(d)) return; for (const e of readdirSync(d, { withFileTypes: true })) { if (e.isDirectory()) walk(join(d, e.name)); else if (/^phone-\d+\.json$/.test(e.name)) { const r = readJson(join(d, e.name)); if (Number.isFinite(r?.cpuMeasured)) measured.push(r.cpuMeasured); } } };
  walk(dir);
  measured.sort((x, y) => x - y);
  const numbers = {
    v: 1, game, goal: s.goal, devices: s.devices, runs: s.runs, seconds: s.seconds, phoneCpuSlowdown: s.cpu, minChange: s.min / 100,
    machine: baseSummary.machine, chrome: baseSummary.chrome, phoneCpuMeasured: measured.length ? { median: measured[Math.floor((measured.length - 1) / 2)], min: measured[0], max: measured[measured.length - 1], runs: measured.length } : null, renderers: baseSummary.renderers, deviceLabels: baseSummary.deviceLabels,
    baseline: Object.fromEntries(Object.entries(baseSummary.metrics).map(([k, v]) => [k, { median: v.median, spread: v.spread, n: v.n }])),
    final: final ? { ...final.compare, runsBefore: undefined, runsAfter: undefined } : null,
    sizes: { before: sizesBase ? { total: sizesBase.total, js: sizesBase.js } : null, after: sizesKept ? { total: sizesKept.total, js: sizesKept.js } : null },
    changes: results.map((r) => ({ n: r.n, name: r.name, verdict: r.verdict, why: r.why, looks: r.looks, plays: r.plays, check: r.check ?? null, goal: r.compare?.goal ?? null, guardsWorse: (r.compare?.guards ?? []).filter((g) => g.verdict === 'worse'), pictures: r.look?.note ?? null })),
    profile: profs.map((p) => ({ device: p.device, role: p.role, idlePct: p.idlePct, gamePct: p.gamePct, gcPct: p.gcPct, programPct: p.programPct, top: p.top.slice(0, 10) })),
  };
  writeJson(join(outDir, 'numbers.json'), numbers);
  writeFileSync(join(outDir, 'README.md'), reportMd(s, numbers, final, pictures, kept, patches));
  return { ok: true, command: 'report', game, kept: kept.map((k) => k.name), report: join(outDir, 'README.md'), numbers: join(outDir, 'numbers.json'), beforeAfter: ba, next: kept.length ? `commit perf/${game}/ with the kept change${kept.length > 1 ? 's' : ''} (games/${game}/ already has ${kept.length > 1 ? 'them' : 'it'})` : `commit perf/${game}/: it says honestly that nothing measured better` };
}

/** The unit a metric is in, for a person. */
const unitOf = (k) => (k.startsWith('bytes.') ? ' B' : /\.load\.(gameKb|prePlayKb)$/.test(k) ? ' KB' : /\.render\./.test(k) ? '' : /\.(frame|work)\.(p\d+|max|mean)$|\.busy$|\.load\./.test(k) ? ' ms' : /\.frame\.over\d+$/.test(k) ? '%' : /heap$/.test(k) ? ' MB' : /heap\.growth$/.test(k) ? ' MB/min' : /\.net\.kb/.test(k) ? ' KB/s' : /\.net\.msgs/.test(k) ? '/s' : '');

function reportMd(s, n, final, pictures, kept, patches = new Map()) {
  const pct = (x) => (x === null || x === undefined ? '–' : `${x > 0 ? '+' : ''}${(x * 100).toFixed(1)}%`);
  const val = (x, k) => (x === null || x === undefined ? '–' : `${x}${unitOf(k)}`);
  const L = [`# ${s.game}: performance`, ''];
  L.push(`Goal: \`${s.goal}\` (lower is better). Measured ${s.created.slice(0, 10)} on ${n.machine?.cpu ?? 'this computer'} (${n.machine?.cores ?? '?'} cores), ${n.chrome ?? 'Chrome'}, ${n.renderers?.join(', ') || 'renderer unknown'}.`, '');
  const cpu = n.phoneCpuMeasured;
  const devicesSaid = {
    computer: 'a computer: 1280x800 at 2x, this computer\'s CPU and GPU',
    phone: `an emulated phone: 390x844 at 3x, touch, a phone's user agent, Chrome's CPU throttle at ${s.cpu}x (${cpu ? `measured ${cpu.median}x slower on a loop of arithmetic here, ${cpu.min}x to ${cpu.max}x over ${cpu.runs} runs` : 'its real slow-down was not measured in these runs'}), 4G (9 Mbit/s down, 1.5 up, 85 ms); this computer's GPU, so it ranks changes and is not a real phone's frame rate`,
  };
  for (const d of s.devices) L.push(`- **${d}**: ${devicesSaid[d]}`);
  L.push('', '## Result', '');
  if (!kept.length) L.push(`**No change was kept.** ${s.history.length ? `${s.history.length} change(s) were tried; none was better beyond the noise without making something else worse (below).` : 'No change was tried.'} The game is as it was.`, '');
  else if (final?.compare) {
    const g = final.compare.goal;
    const paired = /in the median pair/.test(g.why ?? '');
    L.push(`**${kept.length} of ${s.history.length} changes kept.** First build against the kept one, measured in turns${final.from === 'final' ? ' after the last change' : ' (the kept change\'s own comparison)'}: \`${g.metric}\` ${val(g.before, g.metric)} → ${val(g.after, g.metric)} (${pct(g.change)}, 95% interval ${g.ci ? `${pct(g.ci[0])} to ${pct(g.ci[1])}` : '–'}, p = ${g.p}, ${g.n ? (paired ? `${g.n[0]} pairs` : `${g.n[0]} + ${g.n[1]} runs`) : ''}): **${final.compare.verdict}**.`, '', '| metric | before | after | change | 95% interval | p (better) | verdict |', '| --- | --- | --- | --- | --- | --- | --- |');
    for (const x of [g, ...final.compare.guards]) L.push(`| \`${x.metric}\` | ${val(x.before, x.metric)} | ${val(x.after, x.metric)} | ${pct(x.change)} | ${x.ci ? `${pct(x.ci[0])} to ${pct(x.ci[1])}` : '–'} | ${x.p ?? '–'} | ${x.verdict} |`);
    L.push('', paired ? 'Before and after are each side\'s median; the change is the median of the pairs\' ratios (each after-run against the before-run beside it), so it can differ in sign from the two medians when the noise is larger than the change: that is a "same".' : 'Before and after are each side\'s median over its runs.', '');
  }
  const changedLook = n.changes.filter((c) => c.verdict === 'keep' && (c.looks !== 'same' || c.plays !== 'same'));
  L.push(`How it looks and plays: ${changedLook.length ? `**changed by ${changedLook.map((c) => `change ${c.n} (looks: ${c.looks}; plays: ${c.plays})`).join(', ')}**` : kept.length ? 'unchanged: every kept change said it looks and plays the same, and its screenshots measured the same' : 'unchanged'}. The studio's two-browser check (two fresh browsers finish a round together) passed before the first change${kept.length ? ' and after every kept one' : ''}.`, '');
  if (pictures.length) L.push('Pictures (the host\'s screen at the end of a measured run):', '', ...pictures.map((p) => `- [${p}](${p})`), '');
  if (n.sizes.before) {
    const kb = (b) => `${(b / 1024).toFixed(1)} KB`;
    L.push(`What a player downloads: ${kb(n.sizes.before.total.gzip)} gzipped (JavaScript ${kb(n.sizes.before.js.gzip)})${n.sizes.after ? ` → ${kb(n.sizes.after.total.gzip)} (JavaScript ${kb(n.sizes.after.js.gzip)})` : ''}.`, '');
  }
  L.push('## Every change tried', '');
  if (!n.changes.length) L.push('None.', '');
  for (const c of n.changes) {
    L.push(`${c.n}. **${c.name}**: ${c.verdict.toUpperCase()}. ${c.why}`);
    L.push(`   Looks: ${c.looks}. Plays: ${c.plays}.${c.check ? ` Check: ${c.check.ok ? 'passed' : `failed (${c.check.why})`}.` : ''}${c.pictures ? ` Screenshots: ${c.pictures}.` : ''}${patches.has(c.n) ? ` The change: \`${patches.get(c.n)}\`.` : ''}`);
  }
  L.push('', '## The first build, measured', '', '| metric | median | spread |', '| --- | --- | --- |');
  for (const [k, v] of Object.entries(n.baseline)) if (/\.(frame\.(p50|p95|over50)|work\.mean|busy|heap|load\.playable|net\.(msgsOut|kbOut))$/.test(k)) L.push(`| \`${k}\` | ${v.median} | ${v.spread === null ? '–' : `${Math.round(v.spread * 100)}%`} |`);
  L.push('', '## Where the time went (the first build, one profiled run per device)', '');
  for (const p of n.profile) {
    L.push(`- **${p.device} ${p.role}**: ${p.idlePct}% idle; busy time: game ${p.gamePct}%, Chrome's own drawing and compositing ${p.programPct}%, garbage collection ${p.gcPct}%. Hottest: ${p.top.slice(0, 5).map((t) => `${t.name} (${t.where === '(native)' ? 'native' : t.where}) ${t.selfPct}%`).join('; ')}.`);
  }
  L.push('', '## How this was measured', '');
  L.push(`- Each run: two browsers (the host and a replica) in a fresh room of their own, the same seeded presses, a 3 s warm-up and a ${s.seconds} s measured window; headless Chrome on this computer's GPU (never a software renderer).`);
  L.push(`- Each change: the build to beat and the changed build measured in turns (before, after, after, before, …), ${s.runs} runs each per device. Each before-run and the after-run beside it are a pair, so a computer that drifted busier hits both sides alike. Better means: a one-sided signed-rank test on the pairs (Wilcoxon, exact) p < 0.05, the 95% bootstrap interval of the change below zero, and at least ${s.min}% better. Guards (frame time, main thread per frame, time to playable, heap, the host's upload) must not be worse (worse in every pair or p < 0.01, and at least 5%).`);
  L.push(`- The computer is shared: every run waited for the 1-minute load to fall under ${s.maxLoad} per core and recorded it; a run that started busy was taken again and left out.`);
  L.push(`- Before every run the site was checked to serve exactly the build being measured: every file by SHA-256, and the game page as the build made it${s.pageAdded ? `, with what the site adds to it (${addedSaid(s.pageAdded)}) the same throughout` : ''}.`);
  L.push(`- The phone is emulated: Chrome's CPU throttle at ${s.cpu}x${cpu ? ` (measured ${cpu.median}x slower here; it varies from run to run, ${cpu.min}x to ${cpu.max}x, which is part of the phone's noise)` : ''} and 4G, on this computer's GPU. It ranks changes; it is not a real phone's frame rate. Check a real phone (or the iOS Simulator) before promising one.`);
  L.push(`- Raw runs, screenshots and CPU profiles: \`.perf/${s.game}/\` (on this computer, not committed).`, '');
  return `${L.join('\n')}\n`;
}

/* ------------------------------------------------------------------------------------------- main */

async function main() {
  const cmd = pos[0];
  if (!cmd || cmd === 'help' || flags.has('help')) {
    const head = readFileSync(fileURLToPath(import.meta.url), 'utf8').split('*/')[0];
    return { ok: true, command: 'help', usage: head.replace(/^#!.*\n\/\*\*?/, '').replace(/^ \* ?/gm, '').trim() };
  }
  if (cmd === 'baseline') return baseline();
  if (cmd === 'try') return tryChange();
  if (cmd === 'revert') return revert();
  if (cmd === 'report') return report();
  if (cmd === 'status') return status();
  if (cmd === 'goals') return goals();
  return { ok: false, command: cmd, why: `unknown command "${cmd}" (perf.mjs help)` };
}

const print = (o) => {
  if (JSON_OUT) { process.stdout.write(`${JSON.stringify(o, null, 2)}\n`); return; }
  if (o.ok === false && o.why && !o.verdict) { process.stdout.write(`perf: ${o.why}\n`); return; }
  const lines = [];
  for (const [k, v] of Object.entries(o)) if (k !== 'ok' && k !== 'command' && v !== undefined && v !== null) lines.push(Array.isArray(v) ? `${k}:\n  ${v.join('\n  ')}` : `${k}: ${typeof v === 'object' ? JSON.stringify(v) : v}`);
  process.stdout.write(`${lines.join('\n')}\n`);
};

try {
  const r = await main();
  if (r) { print(r); if (r.ok === false) process.exitCode = 1; }
} catch (error) {
  // A network preflight that could not reach the site keeps its verdict (BLOCKED: nothing was measured).
  print({ ok: false, ...(error?.verdict === 'BLOCKED' ? { verdict: 'BLOCKED', kind: error.kind } : {}), why: error instanceof Error ? error.message : String(error) });
  process.exitCode = 1;
}
// Printed and done: leave with the exit code set above, whatever is still on the event loop (lib/exit.mjs).
await finish();
