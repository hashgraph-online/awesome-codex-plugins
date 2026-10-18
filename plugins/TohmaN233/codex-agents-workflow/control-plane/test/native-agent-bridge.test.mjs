import test from 'node:test';
import assert from 'node:assert/strict';
import { Script } from 'node:vm';
import {mkdir,mkdtemp,readFile,readdir,rm,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {dirname,join} from 'node:path';
import {execFileSync} from 'node:child_process';
import {tmpdir} from './physical-tempdir.mjs';
import { nativeAgentHandoff, materializedNativeAgentHandoff, nativeAgentReceipt, nativeAgentCompletion, nativeAgentResultSchema, preflightNativeHostCompletion } from '../lib/execution/native-agent-bridge.mjs';
import {canonicalJSON} from '../lib/workflow-revisions.mjs';

test('native public carrier sends compact scope and sealed semantic file instead of copying known content',async t=>{
  const workspace=await mkdtemp(join(tmpdir(),'native-carrier-'));t.after(()=>rm(workspace,{recursive:true,force:true}));
  const task='NEUTRAL_SEMANTIC_TEXT '+ '雪'.repeat(600),schema={type:'object',properties:{conclusion:{type:'string'}},required:['conclusion'],additionalProperties:false};
  const definition={id:'worker',type:'agent',executor:{kind:'provider',context_inheritance:'upstream'},outputs_schema:schema};
  const record={state:{run_id:'carrier-run',inputs:{task},nodes:{}}};
  const dispatched={handoff_required:true,adapter:{execution:'native_agent',spawn_config:{agent_type:'default'}},envelope:{workspace,access:'bounded_write',effective_allowed_paths:['output'],node_id:'worker',prompt_template:'Author {{task}}',inputs:{task}}};
  const packet=(await materializedNativeAgentHandoff(record,definition,{attempt_id:'carrier-attempt'},dispatched)).packets[0];
  assert.match(packet.prompt,/semantic-task\.json/);assert.doesNotMatch(packet.prompt,/NEUTRAL_SEMANTIC_TEXT|雪|context-preparation|sha256|"result_schema"/);
  assert(packet.prompt.includes('Writable paths: ["output"]'));assert(packet.prompt.length<1000);
  const publicPath=JSON.parse(packet.prompt.match(/Task bundle: (".*")\n/)[1]),semantic=JSON.parse(await readFile(publicPath,'utf8'));
  assert(semantic.task.includes(task));assert.deepEqual(semantic.result_schema,schema);assert.deepEqual(semantic.writable_paths,['output']);
  assert.equal(semantic.workspace,workspace);assert.equal(semantic.access,'bounded_write');assert.equal(semantic.context_preparation,undefined);
  const inlineReference=nativeAgentHandoff(record,definition,{attempt_id:'carrier-attempt'},{...dispatched,
    materialized_packets:{0:{task_projection:{inline:true,task_bundle:semantic},allowed_paths:['output'],assigned_items:null}}}).packets[0];
  assert(inlineReference.prompt.includes(semantic.task));assert(inlineReference.prompt.includes(canonicalJSON(semantic.result_schema)));
  assert.deepEqual(inlineReference.allowed_paths,packet.allowed_paths);assert.deepEqual(inlineReference.spawn_config,packet.spawn_config);
  const original=await readFile(packet.task_bundle_path);
  const replay=(await materializedNativeAgentHandoff(record,definition,{attempt_id:'carrier-attempt'},dispatched)).packets[0];assert.equal(replay.prompt,packet.prompt);assert((await readFile(packet.task_bundle_path)).equals(original));
  await writeFile(publicPath,'tampered');await assert.rejects(materializedNativeAgentHandoff(record,definition,{attempt_id:'carrier-attempt'},dispatched),{code:'NODE_INPUT_MATERIALS_CONFLICT'});
});

test('native public carrier retains callable pinned resource addresses and rejects missing projections',async t=>{
  const root=await mkdtemp(join(tmpdir(),'native-carrier-resource-')),workspace=join(root,'workspace'),objects=join(root,'objects');
  await mkdir(workspace);await mkdir(objects);t.after(()=>rm(root,{recursive:true,force:true}));
  const bytes=Buffer.from('console.log("NEUTRAL_RESOURCE_CALL");'),sha256=createHash('sha256').update(bytes).digest('hex');await writeFile(join(objects,sha256),bytes);
  const definition={id:'writer',type:'agent',resources:['helper.mjs'],outputs_schema:{type:'object',properties:{done:{type:'boolean'}},required:['done']}};
  const record={state:{run_id:'carrier-resource',inputs:{},nodes:{}},pins:{root:{resources:[{path:'helper.mjs',sha256,bytes:bytes.length}]}}};
  const dispatched={handoff_required:true,adapter:{execution:'native_agent',spawn_config:{agent_type:'default'}},envelope:{workspace,access:'read_only',effective_allowed_paths:[],node_id:'writer',inputs:{},
    prompt_template:'Execute the declared helper. '+'NEUTRAL_TASK '.repeat(130),resource_access:{paths:['helper.mjs']},context_projection:{references:[{path:'helper.mjs',sha256,bytes:bytes.length}]}}};
  const packet=(await materializedNativeAgentHandoff(record,definition,{attempt_id:'resource-attempt'},dispatched,64000,null,{resourceRoot:objects})).packets[0];
  const publicPath=JSON.parse(packet.prompt.match(/Task bundle: (".*")\n/)[1]),semantic=JSON.parse(await readFile(publicPath,'utf8'));
  const bundle=JSON.parse(await readFile(packet.task_bundle_path)),preparation=JSON.parse(await readFile(bundle.context_preparation.path));
  const resourcePath=preparation.resources[0].local_path;assert(semantic.task.includes(canonicalJSON(resourcePath)));
  assert.equal(execFileSync(process.execPath,[resourcePath],{encoding:'utf8'}).trim(),'NEUTRAL_RESOURCE_CALL');
  assert.doesNotMatch(packet.prompt,/NEUTRAL_TASK|NEUTRAL_RESOURCE_CALL|helper\.mjs|sha256|context-preparation/);
  assert.throws(()=>nativeAgentHandoff(record,definition,{attempt_id:'resource-attempt'},{...dispatched,materialized_packets:{0:{task_bundle_path:packet.task_bundle_path,allowed_paths:[],assigned_items:null}}}),{code:'NATIVE_TASK_BUNDLE'});
  await writeFile(resourcePath,'changed');await assert.rejects(materializedNativeAgentHandoff(record,definition,{attempt_id:'resource-attempt'},dispatched,64000,null,{resourceRoot:objects}),{code:'NODE_INPUT_MATERIALS_CONFLICT'});
});

test('native legacy inline display retains every nonempty semantic material address',()=>{
  const schema={type:'object',properties:{summary:{type:'string'}},required:['summary']};
  const semantic={schema_version:1,task:'Read the declared historical materials.',workspace:'C:/legacy',access:'read_only',writable_paths:[],result_schema:schema,
    resources:[{path:'reference.md',local_path:'C:/legacy/resources/reference.md'}],
    verified_files:[{path:'source.bin',local_path:'C:/legacy/verified/source.bin'}]};
  const original=structuredClone(semantic);
  const definition={id:'legacy',type:'agent',outputs_schema:schema};
  const dispatched={handoff_required:true,adapter:{execution:'native_agent',spawn_config:{agent_type:'default'}},
    envelope:{workspace:semantic.workspace,access:semantic.access,effective_allowed_paths:[]},
    materialized_packets:{0:{task_projection:{inline:true,task_bundle:semantic},allowed_paths:[],assigned_items:null}}};
  const packet=nativeAgentHandoff({state:{run_id:'legacy-addresses',nodes:{}}},definition,{attempt_id:'legacy-attempt'},dispatched).packets[0];
  for(const [field,items]of Object.entries({resources:semantic.resources,verified_files:semantic.verified_files})){
    assert(packet.prompt.includes(canonicalJSON(items)),field+' semantic addresses must reach the child');
    for(const item of items)assert(packet.prompt.includes(item.local_path),item.local_path);
  }
  assert(packet.prompt.includes(semantic.task));
  assert(packet.prompt.includes(canonicalJSON(schema)));
  assert.doesNotMatch(packet.prompt,/schema_version|sha256|context-preparation/);
  assert.deepEqual(semantic,original);
});

test('native inline display preserves canonical semantic task bytes without nesting JSON string encoding',async t=>{
  const workspace=await mkdtemp(join(tmpdir(),'native-readable-'));t.after(()=>rm(workspace,{recursive:true,force:true}));
  const task='  Preserve "quoted" text, C:\\source\\file, a literal \\n, and\n\tindented second line. ';
  const schema={type:'object',properties:{conclusion:{type:'string'}},required:['conclusion'],additionalProperties:false};
  for(const inheritance of ['fresh','upstream']){
    const definition={id:'worker',type:'agent',executor:{kind:'provider',context_inheritance:inheritance},outputs_schema:schema};
    const record={state:{run_id:'readable-'+inheritance,inputs:{task},nodes:{}}};
    const dispatched={handoff_required:true,adapter:{execution:'native_agent',spawn_config:{agent_type:'default'}},
      envelope:{workspace,access:'read_only',effective_allowed_paths:[],node_id:'worker',prompt_template:'Author {{task}}',inputs:{task,notes:'Unexpanded "notes"\nremain exact.'}}};
    const packet=(await materializedNativeAgentHandoff(record,definition,{attempt_id:'readable-attempt'},dispatched)).packets[0];
    const bytes=await readFile(packet.task_bundle_path),bundle=JSON.parse(bytes);
    assert.equal(createHash('sha256').update(bytes).digest('hex'),packet.task_bundle_sha256);
    assert.equal(packet.prompt,'Workspace: '+workspace+'\nAccess: read_only\nWritable paths: []\n\n'+bundle.task+'\nResult schema:\n'+canonicalJSON(schema));
    assert(packet.prompt.includes(task));
    assert.doesNotMatch(packet.prompt,/"schema_version"|"result_schema"|context-preparation/);
    assert.equal(packet.spawn_config.fork_turns,inheritance==='upstream'?'all':'none');
    const replay=(await materializedNativeAgentHandoff(record,definition,{attempt_id:'readable-attempt'},dispatched)).packets[0];
    assert.equal(replay.prompt,packet.prompt);assert.equal(replay.task_bundle_sha256,packet.task_bundle_sha256);
  }
});

test('native size preflight uses only distinct recorded active children and exact observed assignment',async t=>{
  const definition={id:'writer',type:'agent',subagent_count:'auto',input_bindings:{jobs:'/inputs/jobs'},
    fanout:{input:'jobs',distribution:'one_per_item',item_name:'page',result_mode:'per_item',result_output:'results'},outputs_schema:{}};
  const record={state:{run_id:'neutral-preflight',inputs:{jobs:[{id:'a'},{id:'b'},{id:'c'}]},nodes:{}}};
  const attempt={id:'neutral-attempt',dispatch:{receipt:null},native_agents:{0:'exact-child-a',1:'exact-child-b'}};
  const proposal={result:{items:[{outcome:'completed',result:{summary:'exact a'}}]},target_indices:[0],
    native_observation:{index:0,agent_id:'exact-child-a',turn_id:'exact-terminal-turn'}};
  const original=structuredClone(attempt),completion=preflightNativeHostCompletion(record,definition,attempt,proposal);
  assert.deepEqual(attempt,original,'Size preflight must not create a receipt or accept any item');
  assert.deepEqual(completion.structured_output.results,[{summary:'exact a'},null,null]);
  assert.deepEqual(completion.evidence.find(item=>item.kind==='subagent_pool').dispatch_ids,['exact-child-a','exact-child-b']);
  const invalid=[
    ['wrong slot',a=>{},p=>{p.native_observation.index=1;}],
    ['wrong child',a=>{},p=>{p.native_observation.agent_id='foreign-child';}],
    ['missing observed turn',a=>{},p=>{p.native_observation.turn_id='';}],
    ['duplicate recorded child',a=>{a.native_agents[1]=a.native_agents[0];},p=>{}],
    ['inactive slot',a=>{a.native_agents[3]='foreign-slot';},p=>{}],
    ['noncanonical slot',a=>{a.native_agents['01']='foreign-slot';},p=>{}],
    ['another assignment target',a=>{},p=>{p.target_indices=[1];}],
    ['duplicate target',a=>{},p=>{p.target_indices=[0,0];}],
    ['accepted target',a=>{a.native_item_results={0:{result:{summary:'retained'}}};},p=>{}],
  ];
  for(const [name,changeAttempt,changeProposal]of invalid)await t.test(name,()=>{
    const a=structuredClone(attempt),p=structuredClone(proposal);changeAttempt(a);changeProposal(p);
    assert.throws(()=>preflightNativeHostCompletion(record,definition,a,p),{code:'NATIVE_HOST_CHECK_IDENTITY'});
  });
  await t.test('foreign sealed receipt',()=>{
    const a=structuredClone(attempt);a.dispatch.receipt={executor:'codex-native-subagent',agent_ids:['foreign-child']};
    assert.throws(()=>preflightNativeHostCompletion(record,definition,a,proposal),{code:'NATIVE_AGENT_RECEIPT'});
  });
  await t.test('inherited assignment is inactive',()=>{
    const a=structuredClone(attempt);a.inherited_native_item_indices=[0];
    assert.throws(()=>preflightNativeHostCompletion(record,definition,a,proposal),{code:'NATIVE_HOST_CHECK_IDENTITY'});
  });
});

test('materialized native small semantic assignment reaches the child directly without index or input reads',async t=>{
  const workspace=await mkdtemp(join(tmpdir(),'native-inline-'));t.after(()=>rm(workspace,{recursive:true,force:true}));
  const jobs=[{id:'first',task:'TCP ownership',write_paths:['pages/first']},{id:'second',task:'UDP ownership',write_paths:['pages/second']}];
  const definition={id:'writer',type:'agent',access:'bounded_write',allowed_paths:['pages'],subagent_count:'auto',fanout:{input:'jobs',distribution:'one_per_item',item_name:'jobs',result_mode:'per_item',result_output:'results',write_paths_field:'write_paths'},
    input_bindings:{jobs:'/inputs/jobs'},outputs_schema:{type:'object',properties:{results:{type:'array',items:{type:'object',properties:{markdown:{type:'string'}},required:['markdown'],additionalProperties:false}}}}};
  const state={run_id:'inline-run',inputs:{jobs},nodes:{},permissions:{workspace,access:'bounded_write',allowed_paths:['pages']}};
  const dispatched={handoff_required:true,adapter:{execution:'native_agent',spawn_config:{agent_type:'default'}},envelope:{workspace,access:'bounded_write',effective_allowed_paths:['pages'],
    prompt_template:'Write the assigned page.',inputs:{jobs},node_id:'writer'}};
  const handoff=await materializedNativeAgentHandoff({state},definition,{attempt_id:'inline-attempt'},dispatched);
  assert.equal(handoff.packets.length,2);
  for(const [index,packet] of handoff.packets.entries()){
    assert.match(packet.prompt,new RegExp(jobs[index].task));
    assert.doesNotMatch(packet.prompt,new RegExp(jobs[1-index].task));
    assert.doesNotMatch(packet.prompt,/Read this Host-generated|Task bundle:|context-preparation|task_bundle_sha256|prompt_sha256/);
    assert.match(packet.prompt,/one ordered entry per supplied item/);
    assert.deepEqual(packet.allowed_paths,jobs[index].write_paths);
  }
});

test('materialized native large assignment uses its prepared sidecar without recompiling the raw prompt',async t=>{
  const workspace=await mkdtemp(join(tmpdir(),'native-large-inline-'));t.after(()=>rm(workspace,{recursive:true,force:true}));
  const jobs=[{id:'large',body:'LARGE_BOUND_BODY'.repeat(10000)}];
  const definition={id:'writer',type:'agent',subagent_count:'auto',fanout:{input:'jobs',distribution:'one_per_item',item_name:'job',result_output:'results'},
    input_bindings:{jobs:'/inputs/jobs'}};
  const state={run_id:'large-inline-run',inputs:{jobs},nodes:{}};
  const dispatched={handoff_required:true,adapter:{execution:'native_agent',spawn_config:{agent_type:'default'}},envelope:{workspace,access:'read_only',effective_allowed_paths:[],
    prompt_template:'Inspect the assigned input.',inputs:{jobs},node_id:'writer'}};
  const packet=(await materializedNativeAgentHandoff({state},definition,{attempt_id:'large-inline-attempt'},dispatched)).packets[0];
  assert.doesNotMatch(packet.prompt,/LARGE_BOUND_BODY/);
  const inputs=JSON.parse(packet.prompt.match(/\nInputs:\n([^\n]+)/)[1]);
  const path=JSON.parse(inputs.jobs.match(/local file at (".*") \(format: json\)\./)[1]);
  assert.deepEqual(JSON.parse(await readFile(path)),jobs);
});
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

test('explicit upstream native packet inherits context and omits model overrides',()=>{
  const definition={id:'worker',type:'agent',executor:{kind:'provider',provider_id:'native-sol',context_inheritance:'upstream'}};
  const dispatched={handoff_required:true,adapter:{execution:'native_agent',spawn_config:{agent_type:'default',model:'gpt-6.1-sol',reasoning_effort:'high'}},
    envelope:{workspace:'C:/work',access:'bounded_write',effective_allowed_paths:['.'],inputs:{}},compiled_prompt:'Assigned page only.'};
  const packet=nativeAgentHandoff({state:{run_id:'run',nodes:{}}},definition,{attempt_id:'attempt'},dispatched).packets[0];
  assert.equal(packet.spawn_config.fork_turns,'all');
  assert.equal(Object.hasOwn(packet.spawn_config,'model'),false);
  assert.equal(Object.hasOwn(packet.spawn_config,'reasoning_effort'),false);
  assert.equal(Object.hasOwn(packet.spawn_config,'cwd'),false);
});

test('native handoff materializes each assigned task packet and preserves inputs through its selected public carrier',async t=>{
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
    assert.deepEqual(inputs.jobs_json,[jobs[packet.index]]);
    const publicPath=packet.prompt.match(/Task bundle: (".*")\n/)?.[1];
    assert.deepEqual(await readdir(dirname(packet.task_bundle_path)),publicPath?['context-preparation.json','semantic-task.json','task.json']:['context-preparation.json','task.json']);
    const delivered=publicPath?JSON.parse(await readFile(JSON.parse(publicPath),'utf8')).task:packet.prompt;
    assert.match(delivered,/Implement one assigned card\./);
    assert(delivered.includes(jobs[packet.index].payload));
    assert(!delivered.includes(jobs[1-packet.index].payload));
    assert.match(bundle.task,/Implement one assigned card\./);
  }
});

