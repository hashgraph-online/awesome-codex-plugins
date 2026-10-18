import {open,lstat,readFile,unlink} from 'node:fs/promises';
import {join,resolve,isAbsolute,dirname,relative} from 'node:path';
import {randomUUID,createHash} from 'node:crypto';
import {ensureDirectory,noSymlinks,requireValue} from './workflow-paths.mjs';
import {canonicalJSON,digest} from './workflow-revisions.mjs';
import {writeDurableJSON} from './workflow-events.mjs';
import {syncDirectory,admissionTrace} from './workflow-store.mjs';
import {spawn} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {finished} from 'node:stream/promises';
import {verifiedRetirementReceipt,retireOwnedFile} from './owned-file-retirement.mjs';
import {foregroundActivityCount,onForegroundIdle} from './foreground-activity.mjs';

// Activity-triggered, portable Host policy. Retention eligibility is unchanged;
// automatic removal now occurs on the first successful startup after this
// one-minute interval, rather than delaying every startup for a full audit.
// Idle Hosts need no timer. Manual cleanup/list keep their complete audits.
export const HISTORY_MAINTENANCE_INTERVAL_MS=60_000;
const managers=new Map();
let acceptingManagers=true;
const rootKey=root=>process.platform==='win32'?resolve(root).toLowerCase():resolve(root);
const uuid=/^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/;
const fail=(code,message,details={})=>Object.assign(new Error(message),{code,...details});
const exact=(a,b)=>a.job_id===b.job_id&&a.owner_token===b.owner_token&&a.owner_pid===b.owner_pid&&a.created_at===b.created_at&&a.kind===b.kind;
const codeOf=error=>typeof error?.code==='string'&&/^[a-zA-Z0-9_]{1,128}$/.test(error.code)?error.code:error instanceof SyntaxError?'SyntaxError':'RUN_HISTORY_MAINTENANCE_FAILED';
const carriedDiagnostic=Symbol('history diagnostic');
const alreadyPersisted=Symbol('observed durable diagnostic');
export function diagnostic(error,depth=0,runRoot){
 if(error?.[carriedDiagnostic]){
  if(runRoot&&Object.hasOwn(error[carriedDiagnostic],'retirements'))requireHistoryRetirementReceipts(error[carriedDiagnostic].retirements,runRoot);
  return error[carriedDiagnostic];
 }
 const code=codeOf(error),message=String(error?.message??error);
 // Error text/details can contain credentials or tool output. Persist exact
 // original code and hashes, never their bodies. Bound lineage samples while
 // preserving the complete count/hash when a partial family is large.
 const result={code,message:`History maintenance requires attention (${code})`,message_sha256:digest(message),message_bytes:Buffer.byteLength(message)};
 for(const key of ['family_run_ids','deleted_run_ids'])if(Array.isArray(error?.[key])){
  const values=error[key];result[`${key}_count`]=values.length;result[`${key}_sha256`]=digest(canonicalJSON(values));
  result[key]=values.slice(0,8).filter(id=>typeof id==='string'&&/^[a-z0-9][a-z0-9._-]{0,63}$/.test(id));
 }
 if(Number.isSafeInteger(error?.details?.failed_read_count))result.failed_read_count=error.details.failed_read_count;
 if(error?.cause&&depth===0)result.cause=diagnostic(error.cause,1);
 if(error instanceof AggregateError){result.failure_count=error.errors.length;if(depth===0)result.failures=error.errors.slice(0,4).map(value=>diagnostic(value,1));}
 if(runRoot&&depth===0){const retirements=historyRetirementReceipts(error,runRoot);if(retirements.length)result.retirements=retirements;}
 return result;
}
const fromDiagnostic=error=>Object.assign(fail(error.code,error.message,error),{[carriedDiagnostic]:error});
const cancelled=()=>fail('RUN_HISTORY_CANCELLED','Host stopped its history audit before confirmed completion');

