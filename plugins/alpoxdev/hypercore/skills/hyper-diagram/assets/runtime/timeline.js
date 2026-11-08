/* timeline, gantt, and layers.
   timeline: events: [{id, date, label, sub, kind}] in order, cards alternate above and below one axis
   gantt:    tasks: [{id, label, start, end | days | after, kind, section, milestone}], today
   layers:   layers: [{id, label, sub, kind, items: [{id, label, sub, kind}]}] stacked top to bottom */
(function () {
  'use strict';
  const HD = window.HD;
  const DAY = 86400000;

  HD.types.timeline = async function (spec, L) {
    const ev = spec.events || [];
    HD.checkIds(ev, 'event');
    if (!ev.length) { HD.err('NO_NODES', 'spec.events is empty'); return; }
    for (const e of ev) HD.sizeNode(e, 'rect', { maxText: 170, minW: 140 });
    const xs = [];
    ev.forEach((e, i) => {
      let x = i ? xs[i - 1] + 56 : e._w / 2;
      if (i > 1) x = Math.max(x, xs[i - 2] + (ev[i - 2]._w + e._w) / 2 + 24);
      xs.push(x);
    });
    const upH = Math.max(...ev.filter((e, i) => i % 2 === 0).map((e) => e._h));
    const axisY = upH + 58;
    const x0 = xs[0] - ev[0]._w / 2 - 12, x1 = xs[xs.length - 1] + ev[ev.length - 1]._w / 2 + 12;
    HD.svg('line', { class: 'hd-axis', x1: x0, y1: axisY, x2: x1, y2: axisY }, L.groups);
    ev.forEach((e, i) => {
      const up = i % 2 === 0, x = xs[i];
      const y = up ? axisY - 58 - e._h : axisY + 58;
      HD.svg('line', { class: 'hd-grid', x1: x, y1: up ? y + e._h : axisY, x2: x, y2: up ? axisY : y, style: `stroke:var(--k-${HD.kindOf(e.kind)});stroke-width:1.4` }, L.groups);
      HD.drawNode(L.nodes, e, x - e._w / 2, y);
      const dot = HD.svg('g', { class: `k-${HD.kindOf(e.kind)}` }, L.labels);
      HD.svg('circle', { cx: x, cy: axisY, r: 6, style: 'fill:var(--card);stroke:var(--c);stroke-width:2.4' }, dot);
      if (e.date) {
        const s = HD.labelSize(e.date);
        const gl = HD.svg('g', { class: `hd-elabel e-default` }, L.labels);
        const cy = up ? axisY + 22 : axisY - 22;
        HD.svg('rect', { x: x - s.w / 2, y: cy - 10, width: s.w, height: 20, rx: 10 }, gl);
        HD.svg('text', { x, y: cy + 3.8, 'text-anchor': 'middle', text: e.date, style: 'fill:var(--ink)' }, gl);
      }
    });
  };

  function day(s, what) {
    const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(s || ''));
    if (!m) { HD.err('BAD_DATE', `${what} must be YYYY-MM-DD: ${JSON.stringify(s)}`); return null; }
    return Date.UTC(+m[1], +m[2] - 1, +m[3]) / DAY;
  }
  const fmt = (d) => { const t = new Date(d * DAY); return `${t.getUTCMonth() + 1}/${t.getUTCDate()}`; };

  HD.types.gantt = async function (spec, L) {
    const tasks = spec.tasks || [];
    HD.checkIds(tasks, 'task');
    if (!tasks.length) { HD.err('NO_NODES', 'spec.tasks is empty'); return; }
    const by = new Map(tasks.map((t) => [t.id, t]));
    for (let pass = 0; pass < tasks.length + 1; pass++) {
      for (const t of tasks) {
        if (t._s !== undefined) continue;
        if (t.after) { const p = by.get(t.after); if (!p) { HD.err('UNKNOWN_ENDPOINT', `task ${t.id} is after unknown ${t.after}`); t._s = null; continue; } if (p._e === undefined) continue; t._s = p._e; }
        else t._s = day(t.start, `task ${t.id} start`);
        if (t._s === null) { t._e = null; continue; }
        if (t.milestone) t._e = t._s;
        else if (t.end) t._e = day(t.end, `task ${t.id} end`) + 1;
        else if (t.days) t._e = t._s + Number(t.days);
        else { HD.err('TASK_LENGTH', `task ${t.id} needs end, days, or milestone`); t._e = t._s + 1; }
        if (t._e !== null && t._e < t._s) HD.err('BAD_DATE', `task ${t.id} ends before it starts`);
      }
    }
    const ok = tasks.filter((t) => t._s != null && t._e != null);
    if (!ok.length) return;
    const lo = Math.min(...ok.map((t) => t._s)), hi = Math.max(...ok.map((t) => t._e)) + (ok.some((t) => t.milestone) ? 1 : 0);
    const span = Math.max(1, hi - lo);
    const px = Math.min(44, Math.max(5, 760 / span));
    const labW = Math.max(120, ...tasks.map((t) => HD.measure(t.label || t.id, 12, 500)), ...tasks.map((t) => (t.section ? HD.measure(t.section, 11, 700) : 0))) + 24;
    const X = (d) => labW + (d - lo) * px, ROW = 32;
    let y = 34; let section = null;
    const rows = [];
    for (const t of tasks) {
      if (t.section && t.section !== section) { section = t.section; rows.push({ section, y }); y += 26; }
      rows.push({ t, y }); y += ROW;
    }
    const step = span <= 21 ? 1 : span <= 120 ? 7 : 30;
    for (let d = lo; d <= hi; d += step) {
      HD.svg('line', { class: 'hd-grid', x1: X(d), y1: 22, x2: X(d), y2: y }, L.groups);
      HD.svg('text', { class: 'hd-tick', x: X(d), y: 14, 'text-anchor': 'middle', text: fmt(d) }, L.groups);
    }
    for (const r of rows) {
      if (r.section) { HD.svg('text', { class: 'hd-rowlabel group', x: 0, y: r.y + 16, text: r.section }, L.groups); continue; }
      const t = r.t;
      HD.svg('text', { class: 'hd-rowlabel', x: 12, y: r.y + 20, text: t.label || t.id }, L.groups);
      if (t._s == null || t._e == null) continue;
      const g = HD.nodeGroup(L.nodes, t, t.done ? 'solid' : '');
      if (t.milestone) {
        const cx = X(t._s), cy = r.y + 16;
        HD.svg('path', { class: 'hd-shape', d: `M${cx} ${cy - 9}L${cx + 9} ${cy}L${cx} ${cy + 9}L${cx - 9} ${cy}Z` }, g);
      } else {
        HD.svg('rect', { class: 'hd-shape', x: X(t._s) + 1, y: r.y + 6, width: Math.max(4, (t._e - t._s) * px - 2), height: 20, rx: 6 }, g);
      }
    }
    if (spec.today) {
      const d = day(spec.today, 'today');
      if (d !== null) {
        HD.svg('line', { class: 'hd-today', x1: X(d), y1: 22, x2: X(d), y2: y }, L.groups);
        HD.svg('text', { class: 'hd-tick', x: X(d) + 4, y: y + 12, text: '오늘', style: 'fill:var(--e-error)' }, L.groups);
      }
    }
  };

  HD.types.layers = async function (spec, L) {
    const layers = spec.layers || [];
    HD.checkIds(layers, 'layer');
    const items = layers.flatMap((l) => l.items || []);
    HD.checkIds(items, 'item');
    if (!layers.length) { HD.err('NO_NODES', 'spec.layers is empty'); return; }
    const titleW = Math.max(150, ...layers.map((l) => Math.max(HD.measure(l.label || l.id, 13, 700), l.sub ? HD.measure(l.sub, 10.5, 400, true) : 0))) + 36;
    for (const it of items) HD.sizeNode(it, it.shape || 'rect', { maxText: 160, minW: 128 });
    const rowW = (l) => (l.items || []).reduce((s, it, i) => s + it._w + (i ? 16 : 0), 0);
    const inner = Math.max(240, ...layers.map(rowW));
    const W = titleW + inner + 40;
    let y = 0;
    for (const l of layers) {
      const h = Math.max(56, ...(l.items || []).map((it) => it._h)) + 32;
      const g = HD.svg('g', { class: `hd-group k-${HD.kindOf(l.kind || 'neutral')}`, 'data-group': l.id }, L.groups);
      HD.svg('rect', { class: 'hd-frame', x: 0, y, width: W, height: h, rx: 12 }, g);
      HD.svg('text', { class: 'hd-band-t', x: 18, y: y + h / 2 + (l.sub ? -2 : 5), text: l.label || l.id }, g);
      if (l.sub) HD.svg('text', { class: 'hd-band-s', x: 18, y: y + h / 2 + 15, text: l.sub }, g);
      let x = titleW + 20 + (inner - rowW(l)) / 2;
      for (const it of l.items || []) {
        if (!it.kind) it.kind = l.kind;
        HD.drawNode(L.nodes, it, x, y + (h - it._h) / 2);
        x += it._w + 16;
      }
      y += h + 12;
    }
  };
})();
