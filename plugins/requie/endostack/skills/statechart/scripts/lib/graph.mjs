// Builds the state graph the chart is drawn from: TLC's DOT dump plus the
// marks the drawing run printed, plus counterexample traces. Then finds the
// shortest path from an initial state to each broken rule.

import { parseDot } from './dot.mjs';
import { parseMessages, trace as readTrace, plainLines } from './tlc-output.mjs';
import { parseValue, parseState, show, stateKey, ValueError } from './values.mjs';

export class GraphError extends Error {}

export function defaultLabel(variables, vals) {
  if (variables.length === 1) return show(vals[0]);
  return variables.map((v, i) => `${v}=${show(vals[i])}`).join(' ');
}

function newGraph(variables) {
  return { variables, states: [], edges: [], byKey: new Map(), ruleEnd: new Map(), lassos: new Map(), paths: new Map() };
}

function addState(g, vals, extra = {}) {
  const st = { vals, key: stateKey(vals), initial: false, kind: 'normal', breaks: new Set(), ...extra };
  st.index = g.states.length;
  g.states.push(st);
  if (st.kind === 'normal' && !g.byKey.has(st.key)) g.byKey.set(st.key, st.index);
  st.label0 = defaultLabel(g.variables, vals);
  return st.index;
}

function hasEdge(g, from, to, action) {
  return g.edges.some((e) => e.from === from && e.to === to && e.action === action);
}

// ---- marks ----

function bracketDelta(text) {
  let d = 0;
  let inStr = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (inStr) {
      if (c === '\\') i++;
      else if (c === '"') inStr = false;
      continue;
    }
    if (c === '"') inStr = true;
    else if ((c === '<' && text[i + 1] === '<') || (c === '>' && text[i + 1] === '>')) { d += c === '<' ? 1 : -1; i++; }
    else if (c === '{' || c === '[' || c === '(') d++;
    else if (c === '}' || c === ']' || c === ')') d--;
  }
  return d;
}

// Read marks from the drawing run's plain output lines.
// Returns [{vals, names}] where vals are parsed values in variable order.
export function parseMarks(stdout, tag, variableCount) {
  const tree = parseMessages(stdout);
  const lines = plainLines(tree);
  const opener = new RegExp(`^<<\\s*"${tag}"\\s*,`);
  const marks = [];
  let buf = null;
  let depth = 0;
  for (const line of lines) {
    if (line === null) continue;
    if (buf === null) {
      if (!opener.test(line)) continue;
      buf = line;
      depth = bracketDelta(line);
    } else {
      buf += `\n${line}`;
      depth += bracketDelta(line);
    }
    if (depth <= 0) {
      let v;
      try { v = parseValue(buf); } catch (e) { throw new GraphError(`TLC printed a chart mark the command cannot read (${e.message}).`); }
      const ok = v.t === 'tup' && v.items.length === 3 && v.items[1].t === 'tup' && v.items[1].items.length === variableCount
        && v.items[2].t === 'set' && v.items[2].items.every((x) => x.t === 'str');
      if (!ok) throw new GraphError('TLC printed a chart mark in the wrong shape.');
      marks.push({ vals: v.items[1].items, names: v.items[2].items.map((x) => x.v) });
      buf = null;
    }
  }
  if (buf !== null) throw new GraphError('TLC output ends in the middle of a chart mark.');
  return marks;
}

// ---- traces ----

function traceStates(evidence, variables) {
  const t = readTrace(parseMessages(evidence));
  const states = t.states.map((s) => {
    let vals;
    try { vals = parseState(s.text, variables); } catch (e) {
      if (e instanceof ValueError) throw new GraphError(`Cannot read a counterexample state: ${e.message}`);
      throw e;
    }
    return { action: s.action, vals, key: stateKey(vals) };
  });
  return { states, loopBack: t.loopBack, stutter: t.stutter };
}

function isLasso(t) {
  return t.loopBack !== null || t.stutter;
}

// ---- full graph ----

