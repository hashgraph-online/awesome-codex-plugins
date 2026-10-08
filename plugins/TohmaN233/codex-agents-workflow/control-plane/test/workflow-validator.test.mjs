import test from 'node:test';
import assert from 'node:assert/strict';
import { validateWorkflowGraph } from '../lib/workflow-validator.mjs';
import { evaluateExpression, intersectBoundaries, readPointer, resolveBindings } from '../lib/workflow-bindings.mjs';
import { agent, edge, readyWorkflow } from './fixtures/workflow-fixtures.mjs';

test('declared array projections pass only needed child fields to downstream nodes',()=>{
  const batch_results=[{changes:'A',scenario_jobs:[{card:'A'},{card:'B'}]},
    {changes:'C',scenario_jobs:[{card:'C'}]}];
  const context={nodes:{implementation:{output:{batch_results}}}};
  const result=resolveBindings({changes:{path:'/nodes/implementation/output/batch_results',pluck:'changes'},
    scenario_jobs:{path:'/nodes/implementation/output/batch_results',flat_map:'scenario_jobs'}},context);
  assert.deepEqual(result.changes,['A','C']);
  assert.deepEqual(result.scenario_jobs,[{card:'A'},{card:'B'},{card:'C'}]);
  assert.throws(()=>resolveBindings({bad:{path:'/nodes/implementation/output/batch_results',flat_map:'missing'}},context),{code:'BINDING_FLAT_MAP'});
  context.nodes.scenarios={output:{results:[[{card:'A'},{card:'B'}],[{card:'C'}]]}};
  context.nodes.validation={output:{batch_validations:[{all_passed:true,validation_evidence:'A/B'},{all_passed:false,validation_evidence:'C'}]}};
  const joined=resolveBindings({batches:{path:'/nodes/implementation/output/batch_results',zip:'/nodes/scenarios/output/results',count_field:'scenario_jobs'},
    all_passed:{path:'/nodes/validation/output/batch_validations',every_true:'all_passed'}},context);
  assert.equal(joined.batches.length,2);
  assert.deepEqual(joined.batches[0],{source:batch_results[0],results:[{card:'A'},{card:'B'}]});
  assert.equal(joined.all_passed,false);
  context.nodes.scenarios.output.results=[[{card:'A'},{card:'B'},{card:'C'}]];
  const grouped=resolveBindings({batches:{path:'/nodes/implementation/output/batch_results',zip:'/nodes/scenarios/output/results',count_field:'scenario_jobs',group:2}},context);
  assert.deepEqual(grouped.batches,[{source:batch_results,results:[{card:'A'},{card:'B'},{card:'C'}]}]);
  context.nodes.scenarios.output.results[1]=[];
  assert.throws(()=>resolveBindings({batches:{path:'/nodes/implementation/output/batch_results',zip:'/nodes/scenarios/output/results',count_field:'scenario_jobs'}},context),{code:'BINDING_ZIP'});
});

function withWork() {
  const workflow = readyWorkflow(); workflow.nodes.splice(1, 0, agent('work'));
  workflow.edges = [edge('start', 'work'), edge('work', 'final'), edge('final', 'end')]; return workflow;
}
function branching(type) {
  const workflow = readyWorkflow();
  const fork = type === 'parallel' ? { id: 'fork', type, join_id: 'join' } : { id: 'fork', type, cases: [{ label: 'yes', when: { op: 'exists', args: [{ path: '/inputs/choice' }] } }], default_label: 'no' };
  workflow.nodes.splice(1, 0, fork, agent('a'), agent('b'), ...(type === 'parallel' ? [{ id: 'join', type: 'join', parallel_id: 'fork' }] : []));
  workflow.edges = [edge('start', 'fork'), edge('fork', 'a', 'yes'), edge('fork', 'b', 'no'), edge('a', type === 'parallel' ? 'join' : 'final'), edge('b', type === 'parallel' ? 'join' : 'final'), ...(type === 'parallel' ? [edge('join', 'final')] : []), edge('final', 'end')];
  return workflow;
}
const valid = (workflow, context) => assert.equal(validateWorkflowGraph(workflow, context).valid, true, JSON.stringify(validateWorkflowGraph(workflow, context).errors));
const invalid = (workflow, code, context) => assert(validateWorkflowGraph(workflow, context).errors.some(error => error.code === code), `Missing ${code}: ${JSON.stringify(validateWorkflowGraph(workflow, context))}`);

test('valid sequential, conditional and parallel graphs are deterministic and validation does not mutate inputs', () => {
  for (const workflow of [readyWorkflow(), withWork(), branching('condition'), branching('parallel')]) {
    const before = JSON.stringify(workflow); valid(workflow);
    assert.deepEqual(validateWorkflowGraph(workflow), validateWorkflowGraph(workflow));
    assert.equal(JSON.stringify(workflow), before);
  }
});

