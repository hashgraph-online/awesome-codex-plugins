import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,mkdir,rm} from 'node:fs/promises';
import {join} from 'node:path';
import {tmpdir} from './physical-tempdir.mjs';
import {createDraft} from '../lib/workflow-schema.mjs';
import {validateWorkflowGraph} from '../lib/workflow-validator.mjs';
import {WorkflowStore} from '../lib/workflow-store.mjs';
import {WorkflowRuntime} from '../lib/workflow-runtime.mjs';
import {SHARED_PREFIX_SCHEMA,sharedPrefixDeclarationIssue} from '../lib/execution/shared-prefix-contract.mjs';
import {validateData} from '../lib/workflow-data-schema.mjs';

const object=properties=>({type:'object',properties,required:Object.keys(properties),additionalProperties:false});
function graph(){
  return {...createDraft('prefix-test','Shared setup fixture'),status:'ready',
    skill_policy:{mode:'cooperative',implicit:'deny',ambient_allow:[],shadowed_skill_paths:[]},
    inputs_schema:object({jobs:{type:'array',minItems:1,maxItems:3,items:{type:'string'}},project:{type:'string'}}),
    finalization:{required:true,node_id:'final'},nodes:[{id:'start',type:'start'},
      {id:'work',type:'agent',executor:{kind:'main',mode:'worker'},access:'read_only',path_scope:[],
        approval:{required:false},retry:{max_attempts:1},input_bindings:{jobs:'/inputs/jobs',project:'/inputs/project'},
        prompt_template:'Analyze the assigned input.',outputs_schema:object({results:{type:'array',items:object({finding:{type:'string'}})}}),
        subagent_count:'auto',fanout:{input:'jobs',item_name:'job',result_output:'results',distribution:'one_per_item',
          scheduling:'parallel',join:'all_required',result_mode:'per_item',shared_prefix:{common_inputs:['project']}}},
      {id:'final',type:'agent',executor:{kind:'main',mode:'orchestration'},access:'read_only',path_scope:[],
        approval:{required:false},retry:{max_attempts:1},input_bindings:{},prompt_template:'Accept.',
        outputs_schema:object({accepted:{type:'boolean'}})}, {id:'end',type:'end'}],
    edges:[['start','work'],['work','final'],['final','end']].map(([source,target])=>({id:source+'-'+target,source,target}))};
}

test('shared prefix graph accepts explicit common bindings and retains fresh default',()=>{
  const workflow=graph();assert.equal(validateWorkflowGraph(workflow,{providers:[]}).valid,true);
  workflow.nodes[1].fanout.shared_prefix={common_inputs:[]};
  assert.equal(validateWorkflowGraph(workflow,{providers:[]}).valid,true);
  delete workflow.nodes[1].fanout.shared_prefix;
  assert.equal(validateWorkflowGraph(workflow,{providers:[]}).valid,true);
});

test('shared prefix rejects item topics, invalid bindings, unsupported modes and extra authority fields',()=>{
  for(const declaration of [{common_inputs:['jobs']},{common_inputs:['job']},{common_inputs:['missing']},
    {common_inputs:['project','project']},{common_inputs:['project'],path:'foreign'},
    {common_inputs:Array.from({length:33},(_,i)=>'binding'+i)},null]){
    const workflow=graph();workflow.nodes[1].fanout.shared_prefix=declaration;
    assert(validateWorkflowGraph(workflow,{providers:[]}).errors.some(error=>error.code==='MAIN_SHARED_PREFIX'));
  }
  for(const patch of [{executor:{kind:'main',mode:'orchestration'}},{skill_policy:{mode:'strict'}},
    {executor:{kind:'provider',provider_id:'foreign'}}]){
    const node={...graph().nodes[1],...patch};assert(sharedPrefixDeclarationIssue(node,'cooperative'));
  }
  assert.throws(()=>validateData({common_inputs:['same','same']},SHARED_PREFIX_SCHEMA));
});

test('one prefix setup reservation is durable and does not spend the item correction budget',async t=>{
  const root=await mkdtemp(join(tmpdir(),'prefix-reservation-'));
  t.after(()=>rm(root,{recursive:true,maxRetries:3,retryDelay:100}));
  const workspace=join(root,'workspace');await mkdir(workspace);
  const store=await new WorkflowStore(join(root,'workflows')).initialize();await store.create(graph());
  const runtime=await new WorkflowRuntime({workflowStore:store,runRoot:join(root,'runs')}).initialize();
  const run=await runtime.start({workflow_id:'prefix-test',workspace,access:'read_only',allowed_paths:[],
    main_actor:'root',inputs:{jobs:['a','b'],project:'common constraints'}});
  const lease=await runtime.claimHostMain(run.run_id,{node_id:'work',owner:'root',request_id:'prefix-claim',control_token:run.control_token});
  const binding={...lease,control_token:run.control_token};
  await assert.rejects(runtime.reserveHostMainPrefixTurn(run.run_id,{...binding,control_token:'wrong'}));
  assert.deepEqual(await runtime.reserveHostMainPrefixTurn(run.run_id,binding),{reserved:true});
  await assert.rejects(runtime.reserveHostMainPrefixTurn(run.run_id,binding),{code:'HOST_MAIN_PREFIX_RESERVED'});
  assert.equal((await runtime.reserveHostMainItemTurn(run.run_id,{...binding,item_index:0})).remaining,0);
  assert.equal((await runtime.reserveHostMainItemTurn(run.run_id,{...binding,item_index:1})).remaining,0);
  const attempt=(await runtime.runs.read(run.run_id)).state.nodes.work.attempts[0];
  assert.equal(attempt.main_shared_prefix_turns,1);assert.deepEqual(attempt.main_item_turns,{'0':1,'1':1});
});
