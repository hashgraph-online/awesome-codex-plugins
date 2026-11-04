// Locates corpus cases: each folder holds one .tla with a matching .cfg,
// an optional view.mjs, recordings/, and expected/.

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

export const CORPUS = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', 'corpus');

export function listCases(dir = CORPUS) {
  return fs.readdirSync(dir).filter((n) => fs.statSync(path.join(dir, n)).isDirectory()).sort();
}

export function caseFiles(dir = CORPUS, name) {
  const caseDir = path.join(dir, name);
  const cfgs = fs.readdirSync(caseDir).filter((f) => f.endsWith('.cfg'));
  if (cfgs.length !== 1) throw new Error(`corpus case ${name} needs exactly one .cfg`);
  const base = cfgs[0].slice(0, -4);
  const view = path.join(caseDir, 'view.mjs');
  return {
    name,
    dir: caseDir,
    spec: path.join(caseDir, `${base}.tla`),
    config: path.join(caseDir, cfgs[0]),
    view: fs.existsSync(view) ? view : null,
    recordings: path.join(caseDir, 'recordings'),
    expected: path.join(caseDir, 'expected'),
  };
}

export function expectedFiles(c) {
  const out = new Map();
  for (const f of fs.readdirSync(c.expected)) {
    if (f === 'exit.txt' || f === 'error.txt') continue;
    out.set(f, fs.readFileSync(path.join(c.expected, f), 'utf8'));
  }
  return {
    exit: Number(fs.readFileSync(path.join(c.expected, 'exit.txt'), 'utf8').trim()),
    error: fs.existsSync(path.join(c.expected, 'error.txt')) ? fs.readFileSync(path.join(c.expected, 'error.txt'), 'utf8').trim() : null,
    files: out,
  };
}

// First line of an error with the case folder replaced, so stored errors do
// not depend on where the repository lives.
export function normalizeError(message, c) {
  return message.split('\n')[0].split(c.dir).join('<case>').trim();
}
