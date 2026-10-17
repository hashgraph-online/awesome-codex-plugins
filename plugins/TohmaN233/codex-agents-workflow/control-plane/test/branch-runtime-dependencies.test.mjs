import test from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdtemp, mkdir, rm, copyFile, chmod, stat, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { tmpdir } from './physical-tempdir.mjs';
import { WorkflowStore } from '../lib/workflow-store.mjs';
import { WorkflowRuntime } from '../lib/workflow-runtime.mjs';
import { createDraft, validateWorkflowShape } from '../lib/workflow-schema.mjs';
import { runtimeEnvironmentForWorker, augmentedRuntimeEnvironment } from '../lib/runtime-environment-state.mjs';
import { compileRequirementCoverage,compileExpansion } from '../lib/skill-import/semantic-expander.mjs';
import { importCoarseSkill } from '../lib/skill-import/coarse-compiler.mjs';
import { compileDeployableConversion } from '../lib/skill-import/conversion-deployment.mjs';
import { EXPANSION_PROPOSAL_SCHEMA } from '../lib/skill-import/expansion-run.mjs';
import { validateData } from '../lib/workflow-data-schema.mjs';
import { discoverRuntimeEnvironment, verifyRuntimeEnvironment, updateRuntimeCandidate } from '../lib/runtime-environment.mjs';
import { WorkflowExecutor } from '../lib/workflow-executor.mjs';
import { HostToolRunner } from '../lib/execution/host-tool-runner.mjs';
import { workflowResourceProgramIdentity,workflowResourceProgramRegistry } from '../lib/execution/workflow-resource-program.mjs';
import { digest } from '../lib/workflow-revisions.mjs';
import { WorkflowDrive } from '../lib/workflow-drive.mjs';

