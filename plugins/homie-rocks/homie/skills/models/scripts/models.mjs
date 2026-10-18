#!/usr/bin/env node
/** models.mjs: local asset preparation only. Generation, schemas and pricing belong to the official provider MCP.
 * Read ../SKILL.md for the current workflow. */
import { spawnSync } from 'node:child_process';
import { appendFileSync, copyFileSync, existsSync, mkdirSync, readFileSync, renameSync, writeFileSync } from 'node:fs';
import { dirname, extname, join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { experienceDir, experienceJson, SLUG, checkBudget, findStudio, readBudget, readJson, setBudget, writeJson } from '../../music/scripts/lib/studio.mjs';


const HERE = dirname(fileURLToPath(import.meta.url));
const argv = process.argv.slice(2);
const flags = new Map();
const pos = [];
for (let i = 0; i < argv.length; i++) {
  const a = argv[i];
  if (a.startsWith('--')) { const k = a.slice(2); const v = argv[i + 1]; if (v === undefined || v.startsWith('--')) flags.set(k, true); else { flags.set(k, v); i++; } } else pos.push(a);
}
const JSON_OUT = flags.has('json');
const say = (m) => { if (!JSON_OUT) process.stderr.write(`${m}\n`); };
const rel = (root, f) => relative(root, f).split('\\').join('/');

function studioRoot() {
  const root = findStudio();
  if (!root) throw new Error('not inside a Homie studio (no studio.json here or above). The studio-setup skill makes one.');
  return root;
}
function gameDir(root, game) {
  if (!SLUG.test(String(game ?? ''))) throw new Error('name the game: models.mjs <command> <game> …');
  const d = experienceDir(root, game);
  if (!existsSync(experienceJson(d)) && !existsSync(join(d, 'CODEX.md'))) throw new Error(`no game "${game}" in games/`);
  return d;
}
/** The game's money for generated models: art/<game>-models/budget.json (one cap for every model of the game). */
const budgetDir = (root, game) => join(root, 'art', `${game}-models`);

/** The studio's own pinned homie-studio (HOMIE_STUDIO_CLI points at another), run with --json. */
function studio(root, args) {
  const cli = process.env.HOMIE_STUDIO_CLI || join(root, 'node_modules', '@homie-rocks', 'studio', 'bin', 'homie-studio.mjs');
  if (!existsSync(cli)) throw new Error('the studio has no node_modules yet: run npm install in the studio');
  const r = spawnSync(process.execPath, [cli, ...args, '--json'], { cwd: root, encoding: 'utf8', maxBuffer: 64 * 1024 * 1024, timeout: 10 * 60_000 });
  let out = null;
  try { out = JSON.parse(r.stdout); } catch { out = null; }
  if (r.status !== 0 || !out) throw new Error(`homie-studio ${args.slice(0, 2).join(' ')}: ${out?.why ?? (r.stderr || r.stdout).trim().split('\n').slice(-3).join(' ')}`);
  return out;
}

/** A receipt line: the game's model budget (running total), art/receipts.jsonl, and HOMIE_SPEND_LEDGER when set. */
function receipt(root, game, line) {
  const at = new Date().toISOString();
  const dir = budgetDir(root, game);
  const b = readBudget(dir);
  if (b) {
    b.spent = +(b.spent + (Number(line.cost) || 0)).toFixed(6);
    b.calls.push({ at, provider: line.provider, model: line.model, cost: line.cost, unit: line.unit, requestId: line.requestId ?? null, artifact: line.artifact ?? null });
    writeJson(join(dir, 'budget.json'), b);
  }
  mkdirSync(join(root, 'art'), { recursive: true });
  appendFileSync(join(root, 'art', 'receipts.jsonl'), `${JSON.stringify({ schema: 'homie.media-receipt/1', at, game, ...line })}\n`);
  const ledger = process.env.HOMIE_SPEND_LEDGER;
  if (ledger) {
    try { appendFileSync(ledger, `${JSON.stringify({ schema: 'homie.brand-spend/1', at, provider: line.provider, model: line.model, jobId: line.requestId ?? null, units: line.units ?? null, unit: line.unitName ?? line.unit, usd: line.cost, credits: null, unpriced: null, brand: process.env.HOMIE_SPEND_BRAND ?? null, attribution: process.env.HOMIE_SPEND_ATTRIBUTION ?? null, artifact: line.artifact ?? null })}\n`); } catch (e) { say(`could not write the ledger: ${e.message}`); }
  }
}

/** A file's real picture type from its first bytes; the extension made to match (fal answers PNG or JPEG). */


/**
 * One paid call: priced (live), checked against the cap, asked for without --yes, receipted on acceptance, resumed on
 * a rerun. Returns { ok, file, usd } or { ok: false, needs: 'approval', price } or { already }.
 */


/* ---------------------------------------------------------------- commands */

function budget(root) {
  const game = pos[1];
  gameDir(root, game);
  const cap = Number(flags.get('cap'));
  if (!(cap >= 0 && cap <= 1000)) throw new Error('--cap <US dollars the person agreed to for this game\'s models>');
  const b = setBudget(budgetDir(root, game), { provider: 'fal', unit: 'usd', cap, note: 'generated models and mood images for this game' });
  // The decisions file carries the art budget too (the automatic path uses only free routes without one).
  try { studio(root, ['style', 'init', game, '--budget', String(cap)]); } catch (error) { say(`decisions not updated: ${error.message}`); }
  return { ok: true, command: 'budget', game, cap: b.cap, spent: b.spent };
}

/** The concept's words: the thing, then the derived style prompt (never edited by hand), then how to frame it. */

/** A character's concept words: who, the derived style prompt without its prop framing, then an A-pose, front view. */


/** A library item's thumbnail into the job's folder, as a style reference (CC0, the library's own render). */

/**
 * A connector's job receipt, read tolerantly (what was saved when the connector accepted the job): its request id, its
 * endpoint, what it cost or was estimated to cost, and when. A receipt that says the job is not finished is refused.
 */
function jobReceipt(file, { usd = null } = {}) {
  if (!file) return null;
  const abs = resolve(String(file));
  if (!existsSync(abs)) throw new Error(`no receipt at ${file}`);
  let j;
  try { j = JSON.parse(readFileSync(abs, 'utf8')); } catch { throw new Error(`${file} is not JSON (a connector job receipt: its request id, endpoint and cost)`); }
  const requestId = [j.requestId, j.request_id, j.id, j.job?.request_id, j.job?.id].find((x) => typeof x === 'string' && x.trim());
  const endpoint = [j.endpoint, j.model, j.app, j.endpoint_id, j.job?.endpoint].find((x) => typeof x === 'string' && x.trim());
  if (!requestId) throw new Error(`${file} names no request id (requestId): without it a job cannot be told from the one before, so it is not recorded`);
  if (!endpoint) throw new Error(`${file} names no endpoint (endpoint or model): the provenance of the file would be a guess`);
  const status = String(j.status ?? j.state ?? '').toLowerCase();
  if (status && !/^(completed?|succe(ss|eded)|ok|done|finished)$/.test(status)) throw new Error(`${file} says the job is "${status}", not finished: import it when the connector has the result`);
  const pick = [usd, j.usd, j.cost, j.price?.usd, j.estimate?.usd, j.estimatedCost, j.estimated_cost, j.price].map((x) => (x === null || x === undefined || x === '' || typeof x === 'object' ? NaN : Number(x))).find((n) => Number.isFinite(n) && n >= 0);
  // No cost on the receipt: the registry's recorded price for that endpoint, said as such. Never zero by default.
  let price = Number.isFinite(pick) ? { usd: pick, basis: usd !== null && Number(usd) === pick ? 'the price given with --usd' : 'the connector receipt\'s own cost' } : null;
  if (!price) throw new Error(`${file} names no cost for ${endpoint}: say what it cost with --usd <US dollars> (an unknown cost is never recorded as nothing)`);
  return { file: abs, requestId: requestId.trim(), endpoint: endpoint.trim(), price, at: typeof (j.at ?? j.createdAt ?? j.created_at) === 'string' ? (j.at ?? j.createdAt ?? j.created_at) : null };
}

/** Request ids this studio has a receipt line for already: importing the same connector job twice counts it once. */
function receipted(root) {
  try { return new Set(readFileSync(join(root, 'art', 'receipts.jsonl'), 'utf8').split('\n').filter(Boolean).map((l) => { try { return JSON.parse(l).requestId ?? null; } catch { return null; } }).filter(Boolean)); } catch { return new Set(); }
}

/**
 * `import`: a job a fal connector already ran, into the game as if this script had run it. The money was spent on the
 * connector's sign-in, so nothing here can stop it; what this does is keep the books and the provenance true: the cap
 * the person agreed to is still checked (a job past it is refused until they raise it), every request id gets one
 * receipt line, the raw file is kept beside its job, and the asset is recorded with each step's endpoint and receipt.
 */
async function importJob(root) {
  const [, game, asset] = pos;
  gameDir(root, game);
  if (!SLUG.test(String(asset ?? ''))) throw new Error('name the asset: models.mjs import <game> <asset id> --receipt <job.json> --file <model.glb>');
  if (!flags.get('file') || !flags.get('receipt')) throw new Error('models.mjs import <game> <asset> --receipt <the connector\'s job receipt, JSON> --file <the completed .glb> [--kind prop|character] [--concept <image> --concept-receipt <job.json>]');
  const src = resolve(String(flags.get('file')));
  if (!existsSync(src)) throw new Error(`no completed file at ${flags.get('file')}`);
  if (!/\.glb$/i.test(src)) throw new Error('the completed file must be a .glb (ask the connector for the GLB output)');
  const kind = flags.get('kind') === 'character' ? 'character' : 'prop';
  const mesh = jobReceipt(flags.get('receipt'), { usd: flags.has('usd') ? Number(flags.get('usd')) : null });
  const conceptSrc = flags.get('concept') ? resolve(String(flags.get('concept'))) : null;
  if (conceptSrc && !existsSync(conceptSrc)) throw new Error(`no concept image at ${flags.get('concept')}`);
  const concept = conceptSrc && flags.get('concept-receipt') ? jobReceipt(flags.get('concept-receipt')) : null;
  const seen = receipted(root);
  const jobs = [...(concept ? [{ ...concept, what: `the concept image for ${asset}` }] : []), { ...mesh, what: kind === 'character' ? `the rigged 3D character for ${asset}` : `the 3D model for ${asset}` }];
  const fresh = jobs.filter((j) => !seen.has(j.requestId));
  const owed = +fresh.reduce((n, j) => n + j.price.usd, 0).toFixed(6);
  const dir = join(root, 'art', asset);
  if (flags.has('dry-run')) return { ok: true, command: 'import', dryRun: true, game, asset, kind, jobs: jobs.map((j) => ({ what: j.what, endpoint: j.endpoint, requestId: j.requestId, usd: j.price.usd, basis: j.price.basis, counted: seen.has(j.requestId) ? 'already receipted: not counted again' : 'would be counted' })), usd: owed, budget: readBudget(budgetDir(root, game)) ? { cap: readBudget(budgetDir(root, game)).cap, spent: readBudget(budgetDir(root, game)).spent } : null };
  // The same cap as a call made here. It is checked before anything is written, so a refused import leaves no trace.
  if (fresh.length) {
    try { checkBudget(budgetDir(root, game), owed, { provider: 'fal', unit: 'usd' }); } catch (error) { throw new Error(`${error.message} (this job already ran on the fal connector; importing it only records it, and it is recorded once the budget allows it)`); }
  }
  mkdirSync(join(dir, 'raw'), { recursive: true });
  const keep = (from, to) => { if (resolve(from) !== resolve(to)) copyFileSync(from, to); return to; };
  const rawFile = keep(src, join(dir, 'raw', kind === 'character' ? 'rigged.glb' : 'mesh.glb'));
  const conceptFile = conceptSrc ? keep(conceptSrc, join(dir, `concept${extname(conceptSrc).toLowerCase() || '.png'}`)) : null;
  // Beside each file, what `paid` leaves beside one it made: a later `prop --mesh` then finds the job done and never pays for it again.
  const answer = (file, j) => writeJson(`${file}.json`, { model: j.endpoint, requestId: j.requestId, price: { usd: j.price.usd, basis: j.price.basis }, at: j.at ?? new Date().toISOString(), via: 'connector', receipt: rel(root, j.file).startsWith('..') ? null : rel(root, j.file) });
  answer(rawFile, mesh);
  if (conceptFile && concept) answer(conceptFile, concept);
  for (const j of fresh) receipt(root, game, { provider: 'fal', via: 'connector', model: j.endpoint, requestId: j.requestId, cost: j.price.usd, unit: 'usd', basis: j.price.basis, artifact: rel(root, j === mesh || j.requestId === mesh.requestId ? rawFile : conceptFile), asset, what: j.what });
  const steps = [
    ...(concept ? [{ what: 'concept', provider: 'fal', via: 'connector', endpoint: concept.endpoint, usd: concept.price.usd, receipt: rel(root, `${conceptFile}.json`), requestId: concept.requestId, at: concept.at }] : []),
    { what: kind === 'character' ? 'mesh and rig' : 'mesh', provider: 'fal', via: 'connector', endpoint: mesh.endpoint, usd: mesh.price.usd, receipt: rel(root, `${rawFile}.json`), requestId: mesh.requestId, at: mesh.at },
  ];
  const stepsFile = join(dir, 'steps.json');
  writeJson(stepsFile, steps);
  const card = String(flags.get('card') ?? `${kind === 'character' ? 'Players' : 'Items'}/${asset}`);
  const added = studio(root, ['assets', 'add', game, '--file', rel(root, rawFile), '--route', 'generated', '--license', 'generated', '--as', asset, '--kind', kind, ...(kind === 'character' ? ['--rigged'] : []), '--card', card, '--steps', rel(root, stepsFile), ...(conceptFile ? ['--concept', rel(root, conceptFile)] : []), '--slug', asset, ...(flags.get('clips-from') ? ['--clips-from', String(flags.get('clips-from'))] : []), ...(flags.has('height') ? ['--height', String(Number(flags.get('height')))] : [])]);
  const b = readBudget(budgetDir(root, game));
  return { ok: true, command: 'import', game, asset, kind, via: 'connector', model: added.model ?? added.file, before: added.before, after: added.after, usd: owed, counted: fresh.map((j) => j.requestId), alreadyCounted: jobs.filter((j) => seen.has(j.requestId)).map((j) => j.requestId), spent: b?.spent ?? null, cap: b?.cap ?? null, receipts: steps.map((s) => s.receipt), next: `homie-studio assets lineup ${game} (true scale, silhouettes, palette drift); look at it` };
}

function receiptsOf(root) {
  const game = pos[1];
  const lines = existsSync(join(root, 'art', 'receipts.jsonl')) ? readFileSync(join(root, 'art', 'receipts.jsonl'), 'utf8').trim().split('\n').filter(Boolean).map((l) => { try { return JSON.parse(l); } catch { return null; } }).filter((x) => x && (!game || x.game === game)) : [];
  const b = game ? readBudget(budgetDir(root, game)) : null;
  return { ok: true, command: 'receipts', game: game ?? null, count: lines.length, usd: +lines.reduce((n, l) => n + (Number(l.cost) || 0), 0).toFixed(3), budget: b ? { cap: b.cap, spent: b.spent } : null, receipts: lines.map((l) => ({ at: l.at, what: l.what ?? l.artifact, model: l.model, usd: l.cost, requestId: l.requestId })) };
}

async function main() {
  const cmd = pos[0];
  if (!cmd || cmd === 'help' || flags.has('help')) return { ok: true, command: 'help', usage: readFileSync(fileURLToPath(import.meta.url), 'utf8').split('*/')[0].replace(/^#!.*\n\/\*\*?/, '').replace(/^ \* ?/gm, '').trim() };
  const root = studioRoot();
  if (cmd === 'budget') return budget(root);
  if (cmd === 'import') return importJob(root);
  if (cmd === 'receipts') return receiptsOf(root);
  return { ok: false, command: cmd, why: `unknown command "${cmd}" (models.mjs help)` };
}

const print = (o) => {
  if (JSON_OUT) { process.stdout.write(`${JSON.stringify(o, null, 2)}\n`); return; }
  if (o.ok === false && o.why) { process.stdout.write(`models: ${o.why}\n`); return; }
  for (const [k, v] of Object.entries(o)) if (k !== 'ok' && k !== 'command' && v !== undefined) process.stdout.write(`${k}: ${typeof v === 'object' ? JSON.stringify(v) : v}\n`);
};

try {
  const r = await main();
  if (r) { print(r); if (r.ok === false) process.exitCode = 1; }
} catch (error) {
  print({ ok: false, why: error instanceof Error ? error.message : String(error) });
  process.exitCode = 1;
}
