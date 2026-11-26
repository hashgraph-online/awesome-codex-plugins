// Layout audit for a rendered Mini App screen: the geometry a CSS lint cannot see.
// Measures every surface (card, inset group, banner, plan card: a rounded box with its own background or
// border) and reports the rules of references/mini-apps/design-system.md section 5 (S1-S6):
//   LA01 surface-gap    two stacked surfaces closer than 12 px (error below 8: touching or nearly)
//   LA02 text-inset     content closer than 16 px to a surface's side edge (error below 12), or than 12 px to its
//                       top / bottom (error below 8)
//   LA03 radius-mix     more than three corner radii on one screen, or a radius that is not a kit token
//   LA04 nested-radius  a surface inside a surface with a larger radius than its parent
//   LA05 edge-margin    a surface that is neither full-bleed nor at least 12 px from the screen edge
// No dependencies. analyze() is pure (unit-tested); collect() reads the DOM; audit() does both and can outline
// the findings on the page. The preview stand runs it with ?audit=1; any app can import it in a dev build.

const CONTROL_TAGS = new Set(['BUTTON', 'INPUT', 'SELECT', 'TEXTAREA', 'A', 'LABEL']);
const SKIP_TAGS = new Set(['SCRIPT', 'STYLE', 'SVG', 'IMG', 'VIDEO', 'CANVAS', 'PICTURE', 'svg']);
const CONTROL_ROLES = new Set(['button', 'tab', 'switch', 'checkbox', 'menuitem', 'option', 'slider']);

/** @typedef {{x: number, y: number, w: number, h: number}} Rect */
/** @typedef {{id: string, label: string, rect: Rect, radius: number, parent: string | null, content: Rect[], list?: boolean}} Surface */

export const LIMITS = Object.freeze({
  gapError: 8, gapWarn: 12,        // between stacked surfaces; the kit puts 16 (cards) or 24 (sections)
  sideError: 12, sideWarn: 16,     // content to a surface's left / right edge
  endError: 8, endWarn: 12,        // content to its top / bottom edge
  edge: 12,                        // a surface to the screen edge, unless it is full-bleed
  radii: 3,                        // distinct corner radii on one screen (pills excluded)
});

const right = (r) => r.x + r.w;
const bottom = (r) => r.y + r.h;
const overlapX = (a, b) => Math.max(0, Math.min(right(a), right(b)) - Math.max(a.x, b.x));
const round = (n) => Math.round(n * 10) / 10;

/** Findings for a screen snapshot: {viewport: {w, h}, surfaces: Surface[], tokens?: {radii: number[]}}. */
export function analyze(snapshot, limits = LIMITS) {
  const out = [];
  const add = (rule, level, surface, msg) => out.push({ rule, level, id: surface.id, label: surface.label, msg });
  const surfaces = snapshot.surfaces;
  const vw = snapshot.viewport.w;

  // LA01: each surface and the next one below it in the same column with the same parent
  for (const a of surfaces) {
    const below = surfaces
      .filter((b) => b !== a && b.parent === a.parent && b.rect.y >= bottom(a.rect) - 1
        && overlapX(a.rect, b.rect) > 0.5 * Math.min(a.rect.w, b.rect.w))
      .sort((p, q) => p.rect.y - q.rect.y)[0];
    if (!below) continue;
    const gap = below.rect.y - bottom(a.rect);
    if (gap < limits.gapWarn) {
      add('LA01', gap < limits.gapError ? 'error' : 'warn', below,
        `${round(gap)} px between ${a.label} and ${below.label}: stacked surfaces sit 16 px apart (cards, groups) or 24 px (sections); never touching`);
    }
  }

  // LA02: content inset per surface (its own content only: the collector leaves nested surfaces' text out)
  for (const s of surfaces) {
    if (!s.content.length) continue;
    const left = Math.min(...s.content.map((c) => c.x - s.rect.x));
    const rightGap = Math.min(...s.content.map((c) => right(s.rect) - right(c)));
    // A list's rows set its vertical rhythm (52 / 68 px rows): only text squeezed against its top or bottom counts.
    const endError = s.list ? 6 : limits.endError;
    const endWarn = s.list ? 6 : limits.endWarn;
    const top = Math.min(...s.content.map((c) => c.y - s.rect.y));
    const bot = Math.min(...s.content.map((c) => bottom(s.rect) - bottom(c)));
    const side = Math.min(left, rightGap) + 1; // 1 px of tolerance for sub-pixel layout and glyph boxes
    const end = Math.min(top, bot) + 1;
    if (side < limits.sideWarn) {
      add('LA02', side < limits.sideError ? 'error' : 'warn', s,
        `content ${round(side - 1)} px from the side of ${s.label} (radius ${round(s.radius)}): 16 px inside every surface`);
    }
    if (end < endWarn) {
      add('LA02', end < endError ? 'error' : 'warn', s,
        `content ${round(end - 1)} px from the ${top <= bot ? 'top' : 'bottom'} of ${s.label}: 12 px or more (16 in cards)`);
    }
  }

  // LA03: one radius scale
  const radii = [...new Set(surfaces.filter((s) => s.radius > 0).map((s) => Math.round(s.radius)))].sort((a, b) => a - b);
  if (radii.length > limits.radii) {
    out.push({ rule: 'LA03', level: 'warn', id: null, label: 'screen',
      msg: `${radii.length} corner radii on one screen (${radii.join(', ')} px): groups and cards share one radius, nested ones one smaller` });
  }
  const tokens = (snapshot.tokens?.radii || []).map(Math.round).filter((r) => r > 0);
  if (tokens.length) {
    for (const s of surfaces) {
      const r = Math.round(s.radius);
      if (r > 0 && !tokens.some((t) => Math.abs(t - r) <= 1)) {
        add('LA03', 'warn', s, `${s.label} has a ${r} px radius; the kit's radii are ${tokens.join(', ')} px`);
      }
    }
  }

  // LA04: nested radius never larger than the parent's
  const byId = new Map(surfaces.map((s) => [s.id, s]));
  for (const s of surfaces) {
    const p = s.parent ? byId.get(s.parent) : null;
    if (p && s.radius > p.radius + 0.5) {
      add('LA04', 'warn', s, `${s.label} (${round(s.radius)} px) is rounder than ${p.label} around it (${round(p.radius)} px): inner radius = outer minus padding`);
    }
  }

  // LA05: off the screen edge, or full-bleed
  for (const s of surfaces) {
    if (s.parent || s.rect.x < -0.5 || right(s.rect) > vw + 0.5) continue; // nested, or in a horizontal scroller
    const l = s.rect.x;
    const r = vw - right(s.rect);
    const fullBleed = l <= 0.5 && r <= 0.5;
    if (!fullBleed && Math.min(l, r) < limits.edge) {
      add('LA05', 'warn', s, `${s.label} is ${round(Math.min(l, r))} px from the screen edge: 16 px (the safe area in landscape), or full width`);
    }
  }
  return out;
}