test('identity, topology and final acceptance reject each malformed graph', () => {
  const cases = [
    ['START_COUNT', w => { w.nodes.push({ id: 'start2', type: 'start' }); }],
    ['END_COUNT', w => { w.nodes = w.nodes.filter(n => n.id !== 'end'); }],
    ['NODE_DUPLICATE', w => { w.nodes.push({ ...w.nodes[0] }); }],
    ['EDGE_DUPLICATE', w => { w.edges.push({ ...w.edges[0] }); }],
    ['EDGE_ENDPOINT', w => { w.edges[0].target = 'missing'; }],
    ['UNREACHABLE', w => { w.nodes.push(agent('orphan')); }],
    ['NO_END_PATH', w => { w.edges = w.edges.filter(e => e.source !== 'final'); }],
    ['GRAPH_CYCLE', w => { w.edges.push(edge('final', 'start')); }],
    ['FINALIZER_MISSING', w => { w.finalization.node_id = 'missing'; }],
    ['FINALIZER_AUTHORITY', w => { w.nodes.find(n => n.id === 'final').executor = { kind: 'provider', provider_id: 'p' }; }],
    ['FINALIZER_BYPASS', w => { w.edges.push(edge('work', 'end')); }],
    ['FINALIZER_ORDER', w => { w.edges = [edge('start', 'final'), edge('final', 'work'), edge('work', 'end')]; }],
    ['BINDING_SOURCE', w => { w.nodes.find(n => n.id === 'work').input_bindings = { future: '/nodes/final/output/value' }; }],
    ['BINDING_SOURCE', w => { const producer=w.nodes.find(n => n.id === 'work'); producer.outputs_schema={type:'object',properties:{result:{type:'string'}},required:['result'],additionalProperties:false}; w.nodes.find(n => n.id === 'final').input_bindings={missing:'/nodes/work/output/missing'}; }],
    ['OUTPUT_BINDINGS', w => { w.output_bindings = { missing: '/nodes/missing/output/value' }; }],
    ['PATH_SCOPE', w => { Object.assign(w.nodes.find(n => n.id === 'work'), { access: 'bounded_write', path_scope: ['src/**'] }); }],
  ];
  for (const [code, mutate] of cases) { const workflow = withWork(); mutate(workflow); invalid(workflow, code); }
});

test('a guarded Host tool may finalize without a model relay',()=>{
  const workflow=withWork(),final=workflow.nodes.find(node=>node.id==='final');
  Object.assign(final,{type:'tool',executor:{kind:'tool',tool:'verify_final'},role:undefined,prompt_template:undefined,
    outputs_schema:{type:'object',properties:{all_passed:{type:'boolean'}},required:['all_passed'],additionalProperties:false},
    completion_contract:{on_missing:'block',outcome:'validated_artifact',fail_on_false:['all_passed']}});
  delete final.role;delete final.prompt_template;
  workflow.host_tools=[{id:'verify_final',identity:{name:'verify_final',version:'1',sha256:'a'.repeat(64)},argv:['verify_final'],
    input_schema:{type:'object',properties:{},required:[],additionalProperties:false},output_schema:structuredClone(final.outputs_schema),
    env_allow:[],permissions:{network:false,read_paths:[],write_paths:[]},output_cap_bytes:4096,deadline_ms:1000,idempotency:{mode:'safe'}}];
  valid(workflow,{tools:['verify_final']});
  final.completion_contract.fail_on_false=[];
  invalid(workflow,'FINALIZER_DETERMINISTIC',{tools:['verify_final']});
});

test('condition DSL, labels and exit correspondence are validated', () => {
  const workflow = branching('condition'); valid(workflow);
  const fork = workflow.nodes.find(n => n.id === 'fork');
  fork.cases.push({ ...fork.cases[0] }); invalid(workflow, 'CONDITION_LABEL'); fork.cases.pop();
  fork.cases[0].when = { op: 'eval', args: [{ value: 'process.exit()' }] }; invalid(workflow, 'CONDITION_DSL');
  fork.cases[0].when = { value: true };
  workflow.edges.find(e => e.source === 'fork').label = 'unknown'; invalid(workflow, 'CONDITION_EDGES');
});

test('parallel joins forbid missing pair, early merges, unrelated branch entry and bypass', () => {
  for (const [code, mutate] of [
    ['PARALLEL_JOIN', w => { w.nodes.find(n => n.id === 'fork').join_id = 'final'; }],
    ['JOIN_PARALLEL', w => { w.nodes.find(n => n.id === 'join').parallel_id = 'missing'; }],
    ['JOIN_BYPASS', w => { w.edges.push(edge('a', 'end')); }],
    ['BRANCH_OVERLAP', w => { w.edges.push(edge('a', 'b')); }],
    ['JOIN_FOREIGN_BRANCH', w => { w.edges.push(edge('start', 'join')); }],
  ]) { const workflow = branching('parallel'); mutate(workflow); invalid(workflow, code); }
});

