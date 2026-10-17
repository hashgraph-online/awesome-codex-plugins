import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,mkdir,writeFile,readFile,rm} from 'node:fs/promises';
import {join} from 'node:path';
import {tmpdir} from './physical-tempdir.mjs';
import {readyWorkflow,agent,edge} from './fixtures/workflow-fixtures.mjs';
import {WorkflowStore} from '../lib/workflow-store.mjs';
import {WorkflowRuntime} from '../lib/workflow-runtime.mjs';
import {WorkflowExecutor} from '../lib/workflow-executor.mjs';
import {WorkflowDrive} from '../lib/workflow-drive.mjs';
import {HostToolRunner} from '../lib/execution/host-tool-runner.mjs';
import {RunExecutionCoordinator} from '../lib/execution/run-execution-coordinator.mjs';
import {prepareMainOrchestration,completeMainOrchestration} from '../lib/execution/main-orchestration.mjs';
import {validateLoopRegions} from '../lib/workflow-loops.mjs';
import {validateSharedHostPolicy} from '../lib/execution/shared-host-work.mjs';
import {semanticTurnsConsumed} from '../lib/execution/completion-turn-budget.mjs';
import {digest} from '../lib/workflow-revisions.mjs';
import {WorkflowService} from '../lib/workflow-service.mjs';
import {HostMainManager} from '../lib/execution/host-main-manager.mjs';
import {retainOwnedAuthority} from '../lib/execution/owned-workflow-authority.mjs';
import {DEFAULT_CONFIG_PATH} from '../server.mjs';

