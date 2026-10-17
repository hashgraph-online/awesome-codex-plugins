/**
 * The collector for k.js: one POST endpoint that checks every report, cuts it
 * down to what the totals and rows use, and stores it. Reference
 * implementation from the sectionsight skill (MIT).
 *
 * Runtime: any Fetch API server (Next.js route handlers, Cloudflare Workers
 * and Pages Functions, Deno, Bun, Hono). For Node's http/Express, wrap it
 * with toNodeHandler below. No dependencies.
 *
 *   import { createCollector, memoryStore } from './collector.mjs';
 *   const collect = createCollector({ hosts: ['example.com'], store: memoryStore() });
 *   export const POST = (req) => collect(req);
 *
 * What it keeps from the request: the country the CDN resolved (a header,
 * never an IP lookup of our own) and a device class from the user agent. It
 * never stores the IP address or the user agent. The IP is used only in
 * memory, to throttle a flood, and in "always" mode, hashed with the date and
 * a secret, to tell one day's visitors apart.
 *
 * Every answer is 204 with no body: the browser never waits for it, and a
 * broken or hostile client learns nothing. The same endpoint takes a
 * visitor's own deletion request, { "del": <visit id> } (references/collector.md).
 * Because a 204 hides failures, the collector keeps a health record off the
 * hot path (collect.health(), store.health(); references/alerts.md).
 */

/** Largest report accepted, in bytes. A real one is under 600. */
export const MAX_BYTES = 4096;
export const EVENTS = ['view', 'read', 'time', 'cta', 'ui', 'dead', 'rage', 'copy', 'print', 'goal', 'form', 'nf', 'err', 'consent'];
/** What consent.js reports when the owner counts the banner's answers (k.js data-consent-counts). */
export const CONSENT_EVENTS = ['shown', 'accept', 'decline', 'withdraw'];
export const DEPTHS = [25, 50, 75, 100];
export const HIST = [0, 5, 10, 20, 30, 60, 120, 300, 600];
/**
 * Core Web Vitals buckets (lower edges; ms, CLS unitless), the same as k.js
 * (a test checks). `poor` is the first bucket that is "poor" by the web.dev
 * thresholds (LCP > 4 s, CLS > 0.25, INP > 500 ms, TTFB > 1.8 s), `good` the
 * first that is no longer good (2.5 s, 0.1, 200 ms, 800 ms). A bucket's lower
 * edge belongs to it, so a value exactly on a threshold counts one bucket up.
 */
export const CWV_BUCKETS = {
  lcp: { edges: [0, 1000, 1800, 2500, 3000, 4000, 6000], good: 3, poor: 5 },
  cls: { edges: [0, 0.05, 0.1, 0.15, 0.25], good: 2, poor: 4 },
  inp: { edges: [0, 100, 200, 350, 500, 1000], good: 2, poor: 4 },
  ttfb: { edges: [0, 200, 500, 800, 1800], good: 3, poor: 4 },
};
const BUILT_IN_LINKS = ['email', 'phone', 'download', 'nav', 'outbound'];

// Requests that are not a person reading the page. "moto g power (2022)" is
// the device Lighthouse emulates; its user agent does not say Lighthouse.
const BOT =
  /bot\b|bot\/|crawl|spider|slurp|headless|lighthouse|moto g power \(2022\)|preview|prerender|python|curl\/|wget|httpclient|axios|node-fetch|go-http|okhttp|java\/|facebookexternalhit|embedly|pingdom|uptime|statuscake/i;

// The country header the CDN or host sets, first found wins.
const COUNTRY_HEADERS = ['cf-ipcountry', 'x-vercel-ip-country', 'cloudfront-viewer-country', 'x-country-code'];

// Referrer host → a source name people recognise. Unknown hosts stay a site.
// AI assistants keep a key each (chatgpt, perplexity…); AI_SOURCES groups
// them, and sourceClass() turns any source into a coarse class. Order
// matters: gemini.google.com before Google.
const SOURCES = [
  [/(^|\.)gemini\.google\.com$|(^|\.)bard\.google\.com$/, 'gemini'],
  [/(^|\.)google\.[a-z.]+$/, 'google'],
  [/^copilot\.microsoft\.com$|(^|\.)copilot\.cloud\.microsoft$/, 'copilot'],
  [/(^|\.)bing\.com$/, 'bing'],
  [/(^|\.)duckduckgo\.com$/, 'duckduckgo'],
  [/(^|\.)yahoo\.com$/, 'yahoo'],
  [/(^|\.)yandex\.[a-z]+$/, 'yandex'],
  [/(^|\.)seznam\.cz$/, 'seznam'],
  [/(^|\.)linkedin\.com$|^lnkd\.in$/, 'linkedin'],
  [/(^|\.)facebook\.com$|^fb\.me$/, 'facebook'],
  [/(^|\.)instagram\.com$/, 'instagram'],
  [/^t\.co$|(^|\.)x\.com$|(^|\.)twitter\.com$/, 'x'],
  [/(^|\.)chatgpt\.com$|(^|\.)openai\.com$/, 'chatgpt'],
  [/(^|\.)perplexity\.(ai|com)$|^pplx\.ai$/, 'perplexity'],
  [/(^|\.)claude\.(ai|com)$/, 'claude'],
  [/^chat\.deepseek\.com$|(^|\.)deepseek\.com$/, 'deepseek'],
  [/(^|\.)grok\.com$/, 'grok'],
  [/(^|\.)meta\.ai$/, 'meta-ai'],
  [/^chat\.mistral\.ai$|(^|\.)mistral\.ai$/, 'mistral'],
  [/(^|\.)you\.com$/, 'you'],
  [/(^|\.)github\.com$/, 'github'],
  [/(^|\.)producthunt\.com$/, 'producthunt'],
  [/(^|\.)news\.ycombinator\.com$/, 'hackernews'],
  [/(^|\.)youtube\.com$|^youtu\.be$/, 'youtube'],
  [/(^|\.)reddit\.com$/, 'reddit'],
  [/(^|\.)whatsapp\.com$|^wa\.me$/, 'whatsapp'],
  [/(^|\.)slack\.com$/, 'slack'],
];
// android-app://<package> referrers: the app, by name where it is known.
const APPS = {
  'com.google.android.gm': 'gmail',
  'com.google.android.googlequicksearchbox': 'google',
  'com.linkedin.android': 'linkedin',
  'com.whatsapp': 'whatsapp',
  'com.slack': 'slack',
  'org.telegram.messenger': 'telegram',
  'com.facebook.katana': 'facebook',
  'com.instagram.android': 'instagram',
  'com.openai.chatgpt': 'chatgpt',
  'com.anthropic.claude': 'claude',
  'ai.perplexity.app.android': 'perplexity',
  'com.google.android.apps.bard': 'gemini',
  'com.deepseek.chat': 'deepseek',
};
// utm_source values that may become a source. Any other value never does: a
// link built for one recipient can carry a value that points at that person.
// ChatGPT adds utm_source=chatgpt.com to the links it cites (OpenAI's
// publishers FAQ; references/ai-visibility.md).
const UTM_SOURCES = {
  linkedin: 'linkedin', li: 'linkedin', google: 'google', facebook: 'facebook', fb: 'facebook',
  instagram: 'instagram', ig: 'instagram', x: 'x', twitter: 'x', newsletter: 'newsletter',
  email: 'email', mail: 'email', qr: 'qr', whatsapp: 'whatsapp', wa: 'whatsapp', slack: 'slack',
  github: 'github', producthunt: 'producthunt', reddit: 'reddit', youtube: 'youtube',
  tiktok: 'tiktok', hackernews: 'hackernews', hn: 'hackernews',
  'chatgpt.com': 'chatgpt', chatgpt: 'chatgpt', openai: 'chatgpt', 'perplexity.ai': 'perplexity', perplexity: 'perplexity',
  'claude.ai': 'claude', claude: 'claude', gemini: 'gemini', copilot: 'copilot', 'copilot.com': 'copilot',
  'grok.com': 'grok', grok: 'grok', deepseek: 'deepseek', 'meta.ai': 'meta-ai', mistral: 'mistral', 'you.com': 'you',
};
/** The AI assistants among the sources ("AI assistants" in the weekly digest). */
export const AI_SOURCES = ['chatgpt', 'perplexity', 'claude', 'gemini', 'copilot', 'deepseek', 'grok', 'meta-ai', 'mistral', 'you'];
const SOCIAL = ['linkedin', 'facebook', 'instagram', 'x', 'reddit', 'youtube', 'tiktok', 'hackernews', 'producthunt', 'whatsapp', 'slack', 'telegram'];
const SEARCH = ['duckduckgo', 'yahoo', 'yandex', 'seznam'];
/** The coarse classes of sourceClass(), the only values a goal's source can take in the totals. */
export const SOURCE_CLASSES = ['google', 'bing', 'search', 'ai', 'social', 'newsletter', 'direct', 'other'];
/** A source (sourceOf, or a known utm_source) as one of SOURCE_CLASSES. */
export function sourceClass(source) {
  if (source === 'google' || source === 'bing' || source === 'direct') return source;
  if (AI_SOURCES.includes(source)) return 'ai';
  if (SOCIAL.includes(source)) return 'social';
  if (SEARCH.includes(source)) return 'search';
  if (source === 'newsletter' || source === 'email' || source === 'gmail') return 'newsletter';
  return 'other';
}

/**
 * Text that may be a person or a credential: an e-mail, a phone or account
 * number (9+ digits once spaces and dashes are gone; a date has 8), a hex id,
 * or a token (a JWT, a nanoid, a random code). The same rule as k.js and
 * posthog-guard.mjs (a test checks that all three agree). A name slug ("jane-doe")
 * or a code under 10 characters reads like any other slug: only the
 * private-path rule keeps such pages out.
 */
export function looksPersonal(s) {
  s = String(s);
  if (/[@\uff20]/.test(s) || /\d{9,}/.test(s.replace(/[\s().+-]/g, '')) ||
    /[a-z0-9]{24,}/i.test(s) || /[0-9a-f]{12,}/i.test(s.replace(/[-_]/g, ''))) return true;
  var words = s.split(/[^A-Za-z0-9_-]+/);
  for (var i = 0; i < words.length; i++) if (tokenLike(words[i])) return true;
  return false;
}
function tokenLike(w) {
  if (w.length < 10) return false;
  if (/^eyJ/.test(w)) return true;
  // A slug: every part between - and _ is a word, a number, "v2", one
  // "h264"/"1080p"/"covid19" among words, or CamelCase words ("iPhone15Pro").
  var parts = w.split(/[-_]/), mixed = 0, cam = 0;
  var slug = parts.every(function (p) {
    if (/^([A-Z]?[a-z]{2,}|[a-z]|\d+|v\d+|[A-Z]{5,12})$/.test(p)) return true;
    if (parts.length > 1 && /^(\d+[a-z]{1,3}|[a-z]{1,8}\d{1,4})$/.test(p)) return ++mixed < 2;
    return camelWords(p) && ++cam > 0;
  });
  // CamelCase counts as words only beside a real lowercase word.
  if (slug && (!cam || /[a-z]{3,}/.test(w))) return false;
  var upper = /[A-Z]/.test(w), lower = /[a-z]/.test(w), digit = /\d/.test(w);
  if (digit && (upper || lower)) return true;
  if (!lower) return upper && w.length >= 16;
  return upper && (w.length >= 16 || (w.match(/[A-Z]/g) || []).length * 3 >= (w.match(/[A-Za-z]/g) || []).length);
}
// Words, acronyms and model numbers run together ("EC2Instances"), with at
// most two numbers, and words that have vowels (random letters often do not).
function camelWords(p) {
  return /^[a-z]*([A-Z][a-z]{2,}|[A-Z]{2,4}(?![a-z])|[A-Z]\d{1,4}|\d{1,4})+$/.test(p) &&
    (p.match(/\d+/g) || []).length <= 2 &&
    (p.match(/[a-z]{2,}/g) || []).every(function (r) { return /[aeiouy]/.test(r); });
}

