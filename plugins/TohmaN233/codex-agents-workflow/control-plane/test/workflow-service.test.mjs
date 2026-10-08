import { deferred } from './fixtures/deferred.mjs';
import test from 'node:test';
import {spawn} from 'node:child_process';
import {once} from 'node:events';
import {createInterface} from 'node:readline';
import {fileURLToPath} from 'node:url';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, rm, rename, readFile, writeFile } from 'node:fs/promises';
import { tmpdir } from './physical-tempdir.mjs';
import { dirname, join, resolve } from 'node:path';
import { loadConfig, saveConfig, configRevision, resolveAuditPath } from '../lib/config.mjs';
import { WorkflowService } from '../lib/workflow-service.mjs';
import { ConnectorTaskStore } from '../connectors/task-store.mjs';
import { ConnectorRegistry, connectorRegistryFor } from '../connectors/registry.mjs';
import { DEFAULT_CONFIG_PATH, handleRpc, startConsole, stopConsole } from '../server.mjs';
import { SkillInventory } from '../lib/skill-import/inventory.mjs';
import { workflowToolDefinitions, HOST_ONLY_WORKFLOW_OPERATIONS } from '../lib/workflow-tools.mjs';
import { createDraft } from '../lib/workflow-schema.mjs';
import { hostResultProposalEnvelope } from '../lib/execution/host-main-automation.mjs';
import { inspectNativeAgent } from '../lib/execution/native-agent-observer.mjs';
import { createConversionCertificate, requireCurrentConversionCertificate } from '../lib/skill-import/conversion-certificate.mjs';
import { CONVERSION_CONTRACT } from '../lib/skill-import/conversion-contract.mjs';
import { digest } from '../lib/workflow-revisions.mjs';
import { workflowResourceProgramIdentity } from '../lib/execution/workflow-resource-program.mjs';
import { qualifiedExecutionBinding } from '../lib/execution/codex-tool-broker.mjs';

test('customized connector Role delivers its current instructions without a legacy Task Type or Workflow Run',async t=>{
  const delivered=[];
  const f=await fixture(t,{configure:config=>{config.providers.find(p=>p.id==='grok-local').enabled=true;},
    registry:{start:async args=>{delivered.push(args);return {task_id:'connector-role-task',state:'running'};}}});
  await f.migrate();
  const draft=await f.service.call('customize_role',{workflow_id:'builtin-role-cross-review'},{human:true});
  const workflow=structuredClone(draft.workflow);workflow.enabled=true;
  const node=workflow.nodes.find(n=>n.id==='role');node.executor={kind:'provider',provider_id:'grok-local'};
  node.prompt_template='Review the actual source independently. Return evidence-backed findings.';
  const saved=await f.service.call('save',{workflow_id:workflow.id,expected_revision:draft.revision_hash,workflow},{human:true});
  await f.service.call('publish',{workflow_id:workflow.id,expected_revision:saved.revision_hash},{human:true});
  const role=(await f.service.call('role_templates')).find(r=>r.id==='builtin-role-cross-review');
  const args={workflow_id:role.id,revision_hash:role.revision_hash,task:'Audit retry identity.',workspace:f.workspace,
    context:'Frozen local commit',constraints:'No writes',verification:'Trace the actual callers'};
  const profile=await f.service.call('role_template',args);
  assert.equal(profile.adapter.operations.start,'workflow_start_role_connector');
  const tool=workflowToolDefinitions().find(t=>t.name===profile.adapter.operations.start);
  assert(tool);assert(tool.inputSchema.required.includes('revision_hash'));
  assert.equal(Object.hasOwn(tool.inputSchema.properties,'task_type_id'),false);
  t.mock.method(connectorRegistryFor({configPath:f.configPath,env:{}}),'start',f.service.registry.start);
  const rpc=await handleRpc({jsonrpc:'2.0',id:1,method:'tools/call',params:{name:tool.name,arguments:args}},
    {configPath:f.configPath,defaultConfigPath:DEFAULT_CONFIG_PATH,env:{}});
  assert.notEqual(rpc.result.isError,true,JSON.stringify(rpc.result));
  assert.equal(delivered.length,1);assert.equal(delivered[0].provider.id,'grok-local');
  assert.equal(delivered[0].prompt,profile.instructions);assert.equal(delivered[0].stage.read_only,true);
  assert.equal(delivered[0].taskTypeId,role.id);assert.equal(delivered[0].userApproved,false);
  assert.equal((await f.service.call('runs')).length,0);
  const audit=await readFile(resolveAuditPath(f.configPath),'utf8');
  assert.match(audit,/role-connector-start/);assert.match(audit,/connector-role-task/);
  await assert.rejects(f.service.call('start_role_connector',{...args,revision_hash:'stale'}),{code:'ROLE_REVISION'});
  await assert.rejects(f.service.call('start_role_connector',{...args,revision_hash:undefined}),{code:'ROLE_REVISION'});
  const config=await loadConfig({configPath:f.configPath,defaultConfigPath:DEFAULT_CONFIG_PATH});
  config.providers.find(p=>p.id==='grok-local').enabled=false;await saveConfig(config,{configPath:f.configPath});
  await assert.rejects(f.service.call('start_role_connector',args),{code:'ROLE_PROVIDER_UNAVAILABLE'});
  assert.equal(delivered.length,1,'Rejected configuration must not invoke a different Provider');
});

test('connector Role launch retains write scope/approval and rejects disabled control, native routes and cancellation',async t=>{
  const delivered=[];
  const f=await fixture(t,{configure:config=>{const p=config.providers.find(p=>p.id==='grok-local');p.enabled=true;p.requires_user_approval=true;},
    registry:{start:async args=>{args.assertActive();delivered.push(args);return {task_id:'write-role-task',state:'running'};}}});
  await f.migrate();
  const draft=await f.service.call('build_workflow',{workflow_id:'write-connector-role',name:'Write connector Role',brief:'Fix the owned parser.',provider_id:'grok-local',template_kind:'role',access:'bounded_write'});
  const ready=await f.service.call('publish',{workflow_id:draft.workflow.id,expected_revision:draft.revision_hash},{human:true});
  const args={workflow_id:ready.workflow.id,revision_hash:ready.revision_hash,task:'Fix parser.',workspace:f.workspace,allowed_paths:['parser.mjs'],user_approved:true};
  await f.service.call('start_role_connector',args);
  assert.equal(delivered[0].stage.read_only,false);assert.deepEqual(delivered[0].allowedPaths,['parser.mjs']);
  assert.equal(delivered[0].provider.requires_user_approval,true);assert.equal(delivered[0].userApproved,true);
  const cancelled=new AbortController();cancelled.abort();
  await assert.rejects(f.service.call('start_role_connector',args,{signal:cancelled.signal}),{code:'ROLE_START_CANCELLED'});
  const native=await f.service.call('role_template',{workflow_id:'builtin-role-repository-analysis',task:'Trace calls'});
  await assert.rejects(f.service.call('start_role_connector',{workflow_id:native.id,revision_hash:native.revision_hash,task:'Trace calls',workspace:f.workspace}),{code:'ROLE_CONNECTOR_REQUIRED'});
  const config=await loadConfig({configPath:f.configPath,defaultConfigPath:DEFAULT_CONFIG_PATH});config.global.enabled=false;
  await saveConfig(config,{configPath:f.configPath});
  await assert.rejects(f.service.call('start_role_connector',args),{code:'CONTROL_DISABLED'});
  assert.equal(delivered.length,1);
});

async function publishedConnectorRole(t, { access = 'bounded_write', approval = false, pathScope, providerApproval = false } = {}) {
  const delivered = [];
  const f = await fixture(t, { configure: config => {
    const provider = config.providers.find(p => p.id === 'grok-local');
    provider.enabled = true; provider.requires_user_approval = providerApproval;
  } });
  const registry = new ConnectorRegistry({ configPath: f.configPath, env: {} });
  t.mock.method(registry.grok, 'start', async params => {
    params.assertActive(); delivered.push(params);
    return { task_id: 'published-role-task', state: 'running' };
  });
  f.service.registry = registry;
  await f.migrate();
  const draft = await f.service.call('build_workflow', { workflow_id: 'published-connector-policy', name: 'Published connector policy',
    brief: 'Perform the assigned task within its configured scope.', provider_id: 'grok-local', template_kind: 'role', access });
  const workflow = structuredClone(draft.workflow), node = workflow.nodes.find(n => n.id === 'role');
  node.approval.required = approval;
  if (pathScope !== undefined) node.path_scope = pathScope;
  const saved = await f.service.call('save', { workflow_id: workflow.id, expected_revision: draft.revision_hash, workflow }, { human: true });
  const ready = await f.service.call('publish', { workflow_id: workflow.id, expected_revision: saved.revision_hash }, { human: true });
  assert.equal(ready.workflow.status, 'ready');
  const args = { workflow_id: ready.workflow.id, revision_hash: ready.revision_hash, task: 'Perform the configured task.', workspace: f.workspace };
  return { ...f, ready, args, delivered };
}

test('published connector Role approval and fixed paths reach actual registry admission and durable audit', async t => {
  const f = await publishedConnectorRole(t, { approval: true, pathScope: ['src/allowed'] });
  const args = { ...f.args, allowed_paths: ['src/allowed/parser.mjs'] };
  const profile = await f.service.call('role_template', args);
  assert.equal(profile.adapter.requires_user_approval, true);
  assert.deepEqual(profile.path_scope, ['src/allowed']);
  await assert.rejects(f.service.call('start_role_connector', args), { code: 'APPROVAL_REQUIRED' });
  assert.equal(f.delivered.length, 0);
  for (const allowed_paths of [['src/outside-role'], ['src'], ['.'], ['src/allowed', 'src/outside-role']]) {
    await assert.rejects(f.service.call('start_role_connector', { ...args, user_approved: true, allowed_paths }), { code: 'ROLE_PATH_SCOPE' });
  }
  assert.equal(f.delivered.length, 0);
  await f.service.call('start_role_connector', { ...args, user_approved: true });
  assert.equal(f.delivered.length, 1);
  const delivered = f.delivered[0];
  assert.equal(delivered.provider.id, 'grok-local'); assert.equal(delivered.provider.requires_user_approval, false);
  assert.equal(delivered.stage.requires_user_approval, true); assert.equal(delivered.stage.read_only, false);
  assert.deepEqual(delivered.allowedPaths, ['src/allowed/parser.mjs']);
  await f.service.call('start_role_connector', { ...args, user_approved: true,
    allowed_paths: [join(f.workspace, 'src', 'allowed', 'parser.mjs')] });
  assert.equal(f.delivered.length, 2);
  assert.deepEqual(f.delivered[1].allowedPaths, ['src/allowed/parser.mjs']);
  assert.equal(delivered.prompt, profile.instructions); assert.equal(delivered.taskTypeId, f.ready.workflow.id);
  assert.equal(profile.revision_hash, f.ready.revision_hash); assert.equal(profile.provider_id, 'grok-local');
  const events = (await readFile(resolveAuditPath(f.configPath), 'utf8')).trim().split('\n').map(JSON.parse);
  const audit = events.find(event => event.event === 'role-connector-start');
  assert.equal(audit.role_id, f.ready.workflow.id); assert.equal(audit.revision_hash, f.ready.revision_hash);
  assert.equal(audit.access, 'bounded_write'); assert.equal(audit.provider_id, 'grok-local'); assert.equal(audit.task_id, 'published-role-task');
  assert.equal((await f.service.call('runs')).length, 0);
});

test('published connector Roles preserve unconfigured, fixed-scope, read-only and Provider approval behavior', async t => {
  for (const options of [
    { access: 'read_only' },
    { access: 'bounded_write' },
    { access: 'bounded_write', pathScope: ['src/allowed'] },
    { access: 'read_only', approval: true },
    { access: 'bounded_write', providerApproval: true },
  ]) await t.test(JSON.stringify(options), async child => {
    const f = await publishedConnectorRole(child, options);
    const allowed_paths = options.access === 'read_only' ? undefined : [options.pathScope ? 'src/allowed/result.txt' : 'unscoped/result.txt'];
    const args = { ...f.args, ...(allowed_paths ? { allowed_paths } : {}) };
    const approvalRequired = options.approval === true || options.providerApproval === true;
    const profile = await f.service.call('role_template', args);
    assert.equal(profile.adapter.requires_user_approval, approvalRequired);
    if (approvalRequired) await assert.rejects(f.service.call('start_role_connector', args), { code: 'APPROVAL_REQUIRED' });
    await f.service.call('start_role_connector', { ...args, user_approved: approvalRequired });
    assert.equal(f.delivered.length, 1); assert.equal(f.delivered[0].stage.read_only, options.access === 'read_only');
    assert.deepEqual(f.delivered[0].allowedPaths, allowed_paths ?? []);
    const audit = JSON.parse((await readFile(resolveAuditPath(f.configPath), 'utf8')).trim().split('\n').at(-1));
    assert.equal(audit.role_id, f.ready.workflow.id); assert.equal(audit.revision_hash, f.ready.revision_hash); assert.equal(audit.access, options.access);
  });
});
import { nativeRejectedTurnHistory } from '../lib/workflow-runtime.mjs';
import { readHostMainWorker, watchHostMainAuthority, writeHostMainWorker } from '../lib/execution/host-main-worker.mjs';
import { AUTHORING_PLANNER_PROMPT_V27, AUTHORING_REVIEW_PROMPT_V22 } from '../lib/authoring/authoring-workflows.mjs';
import { leaseToken } from '../lib/workflow-execution-envelope.mjs';

test('production WorkflowService keeps a running native Agent inside one Host event wait', async () => {
  const serviceSource=await readFile(new URL('../lib/workflow-service.mjs',import.meta.url),'utf8');
  assert.doesNotMatch(serviceSource,/await_recorded_agents|collaboration\.wait_agent|nativeAgentWaitInstruction/);
  for(const retired of ['native_spawned','native_result','native_started','native_complete','generation_prompt_preview','start_generation',
    'advance_generation','recheck_generation','accept_rechecked_generation_review','login_generation','accept_generation',
    'create_expansion_run','apply_expansion_result','apply_expansion'])assert.doesNotMatch(serviceSource,new RegExp(`case ['\"]${retired}['\"]`));
  const parentThreadId='01a0db25-ad92-72a0-b6fa-2519a6cfa2f8';
  const childThreadId='01a0db6b-704a-7470-bef4-7da3175bb140';
  let threadReads=0,turnReads=0,sessionCalls=0,complete=false,releaseEvent,settled=false;
  const client={async call(method,args){
    assert.equal(args.threadId,childThreadId);
    if(method==='thread/read'){
      threadReads++;
      return {thread:{id:childThreadId,parentThreadId,
        source:{subAgent:{thread_spawn:{parent_thread_id:parentThreadId,agent_path:'/root/child'}}}}};
    }
    assert.equal(method,'thread/turns/list');turnReads++;
    return {data:[{id:'turn-1',status:complete?'completed':'inProgress',itemsView:complete?'full':'summary',
      items:complete?[{type:'agentMessage',phase:'final_answer',text:JSON.stringify({outcome:'completed',result:{done:true},block_reason:''})}]:[]}]};
  }};
  const service=new WorkflowService({configPath:'unused-config.json',defaultConfigPath:'unused-default.json',env:{},
    capabilities:{nativeAgentObserverSession:async action=>{sessionCalls++;return action(client);}}});
  const pending=service.nativeAgentObserver([childThreadId],{parentThreadId,
    readLifecycle:async()=>({turn_id:'turn-1',status:complete?'completed':'pending'}),
    waitForChange:async()=>new Promise(resolve=>{releaseEvent=()=>{complete=true;resolve();};})}).finally(()=>{settled=true;});
  await new Promise(resolve=>setTimeout(resolve,20));assert.equal(settled,false);
  releaseEvent();const result=await pending;
  assert.equal(result.status,'completed');assert.deepEqual(result.result,{done:true});
  assert.equal(sessionCalls,1);assert.equal(threadReads>=3,true);assert.equal(turnReads>=3,true);
});
test('explicit host discovery never falls back to folder scanning for inventory or import', async t => {
  const f = await fixture(t); await f.migrate();
  f.service.skillInventory = {list:async path=>({adapter:'host',path})};
  f.service.folderInventory = {list:async path=>({adapter:'folders',path})};
  for (const operation of ['skill_inventory','import_skill']) {
    await assert.rejects(f.service.call(operation,{discovery:'host'}),{code:'SKILL_DISCOVERY_WORKSPACE'});
    await assert.rejects(f.service.call(operation,{discovery:'unknown'}),{code:'SKILL_DISCOVERY_MODE'});
  }
  assert.equal((await f.service.call('skill_inventory',{workspace:f.workspace})).adapter,'host');
  assert.equal((await f.service.call('skill_inventory',{})).adapter,'folders');
  assert.equal((await f.service.call('skill_inventory',{discovery:'folders',workspace:f.workspace})).adapter,'folders');
});

test('folder import prepares routing without exposing the removed direct-apply entry', async t => {
  const f = await fixture(t); await f.migrate();
  const source = join(f.root,'skill-folder'); await mkdir(source);
  await writeFile(join(source,'SKILL.md'),'---\nname: routing-test\ndescription: Review results\n---\nReview the result.');
  const inventory = await f.service.call('skill_inventory',{discovery:'folders',folder:source});
  assert.equal(inventory.entries.length,1);
  assert(workflowToolDefinitions().find(t=>t.name==='workflow_prepare_expansion').inputSchema.properties.routing_rules);
  assert.equal(Object.hasOwn(workflowToolDefinitions().find(t=>t.name==='workflow_save').inputSchema.properties,'resources'),false);
  for (const provider_id of [undefined,'native-luna']) {
    const pack = await f.service.call('import_skill',{discovery:'folders',folder:source,skill_id:inventory.entries[0].id,workflow_id:provider_id?'provider-import':'main-import',provider_id});
    assert.deepEqual(pack.workflow.host_automation, { version: 1, lifecycle: 'host_managed', agent_submission: 'semantic_values_only', finite_choices: 'host_form' });
    assert.equal(pack.provenance.compiler_version, 4);
    const packet = await f.service.call('prepare_expansion',{workflow_id:pack.workflow.id,revision_hash:pack.revision_hash,provider_id:'native-luna'});
    assert.equal(packet.routing_rules.routes.review.provider_id,'native-sol');
    assert.equal(packet.invoked,false);
    const origin = {confidence:1,source_span:{resource:'source/SKILL.md',start_line:5,end_line:5}};
    const proposal = {source_revision:pack.revision_hash,planning_analysis:{parallelism:'Single bounded task; no independent work.',main_responsibilities:'Main accepts; subagent checks.',human_intervention:'Final human confirmation only.'},nodes:[{id:'check',type:'agent',execution_target:'subagent',provider_choice:'native-sol',task_type:'review',routing_reason:'Independent review',prompt_template:'Review',...origin}],edges:[{id:'a',source:'start',target:'check',...origin},{id:'b',source:'check',target:'final',...origin}]};
    const args = {workflow_id:pack.workflow.id,expected_revision:pack.revision_hash,proposal};
    assert.equal(workflowToolDefinitions().some(tool=>tool.name==='workflow_apply_expansion'),false);
    await assert.rejects(f.service.call('apply_expansion',args),{code:'WORKFLOW_OPERATION'});
  }
});

async function fixture(t, options = {}) {
  const root = await mkdtemp(join(tmpdir(), 'workflow-service-')); const workspace = join(root, 'workspace'); await mkdir(workspace);
  t.after(async () => { await Promise.allSettled([...service.attemptAdmission.drainJobs.values()]); assert(resolve(root).startsWith(resolve(tmpdir()))); await rm(root, { recursive: true, maxRetries: 3, retryDelay: 100 }); });
  const configPath = join(root, 'control-plane.json'); const config = await loadConfig({ configPath, defaultConfigPath: DEFAULT_CONFIG_PATH });
  if (options.configure) { options.configure(config); await saveConfig(config, { configPath }); }
  const service = new WorkflowService({ configPath, defaultConfigPath: DEFAULT_CONFIG_PATH, env: {}, ...options,
    capabilities:{nativeAgentObserver:null,nativeParentVerifier:async()=>{},...options.capabilities} });
  return { root, configPath, workspace, service,
    migrate: () => service.call('migrate_v6', {}, { human: true }),
    start: () => service.call('start', { workflow_id: 'brainstorm', workspace, access: 'read_only', main_actor: 'root', native_parent_thread_id:'01a0db81-70bf-7233-9021-4b4e3849bec7',inputs: { task: 'Synthetic workflow integration', context: 'Fixture only' } }),
  };
}
const control = run => ({ run_id: run.run_id, control_token: run.control_token });

