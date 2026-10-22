import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,mkdir,writeFile,rm} from 'node:fs/promises';
import {join,resolve} from 'node:path';
import {tmpdir} from './physical-tempdir.mjs';
import {WorkflowStore} from '../lib/workflow-store.mjs';
import {WorkflowRuntime,resolvedSubagentPlan} from '../lib/workflow-runtime.mjs';
import {createDraft} from '../lib/workflow-schema.mjs';
import {canonicalJSON,digest} from '../lib/workflow-revisions.mjs';
import {reattachAttempt} from '../lib/workflow-recovery.mjs';
import {semanticTurnsConsumed,currentRoundAttempts} from '../lib/execution/completion-turn-budget.mjs';
import {regionBranchOwner} from '../lib/parallel/workspace.mjs';
import {ParallelWorktreeManager} from '../lib/parallel/worktree-manager.mjs';
import {preflightSemanticOutput} from '../lib/execution/completion-preflight.mjs';
import {initialRunState,graphInfo,setOutcome,advanceRun} from '../lib/workflow-state.mjs';

const eq=(path,value)=>({op:'eq',args:[{path},{value}]});
const edge=(source,target,label)=>({id:`${source}-${target}`,source,target,...(label?{label}:{})});
const agent=id=>({id,type:'agent',role:'implementer',executor:{kind:'provider',provider_id:'fixture'},access:'read_only',approval:{required:false},retry:{max_attempts:3},input_bindings:{},outputs_schema:{},prompt_template:'Perform the assigned task.'});
function definition(max=3){
  const workflow={...createDraft('loop-fixture','Bounded repair fixture'),status:'ready',skill_policy:{mode:'cooperative',implicit:'allow',ambient_allow:[],shadowed_skill_paths:[]},finalization:{required:true,node_id:'final'}};
  workflow.inputs_schema={type:'object',properties:{items:{type:'array',items:{type:'object',properties:{name:{type:'string'},files:{type:'array',items:{type:'string'}},dependencies:{type:'array',items:{type:'string'}}},required:['name','files','dependencies']}}},required:['items']};
  const repair={...agent('repair'),access:'bounded_write',path_scope:{binding:'run.allowed_paths'},input_bindings:{items:'/loops/repair-loop/repair_items'}};
  const review={...agent('review'),role:'reviewer',input_bindings:{items:'/loops/repair-loop/review_items'},outputs_schema:{type:'object',properties:{verdicts:{type:'array',items:{type:'object',properties:{accepted:{type:'boolean'},findings:{type:'string'}},required:['accepted'],additionalProperties:false}}},required:['verdicts'],additionalProperties:false}};
  workflow.nodes=[{id:'start',type:'start'},agent('work'),{id:'gate',type:'condition',cases:[{label:'repair',when:{op:'ne',args:[{path:'/loops/repair-loop/repair_items'},{value:[]}]}}],default_label:'review'},repair,review,{...agent('final'),executor:{kind:'main'},role:'finalizer'}, {id:'end',type:'end'}];
  workflow.edges=[edge('start','work'),edge('work','gate'),edge('gate','repair','repair'),edge('gate','review','review'),edge('repair','review'),edge('review','final'),edge('final','end')];
  workflow.loops=[{id:'repair-loop',entry_node:'gate',exit_node:'review',node_ids:['gate','repair','review'],max_rounds:max,until:eq('/loops/repair-loop/all_accepted',true),item_scope:{items:'/inputs/items',verdicts:'/nodes/review/output/verdicts',paths_field:'files',dependencies_field:'dependencies'}}];
  return workflow;
}
async function fixture(t,max=3,transform=w=>w,inputsOverride){
  const root=await mkdtemp(join(tmpdir(),'workflow-loop-')),workspace=join(root,'workspace');await mkdir(workspace);
  t.after(async()=>{assert(resolve(root).startsWith(resolve(tmpdir())));await rm(root,{recursive:true,force:true,maxRetries:3});});
  const context={providers:[{id:'fixture',kind:'openai_compatible',enabled:true,capabilities:{read:true,write:true}}]};
  const store=await new WorkflowStore(join(root,'packs'),{validationContext:context}).initialize();
  await store.create(transform(definition(max)));
  const options={workflowStore:store,runRoot:join(root,'runs'),context};
  const runtime=await new WorkflowRuntime(options).initialize();
  const items=[1,2,3].map(i=>({name:`item${i}`,files:[i===1?join(workspace,'1.txt'):`${i}.txt`],dependencies:i===1?[]:['shared.txt']}));
  for(const file of ['1.txt','2.txt','3.txt','shared.txt'])await writeFile(join(workspace,file),'original');
  const run=await runtime.start({workflow_id:'loop-fixture',workspace,access:'bounded_write',allowed_paths:['.'],main_actor:'root',inputs:inputsOverride??{items}});
  return {root,workspace,options,runtime,run,items};
}
async function claim(f,id){return (id==='final'?f.runtime.claimHostMain.bind(f.runtime):f.runtime.claimNode.bind(f.runtime))(f.run.run_id,{node_id:id,owner:id==='final'?'root':'executor',request_id:`claim-${id}-${(await f.runtime.get(f.run.run_id)).nodes[id].attempts.length}`,control_token:f.run.control_token});}
const payload=output=>({status:'succeeded',summary:'Synthetic verified result',structured_output:output,artifacts:[],evidence:[{check:'fixture',passed:true}],changed_paths:[],outside_paths:[]});
async function complete(f,envelope,output){
  const args={node_id:envelope.node_id,attempt_id:envelope.attempt_id,lease_token:envelope.lease_token,control_token:f.run.control_token},request_id=`dispatch-${envelope.attempt_id}`,envelope_hash=digest(canonicalJSON(envelope));
  const record=await f.runtime.runs.read(f.run.run_id),attempt=record.state.nodes[envelope.node_id].attempts.find(a=>a.id===envelope.attempt_id);
  if(envelope.executor.kind==='main'){
    if(!attempt.dispatch){await f.runtime.recordHostMainDispatchIntent(f.run.run_id,{...args,request_id,envelope_hash});await f.runtime.recordHostMainDispatchReceipt(f.run.run_id,{...args,request_id,receipt:{invocation_id:`main-${envelope.attempt_id}`,executor:'codex-app-server-host-main',executable_sha256:'a'.repeat(64),model:'fixture',effort:'medium',main_actor:'root',session_id:'fixture-main',call_chain_id:'fixture-chain'}});}
    const saved=await f.runtime.runs.saveExecutorResult(f.run.run_id,envelope.attempt_id,payload(output));
    await f.runtime.recordExecutorEvent(f.run.run_id,{...args,event:{kind:'result_proposed',metadata:{...saved,final_acceptance_required:true}}});
    return f.runtime.completeHostMainResult(f.run.run_id,args,{accepted:true});
  }
  if(!attempt.dispatch){await f.runtime.recordDispatchIntent(f.run.run_id,{...args,request_id,envelope_hash});await f.runtime.recordDispatchReceipt(f.run.run_id,{...args,request_id,receipt:{task_id:request_id}});}
  return f.runtime.completeNode(f.run.run_id,{...args,completion:payload(output)});
}
async function firstReview(f){
  await complete(f,await claim(f,'work'),{});
  assert.equal((await f.runtime.get(f.run.run_id)).nodes.repair.status,'skipped');
  const review=await claim(f,'review');assert.equal(review.inputs.items.length,3);
  await complete(f,review,{verdicts:[{accepted:true},{accepted:true},{accepted:false,findings:'Fix the missing behavior.'}]});
  return review;
}

