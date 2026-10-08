import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, rm, readFile, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { tmpdir } from './physical-tempdir.mjs';
import { WorkflowService } from '../lib/workflow-service.mjs';
import { HostMainManager } from '../lib/execution/host-main-manager.mjs';
import { prepareMainOrchestration } from '../lib/execution/main-orchestration.mjs';
import { isWorkerMain, isOrchestrationMain } from '../lib/execution/main-execution-mode.mjs';
import { retainOwnedAuthority } from '../lib/execution/owned-workflow-authority.mjs';
import { workflowToolDefinitions } from '../lib/workflow-tools.mjs';
import { validateWorkflowGraph } from '../lib/workflow-validator.mjs';
import { readyWorkflow, agent, edge } from './fixtures/workflow-fixtures.mjs';
import { DEFAULT_CONFIG_PATH } from '../server.mjs';
import { launchEditedWorkflow } from '../web-src/launch-edited-workflow.mjs';

const thread = '12345678-1234-4234-8234-123456789abc';
const schema = { type: 'object', properties: { conclusion: {type:'string'} }, required: ['conclusion'], additionalProperties: false };
async function fixture(t, {write = false, resources = {}, mutateWorkflow = () => {}} = {}) {
  const directory = await mkdtemp(join(tmpdir(), 'main-orchestration-'));
  t.after(() => rm(directory, {recursive:true,maxRetries:3,retryDelay:100}));
  const workspace = join(directory, 'workspace'); await mkdir(workspace);
  let sessions = 0;
  const manager = new HostMainManager({configPath:join(directory,'control-plane.json'),getConfig:async()=>({}),
    qualify:async()=>{throw new Error('Orchestration must not qualify an isolated executor');},
    sessionFactory:async()=>{sessions++;throw new Error('Orchestration must not create a session');}});
  t.after(()=>manager.close());
  const service = new WorkflowService({configPath:join(directory,'control-plane.json'),defaultConfigPath:DEFAULT_CONFIG_PATH,env:{},
    capabilities:{hostMainManager:manager,nativeAgentObserver:null,nativeParentVerifier:async()=>({agent_path:'/root'})}});
  await service.call('migrate_v6',{}, {human:true});
  const workflow = readyWorkflow('main-orchestration');
  workflow.context_projection_version = 2;
  workflow.skill_policy.mode = 'cooperative';
  workflow.inputs_schema = {type:'object',properties:{task:{type:'string'}},required:['task'],additionalProperties:false};
  const node = workflow.nodes.find(item=>item.id==='final');
  node.executor = {kind:'main',mode:'orchestration'}; node.retry.max_attempts=3;
  node.outputs_schema=schema;node.prompt_template='Resolve the user decision using the current working context.';
  node.input_bindings={task:'/inputs/task'};node.resources=Object.keys(resources);
  if(write){node.access='bounded_write';node.path_scope=['result.txt'];node.required_artifacts=[{path:'result.txt',requirement_id:'result'}];}
  mutateWorkflow(workflow);
  const pack = await service.call('create',{workflow,resources});
  const options = {workflow_id:workflow.id,revision_hash:pack.revision_hash,workspace,access:write?'bounded_write':'read_only',
    ...(write?{allowed_paths:['result.txt']}:{}),inputs:{task:'Use our prior conclusions'},main_actor:'codex',native_parent_thread_id:thread};
  const handoff = await service.call('begin_main',options);
  const {runtime}=await service.open();
  const {run_id,control_token}=handoff.host_binding;
  await retainOwnedAuthority(runtime,{run_id,control_token});
  return {service,manager,runtime,workflow,workspace,options,handoff,run_id,control_token,sessions:()=>sessions};
}

test('Main modes distinguish current conversation from isolated workers and reject invented modes',()=>{
  const workflow=readyWorkflow();workflow.skill_policy.mode='cooperative';
  const final=workflow.nodes.find(node=>node.id==='final');
  assert(isWorkerMain(final));assert(!isOrchestrationMain(final));
  final.executor.mode='orchestration';assert(isOrchestrationMain(final));assert(!isWorkerMain(final));
  assert(validateWorkflowGraph(workflow).valid);
  final.executor.mode='resumed-worker';assert(validateWorkflowGraph(workflow).errors.some(item=>item.code==='MAIN_EXECUTION_MODE'));
  final.executor={kind:'provider',provider_id:'somewhere',mode:'orchestration'};
  assert(!isOrchestrationMain(final));
});

