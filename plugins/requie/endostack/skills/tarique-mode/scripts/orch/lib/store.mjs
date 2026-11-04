// The orchestration store: plain files in one directory, guarded by a
// pid lock for writers. Readers never take the lock; every write replaces
// its file atomically, so a reader sees either the old or the new file.

import path from 'node:path';
import fs from 'node:fs';
import { randomUUID } from 'node:crypto';
import { UserError, NotFound } from './errors.mjs';
import { writeAtomic, readTsv, formatTsv, cleanCell, requiredCell, requiredLine, parsePr } from './files.mjs';
import { acquireLock, releaseLock } from './lock.mjs';
import { parseGates, formatGates, parseStanding, formatStanding } from './gates.mjs';
import { resolveChain, checkPin } from './frontier.mjs';

export const UNIT_COLUMNS = ['name', 'track', 'stage', 'pr', 'branch', 'head', 'brief'];
export const LEDGER_COLUMNS = ['pr', 'head', 'verdict', 'evidence', 'verifier', 'recorded'];
export const INBOX_COLUMNS = ['at', 'from', 'unit', 'outcome', 'report'];
// Strongest first: seen working in the live product, covered by passing tests,
// type-checked and nothing more, the checker could not run, the checker saw it fail.
export const VERDICTS = ['live-proven', 'tests-proven', 'types-only', 'check-blocked', 'check-failed'];
export const NO_VERDICT = 'NO-VERDICT';
const EMPTY_FRONTIER = Object.freeze({ generation: 0, prs: [], lowestUnmerged: null });

const FILES = {
  units: 'work-units.tsv',
  ledger: 'ledger.tsv',
  inbox: 'inbox',
  gates: 'gates.md',
  standing: 'standing-orders.md',
  frontier: 'frontier.json',
  status: 'status.md',
  lock: '.writer.pid',
};

const SUMMARY_TAG = 'orch-summary';

export class Store {
  constructor(dir, { force = false, warn = (m) => process.stderr.write(`warning: ${m}\n`), now = () => new Date() } = {}) {
    if (typeof dir !== 'string' || dir.trim() === '') throw new UserError('set --store or ORCH_STORE');
    this.dir = path.resolve(dir);
    this.force = force;
    this.warn = warn;
    this.now = now;
    this.locked = false;
    this.closed = false;
  }

  path(key) {
    return path.join(this.dir, FILES[key]);
  }

  // ---------- lifecycle ----------

  assertOpen() {
    if (this.closed) throw new UserError('this store handle was already closed');
  }

  missingStore() {
    return new UserError(`no orch store at ${this.dir}; create it with orch init`);
  }

  assertInitialized() {
    for (const key of ['units', 'ledger', 'inbox', 'gates', 'standing', 'frontier']) {
      if (!fs.existsSync(this.path(key))) throw this.missingStore();
    }
  }

  lockForWrite() {
    this.assertOpen();
    if (this.locked) return;
    if (!fs.existsSync(this.dir)) throw this.missingStore();
    acquireLock(this.path('lock'), { force: this.force, warn: this.warn });
    this.locked = true;
  }

  close() {
    if (this.closed) return;
    if (this.locked) releaseLock(this.path('lock'));
    this.locked = false;
    this.closed = true;
  }

  init() {
    this.assertOpen();
    fs.mkdirSync(this.dir, { recursive: true });
    this.lockForWrite();
    const empty = {
      units: UNIT_COLUMNS.join('\t') + '\n',
      ledger: LEDGER_COLUMNS.join('\t') + '\n',
      gates: '',
      standing: '',
      frontier: '{}\n',
    };
    for (const [key, content] of Object.entries(empty)) {
      if (!fs.existsSync(this.path(key))) writeAtomic(this.path(key), content);
    }
    if (!fs.existsSync(this.path('inbox'))) fs.mkdirSync(this.path('inbox'));
    return this.dir;
  }

  // ---------- read helpers ----------

  read(key) {
    this.assertOpen();
    try {
      return fs.readFileSync(this.path(key), 'utf8');
    } catch (err) {
      throw err.code === 'ENOENT' ? this.missingStore() : err;
    }
  }

  readUnits() {
    this.read('units');
    return readTsv(this.path('units'), UNIT_COLUMNS, FILES.units);
  }

  readLedger() {
    this.read('ledger');
    const rows = readTsv(this.path('ledger'), LEDGER_COLUMNS, FILES.ledger);
    for (const r of rows) {
      if (!VERDICTS.includes(r.verdict)) throw new UserError(`${FILES.ledger} has an unknown verdict '${r.verdict}' for PR ${r.pr}`);
    }
    return rows;
  }