test('unknown Host identity reports only its workflow while service opening and unrelated start remain available', async t => {
  const f = await fixture(t); await f.migrate();
  const { store } = await f.service.open();
  const workflow = { ...createDraft('unknown-host-identity', 'Unknown Host identity'), host_tools: [{
    id: 'unknown-resource-tool', identity: { ...workflowResourceProgramIdentity(), sha256: 'f'.repeat(64) },
    argv: ['node', 'scripts/check.mjs', 'work'], input_schema: { type: 'object' }, output_schema: { type: 'object' }, env_allow: [],
    permissions: { network: false, read_paths: [], write_paths: ['work'] }, output_cap_bytes: 4096,
    deadline_ms: 10000, idempotency: { mode: 'safe' },
  }] };
  const original = await store.create(workflow);
  const opened = await f.service.open();
  assert.equal(opened.host_tool_identity_issues.length, 1);
  assert.equal(opened.host_tool_identity_issues[0].workflow_id, workflow.id);
  assert.equal(opened.host_tool_identity_issues[0].code, 'HOST_TOOL_IDENTITY_MIGRATION_UNSUPPORTED');
  assert.deepEqual(await opened.store.snapshot(workflow.id), original);
  const listed = await f.service.call('list', { include_legacy: true });
  const blocked = listed.find(pack => pack.id === workflow.id);
  assert.equal(blocked.validation.launch_ready, false);
  assert(blocked.validation.errors.some(error => error.host_tool_id === 'unknown-resource-tool'));
  const authoring = await opened.store.snapshot(listed.find(pack => pack.system_managed).id);
  const unknownAuthoring = structuredClone(authoring.workflow);
  unknownAuthoring.host_tools[0].identity.sha256 = 'e'.repeat(64);
  const authoringHead = await opened.store.save(authoring.workflow.id, unknownAuthoring, { expected_revision: authoring.revision_hash });
  const inventory = await f.service.call('list', { include_legacy: true });
  assert.equal(inventory.find(pack => pack.id === authoring.workflow.id).validation.launch_ready, false);
  assert.deepEqual(await opened.store.snapshot(authoring.workflow.id), authoringHead);
  const beforeRuns = (await opened.runtime.runs.list()).length;
  await assert.rejects(f.service.call('start', { workflow_id: workflow.id, workspace: f.workspace, access: 'read_only', main_actor: 'root', inputs: {} }),
    { code: 'HOST_TOOL_BINDING_STALE' });
  assert.equal((await opened.runtime.runs.list()).length, beforeRuns);
  const unrelated = await f.start();
  assert.equal(unrelated.status, 'running');
  assert.deepEqual(await opened.store.snapshot(workflow.id), original);
});

async function recordNativeSpawn(f,args){
  const {runtime}=await f.service.open();await runtime.authorizeController(args.run_id,{control_token:args.control_token});
  const record=await runtime.runs.read(args.run_id);
  const matches=record.pins.root.workflow.nodes.flatMap(definition=>{
    const attempt=record.state.nodes[definition.id]?.attempts.find(item=>item.id===args.attempt_id);
    return attempt?[{definition,attempt}]:[];
  });
  assert.equal(matches.length,1);const {definition,attempt}=matches[0];
  const binding={run_id:args.run_id,node_id:definition.id,attempt_id:attempt.id,control_token:args.control_token,
    lease_token:leaseToken(args.control_token,args.run_id,definition.id,attempt.id,attempt.lease_generation??0)};
  await runtime.recordExecutorEvent(args.run_id,{...binding,event:{kind:'native_agent_spawn',metadata:{index:args.index,agent_id:args.agent_id}}});
  return {recorded:true,index:args.index,agent_id:args.agent_id};
}

test('cross-instance Run cancellation waits for detached owner interrupt and close confirmation', async t => {
  const f = await fixture(t); await f.migrate(); const run = await f.start();
  const { runtime } = await f.service.open();
  await writeHostMainWorker(f.configPath, run.run_id, 'running');
  let enteredStop, releaseClose; const stopEntered = new Promise(resolve => { enteredStop = resolve; });
  const closeReleased = new Promise(resolve => { releaseClose = resolve; });
  let interrupted = false, closed = false;
  // The owner is deliberately separate from the WorkflowService that cancels.
  const owner = { async stopRun(id) {
    assert.equal(id, run.run_id); interrupted = true; enteredStop();
    await closeReleased; closed = true;
  } };
  const observation = watchHostMainAuthority({ runtime, runId: run.run_id, controlToken: run.control_token,
    owner: 'root', stopRun: id => owner.stopRun(id), healthMs: 20 });
  t.after(() => { releaseClose(); void observation.close(); });
  const other = new WorkflowService({ configPath: f.configPath, defaultConfigPath: DEFAULT_CONFIG_PATH, env: {},
    capabilities: f.service.capabilities });
  let cancellationReturned = false;
  const cancelling = other.call('cancel', control(run)).then(value => { cancellationReturned = true; return value; });
  await stopEntered;
  assert.equal(interrupted, true); assert.equal(closed, false); assert.equal(cancellationReturned, false);
  releaseClose();
  assert.deepEqual(await observation.done, { reason: 'cancelled' });
  await writeHostMainWorker(f.configPath, run.run_id, 'cancelled', { termination: { confirmed: true, reason: 'cancelled' } });
  const result = await cancelling;
  assert.equal(result.status, 'cancelled'); assert.equal(closed, true);
  assert.equal(cancellationReturned, true);
});

test('independent detached process closes its Host Main session before cancellation returns', { timeout: 15_000 }, async t => {
  const f = await fixture(t); await f.migrate(); const run = await f.start();
  const { runtime } = await f.service.open();
  const child = spawn(process.execPath, [fileURLToPath(new URL('./fixtures/detached-host-owner.mjs', import.meta.url)),
    f.configPath, runtime.runs.directory(run.run_id), run.run_id, run.control_token, 'root'],
  { stdio: ['ignore', 'pipe', 'pipe'], windowsHide: true });
  t.after(() => { if (child.exitCode === null) child.kill(); });
  let stderr = ''; child.stderr.on('data', data => { stderr += data; });
  const exited = once(child, 'exit');
  await new Promise((resolveReady, rejectReady) => {
    const lines = createInterface({ input: child.stdout });
    lines.once('line', line => line === 'ready' ? resolveReady() : rejectReady(new Error(`Unexpected detached owner startup: ${line}`)));
    child.once('exit', code => rejectReady(new Error(`Detached owner exited before ready (${code}): ${stderr}`)));
  });
  const other = new WorkflowService({ configPath: f.configPath, defaultConfigPath: DEFAULT_CONFIG_PATH, env: {}, capabilities: f.service.capabilities });
  const cancelled = await other.call('cancel', control(run));
  assert.equal(cancelled.status, 'cancelled');
  const record = await readHostMainWorker(f.configPath, run.run_id);
  assert.equal(record.phase, 'cancelled');
  assert(record.termination.interrupted >= 1);
  assert(record.termination.closed >= 1);
  assert.equal((await exited)[0], 0, stderr);
});

test('detached owner survives ordinary pause but stops on control recovery', async t => {
  const f = await fixture(t); await f.migrate(); const run = await f.start();
  const { runtime } = await f.service.open();
  let stops = 0;
  const observation = watchHostMainAuthority({ runtime, runId: run.run_id, controlToken: run.control_token,
    owner: 'root', stopRun: async () => { stops++; }, healthMs: 20 });
  t.after(() => { void observation.close(); });
  await runtime.pause(run.run_id, control(run));
  await new Promise(resolve => setTimeout(resolve, 50));
  assert.equal(stops, 0);
  await runtime.runs.mutate(run.run_id, 'control_recovery', state => { state.main_actor = 'new-owner'; });
  assert.deepEqual(await observation.done, { reason: 'authority_revoked' });
  assert.equal(stops, 1);
});

test('resume relaunches the same detached Host owner after controller recovery stopped it', async t => {
  const launches = [];
  const f = await fixture(t, { capabilities: {
    launchDetachedHostMain: async args => { launches.push(args); return { run_id: args.runId, status: 'starting', host_worker_pid: 4242 }; },
  } });
  await f.migrate();
  const run = await f.start();
  const { runtime } = await f.service.open();
  await runtime.pause(run.run_id, control(run));
  await writeHostMainWorker(f.configPath, run.run_id, 'stopped', {
    termination: { confirmed: true, reason: 'authority_revoked' },
  });

  const resumed = await f.service.call('resume', control(run));

  assert.equal(resumed.status, 'running');
  assert.equal(resumed.execution_owner, 'host_main_worker');
  assert.equal(resumed.next_action, 'workflow_wait');
  assert.equal(launches.length, 1);
  assert.equal(launches[0].runId, run.run_id);
  assert.equal(launches[0].controlToken, run.control_token);
  assert.equal(launches[0].owner, 'root');
});

test('resume rejects the removed failed-worker compatibility state', async t => {
  const launches = [];
  const f = await fixture(t, { capabilities: {
    launchDetachedHostMain: async args => { launches.push(args); return { run_id: args.runId, status: 'starting', host_worker_pid: 4243 }; },
  } });
  await f.migrate();
  const run = await f.start();
  await writeHostMainWorker(f.configPath, run.run_id, 'failed', {
    termination: { confirmed: true, reason: 'authority_revoked' },
    error: { code: 'HOST_MAIN_STOPPED', diagnostic: 'Host Main permission was revoked', secondary_codes: [] },
  });

  await assert.rejects(f.service.call('resume', control(run)),{code:'HOST_MAIN_RESTART_UNSAFE'});
  assert.equal(launches.length, 0);
});

test('cross-instance cancellation reports an unconfirmed detached stop instead of success', async t => {
  const f = await fixture(t); await f.migrate(); const run = await f.start();
  const { runtime } = await f.service.open();
  await writeHostMainWorker(f.configPath, run.run_id, 'running');
  const observation = watchHostMainAuthority({ runtime, runId: run.run_id, controlToken: run.control_token,
    owner: 'root', stopRun: async () => { throw Object.assign(new Error('session close was not confirmed'), { code: 'CLOSE_UNCONFIRMED' }); }, healthMs: 20 });
  t.after(() => { void observation.close().catch(() => {}); });
  const failureRecorded = observation.done.catch(async error => {
    await writeHostMainWorker(f.configPath, run.run_id, 'failed', { error: { code: error.code, message: error.message } });
  });
  const other = new WorkflowService({ configPath: f.configPath, defaultConfigPath: DEFAULT_CONFIG_PATH, env: {}, capabilities: f.service.capabilities });
  await assert.rejects(other.call('cancel', control(run)), error =>
    error.code === 'RUN_CANCEL_INCOMPLETE' && error.details.failures.some(item => item.code === 'CLOSE_UNCONFIRMED'));
  await failureRecorded;
  assert.equal((await other.call('get', control(run))).status, 'cancelled');
});

test('real MCP cancellation and EOF release a one-hour wait without cancelling its Run',{timeout:15000},async t=>{
  const f=await fixture(t);await f.migrate();const run=await f.start();
  const child=spawn(process.execPath,[fileURLToPath(new URL('../server.mjs',import.meta.url))],{
    env:{...process.env,CODEX_WORKFLOW_CONFIG:f.configPath,CODEX_WORKFLOW_DISABLED:'0',SOL_CONTROL_DISABLED:'0'},stdio:['pipe','pipe','pipe'],windowsHide:true});
  t.after(()=>{if(child.exitCode===null)child.kill();});
  let stderr='';child.stderr.on('data',data=>stderr+=data);
  const exited=once(child,'exit'),pending=new Map();
  createInterface({input:child.stdout}).on('line',line=>{const response=JSON.parse(line);pending.get(response.id)?.(response);pending.delete(response.id);});
  const send=message=>child.stdin.write(JSON.stringify({jsonrpc:'2.0',...message})+'\n');
  const request=message=>new Promise(resolve=>{pending.set(message.id,resolve);send(message);});
  const wait=id=>request({id,method:'tools/call',params:{name:'workflow_wait',arguments:{run_id:run.run_id}}});
  const first=wait(1);
  assert.deepEqual((await request({id:2,method:'ping'})).result,{});
  send({method:'notifications/cancelled',params:{requestId:1}});
  assert.match(JSON.stringify(await first),/WORKFLOW_WAIT_CANCELLED/);
  assert.equal((await f.service.call('get',{run_id:run.run_id})).status,'running');
  const second=wait(3);
  await request({id:4,method:'ping'});child.stdin.end();
  assert.match(JSON.stringify(await second),/WORKFLOW_WAIT_CANCELLED/);
  assert.equal((await exited)[0],0,stderr);
  assert.equal((await f.service.call('get',{run_id:run.run_id})).status,'running');
});

test('native bridge exposes only the three argumentless deterministic operations', async () => {
  const nativeSchemas = Object.fromEntries(workflowToolDefinitions()
    .filter(tool => tool.name.startsWith('workflow_native_'))
    .map(tool => [tool.name, tool.inputSchema.required]));
  assert.deepEqual(nativeSchemas,{
    workflow_native_next:[],
    workflow_native_spawned_batch:[],
    workflow_native_followed_up:[],
  });
  for(const name of Object.keys(nativeSchemas))assert.deepEqual(
    workflowToolDefinitions().find(tool=>tool.name===name).inputSchema.properties,{});
  for(const retired of ['native_spawned','native_result','native_started','native_complete'])
    assert.equal(HOST_ONLY_WORKFLOW_OPERATIONS.has(retired),false);
});

test('Host seals a single visible native Agent from its observed final turn',async t=>{
  const seen=[];
  const f=await fixture(t,{capabilities:{nativeAgentObserver:async ids=>{
    seen.push([...ids]);return {status:'completed',agent_id:ids[0],turn_id:'turn-1',result:{design:'ready'}};
  }}});await f.migrate();
  const run=await f.start(),binding=control(run),handoff=await f.service.call('native_next',binding);
  await recordNativeSpawn(f,{...binding,attempt_id:handoff.attempt_id,index:0,agent_id:'visible-single'});
  const completed=await f.service.call('native_next',binding);
  assert.equal(completed.next_action,'workflow_native_next',JSON.stringify(completed));
  assert.deepEqual(seen,[['visible-single']]);
  const state=await f.service.call('get',binding);
  assert.equal(state.nodes.implementation.status,'succeeded');
  assert.equal(state.nodes.implementation.output.design,'ready');
});

test('schema-valid bare native final completes the pinned node without a correction turn',async t=>{
  const parent='01a0db81-70bf-7233-9021-4b4e3849bec7';
  let observations=0;
  const observer=async(ids,options)=>{
    observations++;
    const client={async call(method,args){
      if(method==='thread/read')return {thread:{id:args.threadId,parentThreadId:parent}};
      return {data:[{id:'bare-turn',status:'completed',itemsView:'full',
        items:[{type:'agentMessage',phase:'final_answer',text:'{"design":"ready"}'}]}]};
    }};
    return inspectNativeAgent(client,ids[0],{...options,afterTurnId:options.afterTurnIds?.[ids[0]],
      rejectedTurnIds:options.rejectedTurnIds?.[ids[0]]??[],
      readLifecycle:async({turn})=>({turn_id:turn.id,status:'completed'})});
  };
  const f=await fixture(t,{capabilities:{nativeAgentObserver:observer}});await f.migrate();
  const base=await f.service.call('read',{workflow_id:'brainstorm'});
  const workflow=structuredClone(base.workflow);workflow.id='brainstorm-bare-schema';
  workflow.nodes.find(node=>node.id==='implementation').outputs_schema={type:'object',additionalProperties:false,
    properties:{design:{type:'string'}},required:['design']};
  const created=await f.service.call('create',{workflow});
  const run=await f.service.call('start',{workflow_id:workflow.id,revision_hash:created.revision_hash,
    workspace:f.workspace,access:'read_only',main_actor:'root',native_parent_thread_id:parent,
    inputs:{task:'Synthetic workflow integration',context:'Fixture only'}});
  const binding=control(run),handoff=await f.service.call('native_next',binding);
  assert.equal(handoff.result_schema?.type,'object',JSON.stringify(handoff.result_schema));
  await recordNativeSpawn(f,{...binding,attempt_id:handoff.attempt_id,index:0,agent_id:'visible-single'});
  const completed=await f.service.call('native_next',binding);
  assert.equal(completed.next_action,'workflow_native_next',JSON.stringify(completed));
  assert.equal(observations,1);
  const node=(await f.service.call('get',binding)).nodes.implementation;
  assert.equal(node.status,'succeeded');assert.deepEqual(node.output,{design:'ready'});
  assert.equal(node.attempts.length,1);assert.equal(node.attempts[0].native_rejected_turns,undefined);
  assert(node.attempts[0].executor_events.some(event=>event.kind==='session_state'&&
    event.metadata.code==='NATIVE_AGENT_RESULT_SHAPE'&&event.metadata.diagnostic.includes('bare_semantic_result')));
});

test('native wait supplies the recorded parent and journals identity registration diagnostics',async t=>{
  const diagnostic='Native Agent /root/fixture awaits registration under parent root';
  const f=await fixture(t,{capabilities:{nativeAgentObserver:async(ids,options)=>{
    assert.equal(options.parentThreadId,'01a0db81-70bf-7233-9021-4b4e3849bec7');
    await options.onIdentityEvent({status:'waiting',code:'NATIVE_AGENT_IDENTITY_PENDING',diagnostic});
    return {status:'completed',agent_id:ids[0],turn_id:'turn-path',result:{design:'ready'}};
  }}});await f.migrate();
  const run=await f.start(),binding=control(run),handoff=await f.service.call('native_next',binding);
  await recordNativeSpawn(f,{...binding,attempt_id:handoff.attempt_id,index:0,agent_id:'/root/fixture'});
  await f.service.call('native_next',binding);
  const state=await f.service.call('get',binding),attempt=state.nodes.implementation.attempts[0];
  assert.equal(attempt.dispatch.receipt.agent_id,'/root/fixture');
  assert(attempt.executor_events.some(event=>event.kind==='session_state'&&event.metadata.code==='NATIVE_AGENT_IDENTITY_PENDING'&&event.metadata.diagnostic===diagnostic));
});

test('rejected native turn is journaled once and a restarted Host keeps duplicate observations inside one pending call',async t=>{
  const observed=[];
  const observer=async(ids,options)=>{
    observed.push({ids:[...ids],afterTurnIds:options.afterTurnIds??{}});
    if(observed.length===1)return {status:'invalid',agent_id:ids[0],turn_id:'bad-turn',reason:'Final JSON malformed'};
    assert.equal(options.afterTurnIds['visible-child'],'bad-turn');
    assert.deepEqual(options.rejectedTurnIds['visible-child'],['bad-turn']);
    if(observed.length===2)return {status:'invalid',agent_id:ids[0],turn_id:'bad-turn',reason:'Final JSON malformed'};
    return {status:'completed',agent_id:ids[0],turn_id:'fixed-turn',result:{design:'ready'}};
  };
  const f=await fixture(t,{capabilities:{nativeAgentObserver:observer}});await f.migrate();
  const base=await f.service.call('read',{workflow_id:'brainstorm'});
  const workflow={...base.workflow,id:'brainstorm-repair-fixture'};
  workflow.nodes.find(node=>node.id==='implementation').retry={max_attempts:2};
  const created=await f.service.call('create',{workflow},{human:true});
  const run=await f.service.call('start',{workflow_id:workflow.id,revision_hash:created.revision_hash,
    workspace:f.workspace,access:'read_only',main_actor:'root',native_parent_thread_id:'01a0db81-70bf-7233-9021-4b4e3849bec7',
    inputs:{task:'Synthetic workflow integration',context:'Fixture only'}});
  const binding=control(run),handoff=await f.service.call('native_next',binding);
  await recordNativeSpawn(f,{...binding,attempt_id:handoff.attempt_id,index:0,agent_id:'visible-child'});
  const rejected=await f.service.call('native_next',binding);
  assert.equal(rejected.next_action,'repair_recorded_agent');
  assert.equal(rejected.turn_id,'bad-turn');
  const state=await f.service.call('get',binding);
  assert.equal(state.nodes.implementation.attempts[0].native_rejected_turns[0].turn_id,'bad-turn');
  const restarted=new WorkflowService({configPath:f.configPath,defaultConfigPath:DEFAULT_CONFIG_PATH,env:{},
    capabilities:{nativeAgentObserver:observer}});
  const completed=await restarted.call('native_next',binding);
  assert.equal(completed.next_action,'workflow_native_next');
  assert.equal(observed.length,3);
  const completedState=await restarted.call('get',binding);
  assert.equal(completedState.nodes.implementation.status,'succeeded');
  assert.equal(completedState.nodes.implementation.attempts[0].native_rejected_turns[0].count,1);
});

