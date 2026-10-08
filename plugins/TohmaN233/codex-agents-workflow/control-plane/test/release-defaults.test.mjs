import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, readFile, rm } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { join, resolve } from 'node:path';
import { tmpdir } from './physical-tempdir.mjs';
import { WorkflowService } from '../lib/workflow-service.mjs';
import { loadConfig, saveConfig } from '../lib/config.mjs';
import { DEFAULT_CONFIG_PATH } from '../server.mjs';

const EXAMPLES=fileURLToPath(new URL('../../examples/workflows/',import.meta.url));
const PACKAGES=[
  'mathematical-research-hybrid.workflow-package.json',
  'video-use.workflow-package.json',
  'zenonzard-card-implementation.workflow-package.json',
];

async function installExamplePackage(service,filename){
  try{return await service.call('install_workflow_package',{package_path:join(EXAMPLES,filename)});}
  catch(error){
    error.message=`${filename}: ${error.code}: ${error.message}; validation=${JSON.stringify(error.validation??null)}`;
    throw error;
  }
}

async function fixture(t){
  const root=await mkdtemp(join(tmpdir(),'workflow-release-defaults-'));
  t.after(async()=>{assert(resolve(root).startsWith(resolve(tmpdir())));await rm(root,{recursive:true,force:true,maxRetries:3,retryDelay:100});});
  const configPath=join(root,'control-plane.json');
  await loadConfig({configPath,defaultConfigPath:DEFAULT_CONFIG_PATH});
  const service=new WorkflowService({configPath,defaultConfigPath:DEFAULT_CONFIG_PATH,env:{}});
  await service.call('migrate_v6',{}, {human:true});
  return {service,configPath};
}

test('fresh release library exposes only the two built-in authoring Workflows',async t=>{
  const {service}=await fixture(t);
  const workflows=await service.call('list');
  assert.deepEqual(workflows.map(item=>item.id),['system.build-workflow','system.skill2workflow']);
  assert(workflows.every(item=>item.system_managed&&item.status==='ready'&&item.enabled));
});

test('external Providers, GPT reviewer, and Cross-review are disabled by default without hiding their Roles',async t=>{
  const defaults=JSON.parse(await readFile(DEFAULT_CONFIG_PATH,'utf8'));
  const nativeIds=new Set(['native-luna','native-sol','native-astra']);
  assert(defaults.providers.filter(provider=>!nativeIds.has(provider.id)).every(provider=>provider.enabled===false));
  assert(defaults.providers.filter(provider=>nativeIds.has(provider.id)).every(provider=>provider.enabled===true));
  assert.equal(defaults.task_types.find(item=>item.id==='cross-review').enabled,false);

  const {service}=await fixture(t);
  const roles=await service.call('role_templates');
  const review=roles.find(item=>item.id==='builtin-role-cross-review');
  assert(review);
  assert.equal(review.enabled,false);
  assert.equal(review.default_enabled,false);
  assert.equal(review.provider_id,'grok-local');
  assert.equal(review.provider_kind,'builtin_connector');
  assert.equal(review.provider_enabled,false);
  await assert.rejects(service.call('role_template',{workflow_id:review.id,task:'Review this change'}),{code:'ROLE_NOT_READY'});

  const gptReview=roles.find(item=>item.id==='builtin-role-hard-path-web-advice');
  assert(gptReview);
  assert.equal(gptReview.name,'GPT reviewer');
  assert.equal(gptReview.provider_id,'chatgpt-web-pro');
  assert.equal(gptReview.provider_kind,'web_review');
  assert.equal(gptReview.enabled,false);
  assert.equal(gptReview.default_enabled,false);
  assert.equal(gptReview.provider_enabled,false);
  const editable=await service.call('customize_role',{workflow_id:gptReview.id},{human:true});
  assert.equal(editable.workflow.nodes.find(node=>node.id==='role').executor.provider_id,'chatgpt-web-pro');
  await assert.rejects(service.call('role_template',{workflow_id:gptReview.id,task:'Review this packet'}),{code:'ROLE_NOT_READY'});
});

test('Cross-review uses Grok and requires both its Role and Provider to be enabled',async t=>{
  const {service,configPath}=await fixture(t);
  const editable=await service.call('customize_role',{workflow_id:'builtin-role-cross-review'},{human:true});
  assert.equal(editable.workflow.enabled,false);
  const workflow=structuredClone(editable.workflow);workflow.enabled=true;
  const saved=await service.call('save',{workflow_id:workflow.id,expected_revision:editable.revision_hash,workflow},{human:true});
  const published=await service.call('publish',{workflow_id:workflow.id,expected_revision:saved.revision_hash},{human:true});
  const entry=(await service.call('role_templates')).find(item=>item.id==='builtin-role-cross-review');
  assert.equal(entry.enabled,true);
  assert.equal(entry.revision_hash,published.revision_hash);
  assert.equal(entry.provider_id,'grok-local');
  assert.equal(entry.provider_enabled,false);
  await assert.rejects(service.call('role_template',{workflow_id:entry.id,task:'Review this change'}),{code:'ROLE_PROVIDER_UNAVAILABLE'});
  const config=await loadConfig({configPath,defaultConfigPath:DEFAULT_CONFIG_PATH});
  config.providers.find(provider=>provider.id==='grok-local').enabled=true;
  await saveConfig(config,{configPath});
  const profile=await service.call('role_template',{workflow_id:entry.id,revision_hash:entry.revision_hash,task:'Review this change'});
  assert.equal(profile.role,'reviewer');
  assert.match(profile.instructions,/Review this change/);
});

test('optional example packages install, delete, and reinstall from local files',async t=>{
  const {service}=await fixture(t);
  for(const filename of PACKAGES){
    const packagePath=join(EXAMPLES,filename);
    const text=await readFile(packagePath,'utf8');
    assert.doesNotMatch(text,/[A-Za-z]:[\\/](?:Users|Documents)[\\/]/i);
    const first=await installExamplePackage(service,filename);
    const installed=await service.call('read',{workflow_id:first.workflow.id,revision_hash:first.revision_hash});
    assert.equal(installed.validation.valid,true,`${filename} must remain structurally installable`);
    assert.equal(installed.workflow.status,'ready');

    await service.call('delete',{workflow_id:first.workflow.id,expected_revision:first.revision_hash});
    assert.equal((await service.call('list')).some(item=>item.id===first.workflow.id),false);

    const second=await installExamplePackage(service,filename);
    assert.equal(second.workflow.id,first.workflow.id);
    assert.equal(second.revision_hash,first.revision_hash);
    await service.call('delete',{workflow_id:second.workflow.id,expected_revision:second.revision_hash});
  }
  assert.deepEqual((await service.call('list')).map(item=>item.id),['system.build-workflow','system.skill2workflow']);
});
