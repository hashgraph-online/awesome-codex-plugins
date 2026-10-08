import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, readFile, rm } from 'node:fs/promises';
import { join, resolve } from 'node:path';
import { tmpdir } from './physical-tempdir.mjs';
import { DEFAULT_CONFIG_PATH } from '../server.mjs';
import { createDraft } from '../lib/workflow-schema.mjs';
import { WorkflowService } from '../lib/workflow-service.mjs';
import { retainOwnedAuthority } from '../lib/execution/owned-workflow-authority.mjs';
import { leaseToken } from '../lib/workflow-execution-envelope.mjs';
import { deferred } from './fixtures/deferred.mjs';
import { canonicalJSON, digest } from '../lib/workflow-revisions.mjs';

const PARENT_THREAD_ID = '00000000-0000-7000-8000-000000000001';
const MODEL_REQUEST = Object.freeze({ model: true, modelThreadId: PARENT_THREAD_ID });
const control = run => ({ run_id: run.run_id, control_token: run.control_token });

async function nativeAttemptContext(f,args){
  const {runtime}=await f.service.open();await runtime.authorizeController(args.run_id,{control_token:args.control_token});
  const record=await runtime.runs.read(args.run_id);
  const match=record.pins.root.workflow.nodes.flatMap(definition=>{
    const attempt=record.state.nodes[definition.id]?.attempts.find(item=>item.id===args.attempt_id);
    return attempt?[{definition,attempt}]:[];
  });
  assert.equal(match.length,1,'Test must identify one native attempt');
  const {definition,attempt}=match[0],binding={run_id:args.run_id,node_id:definition.id,attempt_id:attempt.id,
    lease_token:leaseToken(args.control_token,args.run_id,definition.id,attempt.id,attempt.lease_generation??0),
    control_token:args.control_token};
  return {runtime,record,definition,attempt,binding};
}

async function recordNativeSpawn(f,args){
  const {runtime,binding}=await nativeAttemptContext(f,args);
  await runtime.recordExecutorEvent(args.run_id,{...binding,event:{kind:'native_agent_spawn',metadata:{index:args.index,agent_id:args.agent_id}}});
  return {recorded:true,index:args.index,agent_id:args.agent_id};
}

async function fixture(t, nativeAgentObserver, extraCapabilities={}) {
  const root = await mkdtemp(join(tmpdir(), 'native-continuation-regression-'));
  const workspace = join(root, 'workspace');
  await mkdir(workspace);
  const configPath = join(root, 'control-plane.json');
  const service = new WorkflowService({
    configPath,
    defaultConfigPath: DEFAULT_CONFIG_PATH,
    env: {},
    capabilities: { ...extraCapabilities, nativeAgentObserver, nativeParentVerifier: async () => {} },
  });
  await service.call('migrate_v6', {}, { human: true });
  t.after(async () => {
    await Promise.allSettled([...service.attemptAdmission.drainJobs.values()]);
    assert(resolve(root).startsWith(resolve(tmpdir())));
    await rm(root, { recursive: true, maxRetries: 3, retryDelay: 100 });
  });
  return { workspace, service };
}

function delayedReceiptHostMainManager(){
  let current=null,release,launchedResolve;
  const gate=new Promise(resolve=>{release=resolve;});
  const launched=new Promise(resolve=>{launchedResolve=resolve;});
  const manager={launches:0,waits:0,launched,
    async launch({runtime,handoff}){
      if(handoff?.stop_reason!=='main_node')return handoff;
      manager.launches++;
      const binding=handoff.host_binding;
      await runtime.recordHostMainDispatchReceipt(binding.run_id,{...binding,
        request_id:`dispatch-${binding.attempt_id}`,receipt:{invocation_id:`host-main-${binding.attempt_id}`,
          executor:'codex-app-server-host-main',executable_sha256:'0'.repeat(64),model:'gpt-6-sol',effort:'medium',
          main_actor:'root',session_id:`logical-main-${binding.run_id}`,call_chain_id:`workflow-run-${binding.run_id}`}});
      current={runtime,binding};launchedResolve();
      return {run_id:binding.run_id,status:'running',node_id:binding.node_id};
    },
    async wait(runId){manager.waits++;assert.equal(current?.binding.run_id,runId);await gate;return {run_id:runId,status:'failed'};},
    async fail(){
      assert(current);
      await current.runtime.failNode(current.binding.run_id,{...current.binding,
        error:{code:'TEST_HOST_MAIN_STOP',message:'Test completes the joined Host Main owner'}});
      release();
    },
    async pending(){return current?{kind:'host_main',run_id:current.binding.run_id,status:'running'}:null;},
    fenceAttempt(){},fenceRun(){},async stopAttempt(){},async stopRun(){},
  };
  return manager;
}

function definition(id, mode) {
  const hasFanout = mode !== 'ordinary';
  const outputSchema = hasFanout
    ? { type: 'object', properties: { results: { type: 'array', items: { type: 'array', items: { type: 'integer' } } } }, required: ['results'], additionalProperties: false }
    : { type: 'object', properties: { summary: { type: 'string' } }, required: ['summary'], additionalProperties: false };
  const inputSchema = hasFanout
    ? { type: 'object', properties: { jobs: { type: 'array', items: { type: 'integer' } } }, required: ['jobs'], additionalProperties: false }
    : { type: 'object', properties: { task: { type: 'string' } }, required: ['task'], additionalProperties: false };
  const fanout = ['capped-one','capped-two'].includes(mode)
    ? { input: 'jobs', item_name: 'job', distribution: 'partition', batch_size: 10, result_output: 'results', scheduling: 'parallel', max_concurrency: mode==='capped-two'?2:4, join: 'all_required' }
    : mode === 'uncapped-three'
      ? { input: 'jobs', item_name: 'job', distribution: 'partition', batch_size: 1, result_output: 'results', scheduling: 'parallel', join: 'all_required' }
      : null;
  const worker = {
    id: 'worker', type: 'agent', role: 'implementer',
    executor: { kind: 'provider', provider_id: 'native-luna' },
    access: 'read_only', approval: { required: false }, retry: { max_attempts: 2 },
    input_bindings: hasFanout ? { jobs: '/inputs/jobs' } : { task: '/inputs/task' },
    prompt_template: hasFanout ? 'Process assigned jobs.' : 'Complete the assigned task.',
    outputs_schema: outputSchema,
    ...(fanout ? { subagent_count: 'auto', fanout } : {}),
  };
  return {
    ...createDraft(id, 'Native continuation regression'),
    status: 'ready',
    skill_policy: { mode: 'cooperative', implicit: 'deny', ambient_allow: [], shadowed_skill_paths: [] },
    inputs_schema: inputSchema,
    finalization: { required: true, node_id: 'final' },
    nodes: [
      { id: 'start', type: 'start' },
      worker,
      {
        id: 'final', type: 'agent', role: 'finalizer', executor: { kind: 'main' },
        access: 'read_only', approval: { required: false }, retry: { max_attempts: 1 },
        input_bindings: hasFanout ? { results: '/nodes/worker/output/results' } : { summary: '/nodes/worker/output/summary' },
        prompt_template: 'Accept the completed work.',
        outputs_schema: { type: 'object', properties: { accepted: { type: 'boolean' } }, required: ['accepted'], additionalProperties: false },
      },
      { id: 'end', type: 'end' },
    ],
    edges: [
      { id: 'start-worker', source: 'start', target: 'worker' },
      { id: 'worker-final', source: 'worker', target: 'final' },
      { id: 'final-end', source: 'final', target: 'end' },
    ],
  };
}

function sequentialNativeDefinition(id) {
  const workflow=definition(id,'ordinary');
  const first=workflow.nodes.find(node=>node.id==='worker');
  first.outputs_schema={type:'object',properties:{summary:{type:'string'}},required:['summary'],additionalProperties:false};
  const second={id:'integrator',type:'agent',role:'implementer',executor:{kind:'provider',provider_id:'native-luna'},
    access:'read_only',approval:{required:false},retry:{max_attempts:3},
    input_bindings:{task:'/nodes/worker/output/summary'},prompt_template:'Integrate the completed work.',
    outputs_schema:{type:'object',properties:{summary:{type:'string'}},required:['summary'],additionalProperties:false}};
  workflow.nodes.splice(workflow.nodes.indexOf(workflow.nodes.find(node=>node.id==='final')),0,second);
  workflow.nodes.find(node=>node.id==='final').input_bindings={summary:'/nodes/integrator/output/summary'};
  workflow.edges=[{id:'start-worker',source:'start',target:'worker'},
    {id:'worker-integrator',source:'worker',target:'integrator'},
    {id:'integrator-final',source:'integrator',target:'final'},
    {id:'final-end',source:'final',target:'end'}];
  return workflow;
}

async function startRun(f, workflow, inputs) {
  const created = await f.service.call('create', { workflow }, { human: true });
  const run = await f.service.call('start', {
    workflow_id: workflow.id,
    revision_hash: created.revision_hash,
    workspace: f.workspace,
    access: 'read_only',
    main_actor: 'root',
    native_parent_thread_id: PARENT_THREAD_ID,
    inputs,
  });
  const {runtime}=await f.service.open();
  await retainOwnedAuthority(runtime,run);
  return { run, binding: control(run) };
}

test('native_next completes an ordinary Agent and a capped fan-out with exactly one partition', async t => {
  for (const scenario of [
    { name: 'ordinary Agent', mode: 'ordinary', inputs: { task: 'one task' }, agentId: 'ordinary-child', expected: { summary: 'accepted' } },
    { name: 'one capped partition', mode: 'capped-one', inputs: { jobs: Array.from({ length: 10 }, (_, index) => index) }, agentId: 'capped-child' },
  ]) {
    await t.test(scenario.name, async t => {
      const expected = scenario.expected ?? { results: [scenario.inputs.jobs] };
      const observed = [];
      const f = await fixture(t, async ids => {
        observed.push([...ids]);
        return {
          status: 'completed',
          agent_id: ids[0],
          turn_id: 'turn-' + scenario.agentId,
          result: scenario.mode === 'ordinary' ? expected : scenario.inputs.jobs,
        };
      });
      const workflow = definition('native-' + scenario.mode, scenario.mode);
      const { run, binding } = await startRun(f, workflow, scenario.inputs);
      const handoff = await f.service.call('native_next', binding);
      assert.equal(handoff.status, 'native_handoff');
      assert.deepEqual(handoff.packets.map(packet => packet.index), [0]);
      assert.equal(Object.hasOwn(handoff,'next_action'),false,'The internal test seam must not publish a retired receipt interface');

      const spawned = await recordNativeSpawn(f, {
        ...binding, attempt_id: handoff.attempt_id, index: 0, agent_id: scenario.agentId,
      });
      assert.equal(spawned.recorded,true);

      if (scenario.mode === 'capped-one') {
        const beforeObservation = await f.service.call('get', binding);
        const attempt = beforeObservation.nodes.worker.attempts[0];
        assert.equal(beforeObservation.nodes.worker.status, 'claimed');
        assert.equal(attempt.dispatch.receipt ?? null, null);
        assert.equal(beforeObservation.nodes.worker.output, null);
      }

      const advanced = await f.service.call('native_next', binding);
      assert.equal(advanced.next_action, 'workflow_native_next');
      assert.deepEqual(observed, [[scenario.agentId]]);
      const state = await f.service.call('get', binding);
      assert.equal(state.nodes.worker.status, 'succeeded');
      assert.deepEqual(state.nodes.worker.output, expected);
      const receipt = state.nodes.worker.attempts[0].dispatch.receipt;
      assert.deepEqual(receipt.agent_ids ?? [receipt.agent_id], [scenario.agentId]);
      assert.equal(state.nodes.final.attempts.length, 0);
      assert.equal(run.status, 'running');
    });
  }
});

