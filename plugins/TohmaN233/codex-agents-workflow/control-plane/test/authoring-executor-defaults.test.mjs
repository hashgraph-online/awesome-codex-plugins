import test from 'node:test';
import assert from 'node:assert/strict';
import * as blueprint from '../lib/authoring/blueprint-contract.mjs';
import * as routing from '../lib/skill-import/routing-rules.mjs';
import { generatedNodePermissions } from '../lib/node-permissions.mjs';
import { compileWorkflowBrief } from '../lib/skill-import/workflow-authoring.mjs';
import { WorkflowForge } from '../lib/authoring/workflow-forge.mjs';
import { sourceSectionInventory } from '../lib/skill-import/source-dispositions.mjs';
import { prepareResources, revisionHash } from '../lib/workflow-revisions.mjs';
import { validateGenerationProposal } from '../lib/skill-import/proposal-validation.mjs';
import { BUILTIN_NATIVE_AGENT_PROFILES, BUILTIN_NATIVE_PROVIDER_METADATA } from '../lib/native-provider-identity.mjs';
import { expansionPacket } from '../lib/skill-import/semantic-expander.mjs';

const providers=[
  {id:'configured-worker',kind:'native_agent',enabled:true,capabilities:{read:true,write:true}},
  {id:'other-worker',kind:'native_agent',enabled:true,capabilities:{read:true,write:true}},
];
const rules=mode=>({version:1,instructions:'Use the configured model connections.',selection_mode:mode,
  routes:Object.fromEntries(routing.TASK_TYPES.map(type=>[type,{provider_id:'configured-worker'}]))});
const compactActivity=(profile,extra={})=>({key:'work',instructions:'Produce the requested semantic result.',profile,
  source_sections:['section'],inputs:[],outputs:[{name:'result',kind:'text',values:[],type_ref:''}],tool:'',...extra});
const compactPlan=activity=>({contract:blueprint.SEMANTIC_BLUEPRINT_CONTRACT,purpose:'Produce the requested result.',
  source_dispositions:[{section_id:'section',disposition:'workflow',activity_keys:['work'],note:'Required.'}],
  requirement_assignments:[],runtime_dependencies:[],records:[],lists:[],enums:[],activities:[activity],
  approvals:[],sequences:[],parallels:[],choices:[]});
const routedNode=extra=>({task_type:'implementation',routing_reason:'Bounded independent production.',...extra});
function forgeFixture(){
  const seed=compileWorkflowBrief({workflow_id:'executor-default-fixture',name:'Executor default fixture',
    brief:'# Workflow\n\n## Work\n\nProduce the requested result.',provider_id:'configured-worker'});
  const snapshot={workflow:seed.workflow,resources:prepareResources(seed.resources).manifest,provenance:seed.provenance,import_report:seed.import_report};
  return {pack:{...snapshot,revision_hash:revisionHash(snapshot)},resources:seed.resources,sections:sourceSectionInventory(seed.resources).map(item=>item.section_id)};
}
function sourcePlan(profile,sections){
  const plan=compactPlan(compactActivity(profile,{source_sections:sections}));
  plan.source_dispositions=sections.map(section_id=>({section_id,disposition:'workflow',activity_keys:['work'],note:'Required.'}));
  return plan;
}

test('compact generated worker profiles normalize before Main-specific fanout validation',()=>{
  for(const profile of ['main_read','main_write','worker_read','worker_write','review']){
    const original=compactPlan(compactActivity(profile)),snapshot=structuredClone(original);
    const normalized=blueprint.normalizeGeneratedSemanticBlueprint(original);
    assert.equal(normalized.activities[0].ownership,'isolated_worker');
    assert.equal(normalized.activities[0].main_mode,undefined);
    assert.equal(normalized.activities[0].instructions,original.activities[0].instructions);
    assert.deepEqual(original,snapshot,'the persisted planner result stays immutable');
  }
  const fanout=compactActivity('main_write',{inputs:[{name:'items',from:'input:items'}],outputs:[{name:'results',kind:'list',values:[],type_ref:''}],
    fanout:{input:'items',item_name:'item',result_output:'results',count_mode:'auto',fixed_count:0,max_concurrency:1}});
  assert.equal(blueprint.normalizeGeneratedSemanticBlueprint(compactPlan(fanout)).activities[0].ownership,'isolated_worker');
});