test('materialized native handoff delivers small declared pinned resources without workflow reader calls',async t=>{
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
  const preparation=JSON.parse(await readFile(bundle.context_preparation.path,'utf8'));
  assert.equal(preparation.resources.length,1);
  assert.equal(await readFile(preparation.resources[0].local_path,'utf8'),bytes.toString('utf8'));
  assert.doesNotMatch(packet.prompt,/workflow_read_resource|context-preparation|prompt_sha256/);
  assert.match(packet.prompt,/Exact pinned contract body|Use the contract/);
  assert.doesNotMatch(bundle.task,/workflow_read_resource/);
  assert.match(bundle.task,/Declared pinned resources below contain complete text or an exact Host-prepared local file address/);
});

test('native resource guidance gives the exact pinned MCP call without changing Main or task data', () => {
  const definition={id:'source',type:'agent',executor:{kind:'provider',provider_id:'native'},access:'read_only',
    resources:['workflow-assets/first.md','workflow-assets/second.md'],input_bindings:{task:'/inputs/task'},
    prompt_template:'Inspect the supplied files. {{task}}',outputs_schema:{type:'object',properties:{source:{type:'string'}},required:['source'],additionalProperties:false}};
  const state={run_id:'resource-run',workflow_id:'sample-workflow',workflow_revision:'a'.repeat(64),
    inputs:{task:'Preserve this task literal: read_workflow_resource.'},nodes:{},constraints:{},
    permissions:{workspace:'C:/workspace',access:'read_only',allowed_paths:[]}};
  const pins={root:{workflow:{name:'Sample',finalization:{node_id:'final'},nodes:[definition],edges:[],context_projection_version:2,
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
