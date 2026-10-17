import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,mkdir,readFile,rm} from 'node:fs/promises';
import {join} from 'node:path';
import {tmpdir} from './physical-tempdir.mjs';
import {digest} from '../lib/workflow-revisions.mjs';
import {HostToolRunner,validateHostToolContract} from '../lib/execution/host-tool-runner.mjs';
import {createCodexToolBroker} from '../lib/execution/codex-tool-broker.mjs';
import {workflowResourceProgramIdentity,workflowResourceProgramRegistry} from '../lib/execution/workflow-resource-program.mjs';
import {rebindBuiltinHostToolIdentities} from '../lib/workflow-host-tool-identity.mjs';
const effects=()=>({observed:true,changed_paths:[],outside_paths:[],artifacts:[]});
const identity={name:'deadline-fixture',version:'1',sha256:digest('deadline-fixture')};
const contract=(deadline_ms=1000)=>({id:'deadline-fixture',identity,argv:[],input_schema:{type:'object',additionalProperties:false},output_schema:{type:'object',properties:{ok:{type:'boolean'}},required:['ok'],additionalProperties:false},env_allow:[],permissions:{network:false,read_paths:[],write_paths:[]},output_cap_bytes:1024,deadline_ms,idempotency:{mode:'safe'}});
const context=()=>({run_id:'run',node_id:'node',attempt_id:'attempt',deadline_ms:1,permissions:{access:'read_only',allowed_paths:[]}});
function deferred(){let resolve,reject;const promise=new Promise((yes,no)=>{resolve=yes;reject=no;});return {promise,resolve,reject};}
const termination=()=>({termination_confirmed:true,evidence:[{kind:'settled',sha256:digest('settled')}],effects:effects()});
function registry(execute,cancel=async()=>termination()) {return {[identity.name]:{identity,attestation:{qualified:true,cancellable:true,effect_observation:true,tool_identity:identity,broker_id:'deadline-fixture-broker',evidence_sha256:digest('qualified')},execute,cancel}};}

test('Host accepts the explicit one-hour bound and rejects invalid/larger bounds',()=>{
 for(const value of [1,300000,3600000])assert.equal(validateHostToolContract(contract(value)).deadline_ms,value);
 for(const value of [0,-1,1.5,3600001,Number.MAX_SAFE_INTEGER])assert.throws(()=>validateHostToolContract(contract(value)),{code:'HOST_TOOL_CONTRACT'});
});

test('one-hour Host execution uses its pinned deadline and settles success/nonzero failure once',async()=>{
 for(const exit_code of [0,7]){
  let calls=0,cancels=0,deadline;
  const runner=new HostToolRunner({registry:registry(async({context:received})=>{calls++;deadline=received.deadline_ms;return {exit_code,output:{ok:true},diagnostic:exit_code?'deliberate failure':'',effects:effects()};},async()=>{cancels++;return termination();})});
  const result=await runner.execute(contract(3600000),{},context());
  assert.equal(deadline,3600000);assert.equal(calls,1);assert.equal(cancels,0);
  assert.equal(result.receipt.status,exit_code?'failed':'succeeded');assert.equal(result.receipt.exit_code,exit_code);
  assert.deepEqual(result.output,exit_code?null:{ok:true});
 }
});

test('long Host cancellation waits for confirmed settlement and preserves cancellation receipt',async()=>{
 const started=deferred(),stopping=deferred(),release=deferred(),controller=new AbortController();let calls=0,settled=false,returned=false;
 const runner=new HostToolRunner({registry:registry(async({signal})=>{calls++;started.resolve();return await new Promise((resolve)=>signal.addEventListener('abort',()=>resolve({exit_code:9,output:null,diagnostic:'stopped',effects:effects()}),{once:true}));},async()=>{stopping.resolve();await release.promise;settled=true;return termination();})});
 const pending=runner.execute(contract(3600000),{},context(),{signal:controller.signal}).then(result=>{returned=true;return result;});
 await started.promise;controller.abort(new Error('explicit cancellation'));await stopping.promise;
 assert.equal(returned,false);assert.equal(settled,false);release.resolve();
 const result=await pending;assert.equal(calls,1);assert.equal(settled,true);assert.equal(result.receipt.status,'cancelled');assert.equal(result.receipt.reconciliation.termination_confirmed,true);assert.equal(result.output,null);
});

test('short Host timeout and thrown error still require termination; cleanup failure remains visible',async()=>{
 let cancelled=0;
 const pendingRunner=new HostToolRunner({registry:registry(async()=>new Promise(()=>{}),async()=>{cancelled++;return termination();})});
 const stopped=await pendingRunner.execute(contract(5),{},context());assert.equal(stopped.receipt.status,'timed_out');assert.equal(cancelled,1);assert.equal(stopped.receipt.reconciliation.termination_confirmed,true);
 const failure=Object.assign(new Error('original broker failure'),{code:'FIXTURE_FAILURE'});
 const failingRunner=new HostToolRunner({registry:registry(async()=>{throw failure;},async()=>{cancelled++;return termination();})});
 await assert.rejects(failingRunner.execute(contract(3600000),{},context(),{receiptOnError:true}),error=>error===failure&&error.host_tool_receipt.status==='cancelled');assert.equal(cancelled,2);
 const unconfirmed=new HostToolRunner({registry:registry(async()=>{throw new Error('original error');},async()=>{throw new Error('termination unconfirmed');})});
 await assert.rejects(unconfirmed.execute(contract(3600000),{},context(),{receiptOnError:true}),error=>error instanceof AggregateError&&error.errors.some(item=>item.message==='original error')&&error.errors.some(item=>item.message==='termination unconfirmed'));
});

