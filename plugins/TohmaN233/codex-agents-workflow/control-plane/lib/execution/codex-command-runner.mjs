import { createWriteStream } from 'node:fs';
import { open, readFile, stat } from 'node:fs/promises';
import { spawn } from 'node:child_process';

const specPath = process.argv[2];
if (!specPath) throw new Error('Command runner requires a Host-owned specification path');
const spec = JSON.parse(await readFile(specPath, 'utf8'));
if (spec?.schema_version !== 1 || !Array.isArray(spec.argv) || !spec.argv.length
  || !spec.argv.every(value => typeof value === 'string') || typeof spec.cwd !== 'string'
  || typeof spec.output_path !== 'string' || typeof spec.stdin_path !== 'string')
  throw new Error('Command runner specification is invalid');

const output = createWriteStream(spec.output_path, { flags: 'wx' });
const child = spawn(spec.argv[0], spec.argv.slice(1), { cwd: spec.cwd, env: process.env,
  windowsHide: true, shell: false, stdio: ['pipe', 'pipe', 'pipe'] });
const sources = [child.stdout, child.stderr];
let paused = false;
for (const source of sources) source.on('data', chunk => {
  if (!output.write(chunk) && !paused) {
    paused = true;
    for (const item of sources) item.pause();
    output.once('drain', () => { paused = false; for (const item of sources) item.resume(); });
  }
});

let stdinOffset = 0, polling = false, exited = false;
let stopRequested = false, stopPromise, controlError;
async function stopChildTree() {
  if (exited || stopPromise) return stopPromise;
  stopRequested = true;
  stopPromise = new Promise((resolve, reject) => {
    try {
      // The runner is itself inside the App Server command sandbox. Stopping
      // its exact shell child lets the buffered request finish normally; the
      // sandbox owns and reaps any remaining descendants with the runner.
      if(child.kill(process.platform==='win32'?'SIGTERM':'SIGINT')||exited)resolve();
      else reject(Object.assign(new Error('Owned command rejected the stop signal'),{code:'COMMAND_TREE_STOP_FAILED'}));
    } catch(error){reject(error);}
  });
  return stopPromise;
}
async function forwardStdin() {
  if (polling || exited) return;
  polling = true;
  try {
    const size = (await stat(spec.stdin_path)).size;
    if (size > stdinOffset) {
      const count = size - stdinOffset, buffer = Buffer.allocUnsafe(count), handle = await open(spec.stdin_path, 'r');
      let bytesRead;
      try { ({ bytesRead } = await handle.read(buffer, 0, count, stdinOffset)); }
      finally { await handle.close(); }
      stdinOffset += bytesRead;
      if (bytesRead) {
        const bytes=buffer.subarray(0,bytesRead),control=bytes.includes(3);
        const forwarded=control?Buffer.from(bytes.filter(value=>value!==3)):bytes;
        if(forwarded.length&&!child.stdin.destroyed)child.stdin.write(forwarded);
        if(control)await stopChildTree();
      }
    }
  } finally { polling = false; }
}
const timer = setInterval(() => { void forwardStdin().catch(error => { controlError=error; child.kill(); }); }, 50);
const result = await new Promise((resolve, reject) => {
  child.once('error', reject);
  child.once('close', (code, signal) => { exited=true; resolve({ code, signal }); });
});
clearInterval(timer);
await forwardStdin().catch(() => {});
if (!child.stdin.destroyed) child.stdin.end();
await new Promise((resolve, reject) => { output.once('error', reject); output.end(resolve); });
if(controlError)throw controlError;
const outputBytes = (await stat(spec.output_path)).size;
const exitCode = stopRequested ? 130 : Number.isInteger(result.code) ? result.code : 1;
process.stdout.write(JSON.stringify({ schema_version: 1, exit_code: exitCode, signal: stopRequested?'SIGINT':result.signal ?? null, output_bytes: outputBytes }));
process.exitCode = exitCode;
