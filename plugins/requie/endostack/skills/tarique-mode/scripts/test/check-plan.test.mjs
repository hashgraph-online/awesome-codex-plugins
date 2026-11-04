import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as cp from 'node:child_process';
import * as url from 'node:url';
import * as path from 'node:path';
import * as os from 'node:os';
import * as fs from 'node:fs';
import { checkPlan, stripCodeSpans, RULE } from '../check-plan.mjs';

const testDir = path.dirname(url.fileURLToPath(import.meta.url));
const checker = path.join(testDir, '..', 'check-plan.mjs');
const formatDoc = fs.readFileSync(path.join(testDir, '..', 'PLAN-FORMAT.md'), 'utf8');

// The known-good plan is the example inside PLAN-FORMAT.md, so the doc and the checker cannot drift apart.
const VALID = (() => {
  const m = /^~~~~markdown\n([\s\S]*?)\n~~~~$/m.exec(formatDoc);
  assert.ok(m, 'PLAN-FORMAT.md must embed the example plan in a ~~~~markdown fence');
  return m[1] + '\n';
})();

const problems = (src) => checkPlan(src).problems;
const messages = (src) => problems(src).map((p) => p.message);
const withTail = (extra) => VALID + extra;
const replace = (from, to) => {
  assert.ok(VALID.includes(from), `fixture missing: ${from}`);
  return VALID.replace(from, to);
};
const has = (src, msg) => messages(src).some((m) => m.includes(msg));

// Write `source` to a scratch plan.md, run the checker on it, and clean up afterwards.
function runOnFile(source) {
  const scratch = fs.mkdtempSync(path.join(os.tmpdir(), 'check-plan-'));
  try {
    const file = path.join(scratch, 'plan.md');
    fs.writeFileSync(file, source);
    return cp.spawnSync(process.execPath, [checker, file], { encoding: 'utf8' });
  } finally {
    fs.rmSync(scratch, { recursive: true, force: true });
  }
}

const runWithArgs = (args) => cp.spawnSync(process.execPath, [checker, ...args], { encoding: 'utf8' });

// ---------- CLI ----------

test('the embedded example plan is accepted and summarized per PR', () => {
  const r = runOnFile(VALID);
  assert.equal(r.status, 0, r.stderr);
  assert.match(r.stdout, /Add the export endpoint \(PR-1\)\tboxes=19 needs=0 touches=1 changes=1 result=1 unit=1 live=10 perf=4 review=0 land=1/);
  assert.match(r.stdout, /checked 1 PR sections; found 0 problems/);
  assert.equal(r.stderr, '');
});

test('a faulty plan exits 1 with FILE:LINE findings on stderr', () => {
  const r = runOnFile(withTail('\nA note—with a dash.\n'));
  assert.equal(r.status, 1);
  const lineNo = VALID.split('\n').length + 1;
  assert.match(r.stderr, new RegExp(`plan\\.md:${lineNo}: long dash`));
  assert.match(r.stdout, /found 1 problems/);
});

test('running without a plan path prints the expected usage and exits 2', () => {
  const r = runWithArgs([]);
  assert.ok(r.stderr.includes('expects exactly one argument'), r.stderr);
  assert.strictEqual(r.status, 2);
});

test('a plan path that cannot be read exits 2', () => {
  const r = runWithArgs([path.join(os.tmpdir(), 'nope-does-not-exist.md')]);
  assert.strictEqual(r.status, 2);
});

test('Windows line endings parse cleanly', () => {
  assert.deepEqual(problems(VALID.replace(/\n/g, '\r\n')), []);
});

// ---------- fences ----------

test('fences with up to three leading spaces and longer closers mask headings', () => {
  for (const indent of ['', ' ', '  ', '   ']) {
    const src = withTail(`\n${indent}\`\`\`js\n## Not a section\n${indent}\`\`\`\`\`\n`);
    assert.deepEqual(messages(src), [], `indent ${JSON.stringify(indent)}`);
  }
});

test('a four-space indent does not open a fence, so its heading-like line counts as prose', () => {
  const src = withTail('\n    ```\nnote: here\n    ```\n');
  assert.ok(has(src, 'mid-sentence colon'));
});

test('nested backtick fences and tilde fences carrying backticks in the info string parse', () => {
  const nested = withTail('\n````md\n```js\n## Inner\n```\n````\n');
  assert.deepEqual(messages(nested), []);
  const tilde = withTail('\n~~~ info `x`\n## Inner\n~~~\n');
  assert.deepEqual(messages(tilde), []);
});

