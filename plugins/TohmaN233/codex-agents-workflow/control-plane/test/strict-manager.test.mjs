import { REVIEW_IDS } from '../lib/skill-import/review-checklist.mjs';
import test from 'node:test';
import assert from 'node:assert/strict';
import { lstat, mkdtemp, mkdir, rm, readFile, writeFile, symlink } from 'node:fs/promises';
import { tmpdir } from './physical-tempdir.mjs';
import { join, resolve } from 'node:path';
import { WorkflowService } from '../lib/workflow-service.mjs';
import { loadConfig, saveConfig } from '../lib/config.mjs';
import { createDraft } from '../lib/workflow-schema.mjs';
import { StrictSessionManager, strictOutputByteBudget } from '../lib/execution/strict-session-manager.mjs';
import { refreshCodexRegistration } from '../lib/execution/codex-runtime-registration.mjs';
import { EXECUTOR_RESULT_MAX_BYTES } from '../lib/workflow-run-store.mjs';
import { codexStructuredSchema, restoreOptionalOmissions } from '../lib/execution/codex-structured-output.mjs';
import { validateStrictConfig, qualifiedStrictSettings, qualifiedCodexBinary, verifyCodexDistribution, codexQualification } from '../lib/execution/strict-config.mjs';
import { DEFAULT_CONFIG_PATH } from '../server.mjs';
import { randomUUID } from 'node:crypto';
import { processIdentity } from '../lib/execution/codex-process-ownership.mjs';
import { importCoarseSkill } from '../lib/skill-import/coarse-compiler.mjs';
import { canonicalJSON, digest } from '../lib/workflow-revisions.mjs';
import { repairGeneration } from '../lib/skill-import/generation-repair.mjs';
import { CONVERSION_CONTRACT } from '../lib/skill-import/conversion-contract.mjs';
import { SEMANTIC_BLUEPRINT_CONTRACT, SEMANTIC_REPAIR_CONTRACT } from '../lib/authoring/blueprint-contract.mjs';
import { GENERATED_PROPOSAL_ENVELOPE_SCHEMA, GENERATED_PROPOSAL_ENVELOPE_SCHEMA_V21, GENERATED_REPAIR_ENVELOPE_SCHEMA } from '../lib/skill-import/expansion-run.mjs';
import { AUTHORING_REPAIR_RESOURCE, AUTHORING_REVIEW_RESOURCE } from '../lib/authoring/authoring-workflows.mjs';
import { codexEventMetadata } from '../lib/execution/codex-session.mjs';
import { leaseToken } from '../lib/workflow-execution-envelope.mjs';

test('Strict wait observes only the exact owned attempt and its settled result',async()=>{
  const manager=new StrictSessionManager({configPath:'C:\\fixture\\strict-wait.json',getConfig:async()=>({})});
  const gate=deferred();
  const entry={runId:'run-exact',args:{node_id:'work',attempt_id:'attempt-exact'},adapter:{final_acceptance_required:false},
    preview:null,status:'running',error:null,job:gate.promise};
  manager.entries.set('run-exact/attempt-exact',entry);
  let resolved=false;const pending=manager.wait('run-exact','attempt-exact').then(result=>{resolved=true;return result;});
  await Promise.resolve();assert.equal(resolved,false);
  await assert.rejects(manager.wait('run-exact','other-attempt'),{code:'STRICT_SESSION_UNAVAILABLE'});
  entry.status='succeeded';gate.resolve();
  assert.equal((await pending).status,'succeeded');
});

const deferred = () => { let resolve, reject; const promise = new Promise((a, b) => { resolve = a; reject = b; }); return { promise, resolve, reject }; };

function checklist(proposal, failure='') {
  return {checks:REVIEW_IDS.map(id=>({status:failure && id==='hard_rules'?'fail':'pass',evidence:failure && id==='hard_rules'?failure:'Verified source and proposed graph for '+id}))};
}
const generatedProposal = proposal => {
  const node=proposal.nodes[0],key=node.id;
  const write=node.operation_mode==='write'||['implementation','complex_implementation'].includes(node.task_type),complex=node.task_type==='complex_implementation';
  const profile=node.task_type==='review'?'review':node.execution_target==='main'?(write?'main_write':'main_read'):complex?(write?'worker_complex_write':'worker_complex_read'):(write?'worker_write':'worker_read');
  return {proposal:{contract:SEMANTIC_BLUEPRINT_CONTRACT,purpose:'Preserve the imported task as an executable Workflow.',source_dispositions:[{section_id:'section_01_overview',disposition:'workflow',activity_keys:[key],note:'The entrypoint overview defines the generated task.'}],requirement_assignments:[],runtime_dependencies:[],records:[],lists:[],enums:[],activities:[{key,instructions:node.prompt_template ?? 'Perform the source-defined task.',profile,source_sections:['section_01_overview'],inputs:[],outputs:[],tool:''}],approvals:[],sequences:[],parallels:[],choices:[]}};
};
const generatedRepair = proposal => {
  const plan=generatedProposal(proposal).proposal,empty={source_dispositions:[],requirement_assignments:[],records:[],lists:[],enums:[],activities:[],approvals:[],sequences:[],parallels:[],choices:[]};
  return {proposal:{contract:SEMANTIC_REPAIR_CONTRACT,purpose:'',upsert:{...structuredClone(empty),activities:plan.activities.map(item=>({...item,instructions:item.instructions+' Clarify the review deliverable and its evidence.'}))},remove:empty}};
};

test('authoring output schemas are statically compatible with strict Codex output',()=>{
  for(const source of [GENERATED_PROPOSAL_ENVELOPE_SCHEMA,GENERATED_PROPOSAL_ENVELOPE_SCHEMA_V21,GENERATED_REPAIR_ENVELOPE_SCHEMA]){
    const schema=codexStructuredSchema(source);
    const check=node=>{
      if(node.anyOf){node.anyOf.forEach(check);return;}
      if(node.type==='object'){
        assert.equal(node.additionalProperties,false);
        assert.deepEqual(new Set(node.required),new Set(Object.keys(node.properties)));
        Object.values(node.properties).forEach(check);
      }
      if(node.type==='array')check(node.items);
    };
    check(schema);
  }
  const proposalSchema=codexStructuredSchema(GENERATED_PROPOSAL_ENVELOPE_SCHEMA);
  assert.equal(proposalSchema.properties.proposal.properties.choices.items.properties.default_body.minLength,1);
  assert.equal(proposalSchema.properties.proposal.properties.records.items.properties.fields.items.properties.type.pattern,'^[A-Za-z][A-Za-z0-9_-]*$');
  const source={type:'object',required:['items'],additionalProperties:false,properties:{items:{type:'array',items:{type:'object',required:['name'],additionalProperties:false,properties:{name:{type:'string'},optional:{type:'string'}}}}}};
  const strict=codexStructuredSchema(source);
  assert.equal(strict.properties.items.items.properties.optional.anyOf[1].type,'null');
  const restored=restoreOptionalOmissions({items:[{name:'kept',optional:null}]},source);
  assert.deepEqual(restored,{items:[{name:'kept'}]});
});

test('Strict planner submission requires dependency assessment only for the pinned v21 contract',async()=>{
  for(const [version,assessment] of [[20,undefined],[21,undefined],[21,null],[21,[]]]){
    const result=generatedProposal({nodes:[{id:'inspect',task_type:'review',prompt_template:'Review the source.'}]});
    if(assessment===undefined)delete result.proposal.runtime_dependencies;
    else result.proposal.runtime_dependencies=assessment;
    const persisted=new Error('Stop after validated output reaches persistence');
    let turnOptions,saves=0;
    const manager=new StrictSessionManager({configPath:join(tmpdir(),'strict-dependency-schema.json'),getConfig:async()=>({global:{max_prompt_chars:100000}})});
    const entry={runId:'schema-fixture',args:{node_id:'expand',attempt_id:'attempt'},envelope:{outputs_schema:{}},prompt:'Assess the pinned source.',skillResources:[],settings:{inactivity_timeout_ms:0},outputByteBudget:100000,writes:new Set(),authorize:async()=>{},event:async()=>{},
      runtime:{runs:{read:async()=>({pins:{root:{provenance:{kind:'authoring_workflow_run'},workflow:{authoring:{contract:`codex-authoring-workflow/v${version}`}}}},state:{}}),saveExecutorResult:async()=>{saves++;throw persisted;}}},
      session:{turn:async(_prompt,options)=>{turnOptions=options;return {output:JSON.stringify(result),thread_id:'synthetic',turn_id:'synthetic',audit:{}};},close:async()=>{}},
    };
    const accepted=version===20||Array.isArray(assessment);
    await assert.rejects(manager.execute(entry),error=>accepted?error===persisted:error.code==='DATA_INVALID'&&error.message.includes('runtime_dependencies'));
    assert.equal(saves,accepted?1:0);
    const dependencySchema=turnOptions.output_schema.properties.proposal.properties.runtime_dependencies;
    if(version===21){assert.equal(dependencySchema.type,'array');assert.equal(dependencySchema.anyOf,undefined);}
    else assert(dependencySchema.anyOf.some(schema=>schema.type==='null'));
  }
});

test('explicit blocked model results fail durably rather than advancing success edges',async t=>{
  for(const schema of [{},{type:'object',required:['ok'],properties:{ok:{type:'boolean'}},additionalProperties:false}]) {
    const f=await fixture(t,{schema,turn:async()=>({output:JSON.stringify({$workflow_blocked:'Required footage and briefing are missing.'}),thread_id:'blocked',turn_id:'blocked',audit:{}})});
    await f.service.call('dispatch',f.args);await f.entry(f.args).job;
    const state=await f.service.call('get',f.args);
    assert.equal(state.status,'failed');assert.equal(state.nodes.work.status,'failed');assert.equal(state.nodes.work.error.code,'WORKFLOW_NODE_BLOCKED');assert.equal(state.nodes.work.error.message,'Required footage and briefing are missing.');
    assert.notEqual(state.nodes.final.status,'ready');assert.equal(state.nodes.work.output,null);await assert.rejects(f.service.call('collect_strict',f.args),{code:'WORKFLOW_NODE_BLOCKED'});assert.equal(state.nodes.work.attempts[0].result_proposal,undefined);assert.equal(f.sessions[0].closed,true);
  }
});

test('Strict inactivity termination is disabled by default and requires an explicit positive duration',()=>{
  assert.equal(validateStrictConfig().inactivity_timeout_ms,0);
  assert.equal(validateStrictConfig({inactivity_timeout_ms:120000}).inactivity_timeout_ms,120000);
  assert.throws(()=>validateStrictConfig({inactivity_timeout_ms:-1}),{code:'STRICT_CONFIG'});
});

test('Strict nodes receive recoverable tool rejections and can correct the request in the same turn',async t=>{
  const f=await fixture(t,{turn:async settings=>{
    const rejected=await settings.toolBroker.call('read_workflow_resource',{path:'missing.txt'},'missing');
    assert.deepEqual(JSON.parse(rejected.contentItems[0].text),{error:{code:'CODEX_RESOURCE_DENIED',message:'Resource is outside the pinned node manifest'}});
    const corrected=await settings.toolBroker.call('read_workflow_resource',{path:'pinned.txt'},'corrected');
    assert.equal(JSON.parse(corrected.contentItems[0].text).text,'Immutable task instructions');
    return {output:'Recovered result',thread_id:'recoverable-tool',turn_id:'turn',audit:{}};
  }});
  await f.service.call('dispatch',f.args);await f.entry(f.args).job;
  const state=await f.service.call('get',f.args);
  assert.equal(state.nodes.work.status,'succeeded');
  const rejection=state.nodes.work.attempts[0].executor_events.find(event=>event.kind==='tool_operation'&&event.metadata.phase==='rejected');
  assert.equal(rejection.metadata.code,'CODEX_RESOURCE_DENIED');
});

test('Strict failures persist a bounded redacted diagnostic instead of a generic executor message',async t=>{
  const failure=Object.assign(new Error('authorization=top-secret broker crashed'),{code:'SYNTHETIC_FAILURE'});
  const f=await fixture(t,{turn:async()=>{throw failure;}});
  await f.service.call('dispatch',f.args);await f.entry(f.args).job;
  const state=await f.service.call('get',f.args);const attempt=state.nodes.work.attempts[0];
  assert.equal(attempt.error.code,'SYNTHETIC_FAILURE');
  assert.match(attempt.error.message,/SYNTHETIC_FAILURE: authorization=\[redacted\] broker crashed/);
  assert(!attempt.error.message.includes('top-secret'));
  const failed=attempt.executor_events.find(event=>event.kind==='session_state'&&event.metadata.status==='failed');
  assert.equal(failed.metadata.diagnostic,attempt.error.message);
});

test('Strict App Server error metadata retains a bounded useful cause without credentials or URLs',()=>{
  const metadata=codexEventMetadata({method:'error',params:{threadId:'thread',turnId:'turn',error:{code:'OUTPUT_LIMIT',message:'output limit reached authorization=secret see https://example.invalid/?token=secret'}}});
  assert.equal(metadata.error_code,'OUTPUT_LIMIT');
  assert.match(metadata.diagnostic,/OUTPUT_LIMIT: output limit reached authorization=\[redacted\] see \[redacted-url\]/);
  assert.doesNotMatch(metadata.diagnostic,/secret|example\.invalid/);
});

test('Strict token-usage metadata is journal-safe flat scalar evidence',()=>{
  const metadata=codexEventMetadata({method:'thread/tokenUsage/updated',params:{threadId:'thread',turnId:'turn',tokenUsage:{last:{inputTokens:120,cachedInputTokens:80,cacheWriteInputTokens:2,outputTokens:30,reasoningOutputTokens:20}}}});
  assert.deepEqual(metadata,{method:'thread/tokenUsage/updated',thread_id:'thread',turn_id:'turn',item_type:null,status:null,usage_available:true,input_tokens:120,cached_input_tokens:80,cache_write_input_tokens:2,output_tokens:30,reasoning_output_tokens:20});
  assert(Object.values(metadata).every(value=>value===null||typeof value==='string'||typeof value==='boolean'||Number.isSafeInteger(value)));
});

test('Codex context compaction does not interrupt ordinary event handling',()=>{
  const metadata=codexEventMetadata({method:'thread/tokenUsage/updated',params:{threadId:'thread',turnId:'turn',tokenUsage:{
    last:{inputTokens:0,cachedInputTokens:0,outputTokens:0,reasoningOutputTokens:0,totalTokens:4200},
    total:{inputTokens:0,cachedInputTokens:0,outputTokens:0,reasoningOutputTokens:0,totalTokens:32000},
  }}});
  assert.equal(metadata.method,'thread/tokenUsage/updated');
  assert.equal(metadata.thread_id,'thread');
  assert.equal(metadata.turn_id,'turn');
});