const contract = { executables: [{ name: 'node', version: '>=22' }, 'fixture-ffmpeg', 'fixture-chrome'], source_requirement_ids: ['mp4_runtime'] };
async function pathFixture(t){
  const root=await mkdtemp(join(tmpdir(),'runtime-path-order-'));t.after(()=>rm(root,{recursive:true,maxRetries:3,retryDelay:100}));
  const paths={};
  for(const directory of ['helpers','qualified','cycle','cwd'])await mkdir(join(root,directory));
  for(const item of ['helpers/helper','helpers/alpha','helpers/beta','qualified/alpha','qualified/beta','cycle/alpha','cycle/beta','cwd/alpha','helpers/google-chrome']){
    const path=join(root,item+(process.platform==='win32'?'.exe':''));await copyFile(process.execPath,path);if(process.platform!=='win32')await chmod(path,0o755);paths[item]=path;
  }
  const tool=(name,item)=>({name,status:'found',path:paths[item]});return {root,paths,tool};
}
for(const reversed of [false,true])test(`native PATH consumes all qualified logical paths with ${reversed?'reversed':'original'} binding order`,async t=>{
  const f=await pathFixture(t),tools=[f.tool('helper','helpers/helper'),f.tool('alpha','qualified/alpha')];if(reversed)tools.reverse();
  const env=augmentedRuntimeEnvironment(process.env,{tools},{workspace:f.root});
  for(const name of ['helper','alpha']){const child=spawnSync(name,['-p','process.execPath'],{cwd:f.root,env,encoding:'utf8'});assert.equal(child.status,0,child.stderr);assert.equal(child.stdout.trim(),tools.find(tool=>tool.name===name).path);}
});
test('native PATH rejects mutually incompatible qualified directories',async t=>{
  const f=await pathFixture(t);assert.throws(()=>augmentedRuntimeEnvironment({}, {tools:[f.tool('alpha','qualified/alpha'),f.tool('beta','cycle/beta')]},{workspace:f.root}),{code:'ENVIRONMENT_BINDING_STALE'});
});
test('Windows current directory shadow fails before native dispatch',{skip:process.platform!=='win32'},async t=>{
  const f=await pathFixture(t);assert.throws(()=>augmentedRuntimeEnvironment({}, {tools:[f.tool('alpha','qualified/alpha')]},{workspace:join(f.root,'cwd')}),error=>error.code==='ENVIRONMENT_BINDING_STALE'&&error.observed_path===f.paths['cwd/alpha']);
});
test('physical executable aliases retain their exact absolute binding',async t=>{
  const f=await pathFixture(t),env=augmentedRuntimeEnvironment({}, {tools:[f.tool('chrome','helpers/google-chrome')]},{workspace:f.root});
  const child=spawnSync(f.paths['helpers/google-chrome'],['-p','process.execPath'],{env,cwd:f.root,encoding:'utf8'});assert.equal(child.status,0,child.stderr);assert.equal(child.stdout.trim(),f.paths['helpers/google-chrome']);
});
test('Windows trailing-dot native names reject a double-dot pin instead of misclassifying it as an alias',{skip:process.platform!=='win32'},async t=>{
  const f=await pathFixture(t),expected=join(f.root,'qualified','alpha..exe');await copyFile(process.execPath,expected);
  const tools=[{name:'alpha.',status:'found',path:expected}];
  assert.throws(()=>augmentedRuntimeEnvironment(process.env,{tools},{workspace:f.root}),error=>error.code==='ENVIRONMENT_BINDING_STALE'&&error.expected_path===expected&&error.observed_path===f.paths['qualified/alpha']);
});
test('Windows trailing-dot logical bindings still enforce the actual current-directory candidate',{skip:process.platform!=='win32'},async t=>{
  const f=await pathFixture(t),tools=[{name:'alpha.',status:'found',path:f.paths['qualified/alpha']}];
  assert.throws(()=>augmentedRuntimeEnvironment(process.env,{tools},{workspace:join(f.root,'cwd')}),error=>error.code==='ENVIRONMENT_BINDING_STALE'&&error.observed_path===f.paths['cwd/alpha']);
});
test('Windows native names with trailing dot and nonempty extensions consume exact physical candidates',{skip:process.platform!=='win32'},async t=>{
  const f=await pathFixture(t);
  for(const name of ['alpha.','alpha..','alpha.ext','alpha.exe']){
    const filename=name==='alpha.'?'alpha.exe':name==='alpha..'?'alpha..exe':name;
    const path=join(f.root,'qualified',filename);if(filename!=='alpha.exe')await copyFile(process.execPath,path);
    const env=augmentedRuntimeEnvironment(process.env,{tools:[{name,status:'found',path}]},{workspace:f.root});
    const child=spawnSync(name,['-p','process.execPath'],{env,cwd:f.root,encoding:'utf8'});assert.equal(child.status,0,child.stderr);assert.equal(child.stdout.trim(),path);
  }
});
async function fixture(t, format = 'mp4') {
  const root = await mkdtemp(join(tmpdir(), 'branch-runtime-')); t.after(() => rm(root,{recursive:true,maxRetries:3,retryDelay:100}));
  const workspace=join(root,'workspace'); await mkdir(workspace);
  const wf={...createDraft('branch-runtime','Branch runtime'), status:'ready',
    skill_policy:{mode:'cooperative',implicit:'allow',ambient_allow:[],shadowed_skill_paths:[]},
    requirements:{providers:[],tools:[],mcp_servers:[],executables:[{name:'node',version:'>=20'}]},
    inputs_schema:{type:'object',properties:{format:{type:'string'}},required:['format']},finalization:{required:true,node_id:'final'},
    nodes:[{id:'start',type:'start'},{id:'route',type:'condition',cases:[{label:'mp4',when:{op:'eq',args:[{path:'/inputs/format'},{value:'mp4'}]}}],default_label:'html'},
      ...['html','mp4','final'].map(id=>({id,type:'agent',executor:{kind:'main'},access:'read_only',approval:{required:false},retry:{max_attempts:1},prompt_template:'Semantic fixture',input_bindings:{},...(id==='mp4'?{runtime_requirements:contract}:{})})),{id:'end',type:'end'}],
    edges:[['start','route'],['route','html','html'],['route','mp4','mp4'],['html','final'],['mp4','final'],['final','end']].map(([source,target,label])=>({id:`${source}-${target}`,source,target,...(label?{label}:{})}))};
  const store=await new WorkflowStore(join(root,'packs')).initialize(); const pack=await store.create(wf);
  const base={status:'ready',tools:[{name:'node',status:'ready',path:join(root,'node20')}],missing:[]};
  let ready=false, calls=[];
  const runtime=await new WorkflowRuntime({workflowStore:store,runRoot:join(root,'runs'),context:{},
    environmentVerifier:async (requirements,environment)=>{if(requirements.executables.some(x=>x.name==='fixture-ffmpeg')&&environment?.tools?.length!==3)throw Object.assign(new Error('scope missing'),{code:'ENVIRONMENT_BINDING_STALE'});},
    environmentResolver:async requirements=>{calls.push(structuredClone(requirements)); if(requirements.executables.some(x=>x.name==='fixture-ffmpeg'))return ready?{status:'ready',tools:requirements.executables.map(x=>({name:x.name,status:'ready',path:join(root,x.name==='node'?'node22':x.name)})),missing:[],installation_performed:false}:{status:'installation_approval_required',tools:[],missing:['fixture-ffmpeg','fixture-chrome'],installation_performed:false};return base;}}).initialize();
  const run=await runtime.start({workflow_id:wf.id,revision_hash:pack.revision_hash,workspace,access:'read_only',main_actor:'main',inputs:{format},require_approval:false});
  const claim=id=>runtime.claimHostMain(run.run_id,{node_id:id,owner:'main',request_id:`claim-${id}`,control_token:run.control_token});
  return {runtime,run,claim,root,calls,setReady:()=>{ready=true;}};
}

