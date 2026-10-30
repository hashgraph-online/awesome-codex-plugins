// Turns a labelled state graph into a chart model: chart states (flat,
// nested, or parallel regions), arrows with conditions, marks, and notes.

import { show } from './values.mjs';
import { ViewError } from './view.mjs';
import { bfs } from './graph.mjs';

export class ChartError extends Error {}

const PATH_SEP = ' / ';
const cmp = (a, b) => (a < b ? -1 : a > b ? 1 : 0);

function edgeKey(from, to, action) {
  return [from, to, action].map(String).join('>');
}

// ---- trees of chart states ----

function newTree(region) {
  return { region, nodes: new Map(), roots: [] };
}

function nodeFor(tree, pathArr, nextId) {
  let parentKey = null;
  let node = null;
  for (let d = 0; d < pathArr.length; d++) {
    const key = JSON.stringify([tree.region, ...pathArr.slice(0, d + 1)]);
    node = tree.nodes.get(key);
    if (!node) {
      node = { key, id: nextId(), name: pathArr[d], path: pathArr.slice(0, d + 1), depth: d, parent: parentKey, children: [], members: [], region: tree.region, leaf: false };
      tree.nodes.set(key, node);
      if (parentKey) tree.nodes.get(parentKey).children.push(key);
      else tree.roots.push(key);
    }
    parentKey = key;
  }
  return node;
}

// `order` lists state indices in a canonical order (BFS from the sorted
// initial states, then any unreached states by default label), so chart ids
// do not depend on the order TLC printed its graph.
function buildTrees(regionNames, labels, nextId, order) {
  const trees = new Map(regionNames.map((r) => [r, newTree(r)]));
  const leafOf = new Map(regionNames.map((r) => [r, []]));
  for (const i of order) {
    const paths = labels[i];
    for (const r of regionNames) {
      const node = nodeFor(trees.get(r), paths.get(r), nextId);
      node.leaf = true;
      node.members.push(i);
      leafOf.get(r)[i] = node.key;
    }
  }
  for (const t of trees.values()) {
    for (const n of t.nodes.values()) {
      if (n.leaf && n.children.length) {
        throw new ViewError(`The view's state label ${JSON.stringify(n.path.join(PATH_SEP))} is used both as a state and as the parent of other states. Give the leaf its own child name, for example [...parent, "${n.name}"] becomes [...parent, "${n.name}", "idle"].`);
      }
    }
  }
  return { trees, leafOf };
}

function isUnder(tree, key, ancestor) {
  let k = key;
  while (k) {
    if (k === ancestor) return true;
    k = tree.nodes.get(k).parent;
  }
  return false;
}

function leavesUnder(tree, key) {
  const n = tree.nodes.get(key);
  if (n.leaf) return [key];
  return n.children.flatMap((c) => leavesUnder(tree, c));
}

// ---- lifting and merging ----

function liftArrows(tree, triples) {
  const parents = [...tree.nodes.values()].filter((n) => !n.leaf).sort((a, b) => a.depth - b.depth || cmp(a.key, b.key));
  let arrows = triples;
  for (const p of parents) {
    const leaves = leavesUnder(tree, p.key);
    if (leaves.length < 2) continue;
    const leafSet = new Set(leaves);
    const counts = new Map();
    for (const a of arrows) {
      if (!leafSet.has(a.from) || isUnder(tree, a.to, p.key)) continue;
      const k = JSON.stringify([a.to, a.label, a.cond ?? '']);
      if (!counts.has(k)) counts.set(k, new Set());
      counts.get(k).add(a.from);
    }
    const lift = new Set([...counts].filter(([, s]) => s.size === leaves.length).map(([k]) => k));
    if (!lift.size) continue;
    const kept = [];
    const added = new Set();
    for (const a of arrows) {
      const k = JSON.stringify([a.to, a.label, a.cond ?? '']);
      if (leafSet.has(a.from) && lift.has(k)) {
        if (!added.has(k)) { added.add(k); kept.push({ ...a, from: p.key, lifted: true, sources: [...counts.get(k)] }); }
        continue;
      }
      kept.push(a);
    }
    arrows = kept;
  }
  return arrows;
}

