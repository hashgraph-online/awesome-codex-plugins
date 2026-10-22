import test from 'node:test';
import assert from 'node:assert/strict';
import { join, resolve } from 'node:path';
import { compileWorkflowBrief } from '../lib/skill-import/workflow-authoring.mjs';
import { compileCoarseSkill } from '../lib/skill-import/coarse-compiler.mjs';
import { WorkflowForge } from '../lib/authoring/workflow-forge.mjs';
import { SEMANTIC_BLUEPRINT_CONTRACT } from '../lib/authoring/blueprint-contract.mjs';
import { sourceSectionInventory, disjointSourceSpans } from '../lib/skill-import/source-dispositions.mjs';
import { observedSourceRequirements, projectObservedRequirements } from '../lib/skill-import/source-requirements.mjs';
import { callableInventory } from '../lib/skill-import/callable-inventory.mjs';
import { compileDeployableConversion } from '../lib/skill-import/conversion-deployment.mjs';
import { prepareResources, revisionHash } from '../lib/workflow-revisions.mjs';
import { validateGenerationProposal } from '../lib/skill-import/proposal-validation.mjs';
import { callableBindingIssues } from '../lib/skill-import/callable-runtime-interface.mjs';
import { resolveBindings } from '../lib/workflow-bindings.mjs';

const skillFixtureRoot = resolve('skill-fixture');
const skillFixturePath = join(skillFixtureRoot, 'SKILL.md');

for(const kind of ['skill','brief'])test(`${kind} current Main receives only needed behavioral guides while executable and worker references remain`,()=>{
  const content='# Workflow\n\n## Mandatory procedure\n\nUse `refs/production.md`, `refs/decision.md` and `tools/helper.mjs` for their applicable work. Gather evidence, then let the initiating conversation choose the requested route.\nMethod: preserve verified claims.';
  const supporting={'source/refs/production.md':Buffer.from('# Production\nPreserve verified claims.'),
    'source/refs/decision.md':Buffer.from('# Decision\nUse the requested mode.'),'source/tools/helper.mjs':Buffer.from('export const marker = 1;\n')};
  const build=kind==='brief'?compileWorkflowBrief({workflow_id:`main-resource-${kind}`,name:'Main resource fixture',brief:content,provider_id:'worker'})
    :compileCoarseSkill({source_path:skillFixturePath,root:skillFixtureRoot,source_hash:'a'.repeat(64),instructions_start_line:1,metadata:{name:'Main resource fixture',description:'Gather evidence then choose the user route.'},files:{'source/SKILL.md':Buffer.from(content),...supporting},inventory:[],problems:[],metadata_files:{}},{id:`main-resource-${kind}`,providerId:'worker'});
  const resources={...build.resources,...supporting},snapshot={workflow:build.workflow,resources:prepareResources(resources).manifest,provenance:build.provenance,import_report:build.import_report},pack={...snapshot,revision_hash:revisionHash(snapshot)};
  const ids=sourceSectionInventory(resources).map(item=>item.section_id);
  const plan={contract:SEMANTIC_BLUEPRINT_CONTRACT,purpose:'Gather evidence then choose the user route.',source_dispositions:ids.map(section_id=>({section_id,disposition:'workflow',activity_keys:['work','choose'],note:'Required.'})),
    requirement_assignments:observedSourceRequirements(resources).map(item=>({requirement_id:item.requirement_id,activity_keys:['work']})),runtime_dependencies:[],records:[],lists:[],enums:[],
    activities:[{key:'work',profile:'worker_read',instructions:'Produce concise evidence using the declared production references.',source_sections:ids,inputs:[],outputs:[{name:'findings',kind:'text',values:[],type_ref:''}],tool:''},
      {key:'choose',profile:'decision',instructions:'Choose the requested mode using the supplied findings.',source_sections:ids,inputs:[{name:'findings',from:'work.findings'}],outputs:[{name:'decision',kind:'text',values:[],type_ref:''}],tool:''}],approvals:[],sequences:[],parallels:[],choices:[]};
  for(const needed of [false,true]){
    const candidate=structuredClone(plan);if(needed)candidate.activities[1].instructions+=' Read refs/decision.md for the required decision rule.';
    const result=new WorkflowForge().compile({pack,resources,blueprint:candidate,context}).compiled;
    assert.equal(result.validation.valid,true);
    const main=result.workflow.nodes.find(node=>node.origin?.semantic_key==='choose'),worker=result.workflow.nodes.find(node=>node.origin?.semantic_key==='work');
    assert.equal(main.executor.mode,'orchestration');
    assert.equal(main.resources.includes('source/refs/production.md'),false);
    assert.equal(main.resources.includes('source/refs/decision.md'),needed);
    assert.ok(main.resources.includes('source/tools/helper.mjs'),'executable references are never pruned by document scoping');
    assert.ok(worker.resources.includes('source/refs/production.md'));assert.ok(worker.resources.includes('source/refs/decision.md'));
  }
  const reference=observedSourceRequirements(resources).find(item=>(item.resource_refs??[]).includes('source/refs/production.md'));
  assert.ok(reference,'the regression must exercise an actual required reference');
  const required=structuredClone(plan);required.requirement_assignments.find(item=>item.requirement_id===reference.requirement_id).activity_keys=['choose'];
  const requiredResult=new WorkflowForge().compile({pack,resources,blueprint:required,context}).compiled;
  assert.equal(requiredResult.validation.valid,true);
  assert.ok(requiredResult.workflow.nodes.find(node=>node.origin?.semantic_key==='choose').resources.includes('source/refs/production.md'),'typed requirements are preserved without asking the planner to rewrite a path into prose');
  const primary=kind==='skill'?'source/SKILL.md':'source/WORKFLOW.md';
  const method=observedSourceRequirements(resources).find(item=>item.requirement_kind==='method_rule'&&(item.resource_refs??[]).includes(primary));
  assert.ok(method);
  required.requirement_assignments.find(item=>item.requirement_id===method.requirement_id).activity_keys=['choose'];
  const semantic=new WorkflowForge().compile({pack,resources,blueprint:required,context});
  assert.equal(semantic.compiled.validation.valid,true);
  const deployed=compileDeployableConversion({workflow:semantic.compiled.workflow,proposal:semantic.proposal,resources,pack,proposalHash:semantic.compiled.proposal_hash,reviewContractVersion:15});
  const mainId=semantic.compiled.workflow.nodes.find(node=>node.origin?.semantic_key==='choose').id;
  assert.equal(deployed.workflow.nodes.find(node=>node.id===mainId).resources.some(path=>/SKILL\.md|WORKFLOW\.md/.test(path)),false,'source anchors never reintroduce the private entrypoint after deployment');
  const previous=validateGenerationProposal({proposal:plan},{pack,resources,
    provenance:{source_revision:pack.revision_hash,generation_executor_policy:'provider-subagents/v1',routing_rules:context.routing_rules,routing_catalog:context.providers},context}).compiled;
  assert.ok(previous.workflow.nodes.find(node=>node.origin?.semantic_key==='choose').resources.includes('source/refs/production.md'),'pinned historical Main material stays immutable');
});

