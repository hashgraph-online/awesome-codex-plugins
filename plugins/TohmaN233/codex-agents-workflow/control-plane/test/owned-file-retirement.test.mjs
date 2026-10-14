import test from 'node:test';
import assert from 'node:assert/strict';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {mkdtemp,rm,writeFile,readFile,mkdir,open} from 'node:fs/promises';
import {join} from 'node:path';
import {tmpdir} from './physical-tempdir.mjs';
import {retireOwnedFile,verifiedRetirementReceipt,retirementErrorDetails} from '../lib/owned-file-retirement.mjs';
const helperModule=new URL('../lib/owned-file-retirement.mjs',import.meta.url).href;
const storeModule=new URL('../lib/workflow-store.mjs',import.meta.url).href;
async function fixture(t){const root=await mkdtemp(join(tmpdir(),'owned-retirement-'));
 t.after(()=>rm(root,{recursive:true,maxRetries:3,retryDelay:100}));return root;}
const validate=expected=>bytes=>assert.deepEqual(bytes,Buffer.from(expected));

for(const mode of ['released','held','extra-entry','replacement-file','replacement-directory','initial-directory-replacement','permission'])
test(`Windows injected exact retired directory settlement preserves ownership for ${mode}`,
 {skip:process.platform!=='win32',timeout:5000},async t=>{
  const root=await fixture(t),path=join(root,'.writer.lock');await writeFile(path,'exact owner');
  const script=`import fs from 'node:fs/promises';import {syncBuiltinESMExports} from 'node:module';import {join,dirname} from 'node:path';
   const path=process.argv[1],stagingRoot=process.argv[2],mode=process.argv[3],reader=await fs.open(path,'r');
   const remove=fs.rmdir,unlink=fs.unlink;let dirCalls=0,unlinks=0,retired=0,firstError,timer,released,foreign,foreignDirectory,retiredDirectory,settled=false;
   fs.unlink=async p=>{unlinks++;const result=await unlink(p);
    retiredDirectory=dirname(p);
    if(mode==='initial-directory-replacement'){await reader.close();foreignDirectory=dirname(p);await fs.rename(foreignDirectory,foreignDirectory+'.original');await fs.mkdir(foreignDirectory);}
    return result;};
   fs.rmdir=async p=>{
    if(p!==retiredDirectory)return remove(p);
    dirCalls++;if(mode==='permission')throw Object.assign(new Error('Exact directory permission failure'),{code:'EPERM'});
    // An ordinary open peer may permit immediate POSIX deletion on Windows.
    // Inject only the exact rmdir fault; ownership checks and directory reads stay real.
    if(mode==='held'||(mode==='released'&&!settled)||(!firstError&&['extra-entry','replacement-file','replacement-directory'].includes(mode))){
     const error=firstError??Object.assign(new Error('Injected exact retired directory nonempty'),{code:'ENOTEMPTY',path:p});
     if(!firstError){firstError=error;
      if(mode==='released')timer=setTimeout(()=>{released=reader.close().then(()=>{settled=true;});},25);
      if(mode==='extra-entry'){foreign=join(p,'foreign.txt');await fs.writeFile(foreign,'foreign');}
      if(mode==='replacement-file'){await reader.close();foreign=join(p,'record.json');await fs.writeFile(foreign,'foreign');}
      if(mode==='replacement-directory'){await reader.close();await fs.rename(p,p+'.original');await fs.mkdir(p);foreign=join(p,'foreign.txt');await fs.writeFile(foreign,'foreign');}
     }throw error;
    }
    return remove(p);
   };syncBuiltinESMExports();const {retireOwnedFile}=await import(${JSON.stringify(helperModule)});
   let error;try{await retireOwnedFile(path,{stagingRoot,validate:bytes=>{if(bytes.toString()!=='exact owner')throw new Error('Owner changed');},
    onRetired:async()=>{retired++;await fs.writeFile(path,'successor',{flag:'wx'});}});}catch(cause){error=cause;}
   finally{clearTimeout(timer);if(released)await released;else if(reader.fd!==-1)await reader.close();}
   let foreignDirectoryPreserved;if(foreignDirectory)try{foreignDirectoryPreserved=(await fs.lstat(foreignDirectory)).isDirectory();}catch(error){if(error.code!=='ENOENT')throw error;foreignDirectoryPreserved=false;}
   let historyRetirement;if(mode==='held'&&error){const {diagnostic,requireHistoryRetirementReceipts}=await import(${JSON.stringify(new URL('../lib/run-history-maintenance.mjs',import.meta.url).href)});
    const detail=diagnostic(error,0,dirname(path));requireHistoryRetirementReceipts(detail.retirements,dirname(path));historyRetirement=detail.retirements[0];}
   console.log(JSON.stringify({code:error?.code??null,original_error:error===firstError,dirCalls,unlinks,retired,foreignDirectoryPreserved,historyRetirement,
    successor:await fs.readFile(path,'utf8'),foreign_preserved:foreign?await fs.readFile(foreign,'utf8'):null,retirement:error?.details?.retirement}));`;
  const result=await promisify(execFile)(process.execPath,['--input-type=module','-e',script,path,join(root,'.pending'),mode],{windowsHide:true,timeout:4000});
  const observed=JSON.parse(result.stdout);assert.equal(observed.unlinks,1);assert.equal(observed.retired,1);assert.equal(observed.successor,'successor');
  if(mode==='released'){assert.equal(observed.code,null);assert(observed.dirCalls>=2);}
  else if(mode==='held'){assert.equal(observed.code,'ENOTEMPTY');assert.equal(observed.original_error,true);assert(observed.retirement.cleanup_waited_ms>=1000);
   assert.equal(observed.historyRetirement.cause_code,'ENOTEMPTY');assert(observed.historyRetirement.cleanup_waited_ms>=1000);assert(observed.historyRetirement.cleanup_checks>0);}
  else if(mode==='permission'){assert.equal(observed.code,'EPERM');assert.equal(observed.dirCalls,1);}
  else if(mode==='initial-directory-replacement'){assert.equal(observed.code,'OWNED_FILE_RETIREMENT_DIRECTORY');assert.equal(observed.foreignDirectoryPreserved,true);assert.equal(observed.dirCalls,0);}
  else{assert.equal(observed.code,'OWNED_FILE_RETIREMENT_DIRECTORY');assert.equal(observed.foreign_preserved,'foreign');assert.equal(observed.dirCalls,1);}
 });