function mergeArrows(arrows) {
  const byPair = new Map();
  for (const a of arrows) {
    const k = JSON.stringify([a.from, a.to, a.cond ?? '']);
    if (!byPair.has(k)) byPair.set(k, { from: a.from, to: a.to, cond: a.cond ?? null, labels: [], parts: [] });
    const m = byPair.get(k);
    if (!m.labels.includes(a.label)) m.labels.push(a.label);
    m.parts.push(a);
  }
  const out = [...byPair.values()];
  for (const m of out) {
    m.labels.sort(cmp);
    let text = m.labels.join(' or ');
    if (m.cond && !text.endsWith(']')) text += ` [${m.cond}]`;
    m.text = text;
  }
  return out.sort((a, b) => cmp(a.from, b.from) || cmp(a.to, b.to) || cmp(a.text, b.text));
}

// ---- region conditions ----

function product(lists) {
  let acc = [[]];
  for (const l of lists) {
    const next = [];
    for (const a of acc) for (const v of l) next.push([...a, v]);
    acc = next;
    if (acc.length > 200000) throw new ChartError('too many region combinations');
  }
  return acc;
}

function phraseList(values, all, regionName, single) {
  const isList = values;
  const notList = all.filter((v) => !values.includes(v));
  if (single) {
    if (isList.length <= notList.length) return `when ${isList.join(' or ')}`;
    return `when not ${notList.join(' or ')}`;
  }
  if (isList.length <= notList.length) {
    return isList.length === 1 ? `${regionName} is ${isList[0]}` : `${regionName} is one of ${isList.join(', ')}`;
  }
  return notList.length === 1 ? `${regionName} is not ${notList[0]}` : `${regionName} is none of ${notList.join(', ')}`;
}

// contexts: Set of JSON tuples over `others` (array of {region, leaves:[key], names: Map key->display}).
// Returns {kind:'none'|'and'|'or'|'tuple', phrase}.
export function condition(contexts, others) {
  if (others.length === 0) return { kind: 'none', phrase: null };
  const universe = product(others.map((o) => o.leaves));
  const ctx = [...contexts].map((c) => JSON.parse(c));
  if (ctx.length === universe.length) return { kind: 'none', phrase: null };
  const single = others.length === 1;
  const proj = others.map((o, i) => o.leaves.filter((l) => ctx.some((c) => c[i] === l)));
  const prodSize = proj.reduce((n, p) => n * p.length, 1);
  if (prodSize === ctx.length) {
    const parts = [];
    others.forEach((o, i) => {
      if (proj[i].length === o.leaves.length) return;
      parts.push(phraseList(proj[i].map((l) => o.names.get(l)), o.leaves.map((l) => o.names.get(l)), o.region, single));
    });
    return { kind: 'and', phrase: single ? parts[0] : parts.join(' and ') };
  }
  const seen = new Set(contexts);
  const allowed = others.map((o, i) => o.leaves.filter((l) => universe.filter((u) => u[i] === l).every((u) => seen.has(JSON.stringify(u)))));
  const covered = universe.filter((u) => u.some((v, i) => allowed[i].includes(v)));
  if (covered.length === ctx.length && allowed.some((a) => a.length)) {
    const parts = [];
    others.forEach((o, i) => {
      if (allowed[i].length) parts.push(phraseList(allowed[i].map((l) => o.names.get(l)), o.leaves.map((l) => o.names.get(l)), o.region, false));
    });
    return { kind: 'or', phrase: parts.join(' or ') };
  }
  return { kind: 'tuple', phrase: null };
}

// ---- main ----

function canonicalOrder(graph) {
  const { order } = bfs(graph);
  const seen = new Set(order);
  const rest = graph.states.filter((st) => !seen.has(st.index)).sort((a, b) => cmp(a.label0, b.label0) || a.index - b.index).map((st) => st.index);
  return [...order, ...rest];
}