const providers=[{id:'worker',enabled:true,kind:'native_agent',capabilities:{read:true,write:true}}];
const routing={version:1,instructions:'Use existing configured providers.',selection_mode:'automatic',routes:Object.fromEntries(['implementation','complex_implementation','planning','review'].map(type=>[type,{provider_id:'worker'}]))};
const context={providers,routing_rules:routing};
for(const kind of ['skill','brief'])test(`${kind} generated final binds its producer without guessing semantic inputs or requiring the private source`,()=>{
  const source='# Workflow\n\n## Procedure\n\nWrite a README using the repository and request.\n';
  const build=kind==='brief'?compileWorkflowBrief({workflow_id:'final-input-brief',name:'Final input',brief:source,provider_id:'worker'}):compileCoarseSkill({metadata:{name:'final-input',description:'Final input'},source_path:skillFixturePath,root:skillFixtureRoot,source_hash:'a'.repeat(64),instructions_start_line:1,files:{'source/SKILL.md':Buffer.from(source)},inventory:[],problems:[],metadata_files:{}},{id:'final-input-skill',providerId:'worker'});
  build.workflow.inputs_schema={type:'object',properties:{task:{type:'string'},mechanical_rows:{type:'array',items:{type:'object'}}},required:[],additionalProperties:true};
  const resources=build.resources,snapshot={workflow:build.workflow,resources:prepareResources(resources).manifest,provenance:build.provenance,import_report:build.import_report},pack={...snapshot,revision_hash:revisionHash(snapshot)},sections=sourceSectionInventory(resources);
  const blueprint={contract:SEMANTIC_BLUEPRINT_CONTRACT,purpose:'Produce requested documentation.',source_dispositions:sections.map(s=>({section_id:s.section_id,disposition:'workflow',activity_keys:['produce'],note:'Required work.'})),requirement_assignments:observedSourceRequirements(resources).map(r=>({requirement_id:r.requirement_id,activity_keys:['produce']})),runtime_dependencies:[],records:[],lists:[],enums:[],activities:[{key:'produce',instructions:'Write the requested documentation using established repository evidence.',profile:'worker_write',source_sections:sections.map(s=>s.section_id),inputs:[{name:'repository',from:'input:repository'},{name:'request',from:'input:request'},{name:'mechanical_rows',from:'input:mechanical_rows'}],outputs:[{name:'handover',kind:'text',values:[],type_ref:''}],tool:''}],approvals:[],sequences:[],parallels:[],choices:[]};
  const {compiled}=new WorkflowForge().compile({pack,resources,blueprint,context});
  const final=compiled.workflow.nodes.find(n=>n.id==='final'),producer=compiled.workflow.nodes.find(n=>n.origin?.semantic_key==='produce');
  const state={inputs:{repository:'repository location',request:'Create the README',mechanical_rows:[{private:'checker input'}]},nodes:{[producer.id]:{output:{handover:'Created and checked the requested README.'}}}};
  const result=resolveBindings(final.input_bindings,state);
  assert.deepEqual({...result},{upstream_result:state.nodes[producer.id].output});
  assert.deepEqual(final.input_bindings,{upstream_result:`/nodes/${producer.id}/output`});
  assert.equal(final.executor.mode,'orchestration');
  assert(!Object.hasOwn(final.input_bindings,'task'));
  assert(!Object.hasOwn(final.input_bindings,'mechanical_rows'));
  assert.doesNotMatch(final.prompt_template,/pinned source Skill|source\/SKILL\.md|source\/WORKFLOW\.md|\{\{task\}\}/);
  // Explicit semantic acceptance owns its inputs, regardless of their types.
  const selected=structuredClone(pack);
  const selectedFinal=selected.workflow.nodes.find(n=>n.id==='final');
  selectedFinal.prompt_template='Accept the result against the structured user requirements and reviewer decisions.';
  selectedFinal.executor={kind:'main',mode:'orchestration'};
  selectedFinal.input_bindings={requirements:'/inputs/requirements',decisions:'/inputs/decisions',result:'/nodes/instructions/output'};
  selected.workflow.inputs_schema.properties.requirements={type:'object',properties:{duration:{type:'number'}},required:['duration']};
  selected.workflow.inputs_schema.properties.decisions={type:'array',items:{type:'string'}};
  const explicit=new WorkflowForge().compile({pack:selected,resources,blueprint,context}).compiled.workflow.nodes.find(n=>n.id==='final');
  const structured={...state,inputs:{...state.inputs,requirements:{duration:90},decisions:['Use supplied audio']}};
  assert.deepEqual({...resolveBindings(explicit.input_bindings,structured)},{requirements:structured.inputs.requirements,decisions:structured.inputs.decisions,result:state.nodes[producer.id].output});
  assert.equal(explicit.prompt_template,selectedFinal.prompt_template);
});
test('Host evidence union preserves gaps, adjacent selections and different resources',()=>{
  const spans=[{resource:'source/A.md',start_line:7,end_line:12},{resource:'source/A.md',start_line:2,end_line:8},{resource:'source/A.md',start_line:4,end_line:5},{resource:'source/A.md',start_line:13,end_line:15},{resource:'source/A.md',start_line:20,end_line:22},{resource:'source/B.md',start_line:4,end_line:5}];
  const original=structuredClone(spans);
  assert.deepEqual(disjointSourceSpans(spans),[{resource:'source/A.md',start_line:2,end_line:12},{resource:'source/A.md',start_line:13,end_line:15},{resource:'source/A.md',start_line:20,end_line:22},{resource:'source/B.md',start_line:4,end_line:5}]);
  assert.deepEqual(spans,original);
});
test('Host evidence union rejects malformed nested ranges before normalization',()=>{
  const outer={resource:'source/A.md',start_line:1,end_line:20};
  for(const invalid of [{resource:'source/A.md',start_line:8,end_line:7},{resource:'source/A.md',start_line:2,end_line:'3'},{resource:'source/A.md',start_line:2.5,end_line:3},{resource:'source/A.md',start_line:2,end_line:3,unowned:'metadata'}])assert.throws(()=>disjointSourceSpans([outer,invalid]),{code:'EXPANSION_SOURCE_SPAN'});
});
for(const kind of ['skill','brief'])for(const ending of ['LF','CRLF'])test(`${kind} generation preserves source-authorized output filename selection with ${ending}`,()=>{
  const source='# Workflow\n\n## Procedure\n\nProduce a root `README.md`.\n\nModify only the root `README.md`, or another file\nthat the user explicitly names. Never edit production code.\n\nCreate `summary.json`.\n'.replaceAll('\n',ending==='CRLF'?'\r\n':'\n');
  const build=kind==='brief'?compileWorkflowBrief({workflow_id:'selected-output-brief',name:'Selected output',brief:source,provider_id:'worker'}):compileCoarseSkill({metadata:{name:'selected-output',description:'Selected output'},source_path:skillFixturePath,root:skillFixtureRoot,source_hash:'a'.repeat(64),instructions_start_line:1,files:{'source/SKILL.md':Buffer.from(source)},inventory:[],problems:[],metadata_files:{}},{id:'selected-output-skill',providerId:'worker'});
  const resources=build.resources,snapshot={workflow:build.workflow,resources:prepareResources(resources).manifest,provenance:build.provenance,import_report:build.import_report},pack={...snapshot,revision_hash:revisionHash(snapshot)},sections=sourceSectionInventory(resources),requirements=observedSourceRequirements(resources);
  const target=requirements.find(item=>item.requirement_kind==='artifact_path'&&item.details.artifact_path==='README.md');
  assert.equal(target.trigger,'runtime_resolved_artifact');
  assert.match(target.required_result,/user/);
  assert(target.source_spans.some(span=>span.start_line>target.source_spans[0].start_line),'The Host must preserve the source evidence authorizing a selected target');
  const fixed=requirements.find(item=>item.requirement_kind==='artifact_path'&&item.details.artifact_path==='summary.json');
  assert.equal(fixed.trigger,'produce_declared_artifact');
  const blueprint={contract:SEMANTIC_BLUEPRINT_CONTRACT,purpose:'Write the requested documentation and fixed summary.',source_dispositions:sections.map(section=>({section_id:section.section_id,disposition:'workflow',activity_keys:['write'],note:'Preserve target selection and fixed summary.'})),requirement_assignments:requirements.map(item=>({requirement_id:item.requirement_id,activity_keys:['write']})),runtime_dependencies:[],records:[],lists:[],enums:[],activities:[{key:'write',instructions:'Write README.md by default or the file the user explicitly names. Preserve the source scope and produce summary.json.',profile:'worker_write',source_sections:sections.map(section=>section.section_id),inputs:[{name:'request',from:'input:request'}],outputs:[{name:'handover',kind:'text',values:[],type_ref:''}],tool:''}],approvals:[],sequences:[],parallels:[],choices:[]};
  const {compiled}=new WorkflowForge().compile({pack,resources,blueprint,context});
  const worker=compiled.workflow.nodes.find(node=>node.origin?.semantic_key==='write');
  assert(!worker.required_artifacts?.some(item=>item.path==='README.md'));
  assert(worker.required_artifacts?.some(item=>item.path==='summary.json'));
});
function fixture(kind,brief='# Workflow\n\n## Procedure\n\nUse `node scripts/produce.mjs --file draft.txt`.\nWhen export is requested, use `node scripts/produce.mjs --stdin --export` with text on stdin.\n'){
  const build=kind==='brief'?compileWorkflowBrief({workflow_id:'fidelity-brief',name:'Fidelity',brief,provider_id:'worker'}):compileCoarseSkill({metadata:{name:'fidelity',description:'Fidelity'},source_path:skillFixturePath,root:skillFixtureRoot,source_hash:'a'.repeat(64),instructions_start_line:1,files:{'source/SKILL.md':Buffer.from(brief)},inventory:[],problems:[],metadata_files:{}},{id:'fidelity-skill',providerId:'worker'});
  const resources={...build.resources,'source/scripts/produce.mjs':Buffer.from("import {produce} from '../runtime/produce.mjs'; produce();"),'source/runtime/produce.mjs':Buffer.from("import {basename} from 'node:path'; export const produce=()=>basename('draft.txt');"),'source/benchmarks/answer.txt':Buffer.from('A benchmark answer must never be deployed.')};
  const snapshot={workflow:build.workflow,resources:prepareResources(resources).manifest,provenance:build.provenance,import_report:build.import_report};
  const pack={...snapshot,revision_hash:revisionHash(snapshot)},sections=sourceSectionInventory(resources);
  const calls=callableInventory(resources).callsites.filter(call=>call.classification==='exact_call'&&['required','conditional'].includes(call.authority));
  const ids=[...new Set([...observedSourceRequirements(resources).map(item=>item.requirement_id),...calls.map(call=>call.callsite_id)])];
  const blueprint={contract:SEMANTIC_BLUEPRINT_CONTRACT,purpose:'Preserve original production and conditional export.',source_dispositions:sections.map(section=>({section_id:section.section_id,disposition:'workflow',activity_keys:['produce'],note:'Original source operations.'})),requirement_assignments:ids.map(requirement_id=>({requirement_id,activity_keys:['produce']})),runtime_dependencies:[],records:[],lists:[],enums:[],activities:[{key:'produce',instructions:'Use the original production command and its conditional export variant with the source transport and repair budget.',profile:'worker_write',source_sections:sections.map(section=>section.section_id),inputs:[{name:'task',from:'input:task'}],outputs:[{name:'result',kind:'text',values:[],type_ref:''}],tool:''}],approvals:[],sequences:[],parallels:[],choices:[]};
  return {pack,resources,blueprint,calls};
}
function refresh(input,source){
  if(source!==undefined)input.resources['source/WORKFLOW.md']=Buffer.from(source);
  const snapshot={workflow:input.pack.workflow,provenance:input.pack.provenance,import_report:input.pack.import_report,resources:prepareResources(input.resources).manifest};
  input.pack={...snapshot,revision_hash:revisionHash(snapshot)};
  const sections=sourceSectionInventory(input.resources);
  input.calls=callableInventory(input.resources).callsites.filter(call=>call.actionable);
  input.blueprint.source_dispositions=sections.map(section=>({section_id:section.section_id,disposition:'workflow',activity_keys:['produce'],note:'Original source operations.'}));
  input.blueprint.activities[0].source_sections=sections.map(section=>section.section_id);
  input.blueprint.requirement_assignments=[...observedSourceRequirements(input.resources,{source_resource_policy:true}),...input.calls.map(call=>({requirement_id:call.callsite_id}))].map(item=>({requirement_id:item.requirement_id,activity_keys:['produce']}));
  return input;
}
function deployed(input){
  const {compiled,proposal}=new WorkflowForge().compile({...input,context});
  return {...compileDeployableConversion({workflow:compiled.workflow,proposal,resources:input.resources,pack:input.pack,proposalHash:compiled.proposal_hash,reviewContractVersion:15}),compiled,proposal};
}
for(const kind of ['skill','brief'])test(`${kind} Host evidence stays disjoint and idempotent after section and callable projection`,()=>{
  const input=fixture(kind),{proposal}=new WorkflowForge().compile({...input,context});
  for(const item of [...proposal.nodes,...proposal.edges]){
    assert(item.source_spans.some(span=>JSON.stringify(span)===JSON.stringify(item.source_span)));
    for(let i=0;i<item.source_spans.length;i++)for(let j=i+1;j<item.source_spans.length;j++){
      const a=item.source_spans[i],b=item.source_spans[j];
      assert(a.resource!==b.resource||a.start_line>b.end_line||b.start_line>a.end_line,`Host duplicated nested source evidence on ${item.id}`);
    }
  }
  for(const call of input.calls){
    const requirement=proposal.source_requirements.find(item=>item.requirement_id===call.callsite_id);
    assert.deepEqual(requirement.source_spans,[call.source_span],'Exact callable source locations stay in their authoritative requirements');
    assert(proposal.nodes.some(node=>node.source_spans.some(span=>span.resource===call.source_span.resource&&span.start_line<=call.source_span.start_line&&span.end_line>=call.source_span.end_line)));
  }
  assert.deepEqual(projectObservedRequirements(proposal,input.resources,{callable_inventory_policy:true}),proposal);
});
for(const kind of ['skill','brief'])test(`${kind} clarification compiles to current Main between ordinary workers`,()=>{
  const input=fixture(kind,'# Workflow\n\n## Procedure\n\nScan repository facts. Ask the user when audience ambiguity materially affects the result. Write `README.md` after resolving the audience.\n'),sections=sourceSectionInventory(input.resources).map(section=>section.section_id);
  const base={profile:'worker_read',source_sections:sections,tool:''};
  const blueprint={...input.blueprint,activities:[
    {...base,key:'scan',instructions:'Inspect repository facts and report new findings, including any material audience ambiguity.',inputs:[{name:'task',from:'input:task'}],outputs:[{name:'findings',kind:'text',values:[],type_ref:''}]},
    {...base,key:'clarify',profile:'orchestration_read',instructions:'Use the initiating conversation to resolve material audience ambiguity. Ask the user only when needed, receive the answer here, and establish the audience decision.',inputs:[{name:'task',from:'input:task'},{name:'findings',from:'scan.findings'}],outputs:[{name:'decision',kind:'text',values:[],type_ref:''}],outcome:'decision'},
    {...base,key:'produce',profile:'worker_write',instructions:'Write README.md using established findings and the resolved audience decision.',inputs:[{name:'task',from:'input:task'},{name:'findings',from:'scan.findings'},{name:'decision',from:'clarify.decision'}],outputs:[{name:'result',kind:'text',values:[],type_ref:''}],outcome:'artifact'},
  ],source_dispositions:input.blueprint.source_dispositions.map(item=>({...item,activity_keys:['scan','clarify','produce']}))};
  const {compiled}=new WorkflowForge().compile({...input,blueprint,context});
  const activity=key=>compiled.workflow.nodes.find(node=>node.origin?.semantic_key===key);
  assert.equal(activity('scan').executor.kind,'provider');
  assert.equal(activity('clarify').executor.kind,'main');
  assert.equal(activity('clarify').executor.mode,'orchestration');
  assert.equal(activity('produce').executor.kind,'provider');
  assert.equal(activity('produce').input_bindings.decision,`/nodes/${activity('clarify').id}/output/decision`);
});
for(const kind of ['skill','brief'])test(`${kind} generation preserves every direct call and transitive runtime without shipping answers`,()=>{
  const input=fixture(kind),{compiled,proposal}=new WorkflowForge().compile({...input,context});
  const worker=compiled.workflow.nodes.find(node=>node.origin?.semantic_key==='produce');
  assert.equal(worker.executor.kind,'provider');
  assert(worker.resources.includes('source/runtime/produce.mjs'),'transitive runtime must be usable by the original entrypoint');
  assert(!worker.resources.includes('source/benchmarks/answer.txt'));
  for(const call of input.calls){
    const requirement=proposal.source_requirements.find(item=>item.requirement_id===call.callsite_id);
    assert(requirement,'same-section coverage cannot replace individual call coverage');
    assert.equal(requirement.details.callable_id,call.callsite_id);
    assert.deepEqual(requirement.details.interface,call.interface);
    const mapping=proposal.requirement_mappings.find(item=>item.requirement_id===call.callsite_id);
    assert(mapping.node_ids.includes(worker.id));
  }
  assert.equal(compiled.validation_passes,1);
  const exported=compileDeployableConversion({workflow:compiled.workflow,proposal,resources:input.resources,pack:input.pack,proposalHash:compiled.proposal_hash,reviewContractVersion:15});
  assert(Buffer.from(exported.resources['workflow-assets/runtime/produce.mjs']).equals(input.resources['source/runtime/produce.mjs']));
  assert(!Object.keys(exported.resources).some(path=>/SKILL\.md|WORKFLOW\.md|benchmarks/.test(path)));
  const exportedWorker=exported.workflow.nodes.find(node=>node.id===worker.id);
  assert.match(exportedWorker.prompt_template,/--file/);
  assert.match(exportedWorker.prompt_template,/--stdin/);
  assert.match(exportedWorker.prompt_template,/--export/);
  assert.match(exportedWorker.prompt_template,/workflow-assets\/scripts\/produce\.mjs/);
  const interfaces=exported.workflow.import_status.requirement_coverage.filter(item=>item.details?.callable_id).map(item=>item.details.interface);
  assert.equal(interfaces.length,input.calls.length);
  assert(interfaces.every(item=>item.entrypoint==='workflow-assets/scripts/produce.mjs'&&item.argv[0]===item.entrypoint));
  assert.doesNotMatch(JSON.stringify(exported.workflow.import_status.requirement_coverage),/source\/scripts\/produce\.mjs/);
});

