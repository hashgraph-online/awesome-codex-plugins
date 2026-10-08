import test from 'node:test';
import assert from 'node:assert/strict';
import { REVIEW_IDS, evaluateReview, reviewIds, reviewSchema } from '../lib/skill-import/review-checklist.mjs';
import { CONVERSION_CONTRACT, HOST_OWNED_REVIEW_IDS, PLANNER_CONVERSION_CONTRACT } from '../lib/skill-import/conversion-contract.mjs';
import { validateRepairTargets } from '../lib/skill-import/generation-repair.mjs';
import { projectObservedRequirements } from '../lib/skill-import/source-requirements.mjs';

const proposal={source_requirements:[{requirement_id:'approval_2',requirement_kind:'approval',source_spans:[{resource:'source/SKILL.md',start_line:2,end_line:2}],trigger:'before completion',required_result:'approved'}],requirement_mappings:[{requirement_id:'approval_2',node_ids:['work','confirm'],status:'compiled'}],source_dispositions:[{section_id:'section_01_overview',disposition:'workflow',node_ids:['work','confirm'],requirement_ids:['approval_2'],rationale:'The entrypoint defines the work and confirmation boundary.'}],nodes:[{id:'work',type:'agent',requirement_ids:['approval_2']},{id:'confirm',type:'human_gate',requirement_ids:['approval_2']}],edges:[{id:'work-confirm'}]};
const resources={'source/SKILL.md':Buffer.from('Perform work.\nConfirm it.')};
const result=(ids=REVIEW_IDS)=>({checks:ids.map(()=>({status:'pass',evidence:'The source duties are preserved in the work and confirmation boundary.'}))});
const rowFor=(value,id,ids=REVIEW_IDS)=>value.checks[ids.indexOf(id)];
const legacyResult=(ids=reviewIds(13))=>({checks:ids.map(id=>({id,status:'pass',evidence:'The cited source is preserved in work and its confirmation.',node_ids:['work','confirm'],edge_ids:['work-confirm'],source_spans:[{resource:'source/SKILL.md',start_line:1,end_line:2}]}))});
const evaluateLegacy=(value,current=proposal,source=resources)=>evaluateReview(value,current,source,{version:13});

test('planner responsibilities cover exactly the reviewer checks the planner can change',()=>{
  const assigned=[...new Set(PLANNER_CONVERSION_CONTRACT.responsibility_check_ids.flat())].sort();
  assert.deepEqual(assigned,REVIEW_IDS.filter(id=>!HOST_OWNED_REVIEW_IDS.includes(id)).sort());
  assert.equal(PLANNER_CONVERSION_CONTRACT.responsibility_check_ids.length,PLANNER_CONVERSION_CONTRACT.responsibilities.length);
});

test('Host-owned review checks do not ask for a planner semantic repair',()=>{
  for(const check of CONVERSION_CONTRACT.checks.filter(item=>HOST_OWNED_REVIEW_IDS.includes(item.id)))
    assert.match(check.requirement,/^Host:/,check.id);
});

test('current review schema exposes no Host-owned identity fields to the reviewer',()=>{
  const item=reviewSchema().properties.checks.items;
  assert.deepEqual(item.required,['status','evidence']);
  assert.deepEqual(Object.keys(item.properties),['status','evidence']);
  assert.equal(item.additionalProperties,false);
});

test('verdict is computed from complete checks rather than a model approval flag',()=>{
  assert.equal(evaluateReview(result(),proposal,resources).approved,true);
  const failed=result();failed.checks[0].status='fail';failed.checks[0].evidence='Separate independent inputs before synthesis.';
  const verdict=evaluateReview(failed,proposal,resources);assert.equal(verdict.approved,false);assert.match(verdict.findings[0],/^\[parallelism\]/);
  assert.throws(()=>evaluateReview({...result(),approved:true},proposal,resources),{code:'GENERATION_CHECKLIST_INVALID'});
});

test('current ordered review rejects missing, extra, malformed, and copied identity fields',()=>{
  for(const mutate of [
    r=>r.checks.pop(),
    r=>r.checks[0].id='parallelism',
    r=>r.checks[0].node_ids=['work'],
    r=>r.checks[0].evidence=' ',
    r=>r.checks[0].status='unknown',
    r=>rowFor(r,'human_confirmation').status='not_applicable',
  ]){const value=result();mutate(value);assert.throws(()=>evaluateReview(value,proposal,resources),{code:'GENERATION_CHECKLIST_INVALID'});}
});