test('HTML enters without conditional executable discovery',async t=>{
  const f=await fixture(t,'html'); const lease=await f.claim('html'); assert.equal(lease.node_id,'html');
  assert.equal(f.calls.some(x=>x.executables.some(y=>y.name==='fixture-ffmpeg')),false);
});
test('selected MP4 pauses before model claim and exposes scoped attention without installation',async t=>{
  const f=await fixture(t); await assert.rejects(f.claim('mp4'),{code:'ENVIRONMENT_SETUP_REQUIRED'});
  const state=await f.runtime.get(f.run.run_id); assert.equal(state.nodes.mp4.attempts.length,0); assert.equal(state.environment_attention.node_id,'mp4'); assert.equal(state.environment_attention.installation_performed,false);
});
test('deterministic drive prepares only the selected branch before any executor handoff',async t=>{
  for(const format of ['html','mp4']){
    const f=await fixture(t,format),drive=new WorkflowDrive({runtime:f.runtime,executor:{executeHostTool:()=>assert.fail('No tool dispatch is expected')}});
    const progress=await drive.advance(f.run.run_id,{control_token:f.run.control_token});
    assert.equal(progress.stop_reason,format==='html'?'semantic_node':'environment_attention');
    if(format==='mp4')assert.equal(progress.environment.node_id,'mp4');else assert.equal(progress.node_id,'html');
    assert.equal((await f.runtime.get(f.run.run_id)).nodes[format].attempts.length,0);
  }
});
test('node rebind survives global recheck and projects exact scoped worker paths',async t=>{
  const f=await fixture(t); f.setReady(); const lease=await f.claim('mp4');
  assert.equal(lease.constraints.runtime_environment.tools.find(x=>x.name==='node').path,join(f.root,'node22'));
  await f.runtime.ensureRuntimeEnvironment(f.run.run_id,{control_token:f.run.control_token});
  const reopened=await new WorkflowRuntime({workflowStore:f.runtime.workflows,runRoot:f.runtime.runs.root}).initialize();
  const record=await f.runtime.runs.read(f.run.run_id);
  assert.equal(runtimeEnvironmentForWorker(record.state,record.pins.root.workflow.nodes.find(x=>x.id==='mp4'),record.pins).tools.find(x=>x.name==='node').path,join(f.root,'node22'));
  assert.equal((await reopened.runs.read(f.run.run_id)).state.nodes.mp4.runtime_environment_binding.scope_sha256,record.state.nodes.mp4.runtime_environment_binding.scope_sha256);
});
test('node typed declaration rejects unknown probes and conflicting versions',()=>{
  const wf=createDraft('shape','Shape');wf.nodes=[{id:'mp4',type:'agent',runtime_requirements:{...contract,probe:'special-script'}}];
  assert.throws(()=>validateWorkflowShape(wf),{code:'NODE_RUNTIME_REQUIREMENTS'});
  wf.nodes[0].runtime_requirements=contract;wf.requirements.executables=[{name:'node',version:'<22'}];
  assert.throws(()=>validateWorkflowShape(wf),{code:'ENVIRONMENT_REQUIREMENT_CONFLICT'});
});