test('source-declared CLI aliases resolve to deployed program arguments without leaking private alias evidence',()=>{
  const input=fixture('brief');
  input.resources['source/WORKFLOW.md']=Buffer.from('# Workflow\n\n## Procedure\n\n下文的 `produce` 都指：\n```sh\nnode "${CLAUDE_SKILL_DIR}/scripts/produce.mjs"\n```\nUse `produce --stdin --export` with text on stdin.\n');
  const calls=callableInventory(input.resources).callsites.filter(call=>call.actionable);
  assert(calls.some(call=>call.interface.original_executable==='produce'),'the source alias must be recognized');
  const snapshot={workflow:input.pack.workflow,provenance:input.pack.provenance,import_report:input.pack.import_report,resources:prepareResources(input.resources).manifest};
  input.pack={...snapshot,revision_hash:revisionHash(snapshot)};
  const sections=sourceSectionInventory(input.resources);
  input.blueprint.source_dispositions=sections.map(section=>({section_id:section.section_id,disposition:'workflow',activity_keys:['produce'],note:'Original operations.'}));
  input.blueprint.activities[0].source_sections=sections.map(section=>section.section_id);
  input.blueprint.requirement_assignments=[...observedSourceRequirements(input.resources),...calls.map(call=>({requirement_id:call.callsite_id}))].map(item=>({requirement_id:item.requirement_id,activity_keys:['produce']}));
  const {compiled,proposal}=new WorkflowForge().compile({...input,context});
  assert(proposal.source_requirements.some(item=>item.details?.interface?.alias_declaration));
  const exported=compileDeployableConversion({workflow:compiled.workflow,proposal,resources:input.resources,pack:input.pack,proposalHash:compiled.proposal_hash,reviewContractVersion:15});
  const prompt=exported.workflow.nodes.find(node=>node.origin?.evidence_ids?.length&&node.executor?.kind==='provider').prompt_template;
  assert.doesNotMatch(prompt,/CLAUDE_SKILL_DIR|alias_declaration|resource_sha256/);
  const interfaces=exported.workflow.import_status.requirement_coverage.filter(item=>item.details?.callable_id).map(item=>item.details.interface);
  assert(interfaces.every(item=>item.entrypoint==='workflow-assets/scripts/produce.mjs'&&item.argv[0]===item.entrypoint));
  assert(interfaces.some(item=>item.argv.includes('--stdin')&&item.argv.includes('--export')));
});
test('unassigned original call variants are returned together before semantic review',()=>{
  const input=fixture('brief');
  input.blueprint.requirement_assignments=input.blueprint.requirement_assignments.filter(item=>!input.calls.some(call=>call.callsite_id===item.requirement_id));
  const {compiled}=new WorkflowForge().compile({...input,context});
  const missing=compiled.workflow.import_status.requirement_coverage.filter(item=>item.status==='unsupported');
  assert(input.calls.every(call=>missing.some(item=>item.requirement_id===call.callsite_id)));
  assert.equal(compiled.workflow.import_status.conversion_level,'unsupported');
});