const thread='12345678-1234-4234-8234-123456789abc';
const decision={type:'object',additionalProperties:false,required:['accepted','assessment'],properties:{accepted:{type:'boolean'},assessment:{type:'string',minLength:1,maxLength:600}}};
const accepted=id=>({op:'eq',args:[{path:`/nodes/${id}/output/accepted`},{value:true}]});
function definition({max=null,defer=true,skip=false}={}){
  const workflow=readyWorkflow('current-main-repair-loop');workflow.skill_policy.mode='cooperative';
  const contracts=['produce','prepare','export','observe','commit'].map(id=>({id,identity:{name:`repair-${id}`,version:'1',sha256:digest(id)},argv:[id],input_schema:{},output_schema:{},
    env_allow:[],permissions:{network:false,read_paths:['.'],write_paths:['produce','export'].includes(id)?['source.md','output.mp4']:[]},output_cap_bytes:4096,deadline_ms:10000,idempotency:{mode:id==='export'?'non_idempotent':'safe'}}));
  workflow.host_tools=contracts;
  const tool=(id,inputs={},access='read_only')=>({...agent(id),type:'tool',executor:{kind:'tool',tool:id},access,...(access==='bounded_write'?{path_scope:['source.md','output.mp4']}:{}),input_bindings:inputs,outputs_schema:{}});
  const produce=tool('produce',{feedback:'/loops/repair/feedback'},'bounded_write');
  const prepare=tool('prepare',{production:'/nodes/produce/output'});prepare.outputs_schema={type:'object',properties:{product_source:{type:'object',required:['path','format'],properties:{path:{type:'string'},format:{type:'string'}},additionalProperties:false}},required:['product_source']};
  const review={...agent('source_review'),executor:{kind:'main',mode:'orchestration'},prompt_template:'Review the supplied manuscript.',outputs_schema:decision,input_bindings:{product_source:'/nodes/prepare/output/product_source'}};
  const fork={id:'fork',type:'parallel',join_id:'join',failure_policy:'fail_fast',workspace_policy:{kind:'host_tool_overlap',tool_node_id:'export',main_node_id:'source_review',read_inputs:['product_source'],...(defer?{semantic_rejection:'defer_to_join'}:{})}};
  const visual={...agent('visual'),executor:{kind:'main',mode:'orchestration'},prompt_template:'Inspect the actual product. Return concrete repair feedback on rejection.',outputs_schema:decision,input_bindings:{evidence:'/nodes/observe/output'}};
  const commit=tool('commit',{review:'/nodes/visual/output',evidence:'/nodes/observe/output'});commit.outputs_schema={type:'object',required:['verified','semantic_result'],properties:{verified:{type:'boolean'},semantic_result:{type:'string'}},additionalProperties:false};commit.completion_contract={outcome:'validated_artifact',on_missing:'block',fail_on_false:['verified']};
  workflow.finalization.node_id='commit';workflow.nodes=[{id:'start',type:'start'},produce,prepare,...(skip?[{id:'route',type:'condition',cases:[{label:'export',when:{value:false}}],default_label:'skip'}]:[]),fork,tool('export',{production:'/nodes/produce/output'},'bounded_write'),review,{id:'join',type:'join',parallel_id:'fork'},tool('observe',{production:'/nodes/produce/output'}),visual,commit,{id:'end',type:'end'}];
  workflow.edges=[edge('start','produce'),edge('produce','prepare'),...(skip?[edge('prepare','route'),edge('route','fork','export'),edge('route','observe','skip')]:[edge('prepare','fork')]),edge('fork','export','export'),edge('fork','source_review','review'),edge('export','join'),edge('source_review','join'),edge('join','observe'),edge('observe','visual'),edge('visual','commit'),edge('commit','end')];
  workflow.loops=[{id:'repair',entry_node:'produce',exit_node:'visual',node_ids:workflow.nodes.filter(node=>!['start','commit','end'].includes(node.id)).map(node=>node.id),max_rounds:max,review_context:'current_main',until:accepted('visual'),feedback_bindings:{finding:'/nodes/visual/output/assessment',source_assessment:{path:'/nodes/source_review/output/assessment',default:null},product_source:'/nodes/prepare/output/product_source'}}];
  return {workflow,contracts,fork};
}
async function fixture(t,options={}){
  const root=await mkdtemp(join(tmpdir(),'current-main-repair-')),workspace=join(root,'workspace');await mkdir(workspace);
  const source=join(workspace,'source.md'),mp4=join(workspace,'output.mp4'),{workflow,contracts}=definition(options),context={host_tools:contracts.map(tool=>tool.id)};
  const store=await new WorkflowStore(join(root,'packs'),{validationContext:context}).initialize();await store.create(workflow).catch(error=>{error.message+=' '+JSON.stringify(error.validation);throw error;});
  const runtime=await new WorkflowRuntime({workflowStore:store,runRoot:join(root,'runs'),context}).initialize();
  const run=await runtime.start({workflow_id:workflow.id,workspace,access:'bounded_write',allowed_paths:['source.md','output.mp4'],main_actor:'root',inputs:{},constraints:{native_parent_thread_id:thread}});
  const calls={produce:0,prepare:0,export:0,observe:0,commit:0,cancel:0},gates=[],feedbacks=[];
  const registry=Object.fromEntries(contracts.map(contract=>[contract.id,{identity:contract.identity,attestation:{qualified:true,cancellable:true,effect_observation:true,tool_identity:contract.identity,broker_id:contract.id,evidence_sha256:digest('qualified')},
    async execute({input}){
      calls[contract.id]++;let output,changed=[];
      if(contract.id==='produce'){
        feedbacks.push(input.feedback);await writeFile(source,`Manuscript revision ${calls.produce}`);changed=['source.md'];output={counter:calls.produce,sha256:digest(await readFile(source))};
      }else if(contract.id==='prepare')output={product_source:{path:source,format:'extended_markdown'}};
      else if(contract.id==='export'){
        let release,finished;const gate={pending:new Promise(resolve=>{release=resolve;}),done:new Promise(resolve=>{finished=resolve;}),release:()=>release(),cancelled:false};gates.push(gate);
        try{await gate.pending;if(gate.cancelled)return {exit_code:1,output:null,effects:{observed:true,changed_paths:[],outside_paths:[],artifacts:[]}};
          await writeFile(mp4,`MP4 primary ${input.production.counter}`);changed=['output.mp4'];output={counter:input.production.counter,sha256:digest(await readFile(mp4))};}finally{finished();}
      }else if(contract.id==='observe'){
        assert.equal(digest(await readFile(source)),input.production.sha256);output={counter:input.production.counter,sha256:input.production.sha256,mp4_sha256:options.skip?null:digest(await readFile(mp4))};
      }else{
        assert.equal(input.review.accepted,true);assert.equal(input.evidence.counter,calls.produce);assert.equal(input.evidence.sha256,digest(await readFile(source)));
        if(!options.skip)assert.equal(input.evidence.mp4_sha256,digest(await readFile(mp4)));output={verified:true,semantic_result:input.review.assessment};
      }
      return {exit_code:0,output,effects:{observed:true,changed_paths:changed,outside_paths:[],artifacts:[]}};
    },async cancel(){calls.cancel++;const gate=gates.at(-1);if(gate){gate.cancelled=true;gate.release();await gate.done;}return {termination_confirmed:true,evidence:[{kind:'fixture_termination',sha256:digest('settled')}],effects:{observed:true,changed_paths:[],outside_paths:[],artifacts:[]}};}
  }]));
  const executor=new WorkflowExecutor({runtime,env:{},hostToolRunner:new HostToolRunner({registry}),getConfig:async()=>({global:{enabled:true,max_prompt_chars:64000},providers:[]})});runtime.executionAdmission=executor.attemptAdmission;
  const manager=()=>({entries:new Map(),fenceRun(){},fenceAttempt(){},async stopRun(){},async stopAttempt(){}}),coordinator=new RunExecutionCoordinator({admission:executor.attemptAdmission,strictManager:manager(),managedNativeManager:manager(),hostMainManager:manager(),registry:{}});coordinator.bind(runtime);
  runtime.failAttemptAfterQuiescence=(...args)=>coordinator.failAttemptAfterQuiescence(...args);runtime.fenceRunExecution=(...args)=>coordinator.fenceRun(...args);
  const drive=new WorkflowDrive({runtime,executor}),current={run_id:run.run_id,control_token:run.control_token,thread_id:thread},args={control_token:run.control_token,owner:'root'};
  const cleanup=[];
  t.after(async()=>{gates.forEach(gate=>gate.release());for(const close of cleanup)await close();await runtime.executionAdmission.wait(run.run_id);await Promise.all(runtime.executionAdmission.drainJobs.values());await rm(root,{recursive:true,maxRetries:3,retryDelay:100});});
  const advance=()=>drive.advanceToMain(run.run_id,args),complete=output=>completeMainOrchestration(runtime,{...current,output},{executor});
  const review=async accepted=>{assert.equal((await advance()).node_id,'source_review');const task=await prepareMainOrchestration(runtime,current);assert.equal(task.context,'current_conversation');await complete({accepted,assessment:accepted?'Source accepted':'Fix the source relationship'});};
  const visual=async accepted=>{const pending=advance();gates.at(-1)?.release();assert.equal((await pending).node_id,'visual');const task=await prepareMainOrchestration(runtime,current);assert.equal(task.context,'current_conversation');assert.equal(task.rejection_route.loop_id,'repair');await complete({accepted,assessment:accepted?'Accepted latest MP4':'Move the title clear of the diagram'});};
  return {root,workspace,workflow,registry,cleanup,runtime,run,calls,gates,feedbacks,advance,complete,review,visual,current};
}