function coverageFixture(target='mp4',activation={condition_node_id:'route',branch_label:'导出 MP4'}){
  const resource='source/SKILL.md',resources={[resource]:Buffer.from('When exporting MP4, fixture-renderer >=22 is required.\n')};
  const nodes=[{id:'route',type:'condition',cases:[{label:'导出 MP4'}],default_label:'default'},
    ...['mp4','html','shared'].map(id=>({id,type:'agent',operation_mode:'read',input_bindings:{},resource_refs:[resource],requirement_ids:id===target?['render_dependency']:[]}))];
  const edges=[['start','route'],['route','mp4','导出 MP4'],['route','html','default'],['mp4','shared'],['html','shared']].map(([source,target,label])=>({source,target,...(label?{label}:{})}));
  const requirement={requirement_id:'render_dependency',requirement_kind:'dependency',source_spans:[{resource,start_line:1,end_line:1}],trigger:'Exporting MP4',required_result:'Prepare the MP4 renderer.',resource_refs:[resource],details:{executable:'fixture-renderer',version:'>=22',phase:'conditional'}};
  const mapping={requirement_id:requirement.requirement_id,node_ids:[target],binding_names:[],runtime_guards:['Exporting MP4'],resource_refs:[resource],status:'compiled',rationale:'Source-defined MP4 consumer',...(activation?{runtime_activation:activation}:{})};
  return {proposal:{source_requirements:[requirement],requirement_mappings:[mapping]},resources,nodes,edges};
}
test('conditional compilation requires typed activation and proves the original Unicode branch edge',()=>{
  const f=coverageFixture();const result=compileRequirementCoverage(f.proposal,f.resources,f.nodes,f.edges);
  assert.equal(result.coverage[0].status,'compiled');assert.equal(result.coverage[0].runtime_activation.branch_label,'导出 MP4');
  assert.deepEqual(result.node_runtime_requirements,[{node_id:'mp4',runtime_requirements:{executables:[{name:'fixture-renderer',version:'>=22.0.0'}],source_requirement_ids:['render_dependency']}}]);
});
test('shared consumer, bypass and prose-only conditions stay visibly uncompiled',()=>{
  for(const mode of ['shared','bypass','failure-bypass','prose']){
    const f=coverageFixture(mode==='shared'?'shared':'mp4',mode==='prose'?null:undefined);
    if(mode==='bypass')f.edges.push({source:'start',target:'mp4'});
    if(mode==='failure-bypass')f.edges.push({source:'start',target:'mp4',on:'failure'});
    const result=compileRequirementCoverage(f.proposal,f.resources,f.nodes,f.edges);
    assert.equal(result.coverage[0].status,'agent_assisted',mode);assert.match(result.coverage[0].reason,/conditional runtime preparation unbound/i);assert.deepEqual(result.node_runtime_requirements,[]);
  }
});

test('invalid typed activation and source version mismatch never become executable authority',()=>{
  const malformed=coverageFixture('mp4',{condition_node_id:'route',branch_label:'导出 MP4',probe:'guess'});
  assert.throws(()=>compileRequirementCoverage(malformed.proposal,malformed.resources,malformed.nodes,malformed.edges),{code:'EXPANSION_RUNTIME_ACTIVATION'});
  const mismatch=coverageFixture();mismatch.proposal.source_requirements[0].details.version='>=23';
  assert.equal(compileRequirementCoverage(mismatch.proposal,mismatch.resources,mismatch.nodes,mismatch.edges).coverage[0].status,'agent_assisted');
});