test('only genuine immutable retirement provenance is summarized and bounded omissions remain explicit',async t=>{
 const root=await fixture(t),errors=[];
 const forged=Object.assign(new Error('forged body'),{details:{retirement:{phase:'retirement_delete',original_path:'private-token',retired_path:'private-token'}}});
 assert.equal(verifiedRetirementReceipt(forged),null);assert.deepEqual(retirementErrorDetails([forged]),{});
 for(let index=0;index<5;index++){
  const path=join(root,`owner-${index}.json`);await writeFile(path,'exact owner');
  const failure=Object.assign(new Error('private body'),{code:'NEUTRAL_RETIREMENT_FAILURE',errno:-4048});
  await assert.rejects(retireOwnedFile(path,{stagingRoot:join(root,'.pending'),validate:bytes=>{
   assert.equal(bytes.toString(),'exact owner');return process.pid;},onRetired:()=>{throw failure;}}),error=>error===failure);
  errors.push(failure);
 }
 const original=verifiedRetirementReceipt(errors[0]);assert.equal(original.owner_pid,process.pid);assert(Object.isFrozen(original));
 errors[0].details.retirement.retired_path='private-token';errors[0].code='private-token';
 assert.equal(verifiedRetirementReceipt(errors[0]),original);assert.equal(original.cause_code,'NEUTRAL_RETIREMENT_FAILURE');
 const sampled=retirementErrorDetails([new AggregateError(errors,'private body')]);
 assert.equal(sampled.retirement_failures.length,4);assert.equal(sampled.retirement_failures_complete,false);
 assert.equal(JSON.stringify(sampled).includes('private-token'),false);assert.equal(JSON.stringify(sampled).includes('private body'),false);
 let nested=errors[0];for(let depth=0;depth<6;depth++)nested=new AggregateError([nested],'nested');
 const bounded=retirementErrorDetails([nested]);assert.equal(bounded.retirement_failures_complete,false);
 assert.equal(bounded.retirement_failures.length,0);
});