test('orchestration receives a compact Host bundle and completes in the bound conversation without a session',async t=>{
  const f=await fixture(t,{resources:{'reference.txt':'The approved technical conclusion'}});
  assert.equal(f.handoff.stop_reason,'main_orchestration');
  const result=await f.service.call('native_next',{}, {model:true,modelThreadId:thread});
  assert.equal(result.status,'orchestration_handoff');assert.equal(result.context,'current_conversation');
  for(const key of ['run_id','node_id','attempt_id','control_token','lease_token','host_binding'])assert(!Object.hasOwn(result,key));
  const bundle=JSON.parse(await readFile(result.task_bundle_path,'utf8'));
  assert.equal(bundle.resources.length,1);
  assert.equal(await readFile(bundle.resources[0].local_path,'utf8'),'The approved technical conclusion');
  const second=await f.service.call('native_next',{}, {model:true,modelThreadId:thread});
  assert.deepEqual(second,result,'Reopening the handoff reuses its exact receipt and task bundle');
  await assert.rejects(f.service.call('orchestration_complete',{output:{conclusion:'wrong chat'}},{model:true,modelThreadId:'22345678-1234-4234-8234-123456789abc'}),{code:'MODEL_RUN_AUTHORITY'});
  const completed=await f.service.call('orchestration_complete',{output:{conclusion:'Applied the earlier decision'}},{model:true,modelThreadId:thread});
  assert.equal(completed.status,'succeeded');assert.equal(completed.completion_satisfied,true);
  assert.equal(f.sessions(),0);
  const record=await f.runtime.runs.read(f.run_id);
  assert.equal(record.state.nodes.final.output.conclusion,'Applied the earlier decision');
  assert.equal(record.state.nodes.final.attempts[0].dispatch.receipt.thread_id,thread);
});

test('semantic correction stays in the same orchestration attempt and writes only required products',async t=>{
  const f=await fixture(t,{write:true});
  await f.service.call('native_next',{}, {model:true,modelThreadId:thread});
  await assert.rejects(f.service.call('orchestration_complete',{output:{conclusion:'Missing artifact'}},{model:true,modelThreadId:thread}),{code:'REQUIRED_ARTIFACT_MISSING'});
  await writeFile(join(f.workspace,'result.txt'),'Resolved from current context');
  await f.service.call('orchestration_complete',{output:{conclusion:'Repaired only the missing file'}},{model:true,modelThreadId:thread});
  const record=await f.runtime.runs.read(f.run_id);
  assert.equal(record.state.status,'succeeded');assert.equal(record.state.nodes.final.attempts.length,1);
  assert.equal(record.state.nodes.final.attempts[0].completion_turns,2);
});

test('rejected producer output can be corrected before pinning an immutable Main result', async t => {
  const f = await fixture(t, { mutateWorkflow: workflow => {
    const work = { ...agent('work'), executor: { kind: 'main', mode: 'orchestration' }, retry: { max_attempts: 3 },
      outputs_schema: { type: 'object', properties: { jobs: { type: 'array', items: { type: 'string' } } }, required: ['jobs'], additionalProperties: false } };
    const pool = { ...agent('pool'), executor: { kind: 'provider', provider_id: 'native-luna' }, subagent_count: 'auto',
      input_bindings: { items: '/nodes/work/output/jobs' },
      fanout: { input: 'items', item_name: 'item', result_output: 'results', distribution: 'one_per_item', scheduling: 'parallel', join: 'all_required' },
      outputs_schema: { type: 'object', properties: { results: { type: 'array', items: { type: 'string' } } }, required: ['results'], additionalProperties: false } };
    workflow.nodes.splice(1, 0, work, pool);
    workflow.edges = [edge('start', 'work'), edge('work', 'pool'), edge('pool', 'final'), edge('final', 'end')];
  } });
  await f.service.call('native_next', {}, { model: true, modelThreadId: thread });
  await assert.rejects(f.service.call('orchestration_complete', { output: { jobs: [] } }, { model: true, modelThreadId: thread }),
    { code: 'SUBAGENT_FANOUT_INPUT' });
  const rejected = await f.runtime.runs.read(f.run_id);
  assert.equal(rejected.state.nodes.work.attempts[0].result_proposal, undefined);
  assert.equal(rejected.state.nodes.work.status, 'running');
  await f.service.call('orchestration_complete', { output: { jobs: ['valid'] } }, { model: true, modelThreadId: thread });
  const corrected = await f.runtime.runs.read(f.run_id);
  assert.equal(corrected.state.nodes.work.status, 'succeeded');
  assert.deepEqual(corrected.state.nodes.work.output, { jobs: ['valid'] });
  assert.equal(corrected.state.nodes.work.attempts.length, 1);
  assert.equal(corrected.state.nodes.work.attempts[0].completion_turns, 2);
  assert.equal(f.sessions(), 0);
});

