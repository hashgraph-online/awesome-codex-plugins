import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, rm } from 'node:fs/promises';
import { join } from 'node:path';
import { tmpdir } from './physical-tempdir.mjs';
import { buildProviderAdapter } from '../lib/providers.mjs';
import { WorkflowService } from '../lib/workflow-service.mjs';
import { loadConfig, saveConfig, configRevision } from '../lib/config.mjs';
import { DEFAULT_CONFIG_PATH } from '../server.mjs';

const provider = (agent_type, reasoning_effort, model='gpt-6-luna') => ({ id:'native-luna',kind:'native_agent',enabled:true,capabilities:{read:true,write:true},config:{agent_type,model,reasoning_effort,role:'advisor',fresh_context:true} });
test('native dispatch uses the generic Agent and preserves the configured model and effort',()=>{
  assert.deepEqual(buildProviderAdapter(provider('default','xhigh'),{access:'bounded_write'}).spawn_config,
    {agent_type:'default',fork_turns:'none',model:'gpt-6-luna',reasoning_effort:'xhigh'});
  assert.throws(()=>buildProviderAdapter(provider('duplicate-fixed-role','high','gpt-6-sol'),{access:'bounded_write'}),{code:'NATIVE_PROVIDER_AGENT_TYPE'});
});

test('registry model edits update dependent Workflows and deletion blocks new Runs while snapshots stay fixed',async t=>{
  const root=await mkdtemp(join(tmpdir(),'provider-binding-'));
  t.after(()=>rm(root,{recursive:true,maxRetries:3,retryDelay:100}));
  const workspace=join(root,'workspace');await mkdir(workspace);
  const configPath=join(root,'control-plane.json');
  await loadConfig({configPath,defaultConfigPath:DEFAULT_CONFIG_PATH});
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