test('legacy review replay still validates copied identity evidence under its pinned contract',()=>{
  for(const mutate of [
    r=>r.checks[1].id=r.checks[0].id,r=>r.checks[0].id='invented',
    r=>r.checks[0].node_ids=['nonexistent'],r=>r.checks[0].edge_ids=['nonexistent'],
    r=>r.checks[0].source_spans[0].end_line=100,r=>r.checks[0].source_spans[0].resource='missing',
  ]){const value=legacyResult();mutate(value);assert.throws(()=>evaluateLegacy(value),{code:'GENERATION_CHECKLIST_INVALID'});}
});

test('not-applicable requires an allowed rule and still retains its explanation',()=>{
  const value=result();rowFor(value,'conditional_dependencies').status='not_applicable';
  assert.equal(evaluateReview(value,proposal,resources).approved,true);
  rowFor(value,'model_selection').status='not_applicable';
  assert.throws(()=>evaluateReview(value,proposal,resources),{code:'GENERATION_CHECKLIST_INVALID'});
});

test('a failing source-support check may cite only the affected graph entities',()=>{
  const review=result(),row=rowFor(review,'source_support');
  row.status='fail';row.evidence='The work node has an unrelated projected source span.';
  const verdict=evaluateReview(review,proposal,resources);
  assert.equal(verdict.approved,false);
  assert.deepEqual(verdict.host_repair_targets[0].check_ids,['source_support']);
});

test('source support covers semantic edges but not Host entry and finalization edges',()=>{
  const current=structuredClone(proposal);
  current.edges=[
    {id:'host-entry',source:'start',target:'work'},
    {id:'work-confirm',source:'work',target:'confirm'},
    {id:'host-exit',source:'confirm',target:'final'},
  ];
  const verdict=evaluateReview(result(),current,resources);
  assert.equal(verdict.approved,true);
  const sourceSupport=verdict.checks.find(row=>row.id==='source_support');
  assert.deepEqual(sourceSupport.node_ids,['work','confirm']);
  assert.deepEqual(sourceSupport.edge_ids,['host-entry','work-confirm','host-exit']);
});

test('an observed artifact schema makes interface review applicable without an artifact path',()=>{
  const current=structuredClone(proposal);
  current.source_requirements.push({requirement_id:'schema_1',requirement_kind:'artifact_schema',source_spans:[{resource:'source/SKILL.md',start_line:1,end_line:1}],trigger:'produce_or_validate_interface',required_result:'Preserve exact fields.'});
  current.requirement_mappings.push({requirement_id:'schema_1',node_ids:['work'],status:'agent_assisted'});
  const review=result();rowFor(review,'artifact_interface_contract').status='not_applicable';
  assert.throws(()=>evaluateReview(review,current,resources),{code:'GENERATION_CHECKLIST_INVALID'});
});

test('legacy reviewer edge shorthand is canonicalized only when it identifies an exact Host edge',()=>{
  const current=structuredClone(proposal);current.edges=[{id:'edge_001',source:'work',target:'confirm'}];
  const review=legacyResult();for(const row of review.checks)row.edge_ids=['e001'];
  assert.equal(evaluateLegacy(review,current,resources).approved,true);
  review.checks[0].edge_ids=['e999'];
  assert.throws(()=>evaluateLegacy(review,current,resources),{code:'GENERATION_CHECKLIST_INVALID'});
});

test('human intervention is not applicable when the source declares no approval',()=>{
  const noApproval={...proposal,source_requirements:[],requirement_mappings:[]};
  const plainResources={'source/SKILL.md':Buffer.from('Perform work.\nArchive result.')};
  const value=result();
  const row=rowFor(value,'human_intervention');
  row.status='not_applicable';row.evidence='The source declares no human approval gate.';
  assert.doesNotThrow(()=>evaluateReview(value,noApproval,plainResources));
  assert.throws(()=>evaluateReview(value,proposal,resources),{code:'GENERATION_CHECKLIST_INVALID'});
});

