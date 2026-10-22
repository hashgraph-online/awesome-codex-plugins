/**
 * PostHog (session replay, heatmaps) only with consent, and nothing personal
 * in what it sends. Reference implementation from the sectionsight
 * skill (MIT), written against posthog-js 1.438.3; references/posthog.md
 * explains every line and what to re-check on a newer version.
 *
 *   import { startPostHog, stopPostHog, purgePostHog } from './posthog-guard.mjs';
 *   const site = {
 *     token: 'phc_…', hosts: ['example.com'], private: [/^\/account(\/|$)/], origin: 'https://example.com',
 *     consented: () => window.analyticsConsent?.get() === 'granted',   // consent.js
 *   };
 *   const load = () => import('posthog-js');   // or a self-hosted copy of posthog-js/dist/module.mjs
 *   if (site.consented()) startPostHog(site, load); else purgePostHog();
 *
 * `site.consented` must read the current (stored) consent from the storage all tabs
 * share, on every call. references/posthog.md has the wiring per stack.
 */

// --- What a URL may still say ---------------------------------------------------

/**
 * Text that may be a person or a credential: an e-mail, a phone or account
 * number (9+ digits once spaces and dashes are gone; a date has 8), a hex id,
 * or a token (a JWT, a nanoid, a random code). The same rule as k.js and
 * collector.mjs (a test checks that all three agree). A name slug ("jane-doe")
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

/**
 * A URL as it may be stored: token-like path segments replaced, the query
 * reduced to utm_* without personal values, no hash. Relative input stays
 * relative; something that is not a URL ("$direct") is left alone.
 */
export function cleanUrl(raw, origin = 'https://example.invalid') {
  if (!raw || typeof raw !== 'string') return raw;
  // PostHog's own markers ("$direct") are not URLs.
  if (raw.startsWith('$')) return raw;
  const absolute = /^[a-z][a-z0-9+.-]*:/i.test(raw);
  // Anything else is resolved against the page, so "signup?e=…",
  // "?page=2&email=…" and "../reset?token=…" are cleaned too.
  const base = typeof location !== 'undefined' && location.href ? location.href : origin;
  let url;
  try {
    url = new URL(raw, base);
  } catch {
    return '';
  }
  // "//cdn.example.net/a?q": another host, kept as protocol-relative.
  const protocolRelative = raw.startsWith('//');
  const relative = !absolute && !protocolRelative;
  // android-app://…, chrome-extension://…, mailto:…: the scheme and app are enough.
  if (!/^https?:$/.test(url.protocol)) return `${url.protocol}//${url.hostname}`;
  const path = url.pathname
    .split('/')
    .map((seg) => {
      let s = seg;
      try {
        s = decodeURIComponent(seg);
      } catch {}
      return seg && looksPersonal(s) ? '[id]' : seg;
    })
    .join('/');
  const kept = new URLSearchParams();
  url.searchParams.forEach((v, k) => {
    if (k.startsWith('utm_') && !looksPersonal(v)) kept.append(k, v);
  });
  const query = kept.toString() ? `?${kept}` : '';
  if (protocolRelative) return `//${url.host}${path}${query}`;
  return relative ? `${path}${query}` : `${url.origin}${path}${query}`;
}

const URL_KEY = /url|referrer|pathname/i;
// Search terms PostHog reads from a search engine's referrer; Meta's click and
// browser ids ($fbc from fbclid or the _fbc cookie, $fbp from the _fbp cookie,
// read by default since 1.426.0 and 1.433.0); the text of a clicked element
// and of a copied selection, which can be anything on the page.
const DROPPED_KEY = /ph_keyword$|^\$fb[cp](_|$)|^\$el_text$|^\$selected_content$/;
const UTM_KEY = /(^|_)utm_[a-z]+$/;

