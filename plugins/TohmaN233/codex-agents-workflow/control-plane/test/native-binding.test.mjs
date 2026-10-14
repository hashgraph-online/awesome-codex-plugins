import { loadLegacyConfig } from './legacy-config.mjs';
import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, rm } from 'node:fs/promises';
import { join } from 'node:path';
import { tmpdir } from './physical-tempdir.mjs';
import { buildProviderAdapter } from '../lib/providers.mjs';
import { WorkflowService } from '../lib/workflow-service.mjs';
import { WorkflowExecutor } from '../lib/workflow-executor.mjs';
import { saveConfig, configRevision, migrateBuiltinNativeAgentRoles } from '../lib/config.mjs';
import { nativeBindingIssue, nativeSpawnConfig } from '../lib/native-binding.mjs';
import { NATIVE_BUILTINS_PROFILE_NAME } from '../../scripts/native-context-profile.mjs';
import { DEFAULT_CONFIG_PATH } from '../server.mjs';

const provider = (agent_type, reasoning_effort, model='gpt-6-luna') => ({ id:'native-luna',kind:'native_agent',enabled:true,capabilities:{read:true,write:true},config:{agent_type,model,reasoning_effort,role:'advisor',fresh_context:true} });
test('native dispatch uses the generic Agent and preserves the configured model and effort',()=>{
  assert.deepEqual(buildProviderAdapter(provider('default','xhigh'),{access:'bounded_write'}).spawn_config,
    {agent_type:'default',fork_turns:'none',model:'gpt-6-luna',reasoning_effort:'xhigh'});
  assert.throws(()=>buildProviderAdapter(provider('duplicate-fixed-role','high','gpt-6-sol'),{access:'bounded_write'}),{code:'NATIVE_PROVIDER_AGENT_TYPE'});
});

test('the installed tool context profile preserves explicit model/effort and does not become a behavioral Role',()=>{
  const verifyProfile=name=>assert.equal(name,NATIVE_BUILTINS_PROFILE_NAME);
  for(const [model,effort]of [['gpt-6.1-sol','high'],['gpt-6-astra','xhigh']]){
    const selected=provider(NATIVE_BUILTINS_PROFILE_NAME,effort,model);
    assert.deepEqual(nativeSpawnConfig(selected,{verifyProfile}),
      {agent_type:NATIVE_BUILTINS_PROFILE_NAME,fork_turns:'none',model,reasoning_effort:effort});
  }
  const unavailable=Object.assign(new Error('Owned profile bytes changed'),{code:'NATIVE_CONTEXT_PROFILE_CHANGED'});
  assert.throws(()=>nativeSpawnConfig(provider(NATIVE_BUILTINS_PROFILE_NAME,'high'),
    {verifyProfile:()=>{throw unavailable;}}),{code:unavailable.code,message:unavailable.message});
  let reads=0;
  assert.equal(nativeBindingIssue(provider('default','high'),{verifyProfile:()=>{reads++;}}),null);
  assert.equal(nativeBindingIssue(provider('arbitrary-custom-role','high'),{verifyProfile:()=>{reads++;}}).code,'NATIVE_PROVIDER_AGENT_TYPE');
  assert.equal(reads,0,'Default and unsupported behavior roles must not probe a profile');
});

test('a narrowed tool context cannot silently inherit the parent transcript',()=>{
  const selected=provider(NATIVE_BUILTINS_PROFILE_NAME,'high');selected.config.fresh_context=false;
  assert.throws(()=>nativeSpawnConfig(selected,{verifyProfile:()=>assert.fail('History rejects before any profile read')}),
    {code:'NATIVE_CONTEXT_PROFILE_HISTORY'});
});

test('native migration preserves an explicit tool context profile and still retires duplicated behavior roles',()=>{
  const profiles=[provider(NATIVE_BUILTINS_PROFILE_NAME,'high','gpt-6.1-sol'),provider('arbitrary-custom-role','xhigh')];
  profiles[0].id='custom-builtin-context';profiles[1].id='custom-behavior';
  const {config:migrated}=migrateBuiltinNativeAgentRoles({providers:profiles});
  assert.equal(migrated.providers.find(p=>p.id===profiles[0].id).config.agent_type,NATIVE_BUILTINS_PROFILE_NAME);
  assert.equal(migrated.providers.find(p=>p.id===profiles[0].id).config.model,'gpt-6.1-sol');
  assert.equal(migrated.providers.find(p=>p.id===profiles[1].id).config.agent_type,'default');
  assert.equal(profiles[1].config.agent_type,'arbitrary-custom-role','Migration cannot mutate source config');
});