test('disabled Provider is structurally valid but launch blocked; binding and capabilities are preserved', () => {
  const workflow = withWork(); const worker = workflow.nodes.find(n => n.id === 'work');
  Object.assign(worker, { executor: { kind: 'provider', provider_id: 'p' }, access: 'bounded_write', path_scope: { binding: 'run.allowed_paths' } });
  const provider = { id: 'p', kind: 'native_agent', enabled: false, capabilities: { read: true, write: true }, config: { role: 'implementer' } };
  const context = { providers: [provider] }; valid(workflow, context);
  assert.equal(validateWorkflowGraph(workflow, context).launch_ready, false);
  assert(validateWorkflowGraph(workflow, context).blockers.some(b => b.code === 'PROVIDER_DISABLED'));
  invalid(workflow, 'PROVIDER_MISSING');
  provider.capabilities.write = false; invalid(workflow, 'PROVIDER_CAPABILITY', context);
  provider.capabilities.write = true; provider.config.role = 'reviewer'; invalid(workflow, 'PROVIDER_ROLE', context);
});

test('legacy Role metadata cannot affect Workflow validation or node authority',()=>{
  const workflow=withWork(),worker=workflow.nodes.find(node=>node.id==='work');
  worker.executor={kind:'provider',provider_id:'p'};worker.role_ref={id:'bounded'};
  const provider={id:'p',kind:'native_agent',enabled:true,capabilities:{read:true,write:true},config:{role:'advisor'}};
  valid(workflow,{providers:[provider],roles:[]});
  worker.role_ref={id:'missing-or-disabled'};
  valid(workflow,{providers:[provider],roles:[]});
});

test('Codex task-thread nodes pin a native Provider and continuation can only reuse an upstream task', () => {
  const workflow = withWork(); const worker = workflow.nodes.find(node => node.id === 'work');
  const continuation = agent('continue'); workflow.nodes.splice(workflow.nodes.findIndex(node => node.id === 'final'), 0, continuation);
  workflow.edges = [edge('start', 'work'), edge('work', 'continue'), edge('continue', 'final'), edge('final', 'end')];
  workflow.skill_policy = { mode: 'cooperative', implicit: 'allow', ambient_allow: [], shadowed_skill_paths: [] };
  worker.executor = { kind: 'thread', provider_id: 'p', lifecycle: 'start' };
  continuation.executor = { kind: 'thread', provider_id: 'p', lifecycle: 'continue', source_node: 'work' };
  const context = { providers: [{ id: 'p', kind: 'native_agent', enabled: true, capabilities: { read: true, write: true }, config: { role: 'implementer' } }, { id: 'other', kind: 'native_agent', enabled: true, capabilities: { read: true, write: true }, config: { role: 'implementer' } }] };
  valid(workflow, context);
  continuation.executor = { kind: 'thread', provider_id: 'other', lifecycle: 'continue', source_node: 'work' }; invalid(workflow, 'THREAD_PROVIDER_CONTINUITY', context);
  continuation.executor = { kind: 'thread', provider_id: 'p', lifecycle: 'continue', source_node: 'final' }; invalid(workflow, 'THREAD_SOURCE', context);
  continuation.executor = { kind: 'thread', provider_id: 'p', lifecycle: 'continue', source_node: 'work' }; workflow.skill_policy.mode = 'strict'; workflow.skill_policy.implicit = 'deny'; invalid(workflow, 'THREAD_STRICT_UNSUPPORTED', context);
  workflow.skill_policy.mode = 'cooperative'; workflow.skill_policy.implicit = 'allow'; context.providers[0].kind = 'openai_compatible'; invalid(workflow, 'THREAD_PROVIDER_UNSUPPORTED', context);
});

test('all Ready Workflow paths reject Agent field transcription',()=>{
  const copiedPrompt=withWork();
  copiedPrompt.nodes.find(node=>node.id==='work').prompt_template='Copy the supplied record IDs and paths into the result.';
  invalid(copiedPrompt,'AGENT_DETERMINISTIC_TRANSCRIPTION');

  for(const instruction of [
    'Return the supplied label and name in the output.',
    'Preserve the provided category in the result.',
    'Set the output category from the input record.',
    'Return the final accepted result from metadata_check and the latest applicable successful review: repaired_review, then initial_review.',
    'Choose the latest successful result among the upstream review records and output it.',
    '输出输入记录提供的名称和标签。',
    '保留输入记录中的类别并写入结果。',
    '将输入记录的类别写入输出字段。',
  ]){
    const arbitraryCopy=withWork();
    arbitraryCopy.nodes.find(node=>node.id==='work').prompt_template=instruction;
    invalid(arbitraryCopy,'AGENT_DETERMINISTIC_TRANSCRIPTION');
  }

  const copiedSchema=withWork(),worker=copiedSchema.nodes.find(node=>node.id==='work');
  copiedSchema.inputs_schema={type:'object',properties:{card_id:{type:'string'}},required:['card_id'],additionalProperties:false};
  worker.input_bindings={card_id:'/inputs/card_id'};
  worker.outputs_schema={type:'object',properties:{result:{type:'object',properties:{card_id:{type:'string'},evidence:{type:'string'}},required:['card_id','evidence'],additionalProperties:false}},required:['result'],additionalProperties:false};
  invalid(copiedSchema,'AGENT_DETERMINISTIC_TRANSCRIPTION');

  const semanticOnly=withWork(),semanticWorker=semanticOnly.nodes.find(node=>node.id==='work');
  semanticWorker.prompt_template='Return only a newly created semantic finding in input order. Do not return IDs, paths or hashes.';
  semanticWorker.outputs_schema={type:'object',properties:{finding:{type:'string'}},required:['finding'],additionalProperties:false};
  semanticOnly.nodes.find(node=>node.id==='final').input_bindings={finding:'/nodes/work/output/finding'};
  valid(semanticOnly);

  const ordered=withWork();
  ordered.nodes.find(node=>node.id==='work').prompt_template='Preserve input order while producing a new finding for each item.';
  valid(ordered);
  ordered.nodes.find(node=>node.id==='work').prompt_template='保持输入顺序，为每项生成新的结论。';
  valid(ordered);
});

