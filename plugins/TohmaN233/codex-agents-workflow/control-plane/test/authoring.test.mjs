import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, rm } from 'node:fs/promises';
import { join, resolve } from 'node:path';
import { tmpdir } from './physical-tempdir.mjs';
import { compileWorkflowBrief } from '../lib/skill-import/workflow-authoring.mjs';
import { compileCoarseSkill } from '../lib/skill-import/coarse-compiler.mjs';
import { compileDeployableConversion } from '../lib/skill-import/conversion-deployment.mjs';
import { WorkflowForge, actionableSemanticError, lowerSemanticBlueprint } from '../lib/authoring/workflow-forge.mjs';
import { applySemanticRepair, canonicalizeSemanticRepair, collectSemanticBlueprintFindings, CURRENT_AUTHORING_SEMANTIC_BLUEPRINT_SCHEMA, INTERNAL_SEMANTIC_BLUEPRINT_SCHEMA, normalizeSemanticBlueprint, PREVIOUS_SEMANTIC_BLUEPRINT_CONTRACT as SEMANTIC_BLUEPRINT_CONTRACT, SEMANTIC_BLUEPRINT_CONTRACT as CURRENT_SEMANTIC_BLUEPRINT_CONTRACT, SEMANTIC_BLUEPRINT_SCHEMA, SEMANTIC_REPAIR_CONTRACT, SEMANTIC_REPAIR_SCHEMA, targetedSemanticRepairSchema, AUTHORING_ACTIVITY_INSTRUCTION_MAX_LENGTH, AUTHORING_NODE_PROMPT_MAX_LENGTH } from '../lib/authoring/blueprint-contract.mjs';
import { sourceSectionInventory } from '../lib/skill-import/source-dispositions.mjs';
import { authoringSourcePath } from '../lib/skill-import/authoring-source.mjs';
import { observedSourceRequirements, projectObservedRequirements } from '../lib/skill-import/source-requirements.mjs';
import { canonicalJSON, digest, prepareResources, revisionHash } from '../lib/workflow-revisions.mjs';
import { WorkflowStore } from '../lib/workflow-store.mjs';
import { exportWorkflowPackage, installWorkflowPackage, validateWorkflowPackage } from '../lib/workflow-package.mjs';
import { generationRetryClass, isGenerationContractFailure, MAX_PLANNER_ATTEMPTS } from '../lib/skill-import/generation-retry-policy.mjs';
import { AUTHORING_PLANNER_PROMPT, AUTHORING_PLANNER_PROMPT_V14, AUTHORING_PLANNER_PROMPT_V15, AUTHORING_PLANNER_PROMPT_V20, AUTHORING_PLANNER_PROMPT_V22, AUTHORING_PLANNER_PROMPT_V26, AUTHORING_PLANNER_PROMPT_V27, AUTHORING_REVIEW_PROMPT_V12, AUTHORING_REVIEW_PROMPT_V13, AUTHORING_REVIEW_PROMPT_V14, AUTHORING_REVIEW_PROMPT_V15, AUTHORING_REVIEW_PROMPT_V16, AUTHORING_REVIEW_PROMPT_V17, AUTHORING_REVIEW_PROMPT_V18, AUTHORING_REVIEW_PROMPT_V19, AUTHORING_REVIEW_PROMPT_V20, AUTHORING_REVIEW_PROMPT_V21, AUTHORING_REVIEW_PROMPT_V22, AUTHORING_WORKFLOWS, authoringWorkflowForPack, createStoredAuthoringWorkflow, ensureStoredAuthoringWorkflows } from '../lib/authoring/authoring-workflows.mjs';
import { AUTHORING_RUNTIME_ENVELOPE_SCHEMA, EXPANSION_PROPOSAL_SCHEMA, authoringRunPack, decodeGeneratedProposalDetailed } from '../lib/skill-import/expansion-run.mjs';
import { managedNativeResultSchema, strictAgentOutputSchema } from '../lib/execution/host-main-automation.mjs';
import { validateWorkflowShape } from '../lib/workflow-schema.mjs';
import { codexStructuredSchema } from '../lib/execution/codex-structured-output.mjs';
import { validateData } from '../lib/workflow-data-schema.mjs';
import { authoringPipelineTrace, deterministicProposalFindings, validateGenerationProposal } from '../lib/skill-import/proposal-validation.mjs';
import { evaluateExpression } from '../lib/workflow-bindings.mjs';
import { sourceContractIndex } from '../lib/skill-import/source-contracts.mjs';
import { resolvedSubagentPlan } from '../lib/workflow-runtime.mjs';
import { nativeAgentHandoff } from '../lib/execution/native-agent-bridge.mjs';

async function seedLegacyReady(store,workflow,options){
  store.validate=validateWorkflowShape;
  try{return await store.create(workflow,options);}finally{delete store.validate;}
}
import { WORKSPACE_SOURCE_LOCATIONS, WORKSPACE_SOURCE_LOCATIONS_SCHEMA } from '../lib/workspace-source-locations.mjs';

const rules={version:1,instructions:'Host routing.',selection_mode:'automatic',routes:{implementation:{provider_id:'native-luna',role:'implementer'},complex_implementation:{provider_id:'native-sol',role:'implementer'},review:{provider_id:'native-sol',role:'reviewer'},planning:{provider_id:'native-astra',role:'implementer'}},generation:{planner_provider_id:'native-astra',review_provider_id:'native-sol',max_rounds:2}};
const providers=[
  {id:'native-luna',enabled:true,kind:'native_agent',capabilities:{read:true,write:true},config:{role:'advisor'}},
  {id:'native-astra',enabled:true,kind:'native_agent',capabilities:{read:true,write:true},config:{role:'advisor'}},
  {id:'native-sol',enabled:true,kind:'native_agent',capabilities:{read:true,write:true},config:{role:'advisor'}},
];
const roles=[
  {id:'builtin-role-bounded-code-change',revision_hash:'1'.repeat(64),role:'implementer',access:'bounded_write',instructions:'Implement the bounded task.'},
  {id:'builtin-role-judgment-heavy-change',revision_hash:'2'.repeat(64),role:'implementer',access:'bounded_write',instructions:'Implement the complex bounded task.'},
  {id:'builtin-role-cross-review',revision_hash:'3'.repeat(64),role:'reviewer',access:'read_only',instructions:'Review independently.'},
  {id:'builtin-role-repository-analysis',revision_hash:'4'.repeat(64),role:'implementer',access:'read_only',instructions:'Analyze the repository.'},
  {id:'builtin-role-review-and-repair',revision_hash:'5'.repeat(64),role:'reviewer',access:'bounded_write',instructions:'Review and repair bounded defects.'},
];

function sourceFixture(){
  const compiled=compileWorkflowBrief({workflow_id:'brief-fixture',name:'Brief fixture',brief:'# Workflow\n\n## Process\n\nImplement the requested change.\n\n## Review Checklist\n\nReview the evidence before delivery.',provider_id:'native-luna'});
  const prepared=prepareResources(compiled.resources);
  const snapshot={workflow:compiled.workflow,resources:prepared.manifest,provenance:compiled.provenance,import_report:compiled.import_report};
  return {pack:{...snapshot,revision_hash:revisionHash(snapshot)},resources:compiled.resources};
}

function activity(key,instructions,sections,{kind='work',operation='read',ownership='main',complexity='routine',continues='',produces=[],consumes=[]}={}){
  return {key,purpose:key,kind,instructions,ownership,operation,complexity,source_sections:sections,continues,consumes:consumes.map(item=>item.from.input?{name:item.name,source_kind:'input',input:item.from.input,activity:'',output:''}:{name:item.name,source_kind:'activity',input:'',activity:item.from.activity,output:item.from.output}),produces:produces.map(item=>({name:item.name,shape:typeof item.shape==='string'?{kind:item.shape,values:[],type_ref:''}:{...item.shape,values:item.shape.values.map(String),type_ref:item.shape.type_ref??''}})),capability:{kind:'none',semantic_name:''}};
}

function dispositions(sections,keys){return sections.map(item=>({section_id:item.section_id,disposition:'workflow',activity_keys:keys,trigger:'',reason:'Required by the brief.'}));}
function blueprint(fields){return {contract:SEMANTIC_BLUEPRINT_CONTRACT,purpose:fields.purpose,source_dispositions:fields.source_dispositions,semantic_rules:[],requirement_assignments:[],data_types:fields.data_types??[],activities:fields.activities,approvals:[],sequences:fields.sequences??[],parallels:fields.parallels??[],choices:fields.choices??[],root:fields.root};}
const activityNode=(proposal,key)=>proposal.nodes.find(node=>node.name===key||node.semantic_key===key);

function dependencyBlueprint(line,dependency){
  const compiled=compileWorkflowBrief({workflow_id:'dependency-evidence-fixture',name:'Dependency evidence fixture',brief:`# Workflow\n\n## Process\n\n${line}`,provider_id:'native-luna'});
  const resources=compiled.resources,prepared=prepareResources(resources),snapshot={workflow:compiled.workflow,resources:prepared.manifest,provenance:compiled.provenance,import_report:compiled.import_report},pack={...snapshot,revision_hash:revisionHash(snapshot)};
  const sections=sourceSectionInventory(resources),section=sections.at(-1),plan={contract:CURRENT_SEMANTIC_BLUEPRINT_CONTRACT,purpose:'Complete the source task.',source_dispositions:sections.map(item=>({section_id:item.section_id,disposition:'workflow',activity_keys:['work'],note:'Required by the brief.'})),requirement_assignments:[],runtime_dependencies:[{key:'runtime_need',executable:dependency.executable,phase:dependency.phase??'unconditional',trigger:dependency.trigger??'',source_section:section.section_id,evidence:{resource:authoringSourcePath(resources),quote:dependency.quote??line},activity_keys:['work']}],records:[],lists:[],enums:[],activities:[{key:'work',instructions:'Complete the requested work.',profile:'main_write',source_sections:sections.map(item=>item.section_id),inputs:[],outputs:[],tool:''}],approvals:[],sequences:[],parallels:[],choices:[]};
  return {pack,resources,plan};
}

test('v21 requires an explicit dependency assessment while historical v6 remains readable',()=>{
  const {pack,resources,plan}=dependencyBlueprint('Complete the task.',{executable:{name:'helperctl'}});
  delete plan.runtime_dependencies;
  validateData(plan,SEMANTIC_BLUEPRINT_SCHEMA);
  assert.throws(()=>validateData(plan,CURRENT_AUTHORING_SEMANTIC_BLUEPRINT_SCHEMA));
  assert.throws(()=>validateGenerationProposal({proposal:plan},{pack,resources,provenance:{authoring_contract:'codex-authoring-workflow/v21',source_revision:pack.revision_hash},context:{routing_rules:rules,routing_catalog:providers,providers,roles}}),{code:'GENERATION_DEPENDENCY_ASSESSMENT'});
  assert.deepEqual(normalizeSemanticBlueprint(plan).runtime_dependencies,[]);
});

test('source-location handoff compiles one marked output and an explicit successor binding',()=>{
  const {pack,resources}=sourceFixture(),ids=sourceSectionInventory(resources).map(item=>item.section_id);
  const compact={contract:CURRENT_SEMANTIC_BLUEPRINT_CONTRACT,purpose:'Locate code, then implement from verified locations.',source_dispositions:ids.map(section_id=>({section_id,disposition:'workflow',activity_keys:['analyze','implement'],note:'Required.'})),requirement_assignments:[],runtime_dependencies:[],records:[],lists:[],enums:[],activities:[
    {key:'analyze',instructions:'Inspect relevant code and return bounded workspace source locations with usage.',profile:'main_read',source_sections:ids,inputs:[],outputs:[{name:'locations',kind:'list',values:[],type_ref:'',host_validation:WORKSPACE_SOURCE_LOCATIONS}],tool:''},
    {key:'implement',instructions:'Use the verified locations input to implement and test the change.',profile:'main_write',source_sections:ids,inputs:[{name:'locations',from:'analyze.locations'}],outputs:[{name:'result',kind:'text',values:[],type_ref:''}],tool:''},
  ],approvals:[],sequences:[],parallels:[],choices:[]};
  validateData(compact,CURRENT_AUTHORING_SEMANTIC_BLUEPRINT_SCHEMA);
  const normalized=normalizeSemanticBlueprint(compact);
  assert.equal(normalized.activities[0].produces[0].host_validation,WORKSPACE_SOURCE_LOCATIONS);
  const forged=new WorkflowForge().compile({pack,resources,blueprint:compact,context:{routing_rules:rules,routing_catalog:providers,providers,roles}});
  const producer=activityNode(forged.proposal,'analyze'),ready=forged.compiled.workflow.nodes.find(node=>node.origin?.semantic_key==='analyze');
  assert.deepEqual(producer.output_validators,{locations:WORKSPACE_SOURCE_LOCATIONS});
  assert.deepEqual(producer.outputs_schema.properties.locations,WORKSPACE_SOURCE_LOCATIONS_SCHEMA);
  assert.deepEqual(ready?.output_validators,{locations:WORKSPACE_SOURCE_LOCATIONS});
  assert.deepEqual(ready?.outputs_schema.properties.locations,WORKSPACE_SOURCE_LOCATIONS_SCHEMA);
  assert.equal(forged.compiled.validation.valid,true);
  assert.doesNotThrow(()=>validateWorkflowShape(forged.compiled.workflow));
  assert.deepEqual(strictAgentOutputSchema(ready.outputs_schema),ready.outputs_schema);
  assert.deepEqual(managedNativeResultSchema(ready),ready.outputs_schema);
  assert.deepEqual(codexStructuredSchema(ready.outputs_schema),ready.outputs_schema);
  assert.deepEqual(forged.compiled.workflow.nodes.find(node=>node.origin?.semantic_key==='implement')?.input_bindings?.locations,`/nodes/${producer.id}/output/locations`);
  const empty={source_dispositions:[],requirement_assignments:[],records:[],lists:[],enums:[],activities:[],approvals:[],sequences:[],parallels:[],choices:[]};
  const repaired=applySemanticRepair(compact,{contract:SEMANTIC_REPAIR_CONTRACT,purpose:'',upsert:{...empty,activities:[{...compact.activities[0],instructions:'Inspect the required code and return exact locations.'}]},remove:empty},{targets:[{semantic_keys:['analyze'],affected_semantic_fields:['activities.analyze.instructions']}]});
  assert.equal(repaired.activities[0].outputs[0].host_validation,WORKSPACE_SOURCE_LOCATIONS);
  const invalid=structuredClone(compact);invalid.activities[0].outputs[0].type_ref='custom_locations';
  assert.throws(()=>new WorkflowForge().compile({pack,resources,blueprint:invalid,context:{routing_rules:rules,routing_catalog:providers,providers,roles}}),error=>error.code==='AUTHORING_SEMANTIC'&&error.findings.some(item=>item.code==='workspace_source_locations_shape'));
  const unused=structuredClone(compact);unused.activities[1].inputs=[];
  assert.throws(()=>new WorkflowForge().compile({pack,resources,blueprint:unused,context:{routing_rules:rules,routing_catalog:providers,providers,roles}}),error=>error.code==='AUTHORING_SEMANTIC'&&error.findings.some(item=>item.code==='workspace_source_locations_handoff'));
});

test('long activity instructions survive planning, repair and lowering without truncation',()=>{
  const {pack,resources}=sourceFixture(),ids=sourceSectionInventory(resources).map(item=>item.section_id);
  const instructions='Inspect the source and implement the requested behavior.\n'+'Preserve this source-grounded detail. '.repeat(100)+'\nEND-OF-INSTRUCTIONS';
  assert(instructions.length>2000 && instructions.length<AUTHORING_ACTIVITY_INSTRUCTION_MAX_LENGTH);
  const plan={contract:CURRENT_SEMANTIC_BLUEPRINT_CONTRACT,purpose:'Implement the source task.',source_dispositions:ids.map(section_id=>({section_id,disposition:'workflow',activity_keys:['work'],note:'Required.'})),requirement_assignments:[],runtime_dependencies:[],records:[],lists:[],enums:[],activities:[{key:'work',instructions,profile:'main_write',source_sections:ids,inputs:[],outputs:[{name:'result',kind:'text',values:[],type_ref:''}],tool:''}],approvals:[],sequences:[],parallels:[],choices:[]};
  validateData(plan,CURRENT_AUTHORING_SEMANTIC_BLUEPRINT_SCHEMA);
  assert.equal(normalizeSemanticBlueprint(plan).activities[0].instructions,instructions);
  const forged=new WorkflowForge().compile({pack,resources,blueprint:plan,context:{routing_rules:rules,routing_catalog:providers,providers,roles}});
  assert.equal(activityNode(forged.proposal,'work').prompt_template,instructions);
  const empty={source_dispositions:[],requirement_assignments:[],runtime_dependencies:[],records:[],lists:[],enums:[],activities:[],approvals:[],sequences:[],parallels:[],choices:[]};
  const revised=instructions+'\nREPAIR-PRESERVED';
  const repair={contract:SEMANTIC_REPAIR_CONTRACT,purpose:'',upsert:{...empty,activities:[{...plan.activities[0],instructions:revised}]},remove:empty};
  validateData(repair,SEMANTIC_REPAIR_SCHEMA);
  validateData(repair,targetedSemanticRepairSchema(plan,{findings:[{semantic_keys:['work']}]}));
  const applied=applySemanticRepair(plan,repair,{targets:[{semantic_keys:['work'],affected_semantic_fields:['activities.work.instructions']} ]});
  assert.equal(applied.activities[0].instructions,revised);
  assert.equal(activityNode(new WorkflowForge().compile({pack,resources,blueprint:applied,context:{routing_rules:rules,routing_catalog:providers,providers,roles}}).proposal,'work').prompt_template,revised);
  const oversized={...plan,activities:[{...plan.activities[0],instructions:'X'.repeat(AUTHORING_ACTIVITY_INSTRUCTION_MAX_LENGTH+1)}]};
  assert.throws(()=>validateData(oversized,CURRENT_AUTHORING_SEMANTIC_BLUEPRINT_SCHEMA));
  assert.throws(()=>validateData({...repair,upsert:{...empty,activities:oversized.activities}},SEMANTIC_REPAIR_SCHEMA));
  const appendixOverflow={...plan,activities:[{...plan.activities[0],instructions:'X'.repeat(AUTHORING_ACTIVITY_INSTRUCTION_MAX_LENGTH),repeat_until:{condition:'Y'.repeat(2000),max_attempts:2}}]};
  validateData(appendixOverflow,CURRENT_AUTHORING_SEMANTIC_BLUEPRINT_SCHEMA);
  assert.throws(()=>new WorkflowForge().compile({pack,resources,blueprint:appendixOverflow,context:{routing_rules:rules,routing_catalog:providers,providers,roles}}),error=>error.code==='AUTHORING_PROMPT_LIMIT'&&error.prompt_chars>AUTHORING_NODE_PROMPT_MAX_LENGTH);
});

test('authoring rejects unchecked Agent transcription of artifact identity fields',()=>{
  const {pack,resources}=sourceFixture(),ids=sourceSectionInventory(resources).map(item=>item.section_id);
  const compact={contract:CURRENT_SEMANTIC_BLUEPRINT_CONTRACT,purpose:'Implement and independently verify the artifact.',source_dispositions:ids.map(section_id=>({section_id,disposition:'workflow',activity_keys:['implement','verify'],note:'Both responsibilities apply.'})),requirement_assignments:[],runtime_dependencies:[],records:[{key:'artifact_ref',fields:[{name:'path',type:'string',required:true},{name:'sha256',type:'string',required:true},{name:'item_index',type:'integer',required:true}],open:false}],lists:[],enums:[],activities:[
    {key:'implement',instructions:'Implement the requested change and return a concise semantic summary.',profile:'main_write',source_sections:ids,inputs:[],outputs:[{name:'artifact',kind:'object',values:[],type_ref:'artifact_ref'}],tool:''},
    {key:'verify',instructions:'Inspect the referenced artifact and its evidence against the source review checklist.',profile:'review',source_sections:ids,inputs:[{name:'artifact',from:'implement.artifact'}],outputs:[{name:'passed',kind:'boolean',values:[],type_ref:''}],tool:'',outcome:'review',fail_on_false:['passed']},
  ],approvals:[],sequences:[],parallels:[],choices:[]};
  assert.throws(()=>new WorkflowForge().compile({pack,resources,blueprint:compact,context:{routing_rules:rules,routing_catalog:providers,providers,roles}}),error=>{
    const finding=error.findings?.find(item=>item.code==='agent_deterministic_transcription');
    assert.equal(error.code,'AUTHORING_SEMANTIC');
    assert(finding);
    assert.match(finding.message,/artifact\.path/);
    assert.match(finding.message,/artifact\.sha256/);
    assert.match(finding.message,/artifact\.item_index/);
    assert(finding.affected_semantic_fields.includes('activities.implement.outputs.artifact'));
    return true;
  });
});

test('authoring rejects identity transcription hidden inside free-text evidence instructions',()=>{
  const {pack,resources}=sourceFixture(),ids=sourceSectionInventory(resources).map(item=>item.section_id);
  const plan={contract:CURRENT_SEMANTIC_BLUEPRINT_CONTRACT,purpose:'Validate items without copying their identities.',source_dispositions:ids.map(section_id=>({section_id,disposition:'workflow',activity_keys:['validate'],note:'Validation applies.'})),requirement_assignments:[],runtime_dependencies:[],records:[],lists:[],enums:[],activities:[
    {key:'validate',instructions:'Inspect the supplied items. Return concise validation evidence with exact item IDs and artifact paths.',profile:'review',source_sections:ids,inputs:[],outputs:[{name:'validation_evidence',kind:'text',values:[],type_ref:''}],tool:'',outcome:'review'},
  ],approvals:[],sequences:[],parallels:[],choices:[]};
  assert.throws(()=>new WorkflowForge().compile({pack,resources,blueprint:plan,context:{routing_rules:rules,routing_catalog:providers,providers,roles}}),error=>{
    const finding=error.findings?.find(item=>item.code==='agent_deterministic_transcription');
    assert.equal(error.code,'AUTHORING_SEMANTIC');
    assert(finding?.affected_semantic_fields.includes('activities.validate.instructions'));
    return true;
  });
  plan.activities[0].instructions='Inspect the supplied items and return semantic findings in input order. Do not return IDs, paths or hashes.';
  assert.doesNotThrow(()=>new WorkflowForge().compile({pack,resources,blueprint:plan,context:{routing_rules:rules,routing_catalog:providers,providers,roles}}));
});