test('canonical conditional mapping compiles and exports its exact node declaration and source phase',async t=>{
  const root=await mkdtemp(join(tmpdir(),'conditional-compile-'));t.after(()=>rm(root,{recursive:true,maxRetries:3,retryDelay:100}));
  const source=join(root,'SKILL.md');await writeFile(source,'---\nname: Conditional export\ndescription: Export the chosen format.\n---\n\nWhen exporting MP4, fixture-renderer >=22 is required.\n');
  const store=await new WorkflowStore(join(root,'source-packs')).initialize(),provider={id:'fixture-provider',enabled:true,capabilities:{read:true,write:true}};
  const pack=await importCoarseSkill(store,source,{id:'conditional-source',providerId:provider.id}),resources=await store.resources(pack.workflow.id);
  const f=coverageFixture(),origin={confidence:1,source_span:{resource:'source/SKILL.md',start_line:6,end_line:6}};
  f.proposal.source_requirements[0].source_spans=[origin.source_span];
  const identity={name:'fixture-check',version:'1',sha256:'a'.repeat(64)},tool={id:'fixture-check',identity,argv:['fixture-check'],input_schema:{type:'object',additionalProperties:false},output_schema:{type:'object',required:['checked'],properties:{checked:{type:'boolean'}},additionalProperties:false},env_allow:[],permissions:{network:false,read_paths:[],write_paths:[]},output_cap_bytes:1024,deadline_ms:1000,idempotency:{mode:'safe'}};
  const proposal={...f.proposal,source_revision:pack.revision_hash,source_dispositions:[{section_id:'section_01_overview',disposition:'workflow',node_ids:['mp4','html'],requirement_ids:['render_dependency'],rationale:'Retain the source-defined conditional export requirement.'}],required_executables:[],
    nodes:[{id:'route',type:'condition',cases:[{label:'导出 MP4',when:{op:'eq',args:[{path:'/inputs/task'},{value:'mp4'}]}}],default_label:'default',...origin},
      ...['mp4','html'].map(id=>({id,type:'tool',tool:tool.id,input_bindings:{},resource_refs:['source/SKILL.md'],requirement_ids:id==='mp4'?['render_dependency']:[],...origin}))],
    edges:[['start','route'],['route','mp4','导出 MP4'],['route','html','default'],['mp4','final'],['html','final']].map(([source,target,label])=>({id:`${source}-${target}`,source,target,...(label?{label}:{}),...origin}))};
  validateData(proposal.requirement_mappings[0],EXPANSION_PROPOSAL_SCHEMA.properties.requirement_mappings.items);
  const compiled=compileExpansion(pack,resources,proposal,{providers:[provider],host_tools:[tool.id],host_tool_contracts:[tool]});
  assert.equal(compiled.validation.valid,true,JSON.stringify(compiled.validation));
  assert.deepEqual(compiled.workflow.nodes.find(node=>node.id==='mp4').runtime_requirements,{executables:[{name:'fixture-renderer',version:'>=22.0.0'}],source_requirement_ids:['render_dependency']});
  assert.equal(compiled.workflow.nodes.find(node=>node.id==='html').runtime_requirements,undefined);
  assert.deepEqual(compiled.workflow.requirements.executables,[]);
  const deployed=compileDeployableConversion({workflow:compiled.workflow,proposal:compiled.canonical_proposal,resources,pack,proposalHash:compiled.proposal_hash,reviewContractVersion:4});
  assert.deepEqual(deployed.workflow.nodes.find(node=>node.id==='mp4').runtime_requirements,compiled.workflow.nodes.find(node=>node.id==='mp4').runtime_requirements);
  assert.equal(deployed.workflow.import_status.requirement_coverage.find(item=>item.requirement_id==='render_dependency').details.phase,'conditional');
  assert.equal(deployed.workflow.import_status.requirement_coverage.find(item=>item.requirement_id==='render_dependency').runtime_activation.branch_label,'导出 MP4');
});

test('scoped discovery cannot commit after controller or Run sequence changes',async t=>{
  const f=await fixture(t);let entered,release;const started=new Promise(resolve=>{entered=resolve;});const wait=new Promise(resolve=>{release=resolve;});
  const resolver=f.runtime.environmentResolver;
  f.runtime.environmentResolver=async (...args)=>{entered();await wait;return resolver(...args);};
  const pending=f.claim('mp4');await started;
  await f.runtime.transition(f.run.run_id,'control_recovery',state=>{state.control_hash=digest('replacement-controller');});
  release();await assert.rejects(pending,{code:'RUN_SEQUENCE_CONFLICT'});
  const state=await f.runtime.get(f.run.run_id);assert.equal(state.environment_attention,undefined);assert.equal(state.nodes.mp4.attempts.length,0);
});