test('real Service rejection retains model Run authority for repair and finalizes after the same initiating Main accepts',async t=>{
  const f=await fixture(t),configPath=join(f.root,'control-plane.json');let workerSessions=0;
  const manager=new HostMainManager({configPath,getConfig:async()=>({}),qualify:async()=>{throw new Error('Current Main must not qualify a worker');},sessionFactory:async()=>{workerSessions++;throw new Error('Current Main must not open a worker');}});
  const service=new WorkflowService({configPath,defaultConfigPath:DEFAULT_CONFIG_PATH,env:{},capabilities:{hostMainManager:manager,hostToolRegistry:f.registry,nativeAgentObserver:null,nativeParentVerifier:async()=>({agent_path:'/root'})}});
  f.cleanup.push(async()=>{await Promise.all(service.attemptAdmission.drainJobs.values());await service.historyMaintenance.settle();await service.historyMaintenance.close();await manager.close();});
  await service.call('migrate_v6',{}, {human:true});const pack=await service.call('create',{workflow:f.workflow,resources:{}});
  const begun=await service.call('begin_main',{workflow_id:f.workflow.id,revision_hash:pack.revision_hash,workspace:f.workspace,access:'bounded_write',allowed_paths:['source.md','output.mp4'],inputs:{},main_actor:'codex',native_parent_thread_id:thread});
  const {runtime}=await service.open(),{run_id,control_token}=begun.host_binding;await retainOwnedAuthority(runtime,{run_id,control_token});
  const call=output=>service.call('orchestration_complete',{output},{model:true,modelThreadId:thread});
  assert.equal((await service.call('native_next',{}, {model:true,modelThreadId:thread})).context,'current_conversation');
  let next=call({accepted:true,assessment:'Source accepted'});f.gates.at(-1).release();let visual=await next;assert.equal(visual.rejection_route.round,1);
  const repaired=await call({accepted:false,assessment:'Move the title clear of the diagram'});assert.equal(repaired.status,'orchestration_handoff');assert.equal(repaired.context,'current_conversation');
  assert.equal((await runtime.get(run_id)).status,'running');assert.equal(f.calls.commit,0);assert.equal(f.calls.produce,2);assert.equal(f.feedbacks[1].finding,'Move the title clear of the diagram');
  next=call({accepted:true,assessment:'Repaired source accepted'});f.gates.at(-1).release();visual=await next;assert.equal(visual.rejection_route.round,2);
  const completed=await call({accepted:true,assessment:'Accepted latest MP4'});assert.equal(completed.status,'succeeded');assert.equal(completed.output.semantic_result,'Accepted latest MP4');
  assert.equal(f.calls.commit,1);assert.equal(f.calls.export,2);assert.equal(workerSessions,0);
  const state=await runtime.get(run_id);for(const attempt of [...state.nodes.visual.attempts,...state.nodes.source_review.attempts])assert.equal(attempt.dispatch.receipt.thread_id,thread);
});

