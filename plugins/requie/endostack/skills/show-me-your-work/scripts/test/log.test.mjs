import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
import { after, before, test } from 'node:test';
import { dirname, join } from 'node:path';
import { tmpdir } from 'node:os';
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { appendDecision, cleanCell, timestamp, HEADER, COLUMNS } from '../log.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const script = join(here, '..', 'log.mjs');
let dir;
const run = (...args) => spawnSync(process.execPath, [script, ...args], { encoding: 'utf8', cwd: dir });
const rowsOf = (file) => readFileSync(file, 'utf8').split('\n').filter(Boolean).map((l) => l.split('\t'));

before(() => (dir = mkdtempSync(join(tmpdir(), 'decision-log-'))));
after(() => rmSync(dir, { force: true, recursive: true }));

test('a wrong argument count prints usage, exits 1, and creates no file', () => {
  for (const args of [[], ['a.tsv'], ['a.tsv', '1', '2', '3', '4'], ['a.tsv', '1', '2', '3', '4', '5', '6']]) {
    const r = run(...args);
    assert.equal(r.status, 1, `args ${args.length}`);
    assert.match(r.stderr, /^usage: node log\.mjs/);
  }
  assert.throws(() => readFileSync(join(dir, 'a.tsv')), { code: 'ENOENT' });
});

test('the header is written on the first call only, and later calls append rows', () => {
  const file = join(dir, 'once.tsv');
  assert.equal(run(file, 'plan', 'd1', 'r1', 'e1', 'o1').status, 0);
  assert.equal(run(file, 'build', 'd2', 'r2', 'e2', 'o2').status, 0);
  const rows = rowsOf(file);
  assert.deepEqual(rows[0], COLUMNS);
  assert.equal(rows.length, 3);
  assert.deepEqual(rows[1].slice(1), ['plan', 'd1', 'r1', 'e1', 'o1']);
  assert.deepEqual(rows[2].slice(1), ['build', 'd2', 'r2', 'e2', 'o2']);
  assert.equal(readFileSync(file, 'utf8').split(HEADER).length, 2);
});

test('an empty existing file receives the header and a non-empty one is never truncated', () => {
  const empty = join(dir, 'empty.tsv');
  writeFileSync(empty, '');
  run(empty, 'p', 'd', 'r', 'e', 'o');
  assert.deepEqual(rowsOf(empty)[0], COLUMNS);

  const kept = join(dir, 'kept.tsv');
  writeFileSync(kept, 'existing\trow');
  run(kept, 'p', 'd', 'r', 'e', 'o');
  const rows = rowsOf(kept);
  assert.deepEqual(rows[0], ['existing', 'row']);
  assert.equal(rows[1][1], 'p');
});

test('absent parent directories are created', () => {
  const file = join(dir, 'a', 'b', 'c', 'log.tsv');
  assert.equal(run(file, 'p', 'd', 'r', 'e', 'o').status, 0);
  assert.equal(rowsOf(file).length, 2);
});

test('a plain filename writes into the current directory', () => {
  assert.equal(run('bare.tsv', 'p', 'd', 'r', 'e', 'o').status, 0);
  assert.equal(rowsOf(join(dir, 'bare.tsv')).length, 2);
});

test('tabs, LF, and CR are collapsed so each row has six cells', () => {
  const file = join(dir, 'flat.tsv');
  run(file, 'ph\tase', 'line1\nline2', 'a\r\nb', 'x\ty\tz', 'ok');
  const rows = rowsOf(file);
  assert.equal(rows.length, 2);
  assert.equal(rows[1].length, 6);
  assert.deepEqual(rows[1].slice(1), ['ph ase', 'line1 line2', 'a  b', 'x y z', 'ok']);
});

test('cells beginning with = + - @ are prefixed with a quote, even after whitespace', () => {
  for (const [input, want] of [
    ['=HYPERLINK("http://evil")', `'=HYPERLINK("http://evil")`],
    ['+1+1', `'+1+1`],
    ['-2', `'-2`],
    ['@SUM(A1)', `'@SUM(A1)`],
    ['\t=cmd', `' =cmd`],
    ['safe = fine', 'safe = fine'],
    ['', ''],
  ]) {
    assert.equal(cleanCell(input), want, JSON.stringify(input));
  }
  const file = join(dir, 'formula.tsv');
  run(file, '=phase', '+d', '-r', '@e', '=o');
  assert.deepEqual(rowsOf(file)[1].slice(1), ["'=phase", "'+d", "'-r", "'@e", "'=o"]);
});

test('the timestamp is UTC ISO 8601 with seconds and a Z', () => {
  assert.equal(timestamp(new Date(Date.UTC(2026, 9, 27, 14, 2, 11, 999))), '2026-10-27T14:02:11Z');
  const file = join(dir, 'ts.tsv');
  run(file, 'p', 'd', 'r', 'e', 'o');
  assert.match(rowsOf(file)[1][0], /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/);
});

test('a trailing newline is added to a log missing one before the new row', () => {
  const file = join(dir, 'nonl.tsv');
  writeFileSync(file, HEADER + '2026-01-01T00:00:00Z\tp\td\tr\te\to');
  appendDecision(file, ['p2', 'd', 'r', 'e', 'o']);
  const rows = rowsOf(file);
  assert.equal(rows.length, 3);
  assert.equal(rows[2][1], 'p2');
});

test('the template shares the header and holds a well-formed row', () => {
  const tpl = readFileSync(join(here, '..', 'decisions.template.tsv'), 'utf8');
  assert.ok(tpl.startsWith(HEADER));
  for (const row of tpl.split('\n').filter(Boolean)) assert.equal(row.split('\t').length, COLUMNS.length);
});