test('Windows real open-peer retirement preserves original inode, bytes and successor with either deletion behavior',
 {skip:process.platform!=='win32',timeout:5000},async t=>{
 const root=await fixture(t),path=join(root,'owner.json');await writeFile(path,'exact owner');
 const reader=await open(path,'r'),identity=await reader.stat({bigint:true});let retired=0,error;
 try{
  try{await retireOwnedFile(path,{stagingRoot:join(root,'.pending'),validate:validate('exact owner'),onRetired:async()=>{
   retired++;await assert.rejects(readFile(path),{code:'ENOENT'});await writeFile(path,'successor',{flag:'wx'});
  }});}catch(cause){error=cause;}
  if(error){
   assert.equal(error.code,'ENOTEMPTY');const receipt=verifiedRetirementReceipt(error);
   assert.equal(receipt.phase,'retirement_directory_cleanup');assert.equal(receipt.retired,true);assert.equal(receipt.deleted,true);
   assert.equal(receipt.cause_code,'ENOTEMPTY');assert(receipt.cleanup_waited_ms>=1000);assert(receipt.cleanup_checks>0);
  }
  assert.equal((await reader.stat({bigint:true})).ino,identity.ino);assert.equal((await reader.readFile()).toString(),'exact owner');
  assert.equal(retired,1);assert.equal(await readFile(path,'utf8'),'successor');
 }finally{await reader.close();}
});

for(const holdThroughDelete of [false,true])test(holdThroughDelete
 ?'POSIX retirement deletion preserves an open peer original inode and bytes'
 :'retirement releases the canonical name while an open peer verifies the original inode and bytes',
 {skip:holdThroughDelete&&process.platform==='win32'},async t=>{
 const root=await fixture(t),path=join(root,'owner.json'),pending=join(root,'.pending');await writeFile(path,'exact owner');
 const reader=await open(path,'r'),identity=await reader.stat({bigint:true});let retired=0;
 try{await retireOwnedFile(path,{stagingRoot:pending,validate:validate('exact owner'),onRetired:async()=>{
  retired++;await assert.rejects(readFile(path),{code:'ENOENT'});await writeFile(path,'successor',{flag:'wx'});
  assert.equal((await reader.stat({bigint:true})).ino,identity.ino);assert.equal((await reader.readFile()).toString(),'exact owner');
  // Windows can retain the retired directory entry until this peer closes.
  // The portable case checks rename ownership before allowing deletion.
  if(!holdThroughDelete)await reader.close();
 }});
 if(holdThroughDelete){
  assert.equal((await reader.stat({bigint:true})).ino,identity.ino);
  const bytes=Buffer.alloc(11),read=await reader.read(bytes,0,bytes.length,0);
  assert.equal(read.bytesRead,11);assert.equal(bytes.toString(),'exact owner');
 }
 }finally{if(reader.fd!==-1)await reader.close();}
 assert.equal(retired,1);assert.equal(await readFile(path,'utf8'),'successor');
});