test('same actual Main rejection archives the round, repairs and refreshes export evidence, then Host finalizes exactly once',async t=>{
  const f=await fixture(t);await f.review(true);assert.equal(f.calls.export,1);assert.equal(f.calls.commit,0);await f.visual(false);
  let state=await f.runtime.get(f.run.run_id);assert.equal(state.status,'running');assert.equal(state.loops.repair.round,2);assert.equal(state.loops.repair.rounds[0].nodes.visual.output.accepted,false);assert.equal(state.nodes.commit.attempts.length,0);
  await f.review(true);assert.equal(f.calls.export,2);assert.equal(f.feedbacks[1].finding,'Move the title clear of the diagram');assert.equal(f.feedbacks[1].source_assessment,'Source accepted');await f.visual(true);
  assert.equal((await f.advance()).status,'succeeded');assert.equal(f.calls.commit,1);state=await f.runtime.get(f.run.run_id);
  assert.equal(state.output.semantic_result,'Accepted latest MP4');assert.equal(state.nodes.observe.output.counter,2);assert.equal(state.nodes.export.attempts.length,2);assert.equal(state.nodes.visual.attempts.length,2);assert.equal(semanticTurnsConsumed(state.nodes.visual),1);
  for(const attempt of [...state.nodes.visual.attempts,...state.nodes.source_review.attempts])assert.equal(attempt.dispatch.receipt.thread_id,thread);
  assert.notEqual(state.nodes.export.attempts[0].shared_host_projection.sources[0].sha256,state.nodes.export.attempts[1].shared_host_projection.sources[0].sha256);
  assert.equal(state.loops.repair.rounds.length,2);assert.equal(state.loops.repair.status,'accepted');
});

