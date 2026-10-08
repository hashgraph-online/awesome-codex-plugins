import test from 'node:test';
import assert from 'node:assert/strict';
import { adoptAuthoringRun, assessAuthoringRecovery, continueControlledAuthoringRun, inspectAuthoringRun, inspectControlledAuthoringRun, mountedAuthoringSession, shouldPollAuthoring } from '../web-src/skill-generation-recovery.mjs';

const pack={workflow:{id:'source-draft'},revision_hash:'a'.repeat(64)};
const definition={provenance:{kind:'authoring_workflow_run',source_workflow_id:'source-draft',source_revision:pack.revision_hash}};
const state=()=>({run_id:'authoring-existing',sequence:12,status:'running',nodes:{expand:{status:'ready',attempts:[{status:'succeeded',result_proposal:{sha256:'b'.repeat(64)}}]},final:{status:'ready',attempts:[]}},generation_repair:{awaiting_user_input:true,latest_cumulative_plan:{proposal:{contract:'workflow-semantic-blueprint/v6'}},feedback:{code:'GENERATION_REVIEW_FINDINGS',findings:[{code:'source_mapping'}]}}});

test('authoring recovery checks exact source identity before authenticated adoption',async()=>{
  for(const changed of [
    {workflow:{id:'other-draft'},revision_hash:pack.revision_hash},
    {workflow:{id:pack.workflow.id},revision_hash:'c'.repeat(64)},
  ]){
    const calls=[];
    const api=async operation=>{calls.push(operation);return operation==='run_definition'?definition:state();};
    await assert.rejects(adoptAuthoringRun(api,changed,'authoring-existing'),{code:'AUTHORING_RECOVERY_SOURCE'});
    assert.deepEqual(calls.sort(),['get','run_definition']);
  }
});

test('authoring recovery requires a retained plan and never starts or advances a planner while inspecting',async()=>{
  const calls=[];
  const empty=state();empty.nodes.expand.attempts=[];delete empty.generation_repair;
  const api=async operation=>{calls.push(operation);return operation==='run_definition'?definition:empty;};
  await assert.rejects(adoptAuthoringRun(api,pack,'authoring-existing'),{code:'AUTHORING_RECOVERY_PROPOSAL'});
  assert.deepEqual(calls.sort(),['get','run_definition']);
  const validCalls=[];
  const validApi=async(operation,args)=>{validCalls.push([operation,args]);return operation==='run_definition'?definition:operation==='get'?state():{...state(),status:'paused',control_token:'example-new-token'};};
  const recovered=await adoptAuthoringRun(validApi,pack,'authoring-existing');
  assert.equal(recovered.inspected.continuation,'guidance');
  assert.equal(recovered.adopted.control_token,'example-new-token');
  assert.deepEqual(validCalls.map(([operation])=>operation),['run_definition','get','adopt_run']);
  assert.equal(validCalls[2][1].expected_sequence,12);
});

test('recovered authoring Run distinguishes saved guidance, completed projection and interrupted reconciliation',async()=>{
  const awaiting=state();
  assert.equal(assessAuthoringRecovery(pack,definition,awaiting).continuation,'guidance');
  const compiled=state();compiled.nodes.expand.status='succeeded';compiled.nodes.expand.output={proposal:{}};delete compiled.generation_repair;
  assert.equal(assessAuthoringRecovery(pack,definition,compiled).continuation,'advance');
  compiled.nodes.final.status='interrupted';
  assert.equal(assessAuthoringRecovery(pack,definition,compiled).continuation,'reconcile');
  const accepted={...compiled,status:'succeeded'};
  assert.equal(assessAuthoringRecovery(pack,definition,accepted).continuation,'accepted');
  const calls=[];
  const api=async operation=>{calls.push(operation);return operation==='run_definition'?definition:awaiting;};
  assert.equal((await inspectAuthoringRun(api,pack,'authoring-existing')).run_id,'authoring-existing');
  assert.deepEqual(calls.sort(),['get','run_definition']);
});

test('remounted sessions and retained user guidance cannot silently advance a planner',()=>{
  const run={run_id:'authoring-existing',control_token:'known'};
  assert.equal(shouldPollAuthoring({run,pollEnabled:false,stopping:false,error:null,phase:null}),false);
  assert.equal(shouldPollAuthoring({run,pollEnabled:true,stopping:false,error:null,phase:'user_input_required'}),false);
  assert.equal(shouldPollAuthoring({run,pollEnabled:true,stopping:false,error:null,phase:'attention'}),false);
  assert.equal(shouldPollAuthoring({run,pollEnabled:true,stopping:false,error:null,phase:'reviewing'}),true);
});

test('failed or cancelled authoring Runs are rejected before controller adoption',async()=>{
  for(const status of ['failed','cancelled']){
    const calls=[];
    const terminal={...state(),status};
    const api=async operation=>{calls.push(operation);return operation==='run_definition'?definition:terminal;};
    await assert.rejects(adoptAuthoringRun(api,pack,'authoring-existing'),{code:'AUTHORING_RECOVERY_TERMINAL'});
    assert.deepEqual(calls.sort(),['get','run_definition']);
  }
});