test('unknown rename and retired deletion failures remain original errors and preserve successor/evidence',async t=>{
 for(const fault of ['rename','delete']){
  const root=await fixture(t),path=join(root,'owner.json');await writeFile(path,'exact owner');
  const script=`import fs from 'node:fs/promises';import {syncBuiltinESMExports} from 'node:module';import assert from 'node:assert/strict';
   const path=process.argv[1],stagingRoot=process.argv[2],fault=process.argv[3],originalRename=fs.rename,originalUnlink=fs.unlink;
   const denied=Object.assign(new Error('Exact permission denial'),{code:'EPERM'});let attempts=0,retired=0;
   fs.rename=async(...args)=>{if(fault==='rename'){attempts++;throw denied;}return originalRename(...args);};
   fs.unlink=async(p)=>{if(fault==='delete'){attempts++;await fs.writeFile(path,'successor',{flag:'wx'});throw denied;}return originalUnlink(p);};
   syncBuiltinESMExports();const {retireOwnedFile}=await import(${JSON.stringify(helperModule)});
   let error;try{await retireOwnedFile(path,{stagingRoot,validate:bytes=>assert.equal(bytes.toString(),'exact owner'),onRetired:()=>retired++});}catch(e){error=e;}
   assert.equal(error,denied);assert.equal(attempts,1);assert.equal(retired,fault==='delete'?1:0);
   assert.equal(await fs.readFile(path,'utf8'),fault==='delete'?'successor':'exact owner');
   if(fault==='delete')assert.equal(await fs.readFile(error.details.retirement.retired_path,'utf8'),'exact owner');
   console.log(JSON.stringify({code:error.code,attempts,retired,details:error.details}));`;
  const result=await promisify(execFile)(process.execPath,['--input-type=module','-e',script,path,join(root,'.pending'),fault],{windowsHide:true});
  const actual=JSON.parse(result.stdout);assert.equal(actual.code,'EPERM');assert.equal(actual.attempts,1);
  assert.equal(actual.details.retirement.retired,fault==='delete');assert.equal(actual.details.retirement.deleted,false);
 }
});

test('ownership read and handle close faults both remain observable before canonical release',async t=>{
 const root=await fixture(t),path=join(root,'owner.json');await writeFile(path,'exact owner');
 const script=`import fs from 'node:fs/promises';import {syncBuiltinESMExports} from 'node:module';import assert from 'node:assert/strict';
  const path=process.argv[1],original=fs.open,readFailure=Object.assign(new Error('Read denied'),{code:'EPERM'}),closeFailure=Object.assign(new Error('Close denied'),{code:'EBUSY'});
  fs.open=async(p,...args)=>{const handle=await original(p,...args);if(p===path){const close=handle.close.bind(handle);
   handle.readFile=async()=>{throw readFailure;};handle.close=async()=>{await close();throw closeFailure;};}return handle;};
  syncBuiltinESMExports();const {retireOwnedFile}=await import(${JSON.stringify(helperModule)});let error;
  try{await retireOwnedFile(path,{stagingRoot:process.argv[2],validate:()=>assert.fail('read failed')});}catch(e){error=e;}
  assert.deepEqual(error.errors,[readFailure,closeFailure]);assert.equal(error.details.retirement.retired,false);assert.equal(await fs.readFile(path,'utf8'),'exact owner');
  console.log(JSON.stringify({codes:error.errors.map(e=>e.code),canonical_preserved:true}));`;
 const result=await promisify(execFile)(process.execPath,['--input-type=module','-e',script,path,join(root,'.pending')],{windowsHide:true});
 assert.deepEqual(JSON.parse(result.stdout),{codes:['EPERM','EBUSY'],canonical_preserved:true});
});