// What autocapture may keep about a clicked element and its ancestors: the
// tag, its classes, an id, a link target and the position. Everything else
// (text, title, aria-label, data-*, a form's action, an image's src) is
// dropped, whatever the SDK's own masking did.
const CHAIN_KEY = '(?:attr__[A-Za-z0-9_$.-]+(?::[A-Za-z0-9_.-]+)?|[A-Za-z0-9_$-]+)';
const CHAIN_KEY_START = new RegExp(`(${CHAIN_KEY})="`, 'y');
// Classes may contain ";" (Tailwind's w-[calc(1px;2px)]), never a quote.
const CHAIN_HEAD = new RegExp(`([A-Za-z][A-Za-z0-9_-]*)([^"]*?):(?=${CHAIN_KEY}=")`, 'y');
// A quote ends a value only when a key, the next element or the end follows.
// PostHog escapes " in values as \" but not \ itself, so "C:\" looks escaped;
// "=" followed by a bare quote cannot occur inside a value.
const CHAIN_VALUE_END = new RegExp(`"(?=${CHAIN_KEY}="|;[A-Za-z][A-Za-z0-9_-]*[^"]*?:${CHAIN_KEY}="|$)`, 'g');

/** A class list without classes that look personal. */
function cleanClasses(list) {
  return list.filter((c) => c && !/["'<>]/.test(c) && !looksPersonal(c));
}

/** One kept attribute, cleaned, or undefined to drop it. */
function keptAttribute(key, value, origin) {
  if (/^(attr__)?href$/.test(key)) return cleanUrl(value, origin);
  if (/^(attr__id|attr_id)$/.test(key)) return looksPersonal(value) ? undefined : value;
  if (/^(nth-child|nth-of-type|nth_child|nth_of_type|order)$/.test(key)) return /^\d{1,4}$/.test(String(value)) ? value : undefined;
  return undefined;
}

/**
 * Autocapture's element chain ("a.btn:attr__href=\"/x\"nth-child=\"1\";div:…")
 * rebuilt from the allowlist above. Anything it cannot parse is dropped.
 */
export function cleanElementsChain(chain, origin) {
  const out = [];
  let i = 0;
  while (i < chain.length) {
    CHAIN_HEAD.lastIndex = i;
    const head = CHAIN_HEAD.exec(chain);
    if (!head) break;
    i = CHAIN_HEAD.lastIndex;
    const pairs = [];
    for (;;) {
      CHAIN_KEY_START.lastIndex = i;
      const k = CHAIN_KEY_START.exec(chain);
      if (!k) break;
      CHAIN_VALUE_END.lastIndex = CHAIN_KEY_START.lastIndex;
      const end = CHAIN_VALUE_END.exec(chain);
      if (!end) {
        i = chain.length;
        break;
      }
      const slice = chain.slice(CHAIN_KEY_START.lastIndex, end.index);
      // An unescaped quote inside means an attribute this parser cannot read
      // (a name like "x;y" or "hx-on::after") ran into this one: drop it.
      const v = /(^|[^\\])"/.test(slice) ? undefined : keptAttribute(k[1], slice.replace(/\\"/g, '"'), origin);
      if (v !== undefined) pairs.push(`${k[1]}="${String(v).replace(/"/g, '\\"')}"`);
      i = end.index + 1;
      if (chain[i] === ';') {
        i++;
        break;
      }
    }
    const classes = cleanClasses(head[2].split('.'));
    out.push(`${head[1]}${classes.length ? '.' + classes.join('.') : ''}:${pairs.join('')}`);
  }
  return out.join(';');
}

/** Autocapture's $elements (when the chain is not sent as a string), by the same allowlist. */
export function cleanElements(list, origin) {
  return list.map((el) => {
    if (!el || typeof el !== 'object') return null;
    const copy = {};
    if (typeof el.tag_name === 'string') copy.tag_name = el.tag_name;
    if (Array.isArray(el.classes)) copy.classes = cleanClasses(el.classes.map(String));
    if (typeof el.attr__class === 'string') copy.attr__class = cleanClasses(el.attr__class.split(/\s+/)).join(' ');
    for (const [k, v] of Object.entries(el)) {
      if (k === 'tag_name' || k === 'classes' || k === 'attr__class' || (typeof v !== 'string' && typeof v !== 'number')) continue;
      const kept = keptAttribute(k, typeof v === 'string' ? v : String(v), origin);
      if (kept !== undefined) copy[k] = typeof v === 'number' ? v : kept;
    }
    return copy;
  });
}

/**
 * Every URL-shaped property cleaned; search terms, personal utm values and
 * anything about a private page dropped. Covers the places PostHog hides
 * URLs: $elements_chain, $elements, heatmap data keyed by URL, web vitals
 * (one nested object per metric) and the replay's meta event.
 */