test('generation normalizes legacy Main workers and preserves Main orchestration, decisions and Host tools',()=>{
  for(const contract of [blueprint.LEGACY_SEMANTIC_BLUEPRINT_CONTRACT,blueprint.PREVIOUS_SEMANTIC_BLUEPRINT_CONTRACT]){
    const internal=blueprint.normalizeSemanticBlueprint(compactPlan(compactActivity('main_write')));
    internal.contract=contract;
    internal.activities[0].main_mode='worker';
    const worker=blueprint.normalizeGeneratedSemanticBlueprint(internal).activities[0];
    assert.equal(worker.ownership,'isolated_worker');assert.equal(worker.main_mode,undefined);
    assert.equal(blueprint.normalizeSemanticBlueprint(internal).activities[0].ownership,'main','manual normalization remains compatible');
  }
  for(const profile of ['orchestration_read','orchestration_write','decision']){
    const actual=blueprint.normalizeGeneratedSemanticBlueprint(compactPlan(compactActivity(profile))).activities[0];
    assert.equal(actual.ownership,'main');assert.equal(actual.main_mode,'orchestration');
  }
  const tool=compactActivity('main_write',{tool:'registered-script'});
  assert.deepEqual(blueprint.normalizeGeneratedActivity(tool),tool);
  const isolated=blueprint.normalizeGeneratedActivity({key:'work',kind:'work',ownership:'main',main_mode:'worker',continues:'',
    fanout:{workspace_field:'item_workspace',write_paths_field:'owned_paths'}});
  assert.deepEqual(isolated.fanout,{write_paths_field:'owned_paths'});
});

test('unqualified generated task lineage produces one actionable source semantic finding',()=>{
  for(const activity of [compactActivity('worker_write',{task_continues:'earlier'}),{key:'work',kind:'work',ownership:'isolated_worker',continues:'earlier'}]){
    assert.throws(()=>blueprint.normalizeGeneratedActivity(activity),error=>{
      assert.equal(error.code,'AUTHORING_SEMANTIC');assert.equal(error.findings.length,1);
      assert.equal(error.findings[0].code,'generated_task_lineage');
      assert.deepEqual(error.findings[0].semantic_keys,['work','earlier']);
      assert.match(error.findings[0].minimal_change,/worker|loop/);return true;
    });
  }
  const span={resource:'source/WORKFLOW.md',start_line:3,end_line:5};
  assert.throws(()=>blueprint.normalizeGeneratedActivity(compactActivity('worker_write',{task_continues:'earlier'}),
    {sectionInventory:[{section_id:'section',source_span:span}]}),error=>{
      assert.deepEqual(error.findings[0].source_refs,[span]);return true;
    });
  for(const invalid of [{key:'work',kind:'decision',ownership:'unknown'},{key:'work',kind:'decision',ownership:'main',main_mode:'unknown'}]){
    assert.deepEqual(blueprint.normalizeGeneratedActivity(invalid),invalid,'executor normalization must not hide malformed semantic fields');
  }
});

test('fixed and automatic generation use the configured existing writable Provider',()=>{
  for(const mode of ['automatic','fixed'])for(const choice of [undefined,'main','thread','subagent']){
    const node=routedNode({execution_target:choice,provider_choice:'other-worker',main_mode:choice==='main'?'worker':undefined});
    assert.deepEqual(routing.routeGeneratedAgent(node,rules(mode),providers),{executor:{kind:'provider',provider_id:'configured-worker'}});
    assert.deepEqual(generatedNodePermissions(),{access:'bounded_write',path_scope:{binding:'run.allowed_paths'}});
    assert.equal(Object.hasOwn(routing.routeGeneratedAgent(node,rules(mode),providers),'role'),false);
  }
});

