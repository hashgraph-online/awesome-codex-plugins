// Writes report.md: size, notes, one section per bug with its numbered path
// in the chart's own words, then the rules that hold or were not checked.

export const CHART_BUDGET = 500;

function plural(n, one, many = `${one}s`) {
  return `${n} ${n === 1 ? one : many}`;
}

function fence(text) {
  const longest = Math.max(2, ...[...text.matchAll(/`+/g)].map((m) => m[0].length));
  const f = '`'.repeat(longest + 1);
  return `${f}\n${text.replace(/\n+$/, '')}\n${f}`;
}

export function outFileName(rule) {
  return `tlc-${rule.display.replace(/[^A-Za-z0-9_.-]/g, '_')}.out`;
}

// r: everything the pipeline learned. See pipeline.mjs for the fields.
export function renderReport(r) {
  const out = [];
  const ruleById = new Map(r.rules.map((x) => [x.id, x]));
  out.push(`# ${r.module}`, '');

  // Size line.
  if (r.mode === 'full') {
    let s = `TLC reached ${plural(r.graph.stateCount, 'state')} and ${plural(r.graph.stepCount, 'step')}.`;
    s += r.chart ? ` The chart draws ${plural(r.chart.stateCount, 'state')} and ${plural(r.chart.arrowCount, 'arrow')}.` : '';
    out.push(s);
  } else {
    const count = r.exactCount !== null ? `${r.exactCount.toLocaleString('en-US')} distinct states` : `more than ${CHART_BUDGET} distinct states`;
    let s = `TLC reached ${count}, over the chart budget of ${CHART_BUDGET}.`;
    if (r.chart) s += ` The chart draws only the paths to broken rules: ${plural(r.chart.stateCount, 'state')} and ${plural(r.chart.arrowCount, 'arrow')}.`;
    else s += ' Nothing broke, so no chart was written.';
    out.push(s);
  }
  out.push('');

  // Notes.
  const notes = [];
  if (r.drawExit !== null && r.drawExit !== undefined && r.drawExit !== 0) {
    notes.push(`The drawing run stopped early with TLC exit status ${r.drawExit}, so the chart shows only the part of the state graph TLC reached before it stopped.`);
  }
  if (r.initialCount === 0) notes.push('No state satisfies Init, or every initial state is outside the constraints, so TLC explored nothing.');
  if (r.graph) {
    const past = r.graph.states.filter((s) => s.kind === 'past').length;
    const excl = r.graph.states.filter((s) => s.kind === 'excluded').length;
    if (past) notes.push(`${plural(past, 'state')} beyond a CONSTRAINT ${past === 1 ? 'ends' : 'end'} a rule's path, and the chart includes ${past === 1 ? 'it' : 'them'}. TLC checks rules in such states but explores no further from them.`);
    if (excl) notes.push(`${plural(excl, 'step')} that an ACTION_CONSTRAINT excludes ${excl === 1 ? 'ends' : 'end'} a rule's path, and the chart includes ${excl === 1 ? 'it' : 'them'} as separate states. TLC checks rules after such steps but explores no further.`);
  }
  if (r.chart) {
    if (r.chart.notes.inside) notes.push(`${plural(r.chart.notes.inside, 'step')} ${r.chart.notes.inside === 1 ? 'stays' : 'stay'} inside one chart state and ${r.chart.notes.inside === 1 ? 'is' : 'are'} not drawn.`);
    if (r.chart.notes.hidden) notes.push(`The view hides ${plural(r.chart.notes.hidden, 'step')}.`);
  }
  if (r.deadlockCaveat) notes.push(r.deadlockCaveat);
  if (r.chart?.notes.regionsReason) notes.push(`${r.chart.notes.regionsReason} The chart draws parent states named after the regions instead of parallel regions.`);
  for (const sn of r.chart?.notes.stepNotes ?? []) {
    if (sn.alone) notes.push(`The step "${sn.label}" sometimes changes ${sn.together.join('; ')} at the same time, and sometimes changes only one region.`);
    else notes.push(`The step "${sn.label}" changes ${sn.together.join('; ')} at the same time.`);
  }
  if (r.config.hasView || r.config.hasSymmetry) {
    notes.push(`The config uses ${[r.config.hasView && 'VIEW', r.config.hasSymmetry && 'SYMMETRY'].filter(Boolean).join(' and ')}, so TLC treats equivalent states as one; an arrow may point at TLC's representative state instead of the exact state the step reaches.`);
  }
  for (const n of notes) out.push(n, '');

  // Bug sections.
  const drawn = new Set();
  for (const b of r.bugs) {
    const rule = ruleById.get(b.ruleId);
    drawn.add(rule.id);
    out.push(`## ${rule.display} breaks`, '');
    if (b.kind === 'path') {
      out.push(`The shortest path to a state that breaks ${rule.display} takes ${plural(b.states.length - 1, 'step')}.`, '');
    } else {
      out.push(`TLC's counterexample for ${rule.display} is in \`${outFileName(rule)}\`. It takes ${plural(b.states.length - 1, 'step')} before it repeats forever.`, '');
    }
    b.states.forEach((s, i) => {
      const label = i === 0 ? null : b.labels[i];
      out.push(`${i}. ${label ? `${label} → ` : ''}${r.describe(s)}`);
    });
    out.push('');
    if (b.kind === 'lasso') {
      const loop = b.states.slice(b.loopIndex);
      const uniq = [];
      for (const s of loop) if (!uniq.includes(s)) uniq.push(s);
      if (b.stutter) out.push(`From step ${b.states.length - 1} the run stops in ${r.describe(b.states[b.states.length - 1])} forever, so ${rule.display} never holds.`);
      else if (uniq.length === 1) out.push(`From step ${b.loopIndex} the run stays in ${r.describe(uniq[0])} forever.`);
      else out.push(`From step ${b.loopIndex} the run loops through steps ${b.loopIndex} to ${b.states.length - 1} forever, returning to step ${b.loopIndex} by ${b.loopLabel ?? 'a step'}.`);
      out.push('');
    }
  }
  for (const rule of r.rules) {
    if (r.verdicts.get(rule.id).status !== 'broken' || drawn.has(rule.id)) continue;
    out.push(`## ${rule.display} breaks`, '', `TLC found a counterexample for ${rule.display} that the chart does not show as a path. It is in \`${outFileName(rule)}\`.`, '');
  }

  // Holds / not checked.
  const holds = r.rules.filter((x) => r.verdicts.get(x.id).status === 'holds');
  const unchecked = r.rules.filter((x) => r.verdicts.get(x.id).status === 'unchecked');
  if (unchecked.length) {
    out.push('## Rules not checked', '', unchecked.map((x) => x.display).join(', '), '');
    if (r.stop) {
      out.push(`A later TLC run stopped with exit status ${r.stop.exit} before it reached these rules, so each may hold or break. TLC printed:`, '', fence(r.stop.text), '');
    } else if (r.cut) {
      out.push(`After the first break, each rerun stops at ${(100000).toLocaleString('en-US')} distinct states, and a run hit that bound before it explored everything. These rules may hold or break. To check them, remove the rules that break from the config or shrink the model.`, '');
    }
  }
  if (holds.length) {
    out.push('## Rules that hold', '', holds.map((x) => x.display).join(', '), '');
    for (const x of holds) {
      if (r.initialOnly.has(x.id)) {
        out.push(`TLC checked ${x.display} only in initial states, because it is listed under PROPERTY and has no temporal operator. List it under INVARIANT to check it in every state.`, '');
      }
    }
  }
  return `${out.join('\n').replace(/\n+$/, '')}\n`;
}