test('the model-facing last native spawn stays inside Host collection until the Agent event', async t => {
  let release;
  const observed = new Promise(resolve => { release = resolve; });
  const f = await fixture(t, async ids => {
    const result = await observed;
    return { ...result, agent_id: ids[0] };
  });
  const { binding } = await startRun(f, definition('native-wait-before-collection', 'ordinary'), { task: 'one task' });
  const handoff = await f.service.call('native_next', {}, MODEL_REQUEST);
  assert.equal(handoff.registration_tool, 'workflow_native_spawned_batch');
  const expectedAgent=`/root/${handoff.packets[0].spawn_config.task_name}`;
  let settled = false;
  const pending = f.service.call('native_spawned_batch', {}, MODEL_REQUEST).finally(() => { settled = true; });

  await new Promise(resolve => setTimeout(resolve, 50));
  assert.equal(settled, false, 'The last registration must hold the model-facing call instead of returning a prompt instruction');
  release({ status: 'completed', agent_id:expectedAgent,turn_id: 'turn-waiting-child', result: { summary: 'accepted' } });
  const spawned = await pending;

  assert.equal(spawned.next_action, 'workflow_native_next');
  assert.deepEqual(spawned.next_action_args, {});
  assert.equal(spawned.journaled_spawn_count,1);
  assert.equal((await f.service.call('get', binding)).nodes.worker.status, 'succeeded');
});

test('model-facing native continuation joins one receipted Host Main job without returning a polling turn',async t=>{
  const hostMainManager=delayedReceiptHostMainManager();
  const f=await fixture(t,async ids=>({status:'completed',agent_id:ids[0],turn_id:'turn-native-complete',
    result:{summary:'accepted'}}),{hostMainManager});
  const {binding}=await startRun(f,definition('native-host-main-join','ordinary'),{task:'one task'});
  const handoff=await f.service.call('native_next',{},MODEL_REQUEST);
  const registered=await f.service.call('native_spawned_batch',{},MODEL_REQUEST);
  assert.equal(registered.next_action,'workflow_native_next');

  let firstSettled=false;
  const first=f.service.call('native_next',{},MODEL_REQUEST).finally(()=>{firstSettled=true;});
  await hostMainManager.launched;
  await new Promise(resolve=>setTimeout(resolve,20));
  assert.equal(firstSettled,false,'The model-facing call must remain inside the Host Main owner');
  assert.equal(hostMainManager.launches,1);
  assert.equal(hostMainManager.waits,1);

  await hostMainManager.fail();
  const firstResult=await first;
  assert.equal(firstResult.status,'failed');
  assert.equal((await f.service.call('get',binding)).status,'failed');
});

test('model-facing spawn registration follows the newly active Agent node after a prior Agent succeeds',async t=>{
  let observation=0;
  const f=await fixture(t,async ids=>({status:'completed',agent_id:ids[0],turn_id:`turn-${++observation}`,
    result:{summary:observation===1?'written':'integrated'}}));
  const workflow=sequentialNativeDefinition('native-model-sequential-agent-nodes');
  const {binding}=await startRun(f,workflow,{task:'one task'});

  const first=await f.service.call('native_next',{},MODEL_REQUEST);
  assert.equal(first.node_id,'worker');
  await f.service.call('native_spawned_batch',{},MODEL_REQUEST);
  const second=await f.service.call('native_next',{},MODEL_REQUEST);
  assert.equal(second.node_id,'integrator');

  const registered=await f.service.call('native_spawned_batch',{},MODEL_REQUEST);
  assert.equal(registered.journaled_spawn_count,1);
  const state=await f.service.call('get',binding);
  assert.equal(state.nodes.worker.status,'succeeded');
  assert.equal(state.nodes.integrator.status,'succeeded');
  assert.deepEqual(state.nodes.integrator.output,{summary:'integrated'});
});

test('model-facing capped fan-out releases and journals one complete concurrency window', async t => {
  const jobs = Array.from({ length: 20 }, (_, index) => index);
  let release;
  const observed = new Promise(resolve => { release = resolve; });
  const indexByAgent=new Map();
  const f = await fixture(t, async ids => {
    await observed;
    const agentId = ids[0];
    const index = indexByAgent.get(agentId);
    return { status: 'completed', agent_id: agentId, turn_id: 'turn-' + agentId,
      result: jobs.slice(index * 10, (index + 1) * 10) };
  });
  const { binding } = await startRun(f, definition('native-model-capped-two', 'capped-one'), { jobs });
  const first = await f.service.call('native_next', {}, MODEL_REQUEST);
  for(const packet of first.packets)indexByAgent.set(`/root/${packet.spawn_config.task_name}`,packet.index);
  assert.deepEqual(first.packets.map(packet => packet.index), [0, 1]);
  assert.deepEqual(first.released_packet_indices, [0, 1]);
  assert.equal(first.registration_tool, 'workflow_native_spawned_batch');

  let settled = false;
  const pending = f.service.call('native_spawned_batch', {}, MODEL_REQUEST).finally(() => { settled = true; });
  await new Promise(resolve => setTimeout(resolve, 50));
  assert.equal(settled, false, 'The final registration must enter Host collection after both exact IDs are journaled');
  release();
  const completed = await pending;
  assert.equal(completed.next_action, 'workflow_native_next');
  assert.equal(completed.journaled_spawn_count,2);
  assert.equal((await f.service.call('get', binding)).nodes.worker.status, 'succeeded');
});

test('31-item model-facing fan-out refills only the completed slot and never reissues accepted partitions', {timeout:30_000}, async t => {
  const jobs=Array.from({length:31},(_,index)=>index),waiters=[];
  const observerEntries=Array.from({length:4},()=>deferred());
  const f=await fixture(t,ids=>new Promise(resolve=>{
    const waiter={ids:[...ids],resolve};waiters.push(waiter);
    assert(waiters.length<=observerEntries.length,'Host must not observe an accepted partition again');
    observerEntries[waiters.length-1].resolve(waiter);
  }));
  const {binding}=await startRun(f,definition('native-model-rolling-window','capped-two'),{jobs});
  const agentByIndex=new Map();
  const waitForObserver=(count,operation)=>Promise.race([
    observerEntries[count-1].promise,
    operation.then(()=>{throw new Error('Host operation completed before entering its expected observer wait');}),
  ]);
  const result=index=>({status:'completed',agent_id:agentByIndex.get(index),turn_id:`turn-child-${index}`,
    result:jobs.slice(index*10,Math.min(jobs.length,(index+1)*10))});

  const first=await f.service.call('native_next',{}, MODEL_REQUEST);
  assert.deepEqual(first.packets.map(packet=>packet.index),[0,1]);
  for(const packet of first.packets)agentByIndex.set(packet.index,`/root/${packet.spawn_config.task_name}`);
  await assert.rejects(f.service.call('native_spawned_batch',{attempt_id:first.attempt_id},MODEL_REQUEST),{code:'MODEL_CONTINUATION_FIELDS'});
  assert.deepEqual((await f.service.call('get',binding)).nodes.worker.attempts[0].native_agents??{},{});

  const firstWindow=f.service.call('native_spawned_batch',{}, MODEL_REQUEST);
  await waitForObserver(1,firstWindow);assert.deepEqual(waiters[0].ids,[agentByIndex.get(0),agentByIndex.get(1)]);waiters[0].resolve(result(0));
  const refillTwo=await firstWindow;assert.deepEqual(refillTwo.packets.map(packet=>packet.index),[2]);
  agentByIndex.set(2,`/root/${refillTwo.packets[0].spawn_config.task_name}`);

  const secondWindow=f.service.call('native_spawned_batch',{}, MODEL_REQUEST);
  await waitForObserver(2,secondWindow);assert.deepEqual(waiters[1].ids,[agentByIndex.get(1),agentByIndex.get(2)]);waiters[1].resolve(result(1));
  const refillThree=await secondWindow;assert.deepEqual(refillThree.packets.map(packet=>packet.index),[3]);
  agentByIndex.set(3,`/root/${refillThree.packets[0].spawn_config.task_name}`);

  const finalWindow=f.service.call('native_spawned_batch',{}, MODEL_REQUEST);
  await waitForObserver(3,finalWindow);assert.deepEqual(waiters[2].ids,[agentByIndex.get(2),agentByIndex.get(3)]);waiters[2].resolve(result(2));
  await waitForObserver(4,finalWindow);assert.deepEqual(waiters[3].ids,[agentByIndex.get(3)]);waiters[3].resolve(result(3));
  const completed=await finalWindow;
  assert.equal(completed.next_action,'workflow_native_next');
  const state=await f.service.call('get',binding);
  assert.equal(state.nodes.worker.status,'succeeded');
  assert.deepEqual(state.nodes.worker.output.results,[jobs.slice(0,10),jobs.slice(10,20),jobs.slice(20,30),jobs.slice(30)]);
  assert.deepEqual(state.nodes.worker.attempts[0].native_agents,
    Object.fromEntries([...agentByIndex].map(([index,id])=>[String(index),id])));
});

test('native observer cannot return a polling continuation to WorkflowService', async t => {
  let inspections = 0;
  const f = await fixture(t, async ids => {
    inspections++;
    return { status: 'pending', pending_phase: 'running', agent_ids: [...ids] };
  });
  const { binding } = await startRun(f, definition('native-nonblocking-collection', 'ordinary'), { task: 'one task' });
  const handoff = await f.service.call('native_next', binding);
  await recordNativeSpawn(f, {
    ...binding, attempt_id: handoff.attempt_id, index: 0, agent_id: 'running-child',
  });

  await assert.rejects(f.service.call('native_next', binding),{code:'NATIVE_AGENT_OBSERVER_PROTOCOL'});
  assert.equal(inspections, 1);
});

test('partial out-of-order spawn journaling reports exact remaining indexes and does not reissue a sealed packet', async t => {
  const jobs = [10, 20, 30];
  const observed = [];
  const f = await fixture(t, async ids => {
    observed.push([...ids]);
    const agentId = ids[0];
    const jobIndex = Number(agentId.slice('agent-'.length));
    return { status: 'completed', agent_id: agentId, turn_id: 'turn-' + agentId, result: [jobs[jobIndex]] };
  });
  const workflow = definition('native-uncapped-three', 'uncapped-three');
  const { binding } = await startRun(f, workflow, { jobs });
  const firstHandoff = await f.service.call('native_next', binding);
  assert.deepEqual(firstHandoff.packets.map(packet => packet.index), [0, 1, 2]);
  const sealedPrompt = firstHandoff.packets.find(packet => packet.index === 1).prompt;
  const attemptId = firstHandoff.attempt_id;

  const firstJournal = await recordNativeSpawn(f, { ...binding, attempt_id: attemptId, index: 1, agent_id: 'agent-1' });
  assert.equal(firstJournal.recorded,true);
  assert.equal(Object.hasOwn(firstJournal, 'packets'), false);

  const recoveredHandoff = await f.service.call('native_next', binding);
  assert.deepEqual(recoveredHandoff.packets.map(packet => packet.index), [0, 2]);
  assert.equal(recoveredHandoff.packets.some(packet => packet.index === 1 || packet.prompt === sealedPrompt), false);

  const secondJournal = await recordNativeSpawn(f, { ...binding, attempt_id: attemptId, index: 0, agent_id: 'agent-0' });
  assert.equal(secondJournal.recorded,true);
  const finalJournal = await recordNativeSpawn(f, { ...binding, attempt_id: attemptId, index: 2, agent_id: 'agent-2' });
  assert.equal(finalJournal.recorded,true);
  assert.deepEqual(observed, []);

  const advanced = await f.service.call('native_next', binding);
  assert.equal(advanced.next_action, 'workflow_native_next');
  assert.deepEqual((await f.service.call('get', binding)).nodes.worker.output.results, [[10], [20], [30]]);
  assert.deepEqual(observed[0], ['agent-0', 'agent-1', 'agent-2']);
  assert.equal(observed.length, 3);
});