  readGates() {
    return parseGates(this.read('gates'), FILES.gates);
  }

  readStanding() {
    return parseStanding(this.read('standing'), FILES.standing);
  }

  readFrontier() {
    const text = this.read('frontier');
    let data;
    try {
      data = JSON.parse(text);
    } catch {
      throw new UserError(`${FILES.frontier} is not valid JSON`);
    }
    if (data === null || typeof data !== 'object' || Array.isArray(data)) throw new UserError(`${FILES.frontier} has an invalid shape`);
    if (Object.keys(data).length === 0) return { ...EMPTY_FRONTIER, prs: [] };
    const okGen = Number.isSafeInteger(data.generation) && data.generation >= 0;
    const okLow = data.lowestUnmerged === null || (Number.isSafeInteger(data.lowestUnmerged) && data.lowestUnmerged > 0);
    if (!okGen || !Array.isArray(data.prs) || !okLow) throw new UserError(`${FILES.frontier} has an invalid shape`);
    for (const p of data.prs) {
      const ok =
        p && Number.isSafeInteger(p.pr) && p.pr > 0 && typeof p.branch === 'string' && p.branch !== '' &&
        typeof p.sha === 'string' && /^[0-9a-f]{40,64}$/.test(p.sha) && ['OPEN', 'MERGED', 'CLOSED'].includes(p.state);
      if (!ok) throw new UserError(`${FILES.frontier} has an invalid PR row`);
    }
    return { generation: data.generation, prs: data.prs, lowestUnmerged: data.lowestUnmerged };
  }

  // ---------- units ----------

  addUnit(name, { track, brief = '' }) {
    this.lockForWrite();
    const row = Object.fromEntries(UNIT_COLUMNS.map((c) => [c, '']));
    row.name = requiredCell(name, 'unit name');
    row.track = requiredCell(track, 'track');
    row.stage = 'pending';
    row.brief = cleanCell(brief);
    const units = this.readUnits();
    if (units.some((u) => u.name === row.name)) throw new UserError(`a unit named '${row.name}' is already recorded`);
    units.push(row);
    writeAtomic(this.path('units'), formatTsv(UNIT_COLUMNS, units));
    return row;
  }

  setUnit(name, { stage, branch, pr, head }) {
    this.lockForWrite();
    const key = requiredCell(name, 'unit name');
    const units = this.readUnits();
    const unit = units.find((u) => u.name === key);
    if (!unit) throw new NotFound(`unit '${key}' not found`);
    unit.stage = requiredCell(stage, 'stage');
    if (branch !== undefined) unit.branch = cleanCell(branch);
    if (pr !== undefined) unit.pr = String(parsePr(pr, '--pr'));
    if (head !== undefined) unit.head = cleanCell(head);
    writeAtomic(this.path('units'), formatTsv(UNIT_COLUMNS, units));
    return unit;
  }

  getUnit(name) {
    const key = cleanCell(name);
    const unit = this.readUnits().find((u) => u.name === key);
    if (!unit) throw new NotFound(`unit '${key}' not found`);
    return unit;
  }

  listUnits({ stage, track } = {}) {
    return this.readUnits().filter((u) => (stage === undefined || u.stage === stage) && (track === undefined || u.track === track));
  }

  unitCounts() {
    return countBy(this.readUnits(), 'stage');
  }

  // ---------- ledger ----------

  record(pr, head, verdict, { evidence, verifier = '' }) {
    this.lockForWrite();
    const prNum = parsePr(pr, 'pr');
    const headCell = requiredCell(head, 'head');
    if (!VERDICTS.includes(verdict)) throw new UserError(`verdict must be one of: ${VERDICTS.join(', ')}`);
    const row = { pr: String(prNum), head: headCell, verdict, evidence: requiredCell(evidence, 'evidence'), verifier: cleanCell(verifier), recorded: this.now().toISOString() };
    const rows = this.readLedger().filter((r) => !(r.pr === row.pr && r.head === row.head));
    rows.push(row);
    writeAtomic(this.path('ledger'), formatTsv(LEDGER_COLUMNS, rows));
    return row;
  }

  check(pr, head) {
    const prNum = String(parsePr(pr, 'pr'));
    const headCell = cleanCell(head);
    return this.readLedger().find((r) => r.pr === prNum && r.head === headCell) ?? null;
  }