test('generation fails visibly for missing, disabled, read-only or unpinned configured Provider without Main fallback',()=>{
  assert.throws(()=>routing.routeGeneratedAgent(routedNode(),undefined,providers),{code:'ROUTING_PROVIDER_UNAVAILABLE'});
  for(const mode of ['automatic','fixed']){
    for(const available of [[],providers.map(item=>({...item,enabled:false}))]){
      assert.throws(()=>routing.routeGeneratedAgent(routedNode({execution_target:'main'}),rules(mode),available),{code:'ROUTING_PROVIDER_UNAVAILABLE'});
    }
    assert.throws(()=>routing.routeGeneratedAgent(routedNode({execution_target:'main'}),rules(mode),providers.map(item=>({...item,capabilities:{read:true,write:false}}))),{code:'EXPANSION_WRITE_PROVIDER'});
    assert.throws(()=>routing.routeGeneratedAgent(routedNode(),rules(mode),providers,[]),{code:'ROUTING_PROVIDER_UNAVAILABLE'});
  }
});

test('manual Main worker and persistent task options remain explicit and generated orchestration stays Main',()=>{
  const automatic=rules('automatic');
  assert.deepEqual(routing.routeAgent(routedNode({main_mode:'worker'}),automatic,providers),{executor:{kind:'main',mode:'worker'}});
  assert.deepEqual(routing.routeAgent(routedNode({execution_target:'thread',provider_choice:'other-worker',thread_lifecycle:'start'}),automatic,providers),
    {executor:{kind:'thread',provider_id:'other-worker',lifecycle:'start'}});
  assert.deepEqual(routing.routeGeneratedAgent(routedNode({main_mode:'orchestration'}),rules('fixed'),[]),{executor:{kind:'main',mode:'orchestration'}});
  assert.throws(()=>routing.routeGeneratedAgent(routedNode({execution_target:'thread',thread_lifecycle:'continue',thread_source_node:'earlier'}),automatic,providers),{code:'AUTHORING_SEMANTIC'});
  assert.equal(blueprint.GENERATION_EXECUTOR_OPTIONS.provider.default_for,'independent_workers');
  assert.equal(blueprint.GENERATION_EXECUTOR_OPTIONS.main_worker.selection,'explicit_user_edit');
  assert.equal(blueprint.GENERATION_EXECUTOR_OPTIONS.thread.selection,'explicit_user_edit');
});

test('real Forge compact and legacy compilation emits writable Provider workers in either routing mode',()=>{
  const {pack,resources,sections}=forgeFixture();
  for(const mode of ['automatic','fixed'])for(const profile of ['main_read','main_write','worker_write','review','orchestration_read','decision']){
    const original=sourcePlan(profile,sections);
    const plans=profile==='main_write'?[original,blueprint.normalizeSemanticBlueprint(original)]:[original];
    for(const plan of plans){
      const compiled=new WorkflowForge().compile({pack,resources,blueprint:plan,
        context:{routing_rules:rules(mode),providers,routing_catalog:routing.routingCatalog(providers)}}).compiled;
      assert.equal(compiled.validation.valid,true);
      const work=compiled.workflow.nodes.find(node=>node.origin?.semantic_key==='work');
      assert.ok(work);
      if(['orchestration_read','decision'].includes(profile))assert.deepEqual(work.executor,{kind:'main',mode:'orchestration'});
      else assert.deepEqual(work.executor,{kind:'provider',provider_id:'configured-worker'});
      assert.equal(work.access,'bounded_write');assert.deepEqual(work.path_scope,{binding:'run.allowed_paths'});
      assert.equal(Object.hasOwn(work,'role'),false);assert.equal(Object.hasOwn(work,'role_ref'),false);
    }
    if(!['orchestration_read','decision'].includes(profile)){
      assert.throws(()=>new WorkflowForge().compile({pack,resources,blueprint:original,
        context:{providers,routing_catalog:routing.routingCatalog(providers)}}),{code:'ROUTING_RULES_REQUIRED'});
      assert.throws(()=>new WorkflowForge().compile({pack,resources,blueprint:original,
        context:{routing_rules:rules(mode),providers:providers.map(item=>({...item,capabilities:{read:true,write:false}}))}}),{code:'EXPANSION_WRITE_PROVIDER'});
    }
  }
});

