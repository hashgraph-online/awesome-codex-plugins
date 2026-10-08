/**
 * ElevenLabs, through the creator's OWN account, by one of two roads:
 *
 *   cli  the official `elevenlabs` CLI (github.com/elevenlabs/cli), signed in with
 *        its own browser sign-in (`elevenlabs auth login`); the sign-in stays in the
 *        OS keychain and nothing here ever sees it;
 *   key  ELEVENLABS_API_KEY in the environment (the person's own key; never
 *        written into the studio, never printed), or, for a studio set up through
 *        Stripe Projects (`homie-studio setup --via stripe-projects --with elevenlabs`;
 *        studio.json providers.elevenlabs), the key Projects synced to the studio's
 *        git-ignored .env: read here, in this process only, never printed or passed on.
 *
 * ELEVENLABS_BASE_URL points either road at another address (a test double).
 */
import { spawnSync } from 'node:child_process';
import { existsSync, readFileSync } from 'node:fs';
import { basename, dirname, isAbsolute, join, normalize, sep } from 'node:path';

const BASE = () => (process.env.ELEVENLABS_BASE_URL || 'https://api.elevenlabs.io').replace(/\/+$/, '');
const CLI = () => process.env.ELEVENLABS_CLI || 'elevenlabs';

/**
 * Measured on a Creator-plan account, 2026-09-28: music_v2 composition-plan renders
 * billed 1,015 credits for 37 s and 5,204 credits for 189.2 s, about 27.5 credits a
 * second. The quote uses this; every render then records what it really cost.
 */
export const MUSIC_CREDITS_PER_SECOND = 27.5;
/** Speech-to-text (the lyric check) is small next to a render; measured per run and recorded. */
export const STT_CREDITS_PER_SECOND_ESTIMATE = 0.5;

function cli(args, { input, timeout = 15 * 60_000 } = {}) {
  const base = process.env.ELEVENLABS_BASE_URL ? ['--base-url', process.env.ELEVENLABS_BASE_URL] : [];
  const r = spawnSync(CLI(), [...args, ...base], { input: typeof input === 'string' ? Buffer.from(input) : input, maxBuffer: 512 * 1024 * 1024, timeout });
  if (r.error) return { code: 127, stdout: Buffer.alloc(0), stderr: r.error.message };
  return { code: r.status ?? 1, stdout: r.stdout ?? Buffer.alloc(0), stderr: (r.stderr ?? Buffer.alloc(0)).toString('utf8') };
}

const parse = (buf) => { try { return JSON.parse(buf.toString('utf8')); } catch { return null; } };

/**
 * The ElevenLabs key Stripe Projects keeps for this studio, or null: studio.json (found from the working folder up)
 * says `providers.elevenlabs.via: "stripe-projects"` and which variable of which output file holds it.
 */
