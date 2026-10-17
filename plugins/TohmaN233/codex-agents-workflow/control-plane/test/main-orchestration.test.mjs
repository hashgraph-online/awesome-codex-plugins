import test from 'node:test';
import nativeFs from 'node:fs/promises';
import {syncBuiltinESMExports} from 'node:module';
import {snapshotWorkspace} from '../lib/execution/workspace-snapshot.mjs';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, rm, readFile, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { tmpdir } from './physical-tempdir.mjs';
import { WorkflowService } from '../lib/workflow-service.mjs';
import {WorkflowRuntime} from '../lib/workflow-runtime.mjs';
import { HostMainManager } from '../lib/execution/host-main-manager.mjs';
import { prepareMainOrchestration, completeMainOrchestration,terminalMainInputStage } from '../lib/execution/main-orchestration.mjs';
import { isWorkerMain, isOrchestrationMain } from '../lib/execution/main-execution-mode.mjs';
import { retainOwnedAuthority } from '../lib/execution/owned-workflow-authority.mjs';
import { workflowToolDefinitions } from '../lib/workflow-tools.mjs';
import { validateWorkflowGraph } from '../lib/workflow-validator.mjs';
import { readyWorkflow, agent, edge } from './fixtures/workflow-fixtures.mjs';
test('terminal Main input stage excludes future workers, loops and nonfinal Main nodes',()=>{
  const graph={finalization:{node_id:'main'},nodes:[{id:'main',type:'agent'},{id:'end',type:'end'},{id:'child',type:'agent'}],edges:[{source:'main',target:'end'}]};
  assert.equal(terminalMainInputStage(graph,'main'),true);assert.equal(terminalMainInputStage(graph,'child'),false);
  for(const target of ['main','child','missing'])assert.equal(terminalMainInputStage({...graph,edges:[{source:'main',target}]},'main'),false);
  assert.equal(terminalMainInputStage({...graph,edges:[]},'main'),false);
});
test('last semantic Main remains terminal when the declared Host finalizer only records its result',()=>{
  const graph={finalization:{node_id:'commit'},nodes:[{id:'review',type:'agent'},
    {id:'commit',type:'tool',executor:{kind:'tool',tool:'commit'},input_bindings:{output:'/nodes/review/output'}},
    {id:'end',type:'end'},{id:'worker',type:'agent'}],edges:[{source:'review',target:'commit'},{source:'commit',target:'end'}]};
  assert.equal(terminalMainInputStage(graph,'review'),true);
  for(const change of [g=>g.nodes.find(n=>n.id==='commit').type='agent',g=>g.edges[1].target='worker',
    g=>g.edges.push({source:'review',target:'worker'}),g=>g.nodes.find(n=>n.id==='commit').input_bindings={task:'/inputs/task'}]){
    const other=structuredClone(graph);change(other);assert.equal(terminalMainInputStage(other,'review'),false);
  }
});
import { DEFAULT_CONFIG_PATH,handleRpc } from '../server.mjs';
import {foregroundActivityCount,inForegroundActivity} from '../lib/foreground-activity.mjs';
import { launchEditedWorkflow } from '../web-src/launch-edited-workflow.mjs';
import { canonicalJSON, digest } from '../lib/workflow-revisions.mjs';
import {WorkflowExecutor} from '../lib/workflow-executor.mjs';
import {HostToolRunner} from '../lib/execution/host-tool-runner.mjs';
import {AttemptAdmissionRegistry} from '../lib/execution/attempt-admission.mjs';
import { schemaAcceptedBy } from '../lib/execution/main-host-check.mjs';
import { leaseToken } from '../lib/workflow-execution-envelope.mjs';
import { hostResultProposalEnvelope } from '../lib/execution/host-main-automation.mjs';
import { materializeNativeTaskBundle } from '../lib/execution/node-input-materials.mjs';

const thread = '12345678-1234-4234-8234-123456789abc';

test('current Main prepares and completes with an unrelated file larger than 2 GiB without reading it',async t=>{
 const f=await fixture(t),outside=join(f.workspace,'large-unrelated');await writeFile(outside,'small physical fixture');
 const originalStat=nativeFs.lstat,originalRead=nativeFs.readFile;
 t.mock.method(nativeFs,'lstat',async(path,...args)=>{const info=await originalStat(path,...args);if(path===outside)info.size=typeof info.size==='bigint'?2147483649n:2147483649;return info;});
 t.mock.method(nativeFs,'readFile',async(path,...args)=>{assert.notEqual(path,outside,'Main scope observation must not read unrelated contents');return originalRead(path,...args);});syncBuiltinESMExports();
 try{
  await f.service.call('native_next',{}, {model:true,modelThreadId:thread});
  const result=await f.service.call('orchestration_complete',{output:{conclusion:'Selected the documentation scope.'}}, {model:true,modelThreadId:thread});
  assert.equal(result.status,'succeeded');assert.equal(f.sessions(),0);
 }finally{t.mock.restoreAll();syncBuiltinESMExports();}
});
test('current Main replays a historical content baseline without changing its observation mode',async t=>{
 const f=await fixture(t);await writeFile(join(f.workspace,'unchanged.txt'),'retained content');
 const prototype=Object.getPrototypeOf(f.runtime.runs),save=prototype.saveArtifact;
 t.mock.method(prototype,'saveArtifact',async function(id,label,bytes){
  if(label.startsWith('orchestration-before-')){
   const legacy=await snapshotWorkspace(f.workspace);
   bytes=canonicalJSON({files:[...legacy],unreadable:[...legacy.unreadablePaths]});
  }
  return save.call(this,id,label,bytes);
 });
 await f.service.call('native_next',{}, {model:true,modelThreadId:thread});
 const {receipt}=await retainedMainBundle(f);
 const saved=JSON.parse((await f.runtime.runs.readArtifact(f.run_id,receipt.before_snapshot)).toString('utf8'));
 assert.equal(Object.hasOwn(saved,'hash_paths'),false);
 const result=await f.service.call('orchestration_complete',{output:{conclusion:'Retained the prior content observation.'}}, {model:true,modelThreadId:thread});
 assert.equal(result.status,'succeeded');
});

const schema = { type: 'object', properties: { conclusion: {type:'string'} }, required: ['conclusion'], additionalProperties: false };
function hostCheckFixture({ verified = true, exit = 0, write = true, changed = 'result.txt', deadline = 1000, execute } = {}) {
  const tool = { id: 'final-check', identity: { name: 'final-check-fixture', version: '1', sha256: digest('fixture') },
    argv: ['check'], input_schema: { type: 'object', properties: { inputs: {}, output: schema }, required: ['inputs','output'], additionalProperties: false },
    output_schema: { type: 'object', properties: { verified: {type:'boolean'} }, required: ['verified'], additionalProperties: false },
    env_allow: [], permissions: { network: false, read_paths: ['.'], write_paths: ['result.txt'] }, output_cap_bytes: 1024,
    deadline_ms: deadline, idempotency: { mode: 'safe' } };
  const calls = [];
  const broker = { identity: tool.identity, attestation: { qualified: true, cancellable: true, effect_observation: true,
    tool_identity: tool.identity, broker_id: 'check-broker', evidence_sha256: digest('qualification') },
    execute: async request => {
      calls.push(request);
      if (execute) return execute(request);
      if (write) await writeFile(join(request.context.workspace, changed), request.input.output.conclusion);
      return { exit_code: exit, output: { verified }, diagnostic: exit ? 'checker exited unsuccessfully' : '',
        effects: { observed: true, changed_paths: write ? [changed] : [], outside_paths: [], artifacts: [] } };
    },
    cancel: async () => ({ termination_confirmed: true, evidence: [{kind:'termination',sha256:digest('stopped')}],
      effects: { observed:true,changed_paths:[],outside_paths:[],artifacts:[] } }) };
  const install = workflow => {
    workflow.host_tools = [tool];
    const node = workflow.nodes.find(item => item.id === 'final');
    node.completion_contract = { on_missing:'block',outcome:'decision',host_check:{tool:tool.id,success_field:'verified'} };
  };
  return { tool, broker, calls, install, registry: { [tool.id]: broker } };
}
async function fixture(t, {write = false, resources = {}, mutateWorkflow = () => {}, hostToolRegistry = {}, allowedPaths = ['result.txt'], extraInputs = {},runtimeEnv={},expectedDrainFailure=false,legacyTaskDelivery=false} = {}) {
  const directory = await mkdtemp(join(tmpdir(), 'main-orchestration-'));
  let service;
  t.after(async () => {
    if(service){
      const drain=Promise.all(service.attemptAdmission.drainJobs.values());
      if(expectedDrainFailure)await assert.rejects(drain,error=>{
        assert.equal(error.code,'RUN_EXECUTION_STOP_INCOMPLETE');
        assert.equal(error.errors.length,1);assert.equal(error.errors[0].code,'ATTEMPT_STOP_INCOMPLETE');
        assert.equal(error.errors[0].errors.length,1);
        assert.equal(service.attemptAdmission.entries.size,1,'Unconfirmed exact effect owner remains retained');
        const owner=[...service.attemptAdmission.entries.values()][0];
        assert.equal(error.errors[0].errors[0],owner.result.error,'The original effect failure remains exact in the cleanup failure');
        if(expectedDrainFailure==='scope')assert.equal(owner.result.error.code,'HOST_TOOL_SCOPE');
        else assert.equal(owner.result.error.message,'lost broker response');
        assert.equal(owner.intent_pending,true);assert.equal(owner.receipt_recorded,false);assert.equal(owner.cleanupConfirmed,false);
        return true;
      });else await drain;
      if(expectedDrainFailure){
        const owner=[...service.attemptAdmission.entries.values()][0];
        await assert.rejects(owner.cleanup(),{code:'HOST_TOOL_CANCEL_INCOMPLETE'});
        assert.equal(service.attemptAdmission.entries.get(owner.admission_key),owner);
        assert.equal(owner.cleanupConfirmed,false);
      }
    }
    if (service) await service.historyMaintenance.settle();
    if (service) await service.historyMaintenance.close();
    await rm(directory, {recursive:true,maxRetries:3,retryDelay:100});
  });
  const workspace = join(directory, 'workspace'); await mkdir(workspace);
  let sessions = 0;
  const manager = new HostMainManager({configPath:join(directory,'control-plane.json'),getConfig:async()=>({}),
    qualify:async()=>{throw new Error('Orchestration must not qualify an isolated executor');},
    sessionFactory:async()=>{sessions++;throw new Error('Orchestration must not create a session');}});
  t.after(()=>manager.close());
  service = new WorkflowService({configPath:join(directory,'control-plane.json'),defaultConfigPath:DEFAULT_CONFIG_PATH,env:runtimeEnv,
    capabilities:{hostMainManager:manager,hostToolRegistry,nativeAgentObserver:null,nativeParentVerifier:async()=>({agent_path:'/root'})}});
  await service.call('migrate_v6',{}, {human:true});
  const workflow = readyWorkflow('main-orchestration');
  workflow.context_projection_version = 2;
  workflow.skill_policy.mode = 'cooperative';
  workflow.inputs_schema = {type:'object',properties:{task:{type:'string'}},required:['task'],additionalProperties:false};
  const node = workflow.nodes.find(item=>item.id==='final');
  node.executor = {kind:'main',mode:'orchestration'}; node.retry.max_attempts=3;
  node.outputs_schema=schema;node.prompt_template='Resolve the user decision using the current working context.';
  node.input_bindings={task:'/inputs/task'};node.resources=Object.keys(resources);
  if(write){node.access='bounded_write';node.path_scope=allowedPaths;node.required_artifacts=[{path:'result.txt',requirement_id:'result'}];}
  mutateWorkflow(workflow);
  const pack = await service.call('create',{workflow,resources}).catch(error=>{
    if(error.validation)error.message+=' '+JSON.stringify(error.validation);
    throw error;
  });
  const options = {workflow_id:workflow.id,revision_hash:pack.revision_hash,workspace,access:write?'bounded_write':'read_only',
    ...(write?{allowed_paths:allowedPaths}:{}),inputs:{task:'Use our prior conclusions',...extraInputs},main_actor:'codex',native_parent_thread_id:thread};
  const handoff = await service.call('begin_main',options);
  const {runtime}=await service.open();
  if(legacyTaskDelivery){
    const record=WorkflowRuntime.prototype.recordHostMainDispatchReceipt;
    t.mock.method(WorkflowRuntime.prototype,'recordHostMainDispatchReceipt',function(runId,args){
      delete args.receipt.task_inline_limit;
      return record.call(this,runId,args);
    });
  }
  const {run_id,control_token}=handoff.host_binding;
  await retainOwnedAuthority(runtime,{run_id,control_token});
  return {service,manager,runtime,workflow,workspace,options,handoff,run_id,control_token,sessions:()=>sessions};
}