test('native rejection history survives a Host restart and rejects conflicting old-turn replays',async t=>{
  const f=await fixture(t);await f.migrate();
  const run=await f.start(),binding=control(run),handoff=await f.service.call('native_next',binding);
  await recordNativeSpawn(f,{...binding,attempt_id:handoff.attempt_id,index:0,agent_id:'visible-child'});
  const {runtime}=await f.service.open();
  const attempt=(await runtime.runs.read(run.run_id)).state.nodes[handoff.node_id].attempts[0];
  const {leaseToken}=await import('../lib/workflow-execution-envelope.mjs');
  const rejection={...binding,node_id:handoff.node_id,attempt_id:attempt.id,
    lease_token:leaseToken(run.control_token,run.run_id,handoff.node_id,attempt.id,attempt.lease_generation??0),
    index:0,agent_id:'visible-child',category:'invalid',reason:'Final JSON malformed'};
  for(const turn_id of ['old-turn','new-turn'])assert.equal((await runtime.recordNativeRejectedTurn(run.run_id,{...rejection,turn_id})).new,true);
  const restarted=new WorkflowService({configPath:f.configPath,defaultConfigPath:DEFAULT_CONFIG_PATH,env:{},capabilities:{nativeAgentObserver:null}});
  const nextRuntime=(await restarted.open()).runtime;
  const before=await nextRuntime.runs.read(run.run_id);
  assert.deepEqual(before.state.nodes[handoff.node_id].attempts[0].native_rejected_turns[0].turns.map(item=>item.turn_id),['old-turn','new-turn']);
  assert.equal((await nextRuntime.recordNativeRejectedTurn(run.run_id,{...rejection,turn_id:'old-turn'})).new,false);
  assert.equal((await nextRuntime.runs.read(run.run_id)).sequence,before.sequence,'same evidence does not append another journal event');
  await assert.rejects(nextRuntime.recordNativeRejectedTurn(run.run_id,{...rejection,turn_id:'old-turn',reason:'Conflicting reason'}),{code:'NATIVE_AGENT_REJECTION_CONFLICT'});
});

test('legacy native rejection snapshots recover every exact turn from their journal',()=>{
  const slot=turn_id=>({agent_id:'child',turn_id,category:'invalid',reason:`Invalid ${turn_id}`});
  const node=turn_id=>({attempts:[{id:'attempt',native_rejected_turns:{0:slot(turn_id)}}]});
  const record={state:{nodes:{work:node('new')}},events:['old','new'].map(id=>({kind:'native_agent_rejection',
    payload:{patch:{nodes:{work:node(id)}}}}))};
  assert.deepEqual(nativeRejectedTurnHistory(record,'work','attempt')[0].map(item=>item.turn_id),['old','new']);
  assert.equal(Object.hasOwn(record.state.nodes.work.attempts[0].native_rejected_turns[0],'turns'),false);
});

test('concurrent native drive calls cannot duplicate the observer or release the same successor twice',async t=>{
  const entered=deferred(),release=deferred();let observations=0;
  const observer=async ids=>{observations++;entered.resolve();await release.promise;
    return {status:'completed',agent_id:ids[0],turn_id:'turn-1',result:{design:'ready'}};};
  const f=await fixture(t,{capabilities:{nativeAgentObserver:observer}});await f.migrate();
  const run=await f.start(),binding=control(run),handoff=await f.service.call('native_next',binding);
  await recordNativeSpawn(f,{...binding,attempt_id:handoff.attempt_id,index:0,agent_id:'visible-child'});
  const pending=f.service.call('native_next',binding);
  await entered.promise;
  const duplicate=new WorkflowService({configPath:f.configPath,defaultConfigPath:DEFAULT_CONFIG_PATH,env:{},capabilities:{nativeAgentObserver:observer}});
  const deadline=setTimeout(()=>release.resolve(),100);
  try { await assert.rejects(duplicate.call('native_next',binding),{code:'NATIVE_AGENT_WAIT_ACTIVE'}); }
  finally { clearTimeout(deadline);release.resolve();await pending; }
  assert.equal(observations,1);
  assert.equal((await f.service.call('get',binding)).nodes.implementation.status,'succeeded');
});

test('native wait ownership permits another Run and releases after an observer failure',async t=>{
  const entered=deferred(),release=deferred();let fail=true;
  const observer=async ids=>{
    if(ids[0]==='slow-child'&&fail){entered.resolve();await release.promise;throw new Error('observer transport exited');}
    return {status:'completed',agent_id:ids[0],turn_id:'turn-complete',result:{design:'ready'}};
  };
  const f=await fixture(t,{capabilities:{nativeAgentObserver:observer}});await f.migrate();
  const bindings=[];
  for(const agent_id of ['slow-child','fast-child']){
    const run=await f.start(),binding=control(run),handoff=await f.service.call('native_next',binding);
    await recordNativeSpawn(f,{...binding,attempt_id:handoff.attempt_id,index:0,agent_id});
    bindings.push({...binding,attempt_id:handoff.attempt_id});
  }
  const pending=f.service.call('native_next',bindings[0]);
  const failed=assert.rejects(pending,/observer transport exited/);
  await entered.promise;
  try { assert.equal((await f.service.call('native_next',bindings[1])).next_action,'workflow_native_next'); }
  finally { release.resolve();await failed; }
  fail=false;
  assert.equal((await f.service.call('native_next',bindings[0])).next_action,'workflow_native_next');
});

test('pausing a Run fences an in-flight native observation and releases its wait owner',async t=>{
  const entered=deferred(),release=deferred();
  const f=await fixture(t,{capabilities:{nativeAgentObserver:async ids=>{
    entered.resolve();await release.promise;
    return {status:'completed',agent_id:ids[0],turn_id:'turn-complete',result:{design:'ready'}};
  }}});await f.migrate();
  const run=await f.start(),binding=control(run),handoff=await f.service.call('native_next',binding);
  await recordNativeSpawn(f,{...binding,attempt_id:handoff.attempt_id,index:0,agent_id:'visible-child'});
  const pending=f.service.call('native_next',binding);
  const stopped=assert.rejects(pending,{code:'NATIVE_AGENT_ATTEMPT_CHANGED'});
  await entered.promise;
  try { await f.service.call('pause',binding); }
  finally { release.resolve();await stopped; }
  assert.equal((await f.service.call('get',binding)).nodes.implementation.status,'running');
  await f.service.call('resume',binding);
  assert.equal((await f.service.call('native_next',binding)).next_action,'workflow_native_next');
});

test('cancelling a Run fences an in-flight unified native continuation before sealing',async t=>{
  const entered=deferred(),release=deferred();
  const f=await fixture(t,{capabilities:{nativeAgentObserver:async ids=>{
    entered.resolve();await release.promise;
    return {status:'completed',agent_id:ids[0],turn_id:'turn-after-cancel',result:{design:'late'}};
  }}});await f.migrate();
  const run=await f.start(),binding=control(run),handoff=await f.service.call('native_next',binding);
  await recordNativeSpawn(f,{...binding,attempt_id:handoff.attempt_id,index:0,agent_id:'visible-child'});
  const pending=f.service.call('native_next',binding),stopped=assert.rejects(pending,{code:'ATTEMPT_STOPPED'});
  await entered.promise;
  try{await f.service.call('cancel',binding);}
  finally{release.resolve();await stopped;}
  const state=await f.service.call('get',binding);
  assert.equal(state.nodes.implementation.status,'cancelled');
  assert.equal(state.nodes.implementation.output,null);
});

test('uncapped native fan-out records every released packet before native_next joins out-of-order results',async t=>{
  const seen=[];
  const f=await fixture(t,{capabilities:{nativeAgentObserver:async ids=>{
    seen.push([...ids]);const agent_id=ids.at(-1);
    return {status:'completed',agent_id,turn_id:`turn-${agent_id}`,result:[Number(agent_id.at(-1))]};
  }}});await f.migrate();
  const workflow={...createDraft('uncapped-native-fixture','Uncapped native fixture'),status:'ready',context_projection_version:2,
    skill_policy:{mode:'cooperative',implicit:'deny',ambient_allow:[],shadowed_skill_paths:[]},
    inputs_schema:{type:'object',properties:{jobs:{type:'array',items:{type:'integer'}}},required:['jobs'],additionalProperties:false},
    finalization:{required:true,node_id:'final'},nodes:[{id:'start',type:'start'},
      {id:'jobs',type:'agent',role:'implementer',executor:{kind:'provider',provider_id:'native-luna'},access:'read_only',
        approval:{required:false},retry:{max_attempts:1},input_bindings:{jobs:'/inputs/jobs'},
        prompt_template:'Process assigned job.',subagent_count:'auto',
        fanout:{input:'jobs',item_name:'job',distribution:'one_per_item',result_output:'results',scheduling:'parallel',join:'all_required'},
        outputs_schema:{type:'object',properties:{results:{type:'array',items:{type:'array',items:{type:'integer'}}}},required:['results'],additionalProperties:false}},
      {id:'final',type:'agent',role:'finalizer',executor:{kind:'main'},access:'read_only',approval:{required:false},retry:{max_attempts:1},
        input_bindings:{results:'/nodes/jobs/output/results'},prompt_template:'Review results.'},{id:'end',type:'end'}],
    edges:[{id:'start-jobs',source:'start',target:'jobs'},{id:'jobs-final',source:'jobs',target:'final'},{id:'final-end',source:'final',target:'end'}]};
  const created=await f.service.call('create',{workflow},{human:true});
  const run=await f.service.call('start',{workflow_id:workflow.id,revision_hash:created.revision_hash,workspace:f.workspace,
    access:'bounded_write',allowed_paths:['.'],main_actor:'root',native_parent_thread_id:'01a0db81-70bf-7233-9021-4b4e3849bec7',inputs:{jobs:[0,1]}});
  const binding=control(run),handoff=await f.service.call('native_next',binding);
  assert.deepEqual(handoff.packets.map(item=>item.index),[0,1]);
  const first=await recordNativeSpawn(f,{...binding,attempt_id:handoff.attempt_id,index:1,agent_id:'agent-1'});
  assert.equal(first.recorded,true);
  const second=await recordNativeSpawn(f,{...binding,attempt_id:handoff.attempt_id,index:0,agent_id:'agent-0'});
  assert.equal(second.recorded,true);
  const completed=await f.service.call('native_next',binding);
  assert.equal(completed.next_action,'workflow_native_next');
  assert.deepEqual(completed.next_action_args,binding);
  assert.deepEqual(seen,[['agent-0','agent-1'],['agent-0']]);
  assert.deepEqual((await f.service.call('get',binding)).nodes.jobs.output.results,[[0],[1]]);
});

test('Host awaits and records a visible native child without Main polling or manual result transcription',async t=>{
  const observed=[];
  const f=await fixture(t,{capabilities:{nativeAgentObserver:async ids=>{
    observed.push([...ids]);return {status:'completed',agent_id:ids[0],turn_id:'turn-observed',result:[42]};
  }}});await f.migrate();
  const workflow={...createDraft('host-observed-native','Host observed native'),status:'ready',context_projection_version:2,
    skill_policy:{mode:'cooperative',implicit:'deny',ambient_allow:[],shadowed_skill_paths:[]},
    inputs_schema:{type:'object',properties:{jobs:{type:'array',items:{type:'integer'}}},required:['jobs'],additionalProperties:false},
    finalization:{required:true,node_id:'final'},nodes:[{id:'start',type:'start'},
      {id:'jobs',type:'agent',role:'implementer',executor:{kind:'provider',provider_id:'native-luna'},access:'read_only',
        approval:{required:false},retry:{max_attempts:1},input_bindings:{jobs:'/inputs/jobs'},
        prompt_template:'Process assigned job.',subagent_count:'auto',
        fanout:{input:'jobs',item_name:'job',distribution:'one_per_item',result_output:'results',scheduling:'parallel',max_concurrency:1,join:'all_required'},
        outputs_schema:{type:'object',properties:{results:{type:'array',items:{type:'array',items:{type:'integer'}}}},required:['results'],additionalProperties:false}},
      {id:'final',type:'agent',role:'finalizer',executor:{kind:'main'},access:'read_only',approval:{required:false},retry:{max_attempts:1},
        input_bindings:{results:'/nodes/jobs/output/results'},prompt_template:'Review results.'},{id:'end',type:'end'}],
    edges:[{id:'start-jobs',source:'start',target:'jobs'},{id:'jobs-final',source:'jobs',target:'final'},{id:'final-end',source:'final',target:'end'}]};
  const created=await f.service.call('create',{workflow},{human:true});
  const run=await f.service.call('start',{workflow_id:workflow.id,revision_hash:created.revision_hash,workspace:f.workspace,
    access:'bounded_write',allowed_paths:['.'],main_actor:'root',native_parent_thread_id:'01a0db81-70bf-7233-9021-4b4e3849bec7',inputs:{jobs:[42]}});
  const binding=control(run);const handoff=await f.service.call('native_next',binding);
  await recordNativeSpawn(f,{...binding,attempt_id:handoff.attempt_id,index:0,agent_id:'visible-child'});
  const next=await f.service.call('native_next',binding);
  assert.equal(next.next_action,'workflow_native_next');
  assert.deepEqual(observed,[['visible-child']]);
  const state=await f.service.call('get',binding);
  assert.equal(state.nodes.jobs.status,'succeeded');
  assert.deepEqual(state.nodes.jobs.attempts[0].native_parallel_results[0].result,[42]);
});

test('model-facing Main start returns its persisted Run while prior Provider work is still pending', async t => {
  const gate = deferred(); const entered = deferred(); let progress;
  const hostMainManager = {
    launchRun: ({ drive }) => { progress = drive.advanceToMain(); return { status: 'starting' }; },
    launch: async () => ({ status: 'host-owned' }), stopRun: async () => {}, qualify: async () => ({}),
  };
  const strictManager = { capability: async () => true, stopRun: async () => {} };
  const f = await fixture(t, { capabilities: { hostMainManager, strictManager } }); await f.migrate();
  const originalOpen = f.service.open.bind(f.service);
  f.service.open = async () => {
    const opened = await originalOpen();
    opened.drive.advanceToMain = async () => { entered.resolve(); return gate.promise; };
    return opened;
  };
  const pending = f.service.call('run_main', {
    workflow_id: 'brainstorm', workspace: f.workspace, access: 'read_only', main_actor: 'root',
    inputs: { task: 'Synthetic workflow integration', context: 'Fixture only' }, return_after_start: true,
  });
  try {
    await entered.promise;
    const settled = await Promise.race([pending.then(() => true), new Promise(resolve => setTimeout(() => resolve(false), 50))]);
    assert.equal(settled, true, 'startup must not await prior Provider execution');
    const result = await pending;
    assert.equal(result.status, 'starting'); assert.equal(typeof result.control_token, 'string');
    assert((await f.service.call('runs')).some(run => run.run_id === result.run_id));
  } finally { gate.resolve({ status: 'running', stop_reason: 'no_deterministic_progress' }); if (progress) await progress; }
});

test('workflow_start keeps native dispatch and opaque continuation inside its Host owner',async t=>{
  const f=await fixture(t);await f.migrate();
  const launches=[],waits=[];
  const threadId='01a0db81-70bf-7233-9021-4b4e3849bec7';
  const response=await handleRpc({jsonrpc:'2.0',id:1,method:'tools/call',params:{name:'workflow_start',_meta:{threadId},arguments:{
    workflow_id:'brainstorm',workspace:f.workspace,access:'read_only',inputs:{task:'Synthetic',context:'Fixture'},
  }}},{configPath:f.configPath,defaultConfigPath:DEFAULT_CONFIG_PATH,env:{},serviceCapabilities:{
    hostMainManager:{qualify:async()=>({})},
    nativeParentVerifier:async parent=>{assert.equal(parent,threadId);return {agent_path:'/root'};},
    launchDetachedHostMain:async args=>{launches.push(args);return {run_id:args.runId,status:'starting'};},
    waitForOwnedWorkflow:async(service,started)=>{
      waits.push(started);assert.equal(started.run_id,launches[0].runId);
      assert.equal(started.control_token,launches[0].controlToken);
      assert.equal((await service.call('get',{run_id:started.run_id})).main_actor,'codex');
      return {run_id:started.run_id,status:'running',wake_reason:'native_handoff_required',execution_owner:'host_main_worker',
        control_token:started.control_token,next_action:'workflow_native_next',
        next_action_args:{run_id:started.run_id,control_token:started.control_token}};
    },
  }});
  assert.equal(response.result.isError,undefined,JSON.stringify(response));
  const value=JSON.parse(response.result.content[0].text);
  assert.equal(launches.length,1);assert.equal(waits.length,1);
  assert.equal(value.execution_owner,'host_main_worker');
  assert.equal(value.wake_reason,'native_handoff_required');
  assert.equal(value.control_token,undefined);assert.equal(value.packets,undefined);
  assert.deepEqual(value.next_action_args,{});
  const continued=await handleRpc({jsonrpc:'2.0',id:2,method:'tools/call',params:{name:'workflow_native_next',_meta:{threadId},arguments:{}}},
    {configPath:f.configPath,defaultConfigPath:DEFAULT_CONFIG_PATH,env:{},serviceCapabilities:{nativeParentVerifier:async parent=>({agent_path:parent===threadId?'/root':'invalid'})}});
  assert.equal(continued.result.isError,undefined,continued.result.content[0].text);
  const continuation=JSON.parse(continued.result.content[0].text);
  assert.equal(continuation.next_action,'spawn_released_packets_then_journal_batch');
  assert.deepEqual(continuation.next_action_args,{});
  assert.equal(continuation.control_token,undefined);
});

test('native_next refuses an unbound logical controller before any native dispatch or observation',async t=>{
  let observed=0,verified=0;
  const f=await fixture(t,{capabilities:{nativeAgentObserver:async()=>{observed++;},nativeParentVerifier:async()=>{verified++;}}});await f.migrate();
  const run=await f.service.call('start',{workflow_id:'brainstorm',workspace:f.workspace,access:'read_only',main_actor:'codex',
    inputs:{task:'Synthetic',context:'Fixture'}});
  await assert.rejects(f.service.call('native_next',control(run)),{code:'NATIVE_AGENT_IDENTITY_PARENT'});
  const state=await f.service.call('get',control(run));assert.equal(state.nodes.implementation.attempts.length,0);
  assert.equal(observed,0);assert.equal(verified,0);
});

test('a detached Host worker startup failure is persisted instead of leaving a ready Run silently running', async t => {
  const failure = Object.assign(new Error('worker handshake failed'), { code: 'HOST_MAIN_WORKER_START_TIMEOUT' });
  const f = await fixture(t, { capabilities: {
    hostMainManager: { qualify: async () => ({}) },
    launchDetachedHostMain: async () => { throw failure; },
  } });
  await f.migrate();
  const pack = await f.service.call('read', { workflow_id: 'brainstorm' });
  await assert.rejects(f.service.call('run_main', {
    workflow_id: 'brainstorm', revision_hash: pack.revision_hash, workspace: f.workspace,
    access: 'read_only', main_actor: 'root', inputs: { task: 'Startup failure fixture', context: 'Fixture only' },
    return_after_start: true, detached_host: true,
  }), { code: 'HOST_MAIN_WORKER_START_TIMEOUT' });
  const runs = await f.service.call('runs');
  const state = await f.service.call('get', { run_id: runs.at(-1).run_id });
  assert.equal(state.status, 'failed');
  assert.equal(state.error.code, 'HOST_MAIN_WORKER_START_TIMEOUT');
});

test('detached run_main returns an approval stop without launching a Host worker', async t => {
  const launches=[];
  const f=await fixture(t,{capabilities:{
    hostMainManager:{qualify:async()=>({}),stopRun:async()=>{}},
    launchDetachedHostMain:async args=>{launches.push(args);return {run_id:args.runId,status:'starting'};},
  }});
  await f.migrate();
  const pack=await f.service.call('read',{workflow_id:'brainstorm'});
  const stopped=await f.service.call('run_main',{
    workflow_id:'brainstorm',revision_hash:pack.revision_hash,workspace:f.workspace,
    access:'read_only',main_actor:'root',inputs:{task:'Approval stop fixture',context:'Fixture only'},
    require_approval:true,return_after_start:true,detached_host:true,
  });
  assert.equal(stopped.status,'blocked');
  assert.equal(typeof stopped.control_token,'string');
  assert.equal(Object.values(stopped.approvals).some(item=>item.status==='pending'),true);
  assert.equal(launches.length,0);
});

