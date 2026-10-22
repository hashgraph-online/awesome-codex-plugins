import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,mkdir,rm,writeFile,readFile,link,symlink,readdir} from 'node:fs/promises';
import {resolveAuditPath} from '../lib/config.mjs';
import {join,dirname,sep} from 'node:path';
import {runPermissions} from '../lib/workflow-execution-envelope.mjs';
import {PREPARED_STARTUP_LIMIT,createPreparedStartup,resolvePreparedStartup} from '../lib/execution/prepared-startup-record.mjs';
import {tmpdir} from './physical-tempdir.mjs';
import {readyWorkflow,edge} from './fixtures/workflow-fixtures.mjs';
import {WorkflowService} from '../lib/workflow-service.mjs';
import {WorkflowRunStore} from '../lib/workflow-run-store.mjs';
import {DEFAULT_CONFIG_PATH,handleRpc} from '../server.mjs';
import {startupSemanticContract,validateStartupSemanticSubmission} from '../lib/execution/workflow-startup-semantic.mjs';
import {digest,canonicalJSON} from '../lib/workflow-revisions.mjs';
import {readOwnedAuthorityForThread} from '../lib/execution/owned-workflow-authority.mjs';
import {completeMainOrchestration} from '../lib/execution/main-orchestration.mjs';
import {workflowToolDefinitions} from '../lib/workflow-tools.mjs';
import {randomUUID,createHmac} from 'node:crypto';
import {spawn} from 'node:child_process';
import {WORKFLOW_EXECUTION_TOOL_NAMESPACE} from '../lib/workflow-call-policy.mjs';
const taskInputs={task:'Explain a neutral process.'};
const inputsHash=digest(canonicalJSON(taskInputs));
const executeDescriptor=(descriptor,output,call)=>{
 assert.equal(descriptor.kind,'direct_mcp');assert.equal(descriptor.scope,'direct_mcp_only');
 assert.equal(descriptor.tool,WORKFLOW_EXECUTION_TOOL_NAMESPACE+descriptor.tool_name);
 const args=JSON.parse(canonicalJSON(descriptor.arguments));
 if(descriptor.slot!=='none'){
  assert.equal(descriptor.slot,'initial_output');args.initial_output=output;
 }
 return call(args);
};

test('typed startup preparation validates the real semantic schema and generates a complete reusable invocation without a Run',async t=>{
 const f=await fixture(t);
 const prepared=await f.publicRpc('workflow_startup_contract',{...f.startArgs,initial_output:{mode:'video'}});
 assert.equal(prepared.error,undefined);assert.notEqual(prepared.result.isError,true,JSON.stringify(prepared.result));
 const contract=prepared.result.structuredContent??JSON.parse(prepared.result.content[0].text);
 assert.equal(contract.invocation_adapter.slot,'none');
 assert.equal(contract.model_invocations,0);assert.equal(contract.runs_started,0);
 assert.equal((await f.service.call('runs')).length,0);assert.equal(f.checks.length,0);
 const received=[];
 const execute=()=>executeDescriptor(contract.invocation_adapter,undefined,async args=>{received.push(args);return {};});
 await execute();await execute();
 assert.deepEqual(received[0],received[1]);
 assert.deepEqual(received[0],{startup_reference:contract.startup_reference});
 for(const output of [{mode:'invented'},{mode:{}},{mode:'page',extra:true},null]){
  const invalid=await f.publicRpc('workflow_startup_contract',{...f.startArgs,initial_output:output});
  assert.equal(invalid.result.isError,true);assert.equal((await f.service.call('runs')).length,0);
 }
 const ordinary=await f.service.call('startup_contract',f.startArgs);
 assert.equal(ordinary.invocation_adapter.slot,'initial_output','Existing unfilled callers remain compatible');
});

test('the complete typed invocation retains original checker, input pin and idempotent launch lifecycle',async t=>{
 const f=await fixture(t);
 const prepared=await f.service.call('startup_contract',{...f.startArgs,initial_output:{mode:'video'}});
 const outputs=[];
 const execute=()=>executeDescriptor(prepared.invocation_adapter,undefined,async args=>{
   const response=await f.publicRpc('workflow_start_prepared',args);assert.notEqual(response.result.isError,true,JSON.stringify(response));outputs.push(response.result);return response.result;
  });
 await execute();await execute();
 const runs=await f.service.call('runs');assert.equal(runs.length,1);
 assert.equal(f.checks.length,1);assert.equal(f.launches(),1);
 assert.deepEqual(f.checks[0].output,{mode:'video'});
 assert(outputs.every(value=>JSON.parse(value.content[0].text).status==='orchestration_handoff'));
 const file='request.json';await writeFile(join(f.workspace,file),JSON.stringify(taskInputs));
 const {inputs,...fileArgs}=f.startArgs;
 const pinned=await f.service.call('startup_contract',{...fileArgs,inputs_path:file,initial_output:{mode:'page'}});
 await writeFile(join(f.workspace,file),JSON.stringify({task:'Changed original request.'}));
 const rejected=await executeDescriptor(pinned.invocation_adapter,undefined,async args=>
   (await f.publicRpc('workflow_start_prepared',args)).result);
 assert.equal(rejected.isError,true);assert.match(rejected.content[0].text,/WORKFLOW_STARTUP_INPUTS/);
 assert.equal((await f.service.call('runs')).length,1);assert.equal(f.checks.length,1);
});

const threadId='12345678-1234-4234-8234-123456789abc';

test('each launcher prepares its own fixed protocol and rejects sealed cross-transport startup before a Run',async t=>{
 for(const transport of ['code_mode','direct_mcp'])await t.test(transport,async t=>{
  const f=await fixture(t,{transport}),response=await f.publicRpc('workflow_startup_contract',{...f.startArgs,initial_output:{mode:'page'}});
  assert.notEqual(response.result.isError,true,JSON.stringify(response));
  const prepared=JSON.parse(response.result.content[0].text),expected=transport==='code_mode'?'functions_exec':'direct_mcp';
  assert.equal(prepared.invocation_adapter.kind,expected);assert.equal(prepared.invocation_adapter.slot,'none');
  const path=join(dirname(f.service.configPath),'workflow-preparations',`${prepared.startup_reference}.json`),record=JSON.parse(await readFile(path,'utf8'));
  assert.equal(record.payload.schema_version,2);assert.equal(record.payload.invocation_transport,transport);
  const other=transport==='code_mode'?'direct_mcp':'code_mode',args={startup_reference:prepared.startup_reference};
  const rejected=await handleRpc({jsonrpc:'2.0',id:'cross',method:'tools/call',params:{name:'workflow_start_prepared',_meta:{threadId},arguments:args}},
   {configPath:f.service.configPath,defaultConfigPath:DEFAULT_CONFIG_PATH,env:{WORKFLOW_MCP_TRANSPORT:other}});
  assert.equal(rejected.result.isError,true);assert.match(rejected.result.content[0].text,/WORKFLOW_PREPARATION_TRANSPORT/);
  assert.equal((await f.service.call('runs')).length,0);assert.equal(f.launches(),0);assert.equal(f.checks.length,0);
  const tampered=structuredClone(record);tampered.payload.invocation_transport=other;await writeFile(path,canonicalJSON(tampered));
  const badSeal=await f.publicRpc('workflow_start_prepared',args);assert.match(badSeal.result.content[0].text,/WORKFLOW_PREPARATION_RECORD/);
  await writeFile(path,canonicalJSON(record));
  const started=await f.publicRpc('workflow_start_prepared',args);assert.notEqual(started.result.isError,true,JSON.stringify(started));
  assert.equal(JSON.parse(started.result.content[0].text).invocation_adapter.kind,expected);
  assert.equal(f.launches(),1);assert.equal(f.checks.length,1);
 });
});

