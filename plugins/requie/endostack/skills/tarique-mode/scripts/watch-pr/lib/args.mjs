// Command-line parsing for watch-pr. Returns a plain options object or
// throws UsageError; the caller maps that to exit 64.

import { parseArgs } from 'node:util';
import { UsageError } from './errors.mjs';

export const HELP = `watch-pr: wait on a GitHub pull request, a stack, or a merge queue, and exit with a code that names the outcome.

usage: watch-pr [options]

selection
  --owner <owner>            repository owner (default: from origin remote or gh)
  --repo <repo>              repository name (default: from origin remote or gh)
  --pr <n>                   PR number, '#12' accepted (default: current branch's PR)
  --stack                    watch the open stack connected to the PR
  --queued-stack             watch a captured stack until every PR merges
  --stack-prs <n,...>        PR numbers for --queued-stack, lowest first; fixed for the run

timing
  --interval <s>             seconds between polls, > 0 (default 60)
  --sweep-interval <s>       seconds between whole-stack reads in queued mode (default 300)
  --timeout <s>              overall deadline in seconds, 0 = none (default 0)
  --max-query-errors <n>     consecutive read failures before giving up (default 5)

behavior
  --status-only              print one STATUS snapshot and exit 0
  --allow-draft              do not treat draft as a merge gate
  --review-bot <login>       account whose threads count as review-bot threads (repeatable)
  --approval-check <name>    check that waits on a human approval; reported as a gate (repeatable)
  --config <file>            JSON config (default: .endostack/watch-pr.json if present)
  --pretty                   human-readable text instead of JSON lines
  -h, --help                 show this help

exit codes
  0 ready, complete, or status-only   2 merge conflicts      3 unresolved review threads
  4 failing checks                    5 timeout              6 merge gate
  7 GitHub could not be read          64 usage error
`;

const OPTIONS = {
  owner: { type: 'string' },
  repo: { type: 'string' },
  pr: { type: 'string' },
  stack: { type: 'boolean' },
  'queued-stack': { type: 'boolean' },
  'stack-prs': { type: 'string' },
  interval: { type: 'string' },
  'sweep-interval': { type: 'string' },
  timeout: { type: 'string' },
  'max-query-errors': { type: 'string' },
  'status-only': { type: 'boolean' },
  'allow-draft': { type: 'boolean' },
  'review-bot': { type: 'string', multiple: true },
  'approval-check': { type: 'string', multiple: true },
  config: { type: 'string' },
  pretty: { type: 'boolean' },
  help: { type: 'boolean', short: 'h' },
};

export function parsePrNumber(raw, label = '--pr') {
  const text = String(raw).trim().replace(/^#\s*/, '');
  if (!/^[1-9][0-9]*$/.test(text)) throw new UsageError(`${label} expects a positive PR number, got '${raw}'`);
  const n = Number(text);
  if (!Number.isSafeInteger(n)) throw new UsageError(`${label} is out of range: '${raw}'`);
  return n;
}

function parseSeconds(raw, flag, { allowZero }) {
  const text = String(raw).trim();
  if (!/^(?:\d+(?:\.\d*)?|\.\d+)$/.test(text)) throw new UsageError(`${flag} expects a number of seconds, got '${raw}'`);
  const n = Number(text);
  if (!Number.isFinite(n) || (allowZero ? n < 0 : n <= 0)) {
    throw new UsageError(`${flag} must be ${allowZero ? '>= 0' : '> 0'}, got '${raw}'`);
  }
  return n;
}

function parsePositiveInt(raw, flag) {
  const text = String(raw).trim();
  if (!/^[1-9][0-9]*$/.test(text) || !Number.isSafeInteger(Number(text))) {
    throw new UsageError(`${flag} expects a positive integer, got '${raw}'`);
  }
  return Number(text);
}

export function parseStackList(raw) {
  const parts = String(raw).split(',').map((p) => p.trim());
  if (parts.length === 0 || parts.every((p) => p === '')) throw new UsageError('--stack-prs is empty');
  const out = [];
  for (const part of parts) {
    if (part === '') throw new UsageError('--stack-prs has an empty entry');
    const n = parsePrNumber(part, '--stack-prs');
    if (out.includes(n)) throw new UsageError(`--stack-prs lists #${n} twice`);
    out.push(n);
  }
  return out;
}

export function parseCli(argv) {
  let parsed;
  try {
    parsed = parseArgs({ args: argv, options: OPTIONS, allowPositionals: false, strict: true });
  } catch (err) {
    throw new UsageError(err.message.replace(/\. To specify a positional.*$/s, ''));
  }
  const v = parsed.values;
  if (v.help) return { help: true };

  if (v.stack && v['queued-stack']) throw new UsageError('--stack and --queued-stack cannot be combined');
  if (v['stack-prs'] !== undefined && !v['queued-stack']) throw new UsageError('--stack-prs requires --queued-stack');
  for (const key of ['owner', 'repo']) {
    if (v[key] !== undefined && !/^[A-Za-z0-9_.-]+$/.test(v[key])) throw new UsageError(`--${key} has invalid characters: '${v[key]}'`);
  }
  for (const key of ['review-bot', 'approval-check', 'config']) {
    for (const item of [v[key]].flat()) {
      if (item !== undefined && item.trim() === '') throw new UsageError(`--${key} must not be empty`);
    }
  }

  const opts = {
    help: false,
    owner: v.owner ?? null,
    repo: v.repo ?? null,
    pr: v.pr !== undefined ? parsePrNumber(v.pr) : null,
    mode: v['queued-stack'] ? 'queued' : v.stack ? 'stack' : 'single',
    stackPrs: v['stack-prs'] !== undefined ? parseStackList(v['stack-prs']) : null,
    interval: v.interval !== undefined ? parseSeconds(v.interval, '--interval', { allowZero: false }) : 60,
    sweepInterval: v['sweep-interval'] !== undefined ? parseSeconds(v['sweep-interval'], '--sweep-interval', { allowZero: false }) : 300,
    timeout: v.timeout !== undefined ? parseSeconds(v.timeout, '--timeout', { allowZero: true }) : 0,
    maxQueryErrors: v['max-query-errors'] !== undefined ? parsePositiveInt(v['max-query-errors'], '--max-query-errors') : 5,
    statusOnly: Boolean(v['status-only']),
    allowDraft: Boolean(v['allow-draft']),
    reviewBots: (v['review-bot'] ?? []).map((s) => s.trim()),
    approvalChecks: (v['approval-check'] ?? []).map((s) => s.trim()),
    configPath: v.config ?? null,
    pretty: Boolean(v.pretty),
  };
  return opts;
}
