/*
 * skins.js: the same rig in different art forms. A skin is a style map plus per-frame effect hooks:
 *
 *   id, name       the art-form page it follows (references/art-forms/<id>.md)
 *   steps          drawings per second for handmade looks, null for smooth looks (pass it to B2M.pose as opts.steps)
 *   variant        optional: parts that have a variant with this name are redrawn (the anime skin's eyes and hair)
 *   shape(ctx)     turns one shape of one part into 0..n drawing primitives (fill, outline, shadow, wobble, grain)
 *   image(ctx)     optional: extra properties for an image part (a drop shadow)
 *   character(ctx) optional: adds primitives for the whole character (speed lines, rods)
 *
 * Every wobble comes from B2M.jitterPath, which is seeded by (shape, drawing number): two renders match.
 */
(function (g) {
  'use strict';
  if (typeof require === 'function' && !(g.B2M && g.B2M.layout)) require('./render.js');
  const B = (g.B2M = g.B2M || {});
  const SKINS = {};

  const roleOf = (shape) => shape.role || 'base';
  const lineOf = (ctx, sw, extra) => Object.assign({ d: ctx.d, fill: null, stroke: ctx.color(ctx.shape.stroke || 'ink'), sw: (ctx.shape.sw || 2) * sw, cap: 'round' }, extra);

  // A tile of paper fibres: seeded dots, light and dark, laid over every layer of the paper skin.
  function makeGrain(size, count) {
    const dots = [];
    for (let i = 0; i < count; i++) {
      const dark = B.hash('grain', i * 3) < 0.55;
      dots.push([Math.round(B.hash('grain', i * 3 + 1) * size * 10) / 10, Math.round(B.hash('grain', i * 3 + 2) * size * 10) / 10, Math.round((0.5 + B.hash('grain', i + 900) * 0.9) * 10) / 10, 0, dark ? 'rgba(90,60,30,0.07)' : 'rgba(255,255,255,0.13)']);
    }
    return { pattern: 'grain', id: 'b2m-grain', size, dots };
  }
  const GRAIN = makeGrain(36, 54);

  // Paper cut-out: flat fills, a thin lighter cut edge (the paper core), grain, a tight shadow under every layer,
  // and edges that wobble a little on every held drawing.
  const PAPER = '#f3e6c8';
  SKINS['paper-cutout'] = {
    id: 'paper-cutout', name: 'Paper cut-out', steps: 12, bg: '#f3e6c8', ink: '#4a3320', jitter: 0.9,
    shape(ctx) {
      const role = roleOf(ctx.shape), s = ctx.shape;
      const wobble = (d) => B.jitterPath(d, ctx.seed, ctx.frame, role === 'line' ? 0.5 : this.jitter);
      if (role === 'cel') return [];
      if (role === 'line' || !s.fill) return [lineOf(ctx, 0.9, { d: wobble(ctx.d), stroke: B.mix(ctx.color(s.stroke || 'ink'), '#4a3320', 0.35) })];
      if (role === 'hole') return [{ d: ctx.d, fill: '#fbf5e4', stroke: null }];
      const col = B.mix(ctx.color(s.fill), PAPER, 0.12), d = wobble(ctx.d);
      if (role !== 'base') return [{ d, fill: col, stroke: null }];
      const out = [{ d, fill: col, stroke: B.mix(col, '#fffaf0', 0.62), sw: 1.6, shadow: { dx: 3, dy: 4, blur: 5, color: 'rgba(70,40,10,0.38)' } }];
      if (Math.min(ctx.bounds().w, ctx.bounds().h) > 9) out.push({ d, fill: GRAIN, stroke: null, alpha: 0.8 });
      return out;
    },
    image() { return { shadow: { dx: 3, dy: 4, blur: 5, color: 'rgba(70,40,10,0.38)' } }; },
  };

  // Anime / cel shading: the design changes, not only the line. Parts with an "anime" variant are redrawn (big eyes
  // with two highlights, spiky hair with a shine band, a tick for a nose), hard shadow shapes drawn into the
  // character (role "cel") are filled in a tinted dark tone, and a jump or a run throws speed lines.
  function speedLines(ctx) {
    const p = ctx.posed, run = p.cycles.indexOf('run') >= 0, up = p.lift < -0.12;
    if (!(p.speedLines || run || up)) return;
    const ink = B.colorOf(ctx.character, 'ink'), h = ctx.character.proportions.height, out = [], y0 = -0.5 * h + p.lift * ctx.character.proportions.legLength;
    for (let i = 0; i < 11; i++) {
      const a = B.hash(ctx.character.id + 'sl', p.frame * 17 + i), b = B.hash(ctx.character.id + 'sm', p.frame * 17 + i), len = 0.45 * h + b * 0.55 * h, w = 1.8 + a * 2.2;
      const d = run || p.speedLines
        ? 'M' + B.fmt(-h * 0.2) + ' ' + B.fmt(-a * h * 0.95 - w) + 'L' + B.fmt(-h * 0.2 - len) + ' ' + B.fmt(-a * h * 0.95) + 'L' + B.fmt(-h * 0.2) + ' ' + B.fmt(-a * h * 0.95 + w) + 'Z'
        : 'M' + B.fmt(-h * 0.25 + a * h * 0.5 - w) + ' ' + B.fmt(y0) + 'L' + B.fmt(-h * 0.25 + a * h * 0.5) + ' ' + B.fmt(y0 + len) + 'L' + B.fmt(-h * 0.25 + a * h * 0.5 + w) + ' ' + B.fmt(y0) + 'Z';
      out.push({ kind: 'path', part: 'fx', m: ctx.base, d, fill: ink, stroke: null, alpha: 0.7 });
    }
    out.reverse().forEach((it) => ctx.under(it));
  }

  SKINS['cel-shaded'] = {
    id: 'cel-shaded', name: 'Anime and cel shading', steps: 12, bg: '#ffe0b0', ink: '#1b1530', variant: 'anime',
    shape(ctx) {
      const role = roleOf(ctx.shape), s = ctx.shape, ink = ctx.color('ink');
      if (role === 'line' || !s.fill) return [lineOf(ctx, 1.15)];
      const base = ctx.color(s.fill), b = ctx.bounds(), small = Math.min(b.w, b.h);
      const tint = (c) => B.mix(B.mix(c, '#2b2170', 0.4), '#000000', 0.08);
      if (role === 'cel') return [{ d: ctx.d, fill: tint(base), stroke: null }];
      // outline weight follows the size of the shape, so an eye gets a fine line and a torso a bold one
      const sw = base === ink || small < 7 ? 0 : Math.min(3.4, Math.max(1.5, small * 0.07));
      const stroke = sw ? ink : null;
      if (role === 'hole') return [{ d: ctx.d, fill: '#ffffff', stroke: ink, sw: 2 }];
      if (role === 'detail' || role === 'mouth') return [{ d: ctx.d, fill: base, stroke: role === 'mouth' && s.fill !== 'mouth' ? null : stroke, sw: Math.min(sw, 1.8) }];
      if (s.shade === false || small < 12) return [{ d: ctx.d, fill: base, stroke, sw }];
      const lit = B.mix(base, '#ffffff', 0.1);
      const litD = B.mapPoints(ctx.d, (x, y) => [b.cx + (x - b.cx) * 0.8 - b.w * 0.08, b.cy + (y - b.cy) * 0.8 - b.h * 0.1]);
      return [{ d: ctx.d, fill: tint(base), stroke, sw }, { d: litD, fill: lit, stroke: null }];
    },
    character: speedLines,
  };

  // The scene stage asks a skin for its sky and its foreground (panel border, caption box) when it has them.
  SKINS['paper-cutout'].sky = (c) => [{ d: c.rect, fill: c.color('sky'), stroke: null }];

  Object.assign(B, { SKINS, GRAIN, skinKit: { roleOf, lineOf } });
  if (typeof module !== 'undefined' && module.exports) module.exports = B;
})(globalThis);