async function retainedMainBundle(f) {
  const record = await f.runtime.runs.read(f.run_id);
  const receipt = record.state.nodes.final.attempts[0].dispatch.receipt;
  const bytes = await readFile(receipt.task_bundle_path), bundle = JSON.parse(bytes);
  return { receipt, bytes, bundle };
}

test('terminal Main whole reply budget keeps an exact public semantic input reference without truncation',async t=>{
  const value='\u0001'.repeat(13000);
  const f=await fixture(t,{extraInputs:{large:value},mutateWorkflow:workflow=>{
    workflow.inputs_schema.properties.large={type:'string'};
    workflow.nodes.find(node=>node.id==='final').input_bindings.large='/inputs/large';
    workflow.nodes.find(node=>node.id==='final').outputs_schema={...schema,description:'declared semantic schema '.repeat(1300)};
  }});
  const result=await f.service.call('native_next',{}, {model:true,modelThreadId:thread});
  assert.equal(result.semantic_input_delivery,'file');assert.equal(Object.hasOwn(result,'semantic_inputs'),false);
  const {bundle}=await retainedMainBundle(f),metadata=JSON.parse(await readFile(bundle.context_preparation.path));
  const input=metadata.inputs.find(item=>item.name==='large');
  assert.equal(await readFile(input.path,'utf8'),value);
  const publicTask=result.task_bundle??JSON.parse(await readFile(result.task_bundle_path));
  const inputs=JSON.parse(publicTask.task.split('\nInputs:\n')[1].split('\n')[0]);
  assert(inputs.large.includes(canonicalJSON(input.path)));
  assert(!JSON.stringify(result).includes(bundle.context_preparation.path));
});

for (const lane of ['inline', 'file']) test(`semantic Main projection hides Host preparation addresses in ${lane} native_next handoff`, async t => {
  const f = await fixture(t, { legacyTaskDelivery:true,mutateWorkflow: workflow => {
    if (lane === 'file') workflow.nodes.find(node => node.id === 'final').prompt_template = 'Bounded task ' + 'instruction '.repeat(1000);
  } });
  const result = await f.service.call('native_next', {}, { model: true, modelThreadId: thread });
  assert.equal(result.task_delivery, lane);
  const record = await f.runtime.runs.read(f.run_id), receipt = record.state.nodes.final.attempts[0].dispatch.receipt;
  const canonical = JSON.parse(await readFile(receipt.task_bundle_path));
  const packet = lane === 'inline' ? result.task_bundle : JSON.parse(await readFile(result.task_bundle_path));
  assert.deepEqual(Object.keys(packet).sort(), ['schema_version', 'task']);
  assert.equal(packet.task, canonical.task);
  assert.equal(JSON.stringify(result).includes(receipt.task_bundle_path), false);
  assert.equal(JSON.stringify(result).includes(canonical.context_preparation.path), false);
  if (lane === 'inline') assert.equal(Object.hasOwn(result, 'task_bundle_path'), false);
  else {
    assert.notEqual(result.task_bundle_path, receipt.task_bundle_path);
    assert.equal(digest(await readFile(result.task_bundle_path)), result.task_bundle_sha256);
  }
});

for (const lane of ['inline', 'file']) test(`semantic Main projection reopens an existing canonical ${lane} receipt without changing diagnostics or sidecars`, async t => {
  const context = 'RETAIN_DECLARED_VALUE_'.repeat(1000), reference = 'RETAIN_DECLARED_RESOURCE_'.repeat(700);
  assert(Buffer.byteLength(context)>16384&&Buffer.byteLength(reference)>16384,'Sidecar coverage must not depend on temporary path length');
  const f = await fixture(t, { legacyTaskDelivery:true,resources: { 'reference.txt': reference }, extraInputs: { context }, mutateWorkflow: workflow => {
    workflow.inputs_schema.properties.context = { type: 'string' };
    const node = workflow.nodes.find(node => node.id === 'final');
    node.input_bindings.context = '/inputs/context';
    if (lane === 'file') node.prompt_template = 'Bounded task ' + 'instruction '.repeat(1000);
  } });
  const initial = await f.service.call('native_next', {}, { model: true, modelThreadId: thread });
  assert.equal(initial.task_delivery, lane);
  const { receipt, bytes, bundle } = await retainedMainBundle(f);
  assert.equal(digest(bytes), receipt.task_bundle_sha256);
  assert.deepEqual(Object.keys(receipt).sort(), ['before_snapshot', 'call_chain_id', 'executor', 'main_actor', 'session_id', 'task_bundle_path', 'task_bundle_sha256', 'thread_id']);
  const metadataBytes = await readFile(bundle.context_preparation.path), metadata = JSON.parse(metadataBytes);
  const input = metadata.inputs.find(item => item.name === 'context'), resource = metadata.resources[0];
  const task = lane === 'inline' ? initial.task_bundle.task : JSON.parse(await readFile(initial.task_bundle_path)).task;
  const inputs = JSON.parse(task.split('\nInputs:\n')[1].split('\n')[0]);
  const resources = JSON.parse(task.split('\nResources:\n')[1].split('\n')[0]);
  if(lane==='inline'){
    assert.deepEqual(inputs.context,{delivery:'inline',value_path:['semantic_inputs','context','content'],format:'text'});
    assert.equal(initial.semantic_inputs.context.content,context);assert(!task.includes(input.path));
  }else{
    assert(inputs.context.includes(canonicalJSON(input.path)));assert.equal(initial.semantic_input_delivery,'file');
    assert.equal(Object.hasOwn(initial,'semantic_inputs'),false);
  }
  assert.deepEqual(resources, [{ path: resource.path, local_path: resource.local_path }]);
  assert.equal(await readFile(input.path, 'utf8'), context); assert.equal(await readFile(resource.local_path, 'utf8'), reference);
  assert.equal(digest(await readFile(input.path)), input.sha256); assert.equal(digest(await readFile(resource.local_path)), resource.sha256);
  if (lane === 'file') await rm(initial.task_bundle_path);
  const reopened = new WorkflowService({ configPath: f.service.configPath, defaultConfigPath: DEFAULT_CONFIG_PATH,
    capabilities: { hostMainManager: f.manager, nativeAgentObserver: null, nativeParentVerifier: async () => ({ agent_path: '/root' }) } });
  t.after(async () => { await reopened.historyMaintenance.settle(); await reopened.historyMaintenance.close(); });
  const again = await reopened.call('native_next', {}, { model: true, modelThreadId: thread });
  assert.deepEqual(again, initial);
  const retained = await retainedMainBundle(f);
  assert.deepEqual(retained.receipt, receipt); assert.deepEqual(retained.bytes, bytes);
  assert.deepEqual(await readFile(bundle.context_preparation.path), metadataBytes);
  assert.equal(await readFile(input.path, 'utf8'), context); assert.equal(await readFile(resource.local_path, 'utf8'), reference);
  await reopened.call('orchestration_complete', { output: { conclusion: 'Retained semantic context accepted' } }, { model: true, modelThreadId: thread });
  assert.equal((await f.runtime.get(f.run_id)).status, 'succeeded'); assert.equal(f.sessions(), 0);
});

