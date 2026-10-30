// Loads, validates, and calls a view module (labels, groups, colors, title).

import { inspect } from 'node:util';
import { pathToFileURL } from 'node:url';
import path from 'node:path';

export const COLORS = ['blue', 'orange', 'purple', 'yellow', 'teal', 'tan', 'pink'];
export const MARK_CLASSES = ['breaks', 'mayBreak', 'bugPath', 'repeats'];
const ALLOWED = ['state', 'step', 'group', 'colors', 'title'];

export class ViewError extends Error {}

export function describeThrown(e) {
  if (e !== null && typeof e === 'object') {
    let msg;
    try { msg = e.message; } catch { msg = undefined; }
    if (typeof msg === 'string') return msg;
  }
  return inspect(e, { breakLength: Infinity, depth: 4 });
}

function show(v) {
  return inspect(v, { breakLength: Infinity, depth: 6 });
}

function isPlainObject(v) {
  if (v === null || typeof v !== 'object') return false;
  const proto = Object.getPrototypeOf(v);
  return proto === Object.prototype || proto === null;
}

// Validate a module namespace (or any object with the view's exports).
export function checkView(ns) {
  const names = Object.keys(ns);
  const unexpected = names.filter((n) => !ALLOWED.includes(n));
  if (unexpected.length) {
    throw new ViewError(`The view's exports ${unexpected.join(', ')} are not recognized. A view may export only ${ALLOWED.join(', ')}.`);
  }
  const problems = [];
  for (const fn of ['state', 'step', 'group']) {
    if (fn in ns && typeof ns[fn] !== 'function') problems.push(`The view's ${fn} export must be a function, not ${show(ns[fn])}.`);
  }
  if ('title' in ns && typeof ns.title !== 'string') problems.push(`The view's title export must be a string, not ${show(ns.title)}.`);
  let colors = null;
  if ('colors' in ns) {
    if (!isPlainObject(ns.colors)) {
      problems.push(`The view's colors export must be a plain object mapping group names to colors, not ${show(ns.colors)}.`);
    } else {
      colors = new Map();
      for (const k of Object.keys(ns.colors)) {
        const v = ns.colors[k];
        if (!COLORS.includes(v)) {
          problems.push(`The view's colors entry ${JSON.stringify(k)} is ${show(v)}; use one of ${COLORS.join(', ')}.`);
        } else colors.set(k, v);
      }
    }
  }
  if ('group' in ns && !('colors' in ns)) problems.push("The view's group export needs a colors export that gives each group a color.");
  if (problems.length) throw new ViewError(problems.join('\n'));
  return {
    state: ns.state ?? null,
    step: ns.step ?? null,
    group: ns.group ?? null,
    colors: colors ?? new Map(),
    title: ns.title ?? null,
  };
}

export async function loadView(file) {
  let ns;
  try {
    ns = await import(pathToFileURL(path.resolve(file)).href);
  } catch (e) {
    throw new ViewError(describeThrown(e));
  }
  return checkView({ ...ns });
}

const BAD_TEXT = /undefined|NaN|\[object Object\]/;

function checkLabelText(s) {
  return typeof s === 'string' && s.length > 0 && !BAD_TEXT.test(s);
}

// Normalize a state label into {kind:'flat'|'nested'|'regions', paths}.
// paths: Map(regionName -> array of strings), regionName '' for non-region.
export function normalizeStateLabel(raw, describeState) {
  const bad = (why) => new ViewError(`The view's state function returned ${show(raw)} ${why} for the state ${describeState()}.`);
  const asPath = (v) => {
    if (typeof v === 'string') {
      if (!checkLabelText(v)) throw bad('(a label must be a non-empty string without the words undefined or NaN or the text [object Object])');
      return [v];
    }
    if (Array.isArray(v)) {
      if (v.length === 0) throw bad('(an empty array has no leaf label)');
      for (const p of v) if (!checkLabelText(p)) throw bad('(each part of a label path must be a non-empty string without undefined, NaN, or [object Object])');
      return v.slice();
    }
    throw bad('(a label must be a string, an array of strings, or an object of regions)');
  };
  if (typeof raw === 'string') return { kind: 'flat', paths: new Map([['', asPath(raw)]]) };
  if (Array.isArray(raw)) return { kind: 'nested', paths: new Map([['', asPath(raw)]]) };
  if (raw !== null && typeof raw === 'object' && isPlainObject(raw)) {
    const keys = Object.keys(raw);
    if (keys.length === 0) throw bad('(an object of regions needs at least one region)');
    const paths = new Map();
    for (const k of keys) paths.set(k, asPath(raw[k]));
    return { kind: 'regions', paths };
  }
  throw bad('(a label must be a string, an array of strings, or an object of regions)');
}