test('orchestration rejects out-of-scope modifications and retains exact failure evidence',async t=>{
  const f=await fixture(t,{write:true});
  await f.service.call('native_next',{}, {model:true,modelThreadId:thread});
  await writeFile(join(f.workspace,'unexpected.txt'),'outside');
  await assert.rejects(f.service.call('orchestration_complete',{output:{conclusion:'done'}},{model:true,modelThreadId:thread}),{code:'MAIN_ORCHESTRATION_SCOPE_VIOLATION'});
  const record=await f.runtime.runs.read(f.run_id);
  assert(record.state.nodes.final.attempts[0].executor_events.some(item=>item.kind==='scope_violation'));
});

test('a standalone launch cannot silently substitute an isolated session for orchestration',async t=>{
  const f=await fixture(t);
  const {native_parent_thread_id,...withoutContext}=f.options;
  const count=(await f.service.call('runs')).length;
  await assert.rejects(f.service.call('run_main',withoutContext),{code:'MAIN_ORCHESTRATION_CONTEXT'});
  assert.equal((await f.service.call('runs')).length,count);
  await assert.rejects(prepareMainOrchestration(f.runtime,{run_id:f.run_id,control_token:f.control_token,thread_id:'different'}),{code:'MAIN_ORCHESTRATION_CONTEXT'});
});

test('the completion tool accepts semantic output only and the App sends orchestration launch to the conversation',async()=>{
  const definition=workflowToolDefinitions().find(tool=>tool.name==='workflow_orchestration_complete');
  assert.deepEqual(Object.keys(definition.inputSchema.properties),['output']);
  const workflow=readyWorkflow();workflow.nodes.find(node=>node.id==='final').executor.mode='orchestration';
  let sent=0;
  const launch=()=>launchEditedWorkflow({pack:{workflow,revision_hash:'revision'},dirty:false,request:()=>{throw new Error('No detached launch');},
    options:{inputs:{task:'Use earlier conclusions'},workspace:'/project'},conversationLaunch:async request=>{sent++;assert.equal(request.task,'Use earlier conclusions');}});
  assert.deepEqual(await launch(),{conversation_requested:true});assert.equal(sent,1);
});


test('exhausted orchestration corrections fail visibly without starting another session',async t=>{
  const f=await fixture(t,{write:true});
  await f.service.call('native_next',{}, {model:true,modelThreadId:thread});
  for(let turn=0;turn<3;turn++) await assert.rejects(
    f.service.call('orchestration_complete',{output:{conclusion:'Still missing output'}},{model:true,modelThreadId:thread}),
    {code:'REQUIRED_ARTIFACT_MISSING'});
  const record=await f.runtime.runs.read(f.run_id);
  assert.equal(record.state.status,'failed');
  assert.equal(record.state.nodes.final.attempts.length,1);
  assert.equal(record.state.nodes.final.attempts[0].completion_turns,3);
  assert.equal(f.sessions(),0);
});


test('Run startup applies 24-hour cleanup and the Workbench clears recent terminal history only',async t=>{
  const f=await fixture(t);
  await f.service.call('native_next',{}, {model:true,modelThreadId:thread});
  await f.service.call('orchestration_complete',{output:{conclusion:'completed'}},{model:true,modelThreadId:thread});
  const record=await f.runtime.runs.read(f.run_id);
  const state=structuredClone(record.state);
  state.run_id='old-completed';state.finished_at='2020-01-01T00:00:00.000Z';state.updated_at=state.finished_at;
  await f.runtime.runs.create(state.run_id,record.pins,new Map(),state);
  const newRun=await f.service.call('begin_main',f.options);
  await assert.rejects(f.runtime.runs.read('old-completed'),{code:'ENOENT'});
  assert.equal((await f.runtime.runs.read(f.run_id)).state.status,'succeeded');
  const cleaned=await f.service.call('cleanup_run_history',{}, {human:true});
  assert.deepEqual(cleaned.deleted_run_ids,[f.run_id]);
  assert.equal((await f.runtime.runs.read(newRun.host_binding.run_id)).state.status,'running');
});
