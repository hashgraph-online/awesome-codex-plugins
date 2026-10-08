import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, rm } from 'node:fs/promises';
import { join } from 'node:path';
import { tmpdir } from './physical-tempdir.mjs';
import { createHash } from 'node:crypto';
import { WorkflowStore } from '../lib/workflow-store.mjs';
import * as authoring from '../lib/authoring/authoring-workflows.mjs';
import { validateWorkflowShape } from '../lib/workflow-schema.mjs';

const providers=[
  {id:'planner',enabled:true,kind:'native_agent',capabilities:{read:true,write:true},config:{role:'implementer'}},
  {id:'reviewer',enabled:true,kind:'native_agent',capabilities:{read:true,write:false},config:{role:'reviewer'}},
];
const roles=[{id:'builtin-role-repository-analysis',revision_hash:'a'.repeat(64),role:'implementer',access:'read_only',instructions:'Analyze the repository.'}];
const routingRules={generation:{planner_provider_id:'planner',review_provider_id:'reviewer',max_rounds:2}};
const promptBaseIdentity=prompt=>({sha256:createHash('sha256').update(prompt).digest('hex'),length:prompt.length});

test('current bundled authoring Host identities refresh without changing configured prompts or Providers', async t => {
  const root = await mkdtemp(join(tmpdir(), 'authoring-host-identity-refresh-'));
  t.after(() => rm(root, { recursive: true, maxRetries: 3, retryDelay: 100 }));
  const store = await new WorkflowStore(root).initialize();
  const tools = ['read_workflow_resource', 'authoring-graph-assembly', 'authoring-execution-binding', 'authoring-deterministic-validation'];
  store.validationContext = { providers, roles, host_tools: tools, tools };
  const previous = {
    'authoring-graph-assembly': '36767b11957d25aec4c24172c067378a5747f6a61e81f8d76383e747b46df49c',
    'authoring-execution-binding': 'cb7042b94a55f68645c3f71be741c67e20deeeb4ed2fa703b334cf112b688af5',
    'authoring-deterministic-validation': '885511b02f8f1f1108b502c5905b8e3080e570e35e0369a17355f6481c3ec39f',
  };
  const originals = [];
  for (const definition of authoring.AUTHORING_WORKFLOWS) {
    const workflow = authoring.createStoredAuthoringWorkflow(definition, { planner: providers[0], reviewer: providers[1], maxRounds: 2 });
    for (const contract of workflow.host_tools) contract.identity.sha256 = previous[contract.identity.name];
    workflow.nodes.find(node => node.id === 'expand').prompt_template += ' User planner policy.';
    originals.push(await store.create(workflow, { provenance: { kind: 'bundled_authoring_workflow', authoring_workflow_id: definition.id,
      builtin_contract: definition.contract, builtin_prompt_bases: { planner: promptBaseIdentity(authoring.AUTHORING_PLANNER_PROMPT_V27), reviewer: promptBaseIdentity(authoring.AUTHORING_REVIEW_PROMPT_V22) } } }));
  }
  const refreshed = await authoring.ensureStoredAuthoringWorkflows(store, { providers, routingRules });
  for (const [index, pack] of refreshed.entries()) {
    authoring.storedAuthoringBindings(pack.workflow, providers);
    assert.deepEqual(pack.workflow.nodes, originals[index].workflow.nodes);
    assert.deepEqual(pack.workflow.authoring, originals[index].workflow.authoring);
    assert.equal(pack.workflow.revision, originals[index].workflow.revision + 1);
    assert.deepEqual(await store.snapshot(pack.workflow.id, originals[index].revision_hash), originals[index]);
  }
  assert.deepEqual((await authoring.ensureStoredAuthoringWorkflows(store, { providers, routingRules })).map(pack => pack.revision_hash), refreshed.map(pack => pack.revision_hash));
});

async function seedLegacyReady(store,workflow,options){
  store.validate=validateWorkflowShape;
  try{return await store.create(workflow,options);}finally{delete store.validate;}
}