for (const target of ['canonical', 'preparation', 'public']) test(`semantic Main projection rejects ${target} tampering at native_next and completion before effects`, async t => {
  const h = hostCheckFixture();
  const f = await fixture(t, { legacyTaskDelivery:true,write: true, hostToolRegistry: h.registry, mutateWorkflow: workflow => {
    h.install(workflow); workflow.nodes.find(node => node.id === 'final').prompt_template = 'Bounded task ' + 'instruction '.repeat(1000);
  } });
  const handoff = await f.service.call('native_next', {}, { model: true, modelThreadId: thread });
  assert.equal(handoff.task_delivery, 'file');
  const { receipt, bundle } = await retainedMainBundle(f);
  const path = target === 'canonical' ? receipt.task_bundle_path : target === 'preparation' ? bundle.context_preparation.path : handoff.task_bundle_path;
  await writeFile(path, Buffer.concat([await readFile(path), Buffer.from(' ')]));
  await assert.rejects(f.service.call('native_next', {}, { model: true, modelThreadId: thread }), { code: 'MAIN_ORCHESTRATION_BUNDLE' });
  await assert.rejects(f.service.call('orchestration_complete', { output: { conclusion: 'Cannot accept tampered material' } },
    { model: true, modelThreadId: thread }), { code: 'MAIN_ORCHESTRATION_BUNDLE' });
  const record = await f.runtime.runs.read(f.run_id), attempt = record.state.nodes.final.attempts[0];
  assert.deepEqual(attempt.dispatch.receipt, receipt); assert.equal(attempt.completion_turns ?? 0, 0);
  assert.equal(record.state.status, 'running'); assert.equal(h.calls.length, 0); assert.equal(f.sessions(), 0);
});

test('new Main dispatch delivers the entire 12–16 KiB semantic task inline and replays the pinned budget',async t=>{
  const complete='Keep every original condition.\n'+'中文🌱'.repeat(1350)+'\nEND_OF_COMPLETE_REFERENCE';
  const f=await fixture(t,{mutateWorkflow:workflow=>{workflow.nodes.find(node=>node.id==='final').prompt_template=complete;}});
  const result=await f.service.call('native_next',{}, {model:true,modelThreadId:thread});
  const bytes=Buffer.from(canonicalJSON(result.task_bundle));
  assert(bytes.length>12000&&bytes.length<=16384);
  assert.equal(result.task_delivery,'inline');assert(result.task_bundle.task.includes(complete));
  assert.equal(Object.hasOwn(result,'task_bundle_path'),false);
  const {receipt}=await retainedMainBundle(f);assert.equal(receipt.task_inline_limit,16384);
  assert.deepEqual(await f.service.call('native_next',{}, {model:true,modelThreadId:thread}),result);
  await f.service.call('orchestration_complete',{output:{conclusion:'The complete original conditions are retained.'}}, {model:true,modelThreadId:thread});
  assert.equal((await f.runtime.get(f.run_id)).status,'succeeded');assert.equal(f.sessions(),0);
});

test('semantic Main projection preserves historical schema1 receipt resource addresses', async t => {
  const f = await fixture(t, { resources: { 'reference.txt': 'Historical declared resource' } });
  const recordDispatch = WorkflowRuntime.prototype.recordHostMainDispatchReceipt;
  t.mock.method(WorkflowRuntime.prototype, 'recordHostMainDispatchReceipt', async function (runId, options) {
    const envelope = await this.execution(runId, options);
    const content = Buffer.from('Historical declared resource');
    const legacy = await materializeNativeTaskBundle({ directory: join(f.runtime.runs.directory(f.run_id), 'historical-fixture'), envelope,
      resources: [{ path: 'reference.txt', bytes: content, size: content.length, sha256: digest(content) }], resultSchema: schema });
    // Freeze an explicit historical schema1 fixture; the current materializer
    // writes schema2 and must not manufacture history implicitly for this test.
    const current=JSON.parse(await readFile(legacy.task_bundle_path));
    const metadata=JSON.parse(await readFile(current.context_preparation.path));
    const historical={schema_version:1,task:current.task,workspace:current.workspace,access:current.access,
      writable_paths:current.writable_paths,result_schema:current.result_schema,
      resources:metadata.resources.map(({delivery,...item})=>item),verified_files:metadata.verified_files.map(({delivery,...item})=>item)};
    const bytes=Buffer.from(canonicalJSON(historical));await writeFile(legacy.task_bundle_path,bytes);legacy.task_bundle_sha256=digest(bytes);
    return recordDispatch.call(this, runId, { ...options, receipt: { ...options.receipt,
      task_bundle_path: legacy.task_bundle_path, task_bundle_sha256: legacy.task_bundle_sha256 } });
  });
  // The first publication returns its caller's original receipt. Reopening must
  // consume the retained historical receipt, with no conversion of its bytes.
  await f.service.call('native_next', {}, { model: true, modelThreadId: thread });
  t.mock.restoreAll();
  const { receipt, bytes, bundle } = await retainedMainBundle(f);
  const handoff = await f.service.call('native_next', {}, { model: true, modelThreadId: thread });
  assert.equal(handoff.task_bundle.schema_version, 1); assert.equal(handoff.task_bundle.task, bundle.task);
  assert.deepEqual(handoff.task_bundle.resources, [{ path: 'reference.txt', local_path: bundle.resources[0].local_path }]);
  assert.equal(await readFile(handoff.task_bundle.resources[0].local_path, 'utf8'), 'Historical declared resource');
  assert.deepEqual((await retainedMainBundle(f)).bytes, bytes);
  assert.deepEqual((await retainedMainBundle(f)).receipt, receipt);
  await f.service.call('orchestration_complete', { output: { conclusion: 'Historical receipt accepted' } }, { model: true, modelThreadId: thread });
  assert.equal((await f.runtime.get(f.run_id)).status, 'succeeded');
});

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

test('current Main handoff reuses one fresh authorized projection and rejects another thread or authority', async t => {
  const f = await fixture(t);
  const initial = await f.service.call('native_next', {}, { model: true, modelThreadId: thread });
  await f.service.historyMaintenance.settle();
  const read = f.runtime.runs.read.bind(f.runtime.runs); let reads = 0;
  f.runtime.runs.read = (...values) => { reads++; return read(...values); };
  const args = { run_id: f.run_id, control_token: f.control_token, thread_id: thread };
  const handoff = await prepareMainOrchestration(f.runtime, args);
  assert.equal(reads, 1, 'Authorization, unique current node selection and envelope share one complete audit');
  assert.deepEqual(handoff.task_bundle, initial.task_bundle);
  await assert.rejects(prepareMainOrchestration(f.runtime, { ...args, control_token: 'wrong' }), { code: 'RUN_AUTHORITY' });
  await assert.rejects(prepareMainOrchestration(f.runtime, { ...args, thread_id: 'another-thread' }), { code: 'MAIN_ORCHESTRATION_CONTEXT' });
  await f.runtime.cancel(f.run_id, { control_token: f.control_token });
  await assert.rejects(prepareMainOrchestration(f.runtime, args), { code: 'MAIN_ORCHESTRATION_CONTEXT' });
});

for(const failure of ['audit','serialization'])test(`real RPC ${failure} failure after first semantic preparation preserves dispatch effects and retained priority`,async t=>{
 const f=await fixture(t);await f.service.historyMaintenance.settle();
 const audit=join(f.service.configPath,'..','control-plane-audit.jsonl');
 if(failure==='audit'){
  const receipt=WorkflowRuntime.prototype.recordHostMainDispatchReceipt;
  t.mock.method(WorkflowRuntime.prototype,'recordHostMainDispatchReceipt',async function(...args){
   const result=await receipt.apply(this,args);await rm(audit,{force:true});await mkdir(audit);return result;
  });
 }else{
  const serialize=JSON.stringify;
  t.mock.method(JSON,'stringify',function(value,...args){
   if(value?.status==='orchestration_handoff')throw Object.assign(new Error('Exact post-preparation serializer failure'),{code:'FIXTURE_SERIALIZER_FAILURE'});
   return serialize(value,...args);
  });
 }
 const request={jsonrpc:'2.0',id:901,method:'tools/call',params:{name:'workflow_native_next',_meta:{threadId:thread},arguments:{}}};
 const options={configPath:f.service.configPath,defaultConfigPath:DEFAULT_CONFIG_PATH,env:{},serviceCapabilities:{hostMainManager:f.manager,
  nativeAgentObserver:null,nativeParentVerifier:async()=>({agent_path:'/root'})}};
 if(failure==='audit')await assert.rejects(handleRpc(request,options));
 else{const failed=await handleRpc(request,options);assert.equal(failed.result.isError,true);assert.match(JSON.stringify(failed),/FIXTURE_SERIALIZER_FAILURE/);}
 t.mock.restoreAll();
 assert.equal(inForegroundActivity(f.runtime.runs.root),false);assert.equal(foregroundActivityCount(f.runtime.runs.root),1);
 const before=await f.runtime.runs.read(f.run_id),attempt=before.state.nodes.final.attempts[0];
 assert.equal(attempt.dispatch.receipt.executor,'codex-current-main-orchestration');assert.equal(f.sessions(),0);
 if(failure==='audit')await rm(audit,{recursive:true});
 const reconciled=await handleRpc({...request,id:902},options);assert.equal(reconciled.result.isError,undefined);
 const after=await f.runtime.runs.read(f.run_id);assert.equal(after.state.nodes.final.attempts.length,1);
 assert.deepEqual(after.state.nodes.final.attempts[0].dispatch,attempt.dispatch);
 const completed=await handleRpc({jsonrpc:'2.0',id:903,method:'tools/call',params:{name:'workflow_orchestration_complete',_meta:{threadId:thread},
  arguments:{output:{conclusion:'Accepted exact original handoff'}}}},options);
 assert.equal(completed.result.isError,undefined);assert.equal((await f.runtime.get(f.run_id)).status,'succeeded');
 assert.equal(foregroundActivityCount(f.runtime.runs.root),0);
});

