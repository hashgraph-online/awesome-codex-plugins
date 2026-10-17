import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {syncBuiltinESMExports} from 'node:module';
import {join} from 'node:path';
import {tmpdir} from './physical-tempdir.mjs';
import {WorkflowRuntime} from '../lib/workflow-runtime.mjs';
import {WorkflowStore} from '../lib/workflow-store.mjs';
import {createDraft} from '../lib/workflow-schema.mjs';
import {digest,LIMITS} from '../lib/workflow-revisions.mjs';
import {withRunStoreObservation} from '../lib/workflow-run-store.mjs';
import {readPinnedObject} from '../lib/pinned-object-reader.mjs';
import {readPinnedNodeResources} from '../lib/execution/node-input-materials.mjs';
import {loadNodeSkillSnapshots} from '../lib/execution/workflow-resource-broker.mjs';
const native={...fs};
async function patched(overrides,action){Object.assign(fs,overrides);syncBuiltinESMExports();try{return await action();}finally{for(const key of Object.keys(overrides))fs[key]=native[key];syncBuiltinESMExports();}}
async function fixture(t){
 const root=await native.mkdtemp(join(tmpdir(),'pinned-consumption-')),workspace=join(root,'workspace');await native.mkdir(workspace);t.after(()=>native.rm(root,{recursive:true,maxRetries:3,retryDelay:100}));
 const resources=Object.fromEntries(Array.from({length:73},(_,i)=>['resource-'+i+'.txt','neutral object '+i]));
 const workflow={...createDraft('resource-test','Neutral resource test'),status:'ready',finalization:{required:true,node_id:'work'},skill_policy:{mode:'cooperative',implicit:'deny',ambient_allow:[],shadowed_skill_paths:[]},nodes:[{id:'start',type:'start'},{id:'work',type:'agent',executor:{kind:'main'},role:'finalizer',access:'read_only',resources:['resource-0.txt'],prompt_template:'{{task}}',approval:{required:false},retry:{max_attempts:3},input_bindings:{}},{id:'end',type:'end'}],edges:[{id:'start-work',source:'start',target:'work'},{id:'work-end',source:'work',target:'end'}]};
 const store=await new WorkflowStore(join(root,'packs')).initialize();await store.create(workflow,{resources});const runtime=await new WorkflowRuntime({workflowStore:store,runRoot:join(root,'runs')}).initialize(),run=await runtime.start({workflow_id:workflow.id,workspace,access:'read_only',main_actor:'root'}),lease=await runtime.claimHostMain(run.run_id,{node_id:'work',owner:'root',request_id:'claim',control_token:run.control_token}),binding={node_id:'work',attempt_id:lease.attempt_id,lease_token:lease.lease_token,control_token:run.control_token},record=await runtime.runs.read(run.run_id),objects=join(runtime.runs.directory(run.run_id),'objects');return {runtime,run,binding,record,objects};
}
test('73 objects: ordinary journal read, event, authorization and cancel read no objects; explicit audit reads all',async t=>{
 const f=await fixture(t);let objectReads=0,objectStats=0,report;
 await patched({readFile:async(path,...args)=>{if(String(path).startsWith(f.objects))objectReads++;return native.readFile(path,...args);},lstat:async(path,...args)=>{if(String(path).startsWith(f.objects))objectStats++;return native.lstat(path,...args);}},async()=>{
  await withRunStoreObservation(async()=>{await f.runtime.runs.read(f.run.run_id);await f.runtime.recordExecutorEvent(f.run.run_id,{...f.binding,event:{kind:'codex_event',metadata:{method:'item/started',thread_id:'neutral-thread',turn_id:'neutral-turn',item_id:'neutral-item'}}});await f.runtime.authorizedRun(f.run.run_id,f.binding);await f.runtime.execution(f.run.run_id,f.binding);await f.runtime.cancel(f.run.run_id,{control_token:f.run.control_token});},value=>report=value);
  assert.equal(objectReads,0);assert.equal(objectStats,0);assert.equal(report.resource_audits,0);assert.equal(report.resource_objects,0);
  await f.runtime.runs.audit(f.run.run_id);assert.equal(objectReads,73);assert.equal(objectStats,146,'Each object walks its object directory and checks its leaf; ordinary state reads walk neither');
 });
});
test('unused corrupt objects do not block state reads; actual Node and Skill consumption and explicit audits fail visibly',async t=>{
 const f=await fixture(t),pin=f.record.pins.root.resources.find(r=>r.path==='resource-0.txt');await native.writeFile(join(f.objects,pin.sha256),'changed');await f.runtime.authorizedRun(f.run.run_id,f.binding);await f.runtime.runs.read(f.run.run_id);let effects=0;
 await assert.rejects((async()=>{await readPinnedNodeResources({objectDirectory:f.objects,pins:f.record.pins.root.resources,paths:[pin.path]});effects++;})(),{code:'RUN_RESOURCE_CORRUPT'});assert.equal(effects,0);
 await assert.rejects(loadNodeSkillSnapshots(f.runtime,f.run.run_id,{allowed_skills:[{path:'neutral',resources:[pin]}]}),{code:'RUN_RESOURCE_CORRUPT'});
 await assert.rejects(f.runtime.runs.audit(f.run.run_id),{code:'RUN_RESOURCE_CORRUPT'});await assert.rejects(f.runtime.runs.read(f.run.run_id,{auditHistoryTree:true}),{code:'RUN_RESOURCE_CORRUPT'});
});
test('ordinary reads and authorization still reject changed committed pins and journal',async t=>{
 for(const target of ['pins','journal'])await t.test(target,async t=>{const f=await fixture(t),directory=f.runtime.runs.directory(f.run.run_id);if(target==='pins')await native.writeFile(join(directory,'pins.json'),'{}');else {const path=join(directory,'events.jsonl'),rows=(await native.readFile(path,'utf8')).trim().split('\n').map(JSON.parse);rows.at(-1).hash='0'.repeat(64);await native.writeFile(path,rows.map(JSON.stringify).join('\n')+'\n');}const code=target==='pins'?'RUN_PINS_CORRUPT':'RUN_JOURNAL_CORRUPT';await assert.rejects(f.runtime.runs.read(f.run.run_id),{code});await assert.rejects(f.runtime.authorizedRun(f.run.run_id,f.binding),{code});});
});
for(const fault of ['directory','oversize','symlink'])test(`actual resource ${fault} is rejected before reading bytes`,async t=>{
 const f=await fixture(t),pin=f.record.pins.root.resources[0],path=join(f.objects,pin.sha256);if(fault==='oversize')await native.truncate(path,LIMITS.resource+1);else{await native.unlink(path);if(fault==='directory')await native.mkdir(path);else{const target=join(f.objects,'neutral-target');await native.mkdir(target);await native.symlink(target,path,process.platform==='win32'?'junction':'dir');}}let reads=0;await patched({readFile:async(p,...args)=>{if(p===path)reads++;return native.readFile(p,...args);}},async()=>{await assert.rejects(readPinnedObject(f.objects,pin),{code:fault==='symlink'?'WORKFLOW_SYMLINK':'RUN_RESOURCE'});assert.equal(reads,0);});
});
