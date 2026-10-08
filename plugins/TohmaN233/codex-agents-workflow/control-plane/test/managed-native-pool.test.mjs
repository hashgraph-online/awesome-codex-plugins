import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdir, mkdtemp, readFile, rm } from 'node:fs/promises';
import { join, resolve } from 'node:path';
import { tmpdir } from './physical-tempdir.mjs';
import { ManagedNativeManager, closeManagedNativeManagers, managedNativeManagerFor, runAssignedPool } from '../lib/execution/managed-native-manager.mjs';
import { canonicalJSON, digest } from '../lib/workflow-revisions.mjs';
import { resolvedSubagentPlan, WorkflowRuntime } from '../lib/workflow-runtime.mjs';
import { assignFanoutItems, assignedFanoutWritePaths } from '../lib/execution/fanout-input-projection.mjs';

const deferred=()=>{let resolve;const promise=new Promise(done=>{resolve=done;});return {promise,resolve};};

test('managed preparation accepts exact pinned Skill allowances for native session policy',async()=>{
  const manager=new ManagedNativeManager({configPath:'C:\\fixture\\managed-skills.json',env:{},getConfig:async()=>({}),
    qualify:async()=>({binary_sha256:'a'.repeat(64)})});
  const envelope={skill_policy:{mode:'cooperative'},provider:{kind:'native_agent',config:{model:'gpt-test',reasoning_effort:'low'}},
    skill_ref:{path:'skills/exact/SKILL.md'},allowed_skills:[{path:'skills/exact/SKILL.md',resources:[]}]};
  const prepared=await manager.prepare(null,null,null,envelope);
  assert.equal(prepared.execution,'managed_native_codex');
});

test('managed fan-out respects the declared concurrency and preserves dispatch order', async () => {
  const assignments=Array.from({length:10},(_,index)=>({index}));
  let active=0, peak=0;
  const results=await runAssignedPool(assignments,3,async ({index})=>{
    active++; peak=Math.max(peak,active);
    await new Promise(resolve=>setTimeout(resolve,10-index));
    active--; return index;
  });
  assert.equal(peak,3);
  assert.deepEqual(results,assignments.map(item=>item.index));
});

test('one failed assignment does not prevent untouched siblings from running',async()=>{
  const assignments=Array.from({length:8},(_,index)=>({index})),visited=[];
  await assert.rejects(runAssignedPool(assignments,3,async({index})=>{
    visited.push(index);
    if(index===1)throw Object.assign(new Error('one card failed'),{code:'CARD_FAILED'});
    return index;
  }),error=>error.code==='MANAGED_NATIVE_POOL_FAILED'&&error.errors[0].assignment_index===1);
  assert.deepEqual(visited.sort((a,b)=>a-b),assignments.map(item=>item.index));
});

test('Host derives disjoint child write scopes from fan-out items without Agent transcription',async t=>{
  const root=await mkdtemp(join(tmpdir(),'fanout-item-paths-')),outside=join(root,'..','outside.py');
  t.after(()=>rm(root,{recursive:true,force:true}));
  const fanout={write_paths_field:'write_paths'};
  assert.deepEqual(assignedFanoutWritePaths({workspace:root,nodeAllowedPaths:['cards','scenarios'],fanout,
    assignedItems:[{write_paths:['cards/a.py',join(root,'scenarios','a.json')]}]}),['cards/a.py','scenarios/a.json']);
  assert.deepEqual(assignedFanoutWritePaths({workspace:root,nodeAllowedPaths:['cards','scenarios'],fanout,
    assignedItems:[{write_paths:['cards/b.py']}]}),['cards/b.py']);
  assert.throws(()=>assignedFanoutWritePaths({workspace:root,nodeAllowedPaths:['cards','scenarios'],fanout,
    assignedItems:[{write_paths:[outside]}]}),{code:'SUBAGENT_ITEM_WRITE_PATHS'});
  assert.throws(()=>assignedFanoutWritePaths({workspace:root,nodeAllowedPaths:['cards'],fanout,
    assignedItems:[{write_paths:['scenarios/a.json']}]}),{code:'SUBAGENT_ITEM_WRITE_PATHS'});
});

test('managed native fan-out launches independent sub-Agents concurrently and joins Host-owned evidence',async t=>{
  const root=await mkdtemp(join(tmpdir(),'managed-native-pool-')),workspace=join(root,'workspace');await mkdir(workspace);
  t.after(async()=>{await rm(root,{recursive:true,maxRetries:3,retryDelay:100});});
  const provider={id:'pool-provider',kind:'native_agent',enabled:true,capabilities:{read:true,write:true},config:{role:'implementer',model:'gpt-test',reasoning_effort:'low',inactivity_timeout_ms:0}};
  const fanout={input:'items',item_name:'animation_slot',result_output:'results',distribution:'one_per_item',scheduling:'parallel',join:'all_required'};
  const definition={id:'render',type:'agent',executor:{kind:'provider',provider_id:provider.id},outputs_schema:{type:'object',properties:{results:{type:'array',items:{type:'string'}}},required:['results'],additionalProperties:false}};
  const envelope={run_id:'run-1',workflow_id:'workflow-1',node_id:'render',attempt_id:'attempt-1',executor:definition.executor,provider,access:'read_only',workspace,inputs:{items_json:JSON.stringify(['slot-a','slot-b']),background_json:JSON.stringify({api:'stable shared API'})},constraints:{},resources:[],effective_allowed_paths:[],subagents:{configured_count:'auto',resolved_count:2,fanout,items:['slot-a','slot-b']}};
  const record={pins:{root:{workflow:{nodes:[definition]}}},state:{constraints:{}}},receipts=[],events=[],usage=[],completions=[],trustedResults=[],savedArtifacts=[];
  const runtime={workflows:{root:join(root,'workflows')},runs:{root:join(root,'runs'),read:async()=>record,directory:()=>join(root,'runs','run-1'),
    saveArtifact:async(_run,label,bytes)=>{savedArtifacts.push({label,bytes});return {artifact:`artifact-${label}-${'c'.repeat(64)}.bin`,sha256:'c'.repeat(64),bytes:bytes.length};},
    saveExecutorResult:async(_run,_attempt,completion)=>{assert(Buffer.byteLength(canonicalJSON(completion))<256*1024);return {sha256:'a'.repeat(64)};}},
    execution:async()=>envelope,recordDispatchReceipt:async(_run,args)=>{receipts.push(args.receipt);},recordManagedNativeResults:async(_run,args)=>{trustedResults.push(args.results);},recordExecutorEvent:async(_run,args)=>{events.push(args.event);},recordUsage:async(_run,args)=>{usage.push(args.usage);},completeNode:async(_run,args)=>{completions.push(args.completion);return {nodes:{render:{status:'succeeded'}}};},failNode:async()=>{throw new Error('pool test should not fail');},get:async()=>({nodes:{render:{active_attempt_id:'attempt-1',status:'running'}}})};
  const bothStarted=deferred();let started=0;
  const manager=new ManagedNativeManager({configPath:join(root,'control-plane.json'),env:{},getConfig:async()=>({global:{enabled:true},providers:[provider]}),qualify:async()=>({}),sessionFactory:async settings=>({
    async turn(prompt){started++;if(started===2)bothStarted.resolve();await bothStarted.promise;const index=settings.owner.attempt_id.endsWith('001')?1:2;const refs=JSON.parse(prompt.match(/\nInputs:\n([^\n]+)/)[1]);const slots=JSON.parse(await readFile(refs.items_json.path,'utf8'));const background=JSON.parse(await readFile(refs.background_json.path,'utf8'));assert.deepEqual(slots,[`slot-${index===1?'a':'b'}`]);assert.equal(background.api,'stable shared API');assert.doesNotMatch(prompt,/stable shared API|slot-a|slot-b/);return {output:JSON.stringify({outcome:'completed',result:{result:`render-${index}`},block_reason:''}),thread_id:`thread-${index}`,turn_id:`turn-${index}`,usage:{unknown:true,input_tokens:index,output_tokens:1},audit:{index},item_types:['agentMessage'],command_audit:[{status:'completed',output:'x'.repeat(140000)}]};},
    async close(){settings.toolBroker.revoke();},async interrupt(){},
  })});
  const args={node_id:'render',attempt_id:'attempt-1',lease_token:'lease-1',control_token:'example-control-1'};
  const prepared={envelope,adapter:{model:'gpt-test',effort:'low',executable_sha256:'b'.repeat(64),settings:{authentication:{mode:'environment_api_key'},codex_binary:'unused'}},prompt:'Render the assigned animation slot.'};
  const launched=await manager.launch(runtime,'run-1',args,prepared);assert.equal(launched.dispatched,true);await manager.wait('run-1','attempt-1');
  assert.equal(started,2);assert.deepEqual(receipts[0].subagent_dispatch_ids,['managed-attempt-1-001','managed-attempt-1-002']);
  assert.equal(receipts[0].subagent_plan.resolved_count,2);assert.equal(receipts[0].subagent_plan.assignments.length,2);
  assert.deepEqual(usage,[{unknown:true,input_tokens:3,output_tokens:2}]);
  assert.deepEqual(trustedResults[0].map(item=>[item.dispatch_id,item.result_index,item.result_sha256,item.thread_id,item.turn_id]),[['managed-attempt-1-001',0,digest(canonicalJSON('render-1')),'thread-1','turn-1'],['managed-attempt-1-002',1,digest(canonicalJSON('render-2')),'thread-2','turn-2']]);
  assert.deepEqual(completions[0].structured_output,{results:['render-1','render-2']});
  assert.deepEqual(completions[0].evidence[0],{kind:'subagent_pool',resolved_count:2,dispatch_ids:['managed-attempt-1-001','managed-attempt-1-002']});
  assert.deepEqual(completions[0].evidence.filter(item=>item.kind==='managed_native_result').map(item=>[item.dispatch_id,item.result_index,item.result_sha256]),[['managed-attempt-1-001',0,digest(canonicalJSON('render-1'))],['managed-attempt-1-002',1,digest(canonicalJSON('render-2'))]]);
  assert.equal(savedArtifacts.length,1);assert(savedArtifacts[0].bytes.length>256*1024);
  assert.equal(completions[0].evidence.some(item=>Object.hasOwn(item,'command_audit')),false);
  assert.equal(completions[0].evidence.at(-1).kind,'command_audit_artifact');
  assert(events.some(event=>event.kind==='session_state'&&event.metadata.status==='closed'));
  await manager.close();assert(resolve(root).startsWith(resolve(tmpdir())));
});

