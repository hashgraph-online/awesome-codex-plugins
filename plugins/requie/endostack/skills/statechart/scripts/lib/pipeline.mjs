// The whole check, independent of process handling: parse inputs, run TLC
// through an injected runner, build graph and chart, and return the output
// files as { name -> text }.

import fs from 'node:fs';
import path from 'node:path';
import { randomBytes } from 'node:crypto';
import { parseConfig } from './config.mjs';
import { parseSanyXml } from './sany.mjs';
import { checkRules, makeRules, initialOnlyProperties } from './verdicts.mjs';
import { buildFullGraph, buildPathsGraph, findBugs, defaultLabel } from './graph.mjs';
import { applyView } from './view.mjs';
import { buildChart } from './chart.mjs';
import { renderMermaid } from './mermaid.mjs';
import { renderReport, outFileName, CHART_BUDGET } from './report.mjs';
import { renderPlainText, parseMessages, runFacts, errorExcerpt } from './tlc-output.mjs';
import { toView } from './values.mjs';

export class PipelineError extends Error {}

export function drawWrapper(module, name, variables, invariants, tag, budget = CHART_BUDGET) {
  const brokenSet = invariants.length
    ? invariants.map((n) => `(IF ${n} THEN {} ELSE {${JSON.stringify(n)}})`).join(' \\cup ')
    : '{}';
  const tuple = variables.length ? `<<${variables.join(', ')}>>` : '<<>>';
  return {
    name,
    text: [
      `---- MODULE ${name} ----`,
      `EXTENDS ${module}`,
      'LOCAL INSTANCE Naturals',
      `${name}_TLC == INSTANCE TLC`,
      `${name}_Budget == ${name}_TLC!TLCGet("distinct") <= ${budget}`,
      `${name}_Broken == ${brokenSet}`,
      `${name}_Mark == IF ${name}_Broken = {} THEN TRUE ELSE ${name}_TLC!PrintT(<<"${tag}", ${tuple}, ${name}_Broken>>)`,
      '====',
      '',
    ].join('\n'),
  };
}

function drawConfig(config, name) {
  const lines = [];
  if (config.written) lines.push(config.written);
  lines.push(`INVARIANT ${name}_Mark`, `CONSTRAINT ${name}_Budget`, 'CHECK_DEADLOCK FALSE');
  return lines.join('\n');
}

