import test from 'node:test';
import assert from 'node:assert/strict';
import {executionEnvelope} from '../lib/workflow-execution-envelope.mjs';

function fixture({ready=true,tools=[{name:'node',status:'found',path:process.execPath}],environment=[]}={}){
 const node={id:'work',type:'agent',executor:{kind:'provider',provider_id:'native'},access:'read_only',prompt_template:'Produce the assigned explanation.'};
 const state={run_id:'neutral',workflow_id:'neutral',workflow_revision:1,inputs:{},constraints:{runtime_requirements:{executables:[{name:'node',version:'>=20'}]},runtime_environment:{status:ready?'ready':'attention',tools}},permissions:{workspace:process.cwd(),access:'read_only',allowed_paths:[]},nodes:{work:{status:'claimed',output:null}}};
 const pins={executable_projection_version:1,root:{workflow:{finalization:{node_id:'final'},skill_policy:{mode:'cooperative',implicit:'allow',ambient_allow:[],shadowed_skill_paths:[]},edges:[],requirements:{executables:[{name:'node',version:'>=20'}],environment}},resources:[]},providers:[{id:'native',kind:'native_agent'}],skills:[]};
 return {node,state,pins};
}
test('prepared native executable projection retains exact locations without assigning another dependency probe',()=>{
 const f=fixture(),e=executionEnvelope(f.node,f.state,f.pins,{id:'attempt'},'lease');
 assert.doesNotMatch(e.prompt_template,/Report unresolved dependencies/);
 assert.match(e.prompt_template,/Run executables:/);assert(e.prompt_template.includes(process.execPath.replaceAll('\\','\\\\')));
 assert.deepEqual(e.constraints.runtime_environment.tools,f.state.constraints.runtime_environment.tools);
});
test('unprepared or incomplete executable projections retain their unresolved declarations',()=>{
 for(const options of [{ready:false},{tools:[]},{tools:[{name:'node',status:'missing',path:process.execPath}]}]){
  const f=fixture(options),e=executionEnvelope(f.node,f.state,f.pins,{id:'attempt'},'lease');
  assert.match(e.prompt_template,/Report unresolved dependencies/);
 }
});
test('verified executables do not discard separate environment declarations',()=>{
 const f=fixture({environment:['NEUTRAL_REQUIRED_FLAG']}),e=executionEnvelope(f.node,f.state,f.pins,{id:'attempt'},'lease');
 assert.match(e.prompt_template,/NEUTRAL_REQUIRED_FLAG/);assert.match(e.prompt_template,/"executables":\[\]/);
});
test('legacy ready metadata cannot hide a missing declared executable',()=>{
 const f=fixture({tools:[]});delete f.state.constraints.runtime_requirements;
 assert.match(executionEnvelope(f.node,f.state,f.pins,{id:'attempt'},'lease').prompt_template,/Report unresolved dependencies/);
});
test('historical native executable projection retains its original prompt bytes',()=>{
 const f=fixture();delete f.pins.executable_projection_version;
 const e=executionEnvelope(f.node,f.state,f.pins,{id:'attempt'},'lease');
 assert.equal(e.prompt_template,'Dependencies: '+JSON.stringify(f.pins.root.workflow.requirements)+'. Report unresolved dependencies with command/error evidence.\n'
  +'Run executables: '+JSON.stringify(f.state.constraints.runtime_environment.tools)+'. Use these locations and a process-local PATH for helpers.\nProduce the assigned explanation.');
});
test('unknown executable projection version fails rather than reinterpreting a dispatch',()=>{
 const f=fixture();f.pins.executable_projection_version=2;
 assert.throws(()=>executionEnvelope(f.node,f.state,f.pins,{id:'attempt'},'lease'),{code:'EXECUTABLE_PROJECTION_VERSION'});
});
