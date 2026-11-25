// Verify Telegram Mini App initData on a Node server. node:crypto only, no packages.
// Rules: https://core.telegram.org/bots/webapps (checked 2026-11-23); policy: references/mini-apps/security.md.
//   verifyHmac(raw, { botToken })                 - your server owns the bot token
//   verifyEd25519(raw, { botId, publicKeyHex })   - a third party with only the bot id (Bot API 8.0)
// Both return the parsed fields (user / receiver / chat decoded) or throw InitDataError.
// Library alternative: @tma.js/init-data (validate, validate3rd, expiresIn).
import { createHmac, createPublicKey, timingSafeEqual, verify } from 'node:crypto';

export const TELEGRAM_ED25519_PROD = 'e7bf03a2fa4602af4580703d88dda5bb59f32ed8b02a56c187fe7d34caed242d';
export const TELEGRAM_ED25519_TEST = '40055058a4ee38156a06562e52eece92a771bcd8346a8c4615cb7376eddf72ec';
const JSON_FIELDS = ['user', 'receiver', 'chat'];
const CLOCK_SKEW = 60;
const SPKI_ED25519 = Buffer.from('302a300506032b6570032100', 'hex'); // DER prefix of a raw 32-byte key

export class InitDataError extends Error {
  constructor(message: string) { super(message); this.name = 'InitDataError'; }
}

export interface Options {
  maxAge?: number | null;   // seconds; default 86400. null = no age check (not recommended)
  now?: number;             // seconds since epoch, for tests
}

export function parse(raw: string): Map<string, string> {
  if (typeof raw !== 'string' || !raw || raw.length > 16384) throw new InitDataError('empty or oversized initData');
  // Same grammar as the Python twin: no leading '?', every pair has '='.
  if (raw.startsWith('?') || raw.split('&').some((p) => !p.includes('='))) throw new InitDataError('initData is not a query string');
  const out = new Map<string, string>();
  for (const [key, value] of new URLSearchParams(raw)) {
    if (out.has(key)) throw new InitDataError(`duplicate field ${key}`);
    // The check string joins key=value with newlines: a newline inside a value (%0A) could fold the next field
    // into this one without changing the signed text. Telegram never sends one (JSON escapes it).
    if (!/^[a-z_]{1,64}$/.test(key) || /[\r\n]/.test(value)) throw new InitDataError('malformed field name or value');
    out.set(key, value);
  }
  return out;
}

export function checkString(fields: Map<string, string>, exclude: string[]): string {
  return [...fields].filter(([k]) => !exclude.includes(k)).sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0))
    .map(([k, v]) => `${k}=${v}`).join('\n');
}

function decode(fields: Map<string, string>): Record<string, unknown> {
  const out: Record<string, unknown> = Object.fromEntries(fields);
  for (const key of JSON_FIELDS) {
    if (typeof out[key] === 'string') {
      try { out[key] = JSON.parse(out[key] as string); } catch { throw new InitDataError(`${key} is not JSON`); }
    }
  }
  return out;
}

function checkAge(fields: Map<string, string>, opts: Options): void {
  const raw = fields.get('auth_date') ?? '';
  if (!/^[0-9]{1,12}$/.test(raw)) throw new InitDataError('auth_date missing or not a number');
  const now = opts.now ?? Date.now() / 1000;
  if (!Number.isFinite(now) || (opts.maxAge !== undefined && opts.maxAge !== null && !Number.isFinite(opts.maxAge))) {
    throw new InitDataError('now and maxAge must be finite numbers'); // NaN would silently disable expiry
  }
  const age = now - Number(raw);
  if (age < -CLOCK_SKEW) throw new InitDataError('auth_date is in the future');
  const maxAge = opts.maxAge === undefined ? 86400 : opts.maxAge;
  if (maxAge !== null && age > maxAge) throw new InitDataError('initData expired');
}

/** HMAC_SHA256(key = "WebAppData", msg = bot token). Keep this instead of the token where you can. */
export function secretKey(botToken: string): Buffer {
  return createHmac('sha256', 'WebAppData').update(botToken).digest();
}

/** Every field except `hash` (so `signature` stays in), sorted, key=value joined by "\n". */
export function verifyHmac(raw: string, opts: Options & { botToken?: string; key?: Buffer }): Record<string, unknown> {
  const fields = parse(raw);
  const received = fields.get('hash') ?? '';
  if (!/^[0-9a-f]{64}$/.test(received)) throw new InitDataError('hash missing or malformed');
  const key = opts.key ?? (opts.botToken ? secretKey(opts.botToken) : null);
  if (!key) throw new InitDataError('no bot token or secret key configured');
  const expected = createHmac('sha256', key).update(checkString(fields, ['hash'])).digest();
  if (!timingSafeEqual(expected, Buffer.from(received, 'hex'))) throw new InitDataError('hash mismatch');
  checkAge(fields, opts);
  return decode(fields);
}

/** "<bot_id>:WebAppData\n" + every field except `hash` and `signature`; signature is base64url without padding. */
export function verifyEd25519(raw: string, opts: Options & { botId: number; publicKeyHex?: string }): Record<string, unknown> {
  const fields = parse(raw);
  const sig = fields.get('signature');
  if (!sig) throw new InitDataError('signature missing');
  if (!/^[A-Za-z0-9_-]{86}(?:==)?$/.test(sig)) throw new InitDataError('signature or public key malformed');
  const signature = Buffer.from(sig.replace(/=+$/, ''), 'base64url');
  const pub = Buffer.from(opts.publicKeyHex ?? TELEGRAM_ED25519_PROD, 'hex');
  if (signature.length !== 64 || pub.length !== 32) throw new InitDataError('signature or public key malformed');
  const key = createPublicKey({ key: Buffer.concat([SPKI_ED25519, pub]), format: 'der', type: 'spki' });
  const message = `${Math.trunc(opts.botId)}:WebAppData\n${checkString(fields, ['hash', 'signature'])}`;
  if (!verify(null, Buffer.from(message), key, signature)) throw new InitDataError('signature mismatch');
  checkAge(fields, opts);
  return decode(fields);
}

/**
 * Express/Fastify-style helper: read `Authorization: tma <initData>` and verify it. The scheme is
 * case-insensitive, and the value may also be base64, the form telegram-web-app.js sends for
 * `WebApp.Serverless.call` (`'TMA ' + btoa(initData)`). Raw initData always holds `hash=`; base64 never does.
 */
export function fromAuthorization(header: string | undefined, botToken: string, opts: Options = {}): Record<string, unknown> {
  const m = /^tma (.+)$/i.exec(header ?? '');
  if (!m) throw new InitDataError('missing Authorization: tma <initData>');
  const raw = m[1].includes('hash=') ? m[1] : Buffer.from(m[1], 'base64').toString('utf8');
  return verifyHmac(raw, { ...opts, botToken });
}