test('historical untagged sealed preparations retain only their original management contract',async t=>{
 const f=await fixture(t,{transport:'code_mode'}),prepared=await f.service.call('startup_contract',{...f.startArgs,initial_output:{mode:'page'}});
 const root=join(dirname(f.service.configPath),'workflow-preparations'),path=join(root,`${prepared.startup_reference}.json`),record=JSON.parse(await readFile(path,'utf8'));
 record.payload.schema_version=1;delete record.payload.invocation_transport;
 record.seal=createHmac('sha256',await readFile(join(root,'seal-key'))).update(canonicalJSON(record.payload)).digest('hex');
 await writeFile(path,canonicalJSON(record));
 const args={startup_reference:prepared.startup_reference};
 const recovered=await resolvePreparedStartup(f.service.configPath,args);
 assert.equal(recovered.workflow_id,f.startArgs.workflow_id);
 await assert.rejects(resolvePreparedStartup(f.service.configPath,args,{invocationTransport:'direct_mcp'}),{code:'WORKFLOW_PREPARATION_TRANSPORT'});
 const started=await f.publicRpc('workflow_start_prepared',args);assert.notEqual(started.result.isError,true,JSON.stringify(started));
 assert.equal(JSON.parse(started.result.content[0].text).invocation_adapter.kind,'functions_exec');
});

test('Host-owned project_root omitted from typed and untyped prepared calls inherits the original Run workspace through retry and continuation',async t=>{
 for(const typed of [false,true])await t.test(typed?'typed':'untyped',async t=>{
  const f=await fixture(t,{projectRootInput:true}),workspace=f.workspace+sep+'.',
   business={...f.startArgs,workspace},expectedRoot=runPermissions(business).workspace;
  const response=await f.publicRpc('workflow_startup_contract',{...business,...(typed?{initial_output:{mode:'page'}}:{})});
  assert.notEqual(response.result.isError,true,JSON.stringify(response));
  const prepared=JSON.parse(response.result.content[0].text);
  assert.equal(prepared.runs_started,0);assert.equal(prepared.model_invocations,0);
  assert.deepEqual(prepared.inputs,taskInputs);assert.equal((await f.service.call('runs')).length,0);
  assert.equal(f.checks.length,0);assert.equal(f.launches(),0);
  const submission={startup_reference:prepared.startup_reference,...(typed?{}:{initial_output:{mode:'page'}})},
   recovered=await resolvePreparedStartup(f.service.configPath,submission,{invocationTransport:'direct_mcp'});
  assert.deepEqual(recovered.inputs,taskInputs);assert(!Object.hasOwn(recovered.inputs,'project_root'));
  assert.equal(recovered.startup_inputs_sha256,inputsHash);assert.equal(recovered.workspace,workspace);
  const execute=()=>executeDescriptor(prepared.invocation_adapter,{mode:'page'},async args=>{
    assert.deepEqual(args,submission);
    const value=await f.publicRpc('workflow_start_prepared',args);
    assert.notEqual(value.result.isError,true,JSON.stringify(value));return value.result;
   });
  await execute();await execute();
  const [run]=await f.service.call('runs'),state=await f.service.call('get',{run_id:run.run_id});
  assert.equal(state.inputs.project_root,expectedRoot);assert.equal(state.permissions.workspace,expectedRoot);
  assert.equal(f.launches(),1);assert.equal(f.checks.length,1);assert.equal(f.waits(),1);
  const completed=await f.publicRpc('workflow_orchestration_complete',{output:{conclusion:'Verified neutral root inheritance.'}});
  assert.notEqual(completed.result.isError,true,JSON.stringify(completed));
  const terminal=await f.publicRpc('workflow_start_prepared',submission);
  assert.equal(JSON.parse(terminal.result.content[0].text).status,'succeeded');
  assert.equal((await f.service.call('runs')).length,1);assert.equal(f.launches(),1);assert.equal(f.checks.length,1);
 });
});

test('Host-owned project_root normalization feeds initial bindings while retaining raw inputs and explicit roots',async t=>{
 const f=await fixture(t,{projectRootInput:true,initialProjectRoot:true}),workspace=f.workspace+sep+'.';
 const omitted=await f.publicRpc('workflow_startup_contract',{...f.startArgs,workspace});
 assert.notEqual(omitted.result.isError,true,JSON.stringify(omitted));
 const contract=JSON.parse(omitted.result.content[0].text);
 assert.deepEqual(contract.inputs,{...taskInputs,project_root:runPermissions({...f.startArgs,workspace}).workspace});
 const raw=await resolvePreparedStartup(f.service.configPath,{startup_reference:contract.startup_reference,initial_output:{mode:'page'}},{invocationTransport:'direct_mcp'});
 assert.deepEqual(raw.inputs,taskInputs);assert.equal(raw.startup_inputs_sha256,inputsHash);
 const explicitInputs={...taskInputs,project_root:join(dirname(f.workspace),'explicit-root')};
 const explicit=await f.publicRpc('workflow_startup_contract',{...f.startArgs,inputs:explicitInputs,initial_output:{mode:'page'}});
 assert.notEqual(explicit.result.isError,true,JSON.stringify(explicit));
 const explicitContract=JSON.parse(explicit.result.content[0].text);
 assert.deepEqual(explicitContract.inputs,explicitInputs);
 const retained=await resolvePreparedStartup(f.service.configPath,{startup_reference:explicitContract.startup_reference},{invocationTransport:'direct_mcp'});
 assert.deepEqual(retained.inputs,explicitInputs);assert.equal(retained.startup_inputs_sha256,digest(canonicalJSON(explicitInputs)));
 assert.equal(f.launches(),0);assert.equal(f.checks.length,0);assert.equal((await f.service.call('runs')).length,0);
});