test('authoring rejects generic Agent copy-through even when fields are not identity-shaped',()=>{
  const {pack,resources}=sourceFixture(),ids=sourceSectionInventory(resources).map(item=>item.section_id);
  const base={contract:CURRENT_SEMANTIC_BLUEPRINT_CONTRACT,purpose:'Analyze supplied content without Agent transcription.',source_dispositions:ids.map(section_id=>({section_id,disposition:'workflow',activity_keys:['source','analyze'],note:'Both responsibilities apply.'})),requirement_assignments:[],runtime_dependencies:[],records:[{key:'content_record',fields:[{name:'title',type:'string',required:true},{name:'category',type:'string',required:true},{name:'body',type:'string',required:true}],open:false}],lists:[],enums:[],activities:[
    {key:'source',instructions:'Create the requested semantic content record.',profile:'main_write',source_sections:ids,inputs:[],outputs:[{name:'record',kind:'object',values:[],type_ref:'content_record'}],tool:''},
    {key:'analyze',instructions:'Analyze the supplied record and return a new concise assessment.',profile:'review',source_sections:ids,inputs:[{name:'record',from:'source.record'}],outputs:[{name:'assessment',kind:'text',values:[],type_ref:''}],tool:'',outcome:'review'},
  ],approvals:[],sequences:[],parallels:[],choices:[]};
  const copiedInstruction=structuredClone(base);
  copiedInstruction.activities[1].instructions='Copy the supplied title, category and body into the output record.';
  assert.throws(()=>new WorkflowForge().compile({pack,resources,blueprint:copiedInstruction,context:{routing_rules:rules,routing_catalog:providers,providers,roles}}),error=>
    error.code==='AUTHORING_SEMANTIC'&&error.findings.some(item=>item.code==='agent_deterministic_transcription'&&item.affected_semantic_fields.includes('activities.analyze.instructions')));
  for(const instructions of [
    'Return the supplied label and name in the output.',
    'Preserve the provided category in the result.',
    'Set the output category from the input record.',
    '输出输入记录提供的名称和标签。',
    '保留输入记录中的类别并写入结果。',
    '将输入记录的类别写入输出字段。',
  ]){
    const renamedCopy=structuredClone(base);renamedCopy.activities[1].instructions=instructions;
    assert.throws(()=>new WorkflowForge().compile({pack,resources,blueprint:renamedCopy,context:{routing_rules:rules,routing_catalog:providers,providers,roles}}),error=>
      error.code==='AUTHORING_SEMANTIC'&&error.findings.some(item=>item.code==='agent_deterministic_transcription'));
  }
  assert.doesNotThrow(()=>new WorkflowForge().compile({pack,resources,blueprint:base,context:{routing_rules:rules,routing_catalog:providers,providers,roles}}));
});

test('runtime dependency evidence rejects partial names, module case and unrelated version digits',()=>{
  const cases=[
    ['Render digital output.',{executable:{name:'git'}},'evidence.quote'],
    ['Use python with foobar.',{executable:{name:'python',python_modules:['foo']}},'executable.python_modules'],
    ['Use python with YAML.',{executable:{name:'python',python_modules:['yaml']}},'executable.python_modules'],
    ['Run mediactl 2.4.',{executable:{name:'mediactl',version:'>=4'}},'executable.version'],
    ['Run mediactl.',{executable:{name:'C:\\Tools\\mediactl.exe'}},'executable'],
  ];
  for(const [line,dependency,field] of cases){
    const fixture=dependencyBlueprint(line,dependency);
    assert.throws(()=>new WorkflowForge().compile({pack:fixture.pack,resources:fixture.resources,blueprint:fixture.plan,context:{routing_rules:rules,routing_catalog:providers,providers,roles}}),error=>error.code==='AUTHORING_SEMANTIC'&&error.findings.some(item=>item.affected_semantic_fields.includes(`runtime_dependencies.runtime_need.${field}`)),line);
  }
});

test('runtime dependency evidence accepts exact names and versions before prose punctuation',()=>{
  for(const [line,executable] of [
    ['Use git.',{name:'git'}],
    ['Run mediactl >=2.4.',{name:'mediactl',version:'>=2.4'}],
    ['Use python with yaml.',{name:'python',python_modules:['yaml']}],
  ]){
    const {pack,resources,plan}=dependencyBlueprint(line,{executable});
    const forged=new WorkflowForge().compile({pack,resources,blueprint:plan,context:{routing_rules:rules,routing_catalog:providers,providers,roles}});
    assert.equal(forged.compiled.workflow.requirements.executables.length,1,line);
  }
});

test('dependency source diagnostics distinguish the numbered request from the pinned source path and exact quote',()=>{
  const source=['# Workflow','','## Inspection','','Use codegraph to inspect the project.','','## Process','','Run python to validate the result.','Run node to package the result.','Use git to review the changes.'].join('\n');
  const compiled=compileWorkflowBrief({workflow_id:'dependency-source-fixture',name:'Dependency source fixture',brief:source,provider_id:'native-luna'});
  const workflow=structuredClone(compiled.workflow);
  for(const node of workflow.nodes){
    if(Array.isArray(node.resources))node.resources=node.resources.map(path=>path==='source/WORKFLOW.md'?'source/SKILL.md':path);
    if(node.origin?.source_span?.resource==='source/WORKFLOW.md')node.origin.source_span.resource='source/SKILL.md';
    if(typeof node.prompt_template==='string')node.prompt_template=node.prompt_template.replaceAll('source/WORKFLOW.md','source/SKILL.md');
  }
  const resources={'source/SKILL.md':compiled.resources['source/WORKFLOW.md']},prepared=prepareResources(resources);
  const snapshot={workflow,resources:prepared.manifest,provenance:compiled.provenance,import_report:compiled.import_report};
  const pack={...snapshot,revision_hash:revisionHash(snapshot)};
  const sections=sourceSectionInventory(resources);
  const entries=[
    ['codegraph','Use codegraph to inspect the project.',sections[0]],
    ['python','Run python to validate the result.',sections[1]],
    ['node','Run node to package the result.',sections[1]],
    ['git','Use git to review the changes.',sections[1]],
  ];
  const plan={contract:CURRENT_SEMANTIC_BLUEPRINT_CONTRACT,purpose:'Execute the source task.',source_dispositions:sections.map(section=>({section_id:section.section_id,disposition:'workflow',activity_keys:['work'],note:'Required by the source.'})),requirement_assignments:[],runtime_dependencies:entries.map(([name,quote,section])=>({key:name,executable:{name},phase:'unconditional',trigger:'',source_section:section.section_id,evidence:{resource:'analysis/request.txt',quote:`${source.split('\n').indexOf(quote)+1}: ${quote}`},activity_keys:['work']})),records:[],lists:[],enums:[],activities:[{key:'work',instructions:'Execute and validate the source task.',profile:'main_write',source_sections:sections.map(section=>section.section_id),inputs:[],outputs:[],tool:''}],approvals:[],sequences:[],parallels:[],choices:[]};
  const forge=()=>new WorkflowForge().compile({pack,resources,blueprint:plan,context:{routing_rules:rules,routing_catalog:providers,providers,roles}});
  const checkFindings=expectedFields=>assert.throws(forge,error=>{
    assert.equal(error.code,'AUTHORING_SEMANTIC');
    assert.equal(error.findings.length,expectedFields.length*entries.length);
    for(const [name,,section] of entries){
      for(const field of expectedFields){
        const finding=error.findings.find(item=>item.affected_semantic_fields.includes(`runtime_dependencies.${name}.${field}`));
        assert(finding,`${name}.${field}`);
        assert.deepEqual(finding.source_refs,[section.source_span]);
        assert.match(finding.message,/source\/SKILL\.md lines \d+-\d+/);
      }
    }
    return true;
  });
  checkFindings(['evidence.resource','evidence.quote']);
  for(const dependency of plan.runtime_dependencies)dependency.evidence.resource=dependency.source_section;
  checkFindings(['evidence.resource','evidence.quote']);
  for(const dependency of plan.runtime_dependencies)dependency.evidence.resource='source/SKILL.md';
  checkFindings(['evidence.quote']);
  for(const [index,dependency] of plan.runtime_dependencies.entries())dependency.evidence.quote=entries[index][1];
  const forged=forge();
  assert.deepEqual(forged.compiled.workflow.requirements.executables,['codegraph','git','node','python']);
});