for (const change of ['claim', 'inactive']) test(`current Main rechecks its exact current selection after environment preparation changes ${change}`, async t => {
  const f = await fixture(t, { runtimeEnv: { PATH: process.env.PATH }, mutateWorkflow: workflow => {
    workflow.nodes.find(node => node.id === 'final').runtime_requirements = { executables: ['node'] };
  } });
  await f.service.call('native_next', {}, { model: true, modelThreadId: thread });
  f.runtime.environmentVerifier = async () => {
    const id = f.run_id, current = await f.runtime.runs.read(id);
    const nodeId = 'final', node = current.state.nodes[nodeId], binding = { node_id: nodeId, attempt_id: node.active_attempt_id };
    await f.runtime.runs.mutate(id, 'runtime_environment_rebound', state => {
      const activeNode = state.nodes[binding.node_id], attempt = activeNode.attempts.find(item => item.id === binding.attempt_id);
      if (change === 'inactive') { activeNode.status = 'ready'; return; }
      const next = { ...structuredClone(attempt), id: 'replacement-claim', lease_generation: 0 };
      next.lease_hash = digest(leaseToken(f.control_token, id, binding.node_id, next.id));
      attempt.status = 'cancelled'; activeNode.attempts.push(next); activeNode.active_attempt_id = next.id;
    });
  };
  await assert.rejects(prepareMainOrchestration(f.runtime, { run_id: f.run_id, control_token: f.control_token, thread_id: thread }), {
    code: change === 'claim' ? 'STALE_LEASE' : 'MAIN_ORCHESTRATION_NODE',
  });
});

test('automatic completion check writes required artifacts through the exact pinned Host runner without model invocation', async t => {
  const h = hostCheckFixture();
  const f = await fixture(t, {write:true,hostToolRegistry:h.registry,mutateWorkflow:h.install,resources:{'check.txt':'pinned check evidence'}});
  const handoff = await f.service.call('native_next', {}, {model:true,modelThreadId:thread});
  assert.equal(Object.hasOwn(handoff,'host_check'),false,'Automatic checker mechanics stay private to the Host');
  assert.equal(handoff.instruction.includes('mechanical completion check'),false);
  const bundle = handoff.task_bundle;
  assert.equal(bundle.task.includes('"host_check"'),false,'Mechanical tool metadata stays outside the semantic task');
  const output = {conclusion:'The accepted semantic decision'};
  const completed = await f.service.call('orchestration_complete',{output},{model:true,modelThreadId:thread});
  assert.equal(completed.status,'succeeded'); assert.equal(f.sessions(),0); assert.equal(h.calls.length,1);
  assert.deepEqual(h.calls[0].input,{inputs:{task:'Use our prior conclusions'},output});
  assert.equal(h.calls[0].context.resources[0].bytes.toString(),'pinned check evidence');
  assert.equal(digest(h.calls[0].context.resources[0].bytes),h.calls[0].context.resources[0].sha256);
  assert.equal(h.calls[0].context.runtime_environment.status,'ready');
  assert.equal(await readFile(join(f.workspace,'result.txt'),'utf8'),output.conclusion);
  const record = await f.runtime.runs.read(f.run_id), host = record.state.nodes.final.attempts[0].host_tool;
  assert.equal(host.input_sha256,digest(canonicalJSON(h.calls[0].input)));
  assert.equal(host.receipt.status,'succeeded'); assert(host.receipt.output_ref);
  assert.deepEqual(record.state.nodes.final.output,output);
});

test('resource-program completion selects its own pinned scripts while Main sees only semantic references',async t=>{
  const h=hostCheckFixture();h.tool.identity.name='workflow-resource-program';
  h.tool.permissions.write_paths.push('work');
  h.tool.argv=['node','scripts/check.mjs','work','@INPUT@','@RESOURCE:scripts/helper.mjs@'];
  const resources={'scripts/check.mjs':'mechanical check','scripts/helper.mjs':'mechanical helper','reference.md':'semantic reference'};
  const f=await fixture(t,{write:true,resources,runtimeEnv:{PATH:process.env.PATH},allowedPaths:['result.txt','work'],hostToolRegistry:h.registry,mutateWorkflow:w=>{
    h.install(w);w.requirements.executables=[{name:'node',version:'>=20'}];w.nodes.find(n=>n.id==='final').resources=['reference.md'];
  }});
  const handoff=await f.service.call('native_next',{},{model:true,modelThreadId:thread});
  const task=handoff.task_bundle.task;
  assert(task.includes('semantic reference'));assert(!task.includes('mechanical check'));assert(!task.includes('scripts/check.mjs'));assert(!task.includes('scripts/helper.mjs'));
  await f.service.call('orchestration_complete',{output:{conclusion:'Accepted'}},{model:true,modelThreadId:thread});
  assert.deepEqual(h.calls[0].context.resources.map(r=>r.path),['scripts/check.mjs','scripts/helper.mjs']);
  assert.equal(await readFile(join(f.workspace,'result.txt'),'utf8'),'Accepted');
});

test('completion-only bindings reach the exact Host checker without entering current Main context',async t=>{
  const ledger={record:'PRIVATE_MECHANICAL_RECORD'.repeat(900),execution:{counter:12,source_sha256:'a'.repeat(64)}};
  const h=hostCheckFixture();
  const f=await fixture(t,{write:true,hostToolRegistry:h.registry,extraInputs:{machine_record:ledger},mutateWorkflow:w=>{
    h.install(w);w.inputs_schema.properties.machine_record={type:'object'};w.inputs_schema.required.push('machine_record');
    w.nodes.find(n=>n.id==='final').completion_contract.host_check.input_bindings={task:'/inputs/task',ledger:'/inputs/machine_record'};
  }});
  const handoff=await f.service.call('native_next',{},{model:true,modelThreadId:thread});
  const task=handoff.task_bundle.task;
  assert(!task.includes('PRIVATE_MECHANICAL_RECORD'));assert(!task.includes('machine_record'));
  assert.equal(Object.hasOwn(handoff,'host_check'),false);
  assert(task.includes('Use our prior conclusions'));
  const output={conclusion:'Accepted using semantic inputs'};
  const completed=await f.service.call('orchestration_complete',{output},{model:true,modelThreadId:thread});
  assert.equal(completed.status,'succeeded');assert.equal(f.sessions(),0);
  assert.deepEqual(h.calls[0].input,{inputs:{task:'Use our prior conclusions',ledger},output});
  const record=await f.runtime.runs.read(f.run_id);
  assert.equal(record.state.nodes.final.attempts[0].host_tool.input_sha256,digest(canonicalJSON(h.calls[0].input)));
});

test('Host-only completion bindings reject non-upstream and malformed inputs before a Run starts',async t=>{
  for(const [binding,code] of [['/nodes/final/output','BINDING_SOURCE'], ['/nodes/absent/output','BINDING_SOURCE'], [{path:'/inputs/task',unknown:true},'BINDING_SCHEMA']]){
    const h=hostCheckFixture();
    await assert.rejects(fixture(t,{write:true,hostToolRegistry:h.registry,mutateWorkflow:w=>{
      h.install(w);w.nodes.find(n=>n.id==='final').completion_contract.host_check.input_bindings={original:binding};
    }}),error=>error.validation?.errors?.some(item=>item.code===code));
    assert.equal(h.calls.length,0);
  }
});

test('missing completion-only input fails before model handoff and does not spend a semantic turn',async t=>{
  const h=hostCheckFixture(),f=await fixture(t,{write:true,hostToolRegistry:h.registry,mutateWorkflow:w=>{
    h.install(w);w.inputs_schema.properties.optional_record={type:'object'};
    w.nodes.find(n=>n.id==='final').completion_contract.host_check.input_bindings={ledger:'/inputs/optional_record'};
  }});
  await assert.rejects(f.service.call('native_next',{},{model:true,modelThreadId:thread}),{code:'BINDING_MISSING'});
  const record=await f.runtime.runs.read(f.run_id);
  assert.equal(record.state.nodes.final.attempts[0].completion_turns??0,0);
  assert.equal(h.calls.length,0);assert.equal(f.sessions(),0);
});

test('a model-visible projection cannot replace or alter Host-only completion input identity',async t=>{
  const ledger={counter:12},h=hostCheckFixture(),f=await fixture(t,{write:true,hostToolRegistry:h.registry,extraInputs:{machine_record:ledger},mutateWorkflow:w=>{
    h.install(w);w.inputs_schema.properties.machine_record={type:'object'};
    w.nodes.find(n=>n.id==='final').completion_contract.host_check.input_bindings={task:'/inputs/task',ledger:'/inputs/machine_record'};
  }});
  await f.service.call('native_next',{},{model:true,modelThreadId:thread});
  const record=await f.runtime.runs.read(f.run_id),attempt=record.state.nodes.final.attempts[0];
  const binding={node_id:'final',attempt_id:attempt.id,control_token:f.control_token,
    lease_token:leaseToken(f.control_token,f.run_id,'final',attempt.id,attempt.lease_generation??0),contract:h.tool};
  for(const inputs of [{task:'Use our prior conclusions'},{task:'Use our prior conclusions',ledger:{counter:13}},
    {task:'Use our prior conclusions',ledger,extra:'unbound'}])
    await assert.rejects(f.runtime.recordHostToolIntent(f.run_id,{...binding,input:{inputs,output:{conclusion:'Accepted'}}}),{code:'HOST_TOOL_CONFLICT'});
  assert.equal((await f.runtime.runs.read(f.run_id)).state.nodes.final.attempts[0].host_tool,undefined);
  assert.equal(h.calls.length,0);
  assert.equal((await f.service.call('orchestration_complete',{output:{conclusion:'Accepted'}},{model:true,modelThreadId:thread})).status,'succeeded');
  assert.deepEqual(h.calls[0].input.inputs,{task:'Use our prior conclusions',ledger});
});