export function cleanProperties(props, site) {
  if (!props) return props;
  const out = { ...props };
  const onPrivate = (raw) => onPrivatePage(raw, site);
  // The page before this one was private: nothing about it goes.
  if (typeof out.$prev_pageview_pathname === 'string' && isPrivate(out.$prev_pageview_pathname, site)) {
    for (const k of Object.keys(out)) if (k.startsWith('$prev_pageview_')) delete out[k];
  }
  for (const [k, v] of Object.entries(out)) {
    if (DROPPED_KEY.test(k)) delete out[k];
    else if (typeof v === 'string' && UTM_KEY.test(k) && looksPersonal(v)) delete out[k];
    else if (typeof v === 'string' && URL_KEY.test(k) && k !== '$current_url' && k !== '$pathname' && onPrivate(v)) delete out[k];
    else if (typeof v === 'string' && URL_KEY.test(k) && k !== '$referring_domain') out[k] = cleanUrl(v, site.origin);
  }
  if (typeof out.$elements_chain === 'string') out.$elements_chain = cleanElementsChain(out.$elements_chain, site.origin);
  if (Array.isArray(out.$elements)) out.$elements = cleanElements(out.$elements, site.origin);
  if (out.$heatmap_data && typeof out.$heatmap_data === 'object' && !Array.isArray(out.$heatmap_data)) {
    const byUrl = {};
    for (const [url, points] of Object.entries(out.$heatmap_data)) {
      // Points collected on a private page ride along with the next event elsewhere.
      if (onPrivate(url)) continue;
      const clean = cleanUrl(url, site.origin);
      byUrl[clean] = Array.isArray(byUrl[clean]) && Array.isArray(points) ? [...byUrl[clean], ...points] : points;
    }
    out.$heatmap_data = byUrl;
  }
  for (const k of Object.keys(out)) {
    if (/^\$web_vitals_.+_event$/.test(k) && out[k] && typeof out[k] === 'object') out[k] = cleanProperties(out[k], site);
  }
  // Error tracking: each stack frame names the URL of its script or page (an
  // inline script's frame is the page itself, query included), and messages
  // can quote URLs.
  const urlsIn = (text) => (typeof text === 'string' ? text.replace(/https?:\/\/[^\s"'<>)]+/g, (u) => cleanUrl(u, site.origin)) : text);
  if (Array.isArray(out.$exception_list)) {
    out.$exception_list = out.$exception_list.map((ex) => {
      if (!ex || typeof ex !== 'object') return ex;
      const copy = { ...ex, value: urlsIn(ex.value) };
      const frames = ex.stacktrace?.frames;
      if (Array.isArray(frames)) {
        copy.stacktrace = {
          ...ex.stacktrace,
          frames: frames.map((f) => (f && typeof f === 'object' ? { ...f, filename: cleanUrl(f.filename, site.origin), abs_path: cleanUrl(f.abs_path, site.origin) } : f)),
        };
      }
      return copy;
    });
  }
  for (const k of ['$exception_message', '$exception_source']) if (typeof out[k] === 'string') out[k] = urlsIn(out[k]);
  // Session replay: rrweb's meta event (type 4) carries the page's href.
  if (Array.isArray(out.$snapshot_data)) {
    out.$snapshot_data = out.$snapshot_data.map((ev) => {
      if (!ev || ev.type !== 4 || !ev.data || typeof ev.data.href !== 'string') return ev;
      return { ...ev, data: { ...ev.data, href: cleanUrl(ev.data.href, site.origin) } };
    });
  }
  return out;
}

/** Whether a path is private. A rule that does not parse counts as matching (fail closed). */
export function isPrivate(pathname, site) {
  let rules;
  try {
    rules = toRegExps(site.private ?? []);
  } catch {
    return true;
  }
  return rules.some((re) => re.test(pathname));
}

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

// Attributes whose value is always a URL (or a list of them).
const URL_ATTR = /^(href|src|action|formaction|poster|cite|data|xlink:href|background|lowsrc|longdesc|itemid|manifest|codebase|archive|profile|data-(src|href|url|link|background|poster))$/i;
const SRCSET_ATTR = /^(srcset|imagesrcset|data-srcset)$/i;

/** A fragment that is a plain anchor ("#faq", "#icon"), or "" when it may carry data. */
function safeHash(h) {
  return /^#[A-Za-z0-9_:.-]{1,64}$/.test(h) && !looksPersonal(h.slice(1)) ? h : '';
}

/** One URL as it may be recorded: data: and blob: kept, a plain anchor kept. */
function maskUrl(u, origin) {
  const t = u.trim();
  if (!t || /^(data|blob):/i.test(t)) return u;
  if (t.charAt(0) === '#') return safeHash(t) || '#';
  const hash = t.indexOf('#') >= 0 ? safeHash(t.slice(t.indexOf('#'))) : '';
  const clean = cleanUrl(t, origin);
  return /^(https?:\/\/|\/|\.)/.test(clean) || !/:/.test(clean) ? clean + hash : clean;
}

/** A srcset: "url [descriptor], …", where a data: URL may itself contain commas. */
function maskSrcset(value, origin) {
  const out = [];
  const re = /\s*(data:[^\s]*|[^\s,][^\s]*?)(?=[\s,]|$)([^,]*)(,|$)/gy;
  let m;
  while (re.lastIndex < value.length && (m = re.exec(value))) {
    if (!m[0]) break;
    out.push((maskUrl(m[1].replace(/,$/, ''), origin) + m[2]).trim());
  }
  return out.join(', ');
}

// A quoted URL inside CSS (image-set("…")) or an inline handler (location='…').
const QUOTED_URL = /(["'])((?:https?:)?\/[^"'\s]*|\.{1,2}\/[^"'\s]*)\1/g;
// Attributes that describe the page's structure or rendering, left as they
// are: SVG geometry, integrity hashes, dates, ARIA and form plumbing. Every
// other value is cleaned of URLs and blanked when it looks personal.
const STRUCTURAL_ATTR = /^(d|viewbox|points|transform|path|integrity|datetime|type|role|lang|dir|width|height|x|y|x1|x2|y1|y2|cx|cy|r|rx|ry|dx|dy|fill|stroke|stroke-[\w-]+|fill-[\w-]+|opacity|offset|stop-color|stop-opacity|preserveaspectratio|gradientunits|gradienttransform|patternunits|clip-path|mask|filter|crossorigin|rel|media|sizes|loading|decoding|tabindex|colspan|rowspan|span|min|max|step|maxlength|minlength|autocomplete|inputmode|enterkeyhint|charset|http-equiv|as|fetchpriority|referrerpolicy|sandbox|allow|target|method|enctype|accept|aria-hidden|aria-expanded|aria-selected|aria-checked|aria-pressed|aria-current|aria-level|aria-live|hidden|disabled|checked|selected|readonly|required|open|draggable|spellcheck|translate|contenteditable|xmlns|xmlns:\w+|version|class|style)$/i;
// URLs inside free text ("Reset at https://…?token=… now", '/reset?token=…').
const TEXT_URL = /(?:https?:)?\/\/[^\s"'<>)]+|(^|[\s"'(=])(\/[^\s"'<>]*\?[^\s"'<>]*)/g;

/** Free text with every URL in it cleaned, or "" when it still looks personal. */
function maskText(value, origin) {
  const t = value.replace(TEXT_URL, (m, pre, path) => (path !== undefined ? pre + maskUrl(path, origin) : maskUrl(m, origin)));
  return looksPersonal(t) ? '' : t;
}

/** url(…) (quoted, or unquoted with balanced parentheses) and quoted URLs such as image-set("…"). */
function maskCss(value, origin) {
  return value
    .replace(/url\(\s*(?:"([^"]*)"|'([^']*)'|((?:[^()\s'"]|\([^()]*\))*))\s*\)/gi, (m, dq, sq, bare) => {
      const u = dq ?? sq ?? bare ?? '';
      const q = dq !== undefined ? '"' : sq !== undefined ? "'" : '';
      return `url(${q}${maskUrl(u, origin)}${q})`;
    })
    .replace(QUOTED_URL, (m, q, u) => `${q}${maskUrl(u, origin)}${q}`);
}

