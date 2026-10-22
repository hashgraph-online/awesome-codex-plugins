import {open,lstat,mkdir,rename,unlink,rmdir,readdir} from 'node:fs/promises';
import {join,resolve} from 'node:path';
import {randomUUID} from 'node:crypto';
import {performance} from 'node:perf_hooks';
import {ensureDirectory,noSymlinks,requireValue} from './workflow-paths.mjs';

async function record(path){
 await noSymlinks(path);
 const handle=await open(path,'r');
 let result,failure;
 try{
  const info=await handle.stat({bigint:true});
  requireValue(info.isFile()&&info.nlink===1n&&info.size<=4096n,
   'OWNED_FILE_RETIREMENT_RECORD','Retirement requires one bounded regular ownership record');
  const bytes=await handle.readFile();
  requireValue(bytes.length<=4096,'OWNED_FILE_RETIREMENT_RECORD','Ownership record grew during retirement');
  result={info,bytes};
 }catch(error){failure=error;}
 try{await handle.close();}
 catch(error){if(failure)throw new AggregateError([failure,error],'Ownership record read and close both failed');throw error;}
 if(failure)throw failure;return result;
}
const sameFile=(a,b)=>a.dev===b.dev&&a.ino===b.ino;
const exactPath=(a,b)=>typeof a==='string'&&(process.platform==='win32'
 ?resolve(a).toLowerCase()===resolve(b).toLowerCase():resolve(a)===resolve(b));
const retirementReceipts=new WeakMap();
export const verifiedRetirementReceipt=error=>retirementReceipts.get(error)??null;
function captureReceipt(error,state){
 const receipt=Object.freeze({phase:state.phase,original_path:state.original_path,retired_path:state.retired_path,
  retired:state.retired,deleted:state.deleted,
  ...(Number.isSafeInteger(state.owner_pid)&&state.owner_pid>0?{owner_pid:state.owner_pid}:{}),
  ...(typeof error.code==='string'&&/^[a-zA-Z0-9_]{1,128}$/.test(error.code)?{cause_code:error.code}:{}),
  ...(Number.isSafeInteger(error.errno)?{cause_errno:error.errno}:{}),
  ...(Number.isSafeInteger(state.cleanup_waited_ms)?{cleanup_waited_ms:state.cleanup_waited_ms}:{}),
  ...(Number.isSafeInteger(state.cleanup_checks)?{cleanup_checks:state.cleanup_checks}:{})});
 retirementReceipts.set(error,receipt);
}

// Public AggregateError payloads do not traverse child errors. Carry only
// bounded retirement receipts, never ownership bytes/tokens or error bodies.
export function retirementErrorDetails(errors){
 const failures=[],seen=new Set();let complete=errors.length<=4;
 const visit=(error,depth)=>{
  if(depth>4){complete=false;return;}
  const detail=verifiedRetirementReceipt(error);
  if(detail&&typeof detail.phase==='string'&&/^retirement_[a-z_]+$/.test(detail.phase)
   &&[detail.original_path,detail.retired_path].every(path=>typeof path==='string'&&path.length<=4096)){
   const key=detail.retired_path+'|'+detail.phase+'|'+(detail.cause_code??'');
   if(!seen.has(key)){seen.add(key);if(failures.length<4)failures.push({...detail});else complete=false;}
  }
  if(error instanceof AggregateError){if(error.errors.length>4)complete=false;
   for(const child of error.errors.slice(0,4))visit(child,depth+1);}
 };
 for(const error of errors.slice(0,4))visit(error,0);
 return failures.length||!complete?{retirement_failures:failures,retirement_failures_complete:complete}:{};
}