// opts: { specPath, configPath, view (checked view or null), run, tag?, budget? }
export async function runPipeline(opts) {
  const { specPath, configPath, view, run } = opts;
  const budget = opts.budget ?? CHART_BUDGET;
  const tag = opts.tag ?? randomBytes(16).toString('hex');
  const specDir = path.dirname(path.resolve(specPath));
  const config = parseConfig(fs.readFileSync(configPath, 'utf8'), configPath);

  const sanyRes = await run({ name: 'sany', kind: 'sany', spec: path.resolve(specPath) });
  if (sanyRes.exit !== 0) {
    const tail = `${sanyRes.stdout}\n${sanyRes.stderr}`.trim().split('\n').slice(-30).join('\n');
    throw new PipelineError(`SANY could not parse ${specPath} (exit status ${sanyRes.exit}):\n${tail}`);
  }
  const sany = parseSanyXml(sanyRes.stdout);
  const variables = sany.variables;
  const rules = makeRules(config);
  const initialOnly = initialOnlyProperties(rules, config, sany);

  const check = await checkRules({ run, specPath: path.resolve(specPath), specDir, module: sany.module, config, rules });
  const { verdicts } = check;
  const brokenRules = rules.filter((r) => verdicts.get(r.id).status === 'broken');

  let graph = null;
  let mode = 'full';
  let drawExit = null;
  let partial = false;
  if (check.distinct !== null && check.distinct <= budget) {
    const name = `SCDraw_${sany.module}`;
    const brokenInvs = [...new Set(brokenRules.filter((r) => r.kind === 'invariant').map((r) => r.name))];
    const res = await run({
      name: 'draw', kind: 'tlc', spec: path.resolve(specPath), specDir, dump: true,
      wrapper: drawWrapper(sany.module, name, variables, brokenInvs, tag, budget),
      cfgText: drawConfig(config, name),
    });
    if (!res.dot) {
      throw new PipelineError(`The drawing run wrote no state graph (TLC exit status ${res.exit}):\n${errorExcerpt(parseMessages(res.stdout))}`);
    }
    const facts = runFacts(parseMessages(res.stdout));
    if (res.exit !== 0 && facts.initial === null) {
      throw new PipelineError(`The drawing run failed before TLC computed the initial states (exit status ${res.exit}):\n${errorExcerpt(parseMessages(res.stdout))}`);
    }
    if ((facts.distinct ?? 0) > budget) {
      mode = 'paths';
    } else {
      if (res.exit !== 0) { drawExit = res.exit; partial = true; }
      graph = buildFullGraph({
        variables, dotText: res.dot, drawStdout: res.stdout, tag, rules, verdicts, config,
        drawComplete: !partial, partial,
      });
    }
  } else {
    mode = 'paths';
  }
  if (mode === 'paths') graph = buildPathsGraph({ variables, rules, verdicts });

  for (const s of graph.states) if (s.kind === 'excluded') s.label0 = `${s.label0} (excluded step)`;
  const { bugs } = findBugs(graph, rules, verdicts);

  const constrained = config.constraints.length > 0 || config.actionConstraints.length > 0;
  let deadlockCaveat = null;
  if (mode === 'full' && brokenRules.some((r) => r.kind === 'deadlock')) {
    if (partial) deadlockCaveat = 'The drawing run stopped early, so only the deadlock TLC reported is marked; other states without a drawn step may or may not deadlock.';
    else if (constrained) deadlockCaveat = 'The config has a constraint, so only the deadlock TLC reported is marked. A state with no drawn step may have steps the constraint removed, and TLC does not count that as a deadlock.';
  }

  let chart = null;
  let chartText = null;
  if (graph.states.length > 0 && !(mode === 'paths' && brokenRules.length === 0)) {
    const applied = applyView(view, variables, graph.states, graph.edges, toView, (s) => s.label0);
    // A state reached by a step an ACTION_CONSTRAINT excludes stays separate
    // from the same values reached normally, whatever the view calls it.
    if (view?.state) {
      graph.states.forEach((s, i) => {
        if (s.kind !== 'excluded') return;
        for (const [r, p] of applied.labels[i]) applied.labels[i].set(r, [...p.slice(0, -1), `${p[p.length - 1]} (excluded step)`]);
      });
    }
    chart = buildChart({ graph, applied, bugs, rules, verdicts });
    for (const b of bugs) {
      b.labels = b.states.map((s, i) => {
        if (i === 0) return null;
        const ei = graph.edges.findIndex((e) => e.from === b.states[i - 1] && e.to === s && e.action === b.actions[i]);
        return ei < 0 ? b.actions[i] : applied.stepLabels[ei];
      });
      if (b.kind === 'lasso' && !b.stutter) {
        const last = b.states[b.states.length - 1];
        const ei = graph.edges.findIndex((e) => e.from === last && e.to === b.states[b.loopIndex] && e.action === b.loopAction);
        b.loopLabel = ei < 0 ? b.loopAction : applied.stepLabels[ei];
      }
    }
    const ruleName = (id) => rules.find((r) => r.id === id).display;
    chartText = renderMermaid(chart, { title: view?.title ?? null, colors: view?.colors ?? new Map(), ruleName });
  } else {
    for (const b of bugs) b.labels = b.actions;
  }

  const describe = chart ? chart.describe : (idx) => graph.states[idx].label0;
  const exactCount = mode === 'paths' && check.complete && check.distinct > budget ? check.distinct : null;
  const report = renderReport({
    module: sany.module, rules, verdicts, mode, graph, chart, bugs, describe, config,
    drawExit, initialCount: check.initial, deadlockCaveat, exactCount,
    cut: check.cut, stop: check.stop, initialOnly,
  });

  const files = new Map();
  files.set('report.md', report);
  if (chartText) files.set('chart.mmd', chartText);
  files.set('tlc.out', renderPlainText(check.firstOutput));
  const drawnPaths = new Set(bugs.filter((b) => b.kind === 'path').map((b) => b.ruleId));
  for (const r of brokenRules) {
    if (r.kind !== 'property' && drawnPaths.has(r.id) && chart) continue;
    files.set(outFileName(r), renderPlainText(verdicts.get(r.id).evidence));
  }
  return { exit: check.firstExit, files, report };
}