test('a real runtime closure larger than 64 resources is preserved rather than rejected or truncated',()=>{
  const input=fixture('brief');
  input.resources['source/scripts/produce.mjs']=Buffer.from(Array.from({length:75},(_,index)=>`import '../runtime/module-${index}.mjs';`).join('\n'));
  for(let index=0;index<75;index++)input.resources[`source/runtime/module-${index}.mjs`]=Buffer.from(`export const value=${index};`);
  const snapshot={workflow:input.pack.workflow,provenance:input.pack.provenance,import_report:input.pack.import_report,resources:prepareResources(input.resources).manifest};
  input.pack={...snapshot,revision_hash:revisionHash(snapshot)};
  const {compiled,proposal}=new WorkflowForge().compile({...input,context});
  const worker=compiled.workflow.nodes.find(node=>node.origin?.semantic_key==='produce');
  assert.equal(worker.resources.filter(path=>/module-\d+\.mjs$/.test(path)).length,75);
  assert(proposal.source_requirements.filter(item=>item.details?.callable_id).every(item=>item.resource_refs.length===76));
  const exported=compileDeployableConversion({workflow:compiled.workflow,proposal,resources:input.resources,pack:input.pack,proposalHash:compiled.proposal_hash,reviewContractVersion:15});
  assert.equal(Object.keys(exported.resources).filter(path=>/module-\d+\.mjs$/.test(path)).length,75);
  assert.equal(exported.import_report.expansion.executor_options.main_worker.selection,'explicit_user_edit');
});