test('managed serial fan-out keeps two exact partitions isolated without overlapping sessions',async t=>{
  const root=await mkdtemp(join(tmpdir(),'managed-native-serial-')),workspace=join(root,'workspace');await mkdir(workspace);
  t.after(async()=>rm(root,{recursive:true,maxRetries:3,retryDelay:100}));
  const provider={id:'serial-provider',kind:'native_agent',enabled:true,capabilities:{read:true,write:true},
    config:{role:'implementer',model:'gpt-test',reasoning_effort:'low',inactivity_timeout_ms:0}};
  const fanout={input:'items',item_name:'item',result_output:'results',distribution:'one_per_item',
    scheduling:'serial',max_concurrency:2,join:'all_required'};
  const definition={id:'work',type:'agent',executor:{kind:'provider',provider_id:provider.id},fanout,
    outputs_schema:{type:'object',properties:{results:{type:'array',items:{type:'string'}}},required:['results'],additionalProperties:false}};
  const envelope={run_id:'run-serial',workflow_id:'serial-workflow',node_id:'work',attempt_id:'attempt-serial',executor:definition.executor,
    provider,access:'read_only',workspace,inputs:{items_json:JSON.stringify(['first','second'])},resources:[],effective_allowed_paths:[],
    skill_policy:{mode:'cooperative'},allowed_skills:[],subagents:{configured_count:'auto',resolved_count:2,fanout,items:['first','second']}};
  const record={pins:{root:{workflow:{nodes:[definition]}}},state:{constraints:{},nodes:{work:{status:'running'}}}};let active=0,peak=0;const completed=[],failures=[];
  const runtime={workflows:{root:join(root,'workflows')},runs:{root:join(root,'runs'),read:async()=>record,
    directory:()=>join(root,'runs','run-serial'),saveExecutorResult:async()=>({sha256:'a'.repeat(64)})},
    execution:async()=>envelope,recordDispatchReceipt:async()=>{},recordManagedNativeResults:async()=>{},
    recordExecutorEvent:async()=>{},recordUsage:async()=>{},completeNode:async(_run,args)=>{completed.push(args.completion);return {nodes:{work:{status:'succeeded'}}};},
    failAttemptAfterQuiescence:async(_run,_args,error)=>{failures.push(error);}};
  const manager=new ManagedNativeManager({configPath:join(root,'control-plane.json'),env:{},
    getConfig:async()=>({global:{enabled:true},providers:[provider]}),qualify:async()=>({}),sessionFactory:async settings=>{
      active++;peak=Math.max(peak,active);
      return {async turn(prompt){const refs=JSON.parse(prompt.match(/\nInputs:\n([^\n]+)/)[1]);
        const [item]=JSON.parse(await readFile(refs.items_json.path,'utf8'));
        await new Promise(resolve=>setTimeout(resolve,20));
        return {output:JSON.stringify({outcome:'completed',result:{result:item},block_reason:''}),
          thread_id:`thread-${item}`,turn_id:`turn-${item}`,usage:{unknown:true},audit:{},item_types:[],command_audit:[]};},
        async close(){active--;settings.toolBroker.revoke();},async interrupt(){}};
    }});
  t.after(()=>manager.close());
  const args={node_id:'work',attempt_id:'attempt-serial',lease_token:'lease',control_token:'control'};
  const prepared={envelope,adapter:{model:'gpt-test',effort:'low',settings:{authentication:{mode:'environment_api_key'},codex_binary:'unused'}}};
  await manager.launch(runtime,'run-serial',args,prepared);
  const settled=await manager.wait('run-serial','attempt-serial');
  assert.equal(settled.status,'succeeded',JSON.stringify({settled,failures}));
  assert.equal(peak,1);assert.equal(active,0);
  assert.deepEqual(completed[0].structured_output.results,['first','second']);
});

test('shared fan-out grouping preserves fixed round-robin partitions and the parallel ceiling',()=>{
  const items=Array.from({length:7},(_,index)=>index);
  const fanout={distribution:'partition',scheduling:'parallel'};
  assert.deepEqual(assignFanoutItems(items,fanout,3),[[0,3,6],[1,4],[2,5]]);
  assert.deepEqual(assignFanoutItems(items,{distribution:'one_per_item',scheduling:'parallel'},items.length),items.map(item=>[item]));
  const many=Array.from({length:40},(_,index)=>index);
  assert.throws(()=>assignFanoutItems(many,{...fanout,batch_size:1},40),{code:'SUBAGENT_COUNT'});
  assert.throws(()=>assignFanoutItems(many,{...fanout,batch_size:1,max_concurrency:33},40),{code:'SUBAGENT_FANOUT_CONCURRENCY'});
  assert.throws(()=>assignFanoutItems(many,{...fanout,batch_size:10,max_concurrency:5},5),{code:'SUBAGENT_FANOUT_INPUT'});
});