test('retirement never overwrites a colliding target or deletes changed moved identity',async t=>{
 for(const fault of ['collision','changed-bytes','changed-inode']){
  const root=await fixture(t),path=join(root,'owner.json');await writeFile(path,'exact owner');
  const script=`import fs from 'node:fs/promises';import {syncBuiltinESMExports} from 'node:module';import {join} from 'node:path';import assert from 'node:assert/strict';
   const path=process.argv[1],stagingRoot=process.argv[2],fault=process.argv[3],originalMkdir=fs.mkdir,originalRename=fs.rename;let deletes=0;
   fs.mkdir=async(p,...args)=>{await originalMkdir(p,...args);if(fault==='collision'&&p.includes('retired-owner-'))await fs.writeFile(join(p,'record.json'),'unknown target');};
   fs.rename=async(source,destination)=>{await originalRename(source,destination);
    if(fault==='changed-bytes')await fs.writeFile(destination,'changed owner');
    if(fault==='changed-inode'){const other=destination+'.other';await fs.writeFile(other,'exact owner');await originalRename(other,destination);}};
   fs.unlink=async()=>{deletes++;throw new Error('Wrong record deletion');};syncBuiltinESMExports();
   const {retireOwnedFile}=await import(${JSON.stringify(helperModule)});let error;
   try{await retireOwnedFile(path,{stagingRoot,validate:bytes=>{if(bytes.toString()!=='exact owner')throw Object.assign(new Error('Changed token'),{code:'LOCK_OWNERSHIP'});}});}catch(e){error=e;}
   assert(error);assert.equal(deletes,0);const detail=error.details.retirement;
   const retained=await fs.readFile(detail.retired_path,'utf8');
   assert.equal(retained,fault==='collision'?'unknown target':fault==='changed-bytes'?'changed owner':'exact owner');
   if(fault==='collision')assert.equal(await fs.readFile(path,'utf8'),'exact owner');
   console.log(JSON.stringify({code:error.code,causes:error.errors?.map(e=>e.code),detail,deletes}));`;
  const result=await promisify(execFile)(process.execPath,['--input-type=module','-e',script,path,join(root,'.pending'),fault],{windowsHide:true});
  const actual=JSON.parse(result.stdout);assert.equal(actual.deletes,0);
  assert.equal(actual.code,fault==='collision'?'OWNED_FILE_RETIREMENT_CLEANUP':fault==='changed-bytes'?'LOCK_OWNERSHIP':'OWNED_FILE_RETIREMENT_IDENTITY');
  if(fault==='collision')assert(actual.causes.includes('OWNED_FILE_RETIREMENT_TARGET'));
 }
});

test('a peer inventory read raced by retirement accepts only the exact disappeared ticket',async t=>{
 const root=await fixture(t),directory=join(root,'.admission-queue');await mkdir(directory);const id='00000000-0000-0000-0000-000000000000';
 const path=join(directory,`ticket-${id}.json`),ticket={id,pid:process.pid,token:id,created_at:new Date().toISOString(),number:1};
 await writeFile(path,JSON.stringify(ticket));
 const queueModule=new URL('../lib/run-admission-queue.mjs',import.meta.url).href;
 const script=`import fs from 'node:fs/promises';import {syncBuiltinESMExports} from 'node:module';import {join} from 'node:path';import assert from 'node:assert/strict';
  const root=process.argv[1],path=process.argv[2],expected=process.argv[3],original=fs.readFile;let reads=0;
  const {retireOwnedFile}=await import(${JSON.stringify(helperModule)});
  fs.readFile=async(p,...args)=>{if(p===path){reads++;await retireOwnedFile(path,{stagingRoot:join(root,'.admission-queue','.pending'),
   validate:bytes=>assert.equal(bytes.toString(),expected)});}return original(p,...args);};
  syncBuiltinESMExports();const {inspectRunAdmissionQueue}=await import(${JSON.stringify(queueModule)});
  assert.deepEqual(await inspectRunAdmissionQueue(root),[]);assert.equal(reads,1);console.log(JSON.stringify({reads,canonical_disappeared:true}));`;
 const result=await promisify(execFile)(process.execPath,['--input-type=module','-e',script,root,path,JSON.stringify(ticket)],{windowsHide:true});
 assert.deepEqual(JSON.parse(result.stdout),{reads:1,canonical_disappeared:true});
});