export function projectsKey(from = process.cwd()) {
  let dir = from;
  for (let i = 0; i < 12; i += 1) {
    if (existsSync(join(dir, 'studio.json'))) break;
    const up = dirname(dir);
    if (up === dir) return null;
    dir = up;
  }
  let p = null;
  try { p = JSON.parse(readFileSync(join(dir, 'studio.json'), 'utf8'))?.providers?.elevenlabs ?? null; } catch { return null; }
  if (p?.via !== 'stripe-projects') return null;
  const name = /^[A-Z][A-Z0-9_]{2,}$/.test(String(p.envKey ?? '')) ? p.envKey : 'ELEVENLABS_API_KEY';
  const file = normalize(String(p.envFile || '.env'));
  if (isAbsolute(file) || file === '..' || file.startsWith(`..${sep}`)) return null;
  let text = '';
  try { text = readFileSync(join(dir, file), 'utf8'); } catch { return null; }
  for (const line of text.split(/\r?\n/)) {
    const m = /^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$/.exec(line);
    if (!m || m[1] !== name) continue;
    const v = m[2].trim().replace(/^(["'])(.*)\1$/, '$2');
    return v || null;
  }
  return null;
}
const keyOf = () => process.env.ELEVENLABS_API_KEY || projectsKey();

/** Which road is open, without spending anything and without printing a secret. */
export function road() {
  const probe = cli(['--version']);
  const hasCli = probe.code === 0;
  let signedIn = false;
  if (hasCli) {
    const s = parse(cli(['auth', 'status', '--format', 'json']).stdout);
    signedIn = Boolean(s?.schemes?.some((x) => x.logged_in));
  }
  const hasKey = Boolean(keyOf());
  if (hasCli && signedIn) return { road: 'cli', cli: probe.stdout.toString('utf8').trim() };
  if (hasKey) return { road: 'key', via: process.env.ELEVENLABS_API_KEY ? 'environment' : 'stripe-projects', cli: hasCli ? probe.stdout.toString('utf8').trim() : null, cliSignedIn: false };
  return {
    road: null, cli: hasCli ? probe.stdout.toString('utf8').trim() : null, cliSignedIn: false,
    why: hasCli
      ? 'the elevenlabs CLI is here but not signed in: run `elevenlabs auth login` (it opens ElevenLabs in the browser; the person signs in once)'
      : 'no ElevenLabs connection: install the official CLI (`brew install elevenlabs/tap/elevenlabs`, then `elevenlabs auth login`), or set ELEVENLABS_API_KEY from https://elevenlabs.io/app/developers/api-keys in the environment',
  };
}

async function api(path, { method = 'GET', json, form, query } = {}) {
  const key = keyOf();
  if (!key) throw new Error('ELEVENLABS_API_KEY is not set (and no Stripe Projects key for this studio)');
  const url = new URL(`${BASE()}${path}`);
  for (const [k, v] of Object.entries(query ?? {})) if (v != null) url.searchParams.set(k, String(v));
  const headers = { 'xi-api-key': key };
  let body;
  if (json) { headers['content-type'] = 'application/json'; body = JSON.stringify(json); }
  if (form) body = form;
  const res = await fetch(url, { method, headers, body, signal: AbortSignal.timeout(15 * 60_000) });
  const buf = Buffer.from(await res.arrayBuffer());
  if (!res.ok) throw new Error(`ElevenLabs ${method} ${path} answered ${res.status}: ${buf.toString('utf8').slice(0, 300)}`);
  return { headers: res.headers, body: buf };
}

/** Plan and credit facts. `used`/`limit` are ElevenLabs' character_count/character_limit (its credits). */
export async function subscription(r = road()) {
  let s;
  if (r.road === 'cli') {
    const out = cli(['user', 'subscription', 'get', '--format', 'json']);
    s = parse(out.stdout);
    if (out.code !== 0 || !s) throw new Error(`could not read the ElevenLabs subscription: ${out.stderr.trim().split('\n').pop() || out.stdout.toString('utf8').slice(0, 200)}`);
  } else if (r.road === 'key') s = parse((await api('/v1/user/subscription')).body);
  else throw new Error(r.why);
  const used = Number(s.character_count); const limit = Number(s.character_limit);
  return {
    tier: s.tier ?? null, status: s.status ?? null, used, limit, remaining: limit - used,
    resetAt: s.next_character_count_reset_unix ? new Date(s.next_character_count_reset_unix * 1000).toISOString() : null,
    canGoOver: Boolean(s.can_extend_character_limit || s.allowed_to_extend_character_limit),
  };
}

/**
 * What the plan means for rights, in plain words (ElevenLabs help centre, "Can I
 * publish the content I generate on the platform?", read 2026-09-29): the free plan
 * has no commercial licence and asks for "Eleven Music" attribution; paid plans
 * include a commercial licence (not for Beta services), under the Terms of Service
 * and the Prohibited Use Policy. The tier is recorded with every render because it
 * is the tier AT RENDER TIME that counts: upgrading later does not relicense a
 * render made on the free plan.
 */
export function rightsFor(tier) {
  const t = String(tier ?? '').toLowerCase();
  if (!t) return { plan: null, commercial: null, attribution: null, words: 'The plan could not be read, so the rights are unknown: do not publish commercially until it is.' };
  if (t === 'free') {
    return { plan: t, commercial: false, attribution: 'Made with Eleven Music.', words: 'Free plan: no commercial use (no ads, no sales, no monetised channels), and published copies credit "Eleven Music". A paid plan is needed for commercial use, and a render made now stays under the free-plan terms.' };
  }
  return { plan: t, commercial: true, attribution: null, words: `Paid plan (${t}): ElevenLabs includes a commercial licence for music made on it (not for Beta features), within their Terms of Service and Prohibited Use Policy. It is recorded with the render, because the plan at render time is what counts.` };
}

export const quoteCredits = (seconds, { vocals = false } = {}) => {
  const music = Math.ceil(seconds * MUSIC_CREDITS_PER_SECOND);
  const stt = vocals ? Math.ceil(seconds * STT_CREDITS_PER_SECOND_ESTIMATE) : 0;
  return { music, lyricCheck: stt, total: music + stt, basis: `about ${MUSIC_CREDITS_PER_SECOND} credits per second of music_v2 (measured on a Creator-plan account); the lyric check is an estimate` };
};

/** The free check: the CLI validates the body locally and sends nothing. */
export function dryRun(body, { outputFormat }) {
  const r = road();
  if (r.road !== 'cli') return { ok: true, sent: false, road: r.road, body, note: 'no CLI to validate with: the body is shown as it would be sent' };
  const out = cli(['music', 'compose_detailed', '--dry-run', '--format', 'json', '--output-format', outputFormat, '--json', '-'], { input: JSON.stringify(body) });
  const j = parse(out.stdout);
  if (out.code !== 0 || !j || j.error) return { ok: false, why: j?.error?.message ?? out.stderr.trim() };
  return { ok: true, sent: false, road: 'cli', request: { url: j.url, query: j.query_params, body: j.body } };
}

/** Split a multipart/mixed answer (JSON + audio) into its parts. */
export function splitMultipart(buf, contentType) {
  const m = /boundary="?([^";]+)"?/i.exec(contentType ?? '');
  let boundary = m ? m[1] : null;
  if (!boundary) {
    const first = buf.indexOf('\r\n');
    const line = buf.subarray(0, first).toString('latin1');
    if (line.startsWith('--')) boundary = line.slice(2);
  }
  if (!boundary) throw new Error('the answer is not multipart');
  const sep = Buffer.from(`--${boundary}`);
  const parts = [];
  let at = buf.indexOf(sep);
  while (at >= 0) {
    const next = buf.indexOf(sep, at + sep.length);
    if (next < 0) break;
    let part = buf.subarray(at + sep.length, next);
    if (part.subarray(0, 2).toString() === '\r\n') part = part.subarray(2);
    if (part.subarray(part.length - 2).toString() === '\r\n') part = part.subarray(0, part.length - 2);
    const headEnd = part.indexOf('\r\n\r\n');
    const head = part.subarray(0, headEnd).toString('latin1').toLowerCase();
    parts.push({ head, body: part.subarray(headEnd + 4) });
    at = next;
  }
  const json = parts.find((p) => p.head.includes('application/json'));
  const audio = parts.find((p) => /audio|octet-stream/.test(p.head));
  return { json: json ? JSON.parse(json.body.toString('utf8')) : null, audio: audio?.body ?? null };
}

/** Split `--format http` output (status line, headers, body). */
function splitHttp(buf) {
  const end = buf.indexOf('\r\n\r\n') >= 0 ? buf.indexOf('\r\n\r\n') : buf.indexOf('\n\n');
  const sepLen = buf.indexOf('\r\n\r\n') >= 0 ? 4 : 2;
  const head = buf.subarray(0, end).toString('latin1');
  const [status, ...lines] = head.split(/\r?\n/);
  const headers = {};
  for (const l of lines) { const i = l.indexOf(':'); if (i > 0) headers[l.slice(0, i).trim().toLowerCase()] = l.slice(i + 1).trim(); }
  let body = buf.subarray(end + sepLen);
  if (/chunked/i.test(headers['transfer-encoding'] ?? '') && !/^--/.test(body.subarray(0, 2).toString())) {
    // De-chunk (the CLI normally hands the body over already joined).
    const out = []; let i = 0;
    while (i < body.length) { const nl = body.indexOf('\r\n', i); const n = parseInt(body.subarray(i, nl).toString(), 16); if (!n) break; out.push(body.subarray(nl + 2, nl + 2 + n)); i = nl + 2 + n + 2; }
    body = Buffer.concat(out);
  }
  return { status: Number(status.split(' ')[1]), headers, body };
}

/** One paid render: audio, the plan it used, word timestamps, and the song id (for inpainting). */
export async function composeDetailed(body, { outputFormat }) {
  const r = road();
  if (r.road === 'cli') {
    const out = cli(['music', 'compose_detailed', '--format', 'http', '--output-format', outputFormat, '--json', '-'], { input: JSON.stringify(body) });
    if (out.code !== 0) throw new Error(`the render failed: ${out.stderr.trim().split('\n').slice(-3).join(' ') || out.stdout.toString('utf8').slice(0, 300)}`);
    const h = splitHttp(out.stdout);
    if (h.status >= 400) throw new Error(`ElevenLabs answered ${h.status}: ${h.body.toString('utf8').slice(0, 300)}`);
    const parts = splitMultipart(h.body, h.headers['content-type']);
    return { ...parts, songId: h.headers['song-id'] ?? null };
  }
  if (r.road === 'key') {
    const res = await api('/v1/music/detailed', { method: 'POST', json: body, query: { output_format: outputFormat } });
    return { ...splitMultipart(res.body, res.headers.get('content-type')), songId: res.headers.get('song-id') };
  }
  throw new Error(r.why);
}

/** Scribe (speech-to-text) with word timings. */
export async function transcribe(file, { model = 'scribe_v2', language = null } = {}) {
  const r = road();
  if (r.road === 'cli') {
    const args = ['speech-to-text', 'convert', '--format', 'json', '--model-id', model, '--file', file];
    if (language) args.push('--language-code', language);
    const out = cli(args);
    const j = parse(out.stdout);
    if (out.code !== 0 || !j || j.error) throw new Error(`the transcription failed: ${j?.error?.message ?? out.stderr.trim().split('\n').pop()}`);
    return j;
  }
  if (r.road === 'key') {
    const form = new FormData();
    form.set('model_id', model);
    if (language) form.set('language_code', language);
    form.set('file', new Blob([readFileSync(file)]), basename(file));
    return JSON.parse((await api('/v1/speech-to-text', { method: 'POST', form })).body.toString('utf8'));
  }
  throw new Error(r.why);
}

/** Stem separation: a zip of stems. Priced by measurement (the account's credits before and after). */
export async function separateStems(file, outZip) {
  const r = road();
  if (r.road === 'cli') {
    const out = cli(['music', 'separate_stems', '--file', file, '-o', outZip]);
    if (out.code !== 0) throw new Error(`stem separation failed: ${out.stderr.trim().split('\n').pop()}`);
    return outZip;
  }
  if (r.road === 'key') {
    const form = new FormData();
    form.set('file', new Blob([readFileSync(file)]), basename(file));
    const res = await api('/v1/music/stem-separation', { method: 'POST', form });
    const { writeFileSync } = await import('node:fs');
    writeFileSync(outZip, res.body);
    return outZip;
  }
  throw new Error(r.why);
}
