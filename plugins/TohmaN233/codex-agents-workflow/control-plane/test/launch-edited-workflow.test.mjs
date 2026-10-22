import test from 'node:test';
import assert from 'node:assert/strict';
import {launchEditedWorkflow,publishEditedWorkflow} from '../web-src/launch-edited-workflow.mjs';
const pack=(revision,status='draft')=>({workflow:{id:'example',status,enabled:true,nodes:[]},revision_hash:revision});
test('publication saves exact edited revision and never starts a task',async()=>{
 const calls=[];
 const result=await publishEditedWorkflow({pack:pack('old','ready'),dirty:true,save:async()=>{calls.push('save');return pack('saved');},request:async(op,args)=>{calls.push(op);assert.equal(op,'publish');assert.equal(args.expected_revision,'saved');assert.equal(Object.hasOwn(args,'reviewed'),false);return pack('published','ready');},onSaved:async()=>calls.push('shown')});
 assert.equal(result.revision_hash,'published');assert.deepEqual(calls,['save','publish','shown']);
});
test('task execution never saves or publishes and refuses dirty or draft revisions',async()=>{
 const args={pack:pack('published','ready'),dirty:false,request:async(op,value)=>{assert.equal(op,'run_main');assert.equal(value.revision_hash,'published');return {run_id:'run'};},options:{revision_hash:'wrong'}};
 assert.equal((await launchEditedWorkflow(args)).run_id,'run');
 for(const change of [{dirty:true},{pack:pack('draft')},{pack:null}])await assert.rejects(launchEditedWorkflow({...args,...change,request:async()=>assert.fail('must not mutate')}),/先发布/);
 await assert.rejects(launchEditedWorkflow({...args,pack:{...args.pack,workflow:{...args.pack.workflow,enabled:false}}}),/已禁用/);
});
test('publication CAS failure does not publish local state',async()=>{
 await assert.rejects(publishEditedWorkflow({pack:pack('old'),dirty:false,request:async()=>{throw Error('revision conflict');},onSaved:async()=>assert.fail('not published')}),/revision conflict/);
});