test('generation accepts a non-reviewer registered native model with read-only review and role-specific prompt contracts',async t=>{
  let proposal;
  const f=await fixture(t,{turn:async(settings,session)=>{const review=session.prompt.includes(AUTHORING_REVIEW_RESOURCE);if(review){const duplicate=await settings.toolBroker.call('read_workflow_resource',{path:'source/SKILL.md'},'duplicate-skill');assert.equal(JSON.parse(duplicate.contentItems[0].text).error.code,'CODEX_RESOURCE_DENIED');const packet=await settings.toolBroker.call('read_workflow_resource',{path:'analysis/review-request.txt'},'review-packet');assert.match(JSON.parse(packet.contentItems[0].text).text,/Review result\./);const canonical=await settings.toolBroker.call('read_workflow_resource',{path:AUTHORING_REVIEW_RESOURCE},'review-proposal');const exact=JSON.parse(JSON.parse(canonical.contentItems[0].text).text);assert(Array.isArray(exact.nodes));assert.equal(exact.source_revision,proposal.source_revision);}return {output:JSON.stringify(review?checklist(proposal):generatedProposal(proposal)),thread_id:'selectable-review',turn_id:'turn',audit:{}};}});
  const source=join(f.root,'selectable-source');await mkdir(source);await writeFile(join(source,'SKILL.md'),'---\nname: selectable\ndescription: test\n---\nReview result.');
  const {store}=await f.service.open();const pack=await importCoarseSkill(store,join(source,'SKILL.md'),{id:'selectable-source'});
  const origin={confidence:1,source_span:{resource:'source/SKILL.md',start_line:5,end_line:5}};
  proposal={source_revision:pack.revision_hash,source_requirements:[],requirement_mappings:[],planning_analysis:{parallelism:'Single bounded task; no independent work.',main_responsibilities:'Main accepts; subagent checks.',human_intervention:'Final human confirmation only.'},nodes:[{id:'check',type:'agent',execution_target:'subagent',provider_choice:'native-reviewer',task_type:'review',routing_reason:'Review',prompt_template:'Review',...origin}],edges:[{id:'a',source:'start',target:'check',...origin},{id:'b',source:'check',target:'final',...origin}]};
  const rules=await f.service.call('routing_defaults');rules.generation={review_provider_id:'native-luna',planner_provider_id:'native-luna',max_rounds:2};rules.routes.planning.provider_id='native-luna';
  const input={workflow_id:pack.workflow.id,revision_hash:pack.revision_hash,routing_rules:rules};
  const preview=await f.service.call('authoring_prompt_preview',input,{human:true});
  assert.equal(preview.invoked,false);assert.equal(f.sessions.length,0);assert.match(preview.shared_request,/Planner semantic responsibility contract/);assert.doesNotMatch(preview.shared_request,/cross_resource_consistency/);assert.match(preview.review_request,/Independent review acceptance contract/);assert.match(preview.review_request,/cross_resource_consistency/);
  const run=await f.service.call('start_authoring',{...input,run_id:'selectable-generation'},{human:true});const control={run_id:run.run_id,control_token:run.control_token};
  for(const phase of ['generating','reviewing']){const value=await f.service.call('advance_authoring',control,{human:true});assert.equal(value.phase,phase,JSON.stringify(value));assert.equal(value.progress.round,1);await Promise.all([...f.manager.entries.values()].map(e=>e.job));}
  const observed=await f.service.call('get',control);const denied=observed.nodes.final.attempts[0].executor_events.find(e=>e.kind==='tool_operation' && e.metadata.call_id==='duplicate-skill');assert.equal(denied.metadata.phase,'rejected');assert.equal(denied.metadata.code,'CODEX_RESOURCE_DENIED');
  assert.equal(f.sessions[0].settings.model,'gpt-6-luna');assert.equal(f.sessions[1].settings.model,'gpt-6-luna');assert.equal(f.sessions[1].settings.toolBroker.tools().some(t=>t.name==='write_workspace'),false);
  assert(f.sessions[1].prompt.includes(AUTHORING_REVIEW_RESOURCE));
  assert.doesNotMatch(f.sessions[1].prompt,/\nInputs:\n/,'empty reviewer bindings have no prompt block');
  assert(!f.sessions[1].prompt.includes(canonicalJSON(observed.nodes.expand.output.proposal)),
    'the canonical proposal is read from its pinned resource, never duplicated in the prompt');
  assert(observed.nodes.final.attempts[0].executor_events.some(event=>event.kind==='review_context_prepared'&&event.metadata.path===AUTHORING_REVIEW_RESOURCE));
  assert.equal((await f.service.call('advance_authoring',control,{human:true})).phase,'review_required');
  await f.service.call('cancel',control);
});

test('manually driven authoring pins the configured reviewer without enabling automatic repair',async t=>{
  let proposal;
  const f=await fixture(t,{turn:async(_settings,session)=>({output:JSON.stringify(session.prompt.includes(AUTHORING_REVIEW_RESOURCE)?checklist(proposal):generatedProposal(proposal)),thread_id:'manual-authoring-reviewer',turn_id:'turn',audit:{}})});
  const source=join(f.root,'manual-authoring-source');await mkdir(source);await writeFile(join(source,'SKILL.md'),'---\nname: manual-authoring\ndescription: test\n---\nReview result.');
  const {store,runtime}=await f.service.open();const pack=await importCoarseSkill(store,join(source,'SKILL.md'),{id:'manual-authoring-source'});
  const origin={confidence:1,source_span:{resource:'source/SKILL.md',start_line:5,end_line:5}};
  proposal={source_revision:pack.revision_hash,source_requirements:[],requirement_mappings:[],planning_analysis:{parallelism:'Single bounded task; no independent work.',main_responsibilities:'Main accepts; subagent checks.',human_intervention:'Final human confirmation only.'},nodes:[{id:'check',type:'agent',execution_target:'subagent',provider_choice:'native-reviewer',task_type:'review',routing_reason:'Review',prompt_template:'Review',...origin}],edges:[{id:'a',source:'start',target:'check',...origin},{id:'b',source:'check',target:'final',...origin}]};
  const rules=await f.service.call('routing_defaults');rules.generation={review_provider_id:'native-luna',planner_provider_id:'native-luna',max_rounds:2};
  const run=await f.service.call('create_authoring_run',{workflow_id:pack.workflow.id,revision_hash:pack.revision_hash,run_id:'manual-authoring-reviewer',workspace:f.workspace,provider_id:'native-luna',routing_rules:rules,automatic_generation:false,main_actor:'human-console'});
  const control={run_id:run.run_id,control_token:run.control_token},record=await runtime.runs.read(run.run_id);
  assert.equal(record.pins.generation,undefined);assert.equal(record.pins.authoring_reviewer.id,'native-luna');
  for(const phase of ['generating','reviewing']){const value=await f.service.call('drive',control,{model:true});assert.equal(value.phase,phase);await Promise.all([...f.manager.entries.values()].map(entry=>entry.job));}
  assert.equal(f.sessions.at(-2).settings.model,'gpt-6-luna');assert.equal(f.sessions.at(-1).settings.model,'gpt-6-luna');
  assert.equal((await f.service.call('drive',control,{model:true})).phase,'review_required');
  await f.service.call('cancel',control);
});

test('one-click generation prepares workspace and advances only to explicit human acceptance', async t => {
  let proposal,calls=0;
  const f = await fixture(t,{turn:async()=>({output:JSON.stringify(calls++===0?generatedProposal(proposal):checklist(proposal)),thread_id:'generation-test',turn_id:'turn',audit:{}})});
  const source = join(f.root,'generate-source'); await mkdir(source);
  await writeFile(join(source,'SKILL.md'),'---\nname: generate\ndescription: Review\n---\nReview a result.');
  const {store} = await f.service.open();
  const originalPack = await importCoarseSkill(store,join(source,'SKILL.md'),{id:'one-click-source'});
  const siblingWorkspace=join(f.root,'sibling-authoring-workspace');await mkdir(siblingWorkspace);
  const sibling=await f.service.call('create_authoring_run',{workflow_id:originalPack.workflow.id,revision_hash:originalPack.revision_hash,run_id:'one-click-sibling',workspace:siblingWorkspace,main_actor:'human-console'});
  const pack=await store.rename(originalPack.workflow.id,'Generate from renamed private source',originalPack.revision_hash);
  const origin={confidence:1,source_span:{resource:'source/SKILL.md',start_line:5,end_line:5}};
  proposal={source_revision:pack.revision_hash,source_requirements:[],requirement_mappings:[],planning_analysis:{parallelism:'Single bounded task; no independent work.',main_responsibilities:'Main accepts; subagent checks.',human_intervention:'Final human confirmation only.'},nodes:[{id:'check',type:'agent',prompt_template:'Review',execution_target:'subagent',provider_choice:'native-reviewer',task_type:'review',routing_reason:'Independent review',...origin}],edges:[{id:'a',source:'start',target:'check',...origin},{id:'b',source:'check',target:'final',...origin}]};
  const start={workflow_id:pack.workflow.id,revision_hash:pack.revision_hash,run_id:'one-click'};
  await assert.rejects(f.service.call('start_authoring',start),{code:'HUMAN_GENERATION'});
  const run=await f.service.call('start_authoring',start,{human:true});
  const control={run_id:run.run_id,control_token:run.control_token};
  const stateBefore=await f.service.call('get',control);
  assert(stateBefore.permissions.workspace.includes('skill-generation-workspaces'));
  const privateArtifacts=[stateBefore.permissions.workspace,join(f.root,'workflow-expansion-jobs',`wf-${run.run_id}.pack`),join(f.root,'workflow-runs',`run-${run.run_id}.run`)];
  await assert.rejects(f.service.call('accept_authoring',{...control,accepted:true},{human:true}),{code:'GENERATION_NOT_READY'});
  for(const phase of ['generating','reviewing']) {
    const progress=await f.service.call('advance_authoring',control,{human:true}); assert.equal(progress.phase,phase);
    await Promise.all([...f.manager.entries.values()].map(entry=>entry.job));
  }
  const preview=await f.service.call('advance_authoring',control,{human:true});
  assert.equal(preview.phase,'review_required',JSON.stringify(preview));
  assert.equal(preview.validation.valid,true);
  const activeRules=await f.service.call('routing_defaults'),activeConfig=await f.service.config();
  const configuredReviewer=activeConfig.providers.find(item=>item.id===activeRules.generation.review_provider_id);assert(configuredReviewer);
  assert.equal(f.sessions[1].settings.model,configuredReviewer.config.model);
  assert.equal(f.sessions[1].settings.effort,configuredReviewer.config.reasoning_effort);
  assert.equal(preview.workflow.finalization.required,true);
  assert.equal(preview.workflow.nodes.find(n=>n.id==='activity_001').executor.provider_id,'native-sol');
  assert.equal((await store.snapshot(pack.workflow.id)).revision_hash,pack.revision_hash);
  const {runtime}=await f.service.open(),pending=await runtime.runs.read(run.run_id),finalAttempt=pending.state.nodes.final.attempts.find(item=>item.id===pending.state.nodes.final.active_attempt_id);
  const finalLease={...control,node_id:'final',attempt_id:finalAttempt.id,lease_token:leaseToken(control.control_token,run.run_id,'final',finalAttempt.id,finalAttempt.lease_generation??0)};
  const originalOutput=structuredClone(pending.state.nodes.expand.output),originalProjection=structuredClone(pending.state.generation_projection);
  await runtime.transition(run.run_id,'generation_projection',state=>{state.nodes.expand.output.proposal.nodes[0].prompt_template+=' Semantically changed after review.';state.nodes.expand.output.host_pipeline.proposal_hash=digest(canonicalJSON(state.nodes.expand.output.proposal));state.generation_projection.projected_output_hash=digest(canonicalJSON(state.nodes.expand.output));state.updated_at=new Date().toISOString();});
  await assert.rejects(runtime.acceptAuthoringFinal(run.run_id,finalLease),{code:'AUTHORING_REVIEW_IDENTITY'});
  await runtime.transition(run.run_id,'generation_projection',state=>{state.nodes.expand.output=originalOutput;state.generation_projection=originalProjection;state.updated_at=new Date().toISOString();});
  await assert.rejects(f.service.call('collect_strict',{...finalLease,accepted:true},{human:true}),{code:'AUTHORING_HUMAN_ACCEPTANCE_REQUIRED'});
  const rawCompletion=await runtime.runs.readExecutorResult(run.run_id,finalAttempt.id,finalAttempt.result_proposal.sha256);
  await assert.rejects(runtime.completeNode(run.run_id,{...finalLease,completion:{...rawCompletion,acceptance:{accepted:true}}}),{code:'HOST_MAIN_LIFECYCLE_REQUIRED'});
  await assert.rejects(f.service.call('accept_authoring',{...control,accepted:false},{human:true}),{code:'GENERATION_ACCEPTANCE'});
  await assert.rejects(f.service.call('accept_authoring',{...control,accepted:true},{human:true}),error=>error.code==='AUTHORING_PURGE_INCOMPLETE'&&error.cause_code==='AUTHORING_CLEANUP_CONFLICT');
  for(const path of privateArtifacts)assert((await lstat(path)).isDirectory(),'cleanup conflict must delete no private artifact');
  assert.equal((await store.snapshot(pack.workflow.id,pack.revision_hash)).revision_hash,pack.revision_hash,'cleanup conflict must retain the private source revision');
  assert((await store.resources(pack.workflow.id,pack.revision_hash))['source/SKILL.md'],'cleanup conflict must retain private source objects');
  assert.equal((await store.snapshot(originalPack.workflow.id,originalPack.revision_hash)).revision_hash,originalPack.revision_hash,'cleanup conflict must retain a different private source revision used by a sibling Run');
  assert((await store.resources(originalPack.workflow.id,originalPack.revision_hash))['source/SKILL.md'],'cleanup conflict must retain source objects used by a different-revision sibling Run');
  await f.service.call('cancel',{run_id:sibling.run_id,control_token:sibling.control_token});
  const authoring_cleanup=await f.service.call('purge_authoring_artifacts',{...control,workflow_id:pack.workflow.id},{human:true});
  const saved={...await store.snapshot(pack.workflow.id),authoring_cleanup};
  assert.equal(saved.workflow.status,'draft'); assert.notEqual(saved.revision_hash,pack.revision_hash);
  assert(saved.workflow.nodes.filter(n=>n.origin).every(n=>n.origin.kind==='converted'&&n.origin.reviewed));
  assert(saved.workflow.edges.filter(n=>n.origin).every(n=>n.origin.kind==='converted'&&n.origin.reviewed));
  assert(!saved.workflow.import_status.unresolved.some(i=>i.code==='AI_INFERENCES_REQUIRE_REVIEW'));
  assert.equal(saved.authoring_cleanup.private_authoring_artifacts_purged,true);
  assert((await store.snapshot(pack.workflow.id)).resources.every(item=>!item.path.startsWith('source/')));
  for(const path of privateArtifacts)await assert.rejects(lstat(path),{code:'ENOENT'});
  assert.equal(f.sessions.length,2);
  await assert.rejects(runtime.runs.read(run.run_id),{code:'ENOENT'});
});

test('Strict capability rejects fan-out before creating any model session',async t=>{
  const f=await fixture(t),pack=await f.service.call('read',{workflow_id:'strict-test'}),workflow=structuredClone(pack.workflow),work=workflow.nodes.find(node=>node.id==='work');
  work.subagent_count='auto';work.fanout={input:'items',item_name:'item',result_output:'results',distribution:'one_per_item',scheduling:'parallel',join:'all_required'};
  const providers=(await f.service.config()).providers;
  await assert.rejects(f.manager.capability({...pack,workflow},providers,[]),{code:'STRICT_FANOUT_UNSUPPORTED'});assert.equal(f.sessions.length,0);
});