test('deferred source false remains data until tool success and cannot be overridden by later Main true',async t=>{
  const f=await fixture(t);await f.review(false);let state=await f.runtime.get(f.run.run_id);assert.equal(state.status,'running');assert.equal(state.nodes.source_review.output.accepted,false);assert.equal(f.calls.cancel,0);assert.equal(f.calls.commit,0);
  await f.visual(true);state=await f.runtime.get(f.run.run_id);assert.equal(state.loops.repair.round,2);assert.equal(state.loops.repair.feedback.source_assessment,'Fix the source relationship');assert.equal(f.calls.commit,0);
  await f.review(true);await f.visual(true);assert.equal((await f.advance()).status,'succeeded');assert.equal(f.calls.commit,1);
});

test('cancel during a repair export waits for its actual producer and never releases finalization',async t=>{
  const f=await fixture(t);await f.review(true);await f.visual(false);await f.review(true);
  await f.runtime.cancel(f.run.run_id,{control_token:f.run.control_token});await f.runtime.executionAdmission.wait(f.run.run_id);await f.gates[1].done;
  assert.equal((await f.advance()).status,'cancelled');assert.equal(f.calls.export,2);assert.equal(f.calls.cancel,1);assert.equal(f.calls.commit,0);
});

test('finite opted-in loop exhausts at its declared bound without finalization',async t=>{
  const f=await fixture(t,{max:1});await f.review(true);await f.visual(false);const state=await f.runtime.get(f.run.run_id);
  assert.equal(state.status,'failed');assert.equal(state.error.code,'LOOP_EXHAUSTED');assert.equal(state.loops.repair.rounds.length,1);assert.equal(f.calls.commit,0);
});

test('conditional skipped export has no source acceptance requirement',async t=>{
  const f=await fixture(t,{skip:true});assert.equal((await f.advance()).node_id,'visual');await prepareMainOrchestration(f.runtime,f.current);
  await f.complete({accepted:true,assessment:'Accepted non-MP4 video'});
  assert.equal((await f.advance()).status,'succeeded');assert.equal(f.calls.export,0);assert.equal(f.calls.commit,1);assert.equal((await f.runtime.get(f.run.run_id)).nodes.source_review.status,'skipped');
});

test('current Main and deferred rejection require explicit qualified contracts; independent defaults remain',()=>{
  const {workflow,fork}=definition();assert.equal(validateLoopRegions(workflow),true);assert.equal(validateSharedHostPolicy(workflow,fork),undefined);
  for(const change of [w=>delete w.loops[0].review_context,w=>w.nodes.find(n=>n.id==='visual').access='bounded_write',w=>w.loops[0].until={value:true},w=>w.loops[0].node_ids.push('commit'),w=>w.loops[0].max_rounds=0]){
    const candidate=structuredClone(workflow);change(candidate);assert.throws(()=>validateLoopRegions(candidate));
  }
  const noLoop=structuredClone(workflow);delete noLoop.loops;assert.throws(()=>validateSharedHostPolicy(noLoop,noLoop.nodes.find(n=>n.id==='fork')),{code:'SHARED_HOST_POLICY'});
  const badPolicy=structuredClone(workflow);badPolicy.nodes.find(n=>n.id==='fork').workspace_policy.semantic_rejection='ignore';assert.throws(()=>validateSharedHostPolicy(badPolicy,badPolicy.nodes.find(n=>n.id==='fork')),{code:'SHARED_HOST_POLICY'});
});
