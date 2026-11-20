#!/usr/bin/env node
// Deterministic contract checks for Boss artifacts in `.boss/<feature>/`.
//
// These cover only the requirements a script can decide. Everything that needs judgement
// (is the acceptance scenario testable, does the design trace to the PRD) belongs to the
// verifier agent in `agents/boss-verifier.md`.
//
// Usage: node check-artifacts.mjs <feature-dir> [--require a.md,b.md] [--only a.md,b.md] [--json]
// Exit codes: 0 all checks passed, 1 at least one check failed, 2 usage error.

import fs from 'node:fs';
import path from 'node:path';

const SUMMARY_HEADING = /^##\s+(摘要|Summary)\s*$/i;
const TEMPLATE_TOKEN = /\{\{[^}\n]+\}\}/;

/** Drop fenced blocks and inline code, so quoted examples do not count as prose. */
function prose(text) {
  return text.replace(/^(```|~~~)[\s\S]*?^\1.*$/gm, '').replace(/`[^`\n]*`/g, '');
}

function firstSectionIsSummary(text) {
  const headings = prose(text)
    .split('\n')
    .filter((line) => /^##\s+/.test(line));
  return headings.length > 0 && SUMMARY_HEADING.test(headings[0]);
}

function placeholders(words) {
  const pattern = new RegExp(
    words.map((word) => (/^\w+$/.test(word) ? `\\b${word}\\b` : word)).join('|'),
  );
  return (text) => {
    const body = prose(text);
    const hit = body.match(pattern) ?? body.match(TEMPLATE_TOKEN);
    return hit ? `found "${hit[0]}"` : null;
  };
}

function givenWhenThen(text) {
  const body = prose(text);
  const english = /\bgiven\b[\s\S]{0,400}?\bwhen\b[\s\S]{0,400}?\bthen\b/i.test(body);
  const chinese = /(假设|给定|假如|前置)[\s\S]{0,400}?当[\s\S]{0,400}?(那么|则)/.test(body);
  return english || chinese ? null : 'no Given-When-Then acceptance scenario';
}

function singleVerdict(labels, options) {
  return (text) => {
    const line = prose(text)
      .split('\n')
      .find((candidate) => labels.test(candidate));
    if (!line) return 'no verdict line';
    const chosen = options.filter((option) => option.test(line));
    if (chosen.length === 0) return 'the verdict line does not state a verdict';
    return chosen.length > 1 ? 'the verdict line still lists more than one option' : null;
  };
}

const summaryFirst = {
  rule: 'summary-first',
  test: (text) =>
    firstSectionIsSummary(text) ? null : 'the first "## " section is not "Summary" or "摘要"',
};
const noPlaceholders = (words) => ({ rule: 'no-placeholders', test: placeholders(words) });
const matches = (rule, pattern, reason) => ({
  rule,
  test: (text) => (pattern.test(prose(text)) ? null : reason),
});

const REVIEW_VERDICT = singleVerdict(
  /结论|是否通过|总体评价|verdict|decision|conclusion|outcome/i,
  [
    /有条件通过|approved? with conditions|conditionally approved/i,
    /(?<!有条件|不)通过(?!率)|\bapproved?\b(?! with conditions)(?<!conditionally approved)/i,
    /不通过|需要?修改|(needs|requests?|requested|requires?|required) changes|changes (required|requested|needed)|rejected/i,
  ],
);

/** Rules per artifact. Each test returns null on pass, or the reason it failed. */
export const CONTRACTS = {
  'prd.md': [
    summaryFirst,
    noPlaceholders(['TBD', '待确认', '待补充']),
    { rule: 'given-when-then', test: givenWhenThen },
    matches(
      'out-of-scope',
      /^#{2,4}\s+.*(不做什么|不做|非目标|范围外|不在范围|out[- ]of[- ]scope|not in scope|non[- ]goals|not doing|won[’']t do|exclu(sions|ded))/im,
      'no "Out of scope" / "不做什么" section',
    ),
    matches('priorities', /\bP[0-2]\b/, 'no P0/P1/P2 priority'),
  ],
  'architecture.md': [
    summaryFirst,
    noPlaceholders(['TBD', '待定']),
    matches(
      'alternatives-compared',
      /对比|比较|候选|备选|alternativ|compar|trade-?off|versus|\bvs\.?\b/i,
      'no comparison of candidate options',
    ),
  ],
  'ui-spec.md': [summaryFirst, noPlaceholders(['TBD'])],
  'tech-review.md': [
    summaryFirst,
    noPlaceholders(['TBD']),
    { rule: 'single-verdict', test: REVIEW_VERDICT },
  ],
  'code-review.md': [
    summaryFirst,
    noPlaceholders(['TBD']),
    { rule: 'single-verdict', test: REVIEW_VERDICT },
    {
      // Tested on the raw text: `path:line` references are usually written as inline code.
      rule: 'findings-cite-lines',
      test: (text) =>
        /[\w./-]+\.\w+:\d+|无发现|no findings/i.test(text)
          ? null
          : 'no finding cites file:line, and the review does not say "No findings"',
    },
  ],
  'plan.md': [
    summaryFirst,
    noPlaceholders(['TBD']),
    matches('milestones', /里程碑|milestone/i, 'no milestones'),
  ],
  'tasks.md': [
    summaryFirst,
    noPlaceholders(['TBD']),
    matches('task-ids', /\bT-\d+\b/, 'no task with a T-<n> id'),
    {
      rule: 'tasks-have-acceptance',
      test: (text) => {
        const blocks = prose(text)
          .split(/^###\s+/m)
          .slice(1)
          .filter((block) => /^.*\bT-\d+\b/.test(block.split('\n')[0]));
        const missing = blocks.filter((block) => !/验收|acceptance|done when/i.test(block));
        return missing.length === 0
          ? null
          : `${missing.length} task(s) have no acceptance criteria`;
      },
    },
  ],
  'qa-report.md': [
    summaryFirst,
    noPlaceholders(['TBD']),
    matches(
      'exit-code',
      /(退出码|exit code)[\s\S]{0,200}?\b\d+\b/i,
      'no command result with an observed exit code',
    ),
    matches(
      'result-counts',
      /\b\d+\s*\/\s*\d+\s*\/\s*\d+\b|\b\d+\s+(passed|failed|skipped)\b|(通过|失败|跳过)\D{0,6}\d+/i,
      'no passed/failed/skipped counts',
    ),
    {
      rule: 'no-speculation',
      test: (text) => {
        const hit = prose(text).match(/应该能通过|预期通过|should pass|expected to pass/i);
        return hit ? `speculative claim "${hit[0]}" instead of an observed result` : null;
      },
    },
  ],
  'deploy-report.md': [
    summaryFirst,
    noPlaceholders(['TBD']),
    matches(
      'outcome',
      /https?:\/\/\S+|未部署|not deployed/i,
      'neither a URL nor an explicit "Not deployed"',
    ),
  ],
};

export function checkArtifact(file, text) {
  return (CONTRACTS[file] ?? []).map(({ rule, test }) => {
    const reason = test(text);
    return { file, rule, ok: reason === null, reason: reason ?? '' };
  });
}

export function checkFeature(dir, { require = [], only = [] } = {}) {
  const results = [];
  const names = only.length > 0 ? only : Object.keys(CONTRACTS);
  for (const file of new Set([...require, ...names])) {
    const full = path.join(dir, file);
    if (!fs.existsSync(full)) {
      if (require.includes(file)) {
        results.push({ file, rule: 'exists', ok: false, reason: 'the stage did not produce it' });
      }
      continue;
    }
    const text = fs.readFileSync(full, 'utf8');
    results.push({
      file,
      rule: 'exists',
      ok: text.trim().length > 0,
      reason: text.trim() ? '' : 'the file is empty',
    });
    results.push(...checkArtifact(file, text));
  }
  return results;
}

function list(value) {
  return (value ?? '')
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);
}

function main(argv) {
  const args = [...argv];
  const json = args.includes('--json');
  const option = (name) => {
    const index = args.indexOf(name);
    return index === -1 ? undefined : args[index + 1];
  };
  const dir = args.find(
    (arg, index) => !arg.startsWith('--') && !/^--(require|only)$/.test(args[index - 1] ?? ''),
  );

  if (!dir || !fs.existsSync(dir) || !fs.statSync(dir).isDirectory()) {
    console.error(
      'Usage: node check-artifacts.mjs <feature-dir> [--require a.md,b.md] [--only a.md,b.md] [--json]',
    );
    if (dir) console.error(`Not a directory: ${dir}`);
    return 2;
  }

  const results = checkFeature(dir, {
    require: list(option('--require')),
    only: list(option('--only')),
  });
  const ok = results.every((result) => result.ok);
  if (json) {
    console.log(JSON.stringify({ ok, results }, null, 2));
  } else {
    for (const result of results) {
      const detail = result.ok ? '' : ` — ${result.reason}`;
      console.log(`${result.ok ? 'PASS' : 'FAIL'} ${result.file} ${result.rule}${detail}`);
    }
    if (results.length === 0) console.log('No Boss artifacts found to check.');
  }
  return ok ? 0 : 1;
}

if (
  process.argv[1] &&
  path.resolve(process.argv[1]) === path.resolve(new URL(import.meta.url).pathname)
) {
  process.exitCode = main(process.argv.slice(2));
}
