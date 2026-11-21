// Command-line front end for the store. main(argv, deps) returns the exit
// code; deps lets tests supply env, cwd, and output sinks.

import { parseArgs } from 'node:util';
import path from 'node:path';
import { Store, VERDICTS, NO_VERDICT, UNIT_COLUMNS, INBOX_COLUMNS, formatCounts } from './store.mjs';
import { UserError, UsageError, NotFound } from './errors.mjs';
import { commandRunner, frontierLine } from './frontier.mjs';
import { parsePr } from './files.mjs';

const GLOBAL = ['store', 'json', 'force', 'help'];
const OPTION_TYPES = {
  store: 'string', json: 'boolean', force: 'boolean', help: 'boolean',
  track: 'string', brief: 'string', stage: 'string', branch: 'string', pr: 'string', head: 'string',
  evidence: 'string', verifier: 'string', report: 'string', peek: 'boolean',
  question: 'string', options: 'string', default: 'string', answer: 'string',
  repo: 'string', prs: 'string',
};

// name -> { args: positional names, opts: allowed options, required: required options, help }
const COMMANDS = {
  init: { args: [], opts: [], required: [], help: 'create the store directory and its empty files (safe to rerun)' },
  'unit add': { args: ['name'], opts: ['track', 'brief'], required: ['track'], help: 'add a unit at stage pending' },
  'unit set': { args: ['name'], opts: ['stage', 'branch', 'pr', 'head'], required: ['stage'], help: 'move a unit to a new stage, optionally setting branch, PR, head SHA' },
  'unit get': { args: ['name'], opts: [], required: [], help: 'print one unit (exit 2 if missing)' },
  'unit list': { args: [], opts: ['stage', 'track'], required: [], help: 'list units, optionally filtered' },
  'unit counts': { args: [], opts: [], required: [], help: 'count units by stage' },
  'ledger record': { args: ['pr', 'head', 'verdict'], opts: ['evidence', 'verifier'], required: ['evidence'], help: `record a verification verdict (${VERDICTS.join(', ')})` },
  'ledger check': { args: ['pr', 'head'], opts: [], required: [], help: `print the verdict for a PR head, or ${NO_VERDICT} with exit 2` },
  'ledger summary': { args: [], opts: [], required: [], help: 'count ledger rows by verdict' },
  'inbox push': { args: ['from', 'unit', 'outcome'], opts: ['report'], required: [], help: 'drop a report pointer into the inbox' },
  'inbox drain': { args: [], opts: ['peek'], required: [], help: 'take and print every pointer (--peek reads without taking)' },
  'inbox count': { args: [], opts: [], required: [], help: 'count pointers waiting in the inbox' },
  'gate park': { args: ['id'], opts: ['question', 'options', 'default'], required: ['question', 'options', 'default'], help: 'open (or replace) a decision gate for the human' },
  'gate list': { args: [], opts: [], required: [], help: 'list open gates' },
  'gate resolve': { args: ['id'], opts: ['answer'], required: ['answer'], help: 'resolve a gate with the human\'s answer (exit 2 if missing)' },
  'frontier set': { args: [], opts: ['repo', 'prs'], required: [], help: 'resolve the PR stack for the repo\'s checked-out branch and store it' },
  'frontier show': { args: [], opts: [], required: [], help: 'print the stored frontier' },
  status: { args: [], opts: [], required: [], help: 'write status.md and print counts, changes, and open gates' },
  'standing show': { args: [], opts: [], required: [], help: 'list standing orders' },
  'standing add': { args: ['line'], opts: [], required: [], help: 'append a standing order' },
};
const GROUPS = ['unit', 'ledger', 'inbox', 'gate', 'frontier', 'standing'];

const OPTION_HELP = {
  track: '--track <t>', brief: '--brief <path>', stage: '--stage <s>', branch: '--branch <b>', pr: '--pr <n>', head: '--head <sha>',
  evidence: '--evidence <path>', verifier: '--verifier <name>', report: '--report <path>', peek: '--peek',
  question: '--question <text>', options: '--options <text>', default: '--default <text>', answer: '--answer <text>',
  repo: '--repo <dir>      repository to read (default: ORCH_REPO)', prs: '--prs <n,...>     expected bottom-to-top PR order; fail on drift',
};

