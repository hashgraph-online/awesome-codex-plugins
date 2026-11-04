// Turns a parsed config into rules, then runs TLC as many times as needed to
// learn the verdict of every rule (TLC stops at the first violation).

import { parseMessages, runFacts, errorExcerpt } from './tlc-output.mjs';
import { definitionLevel } from './sany.mjs';

export const RERUN_BOUND = 100000;

export class CheckError extends Error {}

export function exitClass(code) {
  if (code === 0) return 0;
  if (code === 11 || code === 12 || code === 13) return 1;
  return 2;
}

// Rules in report order: invariants, deadlock, properties.
export function makeRules(config) {
  const rules = [];
  config.invariants.forEach((name, i) => rules.push({ id: `inv:${i}:${name}`, kind: 'invariant', name, display: name }));
  if (config.checkDeadlock) {
    const taken = config.invariants.includes('NoDeadlock') || config.properties.includes('NoDeadlock');
    rules.push({ id: 'deadlock', kind: 'deadlock', name: null, display: taken ? 'CHECK_DEADLOCK' : 'NoDeadlock' });
  }
  config.properties.forEach((name, i) => rules.push({ id: `prop:${i}:${name}`, kind: 'property', name, display: name }));
  return rules;
}

// Properties TLC only evaluates in initial states (no temporal operator).
export function initialOnlyProperties(rules, config, sany) {
  const out = new Set();
  for (const r of rules) {
    if (r.kind !== 'property') continue;
    let name = r.name;
    const seen = new Set();
    while (config.substitutions.has(name) && !seen.has(name)) { seen.add(name); name = config.substitutions.get(name); }
    const level = definitionLevel(sany, name);
    if (level !== null && level <= 1) out.add(r.id);
  }
  return out;
}

export function verdictConfig(config, rules, extra = {}) {
  const lines = [];
  if (config.written) lines.push(config.written);
  const invs = rules.filter((r) => r.kind === 'invariant').map((r) => r.name);
  const props = rules.filter((r) => r.kind === 'property').map((r) => r.name);
  if (invs.length) lines.push(`INVARIANT ${invs.join(' ')}`);
  if (props.length) lines.push(`PROPERTY ${props.join(' ')}`);
  if (extra.constraint) lines.push(`CONSTRAINT ${extra.constraint}`);
  lines.push(`CHECK_DEADLOCK ${rules.some((r) => r.kind === 'deadlock') ? 'TRUE' : 'FALSE'}`);
  return lines.join('\n');
}

function boundWrapper(module, name, bound) {
  return {
    name,
    text: [
      `---- MODULE ${name} ----`,
      `EXTENDS ${module}`,
      'LOCAL INSTANCE Naturals',
      `${name}_TLC == INSTANCE TLC`,
      `${name}_Bound == ${name}_TLC!TLCGet("distinct") < ${bound}`,
      '====',
      '',
    ].join('\n'),
  };
}

function attribute(facts, group) {
  const b = facts.broken;
  if (!b) return null;
  if (b.kind === 'deadlock') return group.find((r) => r.kind === 'deadlock') ?? null;
  if (b.kind === 'temporal') return null;
  if (b.kind === 'invariant') {
    return group.find((r) => r.kind === 'invariant' && r.name === b.name)
      ?? group.find((r) => r.kind === 'property' && r.name === b.name) ?? null;
  }
  return group.find((r) => r.kind === 'property' && r.name === b.name) ?? null;
}

// Runs the verdict loop. `run` is a runner (see toolchain.mjs).
// Returns { firstExit, firstOutput, verdicts: Map<ruleId, {status, evidence?}>,
//           distinct, initial, complete, cut, stop }.
export async function checkRules({ run, specPath, specDir, module, config, rules, bound = RERUN_BOUND }) {
  const verdicts = new Map();
  let distinct = null;
  let initial = null;
  let complete = false;
  let cut = false;
  let stop = null;
  let runNo = 0;

  const doRun = async (group, bounded) => {
    runNo++;
    const req = { name: `verdict-${runNo}`, kind: 'tlc', spec: specPath, specDir, dump: false };
    if (bounded) {
      const w = boundWrapper(module, `SCBound_${module}`, bound);
      req.wrapper = w;
      req.cfgText = verdictConfig(config, group, { constraint: `${w.name}_Bound` });
    } else {
      req.cfgText = verdictConfig(config, group);
    }
    const res = await run(req);
    const tree = parseMessages(res.stdout);
    const facts = runFacts(tree);
    if (facts.distinct !== null) distinct = Math.max(distinct ?? 0, facts.distinct);
    if (facts.initial !== null) initial = Math.max(initial ?? 0, facts.initial);
    return { res, tree, facts };
  };

  const first = await doRun(rules, false);
  const firstExit = exitClass(first.res.exit);
  if (firstExit === 2) {
    throw new CheckError(`TLC stopped with exit status ${first.res.exit} on the config as written:\n${errorExcerpt(first.tree)}`);
  }
  const firstExploredAll = first.res.exit === 0;
  const queue = [rules.slice()];
  let pending = first;

  while (queue.length && !stop) {
    const group = queue.shift();
    const open = group.filter((r) => !verdicts.has(r.id));
    if (open.length === 0) continue;
    const bounded = !firstExploredAll && pending === null;
    const result = pending ?? await doRun(open, bounded);
    pending = null;
    const { res, facts, tree } = result;
    const cls = exitClass(res.exit);
    const hitBound = bounded && (facts.distinct ?? 0) >= bound;
    if (cls === 2) {
      stop = { exit: res.exit, text: errorExcerpt(tree) };
      break;
    }
    const named = cls === 1 ? attribute(facts, open) : null;
    if (named) {
      verdicts.set(named.id, { status: 'broken', evidence: res.stdout });
      queue.unshift(open.filter((r) => r !== named));
      continue;
    }
    if (hitBound && (cls === 0 || facts.broken?.kind === 'temporal')) {
      for (const r of open) verdicts.set(r.id, { status: 'unchecked' });
      cut = true;
      continue;
    }
    if (cls === 0) {
      for (const r of open) verdicts.set(r.id, { status: 'holds' });
      complete = true;
      continue;
    }
    if (facts.broken?.kind === 'temporal') {
      const props = open.filter((r) => r.kind === 'property');
      if (props.length) {
        for (const r of open) if (r.kind !== 'property') verdicts.set(r.id, { status: 'holds' });
        complete = true;
        if (props.length === 1) verdicts.set(props[0].id, { status: 'broken', evidence: res.stdout });
        else for (const p of props) queue.push([p]);
        continue;
      }
    }
    throw new CheckError(`TLC reported a failure (exit status ${res.exit}) but named no rule this command checks:\n${errorExcerpt(tree)}`);
  }
  for (const r of rules) if (!verdicts.has(r.id)) verdicts.set(r.id, { status: 'unchecked' });
  return {
    firstExit, firstStatus: first.res.exit, firstOutput: first.res.stdout,
    verdicts, distinct, initial, complete: complete || firstExploredAll, cut, stop,
  };
}
