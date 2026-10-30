import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as path from 'node:path';
import * as fs from 'node:fs';
import * as cp from 'node:child_process';
import { Store, diffSummary, UNIT_COLUMNS, LEDGER_COLUMNS } from '../lib/store.mjs';
import { cleanCell } from '../lib/files.mjs';
import { UserError, NotFound } from '../lib/errors.mjs';
import { tmpdir } from './helpers.mjs';

function fresh() {
  const dir = path.join(tmpdir(), 'store');
  const s = new Store(dir, { warn: () => {} });
  s.init();
  s.close();
  return dir;
}

const open = (dir, opts = {}) => new Store(dir, { warn: () => {}, ...opts });

const STORE_ENTRIES = ['standing-orders.md', '.writer.pid', 'inbox', 'work-units.tsv', 'gates.md', 'ledger.tsv', 'frontier.json'].sort();
const DATA_FILES = STORE_ENTRIES.filter((n) => !n.startsWith('.') && n !== 'inbox');

test('init makes the seven entries, a rerun changes no bytes, and close releases the lock', () => {
  const dir = path.join(tmpdir(), 'store');
  const s = open(dir);
  s.init();
  assert.deepEqual(fs.readdirSync(dir).sort(), STORE_ENTRIES);
  s.close();
  assert.ok(!fs.existsSync(path.join(dir, '.writer.pid')));
  const before = Object.fromEntries(DATA_FILES.map((f) => [f, fs.readFileSync(path.join(dir, f))]));
  fs.appendFileSync(path.join(dir, 'work-units.tsv'), 'u1\tt\tpending\t\t\t\t\n');
  const after1 = fs.readFileSync(path.join(dir, 'work-units.tsv'));
  const s2 = open(dir);
  s2.init();
  s2.close();
  assert.deepEqual(fs.readFileSync(path.join(dir, 'work-units.tsv')), after1, 'existing files are left alone');
  for (const f of DATA_FILES.filter((n) => n !== 'work-units.tsv')) assert.deepEqual(fs.readFileSync(path.join(dir, f)), before[f]);
  assert.ok(!fs.readdirSync(dir).some((n) => n.endsWith('.tmp')));
});

test('unit add, set, get, list, and counts work together', () => {
  const dir = fresh();
  const s = open(dir);
  s.addUnit('auth', { track: 'backend', brief: 'briefs/auth.md' });
  s.addUnit('ui', { track: 'frontend' });
  s.addUnit('db', { track: 'backend' });
  assert.throws(() => s.addUnit('ui', { track: 'x' }), /already recorded/);
  s.setUnit('auth', { stage: 'in-review', branch: 'feat/auth', pr: '12', head: 'abc' });
  s.setUnit('auth', { stage: 'merged' });
  const u = s.getUnit('auth');
  assert.deepEqual(u, { name: 'auth', track: 'backend', stage: 'merged', pr: '12', branch: 'feat/auth', head: 'abc', brief: 'briefs/auth.md' });
  assert.throws(() => s.getUnit('nope'), NotFound);
  assert.throws(() => s.setUnit('nope', { stage: 'x' }), NotFound);
  assert.deepEqual(s.listUnits({ track: 'backend' }).map((x) => x.name), ['auth', 'db']);
  assert.deepEqual(s.listUnits({ stage: 'pending', track: 'backend' }).map((x) => x.name), ['db']);
  assert.deepEqual(s.unitCounts(), { merged: 1, pending: 2 });
  s.close();
});

test('cell cleanup turns tabs and newlines into spaces, quotes formulas, and rejects blanks', () => {
  assert.equal(cleanCell('a\tb\nc\rd'), 'a b c d');
  for (const c of ['=SUM(A1)', '+1', '-1', '@x']) assert.equal(cleanCell(c), `'${c}`);
  const dir = fresh();
  const s = open(dir);
  assert.throws(() => s.addUnit('   ', { track: 't' }), /unit name cannot be blank/);
  assert.throws(() => s.addUnit('x', { track: '\t' }), /track cannot be blank/);
  s.addUnit('=cmd', { track: 't\tx' });
  assert.equal(s.getUnit('=cmd').name, "'=cmd");
  assert.equal(s.getUnit('=cmd').track, 't x');
  s.close();
});