export function helpText(command = null) {
  if (command && COMMANDS[command]) {
    const c = COMMANDS[command];
    const lines = [`usage: orch [--store <dir>] [--json] [--force] ${command}${c.args.map((a) => ` <${a}>`).join('')}${c.opts.map((o) => ` ${c.required.includes(o) ? '' : '['}${OPTION_HELP[o].split(/\s{2,}/)[0]}${c.required.includes(o) ? '' : ']'}`).join('')}`, '', c.help];
    if (c.opts.length) {
      lines.push('', 'options');
      for (const o of c.opts) lines.push(`  ${OPTION_HELP[o]}${c.required.includes(o) ? '  (required)' : ''}`);
    }
    return lines.join('\n') + '\n';
  }
  const lines = [
    'orch: shared state for a multi-agent program, kept as plain files in one directory.',
    '',
    'usage: orch [--store <dir>] [--json] [--force] <command> ...',
    '',
    'global options',
    '  --store <dir>   store directory (default: ORCH_STORE)',
    '  --json          print complete rows as JSON',
    '  --force         take the store lock even from a live holder',
    '  -h, --help      show help (also after a command)',
    '',
    'commands',
  ];
  for (const [name, c] of Object.entries(COMMANDS)) {
    const sig = `${name}${c.args.map((a) => ` <${a}>`).join('')}`;
    lines.push(`  ${sig.padEnd(34)}${c.help}`);
  }
  lines.push('', 'exit codes', '  0  success', '  1  usage or user error', '  2  no such unit, gate, or ledger row');
  return lines.map((l) => `${l}\n`).join('');
}

function parse(argv) {
  let parsed;
  try {
    parsed = parseArgs({
      args: argv,
      options: Object.fromEntries(Object.entries(OPTION_TYPES).map(([k, type]) => [k, { type, ...(k === 'help' ? { short: 'h' } : {}) }])),
      allowPositionals: true,
      strict: true,
      tokens: true,
    });
  } catch (err) {
    throw new UsageError(err.message.replace(/\. To specify a positional.*$/s, ''));
  }
  const given = new Set(parsed.tokens.filter((t) => t.kind === 'option').map((t) => t.name));
  return { values: parsed.values, positionals: parsed.positionals, given };
}

function pickCommand(positionals) {
  const [first, second] = positionals;
  if (first === undefined) return { name: null, rest: [] };
  if (GROUPS.includes(first)) {
    if (second === undefined) return { name: null, group: first, rest: [] };
    const name = `${first} ${second}`;
    if (!COMMANDS[name]) throw new UsageError(`unknown command '${name}'`);
    return { name, rest: positionals.slice(2) };
  }
  if (!COMMANDS[first]) throw new UsageError(`unknown command '${first}'`);
  return { name: first, rest: positionals.slice(1) };
}

function parsePrList(text) {
  const parts = String(text).split(',');
  if (parts.some((p) => p.trim() === '')) throw new UserError('--prs must be a comma list with no empty entries');
  const out = parts.map((p) => parsePr(p.trim(), '--prs entry'));
  const dup = out.find((n, i) => out.indexOf(n) !== i);
  if (dup !== undefined) throw new UserError(`--prs lists #${dup} twice`);
  return out;
}

const COMPACT_LIMIT = 4;

function compactList(lines, empty) {
  if (lines.length === 0) return [empty];
  if (lines.length <= COMPACT_LIMIT) return lines;
  return [...lines.slice(0, COMPACT_LIMIT), `${lines.length - COMPACT_LIMIT} more; use --json`];
}

const unitLine = (u) => UNIT_COLUMNS.map((c) => u[c]).join('\t');
const pointerLine = (p) => INBOX_COLUMNS.map((c) => p[c]).join('\t');
const gateLine = (g) => [g.id, g.question, g.options, g.default].join('\t');

