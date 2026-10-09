/**
 * The studio a media job works in (the folder with studio.json at or above the
 * current directory), its music/ and videos/ manifests, and its money: every
 * paid call is priced before it is made, checked against the budget the person
 * set, and written to the studio's receipt file the moment the provider accepts it.
 */
import { spawnSync } from 'node:child_process';
import { appendFileSync, existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join, relative, resolve } from 'node:path';

export function findStudio(from = process.cwd()) {
  let at = resolve(from);
  for (;;) {
    if (existsSync(join(at, 'studio.json'))) return at;
    const up = dirname(at);
    if (up === at) return null;
    at = up;
  }
}

export function requireStudio(from) {
  const root = findStudio(from);
  if (!root) throw new Error('not inside a Homie studio (no studio.json here or above). The studio-setup skill makes one.');
  return root;
}

export const SLUG = /^[a-z0-9][a-z0-9-]{0,39}$/;
export function slugify(text) {
  return String(text ?? '').normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 40).replace(/-+$/g, '') || 'untitled';
}

export function readJson(file, fallback = null) {
  try { return JSON.parse(readFileSync(file, 'utf8')); } catch { return fallback; }
}
export function writeJson(file, value) {
  mkdirSync(dirname(file), { recursive: true });
  writeFileSync(file, `${JSON.stringify(value, null, 2)}\n`);
}

export function readManifest(root, kind) {
  const m = readJson(join(root, kind, 'manifest.json'), null) ?? { v: 1, items: [] };
  return { v: 1, ...m, items: Array.isArray(m.items) ? m.items : [] };
}

/**
 * Put an entry in a manifest: replace the one with the same slug, else add it FIRST (the site shows newest first).
 * A file that keeps its path keeps its R2 record (`r2`, from `homie-studio media move`): the studio checks it against
 * the file's SHA-256 before it trusts it, so a re-cut at the same path is uploaded again, never served stale.
 */
export function upsertEntry(root, kind, entry) {
  const m = readManifest(root, kind);
  const i = m.items.findIndex((x) => x?.slug === entry.slug);
  if (i >= 0 && Array.isArray(entry.files)) {
    const held = new Map((m.items[i].files ?? []).filter((f) => f?.path && f?.r2).map((f) => [f.path, f.r2]));
    entry = { ...entry, files: entry.files.map((f) => (f?.path && held.has(f.path) && !f.r2 ? { ...f, r2: held.get(f.path) } : f)) };
  }
  if (i >= 0) m.items[i] = { ...m.items[i], ...entry };
  else m.items.unshift(entry);
  writeJson(join(root, kind, 'manifest.json'), m);
  return m.items.find((x) => x.slug === entry.slug);
}

export function getEntry(root, kind, slug) {
  return readManifest(root, kind).items.find((x) => x?.slug === slug) ?? null;
}

/** A path relative to the studio, with forward slashes (what the manifest records). */
export const rel = (root, abs) => relative(root, abs).split('\\').join('/');

/* ---------------------------------------------------------------- money */

/**
 * The job's budget file (<job>/budget.json): { provider, unit, cap, spent, calls[] }.
 * `unit` is "usd" for fal and "credits" for ElevenLabs.
 */
export function readBudget(jobDir) { return readJson(join(jobDir, 'budget.json'), null); }

export function setBudget(jobDir, { provider, unit, cap, approvedBy = 'the person', note = null }) {
  const prev = readBudget(jobDir);
  const b = { provider, unit, cap: Number(cap), spent: prev?.spent ?? 0, approvedBy, approvedAt: new Date().toISOString(), note, calls: prev?.calls ?? [] };
  writeJson(join(jobDir, 'budget.json'), b);
  return b;
}