test('current generation succeeds in one planner round when the planner omits host-owned node fields', async t => {
  let proposal;
  const f=await fixture(t,{fixtureProjection:false,turn:async settings=>({output:JSON.stringify(settings.model==='gpt-6.1-sol'?checklist(proposal):generatedProposal(proposal)),thread_id:'host-projection',turn_id:'turn',audit:{}})});
  const source=join(f.root,'host-projection-source');await mkdir(source);await writeFile(join(source,'SKILL.md'),'---\nname: host-projection\ndescription: Review\n---\nReview a result.');
  const {store}=await f.service.open();const pack=await importCoarseSkill(store,join(source,'SKILL.md'),{id:'host-projection-source'});
  const origin={confidence:1,source_span:{resource:'source/SKILL.md',start_line:5,end_line:5}};
  proposal={source_revision:pack.revision_hash,source_requirements:[],requirement_mappings:[],planning_analysis:{parallelism:'One task.',main_responsibilities:'Main accepts.',human_intervention:'Final confirmation.'},nodes:[{id:'check',type:'agent',execution_target:'subagent',provider_choice:'native-reviewer',task_type:'review',routing_reason:'Independent review',prompt_template:'Review',...origin}],edges:[{id:'a',source:'start',target:'check',...origin},{id:'b',source:'check',target:'final',...origin}]};
  const run=await f.service.call('start_authoring',{workflow_id:pack.workflow.id,revision_hash:pack.revision_hash,run_id:'host-projection'},{human:true});const control={run_id:run.run_id,control_token:run.control_token};
  for(const phase of ['generating','reviewing','review_required']){assert.equal((await f.service.call('advance_authoring',control,{human:true})).phase,phase);await Promise.all([...f.manager.entries.values()].map(entry=>entry.job));}
  const projected=await f.service.call('get',control);const projectedProposal=projected.nodes.expand.output.proposal;
  assert.equal(projected.generation_projection.contract_version,CONVERSION_CONTRACT.version);
  assert.deepEqual(projected.generation_projection.review_inputs_schema.properties.task,{type:'string'});
  assert(projected.generation_projection.repair_actions.some(item=>item.kind==='host_contract_projection'));
  assert.equal(projected.generation_projection.pipeline_trace.contract,'codex-authoring-pipeline/v1');
  assert.equal(projected.generation_projection.pipeline_trace.stages.find(stage=>stage.id==='deterministic_validation').result.cycle_free,true);
  assert.deepEqual(projectedProposal.nodes[0].input_bindings,{});
  assert.deepEqual(projectedProposal.nodes[0].resource_refs,['source/SKILL.md']);
  assert.deepEqual(projectedProposal.nodes[0].requirement_ids,[]);
  const saved=await f.service.call('accept_authoring',{...control,accepted:true},{human:true});const node=saved.workflow.nodes.find(item=>item.id==='activity_001');
  assert.deepEqual(node.input_bindings,{});assert.deepEqual(node.resources,[]);assert.equal(f.sessions.length,2);
  assert.equal(saved.workflow.nodes.find(item=>item.id==='final').input_bindings.task,'/inputs/task');
});

test('host/compiler upgrades recheck an exact persisted proposal without another planner call', async t => {
  let proposal;
  const f=await fixture(t,{turn:async settings=>({output:JSON.stringify(settings.model==='gpt-6.1-sol'?checklist(proposal):generatedProposal(proposal)),thread_id:'generation-recheck',turn_id:'turn',audit:{}})});
  const source=join(f.root,'recheck-source');await mkdir(source);await writeFile(join(source,'SKILL.md'),'---\nname: recheck\ndescription: Review\n---\nReview a result.');
  const {store}=await f.service.open();const pack=await importCoarseSkill(store,join(source,'SKILL.md'),{id:'recheck-source'});
  const origin={confidence:1,source_span:{resource:'source/SKILL.md',start_line:5,end_line:5}};
  proposal={source_revision:pack.revision_hash,source_requirements:[],requirement_mappings:[],planning_analysis:{parallelism:'One task.',main_responsibilities:'Main accepts.',human_intervention:'Final confirmation.'},nodes:[{id:'check',type:'agent',execution_target:'subagent',provider_choice:'native-reviewer',task_type:'review',routing_reason:'Independent review',prompt_template:'Review',...origin}],edges:[{id:'a',source:'start',target:'check',...origin},{id:'b',source:'check',target:'final',...origin}]};
  const original=await f.service.call('start_authoring',{workflow_id:pack.workflow.id,revision_hash:pack.revision_hash,run_id:'recheck-original'},{human:true});
  const originalControl={run_id:original.run_id,control_token:original.control_token};
  assert.equal((await f.service.call('advance_authoring',originalControl,{human:true})).phase,'generating');await Promise.all([...f.manager.entries.values()].map(entry=>entry.job));
  await f.service.call('cancel',originalControl);assert.equal(f.sessions.length,1);

  await assert.rejects(f.service.call('recheck_authoring',{source_run_id:original.run_id,run_id:'recheck-copy'}),{code:'HUMAN_GENERATION'});
  const replay=await f.service.call('recheck_authoring',{source_run_id:original.run_id,run_id:'recheck-copy'},{human:true});
  assert.equal(replay.recheck.planner_invoked,false);assert.equal(f.sessions.length,1);
  const replayState=await f.service.call('get',{run_id:replay.run_id,control_token:replay.control_token});
  assert.equal(replayState.nodes.expand.status,'succeeded');
  assert.equal(replayState.nodes.expand.attempts[0].dispatch.receipt.executor,'host-generation-replay');
  assert.equal(replayState.nodes.expand.attempts[0].dispatch.receipt.task_id,original.run_id);
  const replayControl={run_id:replay.run_id,control_token:replay.control_token};
  assert.equal((await f.service.call('advance_authoring',replayControl,{human:true})).phase,'reviewing');await Promise.all([...f.manager.entries.values()].map(entry=>entry.job));
  assert.equal((await f.service.call('advance_authoring',replayControl,{human:true})).phase,'review_required');assert.equal(f.sessions.length,2);
  await f.service.call('cancel',replayControl);

  const repairReplay=await f.service.call('recheck_authoring',{source_run_id:original.run_id,run_id:'recheck-repair-copy'},{human:true});
  const repairControl={run_id:repairReplay.run_id,control_token:repairReplay.control_token};
  const repairRecord=await (await f.service.open()).runtime.runs.read(repairReplay.run_id);
  const repair=await repairGeneration((await f.service.open()).runtime,repairControl,repairRecord,{code:'GENERATION_REVIEW_FINDINGS',findings:[{target_id:'planner_repair_001',owner:'planner',check_ids:['hard_rules'],semantic_keys:['check'],affected_semantic_fields:['activities.instructions'],source_spans:[],evidence:['Preserve the exact source rule.'],minimal_change:'Preserve the exact source rule.'}]});
  assert.equal(repair.phase,'repairing');assert.equal(f.sessions.length,2);
  await f.service.call('cancel',repairControl);
});

test('review protocol defects stop without consuming a planner or reviewer retry', async t => {
  let proposal;
  const f=await fixture(t,{turn:async settings=>{
    if(settings.model!=='gpt-6.1-sol') return {output:JSON.stringify(generatedProposal(proposal)),thread_id:'review-recheck',turn_id:'planner',audit:{}};
    const value=checklist(proposal);value.checks.find(row=>row.id==='portable_artifact').source_spans=[{resource:'source/SKILL.md',start_line:999,end_line:999}];
    return {output:JSON.stringify(value),thread_id:'review-recheck',turn_id:'reviewer',audit:{}};
  }});
  const source=join(f.root,'review-recheck-source');await mkdir(source);await writeFile(join(source,'SKILL.md'),'---\nname: review-recheck\ndescription: Review\n---\nReview a result.');
  const {store,runtime}=await f.service.open();const pack=await importCoarseSkill(store,join(source,'SKILL.md'),{id:'review-recheck-source'});
  const origin={confidence:1,source_span:{resource:'source/SKILL.md',start_line:5,end_line:5}};
  proposal={source_revision:pack.revision_hash,source_requirements:[],requirement_mappings:[],planning_analysis:{parallelism:'One task.',main_responsibilities:'Main accepts.',human_intervention:'Final confirmation.'},nodes:[{id:'check',type:'agent',execution_target:'subagent',provider_choice:'native-reviewer',task_type:'review',routing_reason:'Independent review',prompt_template:'Review',...origin}],edges:[{id:'a',source:'start',target:'check',...origin},{id:'b',source:'check',target:'final',...origin}]};
  const run=await f.service.call('start_authoring',{workflow_id:pack.workflow.id,revision_hash:pack.revision_hash,run_id:'review-recheck'},{human:true});const control={run_id:run.run_id,control_token:run.control_token};
  for(const phase of ['generating','reviewing']){assert.equal((await f.service.call('advance_authoring',control,{human:true})).phase,phase);await Promise.all([...f.manager.entries.values()].map(entry=>entry.job));}
  const record=await runtime.runs.read(run.run_id);const repair=await repairGeneration(runtime,control,record,{code:'GENERATION_CHECKLIST_INVALID',message:'Invalid source evidence in portable_artifact'},{reviewOnly:true});
  assert.equal(repair.phase,'attention');assert.equal(repair.error.code,'GENERATION_REVIEW_PROTOCOL');assert.equal(f.sessions.length,2);
  await f.service.call('cancel',control);
});

