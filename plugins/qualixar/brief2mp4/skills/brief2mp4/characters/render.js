/*
 * render.js: turns a posed character into a display list, and draws the list on a canvas or in SVG.
 *
 *   const items = B2M.layout(character, skin, B2M.pose(character, track, t, { steps: skin.steps }), { x, y, scale });
 *   B2M.drawCanvas(ctx, items);                    // canvas 2D
 *   const svg = B2M.createSVG(document, parent, w, h); svg.update(items);   // HyperFrames DOM / SVG
 *
 * An item is { kind: 'path' | 'text', m: [a, b, c, d, e, f], d, fill, stroke, sw, alpha, shadow, ... }. The list is a
 * plain array of numbers and strings, so the same frame can be compared, hashed or drawn by either backend.
 */
(function (g) {
  'use strict';
  if (typeof require === 'function' && !(g.B2M && g.B2M.shapePath)) require('./shapes.js');
  const B = (g.B2M = g.B2M || {});

  const IDENT = [1, 0, 0, 1, 0, 0];
  const mul = (p, q) => [p[0] * q[0] + p[2] * q[1], p[1] * q[0] + p[3] * q[1], p[0] * q[2] + p[2] * q[3], p[1] * q[2] + p[3] * q[3], p[0] * q[4] + p[2] * q[5] + p[4], p[1] * q[4] + p[3] * q[5] + p[5]];
  const translate = (x, y) => [1, 0, 0, 1, x, y];
  const rotate = (deg) => { const r = B.rad(deg), c = Math.cos(r), s = Math.sin(r); return [c, s, -s, c, 0, 0]; };
  const scaleM = (sx, sy) => [sx, 0, 0, sy, 0, 0];
  const round = (m) => m.map((v) => Math.round(v * 1000) / 1000);

  const INDEX = new WeakMap();
  function indexOf(character) {
    let ix = INDEX.get(character);
    if (ix) return ix;
    const byId = {};
    character.parts.forEach((p, i) => { byId[p.id] = Object.assign({ order: i }, p); });
    const topo = [];
    const seen = new Set();
    const visit = (p) => { if (seen.has(p.id)) return; seen.add(p.id); if (p.parent) visit(byId[p.parent]); topo.push(p); };
    Object.values(byId).forEach(visit);
    ix = { byId, topo };
    INDEX.set(character, ix);
    return ix;
  }

  // The drawing a part uses right now: its own, or a variant chosen by the pose (an open hand), the view
  // ('front' for a close-up facing the camera) or the skin (the anime skin redraws eyes and hair).
  function effectiveParts(character, posed, skin) {
    const out = {}, view = skin && skin.profileOnly ? 'side' : posed.view || 'side', sv = skin && skin.variant;
    indexOf(character).topo.forEach((p) => {
      const names = [posed.variants && posed.variants[p.id], view !== 'side' && sv && view + '+' + sv, view !== 'side' && view, sv];
      const hit = p.variants && names.find((n) => n && p.variants[n]);
      out[p.id] = hit ? Object.assign({}, p, p.variants[hit]) : p;
    });
    return out;
  }

  function partMatrices(eff, character, posed, base) {
    const W = {};
    indexOf(character).topo.forEach((q) => {
      const p = eff[q.id], ch = posed.parts[p.id], parent = p.parent ? W[p.parent] : base;
      const local = mul(translate(ch.x, ch.y), mul(translate(p.pivot[0], p.pivot[1]), mul(rotate(ch.r + (ch.jaw || 0)), mul(scaleM(ch.sx, ch.sy), translate(-p.pivot[0], -p.pivot[1])))));
      W[p.id] = mul(parent, local);
    });
    return W;
  }

  const mouthOpen = (posed) => (B.VISEME_SHAPE[posed.viseme] || B.VISEME_SHAPE.rest).open;

  function shapesOf(part, posed) {
    const cfg = part.mouth;
    return cfg && cfg.kind === 'lips' ? B.lipShapes(cfg, part.pivot, posed.viseme, posed.smile) : part.shapes;
  }

  function imageOf(part, posed) {
    const cfg = part.mouth;
    if (cfg && cfg.kind === 'images') return cfg.images[posed.viseme] || cfg.images.rest;
    return part.image || null;
  }

  // A shape may carry `calm`, a second set of points for the same polygon. How far it goes towards `pts` is the
  // character's `spikes` (0 to 1, default 0.6): hair drawn once as a spiky outline and once as a swept one.
  function morph(character, shape) {
    if (!shape.calm) return shape;
    const k = character.spikes === undefined ? 0.6 : character.spikes;
    return Object.assign({}, shape, { calm: undefined, pts: shape.pts.map((p, i) => [shape.calm[i][0] + (p[0] - shape.calm[i][0]) * k, shape.calm[i][1] + (p[1] - shape.calm[i][1]) * k]) });
  }

  // The move track's x and y are absolute; where it gives none, the caller's x and y are where the character stands.
  const at = (v, home) => (v === null || v === undefined ? home || 0 : v);
  const placement = (o, posed) => mul(translate(at(posed.move.x, o.x), at(posed.move.y, o.y)), scaleM((o.scale || 1) * posed.move.flip, o.scale || 1));

  function posedWithJaw(eff, posed) {
    const work = { parts: {} };
    Object.keys(posed.parts).forEach((id) => {
      const part = eff[id], jaw = part.mouth && part.mouth.kind === 'jaw' ? mouthOpen(posed) * (part.mouth.maxOpen || 28) * (part.sign || 1) : 0;
      work.parts[id] = Object.assign({}, posed.parts[id], { jaw });
    });
    return work;
  }

  /**
   * @param opts { x, y, scale } where the character stands (feet at x, y). A move track in the pose overrides it with absolute positions.
   *        frame: { width, height } of the picture, so a skin can reach its edges (the shadow puppet's rods).
   */
  function layout(character, skin, posed, opts) {
    const o = opts || {}, eff = effectiveParts(character, posed, skin);
    const base = placement(o, posed), W = partMatrices(eff, character, posedWithJaw(eff, posed), base);
    const items = [], shown = new Set(posed.props);
    const under = (it) => items.unshift(it);
    Object.values(eff).sort((a, b) => a.z - b.z || a.order - b.order).forEach((part) => {
      if (part.prop && !shown.has(part.id)) return;
      shapesOf(part, posed).forEach((shapeIn, si) => {
        const shape = morph(character, shapeIn), d = B.shapePath(shape);
        const ctx = { character, part, shape, d, posed, skin, frame: posed.frame, seed: character.id + ':' + part.id + ':' + si, color: (k) => B.colorOf(character, k), bounds: () => B.pathBounds(d) };
        skin.shape(ctx).forEach((prim) => items.push(Object.assign({ kind: 'path', part: part.id, m: round(W[part.id]) }, prim)));
      });
      const img = imageOf(part, posed);
      if (img) items.push(Object.assign({ kind: 'image', part: part.id, m: round(W[part.id]), src: img.src, x: img.x, y: img.y, w: img.w, h: img.h }, skin.image ? skin.image({ part, posed, skin }) : {}));
    });
    if (skin.character) skin.character({ character, posed, items, matrices: W, base, frame: o.frame, push: (it) => items.push(it), under });
    return items;
  }

  // Where a part sits on screen at this pose: used for captions, speech bubbles and tests.
  function partPoint(character, posed, opts, partId, skin) {
    const eff = effectiveParts(character, posed, skin), W = partMatrices(eff, character, posedWithJaw(eff, posed), placement(opts || {}, posed));
    const p = eff[partId].pivot, m = W[partId];
    return [m[0] * p[0] + m[2] * p[1] + m[4], m[1] * p[0] + m[3] * p[1] + m[5]];
  }

  // Every image a character uses, loaded and decoded, so that a frame never draws a half-loaded picture.
  const IMAGES = {};
  function imageSources(character) {
    const found = new Set();
    const take = (img) => img && img.src && found.add(img.src);
    character.parts.forEach((p) => {
      [p].concat(Object.values(p.variants || {})).forEach((v) => {
        take(v.image);
        if (v.mouth && v.mouth.images) Object.values(v.mouth.images).forEach(take);
      });
    });
    return Array.from(found);
  }

  function preloadImages(characters) {
    const jobs = [];
    Object.values(characters).forEach((c) => imageSources(c).forEach((src) => {
      if (IMAGES[src] || typeof Image === 'undefined') return;
      const img = new Image();
      img.src = src;
      IMAGES[src] = img;
      jobs.push(img.decode());
    }));
    return Promise.all(jobs);
  }

  // ---- canvas backend ----
  const PATTERNS = {};
  function pattern(g2, v) {
    if (!PATTERNS[v.id]) {
      const c = document.createElement('canvas');
      c.width = c.height = v.size;
      const k = c.getContext('2d');
      v.dots.forEach((d) => { k.fillStyle = d[4]; k.beginPath(); k.arc(d[0], d[1], d[2], 0, 6.2832); k.fill(); });
      PATTERNS[v.id] = g2.createPattern(c, 'repeat');
    }
    return PATTERNS[v.id];
  }

  function paint(g2, v, item) {
    if (v && v.pattern) return pattern(g2, v);
    if (v && typeof v === 'object') {
      const gr = v.grad === 'radial' ? g2.createRadialGradient(v.cx, v.cy, v.r0 || 0, v.cx, v.cy, v.r) : g2.createLinearGradient(v.x1, v.y1, v.x2, v.y2);
      v.stops.forEach((s) => gr.addColorStop(s[0], s[1]));
      return gr;
    }
    return v;
  }

  function drawCanvas(g2, items) {
    items.forEach((it) => {
      g2.save();
      g2.setTransform(it.m[0], it.m[1], it.m[2], it.m[3], it.m[4], it.m[5]);
      g2.globalAlpha = it.alpha === undefined ? 1 : it.alpha;
      if (it.shadow) { g2.shadowColor = it.shadow.color; g2.shadowBlur = it.shadow.blur; g2.shadowOffsetX = it.shadow.dx; g2.shadowOffsetY = it.shadow.dy; }
      if (it.kind === 'image') {
        const img = IMAGES[it.src];
        if (img && img.complete) g2.drawImage(img, it.x, it.y, it.w, it.h);
      } else if (it.kind === 'text') {
        g2.font = it.font; g2.textAlign = it.align || 'left'; g2.textBaseline = it.baseline || 'alphabetic';
        if (it.stroke) { g2.strokeStyle = it.stroke; g2.lineWidth = it.sw || 1; g2.lineJoin = 'round'; g2.strokeText(it.text, it.x, it.y); }
        g2.fillStyle = paint(g2, it.fill, it); g2.fillText(it.text, it.x, it.y);
      } else {
        const p = new Path2D(it.d);
        if (it.fill) { g2.fillStyle = paint(g2, it.fill, it); g2.fill(p, it.rule || 'nonzero'); }
        if (it.shadow && it.fill) { g2.shadowColor = 'rgba(0,0,0,0)'; }
        if (it.stroke) { g2.strokeStyle = it.stroke; g2.lineWidth = it.sw || 1; g2.lineCap = it.cap || 'round'; g2.lineJoin = it.join || 'round'; g2.stroke(p); }
      }
      g2.restore();
    });
  }

  // ---- SVG backend: a pool of elements, updated in place every frame ----
  const NS = 'http://www.w3.org/2000/svg';
  function createSVG(doc, parent, width, height) {
    const svg = doc.createElementNS(NS, 'svg');
    svg.setAttribute('viewBox', '0 0 ' + width + ' ' + height); svg.setAttribute('width', width); svg.setAttribute('height', height);
    const defs = doc.createElementNS(NS, 'defs'); svg.appendChild(defs); parent.appendChild(svg);
    const pool = [], gradients = new Map();
    const patternDef = (v) => {
      if (!gradients.has(v.id)) {
        const el = doc.createElementNS(NS, 'pattern');
        el.setAttribute('id', v.id); el.setAttribute('patternUnits', 'userSpaceOnUse'); el.setAttribute('width', v.size); el.setAttribute('height', v.size);
        v.dots.forEach((d) => { const c = doc.createElementNS(NS, 'circle'); c.setAttribute('cx', d[0]); c.setAttribute('cy', d[1]); c.setAttribute('r', d[2]); c.setAttribute('fill', d[4]); el.appendChild(c); });
        defs.appendChild(el); gradients.set(v.id, v.id);
      }
      return 'url(#' + v.id + ')';
    };
    const gradient = (v) => {
      if (v.pattern) return patternDef(v);
      const key = JSON.stringify(v);
      if (!gradients.has(key)) {
        const el = doc.createElementNS(NS, v.grad === 'radial' ? 'radialGradient' : 'linearGradient'), id = 'g' + gradients.size;
        el.setAttribute('id', id); el.setAttribute('gradientUnits', 'userSpaceOnUse');
        const attrs = v.grad === 'radial' ? { cx: v.cx, cy: v.cy, r: v.r } : { x1: v.x1, y1: v.y1, x2: v.x2, y2: v.y2 };
        Object.entries(attrs).forEach(([k, n]) => el.setAttribute(k, n));
        v.stops.forEach((s) => { const st = doc.createElementNS(NS, 'stop'); st.setAttribute('offset', s[0]); st.setAttribute('stop-color', s[1]); el.appendChild(st); });
        defs.appendChild(el); gradients.set(key, id);
      }
      return 'url(#' + gradients.get(key) + ')';
    };
    const paintAttr = (v) => (v && typeof v === 'object' ? gradient(v) : v || 'none');
    const TAGS = { text: 'text', image: 'image', path: 'path' };
    function update(items) {
      items.forEach((it, i) => {
        const tag = TAGS[it.kind];
        let el = pool[i];
        if (!el || el.tagName !== tag) { const n = doc.createElementNS(NS, tag); if (el) svg.replaceChild(n, el); else svg.appendChild(n); pool[i] = el = n; }
        el.style.display = '';
        el.setAttribute('transform', 'matrix(' + it.m.join(' ') + ')');
        el.setAttribute('fill', paintAttr(it.fill)); el.setAttribute('stroke', it.stroke || 'none');
        el.setAttribute('stroke-width', it.sw || 1); el.setAttribute('stroke-linecap', it.cap || 'round'); el.setAttribute('stroke-linejoin', it.join || 'round');
        el.setAttribute('opacity', it.alpha === undefined ? 1 : it.alpha); el.setAttribute('fill-rule', it.rule || 'nonzero');
        el.style.filter = it.shadow ? 'drop-shadow(' + it.shadow.dx + 'px ' + it.shadow.dy + 'px ' + it.shadow.blur / 2 + 'px ' + it.shadow.color + ')' : '';
        if (tag === 'path') el.setAttribute('d', it.d);
        else if (tag === 'image') { el.setAttribute('href', it.src); el.setAttribute('x', it.x); el.setAttribute('y', it.y); el.setAttribute('width', it.w); el.setAttribute('height', it.h); }
        else { el.setAttribute('x', it.x); el.setAttribute('y', it.y); el.setAttribute('style', 'font:' + it.font + ';text-anchor:' + ({ center: 'middle', right: 'end' }[it.align] || 'start')); el.textContent = it.text; }
      });
      for (let i = items.length; i < pool.length; i++) pool[i].style.display = 'none';
    }
    return { svg, update };
  }

  Object.assign(B, { layout, partPoint, drawCanvas, createSVG, preloadImages, imageSources, effectiveParts, matrix: { mul, translate, rotate, scale: scaleM, IDENT } });
  if (typeof module !== 'undefined' && module.exports) module.exports = B;
})(globalThis);