test('unknown authoring Host implementation remains visible without blocking other built-ins or rewriting its head', async t => {
  const root = await mkdtemp(join(tmpdir(), 'authoring-host-identity-blocked-'));
  t.after(() => rm(root, { recursive: true, maxRetries: 3, retryDelay: 100 }));
  const store = await new WorkflowStore(root).initialize();
  const tools = ['read_workflow_resource', 'authoring-graph-assembly', 'authoring-execution-binding', 'authoring-deterministic-validation'];
  store.validationContext = { providers, roles, host_tools: tools, tools };
  const definition = authoring.AUTHORING_WORKFLOWS[0];
  const workflow = authoring.createStoredAuthoringWorkflow(definition, { planner: providers[0], reviewer: providers[1], maxRounds: 2 });
  workflow.host_tools[0].identity.sha256 = 'f'.repeat(64);
  const original = await store.create(workflow, { provenance: { kind: 'bundled_authoring_workflow', authoring_workflow_id: definition.id } });
  const packs = await authoring.ensureStoredAuthoringWorkflows(store, { providers, routingRules });
  const blocked = packs.find(pack => pack.workflow.id === definition.id);
  assert.equal(blocked.host_tool_identity_issue.code, 'HOST_TOOL_IDENTITY_MIGRATION_UNSUPPORTED');
  assert.equal(blocked.host_tool_identity_issue.host_tool_id, workflow.host_tools[0].id);
  assert.deepEqual(await store.snapshot(definition.id), original);
  for (const pack of packs.filter(pack => pack.workflow.id !== definition.id)) authoring.storedAuthoringBindings(pack.workflow, providers);
  assert.throws(() => authoring.storedAuthoringBindings(blocked.workflow, providers), { code: 'AUTHORING_WORKFLOW_CONTRACT' });
});

test('a future bundled authoring contract fails before any downgrade write',async()=>{
  const definition=authoring.AUTHORING_WORKFLOWS[0];
  const workflow=authoring.createStoredAuthoringWorkflow(definition,{planner:providers[0],reviewer:providers[1],maxRounds:2});
  workflow.authoring.contract='codex-authoring-workflow/v999';
  const pack={workflow,provenance:{kind:'bundled_authoring_workflow',authoring_workflow_id:definition.id}};
  const before=structuredClone(pack),writes=[];
  const store={snapshot:async()=>pack,create:async()=>writes.push('create'),resources:async()=>writes.push('resources'),save:async()=>writes.push('save')};
  await assert.rejects(authoring.ensureStoredAuthoringWorkflows(store,{providers,routingRules}),{code:'AUTHORING_WORKFLOW_CONTRACT'});
  assert.deepEqual(writes,[]);
  assert.deepEqual(pack,before);
});

test('the bundled v28 prompt refreshes to the generic no-transcription contract',async t=>{
  const root=await mkdtemp(join(tmpdir(),'authoring-v26-refresh-'));
  t.after(()=>rm(root,{recursive:true,force:true}));
  const store=await new WorkflowStore(root).initialize();
  const tools=['read_workflow_resource','authoring-graph-assembly','authoring-execution-binding','authoring-deterministic-validation'];
  store.validationContext={providers,roles,host_tools:tools,tools};
  const oldPrompt=authoring.AUTHORING_PLANNER_PROMPT_V25
    +' This prohibition also applies to free-text evidence and review findings: never ask a validator or reviewer to repeat item IDs, artifact paths, hashes or other input identity values. Return semantic findings in input order and bind the original items beside them downstream, or use a registered Host tool to join identity mechanically.';
  for(const definition of authoring.AUTHORING_WORKFLOWS){
    const workflow=authoring.createStoredAuthoringWorkflow(definition,{planner:providers[0],reviewer:providers[1],maxRounds:2});
    workflow.nodes.find(node=>node.id==='expand').prompt_template=oldPrompt;
    await seedLegacyReady(store,workflow,{provenance:{kind:'bundled_authoring_workflow',authoring_workflow_id:definition.id,builtin_contract:definition.contract}});
  }
  await authoring.ensureStoredAuthoringWorkflows(store,{providers,routingRules});
  for(const definition of authoring.AUTHORING_WORKFLOWS){
    const pack=await store.snapshot(definition.id);
    assert.equal(pack.workflow.nodes.find(node=>node.id==='expand').prompt_template,authoring.AUTHORING_PLANNER_PROMPT_V27);
    assert.deepEqual(pack.provenance.migration,{kind:'bundled_authoring_refresh',contract:'codex-authoring-workflow/v30',from_prompt_sha256:'292b851153c56cf9053fb90066ed3560fc49c74c63eeb6ec37a79feeb1da7d38'});
  }
});