test('invalid capped result cannot seal before validation', async t => {
  const jobs = Array.from({ length: 10 }, (_, index) => index);
  let observations = 0;
  const f = await fixture(t, async ids => {
    observations++;
    return observations === 1
      ? { status: 'completed', agent_id: ids[0], turn_id: 'invalid-turn', result: { invalid: true } }
      : { status: 'completed', agent_id: ids[0], turn_id: 'repaired-turn', result: jobs };
  });
  const workflow = definition('native-capped-invalid', 'capped-one');
  const { binding } = await startRun(f, workflow, { jobs });
  const handoff = await f.service.call('native_next', binding);
  const attemptId = handoff.attempt_id;
  await recordNativeSpawn(f, { ...binding, attempt_id: attemptId, index: 0, agent_id: 'repairable-child' });

  const invalid = await f.service.call('native_next', binding);
  assert.equal(invalid.status, 'native_agent_invalid_result');
  assert.equal(invalid.next_action, 'repair_recorded_agent');
  assert.equal(invalid.turn_id, 'invalid-turn');
  const rejectedState = await f.service.call('get', binding);
  const rejectedAttempt = rejectedState.nodes.worker.attempts[0];
  assert.equal(rejectedState.nodes.worker.status, 'claimed');
  assert.equal(rejectedState.nodes.worker.output, null);
  assert.equal(rejectedAttempt.dispatch.receipt ?? null, null);
  assert.equal(Object.keys(rejectedAttempt.native_parallel_results ?? {}).length, 0);
  assert.equal(rejectedAttempt.native_rejected_turns[0].turn_id, 'invalid-turn');

  const repaired = await f.service.call('native_next', binding);
  assert.equal(repaired.next_action, 'workflow_native_next');
  const finalState = await f.service.call('get', binding);
  assert.equal(finalState.nodes.worker.status, 'succeeded');
  assert.deepEqual(finalState.nodes.worker.output.results, [jobs]);
  assert.equal(observations, 2);
});

test('uncapped native fan-out retains a valid sibling across same-child repair and exhausts pinned correction budget', async t => {
  const jobs = [10, 20, 30];
  const observed = [];
  let badTurns = 0;
  const f = await fixture(t, async ids => {
    observed.push([...ids]);
    const id = ids[0];
    if (id === 'agent-1') return ++badTurns === 1
      ? { status: 'completed', agent_id: id, turn_id: 'bad-1', result: { wrong: true } }
      : { status: 'completed', agent_id: id, turn_id: 'fixed-1', result: [20] };
    const index = Number(id.slice(-1));
    return { status: 'completed', agent_id: id, turn_id: `good-${index}`, result: [jobs[index]] };
  });
  const { binding } = await startRun(f, definition('native-uncapped-repair', 'uncapped-three'), { jobs });
  const handoff = await f.service.call('native_next', binding);
  for (let index = 0; index < 3; index++) await recordNativeSpawn(f, {
    ...binding, attempt_id: handoff.attempt_id, index, agent_id: `agent-${index}`,
  });
  const rejected = await f.service.call('native_next', binding);
  assert.equal(rejected.next_action, 'repair_recorded_agent');
  assert.equal(rejected.agent_id, 'agent-1');
  assert.equal(rejected.repair_remaining, 1);
  assert.doesNotMatch(rejected.repair_prompt, /bad-1/);
  assert.match(rejected.repair_prompt, /Result schema/);
  assert.doesNotMatch(rejected.repair_prompt, /same recorded Agent|"outcome":"blocked"/);
  assert.doesNotMatch(rejected.repair_prompt, /Process assigned jobs|\[10,20,30\]/);
  assert.deepEqual((await f.service.call('get', binding)).nodes.worker.attempts[0].native_parallel_results[0],
    { agent_id: 'agent-0', result: [10] });
  await f.service.call('native_next', binding);
  const state = await f.service.call('get', binding);
  assert.deepEqual(state.nodes.worker.output.results, [[10], [20], [30]]);
  assert.deepEqual(observed[0], ['agent-0', 'agent-1', 'agent-2']);
  assert.ok(observed.slice(1).every(ids => !ids.includes('agent-0')), 'Validated sibling must never be observed again');
  assert.deepEqual(Object.values(state.nodes.worker.attempts[0].native_agents), ['agent-0', 'agent-1', 'agent-2']);
});

test('repeated malformed native result stops same-child repair but leaves an explicit node-attempt retry', async t => {
  let turn = 0;
  const f = await fixture(t, async ids => ({ status: 'completed', agent_id: ids[0], turn_id: `bad-${++turn}`, result: { wrong: true } }));
  const { binding } = await startRun(f, definition('native-repair-limit', 'ordinary'), { task: 'test' });
  const handoff = await f.service.call('native_next', binding);
  await recordNativeSpawn(f, { ...binding, attempt_id: handoff.attempt_id, index: 0, agent_id: 'same-child' });
  const first = await f.service.call('native_next', binding);
  assert.equal(first.next_action, 'repair_recorded_agent');
  assert.equal(first.repair_remaining, 1);
  const exhausted = await f.service.call('native_next', binding);
  assert.equal(exhausted.status, 'native_agent_repair_exhausted');
  assert.equal(exhausted.next_action, null);
  assert.equal(exhausted.completion_satisfied,false);
  assert.equal(exhausted.recovery_required,true);
  assert.equal(exhausted.agent_id, 'same-child');
  assert.match(exhausted.reason, /wrong|summary/i);
  assert.equal(turn, 2);
  const failedState=await f.service.call('get', binding);
  assert.equal(failedState.nodes.worker.status, 'failed');
  assert.equal(failedState.completion_satisfied,false);
  assert.equal(failedState.recovery_required,true);
  const { runtime } = await f.service.open();
  const previous=failedState.nodes.worker.attempts.at(-1);
  const retried=await runtime.retryNode(binding.run_id,{...binding,node_id:'worker',reconciliation:{attempt_id:previous.id,
    dispatch_request_id:previous.dispatch.request_id,outcome:'explicit_retry',evidence:[{kind:'host_protocol_repaired'}]}});
  assert.equal(retried.status,'running');
  assert.equal(retried.nodes.worker.status,'ready');
  assert.equal(retried.nodes.worker.attempts.length,1,'Retry releases a new attempt without rewriting the failed journal');
});

test('explicit per-item retry inherits accepted siblings and resets the fresh Agent correction allowance', async t => {
  const jobs=Array.from({length:10},(_,index)=>index);let firstTurns=0,retryTurns=0;
  const f=await fixture(t,async ids=>{
    if(ids[0]==='first-child'){
      firstTurns++;
      return {status:'completed',agent_id:ids[0],turn_id:`first-${firstTurns}`,result:{items:firstTurns===1
        ?jobs.map((job,index)=>index===7?{outcome:'blocked',block_reason:'item 7 still needs work'}:{outcome:'completed',result:[job]})
        :[{outcome:'blocked',block_reason:'item 7 still needs work'}]}};
    }
    return {status:'completed',agent_id:ids[0],turn_id:`second-invalid-${++retryTurns}`,result:{wrong:true}};
  });
  const workflow=definition('native-per-item-explicit-retry','capped-one');
  const worker=workflow.nodes.find(node=>node.id==='worker');
  worker.retry.max_attempts=3;worker.fanout.result_mode='per_item';
  const {binding}=await startRun(f,workflow,{jobs});
  const first=await f.service.call('native_next',binding);
  await recordNativeSpawn(f,{...binding,attempt_id:first.attempt_id,index:0,agent_id:'first-child'});
  const firstRepair=await f.service.call('native_next',binding);
  assert.equal(firstRepair.repair_remaining,2);
  await f.service.call('native_followed_up',firstRepair.next_action_args);
  const secondRepair=await f.service.call('native_next',binding);
  assert.equal(secondRepair.repair_remaining,1);
  await f.service.call('native_followed_up',secondRepair.next_action_args);
  const exhausted=await f.service.call('native_next',binding);
  assert.equal(exhausted.status,'native_agent_repair_exhausted');
  const failed=await f.service.call('get',binding),previous=failed.nodes.worker.attempts.at(-1);
  assert.deepEqual(Object.keys(previous.native_item_results).map(Number),[0,1,2,3,4,5,6,8,9]);
  await f.service.call('retry_node',{...binding,node_id:'worker',reconciliation:{attempt_id:previous.id,
    dispatch_request_id:previous.dispatch.request_id,outcome:'explicit_retry',evidence:[{kind:'fresh_attempt'}]}});
  const retry=await f.service.call('native_next',binding);
  assert.equal(retry.packets.length,1);
  const retryBundle=JSON.parse(await readFile(retry.packets[0].task_bundle_path,'utf8'));
  assert.equal(retryBundle.result_schema.properties.items.minItems,1);
  assert.equal(retryBundle.result_schema.properties.items.maxItems,1);
  assert.equal(retryBundle.verified_files.length,0);
  await recordNativeSpawn(f,{...binding,attempt_id:retry.attempt_id,index:0,agent_id:'second-child'});
  const rejected=await f.service.call('native_next',binding);
  assert.equal(rejected.next_action,'repair_recorded_agent');
  assert.equal(rejected.repair_remaining,2,'A prior failed attempt must not consume this Agent correction budget');
  const retried=await f.service.call('get',binding),attempt=retried.nodes.worker.attempts.at(-1);
  assert.deepEqual(attempt.inherited_native_item_indices,[0,1,2,3,4,5,6,8,9]);
  await f.service.call('native_followed_up',rejected.next_action_args);
  const observedRepairTurn=await f.service.call('native_next',binding);
  assert.equal(observedRepairTurn.next_action,'repair_recorded_agent',
    'An acknowledged repair must be observed before another incremental packet is generated for its unresolved item');
  assert.equal(observedRepairTurn.turn_id,'second-invalid-2');
  assert.equal(observedRepairTurn.repair_remaining,1);
  assert.equal(retryTurns,2);
  assert.equal((await f.service.call('get',binding)).nodes.worker.attempts.at(-1).native_rejected_turns[0].count,2);
});