test('model-authored Provider choices are structurally absent and Host routing proceeds without repair',async t=>{
  let proposal;let generated=0;
  const f=await fixture(t,{turn:async settings=>{
    if(settings.model==='gpt-6.1-sol') return {output:JSON.stringify(checklist(proposal)),thread_id:'routing-repair',turn_id:'turn',audit:{}};
    const value=structuredClone(proposal);if(generated++===0)value.nodes[0].provider_choice='invented-provider';
    return {output:JSON.stringify(generatedProposal(value)),thread_id:'routing-repair',turn_id:'turn',audit:{}};
  }});
  const source=join(f.root,'routing-repair');await mkdir(source);await writeFile(join(source,'SKILL.md'),'---\nname: routing-repair\ndescription: Review\n---\nReview a result.');
  const {store}=await f.service.open();const pack=await importCoarseSkill(store,join(source,'SKILL.md'),{id:'routing-repair'});
  const origin={confidence:1,source_span:{resource:'source/SKILL.md',start_line:5,end_line:5}};
  proposal={source_revision:pack.revision_hash,source_requirements:[],requirement_mappings:[],planning_analysis:{parallelism:'One task.',main_responsibilities:'Main accepts.',human_intervention:'Final confirmation.'},nodes:[{id:'check',type:'agent',execution_target:'subagent',provider_choice:'native-reviewer',task_type:'review',routing_reason:'Independent review',prompt_template:'Review',...origin}],edges:[{id:'a',source:'start',target:'check',...origin},{id:'b',source:'check',target:'final',...origin}]};
  const run=await f.service.call('start_authoring',{workflow_id:pack.workflow.id,revision_hash:pack.revision_hash,run_id:'routing-repair'},{human:true});const control={run_id:run.run_id,control_token:run.control_token};
  for(const phase of ['generating','reviewing','review_required']){
    assert.equal((await f.service.call('advance_authoring',control,{human:true})).phase,phase);
    await Promise.all([...f.manager.entries.values()].map(e=>e.job));
  }
  assert.equal(generated,1);await f.service.call('cancel',control);
});
test('an invalid review checklist stops without retrying either model',async t=>{
  let proposal;let generated=0;let reviews=0;
  const f=await fixture(t,{turn:async settings=>{
    if(settings.model!=='gpt-6.1-sol'){generated++;return {output:JSON.stringify(generatedProposal(proposal)),thread_id:'routing-repair',turn_id:'turn',audit:{}};}
    const value=checklist(proposal);if(reviews++===0)value.checks[1].id='hard_rules';
    return {output:JSON.stringify(value),thread_id:'routing-repair',turn_id:'turn',audit:{}};
  }});
  const source=join(f.root,'routing-repair');await mkdir(source);await writeFile(join(source,'SKILL.md'),'---\nname: routing-repair\ndescription: Review\n---\nReview a result.');
  const {store}=await f.service.open();const pack=await importCoarseSkill(store,join(source,'SKILL.md'),{id:'routing-repair'});
  const origin={confidence:1,source_span:{resource:'source/SKILL.md',start_line:5,end_line:5}};
  proposal={source_revision:pack.revision_hash,source_requirements:[],requirement_mappings:[],planning_analysis:{parallelism:'One task.',main_responsibilities:'Main accepts.',human_intervention:'Final confirmation.'},nodes:[{id:'check',type:'agent',execution_target:'subagent',provider_choice:'native-reviewer',task_type:'review',routing_reason:'Independent review',prompt_template:'Review',...origin}],edges:[{id:'a',source:'start',target:'check',...origin},{id:'b',source:'check',target:'final',...origin}]};
  const run=await f.service.call('start_authoring',{workflow_id:pack.workflow.id,revision_hash:pack.revision_hash,run_id:'routing-repair'},{human:true});const control={run_id:run.run_id,control_token:run.control_token};
  for(const phase of ['generating','reviewing','attention']){
    assert.equal((await f.service.call('advance_authoring',control,{human:true})).phase,phase);
    await Promise.all([...f.manager.entries.values()].map(e=>e.job));
  }
  assert.equal(generated,1);assert.equal(reviews,1);const state=await f.service.call('get',control);assert.equal(state.nodes.expand.attempts.length,1);assert.equal(state.nodes.final.attempts.length,1);await f.service.call('cancel',control);
});
test('a schema-invalid review stops after the failed session closes',async t=>{
  let proposal;let generated=0;let reviews=0;
  const f=await fixture(t,{turn:async settings=>{
    if(settings.model!=='gpt-6.1-sol'){generated++;return {output:JSON.stringify(generatedProposal(proposal)),thread_id:'routing-repair',turn_id:'turn',audit:{}};}
    const value=checklist(proposal);if(reviews++===0)value.checks.pop();
    return {output:JSON.stringify(value),thread_id:'routing-repair',turn_id:'turn',audit:{}};
  }});
  const source=join(f.root,'routing-repair');await mkdir(source);await writeFile(join(source,'SKILL.md'),'---\nname: routing-repair\ndescription: Review\n---\nReview a result.');
  const {store}=await f.service.open();const pack=await importCoarseSkill(store,join(source,'SKILL.md'),{id:'routing-repair'});
  const origin={confidence:1,source_span:{resource:'source/SKILL.md',start_line:5,end_line:5}};
  proposal={source_revision:pack.revision_hash,source_requirements:[],requirement_mappings:[],planning_analysis:{parallelism:'One task.',main_responsibilities:'Main accepts.',human_intervention:'Final confirmation.'},nodes:[{id:'check',type:'agent',execution_target:'subagent',provider_choice:'native-reviewer',task_type:'review',routing_reason:'Independent review',prompt_template:'Review',...origin}],edges:[{id:'a',source:'start',target:'check',...origin},{id:'b',source:'check',target:'final',...origin}]};
  const run=await f.service.call('start_authoring',{workflow_id:pack.workflow.id,revision_hash:pack.revision_hash,run_id:'routing-repair'},{human:true});const control={run_id:run.run_id,control_token:run.control_token};
  for(const phase of ['generating','reviewing','attention']){
    assert.equal((await f.service.call('advance_authoring',control,{human:true})).phase,phase);
    await Promise.all([...f.manager.entries.values()].map(e=>e.job));
  }
  assert.equal(generated,1);assert.equal(reviews,1);const state=await f.service.call('get',control);assert.equal(state.nodes.expand.attempts.length,1);assert.equal(state.nodes.final.attempts.length,1);await f.service.call('cancel',control);
});
test('one-click generation exposes managed login without silently starting a model', async t => {
  const f = await fixture(t,{authenticated:false});
  const source=join(f.root,'login-source'); await mkdir(source);
  await writeFile(join(source,'SKILL.md'),'---\nname: login\ndescription: Review\n---\nReview a result.');
  const {store}=await f.service.open();
  const pack=await importCoarseSkill(store,join(source,'SKILL.md'),{id:'login-source'});
  const run=await f.service.call('start_authoring',{workflow_id:pack.workflow.id,revision_hash:pack.revision_hash,run_id:'login-generation'},{human:true});
  const control={run_id:run.run_id,control_token:run.control_token};
  await f.service.call('advance_authoring',control,{human:true});
  const progress=await f.service.call('advance_authoring',control,{human:true});
  assert.equal(progress.phase,'authentication_required');
  assert.equal(progress.live.status,'auth_required');
  assert.equal(f.sessions[0].calls,0);
  await assert.rejects(f.service.call('login_authoring',control),{code:'HUMAN_AUTHENTICATION_REQUIRED'});
  await assert.rejects(f.service.call('login_authoring',{...control,control_token:'wrong'},{human:true}));
  const session=f.sessions[0];
  session.login=async()=>({login_id:'test-login',auth_url:'https://auth.openai.com/test-only'});
  session.client.waitFor=async(predicate)=>{
    const event=[{method:'account/login/completed',params:{loginId:'test-login',success:true}},{method:'account/updated',params:{authMode:'chatgpt'}}].find(predicate);
    session.client.events.push(event);return event;
  };
  session.turn=async()=>{throw new Error('Synthetic stop after successful login handoff');};
  const login=await f.service.call('login_authoring',control,{human:true});
  assert.equal(login.auth_url,'https://auth.openai.com/test-only');
  assert.equal(login.status,'auth_pending');

  await f.service.call('cancel',control);
});
test('generation repairs review findings with pinned providers and preserves rejected attempts', async t => {
  let proposal, reviews=0,plannerCalls=0,repairContext=null; const prompts=[];
  const f=await fixture(t,{turn:async(settings,session)=>{prompts.push(session.prompt);if(settings.model!=='gpt-6.1-sol' && plannerCalls>0){const resource=await settings.toolBroker.call('read_workflow_resource',{path:AUTHORING_REPAIR_RESOURCE},'repair-context');repairContext=JSON.parse(JSON.parse(resource.contentItems[0].text).text);}return {output:JSON.stringify(settings.model==='gpt-6.1-sol'?checklist(proposal,++reviews>1?'':'Clarify the review deliverable.'):(plannerCalls++?generatedRepair(proposal):generatedProposal(proposal))),thread_id:'repair',turn_id:'round',audit:{}};}});
  const config=await f.service.config();config.providers.find(p=>p.id==='native-sol').requires_user_approval=true;await saveConfig(config,{configPath:f.configPath});
  const source=join(f.root,'repair-source');await mkdir(source);await writeFile(join(source,'SKILL.md'),'---\nname: repair\ndescription: Review\n---\nReview result.');
  const {store,runtime}=await f.service.open();const pack=await importCoarseSkill(store,join(source,'SKILL.md'),{id:'repair-source'});
  const origin={confidence:1,source_span:{resource:'source/SKILL.md',start_line:5,end_line:5}};
  proposal={source_revision:pack.revision_hash,source_requirements:[],requirement_mappings:[],planning_analysis:{parallelism:'Single bounded task; no independent work.',main_responsibilities:'Main accepts; subagent checks.',human_intervention:'Final human confirmation only.'},nodes:[{id:'check',type:'agent',execution_target:'subagent',provider_choice:'native-sol',task_type:'review',routing_reason:'Review',prompt_template:'Review',...origin}],edges:[{id:'a',source:'start',target:'check',...origin},{id:'b',source:'check',target:'final',...origin}]};
  const run=await f.service.call('start_authoring',{workflow_id:pack.workflow.id,revision_hash:pack.revision_hash,run_id:'repair-generation'},{human:true});const control={run_id:run.run_id,control_token:run.control_token};
  async function step(){const result=await f.service.call('advance_authoring',control,{human:true});await Promise.all([...f.manager.entries.values()].map(e=>e.job));return result;}
  assert.equal((await step()).phase,'generating');const approval=await step();assert.equal(approval.phase,'approval');await f.service.call('approve',{...control,approval_id:approval.approvals[0].id,decision:true});assert.equal((await step()).phase,'reviewing');
  await assert.rejects(f.service.call('accept_authoring',{...control,accepted:true},{human:true}),{code:'GENERATION_REVIEW_BLOCKED'});
  const blockedRecord=await runtime.runs.read(run.run_id),blockedAttempt=blockedRecord.state.nodes.final.attempts.find(item=>item.id===blockedRecord.state.nodes.final.active_attempt_id),blockedLease={...control,node_id:'final',attempt_id:blockedAttempt.id,lease_token:leaseToken(control.control_token,run.run_id,'final',blockedAttempt.id,blockedAttempt.lease_generation??0)};
  await assert.rejects(runtime.acceptAuthoringFinal(run.run_id,blockedLease),{code:'GENERATION_REVIEW_BLOCKED'});
  const unchanged=await runtime.runs.read(run.run_id);assert.equal(unchanged.state.status,'running');assert.equal(unchanged.state.nodes.final.attempts.at(-1).human_acceptance,undefined);
  assert.equal((await step()).phase,'repairing');
  assert.equal((await step()).phase,'generating');const nextApproval=await step();assert.equal(nextApproval.phase,'approval');await f.service.call('approve',{...control,approval_id:nextApproval.approvals[0].id,decision:true});assert.equal((await step()).phase,'reviewing');assert.equal((await step()).phase,'review_required');
  assert(prompts[2].includes(AUTHORING_REPAIR_RESOURCE));assert.match(JSON.stringify(repairContext.feedback),/Clarify the review deliverable\./);
  const state=await f.service.call('get',control);assert.equal(state.nodes.expand.attempts.length,2);assert.equal(state.nodes.final.attempts.length,2);assert.equal(state.status,'running');
  const saved=await f.service.call('accept_authoring',{...control,accepted:true},{human:true});
  assert.equal(saved.workflow.status,'draft');assert.notEqual(saved.revision_hash,pack.revision_hash);
  assert.match(saved.workflow.nodes.find(item=>item.id==='activity_001').prompt_template,/Clarify the review deliverable and its evidence\./);
  assert.equal(f.sessions.length,4);
  const plannerSessions=f.sessions.filter(session=>session.settings.model!=='gpt-6.1-sol');
  assert.equal(plannerSessions.length,2);
  assert.equal(plannerSessions[0].turnOptions.output_schema?.properties?.proposal?.properties?.contract?.const,SEMANTIC_BLUEPRINT_CONTRACT);
  assert.equal(plannerSessions[1].turnOptions.output_schema?.properties?.proposal?.properties?.contract?.const,SEMANTIC_REPAIR_CONTRACT);
  assert(plannerSessions[1].turnOptions.output_schema.properties.proposal.properties.upsert.properties.requirement_assignments.maxItems<500);
  assert.equal(plannerSessions[1].turnOptions.output_schema.properties.proposal.properties.remove.properties.records.maxItems,0);
});
test('targeted repairs accumulate from the newest planner artifact while the last canonical projection stays separate', async t => {
  let proposal,plannerCalls=0,reviews=0,patchOneArtifact=null;const repairContexts=[];
  const emptyGroups=()=>({source_dispositions:[],requirement_assignments:[],records:[],lists:[],enums:[],activities:[],approvals:[],sequences:[],parallels:[],choices:[]});
  const patch=(previous,marker,sourceSection)=>{const empty=emptyGroups();return {proposal:{contract:SEMANTIC_REPAIR_CONTRACT,purpose:'',upsert:{...structuredClone(empty),activities:[{...structuredClone(previous.activities[0]),instructions:`${previous.activities[0].instructions} ${marker}`,source_sections:[sourceSection]}]},remove:empty}};};
  const f=await fixture(t,{turn:async(settings)=>{
    if(settings.model==='gpt-6.1-sol')return {output:JSON.stringify(checklist(proposal,++reviews===1?'First review requires a semantic clarification.':'')),thread_id:'cumulative-review',turn_id:`review-${reviews}`,audit:{}};
    if(plannerCalls++===0)return {output:JSON.stringify(generatedProposal(proposal)),thread_id:'cumulative-plan',turn_id:'plan-0',audit:{}};
    const resource=await settings.toolBroker.call('read_workflow_resource',{path:AUTHORING_REPAIR_RESOURCE},`cumulative-${plannerCalls}`);
    const context=JSON.parse(JSON.parse(resource.contentItems[0].text).text);repairContexts.push(context);
    if(plannerCalls===2){patchOneArtifact=patch(context.previous_proposal,'PATCH_ONE','section_missing_from_source');return {output:JSON.stringify(patchOneArtifact),thread_id:'cumulative-plan',turn_id:'plan-1',audit:{}};}
    assert.match(context.previous_proposal.activities[0].instructions,/PATCH_ONE/);
    const second=patch(context.previous_proposal,'','section_01_overview');second.proposal.upsert.activities[0].instructions=context.previous_proposal.activities[0].instructions;
    return {output:JSON.stringify(second),thread_id:'cumulative-plan',turn_id:'plan-2',audit:{}};
  }});
  const source=join(f.root,'cumulative-repair-source');await mkdir(source);await writeFile(join(source,'SKILL.md'),'---\nname: cumulative-repair\ndescription: Review\n---\nReview result.');
  const {store}=await f.service.open();const pack=await importCoarseSkill(store,join(source,'SKILL.md'),{id:'cumulative-repair-source'});
  const origin={confidence:1,source_span:{resource:'source/SKILL.md',start_line:5,end_line:5}};
  proposal={source_revision:pack.revision_hash,source_requirements:[],requirement_mappings:[],planning_analysis:{parallelism:'Single bounded task.',main_responsibilities:'Main accepts.',human_intervention:'Final confirmation.'},nodes:[{id:'check',type:'agent',execution_target:'subagent',provider_choice:'native-reviewer',task_type:'review',routing_reason:'Review',prompt_template:'Review',...origin}],edges:[{id:'a',source:'start',target:'check',...origin},{id:'b',source:'check',target:'final',...origin}]};
  const run=await f.service.call('start_authoring',{workflow_id:pack.workflow.id,revision_hash:pack.revision_hash,run_id:'cumulative-repair'},{human:true});const control={run_id:run.run_id,control_token:run.control_token};
  async function step(){const result=await f.service.call('advance_authoring',control,{human:true});await Promise.all([...f.manager.entries.values()].map(entry=>entry.job));return result;}
  assert.equal((await step()).phase,'generating');assert.equal((await step()).phase,'reviewing');
  const canonical=await f.service.call('get',control);assert.doesNotMatch(canonical.generation_projection.authoring_plan.activities[0].instructions,/PATCH_ONE/);
  const firstRepair=await step();assert.equal(firstRepair.phase,'repairing',JSON.stringify(firstRepair));assert.equal((await step()).phase,'generating');
  const secondRepair=await step();assert.equal(secondRepair.phase,'repairing',JSON.stringify(secondRepair));
  const cumulative=await f.service.call('get',control),patchAttempt=cumulative.nodes.expand.attempts.at(-1);
  assert.match(cumulative.generation_repair.latest_cumulative_plan.proposal.activities[0].instructions,/PATCH_ONE/);
  assert.equal(cumulative.generation_repair.latest_cumulative_plan.attempt_id,patchAttempt.id);
  assert.equal(cumulative.generation_repair.latest_cumulative_plan.output_hash,digest(canonicalJSON(patchOneArtifact)));
  assert(cumulative.generation_repair.plan_ledger.some(entry=>entry.attempt_id===patchAttempt.id&&entry.output_hash===digest(canonicalJSON(patchOneArtifact))));
  assert.doesNotMatch(cumulative.generation_projection.authoring_plan.activities[0].instructions,/PATCH_ONE/);
  assert.equal((await step()).phase,'generating');assert.equal((await step()).phase,'reviewing');assert.equal((await step()).phase,'review_required');
  assert.equal(repairContexts.length,2);assert.match(repairContexts[1].previous_proposal.activities[0].instructions,/PATCH_ONE/);
  const replay=await f.service.call('recheck_authoring',{source_run_id:run.run_id,run_id:'cumulative-replay'},{human:true});
  const replayControl={run_id:replay.run_id,control_token:replay.control_token},replayed=await f.service.call('get',replayControl);
  assert.equal(replay.recheck.planner_invoked,false);
  assert.equal(replayed.nodes.expand.output.proposal.contract,SEMANTIC_BLUEPRINT_CONTRACT);
  assert.match(replayed.nodes.expand.output.proposal.activities[0].instructions,/PATCH_ONE/);
  assert.equal((await f.service.call('advance_authoring',replayControl,{human:true})).phase,'reviewing');
  await f.service.call('cancel',replayControl);
  await f.service.call('cancel',control);
});
test('authoring pre-review gate preserves semantic source identity across claim, dispatch and idempotent redispatch', async t => {
  let proposal,reviews=0;
  const f=await fixture(t,{turn:async settings=>({output:JSON.stringify(settings.model==='gpt-6.1-sol'?checklist(proposal,++reviews===1?'Reviewer requests one semantic revision.':''):generatedProposal(proposal)),thread_id:'idempotent-review',turn_id:`turn-${reviews}`,audit:{}})});
  const source=join(f.root,'idempotent-review-source');await mkdir(source);await writeFile(join(source,'SKILL.md'),'---\nname: idempotent-review\ndescription: Review\n---\nReview result.');
  const {store,runtime}=await f.service.open();const pack=await importCoarseSkill(store,join(source,'SKILL.md'),{id:'idempotent-review-source'});
  const origin={confidence:1,source_span:{resource:'source/SKILL.md',start_line:5,end_line:5}};
  proposal={source_revision:pack.revision_hash,source_requirements:[],requirement_mappings:[],planning_analysis:{parallelism:'Single task.',main_responsibilities:'Main accepts.',human_intervention:'Final confirmation.'},nodes:[{id:'check',type:'agent',execution_target:'subagent',provider_choice:'native-reviewer',task_type:'review',routing_reason:'Review',prompt_template:'Review',...origin}],edges:[{id:'a',source:'start',target:'check',...origin},{id:'b',source:'check',target:'final',...origin}]};
  const run=await f.service.call('start_authoring',{workflow_id:pack.workflow.id,revision_hash:pack.revision_hash,run_id:'idempotent-review'},{human:true});const control={run_id:run.run_id,control_token:run.control_token};
  assert.equal((await f.service.call('advance_authoring',control,{human:true})).phase,'generating');await Promise.all([...f.manager.entries.values()].map(entry=>entry.job));
  const planned=await runtime.runs.read(run.run_id),expandAttempt=planned.state.nodes.expand.active_attempt_id;
  assert.equal((await f.service.call('advance_authoring',control,{human:true})).phase,'reviewing');
  const claimed=await runtime.runs.read(run.run_id),projection=structuredClone(claimed.state.generation_projection),finalAttempt=claimed.state.nodes.final.attempts.find(item=>item.id===claimed.state.nodes.final.active_attempt_id);
  assert(projection.authoring_plan);assert(projection.pipeline_trace);assert.equal(projection.pipeline_trace_binding.attempt_id,expandAttempt);
  const args={...control,node_id:'final',attempt_id:finalAttempt.id,lease_token:leaseToken(control.control_token,run.run_id,'final',finalAttempt.id,finalAttempt.lease_generation??0)};
  const afterDispatch=await runtime.runs.read(run.run_id);
  assert.deepEqual(afterDispatch.state.generation_projection,projection);await f.entry(args).job;

  await runtime.transition(run.run_id,'generation_projection',state=>{delete state.generation_projection.pipeline_trace;delete state.generation_projection.pipeline_trace_binding;state.updated_at=new Date().toISOString();});
  const legacy=await runtime.runs.read(run.run_id),legacySequence=legacy.sequence,legacySource=legacy.state.generation_projection.source_output_hash,legacyPlan=structuredClone(legacy.state.generation_projection.authoring_plan);
  const duplicate=await f.service.call('dispatch',args);assert.equal(duplicate.idempotent,true);
  const repeated=await runtime.runs.read(run.run_id);assert.equal(repeated.sequence,legacySequence);assert.equal(repeated.state.generation_projection.source_output_hash,legacySource);assert.deepEqual(repeated.state.generation_projection.authoring_plan,legacyPlan);assert.equal(repeated.state.generation_projection.pipeline_trace,undefined);

  const repair=await f.service.call('advance_authoring',control,{human:true});assert.equal(repair.phase,'repairing',JSON.stringify(repair));
  const repairing=await runtime.runs.read(run.run_id);assert.deepEqual(repairing.state.generation_repair.previous_proposal,legacyPlan);
  await f.service.call('cancel',control);
});
test('generation stops on identical semantic feedback before spending another automatic patch', async t => {
  let proposal,plannerCalls=0;const repairContexts=[];const f=await fixture(t,{turn:async(settings,session)=>{
    if(plannerCalls>0){
      assert.match(session.prompt,new RegExp(`^Read ${AUTHORING_REPAIR_RESOURCE.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')} once`));
      const resource=await settings.toolBroker.call('read_workflow_resource',{path:AUTHORING_REPAIR_RESOURCE},`repair-${plannerCalls}`);
      repairContexts.push(JSON.parse(JSON.parse(resource.contentItems[0].text).text));
    }
    const output=plannerCalls++?{proposal:{contract:SEMANTIC_REPAIR_CONTRACT,purpose:'',upsert:{source_dispositions:[],requirement_assignments:[],records:[],lists:[],enums:[],activities:[structuredClone(repairContexts.at(-1).previous_proposal.activities[0])],approvals:[],sequences:[],parallels:[],choices:[]},remove:{source_dispositions:[],requirement_assignments:[],records:[],lists:[],enums:[],activities:[],approvals:[],sequences:[],parallels:[],choices:[]}}}:generatedProposal(proposal);
    const activity=output.proposal.contract===SEMANTIC_REPAIR_CONTRACT?output.proposal.upsert.activities[0]:output.proposal.activities[0];
    if(plannerCalls===1)activity.source_sections=['section_missing_from_source'];
    return {output:JSON.stringify(output),thread_id:'bad-graph',turn_id:'round',audit:{}};
  }});
  const source=join(f.root,'invalid-source');await mkdir(source);await writeFile(join(source,'SKILL.md'),'---\nname: invalid\ndescription: Review\n---\nReview result.');
  const {store}=await f.service.open();const pack=await importCoarseSkill(store,join(source,'SKILL.md'),{id:'invalid-source'});
  const origin={confidence:1,source_span:{resource:'source/SKILL.md',start_line:5,end_line:5}};
  proposal={source_revision:pack.revision_hash,source_requirements:[],requirement_mappings:[],planning_analysis:{parallelism:'Single bounded task; no independent work.',main_responsibilities:'Main accepts; subagent checks.',human_intervention:'Final human confirmation only.'},nodes:[{id:'check',type:'agent',execution_target:'subagent',provider_choice:'native-reviewer',task_type:'review',routing_reason:'Review',prompt_template:'Review',...origin}],edges:[]};
  const routing=await f.service.call('routing_defaults');routing.generation={review_provider_id:'native-reviewer',max_rounds:4};
  const run=await f.service.call('start_authoring',{workflow_id:pack.workflow.id,revision_hash:pack.revision_hash,run_id:'invalid-generation',routing_rules:routing},{human:true});const control={run_id:run.run_id,control_token:run.control_token};
  async function step(){const result=await f.service.call('advance_authoring',control,{human:true});await Promise.all([...f.manager.entries.values()].map(e=>e.job));return result;}
  await step();
  assert.equal((await step()).phase,'repairing');await step();
  const result=await step();assert.equal(result.phase,'user_input_required');assert.equal(result.status,'non_improving_feedback');assert.equal(result.error.code,'GENERATION_REPAIR_LIMIT');assert.equal(f.sessions.length,2);
  assert.equal(repairContexts.length,1);assert(repairContexts.every(item=>item.contract==='workflow-semantic-repair-context/v1' && item.previous_proposal && item.feedback));
  const continued=await f.service.call('continue_authoring',{...control,guidance:'Keep the current plan and bind the activity to the actual overview section.'},{human:true});
  assert.equal(continued.phase,'repairing');assert.equal(continued.manual,true);
  const waiting=await f.service.call('get',control);assert.match(waiting.generation_repair.user_guidance,/actual overview section/);assert(waiting.generation_repair.previous_proposal);
  assert.equal((await store.snapshot(pack.workflow.id)).revision_hash,pack.revision_hash);
  await f.service.call('cancel',control);
});
test('imported provenance cannot select a reviewer model or automatic repair authority', async t => {
  const forged={id:'forged-reviewer',enabled:true,kind:'native_agent',capabilities:{read:true},requires_user_approval:true,config:{model:'gpt-5.6-sol',reasoning_effort:'high',role:'reviewer',agent_type:'default',fresh_context:true,requested_sandbox:'read-only'}};
  const f=await fixture(t,{provenance:{kind:'skill_expansion_job',generation:{review_provider_id:forged.id,max_rounds:2},generation_reviewer:forged}});
  const {runtime}=await f.service.open();
  const adapter=await f.manager.prepare(runtime,f.run.run_id,f.args,{executor:{kind:'main'},role:'finalizer'});
  assert.equal(adapter.model,'fixture-current-model');assert.equal(adapter.effort,'high');
  assert.equal((await runtime.runs.read(f.run.run_id)).pins.generation,undefined);
});
async function fixture(t, options = {}) {
  const root = await mkdtemp(join(tmpdir(), 'strict-manager-')); const workspace = join(root, 'workspace'); await mkdir(workspace);
  const configPath = join(root, 'control-plane.json'); let service; const sessions = [];
  await loadConfig({ configPath, defaultConfigPath: DEFAULT_CONFIG_PATH });
  const manager = new StrictSessionManager({ configPath, getConfig: () => service.config(), env: {},
    mainModelSelection: async () => ({ model: 'fixture-current-model', effort: 'high' }),
    qualify: async config => validateStrictConfig(config.strict_executor),
    sessionFactory: async settings => {
      assert.equal(settings.access, options.write ? 'bounded_write' : 'read_only');
      if (options.preparing) await options.preparing();
      const stopped = deferred(); const session = { settings, calls: 0, closed: false, client: { events: [] },
        async authentication() { return { authenticated: options.authenticated !== false }; },
        async turn(prompt, turnOptions) {
          session.calls++; session.prompt = prompt; session.turnOptions = turnOptions;
          if (options.turn) {
            const result=await options.turn(settings, session, stopped.promise);
            // Legacy fixtures describe only the semantic graph.  Simulate the
            // v4 generator's required contract envelope without changing the
            // individual routing assertions.
            try { const envelope=JSON.parse(result.output); const value=typeof envelope?.proposal_json==='string'?JSON.parse(envelope.proposal_json):envelope; if (options.fixtureProjection !== false && Array.isArray(value?.nodes)) { value.required_executables ??=[]; for(const node of value.nodes) if(['agent','tool','human_gate'].includes(node.type)) { node.input_bindings ??=node.type==='agent'?{task:'/inputs/task'}:{}; node.resource_refs ??=['source/SKILL.md']; node.requirement_ids ??=[]; } result.output=JSON.stringify(typeof envelope?.proposal_json==='string'?generatedProposal(value):value); } } catch { /* non-JSON fixture is tested elsewhere */ }
            return result;
          }
          const resource = await settings.toolBroker.call('read_workflow_resource', { path: 'pinned.txt' }, 'resource-read');
          assert.equal(JSON.parse(resource.contentItems[0].text).text, 'Immutable task instructions');
          return { output: 'Synthetic result', thread_id: 'fixture-thread', turn_id: 'fixture-turn', audit: { fixture: true } };
        },
        async close() {
          if (options.close) return options.close(settings, session, stopped);
          session.closed = true; settings.toolBroker.revoke(); stopped.resolve();
        },
      }; sessions.push(session);
      await settings.onSessionOwned?.(session);
      if (options.setupFailure) {
        const setupError = Object.assign(new Error('Synthetic session initialization failure'), { code: 'SYNTHETIC_SESSION_SETUP' });
        try { await session.close(); }
        catch (cleanupError) {
          throw Object.assign(new AggregateError([setupError, cleanupError], 'Synthetic setup/cleanup failure'), {
            code: 'STRICT_SESSION_SETUP_FAILED', retained_at: join(root, 'fake-profile'),
          });
        }
        throw setupError;
      }
      await settings.onProfilePrepared({ home: join(root, 'fake-profile'), binary_sha256: 'a'.repeat(64) });
      return session;
    },
  });
  service = new WorkflowService({ configPath, defaultConfigPath: DEFAULT_CONFIG_PATH, env: {}, capabilities: { strictManager: manager } });
  await service.call('migrate_v6', {}, { human: true });
  const config = await service.config(); config.strict_executor = validateStrictConfig({ enabled: true, codex_binary: join(root, 'never-executed'), binary_sha256: 'a'.repeat(64), authentication: { mode: options.authMode ?? 'managed_chatgpt' } });
  await saveConfig(config, { configPath });
  const provider = config.providers.find(item => item.enabled && item.kind === 'native_agent');
  const workflow = { ...createDraft('strict-test', 'Strict manager test'), status: 'ready', finalization: { required: true, node_id: 'final' } };
  const common = { type: 'agent', access: options.write ? 'bounded_write' : 'read_only', ...(options.write ? { path_scope: ['out.txt'] } : {}), approval: { required: false }, retry: { max_attempts: 1 }, input_bindings: {}, prompt_template: '{{task}}', resources: ['pinned.txt'] };
  const workId=options.workId ?? 'work';
  workflow.nodes = [{ id: 'start', type: 'start' }, { ...common, id: workId, role: provider.config.role, executor: { kind: 'provider', provider_id: provider.id }, ...(options.schema ? { outputs_schema: options.schema } : {}) },
    { ...common, id: 'final', role: 'finalizer', access: 'read_only', executor: { kind: 'main' } }, { id: 'end', type: 'end' }];
  workflow.edges = [['start', workId], [workId, 'final'], ['final', 'end']].map(([source, target]) => ({ id: source + '-' + target, source, target }));
  await service.call('create', { workflow, ...(options.provenance ? {provenance:options.provenance} : {}), resources: { 'pinned.txt': 'Immutable task instructions' } }, {human:true});
  const run = await service.call('start', { workflow_id: workflow.id, workspace, access: options.write ? 'bounded_write' : 'read_only', ...(options.write ? { allowed_paths: ['out.txt'] } : {}), main_actor: 'root', inputs: { task: 'Synthetic only' } });
  const claim = async (node = workId) => {
    const {runtime}=await service.open(),record=await runtime.runs.read(run.run_id);
    const claimArgs={run_id:run.run_id,control_token:run.control_token,node_id:node,owner:node==='final'?'root':'worker',request_id:'claim-'+node};
    const lease = record.pins.root.workflow.nodes.find(item=>item.id===node)?.executor?.kind==='main'
      ? await runtime.claimHostMain(run.run_id,claimArgs)
      : await service.call('claim_node',claimArgs);
    return { run_id: run.run_id, control_token: run.control_token, node_id: node, attempt_id: lease.attempt_id, lease_token: lease.lease_token };
  };
  const args = await claim();
  const entry = args => manager.entries.get(args.run_id + '/' + args.attempt_id);
  t.after(async () => { await manager.close(); assert(resolve(root).startsWith(resolve(tmpdir()))); await rm(root, { recursive: true, maxRetries: 3, retryDelay: 100 }); });
  return { root, workspace, configPath, service, manager, sessions, run, claim, args, entry };
}