test('unselected consumer and wrong controller do not probe or acquire a scope',async t=>{
  const f=await fixture(t,'html');const before=f.calls.length;
  await assert.rejects(f.claim('mp4'),{code:'NODE_NOT_READY'});
  await assert.rejects(f.runtime.ensureRuntimeEnvironment(f.run.run_id,{node_id:'html',control_token:'wrong'}),{code:'RUN_AUTHORITY'});
  assert.equal(f.calls.length,before);
});

test('wrong Main owner and stale lease cannot prepare dependencies or dispatch',async t=>{
  const f=await fixture(t);const before=f.calls.length;
  await assert.rejects(f.runtime.claimHostMain(f.run.run_id,{node_id:'mp4',owner:'other-main',request_id:'wrong-owner',control_token:f.run.control_token}),{code:'FINALIZER_AUTHORITY'});
  assert.equal(f.calls.length,before);f.setReady();const lease=await f.claim('mp4');
  await assert.rejects(f.runtime.execution(f.run.run_id,{...lease,control_token:f.run.control_token,lease_token:'wrong'}),{code:'LEASE_INVALID'});
  await f.runtime.transition(f.run.run_id,'runtime_environment_rebound',state=>{state.nodes.mp4.runtime_environment_binding.environment.tools.find(x=>x.name==='node').path=join(f.root,'different-node22');});
  await assert.rejects(f.runtime.execution(f.run.run_id,{...lease,control_token:f.run.control_token}),{code:'ENVIRONMENT_BINDING_STALE'});
  assert.equal((await f.runtime.get(f.run.run_id)).nodes.mp4.attempts[0].dispatch,null);
});

