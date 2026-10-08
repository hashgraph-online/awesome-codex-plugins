#!/usr/bin/env node
/**
 * models.mjs: 3D props made for a game from its locked style, on the creator's OWN fal account, under a hard budget,
 * with a receipt for every call. The free parts (the starter library, optimising, checking, the lineup)
 * are `npx --no-install homie-studio assets …`; this script is only the paid route and its registry.
 *
 *   check                                  the LOCAL fal key (a free check), the studio, the registry's endpoints; a fal
 *                                          connector signed in from the app is a separate sign-in this script cannot see
 *   registry [--write]                     every registry endpoint's live price again (free), and what moved or retired
 *   budget <game> --cap <usd>              what the person agreed to spend on this game's generated models
 *   quote <game> [--count <n>]             what one prop costs today (concept + mesh), and n of them, against the cap
 *   prop <game> <asset> --card "Items/Lantern" --what "<the thing, in plain words>" [--height <m>] [--faces 1500]
 *                                          [--dry-run | --yes]
 *        step 1 (no concept yet): ONE concept image in the locked style (the derived style prompt; the golden images as
 *          references when there are any), plain background, even light. Then STOP: look at it.
 *        step 2 (`prop … --mesh --yes`): Tripo P1 image-to-3D from that concept (textured, face_limit from the tier),
 *          then `homie-studio assets add` makes it phone-sized for free and records it with every step and receipt.
 *   character <game> <asset> --card "Players/Ranger" --what "<who, in plain words>" [--height <m>] [--like <library item>]
 *                                          [--faces 7000] [--dry-run | --yes]
 *        step 1: ONE full-body concept in an A-pose, front view, in the locked style (the golden images, or --like: a
 *          library character's thumbnail as the style reference). Then STOP: look at it.
 *        step 2 (`character … --mesh --yes`): Meshy 7.1 image-to-3D with a humanoid auto-rig (textured, about US$1.40),
 *          then `homie-studio assets add --rigged` makes it phone-sized for free, maps its skeleton to the standard and
 *          retargets the library's clips onto it (KayKit's CC0 humanoid set by default; --clips-from another).
 *   import <game> <asset> --receipt <job.json> --file <completed.glb> [--kind prop|character] [--card "…"] [--height <m>]
 *                                          [--concept <image> --concept-receipt <job.json>] [--usd <n>] [--dry-run]
 *        a job ALREADY RUN through a fal connector (its MCP server, signed in from the app, with no key in this shell),
 *        brought in under the same budget, receipts and provenance as one made here: the receipt's request id and cost
 *        go to art/receipts.jsonl and the game's budget (refused with no budget, or past the cap), the file is kept in
 *        art/<asset>/raw/, then `homie-studio assets add` makes it phone-sized and records every step. No network; the
 *        same receipt imported twice is counted once.
 *   mood <game> <a|b|c|all> [--yes]        a painted mood image per style-board direction (a target, never shipped)
 *   receipts <game>                        what this game's models cost so far, from art/receipts.jsonl
 *
 * Every paid call is priced from fal's own pricing API first (a credit-billed endpoint through the registry's credit
 * table), refused with no budget or past the cap, asked again without --yes, receipted the moment fal accepts it, and
 * resumed (never paid twice) from <out>.request. Never a retry loop: look, change the words, run once more.
 * FAL_QUEUE_URL, FAL_API_URL and FAL_STORAGE_URL point it at a test double. Every command takes --json.
 */