test('deployed direct scripts relocate the executable as well as argv and entrypoint',()=>{
  const input=refresh(fixture('brief'),'# Workflow\n\n## Procedure\n\nRun `scripts/produce.mjs --export`.\n');
  const result=deployed(input),interfaces=result.workflow.import_status.requirement_coverage.filter(item=>item.details?.callable_id).map(item=>item.details.interface);
  assert.equal(interfaces.length,1);
  assert.equal(interfaces[0].executable,'workflow-assets/scripts/produce.mjs');
  assert.equal(interfaces[0].entrypoint,interfaces[0].executable);
  assert.deepEqual(interfaces[0].argv,['--export']);
});

test('deployed MCP calls preserve distinct exact arguments without publishing source coordinates',()=>{
  const input=refresh(fixture('brief'),'# Workflow\n\n## Procedure\n\nCall `mcp__draw__render({"label":"a|b","size":2})`.\nCall `mcp__draw__render({"label":"c","size":4})`.\n');
  const result=deployed(input),interfaces=result.workflow.import_status.requirement_coverage.filter(item=>item.details?.callable_id).map(item=>item.details.interface);
  assert.equal(interfaces.length,2);
  assert.deepEqual(interfaces.map(item=>item.arguments),[{label:'a|b',size:2},{label:'c',size:4}]);
  assert(interfaces.every(item=>item.tool==='mcp__draw__render'&&item.arguments_transport==='literal_json'));
  const worker=result.compiled.workflow.nodes.find(item=>item.origin?.semantic_key==='produce');
  const prompt=result.workflow.nodes.find(item=>item.id===worker.id).prompt_template;
  assert.match(prompt,/mcp__draw__render/);
  assert.doesNotMatch(prompt,/arguments_source_span|arguments_source_location/);
});

