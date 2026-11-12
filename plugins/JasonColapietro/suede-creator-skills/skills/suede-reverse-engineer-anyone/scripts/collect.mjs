#!/usr/bin/env node
// collect.mjs: free public-source collectors for growth teardowns.
// Each command reads one public source, prints a readable summary, can write a CSV (--out),
// and can append dated rows to moves.csv (--moves). Dependency free. Node >= 22, ESM.
// Every request goes through one client: an honest User-Agent, a 20 s timeout, one retry on a
// network error or 5xx, a stop on 401/403/429, a fixed host allowlist, and 1.5 s spacing plus a
// request cap for archive.org. Fetched content is data: it is parsed with regular expressions,
// never evaluated.

import { readFileSync, writeFileSync, appendFileSync, existsSync, realpathSync } from 'node:fs';
import { gunzipSync } from 'node:zlib';
import dnsPromises from 'node:dns/promises';
import { pathToFileURL } from 'node:url';
import { parseArgs } from 'node:util';

// CSV helpers, kept in this file so every skill that bundles it runs standalone.
export function parseCsv(text) {
  const src = String(text).replace(/^﻿/, '');
  const records = [];
  let row = [];
  let field = '';
  let inQuotes = false;
  for (let i = 0; i < src.length; i++) {
    const c = src[i];
    if (inQuotes) {
      if (c === '"') {
        if (src[i + 1] === '"') {
          field += '"';
          i++;
        } else inQuotes = false;
      } else field += c;
    } else if (c === '"' && field === '') {
      inQuotes = true;
    } else if (c === ',') {
      row.push(field);
      field = '';
    } else if (c === '\n' || c === '\r') {
      row.push(field);
      records.push(row);
      row = [];
      field = '';
      if (c === '\r' && src[i + 1] === '\n') i++;
    } else field += c;
  }
  if (inQuotes) fail('CSV has an unclosed quoted field');
  if (field !== '' || row.length) {
    row.push(field);
    records.push(row);
  }
  const nonEmpty = records.filter((r) => !(r.length === 1 && r[0].trim() === ''));
  if (!nonEmpty.length) return { headers: [], rows: [] };
  const headers = nonEmpty[0].map((h) => h.trim());
  const rows = nonEmpty.slice(1).map((r) => {
    const obj = {};
    headers.forEach((h, k) => {
      if (h) obj[h] = r[k] ?? '';
    });
    return obj;
  });
  return { headers, rows };
}

