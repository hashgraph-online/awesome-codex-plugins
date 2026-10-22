#!/usr/bin/env node
/**
 * verify.mjs: checks in a real browser that a site's analytics keep their
 * privacy promises. Part of the sectionsight skill (MIT).
 *
 *   node verify.mjs --url http://192.168.1.20:3000 --pages /,/pricing --private /account/x \
 *     --mode consent --banner yes --posthog /ingest
 *
 * Needs Playwright where it can be imported from the current directory or
 * this script's: `npm i -D playwright && npx playwright install chromium`.
 *
 * Checks (each PASS / FAIL / SKIP, exit code 1 on any FAIL):
 *  1. Before any answer: no cookies, nothing in localStorage, sessionStorage,
 *     IndexedDB or Cache Storage (except --allow-storage), also after waiting
 *     --settle ms for late scripts; no request to PostHog or a known
 *     third-party tracker; the collector's reports carry no ids (mode
 *     consent/never) and never the probe e-mail or token put into every URL's
 *     query, nor the token-like path segment of --path-probe.
 *  2. Private paths: no report, no PostHog request, no banner.
 *  3. After Accept: reports carry ids (mode consent), PostHog runs (if
 *     --posthog), and no request body (gzip/base64 decoded) holds the probes.
 *  4. Withdrawal in one tab stops PostHog and ids in another open tab, and
 *     removes PostHog's storage (except its opt-out flag) in both tabs.
 *  5. --consent-counts (k.js data-consent-counts="on"): the banner's
 *     shown/accept/decline/withdraw reports never carry ids, the Accept and
 *     the withdrawal included (SKIP when no Accept was counted); under GPC
 *     nothing is sent at all (check 9).
 *  6. Global Privacy Control after an earlier Accept, and an expired answer.
 *  7. "Delete my visit data" (consent.js, after an Accept): the request
 *     carries { del: <this visit's id> } and nothing else, no query in its
 *     URL; with --rows-url the visit's rows are gone (SKIP without a button).
 *  8. --errors (k.js data-errors="on"): an Error thrown by a same-origin
 *     script with the probe e-mail (also as %40) and token, the page URL and a
 *     relative query in its message must reach the
 *     collector as an "err" report without the probes and without ids,
 *     before consent and after it (SKIP when no err report arrives).
 *  9. Global Privacy Control: no report, no PostHog, no banner.
 * 10. The 404 page: with k.js's data-k404 marker, an "nf" report with the
 *     path only (SKIP without the marker); a missing path answers 404.
 * 11. Broken things, read-only (also with --no-write): --expect CTA targets,
 *     --indexable and --noindex pages (meta robots, X-Robots-Tag,
 *     robots.txt), --sitemap.
 * 12. Nothing broken by these scripts: no uncaught error or CSP violation
 *     from k.js, consent.js or the PostHog guard, no hydration error.
 * 13. --privacy-page: the privacy text names every recipient: PostHog (with
 *     --posthog), each of --processors ("Umami", or "Google Fonts=fonts.gstatic.com"
 *     to cover a host), and every other host the browser sent a request to.
 * Throughout: the collector answers every report without an error.
 *
 * It sees what the browser sends, not what a server forwards afterwards: a
 * server-side rewrite that passes Cookie or Referer on to a vendor is
 * invisible here (references/verify.md has the manual check).
 *
 * The browser hides navigator.webdriver, because k.js and PostHog stay
 * silent under automation by design.
 *
 * --no-write: reports and PostHog events are read in the browser and then
 * answered there (204), so nothing reaches the server. Use it on production.
 *
 * In CI: --config privacy-check.config.json holds the settings (flags win
 * over it), --github writes a table to the job summary and an annotation per
 * failure, --json <file> is where the full results go (default
 * privacy-check.json), and --fail-on-skip fails on any SKIP too.
 * assets/ci/privacy-check.yml is a workflow that runs it.
 */
import { createRequire } from 'node:module';
import { randomBytes } from 'node:crypto';
import { gunzipSync } from 'node:zlib';
import { writeFileSync, readFileSync, appendFileSync } from 'node:fs';
import path from 'node:path';

// --- Arguments ---------------------------------------------------------------------
// Flags may also come from a JSON file (--config privacy-check.config.json),
// so CI and local runs share one set of settings; flags on the command line
// win over the file. references/verify.md has the file's schema.
const FLAGS = new Set(['url', 'pages', 'private', 'mode', 'banner', 'collector', 'posthog', 'accept', 'decline', 'settings',
  'settings-page', 'allow-storage', 'allow-cookies', 'allow-hosts', 'resolve', 'consent-key', 'path-probe', 'settle',
  'no-write', 'headed', 'report', 'json', 'github', 'fail-on-skip', 'config',
  'expect', 'indexable', 'noindex', 'sitemap', 'sitemap-host', 'delete-button', 'rows-url', 'preview', 'preview-writes', 'errors', 'consent-counts',
  'privacy-page', 'processors']);
const REPEATED = new Set(['expect']);
const cli = {};
for (let i = 2; i < process.argv.length; i++) {
  const a = process.argv[i];
  if (!a.startsWith('--')) continue;
  const next = process.argv[i + 1];
  const name = a.slice(2);
  const value = next !== undefined && !next.startsWith('--') ? (i++, next) : 'yes';
  if (REPEATED.has(name)) (cli[name] ??= []).push(value);
  else cli[name] = value;
}
function fromConfig(file) {
  let raw;
  try {
    raw = JSON.parse(readFileSync(file, 'utf8'));
  } catch (err) {
    console.error(`--config ${file}: ${err.message}`);
    process.exit(2);
  }
  const out = {};
  for (const [k, v] of Object.entries(raw ?? {})) {
    if (k.startsWith('$') || k.startsWith('_')) continue; // "$schema", "_comment"
    // camelCase or kebab-case; "ids" is the k.js name of --mode.
    const name = k === 'ids' ? 'mode' : k.replace(/[A-Z]/g, (c) => '-' + c.toLowerCase());
    if (!FLAGS.has(name) || name === 'config') {
      console.error(`--config ${file}: unknown key "${k}"`);
      process.exit(2);
    }
    if (v === null || v === undefined) continue;
    if (REPEATED.has(name)) {
      // "expect": false (or true, or a number) is a mistake, not a selector.
      const list = Array.isArray(v) ? v : [v];
      if (list.some((x) => !(typeof x === 'string' || (x && typeof x === 'object' && !Array.isArray(x))))) {
        console.error(`--config ${file}: "${k}" takes a string, an object or a list of them`);
        process.exit(2);
      }
      out[name] = list;
    }
    else if (v === true) out[name] = 'yes';
    else if (v === false) out[name] = 'no';
    else if (Array.isArray(v)) out[name] = v.join(',');
    else out[name] = String(v);
  }
  return out;
}
const args = { ...(cli.config ? fromConfig(cli.config) : {}), ...cli };

const csv = (v) => String(v ?? '').split(',').map((s) => s.trim()).filter(Boolean);
const BASE = (args.url || '').replace(/\/$/, '');
if (!BASE) {
  console.error('Usage: node verify.mjs --url <base> [--pages /,/a] [--private /p] [--mode consent|never|always] [--banner yes|no]\n' +
    '  [--collector /api/k] [--posthog /ingest] [--accept "text=Accept"] [--decline "text=Decline"]\n' +
    '  [--settings "[data-consent-open]"] [--settings-page /privacy] [--allow-storage key1,key2] [--allow-cookies name1]\n' +
    '  [--allow-hosts cdn.example.com] [--resolve acme.test] [--consent-key analytics-consent] [--path-probe /blog/<token>|no]\n' +
    '  [--settle 8000] [--no-write] [--headed] [--json privacy-check.json] [--github] [--fail-on-skip]\n' +
    '  [--config privacy-check.config.json] [--expect \'a[data-kcta=x]@href=^https://\']... [--indexable /,/a] [--noindex /thanks]\n' +
    '  [--sitemap [/sitemap.xml]] [--sitemap-host www.example.com] [--delete-button "[data-consent-delete]"] [--rows-url /__rows] [--errors] [--consent-counts]\n' +
    '  [--preview] [--preview-writes] [--privacy-page /privacy] [--processors "Umami,Google Fonts=fonts.gstatic.com"]');
  process.exit(2);
}
const PAGES = csv(args.pages || '/');
const PRIVATE = csv(args.private);
const MODE = args.mode || 'consent';
const BANNER = (args.banner || (MODE === 'consent' ? 'yes' : 'no')) === 'yes';
const COLLECTOR = args.collector || '/api/k';
const POSTHOG = args.posthog || '';
const ACCEPT = args.accept || 'button:has-text("Accept")';
const DECLINE = args.decline || 'button:has-text("Decline")';
const SETTINGS = args.settings || '[data-consent-open]';
// Where the withdrawal control is checked (every page should have one; a site
// that has it only on its privacy page can say so here).
const SETTINGS_PAGE = args['settings-page'] || '';
const ALLOW_STORAGE = csv(args['allow-storage'] || 'analytics-consent,analytics-consent-at');
const ALLOW_COOKIES = csv(args['allow-cookies']);
// Other hosts a page may contact before consent (a font or script CDN).
const ALLOW_HOSTS = csv(args['allow-hosts']);
// --json (or its older name --report): where the full results go.
const REPORT = args.json || args.report || 'privacy-check.json';
// --github: also a table in the job summary and an annotation per failure.
const GITHUB = args.github === 'yes';
const FAIL_ON_SKIP = args['fail-on-skip'] === 'yes';
const HEADED = args.headed === 'yes';
// --resolve acme.test: the browser resolves these hosts to 127.0.0.1, so a
// local server can be checked under its production name (some code, PostHog's
// included, behaves differently on localhost).
const RESOLVE = csv(args.resolve);
// Where the consent answer is stored (consent.js's default), for the expiry check.
const CONSENT_KEY = args['consent-key'] || 'analytics-consent';
// --preview: a preview deployment, which often shares the production
// database: reads only (as --no-write), unless the config says previews
// have a store of their own ("previewWrites": true).
const PREVIEW = args.preview === 'yes';
const NO_WRITE = args['no-write'] === 'yes' || (PREVIEW && args['preview-writes'] !== 'yes');
// "Delete my visit data" in the reopened banner (consent.js), and optionally
// a same-origin JSON endpoint of a test or staging store ({ rows: [...] }) to
// see the rows go. Never expose such an endpoint in production.
const DELETE_BUTTON = args['delete-button'] || '[data-consent-delete]';
const ROWS_URL = args['rows-url'] && args['rows-url'] !== 'no' ? args['rows-url'] : '';
// --errors: the site runs k.js with data-errors="on"; check what an error report says.
const ERRORS = args.errors === 'yes';
// --consent-counts: the site counts consent.js's banner events (k.js data-consent-counts="on").
const CONSENT_COUNTS = args['consent-counts'] === 'yes';