test('review failures on the same semantic entity become one field-bounded repair target',()=>{
  const current=structuredClone(proposal);current.nodes[0].semantic_key='produce_scenario';current.nodes[1].semantic_key='approve_scenario';
  const review=result();
  for(const id of ['artifact_interface_contract','validation_strength']){const row=rowFor(review,id);row.status='fail';row.evidence=id==='artifact_interface_contract'?'Select the exact scenario artifact contract.':'The scenario schema must retain its required nonempty arrays.';}
  const verdict=evaluateReview(review,current,resources);
  assert.equal(verdict.semantic_repair_targets.length,1);
  assert.deepEqual(verdict.semantic_repair_targets[0].check_ids,['artifact_interface_contract','validation_strength']);
  assert(verdict.semantic_repair_targets[0].affected_semantic_fields.includes('activities.outputs.contract_ref'));
  assert.deepEqual(verdict.semantic_repair_targets[0].semantic_keys,['approve_scenario','produce_scenario']);
});

test('mixed checklist complaints about Host projection fields never become planner repairs',()=>{
  const review=result();
  for(const id of ['artifact_interface_contract','validation_strength']){
    const row=rowFor(review,id);
    row.status='fail';row.evidence='The Host-projected required_artifacts array is empty for this node.';
  }
  const verdict=evaluateReview(review,proposal,resources);
  assert.equal(verdict.semantic_repair_targets.length,0);
  assert.equal(verdict.host_repair_targets.length,1);
  assert.deepEqual(verdict.host_repair_targets[0].check_ids,['artifact_interface_contract','validation_strength']);
});

test('a semantic validation failure stays with the planner when it explicitly excludes a Host field',()=>{
  const review=result(),row=rowFor(review,'validation_strength');
  row.status='fail';
  row.evidence='The producer lacks an artifact-success boolean and fail_on_false before consumers; this is not Host required_artifacts.';
  const verdict=evaluateReview(review,proposal,resources);
  assert.equal(verdict.host_repair_targets.length,0);
  assert.equal(verdict.semantic_repair_targets.length,1);
  assert.deepEqual(verdict.semantic_repair_targets[0].check_ids,['validation_strength']);
});

test('legacy semantic repair targets cited producers rather than contextual downstream edges',()=>{
  const current=structuredClone(proposal);current.nodes[0].semantic_key='producer';current.nodes[1].semantic_key='consumer';
  const review=legacyResult(),row=review.checks.find(item=>item.id==='validation_strength');
  row.status='fail';row.evidence='work must validate its artifact before downstream consumption; add a boolean guard to work.';
  row.node_ids=['work','confirm'];row.edge_ids=['work-confirm'];
  const verdict=evaluateLegacy(review,current,resources);
  assert.deepEqual(verdict.semantic_repair_targets[0].semantic_keys,['producer']);
});

test('legacy edge-only semantic findings map to both endpoint keys and an editable relation field',()=>{
  const current=structuredClone(proposal);current.nodes[0].semantic_key='produce_scenario';current.nodes[1].semantic_key='approve_scenario';current.edges[0]={...current.edges[0],source:'work',target:'confirm'};
  const review=legacyResult(),row=review.checks.find(item=>item.id==='phase_order');row.status='fail';row.evidence='The approval relation is ordered before its evidence.';row.node_ids=[];row.edge_ids=['work-confirm'];
  const verdict=evaluateLegacy(review,current,resources),target=verdict.semantic_repair_targets[0];
  assert.deepEqual(target.semantic_keys,['approve_scenario','produce_scenario']);assert(target.affected_semantic_fields.includes('activities.inputs'));
});

test('an identity-free semantic failure uses Host-bound graph scope',()=>{
  const review=result(),row=rowFor(review,'hard_rules');
  row.status='fail';row.evidence='Add the missing source-required validation activity.';
  const verdict=evaluateReview(review,proposal,resources),target=verdict.semantic_repair_targets[0];
  assert.deepEqual(target.semantic_keys,['confirm','work']);
  assert(target.affected_semantic_fields.includes('activities.instructions'));
});