test('Host-owned project_root defaults retain schema rejection for explicit mismatches and malformed other inputs',async t=>{
 const f=await fixture(t,{projectRootInput:true,initialProjectRoot:true,projectRootConstraint:true});
 for(const inputs of [{...taskInputs,project_root:'schema-mismatch'},{...taskInputs,project_root:42},{task:42},{}]){
  const result=await f.publicRpc('workflow_startup_contract',{...f.startArgs,inputs,initial_output:{mode:'page'}});
  assert.equal(result.result.isError,true);assert.match(result.result.content[0].text,/DATA_INVALID/);
 }
 const valid=await f.publicRpc('workflow_startup_contract',f.startArgs);
 assert.notEqual(valid.result.isError,true,JSON.stringify(valid));
 assert.equal(JSON.parse(valid.result.content[0].text).inputs.project_root,f.workspace);
 assert.equal(f.launches(),0);assert.equal(f.checks.length,0);assert.equal((await f.service.call('runs')).length,0);
});

test('prepared untyped submission authenticates the caller, retains one exact Run and rejects changed semantics through terminal continuation',async t=>{
 const f=await fixture(t),prepared=await f.service.call('startup_contract',f.startArgs);
 const args={startup_reference:prepared.startup_reference,initial_output:{mode:'page'}};
 const schema=workflowToolDefinitions().find(tool=>tool.name==='workflow_start_prepared').inputSchema;
 assert.deepEqual(Object.keys(schema.properties),['startup_reference','initial_output']);
 const unauthenticated=await handleRpc({jsonrpc:'2.0',id:1,method:'tools/call',params:{name:'workflow_start_prepared',arguments:args}},
  {configPath:f.service.configPath,env:{}});
 assert.match(unauthenticated.result.content[0].text,/MODEL_THREAD_ID/);
 for(const field of ['revision_hash','startup_inputs_sha256','workspace','access','launch_key','main_actor','native_parent_thread_id']){
  const bad=await f.publicRpc('workflow_start_prepared',{...args,[field]:'override'});assert.equal(bad.result.isError,true);
 }
 const submit=async value=>f.publicRpc('workflow_start_prepared',value);
 for(let i=0;i<2;i++)assert.notEqual((await submit(args)).result.isError,true);
 assert.equal(f.launches(),1);assert.equal(f.checks.length,1);assert.equal(f.waits(),1);
 const conflict=await submit({...args,initial_output:{mode:'video'}});
 assert.match(conflict.result.content[0].text,/WORKFLOW_STARTUP_CONFLICT/);
 const completed=await f.publicRpc('workflow_orchestration_complete',{output:{conclusion:'Neutral verified result.'}});
 assert.notEqual(completed.result.isError,true,JSON.stringify(completed));
 const terminal=await submit(args);assert.equal(JSON.parse(terminal.result.content[0].text).status,'succeeded');
 const runs=await f.service.call('runs');assert.equal(runs.length,1);assert.equal(f.launches(),1);assert.equal(f.checks.length,1);
 const record=await (await f.service.open()).runtime.runs.read(runs[0].run_id);
 assert.equal(record.pins.root.revision_hash,f.pack.revision_hash);
 assert.equal(record.state.constraints.native_parent_thread_id,threadId);
 const observations=(await readFile(resolveAuditPath(f.service.configPath),'utf8')).trim().split('\n').map(JSON.parse)
  .filter(item=>item.event==='workflow-foreground-operation'&&item.action==='start_prepared');
 assert(observations.length>0);assert(observations.every(item=>!item.detail.includes(args.startup_reference)));
});

test('prepared typed output is immutable and missing semantics fail before launch',async t=>{
 const f=await fixture(t),typed=await f.service.call('startup_contract',{...f.startArgs,initial_output:{mode:'page'}}),
  untyped=await f.service.call('startup_contract',f.startArgs);
 for(const args of [{startup_reference:typed.startup_reference,initial_output:{mode:'page'}},
  {startup_reference:typed.startup_reference,initial_output:{mode:'video'}},{startup_reference:untyped.startup_reference},
  {startup_reference:untyped.startup_reference.toUpperCase(),initial_output:{mode:'page'}},
  {startup_reference:'../'+untyped.startup_reference,initial_output:{mode:'page'}}]){
  const result=await f.publicRpc('workflow_start_prepared',args);assert.equal(result.result.isError,true);
 }
 assert.equal((await f.service.call('runs')).length,0);assert.equal(f.launches(),0);assert.equal(f.checks.length,0);
});

test('prepared records fail visibly for missing, tampered, noncanonical, identity-changed, hardlinked and oversized bytes',async t=>{
 const f=await fixture(t),root=join(dirname(f.service.configPath),'workflow-preparations');
 for(const defect of ['missing','tamper','identity','format','hardlink','oversize']){
  const p=await f.service.call('startup_contract',f.startArgs),path=join(root,`${p.startup_reference}.json`),bytes=await readFile(path);
  const record=JSON.parse(bytes);
  if(defect==='missing')await rm(path);
  if(defect==='tamper'){record.payload.args.access='read_only';await writeFile(path,canonicalJSON(record));}
  if(defect==='identity'){record.payload.startup_reference=randomUUID();await writeFile(path,canonicalJSON(record));}
  if(defect==='format')await writeFile(path,JSON.stringify(record,null,2));
  if(defect==='hardlink')await link(path,join(root,`${p.startup_reference}-alias`));
  if(defect==='oversize')await writeFile(path,Buffer.alloc(PREPARED_STARTUP_LIMIT+1,32));
  const result=await f.publicRpc('workflow_start_prepared',{startup_reference:p.startup_reference,initial_output:{mode:'page'}});
  assert.equal(result.result.isError,true,defect);assert.equal(f.launches(),0);assert.equal(f.checks.length,0);
 }
 assert.equal((await f.service.call('runs')).length,0);
 const retained=await f.service.call('startup_contract',f.startArgs);
 const key=join(root,'seal-key');await writeFile(key,Buffer.alloc(32,1));
 const result=await f.publicRpc('workflow_start_prepared',{startup_reference:retained.startup_reference,initial_output:{mode:'page'}});
 assert.match(result.result.content[0].text,/WORKFLOW_PREPARATION_RECORD/);assert.equal(f.launches(),0);
});

test('prepared references retain the current revision fence before any Run exists',async t=>{
 const f=await fixture(t),prepared=await f.service.call('startup_contract',f.startArgs);
 const workflow=structuredClone(f.pack.workflow);workflow.description='Changed neutral definition.';
 await f.service.call('save',{workflow_id:workflow.id,workflow,expected_revision:f.pack.revision_hash});
 const result=await f.publicRpc('workflow_start_prepared',{startup_reference:prepared.startup_reference,initial_output:{mode:'page'}});
 assert.match(result.result.content[0].text,/WORKFLOW_STARTUP_REVISION/);assert.equal(f.launches(),0);assert.equal(f.checks.length,0);
 assert.equal((await f.service.call('runs')).length,0);
});

