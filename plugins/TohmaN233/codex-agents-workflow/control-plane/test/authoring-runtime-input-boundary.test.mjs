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
  {id:'planner',enabled:true,kind:'native_agent',capabilities:{read:true,write:true},config:{role:'implementer'}},
  {id:'reviewer',enabled:true,kind:'native_agent',capabilities:{read:true,write:false},config:{role:'reviewer'}},
];
const routingRules={version:1,instructions:'Use configured authoring slots.',selection_mode:'automatic',routes:{implementation:{provider_id:'planner',role:'implementer'},complex_implementation:{provider_id:'planner',role:'implementer'},planning:{provider_id:'planner',role:'implementer'},review:{provider_id:'reviewer',role:'reviewer'}},generation:{planner_provider_id:'planner',review_provider_id:'reviewer',max_rounds:2}};

test('runtime reading and deterministic ownership are shared planner/reviewer obligations',()=>{
  assert.equal(PLANNER_CONVERSION_CONTRACT.version,15);
  assert.equal(CONVERSION_CONTRACT.version,15);
  const responsibilities=PLANNER_CONVERSION_CONTRACT.responsibilities.join('\n');
  assert.match(responsibilities,/source-provided runtime entrypoints and artifact references/);
  assert.match(responsibilities,/availability check before reading optional files/);
  assert.match(responsibilities,/mixed semantic activities consume its results/);
  assert.match(responsibilities,/every unchanged input or resource value/);
  assert.match(responsibilities,/persistent task continuation only when the source requires one exact task identity/);
  const check=id=>CONVERSION_CONTRACT.checks.find(item=>item.id===id).requirement;
  assert.match(check('data_handoffs'),/source-provided runtime entrypoints/);
  assert.match(check('data_handoffs'),/Every unchanged supplied record/);
  assert.match(check('model_selection'),/one-off registered native Provider for ordinary worker activities/);
  assert.match(check('conditional_dependencies'),/optional local context and startup procedures/);
  assert.match(check('validation_strength'),/mixed semantic activities/);
});

for(const sourceKind of ['skill','brief'])test(`${sourceKind} authoring packets carry one current runtime-input contract without changing Host interfaces`,()=>{
  const compiled=compileWorkflowBrief({workflow_id:`input-boundary-${sourceKind}`,name:'Input boundary fixture',brief:'# Workflow\n\nResolve the supplied source manifest and relevant code interfaces. If local context exists, read the relevant sections. A registered Host tool extracts and validates the selected rows. Return source decisions and an implementation plan.',provider_id:'planner'});
  const provenance={...compiled.provenance,kind:sourceKind==='skill'?'skill_import':'workflow_build',source_kind:sourceKind};
  const snapshot={workflow:compiled.workflow,resources:prepareResources(compiled.resources).manifest,provenance,import_report:compiled.import_report};
  const pack={...snapshot,revision_hash:revisionHash(snapshot)};
  const job=authoringRunPack(pack,compiled.resources,providers[0],`boundary-${sourceKind}`,routingRules,false,providers[1],providers);
  const definition=authoring.AUTHORING_WORKFLOWS.find(item=>item.source_kind===sourceKind);
  const planner=job.workflow.nodes.find(node=>node.id==='expand');
  assert.equal(definition.contract,'codex-authoring-workflow/v30');
  assert.equal(authoring.authoringDependencyAssessmentRequired(definition.contract),true);
  assert.equal(job.provenance.authoring_workflow_id,definition.id);
  assert.equal(planner.prompt_template,authoring.AUTHORING_PLANNER_PROMPT_V27);
  assert.match(planner.prompt_template,/host_validation workspace_source_locations/);
  assert.match(planner.prompt_template,/shared workspace_source_locations contract in the packet/);
  assert.doesNotMatch(planner.prompt_template,/workspace-relative path/);
  assert.match(planner.prompt_template,/responsibility-handoff rule/);
  assert.match(planner.prompt_template,/every unchanged pre-existing input or resource value/);
  assert.doesNotMatch(planner.prompt_template,/fewest meaningful activities/);
  assert.notEqual(planner.prompt_template,authoring.AUTHORING_PLANNER_PROMPT_V19);
  assert.equal(job.workflow.nodes.find(node=>node.id==='final').prompt_template,authoring.AUTHORING_REVIEW_PROMPT_V22);
  assert.match(job.workflow.nodes.find(node=>node.id==='final').prompt_template,/Return exactly one verdict for every checklist entry/);
  assert.match(job.workflow.nodes.find(node=>node.id==='final').prompt_template,/Do not return, quote or reproduce checklist IDs, node or edge IDs/);
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
