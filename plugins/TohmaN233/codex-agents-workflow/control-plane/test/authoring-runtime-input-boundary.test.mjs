import test from 'node:test';
import assert from 'node:assert/strict';
import * as authoring from '../lib/authoring/authoring-workflows.mjs';
import { authoringRunPack, GENERATED_PROPOSAL_ENVELOPE_SCHEMA_V21 } from '../lib/skill-import/expansion-run.mjs';
import { compileWorkflowBrief } from '../lib/skill-import/workflow-authoring.mjs';
import { CONVERSION_CONTRACT, PLANNER_CONVERSION_CONTRACT } from '../lib/skill-import/conversion-contract.mjs';
import { AUTHORING_ACTIVITY_INSTRUCTION_MAX_LENGTH, AUTHORING_NODE_PROMPT_MAX_LENGTH, SEMANTIC_BLUEPRINT_CONTRACT, SEMANTIC_BLUEPRINT_GUIDE, targetedSemanticRepairSchema } from '../lib/authoring/blueprint-contract.mjs';
import { WORKSPACE_SOURCE_LOCATION_RULES } from '../lib/workspace-source-locations.mjs';
import { canonicalJSON, prepareResources, revisionHash } from '../lib/workflow-revisions.mjs';

const providers=[
  {id:'planner',enabled:true,kind:'native_agent',capabilities:{read:true,write:true},config:{role:'implementer',model:'configured-planner',reasoning_effort:'medium'},description:'Suitable for difficult source conversion and semantic planning.'},
  {id:'reviewer',enabled:true,kind:'native_agent',capabilities:{read:true,write:false},config:{role:'reviewer',model:'configured-reviewer',reasoning_effort:'high'},description:'Suitable for independent critical review.'},
];
const routingRules={version:1,instructions:'Use configured authoring slots.',selection_mode:'automatic',routes:{implementation:{provider_id:'planner',role:'implementer'},complex_implementation:{provider_id:'planner',role:'implementer'},planning:{provider_id:'planner',role:'implementer'},review:{provider_id:'reviewer',role:'reviewer'}},generation:{planner_provider_id:'planner',review_provider_id:'reviewer',max_rounds:2}};

test('runtime reading and deterministic ownership are shared planner/reviewer obligations',()=>{
  assert.equal(PLANNER_CONVERSION_CONTRACT.version,15);
  assert.equal(CONVERSION_CONTRACT.version,15);
  const responsibilities=PLANNER_CONVERSION_CONTRACT.responsibilities.join('\n');
  assert.match(responsibilities,/source-provided runtime entrypoints and artifact references/);
  assert.match(responsibilities,/availability check before reading optional files/);
  assert.match(responsibilities,/mixed semantic activities consume its results/);
  assert.match(responsibilities,/Unchanged node-to-node transport records/);
  assert.match(responsibilities,/source-required quotations, citations and exact command examples/);
  assert.match(responsibilities,/Main worker and persistent task(?:\/thread)? (?:executors )?remain explicit user-edited options/);
  const check=id=>CONVERSION_CONTRACT.checks.find(item=>item.id===id).requirement;
  assert.match(check('data_handoffs'),/source-provided runtime entrypoints/);
  assert.match(check('data_handoffs'),/Unchanged node-to-node transport records/);
  assert.match(check('data_handoffs'),/Source-required quotations, citations and exact command examples/);
  assert.match(check('model_selection'),/configured existing enabled writable Provider/);
  assert.match(check('conditional_dependencies'),/optional local context and startup procedures/);
  assert.match(check('validation_strength'),/mixed semantic activities/);
  assert.match(responsibilities,/Tool interface qualification includes source aggregation/);
  assert.match(check('hard_rules'),/actual executor interface compatibility/);
  assert.match(check('hard_rules'),/explicit unresolved qualification findings/);
});