for (const scheduling of ['serial', 'parallel', 'capped_parallel']) {
  test(`explicit per-item retry closes the ${scheduling} join with inherited siblings and exact evidence`, async t => {
    const jobs=Array.from({length:10},(_,index)=>index);let turns=0;
    const f=await fixture(t,async ids=>({status:'completed',agent_id:ids[0],turn_id:`turn-${++turns}`,
      result:{items:ids[0]==='retry-child'?[{outcome:'completed',result:[7]}]
        :(turns===1?jobs:[7]).map(job=>job===7?{outcome:'blocked',block_reason:'only item 7 needs work'}
          :{outcome:'completed',result:[job]})}}));
    const workflow=definition(`retry-join-${scheduling}`,'capped-one'),worker=workflow.nodes.find(node=>node.id==='worker');
    worker.fanout.result_mode='per_item';worker.retry.max_attempts=2;
    if(scheduling==='serial'){worker.fanout.scheduling='serial';delete worker.fanout.max_concurrency;}
    if(scheduling==='parallel')delete worker.fanout.max_concurrency;
    const {binding}=await startRun(f,workflow,{jobs});
    const first=await f.service.call('native_next',binding);
    await recordNativeSpawn(f,{...binding,attempt_id:first.attempt_id,index:0,agent_id:'failed-child'});
    const repair=await f.service.call('native_next',binding);
    await f.service.call('native_followed_up',repair.next_action_args);
    assert.equal((await f.service.call('native_next',binding)).status,'native_agent_repair_exhausted');
    const failed=await f.service.call('get',binding),previous=failed.nodes.worker.attempts.at(-1);
    const accepted=structuredClone(previous.native_item_results);
    await f.service.call('retry_node',{...binding,node_id:'worker',reconciliation:{attempt_id:previous.id,
      dispatch_request_id:previous.dispatch.request_id,outcome:'explicit_retry',evidence:[{kind:'fresh_attempt'}]}});
    const retry=await f.service.call('native_next',binding);
    const bundle=JSON.parse(await readFile(retry.packets[0].task_bundle_path,'utf8'));
    assert.equal(bundle.result_schema.properties.items.minItems,1);
    await recordNativeSpawn(f,{...binding,attempt_id:retry.attempt_id,index:0,agent_id:'retry-child'});
    await f.service.call('native_next',binding);
    const state=await f.service.call('get',binding),attempt=state.nodes.worker.attempts.at(-1);
    assert.equal(state.nodes.worker.status,'succeeded');
    assert.deepEqual(state.nodes.worker.output.results,jobs.map(job=>[job]));
    for(const [index,result]of Object.entries(accepted))assert.deepEqual(attempt.native_item_results[index],result);
    assert.equal(attempt.managed_native_results.length,1);
    assert.equal(attempt.managed_native_results[0].result_sha256,digest(canonicalJSON(jobs.map(job=>[job]))));
    assert.equal(state.nodes.final.status,'ready','Only the verified complete join releases its successor');
    assert.equal(turns,3,'Accepted siblings require no new observation or model turn');
    const {runtime}=await f.service.open();
    const final=await runtime.claimHostMain(binding.run_id,{...binding,node_id:'final',owner:'root',request_id:'claim-final'});
    const finalArgs={...binding,node_id:'final',attempt_id:final.attempt_id,lease_token:final.lease_token};
    const request_id=`dispatch-${final.attempt_id}`;
    await runtime.recordHostMainDispatchIntent(binding.run_id,{...finalArgs,request_id,envelope_hash:digest(canonicalJSON(final))});
    await runtime.recordHostMainDispatchReceipt(binding.run_id,{...finalArgs,request_id,receipt:{
      invocation_id:`fixture-${final.attempt_id}`,executor:'codex-app-server-host-main',executable_sha256:'a'.repeat(64),
      model:'fixture-main',effort:'medium',main_actor:'root',session_id:`logical-main-${binding.run_id}`,call_chain_id:`workflow-run-${binding.run_id}`}});
    const proposal={status:'succeeded',summary:'Fixture accepts verified results',structured_output:{accepted:true},
      artifacts:[],evidence:[{kind:'fixture_acceptance'}],changed_paths:[],outside_paths:[]};
    const saved=await runtime.runs.saveExecutorResult(binding.run_id,final.attempt_id,proposal);
    await runtime.recordExecutorEvent(binding.run_id,{...finalArgs,event:{kind:'result_proposed',metadata:{...saved,final_acceptance_required:true}}});
    assert.equal((await runtime.completeHostMainResult(binding.run_id,finalArgs,{accepted:true})).status,'succeeded');
  });
}

for(const scheduling of ['serial','parallel','capped_parallel']){
test(`explicit per-item ${scheduling} retry completes after omitting a fully inherited partition`,async t=>{
  const jobs=Array.from({length:20},(_,index)=>index);let badTurns=0;
  const f=await fixture(t,async ids=>{
    const id=ids[0];
    if(id==='first-good')return {status:'completed',agent_id:id,turn_id:'good',result:{items:jobs.slice(0,10)
      .map(job=>({outcome:'completed',result:[job]}))}};
    if(id==='retry-child')return {status:'completed',agent_id:id,turn_id:'retry-good',result:{items:jobs.slice(10)
      .map(job=>({outcome:'completed',result:[job]}))}};
    badTurns++;
    return {status:'completed',agent_id:id,turn_id:`bad-${badTurns}`,result:{items:jobs.slice(10)
      .map(()=>({outcome:'blocked',block_reason:'second partition still needs work'}))}};
  });
  const workflow=definition(`native-full-partition-${scheduling}-retry`,'capped-two');
  const worker=workflow.nodes.find(node=>node.id==='worker');
  worker.retry.max_attempts=3;worker.fanout.result_mode='per_item';
  if(scheduling==='serial'){worker.fanout.scheduling='serial';delete worker.fanout.max_concurrency;}
  if(scheduling==='parallel')delete worker.fanout.max_concurrency;
  const {binding}=await startRun(f,workflow,{jobs});
  const first=await f.service.call('native_next',binding);
  await recordNativeSpawn(f,{...binding,attempt_id:first.attempt_id,index:0,agent_id:'first-good'});
  if(scheduling==='serial')assert.deepEqual((await f.service.call('native_next',binding)).packets.map(packet=>packet.index),[1]);
  await recordNativeSpawn(f,{...binding,attempt_id:first.attempt_id,index:1,agent_id:'first-bad'});
  const repair1=await f.service.call('native_next',binding);
  assert.equal(repair1.agent_id,'first-bad');
  await f.service.call('native_followed_up',repair1.next_action_args);
  const repair2=await f.service.call('native_next',binding);
  await f.service.call('native_followed_up',repair2.next_action_args);
  assert.equal((await f.service.call('native_next',binding)).status,'native_agent_repair_exhausted');
  const failed=await f.service.call('get',binding),previous=failed.nodes.worker.attempts.at(-1);
  assert.deepEqual(Object.keys(previous.native_item_results).map(Number),jobs.slice(0,10));
  await f.service.call('retry_node',{...binding,node_id:'worker',reconciliation:{attempt_id:previous.id,
    dispatch_request_id:previous.dispatch.request_id,outcome:'explicit_retry',evidence:[{kind:'fresh_attempt'}]}});
  const retry=await f.service.call('native_next',binding);
  assert.deepEqual(retry.packets.map(packet=>packet.index),[1]);
  const bundle=JSON.parse(await readFile(retry.packets[0].task_bundle_path,'utf8'));
  assert.equal(bundle.result_schema.properties.items.minItems,10);
  assert.equal(bundle.verified_files.length,0);
  await recordNativeSpawn(f,{...binding,attempt_id:retry.attempt_id,index:1,agent_id:'retry-child'});
  await f.service.call('native_next',binding);
  const state=await f.service.call('get',binding),attempt=state.nodes.worker.attempts.at(-1);
  assert.equal(state.nodes.worker.status,'succeeded');
  assert.deepEqual(state.nodes.worker.output.results,jobs.map(job=>[job]));
  assert.deepEqual(Object.keys(attempt.native_agents),['1']);
  assert.equal(attempt.managed_native_results.length,1);
  assert.equal(attempt.managed_native_results[0].result_sha256,digest(canonicalJSON(jobs.slice(10).map(job=>[job]))));
});
}

test('all-inherited serial per-item retry records an empty trusted dispatch and completes idempotently',async t=>{
  const jobs=[10,20,30];let observerCalls=0;
  const f=await fixture(t,async ids=>{
    observerCalls++;
    assert.fail(`All items are inherited; native child ${ids[0]} must not be observed`);
  });
  const workflow=definition('native-serial-all-inherited-retry','capped-one');
  const worker=workflow.nodes.find(node=>node.id==='worker');
  worker.fanout.result_mode='per_item';worker.fanout.scheduling='serial';delete worker.fanout.max_concurrency;
  const {run,binding}=await startRun(f,workflow,{jobs});
  const first=await f.service.call('native_next',binding);
  assert.deepEqual(first.packets.map(packet=>packet.index),[0]);
  await recordNativeSpawn(f,{...binding,attempt_id:first.attempt_id,index:0,agent_id:'seed-serial-child'});

  const seed=await nativeAttemptContext(f,{...binding,attempt_id:first.attempt_id});
  await seed.runtime.recordNativeItemResults(run.run_id,{...seed.binding,index:0,agent_id:'seed-serial-child',turn_id:'seed-complete-turn',
    target_indices:jobs.map((_job,index)=>index),result:{items:jobs.map(job=>({outcome:'completed',result:[job]}))}});
  await f.service.call('fail_node',{...seed.binding,error:{code:'TEST_RETRY_SEED',message:'Retry after all per-item results were journaled'}});
  const failed=await f.service.call('get',binding);
  const previous=failed.nodes.worker.attempts.at(-1);
  assert.equal(failed.nodes.worker.status,'failed');
  assert.deepEqual(Object.keys(previous.native_item_results).map(Number),[0,1,2]);

  await f.service.call('retry_node',{...binding,node_id:'worker',reconciliation:{attempt_id:previous.id,
    dispatch_request_id:previous.dispatch.request_id,outcome:'explicit_retry',evidence:[{kind:'all_items_already_accepted'}]}});
  const recovered=await f.service.call('native_next',binding);
  assert.equal(recovered.node_id,'worker');
  assert.equal(recovered.next_action,'workflow_native_next');
  const completed=await f.service.call('get',binding);
  const attempt=completed.nodes.worker.attempts.at(-1);
  assert.equal(completed.nodes.worker.status,'succeeded');
  assert.deepEqual(completed.nodes.worker.output.results,jobs.map(job=>[job]));
  assert.deepEqual(Object.keys(attempt.native_agents??{}),[],'The all-inherited retry must not spawn a child');
  assert.deepEqual(attempt.native_serial_results??[],[]);
  assert.deepEqual(attempt.dispatch.receipt.agent_ids,[]);
  assert.deepEqual(attempt.dispatch.receipt.subagent_dispatch_ids,[]);
  assert.deepEqual(attempt.dispatch.receipt.subagent_plan,{resolved_count:0,input_sha256:digest(canonicalJSON(jobs)),assignments:[]});
  assert.deepEqual(attempt.managed_native_results,[]);
  assert.deepEqual(attempt.completion.evidence.find(item=>item.kind==='subagent_pool'),
    {kind:'subagent_pool',resolved_count:0,dispatch_ids:[]});
  assert.deepEqual(attempt.completion.evidence.filter(item=>item.kind==='native_agent_result'),[]);
  assert.equal(completed.nodes.final.status,'ready','The accepted full join must release the successor');
  assert.equal(observerCalls,0);

  const replay=await nativeAttemptContext(f,{...binding,attempt_id:attempt.id});
  await replay.runtime.recordDispatchReceipt(run.run_id,{...replay.binding,request_id:attempt.dispatch.request_id,
    receipt:attempt.dispatch.receipt});
  await replay.runtime.completeNode(run.run_id,{...replay.binding,completion:attempt.completion});
  let afterReplay=await f.service.call('get',binding);
  assert.deepEqual(afterReplay.nodes.worker.output.results,jobs.map(job=>[job]));
  assert.deepEqual(afterReplay.nodes.worker.attempts.at(-1).managed_native_results,[]);

  const final=await replay.runtime.claimHostMain(run.run_id,{...binding,node_id:'final',owner:'root',request_id:'all-inherited-final'});
  const finalArgs={...binding,node_id:'final',attempt_id:final.attempt_id,lease_token:final.lease_token};
  const request_id=`dispatch-${final.attempt_id}`;
  await replay.runtime.recordHostMainDispatchIntent(run.run_id,{...finalArgs,request_id,envelope_hash:digest(canonicalJSON(final))});
  await replay.runtime.recordHostMainDispatchReceipt(run.run_id,{...finalArgs,request_id,receipt:{
    invocation_id:`fixture-${final.attempt_id}`,executor:'codex-app-server-host-main',executable_sha256:'b'.repeat(64),
    model:'fixture-main',effort:'medium',main_actor:'root',session_id:`logical-main-${run.run_id}`,call_chain_id:`workflow-run-${run.run_id}`}});
  const proposal={status:'succeeded',summary:'Fixture accepts inherited serial results',structured_output:{accepted:true},
    artifacts:[],evidence:[{kind:'fixture_acceptance'}],changed_paths:[],outside_paths:[]};
  const saved=await replay.runtime.runs.saveExecutorResult(run.run_id,final.attempt_id,proposal);
  await replay.runtime.recordExecutorEvent(run.run_id,{...finalArgs,event:{kind:'result_proposed',metadata:{...saved,final_acceptance_required:true}}});
  assert.equal((await replay.runtime.completeHostMainResult(run.run_id,finalArgs,{accepted:true})).status,'succeeded');
  afterReplay=await f.service.call('get',binding);
  assert.equal(afterReplay.nodes.final.status,'succeeded');
  assert.equal(afterReplay.status,'succeeded');
  assert.equal(observerCalls,0);
});