async function boundedJSON(path,{optional=false,initializationMs=0}={}){
 try{
  for(;;){
  await noSymlinks(path);const info=await lstat(path);
  requireValue(info.isFile()&&info.nlink===1&&info.size<=16_384,'RUN_HISTORY_MAINTENANCE_RECORD','Maintenance record must be one bounded regular file',{record_path:path});
  const bytes=await readFile(path);
  requireValue(bytes.length<=16_384,'RUN_HISTORY_MAINTENANCE_RECORD','Maintenance record grew beyond its bound',{record_path:path});
  if(!bytes.length&&initializationMs){
   const created=info.birthtimeMs>0?info.birthtimeMs:info.ctimeMs,remaining=initializationMs-(Date.now()-created);
   requireValue(remaining>0,'RUN_HISTORY_MAINTENANCE_INITIALIZATION','Exclusive maintenance claim initialization did not settle within its bound',{record_path:path});
   await new Promise(r=>setTimeout(r,Math.min(25,remaining)));continue;
  }
  try{return JSON.parse(bytes);}catch(cause){throw fail('RUN_HISTORY_MAINTENANCE_RECORD','Maintenance record JSON is malformed',{record_path:path,cause});}
  }
 }catch(error){if(optional&&error.code==='ENOENT'&&resolve(error.path)===path)return null;throw error;}
}
function ownership(value){
 requireValue(value?.schema_version===1&&uuid.test(value.job_id)&&uuid.test(value.owner_token)
  &&Number.isSafeInteger(value.owner_pid)&&value.owner_pid>0&&Number.isSafeInteger(value.created_at)&&value.created_at>=0,
 'RUN_HISTORY_MAINTENANCE_OWNERSHIP','Maintenance requires an exact bounded job and owner identity');
 return value;
}
function receipt(value){
 ownership(value);
 requireValue(Object.keys(value).every(key=>['schema_version','job_id','owner_token','owner_pid','worker_pid','kind','created_at','due_at','phase','outcome','finished_at','audit','error'].includes(key))
  &&(!Object.hasOwn(value,'kind')||value.kind==='cancelled_diagnostic_recovery')
  &&(!Object.hasOwn(value,'worker_pid')||Number.isSafeInteger(value.worker_pid)&&value.worker_pid>0)
  &&['claimed','auditing','settled','stopping'].includes(value.phase)
  &&['pending','succeeded','failed','cancelled','stop_pending'].includes(value.outcome)
  &&Number.isSafeInteger(value.due_at)&&value.due_at>=value.created_at
  &&(value.phase==='settled'?['succeeded','failed','cancelled'].includes(value.outcome):['pending','stop_pending'].includes(value.outcome))
  &&(['failed','cancelled','stop_pending'].includes(value.outcome)?typeof value.error?.code==='string'&&typeof value.error.message==='string':!value.error),
 'RUN_HISTORY_MAINTENANCE_RECEIPT','Maintenance phase/outcome/due time is invalid');
 return value;
}
function live(owner){
 try{process.kill(owner.owner_pid,0);}
 catch(cause){throw fail(cause.code==='ESRCH'?'RUN_HISTORY_MAINTENANCE_ORPHANED':'RUN_HISTORY_MAINTENANCE_OWNER_UNVERIFIED',
  'Maintenance owner requires explicit inspection; no automatic takeover',{owner_pid:owner.owner_pid,job_id:owner.job_id,cause});}
}
async function durableExclusive(path,value){
 const bytes=canonicalJSON(value)+'\n';
 requireValue(Buffer.byteLength(bytes)<=16_384,'RUN_HISTORY_MAINTENANCE_RECORD','Maintenance record exceeds its bound');
 const handle=await open(path,'wx',0o600);
 try{await handle.writeFile(bytes);await handle.sync();}finally{await handle.close();}
 await syncDirectory(dirname(path));
}

export function runHistoryMaintenanceFor(options){
 requireValue(acceptingManagers,'RUN_HISTORY_MAINTENANCE_CLOSED','History maintenance Host is closed');
 const key=rootKey(options.runRoot);
 if(!managers.has(key))managers.set(key,new RunHistoryMaintenance(options));
 return managers.get(key);
}
export function stopRunHistoryMaintenanceAdmission(){acceptingManagers=false;}
export async function closeRunHistoryMaintenances(){
 const settled=await Promise.allSettled([...managers.entries()].map(async([key,manager])=>{await manager.close();managers.delete(key);}));
 const errors=settled.filter(x=>x.status==='rejected').map(x=>x.reason);
 if(errors.length)throw new AggregateError(errors,'Host history maintenance shutdown requires attention');
}

// Explicit operator recovery only. No automatic caller uses this operation.
// A known legacy cancellation diagnostic can be archived only with exact byte
// hashes, an unchanged settled cancellation, no claim and confirmed dead PIDs.
// All other diagnostics/uncertain owners remain blocking evidence.
export async function archiveCancelledHistoryDiagnostic({runRoot,jobId,ownerPid,receiptSha256,diagnosticSha256,readRecord=boundedJSON}){
 requireValue(isAbsolute(runRoot)&&uuid.test(jobId)&&Number.isSafeInteger(ownerPid)&&ownerPid>0
  &&/^[a-f0-9]{64}$/.test(receiptSha256)&&/^[a-f0-9]{64}$/.test(diagnosticSha256)&&typeof readRecord==='function',
  'RUN_HISTORY_RECOVERY_ARGUMENTS','Recovery requires one exact cancelled job and byte hashes');
 const directory=join(resolve(runRoot),'.run-locks','.history-maintenance'),lockPath=join(directory,'.writer.lock');
 const receiptPath=join(directory,'receipt.json'),diagnosticPath=join(directory,'diagnostic.json');
 const archivePath=join(directory,`recovered-cancelled-${jobId}-${diagnosticSha256}.json`);
 const assertDead=pid=>{
  try{process.kill(pid,0);}catch(error){if(error.code==='ESRCH')return;throw fail('RUN_HISTORY_RECOVERY_OWNER_UNVERIFIED','Recovery cannot confirm owner termination',{cause:error});}
  throw fail('RUN_HISTORY_RECOVERY_OWNER_LIVE','Recovery requires confirmed absent owner processes');
 };
 async function verify(){
  const saved=receipt(await readRecord(receiptPath)),observed=await readRecord(diagnosticPath);
  requireValue(saved.job_id===jobId&&saved.owner_pid===ownerPid&&saved.phase==='settled'&&saved.outcome==='cancelled'
   &&saved.error?.code==='RUN_HISTORY_CANCELLED'&&observed.schema_version===1&&observed.error?.code==='RUN_HISTORY_CANCELLED',
   'RUN_HISTORY_RECOVERY_IDENTITY','Recovery evidence is not the exact settled cancelled job');
  const [savedBytes,observedBytes]=await Promise.all([readFile(receiptPath),readFile(diagnosticPath)]);
  requireValue(savedBytes.length<=16_384&&observedBytes.length<=16_384&&digest(savedBytes)===receiptSha256&&digest(observedBytes)===diagnosticSha256,
   'RUN_HISTORY_RECOVERY_HASH','Recovery evidence changed from the approved exact byte hashes');
  assertDead(saved.owner_pid);if(saved.worker_pid)assertDead(saved.worker_pid);
  return observedBytes;
 }
 await verify();
 const now=Date.now(),recoveryOwner={schema_version:1,kind:'cancelled_diagnostic_recovery',job_id:randomUUID(),owner_token:randomUUID(),owner_pid:process.pid,
  created_at:now,due_at:now+HISTORY_MAINTENANCE_INTERVAL_MS,phase:'claimed',outcome:'pending'};
 const recoveryReceiptPath=join(directory,`recovery-${recoveryOwner.job_id}.json`);
 // wx both confirms absent claim and fences peers while the exact CAS is
 // rechecked. A conflicting/live/dead claim is never removed or taken over.
 await durableExclusive(lockPath,recoveryOwner);
 let failure;
 try{
  const bytes=await verify();
  const handle=await open(archivePath,'wx',0o600);
  try{await handle.writeFile(bytes);await handle.sync();}finally{await handle.close();}
  await syncDirectory(directory);
  requireValue(digest(await readFile(archivePath))===diagnosticSha256,'RUN_HISTORY_RECOVERY_ARCHIVE','Cancelled diagnostic archive did not preserve exact bytes');
  await verify();
  requireValue(exact(receipt(await boundedJSON(lockPath)),recoveryOwner),'RUN_HISTORY_MAINTENANCE_OWNERSHIP','Recovery claim changed; retain evidence');
  await unlink(diagnosticPath);await syncDirectory(directory);
 }catch(error){failure=error;}
 // A peer can observe this short claim and then recapture its release. Give
 // that exact job its own terminal evidence without replacing legacy history
 // receipt bytes. Recovery is not an audit and grants no audit cooldown.
 const recoveryReceipt={...recoveryOwner,phase:'settled',outcome:failure?'failed':'succeeded',finished_at:Date.now(),due_at:now,
  ...(failure?{error:diagnostic(failure)}:{})};
 try{await writeDurableJSON(recoveryReceiptPath,recoveryReceipt);}catch(error){
  if(failure)throw new AggregateError([failure,error],'Cancellation recovery receipt requires attention');throw error;
 }
 if(failure)throw failure; // retain exact claim on any uncertain recovery effect
 try{
  requireValue(exact(receipt(await boundedJSON(lockPath)),recoveryOwner),'RUN_HISTORY_MAINTENANCE_OWNERSHIP','Recovery claim changed; retain evidence');
  await retireOwnedFile(lockPath,{stagingRoot:join(directory,'.pending'),validate:bytes=>{
   const current=receipt(JSON.parse(bytes));
   requireValue(exact(current,recoveryOwner),'RUN_HISTORY_MAINTENANCE_OWNERSHIP','Recovery claim changed; retain evidence');return current.owner_pid;
  }});await syncDirectory(directory);
 }catch(error){if(failure)throw new AggregateError([failure,error],'Cancellation recovery and exact claim release require attention');throw error;}
 return {job_id:jobId,owner_pid:ownerPid,archive_path:archivePath,recovery_receipt_path:recoveryReceiptPath,diagnostic_sha256:diagnosticSha256,receipt_sha256:receiptSha256};
}