test('real registry probes rebind selected tool and its actual child uses scoped helper paths',async t=>{
  const root=await mkdtemp(join(tmpdir(),'branch-real-registry-'));t.after(()=>rm(root,{recursive:true,maxRetries:3,retryDelay:100}));
  const workspace=join(root,'workspace'),bin=join(root,'registered-only'),home=join(root,'home');await Promise.all([mkdir(workspace),mkdir(bin),mkdir(home)]);await mkdir(join(workspace,'work'));
  const env={USERPROFILE:home,HOME:home,PATH:'',...(process.platform==='win32'?{SystemRoot:process.env.SystemRoot}:{})},registryPath=join(root,'registry.json');
  const baseRequirement={name:'node',version:'>=1'},nodeRequirement={name:'node',version:`>=${process.versions.node.split('.')[0]}`};
  await updateRuntimeCandidate(baseRequirement,process.execPath,{registryPath,env});
  const wf={...createDraft('actual-branch','Actual branch'),status:'ready',
    skill_policy:{mode:'cooperative',implicit:'allow',ambient_allow:[],shadowed_skill_paths:[]},
    requirements:{providers:[],tools:['actual-export'],mcp_servers:[],executables:[baseRequirement]},inputs_schema:{},finalization:{required:true,node_id:'final'},
    nodes:[{id:'start',type:'start'},{id:'mp4',type:'tool',executor:{kind:'tool',tool:'actual-export'},access:'bounded_write',path_scope:['work'],input_bindings:{},approval:{required:false},retry:{max_attempts:1},
      runtime_requirements:{executables:[nodeRequirement,'fixture-ffmpeg','fixture-chrome'],source_requirement_ids:['source_mp4_runtime']}},
      {id:'final',type:'agent',executor:{kind:'main'},access:'read_only',prompt_template:'Semantic acceptance',input_bindings:{},approval:{required:false},retry:{max_attempts:1}},{id:'end',type:'end'}],
    edges:[['start','mp4'],['mp4','final'],['final','end']].map(([source,target])=>({id:`${source}-${target}`,source,target}))};
  const path='source/export.mjs',bytes=Buffer.from('import {spawnSync} from "node:child_process";const paths=["fixture-ffmpeg","fixture-chrome"].map(name=>{const result=spawnSync(name,["-p","process.execPath"],{encoding:"utf8"});if(result.status!==0)throw new Error(result.error?.message??result.stderr);return result.stdout.trim();});console.log(JSON.stringify({paths,value:process.env.WORKFLOW_FIXTURE_ENV}));');
  const contract={id:'actual-export',identity:workflowResourceProgramIdentity(),argv:['node',path,'work/.runtime'],
    input_schema:{type:'object',additionalProperties:false},output_schema:{type:'object',required:['paths','value'],properties:{paths:{type:'array',items:{type:'string'}},value:{type:'string'}}},
    env_allow:['WORKFLOW_FIXTURE_ENV'],permissions:{network:false,read_paths:[path],write_paths:['work']},output_cap_bytes:8192,deadline_ms:30000,idempotency:{mode:'safe'}};
  wf.host_tools=[contract];wf.nodes[1].resources=[path];wf.nodes[1].outputs_schema=contract.output_schema;
  const context={host_tools:[contract.id]},store=await new WorkflowStore(join(root,'packs'),{validationContext:context}).initialize();const pack=await store.create(wf,{resources:{[path]:bytes}});
  const runtime=await new WorkflowRuntime({workflowStore:store,runRoot:join(root,'runs'),context,
    environmentResolver:(requirements,options)=>discoverRuntimeEnvironment(requirements,{...options,env,registryPath}),environmentVerifier:(requirements,environment)=>verifyRuntimeEnvironment(requirements,environment,{env,registryPath})}).initialize();
  const run=await runtime.start({workflow_id:wf.id,revision_hash:pack.revision_hash,workspace,access:'bounded_write',allowed_paths:['work'],main_actor:'main',require_approval:false});
  const args={node_id:'mp4',owner:'main',request_id:'actual-once',control_token:run.control_token};
  await assert.rejects(runtime.claimNode(run.run_id,args),{code:'ENVIRONMENT_SETUP_REQUIRED'});
  assert.equal((await runtime.get(run.run_id)).nodes.mp4.attempts.length,0);
  await assert.rejects(stat(join(workspace,'work/.runtime')),{code:'ENOENT'});
  const paths={};for(const name of ['node','fixture-ffmpeg','fixture-chrome']){const candidate=join(bin,name+(process.platform==='win32'?'.exe':''));await copyFile(process.execPath,candidate);if(process.platform!=='win32')await chmod(candidate,0o755);paths[name]=candidate;
    await updateRuntimeCandidate(name==='node'?nodeRequirement:name,candidate,{registryPath,env});}
  const prepared=await runtime.ensureRuntimeEnvironment(run.run_id,{control_token:run.control_token,node_id:'mp4'});
  assert.equal(prepared.environment.installation_performed,false);assert.equal(prepared.environment.tools.find(x=>x.name==='node').path,paths.node);
  await runtime.ensureRuntimeEnvironment(run.run_id,{control_token:run.control_token});
  const lease=await runtime.claimNode(run.run_id,args);
  assert.equal(lease.constraints.runtime_environment.tools.find(x=>x.name==='node').path,paths.node);
  const runner=new HostToolRunner({registry:workflowResourceProgramRegistry(),env:{WORKFLOW_FIXTURE_ENV:'from-host'}}),executor=new WorkflowExecutor({runtime,registry:{},hostToolRunner:runner,env:{},getConfig:async()=>({global:{enabled:true},providers:[]})});
  await executor.executeHostTool(run.run_id,{...lease,control_token:run.control_token});
  const record=await runtime.runs.read(run.run_id);assert.equal(record.state.nodes.mp4.status,'succeeded');
  assert.deepEqual(record.state.nodes.mp4.output,{paths:[paths['fixture-ffmpeg'],paths['fixture-chrome']],value:'from-host'});
  assert.equal(record.state.nodes.mp4.attempts.length,1);assert.equal(record.state.nodes.mp4.runtime_environment_binding.scope_sha256,prepared.scope_sha256);
  assert.equal(record.state.constraints.runtime_requirements.executables[0].version,'>=1.0.0');
});