test('deployed shell composites retain pipe stdin and guards with each relocated member',()=>{
  const input=refresh(fixture('brief'),'# Workflow\n\n## Procedure\n\nRun `node "${CLAUDE_SKILL_DIR}/scripts/produce.mjs" --file draft.txt | node "${CLAUDE_SKILL_DIR}/scripts/produce.mjs" --stdin && node "${CLAUDE_SKILL_DIR}/scripts/produce.mjs" --export`.\n');
  const result=deployed(input),coverage=result.workflow.import_status.requirement_coverage.filter(item=>item.details?.callable_id),interfaces=coverage.map(item=>item.details.interface);
  assert.equal(interfaces.length,3);
  assert(coverage.every(item=>item.status==='agent_assisted'));
  assert(interfaces.every(item=>item.entrypoint==='workflow-assets/scripts/produce.mjs'&&item.argv[0]===item.entrypoint));
  assert.deepEqual(interfaces.map(item=>item.composite_transport.connector_before),[null,'|','&&']);
  assert.equal(interfaces[1].stdin.kind,'pipeline');
  assert.equal(interfaces[1].stdin.source_callsite_id,coverage[0].requirement_id);
  assert.equal(interfaces[2].composite_transport.guards[0].preceding_callsite_id,coverage[1].requirement_id);
  assert(interfaces.every(item=>item.composite_transport.transport_status==='same_activity'));
  const worker=result.compiled.workflow.nodes.find(item=>item.origin?.semantic_key==='produce');
  const prompt=result.workflow.nodes.find(item=>item.id===worker.id).prompt_template;
  assert.doesNotMatch(prompt,/CLAUDE_SKILL_DIR|source_quote|source_location|resource_sha256|authoring_only/);
});