// input: { graph, applied, bugs, rules, verdicts, colors }
export function buildChart(input) {
  const { graph, applied, bugs, rules } = input;
  if (!input.order) input = { ...input, order: canonicalOrder(graph) };
  const ruleById = new Map(rules.map((r) => [r.id, r]));
  const edgeIndex = new Map(graph.edges.map((e, i) => [edgeKey(e.from, e.to, e.action), i]));
  const bugEdges = new Map(); // edge index -> rule id
  const leadIn = new Set();
  const loopStates = new Map(); // ruleId -> Set(state idx)
  for (const b of bugs) {
    const n = b.states.length;
    for (let i = 1; i < n; i++) {
      const ei = edgeIndex.get(edgeKey(b.states[i - 1], b.states[i], b.actions[i]));
      if (ei !== undefined && !bugEdges.has(ei)) bugEdges.set(ei, b.ruleId);
    }
    if (b.kind === 'path') b.states.slice(0, -1).forEach((s) => leadIn.add(s));
    else {
      b.states.slice(0, b.loopIndex).forEach((s) => leadIn.add(s));
      const loop = new Set(b.states.slice(b.loopIndex));
      loopStates.set(b.ruleId, loop);
      if (!b.stutter) {
        const ei = edgeIndex.get(edgeKey(b.states[n - 1], b.states[b.loopIndex], b.loopAction));
        if (ei !== undefined && !bugEdges.has(ei)) bugEdges.set(ei, b.ruleId);
      }
    }
  }
  const describeChange = (e) => {
    const changed = graph.variables.filter((v, k) => show(graph.states[e.from].vals[k]) !== show(graph.states[e.to].vals[k]));
    return changed.length ? changed.join(', ') : 'no variables';
  };
  let hidden = 0;
  graph.edges.forEach((e, i) => {
    if (applied.stepLabels[i] !== null) return;
    hidden++;
    if (bugEdges.has(i)) {
      throw new ViewError(`The view's step function hides ${e.action} from ${graph.states[e.from].label0} to ${graph.states[e.to].label0} (it changes ${describeChange(e)}), but that step is on the path to the ${ruleById.get(bugEdges.get(i)).display} bug. Give it a label.`);
    }
    for (const [rid, loop] of loopStates) {
      if (loop.has(e.from) && !loop.has(e.to)) {
        throw new ViewError(`The view's step function hides ${e.action} from ${graph.states[e.from].label0} (it changes ${describeChange(e)}), a step that leaves the loop of ${ruleById.get(rid).display}. Give it a label.`);
      }
    }
  });

  let idCounter = 0;
  const nextId = () => `s${idCounter++}`;
  let mode = applied.kind;
  let regionNames = applied.regionNames;
  let labels = applied.labels;
  const notes = { hidden, inside: 0, regionsReason: null, stepNotes: [] };

  if (mode === 'regions') {
    const attempt = tryRegions({ graph, applied, nextId, bugEdges, order: input.order });
    if (attempt.ok) return finish(attempt.model);
    notes.regionsReason = attempt.reason;
    idCounter = 0;
    mode = 'nested';
    labels = applied.labels.map((paths) => new Map([['', applied.regionNames.flatMap((r) => paths.get(r).map((p) => `${r}: ${p}`))]]));
    regionNames = [''];
  }

  const { trees, leafOf } = buildTrees(regionNames, labels, nextId, input.order);
  const tree = trees.get('');
  const leaves = leafOf.get('');
  const triples = [];
  graph.edges.forEach((e, i) => {
    const label = applied.stepLabels[i];
    if (label === null) return;
    const a = leaves[e.from];
    const b = leaves[e.to];
    if (a === b && !(mode === 'flat' && bugEdges.has(i))) { notes.inside++; return; }
    triples.push({ from: a, to: b, label, edges: [i] });
  });
  const dedup = new Map();
  for (const t of triples) {
    const k = JSON.stringify([t.from, t.to, t.label]);
    if (dedup.has(k)) dedup.get(k).edges.push(...t.edges);
    else dedup.set(k, t);
  }
  const lifted = liftArrows(tree, [...dedup.values()]);
  loopCheck({ graph, tree, leaves, lifted, loopStates, applied, ruleById });
  const arrows = mergeArrows(lifted);
  const model = {
    mode, regionNames, trees, leafOf, arrows: new Map([['', arrows]]),
    initial: new Map([['', [...new Set(graph.states.filter((s) => s.initial).map((s) => leaves[s.index]))]]]),
  };
  return finish(model);

  function finish(m) {
    m.notes = { ...notes, ...(m.notes ?? {}) };
    if (m.mode === 'regions') m.notes.inside = m.inside;
    markStates(m, { graph, applied, leadIn, loopStates, bugs });
    m.stateCount = [...m.trees.values()].reduce((n, t) => n + [...t.nodes.values()].filter((x) => x.leaf).length, 0);
    m.arrowCount = [...m.arrows.values()].reduce((n, a) => n + a.length, 0);
    m.describe = (stateIdx) => describeState(m, labels, stateIdx);
    return m;
  }
}