// A claim belongs to the Host; its exact child runs the expensive audit. IPC
// carries only bounded job metadata, never Run inputs or controller authority.
// Completion is usable only after the child process has closed, including its
// IPC/stdio handles. Protocol and termination failures cannot release a claim
// while a child may still be executing a read or deletion.
export function requireHistoryRetirementReceipts(values,runRoot){
 requireValue(isAbsolute(runRoot)&&Array.isArray(values)&&values.length>0&&Buffer.byteLength(JSON.stringify(values))<=8192,
  'RUN_HISTORY_WORKER_RETIREMENT','Worker retirement metadata exceeds its typed bound');
 const prefix='.run-locks/.store-operation/',phases=['retirement_allocate','retirement_rename','retirement_verify','retirement_delete','retirement_directory_cleanup'];
 for(const value of values){
  requireValue(value&&typeof value==='object'&&!Array.isArray(value)
   &&Object.keys(value).every(key=>['phase','canonical_path','retired_path','retired','deleted','cause_code','cause_errno','owner_pid','cleanup_waited_ms','cleanup_checks'].includes(key))
   &&phases.includes(value.phase)&&typeof value.retired==='boolean'&&typeof value.deleted==='boolean'&&(!value.deleted||value.retired),
   'RUN_HISTORY_WORKER_RETIREMENT','Worker retirement receipt is not typed metadata');
  const canonical=value.canonical_path;
  requireValue(typeof canonical==='string'&&(canonical==='.writer.lock'||canonical===prefix+'.writer.lock'||canonical==='.run-locks/.history-maintenance/.writer.lock'
   ||/^\.run-locks\/run-[a-z0-9][a-z0-9._-]{0,63}\/\.writer\.lock$/.test(canonical)
   ||/^run-[a-z0-9][a-z0-9._-]{0,63}\.run\/\.writer\.lock$/.test(canonical)
   ||canonical.startsWith(prefix+'.admission-queue/ticket-')&&canonical.endsWith('.json')&&uuid.test(canonical.slice((prefix+'.admission-queue/ticket-').length,-5))),
   'RUN_HISTORY_WORKER_RETIREMENT','Worker canonical retirement identity is outside its exact admission');
  const pending=canonical.slice(0,canonical.lastIndexOf('/')+1)+'.pending/retired-owner-';
  requireValue(typeof value.retired_path==='string'&&value.retired_path.startsWith(pending)&&value.retired_path.endsWith('/record.json')
   &&uuid.test(value.retired_path.slice(pending.length,-'/record.json'.length)),
   'RUN_HISTORY_WORKER_RETIREMENT','Worker private retirement identity is outside its exact admission');
  if(Object.hasOwn(value,'cause_code'))requireValue(typeof value.cause_code==='string'&&/^[a-zA-Z0-9_]{1,128}$/.test(value.cause_code),
   'RUN_HISTORY_WORKER_RETIREMENT','Worker retirement error code is invalid');
  if(Object.hasOwn(value,'cause_errno'))requireValue(Number.isSafeInteger(value.cause_errno),'RUN_HISTORY_WORKER_RETIREMENT','Worker retirement errno is invalid');
  if(Object.hasOwn(value,'owner_pid'))requireValue(Number.isSafeInteger(value.owner_pid)&&value.owner_pid>0,'RUN_HISTORY_WORKER_RETIREMENT','Worker verified owner PID is invalid');
  for(const key of ['cleanup_waited_ms','cleanup_checks'])if(Object.hasOwn(value,key))
   requireValue(Number.isSafeInteger(value[key])&&value[key]>=0&&value[key]<=2147483647,
    'RUN_HISTORY_WORKER_RETIREMENT','Worker retirement cleanup observation is invalid');
 }
 return values;
}
function historyRetirementReceipts(error,runRoot){
 const seen=new Set(),identities=new Set(),receipts=[],queue=[error];
 const append=value=>{
  requireHistoryRetirementReceipts([value],runRoot);const identity=canonicalJSON(value);
  if(!identities.has(identity)){identities.add(identity);receipts.push(value);requireHistoryRetirementReceipts(receipts,runRoot);}
 };
 const scoped=path=>{
  requireValue(typeof path==='string'&&isAbsolute(path),'RUN_HISTORY_WORKER_RETIREMENT','Retirement provenance requires an absolute source path');
  const value=relative(resolve(runRoot),resolve(path)).replaceAll('\\','/');
  requireValue(value&&!isAbsolute(value)&&!value.split('/').includes('..'),'RUN_HISTORY_WORKER_RETIREMENT','Retirement provenance escapes its exact Run root');return value;
 };
 for(let index=0;index<queue.length;index++){
  const current=queue[index];if(!current||typeof current!=='object'||seen.has(current))continue;seen.add(current);
  // Only the retirement module's private provenance registry can supply an
  // identity. Public details, hashes and similarly shaped objects are ignored.
  const receipt=verifiedRetirementReceipt(current);
  if(receipt){const {original_path,retired_path,...metadata}=receipt;
   append({...metadata,canonical_path:scoped(original_path),retired_path:scoped(retired_path)});
  }
  // A child diagnostic was already bound to its genuine launch and validated
  // before receiving this module-private marker. Keep every such locator when
  // a later Host cleanup fault wraps it, outside the generic first-four sample.
  if(current[carriedDiagnostic]?.retirements){
   requireHistoryRetirementReceipts(current[carriedDiagnostic].retirements,runRoot);
   for(const value of current[carriedDiagnostic].retirements)append(value);
  }
  if(current instanceof AggregateError)queue.push(...current.errors);
  if(current.cause)queue.push(current.cause);
 }
 return receipts;
}

