#!/usr/bin/env node
// Preview Lab CLI: one persistent, self-cleaning review lab per project checkout. Zero dependencies.
// Run from the project root. `node pl.mjs help` lists the commands.
import { createServer } from 'node:http';
import { spawn, spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import fs from 'node:fs';
import { homedir } from 'node:os';
import { basename, dirname, extname, join, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

const SELF = fileURLToPath(import.meta.url);
const TEMPLATE = fs.readFileSync(fileURLToPath(new URL('../assets/lab.html', import.meta.url)), 'utf8');
const BRAND_RE = /\/\* BRAND:START[\s\S]*?BRAND:END \*\//g;
const specOf = html => html.match(/name="preview-lab-spec"\s+content="(\d+)"/)?.[1];
const SPEC = specOf(TEMPLATE);
const sha = (s, n = 8) => createHash('sha1').update(s).digest('hex').slice(0, n);
const bodyHash = html => sha(html.replace(BRAND_RE, ''), 12); // the lab code without its branding
const slug = s => String(s).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'x';
const exists = fs.existsSync, readJson = f => JSON.parse(fs.readFileSync(f, 'utf8'));
const die = (msg, code = 1) => { console.error(msg); process.exit(code); };
const pick = (o, keys) => Object.fromEntries(keys.filter(k => o?.[k] !== undefined).map(k => [k, o[k]]));
const TYPES = { '.html': 'text/html; charset=utf-8', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
  '.webp': 'image/webp', '.gif': 'image/gif', '.avif': 'image/avif', '.svg': 'image/svg+xml', '.htm': 'text/html; charset=utf-8',
  '.mp4': 'video/mp4', '.m4v': 'video/mp4', '.webm': 'video/webm', '.mov': 'video/quicktime', '.pdf': 'application/pdf',
  '.md': 'text/markdown; charset=utf-8', '.markdown': 'text/markdown; charset=utf-8', '.txt': 'text/plain; charset=utf-8',
  '.csv': 'text/plain; charset=utf-8', '.log': 'text/plain; charset=utf-8' };

const BOOL = new Set(['open', 'detach', 'in-project', 'force', 'all']);
const [cmd = 'help', ...rest] = process.argv.slice(2);
const flags = {}, args = [];
for (let i = 0; i < rest.length; i++) {
  if (!rest[i].startsWith('--')) { args.push(rest[i]); continue; }
  const k = rest[i].slice(2);
  if (BOOL.has(k)) flags[k] = true;
  else if (rest[i + 1] === undefined) die(`--${k} needs a value`);
  else flags[k] = rest[++i];
}

// Identity: the checkout (root) owns the lab; the repo (shared by all its worktrees) shares the branding.
const cwd = resolve(flags.project || process.cwd());
const git = (...a) => { const r = spawnSync('git', a, { cwd, encoding: 'utf8' }); return r.status === 0 ? r.stdout.trim() : ''; };
const root = resolve(git('rev-parse', '--show-toplevel') || cwd);
const commonDir = git('rev-parse', '--git-common-dir');
const repo = commonDir ? resolve(cwd, commonDir) : root;
const projectName = basename(repo) === '.git' ? basename(dirname(repo)) : basename(root);
const HOME = resolve(process.env.PREVIEW_LAB_HOME || join(homedir(), '.preview-lab'));
const IN_PROJECT = join(root, '.preview-lab');
const KEEP = new Set(['index.html', 'manifest.json', 'feedback.json', 'feedback.md', 'server.json', 'shots', 'inbox']);
// what a shot file is shown as in the lab; anything else is refused
const KIND = { '.png': 'image', '.jpg': 'image', '.jpeg': 'image', '.webp': 'image', '.gif': 'image', '.avif': 'image', '.svg': 'image',
  '.mp4': 'video', '.m4v': 'video', '.webm': 'video', '.mov': 'video', '.html': 'html', '.htm': 'html', '.pdf': 'pdf',
  '.md': 'md', '.markdown': 'md', '.txt': 'text', '.json': 'text', '.csv': 'text', '.log': 'text' };
let lab, P;
const setLab = dir => {
  lab = resolve(dir);
  P = { manifest: join(lab, 'manifest.json'), index: join(lab, 'index.html'), feedback: join(lab, 'feedback.json'), md: join(lab, 'feedback.md'),
    server: join(lab, 'server.json'), shots: join(lab, 'shots'), inbox: join(lab, 'inbox') };
};
// Sessions: a lab belongs to the agent session that writes it, so two sessions on one checkout never overwrite each other's items or shots.
// Another session gets its own lab next to it (<lab>--<id>); it takes the shared one over only when that is unclaimed, or idle for a day and not served.
const SESSION = flags.session || process.env.PREVIEW_LAB_SESSION || process.env.CLAUDE_CODE_SESSION_ID || 'anonymous'; // agents without an id share one
const SID = SESSION && sha(SESSION, 12), IDLE = 24 * 3600e3;
const serving = dir => { try { process.kill(readJson(join(dir, 'server.json')).pid, 0); return true; } catch { return false; } };
function forSession(base) {
  if (!SID) return base;
  const own = `${base}--${SID.slice(0, 6)}`;
  if (exists(own)) return own;
  try {
    const f = join(base, 'manifest.json'), owner = readJson(f).session;
    if (owner && owner !== SID && (Date.now() - fs.statSync(f).mtimeMs < IDLE || serving(base))) return own;
  } catch {} // no lab there yet
  return base;
}
const BASE = flags['in-project'] || exists(IN_PROJECT) ? IN_PROJECT : join(HOME, `${slug(basename(root))}-${sha(root, 6)}`);
setLab(flags.lab || forSession(BASE));

const commands = { init, status, prune: pruneCmd, upgrade, brand, contrast: contrastCmd, export: exportLab, add, recapture, remove, round, feedback, clean: () => { const m = load(); clean(m, true); brief(m); }, reset, serve, stop, help };

function load() {
  if (!exists(P.manifest)) die(`NO_LAB: run "pl.mjs init" from the project root first (${lab})`, 3);
  const m = readJson(P.manifest);
  if (!m.previewLab) die(`REFUSED: ${P.manifest} was not created by preview-lab`);
  m.items ||= [];
  return m;
}
function save(m) { if (SID) m.session = SID; fs.writeFileSync(P.manifest + '.tmp', JSON.stringify(m, null, 1)); fs.renameSync(P.manifest + '.tmp', P.manifest); }
const indexState = html => !html ? 'missing' : specOf(html) !== SPEC ? 'outdated' : /BRAND:START default/.test(html) ? 'unbranded' : 'ok';
const readIndex = () => (exists(P.index) ? fs.readFileSync(P.index, 'utf8') : '');

function info(m, extra = {}) {
  const html = readIndex(), inboxFiles = exists(P.inbox) ? fs.readdirSync(P.inbox).length : 0, live = running();
  return { lab, inbox: P.inbox, index: indexState(html), ...(html && m.labHash && bodyHash(html) !== m.labHash ? { customized: true } : {}),
    round: m.round, mode: m.mode || 'visual', items: m.items.map(i => i.id), ...(inboxFiles ? { inboxFiles } : {}),
    pendingFeedback: exists(P.feedback), ...(live ? { server: live.url } : {}), ...extra };
}
function status(extra) { console.log(JSON.stringify(info(load(), extra), null, 1)); }
// One line for mutating commands: paths are only printed by init/status.
function brief(m, extra = {}) { console.log(JSON.stringify({ ok: true, round: m.round, items: m.items.map(i => i.id), ...extra })); }

function init() {
  let note;
  const was = lab, expired = exists(P.manifest) && stale(lab); // checked before create() touches the manifest
  try { create(); } catch (e) {
    if (!['EACCES', 'EPERM', 'EROFS'].includes(e.code) || flags.lab || lab === IN_PROJECT) throw e;
    setLab(forSession(IN_PROJECT)); create(); // sandboxed harness: fall back to the project folder
    note = 'home folder not writable: the lab lives in <project>/.preview-lab/ (git-ignored)';
  }
  if (expired && lab === was && hasContent(lab)) { wipe(lab); note = [note, 'this lab was untouched for 7 days, so it was emptied (its branding is kept)'].filter(Boolean).join('; '); }
  const { pruned, emptied } = prune();
  if (!note && SID && lab.endsWith(`--${SID.slice(0, 6)}`)) note = 'another session is using this checkout\'s main lab: this session has its own, so neither overwrites the other';
  status({ ...(pruned ? { pruned } : {}), ...(emptied ? { emptied } : {}), ...(note ? { note } : {}) });
}

function create() {
  if (exists(lab) && !exists(P.manifest) && fs.readdirSync(lab).length) die(`REFUSED: ${lab} is not empty and is not a preview lab`);
  fs.mkdirSync(P.shots, { recursive: true }); fs.mkdirSync(P.inbox, { recursive: true });
  const m = exists(P.manifest) ? load() : { previewLab: SPEC, project: projectName, round: 1, items: [] };
  Object.assign(m, { root, repo });
  if (!exists(P.index)) { // reuse the branding of another checkout of this repo, else start from the template
    fs.writeFileSync(P.index, siblingIndex() || TEMPLATE);
    m.labHash = bodyHash(TEMPLATE);
  }
  m.labHash ??= bodyHash(readIndex());
  save(m);
  if (lab.startsWith(root + sep) && git('rev-parse', '--git-dir')) { // in-project lab: keep it out of git
    const gi = join(root, '.gitignore'), cur = exists(gi) ? fs.readFileSync(gi, 'utf8') : '';
    if (!/^\/?\.preview-lab\*\/?$/m.test(cur)) fs.appendFileSync(gi, (cur && !cur.endsWith('\n') ? '\n' : '') + '.preview-lab*/\n'); // * : session labs too
  }
}

const labDirs = () => [...(exists(HOME) ? fs.readdirSync(HOME).map(d => join(HOME, d)) : []),
  ...fs.readdirSync(root).filter(d => /^\.preview-lab(--\w+)?$/.test(d)).map(d => join(root, d))]; // in-project labs of this checkout too
const otherLabs = () => labDirs().filter(d => d !== lab && exists(join(d, 'manifest.json')))
  .map(d => { try { return { dir: d, m: readJson(join(d, 'manifest.json')) }; } catch { return null; } }).filter(x => x?.m.previewLab);
function siblingIndex() {
  const hits = otherLabs().filter(x => x.m.repo === repo && exists(join(x.dir, 'index.html')))
    .map(x => ({ html: fs.readFileSync(join(x.dir, 'index.html'), 'utf8'), t: fs.statSync(join(x.dir, 'index.html')).mtimeMs }))
    .filter(x => indexState(x.html) === 'ok').sort((a, b) => b.t - a.t);
  return hits[0]?.html;
}
// Retention, one rule: a lab untouched for 7 days and not being served expires. Session labs (<lab>--<id>) and labs whose
// checkout is gone are deleted; a checkout's main lab is emptied but keeps its code, so its branding survives.
const TTL = 7 * 24 * 3600e3;
const stale = (d, ttl = TTL) => Date.now() - fs.statSync(join(d, 'manifest.json')).mtimeMs >= ttl && !serving(d);
const hasContent = d => { const m = readJson(join(d, 'manifest.json')); return !!(m.items?.length || m.history?.length || ['shots', 'inbox'].some(x => exists(join(d, x)) && fs.readdirSync(join(d, x)).length)); };
function wipe(dir) { // empty a lab: no items, rounds, shots, inbox or feedback; keeps its code, identity and owner
  const f = join(dir, 'manifest.json'), m = readJson(f);
  for (const k of ['title', 'subtitle', 'mode', 'categories', 'devices', 'history']) delete m[k];
  m.items = []; m.round = 1;
  for (const x of ['shots', 'inbox']) if (exists(join(dir, x))) for (const y of fs.readdirSync(join(dir, x))) fs.rmSync(join(dir, x, y), { recursive: true, force: true });
  for (const x of ['feedback.json', 'feedback.md']) fs.rmSync(join(dir, x), { force: true });
  fs.writeFileSync(f + '.tmp', JSON.stringify(m, null, 1)); fs.renameSync(f + '.tmp', f);
}
function prune(ttl = TTL) {
  let pruned = 0, emptied = 0;
  for (const x of otherLabs()) {
    try {
      if (x.m.root && !exists(x.m.root) && !serving(x.dir)) { fs.rmSync(x.dir, { recursive: true, force: true }); pruned++; }
      else if (!stale(x.dir, ttl)) continue;
      else if (basename(x.dir).includes('--')) { fs.rmSync(x.dir, { recursive: true, force: true }); pruned++; }
      else if (hasContent(x.dir)) { wipe(x.dir); emptied++; }
    } catch {} // a lab another process is changing right now: next time
  }
  return { pruned, emptied };
}
// prune [--all]: apply the retention rule now; --all expires every other lab that is not being served, whatever its age.
function pruneCmd() { console.log(JSON.stringify({ ok: true, ...prune(flags.all ? 0 : TTL) })); }

// upgrade: current template + this lab's BRAND blocks. Edits outside the blocks would be lost, so they need --force.
function upgrade() {
  const m = load(), old = readIndex();
  if (old && m.labHash && bodyHash(old) !== m.labHash && !flags.force)
    die('CUSTOMIZED: index.html has edits outside the BRAND blocks and upgrade would drop them. Note them, run "upgrade --force", then re-apply them.', 5);
  const blocks = old.match(BRAND_RE) || [];
  let i = 0;
  fs.writeFileSync(P.index, TEMPLATE.replace(BRAND_RE, b => blocks[i++] ?? b));
  m.labHash = bodyHash(TEMPLATE); save(m); status();
}

// brand [file | -]: read or set the lab's branding as JSON, so nobody has to open the 45 KB index.html for it.
const COLORS = ['bg', 'fg', 'surface', 'muted', 'line', 'accent', 'on-accent', 'ok', 'warn', 'bad'];
const strKeys = () => Object.fromEntries([...(TEMPLATE.match(/const STR = \{([\s\S]*?)\n\};/)?.[1] || '').matchAll(/(\w+): '((?:[^'\\]|\\.)*)'/g)].map(x => [x[1], x[2]]));
function readBrand(html) {
  const [css = '', js = ''] = html.match(BRAND_RE) || [];
  const vars = re => Object.fromEntries([...(css.match(re)?.[1] || '').matchAll(/--([\w-]+)\s*:\s*([^;}]+)/g)].map(x => [x[1], x[2].trim()]));
  const { radius, font, ...light } = vars(/:root\s*\{([^}]*)\}/);
  let meta = {};
  try { meta = JSON.parse(js.match(/const BRAND = (\{[\s\S]*\});/)[1]); } catch {} // a hand-edited block is replaced by the next "brand"
  return { name: '', logo: '', lang: 'en', copy: {}, ...meta, radius, font, light, dark: vars(/:root\[data-theme=dark\]\s*\{([^}]*)\}/) };
}
// WCAG contrast of two hex colors (null when either is not plain hex, e.g. oklch()).
const lum = hex => { const h = hex.slice(1), f = h.length === 3 ? [...h].map(c => c + c).join('') : h;
  return [0.2126, 0.7152, 0.0722].reduce((s, w, k) => { const v = parseInt(f.slice(k * 2, k * 2 + 2), 16) / 255; return s + w * (v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4); }, 0); };