test('portable executable descriptors validate without rewriting legacy strings or accepting host bindings', () => {
  const workflow = readyWorkflow();
  workflow.requirements.executables = [{ name: 'python', version: '>=3.11,<4', python_modules: ['yaml', 'requests'] }];
  const before = JSON.stringify(workflow);
  valid(workflow);
  assert.equal(JSON.stringify(workflow), before);

  const legacy = readyWorkflow();
  legacy.requirements.executables = ['python'];
  valid(legacy);
  assert.deepEqual(legacy.requirements.executables, ['python']);

  for (const requirement of [
    { name: 'python', path: 'C:\\host\\python.exe' },
    { name: 'python', command: 'python -c "print(1)"' },
    { name: 'python', probe: 'arbitrary code' },
  ]) {
    const invalidWorkflow = readyWorkflow();
    invalidWorkflow.requirements.executables = [requirement];
    assert.equal(validateWorkflowGraph(invalidWorkflow).valid, false, JSON.stringify(requirement));
  }

  const localPath = readyWorkflow();
  localPath.requirements.executables = ['C:\\host\\python.exe'];
  assert.equal(validateWorkflowGraph(localPath).valid, false);
});

test('reviewer role does not decide write authority; explicit access and Provider capability do', () => {
  const workflow = withWork(); const worker = workflow.nodes.find(node => node.id === 'work');
  Object.assign(worker, { role: 'reviewer', executor: { kind: 'provider', provider_id: 'p' },
    access: 'bounded_write', path_scope: { binding: 'run.allowed_paths' } });
  const provider = { id: 'p', kind: 'native_agent', enabled: true,
    capabilities: { read: true, write: true }, config: { role: 'reviewer' } };
  valid(workflow, { providers: [provider] });
  provider.capabilities.write = false;
  invalid(workflow, 'PROVIDER_CAPABILITY', { providers: [provider] });
});

