/**
 * fal, through the creator's OWN account (FAL_KEY in the environment: the
 * person's key from https://fal.ai/dashboard/keys; never written into the
 * studio, never printed). One paid call at a time, each:
 *
 *   priced first from fal's own pricing API (unit price x the units this input asks for),
 *   checked against the job's budget (refused past the cap),
 *   written to the receipts the moment fal accepts it (before anything else is paid for),
 *   resumable: <out>.request is kept, and running the same call again polls instead of paying twice.
 *
 * FAL_QUEUE_URL, FAL_API_URL and FAL_STORAGE_URL point it at a test double.
 */
import { createHash } from 'node:crypto';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { basename, dirname, extname, resolve } from 'node:path';

const QUEUE = () => (process.env.FAL_QUEUE_URL || 'https://queue.fal.run').replace(/\/+$/, '');
const API = () => (process.env.FAL_API_URL || 'https://api.fal.ai').replace(/\/+$/, '');
const STORAGE = () => (process.env.FAL_STORAGE_URL || 'https://rest.alpha.fal.ai').replace(/\/+$/, '');

export function falKey() {
  const k = (process.env.FAL_KEY ?? '').trim();
  return k || null;
}
const auth = () => { const k = falKey(); if (!k) throw new Error('no fal key: the person sets FAL_KEY (their key from https://fal.ai/dashboard/keys) in the environment this runs in'); return { Authorization: `Key ${k}` }; };

async function retry(fn, tries = 6) {
  for (let i = 0; ; i++) {
    try { return await fn(); } catch (error) { if (i >= tries - 1) throw error; await new Promise((r) => setTimeout(r, 1500 * (i + 1))); }
  }
}

/** The free check: fal answers the pricing API only to a valid key. */
export async function checkKey() {
  if (!falKey()) return { ok: false, why: 'FAL_KEY is not set' };
  const res = await fetch(`${API()}/v1/models/pricing?endpoint_id=fal-ai/flux/dev`, { headers: auth() }).catch((e) => ({ ok: false, status: 0, text: async () => e.message }));
  if (res.ok) return { ok: true };
  return { ok: false, why: res.status === 401 || res.status === 403 ? 'fal refused the key (401/403): it is wrong or revoked' : `fal answered ${res.status}` };
}

export async function unitPrice(model) {
  const res = await retry(() => fetch(`${API()}/v1/models/pricing?endpoint_id=${encodeURIComponent(model)}`, { headers: auth() }));
  if (!res.ok) throw new Error(`fal's pricing API answered ${res.status} for ${model}`);
  const j = await res.json();
  const p = (j.prices ?? []).find((x) => x.endpoint_id === model) ?? j.prices?.[0];
  if (!p) throw new Error(`fal has no price for ${model}`);
  return { unitPrice: Number(p.unit_price), unit: String(p.unit), currency: p.currency ?? 'USD' };
}

/**
 * Seedance-style video models bill tokens: width x height x 24 fps x seconds / 1024.
 * These are the frame sizes that reproduce fal's own per-second prices for Seedance
 * 2.5 (480p about US$0.22/s, 720p about US$0.47/s at US$0.0214 per 1,000 tokens),
 * rounded UP so a quote never undershoots.
 */
const TOKENS_PER_SECOND = { '480p': 10_304, '720p': 22_103, '1080p': 54_673 };

/**
 * How many billing units this input asks for, for the unit fal names. Unknown shapes are refused, never guessed.
 * `credits`: for a partner endpoint billed in credits (Tripo: "credits" at US$0.01), its credit table from the models
 * skill's dated registry, e.g. { base: 40, texture: 10 }: the base, plus each add-on whose input is switched on.
 */
