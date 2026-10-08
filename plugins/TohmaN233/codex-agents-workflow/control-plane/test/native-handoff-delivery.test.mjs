import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdir,mkdtemp,readFile,rm} from 'node:fs/promises';
import {join} from 'node:path';
import {tmpdir} from './physical-tempdir.mjs';
import {materializedNativeAgentHandoff} from '../lib/execution/native-agent-bridge.mjs';

test('large native inputs stay in Host files instead of crossing the controller conversation',async t=>{
  const root=await mkdtemp(join(tmpdir(),'native-delivery-')),workspace=join(root,'workspace');await mkdir(workspace);
  t.after(()=>rm(root,{recursive:true,maxRetries:3,retryDelay:50}));
  const jobs=Array.from({length:20},(_,index)=>({card_id:`card_${index}`,
    material:{rules:{english:`unique_rule_${index} ${'Distinct printed card rule. '.repeat(65)}`},
      output_paths:{module_path:`zz/card_${index}.py`}}}));
  const definition={id:'writer',type:'agent',subagent_count:'auto',
    fanout:{input:'card_jobs',item_name:'card job',distribution:'partition',batch_size:10,
      result_output:'results',scheduling:'parallel',max_concurrency:2,join:'all_required'},
    input_bindings:{card_jobs:'/inputs/card_jobs'},
    outputs_schema:{type:'object',properties:{results:{type:'array',items:{type:'string'}}},required:['results'],additionalProperties:false}};
  const state={run_id:'run-packets',inputs:{card_jobs:jobs},nodes:{}};
  const dispatched={handoff_required:true,adapter:{execution:'native_agent',
    spawn_config:{agent_type:'default',model:'gpt-6-luna',reasoning_effort:'max'}},
    envelope:{workflow_id:'sample',workflow_revision:'revision',workspace,access:'bounded_write',effective_allowed_paths:['zz'],
      prompt_template:'Implement assigned cards.',inputs:{card_jobs_json:JSON.stringify(jobs),implementation_plan:'shared plan'},node_id:'writer'}};
  const handoff=await materializedNativeAgentHandoff({state},definition,{attempt_id:'attempt-1'},dispatched,64000);
  assert.deepEqual(handoff.packets.map(packet=>packet.index),[0,1]);
  assert.ok(JSON.stringify(handoff).length<10000,'The controller handoff must stay compact');
  for(const packet of handoff.packets){
    const bundle=JSON.parse(await readFile(packet.task_bundle_path,'utf8'));
    const inputs=JSON.parse(bundle.task.match(/\nInputs:\n([^\n]+)/)?.[1]??'null');
    const assigned=jobs.slice(packet.index*10,packet.index*10+10);
    const inputPath=JSON.parse(inputs.card_jobs_json.match(/local file at (".*") \(format: json\)\./)?.[1]??'null');
    assert.deepEqual(JSON.parse(await readFile(inputPath,'utf8')),assigned);
    assert.ok(Buffer.byteLength(JSON.stringify(bundle))<16*1024);
    assert.doesNotMatch(JSON.stringify(bundle),/unique_rule_|Distinct printed card rule/);
    assert.equal(packet.task_bundle_path,join(workspace,'work','.workflow-runtime','native-agent','run-packets','attempt-1',`partition-${packet.index}`,'task.json'));
    assert.doesNotMatch(packet.prompt,/unique_rule_|Distinct printed card rule/);
    assert.doesNotMatch(packet.prompt,/Implement assigned cards/);
    assert.match(bundle.task,/Implement assigned cards/);
    assert.deepEqual({...packet.spawn_config,task_name:undefined},{agent_type:'default',model:'gpt-6-luna',reasoning_effort:'max',fork_turns:'none',task_name:undefined});
    assert.match(packet.spawn_config.task_name,new RegExp(`^wf_[a-f0-9]{24}_${packet.index}$`));
  }
});

test('retry task bundle materializes only unresolved items inherited from a prior attempt',async t=>{
  const root=await mkdtemp(join(tmpdir(),'native-retry-delivery-')),workspace=join(root,'workspace');await mkdir(workspace);
  t.after(()=>rm(root,{recursive:true,maxRetries:3,retryDelay:50}));
  const jobs=Array.from({length:10},(_,index)=>({card_id:`card_${index}`,output_paths:{module_path:`zz/card_${index}.py`}}));
  const definition={id:'writer',type:'agent',subagent_count:'auto',
    fanout:{input:'card_jobs',item_name:'card job',distribution:'partition',batch_size:10,result_output:'results',
      result_mode:'per_item',scheduling:'parallel',max_concurrency:2,join:'all_required'},
    input_bindings:{card_jobs:'/inputs/card_jobs'},outputs_schema:{type:'object',properties:{results:{type:'array',items:{type:'string'}}},required:['results'],additionalProperties:false}};
  const attempt={id:'attempt-retry',inherited_native_item_indices:[0,3,4,5,7,8,9]};
  const state={run_id:'run-retry-packets',inputs:{card_jobs:jobs},nodes:{writer:{attempts:[attempt]}}};
  const dispatched={handoff_required:true,adapter:{execution:'native_agent',spawn_config:{agent_type:'default'}},
    envelope:{workflow_id:'sample',workflow_revision:'revision',workspace,access:'bounded_write',effective_allowed_paths:['zz'],
      prompt_template:'Implement assigned cards.',inputs:{card_jobs_json:JSON.stringify(jobs)},node_id:'writer'}};
  const handoff=await materializedNativeAgentHandoff({state},definition,{attempt_id:attempt.id},dispatched,64000,0);
  const bundle=JSON.parse(await readFile(handoff.packets[0].task_bundle_path,'utf8'));
  const inputs=JSON.parse(bundle.task.match(/\nInputs:\n([^\n]+)/)?.[1]??'null');
  const inputPath=JSON.parse(inputs.card_jobs_json.match(/local file at (".*") \(format: json\)\./)?.[1]??'null');
  assert.deepEqual(JSON.parse(await readFile(inputPath,'utf8')),[jobs[1],jobs[2],jobs[6]]);
  assert.equal(bundle.result_schema.properties.items.minItems,3);
  assert.equal(bundle.result_schema.properties.items.maxItems,3);
  assert.deepEqual(bundle.writable_paths,['zz']);
});
