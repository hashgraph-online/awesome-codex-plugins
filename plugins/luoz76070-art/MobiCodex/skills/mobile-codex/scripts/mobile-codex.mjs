import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const entry = fileURLToPath(new URL('../lib/gateway.mjs', import.meta.url));
if (Number(process.versions.node.split('.')[0]) < 20) {
  console.error('Mobile Codex requires Node.js >= 20.');
  process.exitCode = 1;
} else {
  const child = spawn(process.execPath, [entry, ...process.argv.slice(2)], { stdio: 'inherit' });
  child.on('error', () => { console.error('Mobile Codex CLI could not start. Build the complete plugin package first.'); process.exitCode = 1; });
  child.on('exit', code => { process.exitCode = code ?? 1; });
}