test('Ready completion check cannot omit a mechanically declared resource pin',async t=>{
  const h=hostCheckFixture();h.tool.identity.name='workflow-resource-program';
  h.tool.permissions.write_paths.push('work');
  h.tool.argv=['node','scripts/check.mjs','work','@RESOURCE:scripts/missing.mjs@'];
  await assert.rejects(fixture(t,{write:true,resources:{'scripts/check.mjs':'check'},allowedPaths:['result.txt','work'],hostToolRegistry:h.registry,
    mutateWorkflow:w=>{h.install(w);w.requirements.executables=[{name:'node',version:'>=20'}];w.nodes.find(n=>n.id==='final').resources=[];}}),{code:'WORKFLOW_RESOURCE_MISSING'});
});

test('Host-only completion bytes remain checked even when absent from Main reading materials',async t=>{
  const h=hostCheckFixture();h.tool.identity.name='workflow-resource-program';
  h.tool.permissions.write_paths.push('work');h.tool.argv=['node','scripts/check.mjs','work','@INPUT@'];
  const f=await fixture(t,{write:true,resources:{'scripts/check.mjs':'exact check'},runtimeEnv:{PATH:process.env.PATH},
    allowedPaths:['result.txt','work'],hostToolRegistry:h.registry,mutateWorkflow:w=>{
      h.install(w);w.requirements.executables=[{name:'node',version:'>=20'}];w.nodes.find(n=>n.id==='final').resources=[];
    }});
  await f.service.call('native_next',{},{model:true,modelThreadId:thread});
  const record=await f.runtime.runs.read(f.run_id),pin=record.pins.root.resources.find(r=>r.path==='scripts/check.mjs');
  await writeFile(join(f.runtime.runs.directory(f.run_id),'objects',pin.sha256),'changed check');
  await assert.rejects(f.service.call('orchestration_complete',{output:{conclusion:'Accepted'}},{model:true,modelThreadId:thread}),
    {code:'RUN_RESOURCE_CORRUPT'});
  assert.equal(h.calls.length,0);
});

test('the final runtime acceptance transaction cannot bypass the required exact Host check receipt',async t=>{
  const h=hostCheckFixture(),f=await fixture(t,{write:true,hostToolRegistry:h.registry,mutateWorkflow:h.install});
  await f.service.call('native_next',{}, {model:true,modelThreadId:thread});
  const record=await f.runtime.runs.read(f.run_id),definition=record.pins.root.workflow.nodes.find(item=>item.id==='final');
  const attempt=record.state.nodes.final.attempts[0],binding={run_id:f.run_id,node_id:'final',attempt_id:attempt.id,control_token:f.control_token,
    lease_token:leaseToken(f.control_token,f.run_id,'final',attempt.id,attempt.lease_generation??0)};
  await writeFile(join(f.workspace,'result.txt'),'unverified product');
  const proposal=hostResultProposalEnvelope(definition,{output:{conclusion:'unverified semantic decision'},changed_paths:['result.txt']});
  const stored=await f.runtime.runs.saveExecutorResult(f.run_id,attempt.id,proposal);
  await f.runtime.recordExecutorEvent(f.run_id,{...binding,event:{kind:'result_proposed',metadata:{...stored,final_acceptance_required:false}}});
  await assert.rejects(f.runtime.completeHostMainResult(f.run_id,binding,{accepted:true}),{code:'HOST_TOOL_RECEIPT_REQUIRED'});
  assert.equal(h.calls.length,0);assert.equal((await f.runtime.runs.read(f.run_id)).state.status,'running');
});

test('successful Host completion receipt reconciles an uncertain semantic commit without re-execution and rejects changed output', async t => {
  const h = hostCheckFixture(), f = await fixture(t,{write:true,hostToolRegistry:h.registry,mutateWorkflow:h.install});
  await f.service.call('native_next',{}, {model:true,modelThreadId:thread});
  const {executor}=await f.service.open();
  const complete = f.runtime.completeHostMainResult.bind(f.runtime);
  f.runtime.completeHostMainResult = async () => { throw Object.assign(new Error('uncertain semantic commit'),{code:'FIXTURE_COMMIT_UNCERTAIN'}); };
  const args = {run_id:f.run_id,control_token:f.control_token,thread_id:thread,output:{conclusion:'original semantic result'}};
  const completeCurrent = request => completeMainOrchestration(f.runtime,request,{executor});
  await assert.rejects(completeCurrent(args),{code:'FIXTURE_COMMIT_UNCERTAIN'});
  f.runtime.completeHostMainResult = complete;
  await assert.rejects(completeCurrent({...args,output:{conclusion:'changed semantic result'}}),{code:'HOST_TOOL_CONFLICT'});
  const completed = await completeCurrent(args);
  assert.equal(completed.status,'succeeded'); assert.equal(h.calls.length,1); assert.equal(f.sessions(),0);
  assert.equal((await f.runtime.runs.read(f.run_id)).state.nodes.final.attempts[0].completion_turns,1);
});

test('a completion check uncertain intent is never automatically replayed even when its tool declares safe idempotency', async t => {
  const h = hostCheckFixture({execute:async()=>{throw new Error('lost broker response');}});
  const f = await fixture(t,{write:true,hostToolRegistry:h.registry,mutateWorkflow:h.install,expectedDrainFailure:'uncertain'});
  await f.service.call('native_next',{}, {model:true,modelThreadId:thread});
  const args = {output:{conclusion:'semantic decision'}},options={model:true,modelThreadId:thread};
  await assert.rejects(f.service.call('orchestration_complete',args,options),/lost broker response/);
  await assert.rejects(f.service.call('orchestration_complete',args,options),{code:'ATTEMPT_DUPLICATE'});
  const owner=[...f.service.attemptAdmission.entries.values()];
  assert.equal(owner.length,1);assert.equal(owner[0].run_id,f.run_id);assert.equal(owner[0].receipt_recorded,false);
  const freshAdmission=new AttemptAdmissionRegistry();
  const freshExecutor=new WorkflowExecutor({runtime:f.runtime,attemptAdmission:freshAdmission,hostToolRunner:new HostToolRunner({registry:h.registry})});
  await assert.rejects(completeMainOrchestration(f.runtime,{run_id:f.run_id,control_token:f.control_token,thread_id:thread,...args},{executor:freshExecutor}),{code:'HOST_TOOL_RECONCILIATION_REQUIRED'});
  assert.equal(freshAdmission.entries.size,0,'Missing-owner reconciliation starts no effect and retains no new owner');
  assert.equal(f.sessions(),0);
  assert.equal(h.calls.length,1);
  const record=await f.runtime.runs.read(f.run_id);
  assert.equal(record.state.nodes.final.attempts[0].host_tool.phase,'intent');
});

for (const [name,options,code] of [
  ['false success field',{verified:false},'MAIN_ORCHESTRATION_HOST_CHECK_FALSE'],
  ['failed exit',{exit:7},'HOST_TOOL_FAILED'],
  ['out-of-scope broker effects',{changed:'unexpected.txt'},'HOST_TOOL_SCOPE'],
]) test(`automatic completion fails visibly on ${name}`,async t=>{
  const h=hostCheckFixture(options),f=await fixture(t,{write:true,hostToolRegistry:h.registry,mutateWorkflow:h.install,expectedDrainFailure:code==='HOST_TOOL_SCOPE'?'scope':false});
  await f.service.call('native_next',{}, {model:true,modelThreadId:thread});
  await assert.rejects(f.service.call('orchestration_complete',{output:{conclusion:'semantic decision'}},{model:true,modelThreadId:thread}),{code});
  const record=await f.runtime.runs.read(f.run_id);assert.equal(record.state.status,'failed');assert.equal(h.calls.length,1);assert.equal(f.sessions(),0);
});

test('semantic acceptance, current conversation and preexisting scope violations gate Host mechanical effects',async t=>{
  const h=hostCheckFixture(), f=await fixture(t,{write:true,hostToolRegistry:h.registry,mutateWorkflow:workflow=>{
    h.install(workflow);const node=workflow.nodes.find(item=>item.id==='final');
    node.outputs_schema={type:'object',properties:{conclusion:{type:'string'},accepted:{type:'boolean'}},required:['conclusion','accepted'],additionalProperties:false};
    h.tool.input_schema.properties.output=node.outputs_schema;
    node.completion_contract.fail_on_false=['accepted'];
  }});
  await f.service.call('native_next',{}, {model:true,modelThreadId:thread});
  await assert.rejects(f.service.call('orchestration_complete',{output:{conclusion:'wrong context',accepted:true}},{model:true,modelThreadId:'22345678-1234-4234-8234-123456789abc'}),{code:'MODEL_RUN_AUTHORITY'});
  await writeFile(join(f.workspace,'unexpected.txt'),'outside grant');
  await assert.rejects(f.service.call('orchestration_complete',{output:{conclusion:'accepted',accepted:true}},{model:true,modelThreadId:thread}),{code:'MAIN_ORCHESTRATION_SCOPE_VIOLATION'});
  assert.equal(h.calls.length,0);
});