/* ---------------------------------------------------------------- DOM */

function alpha(color) {
  const m = color.match(/rgba?\(([^)]+)\)/);
  if (!m) return color === 'transparent' ? 0 : 1;
  const parts = m[1].split(/[\s,/]+/).filter(Boolean);
  return parts.length > 3 ? parseFloat(parts[3]) : 1;
}

function rectOf(r) { return { x: r.left, y: r.top, w: r.width, h: r.height }; }

function describe(el) {
  const cls = typeof el.className === 'string' ? el.className.trim().split(/\s+/).filter(Boolean).slice(0, 2).join('.') : '';
  const text = (el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 28);
  return `${el.tagName.toLowerCase()}${el.id ? '#' + el.id : ''}${cls ? '.' + cls : ''}${text ? ` "${text}"` : ''}`;
}

function isVisible(el, cs) {
  if (cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity) === 0) return false;
  const r = el.getBoundingClientRect();
  return r.width > 0 && r.height > 0;
}

function isControl(el) {
  return CONTROL_TAGS.has(el.tagName) || CONTROL_ROLES.has(el.getAttribute('role') || '');
}

/** border-radius in px; a percentage resolves against the shorter side (50% of a square is a circle). */
function radiusOf(cs, r) {
  const v = cs.borderTopLeftRadius || '0';
  const n = parseFloat(v) || 0;
  return v.trim().endsWith('%') ? (n / 100) * Math.min(r.width, r.height) : n;
}

function isSurface(el, cs, win) {
  if (SKIP_TAGS.has(el.tagName) || cs.position === 'fixed' || cs.position === 'sticky') return false;
  if (isControl(el) && el.getAttribute('role') !== 'radio') return false;
  const r = el.getBoundingClientRect();
  if (r.width < 120 || r.height < 28) return false;
  const radius = radiusOf(cs, r);
  // chips, fields, segmented controls and capsule buttons: short and fully rounded; a taller capsule is a card
  if (radius < 6 || (r.height < 44 && radius >= r.height / 2 - 1) || radius >= r.width / 2 - 1) return false;
  const filled = alpha(cs.backgroundColor) > 0.04 && cs.backgroundColor !== win.getComputedStyle(el.parentElement || el).backgroundColor;
  const bordered = parseFloat(cs.borderTopWidth) > 0 && alpha(cs.borderTopColor) > 0.04;
  const image = cs.backgroundImage && cs.backgroundImage !== 'none';
  return filled || bordered || image;
}

/** Content outside its surface is clipped or scrolled away (a closed <details>, a scroller): not measured. */
function inside(c, s) {
  return c.h > 0 && c.x >= s.x - 1 && c.y >= s.y - 1 && c.x + c.w <= s.x + s.w + 1 && c.y + c.h <= s.y + s.h + 1;
}

/** Inside a closed <details> (not its summary): laid out by some engines, never drawn. */
function folded(el) {
  const d = el.closest('details:not([open])');
  return !!d && !el.closest('summary');
}

