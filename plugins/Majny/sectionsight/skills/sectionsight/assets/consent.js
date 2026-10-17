/*!
 * consent.js: a small consent banner, designed around the EDPB cookie-banner
 * taskforce report (2023) and CNIL guidance; have its texts reviewed.
 * Reference implementation from the sectionsight skill (MIT).
 *
 * - Declining is exactly as easy and as visible as accepting: two buttons of
 *   the same size and style, Decline first, no "X" that means neither.
 * - Nothing that needs consent runs before Accept. The choice itself is
 *   stored without consent (it is needed to honour it).
 * - Withdrawing is as easy as giving: any element with data-consent-open
 *   (a "Privacy settings" link at the bottom of every page) brings the
 *   banner back, and Decline then withdraws.
 * - The answer expires after 12 months and is asked again.
 * - Global Privacy Control or Do Not Track count as a refusal: no banner, and
 *   get() answers 'denied' even after an earlier Accept.
 * - Not shown on paths in data-skip (pages that never run analytics).
 * - A withdrawal reloads the page after the onWithdraw hook, so no code that
 *   was allowed to run stays in memory.
 * - Reopened after an Accept, it also offers "Delete my visit data" (with
 *   k.js on the page; deleteButton: false turns it off): k.js asks the
 *   collector to delete this visit's rows, then consent is withdrawn.
 *
 * Configuration: data-* attributes on this script tag or window.consentConfig
 * (camelCase): key, grantedValue, deniedValue, maxAgeDays, skip (one regex;
 * "/source/i" with flags), reloadOnWithdraw, deleteButton, styles, styleNonce,
 * texts, and
 * the hooks onGranted, onDecline,
 * onWithdraw. See references/consent.md. Texts MUST be edited: they have to
 * say what Accept turns on, for how long data is kept, and where the choice
 * can be changed, or the consent is not informed.
 *
 * API (window.analyticsConsent): get() → 'granted' | 'denied' | null,
 * set('granted' | 'denied'), open(). Events on window: 'consent:changed'
 * (detail: the choice) and 'k:consent' (for k.js); 'consent:open' opens it;
 * 'consent:ui' (detail 'shown' | 'accept' | 'decline' | 'withdraw', also
 * kept in window.__consentUi) for k.js's data-consent-counts.
 */