test('Strict settings are opt-in, reject secrets/unknown fields and verify selected executable integrity', async () => {
  assert.equal(validateStrictConfig().enabled, false);
  assert.equal(validateStrictConfig().authentication.mode, 'host_chatgpt');
  assert.throws(() => validateStrictConfig({ authentication: { api_key: 'secret' } }), { code: 'STRICT_CONFIG' });
  assert.throws(() => validateStrictConfig({ enabled: true }), { code: 'STRICT_CONFIG' });
  assert.equal(validateStrictConfig({ main_model: 'gpt-5.6-luna' }).main_model, 'gpt-5.6-luna');
  assert.equal(validateStrictConfig({ main_model: 'future-model', main_reasoning_effort: 'medium' }).main_model, 'future-model');
  assert.equal(validateStrictConfig().main_model, '');
  assert.equal(validateStrictConfig().main_reasoning_effort, '');
  assert.throws(() => validateStrictConfig({ main_model: 'bad model' }), { code: 'STRICT_CONFIG' });
  assert.throws(() => validateStrictConfig({ main_reasoning_effort: 'bad effort' }), { code: 'STRICT_CONFIG' });
  await assert.rejects(qualifiedStrictSettings({ strict_executor: { enabled: true, codex_binary: resolve('fake.exe'), binary_sha256: 'a'.repeat(64) } }), { code: 'CODEX_BINARY_MISSING' });
});