  ledgerSummary() {
    return countBy(this.readLedger(), 'verdict');
  }

  // ---------- inbox ----------

  push(from, unit, outcome, { report = '' } = {}) {
    this.lockForWrite();
    const dir = this.path('inbox');
    if (!fs.existsSync(dir)) throw this.missingStore();
    const at = this.now().toISOString();
    const pointer = { at, from: requiredCell(from, 'from'), unit: requiredCell(unit, 'unit'), outcome: requiredCell(outcome, 'outcome'), report: cleanCell(report) };
    const name = `${at.replace(/[:.]/g, '-')}-${process.pid}-${randomUUID()}.tsv`;
    writeAtomic(path.join(dir, name), INBOX_COLUMNS.map((c) => pointer[c]).join('\t') + '\n');
    return { ...pointer, file: name };
  }

  readInboxDir(dir) {
    let names;
    try {
      names = fs.readdirSync(dir).filter((n) => n.endsWith('.tsv') && !n.startsWith('.')).sort();
    } catch (err) {
      throw err.code === 'ENOENT' ? this.missingStore() : err;
    }
    return names.map((name) => {
      const text = fs.readFileSync(path.join(dir, name), 'utf8').replace(/\n$/, '');
      const cells = text.split('\t');
      if (/[\r\n]/.test(text) || cells.length !== INBOX_COLUMNS.length) throw new UserError(`inbox pointer ${name} is malformed`);
      return { ...Object.fromEntries(INBOX_COLUMNS.map((c, i) => [c, cells[i]])), file: name };
    });
  }

  peek() {
    this.assertOpen();
    return this.readInboxDir(this.path('inbox'));
  }

  inboxCount() {
    return this.peek().length;
  }

  // Take every pointer in one step: read them, move the directory aside,
  // put a fresh empty one in place, then delete the old one. A pointer
  // pushed during the drain lands in either the old directory (and is
  // returned, because it is read again after the rename) or the new one.
  drain() {
    this.lockForWrite();
    const dir = this.path('inbox');
    this.readInboxDir(dir);
    const aside = path.join(this.dir, `.inbox.draining.${process.pid}.${randomUUID()}`);
    fs.renameSync(dir, aside);
    try {
      fs.mkdirSync(dir);
    } catch (err) {
      fs.renameSync(aside, dir);
      throw err;
    }
    const drained = this.readInboxDir(aside);
    fs.rmSync(aside, { recursive: true, force: true });
    return drained;
  }

  // ---------- gates ----------

  park(id, { question, options, def }) {
    this.lockForWrite();
    const gate = {
      id: requiredLine(id, 'gate id'),
      status: 'open',
      question: requiredLine(question, 'question'),
      options: requiredLine(options, 'options'),
      default: requiredLine(def, 'default'),
    };
    if (gate.id.includes('#')) throw new UserError('gate id must not contain #');
    const gates = this.readGates();
    const i = gates.findIndex((g) => g.id === gate.id);
    if (i >= 0) gates[i] = gate;
    else gates.push(gate);
    writeAtomic(this.path('gates'), formatGates(gates));
    return gate;
  }

  openGates() {
    return this.readGates().filter((g) => g.status === 'open');
  }

  resolveGate(id, answer) {
    this.lockForWrite();
    const key = requiredLine(id, 'gate id');
    const gates = this.readGates();
    const gate = gates.find((g) => g.id === key);
    if (!gate) throw new NotFound(`gate '${key}' not found`);
    gate.status = 'resolved';
    gate.answer = requiredLine(answer, 'answer');
    writeAtomic(this.path('gates'), formatGates(gates));
    return gate;
  }

  // ---------- standing orders ----------

  addStanding(line) {
    this.lockForWrite();
    const text = requiredLine(line, 'standing order');
    const lines = this.readStanding();
    lines.push(text);
    writeAtomic(this.path('standing'), formatStanding(lines));
    return { n: lines.length, text };
  }

  // ---------- frontier ----------

  setFrontier({ run, pin = null }) {
    this.lockForWrite();
    const prev = this.readFrontier();
    const { chain } = resolveChain(run);
    if (pin) checkPin(chain, pin);
    const next = {
      generation: prev.generation + 1,
      prs: chain,
      lowestUnmerged: chain.find((p) => p.state === 'OPEN')?.pr ?? null,
    };
    writeAtomic(this.path('frontier'), JSON.stringify(next, null, 2) + '\n');
    return next;
  }

  // ---------- status ----------

