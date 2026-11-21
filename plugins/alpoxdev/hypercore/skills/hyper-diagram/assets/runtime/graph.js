/* ELK-laid graph types: architecture, dataflow, flowchart, state, class, erd.
   Nodes and groups become an ELK compound graph; ELK returns orthogonal routes
   and label positions, which the drawing primitives render. */
(function () {
  'use strict';
  const HD = window.HD;
  const DIR = { architecture: 'RIGHT', dataflow: 'RIGHT', flowchart: 'DOWN', state: 'RIGHT', class: 'DOWN', erd: 'RIGHT' };
  const DIRS = { right: 'RIGHT', down: 'DOWN', left: 'LEFT', up: 'UP', RIGHT: 'RIGHT', DOWN: 'DOWN', LEFT: 'LEFT', UP: 'UP' };

  function flowShape(n) {
    if (n.shape) return n.shape;
    if (n.kind === 'start' || n.kind === 'end') return 'pill';
    if (n.kind === 'decision') return 'diamond';
    if (n.kind === 'data') return 'cylinder';
    if (n.kind === 'doc' || n.io) return 'parallelogram';
    return 'rect';
  }

  /* ERD table: n.columns = [{name, type, key: PK|FK|UK|PK,FK}] */
  function sizeTable(n) {
    const cols = n.columns || [];
    const nameW = HD.measure(n.label || n.id, 13, 700);
    let rowW = 0;
    for (const c of cols) {
      const kw = c.key ? HD.measure(c.key, 9.5, 600, true) + 10 : 0;
      rowW = Math.max(rowW, kw + HD.measure(c.name, 11, 400, true) + 18 + HD.measure(c.type || '', 10.5, 400, true));
    }
    n._w = Math.ceil(Math.max(168, nameW + 40, rowW + 28));
    n._h = 34 + Math.max(1, cols.length) * 21 + 6;
  }
  function drawTable(layer, n, x, y) {
    const g = HD.nodeGroup(layer, n, 'plain');
    const w = n._w, h = n._h;
    HD.svg('rect', { class: 'hd-shape', x, y, width: w, height: h, rx: 9 }, g);
    HD.svg('path', { class: 'hd-head-fill', d: `M${x + 0.8} ${y + 34}V${y + 9}a8.2 8.2 0 0 1 8.2-8.2H${x + w - 9}a8.2 8.2 0 0 1 8.2 8.2V${y + 34}Z` }, g);
    HD.svg('line', { class: 'hd-rule', x1: x, y1: y + 34, x2: x + w, y2: y + 34 }, g);
    HD.svg('text', { class: 'hd-t', x: x + w / 2, y: y + 22, 'text-anchor': 'middle', text: n.label || n.id }, g);
    let ry = y + 34;
    for (const c of n.columns || []) {
      let tx = x + 12;
      if (c.key) { HD.svg('text', { class: 'hd-key', x: tx, y: ry + 15, text: c.key }, g); tx += HD.measure(c.key, 9.5, 600, true) + 8; }
      HD.svg('text', { class: 'hd-m', x: tx, y: ry + 15, text: c.name }, g);
      if (c.type) HD.svg('text', { class: 'hd-s', x: x + w - 12, y: ry + 15, 'text-anchor': 'end', text: c.type }, g);
      ry += 21;
    }
    n._box = { x, y, w, h };
  }

  /* class box: n.stereotype, n.attributes[], n.methods[] */
  function sizeClass(n) {
    const lines = [...(n.attributes || []), ...(n.methods || [])];
    const w = Math.max(HD.measure(n.label || n.id, 13, 700), n.stereotype ? HD.measure(`«${n.stereotype}»`, 10, 400, true) : 0, HD.textWidth(lines, 11, 400, true));
    n._w = Math.ceil(Math.max(160, w + 32));
    n._headH = n.stereotype ? 44 : 32;
    n._h = n._headH + Math.max(1, (n.attributes || []).length) * 18 + 10 + Math.max(1, (n.methods || []).length) * 18 + 10;
  }
  function drawClass(layer, n, x, y) {
    const g = HD.nodeGroup(layer, n, 'plain');
    const w = n._w, hh = n._headH;
    HD.svg('rect', { class: 'hd-shape', x, y, width: w, height: n._h, rx: 9 }, g);
    HD.svg('path', { class: 'hd-head-fill', d: `M${x + 0.8} ${y + hh}V${y + 9}a8.2 8.2 0 0 1 8.2-8.2H${x + w - 9}a8.2 8.2 0 0 1 8.2 8.2V${y + hh}Z` }, g);
    if (n.stereotype) HD.svg('text', { class: 'hd-stereo', x: x + w / 2, y: y + 16, 'text-anchor': 'middle', text: `«${n.stereotype}»` }, g);
    HD.svg('text', { class: 'hd-t', x: x + w / 2, y: y + hh - 11, 'text-anchor': 'middle', text: n.label || n.id, style: n.abstract ? 'font-style:italic' : null }, g);
    let ry = y + hh;
    for (const part of [n.attributes || [], n.methods || []]) {
      HD.svg('line', { class: 'hd-rule', x1: x, y1: ry, x2: x + w, y2: ry }, g);
      ry += 5;
      if (!part.length) ry += 18;
      for (const l of part) { HD.svg('text', { class: 'hd-m', x: x + 12, y: ry + 13, text: l }, g); ry += 18; }
      ry += 5;
    }
    n._box = { x, y, w, h: n._h };
  }

  const CLASS_REL = {
    inherit: { end: 'tri', name: '상속' }, implement: { end: 'tri', dashed: true, name: '구현' },
    compose: { start: 'dia', end: null, name: '합성(소유)' }, aggregate: { start: 'odia', end: null, name: '집합(참조)' },
    depend: { end: 'open', dashed: true, name: '의존' }, assoc: { end: 'open', name: '연관' }, link: { end: null, name: '연결' }
  };

  /* move an orthogonal endpoint from the bounding box to a diamond outline */
  function snapDiamond(p, prev, b) {
    const cx = b.x + b.w / 2, cy = b.y + b.h / 2, hw = b.w / 2, hh = b.h / 2;
    if (Math.abs(prev.y - p.y) < 0.5) { const k = 1 - Math.min(1, Math.abs(p.y - cy) / hh); return { x: p.x < cx ? cx - hw * k : cx + hw * k, y: p.y }; }
    if (Math.abs(prev.x - p.x) < 0.5) { const k = 1 - Math.min(1, Math.abs(p.x - cx) / hw); return { x: p.x, y: p.y < cy ? cy - hh * k : cy + hh * k }; }
    return p;
  }

  async function graph(spec, L) {
    if (typeof window.ELK !== 'function') { HD.err('ELK_MISSING', 'the ELK layout engine did not load'); return; }
    const type = spec.type;
    const nodes = spec.nodes || [], groups = spec.groups || [], edges = spec.edges || [];
    HD.checkIds(groups, 'group'); HD.checkIds(nodes, 'node');
    const known = new Set([...nodes.map((n) => n.id), ...groups.map((g) => g.id)]);
    HD.checkRefs(edges, known, 'edges');
    if (!nodes.length) { HD.err('NO_NODES', 'spec.nodes is empty'); return; }
    if (nodes.length > 40) HD.warn('DENSE_DIAGRAM', `${nodes.length} nodes; split into an overview and detail diagrams`);
    const byId = new Map(nodes.map((n) => [n.id, n]));
    for (const n of nodes) {
      if (type === 'erd') sizeTable(n);
      else if (type === 'class') sizeClass(n);
      else if (type === 'state' && (n.kind === 'start' || n.kind === 'end') && !n.label) HD.sizeNode(n, 'circle', { size: n.kind === 'end' ? 24 : 20 });
      else if (type === 'state') HD.sizeNode(n, n.shape || 'soft');
      else if (type === 'flowchart') HD.sizeNode(n, flowShape(n));
      else HD.sizeNode(n, n.shape || 'rect');
    }
    const dir = DIRS[spec.direction] || DIR[type];
    const elkGroups = new Map();
    const root = {
      id: '__root',
      layoutOptions: {
        'elk.algorithm': 'layered', 'elk.direction': dir, 'elk.hierarchyHandling': 'INCLUDE_CHILDREN',
        'elk.edgeRouting': 'ORTHOGONAL', 'elk.json.edgeCoords': 'ROOT', 'elk.json.shapeCoords': 'ROOT',
        'elk.spacing.nodeNode': String(spec.spacing || 36), 'elk.layered.spacing.nodeNodeBetweenLayers': String((spec.spacing || 36) * 1.6),
        'elk.layered.spacing.edgeNodeBetweenLayers': '26', 'elk.spacing.edgeNode': '24', 'elk.spacing.edgeEdge': '16',
        'elk.layered.spacing.edgeEdgeBetweenLayers': '16', 'elk.spacing.edgeLabel': '6', 'elk.spacing.labelNode': '8',
        'elk.layered.nodePlacement.strategy': 'NETWORK_SIMPLEX', 'elk.layered.considerModelOrder.strategy': 'NODES_AND_EDGES',
        'elk.layered.edgeLabels.sideSelection': 'SMART_DOWN', 'elk.padding': '[top=8,left=8,bottom=8,right=8]'
      },
      children: [], edges: []
    };
    const pending = groups.slice(); let guard = 0;
    while (pending.length && guard++ < 500) {
      const g = pending.shift();
      if (g.parent && !elkGroups.has(g.parent)) { if (known.has(g.parent)) pending.push(g); else HD.err('UNKNOWN_PARENT', `group ${g.id} names an unknown parent ${g.parent}`); continue; }
      const eg = { id: g.id, children: [], layoutOptions: { 'elk.padding': '[top=44,left=20,bottom=20,right=20]' } };
      (g.parent ? elkGroups.get(g.parent).children : root.children).push(eg);
      elkGroups.set(g.id, eg);
    }
    for (const n of nodes) {
      const container = n.group ? elkGroups.get(n.group) : root;
      if (n.group && !container) HD.err('UNKNOWN_GROUP', `node ${n.id} names an unknown group ${n.group}`);
      (container || root).children.push({ id: n.id, width: n._w, height: n._h });
    }
    edges.forEach((e, i) => {
      if (!known.has(e.from) || !known.has(e.to)) return;
      const labels = e.label ? [{ id: `l${i}`, text: e.label, width: HD.labelSize(e.label).w, height: 20 }] : [];
      root.edges.push({ id: `e${i}`, sources: [e.from], targets: [e.to], labels });
    });
    const res = await new window.ELK().layout(root);
    const pos = new Map();
    (function walk(list, depth) {
      for (const c of list || []) { pos.set(c.id, { x: c.x, y: c.y, w: c.width, h: c.height, depth }); walk(c.children, depth + 1); }
    })(res.children, 0);
    const gs = groups.filter((g) => pos.has(g.id)).sort((a, b) => pos.get(a.id).depth - pos.get(b.id).depth);
    for (const g of gs) { const p = pos.get(g.id); HD.drawGroup(L.groups, g, p.x, p.y, p.w, p.h); }
    for (const n of nodes) {
      const p = pos.get(n.id); if (!p) continue;
      if (type === 'erd') drawTable(L.nodes, n, p.x, p.y);
      else if (type === 'class') drawClass(L.nodes, n, p.x, p.y);
      else HD.drawNode(L.nodes, n, p.x, p.y);
    }
    for (const re of res.edges || []) {
      let e = edges[Number(re.id.slice(1))];
      const pts = [];
      for (const s of re.sections || []) { if (!pts.length) pts.push(s.startPoint); pts.push(...(s.bendPoints || []), s.endPoint); }
      if (pts.length < 2) continue;
      const fromN = byId.get(e.from), toN = byId.get(e.to);
      if (fromN && fromN._shape === 'diamond') pts[0] = snapDiamond(pts[0], pts[1], fromN._box);
      if (toN && toN._shape === 'diamond') pts[pts.length - 1] = snapDiamond(pts[pts.length - 1], pts[pts.length - 2], toN._box);
      const opt = { points: pts, labelLayer: L.labels };
      let legendLabel = null;
      if (type === 'class') {
        const rel = CLASS_REL[e.kind] || CLASS_REL.assoc;
        Object.assign(opt, { end: rel.end, start: rel.start });
        legendLabel = rel.name;
        e = Object.assign({}, e, { dashed: rel.dashed || false, kind: 'default' });
      }
      const lab = re.labels && re.labels[0];
      if (lab) opt.labelAt = { x: lab.x + lab.width / 2, y: lab.y + lab.height / 2 };
      else if (e.label) opt.labelAt = HD.midpoint(pts);
      const eg = HD.drawEdge(L.edges, e, opt);
      if (legendLabel) eg.dataset.legendLabel = legendLabel;
      if (type === 'erd' && e.card) cardinality(eg, e.card, pts);
    }
  }

  /* ERD cardinality: "1:N" puts 1 at the source end and N at the target end */
  function cardinality(g, card, pts) {
    const [a, b] = String(card).split(':');
    const put = (p, q, text) => {
      if (!text) return;
      const len = Math.hypot(q.x - p.x, q.y - p.y) || 1;
      const dx = (q.x - p.x) / len, dy = (q.y - p.y) / len;
      const tw = HD.measure(text, 10.5, 600, true);
      const along = 8 + (Math.abs(dx) > 0.5 ? tw / 2 : 6);
      HD.svg('text', { class: 'hd-card', x: p.x + dx * along - dy * 10, y: p.y + dy * along + dx * 10 + 4, 'text-anchor': 'middle', text }, g);
    };
    put(pts[0], pts[1], a); put(pts[pts.length - 1], pts[pts.length - 2], b);
  }

  for (const t of Object.keys(DIR)) HD.types[t] = graph;
})();
