/* hyper-diagram runtime: reads #hd-spec, validates it, calls the type renderer,
   builds the legend and hover styles, runs geometry checks, sizes the PDF page,
   removes every runtime script, and leaves the result on <body data-hd-result>. */
(function () {
  'use strict';
  const HD = window.HD;
  const ID_RE = /^[A-Za-z0-9_-]+$/;
  HD.TYPE_LABEL = {
    architecture: 'ARCHITECTURE', flowchart: 'FLOWCHART', dataflow: 'DATA FLOW', state: 'STATE',
    class: 'CLASS', erd: 'ERD', sequence: 'SEQUENCE', tree: 'TREE', mindmap: 'MIND MAP',
    timeline: 'TIMELINE', gantt: 'SCHEDULE', layers: 'LAYERS'
  };

  HD.checkIds = function (list, what) {
    const seen = new Set();
    for (const it of list || []) {
      if (!it || typeof it.id !== 'string' || !ID_RE.test(it.id)) { HD.err('BAD_ID', `${what} id must match [A-Za-z0-9_-]+: ${JSON.stringify(it && it.id)}`); continue; }
      if (seen.has(it.id) || HD._ids.has(it.id)) HD.err('DUPLICATE_ID', `duplicate id ${it.id}`);
      seen.add(it.id); HD._ids.add(it.id);
    }
  };
  HD.checkRefs = function (edges, known, what) {
    (edges || []).forEach((e, i) => {
      for (const end of ['from', 'to']) if (!known.has(e[end])) HD.err('UNKNOWN_ENDPOINT', `${what}[${i}].${end} names an unknown id: ${e[end]}`);
    });
  };

  const rectOf = (el) => { const r = el.getBoundingClientRect(); return { x: r.left, y: r.top, w: r.width, h: r.height }; };
  const inset = (r, d) => ({ x: r.x + d, y: r.y + d, w: Math.max(0, r.w - 2 * d), h: Math.max(0, r.h - 2 * d) });
  const overlap = (a, b) => Math.max(0, Math.min(a.x + a.w, b.x + b.w) - Math.max(a.x, b.x)) * Math.max(0, Math.min(a.y + a.h, b.y + b.h) - Math.max(a.y, b.y));
  const contains = (o, i, t) => i.x >= o.x - t && i.y >= o.y - t && i.x + i.w <= o.x + o.w + t && i.y + i.h <= o.y + o.h + t;
  const inside = (p, r) => p.x > r.x && p.x < r.x + r.w && p.y > r.y && p.y < r.y + r.h;
  function sample(path) {
    const total = path.getTotalLength(), m = path.getScreenCTM(), pts = [];
    const steps = Math.max(2, Math.ceil(total / 4));
    for (let i = 0; i <= steps; i++) { const p = path.getPointAtLength((total * i) / steps); const q = new DOMPoint(p.x, p.y).matrixTransform(m); pts.push({ x: q.x, y: q.y }); }
    return pts;
  }
  function segCross(a, b, c, d) {
    const o = (p, q, r) => Math.sign((q.x - p.x) * (r.y - p.y) - (q.y - p.y) * (r.x - p.x));
    return o(a, b, c) * o(a, b, d) < 0 && o(c, d, a) * o(c, d, b) < 0;
  }

  HD.check = function (svg) {
    const nodes = [...svg.querySelectorAll('.hd-node')].map((g) => ({ id: g.dataset.node, g, r: rectOf(g.querySelector('.hd-shape')) }));
    const groups = [...svg.querySelectorAll('.hd-group')].map((g) => ({ id: g.dataset.group, g, r: rectOf(g.querySelector('.hd-frame')) }));
    const labels = [...svg.querySelectorAll('.hd-elabel, .hd-group-label')].map((g) => ({ g, r: rectOf(g), text: g.textContent.trim(), group: g.classList.contains('hd-group-label') }));
    for (const n of nodes) {
      for (const t of n.g.querySelectorAll('text')) if (!contains(inset(n.r, 1), rectOf(t), 0.5)) HD.err('TEXT_OVERFLOW', `text "${t.textContent.trim()}" spills out of node ${n.id}`, { node: n.id });
    }
    for (let i = 0; i < nodes.length; i++) for (let j = i + 1; j < nodes.length; j++) {
      if (overlap(nodes[i].r, nodes[j].r) > 1) HD.err('NODE_OVERLAP', `nodes ${nodes[i].id} and ${nodes[j].id} overlap`);
    }
    for (const gr of groups) {
      for (const n of nodes) if (overlap(gr.r, n.r) > 1 && !contains(gr.r, n.r, 0.5)) HD.err('NODE_CROSSES_GROUP', `node ${n.id} straddles the border of group ${gr.id}`);
      for (const g2 of groups) if (g2 !== gr && overlap(gr.r, g2.r) > 1 && !contains(gr.r, g2.r, 0.5) && !contains(g2.r, gr.r, 0.5)) HD.err('GROUP_OVERLAP', `groups ${gr.id} and ${g2.id} overlap without nesting`);
    }
    for (const l of labels) {
      for (const n of nodes) if (overlap(l.r, n.r) > 1) HD.err('LABEL_OVERLAPS_NODE', `label "${l.text}" overlaps node ${n.id}`, { node: n.id });
    }
    for (let i = 0; i < labels.length; i++) for (let j = i + 1; j < labels.length; j++) {
      if (overlap(labels[i].r, labels[j].r) > 1) HD.err('LABEL_OVERLAP', `labels "${labels[i].text}" and "${labels[j].text}" overlap`);
    }
    const lines = [];
    for (const e of svg.querySelectorAll('.hd-edge')) {
      const path = e.querySelector('.hd-path');
      if (!path || path.getTotalLength() < 1) continue;
      const pts = sample(path);
      const touch = new Set((e.dataset.touch || '').split(' '));
      if (!e.dataset.free) {
        for (const n of nodes) {
          if (touch.has(n.id)) continue;
          if (pts.some((p) => inside(p, inset(n.r, 3)))) HD.err('EDGE_CROSSES_NODE', `edge ${e.dataset.from}->${e.dataset.to} runs through node ${n.id}`);
        }
        lines.push({ name: `${e.dataset.from}->${e.dataset.to}`, pts, touch });
      }
    }
    let crossings = 0;
    for (let i = 0; i < lines.length; i++) for (let j = i + 1; j < lines.length; j++) {
      const a = lines[i].pts, b = lines[j].pts; let hit = false;
      for (let k = 0; k + 1 < a.length && !hit; k++) for (let m = 0; m + 1 < b.length && !hit; m++) if (segCross(a[k], a[k + 1], b[m], b[m + 1])) hit = true;
      if (hit) crossings++;
    }
    if (crossings) HD.warn('EDGE_CROSSINGS', `${crossings} edge pair(s) cross; reorder or regroup nodes when the reading suffers`);
    for (const t of svg.querySelectorAll('text')) {
      const fs = parseFloat(getComputedStyle(t).fontSize);
      if (fs < 9.5) HD.warn('SMALL_TEXT', `text "${t.textContent.trim()}" is ${fs}px`);
    }
    return { nodes: nodes.length, groups: groups.length, edges: svg.querySelectorAll('.hd-edge').length, edgeCrossings: crossings };
  };

  function buildLegend(spec, svg) {
    const ul = document.getElementById('hd-legend');
    if (spec.legend === false) { ul.remove(); return; }
    const names = Object.assign({}, (spec.legend && spec.legend.kinds) || {});
    const enames = Object.assign({}, (spec.legend && spec.legend.edges) || {});
    const nk = new Map(), ek = new Map();
    for (const g of svg.querySelectorAll('.hd-node')) { if (g.dataset.legend === 'no') continue; const k = [...g.classList].find((c) => c.startsWith('k-')); if (k) nk.set(k.slice(2), (nk.get(k.slice(2)) || 0) + 1); }
    for (const g of svg.querySelectorAll('.hd-edge')) { if (g.dataset.legend === 'no') continue; const k = [...g.classList].find((c) => c.startsWith('e-')); const dash = g.classList.contains('dash') ? 'dash' : g.classList.contains('dot') ? 'dot' : ''; const key = k.slice(2) + '|' + dash + '|' + (g.dataset.legendLabel || ''); ek.set(key, (ek.get(key) || 0) + 1); }
    if (nk.size + ek.size < 2) { ul.remove(); return; }
    HD.html('li', { class: 'hd-legend-title', text: spec.legendTitle || '범례' }, ul);
    for (const [k, c] of nk) {
      const li = HD.html('li', { class: `k-${k}` }, ul);
      HD.html('span', { class: 'hd-sw' }, li);
      HD.html('span', { text: names[k] || HD.KINDS[k] }, li);
      HD.html('span', { class: 'hd-count', text: String(c) }, li);
    }
    for (const [key, c] of ek) {
      const [k, dash, custom] = key.split('|');
      if (ek.size === 1 && k === 'default' && !custom) break;
      const li = HD.html('li', { class: `e-${k}` }, ul);
      HD.html('span', { class: `hd-sw line ${dash}` }, li);
      HD.html('span', { text: custom || enames[k] || HD.EDGE_KINDS[k] }, li);
      HD.html('span', { class: 'hd-count', text: String(c) }, li);
    }
  }
  HD.html = function (tag, attrs, parent) {
    const el = document.createElement(tag);
    for (const k in attrs || {}) { if (k === 'text') el.textContent = attrs[k]; else el.setAttribute(k, attrs[k]); }
    if (parent) parent.appendChild(el);
    return el;
  };

  function hoverStyles(svg) {
    const near = new Map();
    for (const g of svg.querySelectorAll('.hd-node')) near.set(g.dataset.node, new Set([g.dataset.node]));
    for (const e of svg.querySelectorAll('.hd-edge')) {
      const a = e.dataset.from, b = e.dataset.to;
      if (near.has(a)) near.get(a).add(b);
      if (near.has(b)) near.get(b).add(a);
    }
    let css = '';
    for (const g of svg.querySelectorAll('.hd-node')) {
      const id = g.dataset.node;
      g.setAttribute('data-near', [...near.get(id)].join(' '));
      if (!/^[A-Za-z0-9_-]+$/.test(id)) continue;
      css += `#hd-svg:has([data-node="${id}"]:hover) .hd-node:not([data-near~="${id}"]),#hd-svg:has([data-node="${id}"]:hover) :is(.hd-edge,.hd-elabel):not([data-touch~="${id}"]){opacity:.18}\n`;
    }
    if (css) { const s = document.createElement('style'); s.id = 'hd-hover'; s.textContent = '@media (hover:hover){' + css + '}'; document.head.appendChild(s); }
  }

  HD.run = async function () {
    const R = { version: 2, type: null, errors: HD.errors, warnings: HD.warnings, canvas: null, counts: {} };
    HD._ids = new Set();
    try {
      const spec = JSON.parse(document.getElementById('hd-spec').textContent);
      HD.spec = spec; R.type = spec.type;
      document.documentElement.lang = spec.lang || 'ko';
      document.documentElement.dataset.theme = spec.theme === 'dark' ? 'dark' : 'light';
      HD.SANS = HD.cssVar('--font'); HD.MONO = HD.cssVar('--mono');
      if (document.fonts && document.fonts.ready) await document.fonts.ready;
      document.title = spec.title || 'diagram';
      if (!spec.title || !String(spec.title).trim()) HD.err('TITLE_MISSING', 'spec.title is required');
      if (!spec.description || String(spec.description).trim().length < 20) HD.err('DESCRIPTION_MISSING', 'spec.description needs a long description of at least 20 characters');
      document.getElementById('hd-title').textContent = spec.title || '';
      document.getElementById('hd-subtitle').textContent = spec.subtitle || '';
      document.getElementById('hd-badge').textContent = spec.badge || HD.TYPE_LABEL[spec.type] || String(spec.type || '').toUpperCase();
      document.getElementById('hd-desc').textContent = spec.description || '';
      const svg = document.getElementById('hd-svg');
      HD.defs = HD.svg('defs', {}, svg);
      const root = HD.svg('g', { id: 'hd-root' }, svg);
      HD.layer = {};
      for (const name of ['groups', 'edges', 'nodes', 'labels']) HD.layer[name] = HD.svg('g', { class: 'hd-layer-' + name }, root);
      const fn = HD.types[spec.type];
      if (!fn) HD.err('TYPE_UNKNOWN', `spec.type must be one of: ${Object.keys(HD.types).join(', ')}`);
      else await fn(spec, HD.layer);
      const bb = root.getBBox();
      const pad = 14;
      const W = Math.ceil(bb.width + pad * 2), H = Math.ceil(bb.height + pad * 2);
      svg.setAttribute('viewBox', `${Math.floor(bb.x - pad)} ${Math.floor(bb.y - pad)} ${W} ${H}`);
      svg.setAttribute('width', W); svg.setAttribute('height', H);
      if (W > 2400) HD.warn('WIDE_DIAGRAM', `diagram is ${W}px wide; split it or change direction`);
      buildLegend(spec, svg);
      hoverStyles(svg);
      R.counts = HD.check(svg);
    } catch (e) {
      HD.err('RUNTIME_ERROR', String((e && (e.stack || e.message)) || e).slice(0, 700));
    } finally {
      for (const el of document.querySelectorAll('script[data-hd-runtime], #hd-spec')) el.remove();
      const fig = document.getElementById('hd-canvas');
      const r = fig.getBoundingClientRect();
      const W = Math.ceil(r.width), H = Math.ceil(r.height);
      R.canvas = { width: W, height: H };
      const s = document.createElement('style');
      s.id = 'hd-page';
      s.textContent = `@page{size:${W}px ${H}px;margin:0}@media print{html,body{width:${W}px;height:${H}px;overflow:hidden}}`;
      document.head.appendChild(s);
      document.documentElement.dataset.hdState = 'baked';
      document.body.dataset.hdResult = JSON.stringify(R);
    }
  };
})();
