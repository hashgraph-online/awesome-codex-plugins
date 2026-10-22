import { createWriteStream } from 'node:fs';
import { appendFile, open, readFile, stat } from 'node:fs/promises';
import { spawn } from 'node:child_process';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

export async function runHostCommand(spec,{spawnImpl=spawn,drainTimeoutMs=2000,appendLifecycleImpl=appendFile,observationTimeoutMs=1000}={}) {
if (spec?.schema_version !== 1 || !Array.isArray(spec.argv) || !spec.argv.length
  || !spec.argv.every(value => typeof value === 'string') || typeof spec.cwd !== 'string'
  || typeof spec.output_path !== 'string' || typeof spec.stdin_path !== 'string'
  || typeof spec.lifecycle_path !== 'string' || typeof spec.process_id !== 'string'
  || spec.stdin_closed!==undefined&&typeof spec.stdin_closed!=='boolean'
  || !Number.isSafeInteger(drainTimeoutMs)||drainTimeoutMs<1||drainTimeoutMs>2000
  || typeof appendLifecycleImpl!=='function'
  || !Number.isSafeInteger(observationTimeoutMs)||observationTimeoutMs<1||observationTimeoutMs>1000)
  throw new Error('Command runner specification is invalid');
let observations=Promise.resolve(),observationsStopped=false,cancelWrite;
const lifecycleErrors=[];
const recordFailure=(phase,error)=>lifecycleErrors.push({phase,code:typeof error?.code==='string'&&/^[A-Z0-9_]+$/.test(error.code)?error.code:'CODEX_COMMAND_LIFECYCLE_WRITE_FAILED'});
async function boundedObservation(operation) {
  let timer;
  try{return await Promise.race([operation,new Promise((_,reject)=>{
    timer=setTimeout(()=>reject(Object.assign(new Error('Lifecycle evidence write timed out'),{code:'CODEX_COMMAND_LIFECYCLE_TIMEOUT'})),observationTimeoutMs);
  })]);}finally{clearTimeout(timer);}
}
async function writeObservation(fields,cancellable=false) {
  let cancel;
  const cancelled=new Promise((_,reject)=>{cancel=()=>reject(Object.assign(new Error('Lifecycle flush timed out'),{code:'CODEX_COMMAND_LIFECYCLE_TIMEOUT'}));});
  if(cancellable)cancelWrite=cancel;
  try{
    // Attach rejection handlers as the write is created, including synchronous
    // failures. A failed write does not poison the next explicit observation.
    const write=Promise.resolve().then(()=>appendLifecycleImpl(spec.lifecycle_path,JSON.stringify({at:new Date().toISOString(),process_id:spec.process_id,...fields})+'\n'));
    await boundedObservation(cancellable?Promise.race([write,cancelled]):write);
  }catch(error){recordFailure(fields.phase,error);}
  finally{if(cancelWrite===cancel)cancelWrite=undefined;}
}
const observe=fields=>{
  observations=observations.then(async()=>{if(!observationsStopped)await writeObservation(fields,true);});
};

let initialInput;
if(spec.stdin_closed){
  if((await stat(spec.stdin_path)).size>2*1024*1024)throw new Error('Program stdin exceeds its declared boundary');
  initialInput=await readFile(spec.stdin_path);
  if(initialInput.length>2*1024*1024)throw new Error('Program stdin exceeds its declared boundary');
}
const output = createWriteStream(spec.output_path, { flags: 'wx' });
const child = spawnImpl(spec.argv[0], spec.argv.slice(1), { cwd: spec.cwd, env: process.env,
  windowsHide: true, shell: false, stdio: ['pipe', 'pipe', 'pipe'] });
observe({phase:'started',platform:process.platform,runner_pid:process.pid,runner_parent_pid:process.ppid,child_pid:child.pid});
const sources = [child.stdout, child.stderr];
sources.forEach((source,index)=>source.once('close',()=>observe({phase:'stream_close',stream:index===0?'stdout':'stderr'})));
let paused = false;
for (const source of sources) source.on('data', chunk => {
  if (!output.write(chunk) && !paused) {
    paused = true;
    for (const item of sources) item.pause();
    output.once('drain', () => { paused = false; for (const item of sources) item.resume(); });
  }
});

let stdinOffset = 0, polling = false, exited = false, childExited=false;
let stopRequested = false, stopPromise, controlError;
child.stdin.on('error',error=>{controlError=error;child.kill();});
if(spec.stdin_closed){
  stdinOffset=initialInput.length;
  child.stdin.end(initialInput);
}
async function stopChildTree() {
  if (exited || childExited || stopPromise) return stopPromise;
  stopRequested = true;
  stopPromise = new Promise((resolve, reject) => {
    try {
      // The runner is itself inside the App Server command sandbox. Stopping
      // its exact shell child lets the buffered request finish normally; the
      // sandbox owns and reaps any remaining descendants with the runner.
      const signal=process.platform==='win32'?'SIGTERM':'SIGINT',accepted=child.kill(signal);
      observe({phase:'stop_signal_sent',signal,accepted,child_pid:child.pid});
      if(accepted||exited)resolve();
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
        if(control){observe({phase:'stop_control_consumed',child_pid:child.pid,child_exited:childExited});await stopChildTree();}
      }
    }
  } finally { polling = false; }
}
const timer = setInterval(() => { void forwardStdin().catch(error => { controlError=error; child.kill(); }); }, 50);
let drainTimer,pipeHeld=false;
let result;
try { result = await new Promise((resolve, reject) => {
  child.once('error', reject);
  child.once('exit',(code,signal)=>{
    childExited=true;
    observe({phase:'child_exit',exit_code:code,signal});
    drainTimer=setTimeout(()=>{
      pipeHeld=true;exited=true;
      observe({phase:'stdio_drain_timeout',child_pid:child.pid});
      for(const source of sources)source.destroy();
      resolve({code,signal});
    },drainTimeoutMs);
  });
  child.once('close', (code, signal) => { clearTimeout(drainTimer);exited=true;observe({phase:'child_close',exit_code:code,signal});resolve({ code, signal }); });
}); } finally { clearTimeout(drainTimer);clearInterval(timer); }
await forwardStdin();
if (!child.stdin.destroyed) child.stdin.end();
await new Promise((resolve, reject) => { output.once('error', reject); output.end(resolve); });
if(controlError)throw controlError;
const outputBytes = (await stat(spec.output_path)).size;
const exitCode = pipeHeld?1:stopRequested ? 130 : Number.isInteger(result.code) ? result.code : 1;
let receipt={ schema_version: 1, exit_code: exitCode, signal: stopRequested?'SIGINT':result.signal ?? null, output_bytes: outputBytes,
  ...(pipeHeld?{error_code:'CODEX_COMMAND_PIPE_HELD'}:{}) };
try{await boundedObservation(observations);}catch(error){
  recordFailure('lifecycle_flush',error);observationsStopped=true;cancelWrite?.();
}
observationsStopped=true;
const withLifecycleFailure=()=>({...receipt,exit_code:1,command_exit_code:Number.isInteger(result.code)?result.code:null,
  ...(pipeHeld?{execution_error_code:'CODEX_COMMAND_PIPE_HELD'}:{}),error_code:'CODEX_COMMAND_LIFECYCLE_FAILED',
  lifecycle_error_count:lifecycleErrors.length,lifecycle_errors:lifecycleErrors.map(error=>({...error}))});
if(lifecycleErrors.length)receipt=withLifecycleFailure();
// The control receipt remains writable evidence even when the lifecycle file
// is unavailable. This final independent write has the same finite bound.
await writeObservation({phase:'receipt',...receipt});
if(lifecycleErrors.length)receipt=withLifecycleFailure();
return receipt;
}

if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)) {
  const specPath=process.argv[2];
  if(!specPath)throw new Error('Command runner requires a Host-owned specification path');
  const receipt=await runHostCommand(JSON.parse(await readFile(specPath,'utf8')));
  process.stdout.write(JSON.stringify(receipt));process.exitCode=receipt.exit_code;
}