test('original composites cannot be covered by split owners or unrelated registered tools',()=>{
  const input=refresh(fixture('brief'),'# Workflow\n\n## Procedure\n\nRun `node scripts/produce.mjs | node scripts/produce.mjs --stdin`.\n');
  const {proposal}=new WorkflowForge().compile({...input,context});
  const requirements=proposal.source_requirements.filter(item=>item.details?.callable_id);
  const mappings=requirements.map((item,index)=>({requirement_id:item.requirement_id,node_ids:[`worker_${index}`],status:'agent_assisted'}));
  const nodes=mappings.map(item=>({id:item.node_ids[0],type:'agent'}));
  assert.equal(callableBindingIssues(requirements,mappings,nodes).size,2);
  const mixed=mappings.map(item=>({...item,node_ids:['together',...item.node_ids]}));
  assert.equal(callableBindingIssues(requirements,mixed,[...nodes,{id:'together',type:'agent'}]).size,2);
  const tools=[{id:'tool',type:'tool',tool:'unrelated'}];
  const together=mappings.map(item=>({...item,node_ids:['tool']}));
  assert.equal(callableBindingIssues(requirements,together,tools).size,2);
  const contracts=new Map([['unrelated',{implements:requirements.map(item=>item.requirement_id)}]]);
  assert.equal(callableBindingIssues(requirements,together,tools,contracts).size,0);
});

test('deployed heredoc preserves exact stdin body while keeping its source coordinates private',()=>{
  const input=refresh(fixture('brief'),"# Workflow\n\n## Procedure\n\nRun the original producer:\n```sh\nnode scripts/produce.mjs render - <<'END'\nhello\nEND\n```\n");
  const result=deployed(input),coverage=result.workflow.import_status.requirement_coverage.filter(item=>item.details?.callable_id);
  assert.equal(coverage.length,1);
  const original=result.proposal.source_requirements.find(item=>item.details?.callable_id).details.interface;
  assert(original.stdin.source_span,'original authoring evidence remains intact');
  assert.equal(coverage[0].details.interface.stdin.kind,'heredoc');
  assert.equal(coverage[0].details.interface.stdin.delimiter,'END');
  assert.equal(coverage[0].details.interface.stdin.body,'hello\n');
  assert.equal(coverage[0].details.interface.stdin.source_span,undefined);
  assert.equal(coverage[0].details.interface.stdin.source_location,undefined);
});