test('source-disposition feedback keeps the cited section key even when graph nodes are named',()=>{
  const current=structuredClone(proposal);current.nodes[0].semantic_key='produce_result';
  const review=result(),row=rowFor(review,'source_disposition');
  row.status='fail';row.evidence='This section includes an unconditional step, so its conditional disposition is too narrow.';
  const target=evaluateReview(review,current,resources).semantic_repair_targets[0];
  assert(target.semantic_keys.includes('section_01_overview'));
  assert(target.semantic_keys.includes('produce_result'));
});

test('requirement-coverage feedback keeps a typed requirement inside a broader cited span',()=>{
  const current=structuredClone(proposal);current.nodes[0].semantic_key='produce_result';
  const review=result(),row=rowFor(review,'requirement_coverage');
  row.status='fail';row.evidence='The approval requirement lacks the necessary producer mapping.';
  const target=evaluateReview(review,current,resources).semantic_repair_targets[0];
  assert(target.semantic_keys.includes('approval_2'));
});

test('review honors reconciled Host-observed dependencies and targets a genuinely unmapped one once',()=>{
  // Reduced from authoring-2b6afd29: the source observation and the typed
  // runtime dependency cite the same four command lines. The typed declaration
  // owns module/version refinements; the coarse Host observation must not be
  // resurrected after proposal projection.
  const lines=['# Skill','## Implementation Loop','Run codegraph explore to inspect the repository.','Run python -m pytest tests/test_cards.py -q.','Run node --check app.js.','Run git diff --check.'];
  const source={'source/SKILL.md':Buffer.from(lines.join('\n'))};
  const names=['codegraph','python','node','git'];
  const declared=names.map((name,index)=>({requirement_id:`authoring_dependency_${name}`,requirement_kind:'dependency',source_spans:[{resource:'source/SKILL.md',start_line:index+3,end_line:index+3}],trigger:'unconditional_source_dependency',required_result:`Prepare ${name}.`,resource_refs:['source/SKILL.md'],details:{executable:name,phase:'unconditional',source_quote:lines[index+2].slice(4),...(name==='python'?{python_modules:['pytest']}:{})}}));
  const current={...structuredClone(proposal),source_requirements:declared,requirement_mappings:declared.map(item=>({requirement_id:item.requirement_id,node_ids:['work'],binding_names:[],runtime_guards:[],resource_refs:['source/SKILL.md'],status:'compiled',rationale:'Host prepares this declared runtime dependency.'})),source_dispositions:[{section_id:'section_01_implementation_loop',disposition:'workflow',node_ids:['work'],requirement_ids:declared.map(item=>item.requirement_id),rationale:'The implementation loop requires these tools.'}],nodes:[{id:'work',type:'agent',requirement_ids:declared.map(item=>item.requirement_id)},{id:'confirm',type:'human_gate',requirement_ids:[]}]};
  const projected=projectObservedRequirements(current,source);
  assert.equal(projected.source_requirements.filter(item=>item.requirement_kind==='dependency').length,4);
  assert(projected.source_requirements.every(item=>!item.requirement_id.startsWith('observed_dependency_')));
  for(const candidate of [current,projected]){
    const verdict=evaluateReview(result(),candidate,source);
    assert.equal(verdict.approved,true,verdict.findings.join('\n'));
    assert.equal(verdict.semantic_repair_targets.length,0);
  }

  const missing=structuredClone(current);
  missing.source_requirements.pop();missing.requirement_mappings.pop();missing.source_dispositions[0].requirement_ids.pop();
  const canonicalMissing=projectObservedRequirements(missing,source);
  const verdict=evaluateReview(result(),canonicalMissing,source);
  const finding='[requirement_coverage] observed_dependency_6_1 has no mapping.';
  assert.equal(verdict.findings.filter(item=>item===finding).length,1);
  const target=verdict.semantic_repair_targets.find(item=>item.evidence.includes(finding));
  assert.deepEqual(target.semantic_keys,['observed_dependency_6_1']);
  assert.deepEqual(target.source_spans,[{resource:'source/SKILL.md',start_line:6,end_line:6}]);
  assert.equal(validateRepairTargets({activities:[{key:'work'}]}, {findings:[target]}, {canonicalProposal:canonicalMissing}).valid,true);
});

