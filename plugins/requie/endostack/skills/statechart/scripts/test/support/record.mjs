// Re-records the corpus against a live TLC. Run with TLA2TOOLS set:
//   node skills/statechart/scripts/test/support/record.mjs [case ...]
// For each case it saves recordings/<run>.json and expected/<file> and
// expected/exit.txt. Review the diffs before committing.

import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { listCases, caseFiles, normalizeError } from './corpus.mjs';
import { liveRunner, resolveToolchain } from '../../lib/toolchain.mjs';
import { recordingRunner, TAG_PLACEHOLDER } from '../../lib/replay.mjs';
import { runPipeline } from '../../lib/pipeline.mjs';
import { loadView } from '../../lib/view.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const corpus = path.join(here, '..', 'corpus');

// Run only when invoked directly, never when a test runner imports this file.
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url) && !process.env.NODE_TEST_CONTEXT) {
  await record(process.argv.slice(2));
}

async function record(wanted) {
const { java, jar } = await resolveToolchain();

for (const name of listCases(corpus)) {
  if (wanted.length && !wanted.includes(name)) continue;
  const c = caseFiles(corpus, name);
  const recDir = path.join(c.dir, 'recordings');
  const expDir = path.join(c.dir, 'expected');
  fs.rmSync(recDir, { recursive: true, force: true });
  fs.rmSync(expDir, { recursive: true, force: true });
  const workDir = fs.mkdtempSync(path.join(os.tmpdir(), 'statechart-rec-'));
  const run = recordingRunner(liveRunner({ java, jar, workDir }), recDir, TAG_PLACEHOLDER);
  const view = c.view ? await loadView(c.view) : null;
  fs.mkdirSync(expDir, { recursive: true });
  try {
    const result = await runPipeline({ specPath: c.spec, configPath: c.config, view, run, tag: TAG_PLACEHOLDER });
    for (const [f, text] of result.files) fs.writeFileSync(path.join(expDir, f), text);
    fs.writeFileSync(path.join(expDir, 'exit.txt'), `${result.exit}\n`);
    console.log(`${name}: exit ${result.exit}, files ${[...result.files.keys()].join(' ')}`);
  } catch (e) {
    fs.writeFileSync(path.join(expDir, 'exit.txt'), '2\n');
    fs.writeFileSync(path.join(expDir, 'error.txt'), `${normalizeError(e.message, c)}\n`);
    console.log(`${name}: exit 2: ${e.message.split('\n')[0]}`);
  }
  fs.rmSync(workDir, { recursive: true, force: true });
}
}