const contrast = (a, b) => { if (![a, b].every(c => /^#([0-9a-f]{3}|[0-9a-f]{6})$/i.test(c || ''))) return null; const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p); return (x + 0.05) / (y + 0.05); };
const CHECKS = [['fg', 'bg', 4.5, 'text'], ['fg', 'surface', 4.5, 'text'], ['muted', 'bg', 4.5, 'secondary text'], ['muted', 'surface', 4.5, 'secondary text'],
  ['on-accent', 'accent', 4.5, 'button text'], ['accent', 'surface', 3, 'accent text'], ['surface', 'ok', 3, 'text on Approve'], ['surface', 'warn', 3, 'text on Changes'], ['line', 'surface', 1.25, 'borders'], ['surface', 'bg', 1.04, 'cards against the page']];

// contrast <fg> <bg>: WCAG ratio of two hex colors, for measured accessibility recommendations.
function contrastCmd() {
  const r = contrast(args[0], args[1]);
  if (r === null) die('usage: contrast <#fg> <#bg> (hex colors)');
  console.log(JSON.stringify({ ratio: +r.toFixed(2), text: r >= 4.5, largeText: r >= 3, ui: r >= 3 }));
}

function brand() {
  load();
  const html = readIndex(), cur = readBrand(html);
  if ((html.match(BRAND_RE) || []).length !== 2) die('index.html has no BRAND blocks: run "pl.mjs upgrade --force" first', 3);
  if (!args.length) return console.log(JSON.stringify({ brand: cur, copyKeys: strKeys() }));
  let b;
  try { b = JSON.parse(fs.readFileSync(args[0] === '-' ? 0 : args[0], 'utf8')); } catch (e) { die(`cannot read the brand JSON: ${e.message}`); }
  const errors = [], known = strKeys();
  for (const k of Object.keys(b)) if (!['name', 'logo', 'lang', 'copy', 'light', 'dark', 'radius', 'font'].includes(k)) errors.push(`unknown key "${k}"`);
  for (const t of ['light', 'dark']) for (const k of Object.keys(b[t] || {})) if (!COLORS.includes(k)) errors.push(`${t}.${k} is not a token (${COLORS.join(', ')})`);
  for (const k of Object.keys(b.copy || {})) if (!(k in known)) errors.push(`copy.${k} is not a text key (run "brand" with no file to list them)`);
  const next = { ...cur, ...b, light: { ...cur.light, ...b.light }, dark: { ...cur.dark, ...b.dark },
    copy: Object.fromEntries(Object.entries({ ...cur.copy, ...b.copy }).filter(([, v]) => v != null)) }; // null removes an override
  for (const k of ['name', 'logo', 'lang']) if (typeof next[k] !== 'string') errors.push(`${k} must be a string`);
  for (const [k, v] of [...['light', 'dark'].flatMap(t => Object.entries(next[t]).map(([n, v]) => [`${t}.${n}`, v])), ['radius', next.radius], ['font', next.font]])
    if (typeof v !== 'string' || !v.trim() || /[;{}<>]|\*\//.test(v)) errors.push(`${k}: not a plain CSS value`);
  if (errors.length) die(`INVALID (nothing was changed):\n- ${errors.join('\n- ')}`, 4);
  const warnings = [];
  for (const t of ['light', 'dark']) for (const [a, on, min, what] of CHECKS) {
    const r = contrast(next[t][a], next[t][on]);
    if (r !== null && r < min) warnings.push(`${t}: --${a} on --${on} is ${r.toFixed(2)}:1; ${what} needs ${min}:1`);
  }
  const decl = (o, keys) => keys.filter(k => o[k]).map(k => `--${k}:${o[k]}`).join(';');
  const blocks = [`/* BRAND:START set (${slug(next.name || projectName)}) — written by "pl.mjs brand"; keep the token names */
:root{${decl({ ...next.light, radius: next.radius, font: next.font }, [...COLORS, 'radius', 'font'])}}
:root[data-theme=dark]{${decl(next.dark, COLORS)}}
/* BRAND:END */`,
  `/* BRAND:START — written by "pl.mjs brand": name, logo (inline svg or image URL; empty = initial letter), lang, copy (text overrides) */
const BRAND = ${JSON.stringify(pick(next, ['name', 'logo', 'lang', 'copy'])).replace(/</g, '\\u003c')};
/* BRAND:END */`];
  let i = 0;
  fs.writeFileSync(P.index, html.replace(BRAND_RE, () => blocks[i++]));
  console.log(JSON.stringify({ ok: true, index: indexState(readIndex()), ...(warnings.length ? { warnings } : {}) }));
}

// export [file]: this round as one self-contained HTML file (screenshots inlined) for sessions the user cannot reach on localhost.
// There is no server behind it, so its Send button copies the feedback for pasting into the chat.
function exportLab() {
  const m = load(), html = readIndex();
  const inline = s => ({ ...s, src: `data:${TYPES[extname(s.src).toLowerCase()].replace(' ', '')};base64,${fs.readFileSync(join(lab, s.src)).toString('base64')}` });
  const data = { ...pick(m, ['project', 'title', 'subtitle', 'mode', 'round', 'categories', 'devices']),
    items: m.items.map(({ capture, ...it }) => ({ ...it, ...(it.shots ? { shots: it.shots.map(inline) } : {}) })) }; // no local paths, recipes or history
  const out = resolve(args[0] || join(lab, 'export.html'));
  fs.writeFileSync(out, html.replace('<script>', () => `<script>window.PL_DATA=${JSON.stringify(data).replace(/</g, '\\u003c')}</script>\n<script>`));
  console.log(JSON.stringify({ ok: true, file: out, kb: Math.round(fs.statSync(out).size / 1024) }));
}

// add <items.json | ->: validate everything, capture, then commit. A failure changes nothing.
async function add() {
  const src = args[0] && args[0] !== '-' ? args[0] : 0;
  let input;
  try { input = JSON.parse(fs.readFileSync(src, 'utf8')); } catch (e) { die(`cannot read the items JSON: ${e.message}`); }
  await apply(input, src ? dirname(resolve(src)) : process.cwd());
}
async function recapture() {
  const m = load(), unknown = args.filter(id => !m.items.some(i => i.id === id && i.capture));
  if (unknown.length) die(`no stored capture recipe for: ${unknown.join(', ')}`);
  const items = m.items.filter(i => i.capture && (!args.length || args.includes(i.id))).map(i => ({ id: i.id, capture: i.capture }));
  if (!items.length) die('no item has a capture recipe (items added with "capture")');
  await apply({ items }, process.cwd());
}

async function apply(input, base) {
  const m = load(), top = Array.isArray(input) ? {} : input, list = Array.isArray(input) ? input : input.items || [];
  const errors = [], plan = [];
  if (top.mode && !['visual', 'complete'].includes(top.mode)) errors.push(`mode must be "visual" or "complete", not "${top.mode}"`);
  for (const raw of list) {
    const it = { ...raw }, err = msg => errors.push(`${it.id ?? '(no id)'}: ${msg}`);
    if (!it.id || !/^[\w.-]+$/.test(it.id)) { err('bad id (letters, digits, - _ . only)'); continue; }
    if (plan.some(p => p.it.id === it.id)) { err('listed twice'); continue; }
    const prev = m.items.find(x => x.id === it.id);
    if (!prev && !it.title) err('a new item needs a title');
    const shots = (it.shots || []).map((s, n) => {
      const shot = { ...s, label: String(s.label || `view ${n + 1}`) }, kind = KIND[extname(String(s.src || '')).toLowerCase()];
      if (kind && kind !== 'image') shot.type = kind; else delete shot.type; // images are the default
      if (/^shots\/[^/]+$/.test(s.src || '') && exists(join(lab, s.src))) return shot; // already in the lab
      shot.from = resolve(base, s.src || '');
      if (!s.src || !exists(shot.from) || !fs.statSync(shot.from).isFile()) err(`shot file not found: ${s.src ? shot.from : '(no src)'}`);
      else if (!kind) err(`unsupported file type: ${s.src} (${Object.keys(KIND).join(' ')})`);
      return shot;
    });
    const jobs = it.capture ? captureJobs(it, top.viewports, err) : [];
    if ('recommendations' in it) checkRecs(it.recommendations, err);
    const keptShots = 'shots' in raw ? shots : (prev?.shots || []).filter(s => !it.capture || !s.captured);
    const labels = [...keptShots, ...jobs].map(s => s.label.toLowerCase());
    if (new Set(labels).size !== labels.length) err('two views share a label');
    if (labels.includes('live')) err('"Live" is reserved for the live tab; rename that view');
    if (!keptShots.length && !jobs.length && !(it.url ?? prev?.url)) err('nothing to show: give "shots", "capture" or "url"');
    plan.push({ it, prev, keptShots, jobs, visual: 'shots' in raw || 'capture' in raw || 'url' in raw });
  }
  if (errors.length) die(`INVALID (nothing was changed):\n- ${errors.join('\n- ')}`, 4);

  const jobs = plan.flatMap(p => p.jobs);
  if (jobs.length) {
    const { capture } = await import('./capture.mjs');
    const results = await capture(jobs).catch(e => { jobs.forEach(j => fs.rmSync(j.file, { force: true })); die(e.message, 4); });
    const failed = jobs.map((j, i) => (results[i].ok ? null : `${j.id} · ${j.label}: ${results[i].error}`)).filter(Boolean);
    if (failed.length) { jobs.forEach(j => fs.rmSync(j.file, { force: true })); die(`CAPTURE_FAILED (nothing was changed):\n- ${failed.join('\n- ')}`, 4); }
    jobs.forEach((j, i) => (j.scale = results[i].scale));
  }

  for (const k of ['project', 'title', 'subtitle', 'mode', 'categories', 'devices']) if (k in top) m[k] = top[k];
  const changed = [];
  for (const { it, prev, keptShots, jobs, visual } of plan) {
    it.shots = [...keptShots.map(s => importShot(it.id, s)), ...jobs.map(j => importShot(it.id, { label: j.label, from: j.file, scale: j.scale, captured: true }))];
    if (!it.shots.length) delete it.shots;
    if (!prev) { if (m.round > 1) it.added = m.round; m.items.push(it); continue; }
    // Shot files are named by content hash, so an identical recapture is not a change: the approval and badges stay.
    const look = x => JSON.stringify([x.shots?.map(s => s.src), x.url]), before = look(prev);
    Object.assign(prev, it); if (!it.shots) delete prev.shots;
    if (visual && look(prev) !== before) { changed.push(prev.id); if (m.round > 1 && prev.added !== m.round) prev.updated = m.round; }
  }
  clean(m, true); save(m); brief(m, { ...(jobs.length ? { captured: jobs.length } : {}), ...(changed.length ? { changed } : {}) });
}

// complete mode: what the lab needs to show a recommendation (see references/complete-mode.md).
const REC_TYPES = ['ux', 'ui', 'a11y', 'responsive', 'consistency', 'branding', 'copy', 'perf'];
function checkRecs(recs, err) {
  if (!Array.isArray(recs)) return err('recommendations must be a list');
  const ids = new Set();
  recs.forEach((r, n) => {
    const at = `recommendation ${r?.id ?? n + 1}`;
    if (!r?.id || !/^[\w.-]+$/.test(r.id) || ids.has(r.id)) err(`${at}: needs a unique id (letters, digits, - _ .)`); ids.add(r?.id);
    if (!REC_TYPES.includes(r?.type)) err(`${at}: type must be one of ${REC_TYPES.join(', ')}`);
    if (!['high', 'medium', 'low'].includes(r?.severity)) err(`${at}: severity must be high, medium or low`);
    if (typeof r?.text !== 'string' || !r.text.trim()) err(`${at}: needs text`);
    if (r?.area && !['x', 'y', 'w', 'h'].every(k => typeof r.area[k] === 'number' && r.area[k] >= 0 && r.area[k] <= 100)) err(`${at}: area needs x, y, w, h as % (0–100)`);
  });
}

// One job per viewport × scheme. The recipe is stored on the item (viewports resolved) so `recapture` can replay it.
function captureJobs(it, viewports, err) {
  const c = it.capture, url = c.url || it.url;
  if (!url) err('capture needs a url (capture.url or the item url)');
  const vps = Array.isArray(c.viewports) ? c.viewports.map(n => [n, viewports?.[n]]) : Object.entries(c.viewports || viewports || {});
  if (!vps.length) err('capture needs viewports: { "<label>": [width, height] }');
  for (const [n, size] of vps) if (typeof n !== 'string' || !Array.isArray(size) || size.length !== 2 || !size.every(v => Number.isInteger(v) && v > 0)) err(`viewport ${JSON.stringify(n)} needs [width, height] (name a top-level viewport, or use an object: { "label": [w, h] })`);
  const schemes = c.schemes || [c.scheme || 'light'];
  for (const s of schemes) if (s !== 'light' && s !== 'dark') err(`scheme must be "light" or "dark", not "${s}"`);
  it.capture = { ...c, url, viewports: Object.fromEntries(vps) };
  return vps.flatMap(([n, size]) => schemes.map(scheme => {
    const label = scheme === 'dark' ? `${n} dark` : n;
    return { id: it.id, label, file: join(P.inbox, `.capture-${it.id}--${slug(label)}.png`), url, w: size?.[0], h: size?.[1], scheme,
      scale: c.scale, fullPage: c.fullPage, selector: c.selector, padding: c.padding, wait: c.wait, actions: c.actions };
  }));
}

function importShot(id, { from, ...shot }) {
  if (!from) return shot;
  const data = fs.readFileSync(from);
  shot.src = `shots/${id}--${slug(shot.label)}-${sha(data)}${extname(from).toLowerCase()}`;
  fs.writeFileSync(join(lab, shot.src), data); // sources inside inbox/ are deleted by clean() after the manifest is saved
  return shot;
}

function remove() {
  const m = load(), missing = args.filter(id => !m.items.some(i => i.id === id));
  m.items = m.items.filter(i => !args.includes(i.id));
  clean(m); save(m); brief(m, missing.length ? { notFound: missing } : {});
}

// round: the finished round is archived read-only in history (items, shots and feedback), approved items leave,
// the rest keep the last feedback as items[].previous, and the round number goes up.
function round() {
  const m = load(), fb = exists(P.feedback) ? readJson(P.feedback) : null, of = id => fb?.items?.find(x => x.id === id);
  const keep = Number(flags.keep ?? 5);
  if (!Number.isInteger(keep) || keep < 0) die('--keep needs a whole number of past rounds to keep');
  (m.history ||= []).push({ round: m.round || 1, ...pick(m, ['title', 'subtitle', 'categories']),
    items: m.items.map(it => pick(it, ['id', 'title', 'category', 'route', 'note', 'shots', 'url', 'previous', 'added', 'updated', 'recommendations'])),
    ...(fb ? { feedback: { submittedAt: fb.submittedAt, general: fb.general || '', items: (fb.items || []).map(i => pick(i, ['id', 'status', 'comment', 'areas', 'accepted'])) } } : {}) });
  m.history = keep ? m.history.slice(-keep) : []; // older rounds and their shots go: the lab stays small
  if (!m.history.length) delete m.history;
  const approved = m.items.filter(it => of(it.id)?.status === 'approved').map(it => it.id);
  m.items = m.items.filter(it => !approved.includes(it.id));
  for (const it of m.items) {
    const f = of(it.id);
    if (f && (f.status || f.comment || f.areas?.length)) it.previous = { round: m.round, status: f.status || '', comment: f.comment || '', areas: f.areas || [] };
    else delete it.previous;
    delete it.recommendations; // they were about this round's screens: complete mode writes new ones each round
  }
  m.round = (m.round || 1) + 1;
  fs.rmSync(P.feedback, { force: true }); fs.rmSync(P.md, { force: true });
  clean(m); save(m); brief(m, fb ? (approved.length ? { removedApproved: approved } : {}) : { note: 'no feedback.json was found, so no item was archived or removed' });
}

function feedback() {
  const md = P.md;
  if (exists(md)) return console.log(fs.readFileSync(md, 'utf8'));
  const live = running();
  die(live ? `NO_FEEDBACK yet: the lab is open at ${live.url}/` : 'NO_FEEDBACK and the lab is not being served. Run "pl.mjs serve".', 4);
}

function reset() {
  load(); wipe(lab);
  const m = load(); clean(m, true); save(m); brief(m);
}

// Everything the manifest does not reference goes. The inbox is only emptied once its files were imported (or on clean/reset).
function clean(m, inbox = false) {
  const used = new Set([...m.items, ...(m.history || []).flatMap(h => h.items)].flatMap(i => (i.shots || []).map(s => s.src))); // past rounds keep their shots
  for (const f of fs.readdirSync(lab)) if (!KEEP.has(f)) fs.rmSync(join(lab, f), { recursive: true, force: true });
  for (const f of fs.readdirSync(P.shots)) if (!used.has('shots/' + f)) fs.rmSync(join(P.shots, f), { recursive: true, force: true });
  if (inbox) for (const f of fs.readdirSync(P.inbox)) fs.rmSync(join(P.inbox, f), { recursive: true, force: true });
}

function stop() {
  const live = running();
  if (live) { process.kill(live.pid); fs.rmSync(P.server, { force: true }); }
  console.log(JSON.stringify({ ok: true, stopped: !!live }));
}

function running() {
  try {
    const s = readJson(P.server);
    process.kill(s.pid, 0); // throws when that process is gone
    return s;
  } catch { fs.rmSync(P.server, { force: true }); return null; }
}

async function serve() {
  load();
  if (!exists(P.index)) die('LAB_MISSING: run "pl.mjs init" first', 3);
  const started = Date.now(), md = P.md;
  const live = running();
  if (live || flags.detach) {
    let s = live;
    if (!s) {
      spawn(process.execPath, [SELF, 'serve', '--lab', lab, '--port', String(flags.port ?? 4747), '--timeout', String(flags.timeout || 120), ...(flags.open ? ['--open'] : [])],
        { cwd, detached: true, stdio: 'ignore' }).unref();
      for (let i = 0; i < 50 && !(s = running()); i++) await new Promise(r => setTimeout(r, 100));
      if (!s) die('the detached server did not start');
    }
    console.log(`PREVIEW_LAB_URL ${s.url}/${live ? ' (already running)' : ''}`);
    if (flags.detach) return console.log('Detached. When the user says they sent it, run: pl.mjs feedback');
    while (running()) await new Promise(r => setTimeout(r, 500)); // attach to the running server
    if (exists(md) && fs.statSync(md).mtimeMs >= started) { console.log(`\n--- FEEDBACK ---\n${fs.readFileSync(md, 'utf8')}`); return; }
    console.log('The lab server stopped without feedback.'); process.exit(2);
  }

  const timeoutMin = Number(flags.timeout || 120);
  let hosts = [], seen = false;
  const server = createServer(async (req, res) => {
    const send = (code, msg) => { res.writeHead(code, { 'content-type': 'text/plain' }); res.end(msg); };
    try {
      // Only this machine's own lab page may talk to the server (blocks DNS rebinding and cross-site posts).
      if (!hosts.includes(req.headers.host)) return send(403, 'forbidden');
      if (req.headers.origin && !hosts.includes(req.headers.origin.replace(/^http:\/\//, ''))) return send(403, 'forbidden');
      const url = new URL(req.url, 'http://x');
      if (req.method === 'POST' && url.pathname === '/feedback') {
        let body = '';
        for await (const c of req) { body += c; if (body.length > 5e6) return send(413, 'too large'); }
        let fb;
        try { fb = JSON.parse(body); if (!Array.isArray(fb.items)) throw 0; } catch { return send(400, 'bad json'); }
        const text = typeof fb.markdown === 'string' ? fb.markdown : '```json\n' + JSON.stringify(fb) + '\n```\n';
        delete fb.markdown;
        fs.writeFileSync(P.feedback, JSON.stringify(fb, null, 1)); fs.writeFileSync(md, text);
        send(200, 'ok');
        console.log(`\n--- FEEDBACK ---\n${text}`);
        return setTimeout(() => process.exit(0), 300);
      }
      if (req.method !== 'GET' && req.method !== 'HEAD') return send(405, 'method not allowed');
      const file = resolve(lab, '.' + decodeURIComponent(url.pathname === '/' ? '/index.html' : url.pathname));
      if (!file.startsWith(lab + sep) || file === P.server) return send(403, 'forbidden');
      if (url.pathname === '/manifest.json') seen = true;
      let data = await fs.promises.readFile(file);
      const head = { 'content-type': TYPES[extname(file).toLowerCase()] || 'application/octet-stream', 'cache-control': 'no-store', 'x-content-type-options': 'nosniff', 'accept-ranges': 'bytes',
        ...(/^\/shots\/.*\.(html?|svg)$/i.test(url.pathname) ? { 'content-security-policy': 'sandbox allow-scripts' } : {}) }; // opened on their own, they must not act as the lab
      const r = /^bytes=(\d*)-(\d*)$/.exec(req.headers.range || ''), n = data.length; // Safari only plays video served with ranges
      if (r && (r[1] || r[2])) {
        const a = r[1] ? +r[1] : Math.max(0, n - +r[2]), b = r[1] && r[2] ? Math.min(+r[2], n - 1) : n - 1;
        if (a > b) { res.writeHead(416, { 'content-range': `bytes */${n}` }); return res.end(); }
        res.writeHead(206, { ...head, 'content-range': `bytes ${a}-${b}/${n}` }); data = data.subarray(a, b + 1);
      } else res.writeHead(200, head);
      res.end(req.method === 'HEAD' ? undefined : data);
    } catch (e) { send(e instanceof URIError ? 400 : 404, e instanceof URIError ? 'bad request' : 'not found'); }
  });
  const listen = port => {
    server.once('error', e => (e.code === 'EADDRINUSE' && port ? listen(0) : die(`cannot start the lab server: ${e.message}`)));
    server.listen(port, '127.0.0.1', () => {
      const p = server.address().port, url = `http://127.0.0.1:${p}`;
      hosts = [`127.0.0.1:${p}`, `localhost:${p}`];
      fs.writeFileSync(P.server, JSON.stringify({ pid: process.pid, url }));
      console.log(`PREVIEW_LAB_URL ${url}/\nWaiting for feedback (timeout ${timeoutMin} min)…`);
      // A lab tab left open from the last round reloads by itself; only open a new one if none shows up.
      if (flags.open) setTimeout(() => {
        if (seen) return;
        const [c, a] = process.platform === 'darwin' ? ['open', [url]] : process.platform === 'win32' ? ['cmd', ['/c', 'start', '', url]] : ['xdg-open', [url]];
        spawn(c, a, { stdio: 'ignore', detached: true }).on('error', () => {}).unref();
      }, 3000);
    });
  };
  process.on('exit', () => { try { if (readJson(P.server).pid === process.pid) fs.rmSync(P.server); } catch {} });
  for (const sig of ['SIGINT', 'SIGTERM']) process.on(sig, () => process.exit(130));
  listen(Number(flags.port ?? 4747));
  setTimeout(() => { console.log('TIMEOUT: no feedback was sent'); process.exit(2); }, timeoutMin * 60000);
  await new Promise(() => {}); // keep serving until an exit above
}

function help() {
  console.log(`preview-lab (template v${SPEC}) — run from the project root
  init [--in-project]       create or locate this checkout's lab; prints its status
  status                    lab path, index (unbranded|ok|outdated), round, items, pending feedback
  upgrade [--force]         swap in the current template, keeping the BRAND blocks
  brand [file|-]            no file: print the branding and the text keys as JSON; with a file: set it (colors, font, logo, language, texts)
  contrast <#fg> <#bg>      WCAG contrast ratio of two colors (for complete mode)
  export [file]             this round as one self-contained HTML file, for sessions the user cannot reach on localhost
  add <items.json|->        validate, capture, then add or update items (nothing changes on error)
  recapture [id...]         replay the stored capture recipes (all items, or the given ones)
  remove <id...>            drop items and their shots
  serve [--open] [--detach] [--port N] [--timeout MIN]
                            serve the lab; exits 0 and prints the feedback when the user sends it
  feedback                  print the saved feedback (after serve --detach)
  stop                      stop a running lab server
  round [--keep N]          archive this round (read-only in the lab; the last 5 are kept), drop approved items, start the next one
  clean | reset             delete unreferenced files | empty the lab (keeps its code)
  prune [--all]             expire labs untouched for 7 days now (--all: every other lab not being served); init does this too
options: --project <dir>  --lab <dir>  --session <id>
env: PREVIEW_LAB_HOME (default ~/.preview-lab), PREVIEW_LAB_CHROME, PREVIEW_LAB_SESSION (else CLAUDE_CODE_SESSION_ID): labs are per session`);
}

// Dispatch last: every helper above is defined by now.
try { await (commands[cmd] || help)(); } catch (e) { die(`ERROR: ${e.message}`); }
