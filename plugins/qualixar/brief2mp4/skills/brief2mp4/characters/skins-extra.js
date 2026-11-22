/*
 * skins-extra.js: four more skins on the same rig, written like the first two (see skins.js for the contract).
 *
 *   line-art         strokes only: one weight of line on a plain ground, the line boils on every held drawing
 *   shadow-puppet    black leather profile silhouettes (an optional eye hole), visible rods, a warm lamp behind
 *   motion-comic     flat colour, a bold ink line, halftone dots for shadow, a panel border and a caption box
 *   flat-explainer   clean flat vector: fills only, smooth motion, no outline and no shadow
 *
 * A skin may also give the stage `sky(ctx)` (the background) and `foreground(ctx)` (anything drawn over everything).
 */
(function (g) {
  'use strict';
  if (typeof require === 'function' && !(g.B2M && g.B2M.SKINS)) require('./skins.js');
  const B = (g.B2M = g.B2M || {});
  const { roleOf, lineOf } = B.skinKit;
  const SKINS = B.SKINS;
  const lum = (hex) => B.toRgb(hex).reduce((a, b) => a + b, 0);

  // ---- line art ----
  const LINE_INK = '#151515', LINE_BG = '#fffdf8';
  SKINS['line-art'] = {
    id: 'line-art', name: 'Line art', steps: 10, bg: LINE_BG, ink: LINE_INK, jitter: 1.3,
    shape(ctx) {
      const role = roleOf(ctx.shape), s = ctx.shape;
      if (role === 'cel' || role === 'hole' || s.fill === 'blush') return [];
      const d = B.jitterPath(ctx.d, ctx.seed, ctx.frame, role === 'line' ? 0.7 : this.jitter);
      if (role === 'line' || !s.fill) return [{ d, fill: null, stroke: LINE_INK, sw: 3, cap: 'round' }];
      const size = Math.min(ctx.bounds().w, ctx.bounds().h), dot = size < 14 && lum(ctx.color(s.fill)) < 200;
      return [{ d, fill: dot ? LINE_INK : LINE_BG, stroke: LINE_INK, sw: role === 'detail' || role === 'mouth' ? 1.6 : Math.min(3.2, Math.max(1.5, size * 0.09)) }];
    },
    sky: (c) => [{ d: c.rect, fill: LINE_BG, stroke: null }],
  };

  // ---- shadow puppet ----
  const LEATHER = '#150b06', LAMP = '#f7c470', ROD = '#2c180a';
  const screenPoint = (m, p) => [m[0] * p[0] + m[2] * p[1] + m[4], m[1] * p[0] + m[3] * p[1] + m[5]];
  function rods(ctx) {
    const ix = ctx.character.parts.reduce((o, p) => { o[p.id] = p; return o; }, {}), out = [];
    const bottom = ctx.frame ? ctx.frame.height + 20 : 1400;      // rods run off the bottom of the frame: that is how a puppet is held
    const rod = (from, to, w) => out.push({ kind: 'path', part: 'rod', m: [1, 0, 0, 1, 0, 0], d: 'M' + B.fmt(from[0]) + ' ' + B.fmt(from[1]) + 'L' + B.fmt(to[0]) + ' ' + B.fmt(to[1]), fill: null, stroke: ROD, sw: w, cap: 'butt' });
    if (ix.torso) { const a = screenPoint(ctx.matrices.torso, ix.torso.pivot); rod([a[0], a[1] - 30], [a[0], bottom], 6 * (ctx.frame ? ctx.frame.height / 1080 : 1)); }
    ['handN', 'handF'].forEach((h) => {
      if (!ix[h]) return;
      const a = screenPoint(ctx.matrices[h], ix[h].pivot), dir = ctx.posed.move.flip;
      rod(a, [a[0] + 70 * dir * ((bottom - a[1]) / 420), bottom], 3.5 * (ctx.frame ? ctx.frame.height / 1080 : 1));
    });
    out.reverse().forEach((it) => ctx.under(it));
  }

  // A shadow puppet is a flat leather profile: one black shape per part, rods below, a lamp behind. The only thing
  // cut out is an optional eye hole and the hinged jaw's gap; no brows, mouth, pupils or patterns, and no front view
  // (profileOnly). Parts with a "shadow" variant are redrawn with a profile edge (nose, lips, chin, hem, cuffs, hands).
  // The jaw is a separate leather piece on a hinge (parts jaw and jawGap): it swings open with the mouth shape.
  // Scenery uses the screen's own tones so black figures never vanish into it: mid-tone hills, a mid-brown ground,
  // black set pieces, and set shapes with role "light" (sun, moon, lamp, fire) stay light.
  const SCREEN = { hills: ['#d98a35', '#bd6a22'], ground: '#a85a1c', light: '#fff4c2' };
  function scenery(ctx, role) {
    const id = ctx.part.id, hill = /^hill(\d+)/.exec(id);
    if (hill) return [{ d: ctx.d, fill: SCREEN.hills[Math.min(+hill[1], SCREEN.hills.length - 1)], stroke: null }];
    if (id === 'ground') return [{ d: ctx.d, fill: SCREEN.ground, stroke: null }];
    if (role === 'light') return [{ d: ctx.d, fill: SCREEN.light, stroke: null }];
    return ctx.shape.fill ? [{ d: ctx.d, fill: LEATHER, stroke: null }] : [lineOf(ctx, 1, { stroke: LEATHER })];
  }

  SKINS['shadow-puppet'] = {
    id: 'shadow-puppet', name: 'Shadow puppetry', steps: 12, bg: '#e8a24e', ink: LEATHER, profileOnly: true, variant: 'shadow', screen: SCREEN,
    shape(ctx) {
      const role = roleOf(ctx.shape), s = ctx.shape, id = ctx.part.id;
      if (ctx.character.id === 'scene') return scenery(ctx, role);
      if (role === 'cel' || /^(brow|pupil)/.test(id) || (id === 'mouth' && ctx.part.mouth.kind === 'lips')) return [];
      if (role === 'hole') return [{ d: ctx.d, fill: LAMP, stroke: null }];
      if (/^eye/.test(id)) return role === 'base' && s.fill && lum(ctx.color(s.fill)) > 600 ? [{ d: ctx.d, fill: LAMP, stroke: null }] : [];
      if (role === 'line') return [lineOf(ctx, 1.25, { stroke: LEATHER })];
      return s.fill ? [{ d: ctx.d, fill: LEATHER, stroke: null }] : [];
    },
    character: rods,
    sky: (c) => [{ d: c.rect, fill: { grad: 'radial', cx: c.W / 2, cy: c.H * 0.5, r0: 40, r: c.W * 0.7, stops: [[0, '#ffe29a'], [0.55, '#f0a64a'], [1, '#c4691f']] }, stroke: null }],
  };

  // ---- motion comic ----
  const HALFTONE = { pattern: 'halftone', id: 'b2m-halftone', size: 8, dots: [[2, 2, 1.7, 0, 'rgba(16,16,16,0.6)'], [6, 6, 1.7, 0, 'rgba(16,16,16,0.6)']] };
  const COMIC_INK = '#101010';
  SKINS['motion-comic'] = {
    id: 'motion-comic', name: 'Motion comic', steps: null, bg: '#f0ead8', ink: COMIC_INK, captions: true,
    shape(ctx) {
      const role = roleOf(ctx.shape), s = ctx.shape;
      if (role === 'cel') return [{ d: ctx.d, fill: HALFTONE, stroke: null }];
      if (role === 'line' || !s.fill) return [lineOf(ctx, 1.1, { stroke: COMIC_INK })];
      if (role === 'hole') return [{ d: ctx.d, fill: '#ffffff', stroke: COMIC_INK, sw: 2 }];
      const small = Math.min(ctx.bounds().w, ctx.bounds().h);
      const sw = ctx.color(s.fill) === ctx.color('ink') || small < 7 ? 0 : Math.min(3.6, Math.max(1.5, small * 0.07));
      return [{ d: ctx.d, fill: ctx.color(s.fill), stroke: sw ? COMIC_INK : null, sw: role === 'detail' || role === 'mouth' ? Math.min(sw, 1.8) : sw }];
    },
    sky: (c) => [{ d: c.rect, fill: c.color('sky'), stroke: null }, { d: c.rect, fill: HALFTONE, stroke: null, alpha: 0.18 }],
    foreground(c) {
      const k = c.scale || 1, one = [1, 0, 0, 1, 0, 0], ink = COMIC_INK;
      const out = [{ kind: 'path', part: 'panel', m: one, d: B.rectPath(36 * k, 36 * k, c.W - 72 * k, c.H - 72 * k, 0), fill: null, stroke: ink, sw: 14 * k, join: 'miter' }];
      (c.lines || []).forEach((text, n) => {           // the caption box: one yellow box per line, stacked
        const w = Math.min(c.W - 160 * k, (60 + text.length * 26) * k), y = (80 + n * 92) * k;
        out.push({ kind: 'path', part: 'caption', m: one, d: B.rectPath(80 * k, y, w, 84 * k, 0), fill: '#ffd23f', stroke: ink, sw: 6 * k, join: 'miter' },
          { kind: 'text', part: 'caption', m: one, x: 104 * k, y: y + 58 * k, text, font: '800 ' + 40 * k + 'px "Helvetica Neue", Arial, sans-serif', fill: ink });
      });
      return out;
    },
  };

  // ---- flat explainer ----
  SKINS['flat-explainer'] = {
    id: 'flat-explainer', name: 'Flat vector explainer', steps: null, bg: '#f5f7fb', ink: '#1f2a44',
    shape(ctx) {
      const role = roleOf(ctx.shape), s = ctx.shape;
      if (role === 'cel') return [];
      if (role === 'line' || !s.fill) return [lineOf(ctx, 0.9, { stroke: B.mix(ctx.color(s.stroke || 'ink'), '#1f2a44', 0.4) })];
      if (role === 'hole') return [{ d: ctx.d, fill: '#ffffff', stroke: null }];
      return [{ d: ctx.d, fill: ctx.color(s.fill), stroke: null }];
    },
    sky: (c) => [{ d: c.rect, fill: c.color('sky'), stroke: null }],
  };

  B.HALFTONE = HALFTONE;
  if (typeof module !== 'undefined' && module.exports) module.exports = B;
})(globalThis);
