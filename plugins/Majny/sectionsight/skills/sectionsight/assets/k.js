/*!
 * k.js: first-party page analytics with no cookies and no client-side
 * fingerprinting. (In ids mode "always" the collector hashes a shortened IP
 * and the user agent on the server; see references/collector.md.)
 * Reference implementation from the sectionsight skill (MIT).
 *
 * Per page view it measures: the view; active seconds per page section (tab
 * visible and input in the last 45 s) and a "read" once a section has had 3;
 * the deepest scroll; link clicks by kind (email, phone, download, internal,
 * outbound, or a kind the page names with data-kcta); [data-kui] controls;
 * dead and rage clicks; copying (e-mail or not and the length, never the
 * text); printing; video plays. Per visit: where it came from, its active
 * time and the goals it reached ([data-kgoal] or the k:goal event); form
 * submits ([data-kform], the form's name only, never a field). On a
 * 404 page (data-k404 on <html> or <body>, or kConfig.notFound): the path
 * asked for and whether the link to it was internal, external or none.
 * Opt-in, off by default: data-errors="on" reports the page's own JavaScript
 * errors, scrubbed (message without strings, numbers, e-mails, URLs or
 * tokens; file name and line), never with ids; data-vitals="on" adds Core
 * Web Vitals buckets (LCP, CLS, INP, TTFB) and the section of the LCP element
 * and of the slowest interaction to the view's first time report;
 * data-consent-counts="on" counts consent.js's banner shown/accept/decline/
 * withdraw, never with ids; data-strip-utm="on" removes utm_* parameters
 * from the address bar once they are read.
 *
 * Nothing is stored in the browser. (One opt-in exception, data-visit-store=
 * "session": with consent, the visit id is kept in sessionStorage for up to
 * 30 idle minutes, so a visit spans the page loads of a multi-page site.)
 * Ids go out only as the mode allows:
 *   never    no ids at all; the collector can only add to the day's totals
 *   consent  a visit id and a view id once the visitor consented
 *   always   a view id, kept in memory for one page view (no consent banner
 *            model; the collector groups views into visits on its own)
 *
 * Off with Global Privacy Control or Do Not Track, in automated browsers
 * (navigator.webdriver), on hosts outside data-hosts, on paths matching
 * data-skip, and in browsers whose owner opened the site with ?k=off.
 *
 * Configuration: data-* attributes on this script tag, or window.kConfig
 * (same names in camelCase) when it is bundled. See references/tracker.md.
 *
 * Page API, all optional (plain events, so they work whether or not k.js runs):
 *   window.dispatchEvent(new CustomEvent('k:route', { detail: location.pathname }))
 *   window.dispatchEvent(new CustomEvent('k:goal', { detail: 'signup' }))
 *   window.dispatchEvent(new Event('k:consent'))       // the consent changed
 *   window.dispatchEvent(new CustomEvent('k:replay', { detail: () => recordingIdOrNull }))
 *   window.__k.deleteMyData() // the visitor's own rows deleted (consent.js calls it)
 *   window.__k.canDelete      // false in mode "never" or with data-delete="off"
 */