(function () {
  'use strict';
  var w = window, d = document, n = navigator;
  if (w.analyticsConsent) return;

  var tag = d.currentScript;
  var ds = (tag && tag.dataset) || {};
  var cfg = w.consentConfig || {};
  function opt(name, fallback) {
    var v = cfg[name] !== undefined ? cfg[name] : ds[name];
    return v === undefined || v === '' ? fallback : v;
  }
  var KEY = opt('key', 'analytics-consent');
  var AT_KEY = KEY + '-at';
  var GRANTED = opt('grantedValue', 'granted');
  var DENIED = opt('deniedValue', 'denied');
  var MAX_AGE_MS = +opt('maxAgeDays', 365) * 86400000;
  // <toRegExp> (the same in k.js, consent.js, collector.mjs and posthog-guard.mjs; a test checks)
  // A private-path rule: a RegExp, one regex source ("^/account(/|$)"), or
  // "/source/flags" ("/^\/account(\/|$)/i"), spaces trimmed. g and y are
  // dropped; unknown flags, a "/^…" without its closing slash or a source that
  // does not compile throw, so a broken rule never silently matches nothing.
  function toRegExp(v) {
    if (v instanceof RegExp) return new RegExp(v.source, v.flags.replace(/[gy]/g, ''));
    var s = String(v).trim(), m = /^\/(.+)\/([A-Za-z]*)$/.exec(s);
    // "^/account, ^/reset": a list, which would be one regex matching neither.
    if (/,\s*[\^\/]/.test(s)) throw new Error('a comma-separated list; join the paths with | in one regex: ' + s);
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
  var SKIP, skipError = '';
  try {
    SKIP = toRegExps(opt('skip', ''));
  } catch (e) {
    // Fail closed: with a private-path rule that does not parse, every page
    // counts as private, so the banner shows only when opened and nobody is
    // asked. On a development host (or with ?k-debug) it says so on the page.
    skipError = e.message;
    if (w.console) console.warn('[consent.js] skip is not a valid regex, so the banner stays hidden:', e.message);
    SKIP = [/(?:)/];
  }
  var RELOAD = String(opt('reloadOnWithdraw', 'true')) !== 'false';
  // "Delete my visit data" next to Decline once consent was given (k.js deletes).
  var DELETE = String(opt('deleteButton', 'true')) !== 'false';
  // Where the banner lives: 'start' of <body> (keyboard users reach it first),
  // or 'end' for a <body> a framework hydrates (React, Next.js): a node put
  // before its children makes hydration fail. With 'end', the banner that
  // shows by itself takes focus instead (without scrolling).
  var AT_END = opt('mount', 'start') === 'end';
  // The default look (the same rules as assets/consent.css).
  var CSS =
    '.consent-banner{position:fixed;left:0;right:0;bottom:0;z-index:var(--consent-z,45);padding:12px;font:inherit;box-sizing:border-box;max-height:100vh;max-height:100dvh;overflow-y:auto}' +
    '.consent-banner__inner{max-width:440px;margin-left:auto;background:var(--consent-bg,#111);color:var(--consent-fg,#fff);border-radius:14px;padding:16px;border:1px solid rgba(255,255,255,.2);box-shadow:0 12px 40px rgba(0,0,0,.35)}' +
    '.consent-banner__title{font-weight:600;margin:0 0 6px}' +
    '.consent-banner__body{margin:0 0 12px;font-size:.9em;opacity:.85}' +
    '.consent-banner__body a{color:inherit;text-decoration:underline}' +
    '.consent-banner__buttons{display:flex;gap:12px}' +
    '.consent-banner__more{margin-top:12px}' +
    '.consent-banner__button{flex:1;min-height:44px;border-radius:999px;border:1px solid currentColor;background:transparent;color:inherit;font:inherit;font-weight:600;cursor:pointer}';
  function place() { if (AT_END) d.body.appendChild(live); else d.body.insertBefore(live, d.body.firstChild); }
  // Defaults, overridden one by one by data-* or consentConfig.texts.
  var TEXT = {
    title: opt('title', 'We measure how people use this site.'),
    body: opt('body', 'EDIT THIS: say what Accept turns on, how long it is kept, and that the choice can be changed at the bottom of every page. Without consent we only count totals, with no cookies and no identifiers.'),
    decline: opt('decline', 'Decline'),
    accept: opt('accept', 'Accept'),
    details: opt('details', 'Details'),
    deleteData: opt('deleteData', 'Delete my visit data'),
    detailsHref: opt('detailsHref', '/privacy'),
  };
  if (cfg.texts) for (var t in cfg.texts) if (cfg.texts[t]) TEXT[t] = cfg.texts[t];

  // The answer when the browser refused to store it: it holds for this page
  // load, unless a newer one is stored meanwhile (another tab).
  var unstored = null;

  function storageGet(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function asksNotToBeTracked() { return n.globalPrivacyControl === true || n.doNotTrack === '1' || w.doNotTrack === '1'; }

  /** The visitor's standing choice, or null when there is none or it expired. */
  function get() {
    // Global Privacy Control / Do Not Track: a refusal, whatever was stored.
    if (asksNotToBeTracked()) return 'denied';
    var stored = storageGet(KEY);
    var at = Date.parse(storageGet(AT_KEY) || '');
    var valid = stored === GRANTED || stored === DENIED;
    var now = Date.now();
    if (unstored && !(valid && isFinite(at) && at > unstored.at)) {
      return now - unstored.at > MAX_AGE_MS ? null : unstored.choice === GRANTED ? 'granted' : 'denied';
    }
    if (!valid) return null;
    // A choice with no date (an older setup) counts, and ages from now on:
    // it is dated on load (below), so it expires like any other.
    if (isFinite(at) && now - at > MAX_AGE_MS) return null;
    return stored === GRANTED ? 'granted' : 'denied';
  }

  function set(choice) {
    var value = choice === 'granted' ? GRANTED : DENIED;
    try {
      localStorage.setItem(KEY, value);
      localStorage.setItem(AT_KEY, new Date().toISOString());
      unstored = null;
    } catch (e) {
      unstored = { choice: value, at: Date.now() };
    }
    w.dispatchEvent(new CustomEvent('consent:changed', { detail: choice }));
    w.dispatchEvent(new Event('k:consent'));
  }

  // An expired answer is removed, so every reader of the storage (k.js too)
  // sees no answer, and the banner asks again. An answer without a date is
  // dated now, so it expires maxAgeDays from today.
  (function expire() {
    var stored = storageGet(KEY);
    var at = Date.parse(storageGet(AT_KEY) || '');
    try {
      if (isFinite(at) && Date.now() - at > MAX_AGE_MS) { localStorage.removeItem(KEY); localStorage.removeItem(AT_KEY); }
      else if (!isFinite(at) && (stored === GRANTED || stored === DENIED)) localStorage.setItem(AT_KEY, new Date().toISOString());
    } catch (e) {}
  })();

  // Another tab answered: this one follows, and drops its in-memory answer.
  w.addEventListener('storage', function (e) {
    if (e.key === KEY || e.key === AT_KEY || e.key === null) {
      unstored = null;
      w.dispatchEvent(new CustomEvent('consent:changed', { detail: get() }));
      w.dispatchEvent(new Event('k:consent'));
      render();
    }
  });

  // --- The banner ------------------------------------------------------------

  var live = null, back = null, asked = false, shown = false;

  // What the banner did, for k.js's optional counts (no id, no choice stored).
  function ui(k) {
    try {
      var q = w.__consentUi = w.__consentUi || [];
      if (q.length < 8) q.push(k);
      w.dispatchEvent(new CustomEvent('consent:ui', { detail: k }));
    } catch (e) {}
  }

  function skippedHere() {
    for (var i = 0; i < SKIP.length; i++) if (SKIP[i].test(location.pathname)) return true;
    return false;
  }
  function needsAnswer() { return get() === null && !asksNotToBeTracked() && !skippedHere(); }

  function el(tagName, attrs, text) {
    var e = d.createElement(tagName);
    for (var k in attrs) e.setAttribute(k, attrs[k]);
    if (text) e.textContent = text;
    return e;
  }

  function close() {
    var inside = !!live && live.contains(d.activeElement);
    asked = false;
    render();
    if (back && back.isConnected) back.focus();
    // Answered the banner that showed by itself: focus the empty spot where it
    // was (the start of <body>), so the next Tab goes on into the page rather
    // than starting over from the top of the document.
    else if (inside && live) { live.setAttribute('tabindex', '-1'); live.focus({ preventScroll: true }); }
    back = null;
  }

  // Hooks are read when they are needed, so a page may set them after this script.
  function hook(name) {
    var c = w.consentConfig || cfg;
    return typeof c[name] === 'function' ? c[name] : null;
  }

  function accept() {
    ui('accept');
    set('granted');
    close();
    var granted = hook('onGranted');
    if (granted) granted();
  }

  function decline() {
    var withdrawing = get() === 'granted';
    ui(withdrawing ? 'withdraw' : 'decline');
    set('denied');
    close();
    // A first refusal: clear what an older setup may have stored (e.g. purgePostHog).
    var declined = !withdrawing ? hook('onDecline') : null;
    if (declined) try { declined(); } catch (e) {}
    var withdraw = withdrawing ? hook('onWithdraw') : null;
    // The reload happens even if the hook throws or rejects.
    Promise.resolve().then(function () { return withdraw ? withdraw() : null; }).catch(function () {}).then(function () {
      if (withdrawing && RELOAD) location.reload();
    });
  }

  // Deletes this visit's rows (k.js sends only the visit id), then withdraws.
  function deleteData() {
    try { w.__k.deleteMyData(); } catch (e) {}
    decline();
  }

  function render() {
    // A client-side router may replace <body> (Astro's ClientRouter): mount again.
    if (live && !live.isConnected && d.body) place();
    if (!live) return;
    var open = asked || needsAnswer();
    var existing = live.firstChild;
    if (!open) { if (existing) live.removeChild(existing); return; }
    if (existing) return;
    // ph-no-capture: PostHog records no click on the banner, a Decline that
    // withdraws consent included.
    var box = el('section', { 'class': 'consent-banner ph-no-capture', 'aria-labelledby': 'consent-title' });
    var inner = el('div', { 'class': 'consent-banner__inner' });
    inner.appendChild(el('p', { id: 'consent-title', 'class': 'consent-banner__title' }, TEXT.title));
    var body = el('p', { 'class': 'consent-banner__body' }, TEXT.body + ' ');
    body.appendChild(el('a', { href: TEXT.detailsHref }, TEXT.details));
    inner.appendChild(body);
    var row = el('div', { 'class': 'consent-banner__buttons' });
    var no = el('button', { type: 'button', 'class': 'consent-banner__button' }, TEXT.decline);
    var yes = el('button', { type: 'button', 'class': 'consent-banner__button' }, TEXT.accept);
    no.addEventListener('click', decline);
    yes.addEventListener('click', accept);
    row.appendChild(no);
    row.appendChild(yes);
    inner.appendChild(row);
    // Only when reopened after an Accept, and only if k.js can delete. Same
    // style as the others: it never outweighs Decline.
    if (asked && DELETE && get() === 'granted' && w.__k && w.__k.canDelete === true && typeof w.__k.deleteMyData === 'function') {
      var more = el('div', { 'class': 'consent-banner__buttons consent-banner__more' });
      var del = el('button', { type: 'button', 'class': 'consent-banner__button', 'data-consent-delete': '' }, TEXT.deleteData);
      del.addEventListener('click', deleteData);
      more.appendChild(del);
      inner.appendChild(more);
    }
    box.appendChild(inner);
    // Reopened from "Privacy settings", Escape closes it with nothing changed.
    // The banner that asks by itself stays: Escape is not an answer.
    if (asked) box.addEventListener('keydown', function (e) { if (e.key === 'Escape' && asked) { e.preventDefault(); close(); } });
    live.appendChild(box);
    // Shown by itself (not opened from "Privacy settings"): once a page load.
    if (!asked && !shown) { shown = true; ui('shown'); if (AT_END) no.focus({ preventScroll: true }); }
    if (asked) no.focus();
  }

  function open() {
    back = d.activeElement instanceof HTMLElement ? d.activeElement : null;
    asked = true;
    if (live && live.firstChild) live.removeChild(live.firstChild);
    render();
  }

  w.addEventListener('consent:open', open);
  // Client-side routes: show or hide the banner for the new path (private pages).
  ['pushState', 'replaceState'].forEach(function (m) {
    var orig = history[m];
    history[m] = function () { var r = orig.apply(this, arguments); setTimeout(render, 0); return r; };
  });
  w.addEventListener('popstate', render);
  d.addEventListener('click', function (e) {
    var t = e.target && e.target.closest ? e.target.closest('[data-consent-open]') : null;
    if (t) { e.preventDefault(); open(); }
  });

  function mount() {
    // The live region is in the page before the banner appears, so screen
    // readers announce it.
    live = el('div', { 'aria-live': 'polite', 'class': 'consent-live' });
    // First in <body>: keyboard users reach the question before the page
    // (or last, with mount: 'end').
    place();
    if (skipError && (/^(localhost|127\.0\.0\.1|\[::1\])$|\.localhost$/.test(location.hostname) || /[?&]k-debug(=|&|$)/.test(location.search))) {
      var note = el('p', { role: 'alert', 'class': 'consent-error' }, 'consent.js: the skip rule does not parse (' + skipError + '), so the banner never asks. Fix the rule.');
      note.style.cssText = 'position:fixed;left:0;right:0;top:0;z-index:99999;margin:0;padding:8px 12px;background:#b00020;color:#fff;font:14px/1.4 system-ui,sans-serif';
      d.body.insertBefore(note, d.body.firstChild);
    }
    // The banner's look: a stylesheet the site serves (stylesheet option,
    // assets/consent.css: allowed by style-src 'self', no nonce, never
    // render-blocking), else a <style> element (needs 'unsafe-inline' or the
    // page's nonce under a CSP), else nothing (styles: false, the same rules
    // in the site's own CSS). See references/consent.md.
    var waits = [];
    var sheet = opt('stylesheet', '');
    if (sheet) {
      var link = el('link', { rel: 'stylesheet', href: sheet });
      waits.push(new Promise(function (ok) { link.onload = link.onerror = ok; }));
      d.head.appendChild(link);
    } else if (String(opt('styles', 'true')) !== 'false') {
      // The nonce of this script tag itself is the simplest: give
      // <script src="/consent.js" nonce="…"> and it carries over. (The nonce
      // property, not the attribute: browsers hide the attribute's value.)
      var nonce = opt('styleNonce', '') || (tag && tag.nonce) || '';
      var css = el('style', {});
      if (nonce) css.nonce = nonce;
      css.textContent = CSS;
      d.head.appendChild(css);
    }
    // Web fonts first: a bottom-anchored banner that reflows when they swap in
    // grows upward, and that counts as a layout shift. At most 3 s.
    if (d.fonts && d.fonts.ready) waits.push(d.fonts.ready);
    if (!waits.length || typeof Promise === 'undefined') return render();
    var done = false;
    var go = function () { if (!done) { done = true; render(); } };
    Promise.all(waits).then(go, go);
    setTimeout(go, 3000);
  }

  w.analyticsConsent = { get: get, set: set, open: open };
  if (d.body) mount(); else d.addEventListener('DOMContentLoaded', mount, { once: true });
})();