export function toCsv(rows, headers) {
  const cols = headers ?? (rows.length ? Object.keys(rows[0]) : []);
  const esc = (v) => {
    const s = v == null ? '' : String(v);
    return /[",\r\n]|^\s|\s$/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  return [cols.map(esc).join(','), ...rows.map((r) => cols.map((c) => esc(r[c])).join(','))].join('\n') + '\n';
}

export const USER_AGENT = 'suede-collect/1.0 (+https://skills.suedeai.ai)';
export const MOVE_HEADERS = ['date', 'channel', 'kind', 'move', 'reach', 'link', 'evidence'];
export const FIXED_HOSTS = new Set([
  'web.archive.org', 'crt.sh', 'boards-api.greenhouse.io', 'api.lever.co', 'api.ashbyhq.com',
  'itunes.apple.com', 'api.npmjs.org', 'pypistats.org', 'api.github.com', 'www.youtube.com',
]);
export const WAYBACK_DELAY_MS = 1500;
export const TIMEOUT_MS = 20000;
const ROBOTS_AGENT = 'suede-collect';

export class InputError extends Error {}
export class BlockedError extends Error {
  constructor(host, status) {
    super(`blocked by ${host} (${status}): use an archived copy or a manual export`);
    Object.assign(this, { host, status });
  }
}
export class HttpError extends Error {
  constructor(host, status, url) {
    super(`${host} returned ${status} for ${url}`);
    Object.assign(this, { host, status });
  }
}
export class CapError extends Error {}

const fail = (msg) => {
  throw new InputError(msg);
};
const tryUrl = (s, base) => {
  try {
    return new URL(s, base);
  } catch {
    return null;
  }
};
const defaultSleep = (ms) => new Promise((r) => setTimeout(r, ms));
const isStop = (e) => e instanceof BlockedError || e instanceof CapError;

// ---------- dates ----------

const pad = (n) => String(n).padStart(2, '0');
export const ymd = (d) => d.toISOString().slice(0, 10);
export function addMonths(ym, k) {
  const i = Number(ym.slice(0, 4)) * 12 + Number(ym.slice(5, 7)) - 1 + k;
  return `${Math.floor(i / 12)}-${pad((i % 12) + 1)}`;
}
const daysInMonth = (ym) => new Date(Date.UTC(+ym.slice(0, 4), +ym.slice(5, 7), 0)).getUTCDate();
/** Any date string to YYYY-MM-DD, or '' when unreadable. ISO strings keep their written calendar date. */
export function toDate(s) {
  const t = String(s ?? '').trim();
  if (/^\d{4}-\d{2}-\d{2}/.test(t)) return t.slice(0, 10);
  const n = Date.parse(t);
  return Number.isNaN(n) ? '' : new Date(n).toISOString().slice(0, 10);
}
const tsDate = (ts) => `${ts.slice(0, 4)}-${ts.slice(4, 6)}-${ts.slice(6, 8)}`;

// ---------- text, HTML and XML helpers ----------

const escapeRe = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
const ENTITIES = { amp: '&', lt: '<', gt: '>', quot: '"', apos: "'", nbsp: ' ' };
const codePoint = (n) => (Number.isFinite(n) && n > 0 && n < 0x110000 ? String.fromCodePoint(n) : '');
export function decodeEntities(s) {
  return String(s).replace(/&(#x[0-9a-f]+|#\d+|[a-z]+);/gi, (m, e) =>
    e[0] === '#' ? codePoint(e[1].toLowerCase() === 'x' ? parseInt(e.slice(2), 16) : parseInt(e.slice(1), 10)) : ENTITIES[e.toLowerCase()] ?? m);
}
/** Remove scripts, styles, templates and comments so their text is never read as page copy. */
export function stripScripts(html) {
  return String(html).replace(/<(script|style|noscript|template)\b[\s\S]*?<\/\1\s*>/gi, ' ').replace(/<!--[\s\S]*?-->/g, ' ');
}
export function cleanText(s) {
  const raw = String(s ?? '').replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g, '$1');
  return decodeEntities(raw.replace(/<[^>]+>/g, ' ')).replace(/\s+/g, ' ').trim();
}
const tagRe = (tag, flags) => new RegExp(`<${escapeRe(tag)}\\b[^>]*>([\\s\\S]*?)</${escapeRe(tag)}\\s*>`, flags);
export const xmlBlocks = (xml, tag) => [...String(xml).matchAll(tagRe(tag, 'gi'))].map((m) => m[0]);
export const xmlText = (block, tag) => cleanText(String(block).match(tagRe(tag, 'i'))?.[1] ?? '');
function attrOf(tag, name) {
  const m = tag.match(new RegExp(`\\s${escapeRe(name)}\\s*=\\s*(?:"([^"]*)"|'([^']*)'|([^\\s>]+))`, 'i'));
  return m ? decodeEntities(m[1] ?? m[2] ?? m[3]) : '';
}
export function xmlAttr(block, tag, name) {
  const m = String(block).match(new RegExp(`<${escapeRe(tag)}\\b[^>]*>`, 'i'));
  return m ? attrOf(m[0], name) : '';
}
const clip = (s, n = 140) => (s.length > n ? `${s.slice(0, n - 3)}...` : s);
/** Drop emails and @handles from free text so no individual's contact details leave the script. */
export const scrubPersonal = (s) => String(s).replace(/[\w.+-]+@[\w-]+\.[\w.-]+/g, '[email]').replace(/(^|\s)@[\w.]{2,}/g, '$1[handle]');

// ---------- CSV output and moves ----------

export function table(headers, rows) {
  const cells = rows.map((r) => r.map((c) => (c == null ? '' : String(c))));
  const w = headers.map((h, k) => Math.max(h.length, ...cells.map((r) => r[k].length)));
  const line = (r) => r.map((c, k) => c.padEnd(w[k])).join('  ').trimEnd();
  return [line(headers), line(w.map((n) => '-'.repeat(n))), ...cells.map(line)].join('\n');
}

function onFile(path, verb, fn) {
  try {
    return fn();
  } catch (e) {
    if (e instanceof InputError) throw e;
    fail(`cannot ${verb} ${path}: ${e.code ?? e.message}`);
  }
}
const writeOut = (path, rows, headers) => onFile(path, 'write', () => writeFileSync(path, toCsv(rows, headers)));

export const moveKey = (r) => [toDate(r.date) || r.date, r.channel, r.kind, r.move].map((v) => String(v ?? '').trim().toLowerCase()).join('|');

/** Append move rows to a moves.csv (created with a header when absent), skipping date+channel+kind+move duplicates. */
export function appendMoves(path, rows) {
  let text = '';
  let headers = MOVE_HEADERS;
  let existing = [];
  if (existsSync(path)) {
    text = onFile(path, 'read', () => readFileSync(path, 'utf8'));
    const csv = parseCsv(text);
    if (csv.headers.length) {
      const missing = ['date', 'channel', 'kind', 'move'].filter((c) => !csv.headers.includes(c));
      if (missing.length) fail(`${path} is missing column(s): ${missing.join(', ')}`);
      headers = csv.headers;
      existing = csv.rows;
    }
  }
  const seen = new Set(existing.map(moveKey));
  const fresh = [];
  for (const r of rows) {
    const k = moveKey(r);
    if (!seen.has(k)) {
      seen.add(k);
      fresh.push(r);
    }
  }
  const csv = toCsv(fresh, headers);
  if (!text.trim()) onFile(path, 'write', () => writeFileSync(path, csv));
  else if (fresh.length) onFile(path, 'write', () => appendFileSync(path, (text.endsWith('\n') ? '' : '\n') + csv.slice(csv.indexOf('\n') + 1)));
  return { added: fresh.length, skipped: rows.length - fresh.length };
}

const moveRow = (date, channel, kind, move, link, evidence) => ({ date, channel, kind, move: clip(move, 200), reach: '', link, evidence });

// ---------- network client ----------

/**
 * One client per command. All requests go through fetchImpl with an honest User-Agent and a timeout.
 * Hosts must be in FIXED_HOSTS or in `allow` ({host, subdomains}). Redirects are followed by hand so
 * every hop is checked against the allowlist. 401/403/429 stop the source; network errors and 5xx get
 * one retry. archive.org requests are spaced by waybackDelayMs and capped at maxRequests.
 */
export function createClient({ fetchImpl = globalThis.fetch, sleep = defaultSleep, waybackDelayMs = WAYBACK_DELAY_MS, maxRequests = 40, timeoutMs = TIMEOUT_MS, allow = [] } = {}) {
  const state = { archive: 0, calls: 0 };
  const allowed = (host) => FIXED_HOSTS.has(host) || allow.some((a) => host === a.host || (a.subdomains && host.endsWith(`.${a.host}`)));

  async function attempt(u, accept) {
    if (u.hostname.endsWith('archive.org')) {
      if (state.archive >= maxRequests) throw new CapError(`archive.org request cap reached (${maxRequests}); results are partial. Rerun with a higher --max-requests to read more.`);
      if (state.archive > 0) await sleep(waybackDelayMs);
      state.archive++;
    }
    state.calls++;
    return fetchImpl(u.href, { headers: { 'user-agent': USER_AGENT, accept }, redirect: 'manual', signal: AbortSignal.timeout(timeoutMs) });
  }

  async function send(u, accept) {
    let res = null;
    try {
      res = await attempt(u, accept);
      if (res.status < 500) return res;
    } catch (e) {
      if (e instanceof CapError) throw e;
    }
    try {
      return await attempt(u, accept);
    } catch (e) {
      if (e instanceof CapError) throw e;
      const why = e?.name === 'TimeoutError' ? `timed out after ${timeoutMs / 1000}s` : e?.message ?? String(e);
      throw new Error(`${u.hostname} did not respond (${why})`);
    }
  }

  async function request(url, accept = '*/*') {
    let current = url;
    for (let hop = 0; hop < 6; hop++) {
      const u = tryUrl(current);
      if (!u) throw new InputError(`not a valid URL: ${current}`);
      if (!/^https?:$/.test(u.protocol)) throw new InputError(`only http(s) URLs are fetched: ${current}`);
      if (!allowed(u.hostname)) throw new InputError(`${u.hostname} is not an allowed source for this command; nothing was fetched from it`);
      const res = await send(u, accept);
      if ([301, 302, 303, 307, 308].includes(res.status)) {
        const loc = res.headers.get('location');
        if (!loc) throw new HttpError(u.hostname, res.status, current);
        current = new URL(loc, u).href;
        continue;
      }
      if ([401, 403, 429].includes(res.status)) throw new BlockedError(u.hostname, res.status);
      if (!res.ok) throw new HttpError(u.hostname, res.status, current);
      return { url: current, buf: Buffer.from(await res.arrayBuffer()) };
    }
    throw new Error(`too many redirects from ${url}`);
  }

  async function text(url, accept) {
    const { buf } = await request(url, accept);
    const body = buf[0] === 0x1f && buf[1] === 0x8b ? gunzipSync(buf, { maxOutputLength: 64 * 1024 * 1024 }) : buf;
    return body.toString('utf8');
  }

  async function json(url, accept = 'application/json') {
    const t = await text(url, accept);
    try {
      return JSON.parse(t);
    } catch {
      const host = new URL(url).hostname;
      throw new Error(`${host} returned ${/^\s*</.test(t) ? 'an HTML page' : 'something'} instead of JSON`);
    }
  }

  return { request, text, json, state };
}

// ---------- input parsing ----------

const HOST_RE = /^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z][a-z0-9-]{0,62}$/;
export function parseHost(input, cmd) {
  const raw = String(input ?? '').trim().toLowerCase();
  if (!raw) fail(`${cmd} needs a domain, for example: ${cmd} example.com`);
  const host = tryUrl(/^[a-z]+:\/\//.test(raw) ? raw : `https://${raw}`)?.hostname ?? '';
  if (!HOST_RE.test(host)) fail(`"${input}" is not a domain`);
  return host;
}
const bare = (h) => h.replace(/^www\./, '');

function posInt(v, flag, { def, max = Infinity } = {}) {
  if (v === undefined) return def;
  const n = Number(v);
  if (!Number.isInteger(n) || n < 1 || n > max) fail(`--${flag} must be a whole number from 1 to ${max}`);
  return n;
}

// ---------- site: sitemaps and page families ----------

/** Parse robots.txt into the rules for this tool (its own group, else `*`) and the Sitemap lines. */
export function parseRobots(text, agent = ROBOTS_AGENT) {
  const groups = [];
  const sitemaps = [];
  let cur = null;
  let lastAgent = false;
  for (const raw of String(text).split(/\r?\n/)) {
    const line = raw.replace(/#.*/, '').trim();
    const i = line.indexOf(':');
    if (i < 0) continue;
    const key = line.slice(0, i).trim().toLowerCase();
    const val = line.slice(i + 1).trim();
    if (key === 'sitemap') {
      if (val) sitemaps.push(val);
      continue;
    }
    if (key === 'user-agent') {
      if (!lastAgent || !cur) groups.push((cur = { agents: [], rules: [] }));
      cur.agents.push(val.toLowerCase());
      lastAgent = true;
      continue;
    }
    lastAgent = false;
    if (cur && (key === 'allow' || key === 'disallow') && val) cur.rules.push({ allow: key === 'allow', path: val });
  }
  const own = groups.filter((g) => g.agents.some((a) => a.length >= 3 && a !== '*' && agent.toLowerCase().startsWith(a)));
  const chosen = own.length ? own : groups.filter((g) => g.agents.includes('*'));
  return { rules: chosen.flatMap((g) => g.rules), sitemaps };
}

/** Longest matching rule wins; Allow wins a tie. Supports * and a trailing $. */
export function robotsAllows(rules, path) {
  let best = null;
  for (const r of rules) {
    const re = new RegExp(`^${r.path.split('*').map(escapeRe).join('.*').replace(/\\\$$/, '$')}`);
    if (re.test(path) && (!best || r.path.length > best.path.length || (r.path.length === best.path.length && r.allow))) best = r;
  }
  return !best || best.allow;
}

export function parseSitemap(xml) {
  const src = String(xml);
  if (!src.includes('<')) {
    const entries = src.split(/\s+/).filter((l) => /^https?:\/\//.test(l)).map((loc) => ({ loc, lastmod: '' }));
    return { isIndex: false, entries };
  }
  const isIndex = /<sitemapindex\b/i.test(src);
  const entries = xmlBlocks(src, isIndex ? 'sitemap' : 'url')
    .map((b) => ({ loc: xmlText(b, 'loc'), lastmod: toDate(xmlText(b, 'lastmod')) }))
    .filter((e) => e.loc);
  return { isIndex, entries };
}

const LOCALES = new Set('en de fr es it pt nl ja ko zh sv da no nb fi pl tr ru ar he id th vi cs hu ro uk el'.split(' '));
const isLocale = (s) => /^[a-z]{2}(?:[-_][a-z]{2,4})?$/.test(s) && LOCALES.has(s.slice(0, 2));
const HUBS = new Set(['blog', 'resources', 'learn', 'guides', 'docs', 'help', 'articles', 'news', 'library', 'academy', 'hub', 'insights', 'stories', 'customers', 'integrations', 'templates', 'solutions', 'use-cases', 'industries', 'compare', 'alternatives', 'tools']);

/** Page family from the first path segment (locale prefixes skipped), and the second for hubs like /blog/<section>/<post>. */
export function pageFamily(url) {
  const segs = tryUrl(url)?.pathname.split('/').filter(Boolean).map((s) => s.toLowerCase());
  if (!segs) return '(invalid)';
  if (segs.length > 1 && isLocale(segs[0])) segs.shift();
  if (!segs.length) return '/';
  if (HUBS.has(segs[0]) && segs.length >= 3 && !/^\d{4}$/.test(segs[1])) return `/${segs[0]}/${segs[1]}`;
  return `/${segs[0]}`;
}

async function cmdSite(o, ctx) {
  const domain = parseHost(o.args[0], 'site');
  const root = bare(domain);
  const client = ctx.client({ allow: [{ host: root, subdomains: true }] });
  const notes = [];
  const robots = new Map();
  let stopped = false;
  async function rulesFor(u) {
    if (!robots.has(u.host)) {
      let parsed = { rules: [], sitemaps: [] };
      try {
        parsed = parseRobots(await client.text(`${u.protocol}//${u.host}/robots.txt`, 'text/plain'));
      } catch (e) {
        if (isStop(e)) throw e;
        if (!(e instanceof HttpError && e.status >= 400 && e.status < 500)) {
          throw new Error(`robots.txt on ${u.host} could not be read (${e.message}); sitemaps were not fetched`);
        }
      }
      robots.set(u.host, parsed);
    }
    return robots.get(u.host);
  }
  const roots = [];
  try {
    roots.push(...(await rulesFor(new URL(`https://${domain}/`))).sitemaps);
  } catch (e) {
    if (!isStop(e)) throw e;
    notes.push(e.message);
    stopped = true;
  }
  if (!roots.length) roots.push(`https://${domain}/sitemap.xml`);
  const queue = [...roots];
  const visited = new Set();
  const urls = new Map();
  let sitemaps = 0;
  while (!stopped && queue.length && sitemaps < 50 && urls.size < 50000) {
    const sm = queue.shift();
    if (visited.has(sm)) continue;
    visited.add(sm);
    const u = tryUrl(sm);
    if (!u) {
      notes.push(`skipped a malformed sitemap URL: ${clip(sm, 80)}`);
      continue;
    }
    if (u.hostname !== root && !u.hostname.endsWith(`.${root}`)) {
      notes.push(`skipped off-domain sitemap ${u.hostname}${u.pathname} (only ${root} is fetched)`);
      continue;
    }
    try {
      if (!robotsAllows((await rulesFor(u)).rules, u.pathname + u.search)) {
        notes.push(`blocked by ${u.hostname} (robots.txt): use an archived copy or a manual export [${u.pathname}]`);
        continue;
      }
      sitemaps++;
      const { isIndex, entries } = parseSitemap(await client.text(sm, 'application/xml,text/xml,text/plain'));
      if (isIndex) queue.push(...entries.map((e) => e.loc));
      else for (const e of entries) if (urls.size < 50000 && !urls.has(e.loc)) urls.set(e.loc, e.lastmod);
    } catch (e) {
      notes.push(e.message);
      if (isStop(e)) stopped = true;
    }
  }
  if (queue.length && sitemaps >= 50) notes.push('stopped at 50 sitemaps; the count is a floor');
  if (urls.size >= 50000) notes.push('stopped at 50,000 URLs; the count is a floor');
  const rows = [...urls].map(([url, lastmod]) => ({ url, family: pageFamily(url), lastmod }));
  const counts = {};
  for (const r of rows) counts[r.family] = (counts[r.family] ?? 0) + 1;
  const families = Object.entries(counts).sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
  const text = [
    `${domain}: ${rows.length} URLs from ${sitemaps} sitemap(s), pulled ${ctx.today}`,
    rows.length ? table(['family', 'pages'], families) : 'No sitemap URLs found. Try the Wayback CDX listing for page families.',
  ].join('\n');
  return { text, notes, out: { rows, headers: ['url', 'family', 'lastmod'] }, json: { domain, pulled: ctx.today, sitemaps, urls: rows.length, families: Object.fromEntries(families) } };
}

// ---------- Wayback: stack, history, hero ----------

const archiveRaw = (s) => `https://web.archive.org/web/${s.timestamp}id_/${s.original}`;
const archiveView = (s) => `https://web.archive.org/web/${s.timestamp}/${s.original}`;

export function cdxUrl(target, months, now) {
  const from = addMonths(ymd(now).slice(0, 7), -(months - 1)).replace('-', '');
  const p = new URLSearchParams({ url: target, output: 'json', from, filter: 'statuscode:200', collapse: 'timestamp:6', fl: 'timestamp,original,digest' });
  return `https://web.archive.org/cdx/search/cdx?${p}`;
}

/** CDX JSON (header row first) to one snapshot per month. */
export function parseCdx(json) {
  if (!Array.isArray(json) || json.length < 2) return [];
  const [head, ...rows] = json;
  const col = (n) => head.indexOf(n);
  const seen = new Set();
  const out = [];
  for (const r of rows) {
    const timestamp = String(r[col('timestamp')] ?? '');
    if (!/^\d{8}/.test(timestamp)) continue;
    const month = `${timestamp.slice(0, 4)}-${timestamp.slice(4, 6)}`;
    if (seen.has(month)) continue;
    seen.add(month);
    out.push({ timestamp, original: r[col('original')], digest: col('digest') >= 0 ? r[col('digest')] : '', month, date: tsDate(timestamp) });
  }
  return out.sort((a, b) => a.timestamp.localeCompare(b.timestamp));
}

async function snapshots(client, target, months, now) {
  const t = await client.text(cdxUrl(target, months, now), 'application/json');
  if (!t.trim()) return [];
  try {
    return parseCdx(JSON.parse(t));
  } catch {
    throw new Error('web.archive.org CDX returned something other than JSON; try again later');
  }
}

/** Read each snapshot's raw HTML in order; stop the source on a block or the request cap. */
async function eachSnapshot(client, snaps, notes, fn) {
  let read = 0;
  for (const s of snaps) {
    let html;
    try {
      html = await client.text(archiveRaw(s), 'text/html');
    } catch (e) {
      notes.push(isStop(e) ? e.message : `${s.month}: capture unreadable (${e.message})`);
      if (isStop(e)) break;
      continue;
    }
    read++;
    fn(s, html);
  }
  return read;
}

const sig = (tool, group, ...patterns) => ({ tool, group, patterns });
export const SIGNATURES = [
  sig('Meta Pixel', 'ads', /connect\.facebook\.net\/[^"'\s]*fbevents\.js/, /fbq\(\s*['"]init/), sig('Google Ads', 'ads', /googleadservices\.com\/pagead\/conversion/, /gtag\/js\?id=AW-/, /['"]AW-\d{6,}['"]/), sig('Microsoft Advertising', 'ads', /bat\.bing\.com\/bat\.js/),
  sig('LinkedIn Insight Tag', 'ads', /snap\.licdn\.com\/li\.lms-analytics/, /px\.ads\.linkedin\.com/, /_linkedin_partner_id/), sig('X Pixel', 'ads', /static\.ads-twitter\.com\/uwt\.js/, /twq\(\s*['"](?:init|config)/), sig('TikTok Pixel', 'ads', /analytics\.tiktok\.com\/i18n\/pixel/, /ttq\.load\(/),
  sig('Reddit Pixel', 'ads', /redditstatic\.com\/ads\/pixel\.js/, /rdt\(\s*['"]init/), sig('Pinterest Tag', 'ads', /s\.pinimg\.com\/ct\/core\.js/, /ct\.pinterest\.com\/v3/), sig('Snap Pixel', 'ads', /sc-static\.net\/scevent\.min\.js/),
  sig('Quora Pixel', 'ads', /a\.quora\.com\/qevents\.js/), sig('Criteo', 'ads', /static\.criteo\.net\/js/), sig('AdRoll', 'ads', /s\.adroll\.com\/j\//),
  sig('Taboola Pixel', 'ads', /cdn\.taboola\.com\/libtrc/), sig('Outbrain Pixel', 'ads', /amplify\.outbrain\.com\/cp\/obtp\.js/), sig('Google Analytics 4', 'analytics', /googletagmanager\.com\/gtag\/js\?id=G-/),
  sig('Universal Analytics', 'analytics', /google-analytics\.com\/(?:analytics|ga)\.js/, /gtag\/js\?id=UA-/), sig('Google Tag Manager', 'analytics', /googletagmanager\.com\/gtm\.js/, /['"]GTM-[A-Z0-9]{4,}['"]/), sig('Segment', 'analytics', /cdn\.segment\.com\/analytics\.js/),
  sig('Mixpanel', 'analytics', /cdn\.mxpnl\.com/, /mixpanel\.init\(/), sig('Amplitude', 'analytics', /cdn\.amplitude\.com/, /amplitude\.getInstance\(\)\.init|amplitude\.init\(/), sig('Heap', 'analytics', /cdn\.heapanalytics\.com/),
  sig('PostHog', 'analytics', /[a-z]+\.i\.posthog\.com|app\.posthog\.com/, /posthog\.init\(/), sig('Hotjar', 'analytics', /static\.hotjar\.com/), sig('Microsoft Clarity', 'analytics', /clarity\.ms\/tag/),
  sig('FullStory', 'analytics', /edge\.fullstory\.com|fullstory\.com\/s\/fs\.js/), sig('Plausible', 'analytics', /plausible\.io\/js/), sig('Optimizely', 'testing', /cdn\.optimizely\.com/),
  sig('VWO', 'testing', /visualwebsiteoptimizer\.com/), sig('Google Optimize', 'testing', /googleoptimize\.com\/optimize\.js/), sig('AB Tasty', 'testing', /try\.abtasty\.com/),
  sig('LaunchDarkly', 'testing', /launchdarkly\.com/), sig('Statsig', 'testing', /statsigapi\.net|cdn\.jsdelivr\.net\/npm\/statsig/), sig('Rewardful', 'referral', /r\.wdfl\.co/),
  sig('PartnerStack', 'referral', /partnerstack\.com\/[^"'\s]*\.js|pstack/), sig('FirstPromoter', 'referral', /cdn\.firstpromoter\.com/), sig('Impact', 'referral', /impactcdn\.com|impactradius-event\.com/),
  sig('ReferralCandy', 'referral', /referralcandy\.com/), sig('Friendbuy', 'referral', /friendbuy\.(?:com|io)/), sig('HubSpot', 'lifecycle', /js\.hs-scripts\.com|js\.hsforms\.net|js\.hs-analytics\.net/),
  sig('Intercom', 'lifecycle', /widget\.intercom\.io|js\.intercomcdn\.com/), sig('Drift', 'lifecycle', /js\.driftt\.com/), sig('Marketo', 'lifecycle', /munchkin\.marketo\.net/),
  sig('Pardot', 'lifecycle', /pi\.pardot\.com/), sig('Customer.io', 'lifecycle', /assets\.customer\.io/), sig('Braze', 'lifecycle', /js\.appboycdn\.com|sdk\.[a-z0-9-]+\.braze\.com/),
  sig('Mailchimp', 'lifecycle', /chimpstatic\.com|list-manage\.com/), sig('Klaviyo', 'lifecycle', /static\.klaviyo\.com|klaviyo\.com\/onsite/), sig('Attentive', 'lifecycle', /cdn\.attn\.tv/),
  sig('OneSignal', 'lifecycle', /cdn\.onesignal\.com/), sig('Shopify', 'ecommerce', /cdn\.shopify\.com/), sig('BigCommerce', 'ecommerce', /cdn\d*\.bigcommerce\.com/),
  sig('WooCommerce', 'ecommerce', /wp-content\/plugins\/woocommerce/), sig('Yotpo', 'ecommerce', /staticw2\.yotpo\.com|cdn-widgetsrepository\.yotpo\.com/), sig('Recharge', 'ecommerce', /rechargecdn\.com|rechargeapps\.com/),
  sig('Stripe', 'payments', /js\.stripe\.com/), sig('PayPal', 'payments', /paypal\.com\/sdk\/js|paypalobjects\.com\/api/), sig('Klarna', 'payments', /klarnaservices\.com|js\.klarna\.com/),
  sig('Afterpay', 'payments', /js\.afterpay\.com|static\.afterpay\.com/), sig('Affirm', 'payments', /cdn1\.affirm\.com/), sig('Paddle', 'payments', /cdn\.paddle\.com/),
  sig('CallRail', 'call-tracking', /cdn\.callrail\.com/), sig('CallTrackingMetrics', 'call-tracking', /tctm\.co/), sig('Invoca', 'call-tracking', /invocacdn\.com/),
  sig('WhatConverts', 'call-tracking', /whatconverts\.com/),
];
const GROUP_CHANNEL = { ads: 'paid', analytics: 'infrastructure', testing: 'infrastructure', referral: 'referral', lifecycle: 'lifecycle', ecommerce: 'store', payments: 'pricing', 'call-tracking': 'sales' };

/** Script tags (minus JSON data blocks) and resource URLs on non-anchor tags: where installed tools show. */
export function scriptSurface(html) {
  const s = String(html);
  const scripts = [...s.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script\s*>/gi)]
    .filter((m) => !/type\s*=\s*["']?(?:application\/(?:ld\+)?json|text\/(?:template|html))/i.test(m[1]))
    .map((m) => `${m[1]}\n${m[2]}`);
  const urls = [...s.matchAll(/<(?!a\b)[a-z][\w:-]*\b[^>]*?\s(?:src|href|data-src)\s*=\s*["']([^"']+)["']/gi)].map((m) => m[1]);
  return [...scripts, ...urls].join('\n');
}
export function detectTools(html) {
  const surface = scriptSurface(html);
  return SIGNATURES.filter((s) => s.patterns.some((p) => p.test(surface))).map((s) => s.tool);
}

async function cmdStack(o, ctx) {
  const domain = parseHost(o.args[0], 'stack');
  const months = posInt(o.months, 'months', { def: 24, max: 120 });
  const client = ctx.client();
  const snaps = await snapshots(client, `${domain}/`, months, ctx.now);
  const notes = [];
  const seen = new Map();
  let firstMonth = null;
  const read = await eachSnapshot(client, snaps, notes, (s, html) => {
    firstMonth ??= s.month;
    for (const tool of detectTools(html)) {
      if (!seen.has(tool)) seen.set(tool, { first: s, last: s });
      else seen.get(tool).last = s;
    }
  });
  const group = (t) => SIGNATURES.find((s) => s.tool === t).group;
  const tools = [...seen].map(([tool, v]) => ({ tool, group: group(tool), first_seen: v.first.month, last_seen: v.last.month, present_at_start: v.first.month === firstMonth ? 'yes' : '', capture: archiveView(v.first) }))
    .sort((a, b) => a.first_seen.localeCompare(b.first_seen) || a.tool.localeCompare(b.tool));
  const moves = tools.filter((t) => !t.present_at_start).map((t) => {
    const s = seen.get(t.tool).first;
    return t.group === 'ads'
      ? moveRow(s.date, 'paid', 'ad-start', `${t.tool} first seen in ${domain} homepage source (pixel present; ads running is inferred)`, archiveView(s), 'Inferred')
      : moveRow(s.date, GROUP_CHANNEL[t.group], 'tool-added', `${t.tool} (${t.group}) first seen in ${domain} homepage source`, archiveView(s), 'Observed');
  });
  notes.push('first_seen is the first monthly capture containing the script; the tool may predate it. Scripts loaded through a tag manager or after consent do not show, so absence is not proof.');
  const text = [
    `${domain}: ${read} of ${snaps.length} monthly homepage captures read (window ${months} months), pulled ${ctx.today}`,
    tools.length ? table(['tool', 'group', 'first seen', 'last seen', 'at start'], tools.map((t) => [t.tool, t.group, t.first_seen, t.last_seen, t.present_at_start])) : 'No known tool signatures found in the captures.',
  ].join('\n');
  return { text, notes, moves, out: { rows: tools, headers: ['tool', 'group', 'first_seen', 'last_seen', 'present_at_start', 'capture'] }, json: { domain, pulled: ctx.today, captures: snaps.length, read, tools } };
}

function parseTargetUrl(input, cmd) {
  const raw = String(input ?? '').trim();
  if (!raw) fail(`${cmd} needs a URL, for example: ${cmd} ${cmd === 'podcast' ? 'https://feeds.example.com/show.xml' : 'example.com/pricing'}`);
  const u = tryUrl(/^[a-z]+:\/\//i.test(raw) ? raw : `https://${raw}`);
  if (!u) fail(`"${input}" is not a URL`);
  if (!HOST_RE.test(u.hostname)) fail(`"${input}" is not a URL with a domain`);
  return u;
}

async function cmdHistory(o, ctx) {
  const u = parseTargetUrl(o.args[0], 'history');
  const months = posInt(o.months, 'months', { def: 24, max: 120 });
  const target = `${u.hostname}${u.pathname}${u.search}`;
  const channel = o.channel || (/pric|plans?\b/i.test(u.pathname) ? 'pricing' : 'site');
  const snaps = await snapshots(ctx.client(), target, months, ctx.now);
  const rows = snaps.map((s, k) => ({ month: s.month, date: s.date, digest: s.digest, changed: k > 0 && s.digest !== snaps[k - 1].digest ? 'yes' : '', capture: archiveView(s) }));
  const changes = rows.filter((r) => r.changed);
  const moves = changes.map((r) => moveRow(r.date, channel, 'page-change', `${target} content changed since the prior monthly capture`, r.capture, 'Observed'));
  const notes = ['A digest change means the archived bytes changed; small template or token changes count too. Open the capture to see what moved.'];
  const text = [
    `${target}: ${snaps.length} monthly captures, ${changes.length} month(s) with changed content, pulled ${ctx.today}`,
    changes.length ? table(['month', 'capture'], changes.map((r) => [r.month, r.capture])) : 'No content changes between monthly captures.',
  ].join('\n');
  return { text, notes, moves, out: { rows, headers: ['month', 'date', 'digest', 'changed', 'capture'] }, json: { url: target, pulled: ctx.today, captures: snaps.length, changes } };
}

/** Title, first H1 and meta description, read with scripts and styles removed. */
export function extractHero(html) {
  const clean = stripScripts(html);
  const title = cleanText(clean.match(/<title\b[^>]*>([\s\S]*?)<\/title\s*>/i)?.[1] ?? '');
  const h1 = cleanText(clean.match(/<h1\b[^>]*>([\s\S]*?)<\/h1\s*>/i)?.[1] ?? '');
  let description = '';
  for (const m of clean.matchAll(/<meta\b[^>]*>/gi)) {
    if (attrOf(m[0], 'name').toLowerCase() === 'description') {
      description = cleanText(attrOf(m[0], 'content'));
      break;
    }
  }
  return { title, h1, description };
}

async function cmdHero(o, ctx) {
  const domain = parseHost(o.args[0], 'hero');
  const months = posInt(o.months, 'months', { def: 24, max: 120 });
  const client = ctx.client();
  const snaps = await snapshots(client, `${domain}/`, months, ctx.now);
  const notes = [];
  const rows = [];
  let prev = null;
  await eachSnapshot(client, snaps, notes, (s, html) => {
    const hero = extractHero(html);
    if (!hero.title && !hero.h1 && !hero.description) return notes.push(`${s.month}: no title, H1 or description in the capture`);
    const changed = prev ? ['h1', 'title', 'description'].filter((f) => hero[f] !== prev[f]) : [];
    rows.push({ month: s.month, date: s.date, ...hero, changed: changed.join(' '), capture: archiveView(s) });
    prev = hero;
  });
  const changes = rows.filter((r) => r.changed);
  const moves = changes.map((r) => moveRow(r.date, 'site', 'positioning-change', `${domain} homepage ${r.changed.split(' ').map((f) => `${f === 'h1' ? 'H1' : f}: "${clip(r[f], 70)}"`).join('; ')}`, r.capture, 'Observed'));
  const text = [
    `${domain}: ${rows.length} homepage captures read, ${changes.length} month(s) with a hero change, pulled ${ctx.today}`,
    rows.length ? table(['month', 'changed', 'h1', 'title'], rows.map((r) => [r.month, r.changed || (r === rows[0] ? '(start)' : ''), clip(r.h1, 60), clip(r.title, 50)])) : 'No readable captures.',
  ].join('\n');
  return { text, notes, moves, out: { rows, headers: ['month', 'date', 'title', 'h1', 'description', 'changed', 'capture'] }, json: { domain, pulled: ctx.today, captures: snaps.length, rows } };
}

// ---------- subdomains (certificate logs) ----------

const NOISE = /^(?:pr-?\d+|preview|staging|stage|stg|dev|test|qa|uat|sandbox|internal|canary|deploy-preview)(?:$|[-\d])/i;

/** crt.sh rows to distinct subdomains with the earliest not_before, minus wildcards and preview/staging names. */
export function parseCertificates(rows, domain) {
  const first = new Map();
  let dropped = 0;
  for (const row of Array.isArray(rows) ? rows : []) {
    const date = toDate(row.not_before ?? row.entry_timestamp);
    for (const raw of String(row.name_value ?? '').split(/\s+/)) {
      const name = raw.trim().toLowerCase().replace(/\.$/, '');
      if (!name || name.startsWith('*') || name === domain || !name.endsWith(`.${domain}`)) continue;
      const cur = first.get(name);
      if (!cur) first.set(name, { date, certs: 1 });
      else {
        cur.certs++;
        if (date && (!cur.date || date < cur.date)) cur.date = date;
      }
    }
  }
  const kept = [];
  for (const [subdomain, v] of first) {
    const labels = subdomain.slice(0, -(domain.length + 1)).split('.');
    if (labels.length > 2 || labels.some((l) => NOISE.test(l))) dropped++;
    else kept.push({ subdomain, first_seen: v.date, certificates: v.certs });
  }
  kept.sort((a, b) => a.first_seen.localeCompare(b.first_seen) || a.subdomain.localeCompare(b.subdomain));
  return { subdomains: kept, dropped };
}

async function cmdSubdomains(o, ctx) {
  const domain = bare(parseHost(o.args[0], 'subdomains'));
  const url = `https://crt.sh/?q=%25.${domain}&output=json`;
  let body;
  try {
    body = await ctx.client().text(url, 'application/json');
  } catch (e) {
    if (isStop(e) || e instanceof InputError) throw e;
    throw new Error(`crt.sh did not answer (${e.message}). It is often overloaded: try again in a few minutes, or open https://crt.sh/?q=%25.${domain} in a browser.`);
  }
  let rows;
  try {
    rows = body.trim() ? JSON.parse(body) : [];
  } catch {
    throw new Error(`crt.sh returned ${/^\s*</.test(body) ? 'an HTML error page' : 'unreadable data'} instead of JSON. It is often overloaded: try again in a few minutes, or open https://crt.sh/?q=%25.${domain} in a browser.`);
  }
  const { subdomains, dropped } = parseCertificates(rows, domain);
  const moves = subdomains.filter((s) => s.first_seen).map((s) => moveRow(s.first_seen, 'infrastructure', 'subdomain', `New subdomain ${s.subdomain} (first certificate)`, `https://crt.sh/?q=${s.subdomain}`, 'Observed'));
  const notes = [`${dropped} preview, staging or deeply nested name(s) dropped. What a subdomain is for stays Inferred until a page confirms it.`];
  const text = [
    `${domain}: ${subdomains.length} subdomain(s) in certificate logs, pulled ${ctx.today}`,
    subdomains.length ? table(['first seen', 'subdomain', 'certs'], subdomains.map((s) => [s.first_seen, s.subdomain, s.certificates])) : 'No subdomains found.',
  ].join('\n');
  return { text, notes, moves, out: { rows: subdomains, headers: ['subdomain', 'first_seen', 'certificates'] }, json: { domain, pulled: ctx.today, dropped, subdomains } };
}

// ---------- dns ----------

const m2 = (tool, pattern) => ({ tool, pattern });
export const TXT_VERIFICATIONS = [
  m2('Google (Search Console or Workspace)', /^google-site-verification=/i), m2('Meta Business', /^facebook-domain-verification=/i),
  m2('Atlassian', /^atlassian-domain-verification=/i), m2('HubSpot', /^hubspot-(?:developer-)?verification=/i),
  m2('Apple', /^apple-domain-verification=/i), m2('Stripe', /^stripe-verification=/i), m2('Microsoft 365', /^MS=/),
  m2('Zendesk', /^zendesk(?:verification|-domain-verification)=/i), m2('Mailchimp (Mandrill)', /^mandrill_verify\./i),
  m2('Brevo', /^(?:sendinblue|brevo)-code:/i), m2('DocuSign', /^docusign=/i), m2('Zoom', /^ZOOM_verify_/i),
  m2('Adobe', /^adobe-(?:idp-site|sign)-verification=/i), m2('OpenAI', /^openai-domain-verification=/i),
  m2('Anthropic', /^anthropic-domain-verification/i), m2('Slack', /^slack-domain-verification=/i),
  m2('Notion', /^notion-domain-verification/i), m2('Pinterest', /^pinterest-site-verification=/i),
  m2('TikTok', /^tiktok-(?:developers-site-)?verification=/i), m2('Dropbox', /^dropbox-domain-verification=/i),
  m2('Miro', /^miro-verification=/i), m2('Canva', /^canva-site-verification=/i), m2('Yandex Webmaster', /^yandex-verification:/i),
  m2('Klaviyo', /^klaviyo-site-verification=/i), m2('Postman', /^postman-domain-verification=/i),
];
export const MAIL_SENDERS = [
  m2('Google Workspace', /_spf\.google\.com|aspmx\.l\.google\.com/i), m2('Microsoft 365', /spf\.protection\.outlook\.com|mail\.protection\.outlook\.com/i),
  m2('SendGrid', /sendgrid\.net/i), m2('Mailchimp', /servers\.mcsv\.net/i), m2('Mandrill', /mandrillapp\.com/i), m2('Klaviyo', /klaviyo/i),
  m2('Postmark', /spf\.mtasv\.net/i), m2('Amazon SES', /amazonses\.com/i), m2('Customer.io', /customeriomail\.com|customer\.io/i),
  m2('Mailgun', /mailgun\.org/i), m2('HubSpot', /hubspotemail\.net|hubspot/i), m2('Salesforce', /_spf\.salesforce\.com/i),
  m2('Marketo', /mktomail\.com/i), m2('Pardot', /pardot\.com/i), m2('Zendesk', /zendesk\.com/i), m2('Intercom', /intercom\.io/i),
  m2('Help Scout', /helpscoutemail\.com/i), m2('Freshdesk', /freshdesk\.com|freshemail\.io/i), m2('Brevo', /sendinblue\.com|brevo\.com/i),
  m2('SparkPost', /sparkpostmail\.com/i), m2('Campaign Monitor', /createsend\.com/i), m2('Mailjet', /mailjet\.com/i),
  m2('Proofpoint', /pphosted\.com/i), m2('Mimecast', /mimecast/i), m2('Zoho Mail', /zoho\.(?:com|eu)/i),
];
export const CNAME_TOOLS = [
  m2('HubSpot', /hubspot|hs-sites/i), m2('Marketo', /mktoweb|mktossl|marketo/i), m2('Pardot', /pardot/i), m2('Zendesk', /zendesk/i),
  m2('Intercom', /intercom/i), m2('Help Scout', /helpscout/i), m2('GitBook', /gitbook/i), m2('Mintlify', /mintlify/i),
  m2('ReadMe', /readme\.io|readmessl/i), m2('Discourse', /discourse/i), m2('Circle', /circle\.so/i), m2('Webflow', /webflow/i),
  m2('Framer', /framer/i), m2('Ghost', /ghost\.io/i), m2('Substack', /substack/i), m2('beehiiv', /beehiiv/i), m2('Unbounce', /unbounce/i),
  m2('Instapage', /pageserve|instapage/i), m2('Leadpages', /leadpages/i), m2('Shopify', /myshopify|shopify/i),
  m2('SendGrid (link branding)', /sendgrid\.net/i), m2('Mailgun', /mailgun\.org/i), m2('Mailchimp', /mcsv\.net|mailchimp/i),
  m2('Klaviyo', /klaviyo/i), m2('Customer.io', /customer\.io|customeriomail/i), m2('Braze', /braze/i), m2('Branch', /app\.link|branch\.io/i),
  m2('Bitly', /bitly/i), m2('Rebrandly', /rebrandly/i), m2('Dub', /dub\.co/i), m2('Teachable', /teachable/i), m2('Thinkific', /thinkific/i),
  m2('Kajabi', /kajabi/i), m2('Eventbrite', /eventbrite/i), m2('Statuspage', /statuspage\.io/i), m2('Vercel', /vercel/i), m2('Netlify', /netlify/i),
];
export const MARKETING_SUBDOMAINS = ['www', 'go', 'get', 'info', 'mail', 'email', 'links', 'link', 'click', 'learn', 'events', 'community',
  'help', 'support', 'docs', 'blog', 'shop', 'store', 'partners', 'affiliates', 'try', 'lp', 'pages', 'news', 'academy', 'status', 'creators', 'merch'];

/** Map TXT, MX and CNAME answers to tool names. Verification tokens are reduced to their prefix. */
export function mapDns(domain, { txt = [], mx = [], cnames = {} }) {
  const found = [];
  for (const r of txt) {
    if (/^v=spf1/i.test(r)) {
      for (const inc of r.split(/\s+/).filter((p) => /^(?:include:|redirect=)/i.test(p))) {
        const s = MAIL_SENDERS.find((x) => x.pattern.test(inc));
        found.push({ record: 'SPF', host: domain, value: inc, tool: s?.tool ?? '' });
      }
      continue;
    }
    const v = TXT_VERIFICATIONS.find((x) => x.pattern.test(r));
    if (v) found.push({ record: 'TXT', host: domain, value: r.split(/[=:]/)[0], tool: v.tool });
    else if (/verif/i.test(r)) found.push({ record: 'TXT', host: domain, value: r.split(/[=:]/)[0], tool: '' });
  }
  for (const m of mx) found.push({ record: 'MX', host: domain, value: m, tool: MAIL_SENDERS.find((x) => x.pattern.test(m))?.tool ?? '' });
  for (const [host, target] of Object.entries(cnames)) found.push({ record: 'CNAME', host, value: target, tool: CNAME_TOOLS.find((x) => x.pattern.test(target))?.tool ?? '' });
  return found;
}

async function cmdDns(o, ctx) {
  const domain = bare(parseHost(o.args[0], 'dns'));
  const notes = [];
  const q = async (fn, name) => {
    try {
      return await fn(name);
    } catch (e) {
      if (!['ENODATA', 'ENOTFOUND', 'NXDOMAIN', 'ENOTIMP'].includes(e?.code)) notes.push(`${name}: ${e?.code ?? e?.message}`);
      return [];
    }
  };
  const r = ctx.dns;
  const txt = (await q((n) => r.resolveTxt(n), domain)).map((parts) => (Array.isArray(parts) ? parts.join('') : String(parts)));
  const mx = (await q((n) => r.resolveMx(n), domain)).map((x) => x.exchange ?? String(x));
  const cnames = {};
  for (const sub of MARKETING_SUBDOMAINS) {
    const name = `${sub}.${domain}`;
    const ans = await q((n) => r.resolveCname(n), name);
    if (ans.length) cnames[name] = ans[0];
  }
  const rows = mapDns(domain, { txt, mx, cnames });
  const tools = rows.filter((x) => x.tool);
  const seen = new Set();
  const moves = [];
  for (const t of tools) {
    const what = t.record === 'CNAME' ? `${t.host} points to ${t.tool}` : t.record === 'TXT' ? `${t.tool} domain verification on ${domain}` : `${t.record} names ${t.tool} for ${domain}`;
    if (seen.has(what)) continue;
    seen.add(what);
    const type = t.record === 'SPF' ? 'TXT' : t.record;
    moves.push(moveRow(ctx.today, 'infrastructure', 'tool-verified', what, `https://dns.google/resolve?name=${t.host}&type=${type}`, 'Observed'));
  }
  notes.push('DNS has no dates: the moves carry today\'s date. Date a tool only when an archive shows when it appeared. What a record implies about use is Inferred.');
  const text = [
    `${domain}: ${rows.length} record(s) of interest, ${new Set(tools.map((t) => t.tool)).size} tool(s) named, checked ${ctx.today}`,
    rows.length ? table(['record', 'host', 'tool', 'value'], rows.map((x) => [x.record, x.host, x.tool || '(unmapped)', clip(x.value, 50)])) : 'No TXT, MX or marketing CNAME records found.',
  ].join('\n');
  return { text, notes, moves, out: { rows, headers: ['record', 'host', 'value', 'tool'] }, json: { domain, checked: ctx.today, records: rows } };
}

// ---------- jobs ----------

export const CHANNELS = [
  ['seo', /\bseo\b|search engine optimi[sz]ation|organic search/i],
  ['ai-search', /\baeo\b|\bgeo\b|ai search|answer engine|generative engine|llm (?:visibility|optimi[sz]ation)/i],
  ['content', /content (?:market|strateg|writ|lead|manag|creat|design|produc)|editorial|copywrit/i],
  ['paid', /paid (?:social|search|media|acquisition|ads)|performance marketing|\bppc\b|\bsem\b|media buy|user acquisition/i],
  ['lifecycle', /lifecycle|email marketing|\bcrm\b|retention marketing|marketing automation/i],
  ['partnerships', /partnerships?\b|alliances|affiliate|channel partner/i],
  ['community', /community/i],
  ['influencer', /influencer|creator (?:marketing|partnership|program)|\bugc\b/i],
  ['pr', /public relations|\bpr\b|media relations|\bpress\b|communications manager|corporate communications/i],
  ['product-marketing', /product marketing|\bpmm\b|go-to-market/i],
  ['growth', /growth (?:market|lead|manag|team|engineer|hack)|head of growth|\bplg\b|product-led|experimentation/i],
];
const FUNCTIONS = [
  ['marketing', /market|growth|brand|content|\bseo\b|communications|\bpr\b|community|social media|lifecycle|demand gen|devrel|developer relations|advocate|influencer|creator|copywrit/i],
  ['sales', /sales|account executive|business development|\b[sb]dr\b|account manager|partnerships|revenue/i],
  ['customer', /support|customer success|customer experience|implementation|onboarding/i],
  ['product', /product manager|product owner|head of product|product lead/i],
  ['design', /design|\bux\b/i],
  ['data', /\bdata\b|analytics|analyst|scientist|machine learning|\bml\b/i],
  ['engineering', /engineer|developer|\bsre\b|devops|architect|security|infrastructure/i],
  ['operations', /recruit|talent|people|\bhr\b|finance|accounting|accountant|legal|counsel|operations|office|admin|assistant/i],
];
export const classifyRole = (title, dept = '') => FUNCTIONS.find(([, re]) => re.test(title))?.[0] ?? FUNCTIONS.find(([, re]) => re.test(dept))?.[0] ?? 'other';
export const tagChannels = (text) => CHANNELS.filter(([, re]) => re.test(text)).map(([c]) => c);

export const atsUrl = (ats, slug) => ({
  greenhouse: `https://boards-api.greenhouse.io/v1/boards/${slug}/jobs?content=true`,
  lever: `https://api.lever.co/v0/postings/${slug}?mode=json`,
  ashby: `https://api.ashbyhq.com/posting-api/job-board/${slug}`,
})[ats];

/** Normalize one board's JSON. Only role facts are kept; recruiter or hiring-manager details are never read. */
export function normalizeJobs(ats, json) {
  const pick = (title, department, location, posted, url, body) => {
    const t = cleanText(title);
    const text = scrubPersonal(`${t} ${department} ${cleanText(decodeEntities(body ?? ''))}`);
    return { title: t, department: cleanText(department), location: cleanText(location), posted: toDate(posted), url: url ?? '', channels: tagChannels(text).join(' '), function: classifyRole(t, department) };
  };
  if (ats === 'greenhouse') return (json?.jobs ?? []).map((j) => pick(j.title, j.departments?.[0]?.name ?? '', j.location?.name ?? '', j.first_published ?? j.updated_at, j.absolute_url, j.content));
  if (ats === 'lever') {
    return (Array.isArray(json) ? json : []).map((j) => pick(j.text, j.categories?.department ?? j.categories?.team ?? '', j.categories?.location ?? '',
      j.createdAt ? new Date(Number(j.createdAt)).toISOString() : '', j.hostedUrl, [j.descriptionPlain, ...(j.lists ?? []).map((l) => `${l.text} ${l.content}`), j.additionalPlain].join(' ')));
  }
  if (ats === 'ashby') return (json?.jobs ?? []).filter((j) => j.isListed !== false).map((j) => pick(j.title, j.department ?? j.team ?? '', j.location ?? '', j.publishedAt, j.jobUrl, j.descriptionPlain ?? j.descriptionHtml));
  return [];
}

async function cmdJobs(o, ctx) {
  const slug = String(o.args[0] ?? '').trim().toLowerCase().replace(/[^a-z0-9._-]/g, '');
  if (!slug) fail('jobs needs a company or board slug, for example: jobs acme');
  const client = ctx.client();
  const notes = [];
  const sources = [];
  const jobs = [];
  for (const ats of ['greenhouse', 'lever', 'ashby']) {
    try {
      const found = normalizeJobs(ats, await client.json(atsUrl(ats, slug)));
      sources.push([ats, found.length ? `${found.length} open role(s)` : 'board empty']);
      jobs.push(...found.map((j) => ({ ...j, source: ats })));
    } catch (e) {
      if (e instanceof HttpError && e.status === 404) sources.push([ats, 'no board']);
      else {
        sources.push([ats, isStop(e) ? 'blocked' : 'error']);
        notes.push(e.message);
      }
    }
  }
  const byFn = {};
  for (const j of jobs) {
    const f = (byFn[j.function] ??= { roles: 0, channels: {} });
    f.roles++;
    for (const c of j.channels.split(' ').filter(Boolean)) f.channels[c] = (f.channels[c] ?? 0) + 1;
  }
  const fnRows = Object.entries(byFn).sort((a, b) => b[1].roles - a[1].roles).map(([fn, v]) => [fn, v.roles, Object.entries(v.channels).sort((a, b) => b[1] - a[1]).map(([c, n]) => `${c} ${n}`).join(', ')]);
  notes.push('Names and contact details in postings are not collected. Posted dates come from each board (Greenhouse falls back to the last update).');
  const text = [
    `${slug}: ${jobs.length} open role(s), pulled ${ctx.today}`,
    table(['board', 'result'], sources),
    jobs.length ? `\nBy function:\n${table(['function', 'roles', 'marketing channels named'], fnRows)}` : 'No public Greenhouse, Lever or Ashby board under that slug. Check the careers page for the board link.',
  ].join('\n');
  return { text, notes, out: { rows: jobs, headers: ['title', 'department', 'location', 'posted', 'url', 'channels', 'function', 'source'] }, json: { slug, pulled: ctx.today, sources: Object.fromEntries(sources), functions: byFn, jobs } };
}

// ---------- reviews (App Store) ----------

const STOPWORDS = new Set(('a about after again all also always am an and any app apps are as at back be because been before being but by can cant could did didnt do does doesnt dont even ever every for from get gets got had has have how i id if im in into is isnt it its ive just keep like make me more most much my need never new no not now of off on once one only or other our out over please really same so some still than that thats the their them then there they thing things this time to too try up use used using very want was way we were what when which while will with wont would yes you your youre').split(' '));

/** Apple review feed entries to {date, rating, text}. Author fields are never read. */
export function parseAppleReviews(json) {
  const entries = [].concat(json?.feed?.entry ?? []);
  return entries.filter((e) => e?.['im:rating']).map((e) => ({ date: toDate(e.updated?.label), rating: Number(e['im:rating'].label), text: `${e.title?.label ?? ''} ${e.content?.label ?? ''}` }));
}

export function reviewSummary(reviews, top = 12) {
  const months = {};
  const terms = {};
  for (const r of reviews) {
    if (!r.date || !(r.rating >= 1 && r.rating <= 5)) continue;
    const m = (months[r.date.slice(0, 7)] ??= { month: r.date.slice(0, 7), count: 0, sum: 0, low_count: 0 });
    m.count++;
    m.sum += r.rating;
    if (r.rating <= 2) {
      m.low_count++;
      const words = new Set(scrubPersonal(r.text).toLowerCase().replace(/['’]/g, '').match(/[a-z][a-z0-9]{2,}/g) ?? []);
      for (const w of words) if (!STOPWORDS.has(w)) terms[w] = (terms[w] ?? 0) + 1;
    }
  }
  const rows = Object.values(months).sort((a, b) => a.month.localeCompare(b.month)).map((m) => ({ month: m.month, count: m.count, avg_rating: Math.round((m.sum / m.count) * 100) / 100, low_count: m.low_count }));
  const complaints = Object.entries(terms).filter(([, n]) => n >= 2).sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0])).slice(0, top).map(([term, reviews]) => ({ term, reviews }));
  return { rows, complaints };
}

async function cmdReviews(o, ctx) {
  const id = String(o.args[0] ?? '').replace(/^id/i, '');
  if (!/^\d{5,12}$/.test(id)) fail('reviews needs a numeric App Store app id, for example: reviews 284882215');
  const country = String(o.country ?? 'us').toLowerCase();
  if (!/^[a-z]{2}$/.test(country)) fail('--country must be a two-letter store code, for example us');
  const pages = posInt(o.pages, 'pages', { def: 10, max: 10 });
  const client = ctx.client();
  const notes = [];
  const reviews = [];
  for (let p = 1; p <= pages; p++) {
    try {
      const batch = parseAppleReviews(await client.json(`https://itunes.apple.com/${country}/rss/customerreviews/page=${p}/id=${id}/sortby=mostrecent/json`));
      if (!batch.length) break;
      reviews.push(...batch);
    } catch (e) {
      notes.push(`page ${p}: ${e.message}`);
      break;
    }
  }
  const { rows, complaints } = reviewSummary(reviews);
  notes.push('The feed holds at most the 500 newest reviews with text for one country, so the oldest month may be partial. Reviewer names are never collected.');
  const avg = reviews.length ? (reviews.reduce((a, r) => a + r.rating, 0) / reviews.length).toFixed(2) : '-';
  const text = [
    `App ${id} (${country}): ${reviews.length} review(s), average ${avg}, pulled ${ctx.today}`,
    rows.length ? table(['month', 'count', 'avg', '1-2 star'], rows.map((r) => [r.month, r.count, r.avg_rating, r.low_count])) : 'No reviews returned.',
    complaints.length ? `\nTop terms in 1-2 star reviews:\n${table(['term', 'reviews'], complaints.map((c) => [c.term, c.reviews]))}` : '',
  ].filter(Boolean).join('\n');
  return { text, notes, out: { rows, headers: ['month', 'count', 'avg_rating', 'low_count'] }, json: { app_id: id, country, pulled: ctx.today, reviews: reviews.length, months: rows, complaint_terms: complaints } };
}

// ---------- adoption ----------

/** Complete months in the window: `months` months ending with the month before `now`. */
export function windowMonths(months, now) {
  const last = addMonths(ymd(now).slice(0, 7), -1);
  return Array.from({ length: months }, (_, k) => addMonths(last, k - months + 1));
}
/** Split the window into npm range requests of at most 18 months each. */
export function npmChunks(months, now) {
  const list = windowMonths(months, now);
  const out = [];
  for (let i = 0; i < list.length; i += 18) {
    const part = list.slice(i, i + 18);
    const end = part[part.length - 1];
    out.push({ from: `${part[0]}-01`, to: `${end}-${pad(daysInMonth(end))}` });
  }
  return out;
}
/** Daily [{day, downloads}] to complete-month totals; months with missing days are dropped. */
export function monthlyTotals(days, wanted) {
  const by = {};
  for (const d of days) {
    const m = String(d.day ?? '').slice(0, 7);
    (by[m] ??= { sum: 0, days: new Set() }).sum += Number(d.downloads) || 0;
    by[m].days.add(d.day);
  }
  const out = {};
  for (const m of wanted) if (by[m] && by[m].days.size >= daysInMonth(m)) out[m] = by[m].sum;
  return out;
}
/** Stars at each month end, interpolated between sampled (index, date) points; null past the last known point. */
export function starsByMonth(points, months, total, now) {
  const pts = [...points].sort((a, b) => a.index - b.index).map((p) => ({ i: p.index, t: Date.parse(p.date) }));
  if (total != null && total <= 40000) pts.push({ i: total, t: now.getTime() });
  const out = {};
  for (const m of months) {
    const t = Date.UTC(+m.slice(0, 4), +m.slice(5, 7), 1) - 1;
    if (!pts.length || t < pts[0].t) out[m] = pts.length ? 0 : null;
    else if (t >= pts[pts.length - 1].t) out[m] = total != null && total <= 40000 ? total : null;
    else {
      const j = pts.findIndex((p) => p.t > t);
      const [a, b] = [pts[j - 1], pts[j]];
      out[m] = Math.round(a.i + ((b.i - a.i) * (t - a.t)) / Math.max(1, b.t - a.t));
    }
  }
  return out;
}

async function githubStars(client, repo, months, pageCap, now, notes) {
  const info = await client.json(`https://api.github.com/repos/${repo}`, 'application/vnd.github+json');
  const total = Number(info.stargazers_count) || 0;
  const last = Math.min(Math.ceil(total / 100), 400);
  const n = Math.min(pageCap, last);
  const pages = [...new Set(Array.from({ length: n }, (_, k) => (n === 1 ? 1 : 1 + Math.round((k * (last - 1)) / (n - 1)))))];
  const points = [];
  try {
    for (const p of pages) {
      const rows = await client.json(`https://api.github.com/repos/${repo}/stargazers?per_page=100&page=${p}`, 'application/vnd.github.star+json');
      if (Array.isArray(rows) && rows.length) points.push({ index: (p - 1) * 100 + 1, date: rows[0].starred_at });
    }
  } catch (e) {
    notes.push(`stars over time stopped: ${e.message}`);
    return { total, history: null };
  }
  if (total > 40000) notes.push('GitHub lists only the first 40,000 stargazers, so later months are blank.');
  return { total, history: starsByMonth(points, months, total, now) };
}

async function cmdAdoption(o, ctx) {
  if (!o.npm && !o.pypi && !o.github) fail('adoption needs --npm <pkg>, --pypi <pkg> or --github <owner/repo>');
  if (o.npm && o.pypi) fail('pick one registry (--npm or --pypi): a curve comes from one source');
  if (o.npm && !/^(?:@[a-z0-9-~][a-z0-9-._~]*\/)?[a-z0-9-~][a-z0-9-._~]*$/.test(o.npm)) fail(`"${o.npm}" is not an npm package name`);
  if (o.pypi && !/^[A-Za-z0-9][A-Za-z0-9._-]*$/.test(o.pypi)) fail(`"${o.pypi}" is not a PyPI package name`);
  if (o.github && !/^[\w.-]+\/[\w.-]+$/.test(o.github)) fail('--github must be owner/repo');
  const months = posInt(o.months, 'months', { def: 24, max: 120 });
  const pageCap = posInt(o['star-pages'], 'star-pages', { def: 10, max: 50 });
  const client = ctx.client();
  const notes = [];
  const list = windowMonths(months, ctx.now);
  let registry = null;
  let source = '';
  if (o.npm) {
    const days = [];
    for (const c of npmChunks(months, ctx.now)) days.push(...((await client.json(`https://api.npmjs.org/downloads/range/${c.from}:${c.to}/${o.npm}`)).downloads ?? []));
    registry = monthlyTotals(days, list);
    source = `npm downloads (${o.npm})`;
  } else if (o.pypi) {
    const json = await client.json(`https://pypistats.org/api/packages/${o.pypi.toLowerCase()}/overall?mirrors=false`);
    registry = monthlyTotals((json.data ?? []).filter((d) => d.category === 'without_mirrors').map((d) => ({ day: d.date, downloads: d.downloads })), list);
    source = `PyPI downloads without mirrors (${o.pypi})`;
    notes.push('PyPI Stats keeps about 180 days, so the curve starts there. Do not stitch in another source.');
  }
  let gh = null;
  if (o.github) {
    try {
      gh = await githubStars(client, o.github, list, pageCap, ctx.now, notes);
    } catch (e) {
      if (!registry) throw e;
      notes.push(`GitHub: ${e.message}`);
    }
  }
  const primary = registry ?? gh?.history ?? {};
  const secondary = registry && gh?.history ? gh.history : null;
  const filled = list.filter((m) => primary[m] != null);
  while (registry && filled.length && registry[filled[0]] === 0) filled.shift(); // before the package existed
  let rows = [];
  if (filled.length) {
    const span = list.slice(list.indexOf(filled[0]), list.indexOf(filled[filled.length - 1]) + 1);
    if (span.some((m) => primary[m] == null)) notes.push('some months inside the window had no complete data; those rows are blank');
    rows = span.map((m) => ({ month: m, primary: primary[m] ?? '', secondary: secondary?.[m] ?? '' }));
  }
  const labelP = registry ? source : `GitHub stars (${o.github})`;
  notes.push(`primary = ${labelP}${secondary ? `; secondary = GitHub stars (${o.github}), interpolated from sampled stargazer pages` : ''}. Downloads include CI and bots: read the trend, not the level. Partial months are left out.`);
  const text = [
    `Adoption, pulled ${ctx.today}: ${rows.length} complete month(s)${gh ? `; ${o.github} has ${gh.total} stars now` : ''}`,
    rows.length ? table(['month', 'primary', 'secondary'], rows.map((r) => [r.month, r.primary, r.secondary])) : 'No monthly data returned.',
  ].join('\n');
  return { text, notes, out: { rows, headers: ['month', 'primary', 'secondary'] }, json: { pulled: ctx.today, primary: labelP, secondary: secondary ? `GitHub stars (${o.github})` : null, github_stars_now: gh?.total ?? null, curve: rows } };
}

// ---------- feeds: YouTube and podcasts ----------

function cadence(dates) {
  const by = {};
  for (const d of dates) if (d) by[d.slice(0, 7)] = (by[d.slice(0, 7)] ?? 0) + 1;
  const sorted = [...dates].filter(Boolean).sort();
  const gaps = sorted.slice(1).map((d, k) => (Date.parse(d) - Date.parse(sorted[k])) / 86400000).sort((a, b) => a - b);
  const h = gaps.length >> 1;
  const median = gaps.length ? (gaps.length % 2 ? gaps[h] : (gaps[h - 1] + gaps[h]) / 2) : null;
  return { months: Object.entries(by).sort((a, b) => a[0].localeCompare(b[0])), median };
}

export function parseYoutubeFeed(xml) {
  return xmlBlocks(xml, 'entry').map((e) => {
    const views = xmlAttr(e, 'media:statistics', 'views');
    const id = xmlText(e, 'yt:videoId');
    return { channel: 'youtube', date: toDate(xmlText(e, 'published')), url: xmlAttr(e, 'link', 'href') || (id ? `https://www.youtube.com/watch?v=${id}` : ''), views: views === '' ? '' : Number(views), title: xmlText(e, 'title') };
  });
}

async function cmdYoutube(o, ctx) {
  const id = String(o.args[0] ?? '').trim();
  if (!/^UC[\w-]{22}$/.test(id)) fail('youtube needs a channel id that starts with UC (24 characters), found on the channel page source or its About share link');
  const posts = parseYoutubeFeed(await ctx.client().text(`https://www.youtube.com/feeds/videos.xml?channel_id=${id}`, 'application/atom+xml,application/xml'));
  const c = cadence(posts.map((p) => p.date));
  const notes = ['The public feed holds only the latest ~15 uploads, so cadence covers a short window. Call no content pattern until 24+ settled posts exist.'];
  const text = [
    `YouTube ${id}: ${posts.length} recent upload(s), pulled ${ctx.today}${c.median != null ? `, median ${c.median.toFixed(1)} days between uploads` : ''}`,
    c.months.length ? table(['month', 'uploads'], c.months) : 'No uploads in the feed.',
  ].join('\n');
  return { text, notes, out: { rows: posts, headers: ['channel', 'date', 'url', 'views', 'title'] }, json: { channel_id: id, pulled: ctx.today, uploads: posts, median_days_between: c.median } };
}

export function parsePodcastFeed(xml) {
  return xmlBlocks(xml, 'item').map((b) => ({
    date: toDate(xmlText(b, 'pubDate')),
    title: xmlText(b, 'title'),
    url: xmlText(b, 'link') || xmlAttr(b, 'enclosure', 'url'),
    enclosure: xmlAttr(b, 'enclosure', 'url'),
    duration: xmlText(b, 'itunes:duration'),
  }));
}

async function cmdPodcast(o, ctx) {
  const feed = parseTargetUrl(o.args[0], 'podcast').href;
  const host = new URL(feed).hostname;
  const episodes = parsePodcastFeed(await ctx.client({ allow: [{ host }] }).text(feed, 'application/rss+xml,application/xml,text/xml'));
  episodes.sort((a, b) => b.date.localeCompare(a.date));
  const c = cadence(episodes.map((e) => e.date));
  const show = feed;
  const moves = episodes.filter((e) => e.date).map((e) => moveRow(e.date, 'podcast', 'release', `Podcast episode: ${e.title}`, e.url || e.enclosure || show, 'Observed'));
  const text = [
    `${host}: ${episodes.length} episode(s), pulled ${ctx.today}${c.median != null ? `, median ${c.median.toFixed(1)} days between episodes` : ''}`,
    c.months.length ? table(['month', 'episodes'], c.months.slice(-24)) : 'No episodes in the feed.',
  ].join('\n');
  return { text, notes: [], moves, out: { rows: episodes, headers: ['date', 'title', 'url', 'enclosure', 'duration'] }, json: { feed, pulled: ctx.today, episodes, median_days_between: c.median } };
}

// ---------- ads (links only) ----------

export function adLibraryLinks(name, domain) {
  const q = encodeURIComponent(name);
  return [
    { network: 'Meta Ad Library', url: `https://www.facebook.com/ads/library/?active_status=all&ad_type=all&country=ALL&q=${q}&search_type=keyword_unordered` },
    { network: 'Google Ads Transparency Center', url: domain ? `https://adstransparency.google.com/?region=anywhere&domain=${encodeURIComponent(domain)}` : `https://adstransparency.google.com/?region=anywhere` },
    { network: 'LinkedIn Ad Library', url: `https://www.linkedin.com/ad-library/search?companyName=${q}` },
    { network: 'TikTok Ad Library', url: `https://library.tiktok.com/ads?region=all&adv_name=${q}` },
  ];
}

async function cmdAds(o, ctx) {
  const name = o.args.join(' ').trim();
  if (!name) fail('ads needs an advertiser name, for example: ads "Acme" --domain acme.com');
  const domain = o.domain ? bare(parseHost(o.domain, 'ads --domain')) : '';
  const links = adLibraryLinks(name, domain).map((l) => ({ ...l, searched: ctx.today }));
  const notes = ['Nothing was fetched. Open each link, record the filter and the date with every finding, and say "no ads found in <library, filter, date>" when empty.'];
  if (!domain) notes.push('Google searches best by domain: rerun with --domain, or type the advertiser name into the search box.');
  const text = [`Ad library searches for "${name}"${domain ? ` (${domain})` : ''}, ${ctx.today}:`, table(['network', 'url'], links.map((l) => [l.network, l.url]))].join('\n');
  return { text, notes, out: { rows: links, headers: ['network', 'url', 'searched'] }, json: { name, domain: domain || null, links } };
}

// ---------- CLI ----------

const USAGE = `collect.mjs: free public-source collectors for growth teardowns

Usage:
  node collect.mjs site <domain> [--out urls.csv]
  node collect.mjs stack <domain> [--months 24] [--max-requests 40] [--out stack.csv] [--moves moves.csv]
  node collect.mjs history <url> [--months 24] [--channel pricing] [--out history.csv] [--moves moves.csv]
  node collect.mjs hero <domain> [--months 24] [--out hero.csv] [--moves moves.csv]
  node collect.mjs subdomains <domain> [--out subdomains.csv] [--moves moves.csv]
  node collect.mjs dns <domain> [--out dns.csv] [--moves moves.csv]
  node collect.mjs jobs <company-or-board-slug> [--out jobs.csv]
  node collect.mjs reviews <app-id> [--country us] [--pages 10] [--out reviews.csv]
  node collect.mjs adoption (--npm <pkg> | --pypi <pkg>) [--github <owner/repo>] [--months 24] [--star-pages 10] [--out curve.csv]
  node collect.mjs youtube <channel-id> [--out posts-youtube.csv]
  node collect.mjs podcast <rss-url> [--out episodes.csv] [--moves moves.csv]
  node collect.mjs ads <name> [--domain example.com] [--out ads.csv]

Every command takes --json. --moves appends rows (date,channel,kind,move,reach,link,evidence) to a
moves.csv, creating it if absent and skipping rows already there (same date, channel, kind, move).
Requests identify as ${USER_AGENT}. A 401/403/429 stops that source;
archive.org requests are spaced 1.5 s apart and capped by --max-requests (default 40).`;

const COMMANDS = { site: cmdSite, stack: cmdStack, history: cmdHistory, hero: cmdHero, subdomains: cmdSubdomains, dns: cmdDns, jobs: cmdJobs, reviews: cmdReviews, adoption: cmdAdoption, youtube: cmdYoutube, podcast: cmdPodcast, ads: cmdAds };
const MOVE_COMMANDS = new Set(['stack', 'history', 'hero', 'subdomains', 'dns', 'podcast']);

/** Run the CLI. Returns a promise of the exit code. deps: { log, error, fetchImpl, sleep, dns, now }. */
export async function main(argv, deps = {}) {
  const log = deps.log ?? console.log;
  const error = deps.error ?? console.error;
  const [cmd, ...rest] = argv;
  if (!cmd || cmd === '--help' || cmd === '-h' || cmd === 'help') {
    log(USAGE);
    return cmd ? 0 : 1;
  }
  try {
    if (!COMMANDS[cmd]) fail(`unknown command "${cmd}" (expected: ${Object.keys(COMMANDS).join(', ')})`);
    const str = { type: 'string' };
    const { values, positionals } = parseArgs({
      args: rest,
      strict: true,
      allowPositionals: true,
      options: {
        out: str, moves: str, months: str, 'max-requests': str, channel: str, country: str, pages: str,
        npm: str, pypi: str, github: str, 'star-pages': str, domain: str,
        json: { type: 'boolean' }, help: { type: 'boolean', short: 'h' },
      },
    });
    if (values.help) {
      log(USAGE);
      return 0;
    }
    if (values.moves && !MOVE_COMMANDS.has(cmd)) fail(`${cmd} does not produce moves; --moves works with ${[...MOVE_COMMANDS].join(', ')}`);
    const maxRequests = posInt(values['max-requests'], 'max-requests', { def: 40, max: 1000 });
    const now = deps.now ? deps.now() : new Date();
    const ctx = {
      now,
      today: ymd(now),
      dns: deps.dns ?? dnsPromises,
      client: (extra = {}) => createClient({ fetchImpl: deps.fetchImpl ?? globalThis.fetch, sleep: deps.sleep ?? defaultSleep, maxRequests, ...extra }),
    };
    const result = await COMMANDS[cmd]({ ...values, args: positionals }, ctx);
    const done = [];
    if (values.out) {
      writeOut(values.out, result.out.rows, result.out.headers);
      done.push(`wrote ${result.out.rows.length} row(s) to ${values.out}`);
    }
    if (values.moves) {
      const r = appendMoves(values.moves, result.moves ?? []);
      done.push(`moves: ${r.added} added to ${values.moves}, ${r.skipped} already there`);
    }
    if (values.json) log(JSON.stringify({ ...result.json, notes: result.notes ?? [], moves: result.moves ?? [] }, null, 2));
    else log([result.text, ...(result.notes ?? []).map((n) => `note: ${n}`), ...done].join('\n'));
    return 0;
  } catch (e) {
    error(`collect: ${e.message}`);
    if (e?.code?.startsWith?.('ERR_PARSE_ARGS')) error('Run with --help for usage.');
    return 1;
  }
}

function invokedDirectly() {
  if (!process.argv[1]) return false;
  try {
    return import.meta.url === pathToFileURL(realpathSync(process.argv[1])).href;
  } catch {
    return import.meta.url === pathToFileURL(process.argv[1]).href;
  }
}

if (invokedDirectly()) main(process.argv.slice(2)).then((code) => (process.exitCode = code));
