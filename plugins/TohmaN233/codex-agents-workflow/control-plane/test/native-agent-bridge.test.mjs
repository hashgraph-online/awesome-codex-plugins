import test from 'node:test';
import assert from 'node:assert/strict';
import { Script } from 'node:vm';
import {mkdir,mkdtemp,readFile,readdir,rm,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {dirname,join} from 'node:path';
import {tmpdir} from './physical-tempdir.mjs';
import { nativeAgentHandoff, materializedNativeAgentHandoff, nativeAgentReceipt, nativeAgentCompletion, nativeAgentResultSchema } from '../lib/execution/native-agent-bridge.mjs';
import { resolvedSubagentPlan } from '../lib/workflow-runtime.mjs';
import { executionEnvelope } from '../lib/workflow-execution-envelope.mjs';
import { compilePrompt } from '../lib/workflow-executor.mjs';

test('per-item native result schema keeps Host-owned item positions out of Agent output',()=>{
  const definition={fanout:{result_mode:'per_item',result_output:'results'},outputs_schema:{type:'object',properties:{results:{type:'array',items:{type:'object',properties:{changes:{type:'string'}},required:['changes'],additionalProperties:false}}}}};
  const schema=nativeAgentResultSchema(definition);
  assert.equal(schema.properties.items.items.properties.item_index,undefined);
  assert.deepEqual(schema.properties.items.items.required,['outcome']);
  assert.deepEqual(Object.keys(schema.properties.items.items.properties).sort(),['block_reason','outcome','result']);
});

test('native packet keeps only the task scope needed by a real native subagent',()=>{
  const workspace='C:/workspace with 空格';
  const definition={id:'writer',type:'agent',outputs_schema:{type:'object',properties:{done:{type:'boolean'}},required:['done']}};
  const state={run_id:'run-workdir',inputs:{},nodes:{}};
  const dispatched={handoff_required:true,adapter:{execution:'native_agent',spawn_config:{agent_type:'default',model:'gpt-6-luna',reasoning_effort:'max'}},
    envelope:{workflow_id:'sample',workflow_revision:'revision',workspace,access:'bounded_write',effective_allowed_paths:['zz'],
      prompt_template:'Inspect the needed source and implement.',inputs:{},node_id:'writer'},compiled_prompt:'Inspect the needed source and implement.'};
  const packet=nativeAgentHandoff({state},definition,{attempt_id:'attempt'},dispatched).packets[0];
  assert.deepEqual({...packet.spawn_config,task_name:undefined},{agent_type:'default',model:'gpt-6-luna',reasoning_effort:'max',fork_turns:'none',task_name:undefined});
  assert.match(packet.spawn_config.task_name,/^wf_[a-f0-9]{24}_0$/);
  assert.equal(nativeAgentHandoff({state},definition,{attempt_id:'attempt'},dispatched).packets[0].spawn_config.task_name,packet.spawn_config.task_name);
  assert.equal(Object.hasOwn(packet.spawn_config,'cwd'),false,'Native spawn has no default-cwd binding');
  assert.match(packet.prompt,/^Workspace: C:\/workspace with 空格\nAccess: bounded_write\nWritable paths: \["zz"\]/);
  assert.match(packet.prompt,/Inspect the needed source and implement\./);
  assert.doesNotMatch(packet.prompt,/Code Mode shell call example|outer display budget|output truncation|pinned Workflow|workflow_revision/);
});

test('native handoff materializes each assigned task packet and sends only exact local addresses',async t=>{
  const root=await mkdtemp(join(tmpdir(),'native-materials-')),workspace=join(root,'workspace');await mkdir(workspace);
  t.after(()=>rm(root,{recursive:true,maxRetries:3,retryDelay:50}));
  const jobs=[{card_id:'card-a',payload:'A'.repeat(2000)},{card_id:'card-b',payload:'B'.repeat(2000)}];
  const definition={id:'cards',type:'agent',subagent_count:'auto',
    fanout:{input:'jobs',item_name:'card',distribution:'one_per_item',result_output:'results'},
    input_bindings:{task:'/inputs/task',jobs:'/inputs/jobs'}};
  const state={run_id:'run-materials',inputs:{task:'Implement one assigned card',jobs},nodes:{}};
  const dispatched={handoff_required:true,adapter:{execution:'native_agent',spawn_config:{agent_type:'default'}},
    envelope:{workflow_id:'cards',workflow_revision:'revision',workspace,access:'bounded_write',effective_allowed_paths:['zz'],
      prompt_template:'{{task}}.',inputs:{task:state.inputs.task,jobs_json:JSON.stringify(jobs)},node_id:'cards'}};
  const handoff=await materializedNativeAgentHandoff({state},definition,{attempt_id:'attempt-materials'},dispatched);
  assert.equal(handoff.packets.length,2);
  for(const packet of handoff.packets){
    assert.equal(typeof packet.task_bundle_path,'string');
    const bundle=JSON.parse(await readFile(packet.task_bundle_path,'utf8'));
    const inputs=JSON.parse(bundle.task.match(/\nInputs:\n([^\n]+)/)?.[1]??'null');
    const inputPath=JSON.parse(inputs.jobs_json.match(/local file at (".*") \(format: json\)\./)?.[1]??'null');
    assert.deepEqual(JSON.parse(await readFile(inputPath,'utf8')),[jobs[packet.index]]);
    assert.deepEqual(await readdir(dirname(packet.task_bundle_path)),['inputs','task.json']);
    assert.doesNotMatch(packet.prompt,/"payload":"[AB]{100}/);
    assert.doesNotMatch(packet.prompt,/Implement one assigned card\./);
    assert.match(bundle.task,/Implement one assigned card\./);
  }
});

test('materialized native handoff gives pinned resources exact local paths instead of making the child call the workflow reader',async t=>{
  const root=await mkdtemp(join(tmpdir(),'native-resource-bundle-')),workspace=join(root,'workspace'),objects=join(root,'objects');
  await mkdir(workspace);await mkdir(objects);t.after(()=>rm(root,{recursive:true,maxRetries:3,retryDelay:50}));
  const bytes=Buffer.from('Exact pinned contract body.','utf8'),sha256=createHash('sha256').update(bytes).digest('hex');
  await writeFile(join(objects,sha256),bytes);
  const definition={id:'writer',type:'agent',resources:['contract.md'],outputs_schema:{type:'object',properties:{done:{type:'boolean'}},required:['done']}};
  const state={run_id:'run-resources',inputs:{task:'Use the contract'},nodes:{}};
  const record={state,pins:{root:{resources:[{path:'contract.md',sha256,bytes:bytes.length}]}}};
  const dispatched={handoff_required:true,adapter:{execution:'native_agent',spawn_config:{agent_type:'default'}},
    envelope:{workflow_id:'sample',workflow_revision:'revision',workspace,access:'bounded_write',effective_allowed_paths:['zz'],
      prompt_template:'Resources listed below are logical identifiers, not filesystem paths. Use read_workflow_resource; cite resource IDs.\n{{task}}',
      inputs:state.inputs,node_id:'writer',resource_access:{reader:'read_workflow_resource',paths:['contract.md']},
      context_projection:{mode:'declared_bindings',bindings:[],references:[{path:'contract.md',sha256,bytes:bytes.length}]}}};
  const handoff=await materializedNativeAgentHandoff(record,definition,{attempt_id:'attempt-resources'},dispatched,64000,null,{resourceRoot:objects});
  const packet=handoff.packets[0],bundle=JSON.parse(await readFile(packet.task_bundle_path,'utf8'));
  assert.equal(bundle.resources.length,1);
  assert.deepEqual({...bundle.resources[0],local_path:undefined},{path:'contract.md',sha256,bytes:bytes.length,local_path:undefined});
  assert.equal(await readFile(bundle.resources[0].local_path,'utf8'),bytes.toString('utf8'));
  assert.doesNotMatch(packet.prompt,/workflow_read_resource|Exact pinned contract body|Use the contract/);
  assert.doesNotMatch(bundle.task,/workflow_read_resource/);
  assert.match(bundle.task,/Pinned resources are Host-materialized local files listed in this task bundle/);
});

test('native resource guidance gives the exact pinned MCP call without changing Main or task data', () => {
  const definition={id:'source',type:'agent',executor:{kind:'provider',provider_id:'native'},access:'read_only',
    resources:['workflow-assets/first.md','workflow-assets/second.md'],input_bindings:{task:'/inputs/task'},
    prompt_template:'Inspect the supplied files. {{task}}',outputs_schema:{type:'object',properties:{source:{type:'string'}},required:['source'],additionalProperties:false}};
  const state={run_id:'resource-run',workflow_id:'sample-workflow',workflow_revision:'a'.repeat(64),
    inputs:{task:'Preserve this task literal: read_workflow_resource.'},nodes:{},constraints:{},
    permissions:{workspace:'C:/workspace',access:'read_only',allowed_paths:[]}};
  const pins={root:{workflow:{name:'Sample',nodes:[definition],edges:[],context_projection_version:2,
    skill_policy:{mode:'cooperative',implicit:'deny',ambient_allow:[],shadowed_skill_paths:[]}}},providers:[{id:'native'}]};
  const envelope=executionEnvelope(definition,state,pins,{id:'attempt'},'example-private-lease-token');
  const original=JSON.stringify(envelope);
  const mainPrompt=compilePrompt(envelope,64000);
  const dispatched={handoff_required:true,adapter:{execution:'native_agent',spawn_config:{agent_type:'default'}},envelope,compiled_prompt:mainPrompt};
  const packet=nativeAgentHandoff({state,control_token:'example-private-controller-token'},definition,
    {attempt_id:'attempt',lease_token:'example-private-lease-token'},dispatched).packets[0];
  assert.match(mainPrompt,/Use read_workflow_resource; cite resource IDs/);
  assert.doesNotMatch(mainPrompt,/mcp__codex_agents_workflow__workflow_read_resource/);
  assert.doesNotMatch(packet.prompt,/Use read_workflow_resource; cite resource IDs/);
  assert.match(packet.prompt,/Preserve this task literal: read_workflow_resource\./);
  const call=packet.prompt.match(/tools\.mcp__codex_agents_workflow__workflow_read_resource\(([^\n]+?)\)/)?.[0];
  assert.ok(call,'Native packet must carry an executable exact-reader call');
  for(const resource_path of definition.resources){
    const args=new Script(call).runInNewContext({tools:{mcp__codex_agents_workflow__workflow_read_resource:value=>value},resource_path},{timeout:1000});
    assert.deepEqual({...args},{workflow_id:'sample-workflow',revision_hash:'a'.repeat(64),resource_path});
  }
  const discovery=packet.prompt.match(/ALL_TOOLS\.find\([^\n]+?\)/)?.[0];
  assert.ok(discovery,'Lazy discovery must select one exact tool name');
  const tools=[{name:'workflow_read_resource_decoy'},{name:'mcp__codex_agents_workflow__workflow_read_resource'}];
  assert.equal(new Script(discovery).runInNewContext({ALL_TOOLS:tools},{timeout:1000}),tools[1]);
  assert.doesNotMatch(JSON.stringify(packet),/example-private-controller-token|example-private-lease-token/);
  assert.equal(JSON.stringify(envelope),original);
  assert.equal(compilePrompt(envelope,64000),mainPrompt);
  const fanoutDefinition={...definition,subagent_count:'auto',input_bindings:{task:'/inputs/task',jobs:'/inputs/jobs'},
    fanout:{input:'jobs',item_name:'job',distribution:'one_per_item',result_output:'sources'},
    outputs_schema:{type:'object',properties:{sources:{type:'array',items:definition.outputs_schema}}}};
  const fanoutState={...state,inputs:{...state.inputs,jobs:['one','two']}};
  const fanoutEnvelope=executionEnvelope(fanoutDefinition,fanoutState,pins,{id:'attempt'},'example-private-lease-token');
  const fanout=nativeAgentHandoff({state:fanoutState},fanoutDefinition,{attempt_id:'attempt'},
    {...dispatched,envelope:fanoutEnvelope,compiled_prompt:'Unprojected routing input must not reach children.'});
  for(const child of fanout.packets){
    assert.ok(child.prompt.includes(call));
    assert.doesNotMatch(child.prompt,/Use read_workflow_resource; cite resource IDs|Unprojected routing input|example-private-lease-token/);
  }
});

test('native packets include exactly their semantic result schema and enforce the complete prompt bound', () => {
  const child={type:'array',items:{type:'object',properties:{card_id:{type:'string'},scenario_jobs:{type:'array',items:{type:'object'}}},required:['card_id','scenario_jobs'],additionalProperties:false}};
  for(const fanout of [false,true]){
    const definition={id:'writer',type:'agent',input_bindings:{jobs:'/inputs/jobs'},
      outputs_schema:fanout?{type:'object',properties:{joined_results:{type:'array',items:child}},required:['joined_results'],additionalProperties:false}:child,
      ...(fanout?{subagent_count:'auto',fanout:{input:'jobs',item_name:'job',distribution:'partition',batch_size:1,result_output:'joined_results'}}:{})};
    const state={run_id:'schema-run',inputs:{jobs:['one','two']},nodes:{}};
    const envelope={workflow_id:'sample',workflow_revision:'revision',workspace:'C:/workspace',access:'bounded_write',effective_allowed_paths:['work'],
      prompt_template:'Implement the assigned job.',inputs:{jobs:state.inputs.jobs},node_id:'writer'};
    const dispatched={handoff_required:true,adapter:{execution:'native_agent',spawn_config:{agent_type:'default'}},envelope,compiled_prompt:compilePrompt(envelope,64000)};
    const handoff=nativeAgentHandoff({state},definition,{attempt_id:'attempt'},dispatched);
    assert.deepEqual(handoff.result_schema,child);
    for(const packet of handoff.packets){
      const schemaText=packet.prompt.split('\nResult schema:\n');
      assert.equal(schemaText.length,2,'One semantic schema per child');
      assert.deepEqual(JSON.parse(schemaText[1]),child);
      assert.doesNotMatch(packet.prompt,/joined_results/);
      assert.throws(()=>nativeAgentHandoff({state},definition,{attempt_id:'attempt'},dispatched,packet.prompt.length-1,packet.index),{code:'PROMPT_LIMIT'});
    }
  }
});

test('native fan-out packets preserve partition, real Agent identities and joined semantic results', () => {
  const definition = { id: 'jobs', type: 'agent', subagent_count: 'auto',
    fanout: { input: 'jobs', item_name: 'job', distribution: 'one_per_item', result_output: 'results' },
    input_bindings: { jobs: '/inputs/jobs' },
    outputs_schema: { type: 'object', properties: { results: { type: 'array', items: { type: 'object', properties: { done: { type: 'boolean' } }, required: ['done'], additionalProperties: false } } }, required: ['results'], additionalProperties: false } };
  const state = { run_id: 'run-1', inputs: { jobs: ['a','b'] }, nodes: {} };
  const dispatched = { handoff_required: true, request_id: 'dispatch-attempt-1',
    adapter: { execution: 'native_agent', spawn_config: { agent_type: 'default', model: 'gpt-6-luna', reasoning_effort: 'max', fork_turns: 'none' } },
    compiled_prompt: 'Do one job.', envelope: { workflow_id: 'sample-workflow', workflow_revision: 'pinned-revision', workspace: 'C:/workspace', access: 'bounded_write', effective_allowed_paths: ['work'],
      prompt_template: 'Do one job.', inputs: { jobs: ['a','b'], upstream: { scenario_jobs: ['a','b'], note: 'keep' } }, node_id: 'jobs' } };
  const handoff = nativeAgentHandoff({ state }, definition, { attempt_id: 'attempt-1', lease_token: 'lease-1' }, dispatched);
  assert.equal(handoff.packets.length, 2);
  assert.match(handoff.packets[0].prompt, /\["a"\]/);
  assert.match(handoff.packets[1].prompt, /\["b"\]/);
  assert.doesNotMatch(handoff.packets[0].prompt, /\["a","b"\]/);
  assert.equal(handoff.packets[0].spawn_config.fork_turns, 'none');
  assert.doesNotMatch(handoff.packets[0].prompt, /sample-workflow|pinned-revision/);
  const receipt = nativeAgentReceipt(definition, state, 'attempt-1', ['agent-a','agent-b']);
  assert.deepEqual(receipt.subagent_dispatch_ids, ['agent-a','agent-b']);
  const completion = nativeAgentCompletion(definition, receipt, [
    { agent_id: 'agent-a', result: { done: true } }, { agent_id: 'agent-b', result: { done: false } },
  ], { changed_paths: ['work/result.txt'] });
  assert.deepEqual(completion.structured_output.results, [{ done: true }, { done: false }]);
  assert.deepEqual(completion.evidence.filter(item => item.kind === 'native_agent_result').map(item => item.agent_id), ['agent-a','agent-b']);
  assert.deepEqual(completion.changed_paths, ['work/result.txt']);
});

test('native batched fan-out keeps one result list per Agent without losing assigned items', () => {
  const definition = { id: 'jobs', type: 'agent', subagent_count: 'auto',
    fanout: { input: 'jobs', item_name: 'job', distribution: 'partition', batch_size: 20, result_output: 'results' },
    input_bindings: { jobs: '/inputs/jobs' },
    outputs_schema: { type: 'object', properties: { results: { type: 'array', items: { type: 'array', items: { type: 'integer' } } } }, required: ['results'], additionalProperties: false } };
  const jobs = Array.from({ length: 31 }, (_, index) => index);
  const state = { run_id: 'run-batch', inputs: { jobs }, nodes: {} };
  const dispatched = { handoff_required: true, adapter: { execution: 'native_agent', spawn_config: { agent_type: 'default' } },
    envelope: { workflow_id: 'sample', workflow_revision: 'revision', workspace: 'C:/workspace', access: 'read_only', effective_allowed_paths: [],
      prompt_template: 'Process assigned jobs.', inputs: { jobs }, node_id: 'jobs' } };
  const handoff = nativeAgentHandoff({ state }, definition, { attempt_id: 'attempt-batch' }, dispatched);
  assert.equal(handoff.packets.length, 2);
  const receipt = nativeAgentReceipt(definition, state, 'attempt-batch', ['agent-a', 'agent-b']);
  const completion = nativeAgentCompletion(definition, receipt, [
    { agent_id: 'agent-a', result: jobs.slice(0, 20) }, { agent_id: 'agent-b', result: jobs.slice(20) },
  ]);
  assert.deepEqual(completion.structured_output.results.flat(), jobs);
});

test('serial native fan-out scales with runtime input and exposes only the requested fresh-context batch', () => {
  const definition={id:'jobs',type:'agent',subagent_count:'auto',
    fanout:{input:'jobs',item_name:'job',distribution:'partition',batch_size:10,result_output:'results',scheduling:'serial',join:'all_required'},
    input_bindings:{jobs:'/inputs/jobs'},outputs_schema:{type:'object',properties:{results:{type:'array',items:{type:'array',items:{type:'integer'}}}},required:['results'],additionalProperties:false}};
  const dispatched={handoff_required:true,adapter:{execution:'native_agent',spawn_config:{agent_type:'default'}},
    envelope:{workflow_id:'sample',workflow_revision:'revision',workspace:'C:/workspace',access:'bounded_write',effective_allowed_paths:['work'],
      prompt_template:'Process assigned jobs.',inputs:{jobs:[]},node_id:'jobs'}};
  for(const size of [31,200]){
    const jobs=Array.from({length:size},(_,index)=>index),state={run_id:'run-batch',inputs:{jobs},nodes:{}};
    dispatched.envelope.inputs.jobs=jobs;
    const plan=resolvedSubagentPlan(definition,state);
    assert.equal(plan.count,Math.ceil(size/10));
    assert.deepEqual(plan.assignments.flat(),jobs);
    for(let index=0;index<plan.count;index++){
      const packet=nativeAgentHandoff({state},definition,{attempt_id:'attempt-batch'},dispatched,64000,index).packets;
      assert.equal(packet.length,1);
      assert.equal(packet[0].index,index);
      assert.equal(packet[0].spawn_config.fork_turns,'none');
      assert.match(packet[0].prompt,new RegExp(`\\[${plan.assignments[index].join(',')}\\]`));
    }
  }
});

test('one-per-item fan-out gives each card a fresh packet without the other cards', () => {
  const definition={id:'cards',type:'agent',subagent_count:'auto',
    fanout:{input:'card_jobs',item_name:'card job',distribution:'one_per_item',result_output:'results',scheduling:'parallel',max_concurrency:5,join:'all_required'},
    input_bindings:{card_jobs:'/inputs/card_jobs'}};
  for(const size of [31,200]){
    const jobs=Array.from({length:size},(_,index)=>({card_id:`card_${index}`,card_plan:`packets/${index}.json`,module_path:`parts/${index}.py`}));
    const state={run_id:'cards-run',inputs:{card_jobs:jobs},nodes:{}};
    const dispatched={handoff_required:true,adapter:{execution:'native_agent',spawn_config:{agent_type:'default'}},
      envelope:{workflow_id:'cards',workflow_revision:'revision',workspace:'C:/workspace',access:'bounded_write',effective_allowed_paths:['parts'],
        prompt_template:'Implement assigned card_jobs.',inputs:{card_jobs:jobs},node_id:'cards'}};
    assert.equal(resolvedSubagentPlan(definition,state).count,size);
    for(const index of [0,size-1]){
      const packet=nativeAgentHandoff({state},definition,{attempt_id:'attempt'},dispatched,64000,index).packets[0];
      assert.equal(packet.spawn_config.fork_turns,'none');
      assert.match(packet.prompt,new RegExp(`card_${index}`));
      assert.doesNotMatch(packet.prompt,new RegExp(`card_${index===0?size-1:0}`));
    }
  }
});

test('serialized fan-out bindings keep shared background but exclude sibling jobs', () => {
  const jobs=[{card_id:'one'},{card_id:'two'}];
  const definition={id:'cards',type:'agent',subagent_count:'auto',
    fanout:{input:'card_jobs',item_name:'card job',distribution:'one_per_item',result_output:'results'},
    input_bindings:{card_jobs:'/inputs/card_jobs'}};
  const dispatched={handoff_required:true,adapter:{execution:'native_agent',spawn_config:{agent_type:'default'}},
    envelope:{workflow_id:'cards',workflow_revision:'revision',workspace:'C:/workspace',access:'bounded_write',effective_allowed_paths:['parts'],
      prompt_template:'Implement assigned card.',inputs:{card_jobs_json:JSON.stringify(jobs),background_json:JSON.stringify({api:'shared stable API'})},node_id:'cards'}};
  const state={run_id:'cards-run',inputs:{card_jobs:jobs},nodes:{}};
  const first=nativeAgentHandoff({state},definition,{attempt_id:'attempt'},dispatched,64000,0).packets[0];
  assert.match(first.prompt,/"card_id":"one"/);
  assert.doesNotMatch(first.prompt,/"card_id":"two"/);
  assert.match(first.prompt,/shared stable API/);
});

test('ten-card partition sends only assigned verified material and shared background once per child',()=>{
  const jobs=Array.from({length:31},(_,index)=>({card_id:`card_${index}`,
    material:{rules:{japanese:`unique_rule_${index}`}}}));
  const definition={id:'cards',type:'agent',subagent_count:'auto',
    fanout:{input:'card_jobs',item_name:'card job',distribution:'partition',batch_size:10,
      result_output:'batch_results',scheduling:'parallel',max_concurrency:5,join:'all_required'},
    input_bindings:{card_jobs:'/inputs/card_jobs'}};
  const dispatched={handoff_required:true,adapter:{execution:'native_agent',spawn_config:{agent_type:'default'}},
    envelope:{workflow_id:'cards',workflow_revision:'revision',workspace:'C:/workspace',access:'bounded_write',effective_allowed_paths:['zz'],
      prompt_template:'Implement assigned cards.',inputs:{card_jobs_json:JSON.stringify(jobs),implementation_plan:'shared stable plan'},node_id:'cards'}};
  const state={run_id:'cards-run',inputs:{card_jobs:jobs},nodes:{}};
  const handoff=nativeAgentHandoff({state},definition,{attempt_id:'attempt'},dispatched,64000,[0,1,2,3]);
  assert.deepEqual(handoff.packets.map(packet=>packet.index),[0,1,2,3]);
  for(const packet of handoff.packets){
    const boundInputs=JSON.parse(packet.prompt.match(/\nInputs:\n([^\n]+)/)?.[1]??'null');
    assert.match(packet.prompt,/shared stable plan/);
    assert.equal((packet.prompt.match(/shared stable plan/g)??[]).length,1);
    const assigned=jobs.slice(packet.index*10,(packet.index+1)*10);
    assert.deepEqual(boundInputs.card_jobs_json,assigned,'One child receives its exact assigned material');
    assert.equal(boundInputs.implementation_plan,'shared stable plan');
    assert.deepEqual({...packet.spawn_config,task_name:undefined},{agent_type:'default',fork_turns:'none',task_name:undefined});
    assert.match(packet.spawn_config.task_name,new RegExp(`^wf_[a-f0-9]{24}_${packet.index}$`));
    assert.doesNotMatch(packet.prompt,/For relative shell paths|outer functions\.exec output budget|needed code symbols or line ranges/);
    for(const item of assigned){
      assert.equal((packet.prompt.match(new RegExp(`\\b${item.card_id}\\b`,'g'))??[]).length,1,
        `card ${item.card_id} is duplicated in one child packet`);
      assert.match(packet.prompt,new RegExp(item.material.rules.japanese));
    }
    const other=jobs.find(item=>!assigned.includes(item));
    assert.doesNotMatch(packet.prompt,new RegExp(`\\b${other.card_id}\\b`));
    assert.doesNotMatch(packet.prompt,new RegExp(other.material.rules.japanese));
  }
});

test('opt-in per-item packet maps fixed partition items to exact global indices and item schema',()=>{
  const jobs=['a','b','c','d'];
  const definition={id:'work',type:'agent',subagent_count:2,
    fanout:{input:'jobs',item_name:'job',distribution:'partition',result_output:'results',scheduling:'parallel',join:'all_required',result_mode:'per_item'},
    input_bindings:{jobs:'/inputs/jobs'},outputs_schema:{type:'object',properties:{results:{type:'array',items:{type:'string'}}},required:['results'],additionalProperties:false}};
  const state={run_id:'per-item',inputs:{jobs},nodes:{}};
  const dispatched={handoff_required:true,adapter:{execution:'native_agent',spawn_config:{agent_type:'default'}},
    envelope:{workflow_id:'per-item',workflow_revision:'revision',workspace:'C:/workspace',access:'read_only',effective_allowed_paths:[],
      prompt_template:'Process assigned jobs.',inputs:{jobs},node_id:'work'}};
  const handoff=nativeAgentHandoff({state},definition,{attempt_id:'attempt'},dispatched);
  assert.doesNotMatch(handoff.packets[0].prompt,/item positions|\[0,2\]/i);
  assert.doesNotMatch(handoff.packets[1].prompt,/item positions|\[1,3\]/i);
  assert.match(handoff.packets[0].prompt,/Host binds entries to supplied items by order/);
  assert.doesNotMatch(handoff.packets[0].prompt,/"item_index"/);
  assert.deepEqual(handoff.result_schema.properties.items.items.properties.result,{type:'string'});
  assert.match(handoff.packets[0].prompt,/"outcome":"blocked"/);
});