test('run_main preserves the exact newly started Run identity for immediate and approval stops',async t=>{
  const launches=[];const hostMainManager={launch:async value=>{launches.push(value.handoff);return {status:'host-owned'};},pending:async()=>null,accept:async()=>null,stopRun:async()=>{}};
  const strictManager={capability:async()=>true,stopRun:async()=>{}};
  const f=await fixture(t,{capabilities:{hostMainManager,strictManager}});await f.migrate();
  const workflow={...createDraft('run-main-identity','Run Main identity'),status:'ready',inputs_schema:{type:'object',properties:{task:{type:'string'}},required:['task'],additionalProperties:false},finalization:{required:true,node_id:'final'},nodes:[{id:'start',type:'start'},{id:'final',type:'agent',executor:{kind:'main'},role:'finalizer',access:'read_only',approval:{required:false},retry:{max_attempts:1},input_bindings:{task:'/inputs/task'},prompt_template:'Return {{task}}',outputs_schema:{type:'object',properties:{value:{type:'string'}},required:['value'],additionalProperties:false}},{id:'end',type:'end'}],edges:[{id:'start-final',source:'start',target:'final'},{id:'final-end',source:'final',target:'end'}]};
  const created=await f.service.call('create',{workflow},{human:true});
  const request={workflow_id:workflow.id,revision_hash:created.revision_hash,workspace:f.workspace,access:'read_only',main_actor:'root',inputs:{task:'Identity fixture'}};
  const immediate=await f.service.call('run_main',request),approval=await f.service.call('run_main',{...request,run_id:'approval-stop',require_approval:true});
  assert.match(immediate.run_id,/^[a-f0-9-]{36}$/);assert.equal(typeof immediate.control_token,'string');assert.equal(approval.run_id,'approval-stop');assert.equal(typeof approval.control_token,'string');
  assert.equal(immediate.run_id===approval.run_id,false);assert.equal(launches.length,2);
  const ids=(await f.service.call('runs')).map(run=>run.run_id);assert(ids.includes(immediate.run_id));assert(ids.includes(approval.run_id));
});

test('Role build is a direct agent profile while Workflow build keeps the shared authoring path',async t=>{
  const f=await fixture(t);await f.migrate();
  const catalog=await f.service.call('role_templates');
  assert(catalog.some(item=>item.id==='builtin-role-bounded-code-change'&&item.template_kind==='role'));
  assert(catalog.some(item=>item.id==='builtin-role-judgment-heavy-change'&&item.model==='gpt-6.1-sol'&&item.reasoning_effort==='high'));
  assert(catalog.some(item=>item.id==='builtin-role-hard-problem-solver'&&item.model==='gpt-6-astra'&&item.reasoning_effort==='medium'));
  assert(catalog.some(item=>item.id==='builtin-role-brainstorm'&&item.model==='gpt-6-astra'&&item.reasoning_effort==='medium'));
  const builtin=await f.service.call('role_template',{workflow_id:'builtin-role-bounded-code-change',task:'Change one parser function.',context:'Parser module',constraints:'Only parser.mjs',verification:'Run parser tests'});
  assert.match(builtin.instructions,/Change one parser function/);
  assert.equal(builtin.access,'bounded_write');
  const heavy=await f.service.call('role_template',{workflow_id:'builtin-role-judgment-heavy-change',task:'Change the parser interface.',context:'Several callers',constraints:'Only parser and callers',verification:'Run parser tests'});
  assert.equal(heavy.model,'gpt-6.1-sol');assert.equal(heavy.reasoning_effort,'high');
  assert.match(heavy.instructions,/judgment-heavy but bounded implementation/);
  assert.equal((await f.service.call('runs')).length,0,'Role retrieval must not create a Workflow Run or append review');
  const editable=await f.service.call('customize_role',{workflow_id:'builtin-role-bounded-code-change'},{human:true});
  assert.equal(editable.workflow.id,'role-bounded-code-change');
  assert.equal(editable.workflow.template_kind,'role');
  assert.equal(editable.workflow.status,'draft');
  assert.equal(editable.workflow.nodes.find(node=>node.id==='role').executor.provider_id,'native-luna');
  assert.match(editable.workflow.nodes.find(node=>node.id==='role').prompt_template,/supplied bounded implementation/);
  const reopened=await f.service.call('customize_role',{workflow_id:'builtin-role-bounded-code-change'},{human:true});
  assert.equal(reopened.revision_hash,editable.revision_hash,'editing a built-in Role reopens its existing editable copy');
  const listed=await f.service.call('list',{include_legacy:true});
  assert.equal(listed.find(item=>item.id===editable.workflow.id).role_builtin_id,'builtin-role-bounded-code-change');
  let deduplicated=await f.service.call('role_templates');
  assert.equal(deduplicated.filter(item=>item.id==='builtin-role-bounded-code-change').length,1);
  assert.equal(deduplicated.some(item=>item.id===editable.workflow.id),false,'a customization Pack is not exposed as a second Role identity');
  assert.equal(deduplicated.find(item=>item.id==='builtin-role-bounded-code-change').customization.status,'draft');
  const customized=structuredClone(editable.workflow),customizedNode=customized.nodes.find(node=>node.id==='role');
  customizedNode.executor={kind:'provider',provider_id:'native-sol'};customizedNode.prompt_template='Use the customized bounded role exactly once.';
  customized.requirements.providers=['native-sol'];
  const customizedDraft=await f.service.call('save',{workflow_id:customized.id,expected_revision:editable.revision_hash,workflow:customized},{human:true});
  const customizedReady=await f.service.call('publish',{workflow_id:customized.id,expected_revision:customizedDraft.revision_hash,reviewed:true},{human:true});
  deduplicated=await f.service.call('role_templates');
  const effective=deduplicated.find(item=>item.id==='builtin-role-bounded-code-change');
  assert.equal(deduplicated.filter(item=>item.id==='builtin-role-bounded-code-change').length,1);assert.equal(effective.model,'gpt-6.1-sol');assert.equal(effective.customized,true);
  const customizedProfile=await f.service.call('role_template',{workflow_id:'builtin-role-bounded-code-change',revision_hash:effective.revision_hash,task:'Change one parser function.'});
  assert.equal(customizedProfile.id,'builtin-role-bounded-code-change');assert.equal(customizedProfile.source_workflow_id,customizedReady.workflow.id);assert.equal(customizedProfile.provider_id,'native-sol');
  assert.match(customizedProfile.instructions,/customized bounded role exactly once/);
  const role=await f.service.call('build_workflow',{workflow_id:'new-review-role',name:'New review role',brief:'Review the supplied patch and report concrete findings.',template_kind:'role',access:'read_only'});
  assert.equal(role.workflow.template_kind,'role');assert.equal(role.workflow.role_prompt_mode,'append_context');assert.equal(role.provenance.kind,'role_build');
  assert.equal((await f.service.call('read',{workflow_id:role.workflow.id})).validation.errors.length,0);
  await assert.rejects(f.service.call('role_template',{workflow_id:role.workflow.id,task:'Review patch'}),{code:'ROLE_NOT_READY'});
  await assert.rejects(f.service.call('start',{workflow_id:role.workflow.id,workspace:f.workspace,access:'read_only',main_actor:'test',inputs:{task:'Review patch'}}),{code:'ROLE_NOT_RUNNABLE'});
  const published=await f.service.call('publish',{workflow_id:role.workflow.id,expected_revision:role.revision_hash,reviewed:true},{human:true});
  const profile=await f.service.call('role_template',{workflow_id:published.workflow.id,revision_hash:published.revision_hash,task:'Review patch'});
  assert.match(profile.instructions,/Review the supplied patch/);assert.equal(profile.access,'read_only');
  assert.equal((await f.service.call('role_templates')).some(item=>item.id===published.workflow.id),true);
  assert.equal((await f.service.call('route',{task:'Run new-review-role to review the patch.'})).candidates.some(item=>item.id===published.workflow.id),false);
  assert(workflowToolDefinitions().find(item=>item.name==='workflow_build_workflow').inputSchema.properties.template_kind);
});
test('GPT reviewer Role reuses the configured web-review Provider without creating a duplicate Role',async t=>{
  const f=await fixture(t,{configure:config=>{
    const provider=config.providers.find(item=>item.id==='chatgpt-web-pro');
    provider.enabled=true;provider.config.model_label='Configured ChatGPT reviewer';
  }});await f.migrate();
  let catalog=await f.service.call('role_templates');
  let roles=catalog.filter(item=>item.id==='builtin-role-hard-path-web-advice');
  assert.equal(roles.length,1);
  assert.equal(roles[0].name,'GPT reviewer');
  assert.equal(roles[0].provider_id,'chatgpt-web-pro');
  assert.equal(roles[0].provider_kind,'web_review');
  assert.equal(roles[0].provider_enabled,true);
  assert.equal(roles[0].enabled,false);
  assert.equal(roles[0].model,'Configured ChatGPT reviewer');
  const editable=await f.service.call('customize_role',{workflow_id:roles[0].id},{human:true});
  const workflow=structuredClone(editable.workflow);workflow.enabled=true;
  const saved=await f.service.call('save',{workflow_id:workflow.id,expected_revision:editable.revision_hash,workflow},{human:true});
  await f.service.call('publish',{workflow_id:workflow.id,expected_revision:saved.revision_hash},{human:true});
  catalog=await f.service.call('role_templates');roles=catalog.filter(item=>item.id==='builtin-role-hard-path-web-advice');
  assert.equal(roles.length,1);assert.equal(roles[0].enabled,true);
  const profile=await f.service.call('role_template',{workflow_id:roles[0].id,task:'Review the supplied release packet.',context:'One ZIP packet.',constraints:'Read only.',verification:'Check cited evidence.'});
  assert.equal(profile.provider_kind,'web_review');
  assert.equal(profile.adapter.execution,'packet_review');
  assert.equal(profile.adapter.skill,'chatgpt-agent');
  assert.equal(profile.adapter.ambient_repository_access,false);
  assert.equal(profile.agent_type,null);
  assert.match(profile.instructions,/Review the supplied release packet/);
  const built=await f.service.call('build_workflow',{workflow_id:'configured-gpt-reviewer',name:'Configured GPT reviewer',brief:'Review one supplied packet and report evidence-backed findings.',provider_id:'chatgpt-web-pro',template_kind:'role',access:'read_only'});
  assert.equal(built.workflow.nodes.find(node=>node.id==='role').executor.provider_id,'chatgpt-web-pro');
  assert.equal((await f.service.call('read',{workflow_id:built.workflow.id})).validation.errors.length,0);
});
async function persistHostResult(service,run,lease,output,{accepted}={}){
  const {runtime}=await service.open(),record=await runtime.runs.read(run.run_id),definition=record.pins.root.workflow.nodes.find(node=>node.id===lease.node_id);
  const args={run_id:run.run_id,control_token:run.control_token,node_id:lease.node_id,attempt_id:lease.attempt_id,lease_token:lease.lease_token};
  const attempt=record.state.nodes[lease.node_id].attempts.find(item=>item.id===lease.attempt_id);
  if(!attempt.dispatch){
    const request_id=`dispatch-${lease.attempt_id}`;
    await runtime.recordHostMainDispatchIntent(run.run_id,{...args,request_id,envelope_hash:'f'.repeat(64)});
  }
  const refreshed=await runtime.runs.read(run.run_id),request_id=refreshed.state.nodes[lease.node_id].attempts.find(item=>item.id===lease.attempt_id).dispatch.request_id;
  if(!refreshed.state.nodes[lease.node_id].attempts.find(item=>item.id===lease.attempt_id).dispatch.receipt){
    await runtime.recordHostMainDispatchReceipt(run.run_id,{...args,request_id,receipt:{invocation_id:`host-main-${lease.attempt_id}`,executor:'codex-app-server-host-main',executable_sha256:'a'.repeat(64),model:'fixture-main',effort:'medium',main_actor:record.state.main_actor,session_id:`logical-main-${run.run_id}`,call_chain_id:`workflow-run-${run.run_id}`}});
  }
  const final=record.pins.root.workflow.finalization?.node_id===lease.node_id;
  const proposal=hostResultProposalEnvelope(definition,{output,summary:'Host fixture result',artifacts:[],evidence:[{kind:'host_fixture'}],changed_paths:[],outside_paths:[]},{finalAcceptance:final});
  const saved=await runtime.runs.saveExecutorResult(run.run_id,lease.attempt_id,proposal);
  await runtime.recordExecutorEvent(run.run_id,{...args,event:{kind:'result_proposed',metadata:{...saved,final_acceptance_required:final}}});
  if(definition.decision&&output.decision==='blocked')return runtime.failNode(run.run_id,{...args,error:{code:'WORKFLOW_NODE_BLOCKED',message:'Host fixture reported a blocked decision'}});
  if(final&&accepted===false)return runtime.failNode(run.run_id,{...args,error:{code:'FINAL_ACCEPTANCE_REJECTED',message:'Human rejected the final result'}});
  return runtime.completeHostMainResult(run.run_id,args,{...(final?{accepted}: {})});
}
async function completeHostHandoff(service,handoff,output,options={}){
  const run={run_id:handoff.host_binding.run_id,control_token:handoff.host_binding.control_token};
  const state=await persistHostResult(service,run,handoff.host_binding,output,options);
  if(['succeeded','failed','cancelled'].includes(state.status))return {status:state.status,stop_reason:'terminal'};
  const {drive}=await service.open();return drive.advanceToMain(run.run_id,{control_token:run.control_token,owner:handoff.host_binding.owner,request_prefix:`fixture-${run.run_id}`});
}

test('compact main-session service starts, projects one node and completes to the next main node without granular round trips', async t => {
  const f = await fixture(t); await f.migrate();
  assert.equal(workflowToolDefinitions().find(tool => tool.name === 'workflow_begin_main'), undefined);
  assert.equal(workflowToolDefinitions().find(tool => tool.name === 'workflow_complete_main'), undefined);
  const output = { type: 'object', properties: { value: { type: 'string' }, accepted: { type: 'boolean' } }, required: ['value', 'accepted'], additionalProperties: false };
  const decisionOutput = { type: 'object', properties: { value: { type: 'string' }, decision_id: { type: 'string' }, decision: { type: 'string' }, references: { type: 'array', items: { type: 'string' } } }, required: ['value', 'decision_id', 'decision', 'references'], additionalProperties: false };
  const workflow = { ...createDraft('compact-main-fixture', 'Compact main fixture'), status: 'ready', context_projection_version: 2,
    inputs_schema: { type: 'object', properties: { task: { type: 'string' } }, required: ['task'], additionalProperties: false },
    skill_policy: { mode: 'cooperative', implicit: 'allow', ambient_allow: [], shadowed_skill_paths: [] }, finalization: { required: true, node_id: 'final' },
    nodes: [
      { id: 'start', type: 'start' },
      { id: 'work', type: 'agent', executor: { kind: 'main' }, role: 'implementer', access: 'read_only', approval: { required: false }, retry: { max_attempts: 1 }, input_bindings: { task: '/inputs/task' }, prompt_template: 'Do {{task}}', resources: ['workflow/current.md'], outputs_schema: decisionOutput, decision: { id: 'work-disposition', options: ['continue', 'blocked'], required_references: ['workflow/current.md'] } },
      { id: 'final', type: 'agent', executor: { kind: 'main' }, role: 'finalizer', access: 'read_only', approval: { required: false }, retry: { max_attempts: 1 }, input_bindings: { prior: '/nodes/work/output' }, prompt_template: 'Accept the bound prior result.', outputs_schema: output },
      { id: 'end', type: 'end' },
    ], edges: [{ id: 'start-work', source: 'start', target: 'work' }, { id: 'work-final', source: 'work', target: 'final' }, { id: 'final-end', source: 'final', target: 'end' }] };
  const created = await f.service.call('create', { workflow, resources: { 'workflow/current.md': 'node-scoped' } });
  const first = await f.service.call('begin_main', { workflow_id: workflow.id, revision_hash: created.revision_hash, workspace: f.workspace, access: 'read_only', main_actor: 'root', inputs: { task: 'one thing' }, constraints: { network: false } });
  assert.equal(first.stop_reason, 'main_node'); assert.equal(first.host_binding.node_id, 'work'); assert.deepEqual(first.agent_packet.resources, [{ path: 'workflow/current.md' }]);
  assert.equal(first.agent_packet.response_form.schema.properties.decision_id, undefined);
  assert.deepEqual(first.agent_packet.response_form.decision.options, ['continue', 'blocked']);
  assert.equal(Object.hasOwn(first.agent_packet, 'run_id'), false);
  assert.match(first.agent_packet.prompt, /read_workflow_resource/);
  assert.doesNotMatch(first.agent_packet.prompt, /agent_packet\.resources/);
  assert.doesNotMatch(first.agent_packet.prompt, /Perform a bounded implementation task/,'Workflow nodes do not implicitly inject a catalog Role prompt');
  const second = await completeHostHandoff(f.service,first,{ value: 'done', decision: 'continue' });
  assert.equal(second.stop_reason, 'main_node'); assert.equal(second.host_binding.node_id, 'final'); assert.deepEqual(second.agent_packet.resources, []);
  assert.doesNotMatch(second.agent_packet.prompt, /"decision_id"/);
  assert.doesNotMatch(second.agent_packet.prompt, /"references"/);
  assert.equal(second.agent_packet.response_form.acceptance, null);
  assert.deepEqual(second.agent_packet.response_form.schema.properties.accepted, { type: 'boolean' });
  assert.deepEqual(second.agent_packet.response_form.schema.required, ['value', 'accepted']);
  const terminal = await completeHostHandoff(f.service,second,{ value: 'accepted' },{ accepted: true });
  assert.equal(terminal.stop_reason, 'terminal'); assert.equal(terminal.status, 'succeeded');
});