for(const size of [31,200,400])test(`managed launch preserves contiguous ten-item batches for ${size} runtime items with five active children`,{timeout:10000},async t=>{
  const root=await mkdtemp(join(tmpdir(),'managed-native-batches-')),workspace=join(root,'workspace');await mkdir(workspace);
  const items=Array.from({length:size},(_,index)=>index),receipts=[],completions=[],childInputs=[],finished=[];
  const provider={id:'batch-provider',kind:'native_agent',enabled:true,capabilities:{read:true,write:true},
    config:{role:'implementer',model:'gpt-test',reasoning_effort:'low',inactivity_timeout_ms:0}};
  const fanout={input:'items',item_name:'card',result_output:'results',distribution:'partition',batch_size:10,
    scheduling:'parallel',max_concurrency:5,join:'all_required'};
  const definition={id:'work',type:'agent',executor:{kind:'provider',provider_id:provider.id},subagent_count:'auto',fanout,
    input_bindings:{items:'/inputs/items'},outputs_schema:{type:'object',properties:{results:{type:'array',items:{type:'array',items:{type:'integer'}}}},required:['results'],additionalProperties:false}};
  const plan=resolvedSubagentPlan(definition,{inputs:{items},nodes:{}});
  assert.deepEqual(plan.assignments.map(batch=>batch.length),Array.from({length:Math.ceil(size/10)},(_,index)=>Math.min(10,size-index*10)));
  const runId=`run-${size}`,attemptId=`attempt-${size}`,args={node_id:'work',attempt_id:attemptId,lease_token:'lease',control_token:'control'};
  const envelope={run_id:runId,workflow_id:'batch-workflow',node_id:'work',attempt_id:attemptId,executor:definition.executor,provider,
    access:'read_only',workspace,effective_allowed_paths:[],resources:[],prompt_template:'Process assigned cards.',
    inputs:{items_json:JSON.stringify(items),background_json:JSON.stringify({api:'shared API'})},
    subagents:{configured_count:'auto',resolved_count:plan.count,fanout,items}};
  const state={constraints:{},nodes:{work:{active_attempt_id:attemptId,status:'running'}}};
  const record={pins:{root:{workflow:{nodes:[definition]}}},state};
  const runtime={workflows:{root:join(root,'workflows')},runs:{root:join(root,'runs'),read:async()=>record,
    directory:()=>join(root,'runs',runId),saveExecutorResult:async()=>({sha256:'a'.repeat(64)})},
    execution:async()=>envelope,get:async()=>state,recordDispatchReceipt:async(_run,args)=>{receipts.push(args.receipt);},
    recordManagedNativeResults:async()=>{},recordExecutorEvent:async()=>{},recordUsage:async()=>{},
    completeNode:async(_run,args)=>{completions.push(args.completion);return {nodes:{work:{status:'succeeded'}}};}};
  const initialReady=deferred();let started=0,active=0,peak=0;
  const manager=new ManagedNativeManager({configPath:join(root,'control-plane.json'),env:{},
    getConfig:async()=>({global:{enabled:true},providers:[provider]}),qualify:async()=>({}),sessionFactory:async settings=>{
      assert.equal(receipts.length,1,'the assignment receipt precedes every child session');
      const index=Number(settings.owner.attempt_id.match(/-(\d+)$/)[1])-1;let closed=false;
      started++;active++;peak=Math.max(peak,active);if(started===Math.min(plan.count,5))initialReady.resolve();
      return {async turn(prompt){
        const refs=JSON.parse(prompt.match(/\nInputs:\n([^\n]+)/)[1]);
        const inputs={items_json:JSON.parse(await readFile(refs.items_json.path,'utf8')),
          background_json:JSON.parse(await readFile(refs.background_json.path,'utf8'))};childInputs[index]=inputs;
        await initialReady.promise;await new Promise(resolve=>setTimeout(resolve,5-index%5));finished.push(index);
        return {output:JSON.stringify({outcome:'completed',result:{result:inputs.items_json},block_reason:''}),
          thread_id:`thread-${index}`,turn_id:`turn-${index}`,usage:{unknown:true},audit:{},item_types:['agentMessage'],command_audit:[]};
      },async close(){if(!closed){closed=true;active--;settings.toolBroker.revoke();}},async interrupt(){}};
    }});
  t.after(async()=>{initialReady.resolve();await manager.close();await rm(root,{recursive:true,maxRetries:3,retryDelay:100});});
  const prepared={envelope,adapter:{model:'gpt-test',effort:'low',executable_sha256:'b'.repeat(64),
    settings:{authentication:{mode:'environment_api_key'},codex_binary:'unused'}},prompt:'Process assigned cards.'};
  await manager.launch(runtime,runId,args,prepared);const settled=await manager.wait(runId,attemptId);
  assert.equal(settled.status,'succeeded',JSON.stringify(settled));assert.equal(started,plan.count);
  assert.equal(peak,Math.min(5,plan.count));assert.equal(active,0);
  assert.deepEqual(receipts[0].subagent_plan,{resolved_count:plan.count,input_sha256:digest(canonicalJSON(items)),
    assignments:plan.assignments.map((assigned,index)=>({dispatch_id:`managed-${attemptId}-${String(index+1).padStart(3,'0')}`,items_sha256:digest(canonicalJSON(assigned))}))});
  for(const [index,inputs] of childInputs.entries())assert.deepEqual(inputs,{items_json:plan.assignments[index],background_json:{api:'shared API'}});
  assert.deepEqual(completions[0].structured_output.results,plan.assignments);
  assert.deepEqual(completions[0].structured_output.results.flat(),items);
  assert.equal(finished.length,plan.count);
});

