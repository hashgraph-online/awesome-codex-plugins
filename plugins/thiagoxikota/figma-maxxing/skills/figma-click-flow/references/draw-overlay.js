// figma-click-flow: full hardened overlay snippet.
// Run inside `figma_execute` (figma-console MCP) or `use_figma` (official Figma MCP server).
// The use_figma path is not validated by this repo; the guards below follow Figma's figma-use
// skill (https://github.com/figma/mcp-server-guide), which documents that runtime.
// Replace the four CONFIG lines below.
// Verified API behavior (field note, 2026-05): SECTION children use local coords; createNodeFromSvg
// returns a FRAME of vectors; figma.createConnector is not a function in design files.
//
// To run: substitute the CONFIG block, then paste the rest into figma_execute.
// This file is a figma_execute body (top-level await and return), not a standalone Node script.

// ============== CONFIG (replace before running) ==============
const SECTION_ID    = "REPLACE_WITH_SECTION_ID";   // e.g. "123:456"
const MODE          = "from-prototype";            // "from-prototype" | "explicit" | "auto-layout"
const EXPLICIT_PAIRS = [];                          // [{ from, to }, ...] when MODE === "explicit"
// auto-layout mode: groups top-level FRAMEs in the section into rows by Y, sorts each row by X,
//   builds intra-row left-to-right pairs. Skips children that aren't taller-than-wide (filters out
//   labels/dividers). Use when prototype isn't wired and screens are sequentially laid out.
const AUTO_LAYOUT_MIN_AR = 1.3;     // min height/width ratio to count as a screen
const AUTO_LAYOUT_ROW_GAP = 100;    // Y delta < this = same row
const TRIGGER_FILTER = ["ON_CLICK", "ON_PRESS", "ON_TAP"];
const INCLUDE_OVERLAY_ACTIONS = true;
// Accent color: neutral red by default. Configurable: set it to the file's own accent color.
const STROKE_COLOR  = "#E5484D";
const STROKE_WEIGHT = 4;
const CORNER_RADIUS = 12;
const DOT_RADIUS    = 5;
const ARROW_LEN     = 12;
const OVERLAY_NAME  = "flow-overlay · click-connectors";
// originAnchor controls where the dot lands on the source node:
//   "auto"            : center for small nodes (<200×200), edge-toward-dest for larger (default)
//   "center"          : always bbox center (correct for prototype-driven mode on buttons)
//   "edge-toward-dest": right/left/top/bottom midpoint nearest dest (correct for screen-level pairs)
const ORIGIN_ANCHOR = "auto";
// ==============================================================

// figma.loadAllPagesAsync() exists in the Desktop Bridge plugin (figma_execute). Figma's own
// figma-use skill lists it as "Not implemented" in use_figma (official Figma MCP server), and a
// missing member can throw there on access. So try it and go on without it: getNodeByIdAsync
// resolves across pages, and setCurrentPageAsync below loads the page the section lives on.
try { await figma.loadAllPagesAsync(); } catch (e) { /* use_figma: not implemented */ }

const section = await figma.getNodeByIdAsync(SECTION_ID);
if (!section) throw new Error(`Section ${SECTION_ID} not found`);

// Walk to PAGE ancestor: section may be nested
let pageNode = section;
while (pageNode && pageNode.type !== "PAGE") pageNode = pageNode.parent;
if (!pageNode) throw new Error("No PAGE ancestor for section");
await figma.setCurrentPageAsync(pageNode);

const sb = section.absoluteBoundingBox;
if (!sb) throw new Error("Section has no bounding box");