test('a valid seal never substitutes for the full legacy public startup schema',async t=>{
 const f=await fixture(t);
 for(const invalid of [{main_actor:'forged'},{run_id:randomUUID()},{access:'unbounded'}]){
  // The module is Host-internal. A malformed Host preparation must still fail
  // at the ordinary public schema boundary, before metadata stamps or launch.
  const args={...f.startArgs,revision_hash:f.pack.revision_hash,startup_inputs_sha256:inputsHash,launch_key:randomUUID(),...invalid};
  const startup_reference=await createPreparedStartup(f.service.configPath,args,{typed:true,initialOutput:{mode:'page'},invocationTransport:'direct_mcp'});
  const result=await f.publicRpc('workflow_start_prepared',{startup_reference});
  assert.match(result.result.content[0].text,/DATA_INVALID/);assert.equal(f.launches(),0);assert.equal(f.checks.length,0);
 }
 assert.equal((await f.service.call('runs')).length,0);
});

test('bounded preparation seals persist across resolution and fail rather than regenerate when the key is missing',async t=>{
 const root=await mkdtemp(join(tmpdir(),'preparation-store-'));t.after(()=>rm(root,{recursive:true,maxRetries:3,retryDelay:100}));
 const configPath=join(root,'config.json'),args={workspace:join(root,'work'),launch_key:randomUUID()};
 const reference=await createPreparedStartup(configPath,args,{typed:true,initialOutput:{text:'semantic'}});
 const keyBefore=await readFile(join(root,'workflow-preparations','seal-key'));
 await createPreparedStartup(configPath,args,{typed:true,initialOutput:{text:'other semantic'}});
 assert.deepEqual(await readFile(join(root,'workflow-preparations','seal-key')),keyBefore);
 assert.deepEqual(await resolvePreparedStartup(configPath,{startup_reference:reference}),{...args,initial_output:{text:'semantic'}});
 await rm(join(root,'workflow-preparations','seal-key'));
 await assert.rejects(resolvePreparedStartup(configPath,{startup_reference:reference}),{code:'ENOENT'});
 assert(!(await readdir(join(root,'workflow-preparations'))).includes('seal-key'));
});

test('preparation rejects symlink storage before reading its target',async t=>{
 const root=await mkdtemp(join(tmpdir(),'preparation-link-'));t.after(()=>rm(root,{recursive:true,maxRetries:3,retryDelay:100}));
 const configPath=join(root,'config.json'),reference=await createPreparedStartup(configPath,{},{}),
  path=join(root,'workflow-preparations',`${reference}.json`),target=join(root,'target.json');
 await writeFile(target,await readFile(path));await rm(path);
 try { await symlink(target,path,'file'); }
 catch(error) { if(process.platform==='win32'&&error.code==='EPERM'){t.skip('Windows file symlink privilege unavailable');return;}throw error; }
 await assert.rejects(resolvePreparedStartup(configPath,{startup_reference:reference,initial_output:{}}),{code:'WORKFLOW_SYMLINK'});
});

test('prepared startup refuses a Host storage area inside the actual business workspace without creating storage',async t=>{
 const f=await fixture(t),root=dirname(f.service.configPath);
 const result=await f.publicRpc('workflow_startup_contract',{...f.startArgs,workspace:root});
 assert.match(result.result.content[0].text,/WORKFLOW_PREPARATION_WORKSPACE/);
 await assert.rejects(readdir(join(root,'workflow-preparations')),{code:'ENOENT'});
 assert.equal(f.launches(),0);assert.equal((await f.service.call('runs')).length,0);
 const alias=join(root,'workspace-alias');await symlink(root,alias,process.platform==='win32'?'junction':'dir');
 const linked=await f.publicRpc('workflow_startup_contract',{...f.startArgs,workspace:alias});
 assert.match(linked.result.content[0].text,/WORKFLOW_SYMLINK/);
 await assert.rejects(readdir(join(root,'workflow-preparations')),{code:'ENOENT'});
});
const routeSchema={type:'object',properties:{mode:{type:'string',enum:['page','video']}},required:['mode'],additionalProperties:false};
function graph(){
 const workflow=readyWorkflow('neutral-routing');workflow.skill_policy.mode='cooperative';
 const final=workflow.nodes.find(n=>n.id==='final');final.executor={kind:'main',mode:'orchestration'};
 final.outputs_schema={type:'object',properties:{conclusion:{type:'string'}},required:['conclusion'],additionalProperties:false};
 final.input_bindings={mode:'/nodes/choose/output/mode'};
 const first={...structuredClone(final),id:'choose',name:'Choose the requested form',prompt_template:'Use the original request and current conversation to choose page or video.',
  input_bindings:{task:'/inputs/task'},outputs_schema:routeSchema,resources:[]};
 workflow.nodes.splice(1,0,first);workflow.edges=[edge('start','choose'),edge('choose','final'),edge('final','end')];
 return workflow;
}
test('startup contract exposes only the unique input-bound initial Main semantic contract',()=>{
 const workflow=graph(),pack={workflow,revision_hash:'a'.repeat(64),resources:[]};
 const contract=startupSemanticContract(pack);
 assert.equal(contract.workflow_id,workflow.id);assert.equal(contract.revision_hash,pack.revision_hash);
 assert.equal(contract.prompt,workflow.nodes.find(n=>n.id==='choose').prompt_template);
 assert.deepEqual(contract.response_schema,routeSchema);assert.deepEqual(contract.input_bindings,{task:'/inputs/task'});
 assert(!Object.hasOwn(contract,'workflow'));assert(!Object.hasOwn(contract,'node_id'));
 assert.equal(validateStartupSemanticSubmission(pack,{revision_hash:pack.revision_hash,initial_output:{mode:'video'}}).node_id,'choose');
 assert.throws(()=>validateStartupSemanticSubmission(pack,{initial_output:{mode:'page'}}),{code:'WORKFLOW_STARTUP_REVISION'});
 assert.throws(()=>validateStartupSemanticSubmission(pack,{revision_hash:'b'.repeat(64),initial_output:{mode:'page'}}),{code:'WORKFLOW_STARTUP_REVISION'});
 assert.throws(()=>validateStartupSemanticSubmission(pack,{revision_hash:pack.revision_hash,initial_output:{mode:'invented'}}));
});
for(const [name,mutate] of [
 ['a tool before the first Main',w=>{w.nodes.find(n=>n.id==='choose').type='tool';}],
 ['a persistent or isolated executor',w=>{w.nodes.find(n=>n.id==='choose').executor={kind:'main'};}],
 ['an approval boundary',w=>{w.nodes.find(n=>n.id==='choose').approval={required:true};}],
 ['upstream output bindings',w=>{w.nodes.find(n=>n.id==='choose').input_bindings={task:'/nodes/other/output'};}],
 ['an upstream zip binding',w=>{w.nodes.find(n=>n.id==='choose').input_bindings={task:{path:'/inputs/tasks',zip:'/nodes/other/output'}};}],
 ['final acceptance',w=>{w.finalization.node_id='choose';}],
 ['fan-out at startup',w=>{w.edges.push(edge('start','final'));}],
 ['required artifacts',w=>{w.nodes.find(n=>n.id==='choose').required_artifacts=[{path:'out.html',requirement_id:'page'}];}],
 ['a loop involving startup',w=>{w.loops=[{node_ids:['choose','final'],entry_node:'choose',exit_node:'final'}];}]
])test('startup submission cannot bypass '+name,()=>{
 const workflow=graph();mutate(workflow);const pack={workflow,revision_hash:'a'.repeat(64),resources:[]};
 assert.throws(()=>startupSemanticContract(pack),{code:'WORKFLOW_STARTUP_NOT_ELIGIBLE'});
});