test('onAcquired ticket retirement cleanup failure enters zero callbacks and never cleans a successor',async t=>{
 const root=await fixture(t),admission=join(root,'.run-locks','.store-operation');await mkdir(admission,{recursive:true});
 const script=`import fs from 'node:fs/promises';import {syncBuiltinESMExports} from 'node:module';import assert from 'node:assert/strict';
  const root=process.argv[1],original=fs.unlink;let callbacks=0,attempts=0,retained;
  const denied=Object.assign(new Error('Owned retired ticket deletion denied'),{code:'EPERM'});
  fs.unlink=async path=>{if(path.includes('.admission-queue')&&path.includes('retired-owner-')){attempts++;retained=path;throw denied;}return original(path);};
  syncBuiltinESMExports();const {WorkflowStore}=await import(${JSON.stringify(storeModule)});const store=new WorkflowStore(root);let error;
  try{await store.withRunAdmission(()=>callbacks++,{onWait:()=>{}});}catch(e){error=e;}
  const leaves=e=>e?.errors?e.errors.flatMap(leaves):[e];const failures=leaves(error);
  assert(error);assert.equal(callbacks,0);assert.equal(attempts,1);assert.deepEqual(failures.map(e=>e.code),['EPERM']);assert.equal(failures[0],denied);
  assert.equal(denied.details.retirement.retired,true);assert.equal(denied.details.retirement.deleted,false);
  assert(JSON.parse(await fs.readFile(retained,'utf8')).pid===process.pid);assert.equal(await store.inspectWriter(),null);
  console.log(JSON.stringify({callbacks,attempts,codes:failures.map(e=>e.code),retired_preserved:true}));`;
 const result=await promisify(execFile)(process.execPath,['--input-type=module','-e',script,admission],{windowsHide:true});
 assert.deepEqual(JSON.parse(result.stdout),{callbacks:0,attempts:1,codes:['EPERM'],retired_preserved:true});
});

test('public double retirement failure retains both locators and original errors without callbacks or successor cleanup',async t=>{
 const root=await fixture(t),admission=join(root,'.run-locks','.store-operation');await mkdir(admission,{recursive:true});
 const errorModule=new URL('../lib/workbench-api.mjs',import.meta.url).href;
 const script=`import fs from 'node:fs/promises';import {syncBuiltinESMExports} from 'node:module';import {join} from 'node:path';import assert from 'node:assert/strict';
  const root=process.argv[1],original=fs.unlink,denied={
   ticket:Object.assign(new Error('Retired ticket deletion denied'),{code:'EPERM',errno:-4048}),
   writer:Object.assign(new Error('Retired writer deletion denied'),{code:'EACCES',errno:-4092})};
  const retained={},successors={},attempts={ticket:0,writer:0};let callbacks=0;
  fs.unlink=async path=>{
   if(!path.includes('retired-owner-'))return original(path);
   const kind=path.includes('.admission-queue')?'ticket':'writer',bytes=await fs.readFile(path),record=JSON.parse(bytes);
   attempts[kind]++;retained[kind]={path,bytes};
   const canonical=kind==='ticket'?join(root,'.admission-queue','ticket-'+record.id+'.json'):join(root,'.writer.lock');
   const successor=Buffer.from(JSON.stringify({...record,token:'successor-'+kind}));
   await fs.writeFile(canonical,successor,{flag:'wx'});successors[kind]={canonical,bytes:successor};throw denied[kind];
  };syncBuiltinESMExports();
  const {WorkflowStore}=await import(${JSON.stringify(storeModule)});const {workbenchErrorPayload}=await import(${JSON.stringify(errorModule)});
  let error;try{await new WorkflowStore(root).withRunAdmission(()=>callbacks++,{onWait:()=>{}});}catch(e){error=e;}
  assert(error instanceof AggregateError);assert.deepEqual(error.errors,[denied.ticket,denied.writer]);
  assert.equal(error.errors[0],denied.ticket);assert.equal(error.errors[1],denied.writer);
  assert.equal(callbacks,0);assert.deepEqual(attempts,{ticket:1,writer:1});
  const payload=workbenchErrorPayload(error),receipts=payload.details.retirement_failures;
  assert.equal(receipts.length,2);assert.equal(payload.details.retirement_failures_complete,true);
  for(const kind of ['ticket','writer']){
   const receipt=receipts.find(value=>value.retired_path===retained[kind].path);
   assert(receipt,'Missing '+kind+' retained locator');assert.equal(receipt.original_path,successors[kind].canonical);
   assert.equal(receipt.retired,true);assert.equal(receipt.deleted,false);assert.equal(receipt.cause_code,denied[kind].code);
   assert.deepEqual(await fs.readFile(retained[kind].path),retained[kind].bytes);
   assert.deepEqual(await fs.readFile(successors[kind].canonical),successors[kind].bytes);
   assert.equal(JSON.stringify(payload).includes(JSON.parse(retained[kind].bytes).token),false);
  }
  console.log(JSON.stringify({callbacks,attempts,original_errors_preserved:true,both_retained_paths_visible:true,complete:true,successors_preserved:true}));`;
 const result=await promisify(execFile)(process.execPath,['--input-type=module','-e',script,admission],{windowsHide:true});
 assert.deepEqual(JSON.parse(result.stdout),{callbacks:0,attempts:{ticket:1,writer:1},original_errors_preserved:true,both_retained_paths_visible:true,complete:true,successors_preserved:true});
});