test('parallel siblings each retain their own pinned correction allowance', async t => {
  const jobs = [10, 20, 30], turns = new Map(), repairs = [];
  const f = await fixture(t, async ids => {
    const id = ids[0], count = (turns.get(id) ?? 0) + 1;
    turns.set(id, count);
    if (id !== 'agent-2' && count === 1) return {
      status: 'invalid', agent_id: id, turn_id: `${id}-bad`, reason: `Invalid ${id} fields`,
    };
    return { status: 'completed', agent_id: id, turn_id: `${id}-good`, result: [jobs[Number(id.slice(-1))]] };
  });
  const { binding } = await startRun(f, definition('native-two-repairs', 'uncapped-three'), { jobs });
  const handoff = await f.service.call('native_next', binding);
  for (let index = 0; index < 3; index++) await recordNativeSpawn(f, {
    ...binding, attempt_id: handoff.attempt_id, index, agent_id: `agent-${index}`,
  });
  for (let call = 0; call < 4; call++) {
    const next = await f.service.call('native_next', binding);
    if (next.next_action === 'repair_recorded_agent') {
      repairs.push(next.agent_id);
      assert.equal(next.repair_remaining, 1);
      continue;
    }
    assert.equal(next.next_action, 'workflow_native_next');
    break;
  }
  assert.deepEqual(repairs, ['agent-0', 'agent-1']);
  assert.deepEqual((await f.service.call('get', binding)).nodes.worker.output.results, [[10], [20], [30]]);
});

test('repair exhaustion identifies only still outstanding recorded parallel siblings for controller interruption', async t => {
  const jobs = [10, 20, 30];
  let badTurns = 0;
  const f = await fixture(t, async ids => {
    const id = ids[0];
    if (id === 'agent-0') return { status: 'completed', agent_id: id, turn_id: 'good-0', result: [10] };
    if (id === 'agent-1') return { status: 'invalid', agent_id: id, turn_id: `bad-${++badTurns}`, reason: 'Missing result field' };
    assert.fail('Outstanding sibling should not be observed before correction is exhausted');
  });
  const { binding } = await startRun(f, definition('native-exhausted-siblings', 'uncapped-three'), { jobs });
  const handoff = await f.service.call('native_next', binding);
  for (let index = 0; index < 3; index++) await recordNativeSpawn(f, {
    ...binding, attempt_id: handoff.attempt_id, index, agent_id: `agent-${index}`,
  });
  assert.equal((await f.service.call('native_next', binding)).next_action, 'repair_recorded_agent');
  const exhausted = await f.service.call('native_next', binding);
  assert.equal(exhausted.status, 'native_agent_repair_exhausted');
  assert.equal(exhausted.next_action, null);
  assert.deepEqual(exhausted.outstanding_agent_ids, ['agent-2']);
  assert.deepEqual(exhausted.controller_cleanup, { tool: 'collaboration.interrupt_agent', agent_ids: ['agent-2'] });
  assert.deepEqual((await f.service.call('get', binding)).nodes.worker.attempts[0].native_parallel_results[0],
    { agent_id: 'agent-0', result: [10] });
});

test('one ten-item native batch journals nine accepted items and repairs only the failed index in the same child', async t => {
  const jobs = Array.from({ length: 10 }, (_, index) => index);
  const observed = [];
  const f = await fixture(t, async ids => {
    observed.push([...ids]);
    return { status: 'completed', agent_id: ids[0], turn_id: `turn-${observed.length}`, result: {
      items: observed.length === 1
        ? jobs.map((job, item_index) => item_index === 7
          ? { outcome: 'blocked', block_reason: 'Scenario 7 needs correction' }
          : { outcome: 'completed', result: [job] })
        : [{ outcome: 'completed', result: [7] }],
    } };
  });
  const workflow = definition('native-per-item-ten', 'capped-one');
  workflow.nodes.find(node => node.id === 'worker').fanout.result_mode = 'per_item';
  const { binding } = await startRun(f, workflow, { jobs });
  const handoff = await f.service.call('native_next', binding);
  const bundle=JSON.parse(await readFile(handoff.packets[0].task_bundle_path,'utf8'));
  assert.equal(Object.hasOwn(bundle,'item_positions'),false);
  assert.doesNotMatch(JSON.stringify(bundle.result_schema),/"item_index"/);
  assert.equal(bundle.result_schema.properties.items.minItems,10);
  assert.equal(bundle.result_schema.properties.items.maxItems,10);
  assert.equal(handoff.packets[0].spawn_config.fork_turns, 'none');
  await recordNativeSpawn(f, { ...binding, attempt_id: handoff.attempt_id, index: 0, agent_id: 'batch-child' });
  const partial = await f.service.call('native_next', binding);
  assert.equal(partial.next_action, 'repair_recorded_agent');
  assert.equal(partial.agent_id, 'batch-child');
  assert.deepEqual(partial.unresolved_item_indices, [7]);
  assert.deepEqual(partial.accepted_item_indices, [0,1,2,3,4,5,6,8,9]);
  assert.match(partial.repair_prompt, /Task bundle:/);
  assert.doesNotMatch(partial.repair_prompt,/Host-selected unresolved positions/);
  assert.equal(partial.followup_config.target,'batch-child');
  assert.equal(partial.item_index,7);
  assert.deepEqual(partial.next_action_args,binding);
  const repairTask=JSON.parse(await readFile(JSON.parse(partial.followup_config.message.match(/Task bundle: ("[^\n]+")/)[1]),'utf8'));
  assert.equal(Object.hasOwn(repairTask,'item_positions'),false);
  assert.equal(repairTask.result_schema.properties.items.minItems,1);
  assert.equal(repairTask.result_schema.properties.items.maxItems,1);
  const repairInputs=JSON.parse(repairTask.task.match(/\nInputs:\n([^\n]+)/)?.[1]??'null');
  const repairJobsPath=JSON.parse(repairInputs.jobs.match(/local file at (".*") \(format: json\)\./)?.[1]??'null');
  assert.deepEqual(JSON.parse(await readFile(repairJobsPath,'utf8')),[7]);
  await f.service.call('native_followed_up',partial.next_action_args);
  const prior = await f.service.call('get', binding);
  assert.equal(Object.keys(prior.nodes.worker.attempts[0].native_item_results).length, 9);
  assert.equal(prior.nodes.worker.attempts[0].native_item_results[7], undefined);
  assert.deepEqual(prior.nodes.worker.attempts[0].native_repair_followups['0:1'].item_indices,[7]);
  const completed = await f.service.call('native_next', binding);
  assert.equal(completed.next_action, 'workflow_native_next');
  const state = await f.service.call('get', binding);
  assert.deepEqual(state.nodes.worker.output.results, jobs.map(job => [job]));
  assert.deepEqual(observed, [['batch-child'], ['batch-child']]);
  assert.deepEqual(Object.values(state.nodes.worker.attempts[0].native_agents), ['batch-child']);
});

test('a schema-valid shared change is admitted as delegated work instead of retrying the local item', async t => {
  const f = await fixture(t, async ids => ({status:'completed',agent_id:ids[0],turn_id:'delegated-turn',result:{items:[{
    outcome:'delegated',block_reason:'Shared runtime work belongs to the integration owner.',
    result:{changes:'Local card and scenarios written.',shared_change:'Add the shared transform hook.'},
  }]}}));
  const workflow=definition('native-delegated-shared-change','capped-one');
  workflow.inputs_schema={type:'object',additionalProperties:false,required:['jobs'],properties:{jobs:{type:'array',minItems:1,items:{type:'object',additionalProperties:false,required:['write_paths'],properties:{write_paths:{type:'array',minItems:1,items:{type:'string'}}}}}}};
  const worker=workflow.nodes.find(node=>node.id==='worker');
  worker.access='bounded_write';worker.path_scope={binding:'run.allowed_paths'};worker.fanout.result_mode='per_item';
  worker.fanout.write_paths_field='write_paths';worker.fanout.shared_change_field='shared_change';
  worker.outputs_schema={type:'object',additionalProperties:false,required:['results'],properties:{results:{type:'array',minItems:1,items:{type:'object',additionalProperties:false,required:['changes','shared_change'],properties:{changes:{type:'string'},shared_change:{type:'string'}}}}}};
  const integrator={id:'integrator',type:'agent',role:'implementer',executor:{kind:'provider',provider_id:'native-luna'},
    access:'bounded_write',path_scope:{binding:'run.allowed_paths'},approval:{required:false},retry:{max_attempts:3},
    input_bindings:{requests:{path:'/nodes/worker/output/results',pluck:'shared_change'}},prompt_template:'Apply shared changes once.',
    outputs_schema:{type:'object',additionalProperties:false,required:['all_passed','evidence'],properties:{all_passed:{type:'boolean'},evidence:{type:'string'}}},
    completion_contract:{on_missing:'block',outcome:'validated_artifact',fail_on_false:['all_passed']}};
  workflow.nodes.splice(workflow.nodes.indexOf(workflow.nodes.find(node=>node.id==='final')),0,integrator);
  workflow.edges=[{id:'start-worker',source:'start',target:'worker'},{id:'worker-integrator',source:'worker',target:'integrator'},
    {id:'integrator-final',source:'integrator',target:'final'},{id:'final-end',source:'final',target:'end'}];
  workflow.nodes.find(node=>node.id==='final').input_bindings={evidence:'/nodes/integrator/output/evidence'};
  const created=await f.service.call('create',{workflow},{human:true});
  const run=await f.service.call('start',{workflow_id:workflow.id,revision_hash:created.revision_hash,workspace:f.workspace,
    access:'bounded_write',allowed_paths:['.'],main_actor:'root',native_parent_thread_id:PARENT_THREAD_ID,
    inputs:{jobs:[{write_paths:['cards/one.ts']}]}});
  const binding=control(run),handoff=await f.service.call('native_next',binding);
  assert.deepEqual(handoff.result_schema.properties.items.items.properties.outcome.enum,['completed','delegated','blocked']);
  await recordNativeSpawn(f,{...binding,attempt_id:handoff.attempt_id,index:0,agent_id:'delegating-child'});
  const continued=await f.service.call('native_next',binding);
  assert.equal(continued.next_action,'workflow_native_next');
  const state=await f.service.call('get',binding),attempt=state.nodes.worker.attempts[0];
  assert.equal(state.nodes.worker.status,'succeeded');
  assert.deepEqual(state.nodes.worker.output.results,[{changes:'Local card and scenarios written.',shared_change:'Add the shared transform hook.'}]);
  assert.equal(attempt.native_item_results[0].delegated,true);
  assert.match(attempt.native_item_results[0].delegation_reason,/integration owner/);
});