test('pinned full-proposal replays rederive Host interfaces and reject an omitted tool-only source',()=>{
  const input=refresh(fixture('brief'),'# Workflow\n\n## Procedure\n\nCall `mcp__draw__render({"label":"exact","size":2})`.\n');
  const provenance={source_revision:input.pack.revision_hash,routing_rules:routing,review_contract_version:15,generation_executor_policy:'provider-subagents/v1',callable_inventory_policy:'workflow-callable-inventory/v1'};
  const options={pack:input.pack,resources:input.resources,provenance,context:{providers}};
  const initial=validateGenerationProposal({proposal:input.blueprint},options),trace=initial.pipeline_trace;
  const persisted={proposal:structuredClone(initial.proposal),host_pipeline:{contract:trace.contract,proposal_hash:trace.proposal_hash,results:trace.results}};
  const replay=validateGenerationProposal(persisted,options);
  assert.equal(replay.pipeline_trace.proposal_hash,trace.proposal_hash);
  const poisoned=structuredClone(persisted);
  poisoned.proposal.source_requirements.find(item=>item.details?.callable_id).details.interface.arguments={label:'forged'};
  assert.equal(validateGenerationProposal(poisoned,options).pipeline_trace.proposal_hash,trace.proposal_hash);
  const omitted=structuredClone(initial.proposal);
  omitted.source_requirements=omitted.source_requirements.filter(item=>!item.requirement_id.startsWith('callable_'));
  omitted.requirement_mappings=omitted.requirement_mappings.filter(item=>!item.requirement_id.startsWith('callable_'));
  for(const node of omitted.nodes)node.requirement_ids=node.requirement_ids.filter(id=>!id.startsWith('callable_'));
  assert.throws(()=>validateGenerationProposal({proposal:omitted},options),error=>error.code==='GENERATION_DETERMINISTIC_AUDIT'&&error.findings.some(item=>item.requirement_id===input.calls[0].callsite_id));
  const historical={...options,provenance:{...provenance}};delete historical.provenance.callable_inventory_policy;
  assert.doesNotThrow(()=>validateGenerationProposal({proposal:omitted},historical));
});

test('pinned Host replay preserves real closures over the legacy 64-resource limit',()=>{
  const input=fixture('brief');
  input.resources['source/scripts/produce.mjs']=Buffer.from(Array.from({length:75},(_,index)=>`import '../runtime/module-${index}.mjs';`).join('\n'));
  for(let index=0;index<75;index++)input.resources[`source/runtime/module-${index}.mjs`]=Buffer.from(`export const value=${index};`);
  refresh(input);
  const provenance={source_revision:input.pack.revision_hash,routing_rules:routing,review_contract_version:15,generation_executor_policy:'provider-subagents/v1',callable_inventory_policy:'workflow-callable-inventory/v1'};
  const options={pack:input.pack,resources:input.resources,provenance,context:{providers}},initial=validateGenerationProposal({proposal:input.blueprint},options),trace=initial.pipeline_trace;
  const replay=validateGenerationProposal({proposal:initial.proposal,host_pipeline:{contract:trace.contract,proposal_hash:trace.proposal_hash,results:trace.results}},options);
  assert.equal(replay.pipeline_trace.proposal_hash,trace.proposal_hash);
  assert(replay.proposal.source_requirements.filter(item=>item.details?.callable_id).every(item=>item.resource_refs.length===76));
});

test('deployment excludes explicitly historical or forbidden answer references but retains required templates',()=>{
  for(const exclusion of ['Historical benchmark example `benchmarks/answer.txt` is not an execution input.','Do not read `benchmarks/answer.txt`.','Use `answer.txt`, historical benchmark `benchmarks/answer.txt` is not an execution input.','For example, benchmarks/answer.txt shows a historical answer; it is not an execution input.']){
    const input=fixture('brief');
    input.resources['source/answer.txt']=Buffer.from('Required template bytes.');
    refresh(input,`# Workflow\n\n## Procedure\n\nUse \`node scripts/produce.mjs --stdin\`.\n${exclusion}\nUse \`answer.txt\` as the required input template.\n`);
    const result=deployed(input);
    assert(!Object.hasOwn(result.resources,'workflow-assets/benchmarks/answer.txt'));
    assert.equal(result.resources['workflow-assets/answer.txt'].toString(),'Required template bytes.');
    const worker=result.compiled.workflow.nodes.find(item=>item.origin?.semantic_key==='produce');
    assert(!worker.resources.includes('source/benchmarks/answer.txt'));
    assert(worker.resources.includes('source/answer.txt'));
    assert(!result.proposal.source_requirements.some(item=>item.requirement_kind==='knowledge'&&item.resource_refs.includes('source/benchmarks/answer.txt')));
  }
});