test('managed native retains the exact session owner when factory initialization and rollback fail', async t => {
  const root = await mkdtemp(join(tmpdir(), 'managed-native-factory-failure-')); const workspace = join(root, 'workspace'); await mkdir(workspace);
  t.after(() => rm(root, { recursive: true, maxRetries: 3, retryDelay: 100 }));
  const provider = { id: 'failure-provider', kind: 'native_agent', enabled: true, capabilities: { read: true, write: true },
    config: { role: 'implementer', model: 'gpt-test', reasoning_effort: 'low', inactivity_timeout_ms: 0 } };
  const definition = { id: 'work', type: 'agent', executor: { kind: 'provider', provider_id: provider.id },
    outputs_schema: { type: 'object', properties: { value: { type: 'string' } }, required: ['value'], additionalProperties: false } };
  const envelope = { run_id: 'run-factory', workflow_id: 'workflow-factory', node_id: 'work', attempt_id: 'attempt-factory',
    executor: definition.executor, provider, access: 'read_only', workspace, inputs: {}, constraints: {}, resources: [],
    effective_allowed_paths: [], skill_policy: { mode: 'cooperative' }, allowed_skills: [], skill_ref: null, subagents: null };
  const state = { constraints: {}, nodes: { work: { status: 'running', active_attempt_id: 'attempt-factory' } } };
  const record = { pins: { root: { workflow: { nodes: [definition] }, resources: [] } }, state };
  const runtime = {
    workflows: { root: join(root, 'workflows') },
    runs: { root: join(root, 'runs'), read: async () => record, directory: () => join(root, 'runs', 'run-factory') },
    execution: async () => envelope,
    recordDispatchReceipt: async () => {}, recordExecutorEvent: async () => {}, recordUsage: async () => {},
    failNode: async () => { state.nodes.work.status = 'failed'; }, get: async () => state,
    failAttemptAfterQuiescence: async (_runId, _args, _error, { originEntry }) => {
      try { for (const session of originEntry.sessions) await session.close(); }
      catch (error) { originEntry.cleanupPending = true; throw error; }
      originEntry.sessions = [];
      state.nodes.work.status = 'failed';
    },
  };
  let allowClose = false; let closeCalls = 0; let owned;
  const manager = new ManagedNativeManager({ configPath: join(root, 'control-plane.json'), env: {},
    getConfig: async () => ({ global: { enabled: true }, providers: [provider] }), qualify: async () => ({}),
    sessionFactory: async settings => {
      owned = { async interrupt() {}, async close() {
        closeCalls++;
        if (!allowClose) throw Object.assign(new Error('Synthetic profile cleanup failure'), { code: 'SYNTHETIC_PROFILE_RETAINED' });
        settings.toolBroker.revoke();
      } };
      await settings.onSessionOwned(owned);
      const setupError = Object.assign(new Error('Synthetic initialization failure'), { code: 'SYNTHETIC_SESSION_SETUP' });
      try { await owned.close(); }
      catch (cleanupError) {
        throw Object.assign(new AggregateError([setupError, cleanupError], 'Synthetic setup/cleanup failure'), {
          code: 'MANAGED_NATIVE_SETUP_FAILED', retained_at: join(root, 'fake-profile'),
        });
      }
      throw setupError;
    },
  });
  const args = { node_id: 'work', attempt_id: 'attempt-factory', lease_token: 'lease', control_token: 'control' };
  const prepared = { envelope, adapter: { model: 'gpt-test', effort: 'low', executable_sha256: 'b'.repeat(64),
    settings: { authentication: { mode: 'environment_api_key' }, codex_binary: 'unused', binary_sha256: 'b'.repeat(64) } }, prompt: 'UNREACHED' };
  await manager.launch(runtime, 'run-factory', args, prepared);
  const settled = await manager.wait('run-factory', 'attempt-factory');
  const entry = [...manager.entries.values()][0];
  assert.equal(settled.status, 'audit_or_cleanup_failed');
  assert.equal(entry.cleanupPending, true);
  assert(entry.sessions.includes(owned), 'manager must retain the exact owner published before initialization');
  assert(closeCalls >= 2, 'factory rollback and manager failure cleanup both reached the owner');
  allowClose = true;
  await manager.stopRun('run-factory');
  assert.equal(entry.cleanupPending, false);
  assert.deepEqual(entry.sessions, []);
  await manager.close();
});

test('managed native cancellation cleans a late factory owner without submitting a turn', async t => {
  const root = await mkdtemp(join(tmpdir(), 'managed-native-late-owner-')); const workspace = join(root, 'workspace'); await mkdir(workspace);
  t.after(() => rm(root, { recursive: true, maxRetries: 3, retryDelay: 100 }));
  const provider = { id: 'late-provider', kind: 'native_agent', enabled: true, capabilities: { read: true, write: true },
    config: { role: 'implementer', model: 'gpt-test', reasoning_effort: 'low', inactivity_timeout_ms: 0 } };
  const definition = { id: 'work', type: 'agent', executor: { kind: 'provider', provider_id: provider.id },
    outputs_schema: { type: 'object', properties: { value: { type: 'string' } }, required: ['value'], additionalProperties: false } };
  const envelope = { run_id: 'run-late', workflow_id: 'workflow-late', node_id: 'work', attempt_id: 'attempt-late',
    executor: definition.executor, provider, access: 'read_only', workspace, inputs: {}, constraints: {}, resources: [],
    effective_allowed_paths: [], skill_policy: { mode: 'cooperative' }, allowed_skills: [], skill_ref: null, subagents: null };
  const state = { constraints: {}, nodes: { work: { status: 'running', active_attempt_id: 'attempt-late' } } };
  const record = { pins: { root: { workflow: { nodes: [definition] }, resources: [] } }, state };
  const runtime = { workflows: { root: join(root, 'workflows') },
    runs: { root: join(root, 'runs'), read: async () => record, directory: () => join(root, 'runs', 'run-late') },
    execution: async () => envelope, recordDispatchReceipt: async () => {}, recordExecutorEvent: async () => {}, recordUsage: async () => {},
    failNode: async () => { state.nodes.work.status = 'failed'; }, get: async () => state };
  const entered = deferred(); const release = deferred(); let allowClose = false; let closeCalls = 0; let turnCalls = 0; let owned;
  const manager = new ManagedNativeManager({ configPath: join(root, 'control-plane.json'), env: {},
    getConfig: async () => ({ global: { enabled: true }, providers: [provider] }), qualify: async () => ({}),
    sessionFactory: async settings => {
      entered.resolve(); await release.promise;
      owned = { async interrupt() {}, async turn() { turnCalls++; return { output: '{"value":"forbidden"}' }; }, async close() {
        closeCalls++; if (!allowClose) throw Object.assign(new Error('Synthetic late-owner cleanup failure'), { code: 'SYNTHETIC_PROFILE_RETAINED' });
        settings.toolBroker.revoke();
      } };
      await settings.onSessionOwned(owned); return owned;
    } });
  const args = { node_id: 'work', attempt_id: 'attempt-late', lease_token: 'lease', control_token: 'control' };
  const prepared = { envelope, adapter: { model: 'gpt-test', effort: 'low', executable_sha256: 'b'.repeat(64),
    settings: { authentication: { mode: 'environment_api_key' }, codex_binary: 'unused', binary_sha256: 'b'.repeat(64) } }, prompt: 'UNREACHED' };
  await manager.launch(runtime, 'run-late', args, prepared); await entered.promise;
  const stopping = manager.stopRun('run-late'); release.resolve();
  await assert.rejects(stopping, error => error instanceof AggregateError && /retained one or more exact executions/.test(error.message));
  const entry = [...manager.entries.values()][0];
  assert.equal(turnCalls, 0, 'a session returned after cancellation must never submit a model turn');
  assert.equal(entry.cleanupPending, true); assert(entry.sessions.includes(owned)); assert(closeCalls >= 2);
  allowClose = true; await manager.stopRun('run-late');
  assert.equal(entry.cleanupPending, false); assert.deepEqual(entry.sessions, []);
  await manager.close();
});