test('selected distribution file pins detect missing and changed actual companions', async t => {
  const root = await mkdtemp(join(tmpdir(), 'codex-distribution-'));
  t.after(async () => { assert(resolve(root).startsWith(resolve(tmpdir()))); await rm(root, { recursive: true, force: true }); });
  const binary = join(root, 'codex.exe');
  const names = ['codex-code-mode-host.exe', 'codex-command-runner.exe', 'codex-windows-sandbox-setup.exe'];
  const bytes = Object.fromEntries(['codex.exe', ...names].map(name => [name, Buffer.from(`fixture:${name}`)]));
  const expected = { sha256: digest(bytes['codex.exe']), companions: Object.fromEntries(names.map(name => [name, digest(bytes[name])])) };
  await writeFile(binary, bytes['codex.exe']);
  await assert.rejects(verifyCodexDistribution(binary, expected), { code: 'CODEX_COMPANION_MISSING' });
  for (const name of names) await writeFile(join(root, name), bytes[name]);
  await verifyCodexDistribution(binary, expected);
  await writeFile(join(root, names[0]), 'changed Code Mode host');
  await assert.rejects(verifyCodexDistribution(binary, expected), { code: 'CODEX_COMPANION_CHANGED' });
  await writeFile(join(root, names[0]), bytes[names[0]]);
  await rm(join(root, names[1]));
  await assert.rejects(verifyCodexDistribution(binary, expected), { code: 'CODEX_COMPANION_MISSING' });
});

function protocolFixture() {
  const params = {
    initialize: ['clientInfo', 'capabilities'], 'account/read': ['refreshToken'], 'config/read': ['includeLayers'],
    'model/list': ['includeHidden', 'limit'], 'skills/list': ['cwds', 'forceReload'],
    'thread/start': ['cwd', 'model', 'modelProvider', 'sandbox', 'config', 'dynamicTools', 'ephemeral', 'allowProviderModelFallback'],
    'turn/start': ['threadId', 'input', 'effort', 'outputSchema'], 'turn/interrupt': ['threadId', 'turnId'],
    'thread/read': ['threadId', 'includeTurns'], 'thread/list': ['parentThreadId', 'sourceKinds', 'modelProviders', 'useStateDbOnly', 'limit'],
    'thread/turns/list': ['threadId', 'itemsView', 'sortDirection', 'limit'],
    'command/exec': ['command', 'cwd', 'env', 'disableOutputCap', 'disableTimeout', 'sandboxPolicy', 'processId', 'streamStdin', 'streamStdoutStderr', 'timeoutMs'],
    'command/exec/write': ['deltaBase64', 'closeStdin', 'processId'], 'command/exec/terminate': ['processId'],
  };
  const methods = entries => ({ oneOf: entries.map(([method, fields]) => ({ properties: {
    method: { enum: [method] }, params: { type: 'object', properties: Object.fromEntries(fields.map(field => [field, {}])) },
  } })) });
  const client = methods(Object.entries(params));
  client.definitions = { DynamicToolSpec: { type: 'object', properties: { name: {}, description: {}, inputSchema: {} } } };
  return { ClientRequest: client, ServerRequest: methods([['item/tool/call', ['threadId', 'turnId', 'callId', 'tool', 'arguments']]]),
    ServerNotification: methods([['turn/completed', []], ['item/completed', []], ['thread/tokenUsage/updated', []]]) };
}

async function qualificationFixture(t, name = 'codex') {
  const root = await mkdtemp(join(tmpdir(), 'portable-codex-'));
  t.after(() => rm(root, { recursive: true, force: true }));
  const directory = join(root, 'distribution'); await mkdir(directory);
  const binary = join(directory, name), bytes = Buffer.from(`selected real distribution fixture: ${name}`);
  await writeFile(binary, bytes);
  const calls = [], schemas = protocolFixture(), env = { CODEX_HOME: root };
  const clientFactory = (_binary, { home }) => ({ initialized() {}, async close() { calls.push('close'); },
    async call(method) {
      calls.push(method);
      if (method === 'initialize') return { userAgent: 'fixture-cli arbitrary-release' };
      if (method === 'account/read') return { account: { type: 'chatgpt' }, requiresOpenaiAuth: true };
      if (method === 'config/read') return { config: {} };
      if (method === 'model/list') return { data: [{ model: 'fixture-model', supportedReasoningEfforts: [] }], nextCursor: null };
      if (method === 'skills/list') return { data: [{ cwd: home, skills: [], errors: [] }] };
      assert.fail(`Qualification must not call ${method}`);
    } });
  const settings = validateStrictConfig({ enabled: true, codex_binary: binary, binary_sha256: digest(bytes) });
  return { root, binary, settings, schemas, calls, options: { env, schemaReader: async () => schemas, clientFactory, cache: new Map() } };
}

test('selected Codex distributions qualify by actual protocol without a shipped release or platform hash', async t => {
  for (const name of ['codex', 'codex.exe']) {
    const f = await qualificationFixture(t, name);
    assert.equal(await qualifiedCodexBinary(f.settings, f.options), f.settings);
    assert.deepEqual(f.calls, ['initialize', 'account/read', 'config/read', 'model/list', 'skills/list', 'close']);
    const before = [...f.calls];
    await qualifiedCodexBinary(f.settings, f.options);
    assert.deepEqual(f.calls, before, 'The same observed executable/profile reuses successful capability evidence');
    await writeFile(f.binary, 'changed selected executable');
    await assert.rejects(qualifiedCodexBinary(f.settings, f.options), { code: 'CODEX_BINARY_CHANGED' });
  }
});

test('missing required App Server capability rejects before thread or model effects', async t => {
  const f = await qualificationFixture(t);
  delete f.schemas.ClientRequest.oneOf.find(item => item.properties.method.enum[0] === 'turn/start').properties.params.properties.outputSchema;
  await assert.rejects(qualifiedCodexBinary(f.settings, f.options), error =>
    error.code === 'CODEX_CAPABILITY_UNSUPPORTED' && error.capability === 'turn/start.outputSchema');
  assert.deepEqual(f.calls, []);
});

test('qualification resolves selected executable aliases and negotiates tagged function tools', async t => {
  const f = await qualificationFixture(t), aliasDirectory = join(f.root, 'selected-distribution'), alias = join(aliasDirectory, 'codex');
  await symlink(join(f.root, 'distribution'), aliasDirectory, process.platform === 'win32' ? 'junction' : 'dir');
  f.settings.codex_binary = alias;
  f.schemas.ClientRequest.definitions.DynamicToolSpec = { oneOf: [{ properties: { name: {}, description: {}, inputSchema: {}, type: { enum: ['function'] } },
    required: ['name', 'description', 'inputSchema', 'type'] }] };
  await qualifiedCodexBinary(f.settings, f.options);
  const proof = codexQualification(f.settings);
  assert.equal(proof.selected_path, alias);assert.equal(proof.resolved_path, f.binary);
  assert.equal(proof.executable_sha256, f.settings.binary_sha256);assert.equal(proof.dynamic_tool_format, 'tagged_function');
  assert.equal(proof.model_calls, 0);
  await rm(aliasDirectory, { recursive: true }); const changed = join(f.root, 'changed-distribution'); await mkdir(changed);
  await writeFile(join(changed, 'codex'), 'different executable'); await symlink(changed, aliasDirectory, process.platform === 'win32' ? 'junction' : 'dir');
  await assert.rejects(qualifiedCodexBinary(f.settings, f.options), { code: 'CODEX_BINARY_CHANGED' });
});

test('qualification scopes exclude unrelated native continuation and execution capabilities', async t => {
  const f = await qualificationFixture(t);
  f.schemas.ClientRequest.oneOf = f.schemas.ClientRequest.oneOf.filter(item => !['thread/read', 'thread/list', 'thread/turns/list'].includes(item.properties.method.enum[0]));
  await qualifiedCodexBinary(f.settings, f.options);
  assert.equal(codexQualification(f.settings).scope, 'main');
  await qualifiedCodexBinary(f.settings, { ...f.options, scope: 'managed_native' });
  assert.equal(codexQualification(f.settings).scope, 'managed_native');
  f.calls.length = 0;
  const discovery = { ClientRequest: { oneOf: f.schemas.ClientRequest.oneOf.filter(item => ['initialize', 'skills/list'].includes(item.properties.method.enum[0])) } };
  await qualifiedCodexBinary(f.settings, { ...f.options, scope: 'discovery', schemaReader: async () => discovery });
  assert.deepEqual(f.calls, ['initialize', 'skills/list', 'close']);
  assert.equal(codexQualification(f.settings).scope, 'discovery');
});

test('Strict prepare qualification survives config revalidation and reaches actual launch arguments',async t=>{
  const f=await fixture(t),q=await qualificationFixture(t);
  const config=await f.service.config();
  config.strict_executor.codex_binary=q.binary;config.strict_executor.binary_sha256=q.settings.binary_sha256;
  await saveConfig(config,{configPath:f.service.configPath});
  f.manager.qualify=async current=>qualifiedCodexBinary(validateStrictConfig(current.strict_executor),q.options);
  await f.service.call('dispatch',f.args);await f.entry(f.args).job;
  assert.equal(f.sessions[0].settings.expectedBinaryPath,q.binary);
  assert.equal(f.sessions[0].settings.dynamicToolFormat,'untagged_function');
});

test('in-place Codex upgrade re-registers only the proved local executable before a new Run',async t=>{
  const f=await qualificationFixture(t),configPath=join(f.root,'control-plane.json');
  const service=new WorkflowService({configPath,defaultConfigPath:DEFAULT_CONFIG_PATH});
  await service.call('migrate_v6',{}, {human:true});
  const config=await service.config();
  config.strict_executor={...f.settings,binary_sha256:digest('prior release')};
  await saveConfig(config,{configPath});
  const original=structuredClone(config),qualify=async candidate=>qualifiedCodexBinary(validateStrictConfig(candidate.strict_executor),f.options);
  const saved=await refreshCodexRegistration({configPath,config,qualify,env:f.options.env});
  assert.equal(saved.strict_executor.binary_sha256,f.settings.binary_sha256);
  assert.equal(saved.strict_executor.codex_binary,original.strict_executor.codex_binary);
  assert.deepEqual(saved.providers,original.providers);
  assert.deepEqual(saved.strict_executor.authentication,original.strict_executor.authentication);
  const audit=JSON.parse(await readFile(join(f.root,'codex-runtime-registration.json'),'utf8'));
  assert.equal(audit.status,'registered');assert.equal(audit.qualification.model_calls,0);
  assert.equal(audit.previous_sha256,original.strict_executor.binary_sha256);
  assert.equal(audit.executable_sha256,f.settings.binary_sha256);
  const count=f.calls.length;
  await refreshCodexRegistration({configPath,config:saved,qualify,env:f.options.env});
  assert.equal(f.calls.length,count);
  await writeFile(f.binary,'changed during owned attempt');
  await assert.rejects(qualifiedCodexBinary(validateStrictConfig(saved.strict_executor),f.options),{code:'CODEX_BINARY_CHANGED'});
});

test('unqualified Codex upgrade and concurrent user edits never overwrite local registration',async t=>{
  const f=await qualificationFixture(t),configPath=join(f.root,'control-plane.json');
  const service=new WorkflowService({configPath,defaultConfigPath:DEFAULT_CONFIG_PATH});
  await service.call('migrate_v6',{}, {human:true});
  const config=await service.config();
  config.strict_executor={...f.settings,binary_sha256:digest('old installed release')};
  await saveConfig(config,{configPath});
  const before=await readFile(configPath,'utf8');
  await assert.rejects(refreshCodexRegistration({configPath,config,qualify:async()=>{throw Object.assign(new Error('Unsupported output contract'),{code:'CODEX_CAPABILITY_UNSUPPORTED'});}}),{code:'CODEX_CAPABILITY_UNSUPPORTED'});
  assert.equal(await readFile(configPath,'utf8'),before);
  const qualify=async candidate=>{
    const changed=structuredClone(config);changed.global.max_prompt_chars++;
    await saveConfig(changed,{configPath});
    return qualifiedCodexBinary(validateStrictConfig(candidate.strict_executor),f.options);
  };
  await assert.rejects(refreshCodexRegistration({configPath,config,qualify,env:f.options.env}),/configuration changed/);
  const retained=await loadConfig({configPath,defaultConfigPath:DEFAULT_CONFIG_PATH});
  assert.equal(retained.strict_executor.binary_sha256,config.strict_executor.binary_sha256);
  assert.equal(retained.global.max_prompt_chars,config.global.max_prompt_chars+1);
});

test('removed Codex installation is rediscovered, qualified and durably registered without changing Providers',async t=>{
  const f=await qualificationFixture(t),configPath=join(f.root,'control-plane.json');
  const service=new WorkflowService({configPath,defaultConfigPath:DEFAULT_CONFIG_PATH});
  await service.call('migrate_v6',{}, {human:true});
  const config=await service.config();
  config.strict_executor={...f.settings,codex_binary:join(f.root,'removed-install','codex')};
  await saveConfig(config,{configPath});
  let discoveries=0;
  const saved=await refreshCodexRegistration({configPath,config,env:f.options.env,
    discover:async()=>{discoveries++;return {binary:f.binary};},
    qualify:candidate=>qualifiedCodexBinary(validateStrictConfig(candidate.strict_executor),f.options)});
  assert.equal(discoveries,1);assert.equal(saved.strict_executor.codex_binary,f.binary);
  assert.deepEqual(saved.providers,config.providers);
  const audit=JSON.parse(await readFile(join(f.root,'codex-runtime-registration.json'),'utf8'));
  assert.equal(audit.reason,'stale_installation_rediscovered');
  assert.equal(audit.previous_selected_path,config.strict_executor.codex_binary);
  assert.equal(audit.qualification.model_calls,0);
});

test('qualification preserves authentication checks and closes failed read-only probes without caching them', async t => {
  const f = await qualificationFixture(t), config = { strict_executor: { ...f.settings,
    authentication: { mode: 'environment_api_key', api_key_env: 'PORTABLE_CODEX_TEST_KEY' } } };
  await assert.rejects(qualifiedStrictSettings(config, f.options.env, f.options), { code: 'CODEX_CREDENTIAL_MISSING' });
  assert.deepEqual(f.calls, []);
  let closes = 0, reads = 0;
  f.options.clientFactory = () => ({ initialized() {}, async close() { closes++; }, async call(method) {
    reads++;
    if (method === 'initialize') return {};
    throw Object.assign(new Error('unsupported account RPC'), { rpc_code: -32601 });
  } });
  for (let attempt = 0; attempt < 2; attempt++) await assert.rejects(qualifiedCodexBinary(f.settings, f.options),
    error => error.code === 'CODEX_CAPABILITY_PROBE_FAILED' && error.capability === 'account/read' && error.rpc_code === -32601);
  assert.equal(reads, 4);assert.equal(closes, 2);
});