/** Whether a value of any attribute reads as a URL: absolute, or a path or relative link with a query or fragment. */
function urlLike(v) {
  const t = v.trim();
  if (/\s/.test(t)) return false;
  return /^[a-z][a-z0-9+.-]*:\/\//i.test(t) || /^\/\//.test(t) || (/^(\/|\.{1,2}\/)/.test(t) && /[?#]/.test(t)) || (/^[\w.-]+\/[^?#]*[?#]/.test(t));
}

/**
 * The recorder's attribute mask: every URL the recorded page holds, cleaned
 * with cleanUrl, whatever the attribute is called (href, data-src, lowsrc,
 * itemid…, or any value that reads as a URL with a query or fragment);
 * srcset lists part by part; url(…) and quoted URLs in style; a refresh
 * target in <meta content>. data: and blob: URLs and plain #anchors stay.
 */
export function maskAttribute(name, value, origin) {
  if (typeof value !== 'string' || !value) return value;
  if (/^ping$/i.test(name)) return value.split(/\s+/).filter(Boolean).map((u) => maskUrl(u, origin)).join(' ');
  if (URL_ATTR.test(name)) return maskUrl(value, origin);
  if (SRCSET_ATTR.test(name)) return maskSrcset(value, origin);
  if (/^style$/i.test(name)) return maskCss(value, origin);
  // <meta http-equiv="refresh" content="0; URL='/next?…'">: keep the shape.
  const refresh = /^(\s*\d+\s*;\s*url\s*=\s*)(['"]?)(.*?)\2(\s*)$/i.exec(value);
  if (refresh) return `${refresh[1]}${refresh[2]}${maskUrl(refresh[3], origin)}${refresh[2]}${refresh[4]}`;
  if (urlLike(value)) return maskUrl(value, origin);
  // <meta content="https://…">, og:url and the like.
  if (/^content$/i.test(name) && /^\s*\/\S*$/.test(value)) return maskUrl(value, origin);
  // A class token that looks personal ("user-jane@example.com") goes, the rest stays.
  if (/^class$/i.test(name)) return value.split(/\s+/).filter((c) => c && !looksPersonal(c)).join(' ');
  if (STRUCTURAL_ATTR.test(name)) return value;
  // Everything else (title, alt, aria-label, data-*, x-data, hx-vals, for,
  // headers, srcdoc, inline handlers, custom attributes): URLs in it
  // cleaned, and blanked when it still holds an e-mail, a phone number or a token.
  return maskText(value.replace(QUOTED_URL, (m, q, u) => `${q}${maskUrl(u, origin)}${q}`), origin);
}

function onPrivatePage(raw, site) {
  try {
    const url = new URL(raw, site.origin);
    const ours = (site.hosts ?? []).includes(url.hostname) || url.origin === site.origin;
    return ours && isPrivate(url.pathname, site);
  } catch {
    return false;
  }
}

/**
 * before_send. Nothing leaves without current (stored) consent, read on every event
 * from the storage all tabs share: a withdrawal in any tab stops every tab at
 * once, whatever state its PostHog is in. Drops anything captured on, or
 * about, a private page (a client-side route can land there after init), and
 * cleans every URL.
 */
export function makeBeforeSend(site) {
  return (capture) => {
    if (!capture) return capture;
    if (!site.consented()) return null;
    if (isPrivate(location.pathname, site)) return null;
    for (const page of [capture.properties?.$pathname, capture.properties?.$current_url]) {
      if (typeof page === 'string' && onPrivatePage(page, site)) return null;
    }
    return {
      ...capture,
      properties: cleanProperties(capture.properties, site),
      $set: cleanProperties(capture.$set, site),
      $set_once: cleanProperties(capture.$set_once, site),
    };
  };
}

// --- Loading, following the consent, stopping -----------------------------------

/** Set once PostHog has started fresh after consent; purgePostHog removes it. */
export const FRESH_KEY = 'ph-fresh';

/**
 * Removes what PostHog keeps in the browser: its ph_<token>_posthog cookie
 * (on the parent domain too) and its localStorage / sessionStorage keys. It
 * KEEPS __ph_opt_in_out_<token>: a bare 0/1 with no identifier, which PostHog
 * in every other open tab reads; deleting the opt-out written on withdrawal
 * would switch those tabs back on.
 */
export function purgePostHog() {
  try {
    const names = document.cookie.split(';').map((c) => c.split('=')[0].trim()).filter((n) => /^ph_.+_posthog$/.test(n));
    // Every suffix of the host down to two labels: a cookie set on
    // .example.co.uk is only removed with that exact Domain.
    const labels = location.hostname.split('.');
    const domains = [''];
    for (let i = 0; i <= labels.length - 2; i++) domains.push(`; Domain=${labels.slice(i).join('.')}`);
    for (const name of names) for (const domain of domains) document.cookie = `${name}=; Max-Age=0; Path=/${domain}`;
  } catch {}
  for (const store of ['localStorage', 'sessionStorage']) {
    try {
      const s = window[store];
      const keys = Array.from({ length: s.length }, (_, i) => s.key(i));
      for (const k of keys) if (k && (k.startsWith('ph_') || k === FRESH_KEY)) s.removeItem(k);
    } catch {}
  }
}

/** The options. `pathname` is the page PostHog starts on. */
export function posthogConfig(site, pathname) {
  return {
    // A same-origin proxy (posthog-proxy.mjs), so ad blockers and CSP stay simple.
    api_host: site.apiHost ?? '/ingest',
    ui_host: site.uiHost ?? 'https://eu.posthog.com',
    capture_pageview: 'history_change',
    capture_pageleave: true,
    respect_dnt: true,
    before_send: makeBeforeSend(site),
    // Ad click ids (gclid, fbclid…) and these parameters become "<masked>" in
    // every URL the SDK builds, $initial_* included.
    mask_personal_data_properties: true,
    custom_personal_data_properties: ['email', 'sig', 'signature', 'exp', 'token', 'ref', 'code', 'key', 'auth', 'session'],
    disable_capture_url_hashes: true,
    disableDeviceModel: true,
    // Autocapture keeps no element text ($el_text): a button or link can show
    // a name, an e-mail or an order number. before_send drops it as well.
    mask_all_text: true,
    // ...and no attributes of the clicked element (a form's action, an
    // image's signed src, data-user="…"); before_send keeps only an
    // allowlist anyway. This also drops link targets from autocapture.
    mask_all_element_attributes: true,
    // The recorder and other extensions load from the exact version this SDK
    // was built with (/static/<version>/recorder.js), never an unversioned
    // fallback that could be a newer, untested build.
    strict_script_versioning: true,
    // When opted out (consent withdrawn), PostHog keeps nothing in the browser.
    opt_out_persistence_by_default: true,
    // No /flags call: /flags carries the first URL a browser saw, outside
    // before_send. Turn it back on only if the site uses feature flags.
    advanced_disable_feature_flags: true,
    // Replay: every input masked, no console, and no network request whatever
    // the project settings say. The recorder also runs page URLs through
    // maskCapturedNetworkRequestFn, as bare { name } objects; those pass.
    disable_session_recording: isPrivate(pathname, site),
    enable_recording_console_log: false,
    session_recording: {
      maskAllInputs: true,
      // The recorder stores links and sources as absolute URLs, so even
      // <a href="#faq"> carries the page's query string. Clean every URL
      // attribute of the recorded page.
      // Never add maskAllElementAttributes: since 1.413.3 it wins and this
      // function is silently ignored.
      maskAttributeFn: (name, value) => maskAttribute(name, value, site.origin),
      recordHeaders: false,
      recordBody: false,
      maskCapturedNetworkRequestFn: (r) => (r.entryType || r.initiatorType || r.method ? null : r),
    },
    // Exception messages are whatever the code put in them, URLs and names
    // included. Off unless the owner wants error tracking (site.exceptions);
    // then before_send cleans the stack frames' URLs.
    capture_exceptions: site.exceptions === true,
    capture_heatmaps: true,
    capture_dead_clicks: true,
    // Page speed (Core Web Vitals) goes to PostHog only when the owner said
    // yes to page speed (site.webVitals, the same answer as k.js data-vitals).
    capture_performance: { web_vitals: site.webVitals === true, network_timing: false },
    disable_surveys: true,
    // Every event leaves when it is captured: nothing waits in a queue that a
    // withdrawal (or the reload after it) would still send.
    request_batching: false,
  };
}

let ready = null;
let identified = false;

/** Global Privacy Control or Do Not Track: PostHog never loads, whatever was stored. */
export function asksNotToBeTracked() {
  return navigator.globalPrivacyControl === true || navigator.doNotTrack === '1' || window.doNotTrack === '1';
}

/**
 * Loads and starts PostHog, once consent is given. `load` returns the module
 * (() => import('posthog-js')), so nothing of PostHog is downloaded before.
 * `onRecording(getId)` is optional: k.js's 'k:replay' takes it, so a visit's
 * row names the recording only when PostHog really sent one.
 */
export function startPostHog(site, load) {
  // A private-path rule that does not parse is the owner's mistake: say so
  // loudly, and never start. No throw: the page's other consent wiring
  // (listeners, onWithdraw, a React effect) must keep working.
  try {
    toRegExps(site.private ?? []);
  } catch (err) {
    console.error('[posthog-guard] site.private is not a valid regex, so PostHog stays off:', err.message);
    return Promise.resolve(null);
  }
  if (typeof window === 'undefined' || !site.token || !site.consented() || asksNotToBeTracked()) return Promise.resolve(null);
  if (!(site.hosts ?? []).includes(location.hostname) || isPrivate(location.pathname, site)) return Promise.resolve(null);
  if (ready) return ready.then((ph) => (ph && follow(ph, site), ph));
  // Whatever an older setup stored before consent must not carry over.
  let fresh = null;
  try {
    fresh = localStorage.getItem(FRESH_KEY);
  } catch {}
  if (fresh !== '1') {
    purgePostHog();
    try {
      localStorage.setItem(FRESH_KEY, '1');
    } catch {}
  }
  ready = load().then((mod) => {
    const posthog = mod.default ?? mod;
    posthog.init(site.token, posthogConfig(site, location.pathname));
    follow(posthog, site);
    const shipped = new Set();
    posthog.on?.('eventCaptured', (e) => {
      if (e?.event === '$snapshot' && typeof e.properties?.$session_id === 'string') shipped.add(e.properties.$session_id);
    });
    const recording = () => {
      const id = posthog.get_session_id();
      return shipped.has(id) ? id : null;
    };
    // k.js may start before or after this: leave the getter where it looks.
    window.__kReplay = recording;
    window.dispatchEvent(new CustomEvent('k:replay', { detail: recording }));
    const again = () => follow(posthog, site);
    window.addEventListener('consent:changed', again);
    window.addEventListener('storage', again);
    window.addEventListener('pageshow', (e) => e.persisted && again());
    // A client-side route into a private page stops the recording (before_send
    // drops what is captured there anyway); back out, it resumes.
    window.addEventListener('popstate', again);
    window.addEventListener('k:route', again);
    for (const m of ['pushState', 'replaceState']) {
      const orig = history[m];
      history[m] = function (...args) {
        const r = orig.apply(this, args);
        setTimeout(again, 0);
        return r;
      };
    }
    return posthog;
  });
  return ready;
}

/** Puts a loaded PostHog in the state the consent and the current page call for. */
export function follow(posthog, site) {
  if (!site.consented()) {
    posthog.stopSessionRecording();
    if (identified || !posthog.has_opted_out_capturing()) {
      // A new identity first, so consent given later never brings this one
      // back; then the opt-out, LAST, because reset() clears it.
      posthog.reset(true);
      posthog.opt_out_capturing();
      identified = false;
    }
    // This tab's own storage too: sessionStorage is per tab, so the tab
    // that withdrew cannot clear PostHog's window id here.
    purgePostHog();
    return;
  }
  identified = true;
  if (posthog.has_opted_out_capturing()) posthog.opt_in_capturing({ captureEventName: null });
  if (isPrivate(location.pathname, site)) posthog.stopSessionRecording();
  else if (!posthog.sessionRecordingStarted()) posthog.startSessionRecording();
}

/**
 * Consent withdrawn: stop, forget this browser, opt out. The order matters:
 * reset() clears PostHog's stored consent along with the identity, so the
 * opt-out comes last. Reload the page after this.
 */
export async function stopPostHog() {
  const posthog = ready ? await ready.catch(() => null) : null;
  if (posthog) {
    posthog.stopSessionRecording();
    posthog.reset(true);
    posthog.opt_out_capturing();
    identified = false;
  }
  purgePostHog();
}