test('service exposes both authoring Workflows and installs an exported package from HTTPS', async t => {
  const source=await fixture(t);await source.migrate();
  const definitions=await source.service.call('authoring_workflows');
  assert.deepEqual(definitions.map(item=>item.id),['system.skill2workflow','system.build-workflow']);
  const library=await source.service.call('list');
  assert.deepEqual(library.filter(item=>item.id.startsWith('system.')).map(item=>item.id),['system.build-workflow','system.skill2workflow']);
  for(const definition of definitions){
    assert.match(definition.revision_hash,/^[a-f0-9]{64}$/);assert.equal(definition.status,'ready');
    const stored=await source.service.call('read',{workflow_id:definition.id,revision_hash:definition.revision_hash});
    assert.equal(stored.provenance.kind,'bundled_authoring_workflow');assert.equal(stored.workflow.authoring.contract,'codex-authoring-workflow/v30');
    assert.equal(stored.workflow.nodes.find(node=>node.id==='expand').prompt_template,AUTHORING_PLANNER_PROMPT_V27);
    assert.equal(stored.workflow.nodes.find(node=>node.id==='final').prompt_template,AUTHORING_REVIEW_PROMPT_V22);
    assert.equal(stored.workflow.authoring.pipeline.contract,'codex-authoring-pipeline/v1');
  }
  assert(definitions.every(item=>item.mechanical_repairs===0 && item.semantic_repairs===3));
  assert(definitions.every(item=>item.contract==='codex-authoring-workflow/v30'));
  assert(definitions.every(item=>item.stages.map(stage=>stage.owner).join(',')==='host,planner,host,host,host,reviewer,human'));
  assert(definitions.every(item=>item.edges.map(edge=>`${edge.source}>${edge.target}`).join(',')==='start>expand,expand>graph_assembly,graph_assembly>execution_binding,execution_binding>deterministic_validation,deterministic_validation>final,final>end'));
  assert(definitions.every(item=>item.pipeline.repair.mode==='stable_key_delta'&&item.pipeline.repair.automatic_rounds===3));
  assert(definitions.every(item=>item.configurable_slots.includes('planner_provider_id')&&item.configurable_slots.includes('review_provider_id')));
  await assert.rejects(source.service.call('delete',{workflow_id:definitions[0].id,expected_revision:definitions[0].revision_hash},{model:true}),{code:'WORKFLOW_SYSTEM_MANAGED'});
  const built=await source.service.call('build_workflow',{workflow_id:'service-built',name:'Service built',brief:'# Workflow\n\n## Check\n\nInspect the change and report evidence.'});
  assert.equal(built.provenance.source_kind,'brief');assert.equal(built.workflow.import_status.mode,'authored');
  assert.equal(built.workflow.template_kind,'workflow');
  const preview=await source.service.call('authoring_prompt_preview',{workflow_id:built.workflow.id,revision_hash:built.revision_hash},{human:true});
  assert.deepEqual(preview.authoring_pipeline.stages.map(stage=>stage.id),['start','expand','graph_assembly','execution_binding','deterministic_validation','final','end']);
  const plannerResources=preview.model_resource_paths.find(node=>node.node_id==='expand').paths;
  const reviewerResources=preview.model_resource_paths.find(node=>node.node_id==='final').paths;
  assert(plannerResources.includes('analysis/request.txt')&&!plannerResources.includes('analysis/review-request.txt')&&!plannerResources.includes('source/WORKFLOW.md'));
  assert(reviewerResources.includes('analysis/review-request.txt')&&!reviewerResources.includes('analysis/request.txt')&&!reviewerResources.includes('source/WORKFLOW.md'));
  await assert.rejects(source.service.call('export_workflow_package',{workflow_id:built.workflow.id,revision_hash:built.revision_hash,package_version:'2.1.0'}),{code:'WORKFLOW_PACKAGE_AUTHORING_PRIVATE'});
  const output={type:'object',properties:{result:{type:'string'}},required:['result'],additionalProperties:false};
  const portable={...createDraft('service-portable','Service portable'),status:'ready',inputs_schema:{type:'object',properties:{task:{type:'string'}},required:['task'],additionalProperties:false},
    finalization:{required:true,node_id:'final'},nodes:[{id:'start',type:'start'},{id:'final',type:'agent',executor:{kind:'main'},role:'finalizer',access:'read_only',approval:{required:false},retry:{max_attempts:1},input_bindings:{task:'/inputs/task'},prompt_template:'Return the task result.',outputs_schema:output},{id:'end',type:'end'}],
    edges:[{id:'start-final',source:'start',target:'final'},{id:'final-end',source:'final',target:'end'}]};
  const portablePack=await source.service.call('create',{workflow:portable},{human:true});
  const bundle=await source.service.call('export_workflow_package',{workflow_id:portable.id,revision_hash:portablePack.revision_hash,package_version:'2.1.0'});
  const bytes=Buffer.from(JSON.stringify(bundle));
  const target=await fixture(t,{fetchImpl:async(url,options)=>{assert.equal(String(url),'https://example.invalid/service-built.workflow.json');assert.equal(options.redirect,'error');return new Response(bytes,{status:200,headers:{'content-type':'application/json'}});}});await target.migrate();
  const installed=await target.service.call('install_workflow_package',{source_url:'https://example.invalid/service-built.workflow.json'},{model:true});
  assert.equal(installed.workflow.id,'service-portable');assert.equal(installed.installation.source,'https://example.invalid/service-built.workflow.json');
  assert.equal(installed.revision_hash,portablePack.revision_hash);

  const relativeTarget=await fixture(t);await relativeTarget.migrate();
  const relativePackage=join(relativeTarget.workspace,'portable.workflow-package.json');await writeFile(relativePackage,bytes);
  const relativeRpc=await handleRpc({jsonrpc:'2.0',id:1,method:'tools/call',params:{name:'workflow_install_workflow_package',arguments:{package_path:'portable.workflow-package.json',workspace:relativeTarget.workspace}}},{configPath:relativeTarget.configPath,defaultConfigPath:DEFAULT_CONFIG_PATH,env:{}});
  assert.equal(relativeRpc.result.isError,undefined,JSON.stringify(relativeRpc));
  const relativeInstalled=JSON.parse(relativeRpc.result.content[0].text);
  assert.equal(relativeInstalled.revision_hash,portablePack.revision_hash);assert.equal(relativeInstalled.installation.source,relativePackage);
  const absoluteTarget=await fixture(t);await absoluteTarget.migrate();
  const absolutePackage=join(absoluteTarget.workspace,'portable.workflow-package.json');await writeFile(absolutePackage,bytes);
  const absoluteInstalled=await absoluteTarget.service.call('install_workflow_package',{package_path:absolutePackage},{model:true});
  assert.equal(absoluteInstalled.revision_hash,portablePack.revision_hash);assert.equal(absoluteInstalled.installation.source,absolutePackage);
  const missingWorkspaceTarget=await fixture(t);await missingWorkspaceTarget.migrate();
  await assert.rejects(missingWorkspaceTarget.service.call('install_workflow_package',{package_path:'relative.json'},{model:true}),{code:'WORKFLOW_PACKAGE_WORKSPACE'});

  const childWorkflow=structuredClone(portable);childWorkflow.id='package-child';childWorkflow.name='Package child';
  const childV1=await source.service.call('create',{workflow:childWorkflow},{human:true});
  const childEdit=structuredClone(childV1.workflow);childEdit.description='Second immutable child revision.';
  const child=await source.service.call('save',{workflow_id:childEdit.id,workflow:childEdit,expected_revision:childV1.revision_hash},{human:true});
  const parent=structuredClone(portable);parent.id='package-parent';parent.name='Package parent';
  const call={id:'call',type:'subworkflow',executor:{kind:'subworkflow'},role:'advisor',access:'read_only',prompt_template:'Run the pinned child.',approval:{required:false},retry:{max_attempts:1},input_bindings:{task:'/inputs/task'},
    subworkflow:{workflow_id:child.workflow.id,revision_pin:child.revision_hash,output_bindings:{result:'/output'}}};
  const final=structuredClone(parent.nodes.find(node=>node.id==='final'));parent.nodes=[{id:'start',type:'start'},call,final,{id:'end',type:'end'}];
  parent.edges=[['start','call'],['call','final'],['final','end']].map(([sourceId,targetId])=>({id:`${sourceId}-${targetId}`,source:sourceId,target:targetId}));
  const parentPack=await source.service.call('create',{workflow:parent},{human:true});
  const childBundle=await source.service.call('export_workflow_package',{workflow_id:child.workflow.id,revision_hash:child.revision_hash,package_version:'1.0.0'});
  const parentBundle=await source.service.call('export_workflow_package',{workflow_id:parent.id,revision_hash:parentPack.revision_hash,package_version:'1.0.0'});
  const installedChild=await target.service.call('install_workflow_package',{package:childBundle},{human:true});
  const installedParent=await target.service.call('install_workflow_package',{package:parentBundle},{human:true});
  assert.equal(installedChild.revision_hash,child.revision_hash);assert.equal(installedChild.workflow.revision,2);
  assert.equal(installedParent.workflow.id,parent.id);
  assert.equal((await target.service.call('read',{workflow_id:child.workflow.id,revision_hash:child.revision_hash})).revision_hash,child.revision_hash);
});

test('stored authoring configuration is pinned into ordinary starts while unrelated Draft or disabled system entries remain listable',async t=>{
  const f=await fixture(t,{capabilities:{strictManager:{capability:async()=>true}}});await f.migrate();await f.service.call('authoring_workflows');
  const source=await f.service.call('build_workflow',{workflow_id:'stored-authoring-source',name:'Stored authoring source',brief:'# Workflow\n\n## Task\n\nProduce one reviewed result.'});
  const template=await f.service.call('read',{workflow_id:'system.build-workflow'}),edited=structuredClone(template.workflow);
  const planner=edited.nodes.find(node=>node.id==='expand'),reviewer=edited.nodes.find(node=>node.id==='final');
  planner.prompt_template='Use the saved planner prompt and return only the semantic plan.';planner.approval.required=true;
  reviewer.prompt_template='Use the saved reviewer prompt and report every material semantic issue.';reviewer.approval.required=true;
  const saved=await f.service.call('save',{workflow_id:edited.id,expected_revision:template.revision_hash,workflow:edited},{human:true});
  const unsupported=structuredClone(saved.workflow);unsupported.edges[0].target='final';
  await assert.rejects(f.service.call('save',{workflow_id:unsupported.id,expected_revision:saved.revision_hash,workflow:unsupported},{human:true}),{code:'AUTHORING_WORKFLOW_CONTRACT'});
  const run=await f.service.call('start',{workflow_id:saved.workflow.id,revision_hash:saved.revision_hash,run_id:'stored-authoring-start',workspace:f.workspace,access:'read_only',main_actor:'root',inputs:{source_workflow_id:source.workflow.id,source_revision:source.revision_hash}},{human:true});
  const record=await (await f.service.open()).runtime.runs.read(run.run_id),pinned=record.pins.root.workflow;
  assert.equal(record.pins.root.provenance.kind,'authoring_workflow_run');assert.equal(record.pins.root.provenance.authoring_workflow_revision,saved.revision_hash);
  assert.equal(pinned.nodes.find(node=>node.id==='expand').prompt_template,planner.prompt_template);assert.equal(pinned.nodes.find(node=>node.id==='expand').approval.required,true);
  assert.equal(pinned.nodes.find(node=>node.id==='final').prompt_template,reviewer.prompt_template);assert.equal(pinned.nodes.find(node=>node.id==='final').approval.required,true);

  const sibling=await f.service.call('read',{workflow_id:'system.skill2workflow'}),draft={...sibling.workflow,status:'draft'};
  const draftSaved=await f.service.call('save',{workflow_id:draft.id,expected_revision:sibling.revision_hash,workflow:draft});
  assert((await f.service.call('list')).some(item=>item.id===draft.id && item.status==='draft'));
  const disabled={...draftSaved.workflow,status:'ready',enabled:false};await f.service.call('save',{workflow_id:disabled.id,expected_revision:draftSaved.revision_hash,workflow:disabled});
  const listed=await f.service.call('list');assert(listed.some(item=>item.id===disabled.id && item.enabled===false));assert(listed.some(item=>item.id===saved.workflow.id));
});

test('converted Workflow edits refresh content hashes at direct publication',async t=>{
  const f=await fixture(t);await f.migrate();
  const origin={kind:'converted',reviewed:true,evidence_ids:['section_001']};
  const output={type:'object',properties:{result:{type:'string'}},required:['result'],additionalProperties:false};
  const source_hash=digest('Certified source.');
  const workflow={...createDraft('certificate-review-flow','Certificate review flow'),skill_policy:{mode:'cooperative',implicit:'deny',ambient_allow:[],shadowed_skill_paths:[]},
    import_status:{mode:'ai_expanded',source_hash,source_independent:true,unresolved:[],conversion_level:'fully_compiled',conversion_contract_version:3,requirement_coverage:[],source_dispositions:[]},
    finalization:{required:true,node_id:'final'},nodes:[
      {id:'start',type:'start'},
      {id:'work',type:'agent',executor:{kind:'main'},role:'implementer',access:'read_only',approval:{required:false},retry:{max_attempts:1},input_bindings:{task:'/inputs/task'},prompt_template:'Perform the certified work.',outputs_schema:output,origin:structuredClone(origin)},
      {id:'final',type:'agent',executor:{kind:'main'},role:'finalizer',access:'read_only',approval:{required:false},retry:{max_attempts:1},input_bindings:{result:'/nodes/work/output/result'},prompt_template:'Accept the certified result.',outputs_schema:output,origin:structuredClone(origin)},
      {id:'end',type:'end'},
    ],edges:[['start-work','start','work'],['work-final','work','final'],['final-end','final','end']].map(([id,source,target])=>({id,source,target,origin:structuredClone(origin)}))};
  const resources={},identity={source_revision:'a'.repeat(64),source_hash,proposal_hash:'b'.repeat(64),review_contract_version:CONVERSION_CONTRACT.version};
  const certificate=createConversionCertificate(workflow,resources,identity),import_report={mode:'converted',expansion:{...identity,status:'draft',conversion_level:'fully_compiled',requirement_coverage:[],source_dispositions:[],inferred_nodes:2,inferred_edges:3,certificate}};
  const provenance={kind:'workflow_conversion',compiler_version:5,source_kind:'skill',source_hash,conversion:{source_revision:identity.source_revision,proposal_hash:identity.proposal_hash,review_contract_version:identity.review_contract_version}};
  const created=await f.service.call('create',{workflow,resources,provenance,import_report});
  assert.equal((await f.service.call('list')).find(item=>item.id===workflow.id)?.import_mode,'ai_expanded');
  const metadataOnly=structuredClone(created.workflow);metadataOnly.nodes.find(node=>node.id==='work').origin.review={actor:'user',note:'Presentation-only audit note'};
  const reviewed=await f.service.call('save',{workflow_id:workflow.id,workflow:metadataOnly,expected_revision:created.revision_hash});
  const published=await f.service.call('publish',{workflow_id:workflow.id,expected_revision:reviewed.revision_hash,reviewed:true},{human:true});assert.equal(published.workflow.status,'ready');
  const changed=structuredClone(published.workflow);changed.status='draft';changed.nodes.find(node=>node.id==='work').executor={kind:'provider',provider_id:'native-luna'};
  const saved=await f.service.call('save',{workflow_id:workflow.id,workflow:changed,expected_revision:published.revision_hash});
  const republished=await f.service.call('publish',{workflow_id:workflow.id,expected_revision:saved.revision_hash});
  assert.equal(republished.workflow.status,'ready');
  assert.equal(republished.workflow.nodes.find(node=>node.id==='work').executor.provider_id,'native-luna');
  assert.notEqual(republished.import_report.expansion.certificate.workflow_hash,published.import_report.expansion.certificate.workflow_hash);
  assert.doesNotThrow(()=>requireCurrentConversionCertificate(republished.workflow,republished.resources,republished.import_report,{required:true}));

  const reassigned=structuredClone(republished.workflow);reassigned.status='draft';
  reassigned.import_status.source_dispositions=[{section_id:'section_001',disposition:'workflow',node_ids:['work'],requirement_ids:[],rationale:'The edited graph assigns this source section to the retained work node.'}];
  const reassignedDraft=await f.service.call('save',{workflow_id:workflow.id,workflow:reassigned,expected_revision:republished.revision_hash});
  const reassignedPublished=await f.service.call('publish',{workflow_id:workflow.id,expected_revision:reassignedDraft.revision_hash});
  assert.deepEqual(reassignedPublished.import_report.expansion.source_dispositions,reassignedPublished.workflow.import_status.source_dispositions);
  assert.doesNotThrow(()=>requireCurrentConversionCertificate(reassignedPublished.workflow,reassignedPublished.resources,reassignedPublished.import_report,{required:true}));

  const resourceEdit=await f.service.call('write_resource',{workflow_id:workflow.id,expected_revision:reassignedPublished.revision_hash,
    resource_path:'workflow-assets/reviewed.txt',text:'Workflow-owned resource changed after conversion.'});
  assert.equal(resourceEdit.workflow.import_status.source_independent,true);
  assert.equal(resourceEdit.workflow.import_status.unresolved.some(item=>item.code==='RESOURCE_EDIT_REQUIRES_REVIEW'),false);
  const resourceReviewed=await f.service.call('publish',{workflow_id:workflow.id,expected_revision:resourceEdit.revision_hash,
    reviewed:true},{human:true});
  assert.equal(resourceReviewed.workflow.status,'ready');
  assert.equal(resourceReviewed.workflow.import_status.unresolved.some(item=>item.code==='RESOURCE_EDIT_REQUIRES_REVIEW'),false);
  assert.notEqual(resourceReviewed.import_report.expansion.certificate.resources_hash,republished.import_report.expansion.certificate.resources_hash);
  assert.doesNotThrow(()=>requireCurrentConversionCertificate(resourceReviewed.workflow,resourceReviewed.resources,
    resourceReviewed.import_report,{required:true}));

  const forgedCopy=await f.service.call('duplicate',{workflow_id:workflow.id,new_id:'certificate-forged-status',name:'Certificate forged status',revision_hash:published.revision_hash});
  const forgedStatus=structuredClone(forgedCopy.workflow);forgedStatus.status='draft';forgedStatus.import_status.conversion_level='unsupported';
  const forgedDraft=await f.service.call('save',{workflow_id:forgedStatus.id,workflow:forgedStatus,expected_revision:forgedCopy.revision_hash});
  await assert.rejects(f.service.call('publish',{workflow_id:forgedStatus.id,expected_revision:forgedDraft.revision_hash,reviewed:true},{human:true}),{code:'CONVERSION_IDENTITY_REQUIRED'});

  const downgrades=[
    {suffix:'coarse',mutate:item=>{item.import_status.mode='coarse';},extra:{}},
    {suffix:'authored',mutate:item=>{item.import_status.mode='authored';},extra:{}},
    {suffix:'removed',mutate:item=>{delete item.import_status;},extra:{import_report:{}}},
  ];
  for(const candidate of downgrades){
    const copy=await f.service.call('duplicate',{workflow_id:workflow.id,new_id:`certificate-${candidate.suffix}`,name:`Certificate ${candidate.suffix}`,revision_hash:published.revision_hash});
    const edited=structuredClone(copy.workflow);edited.status='draft';edited.nodes.find(node=>node.id==='work').prompt_template='Changed while trying to erase conversion identity.';candidate.mutate(edited);
    await assert.rejects(f.service.call('save',{workflow_id:edited.id,workflow:edited,expected_revision:copy.revision_hash,...candidate.extra}),
      {code:candidate.suffix==='removed'?'WORKFLOW_EDITOR_METADATA':'CONVERSION_IDENTITY_REQUIRED'});
  }
});

test('ordinary editor save cannot erase or replace private authoring identity',async t=>{
  const f=await fixture(t);await f.migrate();
  const built=await f.service.call('build_workflow',{workflow_id:'private-editor-seed',name:'Private editor seed',brief:'# Workflow\n\n## Task\n\nProduce one result.'});
  const erased=structuredClone(built.workflow);delete erased.import_status;
  await assert.rejects(f.service.call('save',{workflow_id:erased.id,workflow:erased,expected_revision:built.revision_hash}),{code:'CONVERSION_IDENTITY_REQUIRED'});
  await assert.rejects(f.service.call('save',{workflow_id:built.workflow.id,workflow:built.workflow,expected_revision:built.revision_hash,provenance:{kind:'workflow_authored'}}),{code:'WORKFLOW_EDITOR_METADATA'});
  assert.equal((await f.service.call('read',{workflow_id:built.workflow.id})).provenance.kind,'workflow_build');
});

test('every Ready persistence path rejects node resources absent from the actual Pack manifest',async t=>{
  const f=await fixture(t);await f.migrate();
  const output={type:'object',properties:{value:{type:'string'}},required:['value'],additionalProperties:false};
  const workflow={...createDraft('ready-resource-closure','Ready resource closure'),status:'ready',inputs_schema:{type:'object',properties:{task:{type:'string'}},required:['task'],additionalProperties:false},skill_policy:{mode:'cooperative',implicit:'allow',ambient_allow:[],shadowed_skill_paths:[]},finalization:{required:true,node_id:'final'},nodes:[
    {id:'start',type:'start'},
    {id:'final',type:'agent',executor:{kind:'main'},role:'finalizer',access:'read_only',approval:{required:false},retry:{max_attempts:1},input_bindings:{task:'/inputs/task'},prompt_template:'Read the required resource.',resources:['missing.md'],outputs_schema:output},
    {id:'end',type:'end'},
  ],edges:[{id:'start-final',source:'start',target:'final'},{id:'final-end',source:'final',target:'end'}]};
  await assert.rejects(f.service.call('create',{workflow,resources:{}},{human:true}),{code:'WORKFLOW_RESOURCE_MISSING'});
  const draft=await f.service.call('create',{workflow:{...workflow,status:'draft'},resources:{}});
  await assert.rejects(f.service.call('save',{workflow_id:workflow.id,workflow,expected_revision:draft.revision_hash},{human:true}),{code:'WORKFLOW_RESOURCE_MISSING'});
});