test('public writer failure payload retains bounded retired evidence alongside the original action failure',async t=>{
 const root=await fixture(t);
 const errorModule=new URL('../lib/workbench-api.mjs',import.meta.url).href;
 const script=`import fs from 'node:fs/promises';import {syncBuiltinESMExports} from 'node:module';import assert from 'node:assert/strict';
  const root=process.argv[1],original=fs.unlink,business=Object.assign(new Error('Action failed'),{code:'NEUTRAL_ACTION_FAILURE'}),denied=Object.assign(new Error('Retired deletion denied'),{code:'EPERM'});
  fs.unlink=async path=>{if(path.includes('retired-owner-'))throw denied;return original(path);};syncBuiltinESMExports();
  const {WorkflowStore}=await import(${JSON.stringify(storeModule)});const {workbenchErrorPayload}=await import(${JSON.stringify(errorModule)});
  let error;try{await new WorkflowStore(root).withWriter(()=>{throw business;});}catch(e){error=e;}
  assert.deepEqual(error.errors,[business,denied]);const payload=workbenchErrorPayload(error),receipt=payload.details.retirement_failures[0];
  assert.equal(receipt.cause_code,'EPERM');assert.equal(receipt.retired,true);assert.equal(receipt.deleted,false);
  const owner=JSON.parse(await fs.readFile(receipt.retired_path,'utf8'));assert.equal(JSON.stringify(payload).includes(owner.token),false);
  console.log(JSON.stringify({original_errors_preserved:true,retired_path_visible:true,owner_token_hidden:true}));`;
 const result=await promisify(execFile)(process.execPath,['--input-type=module','-e',script,root],{windowsHide:true});
 assert.deepEqual(JSON.parse(result.stdout),{original_errors_preserved:true,retired_path_visible:true,owner_token_hidden:true});
});