test('execution instructions reject authoring-only resources before graph compilation without rejecting supporting paths',()=>{
  const {pack,resources,plan}=dependencyBlueprint('Use helperctl for the task.',{executable:{name:'helperctl'}});
  const section=sourceSectionInventory(resources).at(-1);
  for(const reference of ['analysis/request.txt','analysis/review-request.txt','__authoring__/planner.json','source/SKILL.md','source/WORKFLOW.md']){
    plan.activities[0].instructions=`Read ${reference} and complete the task.`;
    assert.throws(()=>new WorkflowForge().compile({pack,resources,blueprint:plan,context:{routing_rules:rules,routing_catalog:providers,providers,roles}}),error=>{
      const finding=error.findings?.find(item=>item.code==='authoring_only_execution_reference');
      assert.equal(error.code,'AUTHORING_SEMANTIC');
      assert(finding,reference);
      assert.deepEqual(finding.affected_semantic_fields,['activities.work.instructions']);
      assert.deepEqual(finding.source_refs,[section.source_span]);
      assert.match(finding.message,new RegExp(reference.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')));
      return true;
    },reference);
  }
  for(const reference of ['source/scripts/check.py','workspace/analysis/request.txt','analysis/report.json']){
    plan.activities[0].instructions=`Read ${reference} and complete the task.`;
    assert.equal(new WorkflowForge().compile({pack,resources,blueprint:plan,context:{routing_rules:rules,routing_catalog:providers,providers,roles}}).compiled.validation.valid,true,reference);
  }
  plan.activities[0].instructions='Complete the task using the pinned source meaning.';
  plan.approvals=[{key:'review_gate',question:'Review analysis/review-request.txt before approval.',source_sections:[section.section_id],subject:'work.result',before:['work']}];
  const finding=collectSemanticBlueprintFindings(plan,{sectionInventory:sourceSectionInventory(resources)}).find(item=>item.code==='authoring_only_execution_reference');
  assert(finding);
  assert.deepEqual(finding.affected_semantic_fields,['approvals.review_gate.question']);
  assert.deepEqual(finding.source_refs,[section.source_span]);
});

test('explicit Host preparation absorbs only its cited install approval and retains task approvals',()=>{
  const preparation='Use mediactl. If mediactl is missing, ask user approval to install mediactl before running it.';
  const {pack,resources,plan}=dependencyBlueprint(preparation,{executable:{name:'mediactl'}});
  const installApproval=observedSourceRequirements(resources).find(item=>item.requirement_kind==='approval');
  assert(installApproval);
  plan.runtime_dependencies[0].host_preparation_observation_ids=[installApproval.requirement_id];
  const forged=new WorkflowForge().compile({pack,resources,blueprint:plan,context:{routing_rules:rules,routing_catalog:providers,providers,roles}});
  assert.deepEqual(forged.compiled.workflow.requirements.executables,['mediactl']);
  assert(!forged.proposal.source_requirements.some(item=>item.requirement_id===installApproval.requirement_id));
  const mapped=forged.proposal.source_requirements.find(item=>item.requirement_id==='authoring_dependency_runtime_need');
  assert.deepEqual(mapped.details.host_preparation_observation_ids,[installApproval.requirement_id]);
  assert(forged.proposal.source_dispositions.some(item=>item.requirement_ids.includes(mapped.requirement_id)));

  const separate=`${preparation}\nObtain user approval before publishing the result.`;
  const second=dependencyBlueprint(separate,{executable:{name:'mediactl'},quote:preparation});
  const approvals=observedSourceRequirements(second.resources).filter(item=>item.requirement_kind==='approval');
  assert.equal(approvals.length,2);
  second.plan.runtime_dependencies[0].host_preparation_observation_ids=[approvals[0].requirement_id];
  const lowered=lowerSemanticBlueprint(second.pack,second.resources,second.plan,{routing_rules:rules,routing_catalog:providers,providers,roles});
  const projected=projectObservedRequirements(lowered,second.resources);
  assert(!projected.source_requirements.some(item=>item.requirement_id===approvals[0].requirement_id));
  assert(projected.source_requirements.some(item=>item.requirement_id===approvals[1].requirement_id));

  const mixed=dependencyBlueprint(`${preparation} Obtain user approval before publishing the result.`,{executable:{name:'mediactl'}});
  const mixedApproval=observedSourceRequirements(mixed.resources).find(item=>item.requirement_kind==='approval');
  mixed.plan.runtime_dependencies[0].host_preparation_observation_ids=[mixedApproval.requirement_id];
  assert.throws(()=>new WorkflowForge().compile({pack:mixed.pack,resources:mixed.resources,blueprint:mixed.plan,context:{routing_rules:rules,routing_catalog:providers,providers,roles}}),error=>error.code==='AUTHORING_SEMANTIC'&&error.findings.some(item=>item.affected_semantic_fields.includes('runtime_dependencies.runtime_need.host_preparation_observation_ids')));
});

test('Host preparation never absorbs a task approval merely because its line mentions the dependency',()=>{
  const install='If Python is missing, ask for approval to install Python.';
  const prepared=dependencyBlueprint(install,{executable:{name:'python'}});
  const installApproval=observedSourceRequirements(prepared.resources).find(item=>item.requirement_kind==='approval');
  assert(installApproval);
  prepared.plan.runtime_dependencies[0].host_preparation_observation_ids=[installApproval.requirement_id];
  const compiled=new WorkflowForge().compile({pack:prepared.pack,resources:prepared.resources,blueprint:prepared.plan,context:{routing_rules:rules,routing_catalog:providers,providers,roles}});
  assert(!compiled.proposal.source_requirements.some(item=>item.requirement_id===installApproval.requirement_id));
  for(const line of [
    'Use Python to locate the release draft and obtain approval before publishing.',
    'If Python is missing, ask for approval to install Python and publish the result.',
  ]){
    const fixture=dependencyBlueprint(line,{executable:{name:'python'}});
    const taskApproval=observedSourceRequirements(fixture.resources).find(item=>item.requirement_kind==='approval');
    assert(taskApproval,line);
    fixture.plan.runtime_dependencies[0].host_preparation_observation_ids=[taskApproval.requirement_id];
    assert.throws(()=>new WorkflowForge().compile({pack:fixture.pack,resources:fixture.resources,blueprint:fixture.plan,context:{routing_rules:rules,routing_catalog:providers,providers,roles}}),error=>error.code==='AUTHORING_SEMANTIC'&&error.findings.some(item=>item.affected_semantic_fields.includes('runtime_dependencies.runtime_need.host_preparation_observation_ids')),line);
  }
});

test('Host preparation absorbs a location input only when the requested object is the executable environment',()=>{
  for(const [line,accepted] of [
    ['Ask the user for input to locate Python path.',true],
    ['Ask the user for input to locate the release draft with Python.',false],
  ]){
    const fixture=dependencyBlueprint(line,{executable:{name:'python'}});
    const input=observedSourceRequirements(fixture.resources).find(item=>item.requirement_kind==='user_input');
    assert(input,line);
    fixture.plan.runtime_dependencies[0].host_preparation_observation_ids=[input.requirement_id];
    const compile=()=>new WorkflowForge().compile({pack:fixture.pack,resources:fixture.resources,blueprint:fixture.plan,context:{routing_rules:rules,routing_catalog:providers,providers,roles}});
    if(accepted){
      const forged=compile();
      assert(!forged.proposal.source_requirements.some(item=>item.requirement_id===input.requirement_id));
    }else assert.throws(compile,error=>error.code==='AUTHORING_SEMANTIC'&&error.findings.some(item=>item.affected_semantic_fields.includes('runtime_dependencies.runtime_need.host_preparation_observation_ids')),line);
  }
});

test('an artifact-only decision refines the same coarse observed dependency without gating startup',()=>{
  const line='Generate a Python script; it requires python with yaml when that generated script runs later.';
  const {pack,resources,plan}=dependencyBlueprint(line,{executable:{name:'python',python_modules:['yaml']},phase:'artifact_only',trigger:'when the generated script runs later'});
  assert(observedSourceRequirements(resources).some(item=>item.requirement_kind==='dependency'&&item.details.executable==='python'));
  const forged=new WorkflowForge().compile({pack,resources,blueprint:plan,context:{routing_rules:rules,routing_catalog:providers,providers,roles}});
  assert.deepEqual(forged.compiled.workflow.requirements.executables,[]);
  assert(forged.proposal.source_requirements.some(item=>item.requirement_id==='authoring_dependency_runtime_need'&&item.details.phase==='artifact_only'));
  assert(!forged.proposal.source_requirements.some(item=>item.requirement_id.startsWith('observed_dependency_')&&item.details.executable==='python'));
});

test('targeted semantic repair cannot ask the planner to rewrite the Workflow purpose',()=>{
  assert.equal(SEMANTIC_REPAIR_SCHEMA.properties.purpose.const,'');
  const empty={source_dispositions:[],requirement_assignments:[],records:[],lists:[],enums:[],activities:[],approvals:[],sequences:[],parallels:[],choices:[]};
  const patch={contract:SEMANTIC_REPAIR_CONTRACT,purpose:'A rewritten purpose',upsert:empty,remove:empty};
  assert.throws(()=>validateData(patch,SEMANTIC_REPAIR_SCHEMA));
  const canonical=canonicalizeSemanticRepair(patch);
  assert.equal(canonical.purpose,'');
  assert.deepEqual(canonical.upsert,patch.upsert);
  validateData(canonical,SEMANTIC_REPAIR_SCHEMA);
});

test('repair output schema is sized to the pinned plan and findings, not the global whole-library maxima',()=>{
  const plan={contract:CURRENT_SEMANTIC_BLUEPRINT_CONTRACT,activities:[{key:'analyze'},{key:'implement'},{key:'review'}],requirement_assignments:[{requirement_id:'r1'}],source_dispositions:[],records:[],lists:[],enums:[],approvals:[],sequences:[],parallels:[],choices:[]};
  const feedback={findings:[{semantic_keys:['implement'],affected_semantic_fields:['activities.implement.inputs']} ]};
  const schema=targetedSemanticRepairSchema(plan,feedback);
  const changes=schema.properties.upsert.properties;
  assert(changes.activities.maxItems<SEMANTIC_REPAIR_SCHEMA.properties.upsert.properties.activities.maxItems);
  assert(changes.requirement_assignments.maxItems<SEMANTIC_REPAIR_SCHEMA.properties.upsert.properties.requirement_assignments.maxItems);
  assert.equal(schema.properties.remove.properties.requirement_assignments.maxItems,1);
  assert.equal(SEMANTIC_REPAIR_SCHEMA.properties.upsert.properties.requirement_assignments.maxItems,500);
});

test('untyped lowering errors are Host diagnostic gaps, not broad planner repairs',()=>{
  const plan={activities:[{key:'check'}],approvals:[{key:'approve'}],sequences:[],parallels:[],choices:[],records:[],lists:[],enums:[],source_dispositions:[],requirement_assignments:[]};
  const error=actionableSemanticError(Object.assign(new Error('decision outcome review approval'),{code:'AUTHORING_SEMANTIC'}),plan);
  assert.equal(error.code,'AUTHORING_DIAGNOSTIC_GAP');
  assert.equal(error.findings,undefined);
  assert.match(error.message,/decision outcome review approval/);
});

test('a top-level data cycle identifies its semantic activities and editable input relations',()=>{
  const {pack,resources}=sourceFixture(),sections=sourceSectionInventory(resources),ids=sections.map(item=>item.section_id);
  const compact={contract:CURRENT_SEMANTIC_BLUEPRINT_CONTRACT,purpose:'Diagnose a cross-activity cycle.',source_dispositions:sections.map(item=>({section_id:item.section_id,disposition:'workflow',activity_keys:['first','second'],note:'Required.'})),requirement_assignments:[],records:[],lists:[],enums:[],activities:[
    {key:'first',instructions:'Produce the first result.',profile:'main_write',source_sections:ids,inputs:[{name:'previous',from:'second.result'}],outputs:[{name:'result',kind:'text',values:[],type_ref:''}],tool:''},
    {key:'second',instructions:'Produce the second result.',profile:'main_write',source_sections:ids,inputs:[{name:'previous',from:'first.result'}],outputs:[{name:'result',kind:'text',values:[],type_ref:''}],tool:''},
  ],approvals:[],sequences:[],parallels:[],choices:[]};
  assert.throws(()=>new WorkflowForge().compile({pack,resources,blueprint:compact,context:{routing_rules:rules,routing_catalog:providers,providers,roles}}),error=>{
    assert.equal(error.code,'AUTHORING_SEMANTIC');
    assert.equal(error.findings?.[0]?.code,'top_level_dependency_cycle');
    assert.deepEqual(new Set(error.findings[0].semantic_keys),new Set(['first','second']));
    assert(error.findings[0].affected_semantic_fields.includes('activities.first.inputs'));
    assert(error.findings[0].affected_semantic_fields.includes('activities.second.inputs'));
    return true;
  });
});

test('compact authoring contract derives the root and semantic repair changes only named entities',()=>{
  const {pack,resources}=sourceFixture(),sections=sourceSectionInventory(resources),ids=sections.map(item=>item.section_id);
  const compact={contract:CURRENT_SEMANTIC_BLUEPRINT_CONTRACT,purpose:'Implement and review.',source_dispositions:sections.map(item=>({section_id:item.section_id,disposition:'workflow',activity_keys:['implement','review'],note:'Required by the brief.'})),requirement_assignments:[],records:[],lists:[],enums:[],activities:[
    {key:'implement',instructions:'Implement the requested change.',profile:'main_write',source_sections:ids,inputs:[],outputs:[{name:'result',kind:'text',values:[],type_ref:''}],tool:''},
    {key:'review',instructions:'Review the implementation evidence.',profile:'review',source_sections:ids,inputs:[{name:'implementation',from:'implement.result'}],outputs:[{name:'verdict',kind:'enum',values:['pass','fail'],type_ref:''}],tool:''},
  ],approvals:[],sequences:[{key:'delivery',members:['implement','review'],failure_meaning:'all_required'}],parallels:[],choices:[]};
  validateData(compact,SEMANTIC_BLUEPRINT_SCHEMA);
  const forged=new WorkflowForge().compile({pack,resources,blueprint:compact,context:{routing_rules:rules,routing_catalog:providers,providers,roles}});
  assert.equal(forged.compiled.validation.valid,true);const [implement,review]=forged.proposal.nodes;assert(forged.proposal.edges.some(edge=>edge.source===implement.id&&edge.target===review.id));
  const trace=authoringPipelineTrace({pack,resources,authoringPlan:compact,proposal:forged.proposal,compiled:forged.compiled});
  assert.deepEqual(trace.stages.map(stage=>stage.id),['start','expand','graph_assembly','execution_binding','deterministic_validation','final','end']);
  assert.equal(trace.stages.find(stage=>stage.id==='graph_assembly').result.node_count,forged.proposal.nodes.length);
  assert.equal(trace.stages.find(stage=>stage.id==='deterministic_validation').result.cycle_free,true);
  assert.equal(trace.stages.find(stage=>stage.id==='final').status,'pending');
  const empty={source_dispositions:[],requirement_assignments:[],records:[],lists:[],enums:[],activities:[],approvals:[],sequences:[],parallels:[],choices:[]};
  const instructionTarget=[{semantic_keys:['review'],affected_semantic_fields:['activities.instructions']}];
  const repaired=applySemanticRepair(compact,{contract:SEMANTIC_REPAIR_CONTRACT,purpose:'',upsert:{...structuredClone(empty),activities:[{...compact.activities[1],instructions:'Review exact implementation evidence and report gaps.'}]},remove:empty},{targets:instructionTarget});
  assert.equal(repaired.activities[0].instructions,compact.activities[0].instructions);assert.match(repaired.activities[1].instructions,/exact implementation evidence/);
  const ignored=[];
  const bounded=applySemanticRepair(compact,{contract:SEMANTIC_REPAIR_CONTRACT,purpose:'',upsert:{...structuredClone(empty),activities:[{...compact.activities[1],instructions:'Review exact evidence.',profile:'main_write'}]},remove:empty},{targets:instructionTarget,corrections:ignored});
  assert.equal(bounded.activities[1].instructions,'Review exact evidence.');
  assert.equal(bounded.activities[1].profile,'main_write');
  assert.deepEqual(ignored,[]);
  const newSequence={key:'initial_path',members:['implement','review'],failure_meaning:'all_required'};
  const sequenced=applySemanticRepair(compact,{contract:SEMANTIC_REPAIR_CONTRACT,purpose:'',upsert:{...structuredClone(empty),sequences:[newSequence]},remove:empty},{targets:[{semantic_keys:['implement'],affected_semantic_fields:['sequences.members']}]});
  assert.deepEqual(sequenced.sequences.at(-1),newSequence);
  const validationActivity={key:'validate',instructions:'Validate the implementation result.',profile:'main_read',source_sections:ids,inputs:[{name:'result',from:'implement.result'}],outputs:[{name:'passed',kind:'boolean',values:[],type_ref:''}],tool:'',fail_on_false:['passed']};
  const connectedAddition=applySemanticRepair(compact,{contract:SEMANTIC_REPAIR_CONTRACT,purpose:'',upsert:{...structuredClone(empty),activities:[validationActivity],sequences:[{...compact.sequences[0],members:['implement','validate','review']}]},remove:empty},{targets:[{semantic_keys:['implement'],affected_semantic_fields:['activities.outputs']} ]});
  assert.deepEqual(connectedAddition.activities.at(-1),validationActivity);
  assert.deepEqual(connectedAddition.sequences[0].members,['implement','validate','review']);
  const unlinked=applySemanticRepair(compact,{contract:SEMANTIC_REPAIR_CONTRACT,purpose:'',upsert:{...structuredClone(empty),sequences:[{...compact.sequences[0],members:['review']}]},remove:empty},{targets:[{semantic_keys:['implement'],affected_semantic_fields:['sequences.members']}]});
  assert.deepEqual(unlinked.sequences[0].members,['review']);
  const removeLinkedControl={contract:SEMANTIC_REPAIR_CONTRACT,purpose:'',upsert:empty,remove:{...structuredClone(empty),sequences:['delivery']}};
  assert.deepEqual(applySemanticRepair(compact,removeLinkedControl,{targets:[{semantic_keys:['implement'],affected_semantic_fields:['sequences'] }]}).sequences,[]);
  assert.throws(()=>applySemanticRepair(compact,{contract:SEMANTIC_REPAIR_CONTRACT,purpose:'',upsert:{...structuredClone(empty),activities:[{...validationActivity,key:'unrelated',inputs:[]}]},remove:empty},{targets:[{semantic_keys:['implement'],affected_semantic_fields:['activities.outputs']}]}),{code:'AUTHORING_REPAIR_SCOPE'});
  const changedCard={key:'changed_card',fields:[{name:'card',type:'text',required:true}],open:false};
  const changedCards={key:'changed_cards',item_type:'changed_card'};
  const typed=applySemanticRepair(compact,{contract:SEMANTIC_REPAIR_CONTRACT,purpose:'',upsert:{...structuredClone(empty),activities:[{...compact.activities[0],outputs:[{name:'cards',kind:'list',values:[],type_ref:'changed_cards'}]}],records:[changedCard],lists:[changedCards]},remove:empty},{targets:[{semantic_keys:['implement'],affected_semantic_fields:['activities.outputs']}]});
  assert.deepEqual(typed.records,[changedCard]);assert.deepEqual(typed.lists,[changedCards]);
  const dangling={...structuredClone(compact),lists:[{key:'card_results',item_type:'card_result'}]};
  const resultType={key:'card_result',fields:[{name:'summary',type:'text',required:true}],open:false};
  const typePatch={contract:SEMANTIC_REPAIR_CONTRACT,purpose:'',upsert:{...structuredClone(empty),records:[resultType]},remove:empty};
  assert.deepEqual(applySemanticRepair(dangling,typePatch,{targets:[{semantic_keys:['card_results'],affected_semantic_fields:['lists.card_results.item_type']}]}).records,[resultType]);
  assert.throws(()=>applySemanticRepair(dangling,typePatch,{targets:[{semantic_keys:['implement'],affected_semantic_fields:['activities.instructions']}]}),{code:'AUTHORING_REPAIR_SCOPE'});
  const duplicatePatch={contract:SEMANTIC_REPAIR_CONTRACT,purpose:'',upsert:{...structuredClone(empty),activities:[compact.activities[0],compact.activities[0]]},remove:empty};
  assert.throws(()=>applySemanticRepair(compact,duplicatePatch,{targets:[{semantic_keys:['implement'],affected_semantic_fields:['activities']}]}),{code:'AUTHORING_FORMAT'});
  const unrelated={contract:SEMANTIC_REPAIR_CONTRACT,purpose:'',upsert:{...structuredClone(empty),activities:[{...compact.activities[0],instructions:'Unrelated change.'}]},remove:empty};
  assert.equal(applySemanticRepair(compact,unrelated,{targets:instructionTarget}).activities[0].instructions,compact.activities[0].instructions);
  const removeReview={contract:SEMANTIC_REPAIR_CONTRACT,purpose:'',upsert:empty,remove:{...structuredClone(empty),activities:['review']}};
  assert.deepEqual(applySemanticRepair(compact,removeReview,{targets:[{semantic_keys:['review'],affected_semantic_fields:['activities.inputs']}]}).activities.map(item=>item.key),['implement']);
  assert.throws(()=>applySemanticRepair(compact,removeReview,{targets:[{semantic_keys:['implement'],affected_semantic_fields:['activities.inputs']}]}),{code:'AUTHORING_REPAIR_SCOPE'});
  const consumerChange={contract:SEMANTIC_REPAIR_CONTRACT,purpose:'',upsert:{...structuredClone(empty),activities:[{...compact.activities[1],instructions:'Changed through an upstream target.'}]},remove:empty};
  assert.equal(applySemanticRepair(compact,consumerChange,{targets:[{semantic_keys:['implement'],affected_semantic_fields:['activities.instructions']}]}).activities[1].instructions,compact.activities[1].instructions);
  const crossedFindings={contract:SEMANTIC_REPAIR_CONTRACT,purpose:'',upsert:{...structuredClone(empty),activities:[{...compact.activities[0],outputs:[]}]},remove:empty};
  assert.deepEqual(applySemanticRepair(compact,crossedFindings,{targets:[
    {semantic_keys:['implement'],affected_semantic_fields:['activities.instructions']},
    {semantic_keys:['review'],affected_semantic_fields:['activities.outputs']},
  ]}).activities[0].outputs,[]);
  const bindingChange={contract:SEMANTIC_REPAIR_CONTRACT,purpose:'',upsert:{...structuredClone(empty),activities:[{...compact.activities[1],inputs:[{name:'implementation_result',from:'implement.result'}]}]},remove:empty};
  const rebound=applySemanticRepair(compact,bindingChange,{targets:[{semantic_keys:['implement'],affected_semantic_fields:['activities.inputs']}]});
  assert.equal(rebound.activities[1].inputs[0].name,'implementation_result');
  assert(JSON.stringify(SEMANTIC_BLUEPRINT_SCHEMA).length<JSON.stringify(INTERNAL_SEMANTIC_BLUEPRINT_SCHEMA).length*0.9);
});

test('compact requirement assignments let the Host project future user input bindings without model fields',()=>{
  const compiled=compileWorkflowBrief({workflow_id:'input-fixture',name:'Input fixture',brief:'# Workflow\n\n## Process\n\nAsk the user for input before drafting the result.',provider_id:'native-luna'}),prepared=prepareResources(compiled.resources),snapshot={workflow:compiled.workflow,resources:prepared.manifest,provenance:compiled.provenance,import_report:compiled.import_report},pack={...snapshot,revision_hash:revisionHash(snapshot)},resources=compiled.resources;
  const sections=sourceSectionInventory(resources),ids=sections.map(item=>item.section_id),inputRequirement=observedSourceRequirements(resources).find(item=>item.requirement_kind==='user_input');
  assert(inputRequirement);
  const compact={contract:CURRENT_SEMANTIC_BLUEPRINT_CONTRACT,purpose:'Draft from the supplied task input.',source_dispositions:sections.map(item=>({section_id:item.section_id,disposition:'workflow',activity_keys:['draft'],note:'Required by the brief.'})),requirement_assignments:[{requirement_id:inputRequirement.requirement_id,activity_keys:['draft']}],records:[],lists:[],enums:[],activities:[
    {key:'draft',instructions:'Use the user-supplied task input to draft the result.',profile:'main_write',source_sections:ids,inputs:[{name:'editorial_answers',from:'input:editorial_answers'}],outputs:[{name:'result',kind:'text',values:[],type_ref:''}],tool:''},
  ],approvals:[],sequences:[],parallels:[],choices:[]};
  validateData(compact,SEMANTIC_BLUEPRINT_SCHEMA);
  const forged=new WorkflowForge().compile({pack,resources,blueprint:compact,context:{routing_rules:rules,routing_catalog:providers,providers,roles}}),mapping=forged.proposal.requirement_mappings.find(item=>item.requirement_id===inputRequirement.requirement_id),node=forged.proposal.nodes.find(item=>item.id===mapping.node_ids[0]);
  assert.equal(forged.compiled.validation.valid,true);assert.deepEqual(mapping.binding_names,['editorial_answers']);assert.equal(node.input_bindings.task,undefined);
  assert.equal(node.input_bindings.editorial_answers,'/inputs/editorial_answers');
  assert.deepEqual(forged.compiled.workflow.inputs_schema.properties.task,{type:'string'});
  assert.deepEqual(forged.compiled.workflow.inputs_schema.properties.editorial_answers,{type:'string'});
  assert(!(forged.compiled.workflow.inputs_schema.required??[]).includes('editorial_answers'));
});

test('one-member parallel syntax is collapsed mechanically without a semantic retry',()=>{
  const {pack,resources}=sourceFixture(),sections=sourceSectionInventory(resources),ids=sections.map(item=>item.section_id);
  const compact={contract:CURRENT_SEMANTIC_BLUEPRINT_CONTRACT,purpose:'Perform one optional fan-out activity and deliver it.',source_dispositions:sections.map(item=>({section_id:item.section_id,disposition:'workflow',activity_keys:['build'],note:'Required.'})),requirement_assignments:[],records:[],lists:[],enums:[],activities:[
    {key:'build',instructions:'Build the requested artifact.',profile:'worker_write',source_sections:ids,inputs:[],outputs:[{name:'artifact',kind:'text',values:[],type_ref:''}],tool:''},
  ],approvals:[],sequences:[],parallels:[{key:'fanout',members:['build'],failure_meaning:'all_required'}],choices:[]};
  validateData(compact,SEMANTIC_BLUEPRINT_SCHEMA);
  const forged=new WorkflowForge().compile({pack,resources,blueprint:compact,context:{routing_rules:rules,routing_catalog:providers,providers,roles}});
  assert.equal(forged.compiled.validation.valid,true);
  assert.equal(forged.proposal.nodes.some(node=>node.type==='parallel' || node.type==='join'),false);
  assert.equal(forged.proposal.nodes.filter(node=>node.prompt_template==='Build the requested artifact.').length,1);
});

test('runtime-cardinality work lowers to a non-Main sub-Agent pool while Main activities cannot configure quantity',()=>{
  const {pack,resources}=sourceFixture(),sections=sourceSectionInventory(resources),ids=sections.map(item=>item.section_id);
  const compact={contract:CURRENT_SEMANTIC_BLUEPRINT_CONTRACT,purpose:'Plan animation slots and render every slot concurrently.',source_dispositions:sections.map(item=>({section_id:item.section_id,disposition:'workflow',activity_keys:['plan','render'],note:'Required.'})),requirement_assignments:[],records:[],lists:[],enums:[],activities:[
    {key:'plan',instructions:'Plan the animation slots.',profile:'main_read',source_sections:ids,inputs:[],outputs:[{name:'slots',kind:'list',values:[],type_ref:''}],tool:''},
    {key:'render',instructions:'Render one independent animation per slot.',profile:'worker_read',source_sections:ids,inputs:[{name:'slots',from:'plan.slots'}],outputs:[{name:'renders',kind:'list',values:[],type_ref:''}],tool:'',fanout:{input:'slots',item_name:'slot',result_output:'renders',count_mode:'auto',fixed_count:0}},
  ],approvals:[],sequences:[{key:'delivery',members:['plan','render'],failure_meaning:'all_required'}],parallels:[],choices:[]};
  validateData(compact,SEMANTIC_BLUEPRINT_SCHEMA);
  const forged=new WorkflowForge().compile({pack,resources,blueprint:compact,context:{routing_rules:rules,routing_catalog:providers,providers,roles}}),plan=activityNode(forged.proposal,'plan'),render=activityNode(forged.proposal,'render');
  assert.equal(forged.compiled.validation.valid,true);
  assert.equal(plan.execution_target,'main');assert.equal(plan.subagent_count,undefined);assert.equal(plan.fanout,undefined);
  assert.equal(render.execution_target,'subagent');assert.equal(render.subagent_count,'auto');
  assert.equal(render.thread_lifecycle,undefined);
  assert.equal(forged.compiled.workflow.nodes.find(node=>node.id===render.id)?.executor.kind,'provider');
  assert.deepEqual(render.fanout,{input:'slots',item_name:'slot',result_output:'renders',distribution:'one_per_item',scheduling:'parallel',join:'all_required'});
  assert.match(render.prompt_template,/Process only the supplied batch/);

  const invalidScope=structuredClone(compact);invalidScope.activities[1].fanout.write_paths_field='write_paths';invalidScope.activities[1].profile='worker_read';
  assert(collectSemanticBlueprintFindings(invalidScope).some(item=>item.code==='fanout_write_paths_profile'));

  const unsafeWriters=structuredClone(compact);unsafeWriters.activities[1].profile='worker_write';
  assert(collectSemanticBlueprintFindings(unsafeWriters).some(item=>item.code==='fanout_write_isolation'));
  const serializedWriter=activityNode(new WorkflowForge().compile({pack,resources,blueprint:unsafeWriters,context:{routing_rules:rules,routing_catalog:providers,providers,roles}}).proposal,'render');
  assert.equal(serializedWriter.fanout.max_concurrency,1);

  const transcribedPackets=structuredClone(compact);transcribedPackets.activities[1].profile='worker_write';transcribedPackets.activities[1].fanout.write_paths_field='write_paths';
  assert.throws(()=>new WorkflowForge().compile({pack,resources,blueprint:transcribedPackets,context:{routing_rules:rules,routing_catalog:providers,providers,roles}}),error=>
    error.code==='AUTHORING_SEMANTIC'&&error.findings.some(item=>item.code==='fanout_host_item_source'&&item.semantic_keys.includes('render')));
  const packetContract={id:'prepare_slots',identity:{name:'prepare_slots',version:'1',sha256:'a'.repeat(64)},argv:['prepare_slots'],input_schema:{type:'object',properties:{},required:[],additionalProperties:false},output_schema:{type:'object',properties:{slots:{type:'array',items:{type:'object',properties:{write_paths:{type:'array',items:{type:'string'},minItems:1}},required:['write_paths'],additionalProperties:true}}},required:['slots'],additionalProperties:false},env_allow:[],permissions:{network:false,read_paths:[],write_paths:[]},output_cap_bytes:4096,deadline_ms:1000,idempotency:{mode:'safe'}};
  const hostToolPackets=structuredClone(transcribedPackets);hostToolPackets.activities[0].tool=packetContract.id;
  const hostToolContext={routing_rules:rules,routing_catalog:providers,providers,roles,host_tools:[packetContract.id],host_tool_contracts:[packetContract]};
  const hostToolNode=activityNode(new WorkflowForge().compile({pack,resources,blueprint:hostToolPackets,context:hostToolContext}).proposal,'render');
  assert.match(hostToolNode.input_bindings.slots,/\/nodes\/activity_\d+\/output\/slots/);
  assert.equal(hostToolNode.fanout.write_paths_field,'write_paths');

  const wrappedAgentPackets=structuredClone(transcribedPackets),joinContract=structuredClone(packetContract);
  joinContract.id='join_slots';joinContract.identity={...joinContract.identity,name:'join_slots'};joinContract.argv=['join_slots'];
  joinContract.input_schema={type:'object',properties:{slots:structuredClone(packetContract.output_schema.properties.slots)},required:['slots'],additionalProperties:false};
  wrappedAgentPackets.activities.splice(1,0,{key:'join',instructions:'Join the supplied slots.',profile:'main_read',source_sections:ids,
    inputs:[{name:'slots',from:'plan.slots'}],outputs:[{name:'slots',kind:'list',values:[],type_ref:''}],tool:joinContract.id});
  wrappedAgentPackets.activities[2].inputs[0].from='join.slots';wrappedAgentPackets.sequences[0].members=['plan','join','render'];
  assert(collectSemanticBlueprintFindings(wrappedAgentPackets).some(item=>item.code==='fanout_host_item_source'));
  const wrappedContext={routing_rules:rules,routing_catalog:providers,providers,roles,host_tools:[joinContract.id],host_tool_contracts:[joinContract]};
  assert.throws(()=>new WorkflowForge().compile({pack,resources,blueprint:wrappedAgentPackets,context:wrappedContext}),error=>
    error.code==='AUTHORING_SEMANTIC'&&error.findings.some(item=>item.code==='fanout_host_item_source'&&item.semantic_keys.includes('render')));

  const selectiveContract=structuredClone(packetContract);
  selectiveContract.id='select_slots';selectiveContract.identity={...selectiveContract.identity,name:'select_slots'};selectiveContract.argv=['select_slots'];
  selectiveContract.input_schema={type:'object',additionalProperties:false,required:['manifest','verdicts'],properties:{manifest:{type:'string'},verdicts:{type:'array',items:{type:'boolean'},minItems:1}}};
  selectiveContract.host_owned_item_fields=[{output:'slots',fields:['write_paths'],from_inputs:['manifest']}];
  const selectivePackets=structuredClone(transcribedPackets);
  selectivePackets.activities[0]={key:'review',instructions:'Review the supplied manifest.',profile:'worker_read',source_sections:ids,inputs:[{name:'manifest',from:'input:manifest'}],outputs:[{name:'verdicts',kind:'list',values:[],type_ref:''}],tool:''};
  selectivePackets.activities.splice(1,0,{key:'select',instructions:'Select failed Host packets.',profile:'main_read',source_sections:ids,inputs:[{name:'manifest',from:'input:manifest'},{name:'verdicts',from:'review.verdicts'}],outputs:[{name:'slots',kind:'list',values:[],type_ref:''}],tool:selectiveContract.id});
  selectivePackets.activities[2].inputs[0].from='select.slots';selectivePackets.sequences[0].members=['review','select','render'];
  selectivePackets.source_dispositions=selectivePackets.source_dispositions.map(item=>({...item,activity_keys:item.activity_keys.map(key=>key==='plan'?'review':key)}));
  const selectiveContext={routing_rules:rules,routing_catalog:providers,providers,roles,host_tools:[selectiveContract.id],host_tool_contracts:[selectiveContract]};
  const selectiveRender=activityNode(new WorkflowForge().compile({pack,resources,blueprint:selectivePackets,context:selectiveContext}).proposal,'render');
  assert.equal(selectiveRender.fanout.write_paths_field,'write_paths');

  const invalid=structuredClone(compact);invalid.activities[0].fanout={input:'slots',item_name:'slot',result_output:'slots',count_mode:'auto',fixed_count:0};
  assert.throws(()=>new WorkflowForge().compile({pack,resources,blueprint:invalid,context:{routing_rules:rules,routing_catalog:providers,providers,roles}}),error=>error.code==='AUTHORING_SEMANTIC'&&error.findings.some(item=>item.code==='fanout_owner'&&/Main activities cannot configure/.test(item.message)));
});

test('compact batch fan-out separates runtime batch count from concurrency and retains legacy modes',()=>{
  const {pack,resources}=sourceFixture(),sections=sourceSectionInventory(resources),ids=sections.map(item=>item.section_id);
  const compact={contract:CURRENT_SEMANTIC_BLUEPRINT_CONTRACT,purpose:'Process cards in bounded batches.',source_dispositions:sections.map(item=>({section_id:item.section_id,disposition:'workflow',activity_keys:['work'],note:'Required.'})),requirement_assignments:[],records:[],lists:[],enums:[],activities:[
    {key:'work',instructions:'Process the supplied cards.',profile:'worker_read',source_sections:ids,inputs:[{name:'cards',from:'input:cards'}],outputs:[{name:'results',kind:'list',values:[],type_ref:''}],tool:'',fanout:{input:'cards',item_name:'card',result_output:'results',count_mode:'auto',fixed_count:0,batch_size:10,max_concurrency:5}},
  ],approvals:[],sequences:[],parallels:[],choices:[]};
  const compile=value=>new WorkflowForge().compile({pack,resources,blueprint:value,context:{routing_rules:rules,routing_catalog:providers,providers,roles}});
  validateData(compact,SEMANTIC_BLUEPRINT_SCHEMA);
  const forged=compile(compact),node=forged.compiled.workflow.nodes.find(item=>item.name==='work');
  const decoded=decodeGeneratedProposalDetailed(JSON.parse(JSON.stringify({proposal:forged.proposal})),pack.revision_hash,{requirePlanningAnalysis:true,requireSourceDispositions:true,sourceInventory:sections});
  assert.deepEqual(activityNode(decoded.proposal,'work').fanout,node.fanout);
  const validationOptions={pack,resources,provenance:{source_revision:pack.revision_hash,routing_rules:rules,routing_catalog:providers,review_contract_version:18},context:{providers,roles}};
  const initial=validateGenerationProposal({proposal:compact},validationOptions),trace=initial.pipeline_trace;
  const persisted=JSON.parse(JSON.stringify({proposal:initial.proposal,host_pipeline:{contract:trace.contract,proposal_hash:trace.proposal_hash,results:trace.results}}));
  const replayed=validateGenerationProposal(persisted,validationOptions);
  assert.deepEqual(replayed.proposal,initial.proposal);
  assert.equal(replayed.pipeline_trace.proposal_hash,trace.proposal_hash);
  assert.deepEqual(node.fanout,{input:'cards',item_name:'card',result_output:'results',distribution:'partition',scheduling:'parallel',join:'all_required',batch_size:10,max_concurrency:5});
  assert.equal(node.subagent_count,'auto');
  assert.doesNotMatch(node.prompt_template,/dispatch the resolved number|concurrently|simulating multiple owners/);
  assert.match(node.prompt_template,/Return one batch result matching the supplied schema/);
  assert.doesNotMatch(node.prompt_template,/under results|joined list/);
  for(const size of [31,200,400]) {
    const cards=Array.from({length:size},(_,index)=>({id:index})),plan=resolvedSubagentPlan(node,{inputs:{cards},nodes:{}});
    assert.equal(plan.count,Math.ceil(size/10));
    assert.deepEqual(plan.assignments,Array.from({length:plan.count},(_,index)=>cards.slice(index*10,(index+1)*10)));
    assert.deepEqual(plan.assignments.flat(),cards);
    const handoff=nativeAgentHandoff({state:{run_id:'schema-fixture',inputs:{cards},nodes:{}}},node,{attempt_id:'attempt'},
      {handoff_required:true,adapter:{execution:'native_agent',spawn_config:{agent_type:'default'}},envelope:{workflow_id:pack.workflow.id,workflow_revision:pack.revision_hash,workspace:'C:/fixture',access:'read_only',effective_allowed_paths:[],prompt_template:node.prompt_template,inputs:{cards},node_id:node.id}},64000,[0]);
    assert.deepEqual(handoff.result_schema,node.outputs_schema.properties.results.items);
    assert.notDeepEqual(handoff.result_schema,node.outputs_schema);
    assert.match(handoff.packets[0].prompt,/Return one batch result matching the supplied schema/);
  }
  const automatic=structuredClone(compact);delete automatic.activities[0].fanout.batch_size;delete automatic.activities[0].fanout.max_concurrency;
  const automaticNode=activityNode(compile(automatic).proposal,'work');
  assert.equal(automaticNode.fanout.distribution,'one_per_item');
  assert.deepEqual(resolvedSubagentPlan(automaticNode,{inputs:{cards:[0,1,2,3]},nodes:{}}).assignments,[[0],[1],[2],[3]]);
  const perItem=structuredClone(automatic);perItem.activities[0].fanout.result_mode='per_item';
  const perItemNode=activityNode(compile(perItem).proposal,'work');
  assert.deepEqual(perItemNode.fanout,{input:'cards',item_name:'card',result_output:'results',distribution:'one_per_item',
    scheduling:'parallel',join:'all_required',result_mode:'per_item'});
  assert.deepEqual(resolvedSubagentPlan(perItemNode,{inputs:{cards:[0,1,2,3,4,5,6]},nodes:{}}).assignments,[[0],[1],[2],[3],[4],[5],[6]]);
  const incremental=structuredClone(compact);Object.assign(incremental.activities[0].fanout,{result_mode:'per_item',item_delivery:'incremental'});
  const incrementalNode=activityNode(compile(incremental).proposal,'work');
  assert.deepEqual(incrementalNode.fanout,{input:'cards',item_name:'card',result_output:'results',distribution:'partition',
    scheduling:'parallel',join:'all_required',batch_size:10,max_concurrency:5,result_mode:'per_item',item_delivery:'incremental'});
  const invalidIncremental=structuredClone(compact);invalidIncremental.activities[0].fanout.item_delivery='incremental';
  assert.throws(()=>compile(invalidIncremental),error=>error.code==='AUTHORING_SEMANTIC'&&error.findings.some(item=>item.code==='fanout_item_delivery'));
  const fixed=structuredClone(automatic);Object.assign(fixed.activities[0].fanout,{count_mode:'fixed',fixed_count:3});
  const fixedNode=activityNode(compile(fixed).proposal,'work');
  assert.equal(fixedNode.fanout.distribution,'partition');assert.equal(fixedNode.subagent_count,3);
  assert.deepEqual(resolvedSubagentPlan(fixedNode,{inputs:{cards:[0,1,2,3,4,5,6]},nodes:{}}).assignments,[[0,3,6],[1,4],[2,5]]);
  for(const field of ['batch_size','max_concurrency'])for(const value of [0,33,1.5]) {
    const invalid=structuredClone(compact);invalid.activities[0].fanout[field]=value;
    assert.throws(()=>validateData(invalid,SEMANTIC_BLUEPRINT_SCHEMA));
  }
  const contradictory=structuredClone(compact);Object.assign(contradictory.activities[0].fanout,{count_mode:'fixed',fixed_count:3});
  assert.throws(()=>compile(contradictory),error=>error.code==='AUTHORING_SEMANTIC'&&error.findings.some(item=>item.code==='fanout_batch_count'));
});

test('only explicit same-Provider task lineage creates a persistent Codex task',()=>{
  const {pack,resources}=sourceFixture(),sections=sourceSectionInventory(resources),ids=sections.map(item=>item.section_id);
  const compact={contract:CURRENT_SEMANTIC_BLUEPRINT_CONTRACT,purpose:'Continue research in the same durable task.',source_dispositions:sections.map(item=>({section_id:item.section_id,disposition:'workflow',activity_keys:['research','extend'],note:'Required.'})),requirement_assignments:[],records:[],lists:[],enums:[],activities:[
    {key:'research',instructions:'Research the problem.',profile:'worker_complex_read',source_sections:ids,inputs:[],outputs:[],tool:'',task_continues:'extend'},
    {key:'extend',instructions:'Continue that research in the same task.',profile:'worker_complex_read',source_sections:ids,inputs:[],outputs:[],tool:''},
  ],approvals:[],sequences:[{key:'research_sequence',members:['research','extend'],failure_meaning:'all_required'}],parallels:[],choices:[]};
  validateData(compact,SEMANTIC_BLUEPRINT_SCHEMA);
  const forged=new WorkflowForge().compile({pack,resources,blueprint:compact,context:{routing_rules:rules,routing_catalog:providers,providers,roles}});
  const research=activityNode(forged.proposal,'research'),extend=activityNode(forged.proposal,'extend');
  assert.equal(forged.compiled.validation.valid,true);
  assert.equal(research.execution_target,'thread');assert.equal(research.thread_lifecycle,'start');
  assert.equal(extend.execution_target,'thread');assert.equal(extend.thread_lifecycle,'continue');assert.equal(extend.thread_source_node,research.id);
  const invalid=structuredClone(compact);invalid.activities[1].profile='worker_read';
  assert.throws(()=>new WorkflowForge().compile({pack,resources,blueprint:invalid,context:{routing_rules:rules,routing_catalog:providers,providers,roles}}),error=>error.code==='AUTHORING_SEMANTIC'&&error.findings?.[0]?.code==='task_continuation_invalid');
});

test('fan-out joins one list even when the semantic plan names per-item intermediates',()=>{
  const {pack,resources}=sourceFixture(),sections=sourceSectionInventory(resources),ids=sections.map(item=>item.section_id);
  const compact={contract:CURRENT_SEMANTIC_BLUEPRINT_CONTRACT,purpose:'Process every input item and review the joined results.',source_dispositions:sections.map(item=>({section_id:item.section_id,disposition:'workflow',activity_keys:['plan','work','review'],note:'Required.'})),requirement_assignments:[],records:[],lists:[],enums:[],activities:[
    {key:'plan',instructions:'Identify items.',profile:'main_read',source_sections:ids,inputs:[],outputs:[{name:'items',kind:'list',values:[],type_ref:''}],tool:''},
    {key:'work',instructions:'Process each item and retain intermediate evidence.',profile:'worker_read',source_sections:ids,inputs:[{name:'items',from:'plan.items'}],outputs:[{name:'intermediate',kind:'text',values:[],type_ref:''},{name:'results',kind:'list',values:[],type_ref:''}],tool:'',fanout:{input:'items',item_name:'item',result_output:'results',count_mode:'auto',fixed_count:0}},
    {key:'review',instructions:'Review every joined result.',profile:'review',source_sections:ids,inputs:[{name:'results',from:'work.results'}],outputs:[],tool:''},
  ],approvals:[],sequences:[{key:'flow',members:['plan','work','review'],failure_meaning:'all_required'}],parallels:[],choices:[]};
  const forged=new WorkflowForge().compile({pack,resources,blueprint:compact,context:{routing_rules:rules,routing_catalog:providers,providers,roles}});
  assert.equal(forged.compiled.validation.valid,true);
  const worker=activityNode(forged.proposal,'work');
  assert.deepEqual(Object.keys(worker.outputs_schema.properties),['results']);
  assert.match(worker.prompt_template,/intermediate/);
});

test('a unique approval wrapper is connected to its choice branch by the Host',()=>{
  const shape=(name,kind='text',values=[])=>({name,kind,values,type_ref:''});
  const activity=(key,outputs,profile='main_read')=>({key,instructions:key,profile,source_sections:['source'],inputs:[],outputs,tool:''});
  const plan={contract:CURRENT_SEMANTIC_BLUEPRINT_CONTRACT,purpose:'Approve one chosen delivery path.',source_dispositions:[{section_id:'source',disposition:'workflow',activity_keys:['preview','decision','deliver','revise'],note:'Required.'}],requirement_assignments:[],records:[],lists:[],enums:[],activities:[activity('preview',[shape('artifact')]),activity('decision',[shape('route','enum',['final','revise'])],'decision'),activity('deliver',[],'main_write'),activity('revise',[],'main_write')],approvals:[{key:'confirm',question:'Approve the preview?',source_sections:['source'],subject:'preview.artifact',before:['deliver']}],sequences:[{key:'main_path',members:['preview','decision','route_choice'],failure_meaning:'all_required'},{key:'finalize_branch',members:['confirm','deliver'],failure_meaning:'all_required'}],parallels:[],choices:[{key:'route_choice',decision_activity:'decision',output:'route',branches:[{value:'final',body:'deliver'},{value:'revise',body:'revise'}],default_body:'revise'}]};
  const normalized=normalizeSemanticBlueprint(plan);
  const choice=normalized.choices.find(item=>item.key==='route_choice');
  assert.equal(choice.branches[0].body,'finalize_branch');
  assert.equal(normalized.root,'main_path');
});

test('Host connects a unique unplaced approval from its subject to its authorized work',()=>{
  const {pack,resources}=sourceFixture(),sections=sourceSectionInventory(resources),ids=sections.map(item=>item.section_id);
  const plan={contract:CURRENT_SEMANTIC_BLUEPRINT_CONTRACT,purpose:'Approve prepared work before delivery.',source_dispositions:sections.map(item=>({section_id:item.section_id,disposition:'workflow',activity_keys:['prepare','deliver'],note:'Required.'})),requirement_assignments:[],records:[],lists:[],enums:[],activities:[
    {key:'prepare',instructions:'Prepare the artifact.',profile:'main_read',source_sections:ids,inputs:[],outputs:[{name:'artifact',kind:'text',values:[],type_ref:''}],tool:''},
    {key:'deliver',instructions:'Deliver the approved artifact.',profile:'main_write',source_sections:ids,inputs:[{name:'artifact',from:'prepare.artifact'}],outputs:[],tool:''},
  ],approvals:[{key:'approve',question:'Approve this artifact?',source_sections:ids,subject:'prepare.artifact',before:['deliver']}],sequences:[],parallels:[],choices:[]};
  const forged=new WorkflowForge().compile({pack,resources,blueprint:plan,context:{routing_rules:rules,routing_catalog:providers,providers,roles}});
  assert.equal(forged.compiled.validation.valid,true);
  const prepare=activityNode(forged.proposal,'prepare'),gate=activityNode(forged.proposal,'approve'),deliver=activityNode(forged.proposal,'deliver');
  assert(forged.proposal.edges.some(edge=>edge.source===prepare.id&&edge.target===gate.id));
  assert(forged.proposal.edges.some(edge=>edge.source===gate.id&&edge.target===deliver.id));
});

test('Host authority promotes a mapped required reference to an executable disposition',()=>{
  const {pack,resources}=sourceFixture(),sections=sourceSectionInventory(resources),ids=sections.map(item=>item.section_id);
  const plan={contract:CURRENT_SEMANTIC_BLUEPRINT_CONTRACT,purpose:'Implement and review.',source_dispositions:sections.map(item=>({section_id:item.section_id,disposition:item.authority==='required'?'reference':'workflow',activity_keys:['work'],note:'Retained for the responsible activity.'})),requirement_assignments:[],records:[],lists:[],enums:[],activities:[{key:'work',instructions:'Implement and review the requested change.',profile:'main_write',source_sections:ids,inputs:[],outputs:[{name:'result',kind:'text',values:[],type_ref:''}],tool:''}],approvals:[],sequences:[],parallels:[],choices:[]};
  const forged=new WorkflowForge().compile({pack,resources,blueprint:plan,context:{routing_rules:rules,routing_catalog:providers,providers,roles}});
  assert.equal(forged.compiled.validation.valid,true);
  assert(forged.proposal.source_dispositions.filter(item=>sections.find(section=>section.section_id===item.section_id)?.authority==='required').every(item=>item.disposition==='workflow'));
  const omitted=structuredClone(plan);omitted.source_dispositions[0].disposition='omit';
  assert.throws(()=>new WorkflowForge().compile({pack,resources,blueprint:omitted,context:{routing_rules:rules,routing_catalog:providers,providers,roles}}),{code:'AUTHORING_SEMANTIC'});
});

test('compact root derivation rejects overlapping top-level control groups before graph compilation',()=>{
  const {pack,resources}=sourceFixture(),sections=sourceSectionInventory(resources),ids=sections.map(item=>item.section_id);
  const compact={contract:CURRENT_SEMANTIC_BLUEPRINT_CONTRACT,purpose:'Route one decision into one implementation.',source_dispositions:sections.map(item=>({section_id:item.section_id,disposition:'workflow',activity_keys:['decide','implement','review'],note:'Required.'})),requirement_assignments:[],records:[],lists:[],enums:[],activities:[
    {key:'decide',instructions:'Choose the implementation path.',profile:'decision',source_sections:ids,inputs:[],outputs:[{name:'path',kind:'enum',values:['a','b'],type_ref:''}],tool:''},
    {key:'implement',instructions:'Implement the selected path.',profile:'worker_write',source_sections:ids,inputs:[{name:'path',from:'decide.path'}],outputs:[{name:'result',kind:'text',values:[],type_ref:''}],tool:''},
    {key:'review',instructions:'Review the implementation.',profile:'review',source_sections:ids,inputs:[{name:'result',from:'implement.result'}],outputs:[],tool:''},
  ],approvals:[],sequences:[{key:'delivery',members:['decide','implement','review'],failure_meaning:'all_required'},{key:'review_only',members:['review'],failure_meaning:'all_required'}],parallels:[],choices:[{key:'routing',decision_activity:'decide',output:'path',branches:[{value:'a',body:'implement'},{value:'b',body:'implement'}],default_body:'implement'}]};
  assert.throws(()=>new WorkflowForge().compile({pack,resources,blueprint:compact,context:{routing_rules:rules,routing_catalog:providers,providers,roles}}),error=>error.code==='AUTHORING_SEMANTIC'&&/delivery and routing through decide, implement/.test(error.message)&&/delivery and review_only through review/.test(error.message));

  compact.sequences[0].members=['routing','review'];
  compact.sequences.splice(1,1);
  const forged=new WorkflowForge().compile({pack,resources,blueprint:compact,context:{routing_rules:rules,routing_catalog:providers,providers,roles}});
  assert.equal(forged.compiled.validation.valid,true);
});

test('semantic preflight aggregates independent overlap and unknown-reference defects in one planner repair',()=>{
  const {resources}=sourceFixture(),sections=sourceSectionInventory(resources),ids=sections.map(item=>item.section_id);
  const compact={contract:CURRENT_SEMANTIC_BLUEPRINT_CONTRACT,purpose:'Aggregate independent defects.',source_dispositions:sections.map(item=>({section_id:item.section_id,disposition:'workflow',activity_keys:['decide','implement','review'],note:'Required.'})),requirement_assignments:[],records:[{key:'bad_record',fields:[{name:'value',type:'missing_record_type',required:true}],open:false}],lists:[{key:'bad_list',item_type:'missing_item_type'}],enums:[],activities:[
    {key:'decide',instructions:'Decide.',profile:'decision',source_sections:ids,inputs:[],outputs:[{name:'path',kind:'enum',values:['a','b'],type_ref:''}],tool:''},
    {key:'implement',instructions:'Implement.',profile:'main_write',source_sections:ids,inputs:[{name:'missing',from:'unknown.result'}],outputs:[{name:'result',kind:'text',values:[],type_ref:''}],tool:''},
    {key:'review',instructions:'Review.',profile:'review',source_sections:ids,inputs:[],outputs:[{name:'verdict',kind:'text',values:[],type_ref:''}],tool:''},
  ],approvals:[],sequences:[{key:'delivery',members:['decide','implement','review'],failure_meaning:'all_required'},{key:'review_only',members:['review'],failure_meaning:'all_required'}],parallels:[],choices:[{key:'routing',decision_activity:'decide',output:'path',branches:[{value:'a',body:'implement'},{value:'b',body:'missing_body'}],default_body:'implement'}]};
  assert.throws(()=>new WorkflowForge().compile({pack:sourceFixture().pack,resources,blueprint:compact,context:{routing_rules:rules,routing_catalog:providers,providers,roles}}),error=>{
    assert.equal(error.code,'AUTHORING_SEMANTIC');
    const codes=new Set(error.findings.map(item=>item.code));
    assert(codes.has('top_level_overlap'));assert(codes.has('unknown_component'));assert(codes.has('unknown_input_producer'));assert(codes.has('unknown_data_type'));return true;
  });
});

test('outcome labels do not override activity authority while Host connects unique approvals',()=>{
  const {pack,resources}=sourceFixture(),sections=sourceSectionInventory(resources),ids=sections.map(item=>item.section_id);
  const compact={contract:CURRENT_SEMANTIC_BLUEPRINT_CONTRACT,purpose:'Aggregate authoring topology defects.',source_dispositions:sections.map(item=>({section_id:item.section_id,disposition:'workflow',activity_keys:['strategy','prescan','preview','edit','render'],note:'Required.'})),requirement_assignments:[],records:[],lists:[],enums:[],activities:[
    {key:'strategy',instructions:'Create a strategy.',profile:'main_read',source_sections:ids,inputs:[],outputs:[{name:'plan',kind:'text',values:[],type_ref:''}],tool:'',outcome:'artifact'},
    {key:'prescan',instructions:'Review the source.',profile:'worker_read',source_sections:ids,inputs:[],outputs:[{name:'findings',kind:'text',values:[],type_ref:''}],tool:'',outcome:'review'},
    {key:'edit',instructions:'Edit.',profile:'worker_write',source_sections:ids,inputs:[],outputs:[{name:'draft',kind:'text',values:[],type_ref:''}],tool:'',outcome:'artifact'},
    {key:'preview',instructions:'Verify the preview.',profile:'review',source_sections:ids,inputs:[],outputs:[{name:'verified',kind:'text',values:[],type_ref:''}],tool:'',outcome:'review'},
    {key:'render',instructions:'Render.',profile:'worker_write',source_sections:ids,inputs:[],outputs:[{name:'final',kind:'text',values:[],type_ref:''}],tool:'',outcome:'artifact'},
  ],approvals:[
    {key:'strategy_gate',question:'Approve strategy?',source_sections:ids,subject:'strategy.plan',before:['edit']},
    {key:'preview_gate',question:'Approve preview?',source_sections:ids,subject:'preview.verified',before:['render']},
  ],sequences:[{key:'delivery',members:['strategy','edit','preview','render'],failure_meaning:'all_required'}],parallels:[],choices:[]};
  const compiled=new WorkflowForge().compile({pack,resources,blueprint:compact,context:{routing_rules:rules,routing_catalog:providers,providers,roles}});
  const prescan=compiled.proposal.nodes.find(item=>item.semantic_key==='prescan');
  assert.equal(prescan.operation_mode,'read');
  assert.equal(prescan.completion_contract.outcome,'review');
  assert.equal(compiled.proposal.nodes.filter(item=>item.type==='human_gate').length,2);
});

test('write-capable review-and-repair keeps write routing with a review verdict',()=>{
  const {pack,resources}=sourceFixture(),sections=sourceSectionInventory(resources),ids=sections.map(item=>item.section_id);
  const compact={contract:CURRENT_SEMANTIC_BLUEPRINT_CONTRACT,purpose:'Review and repair a deliverable.',source_dispositions:sections.map(item=>({section_id:item.section_id,disposition:'workflow',activity_keys:['review_repair'],note:'Required.'})),requirement_assignments:[],records:[],lists:[],enums:[],activities:[
    {key:'review_repair',instructions:'Review the artifact and repair defects before delivery.',profile:'worker_complex_write',source_sections:ids,inputs:[],outputs:[{name:'passed',kind:'boolean',values:[],type_ref:''}],tool:'',outcome:'review',fail_on_false:['passed']},
  ],approvals:[],sequences:[],parallels:[],choices:[]};
  const compiled=new WorkflowForge().compile({pack,resources,blueprint:compact,context:{routing_rules:rules,routing_catalog:providers,providers,roles}});
  const node=compiled.proposal.nodes.find(item=>item.semantic_key==='review_repair');
  assert.equal(node.name,'review repair');
  assert.match(node.prompt_template,/Review the artifact and repair defects before delivery/);
  assert.equal(node.operation_mode,'write');
  assert.equal(node.task_type,'complex_implementation');
  assert.equal(node.completion_contract.outcome,'review');
  assert.deepEqual(node.completion_contract.fail_on_false,['passed']);
});

test('data binding to a later producer is a targeted semantic finding before graph validation',()=>{
  const {pack,resources}=sourceFixture(),sections=sourceSectionInventory(resources),ids=sections.map(item=>item.section_id);
  const compact={contract:CURRENT_SEMANTIC_BLUEPRINT_CONTRACT,purpose:'Produce a result before consuming it.',source_dispositions:sections.map(item=>({section_id:item.section_id,disposition:'workflow',activity_keys:['produce','consume'],note:'Required.'})),requirement_assignments:[],records:[],lists:[],enums:[],activities:[
    {key:'produce',instructions:'Produce evidence.',profile:'main_read',source_sections:ids,inputs:[],outputs:[{name:'evidence',kind:'text',values:[],type_ref:''}],tool:'',outcome:'artifact'},
    {key:'consume',instructions:'Use the evidence.',profile:'main_read',source_sections:ids,inputs:[{name:'evidence',from:'produce.evidence'}],outputs:[{name:'result',kind:'text',values:[],type_ref:''}],tool:'',outcome:'artifact'},
  ],approvals:[],sequences:[{key:'wrong_order',members:['consume','produce'],failure_meaning:'all_required'}],parallels:[],choices:[]};
  assert.throws(()=>new WorkflowForge().compile({pack,resources,blueprint:compact,context:{routing_rules:rules,routing_catalog:providers,providers,roles}}),error=>error.code==='AUTHORING_SEMANTIC'&&error.findings?.some(item=>item.code==='input_not_upstream'&&item.semantic_keys.includes('consume')&&item.semantic_keys.includes('produce')));
});

test('semantic preflight reports a required source section disposition before graph lowering',()=>{
  const {pack,resources}=sourceFixture(),sections=sourceSectionInventory(resources),ids=sections.map(item=>item.section_id);
  const compact={contract:CURRENT_SEMANTIC_BLUEPRINT_CONTRACT,purpose:'Implement the required workflow.',source_dispositions:sections.map((item,index)=>({section_id:item.section_id,disposition:index===0?'omit':'workflow',activity_keys:['implement'],note:'Required by the brief.'})),requirement_assignments:[],records:[],lists:[],enums:[],activities:[
    {key:'implement',instructions:'Implement the requested workflow.',profile:'main_write',source_sections:ids,inputs:[],outputs:[{name:'result',kind:'text',values:[],type_ref:''}],tool:'',outcome:'artifact'},
  ],approvals:[],sequences:[],parallels:[],choices:[]};
  assert.throws(()=>new WorkflowForge().compile({pack,resources,blueprint:compact,context:{routing_rules:rules,routing_catalog:providers,providers,roles}}),error=>error.code==='AUTHORING_SEMANTIC'&&error.findings.some(item=>item.code==='source_disposition_required'));
});

test('compact validation semantics lower into a Host-enforced false-result guard',()=>{
  const {pack,resources}=sourceFixture(),sections=sourceSectionInventory(resources),ids=sections.map(item=>item.section_id);
  const compact={contract:CURRENT_SEMANTIC_BLUEPRINT_CONTRACT,purpose:'Check the required result.',source_dispositions:sections.map(item=>({section_id:item.section_id,disposition:'workflow',activity_keys:['check'],note:'Required.'})),requirement_assignments:[],records:[],lists:[],enums:[],activities:[
    {key:'check',instructions:'Validate the result.',profile:'main_read',source_sections:ids,inputs:[],outputs:[{name:'passed',kind:'boolean',values:[],type_ref:''}],tool:'',outcome:'validated_artifact',fail_on_false:['passed']},
  ],approvals:[],sequences:[],parallels:[],choices:[]};
  const forged=new WorkflowForge().compile({pack,resources,blueprint:compact,context:{routing_rules:rules,routing_catalog:providers,providers,roles}});
  validateData(forged.proposal,EXPANSION_PROPOSAL_SCHEMA);
  const node=forged.proposal.nodes.find(item=>item.semantic_key==='check');
  assert.deepEqual(node.completion_contract.fail_on_false,['passed']);
  assert.equal(forged.compiled.validation.valid,true);
  compact.activities[0].fail_on_false=['missing'];
  assert.throws(()=>new WorkflowForge().compile({pack,resources,blueprint:compact,context:{routing_rules:rules,routing_catalog:providers,providers,roles}}),error=>error.code==='AUTHORING_SEMANTIC'&&error.findings.some(item=>item.code==='invalid_false_guard'));
});

test('Host edge evidence includes both sides of a phase boundary',()=>{
  const {pack,resources}=sourceFixture(),sections=sourceSectionInventory(resources);
  const [process,review]=sections.map(item=>item.section_id);
  const compact={contract:CURRENT_SEMANTIC_BLUEPRINT_CONTRACT,purpose:'Implement then review.',source_dispositions:[
    {section_id:process,disposition:'workflow',activity_keys:['implement'],note:'Required.'},
    {section_id:review,disposition:'workflow',activity_keys:['review'],note:'Required.'},
  ],requirement_assignments:[],records:[],lists:[],enums:[],activities:[
    {key:'implement',instructions:'Implement.',profile:'main_write',source_sections:[process],inputs:[],outputs:[{name:'result',kind:'text',values:[],type_ref:''}],tool:''},
    {key:'review',instructions:'Review.',profile:'review',source_sections:[review],inputs:[{name:'result',from:'implement.result'}],outputs:[],tool:''},
  ],approvals:[],sequences:[{key:'delivery',members:['implement','review'],failure_meaning:'all_required'}],parallels:[],choices:[]};
  const proposal=new WorkflowForge().compile({pack,resources,blueprint:compact,context:{routing_rules:rules,routing_catalog:providers,providers,roles}}).proposal;
  const producer=proposal.nodes.find(node=>node.semantic_key==='implement'),consumer=proposal.nodes.find(node=>node.semantic_key==='review');
  const transition=proposal.edges.find(edge=>edge.source===producer.id&&edge.target===consumer.id);
  assert(transition);
  for(const section of sections)assert(transition.source_spans.some(span=>canonicalJSON(span)===canonicalJSON(section.source_span)));
});

test('a consumer after an exclusive choice cannot require one branch-only output',()=>{
  const {pack,resources}=sourceFixture(),sections=sourceSectionInventory(resources),ids=sections.map(item=>item.section_id);
  const compact={contract:CURRENT_SEMANTIC_BLUEPRINT_CONTRACT,purpose:'Choose a route, then deliver.',source_dispositions:sections.map(item=>({section_id:item.section_id,disposition:'workflow',activity_keys:['decide','make','skip','deliver'],note:'Required.'})),requirement_assignments:[],records:[],lists:[],enums:[],activities:[
    {key:'decide',instructions:'Choose whether to make the artifact.',profile:'decision',source_sections:ids,inputs:[],outputs:[{name:'selected',kind:'boolean',values:[],type_ref:''}],tool:'',outcome:'decision'},
    {key:'make',instructions:'Make the artifact.',profile:'main_write',source_sections:ids,inputs:[],outputs:[{name:'result',kind:'text',values:[],type_ref:''}],tool:''},
    {key:'skip',instructions:'Retain the prior state.',profile:'main_read',source_sections:ids,inputs:[],outputs:[],tool:''},
    {key:'deliver',instructions:'Deliver the selected outcome.',profile:'main_write',source_sections:ids,inputs:[{name:'result',from:'make.result'}],outputs:[],tool:''},
  ],approvals:[],sequences:[{key:'delivery_path',members:['route','deliver'],failure_meaning:'all_required'}],parallels:[],choices:[{key:'route',decision_activity:'decide',output:'selected',branches:[{value:true,body:'make'}],default_body:'skip'}]};
  assert.throws(()=>new WorkflowForge().compile({pack,resources,blueprint:compact,context:{routing_rules:rules,routing_catalog:providers,providers,roles}}),error=>error.code==='AUTHORING_SEMANTIC'&&error.findings.some(item=>item.code==='branch_input_missing'&&item.semantic_keys.includes('deliver')));
  const shared=structuredClone(compact);shared.activities.find(item=>item.key==='deliver').inputs=[{name:'selected',from:'decide.selected'}];
  assert.doesNotThrow(()=>new WorkflowForge().compile({pack,resources,blueprint:shared,context:{routing_rules:rules,routing_catalog:providers,providers,roles}}));
});

test('fanout false-result guards point to a following aggregate validation activity',()=>{
  const {pack,resources}=sourceFixture(),sections=sourceSectionInventory(resources),ids=sections.map(item=>item.section_id);
  const compact={contract:CURRENT_SEMANTIC_BLUEPRINT_CONTRACT,purpose:'Run each item and validate the joined results.',source_dispositions:sections.map(item=>({section_id:item.section_id,disposition:'workflow',activity_keys:['run'],note:'Required.'})),requirement_assignments:[],records:[],lists:[],enums:[],activities:[
    {key:'run',instructions:'Run each item.',profile:'worker_write',source_sections:ids,inputs:[{name:'items',from:'input:items'}],outputs:[{name:'results',kind:'list',values:[],type_ref:''},{name:'all_passed',kind:'boolean',values:[],type_ref:''}],tool:'',fanout:{input:'items',item_name:'item',result_output:'results',count_mode:'auto',fixed_count:0},fail_on_false:['all_passed']},
  ],approvals:[],sequences:[],parallels:[],choices:[]};
  assert.throws(()=>new WorkflowForge().compile({pack,resources,blueprint:compact,context:{routing_rules:rules,routing_catalog:providers,providers,roles}}),error=>error.code==='AUTHORING_SEMANTIC'&&error.findings.some(item=>item.code==='fanout_false_guard'&&item.semantic_keys.includes('run')));
});

test('source contracts keep exact CLI distinct from candidate artifact observations',()=>{
  const python=Buffer.from(`import argparse\nparser=argparse.ArgumentParser()\nparser.add_argument("scenario", type=Path)\nparser.add_argument("--project-root", required=True, type=Path)\nparser.add_argument("--evidence", required=True, type=Path)\nrequired=("schema_version","setup")\nif self.spec.get("schema_version") != 1: raise ValueError()\nsetup=_require_list(self.spec.get("setup"), "setup")\nif not setup: raise ValueError()\nfor index, call_raw in enumerate(setup):\n    call=_require_mapping(call_raw, "call")\n`);
  const compiled=compileWorkflowBrief({workflow_id:'source-contract-fixture',name:'Source contract fixture',brief:'# Workflow\n\n## Process\n\nCreate a scenario, approve it, then run `python scripts/run.py scenario.json --project-root . --evidence evidence.json`.',provider_id:'native-luna'}),resources={...compiled.resources,'source/scripts/run.py':python},prepared=prepareResources(resources),snapshot={workflow:compiled.workflow,resources:prepared.manifest,provenance:compiled.provenance,import_report:compiled.import_report},pack={...snapshot,revision_hash:revisionHash(snapshot)};
  const sections=sourceSectionInventory(resources),ids=sections.map(item=>item.section_id),contracts=sourceContractIndex(resources).contracts,cli=contracts.find(item=>item.kind==='python_cli'),artifact=contracts.find(item=>item.kind==='json_artifact');
  assert.deepEqual(cli.interface.positionals.map(item=>item.name),['scenario']);assert.deepEqual(cli.interface.options.map(item=>item.flags[0]),['--project-root','--evidence']);
  assert.equal(artifact.status,'candidate');assert.equal(artifact.observed_direction,'read');
  const compact={contract:CURRENT_SEMANTIC_BLUEPRINT_CONTRACT,purpose:'Create, approve and validate one scenario.',source_dispositions:sections.map(item=>({section_id:item.section_id,disposition:'workflow',activity_keys:['create','approve','run'],note:'Required.'})),requirement_assignments:[],records:[],lists:[],enums:[],activities:[
    {key:'create',instructions:'Create the scenario artifact.',profile:'main_write',source_sections:ids,inputs:[],outputs:[{name:'scenario',kind:'object',values:[],type_ref:'',contract_ref:artifact.contract_id}],tool:'',outcome:'artifact'},
    {key:'run',instructions:'Validate the approved scenario.',profile:'worker_write',source_sections:ids,inputs:[{name:'scenario',from:'create.scenario'}],outputs:[{name:'evidence',kind:'text',values:[],type_ref:'',contract_ref:cli.contract_id}],tool:'',contract_refs:[cli.contract_id],on_missing:'block',outcome:'validated_artifact',repeat_until:{condition:'the semantic scenario runner succeeds',max_attempts:3}},
  ],approvals:[{key:'approve',question:'Approve this exact scenario revision?',source_sections:ids,subject:'create.scenario',before:['run']}],sequences:[{key:'delivery',members:['create','approve','run'],failure_meaning:'all_required'}],parallels:[],choices:[]};
  validateData(compact,SEMANTIC_BLUEPRINT_SCHEMA);
  const forged=new WorkflowForge().compile({pack,resources,blueprint:compact,context:{routing_rules:rules,routing_catalog:providers,providers,roles}}),create=forged.proposal.nodes.find(node=>node.semantic_key==='create'),gate=forged.proposal.nodes.find(node=>node.semantic_key==='approve'),run=forged.proposal.nodes.find(node=>node.semantic_key==='run');
  assert.deepEqual(create.outputs_schema.properties.scenario,{type:'object',additionalProperties:true});
  assert.equal(create.prompt_template,'Create the scenario artifact.');
  assert(create.resource_refs.includes('source/scripts/run.py'));
  assert(run.resource_refs.includes('source/scripts/run.py'));
  assert(!create.source_spans.some(span=>span.resource==='source/scripts/run.py'));
  assert.deepEqual(run.source_spans.filter(span=>span.resource==='source/scripts/run.py'),cli.source_spans);
  assert.doesNotMatch(create.prompt_template,/Host-indexed source interfaces|schema_version/);
  assert.equal(gate.input_bindings.subject,`/nodes/${create.id}/output/scenario`);assert.equal(run.retry_max_attempts,3);assert.doesNotMatch(run.prompt_template,/Host-indexed source interfaces|--project-root|--scenario/);
  assert.deepEqual(run.outputs_schema.properties.evidence,{type:'string'});
  assert.deepEqual(create.completion_contract,{on_missing:'block',outcome:'artifact'});
  assert.deepEqual(run.completion_contract,{on_missing:'block',outcome:'validated_artifact'});
  const compiledRun=forged.compiled.workflow.nodes.find(node=>node.id===run.id);
  assert.equal(compiledRun.retry.max_attempts,3);
  assert.deepEqual(compiledRun.completion_contract,run.completion_contract);
});

test('compact root derivation orders disjoint control groups by activity data dependencies',()=>{
  const {pack,resources}=sourceFixture(),sections=sourceSectionInventory(resources),ids=sections.map(item=>item.section_id);
  const compact={contract:CURRENT_SEMANTIC_BLUEPRINT_CONTRACT,purpose:'Prepare, run two checks, then summarize.',source_dispositions:sections.map(item=>({section_id:item.section_id,disposition:'workflow',activity_keys:['prepare','check_a','check_b','summarize'],note:'Required.'})),requirement_assignments:[],records:[],lists:[],enums:[],activities:[
    {key:'prepare',instructions:'Prepare the shared input.',profile:'main_read',source_sections:ids,inputs:[],outputs:[{name:'prepared_input',kind:'text',values:[],type_ref:''}],tool:''},
    {key:'check_a',instructions:'Run check A.',profile:'worker_read',source_sections:ids,inputs:[{name:'prepared_input',from:'prepare.prepared_input'}],outputs:[{name:'result_a',kind:'text',values:[],type_ref:''}],tool:''},
    {key:'check_b',instructions:'Run check B.',profile:'worker_read',source_sections:ids,inputs:[{name:'prepared_input',from:'prepare.prepared_input'}],outputs:[{name:'result_b',kind:'text',values:[],type_ref:''}],tool:''},
    {key:'summarize',instructions:'Summarize both checks.',profile:'main_read',source_sections:ids,inputs:[{name:'a',from:'check_a.result_a'},{name:'b',from:'check_b.result_b'}],outputs:[{name:'summary',kind:'text',values:[],type_ref:''}],tool:''},
  ],approvals:[],sequences:[{key:'preparation',members:['prepare'],failure_meaning:'all_required'},{key:'closeout',members:['summarize'],failure_meaning:'all_required'}],parallels:[{key:'checks',members:['check_a','check_b'],failure_meaning:'all_required'}],choices:[]};
  const forged=new WorkflowForge().compile({pack,resources,blueprint:compact,context:{routing_rules:rules,routing_catalog:providers,providers,roles}});
  assert.equal(forged.compiled.validation.valid,true);
  const workflow=forged.compiled.workflow,summary=workflow.nodes.find(node=>node.prompt_template==='Summarize both checks.'),incoming=workflow.edges.find(edge=>edge.target===summary.id);
  assert.equal(workflow.nodes.find(node=>node.id===incoming.source).type,'join');
  assert(workflow.edges.some(edge=>edge.source===summary.id&&edge.target==='final'));
});

test('WorkflowForge rejects duplicate semantic keys before keyed collections become Maps',()=>{
  const {pack,resources}=sourceFixture(),sections=sourceSectionInventory(resources),ids=sections.map(item=>item.section_id);
  const base=blueprint({purpose:'Reject ambiguous semantic identity.',source_dispositions:dispositions(sections,['work']),activities:[activity('work','Perform the work.',ids)],root:'work'});
  const candidates={
    activities:activity('work','Duplicate the work.',ids),
    approvals:{key:'approve',question:'Approve?',source_sections:ids},
    sequences:{key:'sequence',members:['work'],failure_meaning:'all_required'},
    parallels:{key:'parallel',members:['work','work'],failure_meaning:'all_required'},
    choices:{key:'choice',decision_activity:'work',output:'result',branches:[{value:'yes',body:'work'}],default_body:'work'},
  };
  for(const [collection,item] of Object.entries(candidates)){
    const candidate=structuredClone(base);
    candidate[collection]=collection==='activities'?[candidate.activities[0],structuredClone(item)]:[structuredClone(item),structuredClone(item)];
    assert.throws(()=>new WorkflowForge().compile({pack,resources,blueprint:candidate,context:{routing_rules:rules,routing_catalog:providers,providers,roles}}),{code:'AUTHORING_FORMAT'});
  }
});

test('WorkflowForge rejects duplicate activity input names before any binding projection',()=>{
  const {pack,resources}=sourceFixture(),sections=sourceSectionInventory(resources),ids=sections.map(item=>item.section_id);
  const compact={contract:CURRENT_SEMANTIC_BLUEPRINT_CONTRACT,purpose:'Preserve every declared input relation.',source_dispositions:sections.map(item=>({section_id:item.section_id,disposition:'workflow',activity_keys:['produce','consume'],note:'Required.'})),requirement_assignments:[],records:[],lists:[],enums:[],activities:[
    {key:'produce',instructions:'Produce one result.',profile:'main_read',source_sections:ids,inputs:[],outputs:[{name:'result',kind:'text',values:[],type_ref:''}],tool:''},
    {key:'consume',instructions:'Consume both named relations.',profile:'main_read',source_sections:ids,inputs:[{name:'primary',from:'produce.result'},{name:'secondary',from:'produce.result'}],outputs:[],tool:''},
  ],approvals:[],sequences:[{key:'delivery',members:['produce','consume'],failure_meaning:'all_required'}],parallels:[],choices:[]};
  const positive=new WorkflowForge().compile({pack,resources,blueprint:compact,context:{routing_rules:rules,routing_catalog:providers,providers,roles}});
  const consumer=positive.proposal.nodes.find(node=>node.prompt_template==='Consume both named relations.');
  assert.equal(consumer.input_bindings.primary,consumer.input_bindings.secondary);

  const duplicateV4=structuredClone(compact);duplicateV4.activities[1].inputs[1].name='primary';
  assert.throws(()=>new WorkflowForge().compile({pack,resources,blueprint:duplicateV4,context:{routing_rules:rules,routing_catalog:providers,providers,roles}}),{code:'AUTHORING_FORMAT'});

  const duplicateV3=blueprint({purpose:'Reject duplicate internal inputs.',source_dispositions:dispositions(sections,['produce','consume']),activities:[
    activity('produce','Produce one result.',ids,{produces:[{name:'result',shape:'text'}]}),
    activity('consume','Consume the result.',ids,{consumes:[{name:'payload',from:{activity:'produce',output:'result'}},{name:'payload',from:{activity:'produce',output:'result'}}]}),
  ],sequences:[{key:'delivery',members:['produce','consume'],failure_meaning:'all_required'}],root:'delivery'});
  assert.throws(()=>new WorkflowForge().compile({pack,resources,blueprint:duplicateV3,context:{routing_rules:rules,routing_catalog:providers,providers,roles}}),{code:'AUTHORING_FORMAT'});

  const empty={source_dispositions:[],requirement_assignments:[],records:[],lists:[],enums:[],activities:[],approvals:[],sequences:[],parallels:[],choices:[]};
  const duplicateRepair={contract:SEMANTIC_REPAIR_CONTRACT,purpose:'',upsert:{...structuredClone(empty),activities:[duplicateV4.activities[1]]},remove:empty};
  assert.throws(()=>applySemanticRepair(compact,duplicateRepair,{targets:[{semantic_keys:[duplicateV4.activities[1].key],affected_semantic_fields:['activities.inputs']}]}),{code:'AUTHORING_FORMAT'});
});

test('WorkflowForge lowers a brief semantic blueprint and owns every mechanical graph field',()=>{
  const {pack,resources}=sourceFixture(),sections=sourceSectionInventory(resources),ids=sections.map(item=>item.section_id);
  const semantic=blueprint({purpose:'Implement and review.',source_dispositions:dispositions(sections,['implement','review']),activities:[
    activity('implement','Implement the requested change.',ids,{operation:'write',produces:[{name:'result',shape:'text'}]}),
    activity('review','Review the implementation evidence.',ids,{kind:'review',consumes:[{name:'implementation',from:{activity:'implement',output:'result'}}],produces:[{name:'verdict',shape:{kind:'enum',values:['pass','fail']}}]}),
  ],sequences:[{key:'root_sequence',members:['implement','review'],failure_meaning:'all_required'}],root:'root_sequence'});
  const forged=new WorkflowForge().compile({pack,resources,blueprint:semantic,context:{routing_rules:rules,routing_catalog:providers,providers,roles}});
  assert.equal(forged.compiled.validation.valid,true);
  assert.deepEqual(forged.proposal.nodes.map(node=>node.id),['activity_001','activity_002']);
  assert.equal(forged.proposal.nodes[1].input_bindings.implementation,'/nodes/activity_001/output/result');
  assert.equal(forged.proposal.nodes[0].source_span.start_line,sections[0].source_span.start_line);
  assert.equal(forged.proposal.nodes[0].source_span.end_line,sections[0].source_span.end_line);
  assert.deepEqual(forged.proposal.nodes[0].source_spans,sections.map(item=>item.source_span));
  assert(forged.proposal.edges.every(edge=>/^edge_\d{3}$/.test(edge.id)));
  assert(!JSON.stringify(forged.proposal).includes('planning_analysis.main_responsibilities'));
});

test('WorkflowForge derives parallel/join and conditional fan-in without model-authored IDs or pointers',()=>{
  const {pack,resources}=sourceFixture(),sections=sourceSectionInventory(resources),ids=sections.map(item=>item.section_id);
  const decide=activity('decide','Choose a route.',ids,{kind:'decision',produces:[{name:'route',shape:{kind:'enum',values:['a','b']}}]});
  const branch=value=>activity(`branch_${value}`,`Perform branch ${value}.`,ids,{produces:[{name:'result',shape:'text'}]});
  const semantic=blueprint({purpose:'Branch safely.',source_dispositions:dispositions(sections,['decide','branch_a','branch_b']),activities:[decide,branch('a'),branch('b')],choices:[{key:'root_choice',decision_activity:'decide',output:'route',branches:[{value:'a',body:'branch_a'}],default_body:'branch_b'}],root:'root_choice'});
  const forged=new WorkflowForge().compile({pack,resources,blueprint:semantic,context:{routing_rules:rules,routing_catalog:providers,providers,roles}});
  assert.equal(forged.compiled.validation.valid,true);
  assert.equal(forged.proposal.nodes.filter(node=>node.type==='condition').length,1);
  const branchA=activityNode(forged.proposal,'branch_a'),branchB=activityNode(forged.proposal,'branch_b');
  assert.deepEqual(forged.compiled.workflow.nodes.find(node=>node.id==='final').input_bindings.upstream_result.coalesce.sort(),[`/nodes/${branchA.id}/output`,`/nodes/${branchB.id}/output`].sort());
});

test('WorkflowForge branches directly on a work activity scalar result',()=>{
  const {pack,resources}=sourceFixture(),sections=sourceSectionInventory(resources),ids=sections.map(item=>item.section_id);
  const semantic=blueprint({purpose:'Route the measured result.',source_dispositions:dispositions(sections,['check','passed','failed']),activities:[
    activity('check','Run the actual check and report its result.',ids,{produces:[{name:'passed',shape:{kind:'boolean',values:[]}}]}),
    activity('passed','Continue after a passing check.',ids),
    activity('failed','Report the failed check.',ids),
  ],choices:[{key:'result_route',decision_activity:'check',output:'passed',branches:[{value:true,body:'passed'}],default_body:'failed'}],root:'result_route'});
  const forged=new WorkflowForge().compile({pack,resources,blueprint:semantic,context:{routing_rules:rules,routing_catalog:providers,providers,roles}});
  assert.equal(forged.compiled.validation.valid,true);
  const check=activityNode(forged.proposal,'check'),route=forged.proposal.nodes.find(node=>node.type==='condition');
  assert.equal(check.type,'agent');
  assert.equal(route.cases[0].when.args[0].path,`/nodes/${check.id}/output/passed`);
});

test('a choice after parallel work routes from the Join, not its producer branch',()=>{
  const {pack,resources}=sourceFixture(),sections=sourceSectionInventory(resources),ids=sections.map(item=>item.section_id);
  const semantic=blueprint({purpose:'Check independent evidence before routing.',source_dispositions:dispositions(sections,['check_a','check_b','passed','failed']),activities:[
    activity('check_a','Run check A.',ids,{produces:[{name:'passed',shape:{kind:'boolean',values:[]}}]}),
    activity('check_b','Run check B.',ids,{produces:[{name:'evidence',shape:'text'}]}),
    activity('passed','Continue after the joined checks.',ids),
    activity('failed','Report a failed check.',ids),
  ],sequences:[{key:'whole',members:['checks','route'],failure_meaning:'all_required'}],parallels:[{key:'checks',members:['check_a','check_b'],failure_meaning:'all_required'}],choices:[{key:'route',decision_activity:'check_a',output:'passed',branches:[{value:true,body:'passed'}],default_body:'failed'}],root:'whole'});
  const forged=new WorkflowForge().compile({pack,resources,blueprint:semantic,context:{routing_rules:rules,routing_catalog:providers,providers,roles}});
  assert.equal(forged.compiled.validation.valid,true);
  const join=forged.proposal.nodes.find(node=>node.type==='join'),route=forged.proposal.nodes.find(node=>node.type==='condition'),producer=activityNode(forged.proposal,'check_a');
  assert(forged.proposal.edges.some(edge=>edge.source===join.id&&edge.target===route.id));
  assert(!forged.proposal.edges.some(edge=>edge.source===producer.id&&edge.target===route.id));
});

test('WorkflowForge preserves typed choice literals and rejects mismatched branch values before graph compilation',()=>{
  const cases=[
    {shape:{kind:'boolean',values:[]},value:true,other:false},
    {shape:{kind:'number',values:[]},value:1,other:2},
    {shape:{kind:'text',values:[]},value:'true',other:'false'},
  ];
  for(const [index,item] of cases.entries()){
    const {pack,resources}=sourceFixture(),sections=sourceSectionInventory(resources),ids=sections.map(section=>section.section_id),key=`route_${index}`;
    const semantic=blueprint({purpose:'Preserve the decision output JSON type.',source_dispositions:dispositions(sections,['decide','matched','fallback']),activities:[
      activity('decide','Choose the typed route.',ids,{kind:'decision',produces:[{name:key,shape:item.shape}]}),
      activity('matched','Handle the matching value.',ids,{produces:[{name:'result',shape:'text'}]}),
      activity('fallback','Handle every other value.',ids,{produces:[{name:'result',shape:'text'}]}),
    ],choices:[{key:'typed_choice',decision_activity:'decide',output:key,branches:[{value:item.value,body:'matched'}],default_body:'fallback'}],root:'typed_choice'});
    const forged=new WorkflowForge().compile({pack,resources,blueprint:semantic,context:{routing_rules:rules,routing_catalog:providers,providers,roles}}),condition=forged.proposal.nodes.find(node=>node.type==='condition'),decision=activityNode(forged.proposal,'decide');
    assert.equal(condition.cases[0].when.args[1].value,item.value);assert.equal(typeof condition.cases[0].when.args[1].value,typeof item.value);
    assert.equal(evaluateExpression(condition.cases[0].when,{nodes:{[decision.id]:{output:{[key]:item.value}}}}),true);
    assert.equal(evaluateExpression(condition.cases[0].when,{nodes:{[decision.id]:{output:{[key]:item.other}}}}),false);
  }
  const {pack,resources}=sourceFixture(),sections=sourceSectionInventory(resources),ids=sections.map(section=>section.section_id);
  const invalid=blueprint({purpose:'Reject stringified booleans.',source_dispositions:dispositions(sections,['decide','matched','fallback']),activities:[
    activity('decide','Choose the boolean route.',ids,{kind:'decision',produces:[{name:'selected',shape:{kind:'boolean',values:[]}}]}),activity('matched','Match.',ids),activity('fallback','Fallback.',ids),
  ],choices:[{key:'invalid_choice',decision_activity:'decide',output:'selected',branches:[{value:'true',body:'matched'}],default_body:'fallback'}],root:'invalid_choice'});
  assert.throws(()=>new WorkflowForge().compile({pack,resources,blueprint:invalid,context:{routing_rules:rules,routing_catalog:providers,providers,roles}}),error=>{
    assert.equal(error.code,'AUTHORING_SEMANTIC');assert.equal(error.findings.length,1);
    assert.deepEqual(error.findings[0].semantic_keys,['invalid_choice']);
    assert(error.findings[0].affected_semantic_fields.includes('choices'));
    return true;
  });
});

test('a decision condition cites its decision source, not every downstream branch section',()=>{
  const {pack,resources}=sourceFixture(),sections=sourceSectionInventory(resources),[decisionSection,branchSection]=sections.map(item=>item.section_id);
  const semantic=blueprint({purpose:'Choose one route.',source_dispositions:dispositions(sections,['decide','yes','no']),activities:[
    activity('decide','Select a route.',[decisionSection],{kind:'decision',produces:[{name:'selected',shape:{kind:'boolean',values:[]}}]}),
    activity('yes','Take the selected route.',[branchSection]),activity('no','Take the other route.',[branchSection]),
  ],choices:[{key:'route',decision_activity:'decide',output:'selected',branches:[{value:true,body:'yes'}],default_body:'no'}],root:'route'});
  const proposal=new WorkflowForge().compile({pack,resources,blueprint:semantic,context:{routing_rules:rules,routing_catalog:providers,providers,roles}}).proposal;
  const condition=proposal.nodes.find(node=>node.type==='condition');
  assert.deepEqual(condition.source_spans,[sections[0].source_span]);
});

test('entry and exit edges cite their adjacent semantic activity instead of the whole program',()=>{
  const {pack,resources}=sourceFixture(),sections=sourceSectionInventory(resources),[firstSection,lastSection]=sections.map(item=>item.section_id);
  const semantic=blueprint({purpose:'Run two phases.',source_dispositions:dispositions(sections,['first','last']),activities:[
    activity('first','Implement the change.',[firstSection]),activity('last','Review the result.',[lastSection]),
  ],sequences:[{key:'flow',members:['first','last'],failure_meaning:'all_required'}],root:'flow'});
  const proposal=new WorkflowForge().compile({pack,resources,blueprint:semantic,context:{routing_rules:rules,routing_catalog:providers,providers,roles}}).proposal;
  const first=activityNode(proposal,'first'),last=activityNode(proposal,'last');
  assert.deepEqual(proposal.edges.find(edge=>edge.source==='start'&&edge.target===first.id).source_spans,[sections[0].source_span]);
  assert.deepEqual(proposal.edges.find(edge=>edge.source===last.id&&edge.target==='final').source_spans,[sections[1].source_span]);
});

test('WorkflowForge derives a structured parallel region and aggregate bindings',()=>{
  const {pack,resources}=sourceFixture(),sections=sourceSectionInventory(resources),ids=sections.map(item=>item.section_id);
  const semantic=blueprint({purpose:'Run independent checks.',source_dispositions:dispositions(sections,['check_a','check_b','summarize']),activities:[
    activity('check_a','Run check A.',ids,{produces:[{name:'a',shape:'text'}]}),activity('check_b','Run check B.',ids,{produces:[{name:'b',shape:'text'}]}),
    activity('summarize','Summarize both checks.',ids,{consumes:[{name:'a',from:{activity:'check_a',output:'a'}},{name:'b',from:{activity:'check_b',output:'b'}}],produces:[{name:'summary',shape:'text'}]}),
  ],parallels:[{key:'checks',members:['check_a','check_b'],failure_meaning:'all_required'}],sequences:[{key:'root_sequence',members:['checks','summarize'],failure_meaning:'all_required'}],root:'root_sequence'});
  const forged=new WorkflowForge().compile({pack,resources,blueprint:semantic,context:{routing_rules:rules,routing_catalog:providers,providers,roles}});
  assert.equal(forged.compiled.validation.valid,true);
  const fork=forged.proposal.nodes.find(node=>node.type==='parallel'),join=forged.proposal.nodes.find(node=>node.type==='join'),summary=forged.proposal.nodes.find(node=>node.name==='summarize');
  assert.equal(fork.join_id,join.id);assert.equal(join.parallel_id,fork.id);
  const checkA=activityNode(forged.proposal,'check_a'),checkB=activityNode(forged.proposal,'check_b');
  assert.deepEqual(checkA.input_bindings,{});
  assert.deepEqual(checkB.input_bindings,{});
  assert.deepEqual(summary.input_bindings,{a:`/nodes/${checkA.id}/output/a`,b:`/nodes/${checkB.id}/output/b`});
});

test('WorkflowForge lowers converging choice branches to one shared semantic body',()=>{
  const {pack,resources}=sourceFixture(),sections=sourceSectionInventory(resources),ids=sections.map(item=>item.section_id);
  const semantic=blueprint({purpose:'Converge repeated fallback routes.',source_dispositions:dispositions(sections,['decide','deliver','unresolved']),activities:[
    activity('decide','Classify the outcome.',ids,{kind:'decision',produces:[{name:'outcome',shape:{kind:'enum',values:['pass','issues']}}]}),
    activity('deliver','Deliver the accepted result.',ids,{operation:'write',produces:[{name:'result',shape:'text'}]}),
    activity('unresolved','Report unresolved issues.',ids,{produces:[{name:'issues',shape:'text'}]}),
  ],choices:[{key:'root_choice',decision_activity:'decide',output:'outcome',branches:[{value:'pass',body:'deliver'},{value:'issues',body:'unresolved'}],default_body:'unresolved'}],root:'root_choice'});
  const forged=new WorkflowForge().compile({pack,resources,blueprint:semantic,context:{routing_rules:rules,routing_catalog:providers,providers,roles}});
  assert.equal(forged.compiled.validation.valid,true);
  const unresolved=activityNode(forged.proposal,'unresolved');assert(unresolved);
  assert.equal(forged.proposal.nodes.filter(node=>node.name==='unresolved').length,1);
  const condition=forged.proposal.nodes.find(node=>node.type==='condition');
  assert.equal(condition.cases.length,1);
  assert.equal(forged.proposal.edges.filter(edge=>edge.source===condition.id&&edge.target===unresolved.id).length,1);
});

test('WorkflowForge reuses an explicitly sequenced decision and downstream body without duplicate nodes or self edges',()=>{
  const {pack,resources}=sourceFixture(),sections=sourceSectionInventory(resources),ids=sections.map(item=>item.section_id);
  const semantic=blueprint({purpose:'Reuse semantic components across nested control groups.',source_dispositions:dispositions(sections,['decide','plan','deliver']),activities:[
    activity('decide','Determine whether optional planning applies.',ids,{kind:'decision',produces:[{name:'needed',shape:{kind:'boolean',values:[]}}]}),
    activity('plan','Create the implementation plan.',ids,{produces:[{name:'plan',shape:'text'}]}),
    activity('deliver','Deliver the result.',ids,{operation:'write',consumes:[{name:'plan',from:{activity:'plan',output:'plan'}}],produces:[{name:'result',shape:'text'}]}),
  ],choices:[{key:'planning_choice',decision_activity:'decide',output:'needed',branches:[{value:true,body:'plan'},{value:false,body:'plan'}],default_body:'plan'}],sequences:[
    {key:'preparation',members:['decide','planning_choice'],failure_meaning:'all_required'},
    {key:'delivery',members:['plan','deliver'],failure_meaning:'all_required'},
    {key:'root_sequence',members:['preparation','delivery'],failure_meaning:'all_required'},
  ],root:'root_sequence'});
  const forged=new WorkflowForge().compile({pack,resources,blueprint:semantic,context:{routing_rules:rules,routing_catalog:providers,providers,roles}});
  assert.equal(forged.compiled.validation.valid,true);
  assert.equal(forged.proposal.nodes.filter(node=>node.name==='decide').length,1);
  assert.equal(forged.proposal.nodes.filter(node=>node.name==='plan').length,1);
  assert.equal(forged.proposal.edges.some(edge=>edge.source===edge.target),false);
  const plan=activityNode(forged.proposal,'plan'),deliver=activityNode(forged.proposal,'deliver');
  assert.equal(deliver.input_bindings.plan,`/nodes/${plan.id}/output/plan`);
});

test('WorkflowForge accepts nested mutually exclusive choice exits without treating them as parallel fan-in',()=>{
  const {pack,resources}=sourceFixture(),sections=sourceSectionInventory(resources),ids=sections.map(item=>item.section_id);
  const semantic=blueprint({purpose:'Route nested exclusive outcomes.',source_dispositions:dispositions(sections,['mode','setup','assess','deliver','unresolved']),activities:[
    activity('mode','Choose setup or editing.',ids,{kind:'decision',produces:[{name:'mode',shape:{kind:'enum',values:['setup','editing']}}]}),
    activity('setup','Complete setup only.',ids,{operation:'write',produces:[{name:'setup',shape:'text'}]}),
    activity('assess','Assess editing outcome.',ids,{kind:'decision',produces:[{name:'outcome',shape:{kind:'enum',values:['pass','issues']}}]}),
    activity('deliver','Deliver the accepted edit.',ids,{operation:'write',produces:[{name:'result',shape:'text'}]}),
    activity('unresolved','Report unresolved edit issues.',ids,{produces:[{name:'issues',shape:'text'}]}),
  ],choices:[
    {key:'result_choice',decision_activity:'assess',output:'outcome',branches:[{value:'pass',body:'deliver'}],default_body:'unresolved'},
    {key:'mode_choice',decision_activity:'mode',output:'mode',branches:[{value:'editing',body:'result_choice'}],default_body:'setup'},
  ],root:'mode_choice'});
  const forged=new WorkflowForge().compile({pack,resources,blueprint:semantic,context:{routing_rules:rules,routing_catalog:providers,providers,roles}});
  assert.equal(forged.compiled.validation.valid,true);
  const exits=['deliver','setup','unresolved'].map(key=>`/nodes/${activityNode(forged.proposal,key).id}/output`).sort();
  assert.deepEqual(forged.compiled.workflow.nodes.find(node=>node.id==='final').input_bindings.upstream_result.coalesce.sort(),exits);
});

test('WorkflowForge discards model-authored semantic ordinals instead of cross-wiring Host requirement IDs',()=>{
  const {pack,resources}=sourceFixture(),sections=sourceSectionInventory(resources),ids=sections.map(item=>item.section_id);
  const semantic=blueprint({purpose:'Keep semantic rule ownership local.',source_dispositions:dispositions(sections,['work']),activities:[activity('work','Perform the work.',ids,{produces:[{name:'result',shape:'text'}]})],root:'work'});
  semantic.semantic_rules=[{section_id:ids[0],statement:'Preserve the source-defined rule.',activity_keys:['work'],applies_when:''}];
  semantic.requirement_assignments=[
    {requirement_id:'semantic_rule_001',activity_keys:['work'],binding_names:['result'],runtime_guards:['First redundant ordinal.']},
    {requirement_id:'semantic_rule_017',activity_keys:['work'],binding_names:['result'],runtime_guards:['Dangling redundant ordinal.']},
  ];
  const forged=new WorkflowForge().compile({pack,resources,blueprint:semantic,context:{routing_rules:rules,routing_catalog:providers,providers,roles}}),mapping=forged.proposal.requirement_mappings.find(item=>item.requirement_id==='semantic_rule_001');
  assert.equal(forged.compiled.validation.valid,true);
  assert.deepEqual(mapping.node_ids,[activityNode(forged.proposal,'work').id]);
  assert.deepEqual(mapping.binding_names,[]);
  assert.equal(forged.proposal.requirement_mappings.some(item=>item.requirement_id==='semantic_rule_017'),false);
});

test('WorkflowForge projects an observed approval to its unique gate and only post-gate operations',()=>{
  const compiled=compileWorkflowBrief({workflow_id:'approval-fixture',name:'Approval fixture',brief:'# Workflow\n\n## Process\n\nPropose a plan. Obtain user approval before implementation. Then implement the approved plan.',provider_id:'native-luna'}),prepared=prepareResources(compiled.resources),snapshot={workflow:compiled.workflow,resources:prepared.manifest,provenance:compiled.provenance,import_report:compiled.import_report},pack={...snapshot,revision_hash:revisionHash(snapshot)},resources=compiled.resources;
  const sections=sourceSectionInventory(resources),ids=sections.map(item=>item.section_id),approvalRequirement=observedSourceRequirements(resources).find(item=>item.requirement_kind==='approval');
  assert(approvalRequirement);
  const semantic=blueprint({purpose:'Require approval between proposal and implementation.',source_dispositions:dispositions(sections,['propose','approve','implement']),activities:[
    activity('propose','Propose the plan.',ids,{produces:[{name:'plan',shape:'text'}]}),
    activity('implement','Implement the approved plan.',ids,{operation:'write',consumes:[{name:'plan',from:{activity:'propose',output:'plan'}}],produces:[{name:'result',shape:'text'}]}),
  ],sequences:[{key:'root_sequence',members:['propose','approve','implement'],failure_meaning:'all_required'}],root:'root_sequence'});
  semantic.approvals=[{key:'approve',question:'Approve the plan before implementation?',source_sections:ids}];
  semantic.requirement_assignments=[{requirement_id:approvalRequirement.requirement_id,activity_keys:['propose','implement'],binding_names:['plan'],runtime_guards:[]}];
  const forged=new WorkflowForge().compile({pack,resources,blueprint:semantic,context:{routing_rules:rules,routing_catalog:providers,providers,roles}}),mapping=forged.proposal.requirement_mappings.find(item=>item.requirement_id===approvalRequirement.requirement_id),gate=forged.proposal.nodes.find(item=>item.type==='human_gate');
  assert.equal(forged.compiled.validation.valid,true);
  assert.deepEqual(mapping.node_ids.sort(),[gate.id,activityNode(forged.proposal,'implement').id].sort());
  assert.equal(mapping.node_ids.includes(activityNode(forged.proposal,'propose').id),false);
});

test('one observed approval rule maps every structurally matching gate',()=>{
  const compiled=compileWorkflowBrief({workflow_id:'approval-repeat-fixture',name:'Approval repeat fixture',brief:'# Workflow\n\n## Process\n\nPropose a plan. Obtain user approval before implementation. Then implement the approved plan.',provider_id:'native-luna'}),prepared=prepareResources(compiled.resources),snapshot={workflow:compiled.workflow,resources:prepared.manifest,provenance:compiled.provenance,import_report:compiled.import_report},pack={...snapshot,revision_hash:revisionHash(snapshot)},resources=compiled.resources;
  const sections=sourceSectionInventory(resources),ids=sections.map(item=>item.section_id),approvalRequirement=observedSourceRequirements(resources).find(item=>item.requirement_kind==='approval');
  assert(approvalRequirement);
  const semantic=blueprint({purpose:'Approve each protected implementation phase.',source_dispositions:dispositions(sections,['propose','approve_initial','implement_initial','approve_revision','implement_revision']),activities:[
    activity('propose','Propose the plan.',ids,{produces:[{name:'plan',shape:'text'}]}),
    activity('implement_initial','Implement the approved plan.',ids,{operation:'write',produces:[{name:'result',shape:'text'}]}),
    activity('implement_revision','Implement the approved revision.',ids,{operation:'write',produces:[{name:'revision',shape:'text'}]}),
  ],sequences:[{key:'root_sequence',members:['propose','approve_initial','implement_initial','approve_revision','implement_revision'],failure_meaning:'all_required'}],root:'root_sequence'});
  semantic.approvals=[{key:'approve_initial',question:'Approve initial plan?',source_sections:ids},{key:'approve_revision',question:'Approve revised plan?',source_sections:ids}];
  semantic.requirement_assignments=[{requirement_id:approvalRequirement.requirement_id,activity_keys:['propose','implement_initial','implement_revision'],binding_names:[],runtime_guards:[]}];
  const forged=new WorkflowForge().compile({pack,resources,blueprint:semantic,context:{routing_rules:rules,routing_catalog:providers,providers,roles}}),mapping=forged.proposal.requirement_mappings.find(item=>item.requirement_id===approvalRequirement.requirement_id);
  assert.equal(forged.compiled.validation.valid,true);
  assert.equal(mapping.node_ids.filter(id=>forged.proposal.nodes.find(node=>node.id===id)?.type==='human_gate').length,2);
});

test('WorkflowForge derives continuation only for a direct same-Provider isolated-worker successor',()=>{
  const {pack,resources}=sourceFixture(),sections=sourceSectionInventory(resources),ids=sections.map(item=>item.section_id);
  const semantic=blueprint({purpose:'Derive safe task lineage.',source_dispositions:dispositions(sections,['analyze','implement','finish']),activities:[
    activity('analyze','Analyze the task.',ids,{ownership:'isolated_worker',complexity:'complex',continues:'implement'}),
    activity('implement','Implement the task.',ids,{ownership:'isolated_worker',operation:'write',complexity:'complex'}),
    activity('finish','Finish routine output.',ids,{ownership:'isolated_worker',operation:'write'}),
  ],sequences:[{key:'root_sequence',members:['analyze','implement','finish'],failure_meaning:'all_required'}],root:'root_sequence'});
  const forged=new WorkflowForge().compile({pack,resources,blueprint:semantic,context:{routing_rules:rules,routing_catalog:providers,providers,roles}}),implementation=activityNode(forged.proposal,'implement'),finish=activityNode(forged.proposal,'finish'),analyze=activityNode(forged.proposal,'analyze');
  assert.equal(forged.compiled.validation.valid,true);
  assert.equal(implementation.thread_lifecycle,'continue');
  assert.equal(implementation.thread_source_node,analyze.id);
  assert.equal(finish.execution_target,'subagent');
  assert.equal(finish.thread_lifecycle,undefined);
  assert.equal(finish.thread_source_node,undefined);
});

test('WorkflowForge generates nested schemas from named semantic data types and binds source-mentioned pinned resources',()=>{
  const compiled=compileWorkflowBrief({workflow_id:'typed-fixture',name:'Typed fixture',brief:'# Workflow\n\n## Process\n\nInspect and use scripts/runner.py, then emit its exact evidence records.'});
  compiled.resources['source/scripts/runner.py']=Buffer.from('def run(): pass\n');
  const prepared=prepareResources(compiled.resources),snapshot={workflow:compiled.workflow,resources:prepared.manifest,provenance:compiled.provenance,import_report:compiled.import_report},pack={...snapshot,revision_hash:revisionHash(snapshot)},resources=compiled.resources,sections=sourceSectionInventory(resources),ids=sections.map(item=>item.section_id);
  const semantic=blueprint({purpose:'Preserve a typed runner interface.',source_dispositions:dispositions(sections,['run']),data_types:[
    {key:'assertion_record',kind:'object',fields:[{name:'kind',type_ref:'text',required:true},{name:'passed',type_ref:'boolean',required:true}],item_type_ref:'',values:[],openness:'closed'},
    {key:'assertion_records',kind:'list',fields:[],item_type_ref:'assertion_record',values:[],openness:'closed'},
    {key:'evidence',kind:'object',fields:[{name:'seed',type_ref:'integer',required:true},{name:'assertions',type_ref:'assertion_records',required:true}],item_type_ref:'',values:[],openness:'closed'},
  ],activities:[activity('run','Run the pinned interface.',ids,{operation:'write',produces:[{name:'evidence',shape:{kind:'object',values:[],type_ref:'evidence'}}]})],root:'run'});
  const forged=new WorkflowForge().compile({pack,resources,blueprint:semantic,context:{routing_rules:rules,routing_catalog:providers,providers,roles}}),node=activityNode(forged.proposal,'run');
  assert.equal(forged.compiled.validation.valid,true);
  assert.deepEqual(node.resource_refs,['source/WORKFLOW.md','source/scripts/runner.py']);
  assert.deepEqual(node.outputs_schema.properties.evidence,{type:'object',properties:{seed:{type:'integer'},assertions:{type:'array',items:{type:'object',properties:{kind:{type:'string'},passed:{type:'boolean'}},required:['kind','passed'],additionalProperties:false}}},required:['seed','assertions'],additionalProperties:false});
});

test('WorkflowForge keeps coarse response objects separate from executable file contracts',()=>{
  const compiled=compileWorkflowBrief({workflow_id:'coarse-interface',name:'Coarse interface',brief:'# Workflow\n\n## Process\n\nUse scripts/runner.py and return its result.'});
  compiled.resources['source/scripts/runner.py']=Buffer.from('def run(): pass\n');
  const prepared=prepareResources(compiled.resources),snapshot={workflow:compiled.workflow,resources:prepared.manifest,provenance:compiled.provenance,import_report:compiled.import_report},pack={...snapshot,revision_hash:revisionHash(snapshot)},resources=compiled.resources,sections=sourceSectionInventory(resources),ids=sections.map(item=>item.section_id);
  const semantic=blueprint({purpose:'Reject a missing runner interface.',source_dispositions:dispositions(sections,['run']),activities:[activity('run','Run the pinned interface.',ids,{operation:'write',produces:[{name:'result',shape:{kind:'object',values:[],type_ref:''}}]})],root:'run'});
  const forged=new WorkflowForge().compile({pack,resources,blueprint:semantic,context:{routing_rules:rules,routing_catalog:providers,providers,roles}}),node=activityNode(forged.proposal,'run');
  assert.deepEqual(node.outputs_schema.properties.result,{type:'object',additionalProperties:true});
  assert.equal(forged.compiled.validation.valid,true);
});

test('WorkflowForge canonicalizes JSON string field references without a model repair',()=>{
  const {pack,resources}=sourceFixture(),sections=sourceSectionInventory(resources),ids=sections.map(item=>item.section_id);
  const compact={contract:CURRENT_SEMANTIC_BLUEPRINT_CONTRACT,purpose:'Accept equivalent primitive spelling.',source_dispositions:sections.map(item=>({section_id:item.section_id,disposition:'workflow',activity_keys:['work'],note:'Required.'})),requirement_assignments:[],records:[{key:'report',fields:[{name:'summary',type:'string',required:true}],open:false}],lists:[],enums:[],activities:[{key:'work',instructions:'Produce the report.',profile:'main_read',source_sections:ids,inputs:[],outputs:[{name:'report',kind:'object',values:[],type_ref:'report',contract_ref:''}],tool:''}],approvals:[],sequences:[],parallels:[],choices:[]};
  const forged=new WorkflowForge().compile({pack,resources,blueprint:compact,context:{routing_rules:rules,routing_catalog:providers,providers,roles}}),node=activityNode(forged.proposal,'work');
  assert.equal(node.outputs_schema.properties.report.properties.summary.type,'string');
  assert.equal(forged.compiled.validation.valid,true);
});

test('WorkflowForge upgrades a persisted v2 blueprint without asking a model to rewrite its envelope',()=>{
  const {pack,resources}=sourceFixture(),sections=sourceSectionInventory(resources),ids=sections.map(item=>item.section_id),legacy=blueprint({purpose:'Replay legacy semantics.',source_dispositions:dispositions(sections,['work']),activities:[activity('work','Perform the work.',ids,{produces:[{name:'result',shape:'text'}]})],root:'work'});
  legacy.contract='workflow-semantic-blueprint/v2';delete legacy.data_types;for(const output of legacy.activities[0].produces)delete output.shape.type_ref;
  const forged=new WorkflowForge().compile({pack,resources,blueprint:legacy,context:{routing_rules:rules,routing_catalog:providers,providers,roles}});
  assert.equal(forged.compiled.validation.valid,true);
  assert.equal(activityNode(forged.proposal,'work').outputs_schema.properties.result.type,'string');
});

test('WorkflowForge keeps semantic keys separate from Host node IDs',()=>{
  const {pack,resources}=sourceFixture(),sections=sourceSectionInventory(resources),ids=sections.map(item=>item.section_id);
  const semantic=blueprint({purpose:'Allow source vocabulary that overlaps control nodes.',source_dispositions:dispositions(sections,['final']),activities:[activity('final','Produce the final source-defined result.',ids,{produces:[{name:'result',shape:'text'}]})],root:'final'});
  const forged=new WorkflowForge().compile({pack,resources,blueprint:semantic,context:{routing_rules:rules,routing_catalog:providers,providers,roles}});
  const generated=activityNode(forged.proposal,'final');
  assert.equal(generated.id,'activity_001');
  assert.notEqual(generated.id,'final');
  assert.equal(forged.compiled.workflow.nodes.filter(node=>node.id==='final').length,1);
  assert.equal(forged.compiled.validation.valid,true);
});

test('authoring retry policy never retries mechanical failures and permits three automatic semantic patches',()=>{
  for(const code of ['DATA_INVALID','STRICT_OUTPUT_JSON','GENERATION_PROPOSAL_CONTRACT','GENERATION_HOST_PROJECTION','AUTHORING_BLUEPRINT','AUTHORING_FORMAT','WORKFLOW_PACKAGE_INTEGRITY','EXPANSION_GRAPH_INVALID','ROUTING_CLASSIFICATION','EXPANSION_WRITE_PROVIDER','EXPANSION_THREAD_LIFECYCLE'])assert.equal(generationRetryClass({code}),'mechanical');
  for(const code of ['AUTHORING_SEMANTIC','GENERATION_REVIEW_FINDINGS','GENERATION_DETERMINISTIC_AUDIT','EXPANSION_SOURCE_DISPOSITIONS'])assert.equal(generationRetryClass({code}),'semantic');
  assert.equal(MAX_PLANNER_ATTEMPTS,4);
  assert.equal(isGenerationContractFailure({code:'AUTHORING_SEMANTIC'}),true);
  assert.equal(isGenerationContractFailure({code:'DATA_INVALID'}),true);
  assert.equal(isGenerationContractFailure({code:'ENOENT'}),false);
  const findings=deterministicProposalFindings({nodes:[{id:'work',type:'agent'}],requirement_mappings:[]},{workflow:{import_status:{requirement_coverage:[]}}},6,{});
  assert.equal(findings.mechanical.length,4);assert.deepEqual(findings.semantic,[]);
});

test('Skill conversion and from-scratch authoring are two configurations of the same strict authoring Workflow',()=>{
  assert.deepEqual(AUTHORING_WORKFLOWS.map(item=>item.id),['system.skill2workflow','system.build-workflow']);
  assert.equal(AUTHORING_WORKFLOWS[0].semantic_contract,AUTHORING_WORKFLOWS[1].semantic_contract);
  assert.equal(AUTHORING_WORKFLOWS[0].mechanical_repairs,0);
  assert.equal(AUTHORING_WORKFLOWS[0].semantic_repairs,3);
  const {pack,resources}=sourceFixture();
  assert.equal(pack.workflow.skill_policy.mode,'cooperative');
  assert.equal(authoringWorkflowForPack(pack).id,'system.build-workflow');
  assert.equal(authoringWorkflowForPack({...pack,provenance:{kind:'skill_import',source_kind:'skill'}}).id,'system.skill2workflow');
  const job=authoringRunPack(pack,resources,providers[1],'authoring-contract',rules,false,providers[2],providers);
  assert.equal(job.provenance.authoring_workflow_id,'system.build-workflow');
  assert.equal(job.workflow.nodes.find(node=>node.id==='expand').prompt_template,AUTHORING_PLANNER_PROMPT_V27);
  assert.equal(job.workflow.nodes.find(node=>node.id==='final').prompt_template,AUTHORING_REVIEW_PROMPT_V22);
  assert.doesNotMatch(AUTHORING_REVIEW_PROMPT_V15,/Only conversation_inputs.*may be not_applicable with an explanation/);
  assert.match(AUTHORING_REVIEW_PROMPT_V15,/artifact_interface_contract.*no matching typed requirement/s);
  assert.match(AUTHORING_REVIEW_PROMPT_V15,/a failing check cites only affected entities/);
  assert.match(AUTHORING_REVIEW_PROMPT_V15,/runtime placeholders/);
  assert.match(AUTHORING_REVIEW_PROMPT_V16,/Main model/);
  assert.match(AUTHORING_REVIEW_PROMPT_V16,/runtime output root/);
  assert.match(AUTHORING_REVIEW_PROMPT_V17,/approval-gated continuation/);
  assert.match(AUTHORING_REVIEW_PROMPT_V18,/every proposed semantic node and semantic edge/);
  assert.doesNotMatch(AUTHORING_REVIEW_PROMPT_V18,/every proposed node and edge/);
  assert.deepEqual(AUTHORING_WORKFLOWS[1].stages.map(({id})=>id),job.workflow.nodes.map(({id})=>id));
  assert.deepEqual(AUTHORING_WORKFLOWS[1].edges.map(({source,target})=>[source,target]),job.workflow.edges.map(({source,target})=>[source,target]));
  assert.deepEqual(AUTHORING_WORKFLOWS[1].pipeline.stages.map(({id})=>id),['start','expand','graph_assembly','execution_binding','deterministic_validation','final','end']);
  assert.deepEqual(AUTHORING_WORKFLOWS[1].pipeline.stages.filter(stage=>stage.owner==='host').map(({id})=>id),['start','graph_assembly','execution_binding','deterministic_validation']);
  assert.deepEqual(AUTHORING_WORKFLOWS[1].stages.map(stage=>[stage.id,stage.owner,stage.kind,stage.access??null]),[
    ['start','host','start',null],['expand','planner','agent','read_only'],['graph_assembly','host','tool','read_only'],
    ['execution_binding','host','tool','read_only'],['deterministic_validation','host','tool','read_only'],
    ['final','reviewer','agent','read_only'],['end','human','end',null],
  ]);
  for(const stage of job.workflow.nodes.filter(node=>node.type==='tool'))assert.match(stage.name,/^Verify Host /);
  assert.deepEqual(job.workflow.nodes.filter(node=>node.type==='tool').map(node=>node.executor.tool),['authoring-graph-assembly','authoring-execution-binding','authoring-deterministic-validation']);
  assert.equal(job.workflow.nodes.find(item=>item.id==='expand').outputs_schema,AUTHORING_RUNTIME_ENVELOPE_SCHEMA);
  assert(job.workflow.nodes.find(item=>item.id==='expand').resources.includes('analysis/request.txt'));
  assert(!job.workflow.nodes.find(item=>item.id==='expand').resources.includes('analysis/review-request.txt'));
  assert(job.workflow.nodes.find(item=>item.id==='final').resources.includes('analysis/review-request.txt'));
  assert(!job.workflow.nodes.find(item=>item.id==='final').resources.includes('analysis/request.txt'));
  assert.doesNotMatch(job.resources['analysis/request.txt'],/cross_resource_consistency/);
  assert.match(job.resources['analysis/request.txt'],/evidence\.resource is the literal source_span\.resource path/);
  assert.match(job.resources['analysis/request.txt'],/without the display-only N: line-number prefix/);
  assert.match(job.resources['analysis/request.txt'],/entrypoint are unavailable after deployment/);
  assert.match(job.resources['analysis/review-request.txt'],/cross_resource_consistency/);
  assert(!job.workflow.nodes.find(item=>item.id==='expand').resources.includes('source/WORKFLOW.md'));
  assert.doesNotThrow(()=>managedNativeResultSchema(job.workflow.nodes.find(item=>item.id==='expand')));
  assert.throws(()=>authoringRunPack(pack,resources,providers[1],'disabled-reviewer',rules,false,{...providers[2],enabled:false},providers),{code:'GENERATION_REVIEW_PROVIDER'});
});

test('authoring contract migration preserves supported user configuration while replacing Host-owned pipeline fields',async t=>{
  const root=await mkdtemp(join(tmpdir(),'workflow-authoring-migration-'));t.after(()=>rm(root,{recursive:true,force:true}));
  const store=await new WorkflowStore(root).initialize(),definition=AUTHORING_WORKFLOWS[0];
  store.validationContext={providers,roles,host_tools:['read_workflow_resource','authoring-graph-assembly','authoring-execution-binding','authoring-deterministic-validation'],tools:['read_workflow_resource','authoring-graph-assembly','authoring-execution-binding','authoring-deterministic-validation']};
  const legacy=createStoredAuthoringWorkflow(definition,{planner:providers[1],reviewer:providers[2],maxRounds:2});
  legacy.authoring.contract='codex-authoring-workflow/v2';delete legacy.authoring.pipeline;
  legacy.nodes=legacy.nodes.filter(node=>!['graph_assembly','execution_binding','deterministic_validation'].includes(node.id));
  legacy.edges=[{id:'start-expand',source:'start',target:'expand'},{id:'expand-final',source:'expand',target:'final'},{id:'final-end',source:'final',target:'end'}];
  legacy.host_tools=[];legacy.requirements.tools=['read_workflow_resource'];
  const planner=legacy.nodes.find(node=>node.id==='expand'),reviewer=legacy.nodes.find(node=>node.id==='final');
  planner.prompt_template='Custom planner policy retained across upgrades.';planner.approval.required=true;
  reviewer.prompt_template='Custom reviewer policy retained across upgrades.';reviewer.approval.required=true;
  await seedLegacyReady(store,legacy,{provenance:{kind:'bundled_authoring_workflow',authoring_workflow_id:definition.id,builtin_contract:'codex-authoring-workflow/v2'}});
  await ensureStoredAuthoringWorkflows(store,{providers,routingRules:rules});
  const migrated=await store.snapshot(definition.id),migratedPlanner=migrated.workflow.nodes.find(node=>node.id==='expand'),migratedReviewer=migrated.workflow.nodes.find(node=>node.id==='final');
  assert.equal(migrated.workflow.authoring.contract,'codex-authoring-workflow/v30');
  assert.equal(migrated.workflow.authoring.pipeline.contract,'codex-authoring-pipeline/v1');
  assert.equal(migrated.workflow.authoring.max_rounds,2);
  assert.equal(migratedPlanner.prompt_template,planner.prompt_template);assert.equal(migratedPlanner.approval.required,true);
  assert.equal(migratedReviewer.prompt_template,reviewer.prompt_template);assert.equal(migratedReviewer.approval.required,true);
  assert.deepEqual(migrated.provenance.migration,{kind:'bundled_authoring_contract',from_contract:'codex-authoring-workflow/v2',to_contract:'codex-authoring-workflow/v30'});
});

test('semantic fan-out requires an explicit write owner for declared shared changes',()=>{
  const {resources}=sourceFixture(),sections=sourceSectionInventory(resources),ids=sections.map(item=>item.section_id);
  const compact={contract:CURRENT_SEMANTIC_BLUEPRINT_CONTRACT,purpose:'Write isolated items and integrate shared changes.',source_dispositions:sections.map(item=>({section_id:item.section_id,disposition:'workflow',activity_keys:['write_items','integrate'],note:'Required.'})),requirement_assignments:[],runtime_dependencies:[],records:[{key:'result_record',fields:[{name:'changes',type:'text',required:true},{name:'shared_change',type:'text',required:true}],open:false}],lists:[],enums:[],activities:[
    {key:'write_items',instructions:'Write each assigned item.',profile:'worker_write',source_sections:ids,inputs:[{name:'items',from:'input:items'}],outputs:[{name:'results',kind:'list',values:[],type_ref:'result_record'}],tool:'',fanout:{input:'items',item_name:'item',result_output:'results',count_mode:'auto',fixed_count:0,batch_size:10,result_mode:'per_item',write_paths_field:'write_paths',shared_change_field:'shared_change'}},
    {key:'integrate',instructions:'Apply shared changes once.',profile:'main_write',source_sections:ids,inputs:[],outputs:[{name:'all_passed',kind:'boolean',values:[],type_ref:''}],tool:'',outcome:'validated_artifact',fail_on_false:['all_passed']},
  ],approvals:[],sequences:[{key:'flow',members:['write_items','integrate'],failure_meaning:'all_required'}],parallels:[],choices:[]};
  assert(collectSemanticBlueprintFindings(compact).some(item=>item.code==='fanout_shared_change_handoff'));
  compact.activities[1].inputs=[{name:'writer_results',from:'write_items.results'}];
  assert.equal(collectSemanticBlueprintFindings(compact).some(item=>item.code==='fanout_shared_change_handoff'),false);
  delete compact.activities[1].fail_on_false;
  assert(collectSemanticBlueprintFindings(compact).some(item=>item.code==='fanout_shared_change_completion'));
  compact.activities[1].fail_on_false=['all_passed'];
  delete compact.activities[0].fanout.write_paths_field;
  assert(collectSemanticBlueprintFindings(compact).some(item=>item.code==='fanout_shared_change_contract'));
});

test('build and skill2workflow fold only a guarded linear Main terminal into Host finalization',()=>{
  const source='# Workflow\n\n## Process\n\nImplement the change, verify its evidence, and document the checked result.';
  const skillText='---\nname: fold-fixture\ndescription: Fold fixture\n---\n'+source;
  const skillRoot=resolve(tmpdir(),'fold-fixture');
  const snapshot={metadata:{name:'fold-fixture',description:'Fold fixture'},source_path:join(skillRoot,'SKILL.md'),source_hash:digest(Buffer.from(skillText)),root:skillRoot,instructions_start_line:5,
    files:{'source/SKILL.md':Buffer.from(skillText)},inventory:[],problems:[],metadata_files:{}};
  const builds=[compileWorkflowBrief({workflow_id:'fold-build',name:'Fold build',brief:source,provider_id:'native-luna'}),compileCoarseSkill(snapshot,{id:'fold-skill',providerId:'native-luna'})];
  for(const build of builds){
    const resources=build.resources,prepared=prepareResources(resources),base={workflow:build.workflow,resources:prepared.manifest,provenance:build.provenance,import_report:build.import_report},pack={...base,revision_hash:revisionHash(base)};
    const sections=sourceSectionInventory(resources),ids=sections.map(item=>item.section_id);
    const blueprint={contract:CURRENT_SEMANTIC_BLUEPRINT_CONTRACT,purpose:'Implement, verify and document the result.',source_dispositions:sections.map(item=>({section_id:item.section_id,disposition:'workflow',activity_keys:['implement','validate','document'],note:'Required.'})),requirement_assignments:[],runtime_dependencies:[],records:[],lists:[],enums:[],activities:[
      {key:'implement',instructions:'Implement the change.',profile:'main_write',source_sections:ids,inputs:[],outputs:[{name:'changes',kind:'text',values:[],type_ref:''}],tool:'',outcome:'artifact'},
      {key:'validate',instructions:'Run the required checks and preserve the report.',profile:'main_write',source_sections:ids,inputs:[{name:'changes',from:'implement.changes'}],outputs:[{name:'passed',kind:'boolean',values:[],type_ref:''},{name:'report',kind:'text',values:[],type_ref:''}],tool:'',outcome:'validated_artifact',fail_on_false:['passed']},
      {key:'document',instructions:'Use the verification report to document the checked result and assess completion.',profile:'main_write',source_sections:ids,inputs:[{name:'report',from:'validate.report'}],outputs:[{name:'diff_check_passed',kind:'boolean',values:[],type_ref:''},{name:'completion_report',kind:'text',values:[],type_ref:''}],tool:'',outcome:'artifact',fail_on_false:['diff_check_passed']},
    ],approvals:[],sequences:[{key:'delivery',members:['implement','validate','document'],failure_meaning:'all_required'}],parallels:[],choices:[]};
    const forge=()=>new WorkflowForge().compile({pack,resources,blueprint,context:{routing_rules:rules,routing_catalog:providers,providers,roles}});
    const {proposal,compiled}=forge(),workflow=compiled.workflow,terminal=workflow.nodes.find(node=>node.name==='document'),validator=workflow.nodes.find(node=>node.name==='validate');
    assert.equal(compiled.validation.valid,true);
    assert.equal(workflow.finalization.node_id,terminal.id);
    assert(!workflow.nodes.some(node=>node.id==='final'));
    assert(workflow.edges.some(edge=>edge.source===terminal.id&&edge.target==='end'));
    assert.equal(terminal.input_bindings.report,`/nodes/${validator.id}/output/report`);
    assert.equal(terminal.input_bindings.task,'/inputs/task');
    assert.deepEqual(validator.completion_contract.fail_on_false,['passed']);
    assert.deepEqual(terminal.completion_contract.fail_on_false,['diff_check_passed']);
    assert.deepEqual(terminal.outputs_schema.required.sort(),['completion_report','diff_check_passed'].sort());
    const deployed=compileDeployableConversion({workflow,proposal,resources,pack,proposalHash:compiled.proposal_hash,reviewContractVersion:14});
    assert.equal(deployed.workflow.finalization.node_id,terminal.id);
    assert.match(deployed.workflow.nodes.find(node=>node.id===terminal.id).prompt_template,/Use the verification report/);
    assert(!deployed.workflow.nodes.some(node=>node.id==='final'));
    const noEvidence=structuredClone(blueprint);noEvidence.activities[2].inputs=[];
    const retained=new WorkflowForge().compile({pack,resources,blueprint:noEvidence,context:{routing_rules:rules,routing_catalog:providers,providers,roles}}).compiled.workflow;
    assert.equal(retained.finalization.node_id,'final');
    const noTerminalGuard=structuredClone(blueprint);delete noTerminalGuard.activities[2].fail_on_false;
    assert.equal(new WorkflowForge().compile({pack,resources,blueprint:noTerminalGuard,context:{routing_rules:rules,routing_catalog:providers,providers,roles}}).compiled.workflow.finalization.node_id,'final');
    const noValidationGuard=structuredClone(blueprint);delete noValidationGuard.activities[1].fail_on_false;
    assert.equal(new WorkflowForge().compile({pack,resources,blueprint:noValidationGuard,context:{routing_rules:rules,routing_catalog:providers,providers,roles}}).compiled.workflow.finalization.node_id,'final');
    const partialEvidence=structuredClone(blueprint);partialEvidence.activities[1].outputs.push({name:'check_log',kind:'text',values:[],type_ref:''});
    assert.equal(new WorkflowForge().compile({pack,resources,blueprint:partialEvidence,context:{routing_rules:rules,routing_catalog:providers,providers,roles}}).compiled.workflow.finalization.node_id,'final');
    const workerTerminal=structuredClone(blueprint);workerTerminal.activities[2].profile='worker_write';
    assert.equal(new WorkflowForge().compile({pack,resources,blueprint:workerTerminal,context:{routing_rules:rules,routing_catalog:providers,providers,roles}}).compiled.workflow.finalization.node_id,'final');
    const custom=structuredClone(pack);custom.workflow.nodes.find(node=>node.id==='final').prompt_template+=' Preserve my separate final duty.';
    const customResult=new WorkflowForge().compile({pack:custom,resources,blueprint,context:{routing_rules:rules,routing_catalog:providers,providers,roles}}).compiled.workflow;
    assert.equal(customResult.finalization.node_id,'final');
  }
});

test('v20 bundled authoring prompts upgrade to v27 while custom prompt extensions survive',async t=>{
  const root=await mkdtemp(join(tmpdir(),'workflow-authoring-v20-'));t.after(()=>rm(root,{recursive:true,force:true}));
  const store=await new WorkflowStore(root).initialize();
  store.validationContext={providers,roles,host_tools:['read_workflow_resource','authoring-graph-assembly','authoring-execution-binding','authoring-deterministic-validation'],tools:['read_workflow_resource','authoring-graph-assembly','authoring-execution-binding','authoring-deterministic-validation']};
  for(const [index,definition] of AUTHORING_WORKFLOWS.entries()){
    const previous=createStoredAuthoringWorkflow(definition,{planner:providers[1],reviewer:providers[2],maxRounds:2});
    previous.authoring.contract='codex-authoring-workflow/v20';
    previous.nodes.find(node=>node.id==='expand').prompt_template=index===0?AUTHORING_PLANNER_PROMPT_V20:`${AUTHORING_PLANNER_PROMPT_V20} Keep my custom policy.`;
    previous.nodes.find(node=>node.id==='final').prompt_template=AUTHORING_REVIEW_PROMPT_V18;
    await seedLegacyReady(store,previous,{provenance:{kind:'bundled_authoring_workflow',authoring_workflow_id:definition.id,builtin_contract:'codex-authoring-workflow/v20'}});
  }
  await ensureStoredAuthoringWorkflows(store,{providers,routingRules:rules});
  for(const [index,definition] of AUTHORING_WORKFLOWS.entries()){
    const migrated=await store.snapshot(definition.id),planner=migrated.workflow.nodes.find(node=>node.id==='expand'),reviewer=migrated.workflow.nodes.find(node=>node.id==='final');
    assert.equal(migrated.workflow.authoring.contract,'codex-authoring-workflow/v30');
    assert.equal(planner.prompt_template,index===0?AUTHORING_PLANNER_PROMPT_V27:`${AUTHORING_PLANNER_PROMPT_V27} Keep my custom policy.`);
    assert.equal(reviewer.prompt_template,AUTHORING_REVIEW_PROMPT_V22);
  }
});

test('v22 bundled authoring prompts adopt responsibility handoffs while configured approvals survive',async t=>{
  const root=await mkdtemp(join(tmpdir(),'workflow-authoring-v22-'));t.after(()=>rm(root,{recursive:true,force:true}));
  const store=await new WorkflowStore(root).initialize(),definition=AUTHORING_WORKFLOWS[0];
  store.validationContext={providers,roles,host_tools:['read_workflow_resource','authoring-graph-assembly','authoring-execution-binding','authoring-deterministic-validation'],tools:['read_workflow_resource','authoring-graph-assembly','authoring-execution-binding','authoring-deterministic-validation']};
  const previous=createStoredAuthoringWorkflow(definition,{planner:providers[1],reviewer:providers[2],maxRounds:2});
  previous.authoring.contract='codex-authoring-workflow/v22';
  previous.nodes.find(node=>node.id==='expand').prompt_template=AUTHORING_PLANNER_PROMPT_V22;
  previous.nodes.find(node=>node.id==='final').prompt_template=AUTHORING_REVIEW_PROMPT_V19;
  previous.nodes.find(node=>node.id==='expand').approval.required=true;
  await seedLegacyReady(store,previous,{provenance:{kind:'bundled_authoring_workflow',authoring_workflow_id:definition.id,builtin_contract:'codex-authoring-workflow/v22'}});
  await ensureStoredAuthoringWorkflows(store,{providers,routingRules:rules});
  const migrated=await store.snapshot(definition.id);
  assert.equal(migrated.workflow.authoring.contract,'codex-authoring-workflow/v30');
  assert.equal(migrated.workflow.nodes.find(node=>node.id==='expand').prompt_template,AUTHORING_PLANNER_PROMPT_V27);
  assert.equal(migrated.workflow.nodes.find(node=>node.id==='final').prompt_template,AUTHORING_REVIEW_PROMPT_V22);
  assert.equal(migrated.workflow.nodes.find(node=>node.id==='expand').approval.required,true);
});

test('v12 bundled authoring Workflows migrate the built-in reviewer prompt without losing configured slots',async t=>{
  const root=await mkdtemp(join(tmpdir(),'workflow-authoring-v12-'));t.after(()=>rm(root,{recursive:true,force:true}));
  const store=await new WorkflowStore(root).initialize(),definition=AUTHORING_WORKFLOWS[0];
  store.validationContext={providers,roles,host_tools:['read_workflow_resource','authoring-graph-assembly','authoring-execution-binding','authoring-deterministic-validation'],tools:['read_workflow_resource','authoring-graph-assembly','authoring-execution-binding','authoring-deterministic-validation']};
  const previous=createStoredAuthoringWorkflow(definition,{planner:providers[1],reviewer:providers[2],maxRounds:2});
  previous.authoring.contract='codex-authoring-workflow/v12';
  previous.nodes.find(node=>node.id==='final').prompt_template=AUTHORING_REVIEW_PROMPT_V12;
  previous.nodes.find(node=>node.id==='expand').approval.required=true;
  await seedLegacyReady(store,previous,{provenance:{kind:'bundled_authoring_workflow',authoring_workflow_id:definition.id,builtin_contract:'codex-authoring-workflow/v12'}});
  await ensureStoredAuthoringWorkflows(store,{providers,routingRules:rules});
  const migrated=await store.snapshot(definition.id);
  assert.equal(migrated.workflow.authoring.contract,'codex-authoring-workflow/v30');
  assert.equal(migrated.workflow.authoring.max_rounds,2);
  assert.equal(migrated.workflow.nodes.find(node=>node.id==='expand').approval.required,true);
  assert.equal(migrated.workflow.nodes.find(node=>node.id==='final').prompt_template,AUTHORING_REVIEW_PROMPT_V22);
});

test('v13 bundled authoring Workflows replace their built-in reviewer wording without changing user slots',async t=>{
  const root=await mkdtemp(join(tmpdir(),'workflow-authoring-v13-'));t.after(()=>rm(root,{recursive:true,force:true}));
  const store=await new WorkflowStore(root).initialize(),definition=AUTHORING_WORKFLOWS[0];
  store.validationContext={providers,roles,host_tools:['read_workflow_resource','authoring-graph-assembly','authoring-execution-binding','authoring-deterministic-validation'],tools:['read_workflow_resource','authoring-graph-assembly','authoring-execution-binding','authoring-deterministic-validation']};
  const previous=createStoredAuthoringWorkflow(definition,{planner:providers[1],reviewer:providers[2],maxRounds:2});
  previous.authoring.contract='codex-authoring-workflow/v13';
  previous.nodes.find(node=>node.id==='expand').prompt_template=AUTHORING_PLANNER_PROMPT;
  previous.nodes.find(node=>node.id==='final').prompt_template=AUTHORING_REVIEW_PROMPT_V13;
  previous.nodes.find(node=>node.id==='expand').approval.required=true;
  await seedLegacyReady(store,previous,{provenance:{kind:'bundled_authoring_workflow',authoring_workflow_id:definition.id,builtin_contract:'codex-authoring-workflow/v13'}});
  await ensureStoredAuthoringWorkflows(store,{providers,routingRules:rules});
  const migrated=await store.snapshot(definition.id);
  assert.equal(migrated.workflow.authoring.contract,'codex-authoring-workflow/v30');
  assert.equal(migrated.workflow.authoring.max_rounds,2);
  assert.equal(migrated.workflow.nodes.find(node=>node.id==='expand').approval.required,true);
  assert.equal(migrated.workflow.nodes.find(node=>node.id==='expand').prompt_template,AUTHORING_PLANNER_PROMPT_V27);
  assert.equal(migrated.workflow.nodes.find(node=>node.id==='final').prompt_template,AUTHORING_REVIEW_PROMPT_V22);
});

test('v14 bundled authoring Workflows update both built-in prompts without changing configured slots',async t=>{
  const root=await mkdtemp(join(tmpdir(),'workflow-authoring-v14-'));t.after(()=>rm(root,{recursive:true,force:true}));
  const store=await new WorkflowStore(root).initialize(),definition=AUTHORING_WORKFLOWS[0];
  store.validationContext={providers,roles,host_tools:['read_workflow_resource','authoring-graph-assembly','authoring-execution-binding','authoring-deterministic-validation'],tools:['read_workflow_resource','authoring-graph-assembly','authoring-execution-binding','authoring-deterministic-validation']};
  const previous=createStoredAuthoringWorkflow(definition,{planner:providers[1],reviewer:providers[2],maxRounds:2});
  previous.authoring.contract='codex-authoring-workflow/v14';
  previous.nodes.find(node=>node.id==='expand').prompt_template=AUTHORING_PLANNER_PROMPT_V14;
  previous.nodes.find(node=>node.id==='final').prompt_template=AUTHORING_REVIEW_PROMPT_V14;
  previous.nodes.find(node=>node.id==='expand').approval.required=true;
  await seedLegacyReady(store,previous,{provenance:{kind:'bundled_authoring_workflow',authoring_workflow_id:definition.id,builtin_contract:'codex-authoring-workflow/v14'}});
  await ensureStoredAuthoringWorkflows(store,{providers,routingRules:rules});
  const migrated=await store.snapshot(definition.id);
  assert.equal(migrated.workflow.authoring.contract,'codex-authoring-workflow/v30');
  assert.equal(migrated.workflow.authoring.max_rounds,2);
  assert.equal(migrated.workflow.nodes.find(node=>node.id==='expand').approval.required,true);
  assert.equal(migrated.workflow.nodes.find(node=>node.id==='expand').prompt_template,AUTHORING_PLANNER_PROMPT_V27);
  assert.equal(migrated.workflow.nodes.find(node=>node.id==='final').prompt_template,AUTHORING_REVIEW_PROMPT_V22);
});

test('v15 authoring reviewer migrates to the Run-bound Main and runtime-path contract',async t=>{
  const root=await mkdtemp(join(tmpdir(),'workflow-authoring-v15-'));t.after(()=>rm(root,{recursive:true,force:true}));
  const store=await new WorkflowStore(root).initialize(),definition=AUTHORING_WORKFLOWS[0];
  store.validationContext={providers,roles,host_tools:['read_workflow_resource','authoring-graph-assembly','authoring-execution-binding','authoring-deterministic-validation'],tools:['read_workflow_resource','authoring-graph-assembly','authoring-execution-binding','authoring-deterministic-validation']};
  const previous=createStoredAuthoringWorkflow(definition,{planner:providers[1],reviewer:providers[2],maxRounds:2});
  previous.authoring.contract='codex-authoring-workflow/v15';
  previous.nodes.find(node=>node.id==='final').prompt_template=AUTHORING_REVIEW_PROMPT_V15;
  await seedLegacyReady(store,previous,{provenance:{kind:'bundled_authoring_workflow',authoring_workflow_id:definition.id,builtin_contract:'codex-authoring-workflow/v15'}});
  await ensureStoredAuthoringWorkflows(store,{providers,routingRules:rules});
  const migrated=await store.snapshot(definition.id);
  assert.equal(migrated.workflow.authoring.contract,'codex-authoring-workflow/v30');
  assert.equal(migrated.workflow.authoring.max_rounds,2);
  assert.equal(migrated.workflow.nodes.find(node=>node.id==='expand').prompt_template,AUTHORING_PLANNER_PROMPT_V27);
  assert.equal(migrated.workflow.nodes.find(node=>node.id==='final').prompt_template,AUTHORING_REVIEW_PROMPT_V22);
});

test('v16 authoring reviewer migrates its built-in continuation guidance without changing configured slots',async t=>{
  const root=await mkdtemp(join(tmpdir(),'workflow-authoring-v16-'));t.after(()=>rm(root,{recursive:true,force:true}));
  const store=await new WorkflowStore(root).initialize(),definition=AUTHORING_WORKFLOWS[0];
  store.validationContext={providers,roles,host_tools:['read_workflow_resource','authoring-graph-assembly','authoring-execution-binding','authoring-deterministic-validation'],tools:['read_workflow_resource','authoring-graph-assembly','authoring-execution-binding','authoring-deterministic-validation']};
  const previous=createStoredAuthoringWorkflow(definition,{planner:providers[1],reviewer:providers[2],maxRounds:2});
  previous.authoring.contract='codex-authoring-workflow/v16';
  previous.nodes.find(node=>node.id==='final').prompt_template=AUTHORING_REVIEW_PROMPT_V16;
  previous.nodes.find(node=>node.id==='expand').approval.required=true;
  await seedLegacyReady(store,previous,{provenance:{kind:'bundled_authoring_workflow',authoring_workflow_id:definition.id,builtin_contract:'codex-authoring-workflow/v16'}});
  await ensureStoredAuthoringWorkflows(store,{providers,routingRules:rules});
  const migrated=await store.snapshot(definition.id);
  assert.equal(migrated.workflow.authoring.contract,'codex-authoring-workflow/v30');
  assert.equal(migrated.workflow.authoring.max_rounds,2);
  assert.equal(migrated.workflow.nodes.find(node=>node.id==='expand').approval.required,true);
  assert.equal(migrated.workflow.nodes.find(node=>node.id==='final').prompt_template,AUTHORING_REVIEW_PROMPT_V22);
});

test('v17 authoring reviewer migration aligns semantic-edge evidence with the Host checklist',async t=>{
  const root=await mkdtemp(join(tmpdir(),'workflow-authoring-v17-'));t.after(()=>rm(root,{recursive:true,force:true}));
  const store=await new WorkflowStore(root).initialize(),definition=AUTHORING_WORKFLOWS[0];
  store.validationContext={providers,roles,host_tools:['read_workflow_resource','authoring-graph-assembly','authoring-execution-binding','authoring-deterministic-validation'],tools:['read_workflow_resource','authoring-graph-assembly','authoring-execution-binding','authoring-deterministic-validation']};
  const previous=createStoredAuthoringWorkflow(definition,{planner:providers[1],reviewer:providers[2],maxRounds:2});
  previous.authoring.contract='codex-authoring-workflow/v17';
  previous.nodes.find(node=>node.id==='final').prompt_template=AUTHORING_REVIEW_PROMPT_V17;
  await seedLegacyReady(store,previous,{provenance:{kind:'bundled_authoring_workflow',authoring_workflow_id:definition.id,builtin_contract:'codex-authoring-workflow/v17'}});
  await ensureStoredAuthoringWorkflows(store,{providers,routingRules:rules});
  const migrated=await store.snapshot(definition.id);
  assert.equal(migrated.workflow.authoring.contract,'codex-authoring-workflow/v30');
  assert.equal(migrated.workflow.nodes.find(node=>node.id==='final').prompt_template,AUTHORING_REVIEW_PROMPT_V22);
});

test('portable Workflow package validates content identity and installs atomically',async t=>{
  const root=await mkdtemp(join(tmpdir(),'workflow-authoring-'));t.after(()=>rm(root,{recursive:true,force:true}));
  const source=new WorkflowStore(join(root,'source')).initialize(),target=new WorkflowStore(join(root,'target')).initialize();
  const [sourceStore,targetStore]=await Promise.all([source,target]);
  const compiled=compileWorkflowBrief({workflow_id:'portable-brief',name:'Portable brief',brief:'# Workflow\n\n## Process\n\nPerform the task.'});
  const resourcePath='workflow-assets/instructions.md',workflow=structuredClone(compiled.workflow);
  workflow.skill_policy={mode:'cooperative',implicit:'deny',ambient_allow:[],shadowed_skill_paths:[]};
  workflow.import_status.source_independent=true;
  workflow.requirements.executables=['git'];
  for(const node of workflow.nodes){node.resources=(node.resources??[]).map(()=>resourcePath);if(node.prompt_template)node.prompt_template=node.prompt_template.replaceAll('source/WORKFLOW.md',resourcePath);if(node.origin)node.origin={kind:'authored',reviewed:true};}
  const portable={workflow,resources:{[resourcePath]:compiled.resources['source/WORKFLOW.md']},provenance:{kind:'workflow_authored',compiler_version:1},import_report:null};
  const legacySaved=await sourceStore.create(portable.workflow,portable);
  assert.deepEqual(legacySaved.workflow.requirements.executables,['git']);
  const legacyResources=await sourceStore.resources(legacySaved.workflow.id,legacySaved.revision_hash);
  const obsoleteBundle=exportWorkflowPackage(legacySaved,legacyResources,{packageVersion:'1.2.3'});
  obsoleteBundle.dependencies.executables=['git'];
  const {package_sha256:_obsoleteHash,...obsoletePayload}=obsoleteBundle;
  obsoleteBundle.package_sha256=digest(canonicalJSON(obsoletePayload));
  assert.throws(()=>validateWorkflowPackage(obsoleteBundle),{code:'WORKFLOW_PACKAGE_DEPENDENCIES'});

  const executable={name:'python',version:'>=3.11,<4',python_modules:['yaml','requests']};
  const nextWorkflow={...legacySaved.workflow,requirements:{...legacySaved.workflow.requirements,executables:[executable]}};
  const saved=await sourceStore.save(legacySaved.workflow.id,nextWorkflow,{expected_revision:legacySaved.revision_hash});
  assert.deepEqual(saved.workflow.requirements.executables,[executable]);
  assert.deepEqual((await sourceStore.snapshot(legacySaved.workflow.id,legacySaved.revision_hash)).workflow.requirements.executables,['git']);
  const resources=await sourceStore.resources(saved.workflow.id,saved.revision_hash);
  const bundle=exportWorkflowPackage(saved,resources,{packageVersion:'1.2.3'});
  assert.equal(validateWorkflowPackage(bundle).package.version,'1.2.3');
  assert.deepEqual(bundle.compatibility,{plugin:'codex-agents-workflow',package_api:1,workflow_schema:1});
  assert.deepEqual(bundle.dependencies,{providers:[],tools:['read_workflow_resource'],mcp_servers:[],executables:[{name:'python',version:'>=3.11.0,<4.0.0',python_modules:['requests','yaml']}]});
  assert.deepEqual(bundle.snapshot.workflow.requirements.executables,[executable]);
  const installed=await installWorkflowPackage(targetStore,bundle,{source:'memory'});
  assert.equal(installed.workflow.id,'portable-brief');
  assert.deepEqual(installed.workflow.requirements.executables,[executable]);
  assert.equal(installed.revision_hash,saved.revision_hash);assert.equal(installed.installation.source,'memory');
  assert.equal((await targetStore.snapshot(installed.workflow.id)).revision_hash,saved.revision_hash);
  const tampered=structuredClone(bundle);tampered.objects[0].content_base64=Buffer.from('tampered').toString('base64');
  assert.throws(()=>validateWorkflowPackage(tampered),{code:'WORKFLOW_PACKAGE_INTEGRITY'});
  const incomplete=structuredClone(bundle),missing=incomplete.snapshot.workflow.nodes.flatMap(node=>node.resources ?? [])[0];
  incomplete.snapshot.workflow.status='ready';
  delete incomplete.snapshot.workflow.import_status.mode;
  incomplete.snapshot.provenance={kind:'portable_fixture'};
  incomplete.snapshot.resources=incomplete.snapshot.resources.filter(item=>item.path!==missing);
  incomplete.objects=incomplete.objects.filter(item=>item.path!==missing);
  incomplete.snapshot.revision_hash=revisionHash({workflow:incomplete.snapshot.workflow,resources:incomplete.snapshot.resources,provenance:incomplete.snapshot.provenance,import_report:incomplete.snapshot.import_report});
  const {package_sha256:_old,...payload}=incomplete;incomplete.package_sha256=digest(canonicalJSON(payload));
  assert.throws(()=>validateWorkflowPackage(incomplete),{code:'WORKFLOW_RESOURCE_MISSING'});
});


test('shared authoring compiler preserves explicit orchestration and worker context choices',()=>{
  const {pack,resources}=sourceFixture(),ids=sourceSectionInventory(resources).map(item=>item.section_id);
  const blueprint={contract:CURRENT_SEMANTIC_BLUEPRINT_CONTRACT,purpose:'Use existing conversation conclusions.',source_dispositions:ids.map(section_id=>({section_id,disposition:'workflow',activity_keys:['integrate','inspect'],note:'Required.'})),requirement_assignments:[],runtime_dependencies:[],records:[],lists:[],enums:[],activities:[
    {key:'integrate',instructions:'Apply the decisions already made in the initiating conversation.',profile:'orchestration_write',source_sections:ids,inputs:[],outputs:[{name:'result',kind:'text',values:[],type_ref:''}],tool:''},
    {key:'inspect',instructions:'Inspect the declared integration result.',profile:'main_read',source_sections:ids,inputs:[{name:'result',from:'integrate.result'}],outputs:[{name:'verdict',kind:'text',values:[],type_ref:''}],tool:''},
  ],approvals:[],sequences:[],parallels:[],choices:[]};
  validateData(blueprint,CURRENT_AUTHORING_SEMANTIC_BLUEPRINT_SCHEMA);
  const forged=new WorkflowForge().compile({pack,resources,blueprint,context:{routing_rules:rules,routing_catalog:providers,providers,roles}});
  const orchestration=forged.compiled.workflow.nodes.find(node=>node.origin?.semantic_key==='integrate');
  const worker=forged.compiled.workflow.nodes.find(node=>node.origin?.semantic_key==='inspect');
  assert.deepEqual(orchestration.executor,{kind:'main',mode:'orchestration'});
  assert.equal(forged.compiled.workflow.skill_policy.mode,'cooperative');
  assert.equal(worker.executor.kind,'main');assert.notEqual(worker.executor.mode,'orchestration');
  assert.equal(worker.input_bindings.result,`/nodes/${orchestration.id}/output/result`);
  const fixed=new WorkflowForge().compile({pack,resources,blueprint,context:{routing_rules:{...rules,selection_mode:'fixed'},routing_catalog:providers,providers,roles}});
  assert.deepEqual(fixed.compiled.workflow.nodes.find(node=>node.origin?.semantic_key==='integrate').executor,{kind:'main',mode:'orchestration'});
  assert.deepEqual(fixed.compiled.workflow.nodes.find(node=>node.origin?.semantic_key==='inspect').executor,{kind:'main',mode:'worker'});
});
