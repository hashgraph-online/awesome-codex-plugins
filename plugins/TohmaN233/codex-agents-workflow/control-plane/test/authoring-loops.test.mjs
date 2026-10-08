import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp,writeFile,rm } from 'node:fs/promises';
import { join } from 'node:path';
import { tmpdir } from './physical-tempdir.mjs';
import { compileWorkflowBrief } from '../lib/skill-import/workflow-authoring.mjs';
import { readSkillSnapshot } from '../lib/skill-import/skill-reader.mjs';
import { compileCoarseSkill } from '../lib/skill-import/coarse-compiler.mjs';
import { sourceSectionInventory } from '../lib/skill-import/source-dispositions.mjs';
import { prepareResources,revisionHash } from '../lib/workflow-revisions.mjs';
import { WorkflowForge,lowerSemanticBlueprint } from '../lib/authoring/workflow-forge.mjs';
import { applySemanticRepair,SEMANTIC_BLUEPRINT_CONTRACT,SEMANTIC_BLUEPRINT_SCHEMA,SEMANTIC_REPAIR_CONTRACT } from '../lib/authoring/blueprint-contract.mjs';
import { semanticLoopFindings,sourceRepairLoopIntentFindings } from '../lib/authoring/semantic-loops.mjs';
import { evaluateExpression } from '../lib/workflow-bindings.mjs';
import { validateData } from '../lib/workflow-data-schema.mjs';
import { deterministicProposalFindings } from '../lib/skill-import/proposal-validation.mjs';

const source='# Repair process\n\nImplement the requested artifacts.\n\nReview the artifacts independently. If review rejects an item, repair the failed item and review again until all items are accepted, with at most three rounds.';
const providers=['native-luna','native-sol','native-astra'].map(id=>({id,kind:'native_agent',enabled:true,capabilities:{read:true,write:true},config:{}}));
const rules={version:1,instructions:'Host routing',selection_mode:'automatic',routes:{implementation:{provider_id:'native-luna',role:'implementer'},complex_implementation:{provider_id:'native-sol',role:'implementer'},review:{provider_id:'native-sol',role:'reviewer'},planning:{provider_id:'native-astra',role:'implementer'}}};
const context={routing_rules:rules,routing_catalog:providers,providers,roles:[]};
function fixture(compiled){const snapshot={workflow:compiled.workflow,resources:prepareResources(compiled.resources).manifest,provenance:compiled.provenance,import_report:compiled.import_report};return {pack:{...snapshot,revision_hash:revisionHash(snapshot)},resources:compiled.resources};}
const fixtureFromBrief=brief=>fixture(compileWorkflowBrief({workflow_id:'loop-brief',name:'Loop brief',brief,provider_id:'native-luna'}));
const briefFixture=()=>fixtureFromBrief(source);
const shape=(name,kind,type_ref='')=>({name,kind,type_ref,values:[]});
function plan(resources,{items=false}={}){
  const sections=sourceSectionInventory(resources).map(item=>item.section_id);
  const activities=[{key:'repair',instructions:'Repair only defects in the supplied findings, preserving accepted work.',profile:'worker_write',source_sections:sections,inputs:items?[{name:'items',from:'loop:quality.repair_items'}]:[{name:'task',from:'input:task'},{name:'feedback',from:'loop:quality.feedback'}],outputs:[shape('completed','boolean')],tool:''},
    {key:'review',instructions:'Inspect the current artifacts independently and return new semantic findings in supplied item order.',profile:'review',source_sections:sections,inputs:items?[{name:'items',from:'loop:quality.review_items'}]:[{name:'completed',from:'repair.completed'}],outputs:items?[shape('verdicts','list','verdict_list')]:[shape('accepted','boolean'),shape('findings','text')],tool:''}];
  return {contract:SEMANTIC_BLUEPRINT_CONTRACT,purpose:'Repair artifacts under independent bounded review.',source_dispositions:sections.map(section_id=>({section_id,disposition:'workflow',activity_keys:['repair','review'],note:'Required process.'})),requirement_assignments:[],runtime_dependencies:[],records:items?[{key:'verdict',open:false,fields:[{name:'accepted',type:'boolean',required:true},{name:'findings',type:'text',required:true}]}]:[],lists:items?[{key:'verdict_list',item_type:'verdict'}]:[],enums:[],activities,approvals:[],sequences:[{key:'body',members:['repair','review'],failure_meaning:'all_required'}],parallels:[],choices:[],loops:[{key:'quality',entry_activity:'repair',exit_activity:'review',activity_keys:['repair','review'],max_rounds:3,until:items?{loop:'quality',output:'all_accepted'}:{activity:'review',output:'accepted'},feedback_inputs:items?[]:[{name:'findings',from:'review.findings'}],...(items?{item_scope:{items:'input:items',verdicts:'review.verdicts',paths_field:'paths',dependencies_field:'dependencies'}}:{})}]};
}