export async function main(argv, deps = {}) {
  const env = deps.env ?? process.env;
  const cwd = deps.cwd ?? process.cwd();
  const out = deps.stdout ?? ((s) => process.stdout.write(s));
  const err = deps.stderr ?? ((s) => process.stderr.write(s));
  const print = (lines) => out([lines].flat().join('\n') + '\n');
  let command = null;
  let store = null;

  try {
    const { values: v, positionals, given } = parse(argv);
    const picked = pickCommand(positionals);
    command = picked.name;

    if (v.help || (!picked.name && !picked.group)) {
      if (!v.help && positionals.length === 0) throw new UsageError('no command given');
      out(helpText(picked.name));
      return 0;
    }

    const storeDir = (v.store ?? env.ORCH_STORE ?? '').trim();
    if (storeDir === '') throw new UserError('set --store or ORCH_STORE');
    if (picked.group) throw new UsageError(`'${picked.group}' needs a subcommand`);

    const spec = COMMANDS[command];
    for (const name of given) {
      if (!GLOBAL.includes(name) && !spec.opts.includes(name)) throw new UsageError(`'${command}' does not take --${name}`);
    }
    for (const name of spec.required) {
      if (v[name] === undefined) throw new UsageError(`'${command}' requires --${name}`);
    }
    if (picked.rest.length < spec.args.length) throw new UsageError(`'${command}' needs <${spec.args[picked.rest.length]}>`);
    if (picked.rest.length > spec.args.length) throw new UsageError(`unexpected argument '${picked.rest[spec.args.length]}'`);
    const a = Object.fromEntries(spec.args.map((name, i) => [name, picked.rest[i]]));

    store = new Store(path.resolve(cwd, storeDir), { force: Boolean(v.force), warn: (m) => err(`warning: ${m}\n`), now: deps.now });
    const json = (value) => out(JSON.stringify(value, null, 2) + '\n');
    const emit = (value, text) => (v.json ? json(value) : print(text));

    switch (command) {
      case 'init': {
        const dir = store.init();
        emit({ store: dir }, `initialized ${dir}`);
        break;
      }
      case 'unit add': {
        const row = store.addUnit(a.name, { track: v.track, brief: v.brief });
        emit(row, unitLine(row));
        break;
      }
      case 'unit set': {
        const row = store.setUnit(a.name, { stage: v.stage, branch: v.branch, pr: v.pr, head: v.head });
        emit(row, unitLine(row));
        break;
      }
      case 'unit get': {
        const row = store.getUnit(a.name);
        emit(row, unitLine(row));
        break;
      }
      case 'unit list': {
        const rows = store.listUnits({ stage: v.stage, track: v.track });
        emit(rows, compactList(rows.map(unitLine), 'no units'));
        break;
      }
      case 'unit counts': {
        const counts = store.unitCounts();
        emit(counts, formatCounts(counts));
        break;
      }
      case 'ledger record': {
        const row = store.record(a.pr, a.head, a.verdict, { evidence: v.evidence, verifier: v.verifier });
        emit(row, ['pr', 'head', 'verdict'].map((c) => row[c]).join('\t'));
        break;
      }
      case 'ledger check': {
        const row = store.check(a.pr, a.head);
        if (!row) {
          emit({ pr: parsePr(a.pr, 'pr'), head: a.head, verdict: NO_VERDICT }, NO_VERDICT);
          return 2;
        }
        emit(row, row.verdict);
        break;
      }
      case 'ledger summary': {
        const counts = store.ledgerSummary();
        emit(counts, formatCounts(counts));
        break;
      }
      case 'inbox push': {
        const p = store.push(a.from, a.unit, a.outcome, { report: v.report });
        emit(p, `${p.unit}\t${p.outcome}\t${p.file}`);
        break;
      }
      case 'inbox drain': {
        const rows = v.peek ? store.peek() : store.drain();
        emit(rows, rows.length ? rows.map(pointerLine) : ['(empty)']);
        break;
      }
      case 'inbox count': {
        const count = store.inboxCount();
        emit({ count }, String(count));
        break;
      }
      case 'gate park': {
        const g = store.park(a.id, { question: v.question, options: v.options, def: v.default });
        emit(g, `parked ${g.id}`);
        break;
      }
      case 'gate list': {
        const gates = store.openGates();
        emit(gates, compactList(gates.map(gateLine), 'no open gates'));
        break;
      }
      case 'gate resolve': {
        const g = store.resolveGate(a.id, v.answer);
        emit(g, `resolved ${g.id}: ${g.answer}`);
        break;
      }
      case 'frontier set': {
        const repo = (v.repo ?? env.ORCH_REPO ?? '').trim();
        if (repo === '') throw new UserError('frontier set needs a repository: pass --repo <dir> or set ORCH_REPO');
        const pin = v.prs !== undefined ? parsePrList(v.prs) : null;
        const run = deps.run ?? commandRunner(path.resolve(cwd, repo), env);
        const f = store.setFrontier({ run, pin });
        emit(f, frontierLine(f));
        break;
      }
      case 'frontier show': {
        const f = store.readFrontier();
        emit(f, frontierLine(f));
        break;
      }
      case 'status': {
        const { summary, changes } = store.status();
        const gates = summary.openGates;
        const shown = gates.slice(0, COMPACT_LIMIT).join(', ');
        const more = gates.length > COMPACT_LIMIT ? ` +${gates.length - COMPACT_LIMIT} more` : '';
        emit({ summary, changes }, [
          `units=${summary.unitTotal} (${formatCounts(summary.units)}) ledger=${formatCounts(summary.ledger)}`,
          `changed: ${changes}`,
          `open gates=${gates.length}${gates.length ? `: ${shown}${more}` : ''}`,
        ]);
        break;
      }
      case 'standing show': {
        const lines = store.readStanding();
        emit(lines, compactList(lines.map((l, i) => `${i + 1}. ${l}`), 'no standing orders'));
        break;
      }
      case 'standing add': {
        const s = store.addStanding(a.line);
        emit(s, `${s.n}. ${s.text}`);
        break;
      }
      default:
        throw new UsageError(`unknown command '${command}'`);
    }
    return 0;
  } catch (e) {
    if (e instanceof NotFound) {
      err(`error: ${e.message}\n`);
      return 2;
    }
    if (e instanceof UsageError) {
      err(`error: ${e.message}\n\n${helpText(command)}`);
      return 1;
    }
    if (e instanceof UserError) {
      err(`error: ${e.message}\n`);
      return 1;
    }
    throw e;
  } finally {
    store?.close();
  }
}