test('compact blocked decisions and final rejection fail durably instead of advancing downstream', async t => {
  const f = await fixture(t); await f.migrate();
  const base = { ...createDraft('compact-durable', 'Compact durable result'), status: 'ready', context_projection_version: 2,
    inputs_schema: { type: 'object', properties: { task: { type: 'string' } }, required: ['task'], additionalProperties: false }, skill_policy: { mode: 'cooperative', implicit: 'allow', ambient_allow: [], shadowed_skill_paths: [] } };
  const decisionOutput = { type: 'object', properties: { value: { type: 'string' }, decision_id: { type: 'string' }, decision: { type: 'string' }, references: { type: 'array', items: { type: 'string' } } }, required: ['value', 'decision_id', 'decision', 'references'], additionalProperties: false };
  const blocked = { ...base, id: 'compact-blocked', finalization: { required: true, node_id: 'final' }, nodes: [
    { id: 'start', type: 'start' },
    { id: 'work', type: 'agent', executor: { kind: 'main' }, role: 'implementer', access: 'read_only', approval: { required: false }, retry: { max_attempts: 1 }, input_bindings: { task: '/inputs/task' }, prompt_template: 'Work', outputs_schema: decisionOutput, decision: { id: 'disposition', options: ['continue', 'blocked'], required_references: [] } },
    { id: 'final', type: 'agent', executor: { kind: 'main' }, role: 'finalizer', access: 'read_only', approval: { required: false }, retry: { max_attempts: 1 }, input_bindings: { prior: '/nodes/work/output' }, prompt_template: 'Final', outputs_schema: { type: 'object', properties: { ok: { type: 'boolean' } }, required: ['ok'], additionalProperties: false } }, { id: 'end', type: 'end' }],
    edges: [{ id: 'start-work', source: 'start', target: 'work' }, { id: 'work-final', source: 'work', target: 'final' }, { id: 'final-end', source: 'final', target: 'end' }] };
  const blockedCreated = await f.service.call('create', { workflow: blocked }, {human:true});
  const blockedStart = await f.service.call('begin_main', { workflow_id: blocked.id, revision_hash: blockedCreated.revision_hash, workspace: f.workspace, access: 'read_only', main_actor: 'root', inputs: { task: 'one' } });
  const blockedTerminal = await completeHostHandoff(f.service,blockedStart,{ value: 'cannot continue', decision: 'blocked' });
  assert.equal(blockedTerminal.status, 'failed'); assert.equal(blockedTerminal.stop_reason, 'terminal');
  assert.equal((await f.service.call('get', control(blockedStart.host_binding))).nodes.work.error.code, 'WORKFLOW_NODE_BLOCKED');

  const rejected = { ...base, id: 'compact-rejected', finalization: { required: true, node_id: 'final' }, nodes: [{ id: 'start', type: 'start' }, { id: 'final', type: 'agent', executor: { kind: 'main' }, role: 'finalizer', access: 'read_only', approval: { required: false }, retry: { max_attempts: 1 }, input_bindings: { task: '/inputs/task' }, prompt_template: 'Final', outputs_schema: { type: 'object', properties: { value: { type: 'string' } }, required: ['value'], additionalProperties: false } }, { id: 'end', type: 'end' }], edges: [{ id: 'start-final', source: 'start', target: 'final' }, { id: 'final-end', source: 'final', target: 'end' }] };
  const rejectedCreated = await f.service.call('create', { workflow: rejected }, {human:true});
  const rejectedStart = await f.service.call('begin_main', { workflow_id: rejected.id, revision_hash: rejectedCreated.revision_hash, workspace: f.workspace, access: 'read_only', main_actor: 'root', inputs: { task: 'one' } });
  const rejectedTerminal = await completeHostHandoff(f.service,rejectedStart,{ value: 'rejected' },{ accepted: false });
  assert.equal(rejectedTerminal.status, 'failed'); assert.equal((await f.service.call('get', control(rejectedStart.host_binding))).nodes.final.error.code, 'FINAL_ACCEPTANCE_REJECTED');
});

test('task launch grants project writes without manual allowlists and exposes the task directory', async t => {
  const f=await fixture(t);await f.migrate();
  const args={workflow_id:'bounded-code-change',launch_mode:'task',main_actor:'human-console',inputs:{task:'Write a result'}};
  await assert.rejects(f.service.call('start',args),{code:'HUMAN_TASK_LAUNCH'});
  const run=await f.service.call('start',args,{human:true});
  const state=await f.service.call('get',control(run));
  assert.equal(state.permissions.access,'bounded_write');
  assert.deepEqual(state.permissions.allowed_paths,['.']);
  assert.equal(state.permissions.workspace,state.constraints.task_workspace);
  assert.equal(state.constraints.task_workspace,join(f.root,'workflow-workspaces','run-'+run.run_id));
  const lease=await f.service.call('claim_node',{...control(run),node_id:'implementation',owner:'worker',request_id:'claim-write'});
  assert.equal(lease.access,'bounded_write');
  assert.equal(lease.workspace,state.constraints.task_workspace);
  assert.doesNotMatch(lease.prompt_template,/Output workspace|Rebase other task-output/);
  const explicit=await f.service.call('start',{...args,workspace:f.workspace},{human:true});
  assert.deepEqual((await f.service.call('get',control(explicit))).permissions.allowed_paths,['.']);
});

test('human launch prepares an isolated workspace without expanding access', async t => {
  const f=await fixture(t);await f.migrate();
  const args={workflow_id:'brainstorm',main_actor:'human-console',inputs:{task:'Synthetic task',context:'Fixture only'}};
  const run=await f.service.call('start',args,{human:true});
  const state=await f.service.call('get',control(run));
  assert.equal(state.permissions.workspace,join(f.root,'workflow-workspaces','run-'+run.run_id));
  assert.equal(state.permissions.access,'read_only');
  assert.deepEqual(state.permissions.allowed_paths,[]);
  await assert.rejects(f.service.call('start',{...args,run_id:'../escape'},{human:true}));
});
const claim = async (f, run, node = 'implementation') => {
  const {runtime}=await f.service.open(),record=await runtime.runs.read(run.run_id),args={...control(run),node_id:node,owner:node==='final-acceptance'?'root':'worker',request_id:'claim-'+node};
  return record.pins.root.workflow.nodes.find(item=>item.id===node)?.executor?.kind==='main'
    ? runtime.claimHostMain(run.run_id,args)
    : f.service.call('claim_node',args);
};
const leaseArgs = (run, lease) => ({ ...control(run), node_id: lease.node_id, attempt_id: lease.attempt_id, lease_token: lease.lease_token });
const completion = output => ({ status: 'succeeded', summary: 'Synthetic verification', structured_output: output, artifacts: [], evidence: [{ check: 'fixture', passed: true }], changed_paths: [], outside_paths: [] });

test('Run cancellation aborts an active host broker, journals its termination receipt, and fences old completion', async t => {
  const identity = { name: 'cancel-fixture-tool', version: '1', sha256: 'a'.repeat(64) };
  const contract = { id: 'cancel-fixture-tool', identity, argv: ['cancel-fixture-tool'], input_schema: { type: 'object', properties: { value: { type: 'integer' } }, required: ['value'], additionalProperties: false }, output_schema: { type: 'object', properties: { value: { type: 'integer' } }, required: ['value'], additionalProperties: false }, env_allow: [], permissions: { network: false, read_paths: [], write_paths: [] }, output_cap_bytes: 1024, deadline_ms: 10000, idempotency: { mode: 'safe' } };
  let started; const entered = new Promise(resolve => { started = resolve; }); let aborted = false; let cancels = 0;
  const f = await fixture(t, { capabilities: { hostToolRegistry: { [contract.id]: {
    identity, attestation: { qualified: true, cancellable: true, effect_observation: true, tool_identity: identity, broker_id: 'cancel-fixture-broker', evidence_sha256: 'b'.repeat(64) },
    execute: async ({ signal }) => { started(); return new Promise(resolve => signal.addEventListener('abort', () => { aborted = true; resolve({ exit_code: 143, diagnostic: 'cancelled', effects: { observed: true, changed_paths: [], outside_paths: [], artifacts: [] }, output: null }); }, { once: true })); },
    cancel: async () => { cancels++; return { termination_confirmed: true, evidence: [{ kind: 'fixture-process-exit', sha256: 'c'.repeat(64) }], effects: { observed: true, changed_paths: [], outside_paths: [], artifacts: [] } }; },
  } } } });
  await f.migrate(); const workflow = { ...createDraft('host-cancel', 'Host cancellation'), status: 'ready', skill_policy: { mode: 'cooperative', implicit: 'allow', ambient_allow: [], shadowed_skill_paths: [] }, host_tools: [contract], inputs_schema: { type: 'object', properties: { task: { type: 'string' }, value: { type: 'integer' } }, required: ['task', 'value'], additionalProperties: false }, finalization: { required: true, node_id: 'final' }, nodes: [
    { id: 'start', type: 'start' }, { id: 'tool', type: 'tool', executor: { kind: 'tool', tool: contract.id }, access: 'read_only', approval: { required: false }, retry: { max_attempts: 1 }, input_bindings: { value: '/inputs/value' }, outputs_schema: contract.output_schema },
    { id: 'final', type: 'agent', executor: { kind: 'main' }, role: 'finalizer', access: 'read_only', approval: { required: false }, retry: { max_attempts: 1 }, input_bindings: { task: '/inputs/task', result: '/nodes/tool/output' }, prompt_template: '{{task}}', outputs_schema: { type: 'object' } }, { id: 'end', type: 'end' },
  ], edges: [{ id: 'start-tool', source: 'start', target: 'tool' }, { id: 'tool-final', source: 'tool', target: 'final' }, { id: 'final-end', source: 'final', target: 'end' }] };
  const created = await f.service.call('create', { workflow }, {human:true}); const run = await f.service.call('start', { workflow_id: created.workflow.id, revision_hash: created.revision_hash, workspace: f.workspace, access: 'read_only', main_actor: 'root', inputs: { task: 'fixture', value: 1 } }); const lease = await f.service.call('claim_node', { ...control(run), node_id: 'tool', owner: 'worker', request_id: 'claim-tool' }); const args = { ...control(run), node_id: 'tool', attempt_id: lease.attempt_id, lease_token: lease.lease_token };
  const dispatch = f.service.call('dispatch', args); await entered;
  const cancellationService = new WorkflowService({ configPath: f.configPath, defaultConfigPath: DEFAULT_CONFIG_PATH, capabilities: f.service.capabilities });
  assert.equal(cancellationService.attemptAdmission, f.service.attemptAdmission);
  const cancelled = await cancellationService.call('cancel', control(run)); const settled = await dispatch;
  assert.equal(cancelled.status, 'cancelled'); assert.equal(settled.status, 'cancelled'); assert.equal(aborted, true); assert.equal(cancels, 1); const state = await f.service.call('get', control(run)); assert.equal(state.nodes.tool.attempts[0].host_tool.receipt.status, 'cancelled');
  await assert.rejects(f.service.call('complete_node', { ...args, completion: completion({ value: 1 }) }), { code: 'STALE_LEASE' });
});

test('WorkflowDrive executes a Run-pinned resource tool and journals its output without a semantic merge turn',async t=>{
  const f=await fixture(t,{env:process.env});await f.migrate();
  const path='workflow-assets/scripts/join.mjs';
  const source='import { writeFileSync } from "node:fs"; writeFileSync("work/joined.json", "{\\"joined\\":true}"); console.log(JSON.stringify({joined:true}));\n';
  const output={type:'object',properties:{joined:{type:'boolean'}},required:['joined'],additionalProperties:false};
  const contract={id:'pinned-host-join-tool',identity:workflowResourceProgramIdentity(),argv:['node',path,'work/.workflow-runtime'],
    input_schema:{type:'object',additionalProperties:false},output_schema:output,env_allow:[],
    permissions:{network:false,read_paths:[path],write_paths:['work']},output_cap_bytes:4096,deadline_ms:30000,idempotency:{mode:'safe'}};
  const workflow={...createDraft('pinned-host-join','Pinned Host join'),status:'ready',
    requirements:{providers:[],tools:[],mcp_servers:[],executables:['node']},
    skill_policy:{mode:'cooperative',implicit:'deny',ambient_allow:[],shadowed_skill_paths:[]},host_tools:[contract],
    inputs_schema:{type:'object',properties:{task:{type:'string'}},required:['task'],additionalProperties:false},
    finalization:{required:true,node_id:'final'},nodes:[{id:'start',type:'start'},
      {id:'join',type:'tool',executor:{kind:'tool',tool:contract.id},access:'bounded_write',path_scope:{binding:'run.allowed_paths'},
        approval:{required:false},retry:{max_attempts:1},resources:[path],input_bindings:{},outputs_schema:output},
      {id:'final',type:'agent',role:'finalizer',executor:{kind:'main'},access:'read_only',approval:{required:false},retry:{max_attempts:1},
        input_bindings:{task:'/inputs/task',joined:'/nodes/join/output'},prompt_template:'Report result.'},{id:'end',type:'end'}],
    edges:[{id:'start-join',source:'start',target:'join'},{id:'join-final',source:'join',target:'final'},{id:'final-end',source:'final',target:'end'}]};
  const created=await f.service.call('create',{workflow,resources:{[path]:source}},{human:true});
  const run=await f.service.call('start',{workflow_id:workflow.id,revision_hash:created.revision_hash,workspace:f.workspace,
    access:'bounded_write',allowed_paths:['work'],main_actor:'root',inputs:{task:'Join'},environment_directories:[dirname(process.execPath)]});
  await mkdir(join(f.workspace,'work'));
  const progress=await f.service.call('drive',control(run));
  assert.equal(progress.stop_reason,'semantic_node');
  const state=await f.service.call('get',control(run));
  assert.equal(state.nodes.join.status,'succeeded');
  assert.deepEqual(state.nodes.join.output,{joined:true});
  assert.equal(state.cost_ledger.calls.length,0);
  assert.deepEqual(JSON.parse(await readFile(join(f.workspace,'work/joined.json'),'utf8')),{joined:true});
});

test('WorkflowDrive inherits its physical task root for WSL Host resource execution',
  {skip:process.platform!=='win32'||process.env.CODEX_TEST_WSL_HOST_PROGRAM!=='1'},async t=>{
  const f=await fixture(t,{env:process.env});await f.migrate();
  const path='workflow-assets/scripts/probe.py',output={type:'object',properties:{ok:{type:'boolean'}},required:['ok'],additionalProperties:false};
  const contract={id:'wsl-resource-probe',identity:workflowResourceProgramIdentity(),argv:['python',path,'work/.workflow-runtime'],
    input_schema:{type:'object',additionalProperties:false},output_schema:output,env_allow:[],
    permissions:{network:false,read_paths:[path],write_paths:['work']},output_cap_bytes:4096,deadline_ms:30000,idempotency:{mode:'safe'}};
  const workflow={...createDraft('wsl-resource-root','WSL resource root'),status:'ready',
    requirements:{providers:[],tools:[],mcp_servers:[],executables:['python']},
    skill_policy:{mode:'cooperative',implicit:'deny',ambient_allow:[],shadowed_skill_paths:[]},host_tools:[contract],
    inputs_schema:{type:'object',properties:{task:{type:'string'}},required:['task'],additionalProperties:false},
    finalization:{required:true,node_id:'final'},nodes:[{id:'start',type:'start'},
      {id:'probe',type:'tool',executor:{kind:'tool',tool:contract.id},access:'bounded_write',path_scope:{binding:'run.allowed_paths'},
        approval:{required:false},retry:{max_attempts:1},resources:[path],input_bindings:{},outputs_schema:output},
      {id:'final',type:'agent',role:'finalizer',executor:{kind:'main'},access:'read_only',approval:{required:false},retry:{max_attempts:1},
        input_bindings:{task:'/inputs/task',result:'/nodes/probe/output'},prompt_template:'Report result.'},{id:'end',type:'end'}],
    edges:[{id:'start-probe',source:'start',target:'probe'},{id:'probe-final',source:'probe',target:'final'},{id:'final-end',source:'final',target:'end'}]};
  const created=await f.service.call('create',{workflow,resources:{[path]:'import json\nprint(json.dumps({"ok": True}))\n'}},{human:true});
  const binding=qualifiedExecutionBinding({kind:'wsl',launcher:join(process.env.SystemRoot??'C:\\Windows','System32','wsl.exe'),
    distribution:'Ubuntu',sandbox:'/usr/bin/bwrap',programs:{python:'/usr/bin/python3'},runtime_roots:['/lib','/lib64','/usr'],command_timeout_ms:300000});
  await mkdir(join(f.workspace,'work'));
  const run=await f.service.call('start',{workflow_id:workflow.id,revision_hash:created.revision_hash,workspace:f.workspace,
    access:'bounded_write',allowed_paths:['work'],main_actor:'root',inputs:{task:'Probe'},constraints:{execution_binding:binding}});
  const progress=await f.service.call('drive',control(run));
  assert.equal(progress.stop_reason,'semantic_node');
  assert.deepEqual((await f.service.call('get',control(run))).nodes.probe.output,{ok:true});
});

test('human adoption rotates lost authority and resumes an unsubmitted max-one claim without charging a retry', async t => {
  const f = await fixture(t); await f.migrate(); const run = await f.start(); const old = await claim(f, run); const state = await f.service.call('get', control(run));
  const recovery = { run_id: run.run_id, expected_sequence: state.sequence, reason: 'Synthetic browser loss', main_actor: 'human-console' };
  await assert.rejects(f.service.call('adopt_run', recovery), { code: 'HUMAN_CONTROL_RECOVERY_REQUIRED' });
  await assert.rejects(f.service.call('adopt_run', { ...recovery, expected_sequence: 1 }, { human: true }), { code: 'RUN_SEQUENCE_CONFLICT' });
  const adopted = await f.service.call('adopt_run', recovery, { human: true }); assert.equal(adopted.status, 'paused'); assert.deepEqual(adopted.recovery_errors, []);
  await assert.rejects(f.service.call('pause', control(run)), { code: 'RUN_AUTHORITY' });
  await assert.rejects(f.service.call('complete_node', { ...leaseArgs(run, old), completion: completion({}) }), { code: 'LEASE_INVALID' });
  const restored = await f.service.call('recover_claim', { ...control(adopted), node_id: old.node_id, attempt_id: old.attempt_id });
  assert.notEqual(restored.envelope.lease_token, old.lease_token); assert.equal(restored.envelope.attempt_id, old.attempt_id); assert.equal(restored.retry_charged, false);
  assert.equal(restored.state.nodes[old.node_id].attempts.length, 1);
  await f.service.call('resume', control(adopted));
  assert.equal((await f.service.call('get', control(adopted))).nodes[old.node_id].status, 'claimed');
});

test('native handoff recovery preserves exact host attestation and rejects a replacement task identity', async t => {
  const f = await fixture(t); await f.migrate(); const run = await f.start(); const work = await claim(f, run); const args = leaseArgs(run, work);
  const dispatched = await f.service.call('dispatch', args); const receipt = { agent_id: 'original-native-task' };
  await f.service.call('dispatch_receipt', { ...args, request_id: dispatched.request_id, receipt }); await f.service.call('resume', { ...control(run), after_restart: true });
  await assert.rejects(f.service.call('reattach_handoff', { ...args, reconciliation: { outcome: 'completed', receipt: { agent_id: 'another-task' }, evidence: [{}] } }), { code: 'HANDOFF_RECONCILIATION_REQUIRED' });
  const restored = await f.service.call('reattach_handoff', { ...args, reconciliation: { outcome: 'completed', receipt, evidence: [{ host_tool: 'read exact task', observed: 'completed' }] } });
  assert.equal(restored.state.nodes.implementation.attempts[0].reconciliation.independently_verified, false); assert.equal(restored.state.nodes.implementation.attempts.length, 1);
  await f.service.call('resume', control(run)); await f.service.call('complete_node', { ...leaseArgs(run, restored.envelope), completion: completion({ verified: true }) });
});

test('Run cancel fences first, forwards only exact connector identity and records confirmed remote cancellation', async t => {
  let params; let controls = 0; let state = 'running'; let service; let authority;
  const task = () => ({ task_id: params.taskId, provider_id: params.provider.id, stage_id: params.stageId, task_type_id: params.taskTypeId,
    connector: 'grok_acp', remote_identity: { session_id: 'session-original', run_id: 'remote-original' }, state,
    ...(state === 'cancelled' ? { terminal_evidence: { kind: 'acp_prompt_result' }, execution_cleanup: { local_quiescent: true } } : {}) });
  const registry = { async start(value) { params = value; return task(); }, async status() { return task(); }, async control(id, args) {
    controls++; assert.equal((await service.call('get', authority)).status, 'cancelled'); assert.equal(id, params.taskId); assert.equal(args.expected_session_id, 'session-original'); assert.equal(args.expected_run_id, 'remote-original'); state = 'cancelled'; return task();
  } };
  const f = await fixture(t, { registry, configure(config) { config.providers.find(p => p.id === 'grok-local').enabled = true; config.task_types.find(w => w.id === 'brainstorm').stages[0].provider_id = 'grok-local'; } }); service = f.service;
  await f.migrate(); const run = await f.start(); authority = control(run); const lease = await claim(f, run); await service.call('dispatch', leaseArgs(run, lease));
  const cancelled = await service.call('cancel', authority); assert.equal(controls, 1); assert.equal(cancelled.nodes.implementation.attempts[0].dispatch.cancellation_pending, false);
  assert.equal(cancelled.nodes.implementation.attempts[0].connector_control.state, 'cancelled');
  assert.deepEqual(cancelled.cost_ledger.calls[0].usage, { unknown: true });
  assert.equal(cancelled.cost_ledger.unknown_usage_count, 1);
});