test('Build Workflow and Skill2Workflow deterministically compile equivalent real bounded loops',async()=>{
  const root=await mkdtemp(join(tmpdir(),'authoring-loops-'));
  try{
    await writeFile(join(root,'SKILL.md'),'---\nname: loop-fixture\ndescription: Bounded artifact repair\n---\n\n'+source);
    const skill=fixture(compileCoarseSkill(await readSkillSnapshot(join(root,'SKILL.md')),{id:'loop-skill',providerId:'native-luna'})),brief=briefFixture();
    const outputs=[brief,skill].map(fixture=>new WorkflowForge().compile({...fixture,blueprint:plan(fixture.resources),context}));
    assert.deepEqual(outputs[0].compiled.workflow.loops,outputs[1].compiled.workflow.loops);
    for(const [index,result] of outputs.entries()){
      assert.equal(result.compiled.validation.valid,true);
      const loop=result.compiled.workflow.loops[0];
      assert.equal(loop.id,'loop_001');assert.equal(loop.max_rounds,3);
      const review=result.compiled.workflow.nodes.find(node=>node.id===loop.exit_node);
      assert.equal(review.access,'read_only');assert.equal(review.executor.kind,'provider');assert.equal(review.executor.provider_id,'native-sol');
      assert.notEqual(result.compiled.workflow.finalization.node_id,loop.exit_node);
      assert.equal(result.proposal.nodes.find(node=>node.semantic_key==='repair').input_bindings.feedback,'/loops/loop_001/feedback');
      assert.equal(sourceRepairLoopIntentFindings(result.proposal,[brief,skill][index].resources).length,0);
    }
  }finally{await rm(root,{recursive:true,force:true});}
});

test('item loop compiles Host handoffs and first-round empty repair bypass',()=>{
  const fixture=briefFixture(),blueprint=plan(fixture.resources,{items:true});validateData(blueprint,SEMANTIC_BLUEPRINT_SCHEMA);
  const result=new WorkflowForge().compile({...fixture,blueprint,context}),loop=result.compiled.workflow.loops[0],entry=result.compiled.workflow.nodes.find(node=>node.id===loop.entry_node);
  assert.equal(entry.type,'condition');assert.equal(loop.item_scope.items,'/inputs/items');assert.equal(loop.item_scope.paths_field,'paths');
  assert.equal(loop.item_scope.dependencies_field,'dependencies');assert.equal(loop.until.args[0].path,'/loops/loop_001/all_accepted');
  assert.equal(evaluateExpression(entry.cases[0].when,{loops:{loop_001:{repair_items:[]}}}),false);
  assert.equal(evaluateExpression(entry.cases[0].when,{loops:{loop_001:{repair_items:[{paths:['out.txt'],findings:'Fix the defect.'}]}}}),true);
  const reviewer=result.proposal.nodes.find(node=>node.semantic_key==='review');assert.deepEqual(reviewer.input_bindings,{items:'/loops/loop_001/review_items'});
  assert.equal(result.compiled.workflow.inputs_schema.properties.items.type,'array');
  assert.equal(result.compiled.validation.valid,true);
});

