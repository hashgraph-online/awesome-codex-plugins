#!/usr/bin/env node
// statechart: model-check a TLA+ spec with TLC, then write report.md,
// chart.mmd, and TLC's output into a new folder.
//
// The supervisor (default mode) validates arguments and the output folder,
// starts a worker in its own process group, and a janitor shell that kills
// the worker group and removes temp folders if the supervisor dies for any
// reason. The worker (--worker) does the check and writes into staging.

import { spawn } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { randomBytes } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { constants as osConstants } from 'node:os';

const SELF = fileURLToPath(import.meta.url);

export const USAGE = `usage: statechart SPEC.tla [--config FILE] [--view FILE] [--out DIR]

Model-checks SPEC.tla with TLC and writes a report and a Mermaid state chart.

  --config FILE  TLC config (default: SPEC.cfg beside the spec)
  --view FILE    ES module that labels the chart. Optional exports:
                   state(vars)  label: string, array (parent states), or object (regions)
                   step(action, from, to)  arrow label, or null to hide the step
                   group(vars)  group name; needs colors
                   colors       { group: color }, color one of
                                blue, orange, purple, yellow, teal, tan, pink
                   title        chart title
  --out DIR      output folder (default: SPEC-chart beside the spec); it must
                 not exist yet or must be empty

Output files: report.md (also printed), chart.mmd, tlc.out (TLC on the config
as written), and tlc-RULE.out for each broken rule whose path the chart does
not show. With more than 500 distinct states the chart shows only bug paths,
and no chart is written when nothing breaks.

Toolchain: set TLA2TOOLS to a tla2tools.jar and JAVA to a Java 11+ binary
(default: java on PATH). Without TLA2TOOLS the pinned jar is downloaded once
into ~/.cache/endostack/statechart.

Exit codes: 0 every rule holds; 1 some rule breaks; 2 error (bad input, TLC
or SANY failure, view error, output folder conflict); 130/143 interrupted.
`;

class UsageError extends Error {}
class StopError extends Error {}

export function parseArgs(argv) {
  const out = { spec: null, config: null, view: null, out: null };
  const positionals = [];
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    const flag = /^--(config|view|out)(?:=(.*))?$/.exec(a);
    if (flag) {
      let v = flag[2];
      if (v === undefined) {
        v = argv[++i];
        if (v === undefined) throw new UsageError(`--${flag[1]} needs a value.`);
      }
      if (out[flag[1]] !== null) throw new UsageError(`--${flag[1]} is given twice.`);
      out[flag[1]] = v;
      continue;
    }
    if (a === '--') { positionals.push(...argv.slice(i + 1)); break; }
    if (a.startsWith('-') && a !== '-') throw new UsageError(`Unknown option ${a}.`);
    positionals.push(a);
  }
  if (positionals.length !== 1) {
    throw new UsageError(positionals.length === 0 ? 'Give exactly one spec file.' : `Give exactly one spec file, not ${positionals.length}.`);
  }
  out.spec = positionals[0];
  const base = out.spec.endsWith('.tla') ? out.spec.slice(0, -4) : out.spec;
  out.config ??= `${base}.cfg`;
  out.out ??= `${base}-chart`;
  return out;
}

function checkOutDir(dir) {
  let st;
  try {
    st = fs.lstatSync(dir);
  } catch (e) {
    if (e.code === 'ENOENT') return;
    throw new StopError(`Cannot use the output folder ${dir}: ${e.message}`);
  }
  if (st.isSymbolicLink()) {
    try { fs.statSync(dir); } catch { throw new StopError(`The output folder ${dir} is a broken symbolic link.`); }
  }
  let entries;
  try { entries = fs.readdirSync(dir); } catch (e) {
    throw new StopError(`Cannot list the output folder ${dir}: ${e.message}`);
  }
  if (entries.length) {
    throw new StopError(`The output folder ${dir} already contains ${entries.sort()[0]}. statechart only writes to a new or empty folder; pass a fresh --out.`);
  }
}

function nearestExisting(p) {
  let cur = path.resolve(p);
  for (;;) {
    const parent = path.dirname(cur);
    if (fs.existsSync(parent) || parent === cur) return parent;
    cur = parent;
  }
}

function signalNumber(sig) {
  return osConstants.signals[sig] ?? 0;
}