test('sub-Agent quantity is configurable only on non-Main Agent nodes and fan-out stays finite and typed',()=>{
  const workflow=withWork(),worker=workflow.nodes.find(node=>node.id==='work');
  workflow.inputs_schema={type:'object',properties:{items:{type:'array',minItems:1,maxItems:32,items:{type:'string'}}},required:['items'],additionalProperties:false};
  Object.assign(worker,{executor:{kind:'thread',provider_id:'p',lifecycle:'start'},subagent_count:'auto',input_bindings:{items:'/inputs/items'},outputs_schema:{type:'object',properties:{results:{type:'array',items:{type:'string'}}},required:['results'],additionalProperties:false},fanout:{input:'items',item_name:'item',result_output:'results',distribution:'one_per_item',scheduling:'parallel',join:'all_required'}});
  workflow.skill_policy={mode:'cooperative',implicit:'allow',ambient_allow:[],shadowed_skill_paths:[]};
  const context={providers:[{id:'p',kind:'native_agent',enabled:true,capabilities:{read:true,write:true},config:{role:'implementer'}}]};
  valid(workflow,context);
  worker.fanout.result_mode='per_item';invalid(workflow,'SUBAGENT_FANOUT',context);
  worker.executor={kind:'provider',provider_id:'p'};valid(workflow,context);
  delete worker.fanout.result_mode;worker.executor={kind:'thread',provider_id:'p',lifecycle:'start'};
  worker.executor={kind:'main'};invalid(workflow,'SUBAGENT_COUNT',context);invalid(workflow,'SUBAGENT_FANOUT',context);
  worker.executor={kind:'thread',provider_id:'p',lifecycle:'start'};worker.subagent_count=4;delete worker.fanout;invalid(workflow,'SUBAGENT_FANOUT',context);
  worker.fanout={input:'items',item_name:'item',result_output:'results',distribution:'one_per_item',scheduling:'parallel',join:'all_required'};invalid(workflow,'SUBAGENT_FANOUT',context);
  worker.fanout.distribution='partition';workflow.inputs_schema.properties.items.minItems=4;valid(workflow,context);
  worker.subagent_count='auto';worker.fanout.batch_size=20;workflow.inputs_schema.properties.items.minItems=1;worker.outputs_schema.properties.results.items={type:'array',items:{type:'string'}};valid(workflow,context);
  worker.fanout.batch_size=0;invalid(workflow,'SUBAGENT_FANOUT',context);
  worker.fanout.batch_size=20;worker.fanout.distribution='one_per_item';invalid(workflow,'SUBAGENT_FANOUT',context);
  worker.fanout.distribution='partition';worker.subagent_count=4;invalid(workflow,'SUBAGENT_FANOUT',context);
  delete worker.fanout.batch_size;worker.subagent_count=4;worker.outputs_schema.properties.results.items={type:'string'};
  workflow.skill_policy={mode:'strict',implicit:'deny',ambient_allow:[],shadowed_skill_paths:[]};invalid(workflow,'STRICT_FANOUT_UNSUPPORTED',context);
  workflow.skill_policy={mode:'cooperative',implicit:'allow',ambient_allow:[],shadowed_skill_paths:[]};
  workflow.inputs_schema.properties.items={type:'string'};invalid(workflow,'SUBAGENT_FANOUT_INPUT_SCHEMA',context);
  workflow.inputs_schema.properties.items={type:'array',minItems:1,maxItems:1,items:{type:'string'}};worker.subagent_count=2;invalid(workflow,'SUBAGENT_FANOUT_CARDINALITY',context);
  workflow.inputs_schema.properties.items={type:'array',minItems:1,maxItems:4,items:{type:'string'}};worker.outputs_schema.properties.results.maxItems=1;invalid(workflow,'SUBAGENT_FANOUT_CARDINALITY',context);
  delete worker.outputs_schema.properties.results.maxItems;worker.subagent_count='auto';worker.fanout.distribution='one_per_item';
  workflow.inputs_schema.properties.items={type:'array',minItems:33,maxItems:33,items:{type:'string'}};invalid(workflow,'SUBAGENT_FANOUT_CARDINALITY',context);
  workflow.inputs_schema.properties.fallback={};worker.input_bindings.items={coalesce:['/inputs/items','/inputs/fallback']};invalid(workflow,'SUBAGENT_FANOUT_CARDINALITY',context);
  workflow.inputs_schema.properties.items={type:'array',minItems:0,maxItems:0,items:{type:'string'}};invalid(workflow,'SUBAGENT_FANOUT_CARDINALITY',context);
  worker.subagent_count=2;worker.fanout.distribution='partition';workflow.inputs_schema.properties.items={type:'array',minItems:3,maxItems:4,items:{type:'string'}};invalid(workflow,'SUBAGENT_FANOUT_CARDINALITY',context);
  worker.subagent_count='auto';worker.fanout.distribution='one_per_item';workflow.inputs_schema.properties.items={type:'array',minItems:4,maxItems:4,items:{type:'string'}};worker.outputs_schema.properties.results.maxItems=3;invalid(workflow,'SUBAGENT_FANOUT_CARDINALITY',context);
  worker.input_bindings.items='/inputs/items';
  delete worker.outputs_schema.properties.results.maxItems;workflow.inputs_schema.properties.items={};worker.fanout.distribution='one_per_item';valid(workflow,context);
  worker.subagent_count=33;invalid(workflow,'SUBAGENT_COUNT',context);
  worker.subagent_count='auto';delete worker.fanout;worker.executor={kind:'thread',provider_id:'p',lifecycle:'continue',source_node:'missing'};
  assert.equal(validateWorkflowGraph(workflow,context).errors.some(error=>error.code==='SUBAGENT_COUNT'),false);
  worker.subagent_count=1;invalid(workflow,'SUBAGENT_COUNT',context);
});