test('Strict manager owns the exact close-capable session before initialization can fail', async t => {
  let allowClose = false; let closeCalls = 0;
  const f = await fixture(t, {
    setupFailure: true,
    close: async (settings, session, stopped) => {
      closeCalls++;
      if (!allowClose) throw Object.assign(new Error('Synthetic profile cleanup failure'), { code: 'SYNTHETIC_PROFILE_RETAINED' });
      session.closed = true; settings.toolBroker.revoke(); stopped.resolve();
    },
  });
  await assert.rejects(f.service.call('dispatch', f.args), error => error instanceof AggregateError && error.code === 'STRICT_FAILURE_INCOMPLETE');
  const entry = f.entry(f.args);
  assert.equal(entry.status, 'audit_or_cleanup_failed');
  assert.equal(entry.cleanupPending, true);
  assert.equal(entry.session, f.sessions[0], 'manager must retain the exact owner published before initialization');
  assert(closeCalls >= 2, 'factory rollback and manager cleanup both attempted the same owner');
  allowClose = true;
  await f.manager.stopRun(f.run.run_id);
  assert.equal(entry.status, 'audit_or_cleanup_failed', 'cleanup may settle without erasing the original diagnostic');
  assert.equal(entry.cleanupPending, false);
  assert.equal(entry.session, null);
});

test('an ordinary node named expand keeps its declared output contract',async t=>{
  const schema={type:'object',required:['value'],additionalProperties:false,properties:{value:{type:'string'}}};
  const f=await fixture(t,{workId:'expand',schema,turn:async()=>({output:JSON.stringify({value:'ordinary-workflow-output'}),thread_id:'ordinary-expand',turn_id:'turn',audit:{}})});
  await f.service.call('dispatch',f.args);await f.entry(f.args).job;
  assert.deepEqual((await f.service.call('get',f.args)).nodes.expand.output,{value:'ordinary-workflow-output'});
});

test('host authentication failure closes the node without offering managed login or starting a turn', async t => {
  const f = await fixture(t, { authenticated: false, authMode: 'host_chatgpt' });
  await assert.rejects(f.service.call('dispatch', f.args), { code: 'HOST_AUTH_UNAVAILABLE' });
  assert.equal(f.sessions[0].calls, 0);
  assert.equal(f.sessions[0].closed, true);
  assert.equal(f.entry(f.args).status, 'failed');
});

test('human recovery fences and closes a waiting Strict session with rotated audit authority', async t => {
  const f = await fixture(t, { authenticated: false }); await f.service.call('dispatch', f.args);
  const state = await f.service.call('get', { run_id: f.run.run_id });
  const adopted = await f.service.call('adopt_run', { run_id: f.run.run_id, expected_sequence: state.sequence, reason: 'Synthetic lost console', main_actor: 'human-console' }, { human: true });
  assert.deepEqual(adopted.recovery_errors, []); assert.equal(adopted.nodes.work.status, 'interrupted'); assert(f.sessions[0].closed);
  assert.equal(f.entry(f.args).status, 'stopped');
  await assert.rejects(f.service.call('strict_login', f.args, { human: true }), { code: 'RUN_AUTHORITY' });
  await assert.rejects(f.service.call('recover_strict_result', { run_id: adopted.run_id, control_token: adopted.control_token, node_id: 'work', attempt_id: f.args.attempt_id }), { code: 'STRICT_RESULT_PENDING' });
  assert.equal(f.sessions[0].calls, 0);
});

test('a durable final Strict proposal survives controller loss and reattaches without another model call', async t => {
  const f = await fixture(t); await f.service.call('dispatch', f.args); await f.entry(f.args).job;
  const final = await f.claim('final'); await f.service.call('dispatch', final); await f.entry(final).job;
  const before = await f.service.call('get', { run_id: f.run.run_id });
  const adopted = await f.service.call('adopt_run', { run_id: f.run.run_id, expected_sequence: before.sequence, reason: 'Synthetic final review recovery', main_actor: 'human-console' }, { human: true }); assert.deepEqual(adopted.recovery_errors, []);
  const restored = await f.service.call('recover_strict_result', { run_id: adopted.run_id, control_token: adopted.control_token, node_id: 'final', attempt_id: final.attempt_id });
  await f.service.call('resume', { run_id: adopted.run_id, control_token: adopted.control_token });
  const args = { ...restored.envelope, control_token: adopted.control_token };
  assert.equal((await f.service.call('collect_strict', args)).final_acceptance_required, true);
  const completed = await f.service.call('collect_strict', { ...args, accepted: true }); assert.equal(completed.status, 'succeeded');
  assert.equal(f.sessions.reduce((sum, session) => sum + session.calls, 0), 2); assert.equal(completed.nodes.final.attempts.length, 1);
});

test('Strict child service dispatch reads its pinned Pack and collects only accepted output into its parent', async t => {
  const f = await fixture(t); const childPack = await f.service.call('read', { workflow_id: 'strict-test' });
  const parentWorkflow = structuredClone(childPack.workflow); parentWorkflow.id = 'strict-parent';
  Object.assign(parentWorkflow.nodes[1], { type: 'subworkflow', executor: { kind: 'subworkflow' }, input_bindings: { task: '/inputs/task' },
    subworkflow: { workflow_id: childPack.workflow.id, revision_pin: childPack.revision_hash, output_bindings: { child_result: '/output' } } });
  await f.service.call('create', { workflow: parentWorkflow, resources: { 'pinned.txt': 'Immutable task instructions' } }, {human:true});
  const parent = await f.service.call('start', { workflow_id: parentWorkflow.id, workspace: f.workspace, access: 'read_only', main_actor: 'root', inputs: { task: 'Nested synthetic task' } });
  const claimFor = async (run, nodeId) => {
    const {runtime}=await f.service.open(),record=await runtime.runs.read(run.run_id);
    const claimArgs={run_id:run.run_id,control_token:run.control_token,node_id:nodeId,owner:nodeId==='final'?'root':'worker',request_id:'claim-'+nodeId};
    const lease = record.pins.root.workflow.nodes.find(item=>item.id===nodeId)?.executor?.kind==='main'
      ? await runtime.claimHostMain(run.run_id,claimArgs)
      : await f.service.call('claim_node',claimArgs);
    return { run_id: run.run_id, control_token: run.control_token, node_id: nodeId, attempt_id: lease.attempt_id, lease_token: lease.lease_token };
  };
  const parentArgs = await claimFor(parent, 'work');
  await f.service.call('delete', { workflow_id: childPack.workflow.id, expected_revision: childPack.revision_hash });
  const child = (await f.service.call('dispatch', parentArgs)).child;
  assert.equal(f.sessions.length, 0);
  for (const nodeId of ['work', 'final']) {
    const request = await claimFor(child, nodeId); await f.service.call('dispatch', request); await f.entry(request).job;
    if (nodeId === 'final') await f.service.call('collect_strict', { ...request, accepted: true });
  }
  const collected = await f.service.call('collect_subworkflow', parentArgs);
  assert.deepEqual(collected.nodes.work.output, { child_result: { text: 'Synthetic result' } }); assert.equal(f.sessions.length, 2);
  assert(f.sessions.every(session => !session.prompt.includes(parent.control_token) && !session.prompt.includes(child.control_token)));
  const finalArgs = await claimFor(parent, 'final'); await f.service.call('dispatch', finalArgs); await f.entry(finalArgs).job;
  assert.equal((await f.service.call('collect_strict', { ...finalArgs, accepted: true })).status, 'succeeded');
});

test('streamed output is a bounded unverified preview and only progress metadata enters the durable journal', async t => {
  const ready = deferred(); const release = deferred(); const marker = 'PREVIEW_ONLY_DO_NOT_JOURNAL_';
  t.after(() => release.resolve());
  const f = await fixture(t, { async turn(settings) {
    await settings.onOutput({ delta: marker + 'x'.repeat(40000) });
    await settings.onOutput({ delta: 'TAIL' }); ready.resolve(); await release.promise;
    return { output: 'Accepted durable result', thread_id: 'fixture-thread', turn_id: 'fixture-turn', audit: { fixture: true } };
  } });
  await f.service.call('dispatch', f.args);
  await Promise.race([ready.promise, f.entry(f.args).job.then(() => { throw new Error(JSON.stringify(f.entry(f.args).error ?? 'Turn ended before preview')); })]);
  const live = await f.service.call('strict_status', f.args);
  assert.equal(live.output_preview.text.length, 32768); assert(live.output_preview.text.endsWith('TAIL'));
  assert.equal(live.output_preview.characters, marker.length + 40004); assert.equal(live.output_preview.truncated, true);
  assert.equal(live.output_preview.verified, false); assert.equal(live.output_preview.durable, false);
  const { runtime } = await f.service.open(); const events = JSON.stringify((await runtime.runs.read(f.run.run_id)).events);
  assert(events.includes('output_progress')); assert(!events.includes(marker)); assert(!events.includes('TAIL'));
  release.resolve(); await f.entry(f.args).job;
  assert.deepEqual((await f.service.call('get', f.args)).nodes.work.output, { text: 'Accepted durable result' });
});
test('authoring repair output budget derives from its prior plan and streaming stops before the durable result ceiling',async t=>{
  const smallPlan={activities:[{key:'repair',instructions:'Patch this semantic node.'}]};
  assert.equal(strictOutputByteBudget(),EXECUTOR_RESULT_MAX_BYTES);
  assert.equal(strictOutputByteBudget({previous_proposal:smallPlan}),16*1024);
  const f=await fixture(t,{turn:async settings=>{
    await settings.onOutput({delta:'x'.repeat(EXECUTOR_RESULT_MAX_BYTES)});
    await settings.onOutput({delta:'x'});
    throw new Error('The streaming budget did not stop output');
  }});
  await f.service.call('dispatch',f.args);await f.entry(f.args).job;
  const state=await f.service.call('get',f.args);
  assert.equal(state.nodes.work.error.code,'STRICT_OUTPUT_BUDGET');
  assert.equal(state.nodes.work.attempts[0].result_proposal,undefined);
  assert.equal(f.sessions[0].closed,true);
  const anomaly=state.nodes.work.attempts[0].executor_events.find(event=>event.kind==='output_anomaly');
  assert(anomaly);
  const {runtime}=await f.service.open();
  const diagnostic=JSON.parse(await runtime.runs.readArtifact(f.run.run_id,{artifact:anomaly.metadata.artifact,sha256:anomaly.metadata.sha256,bytes:anomaly.metadata.bytes}));
  assert.equal(diagnostic.streamed_bytes,EXECUTOR_RESULT_MAX_BYTES+1);
  assert.equal(diagnostic.budget_bytes,EXECUTOR_RESULT_MAX_BYTES);
  assert.equal(diagnostic.last_characters.length,4096);
  assert.equal(diagnostic.last_delta_sha256.length,2);
});
test('Strict dispatch runs pinned resources exactly once and keeps final acceptance in the main controller', async t => {
  const f = await fixture(t); const dispatched = await f.service.call('dispatch', f.args);
  assert.equal(dispatched.dispatched, true); await f.entry(f.args).job;
  assert.equal((await f.service.call('strict_status', f.args)).status, 'succeeded');
  assert.equal(f.sessions[0].prompt.includes(f.run.control_token), false); assert.equal(f.sessions[0].closed, true);
  assert.equal((await f.service.call('dispatch', f.args)).idempotent, true); assert.equal(f.sessions[0].calls, 1);
  const final = await f.claim('final'); await f.service.call('dispatch', final); await f.entry(final).job;
  const proposed = await f.service.call('collect_strict', final); assert.equal(proposed.final_acceptance_required, true);
  assert.notEqual((await f.service.call('get', f.args)).status, 'succeeded');
  await assert.rejects(f.service.call('collect_strict', { ...final, control_token: 'wrong', accepted: true }), { code: 'RUN_AUTHORITY' });
  assert.equal((await f.service.call('collect_strict', { ...final, accepted: true })).status, 'succeeded');
  assert.equal((await f.service.call('collect_strict', { ...final, accepted: true })).idempotent, true);
});

test('settled Strict entries release heavyweight session references while retaining status', async t => {
  const f = await fixture(t);
  await f.service.call('dispatch', f.args);
  await f.entry(f.args).job;
  const entry = f.entry(f.args);
  assert.equal(entry.status, 'succeeded');
  assert.equal(entry.session, null);
  assert.equal(entry.broker, null);
  assert.equal(entry.envelope, null);
  assert.equal(entry.prompt, null);
  assert.equal(entry.runtime, null);
  assert.equal(entry.job, null);
  assert.equal((await f.service.call('strict_status', f.args)).status, 'succeeded');
});

test('pending managed authentication exposes status without URLs or dispatching a model; cancellation closes it', async t => {
  const f = await fixture(t, { authenticated: false }); await f.service.call('dispatch', f.args);
  assert.equal((await f.service.call('strict_status', f.args)).status, 'auth_required'); assert.equal(f.sessions[0].calls, 0);
  await assert.rejects(f.service.call('strict_login', f.args), { code: 'HUMAN_AUTHENTICATION_REQUIRED' });
  const cancelled = await f.service.call('cancel', f.args); assert.equal(cancelled.status, 'cancelled');
  assert.equal(f.sessions[0].closed, true); assert.equal(cancelled.nodes.work.attempts[0].dispatch.cancellation_pending, false);
});

test('cancellation fences a pending model write before reporting its local session stopped', async t => {
  const entered = deferred(); let writeError;
  const f = await fixture(t, { write: true, turn: async (settings, _session, stopped) => {
    entered.resolve(); await stopped;
    try { await settings.toolBroker.call('materialize_workflow_resource', { path: 'pinned.txt', destination: 'out.txt', expected_sha256: null }, 'late-write'); }
    catch (error) { writeError = error; throw error; }
  } });
  await f.service.call('dispatch', f.args); await entered.promise;
  const state = await f.service.call('cancel', f.args);
  assert.equal(state.status, 'cancelled'); assert.equal(writeError.code, 'CODEX_BROKER_REVOKED');
  await assert.rejects(readFile(join(f.workspace, 'out.txt')), { code: 'ENOENT' });
});

test('pause permits an already running node to finish, while schema violations fail explicitly', async t => {
  const entered = deferred(); const released = deferred();
  const f = await fixture(t, { turn: async () => { entered.resolve(); await released.promise; return { output: 'Finished', thread_id: 't', turn_id: 'u', audit: {} }; } });
  await f.service.call('dispatch', f.args); await entered.promise; await f.service.call('pause', f.args); released.resolve(); await f.entry(f.args).job;
  const state = await f.service.call('get', f.args); assert.equal(state.status, 'paused'); assert.equal(state.nodes.work.status, 'succeeded');
  const bad = await fixture(t, { schema: { type: 'object', required: ['ok'], properties: { ok: { type: 'boolean' } }, additionalProperties: false } });
  await bad.service.call('dispatch', bad.args); await bad.entry(bad.args).job;
  assert.equal((await bad.service.call('get', bad.args)).nodes.work.error.code, 'STRICT_OUTPUT_JSON');
});