// Build the graph from the drawing run.
// opts: { variables, dotText, drawStdout, tag, rules, verdicts, config, drawComplete, partial }
export function buildFullGraph(opts) {
  const { variables, rules, verdicts, config } = opts;
  const g = newGraph(variables);
  const dot = parseDot(opts.dotText);
  const idToIndex = new Map();
  for (const s of dot.states.values()) {
    let vals;
    try { vals = parseState(s.text, variables); } catch (e) {
      if (e instanceof ValueError) throw new GraphError(`Cannot read a state in TLC's graph dump: ${e.message}`);
      throw e;
    }
    const key = stateKey(vals);
    let idx = g.byKey.get(key);
    if (idx === undefined) idx = addState(g, vals);
    if (s.initial) g.states[idx].initial = true;
    idToIndex.set(s.id, idx);
  }
  const seen = new Set();
  for (const e of dot.edges) {
    const from = idToIndex.get(e.from);
    const to = idToIndex.get(e.to);
    const k = [from, to, e.action].map(String).join('>');
    if (seen.has(k)) continue;
    seen.add(k);
    g.edges.push({ from, to, action: e.action ?? 'Next' });
  }
  g.stepCount = g.edges.length;
  g.stateCount = g.states.length;

  const broken = (r) => verdicts.get(r.id)?.status === 'broken';
  const invByName = new Map();
  for (const r of rules) if (r.kind === 'invariant' && broken(r)) invByName.set(r.name, [...(invByName.get(r.name) ?? []), r.id]);

  const pastMarks = new Map();
  for (const m of parseMarks(opts.drawStdout, opts.tag, variables.length)) {
    const ids = m.names.flatMap((n) => invByName.get(n) ?? []);
    if (!ids.length) continue;
    const key = stateKey(m.vals);
    const idx = g.byKey.get(key);
    if (idx !== undefined) for (const id of ids) g.states[idx].breaks.add(id);
    else {
      const entry = pastMarks.get(key) ?? { vals: m.vals, ids: new Set() };
      for (const id of ids) entry.ids.add(id);
      pastMarks.set(key, entry);
    }
  }

  const deadlock = rules.find((r) => r.kind === 'deadlock' && broken(r));
  const constrained = config.constraints.length > 0 || config.actionConstraints.length > 0;
  if (deadlock && opts.drawComplete && !constrained) {
    const out = new Set(g.edges.map((e) => e.from));
    for (const s of g.states) if (!out.has(s.index)) s.breaks.add(deadlock.id);
  }

  const lenient = config.hasView || config.hasSymmetry;
  const pastByKey = new Map();
  for (const r of rules) {
    if (!broken(r)) continue;
    const t = traceStates(verdicts.get(r.id).evidence, variables);
    if (t.states.length === 0) continue;
    if (isLasso(t)) {
      const lasso = mapLasso(g, t);
      if (lasso) g.lassos.set(r.id, lasso);
      continue;
    }
    const n = t.states.length;
    const known = t.states.slice(0, -1).map((s) => g.byKey.get(s.key));
    if (known.some((x) => x === undefined)) {
      if (opts.partial || lenient) continue;
      throw new GraphError(`The counterexample for ${r.display} passes through a state missing from TLC's graph dump.`);
    }
    const last = t.states[n - 1];
    const prev = n > 1 ? known[n - 2] : null;
    const lastIdx = g.byKey.get(last.key);
    if (lastIdx === undefined) {
      let pidx = pastByKey.get(last.key);
      if (pidx === undefined) {
        pidx = addState(g, last.vals, { kind: 'past' });
        pastByKey.set(last.key, pidx);
        const pm = pastMarks.get(last.key);
        if (pm) for (const id of pm.ids) g.states[pidx].breaks.add(id);
        if (prev === null) g.states[pidx].initial = true;
      }
      if (prev !== null && !hasEdge(g, prev, pidx, last.action)) g.edges.push({ from: prev, to: pidx, action: last.action });
      g.states[pidx].breaks.add(r.id);
      g.ruleEnd.set(r.id, pidx);
    } else if (prev !== null && !hasEdge(g, prev, lastIdx, last.action) && config.actionConstraints.length > 0) {
      const xidx = addState(g, last.vals, { kind: 'excluded' });
      g.edges.push({ from: prev, to: xidx, action: last.action });
      g.states[xidx].breaks.add(r.id);
      g.ruleEnd.set(r.id, xidx);
    } else {
      if (prev !== null && !hasEdge(g, prev, lastIdx, last.action)) {
        if (opts.partial || lenient) continue;
        throw new GraphError(`The counterexample for ${r.display} takes a step missing from TLC's graph dump.`);
      }
      if (r.kind !== 'invariant' || !g.states[lastIdx].breaks.has(r.id)) {
        g.states[lastIdx].breaks.add(r.id);
        if (r.kind !== 'invariant') g.ruleEnd.set(r.id, lastIdx);
      }
    }
  }
  return g;
}