async function fixture(t,{verified=true,execute,compatibleFinal=false,waitFailureOnce=false,projectRootInput=false,initialProjectRoot=false,projectRootConstraint=false,transport='direct_mcp'}={}){
 const directory=await mkdtemp(join(tmpdir(),'startup-semantic-')),workspace=join(directory,'workspace');await mkdir(workspace);
 const configPath=join(directory,'control-plane.json'),checks=[];let cancellations=0;
 const tool={id:'route-check',identity:{name:'route-check-fixture',version:'1',sha256:digest('neutral-route-check')},argv:['check'],
  input_schema:{type:'object',properties:{inputs:{},output:routeSchema},required:['inputs','output'],additionalProperties:false},
  output_schema:{type:'object',properties:{verified:{type:'boolean'}},required:['verified'],additionalProperties:false},env_allow:[],
  permissions:{network:false,read_paths:['.'],write_paths:[]},output_cap_bytes:1024,deadline_ms:1000,idempotency:{mode:'safe'}};
 const broker={identity:tool.identity,attestation:{qualified:true,cancellable:true,effect_observation:true,tool_identity:tool.identity,broker_id:'route-check',evidence_sha256:digest('qualified')},
  execute:async request=>{checks.push(request.input);return execute?execute(request):{exit_code:0,output:{verified},effects:{observed:true,changed_paths:[],outside_paths:[],artifacts:[]}};},
  cancel:async()=>{cancellations++;return {termination_confirmed:true,effects:{observed:true,changed_paths:[],outside_paths:[],artifacts:[]}};}};
 let launches=0,waits=0;
 const capabilities={hostToolRegistry:{[tool.id]:broker},nativeParentVerifier:async parent=>assert.equal(parent,threadId),
  launchDetachedHostMain:async args=>{launches++;return {run_id:args.runId,status:'starting'};},
  waitForOwnedWorkflow:async (service,started)=>{waits++;const {drive}=await service.open();
   if(waitFailureOnce&&waits===1)throw Object.assign(new Error('Neutral post-publication wait failure'),{code:'NEUTRAL_WAIT_FAILURE'});
   const handoff=await drive.advanceToMain(started.run_id,{control_token:started.control_token,owner:'codex',request_prefix:'neutral-startup'});
   assert.equal(handoff.stop_reason,'main_orchestration');
   return {run_id:started.run_id,control_token:started.control_token,status:'running',wake_reason:'native_handoff_required',next_action:'workflow_native_next'};
  }};
 const env=transport===undefined?{}:{WORKFLOW_MCP_TRANSPORT:transport};
 const service=new WorkflowService({configPath,defaultConfigPath:DEFAULT_CONFIG_PATH,env,capabilities});
 await service.call('migrate_v6',{}, {human:true});
 const workflow=graph();workflow.host_tools=[tool];
 if(projectRootInput){
  workflow.inputs_schema={type:'object',properties:{task:{type:'string'},project_root:{type:'string',...(projectRootConstraint?{const:workspace}:{})}},required:['task','project_root'],additionalProperties:false};
  workflow.nodes.find(node=>node.id==='final').input_bindings.project_root='/inputs/project_root';
  if(initialProjectRoot)workflow.nodes.find(node=>node.id==='choose').input_bindings.project_root='/inputs/project_root';
 }
 if(compatibleFinal)workflow.nodes.find(n=>n.id==='final').outputs_schema=routeSchema;
 const route=workflow.nodes.find(n=>n.id==='choose');route.access='bounded_write';route.path_scope=['.'];
 workflow.nodes.find(n=>n.id==='choose').completion_contract={on_missing:'block',outcome:'decision',host_check:{tool:tool.id,success_field:'verified'}};
 const validation=await service.call('validate',{workflow});assert.equal(validation.valid,true,JSON.stringify(validation));
 const pack=await service.call('create',{workflow});
 t.after(async()=>{await Promise.all(service.attemptAdmission.drainJobs.values());await rm(directory,{recursive:true,maxRetries:3,retryDelay:100});});
 const publicRpc=(name,args,{signal}={})=>handleRpc({jsonrpc:'2.0',id:1,method:'tools/call',params:{name,_meta:{threadId},arguments:args}},
  {configPath,defaultConfigPath:DEFAULT_CONFIG_PATH,env,serviceCapabilities:capabilities,signal});
 const startArgs={workflow_id:workflow.id,workspace,access:'bounded_write',allowed_paths:['.'],inputs:taskInputs};
 const rpc=args=>publicRpc('workflow_start',{...startArgs,...args});
 return {service,pack,checks,rpc,publicRpc,startArgs,workspace,launches:()=>launches,waits:()=>waits,cancellations:()=>cancellations};
}
test('ordinary MCP startup with missing initial bindings leaves no Run or active invocation and accepts corrected inputs',async t=>{
 const f=await fixture(t);
 const rejected=await f.rpc({inputs:{}});
 assert.equal(rejected.result.isError,true);assert.equal(JSON.parse(rejected.result.content[0].text).code,'BINDING_MISSING');
 assert.equal((await f.service.call('runs')).length,0);
 assert.equal(f.launches(),0);assert.equal(f.waits(),0);assert.equal(f.checks.length,0);
 const corrected=await f.rpc({});
 assert.equal(corrected.result.isError,undefined,JSON.stringify(corrected));
 const handoff=JSON.parse(corrected.result.content[0].text);assert.equal(handoff.status,'orchestration_handoff');
 const runs=await f.service.call('runs');assert.equal(runs.length,1);
 const state=await f.service.call('get',{run_id:runs[0].run_id});
 assert.equal(state.nodes.choose.attempts.length,1);assert.equal(state.nodes.final.attempts.length,0);
 assert.equal(f.launches(),1);assert.equal(f.waits(),1);assert.equal(f.checks.length,0);
});