test('a losing concurrent resume cannot refence the successful recovered Run', async t => {
  const f = await fixture(t); await f.migrate(); const run = await f.start(); const old = await claim(f, run);
  const state = await f.service.call('get', control(run));
  const adopted = await f.service.call('adopt_run', { run_id: run.run_id, expected_sequence: state.sequence,
    reason: 'Concurrent resume fixture', main_actor: 'human-console' }, { human: true });
  await f.service.call('recover_claim', { ...control(adopted), node_id: old.node_id, attempt_id: old.attempt_id });
  const open = f.service.open.bind(f.service); let entered = 0; let bothEntered;
  const ready = new Promise(resolve => { bothEntered = resolve; }); let release;
  const gate = new Promise(resolve => { release = resolve; });
  f.service.open = async () => {
    const context = await open(); const assertQuiescent = context.coordinator.assertRunQuiescent.bind(context.coordinator);
    context.coordinator.assertRunQuiescent = async (...values) => {
      await assertQuiescent(...values); if (++entered === 2) bothEntered(); await gate;
    };
    return context;
  };
  const first = f.service.call('resume', control(adopted));
  const second = f.service.call('resume', control(adopted));
  await ready; release();
  const outcomes = await Promise.allSettled([first, second]);
  assert.equal(outcomes.filter(result => result.status === 'fulfilled').length, 1);
  assert.equal(outcomes.filter(result => result.status === 'rejected').length, 1);
  assert.equal(f.service.attemptAdmission.fencedRuns.has(run.run_id), false);
  assert.equal((await f.service.call('get', control(adopted))).status, 'running');
});

test('a separate request closes a connector reservation cancelled before its remote receipt', async t => {
  let reserved; const entered = new Promise(resolve => { reserved = resolve; });
  let params; let remoteStarts = 0;
  const registry = {
    async start(value) {
      params = value; reserved();
      await new Promise(resolve => value.signal.addEventListener('abort', resolve, { once: true }));
      try { value.assertActive(); } catch (error) { throw Object.assign(error, { cancellation_confirmed: true }); }
      remoteStarts++; throw new Error('revoked connector reached remote submission');
    },
    async status(id) {
      assert.equal(id, params.taskId);
      return { task_id: id, provider_id: params.provider.id, stage_id: params.stageId, task_type_id: params.taskTypeId,
        connector: 'grok_acp', state: 'failed', remote_identity: { session_id: 'pre-prompt-session' },
        startup_cleanup: { local_quiescent: true, prompt_submitted: false }, usage: null };
    },
    async control() { throw new Error('a pre-submission task must not receive remote control'); },
  };
  const f = await fixture(t, { registry, configure(config) { config.providers.find(p => p.id === 'grok-local').enabled = true; config.task_types.find(w => w.id === 'brainstorm').stages[0].provider_id = 'grok-local'; } });
  await f.migrate(); const run = await f.start(); const args = leaseArgs(run, await claim(f, run));
  const dispatch = assert.rejects(f.service.call('dispatch', args), { code: 'ATTEMPT_STOPPED' }); await entered;
  const other = new WorkflowService({ configPath: f.configPath, defaultConfigPath: DEFAULT_CONFIG_PATH, registry });
  const cancelled = await other.call('cancel', control(run)); await dispatch;
  assert.equal(cancelled.status, 'cancelled'); assert.equal(remoteStarts, 0);
  assert.equal(cancelled.nodes.implementation.attempts[0].dispatch.cancellation_pending, false);
  assert.equal(cancelled.nodes.implementation.attempts[0].dispatch.receipt.task_id, args.attempt_id);
});

test('unconfirmed local connector cleanup cannot make Run cancellation report success', async t => {
  let entered; const started = new Promise(resolve => { entered = resolve; }); let params;
  const registry = {
    async start(value) {
      params = value; entered();
      await new Promise(resolve => value.signal.addEventListener('abort', resolve, { once: true }));
      throw Object.assign(new Error('owned child did not exit'), { code: 'CONNECTOR_CLEANUP_INCOMPLETE' });
    },
    async status(id) {
      assert.equal(id, params.taskId);
      return { task_id: id, provider_id: params.provider.id, stage_id: params.stageId, task_type_id: params.taskTypeId,
        connector: 'grok_acp', state: 'needs_attention', remote_identity: {},
        startup_cleanup: { local_quiescent: false, prompt_submitted: false } };
    },
    async control() { throw new Error('no confirmed remote owner can be cancelled'); },
  };
  const f = await fixture(t, { registry, configure(config) { config.providers.find(p => p.id === 'grok-local').enabled = true; config.task_types.find(w => w.id === 'brainstorm').stages[0].provider_id = 'grok-local'; } });
  await f.migrate(); const run = await f.start(); const args = leaseArgs(run, await claim(f, run));
  const dispatch = assert.rejects(f.service.call('dispatch', args)); await started;
  const other = new WorkflowService({ configPath: f.configPath, defaultConfigPath: DEFAULT_CONFIG_PATH, registry });
  await assert.rejects(other.call('cancel', control(run)), { code: 'RUN_CANCEL_INCOMPLETE' });
  await dispatch;
  assert.equal((await other.call('get', control(run))).status, 'cancelled');
});

test('unconfirmed cancellation remains fenced until the original remote identity is observed terminal', async t => {
  let params; let remote = 'original'; let phase = 'running';
  const task = () => ({ task_id: params.taskId, provider_id: params.provider.id, stage_id: params.stageId, task_type_id: params.taskTypeId,
    connector: 'grok_acp', remote_identity: { session_id: 'session', run_id: remote }, state: phase });
  const registry = { async start(value) { params = value; return task(); }, async status() { return task(); }, async control() { throw new Error('Synthetic remote transport lost'); } };
  const f = await fixture(t, { registry, configure(config) { config.providers.find(p => p.id === 'grok-local').enabled = true; config.task_types.find(w => w.id === 'brainstorm').stages[0].provider_id = 'grok-local'; } });
  await f.migrate(); const run = await f.start(); const lease = await claim(f, run); const args = leaseArgs(run, lease); await f.service.call('dispatch', args);
  await assert.rejects(f.service.call('cancel', control(run)), { code: 'RUN_CANCEL_INCOMPLETE' });
  const pending = () => f.service.call('get', control(run)); assert.equal((await pending()).status, 'cancelled');
  remote = 'replacement'; phase = 'completed';
  await assert.rejects(f.service.call('reconcile_connector', args), { code: 'CONNECTOR_IDENTITY' });
  assert.equal((await pending()).nodes.implementation.attempts[0].dispatch.cancellation_pending, true);
  remote = 'original'; await f.service.call('reconcile_connector', args);
  assert.equal((await pending()).nodes.implementation.attempts[0].dispatch.cancellation_pending, false);
});
test('restart reattachment verifies the exact connector and rotates its lease without resubmission or retry budget', async t => {
  let starts = 0; let reconciles = 0; let params; let phase = 'running'; let changedIdentity = false;
  const task = () => ({ task_id: params.taskId, provider_id: params.provider.id, stage_id: params.stageId, task_type_id: params.taskTypeId,
    connector: 'grok_acp', remote_identity: { session_id: changedIdentity ? 'different' : 'same', run_id: 'original-remote-run' }, state: phase,
    result: { value: 42 }, terminal_evidence: { kind: 'acp_prompt_result' }, execution_cleanup: { local_quiescent: true }, scope: { compliant: true, changed_paths: [], outside_paths: [] } });
  const registry = { async start(value) { starts++; params = value; return task(); }, async status(id) { assert.equal(id, params.taskId); return task(); }, async control(id, args) { assert.equal(id, params.taskId); assert.equal(args.action, 'reconcile'); reconciles++; phase = 'running'; return task(); } };
  const f = await fixture(t, { registry, configure(config) { const provider = config.providers.find(p => p.id === 'grok-local'); provider.enabled = true; config.task_types.find(w => w.id === 'brainstorm').stages[0].provider_id = provider.id; } });
  await f.migrate(); const run = await f.start(); const work = await claim(f, run); await f.service.call('dispatch', leaseArgs(run, work));
  await f.service.call('resume', { ...control(run), after_restart: true }); phase = 'unknown_after_restart';
  const args = { ...control(run), node_id: work.node_id, attempt_id: work.attempt_id };
  changedIdentity = true; await assert.rejects(f.service.call('reattach_connector', args), { code: 'DISPATCH_CONFLICT' }); assert.equal(reconciles, 0);
  changedIdentity = false; const restored = await f.service.call('reattach_connector', args); assert.equal(starts, 1); assert.equal(reconciles, 1); assert.equal(restored.state.nodes[work.node_id].attempts.length, 1);
  await assert.rejects(f.service.call('complete_node', { ...leaseArgs(run, work), completion: completion({}) }), { code: 'LEASE_INVALID' });
  await f.service.call('resume', control(run)); phase = 'completed';
  const completed = await f.service.call('collect_connector', leaseArgs(run, restored.envelope)); assert.equal(completed.nodes[work.node_id].output.value, 42); assert.equal(starts, 1);
});

test('service imports only a fresh actual inventory selection and prepares expansion without invoking a Provider', async t => {
  let source;
  const inventory = new SkillInventory(async () => ({ skills: [{ path: source, scope: 'user', enabled: true }], errors: [], discovered_by: 'synthetic-host-adapter' }));
  const f = await fixture(t, { capabilities: { skillInventory: inventory, context: { tools: ['read_workflow_resource'] } } }); await f.migrate();
  source = join(f.workspace, 'SKILL.md'); await writeFile(source, '---\nname: Import fixture\ndescription: Synthetic Skill\n---\nSummarize the user request.');
  const selected = (await f.service.call('skill_inventory', { workspace: f.workspace })).entries[0];
  const provider = (await f.service.config()).providers.find(item => item.enabled && item.kind === 'native_agent');
  const pack = await f.service.call('import_skill', { workspace: f.workspace, skill_id: selected.id, workflow_id: 'from-skill', provider_id: provider.id });
  assert.equal(pack.workflow.status, 'draft'); assert.equal(pack.workflow.skill_policy.mode, 'cooperative');
  assert.equal(pack.workflow.nodes.find(node => node.id === 'instructions').executor.provider_id, provider.id);
  const packet = await f.service.call('prepare_expansion', { workflow_id: pack.workflow.id, revision_hash: pack.revision_hash, provider_id: provider.id });
  assert.equal(packet.invoked, false); assert.equal(packet.handoff_required, true); assert.equal(packet.access, 'read_only');
  assert.equal((await f.service.call('verify_relocation', { workflow_id: pack.workflow.id, revision_hash: pack.revision_hash })).functional_execution_proven, false);
  await assert.rejects(f.service.call('review_import', { workflow_id: pack.workflow.id, expected_revision: pack.revision_hash }), { code: 'HUMAN_REVIEW_REQUIRED' });
  await writeFile(source, (await readFile(source, 'utf8')) + '\nChanged');
  await assert.rejects(f.service.call('import_skill', { workspace: f.workspace, skill_id: selected.id, workflow_id: 'stale' }), { code: 'SKILL_SELECTION_STALE' });
});

test('migrated bounded and judgment-heavy presets preserve native lanes through journaled main acceptance', async t => {
  const f = await fixture(t); const legacy = await f.service.config(); await f.migrate();
  for (const id of ['bounded-code-change', 'judgment-heavy-change']) {
    const source = legacy.task_types.find(item => item.id === id); const pack = await f.service.call('read', { workflow_id: id });
    const run = await f.service.call('start', { workflow_id: id, revision_hash: pack.revision_hash, workspace: f.workspace, access: 'bounded_write', allowed_paths: ['out.txt'], main_actor: 'root', inputs: { task: 'Synthetic host handoff verification' } });
    for (const stage of source.stages) {
      const definition = pack.workflow.nodes.find(node => node.id === stage.id);
      assert.equal(definition.executor.provider_id, stage.provider_id); assert.equal(definition.prompt_template, stage.template);
      const lease = await claim(f, run, stage.id); const args = leaseArgs(run, lease); const handoff = await f.service.call('dispatch', args);
      assert.equal(handoff.handoff_required, true); assert.equal(handoff.envelope.provider.id, stage.provider_id); assert.equal(handoff.envelope.access, stage.access);
      if (stage.role === 'reviewer') { assert.equal(handoff.envelope.access, 'read_only'); assert.equal(handoff.envelope.inputs.previous_result.synthetic_stage, 'implementation'); assert.equal(handoff.envelope.context_projection.legacy_ancestor_results, undefined); }
      await f.service.call('dispatch_receipt', { ...args, request_id: handoff.request_id, receipt: { agent_id: 'synthetic-' + id + '-' + stage.id } });
      await f.service.call('complete_node', { ...args, completion: completion({ synthetic_stage: stage.id, actual_model_called: false }) });
    }
    const final = await claim(f, run, 'final-acceptance'); const args = leaseArgs(run, final);
    await assert.rejects(f.service.call('complete_node', { ...args, completion: completion({}) }), { code: 'HOST_MAIN_LIFECYCLE_REQUIRED' });
    const accepted = await persistHostResult(f.service,run,final,{ verified_handoff_contract: id },{accepted:true});
    assert.equal(accepted.status, 'succeeded'); assert.equal(Object.values(accepted.nodes).flatMap(node => node.attempts).length, source.stages.length + 1);
    const fresh = new WorkflowService({ configPath: f.configPath, defaultConfigPath: DEFAULT_CONFIG_PATH, env: {} });
    const { idempotent, ...acceptedState } = accepted; assert.equal(idempotent, false);
    assert.deepEqual(await fresh.call('get', control(run)), acceptedState);
  }
});
test('service migration is human-owned; MCP executes a native handoff and main finalization with declared bindings', async t => {
  const f = await fixture(t);
  await assert.rejects(f.service.call('list'), { code: 'WORKFLOW_MIGRATION_REQUIRED' });
  await assert.rejects(f.service.call('migrate_v6'), { code: 'HUMAN_CONFIGURATION_REQUIRED' });
  const installTool=workflowToolDefinitions().find(tool=>tool.name==='workflow_install_workflow_package');
  assert(installTool?.inputSchema.properties.package_path);
  assert.equal(installTool?.inputSchema.properties.package,undefined,'model install must use a Host-read path or URL, not transcribed package JSON');
  assert(workflowToolDefinitions().some(tool=>tool.name==='workflow_delete'));
  for (const name of ['workflow_begin_main', 'workflow_run_main', 'workflow_complete_main', 'workflow_create_authoring_run', 'workflow_apply_authoring_result', 'workflow_purge_authoring_artifacts']) {
    const rejected = await handleRpc({ jsonrpc: '2.0', id: 2, method: 'tools/call', params: { name, arguments: {} } }, { configPath: f.configPath, defaultConfigPath: DEFAULT_CONFIG_PATH, env: {} });
    assert.equal(rejected.result.isError, true); assert.match(JSON.stringify(rejected), /HOST_OPERATION_REQUIRED|Host-only Workflow operations|unknown tool/);
  }
  await f.migrate();
  const publicationOutput={type:'object',properties:{accepted:{type:'boolean'}},required:['accepted'],additionalProperties:false};
  const publicationWorkflow={...createDraft('mcp-direct-publication','MCP direct publication'),status:'ready',
    skill_policy:{mode:'cooperative',implicit:'allow',ambient_allow:[],shadowed_skill_paths:[]},
    finalization:{required:true,node_id:'final'},nodes:[
      {id:'start',type:'start'},
      {id:'final',type:'agent',role:'finalizer',executor:{kind:'main'},access:'read_only',
        approval:{required:false},retry:{max_attempts:1},input_bindings:{},prompt_template:'Accept the result.',outputs_schema:publicationOutput},
      {id:'end',type:'end'}],edges:[{id:'start-final',source:'start',target:'final'},
        {id:'final-end',source:'final',target:'end'}]};
  const mcp=async(name,arguments_)=>handleRpc({jsonrpc:'2.0',id:1,method:'tools/call',params:{name,arguments:arguments_}},
    {configPath:f.configPath,defaultConfigPath:DEFAULT_CONFIG_PATH,env:{}});
  const createdRpc=await mcp('workflow_create',{workflow:publicationWorkflow});
  assert.equal(createdRpc.result.isError,undefined,JSON.stringify(createdRpc));
  const createdPack=JSON.parse(createdRpc.result.content[0].text);
  assert.equal(createdPack.workflow.status,'ready');
  const readyEdit={...createdPack.workflow,nodes:createdPack.workflow.nodes.map(node=>node.id==='final'
    ?{...node,prompt_template:'Accept edited result.'}:node)};
  const savedRpc=await mcp('workflow_save',{workflow_id:readyEdit.id,expected_revision:createdPack.revision_hash,workflow:readyEdit});
  assert.equal(savedRpc.result.isError,undefined,JSON.stringify(savedRpc));
  const savedPack=JSON.parse(savedRpc.result.content[0].text);
  assert.equal(savedPack.workflow.status,'ready');
  const draftRpc=await mcp('workflow_save',{workflow_id:readyEdit.id,expected_revision:savedPack.revision_hash,
    workflow:{...savedPack.workflow,status:'draft'}});
  assert.equal(draftRpc.result.isError,undefined,JSON.stringify(draftRpc));
  const draftPack=JSON.parse(draftRpc.result.content[0].text);
  const publishedRpc=await mcp('workflow_publish',{workflow_id:readyEdit.id,expected_revision:draftPack.revision_hash});
  assert.equal(publishedRpc.result.isError,undefined,JSON.stringify(publishedRpc));
  const publishedPack=JSON.parse(publishedRpc.result.content[0].text);
  assert.equal(publishedPack.workflow.status,'ready');
  const staleRpc=await mcp('workflow_publish',{workflow_id:readyEdit.id,expected_revision:draftPack.revision_hash});
  assert.equal(staleRpc.result.isError,true);
  assert.match(JSON.stringify(staleRpc),/REVISION_CONFLICT/);
  const invalidRpc=await mcp('workflow_create',{workflow:{...publicationWorkflow,id:'mcp-invalid-publication',edges:[]}});
  assert.equal(invalidRpc.result.isError,true);
  assert.match(JSON.stringify(invalidRpc),/WORKFLOW_NOT_READY/);
  const deletedRpc=await mcp('workflow_delete',{workflow_id:readyEdit.id,expected_revision:publishedPack.revision_hash});
  assert.equal(deletedRpc.result.isError,undefined,JSON.stringify(deletedRpc));
  assert.equal(JSON.parse(deletedRpc.result.content[0].text).deleted,true);
  const list = await f.service.call('list');
  assert.equal(list.some(w => w.id === 'brainstorm'), false, 'retired role graphs stay out of default Workflow discovery');
  const historical = await f.service.call('list', { include_legacy: true });
  assert(historical.some(w => w.id === 'brainstorm' && w.legacy_task_type));
  assert.doesNotMatch(JSON.stringify(historical), /CONSTRAINTS AND OWNERSHIP/);
  const mainPack=await f.service.call('read',{workflow_id:'brainstorm'});
  const noBridge=await handleRpc({jsonrpc:'2.0',id:3,method:'tools/call',params:{name:'workflow_start',_meta:{threadId:'01a0db81-70bf-7233-9021-4b4e3849bec7'},arguments:{workflow_id:'brainstorm',workspace:f.workspace,access:'read_only'}}},{configPath:f.configPath,defaultConfigPath:DEFAULT_CONFIG_PATH,env:{},serviceCapabilities:{nativeParentVerifier:async()=>{}}});
  assert.equal(noBridge.result.isError,true);assert.match(JSON.stringify(noBridge),/STRICT_DISABLED/);
  assert.equal((await f.service.call('runs')).length,0,'disabled Main execution must fail before persisting a Run');
  const run = await f.start();
  await assert.rejects(f.service.call('drive',control(run),{model:true}),{code:'HOST_MAIN_BRIDGE_REQUIRED'});
  assert.equal(Object.values((await f.service.call('get',control(run))).nodes).flatMap(node=>node.attempts).length,0);
  const work = await claim(f, run); const args = leaseArgs(run, work);
  const rpc = await handleRpc({ jsonrpc: '2.0', id: 1, method: 'tools/call', params: { name: 'workflow_dispatch', arguments: args } }, { configPath: f.configPath, defaultConfigPath: DEFAULT_CONFIG_PATH, env: {} });
  assert.equal(rpc.result.isError, undefined); const dispatched = JSON.parse(rpc.result.content[0].text);
  assert.equal(dispatched.adapter.execution, 'native_agent'); assert.equal(dispatched.envelope.provider.id, work.provider.id);
  assert.equal(JSON.stringify(dispatched).includes(run.control_token), false);
  await assert.rejects(f.service.call('dispatch', args), { code: 'DISPATCH_UNCERTAIN' });
  await assert.rejects(f.service.call('complete_node', { ...args, completion: completion({ design: 'A' }) }), { code: 'DISPATCH_RECEIPT_REQUIRED' });
  await f.service.call('dispatch_receipt', { ...args, request_id: dispatched.request_id, receipt: { agent_id: 'fake-native-1' } });
  await f.service.call('complete_node', { ...args, completion: completion({ design: 'A' }) });
  assert.equal((await f.service.call('dispatch', args)).idempotent, true);
  const final = await claim(f, run, 'final-acceptance'); assert.equal(final.inputs.result.design, 'A'); assert.equal(final.context_projection.legacy_ancestor_results, undefined);
  await assert.rejects(f.service.call('complete_node', { ...leaseArgs(run, final), completion: { ...completion({ accepted_design: 'A' }), acceptance: { accepted: true } } }),{code:'HOST_MAIN_LIFECYCLE_REQUIRED'});
  const result = await persistHostResult(f.service,run,final,{accepted_design:'A'},{accepted:true});
  assert.equal(result.status, 'succeeded');
});

