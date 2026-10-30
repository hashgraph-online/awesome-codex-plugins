/* app.js: the distribution dashboard's page logic, loaded by index.html. */
'use strict';
var PLAT = { linkedin: 'LinkedIn', x: 'X', substack: 'Substack', threads: 'Threads', bluesky: 'Bluesky' };
var MON = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
var LS = 'lfdState';
var MODE = 'local';          /* 'serve' | 'demo' (server --demo) | 'local' (no server) */
var ISSUES = [], LOG = [], OPEN = null, OPENROW = {};

function $(id) { return document.getElementById(id); }
function el(tag, cls, text) { var n = document.createElement(tag); if (cls) n.className = cls; if (text != null) n.textContent = text; return n; }
function clear(n) { while (n.firstChild) n.removeChild(n.firstChild); }
function pname(p) { return PLAT[p] || p; }
function fdate(s) { if (!s) return ''; var m = String(s).match(/^(\d{4})-(\d{2})-(\d{2})/); return m ? MON[+m[2]-1] + ' ' + (+m[3]) + ', ' + m[1] : s; }
function plural(n, one, many) { return n + ' ' + (n === 1 ? one : (many || one + 's')); }
/* A cover is a web URL, or covers/<file> inside the data folder (serve.py serves it). */
function coverSrc(c) {
  c = c || '';
  if (/^https?:\/\//.test(c)) return c;
  if (/^covers\/[\w.-]+\.(jpe?g|png|webp|gif)$/i.test(c)) return MODE === 'local' ? '../sample/' + c : c;
  return '';
}
function key(slug, id) { return slug + '::' + id; }
function lsGet() { try { return JSON.parse(localStorage.getItem(LS) || '[]'); } catch (e) { return []; } }
function lsSet(v) { try { localStorage.setItem(LS, JSON.stringify(v)); } catch (e) { /* private window */ } }

/* The log is append-only; state is its last word per post. */
function state() {
  var S = {};
  LOG.forEach(function (r) {
    var k = key(r.issue, r.item), s = S[k] || (S[k] = { checked: false, skip: false, url: '', at: '' });
    if (r.kind === 'check') s.checked = !!r.on;
    else if (r.kind === 'skip') s.skip = !!r.on;
    else if (r.kind === 'log') { s.url = r.url; s.at = r.at; s.checked = true; s.skip = false; }
  });
  return S;
}
function counts(d, S) {
  var c = { total: 0, done: 0, logged: 0, skip: 0 };
  (d.items || []).forEach(function (it) {
    var s = S[key(d.slug, it.id)] || {};
    c.total++;
    if (s.skip) c.skip++; else if (s.url) c.logged++; else if (s.checked) c.done++;
  });
  return c;
}

function send(path, body) {
  if (MODE === 'local') {
    var row = Object.assign({}, body, { kind: path.split('/').pop(), at: new Date().toISOString() });
    if (row.kind === 'log' && !/^https?:\/\/\S+$/.test(row.url || '')) return Promise.resolve({ ok: false, error: "That isn't a link. Paste the post's full URL." });
    LOG.push(row); lsSet(LOG); return Promise.resolve({ ok: true, row: row });
  }
  return fetch(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
    .then(function (r) { return r.json(); })
    .then(function (j) { if (j.ok) LOG.push(j.row); return j; })
    .catch(function () { return { ok: false, error: 'The server stopped. Ask your agent to start the distribution dashboard again.' }; });
}

/* ── 01 · issues ─────────────────────────────────────────── */
function renderIssues() {
  var host = $('issues'), S = state(); clear(host);
  if (!ISSUES.length) { host.appendChild(el('div', 'empty', 'No issues yet. Give your agent a published URL and ask it to distribute the piece; the issue appears here.')); return; }
  ISSUES.forEach(function (d) {
    var c = counts(d, S), live = c.done + c.logged, finished = c.total && (live + c.skip) === c.total;
    var b = el('button', 'iss' + (finished ? ' done' : '')); b.type = 'button';
    b.setAttribute('aria-expanded', OPEN === d.slug ? 'true' : 'false');
    var th = el('div', 'thumb');
    var src = coverSrc(d.cover);
    if (src) { var img = el('img'); img.src = src; img.alt = ''; img.loading = 'lazy'; th.appendChild(img); }
    else th.appendChild(el('div', 'noimg', d.series || d.title));
    th.appendChild(el('span', 'tab', finished ? 'done' : live + ' of ' + (c.total - c.skip) + ' posted'));
    b.appendChild(th);
    var body = el('div', 'body');
    body.appendChild(el('div', 'lab', d.title));
    body.appendChild(el('div', 'cnt', [fdate(d.published), plural(c.total, 'post'), c.logged ? c.logged + ' with links' : ''].filter(Boolean).join(' · ')));
    var rail = el('div', 'railbar');
    [['log', c.logged], ['', c.done], ['skip', c.skip]].forEach(function (p) { if (p[1]) { var i = el('i', p[0]); i.style.width = (100 * p[1] / c.total) + '%'; rail.appendChild(i); } });
    body.appendChild(rail); b.appendChild(body);
    b.addEventListener('click', function () { OPEN = OPEN === d.slug ? null : d.slug; OPENROW = {}; renderAll(); if (OPEN) $('qwrap').scrollIntoView({ behavior: 'smooth', block: 'start' }); });
    host.appendChild(b);
  });
  $('s1meta').textContent = plural(ISSUES.length, 'issue');
}

function renderQueue() {
  var d = ISSUES.filter(function (x) { return x.slug === OPEN; })[0];
  $('qwrap').hidden = !d; if (!d) return;
  var q = $('queue'), S = state(); clear(q);
  var head = el('div', 'qhead'); head.appendChild(el('h3', null, d.title));
  if (/^https?:\/\//.test(d.url || '')) { var a = el('a', null, 'read the issue ↗'); a.href = d.url; a.target = '_blank'; a.rel = 'noopener'; head.appendChild(a); }
  q.appendChild(head);
  (d.sections || []).forEach(function (sec) {
    var items = (d.items || []).filter(function (it) { return it.section === sec.id; });
    if (!items.length) return;
    q.appendChild(el('div', 'qgroup', sec.title));
    items.forEach(function (it) { q.appendChild(row(d, it, S[key(d.slug, it.id)] || {})); });
  });
  renderProg(d, S);
}

function row(d, it, s) {
  var wrap = el('div'), k = key(d.slug, it.id);
  var r = el('div', 'ck' + (s.skip ? ' skip' : (s.checked ? ' done' : '')) + (OPENROW[k] ? ' open' : ''));
  var cb = el('input'); cb.type = 'checkbox'; cb.checked = !!s.checked && !s.skip; cb.disabled = !!s.url || !!s.skip;
  cb.setAttribute('aria-label', 'Posted');
  cb.addEventListener('change', function () { send('/api/check', { issue: d.slug, item: it.id, on: cb.checked }).then(renderAll); });
  r.appendChild(cb);
  var t = el('div', 't'); t.appendChild(el('span', 'plat', pname(it.platform)));
  t.appendChild(document.createTextNode([it.format, it.label].filter(Boolean).join(' — ')));
  t.addEventListener('click', function () { OPENROW[k] = !OPENROW[k]; renderQueue(); });
  r.appendChild(t);
  if (s.url) { var a = el('a', 'tag log', 'live ↗'); a.href = s.url; a.target = '_blank'; a.rel = 'noopener'; r.appendChild(a); }
  else if (!s.skip) {
    var lb = el('button', 'tag btnlike', 'add link'); lb.type = 'button';
    lb.addEventListener('click', function () { OPENROW[k + ':log'] = true; renderQueue(); });
    r.appendChild(lb);
  }
  var sk = el('button', 'tag btnlike', s.skip ? 'unskip' : 'skip'); sk.type = 'button';
  if (!s.url) { sk.addEventListener('click', function () { send('/api/skip', { issue: d.slug, item: it.id, on: !s.skip }).then(renderAll); }); r.appendChild(sk); }
  wrap.appendChild(r);
  if (OPENROW[k] && it.copy) {
    var cp = el('div', 'copy', it.copy), acts = el('div', 'acts'), cbtn = el('button', 'btn ghost small', 'Copy text'); cbtn.type = 'button';
    cbtn.addEventListener('click', function () {
      (navigator.clipboard ? navigator.clipboard.writeText(it.copy) : Promise.reject()).then(function () { cbtn.textContent = 'Copied'; cbtn.className = 'btn ok small'; },
        function () { cbtn.textContent = 'Select and copy by hand'; });
    });
    acts.appendChild(cbtn); cp.appendChild(acts);
    /* The passage the post was cut from, so a caveat the post dropped is in view. */
    if (it.source) {
      var pair = el('div', 'pair'), src = el('div', 'src');
      cp.insertBefore(el('span', 'h', 'Post'), cp.firstChild);
      src.appendChild(el('span', 'h', 'From the piece')); src.appendChild(document.createTextNode(it.source));
      pair.appendChild(cp); pair.appendChild(src); wrap.appendChild(pair);
    } else wrap.appendChild(cp);
  }
  if (OPENROW[k + ':log'] && !s.url) wrap.appendChild(logBox(d, it, k));
  return wrap;
}

function logBox(d, it, k) {
  var box = el('div', 'logbox'), inp = el('input'), go = el('button', 'btn small', 'Save link'), msg = el('div', 'msg', 'Paste the link to the live ' + pname(it.platform) + ' post.');
  inp.type = 'url'; inp.placeholder = 'https://…'; go.type = 'button';
  function save() {
    go.disabled = true;
    send('/api/log', { issue: d.slug, item: it.id, url: inp.value.trim() }).then(function (j) {
      go.disabled = false;
      if (j.ok) { delete OPENROW[k + ':log']; renderAll(); }
      else { box.className = 'logbox err'; msg.textContent = j.error || 'Not saved.'; }
    });
  }
  go.addEventListener('click', save);
  inp.addEventListener('keydown', function (e) { if (e.key === 'Enter') save(); });
  box.appendChild(inp); box.appendChild(go); box.appendChild(msg);
  setTimeout(function () { inp.focus(); }, 0);
  return box;
}

function renderProg(d, S) {
  var p = $('prog'), c = counts(d, S); clear(p);
  var live = c.done + c.logged, of = c.total - c.skip;
  p.appendChild(el('div', 'n', String(live)));
  p.appendChild(el('div', 'of', 'of ' + of + ' posted'));
  var bar = el('div', 'bar'), y = 0;
  [['var(--green)', c.logged], ['var(--ink)', c.done], ['var(--rule)', c.skip]].forEach(function (s) {
    if (!s[1]) return; var i = el('i'); i.style.background = s[0]; i.style.bottom = (100 * y / c.total) + '%'; i.style.height = (100 * s[1] / c.total) + '%'; bar.appendChild(i); y += s[1];
  });
  p.appendChild(bar);
  var keyb = el('div', 'key');
  [['var(--green)', 'linked'], ['var(--ink)', 'ticked'], ['var(--rule)', 'skipped']].forEach(function (s) {
    var line = el('div'), sw = el('s'); sw.style.background = s[0]; line.appendChild(sw); line.appendChild(document.createTextNode(s[1])); keyb.appendChild(line);
  });
  p.appendChild(keyb);
}

/* ── 02 · coverage: which sections ever went out ─────────── */
function renderCoverage() {
  var S = state(), plats = {}, tSec = 0, tPosted = 0, tPosts = 0, tLinks = 0, rows = [];
  ISSUES.forEach(function (d) { (d.items || []).forEach(function (it) { plats[it.platform] = 1; }); });
  var P = Object.keys(plats).sort();
  ISSUES.forEach(function (d) {
    var secs = d.sections || [], posted = 0, per = {};
    secs.forEach(function (sec) {
      var hit = false;
      (d.items || []).forEach(function (it) {
        if (it.section !== sec.id) return;
        var s = S[key(d.slug, it.id)] || {};
        if ((s.checked || s.url) && !s.skip) { hit = true; per[it.platform] = (per[it.platform] || 0) + 1; tPosts++; if (s.url) tLinks++; }
      });
      if (hit) posted++;
    });
    tSec += secs.length; tPosted += posted;
    rows.push({ d: d, secs: secs.length, posted: posted, per: per });
  });
  var st = $('stats'); clear(st);
  [[tSec, 'sections written'], [tPosted, 'posted somewhere'], [tSec - tPosted, 'never posted'], [tLinks, 'links logged']].forEach(function (x, i) {
    var s = el('div', 'stat'), b = el('b', i === 2 && x[0] ? 'never' : null, String(x[0])); s.appendChild(b); s.appendChild(el('span', null, x[1])); st.appendChild(s);
  });
  $('finding').textContent = !tSec ? 'Coverage fills in as you post.' :
    tPosted + ' of ' + plural(tSec, 'section') + ' across ' + plural(ISSUES.length, 'issue') + ' have gone out at least once. ' +
    (tSec - tPosted ? (tSec - tPosted) + ' never have. If an issue isn\'t tied to the news, those are posts you\'ve already written.' : 'Everything you wrote has gone out at least once.');
  $('s2meta').textContent = plural(tPosts, 'post');
  var t = $('cov'); clear(t);
  var hr = el('tr'); ['Issue', 'Published', 'Sections posted'].concat(P.map(pname)).forEach(function (h) { hr.appendChild(el('th', null, h)); });
  var th = el('thead'); th.appendChild(hr); t.appendChild(th);
  var tb = el('tbody');
  rows.forEach(function (r) {
    var tr = el('tr');
    tr.appendChild(el('td', null, r.d.title)); tr.appendChild(el('td', 'num', fdate(r.d.published)));
    var c = el('td', 'num' + (r.posted < r.secs ? ' never' : ''), r.posted + ' / ' + r.secs); tr.appendChild(c);
    P.forEach(function (p) { tr.appendChild(el('td', 'num', String(r.per[p] || 0))); });
    tb.appendChild(tr);
  });
  t.appendChild(tb);
}

/* ── 03 · posted links ───────────────────────────────────── */
function renderPosted() {
  var S = state(), out = [], t = $('posted'); clear(t);
  ISSUES.forEach(function (d) {
    (d.items || []).forEach(function (it) {
      var s = S[key(d.slug, it.id)] || {};
      if (!s.url) return;
      var sec = (d.sections || []).filter(function (x) { return x.id === it.section; })[0] || {};
      out.push({ at: s.at, d: d, sec: sec.title || '', it: it, url: s.url });
    });
  });
  out.sort(function (a, b) { return String(b.at).localeCompare(String(a.at)); });
  $('s3meta').textContent = plural(out.length, 'link');
  if (!out.length) { var tr0 = el('tr'), td0 = el('td', 'note', 'No links yet. Once a post is live, hit "add link" next to it and paste the URL.'); tr0.appendChild(td0); t.appendChild(tr0); return; }
  var hr = el('tr'); ['Date', 'Platform', 'Issue', 'Section', 'Link'].forEach(function (h) { hr.appendChild(el('th', null, h)); });
  var th = el('thead'); th.appendChild(hr); t.appendChild(th);
  var tb = el('tbody');
  out.forEach(function (r) {
    var tr = el('tr');
    tr.appendChild(el('td', 'num', fdate(r.at))); tr.appendChild(el('td', null, pname(r.it.platform)));
    tr.appendChild(el('td', null, r.d.title)); tr.appendChild(el('td', null, r.sec));
    var td = el('td'), a = el('a', null, r.url.replace(/^https?:\/\/(www\.)?/, '')); a.href = r.url; a.target = '_blank'; a.rel = 'noopener'; td.appendChild(a); tr.appendChild(td);
    tb.appendChild(tr);
  });
  t.appendChild(tb);
}

function csvLocal() {
  var S = state(), lines = [['issue', 'section', 'platform', 'format', 'date posted', 'link']];
  ISSUES.forEach(function (d) { (d.items || []).forEach(function (it) {
    var s = S[key(d.slug, it.id)] || {}; if (!s.url) return;
    var sec = (d.sections || []).filter(function (x) { return x.id === it.section; })[0] || {};
    lines.push([d.title, sec.title || '', it.platform, it.format || '', String(s.at).slice(0, 10), s.url]);
  }); });
  var csv = lines.map(function (r) { return r.map(function (v) { v = String(v == null ? '' : v); return /[",\n]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v; }).join(','); }).join('\n');
  return URL.createObjectURL(new Blob([csv], { type: 'text/csv' }));
}

function renderAll() { renderIssues(); renderQueue(); renderCoverage(); renderPosted(); }

function setMode(mode, home) {
  MODE = mode;
  var sv = $('serve'), bn = $('banner');
  sv.className = 'serve' + (mode === 'serve' ? ' on' : ' demo');
  sv.firstChild.nodeValue = mode === 'serve' ? 'saving to disk ' : mode === 'demo' ? 'demo · not saved ' : 'sample · this browser only ';
  $('home').textContent = mode === 'local' ? 'this browser only (no server running)' : home;
  if (mode !== 'serve') {
    bn.hidden = false; clear(bn);
    bn.appendChild(el('b', null, ISSUES.length === 1 ? 'This is a sample issue. ' : 'These are sample issues. '));
    bn.appendChild(document.createTextNode(mode === 'demo'
      ? 'Tick, skip and paste links to see how it works; nothing is saved. '
      : 'Ticks stay in this browser. '));
    bn.appendChild(document.createTextNode('To track your own writing, install the plugin, give your agent a published URL and ask it to distribute the piece.'));
  }
  if (mode === 'local') $('csv').addEventListener('click', function (e) { e.preventDefault(); var a = el('a'); a.href = csvLocal(); a.download = 'posted.csv'; a.click(); });
  $('railR').textContent = fdate(new Date().toISOString().slice(0, 10));
}

fetch('/api/state', { cache: 'no-store' }).then(function (r) { if (!r.ok) throw 0; return r.json(); }).then(function (j) {
  ISSUES = j.issues || []; LOG = j.log || []; OPEN = ISSUES.length ? ISSUES[0].slug : null; setMode(j.demo ? 'demo' : 'serve', j.home); renderAll();
}).catch(function () {
  ISSUES = (window.LFD_SAMPLE || []).slice(); LOG = lsGet(); OPEN = ISSUES[0].slug; setMode('local'); renderAll();
});