// <scrubError> (the same in k.js; a test checks)
// An error message as it may be reported, in linear time. Decoded first
// (percent-escapes, also UTF-8 runs and twice-encoded ones, %u0040, &#64;,
// the full-width and small at signs), then quoted text emptied (an
// unterminated quote to the end), then word by word: data: URLs <data>,
// URLs, localhost and IP hosts, host.tld/… and anything with ?…= (also
// #, ; and & before the =) <url>, anything with an @ <email>, anything
// with / or \ <path> (a stack frame keeps its .js file name and line),
// token-like words <id>; digits made 0, one line. The browser's "Uncaught "
// and Firefox's "uncaught exception: " are dropped.
export function scrubError(s) {
  function dec(r) {
    try { return decodeURIComponent(r); } catch (e) {
      return r.replace(/%[0-9a-f]{2}/gi, function (x) { try { return decodeURIComponent(x); } catch (e2) { return x; } });
    }
  }
  s = String(s == null ? '' : s).slice(0, 1000).replace(/^\s*uncaught(?:\s+exception)?(?::|\s)\s*/i, '')
    .replace(/%u([0-9a-f]{4})/gi, function (x, h) { return String.fromCharCode(parseInt(h, 16)); })
    .replace(/(?:%[0-9a-f]{2})+/gi, dec).replace(/(?:%[0-9a-f]{2})+/gi, dec)
    .replace(/&#(?:0*64|x0*40);|&commat;/gi, '@').replace(/[\uff20\ufe6b]/g, '@')
    .replace(/[\u0000-\u001f\u007f\u2028\u2029]+/g, ' ')
    .replace(/["'`]@["'`]/g, '@').replace(/ ?(?:@|\(at\)|\[at\]) ?/gi, '@')
    .replace(/"(?:[^"\\]|\\.)*(?:"|$)/g, '""').replace(/`(?:[^`\\]|\\.)*(?:`|$)/g, '``')
    .replace(/(^|[^A-Za-z])'(?:[^'\\]|\\.)*(?:'|$)/g, "$1''")
    .replace(/[\u201c\u201e\u00ab][^\u201c\u201d\u00bb]*(?:[\u201c\u201d\u00bb]|$)/g, '""').replace(/\u2018[^\u2019]*(?:\u2019|$)/g, "''")
    .replace(/\S+/g, function (t) {
      var lead = /^[(\[{"'`]*/.exec(t)[0], r = t.slice(lead.length), q = r.search(/[?#;&]/), sl = r.search(/[\/\\]/), f;
      if (/^data:/i.test(r)) return lead + '<data>';
      if (/^[a-z][a-z0-9+.-]*:\/\//i.test(r) || /^[(\[{"'`]*(?:localhost|\d{1,3}(?:\.\d{1,3}){3}|\[[0-9a-f:.]*\])(?::\d+)?(?:[\/?#]|$)/i.test(t)) return lead.replace(/\[$/, '') + '<url>';
      if (r.indexOf('@') >= 0) return lead + '<email>';
      if (q >= 0 && r.indexOf('=', q) > q) return lead + '<url>';
      if (sl > 0 && /\.[^.\d:]{2,}(?::\d+)?$/.test(r.slice(0, sl)) && r.charAt(sl) === '/') return lead + '<url>';
      if (sl < 0) return t;
      // A stack frame's file: its name and position, never its directories.
      f = /[\/\\]([\w.-]+\.[mc]?[jt]sx?)(:\d+(?::\d+)?\)?)?$/.exec(r);
      return lead + '<path>' + (f && f[2] && !looksPersonal(f[1]) ? '/' + f[1] + f[2] : '');
    })
    .replace(/[^\s"'`()[\]{}<>,;:=]+/g, function (x) { return looksPersonal(x) ? '<id>' : x; });
  return s.replace(/\d+/g, '0').replace(/\s+/g, ' ').trim().slice(0, 160);
}
// </scrubError>

/** An error's file as k.js reports it ("app-*.js", "(inline)", "(hidden)"), checked again; '' if it is not one. */
export function errFile(v) {
  if (v === '(inline)' || v === '(hidden)') return v;
  if (typeof v !== 'string' || !/^[A-Za-z0-9._~*()-]{1,60}$/.test(v) || !/\.[mc]?[jt]sx?$/i.test(v)) return '';
  // Token-like parts and build hashes (letters and digits mixed, 6+) as *, as k.js does.
  return v.replace(/[A-Za-z0-9]+/g, (x) => (looksPersonal(x) || (x.length >= 6 && /\d/.test(x) && /[A-Za-z]/.test(x)) ? '*' : x));
}

/** An error's fingerprint: 8 hex characters (FNV-1a) of the scrubbed message, the file and the line. */
export function errFingerprint(m, f, l) {
  let h = 0x811c9dc5;
  const s = `${m}|${f}|${l}`;
  for (let i = 0; i < s.length; i++) h = Math.imul(h ^ s.charCodeAt(i), 0x01000193) >>> 0;
  return h.toString(16).padStart(8, '0');
}

/**
 * The 75th percentile from bucket counts ({ "<bucket>": n } or an array), as
 * the bucket it falls in: { bucket, from, to, rating, n } (to is Infinity for
 * the last bucket; rating 'good' | 'needs-improvement' | 'poor'), or null
 * without counts. `metric` is a key of CWV_BUCKETS, or pass `edges` for others.
 */
export function p75FromBuckets(counts, metric, edges) {
  const spec = CWV_BUCKETS[metric];
  const e = edges ?? spec?.edges;
  if (!e) throw new Error(`p75FromBuckets: unknown metric ${metric}`);
  const at = (i) => Math.max(0, Number(Array.isArray(counts) ? counts[i] : counts?.[i]) || 0);
  let n = 0;
  for (let i = 0; i < e.length; i++) n += at(i);
  if (!n) return null;
  let seen = 0;
  for (let i = 0; i < e.length; i++) {
    seen += at(i);
    if (seen >= 0.75 * n) {
      const rating = !spec ? undefined : i >= spec.poor ? 'poor' : i >= spec.good ? 'needs-improvement' : 'good';
      return { bucket: i, from: e[i], to: i + 1 < e.length ? e[i + 1] : Infinity, rating, n };
    }
  }
  return null;
}

export function deviceOf(ua) {
  if (/iPad|Tablet|PlayBook|Silk|Android(?!.*Mobi)/i.test(ua)) return 'tablet';
  if (/Mobi|iPhone|iPod|Android/i.test(ua)) return 'mobile';
  return 'desktop';
}

/**
 * Who sent the request, as far as the totals need, or null when it must not
 * be counted: Global Privacy Control, Do Not Track, a bot, no user agent.
 */
export function visitorOf(headers, cf) {
  if (headers.get('sec-gpc') === '1' || headers.get('dnt') === '1') return null;
  const ua = headers.get('user-agent') ?? '';
  if (!ua || BOT.test(ua)) return null;
  // Cloudflare Workers and Pages give request.cf.country without any header.
  let cc = typeof cf?.country === 'string' ? cf.country.toLowerCase() : '';
  for (const h of COUNTRY_HEADERS) {
    if (cc) break;
    cc = (headers.get(h) ?? '').toLowerCase();
  }
  return { country: /^[a-z]{2}$/.test(cc) && cc !== 'xx' && cc !== 't1' ? cc : 'xx', device: deviceOf(ua) };
}

/**
 * An unknown referrer reduced to its site: the last two labels, three under a
 * second-level suffix. A subdomain can name a person or a customer
 * ("jane-doe.github.io", "acme.sharepoint.com"); the platform is enough.
 */
export function siteOf(host) {
  if (/^[\d.]+$|:/.test(host)) return 'ip';
  const labels = host.split('.').filter(Boolean);
  const keep = labels.length > 2 && /^(co|com|org|net|ac|gov|edu)$/.test(labels[labels.length - 2]) ? 3 : 2;
  return labels.slice(-keep).join('.').slice(0, 60) || 'other';
}

export function sourceOf(refHost, ownHosts) {
  const h = String(refHost || '').toLowerCase().replace(/^www\./, '');
  if (!h) return 'direct';
  if (ownHosts.some((o) => h === o.replace(/^www\./, '') || h.endsWith('.' + o.replace(/^www\./, '')))) return 'internal';
  // An app package reads like a reversed domain ("com.google.android.gm").
  if (Object.hasOwn(APPS, h)) return APPS[h];
  if (/^(com|org|net|io)\.[a-z0-9_.]+$/.test(h)) return 'app';
  for (const [re, name] of SOURCES) if (re.test(h)) return name;
  return siteOf(h);
}

// --- Parsing ------------------------------------------------------------------

const PATH = /^\/[A-Za-z0-9\-._~%/[\]]{0,120}$/;

function int(v, min, max) {
  if (typeof v !== 'number' || !Number.isInteger(v)) return undefined;
  return Math.min(max, Math.max(min, v));
}
/** A section key as k.js makes it ("" = no section, or one that may name someone). */
function key(v) {
  return typeof v === 'string' && /^[a-z0-9][a-z0-9-]{0,23}$/.test(v) && !looksPersonal(v) ? v : '';
}
function text(v, max) {
  return typeof v === 'string' ? v.replace(/[\u0000-\u001f\u007f]/g, ' ').replace(/\s+/g, ' ').trim().slice(0, max) : '';
}
/** A dead/rage click label ("h2:How it works"), cut to its tag when it may name someone. */
function clickLabel(v) {
  const t = text(v, 40);
  return looksPersonal(t) ? t.split(':')[0] : t;
}
/** A utm value as a short token, or nothing when it may name or identify someone. */
function token(v, max) {
  if (typeof v !== 'string' || looksPersonal(v)) return undefined;
  const t = v.toLowerCase().replace(/[^a-z0-9._-]+/g, '-').replace(/^-+|-+$/g, '').slice(0, max);
  return t || undefined;
}

/**
 * Parses one report. Returns { path, event, data, entry?, entryRepeat?, ids? }
 * or null. `ctx`: { ownHosts, skip (RegExp[]), ids ('never'|'consent'|'always'), campaignTotals?,
 * campaigns? (a Set of allowlisted campaign names, as field() writes them), consentCounts? }.
 */
export function parseBeacon(body, ctx) {
  if (!body || body.length > MAX_BYTES) return null;
  let o;
  try {
    o = JSON.parse(body);
  } catch {
    return null;
  }
  if (!o || typeof o !== 'object' || Array.isArray(o)) return null;

  const path = pagePath(o.p, ctx.skip);
  if (!path) return null;
  // A 404 path is whatever a visitor or a bot typed or followed: the whole
  // path is checked once more before it can become a counter's name.
  if (o.e === 'nf' && looksPersonal(path.replace(/\[id\]/g, ''))) return null;
  // A page view has no name on the wire.
  const event = o.e === undefined ? 'view' : EVENTS.includes(o.e) && o.e !== 'view' ? o.e : null;
  if (!event) return null;
  const d = o.d && typeof o.d === 'object' && !Array.isArray(o.d) ? o.d : {};
  const data = DATA[event](d, ctx);
  if (!data) return null;

  const beacon = { path, event, data };
  // Core Web Vitals ride on a time report, but are totals only: never in a row.
  if (event === 'time' && data.cv) {
    beacon.cv = data.cv;
    delete data.cv;
  }
  // An error report, and a consent count, are totals only, in every mode and after consent too.
  if (event === 'err') return beacon;
  if (event === 'consent') return ctx.consentCounts ? beacon : null;
  // A goal carries the entry of its page load (k.js resends the referrer host
  // and utm_source it sent with the visit's first view): only its class is kept.
  if (event === 'goal' && typeof o.gr === 'string') {
    const ref = /^[A-Za-z0-9.-]{0,253}$/.test(o.gr) ? o.gr : '';
    const refSource = sourceOf(ref, ctx.ownHosts);
    const u = ctx.campaignTotals === false ? undefined : token(o.gu, 40);
    const src = (u && UTM_SOURCES[u]) || refSource;
    // A goal on a page load that continued a visit has no entry: no class.
    if (src !== 'internal') beacon.goalSource = sourceClass(src);
  }
  if ((event === 'view' && o.en === 1) || o.en === 2) {
    const u = o.u && typeof o.u === 'object' && !Array.isArray(o.u) ? o.u : {};
    const utm = {};
    for (const k of ['source', 'medium', 'campaign']) {
      const t = token(u[k], 40);
      if (t) utm[k] = t;
    }
    const ref = typeof o.r === 'string' && /^[A-Za-z0-9.-]{1,253}$/.test(o.r) ? o.r : '';
    const lang = typeof o.l === 'string' ? (/^[a-z]{2,3}/i.exec(o.l)?.[0].toLowerCase() ?? '') : '';
    const refSource = sourceOf(ref, ctx.ownHosts);
    beacon.entry = { source: (utm.source && UTM_SOURCES[utm.source]) || refSource, utm, lang };
    // campaignTotals false: a utm_source never becomes a source in the totals
    // (rows still name it). See references/decisions.md, model A.
    if (ctx.campaignTotals === false) beacon.totalsSource = refSource;
    // campaigns: only allowlisted utm_campaign values reach the totals, any
    // other tag counts as "(other)". Off with campaignTotals false.
    else if (ctx.campaigns && utm.campaign) beacon.totalsCampaign = ctx.campaigns.has(field(utm.campaign)) ? field(utm.campaign) : '(other)';
    if (o.en === 2) beacon.entryRepeat = true;
  }
  const hex16 = /^[0-9a-f]{16}$/;
  if (ctx.ids === 'consent' && typeof o.vi === 'string' && typeof o.v === 'string' && hex16.test(o.vi) && hex16.test(o.v)) {
    beacon.ids = { visit: o.vi, view: o.v };
    if (typeof o.ph === 'string' && /^[A-Za-z0-9-]{8,64}$/.test(o.ph)) beacon.ids.replay = o.ph;
  } else if (ctx.ids === 'always' && typeof o.v === 'string' && hex16.test(o.v)) {
    beacon.ids = { view: o.v };
  }
  return beacon;
}

// <toRegExp> (the same in k.js, consent.js, collector.mjs and posthog-guard.mjs; a test checks)
// A private-path rule: a RegExp, one regex source ("^/account(/|$)"), or
// "/source/flags" ("/^\/account(\/|$)/i"), spaces trimmed. g and y are
// dropped; unknown flags, a "/^…" without its closing slash or a source that
// does not compile throw, so a broken rule never silently matches nothing.
export function toRegExp(v) {
  if (v instanceof RegExp) return new RegExp(v.source, v.flags.replace(/[gy]/g, ''));
  var s = String(v).trim(), m = /^\/(.+)\/([A-Za-z]*)$/.exec(s);
  // "^/account, ^/reset": a list, which would be one regex matching neither.
  if (/,\s*[\^\/]/.test(s)) throw new Error('skip is a comma-separated list; join the paths with | in one regex: ' + s);
  if (m) {
    // g and y make test() stateful; anything else unknown is a mistake.
    var f = m[2].toLowerCase().replace(/[gy]/g, '');
    if (/[^dimsuv]/.test(f)) throw new Error('unknown regex flags: ' + s);
    return new RegExp(m[1], f);
  }
  if (s.charAt(0) === '/' && s.charAt(1) === '^') throw new Error('a regex literal without its closing slash: ' + s);
  return new RegExp(s);
}
export function toRegExps(v) {
  return (Array.isArray(v) ? v : [v]).filter(function (x) { return x instanceof RegExp || (x != null && String(x).trim() !== ''); }).map(toRegExp);
}
// </toRegExp>

/** A page path the collector may count: public, no query, no trailing slash. */
export function pagePath(v, skip = []) {
  if (typeof v !== 'string' || !PATH.test(v) || v.includes('//')) return null;
  if (skip.some((re) => re.test(v))) return null;
  // Belt and braces: k.js already turns token-like segments into [id].
  if (v.split('/').some((seg) => seg && seg !== '[id]' && looksPersonal(safeDecode(seg)))) return null;
  return v.length > 1 ? v.replace(/\/$/, '') : v;
}
function safeDecode(s) {
  try {
    return decodeURIComponent(s);
  } catch {
    return s;
  }
}

/** Internal link target: a public path plus an in-page anchor. */
function navTarget(v, skip) {
  if (v === '/[private]') return v;
  const m = typeof v === 'string' ? /^(\/[A-Za-z0-9\-._~%/[\]]{0,120})(#[A-Za-z0-9_-]{1,32})?$/.exec(v) : null;
  if (!m) return undefined;
  const p = pagePath(m[1], skip);
  return p ? p + (m[2] && !looksPersonal(m[2]) ? m[2] : '') : '/[private]';
}
/** Outbound or download target: host and path, no query. */
function outTarget(v) {
  return typeof v === 'string' && /^[a-z0-9.-]{1,80}(\/[A-Za-z0-9\-._~%/[\]]{0,80})?$/i.test(v) && !looksPersonal(v.replace(/^[^/]*/, ''))
    ? v.toLowerCase()
    : undefined;
}
const NAME = /^[a-z0-9][a-z0-9_-]{0,23}$/;
const UI_NAME = /^[a-z0-9][a-z0-9:_-]{0,31}$/;
/** A name the page gave (data-kcta, data-kgoal, data-kui), or null when it is malformed or may name someone. */
function named(v, re) {
  return typeof v === 'string' && re.test(v) && !looksPersonal(v) ? v : null;
}

const DATA = {
  view: (d) => ({ of: int(d.of, 0, 99) ?? 0 }),
  read: (d) => {
    const s = key(d.s);
    return s ? { s, n: int(d.n, 0, 99) ?? 0, of: int(d.of, 0, 99) ?? 0 } : null;
  },
  time: (d) => {
    const sec = int(d.sec, 0, 3600) ?? 0;
    const secs = [];
    if (Array.isArray(d.secs)) {
      for (const x of d.secs.slice(0, 12)) {
        const k = Array.isArray(x) ? key(x[0]) : '';
        const n = Array.isArray(x) ? int(x[1], 1, 3600) : undefined;
        // A section cannot have had more active seconds than the whole report.
        if (k && n !== undefined) secs.push([k, Math.min(n, sec)]);
      }
    }
    const dn = Array.isArray(d.dn) ? DEPTHS.filter((x) => d.dn.includes(x)) : [];
    const out = { sec, vis: int(d.vis, 0, 86400) ?? 0, s: key(d.s), of: int(d.of, 0, 99) ?? 0, secs, dn };
    const cv = vitalsOf(d.cv);
    if (cv) out.cv = cv;
    const n = int(d.n, 0, 99);
    if (n !== undefined) out.n = n;
    // The visit moved up the active-time buckets (HIST).
    if (Array.isArray(d.hb) && d.hb.length === 2) {
      const from = int(d.hb[0], 0, HIST.length - 1);
      const to = int(d.hb[1], 0, HIST.length - 1);
      if (from !== undefined && to !== undefined && from === d.hb[0] && to === d.hb[1] && from < to) out.hb = [from, to];
    }
    return out;
  },
  cta: (d, ctx) => {
    const k = named(d.k, NAME);
    if (!k) return null;
    const out = { k, s: key(d.s), t: int(d.t, 0, 86400) ?? 0, tab: d.tab === 1 ? 1 : 0 };
    const url = k === 'nav' ? navTarget(d.url, ctx.skip) : k === 'email' || k === 'phone' ? undefined : typeof d.url === 'string' && d.url.startsWith('/') ? navTarget(d.url, ctx.skip) : outTarget(d.url);
    if (url) out.url = url;
    return out;
  },
  ui: (d) => {
    const k = named(d.k, UI_NAME);
    return k ? { k, s: key(d.s) } : null;
  },
  dead: (d) => ({ s: key(d.s), label: clickLabel(d.label) }),
  rage: (d) => ({ s: key(d.s), label: clickLabel(d.label) }),
  copy: (d) => ({ kind: d.kind === 'email' ? 'email' : 'text', n: int(d.n, 0, 100_000) ?? 0, s: key(d.s) }),
  print: (d) => ({ s: key(d.s) }),
  goal: (d) => (named(d.k, NAME) ? { k: d.k } : null),
  // A [data-kform] form was submitted: its name only.
  form: (d) => (named(d.k, NAME) ? { k: d.k, s: key(d.s) } : null),
  // A 404 page: where the link to it was (internal = a broken link on the site).
  nf: (d) => ({ r: d.r === 'internal' || d.r === 'external' ? d.r : 'none' }),
  // The consent banner was shown or answered (consent.js, k.js data-consent-counts).
  consent: (d) => (CONSENT_EVENTS.includes(d.k) ? { k: d.k } : null),
  // A JavaScript error, scrubbed again here (a client can send anything).
  err: (d) => {
    const m = scrubError(typeof d.m === 'string' ? d.m : '').slice(0, 120);
    const f = errFile(d.f);
    if (!m || !f) return null;
    const l = int(d.l, 0, 10_000_000) ?? 0;
    return { m, f, l, c: int(d.c, 0, 10_000_000) ?? 0, s: key(d.s), fp: errFingerprint(m, f, l) };
  },
};

/** The cv field of a time report: { lcp, cls, inp, ttfb } bucket indices, lcps/inps section keys. */
function vitalsOf(v) {
  if (!v || typeof v !== 'object' || Array.isArray(v)) return undefined;
  const out = {};
  for (const [m, spec] of Object.entries(CWV_BUCKETS)) {
    const b = int(v[m], 0, spec.edges.length - 1);
    if (b !== undefined && b === v[m]) out[m] = b;
  }
  if ('lcp' in out) out.lcps = key(v.lcps);
  if ('inp' in out) out.inps = key(v.inps);
  return Object.keys(out).length ? out : undefined;
}

/**
 * A 404 path as a counter name: "." would nest in Mongo and in the stores'
 * dotted keys, so it is written %2E; the path is otherwise kept as it is
 * (pagePath allows no "$" and no query).
 */
export function nfKey(path) {
  return String(path).replace(/\./g, '%2E');
}

// --- Aggregation --------------------------------------------------------------

/** A calendar day in `timeZone`, "2026-10-05". */
export function dayOf(at, timeZone = 'UTC') {
  return new Intl.DateTimeFormat('en-CA', { timeZone, year: 'numeric', month: '2-digit', day: '2-digit' }).format(at);
}

/** A field name safe in Mongo and as a JSON key: no ".", no leading "$". */
export function field(s) {
  return (
    String(s)
      .toLowerCase()
      .replace(/[^a-z0-9_-]+/g, '_')
      .replace(/^_+|_+$/g, '')
      .slice(0, 40) || '_'
  );
}

/**
 * What one report adds to the day's totals: one document per page and day
 * (`<day> <path>`) and one per day for the visits (`<day> *`). Counters only;
 * nothing in them describes a single visit. `admit(kind, key)` caps how many
 * distinct keys of a kind a day may add (they come from the browser).
 *
 * The visit histogram (`hist.<bucket>`) is counted without ids: a new visit
 * adds one to bucket 0, and each time its active time crosses into a higher
 * bucket the report moves it (-1 old, +1 new).
 *
 * `hour` ("00"–"23", optional): the hour a new visit started, in the owner's
 * time zone, counted as `hour.<HH>` on the day's visits document. health.mjs
 * compares those with the same hours of earlier weeks. createCollector passes
 * it unless `hourly: false`.
 */
export function dailyIncs(b, who, day, admit, hour) {
  const page = {};
  const visit = {};
  const add = (into, name, n = 1) => {
    into[name] = (into[name] ?? 0) + n;
  };
  const known = (kind, raw) => {
    const f = field(raw);
    return admit(kind, f) ? f : 'other';
  };
  const section = (s) => (typeof s === 'string' && s ? known('section', s) : '_');
  const d = b.data;

  switch (b.event) {
    case 'view':
      add(page, 'views');
      // A repeated entry (after consent) was counted with the visit's first view.
      if (b.entry && !b.entryRepeat) {
        add(page, 'entries');
        add(visit, 'visits');
        add(visit, 'hist.0');
        add(visit, `src.${known('src', b.totalsSource ?? b.entry.source)}`);
        add(visit, `geo.${field(who.country)}`);
        add(visit, `dev.${who.device}`);
        if (b.entry.lang) add(visit, `lang.${known('lang', b.entry.lang)}`);
        // Visits per hour of the day (health.mjs compares them with the same
        // hours of earlier weeks). Only the hour, in the owner's time zone.
        if (typeof hour === 'string' && /^\d\d$/.test(hour)) add(visit, `hour.${hour}`);
        // An allowlisted campaign (collector option campaigns), else "(other)".
        if (b.totalsCampaign) add(visit, `campaign.${b.totalsCampaign === '(other)' || !admit('campaign', b.totalsCampaign) ? '(other)' : b.totalsCampaign}`);
        // The utm values themselves stay out of the totals, which are kept two
        // years: a campaign tag can be made for one recipient. Rows keep them.
      }
      break;
    case 'read':
      add(page, `sec.${section(d.s)}.r`);
      break;
    case 'time': {
      if (d.sec > 0) add(page, 'active', d.sec);
      if (d.vis > 0) add(page, 'visible', d.vis);
      for (const [k, n] of d.secs) if (n > 0) add(page, `sec.${section(k)}.s`, n);
      for (const x of d.dn) add(page, `depth.${x}`);
      // Core Web Vitals: a histogram per device class, and for poor LCP and
      // INP the section of the element or interaction.
      if (b.cv) {
        for (const [m, spec] of Object.entries(CWV_BUCKETS)) {
          if (b.cv[m] === undefined) continue;
          add(page, `cwv.${who.device}.${m}.${b.cv[m]}`);
          if (b.cv[m] >= spec.poor && (m === 'lcp' || m === 'inp')) add(page, `cwvs.${m}.${section(b.cv[m + 's'])}`);
        }
      }
      if (d.hb) {
        add(visit, `hist.${d.hb[0]}`, -1);
        add(visit, `hist.${d.hb[1]}`, 1);
      }
      break;
    }
    case 'cta':
      add(page, `cta.${BUILT_IN_LINKS.includes(d.k) ? d.k : known('cta', d.k)}`);
      if ((d.k === 'outbound' || d.k === 'download') && typeof d.url === 'string' && !d.url.startsWith('/')) {
        add(page, `out.${known('out', d.url.split('/')[0])}`);
      }
      if (d.k === 'nav' && typeof d.url === 'string') add(page, `nav.${known('nav', d.url)}`);
      break;
    case 'ui':
      add(page, `ui.${known('ui', d.k)}`);
      break;
    case 'dead':
      add(page, `dead.${section(d.s)}`);
      break;
    case 'rage':
      add(page, `rage.${section(d.s)}`);
      break;
    case 'copy':
      add(page, `copy.${d.kind}`);
      break;
    case 'print':
      add(page, 'print');
      break;
    case 'goal': {
      const g = known('goal', d.k);
      add(visit, `goal.${g}`);
      // By the class of the page load's entry (SOURCE_CLASSES only, never a referrer).
      if (SOURCE_CLASSES.includes(b.goalSource)) add(visit, `goalsrc.${g}.${b.goalSource}`);
      break;
    }
    case 'form':
      // Per day, next to the goals: submits of a form whose goal is sent when
      // the server confirms (health.mjs compares the two).
      add(visit, `form.${known('form', d.k)}`);
      break;
    case 'consent':
      add(visit, `consent.${d.k}`);
      break;
    case 'nf': {
      // Per day: nf.<path> every 404, nfin.<path> those reached from a link
      // on the site itself. Past the cap, nf.(other).
      const k = nfKey(admit('nf', b.path) ? b.path : '(other)');
      add(visit, `nf.${k}`);
      if (d.r === 'internal') add(visit, `nfin.${k}`);
      break;
    }
    case 'err':
      // Per page: err.<fingerprint>; past the day's cap, err.(other).
      add(page, `err.${admit('err', d.fp) ? d.fp : '(other)'}`);
      break;
  }

  const out = [];
  if (Object.keys(page).length) {
    const path = admit('path', b.path) ? b.path : '(other)';
    out.push({ _id: `${day} ${path}`, day, path, inc: page });
  }
  if (Object.keys(visit).length) out.push({ _id: `${day} *`, day, path: '*', inc: visit });
  return out;
}

/**
 * The row for a report that carries ids, else null. `visitor` is the daily
 * hash ("always" mode) or undefined ("consent" mode, where the visit id is
 * the browser's).
 */
export function eventRow(b, who, day, at, visitor) {
  if (!b.ids) return null;
  const visit = b.ids.visit ?? visitor;
  if (!visit) return null;
  const row = { at, day, visit, view: b.ids.view, path: b.path, e: b.event, d: b.data };
  if (b.entry) row.entry = { ...b.entry, utm: { ...b.entry.utm }, country: who.country, device: who.device };
  if (b.ids.replay) row.replay = b.ids.replay;
  return row;
}

// --- Daily visitor hash ("always" mode) -----------------------------------------

/** IPv4 keeps its /24, IPv6 its /48. The full address is never hashed. */
export function shortIp(ip) {
  if (!ip) return '';
  const mapped = /^::ffff:(\d+\.\d+\.\d+\.\d+)$/i.exec(ip);
  if (mapped) return shortIp(mapped[1]);
  if (!ip.includes(':')) return ip.replace(/\.\d+$/, '.0');
  const [head, tail] = ip.split('::');
  let groups = head ? head.split(':') : [];
  if (tail !== undefined) {
    const t = tail ? tail.split(':') : [];
    groups = groups.concat(Array(Math.max(0, 8 - groups.length - t.length)).fill('0'), t);
  }
  return groups.slice(0, 3).map((g) => g || '0').join(':') + '::';
}

async function hmacHex(secret, text, bytes) {
  const enc = new TextEncoder();
  const k = await crypto.subtle.importKey('raw', enc.encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  const mac = await crypto.subtle.sign('HMAC', k, enc.encode(text));
  return [...new Uint8Array(mac, 0, bytes)].map((x) => x.toString(16).padStart(2, '0')).join('');
}

/**
 * A visitor id that changes every day: HMAC of the day, the shortened IP and
 * the user agent, keyed with a secret. It groups one day's page views into
 * visits; without the secret it cannot be turned back into an address, and
 * days cannot be linked. The view id is hashed with the day too, so a tab
 * left open past midnight does not tie two days together.
 */
export async function dailyIds(secret, day, ip, ua, view) {
  return {
    visitor: await hmacHex(secret, `${day}|${shortIp(ip)}|${ua}`, 8),
    view: await hmacHex(secret, `${day}|view|${view}`, 8),
  };
}

// --- Throttle -------------------------------------------------------------------

/**
 * Per-IP throttle, in memory only and only for its window: the IP is never
 * stored or logged. A long, busy visit sends a few dozen reports; this stops
 * a script. Per process.
 */
export function createThrottle({ windowMs = 5 * 60_000, limit = 150, maxKeys = 20_000 } = {}) {
  const hits = new Map();
  let swept = Date.now();
  const sweep = (now = Date.now()) => {
    swept = now;
    for (const [key, v] of hits) if (now - v.since > windowMs) hits.delete(key);
  };
  // An address is forgotten within two windows of its last report, even when
  // no further report arrives (a timer where the runtime allows one).
  try {
    setInterval(sweep, windowMs).unref?.();
  } catch {}
  return function throttled(ip, now = Date.now()) {
    if (now - swept > windowMs) sweep(now);
    const k = throttleKey(ip);
    const h = hits.get(k);
    if (!h || now - h.since > windowMs) {
      if (hits.size >= maxKeys) {
        // Full: forget expired windows, then the oldest, rather than turn
        // the next real visitor away.
        sweep(now);
        for (const key of hits.keys()) {
          if (hits.size < maxKeys) break;
          hits.delete(key);
        }
      }
      hits.set(k, { n: 1, since: now });
      return false;
    }
    h.n++;
    return h.n > limit;
  };
}
/** An IPv6 address counts by its /64, which is what one subscriber gets. */
export function throttleKey(ip) {
  if (!ip.includes(':')) return ip;
  if (ip.includes('.')) return ip.slice(ip.lastIndexOf(':') + 1);
  const [head, tail] = ip.toLowerCase().split('::');
  const left = head ? head.split(':') : [];
  const right = tail ? tail.split(':') : [];
  const full = tail === undefined ? left : [...left, ...Array(Math.max(0, 8 - left.length - right.length)).fill('0'), ...right];
  return full.slice(0, 4).map((x) => x.replace(/^0+(?=.)/, '')).join(':');
}

// --- The handler ----------------------------------------------------------------

/**
 * The visitor's IP, for the throttle (and the daily hash in 'always' mode).
 * Which header to trust depends on what is in front of the server: pass
 * `clientIp` for it (references/collector.md). This default reads
 * Cloudflare's CF-Connecting-IP, else the LAST X-Forwarded-For entry. It
 * never reads X-Real-IP, which many proxies pass through from the client
 * (if yours sets it, pass clientIp: (r) => r.headers.get('x-real-ip')).
 * CF-Connecting-IP is trustworthy only when every request comes through
 * Cloudflare; otherwise a client can send it. The last X-Forwarded-For
 * entry is the one the nearest proxy added; with no proxy in front, the
 * client writes the whole header.
 */
export function defaultClientIp(request) {
  const h = request.headers;
  const xff = h.get('x-forwarded-for');
  return h.get('cf-connecting-ip') ?? (xff ? xff.split(',').pop().trim() : '');
}

// Distinct keys a day may add per kind. Past them a hostile client's junk is
// counted as "other" instead of growing the documents. Per process.
export const DAILY_CAPS = { path: 300, section: 400, src: 200, campaign: 100, lang: 60, ui: 100, out: 200, nav: 300, cta: 50, goal: 50, form: 50, nf: 100, err: 50 };

/**
 * Creates the collector. Options:
 *   hosts       the site's hostnames; a report from any other Origin is dropped (required)
 *   store       { write({ incs, row }) } — see memoryStore and mongoStore (required)
 *   ids         'never' | 'consent' | 'always' (default 'consent'; must match k.js)
 *   secret      required for ids 'always': the key of the daily visitor hash
 *   skip        the private paths never counted (the same rule as k.js data-skip): a
 *               RegExp, a string (one regex source, or "/source/flags"), or an array
 *               of them. A rule that does not parse throws here, at startup
 *   campaignTotals  default true: a known utm_source ("newsletter", "qr"…) becomes the
 *               visit's source in the totals. false: the totals use the referrer only,
 *               and campaign tags reach rows alone (references/decisions.md, model A)
 *   campaigns   optional list of utm_campaign names that may reach the totals (`campaign.<name>`
 *               on the day's visits; any other tag counts as `campaign.(other)`). Without it no
 *               campaign is counted; with campaignTotals false neither
 *   consentCounts  default false: count consent.js's banner events (`consent.shown|accept|
 *               decline|withdraw`, k.js data-consent-counts="on"); the owner decides
 *   timeZone    IANA zone whose calendar days the totals use (default 'UTC')
 *   hourly      default true: count visits per hour of the day (`hour.<HH>`), which
 *               health.mjs needs for its "no visits for N hours" and "visits so far
 *               today" rules. false: daily counts only
 *   rowsPerDay  rows a day may add (default 5000); past it reports still count in the totals
 *   deletion    default true: accept a visitor's own deletion request, { "del": <visit id> }
 *               (ids 'consent') or { "del": "today" } (ids 'always'), on this endpoint.
 *               Needs a store with deleteVisit (references/collector.md, "Deletion")
 *   healthEveryMs  how often the store's health record is written at most (default 60 s;
 *               a change between failing and working is written at once)
 *   forward     optional async (beacon, who, request) => void, e.g. umamiForwarder(...)
 *   clientIp    optional (request) => string: where the visitor's IP comes from (see defaultClientIp)
 *   onError     optional (err) => void, called at most once a minute
 *
 * The returned function has `collect.health()`: this process's health record
 * (references/alerts.md).
 */
export function createCollector(opts) {
  const ownHosts = (opts.hosts ?? []).map((h) => h.toLowerCase());
  if (!ownHosts.length) throw new Error('createCollector: hosts is required');
  if (!opts.store) throw new Error('createCollector: store is required');
  const idsMode = opts.ids ?? 'consent';
  if (idsMode === 'always' && !opts.secret) throw new Error("createCollector: ids 'always' needs a secret");
  const campaigns = opts.campaigns == null ? null : new Set((Array.isArray(opts.campaigns) ? opts.campaigns : [opts.campaigns]).map((c) => token(String(c), 40)).filter(Boolean).map(field));
  const ctx = { ownHosts, skip: toRegExps(opts.skip ?? []), ids: idsMode, campaignTotals: opts.campaignTotals !== false, campaigns, consentCounts: opts.consentCounts === true };
  const timeZone = opts.timeZone ?? 'UTC';
  const hourly = opts.hourly !== false;
  const rowsPerDay = opts.rowsPerDay ?? 5000;
  const deletion = opts.deletion !== false;
  const throttled = createThrottle();
  // Deletion requests have their own limit per address, before and instead of
  // the reports' one: a busy shared address (an office NAT) must not lose a
  // visitor's deletion to other people's reports. A dropped one is counted in
  // the health record (delDropped), which health.mjs alerts on.
  const delThrottled = createThrottle({ limit: opts.deletionsPerAddress ?? 30 });
  const health = createHealth(opts.store, opts.healthEveryMs ?? 60_000);
  let capDay = '';
  let seen = new Map();
  let sampled = new Set();
  let rows = 0;
  let lastError = 0;

  function admitFor(day) {
    if (day !== capDay) {
      capDay = day;
      seen = new Map();
      sampled = new Set();
      rows = 0;
    }
    return (kind, k) => {
      let keys = seen.get(kind);
      if (!keys) seen.set(kind, (keys = new Set()));
      if (keys.has(k)) return true;
      if (keys.size >= (DAILY_CAPS[kind] ?? 100)) return false;
      keys.add(k);
      return true;
    };
  }

  const done = () => new Response(null, { status: 204, headers: { 'cache-control': 'no-store' } });
  const report = (err) => {
    // At most one line a minute: a database outage must not flood the logs.
    if (Date.now() - lastError > 60_000) {
      lastError = Date.now();
      (opts.onError ?? ((e) => console.error('[k] write failed', e)))(err);
    }
  };

  // { "del": … }: the visitor's own rows, deleted. Same answer either way, so
  // nobody learns whether a visit id exists.
  async function remove(del, request, ip) {
    if (!deletion || typeof opts.store.deleteVisit !== 'function') return;
    if (ip && delThrottled(ip)) return health.delDropped();
    let visit = '';
    if (idsMode === 'consent' && /^[0-9a-f]{16}$/.test(del)) visit = del;
    else if (idsMode === 'always' && del === 'today') {
      // Model C: only today's hash can be computed again (references/collector.md).
      const ua = request.headers.get('user-agent') ?? '';
      if (!ua || !ip) return;
      visit = (await dailyIds(opts.secret, dayOf(new Date(), timeZone), ip, ua, '')).visitor;
    }
    if (!visit) return;
    try {
      await opts.store.deleteVisit(visit);
    } catch (err) {
      health.delDropped();
      report(err);
    }
  }

  async function collect(request) {
    if (request.method !== 'POST') return new Response(null, { status: 405, headers: { allow: 'POST' } });
    const who = visitorOf(request.headers, request.cf);

    // Only the site's own pages: browsers send Origin on a POST.
    let host = '';
    try {
      host = new URL(request.headers.get('origin') || request.headers.get('referer') || '').hostname.toLowerCase();
    } catch {
      return done();
    }
    if (!ownHosts.includes(host)) return done();

    const ip = (opts.clientIp ?? defaultClientIp)(request) || '';

    let body;
    try {
      body = await readCapped(request);
    } catch {
      return done();
    }
    // A deletion request is exactly { "del": … }, and is honoured even with
    // Global Privacy Control on (deleting is never tracking). It is checked
    // before the reports' throttle and has a limit of its own.
    if (body && body.length < 64 && body.includes('"del"')) {
      let o = null;
      try {
        o = JSON.parse(body);
      } catch {}
      if (o && typeof o === 'object' && !Array.isArray(o) && Object.keys(o).length === 1 && typeof o.del === 'string') {
        await remove(o.del, request, ip);
        return done();
      }
    }
    if (ip && throttled(ip)) return done();
    if (!who) return done();
    const beacon = body ? parseBeacon(body, ctx) : null;
    if (!beacon) return done();
    // A broken link "of ours" needs more than the browser's word: the request
    // must come from a page of the site (a same-origin Referer, which
    // sendBeacon sends under the default referrer policy). Without one it
    // counts as an ordinary 404.
    if (beacon.event === 'nf' && beacon.data.r === 'internal' && !sameSiteReferer(request, ownHosts)) beacon.data = { ...beacon.data, r: 'none' };
    health.report();

    try {
      const now = new Date();
      const day = dayOf(now, timeZone);
      const hour = hourly && beacon.entry && !beacon.entryRepeat ? hourOf(now, timeZone) : undefined;
      const admit = admitFor(day);
      const incs = dailyIncs(beacon, who, day, admit, hour);
      let visitor;
      if (idsMode === 'always' && beacon.ids) {
        const h = await dailyIds(opts.secret, day, ip, request.headers.get('user-agent') ?? '', beacon.ids.view);
        visitor = h.visitor;
        beacon.ids.view = h.view;
      }
      let row = eventRow(beacon, who, day, now, visitor);
      if (row && rows >= rowsPerDay) row = null;
      if (row) rows++;
      // One scrubbed sample per error fingerprint and day (no ids; the
      // store keeps the first it gets). None past the cap.
      let sample;
      if (beacon.event === 'err' && admit('err', beacon.data.fp) && !sampled.has(beacon.data.fp)) {
        sampled.add(beacon.data.fp);
        const { fp, m, f, l, c } = beacon.data;
        sample = { day, fp, m, f, l, c, path: beacon.path };
      }
      try {
        await opts.store.write(sample ? { incs, row, sample } : { incs, row });
      } catch (err) {
        health.failed(err);
        throw err;
      }
      health.wrote();
      if (opts.forward) await opts.forward(beacon, who, request);
    } catch (err) {
      report(err);
    }
    return done();
  }
  collect.health = () => health.get();
  return collect;
}

function sameSiteReferer(request, ownHosts) {
  try {
    return ownHosts.includes(new URL(request.headers.get('referer') || '').hostname.toLowerCase());
  } catch {
    return false;
  }
}

/** The hour of the day in `timeZone`, "00"–"23". */
export function hourOf(at, timeZone = 'UTC') {
  const h = new Intl.DateTimeFormat('en-GB', { timeZone, hour: '2-digit', hourCycle: 'h23' }).format(at);
  return h.padStart(2, '0').slice(-2);
}

// --- Health -------------------------------------------------------------------------

/**
 * What a failed write is called in the health record: the error's class and
 * code only (e.g. "MongoNetworkError ECONNREFUSED"), never its message,
 * which can quote the data.
 */
export function errorClass(err) {
  const name = typeof err?.name === 'string' && /^[A-Za-z][A-Za-z0-9_]{0,39}$/.test(err.name) ? err.name : 'Error';
  const code = err?.code;
  return (typeof code === 'string' && /^[A-Za-z0-9_.-]{1,30}$/.test(code)) || (typeof code === 'number' && Number.isFinite(code)) ? `${name} ${code}` : name;
}
/** A time in the health record: to the minute, so it never dates one report exactly. */
function minute(t) {
  return new Date(Math.floor(t / 60_000) * 60_000).toISOString();
}

/**
 * The collector's health record, kept in memory and written to the store
 * (`saveHealth`) off the hot path: never awaited by the request, at most
 * once per `everyMs` (on reports too, so a stored record shows reports
 * arriving while writes do not), and at once when writes start or stop
 * failing.
 *   instance     a random id of this process (several instances keep one record each)
 *   savedAt      when the record was written
 *   lastWrite    the minute of the last successful write (ISO)
 *   writeErrors  failed writes since the last success
 *   lastError    the last failure's class (errorClass), never its message
 *   lastReport   the minute the last valid report arrived (written or not)
 *   reports      valid reports this process has received
 *   delDropped, lastDelDrop  deletion requests dropped (rate limit, store error), and the minute of the last
 *   since        when this process started counting
 */
function createHealth(store, everyMs) {
  const instance = [...crypto.getRandomValues(new Uint8Array(4))].map((x) => x.toString(16).padStart(2, '0')).join('');
  const h = { instance, lastWrite: null, writeErrors: 0, lastError: null, lastReport: null, reports: 0, delDropped: 0, lastDelDrop: null, since: minute(Date.now()) };
  let savedAt = 0;
  let saving = 0;
  let pending = false;
  function persist(force) {
    if (typeof store.saveHealth !== 'function') return;
    // A save that never finished (a hung store) blocks the next one for 30 s
    // at most; a forced save asked for meanwhile follows the current one.
    if (saving && Date.now() - saving < 30_000) {
      if (force) pending = true;
      return;
    }
    if (!force && Date.now() - savedAt < everyMs) return;
    savedAt = saving = Date.now();
    // Not awaited: a slow or failing store never holds up an answer.
    Promise.resolve()
      .then(() => store.saveHealth({ ...h, savedAt: new Date().toISOString() }))
      .catch(() => {})
      .finally(() => {
        saving = 0;
        if (pending) {
          pending = false;
          persist(true);
        }
      });
  }
  return {
    report() {
      h.reports++;
      h.lastReport = minute(Date.now());
      persist(false);
    },
    wrote() {
      const recovering = h.writeErrors > 0 || !h.lastWrite;
      h.lastWrite = minute(Date.now());
      h.writeErrors = 0;
      persist(recovering);
    },
    failed(err) {
      const first = h.writeErrors === 0;
      h.writeErrors++;
      h.lastError = errorClass(err);
      persist(first);
    },
    delDropped() {
      h.delDropped++;
      h.lastDelDrop = minute(Date.now());
      persist(true);
    },
    get: () => ({ ...h }),
  };
}

/** How long an instance's record counts for its failures (several instances, references/alerts.md). */
export const HEALTH_LIVE_MS = 2 * 3600_000;
/** Records older than this are dropped when a store saves. */
const HEALTH_KEEP_MS = 7 * 86_400_000;
const isoMax = (xs) => xs.filter((x) => typeof x === 'string' && x).sort().pop() ?? null;

/**
 * One record from the instances' records: the newest lastWrite and
 * lastReport of any instance, and the failures of those that saved within
 * HEALTH_LIVE_MS (the worst writeErrors, dropped deletions summed).
 */
export function mergeHealth(records, now = Date.now()) {
  const all = (records ?? []).filter((r) => r && typeof r === 'object');
  if (!all.length) return null;
  const live = all.filter((r) => !r.savedAt || now - Date.parse(r.savedAt) <= HEALTH_LIVE_MS);
  const worst = live.reduce((a, r) => (Number(r.writeErrors) > Number(a?.writeErrors ?? 0) ? r : a), null);
  return {
    lastWrite: isoMax(all.map((r) => r.lastWrite)),
    lastReport: isoMax(all.map((r) => r.lastReport)),
    writeErrors: worst ? Number(worst.writeErrors) : 0,
    lastError: worst ? worst.lastError ?? null : null,
    delDropped: live.reduce((n, r) => n + (Number(r.delDropped) || 0), 0),
    lastDelDrop: isoMax(all.map((r) => r.lastDelDrop)),
    instances: live.length,
  };
}
const healthKey = (h) => (typeof h?.instance === 'string' && /^[0-9a-z_-]{1,40}$/i.test(h.instance) ? h.instance : 'default');
const healthOld = (h, now = Date.now()) => h?.savedAt && now - Date.parse(h.savedAt) > HEALTH_KEEP_MS;

/** The health record a store kept (or null): `store.health()` where it has one. */
export async function readHealth(store, now = Date.now()) {
  return typeof store?.health === 'function' ? (await store.health(now)) ?? null : null;
}

async function readCapped(request) {
  if (Number(request.headers.get('content-length') ?? 0) > MAX_BYTES) return null;
  const reader = request.body?.getReader();
  if (!reader) return null;
  const chunks = [];
  let size = 0;
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    size += value.byteLength;
    if (size > MAX_BYTES) {
      void reader.cancel();
      return null;
    }
    chunks.push(value);
  }
  const all = new Uint8Array(size);
  let at = 0;
  for (const c of chunks) {
    all.set(c, at);
    at += c.byteLength;
  }
  return new TextDecoder().decode(all);
}

// --- Stores -----------------------------------------------------------------------

/*
 * A store has write({ incs, row, sample? }); everything else is optional, and the
 * helpers say when a store lacks what they need:
 *   totals(day)            the day's totals, { _id: doc } with nested counters
 *   errSamples(day)        { <fingerprint>: { m, f, l, c, path } }: one scrubbed sample per
 *                          JavaScript error and day (write's `sample`; the first one kept).
 *                          Samples follow the rows' retention (deleteBefore's rowsBefore)
 *   saveHealth(h), health(now?)  the collector's health record, judged at `now` (references/alerts.md)
 *   deleteBefore({ totalsBefore, rowsBefore, gscBefore })  deletes totals, rows (and error
 *                          samples) and Search Console documents of days before those
 *                          ("2024-10-09"); returns { totals, rows } removed
 *   markDeploy(day, { sha, at, note? })  adds a deploy marker to the day's "<day> *" document
 *                          (`deploys`, the newest DEPLOY_CAP kept); use the markDeploy() helper
 *   saveGsc(day, doc), gsc(day)  one Search Console document per day (gsc.mjs), kept 16 months
 *   oldest()               { totalsDay, rowsDay }: the oldest day still kept, or null
 *   visitRows(visit), deleteVisit(visit)  one visit's rows (a visitor's own data)
 * retention.mjs, dsar.mjs and health.mjs use them.
 */

/** Deploy markers kept per day: the newest by `at`, in every store. */
export const DEPLOY_CAP = 20;
const newestDeploys = (list) => list.sort((a, b) => (a.at < b.at ? -1 : a.at > b.at ? 1 : 0)).slice(-DEPLOY_CAP);

/**
 * Marks a deploy in the day's totals (`deploys: [{ sha, at, note? }]` on the
 * "<day> *" document): the commit's first 7 hex characters and the minute.
 * The weekly digest lists them, and health.mjs says "after deploy <sha>".
 * `note` is kept only when it is a short plain label ("v1.4", "hotfix"):
 * never a commit message, which can name people. Skips a sha already marked
 * that day. Returns { day, sha, at } or { unsupported } (Analytics Engine).
 */
export async function markDeploy({ store, sha, at = new Date(), note, timeZone = 'UTC' }) {
  if (!/^[0-9a-f]{7,64}$/i.test(String(sha ?? ''))) throw new Error('markDeploy: sha must be a commit hash (7 to 64 hex characters)');
  if (typeof store?.markDeploy !== 'function') return { unsupported: 'this store keeps no deploy markers' };
  const t = new Date(at);
  if (!Number.isFinite(t.getTime())) throw new Error('markDeploy: at is not a date');
  const entry = { sha: String(sha).toLowerCase().slice(0, 7), at: minute(t.getTime()) };
  const n = typeof note === 'string' ? note.replace(/\s+/g, ' ').trim() : '';
  if (n && /^[A-Za-z0-9 ._:#+-]{1,40}$/.test(n) && !looksPersonal(n)) entry.note = n;
  const day = dayOf(t, timeZone);
  if (typeof store.totals === 'function') {
    const doc = (await store.totals(day))?.[`${day} *`];
    if (Array.isArray(doc?.deploys) && doc.deploys.some((x) => x?.sha === entry.sha)) return { day, ...entry, skipped: 'already marked' };
  }
  await store.markDeploy(day, entry);
  return { day, ...entry };
}

/**
 * In memory, for tests and local development. `daily` maps an _id to its
 * document; `rows` is every row in order.
 */
export function memoryStore() {
  const daily = new Map();
  const rows = [];
  const errs = new Map(); // day → { fp: sample }
  const health = new Map(); // instance → record
  const gscDocs = new Map(); // day → Search Console document
  const removeRows = (keep) => {
    let n = 0;
    for (let i = rows.length - 1; i >= 0; i--) if (!keep(rows[i])) (rows.splice(i, 1), n++);
    return n;
  };
  return {
    daily,
    rows,
    errs,
    async write({ incs, row, sample }) {
      for (const u of incs) {
        const doc = daily.get(u._id) ?? { _id: u._id, day: u.day, path: u.path };
        for (const [k, n] of Object.entries(u.inc)) setIn(doc, k, (getIn(doc, k) ?? 0) + n);
        daily.set(u._id, doc);
      }
      if (row) rows.push(row);
      if (sample) {
        const day = errs.get(sample.day) ?? {};
        day[sample.fp] ??= sampleOf(sample);
        errs.set(sample.day, day);
      }
    },
    async errSamples(day) {
      return structuredClone(errs.get(day) ?? {});
    },
    async totals(day) {
      return Object.fromEntries([...daily].filter(([, d]) => d.day === day).map(([id, d]) => [id, structuredClone(d)]));
    },
    async markDeploy(day, entry) {
      const id = `${day} *`;
      const doc = daily.get(id) ?? { _id: id, day, path: '*' };
      doc.deploys = newestDeploys([...(doc.deploys ?? []), { ...entry }]);
      daily.set(id, doc);
    },
    async saveGsc(day, doc) {
      gscDocs.set(day, structuredClone({ ...doc, day }));
    },
    async gsc(day) {
      return gscDocs.has(day) ? structuredClone(gscDocs.get(day)) : null;
    },
    async saveHealth(h) {
      health.set(healthKey(h), { ...h });
      for (const [k, r] of health) if (healthOld(r)) health.delete(k);
    },
    async health(now) {
      return mergeHealth([...health.values()], now);
    },
    async deleteBefore({ totalsBefore, rowsBefore, gscBefore }) {
      let totals = 0;
      if (totalsBefore) for (const [id, d] of daily) if (d.day < totalsBefore) (daily.delete(id), totals++);
      if (rowsBefore) for (const day of errs.keys()) if (day < rowsBefore) errs.delete(day);
      if (gscBefore) for (const day of gscDocs.keys()) if (day < gscBefore) gscDocs.delete(day);
      return { totals, rows: rowsBefore ? removeRows((r) => r.day >= rowsBefore) : 0 };
    },
    async oldest() {
      const min = (xs) => xs.reduce((a, b) => (a === null || b < a ? b : a), null);
      return { totalsDay: min([...daily.values()].map((d) => d.day)), rowsDay: min(rows.map((r) => r.day)) };
    },
    async visitRows(visit) {
      return rows.filter((r) => r.visit === visit).map((r) => structuredClone(r));
    },
    async deleteVisit(visit) {
      return removeRows((r) => r.visit !== visit);
    },
  };
}
/** What a store keeps of an error sample. */
function sampleOf(x) {
  return { m: String(x.m).slice(0, 120), f: x.f, l: x.l, c: x.c, path: x.path };
}
function getIn(o, path) {
  return path.split('.').reduce((x, k) => (x != null && Object.hasOwn(x, k) ? x[k] : undefined), o);
}
function setIn(o, path, v) {
  const parts = path.split('.');
  let x = o;
  // Own properties only: a key named "constructor" must not walk into Object.
  for (const k of parts.slice(0, -1)) x = Object.hasOwn(x, k) && x[k] && typeof x[k] === 'object' ? x[k] : (x[k] = {});
  x[parts[parts.length - 1]] = v;
}
const DAY = /^\d{4}-\d{2}-\d{2}$/;

/**
 * Local files, for a small site on one Node process with no database:
 *   <dir>/daily/<day>.json    the day's totals, { "<day> <path>": { ...counters } }
 *   <dir>/rows/<day>.jsonl    one row per line
 *   <dir>/errs/<day>.json     one scrubbed sample per JavaScript error, { "<fp>": { m, f, l, c, path } }
 *   <dir>/gsc/<day>.json      the day's Search Console document (gsc.mjs)
 *   <dir>/health.json         the collector's health record
 * Pass the collector's `timeZone`, so purge() cuts at the same days.
 * Every write is applied in order and the day's file is replaced atomically
 * (written to a temporary file, then renamed). Never point two processes at
 * one directory. Call `purge()` at start and once a day: it deletes files
 * older than the retention (`dailyDays`, `rowsDays`).
 */
export function fileStore(dir, { dailyDays = 730, rowsDays = 180, gscDays = 490, timeZone = 'UTC' } = {}) {
  let queue = Promise.resolve();
  const days = new Map(); // day → Map(_id → doc), loaded on first use
  const fsp = () => import('node:fs/promises');
  const join = (...p) => p.join('/').replace(/\/+/g, '/');
  // Writes, purges and deletions run one after another.
  const serial = (fn) => {
    const next = queue.then(fn);
    queue = next.catch(() => {});
    return next;
  };
  async function load(day) {
    if (days.has(day)) return days.get(day);
    const fs = await fsp();
    let docs = new Map();
    try {
      const json = JSON.parse(await fs.readFile(join(dir, 'daily', `${day}.json`), 'utf8'));
      docs = new Map(Object.entries(json));
    } catch {}
    days.set(day, docs);
    return docs;
  }
  async function replace(file, text) {
    const fs = await fsp();
    await fs.writeFile(file + '.tmp', text);
    await fs.rename(file + '.tmp', file);
  }
  async function writeDay(day, docs) {
    const fs = await fsp();
    await fs.mkdir(join(dir, 'daily'), { recursive: true });
    await replace(join(dir, 'daily', `${day}.json`), JSON.stringify(Object.fromEntries(docs)));
  }
  async function dayFiles(sub, ext) {
    const fs = await fsp();
    let names = [];
    try {
      names = await fs.readdir(join(dir, sub));
    } catch {}
    return names.filter((n) => n.endsWith(ext) && DAY.test(n.slice(0, 10)) && n.length === 10 + ext.length).sort();
  }
  async function readRows(name) {
    const fs = await fsp();
    try {
      return (await fs.readFile(join(dir, 'rows', name), 'utf8')).split('\n').filter(Boolean).map((l) => JSON.parse(l));
    } catch {
      return [];
    }
  }
  // Deletes the day files before the cutoffs; the work of purge and deleteBefore.
  async function removeBefore(totalsBefore, rowsBefore, gscBefore) {
    const fs = await fsp();
    const out = { totals: 0, rows: 0 };
    for (const [sub, cutoff, ext, key] of [['daily', totalsBefore, '.json', 'totals'], ['rows', rowsBefore, '.jsonl', 'rows'], ['errs', rowsBefore, '.json', ''], ['gsc', gscBefore, '.json', '']]) {
      if (!cutoff) continue;
      for (const name of await dayFiles(sub, ext)) {
        const day = name.slice(0, 10);
        if (day >= cutoff) continue;
        await fs.rm(join(dir, sub, name));
        if (sub === 'daily') days.delete(day);
        if (key) out[key]++;
      }
    }
    return out;
  }
  async function readJson(file) {
    const fs = await fsp();
    try {
      const json = JSON.parse(await fs.readFile(file, 'utf8'));
      return json && typeof json === 'object' && !Array.isArray(json) ? json : {};
    } catch {
      return {};
    }
  }
  async function readHealthFile() {
    const fs = await fsp();
    try {
      const json = JSON.parse(await fs.readFile(join(dir, 'health.json'), 'utf8'));
      // An older single record.
      return json && typeof json === 'object' ? ('writeErrors' in json ? { default: json } : json) : {};
    } catch {
      return {};
    }
  }
  // Today in the collector's time zone (pass the same timeZone), minus the days kept.
  const cutoffDay = (now, keep) => new Date(Date.parse(`${dayOf(now, timeZone)}T00:00:00Z`) - keep * 86_400_000).toISOString().slice(0, 10);
  return {
    write({ incs, row, sample }) {
      return serial(async () => {
        const touched = new Set();
        for (const u of incs) {
          const docs = await load(u.day);
          const doc = docs.get(u._id) ?? { day: u.day, path: u.path };
          for (const [k, n] of Object.entries(u.inc)) setIn(doc, k, (getIn(doc, k) ?? 0) + n);
          docs.set(u._id, doc);
          touched.add(u.day);
        }
        for (const day of touched) await writeDay(day, days.get(day));
        if (row) {
          const fs = await fsp();
          await fs.mkdir(join(dir, 'rows'), { recursive: true });
          await fs.appendFile(join(dir, 'rows', `${row.day}.jsonl`), JSON.stringify(row) + '\n');
        }
        if (sample && DAY.test(sample.day)) {
          const fs = await fsp();
          const file = join(dir, 'errs', `${sample.day}.json`);
          const all = await readJson(file);
          if (!Object.hasOwn(all, sample.fp)) {
            all[sample.fp] = sampleOf(sample);
            await fs.mkdir(join(dir, 'errs'), { recursive: true });
            await replace(file, JSON.stringify(all));
          }
        }
      });
    },
    async errSamples(day) {
      await queue;
      return DAY.test(day) ? readJson(join(dir, 'errs', `${day}.json`)) : {};
    },
    markDeploy(day, entry) {
      return serial(async () => {
        if (!DAY.test(day)) return;
        const docs = await load(day);
        const id = `${day} *`;
        const doc = docs.get(id) ?? { day, path: '*' };
        doc.deploys = newestDeploys([...(doc.deploys ?? []), { ...entry }]);
        docs.set(id, doc);
        await writeDay(day, docs);
      });
    },
    saveGsc(day, doc) {
      return serial(async () => {
        if (!DAY.test(day)) return;
        const fs = await fsp();
        await fs.mkdir(join(dir, 'gsc'), { recursive: true });
        await replace(join(dir, 'gsc', `${day}.json`), JSON.stringify({ ...doc, day }));
      });
    },
    async gsc(day) {
      await queue;
      if (!DAY.test(day)) return null;
      const doc = await readJson(join(dir, 'gsc', `${day}.json`));
      return Object.keys(doc).length ? doc : null;
    },
    /** The totals of one day, as { _id: doc }. */
    async daily(day) {
      await queue;
      return structuredClone(Object.fromEntries(await load(day)));
    },
    async totals(day) {
      return this.daily(day);
    },
    /** The rows of one day. */
    async rows(day) {
      await queue;
      return readRows(`${day}.jsonl`);
    },
    /**
     * Deletes the files older than the retention (or the `dailyDays` and
     * `rowsDays` given here). Returns how many.
     */
    purge(now = new Date(), keep = {}) {
      return serial(async () => {
        const r = await removeBefore(cutoffDay(now, keep.dailyDays ?? dailyDays), cutoffDay(now, keep.rowsDays ?? rowsDays), cutoffDay(now, keep.gscDays ?? gscDays));
        return r.totals + r.rows;
      });
    },
    deleteBefore({ totalsBefore, rowsBefore, gscBefore }) {
      return serial(() => removeBefore(totalsBefore, rowsBefore, gscBefore));
    },
    async oldest() {
      await queue;
      const [t] = await dayFiles('daily', '.json');
      const [r] = await dayFiles('rows', '.jsonl');
      return { totalsDay: t ? t.slice(0, 10) : null, rowsDay: r ? r.slice(0, 10) : null };
    },
    async visitRows(visit) {
      await queue;
      const out = [];
      for (const name of await dayFiles('rows', '.jsonl')) out.push(...(await readRows(name)).filter((r) => r.visit === visit));
      return out;
    },
    /** Rewrites (atomically) every rows file that holds the visit. Returns the rows removed. */
    deleteVisit(visit) {
      return serial(async () => {
        let n = 0;
        for (const name of await dayFiles('rows', '.jsonl')) {
          const all = await readRows(name);
          const keep = all.filter((r) => r.visit !== visit);
          if (keep.length === all.length) continue;
          n += all.length - keep.length;
          await replace(join(dir, 'rows', name), keep.map((r) => JSON.stringify(r) + '\n').join(''));
        }
        return n;
      });
    },
    async saveHealth(h) {
      const fs = await fsp();
      await fs.mkdir(dir, { recursive: true });
      // { instance: record }; its own temporary name: a health write may overlap a queued one.
      const file = join(dir, 'health.json');
      const all = await readHealthFile();
      all[healthKey(h)] = h;
      for (const k of Object.keys(all)) if (healthOld(all[k])) delete all[k];
      const tmp = `${file}.${Math.random().toString(16).slice(2)}.tmp`;
      await fs.writeFile(tmp, JSON.stringify(all));
      await fs.rename(tmp, file);
    },
    async health(now) {
      return mergeHealth(Object.values(await readHealthFile()), now);
    },
  };
}

/**
 * Cloudflare Workers Analytics Engine (a dataset binding, e.g. env.EVENTS).
 * Append-only: every counter increment is one data point, and a day's totals
 * are summed by SQL:
 *   SELECT blob2 AS path, blob3 AS key, SUM(double1 * _sample_interval) AS n
 *   FROM <dataset> WHERE blob1 = '2026-10-05' AND blob4 = '' GROUP BY path, key
 * Rows (when there are ids) are one data point each, index = visit id; their
 * blob4 holds the row's data, which is how the query above leaves them out.
 * Analytics Engine keeps data for 3 months and samples at volume: say so in
 * the privacy text. Tested against a stand-in binding only.
 *
 * What it cannot do: delete (no visitor's own rows, no shorter retention than
 * its 3 months), keep a health record, or keep error samples (a JavaScript
 * error's err.<fingerprint> counters are stored; its sample is dropped). A Worker reads its own health with
 * collect.health(); an alert job reads the totals and the last write through
 * the SQL API (health.mjs, analyticsEngineReader).
 */
export function analyticsEngineStore(dataset, { rows = true } = {}) {
  return {
    async write({ incs, row }) {
      for (const u of incs) {
        for (const [key, n] of Object.entries(u.inc)) {
          dataset.writeDataPoint({ indexes: [u.path.slice(0, 96)], blobs: [u.day, u.path.slice(0, 200), key], doubles: [n] });
        }
      }
      if (row && rows) {
        dataset.writeDataPoint({
          indexes: [row.visit],
          blobs: [row.day, row.path.slice(0, 200), row.e, JSON.stringify(row.d).slice(0, 2000), row.view, JSON.stringify(row.entry ?? null).slice(0, 500), row.replay ?? ''],
          doubles: [new Date(row.at).getTime() || 0],
        });
      }
    },
  };
}

/**
 * MongoDB (the official driver's Db): totals in `daily` (kept `dailyDays`),
 * rows in `events` (kept `rowsDays`), both expiring by a TTL index on `at`,
 * the collector's health record in `health` (one document per instance), and
 * JavaScript error samples in `errs` (one document per day and fingerprint,
 * `_id: "<day> <fp>"`, kept `rowsDays`), and Search Console documents in
 * `gsc` (one per day, `_id: "<day>"`, kept `gscDays`, 16 months).
 * Call `await store.init()` once before the first write; it creates the TTL
 * indexes, so no row is ever stored without its expiry.
 */
export function mongoStore(db, { daily = 'web_daily', events = 'web_events', health = 'web_health', errs = 'web_errs', gsc = 'web_gsc', dailyDays = 730, rowsDays = 180, gscDays = 490 } = {}) {
  const oldestDay = async (name) => (await db.collection(name).findOne({}, { sort: { day: 1 }, projection: { day: 1 } }))?.day ?? null;
  return {
    async init() {
      await Promise.all([
        db.collection(daily).createIndex({ at: 1 }, { expireAfterSeconds: dailyDays * 86400 }),
        db.collection(daily).createIndex({ day: 1 }),
        db.collection(events).createIndex({ at: 1 }, { expireAfterSeconds: rowsDays * 86400 }),
        db.collection(events).createIndex({ day: 1, visit: 1 }),
        db.collection(events).createIndex({ visit: 1 }),
        db.collection(errs).createIndex({ at: 1 }, { expireAfterSeconds: rowsDays * 86400 }),
        db.collection(errs).createIndex({ day: 1 }),
        db.collection(gsc).createIndex({ at: 1 }, { expireAfterSeconds: gscDays * 86400 }),
      ]);
    },
    async write({ incs, row, sample }) {
      const writes = incs.map((u) =>
        db.collection(daily).updateOne(
          { _id: u._id },
          // The day, not the moment: on a quiet day the first report's time
          // would date one visitor. The TTL only needs the day.
          { $inc: u.inc, $setOnInsert: { day: u.day, path: u.path, at: new Date(`${u.day}T12:00:00Z`) } },
          { upsert: true },
        ),
      );
      if (row) writes.push(db.collection(events).insertOne(row));
      // The first sample of the day wins; later ones change nothing.
      if (sample) {
        writes.push(db.collection(errs).updateOne(
          { _id: `${sample.day} ${sample.fp}` },
          { $setOnInsert: { day: sample.day, fp: sample.fp, ...sampleOf(sample), at: new Date(`${sample.day}T12:00:00Z`) } },
          { upsert: true },
        ));
      }
      await Promise.all(writes);
    },
    async errSamples(day) {
      const docs = await db.collection(errs).find({ day }).toArray();
      return Object.fromEntries(docs.map((d) => [d.fp, sampleOf(d)]));
    },
    async markDeploy(day, entry) {
      await db.collection(daily).updateOne(
        { _id: `${day} *` },
        { $push: { deploys: { $each: [{ ...entry }], $sort: { at: 1 }, $slice: -DEPLOY_CAP } }, $setOnInsert: { day, path: '*', at: new Date(`${day}T12:00:00Z`) } },
        { upsert: true },
      );
    },
    async saveGsc(day, doc) {
      const { _id, ...rest } = doc ?? {};
      await db.collection(gsc).updateOne({ _id: day }, { $set: { ...rest, day, at: new Date(`${day}T12:00:00Z`) } }, { upsert: true });
    },
    async gsc(day) {
      const d = await db.collection(gsc).findOne({ _id: day });
      if (!d) return null;
      const { _id, at, ...rest } = d;
      return rest;
    },
    async totals(day) {
      const docs = await db.collection(daily).find({ day }).toArray();
      return Object.fromEntries(docs.map((d) => [d._id, d]));
    },
    // One document per collector instance; old ones are dropped on save.
    async saveHealth(h) {
      await db.collection(health).updateOne({ _id: `collector:${healthKey(h)}` }, { $set: { ...h, kind: 'collector' } }, { upsert: true });
      await db.collection(health).deleteMany({ kind: 'collector', savedAt: { $lt: new Date(Date.now() - HEALTH_KEEP_MS).toISOString() } });
    },
    async health(now) {
      return mergeHealth(await db.collection(health).find({ kind: 'collector' }).toArray(), now);
    },
    // The TTL indexes already expire both (Mongo's TTL monitor runs about
    // once a minute); this is for a shorter period or a missing index.
    async deleteBefore({ totalsBefore, rowsBefore, gscBefore }) {
      const t = totalsBefore ? await db.collection(daily).deleteMany({ day: { $lt: totalsBefore } }) : null;
      const r = rowsBefore ? await db.collection(events).deleteMany({ day: { $lt: rowsBefore } }) : null;
      if (rowsBefore) await db.collection(errs).deleteMany({ day: { $lt: rowsBefore } });
      if (gscBefore) await db.collection(gsc).deleteMany({ day: { $lt: gscBefore } });
      return { totals: t?.deletedCount ?? 0, rows: r?.deletedCount ?? 0 };
    },
    async oldest() {
      return { totalsDay: await oldestDay(daily), rowsDay: await oldestDay(events) };
    },
    async visitRows(visit) {
      return db.collection(events).find({ visit }, { projection: { _id: 0 } }).sort({ at: 1 }).toArray();
    },
    async deleteVisit(visit) {
      return (await db.collection(events).deleteMany({ visit }))?.deletedCount ?? 0;
    },
  };
}

/**
 * The tables for sqlStore. Postgres and SQLite (also Cloudflare D1).
 * `sqlStore(…).init()` runs them (create … if not exists).
 */
export const SQL_SCHEMA = {
  postgres: [
    'create table if not exists web_daily (day date not null, path text not null, key text not null, n bigint not null default 0, primary key (day, path, key))',
    'create table if not exists web_events (at timestamptz not null, day date not null, visit text not null, view text not null, path text not null, e text not null, d jsonb not null, entry jsonb, replay text)',
    'create index if not exists web_events_day_visit on web_events (day, visit)',
    'create index if not exists web_events_visit on web_events (visit)',
    'create table if not exists web_health (id text primary key, value text not null)',
    'create table if not exists web_errs (day date not null, fp text not null, m text not null, f text not null, l integer not null, c integer not null, path text not null, primary key (day, fp))',
    'create table if not exists web_deploys (day date not null, sha text not null, at text not null, note text)',
    'create table if not exists web_gsc (day date primary key, value text not null)',
  ],
  sqlite: [
    'create table if not exists web_daily (day text not null, path text not null, key text not null, n integer not null default 0, primary key (day, path, key))',
    'create table if not exists web_events (at text not null, day text not null, visit text not null, view text not null, path text not null, e text not null, d text not null, entry text, replay text)',
    'create index if not exists web_events_day_visit on web_events (day, visit)',
    'create index if not exists web_events_visit on web_events (visit)',
    'create table if not exists web_health (id text primary key, value text not null)',
    'create table if not exists web_errs (day text not null, fp text not null, m text not null, f text not null, l integer not null, c integer not null, path text not null, primary key (day, fp))',
    'create table if not exists web_deploys (day text not null, sha text not null, at text not null, note text)',
    'create table if not exists web_gsc (day text primary key, value text not null)',
  ],
};

/**
 * Postgres or SQLite (also Cloudflare D1) through one function you give it:
 * `query(sql, params) → Promise<row objects>` (an empty array for statements
 * that return nothing). Totals are one row per day, path and counter key.
 *
 *   // node-postgres
 *   sqlStore({ dialect: 'postgres', query: async (sql, p) => (await pool.query(sql, p)).rows })
 *   // Cloudflare D1
 *   sqlStore({ dialect: 'sqlite', query: async (sql, p) => (await env.DB.prepare(sql).bind(...p).all()).results })
 *   // better-sqlite3: all() only for statements that return rows
 *   sqlStore({ dialect: 'sqlite', query: async (sql, p) => { const st = db.prepare(sql); return st.reader ? st.all(...p) : (st.run(...p), []); } })
 *   // node:sqlite (its all() also runs statements that return nothing)
 *   sqlStore({ dialect: 'sqlite', query: async (sql, p) => db.prepare(sql).all(...p) })
 *
 * Call `await store.init()` once (it creates the tables), and enforceRetention
 * (retention.mjs) once a day: SQL has no TTL. Tested against SQLite
 * (node:sqlite) and a stand-in for the Postgres placeholders only.
 */
export function sqlStore({ query, dialect = 'postgres' }) {
  if (typeof query !== 'function') throw new Error('sqlStore: query(sql, params) is required');
  if (dialect !== 'postgres' && dialect !== 'sqlite') throw new Error("sqlStore: dialect must be 'postgres' or 'sqlite'");
  const pg = dialect === 'postgres';
  // $1, $2… for Postgres, ? for SQLite.
  const q = (sql, params = []) => query(pg ? sql.replace(/\?/g, ((i) => () => `$${++i}`)(0)) : sql, params);
  const dayCol = pg ? "to_char(day, 'YYYY-MM-DD')" : 'day';
  const json = (v) => (typeof v === 'string' ? JSON.parse(v) : v);
  const toRow = (r) => {
    const row = { at: r.at instanceof Date ? r.at.toISOString() : r.at, day: r.day, visit: r.visit, view: r.view, path: r.path, e: r.e, d: json(r.d) };
    if (r.entry != null) row.entry = json(r.entry);
    if (r.replay) row.replay = r.replay;
    return row;
  };
  const rowCols = `at, ${dayCol} as day, visit, view, path, e, d, entry, replay`;
  const count = async (sql, params) => Number((await q(sql, params))[0]?.n ?? 0);
  return {
    async init() {
      for (const sql of SQL_SCHEMA[dialect]) await q(sql);
    },
    async write({ incs, row, sample }) {
      const upsert = pg
        ? 'insert into web_daily (day, path, key, n) values (?, ?, ?, ?) on conflict (day, path, key) do update set n = web_daily.n + excluded.n'
        : 'insert into web_daily (day, path, key, n) values (?, ?, ?, ?) on conflict (day, path, key) do update set n = n + excluded.n';
      for (const u of incs) for (const [key, n] of Object.entries(u.inc)) await q(upsert, [u.day, u.path, key, n]);
      if (row) {
        await q('insert into web_events (at, day, visit, view, path, e, d, entry, replay) values (?, ?, ?, ?, ?, ?, ?, ?, ?)', [
          new Date(row.at).toISOString(), row.day, row.visit, row.view, row.path, row.e, JSON.stringify(row.d), row.entry ? JSON.stringify(row.entry) : null, row.replay ?? null,
        ]);
      }
      if (sample) {
        const x = sampleOf(sample);
        await q('insert into web_errs (day, fp, m, f, l, c, path) values (?, ?, ?, ?, ?, ?, ?) on conflict (day, fp) do nothing', [sample.day, sample.fp, x.m, x.f, x.l, x.c, x.path]);
      }
    },
    async errSamples(day) {
      const out = {};
      for (const r of await q('select fp, m, f, l, c, path from web_errs where day = ?', [day])) out[r.fp] = sampleOf({ ...r, l: Number(r.l), c: Number(r.c) });
      return out;
    },
    async totals(day) {
      const out = {};
      for (const r of await q('select path, key, n from web_daily where day = ?', [day])) {
        const id = `${day} ${r.path}`;
        const doc = (out[id] ??= { _id: id, day, path: r.path });
        setIn(doc, r.key, Number(r.n));
      }
      const deploys = await q('select sha, at, note from web_deploys where day = ? order by at', [day]);
      if (deploys.length) (out[`${day} *`] ??= { _id: `${day} *`, day, path: '*' }).deploys = deploys.map((r) => (r.note ? { sha: r.sha, at: r.at, note: r.note } : { sha: r.sha, at: r.at }));
      return out;
    },
    async markDeploy(day, entry) {
      await q('insert into web_deploys (day, sha, at, note) values (?, ?, ?, ?)', [day, entry.sha, entry.at, entry.note ?? null]);
      await q(`delete from web_deploys where day = ? and at not in (select at from web_deploys where day = ? order by at desc limit ${DEPLOY_CAP})`, [day, day]);
    },
    async saveGsc(day, doc) {
      await q('insert into web_gsc (day, value) values (?, ?) on conflict (day) do update set value = excluded.value', [day, JSON.stringify({ ...doc, day })]);
    },
    async gsc(day) {
      const [r] = await q('select value from web_gsc where day = ?', [day]);
      return r ? json(r.value) : null;
    },
    // One row per collector instance ('collector:<id>'); old ones are dropped on save.
    async saveHealth(h) {
      await q('insert into web_health (id, value) values (?, ?) on conflict (id) do update set value = excluded.value', [`collector:${healthKey(h)}`, JSON.stringify(h)]);
      for (const r of await q("select id, value from web_health where id like 'collector:%'")) {
        if (healthOld(JSON.parse(r.value))) await q('delete from web_health where id = ?', [r.id]);
      }
    },
    async health(now) {
      return mergeHealth((await q("select value from web_health where id like 'collector:%'")).map((r) => JSON.parse(r.value)), now);
    },
    async deleteBefore({ totalsBefore, rowsBefore, gscBefore }) {
      const out = { totals: 0, rows: 0 };
      if (totalsBefore) {
        out.totals = await count('select count(*) as n from web_daily where day < ?', [totalsBefore]);
        await q('delete from web_daily where day < ?', [totalsBefore]);
        await q('delete from web_deploys where day < ?', [totalsBefore]);
      }
      if (gscBefore) await q('delete from web_gsc where day < ?', [gscBefore]);
      if (rowsBefore) {
        out.rows = await count('select count(*) as n from web_events where day < ?', [rowsBefore]);
        await q('delete from web_events where day < ?', [rowsBefore]);
        await q('delete from web_errs where day < ?', [rowsBefore]);
      }
      return out;
    },
    async oldest() {
      const [t] = await q(`select ${pg ? "to_char(min(day), 'YYYY-MM-DD')" : 'min(day)'} as d from web_daily`);
      const [r] = await q(`select ${pg ? "to_char(min(day), 'YYYY-MM-DD')" : 'min(day)'} as d from web_events`);
      return { totalsDay: t?.d ?? null, rowsDay: r?.d ?? null };
    },
    async visitRows(visit) {
      return (await q(`select ${rowCols} from web_events where visit = ? order by at`, [visit])).map(toRow);
    },
    async deleteVisit(visit) {
      const n = await count('select count(*) as n from web_events where visit = ?', [visit]);
      await q('delete from web_events where visit = ?', [visit]);
      return n;
    },
  };
}

// --- Forwarding to Umami --------------------------------------------------------

/**
 * Forwards page views (and, if listed, events) to Umami, for its dashboard.
 * Umami gets the path, the referrer's site, the language and a shortened IP
 * for its own location lookup; never the ids, sections or timing. The website
 * id stays on the server. `events` lists the k.js events to forward by name.
 * `clientIp` is the collector's: which header to trust depends on what is in
 * front of the server (defaultClientIp reads the LAST X-Forwarded-For entry).
 */
export function umamiForwarder({ websiteId, endpoint = 'https://cloud.umami.is/api/send', hostname, events = [], clientIp = defaultClientIp }) {
  return async (b, who, request) => {
    if (!websiteId || (b.event !== 'view' && !events.includes(b.event))) return;
    const ua = request.headers.get('user-agent') || 'Mozilla/5.0';
    const ip = clientIp(request) || '';
    const payload = {
      website: websiteId,
      hostname,
      url: b.path,
      language: b.entry?.lang ?? '',
      referrer: b.entry && b.entry.source !== 'direct' && b.entry.source !== 'internal' ? `https://${b.entry.source}/` : '',
      ...(b.event !== 'view' ? { name: b.event } : {}),
      ...(ip ? { ip: shortIp(ip) } : {}),
    };
    try {
      await fetch(endpoint, {
        method: 'POST',
        headers: { 'content-type': 'application/json', 'user-agent': ua },
        body: JSON.stringify({ type: 'event', payload }),
      });
    } catch {
      // Analytics is best-effort.
    }
  };
}

// --- Node http / Express ---------------------------------------------------------

/**
 * Wraps the collector for Node's http server or Express: (req, res) => void.
 * Without `trustProxy` the client's own address headers are dropped and the
 * socket's address is used: anyone can send X-Forwarded-For.
 */
export function toNodeHandler(collect, { trustProxy = false } = {}) {
  return async (req, res) => {
    let status = 204;
    try {
      const headers = new Headers();
      for (const [k, v] of Object.entries(req.headers)) if (typeof v === 'string') headers.set(k, v);
      // trustProxy: true trusts the last X-Forwarded-For entry, which a proxy
      // you run appends; 'cloudflare' also trusts CF-Connecting-IP (only when
      // the origin is not reachable except through Cloudflare). X-Real-IP is
      // never trusted here: a proxy may pass the client's own through.
      headers.delete('x-real-ip');
      if (!trustProxy) headers.delete('x-forwarded-for');
      if (trustProxy !== 'cloudflare') headers.delete('cf-connecting-ip');
      if (!trustProxy && req.socket?.remoteAddress) headers.set('x-forwarded-for', req.socket.remoteAddress);
      const chunks = [];
      let size = 0;
      for await (const c of req) {
        size += c.length;
        if (size > MAX_BYTES) break;
        chunks.push(c);
      }
      // A constant base: the Host header is the client's and may not parse.
      const request = new Request(new URL(req.url || '/', 'http://localhost'), {
        method: req.method,
        headers,
        body: req.method === 'POST' && size <= MAX_BYTES ? Buffer.concat(chunks) : undefined,
      });
      status = (await collect(request)).status;
    } catch {
      // An aborted upload, a malformed request: nothing to store, nothing to say.
    }
    if (!res.headersSent && !res.writableEnded && !res.destroyed) {
      res.writeHead(status, status === 405 ? { allow: 'POST', 'cache-control': 'no-store' } : { 'cache-control': 'no-store' });
      res.end();
    }
  };
}