test('managed native cancellation revokes an authorization already waiting on config before turn submission', { timeout: 3000 }, async t => {
  const root = await mkdtemp(join(tmpdir(), 'managed-native-inflight-auth-')); const workspace = join(root, 'workspace'); await mkdir(workspace);
  t.after(() => rm(root, { recursive: true, maxRetries: 3, retryDelay: 100 }));
  const provider = { id: 'inflight-provider', kind: 'native_agent', enabled: true, capabilities: { read: true, write: true },
    config: { role: 'implementer', model: 'gpt-test', reasoning_effort: 'low', inactivity_timeout_ms: 0 } };
  const fanout = { input: 'items', item_name: 'item', result_output: 'results', distribution: 'one_per_item', scheduling: 'parallel', join: 'all_required' };
  const definition = { id: 'work', type: 'agent', executor: { kind: 'provider', provider_id: provider.id },
    outputs_schema: { type: 'object', properties: { results: { type: 'array', items: { type: 'string' } } }, required: ['results'], additionalProperties: false } };
  const envelope = { run_id: 'run-inflight', workflow_id: 'workflow-inflight', node_id: 'work', attempt_id: 'attempt-inflight',
    executor: definition.executor, provider, access: 'read_only', workspace, inputs: { items: ['first', 'second'] }, constraints: {}, resources: [],
    effective_allowed_paths: [], subagents: { configured_count: 'auto', resolved_count: 2, fanout, items: ['first', 'second'] } };
  const state = { constraints: {}, nodes: { work: { status: 'running', active_attempt_id: 'attempt-inflight' } } };
  const record = { pins: { root: { workflow: { nodes: [definition] }, resources: [] } }, state };
  const runtime = { workflows: { root: join(root, 'workflows') },
    runs: { root: join(root, 'runs'), read: async () => record, directory: () => join(root, 'runs', 'run-inflight'), saveExecutorResult: async () => ({ sha256: 'a'.repeat(64) }) },
    execution: async () => envelope, recordDispatchReceipt: async () => {}, recordManagedNativeResults: async () => {}, recordExecutorEvent: async () => {}, recordUsage: async () => {},
    completeNode: async () => { throw new Error('cancelled pool must not complete'); }, failNode: async () => { state.nodes.work.status = 'failed'; }, get: async () => state };
  const firstTurnStarted = deferred(); const firstTurnDone = deferred(); const firstInterruptEntered = deferred(); const releaseFirstInterrupt = deferred();
  const configAuthorizeEntered = deferred(); const releaseConfigAuthorize = deferred(); const secondTurnSettled = deferred();
  let blockConfig = false; let turnStartCalls = 0; let assertActiveFunctions = 0;
  const manager = new ManagedNativeManager({ configPath: join(root, 'control-plane.json'), env: {},
    getConfig: async () => {
      if (blockConfig) { blockConfig = false; configAuthorizeEntered.resolve(); await releaseConfigAuthorize.promise; }
      return { global: { enabled: true }, providers: [provider] };
    }, qualify: async () => ({}),
    sessionFactory: async settings => {
      if (typeof settings.assertActive === 'function') assertActiveFunctions++;
      const first = settings.owner.attempt_id.endsWith('001');
      return {
        async turn() {
          if (first) { firstTurnStarted.resolve(); await firstTurnDone.promise; return { output: '{"result":"first"}', thread_id: 'thread-first', turn_id: 'turn-first', usage: { unknown: true } }; }
          await firstTurnStarted.promise; blockConfig = true;
          try {
            await settings.authorize();
            settings.assertActive();
            turnStartCalls++;
            return { output: '{"result":"forbidden"}', thread_id: 'thread-second', turn_id: 'turn-second', usage: { unknown: true } };
          } finally { secondTurnSettled.resolve(); }
        },
        async interrupt() { if (first) { firstInterruptEntered.resolve(); await releaseFirstInterrupt.promise; firstTurnDone.resolve(); } },
        async close() { settings.toolBroker.revoke(); },
      };
    },
  });
  const args = { node_id: 'work', attempt_id: 'attempt-inflight', lease_token: 'lease', control_token: 'control' };
  const prepared = { envelope, adapter: { model: 'gpt-test', effort: 'low', executable_sha256: 'b'.repeat(64),
    settings: { authentication: { mode: 'environment_api_key' }, codex_binary: 'unused', binary_sha256: 'b'.repeat(64) } }, prompt: 'Process the assigned item.' };
  await manager.launch(runtime, 'run-inflight', args, prepared);
  await configAuthorizeEntered.promise;
  const stopping = manager.stopRun('run-inflight');
  await firstInterruptEntered.promise;
  releaseConfigAuthorize.resolve();
  await secondTurnSettled.promise;
  assert.equal(assertActiveFunctions, 2, 'every child must receive the shared synchronous revocation gate');
  assert.equal(turnStartCalls, 0, 'an authorization begun before cancellation cannot submit turn/start after revocation');
  releaseFirstInterrupt.resolve();
  await stopping;
  await manager.close();
});

test('managed native Run stop revokes every attempt before awaiting the first interrupt', { timeout: 1000 }, async () => {
  const manager = new ManagedNativeManager({ configPath: 'C:\\fixture\\managed-run-revoke.json', getConfig: async () => ({}), qualify: async () => ({}) });
  const firstInterruptEntered = deferred(); const releaseFirstInterrupt = deferred(); let secondInterruptCalls = 0;
  const firstSession = { async interrupt() { firstInterruptEntered.resolve(); await releaseFirstInterrupt.promise; }, async close() {} };
  const secondSession = { async interrupt() { secondInterruptCalls++; }, async close() {} };
  const base = { runId: 'shared-run', status: 'running', stopping: false, cleanupPending: false, broker: null, brokers: [],
    done: Promise.resolve(), prepared: {}, runtime: {}, job: Promise.resolve(), writes: new Set() };
  const first = { ...base, args: { attempt_id: 'attempt-first' }, session: firstSession, sessions: [firstSession] };
  const second = { ...base, args: { attempt_id: 'attempt-second' }, session: secondSession, sessions: [secondSession] };
  second.assertActive = () => { if (second.stopping) throw Object.assign(new Error('revoked'), { code: 'MANAGED_NATIVE_STOPPED' }); };
  manager.entries.set('first', first); manager.entries.set('second', second);
  const stopping = manager.stopRun('shared-run');
  await firstInterruptEntered.promise;
  assert.equal(first.stopping, true);
  assert.equal(second.stopping, true, 'all Run attempts must be revoked before the first interrupt wait');
  assert.throws(() => second.assertActive(), error => error.code === 'MANAGED_NATIVE_STOPPED');
  assert.equal(secondInterruptCalls, 0, 'cleanup may still be waiting on the first exact owner');
  releaseFirstInterrupt.resolve();
  await stopping;
  assert.equal(secondInterruptCalls, 1);
});

test('managed native stop returns with retained ownership when close fails instead of awaiting pending work', { timeout: 1000 }, async () => {
  const manager = new ManagedNativeManager({ configPath: 'C:\\fixture\\managed-pending.json', getConfig: async () => ({}), qualify: async () => ({}) });
  let allowClose = false; let settleDone; const done = new Promise(resolveDone => { settleDone = resolveDone; });
  const broker = { revoke() {}, isQuiescent() { return true; }, async quiesce() { return { quiescent: true }; } };
  const session = { async interrupt() {}, async close() {
    if (!allowClose) throw Object.assign(new Error('Synthetic close failure'), { code: 'SYNTHETIC_CLOSE_RETAINED' });
    settleDone();
  } };
  const entry = { runId: 'run-pending', status: 'running', stopping: false, cleanupPending: false,
    broker, brokers: [broker], session, sessions: [session], done, authorize() {}, prepared: {}, runtime: {}, job: done, writes: new Set() };
  manager.entries.set('fixture', entry);
  await assert.rejects(manager.stopRun('run-pending'), error => error instanceof AggregateError && /retained one or more exact executions/.test(error.message));
  assert.equal(entry.cleanupPending, true);
  assert(entry.sessions.includes(session));
  allowClose = true;
  await manager.stopRun('run-pending');
  assert.equal(entry.cleanupPending, false);
  assert.deepEqual(entry.sessions, []);
});

test('managed native retains failed terminal cleanup ownership and retries the exact broker on the next stop',async()=>{
  const manager=new ManagedNativeManager({configPath:'C:\\fixture\\managed-retry.json',getConfig:async()=>({}),qualify:async()=>({})});
  let quiescent=false,quiesceCalls=0,closeCalls=0,revokeCalls=0;
  const broker={revoke(){revokeCalls++;},isQuiescent(){return quiescent;},async quiesce(){quiesceCalls++;if(quiesceCalls===1)return {quiescent:false,error:Object.assign(new Error('stop helper failed'),{code:'CODEX_EXECUTION_STOP_UNCONFIRMED'})};quiescent=true;return {quiescent:true};}};
  const session={async interrupt(){},async close(){closeCalls++;if(closeCalls===1)throw Object.assign(new Error('first close retained profile'),{code:'CODEX_BROKER_STOP_UNCONFIRMED'});}};
  const entry={runId:'run-retry',status:'audit_or_cleanup_failed',stopping:false,cleanupPending:true,broker,brokers:[broker],session,sessions:[session],done:Promise.resolve(),authorize(){},prepared:{},runtime:{},job:null,writes:new Set()};
  manager.entries.set('fixture',entry);
  await assert.rejects(manager.stopRun('run-retry'),error=>error instanceof AggregateError&&/retained one or more exact executions/.test(error.message));
  assert.equal(entry.broker,broker);assert.equal(entry.cleanupPending,true);assert.equal(quiesceCalls,1);
  await manager.stopRun('run-retry');
  assert.equal(quiesceCalls,2);assert.equal(quiescent,true);assert.equal(entry.cleanupPending,false);assert.equal(entry.broker,null);assert.deepEqual(entry.sessions,[]);assert(revokeCalls>=2);
});