import { spawnSync } from 'node:child_process';
import { appendFileSync, copyFileSync, existsSync, mkdirSync, readFileSync, renameSync, writeFileSync } from 'node:fs';
import { dirname, extname, join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { SLUG, checkBudget, findStudio, readBudget, readJson, setBudget, writeJson } from '../../music/scripts/lib/studio.mjs';
import { checkKey, falKey, priceOf, run as falRun, unitPrice } from '../../video/scripts/lib/fal.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const REGISTRY = join(HERE, '..', 'references', 'models.json');
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
const registry = () => JSON.parse(readFileSync(REGISTRY, 'utf8'));

function studioRoot() {
  const root = findStudio();
  if (!root) throw new Error('not inside a Homie studio (no studio.json here or above). The studio-setup skill makes one.');
  return root;
}
function gameDir(root, game) {
  if (!SLUG.test(String(game ?? ''))) throw new Error('name the game: models.mjs <command> <game> …');
  const d = join(root, 'games', game);
  if (!existsSync(join(d, 'game.json')) && !existsSync(join(d, 'CODEX.md'))) throw new Error(`no game "${game}" in games/`);
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
function fixExt(file) {
  const b = readFileSync(file).subarray(0, 4);
  const ext = b[0] === 0xff && b[1] === 0xd8 ? '.jpg' : b[0] === 0x89 && b[1] === 0x50 ? '.png' : b.toString('latin1', 0, 4) === 'RIFF' ? '.webp' : null;
  if (!ext || file.endsWith(ext)) return file;
  const to = file.replace(/\.[a-z0-9]+$/i, ext);
  renameSync(file, to);
  for (const side of ['.json', '.request']) if (existsSync(`${file}${side}`)) renameSync(`${file}${side}`, `${to}${side}`);
  return to;
}

/**
 * One paid call: priced (live), checked against the cap, asked for without --yes, receipted on acceptance, resumed on
 * a rerun. Returns { ok, file, usd } or { ok: false, needs: 'approval', price } or { already }.
 */
async function paid(root, game, { model, input, out, base, credits = null, addons = null, what, asset }) {
  // Done before (the file and its answer are both there): never paid twice.
  const done = [...new Set(['.png', '.jpg', '.webp', '.glb'].map((e) => out.replace(/\.[a-z0-9]+$/i, e)))].find((f) => existsSync(f) && existsSync(`${f}.json`));
  if (done) return { ok: true, already: true, file: done, usd: readJson(`${done}.json`, {})?.price?.usd ?? 0 };
  const p = await priceOf(model, input, { credits, addons });
  if (flags.has('dry-run')) return { ok: true, dryRun: true, price: p };
  const dir = budgetDir(root, game);
  const resuming = existsSync(`${out}.request`);
  if (!resuming) {
    const b = checkBudget(dir, p.usd, { provider: 'fal', unit: 'usd' });
    if (!flags.has('yes')) return { ok: false, needs: 'approval', price: p, budget: { cap: b.cap, spent: b.spent }, why: `${what} costs about US$${p.usd.toFixed(3)} (${p.basis}) on the person's own fal account; US$${b.spent.toFixed(2)} of US$${b.cap.toFixed(2)} spent so far. Run it with --yes once that is fine.` };
  }
  const r = await falRun(model, input, {
    out, base, uploads: join(dir, 'uploads.json'), price: p, log: say,
    onAccepted: async (q) => { receipt(root, game, { provider: 'fal', model, requestId: q.request_id, cost: p.usd, unit: 'usd', units: p.units, unitName: p.unit, basis: p.basis, artifact: rel(root, out), asset, what }); },
  });
  return { ok: true, file: r.files[0], requestId: r.requestId, usd: p.usd, price: p };
}

/* ---------------------------------------------------------------- commands */

/**
 * Two different sign-ins, which this check used to report as one. FAL_KEY is what THIS script pays with. A fal
 * connector (fal's MCP server, signed in from the app) is signed in somewhere this script cannot see: it can be ready
 * while there is no key here, and neither says anything about the other.
 */
const NO_LOCAL_KEY = 'no local FAL_KEY in this shell, so this script cannot make a paid call itself. That says nothing about a fal connector: one signed in from the app is a separate sign-in this script cannot see or use, and it may well be ready. Two ways on: set FAL_KEY and generate here (prop, character), or generate through the connector and bring the finished job in with `models.mjs import <game> <asset> --receipt <job.json> --file <model.glb>` (the same budget, receipts and provenance). The starter library, optimising and the checks need neither';

async function check() {
  const root = findStudio();
  const reg = registry();
  const local = Boolean(falKey());
  const key = local ? await checkKey() : { ok: false, why: NO_LOCAL_KEY };
  const auth = {
    localKey: key.ok ? 'works (checked free)' : local ? `set, but not accepted: ${key.why}` : 'not set',
    connector: 'not checked here: a fal connector signs in from the app, apart from this script. Ask it for its own account status; if it is ready, generate there and `import` the finished job',
    paidRoutes: [...(key.ok ? ['prop, character and mood here (FAL_KEY)'] : []), 'import: a job a fal connector already ran, with its receipt and its file'],
  };
  return { ok: true, command: 'check', studio: root, fal: key.ok ? 'the key works (checked free)' : key.why, auth, registry: { checked: reg.checked, concept: reg.concept.noRefs.endpoint, conceptWithRefs: reg.concept.withRefs.endpoint, mesh: reg.mesh.prop.endpoint, mood: reg.mood.endpoint } };
}

async function registryCheck() {
  const reg = registry();
  const rows = [];
  const entries = [['concept.withRefs', reg.concept.withRefs], ['concept.noRefs', reg.concept.noRefs], ['mesh.prop', reg.mesh.prop], ['mood', reg.mood], ...reg.mesh.fallbacks.map((f, i) => [`mesh.fallbacks.${i}`, f])];
  for (const [at, e] of entries) {
    try {
      const u = await unitPrice(e.endpoint);
      const usd = /^credits?$/i.test(u.unit) && e.credits ? +(u.unitPrice * (e.credits.base + (e.credits.texture && e.input?.texture !== false ? e.credits.texture : 0))).toFixed(4) : u.unitPrice;
      const moved = Math.abs(usd - Number(e.price.usd)) > 1e-6;
      rows.push({ at, endpoint: e.endpoint, unit: u.unit, unitPrice: u.unitPrice, usd, recorded: e.price.usd, moved });
      if (flags.has('write')) { e.price.usd = usd; e.price.read = new Date().toISOString().slice(0, 10); }
    } catch (error) { rows.push({ at, endpoint: e.endpoint, error: /404/.test(error.message) ? 'retired or renamed (404): find its successor on fal.ai/explore/3d and update the registry' : error.message }); }
  }
  if (flags.has('write')) { reg.checked = new Date().toISOString().slice(0, 10); writeFileSync(REGISTRY, `${JSON.stringify(reg, null, 2)}\n`); }
  return { ok: rows.every((r) => !r.error), command: 'registry', checked: reg.checked, rows };
}

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
function conceptInput(root, game, what) {
  const reg = registry();
  const style = studio(root, ['style', 'prompt', game]);
  const golden = (style.golden ?? []).map((g) => join('games', game, g.path)).filter((p) => existsSync(join(root, p))).slice(0, 4);
  const prompt = `${String(what).trim().replace(/\.$/, '')}. A single game prop, the whole object in frame, centred, seen three-quarters from slightly above. ${style.prompt.text}.`;
  if (golden.length) {
    const c = reg.concept.withRefs;
    return { model: c.endpoint, input: { ...c.input, prompt: `${prompt} Match the style of the reference images exactly; do not copy their content.`, [c.refs]: golden.map((g) => `@file:${g}`) }, refs: golden, rev: style.prompt.rev };
  }
  const c = reg.concept.noRefs;
  return { model: c.endpoint, input: { ...c.input, prompt }, refs: [], rev: style.prompt.rev };
}

async function prop(root) {
  const [, game, asset] = pos;
  gameDir(root, game);
  if (!SLUG.test(String(asset ?? ''))) throw new Error('name the asset: models.mjs prop <game> <asset id> --card "Items/<Name>" --what "<the thing>"');
  const reg = registry();
  const dir = join(root, 'art', asset);
  mkdirSync(join(dir, 'raw'), { recursive: true });
  const conceptFile = ['concept.png', 'concept.jpg', 'concept.webp'].map((f) => join(dir, f)).find((f) => existsSync(f) && existsSync(`${f}.json`));
  const card = String(flags.get('card') ?? `Items/${asset}`);
  const height = flags.has('height') ? Number(flags.get('height')) : null;
  // Step 1: the concept, then stop and look.
  if (!conceptFile || flags.has('concept-again')) {
    const what = flags.get('what');
    if (!what) throw new Error('--what "<the thing, in plain words: shape, material, size>" (the style comes from the game\'s locked decisions)');
    const c = conceptInput(root, game, what);
    if (flags.has('concept-again') && conceptFile) {
      const was = `concept-was-${Date.now()}`;
      for (const f of [conceptFile, `${conceptFile}.json`, `${conceptFile}.request`]) if (existsSync(f)) renameSync(f, f.replace(/concept(?=\.[a-z]+)/, was));
    }
    const meshPrice = await priceOf(reg.mesh.prop.endpoint, { ...reg.mesh.prop.input, image_url: 'x' }, { credits: reg.mesh.prop.credits }).catch(() => null);
    const r = await paid(root, game, { model: c.model, input: c.input, out: join(dir, 'concept.png'), base: root, what: `the concept image for ${asset}`, asset });
    if (!r.ok || r.dryRun) return { ...r, command: 'prop', step: 'concept', game, asset, then: meshPrice ? { what: 'the mesh (Tripo P1, textured)', usd: meshPrice.usd } : null, total: r.price && meshPrice ? +(r.price.usd + meshPrice.usd).toFixed(3) : null };
    const file = fixExt(r.file);
    writeJson(join(dir, 'concept.meta.json'), { what: String(what), card, height, model: c.model, refs: c.refs, promptRev: c.rev, prompt: c.input.prompt });
    return { ok: true, command: 'prop', step: 'concept', game, asset, concept: rel(root, file), usd: r.usd, spent: readBudget(budgetDir(root, game))?.spent ?? null, next: `look at ${rel(root, file)} first (does it read as the thing, in the game's style, whole, on a plain background?). Then: models.mjs prop ${game} ${asset} --mesh --yes (about US$${meshPrice?.usd ?? '0.50'}); or change --what and --concept-again (never a loop)` };
  }
  if (!flags.has('mesh')) return { ok: true, command: 'prop', step: 'look', game, asset, concept: rel(root, conceptFile), next: `the concept exists: look at it, then models.mjs prop ${game} ${asset} --mesh --yes` };
  // Step 2: the mesh from the concept, then optimised and recorded for free.
  const meta = readJson(join(dir, 'concept.meta.json'), {});
  const m = reg.mesh.prop;
  const tierFaces = Number(flags.get('faces') ?? 1500);
  const input = { ...m.input, image_url: `@file:${rel(root, conceptFile)}`, [m.faceLimit]: tierFaces };
  const meshOut = join(dir, 'raw', 'mesh.glb');
  const r = await paid(root, game, { model: m.endpoint, input, out: meshOut, base: root, credits: m.credits, what: `the 3D model for ${asset}`, asset });
  if (!r.ok || r.dryRun) return { ...r, command: 'prop', step: 'mesh', game, asset };
  const concept = readJson(`${conceptFile}.json`, {});
  const mesh = readJson(`${r.file}.json`, {});
  const steps = [
    { what: 'concept', provider: 'fal', endpoint: concept.model ?? meta.model, usd: concept.price?.usd ?? null, receipt: rel(root, `${conceptFile}.json`), refs: meta.refs ?? [], promptRev: meta.promptRev ?? null, requestId: concept.requestId ?? null, at: concept.at ?? null },
    { what: 'mesh', provider: 'fal', endpoint: m.endpoint, input: { [m.faceLimit]: tierFaces, texture: true }, usd: mesh.price?.usd ?? r.usd, receipt: rel(root, `${r.file}.json`), requestId: mesh.requestId ?? r.requestId ?? null, at: mesh.at ?? null },
  ];
  const stepsFile = join(dir, 'steps.json');
  writeJson(stepsFile, steps);
  const added = studio(root, ['assets', 'add', game, '--file', rel(root, r.file), '--route', 'generated', '--license', 'generated', '--as', asset, '--kind', 'prop', '--card', meta.card ?? card, '--steps', rel(root, stepsFile), '--concept', rel(root, conceptFile), '--slug', asset, ...((meta.height ?? height) ? ['--height', String(meta.height ?? height)] : [])]);
  return { ok: true, command: 'prop', step: 'mesh', game, asset, model: added.file, before: added.before, after: added.after, usd: r.usd, spent: readBudget(budgetDir(root, game))?.spent ?? null, receipts: steps.map((s) => s.receipt), next: `homie-studio assets lineup ${game} (true scale, silhouettes, palette drift); look at it` };
}

/** A character's concept words: who, the derived style prompt without its prop framing, then an A-pose, front view. */
function characterConcept(root, game, what, like) {
  const reg = registry();
  const style = studio(root, ['style', 'prompt', game]);
  const golden = (style.golden ?? []).map((g) => join('games', game, g.path)).filter((p) => existsSync(join(root, p))).slice(0, 4);
  const refs = [...golden, ...(like ? [like] : [])].slice(0, 4);
  const look = String(style.prompt.text).replace(/,?\s*3\/4 view, centred, whole object in frame[^]*$/, '');
  const prompt = `${String(what).trim().replace(/\.$/, '')}. One game character, full body from head to feet, standing in an A-pose (arms straight and angled down about 45 degrees away from the body, hands open, legs slightly apart), front view facing the camera, centred. ${look}, lit evenly and neutrally for modelling, plain light grey background, no ground shadow, no text, no logo.`;
  if (refs.length) {
    const c = reg.concept.withRefs;
    return { model: c.endpoint, input: { ...c.input, image_size: { width: 1536, height: 2560 }, prompt: `${prompt} Match the style of the reference images exactly (shapes, proportions, colours, how it is shaded); do not copy their content.`, [c.refs]: refs.map((g) => `@file:${g}`) }, refs, rev: style.prompt.rev };
  }
  const c = reg.concept.noRefs;
  return { model: c.endpoint, input: { ...c.input, image_size: { width: 1536, height: 2560 }, prompt }, refs: [], rev: style.prompt.rev };
}

/** A library item's thumbnail into the job's folder, as a style reference (CC0, the library's own render). */
async function likeRef(root, dir, item) {
  if (!item) return null;
  // The studio's own toolkit and its sharp (both installed in the studio), never this plugin's.
  const { createRequire } = await import('node:module');
  const { pathToFileURL } = await import('node:url');
  const need = createRequire(join(root, 'package.json'));
  const { libraryBase, loadIndex, itemThumb } = await import(pathToFileURL(join(root, 'node_modules', '@homie-rocks', 'studio', 'lib', 'library.mjs')).href);
  const { index, lib } = await loadIndex({ lib: libraryBase() });
  const it = index.items.find((x) => x.id === item);
  if (!it) throw new Error(`no library item "${item}" (homie-studio assets find "<words>" --kind character)`);
  const bytes = await itemThumb(lib, it);
  if (!bytes) throw new Error(`${item} has no thumbnail`);
  const sharp = (await import(pathToFileURL(need.resolve('sharp')).href)).default;
  const file = join(dir, 'like.png');
  await sharp(Buffer.from(bytes)).resize(768, 768, { fit: 'contain', background: '#d9d9d9' }).flatten({ background: '#d9d9d9' }).png().toFile(file);
  return rel(root, file);
}

async function character(root) {
  const [, game, asset] = pos;
  gameDir(root, game);
  if (!SLUG.test(String(asset ?? ''))) throw new Error('name the asset: models.mjs character <game> <asset id> --card "Players/<Name>" --what "<who>"');
  const reg = registry();
  const dir = join(root, 'art', asset);
  mkdirSync(join(dir, 'raw'), { recursive: true });
  const conceptFile = ['concept.png', 'concept.jpg', 'concept.webp'].map((f) => join(dir, f)).find((f) => existsSync(f) && existsSync(`${f}.json`));
  const card = String(flags.get('card') ?? `Players/${asset}`);
  const height = flags.has('height') ? Number(flags.get('height')) : null;
  const m = reg.character.mesh;
  const meshInput = (concept) => ({ ...m.input, image_url: concept, [m.polycount]: Number(flags.get('faces') ?? m.input.target_polycount), ...(height ? { [m.height]: height } : {}) });
  if (!conceptFile || flags.has('concept-again')) {
    const what = flags.get('what');
    if (!what) throw new Error('--what "<who, in plain words: build, clothes, colours, what they carry>" (the style comes from the game\'s locked decisions)');
    const like = flags.has('dry-run') ? (flags.get('like') ? 'like.png' : null) : await likeRef(root, dir, flags.get('like') ?? null);
    const c = characterConcept(root, game, what, like);
    if (flags.has('concept-again') && conceptFile) {
      const was = `concept-was-${Date.now()}`;
      for (const f of [conceptFile, `${conceptFile}.json`, `${conceptFile}.request`]) if (existsSync(f)) renameSync(f, f.replace(/concept(?=\.[a-z]+)/, was));
    }
    const meshPrice = await priceOf(m.endpoint, meshInput('x'), { addons: m.addons }).catch(() => null);
    const r = await paid(root, game, { model: c.model, input: c.input, out: join(dir, 'concept.png'), base: root, what: `the character concept for ${asset}`, asset });
    if (!r.ok || r.dryRun) return { ...r, command: 'character', step: 'concept', game, asset, then: meshPrice ? { what: 'the rigged, textured model (Meshy 7.1)', usd: meshPrice.usd, basis: meshPrice.basis } : null, total: r.price && meshPrice ? +(r.price.usd + meshPrice.usd).toFixed(3) : null };
    const file = fixExt(r.file);
    writeJson(join(dir, 'concept.meta.json'), { what: String(what), card, height, model: c.model, refs: c.refs, promptRev: c.rev, prompt: c.input.prompt, like: flags.get('like') ?? null });
    return { ok: true, command: 'character', step: 'concept', game, asset, concept: rel(root, file), usd: r.usd, spent: readBudget(budgetDir(root, game))?.spent ?? null, next: `look at ${rel(root, file)} first (one character, whole, in an A-pose, in the game's style, on a plain background?). Then: models.mjs character ${game} ${asset} --mesh --yes (about US$${meshPrice?.usd ?? '1.40'}); or change --what and --concept-again (never a loop)` };
  }
  if (!flags.has('mesh')) return { ok: true, command: 'character', step: 'look', game, asset, concept: rel(root, conceptFile), next: `the concept exists: look at it, then models.mjs character ${game} ${asset} --mesh --yes` };
  const meta = readJson(join(dir, 'concept.meta.json'), {});
  const input = meshInput(`@file:${rel(root, conceptFile)}`);
  if (meta.height && !height) input[m.height] = meta.height;
  const meshOut = join(dir, 'raw', 'rigged.glb');
  const r = await paid(root, game, { model: m.endpoint, input, out: meshOut, base: root, credits: null, addons: m.addons, what: `the rigged 3D character for ${asset}`, asset });
  if (!r.ok || r.dryRun) return { ...r, command: 'character', step: 'mesh', game, asset };
  const concept = readJson(`${conceptFile}.json`, {});
  const mesh = readJson(`${r.file}.json`, {});
  const steps = [
    { what: 'concept', provider: 'fal', endpoint: concept.model ?? meta.model, usd: concept.price?.usd ?? null, receipt: rel(root, `${conceptFile}.json`), refs: meta.refs ?? [], promptRev: meta.promptRev ?? null, requestId: concept.requestId ?? null, at: concept.at ?? null },
    { what: 'mesh and rig', provider: 'fal', endpoint: m.endpoint, input: { [m.polycount]: input[m.polycount], pose_mode: input.pose_mode, enable_rigging: true, should_texture: true }, usd: mesh.price?.usd ?? r.usd, receipt: rel(root, `${r.file}.json`), requestId: mesh.requestId ?? r.requestId ?? null, at: mesh.at ?? null },
  ];
  const stepsFile = join(dir, 'steps.json');
  writeJson(stepsFile, steps);
  const added = studio(root, ['assets', 'add', game, '--file', rel(root, r.file), '--route', 'generated', '--license', 'generated', '--as', asset, '--kind', 'character', '--rigged', '--card', meta.card ?? card, '--steps', rel(root, stepsFile), '--concept', rel(root, conceptFile), '--slug', asset, ...(flags.get('clips-from') ? ['--clips-from', String(flags.get('clips-from'))] : []), ...((meta.height ?? height) ? ['--height', String(meta.height ?? height)] : [])]);
  return { ok: true, command: 'character', step: 'mesh', game, asset, model: added.model ?? added.file, anims: added.anims ?? null, skeleton: added.skeleton ?? null, verbs: added.verbs ?? [], before: added.before, after: added.after, usd: r.usd, spent: readBudget(budgetDir(root, game))?.spent ?? null, receipts: steps.map((s) => s.receipt), next: `homie-studio anim preview ${game} --asset ${asset} (its clips, looping) and homie-studio assets lineup ${game}; look at both` };
}

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
  if (!price) {
    const reg = registry();
    const known = [reg.concept.withRefs, reg.concept.noRefs, reg.mesh.prop, reg.mood, reg.character?.mesh, ...(reg.mesh.fallbacks ?? [])].find((e) => e?.endpoint === endpoint);
    if (known && Number.isFinite(Number(known.price?.usd))) price = { usd: Number(known.price.usd), basis: `the registry's recorded price for ${endpoint} (read ${known.price.read ?? reg.checked}); the receipt names none` };
  }
  if (!price) throw new Error(`${file} names no cost and ${endpoint} is not in the registry: say what it cost with --usd <US dollars> (an unknown cost is never recorded as nothing)`);
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

async function quote(root) {
  const game = pos[1];
  gameDir(root, game);
  const reg = registry();
  const n = Math.max(1, Number(flags.get('count') ?? 1));
  const c = await priceOf(reg.concept.noRefs.endpoint, { ...reg.concept.noRefs.input, prompt: 'x' });
  const m = await priceOf(reg.mesh.prop.endpoint, { ...reg.mesh.prop.input, image_url: 'x' }, { credits: reg.mesh.prop.credits });
  const one = +(c.usd + m.usd).toFixed(3);
  const b = readBudget(budgetDir(root, game));
  return { ok: true, command: 'quote', game, concept: c, mesh: m, perProp: one, count: n, total: +(one * n).toFixed(3), budget: b ? { cap: b.cap, spent: b.spent, left: +(b.cap - b.spent).toFixed(3) } : null, note: 'a redo of one step costs that step again; a budget of about US$1.10 a prop allows one redo' };
}

async function mood(root) {
  const [, game, which] = pos;
  gameDir(root, game);
  const reg = registry();
  const doc = readJson(join(root, 'games', game, 'codex', 'decisions.json'), null);
  const dirs = (doc?.board?.directions ?? []).filter((d) => which === 'all' || d.id === which);
  if (!dirs.length) throw new Error(`no style-board direction "${which}" (homie-studio style board ${game} draws the board first)`);
  const out = [];
  for (const d of dirs) {
    const p = d.values['style.palette'] ?? {};
    const prompt = `A painted mood image (key art) for a game: ${d.label}. ${String(doc.prompt ?? '').slice(0, 240)}. Colours ${[p.bg, p.accent, p.accent2, p.gold, p.good].filter(Boolean).join(' ')}, ${d.values['style.light']?.time ?? ''} light, seen from a ${d.values['style.camera']?.angle ?? 'three-quarter'} camera. Concept painting, no text, no logo, no real people or brands.`;
    const file = join(root, 'art', `${game}-board`, `${d.id}-mood.png`);
    const r = await paid(root, game, { model: reg.mood.endpoint, input: { ...reg.mood.input, prompt }, out: file, base: root, what: `a mood image for direction ${d.id.toUpperCase()}`, asset: `board-${d.id}` });
    if (!r.ok || r.dryRun) { out.push({ direction: d.id, ...r }); if (!r.ok) break; continue; }
    const fixed = fixExt(r.file);
    studio(root, ['style', 'mood', game, d.id, '--image', fixed, '--usd', String(r.usd), '--receipt', rel(root, `${fixed}.json`), '--model', reg.mood.endpoint]);
    out.push({ direction: d.id, ok: true, file: rel(root, fixed), usd: r.usd });
  }
  const stop = out.find((x) => x.ok === false);
  return { ok: !stop, command: 'mood', game, images: out, ...(stop ? { needs: stop.needs, why: stop.why } : {}), note: 'a mood image is a target, labelled so, never what the game draws' };
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
  if (cmd === 'check') return check();
  if (cmd === 'registry') return registryCheck();
  const root = studioRoot();
  if (cmd === 'budget') return budget(root);
  if (cmd === 'quote') return quote(root);
  if (cmd === 'prop') return prop(root);
  if (cmd === 'character') return character(root);
  if (cmd === 'import') return importJob(root);
  if (cmd === 'mood') return mood(root);
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