test('a pre-publication failure preserves the reserved Run identity for the exact retry',async t=>{
 const f=await fixture(t),startup={args:{...f.startArgs,launch_key:randomUUID(),revision_hash:f.pack.revision_hash},initial_output:null};
 let reserved,attempts=0;const failure=Object.assign(new Error('Neutral failure before publication'),{code:'NEUTRAL_RESERVED_FAILURE'});
 for(let i=0;i<2;i++)await assert.rejects(f.service.withModelStartup(threadId,startup,async(hash,id,key)=>{
  attempts++;assert.equal(key,startup.args.launch_key);assert.equal(hash,digest(canonicalJSON(startup)));
  if(reserved)assert.equal(id,reserved);else reserved=id;throw failure;
 }),error=>error===failure);
 assert.equal(attempts,2);assert.equal((await f.service.call('runs')).length,0);
});

test('history removal before startup failure reconciliation never replays a committed publication',async t=>{
 const root=await mkdtemp(join(tmpdir(),'startup-publication-race-'));
 t.after(()=>rm(root,{recursive:true,maxRetries:3,retryDelay:100}));
 const runs=await new WorkflowRunStore(join(root,'workflow-runs')).initialize();
 const service=Object.create(WorkflowService.prototype);service.configPath=join(root,'config.json');
 service.authorityReader=async()=>({runs});
 const startup={args:{launch_key:randomUUID()},initial_output:null};
 const pins={resources:[],root:{workflow:{id:'neutral',nodes:[]}}};let launches=0,reserved;
 const failure=Object.assign(new Error('Neutral failure after publication and cleanup'),{code:'NEUTRAL_FAILURE'});
 await assert.rejects(service.withModelStartup(threadId,startup,async(hash,id,key)=>{
  launches++;reserved=id;
  await runs.create(id,pins,new Map(),{run_id:id,control_hash:digest('neutral-token'),pins_hash:digest(canonicalJSON(pins)),
    main_actor:'codex',status:'failed',updated_at:new Date().toISOString(),nodes:{},edges:{},approvals:{},
    constraints:{native_parent_thread_id:threadId,host_startup_sha256:hash,host_startup_key:key}},
    {hostAuthority:{run_id:id,control_token:'neutral-token'}});
  assert.deepEqual((await runs.cleanupHistory({olderThanMs:0})).deleted_run_ids,[id]);throw failure;
 }),error=>error===failure);
 const witness=await runs.startupPublication(reserved);assert.equal(witness.launch_key,startup.args.launch_key);
 await assert.rejects(service.withModelStartup(threadId,startup,()=>launches++),{code:'WORKFLOW_STARTUP_HISTORY_REMOVED'});
 assert.equal(launches,1);
 await assert.rejects(runs.create(reserved,pins,new Map(),{run_id:reserved,pins_hash:digest(canonicalJSON(pins)),nodes:{}}),
  {code:'WORKFLOW_STARTUP_PUBLICATION_REUSED'});
});

test('a second Node process cannot publish another startup while the exact chat gate is owned',{timeout:15000},async t=>{
 const f=await fixture(t),startup={args:{...f.startArgs,launch_key:randomUUID(),revision_hash:f.pack.revision_hash},initial_output:null};
 const source=`import {WorkflowService} from ${JSON.stringify(new URL('../lib/workflow-service.mjs',import.meta.url).href)};
 const service=new WorkflowService({configPath:process.argv[1],defaultConfigPath:process.argv[2],env:{}});
 await service.withModelStartup(${JSON.stringify(threadId)},${JSON.stringify(startup)},async()=>{
  process.send({entered:true});await new Promise(resolve=>process.once('message',resolve));throw new Error('Neutral release');
 }).catch(error=>{if(error.message!=='Neutral release')throw error;});process.disconnect();`;
 const child=spawn(process.execPath,['--input-type=module','-e',source,f.service.configPath,DEFAULT_CONFIG_PATH],
  {windowsHide:true,stdio:['ignore','pipe','pipe','ipc']});let stderr='';child.stderr.on('data',data=>stderr+=data);
 const closed=new Promise(resolve=>child.once('exit',(code,signal)=>resolve({code,signal})));
 t.after(async()=>{if(child.exitCode===null&&child.signalCode===null)child.kill();await closed;});
 const ready=await new Promise((resolve,reject)=>{child.once('message',resolve);child.once('error',reject);closed.then(status=>reject(new Error(`Child ended ${status.code}: ${stderr}`)));});
 assert.equal(ready.entered,true);let duplicate=0;
 await assert.rejects(f.service.withModelStartup(threadId,startup,()=>duplicate++),{code:'WORKFLOW_STORE_BUSY'});
 assert.equal(duplicate,0);assert.equal((await f.service.call('runs')).length,0);
 child.send({release:true});assert.equal((await closed).code,0,stderr);
});

test('startup retries rejoin one active Run and do not repeat accepted initial semantics',async t=>{
 const f=await fixture(t),args={launch_key:randomUUID(),revision_hash:f.pack.revision_hash,startup_inputs_sha256:inputsHash,initial_output:{mode:'page'}};
 const first=await f.rpc(args);assert.equal(first.result.isError,undefined,JSON.stringify(first));
 const run=(await f.service.call('runs'))[0];
 const second=await f.rpc(args);assert.equal(second.result.isError,undefined,JSON.stringify(second));
 assert.equal(JSON.parse(second.result.content[0].text).status,'orchestration_handoff');
 assert.equal(f.launches(),1);assert.equal(f.waits(),1);assert.equal(f.checks.length,1);
 assert.equal((await f.service.call('runs')).length,1);
 assert.equal((await f.service.call('get',{run_id:run.run_id})).nodes.choose.attempts.length,1);
 for(const conflicting of [{...args,initial_output:{mode:'video'}},{...args,launch_key:randomUUID()}]){
  const rejected=await f.rpc(conflicting);assert.equal(rejected.result.isError,true);
  assert.equal(JSON.parse(rejected.result.content[0].text).code,'WORKFLOW_STARTUP_CONFLICT');
 }
 assert.equal((await f.service.call('runs')).length,1);
});

test('a post-publication wait failure retains authority and startup retry resumes the same Run',async t=>{
 const f=await fixture(t,{waitFailureOnce:true}),args={launch_key:randomUUID(),revision_hash:f.pack.revision_hash,
  startup_inputs_sha256:inputsHash,initial_output:{mode:'page'}};
 const first=await f.rpc(args);assert.equal(first.result.isError,true);
 assert.equal(JSON.parse(first.result.content[0].text).code,'NEUTRAL_WAIT_FAILURE');
 const before=(await f.service.call('runs'))[0];assert(before);
 const second=await f.rpc(args);assert.equal(second.result.isError,undefined,JSON.stringify(second));
 const after=await f.service.call('runs');assert.equal(after.length,1);assert.equal(after[0].run_id,before.run_id);
 assert.equal(f.launches(),1);assert.equal(f.checks.length,1);
});