test('semantic loop defects reject unsafe bounds, changed identities, write reviewers and broken regions',()=>{
  const fixture=briefFixture(),valid=plan(fixture.resources);
  for(const value of [0,-1,Infinity,Number.MAX_SAFE_INTEGER+1]){const bad=structuredClone(valid);bad.loops[0].max_rounds=value;assert.ok(semanticLoopFindings(bad).some(item=>item.code==='loop_bound'));}
  const large=structuredClone(valid);large.loops[0].max_rounds=100;assert.equal(semanticLoopFindings(large).length,0);
  assert.throws(()=>lowerSemanticBlueprint(fixture.pack,fixture.resources,large,context),error=>error.findings?.some(item=>item.code==='loop_source_bound'));
  for(const mutate of [b=>b.activities[1].profile='orchestration_read',b=>b.activities[1].fail_on_false=['accepted'],b=>b.loops[0].until.activity='repair',b=>b.loops[0].activity_keys=['repair'],b=>b.activities[0].inputs[1].from='loop:missing.feedback']){
    const bad=structuredClone(valid);mutate(bad);assert.throws(()=>lowerSemanticBlueprint(fixture.pack,fixture.resources,bad,context),error=>error.code==='AUTHORING_SEMANTIC');
  }
  const copied=structuredClone(valid);copied.activities[1].instructions='Copy the supplied item IDs into your findings.';
  assert.throws(()=>lowerSemanticBlueprint(fixture.pack,fixture.resources,copied,context),error=>error.findings?.some(item=>item.code==='agent_deterministic_transcription'));
});

test('local retry stays local and cannot satisfy explicit downstream semantic loop intent',()=>{
  const fixture=briefFixture(),blueprint=plan(fixture.resources);delete blueprint.loops;
  blueprint.activities[0].inputs=[{name:'task',from:'input:task'}];blueprint.activities[0].repeat_until={condition:'The local attempt succeeds.',max_attempts:2};
  assert.throws(()=>new WorkflowForge().compile({...fixture,blueprint,context}),error=>error.findings?.some(item=>item.code==='loop_source_missing'));
  const local=fixtureFromBrief('# Process\n\nImplement the artifact. If a local attempt fails, retry that node at most twice. Review once afterward.');
  const localPlan=plan(local.resources);delete localPlan.loops;localPlan.activities[0].inputs=[{name:'task',from:'input:task'}];localPlan.activities[0].repeat_until=blueprint.activities[0].repeat_until;
  const result=new WorkflowForge().compile({...local,blueprint:localPlan,context});
  assert.equal(result.compiled.workflow.loops?.length??0,0);assert.equal(result.proposal.nodes.find(node=>node.semantic_key==='repair').retry_max_attempts,2);
  assert.ok(deterministicProposalFindings(result.proposal,result.compiled,14,fixture.resources).semantic.some(item=>item.code==='loop_source_missing'));
  const simple={'source/WORKFLOW.md':Buffer.from('# Process\n\nImplement and review the artifacts once.')};assert.equal(sourceRepairLoopIntentFindings(result.proposal,simple).length,0);
  const localReview={'source/WORKFLOW.md':Buffer.from('# Process\n\nOne worker reviews and repairs its own artifact until its local checks pass.')};assert.equal(sourceRepairLoopIntentFindings(result.proposal,localReview).length,0);
  const unbounded={'source/WORKFLOW.md':Buffer.from('# Process\n\nAn independent reviewer inspects artifacts. Repair defects and review again until accepted, without a maximum.')};assert.ok(sourceRepairLoopIntentFindings(result.proposal,unbounded).some(item=>item.code==='loop_source_unbounded'));
});

test('targeted repair can add a loop linked to diagnosed semantic activities',()=>{
  const fixture=briefFixture(),blueprint=plan(fixture.resources),loop=blueprint.loops[0];delete blueprint.loops;
  const repaired=applySemanticRepair(blueprint,{contract:SEMANTIC_REPAIR_CONTRACT,purpose:'',upsert:{loops:[loop]},remove:{}},{targets:[{semantic_keys:['repair','review']}]});
  assert.deepEqual(repaired.loops,[loop]);assert.deepEqual(repaired.activities,blueprint.activities);
});

