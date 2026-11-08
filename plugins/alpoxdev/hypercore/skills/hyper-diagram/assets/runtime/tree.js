/* tree and mindmap: single-parent hierarchies.
   tree:    root: {id, label, sub, kind, children: [...]}, direction down | right
   mindmap: root: {id, label, children: [...]}; branches split left and right */
(function () {
  'use strict';
  const HD = window.HD;
  const PALETTE = ['service', 'data', 'queue', 'ai', 'security', 'client', 'team', 'cloud', 'cache', 'event'];

  function collect(node, depth, list, parent) {
    if (!node || typeof node !== 'object') return;
    node._depth = depth; node._parent = parent; list.push(node);
    for (const c of node.children || []) collect(c, depth + 1, list, node);
  }

  /* lay out a subtree along a cross axis; size(n) -> {main, cross} */
  function place(node, size, gapCross, start) {
    const kids = node.children || [];
    const s = size(node);
    if (!kids.length) { node._c = start + s.cross / 2; return s.cross; }
    let at = start, total = 0;
    kids.forEach((k, i) => { const w = place(k, size, gapCross, at); at += w + gapCross; total += w + (i ? gapCross : 0); });
    const span = Math.max(total, s.cross);
    if (s.cross > total) { const shift = (s.cross - total) / 2; kids.forEach((k) => shiftAll(k, shift)); }
    node._c = (kids[0]._c + kids[kids.length - 1]._c) / 2;
    return span;
  }
  function shiftAll(n, d) { n._c += d; for (const k of n.children || []) shiftAll(k, d); }

  function levels(list, mainOf, gapMain) {
    const depthMain = [];
    for (const n of list) depthMain[n._depth] = Math.max(depthMain[n._depth] || 0, mainOf(n));
    const at = [0];
    for (let d = 1; d < depthMain.length; d++) at[d] = at[d - 1] + depthMain[d - 1] + gapMain;
    return at;
  }

  HD.types.tree = async function (spec, L) {
    const list = [];
    collect(spec.root, 0, list, null);
    if (!list.length) { HD.err('NO_NODES', 'spec.root is missing'); return; }
    HD.checkIds(list, 'node');
    if (list.length > 60) HD.warn('DENSE_DIAGRAM', `${list.length} nodes; split the tree`);
    const right = spec.direction === 'right';
    for (const n of list) HD.sizeNode(n, n.shape || 'rect', { root: n._depth === 0, maxText: right ? 220 : 170 });
    const size = (n) => (right ? { main: n._w, cross: n._h } : { main: n._h, cross: n._w });
    place(list[0], size, right ? 14 : 22, 0);
    const at = levels(list, (n) => size(n).main, right ? 64 : 56);
    for (const n of list) {
      const m = at[n._depth];
      if (right) HD.drawNode(L.nodes, n, m, n._c - n._h / 2, { cls: n._depth === 0 ? 'root' : '' });
      else HD.drawNode(L.nodes, n, n._c - n._w / 2, m, { cls: n._depth === 0 ? 'root' : '' });
    }
    for (const n of list) {
      const p = n._parent; if (!p) continue;
      const pb = p._box, cb = n._box;
      let pts;
      if (right) {
        const mid = pb.x + pb.w + (cb.x - pb.x - pb.w) / 2;
        pts = [{ x: pb.x + pb.w, y: pb.y + pb.h / 2 }, { x: mid, y: pb.y + pb.h / 2 }, { x: mid, y: cb.y + cb.h / 2 }, { x: cb.x - 1, y: cb.y + cb.h / 2 }];
      } else {
        const mid = pb.y + pb.h + (cb.y - pb.y - pb.h) / 2;
        pts = [{ x: pb.x + pb.w / 2, y: pb.y + pb.h }, { x: pb.x + pb.w / 2, y: mid }, { x: cb.x + cb.w / 2, y: mid }, { x: cb.x + cb.w / 2, y: cb.y - 1 }];
      }
      const e = { from: p.id, to: n.id, label: n.edgeLabel, kind: n.edgeKind || 'default' };
      const g = HD.drawEdge(L.edges, e, { points: pts, end: spec.arrows ? 'arrow' : null, labelLayer: L.labels, labelAt: n.edgeLabel ? pts[2] : null });
      g.dataset.legend = 'no';
    }
  };

  HD.types.mindmap = async function (spec, L) {
    const list = [];
    collect(spec.root, 0, list, null);
    if (!list.length) { HD.err('NO_NODES', 'spec.root is missing'); return; }
    HD.checkIds(list, 'node');
    const root = list[0];
    (root.children || []).forEach((b, i) => {
      const kind = b.kind || PALETTE[i % PALETTE.length];
      (function paint(n) { if (!n.kind) n.kind = kind; for (const k of n.children || []) paint(k); })(b);
    });
    if (!root.kind) root.kind = 'neutral';
    for (const n of list) HD.sizeNode(n, n._depth === 0 ? 'pill' : n._depth === 1 ? 'pill' : 'soft', { root: n._depth === 0, maxText: n._depth > 1 ? 180 : 200, minW: n._depth > 1 ? 96 : 120, minH: n._depth > 1 ? 40 : 50 });
    const branches = root.children || [];
    const sides = [[], []];
    const weight = (n) => 1 + (n.children || []).reduce((s, k) => s + weight(k), 0);
    let wr = 0, wl = 0;
    for (const b of branches) { if (wr <= wl) { sides[0].push(b); wr += weight(b); } else { sides[1].push(b); wl += weight(b); } }
    const size = (n) => ({ main: n._w, cross: n._h });
    const at = levels(list, (n) => n._w, 60);
    sides.forEach((side, si) => {
      let start = 0; const spans = [];
      for (const b of side) { const s = place(b, size, 12, start); spans.push(s); start += s + 28; }
      const shift = -(start - 28) / 2;
      for (const b of side) shiftAll(b, shift);
      for (const b of side) {
        (function draw(n) {
          const m = at[n._depth] - at[1] + root._w / 2 + 60;
          const x = si === 0 ? m : -m - n._w;
          HD.drawNode(L.nodes, n, x, n._c - n._h / 2, { noIcon: n._depth > 1 });
          for (const k of n.children || []) draw(k);
        })(b);
      }
    });
    HD.drawNode(L.nodes, root, -root._w / 2, -root._h / 2, { cls: 'root solid' });
    for (const g of L.nodes.querySelectorAll('.hd-node')) g.dataset.legend = 'no';
    const css = HD.svg('style', { text: '.hd-node.root.solid .hd-t{fill:var(--card)} .hd-node.root.solid .hd-icon{stroke:var(--card)}' }, L.nodes);
    css.setAttribute('data-hd-inline', '1');
    for (const n of list) {
      const p = n._parent; if (!p) continue;
      const pb = p._box, cb = n._box;
      const left = cb.x < pb.x;
      const a = { x: left ? pb.x : pb.x + pb.w, y: pb.y + pb.h / 2 };
      const b = { x: left ? cb.x + cb.w : cb.x, y: cb.y + cb.h / 2 };
      const mx = (a.x + b.x) / 2;
      const g = HD.drawEdge(L.edges, { from: p.id, to: n.id, kind: 'default' }, { d: `M${a.x} ${a.y}C${mx} ${a.y} ${mx} ${b.y} ${b.x} ${b.y}`, end: null, cls: `k-${n.kind}` });
      g.querySelector('.hd-path').setAttribute('style', `stroke:var(--k-${HD.kindOf(n.kind)});stroke-width:${n._depth === 1 ? 2.4 : 1.6}`);
      g.dataset.legend = 'no';
    }
  };
})();