test('new generation pins Provider defaults while historical authoring replay retains its executor choices',()=>{
  const {pack,resources,sections}=forgeFixture(),plan=sourcePlan('main_write',sections);
  for(const pinnedPolicy of [undefined,'provider-subagents/v1']){
    const provenance={source_revision:pack.revision_hash,routing_rules:rules('automatic'),routing_catalog:routing.routingCatalog(providers),
      ...(pinnedPolicy?{generation_executor_policy:pinnedPolicy}:{})};
    const options={pack,resources,provenance,context:{providers}};
    const initial=validateGenerationProposal({proposal:plan},options);
    const initialWork=initial.compiled.workflow.nodes.find(node=>node.origin?.semantic_key==='work');
    assert.deepEqual(initialWork.executor,pinnedPolicy?{kind:'provider',provider_id:'configured-worker'}:{kind:'main'});
    assert.equal(initialWork.access,'bounded_write');
    const trace=initial.pipeline_trace,persisted=JSON.parse(JSON.stringify({proposal:initial.proposal,
      host_pipeline:{contract:trace.contract,proposal_hash:trace.proposal_hash,results:trace.results}}));
    const replay=validateGenerationProposal(persisted,options);
    assert.deepEqual(replay.compiled.workflow.nodes.find(node=>node.origin?.semantic_key==='work').executor,initialWork.executor);
    assert.equal(replay.pipeline_trace.proposal_hash,trace.proposal_hash);
  }
});

test('generated routing distinguishes routine reading, independent review, hard reasoning and current Main decisions',()=>{
  const {pack,resources,sections}=forgeFixture();
  const available=Object.entries(BUILTIN_NATIVE_AGENT_PROFILES).map(([id,config])=>({id,config,
    ...BUILTIN_NATIVE_PROVIDER_METADATA[id],kind:'native_agent',enabled:true,capabilities:{read:true,write:true}}));
  const expected={worker_read:'native-luna',worker_write:'native-luna',worker_complex_read:'native-sol',
    worker_complex_write:'native-sol',review:'native-sol',worker_reasoning:'native-astra',
    orchestration_read:'main',orchestration_write:'main',decision:'main'};
  for(const mode of ['automatic','fixed'])for(const [profile,provider] of Object.entries(expected)){
    const configured={...routing.defaultRoutingRules(available),selection_mode:mode};
    const result=new WorkflowForge().compile({pack,resources,blueprint:sourcePlan(profile,sections),
      context:{routing_rules:configured,providers:available,routing_catalog:routing.routingCatalog(available)}});
    const node=result.compiled.workflow.nodes.find(item=>item.origin?.semantic_key==='work');
    assert.equal(result.compiled.validation.valid,true);
    assert.deepEqual(node.executor,provider==='main'?{kind:'main',mode:'orchestration'}:{kind:'provider',provider_id:provider},profile);
  }
  const pinned={source_revision:pack.revision_hash,generation_executor_policy:'provider-subagents/v1',
    routing_rules:routing.defaultRoutingRules(available),routing_catalog:routing.routingCatalog(available)};
  const old=validateGenerationProposal({proposal:sourcePlan('worker_read',sections)},
    {pack,resources,provenance:pinned,context:{providers:available}});
  assert.equal(old.compiled.workflow.nodes.find(item=>item.origin?.semantic_key==='work').executor.provider_id,'native-astra',
    'historical accepted proposals retain their pinned v1 routing, rather than silently changing on replay');
  const current=validateGenerationProposal({proposal:sourcePlan('worker_read',sections)},
    {pack,resources,provenance:{...pinned,generation_executor_policy:'provider-subagents/v2'},context:{providers:available}});
  assert.equal(current.compiled.workflow.nodes.find(item=>item.origin?.semantic_key==='work').executor.provider_id,'native-luna');
});

test('actual planner and reviewer packets expose configured model suitability beside semantic profile selection',()=>{
  const {pack,resources}=forgeFixture();
  const available=[{id:'configured-worker',enabled:true,kind:'native_agent',capabilities:{read:true,write:true},
    config:{model:'custom-model',reasoning_effort:'high'},description:'Only use this connection for evidence-based repository inspection.'}];
  for(const audience of ['planner','reviewer']){
    const packet=expansionPacket(pack,resources,available[0],rules('automatic'),available,{audience});
    assert.ok(packet.prompt.includes(available[0].description),`${audience} must actually receive the description, not just durable provenance`);
    assert.ok(packet.prompt.includes('custom-model'));
    assert.match(packet.prompt,/Main orchestration|Main O/);
    assert.match(packet.prompt,/worker_reasoning/);
    assert.match(packet.prompt,/difficult|hard reasoning/);
  }
});