function describeState(m, labels, idx) {
  if (m.mode === 'regions') {
    return m.regionNames.map((r) => `${r}: ${labels[idx].get(r).join(PATH_SEP)}`).join('; ');
  }
  return labels[idx].get('').join(PATH_SEP);
}

function loopCheck({ graph, tree, leaves, lifted, loopStates, applied, ruleById }) {
  for (const [rid, loop] of loopStates) {
    const loopLeaves = new Set([...loop].map((s) => leaves[s]));
    for (const a of lifted) {
      const srcLoopLeaves = [...loopLeaves].filter((l) => isUnder(tree, l, a.from));
      if (!srcLoopLeaves.length) continue;
      if ([...loopLeaves].some((l) => isUnder(tree, l, a.to))) continue;
      const ok = graph.edges.some((e, i) => loop.has(e.from) && applied.stepLabels[i] === a.label && isUnder(tree, leaves[e.to], a.to));
      if (!ok) {
        const src = tree.nodes.get(a.from).path.join(PATH_SEP);
        const dst = tree.nodes.get(a.to).path.join(PATH_SEP);
        throw new ViewError(`The chart draws the step ${JSON.stringify(a.label)} from ${JSON.stringify(src)} to ${JSON.stringify(dst)}, but no state in the loop that breaks ${ruleById.get(rid).display} can take it. Show in a label what stops the loop from taking that step.`);
      }
    }
  }
}