test('a closer that is shorter, mismatched, or has an info string leaves the fence open', () => {
  for (const closer of ['~~~', '``', '```js']) {
    const src = withTail(`\n\`\`\`\nnote: inside\n${closer}\n## Still inside\n`);
    assert.deepEqual(messages(src), [], `closer ${closer}`);
  }
});

test('trailing spaces or a tab after the closer still close the fence', () => {
  for (const trail of ['   ', '\t']) {
    const src = withTail(`\n\`\`\`\nnote: inside\n\`\`\`${trail}\n## Extra\n`);
    assert.ok(has(src, 'not an appendix'), `trail ${JSON.stringify(trail)}`);
    assert.ok(!has(src, 'mid-sentence colon'));
  }
});

test('a colon in prose after a fence is flagged but one inside the fence is not', () => {
  const src = withTail('\n```\na: b\n```\nafter: this\n');
  const ps = problems(src).filter((p) => p.message === 'mid-sentence colon');
  assert.equal(ps.length, 1);
  assert.equal(ps[0].line, VALID.split('\n').length + 4);
});

test('a backtick info string containing a backtick does not start a fence', () => {
  const src = withTail('\n```a`b\n## Inside\n```\n');
  assert.ok(has(src, 'not an appendix'));
});

test('YAML front matter is ignored', () => {
  assert.ok(VALID.startsWith('---\n'));
  assert.deepEqual(problems(replace('status: draft', 'status: draft: really')), []);
});

// ---------- prose ----------

test('dashes, smart quotes, and colons inside multi-backtick code spans are ignored', () => {
  for (const tick of ['``', '```', '````']) {
    const src = withTail(`\nUse ${tick}a: b – “x”${tick} here.\n`);
    assert.deepEqual(messages(src), [], `ticks ${tick.length}`);
  }
});

test('text following a multi-backtick span is still linted', () => {
  const src = withTail('\nUse ``a: b`` then: this.\n');
  assert.ok(has(src, 'mid-sentence colon'));
});

test('a lone backtick run does not mask the remainder of the line', () => {
  const src = withTail('\nStray ``` then a dash — here.\n');
  assert.ok(has(src, 'long dash'));
  assert.equal(stripCodeSpans('a ``x` b'), 'a ``x` b');
});

test('smart quotes are flagged while link targets and images are skipped', () => {
  assert.ok(has(withTail('\nIt’s here.\n'), 'curly quote'));
  assert.deepEqual(messages(withTail('\nSee [docs](https://x.y/a:b) and ![img](c:d.png).\n')), []);
});

test('a trailing colon at the end of a line is permitted', () => {
  assert.deepEqual(messages(withTail('\nRun these:\n')), []);
});

// ---------- structure ----------

test('a plan without an H1 is flagged', () => {
  assert.ok(has(replace('# Ship CSV', 'Ship CSV'), 'missing H1'));
});

test('an intro running ten or more non-blank lines is flagged', () => {
  const lines = Array.from({ length: 9 }, (_, i) => `Line ${i}.`).join('\n');
  assert.ok(has(replace('## Reading this plan', `${lines}\n\n## Reading this plan`), 'keep it under 10'));
});

test('the reading section must carry its phrases, a playbook path, and the rule', () => {
  assert.ok(has(replace('Each box is a single task.', 'Boxes are work.'), 'each box is a single task'));
  assert.ok(has(replace('The execution playbook is `playbooks/autopilot-stack.md`.', 'Execute it.'), 'point to a playbook'));
  const noRule = VALID.replace(`\n${RULE}\n\n## Run checklist`, '\n\n## Run checklist');
  assert.ok(has(noRule, 'reading section must contain the proof rule'));
});

test('run checklist subheadings must appear in order with their markers', () => {
  assert.ok(has(replace('### Assign owners', '### Owners'), 'exactly these H3s'));
  const swapped = VALID.replace('### Branch and PR rules', '### TMP').replace('### Verification and landing', '### Branch and PR rules').replace('### TMP', '### Verification and landing');
  assert.ok(has(swapped, 'exactly these H3s'));
  assert.ok(has(replace('`git show origin/main:', '`git show main:'), 'git show origin/main:'));
  assert.ok(has(replace('hourly audit loop', 'loop'), 'hourly audit loop'));
  assert.ok(has(replace('Send a status message', 'Send a note'), 'status message'));
});

