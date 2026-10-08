import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,readFile,writeFile,rm} from 'node:fs/promises';
import {join} from 'node:path';
import {tmpdir} from './physical-tempdir.mjs';
import {randomUUID,randomBytes} from 'node:crypto';
import {digest} from '../lib/workflow-revisions.mjs';
import {retainOwnedAuthority,readOwnedAuthority,readOwnedAuthorityForThread} from '../lib/execution/owned-workflow-authority.mjs';
test('Host retains exact authority for authenticated human cancellation and rejects stale or cross-Run data',async t=>{
 const directory=await mkdtemp(join(tmpdir(),'owned-authority-'));t.after(()=>rm(directory,{recursive:true,force:true}));
 const run={run_id:randomUUID(),control_token:randomBytes(32).toString('hex')};
 let hash=digest(run.control_token);
 const runtime={runs:{directory:()=>directory,read:async()=>({state:{control_hash:hash,main_actor:'exact-owner'}})},
  authorizeController:async(id,args)=>{assert.equal(id,run.run_id);assert.equal(args.control_token,run.control_token);}};
 await retainOwnedAuthority(runtime,run);
 await retainOwnedAuthority(runtime,run);
 assert.deepEqual(await readOwnedAuthority(runtime,run.run_id),{...run,owner:'exact-owner'});
 hash=digest('rotated');await assert.rejects(readOwnedAuthority(runtime,run.run_id),{code:'RUN_AUTHORITY'});
 hash=digest(run.control_token);
 await writeFile(join(directory,'host-authority.json'),JSON.stringify({...run,run_id:randomUUID()}));
 await assert.rejects(readOwnedAuthority(runtime,run.run_id),{code:'RUN_AUTHORITY'});
});

test('fresh Host requests recover one active Run from authenticated thread metadata without model fields',async t=>{
 const directory=await mkdtemp(join(tmpdir(),'owned-thread-authority-'));t.after(()=>rm(directory,{recursive:true,force:true}));
 const threadId=randomUUID(),run={run_id:randomUUID(),control_token:randomBytes(32).toString('hex')};
 const state={run_id:run.run_id,status:'running',control_hash:digest(run.control_token),main_actor:'codex',constraints:{native_parent_thread_id:threadId}};
 const runtime={runs:{directory:()=>directory,list:async()=>[{run_id:run.run_id,status:'running'}],read:async()=>({state})},
  authorizeController:async()=>{}};
 await retainOwnedAuthority(runtime,run);
 assert.deepEqual(await readOwnedAuthorityForThread(runtime,threadId),{...run,owner:'codex'});
 await assert.rejects(readOwnedAuthorityForThread(runtime,randomUUID()),{code:'MODEL_RUN_AUTHORITY'});
 await assert.rejects(readOwnedAuthorityForThread(runtime,'copied-by-model'),{code:'MODEL_THREAD_ID'});
});