test('the exact startup invocation returns its terminal outcome while a new invocation has a new Run',async t=>{
 const f=await fixture(t),args={launch_key:randomUUID(),revision_hash:f.pack.revision_hash,
  startup_inputs_sha256:inputsHash,initial_output:{mode:'page'}};
 assert.equal((await f.rpc(args)).result.isError,undefined);
 const completed=await f.publicRpc('workflow_orchestration_complete',{output:{conclusion:'Verified neutral result.'}});
 assert.equal(completed.result.isError,undefined,JSON.stringify(completed));
 const before=(await f.service.call('runs'))[0];assert.equal(before.status,'succeeded');
 const rejoined=await f.rpc(args);assert.equal(rejoined.result.isError,undefined,JSON.stringify(rejoined));
 assert.equal(JSON.parse(rejoined.result.content[0].text).status,'succeeded');
 assert.equal((await f.service.call('runs')).length,1);assert.equal(f.launches(),1);
 const fresh=await f.rpc({...args,launch_key:randomUUID()});assert.equal(fresh.result.isError,undefined,JSON.stringify(fresh));
 assert.equal((await f.service.call('runs')).length,2);assert.equal(f.launches(),2);
});

test('public startup consumes the newly authored route once, checks it and returns final Main in the same call',async t=>{
 const f=await fixture(t);
 const response=await f.rpc({revision_hash:f.pack.revision_hash,startup_inputs_sha256:inputsHash,initial_output:{mode:'video'}});
 assert.equal(response.result.isError,undefined,JSON.stringify(response));
 const handoff=JSON.parse(response.result.content[0].text);
 assert.equal(handoff.status,'orchestration_handoff');assert.equal(handoff.context,'current_conversation');
 assert.match(handoff.task_bundle.task,/"mode":"video"/);
 assert.equal(f.launches(),1);assert.equal(f.waits(),1);assert.equal(f.checks.length,1);
 assert.deepEqual(f.checks[0].output,{mode:'video'});
 const runs=await f.service.call('runs');assert.equal(runs.length,1);
 const state=await f.service.call('get',{run_id:runs[0].run_id});
 assert.equal(state.nodes.choose.status,'succeeded');assert.deepEqual(state.nodes.choose.output,{mode:'video'});
 assert.equal(state.nodes.choose.attempts.length,1);assert.equal(state.nodes.choose.attempts[0].completion_turns,1);
 assert.equal(state.nodes.final.status,'running');
 const audit=(await readFile(resolveAuditPath(f.service.configPath),'utf8')).trim().split('\n').map(JSON.parse)
  .filter(item=>item.event==='workflow-model-authority-lookup');
 assert(audit.length>0);
 for(const item of audit){const detail=JSON.parse(item.detail);assert.equal(detail.thread_id,threadId);
  assert.equal(detail.fully_validated_candidates,1);assert(detail.inspected_start_records>=1);assert(Number.isSafeInteger(detail.duration_ms)&&detail.duration_ms>=0);}
 for(const field of ['run_id','control_token','node_id','attempt_id','lease_token'])assert.equal(handoff[field],undefined);
});

test('authority-only lookup avoids library open while execution still checks fresh configuration',async t=>{
 const f=await fixture(t);await f.rpc({});
 const originalOpen=f.service.open.bind(f.service),originalReader=f.service.authorityReader.bind(f.service);
 let opens=0;
 f.service.open=async(...args)=>{opens++;return originalOpen(...args);};
 await f.service.call('native_next',{}, {model:true,modelThreadId:threadId});assert.equal(opens,1);
 f.service.authorityReader=async()=>{
  const reader=await originalReader();
  const config=JSON.parse(await readFile(f.service.configPath,'utf8'));config.global.enabled=false;
  await writeFile(f.service.configPath,JSON.stringify(config));return reader;
 };
 await assert.rejects(f.service.call('native_next',{}, {model:true,modelThreadId:threadId}),{code:'CONTROL_DISABLED'});
 assert.equal(opens,2);
});
test('public startup rejects stale and malformed semantic submissions before a Run or launch exists',async t=>{
 const f=await fixture(t);
 for(const args of [{initial_output:{mode:'page'}},{revision_hash:'f'.repeat(64),initial_output:{mode:'page'}},{revision_hash:f.pack.revision_hash,initial_output:{mode:'other'}},
  {revision_hash:f.pack.revision_hash,initial_output:{mode:'page'}},
  {revision_hash:f.pack.revision_hash,startup_inputs_sha256:inputsHash,initial_output:{mode:'page'},inputs:{task:'Changed request.'}},
  {startup_inputs_sha256:inputsHash}]){
  const result=await f.rpc(args);assert.equal(result.result.isError,true);
 }
 assert.equal((await f.service.call('runs')).length,0);assert.equal(f.launches(),0);assert.equal(f.checks.length,0);
});

test('public contract binds original inputs and fixes launch arguments without creating a Run',async t=>{
 const f=await fixture(t);
 const response=await f.publicRpc('workflow_startup_contract',f.startArgs);
 assert.equal(response.result.isError,undefined,JSON.stringify(response));
 const contract=JSON.parse(response.result.content[0].text);
 assert.deepEqual(contract.inputs,taskInputs);assert.equal(contract.revision_hash,f.pack.revision_hash);
 assert.equal(contract.invocation_adapter.slot,'initial_output');assert.equal(contract.runs_started,0);
 assert.equal(contract.startup_binding,'exact_revision_and_inputs');
 assert.equal(contract.invocation_adapter.tool_name,'workflow_start_prepared');
 assert(!JSON.stringify(contract.invocation_adapter).includes(f.pack.revision_hash));assert(!JSON.stringify(contract.invocation_adapter).includes(inputsHash));
 assert.equal((await f.service.call('runs')).length,0);assert.equal(f.launches(),0);
 const result=await executeDescriptor(contract.invocation_adapter,{mode:'video'},async args=>{
   assert.deepEqual(args,{startup_reference:contract.startup_reference,initial_output:{mode:'video'}});
   const response=await f.publicRpc('workflow_start_prepared',args);assert.equal(response.result.isError,undefined,JSON.stringify(response));
   return JSON.parse(response.result.content[0].text);
 });
 assert.equal(result.status,'orchestration_handoff');assert.match(result.task_bundle.task,/"mode":"video"/);
 assert.equal(f.checks.length,1);assert.equal(f.launches(),1);
});

