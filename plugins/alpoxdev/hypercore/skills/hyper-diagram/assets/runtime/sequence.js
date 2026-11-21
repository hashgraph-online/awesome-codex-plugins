/* sequence: participants across the top, one row per message, numbered
   arrows, self calls, notes, and dividers. Spec:
   participants: [{id, label, sub, kind}]
   messages: [{from, to, label, kind}] | [{note, over: [id, id?]}] | [{divider}] */
(function () {
  'use strict';
  const HD = window.HD;
  const GAP = 48, ROW = 48, SELF = 64;

  HD.types.sequence = async function (spec, L) {
    const ps = spec.participants || [];
    const steps = spec.messages || [];
    HD.checkIds(ps, 'participant');
    const known = new Set(ps.map((p) => p.id));
    HD.checkRefs(steps.filter((s) => s.from !== undefined || s.to !== undefined), known, 'messages');
    if (!ps.length) { HD.err('NO_NODES', 'spec.participants is empty'); return; }
    if (ps.length > 9) HD.warn('DENSE_DIAGRAM', `${ps.length} participants; split the sequence`);
    const idx = new Map(ps.map((p, i) => [p.id, i]));
    for (const p of ps) HD.sizeNode(p, 'rect', { minW: 120, maxText: 150 });

    const gaps = ps.slice(1).map((p, i) => (ps[i]._w + p._w) / 2 + GAP);
    for (let pass = 0; pass < 3; pass++) {
      for (const s of steps) {
        if (!known.has(s.from) || !known.has(s.to) || !s.label) continue;
        const a = Math.min(idx.get(s.from), idx.get(s.to)), b = Math.max(idx.get(s.from), idx.get(s.to));
        const need = HD.measure(s.label, 12, 500) + 64;
        if (a === b) { if (a < gaps.length && gaps[a] < need + 24) gaps[a] = need + 24; continue; }
        let have = 0; for (let i = a; i < b; i++) have += gaps[i];
        if (have < need) for (let i = a; i < b; i++) gaps[i] += (need - have) / (b - a);
      }
    }
    const cx = [ps[0]._w / 2];
    gaps.forEach((g, i) => cx.push(cx[i] + g));
    const headH = Math.max(...ps.map((p) => p._h));
    ps.forEach((p, i) => HD.drawNode(L.nodes, p, cx[i] - p._w / 2, headH - p._h));

    let y = headH + 34, n = 0;
    for (const s of steps) {
      if (s.divider !== undefined) {
        const g = HD.svg('g', { class: 'hd-divider' }, L.groups);
        HD.svg('line', { class: 'hd-grid', x1: cx[0] - ps[0]._w / 2, y1: y, x2: cx[cx.length - 1] + ps[ps.length - 1]._w / 2, y2: y, 'stroke-dasharray': '4 4' }, g);
        const w = HD.labelSize(s.divider).w;
        const gl = HD.svg('g', { class: 'hd-gl hd-group-label k-neutral' }, L.labels);
        HD.svg('rect', { x: cx[0] - ps[0]._w / 2, y: y - 10, width: w, height: 20, rx: 10, style: 'fill:var(--card);stroke:var(--card-line)' }, gl);
        HD.svg('text', { x: cx[0] - ps[0]._w / 2 + 8, y: y + 4, text: s.divider, style: 'font:500 10.5px var(--mono);fill:var(--muted)' }, gl);
        y += 34; continue;
      }
      if (s.note !== undefined) {
        const over = (s.over || []).filter((id) => known.has(id));
        if (!over.length) { HD.err('NOTE_TARGET', 'a note needs over: [participant ids]'); continue; }
        const xs = over.map((id) => cx[idx.get(id)]);
        const note = { id: `note${n}_${y}`, label: s.note, kind: 'note', icon: false };
        const span = Math.max(...xs) - Math.min(...xs);
        HD.sizeNode(note, 'rect', { minW: Math.max(140, span + 60), minH: 36, maxText: Math.max(180, span + 20) });
        const g = HD.drawNode(L.nodes, note, (Math.min(...xs) + Math.max(...xs)) / 2 - note._w / 2, y - 6);
        g.dataset.legend = 'no';
        y += note._h + 22; continue;
      }
      if (!known.has(s.from) || !known.has(s.to)) continue;
      n++;
      const a = idx.get(s.from), b = idx.get(s.to);
      const e = { from: s.from, to: s.to, label: s.label, kind: s.kind || 'default', dashed: s.dashed };
      if (a === b) {
        const x = cx[a];
        const pts = [{ x: x + 1, y }, { x: x + 40, y }, { x: x + 40, y: y + 24 }, { x: x + 3, y: y + 24 }];
        const w = e.label ? HD.measure(e.label, 12, 500) : 0;
        HD.drawEdge(L.edges, e, { points: pts, plain: true, labelLayer: L.labels, labelAt: e.label ? { x: x + 50 + w / 2, y: y + 8 } : null });
        number(L.labels, x, y, n, e.kind);
        y += SELF; continue;
      }
      const dir = b > a ? 1 : -1;
      const pts = [{ x: cx[a], y }, { x: cx[b] - dir * 2, y }];
      HD.drawEdge(L.edges, e, { points: pts, plain: true, labelLayer: L.labels, labelAt: e.label ? { x: (cx[a] + cx[b]) / 2 + dir * 8, y: y - 12 } : null });
      number(L.labels, cx[a], y, n, e.kind);
      y += ROW;
    }
    for (let i = 0; i < ps.length; i++) HD.svg('line', { class: 'hd-lifeline', x1: cx[i], y1: headH, x2: cx[i], y2: y - 14 }, L.groups);
  };

  function number(layer, x, y, n, kind) {
    const g = HD.svg('g', { class: `hd-num e-${HD.edgeKindOf(kind)}` }, layer);
    HD.svg('circle', { cx: x, cy: y, r: 9 }, g);
    HD.svg('text', { x, y: y + 3.4, 'text-anchor': 'middle', text: String(n) }, g);
  }
})();
