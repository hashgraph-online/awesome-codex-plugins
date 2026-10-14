import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { join, resolve } from 'node:path';
import { tmpdir } from './physical-tempdir.mjs';
import { WorkflowService } from '../lib/workflow-service.mjs';
import { loadConfig, saveConfig } from '../lib/config.mjs';
import { DEFAULT_CONFIG_PATH } from '../server.mjs';
import { createDraft } from '../lib/workflow-schema.mjs';

async function fixture(t){
  const root=await mkdtemp(join(tmpdir(),'workflow-release-defaults-'));
  t.after(async()=>{assert(resolve(root).startsWith(resolve(tmpdir())));await rm(root,{recursive:true,force:true,maxRetries:3,retryDelay:100});});
  const configPath=join(root,'control-plane.json');
  await loadConfig({configPath,defaultConfigPath:DEFAULT_CONFIG_PATH});
  const service=new WorkflowService({configPath,defaultConfigPath:DEFAULT_CONFIG_PATH,env:{}});
  return {service,configPath,root};
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
  assert.equal(defaults.version,7);
  assert.deepEqual(defaults.strict_executor,{enabled:true});
  assert.equal(Object.hasOwn(defaults,'task_types'),false);
  const {roles:definitions}=JSON.parse(await readFile(new URL('../builtin-role-definitions.json',import.meta.url),'utf8'));
  assert.equal(definitions.length,8);
  assert(definitions.every(item=>item.stages.length===1));
  assert.equal(definitions.find(item=>item.id==='cross-review').enabled,false);

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
  await assert.rejects(service.call('publish',{workflow_id:workflow.id,expected_revision:saved.revision_hash},{human:true}),error=>{
    assert.equal(error.code,'WORKFLOW_NOT_READY');
    assert.equal(error.validation.valid,true);
    assert.equal(error.validation.launch_ready,false);
    return true;
  });
  const entry=(await service.call('role_templates')).find(item=>item.id==='builtin-role-cross-review');
  assert.equal(entry.enabled,false);
  const retained=await service.call('read',{workflow_id:workflow.id,revision_hash:saved.revision_hash});
  assert.equal(retained.workflow.status,'draft');
  assert.equal(retained.workflow.enabled,true);
  assert.equal(entry.provider_id,'grok-local');
  assert.equal(entry.provider_enabled,false);
  await assert.rejects(service.call('role_template',{workflow_id:entry.id,task:'Review this change'}),{code:'ROLE_NOT_READY'});
  const config=await loadConfig({configPath,defaultConfigPath:DEFAULT_CONFIG_PATH});
  config.providers.find(provider=>provider.id==='grok-local').enabled=true;
  await saveConfig(config,{configPath});
  const published=await service.call('publish',{workflow_id:workflow.id,expected_revision:saved.revision_hash},{human:true});
  const profile=await service.call('role_template',{workflow_id:entry.id,revision_hash:published.revision_hash,task:'Review this change'});
  assert.equal(profile.role,'reviewer');
  assert.match(profile.instructions,/Review this change/);
});

test('portable packages install, delete, and reinstall from a generated local fixture',async t=>{
  const {service,root}=await fixture(t);
  const output={type:'object',properties:{result:{type:'string'}},required:['result'],additionalProperties:false};
  const workflow={...createDraft('release-portable-fixture','Portable release fixture'),status:'ready',
    skill_policy:{mode:'cooperative',implicit:'deny',ambient_allow:[],shadowed_skill_paths:[]},
    inputs_schema:{type:'object',properties:{task:{type:'string'}},required:['task'],additionalProperties:false},
    finalization:{required:true,node_id:'final'},
    nodes:[{id:'start',type:'start'},{id:'final',type:'agent',executor:{kind:'main',mode:'orchestration'},role:'finalizer',access:'read_only',approval:{required:false},retry:{max_attempts:1},input_bindings:{task:'/inputs/task'},prompt_template:'Return the task result.',outputs_schema:output},{id:'end',type:'end'}],
    edges:[{id:'start-final',source:'start',target:'final'},{id:'final-end',source:'final',target:'end'}]};
  const source=await service.call('create',{workflow},{human:true});
  const bundle=await service.call('export_workflow_package',{workflow_id:workflow.id,revision_hash:source.revision_hash,package_version:'1.0.0'});
  const packagePath=join(root,'portable.workflow-package.json');
  await writeFile(packagePath,JSON.stringify(bundle));
  await service.call('delete',{workflow_id:workflow.id,expected_revision:source.revision_hash});
  const first=await service.call('install_workflow_package',{package_path:packagePath});
  const installed=await service.call('read',{workflow_id:first.workflow.id,revision_hash:first.revision_hash});
  assert.equal(installed.validation.valid,true);
  assert.equal(installed.workflow.status,'ready');
  await service.call('delete',{workflow_id:first.workflow.id,expected_revision:first.revision_hash});
  assert.equal((await service.call('list')).some(item=>item.id===first.workflow.id),false);
  const second=await service.call('install_workflow_package',{package_path:packagePath});
  assert.equal(second.workflow.id,first.workflow.id);
  assert.equal(second.revision_hash,first.revision_hash);
  await service.call('delete',{workflow_id:second.workflow.id,expected_revision:second.revision_hash});
  assert.deepEqual((await service.call('list')).map(item=>item.id),['system.build-workflow','system.skill2workflow']);
});


test('direct fresh service startup needs no migration and missing existing stores stay visible', async t => {
  const root=await mkdtemp(join(tmpdir(),'workflow-release-direct-bootstrap-'));
  t.after(()=>rm(root,{recursive:true,force:true,maxRetries:3,retryDelay:100}));
  const configPath=join(root,'control-plane.json');
  const service=new WorkflowService({configPath,defaultConfigPath:DEFAULT_CONFIG_PATH,env:{}});
  assert.deepEqual((await service.call('list')).map(item=>item.id),['system.build-workflow','system.skill2workflow']);
  const config=JSON.parse(await readFile(configPath,'utf8'));
  assert.equal(config.version,7);
  assert.equal(Object.hasOwn(config,'task_types'),false);
  const storeRoot=join(root,config.workflow_store.relative_path);
  assert.equal(resolve(storeRoot),join(resolve(root),'workflows'));
  await rm(storeRoot,{recursive:true});
  await assert.rejects(service.call('list'),{code:'ENOENT'});
  assert.equal(JSON.parse(await readFile(configPath,'utf8')).workflow_store.relative_path,'workflows');
});