export function requireHistoryAdmissionDiagnostic(value,runRoot){
 const keys=['phase','lock_path','ticket_path','owner_pid','created_at','waited_ms','cause_code','lock_exists','lock_kind','lock_bytes','lock_links',
  'owner_record_valid','observed_owner_pid','observed_owner_alive','owner_operation','observed_owner_operation','owner_probe_error_code','inspection_error_code','open_error_code','open_syscall','open_errno'];
 requireValue(value&&typeof value==='object'&&!Array.isArray(value)&&Object.keys(value).every(key=>keys.includes(key))
  &&Buffer.byteLength(JSON.stringify(value))<=8192&&['queued','waiting','acquired','publication_blocked','open_failed'].includes(value.phase),
  'RUN_HISTORY_WORKER_DIAGNOSTIC','Worker admission diagnostic metadata is invalid');
 const admission=join(runRoot,'.run-locks','.store-operation');
 requireValue(['queued','publication_blocked'].includes(value.phase)?typeof value.ticket_path==='string':typeof value.lock_path==='string',
  'RUN_HISTORY_WORKER_DIAGNOSTIC','Worker admission diagnostic requires its exact operation path');
 if(value.lock_path!==undefined)requireValue(typeof value.lock_path==='string'&&rootKey(value.lock_path)===rootKey(join(admission,'.writer.lock')),
  'RUN_HISTORY_WORKER_DIAGNOSTIC','Worker diagnostic lock is outside its exact admission');
 if(value.ticket_path!==undefined)requireValue(typeof value.ticket_path==='string'&&rootKey(dirname(value.ticket_path))===rootKey(join(admission,'.admission-queue'))
  &&/^ticket-[a-f0-9-]{36}\.json$/.test(value.ticket_path.split(/[\\/]/).at(-1)),
  'RUN_HISTORY_WORKER_DIAGNOSTIC','Worker diagnostic ticket is outside its exact admission');
 for(const [key,item]of Object.entries(value)){
  if(['phase','lock_path','ticket_path'].includes(key))continue;
  const valid=['owner_pid','observed_owner_pid'].includes(key)?item===null||Number.isSafeInteger(item)&&item>0
   :['waited_ms','lock_bytes','lock_links'].includes(key)?Number.isSafeInteger(item)&&item>=0
   :key==='open_errno'?Number.isSafeInteger(item)
   :['lock_exists','owner_record_valid','observed_owner_alive'].includes(key)?item===null||typeof item==='boolean'
   :key==='created_at'?item===null||typeof item==='string'&&item.length<=64&&Number.isFinite(Date.parse(item))
   :key==='lock_kind'?['file','directory','symlink','other'].includes(item)
   :['owner_operation','observed_owner_operation'].includes(key)?typeof item==='string'&&/^[a-z_]{1,32}$/.test(item)
   :typeof item==='string'&&/^[a-zA-Z0-9_]{1,128}$/.test(item);
  requireValue(valid,'RUN_HISTORY_WORKER_DIAGNOSTIC','Worker admission diagnostic field is invalid');
 }
 return value;
}