test('global managed-native shutdown keeps a manager registered until retained ownership is recovered',async()=>{
  const options={configPath:'C:\\fixture\\managed-global-retry.json',getConfig:async()=>({}),qualify:async()=>({})};
  const manager=managedNativeManagerFor(options);let quiescent=false,calls=0;
  const broker={revoke(){},isQuiescent(){return quiescent;},async quiesce(){if(++calls===1)return {quiescent:false};quiescent=true;return {quiescent:true};}};
  manager.entries.set('fixture',{runId:'run-global',status:'failed',stopping:false,cleanupPending:true,broker,brokers:[broker],session:null,sessions:[],done:Promise.resolve(),runtime:{},writes:new Set()});
  await assert.rejects(closeManagedNativeManagers(),AggregateError);assert.equal(managedNativeManagerFor(options),manager);
  await closeManagedNativeManagers();const replacement=managedNativeManagerFor(options);assert.notEqual(replacement,manager);await closeManagedNativeManagers();
});

test('a closed managed-native manager rejects a later dispatch through a retained reference', async () => {
  const manager = new ManagedNativeManager({ configPath: 'C:\\fixture\\managed-stale-reference.json', getConfig: async () => ({}), qualify: async () => ({}) });
  await manager.close();
  let receipts = 0;
  const runtime = { async recordDispatchReceipt() { receipts++; } };
  const prepared = { envelope: { subagents: null }, adapter: { model: 'gpt-test', effort: 'low', executable_sha256: 'a'.repeat(64) } };
  await assert.rejects(manager.launch(runtime, 'run-stale', { node_id: 'worker', attempt_id: 'attempt-stale' }, prepared));
  assert.equal(receipts, 0, 'a closed manager must not register a dispatch receipt');
});

async function perItemFixture(t,{blockedIndex=null,pauseRepair=false,inheritedIndices=[],itemCount=20,initialFailures=[2,7],incremental=false,realItemValidator=false}={}){
  const root=await mkdtemp(join(tmpdir(),'managed-native-items-')),workspace=join(root,'workspace');await mkdir(workspace);
  t.after(async()=>rm(root,{recursive:true,maxRetries:3,retryDelay:100}));
  const items=Array.from({length:itemCount},(_,index)=>`card-${index}`),runId='run-items',attemptId='attempt-items';
  const provider={id:'item-provider',kind:'native_agent',enabled:true,capabilities:{read:true,write:true},
    config:{role:'implementer',model:'gpt-test',reasoning_effort:'low',inactivity_timeout_ms:0}};
  const fanout={input:'items',item_name:'card',result_output:'results',distribution:'partition',batch_size:10,
    scheduling:'parallel',max_concurrency:2,join:'all_required',result_mode:'per_item',...(incremental?{item_delivery:'incremental'}:{})};
  const definition={id:'work',type:'agent',executor:{kind:'provider',provider_id:provider.id},retry:{max_attempts:3},subagent_count:'auto',fanout,
    input_bindings:{items:'/inputs/items'},
    outputs_schema:{type:'object',properties:{results:{type:'array',items:{type:'string'}}},required:['results'],additionalProperties:false}};
  const plan=resolvedSubagentPlan(definition,{inputs:{items},nodes:{}});
  const attempt={id:attemptId,status:'running',lease_hash:digest('lease'),native_item_results:Object.fromEntries(inheritedIndices.map(index=>[index,{agent_id:`prior-${index}`,result:`done-${index}`}])),
    inherited_native_item_indices:inheritedIndices,native_rejected_turns:{},dispatch:null};
  const state={run_id:runId,control_hash:digest('control'),inputs:{items},constraints:{},nodes:{work:{status:'running',active_attempt_id:attemptId,attempts:[attempt]}}};
  const record={pins:{root:{workflow:{nodes:[definition]},resources:[]}},state};
  const envelope={run_id:runId,workflow_id:'workflow-items',node_id:'work',attempt_id:attemptId,executor:definition.executor,provider,
    access:'read_only',workspace,effective_allowed_paths:[],resources:[],skill_policy:{mode:'cooperative'},allowed_skills:[],skill_ref:null,
    prompt_template:'Implement the assigned cards.',inputs:{items_json:JSON.stringify(items)},
    subagents:{configured_count:'auto',resolved_count:plan.count,fanout,items}};
  const events=[],trusted=[],completions=[],turns=new Map(),settingsSeen=[],repairEntered=deferred(),repairReleased=deferred();
  const runtime={workflows:{root:join(root,'workflows')},runs:{root:join(root,'runs'),read:async()=>record,
    directory:()=>join(root,'runs',runId),saveExecutorResult:async()=>({sha256:'a'.repeat(64)})},
    execution:async()=>envelope,get:async()=>state,recordExecutorEvent:async(_run,args)=>{events.push(args.event);},
    recordDispatchReceipt:async(_run,args)=>{attempt.dispatch={receipt:args.receipt};},
    recordNativeItemResults:async(_run,{index,agent_id,target_indices,result})=>{
      assert.equal(agent_id,attempt.dispatch.receipt.subagent_plan.assignments.find(item=>item.assignment_index===index).dispatch_id);
      if(!result||Object.keys(result).length!==1||!Array.isArray(result.items))throw Object.assign(new Error('items array required'),{code:'NATIVE_ITEM_RESULT'});
      const assigned=plan.assignments[index].map(value=>items.indexOf(value));const issues=[];
      const expectedTargets=assigned.filter(itemIndex=>!attempt.native_item_results[itemIndex]);assert.deepEqual(target_indices,expectedTargets);
      for(let localIndex=0;localIndex<Math.min(result.items.length,target_indices.length);localIndex++){
        const item=result.items[localIndex],itemIndex=target_indices[localIndex];
        assert.equal(Object.hasOwn(item,'item_index'),false);
        if(item.outcome==='completed'&&item.result===`done-${itemIndex}`){
          if(!attempt.native_item_results[itemIndex])attempt.native_item_results[itemIndex]={agent_id,result:item.result};
        }else issues.push({item_index:itemIndex,category:item.outcome==='blocked'?'blocked':'invalid',reason:item.block_reason??'invalid result'});
      }
      const unresolved=assigned.filter(itemIndex=>!attempt.native_item_results[itemIndex]);
      for(const itemIndex of unresolved)if(!issues.some(issue=>issue.item_index===itemIndex))issues.push({item_index:itemIndex,category:'invalid',reason:'missing item'});
      return {accepted_item_indices:assigned.filter(itemIndex=>attempt.native_item_results[itemIndex]),unresolved_item_indices:unresolved,issues,
        ...(unresolved.length?{}:{result:assigned.map(itemIndex=>attempt.native_item_results[itemIndex].result)})};
    },
    recordNativeRejectedTurn:async(_run,{index,agent_id,turn_id,reason})=>{
      assert.equal(agent_id,attempt.dispatch.receipt.subagent_plan.assignments.find(item=>item.assignment_index===index).dispatch_id);assert(turn_id);assert(reason);
      const count=(attempt.native_rejected_turns[index]?.count??0)+1;attempt.native_rejected_turns[index]={count};return {new:true,count};
    },recordManagedNativeResults:async(_run,args)=>{trusted.push(args.results);},recordUsage:async()=>{},
    completeNode:async(_run,args)=>{completions.push(args.completion);return {nodes:{work:{status:'succeeded'}}};},
    failAttemptAfterQuiescence:async()=>{state.nodes.work.status='failed';}};
  if(realItemValidator){
    runtime.runs.mutate=async(_run,_kind,change)=>({result:await change(state,record.pins,{state,events:[]})});
    runtime.recordNativeItemResults=(run,args)=>WorkflowRuntime.prototype.recordNativeItemResults.call(runtime,run,args);
    runtime.recordNativeRejectedTurn=(run,args)=>WorkflowRuntime.prototype.recordNativeRejectedTurn.call(runtime,run,args);
    runtime.recordManagedNativeResults=async(run,args)=>{trusted.push(args.results);return WorkflowRuntime.prototype.recordManagedNativeResults.call(runtime,run,args);};
  }
  const manager=new ManagedNativeManager({configPath:join(root,'control-plane.json'),env:{},
    getConfig:async()=>({global:{enabled:true},providers:[provider]}),qualify:async()=>({}),
    sessionFactory:async settings=>{
      settingsSeen.push(settings);const index=Number(settings.owner.attempt_id.match(/-(\d+)$/)[1])-1;
      const assigned=plan.assignments[index].map(value=>items.indexOf(value));let count=0,interrupted=false;const failedOnce=new Set();
      const resultFor=async(prompt,repair)=>{
        count++;turns.set(index,count);
        const allUnresolved=assigned.filter(itemIndex=>!attempt.native_item_results[itemIndex]);
        const unresolved=incremental?allUnresolved.slice(0,1):allUnresolved;
        assert(!prompt.includes('"item_index"'));
        if(repair && (!incremental||prompt.includes('Repair only'))){
          assert.doesNotMatch(prompt,/unresolved positions|item positions/i);
          const refs=JSON.parse(prompt.match(/\nInputs:\n([^\n]+)/)?.[1]??'{}');
          assert(refs.repair_items?.path);
          assert.deepEqual(JSON.parse(await readFile(refs.repair_items.path,'utf8')),unresolved.map(itemIndex=>items[itemIndex]));
        }
        const refs=JSON.parse(prompt.match(/\nInputs:\n([^\n]+)/)?.[1]??'{}');
        assert.deepEqual(JSON.parse(await readFile(refs.items_json.path,'utf8')),unresolved.map(itemIndex=>items[itemIndex]));
        assert.deepEqual(settings.allowedPaths,[]);
        const entries=unresolved.map(itemIndex=>{
          const failFirst=index===0&&initialFailures.includes(itemIndex)&&!failedOnce.has(itemIndex);
          if(failFirst)failedOnce.add(itemIndex);
          return itemIndex===blockedIndex||failFirst?{outcome:'blocked',block_reason:`card ${itemIndex} needs repair`}
            :{outcome:'completed',result:`done-${itemIndex}`};
        });
        const text=JSON.stringify({outcome:'completed',result:{items:entries},block_reason:''});
        return {output:text,thread_id:`thread-${index}`,turn_id:`turn-${index}-${count}`,usage:{unknown:false,input_tokens:1,output_tokens:1},
          audit:{input_sha256:digest(canonicalJSON([{type:'text',text:prompt}]))},item_types:['agentMessage'],command_audit:[]};
      };
       return {async turn(prompt){return await resultFor(prompt,false);},async continueTurn(prompt){
          if(pauseRepair && index===0){repairEntered.resolve();await repairReleased.promise;
            if(interrupted)throw Object.assign(new Error('interrupted'),{code:'CODEX_TURN_FAILED'});}
          return await resultFor(prompt,true);
        },async close(){settings.toolBroker.revoke();},async interrupt(){interrupted=true;repairReleased.resolve();}};
    }});
  const args={node_id:'work',attempt_id:attemptId,lease_token:'lease',control_token:'control'};
  const prepared={envelope,adapter:{model:'gpt-test',effort:'low',executable_sha256:'b'.repeat(64),
    settings:{authentication:{mode:'environment_api_key'},codex_binary:'unused'}},prompt:'Implement the assigned cards.'};
  return {manager,runtime,args,prepared,runId,attemptId,attempt,items,events,trusted,completions,turns,settingsSeen,repairEntered};
}