test('repair target validation stops unlocalized semantic feedback before another planner call',()=>{
  const plan={activities:[{key:'produce_scenario'}],approvals:[],sequences:[],parallels:[],choices:[],source_dispositions:[],requirement_assignments:[],records:[],lists:[],enums:[]};
  assert.equal(validateRepairTargets(plan,{findings:[{semantic_keys:[],affected_semantic_fields:['activities.instructions']}]}).valid,false);
  assert.equal(validateRepairTargets(plan,{findings:[{semantic_keys:['missing'],affected_semantic_fields:['activities.instructions']}]}).valid,false);
  assert.equal(validateRepairTargets(plan,{findings:[{semantic_keys:['produce_scenario'],affected_semantic_fields:['activities.instructions']}]}).valid,true);
});

test('Host-owned review failures remain blockers without becoming planner repair work',()=>{
  const failed=result();
  rowFor(failed,'model_selection').status='fail';
  rowFor(failed,'model_selection').evidence='The pinned Host route does not satisfy the required capability.';
  rowFor(failed,'hard_rules').status='fail';
  rowFor(failed,'hard_rules').evidence='The work activity omits a required source rule.';
  const verdict=evaluateReview(failed,proposal,resources);
  assert.equal(verdict.approved,false);
  assert.deepEqual(verdict.host_findings,['[model_selection] The pinned Host route does not satisfy the required capability.']);
  assert.deepEqual(verdict.semantic_findings,['[hard_rules] The work activity omits a required source rule.']);
});

test('persisted v2, v3, and v4 review contracts retain their pinned checklist shape',()=>{
  for(const version of [2,3,4]) { const ids=reviewIds(version); const value={checks:ids.map(id=>({id,status:'pass',evidence:'Pinned legacy review.',node_ids:['work','confirm'],edge_ids:['work-confirm'],source_spans:[{resource:'source/SKILL.md',start_line:1,end_line:2}]}))}; assert.equal(evaluateReview(value,proposal,resources,{version}).approved,true); assert.equal(reviewSchema(version).properties.checks.minItems,ids.length); }
});

test('v4 all-pass model review cannot approve an explicitly unsupported requirement',()=>{
  const unsupported=structuredClone(proposal);unsupported.requirement_mappings[0].status='unsupported';
  const ids=reviewIds(4); const review={checks:ids.map(id=>({id,status:'pass',evidence:'Pinned v4 review.',node_ids:['work','confirm'],edge_ids:['work-confirm'],source_spans:[{resource:'source/SKILL.md',start_line:1,end_line:2}]}))};
  const verdict=evaluateReview(review,unsupported,resources,{version:4});
  assert.equal(verdict.approved,false);assert(verdict.findings.some(finding=>finding.includes('remains unsupported')));
});

test('v5 replay remains pinned and does not receive current host projection',()=>{
  const current=structuredClone(proposal);
  current.source_requirements.push({requirement_id:'canonical_time',requirement_kind:'canonicalization',source_spans:[{resource:'source/SKILL.md',start_line:1,end_line:1}],trigger:'before final validation',required_result:'whole-second UTC'});
  current.requirement_mappings.push({requirement_id:'canonical_time',node_ids:['work'],status:'compiled'});
  current.nodes[0].requirement_ids.push('canonical_time');
  const verdict=evaluateReview(legacyResult(reviewIds(5)),current,resources,{version:5});
  assert.equal(verdict.approved,false);assert(verdict.findings.some(finding=>finding.includes('canonical_time')));
});

test('a mapped producer output satisfies a requirement binding without a fake input echo',()=>{
  const current=structuredClone(proposal);
  current.source_requirements.push({requirement_id:'produced_result',requirement_kind:'data_dependency',source_spans:[{resource:'source/SKILL.md',start_line:1,end_line:1}],trigger:'produce',required_result:'Produce result.',resource_refs:[],details:{}});
  current.requirement_mappings.push({requirement_id:'produced_result',node_ids:['work'],binding_names:['result'],runtime_guards:[],resource_refs:[],status:'compiled',rationale:'The work node produces result.'});
  current.nodes[0].outputs_schema={type:'object',properties:{result:{type:'string'}},required:['result']};
  current.nodes[0].requirement_ids.push('produced_result');
  assert.equal(evaluateReview(result(),current,resources).approved,true);
});