test('dispatch rechecks disabled/revoked Provider and environment switches with no intent or substitute', async t => {
  const f = await fixture(t); await f.migrate(); const run = await f.start(); const work = await claim(f, run); const args = leaseArgs(run, work);
  const config = await f.service.config(); const provider = config.providers.find(p => p.id === work.provider.id); provider.enabled = false;
  await saveConfig(config, { configPath: f.configPath });
  await assert.rejects(f.service.call('dispatch', args), { code: 'PROVIDER_DISABLED' });
  assert.equal((await f.service.call('get', control(run))).nodes.implementation.attempts[0].dispatch, null);
  provider.enabled = true; await saveConfig(config, { configPath: f.configPath });
  f.service.env.SOL_CONTROL_DISABLED = '1'; await assert.rejects(f.service.call('dispatch', args), { code: 'CONTROL_DISABLED' });
  assert.equal((await f.service.call('get', control(run))).nodes.implementation.status, 'claimed');
});

test('API dispatch is advisory, records identity/output, and duplicate calls cannot invoke it twice', async t => {
  let calls = 0; let body;
  const f = await fixture(t, { configure(config) {
    config.global.allow_direct_api = true; const provider = config.providers.find(p => p.id === 'custom-openai-compatible'); provider.enabled = true; provider.config.auth_type = 'none';
    config.task_types.find(w => w.id === 'brainstorm').stages[0].provider_id = provider.id;
  }, fetchImpl: async (_url, request) => { calls++; body = JSON.parse(request.body); return new Response(JSON.stringify({ id: 'synthetic-response', choices: [{ message: { content: 'Advice' } }], usage: { prompt_tokens: 3, completion_tokens: 2, cost_micros: 17 } }), { status: 200, headers: { 'content-type': 'application/json' } }); } });
  await f.migrate(); const run = await f.start(); const work = await claim(f, run); const args = leaseArgs(run, work);
  const result = await f.service.call('dispatch', args); assert.equal(calls, 1); assert.equal(body.tools, undefined); assert.equal(result.state.nodes.implementation.output.text, 'Advice');
  assert.equal(result.receipt.provider_response_id, 'synthetic-response'); assert.equal(result.state.cost_ledger.spent_micros, 17); assert.deepEqual(result.state.cost_ledger.calls[0].usage, { unknown: false, input_tokens: 3, output_tokens: 2, cost_micros: 17 }); await f.service.call('dispatch', args); assert.equal(calls, 1);
});

test('failed direct API dispatch journals explicit unknown usage before terminal failure', async t => {
  const f = await fixture(t, { configure(config) {
    config.global.allow_direct_api = true; const provider = config.providers.find(p => p.id === 'custom-openai-compatible'); provider.enabled = true; provider.config.auth_type = 'none'; config.task_types.find(w => w.id === 'brainstorm').stages[0].provider_id = provider.id;
  }, fetchImpl: async () => { throw new Error('synthetic transport failure'); } });
  await f.migrate(); const run = await f.start(); const args = leaseArgs(run, await claim(f, run)); await assert.rejects(f.service.call('dispatch', args), { code: 'DISPATCH_UNCERTAIN' });
  const state = await f.service.call('get', control(run)); assert.equal(state.nodes.implementation.status, 'failed'); assert.deepEqual(state.cost_ledger.calls[0].usage, { unknown: true }); assert.equal(state.cost_ledger.unknown_usage_count, 1);
});

test('another request cancels the exact in-flight direct API owner before reporting Run cancellation complete', async t => {
  let entered; const started = new Promise(resolve => { entered = resolve; }); let aborted = false;
  const f = await fixture(t, { configure(config) {
    config.global.allow_direct_api = true; const provider = config.providers.find(p => p.id === 'custom-openai-compatible'); provider.enabled = true; provider.config.auth_type = 'none'; config.task_types.find(w => w.id === 'brainstorm').stages[0].provider_id = provider.id;
  }, fetchImpl: async (_url, { signal }) => {
    entered();
    return new Promise((_resolve, reject) => signal.addEventListener('abort', () => { aborted = true; reject(Object.assign(new Error('aborted'), { name: 'AbortError' })); }, { once: true }));
  } });
  await f.migrate(); const run = await f.start(); const args = leaseArgs(run, await claim(f, run));
  const dispatch = assert.rejects(f.service.call('dispatch', args), { code: 'DIRECT_API_CANCELLED' }); await started;
  const other = new WorkflowService({ configPath: f.configPath, defaultConfigPath: DEFAULT_CONFIG_PATH });
  const cancelled = await other.call('cancel', control(run));
  await dispatch;
  assert.equal(cancelled.status, 'cancelled');
  assert.equal(aborted, true);
  assert.deepEqual(cancelled.cost_ledger.calls[0].usage, { unknown: true });
});

test('explicit fail_node fences an in-flight API attempt before allowing retry', async t => {
  let entered; const started = new Promise(resolve => { entered = resolve; }); let aborted = false;
  const f = await fixture(t, { configure(config) {
    config.global.allow_direct_api = true; const provider = config.providers.find(p => p.id === 'custom-openai-compatible'); provider.enabled = true; provider.config.auth_type = 'none'; config.task_types.find(w => w.id === 'brainstorm').stages[0].provider_id = provider.id;
  }, fetchImpl: async (_url, { signal }) => {
    entered(); return new Promise((_resolve, reject) => signal.addEventListener('abort', () => { aborted = true; reject(Object.assign(new Error('aborted'), { name: 'AbortError' })); }, { once: true }));
  } });
  await f.migrate(); const run = await f.start(); const args = leaseArgs(run, await claim(f, run));
  const dispatch = assert.rejects(f.service.call('dispatch', args), { code: 'DIRECT_API_CANCELLED' }); await started;
  const other = new WorkflowService({ configPath: f.configPath, defaultConfigPath: DEFAULT_CONFIG_PATH });
  const failed = await other.call('fail_node', { ...args, error: { code: 'HOST_REJECTED', message: 'Explicitly failed' } });
  await dispatch; assert.equal(aborted, true); assert.equal(failed.nodes.implementation.status, 'failed');
  assert.equal(other.attemptAdmission.pendingAttempt(run.run_id, args.node_id, args.attempt_id).length, 0);
  assert.throws(() => other.attemptAdmission.begin(run.run_id, args.node_id, args.attempt_id, 'direct_api'), { code: 'ATTEMPT_STOPPED' });
});

test('retry_node rejects a failed attempt that still owns external work', async t => {
  const f = await fixture(t); await f.migrate(); const run = await f.start(); const args = leaseArgs(run, await claim(f, run));
  const owner = f.service.attemptAdmission.begin(run.run_id, args.node_id, args.attempt_id, 'direct_api');
  const { runtime } = await f.service.open();
  await runtime.failNode(run.run_id, { ...args, error: { code: 'FIXTURE_FAILED', message: 'The owner has not stopped' } });
  await assert.rejects(f.service.call('retry_node', { ...control(run), node_id: args.node_id }), { code: 'RETRY_OWNER_ACTIVE' });
  owner.settle();
});

test('a losing concurrent retry cannot refence the successful new Run epoch', async t => {
  const f = await fixture(t); await f.migrate();
  const implementation = { id: 'implementation', type: 'agent', executor: { kind: 'main' }, role: 'implementer', access: 'read_only',
    approval: { required: false }, retry: { max_attempts: 2 }, input_bindings: { task: '/inputs/task' }, prompt_template: '{{task}}', outputs_schema: { type: 'object' } };
  const workflow = { ...createDraft('retry-epoch-fixture', 'Retry epoch fixture'), status: 'ready',
    skill_policy: { mode: 'cooperative', implicit: 'allow', ambient_allow: [], shadowed_skill_paths: [] },
    inputs_schema: { type: 'object', properties: { task: { type: 'string' } }, required: ['task'], additionalProperties: false },
    finalization: { required: true, node_id: 'final' },
    nodes: [{ id: 'start', type: 'start' }, implementation, { ...implementation, id: 'final', role: 'finalizer', retry: { max_attempts: 1 } }, { id: 'end', type: 'end' }],
    edges: [['start', 'implementation'], ['implementation', 'final'], ['final', 'end']].map(([source, target]) => ({ id: source + '-' + target, source, target })) };
  const created = await f.service.call('create', { workflow }, { human: true });
  const run = await f.service.call('start', { workflow_id: workflow.id, revision_hash: created.revision_hash, workspace: f.workspace,
    access: 'read_only', main_actor: 'root', inputs: { task: 'Retry once' } });
  const { runtime } = await f.service.open();
  const lease = await runtime.claimHostMain(run.run_id, { ...control(run), node_id: 'implementation', owner: 'root', request_id: 'retry-epoch-claim' });
  const args = leaseArgs(run, lease);
  await f.service.call('fail_node', { ...args, error: { code: 'FIXTURE_FAILED', message: 'Retry fixture' } });
  const open = f.service.open.bind(f.service); let entered = 0; let bothEntered;
  const ready = new Promise(resolve => { bothEntered = resolve; }); let release;
  const gate = new Promise(resolve => { release = resolve; });
  f.service.open = async () => {
    const context = await open(); const retry = context.runtime.retryNode.bind(context.runtime);
    context.runtime.retryNode = async (...values) => { if (++entered === 2) bothEntered(); await gate; return retry(...values); };
    return context;
  };
  const first = f.service.call('retry_node', { ...control(run), node_id: args.node_id });
  const second = f.service.call('retry_node', { ...control(run), node_id: args.node_id });
  await ready; release();
  const outcomes = await Promise.allSettled([first, second]);
  assert.equal(outcomes.filter(result => result.status === 'fulfilled').length, 1,
    JSON.stringify(outcomes.map(result => result.status === 'rejected' ? { code: result.reason.code, message: result.reason.message } : { status: result.status })));
  assert.equal(outcomes.filter(result => result.status === 'rejected').length, 1);
  assert.equal(f.service.attemptAdmission.fencedRuns.has(run.run_id), false);
  assert.equal((await f.service.call('get', control(run))).status, 'running');
});

test('connector task identity is allocated before start and recovered exactly after receipt loss', async t => {
  let calls = 0; let saved;
  const registry = { async start(params) { calls++; saved = params; throw new Error('Simulated transport loss after task creation'); }, async status(taskId) { assert.equal(taskId, saved.taskId); return { task_id: taskId, provider_id: saved.provider.id, stage_id: saved.stageId, task_type_id: saved.taskTypeId, connector: 'grok_acp', remote_identity: { session_id: 'session-1', run_id: 'remote-1' }, state: 'unknown_after_restart' }; }, async control(taskId) { assert.equal(taskId, saved.taskId); return { task_id: taskId, provider_id: saved.provider.id, stage_id: saved.stageId, task_type_id: saved.taskTypeId, connector: 'grok_acp', remote_identity: { session_id: 'session-1', run_id: 'remote-1' }, state: 'cancelled' }; } };
  const f = await fixture(t, { registry, configure(config) { const p = config.providers.find(p => p.id === 'grok-local'); p.enabled = true; config.task_types.find(w => w.id === 'brainstorm').stages[0].provider_id = p.id; } });
  await f.migrate(); const run = await f.start(); const work = await claim(f, run); const args = leaseArgs(run, work);
  await assert.rejects(f.service.call('dispatch', args), /Simulated transport loss/); assert.equal(saved.taskId, work.attempt_id); assert.deepEqual(saved.allowedPaths, []);
  await assert.rejects(f.service.call('dispatch', args), { code: 'DISPATCH_UNCERTAIN' }); assert.equal(calls, 1);
  const reconciled = await f.service.call('reconcile_connector', args); assert.equal(reconciled.receipt.remote_identity.session_id, 'session-1'); assert.equal(calls, 1);
  await assert.rejects(f.service.call('reconcile_connector', { ...args, control_token: 'wrong' }), { code: 'RUN_AUTHORITY' });
});

test('authenticated console migrates and validates graph; config save cannot replace migration identity', async t => {
  const f = await fixture(t); const state = await startConsole({ configPath: f.configPath, defaultConfigPath: DEFAULT_CONFIG_PATH, open: false }); t.after(stopConsole);
  const url = `http://127.0.0.1:${state.port}/api/workflow/migrate_v6`;
  assert.equal((await fetch(url, { method: 'POST', body: '{}' })).status, 401);
  const response = await fetch(url, { method: 'POST', headers: { authorization: `Bearer ${state.token}`, 'content-type': 'application/json' }, body: '{}' }); assert.equal(response.status, 200);
  const config = await f.service.config(); assert.equal(config.version, 7); const revision = configRevision(config); config.workflow_store.relative_path = 'other-store';
  await assert.rejects(saveConfig(config, { configPath: f.configPath, expectedRevision: revision }), /cannot replace/);
  const valid = await fetch(`http://127.0.0.1:${state.port}/api/workflow/list`, { method: 'POST', headers: { authorization: `Bearer ${state.token}` }, body: '{}' }); assert.equal(valid.status, 200); assert((await valid.json()).length > 0);
  await stopConsole();
});

test('connector persistence failure poisons in-memory state and duplicate IDs cannot overwrite tasks', async t => {
  const f = await fixture(t); const path = join(f.root, 'tasks.json'); const store = new ConnectorTaskStore({ statePath: path });
  await store.create({ task_id: 'synthetic-task', state: 'completed' });
  await assert.rejects(store.create({ task_id: 'synthetic-task' }), { code: 'TASK_ID_CONFLICT' });
  await rename(path, path + '.saved'); await mkdir(path);
  await assert.rejects(store.create({ task_id: 'uncommitted-task' }));
  await assert.rejects(store.get('uncommitted-task'), { code: 'CONNECTOR_STORE_FAILED' });
  assert.equal(JSON.parse(await readFile(path + '.saved', 'utf8')).tasks.length, 1);
});

test('two overlapping dispatch requests elect exactly one local sender', { timeout: 10000 }, async t => {
  let entered; const entering = new Promise(resolve => { entered = resolve; }); let release; const gate = new Promise(resolve => { release = resolve; }); let calls = 0;
  const f = await fixture(t, { configure(config) {
    config.global.allow_direct_api = true; const p = config.providers.find(p => p.id === 'custom-openai-compatible'); p.enabled = true; p.config.auth_type = 'none'; config.task_types.find(w => w.id === 'brainstorm').stages[0].provider_id = p.id;
  }, fetchImpl: async () => { calls++; entered(); await gate; return new Response(JSON.stringify({ id: 'one-response', choices: [{ message: { content: 'Once' } }] })); } });
  await f.migrate(); const run = await f.start(); const args = leaseArgs(run, await claim(f, run));
  const first = f.service.call('dispatch', args); await entering;
  try { await assert.rejects(f.service.call('dispatch', args), { code: 'DISPATCH_UNCERTAIN' }); assert.equal(calls, 1); }
  finally { release(); }
  await first; assert.equal(calls, 1);
});

test('console config save reports committed state when audit persistence fails', async t => {
  const f = await fixture(t); const console = await startConsole({ configPath: f.configPath, defaultConfigPath: DEFAULT_CONFIG_PATH, open: false }); t.after(stopConsole);
  const auditPath = resolveAuditPath(f.configPath); await rename(auditPath, auditPath + '.saved'); await mkdir(auditPath);
  const config = await f.service.config(); const revision = configRevision(config); config.global.console_title = 'Committed title';
  const response = await fetch(`http://127.0.0.1:${console.port}/api/config`, { method: 'PUT', headers: { authorization: `Bearer ${console.token}`, 'content-type': 'application/json' }, body: JSON.stringify({ config, expected_revision: revision }) });
  assert.equal(response.status, 400); const error = await response.json(); assert.equal(error.code, 'AUDIT_WRITE_FAILED'); assert.equal(error.committed, true);
  assert.equal((await f.service.config()).global.console_title, 'Committed title'); await stopConsole();
});

test('connector collection requires exact node identity and independently observed scope evidence', async t => {
  let saved; let observedScope = null;
  const task = () => ({ task_id: saved.taskId, task_type_id: saved.taskTypeId, stage_id: saved.stageId, provider_id: saved.provider.id, connector: 'grok_acp', remote_identity: { session_id: 'session-1', run_id: 'remote-1' }, state: 'completed', result: { text: 'Verified' }, terminal_evidence: { kind: 'acp_prompt_result' }, execution_cleanup: { local_quiescent: true }, scope: observedScope });
  const registry = { async start(params) { saved = params; return task(); }, async status(id) { assert.equal(id, saved.taskId); return task(); } };
  const f = await fixture(t, { registry, configure(config) { const p = config.providers.find(p => p.id === 'grok-local'); p.enabled = true; config.task_types.find(w => w.id === 'brainstorm').stages[0].provider_id = p.id; } });
  await f.migrate(); const run = await f.start(); const work = await claim(f, run); const args = leaseArgs(run, work);
  await f.service.call('dispatch', args);
  await assert.rejects(f.service.call('collect_connector', args), { code: 'CONNECTOR_EVIDENCE' });
  observedScope = { compliant: true, changed_paths: [], outside_paths: [], observed_digest: 'synthetic-observation' };
  const result = await f.service.call('collect_connector', args); assert.equal(result.nodes.implementation.status, 'succeeded'); assert.equal(result.nodes['final-acceptance'].status, 'ready'); assert.deepEqual(result.cost_ledger.calls[0].usage, { unknown: true }); assert.equal(result.cost_ledger.unknown_usage_count, 1);
});

test('terminal connector failure records explicit unknown usage before failNode', async t => {
  let saved; const task = () => ({ task_id: saved.taskId, task_type_id: saved.taskTypeId, stage_id: saved.stageId, provider_id: saved.provider.id, connector: 'grok_acp', remote_identity: { session_id: 'session-failed', run_id: 'remote-failed' }, state: 'failed', terminal_evidence: { kind: 'acp_prompt_result' }, execution_cleanup: { local_quiescent: true }, error: { code: 'SYNTHETIC_FAILURE', message: 'Synthetic terminal failure' } });
  const registry = { async start(params) { saved = params; return task(); }, async status() { return task(); } };
  const f = await fixture(t, { registry, configure(config) { const p = config.providers.find(p => p.id === 'grok-local'); p.enabled = true; config.task_types.find(w => w.id === 'brainstorm').stages[0].provider_id = p.id; } });
  await f.migrate(); const run = await f.start(); const args = leaseArgs(run, await claim(f, run)); await f.service.call('dispatch', args); const state = await f.service.call('collect_connector', args);
  assert.equal(state.nodes.implementation.status, 'failed'); assert.deepEqual(state.cost_ledger.calls[0].usage, { unknown: true }); assert.equal(state.cost_ledger.unknown_usage_count, 1);
});

test('authenticated human can cancel an owned Run without receiving or copying its token',async t=>{
 const f=await fixture(t);await f.migrate();const run=await f.start();
 const {runtime}=await f.service.open();
 const {retainOwnedAuthority}=await import('../lib/execution/owned-workflow-authority.mjs');
 await retainOwnedAuthority(runtime,run);
 await assert.rejects(f.service.call('cancel',{run_id:run.run_id},{model:true}),{code:'RUN_AUTHORITY'});
 const result=await f.service.call('cancel',{run_id:run.run_id},{human:true});
 assert.equal(result.status,'cancelled');assert.equal(result.control_token,undefined);
});