for(const initialFailures of [[],[2]])test(`managed incremental delivers one item with real runtime identity and separate repair budget (${initialFailures.length} repairs)`,async t=>{
  const f=await perItemFixture(t,{itemCount:6,initialFailures,incremental:true,realItemValidator:true,inheritedIndices:[0]});
  const inherited=structuredClone(f.attempt.native_item_results[0]);
  await f.manager.launch(f.runtime,f.runId,f.args,f.prepared);const settled=await f.manager.wait(f.runId,f.attemptId);
  assert.equal(settled.status,'succeeded',JSON.stringify(settled));
  assert.deepEqual(f.completions[0].structured_output.results,f.items.map((_,i)=>`done-${i}`));
  assert.deepEqual(f.attempt.native_item_results[0],inherited);
  assert.equal(f.turns.get(0),5+initialFailures.length);
  assert.equal(f.settingsSeen[0].maxTurns,7);
  assert.equal(f.attempt.native_rejected_turns[0]?.count??0,initialFailures.length);
  for(let i=1;i<6;i++)assert.equal(typeof f.attempt.native_item_results[i].turn_id,'string');
  assert.equal(f.trusted[0][0].result_sha256,digest(canonicalJSON(f.items.map((_,i)=>`done-${i}`))));
  await f.manager.close();
});

test('managed per-item fan-out journals valid cards and repairs only two failed cards in the same session',async t=>{
  const fixture=await perItemFixture(t);
  await fixture.manager.launch(fixture.runtime,fixture.runId,fixture.args,fixture.prepared);
  const settled=await fixture.manager.wait(fixture.runId,fixture.attemptId);
  assert.equal(settled.status,'succeeded');
  assert.deepEqual([...fixture.turns.entries()].sort(),[[0,2],[1,1]]);
  assert.equal(fixture.settingsSeen.length,2);assert(fixture.settingsSeen.every(item=>item.maxTurns===3));
  assert.equal(Object.keys(fixture.attempt.native_item_results).length,20);
  assert.deepEqual(fixture.completions[0].structured_output.results,fixture.items.map((_,index)=>`done-${index}`));
  assert.equal(fixture.trusted[0].length,2);
  assert.equal(fixture.events.filter(event=>event.kind==='native_prompt_delivery').length,3);
  await fixture.manager.close();
});

for(const inheritedIndices of [Array.from({length:10},(_,index)=>index),Array.from({length:10},(_,index)=>index+10),[2,7,11]]){
  test(`managed per-item retry keeps original assignment identities after inheriting ${inheritedIndices.join(',')}`,async t=>{
    const fixture=await perItemFixture(t,{inheritedIndices,itemCount:30,initialFailures:[]});
    const prior=structuredClone(fixture.attempt.native_item_results);
    await fixture.manager.launch(fixture.runtime,fixture.runId,fixture.args,fixture.prepared);
    const settled=await fixture.manager.wait(fixture.runId,fixture.attemptId);
    assert.equal(settled.status,'succeeded',JSON.stringify(settled));
    const active=[0,1,2].filter(index=>!Array.from({length:10},(_,offset)=>index*10+offset).every(item=>inheritedIndices.includes(item)));
    assert.deepEqual([...fixture.turns.keys()].sort(),active);
    assert.deepEqual(fixture.completions[0].structured_output.results,fixture.items.map((_,index)=>`done-${index}`));
    for(const [index,result]of Object.entries(prior))assert.deepEqual(fixture.attempt.native_item_results[index],result);
    const trusted=fixture.trusted[0];assert.equal(trusted.length,active.length);
    for(const [position,index]of active.entries()){
      assert.equal(trusted[position].dispatch_id,`managed-${fixture.attemptId}-${String(index+1).padStart(3,'0')}`);
      assert.equal(trusted[position].result_index,position);
      assert.equal(trusted[position].result_sha256,digest(canonicalJSON(fixture.items.slice(index*10,index*10+10).map((_,offset)=>`done-${index*10+offset}`))));
    }
    await fixture.manager.close();
  });
}