function tryRegions({ graph, applied, nextId, bugEdges, order }) {
  const R = applied.regionNames;
  const { trees, leafOf } = buildTrees(R, applied.labels, nextId, order);
  const nameOf = (r, key) => trees.get(r).nodes.get(key).path.join(PATH_SEP);
  const combo = (i) => R.map((r) => leafOf.get(r)[i]);
  const comboText = (c) => R.map((r, k) => `${r} ${nameOf(r, c[k])}`).join(', ');
  const allLeaves = new Map(R.map((r) => [r, [...trees.get(r).nodes.values()].filter((n) => n.leaf).map((n) => n.key).sort((a, b) => cmp(nameOf(r, a), nameOf(r, b)))]));
  const initialCombos = new Set(graph.states.filter((s) => s.initial).map((s) => JSON.stringify(combo(s.index))));
  const startLeaves = R.map((r) => [...new Set(graph.states.filter((s) => s.initial).map((s) => leafOf.get(r)[s.index]))]);
  let starts;
  try { starts = product(startLeaves); } catch { return { ok: false, reason: 'Regions would need too many start combinations to check.' }; }
  for (const c of starts) {
    if (!initialCombos.has(JSON.stringify(c))) {
      return { ok: false, reason: `Regions would let the run start in ${comboText(c)}, which is not an initial state of the model.` };
    }
  }
  // Model moves and region arrows.
  const modelMoves = new Set();
  const syncLabels = new Map(); // label -> Set of JSON combo-change descriptions
  const regionArrows = new Map(R.map((r) => [r, new Map()]));
  let inside = 0;
  graph.edges.forEach((e, i) => {
    const label = applied.stepLabels[i];
    if (label === null) return;
    const a = combo(e.from);
    const b = combo(e.to);
    const changed = R.filter((r, k) => a[k] !== b[k]);
    if (!changed.length) { inside++; return; }
    modelMoves.add(JSON.stringify([a, b, label]));
    if (changed.length >= 2) {
      if (!syncLabels.has(label)) syncLabels.set(label, new Set());
      syncLabels.get(label).add(changed.join('\u0000'));
    }
    R.forEach((r, k) => {
      if (a[k] === b[k]) return;
      const ak = JSON.stringify([a[k], b[k], label]);
      const m = regionArrows.get(r);
      if (!m.has(ak)) m.set(ak, { from: a[k], to: b[k], label, contexts: new Set(), edges: [] });
      const arrow = m.get(ak);
      arrow.contexts.add(JSON.stringify(a.filter((_, j) => j !== k)));
      arrow.edges.push(i);
    });
  });
  // Labels that change several regions in one step, and whether they ever change just one.
  const stepNotes = [];
  for (const [label] of [...syncLabels].sort((x, y) => cmp(x[0], y[0]))) {
    const combos = new Set();
    let alone = false;
    graph.edges.forEach((e, i) => {
      if (applied.stepLabels[i] !== label) return;
      const a = combo(e.from);
      const b = combo(e.to);
      const changed = R.filter((r, k) => a[k] !== b[k]);
      if (changed.length >= 2) combos.add(changed.join(' and '));
      else if (changed.length === 1) alone = true;
    });
    stepNotes.push({ label, together: [...combos].sort(cmp), alone });
  }
  // Conditions.
  for (const [k, r] of R.entries()) {
    const others = R.filter((_, j) => j !== k).map((o) => ({ region: o, leaves: allLeaves.get(o), names: new Map(allLeaves.get(o).map((l) => [l, nameOf(o, l)])) }));
    for (const arrow of regionArrows.get(r).values()) {
      let c;
      try { c = condition(arrow.contexts, others); } catch { return { ok: false, reason: 'Regions would need too many combinations to check.' }; }
      if (c.kind === 'tuple') {
        return { ok: false, reason: `In region ${r}, the step ${JSON.stringify(arrow.label)} from ${nameOf(r, arrow.from)} to ${nameOf(r, arrow.to)} happens only in combinations of the other regions that no single condition on them can state.` };
      }
      arrow.cond = c.phrase;
    }
  }
  // Chart moves must equal model moves.
  const arrowsByRegion = R.map((r) => [...regionArrows.get(r).values()]);
  const enabled = (k, c, label) => arrowsByRegion[k].filter((a) => a.label === label && a.from === c[k] && a.contexts.has(JSON.stringify(c.filter((_, j) => j !== k))));
  const labelsAll = [...new Set(arrowsByRegion.flat().map((a) => a.label))];
  const seen = new Set(starts.map((c) => JSON.stringify(c)));
  const queue = starts.slice();
  const modelFrom = new Map();
  for (const mv of modelMoves) {
    const [a] = JSON.parse(mv);
    const k = JSON.stringify(a);
    if (!modelFrom.has(k)) modelFrom.set(k, []);
    modelFrom.get(k).push(mv);
  }
  while (queue.length) {
    const c = queue.shift();
    const chartMoves = new Set();
    for (const label of labelsAll) {
      const per = R.map((_, k) => enabled(k, c, label));
      if (syncLabels.has(label)) {
        const active = per.map((p, k) => [k, p]).filter(([, p]) => p.length);
        if (!active.length) continue;
        for (const choice of product(active.map(([, p]) => p))) {
          const next = c.slice();
          active.forEach(([k], j) => { next[k] = choice[j].to; });
          chartMoves.add(JSON.stringify([c, next, label]));
        }
      } else {
        per.forEach((p, k) => {
          for (const a of p) {
            const next = c.slice();
            next[k] = a.to;
            chartMoves.add(JSON.stringify([c, next, label]));
          }
        });
      }
    }
    for (const mv of chartMoves) {
      if (!modelMoves.has(mv)) {
        const [a, b, label] = JSON.parse(mv);
        return { ok: false, reason: `Regions would show the step ${JSON.stringify(label)} from ${comboText(a)} to ${comboText(b)}, which the model never takes.` };
      }
      const [, b] = JSON.parse(mv);
      const bk = JSON.stringify(b);
      if (!seen.has(bk)) { seen.add(bk); queue.push(b); }
    }
    for (const mv of modelFrom.get(JSON.stringify(c)) ?? []) {
      if (!chartMoves.has(mv)) {
        const [a, b, label] = JSON.parse(mv);
        return { ok: false, reason: `Regions cannot show the step ${JSON.stringify(label)} from ${comboText(a)} to ${comboText(b)} that the model takes.` };
      }
    }
  }
  // Build drawn arrows per region (with lifting and merging).
  const arrows = new Map();
  R.forEach((r, k) => {
    const triples = arrowsByRegion[k].map((a) => ({ from: a.from, to: a.to, label: a.label, cond: a.cond, edges: a.edges }));
    arrows.set(r, mergeArrows(liftArrows(trees.get(r), triples)));
  });
  void bugEdges;
  const initial = new Map(R.map((r, k) => [r, startLeaves[k]]));
  return { ok: true, model: { mode: 'regions', regionNames: R, trees, leafOf, arrows, initial, inside, notes: { stepNotes } } };
}