test('path-isolated per-item writers must hand declared shared changes to one downstream writer',()=>{
  const workflow=readyWorkflow(),writer=agent('writer'),integrator=agent('integrator');
  workflow.nodes.splice(1,0,writer,integrator);
  workflow.edges=[edge('start','writer'),edge('writer','integrator'),edge('integrator','final'),edge('final','end')];
  workflow.skill_policy={mode:'cooperative',implicit:'allow',ambient_allow:[],shadowed_skill_paths:[]};
  workflow.inputs_schema={type:'object',additionalProperties:false,required:['items'],properties:{items:{type:'array',minItems:1,items:{type:'object',additionalProperties:false,required:['write_paths'],properties:{write_paths:{type:'array',minItems:1,items:{type:'string'}}}}}}};
  Object.assign(writer,{executor:{kind:'provider',provider_id:'p'},access:'bounded_write',path_scope:{binding:'run.allowed_paths'},subagent_count:'auto',
    input_bindings:{items:'/inputs/items'},outputs_schema:{type:'object',additionalProperties:false,required:['results'],properties:{results:{type:'array',minItems:1,items:{type:'object',additionalProperties:false,required:['changes','shared_change'],properties:{changes:{type:'string'},shared_change:{type:'string'}}}}}},
    fanout:{input:'items',item_name:'item',result_output:'results',distribution:'partition',scheduling:'parallel',join:'all_required',batch_size:10,result_mode:'per_item',write_paths_field:'write_paths',shared_change_field:'shared_change'}});
  Object.assign(integrator,{access:'bounded_write',path_scope:{binding:'run.allowed_paths'},input_bindings:{requests:{path:'/nodes/writer/output/results',pluck:'shared_change'}},
    outputs_schema:{type:'object',additionalProperties:false,required:['all_passed'],properties:{all_passed:{type:'boolean'}}},
    completion_contract:{on_missing:'block',outcome:'validated_artifact',fail_on_false:['all_passed']}});
  const context={providers:[{id:'p',kind:'native_agent',enabled:true,capabilities:{read:true,write:true},config:{role:'implementer'}}]};
  valid(workflow,context);
  const second=agent('second-integrator');Object.assign(second,{access:'bounded_write',path_scope:{binding:'run.allowed_paths'},input_bindings:{requests:{path:'/nodes/writer/output/results',pluck:'shared_change'}}});
  workflow.nodes.splice(workflow.nodes.indexOf(integrator)+1,0,second);
  workflow.edges=[edge('start','writer'),edge('writer','integrator'),edge('integrator','second-integrator'),edge('second-integrator','final'),edge('final','end')];
  invalid(workflow,'SUBAGENT_SHARED_CHANGE_HANDOFF',context);
  workflow.nodes=workflow.nodes.filter(node=>node.id!=='second-integrator');workflow.edges=[edge('start','writer'),edge('writer','integrator'),edge('integrator','final'),edge('final','end')];
  delete integrator.completion_contract.fail_on_false;invalid(workflow,'SUBAGENT_SHARED_CHANGE_COMPLETION',context);
  integrator.completion_contract.fail_on_false=['all_passed'];
  integrator.access='read_only';delete integrator.path_scope;invalid(workflow,'SUBAGENT_SHARED_CHANGE_HANDOFF',context);
  integrator.access='bounded_write';integrator.path_scope={binding:'run.allowed_paths'};writer.fanout.shared_change_field='missing';
  invalid(workflow,'SUBAGENT_SHARED_CHANGE_SCHEMA',context);
  writer.fanout.shared_change_field='shared_change';delete writer.fanout.write_paths_field;invalid(workflow,'SUBAGENT_FANOUT',context);
});

test('project-memory files cannot become required product artifacts',()=>{
  const workflow=withWork(),worker=workflow.nodes.find(node=>node.id==='work');
  worker.access='bounded_write';worker.path_scope={binding:'run.allowed_paths'};
  worker.required_artifacts=[{requirement_id:'memory_progress',path:'project_memory/progress.md'}];
  invalid(workflow,'OPERATIONAL_MEMORY_ARTIFACT');
});

test('import metadata cannot retain references to removed workflow nodes',()=>{
  const workflow=readyWorkflow();
  workflow.import_status={
    mode:'ai_expanded',unresolved:[],conversion_level:'agent_assisted',conversion_contract_version:3,
    requirement_coverage:[],source_dispositions:[{section_id:'loop',node_ids:['final','removed-memory-node']}],
  };
  invalid(workflow,'IMPORT_NODE_REFERENCE');
  workflow.import_status.source_dispositions[0].node_ids=['final'];
  valid(workflow);
});

test('parallel write fan-out requires Host-owned per-item write paths',()=>{
  const workflow=withWork(),worker=workflow.nodes.find(node=>node.id==='work');
  workflow.skill_policy={mode:'cooperative',implicit:'allow',ambient_allow:[],shadowed_skill_paths:[]};
  workflow.inputs_schema={type:'object',properties:{items:{type:'array',minItems:1,maxItems:32,items:{type:'object',additionalProperties:false,properties:{write_paths:{type:'array',minItems:1,items:{type:'string'}}},required:['write_paths']}}},required:['items'],additionalProperties:false};
  Object.assign(worker,{executor:{kind:'provider',provider_id:'p'},access:'bounded_write',path_scope:{binding:'run.allowed_paths'},subagent_count:'auto',input_bindings:{items:'/inputs/items'},outputs_schema:{type:'object',properties:{results:{type:'array',items:{type:'string'}}},required:['results'],additionalProperties:false},fanout:{input:'items',item_name:'item',result_output:'results',distribution:'partition',batch_size:10,scheduling:'parallel',max_concurrency:2,join:'all_required'}});
  const context={providers:[{id:'p',kind:'native_agent',enabled:true,capabilities:{read:true,write:true},config:{role:'implementer'}}]};
  invalid(workflow,'SUBAGENT_WRITE_ISOLATION',context);
  worker.fanout.write_paths_field='write_paths';
  valid(workflow,context);
  delete worker.fanout.write_paths_field;worker.fanout.max_concurrency=1;
  valid(workflow,context);
  worker.fanout.scheduling='serial';delete worker.fanout.max_concurrency;delete worker.fanout.write_paths_field;
  valid(workflow,context);
});