async function workspace(t){const path=await mkdtemp(join(tmpdir(),'host-deadline-'));t.after(()=>rm(path,{recursive:true,maxRetries:3,retryDelay:100}));await mkdir(join(path,'work'));return path;}
function captureTimers(t){const timeouts=[],pending=new Map(),original=globalThis.setTimeout,clear=globalThis.clearTimeout;t.mock.method(globalThis,'setTimeout',(callback,timeout,...args)=>{timeouts.push(timeout);const handle=original(callback,timeout,...args);pending.set(handle,timeout);return handle;});t.mock.method(globalThis,'clearTimeout',handle=>{pending.delete(handle);return clear(handle);});timeouts.pending=pending;return timeouts;}
const environment=()=>({status:'ready',tools:[{name:'node',path:process.execPath,status:'found'}]});

test('one-hour pinned resource deadline reaches native broker after executable preparation and clears timers',async t=>{
 const root=await workspace(t),timeouts=captureTimers(t);let preparations=0;
 const path='source/check.mjs',bytes=Buffer.from('console.log(JSON.stringify({ok:true}));');
 const declared={...contract(3600000),id:'resource-deadline',identity:workflowResourceProgramIdentity(),argv:['node',path,'work/.runtime'],permissions:{network:false,read_paths:[path],write_paths:['work']}};
 const result=await new HostToolRunner({registry:workflowResourceProgramRegistry()}).execute(declared,{}, {...context(),workspace:root,permissions:{access:'bounded_write',allowed_paths:['work']},resources:[{path,sha256:digest(bytes),bytes}],runtime_environment:environment(),prepareRuntimeEnvironment:async()=>{preparations++;return {environment:environment()};}});
 assert.equal(result.receipt.status,'succeeded',result.receipt.diagnostics.message);assert.deepEqual(result.output,{ok:true});assert.equal(preparations,1);
 assert.equal(timeouts.filter(value=>value===3600000).length,2,'Both the Host and prepared command must use the explicit one-hour deadline');assert.equal(timeouts.includes(300000),false);
 assert.equal([...timeouts.pending.values()].includes(3600000),false,'Both one-hour timers must be cleared after terminal settlement');
 await assert.rejects(readFile(join(root,'work/.runtime',digest(bytes)+'.mjs')),{code:'ENOENT'});
});

test('ordinary program broker default stays five minutes; explicit Host broker bounds cannot be widened by arguments',async t=>{
 const root=await workspace(t),timeouts=captureTimers(t),options={workspace:root,access:'bounded_write',allowedPaths:['work'],runtimeEnvironment:environment(),prepareRuntimeEnvironment:async()=>({environment:environment()}),authorize:async()=>{},onOperation:async()=>{}};
 const defaultBroker=await createCodexToolBroker(options);const result=await defaultBroker.call('run_task_program',{program:'node',args:['-p','6*7'],cwd:'workspace'},'default');
 assert.equal(JSON.parse(result.contentItems[0].text).exit_code,0);assert(timeouts.includes(300000));await defaultBroker.quiesce();
 for(const invalid of [0,3600001,1.5])await assert.rejects(createCodexToolBroker({...options,programDeadlineMs:invalid}),{code:'CODEX_EXECUTION_BINDING'});
 const hostBroker=await createCodexToolBroker({...options,programDeadlineMs:3600000});
 await assert.rejects(hostBroker.call('run_task_program',{program:'node',args:['-p','42'],cwd:'workspace',programDeadlineMs:3600001},'invalid'),{code:'CODEX_TOOL_ARGUMENTS'});await hostBroker.quiesce();
});

test('deadline plumbing rebinds only the exact prior resource-program identity',()=>{
 const previous={name:'workflow-resource-program',version:'1',sha256:'00833a81d3b9c1ada37182077befd5e9eb812bd6c6e20f83b81646e726231ebb'};
 const workflow={host_tools:[{...contract(3600000),identity:previous}]},before=structuredClone(workflow);
 const rebound=rebindBuiltinHostToolIdentities(workflow);assert.deepEqual(workflow,before);assert.equal(rebound.changes.length,1);assert.deepEqual(rebound.workflow.host_tools[0].identity,workflowResourceProgramIdentity());
 assert.deepEqual(rebindBuiltinHostToolIdentities(rebound.workflow).changes,[]);
 assert.throws(()=>rebindBuiltinHostToolIdentities({host_tools:[{...contract(),identity:{...previous,sha256:'f'.repeat(64)}}]}),{code:'HOST_TOOL_IDENTITY_MIGRATION_UNSUPPORTED'});
});