async function supervise(argv) {
  let args;
  try {
    args = parseArgs(argv);
  } catch (e) {
    if (e instanceof UsageError) { process.stderr.write(`statechart: ${e.message}\n\n${USAGE}`); return 2; }
    throw e;
  }
  try {
    if (!fs.existsSync(args.spec)) throw new StopError(`The spec ${args.spec} does not exist.`);
    if (!fs.existsSync(args.config)) throw new StopError(`The config ${args.config} does not exist. Pass the right file with --config.`);
    if (args.view && !fs.existsSync(args.view)) throw new StopError(`The view ${args.view} does not exist.`);
    checkOutDir(args.out);
  } catch (e) {
    if (e instanceof StopError) { process.stderr.write(`statechart: ${e.message}\n`); return 2; }
    throw e;
  }

  const dest = path.resolve(args.out);
  const parent = nearestExisting(dest);
  const staging = path.join(parent, `.${path.basename(dest)}.statechart-${randomBytes(6).toString('hex')}`);
  fs.mkdirSync(staging);
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'statechart-'));

  const job = { spec: path.resolve(args.spec), config: path.resolve(args.config), view: args.view ? path.resolve(args.view) : null, staging };
  const worker = spawn(process.execPath, [...process.execArgv, SELF, '--worker', JSON.stringify(job)], {
    detached: true,
    stdio: ['ignore', 'inherit', 'inherit'],
    env: { ...process.env, TMPDIR: tmp },
  });
  const pgid = worker.pid;
  const janitorScript = 'cat >/dev/null; kill -KILL -"$1" 2>/dev/null; rm -rf "$2" "$3"';
  const janitor = spawn('/bin/sh', ['-c', janitorScript, 'janitor', String(pgid), staging, tmp], {
    detached: true, stdio: ['pipe', 'ignore', 'ignore'],
  });
  janitor.unref();

  const killGroup = () => { try { process.kill(-pgid, 'SIGKILL'); } catch { /* already gone */ } };
  const cleanup = () => {
    killGroup();
    fs.rmSync(staging, { recursive: true, force: true });
    fs.rmSync(tmp, { recursive: true, force: true });
    try { janitor.kill('SIGKILL'); } catch { /* gone */ }
    janitor.stdin.destroy();
  };

  const outcome = await new Promise((resolve) => {
    const onSig = (sig) => resolve({ signal: sig });
    process.once('SIGINT', onSig);
    process.once('SIGTERM', onSig);
    worker.on('exit', (code, signal) => resolve({ code, workerSignal: signal }));
    worker.on('error', (e) => resolve({ error: e }));
  });
  killGroup();

  try {
    if (outcome.signal) {
      process.stderr.write(`statechart: stopped by ${outcome.signal}; nothing was written.\n`);
      return 128 + signalNumber(outcome.signal);
    }
    if (outcome.workerSignal) {
      process.stderr.write(`statechart: the check was killed by ${outcome.workerSignal}; nothing was written.\n`);
      return 2;
    }
    if (outcome.error) {
      process.stderr.write(`statechart: could not start the check: ${outcome.error.message}\n`);
      return 2;
    }
    const done = path.join(staging, 'done');
    if ((outcome.code === 0 || outcome.code === 1) && fs.existsSync(done)) {
      try {
        if (fs.existsSync(dest)) fs.rmdirSync(dest);
        fs.mkdirSync(path.dirname(dest), { recursive: true });
        fs.renameSync(done, dest);
      } catch (e) {
        let first = null;
        try { first = fs.readdirSync(dest).sort()[0]; } catch { /* unreadable */ }
        process.stderr.write(`statechart: the output folder ${args.out} ${first ? `gained ${first} during the run` : `could not be written (${e.message})`}; nothing was written.\n`);
        return 2;
      }
      process.stdout.write(fs.readFileSync(path.join(dest, 'report.md'), 'utf8'));
      process.stdout.write(`\nWrote ${args.out}\n`);
      return outcome.code;
    }
    return 2;
  } finally {
    cleanup();
  }
}

async function work(jobJson) {
  const job = JSON.parse(jobJson);
  const { loadView, ViewError, describeThrown } = await import('./lib/view.mjs');
  const { resolveToolchain, liveRunner } = await import('./lib/toolchain.mjs');
  const { runPipeline } = await import('./lib/pipeline.mjs');
  const { writeFiles } = await import('./lib/files.mjs');
  try {
    const view = job.view ? await loadView(job.view) : null;
    const tag = randomBytes(16).toString('hex');
    let run;
    if (process.env.STATECHART_REPLAY) {
      // Test hook: serve recorded TLC output instead of running Java.
      const { replayRunner } = await import('./lib/replay.mjs');
      const inner = replayRunner(process.env.STATECHART_REPLAY, tag);
      const delay = Number(process.env.STATECHART_REPLAY_DELAY_MS || 0);
      run = async (req) => {
        if (delay) await new Promise((r) => setTimeout(r, delay));
        return inner(req);
      };
    } else {
      const { java, jar } = await resolveToolchain();
      const workDir = fs.mkdtempSync(path.join(process.env.TMPDIR || os.tmpdir(), 'runs-'));
      run = liveRunner({ java, jar, workDir });
      if (process.env.STATECHART_RECORD) {
        const { recordingRunner } = await import('./lib/replay.mjs');
        run = recordingRunner(run, process.env.STATECHART_RECORD, tag);
      }
    }
    const result = await runPipeline({ specPath: job.spec, configPath: job.config, view, run, tag });
    const draft = path.join(job.staging, 'draft');
    fs.mkdirSync(draft);
    writeFiles(draft, result.files);
    fs.renameSync(draft, path.join(job.staging, 'done'));
    return result.exit;
  } catch (e) {
    const msg = e instanceof ViewError || e instanceof Error ? e.message : describeThrown(e);
    process.stderr.write(`statechart: ${msg}\n`);
    return 2;
  }
}

if (process.argv[2] === '--worker') {
  process.exitCode = await work(process.argv[3]);
} else if (process.argv[1] && fs.realpathSync(process.argv[1]) === fs.realpathSync(SELF)) {
  process.exitCode = await supervise(process.argv.slice(2));
}