export function unitsFor(model, input, unit, { credits = null } = {}) {
  const u = unit.toLowerCase();
  if (/^(generations?|requests?|calls?)$/.test(u)) return { units: 1, basis: `1 ${u.replace(/s$/, '')}` };
  if (/^credits?$/.test(u)) {
    if (!credits || !Number.isFinite(Number(credits.base))) throw new Error(`fal bills ${model} in credits and the models registry has no credit table for it; check the model page and price it by hand`);
    let n = Number(credits.base);
    const on = [];
    for (const [k, add] of Object.entries(credits)) {
      if (k === 'base' || k === 'note') continue;
      // An add-on counts when its input is on, or when the input leaves it to a default of true (Tripo's texture).
      const v = input[k] ?? credits.defaults?.[k];
      if (v === true || (typeof v === 'string' && v && v !== 'false') || (typeof v === 'number' && v > 0)) { n += Number(add) || 0; on.push(k); }
    }
    return { units: n, basis: `${n} credits (${credits.base} base${on.length ? ` + ${on.join(', ')}` : ''})` };
  }
  const n = Number(input.num_images ?? 1);
  if (/^images?$/.test(u)) {
    // Image models that price per image bill a 4K image as two (fal's model pages); never quote it as one.
    const k4 = /^4k$/i.test(String(input.resolution ?? ''));
    return { units: n * (k4 ? 2 : 1), basis: `${n} image(s)${k4 ? ' at 4K (billed double)' : ''}` };
  }
  if (/megapixel/.test(u)) {
    const s = input.image_size;
    let w = 1024; let h = 768;
    if (s && typeof s === 'object') { w = s.width; h = s.height; }
    else if (typeof s === 'string') { const m = /(\d+)x(\d+)/.exec(s); if (m) { w = +m[1]; h = +m[2]; } else if (/16_9/.test(s)) { w = 1024; h = 576; } else if (/square_hd/.test(s)) { w = 1024; h = 1024; } }
    const mp = Math.max(1, Math.ceil((w * h) / 1_000_000));
    return { units: mp * n, basis: `${n} x ${w}x${h} (${mp} MP each, rounded up)` };
  }
  if (/1000 tokens/.test(u)) {
    const res = input.draft ? '480p' : String(input.resolution ?? '720p');
    const secs = Number(input.duration);
    if (!Number.isFinite(secs)) throw new Error('give the clip an explicit duration (not "auto") so it can be priced before it is paid for');
    if (!TOKENS_PER_SECOND[res]) throw new Error(`no token rate on file for resolution ${res}`);
    if (Array.isArray(input.video_urls) && input.video_urls.length) throw new Error('reference videos are billed on their own length; price them by hand from the model page before sending them');
    return { units: +((TOKENS_PER_SECOND[res] * secs) / 1000).toFixed(3), basis: `${secs} s at ${res} (${TOKENS_PER_SECOND[res]} tokens/s)` };
  }
  if (/^(seconds?|video seconds?)$/.test(u)) {
    const secs = Number(input.duration);
    if (!Number.isFinite(secs)) throw new Error('give the clip an explicit duration so it can be priced');
    return { units: secs, basis: `${secs} s` };
  }
  if (/^videos?$/.test(u)) return { units: 1, basis: '1 video' };
  throw new Error(`fal bills ${model} per "${unit}", which this script does not know how to count; check the model page and price it by hand`);
}

/**
 * The price of one call. `addons`: a per-call endpoint whose page adds dollars for options (Meshy: textures, rigging,
 * an animation), from the models registry: { base, <input key>: usd, defaults: { <key>: true } }. The quote is the
 * pricing API's own figure or the page's base, whichever is higher (the two have disagreed), plus every add-on whose
 * input is on (or left to a default that is on). Never lower than either source.
 */
export async function priceOf(model, input, opts = {}) {
  const p = await unitPrice(model);
  const { units, basis } = unitsFor(model, input, p.unit, opts);
  let usd = units * p.unitPrice;
  let said = basis;
  if (opts.addons) {
    const a = opts.addons;
    const base = Math.max(usd, Number(a.base) || 0);
    const on = [];
    let add = 0;
    for (const [k, v] of Object.entries(a)) {
      if (k === 'base' || k === 'defaults' || k === 'note') continue;
      const val = input[k] ?? a.defaults?.[k];
      if (val === true || (typeof val === 'number' && val > 0) || (typeof val === 'string' && val && val !== 'false')) { add += Number(v) || 0; on.push(`${k} +US$${Number(v).toFixed(2)}`); }
    }
    usd = base + add;
    said = `${basis}: US$${base.toFixed(2)}${on.length ? ` + ${on.join(' + ')}` : ''}`;
  }
  return { model, unit: p.unit, unitPrice: p.unitPrice, units, usd: +usd.toFixed(4), basis: said };
}

/**
 * The media in an answer: a video, images, or a 3D model (Tripo's model_mesh / model_urls.glb, Rodin's model_mesh,
 * Hunyuan's model_glb, Meshy's model_glb or model_urls.glb; a rigged character's rigged_character_glb first). Only the
 * main file: previews and variants stay behind (the whole answer is kept in <out>.json).
 */
export function mediaUrls(result) {
  if (result?.video?.url) return [result.video.url];
  if (Array.isArray(result?.images) && result.images.length) return result.images.map((i) => i.url).filter(Boolean);
  const mesh = result?.rigged_character_glb?.url ?? result?.model_mesh?.url ?? result?.model_glb?.url ?? result?.model_urls?.glb?.url ?? result?.mesh?.url ?? result?.model?.url ?? null;
  return mesh ? [mesh] : [];
}

const MIME = { '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp', '.mp3': 'audio/mpeg', '.wav': 'audio/wav', '.mp4': 'video/mp4' };