test('managed per-item retry reuses every inherited success without launching a child',async t=>{
  const root=await mkdtemp(join(tmpdir(),'managed-native-inherited-')),workspace=join(root,'workspace');await mkdir(workspace);
  t.after(async()=>rm(root,{recursive:true,maxRetries:3,retryDelay:100}));
  const provider={id:'retry-provider',kind:'native_agent',enabled:true,capabilities:{read:true,write:true},
    config:{role:'implementer',model:'gpt-test',reasoning_effort:'low',inactivity_timeout_ms:0}};
  const fanout={input:'items',item_name:'card',result_output:'results',distribution:'one_per_item',scheduling:'parallel',join:'all_required',result_mode:'per_item'};
  const definition={id:'work',type:'agent',executor:{kind:'provider',provider_id:provider.id},subagent_count:'auto',fanout,retry:{max_attempts:3},
    access:'read_only',input_bindings:{items:'/inputs/items'},
    outputs_schema:{type:'object',properties:{results:{type:'array',items:{type:'string'}}},required:['results'],additionalProperties:false}};
  const accepted=Object.fromEntries(['a','b','c'].map((result,index)=>[index,{agent_id:`prior-${index}`,result}]));
  const attempt={id:'attempt-retry',status:'running',lease_hash:digest('lease'),native_item_results:accepted,inherited_native_item_indices:[0,1,2]};
  const policy={mode:'cooperative',implicit:'deny',ambient_allow:[],shadowed_skill_paths:[]};
  const final={id:'final',type:'agent',executor:{kind:'main'},access:'read_only',input_bindings:{},outputs_schema:{},retry:{max_attempts:3},approval:{required:false},skill_policy:policy};
  const record={pins:{root:{workflow:{skill_policy:policy,nodes:[definition,final],edges:[{id:'finish',source:'work',target:'final'}],finalization:{node_id:'final'}},resources:[]}},
    state:{status:'running',workflow_revision:digest('workflow'),control_hash:digest('control'),cost_ledger:{calls:[]},constraints:{},inputs:{items:['a','b','c']},
      permissions:{access:'read_only',allowed_paths:[],workspace},edges:{finish:'pending'},approvals:{},
      nodes:{work:{status:'running',active_attempt_id:attempt.id,attempts:[attempt]},final:{status:'pending',attempts:[],approval_round:0}}}};
  const envelope={run_id:'run-retry',workflow_id:'workflow-retry',node_id:'work',attempt_id:attempt.id,executor:definition.executor,provider,
    access:'read_only',workspace,inputs:{items_json:JSON.stringify(['a','b','c'])},resources:[],effective_allowed_paths:[],skill_policy:{mode:'cooperative'},allowed_skills:[],
    subagents:{configured_count:'auto',resolved_count:3,fanout,items:['a','b','c']}};
  let receipt,completion,managedResults,usage,completionError;
  const runtime={workflows:{root:join(root,'workflows')},runs:{root:join(root,'runs'),read:async()=>record,directory:()=>join(root,'runs','run-retry'),saveExecutorResult:async()=>({sha256:'a'.repeat(64)})},
    execution:async()=>envelope,recordDispatchReceipt:async(_run,args)=>{receipt=args.receipt;attempt.dispatch={receipt,request_id:args.request_id};},recordManagedNativeResults:async(_run,args)=>{managedResults=args.results;},
    recordExecutorEvent:async()=>{},recordUsage:async(_run,args)=>{usage=args.usage;}};
  runtime.runs.mutate=async(_run,_kind,change)=>({result:await change(record.state,record.pins,{state:record.state,events:[]})});
  runtime.transition=async(_run,_kind,change)=>{await change(record.state,record.pins);return record;};
  runtime.recordManagedNativeResults=async(run,args)=>{managedResults=args.results;return WorkflowRuntime.prototype.recordManagedNativeResults.call(runtime,run,args);};
  runtime.completeNode=async(run,args)=>{completion=args.completion;try{return await WorkflowRuntime.prototype.completeNode.call(runtime,run,args);}catch(error){completionError=error;throw error;}};
  const manager=new ManagedNativeManager({configPath:join(root,'control-plane.json'),env:{},getConfig:async()=>({global:{enabled:true},providers:[provider]}),qualify:async()=>({}),
    sessionFactory:async()=>assert.fail('accepted retry items must not launch a child')});
  t.after(()=>manager.close());
  const args={node_id:'work',attempt_id:attempt.id,lease_token:'lease',control_token:'control'};
  const prepared={envelope,adapter:{model:'gpt-test',effort:'low',executable_sha256:'b'.repeat(64),settings:{authentication:{mode:'environment_api_key'},codex_binary:'unused'}}};
  await manager.launch(runtime,'run-retry',args,prepared);const settled=await manager.wait('run-retry',attempt.id);
  assert.equal(settled.status,'succeeded',completionError?.stack??JSON.stringify(settled));assert.deepEqual(receipt.subagent_dispatch_ids,[]);assert.equal(receipt.subagent_plan.resolved_count,0);
  assert.deepEqual(managedResults,[]);assert.deepEqual(usage,{unknown:false,cost_micros:0});assert.deepEqual(completion.structured_output.results,['a','b','c']);
  assert.deepEqual(completion.evidence[0],{kind:'subagent_pool',resolved_count:0,dispatch_ids:[]});
  assert.equal(record.state.nodes.work.status,'succeeded');assert.equal(record.state.nodes.final.status,'ready');
});

test('managed per-item exhaustion keeps completed cards and stops after the pinned same-session allowance',async t=>{
  const fixture=await perItemFixture(t,{blockedIndex:9});
  await fixture.manager.launch(fixture.runtime,fixture.runId,fixture.args,fixture.prepared);
  const settled=await fixture.manager.wait(fixture.runId,fixture.attemptId);
  assert.equal(settled.status,'failed');
  assert.deepEqual([...fixture.turns.entries()].sort(),[[0,3],[1,1]]);
  assert.equal(Object.keys(fixture.attempt.native_item_results).length,19);
  assert.equal(fixture.attempt.native_item_results[9],undefined);
  assert.equal(fixture.completions.length,0);
  assert(fixture.events.some(event=>event.kind==='session_state'&&event.metadata.code==='MANAGED_NATIVE_POOL_FAILED'));
  await fixture.manager.close();
});

test('managed per-item cancellation interrupts a pending same-session repair before any new result is journaled',{timeout:3000},async t=>{
  const fixture=await perItemFixture(t,{pauseRepair:true});
  await fixture.manager.launch(fixture.runtime,fixture.runId,fixture.args,fixture.prepared);
  await fixture.repairEntered.promise;
  const acceptedBefore=Object.keys(fixture.attempt.native_item_results).length;
  await fixture.manager.stopRun(fixture.runId);
  assert.equal(Object.keys(fixture.attempt.native_item_results).length,acceptedBefore);
  assert.equal(fixture.turns.get(0),1);
  assert((fixture.turns.get(1)??0)<=1);
  assert.equal(fixture.completions.length,0);
  await fixture.manager.close();
});