test('incremental ten-item delivery checkpoints one item per turn in the same child and repairs only the failed item', async t => {
  const jobs = Array.from({ length: 10 }, (_, index) => index);
  const observed = [];
  let blockedSeven = false;
  const f = await fixture(t, async ids => {
    const state = await f.service.call('get', binding);
    const attempt = state.nodes.worker.attempts[0];
    const unresolved = jobs.find(index => !attempt.native_item_results?.[index]);
    observed.push({ ids: [...ids], unresolved });
    if (unresolved === 7 && !blockedSeven) {
      blockedSeven = true;
      return { status: 'completed', agent_id: ids[0], turn_id: 'turn-7-blocked', result: {
        items: [{ outcome: 'blocked', block_reason: 'Scenario 7 needs correction' }],
      } };
    }
    return { status: 'completed', agent_id: ids[0], turn_id: `turn-${unresolved}`, result: {
      items: [{ outcome: 'completed', result: [unresolved] }],
    } };
  });
  const workflow = definition('native-per-item-incremental-ten', 'capped-one');
  const worker = workflow.nodes.find(node => node.id === 'worker');
  worker.fanout.result_mode = 'per_item';
  worker.fanout.item_delivery = 'incremental';
  worker.retry.max_attempts = 3;
  let binding;
  ({ binding } = await startRun(f, workflow, { jobs }));

  const handoff = await f.service.call('native_next', binding);
  assert.deepEqual(handoff.packets.map(packet => packet.index), [0]);
  assert.equal(handoff.packets[0].spawn_config.fork_turns, 'none');
  const firstBundle = JSON.parse(await readFile(handoff.packets[0].task_bundle_path, 'utf8'));
  assert.equal(Object.hasOwn(firstBundle,'item_positions'),false);
  assert.equal(firstBundle.result_schema.properties.items.minItems,1);
  assert.equal(firstBundle.result_schema.properties.items.maxItems,1);
  const firstInputs = JSON.parse(firstBundle.task.match(/\nInputs:\n([^\n]+)/)?.[1] ?? 'null');
  const firstJobsPath = JSON.parse(firstInputs.jobs.match(/local file at (".*") \(format: json\)\./)?.[1] ?? 'null');
  assert.deepEqual(JSON.parse(await readFile(firstJobsPath, 'utf8')), [0]);
  await recordNativeSpawn(f, {
    ...binding, attempt_id: handoff.attempt_id, index: 0, agent_id: 'incremental-child',
  });

  for (let expected = 0; expected < jobs.length; expected++) {
    let next = await f.service.call('native_next', binding);
    if (expected === 7) {
      assert.equal(next.next_action, 'repair_recorded_agent');
      assert.equal(next.agent_id, 'incremental-child');
      assert.deepEqual(next.accepted_item_indices, [0,1,2,3,4,5,6]);
      assert.deepEqual(next.unresolved_item_indices, [7,8,9]);
      const beforeRepair = await f.service.call('get', binding);
      assert.equal(Object.keys(beforeRepair.nodes.worker.attempts[0].native_item_results).length, 7);
      await f.service.call('native_followed_up',next.next_action_args);
      next = await f.service.call('native_next', binding);
    }
    if (expected < jobs.length - 1) {
      assert.equal(next.next_action, 'continue_recorded_agent');
      assert.equal(next.followup_config.target, 'incremental-child');
      assert.equal(next.item_index, expected + 1);
      assert.deepEqual(next.next_action_args,binding);
      const taskPath = JSON.parse(next.followup_config.message.match(/Task bundle: ("[^\n]+")/)[1]);
      const task = JSON.parse(await readFile(taskPath, 'utf8'));
      assert.equal(Object.hasOwn(task,'item_positions'),false);
      const taskInputs = JSON.parse(task.task.match(/\nInputs:\n([^\n]+)/)?.[1] ?? 'null');
      const taskJobsPath = JSON.parse(taskInputs.jobs.match(/local file at (".*") \(format: json\)\./)?.[1] ?? 'null');
      assert.deepEqual(JSON.parse(await readFile(taskJobsPath, 'utf8')), [expected + 1]);
      if (expected === 0) {
        const recovered = await f.service.call('native_next', binding);
        assert.equal(recovered.status, 'native_item_continuation_pending');
        assert.deepEqual(recovered.followup_config, next.followup_config);
        assert.deepEqual(recovered.next_action_args, next.next_action_args);
      }
      const followed = await f.service.call('native_followed_up', next.next_action_args);
      assert.equal(followed.next_action, 'workflow_native_next');
      assert.deepEqual(followed.next_action_args,binding);
    } else {
      assert.equal(next.next_action, 'workflow_native_next');
    }
  }

  const state = await f.service.call('get', binding);
  assert.deepEqual(state.nodes.worker.output.results, jobs.map(job => [job]));
  assert.deepEqual(Object.values(state.nodes.worker.attempts[0].native_agents), ['incremental-child']);
  assert.equal(Object.keys(state.nodes.worker.attempts[0].native_followups).length, 9);
  assert.deepEqual(observed.map(item => item.ids), Array(11).fill(['incremental-child']));
  assert.deepEqual(observed.map(item => item.unresolved), [0,1,2,3,4,5,6,7,7,8,9]);
});

for (const scenario of [
  { name: 'post-seal uncapped', mode: 'uncapped-three', scheduling: 'parallel', interruptNextPreparation: true },
  { name: 'pre-seal capped', mode: 'capped-one', scheduling: 'parallel', maxConcurrency: 1 },
  { name: 'pre-seal serial', mode: 'capped-one', scheduling: 'serial' },
]) {
  test(`incremental ${scenario.name} recovery replays an undelivered repair before observing again`, async t => {
    const jobs = [10, 20, 30];
    let binding;
    let rejectedItemOne = false;
    const observed = [];
    const f = await fixture(t, async ids => {
      assert.deepEqual(ids, ['repair-replay-child']);
      const state = await f.service.call('get', binding);
      const attempt = state.nodes.worker.attempts[0];
      const itemIndex = jobs.findIndex((_, index) => !attempt.native_item_results?.[index]);
      assert.ok(itemIndex >= 0, 'The observer must only see an unresolved item');
      assert.equal(attempt.native_pending_followup ?? null, null,
        'The Host must resolve every pending follow-up before invoking the observer');
      observed.push(itemIndex);
      if (itemIndex === 1 && !rejectedItemOne) {
        rejectedItemOne = true;
        return { status: 'completed', agent_id: ids[0], turn_id: 'item-one-blocked', result: {
          items: [{ outcome: 'blocked', block_reason: 'Item 20 needs repair' }],
        } };
      }
      return { status: 'completed', agent_id: ids[0], turn_id: `item-${itemIndex}-accepted`, result: {
        items: [{ outcome: 'completed', result: [jobs[itemIndex]] }],
      } };
    });
    let failAfterRepairResult = false;
    let prepareInterrupted = false;
    if (scenario.interruptNextPreparation) {
      const originalOpen = f.service.open.bind(f.service);
      f.service.open = async (...args) => {
        const opened = await originalOpen(...args);
        const originalPrepare = opened.executor.prepare.bind(opened.executor);
        opened.executor.prepare = async (...prepareArgs) => {
          if (failAfterRepairResult && !prepareInterrupted) {
            const record = await opened.runtime.runs.read(binding.run_id);
            const attempt = record.state.nodes.worker.attempts[0];
            if (attempt.native_item_results?.[1] && !attempt.native_pending_followup) {
              prepareInterrupted = true;
              throw Object.assign(new Error('Simulated interruption after repaired result persistence'), {
                code: 'TEST_PREPARE_INTERRUPTED',
              });
            }
          }
          return originalPrepare(...prepareArgs);
        };
        return opened;
      };
    }
    const workflow = definition(`native-incremental-${scenario.name.replaceAll(' ', '-')}`, scenario.mode);
    const worker = workflow.nodes.find(node => node.id === 'worker');
    worker.fanout.batch_size = jobs.length;
    worker.fanout.result_mode = 'per_item';
    worker.fanout.item_delivery = 'incremental';
    worker.fanout.scheduling = scenario.scheduling;
    if (scenario.maxConcurrency) worker.fanout.max_concurrency = scenario.maxConcurrency;
    else if (scenario.scheduling === 'serial') delete worker.fanout.max_concurrency;
    worker.retry.max_attempts = 3;
    ({ binding } = await startRun(f, workflow, { jobs }));

    const handoff = await f.service.call('native_next', binding);
    assert.deepEqual(handoff.packets.map(packet => packet.index), [0]);
    await recordNativeSpawn(f, { ...binding, attempt_id: handoff.attempt_id, index: 0, agent_id: 'repair-replay-child' });

    const firstContinuation = await f.service.call('native_next', binding);
    assert.equal(firstContinuation.next_action, 'continue_recorded_agent');
    assert.equal(firstContinuation.item_index, 1);
    await f.service.call('native_followed_up', firstContinuation.next_action_args);

    const repair = await f.service.call('native_next', binding);
    assert.equal(repair.status, 'native_agent_blocked');
    assert.equal(repair.next_action, 'repair_recorded_agent');
    assert.equal(repair.item_index, 1);
    assert.deepEqual(observed, [0, 1]);
    const beforeRecovery = await f.service.call('get', binding);
    const beforeAttempt = beforeRecovery.nodes.worker.attempts[0];
    assert.deepEqual(beforeAttempt.native_item_results[0], {
      agent_id: 'repair-replay-child', result: [10], turn_id: 'item-0-accepted',
    });
    assert.equal(Object.hasOwn(beforeAttempt.native_item_results, '1'), false,
      'A rejected item stays unresolved until its repair is observed');
    assert.equal(beforeAttempt.native_rejected_turns[0].count, 1);
    assert.equal(beforeAttempt.native_pending_followup.index, 0);
    assert.equal(beforeAttempt.native_pending_followup.agent_id, 'repair-replay-child');
    assert.equal(beforeAttempt.native_pending_followup.item_index, 1);
    assert.match(beforeAttempt.native_pending_followup.task_bundle_sha256, /^[a-f0-9]{64}$/);
    assert.equal(beforeAttempt.native_pending_followup.followup_kind, 'repair');
    assert.equal(beforeAttempt.native_pending_followup.rejection_count, 1);

    const recoveredRepair = await f.service.call('native_next', binding);
    assert.deepEqual(recoveredRepair, repair,
      'Recovery must regenerate the exact persisted repair packet and message');
    const afterRecovery = await f.service.call('get', binding);
    const afterAttempt = afterRecovery.nodes.worker.attempts[0];
    assert.equal(afterRecovery.sequence, beforeRecovery.sequence,
      'Replaying pending delivery must not append another rejection or follow-up intent');
    assert.equal(afterAttempt.native_rejected_turns[0].count, 1);
    assert.deepEqual(afterAttempt.native_pending_followup, beforeAttempt.native_pending_followup);
    assert.deepEqual(afterAttempt.native_item_results, beforeAttempt.native_item_results,
      'Recovery must retain accepted siblings and must not accept the rejected turn');
    assert.deepEqual(observed, [0, 1], 'Recovery must not observe the undelivered repair turn');

    await f.service.call('native_followed_up', recoveredRepair.next_action_args);
    let secondContinuation;
    if (scenario.interruptNextPreparation) {
      failAfterRepairResult = true;
      await assert.rejects(f.service.call('native_next', binding), error => error.code === 'TEST_PREPARE_INTERRUPTED');
      assert.equal(prepareInterrupted, true, 'The service reached continuation preparation only after persisting the repaired item');
      failAfterRepairResult = false;
    } else {
      const repairContext = await nativeAttemptContext(f, { ...binding, attempt_id: repair.attempt_id });
      const repairResult = await repairContext.runtime.recordNativeItemResults(binding.run_id, {
        ...repairContext.binding, index: 0, agent_id: 'repair-replay-child', turn_id: 'item-1-accepted',
        target_indices: [1], result: { items: [{ outcome: 'completed', result: [20] }] },
      });
      assert.deepEqual(repairResult.accepted_item_indices, [0, 1]);
      assert.deepEqual(repairResult.unresolved_item_indices, [2]);
    }
    const interrupted = await f.service.call('get', binding);
    const interruptedAttempt = interrupted.nodes.worker.attempts[0];
    assert.equal(interruptedAttempt.native_pending_followup ?? null, null,
      'Simulate recovery after the repaired result is journaled but before the next packet intent exists');
    assert.deepEqual(interruptedAttempt.native_item_results[1], {
      agent_id: 'repair-replay-child', result: [20], turn_id: 'item-1-accepted',
    });
    assert.equal(interruptedAttempt.native_last_followup.followup_kind, 'repair');
    assert.equal(interruptedAttempt.native_last_followup.item_index, 1);
    const observedBeforeRecovery = [...observed];

    secondContinuation = await f.service.call('native_next', binding);
    assert.equal(secondContinuation.next_action, 'continue_recorded_agent');
    assert.equal(secondContinuation.item_index, 2,
      'Recovery must deliver the next incremental item after the repaired result is already accepted');
    assert.deepEqual(observed, observedBeforeRecovery, 'Recovery returns item 2 before asking the child for another turn');
    const continuationState = await f.service.call('get', binding);
    assert.equal(continuationState.nodes.worker.attempts[0].native_pending_followup.followup_kind, 'incremental');
    assert.equal(continuationState.nodes.worker.attempts[0].native_pending_followup.item_index, 2);
    await f.service.call('native_followed_up', secondContinuation.next_action_args);
    const completed = await f.service.call('native_next', binding);
    assert.equal(completed.next_action, 'workflow_native_next');
    assert.deepEqual(observed, scenario.interruptNextPreparation ? [0, 1, 1, 2] : [0, 1, 2]);

    const finalState = await f.service.call('get', binding);
    assert.equal(finalState.nodes.worker.status, 'succeeded');
    assert.deepEqual(finalState.nodes.worker.output.results, jobs.map(job => [job]));
    assert.deepEqual(finalState.nodes.worker.attempts[0].native_item_results[0], {
      agent_id: 'repair-replay-child', result: [10], turn_id: 'item-0-accepted',
    }, 'The earlier accepted sibling remains journaled after repair');
    assert.deepEqual(finalState.nodes.worker.attempts[0].native_item_results[1], {
      agent_id: 'repair-replay-child', result: [20], turn_id: 'item-1-accepted',
    });
    assert.deepEqual(finalState.nodes.worker.attempts[0].native_item_results[2], {
      agent_id: 'repair-replay-child', result: [30], turn_id: 'item-2-accepted',
    });
    assert.equal(finalState.nodes.final.status, 'ready', 'The full Host-owned item join releases the successor');
  });
}