export function launchHistoryWorker({runRoot,owner,signal,onReady,onAdmission=admissionTrace,workerURL=new URL('./run-history-maintenance-worker.mjs',import.meta.url)}){
 requireValue(typeof onAdmission==='function','RUN_HISTORY_WORKER_OBSERVER','History worker observer must be callable');
 return new Promise((resolveCompletion,reject)=>{
  const child=spawn(process.execPath,[fileURLToPath(workerURL)],
   {stdio:['ignore','ignore','pipe','ipc'],windowsHide:true});
  const identity={schema_version:1,run_root:runRoot,job_id:owner.job_id,owner_token:owner.owner_token,owner_pid:owner.owner_pid,created_at:owner.created_at};
  let ready=false,initialized=false,terminal=null,failure=null,stderrBytes=0,stderrHash='',handshakeTimer,completed=false;
  let diagnosticSequence=0,pendingObservers=0,diagnosticTail=Promise.resolve();
  const stderrDigest=createHash('sha256');
  let ipcClosed=!child.connected,resolveIPC;
  const ipcSettled=new Promise(resolveIPCClosed=>{resolveIPC=resolveIPCClosed;if(ipcClosed)resolveIPCClosed();});
  child.once('disconnect',()=>{
   ipcClosed=true;
   // A successful send callback only confirms transport submission. The child
   // can lose its ACK channel before reporting completion; classify that observed
   // transition here, rather than letting OS-exit ordering choose the fault.
   if(ready&&!terminal)failure??=fail('RUN_HISTORY_WORKER_IPC','History worker IPC closed before its terminal result');
   resolveIPC();
  });
  const disconnect=()=>{if(child.connected)child.disconnect();};
  const failProtocol=(code,message)=>{
   failure??=fail(code,message);
   if(initialized&&child.connected)void send({...identity,type:'cancel',worker_pid:child.pid}).then(disconnect);else disconnect();
  };
  function send(message){return new Promise(resolveSent=>{
   if(!child.connected){failure??=fail('RUN_HISTORY_WORKER_IPC','History worker IPC closed before delivery');resolveSent(false);return;}
   const sent=error=>{if(error){failure??=fail('RUN_HISTORY_WORKER_IPC','History worker IPC did not confirm delivery',{cause:error});disconnect();resolveSent(false);}else resolveSent(true);};
   try{child.send(message,sent);}catch(error){sent(error);}
  });}
  function cancel(){if(initialized)send({...identity,type:'cancel',worker_pid:child.pid});}
  const aborted=()=>cancel();signal.addEventListener('abort',aborted,{once:true});
  child.stderr.on('data',bytes=>{stderrBytes+=bytes.length;stderrDigest.update(bytes);});
  const stderrSettled=finished(child.stderr).catch(error=>{failure??=fail('RUN_HISTORY_WORKER_STDERR','History worker stderr did not close cleanly',{cause:error});});
  child.once('error',error=>{failure??=fail('RUN_HISTORY_WORKER_LAUNCH','History worker could not launch',{cause:error});});
  child.on('message',message=>{
   try{
    requireValue(Buffer.byteLength(JSON.stringify(message))<=16_384&&message&&typeof message==='object'
     &&Object.keys(message).every(key=>['schema_version','run_root','job_id','owner_token','owner_pid','created_at','worker_pid','type','audit','error','sequence','detail'].includes(key))
     &&Object.keys(identity).every(key=>message[key]===identity[key])&&message.worker_pid===child.pid,
     'RUN_HISTORY_WORKER_IDENTITY','History worker response does not match its exact launch');
    if(message.type==='ready'){
     requireValue(!ready&&!terminal,'RUN_HISTORY_WORKER_PROTOCOL','History worker repeated its handshake');ready=true;clearTimeout(handshakeTimer);
     send({...identity,type:'audit',worker_pid:child.pid});if(signal.aborted)cancel();
    }else if(message.type==='admission'){
     requireValue(ready&&!terminal&&Number.isSafeInteger(message.sequence)&&message.sequence===diagnosticSequence+1,
      'RUN_HISTORY_WORKER_PROTOCOL','History worker diagnostic sequence is invalid');
     requireHistoryAdmissionDiagnostic(message.detail,runRoot);diagnosticSequence=message.sequence;pendingObservers++;
     diagnosticTail=diagnosticTail.then(async()=>{
      let observedFailure;
      try{await onAdmission(message.detail);}catch(error){observedFailure=fail('RUN_HISTORY_WORKER_OBSERVER','History worker admission observer failed',{cause:error});failure??=observedFailure;}
      finally{pendingObservers--;}
      // One ACK per diagnostic after the original observer settles. The child
      // awaits it, bounding in-flight work without a total diagnostic cap.
      await send({...identity,worker_pid:child.pid,type:'admission_ack',sequence:message.sequence,
       ...(observedFailure?{error:diagnostic(observedFailure)}:{})});
     }).catch(error=>{failure??=fail('RUN_HISTORY_WORKER_DIAGNOSTIC','History worker diagnostic transport failed',{cause:error});disconnect();});
    }else{
     requireValue(ready&&!terminal&&pendingObservers===0&&['succeeded','failed','cancelled'].includes(message.type),'RUN_HISTORY_WORKER_PROTOCOL','History worker sent an unexpected completion');
     if(message.type==='succeeded')requireValue(message.audit&&Object.keys(message.audit).every(key=>['examined','deleted_count','preserved_count'].includes(key))
      &&['examined','deleted_count','preserved_count'].every(key=>Number.isSafeInteger(message.audit[key])&&message.audit[key]>=0),
      'RUN_HISTORY_WORKER_PROTOCOL','History worker audit census is invalid');
     else requireValue(message.error&&typeof message.error.code==='string'&&typeof message.error.message==='string',
      'RUN_HISTORY_WORKER_PROTOCOL','History worker failure diagnostic is invalid');
     if(message.error&&Object.hasOwn(message.error,'retirements'))requireHistoryRetirementReceipts(message.error.retirements,runRoot);
     terminal=message;
    }
   }catch(error){failProtocol(error.code??'RUN_HISTORY_WORKER_PROTOCOL',error.message);}
  });
  async function complete(code,exitSignal){
   await Promise.all([stderrSettled,ipcSettled,diagnosticTail]);if(completed)return;completed=true;
   clearTimeout(handshakeTimer);signal.removeEventListener('abort',aborted);
   if(stderrBytes){stderrHash=stderrDigest.digest('hex');failure??=fail('RUN_HISTORY_WORKER_STDERR','History worker emitted unexpected diagnostics',{stderr_bytes:stderrBytes,stderr_sha256:stderrHash});}
   if(code!==0||exitSignal)failure??=fail('RUN_HISTORY_WORKER_EXIT','History worker did not exit normally',{exit_code:code,exit_signal:exitSignal});
   if(!terminal)failure??=fail('RUN_HISTORY_WORKER_PROTOCOL','History worker exited without one terminal result');
   const reportedCancellation=!failure&&terminal?.type==='cancelled';
   if(!failure&&terminal.type!=='succeeded')failure=fromDiagnostic(terminal.error);
   if(failure){failure.worker_quiescent=true;failure.worker_cancelled=reportedCancellation;reject(failure);}else resolveCompletion(terminal.audit);
  }
  // The repeated-handshake regression observed disconnect + OS exit without
  // ChildProcess.close on Windows. Quiescence requires exit (or ordinary close),
  // drained stderr AND observed IPC closure, with one completion gate. It never
  // settles a child that may still run or whose diagnostic/IPC handles remain.
  child.once('exit',(code,exitSignal)=>{disconnect();void complete(code,exitSignal);});
  child.once('close',(code,exitSignal)=>{if(!child.connected&&!ipcClosed){ipcClosed=true;resolveIPC();}void complete(code,exitSignal);});
  handshakeTimer=setTimeout(()=>failProtocol('RUN_HISTORY_WORKER_HANDSHAKE','History worker handshake did not settle within its bound'),5000);
  // Persist the exact child PID before letting it acknowledge or audit. A
  // stalled handshake therefore retains both Host and child identities.
  if(Number.isSafeInteger(child.pid))Promise.resolve().then(()=>onReady(child.pid)).then(()=>{
   initialized=true;send({...identity,type:'initialize',worker_pid:child.pid});if(signal.aborted)cancel();
  },error=>{failure??=error;if(child.connected)child.disconnect();});
 });
}