/** Upload a local file to fal's storage (free) and return its URL; cached by content hash in <jobDir>/work/uploads.json. */
export async function upload(path, cacheFile) {
  const bytes = readFileSync(path);
  const hash = createHash('sha256').update(bytes).digest('hex');
  const cache = existsSync(cacheFile) ? JSON.parse(readFileSync(cacheFile, 'utf8')) : {};
  if (cache[hash]) return cache[hash].url;
  const contentType = MIME[extname(path).toLowerCase()] ?? 'application/octet-stream';
  const url = await retry(async () => {
    const init = await fetch(`${STORAGE()}/storage/upload/initiate?storage_type=fal-cdn-v3`, { method: 'POST', headers: { ...auth(), 'Content-Type': 'application/json' }, body: JSON.stringify({ content_type: contentType, file_name: basename(path) }) });
    if (!init.ok) throw new Error(`upload initiate answered ${init.status}`);
    const { upload_url: put, file_url: fileUrl } = await init.json();
    const r = await fetch(put, { method: 'PUT', headers: { 'Content-Type': contentType }, body: bytes });
    if (!r.ok) throw new Error(`upload answered ${r.status}`);
    return fileUrl;
  }, 4);
  cache[hash] = { url, file: basename(path), at: new Date().toISOString() };
  mkdirSync(dirname(cacheFile), { recursive: true });
  writeFileSync(cacheFile, JSON.stringify(cache, null, 1));
  return url;
}

/** Every "@file:<path>" string in the input becomes an uploaded URL. */
export async function resolveFiles(value, base, cacheFile) {
  if (typeof value === 'string' && value.startsWith('@file:')) return upload(resolve(base, value.slice(6)), cacheFile);
  if (Array.isArray(value)) return Promise.all(value.map((v) => resolveFiles(v, base, cacheFile)));
  if (value && typeof value === 'object') { const o = {}; for (const [k, v] of Object.entries(value)) o[k] = await resolveFiles(v, base, cacheFile); return o; }
  return value;
}

/**
 * Submit (or resume) one call. `onAccepted(queued)` runs the moment fal accepts it,
 * before anything else: it writes the receipt.
 */
export async function run(model, input, { out, base, uploads, price, onAccepted, log = () => {} }) {
  const reqFile = `${out}.request`;
  let queued;
  if (existsSync(reqFile)) {
    queued = JSON.parse(readFileSync(reqFile, 'utf8'));
    log(`resuming ${queued.request_id} (already paid for; not submitted again)`);
    // Accepted but cut off before its receipt was written: write it now.
    if (!queued.receiptAt) { await onAccepted(queued); queued.receiptAt = new Date().toISOString(); writeFileSync(reqFile, `${JSON.stringify(queued, null, 2)}\n`); }
  } else {
    const body = await resolveFiles(input, base, uploads);
    const sub = await fetch(`${QUEUE()}/${model}`, { method: 'POST', headers: { ...auth(), 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    if (!sub.ok) throw new Error(`fal refused the submit (${sub.status}): ${(await sub.text()).slice(0, 400)}`);
    queued = await sub.json();
    mkdirSync(dirname(out), { recursive: true });
    // The request file first (a rerun then resumes instead of paying twice), then the receipt.
    queued = { ...queued, model, input, price, at: new Date().toISOString() };
    writeFileSync(reqFile, `${JSON.stringify(queued, null, 2)}\n`);
    await onAccepted(queued);
    queued.receiptAt = new Date().toISOString();
    writeFileSync(reqFile, `${JSON.stringify(queued, null, 2)}\n`);
    log(`submitted ${queued.request_id} (US$${price.usd})`);
  }
  const started = Date.now();
  for (;;) {
    const s = await retry(() => fetch(queued.status_url, { headers: auth() }));
    if (!s.ok) throw new Error(`status answered ${s.status}`);
    const st = await s.json();
    if (st.status === 'COMPLETED') break;
    if (st.status === 'FAILED' || st.error) throw new Error(`fal says the job failed: ${JSON.stringify(st).slice(0, 400)}`);
    if (Date.now() - started > 40 * 60_000) throw new Error('still not done after 40 minutes; run the same command again to keep waiting (it will not pay again)');
    await new Promise((r) => setTimeout(r, model.includes('video') || model.includes('seedance') ? 8000 : 2500));
  }
  const ans = await retry(() => fetch(queued.response_url, { headers: auth() }));
  const result = await ans.json();
  if (!ans.ok) throw new Error(`result answered ${ans.status}: ${JSON.stringify(result).slice(0, 300)}`);
  const urls = mediaUrls(result);
  if (!urls.length) throw new Error(`no media in the answer: ${JSON.stringify(result).slice(0, 300)}`);
  const files = [];
  for (let i = 0; i < urls.length; i++) {
    const f = i === 0 ? out : out.replace(/(\.[a-z0-9]+)$/i, `-${i + 1}$1`);
    const r = await retry(() => fetch(urls[i]));
    if (!r.ok) throw new Error(`download answered ${r.status}`);
    writeFileSync(f, Buffer.from(await r.arrayBuffer()));
    files.push(f);
  }
  writeFileSync(`${out}.json`, `${JSON.stringify({ model, requestId: queued.request_id, price, input, result, at: new Date().toISOString() }, null, 2)}\n`);
  return { requestId: queued.request_id, files, seed: result.seed ?? null, ms: Date.now() - started };
}