  summary() {
    return {
      units: this.unitCounts(),
      unitTotal: this.readUnits().length,
      ledger: this.ledgerSummary(),
      frontierGeneration: this.readFrontier().generation,
      openGates: this.openGates().map((g) => g.id).sort(),
    };
  }

  previousSummary() {
    let text;
    try {
      text = fs.readFileSync(this.path('status'), 'utf8');
    } catch {
      return null;
    }
    const m = new RegExp(`<!-- ${SUMMARY_TAG} (.*?) -->`).exec(text);
    if (!m) return null;
    try {
      const s = JSON.parse(m[1]);
      return s && typeof s === 'object' ? s : null;
    } catch {
      return null;
    }
  }

  status() {
    this.lockForWrite();
    this.assertInitialized();
    const prev = this.previousSummary();
    const units = this.readUnits();
    const ledger = this.readLedger();
    const frontier = this.readFrontier();
    const gates = this.openGates();
    const summary = this.summary();
    writeAtomic(this.path('status'), renderStatus({ units, ledger, frontier, gates, summary, at: this.now() }));
    return { summary, changes: diffSummary(prev, summary) };
  }
}

// Tally rows by one column; keys come back in code-point order so output is stable.
export function countBy(rows, key) {
  const tally = new Map();
  for (const r of rows) tally.set(r[key], (tally.get(r[key]) ?? 0) + 1);
  const keys = [...tally.keys()].sort();
  return Object.fromEntries(keys.map((k) => [k, tally.get(k)]));
}

export function formatCounts(counts) {
  const entries = Object.entries(counts);
  return entries.length ? entries.map(([k, v]) => `${k}=${v}`).join(', ') : 'none';
}

export function diffSummary(prev, cur) {
  if (!prev) return 'first render';
  const out = [];
  const diffMap = (label, a = {}, b = {}) => {
    for (const k of [...new Set([...Object.keys(a), ...Object.keys(b)])].sort()) {
      if ((a[k] ?? 0) !== (b[k] ?? 0)) out.push(`${label} ${k} ${a[k] ?? 0}->${b[k] ?? 0}`);
    }
  };
  diffMap('units', prev.units, cur.units);
  diffMap('ledger', prev.ledger, cur.ledger);
  if ((prev.frontierGeneration ?? 0) !== cur.frontierGeneration) out.push(`frontier generation ${prev.frontierGeneration ?? 0}->${cur.frontierGeneration}`);
  const pg = Array.isArray(prev.openGates) ? prev.openGates.length : 0;
  if (pg !== cur.openGates.length) out.push(`open gates ${pg}->${cur.openGates.length}`);
  return out.length ? out.join('; ') : 'no derived changes';
}

function mdCell(v) {
  return String(v ?? '').replace(/\\/g, '\\\\').replace(/\|/g, '\\|');
}

function mdTable(columns, rows) {
  if (!rows.length) return '(no rows)';
  return [
    `| ${columns.join(' | ')} |`,
    `| ${columns.map(() => '---').join(' | ')} |`,
    ...rows.map((r) => `| ${columns.map((c) => mdCell(r[c])).join(' | ')} |`),
  ].join('\n');
}

export function renderStatus({ units, ledger, frontier, gates, summary, at }) {
  const parts = [
    '# Orchestration status',
    '',
    `Generated ${at.toISOString()}.`,
    '',
    '## Units',
    '',
    `${units.length} unit${units.length === 1 ? '' : 's'}: ${formatCounts(summary.units)}.`,
    '',
    mdTable(UNIT_COLUMNS, units),
    '',
    '## Verification ledger',
    '',
    `${ledger.length} record${ledger.length === 1 ? '' : 's'}: ${formatCounts(summary.ledger)}.`,
    '',
    mdTable(LEDGER_COLUMNS, ledger),
    '',
    '## Frontier',
    '',
    `Generation ${frontier.generation}, lowest unmerged ${frontier.lowestUnmerged ? `#${frontier.lowestUnmerged}` : 'none'}, ${frontier.prs.length} PR${frontier.prs.length === 1 ? '' : 's'}.`,
    '',
    mdTable(['pr', 'branch', 'sha', 'state'], frontier.prs),
    '',
    '## Open gates',
    '',
    `${gates.length} open gate${gates.length === 1 ? '' : 's'}.`,
    '',
    mdTable(['id', 'question', 'options', 'default'], gates),
    '',
    `<!-- ${SUMMARY_TAG} ${JSON.stringify(summary).replace(/--/g, '-\\u002d')} -->`,
    '',
  ];
  return parts.join('\n');
}
