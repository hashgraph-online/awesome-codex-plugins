/* hyper-diagram drawing primitives: text measurement, wrapping, icons, nodes,
   groups, edges, labels, and markers. Every diagram type draws through these
   so the checks in run.js see one vocabulary. */
(function () {
  'use strict';
  const HD = (window.HD = window.HD || {});
  const NS = 'http://www.w3.org/2000/svg';
  HD.types = HD.types || {};
  HD.errors = []; HD.warnings = [];
  HD.err = (code, message, extra) => HD.errors.push(Object.assign({ code, message }, extra || {}));
  HD.warn = (code, message, extra) => HD.warnings.push(Object.assign({ code, message }, extra || {}));

  HD.svg = function (tag, attrs, parent) {
    const el = document.createElementNS(NS, tag);
    for (const k in attrs || {}) {
      const v = attrs[k];
      if (v === undefined || v === null || v === false) continue;
      if (k === 'text') el.textContent = String(v);
      else el.setAttribute(k, String(v));
    }
    if (parent) parent.appendChild(el);
    return el;
  };
  HD.cssVar = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

  const ctx = document.createElement('canvas').getContext('2d');
  HD.measure = function (text, size, weight, mono) {
    ctx.font = (weight || 400) + ' ' + size + 'px ' + (mono ? HD.MONO : HD.SANS);
    return ctx.measureText(String(text)).width;
  };
  /* monospace only for Latin technical text; Hangul in a mono stack falls back with wide spacing */
  HD.isMono = (text) => !/[\u1100-\u11FF\u3130-\u318F\uAC00-\uD7A3]/.test(String(text || ''));
  function hardSplit(line, max, size, weight, mono) {
    if (HD.measure(line, size, weight, mono) <= max) return [line];
    const out = []; let cur = '';
    for (const ch of Array.from(line)) {
      if (cur && HD.measure(cur + ch, size, weight, mono) > max) { out.push(cur); cur = ch; } else cur += ch;
    }
    if (cur) out.push(cur);
    return out;
  }
  HD.wrap = function (text, max, size, weight, mono) {
    const out = [];
    for (const para of String(text == null ? '' : text).split('\n')) {
      const words = para.split(/\s+/).filter(Boolean);
      let line = '';
      for (const w of words) {
        const t = line ? line + ' ' + w : w;
        if (!line || HD.measure(t, size, weight, mono) <= max) line = t;
        else { out.push(line); line = w; }
      }
      if (line) out.push(line);
    }
    return out.flatMap((l) => hardSplit(l, max, size, weight, mono));
  };
  HD.textWidth = (lines, size, weight, mono) => Math.max(0, ...lines.map((l) => HD.measure(l, size, weight, mono)));

  HD.KINDS = {
    user: '사용자', client: '클라이언트', edge: '엣지·게이트웨이', service: '서비스', data: '데이터베이스',
    cache: '캐시', queue: '메시지 큐', storage: '스토리지', cloud: '클라우드', security: '보안·인증',
    external: '외부 시스템', ai: 'AI·모델', process: '처리 단계', decision: '분기', start: '시작',
    end: '끝', event: '이벤트', doc: '문서', team: '사람·팀', note: '메모', neutral: '기타'
  };
  HD.EDGE_KINDS = {
    default: '호출·연결', primary: '주 흐름', async: '비동기', auth: '인증·보안', data: '데이터 이동',
    deploy: '배포·개발 시점', error: '실패 경로', return: '응답'
  };
  HD.EDGE_DASH = { async: 'dash', auth: 'dash', return: 'dash', deploy: 'dot' };
  HD.kindOf = (k) => (HD.KINDS[k] ? k : 'neutral');
  HD.edgeKindOf = (k) => (HD.EDGE_KINDS[k] ? k : 'default');

  HD.ICONS = {
    user: 'M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8z M4 21a8 8 0 0 1 16 0',
    client: 'M3 4h18v12H3z M8 20h8 M12 16v4',
    edge: 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18z M3 12h18 M12 3c3 3.5 3 14.5 0 18 M12 3c-3 3.5-3 14.5 0 18',
    service: 'M8 7l-5 5 5 5 M16 7l5 5-5 5',
    data: 'M4 6c0-1.7 3.6-3 8-3s8 1.3 8 3-3.6 3-8 3-8-1.3-8-3z M4 6v12c0 1.7 3.6 3 8 3s8-1.3 8-3V6 M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3',
    cache: 'M13 2L4 14h7l-1 8 9-12h-7z',
    queue: 'M4 6h16 M4 12h16 M4 18h16',
    storage: 'M3 8h18v12H3z M3 8l2-4h14l2 4 M10 13h4',
    cloud: 'M7 18h10a4 4 0 0 0 .6-8A6 6 0 0 0 6.1 9 4.5 4.5 0 0 0 7 18z',
    security: 'M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z',
    external: 'M14 4h6v6 M20 4l-9 9 M18 14v6H4V6h6',
    ai: 'M12 3l2 6 6 2-6 2-2 6-2-6-6-2 6-2z',
    process: 'M4 6h16v12H4z M8 10h8 M8 14h5',
    decision: 'M12 3l9 9-9 9-9-9z',
    start: 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18z M10 8l6 4-6 4z',
    end: 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18z M9 9h6v6H9z',
    event: 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18z M12 7v5l3 3',
    doc: 'M6 3h9l4 4v14H6z M14 3v5h5 M9 13h7 M9 17h7',
    team: 'M9 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6z M3 20a6 6 0 0 1 12 0 M16 5.2a3 3 0 0 1 0 5.6 M21 20a6 6 0 0 0-3.5-5.4',
    note: 'M5 3h14v12l-6 6H5z M13 21v-6h6'
  };

  /* Size a box node: n.label, n.sub; shape rect | pill | diamond | cylinder | parallelogram | circle */
  HD.sizeNode = function (n, shape, opt) {
    opt = opt || {};
    const s = shape || 'rect';
    if (s === 'circle') { n._shape = s; n._w = n._h = opt.size || 22; n._lines = []; n._subLines = []; return n; }
    const maxText = opt.maxText || 196;
    const tsize = opt.root ? 15 : 13;
    n._lines = HD.wrap(n.label == null ? n.id : n.label, maxText, tsize, opt.root ? 700 : 600);
    n._subMono = HD.isMono(n.sub);
    n._subLines = n.sub ? HD.wrap(n.sub, maxText, 10.5, 400, n._subMono) : [];
    n._tsize = tsize;
    const tw = Math.max(HD.textWidth(n._lines, tsize, opt.root ? 700 : 600), HD.textWidth(n._subLines, 10.5, 400, n._subMono));
    const th = n._lines.length * (tsize + 4) + (n._subLines.length ? 5 + n._subLines.length * 14 : 0);
    let w = Math.max(opt.minW || 132, Math.ceil(tw) + 52);
    let h = Math.max(opt.minH || 54, Math.ceil(th) + 30);
    if (s === 'diamond') { w = Math.max(120, Math.ceil(tw / 0.58) + 12); h = Math.max(64, Math.ceil(th / 0.42) + 8); }
    if (s === 'cylinder') h += 14;
    if (s === 'parallelogram') w += 24;
    n._shape = s; n._w = w; n._h = h;
    return n;
  };

  function shapePath(s, x, y, w, h) {
    if (s === 'diamond') return { tag: 'path', d: `M${x + w / 2} ${y}L${x + w} ${y + h / 2}L${x + w / 2} ${y + h}L${x} ${y + h / 2}Z` };
    if (s === 'parallelogram') { const k = 14; return { tag: 'path', d: `M${x + k} ${y}H${x + w}L${x + w - k} ${y + h}H${x}Z` }; }
    if (s === 'cylinder') {
      const ry = 7, rx = w / 2;
      return { tag: 'path', d: `M${x} ${y + ry}a${rx} ${ry} 0 0 1 ${w} 0v${h - 2 * ry}a${rx} ${ry} 0 0 1 ${-w} 0Z M${x} ${y + ry}a${rx} ${ry} 0 0 0 ${w} 0` };
    }
    if (s === 'circle') return { tag: 'circle', cx: x + w / 2, cy: y + h / 2, r: w / 2 };
    const r = s === 'pill' ? h / 2 : s === 'soft' ? 14 : 9;
    return { tag: 'rect', x, y, width: w, height: h, rx: r };
  }

  HD.nodeGroup = function (layer, n, extraClass) {
    return HD.svg('g', { class: `hd-node k-${HD.kindOf(n.kind)}${extraClass ? ' ' + extraClass : ''}`, 'data-node': n.id }, layer);
  };

  /* Draw a sized box node at (x, y) */
  HD.drawNode = function (layer, n, x, y, opt) {
    opt = opt || {};
    const s = n._shape || 'rect', w = n._w, h = n._h;
    const g = HD.nodeGroup(layer, n, opt.cls || (s === 'circle' && n.kind === 'start' ? 'solid' : ''));
    const p = shapePath(s, x, y, w, h);
    const tag = p.tag; delete p.tag;
    HD.svg(tag, Object.assign({ class: 'hd-shape' }, p), g);
    if (s === 'circle') {
      if (n.kind === 'end') HD.svg('circle', { class: 'hd-shape', cx: x + w / 2, cy: y + h / 2, r: w / 2 - 5, style: 'fill:var(--c)' }, g);
      n._box = { x, y, w, h };
      return g;
    }
    const iconName = n.icon === false ? null : (n.icon || HD.kindOf(n.kind));
    if (iconName && HD.ICONS[iconName] && s !== 'diamond' && !opt.noIcon) {
      const ig = HD.svg('g', { class: 'hd-icon', transform: `translate(${x + 9} ${y + 8}) scale(0.5)` }, g);
      HD.svg('path', { d: HD.ICONS[iconName] }, ig);
    }
    const lh = n._tsize + 4;
    const total = n._lines.length * lh + (n._subLines.length ? 5 + n._subLines.length * 14 : 0);
    let ty = y + (h - total) / 2 + (s === 'cylinder' ? 7 : 0);
    const cx = x + w / 2;
    for (const l of n._lines) { HD.svg('text', { class: 'hd-t', x: cx, y: ty + n._tsize, 'text-anchor': 'middle', text: l }, g); ty += lh; }
    if (n._subLines.length) ty += 5;
    for (const l of n._subLines) { HD.svg('text', { class: n._subMono ? 'hd-s' : 'hd-s ko', x: cx, y: ty + 10.5, 'text-anchor': 'middle', text: l }, g); ty += 14; }
    n._box = { x, y, w, h };
    return g;
  };

  HD.drawGroup = function (layer, gspec, x, y, w, h) {
    const g = HD.svg('g', { class: `hd-group k-${HD.kindOf(gspec.kind || 'neutral')}${gspec.dashed ? ' dashed' : ''}`, 'data-group': gspec.id }, layer);
    HD.svg('rect', { class: 'hd-frame', x, y, width: w, height: h, rx: 12 }, g);
    if (gspec.label) {
      const mono = HD.isMono(gspec.label);
      const tw = HD.measure(gspec.label, 10.5, 500, mono);
      const gl = HD.svg('g', { class: 'hd-gl hd-group-label' }, g);
      HD.svg('rect', { x: x + 12, y: y + 10, width: tw + 16, height: 20, rx: 10 }, gl);
      HD.svg('text', { x: x + 20, y: y + 24, text: gspec.label, class: mono ? null : 'ko' }, gl);
    }
    return g;
  };

  /* markers: arrow | open | tri | dia | odia, colored by the edge kind */
  HD.marker = function (name, ekind) {
    const id = `hd-m-${name}-${ekind}`;
    if (document.getElementById(id)) return `url(#${id})`;
    const defs = HD.defs;
    const geo = {
      arrow: { vb: '0 0 10 10', ref: [9.5, 5], size: 7, d: 'M0 0L10 5L0 10z' },
      open: { vb: '0 0 10 10', ref: [9.5, 5], size: 8, d: 'M1 1L9.5 5L1 9', hollow: true, line: true },
      tri: { vb: '0 0 12 12', ref: [11.5, 6], size: 11, d: 'M0 0L12 6L0 12z', hollow: true },
      dia: { vb: '0 0 16 10', ref: [0.5, 5], size: 13, d: 'M0 5L8 0L16 5L8 10z' },
      odia: { vb: '0 0 16 10', ref: [0.5, 5], size: 13, d: 'M0 5L8 0L16 5L8 10z', hollow: true }
    }[name];
    const m = HD.svg('marker', { id, class: `e-${ekind}`, viewBox: geo.vb, refX: geo.ref[0], refY: geo.ref[1], markerWidth: geo.size, markerHeight: geo.size, orient: 'auto-start-reverse', markerUnits: 'userSpaceOnUse' }, defs);
    HD.svg('path', { d: geo.d, class: 'hd-marker' + (geo.hollow ? ' hollow' : ''), style: geo.line ? 'fill:none;stroke-width:1.6' : null }, m);
    return `url(#${id})`;
  };

  function roundedPath(pts, r) {
    if (pts.length < 2) return '';
    let d = `M${pts[0].x} ${pts[0].y}`;
    for (let i = 1; i < pts.length - 1; i++) {
      const p = pts[i], a = pts[i - 1], b = pts[i + 1];
      const la = Math.hypot(p.x - a.x, p.y - a.y), lb = Math.hypot(b.x - p.x, b.y - p.y);
      const rr = Math.min(r, la / 2, lb / 2);
      if (rr < 0.5) { d += `L${p.x} ${p.y}`; continue; }
      const p1 = { x: p.x + ((a.x - p.x) / la) * rr, y: p.y + ((a.y - p.y) / la) * rr };
      const p2 = { x: p.x + ((b.x - p.x) / lb) * rr, y: p.y + ((b.y - p.y) / lb) * rr };
      d += `L${p1.x} ${p1.y}Q${p.x} ${p.y} ${p2.x} ${p2.y}`;
    }
    const z = pts[pts.length - 1];
    return d + `L${z.x} ${z.y}`;
  }
  HD.roundedPath = roundedPath;

  /* Edge: e = {from, to, label, kind, dashed, dotted}; opt = {points | d, start, end, labelAt, free, plain} */
  HD.drawEdge = function (layer, e, opt) {
    const ek = HD.edgeKindOf(e.kind);
    const dash = e.dotted ? 'dot' : e.dashed ? 'dash' : (e.dashed === false ? '' : HD.EDGE_DASH[ek] || '');
    const g = HD.svg('g', { class: `hd-edge e-${ek}${dash ? ' ' + dash : ''}${opt.cls ? ' ' + opt.cls : ''}`, 'data-from': e.from, 'data-to': e.to, 'data-touch': `${e.from} ${e.to}`, 'data-free': opt.free ? '1' : null }, layer);
    const d = opt.d || roundedPath(opt.points, 8);
    const end = opt.end === undefined ? 'arrow' : opt.end;
    HD.svg('path', { class: 'hd-path', d, 'marker-end': end ? HD.marker(end, ek) : null, 'marker-start': opt.start ? HD.marker(opt.start, ek) : null }, g);
    if (e.label && opt.labelAt) HD.edgeLabel(opt.labelLayer || layer, e, ek, opt.labelAt.x, opt.labelAt.y, opt.plain, g);
    return g;
  };

  HD.labelSize = (text) => { const m = HD.isMono(text); return { w: Math.ceil(HD.measure(text, 10.5, m ? 500 : 600, m)) + 16, h: 20 }; };
  /* centered pill label at (cx, cy) */
  HD.edgeLabel = function (layer, e, ek, cx, cy, plain, edgeG) {
    const g = HD.svg('g', { class: `hd-elabel e-${ek}${plain ? ' plain' : ''}`, 'data-edge': `${e.from}->${e.to}` }, layer);
    if (plain) {
      HD.svg('text', { x: cx, y: cy + 4, 'text-anchor': 'middle', text: e.label }, g);
    } else {
      const s = HD.labelSize(e.label);
      HD.svg('rect', { x: cx - s.w / 2, y: cy - s.h / 2, width: s.w, height: s.h, rx: 10 }, g);
      HD.svg('text', { x: cx, y: cy + 3.8, 'text-anchor': 'middle', text: e.label, class: HD.isMono(e.label) ? null : 'ko' }, g);
    }
    if (edgeG) g.dataset.touch = edgeG.dataset.touch;
    return g;
  };

  /* longest segment midpoint, for labels the layout engine did not place */
  HD.midpoint = function (pts) {
    let best = null, bl = -1;
    for (let i = 0; i + 1 < pts.length; i++) {
      const l = Math.hypot(pts[i + 1].x - pts[i].x, pts[i + 1].y - pts[i].y);
      if (l > bl) { bl = l; best = { x: (pts[i].x + pts[i + 1].x) / 2, y: (pts[i].y + pts[i + 1].y) / 2 }; }
    }
    return best;
  };
})();