for(const field of ['accepted','verified'])test(`explicit Main ${field}=false fails durably without executing the success checker`,async t=>{
  const h=hostCheckFixture(),f=await fixture(t,{write:true,hostToolRegistry:h.registry,mutateWorkflow:workflow=>{
    h.install(workflow);const node=workflow.nodes.find(item=>item.id==='final');
    node.outputs_schema={type:'object',properties:{conclusion:{type:'string'},[field]:{type:'boolean'}},required:['conclusion',field],additionalProperties:false};
    h.tool.input_schema.properties.output=node.outputs_schema;
    node.completion_contract.fail_on_false=[field];
  }});
  await f.service.call('native_next',{}, {model:true,modelThreadId:thread});
  const output={conclusion:'Reject this delivery because the declared result is incomplete',[field]:false};
  const code=field==='accepted'?'FINAL_ACCEPTANCE_REQUIRED':'NODE_SUCCESS_REQUIRED';
  await assert.rejects(f.service.call('orchestration_complete',{output},{model:true,modelThreadId:thread}),{code});
  const record=await f.runtime.runs.read(f.run_id),attempt=record.state.nodes.final.attempts[0];
  assert.equal(record.state.status,'failed');assert.equal(record.state.nodes.final.status,'failed');
  assert.equal(h.calls.length,0);assert.equal(f.sessions(),0);
  const rejected=attempt.executor_events.find(e=>e.kind==='completion_invalid'&&e.metadata.rejection_artifact);
  assert(rejected,'Negative semantic output must have durable evidence');
  assert.deepEqual(JSON.parse((await f.runtime.runs.readArtifact(f.run_id,{artifact:rejected.metadata.rejection_artifact,sha256:rejected.metadata.rejection_sha256,bytes:rejected.metadata.rejection_bytes})).toString()),output);
  assert(!attempt.host_tool,'No success receipt may be invented for a semantic rejection');
});

test('required artifacts are checked after a successful mechanical receipt and later artifact creation cannot reuse its stale verdict',async t=>{
  const h=hostCheckFixture({write:false}),f=await fixture(t,{write:true,hostToolRegistry:h.registry,mutateWorkflow:h.install});
  await f.service.call('native_next',{}, {model:true,modelThreadId:thread});
  const args={output:{conclusion:'accepted'}},options={model:true,modelThreadId:thread};
  await assert.rejects(f.service.call('orchestration_complete',args,options),{code:'REQUIRED_ARTIFACT_MISSING'});
  await writeFile(join(f.workspace,'result.txt'),'repaired required output');
  await assert.rejects(f.service.call('orchestration_complete',args,options),{code:'MAIN_ORCHESTRATION_HOST_CHECK_STALE'});
  assert.equal(h.calls.length,1);
});

test('an unchanged semantic retry cannot reuse a successful check after an in-scope existing product changes',async t=>{
  const h=hostCheckFixture(),f=await fixture(t,{write:true,hostToolRegistry:h.registry,mutateWorkflow:h.install,allowedPaths:['result.txt','product.txt']});
  await writeFile(join(f.workspace,'product.txt'),'checked product bytes');
  await f.service.call('native_next',{}, {model:true,modelThreadId:thread});
  const {executor}=await f.service.open(),complete=f.runtime.completeHostMainResult.bind(f.runtime);
  f.runtime.completeHostMainResult=async()=>{throw Object.assign(new Error('uncertain semantic commit'),{code:'FIXTURE_COMMIT_UNCERTAIN'});};
  const args={run_id:f.run_id,control_token:f.control_token,thread_id:thread,output:{conclusion:'original result'}};
  await assert.rejects(completeMainOrchestration(f.runtime,args,{executor}),{code:'FIXTURE_COMMIT_UNCERTAIN'});
  f.runtime.completeHostMainResult=complete;
  const record=await f.runtime.runs.read(f.run_id),attempt=record.state.nodes.final.attempts[0];
  const stored=await f.runtime.runs.readExecutorResult(f.run_id,attempt.id,attempt.host_tool.receipt.output_ref.sha256);
  assert(stored.completion_snapshot);
  const snapshot=JSON.parse((await f.runtime.runs.readArtifact(f.run_id,stored.completion_snapshot)).toString('utf8'));
  assert(snapshot.entries.some(item=>item.path==='product.txt'&&item.sha256===digest('checked product bytes')));
  await writeFile(join(f.workspace,'product.txt'),'changed scoped product');
  await assert.rejects(completeMainOrchestration(f.runtime,args,{executor}),{code:'MAIN_ORCHESTRATION_HOST_CHECK_STALE'});
  assert.equal(h.calls.length,1);assert.equal((await f.runtime.runs.read(f.run_id)).state.status,'running');
});

test('the acceptance transaction rejects altered workspace content even after a new exact Main proposal is persisted',async t=>{
  const h=hostCheckFixture(),f=await fixture(t,{write:true,hostToolRegistry:h.registry,mutateWorkflow:h.install,allowedPaths:['result.txt','product.txt']});
  await writeFile(join(f.workspace,'product.txt'),'checked product');
  await f.service.call('native_next',{}, {model:true,modelThreadId:thread});
  const {executor}=await f.service.open(),complete=f.runtime.completeHostMainResult.bind(f.runtime);
  f.runtime.completeHostMainResult=async()=>{throw Object.assign(new Error('uncertain semantic commit'),{code:'FIXTURE_COMMIT_UNCERTAIN'});};
  await assert.rejects(completeMainOrchestration(f.runtime,{run_id:f.run_id,control_token:f.control_token,thread_id:thread,output:{conclusion:'original result'}},{executor}),{code:'FIXTURE_COMMIT_UNCERTAIN'});
  f.runtime.completeHostMainResult=complete;
  await writeFile(join(f.workspace,'product.txt'),'new unchecked product');
  const record=await f.runtime.runs.read(f.run_id),attempt=record.state.nodes.final.attempts[0];
  const proposal=await f.runtime.runs.readExecutorResult(f.run_id,attempt.id,attempt.result_proposal.sha256);
  proposal.summary='Updated delivery';proposal.changed_paths.push('product.txt');proposal.artifacts.push('product.txt');
  const saved=await f.runtime.runs.saveExecutorResult(f.run_id,attempt.id,proposal),binding={run_id:f.run_id,node_id:'final',attempt_id:attempt.id,control_token:f.control_token,
    lease_token:leaseToken(f.control_token,f.run_id,'final',attempt.id,attempt.lease_generation??0)};
  await assert.rejects(f.runtime.recordExecutorEvent(f.run_id,{...binding,event:{kind:'result_proposed',metadata:{...saved,final_acceptance_required:false}}}),{code:'EXECUTOR_RESULT_CONFLICT'});
  // Fault injection bypasses proposal immutability so the acceptance boundary
  // must independently protect workspace freshness even with a replaced pin.
  await f.runtime.runs.mutate(f.run_id,'executor_event',state=>{
    state.nodes.final.attempts[0].result_proposal={...state.nodes.final.attempts[0].result_proposal,...saved};
  });
  await assert.rejects(f.runtime.completeHostMainResult(f.run_id,binding,{accepted:true}),{code:'MAIN_ORCHESTRATION_HOST_CHECK_STALE'});
  assert.equal(h.calls.length,1);assert.equal((await f.runtime.runs.read(f.run_id)).state.status,'running');
});

test('Host completion deadlines retain a qualified termination receipt and cannot accept semantic output',async t=>{
  const h=hostCheckFixture({deadline:25,execute:async()=>new Promise(()=>{})});
  const f=await fixture(t,{write:true,hostToolRegistry:h.registry,mutateWorkflow:h.install});
  await f.service.call('native_next',{}, {model:true,modelThreadId:thread});
  await assert.rejects(f.service.call('orchestration_complete',{output:{conclusion:'accepted'}},{model:true,modelThreadId:thread}),{code:'HOST_TOOL_TIMEOUT'});
  const record=await f.runtime.runs.read(f.run_id),receipt=record.state.nodes.final.attempts[0].host_tool.receipt;
  assert.equal(receipt.status,'timed_out');assert.equal(receipt.reconciliation.termination_confirmed,true);
  assert.equal(record.state.status,'failed');assert.equal(h.calls.length,1);
});

test('cancelling the Run revokes the shared Host completion owner and stores its termination receipt without acceptance',async t=>{
  let entered;
  const started=new Promise(resolve=>{entered=resolve;});
  const h=hostCheckFixture({execute:async()=>{entered();return new Promise(()=>{});}});
  const f=await fixture(t,{write:true,hostToolRegistry:h.registry,mutateWorkflow:h.install});
  await f.service.call('native_next',{}, {model:true,modelThreadId:thread});
  const completion=f.service.call('orchestration_complete',{output:{conclusion:'accepted'}},{model:true,modelThreadId:thread});
  const outcome=completion.then(result=>({result}),error=>({error}));
  await started;
  await f.service.call('cancel',{run_id:f.run_id,control_token:f.control_token},{human:true});
  assert.equal((await outcome).error.code,'HOST_TOOL_CANCELLED');
  const record=await f.runtime.runs.read(f.run_id),receipt=record.state.nodes.final.attempts[0].host_tool.receipt;
  assert.equal(record.state.status,'cancelled');assert.equal(receipt.status,'cancelled');
  assert.equal(receipt.reconciliation.termination_confirmed,true);assert.equal(h.calls.length,1);
});