test('same-source adoption survives detail reconciliation and remount without another adoption or planner',async()=>{
  const controllers=new Map();
  const calls=[];
  let current=state();
  const api=async(operation,args)=>{
    calls.push(operation);
    if(operation==='run_definition')return definition;
    if(operation==='get')return current;
    if(operation==='adopt_run'){
      assert.equal(args.expected_sequence,current.sequence);
      current={...current,sequence:13,status:'paused',nodes:{...current.nodes,final:{status:'interrupted',attempts:[]}}};
      return {...current,control_token:'example-same-authority'};
    }
    if(operation==='run_snapshot'){
      assert.equal(args.control_token,controllers.get(current.run_id));
      return {state:current,events:[]};
    }
    throw new Error(`Unexpected operation ${operation}`);
  };
  const adopted=await adoptAuthoringRun(api,pack,current.run_id);
  controllers.set(adopted.adopted.run_id,adopted.adopted.control_token); // RunPanel.rememberRun
  // Detailed Run recovers the exact interrupted result and resumes the same authority.
  current={...current,sequence:15,status:'running',nodes:{...current.nodes,final:{status:'ready',attempts:[]}}};
  const {inspected,controlToken}=await inspectControlledAuthoringRun(api,pack,current.run_id,controllers);
  assert.equal(inspected.continuation,'guidance');
  assert.equal(controlToken,'example-same-authority');
  const attached=await continueControlledAuthoringRun(api,pack,current.run_id,controllers);
  assert.equal(attached.checked.state.status,'running');
  assert.equal(attached.controlToken,'example-same-authority');
  assert.equal(shouldPollAuthoring({run:{run_id:current.run_id,control_token:controlToken},pollEnabled:true,stopping:false,error:null,phase:'user_input_required'}),false);
  assert.equal(calls.filter(operation=>operation==='adopt_run').length,1);
  assert.equal(calls.includes('resume'),false);
  assert.equal(calls.includes('advance_authoring'),false);
});

test('reused control fails before attachment when source or authenticated token is wrong',async()=>{
  const controllers=new Map([['authoring-existing','example-old-token']]);
  const calls=[];
  const api=async(operation,args)=>{
    calls.push(operation);
    if(operation==='run_definition')return definition;
    if(operation==='get')return state();
    if(operation==='run_snapshot')throw Object.assign(new Error(`Rejected ${args.control_token}`),{code:'RUN_AUTHORITY'});
    if(operation==='adopt_run')return {...state(),status:'paused',control_token:'example-new-token'};
    throw new Error(`Unexpected operation ${operation}`);
  };
  await assert.rejects(inspectControlledAuthoringRun(api,{...pack,revision_hash:'c'.repeat(64)},'authoring-existing',controllers),{code:'AUTHORING_RECOVERY_SOURCE'});
  assert.deepEqual(calls,['run_definition','get']);
  await assert.rejects(continueControlledAuthoringRun(api,pack,'authoring-existing',controllers),error=>{
    assert.equal(error.code,'AUTHORING_RECOVERY_CONTROL_STALE');
    assert.equal(error.inspected.run_id,'authoring-existing');
    return true;
  });
  assert.equal(controllers.has('authoring-existing'),false);
  assert.equal(calls.includes('adopt_run'),false);
  assert.equal(calls.includes('resume'),false);
  assert.equal(calls.includes('advance_authoring'),false);
  const adopted=await adoptAuthoringRun(api,pack,'authoring-existing');
  assert.equal(adopted.adopted.control_token,'example-new-token');
  assert.equal(calls.filter(operation=>operation==='adopt_run').length,1);
});

test('paused saved guidance resumes only after the explicit attachment action and remains waiting',async()=>{
  const controllers=new Map([['authoring-existing','example-same-authority']]);
  const calls=[];
  let current={...state(),status:'paused'};
  const api=async(operation,args)=>{
    calls.push(operation);
    if(operation==='run_definition')return definition;
    if(operation==='get')return current;
    if(operation==='run_snapshot'){
      assert.equal(args.control_token,'example-same-authority');
      return {state:current,events:[]};
    }
    if(operation==='resume'){
      assert.equal(args.control_token,'example-same-authority');
      current={...current,status:'running',sequence:13};
      return current;
    }
    throw new Error(`Unexpected operation ${operation}`);
  };
  const inspected=await inspectControlledAuthoringRun(api,pack,current.run_id,controllers);
  assert.equal(inspected.inspected.continuation,'guidance');
  assert.equal(current.status,'paused');
  assert.equal(calls.includes('resume'),false);
  const attached=await continueControlledAuthoringRun(api,pack,current.run_id,controllers);
  assert.equal(attached.checked.continuation,'guidance');
  assert.equal(calls.filter(operation=>operation==='resume').length,1);
  assert.equal(calls.includes('advance_authoring'),false);
});

test('remount exposes exact Run inspection when detail adoption superseded a cached session token',async()=>{
  const key='source-draft/'+pack.revision_hash;
  const sessions=new Map([[key,{run_id:'authoring-existing',control_token:'example-old-token'}]]);
  const controllers=new Map([['authoring-existing','example-new-token']]);
  assert.equal(mountedAuthoringSession(sessions,controllers,key),null);
  const calls=[];
  const api=async(operation,args)=>{
    calls.push(operation);
    if(operation==='run_definition')return definition;
    if(operation==='get')return state();
    if(operation==='run_snapshot'){
      assert.equal(args.control_token,'example-new-token');
      return {state:state(),events:[]};
    }
    throw new Error(`Unexpected operation ${operation}`);
  };
  const {inspected,controlToken}=await inspectControlledAuthoringRun(api,pack,'authoring-existing',controllers);
  assert.equal(inspected.continuation,'guidance');
  sessions.set(key,{run_id:inspected.run_id,control_token:controlToken});
  assert.deepEqual(mountedAuthoringSession(sessions,controllers,key),{run_id:'authoring-existing',control_token:'example-new-token'});
  assert.deepEqual(calls,['run_definition','get','run_snapshot']);
});