(function () {
  'use strict';
  var w = window, d = document, n = navigator;
  if (w.__kStarted) return;

  // --- Configuration ---------------------------------------------------------
  var tag = d.currentScript;
  var ds = (tag && tag.dataset) || {};
  var cfg = w.kConfig || {};
  function opt(name, fallback) {
    var v = cfg[name] !== undefined ? cfg[name] : ds[name];
    return v === undefined || v === '' ? fallback : v;
  }
  function list(v) {
    return Array.isArray(v) ? v : String(v || '').split(',').map(function (s) { return s.trim(); }).filter(Boolean);
  }
  var ENDPOINT = opt('endpoint', '/api/k');
  var IDS = opt('ids', 'consent');
  var CONSENT_KEY = opt('consentKey', 'analytics-consent');
  var CONSENT_VALUE = opt('consentValue', 'granted');
  var CONSENT_MAX_AGE_MS = +opt('consentMaxAgeDays', 365) * 86400000;
  var OPT_OUT_KEY = opt('optOutKey', 'k-off');
  var OPT_OUT_PARAM = opt('optOutParam', 'k');
  var VISIT_KEY = 'k-visit';
  // 'memory' (default): the visit id lives for one page load. 'session': with
  // consent, in sessionStorage until 30 minutes without a report, so it never
  // links separate visits (a tab restored days later gets a new one).
  var VISIT_STORE = opt('visitStore', 'memory');
  var VISIT_IDLE_MS = 30 * 60000;
  var HOSTS = list(opt('hosts', '')).map(function (h) { return h.toLowerCase(); });
  // <toRegExp> (the same in k.js, consent.js, collector.mjs and posthog-guard.mjs; a test checks)
  // A private-path rule: a RegExp, one regex source ("^/account(/|$)"), or
  // "/source/flags" ("/^\/account(\/|$)/i"), spaces trimmed. g and y are
  // dropped; unknown flags, a "/^…" without its closing slash or a source that
  // does not compile throw, so a broken rule never silently matches nothing.
  function toRegExp(v) {
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
  function toRegExps(v) {
    return (Array.isArray(v) ? v : [v]).filter(function (x) { return x instanceof RegExp || (x != null && String(x).trim() !== ''); }).map(toRegExp);
  }
  // </toRegExp>
  var SKIP;
  try {
    SKIP = toRegExps(opt('skip', ''));
  } catch (e) {
    // Fail closed: with a private-path rule that does not parse, nothing is measured.
    if (w.console) console.warn('[k.js] data-skip is not a valid regex, so nothing is measured:', e.message);
    SKIP = [/(?:)/];
  }
  var SECTIONS = opt('sections', '');
  var IDLE_MS = +opt('idleMs', 45000);
  var READ_SECONDS = +opt('readSeconds', 3);
  var SPA = opt('spa', 'auto');
  var DEPTHS = [25, 50, 75, 100];
  var NAME = /^[a-z0-9][a-z0-9_-]{0,23}$/, UI_NAME = /^[a-z0-9][a-z0-9:_-]{0,31}$/;
  // A visit's active seconds, bucketed by these lower edges, so the totals can
  // give a median and "stayed over a minute" without storing any visit.
  var HIST = [0, 5, 10, 20, 30, 60, 120, 300, 600];
  var consentFn = typeof cfg.consent === 'function' ? cfg.consent : null;
  function on(name) { return /^(on|true|1)$/.test(String(opt(name, ''))); }
  var ERRORS = on('errors'), VITALS = on('vitals'), CONSENT_COUNTS = on('consentCounts'), STRIP_UTM = on('stripUtm');
  // Core Web Vitals are sent as bucket indices by these lower edges (ms; CLS unitless).
  var CWV = { lcp: [0, 1000, 1800, 2500, 3000, 4000, 6000], cls: [0, 0.05, 0.1, 0.15, 0.25], inp: [0, 100, 200, 350, 500, 1000], ttfb: [0, 200, 500, 800, 1800] };

  function storageGet(store, key) {
    try { return w[store].getItem(key); } catch (e) { return null; }
  }

  // The owner's own browsers: ?k=off remembers the switch, ?k=on removes it.
  // Storage is touched only when the parameter is in the URL.
  try {
    var sw = new URLSearchParams(location.search).get(OPT_OUT_PARAM);
    if (sw === 'off') localStorage.setItem(OPT_OUT_KEY, '1');
    if (sw === 'on') localStorage.removeItem(OPT_OUT_KEY);
  } catch (e) {}

  if (n.globalPrivacyControl === true || n.doNotTrack === '1' || w.doNotTrack === '1') return;
  if (n.webdriver && String(opt('allowAutomation', '')) !== '1') return;
  if (HOSTS.length && HOSTS.indexOf(location.hostname.toLowerCase()) < 0) return;
  if (storageGet('localStorage', OPT_OUT_KEY) === '1') return;
  w.__kStarted = true;

  // --- Helpers ---------------------------------------------------------------

  // <looksPersonal> (the same in collector.mjs and posthog-guard.mjs; a test checks)
  // Text that may be a person or a credential: an e-mail, a phone or account
  // number, a hex id, or a token (a JWT, a nanoid, a random code). Such a
  // path segment never leaves the browser. A name slug ("jane-doe") or a
  // code under 10 characters reads like any other slug: only data-skip
  // keeps such pages out.
  function looksPersonal(s) {
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
  // </looksPersonal>
  // <scrubError> (the same in collector.mjs; a test checks)
  // An error message as it may be reported, in linear time. Decoded first
  // (percent-escapes, also UTF-8 runs and twice-encoded ones, %u0040, &#64;,
  // the full-width and small at signs), then quoted text emptied (an
  // unterminated quote to the end), then word by word: data: URLs <data>,
  // URLs, localhost and IP hosts, host.tld/… and anything with ?…= (also
  // #, ; and & before the =) <url>, anything with an @ <email>, anything
  // with / or \ <path> (a stack frame keeps its .js file name and line),
  // token-like words <id>; digits made 0, one line. The browser's "Uncaught "
  // and Firefox's "uncaught exception: " are dropped.
  function scrubError(s) {
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
  // A name the page gives (data-kcta, data-kgoal, data-kui) as it may be sent.
  function named(v, re) {
    return typeof v === 'string' && re.test(v) && !looksPersonal(v) ? v : '';
  }
  function skipped(path) {
    for (var i = 0; i < SKIP.length; i++) if (SKIP[i].test(path)) return true;
    return false;
  }
  // The collector's path rule (collector.mjs pagePath): a view it would drop
  // is never started, or the visit's entry and histogram would go astray.
  function measurable(raw) {
    return !skipped(raw) && raw.indexOf('//') < 0 && /^\/[A-Za-z0-9\-._~%/[\]]{0,120}$/.test(cleanPath(raw));
  }
  // The path as it may be reported: token-like segments become [id].
  function cleanPath(path) {
    return path.split('/').map(function (seg) {
      var s = seg;
      try { s = decodeURIComponent(seg); } catch (e) {}
      return seg && looksPersonal(s) ? '[id]' : seg;
    }).join('/').slice(0, 120) || '/';
  }
  function rid() {
    var a = crypto.getRandomValues(new Uint32Array(2));
    return ('00000000' + a[0].toString(16)).slice(-8) + ('00000000' + a[1].toString(16)).slice(-8);
  }
  function consented() {
    if (consentFn) { try { return consentFn() === true; } catch (e) { return false; } }
    if (storageGet('localStorage', CONSENT_KEY) !== CONSENT_VALUE) return false;
    // consent.js dates the answer; an expired one counts as none.
    var at = Date.parse(storageGet('localStorage', CONSENT_KEY + '-at') || '');
    return !(isFinite(at) && Date.now() - at > CONSENT_MAX_AGE_MS);
  }
  function bucketOf(x, edges) {
    var b = 0;
    edges = edges || HIST;
    for (var i = 1; i < edges.length; i++) if (x >= edges[i]) b = i;
    return b;
  }
  function prerendering() { return d.prerendering === true; }

  // --- State -----------------------------------------------------------------
  var view = null, input = 0, timer = 0, since = 0, ticking = false, clicks = [];
  var memoryVisitId = '', replay = typeof w.__kReplay === 'function' ? w.__kReplay : null;
  // Where this page load's visit came from (en 1 on its first view). Consent
  // usually comes after that view, so the first report that carries ids
  // repeats it (en 2) for the visit's rows; the totals counted it already.
  var entryForRows = null;
  // The entry's referrer host and utm_source, resent with a goal of this page
  // load (the collector keeps only their class). Consent counts waiting for a view.
  var entrySrc = null, consentQ = [];
  // Before the SPA patch below: removing utm_* must not look like a route.
  var replaceState = history.replaceState;
  var visit = { first: true, counted: false, active: 0, bucket: 0, goals: {} };

  function visitId() {
    if (VISIT_STORE === 'session') {
      var m = /^([0-9a-f]{16})\.(\d+)$/.exec(storageGet('sessionStorage', VISIT_KEY) || '');
      var vi;
      if (m && Date.now() - +m[2] < VISIT_IDLE_MS) vi = m[1]; // the visit is still going
      else if (m) vi = rid();                                  // it went quiet: a new visit
      else vi = memoryVisitId || rid();                        // nothing stored, or storage blocked
      try { sessionStorage.setItem(VISIT_KEY, vi + '.' + Date.now()); } catch (e) {}
      return (memoryVisitId = vi);
    }
    return (memoryVisitId = memoryVisitId || rid());
  }

  // The ids this report may carry, or null.
  function ids(v) {
    if (IDS === 'always') return { v: v.id };
    if (IDS !== 'consent' || !consented()) return null;
    var out = { vi: visitId(), v: v.id };
    var ph = null;
    try { ph = replay ? replay() : null; } catch (e) {}
    if (typeof ph === 'string' && ph) out.ph = ph.slice(0, 64);
    return out;
  }

  // noIds: a totals-only report (err), whatever the mode and the consent.
  function send(e, data, extra, noIds) {
    var v = view;
    if (!v) return;
    var body = { p: v.path };
    if (extra) for (var x in extra) body[x] = extra[x];
    if (e) body.e = e;
    if (data) body.d = data;
    var withIds = noIds ? null : ids(v);
    if (withIds) {
      for (var y in withIds) body[y] = withIds[y];
      if (entryForRows && body.en !== 1) for (var z in entryForRows) body[z] = entryForRows[z];
      entryForRows = null;
    }
    var json = JSON.stringify(body);
    // A string goes as text/plain, which needs no CORS preflight; the
    // collector parses the JSON itself. (A string, not a Blob: devtools and
    // test browsers can then show the body.)
    try {
      if (n.sendBeacon && n.sendBeacon(ENDPOINT, json)) return;
    } catch (err) {}
    try {
      fetch(ENDPOINT, { method: 'POST', body: json, keepalive: true, headers: { 'content-type': 'text/plain;charset=UTF-8' } })
        .catch(function () {});
    } catch (err) {}
  }

  // --- Sections --------------------------------------------------------------

  // main [data-k], else the page's hero header and each <section> of main.
  function scan() {
    if (SECTIONS) return [].slice.call(d.querySelectorAll(SECTIONS));
    var marked = d.querySelectorAll('main [data-k]');
    return [].slice.call(marked.length ? marked : d.querySelectorAll('main > header, main section'));
  }
  // A section's key: data-k, else 'intro' for a header, else its id, else its
  // heading, made URL-ish and cut at 24 characters.
  function sectionKey(el, i) {
    var h = el.querySelector('h2');
    var raw = el.getAttribute('data-k') || (el.tagName === 'HEADER' ? 'intro' : el.id) || (h ? h.textContent : '');
    var key = String(raw).toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '')
      .replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 24).replace(/-$/, '');
    // A heading can be personal ("Hello, jane@…", a phone number): then its index.
    return key && !looksPersonal(String(raw)) ? key : 's' + (i + 1);
  }
  function observe(v) {
    if (v.io) v.io.disconnect();
    v.io = null;
    v.line = [];
    if (!v.els.length || !w.IntersectionObserver) return;
    v.io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        var i = v.els.indexOf(en.target), j = v.line.indexOf(i);
        if (j >= 0) v.line.splice(j, 1);
        if (en.isIntersecting) v.line.push(i);
      });
      pick(v);
    }, { rootMargin: '-40% 0px -59% 0px' });
    v.els.forEach(function (el) { v.io.observe(el); });
  }
  // Current section: the last to cross a line 40% down the viewport (at the
  // bottom of the page: the last one).
  function pick(v) {
    v.cur = v.bottom ? v.els.length - 1 : v.line.length ? v.line[v.line.length - 1] : v.cur;
    if (v.cur > v.far) v.far = v.cur;
  }
  function rescan(v) {
    v.els = scan();
    v.keys = v.els.map(sectionKey);
    v.cur = -1;
    observe(v);
  }
  function sectionOf(v, node) {
    for (var i = v.els.length - 1; i >= 0; i--) if (v.els[i].contains(node)) return v.keys[i];
    return '';
  }
  function measure() {
    ticking = false;
    var v = view;
    // A router may change the URL before it reports the route: what is
    // measured then is not this view's page.
    if (!v || location.pathname !== v.raw) return;
    // A menu that locks the page fixes the body: the height read then is the lock's.
    if (d.body && d.body.style.position === 'fixed') return;
    var doc = d.documentElement;
    var pct = Math.min(100, Math.round(((w.scrollY + w.innerHeight) / Math.max(doc.scrollHeight, 1)) * 100));
    if (pct > v.depth) v.depth = pct;
    v.bottom = pct >= 98 && w.scrollY > 0;
    pick(v);
  }

  // --- Views and visits --------------------------------------------------------

  // Whether this page load starts a visit. A reload, a back/forward step and a
  // load from a link on this site continue the visit the visitor is already on.
  function startsVisit() {
    var nav = performance.getEntriesByType && performance.getEntriesByType('navigation')[0];
    if (nav && (nav.type === 'reload' || nav.type === 'back_forward')) return false;
    try {
      var ref = d.referrer ? new URL(d.referrer) : null;
      if (ref && ref.host === location.host && measurable(ref.pathname)) return false;
    } catch (e) {}
    return true;
  }

  function begin(raw, reported, again) {
    var els = scan();
    view = {
      id: rid(), raw: raw, reported: reported || raw, path: cleanPath(reported || raw), t0: Date.now(), els: els, keys: els.map(sectionKey),
      io: null, line: [], bottom: false, cur: -1, far: -1, seen: {}, dwell: {}, active: 0, visibleMs: 0,
      depth: 0, depthSent: 0, deads: 0, rages: 0, copies: 0, printed: false, played: false, scans: 0, errs: 0, errSeen: {}, forms: {},
    };
    observe(view);
    measure();
    var extra = null;
    var first = visit.first;
    visit.first = false;
    if (first && startsVisit()) {
      visit.counted = true;
      var utm = {}, ref = '';
      try {
        new URLSearchParams(location.search).forEach(function (val, k) {
          if (/^utm_(source|medium|campaign)$/.test(k) && !looksPersonal(val)) utm[k.slice(4)] = val.slice(0, 60);
        });
      } catch (e) {}
      try { ref = d.referrer ? new URL(d.referrer).hostname : ''; } catch (e) {}
      extra = { en: 1, r: ref, u: utm, l: n.language || '' };
      entryForRows = { en: 2, r: ref, u: utm, l: n.language || '' };
      entrySrc = { gr: ref };
      if (utm.source) entrySrc.gu = utm.source;
    }
    if (first && STRIP_UTM) stripUtm();
    send(null, { of: els.length }, extra);
    // A 404 page: the path asked for (cleaned like every path, never the
    // query) and where the link to it was. An internal one is a broken link.
    var de = d.documentElement;
    if (!again && (cfg.notFound === true || de.hasAttribute('data-k404') || (d.body && d.body.hasAttribute('data-k404')))) {
      var from = 'none';
      try { from = !first ? 'internal' : d.referrer ? (new URL(d.referrer).host === location.host ? 'internal' : 'external') : 'none'; } catch (e) {}
      send('nf', { r: from });
    }
  }

  function goal(name) {
    if (!named(name, NAME) || visit.goals[name]) return;
    visit.goals[name] = true;
    send('goal', { k: name }, entrySrc);
  }

  // data-strip-utm="on": utm_* parameters out of the address bar, the other
  // parameters (as they were written) and the hash kept. `u` without them
  // ("/a?b=1#c" form), or '' when it has none.
  function dropUtm(u) {
    var h = u.indexOf('#'), hash = h < 0 ? '' : u.slice(h), rest = h < 0 ? u : u.slice(0, h);
    var q = rest.indexOf('?'), kept = [], cut = false;
    if (q < 0) return '';
    rest.slice(q + 1).split('&').forEach(function (p) {
      var k = p.split('=')[0];
      try { k = decodeURIComponent(k.replace(/\+/g, ' ')); } catch (e) {}
      if (/^utm_/i.test(k)) cut = true; else if (p) kept.push(p);
    });
    return cut ? rest.slice(0, q) + (kept.length ? '?' + kept.join('&') : '') + hash : '';
  }
  function withoutUtm() { return dropUtm(location.pathname + location.search + location.hash); }
  // Next.js keeps its own copy of the URL. The App Router keeps its tree in
  // history.state (__NA): a URL changed behind its back is written back on
  // the next refresh, and React sees a mismatch when the page renders search
  // params. So: wait until its router owns the entry, then call its patched
  // history.replaceState with a null state, its documented way (it merges
  // its state back and updates useSearchParams). The Pages Router keeps the
  // query in its router (asPath, history.state.as): a shallow
  // next.router.replace, with its own asPath (basePath excluded) minus the
  // tags. The URL is recomputed when the call is made. Elsewhere: the
  // browser's own replaceState (saved before k.js's history patch), with
  // the entry's state unchanged, so no route is seen and nothing dispatched.
  function nextApp(st) { return !!st && typeof st === 'object' && ('__NA' in st || '__PRIVATE_NEXTJS_INTERNALS_TREE' in st); }
  function stripUtm() {
    if (!withoutUtm()) return;
    var app = w.__next_f || (w.next && w.next.appDir) || nextApp(history.state);
    var pages = !app && !!d.getElementById('__NEXT_DATA__');
    function native() { var u = withoutUtm(); if (u) try { replaceState.call(history, history.state, '', u); } catch (e) {} }
    if (!app && !pages) return native();
    var tries = 0, path0 = location.pathname;
    (function wait() {
      if (location.pathname !== path0 || !withoutUtm()) return;
      var r = w.next && w.next.router;
      var ready = app ? nextApp(history.state) : r && typeof r.replace === 'function' && history.state && history.state.__N;
      if (!ready) { if (++tries < 100) setTimeout(wait, 50); else if (pages) native(); return; }
      setTimeout(function () {
        if (location.pathname !== path0) return;
        try {
          if (app) { var u = withoutUtm(); if (u) history.replaceState(null, '', u); }
          else { var a = dropUtm(String(r.asPath || '')); if (a) r.replace(a, a, { shallow: true, scroll: false }); }
        } catch (e) {}
      }, 50);
    })();
  }

  // consent.js's banner events (data-consent-counts="on"): totals only, never ids.
  function consentEvent(k) {
    if (!/^(shown|accept|decline|withdraw)$/.test(k)) return;
    if (view) send('consent', { k: k }, null, true);
    else if (consentQ.length < 4) consentQ.push(k);
  }

  function tick() {
    var v = view;
    if (!v || location.pathname !== v.raw) return;
    // Hydration, a client-side route or a re-render can replace the sections:
    // look for them again (on a page without sections only for its first 10 s).
    if ((v.els.length && !v.els[0].isConnected) || (!v.els.length && v.scans < 10)) {
      v.scans++;
      rescan(v);
    }
    if (Date.now() - input > IDLE_MS) return;
    v.active++;
    visit.active++;
    var k = v.keys[v.cur];
    if (!k) return;
    v.dwell[k] = (v.dwell[k] || 0) + 1;
    if ((v.seen[k] = (v.seen[k] || 0) + 1) === READ_SECONDS) send('read', { s: k, n: v.cur, of: v.els.length });
  }

  function start() {
    if (!view || d.visibilityState !== 'visible') return;
    if (!since) since = Date.now();
    if (!timer) timer = setInterval(tick, 1000);
    input = Date.now();
  }

  // Reports the time since the last report: active and visible seconds,
  // seconds per section, depth thresholds newly crossed, and the visit's move
  // to a higher active-time bucket. Sent on every hide, page leave and route.
  function flush() {
    clearInterval(timer);
    timer = 0;
    var v = view;
    if (!v) { since = 0; return; }
    if (since) { v.visibleMs += Date.now() - since; since = 0; }
    measure();
    var dn = DEPTHS.filter(function (x) { return v.depth >= x && x > v.depthSent; });
    var b = visit.counted ? bucketOf(visit.active) : visit.bucket;
    var cv = cw && !cw.sent && cw.owner === v.id ? vitalsOf(v) : null;
    if (v.active < 1 && v.visibleMs < 1000 && !dn.length && b <= visit.bucket && !cv) return;
    var data = { sec: v.active, vis: Math.round(v.visibleMs / 1000), s: v.keys[v.cur] || '', of: v.els.length };
    if (v.far >= 0) data.n = v.far;
    var secs = [];
    v.keys.forEach(function (k) { if (v.dwell[k] >= 1 && secs.length < 12) secs.push([k, v.dwell[k]]); });
    if (secs.length) data.secs = secs;
    if (dn.length) { data.dn = dn; v.depthSent = dn[dn.length - 1]; }
    if (b > visit.bucket) { data.hb = [visit.bucket, b]; visit.bucket = b; }
    if (cv) { data.cv = cv; cw.sent = true; }
    send('time', data);
    v.active = 0;
    v.visibleMs = 0;
    v.dwell = {};
  }

  // --- Clicks ----------------------------------------------------------------

  var DOWNLOAD = /\.(pdf|zip|dmg|exe|pkg|msi|csv|xlsx?|docx?|pptx?|ics|vcf|mp3|mp4|epub)$/i;

  // What a link is, by where it goes. Never the address of an e-mail or phone link.
  function linkKind(a) {
    var u;
    try { u = new URL(a.getAttribute('href') || '', location.href); } catch (e) { return null; }
    var cta = a.closest('[data-kcta]');
    var kind = cta ? named(cta.getAttribute('data-kcta'), NAME) : '';
    if (u.protocol === 'mailto:') return { k: kind || 'email' };
    if (u.protocol === 'tel:' || u.protocol === 'sms:') return { k: kind || 'phone' };
    if (!/^https?:$/.test(u.protocol)) return kind ? { k: kind } : null;
    var own = u.host === location.host;
    var url = own
      ? (skipped(u.pathname) ? '/[private]' : cleanPath(u.pathname) + (/^#[A-Za-z0-9_-]{1,32}$/.test(u.hash) && !looksPersonal(u.hash) ? u.hash : ''))
      : (u.hostname.replace(/^www\./, '') + cleanPath(u.pathname)).slice(0, 120);
    return { k: kind || (DOWNLOAD.test(u.pathname) ? 'download' : own ? 'nav' : 'outbound'), url: url };
  }

  // A dead or rage click's label: the tag, plus the text only when it is the
  // page's own copy in <main>. Never what a visitor typed.
  function label(x) {
    var tagName = x.tagName.toLowerCase();
    var field = 'input,textarea,select,[contenteditable]';
    if (!x.closest('main') || x.closest(field) || x.querySelector(field)) return tagName;
    var text = String(x.alt || x.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 32);
    return looksPersonal(text) ? tagName : tagName + ':' + text;
  }

  // Controls answer repeated taps by design (a carousel, a stepper, a field).
  var INTERACTIVE = 'a,button,input,select,textarea,label,summary,[role=button],[role=tab],[onclick],[tabindex],[contenteditable]';

  function click(e) {
    var v = view;
    var el = e.target && e.target.closest ? e.target : null;
    // Primary-button clicks, and middle-button ones (auxclick).
    if (!v || !el || (e.type === 'click' ? e.button !== 0 : e.button !== 1)) return;
    var s = sectionOf(v, el);

    var g = el.closest('[data-kgoal]');
    if (g) goal(g.getAttribute('data-kgoal'));

    var control = el.closest('[data-kui]');
    if (control) {
      var det = control.closest('details');
      var name = control.getAttribute('data-kui');
      // A <details> element counts when it opens, not when it closes.
      if (named(name, UI_NAME) && !(det && el.closest('summary') && det.open)) send('ui', { k: name, s: s });
      return;
    }

    var a = el.closest('a[href]');
    if (a) {
      var kind = linkKind(a);
      if (!kind) return;
      kind.s = s;
      kind.t = Math.round((Date.now() - v.t0) / 1000);
      kind.tab = e.ctrlKey || e.metaKey || e.shiftKey || e.button === 1 ? 1 : 0;
      send('cta', kind);
      return;
    }
    if (e.button || el.closest(INTERACTIVE)) return;

    // Rage: three clicks within 0.8 s on one spot (not a triple-click selection).
    var now = Date.now();
    clicks = clicks.filter(function (c) {
      return now - c.t < 800 && Math.abs(c.x - e.clientX) < 30 && Math.abs(c.y - e.clientY) < 30;
    });
    clicks.push({ t: now, x: e.clientX, y: e.clientY });
    if (clicks.length >= 3) {
      clicks = [];
      if (v.rages < 3 && !String(w.getSelection() || '')) {
        v.rages++;
        // Only the page's own headings and images carry text; anything else
        // (a preview that mirrors a form, a chat bubble) is its tag only.
        var known = el.closest('h1,h2,h3,img,picture,strong');
        send('rage', { s: s, label: known ? label(known) : el.tagName.toLowerCase() });
        return;
      }
    }

    // Dead: a click on something that looks clickable and is not.
    if (v.deads >= 5) return;
    var x = el.closest('h1,h2,h3,img,picture,strong');
    if (!x || String(w.getSelection() || '')) return;
    v.deads++;
    send('dead', { s: s, label: label(x) });
  }

  // --- Routes ----------------------------------------------------------------

  function route(detail) {
    if (prerendering()) return;
    // The view is matched to the URL the browser shows (measure and tick
    // compare with it); a router's own path (k:route detail) is only what
    // gets reported.
    var raw = location.pathname;
    var reported = typeof detail === 'string' && detail.charAt(0) === '/' ? detail : raw;
    if (view && view.raw === raw) return;
    if (view) {
      flush();
      if (view.io) view.io.disconnect();
    }
    view = null;
    clicks = [];
    // The load's vitals belong to its first view (none if that page is private).
    var firstRoute = cw && cw.owner === undefined;
    if (firstRoute) cw.owner = 0;
    if (!measurable(raw) || !measurable(reported)) return;
    begin(raw, reported);
    while (consentQ.length) send('consent', { k: consentQ.shift() }, null, true);
    if (firstRoute) cw.owner = view.id;
    start();
  }

  function listen() {
    ['scroll', 'pointerdown', 'pointermove', 'keydown', 'touchstart', 'wheel'].forEach(function (t) {
      w.addEventListener(t, function () { input = Date.now(); }, { passive: true, capture: true });
    });
    w.addEventListener('scroll', function () {
      if (!ticking) { ticking = true; requestAnimationFrame(measure); }
    }, { passive: true });
    d.addEventListener('click', click, true);
    d.addEventListener('auxclick', click, true);
    // A submit of a [data-kform] form: its name, once per form and view,
    // never a field. Paired with a goal of the same name sent when the server
    // confirms, it shows a form whose backend is broken (health.mjs).
    d.addEventListener('submit', function (e) {
      var v = view, f = e.target;
      var name = v && f && f.getAttribute ? f.getAttribute('data-kform') : '';
      if (!named(name, NAME) || v.forms[name]) return;
      v.forms[name] = true;
      send('form', { k: name, s: sectionOf(v, f) });
    }, true);
    d.addEventListener('copy', function () {
      var v = view;
      if (!v || v.copies >= 5) return;
      v.copies++;
      var sel = w.getSelection(), txt = String(sel || '');
      send('copy', { kind: /@/.test(txt) ? 'email' : 'text', n: txt.length, s: sel && sel.anchorNode ? sectionOf(v, sel.anchorNode) : v.keys[v.cur] || '' });
    });
    w.addEventListener('beforeprint', function () {
      var v = view;
      if (!v || v.printed) return;
      v.printed = true;
      send('print', { s: v.keys[v.cur] || '' });
    });
    // Videos: a play (once a view) and watching one to the end. While a
    // playhead moves the visitor is watching, which counts as active.
    d.addEventListener('play', function (e) {
      var v = view;
      if (!v || !(e.target instanceof HTMLVideoElement) || v.played) return;
      v.played = true;
      send('ui', { k: 'video-play', s: sectionOf(v, e.target) });
    }, true);
    d.addEventListener('timeupdate', function (e) {
      if (e.target instanceof HTMLVideoElement && !e.target.paused) input = Date.now();
    }, true);
    d.addEventListener('ended', function (e) {
      if (view && e.target instanceof HTMLVideoElement) send('ui', { k: 'video-end', s: sectionOf(view, e.target) });
    }, true);
    d.addEventListener('visibilitychange', function () {
      if (d.visibilityState === 'hidden') flush(); else start();
    });
    w.addEventListener('pagehide', flush);
    // Back/forward cache restore: the page did not load again, so count a new view.
    w.addEventListener('pageshow', function (e) {
      if (!e.persisted || !view) return;
      var raw = view.raw, reported = view.reported;
      if (view.io) view.io.disconnect();
      begin(raw, reported, true);
      // Restored, not loaded: no LCP or TTFB; CLS and INP start again.
      if (cw) { cw = { owner: view.id, cls: cw.cls === undefined ? undefined : 0 }; }
      start();
    });
    if (ERRORS) {
      w.addEventListener('error', jsError);
      w.addEventListener('unhandledrejection', jsError);
    }
    w.addEventListener('k:route', function (e) { route(e.detail); });
    w.addEventListener('k:goal', function (e) { goal(e.detail); });
    w.addEventListener('k:replay', function (e) { if (typeof e.detail === 'function') replay = e.detail; });
    // Consent withdrawn: the visit id stored for it goes too.
    function consentChanged() {
      if (IDS === 'consent' && !consented()) {
        try { sessionStorage.removeItem(VISIT_KEY); } catch (e) {}
        memoryVisitId = '';
      }
    }
    w.addEventListener('k:consent', consentChanged);
    if (CONSENT_COUNTS) {
      w.addEventListener('consent:ui', function (e) { consentEvent(e.detail); });
      // What consent.js said before k.js ran (it keeps a short list).
      var early = w.__consentUi;
      if (early && early.splice) early.splice(0).forEach(consentEvent);
    }
    w.addEventListener('storage', function (e) { if (e.key === CONSENT_KEY || e.key === null) consentChanged(); });
    if (SPA !== 'off') {
      // Client-side navigation: the router changes the URL, then the page.
      // Report the route a frame later, once the new page is in the DOM; the
      // sections are looked up again if they are not there yet (tick).
      ['pushState', 'replaceState'].forEach(function (m) {
        var orig = history[m];
        history[m] = function () {
          var r = orig.apply(this, arguments);
          setTimeout(function () { route(); }, 0);
          return r;
        };
      });
      w.addEventListener('popstate', function () { route(); });
    }
  }

  // --- JavaScript errors (data-errors="on") -------------------------------------

  // The file as it may be reported: same origin only, its name without the
  // path or query, token-like parts and build hashes as *, "(hidden)" when
  // the decoded name holds an e-mail. Anything but a script file (the
  // page itself, also after a client-side route) is "(inline)".
  function errFile(src) {
    var u;
    try { u = src ? new URL(src, location.href) : null; } catch (e) {}
    if (!u || u.origin !== location.origin) return '';
    var f = u.pathname.split('/').pop() || '';
    if (!/\.[mc]?[jt]sx?$/i.test(f)) return '(inline)';
    try { f = decodeURIComponent(f); } catch (e) {}
    // An e-mail in the decoded name ("chunk-jane.doe%40example.com.js"): hidden.
    if (/[@\uff20\ufe6b]/.test(f)) return '(hidden)';
    // Token-like parts and build hashes (letters and digits mixed, 6+: Vite's
    // "BXk3aF9q", webpack's "9f8e7d6c") as *.
    return f.replace(/[A-Za-z0-9]+/g, function (x) { return looksPersonal(x) || (x.length >= 6 && /\d/.test(x) && /[A-Za-z]/.test(x)) ? '*' : x; })
      .replace(/[^A-Za-z0-9._~*()-]/g, '_').slice(0, 60);
  }
  // Totals only: never ids, at most 5 a view, each fingerprint once.
  function jsError(e) {
    var v = view;
    if (!v || v.errs >= 5) return;
    try {
      var r = e.reason, m = e.message, f = e.filename, l = e.lineno, c = e.colno, at;
      if (e.type === 'unhandledrejection') {
        // Only an Error whose stack names a script of this site.
        at = r && typeof r.stack === 'string' && /(https?:\/\/[^\s()]+?):(\d+):(\d+)/.exec(r.stack);
        if (!at) return;
        m = (r.name || 'Error') + ': ' + r.message;
        f = at[1]; l = +at[2]; c = +at[3];
      }
      if (/^Script error\.?$/.test(m)) return;
      f = errFile(f);
      m = scrubError(m);
      var fp = m + '|' + f + '|' + l;
      if (!f || !m || v.errSeen[fp]) return;
      v.errSeen[fp] = 1;
      v.errs++;
      send('err', { m: m, f: f, l: l | 0, c: c | 0, s: v.keys[v.cur] || '' }, null, true);
    } catch (x) {}
  }

  // --- Core Web Vitals (data-vitals="on") -----------------------------------------

  // The page load's LCP, CLS (largest session window), INP (the longest
  // interaction) and TTFB, observed from the start (buffered). Skipped for a
  // prerendered load; LCP only while the page had not been hidden.
  var cw = null;
  function vitals() {
    var types = (w.PerformanceObserver && PerformanceObserver.supportedEntryTypes) || [];
    var nav = performance.getEntriesByType && performance.getEntriesByType('navigation')[0];
    if (prerendering() || (nav && nav.activationStart > 0)) return;
    var hiddenAt = d.visibilityState === 'hidden' ? 0 : Infinity, observers = [];
    // Entries still queued in an observer (the last interaction) are taken
    // before the report on hide (these listeners come before k.js's flush).
    function drain() { observers.forEach(function (o) { try { o.po.takeRecords().forEach(o.fn); } catch (e) {} }); }
    d.addEventListener('visibilitychange', function (e) { if (d.visibilityState !== 'hidden') return; drain(); if (hiddenAt > e.timeStamp) hiddenAt = e.timeStamp; }, true);
    w.addEventListener('pagehide', drain, true);
    cw = { load: true, cls: types.indexOf('layout-shift') < 0 ? undefined : 0 };
    if (nav && nav.responseStart > 0) cw.ttfb = nav.responseStart;
    function obs(type, fn, o) {
      if (types.indexOf(type) < 0) return;
      try {
        o = o || {};
        o.type = type;
        o.buffered = true;
        var po = new PerformanceObserver(function (list) { list.getEntries().forEach(fn); });
        po.observe(o);
        observers.push({ po: po, fn: fn });
      } catch (e) {}
    }
    obs('largest-contentful-paint', function (en) { if (cw.load && en.startTime < hiddenAt) { cw.lcp = en.startTime; cw.lcpEl = en.element; } });
    obs('layout-shift', function (en) {
      if (en.hadRecentInput || cw.cls === undefined) return;
      if (cw.ss && en.startTime - cw.sl < 1000 && en.startTime - cw.sf < 5000) cw.ss += en.value;
      else { cw.ss = en.value; cw.sf = en.startTime; }
      cw.sl = en.startTime;
      if (cw.ss > cw.cls) cw.cls = cw.ss;
    });
    obs('event', function (en) { if (en.interactionId && !(en.duration <= cw.inp)) { cw.inp = en.duration; cw.inpEl = en.target; } }, { durationThreshold: 16 });
  }
  // Bucket indices, and the section (never a selector, text or URL) of the
  // LCP element and of the slowest interaction's target.
  function vitalsOf(v) {
    var o = {}, any = false;
    function put(m, x) { if (typeof x === 'number' && x >= 0) { o[m] = bucketOf(x, CWV[m]); any = true; } }
    put('lcp', cw.lcp);
    put('cls', cw.cls);
    put('inp', cw.inp);
    put('ttfb', cw.ttfb);
    if ('lcp' in o) o.lcps = cw.lcpEl ? sectionOf(v, cw.lcpEl) : '';
    if ('inp' in o) o.inps = cw.inpEl ? sectionOf(v, cw.inpEl) : '';
    return any ? o : null;
  }

  // The visitor's own rows deleted (consent.js "Delete my visit data"): one
  // request with the visit id and nothing else. The id is sent, never
  // returned, so no other script gets it from this API. Model B: this visit
  // (this page load, or the tab's visit with data-visit-store="session");
  // model C: today's visitor hash, which the collector computes again.
  function deleteMyData() {
    var vi = '';
    if (!w.__k.canDelete) return false;
    if (IDS === 'consent') {
      vi = memoryVisitId || (/^([0-9a-f]{16})\./.exec(storageGet('sessionStorage', VISIT_KEY) || '') || [])[1] || '';
      memoryVisitId = '';
      try { sessionStorage.removeItem(VISIT_KEY); } catch (e) {}
    } else if (IDS === 'always') vi = 'today';
    if (!vi) return false;
    var json = JSON.stringify({ del: vi }), to = ENDPOINT;
    try { if (n.sendBeacon && n.sendBeacon(to, json)) return true; } catch (e) {}
    try { fetch(to, { method: 'POST', body: json, keepalive: true, headers: { 'content-type': 'text/plain;charset=UTF-8' } }).catch(function () {}); } catch (e) {}
    return true;
  }
  // window.__k (a name unlikely to clash). canDelete: whether a deletion can
  // mean anything here (not in mode "never", not with data-delete="off"),
  // which consent.js reads before it offers the button.
  w.__k = { deleteMyData: deleteMyData, canDelete: IDS !== 'never' && String(opt('delete', 'on')) !== 'off' };

  function go() { route(); }
  if (VITALS) vitals();
  listen();
  // A prerendered page counts once it is actually shown.
  if (prerendering()) d.addEventListener('prerenderingchange', go, { once: true });
  else if (d.readyState === 'loading') d.addEventListener('DOMContentLoaded', go, { once: true });
  else go();
})();