for(const sourceKind of ['skill','brief'])test(`${sourceKind} authoring packets carry one current runtime-input contract without changing Host interfaces`,()=>{
  const compiled=compileWorkflowBrief({workflow_id:`input-boundary-${sourceKind}`,name:'Input boundary fixture',brief:'# Workflow\n\nResolve the supplied source manifest and relevant code interfaces. If local context exists, read the relevant sections. A registered Host tool extracts and validates the selected rows. Return source decisions and an implementation plan.',provider_id:'planner'});
  const provenance={...compiled.provenance,kind:sourceKind==='skill'?'skill_import':'workflow_build',source_kind:sourceKind};
  const snapshot={workflow:compiled.workflow,resources:prepareResources(compiled.resources).manifest,provenance,import_report:compiled.import_report};
  const pack={...snapshot,revision_hash:revisionHash(snapshot)};
  const job=authoringRunPack(pack,compiled.resources,providers[0],`boundary-${sourceKind}`,routingRules,false,providers[1],providers);
  assert.equal(job.provenance.generation_executor_policy,'provider-subagents/v2');
  for(const path of ['analysis/request.txt','analysis/review-request.txt']){
    const packet=Buffer.from(job.resources[path]).toString('utf8');
    for(const provider of providers){assert.ok(packet.includes(provider.description));assert.ok(packet.includes(provider.config.model));}
    assert.match(packet,/worker_reasoning/);assert.match(packet,/Excluding default Main worker never excludes Main O/);
  }
  const definition=authoring.AUTHORING_WORKFLOWS.find(item=>item.source_kind===sourceKind);
  const planner=job.workflow.nodes.find(node=>node.id==='expand');
  assert.equal(definition.contract,'codex-authoring-workflow/v31');
  assert.equal(authoring.authoringDependencyAssessmentRequired(definition.contract),true);
  assert.equal(job.provenance.authoring_workflow_id,definition.id);
  assert.equal(planner.prompt_template,authoring.AUTHORING_PLANNER_PROMPT_CURRENT);
  assert.doesNotMatch(planner.prompt_template,/workspace-relative path/);
  assert.match(planner.prompt_template,/semantic responsibility, data and control relationships/);
  assert.match(planner.prompt_template,/bind existing inputs and tool results directly/);
  assert.doesNotMatch(planner.prompt_template,/fewest meaningful activities/);
  assert.notEqual(planner.prompt_template,authoring.AUTHORING_PLANNER_PROMPT_V19);
  assert.equal(job.workflow.nodes.find(node=>node.id==='final').prompt_template,authoring.AUTHORING_REVIEW_PROMPT_CURRENT);
  assert.match(job.workflow.nodes.find(node=>node.id==='final').prompt_template,/Return exactly one verdict per displayed checklist entry/);
  assert.match(job.workflow.nodes.find(node=>node.id==='final').prompt_template,/do not transcribe supplied IDs, paths, hashes/);
  const stored=authoring.createStoredAuthoringWorkflow(definition,{planner:providers[0],reviewer:providers[1],maxRounds:2});
  assert.deepEqual(stored.nodes.find(node=>node.id==='expand').outputs_schema,{});
  assert.equal(GENERATED_PROPOSAL_ENVELOPE_SCHEMA_V21.properties.proposal.properties.activities.items.properties.instructions.maxLength,AUTHORING_ACTIVITY_INSTRUCTION_MAX_LENGTH);
  assert.equal(targetedSemanticRepairSchema({contract:SEMANTIC_BLUEPRINT_CONTRACT,activities:[{key:'work'}]},{findings:[{semantic_keys:['work']}]}).properties.upsert.properties.activities.items.properties.instructions.maxLength,AUTHORING_ACTIVITY_INSTRUCTION_MAX_LENGTH);
  assert.equal(AUTHORING_NODE_PROMPT_MAX_LENGTH,12000);
  const contract=canonicalJSON(PLANNER_CONVERSION_CONTRACT);
  assert.equal(job.resources['analysis/request.txt'].split(contract).length-1,1);
  assert.match(job.resources['analysis/request.txt'],/workspace_source_locations/);
  assert.equal(SEMANTIC_BLUEPRINT_GUIDE.workspace_source_locations.split(WORKSPACE_SOURCE_LOCATION_RULES).length,2);
  assert.match(job.resources['analysis/request.txt'],/path may be relative to the exact Run workspace or an absolute path inside it/);
  assert.match(job.resources['analysis/request.txt'],/optional literal substring/);
  assert.deepEqual(planner.input_bindings,{});
  assert.deepEqual(job.workflow.inputs_schema.required,['task']);
  assert.deepEqual(Object.keys(job.workflow.inputs_schema.properties),['task']);
  assert.deepEqual(job.workflow.nodes.filter(node=>node.type==='tool').map(node=>({id:node.id,tool:node.executor.tool,input_bindings:node.input_bindings})),[
    {id:'graph_assembly',tool:'authoring-graph-assembly',input_bindings:{evidence:'/nodes/expand/output/host_pipeline/results/graph_assembly'}},
    {id:'execution_binding',tool:'authoring-execution-binding',input_bindings:{evidence:'/nodes/expand/output/host_pipeline/results/execution_binding',previous:'/nodes/graph_assembly/output'}},
    {id:'deterministic_validation',tool:'authoring-deterministic-validation',input_bindings:{evidence:'/nodes/expand/output/host_pipeline/results/deterministic_validation',previous:'/nodes/execution_binding/output'}},
  ]);
});
