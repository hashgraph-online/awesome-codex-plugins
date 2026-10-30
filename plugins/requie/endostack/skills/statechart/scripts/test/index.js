// Node 22 runs `node --test <dir>` by loading the folder as a module (through
// test/package.json "main"), so this file then imports every *.test.mjs
// beside it. When a newer Node expands the folder itself, it runs this file
// by its own path, and the guard below keeps the tests from loading twice.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const loadedAsFolder = path.resolve(process.argv[1] ?? '') === here;
if (loadedAsFolder) {
  for (const f of fs.readdirSync(here).filter((n) => n.endsWith('.test.mjs')).sort()) {
    await import(pathToFileURL(path.join(here, f)).href);
  }
}