test('ledger records upsert on (PR, SHA) and support check and summary', () => {
  const dir = fresh();
  let t = 0;
  const s = open(dir, { now: () => new Date(Date.UTC(2026, 9, 1, 0, 0, t++)) });
  s.record('5', 'aaa', 'types-only', { evidence: 'logs/tc.txt' });
  s.record('5', 'aaa', 'tests-proven', { evidence: 'logs/unit.txt', verifier: 'v1' });
  s.record('5', 'bbb', 'check-failed', { evidence: 'e' });
  assert.equal(s.readLedger().length, 2);
  assert.equal(s.check(5, 'aaa').verdict, 'tests-proven');
  assert.equal(s.check(5, 'aaa').recorded, '2026-10-01T00:00:01.000Z');
  assert.equal(s.check(5, 'zzz'), null);
  assert.deepEqual(s.ledgerSummary(), { 'tests-proven': 1, 'check-failed': 1 });
  assert.throws(() => s.record('5', 'aaa', 'looks-fine', { evidence: 'e' }), /verdict must be one of/);
  assert.throws(() => s.record('0', 'aaa', 'types-only', { evidence: 'e' }), /whole number above zero/);
  assert.throws(() => s.record('5', 'aaa', 'types-only', { evidence: ' ' }), /evidence cannot be blank/);
  s.close();
});

test('inbox push, peek, count, and an atomic drain', () => {
  const dir = fresh();
  const s = open(dir);
  const a = s.push('owner-1', 'auth', 'done', { report: 'reports/a.md' });
  const b = s.push('owner-2', 'ui', 'blocked');
  assert.match(a.file, /^\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}-\d{3}Z-\d+-[0-9a-f-]{36}\.tsv$/);
  assert.equal(s.inboxCount(), 2);
  assert.deepEqual(s.peek().map((p) => p.unit).sort(), ['auth', 'ui']);
  assert.equal(s.inboxCount(), 2, 'peek does not drain');
  const drained = s.drain();
  assert.deepEqual(drained.map((p) => p.file).sort(), [a.file, b.file].sort());
  assert.equal(s.inboxCount(), 0);
  assert.deepEqual(fs.readdirSync(dir).filter((n) => n.startsWith('.inbox')), []);
  assert.deepEqual(s.drain(), []);
  s.close();
});

test('gates can be parked, listed, and resolved, and standing orders are stored', () => {
  const dir = fresh();
  const s = open(dir);
  s.park('schema', { question: 'Drop the legacy column?', options: 'yes / no', def: 'no' });
  s.park('naming', { question: 'Rename\nthe flag?', options: 'a|b', def: 'a' });
  s.park('schema', { question: 'Drop the legacy column now?', options: 'yes / no', def: 'no' });
  assert.deepEqual(s.openGates().map((g) => [g.id, g.question]), [['schema', 'Drop the legacy column now?'], ['naming', 'Rename the flag?']]);
  const r = s.resolveGate('naming', 'b');
  assert.equal(r.status, 'resolved');
  assert.equal(r.question, 'Rename the flag?');
  assert.deepEqual(s.openGates().map((g) => g.id), ['schema']);
  assert.throws(() => s.resolveGate('missing', 'x'), NotFound);
  s.addStanding('Never force-push shared branches');
  s.addStanding('Ask before\ndeleting data');
  assert.deepEqual(s.readStanding(), ['Never force-push shared branches', 'Ask before deleting data']);
  assert.equal(fs.readFileSync(path.join(dir, 'standing-orders.md'), 'utf8'), '1. Never force-push shared branches\n2. Ask before deleting data\n');
  s.close();
});