test('runtime retains accepted siblings, repairs only the failed item and rechecks shared dependants',async t=>{
  const f=await fixture(t),prior=await firstReview(f);
  let state=await f.runtime.get(f.run.run_id);
  assert.equal(state.loops['repair-loop'].round,2);assert.equal(state.nodes.final.status,'pending');
  assert.equal(state.nodes.work.attempts.length,1);
  const repair=await claim(f,'repair');assert.deepEqual(repair.inputs.items.map(i=>i.name),['item3']);assert.equal(repair.inputs.items[0].findings,'Fix the missing behavior.');
  await writeFile(join(f.workspace,'3.txt'),'fixed');await writeFile(join(f.workspace,'shared.txt'),'shared fix');
  await complete(f,repair,{});
  const review=await claim(f,'review');assert.deepEqual(review.inputs.items.map(i=>i.name),['item2','item3']);
  await complete(f,review,{verdicts:[{accepted:true},{accepted:true}]});
  state=await f.runtime.get(f.run.run_id);assert.equal(state.nodes.final.status,'ready');assert.equal(state.loops['repair-loop'].status,'accepted');
  assert.equal(state.nodes.repair.attempts.length,1);assert.equal(state.nodes.review.attempts.length,2);
  assert.equal(currentRoundAttempts(state.nodes.review).length,1);assert.equal(semanticTurnsConsumed(state.nodes.review),1);
  // A duplicate old completion is consumed once, even after later rounds finish.
  const before=state.sequence;
  await f.runtime.completeNode(f.run.run_id,{node_id:'review',attempt_id:prior.attempt_id,lease_token:prior.lease_token,completion:payload({verdicts:[{accepted:true},{accepted:true},{accepted:false,findings:'Fix the missing behavior.'}]})});
  assert.equal((await f.runtime.get(f.run.run_id)).sequence,before);
  await complete(f,await claim(f,'final'),{});assert.equal((await f.runtime.get(f.run.run_id)).status,'succeeded');
});