test('Host check contract validation rejects invalid executors, tools, result fields, input schemas and static scopes',()=>{
  const h=hostCheckFixture();
  const cases=[
    [node=>{node.executor.mode='worker';},'MAIN_WORKER_HOST_CHECK_CORRECTION'],
    [node=>{node.access='read_only';delete node.path_scope;},'MAIN_ORCHESTRATION_HOST_CHECK_MODE'],
    [node=>{node.completion_contract.host_check.tool='unknown';},'MAIN_ORCHESTRATION_HOST_CHECK_TOOL'],
    [node=>{node.completion_contract.host_check.success_field='missing';},'MAIN_ORCHESTRATION_HOST_CHECK_SUCCESS'],
    [(_node,tool)=>{tool.output_schema.required=[];},'MAIN_ORCHESTRATION_HOST_CHECK_SUCCESS'],
    [(_node,tool)=>{tool.input_schema.properties.output={type:'string'};},'MAIN_ORCHESTRATION_HOST_CHECK_SCHEMA'],
    [(_node,tool)=>{tool.input_schema.properties.inputs={type:'object',properties:{task:{type:'integer'}},required:['task']};},'MAIN_ORCHESTRATION_HOST_CHECK_SCHEMA'],
    [node=>{node.path_scope=['elsewhere'];},'HOST_TOOL_PERMISSION'],
  ];
  for(const [mutate,code] of cases){
    const workflow=readyWorkflow();workflow.skill_policy.mode='cooperative';workflow.host_tools=[structuredClone(h.tool)];
    workflow.inputs_schema={type:'object',properties:{task:{type:'string'}},required:['task']};
    const node=workflow.nodes.find(item=>item.id==='final');Object.assign(node,{executor:{kind:'main',mode:'orchestration'},access:'bounded_write',path_scope:['result.txt'],outputs_schema:schema,input_bindings:{task:'/inputs/task'}});
    node.completion_contract={on_missing:'block',outcome:'decision',host_check:{tool:h.tool.id,success_field:'verified'}};
    mutate(node,workflow.host_tools[0]);
    assert(validateWorkflowGraph(workflow,{host_tools:[h.tool.id]}).errors.some(error=>error.code===code),code);
  }
  assert(schemaAcceptedBy(schema,{}));assert(!schemaAcceptedBy({},schema));
});

test('dynamic Run grants are validated before Main work and stale registered tool identities cannot invoke a check',async t=>{
  const h=hostCheckFixture(),f=await fixture(t,{write:true,hostToolRegistry:h.registry,mutateWorkflow:workflow=>{
    h.install(workflow);const final=workflow.nodes.find(item=>item.id==='final');final.path_scope={binding:'run.allowed_paths'};final.required_artifacts=[];
  }});
  const count=(await f.service.call('runs')).length;
  await assert.rejects(f.service.call('begin_main',{...f.options,allowed_paths:['elsewhere']}),{code:'HOST_TOOL_PERMISSION'});
  assert.equal((await f.service.call('runs')).length,count);assert.equal(h.calls.length,0);
  await f.service.call('native_next',{}, {model:true,modelThreadId:thread});
  h.broker.identity={...h.broker.identity,sha256:digest('changed implementation')};
  await assert.rejects(f.service.call('orchestration_complete',{output:{conclusion:'accepted'}},{model:true,modelThreadId:thread}),{code:'HOST_TOOL_UNAVAILABLE'});
  assert.equal(h.calls.length,0);assert.equal(f.sessions(),0);
});