test('current bundled authoring Workflows replace retired planner and reviewer bindings',async t=>{
  const root=await mkdtemp(join(tmpdir(),'authoring-provider-binding-'));
  t.after(()=>rm(root,{recursive:true,force:true}));
  const store=await new WorkflowStore(root).initialize();
  const currentProviders=[
    {id:'native-astra',enabled:true,kind:'native_agent',capabilities:{read:true,write:true},config:{role:'advisor'}},
    {id:'native-sol',enabled:true,kind:'native_agent',capabilities:{read:true,write:false},config:{role:'reviewer'}},
  ];
  const retiredProviders=[
    {...currentProviders[0],id:'native-authoring-astra-low'},
    {...currentProviders[1],id:'native-reviewer-low'},
  ];
  const tools=['read_workflow_resource','authoring-graph-assembly','authoring-execution-binding','authoring-deterministic-validation'];
  store.validationContext={providers:currentProviders,roles,host_tools:tools,tools};
  for(const definition of authoring.AUTHORING_WORKFLOWS){
    const workflow=authoring.createStoredAuthoringWorkflow(definition,{planner:retiredProviders[0],reviewer:retiredProviders[1],maxRounds:3});
    await seedLegacyReady(store,workflow,{provenance:{kind:'bundled_authoring_workflow',authoring_workflow_id:definition.id,builtin_contract:definition.contract}});
  }
  await authoring.ensureStoredAuthoringWorkflows(store,{providers:currentProviders,routingRules:{generation:{planner_provider_id:'native-authoring-astra-low',review_provider_id:'native-reviewer-low',max_rounds:3}}});
  for(const definition of authoring.AUTHORING_WORKFLOWS){
    const pack=await store.snapshot(definition.id);
    assert.equal(pack.workflow.nodes.find(node=>node.id==='expand').executor.provider_id,'native-astra');
    assert.equal(pack.workflow.nodes.find(node=>node.id==='final').authoring_reviewer_provider_id,'native-sol');
    assert.equal(pack.workflow.authoring.planner_provider_id,'native-astra');
    assert.equal(pack.workflow.authoring.review_provider_id,'native-sol');
    assert.deepEqual(pack.provenance.migration,{kind:'bundled_authoring_provider_binding',contract:definition.contract,planner_provider_id:'native-astra',review_provider_id:'native-sol'});
  }
});

test('persisted prompt-base identity replaces unknown retired bases and preserves only user suffixes',async t=>{
  const root=await mkdtemp(join(tmpdir(),'authoring-prompt-identity-'));
  t.after(()=>rm(root,{recursive:true,force:true}));
  const store=await new WorkflowStore(root).initialize();
  const tools=['read_workflow_resource','authoring-graph-assembly','authoring-execution-binding','authoring-deterministic-validation'];
  store.validationContext={providers,roles,host_tools:tools,tools};
  const retiredPlanner='Retired built-in planner contract.';
  const retiredReviewer='Retired built-in reviewer contract.';
  for(const definition of authoring.AUTHORING_WORKFLOWS){
    const workflow=authoring.createStoredAuthoringWorkflow(definition,{planner:providers[0],reviewer:providers[1],maxRounds:2});
    workflow.authoring.contract='codex-authoring-workflow/v27';
    workflow.nodes.find(node=>node.id==='expand').prompt_template=retiredPlanner+' User planner policy.';
    workflow.nodes.find(node=>node.id==='final').prompt_template=retiredReviewer+' User reviewer policy.';
    await seedLegacyReady(store,workflow,{provenance:{kind:'bundled_authoring_workflow',authoring_workflow_id:definition.id,builtin_contract:'codex-authoring-workflow/v27',builtin_prompt_bases:{planner:promptBaseIdentity(retiredPlanner),reviewer:promptBaseIdentity(retiredReviewer)}}});
  }
  await authoring.ensureStoredAuthoringWorkflows(store,{providers,routingRules});
  for(const definition of authoring.AUTHORING_WORKFLOWS){
    const pack=await store.snapshot(definition.id);
    assert.equal(pack.workflow.nodes.find(node=>node.id==='expand').prompt_template,authoring.AUTHORING_PLANNER_PROMPT_V27+' User planner policy.');
    assert.equal(pack.workflow.nodes.find(node=>node.id==='final').prompt_template,authoring.AUTHORING_REVIEW_PROMPT_V22+' User reviewer policy.');
    assert.deepEqual(pack.provenance.builtin_prompt_bases,{planner:promptBaseIdentity(authoring.AUTHORING_PLANNER_PROMPT_V27),reviewer:promptBaseIdentity(authoring.AUTHORING_REVIEW_PROMPT_V22)});
  }
});