// Put into every URL: none of it may leave the page in a report or an event.
const PROBE_EMAIL = 'probe.person@example.com';
// Made up; built from parts so secret scanners do not take it for a real one.
const PROBE_TOKEN = ['prb7f3c9a1e5d2b8f4', 'a6c0e9d1b3a5f7c9e'].join('');
// Parameter names no masking list knows (PostHog masks "email" and "token" by
// itself, which would hide a missing before_send), the usual names too, and a
// campaign tag that carries an address (a link made for one recipient).
const PROBE_QUERY = `?e=${encodeURIComponent(PROBE_EMAIL)}&invite=${PROBE_TOKEN}&email=${encodeURIComponent(PROBE_EMAIL)}&token=${PROBE_TOKEN}` +
  `&utm_source=newsletter&utm_campaign=${encodeURIComponent(PROBE_EMAIL)}`;
// A token-like path segment (nanoid-shaped, a common token format).
// A site that answers 404 there is fine: the check is about what is sent,
// and a 404 page usually runs the tracker too.
const DEFAULT_PATH_TOKEN = ['Pq7xK2mZ9_', 'wR4tY-8sLnB'].join('');
const PATH_PROBE = args['path-probe'] === 'no' ? '' : args['path-probe'] || `${(PAGES[0] || '/').replace(/\/$/, '')}/${DEFAULT_PATH_TOKEN}`;
const PATH_TOKEN = PATH_PROBE ? PATH_PROBE.split('/').filter(Boolean).pop() || '' : '';
const PROBES = [PROBE_EMAIL, encodeURIComponent(PROBE_EMAIL), PROBE_TOKEN, ...(PATH_TOKEN ? [PATH_TOKEN] : [])];
// How long the last page of a run stays open before storage and cookies are
// read: some scripts write late (a consent tool's timer, a lazy widget).
const SETTLE = Math.max(0, Number(args.settle ?? 8000)) || 0;

// Broken things (read-only; they run with --no-write too).
// --expect 'selector@attr=regex' (repeatable; in the config also
// { "selector", "attr", "match", "pages" }): every match on each page has the
// attribute, and it matches.
function parseExpect(e) {
  let x;
  if (e && typeof e === 'object') x = { selector: String(e.selector ?? ''), attr: String(e.attr ?? ''), match: String(e.match ?? ''), pages: e.pages ? csv(Array.isArray(e.pages) ? e.pages.join(',') : e.pages) : null };
  else {
    const m = /^(.+?)@([A-Za-z_:][-\w:.]*)=(.*)$/s.exec(String(e));
    x = m ? { selector: m[1].trim(), attr: m[2], match: m[3], pages: null } : { selector: String(e).trim(), attr: '', match: '', pages: null };
  }
  if (!x.selector) {
    console.error(`--expect: no selector in ${JSON.stringify(e)}`);
    process.exit(2);
  }
  try {
    x.re = new RegExp(x.match);
  } catch (err) {
    console.error(`--expect ${x.selector}: ${err.message}`);
    process.exit(2);
  }
  x.label = x.attr ? `${x.selector}@${x.attr}=${x.match}` : x.selector;
  return x;
}
const EXPECT = (Array.isArray(args.expect) ? args.expect : args.expect ? [args.expect] : []).map(parseExpect);
const INDEXABLE = csv(args.indexable);
const NOINDEX = csv(args.noindex);
const SITEMAP = !args.sitemap || args.sitemap === 'no' ? '' : args.sitemap;
const SITEMAP_HOST = args['sitemap-host'] || new URL(BASE).host;
// Check 13. A processor the browser never talks to (a server-side forward to
// Umami, say) is invisible here: the owner lists it. "Name=host" also covers
// requests to that host (or a subdomain of it).
const PRIVACY_PAGE = args['privacy-page'] || '';
const PROCESSORS = csv(args.processors).map((x) => {
  const [name, host] = x.split('=').map((s) => s.trim());
  return { name, host: (host || '').toLowerCase() };
});
// A path no site has, visited with the probe query: the 404 page's report.
const MISSING = '/sectionsight-check-missing-page';

/**
 * robots.txt, as far as these checks read it: the rules of the groups for
 * "User-agent: *" (not a named crawler's own group), "*" and a final "$" in
 * paths, the longest match wins and Allow wins a tie. No percent-decoding.
 */