test('orchestration receives a compact Host bundle and completes in the bound conversation without a session',async t=>{
  const f=await fixture(t,{resources:{'reference.txt':'The approved technical conclusion'},runtimeEnv:{WORKFLOW_MCP_TRANSPORT:'direct_mcp'}});
  assert.equal(f.handoff.stop_reason,'main_orchestration');
  const result=await f.service.call('native_next',{}, {model:true,modelThreadId:thread});
  assert.equal(result.status,'orchestration_handoff');assert.equal(result.context,'current_conversation');
  assert.equal(result.invocation_adapter?.kind,'direct_mcp');
  assert.equal(result.invocation_adapter.tool_name,'workflow_orchestration_complete');
  assert.equal(result.invocation_adapter.slot,'output');
  assert.equal(result.invocation_adapter.tool,'mcp__caw_execution__workflow_orchestration_complete');
  assert.deepEqual(result.invocation_adapter.arguments,{});
  assert.equal(Object.hasOwn(result.invocation_adapter,'code_prefix'),false);
  assert.equal(result.invocation_adapter.scope,'direct_mcp_only');
  for(const key of ['run_id','node_id','attempt_id','control_token','lease_token','host_binding'])assert(!Object.hasOwn(result,key));
  const {bundle}=await retainedMainBundle(f);
  assert.equal(result.task_delivery,'inline');assert.deepEqual(result.task_bundle,{schema_version:2,task:bundle.task});
  assert(result.instruction.includes('do not reread'));
  const prepared=JSON.parse(await readFile(bundle.context_preparation.path,'utf8'));
  assert.equal(prepared.resources.length,1);
  assert.equal(await readFile(prepared.resources[0].local_path,'utf8'),'The approved technical conclusion');
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

test('Main orchestration includes small declared bound values once without an extra sidecar read',async t=>{
  const context={decision:'Use the independently verified artifact',warnings:[]};
  const f=await fixture(t,{extraInputs:{context},mutateWorkflow:workflow=>{
    workflow.inputs_schema.properties.context={type:'object'};
    workflow.nodes.find(n=>n.id==='final').input_bindings.context='/inputs/context';
  }});
  const result=await f.service.call('native_next',{}, {model:true,modelThreadId:thread});
  assert.equal(result.task_delivery,'inline');
  assert(result.task_bundle.task.includes(JSON.stringify(context)));
  assert(!result.task_bundle.task.includes('Read this bound input'));
  const {bundle}=await retainedMainBundle(f);
  const prepared=JSON.parse(await readFile(bundle.context_preparation.path,'utf8'));
  assert.equal(prepared.audit.inline_input_count,2);
  assert.equal(prepared.audit.file_input_count,0);
  assert.equal(f.sessions(),0);
});

test('Main orchestration keeps oversized declared input values in verified bounded sidecars',async t=>{
  const context='DECLARED_LARGE_VALUE_'.repeat(1000);
  const f=await fixture(t,{extraInputs:{context},mutateWorkflow:workflow=>{
    workflow.inputs_schema.properties.context={type:'string'};
    workflow.nodes.find(n=>n.id==='final').input_bindings.context='/inputs/context';
  }});
  const result=await f.service.call('native_next',{}, {model:true,modelThreadId:thread});
  assert.equal(result.task_delivery,'inline');
  assert(!result.task_bundle.task.includes('DECLARED_LARGE_VALUE_'));
  const semantic=result.semantic_inputs.context;
  assert.equal(semantic.content,context);
  const bindings=JSON.parse(result.task_bundle.task.split('\nInputs:\n')[1].split('\n')[0]);
  const binding=bindings.context;
  assert.deepEqual(binding,{delivery:'inline',value_path:['semantic_inputs','context','content'],format:'text'});
  assert.equal(JSON.stringify(result).split(context).length-1,1,'The verified input reaches Main once');
  const {bundle}=await retainedMainBundle(f);
  const manifest=JSON.parse(await readFile(bundle.context_preparation.path,'utf8'));
  assert.equal(manifest.audit.file_input_count,1);
  assert.equal(digest(await readFile(bundle.context_preparation.path)),bundle.context_preparation.sha256);
  assert.equal(await readFile(manifest.inputs.find(i=>i.name==='context').path,'utf8'),context);
});

test('Main handoff delivers each declared reference once and keeps diagnostics out of model context',async t=>{
  const text='NEUTRAL_BEHAVIOR_'.repeat(390),context='NEUTRAL_CONTEXT_'.repeat(220);
  const f=await fixture(t,{resources:{'reference.txt':text},extraInputs:{context},mutateWorkflow:workflow=>{
    workflow.inputs_schema.properties.context={type:'string'};
    workflow.nodes.find(n=>n.id==='final').input_bindings.context='/inputs/context';
  }});
  const result=await f.service.call('native_next',{}, {model:true,modelThreadId:thread});
  assert.equal(result.task_delivery,'inline');
  assert.equal(result.task_bundle.schema_version,2);
  assert.deepEqual(Object.keys(result.task_bundle).sort(),['schema_version','task']);
  assert.equal(Object.hasOwn(result,'task_bundle_path'),false);
  assert.equal(JSON.stringify(result).split(text).length-1,1);
  assert.equal(JSON.stringify(result).split(context).length-1,1);
  const {bundle}=await retainedMainBundle(f);
  const manifest=JSON.parse(await readFile(bundle.context_preparation.path,'utf8'));
  assert.equal(manifest.audit.inline_resource_count,1);assert.equal(manifest.audit.inline_input_count,2);
  assert.deepEqual(manifest.audit.budgets,{item_bytes:16384,resource_bytes:16384,input_bytes:16384,total_bytes:32768});
  assert.equal(digest(await readFile(bundle.context_preparation.path)),bundle.context_preparation.sha256);
  assert(result.response_schema);assert(result.allowed_paths);assert(result.workspace);
});

test('historical orchestration indices retain file delivery and never inline resource bodies',async t=>{
  const f=await fixture(t,{legacyTaskDelivery:true,resources:{'reference.txt':'PRIVATE_RESOURCE_BODY'.repeat(2000)},mutateWorkflow:workflow=>{
    workflow.nodes.find(n=>n.id==='final').prompt_template='Long bounded task '+ 'instruction '.repeat(1000);
  }});
  const result=await f.service.call('native_next',{}, {model:true,modelThreadId:thread});
  assert.equal(result.task_delivery,'file');assert(!Object.hasOwn(result,'task_bundle'));
  assert(result.instruction.includes('12000-byte inline limit'));
  const bytes=await readFile(result.task_bundle_path);assert(bytes.length>12000);
  assert(!bytes.toString().includes('PRIVATE_RESOURCE_BODY'));
  const again=await f.service.call('native_next',{}, {model:true,modelThreadId:thread});
  assert.deepEqual(again,result);assert.equal(f.sessions(),0);
  await writeFile(result.task_bundle_path,Buffer.concat([bytes,Buffer.from(' ')]));
  await assert.rejects(f.service.call('native_next',{}, {model:true,modelThreadId:thread}),{code:'MAIN_ORCHESTRATION_BUNDLE'});
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


test('API fail_node releases the authenticated handoff when admission fences before cleanup fails',async t=>{
  const f=await fixture(t);
  await f.service.call('native_next',{}, {model:true,modelThreadId:thread});
  const record=await f.runtime.runs.read(f.run_id),attempt=record.state.nodes.final.attempts.at(-1);
  const args={run_id:f.run_id,node_id:'final',attempt_id:attempt.id,control_token:f.control_token,
    lease_token:leaseToken(f.control_token,f.run_id,'final',attempt.id,attempt.lease_generation??0),error:{message:'Exact API failure'}};
  const stop=f.manager.stopAttempt.bind(f.manager);
  f.manager.stopAttempt=async()=>{throw Object.assign(new Error('Exact stop failed'),{code:'EXACT_STOP_FAILURE'});};
  t.after(()=>{f.manager.stopAttempt=stop;});
  await assert.rejects(f.service.call('fail_node',args,{human:true}),error=>{
    assert.equal(error.code,'FAIL_NODE_STOP_INCOMPLETE');assert(error.errors.some(item=>item.code==='EXACT_STOP_FAILURE'));return true;
  });
  assert.throws(()=>f.service.attemptAdmission.assertAttemptActive(f.run_id,'final',attempt.id),{code:'ATTEMPT_STOPPED'});
  assert.equal((await f.runtime.get(f.run_id)).nodes.final.status,'running','Runtime failure was never committed');
  assert.equal(foregroundActivityCount(f.runtime.runs.root),0,'The actual admission fence settles scheduling priority before cleanup errors');
  await assert.rejects(prepareMainOrchestration(f.runtime,{run_id:f.run_id,control_token:f.control_token,thread_id:thread}),{code:'ATTEMPT_STOPPED'});
  assert.equal(foregroundActivityCount(f.runtime.runs.root),0,'A stopped attempt cannot restore a handoff after an uncommitted failure');
});

test('API failure and retry authority errors cannot revoke admission or release another handoff',async t=>{
  const f=await fixture(t);await f.service.call('native_next',{}, {model:true,modelThreadId:thread});
  const record=await f.runtime.runs.read(f.run_id),attempt=record.state.nodes.final.attempts.at(-1);
  const args={run_id:f.run_id,node_id:'final',attempt_id:attempt.id,control_token:f.control_token,
    lease_token:leaseToken(f.control_token,f.run_id,'final',attempt.id,attempt.lease_generation??0),error:{message:'Rejected identity'}};
  for(const [changes,code] of [[{control_token:'wrong'},'RUN_AUTHORITY'],[{lease_token:'wrong'},'LEASE_INVALID'],[{node_id:'wrong'},'LEASE_INVALID'],[{error:{message:null}},'FAILURE_SCHEMA']]){
    await assert.rejects(f.service.call('fail_node',{...args,...changes},{human:true}),{code});
    f.service.attemptAdmission.assertAttemptActive(f.run_id,'final',attempt.id);
    assert.equal(foregroundActivityCount(f.runtime.runs.root),1);
  }
  await assert.rejects(f.service.call('retry_node',{run_id:f.run_id,node_id:'final',control_token:'wrong'},{human:true}),{code:'RUN_AUTHORITY'});
  f.service.attemptAdmission.assertAttemptActive(f.run_id,'final',attempt.id);
  assert.equal(foregroundActivityCount(f.runtime.runs.root),1);
  await assert.rejects(f.service.call('retry_node',{run_id:f.run_id,node_id:'final',control_token:f.control_token},{human:true}),{code:'NODE_RETRY_STATE'});
  f.service.attemptAdmission.assertAttemptActive(f.run_id,'final',attempt.id);
  assert.equal(foregroundActivityCount(f.runtime.runs.root),1,'An active-node invalid retry cannot fence the current handoff');
});

for(const maxAttempts of [1,3])test(`API failed-node retry preserves the pinned attempt budget: ${maxAttempts}`,async t=>{
  const f=await fixture(t,{mutateWorkflow:w=>{w.nodes.find(n=>n.id==='final').retry.max_attempts=maxAttempts;}});
  await f.service.call('native_next',{}, {model:true,modelThreadId:thread});
  const record=await f.runtime.runs.read(f.run_id),attempt=record.state.nodes.final.attempts.at(-1);
  const binding={run_id:f.run_id,node_id:'final',attempt_id:attempt.id,control_token:f.control_token,
    lease_token:leaseToken(f.control_token,f.run_id,'final',attempt.id,attempt.lease_generation??0)};
  await f.service.call('fail_node',{...binding,error:{message:'Retry budget fixture'}},{human:true});
  const retry={run_id:f.run_id,node_id:'final',control_token:f.control_token,reconciliation:{attempt_id:attempt.id,
    dispatch_request_id:attempt.dispatch.request_id,outcome:'terminated',evidence:[{kind:'logical_main_closed'}]}};
  if(maxAttempts===1){await assert.rejects(f.service.call('retry_node',retry,{human:true}),{code:'RETRY_LIMIT'});return;}
  assert.equal((await f.service.call('retry_node',retry,{human:true})).status,'running');
  f.service.attemptAdmission.assertRunActive(f.run_id);
  const next=await f.service.call('native_next',{}, {model:true,modelThreadId:thread});assert.equal(next.status,'orchestration_handoff');
  const current=await f.runtime.get(f.run_id);assert.equal(current.nodes.final.attempts.length,2);
  assert.equal(foregroundActivityCount(f.runtime.runs.root),1);
});

test('Run startup coalesces background history maintenance and manual cleanup preserves active Runs',async t=>{
  const f=await fixture(t);
  await f.service.call('native_next',{}, {model:true,modelThreadId:thread});
  await f.service.call('orchestration_complete',{output:{conclusion:'completed'}},{model:true,modelThreadId:thread});
  await f.service.historyMaintenance.settle();
  const maintenance=await f.service.historyMaintenance.status();
  assert.equal(maintenance.outcome,'succeeded');
  const record=await f.runtime.runs.read(f.run_id);
  const state=structuredClone(record.state);
  state.run_id='old-completed';state.finished_at='2020-01-01T00:00:00.000Z';state.updated_at=state.finished_at;
  await f.runtime.runs.create(state.run_id,record.pins,new Map(),state);
  const newRun=await f.service.call('begin_main',f.options);
  await f.service.historyMaintenance.settle();
  assert.equal((await f.service.historyMaintenance.status()).job_id,maintenance.job_id);
  assert.equal((await f.runtime.runs.read('old-completed')).state.status,'succeeded');
  assert.equal((await f.runtime.runs.read(f.run_id)).state.status,'succeeded');
  const cleaned=await f.service.call('cleanup_run_history',{}, {human:true});
  assert.deepEqual(new Set(cleaned.deleted_run_ids),new Set([f.run_id,'old-completed']));
  await assert.rejects(f.runtime.runs.read('old-completed'),{code:'ENOENT'});
  assert.equal((await f.runtime.runs.read(newRun.host_binding.run_id)).state.status,'running');
});

test('current Main without node runtime requirements skips environment preparation', async t => {
  const f = await fixture(t, { runtimeEnv: { PATH: process.env.PATH } });
  await f.service.call('native_next', {}, { model: true, modelThreadId: thread });
  let verifies = 0, discoveries = 0;
  f.runtime.environmentVerifier = async () => { verifies++; throw new Error('unexpected environment verification'); };
  f.runtime.environmentResolver = async () => { discoveries++; throw new Error('unexpected environment discovery'); };
  const result = await prepareMainOrchestration(f.runtime, { run_id: f.run_id, control_token: f.control_token, thread_id: thread });
  assert.equal(result.status, 'orchestration_handoff');
  assert.equal(verifies, 0);
  assert.equal(discoveries, 0);
});

test('current Main reuses a bound node environment without rediscovery or rebinding', async t => {
  const f = await fixture(t, { runtimeEnv: { PATH: process.env.PATH }, mutateWorkflow: workflow => {
    workflow.nodes.find(node => node.id === 'final').runtime_requirements = { executables: ['node'] };
  } });
  await f.service.call('native_next', {}, { model: true, modelThreadId: thread });
  const before = await f.runtime.runs.read(f.run_id);
  const binding = structuredClone(before.state.nodes.final.runtime_environment_binding);
  assert.equal(binding?.environment?.status, 'ready');
  assert(binding.environment.tools.some(tool => tool.name === 'node' && tool.path));
  let verifies = 0, discoveries = 0, rebinds = 0;
  f.runtime.environmentVerifier = async (requirements, environment) => {
    verifies++;
    assert(requirements.executables.some(item => (typeof item === 'string' ? item : item.name) === 'node'));
    assert.deepEqual(environment, binding.environment);
  };
  f.runtime.environmentResolver = async () => { discoveries++; throw new Error('bound environment must not be rediscovered'); };
  const transition = f.runtime.transition.bind(f.runtime);
  f.runtime.transition = async (runId, kind, ...args) => {
    if (kind === 'runtime_environment_rebound' || kind === 'runtime_environment_attention') rebinds++;
    return transition(runId, kind, ...args);
  };
  const result = await prepareMainOrchestration(f.runtime, { run_id: f.run_id, control_token: f.control_token, thread_id: thread });
  const after = await f.runtime.runs.read(f.run_id);
  assert.equal(result.status, 'orchestration_handoff');
  assert.equal(verifies, 1);
  assert.equal(discoveries, 0);
  assert.equal(rebinds, 0);
  assert.deepEqual(after.state.nodes.final.runtime_environment_binding, binding);
  const task = result.task_bundle?.task ?? JSON.parse(await readFile(result.task_bundle_path, 'utf8')).task;
  assert(task.includes(JSON.stringify(binding.environment.tools.map(({name,status,path})=>({name,status,path})))),
    'Current Main task must retain the exact Host-verified executable locations');
});