test('restart reconciles the exact active repair attempt and preserves completed round evidence',async t=>{
  const f=await fixture(t);await firstReview(f);const repair=await claim(f,'repair');
  const before=await f.runtime.get(f.run.run_id),history=structuredClone(before.loops['repair-loop'].rounds);
  f.runtime=await new WorkflowRuntime(f.options).initialize();
  await f.runtime.resume(f.run.run_id,{control_token:f.run.control_token,after_restart:true});
  const recovered=await reattachAttempt(f.runtime,f.run.run_id,{control_token:f.run.control_token,node_id:'repair',attempt_id:repair.attempt_id},{kind:'unsubmitted_claim'});
  await f.runtime.resume(f.run.run_id,{control_token:f.run.control_token});
  assert.equal(recovered.envelope.attempt_id,repair.attempt_id);
  assert.deepEqual((await f.runtime.get(f.run.run_id)).loops['repair-loop'].rounds,history);
  await complete(f,recovered.envelope,{});const review=await claim(f,'review');assert.deepEqual(review.inputs.items.map(i=>i.name),['item3']);
  await complete(f,review,{verdicts:[{accepted:true}]});assert.equal((await f.runtime.get(f.run.run_id)).nodes.final.status,'ready');
});

test('exhaustion leaves final acceptance blocked rather than reporting success',async t=>{
  const f=await fixture(t,1);await firstReview(f);const state=await f.runtime.get(f.run.run_id);
  assert.equal(state.status,'failed');assert.equal(state.error.code,'LOOP_EXHAUSTED');assert.equal(state.nodes.final.status,'pending');
});

test('fanout bindings and parallel ownership follow the current loop round',()=>{
  const workflow=definition(),state={run_id:'run',inputs:{items:[]},nodes:{},loops:{'repair-loop':{round:2,lineage:[],status:'running',review_items:[1,2],repair_items:[3]}}};
  const node={subagent_count:'auto',fanout:{input:'items',distribution:'one_per_item'},input_bindings:{items:'/loops/repair-loop/review_items'}};
  assert.equal(resolvedSubagentPlan(node,state).count,2);
  const pins={root:{workflow}},first=regionBranchOwner(state,pins,'gate','branch');state.loops['repair-loop'].round=3;
  assert.notEqual(first,regionBranchOwner(state,pins,'gate','branch'));
});

test('bad review cardinality is caught before an immutable result or completion is accepted',async t=>{
  const f=await fixture(t);await firstReview(f);await complete(f,await claim(f,'repair'),{});
  const review=await claim(f,'review'),record=await f.runtime.runs.read(f.run.run_id),node=record.pins.root.workflow.nodes.find(n=>n.id==='review');
  await assert.rejects(preflightSemanticOutput(node,{verdicts:[]},f.workspace,{state:record.state,pins:record.pins}),{code:'LOOP_VERDICT_INVALID'});
  await assert.rejects(complete(f,review,{verdicts:[]}),{code:'LOOP_VERDICT_INVALID'});
  assert.equal((await f.runtime.get(f.run.run_id)).nodes.review.attempts.at(-1).completion_hash,null);
  await complete(f,review,{verdicts:[{accepted:true}]});assert.equal((await f.runtime.get(f.run.run_id)).nodes.final.status,'ready');
});

test('unsafe item paths reject launch before any new Run or executor effect',async t=>{
  const f=await fixture(t),prior=await f.runtime.runs.list();
  await assert.rejects(f.runtime.start({workflow_id:'loop-fixture',workspace:f.workspace,access:'bounded_write',allowed_paths:['.'],main_actor:'root',inputs:{items:[{name:'bad',files:['../escape.txt'],dependencies:[]}]}}),{code:'LOOP_ITEM_PATH'});
  assert.deepEqual((await f.runtime.runs.list()).map(r=>r.run_id),prior.map(r=>r.run_id));
});