export class RunHistoryMaintenance {
 constructor({runRoot,settlementMs=5000,readRecord=boundedJSON,launchWorker=launchHistoryWorker}){
  requireValue(isAbsolute(runRoot),'ABSOLUTE_PATH_REQUIRED','Maintenance Run root must be absolute');
  requireValue(Number.isSafeInteger(settlementMs)&&settlementMs>0&&settlementMs<=5000,'RUN_HISTORY_MAINTENANCE_OPTIONS','Maintenance settlement must be bounded');
  requireValue(typeof readRecord==='function','RUN_HISTORY_MAINTENANCE_OPTIONS','Maintenance metadata reader must be callable');
  requireValue(typeof launchWorker==='function','RUN_HISTORY_MAINTENANCE_OPTIONS','Maintenance worker launcher must be callable');
  this.root=resolve(runRoot);this.directory=join(this.root,'.run-locks','.history-maintenance');
  this.lockPath=join(this.directory,'.writer.lock');this.receiptPath=join(this.directory,'receipt.json');
  this.diagnosticPath=join(this.directory,'diagnostic.json');this.settlementMs=settlementMs;
  this.readRecord=readRecord;
  this.launchWorker=launchWorker;
  this.task=null;this.error=null;this.closed=false;this.controller=null;this.owner=null;this.latest=null;this.writes=Promise.resolve();
  this.deferred=null;
  this.hook=store=>this.schedule(store,{automatic:true});
 }
 schedule(store,{automatic=false}={}){
  // Own every promise, including admission/integrity failures. Startup has
  // already committed its selected Run. Status and shutdown report failures.
  if(this.closed){this.error??=fail('RUN_HISTORY_MAINTENANCE_CLOSED','History maintenance Host is closed');return;}
  if(this.task||this.error)return;
  const allowDeferral=automatic&&foregroundActivityCount(this.root)>0;
  this.task=Promise.resolve().then(()=>this.#run(store,allowDeferral)).catch(async error=>{
   this.#clearDeferred();
   this.error=error;
   // Observing existing durable evidence is not a new failure write. Explicit
   // exact recovery may archive that evidence while this observer is paused;
   // do not resurrect its stale diagnostic afterwards. The observer still
   // reports the original error to status/shutdown.
   if(error[alreadyPersisted])return;
   // Persist admission errors without changing a foreign claim or receipt.
   try{await ensureDirectory(this.directory);await durableExclusive(this.diagnosticPath,{schema_version:1,at:Date.now(),error:diagnostic(error,0,this.root)});}
   catch(cause){
    if(cause.code!=='EEXIST')this.error=Object.assign(new AggregateError([error,cause],'Maintenance diagnostic persistence failed'),{code:error.code});
   }
  }).finally(()=>{
   this.task=null;
   // Scope release can race the final inspection microtask. The registration
   // then leaves this one bounded deferred opportunity for the scheduler tail.
   if(this.deferred&&!this.closed&&!foregroundActivityCount(this.root))this.#flushDeferred();
  });
 }
 #clearDeferred(){const deferred=this.deferred;this.deferred=null;deferred?.cancel();}
 #defer(store){
  if(this.deferred)return;
  this.deferred={store,requestedAt:Date.now(),cancel:()=>{}};
  this.deferred.cancel=onForegroundIdle(this.root,()=>this.#flushDeferred());
 }
 #flushDeferred(){
  if(!this.deferred||this.task)return;
  const {store}=this.deferred;this.#clearDeferred();
  if(!this.closed)this.schedule(store);
 }
 #automaticStatus(){return {automatic_deferred:Boolean(this.deferred),foreground_active:foregroundActivityCount(this.root),
  automatic_requested_at:this.deferred?.requestedAt??null};}
 async #inspect(){
  const ownerValue=await this.readRecord(this.lockPath,{optional:true,initializationMs:250});
  const owner=ownerValue?receipt(ownerValue):null;
  if(owner)live(owner);
  const saved=await this.readRecord(this.receiptPath,{optional:true});
  if(saved)receipt(saved);
  if(owner){
   const current=await this.readRecord(this.lockPath,{optional:true,initializationMs:250});
   if(!current){
    requireValue(!saved||saved.phase==='settled'||exact(saved,owner),'RUN_HISTORY_MAINTENANCE_CONFLICT','Released maintenance owner conflicts with an unfinished foreign receipt');
    // Settlement can commit after our receipt read and release before the
    // second owner read. Recapture evidence once; never replay an audit.
    return {owner:null,saved:await this.#releasedReceipt(owner)};
   }
   receipt(current);
   requireValue(exact(current,owner),'RUN_HISTORY_MAINTENANCE_CONFLICT','Maintenance owner changed during inspection');live(current);
   // The exclusive, synced claim is itself a pending receipt. Publication
   // precedes the full audit; an older completed receipt may still be present.
   if(saved&&exact(saved,owner))return {owner,saved};
   requireValue(!saved||saved.phase==='settled','RUN_HISTORY_MAINTENANCE_CONFLICT','Live maintenance claim conflicts with an unfinished receipt');
   return {owner,saved:owner};
  }
  if(saved&&saved.phase!=='settled'){
   // A peer can publish between our absent-owner and pending-receipt reads.
   // Recheck that exact live claim before classifying missing ownership.
   const current=await this.readRecord(this.lockPath,{optional:true,initializationMs:250});
   if(!current)return {owner:null,saved:await this.#releasedReceipt(saved)};
   receipt(current);
   requireValue(exact(current,saved),'RUN_HISTORY_MAINTENANCE_CONFLICT','New maintenance claim does not own the captured pending receipt');live(current);
   return {owner:current,saved};
  }
  return {owner:null,saved};
 }
 async #releasedReceipt(expected){
  const path=expected.kind==='cancelled_diagnostic_recovery'?join(this.directory,`recovery-${expected.job_id}.json`):this.receiptPath;
  const settled=await this.readRecord(path,{optional:true});
  if(settled)receipt(settled);
  requireValue(settled&&exact(settled,expected)&&settled.phase==='settled','RUN_HISTORY_MAINTENANCE_CONFLICT','Maintenance owner disappeared without its exact settled receipt');
  return settled;
 }
 async #assertOwn(){
  const actual=receipt(await boundedJSON(this.lockPath));
  requireValue(exact(actual,this.owner),'RUN_HISTORY_MAINTENANCE_OWNERSHIP','Maintenance writer ownership changed; retain evidence');live(actual);
 }
 #record(changes){
  const write=this.writes.then(async()=>{
   // A timeout racing a terminal write must not overwrite a confirmed outcome
   // with STOP_PENDING, nor touch a released owner.
   if(changes.outcome==='stop_pending'&&this.latest?.phase==='settled')return;
   await this.#assertOwn();const next={...this.owner,...changes};receipt(next);
   requireValue(Buffer.byteLength(canonicalJSON(next))<=16_384,'RUN_HISTORY_MAINTENANCE_RECORD','Maintenance receipt exceeds its bound');
   await writeDurableJSON(this.receiptPath,next);
   this.latest=next;
  });
  // Every caller awaits its write; the tail owns rejection while later writes
  // remain independently attemptable after an earlier persistence failure.
  this.writes=write.catch(()=>{});return write;
 }
 async #run(store,allowDeferral){
  requireValue(rootKey(store.root)===rootKey(this.root),'RUN_HISTORY_MAINTENANCE_SCOPE','Maintenance audit requires its exact Run store');
  await ensureDirectory(this.directory);
  const recordedFailure=await this.readRecord(this.diagnosticPath,{optional:true});
  if(recordedFailure){
   requireValue(typeof recordedFailure.error?.code==='string'&&typeof recordedFailure.error.message==='string','RUN_HISTORY_MAINTENANCE_RECORD','Maintenance diagnostic is malformed');
   throw Object.assign(fromDiagnostic(recordedFailure.error),{[alreadyPersisted]:true});
  }
  const inspected=await this.#inspect();
  if(inspected.owner){this.#clearDeferred();return;}
  if(inspected.saved?.outcome==='failed')throw fromDiagnostic(inspected.saved.error);
  if(inspected.saved?.outcome==='succeeded'&&inspected.saved.due_at>Date.now()){this.#clearDeferred();return;}
  if(this.closed){this.#clearDeferred();return;}
  // Inspection is never delayed or reused as authority. Only a new automatic
  // claim may wait for the original requests to settle. At a later activity
  // opportunity one existing interval of deferred age ends that preference,
  // even under continuous overlap; no timer or admission semantics change.
  if(allowDeferral&&foregroundActivityCount(this.root)>0
   &&(!this.deferred||Date.now()-this.deferred.requestedAt<HISTORY_MAINTENANCE_INTERVAL_MS)){
   this.#defer(store);return;
  }
  this.#clearDeferred();
  const created_at=Date.now(),owner={schema_version:1,job_id:randomUUID(),owner_token:randomUUID(),owner_pid:process.pid,
   created_at,due_at:created_at+HISTORY_MAINTENANCE_INTERVAL_MS,phase:'claimed',outcome:'pending'};
  try{await durableExclusive(this.lockPath,owner);}
  catch(error){
   if(error.code!=='EEXIST')throw error;
   const concurrent=await this.#inspect();
   if(concurrent.owner)return;
   // No automatic retry after a disputed acquisition, even if its owner just
   // finished. The next normal startup can inspect its completed receipt.
   requireValue(concurrent.saved?.phase==='settled','RUN_HISTORY_MAINTENANCE_CONFLICT','Maintenance acquisition lost its exact owner');
   if(concurrent.saved.outcome==='failed')throw fromDiagnostic(concurrent.saved.error);
   return;
  }
  this.owner=owner;this.latest=null;this.controller=new AbortController();
  if(this.closed)this.controller.abort();
  let failure;
  try{
   await this.#record({phase:'auditing',outcome:'pending'});
   // Only cancellation before launching has no child outcome to preserve.
   if(this.controller.signal.aborted)throw Object.assign(cancelled(),{worker_quiescent:true,worker_cancelled:true});
   const result=await this.launchWorker({runRoot:this.root,owner,signal:this.controller.signal,onReady:async worker_pid=>{
    this.owner={...this.owner,worker_pid};await this.#record({phase:'auditing',outcome:'pending'});
   }});
   // The launcher returns only a confirmed successful child terminal after
   // quiescence. A later Host abort cannot undo the audit's atomic commit or
   // reclassify its successful deletion census as worker cancellation.
   await this.#record({phase:'settled',outcome:'succeeded',finished_at:Date.now(),due_at:Date.now()+HISTORY_MAINTENANCE_INTERVAL_MS,
    audit:{examined:result.examined,deleted_count:result.deleted_count,preserved_count:result.preserved_count}});
  }catch(error){
   const confirmedCancellation=error.code==='RUN_HISTORY_CANCELLED'&&this.controller.signal.aborted&&error.worker_quiescent===true&&error.worker_cancelled===true;
   failure=confirmedCancellation?null:error;
   try{await this.#record({phase:'settled',outcome:confirmedCancellation?'cancelled':'failed',finished_at:Date.now(),error:diagnostic(error,0,this.root)});}
   catch(cause){throw Object.assign(new AggregateError([error,cause],'Maintenance failed before its exact outcome could be committed'),{code:error.code});}
  }
  // Only a confirmed settled audit may release this live exact owner. A failed
  // receipt/ownership check retains both records for explicit inspection.
  try{
   await this.writes;await this.#assertOwn();
   await retireOwnedFile(this.lockPath,{stagingRoot:join(this.directory,'.pending'),validate:bytes=>{
    const current=receipt(JSON.parse(bytes));
    requireValue(exact(current,this.owner),'RUN_HISTORY_MAINTENANCE_OWNERSHIP','Maintenance claim changed; retain evidence');return current.owner_pid;
   }});await syncDirectory(this.directory);
   this.owner=null;this.controller=null;
  }catch(cleanup){if(failure)throw new AggregateError([failure,cleanup],'Maintenance audit and exact claim retirement both require attention');throw cleanup;}
  if(failure)throw failure;
 }
 async settle(){
  // Explicit drains do not wait for a caller's own foreground scope to end.
  for(;;){this.#flushDeferred();const pending=this.task;if(!pending)break;await pending;}
  if(this.error)throw this.error;
 }
 async status(){
  try{
   try{await noSymlinks(this.directory);}catch(error){
    if(error.code==='ENOENT'&&resolve(error.path)===this.directory)return {phase:'idle',outcome:'pending',interval_ms:HISTORY_MAINTENANCE_INTERVAL_MS,...this.#automaticStatus()};
    throw error;
   }
   const {saved}=await this.#inspect();const observation=await boundedJSON(this.diagnosticPath,{optional:true});
   const compact=saved?(({owner_token,...visible})=>visible)(saved):{phase:'idle',outcome:'pending',interval_ms:HISTORY_MAINTENANCE_INTERVAL_MS};
   if(observation?.error)return {...compact,error:observation.error,...this.#automaticStatus()};
   return {...compact,...this.#automaticStatus()};
  }catch(error){return {phase:'blocked',outcome:'failed',error:diagnostic(error),...this.#automaticStatus()};}
 }
 async close(){
  this.closed=true;this.#clearDeferred();this.controller?.abort();
  const pending=this.task;if(!pending){if(this.error)throw this.error;return;}
  let timer;
  const settled=await Promise.race([pending.then(()=>true),new Promise(r=>{timer=setTimeout(()=>r(false),this.settlementMs);})]).finally(()=>clearTimeout(timer));
  if(!settled){
   const error=fail('RUN_HISTORY_MAINTENANCE_STOP_PENDING','History audit did not settle within the Host shutdown bound');
   // The initial synced pending claim remains evidence even if this extra
   // shutdown receipt cannot reach storage. Bound persistence separately; its
   // handled promise stays owned and can never release the audit's live claim.
   if(this.owner){
    const recording=this.#record({phase:'stopping',outcome:'stop_pending',error:diagnostic(error)});
    let persistenceTimer;
    const recorded=await Promise.race([recording.then(()=>({ok:true}),cause=>({cause})),new Promise(r=>{persistenceTimer=setTimeout(()=>r({pending:true}),Math.min(250,this.settlementMs));})]).finally(()=>clearTimeout(persistenceTimer));
    if(!recorded.ok)error.persistence_error=recorded.pending?{code:'RUN_HISTORY_MAINTENANCE_RECEIPT_PENDING'}:diagnostic(recorded.cause);
   }
   throw error;
  }
  if(this.error)throw this.error;
 }
}