function mapLasso(g, t) {
  const first = g.byKey.get(t.states[0].key);
  if (first === undefined || !g.states[first].initial) return null;
  const path = [first];
  const actions = [null];
  for (let i = 1; i < t.states.length; i++) {
    const cur = path[path.length - 1];
    const e = g.edges.find((x) => x.from === cur && x.action === t.states[i].action && g.states[x.to].key === t.states[i].key);
    if (!e) return null;
    path.push(e.to);
    actions.push(e.action);
  }
  if (t.stutter) return { path, actions, loopIndex: path.length - 1, stutter: true, loopAction: null };
  const target = path[t.loopBack.index];
  if (target === undefined) return null;
  const last = path[path.length - 1];
  const back = g.edges.find((x) => x.from === last && x.to === target && x.action === t.loopBack.action);
  if (!back) return null;
  return { path, actions, loopIndex: t.loopBack.index, stutter: false, loopAction: back.action };
}

// ---- paths-only graph ----

export function buildPathsGraph({ variables, rules, verdicts }) {
  const g = newGraph(variables);
  g.pathsOnly = true;
  const get = (s, initial) => {
    let idx = g.byKey.get(s.key);
    if (idx === undefined) idx = addState(g, s.vals);
    if (initial) g.states[idx].initial = true;
    return idx;
  };
  const link = (from, to, action) => { if (!hasEdge(g, from, to, action)) g.edges.push({ from, to, action }); };
  for (const r of rules) {
    const v = verdicts.get(r.id);
    if (v?.status !== 'broken') continue;
    const t = traceStates(v.evidence, variables);
    if (t.states.length === 0) continue;
    const idxs = t.states.map((s, i) => get(s, i === 0));
    for (let i = 1; i < idxs.length; i++) link(idxs[i - 1], idxs[i], t.states[i].action);
    if (isLasso(t)) {
      const lasso = { path: idxs, actions: t.states.map((s) => s.action), loopIndex: t.stutter ? idxs.length - 1 : t.loopBack.index, stutter: t.stutter, loopAction: t.stutter ? null : t.loopBack.action };
      if (!t.stutter) {
        if (idxs[lasso.loopIndex] === undefined) continue;
        link(idxs[idxs.length - 1], idxs[lasso.loopIndex], t.loopBack.action);
      }
      g.lassos.set(r.id, lasso);
    } else {
      const last = idxs[idxs.length - 1];
      g.states[last].breaks.add(r.id);
      g.ruleEnd.set(r.id, last);
    }
  }
  g.stepCount = g.edges.length;
  g.stateCount = g.states.length;
  return g;
}

// ---- shortest bug paths ----

export function bfs(g) {
  const out = new Map();
  for (const e of g.edges) {
    if (!out.has(e.from)) out.set(e.from, []);
    out.get(e.from).push(e);
  }
  const cmp = (a, b) => (a < b ? -1 : a > b ? 1 : 0);
  for (const list of out.values()) list.sort((a, b) => cmp(a.action, b.action) || cmp(g.states[a.to].label0, g.states[b.to].label0) || a.to - b.to);
  const starts = g.states.filter((s) => s.initial).sort((a, b) => cmp(a.label0, b.label0) || a.index - b.index);
  const order = [];
  const pred = new Map();
  const seen = new Set();
  const queue = [];
  for (const s of starts) { seen.add(s.index); pred.set(s.index, null); queue.push(s.index); }
  while (queue.length) {
    const cur = queue.shift();
    order.push(cur);
    for (const e of out.get(cur) ?? []) {
      if (seen.has(e.to)) continue;
      seen.add(e.to);
      pred.set(e.to, e);
      queue.push(e.to);
    }
  }
  return { order, pred };
}

// Returns bugs: [{ruleId, kind:'path'|'lasso', states:[idx], actions:[label|null], loopIndex?, stutter?, loopAction?}]
export function findBugs(g, rules, verdicts) {
  const { order, pred } = bfs(g);
  const rank = new Map(order.map((idx, i) => [idx, i]));
  const bugs = [];
  for (const r of rules) {
    if (verdicts.get(r.id)?.status !== 'broken' || g.lassos.has(r.id)) continue;
    let target = g.ruleEnd.get(r.id);
    if (target === undefined || !rank.has(target)) {
      target = order.find((idx) => g.states[idx].breaks.has(r.id));
    }
    if (target === undefined) continue;
    const states = [target];
    const actions = [];
    let e = pred.get(target);
    while (e) {
      actions.unshift(e.action);
      states.unshift(e.from);
      e = pred.get(e.from);
    }
    actions.unshift(null);
    bugs.push({ ruleId: r.id, kind: 'path', states, actions });
  }
  bugs.sort((a, b) => a.states.length - b.states.length);
  for (const r of rules) {
    const l = g.lassos.get(r.id);
    if (l && verdicts.get(r.id)?.status === 'broken') bugs.push({ ruleId: r.id, kind: 'lasso', states: l.path, actions: l.actions, loopIndex: l.loopIndex, stutter: l.stutter, loopAction: l.loopAction });
  }
  return { bugs, order };
}