function robotsTxt(text) {
  const groups = [];
  const sitemaps = [];
  let cur = null;
  let agentLine = false;
  for (const raw of String(text).split(/\r?\n/)) {
    const m = /^\s*([A-Za-z-]+)\s*:\s*(.*?)\s*$/.exec(raw.replace(/#.*/, ''));
    if (!m) continue;
    const k = m[1].toLowerCase();
    if (k === 'sitemap') sitemaps.push(m[2]);
    else if (k === 'user-agent') {
      if (!agentLine) groups.push((cur = { agents: [], rules: [] }));
      cur.agents.push(m[2].toLowerCase());
      agentLine = true;
      continue;
    } else if (cur && (k === 'allow' || k === 'disallow') && m[2]) cur.rules.push({ allow: k === 'allow', path: m[2] });
    agentLine = false;
  }
  return { rules: groups.filter((g) => g.agents.includes('*')).flatMap((g) => g.rules), sitemaps };
}
/** The Disallow rule that blocks this path, or ''. */
function robotsBlock(rules, path) {
  let best = null;
  for (const r of rules) {
    const re = new RegExp('^' + r.path.replace(/[.+?^${}()|[\]\\]/g, '\\$&').replace(/\*/g, '.*').replace(/\\\$$/, '$'));
    if (re.test(path) && (!best || r.path.length > best.path.length || (r.path.length === best.path.length && r.allow))) best = r;
  }
  return best && !best.allow ? best.path : '';
}
/** The content of <meta name="robots"> and <meta name="googlebot"> in raw HTML. */
function metaRobots(html) {
  const out = [];
  for (const [tag] of String(html).matchAll(/<meta\b[^>]*>/gi)) {
    const name = /\bname\s*=\s*["']?([^"'\s>]+)/i.exec(tag)?.[1]?.toLowerCase();
    if (name !== 'robots' && name !== 'googlebot') continue;
    const c = /\bcontent\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+))/i.exec(tag);
    if (c) out.push(c[1] ?? c[2] ?? c[3]);
  }
  return out.join(', ');
}
const noindexIn = (s) => /(^|[\s,:])(noindex|none)(?=[\s,]|$)/i.test(String(s));
// An X-Robots-Tag value may name a crawler ("otherbot: noindex, nofollow"):
// then its directives are that crawler's only. Those for all crawlers, or for
// Google's and Bing's, count. Directives with a value of their own
// (max-snippet: 20, unavailable_after: …) are not crawler names.
const VALUED = /^(max-snippet|max-image-preview|max-video-preview|unavailable_after|indexifembedded)$/i;
function headerNoindex(value) {
  let agent = '';
  const hits = [];
  for (const part of String(value).split(',')) {
    let d = part.trim();
    const m = /^([A-Za-z0-9_-]+)\s*:\s*(.*)$/.exec(d);
    if (m && !VALUED.test(m[1])) {
      agent = m[1].toLowerCase();
      d = m[2].trim();
    }
    if (/^(noindex|none)$/i.test(d) && (!agent || /^(googlebot|bingbot|robots|\*)$/.test(agent))) hits.push(agent ? `${agent}: ${d}` : d);
  }
  return hits.join(', ');
}
const locsOf = (xml) => [...String(xml).matchAll(/<loc>\s*([^<]+?)\s*<\/loc>/gi)].map((m) => m[1].replace(/&amp;/g, '&'));
function pathOf(u) {
  try {
    const x = new URL(u, BASE);
    return x.pathname + x.search;
  } catch {
    return String(u);
  }
}
function hostOf(u) {
  try {
    return new URL(u).host;
  } catch {
    return '';
  }
}

const THIRD_PARTY = /google-analytics\.com|googletagmanager\.com|doubleclick\.net|facebook\.(com|net)\/tr|connect\.facebook\.net|hotjar\.(com|io)|clarity\.ms|segment\.(io|com)|mixpanel\.com|amplitude\.com|fullstory\.com|mouseflow\.com|smartlook\.com|heap(analytics)?\.(io|com)|linkedin\.com\/px|ads\.linkedin\.com|tiktok\.com\/i18n\/pixel|analytics\.tiktok\.com/i;

// --- Playwright ----------------------------------------------------------------------
async function loadPlaywright() {
  for (const from of [path.join(process.cwd(), 'noop.js'), import.meta.url]) {
    try {
      const resolved = createRequire(from).resolve('playwright');
      return await import(resolved.startsWith('/') ? 'file://' + resolved : resolved);
    } catch {}
  }
  console.error('Playwright is not installed here. Run: npm i -D playwright && npx playwright install chromium');
  process.exit(2);
}
const pw = await loadPlaywright();
const { chromium } = pw.default ?? pw;

// --- Recording ------------------------------------------------------------------------
const results = [];
let K_FORMAT = true;
let consentedState = null;
function check(name, ok, detail = '') {
  results.push({ name, status: ok === null ? 'SKIP' : ok ? 'PASS' : 'FAIL', detail });
}

function expandNested(text, depth = 0) {
  if (depth > 3 || !text || (text[0] !== '{' && text[0] !== '[')) return text;
  let json;
  try {
    json = JSON.parse(text);
  } catch {
    return text;
  }
  const inner = [];
  const walk = (x) => {
    if (typeof x === 'string') {
      if (x.charCodeAt(0) === 0x1f && x.charCodeAt(1) === 0x8b) {
        try {
          inner.push(expandNested(gunzipSync(Buffer.from(x, 'latin1')).toString('utf8'), depth + 1));
        } catch {}
      }
    } else if (Array.isArray(x)) x.forEach(walk);
    else if (x && typeof x === 'object') Object.values(x).forEach(walk);
  };
  walk(json);
  return inner.length ? text + '\n' + inner.join('\n') : text;
}

function decodeBody(req) {
  return expandNested(decodeOuter(req));
}

function decodeOuter(req) {
  let buf = null;
  try {
    buf = req.postDataBuffer();
  } catch {}
  if (!buf) return '';
  const url = req.url();
  try {
    if (/compression=gzip/.test(url) || (buf[0] === 0x1f && buf[1] === 0x8b)) return gunzipSync(buf).toString('utf8');
  } catch {}
  const text = buf.toString('utf8');
  if (/compression=base64/.test(url) || /^data=/.test(text)) {
    try {
      const b64 = decodeURIComponent(text.replace(/^data=/, ''));
      return Buffer.from(b64, 'base64').toString('utf8');
    } catch {}
  }
  return text;
}

function classify(url) {
  let u;
  try {
    u = new URL(url);
  } catch {
    return 'other';
  }
  const own = u.origin === new URL(BASE).origin;
  if (own && u.pathname === COLLECTOR) return 'collector';
  if ((own && POSTHOG && (u.pathname === POSTHOG || u.pathname.startsWith(POSTHOG + '/'))) || /(^|\.)posthog\.com$/.test(u.hostname)) return 'posthog';
  if (THIRD_PARTY.test(url)) return 'third-party';
  return 'other';
}

function record(context, log) {
  const said = new Map(); // url → bodies reported on the console, oldest first
  context.on('console', (msg) => {
    const text = msg.text();
    const MARK = '__sectionsight_body__ ';
    if (!text.startsWith(MARK)) return;
    try {
      const { url, body } = JSON.parse(text.slice(MARK.length));
      if (!said.has(url)) said.set(url, []);
      said.get(url).push(body);
    } catch {}
  });
  context.on('request', (req) => {
    const kind = classify(req.url());
    // The page itself is loaded with the probe in its URL, on purpose.
    if (req.resourceType() === 'document' || /^(data|blob|about|chrome-extension):/.test(req.url())) return;
    let body = req.method() === 'POST' ? decodeBody(req) : '';
    if (req.method() === 'POST' && !body) body = said.get(req.url())?.shift() ?? '';
    let host = '';
    try {
      host = new URL(req.url()).host;
    } catch {}
    if (host) SEEN_HOSTS.add(host.toLowerCase());
    const entry = { kind, host, at: Date.now(), url: req.url(), method: req.method(), body, unread: kind !== 'other' && req.method() === 'POST' && !body, page: req.frame()?.page() ?? null };
    log.push(entry);
    if (kind === 'collector') answered.set(req, entry);
  });
  // The collector's answer: it may take every report and still fail to store
  // it (a skip rule that does not parse answers 500 to everything).
  context.on('response', (res) => {
    const entry = answered.get(res.request());
    if (entry) entry.status = res.status();
  });
}
const answered = new WeakMap();
// Every host any page of this run sent a request to (check 13).
const SEEN_HOSTS = new Set();

// A browser's ordinary user agent: collectors drop "HeadlessChrome" as a bot.
let USER_AGENT = '';
// Uncaught errors and console errors of every page this run opens (check 12).
const PAGE_ERRORS = [];
// silent: reports and PostHog events are answered in the browser even
// without --no-write (the read-only checks of broken things).
async function newContext(browser, { gpc = false, storageState, silent = false, bypassCSP = false } = {}) {
  if (!USER_AGENT) {
    const probe = await browser.newPage();
    USER_AGENT = (await probe.evaluate(() => navigator.userAgent)).replace(/HeadlessChrome/g, 'Chrome');
    await probe.close();
  }
  const context = await browser.newContext({ userAgent: USER_AGENT, extraHTTPHeaders: gpc ? { 'Sec-GPC': '1' } : {}, ...(storageState ? { storageState } : {}), ...(bypassCSP ? { bypassCSP } : {}) });
  context.on('weberror', (e) => { const x = e.error(); PAGE_ERRORS.push(String(x?.stack || x?.message || x)); });
  context.on('console', (m) => { if (m.type() === 'error') PAGE_ERRORS.push(`${m.text()} ${m.location()?.url ?? ''}`); });
  if (NO_WRITE || silent) {
    // Writes are answered here; scripts and remote config still load.
    await context.route((url) => ['collector', 'posthog'].includes(classify(url.toString())), (route) => {
      const req = route.request();
      if (req.method() !== 'POST') return route.continue();
      return classify(req.url()) === 'collector'
        ? route.fulfill({ status: 204, body: '' })
        : route.fulfill({ status: 200, contentType: 'application/json', body: '{"status":1}' });
    });
  }
  // k.js and PostHog stay silent in automated browsers. PostHog looks at
  // navigator.webdriver, the user agent AND navigator.userAgentData.brands.
  await context.addInitScript((g) => {
    Object.defineProperty(Navigator.prototype, 'webdriver', { get: () => false, configurable: true });
    const uad = navigator.userAgentData;
    if (uad) {
      const brands = uad.brands.map((b) => ({ ...b, brand: b.brand.replace(/HeadlessChrome/g, 'Google Chrome') }));
      const fake = {
        brands, mobile: uad.mobile, platform: uad.platform,
        getHighEntropyValues: (hints) => uad.getHighEntropyValues(hints).then((v) => ({ ...v, brands })),
        toJSON: () => ({ brands, mobile: uad.mobile, platform: uad.platform }),
      };
      Object.defineProperty(Navigator.prototype, 'userAgentData', { get: () => fake, configurable: true });
    }
    if (g) Object.defineProperty(Navigator.prototype, 'globalPrivacyControl', { get: () => true, configurable: true });
    // Playwright cannot read a Blob request body. Keep the text of every Blob
    // made from strings, and report beacon and fetch bodies on the console.
    const OrigBlob = window.Blob;
    function TextBlob(parts, opts) {
      const b = new OrigBlob(parts, opts);
      try { Object.defineProperty(b, '__text', { value: (parts || []).map((p) => (typeof p === 'string' ? p : '')).join('') }); } catch {}
      return b;
    }
    TextBlob.prototype = OrigBlob.prototype;
    window.Blob = TextBlob;
    const bodyText = (data) => {
      if (data == null) return '';
      if (typeof data === 'string') return data;
      if (typeof data.__text === 'string') return data.__text;
      if (data instanceof URLSearchParams) return String(data);
      if (data instanceof FormData) return [...data].map(([k, v]) => `${k}=${typeof v === 'string' ? v : ''}`).join('&');
      if (data instanceof ArrayBuffer || ArrayBuffer.isView(data)) { try { return new TextDecoder().decode(data); } catch { return ''; } }
      return '';
    };
    const say = (url, body) => { try { console.debug('__sectionsight_body__ ' + JSON.stringify({ url: String(new URL(url, location.href)), body })); } catch {} };
    const origBeacon = Navigator.prototype.sendBeacon;
    Navigator.prototype.sendBeacon = function (url, data) { say(url, bodyText(data)); return origBeacon.call(this, url, data); };
    const origFetch = window.fetch;
    window.fetch = function (input, init) {
      try { if (init && init.body != null && typeof init.body !== 'string') say(typeof input === 'string' ? input : input.url, bodyText(init.body)); } catch {}
      return origFetch.apply(this, arguments);
    };
  }, gpc);
  return context;
}

// A page closed while on the site sends its last beacon as it unloads, after
// the route that answers it in the browser (--no-write) is gone. Leaving for
// about:blank first sends it while the route still holds.
async function leave(page) {
  if (page.isClosed() || page.url() === 'about:blank') return;
  await page.goto('about:blank').catch(() => {});
  await page.waitForTimeout(300);
}
async function closeContext(context) {
  for (const page of context.pages()) await leave(page);
  await context.close();
}

// Behaves like a reader: moves, scrolls in steps, stays a few seconds.
async function read(page, seconds = 5) {
  const steps = Math.max(1, Math.round(seconds * 2));
  for (let i = 0; i < steps; i++) {
    await page.mouse.move(100 + (i % 5) * 40, 200 + (i % 3) * 30).catch(() => {});
    await page.mouse.wheel(0, 250).catch(() => {});
    await page.waitForTimeout(500);
  }
}

async function hide(page) {
  // What a tab switch does: the tracker reports its time.
  await page.evaluate(() => {
    Object.defineProperty(document, 'visibilityState', { value: 'hidden', configurable: true });
    document.dispatchEvent(new Event('visibilitychange'));
  }).catch(() => {});
  await page.waitForTimeout(300);
  await page.evaluate(() => {
    Object.defineProperty(document, 'visibilityState', { value: 'visible', configurable: true });
    document.dispatchEvent(new Event('visibilitychange'));
  }).catch(() => {});
}

async function storageOf(page) {
  return page.evaluate(async () => {
    const keys = (s) => { try { return Array.from({ length: s.length }, (_, i) => s.key(i)); } catch { return []; } };
    let idb = [];
    try { idb = (await indexedDB.databases()).map((d) => `idb:${d.name}`); } catch {}
    let cache = [];
    try { cache = (await caches.keys()).map((k) => `cache:${k}`); } catch {}
    return { local: keys(localStorage), session: keys(sessionStorage), other: [...idb, ...cache] };
  }).catch(() => ({ local: [], session: [], other: [] }));
}

function parsed(r) {
  try {
    return JSON.parse(r.body);
  } catch {
    return null;
  }
}
const hasProbe = (r) => PROBES.find((p) => r.body.includes(p) || r.url.includes(p));
const short = (s, n = 160) => {
  const t = oneLine(s);
  return t.length > n ? t.slice(0, n) + '…' : t;
};
// What a page sent or contains, made safe to print: one line, and never
// starting with "::" (a GitHub workflow command such as ::error or ::add-mask::).
function oneLine(s) {
  return String(s).replace(/[\r\n\u2028\u2029]+/g, ' ').replace(/^(\s*:)+/, '');
}

// --- Run -----------------------------------------------------------------------------------
const browser = await chromium.launch({
  headless: !HEADED,
  // Chrome tries https:// first for names that are not localhost; a local
  // http server would then time out.
  args: RESOLVE.length
    ? [`--host-resolver-rules=${RESOLVE.map((h) => `MAP ${h} 127.0.0.1`).join(', ')}`, '--disable-features=HttpsUpgrades,HttpsFirstBalancedModeAutoEnable']
    : [],
});
try {
  // 1. Before any answer.
  {
    const log = [];
    const context = await newContext(browser);
    record(context, log);
    const page = await context.newPage();
    let bannerSeen = false;
    const storage = new Set();
    let probeFrom = 0, probeTo = 0;
    for (const p of [...PAGES, ...(PATH_PROBE ? [PATH_PROBE] : [])]) {
      if (p === PATH_PROBE) probeFrom = Date.now();
      await page.goto(BASE + p + PROBE_QUERY, { waitUntil: 'load' });
      if (BANNER && (await page.locator(ACCEPT).first().isVisible().catch(() => false))) bannerSeen = true;
      await read(page);
      await hide(page);
      if (p === PATH_PROBE) probeTo = Date.now() + 300;
      const s = await storageOf(page);
      for (const k of [...s.local, ...s.session, ...s.other]) storage.add(k);
    }
    // Late writers: stay on the last page, then look again.
    await page.waitForTimeout(SETTLE);
    {
      const s = await storageOf(page);
      for (const k of [...s.local, ...s.session, ...s.other]) storage.add(k);
    }
    await page.goto('about:blank');
    await page.waitForTimeout(800);
    const cookies = (await context.cookies()).filter((c) => !ALLOW_COOKIES.includes(c.name));
    const badStorage = [...storage].filter((k) => !ALLOW_STORAGE.includes(k));
    const reports = log.filter((r) => r.kind === 'collector');
    const withIds = reports.filter((r) => { const b = parsed(r); return b && (b.vi !== undefined || (MODE !== 'always' && b.v !== undefined)); });
    const leaked = log.filter(hasProbe);
    const unread = log.filter((r) => r.unread && r.kind === 'collector').length;
    check('before consent: no cookies', cookies.length === 0, cookies.map((c) => c.name).join(', '));
    check('before consent: nothing stored in the browser', badStorage.length === 0, badStorage.join(', '));
    check('before consent: no PostHog request', !log.some((r) => r.kind === 'posthog'), log.filter((r) => r.kind === 'posthog').map((r) => short(r.url)).join(' | '));
    check('before consent: no third-party tracker', !log.some((r) => r.kind === 'third-party'), log.filter((r) => r.kind === 'third-party').map((r) => short(r.url)).join(' | '));
    const ownHost = new URL(BASE).host;
    const others = [...new Set(log.filter((r) => r.host && r.host !== ownHost).map((r) => r.host))].filter((h) => !ALLOW_HOSTS.includes(h));
    check('before consent: no request to another host (or --allow-hosts)', others.length === 0, others.join(', '));
    const failedAnswers = reports.filter((r) => r.status >= 400);
    const okAnswers = reports.filter((r) => r.status >= 200 && r.status < 300);
    check('the collector receives reports', reports.length > 0 && failedAnswers.length === 0,
      !reports.length ? `none at ${COLLECTOR}: is the tracker off on this host (data-hosts, localhost), or not loaded?`
        : failedAnswers.length ? `${failedAnswers.length} of ${reports.length} answered ${[...new Set(failedAnswers.map((r) => r.status))].join(', ')}: the collector fails (a skip rule that does not parse, a store it cannot reach); its logs say why`
        : `${reports.length} reports${okAnswers.length ? `, answered ${[...new Set(okAnswers.map((r) => r.status))].join(', ')}` : ''}`);
    // The id and event checks read k.js's wire format; another tracker's
    // reports are listed for a check by hand instead.
    // k.js's reports: { p, e?, d } where a view has no e and carries d.of.
    // Another tracker may use "p" too; it is not k.js unless its events are.
    const K_EVENTS = new Set(['read', 'time', 'cta', 'ui', 'dead', 'rage', 'copy', 'print', 'goal', 'form', 'nf', 'err', 'consent']);
    const isK = (b) => !!b && typeof b.p === 'string' && !('t' in b) && !('type' in b) && (b.e === undefined ? typeof b.d?.of === 'number' : K_EVENTS.has(b.e));
    K_FORMAT = reports.length > 0 && reports.every((r) => isK(parsed(r)));
    const notK = 'not k.js\'s report format: check by hand: ' + reports.slice(0, 2).map((r) => short(r.body, 120)).join(' | ');
    check(`before consent: reports carry no ids (mode ${MODE})`, MODE === 'always' || !K_FORMAT ? null : withIds.length === 0, K_FORMAT ? withIds.slice(0, 2).map((r) => short(r.body)).join(' | ') : notK);
    check('reports and events never carry the probe e-mail or token', leaked.length ? false : unread ? null : true,
      leaked.length ? leaked.slice(0, 3).map((r) => `${r.kind}: ${short(r.body || r.url)}`).join(' | ') : unread ? `${unread} report bodies could not be read` : '');
    if (PATH_PROBE) {
      const fromProbe = reports.filter((r) => r.at >= probeFrom && r.at <= probeTo);
      const pathLeaks = log.filter((r) => r.body.includes(PATH_TOKEN) || r.url.includes(PATH_TOKEN));
      check(`a token in the path (${PATH_PROBE}) is never sent`, pathLeaks.length ? false : fromProbe.length ? true : null,
        pathLeaks.length ? pathLeaks.slice(0, 2).map((r) => `${r.kind}: ${short(r.body || r.url)}`).join(' | ')
          : fromProbe.length ? `${fromProbe.length} reports from that page` : 'no report from that page (a 404 page without the tracker?): the path rule was not exercised');
    }
    check('the banner is shown', BANNER ? bannerSeen : null, BANNER && !bannerSeen ? `no visible ${ACCEPT}` : '');
    if (BANNER && bannerSeen) {
      // Declining is remembered: asking again on every page pressures people into accepting.
      const declined = await context.newPage();
      await declined.goto(BASE + PAGES[0], { waitUntil: 'load' });
      await declined.locator(DECLINE).first().click().catch(() => {});
      await declined.goto(BASE + (PAGES[1] || PAGES[0]), { waitUntil: 'load' });
      await declined.waitForTimeout(500);
      const again = await declined.locator(ACCEPT).first().isVisible().catch(() => false);
      check('a refusal is remembered (no banner on the next page)', !again, again ? 'the banner came back after Decline' : '');
      await leave(declined);
      await declined.close();
    }
    const kinds = new Set(reports.map((r) => parsed(r)?.e ?? 'view'));
    // Time reports count the sections again when they are sent; a view's
    // count is taken when the route starts, before an SPA may have rendered.
    const times = reports.filter((r) => parsed(r)?.e === 'time');
    const noSections = K_FORMAT && times.length > 0 && times.every((r) => !parsed(r)?.d?.of);
    check('reports include a view, a read and a time report', K_FORMAT ? ['view', 'read', 'time'].every((k) => kinds.has(k)) : null,
      !K_FORMAT ? 'not k.js\'s report format' : [...kinds].join(', ') + (noSections ? ' (no sections found: put the content in <main> with <section>s, or mark them with data-k)' : ''));
    await closeContext(context);
  }

  // 2. Private paths.
  if (PRIVATE.length) {
    const log = [];
    const context = await newContext(browser);
    record(context, log);
    const page = await context.newPage();
    let banner = false;
    for (const p of PRIVATE) {
      await page.goto(BASE + p, { waitUntil: 'load' });
      if (await page.locator(ACCEPT).first().isVisible().catch(() => false)) banner = true;
      await read(page, 2);
      await hide(page);
    }
    await page.goto('about:blank');
    await page.waitForTimeout(500);
    // This browser visits only private paths, so any report at all is one
    // too many (a tracker may report the path as /account/[id]).
    const hits = log.filter((r) => r.kind === 'posthog' || r.kind === 'collector');
    check('private paths: no report and no PostHog request', hits.length === 0, hits.slice(0, 3).map((r) => short(r.body || r.url)).join(' | '));
    check('private paths: no banner', !banner);
    await closeContext(context);
  } else check('private paths', null, 'none given (--private)');

  // 3 and 4. Consent, then withdrawal in another tab.
  if (BANNER) {
    const log = [];
    const context = await newContext(browser);
    record(context, log);
    const page = await context.newPage();
    await page.goto(BASE + PAGES[0] + PROBE_QUERY, { waitUntil: 'load' });
    await page.locator(ACCEPT).first().click();
    const acceptedAt = Date.now();
    for (const p of [...PAGES, ...(PATH_PROBE ? [PATH_PROBE] : [])]) {
      await page.goto(BASE + p + PROBE_QUERY, { waitUntil: 'load' });
      await read(page, 5);
      await hide(page);
    }
    // PostHog's recorder ships its last batch after a while.
    await page.waitForTimeout(1500);
    const after = log.filter((r) => r.at >= acceptedAt);
    consentedState = await context.storageState();
    const reports = after.filter((r) => r.kind === 'collector');
    const withIds = reports.filter((r) => { const b = parsed(r); return b && typeof b.v === 'string'; });
    check('after consent: reports carry ids', MODE === 'consent' && K_FORMAT ? withIds.length > 0 : null,
      !K_FORMAT ? 'not k.js\'s report format: ' + reports.slice(0, 2).map((r) => short(r.body, 120)).join(' | ') : MODE === 'consent' && !withIds.length ? 'no report with vi/v after Accept' : '');
    const ph = after.filter((r) => r.kind === 'posthog' && r.method === 'POST');
    check('after consent: PostHog sends events', POSTHOG ? ph.length > 0 : null, POSTHOG && !ph.length ? `no POST to ${POSTHOG} (loaded but silent? bot detection, before_send, opt-out)` : `${ph.length} POSTs`);
    if (PRIVATE.length) {
      await page.goto('about:blank');
      await page.waitForTimeout(800);
      const from = Date.now();
      for (const p of PRIVATE) {
        await page.goto(BASE + p, { waitUntil: 'load' });
        await read(page, 2);
        await hide(page);
      }
      await page.goto('about:blank');
      await page.waitForTimeout(800);
      const hits = log.filter((r) => r.at >= from && (r.kind === 'posthog' || r.kind === 'collector'));
      check('after consent: private paths still send nothing', hits.length === 0, hits.slice(0, 3).map((r) => `${r.kind}: ${short(r.body || r.url)}`).join(' | '));
    }
    const leaked = log.filter(hasProbe);
    const unread = log.filter((r) => r.unread).length;
    check('after consent: no request carries the probe e-mail or token', leaked.length ? false : unread ? null : true,
      leaked.length ? leaked.slice(0, 3).map((r) => `${r.kind} ${short(r.url, 80)}: ${short(r.body)}`).join(' | ') : unread ? `${unread} request bodies could not be read` : '');

    // Withdrawal: tab A declines, tab B must stop too.
    const tabB = await context.newPage();
    await tabB.goto(BASE + PAGES[0], { waitUntil: 'load' });
    await read(tabB, 2);
    await page.goto(BASE + (SETTINGS_PAGE || PAGES[0]), { waitUntil: 'load' });
    const opener = page.locator(SETTINGS).first();
    // A client-rendered control appears only after hydration.
    await opener.waitFor({ state: 'visible', timeout: 5000 }).catch(() => {});
    if (await opener.count()) {
      await opener.click();
      // A reopened banner is answered with Decline; a control that withdraws
      // by itself (a "Withdraw consent" button) needs no second click.
      const decline = page.locator(DECLINE).first();
      if (await decline.isVisible({ timeout: 1500 }).catch(() => false)) await decline.click();
      const withdrawnAt = Date.now();
      await page.waitForLoadState('load').catch(() => {});
      await page.waitForTimeout(1500);
      await read(tabB, 4);
      await hide(tabB);
      await tabB.mouse.click(5, 5).catch(() => {});
      await tabB.waitForTimeout(2000);
      const late = log.filter((r) => r.at > withdrawnAt + 500);
      const phLate = late.filter((r) => r.kind === 'posthog' && r.method === 'POST');
      check('withdrawal: PostHog sends nothing more, in any tab', POSTHOG ? phLate.length === 0 : null,
        phLate.slice(0, 2).map((r) => `${short(r.url)} (${r.body.length} bytes, ${Math.round((r.at - withdrawnAt) / 100) / 10} s after)`).join(' | '));
      const idsLate = late.filter((r) => r.kind === 'collector' && parsed(r)?.vi !== undefined);
      check('withdrawal: reports carry no visit id, in any tab', MODE === 'consent' && K_FORMAT ? idsLate.length === 0 : null, K_FORMAT ? idsLate.slice(0, 2).map((r) => short(r.body)).join(' | ') : 'not k.js\'s report format');
      // Both tabs: localStorage is shared, sessionStorage is per tab.
      const leftovers = [];
      for (const [name, tab] of [['tab A', page], ['tab B', tabB]]) {
        const s = await storageOf(tab);
        for (const k of [...s.local, ...s.session].filter((k) => /^ph_/.test(k) || k === 'k-visit')) leftovers.push(`${name}: ${k}`);
      }
      check('withdrawal: PostHog and visit storage removed in both tabs (its opt-out flag may stay)', leftovers.length === 0, leftovers.join(', '));
    } else check('withdrawal', false, `no ${SETTINGS} on ${SETTINGS_PAGE || PAGES[0]}: withdrawing must be as easy as consenting`);
    // 5. The banner's counts: totals only, also the Accept and the withdrawal.
    if (CONSENT_COUNTS) {
      await page.waitForTimeout(500);
      const counts = log.filter((r) => r.kind === 'collector' && parsed(r)?.e === 'consent');
      const bad = counts.filter((r) => { const b = parsed(r); return b.vi !== undefined || b.v !== undefined || b.ph !== undefined || b.en !== undefined || hasProbe(r); });
      const kinds = [...new Set(counts.map((r) => parsed(r).d?.k))];
      check('consent counts: totals only, no ids (the Accept too)', bad.length ? false : kinds.includes('accept') ? true : null,
        bad.length ? bad.slice(0, 2).map((r) => short(r.body)).join(' | ') : kinds.includes('accept') ? `${counts.length} reports: ${kinds.join(', ')}` : `no consent report with "accept" reached ${COLLECTOR} (k.js without data-consent-counts="on", or the collector's consentCounts off)`);
    }
    await closeContext(context);
  } else check('consent and withdrawal', null, 'no banner (--banner no)');

  // 6. Global Privacy Control after an earlier Accept, and an expired answer.
  if (consentedState) {
    {
      const log = [];
      const context = await newContext(browser, { gpc: true, storageState: consentedState });
      record(context, log);
      const page = await context.newPage();
      await page.goto(BASE + PAGES[0], { waitUntil: 'load' });
      await read(page, 2);
      await hide(page);
      await page.goto('about:blank');
      await page.waitForTimeout(500);
      const sent = log.filter((r) => r.kind === 'posthog' || (r.kind === 'collector' && (!K_FORMAT || parsed(r)?.vi !== undefined)));
      const posts = sent.filter((r) => r.kind === 'posthog' && r.method === 'POST').length;
      check('GPC after an earlier Accept: no PostHog, no visit ids', sent.length === 0,
        sent.length ? `${sent.length} requests (${posts} PostHog POSTs): ` + sent.slice(0, 2).map((r) => short(r.body || r.url)).join(' | ') : '');
      await closeContext(context);
    }
    const origin = new URL(BASE).origin;
    const ls = consentedState.origins.find((o) => o.origin === origin)?.localStorage ?? [];
    const at = ls.find((e) => e.name === CONSENT_KEY + '-at');
    if (ls.some((e) => e.name === CONSENT_KEY) && at) {
      const old = new Date(Date.now() - 400 * 86_400_000).toISOString();
      const aged = { ...consentedState, origins: consentedState.origins.map((o) => (o.origin !== origin ? o : { ...o, localStorage: o.localStorage.map((e) => (e.name === at.name ? { ...e, value: old } : e)) })) };
      const log = [];
      const context = await newContext(browser, { storageState: aged });
      record(context, log);
      const page = await context.newPage();
      await page.goto(BASE + PAGES[0], { waitUntil: 'load' });
      const asked = await page.locator(ACCEPT).first().isVisible().catch(() => false);
      await read(page, 2);
      await hide(page);
      await page.goto('about:blank');
      await page.waitForTimeout(500);
      const stale = log.filter((r) => r.kind === 'posthog' || (r.kind === 'collector' && K_FORMAT && parsed(r)?.vi !== undefined));
      check('a 400-day-old Accept has expired: asked again, no ids, no PostHog', asked && stale.length === 0,
        !asked ? 'no banner for an expired answer' : stale.slice(0, 2).map((r) => short(r.body || r.url)).join(' | '));
      await closeContext(context);
    } else check('an expired Accept', null, `no ${CONSENT_KEY} / ${CONSENT_KEY}-at in localStorage after Accept (--consent-key)`);
  }

  // 7. "Delete my visit data": only the visit id is sent, and the rows go.
  if (consentedState && MODE === 'consent') {
    const log = [];
    const context = await newContext(browser, { storageState: consentedState });
    record(context, log);
    const page = await context.newPage();
    await page.goto(BASE + PAGES[0] + PROBE_QUERY, { waitUntil: 'load' });
    await read(page, 3);
    await hide(page);
    const vis = new Set(log.filter((r) => r.kind === 'collector').map((r) => parsed(r)?.vi).filter((x) => typeof x === 'string'));
    const opener = page.locator(SETTINGS).first();
    await opener.waitFor({ state: 'visible', timeout: 5000 }).catch(() => {});
    let offered = false;
    if (await opener.count()) {
      await opener.click();
      const button = page.locator(DELETE_BUTTON).first();
      offered = await button.isVisible({ timeout: 1500 }).catch(() => false);
      if (offered) {
        const from = Date.now();
        await button.click();
        await page.waitForLoadState('load').catch(() => {});
        await page.waitForTimeout(1500);
        const dels = log.filter((r) => r.at >= from && r.kind === 'collector' && r.method === 'POST' && /"del"/.test(r.body));
        const bad = [];
        for (const r of dels) {
          const b = parsed(r);
          if (!b || typeof b !== 'object' || Object.keys(b).join() !== 'del') bad.push(`fields: ${short(r.body, 120)}`);
          else if (!vis.has(b.del)) bad.push(`del ${short(String(b.del), 40)} is not this visit's id`);
          if (new URL(r.url).search) bad.push(`a query in the request URL: ${short(r.url, 120)}`);
          if (hasProbe(r)) bad.push('carries the probe');
        }
        const name = 'delete my visit data: the request carries only the visit id';
        if (!vis.size) check(name, null, 'no report with a visit id before the click: nothing to delete');
        else check(name, dels.length > 0 && bad.length === 0, bad.length ? bad.slice(0, 3).join(' | ') : dels.length ? `${dels.length} request${dels.length > 1 ? 's' : ''}` : `no { del } request reached ${COLLECTOR} after the click (k.js deleteMyData missing?)`);
        const after = await page.evaluate(() => window.analyticsConsent?.get?.() ?? null).catch(() => null);
        check('delete my visit data: consent is withdrawn too', after !== 'granted', after === 'granted' ? 'still granted after the click' : '');
        if (ROWS_URL && !NO_WRITE && vis.size) {
          const got = await page.evaluate(async (u) => {
            try {
              const r = await fetch(u, { cache: 'no-store', credentials: 'omit' });
              return { status: r.status, json: await r.json() };
            } catch (e) {
              return { status: 0, error: String(e) };
            }
          }, BASE + ROWS_URL);
          const rows = Array.isArray(got.json?.rows) ? got.json.rows : null;
          const left = rows ? rows.filter((r) => vis.has(r?.visit)).length : 0;
          check('delete my visit data: the visit\'s rows are gone', rows ? left === 0 : null, rows ? (left ? `${left} rows of that visit left` : `${rows.length} rows, none of that visit`) : `${ROWS_URL} answered ${got.status || got.error}, not { rows: [...] }`);
        }
      }
    }
    if (!offered) check('delete my visit data', null, `no ${DELETE_BUTTON} in the reopened banner (the site does not offer it)`);
    await closeContext(context);
  }

  // 8. JavaScript errors (--errors): a same-origin script throws an Error
  // whose message holds the probes. The page's HTML is answered with an
  // inline <script> added (CSP bypassed for this context only): an inline
  // script reports the page's own URL as its file, which k.js sends as
  // "(inline)". Code run by page.evaluate or page.addScriptTag reports no
  // file at all, so k.js would drop it as not the site's own. The err report
  // must arrive scrubbed and without ids, before consent and, after an
  // Accept, still without ids.
  if (ERRORS) {
    for (const [phase, storageState] of [['before consent', undefined], ['after consent', consentedState]]) {
      const name = `errors: an err report, scrubbed, without ids (${phase})`;
      if (phase === 'after consent' && !consentedState) {
        check(name, null, 'no Accept in this run (no banner)');
        continue;
      }
      const log = [];
      const context = await newContext(browser, { storageState, bypassCSP: true });
      record(context, log);
      // After 1.5 s, so k.js (often deferred) listens by then. The message also
      // holds the e-mail percent-escaped and a relative query.
      const script = `<script>setTimeout(function () { Promise.reject(new Error("rejected for ${PROBE_EMAIL} ${PROBE_TOKEN}")); throw new Error("sectionsight-check failed for ${PROBE_EMAIL} with ${PROBE_TOKEN} at " + location.href + " and ${encodeURIComponent(PROBE_EMAIL)} at /account?e=${PROBE_TOKEN}"); }, 1500);</script>`;
      const target = BASE + PAGES[0] + PROBE_QUERY;
      await context.route((u) => u.toString() === target, async (route) => {
        try {
          const res = await route.fetch();
          const html = await res.text();
          const at = /<head\b[^>]*>/i.exec(html);
          const headers = Object.fromEntries(Object.entries(res.headers()).filter(([k]) => !/^(content-length|content-encoding|transfer-encoding)$/i.test(k)));
          await route.fulfill({ status: res.status(), headers, body: at ? html.slice(0, at.index + at[0].length) + script + html.slice(at.index + at[0].length) : script + html });
        } catch {
          await route.continue().catch(() => {});
        }
      });
      const page = await context.newPage();
      const thrownAt = Date.now();
      await page.goto(target, { waitUntil: 'load' });
      await read(page, 1.5);
      await page.waitForTimeout(800);
      await hide(page);
      await leave(page);
      const errs = log.filter((r) => r.at >= thrownAt && r.kind === 'collector' && parsed(r)?.e === 'err');
      const bad = [];
      for (const r of errs) {
        const b = parsed(r);
        if (hasProbe(r)) bad.push(`carries the probe: ${short(r.body)}`);
        if (b.vi !== undefined || b.v !== undefined || b.ph !== undefined) bad.push(`carries ids: ${short(r.body)}`);
        if (/https?:|\?/.test(String(b.d?.m ?? '') + String(b.d?.f ?? ''))) bad.push(`a URL or query in the message or file: ${short(r.body)}`);
      }
      check(name, bad.length ? false : errs.length ? true : null,
        bad.length ? bad.slice(0, 2).join(' | ') : errs.length ? `${errs.length} err report${errs.length > 1 ? 's' : ''}: ${short(errs[0].body, 120)}` : `no err report reached ${COLLECTOR} (k.js without data-errors="on", or an older k.js)`);
      await closeContext(context);
    }
  }

  // 9. Global Privacy Control.
  {
    const log = [];
    const context = await newContext(browser, { gpc: true });
    record(context, log);
    const page = await context.newPage();
    await page.goto(BASE + PAGES[0], { waitUntil: 'load' });
    const banner = await page.locator(ACCEPT).first().isVisible().catch(() => false);
    await read(page, 2);
    await hide(page);
    await page.goto('about:blank');
    await page.waitForTimeout(500);
    const sent = log.filter((r) => r.kind === 'collector' || r.kind === 'posthog');
    check('Global Privacy Control: nothing is sent', sent.length === 0, sent.slice(0, 2).map((r) => short(r.body || r.url)).join(' | '));
    check('Global Privacy Control: no banner', !banner);
    await closeContext(context);
  }

  // 10. The 404 page: with k.js's marker (data-k404) it sends one "nf" report
  // with the path that was asked for, never its query.
  {
    const log = [];
    const context = await newContext(browser);
    record(context, log);
    const page = await context.newPage();
    const res = await page.goto(BASE + MISSING + PROBE_QUERY, { waitUntil: 'load' }).catch(() => null);
    const status = res ? res.status() : 0;
    // A client-rendered 404 page may set the marker after load.
    await page.waitForFunction(() => document.documentElement.hasAttribute('data-k404') || !!document.body?.hasAttribute('data-k404') || window.kConfig?.notFound === true, null, { timeout: 3000 }).catch(() => {});
    const marked = await page.evaluate(() => document.documentElement.hasAttribute('data-k404') || !!document.body?.hasAttribute('data-k404') || window.kConfig?.notFound === true).catch(() => false);
    await read(page, 2);
    await hide(page);
    await leave(page);
    const nf = log.filter((r) => r.kind === 'collector' && parsed(r)?.e === 'nf');
    const soft = status && status !== 404 && status !== 410 ? ` It answered ${status}, not 404: search engines may treat it as a "soft 404".` : '';
    const name = `404 page: an nf report with the path only (${MISSING})`;
    if (!marked) check(name, null, `no data-k404 on <html> or <body> of the 404 page: mark the 404 template to count broken links (references/tracker.md).${soft}`);
    else {
      const bad = nf.filter((r) => hasProbe(r) || parsed(r).p !== MISSING || !['internal', 'external', 'none'].includes(parsed(r).d?.r));
      check(name, nf.length > 0 && bad.length === 0,
        bad.length ? bad.slice(0, 2).map((r) => short(r.body)).join(' | ') : nf.length ? `${nf.length} nf report${nf.length > 1 ? 's' : ''}` : `the page is marked, but no nf report reached ${COLLECTOR} (k.js off on this path, or an older k.js)`);
    }
    // A missing page that answers 200 is a "soft 404": search engines may index
    // it, and hosts that serve the home page for every path hide broken links.
    check('404 page: a missing path answers 404', status ? !soft : null,
      status ? (soft ? soft.trim() + ' Serve the 404 template with status 404 (references/recipes.md).' : `${status}`) : 'the request failed');
    await closeContext(context);
  }

  // 11. Broken things: CTA targets, indexing, the sitemap. Read-only, and run
  // in a context whose reports are answered in the browser, so even without
  // --no-write these visits store nothing.
  if (EXPECT.length || INDEXABLE.length || NOINDEX.length || SITEMAP || PRIVACY_PAGE) {
    const context = await newContext(browser, { silent: true });
    const page = await context.newPage();
    // Same-origin requests from a page of the site: they see every header,
    // and the browser resolves --resolve hosts.
    // follow: follow redirects (the sitemap), and say where it ended.
    const get = (url, method = 'GET', follow = false) =>
      page.evaluate(async ([u, m, f]) => {
        try {
          const r = await fetch(u, { method: m, redirect: f ? 'follow' : 'manual', credentials: 'omit', cache: 'no-store' });
          return { status: r.status, redirected: r.type === 'opaqueredirect' || r.redirected, url: r.url, type: r.headers.get('content-type') || '', text: m === 'GET' ? (await r.text()).slice(0, 5_000_000) : '' };
        } catch (e) {
          return { status: 0, redirected: false, url: '', type: '', text: '', error: String(e) };
        }
      }, [url, method, follow]);

    // CTA targets: every match of the selector, on each page, has the attribute
    // and it matches the pattern.
    if (EXPECT.length) {
      const byPage = new Map();
      for (const x of EXPECT) for (const p of x.pages ?? PAGES) byPage.set(p, [...(byPage.get(p) ?? []), x]);
      const problems = new Map(EXPECT.map((x) => [x, []]));
      const counts = new Map(EXPECT.map((x) => [x, 0]));
      for (const [p, list] of byPage) {
        const res = await page.goto(BASE + p, { waitUntil: 'load' }).catch(() => null);
        if (!res || res.status() >= 400) {
          for (const x of list) problems.get(x).push(`${p}: answered ${res ? res.status() : 'nothing'}`);
          continue;
        }
        for (const x of list) {
          // Client-rendered links appear after hydration.
          await page.waitForSelector(x.selector, { state: 'attached', timeout: 5000 }).catch(() => {});
          const found = await page.evaluate(([sel, attr]) => {
            try {
              return { values: [...document.querySelectorAll(sel)].map((el) => (attr ? el.getAttribute(attr) : '')) };
            } catch (e) {
              return { error: String(e.message || e) };
            }
          }, [x.selector, x.attr]);
          if (found.error) problems.get(x).push(`${p}: not a valid selector (${found.error})`);
          else if (!found.values.length) problems.get(x).push(`${p}: no element matches`);
          else {
            counts.set(x, counts.get(x) + found.values.length);
            for (const v of found.values) {
              if (x.attr && (v === null || !x.re.test(v))) problems.get(x).push(`${p}: ${v === null ? `no ${x.attr}` : `${x.attr}="${short(v, 80)}"`}`);
            }
          }
        }
      }
      for (const x of EXPECT) {
        const bad = problems.get(x);
        check(`expect ${x.label}`, bad.length === 0, bad.length ? bad.slice(0, 4).join(' | ') + (bad.length > 4 ? ` (+${bad.length - 4})` : '') : `${counts.get(x)} match${counts.get(x) === 1 ? '' : 'es'} on ${(x.pages ?? PAGES).join(', ')}`);
      }
    }

    // A page of the site to make the requests from (scripts may run; their
    // reports are answered in the browser).
    await page.goto(BASE + (PAGES[0] || '/'), { waitUntil: 'load' }).catch(() => {});
    const robots = await get(BASE + '/robots.txt');
    const rules = robots.status === 200 ? robotsTxt(robots.text) : { rules: [], sitemaps: [] };
    // Crawlers treat a robots.txt that cannot be fetched (5xx) as "disallow all".
    const robotsDown = robots.status >= 500 || robots.status === 0;

    async function indexState(p) {
      const res = await page.goto(BASE + p, { waitUntil: 'load' }).catch(() => null);
      if (!res) return { status: 0 };
      const chain = [];
      for (let r = res.request().redirectedFrom(); r; r = r.redirectedFrom()) chain.push(r.url());
      const html = await res.text().catch(() => '');
      const header = (await res.allHeaders().catch(() => ({})))['x-robots-tag'] ?? '';
      const rendered = await page.evaluate(() => [...document.querySelectorAll('meta[name]')].filter((m) => /^(robots|googlebot)$/i.test(m.name)).map((m) => m.content).join(', ')).catch(() => '');
      const raw = metaRobots(html);
      const pathname = new URL(BASE + p).pathname;
      return {
        status: res.status(), redirected: chain.length > 0, final: new URL(res.url()).pathname,
        header: headerNoindex(header) ? header : '', raw: noindexIn(raw) ? raw : '', rendered: noindexIn(rendered) ? rendered : '',
        blockedBy: robotsBlock(rules.rules, pathname),
      };
    }
    for (const p of INDEXABLE) {
      const s = await indexState(p);
      const why = [];
      if (s.status !== 200) why.push(`answers ${s.status || 'nothing'}`);
      if (s.redirected) why.push(`redirects to ${s.final} (list the final URL)`);
      if (s.header) why.push(`X-Robots-Tag: ${s.header}`);
      if (s.raw) why.push(`<meta name=robots content="${s.raw}">`);
      else if (s.rendered) why.push(`<meta name=robots content="${s.rendered}"> (added by a script)`);
      if (s.blockedBy) why.push(`robots.txt: Disallow: ${s.blockedBy}`);
      if (robotsDown) why.push(`robots.txt answered ${robots.status || 'nothing'}, which crawlers read as "disallow all"`);
      check(`indexable: ${p}`, why.length === 0, why.length ? why.join('; ') : `200, no noindex, robots.txt ${robots.status === 200 ? 'allows it' : `answers ${robots.status} (no rules)`}`);
    }
    for (const p of NOINDEX) {
      const s = await indexState(p);
      const name = `noindex: ${p}`;
      const tagged = s.header || s.raw || s.rendered;
      if (s.status === 404 || s.status === 410) check(name, null, `answers ${s.status}, so it is not indexed anyway: is the path right?`);
      else if (s.blockedBy && tagged) check(name, false, `robots.txt (Disallow: ${s.blockedBy}) stops crawlers from fetching it, so they never see its noindex; allow crawling it`);
      else if (s.blockedBy) check(name, false, `only robots.txt blocks it (Disallow: ${s.blockedBy}): a blocked URL can still be indexed from links to it; add noindex and allow crawling`);
      else if (!tagged) check(name, false, `answers ${s.status} with no noindex in a <meta name=robots> or an X-Robots-Tag header`);
      else check(name, true, s.header ? `X-Robots-Tag: ${s.header}` : s.raw ? `<meta name=robots content="${s.raw}">` : `<meta name=robots content="${s.rendered}"> added by a script only: put it in the server's HTML or the X-Robots-Tag header to be sure crawlers see it`);
    }

    if (SITEMAP) {
      await page.goto(BASE + (PAGES[0] || '/'), { waitUntil: 'load' }).catch(() => {});
      // --sitemap /path, else robots.txt's Sitemap: line, else /sitemap.xml.
      // A Sitemap: URL on another host (production, seen from a preview) is
      // read from --url at the same path.
      const where = SITEMAP !== 'yes' ? SITEMAP : rules.sitemaps.length ? pathOf(rules.sitemaps[0]) : '/sitemap.xml';
      const name = `sitemap: ${where} lists URLs on ${SITEMAP_HOST} that answer 200`;
      // A redirect to the same site is followed and noted; to another site it fails.
      let sm = await get(BASE + where, 'GET', true);
      let movedNote = '';
      if (sm.redirected && sm.url) {
        if (new URL(sm.url).origin !== new URL(BASE).origin) sm = { ...sm, status: 0, error: `a redirect to another site (${short(sm.url, 80)})` };
        else movedNote = ` (note: ${where} redirects to ${pathOf(sm.url)}; list that URL in robots.txt)`;
      }
      const isXml = (t, type) => /xml/i.test(type) || /^\s*(<\?xml|<urlset|<sitemapindex)/i.test(t);
      if (sm.status !== 200 || !isXml(sm.text, sm.type)) check(name, false, `${where} answered ${sm.error || sm.status || 'nothing'}${sm.status === 200 ? ` with ${sm.type || 'no content type'}, not XML` : ''}`);
      else {
        let locs = locsOf(sm.text);
        const problems = [];
        if (/<sitemapindex/i.test(sm.text)) {
          // An index: read up to five of its sitemaps.
          const children = locs.slice(0, 5);
          locs = [];
          for (const c of children) {
            const child = await get(BASE + pathOf(c));
            if (child.status !== 200 || !isXml(child.text, child.type)) problems.push(`${pathOf(c)}: ${child.status || 'nothing'}`);
            else locs.push(...locsOf(child.text));
          }
        }
        const off = locs.filter((u) => hostOf(u) !== SITEMAP_HOST);
        if (off.length) problems.push(`${off.length} URL${off.length > 1 ? 's' : ''} on another host: ${off.slice(0, 3).map((u) => short(u, 80)).join(', ')}`);
        const on = locs.filter((u) => hostOf(u) === SITEMAP_HOST);
        // Up to 20, spread over the list.
        const sample = on.length <= 20 ? on : Array.from({ length: 20 }, (_, i) => on[Math.floor((i * on.length) / 20)]);
        for (const u of sample) {
          let r = await get(BASE + pathOf(u), 'HEAD');
          if (r.status === 405 || r.status === 501) r = await get(BASE + pathOf(u));
          if (r.status !== 200) problems.push(`${pathOf(u)}: ${r.redirected ? 'redirects' : r.status || 'nothing'}`);
        }
        if (!locs.length) problems.push('no <loc> in it');
        check(name, problems.length === 0, (problems.length ? problems.slice(0, 5).join(' | ') + (problems.length > 5 ? ` (+${problems.length - 5})` : '') : `${locs.length} URLs, ${sample.length} fetched`) + movedNote);
      }
    }

    // 13. The privacy text names who gets data: PostHog, the listed
    // processors, and every other host the pages sent a request to (a host is
    // named by its domain's own label: eu.i.posthog.com → "posthog").
    if (PRIVACY_PAGE) {
      const name = `privacy page ${PRIVACY_PAGE} names every recipient`;
      const res = await page.goto(BASE + PRIVACY_PAGE, { waitUntil: 'load' }).catch(() => null);
      if (!res || res.status() >= 400) check(name, false, `${PRIVACY_PAGE} answered ${res ? res.status() : 'nothing'}`);
      else {
        const text = (await page.evaluate(() => document.body?.innerText ?? '').catch(() => '')).toLowerCase();
        const own = new URL(BASE).host.toLowerCase();
        const covered = (h) => PROCESSORS.some((x) => x.host && (h === x.host || h.endsWith('.' + x.host)));
        const label = (h) => {
          const parts = h.replace(/:\d+$/, '').split('.');
          // example.co.uk → "example"
          const i = parts.length >= 3 && parts.at(-1).length === 2 && parts.at(-2).length <= 3 ? parts.length - 3 : parts.length - 2;
          return parts[Math.max(0, i)];
        };
        const wanted = [
          ...(POSTHOG ? [{ name: 'PostHog', why: '--posthog' }] : []),
          ...PROCESSORS.map((x) => ({ name: x.name, why: '--processors' })),
          ...[...SEEN_HOSTS].filter((h) => h !== own && !covered(h) && !/(^|\.)posthog\.com$/.test(h) && !RESOLVE.includes(h.replace(/:\d+$/, '')))
            .map((h) => ({ name: label(h), why: `requests to ${h}` })),
        ];
        const seen = new Set();
        const missing = wanted.filter((w) => w.name && !seen.has(w.name.toLowerCase()) && seen.add(w.name.toLowerCase()) && !text.includes(w.name.toLowerCase()));
        check(name, missing.length === 0, missing.length
          ? `not named: ${missing.map((m) => `${m.name} (${m.why})`).join(', ')}. Name each recipient and what it receives (references/privacy-policy.md), or cover a host with --processors "Name=host"`
          : seen.size ? `names ${[...seen].join(', ')}` : 'no recipient besides the site itself');
      }
    }
    await closeContext(context);
  }
} finally {
  await browser.close();
}

// 12. The scripts this skill adds break nothing: no uncaught error or CSP
// violation from them (a <style> under style-src 'self' leaves the banner
// unstyled), and no hydration error (a node put into a framework's <body>
// before it hydrates). Other console errors are the site's own and only
// counted.
{
  const OURS = /\/(k|consent)(\.min)?\.js\b|posthog-guard|analyticsConsent/;
  const HYDRATION = /hydrat|Minified React error #(418|423|425)\b/i;
  const mine = PAGE_ERRORS.filter((m) => !/sectionsight-check failed|rejected for /.test(m) && (OURS.test(m) || HYDRATION.test(m)));
  const others = PAGE_ERRORS.length - PAGE_ERRORS.filter((m) => /sectionsight-check failed|rejected for /.test(m)).length - mine.length;
  check('no hydration error, CSP violation or error from the analytics scripts', mine.length === 0,
    mine.length ? [...new Set(mine.map((m) => short(m, 160)))].slice(0, 3).join(' | ') : others ? `${others} other console error${others > 1 ? 's' : ''} (the site's own, not judged)` : '');
}

// --- Report ----------------------------------------------------------------------------
const failed = results.filter((r) => r.status === 'FAIL');
const skipped = results.filter((r) => r.status === 'SKIP');
const passedAll = failed.length === 0 && !(FAIL_ON_SKIP && skipped.length);
// Details quote pages and headers: one line each, never a workflow command,
// and with --github the whole listing between ::stop-commands:: markers.
const resume = GITHUB ? randomBytes(16).toString('hex') : '';
if (GITHUB) console.log(`::stop-commands::${resume}`);
for (const r of results) console.log(`${r.status.padEnd(4)}  ${oneLine(r.name)}${r.detail ? `\n      ${oneLine(r.detail)}` : ''}`);
if (GITHUB) console.log(`::${resume}::`);
console.log(`\n${failed.length ? `FAILED: ${failed.length} of ${results.length}` : FAIL_ON_SKIP && skipped.length ? `FAILED: ${skipped.length} skipped (--fail-on-skip)` : 'PASSED'} (${results.filter((r) => r.status === 'PASS').length} passed, ${skipped.length} skipped)`);
writeFileSync(REPORT, JSON.stringify({ passed: passedAll, url: BASE, mode: MODE, noWrite: NO_WRITE, failOnSkip: FAIL_ON_SKIP, results }, null, 2));
if (GITHUB) {
  // Markdown table cells: backslashes first, then pipes, backticks and tags.
  const cell = (s) => String(s).replace(/\s+/g, ' ').slice(0, 240).replace(/\\/g, '\\\\').replace(/\|/g, '\\|').replace(/`/g, '\\`').replace(/</g, '&lt;');
  const md = [
    `### Privacy check: ${passedAll ? 'passed' : 'FAILED'}`,
    '',
    `${cell(BASE)} · mode ${MODE}${NO_WRITE ? ' · --no-write' : ''} · ${results.length - failed.length - skipped.length} passed, ${failed.length} failed, ${skipped.length} skipped`,
    '',
    '| Check | Result | Detail |',
    '|---|---|---|',
    ...results.map((r) => `| ${cell(r.name)} | ${r.status === 'PASS' ? 'PASS' : r.status === 'FAIL' ? '**FAIL**' : 'SKIP'} | ${cell(r.detail)} |`),
    '',
  ].join('\n');
  if (process.env.GITHUB_STEP_SUMMARY) appendFileSync(process.env.GITHUB_STEP_SUMMARY, md + '\n');
  // Workflow commands: one annotation per failure (and per skip with --fail-on-skip).
  const esc = (s) => String(s).replace(/%/g, '%25').replace(/\r/g, '%0D').replace(/\n/g, '%0A');
  for (const r of [...failed, ...(FAIL_ON_SKIP ? skipped : [])]) console.log(`::error title=Privacy check::${esc(`${r.status} ${r.name}${r.detail ? `: ${r.detail}` : ''}`)}`);
}
process.exit(passedAll ? 0 : 1);