test('uncapped parallel incremental partitions continue their recorded children, join every item and complete downstream', async t => {
  const jobs=[0,1,2,3],observed=[];
  let binding;
  const f=await fixture(t,async ids=>{
    const state=await f.service.call('get',binding);
    if(state.nodes.worker.status==='running'){
      const attempt=state.nodes.worker.attempts[0],agentId=ids[0];
      assert.notEqual(attempt.native_pending_followup?.followup_kind,'incremental',
        'The Host must resolve a pending incremental continuation before observing the old Agent turn again');
      const slot=Object.entries(attempt.native_agents??{}).find(([,id])=>id===agentId)?.[0];
      assert.notEqual(slot,undefined,'Observer must receive a journaled worker Agent');
      const assigned=jobs.slice(Number(slot)*2,Number(slot)*2+2);
      const itemIndex=assigned.find(index=>!attempt.native_item_results?.[index]);
      assert.notEqual(itemIndex,undefined,'Observer must receive a partition with an unresolved item');
      observed.push({node:'worker',agent_id:agentId,item_index:itemIndex});
      return {status:'completed',agent_id:agentId,turn_id:`${agentId}-turn-${itemIndex}`,
        result:{items:[{outcome:'completed',result:[itemIndex]}]}};
    }
    assert.equal(state.nodes.integrator.status,'running','Only the released downstream node may be observed after the join');
    observed.push({node:'integrator',agent_id:ids[0]});
    return {status:'completed',agent_id:ids[0],turn_id:'downstream-integrator-turn',result:{summary:'all joined items integrated'}};
  });
  const workflow=definition('native-per-item-incremental-uncapped','uncapped-three');
  const worker=workflow.nodes.find(node=>node.id==='worker');
  worker.fanout.batch_size=2;
  worker.fanout.result_mode='per_item';
  worker.fanout.item_delivery='incremental';
  assert.equal(Object.hasOwn(worker.fanout,'max_concurrency'),false);
  const integrator={id:'integrator',type:'agent',role:'implementer',executor:{kind:'provider',provider_id:'native-luna'},
    access:'read_only',approval:{required:false},retry:{max_attempts:2},
    input_bindings:{results:'/nodes/worker/output/results'},prompt_template:'Integrate the complete joined results.',
    outputs_schema:{type:'object',properties:{summary:{type:'string'}},required:['summary'],additionalProperties:false}};
  workflow.nodes.splice(workflow.nodes.indexOf(workflow.nodes.find(node=>node.id==='final')),0,integrator);
  workflow.edges=[{id:'start-worker',source:'start',target:'worker'},{id:'worker-integrator',source:'worker',target:'integrator'},
    {id:'integrator-final',source:'integrator',target:'final'},{id:'final-end',source:'final',target:'end'}];
  workflow.nodes.find(node=>node.id==='final').input_bindings={summary:'/nodes/integrator/output/summary'};
  const created=await f.service.call('create',{workflow},{human:true});
  const run=await f.service.call('start',{workflow_id:workflow.id,revision_hash:created.revision_hash,workspace:f.workspace,
    access:'read_only',main_actor:'root',native_parent_thread_id:PARENT_THREAD_ID,inputs:{jobs}});
  binding=control(run);

  const handoff=await f.service.call('native_next',binding);
  assert.equal(handoff.status,'native_handoff');
  assert.deepEqual(handoff.packets.map(packet=>packet.index),[0,1]);
  for(const packet of handoff.packets){
    const bundle=JSON.parse(await readFile(packet.task_bundle_path,'utf8'));
    const taskInputs=JSON.parse(bundle.task.match(/\nInputs:\n([^\n]+)/)?.[1]??'null');
    const jobsPath=JSON.parse(taskInputs.jobs.match(/local file at (".*") \(format: json\)\./)?.[1]??'null');
    assert.deepEqual(JSON.parse(await readFile(jobsPath,'utf8')),[jobs[packet.index*2]],
      'Initial incremental delivery starts with the first item in each partition');
    await recordNativeSpawn(f,{...binding,attempt_id:handoff.attempt_id,index:packet.index,
      agent_id:`uncapped-incremental-child-${packet.index}`});
  }

  const continuations=[];
  let next=await f.service.call('native_next',binding);
  assert.equal(next.next_action,'continue_recorded_agent');
  const firstContinuation={index:next.index,item_index:next.item_index,agent_id:next.agent_id,
    accepted_item_indices:next.accepted_item_indices};
  const recorded=await f.service.call('get',binding);
  assert.deepEqual(recorded.nodes.worker.attempts[0].native_item_results[0],
    {agent_id:'uncapped-incremental-child-0',result:[0],turn_id:'uncapped-incremental-child-0-turn-0'});
  assert.deepEqual(recorded.nodes.worker.attempts[0].native_rejected_turns??{},{});
  assert.equal(observed.length,1);
  const repeated=await f.service.call('native_next',binding);
  assert.equal(repeated.next_action,'continue_recorded_agent');
  assert.equal(repeated.agent_id,next.agent_id);
  assert.equal(repeated.item_index,next.item_index);
  assert.deepEqual(repeated.followup_config,next.followup_config);
  assert.deepEqual(repeated.accepted_item_indices,next.accepted_item_indices);
  const stillPending=await f.service.call('get',binding);
  assert.equal(Object.keys(stillPending.nodes.worker.attempts[0].native_item_results).length,1);
  assert.deepEqual(stillPending.nodes.worker.attempts[0].native_rejected_turns??{},{});
  assert.equal(observed.length,1,'Repeating native_next must not re-observe or accept the old turn');
  continuations.push(firstContinuation);
  await f.service.call('native_followed_up',next.next_action_args);
  next=await f.service.call('native_next',binding);
  while(next.next_action==='continue_recorded_agent'){
    continuations.push({index:next.index,item_index:next.item_index,agent_id:next.agent_id,
      accepted_item_indices:next.accepted_item_indices});
    const taskPath=JSON.parse(next.followup_config.message.match(/Task bundle: ("[^\n]+")/)[1]);
    const bundle=JSON.parse(await readFile(taskPath,'utf8'));
    const taskInputs=JSON.parse(bundle.task.match(/\nInputs:\n([^\n]+)/)?.[1]??'null');
    const jobsPath=JSON.parse(taskInputs.jobs.match(/local file at (".*") \(format: json\)\./)?.[1]??'null');
    assert.deepEqual(JSON.parse(await readFile(jobsPath,'utf8')),[next.item_index],
      'A continuation carries only the next unresolved item, never an accepted item');
    await f.service.call('native_followed_up',next.next_action_args);
    next=await f.service.call('native_next',binding);
  }
  assert.equal(next.next_action,'workflow_native_next');
  let state=await f.service.call('get',binding);
  assert.equal(state.nodes.worker.status,'succeeded');
  assert.deepEqual(state.nodes.worker.output.results,jobs.map(job=>[job]));
  assert.equal(state.nodes.integrator.status,'ready','The downstream integrator is released only after the full item join');
  assert.equal(state.nodes.final.status,'pending');
  assert.deepEqual(continuations,[
    {index:0,item_index:1,agent_id:'uncapped-incremental-child-0',accepted_item_indices:[0]},
    {index:1,item_index:3,agent_id:'uncapped-incremental-child-1',accepted_item_indices:[2]},
  ]);

  const downstream=await f.service.call('native_next',binding);
  assert.equal(downstream.status,'native_handoff');
  assert.equal(downstream.node_id,'integrator');
  assert.equal(downstream.packets.length,1);
  await recordNativeSpawn(f,{...binding,attempt_id:downstream.attempt_id,index:downstream.packets[0].index,
    agent_id:'uncapped-incremental-downstream-integrator'});
  const completed=await f.service.call('native_next',binding);
  assert.equal(completed.next_action,'workflow_native_next');
  state=await f.service.call('get',binding);
  assert.equal(state.nodes.integrator.status,'succeeded');
  assert.deepEqual(state.nodes.integrator.output,{summary:'all joined items integrated'});
  assert.equal(state.nodes.final.status,'ready');
  assert.deepEqual(observed,[
    {node:'worker',agent_id:'uncapped-incremental-child-0',item_index:0},
    {node:'worker',agent_id:'uncapped-incremental-child-0',item_index:1},
    {node:'worker',agent_id:'uncapped-incremental-child-1',item_index:2},
    {node:'worker',agent_id:'uncapped-incremental-child-1',item_index:3},
    {node:'integrator',agent_id:'uncapped-incremental-downstream-integrator'},
  ]);
});

test('per-item native results reject copied Host indices and wrong cardinality atomically', async t => {
  const jobs = Array.from({ length: 10 }, (_, index) => index);
  let turn = 0;
  const f = await fixture(t, async ids => ({ status: 'completed', agent_id: ids[0], turn_id: `invalid-${++turn}`, result: {
    items: turn === 1
      ? [{ outcome: 'completed', result: [0] }, { item_index: 1, outcome: 'completed', result: [1] }]
      : Array.from({length:10},(_,index)=>({outcome:'completed',result:[index]})),
  } }));
  const workflow = definition('native-per-item-invalid', 'capped-one');
  const worker = workflow.nodes.find(node => node.id === 'worker');
  worker.fanout.result_mode = 'per_item';worker.retry.max_attempts = 3;
  const { binding } = await startRun(f, workflow, { jobs });
  const handoff = await f.service.call('native_next', binding);
  await recordNativeSpawn(f, { ...binding, attempt_id: handoff.attempt_id, index: 0, agent_id: 'exact-child' });
  const copied = await f.service.call('native_next', binding);
  assert.equal(copied.status, 'native_agent_invalid_result');
  assert.match(copied.reason, /returned 2 entries for 10 Host-selected items; no positional result was accepted/);
  assert.deepEqual(copied.unresolved_item_indices,jobs);
  await f.service.call('native_followed_up',copied.next_action_args);
  const completed = await f.service.call('native_next', binding);
  assert.equal(completed.next_action,'workflow_native_next');
  const state=await f.service.call('get', binding);
  assert.deepEqual(state.nodes.worker.attempts[0].native_item_results[1],{agent_id:'exact-child',result:[1]});
  assert.equal(Object.keys(state.nodes.worker.attempts[0].native_item_results).length,10);
});