test('per-item write packets cannot hide Agent output behind a Host tool',()=>{
  const workflow=readyWorkflow(),planner=agent('planner'),wrapper={id:'wrapper',type:'tool',executor:{kind:'tool',tool:'join_packets'},access:'read_only',approval:{required:false},retry:{max_attempts:3},input_bindings:{items:'/nodes/planner/output/items'}},writer=agent('writer'),integrator=agent('integrator');
  const items={type:'array',minItems:1,items:{type:'object',additionalProperties:false,required:['write_paths'],properties:{write_paths:{type:'array',minItems:1,items:{type:'string'}}}}};
  planner.outputs_schema={type:'object',additionalProperties:false,required:['items'],properties:{items:structuredClone(items)}};
  wrapper.outputs_schema={type:'object',additionalProperties:false,required:['items'],properties:{items:structuredClone(items)}};
  Object.assign(writer,{executor:{kind:'provider',provider_id:'p'},access:'bounded_write',path_scope:{binding:'run.allowed_paths'},subagent_count:'auto',input_bindings:{items:'/nodes/wrapper/output/items'},
    outputs_schema:{type:'object',additionalProperties:false,required:['results'],properties:{results:{type:'array',minItems:1,items:{type:'object',additionalProperties:false,required:['changes','shared_change'],properties:{changes:{type:'string'},shared_change:{type:'string'}}}}}},
    fanout:{input:'items',item_name:'item',result_output:'results',distribution:'partition',scheduling:'parallel',join:'all_required',batch_size:10,result_mode:'per_item',write_paths_field:'write_paths',shared_change_field:'shared_change'}});
  Object.assign(integrator,{access:'bounded_write',path_scope:{binding:'run.allowed_paths'},input_bindings:{requests:{path:'/nodes/writer/output/results',pluck:'shared_change'}}});
  workflow.nodes.splice(1,0,planner,wrapper,writer,integrator);
  workflow.edges=[edge('start','planner'),edge('planner','wrapper'),edge('wrapper','writer'),edge('writer','integrator'),edge('integrator','final'),edge('final','end')];
  workflow.skill_policy={mode:'cooperative',implicit:'allow',ambient_allow:[],shadowed_skill_paths:[]};
  const context={providers:[{id:'p',kind:'native_agent',enabled:true,capabilities:{read:true,write:true},config:{role:'implementer'}}]};
  invalid(workflow,'SUBAGENT_ITEM_SOURCE',context);
});

test('a pinned Host selector may filter on Agent verdicts while deriving every packet identity field from Host inputs',()=>{
  const workflow=readyWorkflow(),review=agent('review'),selector={id:'selector',type:'tool',executor:{kind:'tool',tool:'select_repairs'},access:'read_only',approval:{required:false},retry:{max_attempts:1},input_bindings:{manifest:'/inputs/manifest',verdicts:'/nodes/review/output/verdicts'}},writer=agent('writer');
  const item={type:'object',additionalProperties:false,required:['packet_path','packet_sha256','write_paths'],properties:{packet_path:{type:'string'},packet_sha256:{type:'string'},write_paths:{type:'array',minItems:1,items:{type:'string'}}}};
  const items={type:'array',minItems:1,items:item};
  workflow.inputs_schema={type:'object',additionalProperties:false,required:['manifest'],properties:{manifest:{type:'string'}}};
  review.outputs_schema={type:'object',additionalProperties:false,required:['verdicts'],properties:{verdicts:{type:'array',minItems:1,items:{type:'boolean'}}}};
  selector.outputs_schema={type:'object',additionalProperties:false,required:['repair_jobs'],properties:{repair_jobs:items}};
  Object.assign(writer,{executor:{kind:'provider',provider_id:'p'},access:'bounded_write',path_scope:{binding:'run.allowed_paths'},subagent_count:'auto',input_bindings:{repair_jobs:'/nodes/selector/output/repair_jobs'},
    outputs_schema:{type:'object',additionalProperties:false,required:['results'],properties:{results:{type:'array',minItems:1,items:{type:'object',additionalProperties:false,required:['evidence'],properties:{evidence:{type:'string'}}}}}},
    fanout:{input:'repair_jobs',item_name:'repair job',result_output:'results',distribution:'partition',scheduling:'parallel',max_concurrency:2,join:'all_required',batch_size:10,result_mode:'per_item',write_paths_field:'write_paths'}});
  workflow.nodes.splice(1,0,review,selector,writer);
  workflow.edges=[edge('start','review'),edge('review','selector'),edge('selector','writer'),edge('writer','final'),edge('final','end')];
  workflow.skill_policy={mode:'cooperative',implicit:'allow',ambient_allow:[],shadowed_skill_paths:[]};
  workflow.host_tools=[{id:'select_repairs',identity:{name:'select_repairs',version:'1',sha256:'a'.repeat(64)},argv:['select_repairs'],input_schema:{type:'object',additionalProperties:false,required:['manifest','verdicts'],properties:{manifest:{type:'string'},verdicts:{type:'array',minItems:1,items:{type:'boolean'}}}},output_schema:selector.outputs_schema,env_allow:[],permissions:{network:false,read_paths:[],write_paths:[]},output_cap_bytes:4096,deadline_ms:1000,idempotency:{mode:'safe'},host_owned_item_fields:[{output:'repair_jobs',fields:['packet_path','packet_sha256','write_paths'],from_inputs:['manifest']}]}];
  const context={providers:[{id:'p',kind:'native_agent',enabled:true,capabilities:{read:true,write:true},config:{role:'implementer'}}],host_tools:['select_repairs']};
  valid(workflow,context);
  workflow.host_tools[0].host_owned_item_fields[0].from_inputs=['verdicts'];
  invalid(workflow,'SUBAGENT_ITEM_SOURCE',context);
});