for(const version of [18,19,21,22,23,24,26,27])for(const custom of [false,true])test(`both v${version} authoring adapters upgrade without losing ${custom?'custom prompts':'configured slots'}`,async t=>{
  const root=await mkdtemp(join(tmpdir(),'authoring-efficiency-'));
  t.after(()=>rm(root,{recursive:true,force:true}));
  const store=await new WorkflowStore(root).initialize();
  const tools=['read_workflow_resource','authoring-graph-assembly','authoring-execution-binding','authoring-deterministic-validation'];
  store.validationContext={providers,roles,host_tools:tools,tools};
  for(const definition of authoring.AUTHORING_WORKFLOWS){
    const previous=authoring.createStoredAuthoringWorkflow(definition,{planner:providers[0],reviewer:providers[1],maxRounds:2});
    previous.authoring.contract=`codex-authoring-workflow/v${version}`;
    const planner=previous.nodes.find(node=>node.id==='expand'),reviewer=previous.nodes.find(node=>node.id==='final');
    const oldPrompt=[26,27].includes(version)?authoring.AUTHORING_PLANNER_PROMPT_V26:version===24?authoring.AUTHORING_PLANNER_PROMPT_V24:version===23?authoring.AUTHORING_PLANNER_PROMPT_V23:version===22?authoring.AUTHORING_PLANNER_PROMPT_V22:version===21?authoring.AUTHORING_PLANNER_PROMPT_V21:version===19?authoring.AUTHORING_PLANNER_PROMPT_V19:authoring.AUTHORING_PLANNER_PROMPT_V15;
    planner.prompt_template=custom?oldPrompt+' User planner policy.':oldPrompt;
    reviewer.prompt_template=custom?'User review policy.':[26,27].includes(version)?authoring.AUTHORING_REVIEW_PROMPT_V20:version===23?authoring.AUTHORING_REVIEW_PROMPT_V20:version===22?authoring.AUTHORING_REVIEW_PROMPT_V19:authoring.AUTHORING_REVIEW_PROMPT_V18;
    if(version===27)reviewer.retry.max_attempts=1;
    planner.approval.required=true;reviewer.approval.required=true;
    await seedLegacyReady(store,previous,{provenance:{kind:'bundled_authoring_workflow',authoring_workflow_id:definition.id,builtin_contract:`codex-authoring-workflow/v${version}`}});
  }
  await authoring.ensureStoredAuthoringWorkflows(store,{providers,routingRules});
  for(const definition of authoring.AUTHORING_WORKFLOWS){
    const pack=await store.snapshot(definition.id),workflow=pack.workflow;
    const planner=workflow.nodes.find(node=>node.id==='expand'),reviewer=workflow.nodes.find(node=>node.id==='final');
    assert.equal(workflow.authoring.contract,'codex-authoring-workflow/v30');
    const oldPrompt=[26,27].includes(version)?authoring.AUTHORING_PLANNER_PROMPT_V26:version===24?authoring.AUTHORING_PLANNER_PROMPT_V24:version===23?authoring.AUTHORING_PLANNER_PROMPT_V23:version===22?authoring.AUTHORING_PLANNER_PROMPT_V22:version===21?authoring.AUTHORING_PLANNER_PROMPT_V21:version===19?authoring.AUTHORING_PLANNER_PROMPT_V19:authoring.AUTHORING_PLANNER_PROMPT_V15;
    assert.equal(planner.prompt_template,custom?authoring.AUTHORING_PLANNER_PROMPT_V27+' User planner policy.':authoring.AUTHORING_PLANNER_PROMPT_V27);
    assert.equal(reviewer.prompt_template,custom?'User review policy.':authoring.AUTHORING_REVIEW_PROMPT_V22);
    assert.equal(planner.approval.required,true);assert.equal(reviewer.approval.required,true);
    assert.equal(planner.retry.max_attempts,10);assert.equal(reviewer.retry.max_attempts,3);
    assert.equal(planner.executor.provider_id,'planner');assert.equal(reviewer.authoring_reviewer_provider_id,'reviewer');
    assert.equal(workflow.authoring.max_rounds,2);
    assert.equal(workflow.nodes.filter(node=>node.type==='agent').length,2);
    assert.equal(workflow.nodes.filter(node=>node.type==='tool').length,3);
    assert.equal(pack.provenance.migration.from_contract,`codex-authoring-workflow/v${version}`);
    assert.equal(pack.provenance.migration.to_contract,'codex-authoring-workflow/v30');
  }
});
