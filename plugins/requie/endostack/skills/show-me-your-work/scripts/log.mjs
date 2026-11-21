#!/usr/bin/env node
// log: write a single tab-separated row onto the end of a decision log file.
//
// Usage: node log.mjs <logfile> <phase> <decision> <reason> <evidence> <outcome>
//
// Columns: logged_at  phase  decision  reason  evidence  outcome
//   logged_at  UTC time, ISO 8601 with seconds and a Z suffix, set by this script.
//   phase      the workflow step the decision belongs to (plan, build, verify, review, ...).
//   decision   what you chose.
//   reason     why you chose it over the alternatives.
//   evidence   what the choice rests on: a file:line, command output, test name, SHA, URL.
//   outcome    what happened after: passed, reverted, pending, superseded by row N.
//
// Each cell has tabs, CR, and LF replaced by spaces. A cell whose first non-space
// character is = + - @ gets a leading single quote, so a spreadsheet opening the log
// shows evidence text (PR titles, filenames, model output) instead of running it as a
// formula. The header row is written once, when the file is missing or empty, and the
// file is only ever appended to. Exit 0 after appending, 1 on a usage or write error.

import { appendFileSync, mkdirSync, statSync, openSync, readSync, closeSync, realpathSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname } from 'node:path';

export const COLUMNS = ['logged_at', 'phase', 'decision', 'reason', 'evidence', 'outcome'];
export const HEADER = COLUMNS.join('\t') + '\n';
const USAGE = 'usage: node log.mjs <logfile> <phase> <decision> <reason> <evidence> <outcome>';

export function cleanCell(value) {
  const flat = String(value).replace(/[\t\r\n]/g, ' ');
  return /^\s*[=+\-@]/.test(flat) ? `'${flat}` : flat;
}

export function timestamp(date = new Date()) {
  return date.toISOString().replace(/\.\d{3}Z$/, 'Z');
}

function sizeOf(file) {
  try {
    return statSync(file).size;
  } catch (e) {
    if (e.code === 'ENOENT') return 0;
    throw e;
  }
}

function endsWithNewline(file, size) {
  const fd = openSync(file, 'r');
  try {
    const buf = Buffer.alloc(1);
    readSync(fd, buf, 0, 1, size - 1);
    return buf[0] === 0x0a;
  } finally {
    closeSync(fd);
  }
}

export function appendDecision(file, cells, now = new Date()) {
  if (cells.length !== COLUMNS.length - 1) throw new Error(`expected ${COLUMNS.length - 1} values, got ${cells.length}`);
  const dir = dirname(file);
  if (dir && dir !== '.') mkdirSync(dir, { recursive: true });
  const size = sizeOf(file);
  let chunk = '';
  if (size === 0) chunk += HEADER;
  else if (!endsWithNewline(file, size)) chunk += '\n';
  chunk += [timestamp(now), ...cells.map(cleanCell)].join('\t') + '\n';
  // One append call per row, so concurrent writers on a local disk do not interleave within a row.
  appendFileSync(file, chunk, { encoding: 'utf8', flag: 'a' });
  return chunk;
}

export function main(argv, io = { err: (s) => process.stderr.write(s) }) {
  if (argv.length !== COLUMNS.length) {
    io.err(`${USAGE}\n`);
    return 1;
  }
  const [file, ...cells] = argv;
  if (!file) {
    io.err(`${USAGE}\n`);
    return 1;
  }
  try {
    appendDecision(file, cells);
    return 0;
  } catch (e) {
    io.err(`log: cannot append to ${file} (${e.code || e.message})\n`);
    return 1;
  }
}

function isEntry() {
  if (!process.argv[1]) return false;
  try {
    return realpathSync(process.argv[1]) === realpathSync(fileURLToPath(import.meta.url));
  } catch {
    return false;
  }
}

if (isEntry()) process.exitCode = main(process.argv.slice(2));