test('the closing section and the experiment appendix must exist', () => {
  assert.ok(has(replace('## Finish the run', '## Wrap up'), 'missing "## Finish the run"'));
  assert.ok(has(replace('Appendix A. Experiment results', 'Appendix A. Spikes'), 'Experiment results'));
});

test('a plan lacking any PR section is flagged', () => {
  const start = VALID.indexOf('## Add the export endpoint');
  const end = VALID.indexOf('## Finish the run');
  assert.ok(has(VALID.slice(0, start) + VALID.slice(end), 'no PR sections'));
});

// ---------- PR sections ----------

test('misordered or absent labels are flagged', () => {
  assert.ok(has(replace('**Observable result.**', '**Results.**'), 'nine bold labels'));
  const swapped = VALID.replace('**Touches.**', '**TMP.**').replace('**Changes.**', '**Touches.**').replace('**TMP.**', '**Changes.**');
  assert.ok(has(swapped, 'nine bold labels'));
});

test('a blank Needs. line and absent required boxes are flagged', () => {
  assert.ok(has(replace('**Needs.** none', '**Needs.**'), 'Needs. requires'));
  assert.ok(has(replace('- [ ] Add `exportCsv` in `server/reports.ts`.', 'Add it.'), 'Changes. needs at least one checkbox'));
});

test('each proof block must begin with the rule sentence', () => {
  assert.ok(has(replace(`**Perf proof.** ${RULE}`, '**Perf proof.** Measure it.'), 'Perf proof. must open'));
});

test('live proof requires the ten-lanes line naming a real model', () => {
  assert.ok(has(replace('Ten lanes run on `fast` against the PR head.', ''), 'Ten lanes run on'));
  assert.ok(has(replace('Ten lanes run on `fast`', 'Ten lanes run on `<model>`'), 'placeholder model'));
});

test('live proof requires exactly ten numbered lanes, each with a screenshot and a predicate', () => {
  const nine = VALID.replace(/- \[ \] Lane 10\..*\n/, '');
  assert.ok(has(nine, 'exactly 10 lanes, found 9'));
  assert.ok(has(replace('Save `lane4.png`. ', ''), 'Lane 4 must name a screenshot'));
  assert.ok(has(replace('Pass when cells are quoted.', 'Cells are quoted.'), 'Lane 4 must state a pass predicate'));
  assert.ok(has(replace('- [ ] Lane 3.', '- [ ] Lane 7.'), 'expected Lane 3'));
  assert.ok(has(replace('- [ ] Lane 10.', '- [ ] Extra box.\n- [ ] Lane 10.'), 'lane boxes only'));
});

test('perf proof requires four boxes in the fixed order', () => {
  assert.ok(has(replace('- [ ] Budget. Fail', '- [ ] Threshold. Fail'), 'box 4 must start with "Budget."'));
  assert.ok(has(replace('- [ ] Budget. Fail if', '- [ ] Budget. a\n- [ ] Budget. Fail if'), 'exactly 4 boxes, found 5'));
});

test('a None. operator review allows no boxes, otherwise boxes and the three words are required', () => {
  assert.ok(has(replace('No interaction changes in this PR.', 'No interaction changes in this PR.\n- [ ] Stray.'), 'says "None." but has checkboxes'));
  const gated = replace(
    '**Operator review.** None. No interaction changes in this PR.',
    '**Operator review.** The operator signs off on this PR.\n- [ ] Post the screenshot and video in chat and wait for the operator.',
  );
  assert.deepEqual(messages(gated), []);
  const missingVideo = replace(
    '**Operator review.** None. No interaction changes in this PR.',
    '**Operator review.** The operator signs off on this PR.\n- [ ] Post the screenshot and wait for the operator.',
  );
  assert.ok(has(missingVideo, 'must mention video'));
});

test('a second PR section gets its own summary line', () => {
  const start = VALID.indexOf('## Add the export endpoint');
  const end = VALID.indexOf('## Finish the run');
  const pr2 = VALID.slice(start, end).replace('Add the export endpoint (PR-1)', 'Add the export button (PR-2)').replace('**Needs.** none', '**Needs.** PR-1');
  const { summaries, problems: ps } = checkPlan(VALID.slice(0, end) + pr2 + VALID.slice(end));
  assert.deepEqual(ps, []);
  assert.deepEqual(summaries.map((s) => s.title), ['Add the export endpoint (PR-1)', 'Add the export button (PR-2)']);
});