test('status renders with an embedded summary and diffs against the last render', () => {
  const dir = fresh();
  const s = open(dir);
  const first = s.status();
  assert.equal(first.changes, 'first render');
  s.addUnit('a|b', { track: 't\\x' });
  s.record('3', 'sha', 'live-proven', { evidence: 'shots/' });
  s.park('g1', { question: 'q', options: 'o', def: 'd' });
  const second = s.status();
  assert.equal(second.changes, 'units pending 0->1; ledger live-proven 0->1; open gates 0->1');
  const md = fs.readFileSync(path.join(dir, 'status.md'), 'utf8');
  assert.match(md, /^# Orchestration status/);
  assert.match(md, /## Units/);
  assert.match(md, /## Verification ledger/);
  assert.match(md, /## Frontier/);
  assert.match(md, /## Open gates/);
  assert.match(md, /\| a\\\|b \| t\\\\x \|/);
  assert.match(md, /<!-- orch-summary \{.*\} -->/);
  assert.equal(s.status().changes, 'no derived changes');
  s.close();
});

test('the status diff reports frontier generation and survives a corrupt previous summary', () => {
  const cur = { units: {}, ledger: {}, frontierGeneration: 2, openGates: [] };
  assert.equal(diffSummary({ units: {}, ledger: {}, frontierGeneration: 1, openGates: [] }, cur), 'frontier generation 1->2');
  const dir = fresh();
  fs.writeFileSync(path.join(dir, 'status.md'), '# old\n<!-- orch-summary {broken -->\n');
  const s = open(dir);
  assert.equal(s.status().changes, 'first render');
  s.close();
});

// ---------- locking ----------

function deadPid() {
  const r = cp.spawnSync(process.execPath, ['-e', 'process.stdout.write(String(process.pid))'], { encoding: 'utf8' });
  return Number(r.stdout);
}

test('a stale lock from a dead pid is taken over with a warning', () => {
  const dir = fresh();
  const pid = deadPid();
  fs.writeFileSync(path.join(dir, '.writer.pid'), `${pid}\n`);
  const warnings = [];
  const s = new Store(dir, { warn: (m) => warnings.push(m) });
  s.addUnit('x', { track: 't' });
  assert.equal(fs.readFileSync(path.join(dir, '.writer.pid'), 'utf8').trim(), String(process.pid));
  assert.match(warnings[0], new RegExp(`stale store lock from pid ${pid}`));
  s.close();
  assert.ok(!fs.existsSync(path.join(dir, '.writer.pid')));
});

test('a running holder blocks writers, and --force takes the lock and names the holder', async () => {
  const dir = fresh();
  const child = cp.spawn(process.execPath, ['-e', 'setTimeout(() => {}, 30000)'], { stdio: 'ignore' });
  try {
    fs.writeFileSync(path.join(dir, '.writer.pid'), `${child.pid}\n`);
    const s = open(dir);
    assert.throws(() => s.addUnit('x', { track: 't' }), new RegExp(`another writer \\(pid ${child.pid}\\) holds the store lock`));
    s.close();
    assert.equal(fs.readFileSync(path.join(dir, '.writer.pid'), 'utf8').trim(), String(child.pid), 'a failed writer leaves the lock alone');
    // Readers do not need the lock.
    assert.deepEqual(open(dir).listUnits(), []);
    const warnings = [];
    const f = new Store(dir, { force: true, warn: (m) => warnings.push(m) });
    f.addUnit('x', { track: 't' });
    assert.match(warnings[0], new RegExp(`taking the store lock from pid ${child.pid}`));
    f.close();
  } finally {
    child.kill();
  }
});

test('close leaves alone a lock this process no longer owns', () => {
  const dir = fresh();
  const s = open(dir);
  s.addUnit('x', { track: 't' });
  fs.writeFileSync(path.join(dir, '.writer.pid'), '999999\n');
  s.close();
  assert.equal(fs.readFileSync(path.join(dir, '.writer.pid'), 'utf8').trim(), '999999');
});

test('calls after close fail, and status after close is a user error', () => {
  const dir = fresh();
  const s = open(dir);
  s.close();
  assert.throws(() => s.addUnit('x', { track: 't' }), /already closed/);
  assert.throws(() => s.listUnits(), /already closed/);
  assert.throws(() => s.status(), (e) => e instanceof UserError && /already closed/.test(e.message));
});

test('writing to a store that does not exist says to run init', () => {
  const s = open(path.join(tmpdir(), 'nowhere'));
  assert.throws(() => s.addUnit('x', { track: 't' }), /no orch store at .*; create it with orch init/);
  assert.throws(() => s.listUnits(), /create it with orch init/);
  s.close();
});

// ---------- validation on read ----------

test('corrupt files produce targeted error messages', () => {
  const dir = fresh();
  const s = open(dir);
  const tsv = (...rows) => rows.map((r) => `${r.join('\t')}\n`).join('');
  fs.writeFileSync(path.join(dir, 'work-units.tsv'), tsv(['name', 'track']));
  assert.throws(() => s.listUnits(), /work-units\.tsv has an invalid header/);
  fs.writeFileSync(path.join(dir, 'work-units.tsv'), tsv(UNIT_COLUMNS, ['short', 'row']));
  assert.throws(() => s.listUnits(), /work-units\.tsv has a malformed row/);
  fs.writeFileSync(path.join(dir, 'ledger.tsv'), tsv(LEDGER_COLUMNS, ['1', 'a', 'lgtm', 'e', '', 't']));
  assert.throws(() => s.ledgerSummary(), /unknown verdict 'lgtm'/);
  for (const bad of ['[]', '{"generation":"1","prs":[],"lowestUnmerged":null}', 'not json']) {
    fs.writeFileSync(path.join(dir, 'frontier.json'), bad);
    assert.throws(() => s.readFrontier(), /frontier\.json (has an invalid shape|is not valid JSON)/);
  }
  fs.writeFileSync(path.join(dir, 'frontier.json'), JSON.stringify({ generation: 1, prs: [{ pr: 1, branch: 'a', sha: 'xyz', state: 'OPEN' }], lowestUnmerged: 1 }));
  assert.throws(() => s.readFrontier(), /invalid PR row/);
  fs.writeFileSync(path.join(dir, 'inbox', 'bad.tsv'), 'only\ttwo\n');
  assert.throws(() => s.peek(), /inbox pointer bad\.tsv is malformed/);
  fs.writeFileSync(path.join(dir, 'inbox', 'bad.tsv'), 'a\tb\nc\td\te\n');
  assert.throws(() => s.peek(), /inbox pointer bad\.tsv is malformed/);
  s.close();
});

test('gates.md and standing-orders.md use a strict parser', () => {
  const dir = fresh();
  const s = open(dir);
  const cases = [
    ['# Gate\n', /must start with '# Gates'/],
    ['# Gates\n\n## a\n- Status: open\n- Question: q\nstray\n', /malformed line/],
    ['# Gates\n\n## a\n- Status: open\n- Question: q\n- Options: o\n', /missing Default/],
    ['# Gates\n\n## a\n- Status: maybe\n- Question: q\n- Options: o\n- Default: d\n', /bad status/],
    ['# Gates\n\n## a\n- Status: resolved\n- Question: q\n- Options: o\n- Default: d\n', /resolved without an answer/],
    ['# Gates\n\n## a\n- Status: open\n- Question: q\n- Options: o\n- Default: d\n\n## a\n- Status: open\n- Question: q\n- Options: o\n- Default: d\n', /duplicate gate id/],
  ];
  for (const [text, re] of cases) {
    fs.writeFileSync(path.join(dir, 'gates.md'), text);
    assert.throws(() => s.openGates(), re);
  }
  fs.writeFileSync(path.join(dir, 'standing-orders.md'), '1. a\n3. b\n');
  assert.throws(() => s.readStanding(), /line 2 must read '2\. <order>'/);
  s.close();
});

test('NotFound and UserError are separate error types', () => {
  assert.ok(new NotFound('x') instanceof UserError);
});