// Phase 1: collect pairs
const pairs = [];
if (MODE === "explicit") {
  for (const p of EXPLICIT_PAIRS) pairs.push({ from: p.from, to: p.to });
} else if (MODE === "auto-layout") {
  // Group section's top-level screen FRAMEs by row, then build intra-row L-to-R pairs.
  const screens = [];
  for (const c of section.children) {
    if (c.type !== "FRAME" && c.type !== "COMPONENT" && c.type !== "INSTANCE") continue;
    const ab = c.absoluteBoundingBox;
    if (!ab || ab.height / ab.width < AUTO_LAYOUT_MIN_AR) continue;
    screens.push({ id: c.id, x: ab.x, y: ab.y });
  }
  screens.sort((a, b) => (a.y - b.y) || (a.x - b.x));
  const rows = [];
  let row = [], lastY = -Infinity;
  for (const s of screens) {
    if (s.y - lastY > AUTO_LAYOUT_ROW_GAP || row.length === 0) {
      if (row.length) rows.push(row);
      row = [s];
    } else row.push(s);
    lastY = s.y;
  }
  if (row.length) rows.push(row);
  for (const r of rows) {
    r.sort((a, b) => a.x - b.x);
    for (let i = 0; i < r.length - 1; i++) pairs.push({ from: r[i].id, to: r[i + 1].id });
  }
} else {
  // from-prototype: walk descendants for reactions
  section.findAll((n) => {
    // SECTION, SLICE and COMPONENT_SET nodes declare no `reactions` (@figma/plugin-typings 1.140.0).
    // use_figma throws on a read of a member the node type lacks, and `?.` does not prevent it,
    // so test with `in` first. In figma_execute the same read returns undefined.
    if (!("reactions" in n)) return false;
    const reactions = n.reactions;
    if (!reactions || !Array.isArray(reactions) || reactions.length === 0) return false;
    for (const r of reactions) {
      const triggerType = r.trigger ? r.trigger.type : null;
      if (triggerType && !TRIGGER_FILTER.includes(triggerType)) continue;
      const actions = r.actions || (r.action ? [r.action] : []);
      for (const a of actions) {
        if (!a || !a.destinationId) continue;
        if (a.type === "NODE" || (INCLUDE_OVERLAY_ACTIONS && a.type === "OVERLAY")) {
          pairs.push({ from: n.id, to: a.destinationId, trigger: triggerType });
        }
      }
    }
    return false;
  });
}

if (pairs.length === 0) {
  return {
    drawn: 0,
    warning: "No pairs found. Try MODE='auto-layout' (infer from layout), MODE='explicit' with EXPLICIT_PAIRS, or wire the prototype first.",
  };
}

// Filter pairs whose endpoints fall outside the section's absolute bounds
const inSection = (n) => {
  if (!("absoluteBoundingBox" in n)) return false; // a PAGE id passed by hand has no box
  const ab = n.absoluteBoundingBox;
  if (!ab) return false;
  const cx = ab.x + ab.width / 2;
  const cy = ab.y + ab.height / 2;
  return cx >= sb.x && cx <= sb.x + sb.width && cy >= sb.y && cy <= sb.y + sb.height;
};

const resolved = [];
const dropped = [];
for (const p of pairs) {
  const a = await figma.getNodeByIdAsync(p.from);
  const b = await figma.getNodeByIdAsync(p.to);
  if (!a || !b) { dropped.push({ ...p, reason: "node not found" }); continue; }
  if (!inSection(a) || !inSection(b)) { dropped.push({ ...p, reason: "outside section" }); continue; }
  resolved.push({ from: a, to: b, trigger: p.trigger });
}

if (resolved.length === 0) {
  return { drawn: 0, dropped, warning: "All pairs outside section bounds or unresolved." };
}

// Phase 3 prep: idempotent overlay (also set hex → rgb here)
const hex = STROKE_COLOR.replace("#", "");
const RGB = {
  r: parseInt(hex.slice(0, 2), 16) / 255,
  g: parseInt(hex.slice(2, 4), 16) / 255,
  b: parseInt(hex.slice(4, 6), 16) / 255,
};

const prior = section.findOne((n) => n.name === OVERLAY_NAME);
if (prior) prior.remove();

const overlay = figma.createFrame();
overlay.name = OVERLAY_NAME;
overlay.fills = [];
overlay.strokes = [];
overlay.clipsContent = false;
overlay.resize(sb.width, sb.height);
section.appendChild(overlay);
// SECTION children use LOCAL coords: align overlay to section's top-left.
overlay.x = 0;
overlay.y = 0;

const createdNodeIds = [overlay.id];