test('Windows pending deletion holds only a retired writer name after all callback work settles',
 {skip:process.platform!=='win32',timeout:20000},async t=>{
 const root=await fixture(t),admission=join(root,'.run-locks','.store-operation');await mkdir(admission,{recursive:true});
 const nativeFixture=new URL('./fixtures/owned-retirement-disposition.mjs',import.meta.url).href;
 const script=`import fs from 'node:fs/promises';import {syncBuiltinESMExports} from 'node:module';import {join} from 'node:path';import assert from 'node:assert/strict';
  import {holdOwnedDeleteDisposition} from ${JSON.stringify(nativeFixture)};
  const root=process.argv[1],original=fs.unlink;let trigger,releaseDelete,firstReleased,firstEntered,waitSeen;
  const pending=new Promise(r=>trigger=r),entered=new Promise(r=>firstEntered=r),callbackGate=new Promise(r=>firstReleased=r),waited=new Promise(r=>waitSeen=r);
  let once=false,firstSettled=false,secondCallbacks=0,closeNative;const deletionGate=new Promise(r=>releaseDelete=r);
  fs.unlink=async path=>{
   if(!once&&!path.includes('.admission-queue')&&(path.endsWith('.writer.lock')||path.includes('retired-owner-'))){
    once=true;closeNative=await holdOwnedDeleteDisposition(path);assert.equal(firstSettled,true);trigger();await deletionGate;await closeNative();closeNative=null;return;
   }return original(path);
  };syncBuiltinESMExports();const {WorkflowStore}=await import(${JSON.stringify(storeModule)});const store=new WorkflowStore(root);
  let first,second;
  try{
   first=store.withWriter(async()=>{firstEntered();await callbackGate;firstSettled=true;});await entered;
   second=store.withRunAdmission(()=>{assert.equal(firstSettled,true);return ++secondCallbacks;},{onWait:()=>waitSeen()});
   const outcome=second.then(value=>({value}),error=>({error}));await waited;assert.equal(secondCallbacks,0);firstReleased();await pending;
   const result=await outcome;assert.equal(result.error,undefined,result.error?.stack);assert.equal(result.value,1);
   releaseDelete();await first;console.log(JSON.stringify({secondCallbacks,firstSettled,real_pending_delete:true}));
  }finally{firstReleased();releaseDelete();if(closeNative)await closeNative();await Promise.allSettled([first,second]);}
 `;
 const result=await promisify(execFile)(process.execPath,['--input-type=module','-e',script,admission],{windowsHide:true,timeout:17000});
 assert.deepEqual(JSON.parse(result.stdout),{secondCallbacks:1,firstSettled:true,real_pending_delete:true});
});

test('Windows pending ticket deletion retains the writer fence while a peer waits without denied reads',
 {skip:process.platform!=='win32',timeout:20000},async t=>{
 const root=await fixture(t),admission=join(root,'.run-locks','.store-operation');await mkdir(admission,{recursive:true});
 const nativeFixture=new URL('./fixtures/owned-retirement-disposition.mjs',import.meta.url).href;
 const script=`import fs from 'node:fs/promises';import {syncBuiltinESMExports} from 'node:module';import assert from 'node:assert/strict';
  import {holdOwnedDeleteDisposition} from ${JSON.stringify(nativeFixture)};
  const root=process.argv[1],original=fs.unlink;let trigger,releaseDelete,waitSeen;
  const pending=new Promise(r=>trigger=r),deletionGate=new Promise(r=>releaseDelete=r),waited=new Promise(r=>waitSeen=r);
  let once=false,firstCallbacks=0,secondCallbacks=0,closeNative;
  fs.unlink=async path=>{if(!once&&path.includes('.admission-queue')){
   once=true;closeNative=await holdOwnedDeleteDisposition(path);trigger();await deletionGate;await closeNative();closeNative=null;return;
  }return original(path);};syncBuiltinESMExports();const {WorkflowStore}=await import(${JSON.stringify(storeModule)});const store=new WorkflowStore(root);
  let first,second;
  try{first=store.withRunAdmission(()=>++firstCallbacks,{onWait:()=>{}});await pending;assert.equal(firstCallbacks,0);
   second=store.withRunAdmission(()=>{assert.equal(firstCallbacks,1);return ++secondCallbacks;},{onWait:()=>waitSeen()});
   const outcome=second.then(value=>({value}),error=>({error}));const beforeRelease=await Promise.race([waited.then(()=>({waiting:true})),outcome]);
   assert.equal(beforeRelease.error,undefined,beforeRelease.error?.stack);assert.equal(beforeRelease.waiting,true);
   assert.equal(secondCallbacks,0);releaseDelete();await first;const done=await outcome;assert.equal(done.error,undefined,done.error?.stack);assert.equal(done.value,1);
   console.log(JSON.stringify({firstCallbacks,secondCallbacks,real_pending_delete:true}));
  }finally{releaseDelete();if(closeNative)await closeNative();await Promise.allSettled([first,second]);}
 `;
 const result=await promisify(execFile)(process.execPath,['--input-type=module','-e',script,admission],{windowsHide:true,timeout:17000});
 assert.deepEqual(JSON.parse(result.stdout),{firstCallbacks:1,secondCallbacks:1,real_pending_delete:true});
});