test('a durable result survives completion failure and can be collected without another invocation or retry', async t => {
  const entered = deferred(); const released = deferred();
  const f = await fixture(t, { turn: async () => { entered.resolve(); await released.promise; return { output: 'Preserved', thread_id: 't', turn_id: 'u', audit: {} }; } });
  await f.service.call('dispatch', f.args); await entered.promise;
  const runsDirectory = f.entry(f.args).runtime.runs.directory(f.run.run_id);
  f.entry(f.args).runtime.completeNode = async () => { throw Object.assign(new Error('Synthetic commit fault'), { code: 'SYNTHETIC_COMMIT_FAULT' }); };
  released.resolve(); await f.entry(f.args).job;
  assert.equal((await f.service.call('strict_status', f.args)).status, 'result_commit_failed');
  const state = await f.service.call('collect_strict', f.args); assert.equal(state.nodes.work.status, 'succeeded');
  assert.equal(state.nodes.work.attempts.length, 1); assert.equal(f.sessions[0].calls, 1);
  const proposal = state.nodes.work.attempts[0].result_proposal;
  await writeFile(join(runsDirectory, proposal.artifact), '{}');
  await assert.rejects(f.service.call('collect_strict', f.args), { code: 'EXECUTOR_RESULT_CORRUPT' });
});

test('cancelling during session preparation waits for that owned preparation to settle', async t => {
  const entered = deferred(); const released = deferred();
  const f = await fixture(t, { preparing: async () => { entered.resolve(); await released.promise; } });
  const dispatch = f.service.call('dispatch', f.args); const dispatchFailure = assert.rejects(dispatch, { code: 'STRICT_SESSION_STOPPED' });
  await entered.promise; const stopping = deferred(); const originalStop = f.manager.stopRun.bind(f.manager);
  f.manager.stopRun = id => { stopping.resolve(); return originalStop(id); };
  const cancel = f.service.call('cancel', f.args); const completed = Promise.all([dispatchFailure, cancel]);
  // Fence publication is observed before permitting session setup to return.
  await stopping.promise;
  try { assert.equal((await f.service.call('get', f.args)).status, 'cancelled'); } finally { released.resolve(); }
  const results = await completed; assert.equal(results[1].status, 'cancelled'); assert.equal(f.sessions[0].closed, true);
  assert.equal(f.sessions[0].calls, 0);
});

test('orphan cleanup selects exact Run/node/attempt ownership and refuses a live owner', async t => {
  const f = await fixture(t, { authenticated: false }); await f.service.call('dispatch', f.args);
  await f.service.call('cancel', f.args); await mkdir(f.manager.parent, { recursive: true });
  const active = join(f.manager.parent, 'strict-node-active'); const orphan = join(f.manager.parent, 'strict-node-orphan'); const other = join(f.manager.parent, 'strict-node-other');
  const supported = ['win32', 'linux'].includes(process.platform);
  if (!supported) await assert.rejects(processIdentity(process.pid), { code: 'PROCESS_IDENTITY_UNSUPPORTED' });
  const identity = supported ? await processIdentity(process.pid) : { pid: process.pid, started: 'synthetic-unqualified', executable: process.execPath };
  for (const home of [active, orphan, other]) {
    await mkdir(home);
    const parentIdentity = home === active ? identity : { pid: 999999999, started: 'synthetic-dead-parent', executable: process.execPath };
    await writeFile(join(home, 'owner.json'), JSON.stringify({ schema_version: 1, token: randomUUID(), parent_pid: parentIdentity.pid, parent_identity: parentIdentity, child_pid: null,
      owner: { run_id: home === other ? 'another-run' : f.run.run_id, node_id: f.args.node_id, attempt_id: f.args.attempt_id } }));
  }
  const result = await f.service.call('cleanup_strict_orphans', f.args);
  if (!supported) {
    assert.deepEqual(result.cleaned, []); assert.equal(result.blocked.length, 3);
    assert(result.blocked.every(item => item.code === 'PROCESS_IDENTITY_UNSUPPORTED'));
    for (const home of [active, orphan, other]) assert(await readFile(join(home, 'owner.json')));
    return;
  }
  assert.deepEqual(result.cleaned, [orphan]); assert(result.blocked.some(item => item.home === active && item.code === 'PROFILE_OWNER_ACTIVE'));
  assert.equal(result.resubmitted, false); await assert.rejects(readFile(join(orphan, 'owner.json')), { code: 'ENOENT' });
  assert(await readFile(join(other, 'owner.json'))); assert(await readFile(join(active, 'owner.json')));
});

test('selected-Provider expansion uses durable read-only execution and applies only an accepted exact-revision Draft', async t => {
  let proposal,calls=0;
  const f = await fixture(t, { turn: async settings => {
    assert.equal(settings.toolBroker.tools().some(tool => tool.name === 'write_workspace'), false);
    const packet = await settings.toolBroker.call('read_workflow_resource', { path: calls===0?'analysis/request.txt':'analysis/review-request.txt' }, 'read-plan');
    assert(JSON.parse(packet.contentItems[0].text).text.includes(proposal.source_revision));
    const reference = await settings.toolBroker.call('read_workflow_resource', { path: 'source/reference.md' }, 'read-pinned-reference');
    assert.equal(JSON.parse(reference.contentItems[0].text).text, 'The marker is PINNED_BLUE, not this entire document.');
    return { output: JSON.stringify(calls++===0?generatedProposal(proposal):checklist(proposal)), thread_id: 'planning-thread', turn_id: 'planning-turn', audit: {} };
  } });
  const source = join(f.root, 'expansion-source'); await mkdir(source);
  await writeFile(join(source, 'SKILL.md'), '---\nname: plan\ndescription: planning fixture\n---\nAnalyze the task and return a result.');
  await writeFile(join(source, 'reference.md'), 'The marker is PINNED_BLUE, not this entire document.');
  const { store,runtime } = await f.service.open(); const config = await f.service.config();
  const providers = config.providers.filter(item => item.enabled && item.kind === 'native_agent'); assert(providers.length >= 2);
  const pack = await importCoarseSkill(store, join(source, 'SKILL.md'), { id: 'source-draft', providerId: providers[0].id, role: providers[0].config.role });
  const origin = { confidence: 0.8, source_span: { resource: 'source/SKILL.md', start_line: 5, end_line: 5 } };
  proposal = { source_revision: pack.revision_hash, source_requirements:[], requirement_mappings:[], planning_analysis:{parallelism:'Single bounded task; no independent work.',main_responsibilities:'Main accepts; subagent checks.',human_intervention:'Final human confirmation only.'}, nodes: [{ id: 'analyze', type: 'agent', execution_target:'subagent',provider_choice:'native-luna',task_type: 'implementation', routing_reason: 'Routine bounded analysis', prompt_template: 'Analyze {{task}}', ...origin }],
    edges: [{ id: 'start-analyze', source: 'start', target: 'analyze', ...origin }, { id: 'analyze-final', source: 'analyze', target: 'final', ...origin }] };
  const originalRules = await f.service.call('routing_defaults');
  const plannerProvider=config.providers.find(item=>item.id===originalRules.generation.planner_provider_id);assert(plannerProvider);
  const planningWorkspace=join(f.root,'skill-generation-workspaces','job-planning-job');await mkdir(planningWorkspace,{recursive:true});
  const planning = await f.service.call('create_authoring_run', { workflow_id: pack.workflow.id, revision_hash: pack.revision_hash, provider_id: plannerProvider.id,
    run_id: 'planning-job', workspace: planningWorkspace, main_actor: 'root' });
  const pinnedAuthoring=await runtime.runs.read(planning.run_id);assert.equal(pinnedAuthoring.pins.root.provenance.review_contract_version,CONVERSION_CONTRACT.version);
  const editedRules = structuredClone(originalRules); editedRules.routes.implementation.provider_id = providers[1].id;
  await f.service.call('save_routing_rules', {routing_rules:editedRules,expected_rules:originalRules}, {human:true});
  await assert.rejects(f.service.call('save_routing_rules', {routing_rules:originalRules,expected_rules:originalRules}, {human:true}), {code:'ROUTING_SETTINGS_CONFLICT'});
  await writeFile(join(source, 'reference.md'), 'Changed after the planning Run was pinned');
  const apply = { run_id: planning.run_id, control_token: planning.control_token, workflow_id: pack.workflow.id, expected_revision: pack.revision_hash };
  await assert.rejects(f.service.call('apply_authoring_result', apply, {human:true}), { code: 'EXPANSION_ACCEPTANCE_REQUIRED' });
  let expanded;
  for (const node of ['expand','graph_assembly','execution_binding','deterministic_validation','final']) {
    const claimArgs={run_id:planning.run_id,control_token:planning.control_token,node_id:node,owner:node==='final'?'root':'planner',request_id:'claim-'+node};
    const planningRecord=await runtime.runs.read(planning.run_id);
    const lease = planningRecord.pins.root.workflow.nodes.find(item=>item.id===node)?.executor?.kind==='main'
      ? await runtime.claimHostMain(planning.run_id,claimArgs)
      : await f.service.call('claim_node',claimArgs);
    if (node === 'expand') assert.equal(lease.provider.id, plannerProvider.id);
    const args = { run_id: planning.run_id, control_token: planning.control_token, node_id: node, attempt_id: lease.attempt_id, lease_token: lease.lease_token };
    await f.service.call('dispatch', args); if(['expand','final'].includes(node))await f.entry(args).job;
    if (node === 'final') {
      await assert.rejects(f.service.call('collect_strict', { ...args, accepted: true }, {human:true}),{code:'AUTHORING_HUMAN_ACCEPTANCE_REQUIRED'});
      assert.equal((await store.snapshot(pack.workflow.id)).revision_hash,pack.revision_hash);
      expanded=await f.service.call('accept_authoring',{...apply,accepted:true},{human:true});
    }
  }
  assert.equal(f.sessions.length, 2); assert.notEqual((await store.snapshot(pack.workflow.id)).revision_hash, pack.revision_hash);
  assert.equal(expanded.workflow.status, 'draft'); assert.equal(expanded.workflow.nodes.find(node => node.id === 'activity_001').executor.provider_id, originalRules.routes.implementation.provider_id);
  assert.equal(expanded.workflow.import_status.unresolved.some(item => item.code === 'AI_INFERENCES_REQUIRE_REVIEW'),false);
  await assert.rejects(f.service.call('apply_authoring_result', apply, {human:true}), { code: 'ENOENT' }); assert.equal(f.sessions.length, 2);
});

test('SkillRef nodes materialize only their Run-pinned source and references after the linked original disappears', async t => {
  let invoked;
  const f = await fixture(t, { turn: async settings => {
    invoked = settings; assert.equal(settings.allowedSkills.length, 1);
    assert.equal(settings.allowedSkills[0].files['reference.txt'].toString(), 'Pinned reference');
    const tools = settings.toolBroker.tools(); const resource = tools.find(tool => tool.name === 'read_workflow_resource').inputSchema.properties.path.enum.find(path => path.endsWith('/reference.txt'));
    assert.equal(JSON.parse((await settings.toolBroker.call('read_workflow_resource', { path: resource }, 'read-reference')).contentItems[0].text).text, 'Pinned reference');
    return { output: 'Skill complete', thread_id: 'skill-thread', turn_id: 'skill-turn', audit: {} };
  } });
  const source = join(f.root, 'linked-source'); await mkdir(source); const path = join(source, 'SKILL.md');
  const text = '---\nname: linked\ndescription: Linked fixture\n---\nRead [the reference](reference.txt) and apply the user task.';
  await writeFile(path, text); await writeFile(join(source, 'reference.txt'), 'Pinned reference');
  const pack = await f.service.call('read', { workflow_id: 'strict-test' }); const workflow = structuredClone(pack.workflow);
  const work = workflow.nodes.find(node => node.id === 'work'); work.type = 'skill_ref'; work.skill_ref = { path, name: 'linked', source_hash: digest(text), allowed_nested_skills: [] }; delete work.prompt_template;
  const saved = await f.service.call('save', { workflow_id: workflow.id, workflow, expected_revision: pack.revision_hash }, {human:true});
  const started = await f.service.call('start', { workflow_id: workflow.id, revision_hash: saved.revision_hash, workspace: f.workspace, main_actor: 'root', access: 'read_only', inputs: { task: 'Pinned Skill task' } });
  await rm(source, { recursive: true });
  const lease = await f.service.call('claim_node', { run_id: started.run_id, control_token: started.control_token, node_id: 'work', owner: 'worker', request_id: 'skill-claim' });
  const args = { run_id: started.run_id, control_token: started.control_token, node_id: 'work', attempt_id: lease.attempt_id, lease_token: lease.lease_token };
  await f.service.call('dispatch', args); await f.entry(args).job;
  assert.equal((await f.service.call('get', args)).nodes.work.status, 'succeeded'); assert.equal(invoked.allowedSkills[0].source_path, path);
  await assert.rejects(f.service.call('start', { workflow_id: workflow.id, workspace: f.workspace, main_actor: 'root', access: 'read_only' }), { code: 'ENOENT' });
});

test('Inline converts a linked node to an independent Draft but private authoring source cannot publish Ready', async t => {
  const f = await fixture(t, { turn: async settings => {
    assert.deepEqual(settings.allowedSkills, []);
    const resource = await settings.toolBroker.call('read_workflow_resource', { path: 'inline/work/root/reference.txt' }, 'inlined-reference');
    assert.equal(JSON.parse(resource.contentItems[0].text).text, 'Independent reference');
    return { output: 'Inlined result', thread_id: 'inline-thread', turn_id: 'inline-turn', audit: {} };
  } });
  const source = join(f.root, 'inline-source'); await mkdir(source); const path = join(source, 'SKILL.md');
  const text = '---\nname: inline-me\ndescription: Inline fixture\n---\nRead [reference](reference.txt) and apply the task.';
  await writeFile(path, text); await writeFile(join(source, 'reference.txt'), 'Independent reference');
  const pack = await f.service.call('read', { workflow_id: 'strict-test' }); const workflow = structuredClone(pack.workflow); const work = workflow.nodes.find(node => node.id === 'work');
  work.type = 'skill_ref'; work.skill_ref = { path, name: 'inline-me', source_hash: digest(text), allowed_nested_skills: [] };
  const linked = await f.service.call('save', { workflow_id: workflow.id, workflow, expected_revision: pack.revision_hash }, {human:true});
  const inlined = await f.service.call('inline_skill', { workflow_id: workflow.id, node_id: 'work', expected_revision: linked.revision_hash });
  assert.equal(inlined.workflow.status, 'draft'); assert.equal(inlined.workflow.nodes.find(node => node.id === 'work').skill_ref, undefined);
  assert.deepEqual(inlined.workflow.nodes.find(node => node.id === 'work').executor, work.executor);
  await rm(source, { recursive: true });
  const review = await f.service.call('import_review', { workflow_id: workflow.id });
  const reviewed = await f.service.call('review_import', { workflow_id: workflow.id, expected_revision: inlined.revision_hash,
    decisions: review.issues.map(issue => ({ issue_id: issue.id, resolution: 'resolved', note: 'Verified the copied instruction and reference mapping' })) }, { human: true });
  await assert.rejects(f.service.call('save', { workflow_id: workflow.id, workflow: { ...reviewed.workflow, status: 'ready' }, expected_revision: reviewed.revision_hash }, {human:true}), {code:'CONVERTED_DEPLOYMENT_REQUIRED'});
  assert.equal((await f.service.call('read',{workflow_id:workflow.id})).workflow.status,'draft');
});