// Per-pair geometry + SVG
for (const r of resolved) {
  const fb = r.from.absoluteBoundingBox;
  const tb = r.to.absoluteBoundingBox;
  if (!fb || !tb) continue;

  // Origin anchor: center vs edge-toward-dest
  const cx = fb.x + fb.width / 2;
  const cy = fb.y + fb.height / 2;
  const tcx = tb.x + tb.width / 2;
  const tcy = tb.y + tb.height / 2;
  const useEdge =
    ORIGIN_ANCHOR === "edge-toward-dest" ||
    (ORIGIN_ANCHOR === "auto" && fb.width >= 200 && fb.height >= 200);

  let ox, oy;
  if (useEdge) {
    const fromCandidates = [
      { x: fb.x,            y: fb.y + fb.height / 2 },
      { x: fb.x + fb.width, y: fb.y + fb.height / 2 },
      { x: fb.x + fb.width / 2, y: fb.y },
      { x: fb.x + fb.width / 2, y: fb.y + fb.height },
    ];
    let best = fromCandidates[0], bestD = Infinity;
    for (const c of fromCandidates) {
      const d = Math.hypot(c.x - tcx, c.y - tcy);
      if (d < bestD) { bestD = d; best = c; }
    }
    ox = best.x; oy = best.y;
  } else {
    ox = cx; oy = cy;
  }

  // Pick nearest edge midpoint of destination frame
  const candidates = [
    { x: tb.x,             y: tb.y + tb.height / 2 },
    { x: tb.x + tb.width,  y: tb.y + tb.height / 2 },
    { x: tb.x + tb.width / 2, y: tb.y },
    { x: tb.x + tb.width / 2, y: tb.y + tb.height },
  ];
  let dest = candidates[0], bestD = Infinity;
  for (const c of candidates) {
    const d = Math.hypot(c.x - ox, c.y - oy);
    if (d < bestD) { bestD = d; dest = c; }
  }

  // SVG-local coords (will offset frame after import)
  const PAD = ARROW_LEN + Math.max(DOT_RADIUS, CORNER_RADIUS) + 4;
  const midX = (ox + dest.x) / 2;
  const minX = Math.min(ox, dest.x, midX) - PAD;
  const minY = Math.min(oy, dest.y) - PAD;
  const maxX = Math.max(ox, dest.x, midX) + PAD;
  const maxY = Math.max(oy, dest.y) + PAD;
  const W = maxX - minX, H = maxY - minY;

  const lox = ox - minX, loy = oy - minY;
  const ldx = dest.x - minX, ldy = dest.y - minY;
  const lmx = midX - minX;

  // Trunk path: straight if elbow would degenerate
  let trunk;
  if (Math.abs(ldy - loy) < 2 * CORNER_RADIUS) {
    trunk = `M ${lox} ${loy} L ${ldx} ${ldy}`;
  } else {
    const sy = Math.sign(ldy - loy) || 1;
    const sx = Math.sign(ldx - lmx) || 1;
    trunk =
      `M ${lox} ${loy}` +
      ` L ${lmx - CORNER_RADIUS * sx} ${loy}` +
      ` Q ${lmx} ${loy} ${lmx} ${loy + CORNER_RADIUS * sy}` +
      ` L ${lmx} ${ldy - CORNER_RADIUS * sy}` +
      ` Q ${lmx} ${ldy} ${lmx + CORNER_RADIUS * sx} ${ldy}` +
      ` L ${ldx} ${ldy}`;
  }

  // Arrowhead pointing at dest (open ARROW_LINES style)
  // Direction: from (lmx,ldy) → (ldx,ldy) for elbow case (horizontal),
  // or from (lox,loy) → (ldx,ldy) for straight case.
  const incomingFromX = (Math.abs(ldy - loy) < 2 * CORNER_RADIUS) ? lox : lmx;
  const incomingFromY = (Math.abs(ldy - loy) < 2 * CORNER_RADIUS) ? loy : ldy;
  const dxn = ldx - incomingFromX, dyn = ldy - incomingFromY;
  const len = Math.hypot(dxn, dyn) || 1;
  const ux = dxn / len, uy = dyn / len;          // unit vector along incoming
  const px = -uy, py = ux;                        // perpendicular
  const headTipX = ldx, headTipY = ldy;
  const headBaseX = headTipX - ux * ARROW_LEN;
  const headBaseY = headTipY - uy * ARROW_LEN;
  const wing = ARROW_LEN * 0.55;
  const ax1 = headBaseX + px * wing, ay1 = headBaseY + py * wing;
  const ax2 = headBaseX - px * wing, ay2 = headBaseY - py * wing;

  const svg =
    `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}">` +
    `<circle cx="${lox}" cy="${loy}" r="${DOT_RADIUS}" fill="${STROKE_COLOR}"/>` +
    `<path d="${trunk}" stroke="${STROKE_COLOR}" stroke-width="${STROKE_WEIGHT}" fill="none" stroke-linecap="round"/>` +
    `<polyline points="${ax1},${ay1} ${headTipX},${headTipY} ${ax2},${ay2}" stroke="${STROKE_COLOR}" stroke-width="${STROKE_WEIGHT}" fill="none" stroke-linecap="round" stroke-linejoin="round"/>` +
    `</svg>`;

  const conn = figma.createNodeFromSvg(svg);
  conn.name = `flow · ${r.from.name} → ${r.to.name}`;
  overlay.appendChild(conn);
  // Position relative to overlay (overlay is at section.absoluteOrigin in local-0 space)
  conn.x = minX - sb.x;
  conn.y = minY - sb.y;
  createdNodeIds.push(conn.id);
}

return {
  createdNodeIds,
  overlayId: overlay.id,
  drawn: resolved.length,
  dropped,
  pageId: pageNode.id,
};