test('nested parent region includes the Host-generated child empty-repair control',()=>{
  const fixture=briefFixture(),blueprint=plan(fixture.resources,{items:true}),sections=blueprint.activities[0].source_sections;
  blueprint.activities.unshift({key:'prepare',instructions:'Prepare the initial artifact state.',profile:'worker_write',source_sections:sections,inputs:[{name:'task',from:'input:task'}],outputs:[shape('ready','boolean')],tool:''});
  blueprint.activities.push({key:'complete_review',instructions:'Independently inspect the integrated artifact and return acceptance.',profile:'review',source_sections:sections,inputs:[{name:'verdicts',from:'review.verdicts'}],outputs:[shape('accepted','boolean')],tool:''});
  blueprint.sequences[0].members=['prepare','repair','review','complete_review'];
  blueprint.loops.unshift({key:'overall',entry_activity:'prepare',exit_activity:'complete_review',activity_keys:['prepare','repair','review','complete_review'],max_rounds:3,until:{activity:'complete_review',output:'accepted'}});
  const result=new WorkflowForge().compile({...fixture,blueprint,context}),outer=result.compiled.workflow.loops.find(loop=>loop.id==='loop_001'),inner=result.compiled.workflow.loops.find(loop=>loop.id==='loop_002');
  assert.equal(result.compiled.validation.valid,true);assert.ok(outer.node_ids.includes(inner.entry_node));assert.ok(inner.node_ids.every(id=>outer.node_ids.includes(id)));
});

test('source loop gate defers negated, one-pass, uncertain and reference discussion clauses',()=>{
  const examples=[
    'Use an independent reviewer. Fix any findings once; do not repeat the review.',
    'Use an independent reviewer. Repair once and never review again.',
    'Use an independent reviewer. Repair once without repeating the review.',
    'Use an independent reviewer. Fix findings once. The documentation describes how to repeat the review.',
    'Use an independent reviewer. Fix findings once. You may review again if desired.',
    'Use an independent reviewer. Repair and review again is not required.',
    'Use an independent reviewer. Repeat the review for style feedback. Repair the deployment configuration once.',
    'Use an independent reviewer. Fix the deployment configuration once. Review the style samples again.',
    'Use an independent reviewer. The label is "repair defects and review again". Fix the artifacts once.',
    '使用独立审核员。只修复一次；不要重复审核。',
    '使用独立审核员。修复发现的问题一次，无需再次审核。',
    '使用独立审核员。修复一次，不重复审查。',
    '使用独立审核员。可以考虑修复后重新审核。',
    '使用独立审核员。修复后重新审核不是必须的。',
    '使用独立审核员。修复一次。参考文档提到修复后重新审核。',
    '使用独立审核员。修复部署配置一次。对样例重新审核。',
    '使用独立审核员。示例标签是“修复后重新审核”。仅执行一次。',
  ];
  for(const example of examples){
    const fixture=fixtureFromBrief(`# Process\n\n${example}`),blueprint=plan(fixture.resources);delete blueprint.loops;blueprint.activities[0].inputs=[{name:'task',from:'input:task'}];
    assert.doesNotThrow(()=>new WorkflowForge().compile({...fixture,blueprint,context}),example);
  }
  for(const example of [
    'Use an independent reviewer. If review rejects the artifact, repair its defects and review again, with at most three rounds.',
    'Use an independent reviewer. Repair the findings; then repeat the review, with at most three rounds.',
    '使用独立审核员。若审核不通过，修复问题后重新审核，最多3轮。',
    '使用独立审核员。修复问题；再次审核，最多3轮。',
  ]){
    const resources={'source/WORKFLOW.md':Buffer.from(`# Process\n\n${example}`)};
    assert.ok(sourceRepairLoopIntentFindings({nodes:[],loops:[]},resources).some(item=>item.code==='loop_source_missing'),example);
  }
});
