// `node --test skills/tarique-mode/scripts/` resolves this directory as a
// package and loads this file (package.json "main"). It imports every
// *.test.mjs under ./test/ and under each tool's own test/ directory, so
// the whole suite runs under that one command.
import { pathToFileURL } from 'node:url';
import path from 'node:path';
import { readdir } from 'node:fs/promises';

const here = import.meta.dirname;

async function testFiles(dir) {
  try {
    return (await readdir(dir)).filter((f) => f.endsWith('.test.mjs')).sort().map((f) => path.join(dir, f));
  } catch {
    return [];
  }
}

const dirs = [path.join(here, 'test')];
for (const entry of (await readdir(here, { withFileTypes: true })).filter((d) => d.isDirectory() && d.name !== 'test' && d.name !== 'node_modules')) {
  dirs.push(path.join(here, entry.name, 'test'));
}
for (const dir of dirs.sort()) {
  for (const file of await testFiles(dir)) await import(pathToFileURL(file).href);
}
