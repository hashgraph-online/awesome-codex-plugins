#!/usr/bin/env node
// doctor: check that the tools endostack's scripts call are installed, and say what is missing.
// endostack scripts are plain Node ESM with no npm dependencies, so there is nothing to install;
// this replaces a dependency bootstrap with a presence check.
//
// Usage: node doctor.mjs [--json]
//
// Required: node >= 22, git. Recommended: gh (PR state in worktree-audit, PR watching),
// authenticated. Optional: java (statechart model checking).
// Exit 0 when every required tool is present, 1 otherwise. Missing optional tools only warn.

import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { realpathSync } from 'node:fs';

export const MIN_NODE_MAJOR = 22;

export const TOOLS = [
  {
    name: 'node',
    level: 'required',
    probe: () => ({ ok: true, version: process.versions.node }),
    check: (v) => Number(v.split('.')[0]) >= MIN_NODE_MAJOR || `version ${v} is older than ${MIN_NODE_MAJOR}`,
    fix: `Install Node ${MIN_NODE_MAJOR} or newer from https://nodejs.org or with your version manager.`,
  },
  {
    name: 'git',
    level: 'required',
    cmd: ['git', '--version'],
    parse: (out) => /(\d+\.\d+(?:\.\d+)?)/.exec(out)?.[1],
    fix: 'Install git from https://git-scm.com/downloads.',
  },
  {
    name: 'gh',
    level: 'recommended',
    cmd: ['gh', '--version'],
    parse: (out) => /gh version (\S+)/.exec(out)?.[1],
    extra: (run) => {
      const r = run(['gh', 'auth', 'status']);
      return r.status === 0 ? null : 'not authenticated (run `gh auth login`)';
    },
    fix: 'Install the GitHub CLI from https://cli.github.com and run `gh auth login`. Without it, PR columns stay empty.',
  },
  {
    name: 'java',
    level: 'optional',
    cmd: ['java', '-version'],
    parse: (out) => /version "([^"]+)"/.exec(out)?.[1] || /openjdk (\S+)/.exec(out)?.[1],
    fix: 'Install a Java 11+ runtime only if you use the statechart skill.',
  },
];

export function defaultRun(argv) {
  const r = spawnSync(argv[0], argv.slice(1), {
    encoding: 'utf8',
    stdio: ['ignore', 'pipe', 'pipe'],
    shell: false,
    windowsHide: true,
    timeout: 15_000,
  });
  return { status: r.error ? null : r.status, out: `${r.stdout || ''}${r.stderr || ''}` };
}

export function diagnose(run = defaultRun, tools = TOOLS) {
  return tools.map((t) => {
    const res = { name: t.name, level: t.level, found: false, version: null, problem: null, fix: t.fix };
    if (t.probe) {
      const p = t.probe();
      res.found = p.ok;
      res.version = p.version;
    } else {
      const r = run(t.cmd);
      res.found = r.status === 0;
      if (res.found) res.version = t.parse(r.out) || 'unknown';
    }
    if (!res.found) {
      res.problem = 'not found on PATH';
      return res;
    }
    if (t.check) {
      const c = t.check(res.version);
      if (c !== true) res.problem = c;
    }
    if (!res.problem && t.extra) res.problem = t.extra(run);
    return res;
  });
}

export function format(results) {
  const lines = [];
  for (const r of results) {
    const mark = !r.problem ? 'ok  ' : r.level === 'required' ? 'FAIL' : 'warn';
    const ver = r.version ? ` ${r.version}` : '';
    lines.push(`${mark}  ${r.name}${ver} (${r.level})${r.problem ? `: ${r.problem}` : ''}`);
  }
  const missing = results.filter((r) => r.problem);
  if (missing.length) {
    lines.push('', 'To fix:');
    for (const r of missing) lines.push(`  ${r.name}: ${r.fix}`);
  }
  const failed = results.filter((r) => r.problem && r.level === 'required').length;
  lines.push('', failed ? `doctor: ${failed} required tool(s) missing or too old` : 'doctor: all required tools present');
  return lines.join('\n') + '\n';
}

export function main(argv, io = { out: (s) => process.stdout.write(s), err: (s) => process.stderr.write(s) }, run = defaultRun) {
  const unknown = argv.filter((a) => a !== '--json');
  if (unknown.length) {
    io.err(`usage: node doctor.mjs [--json]\n`);
    return 2;
  }
  const results = diagnose(run);
  io.out(argv.includes('--json') ? JSON.stringify(results, null, 2) + '\n' : format(results));
  return results.some((r) => r.problem && r.level === 'required') ? 1 : 0;
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