function overlaid(el, surfaceEl, win) {
  for (let e = el; e && e !== surfaceEl; e = e.parentElement) {
    if (win.getComputedStyle(e).position === 'absolute') return true;
  }
  return false;
}

/** A snapshot of the document's visible surfaces and the content each one holds. */
export function collect(doc = document) {
  const win = doc.defaultView;
  const surfaces = [];
  const owner = new Map(); // element -> nearest surface id (itself or an ancestor)
  let n = 0;
  const walk = (el, parentSurface) => {
    const cs = win.getComputedStyle(el);
    if (!isVisible(el, cs)) return;
    let here = parentSurface;
    if (isSurface(el, cs, win)) {
      const id = `s${++n}`;
      surfaces.push({ id, label: describe(el), rect: rectOf(el.getBoundingClientRect()), radius: radiusOf(cs, el.getBoundingClientRect()),
        parent: parentSurface ? parentSurface.id : null, content: [], el,
        // rows set the rhythm of lists, key-value blocks and tables
        list: ['UL', 'OL', 'DL', 'TABLE'].includes(el.tagName) || ['list', 'table'].includes(el.getAttribute('role') || '')
          || !!el.querySelector(':scope > table, :scope > ul, :scope > ol, :scope > dl') });
      here = surfaces[surfaces.length - 1];
    }
    owner.set(el, here);
    for (const child of el.children) walk(child, here);
  };
  walk(doc.body, null);

  // content: text runs, and controls narrower than their surface (a full-width row's text is measured instead)
  const sw = doc.createTreeWalker(doc.body, 4 /* NodeFilter.SHOW_TEXT */);
  for (let t = sw.nextNode(); t; t = sw.nextNode()) {
    if (!t.textContent.trim()) continue;
    const el = t.parentElement;
    const s = el && owner.get(el);
    if (!s || s.el === undefined) continue;
    if (overlaid(el, s.el, win)) continue; // a badge or a caption laid over media sits on purpose near its corner
    if (folded(el)) continue;
    const control = el.closest('button, a, input, select, textarea, [role=button], [role=tab]');
    if (control && s.el.contains(control) && control !== s.el && control.getBoundingClientRect().width < 0.9 * s.rect.w) continue;
    const range = doc.createRange();
    range.selectNodeContents(t);
    // A glyph box taller than its line (a big figure at line-height 1) is clipped to the line: that is what is drawn.
    const line = el.getBoundingClientRect();
    for (const r of range.getClientRects()) {
      if (!(r.width > 0 && r.height > 0)) continue;
      const y = Math.max(r.top, line.top);
      const box = { x: r.left, y, w: r.width, h: Math.min(r.bottom, line.bottom) - y };
      if (inside(box, s.rect)) s.content.push(box);
    }
  }
  for (const s of surfaces) {
    for (const c of s.el.querySelectorAll('button, input, select, textarea, [role=button], [role=tab]')) {
      if (owner.get(c) !== s) continue;
      const r = c.getBoundingClientRect();
      if (!(r.width > 0 && r.width < 0.9 * s.rect.w) || c.closest('[hidden]') || folded(c) || overlaid(c, s.el, win)) continue;
      const cs = win.getComputedStyle(c);
      const drawn = alpha(cs.backgroundColor) > 0.04 || (parseFloat(cs.borderTopWidth) > 0 && alpha(cs.borderTopColor) > 0.04);
      if (drawn) { if (inside(rectOf(r), s.rect)) s.content.push(rectOf(r)); continue; }
      // a transparent control (an icon button's 44 px target) is as far in as what it draws
      for (const g of c.querySelectorAll('svg, img')) {
        const gr = g.getBoundingClientRect();
        if (gr.width > 0 && inside(rectOf(gr), s.rect)) s.content.push(rectOf(gr));
      }
    }
  }
  const rootCs = win.getComputedStyle(doc.documentElement);
  const radii = ['--tma-r-group', '--tma-r-inner', '--tma-r-sheet'].map((v) => parseFloat(rootCs.getPropertyValue(v))).filter((x) => x > 0);
  return { viewport: { w: doc.documentElement.clientWidth, h: win.innerHeight }, surfaces, tokens: { radii } };
}

/** Runs the audit; with outline, draws each finding's surface on the page (red: error, amber: warning). */
export function audit(doc = document, { outline = false } = {}) {
  // Measure the settled screen: a push animation caught mid-way (or paused in a background tab) reads as
  // invisible or shifted.
  for (const a of doc.getAnimations?.() || []) {
    try { a.finish(); } catch { /* an infinite loader cannot finish: it is not layout */ }
  }
  const snap = collect(doc);
  const findings = analyze(snap);
  if (outline) {
    const els = new Map(snap.surfaces.map((s) => [s.id, s.el]));
    for (const f of findings) {
      const el = f.id && els.get(f.id);
      if (el) el.style.outline = `2px dashed ${f.level === 'error' ? 'red' : 'orange'}`;
    }
  }
  return { surfaces: snap.surfaces.length, errors: findings.filter((f) => f.level === 'error').length,
    warnings: findings.filter((f) => f.level === 'warn').length, findings };
}
