// Low-level file helpers: atomic replace, TSV cell hygiene, TSV read/write.

import path from 'node:path';
import fs from 'node:fs';
import { randomUUID } from 'node:crypto';
import { UserError } from './errors.mjs';

// Write to a hidden temp file beside the target, then rename over it, so a
// reader never sees a half-written file. The temp file is removed on any
// failure.
export function writeAtomic(file, content) {
  const dir = path.dirname(file);
  const tmp = path.join(dir, `.${path.basename(file)}.${process.pid}.${randomUUID()}.tmp`);
  let fd = null;
  try {
    fd = fs.openSync(tmp, 'wx', 0o644);
    fs.writeSync(fd, content);
    fs.fsyncSync(fd);
    fs.closeSync(fd);
    fd = null;
    fs.renameSync(tmp, file);
  } finally {
    if (fd !== null) fs.closeSync(fd);
    fs.rmSync(tmp, { force: true });
  }
}

// Make a value safe for one TSV cell: tabs and line breaks become spaces,
// and a leading formula character gets a quote so spreadsheet apps show it
// as text instead of evaluating it.
export function cleanCell(value) {
  let text = String(value ?? '').replace(/[\t\n\r]/g, ' ');
  if (/^[=+\-@]/.test(text)) text = `'${text}`;
  return text;
}

export function requiredCell(value, label) {
  const text = cleanCell(value);
  if (!text.trim()) throw new UserError(`${label} cannot be blank`);
  return text;
}

// Single-line text for Markdown stores (gates, standing orders).
export function cleanLine(value) {
  return String(value ?? '').replace(/[\r\n]+/g, ' ').trim();
}

export function requiredLine(value, label) {
  const text = cleanLine(value);
  if (!text) throw new UserError(`${label} cannot be blank`);
  return text;
}

export function parsePr(value, label = 'pr') {
  const text = String(value ?? '');
  if (!/^[1-9][0-9]*$/.test(text) || !Number.isSafeInteger(Number(text))) {
    throw new UserError(`${label} needs a whole number above zero, got '${text}'`);
  }
  return Number(text);
}

export function readTsv(file, columns, name) {
  const text = fs.readFileSync(file, 'utf8');
  const lines = text.split('\n');
  if (lines.at(-1) === '') lines.pop();
  if (lines[0] !== columns.join('\t')) throw new UserError(`${name} has an invalid header`);
  return lines.slice(1).map((line, i) => {
    const cells = line.split('\t');
    if (cells.length !== columns.length) throw new UserError(`${name} has a malformed row at line ${i + 2}`);
    return Object.fromEntries(columns.map((c, j) => [c, cells[j]]));
  });
}

export function formatTsv(columns, rows) {
  return [columns.join('\t'), ...rows.map((r) => columns.map((c) => cleanCell(r[c])).join('\t'))].join('\n') + '\n';
}
