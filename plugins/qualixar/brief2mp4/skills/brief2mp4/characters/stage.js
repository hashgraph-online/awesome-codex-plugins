/*
 * stage.js: a small 2D stage. It puts a backdrop, a cast of rigged characters and captions in one frame, all as a
 * pure function of time, in the skin the scene names.
 *
 *   const stage = B2M.createStage(scene, cast);       // cast: { child: <character>, ... }
 *   stage.draw(ctx2d, t);                             // or stage.items(t) for the display list (SVG backend, tests)
 *
 * scene = {
 *   width, height, skin, ground,                      // ground: the y where feet stand
 *   palette: { sky, hill1, hill2, ground, sun },      // backdrop colours; every skin restyles them
 *   hills: [{ pts: [[x, y], ...], fill: "hill1" }],   // optional silhouettes behind the cast
 *   set:   [{ type: "circle", c: [x, y], r: 90, fill: "sun", layer: "back" }],   // optional shapes (same records as a character part);
 *                                                     // layer "back" draws behind the hills, the default "front" on the ground
 *   cast:  [{ id, character, x, y, scale, facing, track }],   // x, y: where its feet are (y defaults to the ground top, so feet are never hidden); track as in rig.js, visemes included;
 *                                                       // a move key's x and y are absolute and replace x and y while it plays
 *   captions: [{ from, to, text }] }              // at the bottom, or at the top when a character stands there
 */
