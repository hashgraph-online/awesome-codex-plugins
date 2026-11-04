// Process runner. Every GitHub and git call goes through a function with
// the signature run(cmd, args) -> Promise<{ code, stdout, stderr }>, so
// tests can swap in a fake without touching the network.

import { spawn } from 'node:child_process';
import { QueryError, firstLine } from './errors.mjs';

export function processRunner({ cwd, env } = {}) {
  return (cmd, args) =>
    new Promise((resolve) => {
      let stdout = '';
      let stderr = '';
      let child;
      try {
        child = spawn(cmd, args, { cwd, env, stdio: ['ignore', 'pipe', 'pipe'] });
      } catch (err) {
        resolve({ code: 127, stdout: '', stderr: err.message });
        return;
      }
      child.stdout.setEncoding('utf8').on('data', (d) => (stdout += d));
      child.stderr.setEncoding('utf8').on('data', (d) => (stderr += d));
      child.on('error', (err) => resolve({ code: 127, stdout, stderr: stderr || err.message }));
      child.on('close', (code, signal) => resolve({ code: code ?? (signal ? 128 : 1), stdout, stderr }));
    });
}

export function describeCommand(cmd, args) {
  // GraphQL bodies are long; show the operation name instead.
  const shown = args.map((a) => (a.startsWith('query=') ? `query=${a.match(/query\s+(\w+)/)?.[1] ?? '...'}` : a));
  return [cmd, ...shown].join(' ');
}

export function commandFailure(cmd, args, result) {
  const line = firstLine(result.stderr);
  const detail = line || `${describeCommand(cmd, args)} exited ${result.code}`;
  return new QueryError('command-failed', detail);
}

export async function runJson(run, cmd, args) {
  const result = await run(cmd, args);
  if (result.code !== 0) throw commandFailure(cmd, args, result);
  try {
    return JSON.parse(result.stdout);
  } catch {
    throw new QueryError('json-parse', `${describeCommand(cmd, args)} printed output that is not JSON`);
  }
}