test('concurrent per-item batches join out-of-order child results in original input order', async t => {
  const jobs = Array.from({ length: 20 }, (_, index) => index);
  const observed = [];
  const f = await fixture(t, async ids => {
    observed.push([...ids]);
    const id = ids.includes('agent-1') ? 'agent-1' : ids[0];
    const start = id === 'agent-1' ? 10 : 0;
    return { status: 'completed', agent_id: id, turn_id: `turn-${id}`, result: {
      items: jobs.slice(start, start + 10).map(job => ({outcome: 'completed', result: [job]})),
    } };
  });
  const workflow = definition('native-per-item-parallel', 'capped-one');
  workflow.nodes.find(node => node.id === 'worker').fanout.result_mode = 'per_item';
  const { binding } = await startRun(f, workflow, { jobs });
  const handoff = await f.service.call('native_next', binding);
  assert.deepEqual(handoff.packets.map(packet => packet.index), [0, 1]);
  for (let index = 0; index < 2; index++) await recordNativeSpawn(f, {
    ...binding, attempt_id: handoff.attempt_id, index, agent_id: `agent-${index}`,
  });
  await f.service.call('native_next', binding);
  const state = await f.service.call('get', binding);
  assert.deepEqual(state.nodes.worker.output.results, jobs.map(job => [job]));
  assert.deepEqual(observed, [['agent-0','agent-1'],['agent-0']]);
  assert.equal(Object.keys(state.nodes.worker.attempts[0].native_item_results).length, 20);
});

test('per-item repair exhaustion retains nine accepted items without accepting a blocked tenth', async t => {
  const jobs = Array.from({ length: 10 }, (_, index) => index);
  let turn = 0;
  const f = await fixture(t, async ids => ({ status: 'completed', agent_id: ids[0], turn_id: `turn-${++turn}`, result: {
    items: turn === 1
      ? jobs.map((job, item_index) => item_index === 7
        ? { outcome: 'blocked', block_reason: 'Still failing' }
        : { outcome: 'completed', result: [job] })
      : [{ outcome: 'blocked', block_reason: 'Still failing' }],
  } }));
  const workflow = definition('native-per-item-exhaustion', 'capped-one');
  workflow.nodes.find(node => node.id === 'worker').fanout.result_mode = 'per_item';
  const { binding } = await startRun(f, workflow, { jobs });
  const handoff = await f.service.call('native_next', binding);
  await recordNativeSpawn(f, { ...binding, attempt_id: handoff.attempt_id, index: 0, agent_id: 'batch-child' });
  const repair=await f.service.call('native_next', binding);
  assert.equal(repair.next_action, 'repair_recorded_agent');
  await f.service.call('native_followed_up',repair.next_action_args);
  const exhausted = await f.service.call('native_next', binding);
  assert.equal(exhausted.status, 'native_agent_repair_exhausted');
  assert.deepEqual(exhausted.unresolved_item_indices, [7]);
  const state = await f.service.call('get', binding);
  assert.equal(state.nodes.worker.status, 'failed');
  assert.equal(Object.keys(state.nodes.worker.attempts[0].native_item_results).length, 9);
  assert.equal(state.nodes.worker.attempts[0].native_item_results[7], undefined);
});

test('invalid per-item semantic value keeps valid siblings and rejects extra ordered entries without overwriting accepted values', async t => {
  const jobs = Array.from({ length: 10 }, (_, index) => index);
  let turn = 0;
  const f = await fixture(t, async ids => {
    turn++;
    const items = turn === 1
      ? jobs.map((job, item_index) => ({ outcome: 'completed', result: item_index === 7 ? 'invalid' : [job] }))
      : turn === 2
        ? [{ outcome: 'completed', result: [7] }, { outcome: 'completed', result: [999] }]
        : [{ outcome: 'completed', result: [7] }];
    return { status: 'completed', agent_id: ids[0], turn_id: `turn-${turn}`, result: { items } };
  });
  const workflow = definition('native-per-item-conflict', 'capped-one');
  const worker=workflow.nodes.find(node=>node.id==='worker');worker.fanout.result_mode='per_item';worker.retry.max_attempts=3;
  const { binding } = await startRun(f, workflow, { jobs });
  const handoff = await f.service.call('native_next', binding);
  await recordNativeSpawn(f, { ...binding, attempt_id: handoff.attempt_id, index: 0, agent_id: 'batch-child' });
  const invalid = await f.service.call('native_next', binding);
  assert.deepEqual(invalid.unresolved_item_indices, [7]);
  assert.match(invalid.reason, /item 7/);
  await f.service.call('native_followed_up',invalid.next_action_args);
  const extra = await f.service.call('native_next', binding);
  assert.equal(extra.status, 'native_agent_invalid_result');
  assert.match(extra.reason, /returned 2 entries for 1 Host-selected items/);
  await f.service.call('native_followed_up',extra.next_action_args);
  assert.deepEqual(extra.unresolved_item_indices, [7]);
  assert.match(extra.repair_prompt, /Task bundle:/);
  const before = await f.service.call('get', binding);
  assert.deepEqual(before.nodes.worker.attempts[0].native_item_results[0], { agent_id:'batch-child',result:[0] });
  assert.equal(before.nodes.worker.attempts[0].native_item_results[7],undefined);
  await f.service.call('native_next', binding);
  assert.deepEqual((await f.service.call('get', binding)).nodes.worker.output.results, jobs.map(job=>[job]));
});

test('per-item top-level rejection recomputes unresolved indices from accepted journal', async t => {
  for(const invalidResult of [
    {status:'completed',result:{wrong:[]}},
    {status:'blocked',reason:'Remaining item needs correction'},
    {status:'invalid',reason:'Malformed completion envelope'},
  ])await t.test(invalidResult.status+(invalidResult.result?' container':''),async t=>{
    const jobs=Array.from({length:10},(_,index)=>index);
    let turn=0;
    const f=await fixture(t,async ids=>{
      turn++;
      if(turn===1)return {status:'completed',agent_id:ids[0],turn_id:'partial',result:{items:jobs
        .map((job,index)=>index===9?{outcome:'completed',result:'invalid'}:{outcome:'completed',result:[job]})}};
      if(turn===2)return {agent_id:ids[0],turn_id:'bad-top',...invalidResult};
      return {status:'completed',agent_id:ids[0],turn_id:'repaired',result:{items:[
        {outcome:'completed',result:[9]}]}};
    });
    const workflow=definition('native-per-item-top-'+invalidResult.status+(invalidResult.result?'-container':''),'capped-one');
    const worker=workflow.nodes.find(node=>node.id==='worker');worker.fanout.result_mode='per_item';worker.retry.max_attempts=3;
    const {binding}=await startRun(f,workflow,{jobs});
    const handoff=await f.service.call('native_next',binding);
    await recordNativeSpawn(f,{...binding,attempt_id:handoff.attempt_id,index:0,agent_id:'batch-child'});
    const partial=await f.service.call('native_next',binding);
    assert.deepEqual(partial.unresolved_item_indices,[9]);
    await f.service.call('native_followed_up',partial.next_action_args);
    const top=await f.service.call('native_next',binding);
    assert.deepEqual(top.unresolved_item_indices,[9]);
    assert.deepEqual(top.accepted_item_indices,jobs.slice(0,9));
    assert.match(top.repair_prompt,/Task bundle:/);
    assert.doesNotMatch(top.repair_prompt,/Host-selected unresolved positions/);
    assert.equal(top.next_action,'repair_recorded_agent');
    assert.equal(Object.keys((await f.service.call('get',binding)).nodes.worker.attempts[0].native_item_results).length,9);
    await f.service.call('native_followed_up',top.next_action_args);
    await f.service.call('native_next',binding);
    assert.deepEqual((await f.service.call('get',binding)).nodes.worker.output.results,jobs.map(job=>[job]));
  });
});

test('nine valid items survive one malformed semantic item and same child repairs only that item', async t => {
  const jobs = Array.from({ length: 10 }, (_, index) => index);
  let turn = 0;
  const f = await fixture(t, async ids => ({ status: 'completed', agent_id: ids[0], turn_id: `turn-${++turn}`, result: {
    items: turn === 1
      ? jobs.map((job, item_index) => ({outcome:'completed',result:item_index===7?'invalid':[job]}))
      : [{outcome:'completed',result:[7]}],
  } }));
  const workflow = definition('native-per-item-malformed', 'capped-one');
  workflow.nodes.find(node => node.id === 'worker').fanout.result_mode = 'per_item';
  const { binding } = await startRun(f, workflow, { jobs });
  const handoff = await f.service.call('native_next', binding);
  await recordNativeSpawn(f, { ...binding, attempt_id: handoff.attempt_id, index: 0, agent_id: 'batch-child' });
  const partial = await f.service.call('native_next', binding);
  assert.deepEqual(partial.accepted_item_indices, [0,1,2,3,4,5,6,8,9]);
  assert.deepEqual(partial.unresolved_item_indices, [7]);
  assert.match(partial.reason, /item 7/);
  assert.match(partial.repair_prompt,/Task bundle:/);
  assert.doesNotMatch(partial.repair_prompt,/Host-selected unresolved positions/);
  assert.equal(Object.keys((await f.service.call('get', binding)).nodes.worker.attempts[0].native_item_results).length,9);
  await f.service.call('native_followed_up',partial.next_action_args);
  await f.service.call('native_next', binding);
  assert.equal(turn,2);
  assert.deepEqual((await f.service.call('get', binding)).nodes.worker.output.results,jobs.map(job=>[job]));
});

test('a replayed rejected per-item turn does not spend another correction or replace accepted items', async t => {
  const jobs = Array.from({ length: 10 }, (_, index) => index);
  let observations = 0;
  const f = await fixture(t, async ids => {
    observations++;
    if (observations <= 2) return { status:'completed',agent_id:ids[0],turn_id:'bad-turn',result:{items:
      jobs.map((job,item_index)=>item_index===7
        ? {outcome:'blocked',block_reason:'Repair item seven'}
        : {outcome:'completed',result:[job]})} };
    return {status:'completed',agent_id:ids[0],turn_id:'fixed-turn',result:{items:[{outcome:'completed',result:[7]}]}};
  });
  const workflow=definition('native-per-item-replay','capped-one');
  workflow.nodes.find(node=>node.id==='worker').fanout.result_mode='per_item';
  const {binding}=await startRun(f,workflow,{jobs});
  const handoff=await f.service.call('native_next',binding);
  await recordNativeSpawn(f,{...binding,attempt_id:handoff.attempt_id,index:0,agent_id:'batch-child'});
  const repair=await f.service.call('native_next',binding);
  assert.equal(repair.next_action,'repair_recorded_agent');
  await f.service.call('native_followed_up',repair.next_action_args);
  await f.service.call('native_next',binding);
  const attempt=(await f.service.call('get',binding)).nodes.worker.attempts[0];
  assert.equal(attempt.native_rejected_turns[0].count,1);
  assert.equal(Object.keys(attempt.native_item_results).length,10);
  assert.equal(observations,3);
});

test('cancellation during Host observation leaves a capped native node cancelled and unsealed', async t => {
  const entered = deferred();
  const release = deferred();
  const jobs = Array.from({ length: 10 }, (_, index) => index);
  const f = await fixture(t, async ids => {
    entered.resolve();
    await release.promise;
    return { status: 'completed', agent_id: ids[0], turn_id: 'late-turn', result: jobs };
  });
  const workflow = definition('native-capped-cancel', 'capped-one');
  const { binding } = await startRun(f, workflow, { jobs });
  const handoff = await f.service.call('native_next', binding);
  await recordNativeSpawn(f, { ...binding, attempt_id: handoff.attempt_id, index: 0, agent_id: 'late-child' });

  const pending = f.service.call('native_next', binding);
  const cancelledWait = assert.rejects(pending, { code: 'ATTEMPT_STOPPED' });
  await entered.promise;
  try {
    await f.service.call('cancel', binding);
  } finally {
    release.resolve();
    await cancelledWait;
  }

  const state = await f.service.call('get', binding);
  assert.equal(state.status, 'cancelled');
  assert.equal(state.nodes.worker.status, 'cancelled');
  assert.equal(state.nodes.worker.output, null);
  assert.equal(state.nodes.worker.attempts[0].dispatch.receipt ?? null, null);
});