test('parallel cleanup owns each round once and reconciles duplicate nested archives after a crash',async()=>{
  const make=(owner,tree)=>({phase:'merged',base:{workspace:'/fixture',base_commit:'base'},branches:{branch:{owner,workspace:`/fixture/${owner}`}},proposal:{branches:[{branch_id:'branch',tree}],changed_paths:[]}});
  const first=make('round1','tree1'),second=make('round2','tree2');
  const state={status:'succeeded',nodes:{fork:{attempts:[]},work:{attempts:[]}},parallel:{fork:second},loops:{outer:{rounds:[{parallel:{fork:structuredClone(first)}},{parallel:{fork:structuredClone(second)}}]},inner:{rounds:[{parallel:{fork:structuredClone(first)}}]}}};
  const pins={parallel:{regions:[{id:'fork',isolated:true,node_ids:['fork','work'],branches:[{id:'branch',write_paths:['.']}]}]}};
  const runtime={authorizeController:async()=>{},runs:{read:async()=>({state:structuredClone(state),pins}),mutate:async(_id,_kind,fn)=>fn(state)}};
  const manager=new ParallelWorktreeManager(resolve(tmpdir(),'fixture-loop-ownership'));
  const removed=new Set();let crash=true,verify=0;
  manager.git={verify:async()=>{verify++;},snapshot:async(workspace)=>({tree:workspace.endsWith('round1')?'tree1':'tree2'}),remove:async(owner,options)=>{
    if(removed.has(owner.owner))return;
    await options.beforeRemove();removed.add(owner.owner);
    if(crash){crash=false;throw Object.assign(new Error('Crash after exact worktree removal'),{code:'FIXTURE_CRASH'});}
  }};
  await assert.rejects(manager.cleanup(runtime,'fixture',{}),{code:'FIXTURE_CRASH'});
  await manager.cleanup(runtime,'fixture',{});
  assert.deepEqual([...removed].sort(),['round1','round2']);assert.equal(verify,2);
  for(const loop of Object.values(state.loops))for(const round of loop.rounds)assert.deepEqual(round.parallel.fork.cleaned_branches,['branch']);
  assert.deepEqual(state.parallel.fork.cleaned_branches,['branch']);
  assert.deepEqual((await manager.cleanup(runtime,'fixture',{})).removed,[]);
});

test('failure and always edges cannot bypass unaccepted loop boundaries or final acceptance',()=>{
  const workflow=definition();delete workflow.loops[0].item_scope;workflow.loops[0].until=eq('/nodes/review/output/passed',true);
  workflow.edges.find(e=>e.source==='review').on='always';
  const pins={root:{workflow,revision_hash:'a'.repeat(64)},providers:[]};
  const state=initialRunState({runId:'fixture',pinsHash:'b'.repeat(64),pins,inputs:{},permissions:{workspace:resolve(tmpdir()),access:'bounded_write',allowed_paths:['.']},constraints:{},controlHash:'c'.repeat(64),mainActor:'root',requireApproval:false});
  state.loops['repair-loop'].status='running';state.loops['repair-loop'].round=1;
  setOutcome(state,graphInfo(workflow),'review','failed');advanceRun(state,pins);
  assert.equal(state.status,'failed');assert.equal(state.nodes.final.status,'pending');assert.equal(state.edges['review-final'],'pending');
  // Defensive terminal guard also rejects any corrupt/bypassed completed path.
  for(const node of Object.values(state.nodes))node.status='succeeded';
  state.nodes.review.status='failed';state.nodes.review.failure_handled=true;state.status='running';
  advanceRun(state,pins);assert.equal(state.status,'failed');assert.equal(state.error.code,'FINALIZATION_INCOMPLETE');
});

test('an inactive item-loop branch does not demand its optional source at launch',async t=>{
  const f=await fixture(t,3,w=>{
    w.inputs_schema.required=[];
    w.nodes.push({id:'choice',type:'condition',cases:[{label:'items',when:{op:'exists',args:[{path:'/inputs/items'}]}}],default_label:'none'});
    w.edges=w.edges.filter(e=>e.source!=='start');
    w.edges.push(edge('start','choice'),edge('choice','work','items'),edge('choice','final','none'));
    return w;
  },{});
  const state=await f.runtime.get(f.run.run_id);assert.equal(state.loops['repair-loop'].status,'skipped');assert.equal(state.nodes.review.status,'skipped');assert.equal(state.nodes.final.status,'ready');
  await complete(f,await claim(f,'final'),{});assert.equal((await f.runtime.get(f.run.run_id)).status,'succeeded');
});