async function removeRetiredDirectory(directory,retired,identity,state){
 const owned=async()=>{const current=await lstat(directory,{bigint:true});
  requireValue(current.isDirectory()&&sameFile(current,identity),
   'OWNED_FILE_RETIREMENT_DIRECTORY','Retired directory identity changed; preserve it');};
 if(process.platform==='win32')await owned();
 try{await rmdir(directory);return;}catch(error){
  if(process.platform!=='win32'||error.code!=='ENOTEMPTY')throw error;
  // Successful unlink can precede the last Windows peer handle closing. Wait
  // only for this created directory to become empty; unreadability alone does
  // not prove delete-pending. Never remove files, replay effects or retry EPERM.
  const started=performance.now(),deadline=started+1000;
  state.cleanup_checks=0;
  for(;;){
   state.cleanup_checks++;state.cleanup_waited_ms=Math.ceil(performance.now()-started);
   if(performance.now()>=deadline)throw error;
   await owned();const entries=await readdir(directory);
   requireValue(entries.length<=1&&entries.every(name=>name==='record.json'),
    'OWNED_FILE_RETIREMENT_DIRECTORY','Unexpected retired directory entries; preserve them');
   if(!entries.length){
    await owned();
    if(performance.now()>=deadline){state.cleanup_waited_ms=Math.ceil(performance.now()-started);throw error;}
    try{await rmdir(directory);return;}catch(next){if(next.code!=='ENOTEMPTY')throw next;}
   }else{
    try{await lstat(retired);
     throw Object.assign(new Error('An accessible file replaced the unlinked record; preserve it'),{code:'OWNED_FILE_RETIREMENT_DIRECTORY'});
    }catch(next){
     if(!['ENOENT','EPERM'].includes(next.code)||!exactPath(next.path,retired))throw next;
     state.cleanup_inspection_code=next.code;
    }
   }
   state.cleanup_waited_ms=Math.ceil(performance.now()-started);
   if(performance.now()>=deadline)throw error;
   await new Promise(resolve=>setTimeout(resolve,Math.min(25,Math.ceil(deadline-performance.now()))));
  }
 }
}

// Canonical-name rename releases ownership. Only the unique retired name is
// unlinked: Windows can deny new opens between delete disposition and close,
// including POSIX unlink. No permission error here authorizes a retry/replay.
export async function retireOwnedFile(path,{stagingRoot,validate,onRetired=()=>{}}){
 await ensureDirectory(stagingRoot);
 const directory=join(stagingRoot,'retired-owner-'+randomUUID()),retired=join(directory,'record.json');
 const state={phase:'retirement_allocate',original_path:path,retired_path:retired,retired:false,deleted:false};
 let allocated=false,directoryIdentity;
 try{
  await mkdir(directory,{mode:0o700});allocated=true;await noSymlinks(directory);
  if(process.platform==='win32')directoryIdentity=await lstat(directory,{bigint:true});
  const before=await record(path),ownerPid=await validate(before.bytes);
  if(Number.isSafeInteger(ownerPid)&&ownerPid>0)state.owner_pid=ownerPid;
  state.phase='retirement_rename';
  try{await lstat(retired);throw Object.assign(new Error('Retirement destination already exists'),{code:'OWNED_FILE_RETIREMENT_TARGET'});}
  catch(error){if(error.code!=='ENOENT'||!exactPath(error.path,retired))throw error;}
  await rename(path,retired);state.retired=true;await onRetired();
  state.phase='retirement_verify';
  const after=await record(retired);await validate(after.bytes);
  requireValue(sameFile(before.info,after.info)&&before.bytes.equals(after.bytes),
   'OWNED_FILE_RETIREMENT_IDENTITY','Moved ownership record changed; preserve it for inspection');
  state.phase='retirement_delete';await unlink(retired);state.deleted=true;
  state.phase='retirement_directory_cleanup';await removeRetiredDirectory(directory,retired,directoryIdentity,state);
 }catch(error){
  // Before rename only our empty allocated directory can be removed. After
  // rename retain evidence on every failure; never touch a successor canonical
  // owner, restore over it, or silently sweep a retained retirement record.
  error.details={...error.details,retirement:{...state}};
  captureReceipt(error,state);
  if(allocated&&!state.retired){
   try{await rmdir(directory);}
   catch(cleanup){
    captureReceipt(cleanup,{...state,phase:'retirement_directory_cleanup'});
    const combined=Object.assign(new AggregateError([error,cleanup],'Ownership retirement and staging cleanup failed'),
     {code:'OWNED_FILE_RETIREMENT_CLEANUP',details:{retirement:{...state}}});
    captureReceipt(combined,state);throw combined;
   }
  }
  throw error;
 }
}