test('ordinary startup binds its revision in Host and the real current Main completes the original route checker',async t=>{
 const f=await fixture(t);
 const launched=await f.rpc({});
 assert.equal(launched.result.isError,undefined,JSON.stringify(launched));
 const result=JSON.parse(launched.result.content[0].text);
 assert.equal(result.status,'orchestration_handoff');assert.equal(result.context,'current_conversation');
 assert.equal(f.checks.length,0);
 const completed=await f.publicRpc('workflow_orchestration_complete',{output:{mode:'video'}});
 assert.equal(completed.result.isError,undefined,JSON.stringify(completed));
 const handoff=JSON.parse(completed.result.content[0].text);
 assert.equal(handoff.status,'orchestration_handoff');assert.match(handoff.task_bundle.task,/"mode":"video"/);
 const runs=await f.service.call('runs');assert.equal(runs.length,1);assert.equal(f.launches(),1);assert.equal(f.checks.length,1);
 const state=await f.service.call('get',{run_id:runs[0].run_id});
 assert.equal(state.nodes.choose.status,'succeeded');assert.equal(state.nodes.final.status,'running');
 const record=await (await f.service.open()).runtime.runs.read(runs[0].run_id);assert.equal(record.pins.root.revision_hash,f.pack.revision_hash);
 assert.equal(workflowToolDefinitions().some(t=>t.name==='workflow_start_prepared'),true);
});

test('changed file input fails before a Run after contract preparation',async t=>{
 const f=await fixture(t),path=join(f.workspace,'request.json');await writeFile(path,JSON.stringify(taskInputs));
 const {inputs,...fileArgs}=f.startArgs;
 const response=await f.publicRpc('workflow_startup_contract',{...fileArgs,inputs_path:'request.json'});
 assert.equal(response.result.isError,undefined,JSON.stringify(response));
 await writeFile(path,JSON.stringify({task:'Changed request.'}));
 const started=await f.publicRpc('workflow_start',{...fileArgs,inputs_path:'request.json',revision_hash:f.pack.revision_hash,
  startup_inputs_sha256:inputsHash,initial_output:{mode:'page'}});
 assert.equal(started.result.isError,true);assert.match(started.result.content[0].text,/WORKFLOW_STARTUP_INPUTS/);
 assert.equal((await f.service.call('runs')).length,0);assert.equal(f.checks.length,0);
});

test('ordinary startup without an initial result retains the first Main handoff',async t=>{
 const f=await fixture(t),response=await f.rpc({});assert.equal(response.result.isError,undefined,JSON.stringify(response));
 const handoff=JSON.parse(response.result.content[0].text);assert.equal(handoff.status,'orchestration_handoff');
 const [run]=await f.service.call('runs'),state=await f.service.call('get',{run_id:run.run_id});
 assert.equal(state.nodes.choose.status,'running');assert.equal(state.nodes.final.status,'pending');assert.equal(f.checks.length,0);
});

test('a rejected original checker does not release the successor',async t=>{
 const f=await fixture(t,{verified:false});
 const response=await f.rpc({revision_hash:f.pack.revision_hash,startup_inputs_sha256:inputsHash,initial_output:{mode:'page'}});
 assert.equal(f.checks.length,1);assert.equal(f.launches(),1);
 const [run]=await f.service.call('runs'),state=await f.service.call('get',{run_id:run.run_id});
 assert.notEqual(state.nodes.choose.status,'succeeded');assert.equal(state.nodes.final.status,'pending');
 assert(response.result.isError||JSON.parse(response.result.content[0].text).status!=='orchestration_handoff');
});

test('concurrent completion cannot apply the folded result to a schema-compatible successor',async t=>{
 const f=await fixture(t,{compatibleFinal:true});await f.rpc({});
 const {runtime}=await f.service.open(),authority=await readOwnedAuthorityForThread(runtime,threadId);
 const originalCall=f.service.call.bind(f.service),originalOpen=f.service.open.bind(f.service);let swapped=false,opens=0;
 // Folded completion uses private dispatch. Advance the real current node at
 // its second actual open, after the expected startup attempt was captured.
 f.service.open=async(...args)=>{
  if(++opens===2&&!swapped){
   swapped=true;await originalCall('orchestration_complete',{output:{mode:'page'}},{model:true,modelThreadId:threadId});
  }
  return originalOpen(...args);
 };
 await assert.rejects(f.service.modelStartedResult({...authority,status:'running',wake_reason:'native_handoff_required',next_action:'workflow_native_next'},
  {modelThreadId:threadId,initialSemantic:{node_id:'choose',revision_hash:f.pack.revision_hash,output:{mode:'video'}}}),{code:'WORKFLOW_STARTUP_IDENTITY'});
 const state=await originalCall('get',{run_id:authority.run_id});
 assert.equal(swapped,true);assert.deepEqual(state.nodes.choose.output,{mode:'page'});
 assert.equal(state.nodes.final.status,'running');assert.equal(state.nodes.final.attempts[0].completion_turns??0,0);
 assert.equal(f.checks.length,1);
});

test('abort during the original checker cancels the exact owned Run and prevents successor release',async t=>{
 let entered;const ready=new Promise(resolve=>{entered=resolve;});
 const f=await fixture(t,{execute:async request=>{
  entered();await new Promise(resolve=>{if(request.signal.aborted)resolve();else request.signal.addEventListener('abort',resolve,{once:true});});
  return {exit_code:1,output:{verified:false},effects:{observed:true,changed_paths:[],outside_paths:[],artifacts:[]}};
 }});
 const controller=new AbortController();
 const pending=f.publicRpc('workflow_start',{...f.startArgs,revision_hash:f.pack.revision_hash,startup_inputs_sha256:inputsHash,initial_output:{mode:'page'}},{signal:controller.signal});
 await ready;controller.abort(new Error('Originating startup cancelled during checker'));
 const result=await pending;assert.equal(result.result.isError,true,JSON.stringify(result));
 const [run]=await f.service.call('runs'),state=await f.service.call('get',{run_id:run.run_id});
 assert.equal(state.status,'cancelled');assert.equal(state.nodes.final.status,'cancelled');
 assert.equal(f.cancellations(),1);assert.equal(f.checks.length,1);
});

test('late abort at usage persistence cannot commit the first decision or release a successor',async t=>{
 const f=await fixture(t);await f.rpc({});
 const {runtime,executor}=await f.service.open(),authority=await readOwnedAuthorityForThread(runtime,threadId);
 const controller=new AbortController(),reason=new Error('Late startup abort');
 const originalUsage=runtime.recordHostMainUsage.bind(runtime);
 runtime.recordHostMainUsage=async(...args)=>{await originalUsage(...args);controller.abort(reason);};
 await assert.rejects(completeMainOrchestration(runtime,{...authority,thread_id:threadId,output:{mode:'page'}},
  {executor,signal:controller.signal}),error=>error===reason);
 const state=await f.service.call('get',{run_id:authority.run_id});
 assert.notEqual(state.nodes.choose.status,'succeeded');assert.equal(state.nodes.final.status,'pending');
 assert.equal(state.nodes.final.attempts.length,0);
});