// Assign classes: groups, breaks/mayBreak (with rules), bugPath, repeats.
function markStates(m, { graph, applied, leadIn, loopStates, bugs }) {
  const breakingStates = graph.states.filter((s) => s.breaks.size);
  const comboKey = (i) => JSON.stringify(m.regionNames.map((r) => m.leafOf.get(r)[i]));
  const dirty = new Set(breakingStates.map((s) => comboKey(s.index)));
  const cleanCombos = new Set(graph.states.map((s) => comboKey(s.index)).filter((k) => !dirty.has(k)));
  for (const [r, tree] of m.trees) {
    const leafOf = m.leafOf.get(r);
    for (const n of tree.nodes.values()) {
      if (!n.leaf) continue;
      n.marks = { always: new Set(), some: new Set(), bugPath: new Set(), repeats: new Set() };
      const members = n.members.map((i) => graph.states[i]);
      const rulesHere = new Set(members.flatMap((s) => [...s.breaks]));
      for (const rid of rulesHere) {
        if (members.every((s) => s.breaks.has(rid))) n.marks.always.add(rid);
        else n.marks.some.add(rid);
      }
      // In a regions chart a member "works" when its whole combination of
      // region labels is clean (no model state with that combination breaks).
      n.works = m.mode === 'regions'
        ? members.some((s) => cleanCombos.has(comboKey(s.index)))
        : members.some((s) => s.breaks.size === 0);
      if (applied.groups) {
        const gs = new Set(n.members.map((i) => applied.groups[i]));
        n.group = gs.size === 1 ? [...gs][0] : null;
      }
      for (const b of bugs) {
        if (b.kind === 'path') { if (b.states.slice(0, -1).some((i) => leafOf[i] === n.key)) n.marks.bugPath.add(b.ruleId); }
        else {
          if (b.states.slice(0, b.loopIndex).some((i) => leafOf[i] === n.key)) n.marks.bugPath.add(b.ruleId);
          if ([...loopStates.get(b.ruleId)].some((i) => leafOf[i] === n.key)) n.marks.repeats.add(b.ruleId);
        }
      }
    }
  }
  if (m.mode === 'regions') {
    for (const s of breakingStates) {
      const nodes = m.regionNames.map((r) => m.trees.get(r).nodes.get(m.leafOf.get(r)[s.index]));
      if (nodes.every((n) => n.works)) for (const n of nodes) n.forced = true;
    }
  }
  for (const tree of m.trees.values()) {
    for (const n of tree.nodes.values()) {
      if (!n.leaf) continue;
      const anyBreak = n.marks.always.size + n.marks.some.size > 0;
      if (m.mode === 'regions') {
        if (n.marks.always.size && !n.works) n.mark = 'breaks';
        else if (anyBreak && (!n.works || n.forced)) n.mark = 'mayBreak';
        else n.mark = null;
      } else if (n.marks.always.size) n.mark = 'breaks';
      else if (anyBreak) n.mark = 'mayBreak';
      else n.mark = null;
    }
  }
  void leadIn;
}