test('Skill references detect missing and stale sources', () => {
  const workflow = withWork(); const worker = workflow.nodes.find(n => n.id === 'work');
  workflow.skill_policy.mode = 'strict'; workflow.skill_policy.implicit = 'deny';
  worker.type = 'skill_ref'; worker.skill_ref = { path: '/synthetic/SKILL.md', name: 'synthetic', source_hash: 'a'.repeat(64), expected_version: '1', allowed_nested_skills: [] };
  const context = { skills: [{ path: worker.skill_ref.path, source_hash: worker.skill_ref.source_hash, version: '1' }] };
  valid(workflow, context); invalid(workflow, 'SKILL_MISSING');
  context.skills[0].source_hash = 'b'.repeat(64); invalid(workflow, 'SKILL_STALE', context);
});

test('SubWorkflow references require pinned existence and reject recursive paths', () => {
  const workflow = withWork(); const worker = workflow.nodes.find(n => n.id === 'work');
  worker.type = 'subworkflow'; worker.executor = { kind: 'subworkflow' }; worker.subworkflow = { workflow_id: 'child', revision_pin: 'a'.repeat(64), output_bindings: { result: '/output' } };
  const child = readyWorkflow('child');
  const context = { workflows: { ['child@' + 'a'.repeat(64)]: child } };
  valid(workflow, context); invalid(workflow, 'SUBWORKFLOW_MISSING');
  const childWorker = { id: 'recursive', type: 'subworkflow', subworkflow: { workflow_id: workflow.id, revision_pin: 'b'.repeat(64) } };
  child.nodes.splice(1, 0, childWorker); child.edges = [edge('start', 'recursive'), edge('recursive', 'final'), edge('final', 'end')];
  invalid(workflow, 'SUBWORKFLOW_INVALID', context);
  const error = validateWorkflowGraph(workflow, context).errors.find(e => e.code === 'SUBWORKFLOW_INVALID');
  assert(error.child_errors.some(e => e.code === 'SUBWORKFLOW_CYCLE'));
});

test('finite condition language has typed comparisons, JSON Pointer and short-circuit guards', () => {
  const literal = value => ({ value }); const expr = (op, ...args) => ({ op, args });
  for (const [op, a, b] of [['eq', 1, 1], ['ne', 1, '1'], ['contains', [1, 2], 2], ['contains', 'abcd', 'bc'], ['in', 2, [1, 2]], ['gt', 2, 1], ['gte', 2, 2], ['lt', 1, 2], ['lte', 1, 1]]) assert.equal(evaluateExpression(expr(op, literal(a), literal(b)), {}), true);
  const optional = expr('and', expr('exists', { path: '/absent' }), expr('eq', { path: '/absent' }, literal(1)));
  assert.equal(evaluateExpression(optional, {}), false);
  assert.equal(evaluateExpression(expr('or', literal(true), expr('eq', { path: '/absent' }, literal(1))), {}), true);
  assert.equal(evaluateExpression(expr('not', literal(false)), {}), true);
  assert.throws(() => evaluateExpression(expr('gt', literal('2'), literal(1)), {}), { code: 'CONDITION_TYPE' });
  assert.deepEqual(readPointer({ 'a/b': { '~': 3 } }, '/a~1b/~0'), { found: true, value: 3 });
  assert.throws(() => resolveBindings({ result: '/missing' }, {}), { code: 'BINDING_MISSING' });
  assert.deepEqual({ ...resolveBindings({ result: { coalesce: ['/missing', '/present'] }, optional: { path: '/missing', default: '' } }, { present: 3 }) }, { result: 3, optional: '' });
  assert.throws(() => resolveBindings({ result: { coalesce: ['/missing', '/also-missing'] } }, {}), { code: 'BINDING_MISSING' });
  assert.deepEqual(intersectBoundaries(['src', 'README.md'], ['src/lib', 'README.md', 'other']), ['README.md', 'src/lib']);
});

test('current validation rejects pre-declared context packs and legacy widening', () => {
  const old = readyWorkflow(); delete old.context_projection_version; invalid(old, 'CONTEXT_PROJECTION_VERSION');
  const widened = readyWorkflow(); widened.nodes.find(node => node.id === 'final').context_projection = { legacy_workflow_inputs: true, compatibility_reason: 'Historical compatibility.' };
  invalid(widened, 'LEGACY_CONTEXT_PROJECTION');
});