// Labels for every state and step, each view function called exactly once per item.
// states: [{vals}], edges: [{from, to, action}] (indices into states).
export function applyView(view, variables, states, edges, toViewVars, defaultLabel) {
  const varsCache = new Map();
  const varsOf = (i) => {
    let v = varsCache.get(i);
    if (!v) {
      v = Object.create(null);
      const obj = {};
      variables.forEach((name, k) => Object.defineProperty(obj, name, { value: toViewVars(states[i].vals[k]), enumerable: true, writable: true, configurable: true }));
      v = obj;
      varsCache.set(i, v);
    }
    return v;
  };
  const describe = (i) => () => defaultLabel(states[i]);
  const labels = [];
  let kind = null;
  let regionNames = null;
  for (let i = 0; i < states.length; i++) {
    let raw;
    if (view?.state) {
      try { raw = view.state(varsOf(i)); } catch (e) { throw new ViewError(`The view's state function threw for the state ${defaultLabel(states[i])}: ${describeThrown(e)}`); }
    } else raw = defaultLabel(states[i]);
    const norm = normalizeStateLabel(raw, describe(i));
    if (kind === null) { kind = norm.kind; regionNames = [...norm.paths.keys()]; }
    if (norm.kind !== kind && !(kind !== 'regions' && norm.kind !== 'regions')) {
      throw new ViewError(`The view's state function returns regions for some states and not for others (see ${defaultLabel(states[i])}).`);
    }
    if (kind === 'regions') {
      const names = [...norm.paths.keys()];
      if (names.length !== regionNames.length || names.some((n) => !regionNames.includes(n))) {
        throw new ViewError(`The view's state function must return the same region names for every state; got ${names.join(', ')} instead of ${regionNames.join(', ')} for ${defaultLabel(states[i])}.`);
      }
    }
    if (norm.kind === 'nested') kind = 'nested';
    labels.push(norm.paths);
  }
  const groups = [];
  if (view?.group) {
    for (let i = 0; i < states.length; i++) {
      let g;
      try { g = view.group(varsOf(i)); } catch (e) { throw new ViewError(`The view's group function threw for the state ${defaultLabel(states[i])}: ${describeThrown(e)}`); }
      if (typeof g !== 'string' || !view.colors.has(g)) {
        throw new ViewError(`The view's group function returned ${show(g)} for the state ${defaultLabel(states[i])}, which is not a key of colors.`);
      }
      groups.push(g);
    }
  }
  const stepLabels = [];
  for (const e of edges) {
    let l;
    if (view?.step) {
      try { l = view.step(e.action, varsOf(e.from), varsOf(e.to)); } catch (err) {
        throw new ViewError(`The view's step function threw for ${e.action} from ${defaultLabel(states[e.from])}: ${describeThrown(err)}`);
      }
      if (l !== null && !checkLabelText(l)) {
        throw new ViewError(`The view's step function returned ${show(l)} for ${e.action} from ${defaultLabel(states[e.from])} to ${defaultLabel(states[e.to])}; return a non-empty string without undefined or NaN, or null to hide the step.`);
      }
    } else l = e.action ?? 'step';
    stepLabels.push(l);
  }
  return { kind: kind ?? 'flat', regionNames: kind === 'regions' ? regionNames : [''], labels, groups: view?.group ? groups : null, stepLabels };
}