/** Refuses (throws) a call that would take the job past its cap, or any call with no budget set. */
export function checkBudget(jobDir, cost, { provider, unit }) {
  const b = readBudget(jobDir);
  if (!b) throw new Error(`no budget set for this job: ask the person how much to spend (${unit}) and run \`budget --cap <n>\` first`);
  if (b.provider !== provider || b.unit !== unit) throw new Error(`this job's budget is for ${b.provider} in ${b.unit}, not ${provider} in ${unit}`);
  if (!(Number.isFinite(cost) && cost >= 0)) throw new Error('the cost of this call is unknown, so it is not made (price it first)');
  if (b.spent + cost > b.cap + 1e-9) throw new Error(`REFUSED: ${fmt(b.spent, unit)} spent + ${fmt(cost, unit)} for this call would pass the cap of ${fmt(b.cap, unit)}. Ask the person before raising it.`);
  return b;
}

export const fmt = (n, unit) => (unit === 'usd' ? `US$${Number(n).toFixed(2)}` : `${Math.round(n)} ${unit}`);

/**
 * One receipt line: into the job's budget (running total), the studio's receipts
 * file (<kind>/receipts.jsonl), and the optional ledger named by HOMIE_SPEND_LEDGER
 * (a house or team ledger; the studio's own file is always written).
 */
export function receipt(root, jobDir, line) {
  const at = new Date().toISOString();
  const row = { schema: 'homie.media-receipt/1', at, ...line };
  const b = readBudget(jobDir);
  if (b) {
    b.spent = +(b.spent + (Number(line.cost) || 0)).toFixed(6);
    if (line.model !== 'reconcile') b.calls.push({ at, provider: line.provider, model: line.model, cost: line.cost, unit: line.unit, requestId: line.requestId ?? null, artifact: line.artifact ?? null, ...(line.pending !== undefined ? { pending: line.pending, quoted: line.quoted ?? null, measured: line.measured ?? null, balanceBefore: line.balanceBefore ?? null } : {}) });
    writeJson(join(jobDir, 'budget.json'), b);
  }
  const kind = rel(root, jobDir).startsWith('videos/') ? 'videos' : 'music';
  mkdirSync(join(root, kind), { recursive: true });
  appendFileSync(join(root, kind, 'receipts.jsonl'), `${JSON.stringify(row)}\n`);
  const ledger = process.env.HOMIE_SPEND_LEDGER;
  if (ledger) {
    try {
      appendFileSync(ledger, `${JSON.stringify({
        schema: 'homie.brand-spend/1', at, provider: line.provider, model: line.model, jobId: line.requestId ?? null,
        units: line.units ?? null, unit: line.unitName ?? line.unit, usd: line.unit === 'usd' ? line.cost : null,
        credits: line.unit === 'credits' ? line.cost : null, unpriced: null, brand: process.env.HOMIE_SPEND_BRAND ?? null,
        attribution: process.env.HOMIE_SPEND_ATTRIBUTION ?? null, artifact: line.artifact ?? null,
      })}\n`);
    } catch (error) { process.stderr.write(`could not write the ledger ${ledger}: ${error.message}\n`); }
  }
  return row;
}

/** Does this studio's @homie-rocks/studio know song and video pages? (`homie-studio media list` exists.) */
export function studioHasMediaPages(root) {
  const bin = join(root, 'node_modules', '.bin', 'homie-studio');
  if (!existsSync(bin)) return { ok: false, why: 'the studio has no node_modules yet: run npm install in the studio' };
  const r = spawnSync(bin, ['media', 'list', '--json'], { cwd: root, encoding: 'utf8', timeout: 60_000 });
  // 0.18.0 and later answer with `moves` and have `media move`: big media goes to R2, checked by SHA-256, at the same address.
  try { const j = JSON.parse(r.stdout); if (j.command === 'media list') return { ok: true, move: Array.isArray(j.moves) }; } catch { /* old CLI */ }
  const pkg = readJson(join(root, 'node_modules', '@homie-rocks', 'studio', 'package.json'), {});
  return { ok: false, why: `this studio's @homie-rocks/studio ${pkg.version ?? '(unknown)'} predates song and video pages; update it to the version that has \`homie-studio media list\`` };
}

/** Source paths for media and review jobs; built assets retain the shared games namespace. */
export const experienceDir = (root, id) => join(root, existsSync(join(root, 'apps', id, 'app.json')) ? 'apps' : 'games', id);
export const experienceJson = (dir) => join(dir, existsSync(join(dir, 'app.json')) ? 'app.json' : 'game.json');