test('unsupported native context routes fail before any Strict, managed or task dispatch',async()=>{
  const selected=provider(NATIVE_BUILTINS_PROFILE_NAME,'high','gpt-6.1-sol');
  for(const route of [
    {executor:{kind:'provider',provider_id:selected.id},skill_policy:{mode:'strict'},args:{}},
    {executor:{kind:'provider',provider_id:selected.id},skill_policy:{mode:'cooperative'},args:{host_managed_native:true}},
    {executor:{kind:'thread',provider_id:selected.id},skill_policy:{mode:'cooperative'},args:{}}
  ]){
    const envelope={...route,provider:selected},runtime={authorizedExecution:async()=>({record:{},envelope})};
    const unavailable={prepare:async()=>assert.fail('Unsupported profile must reject before starting another executor')};
    const executor=new WorkflowExecutor({runtime,getConfig:async()=>({global:{enabled:true},providers:[selected]}),strictManager:unavailable,managedNativeManager:unavailable,env:{}});
    await assert.rejects(executor.prepare('fixture',route.args),{code:'NATIVE_CONTEXT_PROFILE_EXECUTION_UNSUPPORTED'});
  }
});

test('registry model edits update dependent Workflows and deletion blocks new Runs while snapshots stay fixed',async t=>{
  const root=await mkdtemp(join(tmpdir(),'provider-binding-'));
  t.after(()=>rm(root,{recursive:true,maxRetries:3,retryDelay:100}));
  const workspace=join(root,'workspace');await mkdir(workspace);
  const configPath=join(root,'control-plane.json');
  await loadLegacyConfig({configPath,defaultConfigPath:DEFAULT_CONFIG_PATH});
  const service=new WorkflowService({configPath,defaultConfigPath:DEFAULT_CONFIG_PATH,env:{}});
  await service.call('migrate_v6',{}, {human:true});
  const edit=async change=>{const config=await service.config();const revision=configRevision(config);change(config);await saveConfig(config,{configPath,expectedRevision:revision});};
  await edit(config=>{const source=config.providers.find(p=>p.id==='native-luna');config.providers.push({...structuredClone(source),id:'custom-complex',config:{...structuredClone(source.config),agent_type:'default'}});});
  const source=await service.call('read',{workflow_id:'judgment-heavy-change'});
  const firstWorkflow=structuredClone(source.workflow);firstWorkflow.id='custom-complex-workflow';firstWorkflow.name='Custom complex workflow';
  firstWorkflow.requirements.providers=['custom-complex'];firstWorkflow.nodes.find(node=>node.executor?.provider_id).executor.provider_id='custom-complex';
  await service.call('create',{workflow:firstWorkflow},{human:true});
  const copy=structuredClone(firstWorkflow);copy.id='second-complex-workflow';copy.name='Second complex workflow';
  await service.call('create',{workflow:copy},{human:true});
  const id=firstWorkflow.id;
  const start=()=>service.call('start',{workflow_id:id,workspace,access:'bounded_write',allowed_paths:['.'],main_actor:'test',inputs:{task:'fixture',context:'fixture'}});
  const first=await start();
  const pinned=(await (await service.open()).runtime.runs.read(first.run_id)).pins.providers.find(p=>p.id==='custom-complex').config;
  await edit(config=>{config.providers.find(p=>p.id==='custom-complex').config.reasoning_effort='xhigh';});
  const second=await start();
  const updated=(await (await service.open()).runtime.runs.read(second.run_id)).pins.providers.find(p=>p.id==='custom-complex').config;
  assert.equal(updated.reasoning_effort,'xhigh');
  assert.deepEqual((await (await service.open()).runtime.runs.read(first.run_id)).pins.providers.find(p=>p.id==='custom-complex').config,pinned);
  await edit(config=>{config.providers=config.providers.filter(p=>p.id!=='custom-complex');});
  for(const workflow_id of [id,copy.id])assert((await service.call('read',{workflow_id})).validation.errors.some(e=>e.code==='PROVIDER_MISSING'));
  await assert.rejects(start(),{code:'WORKFLOW_LAUNCH_BLOCKED'});
});