(function (g) {
  'use strict';
  if (typeof require === 'function' && !(g.B2M && g.B2M.SKINS)) require('./index.js');
  const B = (g.B2M = g.B2M || {});
  const IDENT = [1, 0, 0, 1, 0, 0];

  function styled(scene, skin, shape, tag, frame) {
    const d = B.shapePath(shape);
    const ctx = { character: { id: 'scene', palette: scene.palette }, part: { id: tag }, shape, d, posed: { cycles: [] }, skin, frame, seed: 'scene:' + tag, color: (k) => scene.palette[k] || B.DEFAULT_PALETTE[k] || '#ff00ff', bounds: () => B.pathBounds(d) };
    return skin.shape(ctx).map((p) => Object.assign({ kind: 'path', part: tag, m: IDENT }, p));
  }

  function backdrop(scene, skin, frame) {
    const W = scene.width, H = scene.height, rect = B.rectPath(0, 0, W, H, 0);
    const items = (skin.sky ? skin.sky({ W, H, rect, color: (k) => scene.palette[k] || '#ffffff' }) : [{ d: rect, fill: scene.palette.sky, stroke: null }])
      .map((p) => Object.assign({ kind: 'path', part: 'sky', m: IDENT }, p));
    const setItems = (layer) => (scene.set || []).forEach((sh, i) => { if ((sh.layer || 'front') === layer) items.push(...styled(scene, skin, Object.assign({ role: 'base' }, sh), 'set' + i, frame)); });
    setItems('back');
    (scene.hills || []).forEach((h, i) => {
      const pts = h.pts.concat([[W + 40, H + 40], [-40, H + 40]]);
      items.push(...styled(scene, skin, { type: 'poly', pts, smooth: false, fill: h.fill, role: 'base', shade: false }, 'hill' + i, frame));
    });
    items.push(...styled(scene, skin, { type: 'rect', x: -40, y: scene.ground, w: W + 80, h: H - scene.ground + 40, r: 0, fill: 'ground', role: 'base', shade: false }, 'ground', frame));
    setItems('front');
    return items;
  }

  // Where a cast member stands when its track's move keys say nothing, and which way it faces to begin with.
  function homeOf(c, scene) {
    return { x: c.x, y: c.y === undefined ? scene.ground : c.y, flip: c.facing === 'left' ? -1 : c.facing === 'right' ? 1 : c.flip === undefined ? 1 : c.flip };
  }

  // Every caption that is on screen now, in the order the scene lists them: overlapping captions are stacked.
  function captionsAt(scene, t) {
    return (scene.captions || []).filter((k) => t >= k.from && t < k.to).map((k) => k.text);
  }

  // Caption sizes follow the frame (1080 pixels on the short side is the reference) and stay inside the safe zone: 5%
  // margins on a landscape frame; on a 9:16 frame the zone formats.md gives (top 15%, bottom 35%, 64 px left, 192 px
  // right at 1080 wide), clear of the app's own buttons and title.
  function captionMetrics(scene) {
    const W = scene.width, H = scene.height, s = Math.min(W, H) / 1080, portrait = H > W;
    const safe = portrait ? { x0: (64 * W) / 1080, x1: W - (192 * W) / 1080, y0: 0.15 * H, y1: 0.65 * H } : { x0: 0.05 * W, x1: 0.95 * W, y0: 0.05 * H, y1: 0.95 * H - 6 * s };
    return { W, H, s, portrait, safe, font: 40 * s, lineH: 50 * s, pad: 22 * s, maxText: safe.x1 - safe.x0 - 44 * s };
  }

  // Break a caption into lines that fit: greedy by words, with a width estimate of 0.6 of the font size per letter
  // (the stage cannot measure text, and drawing must not depend on a font). A word longer than a line is cut.
  function wrapCaption(text, maxWidth, font) {
    const per = Math.max(1, Math.floor(maxWidth / (0.6 * font))), lines = [];
    let line = '';
    String(text).split(/\s+/).filter(Boolean).forEach((word) => {
      while (word.length > per) { if (line) { lines.push(line); line = ''; } lines.push(word.slice(0, per)); word = word.slice(per); }
      if (!line) line = word; else if ((line + ' ' + word).length <= per) line += ' ' + word; else { lines.push(line); line = word; }
    });
    if (line) lines.push(line);
    return lines;
  }

  const captionLines = (scene, texts) => { const m = captionMetrics(scene); return texts.flatMap((t) => wrapCaption(t, m.maxText, m.font)); };

  // Where a character is on screen: the box round everything it draws (rods and speed lines are not part of it).
  function boxOf(items) {
    let b = null;
    items.forEach((it) => {
      if (it.kind !== 'path' || it.part === 'fx' || it.part === 'rod' || !it.d) return;
      const q = B.pathBounds(B.mapPoints(it.d, (x, y) => [it.m[0] * x + it.m[2] * y + it.m[4], it.m[1] * x + it.m[3] * y + it.m[5]]));
      b = b ? { x0: Math.min(b.x0, q.x0), y0: Math.min(b.y0, q.y0), x1: Math.max(b.x1, q.x1), y1: Math.max(b.y1, q.y1) } : q;
    });
    return b;
  }

  const overlaps = (r, b) => b && r.x0 < b.x1 && r.x1 > b.x0 && r.y0 < b.y1 && r.y1 > b.y0;

  // The caption goes at the bottom of the safe zone, or at the top of it when it would cover a character.
  function defaultCaption(scene, lines, boxes) {
    if (!lines.length) return [];
    const m = captionMetrics(scene), s = m.s, h = 34 * s + 50 * s * lines.length;
    const w = Math.min(m.safe.x1 - m.safe.x0, Math.max(...lines.map((l) => l.length)) * 0.6 * m.font + 2 * m.pad), x = (m.safe.x0 + m.safe.x1) / 2 - w / 2;
    const bottom = { x0: x, x1: x + w, y0: m.safe.y1 - h, y1: m.safe.y1 }, top = { x0: x, x1: x + w, y0: m.portrait ? m.safe.y0 : 54 * s, y1: (m.portrait ? m.safe.y0 : 54 * s) + h };
    const hit = (r) => boxes.filter((b) => overlaps(r, b)).length;
    const r = hit(bottom) > 0 && hit(top) < hit(bottom) ? top : bottom, cx = (m.safe.x0 + m.safe.x1) / 2;
    const out = [{ kind: 'path', part: 'caption', m: IDENT, d: B.rectPath(r.x0, r.y0, w, h, 18 * s), fill: 'rgba(20,16,28,0.72)', stroke: null }];
    lines.forEach((text, n) => out.push({ kind: 'text', part: 'caption', m: IDENT, x: cx, y: r.y0 + 8 * s + 50 * s * (n + 1), text, align: 'center', font: '700 ' + m.font + 'px "Helvetica Neue", Arial, sans-serif', fill: '#ffffff' }));
    return out;
  }

  function createStage(scene, cast) {
    const skin = B.SKINS[scene.skin];
    if (!skin) throw new Error('unknown skin "' + scene.skin + '". Skins: ' + Object.keys(B.SKINS).join(', '));
    const opts = { steps: skin.steps, smooth: !skin.steps }, frame = { width: scene.width, height: scene.height };
    function items(t) {
      const ts = B.quantise(t, skin.steps), seed = skin.steps ? Math.round(ts * skin.steps) : 0;
      const out = backdrop(scene, skin, seed), texts = captionsAt(scene, t), lines = captionLines(scene, texts), boxes = [];
      // back to front by where the feet are now, so a character that hops or walks forward passes in front of another
      const members = scene.cast.map((c) => {
        const ch = cast[c.character], home = homeOf(c, scene), posed = B.pose(ch, c.track, t, Object.assign({ home, scale: c.scale || 1 }, opts));
        return { c, ch, home, posed, y: posed.move.y === null || posed.move.y === undefined ? home.y : posed.move.y };
      }).sort((a, b) => a.y - b.y);
      members.forEach(({ c, ch, home, posed }) => {
        const drawn = B.layout(ch, skin, posed, { x: home.x, y: home.y, scale: c.scale || 1, frame });
        out.push(...drawn);
        if (texts.length) boxes.push(boxOf(drawn));
      });
      const m = captionMetrics(scene);
      const over = skin.foreground ? skin.foreground({ W: scene.width, H: scene.height, caption: texts.join(' '), captions: texts, lines, scale: m.s, t, scene }) : [];
      return out.concat(over, skin.captions ? [] : defaultCaption(scene, lines, boxes));
    }
    function draw(g2, t) {
      g2.setTransform(1, 0, 0, 1, 0, 0);
      g2.clearRect(0, 0, scene.width, scene.height);
      B.drawCanvas(g2, items(t));
    }
    return { items, draw, skin };
  }

  // ---- checks on a whole scene, used by scripts/character_project.py -------------------------------------------------
  const rgbOf = (c) => (typeof c === 'string' && /^#[0-9a-f]{6}$/i.test(c) ? B.toRgb(c) : null);
  const hex = (rgb) => B.toHex(rgb);

  function fillAt(fill, x, y) {
    if (typeof fill === 'string') return rgbOf(fill);
    if (fill && fill.grad === 'radial') {
      const k = Math.min(1, Math.max(0, (Math.hypot(x - fill.cx, y - fill.cy) - (fill.r0 || 0)) / (fill.r - (fill.r0 || 0))));
      let i = 0;
      while (i < fill.stops.length - 2 && fill.stops[i + 1][0] < k) i++;
      const a = fill.stops[i], b = fill.stops[i + 1], u = Math.min(1, Math.max(0, (k - a[0]) / (b[0] - a[0] || 1))), p = B.toRgb(a[1]), q = B.toRgb(b[1]);
      return p.map((v, n) => v + (q[n] - v) * u);
    }
    return null;
  }

  function insidePath(d, x, y) {
    const pts = [];
    B.parsePath(d).forEach((seg) => seg.pts.forEach((p) => pts.push(p)));
    let c = false;
    for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
      if ((pts[i][1] > y) !== (pts[j][1] > y) && x < ((pts[j][0] - pts[i][0]) * (y - pts[i][1])) / (pts[j][1] - pts[i][1]) + pts[i][0]) c = !c;
    }
    return c;
  }

  // The backdrop item (and its colour) at a point of the frame: what a figure standing there is seen against.
  function backdropAt(items, x, y) {
    for (let n = items.length - 1; n >= 0; n--) {
      const it = items[n], rgb = it.kind === 'path' && it.d ? fillAt(it.fill, x, y) : null;
      if (rgb && insidePath(it.d, x, y)) return { rgb, part: it.part };
    }
    return null;
  }

  // For every cast member: where it stands every 0.1 s, which way it faces, its walks, how big it is, and the worst
  // contrast between its colours and the background behind it, sampled every half second along its path.
  function sceneReport(scene, cast) {
    const skin = B.SKINS[scene.skin], backdropItems = createStage(Object.assign({}, scene, { cast: [], captions: [] }), {}).items(0).filter((i) => i.kind === 'path' && !['panel', 'caption'].includes(i.part));
    const out = { members: {}, captions: (scene.captions || []).map((c, index) => ({ index, lines: captionLines(scene, [c.text]).length })) };
    scene.cast.forEach((m) => {
      const ch = cast[m.character], home = homeOf(m, scene), scale = m.scale || 1, o = { home, scale }, x = [], y = [], flip = [];
      const at = (t) => { const p = B.pose(ch, m.track || {}, t, o).move; return { x: p.x === null ? home.x : p.x, y: p.y === null ? home.y : p.y, flip: p.flip }; };
      for (let t = 0; t <= scene.duration + 1e-9; t += 0.1) { const p = at(t); x.push(p.x); y.push(p.y); flip.push(p.flip); }
      const walks = B.walkLayers(ch, (m.track && m.track.move) || [], scale, home).map((l) => ({ from: l.from, to: l.to, steps: l.steps }));
      const frameAt = (t, p) => B.layout(ch, skin, B.pose(ch, m.track || {}, t, { home, scale, steps: skin.steps, smooth: !skin.steps }), { x: p.x, y: p.y, scale }).filter((i) => i.kind === 'path' && typeof i.fill === 'string' && !['fx', 'rod'].includes(i.part));
      const first = frameAt(0, at(0));
      let sum = [0, 0, 0], wsum = 0;
      const colours = [];       // the figure's colours and how much of the figure each covers
      first.forEach((i) => { const c = rgbOf(i.fill), q = B.pathBounds(B.mapPoints(i.d, (px, py) => [i.m[0] * px + i.m[2] * py + i.m[4], i.m[1] * px + i.m[3] * py + i.m[5]])), a = Math.max(1, (q.x1 - q.x0) * (q.y1 - q.y0)); if (c) { sum = sum.map((v, n) => v + c[n] * a); wsum += a; colours.push([c, a]); } });
      const tone = wsum ? sum.map((v) => v / wsum) : null;
      let low = null;
      for (let t = 0; tone && t <= scene.duration + 1e-9 && !low; t += 0.5) {
        const p = at(t), box = boxOf(frameAt(t, p));
        if (!box) continue;
        [[(box.x0 + box.x1) / 2, (box.y0 + box.y1) / 2], [(box.x0 + box.x1) / 2, box.y0 + (box.y1 - box.y0) * 0.3]].forEach(([sx, sy]) => {   // behind its body, not a stone at its feet
          const bg = backdropAt(backdropItems, sx, sy);
          if (!bg || low) return;
          // hard to see when most of the figure, by area, is close in tone to what is behind it
          const blended = colours.filter(([c]) => B.contrast(c, bg.rgb) < 1.6).reduce((n, [, a]) => n + a, 0) / wsum;
          if (blended > 0.75) low = { t, part: bg.part, colour: hex(bg.rgb), ratio: B.contrast(tone, bg.rgb) };
        });
      }
      out.members[m.id] = { x, y, flip, half: ((ch.proportions.width || ch.proportions.height * 0.6) * scale) / 2, walks, tone: tone && hex(tone), low };
    });
    return out;
  }

  Object.assign(B, { createStage, homeOf, sceneReport, captionLines, captionMetrics, wrapCaption });
  if (typeof module !== 'undefined' && module.exports) module.exports = B;
})(globalThis);
